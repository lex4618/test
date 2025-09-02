# -*- coding: utf-8 -*-

from libconfig.LINUXDOOR.NORMAL.libconfig_LINUXDOOR_NORMAL import *


class config_R27_V2_NORMAL(config_LINUXDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'R27_V2reset.cfg'
        self._autop_cfg_file = 'r000000000027P.cfg'
        self._old_firmware_file = 'R27_V2.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'R27_V2'
        self._model_id_NORMAL = '227'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
