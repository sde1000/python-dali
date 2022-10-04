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


Event messages are supported as per part 103, with specific event types
implemented in relevant submodules, e.g. pushbutton.py for part 301.

Messages which have no implementation will still be decoded, but will be
interpreted as an "UnknownEvent" object.
"""
from __future__ import annotations

from enum import IntEnum, IntFlag
from typing import Any, Optional, TYPE_CHECKING, Type

from dali import address, command, frame

if TYPE_CHECKING:
    from dali.device.helpers import DeviceInstanceTypeMapper


class _DeviceCommand(command.Command):
    """A command addressed to a control device."""
    _framesize = 24
    _devicecommands = []

    @classmethod
    def _register_subclass(cls, subclass):
        cls._devicecommands.append(subclass)

    @classmethod
    def from_frame(cls, f, devicetype=0, dev_inst_map=None):
        # In 24-bit frames, bit 16 is 1 for "commands" (as opposed to "events")
        if not f[16]:
            return
        for dc in cls._devicecommands:
            r = dc.from_frame(f, dev_inst_map=dev_inst_map)
            if r:
                return r
        return UnknownDeviceCommand(f)


class UnknownDeviceCommand(_DeviceCommand):
    """An unknown command addressed to a control device.
    """
    @classmethod
    def from_frame(cls, f, devicetype=0, dev_inst_map=None):
        return


class InstanceEventFilter(IntFlag):
    """
    A base class for implementing specific event filters, which are used by
    each different instance type. Flags in an InstanceEventFilter enum *must*
    only be powers of two, i.e. each bit can only be named once and there cannot
    be named groups of bits.
    """

    @classmethod
    def dali_width(cls) -> int:
        """Indicates if 8, 16, or 24 bits are needed for this event filter"""

        length = len(cls)
        if length <= 8:
            return 8
        elif length <= 16:
            return 16
        elif length <= 24:
            return 24
        else:
            raise TypeError(
                f"{cls.__name__} from {cls.__module__} has more than 24 bits "
                "defined, this is not allowed"
            )


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

        f = frame.ForwardFrame(24, 0x1FE00 | self._opcode)
        self.destination.add_to_frame(f)

        super().__init__(f)

    _opcodes = {}

    @classmethod
    def _register_subclass(cls, subclass):
        cls._opcodes[subclass._opcode] = subclass

    @classmethod
    def from_frame(cls, f, devicetype=0, dev_inst_map=None):
        if f[16:8] != 0x1FE:
            return

        addr = address.from_frame(f)

        if addr is None:
            return

        cc = cls._opcodes.get(f[7:0])
        if not cc:
            return UnknownDeviceCommand(f)

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
    _opcode = 0x1A


class RemoveFromDeviceGroupsZeroToFifteen(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr1 = True
    uses_dtr2 = True
    sendtwice = True
    _opcode = 0x1B


class RemoveFromDeviceGroupsSixteenToThirtyOne(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr1 = True
    uses_dtr2 = True
    sendtwice = True
    _opcode = 0x1C


class StartQuiescentMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x1D


class StopQuiescentMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x1E


class EnablePowerCycleNotification(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    sendtwice = True
    _opcode = 0x1F


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


class QueryDeviceStatusResponse(command.BitmapResponse):
    """
    Control Device Status, as defined in Part 103 Table 15
    """

    bits = [
        "input device error",
        "quiescent mode enabled",
        "short address is mask",
        "application controller active",
        "application controller error",
        "power cycle seen",
        "reset state",
    ]


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
    _opcode = 0x3A


class QueryRandomAddressL(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x3B


class ReadMemoryLocation(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr0 = True
    uses_dtr1 = True
    response = command.NumericResponse
    _opcode = 0x3C


class QueryApplicationControlEnabled(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x3D


class QueryOperatingMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x3E


class QueryManufacturerSpecificMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x3F


class QueryQuiescentMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x40


class QueryDeviceGroupsZeroToSeven(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x41


class QueryDeviceGroupsEightToFifteen(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x42


class QueryDeviceGroupsSixteenToTwentyThree(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x43


class QueryDeviceGroupsTwentyFourToThirtyOne(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x44


class QueryPowerCycleNotification(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x45


class QueryDeviceCapabilitiesResponse(command.BitmapResponse):
    """
    Control Device Capabilities, as defined in Part 103 Table 14
    """

    bits = [
        "application controller present",
        "number instances greater than zero",
        "application controller always active",
    ]


class QueryDeviceCapabilities(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = QueryDeviceCapabilitiesResponse
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

    _opcodes: dict[int, Type[_StandardInstanceCommand]] = dict()

    @classmethod
    def _register_subclass(cls, subclass: Type[_StandardInstanceCommand]):
        cls._opcodes[subclass._opcode] = subclass

    @classmethod
    def from_frame(cls, f, devicetype=0, dev_inst_map=None):
        # In 24-bit frames, bit 16 is 1 for "commands" (as opposed to "events")
        if not f[16]:
            return
        addr = address.from_frame(f)
        instance = address.instance_from_frame(f)

        if addr is None or instance is None:
            return

        cc = cls._opcodes.get(f[7:0])
        if not cc:
            return UnknownDeviceCommand(f)

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
    response = command.NumericResponse
    _opcode = 0x81


class QueryInstanceError(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x82


class QueryInstanceStatusResponse(command.BitmapResponse):
    """
    Instance Status, as defined in Part 103 Table 16
    """

    bits = [
        "instance error",
        "instance active",
    ]


class QueryInstanceStatus(_StandardInstanceCommand):
    inputdev = True
    response = QueryInstanceStatusResponse
    _opcode = 0x83


class QueryEventPriority(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x84


class QueryInstanceEnabled(_StandardInstanceCommand):
    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x86


class QueryPrimaryInstanceGroup(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x88


class QueryInstanceGroup1(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x89


class QueryInstanceGroup2(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x8A


class EventScheme(IntEnum):
    """
    Event Address Scheme setting values, as defined in Part 103 Table 8
    """

    instance = 0
    device = 1
    device_instance = 2
    device_group = 3
    instance_group = 4


class QueryEventSchemeResponse(command.EnumResponse):
    """
    A response object corresponding to a QueryEventScheme message
    """

    enumerator = EventScheme


class QueryEventScheme(_StandardInstanceCommand):
    inputdev = True
    response = QueryEventSchemeResponse
    _opcode = 0x8B


class QueryInputValue(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x8C


class QueryInputValueLatch(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x8D


class QueryFeatureType(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x8E


class QueryNextFeatureType(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x8F


class QueryEventFilterZeroToSeven(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x90


QueryEventFilterL = QueryEventFilterZeroToSeven


class QueryEventFilterEightToFifteen(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
    _opcode = 0x91


QueryEventFilterM = QueryEventFilterEightToFifteen


class QueryEventFilterSixteenToTwentyThree(_StandardInstanceCommand):
    inputdev = True
    response = command.NumericResponse
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
            frame.ForwardFrame(24, (self._addr, self._instance, self._opcode))
        )

    @classmethod
    def from_frame(cls, f, devicetype=0, dev_inst_map=None):
        if cls == _SpecialDeviceCommand:
            return
        if f[23:16] == cls._addr and f[15:8] == cls._instance and f[7:0] == 0x00:
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
    def from_frame(cls, f, devicetype=0, dev_inst_map=None):
        if cls == _SpecialDeviceCommandOneParam:
            return
        if f[23:16] == cls._addr and f[15:8] == cls._instance:
            return cls(f[7:0])

    @property
    def param(self) -> int:
        return self._opcode

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
    def from_frame(cls, f, devicetype=0, dev_inst_map=None):
        if cls == _SpecialDeviceCommandTwoParam:
            return
        if f[23:16] == cls._addr:
            return cls(f[15:8], f[7:0])

    @property
    def param_1(self) -> int:
        return self._instance

    @property
    def param_2(self) -> int:
        return self._opcode

    def __str__(self):
        return "{}({:02x}, {:02x})".format(
            self.__class__.__name__, self._instance, self._opcode)


class Terminate(_SpecialDeviceCommand):
    _addr = 0xC1
    _instance = 0x00


class Initialise(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x01
    sendtwice = True


class Randomise(_SpecialDeviceCommand):
    _addr = 0xC1
    _instance = 0x02
    sendtwice = True


class Compare(_SpecialDeviceCommand):
    _addr = 0xC1
    _instance = 0x03
    response = command.YesNoResponse


class Withdraw(_SpecialDeviceCommand):
    _addr = 0xC1
    _instance = 0x04


class SearchAddrH(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x05


class SearchAddrM(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x06


class SearchAddrL(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x07


class ProgramShortAddress(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x08


class VerifyShortAddress(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x09
    response = command.YesNoResponse


class QueryShortAddress(_SpecialDeviceCommand):
    _addr = 0xC1
    _instance = 0x0A
    response = command.NumericResponse


class WriteMemoryLocation(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x20
    uses_dtr0 = True
    uses_dtr1 = True
    response = command.NumericResponse


class WriteMemoryLocationNoReply(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x21
    uses_dtr0 = True
    uses_dtr1 = True


class DTR0(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x30
    uses_dtr0 = True


class DTR1(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x31
    uses_dtr1 = True


class DTR2(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x32
    uses_dtr2 = True


class SendTestframe(_SpecialDeviceCommandOneParam):
    _addr = 0xC1
    _instance = 0x33
    uses_dtr0 = True
    uses_dtr1 = True
    uses_dtr2 = True


class DirectWriteMemory(_SpecialDeviceCommandTwoParam):
    _addr = 0xC5
    uses_dtr0 = True
    uses_dtr1 = True
    response = command.NumericResponse


class DTR1DTR0(_SpecialDeviceCommandTwoParam):
    _addr = 0xC7
    uses_dtr0 = True
    uses_dtr1 = True


class DTR2DTR1(_SpecialDeviceCommandTwoParam):
    _addr = 0xC9
    uses_dtr1 = True
    uses_dtr2 = True


class _Event(command.Command):
    """
    An event message from a control device
    """

    # 'enabled_by' holds a reference to an element in an enum which, when used
    # with the appropriate 'SetEventFilter' sequence, flags if this event is
    # enabled
    enabled_by: Optional[InstanceEventFilter] = None

    _framesize = 24
    # The metaclass will call '_register_subclass()', which then adds to this
    # dict to maintain a mapping of 'instance type' codes to the Python class
    # which implements that type
    _instance_types: dict[int, Type[_Event]] = {}

    # Identifying information, not all will be present for each message
    _short_address = None
    _instance_number = None
    _instance_group = None
    _device_group = None
    # Instance Type and Event Info will be overridden in subclasses
    _instance_type = None
    _event_info = None

    def __init__(
        self,
        *,
        short_address: Optional[address.DeviceShort | int] = None,
        instance_number: Optional[int] = None,
        instance_group: Optional[int] = None,
        device_group: Optional[int] = None,
        data: Any = None,
    ):
        if isinstance(self, (AmbiguousInstanceType, UnknownEvent)):
            # Start with an empty frame for these edge-case types, the rest will
            # be filled in later to make the frame survive a round-trip
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
                    "Must not specify 'device group' with 'short address'"
                )
            elif instance_group is not None:
                raise ValueError(
                    "Must not specify 'instance group' with 'short address'"
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

            if isinstance(short_address, address.DeviceShort):
                self._short_address = short_address
            else:
                self._short_address = address.DeviceShort(short_address)
            self.short_address.add_to_frame(f)

        elif device_group is not None:
            # If specifying device group, the instance type is implicitly
            # known already through the class type. Other properties are not
            # allowed.
            if instance_number is not None:
                raise ValueError(
                    "Must not specify 'instance number' with 'device group'"
                )
            elif instance_group is not None:
                raise ValueError(
                    "Must not specify 'instance group' with 'device group'"
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
            # If specifying instance group, the instance type is implicitly
            # known already through the class type. Other properties are not
            # allowed.
            if instance_number is not None:
                raise ValueError(
                    "Must not specify 'instance number' with 'instance group'"
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
            # If specifying instance number, the instance type is implicitly
            # known already through the class type. Other properties are not
            # allowed, these have been checked already in the previous
            # statements.
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

        # Each instance type has a class that knows what to do to handle data
        self._set_event_data(data, f)

        super().__init__(f)

    def _set_event_data(self, set_data: Optional[int], set_frame: frame.Frame):
        """
        Overridden in subclasses which have data to include in the 10 bits of
        event information, by default does nothing
        """
        return

    @property
    def event_data(self):
        """
        Overridden in subclasses which have data, primarily used to format
        data in a suitable way for the __repr__ method
        """
        return

    @property
    def short_address(self) -> Optional[address.DeviceShort]:
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
        # Don't register UnknownEvent, no message should be decoded as this
        if subclass.__name__ == "UnknownEvent":
            return
        cls._instance_types[subclass._instance_type] = subclass

    @classmethod
    def get_instance_type_class(
        cls, instance_type: int
    ) -> Optional[Type[_Event]]:
        return cls._instance_types.get(instance_type)

    @classmethod
    def from_event_data(cls, event_data: int) -> Type[_Event]:
        """
        Takes a given set of event data, and returns a class which is
        intended to contain that data. For some event types this might just
        be a mapping, i.e. for events where each possible value represents a
        different event. For some other events which have data, the returned
        class could be the same for multiple data.
        """
        raise NotImplementedError(
            "'from_event_data()' must be implemented in a subclass"
        )

    @classmethod
    def from_frame(
        cls,
        f: frame.Frame,
        devicetype: int = 0,
        dev_inst_map: DeviceInstanceTypeMapper = None,
    ):
        # In 24-bit frames, bit 16 is 0 for "events"
        if f[16] != 0:
            return

        short_address = None
        instance_number = None
        instance_group = None
        device_group = None
        data = f[9:0]

        # Refer to Part 103 Table 3, Event Scheme / Source identification
        if f[23] == 0 and f[15] == 0:
            # "Device", has short address and instance type. This means the
            # event information can be decoded without further context.
            instance_type = f[14:10]
            short_address = address.DeviceShort(f[22:17])
        elif f[23] == 0 and f[15] == 1:
            # "Device/instance", has short address and instance number.
            # NOTE: Further contextual information is needed to decode,
            # since the event information cannot be inferred just from this
            # message alone!
            instance_number = f[14:10]
            short_address = address.DeviceShort(f[22:17])

            if dev_inst_map is not None:
                instance_type = dev_inst_map.get_type(
                    short_address=short_address, instance_number=instance_number
                )
            else:
                instance_type = None
            if instance_type is None:
                # Since this message can't be handled, even though we know it
                # is some sort of event message, return an
                # 'AmbiguousInstanceType'
                return AmbiguousInstanceType(
                    short_address=short_address,
                    instance_number=instance_number,
                    data=data,
                )
        elif f[23] == 1 and f[22] == 0 and f[15] == 0:
            # "Device group", has device group and instance type. The event
            # information can be decoded without further context.
            instance_type = f[14:10]
            device_group = f[21:17]
        elif f[23] == 1 and f[22] == 0 and f[15] == 1:
            # "Instance", has instance type and instance number. The event
            # information can be decoded without further context.
            instance_type = f[21:17]
            instance_number = f[14:10]
        elif f[23] == 1 and f[22] == 1 and f[15] == 0:
            # "Instance group", has instance group and instance type. The event
            # information can be decoded without further context.
            instance_type = f[14:10]
            instance_group = f[21:17]
        else:
            # This message is not an event message
            return

        instance_type_class = cls.get_instance_type_class(instance_type)
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

        # Even though we know this is an event message of some sort, there
        # seemingly isn't the code to handle it
        return UnknownEvent(
            instance_type=instance_type,
            short_address=short_address,
            instance_number=instance_number,
            instance_group=instance_group,
            device_group=device_group,
            data=data,
        )

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


class UnknownEvent(_Event):
    """
    A message known to be an "event", but with no specific implementation
    in this library
    """

    def __init__(self, instance_type: int = 0, **kwargs):
        self._instance_type = instance_type
        super().__init__(**kwargs)

    def _set_event_data(self, set_data: Any, set_frame: frame.Frame):
        """
        Even though the event information can't be decoded because the
        event type is not understood, the information can still be stored into
        the frame
        """
        if set_data is not None:
            self._unhandled_data = set_data
            set_frame[9:0] = set_data

    @property
    def event_data(self):
        return self._unhandled_data

    @classmethod
    def from_frame(cls, f, devicetype=0, dev_inst_map=None):
        return


class AmbiguousInstanceType(_Event):
    """
    A message which is known to be an "event" using the "Device/Instance"
    scheme, but the mapping from device and instance to a concrete instance
    type has not previously been defined. When this happens the event
    information cannot be decoded at all, because the meaning of the event
    information depends on the instance type.

    Mappings of device/instance to event types can be set up using a
    `device_instance_map.add_type()` call, or use the sequence
    `DiscoverInstanceTypes()`.
    """

    def __init__(self, **kwargs):
        short_address = kwargs.pop("short_address")
        if short_address is None:
            raise ValueError(
                "'short_address' is required for AmbiguousInstanceType"
            )
        instance_number = kwargs.pop("instance_number")
        if instance_number is None:
            raise ValueError(
                "'instance_number' is required for AmbiguousInstanceType"
            )
        data = kwargs.pop("data", None)
        self._unhandled_data = None
        super().__init__(
            short_address=short_address,
            instance_number=instance_number,
            data=data,
        )

    @classmethod
    def from_event_data(cls, event_data: int) -> Type[_Event]:
        return cls

    def _set_event_data(self, set_data: Optional[int], set_frame: frame.Frame):
        """
        Even though the event information can't be decoded because the
        instance type is not known, the information can still be stored into
        the frame
        """
        if set_data is not None:
            self._unhandled_data = set_data
            set_frame[9:0] = set_data

    @property
    def event_data(self):
        return self._unhandled_data

    def retry_decode(
        self, dev_inst_map: DeviceInstanceTypeMapper
    ) -> Optional[_Event]:
        """
        Tries to decode this ambiguous instance message, using the additional
        information contained in the provided DeviceInstanceTypeMapper
        object. This might make it possible to decipher this event message
        into a specific instance event.

        :param dev_inst_map: A relevant DeviceInstanceTypeMapper object to
        use, e.g. previously created through scanning and querying devices on
        the same DALI bus
        :return: If the event could be deciphered specifically through the
        additional information then a new event object will be returned,
        otherwise None
        """
        retried = command.Command.from_frame(
            self.frame, devicetype=self.devicetype, dev_inst_map=dev_inst_map
        )
        if not isinstance(retried, AmbiguousInstanceType):
            return retried
