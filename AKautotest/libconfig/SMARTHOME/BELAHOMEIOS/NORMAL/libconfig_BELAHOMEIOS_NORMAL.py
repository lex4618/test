# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_BELAHOMEIOS_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # 系列机型相关配置项
        self._series_product_name = 'BELAHOMEIOS'
        self._model_name = 'BELAHOMEIOS'
        self._product_type_name = 'BELAHOME'
        self._oem = 'NORMAL'
        self._firmware_ext = '.apk'
        self._email_receivers = [
            'frank.feng@akubela.com',
            'vivian.zhang@akubela.com',
            'dolly.chen@akubela.com',
            'jason.huang@akubela.com',
            'andy@akubela.com'
        ]
