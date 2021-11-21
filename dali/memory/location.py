from enum import Enum, auto
from collections import namedtuple

from dali.exceptions import ResponseError, LatchingNotSupported, \
    MemoryLocationNotImplemented, MemoryValueNotWriteable, \
    MemoryLocationNotWriteable, MemoryWriteFailure
from dali.gear.general import ReadMemoryLocation, DTR0, DTR1, \
    EnableWriteMemory, WriteMemoryLocation, WriteMemoryLocationNoReply, \
    QueryContentDTR0


class MemoryType(Enum):
    ROM = auto()       # ROM
    RAM_RO = auto()    # RAM-RO
    RAM_RW = auto()    # RAM-RW
    NVM_RO = auto()    # NVM-RO
    NVM_RW = auto()    # NVM-RW
    NVM_RW_L = auto()  # NVM-RW (lockable)
    NVM_RW_P = auto()  # NVM-RW (protectable — vendor-specific mechanism)


# These two exceptions are declared here rather than in dali.exceptions
# because they are configuration errors and will only be raised if
# a memory bank and its values are declared incorrectly.
class MemoryLocationOverlap(Exception):
    pass


class LockingNotSupported(Exception):
    pass


class MemoryBank:
    MemoryBankEntry = namedtuple(
        'MemoryBankEntry', ['memory_location', 'memory_value'])

    def __init__(self, address, last_address, has_lock=False, has_latch=False):
        """Declares a memory bank at a given address
        """
        self.__address = address
        self.locations = {x: None for x in range(0xff)}
        self.values = []

        # add value for last addressable location
        class LastAddress(NumericValue):
            bank = self
            locations = (MemoryLocation(
                0x00, default=last_address,
                reset=last_address, type_=MemoryType.ROM),)
        self.LastAddress = LastAddress

        if has_lock or has_latch:
            class LockByte(NumericValue):
                bank = self
                lock = has_lock
                latch = has_latch
                locations = (MemoryLocation(
                    0x02, reset=0xff, default=0xff, type_=MemoryType.RAM_RW),)
            self.LockByte = LockByte
        else:
            self.LockByte = None

    @property
    def address(self):
        return self.__address

    @property
    def has_lock(self):
        return bool(self.LockByte and self.LockByte.lock)

    @property
    def has_latch(self):
        return bool(self.LockByte and self.LockByte.latch)

    def _add_memory_value(self, memory_value):
        self.values.append(memory_value)
        for location in memory_value.locations:
            if self.locations[location.address]:
                raise self.MemoryLocationOverlap(
                    f'Overlapping MemoryLocation at address {location.address}')
            if location.type_ == MemoryType.NVM_RW_L and not self.has_lock:
                raise self.LockingNotSupported()
            self.locations[location.address] = self.MemoryBankEntry(
                location, memory_value)

    def last_address(self, addr):
        """Sequence that returns the last available address in this bank
        """
        la = yield from self.LastAddress.read(addr)
        return la

    def read_all(self, addr, use_latch=True):
        """Read all available memory values from this memory bank.

        If the memory bank has a latch, the latch is set during the
        read so that the memory values represent a snapshot in
        time. If you don't want this behaviour, pass use_latch=False.
        """
        last_address = yield from self.LastAddress.read(addr)
        # Reading the last address also sets DTR1 appropriately
        dtr0 = 1
        if use_latch and self.has_latch:
            yield EnableWriteMemory(addr)
            yield DTR0(2)
            yield WriteMemoryLocationNoReply(0xaa)
            dtr0 = 3
        # Bank 0 has a useful value at address 0x02; all other banks
        # use this for the lock/latch byte
        start_address = 0x02 if self.address == 0 else 0x03
        if dtr0 != start_address:
            yield DTR0(start_address)
        raw_data = [None] * start_address
        for loc in range(start_address, last_address + 1):
            r = yield ReadMemoryLocation(addr)
            if r.raw_value is not None:
                if r.raw_value.error:
                    raise ResponseError(
                        f"Framing error while reading memory bank "
                        f"{self.address} location {loc}")
                raw_data.append(r.raw_value.as_integer)
            else:
                raw_data.append(None)
        if use_latch and self.has_latch:
            yield DTR0(2)
            yield WriteMemoryLocationNoReply(0xff)
        result = {}
        for memory_value in self.values:
            try:
                r = memory_value.from_list(raw_data)
            except MemoryLocationNotImplemented:
                pass
            else:
                result[memory_value] = r
        return result

    def latch(self, addr):
        """(Re-)latch all memory locations of this bank.

        Raises LatchingNotSupported exception if bank does not support
        latching.
        """
        if self.has_latch:
            yield from self.LockByte.write(addr, 0xaa, ignore_feedback=True)
        else:
            raise LatchingNotSupported(
                f'Latching not supported for {str(self)}.')

    def unlatch(self, addr):
        """Unlatch all memory locations of this bank.

        Raises LatchingNotSupported exception if bank does not support
        latching.
        """
        if self.has_latch:
            yield from self.LockByte.write(addr, 0xff, ignore_feedback=True)
        else:
            raise LatchingNotSupported(
                f'Latching not supported for {str(self)}.')

    def is_locked(self, addr):
        """Check whether this bank is locked
        """
        if self.has_lock:
            r = yield from self.LockByte.read(addr)
            return r != 0x55
        else:
            return False

    def factory_default_contents(self):
        """Return factory default contents for known memory locations
        """
        for address in range(0xff):
            loc = self.locations[address]
            yield loc.memory_location.default if loc else None

    def __repr__(self):
        return f'MemoryBank(address={self.address}, ' \
            f'has_lock={bool(self.LockByte and self.LockByte.lock)}, ' \
            f'has_latch={bool(self.LockByte and self.LockByte.latch)})'


# It would be nice to implement MemoryLocation as follows:
#
# MemoryLocation = namedtuple(
#     'MemoryLocation', ['address', 'default', 'reset', 'type_'],
#     defaults=[None] * 3)
#
# Unfortunately the 'defaults' keyword argument is only available from
# Python 3.7

class MemoryLocation:
    def __init__(self, address, default=None, reset=None, type_=None):
        self.__address = address
        self.__type_ = type_
        self.__default = default
        self.__reset = reset

    @property
    def address(self):
        return self.__address

    @property
    def type_(self):
        return self.__type_

    @property
    def default(self):
        return self.__default

    @property
    def reset(self):
        return self.__reset

    def __repr__(self):
        return f'MemoryLocation(address=0x{self.address:02x}, ' \
            f'default={f"0x{self.default:02x}" if self.default is not None else None}, ' \
            f'reset={f"0x{self.reset:02x}" if self.reset is not None else None}, ' \
            f'type_={self.type_})'


def MemoryRange(start, end, **kwargs):
    return tuple(
        MemoryLocation(address, **kwargs) for address in range(start, end + 1)
    )


class _RegisterMemoryValue(type):
    """Metaclass to register new MemoryValue classes
    """
    def __init__(cls, name, bases, attrs):
        # cls is the new MemoryValue subclass; it already exists, it's
        # being initialised
        if hasattr(cls, 'locations'):
            if not hasattr(cls, 'bank'):
                raise Exception(
                    f"MemoryValue subclass {name} missing 'bank' attribute")
            cls.name = name
            # Shorthand: locations can be a single MemoryLoction instance
            if isinstance(cls.locations, MemoryLocation):
                cls.locations = (cls.locations, )
            cls.bank._add_memory_value(cls)

            # Some types of value may need to adjust the number of
            # bytes for 'mas' or 'tmask'
            num_loc = len(cls.locations) + getattr(cls, 'mask_length_adjust', 0)

            if cls.mask_supported:
                if cls.signed:
                    cls.mask = (pow(2, num_loc * 8 - 1) - 1).to_bytes(
                        num_loc, 'big', signed=True)
                else:
                    cls.mask = (pow(2, num_loc * 8) - 1).to_bytes(
                        num_loc, 'big')

            if cls.tmask_supported:
                if cls.signed:
                    cls.tmask = (pow(2, num_loc * 8 - 1) - 2).to_bytes(
                        num_loc, 'big', signed=True)
                else:
                    cls.tmask = (pow(2, num_loc * 8) - 2).to_bytes(
                        num_loc, 'big')

    def __str__(cls):
        if hasattr(cls, 'name'):
            return cls.name
        return super().__str__()


class FlagValue(Enum):
    Invalid = "Invalid"  # Memory value not valid according to the standard
    MASK = "MASK"        # Memory value not implemented
    TMASK = "TMASK"      # Memory value temporarily unavailable


class MemoryValue(metaclass=_RegisterMemoryValue):
    """A group of memory locations that together represent a value

    This is an abstract base class. Concrete classes should declare
    the 'bank' and 'locations' attributes.

    'bank' must be a MemoryBank instance

    'locations' must be a sequence of MemoryLocation instances in the
    order required by the _to_value() method. It is most efficient if
    these memory locations are contiguous increasing in address.
    """
    # Is MASK a possible value?  MASK is part of the DiiA extended
    # memory bank specifications, parts 252 and 253.
    mask_supported = False

    # Is TMASK a possible value?  TMASK is part of the DiiA extended
    # memory bank specifications, parts 252 and 253.
    tmask_supported = False

    # Should the value be treated as signed when checking for MASK
    # and/or TMASK?
    signed = False

    @classmethod
    def raw_to_value(cls, raw):
        """Converts raw bytes to the wanted result

        This method should only be called with valid values for 'raw'.
        Checks for invalid and special values should be performed first.
        """
        return raw

    @classmethod
    def value_to_raw(cls, value):
        """Converts a value to raw bytes to write to the memory bank

        If the conversion cannot be performed, raises ValueError
        """
        raise ValueError

    @classmethod
    def is_valid(cls, raw):
        """Check whether raw bytes are valid for this memory value"""
        return True

    @classmethod
    def check_raw(cls, raw):
        """Check for invalid or special patterns in raw bytes

        Returns None if no invalid or special patterns were found, otherwise
        returns the appropriate FlagValue
        """
        if cls.mask_supported:
            if raw == cls.mask:
                return FlagValue.MASK
        if cls.tmask_supported:
            if raw == cls.tmask:
                return FlagValue.TMASK
        if not cls.is_valid(raw):
            return FlagValue.Invalid

    @classmethod
    def read_raw(cls, addr):
        """Read the value from the bus unit without interpretation

        Raises MemoryLocationNotImplemented if the device does
        not respond, e.g. the location is not implemented.

        Returns a bytes() object with the same length as cls.locations
        """
        result = []
        dtr0 = None
        yield DTR1(cls.bank.address)
        for location in cls.locations:
            # select correct memory location
            if location.address != dtr0:
                dtr0 = location.address
                yield DTR0(location.address)
            # read back value of the memory location
            r = yield ReadMemoryLocation(addr)
            # increase DTR0 to reflect the internal state of the driver
            dtr0 = min(dtr0 + 1, 255)
            if r.raw_value is None:
                raise MemoryLocationNotImplemented(
                    f'Bus unit at address "{str(addr)}" does not implement '
                    f'memory bank {cls.bank.address} {str(location)}.')
            if r.raw_value.error:
                raise ResponseError(
                    f'Framing error in response from bus unit at address '
                    f'"{str(addr)}" while reading '
                    f'memory bank {cls.bank.address} {str(location)}.')
            result.append(r.raw_value.as_integer)
        return bytes(result)

    @classmethod
    def read(cls, addr):
        """Read the value from the bus unit

        Raises MemoryLocationNotImplemented if the device does not respond.

        Returns an interpreted value if possible, otherwise a FlagValue
        """
        raw = yield from cls.read_raw(addr)
        return cls.check_raw(raw) or cls.raw_to_value(raw)

    @classmethod
    def from_list(cls, list_):
        """Extracts the value from a list containing all values of the memory bank.
        """
        raw = []
        for location in cls.locations:
            try:
                r = list_[location.address]
            except IndexError:
                raise MemoryLocationNotImplemented(f'List is missing memory location {str(location)}.')
            if r is None:
                raise MemoryLocationNotImplemented(f'List is missing memory location {str(location)}.')
            raw.append(r)
        raw = bytes(raw)
        return cls.check_raw(raw) or cls.raw_to_value(raw)

    @classmethod
    def write_raw(cls, addr, raw, allow_short_write=False,
                  force_unlock=False, ignore_feedback=False):
        """Write a value to the bus unit without interpretation

        Raises MemoryLocationNotWriteable if the memory location is
        not of an appropriate type. If the value to be written is of
        the wrong length, raises ValueError. Pass
        allow_short_write=True if you need to write less than the full
        memory value length (for example, a null-terminated string).

        Handles unlocking and relocking the memory bank if the memory
        location types indicate that this is required. This can be
        forced by passing force_unlock=True.

        By default, checks responses from the bus unit and raises
        MemoryLocationNotWriteable if the bus unit responds to the
        write with NO or MemoryWriteError if the post-write check of
        DTR0 yields an unexpected value. If the bus unit responds with
        an incorrect value or framing error, raises
        ResponseError. These checks can be skipped by setting
        ignore_feedback=True.
        """
        if allow_short_write:
            if len(raw) > len(cls.locations):
                raise ValueError("Raw data too long")
        else:
            if len(raw) != len(cls.locations):
                raise ValueError("Incorrect raw data length")
        unlock_required = force_unlock
        # Check that all locations are writeable
        for location in cls.locations:
            if location.type_ not in (
                    MemoryType.RAM_RW, MemoryType.NVM_RW,
                    MemoryType.NVM_RW_L, MemoryType.NVM_RW_P):
                raise MemoryValueNotWriteable(
                    f"{str(cls)} is not a writeable MemoryValue")
            # Memory of type NVM_RW_P may be write (or read!)
            # protected, but there is no standard way of unprotecting
            # it.
            if location.type_ == MemoryType.NVM_RW_L:
                unlock_required = True

        dtr0 = None
        yield DTR1(cls.bank.address)
        yield EnableWriteMemory(addr)
        if unlock_required:
            yield DTR0(2)
            yield WriteMemoryLocationNoReply(0x55)
            dtr0 = 3
        for location, value in zip(cls.locations, raw):
            if location.address != dtr0:
                yield DTR0(location.address)
                dtr0 = location.address
            if ignore_feedback:
                yield WriteMemoryLocationNoReply(value)
            else:
                r = yield WriteMemoryLocation(value)
                if r.raw_value is None:
                    raise MemoryLocationNotWriteable(
                        f'Bus unit at address "{str(addr)}" responded NO to '
                        f'write of memory bank {cls.bank.address} location '
                        f'{location.address}.')
                if r.raw_value.error:
                    raise ResponseError(
                        f'Framing error in response from bus unit at address '
                        f'"{str(addr)}" while writing memory bank '
                        f'{cls.bank.address} location {location.address}.')
                if r.raw_value.as_integer != value:
                    raise ResponseError(
                        f'Incorrect value in response from bus unit at address '
                        f'"{str(addr)}" while writing memory bank '
                        f'{cls.bank.address} location {location.address}. '
                        f'Expected: {value}, received {r.raw_value.as_integer}')
            dtr0 = min(dtr0 + 1, 255)
        if not ignore_feedback:
            # IEC 62386-102 section 9.10.6 recommends that the
            # application controller checks the value of DTR0 to
            # verify it is at the expected location, with any mismatch
            # indicating an error while writing.
            r = yield QueryContentDTR0(addr)
            if r.raw_value is None:
                raise ResponseError(
                    f'Bus unit at address "{str(addr)}" responded NO to '
                    f'check of DTR0')
            if r.raw_value.error:
                raise ResponseError(
                    f'Framing error in response from bus unit at address '
                    f'"{str(addr)}" while checking DTR0 after write')
            if r.raw_value.as_integer != dtr0:
                raise MemoryWriteFailure(
                    f'Incorrect value in response from bus unit at address '
                    f'"{str(addr)}" while checking DTR0 after writing memory '
                    f'bank {cls.bank.address}. '
                    f'Expected: {dtr0}, received {r.raw_value.as_integer}')
        if unlock_required:
            yield DTR0(2)
            yield WriteMemoryLocationNoReply(0xff)

    @classmethod
    def write(cls, addr, value, **kwargs):
        raw = cls.value_to_raw(value)
        yield from cls.write_raw(addr, raw, **kwargs)

    @classmethod
    def is_addressable(cls, addr):
        """Checks whether this value is addressable

        Queries the value of the last addressable memory location for
        this memory bank
        """
        last_location = max(loc.address for loc in cls.locations)
        try:
            last_address = yield from cls.bank.last_address(addr)
        except MemoryLocationNotImplemented:
            return False
        return last_address >= last_location

    @classmethod
    def is_locked(cls, addr):
        """Checks whether this value is locked
        """
        if cls.locations[0].type_ == MemoryType.NVM_RW_L:
            locked = yield from cls.bank.is_locked(addr)
            return locked
        else:
            return False


class NumericValue(MemoryValue):
    """Numeric value stored with MSB at the first location
    """
    unit = ''
    min_value = None
    max_value = None

    @classmethod
    def raw_to_value(cls, raw):
        return int.from_bytes(raw, 'big', signed=cls.signed)

    @classmethod
    def value_to_raw(cls, value):
        if cls.mask_supported and value == 'MASK':
            return cls.mask
        if cls.tmask_supported and value == 'TMASK':
            return cls.tmask
        if not isinstance(value, int):
            raise ValueError("An int is required here")
        return value.to_bytes(len(cls.locations), 'big', signed=cls.signed)

    @classmethod
    def is_valid(cls, raw):
        trial = int.from_bytes(raw, 'big', signed=cls.signed)
        if cls.min_value is not None:
            if trial < cls.min_value:
                return False
        if cls.max_value is not None:
            if trial > cls.max_value:
                return False
        return True


class FixedScaleNumericValue(NumericValue):
    """Numeric value with fixed scaling factor
    """
    scaling_factor = 1

    @classmethod
    def raw_to_value(cls, raw):
        return cls.scaling_factor * super().raw_to_value(raw)


class StringValue(MemoryValue):
    """An ASCII string, possibly NULL terminated

    Valid ASCII characters are in the range 1..0x7f. If values outside
    this range are encountered while reading from the memory location,
    FlagValue.Invalid will be returned.
    """
    @classmethod
    def raw_to_value(cls, raw):
        try:
            return raw.split(b'\x00')[0].decode('ascii')
        except UnicodeDecodeError:
            return FlagValue.Invalid

    @classmethod
    def value_to_raw(cls, value):
        raw = value.encode('ascii')
        if len(raw) > len(cls.locations):
            raise ValueError("String is too long to write to location")
        if len(raw) < len(cls.locations):
            raw = raw + b'\x00'
        return raw

    @classmethod
    def write(cls, addr, value, **kwargs):
        kwargs['allow_short_write'] = True
        return super().write(addr, value, **kwargs)


class BinaryValue(MemoryValue):
    @classmethod
    def raw_to_value(cls, raw):
        if raw[0] == 1:
            return True
        else:
            return False

    @classmethod
    def is_valid(cls, raw):
        return raw[0] in (0, 1)


class TemperatureValue(NumericValue):
    unit = '°C'
    offset = 60

    @classmethod
    def raw_to_value(cls, raw):
        return int.from_bytes(raw, 'big') - cls.offset


class VersionNumberValue(NumericValue):
    """A version number

    When encoded into a byte, IEC 62386 part 102 section 4.2 states
    that a version shall be in the format "x.y", where the major
    version number x is in the range 0..62 and the minor version
    number y is in the range 0..2. The major version number is placed
    in bits 7:2 and the minor version number is in bits 1:0. Part 102
    section 9.10.6 states that the value 0xff is reserved for "not
    implemented" when used for Part 102 and 103 versions in memory bank 0.

    When encoded into two bytes, the major version number is in the
    first byte and the minor version number is in the second byte.
    """
    @classmethod
    def raw_to_value(cls, raw):
        if len(raw) == 1:
            n = super().raw_to_value(raw)
            if n == 0xff:
                return "not implemented"
            return f"{n >> 2}.{n & 0x3}"
        else:
            return '.'.join(str(x) for x in raw)
