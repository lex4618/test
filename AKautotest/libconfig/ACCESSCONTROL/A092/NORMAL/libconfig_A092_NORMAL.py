# -*- coding: utf-8 -*-

from libconfig.ACCESSCONTROL.NORMAL.libconfig_ACCESSCONTROL_NORMAL import config_ACCESSCONTROL_NORMAL


class config_A092_NORMAL(config_ACCESSCONTROL_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'A092reset.cfg'
        self._autop_cfg_file = 'r000000000092.cfg'
        self._old_firmware_file = 'A092.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'A092'
        self._model_id_NORMAL = '92'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
