from .location import MemoryLocation, MemoryType, MemoryValue, NumericValue, StringValue, LockableValueMixin

class ManufacturerGTIN(MemoryValue, LockableValueMixin):

    locations = (
        MemoryLocation(bank=1, address=0x03, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x04, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x05, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x06, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x07, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x08, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class LuminaireID(MemoryValue, LockableValueMixin):

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

    locations = (
        MemoryLocation(bank=1, address=0x11, default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x12, default=0x03, reset=None, type_=MemoryType.NVM_RW_P),
    )

class YearOfManufacture(NumericValue, LockableValueMixin):

    locations = (MemoryLocation(bank=1, address=0x13, default=0xff, reset=None, type_=MemoryType.NVM_RW_P))

class WeekOfManufacture(NumericValue, LockableValueMixin):

    locations = (MemoryLocation(bank=1, address=0x14, default=0xff, reset=None, type_=MemoryType.NVM_RW_P))

class InputPowerNominal(NumericValue, LockableValueMixin):

    unit = 'W'

    locations = (
        MemoryLocation(bank=1, address=0x15, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x16, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class InputPowerMinimumDim(NumericValue, LockableValueMixin):

    unit = 'W'

    locations = (
        MemoryLocation(bank=1, address=0x17, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x18, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class MainsVoltageMinimum(NumericValue, LockableValueMixin):

    unit = 'V'

    locations = (
        MemoryLocation(bank=1, address=0x19, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x1a, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class MainsVoltageMaximum(NumericValue, LockableValueMixin):

    unit = 'V'

    locations = (
        MemoryLocation(bank=1, address=0x1b, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x1c, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class LightOutputNominal(NumericValue, LockableValueMixin):

    unit = 'Lm'

    locations = (
        MemoryLocation(bank=1, address=0x1d, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x1e, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x1f, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class CRI(NumericValue, LockableValueMixin):

    locations = (BANK_1.locations[0x20])

class CCT(NumericValue, LockableValueMixin):

    unit = 'K'

    locations = (
        MemoryLocation(bank=1, address=0x21, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
        MemoryLocation(bank=1, address=0x22, default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    )

class LightDistributionType(MemoryValue, LockableValueMixin):

    locations = (MemoryLocation(bank=1, address=0x23, default=0xff, reset=None, type_=MemoryType.NVM_RW_P))

    @classmethod
    def retrieve(cls, sync_driver, dali_address):
        light_distribution_type = super().retrieve(sync_driver, dali_address)[0]
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
