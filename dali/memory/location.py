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

    """Retrieves this memory value through a DALI query.

    @param driver: instance of SyncDALIDriver
    @param dali_address: address of the DALI device (Address)
    """
    @classmethod
    def retrieve(cls, sync_driver, dali_address):
        result = []
        for location in cls.locations:
            sync_driver.send(DTR1(location.bank))
            sync_driver.send(DTR0(location.address))
            result.append(sync_driver.send(ReadMemoryLocation(dali_address)).value.as_integer)
        return bytes(result)

    """Checks whether this value is adressable by querying the value of the last addressable memory location
    for this memory bank.

    @param driver: instance of SyncDALIDriver
    @param dali_address: address of the DALI device (Address)
    """
    @classmethod
    def is_addressable(cls, sync_driver, dali_address):
        last_location = cls.locations[-1]
        sync_driver.send(DTR1(last_location.bank))
        sync_driver.send(DTR0(0x00))
        last_addressable = sync_driver.send(ReadMemoryLocation(dali_address)).value.as_integer

        return last_addressable > last_location.address


class LockableValueMixin:

    """Check whether this value is locked. Returns True is value is locked or read-only. Returns false for values
    that can not be locked.

    @param driver: instance of SyncDALIDriver
    @param dali_address: address of the DALI device (Address)
    """
    @classmethod
    def is_locked(cls, sync_driver, dali_address):
        memory_type = cls.locations[0].type_
        if memory_type == MemoryType.NVM_RW_P:
            sync_driver.send(DTR1(cls.locations[0].bank))
            sync_driver.send(DTR0(0x02))
            lock_byte = cls.retrieve(sync_driver, dali_address)[0]
            return lock_byte != 0x55
        else:
            raise ValueError('MemoryType does not support locking')

class NumericValue(MemoryValue):

    """Unit of the numeric value. Set to one if no unit is given."""
    unit = 1

    @classmethod
    def retrieve(cls, sync_driver, dali_address):
        result = 0
        raw_values = super().retrieve(sync_driver, dali_address)
        for shift, value in enumerate(raw_values[::-1]):
            result += value << (shift*8)
        return result

class ScaledNumericValue(NumericValue):

    """Memory location where the scale of the value is stored."""
    scale_location = None

    @classmethod
    def retrieve(cls, sync_driver, dali_address):
        result = super().retrieve(sync_driver, dali_address)

        # setup to read back scale value
        sync_driver.send(DTR1(cls.scale_location.bank))
        sync_driver.send(DTR0(cls.scale_location.address))

        # read scale value and convert it from twos-complement to an integer
        scale_raw = sync_driver.send(ReadMemoryLocation(dali_address)).value.as_integer
        scale = int.from_bytes(bytes([scale_raw]), byteorder='big', signed=True)

        return result * 10.**scale

class FixedScaleNumericValue(NumericValue):

    """Fixed scaling factor."""
    scaling_factor = 1

    @classmethod
    def retrieve(cls, sync_driver, dali_address):
        return cls.scaling_factor * super().retrieve(sync_driver, dali_address)

class StringValue(MemoryValue):

    @classmethod
    def retrieve(cls, sync_driver, dali_address):
        result = ''
        raw_values = super().retrieve(sync_driver, dali_address)
        for value in raw_values:
            if value == 0:
                break # string is Null terminated
            else:
                result += chr(value)
        return result

class BinaryValue(MemoryValue):

    @classmethod
    def retrieve(cls, sync_driver, dali_address):
        if super().retrieve(sync_driver, dali_address) == 1:
            return True
        else:
            return False

class TemperatureValue(NumericValue):

    unit = '°C'

    @classmethod
    def retrieve(cls, sync_driver, dali_address):
        return super().retrieve(sync_driver, dali_address) - 60

class ManufacturerSpecificValue(MemoryValue):

    pass