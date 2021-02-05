from enum import Enum, auto
from functools import total_ordering

from dali.gear.general import ReadMemoryLocation, DTR0, DTR1

class MemoryType(Enum):
    ROM = auto()      # ROM
    RAM_RO = auto()   # RAM-RO
    RAM_RW = auto()   # RAM-RW
    NVM_RO = auto()   # NVM-RO
    NVM_RW = auto()   # NVM-RW
    NVM_RW_P = auto() # NVM-RW (protectable)

class MemoryBank:

    class WrongBank(Exception):
        pass

    class MemoryLocationOverlap(Exception):
        pass

    def __init__(self, address):
        self.__address = address
        self.locations = {x: None for x in range(0xff)}

    @property
    def address(self):
        return self.__address

    def add_memory_location(self, memory_location):
        if memory_location.bank.address != self.address:
            raise self.WrongBank(f'Can not add MemoryLocation of bank "{memory_location.bank.address}" to this bank ({self.address}).')
        if self.locations[memory_location.address]:
            raise self.MemoryLocationOverlap(f'Can not add overlapping MemoryLocation at address {memory_location.address}.')
        self.locations[memory_location.address] = memory_location

@total_ordering
class MemoryLocation:

    def __init__(self, bank, address, default = None, reset = None, type_ = None):
        self.__bank = bank
        self.__address = address
        self.__type_ = type_
        self.__default = default
        self.__reset = reset
        # tie this location to its respective memory bank
        bank.add_memory_location(self)
    
    @property
    def bank(self):
        return self.__bank

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

    def __eq__(self, other):
        if type(other) is not MemoryLocation:
            return NotImplemented
        return ((self.bank, self.address) == (other.bank, other.address))

    def __lt__(self, other):
        if type(other) is not MemoryLocation:
            return NotImplemented
        return ((self.bank, self.address) < (other.bank, other.address))
    
    def __repr__(self):
        return f'MemoryLocation(bank={self.bank}, address=0x{self.address:02x}, default={f"0x{self.default:02x}" if self.default is not None else None}, reset={f"0x{self.reset:02x}" if self.reset is not None else None}, type_={self.type_})'

class MemoryRange:

    def __init__(self, bank, start, end, default = None, reset = None, type_ = None):
        self.__bank = bank
        self.__start = start
        self.__end = end
        self.__type_ = type_
        self.__default = default
        self.__reset = reset
    
    @property
    def bank(self):
        return self.__bank

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
            MemoryLocation(bank=self.bank, address=address, default=self.default, reset=self.reset, type_=self.type_) \
            for address in range(self.start, self.end+1)
        ])

class MemoryValue:

    """Memory locations that belong to this value. Sorted from MSB to LSB."""
    locations = ()

    @classmethod
    def retrieve(cls, addr):
        """Retrieves this memory value through a sequence of DALI queries.

        @param addr: address of the DALI device (Address)
        """
        result = []
        dtr1 = None
        dtr0 = None
        for location in sorted(cls.locations):
            # select correct memory location
            if location.bank != dtr1:
                dtr1 = location.bank.address
                yield DTR1(location.bank.address)
            if location.address != dtr0:
                dtr0 = location.address
                yield DTR0(location.address)
            # read back value of the memory location
            r = yield ReadMemoryLocation(addr)
            # increase DTR0 to reflect the internal state of the driver
            dtr0 = min(dtr0+1, 255)
            result.append(r.raw_value.as_integer)
        return bytes(result)

    @classmethod
    def is_addressable(cls, addr):
        """Checks whether this value is addressable by querying the value of the last addressable memory location
        for this memory bank through a sequence of DALI queries.

        @param addr: address of the DALI device (Address)
        """
        last_location = cls.locations[-1]
        yield DTR1(last_location.bank)
        yield DTR0(0x00)
        r = yield ReadMemoryLocation(addr)

        return r.raw_value.as_integer > last_location.address

class LockableValueMixin:

    @classmethod
    def is_locked(cls, sync_driver, addr):
        """Check whether this value is locked. Returns True is value is locked or read-only. Returns false for values
        that can not be locked. Needs to be executed as a DALI sequence.

        @param addr: address of the DALI device (Address)
        """
        memory_type = cls.locations[0].type_
        if memory_type == MemoryType.NVM_RW_P:
            yield DTR1(cls.locations[0].bank)
            yield DTR0(0x02)
            lock_byte = cls.retrieve(addr)[0]
            return lock_byte != 0x55
        else:
            raise ValueError('MemoryType does not support locking')

class NumericValue(MemoryValue):

    """Unit of the numeric value. Set to one if no unit is given."""
    unit = 1

    @classmethod
    def retrieve(cls, addr):
        result = 0
        r = yield from super().retrieve(addr)
        for shift, value in enumerate(r[::-1]):
            result += value << (shift*8)
        return result

class ScaledNumericValue(MemoryValue):

    @classmethod
    def retrieve(cls, addr):
        result = 0
        r = yield from super().retrieve(addr)
        scale = r[0]
        # loop over all bytes except for the first one
        for shift, value in enumerate(r[:0:-1]):
            result += value << (shift*8)
        return result * 10.**scale

class FixedScaleNumericValue(NumericValue):

    """Fixed scaling factor."""
    scaling_factor = 1

    @classmethod
    def retrieve(cls, addr):
        r = yield from super().retrieve(addr)
        return cls.scaling_factor * r

class StringValue(MemoryValue):

    @classmethod
    def retrieve(cls, addr):
        result = ''
        r = yield from super().retrieve(addr)
        for value in r:
            if value == 0:
                break # string is Null terminated
            else:
                result += chr(value)
        return result

class BinaryValue(MemoryValue):

    @classmethod
    def retrieve(cls, addr):
        r = yield from super().retrieve(addr)
        if r == 1:
            return True
        else:
            return False

class TemperatureValue(NumericValue):

    unit = '°C'

    @classmethod
    def retrieve(cls, addr):
        r = yield from super().retrieve(addr)
        return r - 60

class ManufacturerSpecificValue(MemoryValue):

    pass
