# Useful sequences of commands

# These sequences can be passed to a driver for execution as a
# transaction.

# Sequences may raise exceptions.
from dali.exceptions import DALIError

class DALISequenceError(DALIError):
    pass

from dali.gear.general import *
from dali.address import Broadcast

class sleep:
    """Delay for a while

    Yielded during a sequence to request that the caller wait for at
    least the specified length of time in seconds
    """
    def __init__(self, delay):
        self.delay = delay

class progress:
    """Progress information

    Yielded during a sequence to indicate how the sequence is
    proceeding.  May indicate an amount of progress, a message, or
    both.  The amount of progress is just an indication and there is
    no guarantee that it will not decrease as well as increase.
    """
    def __init__(self, message=None, completed=None, size=None):
        self.message = message
        self.completed = completed
        self.size = size

class QueryDeviceTypes:
    """Obtain a list of part 2xx device types supported by control gear
    """
    def __init__(self, addr):
        self.addr = addr
        self.device_types = []

    def run(self):
        r = yield QueryDeviceType(self.addr)
        if r.raw_value is None:
            raise DALISequenceError("No response to initial query")
        if r.raw_value.as_integer < 254:
            self.device_types.append(r.raw_value.as_integer)
            return
        if r.raw_value.as_integer == 255:
            last_seen = 0
            while True:
                r = yield QueryNextDeviceType(addr)
                if not r.raw_value:
                    raise DALISequenceError(
                        "No response to QueryNextDeviceType()")
                if r.raw_value.as_integer == 254:
                    return
                if r.raw_value.as_integer <= last_seen:
                    # The gear is required to return device types in
                    # ascending order, without repeats
                    raise DALISequenceError("Device type received out of order")
                self.device_types.append(r.raw_value.as_integer)

class Commissioning:
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
    def __init__(self, available_addresses=None, readdress=False,
                 dry_run=False):
        self.available_addresses = available_addresses
        self.readdress = readdress
        self.dry_run = dry_run

    def _find_next(self, low, high):
        yield SetSearchAddrH((high >> 16) & 0xff)
        yield SetSearchAddrM((high >> 8) & 0xff)
        yield SetSearchAddrL(high & 0xff)

        r = yield Compare()

        if low == high:
            if r.value == True:
                self._find_next_result = "clash" if r.raw_value.error else low
            else:
                self._find_next_result = None
            return

        if r.value == True:
            midpoint = (low + high) // 2
            yield from self._find_next(low, midpoint)
            if self._find_next_result:
                return
            yield from self._find_next(midpoint + 1, high)
            return

        self._find_next_result = None

    def run(self):
        available_addresses = self.available_addresses or list(range(0, 64))

        if not self.readdress:
            # We need to know which short addresses are already in use
            for a in range(0, 64):
                in_use = yield QueryControlGearPresent(Short(a))
                if in_use.value and in_use.value in available_addresses:
                    available_addresses.remove(a)
            yield progress(
                message=f"Available addresses: {available_addresses}")

        if self.readdress:
            if self.dry_run:
                yield progress(message="dry_run is set: not deleting existing "
                               "short addresses")
            else:
                yield DTR0(255)
                yield SetShortAddress(Broadcast())

        yield Terminate()
        yield Initialise(broadcast=True if self.readdress else False)

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
                yield from self._find_next(low, high)
                low = self._find_next_result
                if low == "clash":
                    yield progress(message="Multiple ballasts picked the same "
                                   "random address; restarting")
                    break
                if low is not None:
                    yield progress(
                        message="Ballast found at address %x" % low)
                    if available_addresses:
                        new_addr = available_addresses.pop(0)
                        if self.dry_run:
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
                    low = low + 1 if low < high else None
                else:
                    finished = True
        yield Terminate()
        yield progress(message="Addressing complete")
