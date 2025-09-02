# -*- coding: utf-8 -*-

from libconfig.IPPHONE.R53.NORMAL.libconfig_R53_NORMAL import *

class config_R53_GUANBEI(config_R53_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._web_admin_passwd = 'cosmo'

    def get_autop_config_template_file(self):
        return self._test_file_root_path + '\\autop_config_template\\R53\\autop_config_template_R53_GUANBEI.cfg'
