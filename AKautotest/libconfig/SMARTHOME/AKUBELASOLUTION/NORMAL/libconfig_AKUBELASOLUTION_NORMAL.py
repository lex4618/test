# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_AKUBELASOLUTION_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # 系列机型相关配置项
        self._series_product_name = 'AKUBELASOLUTION'

        # Email相关
        self._email_receivers = ['frank.feng@akubela.com',
                                 'vivian.zhang@akubela.com',
                                 'jason.huang@akubela.com',
                                 'dolly.chen@akubela.com',
                                 'andy@akubela.com']
