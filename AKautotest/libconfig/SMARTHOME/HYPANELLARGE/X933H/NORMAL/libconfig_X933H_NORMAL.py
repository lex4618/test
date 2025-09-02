# -*- coding: utf-8 -*-

from libconfig.SMARTHOME.HYPANELLARGE.NORMAL.libconfig_HYPANELLARGE_NORMAL import config_HYPANELLARGE_NORMAL


class config_X933H_NORMAL(config_HYPANELLARGE_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'SmartPanel'
        self._rename_cfg_file = 'X933Hreset.cfg'
        self._autop_cfg_file = 'r000000000933.cfg'
        self._old_firmware_file = 'X933H.zip'
        self._firmware_ext = '.zip'
        self._model_name = 'X933H'
        self._model_id_NORMAL = '933'
        self._oem = 'NORMAL'
        
        self._tln_or_ssh_pwd = ["OSx=w$mGRr4!$3XT0('$", 'OjEEr3d%zyfc0']
        self._tln_ssh_port_list = [2043, 22]
        self._ps_cmd = 'ps'
        self._cur_activity_use_u2 = True
        self._screen_saver_flag = 'mShowingDream'
        
        self._boot_time_after_get_ip = 40
        self._screen_clickable_area = (0, 20, 1280, 800)
        self._screen_width = 1280
        self._screen_height = 800
