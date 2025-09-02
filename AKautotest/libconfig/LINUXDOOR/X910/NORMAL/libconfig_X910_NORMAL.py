# -*- coding: utf-8 -*-

from libconfig.LINUXDOOR.NORMAL.libconfig_LINUXDOOR_NORMAL import *


class config_X910_NORMAL(config_LINUXDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'X910_V2reset.cfg'
        self._autop_cfg_file = 'r00000000002910.cfg'
        self._old_firmware_file = 'X910.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'X910'
        self._model_id_NORMAL = '2910'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
