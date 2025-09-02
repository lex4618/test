# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.HYPANELLARGE.NORMAL.libconfig_HYPANELLARGE_NORMAL import config_HYPANELLARGE_NORMAL


class config_PG71_NORMAL(config_HYPANELLARGE_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'HyPanel Pro'
        self._rename_cfg_file = 'PG71reset.cfg'
        self._autop_cfg_file = 'r000000000071.cfg'
        self._old_firmware_file = 'PG71.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'PG71'
        self._model_id_NORMAL = '71'

        self._boot_time_after_get_ip = 40
        self._screen_clickable_area = (0, 20, 1280, 800)
        self._screen_width = 1280
        self._screen_height = 800
        self._cur_activity_use_u2 = False
        self._ps_cmd = 'ps -elf'
        