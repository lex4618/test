# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOORV6.C317.NORMAL.libconfig_C317_NORMAL import *


class config_C317_TEKVOX(config_C317_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._web_admin_passwd = 'tekv0xAdmin'

    def get_autop_config_template_file(self):
        return self._test_file_root_path + '\\autop_config_template\\C317\\autop_config_template_C317_TEKVOX.cfg'
