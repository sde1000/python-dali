from enum import Enum, auto
from collections import namedtuple

from dali.exceptions import ResponseError
from dali.gear.general import ReadMemoryLocation, DTR0, DTR1, \
    WriteMemoryLocationNoReply


class MemoryType(Enum):
    ROM = auto()       # ROM
    RAM_RO = auto()    # RAM-RO
    RAM_RW = auto()    # RAM-RW
    NVM_RO = auto()    # NVM-RO
    NVM_RW = auto()    # NVM-RW
    NVM_RW_P = auto()  # NVM-RW (protectable)


class MemoryLocationNotImplemented(Exception):
    pass


class MemoryBank:
    class MemoryLocationOverlap(Exception):
        pass

    class LatchingNotSupported(Exception):
        pass

    MemoryBankEntry = namedtuple(
        'MemoryBankEntry', ['memory_location', 'memory_value'])

    def __init__(self, address, last_address, has_lock=False, has_latch=False):
        """Defines a memory bank at a given address.

        The address of the lock/latch byte can be defined by passing
        an int to has_lock/has_latch.
        """
        self.__address = address
        self.locations = {x: None for x in range(0xff)}

        # add value for last addressable location
        class LastAddress(MemoryValue):
            bank = self
            locations = (MemoryLocation(
                0x00, default=last_address,
                reset=last_address, type_=MemoryType.ROM),)

        if has_lock or has_latch:
            class LockByte(MemoryValue):
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

    def add_memory_location(self, memory_location, memory_value):
        if self.locations[memory_location.address]:
            raise self.MemoryLocationOverlap(
                f'Can not add overlapping MemoryLocation at address {memory_location.address}.')
        self.locations[memory_location.address] = self.MemoryBankEntry(
            memory_location, memory_value)

    def last_address(self, addr):
        """Sequence that returns the last available address in this bank
        """
        yield DTR1(self.address)
        yield DTR0(0x00)
        r = yield ReadMemoryLocation(addr)
        if r.raw_value is None:
            raise MemoryLocationNotImplemented(
                f'Device at address "{str(addr)}" does not implement {self}.')
        return r.raw_value.as_integer

    def read_all(self, addr):
        last_address = yield from self.last_address(addr)
        # Bank 0 has a useful value at address 0x02; all other banks
        # use this for the lock/latch byte
        start_address = 0x02 if self.address == 0 else 0x03
        # don't need to set DTR1, as we just did that in last_address()
        yield DTR0(start_address)
        raw_data = [None] * start_address
        for _ in range(start_address, last_address + 1):
            r = yield ReadMemoryLocation(addr)
            if r.raw_value is not None:
                raw_data.append(r.raw_value.as_integer)
            else:
                raw_data.append(None)
        result = {}
        for memory_value in set(
                [x.memory_value for x in self.locations.values() if x]):
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
        if self.LockByte and self.LockByte.latch:
            yield DTR1(self.address)
            yield DTR0(self.LockByte.locations[0].address)
            yield WriteMemoryLocationNoReply(0xAA, addr)
        else:
            raise self.LatchingNotSupported(f'Latching not supported for {str(self)}.')

    def is_locked(self, addr):
        """Check whether this bank is locked
        """
        if self.LockByte and self.LockByte.lock:
            r = yield from self.LockByte.read(addr)
            return r[0] != 0x55
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
            f'has_lock={bool(self.__lock_byte_address)}, ' \
            f'has_latch={bool(self.__latch_byte_address)})'


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


class MemoryRange:
    def __init__(self, start, end, default=None, reset=None, type_=None):
        self.__start = start
        self.__end = end
        self.__type_ = type_
        self.__default = default
        self.__reset = reset

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        return self.__end

    @property
    def type_(self):
        return self.__type_

    @property
    def default(self):
        return self.__default

    @property
    def reset(self):
        return self.__reset

    @property
    def locations(self):
        return tuple([
            MemoryLocation(address=address, default=self.default,
                           reset=self.reset, type_=self.type_)
            for address in range(self.start, self.end + 1)
        ])


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
            for location in cls.locations:
                cls.bank.add_memory_location(location, cls)

    def __str__(cls):
        if hasattr(cls, 'name'):
            return cls.name
        return super().__str__()


class MemoryValue(metaclass=_RegisterMemoryValue):
    """A group of memory locations that together represent a value

    This is an abstract base class. Concrete classes should declare
    the 'bank' and 'locations' attributes.

    'bank' must be a MemoryBank instance

    'locations' must be a sequence of MemoryLocation instances in the
    order required by the _to_value() method. It is most efficient if
    these memory locations are contiguous increasing in address.
    """
    @classmethod
    def _to_value(cls, raw):
        """Converts raw bytes to the wanted result."""
        return raw

    @classmethod
    def read(cls, addr):
        """Returns the value.

        Raises MemoryLocationNotImplemented exception if device does
        not respond, e.g. the location is not implemented.
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
        return cls._to_value(bytes(result))

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
        return cls._to_value(raw)

    @classmethod
    def is_addressable(cls, addr):
        """Checks whether this value is addressable

        Queries the value of the last addressable memory location for
        this memory bank
        """
        last_location = cls.locations[-1]
        try:
            last_address = yield from cls.bank.last_address(addr)
        except MemoryLocationNotImplemented:
            return False
        return last_address >= last_location.address

    @classmethod
    def is_locked(cls, addr):
        """Checks whether this value is locked
        """
        if cls.locations[0].type_ == MemoryType.NVM_RW_P:
            locked = yield from cls.bank.is_locked(addr)
            return locked
        else:
            return False


class NumericValue(MemoryValue):
    """Numeric value stored with MSB at the first location
    """
    unit = ''

    @classmethod
    def _to_value(cls, raw):
        return int.from_bytes(raw, 'big')


class FixedScaleNumericValue(NumericValue):
    """Numeric value with fixed scaling factor
    """
    scaling_factor = 1

    @classmethod
    def _to_value(cls, raw):
        return cls.scaling_factor * int.from_bytes(raw, 'big')


class StringValue(MemoryValue):
    @classmethod
    def _to_value(cls, raw):
        result = ''
        for value in raw:
            if value == 0:
                break  # string is Null terminated
            else:
                result += chr(value)
        return result


class BinaryValue(MemoryValue):
    @classmethod
    def _to_value(cls, raw):
        if raw[0] == 1:
            return True
        else:
            return False


class TemperatureValue(NumericValue):
    unit = '°C'
    offset = 60

    @classmethod
    def _to_value(cls, raw):
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
    def _to_value(cls, raw):
        if len(raw) == 1:
            n = super()._to_value(raw)
            if n == 0xff:
                return "not implemented"
            return f"{n >> 2}.{n & 0x3}"
        else:
            return '.'.join(str(x) for x in raw)
