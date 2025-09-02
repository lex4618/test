# -*- coding: utf-8 -*-

from libconfig.LINUXDOOR.R20.NORMAL.libconfig_R20_NORMAL import *


class config_R20_CELLGATE(config_R20_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._web_admin_passwd = '3V0_Zap0p3n!'
        self._oem = 'CELLGATE'
