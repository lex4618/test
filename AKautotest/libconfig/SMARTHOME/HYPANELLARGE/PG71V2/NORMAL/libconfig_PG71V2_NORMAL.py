# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.HYPANELLARGE.NORMAL.libconfig_HYPANELLARGE_NORMAL import config_HYPANELLARGE_NORMAL


class config_PG71V2_NORMAL(config_HYPANELLARGE_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'HyPanel Pro'
        self._rename_cfg_file = 'PG71V2reset.cfg'
        self._autop_cfg_file = 'r000000000271.cfg'
        self._old_firmware_file = 'PG71V2.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'PG71V2'
        self._model_id_NORMAL = '271'

        self._boot_time_after_get_ip = 40
        self._screen_clickable_area = (0, 20, 1280, 800)
        self._screen_width = 1280
        self._screen_height = 800
        self._ps_cmd = 'ps'
        self._cur_activity_use_u2 = True
        self._screen_power_flag = 'mWakefulness='
        self._screen_power_use_u2 = False
        