"""
Sequence for simplifying certain interactions with 24-bit DALI devices
"""
from __future__ import annotations

from typing import Generator, Optional, Literal, Iterable
import inspect

from dali.address import DeviceBroadcast, DeviceShort, InstanceNumber
from dali.command import Command, Response
from dali.device.general import (
    DTR0,
    DTR1,
    DTR2,
    Compare,
    EventScheme,
    Initialise,
    InstanceEventFilter,
    ProgramShortAddress,
    QueryDeviceStatus,
    QueryResolution,
    QueryInputValue,
    QueryInputValueLatch,
    QueryEventFilterH,
    QueryEventFilterL,
    QueryEventFilterM,
    QueryEventScheme,
    QueryEventSchemeResponse,
    Randomise,
    SearchAddrH,
    SearchAddrL,
    SearchAddrM,
    SetEventFilter,
    SetEventScheme,
    SetShortAddress,
    StartQuiescentMode,
    StopQuiescentMode,
    Terminate,
    VerifyShortAddress,
    Withdraw,
)
from dali.exceptions import DALISequenceError, ProgramShortAddressFailure
from dali.sequences import progress, sleep


def SetEventSchemes(
    device: DeviceShort | int,
    instance: InstanceNumber | int,
    scheme: EventScheme,
) -> Generator[
    Command,
    Optional[Response],
    QueryEventSchemeResponse,
]:
    """
    A generator sequence to set the event scheme of a device instance. Use
    with an appropriate DALI driver instance, through the `run_sequence()`
    method.

    Returns the event scheme that the target instance actually set.

    Example:
    ```
    await driver.send(
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

    yield DTR0(pos)

    yield SetEventScheme(device=device, instance=instance)

    rsp = yield QueryEventScheme(device=device, instance=instance)
    assert isinstance(rsp, QueryEventScheme.response)
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

    await driver.send(
        SetEventFilters(
            device=address.DeviceShort(1),
            instance=address.InstanceNumber(2),
            filter_value=filter_pb.short_press | filter_pb.double_press,
        )
    )
    ```
    """
    if not isinstance(filter_value, InstanceEventFilter):
        raise TypeError(
            f"'filter_value' must be an InstanceEventFilter, not "
            f"{type(filter_value)}"
        )
    # Although the proper types are expected, ints are common enough for
    # addresses and their meaning is unambiguous in this context
    if isinstance(device, int):
        device = DeviceShort(device)
    if isinstance(instance, int):
        instance = InstanceNumber(instance)

    uses_dtr1 = filter_value.dali_width() > 8
    uses_dtr2 = filter_value.dali_width() > 16

    # The values in InstanceEventFilter are already mapped out to the
    # corresponding bits, through the inheritance from IntFlag
    lo, md, hi = filter_value.to_bytes(3, "little")

    # Set the various values into the DTRs
    yield DTR0(lo)
    if uses_dtr1:
        yield DTR1(md)
    if uses_dtr2:
        yield DTR2(hi)
    # Set the filters
    yield SetEventFilter(device=device, instance=instance)

    # Read back the values that were set
    rsp = yield QueryEventFilterL(device=device, instance=instance)
    assert isinstance(rsp, QueryEventFilterL.response)
    if not rsp.valid:
        return None  # XXX Should we be raising an exception here?
    lo = rsp.as_integer
    if uses_dtr1:
        rsp = yield QueryEventFilterM(device=device, instance=instance)
        assert isinstance(rsp, QueryEventFilterM.response)
        if not rsp.valid:
            return None
        md = rsp.as_integer
    if uses_dtr2:
        rsp = yield QueryEventFilterH(device=device, instance=instance)
        assert isinstance(rsp, QueryEventFilterH.response)
        if not rsp.valid:
            return None
        hi = rsp.as_integer

    return filter_value.__class__(int.from_bytes((lo, md, hi), "little"))


def QueryEventFilters(
    device: DeviceShort | int,
    instance: InstanceNumber | int,
    filter_type: type[InstanceEventFilter],
) -> Generator[Command, Optional[Response], Optional[InstanceEventFilter]]:
    """
    A generator sequence to query the event filters of a device instance.
    Use with an appropriate DALI driver instance, through the `run_sequence()`
    method.

    Returns the event filters used by the target device.

    :param device: A DeviceShort address to target
    :param instance: An InstanceNumber to target
    :param filter_type: An InstanceEventFilter type to use, e.g.
    `dali.device.pushbutton.InstanceEventFilter`
    :return: A generator function, to use with e.g. `driver.run_sequence()`

    Example:
    ```
    from dali import address
    from dali.device import pushbutton

    await driver.send(
        QueryEventFilters(
            device=address.DeviceShort(1),
            instance=address.InstanceNumber(2),
            filter_type=pushbutton,
        )
    )
    ```
    """
    # Deprecated support for passing a module as filter_type
    if inspect.ismodule(filter_type):
        if hasattr(filter_type, "InstanceEventFilter"):
            filter_type = getattr(filter_type, "InstanceEventFilter")
        else:
            raise TypeError(
                "If 'filter_type' is a module, it must have an "
                "InstanceEventFilter attribute")

    if not issubclass(filter_type, InstanceEventFilter):
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
    assert isinstance(rsp, QueryEventFilterL.response)
    if not rsp.valid:
        return None  # should we raise an exception instead?
    lo = rsp.as_integer
    if filter_type.dali_width() > 8:
        rsp = yield QueryEventFilterM(device=device, instance=instance)
        assert isinstance(rsp, QueryEventFilterM.response)
        if not rsp.valid:
            return None
        md = rsp.as_integer
    if filter_type.dali_width() > 16:
        rsp = yield QueryEventFilterH(device=device, instance=instance)
        assert isinstance(rsp, QueryEventFilterH.response)
        if not rsp.valid:
            return None
        hi = rsp.as_integer

    return filter_type(int.from_bytes((lo, md, hi), "little"))


def query_input_value(
    device: DeviceShort,
    instance: InstanceNumber,
    resolution: Optional[int] = None
) -> Generator[Command, Optional[Response], int]:
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
        rsp = yield QueryResolution(device, instance)
        assert isinstance(rsp, QueryResolution.response)
        if not rsp.valid:
            raise DALISequenceError("query_input_value: QueryResolution failed")
        resolution = rsp.as_integer

    rsp = yield QueryInputValue(device, instance)
    assert isinstance(rsp, QueryInputValue.response)
    if not rsp.valid:
        raise DALISequenceError("query_input_value: QueryInputValue failed")
    value = rsp.as_integer
    while resolution > 8:
        resolution -= 8
        value <<= 8
        rsp = yield QueryInputValueLatch(device, instance)
        assert isinstance(rsp, QueryInputValueLatch.response)
        if not rsp.valid:
            raise DALISequenceError("query_input_value: QueryInputValueLatch failed")
        value += rsp.as_integer

    if resolution > 0:
        # Strip the repeated trailing bytes as per IEC 62386-103:2014, part 9.7.2
        value >>= 8 - resolution

    return value


# INITIALISE data byte values for control devices, from IEC 62386-103:2014
# Table 21. Unlike control gear (part 102), devices use 0xff for "all" and
# 0x7f for "no short address" (short address == MASK).
_INITIALISE_ALL = 0xFF
_INITIALISE_UNADDRESSED = 0x7F


def _find_next(
    low: int, high: int
) -> Generator[Command, Optional[Response], Optional[Literal["clash"] | int]]:
    """Binary search the 24-bit random address space for a responding device.

    Returns the random address of the device with the lowest address in the
    ``low..high`` range, ``"clash"`` if two devices share the current address,
    or ``None`` if no device answers in the range.
    """
    yield SearchAddrH((high >> 16) & 0xFF)
    yield SearchAddrM((high >> 8) & 0xFF)
    yield SearchAddrL(high & 0xFF)

    r = yield Compare()
    assert isinstance(r, Compare.response)

    if low == high:
        if r.as_boolean is True:
            return "clash" if r.raw_value and r.raw_value.error else low
        return None

    if r.as_boolean is True:
        midpoint = (low + high) // 2
        res = yield from _find_next(low, midpoint)
        if res is not None:
            return res
        return (yield from _find_next(midpoint + 1, high))

    return None


def Commissioning(
    available_addresses: Optional[Iterable[int]] = None,
    readdress: bool = False,
    dry_run: bool = False,
) -> Generator[Command | sleep | progress, Optional[Response],
               list[DeviceShort]]:
    """Assign short addresses to 24-bit (part 103) control devices.

    This mirrors :func:`dali.sequences.Commissioning` for control gear, using
    the part 103 addressing commands. Use with an appropriate DALI driver
    instance, through its ``run_sequence()`` method.

    The bus is placed in quiescent mode for the duration so that spontaneous
    event messages do not collide with the addressing backward frames.

    :param available_addresses: If passed, only these short addresses will be
        assigned; otherwise all 64 short addresses are considered available.
    :param readdress: If set, all existing short addresses are cleared first
        and every device is readdressed; otherwise only devices that are
        currently unaddressed are assigned a short address.
    :param dry_run: If set, no short addresses are actually programmed. Useful
        for testing the search without altering the bus.
    :return: The list of short addresses in use after the sequence completes.
    """
    used_addresses: list[DeviceShort] = []
    if available_addresses is None:
        available_addresses = list(range(64))
    else:
        available_addresses = list(available_addresses)

    if readdress:
        if dry_run:
            yield progress(
                message="dry_run is set: not deleting existing short addresses"
            )
        else:
            yield DTR0(255)
            yield SetShortAddress(DeviceBroadcast())
    else:
        # Devices that already have a short address answer QueryDeviceStatus at
        # that address, so those addresses are considered already in use.
        for a in list(available_addresses):
            in_use = yield QueryDeviceStatus(DeviceShort(a))
            assert isinstance(in_use, QueryDeviceStatus.response)
            if in_use.valid:
                available_addresses.remove(a)
                used_addresses.append(DeviceShort(a))
        yield progress(message=f"Available addresses: {available_addresses}")

    yield Terminate()
    yield StartQuiescentMode(DeviceBroadcast())
    yield Initialise(_INITIALISE_ALL if readdress else _INITIALISE_UNADDRESSED)

    # A verify failure must still leave the bus addressable, so the error is
    # recorded and raised only after quiescent mode has been exited below;
    # yielding during exception unwinding is unsafe because the sequence runner
    # closes the generator via GeneratorExit on failure.
    failed_address: Optional[int] = None
    finished = False
    # Loop to cope with multiple devices picking the same random search
    # address; when that clash is detected we re-randomise and begin again.
    # Devices that already received addresses are unaffected.
    while not finished:
        yield Randomise()
        # Randomise can take up to 200ms to settle.
        yield sleep(0.2)

        low: Optional[int] = 0
        high = 0xFFFFFF

        while low is not None:
            yield progress(completed=low, size=high)
            new_low = yield from _find_next(low, high)
            if new_low == "clash":
                yield progress(message="Multiple ballasts picked the same "
                               "random address; restarting")
                break
            elif new_low is None:
                low = None
                finished = True
                break
            else:
                low = new_low
            yield progress(message=f"Device found at address {low:#x}")
            if available_addresses:
                new_addr = available_addresses.pop(0)
                if dry_run:
                    yield progress(
                        message="Not programming short address "
                        f"{new_addr} because dry_run is set"
                    )
                else:
                    yield progress(
                        message=f"Programming short address {new_addr}"
                    )
                    yield ProgramShortAddress(new_addr)
                    r = yield VerifyShortAddress(new_addr)
                    assert isinstance(r, VerifyShortAddress.response)
                    if r.as_boolean is not True:
                        failed_address = new_addr
                        finished = True
                        break
                    used_addresses.append(DeviceShort(new_addr))
            else:
                yield progress(
                    message="Device found but no short addresses left"
                )
            yield Withdraw()
            if low < high:
                low = low + 1
            else:
                low = None
                finished = True

    yield Terminate()
    yield StopQuiescentMode(DeviceBroadcast())

    if failed_address is not None:
        raise ProgramShortAddressFailure(failed_address)

    yield progress(message="Addressing complete")
    return used_addresses
