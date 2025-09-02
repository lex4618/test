# -*- coding: utf-8 -*-

from libconfig.GUARDPHONE.R48GP.NORMAL.libconfig_R48GP_NORMAL import *


class config_R48GP_AKCLOUDUNION(config_R48GP_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._oem = 'AKCLOUDUNION'
