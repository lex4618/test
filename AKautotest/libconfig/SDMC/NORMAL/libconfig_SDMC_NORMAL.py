# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_SDMC_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # 系列机型相关配置项
        self._series_product_name = 'SDMC'
        self._model_name = 'SDMC'
        self._oem = 'NORMAL'
        self._email_receivers = [
            'cool.shi@akuvox.com',
            'cady.chen@akuvox.com',
            'comiy.chen@akuvox.com'
        ]
