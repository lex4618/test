# -*- coding: utf-8 -*-

from libconfig.IPPHONE.NORMAL.libconfig_IPPHONE_NORMAL import *


class config_R59_NORMAL(config_IPPHONE_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'R59reset.cfg'
        self._autop_cfg_file = '0CAEAC654321.cfg'
        self._old_firmware_file = 'R59.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'R59'
        self._model_id_NORMAL = '59'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
