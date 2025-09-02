# -*- coding: utf-8 -*-

from libconfig.IPPHONE.NORMAL.libconfig_IPPHONE_NORMAL import *


class config_R55_NORMAL(config_IPPHONE_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'R55reset.cfg'
        self._autop_cfg_file = '0C1313131304.cfg'
        self._old_firmware_file = 'R55.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'R55'
        self._model_id_NORMAL = '55'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
