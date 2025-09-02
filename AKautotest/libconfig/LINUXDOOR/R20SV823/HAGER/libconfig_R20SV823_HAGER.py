# -*- coding: utf-8 -*-

from libconfig.LINUXDOOR.R20SV823.NORMAL.libconfig_R20SV823_NORMAL import *


class config_R20SV823_HAGER(config_R20SV823_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'R20SV823reset.cfg'
        self._autop_cfg_file = 'r000000000020P.cfg'
        self._old_firmware_file = 'R20SV823.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'R20SV823'
        self._model_id_NORMAL = '320'
        self._oem = 'HAGER'
        self._remote_connect_type = 'ssh'
        self._tln_or_ssh_pwd = 'Yhg#Z^q@78u'
