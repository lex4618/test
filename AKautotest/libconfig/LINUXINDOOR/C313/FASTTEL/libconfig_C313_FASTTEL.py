# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.C313.NORMAL.libconfig_C313_NORMAL import *


class config_C313_FASTTEL(config_C313_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._web_admin_passwd = 'AdminFasttel123!'
        self._oem = 'FASTTEL'
