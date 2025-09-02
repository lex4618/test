# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.HYPANELLARGE.NORMAL.libconfig_HYPANELLARGE_NORMAL import config_HYPANELLARGE_NORMAL


class config_PH59_NORMAL(config_HYPANELLARGE_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'HyPanel Ultra'
        self._rename_cfg_file = 'PH59reset.cfg'
        self._autop_cfg_file = 'r000000000259.cfg'
        self._old_firmware_file = 'PH59.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'PH59'
        self._model_id_NORMAL = '259'

        self._boot_time_after_get_ip = 40
        self._screen_clickable_area = (0, 20, 1280, 800)
        self._screen_width = 1280
        self._screen_height = 800
        self._ps_cmd = 'ps'
        self._cur_activity_use_u2 = True
        self._screen_power_flag = 'mWakefulness='
        self._screen_power_use_u2 = False

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
