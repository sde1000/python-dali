from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Optional, Type

# Fake hardware for testing
from dali import address, device, frame, gear
from dali.command import Command
from dali.gear.colour import QueryColourValueDTR
from dali.memory import info, oem
from dali.memory.location import MemoryType
from dali.sequences import progress

_yes = 0xff


class FakeMemoryBank:
    """A memory bank used for testing

    Subclass this for each different memory bank you need to
    implement. An instance will be created by each fake Gear instance
    that the memory bank is passed to.
    """
    bank = None
    initial_contents = None
    unlock_value = 0x55
    nobble_dtr0_update = False

    def __init__(self):
        self.contents = list(self.bank.factory_default_contents())
        if self.initial_contents is not None:
            self.set_memory_data(self.initial_contents)

    def set_memory_data(self, new_contents):
        # Update memory bank using new_contents. Locations with
        # new_contents 'None' are not changed.
        for addr, value in enumerate(new_contents):
            if value is not None:
                self.contents[addr] = value

    def read(self, address):
        if address > self.contents[0]:
            return
        try:
            return self.contents[address]
        except IndexError:
            # return nothing when trying to read non-existent
            # memory location
            return

    def write(self, address, value):
        # "If the selected memory bank location is not
        # implemented, or above the last accessible memory
        # location, or locked, or not writeable, the answer [...]
        # shall be NO and no memory location shall be written to."
        location = self.bank.locations[address].memory_location
        if not location:
            return  # not implemented
        if address > self.contents[0]:
            return  # above the last accessible memory location
        if location.type_ == MemoryType.NVM_RW_L \
           and self.contents[2] != self.unlock_value:
            return  # locked
        if location.type_ not in (
                MemoryType.RAM_RW, MemoryType.NVM_RW,
                MemoryType.NVM_RW_L, MemoryType.NVM_RW_P):
            return  # not writeable
        self.contents[address] = value
        return value


# Valid bank 0 ROM contents compatible with IEC 62386-102
class FakeBank0(FakeMemoryBank):
    bank = info.BANK_0
    initial_contents = [
        0x7f, None, 0x01,  # Memory bank 1 is last accessible
        0x01, 0x1f, 0x71, 0xf7, 0x6b, 0xb1,  # GTIN 1234567654321
        0x01, 0x00,  # Firmware version 1.0
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01,  # Serial number 1
        0x02, 0x01,  # Hardware version 2.1
        0x08, 0x08,  # Parts 101 and 102 version 2.0
        0xff,  # Part 103 not implemented
        0x00,  # 0 logical control device units
        0x01,  # 1 logical control gear unit
        0x00,  # This is control gear unit index 0
    ]


class FakeBank1(FakeMemoryBank):
    bank = oem.BANK_1
    initial_contents = [
        0x77, None, 0xff,  # Implemented up to and including address 0x77
        # All the rest of the memory bank is initialised to default values
    ]


class Gear:
    """Control gear on a DALI bus

    Receives 16-bit Command objects and returns None for no response, or
    an integer in the range 0..255 to indicate responding with an 8-bit
    backward frame.
    """
    def __init__(self, shortaddr=None, groups=set(),
                 devicetypes=[], random_preload=[],
                 memory_banks=(FakeBank0, FakeBank1)):
        if isinstance(shortaddr, address.GearShort):
            shortaddr = shortaddr.address
        self.shortaddr = shortaddr
        self.level = 0
        self.level_max = 254
        self.level_min = 1
        self.scenes = [255] * 16
        self.groups = set(groups)
        self.devicetypes = devicetypes
        self.random_preload = random_preload
        self.initialising = False
        self.withdrawn = False
        self.dt_gap = 1  # Number of commands since last QueryNextDeviceType
        self.dt_queue = []  # Devices still to be returned by QueryNextDeviceType
        self.randomaddr = frame.Frame(24)
        self.searchaddr = frame.Frame(24)
        self.dtr0 = 0
        self.dtr1 = 0
        self.dtr2 = 0
        self.prev_cmd = None
        self.temp_ct = 0
        self.actual_ct = 0
        self.ct_mired_min = 153
        self.ct_mired_max = 370
        self.physical_minimum = 1
        self.memory_banks = {}
        for fake_bank in memory_banks:
            bank_number = fake_bank.bank.address
            if bank_number in memory_banks:
                raise Exception(f"Duplicate memory bank {bank_number}")
            self.memory_banks[bank_number] = fake_bank()
        self.enableWriteMemory = False

    def _next_random_address(self):
        if self.random_preload:
            return self.random_preload.pop(0)
        else:
            return random.randrange(0, 0x1000000)

    def valid_address(self, cmd):
        """Should we respond to this command?
        """
        if len(cmd.frame) != 16:
            # A control gear only responds to 16 bit commands
            return False
        if not hasattr(cmd, 'destination'):
            # Command is not addressed: these are treated as broadcast
            return True
        if isinstance(cmd.destination, address.GearBroadcast):
            return True
        if isinstance(cmd.destination, address.GearBroadcastUnaddressed):
            return self.shortaddr is None
        if isinstance(cmd.destination, address.GearShort):
            return cmd.destination.address == self.shortaddr
        if isinstance(cmd.destination, address.GearGroup):
            return cmd.destination.group in self.groups

    def send(self, cmd):
        self.prev_cmd = cmd
        self.dt_gap += 1
        # Reset enableWriteMemory if command is not one of the memory
        # writing commands, even if the command is not addressed to us
        if self.enableWriteMemory and not any(
                isinstance(cmd, ct) for ct in (
                    gear.general.WriteMemoryLocation,
                    gear.general.WriteMemoryLocationNoReply,
                    gear.general.DTR0, gear.general.DTR1, gear.general.DTR2,
                    gear.general.QueryContentDTR0, gear.general.QueryContentDTR1,
                    gear.general.QueryContentDTR2)):
            self.enableWriteMemory = False
        if not self.valid_address(cmd):
            return
        # Command is either addressed to us, or is a broadcast
        if isinstance(cmd, gear.general.SetScene):
            self.scenes[cmd.param] = self.dtr0
        elif isinstance(cmd, gear.general.RemoveFromScene):
            self.scenes[cmd.param] = 255
        elif isinstance(cmd, gear.general.AddToGroup):
            self.groups.add(cmd.param)
        elif isinstance(cmd, gear.general.RemoveFromGroup):
            self.groups.discard(cmd.param)
        elif isinstance(cmd, gear.general.DAPC):
            if cmd.power == 255:
                return
            elif cmd.power == 0:
                self.level = 0
            elif cmd.power > self.level_max:
                self.level = self.level_max
            elif cmd.power < self.level_min:
                self.level = self.level_min
            else:
                self.level = cmd.power
        elif isinstance(cmd, gear.general.RecallMaxLevel):
            self.level = self.level_max
        elif isinstance(cmd, gear.general.RecallMinLevel):
            self.level = self.level_min
        elif isinstance(cmd, gear.general.Off):
            self.level = 0
        elif isinstance(cmd, gear.general.QueryActualLevel):
            return self.level
        elif isinstance(cmd, gear.general.SetMaxLevel):
            if self.level_min >= self.dtr0:
                self.level_max = self.level_min
            elif self.dtr0 == 255:
                self.level_max = 254
            else:
                self.level_max = self.dtr0
            # Ensure output level is no more than the new maximum
            if self.level > self.level_max:
                self.level = self.level_max
        elif isinstance(cmd, gear.general.SetMinLevel):
            if self.dtr0 <= 1:
                self.level_min = 1
            if (self.dtr0 >= self.level_max) or (self.dtr0 == 255):
                self.level_min = self.level_max
            else:
                self.level_min = self.dtr0
            # Ensure output level is either zero or no less than the new minimum
            if self.level > 0:
                if self.level < self.level_min:
                    self.level = self.level_min
        elif isinstance(cmd, gear.general.QueryMaxLevel):
            return self.level_max
        elif isinstance(cmd, gear.general.QueryMinLevel):
            return self.level_min
        elif isinstance(cmd, gear.general.QueryPhysicalMinimum):
            return self.physical_minimum
        elif isinstance(cmd, gear.general.SetShortAddress):
            if self.dtr0 == 0xff:
                self.shortaddr = None
            elif (self.dtr0 & 1) == 1:
                self.shortaddr = (self.dtr0 & 0x7e) >> 1
        elif isinstance(cmd, gear.general.QueryControlGearPresent):
            return _yes
        elif isinstance(cmd, gear.general.QueryMissingShortAddress):
            if self.shortaddr is None:
                return _yes
        elif isinstance(cmd, gear.general.QueryContentDTR0):
            return self.dtr0
        elif isinstance(cmd, gear.general.QueryDeviceType):
            if len(self.devicetypes) == 0:
                return 254
            elif len(self.devicetypes) == 1:
                return self.devicetypes[0]
            else:
                self.dt_gap = 0
                self.dt_queue = list(self.devicetypes)
                return 0xff
        elif isinstance(cmd, gear.general.QueryVersionNumber):
            try:
                return self.memory_banks[0].contents[0x16]
            except (IndexError, AttributeError):
                return 8  # Corresponds to Part 102 Version 2.0
        elif isinstance(cmd, gear.general.QueryContentDTR1):
            return self.dtr1
        elif isinstance(cmd, gear.general.QueryContentDTR2):
            return self.dtr2
        elif isinstance(cmd, gear.general.QueryNextDeviceType):
            # self.dt_gap must be 1 for this command to be valid; otherwise
            # there was an intervening command
            if self.dt_gap == 1:
                if self.dt_queue:
                    self.dt_gap = 0
                    return self.dt_queue.pop(0)
                return 254
        elif isinstance(cmd, gear.general.QuerySceneLevel):
            return self.scenes[cmd.param]
        elif isinstance(cmd, gear.general.GoToScene):
            scene_level = self.scenes[cmd.param]
            if scene_level == 255:
                # Don't change level if scene is MASK
                return
            elif scene_level > self.level_max:
                self.level = self.level_max
            elif scene_level < self.level_min:
                self.level = self.level_min
            else:
                self.level = scene_level
        elif isinstance(cmd, gear.general.QueryGroupsZeroToSeven):
            r = frame.Frame(8)
            for i in range(0, 8):
                if i in self.groups:
                    r[i] = True
            return r.as_integer
        elif isinstance(cmd, gear.general.QueryGroupsEightToFifteen):
            r = frame.Frame(8)
            for i in range(8, 16):
                if i in self.groups:
                    r[i - 8] = True
            return r.as_integer
        elif isinstance(cmd, gear.general.QueryRandomAddressH):
            return self.randomaddr[23:16]
        elif isinstance(cmd, gear.general.QueryRandomAddressM):
            return self.randomaddr[15:8]
        elif isinstance(cmd, gear.general.QueryRandomAddressL):
            return self.randomaddr[7:0]
        elif isinstance(cmd, gear.general.Terminate):
            self.initialising = False
            self.withdrawn = False
        elif isinstance(cmd, gear.general.DTR0):
            self.dtr0 = cmd.param
        elif isinstance(cmd, gear.general.Initialise):
            if cmd.broadcast \
               or (cmd.address == self.shortaddr):
                self.initialising = True
                self.withdrawn = False
                # We don't implement the 15 minute timer
        elif isinstance(cmd, gear.general.Randomise):
            self.randomaddr = frame.Frame(24, self._next_random_address())
        elif isinstance(cmd, gear.general.Compare):
            if self.initialising \
               and not self.withdrawn \
               and self.randomaddr.as_integer <= self.searchaddr.as_integer:
                return _yes
        elif isinstance(cmd, gear.general.Withdraw):
            if self.initialising \
               and self.randomaddr == self.searchaddr:
                self.withdrawn = True
        elif isinstance(cmd, gear.general.SearchaddrH):
            self.searchaddr[23:16] = cmd.param
        elif isinstance(cmd, gear.general.SearchaddrM):
            self.searchaddr[15:8] = cmd.param
        elif isinstance(cmd, gear.general.SearchaddrL):
            self.searchaddr[7:0] = cmd.param
        elif isinstance(cmd, gear.general.ProgramShortAddress):
            if self.initialising \
               and self.randomaddr == self.searchaddr:
                if cmd.address == 'MASK':
                    self.shortaddr = None
                else:
                    self.shortaddr = cmd.address
        elif isinstance(cmd, gear.general.VerifyShortAddress):
            if self.initialising \
               and self.shortaddr == cmd.address:
                return _yes
        elif isinstance(cmd, gear.general.DTR1):
            self.dtr1 = cmd.param
        elif isinstance(cmd, gear.general.DTR2):
            self.dtr2 = cmd.param
        elif isinstance(cmd, gear.general.EnableWriteMemory):
            self.enableWriteMemory = True
        elif isinstance(cmd, gear.general.ReadMemoryLocation):
            # "If the selected memory bank is not implemented, the
            # command shall be ignored."
            bank = self.memory_banks.get(self.dtr1)
            if not bank:
                return
            try:
                return bank.read(self.dtr0)
            finally:
                # increment DTR0 but limit to 0xFF, even if the memory
                # location is not implemented
                if not bank.nobble_dtr0_update:
                    self.dtr0 = min(self.dtr0 + 1, 255)
        elif isinstance(cmd, gear.general.WriteMemoryLocation) \
             or isinstance(cmd, gear.general.WriteMemoryLocationNoReply):  # noqa
            bank = self.memory_banks.get(self.dtr1)
            # "Only while writeEnableState is ENABLED, and the
            # addressed memory bank is implemented, the control gear
            # shall accept..."
            if not self.enableWriteMemory or not bank:
                return
            try:
                r = bank.write(self.dtr0, cmd.param)
                if isinstance(cmd, gear.general.WriteMemoryLocation):
                    return r
            finally:
                if not bank.nobble_dtr0_update:
                    self.dtr0 = min(self.dtr0 + 1, 255)
        # Handle DT8 colour commands, device type decoding has already been
        # handled
        if isinstance(cmd, gear.colour._ColourCommand):
            # Only handle if this Gear instance has been declared as a DT8 type
            if 8 not in self.devicetypes:
                return
            if isinstance(cmd, gear.colour.QueryColourTypeFeatures):
                return 0b00000010  # Bit 1 = Colour temperature Tc capable
            elif isinstance(cmd, gear.colour.QueryColourValue):
                if self.dtr0 == QueryColourValueDTR.TemporaryColourTemperature.value:
                    tmp_ct = self.temp_ct.to_bytes(length=2, byteorder="little")
                    self.dtr0 = tmp_ct[0]
                    self.dtr1 = tmp_ct[1]
                    return tmp_ct[1]
                elif self.dtr0 == QueryColourValueDTR.ColourTemperatureTC.value:
                    tmp_ct = self.actual_ct.to_bytes(length=2, byteorder="little")
                    self.dtr0 = tmp_ct[0]
                    self.dtr1 = tmp_ct[1]
                    return tmp_ct[1]
                elif self.dtr0 == QueryColourValueDTR.ReportColourTemperatureTc.value:
                    tmp_ct = self.actual_ct.to_bytes(length=2, byteorder="little")
                    self.dtr0 = tmp_ct[0]
                    self.dtr1 = tmp_ct[1]
                    return tmp_ct[1]
                elif self.dtr0 == QueryColourValueDTR.ColourTemperatureTcCoolest.value:
                    tmp_ct = self.ct_mired_min.to_bytes(length=2, byteorder="little")
                    self.dtr0 = tmp_ct[0]
                    self.dtr1 = tmp_ct[1]
                    return tmp_ct[1]
                elif (
                    self.dtr0
                    == QueryColourValueDTR.ColourTemperatureTcPhysicalCoolest.value
                ):
                    tmp_ct = self.ct_mired_min.to_bytes(length=2, byteorder="little")
                    self.dtr0 = tmp_ct[0]
                    self.dtr1 = tmp_ct[1]
                    return tmp_ct[1]
                elif self.dtr0 == QueryColourValueDTR.ColourTemperatureTcWarmest.value:
                    tmp_ct = self.ct_mired_max.to_bytes(length=2, byteorder="little")
                    self.dtr0 = tmp_ct[0]
                    self.dtr1 = tmp_ct[1]
                    return tmp_ct[1]
                elif (
                    self.dtr0
                    == QueryColourValueDTR.ColourTemperatureTcPhysicalWarmest.value
                ):
                    tmp_ct = self.ct_mired_max.to_bytes(length=2, byteorder="little")
                    self.dtr0 = tmp_ct[0]
                    self.dtr1 = tmp_ct[1]
                    return tmp_ct[1]
            elif isinstance(cmd, gear.colour.SetTemporaryColourTemperature):
                self.temp_ct = int.from_bytes((self.dtr0, self.dtr1), "little")
            elif isinstance(cmd, gear.colour.Activate):
                if self.temp_ct > self.ct_mired_max:
                    self.actual_ct = self.ct_mired_max
                elif self.temp_ct < self.ct_mired_min:
                    self.actual_ct = self.ct_mired_min
                else:
                    self.actual_ct = self.temp_ct
            elif isinstance(cmd, gear.colour.CopyReportToTemporary):
                self.temp_ct = self.actual_ct
            elif isinstance(cmd, gear.colour.QueryExtendedVersionNumber):
                return 2


# Valid bank 0 ROM contents compatible with IEC 62386-103
class FakeDeviceBank0(FakeMemoryBank):
    bank = info.BANK_0
    initial_contents = [
        0x1A, None, 0x00,  # Memory bank 0 is last accessible
        0x01, 0x1F, 0x71, 0xF7, 0x6B, 0xB1,  # GTIN 1234567654321
        0x01, 0x00,  # Firmware version 1.0
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01,  # Serial number 1
        0x02, 0x01,  # Hardware version 2.1
        0x08,  # Part 101 version 2.0
        0xFF,  # Part 102 not implemented
        0x08,  # Part 103 version 2.0
        0x01,  # 1 logical control device units
        0x00,  # 0 logical control gear unit
        0x00,  # This is control gear unit index 0
    ]


class Device:
    """
    Control device on a DALI bus

    Receives 24-bit Command objects and returns None for no response, or
    an integer in the range 0..255 to indicate responding with an 8-bit
    backward frame.
    """

    @dataclass
    class Instance:
        inst_type: int
        scheme: int
        filter: int = 0
        enabled: bool = True

    # Creates 4 instances of pushbutton types, each set to Device/Instance mode
    _instances = [
        Instance(inst_type=1, scheme=2),
        Instance(inst_type=1, scheme=2),
        Instance(inst_type=1, scheme=2),
        Instance(inst_type=1, scheme=2),
    ]
    # Refer to Table 15 of Part 103, status of all zero is "no error"
    _device_status = 0b00000000

    def __init__(
        self,
        shortaddr: Optional[address.DeviceShort] = None,
        groups: Optional[Iterable[address.DeviceGroup]] = None,
        memory_banks: Optional[Iterable[Type[FakeMemoryBank]]] = (FakeDeviceBank0,),
    ):
        # Store parameters
        self.shortaddr = shortaddr
        self.groups = set(groups) if groups else set()
        # Configure internal variables
        self.dtr0: int = 0
        self.dtr1: int = 0
        self.dtr2: int = 0
        self.enable_write_memory: bool = False
        self.memory_banks = {}
        for fake_bank in memory_banks:
            bank_number = fake_bank.bank.address
            if bank_number in memory_banks:
                raise ValueError(f"Duplicate memory bank {bank_number}")
            self.memory_banks[bank_number] = fake_bank()

    def valid_address(self, cmd: Command) -> bool:
        """Should we respond to this command?"""
        if len(cmd.frame) != 24:
            # A control device only responds to 24 bit commands
            return False
        if not hasattr(cmd, "destination"):
            # Command is not addressed: these are treated as broadcast
            return True
        if isinstance(cmd.destination, address.DeviceBroadcast):
            return True
        if isinstance(cmd.destination, address.DeviceBroadcastUnaddressed):
            return self.shortaddr is None
        if isinstance(cmd.destination, address.DeviceShort):
            return cmd.destination == self.shortaddr
        if isinstance(cmd.destination, address.DeviceGroup):
            return cmd.destination in self.groups

    def send(self, cmd: Command) -> Optional[int]:
        # Reset enable_write_memory if command is not one of the memory
        # writing commands, even if the command is not addressed to us
        if self.enable_write_memory and not isinstance(
            cmd,
            (
                device.general.WriteMemoryLocation,
                device.general.WriteMemoryLocationNoReply,
                device.general.DTR0,
                device.general.DTR1,
                device.general.DTR2,
                device.general.DTR1DTR0,
                device.general.DTR2DTR1,
                device.general.QueryContentDTR0,
                device.general.QueryContentDTR1,
                device.general.QueryContentDTR2,
            ),
        ):
            self.enable_write_memory = False

        if not self.valid_address(cmd):
            return None

        if hasattr(cmd, "instance"):
            if isinstance(cmd.instance, address.InstanceNumber):
                # Handle any instance-specific commands
                # TODO: Support more than just instance number scheme
                inst_num = cmd.instance.value
                if inst_num > len(self._instances) - 1:
                    return None

                if isinstance(cmd, device.general.QueryInstanceEnabled):
                    if self._instances[inst_num].enabled:
                        return _yes
                    else:
                        return None
                elif isinstance(cmd, device.general.QueryInstanceType):
                    return self._instances[inst_num].inst_type
                elif isinstance(cmd, device.general.QueryEventScheme):
                    return self._instances[inst_num].scheme
                elif isinstance(cmd, device.general.SetEventScheme):
                    self._instances[inst_num].scheme = self.dtr0
                elif isinstance(cmd, device.general.QueryEventFilterZeroToSeven):
                    return self._instances[inst_num].filter
                elif isinstance(cmd, device.general.SetEventFilter):
                    self._instances[inst_num].filter = self.dtr0

        # Command is either addressed to the entire device, or is a broadcast
        if isinstance(cmd, device.general.DTR0):
            self.dtr0 = cmd.param
        elif isinstance(cmd, device.general.DTR1):
            self.dtr1 = cmd.param
        elif isinstance(cmd, device.general.DTR2):
            self.dtr2 = cmd.param
        elif isinstance(cmd, device.general.DTR1DTR0):
            self.dtr1 = cmd.param_1
            self.dtr0 = cmd.param_2
        elif isinstance(cmd, device.general.DTR2DTR1):
            self.dtr2 = cmd.param_1
            self.dtr1 = cmd.param_2
        elif isinstance(cmd, device.general.QueryContentDTR0):
            return self.dtr0
        elif isinstance(cmd, device.general.QueryContentDTR1):
            return self.dtr1
        elif isinstance(cmd, device.general.QueryContentDTR2):
            return self.dtr2
        elif isinstance(cmd, device.general.QueryDeviceStatus):
            return self._device_status
        elif isinstance(cmd, device.general.QueryNumberOfInstances):
            return len(self._instances)

        elif isinstance(cmd, device.general.EnableWriteMemory):
            self.enable_write_memory = True
        elif isinstance(cmd, device.general.ReadMemoryLocation):
            # "If the selected memory bank is not implemented, the
            # command shall be ignored."
            bank = self.memory_banks.get(self.dtr1)
            if not bank:
                return
            try:
                return bank.read(self.dtr0)
            finally:
                # increment DTR0 but limit to 0xFF, even if the memory
                # location is not implemented
                if not bank.nobble_dtr0_update:
                    self.dtr0 = min(self.dtr0 + 1, 255)
        elif isinstance(
            cmd,
            (
                device.general.WriteMemoryLocation,
                device.general.WriteMemoryLocationNoReply,
            ),
        ):
            bank = self.memory_banks.get(self.dtr1)
            # "Only while writeEnableState is ENABLED, and the
            # addressed memory bank is implemented, the control gear
            # shall accept..."
            if not self.enable_write_memory or not bank:
                return
            try:
                r = bank.write(self.dtr0, cmd.param)
                if isinstance(cmd, device.general.WriteMemoryLocation):
                    return r
            finally:
                if not bank.nobble_dtr0_update:
                    self.dtr0 = min(self.dtr0 + 1, 255)

        return None


class Bus:
    """A DALI bus

    Commands are sent (fake) simultaneously to all devices on the bus.
    If no devices respond, the response is None.  If one device
    responds, its response is used.  If multiple devices respond, a
    BackwardFrameError is used to represent the bus collision.
    """
    def __init__(self, gear: list):
        self.gear: list = gear

    def send(self, cmd):
        r = [x for x in (i.send(cmd) for i in self.gear) if x is not None]
        if len(r) > 1:
            rf = frame.BackwardFrameError(r[0])
        elif len(r) == 1:
            rf = frame.BackwardFrame(r[0])
        else:
            rf = None

        if cmd.response:
            return cmd.response(rf)

    def run_sequence(self, seq, verbose=False):
        response = None
        while True:
            try:
                cmd = seq.send(response)
            except StopIteration as r:
                return r.value
            response = None
            if isinstance(cmd, Command):
                response = self.send(cmd)
            elif verbose and isinstance(cmd, progress):
                print(cmd)
