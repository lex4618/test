# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.NORMAL.libconfig_LINUXINDOOR_NORMAL import *


class config_S562_NORMAL(config_LINUXINDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'S562reset.cfg'
        self._autop_cfg_file = 'r000000000562.cfg'
        self._old_firmware_file = 'S562.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'S562'
        self._model_id_NORMAL = '562'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
        self._boot_time_after_get_ip = 40
        self._screen_size = (1280, 800)
        self._screen_width = 1280
        self._screen_height = 800
        self._tln_ssh_port_list = [23]
        self._tln_or_ssh_pwd = ['I8+R)#ui6T2^t']
