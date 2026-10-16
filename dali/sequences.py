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

from typing import Optional, Generator, Literal, Iterable, TypeAlias
from typing_extensions import TypeVar
from dali.exceptions import DALISequenceError, ProgramShortAddressFailure
from dali import command
from dali.gear.general import (
    QueryDeviceType,
    QueryNextDeviceType,
    QueryGroupsZeroToSeven,
    QueryGroupsEightToFifteen,
    AddToGroup,
    RemoveFromGroup,
    SetSearchAddrH,
    SetSearchAddrM,
    SetSearchAddrL,
    Compare,
    DTR0,
    QueryControlGearPresent,
    Initialise,
    Randomise,
    Terminate,
    Withdraw,
    SetShortAddress,
    ProgramShortAddress,
    VerifyShortAddress,
)
from dali.address import GearAddress, GearBroadcast, GearShort


class sleep:
    """Delay for a while

    Yielded during a sequence to request that the caller wait for at
    least the specified length of time in seconds
    """
    def __init__(self, delay: float) -> None:
        self.delay = delay


class progress:
    """Progress information

    Yielded during a sequence to indicate how the sequence is
    proceeding.  May indicate an amount of progress, a message, or
    both.  The amount of progress is just an indication and there is
    no guarantee that it will not decrease as well as increase.
    """
    def __init__(self, message: Optional[str] = None,
                 completed: Optional[int] = None,
                 size: Optional[int] = None):
        self.message = message
        self.completed = completed
        self.size = size

    def __str__(self) -> str:
        if self.message:
            return self.message
        if self.completed is not None and self.size is not None:
            return f"Progress: {self.completed}/{self.size}"
        return "No progress"


# NB the "type" statement is only available from Python 3.12:
# type DALISequence[T=None] = Generator[
#     command.Command | sleep | progress,
#     Optional[command.Response], T]

# Here is the version that works on Python 3.11 and earlier using
# typing_extensions:
_T = TypeVar('_T', default=None)
DALISequence: TypeAlias = Generator[
    command.Command | sleep | progress,
    Optional[command.Response], _T]


def QueryDeviceTypes(
        addr: int | GearAddress
) -> DALISequence[list[int]]:
    """Obtain a list of part 2xx device types supported by control gear
    """
    r = yield QueryDeviceType(addr)
    assert isinstance(r, QueryDeviceType.response)
    if r.raw_value is None:
        raise DALISequenceError("No response to initial query")
    if r.raw_value.as_integer < 254:
        return [r.raw_value.as_integer]
    if r.raw_value.as_integer == 254:
        return []
    assert r.raw_value.as_integer == 255
    last_seen = 0
    result: list[int] = []
    while True:
        r = yield QueryNextDeviceType(addr)
        assert isinstance(r, QueryNextDeviceType.response)
        if r.raw_value is None:
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


def QueryGroups(addr: int | GearAddress) -> DALISequence[set[int]]:
    """Obtain the group membership of control gear.

    Returns a set of integers.
    """
    groups: set[int] = set()
    g0 = yield QueryGroupsZeroToSeven(addr)
    assert isinstance(g0, QueryGroupsZeroToSeven.response)
    if g0.raw_value is None:
        raise DALISequenceError("No response reading groups zero to seven")
    if g0.raw_value.error:
        raise DALISequenceError("Framing error reading groups zero to seven")
    g1 = yield QueryGroupsEightToFifteen(addr)
    assert isinstance(g1, QueryGroupsEightToFifteen.response)
    if g1.raw_value is None:
        raise DALISequenceError("No response reading groups eight to fifteen")
    if g1.raw_value.error:
        raise DALISequenceError("Framing error reading groups eight to fifteen")
    g = g1.raw_value + g0.raw_value
    for i in range(0, 16):
        if g[i]:
            groups.add(i)
    return groups


def SetGroups(
        addr: int | GearAddress, groups: set[int]
) -> DALISequence:
    """Set the group membership of control gear.

    groups is a set of integers in the range 0..15
    """
    if isinstance(addr, GearShort) or isinstance(addr, int):
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


def _find_next(
        low: int, high: int
) -> DALISequence[Optional[Literal["clash"] | int]]:
    yield SetSearchAddrH((high >> 16) & 0xff)
    yield SetSearchAddrM((high >> 8) & 0xff)
    yield SetSearchAddrL(high & 0xff)

    r = yield Compare()
    assert isinstance(r, Compare.response)
    if low == high:
        if r.as_boolean is True:
            return "clash" if r.raw_value and r.raw_value.error else low
        return None

    if r.value is True:
        midpoint = (low + high) // 2
        res = yield from _find_next(low, midpoint)
        if res is not None:
            return res
        return (yield from _find_next(midpoint + 1, high))
    return None


def Commissioning(
        available_addresses: Optional[Iterable[int]] = None,
        readdress: bool = False,
        dry_run: bool = False
) -> DALISequence:
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
            yield SetShortAddress(GearBroadcast())
    else:
        # We need to know which short addresses are already in use
        for a in range(0, 64):
            if a in available_addresses:
                in_use = yield QueryControlGearPresent(GearShort(a))
                assert isinstance(in_use, QueryControlGearPresent.response)
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

        low: Optional[int] = 0
        high = 0xffffff

        while low is not None:
            yield progress(completed=low, size=high)
            new_low = yield from _find_next(low, high)
            if new_low == "clash":
                yield progress(message="Multiple ballasts picked the same "
                               "random address; restarting")
                break
            elif new_low is None:
                low = None
                finished = True
                break
            else:
                low = new_low
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
                    assert isinstance(r, VerifyShortAddress.response)
                    if r.as_boolean is not True:
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
