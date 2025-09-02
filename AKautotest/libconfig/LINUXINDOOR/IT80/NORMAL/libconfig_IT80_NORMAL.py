# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.NORMAL.libconfig_LINUXINDOOR_NORMAL import *


class config_IT80_NORMAL(config_LINUXINDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'IT80reset.cfg'
        self._autop_cfg_file = 'r000000000080.cfg'
        self._old_firmware_file = 'IT80.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'IT80'
        self._model_id_NORMAL = '80'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
