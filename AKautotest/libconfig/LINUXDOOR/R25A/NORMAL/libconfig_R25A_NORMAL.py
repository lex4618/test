# -*- coding: utf-8 -*-

from libconfig.LINUXDOOR.NORMAL.libconfig_LINUXDOOR_NORMAL import *


class config_R25A_NORMAL(config_LINUXDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'R25A_V2reset.cfg'
        self._autop_cfg_file = 'r000000000025P.cfg'
        self._old_firmware_file = 'R25A.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'R25A'
        self._model_id_NORMAL = '25'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'