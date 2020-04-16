from enum import Enum, auto
from collections import namedtuple

from dali.gear.general import ReadMemoryLocation, DTR0, DTR1

MemoryBank = namedtuple('MemoryBank', [
    'bank',      # Memory bank as integer.
    'mandatory', # Is this bank mandatory or optional?
    'locations'  # Tuple of MemoryLocations. Index equals address.
])

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
    'description', # Description of the location as noted in the IEC 62386 standard or its extensions.
    'default',     # Default value of the memory location. None if undefined or manufacturer specific. -1 if answers NO.
    'reset',       # Reset value of the memory location. None for no change.
    'type_'        # Memory type.
], defaults=['', None, None])

class MemoryValue:

    """Memory locations that belong to this value. Sorted from MSB to LSB."""
    locations = ()

    @classmethod
    def retrieve(cls, driver, dali_address):
        result = []
        for location in cls.locations:
            driver.send(DTR1(location.bank))
            driver.send(DTR0(location.address))
            result.append(driver.send(ReadMemoryLocation(dali_address)).value.as_integer)
        return bytes(result)

class NumericValue(MemoryValue):

    """Unit of the numeric value. Set to one if no unit is given."""
    unit = 1

    @classmethod
    def retrieve(cls, driver, dali_address):
        result = 0
        raw_values = super().retrieve(driver, dali_address)
        for shift, value in enumerate(raw_values[::-1]):
            result += value << (shift*8)
        return result

class ScaledNumericValue(NumericValue):

    """Memory location where the scale of the value is stored."""
    scale_location = None

    @classmethod
    def retrieve(cls, driver, dali_address):
        result = super().retrieve(driver, dali_address)

        # setup to read back scale value
        driver.send(DTR1(cls.scale_location.bank))
        driver.send(DTR0(cls.scale_location.address))

        # read scale value and convert it from twos-complement to an integer
        scale_raw = driver.send(ReadMemoryLocation(dali_address)).value.as_integer
        scale = int.from_bytes(bytes([scale_raw]), byteorder='big', signed=True)

        return result * 10.**scale

class StringValue(MemoryValue):

    @classmethod
    def retrieve(cls, driver, dali_address):
        result = ''
        raw_values = super().retrieve(driver, dali_address)
        for value in raw_values:
            result += chr(value)
        return result