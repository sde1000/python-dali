from .location import MemoryLocation, MemoryType, MemoryValue, NumericValue, StringValue, ScaledNumericValue, LockableValueMixin

class ActiveEnergy(ScaledNumericValue, LockableValueMixin):
    """Active Energy in Wh"""

    unit = 'Wh'

    locations = (
        MemoryLocation(bank=202, address=0x05, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=202, address=0x06, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=202, address=0x07, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=202, address=0x08, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=202, address=0x09, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=202, address=0x0a, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

    scale_location = MemoryLocation(bank=202, address=0x04, default=None, reset=None, type_=MemoryType.ROM)
    
class ActivePower(ScaledNumericValue, LockableValueMixin):
    """Active Power in W"""

    unit = 'W'

    locations = (
        MemoryLocation(bank=202, address=0x0c, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=202, address=0x0d, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=202, address=0x0e, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=202, address=0x0f, default=0x0d, reset=None, type_=MemoryType.RAM_RO)
    )

    scale_location = MemoryLocation(bank=202, address=0x0b, default=None, reset=None, type_=MemoryType.ROM)

class ApparentEnergy(ScaledNumericValue, LockableValueMixin):
    """Apparent Energy in VAh"""

    unit = 'VAh'

    locations = (
        MemoryLocation(bank=203, address=0x05, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=203, address=0x06, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=203, address=0x07, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=203, address=0x08, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=203, address=0x09, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=203, address=0x0a, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

    scale_location = MemoryLocation(bank=203, address=0x04, default=None, reset=None, type_=MemoryType.ROM)
    
class ApparentPower(ScaledNumericValue, LockableValueMixin):
    """Apparent Power in VA"""

    unit = 'VA'

    locations = (
        MemoryLocation(bank=203, address=0x0c, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=203, address=0x0d, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=203, address=0x0e, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=203, address=0x0f, default=0x0d, reset=None, type_=MemoryType.RAM_RO)
    )

    scale_location = MemoryLocation(bank=203, address=0x0b, default=None, reset=None, type_=MemoryType.ROM)

class ActiveEnergyLoadside(ScaledNumericValue, LockableValueMixin):
    """Loadside Active Energy in Wh"""

    unit = 'Wh'

    locations = (
        MemoryLocation(bank=204, address=0x05, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=204, address=0x06, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=204, address=0x07, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=204, address=0x08, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=204, address=0x09, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=204, address=0x0a, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

    scale_location = MemoryLocation(bank=204, address=0x04, default=None, reset=None, type_=MemoryType.ROM)
    
class ActivePowerLoadside(ScaledNumericValue, LockableValueMixin):
    """Loadside Active Power in W"""

    unit = 'W'

    locations = (
        MemoryLocation(bank=204, address=0x0c, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=204, address=0x0d, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=204, address=0x0e, default=0x0d, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=204, address=0x0f, default=0x0d, reset=None, type_=MemoryType.RAM_RO)
    )

    scale_location = MemoryLocation(bank=204, address=0x0b, default=None, reset=None, type_=MemoryType.ROM)

if __name__ == '__main__':
    import argparse
    from dali.driver.quaddali import SyncQuadDALIUSBDriver
    from dali.address import Short

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', help='repeat query n times', type=int, default=1)
    parser.add_argument('-s', help='short address of the device that is queried', type=int, default=0)
    parser.add_argument('port', help='serial port to connect to', type=str)
    args = parser.parse_args()

    iface = SyncQuadDALIUSBDriver(port=args.port)

    for i in range(args.n):
        print(f'Run #{i+1}')
        print(f'ActiveEnergy: {ActiveEnergy.retrieve(iface, Short(args.s)):.3f} {ActiveEnergy.unit}')
        print(f'ActivePower: {ActivePower.retrieve(iface, Short(args.s)):.3f} {ActivePower.unit}')
        print(f'ApparentEnergy: {ApparentEnergy.retrieve(iface, Short(args.s)):.3f} {ApparentEnergy.unit}')
        print(f'ApparentPower: {ApparentPower.retrieve(iface, Short(args.s)):.3f} {ApparentPower.unit}')
        print(f'ActiveEnergyLoadside: {ActiveEnergyLoadside.retrieve(iface, Short(args.s)):.3f} ' + \
            f'{ActiveEnergyLoadside.unit}')
        print(f'ActivePowerLoadside: {ActivePowerLoadside.retrieve(iface, Short(args.s)):.3f} ' + \
            f'{ActivePowerLoadside.unit}')
        print()

    iface.backend.close()