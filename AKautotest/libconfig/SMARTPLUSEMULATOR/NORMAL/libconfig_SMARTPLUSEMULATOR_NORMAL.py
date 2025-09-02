# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import *


class config_SMARTPLUSEMULATOR_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # 系列配置项
        self._series_product_name = 'SMARTPLUSEMULATOR'
        self._model_name = 'SMARTPLUSEMULATOR'
        self._oem = 'NORMAL'
