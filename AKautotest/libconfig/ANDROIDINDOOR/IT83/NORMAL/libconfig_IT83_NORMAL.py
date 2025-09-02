# -*- coding: utf-8 -*-

# from libconfig.ANDROIDINDOORV6.NORMAL.libconfig_ANDROIDINDOORV6_NORMAL import *
from libconfig.ANDROIDINDOORV6.IT83.NORMAL.libconfig_IT83_NORMAL import config_IT83_NORMAL as config_IT83


class config_IT83_NORMAL(config_IT83):
    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._series_product_name = 'ANDROIDINDOOR'

    #
    # def __init__(self, device_name=''):
    #     super().__init__(device_name)
    #     # Autop配置文件相关
    #     self._rename_cfg_file = 'IT83reset.cfg'
    #     self._autop_cfg_file = 'r000000000083.cfg'
    #     self._old_firmware_file = 'IT83.zip'
    #     self._firmware_ext = '.zip'
    #     self._model_name = 'IT83'
    #     self._model_id_NORMAL = '83'
    #     self._oem = 'NORMAL'
    #     self._remote_connect_type = 'ssh'
    #     self._screen_size = (1280, 800)
    #     self._system_bar_rect = (0, 0, 1280, 46)
    pass
