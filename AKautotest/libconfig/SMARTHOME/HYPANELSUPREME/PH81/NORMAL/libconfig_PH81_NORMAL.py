# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.HYPANELSUPREME.NORMAL.libconfig_HYPANELSUPREME_NORMAL import *


class config_PH81_NORMAL(config_HYPANELSUPREME_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'HyPanel Ultra'
        self._rename_cfg_file = 'PH81reset.cfg'
        self._autop_cfg_file = 'r000000000281.cfg'
        self._old_firmware_file = 'PH81.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'PH81'
        self._model_id_NORMAL = '281'
        self._oem = 'NORMAL'
        self._boot_time_after_get_ip = 40
        self._screen_clickable_area = (25, 20, 2000, 1200)
        self._screen_width = 2000
        self._screen_height = 1200

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
