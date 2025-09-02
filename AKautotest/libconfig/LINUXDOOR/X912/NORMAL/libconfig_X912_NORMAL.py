# -*- coding: utf-8 -*-

from libconfig.LINUXDOOR.NORMAL.libconfig_LINUXDOOR_NORMAL import *


class config_X912_NORMAL(config_LINUXDOOR_NORMAL):
    """
    R20v3s：r000000000020.cfg
    R20T30：r000000000020P.cfg
    R26：r000000000026P.cfg
    R27：r000000000027P.cfg
    R28：r000000000028.cfg
    A01：r000000000101.cfg
    E10：r000000000110.cfg
    E11： r000000000111.cfg
    X912：r000000000912.cfg
    """

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'X912reset.cfg'
        self._autop_cfg_file = 'r000000000912.cfg'
        self._old_firmware_file = 'X912.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'X912'
        self._model_id_NORMAL = '912'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
