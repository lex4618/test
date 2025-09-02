# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOOR.C319.NORMAL.libconfig_C319_NORMAL import config_C319_NORMAL


class config_C319_TEKVOX(config_C319_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._web_admin_passwd = 'tekv0xAdmin'
        self._web_user_passwd = 'tekv0xUser'
