# -*- coding: utf-8 -*-

from libconfig.VIDEOPHONE.R48.NORMAL.libconfig_R48_NORMAL import *


class config_R48_AKCLOUDUNION(config_R48_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._oem = 'AKCLOUDUNION'
