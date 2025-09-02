# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOORV6.NORMAL.libconfig_ANDROIDINDOORV6_NORMAL import *


class config_C317_NORMAL(config_ANDROIDINDOORV6_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'C317reset.cfg'
        self._autop_cfg_file = 'r000000000317.cfg'
        self._old_firmware_file = 'C317.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'C317'
        self._model_id_NORMAL = '117'
        self._oem = 'NORMAL'
        self._screen_size = (1280, 800)
        self._system_bar_rect = (0, 0, 1280, 46)
