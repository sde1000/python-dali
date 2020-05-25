# Useful sequences of commands

# These command sequences can be passed to a driver for execution as a
# transaction.

# A command sequence is a generator co-routine.  It yields a series of
# objects, and optionally returns a result.

# The command sequence can yield the following types of object:
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

def QueryDeviceTypes(addr):
    """Obtain a list of part 2xx device types supported by control gear
    """
    r = yield QueryDeviceType(addr)
    if r.raw_value is None:
        raise DALISequenceError("No response to initial query")
    if r.raw_value.as_integer < 254:
        return [r.raw_value.as_integer]
    if r.raw_value.as_integer == 254:
        return []
    assert r.raw_value.as_integer == 255
    last_seen = 0
    result = []
    while True:
        r = yield QueryNextDeviceType(addr)
        if not r.raw_value:
            raise DALISequenceError(
                "No response to QueryNextDeviceType()")
        if r.raw_value.as_integer == 254:
            if len(result) == 0:
                raise DALISequenceError(
                    "No device types returned by QueryNextDeviceType")
            return result
        if r.raw_value.as_integer <= last_seen:
            # The gear is required to return device types in
            # ascending order, without repeats
            raise DALISequenceError("Device type received out of order")
        result.append(r.raw_value.as_integer)

def QueryGroups(addr):
    """Obtain the group membership of control gear.

    Returns a set of integers.
    """
    groups = set()
    g0 = yield QueryGroupsZeroToSeven(addr)
    if g0.raw_value is None:
        raise DALISequenceError("No response reading groups zero to seven")
    if g0.raw_value.error:
        raise DALISequenceError("Framing error reading groups zero to seven")
    g1 = yield QueryGroupsEightToFifteen(addr)
    if g1.raw_value is None:
        raise DALISequenceError("No response reading groups eight to fifteen")
    if g1.raw_value.error:
        raise DALISequenceError("Framing error reading groups eight to fifteen")
    g = g1.raw_value + g0.raw_value
    for i in range(0, 16):
        if g[i]:
            groups.add(i)
    return groups

def SetGroups(addr, groups):
    """Set the group membership of control gear.

    groups is a set of integers in the range 0..15
    """
    if isinstance(addr, Short) or isinstance(addr, int):
        existing = yield from QueryGroups(addr)
        for i in groups - existing:
            yield AddToGroup(addr, i)
        for i in existing - groups:
            yield RemoveFromGroup(addr, i)
    else:
        # Can't read from multiple devices: must write every group
        for i in range(0, 16):
            if i in groups:
                yield AddToGroup(addr, i)
            else:
                yield RemoveFromGroup(addr, i)

def _find_next(low, high):
    yield SetSearchAddrH((high >> 16) & 0xff)
    yield SetSearchAddrM((high >> 8) & 0xff)
    yield SetSearchAddrL(high & 0xff)

    r = yield Compare()

    if low == high:
        if r.value == True:
            return "clash" if r.raw_value.error else low
        return

    if r.value == True:
        midpoint = (low + high) // 2
        res = yield from _find_next(low, midpoint)
        if res is not None:
            return res
        return (yield from _find_next(midpoint + 1, high))

def Commissioning(available_addresses=None, readdress=False,
                  dry_run=False):
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
    if available_addresses is None:
        available_addresses = list(range(64))
    else:
        available_addresses = list(available_addresses)

    if readdress:
        if dry_run:
            yield progress(message="dry_run is set: not deleting existing "
                           "short addresses")
        else:
            yield DTR0(255)
            yield SetShortAddress(Broadcast())
    else:
        # We need to know which short addresses are already in use
        for a in range(0, 64):
            if a in available_addresses:
                in_use = yield QueryControlGearPresent(Short(a))
                if in_use.value:
                    available_addresses.remove(a)
        yield progress(
            message=f"Available addresses: {available_addresses}")

    yield Terminate()
    yield Initialise(broadcast=True if readdress else False)

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
            low = yield from _find_next(low, high)
            if low == "clash":
                yield progress(message="Multiple ballasts picked the same "
                                   "random address; restarting")
                break
            if low is None:
                finished = True
                break
            yield progress(
                message=f"Ballast found at address {low:#x}")
            if available_addresses:
                new_addr = available_addresses.pop(0)
                if dry_run:
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
    yield Terminate()
    yield progress(message="Addressing complete")
