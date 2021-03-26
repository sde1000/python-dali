from .location import MemoryBank, MemoryLocation, MemoryRange, MemoryType, ScaledNumericValue

"""The mememory bank definitions from
DiiA Specification, DALI Part 252 - Energy Reporting, Version 1.1, October 2019"""
BANK_202 = MemoryBank(202, has_latch=True)
BANK_203 = MemoryBank(203, has_latch=True)
BANK_204 = MemoryBank(204, has_latch=True)

class ActiveEnergy(ScaledNumericValue):
    """Active Energy in Wh"""

    unit = 'Wh'

    locations = (MemoryLocation(bank=BANK_202, address=0x04, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=BANK_202, start=0x05, end=0x0a, default=0x00, type_=MemoryType.NVM_RO).locations
    
class ActivePower(ScaledNumericValue):
    """Active Power in W"""

    unit = 'W'

    locations = (MemoryLocation(bank=BANK_202, address=0x0b, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=BANK_202, start=0x0c, end=0x0f, type_=MemoryType.RAM_RO).locations

class ApparentEnergy(ScaledNumericValue):
    """Apparent Energy in VAh"""

    unit = 'VAh'

    locations = (MemoryLocation(bank=BANK_203, address=0x04, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=BANK_203, start=0x05, end=0x0a, default=0x00, type_=MemoryType.NVM_RO).locations
    
class ApparentPower(ScaledNumericValue):
    """Apparent Power in VA"""

    unit = 'VA'

    locations = (MemoryLocation(bank=BANK_203, address=0x0b, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=BANK_203, start=0x0c, end=0x0f, type_=MemoryType.RAM_RO).locations

class ActiveEnergyLoadside(ScaledNumericValue):
    """Loadside Active Energy in Wh"""

    unit = 'Wh'

    locations = (MemoryLocation(bank=BANK_204, address=0x04, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=BANK_204, start=0x05, end=0x0a, default=0x00, type_=MemoryType.NVM_RO).locations
    
class ActivePowerLoadside(ScaledNumericValue):
    """Loadside Active Power in W"""

    unit = 'W'

    locations = (MemoryLocation(bank=BANK_204, address=0x0b, type_=MemoryType.ROM),) + \
                 MemoryRange(bank=BANK_204, start=0x0c, end=0x0f, type_=MemoryType.RAM_RO).locations
