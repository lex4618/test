# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_AKUBELAADDON_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._web_basic_upgrade_default_time = 90
        self._autop_upgrade_default_time = 120
        self._reboot_default_time = 60
        self._reset_default_time = 90

        self._log_file_name = 'DevicesLog.tgz'
        self._reboot_clear_syslog = True
        self._series_product_name = 'AKUBELAADDON'
        self._product_type_name = 'LOCK'
        self._remote_firmware_dir = [
            r'\\192.168.13.53\smartHome\NormalSpace',
            r'\\192.168.10.51\rom',
            r'\\192.168.10.51\rom2'
        ]

        # password相关
        self._setting_pwd = '123456'
        self._more_pwd = ''
        self._tln_or_ssh_pwd = 'yA@9^b8Zq-T+s'
        self._remote_connect_type = 'telnet'

        self._email_receivers = ['loong.chen@akubela.com',
                                 'frank.feng@akubela.com',
                                 'jason.huang@akubela.com',
                                 'andy@akubela.com']
