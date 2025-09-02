# -*- coding: utf-8 -*-

from libconfig.ACCESSCONTROL.NORMAL.libconfig_ACCESSCONTROL_NORMAL import config_ACCESSCONTROL_NORMAL


class config_A094_NORMAL(config_ACCESSCONTROL_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'A094reset.cfg'
        self._autop_cfg_file = 'r000000000092.cfg'
        self._old_firmware_file = 'A094.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'A094'
        self._model_id_NORMAL = '92'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
