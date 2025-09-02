# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.NORMAL.libconfig_LINUXINDOOR_NORMAL import *


class config_C313_HAGER(config_LINUXINDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'C313reset.cfg'
        self._autop_cfg_file = 'r000000000113.cfg'
        self._old_firmware_file = 'C313.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'C313'
        self._model_id_NORMAL = '113'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
        self._tln_ssh_port_list = [23]
        self._tln_or_ssh_pwd = 'Yhg#Z^q@78u'

