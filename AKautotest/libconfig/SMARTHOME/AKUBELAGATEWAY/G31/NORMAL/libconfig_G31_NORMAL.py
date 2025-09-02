# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.AKUBELAGATEWAY.NORMAL.libconfig_AKUBELAGATEWAY_NORMAL import config_AKUBELAGATEWAY_NORMAL


class config_G31_NORMAL(config_AKUBELAGATEWAY_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'Gateway'
        self._rename_cfg_file = 'G31reset.cfg'
        self._autop_cfg_file = 'r000000000031.cfg'
        self._old_firmware_file = 'G31.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'G31'
        self._model_id_NORMAL = '31'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
