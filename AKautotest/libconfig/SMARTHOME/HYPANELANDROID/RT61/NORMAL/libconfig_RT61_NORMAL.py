# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.HYPANELANDROID.NORMAL.libconfig_HYPANELANDROID_NORMAL import config_HYPANELANDROID_NORMAL


class config_RT61_NORMAL(config_HYPANELANDROID_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'HyPanel Lux'
        self._rename_cfg_file = 'RT61reset.cfg'
        self._autop_cfg_file = 'r000000000061.cfg'
        self._old_firmware_file = 'RT61.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'RT61'
        self._model_id_NORMAL = '61'
        self._oem = 'NORMAL'
        self._boot_time_after_get_ip = 40
        self._screen_width = 480
        self._screen_height = 480
        self._cur_activity_use_u2 = False
        self._ps_cmd = 'ps -elf'
