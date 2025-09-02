# -*- coding: utf-8 -*-

from libconfig.ACCESSCONTROL.NORMAL.libconfig_ACCESSCONTROL_NORMAL import config_ACCESSCONTROL_NORMAL


class config_A01_NORMAL(config_ACCESSCONTROL_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'A01reset.cfg'
        self._autop_cfg_file = 'r000000000101.cfg'
        self._old_firmware_file = 'A01.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'A01'
        self._model_id_NORMAL = '101'
        self._oem = 'NORMAL'

        # 系列配置项
        self._tln_or_ssh_pwd = 'yA@9^b8Zq-T+s'
