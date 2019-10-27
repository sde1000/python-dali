import dali.gear.general as gear

commands = {
    '':'',
    '-':'DIRECT ARC POWER CONTROL (level)',
    0x00:'OFF',
    0x01:'UP',
    0x02:'DOWN',
    0x03:'STEP UP',
    0x04:'STEP DOWN',
    0x05:'RECALL MAX LEVEL',
    0x06:'RECALL MIN LEVEL',
    0x07:'STEP DOWN AND OFF',
    0x08:'ON AND STEP UP',
    0x09:'ENABLE DAPC SEQUENCE',
    0x0A:'GO TO LAST ACTIVE LEVEL',
    0x0B:'CONTINUOUS UP',
    0x0C:'CONTINUOUS DOWN',
    0x10:'GO TO SCENE (scene number)',
    0x20:'RESET',
    0x21:'STORE ACTUAL LEVEL IN THE DTR0',
    0x22:'SAVE PERSISTENT VARIABLES',
    0x23:'SET OPERATION MODE (mode number)',
    0x24:'RESET MEMORY BANK (bank number)',
    0x25:'IDENTIFY DEVICE',
    0x2A:'SET MAX LEVEL (level)',
    0x2B:'SET MIN LEVEL (level)',
    0x2C:'SET SYSTEM FAILURE LEVEL (level)',
    0x2D:'SET POWER ON LEVEL (level)',
    0x2E:'SET FADE TIME (fade time)',
    0x2F:'SET FADE RATE (fade rate)',
    0x30:'SET EXTENDED FADE TIME (fade time)',
    0x40:'SET SCENE (scene number, level)',
    0x50:'REMOVE FROM SCENE (scene number)',
    0x60:'ADD TO GROUP (group)',
    0x70:'REMOVE FROM GROUP (group)',
    0x80:'SET SHORT ADDRESS (address)',
    0x81:'ENABLE WRITE MEMORY',
    0x90:'QUERY STATUS',
    0x91:'QUERY CONTROL GEAR PRESENT',
    0x92:'QUERY LAMP_FAILURE',
    0x93:'QUERY LAMP POWER ON',
    0x94:'QUERY LIMIT ERROR',
    0x95:'QUERY RESET STATE',
    0x96:'QUERY MISSING SHORT ADDRESS',
    0x97:'QUERY VERSION NUMBER',
    0x98:'QUERY CONTENT DTR0',
    0x99:'QUERY DEVICE TYPE',
    0x9A:'QUERY PHYSICAL MINIMUM',
    0x9B:'QUERY POWER FAILURE',
    0x9C:'QUERY CONTENT DTR1',
    0x9D:'QUERY CONTENT DTR2',
    0x9E:'QUERY OPERATING MODE',
    0x9F:'QUERY LIGHT SOURCE TYPE',
    0xA0:'QUERY ACTUAL LEVEL',
    0xA1:'QUERY MAX LEVEL',
    0xA2:'QUERY MIN LEVEL',
    0xA3:'QUERY POWER ON LEVEL',
    0xA4:'QUERY SYSTEM FAILURE LEVEL',
    0xA5:'QUERY FADE TIME/FADE RATE',
    0xA6:'QUERY MANUFACTURER SPECIFIC MODE',
    0xA7:'QUERY NEXT DEVICE TYPE',
    0xA8:'QUERY EXTENDED FADE TIME',
    0xAA:'QUERY CONTROL GEAR FAILURE',
    0xB0:'QUERY SCENE LEVEL (scene number)',
    0xC0:'QUERY GROUPS 0-7',
    0xC1:'QUERY GROUPS 8-15',
    0xC2:'QUERY RANDOM ADDRESS (H)',
    0xC3:'QUERY RANDOM ADDRESS (M)',
    0xC4:'QUERY RANDOM ADDRESS (L)',
    0xC5:'READ MEMORY LOCATION (memory bank, location',
    0xFF:'QUERY EXTENDED VERSION NUMBER',
}

class DALICommandSender(object):
    '''A class taking care of sending individual DALI commands

    '''

    def __init__(self, interface):
        self._interface = interface

    def getDataLabelRange(self, command):
        '''Function checking if data or DTR0 is required
        '''
        if command == commands['-']:
            return 'Level', 255
        elif command == commands[0x10]:
            return 'Scene number', 15
        elif command == commands[0x23]:
            return 'Mode number', 127
        elif command == commands[0x24]:
            return 'Bank number', 255
        elif command == commands[0x2A] or \
             command == commands[0x2B] or \
             command == commands[0x2C] or \
             command == commands[0x2D]:
            return 'Level', 255
        elif command == commands[0x2E]:
            return 'Fade time', 255
        elif command == commands[0x2F]:
            return 'Fade rate', 255
        elif command == commands[0x30]:
            return 'Fade time', 255
        elif command == commands[0x40]:
            return 'Scene number, level', 15
        elif command == commands[0x50]:
            return 'Scene number', 15
        elif command == commands[0x60] or \
             command == commands[0x70]:
            return 'Group', 15
        elif command == commands[0x80]:
            return 'Address', 63
        elif command == commands[0xB0]:
            return 'Scene number', 15
        elif command == commands[0xC5]:
            return 'Memory bank, location', 255
        else:
            return 'Data', 0

    def send(self, command, address, data, data2=None):
        '''Function to send DALI commands.
        '''
        if command == commands['-']:
            main_command = gear.DAPC(address, data)
            self._interface.send(main_command)
        elif command == commands[0x00]:
            main_command = gear.Off(address)
            self._interface.send(main_command)
        elif command == commands[0x01]:
            main_command = gear.Up(address)
            self._interface.send(main_command)
        elif command == commands[0x02]:
            main_command = gear.Down(address)
            self._interface.send(main_command)
        elif command == commands[0x03]:
            main_command = gear.StepUp(address)
            self._interface.send(main_command)
        elif command == commands[0x04]:
            main_command = gear.StepDown(address)
            self._interface.send(main_command)
        elif command == commands[0x05]:
            main_command = gear.RecallMaxLevel(address)
            self._interface.send(main_command)
        elif command == commands[0x06]:
            main_command = gear.RecallMinLevel(address)
            self._interface.send(main_command)
        elif command == commands[0x07]:
            main_command = gear.StepDownAndOff(address)
            self._interface.send(main_command)
        elif command == commands[0x08]:
            main_command = gear.OnAndStepUp(address)
            self._interface.send(main_command)
        elif command == commands[0x09]:
            main_command = gear.EnableDAPCSequence(address)
            self._interface.send(main_command)
        elif command == commands[0x0A]:
            main_command = gear.GoToLastActiveLevel(address)
            self._interface.send(main_command)
        elif command == commands[0x0B]:
            main_command = gear.ContinuousUp(address)
            self._interface.send(main_command)
        elif command == commands[0x0C]:
            main_command = gear.ContinuousDown(address)
            self._interface.send(main_command)
        elif command == commands[0x10]:
            main_command = gear.GoToScene(address, data)
            self._interface.send(main_command)
        elif command == commands[0x20]:
            main_command = gear.Reset(address)
            self._interface.send(main_command)
        elif command == commands[0x21]:
            main_command = gear.StoreActualLevelInDTR0(address)
            self._interface.send(main_command)
        elif command == commands[0x22]:
            main_command = gear.SavePersistentVariables(address)
            self._interface.send(main_command)
        elif command == commands[0x23]:
            self._interface.send(gear.DTR0(data))
            main_command = gear.SetOperatingMode(address)
            self._interface.send(main_command)
        elif command == commands[0x24]:
            self._interface.send(gear.DTR0(data))
            main_command = gear.ResetMemoryBank(address)
            self._interface.send(main_command)
        elif command == commands[0x25]:
            main_command = gear.IdentifyDevice(address)
            self._interface.send(main_command)
        elif command == commands[0x2A]:
            self._interface.send(gear.DTR0(data))
            main_command = gear.SetMaxLevel(address)
            self._interface.send(main_command)
        elif command == commands[0x2B]:
            self._interface.send(gear.DTR0(data))
            main_command = gear.SetMinLevel(address)
            self._interface.send(main_command)
        elif command == commands[0x2C]:
            self._interface.send(gear.DTR0(data))
            main_command = gear.SetSystemFailureLevel(address)
            self._interface.send(main_command)
        elif command == commands[0x2D]:
            self._interface.send(gear.DTR0(data))
            main_command = gear.SetPowerOnLevel(address)
            self._interface.send(main_command)
        elif command == commands[0x2E]:
            self._interface.send(gear.DTR0(data))
            main_command = gear.SetFadeTime(address)
            self._interface.send(main_command)
        elif command == commands[0x2F]:
            self._interface.send(gear.DTR0(data))
            main_command = gear.SetFadeRate(address)
            self._interface.send(main_command)
        elif command == commands[0x30]:
            self._interface.send(gear.DTR0(data))
            main_command = gear.SetExtendedFadeTime(address)
            self._interface.send(main_command)
        elif command == commands[0x40]:
            self._interface.send(gear.DTR0(data2))
            main_command = gear.SetScene(address, data)
            self._interface.send(main_command)
        elif command == commands[0x50]:
            main_command = gear.RemoveFromScene(address, data)
            self._interface.send(main_command)
        elif command == commands[0x60]:
            main_command = gear.AddToGroup(address, data)
            self._interface.send(main_command)
        elif command == commands[0x70]:
            main_command = gear.RemoveFromGroup(address, data)
            self._interface.send(main_command)
        elif command == commands[0x80]:
            self._interface.send(gear.DTR0(data))
            main_command = gear.SetShortAddress(address)
            self._interface.send(main_command)
        elif command == commands[0x81]:
            main_command = gear.EnableWriteMemory(address)
            self._interface.send(main_command)
        elif command == commands[0x90]:
            main_command = gear.QueryStatus(address)
            self._interface.send(main_command)
        elif command == commands[0x91]:
            main_command = gear.QueryControlGearPresent(address)
            self._interface.send(main_command)
        elif command == commands[0x92]:
            main_command = gear.QueryLampFailure(address)
            self._interface.send(main_command)
        elif command == commands[0x93]:
            main_command = gear.QueryLampPowerOn(address)
            self._interface.send(main_command)
        elif command == commands[0x94]:
            main_command = gear.QueryLimitError(address)
            self._interface.send(main_command)
        elif command == commands[0x95]:
            main_command = gear.QueryResetState(address)
            self._interface.send(main_command)
        elif command == commands[0x96]:
            main_command = gear.QueryMissingShortAddress(address)
            self._interface.send(main_command)
        elif command == commands[0x97]:
            main_command = gear.QueryVersionNumber(address)
            self._interface.send(main_command)
        elif command == commands[0x98]:
            main_command = gear.QueryContentDTR0(address)
            self._interface.send(main_command)
        elif command == commands[0x99]:
            main_command = gear.QueryDeviceType(address)
            self._interface.send(main_command)
        elif command == commands[0x9A]:
            main_command = gear.QueryPhysicalMinimum(address)
            self._interface.send(main_command)
        elif command == commands[0x9B]:
            main_command = gear.QueryPowerFailure(address)
            self._interface.send(main_command)
        elif command == commands[0x9C]:
            main_command = gear.QueryContentDTR1(address)
            self._interface.send(main_command)
        elif command == commands[0x9D]:
            main_command = gear.QueryContentDTR2(address)
            self._interface.send(main_command)
        elif command == commands[0x9E]:
            main_command = gear.QueryOperatingMode(address)
            self._interface.send(main_command)
        elif command == commands[0x9F]:
            main_command = gear.QueryLightSourceType(address)
            self._interface.send(main_command)
        elif command == commands[0xA0]:
            main_command = gear.QueryActualLevel(address)
            self._interface.send(main_command)
        elif command == commands[0xA1]:
            main_command = gear.QueryMaxLevel(address)
            self._interface.send(main_command)
        elif command == commands[0xA2]:
            main_command = gear.QueryMinLevel(address)
            self._interface.send(main_command)
        elif command == commands[0xA3]:
            main_command = gear.QueryPowerOnLevel(address)
            self._interface.send(main_command)
        elif command == commands[0xA4]:
            main_command = gear.QuerySystemFailureLevel(address)
            self._interface.send(main_command)
        elif command == commands[0xA5]:
            main_command = gear.QueryFadeTimeFadeRate(address)
            self._interface.send(main_command)
        elif command == commands[0xA6]:
            main_command = gear.QueryManufacturerSpecificMode(address)
            self._interface.send(main_command)
        elif command == commands[0xA7]:
            main_command = gear.QueryNextDeviceType(address)
            self._interface.send(main_command)
        elif command == commands[0xA8]:
            main_command = gear.QueryExtendedFadeTime(address)
            self._interface.send(main_command)
        elif command == commands[0xAA]:
            main_command = gear.QueryControlGearFailure(address)
            self._interface.send(main_command)
        elif command == commands[0xB0]:
            main_command = gear.QuerySceneLevel(address, data)
            self._interface.send(main_command)
        elif command == commands[0xC0]:
            main_command = gear.QueryGroupsZeroToSeven(address)
            self._interface.send(main_command)
        elif command == commands[0xC1]:
            main_command = gear.QueryGroupsEightToFifteen(address)
            self._interface.send(main_command)
        elif command == commands[0xC2]:
            main_command = gear.QueryRandomAddressH(address)
            self._interface.send(main_command)
        elif command == commands[0xC3]:
            main_command = gear.QueryRandomAddressM(address)
            self._interface.send(main_command)
        elif command == commands[0xC4]:
            main_command = gear.QueryRandomAddressL(address)
            self._interface.send(main_command)
        elif command == commands[0xC5]:
            self._interface.send(gear.DTR1(data))
            self._interface.send(gear.DTR0(data2))
            main_command = gear.ReadMemoryLocation(address)
            self._interface.send(main_command)
        elif command == commands[0xFF]:
            main_command = gear.QueryExtendedVersionNumber(address)
            self._interface.send(main_command)
        return main_command.is_query