from .location import MemoryBank, MemoryLocation, MemoryRange, MemoryType, MemoryValue, NumericValue, StringValue, LockableValueMixin, ManufacturerSpecificValue

"""The mememory bank definitions from
DiiA Specification, DALI Part 251 - Memory Bank 1 Extension, Version 1.1, October 2019"""
BANK_1 = MemoryBank(1)

class ManufacturerGTIN(MemoryValue, LockableValueMixin):
    """Luminaire manufacturer GTIN with manufacturer specific prefix to derive manufacturer name"""

    locations = MemoryRange(bank=BANK_1, start=0x03, end=0x08, default=0xff, type_=MemoryType.NVM_RW_P).locations

class LuminaireID(MemoryValue, LockableValueMixin):
    """Luminaire identification number"""

    locations = MemoryRange(bank=BANK_1, start=0x09, end=0x10, default=0xff, type_=MemoryType.NVM_RW_P).locations

class ContentFormatID(NumericValue, LockableValueMixin):
    """Content Format ID
    Must be set to 0x0003 when this format is used."""

    locations = (
        MemoryLocation(bank=BANK_1, address=0x11, default=0x00, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=BANK_1, address=0x12, default=0x03, type_=MemoryType.NVM_RW_P),
    )

class YearOfManufacture(NumericValue, LockableValueMixin):
    """Luminaire year of manufacture (YY)"""

    locations = (MemoryLocation(bank=BANK_1, address=0x13, default=0xff, type_=MemoryType.NVM_RW_P),)

class WeekOfManufacture(NumericValue, LockableValueMixin):
    """Luminaire week of manufacture (WW)"""

    locations = (MemoryLocation(bank=BANK_1, address=0x14, default=0xff, type_=MemoryType.NVM_RW_P),)

class InputPowerNominal(NumericValue, LockableValueMixin):
    """Nominal Input Power in W"""

    unit = 'W'

    locations = MemoryRange(bank=BANK_1, start=0x15, end=0x16, default=0xff, type_=MemoryType.NVM_RW_P).locations

class InputPowerMinimumDim(NumericValue, LockableValueMixin):
    """Power at minimum dim level in W"""

    unit = 'W'

    locations = MemoryRange(bank=BANK_1, start=0x17, end=0x18, default=0xff, type_=MemoryType.NVM_RW_P).locations

class MainsVoltageMinimum(NumericValue, LockableValueMixin):
    """Nominal Minimum AC mains voltage in V"""

    unit = 'V'

    locations = MemoryRange(bank=BANK_1, start=0x19, end=0x1a, default=0xff, type_=MemoryType.NVM_RW_P).locations

class MainsVoltageMaximum(NumericValue, LockableValueMixin):
    """Nominal Maximum AC mains voltage in V"""

    unit = 'V'

    locations = MemoryRange(bank=BANK_1, start=0x1b, end=0x1c, default=0xff, type_=MemoryType.NVM_RW_P).locations

class LightOutputNominal(NumericValue, LockableValueMixin):
    """Nominal light output in Lm"""

    unit = 'Lm'

    locations = MemoryRange(bank=BANK_1, start=0x1d, end=0x1f, default=0xff, type_=MemoryType.NVM_RW_P).locations

class CRI(NumericValue, LockableValueMixin):
    """CRI"""

    locations = (MemoryLocation(bank=BANK_1, address=0x20, default=0xff, type_=MemoryType.NVM_RW_P),)

class CCT(NumericValue, LockableValueMixin):
    """CCT in K"""

    unit = 'K'

    locations = MemoryRange(bank=BANK_1, start=0x21, end=0x22, default=0xff, type_=MemoryType.NVM_RW_P).locations

class LightDistributionType(MemoryValue, LockableValueMixin):
    """Light Distribution Type
    0 = not specified
    1 = Type I
    2 = Type II
    3 = Type III
    4 = Type IV;
    5 = Type V;
    6-254 = reserved for additional types"""

    locations = (MemoryLocation(bank=BANK_1, address=0x23, default=0xff, type_=MemoryType.NVM_RW_P),)

    @classmethod
    def retrieve(cls, addr):
        r = yield from super().retrieve(addr)
        light_distribution_type = r[0]
        if light_distribution_type == 0:
            return 'not specified'
        elif light_distribution_type == 1:
            return 'Type I'
        elif light_distribution_type == 2:
            return 'Type II'
        elif light_distribution_type == 3:
            return 'Type III'
        elif light_distribution_type == 4:
            return 'Type IV'
        elif light_distribution_type == 5:
            return 'Type V'
        else:
            return 'reserved'

class LuminaireColor(StringValue, LockableValueMixin):
    """Luminaire color [24 ascii character string, first char at 0x24]
    Null terminated if shorter than defined length."""

    locations = MemoryRange(bank=BANK_1, start=0x24, end=0x3b, default=0x00, type_=MemoryType.NVM_RW_P).locations

class LuminaireIdentification(StringValue, LockableValueMixin):
    """Luminaire identification [60 ascii character string, first char at 0x3C]
    Null terminated if shorter than defined length."""

    locations = MemoryRange(bank=BANK_1, start=0x3c, end=0x77, default=0x00, type_=MemoryType.NVM_RW_P).locations

class ManufacturerSpecific(ManufacturerSpecificValue):
    """Manufacturer-specific"""

    locations = MemoryRange(bank=BANK_1, start=0x78, end=0xfe).locations
