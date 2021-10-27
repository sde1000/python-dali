from .location import MemoryBank, MemoryLocation, MemoryRange, MemoryType, \
    NumericValue, VersionNumberValue

# Memory bank definition from IEC 62386 part 102:2014 section 9.10.6
#
# Memory bank 0 contains information about the bus unit and must be
# implemented in all bus units
#
# The layout of memory bank 0 is the same in control gear and control
# devices up to and including location 0x19. In bus units that
# implement both control gear and control devices, the data shall be
# the same as well.
#
# The layout of memory bank 0 changed between the 2009 and 2014
# versions of the standard. In the 2009 version, the serial
# (identification) number ends at location 0x0e and further locations
# are "defined by the control gear manufacturer". A unit is using the
# 2009 version if QueryVersionNumber() returns 1.
BANK_0 = MemoryBank(0, 0x7f, has_lock=False)

BANK_0_legacy = MemoryBank(0, 0x0e, has_lock=False)


class LastMemoryBank(NumericValue):
    """Number of last accessible memory bank
    """
    bank = BANK_0
    locations = MemoryLocation(address=0x02, type_=MemoryType.ROM)


class LastMemoryBank_legacy(NumericValue):
    """Number of last accessible memory bank
    """
    bank = BANK_0_legacy
    locations = MemoryLocation(address=0x02, type_=MemoryType.ROM)


class GTIN(NumericValue):
    """Bus unit GTIN
    """
    bank = BANK_0
    locations = MemoryRange(start=0x03, end=0x08, type_=MemoryType.ROM)


class GTIN_legacy(NumericValue):
    """Bus unit GTIN
    """
    bank = BANK_0_legacy
    locations = MemoryRange(start=0x03, end=0x08, type_=MemoryType.ROM)


class FirmwareVersion(VersionNumberValue):
    """Bus unit firmware version
    """
    bank = BANK_0
    locations = MemoryRange(start=0x09, end=0x0a, type_=MemoryType.ROM)


class FirmwareVersion_legacy(VersionNumberValue):
    """Bus unit firmware version
    """
    bank = BANK_0_legacy
    locations = MemoryRange(start=0x09, end=0x0a, type_=MemoryType.ROM)


# The identification number may be truncated at location 0x0e in units
# implemented according to IEC 62386-102:2009.
class IdentificationNumber(NumericValue):
    """Bus unit serial number

    The combination of GTIN and IdentificationNumber shall be globally
    unique
    """
    bank = BANK_0
    locations = MemoryRange(start=0x0b, end=0x12, type_=MemoryType.ROM)


class IdentifictionNumber_legacy(NumericValue):
    """Bus unit serial number

    The combination of GTIN and IdentificationNumber shall be globally
    unique
    """
    bank = BANK_0_legacy
    locations = MemoryRange(start=0x0b, end=0x0e, type_=MemoryType.ROM)


class HardwareVersion(VersionNumberValue):
    """The hardware version of the bus unit
    """
    bank = BANK_0
    locations = MemoryRange(start=0x13, end=0x14, type_=MemoryType.ROM)


class Part101Version(VersionNumberValue):
    """The implemented IEC 62386-101 version number of the bus unit
    """
    bank = BANK_0
    locations = MemoryLocation(address=0x15, type_=MemoryType.ROM)


class Part102Version(VersionNumberValue):
    """The implemented IEC 62386-102 version number of the bus unit

    If no control gear is implemented, the version number is encoded
    as 0xff which is returned as string value "not implemented"
    """
    bank = BANK_0
    locations = MemoryLocation(address=0x16, type_=MemoryType.ROM)


class Part103Version(VersionNumberValue):
    """The implemented IEC 62386-102 version number of the bus unit

    If no control device is implemented, the version number is encoded
    as 0xff which is returned as string value "not implemented"
    """
    bank = BANK_0
    locations = MemoryLocation(address=0x17, type_=MemoryType.ROM)


class DeviceUnitCount(NumericValue):
    """The number of logical control device units integrated into the bus unit

    The number of logical units shall be in the range 0..64 if this
    memory bank is being implemented by control gear, or 1..64 if this
    memory bank is being implemented by a control device.
    """
    bank = BANK_0
    locations = MemoryLocation(address=0x18, type_=MemoryType.ROM)
    max_value = 64


class GearUnitCount(NumericValue):
    """The number of logical control gear units integrated into the bus unit

    The number of logical units shall be in the range 1..64 if this
    memory bank is being implemented by control gear, or 0..64 if this
    memory bank is being implemented by a control device.
    """
    bank = BANK_0
    locations = MemoryLocation(address=0x19, type_=MemoryType.ROM)
    max_value = 64


class UnitIndex(NumericValue):
    """The unique index number of the logical unit

    When accessed using 16-bit commands, this is the index number of
    the logical control gear unit. When accessed using 24-bit
    commands, this is the index number of the logical control device
    unit. It is in the range 0 to the device or gear unit count minus
    one.
    """
    bank = BANK_0
    locations = MemoryLocation(address=0x1a, type_=MemoryType.ROM)
