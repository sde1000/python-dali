"""
Sequence for simplifying certain interactions with 24-bit DALI devices
"""
from __future__ import annotations

from typing import Generator, Iterable, Optional

from dali import address, command, sequences
from dali.device.general import (
    DTR0,
    DeviceStatus,
    EventScheme,
    QueryDeviceStatus,
    QueryDeviceStatusResponse,
    QueryEventScheme,
    QueryEventSchemeResponse,
    QueryInstanceEnabled,
    QueryInstanceType,
    QueryNumberOfInstances,
    SetEventFilter,
    SetEventScheme,
    device_instance_map,
)
from dali.device.pushbutton import (
    EventFilterPushbutton,
    QueryEventFilterPushbutton,
    QueryEventFilterPushbuttonResponse,
)


def SetEventSchemes(
    device: address.Short,
    instance: address.InstanceNumber,
    scheme: EventScheme,
) -> Generator[
    command.Command,
    Optional[command.Response],
    Optional[QueryEventSchemeResponse],
]:
    """
    A generator sequence to set the event scheme of a device instance. Use with an
    appropriate DALI driver instance, through the `run_sequence()` method.

    Returns the event scheme that the target instance actually set.

    Example:
    ```
    await driver.run_sequence(
        SetEventSchemes(
            device=address.Short(1),
            instance=address.InstanceNumber(2),
            scheme=EventScheme.device_instance,
        )
    )
    ```
    """
    # Although the proper types are expected, ints are common enough for addresses
    # and their meaning is unambiguous in this context
    if isinstance(device, int):
        device = address.Short(device)
    if isinstance(instance, int):
        instance = address.InstanceNumber(instance)

    # The values in EventScheme are mapped by value, only one can be set at a time
    if not isinstance(scheme, EventScheme):
        raise ValueError("'scheme' must be an EventScheme enum value")

    pos = scheme.position
    if not isinstance(pos, int):
        raise RuntimeError(f"Somehow got an invalid EventScheme position: {pos}")

    rsp = yield DTR0(pos)
    if rsp is not None:
        return

    rsp = yield SetEventScheme(device=device, instance=instance)
    if rsp is not None:
        return

    rsp = yield QueryEventScheme(device=device, instance=instance)
    return rsp


def DiscoverInstanceTypes(
    address_count: int = 63,
) -> Generator[command.Command, command.Response, None,]:
    """
    A generator sequence to scan a DALI bus for control device instances, and query
    their types. This information is added to the `device_instance_map`, for use in
    decoding "Device/Instance" event messages.

    Example:
    ```
    await driver.run_sequence(DiscoverInstanceTypes())
    ```
    """

    def check_bad_rsp(r: command.Response) -> bool:
        if not r:
            return True
        if not r.raw_value:
            return True
        return False

    for addr_int in range(address_count):
        addr = address.Short(addr_int)

        # Check that the device exists and responds
        rsp = yield QueryDeviceStatus(device=addr)
        if check_bad_rsp(rsp):
            continue
        if isinstance(rsp, QueryDeviceStatusResponse):
            # Make sure the status is OK
            if (
                DeviceStatus.input_device_error in rsp.status
                or DeviceStatus.quiescent_mode in rsp.status
                or DeviceStatus.address_masked in rsp.status
                or DeviceStatus.reset_state in rsp.status
            ):
                continue
        else:
            # If the response isn't QueryDeviceStatusResponse then something is wrong
            continue

        # Find out how many instances the device has
        rsp = yield QueryNumberOfInstances(device=addr)
        if check_bad_rsp(rsp):
            continue
        num_inst = rsp.value

        # For each instance, check it is enabled and then query the type
        for inst_int in range(num_inst):
            inst = address.InstanceNumber(inst_int)
            rsp = yield QueryInstanceEnabled(device=addr, instance=inst)
            if check_bad_rsp(rsp):
                continue
            if not rsp.value:
                # Skip if not enabled
                continue
            rsp = yield QueryInstanceType(device=addr, instance=inst)
            if check_bad_rsp(rsp):
                continue

            yield sequences.progress(
                message=f"A²{addr_int} I{inst_int} type: {rsp.value}"
            )

            # Add the type to the device/instance map
            device_instance_map.add_type(
                short_address=addr,
                instance_number=inst_int,
                instance_type=rsp.value,
            )


def SetPushbuttonEventFilters(
    device: address.Short,
    instance: address.InstanceNumber,
    filters: Iterable[EventFilterPushbutton],
) -> Generator[
    command.Command,
    Optional[command.Response],
    Optional[QueryEventFilterPushbuttonResponse],
]:
    """
    A generator sequence to set the event filters of a push button instance. Use with
    an appropriate DALI driver instance, through the `run_sequence()` method.

    Returns the list of event filters that the target device actually set.

    Example:
    ```
        await driver.run_sequence(
            SetPushbuttonEventFilters(
                device=address.Short(1),
                instance=address.InstanceNumber(2),
                filters=(
                    EventFilterPushbutton.short_press,
                    EventFilterPushbutton.double_press,
                )
            )
        )
    ```
    """
    # Although the proper types are expected, ints are common enough for addresses
    # and their meaning is unambiguous in this context
    if isinstance(device, int):
        device = address.Short(device)
    if isinstance(instance, int):
        instance = address.InstanceNumber(instance)

    # The values in EventFilterPushbutton are a bit map, the position indicates which
    # bit to set
    bits = 0
    for f in filters:
        if not isinstance(f, EventFilterPushbutton):
            raise ValueError(
                "'filters' must be an iterable of EventFilterPushbutton enum values, "
                f"not {type(f)}"
            )
        bits |= 1 << f.position

    rsp = yield DTR0(bits)
    if rsp is not None:
        return

    rsp = yield SetEventFilter(device=device, instance=instance)
    if rsp is not None:
        return

    rsp = yield QueryEventFilterPushbutton(device=device, instance=instance)
    return rsp
