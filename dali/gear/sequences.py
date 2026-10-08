"""
Sequence for simplifying certain interactions with 16-bit DALI gear
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Generator, Optional, Type, TypeVar

from dali import command
from dali.address import GearAddress, GearShort
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
    QueryEmergencyFeatures,
    QueryEmergencyLevel,
    QueryEmergencyMode,
    QueryEmergencyStatus,
    QueryLampEmergencyTime,
    QueryLampTotalOperationTime,
    QueryRatedDuration,
)
from dali.gear.general import DTR0, DTR1, DTR2, QueryActualLevel, QueryContentDTR0


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
class EmergencyMode:
    """Decoded Emergency Mode Information byte (IEC 62386-202).

    Fields are declared least-significant bit first.
    """

    rest_mode: bool
    normal_mode: bool
    emergency_mode: bool
    extended_emergency_mode: bool
    function_test: bool
    duration_test: bool
    hardwired_inhibit_active: bool
    hardwired_switch_on: bool


@dataclass(frozen=True)
class EmergencyFeatures:
    """Decoded Features information byte (IEC 62386-202).

    Fields are declared least-significant bit first.
    """

    integral_emergency_control_gear: bool
    maintained_control_gear: bool
    switched_maintained_control_gear: bool
    auto_test_capability: bool
    adjustable_emergency_level: bool
    hardwired_inhibit_supported: bool
    physical_selection_supported: bool
    relight_in_rest_mode_supported: bool


@dataclass(frozen=True)
class EmergencyFailureStatus:
    """Decoded Failure Status information byte (IEC 62386-202).

    Fields are declared least-significant bit first.
    """

    circuit_failure: bool
    battery_duration_failure: bool
    battery_failure: bool
    emergency_lamp_failure: bool
    function_test_max_delay_exceeded: bool
    duration_test_max_delay_exceeded: bool
    function_test_failed: bool
    duration_test_failed: bool


@dataclass(frozen=True)
class EmergencyStatus:
    """Decoded Emergency Status information byte (IEC 62386-202).

    Fields are declared least-significant bit first.
    """

    inhibit_mode: bool
    function_test_done_and_result_valid: bool
    duration_test_done_and_result_valid: bool
    battery_fully_charged: bool
    function_test_pending: bool
    duration_test_pending: bool
    identification_active: bool
    physically_selected: bool


@dataclass(frozen=True)
class EmergencyInformation:
    """Decoded DT1 (IEC 62386-202) status and measurement values.

    Each status byte is decoded into its named bits, or None where the gear
    did not answer or replied with a framing error. The measurement values
    are plain integers, or None where the gear reports MASK or does not
    answer.
    """

    emergency_mode: Optional[EmergencyMode]
    emergency_features: Optional[EmergencyFeatures]
    emergency_failure_status: Optional[EmergencyFailureStatus]
    emergency_status: Optional[EmergencyStatus]
    battery_charge: Optional[int]
    emergency_level: Optional[int]
    duration_test_result: Optional[int]
    lamp_emergency_time: Optional[int]
    lamp_total_operation_time: Optional[int]
    rated_duration: Optional[int]


_StatusByte = TypeVar("_StatusByte")


def _decode_status(
    response: Optional[command.Response],
    cls: Type[_StatusByte],
) -> Optional[_StatusByte]:
    """Decode a bitmap response into one of the status dataclasses, or None if
    the gear did not answer or replied with a framing error.

    The dataclass fields are declared least-significant bit first, so each is
    assigned the matching bit of the response byte by position.
    """
    if response is None:
        return None
    raw = response.raw_value
    if raw is None or raw.error:
        return None
    byte = raw.as_integer
    return cls(
        **{field.name: bool(byte & (1 << pos)) for pos, field in enumerate(fields(cls))}
    )


def _numeric(response: Optional[command.Response]) -> Optional[int]:
    """Return the integer value of a numeric response, or None for MASK,
    a missing answer or a framing error."""
    if response is None:
        return None
    value = response.value
    return value if isinstance(value, int) else None


def QueryEmergencyInformation(
    address: GearShort,
) -> Generator[command.Command, Optional[command.Response], EmergencyInformation]:
    """Read the DT1 (IEC 62386-202) status and measurement values of an
    emergency control gear in a single sequence.

    Bundling the queries into one sequence runs them under a single
    transaction, so no other command can interleave between them. The four
    status bytes are decoded into their named bits and the measurement values
    are returned as plain integers (or None where the gear reports MASK or
    does not answer).

    :param address: GearShort address to query
    :return: an EmergencyInformation dataclass
    """
    # Although the proper types are expected, ints are common enough for
    # addresses and their meaning is unambiguous in this context
    if isinstance(address, int):
        address = GearShort(address)

    return EmergencyInformation(
        emergency_mode=_decode_status(
            (yield QueryEmergencyMode(address)), EmergencyMode
        ),
        emergency_features=_decode_status(
            (yield QueryEmergencyFeatures(address)), EmergencyFeatures
        ),
        emergency_failure_status=_decode_status(
            (yield QueryEmergencyFailureStatus(address)), EmergencyFailureStatus
        ),
        emergency_status=_decode_status(
            (yield QueryEmergencyStatus(address)), EmergencyStatus
        ),
        battery_charge=_numeric((yield QueryBatteryCharge(address))),
        emergency_level=_numeric((yield QueryEmergencyLevel(address))),
        duration_test_result=_numeric((yield QueryDurationTestResult(address))),
        lamp_emergency_time=_numeric((yield QueryLampEmergencyTime(address))),
        lamp_total_operation_time=_numeric(
            (yield QueryLampTotalOperationTime(address))
        ),
        rated_duration=_numeric((yield QueryRatedDuration(address))),
    )
