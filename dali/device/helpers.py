"""
Helper functions and classes, used in various other places through the library
"""
from __future__ import annotations

import types
from typing import Generator, Iterable, Optional

from dali.address import DeviceBroadcast, DeviceShort, InstanceNumber
from dali.command import Command, Response
from dali.device.general import (
    QueryDeviceStatus,
    QueryDeviceStatusResponse,
    QueryInstanceEnabled,
    QueryInstanceType,
    QueryNumberOfInstances,
    StartQuiescentMode,
    StopQuiescentMode,
)
from dali.exceptions import MissingResponse, ResponseError
from dali.frame import BackwardFrameError
from dali.sequences import progress as seq_progress


def check_bad_rsp(r: Response | None) -> bool:
    """
    Checks if a response is "bad", i.e. if it is missing, is an error, or does
    not have a value when one is expected.

    :param r: A Response object to check
    :return: A boolean, True if the response is "bad"
    """
    if not r:
        return True
    if isinstance(r.raw_value, BackwardFrameError):
        return True
    try:
        # The 'value' property raises an exception if a value is expected but
        # not present (except for NumericResponse)
        val = r.value
        # A NumericResponse uses strings to indicate error state
        if isinstance(val, str):
            if "missing" in val:
                return True
            if "framing error" in val:
                return True
    except (MissingResponse, ResponseError):
        return True

    return False


class DeviceInstanceTypeMapper:
    """
    Part 103 defines five different event message addressing schemes, as per
    Table 8 of IEC 62386.103. These are: "Instance", "Device",
    "Device/Instance", "Device Group" and "Instance Group". Four of these
    only rely on data contained within the message itself, however the
    "Device/Instance" addressing scheme does not include information in the
    24 bits of the message to indicate the instance type - which means that
    without further knowledge it is not possible to decode these messages.

    DeviceInstanceTypeMapper stores a mapping from the address and instance
    number of a device to the instance type, thus allowing a higher-level
    system to decode "Device/Instance" messages.

    One instance of DeviceInstanceTypeMapper should be created for each DALI
    bus, and then re-used whenever decoding event messages from that bus
    through the `from_frame()` method.
    """

    def __init__(self, initial=None):
        """
        Creates a new DeviceInstanceTypeMapper object, optionally with
        preloaded mappings as defined by `initial`.

        :param initial: A dict of data to preload into the mapping
        """
        self._mapping: dict[(int, int), int] = {}
        if initial:
            self._mapping = initial

    @property
    def mapping(self) -> dict[(int, int), int]:
        return self._mapping

    def autodiscover(
        self, addresses: int | tuple[int, int] | Iterable[int] = (0, 63)
    ) -> Generator[Command, Response, None]:
        """
        A generator sequence to scan a DALI bus for control device instances,
        and query their types. This information is stored within this
        DeviceInstanceTypeMapper, for use in decoding "Device/Instance" event
        messages.

        :param addresses: Optional specifier of which addresses to scan. Can
        either be a single int, in which case all addresses from zero to that
        value will be scanned; or can be a tuple in the form (start, end), in
        which case all addresses between the provided values will be scanned;
        or finally can be an iterable of ints in which case each address, in
        the iterator will be scanned.
        :return: A generator function, to use with e.g. `driver.run_sequence()`

        Needs to be used through an appropriate driver, with `run_sequence()`,
        for example:
        ```
        dev_inst_map = DeviceInstanceTypeMapper()
        await driver.run_sequence(dev_inst_map.autodiscover())
        ```
        """

        # Use quiescent mode to reduce bus contention from input devices
        yield StartQuiescentMode(DeviceBroadcast())

        if isinstance(addresses, int):
            addresses = (n for n in range(0, addresses))
        elif isinstance(addresses, tuple) and len(addresses) == 2:
            addresses = (n for n in range(addresses[0], addresses[1] + 1))

        for addr_int in addresses:
            addr = DeviceShort(addr_int)

            # Check that the device exists and responds
            rsp = yield QueryDeviceStatus(device=addr)
            if check_bad_rsp(rsp):
                continue
            if isinstance(rsp, QueryDeviceStatusResponse):
                # Make sure the status is OK
                if (
                    rsp.input_device_error
                    or rsp.short_address_is_mask
                    or rsp.reset_state
                ):
                    continue
            else:
                # If the response isn't QueryDeviceStatusResponse then
                # something is wrong
                continue

            # Find out how many instances the device has
            rsp = yield QueryNumberOfInstances(device=addr)
            if check_bad_rsp(rsp):
                continue
            num_inst = rsp.value

            # For each instance, check it is enabled and then query the type
            for inst_int in range(num_inst):
                inst = InstanceNumber(inst_int)
                rsp = yield QueryInstanceEnabled(device=addr, instance=inst)
                if check_bad_rsp(rsp):
                    continue
                if not rsp.value:
                    # Skip if not enabled
                    continue
                rsp = yield QueryInstanceType(device=addr, instance=inst)
                if check_bad_rsp(rsp):
                    continue

                yield seq_progress(
                    message=f"A²{addr_int} I{inst_int} type: {rsp.value}"
                )

                # Add the type to the device/instance map
                self.add_type(
                    short_address=addr,
                    instance_number=inst,
                    instance_type=rsp.value,
                )

        # End quiescent mode
        yield StopQuiescentMode(DeviceBroadcast())

    def add_type(
        self,
        *,
        short_address: DeviceShort | int,
        instance_number: InstanceNumber | int,
        instance_type: types.ModuleType | int,
    ) -> None:
        """
        Adds a mapping from device address and instance number to instance
        type, so that the "Device/Instance" addressing scheme can be used for
        event messages. Using this method will enable Device/Instance
        messages to be decoded properly, instead of returning the default
        `AmbiguousInstanceType` The * barrier means that arguments must be
        named, this is to avoid accidental ambiguity.

        :param short_address: Integer or `DeviceShort` of the relevant address
        :param instance_number: Integer or `InstanceNumber` of the relevant
        instance number
        :param instance_type: Either an integer corresponding to the instance
        type, e.g. 1 for "Part 301", or the module name that implements the type
         e.g. "device.pushbutton" (which internally has a property
         `instance_type`)
        :return: None
        """
        if isinstance(short_address, DeviceShort):
            short_address = short_address.address
        if isinstance(instance_number, InstanceNumber):
            instance_number = instance_number.value
        if hasattr(instance_type, "instance_type"):
            instance_type = int(instance_type.instance_type)
        else:
            instance_type = int(instance_type)
        self._mapping[(short_address, instance_number)] = instance_type

    def get_type(
        self,
        *,
        short_address: DeviceShort | int,
        instance_number: InstanceNumber | int,
    ) -> Optional[int]:
        """
        Looks up the instance type based on the short address and instance
        number. Only works if this has previously been added through a call
        to `add_type()`. The * barrier means that arguments must be named,
        this is to avoid accidental ambiguity.

        :param short_address: Integer or `DeviceShort` of the relevant address
        :param instance_number: Integer or `InstanceNumber` of the relevant
        instance number
        :return: Either the instance type as an integer, or None
        """
        if isinstance(short_address, DeviceShort):
            short_address = short_address.address
        if isinstance(instance_number, InstanceNumber):
            instance_number = instance_number.value
        return self._mapping.get((short_address, instance_number), None)

    def clear(self) -> None:
        """
        Unconditionally clears all mappings

        :return: None
        """
        self._mapping = {}

    def __repr__(self):
        return f"{self.__class__.__name__}({self._mapping})"
