# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.NORMAL.libconfig_LINUXINDOOR_NORMAL import *


class config_C313_V3_NORMAL(config_LINUXINDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'C313_V3reset.cfg'
        self._autop_cfg_file = 'r000000000313.cfg'
        self._old_firmware_file = 'C313_V3.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'C313_V3'
        self._model_id_NORMAL = '313'
        self._oem = 'NORMAL'
