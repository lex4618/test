# -*- coding: utf-8 -*-

from libconfig.ACCESSCONTROL.NORMAL.libconfig_ACCESSCONTROL_NORMAL import config_ACCESSCONTROL_NORMAL


class config_A08_NORMAL(config_ACCESSCONTROL_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'A08reset.cfg'
        self._autop_cfg_file = 'r000000000108.cfg'
        self._old_firmware_file = 'A08.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'A08'
        self._model_id_NORMAL = '108'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._tln_ssh_port_list = 22
        self._web_basic_upgrade_default_time = 200

        # 系列配置项
        self._tln_or_ssh_pwd = 'yA@9^b8Zq-T+s'
