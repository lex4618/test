# -*- coding: utf-8 -*-

from libconfig.ANDROIDINDOORV6.C317.NORMAL.libconfig_C317_NORMAL import *


class config_C317_KBLUE(config_C317_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._lan_port_type = 'static'
        self._lan_port_ip_address = '10.0.0.200'
        self._web_admin_passwd = 'kblue*20'
        self._web_custom_username = 'kblue'
        self._web_custom_passwd = 'kblue'
        self._oem = 'KBLUE'
