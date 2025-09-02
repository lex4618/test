# -*- coding: utf-8 -*-

from libconfig.LINUXDOOR.NORMAL.libconfig_LINUXDOOR_NORMAL import *


class config_R20K_NORMAL(config_LINUXDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'R20Kreset.cfg'
        self._autop_cfg_file = 'r000000000020.cfg'
        self._old_firmware_file = 'R20K.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'R20K'
        self._model_id_NORMAL = '20'
        self._oem = 'NORMAL'
