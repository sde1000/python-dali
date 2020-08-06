from enum import Enum, auto
from collections import namedtuple

from dali.gear.general import ReadMemoryLocation, DTR0, DTR1

class MemoryType(Enum):
    ROM = auto()      # ROM
    RAM_RO = auto()   # RAM-RO
    RAM_RW = auto()   # RAM-RW
    NVM_RO = auto()   # NVM-RO
    NVM_RW = auto()   # NVM-RW
    NVM_RW_P = auto() # NVM-RW (protectable)

MemoryLocation = namedtuple('MemoryLocation', [
    'bank',        # Memory bank to which the location belongs (mandatory).
    'address',     # Memory address as integer (mandatory).
    'default',     # Default value of the memory location. None if undefined or manufacturer specific. -1 if answers NO.
    'reset',       # Reset value of the memory location. None for no change.
    'type_'        # Memory type.
], defaults=['', None, None])

class MemoryValue:

    """Memory locations that belong to this value. Sorted from MSB to LSB."""
    locations = ()

    @classmethod
    def retrieve(cls, addr):
        """Retrieves this memory value through a sequence of DALI queries.

        @param addr: address of the DALI device (Address)
        """
        result = []
        for location in cls.locations:
            # select correct memory location
            yield DTR1(location.bank)
            yield DTR0(location.address)
            # read back value of the memory location
            r = yield ReadMemoryLocation(addr)
            result.append(r.raw_value.as_integer)
        return bytes(result)

    @classmethod
    def is_addressable(cls, addr):
        """Checks whether this value is adressable by querying the value of the last addressable memory location
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
        raw_values = yield from super().retrieve(addr)
        for shift, value in enumerate(raw_values[::-1]):
            result += value << (shift*8)
        return result

class ScaledNumericValue(NumericValue):

    """Memory location where the scale of the value is stored."""
    scale_location = None

    @classmethod
    def retrieve(cls, addr):
        result = super().retrieve(addr)

        # setup to read back scale value
        yield DTR1(cls.scale_location.bank)
        yield DTR0(cls.scale_location.address)

        # read scale value and convert it from twos-complement to an integer
        r = yield ReadMemoryLocation(addr)
        scale = int.from_bytes(bytes([r.raw_value.as_integer]), byteorder='big', signed=True)

        return result * 10.**scale

class FixedScaleNumericValue(NumericValue):

    """Fixed scaling factor."""
    scaling_factor = 1

    @classmethod
    def retrieve(cls, addr):
        return cls.scaling_factor * super().retrieve(addr)

class StringValue(MemoryValue):

    @classmethod
    def retrieve(cls, addr):
        result = ''
        raw_values = super().retrieve( addr)
        for value in raw_values:
            if value == 0:
                break # string is Null terminated
            else:
                result += chr(value)
        return result

class BinaryValue(MemoryValue):

    @classmethod
    def retrieve(cls, addr):
        if super().retrieve(addr) == 1:
            return True
        else:
            return False

class TemperatureValue(NumericValue):

    unit = '°C'

    @classmethod
    def retrieve(cls, addr):
        return super().retrieve(addr) - 60

class ManufacturerSpecificValue(MemoryValue):

    pass
