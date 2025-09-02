# -*- coding: utf-8 -*-

from libconfig.ANDROIDDOOR.NORMAL.libconfig_ANDROIDDOOR_NORMAL import *


class config_S539_NORMAL(config_ANDROIDDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'S539reset.cfg'
        self._autop_cfg_file = 'r000000000539.cfg'
        self._old_firmware_file = 'S539.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'S539'
        self._model_id_NORMAL = '539'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._platform_version = '12'
