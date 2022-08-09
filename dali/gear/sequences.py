"""
Sequence for simplifying certain interactions with 16-bit DALI gear
"""
from __future__ import annotations

from typing import Generator, Optional

from dali import command
from dali.address import GearAddress, GearShort
from dali.gear.colour import (
    Activate,
    QueryColourValue,
    QueryColourValueDTR,
    SetTemporaryColourTemperature,
)
from dali.gear.general import DTR0, DTR1, QueryActualLevel, QueryContentDTR0


def SetDT8ColourValueTc(
    address: GearAddress,
    tc_mired: int,
) -> Generator[command.Command, Optional[command.Response], None]:
    """
    A generator sequence set query the Colour Temperature of a DT8 control
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
