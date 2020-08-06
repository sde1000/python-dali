from .location import MemoryLocation, MemoryType, MemoryValue, NumericValue, StringValue, LockableValueMixin, ManufacturerSpecificValue

"""The mememory bank definitions from
DiiA Specification, DALI Part 251 - Memory Bank 1 Extension, Version 1.1, October 2019"""

class ManufacturerGTIN(MemoryValue, LockableValueMixin):
    """Luminaire manufacturer GTIN with manufacturer specific prefix to derive manufacturer name"""

    locations = (
        MemoryLocation(bank=1, address=0x03, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x04, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x05, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x06, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x07, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x08, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class LuminaireID(MemoryValue, LockableValueMixin):
    """Luminaire identification number"""

    locations = (
        MemoryLocation(bank=1, address=0x09, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x0a, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x0b, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x0c, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x0d, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x0e, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x0f, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x10, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class ContentFormatID(NumericValue, LockableValueMixin):
    """Content Format ID
    Must be set to 0x0003 when this format is used."""

    locations = (
        MemoryLocation(bank=1, address=0x11, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x12, default=0x03, reset=None, type_=MemoryType.NVM_RW_P),
    )

class YearOfManufacture(NumericValue, LockableValueMixin):
    """Luminaire year of manufacture (YY)"""

    locations = (MemoryLocation(bank=1, address=0x13, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),)

class WeekOfManufacture(NumericValue, LockableValueMixin):
    """Luminaire week of manufacture (WW)"""

    locations = (MemoryLocation(bank=1, address=0x14, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),)

class InputPowerNominal(NumericValue, LockableValueMixin):
    """Nominal Input Power in W"""

    unit = 'W'

    locations = (
        MemoryLocation(bank=1, address=0x15, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x16, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class InputPowerMinimumDim(NumericValue, LockableValueMixin):
    """Power at minimum dim level in W"""

    unit = 'W'

    locations = (
        MemoryLocation(bank=1, address=0x17, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x18, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class MainsVoltageMinimum(NumericValue, LockableValueMixin):
    """Nominal Minimum AC mains voltage in V"""

    unit = 'V'

    locations = (
        MemoryLocation(bank=1, address=0x19, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x1a, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class MainsVoltageMaximum(NumericValue, LockableValueMixin):
    """Nominal Maximum AC mains voltage in V"""

    unit = 'V'

    locations = (
        MemoryLocation(bank=1, address=0x1b, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x1c, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class LightOutputNominal(NumericValue, LockableValueMixin):
    """Nominal light output in Lm"""

    unit = 'Lm'

    locations = (
        MemoryLocation(bank=1, address=0x1d, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x1e, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x1f, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class CRI(NumericValue, LockableValueMixin):
    """CRI"""

    locations = (MemoryLocation(bank=1, address=0x20, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),)

class CCT(NumericValue, LockableValueMixin):
    """CCT in K"""

    unit = 'K'

    locations = (
        MemoryLocation(bank=1, address=0x21, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x22, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class LightDistributionType(MemoryValue, LockableValueMixin):
    """Light Distribution Type
    0 = not specified
    1 = Type I
    2 = Type II
    3 = Type III
    4 = Type IV;
    5 = Type V;
    6-254 = reserved for additional types"""

    locations = (MemoryLocation(bank=1, address=0x23, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),)

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

    locations = (
        MemoryLocation(bank=1, address=0x24, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x25, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x26, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x27, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x28, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x29, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x2a, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x2b, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x2c, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x2d, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x2e, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x2f, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x30, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x31, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x32, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x33, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x34, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x35, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x36, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x37, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x38, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x39, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x3a, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x3b, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    )

class LuminaireIdentification(StringValue, LockableValueMixin):
    """Luminaire identification [60 ascii character string, first char at 0x3C]
    Null terminated if shorter than defined length."""

    locations = (
        MemoryLocation(bank=1, address=0x3c, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x3d, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x3e, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x3f, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x40, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x41, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x42, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x43, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x44, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x45, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x46, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x47, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x48, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x49, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x4a, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x4b, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x4c, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x4d, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x4e, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x4f, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x50, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x51, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x52, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x53, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x54, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x55, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x56, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x57, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x58, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x59, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x5a, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x5b, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x5c, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x5d, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x5e, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x5f, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x60, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x61, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x62, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x63, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x64, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x65, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x66, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x67, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x68, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x69, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x6a, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x6b, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x6c, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x6d, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x6e, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x6f, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x70, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x71, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x72, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x73, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x74, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x75, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x76, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x77, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    )

class ManufacturerSpecific(ManufacturerSpecificValue):
    """Manufacturer-specific"""

    locations = (
        MemoryLocation(bank=1, address=0x78, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x79, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x7a, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x7b, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x7c, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x7d, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x7e, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x7f, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x80, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x81, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x82, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x83, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x84, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x85, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x86, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x87, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x88, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x89, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x8a, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x8b, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x8c, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x8d, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x8e, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x8f, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x90, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x91, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x92, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x93, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x94, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x95, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x96, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x97, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x98, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x99, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x9a, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x9b, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x9c, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x9d, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x9e, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0x9f, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xa0, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xa1, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xa2, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xa3, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xa4, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xa5, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xa6, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xa7, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xa8, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xa9, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xaa, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xab, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xac, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xad, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xae, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xaf, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xb0, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xb1, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xb2, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xb3, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xb4, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xb5, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xb6, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xb7, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xb8, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xb9, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xba, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xbb, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xbc, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xbd, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xbe, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xbf, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xc0, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xc1, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xc2, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xc3, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xc4, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xc5, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xc6, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xc7, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xc8, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xc9, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xca, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xcb, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xcc, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xcd, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xce, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xcf, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xd0, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xd1, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xd2, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xd3, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xd4, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xd5, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xd6, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xd7, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xd8, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xd9, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xda, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xdb, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xdc, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xdd, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xde, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xdf, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xe0, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xe1, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xe2, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xe3, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xe4, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xe5, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xe6, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xe7, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xe8, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xe9, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xea, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xeb, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xec, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xed, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xee, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xef, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xf0, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xf1, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xf2, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xf3, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xf4, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xf5, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xf6, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xf7, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xf8, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xf9, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xfa, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xfb, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xfc, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xfd, default=None, reset=None, type_=None),
        MemoryLocation(bank=1, address=0xfe, default=None, reset=None, type_=None)
    )
