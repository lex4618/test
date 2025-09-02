# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_ACMS_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # 系列配置项
        self._series_product_name = 'ACMS'
        self._model_name = 'ACMS'
        self._oem = 'NORMAL'
