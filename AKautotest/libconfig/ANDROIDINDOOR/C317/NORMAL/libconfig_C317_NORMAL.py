# -*- coding: utf-8 -*-

# from libconfig.ANDROIDINDOORV6.NORMAL.libconfig_ANDROIDINDOORV6_NORMAL import *
from libconfig.ANDROIDINDOORV6.C317.NORMAL.libconfig_C317_NORMAL import config_C317_NORMAL as config_C317


class config_C317_NORMAL(config_C317):
    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._series_product_name = 'ANDROIDINDOOR'

    #
    # def __init__(self, device_name=''):
    #     super().__init__(device_name)
    #     # Autop配置文件相关
    #     self._rename_cfg_file = 'C317reset.cfg'
    #     self._autop_cfg_file = 'r000000000317.cfg'
    #     self._old_firmware_file = 'C317.zip'
    #     self._firmware_ext = '.zip'
    #     self._model_name = 'C317'
    #     self._model_id_NORMAL = '117'
    #     self._oem = 'NORMAL'
    #     self._screen_size = (1280, 800)
    #     self._system_bar_rect = (0, 0, 1280, 46)

    pass
