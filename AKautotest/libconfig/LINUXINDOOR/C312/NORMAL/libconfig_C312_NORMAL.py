# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.NORMAL.libconfig_LINUXINDOOR_NORMAL import *


class config_C312_NORMAL(config_LINUXINDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'C312reset.cfg'
        self._autop_cfg_file = 'r000000000112.cfg'
        self._old_firmware_file = 'C312.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'C312'
        self._model_id_NORMAL = '112'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._tln_ssh_port_list = [22]
        self._selftestdassistant_path = r'\tools\SelftestdAssistant_1.0.0.12\SelftestdAssistant.exe'
