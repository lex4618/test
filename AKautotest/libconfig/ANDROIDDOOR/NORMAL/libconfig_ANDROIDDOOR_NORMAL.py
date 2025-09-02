# -*- coding: utf-8 -*-

import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_ANDROIDDOOR_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._series_product_name = 'ANDROIDDOOR'
        self._product_type_name = 'DOOR'
        self._web_basic_upgrade_default_time = 600
        self._autop_upgrade_default_time = 600
        self._reboot_default_time = 120
        self._reset_default_time = 180
        # password相关
        self._setting_pwd = '123456'
        self._more_pwd = ''
        self._tln_or_ssh_pwd = ['Der%yg2B^aq4t','OjEEr3d%zyfc0']
        self._remote_connect_type = 'ssh'

        self._screen_size = (800, 1280)

        # Appium连接相关配置
        self._platform_version = '5.1.1'

        self._email_receivers = [
            'lex.lin@akuvox.com',
            'jianan.you@akuvox.com'
        ]

        self.ps_command = 'busybox ps'
        self.check_ps_list = [
            'com.akuvox.phone',
            '/app/bin/dclient',
            '/app/bin/sip -a 16'   # 2025.8.15 lex: S539
        ]

    def get_setting_pwd(self):
        return self._setting_pwd

    def get_more_pwd(self):
        return self._more_pwd

    def get_screen_size(self):
        return self._screen_size

    @staticmethod
    def get_launcher_apk():
        return root_path + '\\tools\\AndroidDoor_Launcher\\launcher.apk'
