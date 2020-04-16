from .location import MemoryBank, MemoryLocation, MemoryType, MemoryValue, NumericValue, StringValue, ScaledNumericValue

BANK_202 = MemoryBank(bank=202, mandatory=True, locations=(
    MemoryLocation(bank=202, address=0x00, description='Address of last addressable memory location', default=0x0f, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=202, address=0x01, description='Indicator byte', default=None, reset=None, type_=None),
    MemoryLocation(bank=202, address=0x02, description='Lock byte Lockable bytes in the memory bank shall be read-only while the lock byte has a value different from 0x55.', default=0xff, reset=0xffb, type_=MemoryType.RAM_RW),
    MemoryLocation(bank=202, address=0x03, description='Version of the memory bank', default=0x01, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=202, address=0x04, description='ScaleFactorForActiveEnergy, scale factor for measured Active Energy values in this memory bank, expressed as power of 10 (scale factor = 10^ScaleFactorForActiveEnergy * 1 Wh); example: -3 denotes milli, +3 denotes kilo Range of validity: [0, 6],[0xFA,0xFF]', default=None, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=202, address=0x05, description='ActiveEnergy (MSB)', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=202, address=0x06, description='ActiveEnergy', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=202, address=0x07, description='ActiveEnergy', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=202, address=0x08, description='ActiveEnergy', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=202, address=0x09, description='ActiveEnergy', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=202, address=0x0a, description='ActiveEnergy (LSB); scale factor is defined by ScaleFactorForActiveEnergy (0x04) Range of validity: [0, 0xFF FF FF FF FF FD] ,TMASK', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=202, address=0x0b, description='ScaleFactorForActivePower, scale factor for measured Active Power values in this memory bank, expressed as power of 10 (scale factor = 10^ScaleFactorForActovePower * 1 W); example: -3 denotes milli, +3 denotes kilo Range of validity: [0, 6],[0xFA,0xFF]', default=None, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=202, address=0x0c, description='ActivePower (MSB)', default=0x0d, reset=None, type_=MemoryType.RAM_RO),
    MemoryLocation(bank=202, address=0x0d, description='ActivePower', default=0x0d, reset=None, type_=MemoryType.RAM_RO),
    MemoryLocation(bank=202, address=0x0e, description='ActivePower', default=0x0d, reset=None, type_=MemoryType.RAM_RO),
    MemoryLocation(bank=202, address=0x0f, description='ActivePower (LSB); scale factor is defined by ScaleFactorForActivePower (0x0B) Range of validity: [0, 0xFF FF FF FD], TMASK', default=0x0d, reset=None, type_=MemoryType.RAM_RO)
))

class ActiveEnergy(ScaledNumericValue):

    unit = 'Wh'

    locations = (
        BANK_202.locations[0x05],
        BANK_202.locations[0x06],
        BANK_202.locations[0x07],
        BANK_202.locations[0x08],
        BANK_202.locations[0x09],
        BANK_202.locations[0x0A]
    )

    scale_location = BANK_202.locations[0x04]
    
class ActivePower(ScaledNumericValue):

    unit = 'W'

    locations = (
        BANK_202.locations[0x0C],
        BANK_202.locations[0x0D],
        BANK_202.locations[0x0E],
        BANK_202.locations[0x0F]
    )

    scale_location = BANK_202.locations[0x0B]

BANK_203 = MemoryBank(bank=203, mandatory=False, locations=(
    MemoryLocation(bank=203, address=0x00, description='Address of last addressable memory location', default=0x0f, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=203, address=0x01, description='Indicator byte', default=None, reset=None, type_=None),
    MemoryLocation(bank=203, address=0x02, description='Lock byte Lockable bytes in the memory bank shall be read-only while the lock byte has a value different from 0x55.', default=0xff, reset=0xffb, type_=MemoryType.RAM_RW),
    MemoryLocation(bank=203, address=0x03, description='Version of the memory bank', default=0x01, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=203, address=0x04, description='ScaleFactorForApparentEnergy, scale factor for measured Apparent Energy values in this memory bank, expressed as power of 10 (scale factor = 10ScaleFactorForApparentEnergy * 1 VAh); example: -3 denotes milli, +3 denotes kilo Range of validity: [0, 6],[0xFA,0xFF]', default=None, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=203, address=0x05, description='ApparentEnergy (MSB)', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=203, address=0x06, description='ApparentEnergy', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=203, address=0x07, description='ApparentEnergy', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=203, address=0x08, description='ApparentEnergy', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=203, address=0x09, description='ApparentEnergy', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=203, address=0x0a, description='ApparentEnergy (LSB); scale factor is defined by ScaleFactorForApparentEnergy (0x04) Range of validity: [0, 0xFF FF FF FF FF FD], TMASK', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=203, address=0x0b, description='ScaleFactorForApparentPower, scale factor for measured Apparent Power values in this memory bank, expressed as power of 10 (scale factor = 10ScaleFactortForApparentPower * 1 VA); example: -3 denotes milli, +3 denotes kilo Range of validity: [0, 6],[0xFA,0xFF]', default=None, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=203, address=0x0c, description='ApparentPower (MSB)', default=0x0d, reset=None, type_=MemoryType.RAM_RO),
    MemoryLocation(bank=203, address=0x0d, description='ApparentPower', default=0x0d, reset=None, type_=MemoryType.RAM_RO),
    MemoryLocation(bank=203, address=0x0e, description='ApparentPower', default=0x0d, reset=None, type_=MemoryType.RAM_RO),
    MemoryLocation(bank=203, address=0x0f, description='ApparentPower (LSB); scale factor is defined by ScaleFactorForApparentPower (0x0B) Range of validity: [0, 0xFF FF FF FD], TMASK', default=0x0d, reset=None, type_=MemoryType.RAM_RO)
))

class ApparentEnergy(ScaledNumericValue):

    unit = 'Wh'

    locations = (
        BANK_203.locations[0x05],
        BANK_203.locations[0x06],
        BANK_203.locations[0x07],
        BANK_203.locations[0x08],
        BANK_203.locations[0x09],
        BANK_203.locations[0x0A]
    )

    scale_location = BANK_203.locations[0x04]
    
class ApparentPower(ScaledNumericValue):

    unit = 'W'

    locations = (
        BANK_203.locations[0x0C],
        BANK_203.locations[0x0D],
        BANK_203.locations[0x0E],
        BANK_203.locations[0x0F]
    )

    scale_location = BANK_203.locations[0x0B]

BANK_204 = MemoryBank(bank=204, mandatory=False, locations=(
    MemoryLocation(bank=204, address=0x00, description='Address of last addressable memory location', default=0x0f, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=204, address=0x01, description='Indicator byte', default=None, reset=None, type_=None),
    MemoryLocation(bank=204, address=0x02, description='Lock byte Lockable bytes in the memory bank shall be read-only while the lock byte has a value different from 0x55.', default=0xff, reset=0xffb, type_=MemoryType.RAM_RW),
    MemoryLocation(bank=204, address=0x03, description='Version of the memory bank', default=0x01, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=204, address=0x04, description='ScaleFactorForLoadsideEnergy, scale factor for measured Active Energy Loadside values in this memory bank, expressed as power of 10 (scale factor = 10ScaleFactorForLoadsideEnergy * 1 Wh); example: -3 denotes milli and +3 denotes kilo Range of validity: [0, 6],[0xFA,0xFF]', default=None, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=204, address=0x05, description='ActiveEnergyLoadside (MSB)', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=204, address=0x06, description='ActiveEnergyLoadside', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=204, address=0x07, description='ActiveEnergyLoadside', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=204, address=0x08, description='ActiveEnergyLoadside', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=204, address=0x09, description='ActiveEnergyLoadside', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=204, address=0x0a, description='ActiveEnergyLoadside (LSB); scale factor is defined by ScaleFactorForLoadsideEnergy (0x04) Range of validity: [0, 0xFF FF FF FF FF FD], TMASK', default=0x00, reset=None, type_=MemoryType.NVM_RO),
    MemoryLocation(bank=204, address=0x0b, description='ScaleFactorForLoadsidePower, scale factor for measured Active Power Loadside values in this memory bank, expressed as power of 10 (scale factor = 10ScaleFactorForLoadsidePower * 1 W); example: -3 denotes milli and +3 denotes kilo Range of validity: [0, 6],[0xFA,0xFF]', default=None, reset=None, type_=MemoryType.ROM),
    MemoryLocation(bank=204, address=0x0c, description='ActivePowerLoadside (MSB)', default=0x0d, reset=None, type_=MemoryType.RAM_RO),
    MemoryLocation(bank=204, address=0x0d, description='ActivePowerLoadside', default=0x0d, reset=None, type_=MemoryType.RAM_RO),
    MemoryLocation(bank=204, address=0x0e, description='ActivePowerLoadside', default=0x0d, reset=None, type_=MemoryType.RAM_RO),
    MemoryLocation(bank=204, address=0x0f, description='ActivePowerLoadside (LSB); scale factor is defined by ScaleFactorForLoadsidePower (0x0B) Range of validity: [0, 0xFF FF FF FD], TMASK', default=0x0d, reset=None, type_=MemoryType.RAM_RO)
))

class ActiveEnergyLoadside(ScaledNumericValue):

    unit = 'Wh'

    locations = (
        BANK_204.locations[0x05],
        BANK_204.locations[0x06],
        BANK_204.locations[0x07],
        BANK_204.locations[0x08],
        BANK_204.locations[0x09],
        BANK_204.locations[0x0A]
    )

    scale_location = BANK_204.locations[0x04]
    
class ActivePowerLoadside(ScaledNumericValue):

    unit = 'W'

    locations = (
        BANK_204.locations[0x0C],
        BANK_204.locations[0x0D],
        BANK_204.locations[0x0E],
        BANK_204.locations[0x0F]
    )

    scale_location = BANK_204.locations[0x0B]

if __name__ == '__main__':
    from dali.driver.quaddali import SyncQuadDALIUSBDriver
    from dali.address import Short

    iface = SyncQuadDALIUSBDriver(port='/dev/ttyS24')

    print('"',
        ActiveEnergy.retrieve(iface, Short(0))
    ,'"')
    print('"',
        ActivePower.retrieve(iface, Short(0))
    ,'"')
    print()
    print('"',
        ApparentEnergy.retrieve(iface, Short(0))
    ,'"')
    print('"',
        ApparentPower.retrieve(iface, Short(0))
    ,'"')
    print()
    print('"',
        ActiveEnergyLoadside.retrieve(iface, Short(0))
    ,'"')
    print('"',
        ActivePowerLoadside.retrieve(iface, Short(0))
    ,'"')

    iface.backend.close()