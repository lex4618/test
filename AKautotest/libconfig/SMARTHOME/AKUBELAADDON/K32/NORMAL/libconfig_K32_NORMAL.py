# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.AKUBELAADDON.NORMAL.libconfig_AKUBELAADDON_NORMAL import config_AKUBELAADDON_NORMAL


class config_K32_NORMAL(config_AKUBELAADDON_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'K32'
        self._rename_cfg_file = 'K32reset.cfg'
        self._autop_cfg_file = 'r000000000032.cfg'
        self._old_firmware_file = 'K32'
        self._firmware_ext = ''
        self._model_name = 'K32'
        self._model_id_NORMAL = 'K32'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
