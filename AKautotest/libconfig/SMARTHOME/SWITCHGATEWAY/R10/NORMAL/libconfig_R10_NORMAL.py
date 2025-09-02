# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.SWITCHGATEWAY.NORMAL.libconfig_SWITCHGATEWAY_NORMAL import config_SWITCHGATEWAY_NORMAL


class config_R10_NORMAL(config_SWITCHGATEWAY_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'Gateway'
        self._rename_cfg_file = 'R10reset.cfg'
        self._autop_cfg_file = 'r000000000010.cfg'
        self._old_firmware_file = 'R10.tar'
        self._firmware_ext = '.tar'
        self._firmware_prefix = 'ota_v'
        self._model_name = 'R10'
        self._model_id_NORMAL = '10'
        self._oem = 'NORMAL'
        self._remote_connect_type = None
