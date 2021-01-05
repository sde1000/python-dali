from .location import MemoryLocation, MemoryRange, MemoryType, ScaledNumericValue, LockableValueMixin

"""The mememory bank definitions from
DiiA Specification, DALI Part 252 - Energy Reporting, Version 1.1, October 2019"""

class ActiveEnergy(ScaledNumericValue, LockableValueMixin):
    """Active Energy in Wh"""

    unit = 'Wh'

    locations = (MemoryLocation(bank=202, address=0x04, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=202, start=0x05, end=0x0a, default=0x00, type_=MemoryType.NVM_RO).locations
    
class ActivePower(ScaledNumericValue, LockableValueMixin):
    """Active Power in W"""

    unit = 'W'

    locations = (MemoryLocation(bank=202, address=0x0b, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=202, start=0x0c, end=0x0f, type_=MemoryType.RAM_RO).locations

class ApparentEnergy(ScaledNumericValue, LockableValueMixin):
    """Apparent Energy in VAh"""

    unit = 'VAh'

    locations = (MemoryLocation(bank=203, address=0x04, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=203, start=0x05, end=0x0a, default=0x00, type_=MemoryType.NVM_RO).locations
    
class ApparentPower(ScaledNumericValue, LockableValueMixin):
    """Apparent Power in VA"""

    unit = 'VA'

    locations = (MemoryLocation(bank=203, address=0x0b, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=203, start=0x0c, end=0x0f, type_=MemoryType.RAM_RO).locations

class ActiveEnergyLoadside(ScaledNumericValue, LockableValueMixin):
    """Loadside Active Energy in Wh"""

    unit = 'Wh'

    locations = (MemoryLocation(bank=204, address=0x04, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=204, start=0x05, end=0x0a, default=0x00, type_=MemoryType.NVM_RO).locations
    
class ActivePowerLoadside(ScaledNumericValue, LockableValueMixin):
    """Loadside Active Power in W"""

    unit = 'W'

    locations = (MemoryLocation(bank=204, address=0x0b, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=204, start=0x0c, end=0x0f, type_=MemoryType.RAM_RO).locations
