# -*- coding: utf-8 -*-

from libconfig.ACCESSCONTROL.NORMAL.libconfig_ACCESSCONTROL_NORMAL import config_ACCESSCONTROL_NORMAL


class config_ZIGBEETOOL_NORMAL(config_ACCESSCONTROL_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'EC33reset.cfg'
        self._autop_cfg_file = 'r000000000033.cfg'
        self._old_firmware_file = 'EC33.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'ZIGBEETOOL'
        self._model_id_NORMAL = '33'
        self._oem = 'NORMAL'

        # 系列配置项
        self._tln_or_ssh_pwd = 'yA@9^b8Zq-T+s'
