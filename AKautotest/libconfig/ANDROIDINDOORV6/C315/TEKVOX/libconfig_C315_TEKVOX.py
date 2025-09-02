# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOORV6.C315.NORMAL.libconfig_C315_NORMAL import *


class config_C315_TEKVOX(config_C315_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._web_admin_passwd = 'tekv0xAdmin'

    def get_autop_config_template_file(self):
        return self._test_file_root_path + '\\autop_config_template\\C315\\autop_config_template_C315_TEKVOX.cfg'
