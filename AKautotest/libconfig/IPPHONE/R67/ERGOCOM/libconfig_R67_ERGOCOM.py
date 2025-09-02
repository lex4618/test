# -*- coding: utf-8 -*-

from libconfig.IPPHONE.R67.NORMAL.libconfig_R67_NORMAL import *


class config_R67_ERGOCOM(config_R67_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._oem = 'ERGOCOM'
