# -*- coding: utf-8 -*-

from libconfig.IPPHONE.NORMAL.libconfig_IPPHONE_NORMAL import *


class config_R53_NORMAL(config_IPPHONE_NORMAL):
    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'R53reset.cfg'
        self._autop_cfg_file = '0C11020A0B16.cfg'
        self._old_firmware_file = 'R53.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'R53'
        self._model_id_NORMAL = '53'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
