from .location import MemoryLocation, MemoryType, MemoryValue, NumericValue, StringValue, ScaledNumericValue, LockableValueMixin

class ActiveEnergy(ScaledNumericValue, LockableValueMixin):

    unit = 'Wh'

    locations = (
        MemoryLocation(bank=202, address=0x05, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=202, address=0x06, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=202, address=0x07, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=202, address=0x08, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=202, address=0x09, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=202, address=0x0a, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

    scale_location = MemoryLocation(bank=202, address=0x04, default=None, reset=None, type_=MemoryType.ROM)
    
class ActivePower(ScaledNumericValue, LockableValueMixin):

    unit = 'W'

    locations = (
        MemoryLocation(bank=202, address=0x0c, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=202, address=0x0d, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=202, address=0x0e, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=202, address=0x0f, default=0x0d, reset=None, type_=MemoryType.RAM_RO)
    )

    scale_location = MemoryLocation(bank=202, address=0x0b, default=None, reset=None, type_=MemoryType.ROM)

class ApparentEnergy(ScaledNumericValue, LockableValueMixin):

    unit = 'Wh'

    locations = (
        MemoryLocation(bank=203, address=0x05, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=203, address=0x06, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=203, address=0x07, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=203, address=0x08, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=203, address=0x09, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=203, address=0x0a, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

    scale_location = MemoryLocation(bank=203, address=0x04, default=None, reset=None, type_=MemoryType.ROM)
    
class ApparentPower(ScaledNumericValue, LockableValueMixin):

    unit = 'W'

    locations = (
        MemoryLocation(bank=203, address=0x0c, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=203, address=0x0d, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=203, address=0x0e, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=203, address=0x0f, default=0x0d, reset=None, type_=MemoryType.RAM_RO)
    )

    scale_location = MemoryLocation(bank=203, address=0x0b, default=None, reset=None, type_=MemoryType.ROM)

class ActiveEnergyLoadside(ScaledNumericValue, LockableValueMixin):

    unit = 'Wh'

    locations = (
        MemoryLocation(bank=204, address=0x05, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=204, address=0x06, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=204, address=0x07, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=204, address=0x08, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=204, address=0x09, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=204, address=0x0a, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

    scale_location = MemoryLocation(bank=204, address=0x04, default=None, reset=None, type_=MemoryType.ROM)
    
class ActivePowerLoadside(ScaledNumericValue, LockableValueMixin):

    unit = 'W'

    locations = (
        MemoryLocation(bank=204, address=0x0c, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=204, address=0x0d, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=204, address=0x0e, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=204, address=0x0f, default=0x0d, reset=None, type_=MemoryType.RAM_RO)
    )

    scale_location = MemoryLocation(bank=204, address=0x0b, default=None, reset=None, type_=MemoryType.ROM)

if __name__ == '__main__':
    from dali.driver.quaddali import SyncQuadDALIUSBDriver
    from dali.address import Short

    iface = SyncQuadDALIUSBDriver(port='/dev/ttyS24')

    print('"',
        ActiveEnergy.retrieve(iface, Short(0))
    ,'"')
    print('"',
        ActivePower.retrieve(iface, Short(0))
    ,'"')
    print()
    print('"',
        ApparentEnergy.retrieve(iface, Short(0))
    ,'"')
    print('"',
        ApparentPower.retrieve(iface, Short(0))
    ,'"')
    print()
    print('"',
        ActiveEnergyLoadside.retrieve(iface, Short(0))
    ,'"')
    print('"',
        ActivePowerLoadside.retrieve(iface, Short(0))
    ,'"')

    iface.backend.close()