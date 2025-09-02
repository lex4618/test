# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.SMARTPANEL.NORMAL.libconfig_SMARTPANEL_NORMAL import config_SMARTPANEL_NORMAL


class config_X933H_NORMAL(config_SMARTPANEL_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'SmartPanel'
        self._rename_cfg_file = 'X933Hreset.cfg'
        self._autop_cfg_file = 'r000000000933.cfg'
        self._old_firmware_file = 'X933H.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'X933H'
        self._model_id_NORMAL = '933'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._boot_time_after_get_ip = 40
        self._screen_clickable_area = (0, 20, 1280, 800)
        self._screen_width = 1280
        self._screen_height = 800
