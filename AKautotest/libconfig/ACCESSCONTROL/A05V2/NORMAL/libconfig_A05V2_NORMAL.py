# -*- coding: utf-8 -*-

from libconfig.ACCESSCONTROL.NORMAL.libconfig_ACCESSCONTROL_NORMAL import config_ACCESSCONTROL_NORMAL


class config_A05V2_NORMAL(config_ACCESSCONTROL_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'A05V2reset.cfg'
        self._autop_cfg_file = 'r000000000205.cfg'
        self._old_firmware_file = 'A05V2.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'A05V2'
        self._model_id_NORMAL = '205'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._tln_or_ssh_pwd = ['yA@9^b8Zq-T+s']
        self._web_basic_upgrade_default_time = 300
        self._tln_ssh_port_list = 22
        self.check_ps_list = [
            '/app/bin/dclient',
            '/app/bin/phone',
            '/app/bin/ispserver'
        ]
