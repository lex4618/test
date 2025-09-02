# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.C313.NORMAL.libconfig_C313_NORMAL import *


class config_C313_ROBERT(config_C313_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._oem = 'ROBERT'
        self._reset_after_upgrade_enable = True
