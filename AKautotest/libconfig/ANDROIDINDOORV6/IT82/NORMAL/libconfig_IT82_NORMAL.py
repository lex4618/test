# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOORV6.NORMAL.libconfig_ANDROIDINDOORV6_NORMAL import *


class config_IT82_NORMAL(config_ANDROIDINDOORV6_NORMAL):
    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'IT82reset.cfg'
        self._autop_cfg_file = 'r000000000082.cfg'
        self._old_firmware_file = 'IT82.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'IT82'
        self._model_id_NORMAL = '82'
        self._oem = 'NORMAL'
