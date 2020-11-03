from .location import MemoryLocation, MemoryType, MemoryValue, NumericValue, StringValue, ScaledNumericValue, LockableValueMixin

"""The mememory bank definitions from
DiiA Specification, DALI Part 252 - Energy Reporting, Version 1.1, October 2019"""

class ActiveEnergy(ScaledNumericValue, LockableValueMixin):
    """Active Energy in Wh"""

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
    """Active Power in W"""

    unit = 'W'

    locations = (
        MemoryLocation(bank=202, address=0x0c, default=None, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=202, address=0x0d, default=None, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=202, address=0x0e, default=None, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=202, address=0x0f, default=None, reset=None, type_=MemoryType.RAM_RO)
    )

    scale_location = MemoryLocation(bank=202, address=0x0b, default=None, reset=None, type_=MemoryType.ROM)

class ApparentEnergy(ScaledNumericValue, LockableValueMixin):
    """Apparent Energy in VAh"""

    unit = 'VAh'

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
    """Apparent Power in VA"""

    unit = 'VA'

    locations = (
        MemoryLocation(bank=203, address=0x0c, default=None, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=203, address=0x0d, default=None, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=203, address=0x0e, default=None, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=203, address=0x0f, default=None, reset=None, type_=MemoryType.RAM_RO)
    )

    scale_location = MemoryLocation(bank=203, address=0x0b, default=None, reset=None, type_=MemoryType.ROM)

class ActiveEnergyLoadside(ScaledNumericValue, LockableValueMixin):
    """Loadside Active Energy in Wh"""

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
    """Loadside Active Power in W"""

    unit = 'W'

    locations = (
        MemoryLocation(bank=204, address=0x0c, default=None, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=204, address=0x0d, default=None, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=204, address=0x0e, default=None, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=204, address=0x0f, default=None, reset=None, type_=MemoryType.RAM_RO)
    )

    scale_location = MemoryLocation(bank=204, address=0x0b, default=None, reset=None, type_=MemoryType.ROM)
