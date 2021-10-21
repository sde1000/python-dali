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

"""Bus unit GTIN
"""
GTIN = NumericValue(
    "GTIN",
    locations=MemoryRange(bank=BANK_0, start=0x03, end=0x08,
                          type_=MemoryType.ROM).locations
)

GTIN_legacy = NumericValue(
    "GTIN_legacy",
    locations=MemoryRange(bank=BANK_0_legacy, start=0x03, end=0x08,
                          type_=MemoryType.ROM).locations
)

FirmwareVersion = VersionNumberValue(
    "FirmwareVersion",
    locations=MemoryRange(bank=BANK_0, start=0x09, end=0x0a,
                          type_=MemoryType.ROM).locations
)

FirmwareVersion_legacy = VersionNumberValue(
    "FirmwareVersion_legacy",
    locations=MemoryRange(bank=BANK_0_legacy, start=0x09, end=0x0a,
                          type_=MemoryType.ROM).locations
)

# The identification number may be truncated at location 0x0e in units
# implemented according to IEC 62386-102:2009.
IdentificationNumber = NumericValue(
    "IdentificationNumber",
    locations=MemoryRange(bank=BANK_0, start=0x0b, end=0x12,
                          type_=MemoryType.ROM).locations
)

IdentifictionNumber_legacy = NumericValue(
    "IdentificationNumber_legacy",
    locations=MemoryRange(bank=BANK_0_legacy, start=0x0b, end=0x0e,
                          type_=MemoryType.ROM).locations
)

HardwareVersion = VersionNumberValue(
    "HardwareVersion",
    locations=MemoryRange(bank=BANK_0, start=0x13, end=0x14,
                          type_=MemoryType.ROM).locations
)

Part101Version = VersionNumberValue(
    "Part101Version",
    locations=(MemoryLocation(bank=BANK_0, address=0x15, type_=MemoryType.ROM),)
)

Part102Version = VersionNumberValue(
    "Part102Version",
    locations=(MemoryLocation(bank=BANK_0, address=0x16, type_=MemoryType.ROM),)
)

Part103Version = VersionNumberValue(
    "Part103Version",
    locations=(MemoryLocation(bank=BANK_0, address=0x17, type_=MemoryType.ROM),)
)

"""The number of logical control device units integrated into the bus unit
"""
DeviceUnitCount = NumericValue(
    "DeviceUnitCount",
    locations=(MemoryLocation(bank=BANK_0, address=0x18, type_=MemoryType.ROM),)
)

"""The number of logical control gear units integrated into the bus unit
"""
GearUnitCount = NumericValue(
    "GearUnitCount",
    locations=(MemoryLocation(bank=BANK_0, address=0x19, type_=MemoryType.ROM),)
)

"""The unique index number of the logical unit

When accessed using 16-bit commands, this is the index number of the
logical control gear unit. When accessed using 24-bit commands, this
is the index number of the logical control device unit. It is in the
range 0 to the device or gear unit count minus one.
"""
UnitIndex = NumericValue(
    "UnitIndex",
    locations=(MemoryLocation(bank=BANK_0, address=0x1a, type_=MemoryType.ROM),)
)
