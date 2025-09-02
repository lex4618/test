# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_IPPHONE_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._series_product_name = 'IPPHONE'
        self._remote_firmware_dir = r'\\192.168.10.75\NormalSpace'

        # password相关
        self._setting_pwd = '123456'
        self._more_pwd = ''
        self._tln_or_ssh_pwd = 'yA@^b4Kz-V+s'
        self._remote_connect_type = 'ssh'

        self._web_basic_upgrade_default_time = 150
        self._autop_upgrade_default_time = 150
        self._reboot_default_time = 90
        self._reset_default_time = 90

        self._email_receivers = [
            'alice.guo@akuvox.com',
            'zalman.zhang@akuvox.com',
            'cool.shi@akuvox.com',
        ]

    def get_setting_pwd(self):
        return self._setting_pwd

    def get_more_pwd(self):
        return self._more_pwd
