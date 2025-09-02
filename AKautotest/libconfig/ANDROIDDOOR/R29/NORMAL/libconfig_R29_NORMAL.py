# -*- coding: utf-8 -*-

from libconfig.ANDROIDDOOR.NORMAL.libconfig_ANDROIDDOOR_NORMAL import *


class config_R29_NORMAL(config_ANDROIDDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'R29reset.cfg'
        self._autop_cfg_file = 'r000000000029.cfg'
        self._old_firmware_file = 'R29.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'R29'
        self._model_id_NORMAL = '29'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._platform_version = '5.1.1'
        self._appium_command = 'appium1.22.3'
