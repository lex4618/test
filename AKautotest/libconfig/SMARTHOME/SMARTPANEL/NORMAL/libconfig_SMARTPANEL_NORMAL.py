# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_SMARTPANEL_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # 系列机型相关配置项
        self._product_model_name = 'SmartPanel'
        self._series_product_name = 'SMARTPANEL'
        self._current_activity_flag = 'mResumedActivity'
        self._remote_connect_type = 'ssh'
        self._default_export_syslog_type = 'upload'
        self._tln_or_ssh_pwd = ["OSx=w$mGRr4!$3XT0('$", 'OjEEr3d%zyfc0']
        self._tln_ssh_port_list = [2043, 22]

        self._remote_firmware_dir = [
            r'\\192.168.13.53\tsHome\AndroidSpace',
            r'\\192.168.10.51\rom',
            r'\\192.168.10.51\rom2'
        ]

        # 重启恢复出厂时间
        self._web_basic_upgrade_default_time = 600
        self._autop_upgrade_default_time = 900
        self._reboot_default_time = 200
        self._reset_default_time = 500

        # password相关
        self._setting_pwd = '123456'
        self._more_pwd = ''

        self._screen_size = (1280, 800)
        self._system_bar_rect = (0, 0, 1280, 46)
        self._screen_clickable_area = (0, 20, 1280, 800)
        self._screen_width = 1280
        self._screen_height = 800

        self._email_receivers = ['sweet.tang@akubela.com',
                                 'wish.chen@akubela.com',
                                 'joyce.su@akubela.com',
                                 'jason.huang@akubela.com',
                                 'dolly.chen@akubela.com',
                                 'andy@akubela.com']

    def get_setting_pwd(self):
        return self._setting_pwd

    def get_more_pwd(self):
        return self._more_pwd

    def get_screen_size(self):
        return self._screen_size

    def get_system_bar_rect(self):
        return self._system_bar_rect
