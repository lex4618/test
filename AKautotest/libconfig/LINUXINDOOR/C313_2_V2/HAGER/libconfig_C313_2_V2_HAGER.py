# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.C313_2_V2.NORMAL.libconfig_C313_2_V2_NORMAL import config_C313_2_V2_NORMAL


class config_C313_2_V2_HAGER(config_C313_2_V2_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'C313_2_V2reset.cfg'
        self._autop_cfg_file = 'r000000000212.cfg'
        self._old_firmware_file = 'C313_2_V2.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'C313_2_V2'
        self._model_id_NORMAL = '212'
        self._oem = 'HAGER'
        self._remote_connect_type = 'telnet'
        self._tln_ssh_port_list = [23]
        self._tln_or_ssh_pwd = ['Yhg#Z^q@78u']
