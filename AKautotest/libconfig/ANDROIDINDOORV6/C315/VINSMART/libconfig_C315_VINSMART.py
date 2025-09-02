# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOORV6.C315.NORMAL.libconfig_C315_NORMAL import *


class config_C315_VINSMART(config_C315_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._lan_port_type = 'static'
        self._lan_port_ip_address = '192.168.1.101'
