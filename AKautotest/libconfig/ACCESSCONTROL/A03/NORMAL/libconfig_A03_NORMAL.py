# -*- coding: utf-8 -*-

from libconfig.ACCESSCONTROL.NORMAL.libconfig_ACCESSCONTROL_NORMAL import config_ACCESSCONTROL_NORMAL


class config_A03_NORMAL(config_ACCESSCONTROL_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'A03reset.cfg'
        self._autop_cfg_file = 'r000000000103.cfg'
        self._old_firmware_file = 'A03.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'A03'
        self._model_id_NORMAL = '103'
        self._oem = 'NORMAL'

        # 系列配置项
        self._tln_or_ssh_pwd = 'yA@9^b8Zq-T+s'