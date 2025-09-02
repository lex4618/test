# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_VIDEOPHONE_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._series_product_name = 'VIDEOPHONE'
        self._remote_firmware_dir = r'\\192.168.10.75\AndroidSpace'
        self._setting_pwd = '123456'
        self._more_pwd = ''
        self._tln_or_ssh_pwd = 'nopasswd'
        self._remote_connect_type = 'ssh'

        self._web_basic_upgrade_default_time = 600
        self._autop_upgrade_default_time = 900
        self._reboot_default_time = 200
        self._reset_default_time = 500

        self._email_receivers = [
            'helena.chen@akuvox.com',
            'linfeng.ye@akuvox.com',
            'tao.feng@akuvox.com',
            'cool.shi@akuvox.com'
        ]

    def get_setting_pwd(self):
        return self._setting_pwd

    def get_more_pwd(self):
        return self._more_pwd
