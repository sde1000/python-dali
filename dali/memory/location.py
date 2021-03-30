from enum import Enum, auto
from functools import total_ordering
from collections import namedtuple

from dali.gear.general import ReadMemoryLocation, DTR0, DTR1, WriteMemoryLocationNoReply

class MemoryType(Enum):
    ROM = auto()      # ROM
    RAM_RO = auto()   # RAM-RO
    RAM_RW = auto()   # RAM-RW
    NVM_RO = auto()   # NVM-RO
    NVM_RW = auto()   # NVM-RW
    NVM_RW_P = auto() # NVM-RW (protectable)

class MemoryLocationNotImplemented(Exception):
    pass

class MemoryBank:

    class WrongBank(Exception):
        pass

    class MemoryLocationOverlap(Exception):
        pass

    class LatchingNotSupported(Exception):
        pass

    MemoryBankEntry = namedtuple('MemoryBankEntry', ['address', 'memory_location', 'memory_value'])

    def __init__(self, address, last_address, has_lock=False, has_latch=False):
        """Defines a memory bank at a given address.
        The address of the lock/latch byte can be defined by passing an int to has_lock/has_latch."""
        self.__address = address
        self.locations = {x: None for x in range(0xff)}
        # add value for last addressable location
        _ = MemoryValue(
            'LastAddress', 
            (MemoryLocation(self, 0x00, default=last_address, reset=last_address, type_=MemoryType.RAM_RW),)
        )
        self.__lock_byte_address = None
        self.__latch_byte_address = None
        if has_lock:
            if type(has_lock) == int:
                self.__lock_byte_address = has_lock
            else:
                self.__lock_byte_address = 0x02
        if has_latch:
            if type(has_lock) == int:
                self.__latch_byte_address = has_latch
            else:
                self.__latch_byte_address = 0x02

    @property
    def address(self):
        return self.__address

    def add_memory_location(self, memory_location, memory_value):
        if memory_location.bank.address != self.address:
            raise self.WrongBank(f'Can not add MemoryLocation of bank "{memory_location.bank.address}" to this bank ({self.address}).')
        if self.locations[memory_location.address]:
            raise self.MemoryLocationOverlap(f'Can not add overlapping MemoryLocation at address {memory_location.address}.')
        self.locations[memory_location.address] = self.MemoryBankEntry(memory_location.address, memory_location, memory_value)

    def last_address(self, addr):
        """Returns the last available address in this bank through a sequence of DALI queries."""
        yield DTR1(self.address)
        yield DTR0(0x00)
        r = yield ReadMemoryLocation(addr)
        if r.raw_value is None:
            raise MemoryLocationNotImplemented(f'Device at address "{str(addr)}" does not implement {self}.')
        return r.raw_value.as_integer
    
    def read_all(self, addr):
        last_address = yield from self.last_address(addr)
        # don't need to set DTR1, as we just did that in last_address()
        yield DTR0(0x03)
        raw_data = [None, None, None] # ignore first three bytes
        for _ in range(0x03, last_address+1):
            r = yield ReadMemoryLocation(addr)
            if r.raw_value is not None:
                raw_data.append(r.raw_value.as_integer)
            else:
                raw_data.append(None)
        result = {}
        for memory_value in set([x.memory_value for x in self.locations.values() if x]):
            try:
                r = memory_value.from_list(raw_data)
            except MemoryLocationNotImplemented:
                pass
            else:
                result[memory_value.name] = r
        return result
    
    def latch(self, addr):
        """Generates the commands to (re-)latch all memory locations of this bank.
        Raises LatchingNotSupported exception if bank does not support latching."""
        if self.__latch_byte_address:
            yield DTR1(self.address)
            yield DTR0(self.__latch_byte_address)
            yield WriteMemoryLocationNoReply(0xAA, addr)
        else:
            raise self.LatchingNotSupported(f'Latching not supported for {str(self)}.')

    def is_locked(self, addr):
        """Generates the commands to check whether this bank is locked and returns the result."""
        if self.__lock_byte_address:
            yield DTR1(self.address) 
            yield DTR0(self.__lock_byte_address)
            lock_byte = yield ReadMemoryLocation(addr)
            if lock_byte.raw_value is None:
                return False
            return lock_byte.raw_value.as_integer != 0x55
        else:
            return False

    def __repr__(self):
        return f'MemoryBank(address={self.address}, has_lock={bool(self.__lock_byte_address)}, has_latch={bool(self.__latch_byte_address)})'

@total_ordering
class MemoryLocation:

    def __init__(self, bank, address, default=None, reset=None, type_=None):
        self.__bank = bank
        self.__address = address
        self.__type_ = type_
        self.__default = default
        self.__reset = reset
    
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
        return f'MemoryLocation(bank={self.bank.address}, address=0x{self.address:02x}, default={f"0x{self.default:02x}" if self.default is not None else None}, reset={f"0x{self.reset:02x}" if self.reset is not None else None}, type_={self.type_})'

class MemoryRange:

    def __init__(self, bank, start, end, default=None, reset=None, type_=None):
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

    def __init__(self, name, locations):
        self.name = name
        self.locations = locations
        for location in locations:
            location.bank.add_memory_location(location, self)
        
    def _to_value(self, raw):
        """Converts raw bytes to the wanted result."""
        return raw

    def read(self, addr):
        """Generates the DALI commands necessary to read the value. Finally returns the value.
        Raises MemoryLocationNotImplemented exception if device does not respond, e.g. the location is not implemented.
        """
        result = []
        dtr1 = None
        dtr0 = None
        for location in sorted(self.locations):
            # select correct memory location
            if location.bank.address != dtr1:
                dtr1 = location.bank.address
                yield DTR1(location.bank.address)
            if location.address != dtr0:
                dtr0 = location.address
                yield DTR0(location.address)
            # read back value of the memory location
            r = yield ReadMemoryLocation(addr)
            # increase DTR0 to reflect the internal state of the driver
            dtr0 = min(dtr0+1, 255)
            if r.raw_value is None:
                raise MemoryLocationNotImplemented(f'Device at address "{str(addr)}" does not implement {str(location)}.')
            result.append(r.raw_value.as_integer)
        return self._to_value(bytes(result))
    
    def from_list(self, list_):
        """Extracts the value from a list containing all values of the memory bank."""
        raw = []
        for location in sorted(self.locations):
            try:
                r = list_[location.address]
            except IndexError:
                raise MemoryLocationNotImplemented(f'List is missing memory location {str(location)}.')
            if r is None:
                raise MemoryLocationNotImplemented(f'List is missing memory location {str(location)}.')
            raw.append(r)
        return self._to_value(raw)

    def is_addressable(self, addr):
        """Checks whether this value is addressable by querying the value of the last addressable memory location
        for this memory bank through a sequence of DALI queries."""
        last_location = self.locations[-1]
        try:
            last_address = yield from last_location.bank.last_address(addr)
        except MemoryLocationNotImplemented:
            return False
        return last_address > last_location.address
    
    def is_locked(self, addr):
        """Checks whether this value is locked by checking the lock byte of the memory bank."""
        if self.locations[0].type_ == MemoryType.NVM_RW_P:
            locked = yield from self.locations[0].bank.is_locked(addr)
            return locked
        else:
            return False

class NumericValue(MemoryValue):

    """Unit of the numeric value. Set to one if no unit is given."""
    unit = 1

    def __init__(self, name, locations, unit=1):
        super().__init__(name=name, locations=locations)
        self.unit = unit

    def _to_value(self, raw):
        return int.from_bytes(raw, 'big')

class ScaledNumericValue(NumericValue):

    def _to_value(self, raw):
        return int.from_bytes(raw[1:], 'big') * 10.**raw[0]

class FixedScaleNumericValue(NumericValue):

    """Fixed scaling factor."""
    scaling_factor = 1

    def __init__(self, name, locations, unit=1, scaling_factor=1):
        super().__init__(name=name, locations=locations, unit=unit)
        self.scaling_factor = scaling_factor

    def _to_value(self, raw):
        return self.scaling_factor * int.from_bytes(raw, 'big')

class StringValue(MemoryValue):

    def _to_value(self, raw):
        result = ''
        for value in raw:
            if value == 0:
                break # string is Null terminated
            else:
                result += chr(value)
        return result

class BinaryValue(MemoryValue):

    def _to_value(self, raw):
        if raw == 1:
            return True
        else:
            return False

class TemperatureValue(NumericValue):

    def __init__(self, name, locations, unit='°C'):
        super().__init__(name=name, locations=locations, unit=unit)

    def _to_value(self, raw):
        return int.from_bytes(raw, 'big') - 60

class ManufacturerSpecificValue(MemoryValue):

    pass
