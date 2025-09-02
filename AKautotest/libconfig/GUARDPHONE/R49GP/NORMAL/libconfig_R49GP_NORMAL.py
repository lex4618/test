# -*- coding: utf-8 -*-

from libconfig.GUARDPHONE.NORMAL.libconfig_GUARDPHONE_NORMAL import *


class config_R49GP_NORMAL(config_GUARDPHONE_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'R49GPreset.cfg'
        self._autop_cfg_file = 'r000000000049.cfg'
        self._old_firmware_file = 'R49GP.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'R49GP'
        self._model_id_NORMAL = '49'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._tln_or_ssh_pwd = ['I8+R)#ui6T2^t']
        self._remote_connect_type = 'ssh'
        self._tln_ssh_port_list = [22, 2043]

        # 工程模式相关
        self._factory_screen_img_path = r'\IMG_compare\GUARDPHONE\R49GP\NORMAL\factory_test_lcd'

        # key event相关
        self._key_send_event_commands = {
            'key_num_1': ['sendevent /dev/input/event0 0004 0004 00000003',
                          'sendevent /dev/input/event0 0001 0002 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 00000003',
                          'sendevent /dev/input/event0 0001 0002 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_2': ['sendevent /dev/input/event0 0004 0004 00000010',
                          'sendevent /dev/input/event0 0001 0003 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 00000010',
                          'sendevent /dev/input/event0 0001 0003 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_3': ['sendevent /dev/input/event0 0004 0004 00000011',
                          'sendevent /dev/input/event0 0001 0004 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 00000011',
                          'sendevent /dev/input/event0 0001 0004 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_4': ['sendevent /dev/input/event0 0004 0004 00000004',
                          'sendevent /dev/input/event0 0001 0005 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 00000004',
                          'sendevent /dev/input/event0 0001 0005 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_5': ['sendevent /dev/input/event0 0004 0004 0000000a',
                          'sendevent /dev/input/event0 0001 0006 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 0000000a',
                          'sendevent /dev/input/event0 0001 0006 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_6': ['sendevent /dev/input/event0 0004 0004 00000012',
                          'sendevent /dev/input/event0 0001 0007 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 00000012',
                          'sendevent /dev/input/event0 0001 0007 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_7': ['sendevent /dev/input/event0 0004 0004 00000008',
                          'sendevent /dev/input/event0 0001 0008 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 00000008',
                          'sendevent /dev/input/event0 0001 0008 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_8': ['sendevent /dev/input/event0 0004 0004 0000000b',
                          'sendevent /dev/input/event0 0001 0009 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 0000000b',
                          'sendevent /dev/input/event0 0001 0009 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_9': ['sendevent /dev/input/event0 0004 0004 00000013',
                          'sendevent /dev/input/event0 0001 000a 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 00000013',
                          'sendevent /dev/input/event0 0001 000a 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_0': ['sendevent /dev/input/event0 0004 0004 0000000c',
                          'sendevent /dev/input/event0 0001 000b 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 0000000c',
                          'sendevent /dev/input/event0 0001 000b 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_*': ['sendevent /dev/input/event0 0004 0004 00000009',
                          'sendevent /dev/input/event0 0001 00e3 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 00000009',
                          'sendevent /dev/input/event0 0001 00e3 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_num_#': ['sendevent /dev/input/event0 0004 0004 00000014',
                          'sendevent /dev/input/event0 0001 00e4 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 00000014',
                          'sendevent /dev/input/event0 0001 00e4 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_vol+': ['sendevent /dev/input/event0 0004 0004 00000001',
                         'sendevent /dev/input/event0 0001 0073 00000001',
                         'sendevent /dev/input/event0 0000 0000 00000000',
                         'sendevent /dev/input/event0 0004 0004 00000001',
                         'sendevent /dev/input/event0 0001 0073 00000000',
                         'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_vol-': ['sendevent /dev/input/event0 0004 0004 00000002',
                         'sendevent /dev/input/event0 0001 0072 00000001',
                         'sendevent /dev/input/event0 0000 0000 00000000',
                         'sendevent /dev/input/event0 0004 0004 00000002',
                         'sendevent /dev/input/event0 0001 0072 00000000',
                         'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_hook_up': ['sendevent /dev/input/event3 0001 00b9 00000001',
                            'sendevent /dev/input/event3 0000 0000 00000000'],
            'key_hook_down': ['sendevent /dev/input/event3 0001 00b9 00000000',
                              'sendevent /dev/input/event3 0000 0000 00000000'],
            'key_headset': ['sendevent /dev/input/event0 0004 0004 0000001a',
                            'sendevent /dev/input/event0 0001 003c 00000001',
                            'sendevent /dev/input/event0 0000 0000 00000000',
                            'sendevent /dev/input/event0 0004 0004 0000001a',
                            'sendevent /dev/input/event0 0001 003c 00000000',
                            'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_msg': ['sendevent /dev/input/event4 0001 0074 00000001',
                        'sendevent /dev/input/event4 0000 0000 00000000',
                        'sendevent /dev/input/event4 0001 0074 00000000',
                        'sendevent /dev/input/event4 0000 0000 00000000'],
            'key_conf': ['sendevent /dev/input/event0 0004 0004 00000019',
                         'sendevent /dev/input/event0 0001 003b 00000001',
                         'sendevent /dev/input/event0 0000 0000 00000000',
                         'sendevent /dev/input/event0 0004 0004 00000019',
                         'sendevent /dev/input/event0 0001 003b 00000000',
                         'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_trans': ['sendevent /dev/input/event0 0004 0004 0000001c',
                          'sendevent /dev/input/event0 0001 003e 00000001',
                          'sendevent /dev/input/event0 0000 0000 00000000',
                          'sendevent /dev/input/event0 0004 0004 0000001c',
                          'sendevent /dev/input/event0 0001 003e 00000000',
                          'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_book': ['sendevent /dev/input/event0 0004 0004 00000023',
                         'sendevent /dev/input/event0 0001 008b 00000001',
                         'sendevent /dev/input/event0 0000 0000 00000000',
                         'sendevent /dev/input/event0 0004 0004 00000023',
                         'sendevent /dev/input/event0 0001 008b 00000000',
                         'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_mute': ['sendevent /dev/input/event0 0004 0004 00000024',
                         'sendevent /dev/input/event0 0001 0071 00000001',
                         'sendevent /dev/input/event0 0000 0000 00000000',
                         'sendevent /dev/input/event0 0004 0004 00000024',
                         'sendevent /dev/input/event0 0001 0071 00000000',
                         'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_back': ['sendevent /dev/input/event0 0004 0004 00000021',
                         'sendevent /dev/input/event0 0001 009e 00000001',
                         'sendevent /dev/input/event0 0000 0000 00000000',
                         'sendevent /dev/input/event0 0004 0004 00000021',
                         'sendevent /dev/input/event0 0001 009e 00000000',
                         'sendevent /dev/input/event0 0000 0000 00000000'],
            'key_handfree': ['sendevent /dev/input/event0 0004 0004 00000022',
                             'sendevent /dev/input/event0 0001 00b8 00000001',
                             'sendevent /dev/input/event0 0000 0000 00000000',
                             'sendevent /dev/input/event0 0004 0004 00000022',
                             'sendevent /dev/input/event0 0001 00b8 00000000',
                             'sendevent /dev/input/event0 0000 0000 00000000'],
        }

    def get_factory_screen_img_path(self):
        path = self._test_file_root_path + self._factory_screen_img_path
        return path

    def get_key_send_event_commands(self):
        return self._key_send_event_commands
