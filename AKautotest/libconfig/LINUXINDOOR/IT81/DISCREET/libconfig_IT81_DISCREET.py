# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.IT81.NORMAL.libconfig_IT81_NORMAL import *


class config_IT81_DISCREET(config_IT81_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)

    # autop配置文件模板
    def get_autop_config_template_file(self):
        return self._test_file_root_path + '\\autop_config_template\\IT81\\autop_config_template_IT81_DISCREET.cfg'
