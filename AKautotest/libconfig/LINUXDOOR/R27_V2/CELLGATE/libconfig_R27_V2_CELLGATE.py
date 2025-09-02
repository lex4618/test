# -*- coding: utf-8 -*-

from libconfig.LINUXDOOR.R27_V2.NORMAL.libconfig_R27_V2_NORMAL import *


class config_R27_V2_CELLGATE(config_R27_V2_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._oem = 'CELLGATE'
        self._web_admin_passwd = '3V0_Zap0p3n!'
