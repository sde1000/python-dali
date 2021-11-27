from .location import MemoryBank, MemoryLocation, MemoryRange, MemoryType, \
    MemoryValue, NumericValue, StringValue

# Memory bank definitions from IEC 62386-102 section 9.10.7 and DiiA
# Specification, DALI Part 251 - Memory Bank 1 Extension, Version 1.1,
# October 2019
#
# This bank shall be programmed by the OEM when the bus unit is
# integrated into a luminaire
BANK_1 = MemoryBank(1, 0x77, has_lock=True)


class ManufacturerGTIN(NumericValue):
    """Luminaire manufacturer GTIN

    Defined in IEC 62386-102 section 9.10.7
    """
    bank = BANK_1
    locations = MemoryRange(start=0x03, end=0x08, default=0xff,
                            type_=MemoryType.NVM_RW_L)


class LuminaireID(NumericValue):
    """Luminaire identification number

    Defined in IEC 62386-102 section 9.10.7
    """
    bank = BANK_1
    locations = MemoryRange(start=0x09, end=0x10, default=0xff,
                            type_=MemoryType.NVM_RW_L)


class ContentFormatID(NumericValue):
    """Content Format ID

    Set to 0x0003 to indicate DiiA Specification DALI Part 251 -
    Memory Bank 1 Extension, Version 1.1, October 2019
    """
    # XXX why is this not a MemoryRange? Is it just so the default can
    # be set?
    bank = BANK_1
    locations = (
        MemoryLocation(address=0x11, default=0x00, type_=MemoryType.NVM_RW_L),
        MemoryLocation(address=0x12, default=0x03, type_=MemoryType.NVM_RW_L),
    )


class YearOfManufacture(NumericValue):
    """Luminaire year of manufacture (YY)

    Valid when in the range 0..99; 100..255 indicates "unknown"
    """
    bank = BANK_1
    locations = MemoryLocation(address=0x13, default=0xff,
                               type_=MemoryType.NVM_RW_L)
    mask_supported = True
    max_value = 99


class WeekOfManufacture(NumericValue):
    """Luminaire week of manufacture (WW)

    Valid when in the range 1..53; 0 or 54..255 indicates "unknown"
    """
    bank = BANK_1
    locations = MemoryLocation(address=0x14, default=0xff,
                               type_=MemoryType.NVM_RW_L)
    mask_supported = True
    min_value = 1
    max_value = 53


class InputPowerNominal(NumericValue):
    """Nominal Input Power in W

    Valid when in the range 0..65534; 65535 indicates "unknown"
    """
    bank = BANK_1
    unit = 'W'
    locations = MemoryRange(start=0x15, end=0x16, default=0xff,
                            type_=MemoryType.NVM_RW_L)
    mask_supported = True


class InputPowerMinimumDim(NumericValue):
    """Power at minimum dim level in W

    Valid when in the range 0..65534; 65535 indicates "unknown"
    """
    bank = BANK_1
    unit = 'W'
    locations = MemoryRange(start=0x17, end=0x18, default=0xff,
                            type_=MemoryType.NVM_RW_L)
    mask_supported = True


class MainsVoltageMinimum(NumericValue):
    """Nominal Minimum AC mains voltage in V

    Valid when in the range 90..480; 0..89 or 481..65535 indicates "unknown"
    """
    bank = BANK_1
    unit = 'V'
    locations = MemoryRange(start=0x19, end=0x1a, default=0xff,
                            type_=MemoryType.NVM_RW_L)
    min_value = 90
    max_value = 480
    mask_supported = True


class MainsVoltageMaximum(NumericValue):
    """Nominal Maximum AC mains voltage in V

    Valid when in the range 90..480; 0..89 or 481..65535 indicates "unknown"
    """
    bank = BANK_1
    unit = 'V'
    locations = MemoryRange(start=0x1b, end=0x1c, default=0xff,
                            type_=MemoryType.NVM_RW_L)
    min_value = 90
    max_value = 480
    mask_supported = True


class LightOutputNominal(NumericValue):
    """Nominal light output in Lm

    0xffffff indicates "unknown"
    """
    bank = BANK_1
    unit = 'Lm'
    locations = MemoryRange(start=0x1d, end=0x1f, default=0xff,
                            type_=MemoryType.NVM_RW_L)
    mask_supported = True


class CRI(NumericValue):
    """CRI

    Valid when in the range 0..100; 101..255 indicates "unknown"
    """
    bank = BANK_1
    locations = MemoryLocation(address=0x20, default=0xff,
                               type_=MemoryType.NVM_RW_L)
    max_value = 100
    mask_supported = True


class CCT(NumericValue):
    """CCT in K

    Valid when in the range 0..17000

    May return "Part 209 implemented" for raw value 0xfffe
    """
    bank = BANK_1
    unit = 'K'
    locations = MemoryRange(start=0x21, end=0x22, default=0xff,
                            type_=MemoryType.NVM_RW_L)
    mask_supported = True
    max_value = 17000

    @classmethod
    def raw_to_value(cls, raw):
        if raw == bytes([0xff, 0xfe]):
            return "Part 209 implemented"
        return super().raw_to_value(raw)

    @classmethod
    def is_valid(cls, raw):
        if raw == bytes([0xff, 0xfe]):
            return True
        return super().is_valid(raw)


class LightDistributionType(MemoryValue):
    """Light Distribution Type

    0 = not specified
    1 = Type I
    2 = Type II
    3 = Type III
    4 = Type IV;
    5 = Type V;
    6–254 = reserved for additional types
    """
    bank = BANK_1
    locations = MemoryLocation(address=0x23, default=0xff,
                               type_=MemoryType.NVM_RW_L)
    mask_supported = True

    @classmethod
    def raw_to_value(cls, r):
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


class LuminaireColor(StringValue):
    """Luminaire color

    Up to 24 ascii character string
    """
    bank = BANK_1
    locations = MemoryRange(start=0x24, end=0x3b, default=0x00,
                            type_=MemoryType.NVM_RW_L)


class LuminaireIdentification(StringValue):
    """Luminaire identification

    Up to 60 ascii character string
    """
    bank = BANK_1
    locations = MemoryRange(start=0x3c, end=0x77, default=0x00,
                            type_=MemoryType.NVM_RW_L)
