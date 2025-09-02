# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.C313.NORMAL.libconfig_C313_NORMAL import *


class config_C313_XONTEL(config_C313_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._web_admin_passwd = 'xontel'
        self._lan_port_type = 'static'
        self._lan_port_ip_address = '192.168.1.100'
        self._oem = 'XONTEL'
