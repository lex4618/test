# -*- coding: utf-8 -*-

from libconfig.IPPHONE.NORMAL.libconfig_IPPHONE_NORMAL import *


class config_R67_NORMAL(config_IPPHONE_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'R67reset.cfg'
        self._autop_cfg_file = '0C11050B040A.cfg'
        self._old_firmware_file = 'R67.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'R67'
        self._model_id_NORMAL = '67'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
