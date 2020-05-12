# Useful sequences of commands

# These command sequences can be passed to a driver for execution as a
# transaction.

# A command sequence is a class.  Any arguments to be passed into it
# are passed to the class constructor.  Class instances must have a
# "run" method that is a generator co-routine that takes no arguments,
# and may have a "result" attribute which is the value to be returned
# by the driver to the caller.  They may support other methods and
# attributes if they wish; the "run_sequence" method of drivers must
# also support being passed a generator instead of class instance.

# The generator co-routine can yield the following types of object:
#
# * dali.command.Command instances for execution; the response must be
#   passed back into the sequence via .send() on the generator
#
# * dali.sequence.sleep instances to request a delay in execution
#
# * dali.sequence.progress instances to provide updates on sequence execution

# Sequences may raise exceptions, which the driver should pass to the
# caller.

from dali.exceptions import DALISequenceError, ProgramShortAddressFailure

from dali.gear.general import *
from dali.address import Broadcast, Short

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

    def __str__(self):
        if self.message:
            return self.message
        if self.completed is not None and self.size is not None:
            return f"Progress: {self.completed}/{self.size}"

class QueryDeviceTypes:
    """Obtain a list of part 2xx device types supported by control gear
    """
    def __init__(self, addr):
        self.addr = addr
        self.result = []

    def run(self):
        r = yield QueryDeviceType(self.addr)
        if r.raw_value is None:
            raise DALISequenceError("No response to initial query")
        if r.raw_value.as_integer < 254:
            self.result = [r.raw_value.as_integer]
            return
        if r.raw_value.as_integer == 255:
            last_seen = 0
            while True:
                r = yield QueryNextDeviceType(self.addr)
                if not r.raw_value:
                    raise DALISequenceError(
                        "No response to QueryNextDeviceType()")
                if r.raw_value.as_integer == 254:
                    if len(self.result) == 0:
                        raise DALISequenceError(
                            "No device types returned by QueryNextDeviceType")
                    return
                if r.raw_value.as_integer <= last_seen:
                    # The gear is required to return device types in
                    # ascending order, without repeats
                    raise DALISequenceError("Device type received out of order")
                self.result.append(r.raw_value.as_integer)

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
        if available_addresses is None:
            self.available_addresses = list(range(64))
        else:
            self.available_addresses = list(available_addresses)
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
            if self._find_next_result is not None:
                return
            yield from self._find_next(midpoint + 1, high)
            return

        self._find_next_result = None

    def run(self):
        if not self.readdress:
            # We need to know which short addresses are already in use
            for a in range(0, 64):
                if a in self.available_addresses:
                    in_use = yield QueryControlGearPresent(Short(a))
                    if in_use.value:
                        self.available_addresses.remove(a)
            yield progress(
                message=f"Available addresses: {self.available_addresses}")

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
                        message=f"Ballast found at address {low:#x}")
                    if self.available_addresses:
                        new_addr = self.available_addresses.pop(0)
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
                    if low < high:
                        low = low + 1
                    else:
                        low = None
                        finished = True
                else:
                    finished = True
        yield Terminate()
        yield progress(message="Addressing complete")
