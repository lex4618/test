# -*- coding: utf-8 -*-

from libconfig.LINUXDOOR.NORMAL.libconfig_LINUXDOOR_NORMAL import *


class config_E11_NORMAL(config_LINUXDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'E11reset.cfg'
        self._autop_cfg_file = 'r000000000011.cfg'
        self._old_firmware_file = 'E11.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'E11'
        self._model_id_NORMAL = '111'
        self._oem = 'NORMAL'
