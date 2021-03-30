from .location import MemoryBank, MemoryLocation, MemoryRange, MemoryType, ScaledNumericValue

"""The mememory bank definitions from
DiiA Specification, DALI Part 252 - Energy Reporting, Version 1.1, October 2019"""
BANK_202 = MemoryBank(202, 0x0F, has_latch=True)
BANK_203 = MemoryBank(203, 0x0F, has_latch=True)
BANK_204 = MemoryBank(204, 0x0F, has_latch=True)

"""Active Energy in Wh"""
ActiveEnergy = ScaledNumericValue(
    "ActiveEnergy",
    unit='Wh',
    locations=(MemoryLocation(bank=BANK_202, address=0x04, type_=MemoryType.ROM),) + \
               MemoryRange(bank=BANK_202, start=0x05, end=0x0a, default=0x00, type_=MemoryType.NVM_RO).locations
)
    
"""Active Power in W"""
ActivePower = ScaledNumericValue(
    "ActivePower",
    unit='W',
    locations=(MemoryLocation(bank=BANK_202, address=0x0b, type_=MemoryType.ROM),) + \
               MemoryRange(bank=BANK_202, start=0x0c, end=0x0f, type_=MemoryType.RAM_RO).locations
)

"""Apparent Energy in VAh"""
ApparentEnergy = ScaledNumericValue(
    "ApparentEnergy",
    unit='VAh',
    locations=(MemoryLocation(bank=BANK_203, address=0x04, type_=MemoryType.ROM),) + \
               MemoryRange(bank=BANK_203, start=0x05, end=0x0a, default=0x00, type_=MemoryType.NVM_RO).locations
)
    
"""Apparent Power in VA"""
ApparentPower = ScaledNumericValue(
    "ApparentPower",
    unit='VA',
    locations=(MemoryLocation(bank=BANK_203, address=0x0b, type_=MemoryType.ROM),) + \
               MemoryRange(bank=BANK_203, start=0x0c, end=0x0f, type_=MemoryType.RAM_RO).locations
)

"""Loadside Active Energy in Wh"""
ActiveEnergyLoadside = ScaledNumericValue(
    "ActiveEnergyLoadside",
    unit='Wh',
    locations=(MemoryLocation(bank=BANK_204, address=0x04, type_=MemoryType.ROM),) + \
               MemoryRange(bank=BANK_204, start=0x05, end=0x0a, default=0x00, type_=MemoryType.NVM_RO).locations
)
    
"""Loadside Active Power in W"""
ActivePowerLoadside = ScaledNumericValue(
    "ActivePowerLoadside",
    unit='W',
    locations=(MemoryLocation(bank=BANK_204, address=0x0b, type_=MemoryType.ROM),) + \
               MemoryRange(bank=BANK_204, start=0x0c, end=0x0f, type_=MemoryType.RAM_RO).locations
)
