# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOORV6.IT83.NORMAL.libconfig_IT83_NORMAL import *


class config_IT83_VINSMART(config_IT83_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._lan_port_type = 'static'
        self._lan_port_ip_address = '192.168.1.103'
