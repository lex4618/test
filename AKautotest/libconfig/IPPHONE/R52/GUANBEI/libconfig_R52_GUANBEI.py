# -*- coding: utf-8 -*-

from libconfig.IPPHONE.R52.NORMAL.libconfig_R52_NORMAL import *


class config_R52_GUANBEI(config_R52_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._web_admin_passwd = 'cosmo'

    def get_autop_config_template_file(self):
        return self._test_file_root_path + '\\autop_config_template\\R52\\autop_config_template_R52_GUANBEI.cfg'
