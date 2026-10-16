"""
Sequence for simplifying certain interactions with 16-bit DALI gear
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, Optional, TypeVar

from dali import command, sequences
from dali.address import GearAddress, GearShort
from dali.exceptions import DALISequenceError
from dali.gear.colour import (
    Activate,
    QueryColourValue,
    QueryColourValueDTR,
    SetTemporaryColourTemperature,
    StoreColourTemperatureTcLimit,
)
from dali.gear.emergency import (
    QueryBatteryCharge,
    QueryDurationTestResult,
    QueryEmergencyFailureStatus,
    QueryEmergencyFailureStatusResponse,
    QueryEmergencyFeatures,
    QueryEmergencyFeaturesResponse,
    QueryEmergencyLevel,
    QueryEmergencyMode,
    QueryEmergencyModeResponse,
    QueryEmergencyStatus,
    QueryEmergencyStatusResponse,
    QueryLampEmergencyTime,
    QueryLampTotalOperationTime,
    QueryRatedDuration,
)
from dali.gear.general import DTR0, DTR1, DTR2, QueryActualLevel, QueryContentDTR0


# Gear-related sequences will be moved here from dali.sequences at
# some point. Make the new locations work now.
QueryDeviceTypes = sequences.QueryDeviceTypes
QueryGroups = sequences.QueryGroups
SetGroups = sequences.SetGroups
Commissioning = sequences.Commissioning


def SetDT8ColourValueTc(
    address: GearAddress,
    tc_mired: int,
) -> Generator[command.Command, Optional[command.Response], None]:
    """
    A generator sequence to set the Colour Temperature of a DT8 control
    gear. Note that this sequence assumes that the address being targeted
    supports DT8 Tc control, it will not check this before sending commands.

    :param address: GearAddress (i.e. short, group, broadcast) address to set
    :param tc_mired: An int of the colour temperature to set, in mired
    :return: None
    """
    # Although the proper types are expected, ints are common enough for
    # addresses and their meaning is unambiguous in this context
    if isinstance(address, int):
        address = GearShort(address)

    tc_bytes = tc_mired.to_bytes(length=2, byteorder="little")
    yield DTR0(tc_bytes[0])
    yield DTR1(tc_bytes[1])
    yield SetTemporaryColourTemperature(address)
    yield Activate(address)


def QueryDT8ColourValue(
    address: GearShort,
    query: QueryColourValueDTR,
) -> Generator[command.Command, Optional[command.Response], Optional[int]]:
    """
    A generator sequence to query the Colour Value of a DT8 control gear,
    from the list of numerous options in QueryColourValueDTR.

    Note that this sequence assumes that the address being targeted supports
    the selected colour control method, it will not check this before sending
    commands. The return value will be an int (or None), assembled from the
    two bytes response.

    :param address: GearShort address to query
    :param query: specific option from QueryColourValueDTR to send as the query
    :return: The answer to the query as an int, or None if no answer
    """
    # Although the proper types are expected, ints are common enough for
    # addresses and their meaning is unambiguous in this context
    if isinstance(address, int):
        address = GearShort(address)

    if not isinstance(query, QueryColourValueDTR):
        raise TypeError(
            "'query' must be a value from QueryColourValueDTR enumerator"
        )

    # 62386-209, command 250, Note 2: start by sending "QUERY ACTUAL LEVEL"
    yield QueryActualLevel(address)
    yield DTR0(query.value)
    msb = yield QueryColourValue(address)
    lsb = yield QueryContentDTR0(address)
    col_val = None
    if (
        isinstance(msb, command.NumericResponseMask)
        and isinstance(lsb, command.NumericResponse)
        and isinstance(msb.value, int)
        and isinstance(lsb.value, int)
    ):
        try:
            col_val = int.from_bytes((lsb.value, msb.value), "little")
        except (TypeError, ValueError):
            col_val = None

    return col_val


def SetDT8TcLimit(
    address: GearAddress,
    what_limit: int,
    tc_mired: int,
) -> Generator[command.Command, Optional[command.Response], None]:
    """
    A generator sequence to set the Colour Temperature limit of a DT8 control
    gear. Note that this sequence assumes that the address being targeted
    supports DT8 Tc control, it will not check this before sending commands.

    :param address: GearAddress (i.e. short, group, broadcast) address to set
    :param what_limit: What limit to set, from dali.gear.colour.StoreColourTemperatureTcLimitDTR2
    :param tc_mired: An int of the colour temperature to set, in mired
    """
    # Although the proper types are expected, ints are common enough for
    # addresses and their meaning is unambiguous in this context
    if isinstance(address, int):
        address = GearShort(address)

    tc_bytes = tc_mired.to_bytes(length=2, byteorder="little")
    yield DTR0(tc_bytes[0])
    yield DTR1(tc_bytes[1])
    yield DTR2(what_limit)
    yield StoreColourTemperatureTcLimit(address)


@dataclass(frozen=True)
class EmergencyInformation:
    """DT1 (IEC 62386-202) status and measurement values of an emergency
    control gear.

    Each field holds the query's response object, preserving the attributes
    those classes decode: the named status bits (for example
    ``emergency_mode.emergency_mode``) and the measurement values
    (``battery_charge.value``, which is an integer or ``"MASK"``).
    """

    emergency_mode: QueryEmergencyModeResponse
    emergency_features: QueryEmergencyFeaturesResponse
    emergency_failure_status: QueryEmergencyFailureStatusResponse
    emergency_status: QueryEmergencyStatusResponse
    battery_charge: command.NumericResponseMask
    emergency_level: command.NumericResponseMask
    duration_test_result: command.NumericResponse
    lamp_emergency_time: command.NumericResponse
    lamp_total_operation_time: command.NumericResponse
    rated_duration: command.NumericResponse


ResponseType = TypeVar("ResponseType", bound=command.Response)


def _require(response: Optional[command.Response],
             responsetype: type[ResponseType],
             what: str) -> ResponseType:
    """Return the response, or abort the sequence if the gear did not answer
    or replied with a framing error."""
    if response is None:
        raise DALISequenceError(f"Missing response to {what}")
    assert isinstance(response, responsetype)
    raw = response.raw_value
    if raw is None:
        raise DALISequenceError(f"No response to {what}")
    if raw.error:
        raise DALISequenceError(f"Framing error in response to {what}")
    return response


def QueryEmergencyInformation(
    address: GearAddress,
) -> Generator[command.Command, Optional[command.Response], EmergencyInformation]:
    """Read the DT1 (IEC 62386-202) status and measurement values of an
    emergency control gear in a single sequence.

    Bundling the queries into one sequence runs them under a single
    transaction, so no other command can interleave between them. Each query's
    response object is kept in the returned EmergencyInformation, so the caller
    can read the named status bits and measurement values the response classes
    decode.

    A MASK measurement is a valid answer and is preserved; the sequence aborts
    with a DALISequenceError if any query goes unanswered or returns a framing
    error.

    :param address: GearShort address to query
    :return: an EmergencyInformation dataclass
    """
    # Although the proper types are expected, ints are common enough for
    # addresses and their meaning is unambiguous in this context
    if isinstance(address, int):
        address = GearShort(address)

    return EmergencyInformation(
        emergency_mode=_require(
            (yield QueryEmergencyMode(address)), QueryEmergencyModeResponse,
            "QueryEmergencyMode"
        ),
        emergency_features=_require(
            (yield QueryEmergencyFeatures(address)),
            QueryEmergencyFeaturesResponse, "QueryEmergencyFeatures"
        ),
        emergency_failure_status=_require(
            (yield QueryEmergencyFailureStatus(address)),
            QueryEmergencyFailureStatusResponse, "QueryEmergencyFailureStatus"
        ),
        emergency_status=_require(
            (yield QueryEmergencyStatus(address)),
            QueryEmergencyStatusResponse, "QueryEmergencyStatus"
        ),
        battery_charge=_require(
            (yield QueryBatteryCharge(address)),
            command.NumericResponseMask, "QueryBatteryCharge"
        ),
        emergency_level=_require(
            (yield QueryEmergencyLevel(address)),
            command.NumericResponseMask, "QueryEmergencyLevel"
        ),
        duration_test_result=_require(
            (yield QueryDurationTestResult(address)),
            command.NumericResponse, "QueryDurationTestResult"
        ),
        lamp_emergency_time=_require(
            (yield QueryLampEmergencyTime(address)),
            command.NumericResponse, "QueryLampEmergencyTime"
        ),
        lamp_total_operation_time=_require(
            (yield QueryLampTotalOperationTime(address)),
            command.NumericResponse, "QueryLampTotalOperationTime"
        ),
        rated_duration=_require(
            (yield QueryRatedDuration(address)),
            command.NumericResponse, "QueryRatedDuration"
        ),
    )
