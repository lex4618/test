# -*- coding: utf-8 -*-

from libconfig.IPPHONE.R50.NORMAL.libconfig_R50_NORMAL import *


class config_R50_NAG(config_R50_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)

    def get_autop_config_template_file(self):
        return self._test_file_root_path + '\\autop_config_template\\R50\\autop_config_template_R50_NAG.cfg'
