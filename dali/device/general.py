"""Commands, responses and events from IEC 62386 part 103.

Command names are given in the standard in ALL CAPS.  They have been
converted to CamelCase here, for example ALL CAPS -> AllCaps.

Where a command name is or contains an abbreviation, for example DAPC
or DTR0, the abbreviation has been kept in capitals.

Part 103 refers to application controllers and input devices.

An application controller is the part of the control system that makes
the system "work".  Its functions include commissioning and
configuring the system, reacting to changes in the environment based
on information coming from input devices, and changing the behaviour
of control gear using commands defined in part 102.

A control device that includes an application controller has variable
"applicationControllerPresent" set to True; this can be read through
QueryDeviceCapabilities().

Input devices make a system sensitive to changes in its environment by
transmitting event messages.

Input devices have between 1 and 32 "instances"; variable
"numberOfInstances" can be queried using QueryNumberOfInstances().
Control devices that are only application controllers have
numberOfInstances == 0.

Instances have:

 * a number in the range 0..numberOfInstances-1.

 * a type in the range 0..31.  Instance types 1..31 are described in
   IEC 62386 parts 301 to 331.

 * zero or more feature types in the range 32..96.  Feature types are
   described in IEC 62386 parts 332 to 396.

An application controller may define up to 32 "instance groups" which
it may use to address multiple instances at once.  Instances can be
members of up to three instance groups.


Event messages are supported as per part 103, with specific event types implemented
in relevant submodules, e.g. pushbutton.py for part 301.

Messages which have no implementation will still be decoded, but will be interpreted
as an "UnknownEvent" object.

Part 103 defines five different event message addressing schemes, as per Table 8 of
IEC 62386.103. Four of these only rely on data contained within the message itself,
however the "Device/Instance" addressing scheme does not include information in the
24 bits of the message to indicate the instance type - which means that without
further knowledge it is not possible to decode these messages. By default, these
message types will be decoded as an "AmbiguousInstanceType" object. If there is some
higher-level system managing the DALI bus which is able to query and learn the instance
type of any relevant instances, there is a function `add_type()` which can be used to
create a mapping from a device address and instance number to a known instance type.
It is used like so:

```
from dali import device

device.device_instance_map.add_type(
    short_address=1,
    instance_number=1,
    instance_type=device.pushbutton
)
```

There is also a sequence which will scan the DALI bus and learn the types of all
enabled instances, `SequenceDiscoverInstanceTypes()`.
"""
from __future__ import annotations

import types
from enum import Enum
from typing import Dict, Optional, Type, Union

from dali import address, command, frame


class _DeviceCommand(command.Command):
    """A command addressed to a control device."""
    _framesize = 24
    # Some subclasses have been defined as wrappers around "real" message types, to
    # assist with decoding responses from control devices correctly. These subclasses
    # aren't actual messages types and shouldn't ever be decoded as such.
    no_register = False

    _devicecommands = []

    @classmethod
    def _register_subclass(cls, subclass):
        # Don't register the subclass if it asks not to be
        if not subclass.no_register:
            cls._devicecommands.append(subclass)

    @classmethod
    def from_frame(cls, f, devicetype=0):
        for dc in cls._devicecommands:
            r = dc.from_frame(f)
            if r:
                return r
        return UnknownDeviceCommand(f)


class UnknownDeviceCommand(_DeviceCommand):
    """An unknown command addressed to a control device.
    """
    @classmethod
    def from_frame(cls, f):
        return


class DeviceEnum(str, Enum):
    """
    Defines an enumeration for device command mappings, both bit maps and value maps
    """

    @property
    def position(self) -> int:
        """
        Returns the numeric index of this value, based on where it is defined in the
        enumeration class
        """
        return list(self.__class__).index(self)


###############################################################################
# Commands from Table 21 start here
###############################################################################


class _StandardDeviceCommand(_DeviceCommand):
    """A standard command addressed to a control device.

    A command defined in Table 21 of IEC 62386-103 where the instance
    byte (bits 15:8) is set to 0xfe to indicate the command is
    addressed to the device as a whole, not to any particular
    instance.
    """
    _opcode = None

    def __init__(self, device):
        if self._opcode is None:
            raise NotImplementedError

        self.destination = self._check_destination(device)

        f = frame.ForwardFrame(24, 0x1fe00 | self._opcode)
        self.destination.add_to_frame(f)

        super().__init__(f)

    _opcodes = {}

    @classmethod
    def _register_subclass(cls, subclass):
        # Don't register the subclass if it asks not to be
        if not subclass.no_register:
            cls._opcodes[subclass._opcode] = subclass

    @classmethod
    def from_frame(cls, frame):
        if frame[16:8] != 0x1fe:
            return

        addr = address.from_frame(frame)

        if addr is None:
            return

        cc = cls._opcodes.get(frame[7:0])
        if not cc:
            return UnknownDeviceCommand(frame)

        return cc(addr)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.destination)


class IdentifyDevice(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x00


class ResetPowerCycleSeen(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x01


class Reset(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x10


class ResetMemoryBank(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x11


class SetShortAddress(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x14


class EnableWriteMemory(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x15


class EnableApplicationController(_StandardDeviceCommand):
    appctrl = True
    sendtwice = True
    _opcode = 0x16


class DisableApplicationController(_StandardDeviceCommand):
    appctrl = True
    sendtwice = True
    _opcode = 0x17


class SetOperatingMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x18


class AddToDeviceGroupsZeroToFifteen(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr1 = True
    uses_dtr2 = True
    sendtwice = True
    _opcode = 0x19


class AddToDeviceGroupsSixteenToThirtyOne(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr1 = True
    uses_dtr2 = True
    sendtwice = True
    _opcode = 0x1a


class RemoveFromDeviceGroupsZeroToFifteen(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr1 = True
    uses_dtr2 = True
    sendtwice = True
    _opcode = 0x1b


class RemoveFromDeviceGroupsSixteenToThirtyOne(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr1 = True
    uses_dtr2 = True
    sendtwice = True
    _opcode = 0x1c


class StartQuiescentMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x1d


class StopQuiescentMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x1e


class EnablePowerCycleNotification(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x1f


class DisablePowerCycleNotification(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x20


class SavePersistentVariables(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x21


class DeviceStatus(DeviceEnum):
    """
    Device Status response values, as defined in Part 103 Table 15. The order of the
    values below correspond to the bit position in the bitmask, from 0 to 6.
    """

    input_device_error = "Input Device error"
    quiescent_mode = "Quiescent Mode enabled"
    address_masked = "Short Address is MASK"
    app_control_active = "Application Controller is active"
    app_control_error = "Application Controller error"
    power_cycle_seen = "Power Cycle seen"
    reset_state = "Reset state"


class QueryDeviceStatusResponse(command.BitmapResponse):
    """
    A response object corresponding to a QueryDeviceStatus message. Internally uses the
    DeviceStatus enum, i.e. the `status` attribute will be a list of values from this
    enum.
    """

    bits = list(DeviceStatus)


class QueryDeviceStatus(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = QueryDeviceStatusResponse
    _opcode = 0x30


class QueryApplicationControllerError(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponseMask
    _opcode = 0x31


class QueryInputDeviceError(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponseMask
    _opcode = 0x32


class QueryMissingShortAddress(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x33


class QueryVersionNumber(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x34


class QueryNumberOfInstances(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x35


class QueryContentDTR0(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr0 = True
    response = command.NumericResponse
    _opcode = 0x36


class QueryContentDTR1(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr1 = True
    response = command.NumericResponse
    _opcode = 0x37


class QueryContentDTR2(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr2 = True
    response = command.NumericResponse
    _opcode = 0x38


class QueryRandomAddressH(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x39


class QueryRandomAddressM(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x3a


class QueryRandomAddressL(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x3b


class ReadMemoryLocation(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr0 = True
    uses_dtr1 = True
    response = command.NumericResponse
    _opcode = 0x3c


class QueryApplicationControlEnabled(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x3d


class QueryOperatingMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x3e


class QueryManufacturerSpecificMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x3f


class QueryQuiescentMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x40


class QueryDeviceGroupsZeroToSeven(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x41


class QueryDeviceGroupsEightToFifteen(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x42


class QueryDeviceGroupsSixteenToTwentyThree(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x43


class QueryDeviceGroupsTwentyFourToThirtyOne(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x44


class QueryPowerCycleNotification(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x45


class QueryDeviceCapabilities(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x46


class QueryExtendedVersionNumber(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr0 = True
    response = command.NumericResponse
    _opcode = 0x47


class QueryResetState(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x48


class _StandardInstanceCommand(_DeviceCommand):
    """A standard command addressed to a control device instance."""
    _opcode = None

    def __init__(self, device, instance):
        if self._opcode is None:
            raise NotImplementedError

        self.destination = self._check_destination(device)
        if not isinstance(instance, address.Instance):
            raise ValueError("instance must be a dali.address.Instance object")
        self.instance = instance

        f = frame.ForwardFrame(24, 0x10000 | self._opcode)
        self.destination.add_to_frame(f)
        self.instance.add_to_frame(f)

        super().__init__(f)

    _opcodes = {}

    @classmethod
    def _register_subclass(cls, subclass):
        # Don't register the subclass if it asks not to be
        if not subclass.no_register:
            cls._opcodes[subclass._opcode] = subclass

    @classmethod
    def from_frame(cls, frame):
        # In 24-bit frames, bit 16 is 1 for "commands" (as opposed to "events")
        if not frame[16]:
            return
        addr = address.from_frame(frame)
        instance = address.instance_from_frame(frame)

        if addr is None or instance is None:
            return

        cc = cls._opcodes.get(frame[7:0])
        if not cc:
            return UnknownDeviceCommand(frame)

        return cc(addr, instance)

    def __str__(self):
        return "{}({}, {})".format(
            self.__class__.__name__, self.destination, self.instance)


class SetEventPriority(_StandardInstanceCommand):
    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x61


class EnableInstance(_StandardInstanceCommand):
    inputdev = True
    sendtwice = True
    _opcode = 0x62


class DisableInstance(_StandardInstanceCommand):
    inputdev = True
    sendtwice = True
    _opcode = 0x63


class SetPrimaryInstanceGroup(_StandardInstanceCommand):
    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x64


class SetInstanceGroup1(_StandardInstanceCommand):
    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x65


class SetInstanceGroup2(_StandardInstanceCommand):
    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x66


class SetEventScheme(_StandardInstanceCommand):
    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x67


class SetEventFilter(_StandardInstanceCommand):
    inputdev = True
    uses_dtr0 = True
    uses_dtr1 = True
    uses_dtr2 = True
    sendtwice = True
    _opcode = 0x68


class QueryInstanceType(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x80


class QueryResolution(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x81


class QueryInstanceError(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x82


class QueryInstanceStatus(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x83


class QueryEventPriority(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x84


class QueryInstanceEnabled(_StandardInstanceCommand):
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x86


class QueryPrimaryInstanceGroup(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x88


class QueryInstanceGroup1(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x89


class QueryInstanceGroup2(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x8a


class EventScheme(DeviceEnum):
    """
    Event Address Scheme setting values, as defined in Part 103 Table 8. The order of
    the values below correspond to the numeric value of the scheme, from 0 to 4. Used
    in both QueryEventScheme and SetEventScheme (e.g. via SequenceSetEventScheme).
    """

    instance = "Instance"
    device = "Device"
    device_instance = "Device/Instance"
    device_group = "Device Group"
    instance_group = "Instance Group"


class QueryEventSchemeResponse(command.Response):
    """
    A response object corresponding to a QueryEventScheme message. Internally uses the
    EventScheme enum to map from a numeric response to an enum value.
    """

    @property
    def value(self):
        _value = super().value
        if _value:
            return list(EventScheme)[_value.as_integer]
        return _value


class QueryEventScheme(_StandardInstanceCommand):
    inputdev = True
    response = QueryEventSchemeResponse
    _opcode = 0x8B


class QueryInputValue(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x8c


class QueryInputValueLatch(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x8d


class QueryFeatureType(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x8e


class QueryNextFeatureType(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x8f


class QueryEventFilterZeroToSeven(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x90


QueryEventFilterL = QueryEventFilterZeroToSeven


class QueryEventFilterEightToFifteen(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x91


QueryEventFilterM = QueryEventFilterEightToFifteen


class QueryEventFilterSixteenToTwentyThree(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x92


QueryEventFilterH = QueryEventFilterSixteenToTwentyThree


###############################################################################
# Commands from Table 22 start here
###############################################################################


class _SpecialDeviceCommand(_DeviceCommand):
    _addr = None
    _instance = None
    _opcode = 0x00

    def __init__(self):
        if self._addr is None or self._instance is None:
            raise NotImplementedError
        super().__init__(
            frame.ForwardFrame(24, (
                self._addr, self._instance, self._opcode)))

    @classmethod
    def from_frame(cls, frame):
        if cls == _SpecialDeviceCommand:
            return
        if frame[23:16] == cls._addr and frame[15:8] == cls._instance \
           and frame[7:0] == 0x00:
            return cls()

    def __str__(self):
        return "{}()".format(self.__class__.__name__)


class _SpecialDeviceCommandOneParam(_SpecialDeviceCommand):
    def __init__(self, param):
        if not isinstance(param, int):
            raise ValueError("parameter must be an integer")
        if param < 0 or param > 255:
            raise ValueError("parameter must be in the range 0..255")
        self._opcode = param
        super().__init__()

    @classmethod
    def from_frame(cls, frame):
        if cls == _SpecialDeviceCommandOneParam:
            return
        if frame[23:16] == cls._addr and frame[15:8] == cls._instance:
            return cls(frame[7:0])

    def __str__(self):
        return "{}({:02x})".format(self.__class__.__name__, self._opcode)


class _SpecialDeviceCommandTwoParam(_SpecialDeviceCommand):
    def __init__(self, a, b):
        if not isinstance(a, int) or not isinstance(b, int):
            raise ValueError("parameters must be integers")
        if a < 0 or a > 255 or b < 0 or b > 255:
            raise ValueError("parameters must be in the range 0..255")
        self._instance = a
        self._opcode = b
        super().__init__()

    @classmethod
    def from_frame(cls, frame):
        if cls == _SpecialDeviceCommandTwoParam:
            return
        if frame[23:16] == cls._addr:
            return cls(frame[15:8], frame[7:0])

    def __str__(self):
        return "{}({:02x}, {:02x})".format(
            self.__class__.__name__, self._instance, self._opcode)


class Terminate(_SpecialDeviceCommand):
    _addr = 0xc1
    _instance = 0x00


class Initialise(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x01
    sendtwice = True


class Randomise(_SpecialDeviceCommand):
    _addr = 0xc1
    _instance = 0x02
    sendtwice = True


class Compare(_SpecialDeviceCommand):
    _addr = 0xc1
    _instance = 0x03
    response = command.Response


class Withdraw(_SpecialDeviceCommand):
    _addr = 0xc1
    _instance = 0x04


class SearchAddrH(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x05


class SearchAddrM(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x06


class SearchAddrL(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x07


class ProgramShortAddress(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x08


class VerifyShortAddress(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x09
    response = command.Response


class QueryShortAddress(_SpecialDeviceCommand):
    _addr = 0xc1
    _instance = 0x0a
    response = command.Response


class WriteMemoryLocation(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x20
    uses_dtr0 = True
    uses_dtr1 = True
    response = command.Response


class WriteMemoryLocationNoReply(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x21
    uses_dtr0 = True
    uses_dtr1 = True


class DTR0(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x30
    uses_dtr0 = True


class DTR1(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x31
    uses_dtr1 = True


class DTR2(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x32
    uses_dtr2 = True


class SendTestframe(_SpecialDeviceCommandOneParam):
    _addr = 0xc1
    _instance = 0x33
    uses_dtr0 = True
    uses_dtr1 = True
    uses_dtr2 = True


class DirectWriteMemory(_SpecialDeviceCommandTwoParam):
    _addr = 0xc5
    uses_dtr0 = True
    uses_dtr1 = True
    response = command.Response


class DTR1DTR0(_SpecialDeviceCommandTwoParam):
    _addr = 0xc7
    uses_dtr0 = True
    uses_dtr1 = True


class DTR2DTR1(_SpecialDeviceCommandTwoParam):
    _addr = 0xc9
    uses_dtr1 = True
    uses_dtr2 = True


class UnknownEvent(_DeviceCommand):
    """
    A message which is known to be an "event", but has no specific implementation in
    this library
    """

    @classmethod
    def from_frame(cls, f):
        return


class _EventTypeMappingDeviceInstance:
    def __init__(self, initial: Optional[Dict[(int, int), int]] = None):
        """
        NOTE: DO NOT create a new instance of this class, use the one already in the
        `dali.general`, i.e. use `general.device_instance_map.add_type()`, or use the
        sequence `SequenceDiscoverInstanceTypes()`.

        Creates a new _EventTypeMappingDeviceInstance object, optionally with preloaded
        mappings as defined by `initial`.

        :param initial: A dict of data to preload into the mapping
        """
        self._mapping: Dict[(int, int), int] = {}
        if initial:
            self._mapping = initial

    def add_type(
        self,
        *,
        short_address: Union[address.Short, int],
        instance_number: int,
        instance_type: Union[int, types.ModuleType],
    ) -> None:
        """
        Adds a mapping from device address and instance number to instance type, so
        that the "Device/Instance" addressing scheme can be used for event messages.
        Using this method will enable Device/Instance messages to be decoded properly,
        instead of returning the default `AmbiguousInstanceType`
        The * barrier means that arguments must be named, this is to avoid accidental
        ambiguity.

        :param short_address: Integer or `address.Short` of the relevant address
        :param instance_number: Integer of the relevant instance number
        :param instance_type: Either an integer corresponding to the instance type,
        e.g. 1 for "Part 301", or the module name that implements the type e.g.
        "device.pushbutton" (which internally has a property `instance_type`)
        :return: None
        """
        if isinstance(short_address, address.Short):
            short_address = short_address.address
        if hasattr(instance_type, "instance_type"):
            instance_type = int(instance_type.instance_type)
        else:
            instance_type = int(instance_type)
        self._mapping[(short_address, instance_number)] = instance_type

    def get_type(
        self, *, short_address: Union[address.Short, int], instance_number: int
    ) -> Optional[int]:
        """
        Looks up the instance type based on the short address and instance number. Only
        works if this has previously been added through a call to `add_type()`.
        The * barrier means that arguments must be named, this is to avoid accidental
        ambiguity.

        :param short_address: Integer or `address.Short` of the relevant address
        :param instance_number: Integer of the relevant instance number
        :return: Either the instance type as an integer, or None
        """
        if isinstance(short_address, address.Short):
            short_address = short_address.address
        return self._mapping.get((short_address, instance_number), None)

    def clear(self) -> None:
        """
        Unconditionally clears all mappings

        :return: None
        """
        self._mapping = {}

    def __repr__(self):
        return f"{self.__class__.__name__}({self._mapping})"


# Don't create _EventTypeMappingDeviceInstance, use this instance of it only
device_instance_map = _EventTypeMappingDeviceInstance()


class _Event(_DeviceCommand):
    """
    An event message from a control device
    """

    _framesize = 24
    # The metaclass will call '_register_subclass()', which then adds to this dict
    # to maintain a mapping of 'instance type' codes to the Python class which
    # implements that type
    _instance_types: Dict[int, Type["_Event"]] = {}

    # Identifying information, not all will be present for each message
    _short_address = None
    _instance_number = None
    _instance_group = None
    _device_group = None
    # Instance Type and Event Info will be overridden in subclasses
    _instance_type = None
    _event_info = None
    _data = None

    def __init__(
        self,
        *,
        short_address: Optional[Union[address.Short, int]] = None,
        instance_number: Optional[int] = None,
        instance_group: Optional[int] = None,
        device_group: Optional[int] = None,
        data: Optional[int] = None,
    ):
        if isinstance(self, AmbiguousInstanceType):
            f = frame.ForwardFrame(24, 0)
        elif self._event_info is None:
            raise NotImplementedError
        else:
            f = frame.ForwardFrame(24, self._event_info)

        if short_address is not None:
            # If specifying short address, the instance type is implicitly known
            # already through the class type. Other properties are not allowed.
            if device_group is not None:
                raise ValueError(
                    "Must not specify 'device group' if specifying 'short address'"
                )
            elif instance_group is not None:
                raise ValueError(
                    "Must not specify 'instance group' if specifying 'short address'"
                )

            if instance_number is None:
                # Using "Device" scheme
                f[14:10] = self.instance_type
                # 'Device' scheme: bit 23 = 0, bit 15 = 0
                f[23] = False
                f[15] = False
            else:
                # Using "Device/Instance" scheme
                self._instance_number = instance_number
                f[14:10] = instance_number
                # 'Device/Instance' scheme: bit 23 = 0, bit 15 = 1
                f[23] = False
                f[15] = True

            if isinstance(short_address, address.Short):
                self._short_address = short_address
            else:
                self._short_address = address.Short(short_address)
            self.short_address.add_to_frame(f)

        elif device_group is not None:
            # If specifying device group, the instance type is implicitly known already
            # through the class type. Other properties are not allowed.
            if instance_number is not None:
                raise ValueError(
                    "Must not specify 'instance number' if specifying 'device group'"
                )
            elif instance_group is not None:
                raise ValueError(
                    "Must not specify 'instance group' if specifying 'device group'"
                )
            self._device_group = device_group
            # In the 'device group' scheme, the instance type is in bits 14:10
            f[14:10] = self.instance_type
            # Then the device group is bits 21:17
            f[21:17] = device_group
            # 'device group' scheme: bit 23 = 1, bit 22 = 0, bit 15 = 0
            f[23] = True
            f[22] = False
            f[15] = False

        elif instance_group is not None:
            # If specifying instance group, the instance type is implicitly known
            # already through the class type. Other properties are not allowed.
            if instance_number is not None:
                raise ValueError(
                    "Must not specify 'instance number' if specifying 'instance group'"
                )
            self._instance_group = instance_group
            # In the 'instance group' scheme, the instance type is in bits 14:10
            f[14:10] = self.instance_type
            # Then the instance group is in bits 21:17
            f[21:17] = instance_group
            # 'instance group' scheme: bit 23 = 1, bit 22 = 1, bit 15 = 0
            f[23] = True
            f[22] = True
            f[15] = False

        elif instance_number is not None:
            # If specifying instance number, the instance type is implicitly known
            # already through the class type. Other properties are not allowed, these
            # have been checked already in the previous statements.
            self._instance_number = instance_number
            # In the 'instance' scheme, the instance type is in bits 21:17
            f[21:17] = self.instance_type
            # Then the instance number is in bits 14:10
            f[14:10] = instance_number
            # 'instance' scheme: bit 23 = 1, bit 22 = 0, bit 15 = 1
            f[23] = True
            f[22] = False
            f[15] = True

        else:
            raise ValueError(
                "No valid combination of 'instance number', 'short address', "
                "'device group' or 'instance group'"
            )

        self._set_event_data(data, f)
        super().__init__(f)

    def _set_event_data(self, set_data: int, set_frame: frame.Frame):
        """
        Overridden in subclasses which have data to include in the 10 bits of event
        information, by default does nothing
        """
        return

    @property
    def event_data(self):
        """
        Overridden in subclasses which have data, primarily used to format data in a
        suitable way for the __repr__ method
        """
        return

    @property
    def short_address(self) -> Optional[address.Short]:
        return self._short_address

    @property
    def instance_type(self) -> int:
        return self._instance_type

    @property
    def device_group(self) -> Optional[int]:
        return self._device_group

    @property
    def instance_group(self) -> Optional[int]:
        return self._instance_group

    @property
    def instance_number(self) -> Optional[int]:
        return self._instance_number

    @classmethod
    def _register_subclass(cls, subclass):
        if not issubclass(subclass, _Event):
            raise RuntimeError(
                "Somehow called _Event._register_subclass() "
                "without a subclass of _Event"
            )
        cls._instance_types[subclass._instance_type] = subclass

    @classmethod
    def from_event_data(cls, event_data: int) -> Type[_Event]:
        """
        Takes a given set of event data, and returns a class which is intended to
        contain that data. For some event types this might just be a mapping, i.e.
        for events where each possible value represents a different event. For some
        other events which have data, the returned class could be the same for
        multiple data.
        """
        raise NotImplementedError(
            "'from_event_data()' must be implemented in a subclass"
        )

    @classmethod
    def from_frame(cls, frame: frame.Frame, devicetype: int = 0):
        # In 24-bit frames, bit 16 is 0 for "events"
        if frame[16] != 0:
            return

        short_address = None
        instance_number = None
        instance_group = None
        device_group = None
        data = frame[9:0]

        # Refer to Part 103 Table 3, Event Scheme / Source identification
        if frame[23] == 0 and frame[15] == 0:
            # "Device", has short address and instance type. This means the event
            # information can be decoded without further context.
            instance_type = frame[14:10]
            short_address = address.Short(frame[22:17])
        elif frame[23] == 0 and frame[15] == 1:
            # "Device/instance", has short address and instance number. NOTE: Further
            # contextual information is needed to decode, since the event information
            # cannot be inferred just from this message alone!
            instance_number = frame[14:10]
            short_address = address.Short(frame[22:17])

            instance_type = device_instance_map.get_type(
                short_address=short_address, instance_number=instance_number
            )
            if instance_type is None:
                # Since this message can't be handled, even though we know it is some
                # sort of event message, return an 'AmbiguousInstanceType'
                return AmbiguousInstanceType(
                    short_address=short_address,
                    instance_number=instance_number,
                    data=data,
                )
        elif frame[23] == 1 and frame[22] == 0 and frame[15] == 0:
            # "Device group", has device group and instance type. The event
            # information can be decoded without further context.
            instance_type = frame[14:10]
            device_group = frame[21:17]
        elif frame[23] == 1 and frame[22] == 0 and frame[15] == 1:
            # "Instance", has instance type and instance number. The event
            # information can be decoded without further context.
            instance_type = frame[21:17]
            instance_number = frame[14:10]
        elif frame[23] == 1 and frame[22] == 1 and frame[15] == 0:
            # "Instance group", has instance group and instance type. The event
            # information can be decoded without further context.
            instance_type = frame[14:10]
            instance_group = frame[21:17]
        else:
            # This message is not an event message
            return

        instance_type_class = cls._instance_types.get(instance_type)
        if instance_type_class is not None:
            event_type = instance_type_class.from_event_data(data)
            if event_type is not None:
                return event_type(
                    short_address=short_address,
                    instance_number=instance_number,
                    instance_group=instance_group,
                    device_group=device_group,
                    data=data,
                )

        # Even though we know this is an event message of some sort, there seemingly
        # isn't the code to handle it
        return UnknownEvent(frame)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        rep_str = f"{self.__class__.__name__}("
        if self.short_address:
            rep_str += f"short_address={self.short_address.address}, "
        if self.instance_number is not None:
            rep_str += f"instance_number={self.instance_number}, "
        if self.instance_group is not None:
            rep_str += f"instance_group={self.instance_group}, "
        if self.device_group is not None:
            rep_str += f"device_group={self.device_group}, "
        if self.event_data is not None:
            rep_str += f"data={self.event_data}, "
        # Remove the final ", " characters
        rep_str = rep_str[:-2]
        rep_str += ")"

        return rep_str


class AmbiguousInstanceType(_Event):
    """
    A message which is known to be an "event" using the "Device/Instance" scheme,
    but the mapping from device and instance to a concrete instance type has not
    previously been defined. When this happens the event information cannot be decoded
    at all, because the meaning of the event information depends on the instance type.

    Mappings of device/instance to event types can be set up using a
    `device_instance_map.add_type()` call.
    """

    def __init__(self, **kwargs):
        short_address = kwargs.pop("short_address")
        if short_address is None:
            raise ValueError("'short_address' is required for AmbiguousInstanceType")
        instance_number = kwargs.pop("instance_number")
        if instance_number is None:
            raise ValueError("'instance_number' is required for AmbiguousInstanceType")
        data = kwargs.pop("data", None)
        self._unhandled_data = None
        super().__init__(
            short_address=short_address, instance_number=instance_number, data=data
        )

    @classmethod
    def from_event_data(cls, event_data: int) -> Type[_Event]:
        return cls

    def _set_event_data(self, set_data: Optional[int], set_frame: frame.Frame):
        """
        Even though the event information can't be decoded because the instance type is
        not known, the information can still be stored into the frame
        """
        if set_data is not None:
            self._unhandled_data = set_data
            set_frame[9:0] = set_data

    @property
    def event_data(self):
        return self._unhandled_data
