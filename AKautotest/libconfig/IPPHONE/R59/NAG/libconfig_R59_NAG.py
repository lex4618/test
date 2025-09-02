# -*- coding: utf-8 -*-

from libconfig.IPPHONE.R59.NORMAL.libconfig_R59_NORMAL import *


class config_R59_NAG(config_R59_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)

    def get_autop_config_template_file(self):
        return self._test_file_root_path + '\\autop_config_template\\R59\\autop_config_template_R59_NAG.cfg'
