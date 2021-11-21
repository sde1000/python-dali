# Fake hardware for testing
from dali import frame
from dali.address import Broadcast, BroadcastUnaddressed, Group, Short
from dali.command import Command
from dali.gear import general
from dali.sequences import progress
from dali.memory import info, oem
from dali.memory.location import MemoryType
import random

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
        for address, value in enumerate(new_contents):
            if value is not None:
                self.contents[address] = value

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

    Receives Command objects and returns None for no response, or an
    integer in the range 0..255 to indicate responding with an 8-bit
    backward frame.
    """
    def __init__(self, shortaddr=None, groups=set(),
                 devicetypes=[], random_preload=[],
                 memory_banks=(FakeBank0, FakeBank1)):
        self.shortaddr = shortaddr
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
        if not hasattr(cmd, 'destination'):
            # Command is not addressed: these are treated as broadcast
            return True
        if isinstance(cmd.destination, Broadcast):
            return True
        if isinstance(cmd.destination, BroadcastUnaddressed):
            return self.shortaddr is None
        if isinstance(cmd.destination, Short):
            return cmd.destination.address == self.shortaddr
        if isinstance(cmd.destination, Group):
            return cmd.destination.group in self.groups

    def send(self, cmd):
        self.dt_gap += 1
        # Reset enableWriteMemory if command is not one of the memory
        # writing commands, even if the command is not addressed to us
        if self.enableWriteMemory and not any(
                isinstance(cmd, ct) for ct in (
                    general.WriteMemoryLocation,
                    general.WriteMemoryLocationNoReply,
                    general.DTR0, general.DTR1, general.DTR2,
                    general.QueryContentDTR0, general.QueryContentDTR1,
                    general.QueryContentDTR2)):
            self.enableWriteMemory = False
        if not self.valid_address(cmd):
            return
        # Command is either addressed to us, or is a broadcast
        if isinstance(cmd, general.SetScene):
            self.scenes[cmd.param] = self.dtr0
        elif isinstance(cmd, general.RemoveFromScene):
            self.scenes[cmd.param] = 255
        elif isinstance(cmd, general.AddToGroup):
            self.groups.add(cmd.param)
        elif isinstance(cmd, general.RemoveFromGroup):
            self.groups.discard(cmd.param)
        elif isinstance(cmd, general.SetShortAddress):
            if self.dtr0 == 0xff:
                self.shortaddr = None
            elif (self.dtr0 & 1) == 1:
                self.shortaddr = (self.dtr0 & 0x7e) >> 1
        elif isinstance(cmd, general.QueryControlGearPresent):
            return _yes
        elif isinstance(cmd, general.QueryMissingShortAddress):
            if self.shortaddr is None:
                return _yes
        elif isinstance(cmd, general.QueryContentDTR0):
            return self.dtr0
        elif isinstance(cmd, general.QueryDeviceType):
            if len(self.devicetypes) == 0:
                return 254
            elif len(self.devicetypes) == 1:
                return self.devicetypes[0]
            else:
                self.dt_gap = 0
                self.dt_queue = list(self.devicetypes)
                return 0xff
        elif isinstance(cmd, general.QueryContentDTR1):
            return self.dtr1
        elif isinstance(cmd, general.QueryContentDTR2):
            return self.dtr2
        elif isinstance(cmd, general.QueryNextDeviceType):
            # self.dt_gap must be 1 for this command to be valid; otherwise
            # there was an intervening command
            if self.dt_gap == 1:
                if self.dt_queue:
                    self.dt_gap = 0
                    return self.dt_queue.pop(0)
                return 254
        elif isinstance(cmd, general.QuerySceneLevel):
            return self.scenes[cmd.param]
        elif isinstance(cmd, general.QueryGroupsZeroToSeven):
            r = frame.Frame(8)
            for i in range(0, 8):
                if i in self.groups:
                    r[i] = True
            return r.as_integer
        elif isinstance(cmd, general.QueryGroupsEightToFifteen):
            r = frame.Frame(8)
            for i in range(8, 16):
                if i in self.groups:
                    r[i - 8] = True
            return r.as_integer
        elif isinstance(cmd, general.QueryRandomAddressH):
            return self.randomaddr[23:16]
        elif isinstance(cmd, general.QueryRandomAddressM):
            return self.randomaddr[15:8]
        elif isinstance(cmd, general.QueryRandomAddressL):
            return self.randomaddr[7:0]
        elif isinstance(cmd, general.Terminate):
            self.initialising = False
            self.withdrawn = False
        elif isinstance(cmd, general.DTR0):
            self.dtr0 = cmd.param
        elif isinstance(cmd, general.Initialise):
            if cmd.broadcast \
               or (cmd.address == self.shortaddr):
                self.initialising = True
                self.withdrawn = False
                # We don't implement the 15 minute timer
        elif isinstance(cmd, general.Randomise):
            self.randomaddr = frame.Frame(24, self._next_random_address())
        elif isinstance(cmd, general.Compare):
            if self.initialising \
               and not self.withdrawn \
               and self.randomaddr.as_integer <= self.searchaddr.as_integer:
                return _yes
        elif isinstance(cmd, general.Withdraw):
            if self.initialising \
               and self.randomaddr == self.searchaddr:
                self.withdrawn = True
        elif isinstance(cmd, general.SearchaddrH):
            self.searchaddr[23:16] = cmd.param
        elif isinstance(cmd, general.SearchaddrM):
            self.searchaddr[15:8] = cmd.param
        elif isinstance(cmd, general.SearchaddrL):
            self.searchaddr[7:0] = cmd.param
        elif isinstance(cmd, general.ProgramShortAddress):
            if self.initialising \
               and self.randomaddr == self.searchaddr:
                if cmd.address == 'MASK':
                    self.shortaddr = None
                else:
                    self.shortaddr = cmd.address
        elif isinstance(cmd, general.VerifyShortAddress):
            if self.initialising \
               and self.shortaddr == cmd.address:
                return _yes
        elif isinstance(cmd, general.DTR1):
            self.dtr1 = cmd.param
        elif isinstance(cmd, general.DTR2):
            self.dtr2 = cmd.param
        elif isinstance(cmd, general.EnableWriteMemory):
            self.enableWriteMemory = True
        elif isinstance(cmd, general.ReadMemoryLocation):
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
        elif isinstance(cmd, general.WriteMemoryLocation) \
             or isinstance(cmd, general.WriteMemoryLocationNoReply):  # noqa
            bank = self.memory_banks.get(self.dtr1)
            # "Only while writeEnableState is ENABLED, and the
            # addressed memory bank is implemented, the control gear
            # shall accept..."
            if not self.enableWriteMemory or not bank:
                return
            try:
                r = bank.write(self.dtr0, cmd.param)
                if isinstance(cmd, general.WriteMemoryLocation):
                    return r
            finally:
                if not bank.nobble_dtr0_update:
                    self.dtr0 = min(self.dtr0 + 1, 255)


class Bus:
    """A DALI bus

    Commands are sent (fake) simultaneously to all devices on the bus.
    If no devices respond, the response is None.  If one device
    responds, its response is used.  If multiple devices respond, a
    BackwardFrameError is used to represent the bus collision.
    """
    def __init__(self, gear):
        self.gear = gear

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
