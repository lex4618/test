# -*- coding: utf-8 -*-

from libconfig.ACCESSDOOR.NORMAL.libconfig_ACCESSDOOR_NORMAL import config_ACCESSDOOR_NORMAL


class config_E20_NORMAL(config_ACCESSDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'E20reset.cfg'
        self._autop_cfg_file = 'r000000000120.cfg'
        self._old_firmware_file = 'E20.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'E20'
        self._model_id_NORMAL = '120'
        self._oem = 'NORMAL'
        self._reboot_default_time = 90
        self._web_basic_upgrade_default_time = 130
