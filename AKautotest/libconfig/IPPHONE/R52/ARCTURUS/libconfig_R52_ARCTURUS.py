# -*- coding: utf-8 -*-

from libconfig.IPPHONE.R52.NORMAL.libconfig_R52_NORMAL import *


class config_R52_ARCTURUS(config_R52_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._lan_port_type = 'static'
        self._lan_port_ip_address = '192.168.1.100'

    def get_autop_config_template_file(self):
        return self._test_file_root_path + '\\autop_config_template\\R52\\autop_config_template_R52_ARCTURUS.cfg'
