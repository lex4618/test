# -*- coding: utf-8 -*-

from libconfig.IPPHONE.NORMAL.libconfig_IPPHONE_NORMAL import *


class config_AUSTCO_NORMAL(config_IPPHONE_NORMAL):
    def __init__(self, device_name=''):
        super().__init__(device_name)
        # 设备端默认IP设置
        self._lan_port_type = 'static'
        self._lan_port_ip_address = '10.255.255.10'

        # Autop配置文件相关
        self._rename_cfg_file = 'AUSTCOreset.cfg'
        self._autop_cfg_file = 'r000000000002.cfg'
        self._old_firmware_file = 'AUSTCO.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'AUSTCO'
        self._model_id_NORMAL = '2'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
