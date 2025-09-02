# -*- coding: utf-8 -*-

# from libconfig.ANDROIDINDOORV6.NORMAL.libconfig_ANDROIDINDOORV6_NORMAL import *
from libconfig.ANDROIDINDOORV6.C315.NORMAL.libconfig_C315_NORMAL import config_C315_NORMAL as config_C315


class config_C315_NORMAL(config_C315):
    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._series_product_name = 'ANDROIDINDOOR'

    #     # Autop配置文件相关
    #     self._rename_cfg_file = 'C315reset.cfg'
    #     self._autop_cfg_file = 'r000000000315.cfg'
    #     self._old_firmware_file = 'C315.zip'
    #     self._firmware_ext = '.zip'
    #     self._model_name = 'C315'
    #     self._model_id_NORMAL = '115'
    #     self._oem = 'NORMAL'


