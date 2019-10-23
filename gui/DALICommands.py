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
            # 'QUERY_LAMP_FAILURE',
            # 'QUERY_LAMP_POWER_ON',
            # 'QUERY_LIMIT_ERROR',
            # 'QUERY_RESET_STATE',
            # 'QUERY_MISSING_SHORT_ADDRESS',
            # 'QUERY_VERSION_NUMBER',
            # 'QUERY_CONTENT_DTR',
            # 'QUERY_DEVICE_TYPE',
            # 'QUERY_PHYSICAL_MINIMUM_LEVEL',
            # 'QUERY_POWER_FAILURE',
            # 'QUERY_CONTENT_DTR1',
            # 'QUERY_CONTENT_DTR2',
            # 'RESERVED_158',
            # 'RESERVED_159',
            # 'QUERY_ACTUAL_LEVEL',
            # 'QUERY_MAX_LEVEL',
            # 'QUERY_MIN_LEVEL',
            # 'QUERY_POWER_ON_LEVEL',
            # 'QUERY_SYSTEM_FAILURE_LEVEL',
            # 'QUERY_FADE_TIME_FADE_RATE',
            # 'RESERVED_166',
            # 'RESERVED_167',
            # 'RESERVED_168',
            # 'RESERVED_169',
            # 'RESERVED_170',
            # 'RESERVED_171',
            # 'RESERVED_172',
            # 'RESERVED_173',
            # 'RESERVED_174',
            # 'RESERVED_175',
            # 'QUERY_SCENE_LEVEL_0',
            # 'QUERY_SCENE_LEVEL_1',
            # 'QUERY_SCENE_LEVEL_2',
            # 'QUERY_SCENE_LEVEL_3',
            # 'QUERY_SCENE_LEVEL_4',
            # 'QUERY_SCENE_LEVEL_5',
            # 'QUERY_SCENE_LEVEL_6',
            # 'QUERY_SCENE_LEVEL_7',
            # 'QUERY_SCENE_LEVEL_8',
            # 'QUERY_SCENE_LEVEL_9',
            # 'QUERY_SCENE_LEVEL_10',
            # 'QUERY_SCENE_LEVEL_11',
            # 'QUERY_SCENE_LEVEL_12',
            # 'QUERY_SCENE_LEVEL_13',
            # 'QUERY_SCENE_LEVEL_14',
            # 'QUERY_SCENE_LEVEL_15',
            # 'QUERY_GROUPS_0_7',
            # 'QUERY_GROUPS_8_15',
            # 'QUERY_RANDOM_ADDRESS_H',
            # 'QUERY_RANDOM_ADDRESS_M',
            # 'QUERY_RANDOM_ADDRESS_L',
            # 'READ_MEMORY_LOCATION',
            # 'RESERVED_198',
            # 'RESERVED_199',
            # 'RESERVED_200',
            # 'RESERVED_201',
            # 'RESERVED_202',
            # 'RESERVED_203',
            # 'RESERVED_204',
            # 'RESERVED_205',
            # 'RESERVED_206',
            # 'RESERVED_207',
            # 'RESERVED_208',
            # 'RESERVED_209',
            # 'RESERVED_210',
            # 'RESERVED_211',
            # 'RESERVED_212',
            # 'RESERVED_213',
            # 'RESERVED_214',
            # 'RESERVED_215',
            # 'RESERVED_216',
            # 'RESERVED_217',
            # 'RESERVED_218',
            # 'RESERVED_219',
            # 'RESERVED_220',
            # 'RESERVED_221',
            # 'RESERVED_222',
            # 'RESERVED_223',
            # 'APP_EXTENDED_224',
            # 'APP_EXTENDED_225',
            # 'APP_EXTENDED_226',
            # 'APP_EXTENDED_227',
            # 'APP_EXTENDED_228',
            # 'APP_EXTENDED_229',
            # 'APP_EXTENDED_230',
            # 'APP_EXTENDED_231',
            # 'APP_EXTENDED_232',
            # 'APP_EXTENDED_233',
            # 'APP_EXTENDED_234',
            # 'APP_EXTENDED_235',
            # 'APP_EXTENDED_236',
            # 'APP_EXTENDED_237',
            # 'APP_EXTENDED_238',
            # 'APP_EXTENDED_239',
            # 'APP_EXTENDED_240',
            # 'APP_EXTENDED_241',
            # 'APP_EXTENDED_242',
            # 'APP_EXTENDED_243',
            # 'APP_EXTENDED_244',
            # 'APP_EXTENDED_245',
            # 'APP_EXTENDED_246',
            # 'APP_EXTENDED_247',
            # 'APP_EXTENDED_248',
            # 'APP_EXTENDED_249',
            # 'APP_EXTENDED_250',
            # 'APP_EXTENDED_251',
            # 'APP_EXTENDED_252',
            # 'APP_EXTENDED_253',
            # 'APP_EXTENDED_254',
            # 'QUERY_EXTENDED_VERSION_NUM',
            #
            # # special commands
            # 'TERMINATE',
            # 'DATA_TRANSFER_REGISTER_DTR',
            # 'INITIALISE',
            # 'RANDOMISE',
            # 'COMPARE',
            # 'WITHDRAW',
            # 'RESERVED_262',
            # 'RESERVED_263',
            # 'SEARCH_ADDR_H',
            # 'SEARCH_ADDR_M',
            # 'SEARCH_ADDR_L',
            # 'PROGRAM_SHORT_ADDRESS',
            # 'VERIFY_SHORT_ADDRESS',
            # 'QUERY_SHORT_ADDRESS',
            # 'PHYSICAL_SELECTION',
            # 'RESERVED_271',
            # 'ENABLE_DEVICE_TYPE_X',
            # 'DATA_TRANSFER_REGISTER_1',
            # 'DATA_TRANSFER_REGISTER_2',
            # 'WRITE_MEMORY_LOCATION'
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
            return 'Mode number', 255
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
            return 'Scene number, level', 255
        elif command == commands[0x50]:
            return 'Scene number', 255
        elif command == commands[0x60] or \
             command == commands[0x70]:
            return 'Group', 255
        elif command == commands[0x80]:
            return 'Address', 63
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
        return main_command.is_query