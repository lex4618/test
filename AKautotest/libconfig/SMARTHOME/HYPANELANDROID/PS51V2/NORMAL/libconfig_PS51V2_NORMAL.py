# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.HYPANELANDROID.NORMAL.libconfig_HYPANELANDROID_NORMAL import *


class config_PS51V2_NORMAL(config_HYPANELANDROID_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'PS51V2reset.cfg'
        self._autop_cfg_file = 'r000000000251.cfg'
        self._old_firmware_file = 'PS51V2.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'PS51V2'
        self._model_id_NORMAL = '251'
        self._oem = 'NORMAL'
        self._boot_time_after_get_ip = 40
        self._screen_clickable_area = (25, 20, 455, 460)
        self._screen_width = 480
        self._screen_height = 480
        self._ps_cmd = 'ps'

    def get_location_send_event(self, x, y):
        location_send_event = ['sendevent /dev/input/event1 0003 0057 00000001',
                               'sendevent /dev/input/event1 0003 0053 %08d' % (self._screen_width - x - 1),
                               'sendevent /dev/input/event1 0003 0054 %08d' % (self._screen_height - y - 1),
                               'sendevent /dev/input/event1 0001 0330 00000001',
                               'sendevent /dev/input/event1 0000 0000 00000000',
                               'sendevent /dev/input/event1 0003 0057 ffffffff',
                               'sendevent /dev/input/event1 0001 0330 00000000',
                               'sendevent /dev/input/event1 0000 0000 00000000']
        return location_send_event
