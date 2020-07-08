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
"""

from dali import command
from dali import address
from dali import frame


class _DeviceCommand(command.Command):
    """A command addressed to a control device."""
    _framesize = 24

    _devicecommands = []

    @classmethod
    def _register_subclass(cls, subclass):
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


class QueryDeviceStatus(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x30


class QueryApplicationControllerError(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x31


class QueryInputDeviceError(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x32


class QueryMissingShortAddress(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x33


class QueryVersionNumber(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x34


class QueryNumberOfInstances(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x35


class QueryContentDTR0(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr0 = True
    response = command.Response
    _opcode = 0x36


class QueryContentDTR1(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr1 = True
    response = command.Response
    _opcode = 0x37


class QueryContentDTR2(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr2 = True
    response = command.Response
    _opcode = 0x38


class QueryRandomAddressH(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x39


class QueryRandomAddressM(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x3a


class QueryRandomAddressL(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x3b


class ReadMemoryLocation(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    uses_dtr0 = True
    uses_dtr1 = True
    response = command.Response
    _opcode = 0x3c


class QueryApplicationControlEnabled(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x3d


class QueryOperatingMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x3e


class QueryManufacturerSpecificMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
    _opcode = 0x3f


class QueryQuiescentMode(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
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
    response = command.Response
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
    response = command.Response
    _opcode = 0x47


class QueryResetState(_StandardDeviceCommand):
    appctrl = True
    inputdev = True
    response = command.Response
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
        cls._opcodes[subclass._opcode] = subclass

    @classmethod
    def from_frame(cls, frame):
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
    response = command.Response
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
    response = command.Response
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


class QueryEventScheme(_StandardInstanceCommand):
    inputdev = True
    response = command.Response
    _opcode = 0x8b


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


