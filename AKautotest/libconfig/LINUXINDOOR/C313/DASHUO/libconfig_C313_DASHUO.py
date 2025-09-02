# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.C313.NORMAL.libconfig_C313_NORMAL import *


class config_C313_DASHUO(config_C313_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)

    # autop配置文件模板
    def get_autop_config_template_file(self):
        return self._test_file_root_path + '\\autop_config_template\\C313\\autop_config_template_C313_DASHUO.cfg'

