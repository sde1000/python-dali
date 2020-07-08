# Fake hardware for testing
from dali import frame
from dali.address import Broadcast, BroadcastUnaddressed, Group, Short
from dali.command import Command
from dali.gear import general
from dali.sequences import progress
import random

_yes = 0xff

class Gear:
    """Control gear on a DALI bus

    Receives Command objects and returns None for no response, or an
    integer in the range 0..255 to indicate responding with an 8-bit
    backward frame.
    """
    def __init__(self, shortaddr=None, groups = set(),
                 devicetypes = [], random_preload=[]):
        self.shortaddr = shortaddr
        self.scenes = [255] * 16
        self.groups = set(groups)
        self.devicetypes = devicetypes
        self.random_preload = random_preload
        self.initialising = False
        self.withdrawn = False
        self.dt_gap = 1 # Number of commands since last QueryNextDeviceType
        self.dt_queue = [] # Devices still to be returned by QueryNextDeviceType
        self.randomaddr = frame.Frame(24)
        self.searchaddr = frame.Frame(24)
        self.dtr0 = 0
        self.dtr1 = 0
        self.dtr2 = 0

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
            return self.shortaddr == None
        if isinstance(cmd.destination, Short):
            return cmd.destination.address == self.shortaddr
        if isinstance(cmd.destination, Group):
            return cmd.destination.group in self.groups

    def send(self, cmd):
        self.dt_gap += 1
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
            if self.shortaddr == None:
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
