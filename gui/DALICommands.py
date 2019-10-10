import dali.gear.general as gear

commands = ('',
            'DIRECT_ARC_POWER_CONTROL',
            'OFF',
            'UP',
            'DOWN',
            'STEP_UP',
            'STEP_DOWN',
            'RECALL_MAX_LEVEL',
            'RECALL_MIN_LEVEL',
            'STEP_DOWN_AND_OFF',
            'ON_AND_STEP_UP',
            'ENABLE_DAPC_SEQUENCE',
            'RESERVED_10',
            'RESERVED_11',
            'RESERVED_12',
            'RESERVED_13',
            'RESERVED_14',
            'RESERVED_15',
            'GO_TO_SCENE_0',
            'GO_TO_SCENE_1',
            'GO_TO_SCENE_2',
            'GO_TO_SCENE_3',
            'GO_TO_SCENE_4',
            'GO_TO_SCENE_5',
            'GO_TO_SCENE_6',
            'GO_TO_SCENE_7',
            'GO_TO_SCENE_8',
            'GO_TO_SCENE_9',
            'GO_TO_SCENE_10',
            'GO_TO_SCENE_11',
            'GO_TO_SCENE_12',
            'GO_TO_SCENE_13',
            'GO_TO_SCENE_14',
            'GO_TO_SCENE_15',                                                                                            
            'RESET',
            'STORE_ACTUAL_LEVEL_IN_THE_DTR',
            'RESERVED_34',
            'RESERVED_35',
            'RESERVED_36',
            'RESERVED_37',
            'RESERVED_38',
            'RESERVED_39',
            'RESERVED_40',
            'RESERVED_41',
            'STORE_THE_DTR_AS_MAX_LEVEL',
            'STORE_THE_DTR_AS_MIN_LEVEL',
            'STORE_THE_DTR_AS_SYSTEM_FAILURE_LEVEL',
            'STORE_THE_DTR_AS_POWER_ON_LEVEL',
            'STORE_THE_DTR_AS_FADE_TIME',
            'STORE_THE_DTR_AS_FADE_RATE',
            'RESERVED_48',
            'RESERVED_49',
            'RESERVED_50',
            'RESERVED_51',
            'RESERVED_52',
            'RESERVED_53',
            'RESERVED_54',
            'RESERVED_55',
            'RESERVED_56',
            'RESERVED_57',
            'RESERVED_58',
            'RESERVED_59',
            'RESERVED_60',
            'RESERVED_61',
            'RESERVED_62',
            'RESERVED_63',
            'STORE_THE_DTR_AS_SCENE_0',
            'STORE_THE_DTR_AS_SCENE_1',
            'STORE_THE_DTR_AS_SCENE_2',
            'STORE_THE_DTR_AS_SCENE_3',
            'STORE_THE_DTR_AS_SCENE_4',
            'STORE_THE_DTR_AS_SCENE_5',
            'STORE_THE_DTR_AS_SCENE_6',
            'STORE_THE_DTR_AS_SCENE_7',
            'STORE_THE_DTR_AS_SCENE_8',
            'STORE_THE_DTR_AS_SCENE_9',
            'STORE_THE_DTR_AS_SCENE_10',
            'STORE_THE_DTR_AS_SCENE_11',
            'STORE_THE_DTR_AS_SCENE_12',
            'STORE_THE_DTR_AS_SCENE_13',
            'STORE_THE_DTR_AS_SCENE_14',
            'STORE_THE_DTR_AS_SCENE_15',
            'REMOVE_FROM_SCENE_0',
            'REMOVE_FROM_SCENE_1',
            'REMOVE_FROM_SCENE_2',
            'REMOVE_FROM_SCENE_3',
            'REMOVE_FROM_SCENE_4',
            'REMOVE_FROM_SCENE_5',
            'REMOVE_FROM_SCENE_6',
            'REMOVE_FROM_SCENE_7',
            'REMOVE_FROM_SCENE_8',
            'REMOVE_FROM_SCENE_9',
            'REMOVE_FROM_SCENE_10',
            'REMOVE_FROM_SCENE_11',
            'REMOVE_FROM_SCENE_12',
            'REMOVE_FROM_SCENE_13',
            'REMOVE_FROM_SCENE_14',
            'REMOVE_FROM_SCENE_15',
            'ADD_TO_GROUP_0',
            'ADD_TO_GROUP_1',
            'ADD_TO_GROUP_2',
            'ADD_TO_GROUP_3',
            'ADD_TO_GROUP_4',
            'ADD_TO_GROUP_5',
            'ADD_TO_GROUP_6',
            'ADD_TO_GROUP_7',
            'ADD_TO_GROUP_8',
            'ADD_TO_GROUP_9',
            'ADD_TO_GROUP_10',
            'ADD_TO_GROUP_11',
            'ADD_TO_GROUP_12',
            'ADD_TO_GROUP_13',
            'ADD_TO_GROUP_14',
            'ADD_TO_GROUP_15',
            'REMOVE_FROM_GROUP_0',
            'REMOVE_FROM_GROUP_1',
            'REMOVE_FROM_GROUP_2',
            'REMOVE_FROM_GROUP_3',
            'REMOVE_FROM_GROUP_4',
            'REMOVE_FROM_GROUP_5',
            'REMOVE_FROM_GROUP_6',
            'REMOVE_FROM_GROUP_7',
            'REMOVE_FROM_GROUP_8',
            'REMOVE_FROM_GROUP_9',
            'REMOVE_FROM_GROUP_10',
            'REMOVE_FROM_GROUP_11',
            'REMOVE_FROM_GROUP_12',
            'REMOVE_FROM_GROUP_13',
            'REMOVE_FROM_GROUP_14',
            'REMOVE_FROM_GROUP_15',
            'STORE_DTR_AS_SHORT_ADDRESS',
            'ENABLE_WRITE_MEMORY',
            'RESERVED_130',
            'RESERVED_131',
            'RESERVED_132',
            'RESERVED_133',
            'RESERVED_134',
            'RESERVED_135',
            'RESERVED_136',
            'RESERVED_137',
            'RESERVED_138',
            'RESERVED_139',
            'RESERVED_140',
            'RESERVED_141',
            'RESERVED_142',
            'RESERVED_143',
            'QUERY_STATUS',
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

    #def __init__(self):

    def commandHandler(self, command, address, byte1, byte2, send):
        '''Command codes output and sending is handled in the same function to prevent writing everything twice.
        '''
        if command == 'DIRECT_ARC_POWER_CONTROL':
            if send == 1:
                print('sending...')
            else:
                return address, byte2, 'Short address:', 'Power:'

        elif command == 'OFF':
            if send == 1:
                print('sending...')
            else:
                command = gear.Off(address)
                return command.frame.as_byte_sequence

        elif command == 'UP':
            if send == 1:
                print('sending...')
            else:
                command = gear.Up(address)
                return command.frame.as_byte_sequence
