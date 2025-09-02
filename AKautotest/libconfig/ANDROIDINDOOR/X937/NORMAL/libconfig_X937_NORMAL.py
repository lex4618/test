# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOOR.NORMAL.libconfig_ANDROIDINDOOR_NORMAL import config_ANDROIDINDOOR_NORMAL


class config_X937_NORMAL(config_ANDROIDINDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'X937reset.cfg'
        self._autop_cfg_file = 'r000000000933.cfg'
        self._old_firmware_file = 'X937.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'X937'
        self._model_id_NORMAL = '937'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._boot_time_after_get_ip = 40
        self._screen_size = (1280, 800)
        self._screen_width = 1280
        self._screen_height = 800
        self._tln_ssh_port_list = [2043]
        self._tln_or_ssh_pwd = ['I8+R)#ui6T2^t']
        self._doorbell_event = 'sendevent /dev/input/event1 1 28 1;sendevent /dev/input/event1 1 28 0;sendevent /dev/input/event1 0 0 0'
        self._web_basic_upgrade_default_time = 1200
