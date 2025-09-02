# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_LINUXDOOR_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._series_product_name = 'LINUXDOOR'
        self._product_type_name = 'DOOR'
        self._setting_pwd = '123456'
        self._more_pwd = ''
        self._tln_or_ssh_pwd = ['Der%yg2B^aq4t', 'OjEEr3d%zyfc0']
        self._remote_connect_type = 'ssh'
        self._selftestdassistant_path = r'\tools\SelftestdAssistant\SelftestdAssistant.exe'
        self._web_basic_upgrade_default_time = 120
        self._autop_upgrade_default_time = 120
        self._reboot_default_time = 60
        self._reset_default_time = 90
        self._email_receivers = [
            'lex.lin@akuvox.com',
            'jianan.you@akuvox.com'
        ]
        self._button_dial_key = 'S'
        self.ps_command = 'ps'
        self.check_ps_list = [
            '/app/bin/vaMain',
            '/app/bin/dclient',
            '/app/bin/sip -a 16',
            '/app/bin/phone',
            # '/app/bin/netconfig',
            # '/app/bin/fcgiserver.fcgi',
            # '/app/bin/api.fcgi',
        ]

    def get_setting_pwd(self):
        return self._setting_pwd

    def get_more_pwd(self):
        return self._more_pwd

    def get_rtsp_screenshot_file_path(self):
        return self.get_chrome_download_dir() + 'rtsp.png'

    def get_export_pcap_file_path(self):
        return self.get_chrome_download_dir() + 'phone.pcap'

    def get_button_dial_key(self):
        return self._button_dial_key
