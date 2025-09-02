# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.AKUBELALOCK.NORMAL.libconfig_AKUBELALOCK_NORMAL import config_AKUBELALOCK_NORMAL


class config_SL20_NORMAL(config_AKUBELALOCK_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'SL20'
        self._rename_cfg_file = 'SL20reset.cfg'
        self._autop_cfg_file = 'r000000000220.cfg'
        self._old_firmware_file = 'SL20'
        self._firmware_ext = ''
        self._model_name = 'SL20'
        self._model_id_NORMAL = '220'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
