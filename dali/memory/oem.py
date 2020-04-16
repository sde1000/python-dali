from .location import MemoryBank, MemoryLocation, MemoryType, MemoryValue, NumericValue, StringValue

BANK_1 = MemoryBank(bank=1, mandatory=True, locations=(
    MemoryLocation(bank=1, address=0x00, description='Address of last addressable memory location; Range [0x77,0xFE]', default=None, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=1, address=0x01, description='Indicator byte', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x02, description='Lock byte Lockable bytes in the memory bank shall be read-only while the lock byte has a value different from 0x55.', default=0xff, reset=0xff, type_=MemoryType.RAM_RW),
    MemoryLocation(bank=1, address=0x03, description='Luminaire manufacturer GTIN with manufacturer specific prefix to derive manufacturer name', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x04, description='Luminaire manufacturer GTIN with manufacturer specific prefix to derive manufacturer name', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x05, description='Luminaire manufacturer GTIN with manufacturer specific prefix to derive manufacturer name', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x06, description='Luminaire manufacturer GTIN with manufacturer specific prefix to derive manufacturer name', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x07, description='Luminaire manufacturer GTIN with manufacturer specific prefix to derive manufacturer name', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x08, description='Luminaire manufacturer GTIN with manufacturer specific prefix to derive manufacturer name', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x09, description='Luminaire identification number', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x0a, description='Luminaire identification number', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x0b, description='Luminaire identification number', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x0c, description='Luminaire identification number', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x0d, description='Luminaire identification number', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x0e, description='Luminaire identification number', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x0f, description='Luminaire identification number', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x10, description='Luminaire identification number', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x11, description='Content Format IDa (MSB)', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x12, description='Content Format IDa (LSB)', default=0x03, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x13, description='Luminaire year of manufacture [YY] [0,99] = YY; [100,MASK] = unknown', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x14, description='Luminaire week of manufacture [WW] [1,53] = WW; 0,[54,MASK] = unknown', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x15, description='Nominal Input Power [W] (MSB)', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x16, description='Nominal Input Power [W] (LSB); [0,MASK-1] = Power; MASK = unknown', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x17, description='Power at minimum dim level [W] (MSB)', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x18, description='Power at minimum dim level [W] (LSB); [0,MASK-1] = Power; MASK = unknown', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x19, description='Nominal Minimum AC mains voltage [V] (MSB)', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x1a, description='Nominal Minimum AC mains voltage [V] (LSB); [90,480] = Voltage; [0,89],[481,MASK] = unknown', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x1b, description='Nominal Maximum AC mains voltage [V] (MSB)', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x1c, description='Nominal Maximum AC mains voltage [V] (LSB); [90,480] = Voltage; [0,89],[481,MASK] = unknown', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x1d, description='Nominal light output [Lm] (MSB)', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x1e, description='Nominal light output [Lm]', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x1f, description='Nominal light output [Lm] (LSB); [0,MASK-1] = Light output; MASK = unknown', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x20, description='CRI [0,100] = CRI; [101,MASK] = unknown', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x21, description='CCT [K] (MSB)', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x22, description='CCT [K] (LSB); [0,17000] = CCT; [17001,MASK-2],MASK = unknown; MASK – 1 = Part 209 implemented', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x23, description='Light Distribution Type; 0 = not specified; 1 = Type I; 2 = Type II; 3 = Type III; 4 = Type IV; 5 = Type V; 6-254 = reserved for additional types MASK = unknown According to IES 901.11, Diagram 5', default=0xff, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x24, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x25, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x26, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x27, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x28, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x29, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x2a, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x2b, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x2c, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x2d, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x2e, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x2f, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x30, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x31, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x32, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x33, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x34, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x35, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x36, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x37, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x38, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x39, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x3a, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x3b, description='Luminaire color [24 ascii character string, first char at 0x24]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x3c, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x3d, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x3e, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x3f, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x40, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x41, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x42, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x43, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x44, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x45, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x46, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x47, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x48, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x49, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x4a, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x4b, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x4c, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x4d, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x4e, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x4f, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x50, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x51, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x52, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x53, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x54, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x55, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x56, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x57, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x58, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x59, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x5a, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x5b, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x5c, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x5d, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x5e, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x5f, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x60, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x61, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x62, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x63, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x64, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x65, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x66, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x67, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x68, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x69, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x6a, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x6b, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x6c, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x6d, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x6e, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x6f, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x70, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x71, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x72, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x73, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x74, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x75, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x76, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x77, description='Luminaire identification [60 ascii character string, first char at 0x3C]d Range [0, 0xFF]', default=0x00, reset=None, type_=MemoryType.NVM_RW_P),
    MemoryLocation(bank=1, address=0x78, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x79, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x7a, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x7b, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x7c, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x7d, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x7e, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x7f, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x80, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x81, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x82, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x83, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x84, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x85, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x86, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x87, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x88, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x89, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x8a, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x8b, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x8c, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x8d, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x8e, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x8f, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x90, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x91, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x92, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x93, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x94, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x95, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x96, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x97, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x98, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x99, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x9a, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x9b, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x9c, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x9d, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x9e, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0x9f, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xa0, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xa1, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xa2, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xa3, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xa4, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xa5, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xa6, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xa7, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xa8, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xa9, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xaa, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xab, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xac, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xad, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xae, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xaf, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xb0, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xb1, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xb2, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xb3, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xb4, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xb5, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xb6, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xb7, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xb8, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xb9, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xba, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xbb, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xbc, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xbd, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xbe, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xbf, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xc0, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xc1, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xc2, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xc3, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xc4, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xc5, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xc6, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xc7, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xc8, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xc9, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xca, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xcb, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xcc, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xcd, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xce, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xcf, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xd0, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xd1, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xd2, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xd3, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xd4, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xd5, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xd6, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xd7, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xd8, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xd9, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xda, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xdb, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xdc, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xdd, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xde, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xdf, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xe0, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xe1, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xe2, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xe3, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xe4, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xe5, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xe6, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xe7, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xe8, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xe9, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xea, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xeb, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xec, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xed, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xee, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xef, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xf0, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xf1, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xf2, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xf3, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xf4, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xf5, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xf6, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xf7, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xf8, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xf9, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xfa, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xfb, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xfc, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xfd, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xfe, description='Manufacturer-specific.', default=None, reset=None, type_=None),
    MemoryLocation(bank=1, address=0xff, description='Reserved – not implemented', default=-1, reset=None, type_=None)
))

class ManufacturerGTIN(MemoryValue):

    locations = (
        BANK_1.locations[0x03],
        BANK_1.locations[0x04],
        BANK_1.locations[0x05],
        BANK_1.locations[0x06],
        BANK_1.locations[0x07],
        BANK_1.locations[0x08]
    )

class LuminaireID(MemoryValue):

    locations = (
        BANK_1.locations[0x09],
        BANK_1.locations[0x0A],
        BANK_1.locations[0x0B],
        BANK_1.locations[0x0C],
        BANK_1.locations[0x0D],
        BANK_1.locations[0x0E],
        BANK_1.locations[0x0F],
        BANK_1.locations[0x10]
    )

class ContentFormatID(NumericValue):

    locations = (
        BANK_1.locations[0x11],
        BANK_1.locations[0x12]
    )

class YearOfManufacture(NumericValue):

    locations = (BANK_1.locations[0x13])

class WeekOfManufacture(NumericValue):

    locations = (BANK_1.locations[0x14])

class InputPowerNominal(NumericValue):

    unit = 'W'

    locations = (
        BANK_1.locations[0x15],
        BANK_1.locations[0x16]
    )

class InputPowerMinimumDim(NumericValue):

    unit = 'W'

    locations = (
        BANK_1.locations[0x17],
        BANK_1.locations[0x18]
    )

class MainVoltageMinimum(NumericValue):

    unit = 'V'

    locations = (
        BANK_1.locations[0x19],
        BANK_1.locations[0x1A]
    )

class MainVoltageMaximum(NumericValue):

    unit = 'V'

    locations = (
        BANK_1.locations[0x1B],
        BANK_1.locations[0x1C]
    )

class LightOutputNominal(NumericValue):

    unit = 'Lm'

    locations = (
        BANK_1.locations[0x1D],
        BANK_1.locations[0x1E],
        BANK_1.locations[0x1F]
    )

class CRI(NumericValue):

    locations = (BANK_1.locations[0x20])

class CCT(NumericValue):

    unit = 'K'

    locations = (
        BANK_1.locations[0x21],
        BANK_1.locations[0x22]
    )

class LuminaireColor(StringValue):

    locations = (
        BANK_1.locations[0x24],
        BANK_1.locations[0x25],
        BANK_1.locations[0x26],
        BANK_1.locations[0x27],
        BANK_1.locations[0x28],
        BANK_1.locations[0x29],
        BANK_1.locations[0x2A],
        BANK_1.locations[0x2B],
        BANK_1.locations[0x2C],
        BANK_1.locations[0x2D],
        BANK_1.locations[0x2E],
        BANK_1.locations[0x2F],
        BANK_1.locations[0x30],
        BANK_1.locations[0x31],
        BANK_1.locations[0x32],
        BANK_1.locations[0x33],
        BANK_1.locations[0x34],
        BANK_1.locations[0x35],
        BANK_1.locations[0x36],
        BANK_1.locations[0x37],
        BANK_1.locations[0x38],
        BANK_1.locations[0x39],
        BANK_1.locations[0x3A],
        BANK_1.locations[0x3B]
    )

class LuminaireIdentification(StringValue):

    locations = (
        BANK_1.locations[0x3C],
        BANK_1.locations[0x3D],
        BANK_1.locations[0x3E],
        BANK_1.locations[0x3F],
        BANK_1.locations[0x40],
        BANK_1.locations[0x41],
        BANK_1.locations[0x42],
        BANK_1.locations[0x43],
        BANK_1.locations[0x44],
        BANK_1.locations[0x45],
        BANK_1.locations[0x46],
        BANK_1.locations[0x47],
        BANK_1.locations[0x48],
        BANK_1.locations[0x49],
        BANK_1.locations[0x4A],
        BANK_1.locations[0x4B],
        BANK_1.locations[0x4C],
        BANK_1.locations[0x4D],
        BANK_1.locations[0x4E],
        BANK_1.locations[0x4F],
        BANK_1.locations[0x50],
        BANK_1.locations[0x51],
        BANK_1.locations[0x52],
        BANK_1.locations[0x53],
        BANK_1.locations[0x54],
        BANK_1.locations[0x55],
        BANK_1.locations[0x56],
        BANK_1.locations[0x57],
        BANK_1.locations[0x58],
        BANK_1.locations[0x59],
        BANK_1.locations[0x5A],
        BANK_1.locations[0x5B],
        BANK_1.locations[0x5C],
        BANK_1.locations[0x5D],
        BANK_1.locations[0x5E],
        BANK_1.locations[0x5F],
        BANK_1.locations[0x60],
        BANK_1.locations[0x61],
        BANK_1.locations[0x62],
        BANK_1.locations[0x63],
        BANK_1.locations[0x64],
        BANK_1.locations[0x65],
        BANK_1.locations[0x66],
        BANK_1.locations[0x67],
        BANK_1.locations[0x68],
        BANK_1.locations[0x69],
        BANK_1.locations[0x6A],
        BANK_1.locations[0x6B],
        BANK_1.locations[0x6C],
        BANK_1.locations[0x6D],
        BANK_1.locations[0x6E],
        BANK_1.locations[0x6F],
        BANK_1.locations[0x70],
        BANK_1.locations[0x71],
        BANK_1.locations[0x72],
        BANK_1.locations[0x73],
        BANK_1.locations[0x74],
        BANK_1.locations[0x75],
        BANK_1.locations[0x76],
        BANK_1.locations[0x77]
    )

if __name__ == '__main__':
    from dali.driver.quaddali import SyncQuadDALIUSBDriver
    from dali.address import Short

    iface = SyncQuadDALIUSBDriver(port='/dev/ttyS24')

    print('"',
        LuminaireIdentification.retrieve(iface, Short(0))
    ,'"')

    iface.backend.close()