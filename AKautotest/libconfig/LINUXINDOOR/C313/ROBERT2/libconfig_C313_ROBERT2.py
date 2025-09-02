# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.C313.NORMAL.libconfig_C313_NORMAL import *


class config_C313_ROBERT2(config_C313_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._oem = 'ROBERT2'
        self._reset_after_upgrade_enable = True
        self._web_basic_upgrade_default_time = 600
        self._autop_upgrade_default_time = 600
