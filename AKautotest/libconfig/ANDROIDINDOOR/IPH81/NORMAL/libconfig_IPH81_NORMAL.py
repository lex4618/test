# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOOR.NORMAL.libconfig_ANDROIDINDOOR_NORMAL import config_ANDROIDINDOOR_NORMAL


class config_IPH81_NORMAL(config_ANDROIDINDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'PH81reset.cfg'
        self._autop_cfg_file = 'r000000000581.cfg'
        self._old_firmware_file = 'PH81.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'IPH81'
        self._model_id_NORMAL = '581'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._boot_time_after_get_ip = 40
        self._screen_size = (2000, 1200)
        self._screen_width = 2000
        self._screen_height = 1200
        self._tln_ssh_port_list = [2043]
        self._tln_or_ssh_pwd = ['I8+R)#ui6T2^t']
        self._web_basic_upgrade_default_time = 1200
