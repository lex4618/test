# -*- coding: utf-8 -*-

from libconfig.LINUXDOOR.NORMAL.libconfig_LINUXDOOR_NORMAL import *


class config_S535_NORMAL(config_LINUXDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'S535_V2reset.cfg'
        self._autop_cfg_file = 'r0000000000535.cfg'
        self._old_firmware_file = 'S535.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'S535'
        self._model_id_NORMAL = '535'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
