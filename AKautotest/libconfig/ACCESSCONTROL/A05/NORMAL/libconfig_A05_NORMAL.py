# -*- coding: utf-8 -*-

from libconfig.ACCESSCONTROL.NORMAL.libconfig_ACCESSCONTROL_NORMAL import config_ACCESSCONTROL_NORMAL


class config_A05_NORMAL(config_ACCESSCONTROL_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'A05reset.cfg'
        self._autop_cfg_file = 'r000000000105.cfg'
        self._old_firmware_file = 'A05.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'A05'
        self._model_id_NORMAL = '105'
        self._oem = 'NORMAL'
        self._web_basic_upgrade_default_time = 200 # A05比其他门禁机型下载包时间长
        self._remote_connect_type = 'ssh'
