"""
Sequence for simplifying certain interactions with 24-bit DALI devices
"""
from __future__ import annotations

import types
from typing import Generator, Optional, Type

from dali.address import DeviceShort, InstanceNumber, DeviceBroadcast, DeviceBroadcastUnaddressed
from dali.command import Command, Response
from dali.device.general import (
    Compare,
    DTR0,
    DTR1,
    DTR2,
    EventScheme,
    Initialise,
    InstanceEventFilter,
    ProgramShortAddress,
    QueryDeviceStatus,
    QueryEventFilterH,
    QueryEventFilterL,
    QueryEventFilterM,
    QueryEventScheme,
    QueryEventSchemeResponse,
    QueryInputValue,
    QueryInputValueLatch,
    QueryResolution,
    Randomise,
    SearchAddrH,
    SearchAddrL,
    SearchAddrM,
    SetEventFilter,
    SetEventScheme,
    SetShortAddress,
    Terminate,
    VerifyShortAddress,
    Withdraw,
)
from dali.device.helpers import check_bad_rsp
from dali.exceptions import DALISequenceError, ProgramShortAddressFailure
from dali.sequences import progress, sleep


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


def query_input_value(
    device: DeviceShort,
    instance: InstanceNumber,
    resolution: Optional[int] = None
) -> Generator[Command, Optional[Response], Optional[int]]:
    """
    A generator sequence to retrieve full sensor value from a part-103 control device.
    Use with an appropriate DALI driver instance, through the `run_sequence()`
    method.

    :param device: A DeviceShort address to target
    :param instance: An InstanceNumber to target
    :param resolution: Number of valid bits that the device provides
    """
    # Although the proper types are expected, ints are common enough for
    # addresses and their meaning is unambiguous in this context
    if isinstance(device, int):
        device = DeviceShort(device)
    if isinstance(instance, int):
        instance = InstanceNumber(instance)

    if resolution is None:
        resolution = yield QueryResolution(device, instance)
        if check_bad_rsp(resolution):
            raise DALISequenceError("query_input_value: QueryResolution failed")
        resolution = resolution.value

    value = yield QueryInputValue(device, instance)
    if check_bad_rsp(value):
        raise DALISequenceError("query_input_value: QueryInputValue failed")
    value = value.value
    while resolution > 8:
        resolution -= 8
        value <<= 8
        chunk = yield QueryInputValueLatch(device, instance)
        if check_bad_rsp(chunk):
            raise DALISequenceError("query_input_value: QueryInputValueLatch failed")
        value += chunk.value

    if resolution > 0:
        # Strip the repeated trailing bytes as per IEC 62386-103:2014, part 9.7.2
        value >>= 8 - resolution

    return value

def _find_next(low, high):
    yield SearchAddrH((high >> 16) & 0xff)
    yield SearchAddrM((high >> 8) & 0xff)
    yield SearchAddrL(high & 0xff)

    r = yield Compare()

    if low == high:
        if r.value is True:
            return "clash" if r.raw_value.error else low
        return

    if r.value is True:
        midpoint = (low + high) // 2
        res = yield from _find_next(low, midpoint)
        if res is not None:
            return res
        return (yield from _find_next(midpoint + 1, high))


def Commissioning(available_addresses=None, readdress=False,
                  dry_run=False):
    """Assign short addresses to control gear

    If available_addresses is passed, only the specified addresses
    will be assigned; otherwise all short addresses are considered to
    be available.

    if "readdress" is set, all existing short addresses will be
    cleared; otherwise, only control gear that is currently
    unaddressed will have short addresses assigned.

    If "dry_run" is set then no short addresses will actually be set.
    This can be useful for testing.
    """
    if available_addresses is None:
        available_addresses = list(range(64))
    else:
        available_addresses = list(available_addresses)

    if readdress:
        if dry_run:
            yield progress(message="dry_run is set: not deleting existing "
                           "short addresses")
        else:
            yield DTR0(255)
            yield SetShortAddress(DeviceBroadcast())
    else:
        # We need to know which short addresses are already in use
        for a in range(0, 64):
            if a in available_addresses:
                in_use = yield QueryDeviceStatus(DeviceShort(a))
                if in_use.raw_value is not None:
                    available_addresses.remove(a)
        yield progress(
            message=f"Available addresses: {available_addresses}")

    yield Terminate()
    yield Initialise(0xff if readdress else 0x7f)

    finished = False
    # We loop here to cope with multiple devices picking the same
    # random search address; when we discover that, we
    # re-randomise and begin again.  Devices that have already
    # received addresses are unaffected.
    while not finished:
        yield Randomise()
        # Randomise can take up to 100ms
        yield sleep(0.1)

        low = 0
        high = 0xffffff

        while low is not None:
            yield progress(completed=low, size=high)
            low = yield from _find_next(low, high)
            if low == "clash":
                yield progress(message="Multiple ballasts picked the same "
                               "random address; restarting")
                break
            if low is None:
                finished = True
                break
            yield progress(
                message=f"Ballast found at address {low:#x}")
            if available_addresses:
                new_addr = available_addresses.pop(0)
                if dry_run:
                    yield progress(
                        message="Not programming short address "
                        f"{new_addr} because dry_run is set")
                else:
                    yield progress(
                        message=f"Programming short address {new_addr}")
                    yield ProgramShortAddress(new_addr)
                    r = yield VerifyShortAddress(new_addr)
                    if r.value is not True:
                        raise ProgramShortAddressFailure(new_addr)
            else:
                yield progress(
                    message="Device found but no short addresses left")
            yield Withdraw()
            if low < high:
                low = low + 1
            else:
                low = None
                finished = True
    yield Terminate()
    yield progress(message="Addressing complete")
