import dali.gear.general as gear

commands = ('',
            'DIRECT ARC POWER CONTROL (level)',
            'OFF',
            'UP',
            'DOWN',
            'STEP UP',
            'STEP DOWN',
            'RECALL MAX LEVEL',
            'RECALL MIN LEVEL',
            'STEP DOWN AND OFF',
            'ON AND STEP UP',
            'ENABLE DAPC SEQUENCE',
            'GO TO LAST ACTIVE LEVEL',
            'CONTINUOUS UP',
            'CONTINUOUS DOWN',
            'GO TO SCENE (scene number)',
            'RESET',
            'STORE ACTUAL LEVEL IN THE DTR0',
            'SAVE PERSISTENT VARIABLES',
            'SET OPERATION MODE (mode number)',
            'RESET MEMORY BANK (bank number)',
            'IDENTIFY DEVICE',
            'SET MAX LEVEL (level)',
            'SET MIN LEVEL (level)',
            'SET SYSTEM FAILURE LEVEL (level)',
            'SET POWER ON LEVEL (level)',
            'SET FADE TIME (fade time)',
            'SET FADE RATE (fade rate)',
            'SET EXTENDED FADE TIME (fade time)',
            'SET SCENE (scene number, level)',
            'REMOVE FROM SCENE (scene number)',
            'ADD TO GROUP (group)',
            'REMOVE FROM GROUP (group)',
            'SET SHORT ADDRESS (address)',
            'ENABLE WRITE MEMORY',
            'QUERY STATUS',
            'QUERY_CONTROL_GEAR',
            'QUERY_LAMP_FAILURE',
            'QUERY_LAMP_POWER_ON',
            'QUERY_LIMIT_ERROR',
            'QUERY_RESET_STATE',
            'QUERY_MISSING_SHORT_ADDRESS',
            'QUERY_VERSION_NUMBER',
            'QUERY_CONTENT_DTR',
            'QUERY_DEVICE_TYPE',
            'QUERY_PHYSICAL_MINIMUM_LEVEL',
            'QUERY_POWER_FAILURE',
            'QUERY_CONTENT_DTR1',
            'QUERY_CONTENT_DTR2',
            'RESERVED_158',
            'RESERVED_159',
            'QUERY_ACTUAL_LEVEL',
            'QUERY_MAX_LEVEL',
            'QUERY_MIN_LEVEL',
            'QUERY_POWER_ON_LEVEL',
            'QUERY_SYSTEM_FAILURE_LEVEL',
            'QUERY_FADE_TIME_FADE_RATE',
            'RESERVED_166',
            'RESERVED_167',
            'RESERVED_168',
            'RESERVED_169',
            'RESERVED_170',
            'RESERVED_171',
            'RESERVED_172',
            'RESERVED_173',
            'RESERVED_174',
            'RESERVED_175',
            'QUERY_SCENE_LEVEL_0',
            'QUERY_SCENE_LEVEL_1',
            'QUERY_SCENE_LEVEL_2',
            'QUERY_SCENE_LEVEL_3',
            'QUERY_SCENE_LEVEL_4',
            'QUERY_SCENE_LEVEL_5',
            'QUERY_SCENE_LEVEL_6',
            'QUERY_SCENE_LEVEL_7',
            'QUERY_SCENE_LEVEL_8',
            'QUERY_SCENE_LEVEL_9',
            'QUERY_SCENE_LEVEL_10',
            'QUERY_SCENE_LEVEL_11',
            'QUERY_SCENE_LEVEL_12',
            'QUERY_SCENE_LEVEL_13',
            'QUERY_SCENE_LEVEL_14',
            'QUERY_SCENE_LEVEL_15',
            'QUERY_GROUPS_0_7',
            'QUERY_GROUPS_8_15',
            'QUERY_RANDOM_ADDRESS_H',
            'QUERY_RANDOM_ADDRESS_M',
            'QUERY_RANDOM_ADDRESS_L',
            'READ_MEMORY_LOCATION',
            'RESERVED_198',
            'RESERVED_199',
            'RESERVED_200',
            'RESERVED_201',
            'RESERVED_202',
            'RESERVED_203',
            'RESERVED_204',
            'RESERVED_205',
            'RESERVED_206',
            'RESERVED_207',
            'RESERVED_208',
            'RESERVED_209',
            'RESERVED_210',
            'RESERVED_211',
            'RESERVED_212',
            'RESERVED_213',
            'RESERVED_214',
            'RESERVED_215',
            'RESERVED_216',
            'RESERVED_217',
            'RESERVED_218',
            'RESERVED_219',
            'RESERVED_220',
            'RESERVED_221',
            'RESERVED_222',
            'RESERVED_223',
            'APP_EXTENDED_224',
            'APP_EXTENDED_225',
            'APP_EXTENDED_226',
            'APP_EXTENDED_227',
            'APP_EXTENDED_228',
            'APP_EXTENDED_229',
            'APP_EXTENDED_230',
            'APP_EXTENDED_231',
            'APP_EXTENDED_232',
            'APP_EXTENDED_233',
            'APP_EXTENDED_234',
            'APP_EXTENDED_235',
            'APP_EXTENDED_236',
            'APP_EXTENDED_237',
            'APP_EXTENDED_238',
            'APP_EXTENDED_239',
            'APP_EXTENDED_240',
            'APP_EXTENDED_241',
            'APP_EXTENDED_242',
            'APP_EXTENDED_243',
            'APP_EXTENDED_244',
            'APP_EXTENDED_245',
            'APP_EXTENDED_246',
            'APP_EXTENDED_247',
            'APP_EXTENDED_248',
            'APP_EXTENDED_249',
            'APP_EXTENDED_250',
            'APP_EXTENDED_251',
            'APP_EXTENDED_252',
            'APP_EXTENDED_253',
            'APP_EXTENDED_254',
            'QUERY_EXTENDED_VERSION_NUM',

            # special commands
            'TERMINATE',
            'DATA_TRANSFER_REGISTER_DTR',
            'INITIALISE',
            'RANDOMISE',
            'COMPARE',
            'WITHDRAW',
            'RESERVED_262',
            'RESERVED_263',
            'SEARCH_ADDR_H',
            'SEARCH_ADDR_M',
            'SEARCH_ADDR_L',
            'PROGRAM_SHORT_ADDRESS',
            'VERIFY_SHORT_ADDRESS',
            'QUERY_SHORT_ADDRESS',
            'PHYSICAL_SELECTION',
            'RESERVED_271',
            'ENABLE_DEVICE_TYPE_X',
            'DATA_TRANSFER_REGISTER_1',
            'DATA_TRANSFER_REGISTER_2',
            'WRITE_MEMORY_LOCATION'
            )

class DALICommandSender(object):
    '''A class taking care of sending individual DALI commands

    '''

    def __init__(self, interface):
        self._interface = interface

    def getDataLabelRange(self, command):
        '''Function checking if data or DTR0 is required
        '''
        if command == commands[1]:
            return 'Level', 255
        elif command == commands[15]:
            return 'Scene number', 15
        elif command == commands[19]:
            return 'Mode number', 255
        elif command == commands[20]:
            return 'Bank number', 255
        elif command == commands[22] or \
             command == commands[23] or \
             command == commands[24] or \
             command == commands[25]:
            return 'Level', 255
        elif command == commands[26]:
            return 'Fade time', 255
        elif command == commands[27]:
            return 'Fade rate', 255
        elif command == commands[28]:
            return 'Fade time', 255
        elif command == commands[29]:
            return 'Scene number, level', 255
        elif command == commands[30]:
            return 'Scene number', 255
        elif command == commands[31] or \
             command == commands[32]:
            return 'Group', 255
        elif command == commands[33]:
            return 'Address', 63
        else:
            return 'Data', 0

    def send(self, command, address, data, data2=None):
        '''Function to send DALI commands.
        '''
        if command == commands[1]:
            self._interface.send(gear.DAPC(address, data))
        elif command == commands[2]:
            self._interface.send(gear.Off(address))
        elif command == commands[3]:
            self._interface.send(gear.Up(address))
        elif command == commands[4]:
            self._interface.send(gear.Down(address))
        elif command == commands[5]:
            self._interface.send(gear.StepUp(address))
        elif command == commands[6]:
            self._interface.send(gear.StepDown(address))
        elif command == commands[7]:
            self._interface.send(gear.RecallMaxLevel(address))
        elif command == commands[8]:
            self._interface.send(gear.RecallMinLevel(address))
        elif command == commands[9]:
            self._interface.send(gear.StepDownAndOff(address))
        elif command == commands[10]:
            self._interface.send(gear.OnAndStepUp(address))
        elif command == commands[11]:
            self._interface.send(gear.EnableDAPCSequence(address))
        elif command == commands[12]:
            self._interface.send(gear.GoToLastActiveLevel(address))
        elif command == commands[13]:
            self._interface.send(gear.ContinuousUp(address))
        elif command == commands[14]:
            self._interface.send(gear.ContinuousDown(address))
        elif command == commands[15]:
            self._interface.send(gear.GoToScene(address, data))
        elif command == commands[16]:
            self._interface.send(gear.Reset(address))
        elif command == commands[17]:
            self._interface.send(gear.StoreActualLevelInDTR0(address))
        elif command == commands[18]:
            self._interface.send(gear.SavePersistentVariables(address))
        elif command == commands[19]:
            self._interface.send(gear.DTR0(data))
            self._interface.send(gear.SetOperatingMode(address))
        elif command == commands[20]:
            self._interface.send(gear.DTR0(data))
            self._interface.send(gear.ResetMemoryBank(address))
        elif command == commands[21]:
            self._interface.send(gear.IdentifyDevice(address))
        elif command == commands[22]:
            self._interface.send(gear.DTR0(data))
            self._interface.send(gear.SetMaxLevel(address))
        elif command == commands[23]:
            self._interface.send(gear.DTR0(data))
            self._interface.send(gear.SetMinLevel(address))
        elif command == commands[24]:
            self._interface.send(gear.DTR0(data))
            self._interface.send(gear.SetSystemFailureLevel(address))
        elif command == commands[25]:
            self._interface.send(gear.DTR0(data))
            self._interface.send(gear.SetPowerOnLevel(address))
        elif command == commands[26]:
            self._interface.send(gear.DTR0(data))
            self._interface.send(gear.SetFadeTime(address))
        elif command == commands[27]:
            self._interface.send(gear.DTR0(data))
            self._interface.send(gear.SetFadeRate(address))
        elif command == commands[28]:
            self._interface.send(gear.DTR0(data))
            self._interface.send(gear.SetExtendedFadeTime(address))
        elif command == commands[29]:
            self._interface.send(gear.DTR0(data2))
            self._interface.send(gear.SetScene(address, data))
        elif command == commands[30]:
            self._interface.send(gear.RemoveFromScene(address, data))
        elif command == commands[31]:
            self._interface.send(gear.AddToGroup(address, data))
        elif command == commands[32]:
            self._interface.send(gear.RemoveFromGroup(address, data))
        elif command == commands[33]:
            self._interface.send(gear.DTR0(data))
            self._interface.send(gear.SetShortAddress(address))
        elif command == commands[34]:
            self._interface.send(gear.EnableWriteMemory(address))
        elif command == commands[35]:
            self._interface.send(gear.QueryStatus(address))