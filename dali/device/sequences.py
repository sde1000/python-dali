"""
Sequence for simplifying certain interactions with 24-bit DALI devices
"""
from __future__ import annotations

import types
from typing import Generator, Optional, Type

from dali.address import DeviceShort, InstanceNumber
from dali.command import Command, Response
from dali.device.general import (
    DTR0,
    DTR1,
    DTR2,
    EventScheme,
    InstanceEventFilter,
    QueryEventFilterH,
    QueryEventFilterL,
    QueryEventFilterM,
    QueryEventScheme,
    QueryEventSchemeResponse,
    SetEventFilter,
    SetEventScheme,
)
from dali.device.helpers import check_bad_rsp


def SetEventSchemes(
    device: DeviceShort,
    instance: InstanceNumber,
    scheme: EventScheme,
) -> Generator[
    Command,
    Optional[Response],
    Optional[QueryEventSchemeResponse],
]:
    """
    A generator sequence to set the event scheme of a device instance. Use
    with an appropriate DALI driver instance, through the `run_sequence()`
    method.

    Returns the event scheme that the target instance actually set.

    Example:
    ```
    await driver.run_sequence(
        SetEventSchemes(
            device=address.DeviceShort(1),
            instance=address.InstanceNumber(2),
            scheme=EventScheme.device_instance,
        )
    )
    ```
    """
    # Although the proper types are expected, ints are common enough for
    # addresses and their meaning is unambiguous in this context
    if isinstance(device, int):
        device = DeviceShort(device)
    if isinstance(instance, int):
        instance = InstanceNumber(instance)

    # The scheme should be a member of EventScheme, but an int does work just
    # fine, so allow it
    pos = int(scheme)
    # Check that 'scheme' is actually an EventScheme member, will raise a
    # ValueError if not
    EventScheme(pos)

    rsp = yield DTR0(pos)
    if rsp is not None:
        return

    rsp = yield SetEventScheme(device=device, instance=instance)
    if rsp is not None:
        return

    rsp = yield QueryEventScheme(device=device, instance=instance)
    return rsp


def SetEventFilters(
    device: DeviceShort,
    instance: InstanceNumber,
    filter_value: InstanceEventFilter,
) -> Generator[Command, Optional[Response], Optional[InstanceEventFilter]]:
    """
    A generator sequence to set the event filters of a device instance.
    Use with an appropriate DALI driver instance, through the `run_sequence()`
    method.

    Returns the event filters that the target device actually set.

    Example:
    ```
    from dali import address
    from dali.device.pushbutton import InstanceEventFilter as filter_pb

    await driver.run_sequence(
        SetEventFilters(
            device=address.DeviceShort(1),
            instance=address.InstanceNumber(2),
            filter_value=filter_pb.short_press | filter_pb.double_press,
        )
    )
    ```
    """
    if not isinstance(filter_value, int):
        raise TypeError(
            f"'filter_value' must be an int, not {type(filter_value)}"
        )
    # Although the proper types are expected, ints are common enough for
    # addresses and their meaning is unambiguous in this context
    if isinstance(device, int):
        device = DeviceShort(device)
    if isinstance(instance, int):
        instance = InstanceNumber(instance)

    if isinstance(filter_value, InstanceEventFilter):
        uses_dtr1 = filter_value.dali_width() > 8
        uses_dtr2 = filter_value.dali_width() > 16
    else:
        uses_dtr1 = False
        uses_dtr2 = False

    # The values in InstanceEventFilter are already mapped out to the
    # corresponding bits, through the inheritance from IntFlag
    lo, md, hi = filter_value.to_bytes(3, "little")

    # Set the various values into the DTRs
    rsp = yield DTR0(lo)
    if rsp is not None:
        return
    if uses_dtr1:
        rsp = yield DTR1(md)
        if rsp is not None:
            return
    if uses_dtr2 > 16:
        rsp = yield DTR2(hi)
        if rsp is not None:
            return
    # Set the filters
    rsp = yield SetEventFilter(device=device, instance=instance)
    if rsp is not None:
        return

    # Read back the values that were set
    rsp = yield QueryEventFilterL(device=device, instance=instance)
    if check_bad_rsp(rsp):
        return
    lo = rsp.value
    if uses_dtr1:
        rsp = yield QueryEventFilterM(device=device, instance=instance)
        if check_bad_rsp(rsp):
            return
        md = rsp.value
    if uses_dtr2:
        rsp = yield QueryEventFilterH(device=device, instance=instance)
        if check_bad_rsp(rsp):
            return
        hi = rsp.value

    return filter_value.__class__(int.from_bytes((lo, md, hi), "little"))


def QueryEventFilters(
    device: DeviceShort,
    instance: InstanceNumber,
    filter_type: types.ModuleType | Type[InstanceEventFilter],
) -> Generator[Command, Optional[Response], Optional[InstanceEventFilter]]:
    """
    A generator sequence to query the event filters of a device instance.
    Use with an appropriate DALI driver instance, through the `run_sequence()`
    method.

    Returns the event filters used by the target device.

    :param device: A DeviceShort address to target
    :param instance: An InstanceNumber to target
    :param filter_type: Either the module of the type being targeted, or a
    specific InstanceEventFilter type to use, e.g. `dali.device.pushbutton`
    :return: A generator function, to use with e.g. `driver.run_sequence()`

    Example:
    ```
    from dali import address
    from dali.device import pushbutton

    await driver.run_sequence(
        QueryEventFilters(
            device=address.DeviceShort(1),
            instance=address.InstanceNumber(2),
            filter_type=pushbutton,
        )
    )
    ```
    """
    if hasattr(filter_type, "InstanceEventFilter"):
        filter_type = getattr(filter_type, "InstanceEventFilter")
    elif not issubclass(filter_type, InstanceEventFilter):
        raise TypeError("'filter_type' must be an InstanceEventFilter subclass")
    # Although the proper types are expected, ints are common enough for
    # addresses and their meaning is unambiguous in this context
    if isinstance(device, int):
        device = DeviceShort(device)
    if isinstance(instance, int):
        instance = InstanceNumber(instance)

    lo = 0
    md = 0
    hi = 0

    rsp = yield QueryEventFilterL(device=device, instance=instance)
    if check_bad_rsp(rsp):
        return
    lo = rsp.value
    if filter_type.dali_width() > 8:
        rsp = yield QueryEventFilterM(device=device, instance=instance)
        if check_bad_rsp(rsp):
            return
        md = rsp.value
    if filter_type.dali_width() > 16:
        rsp = yield QueryEventFilterH(device=device, instance=instance)
        if check_bad_rsp(rsp):
            return
        hi = rsp.value

    return filter_type(int.from_bytes((lo, md, hi), "little"))
