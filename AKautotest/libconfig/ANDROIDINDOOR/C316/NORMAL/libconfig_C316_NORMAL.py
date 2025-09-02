# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOOR.NORMAL.libconfig_ANDROIDINDOOR_NORMAL import config_ANDROIDINDOOR_NORMAL


class config_C316_NORMAL(config_ANDROIDINDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'C316reset.cfg'
        self._autop_cfg_file = 'r000000000316.cfg'
        self._old_firmware_file = 'C316.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'C316'
        self._model_id_NORMAL = '316'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._boot_time_after_get_ip = 40
        self._screen_size = (1024, 600)
        self._screen_width = 1024
        self._screen_height = 600
        self._screen_saver_flag = 'dreaming'
