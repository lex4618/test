# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_ACCESSDOOR_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # 系列配置项
        self._series_product_name = 'ACCESSDOOR'
        self._product_type_name = 'DOOR'
        self._tln_or_ssh_pwd = ['Der%yg2B^aq4t', 'OjEEr3d%zyfc0']
        self._remote_connect_type = 'telnet'
        self._tln_ssh_port_list = 23
        self._selftestdassistant_path = r'\tools\SelftestdAssistant\SelftestdAssistant.exe'
        self._web_basic_upgrade_default_time = 100
        self._autop_upgrade_default_time = 100
        self._reboot_default_time = 60
        self._reset_default_time = 90
        self._log_file_name = 'DevicesLog.tgz'
        self._default_location = 'Stair Phone'
        # Email相关
        self._email_receivers = ['lex.lin@akuvox.com', 'jianan.you@akuvox.com']
        self._remote_firmware_dir = r'\\192.168.10.75\NormalSpace'
        self.ps_command = 'ps'
        self.check_ps_list = [
            '/app/bin/dclient',
            '/app/bin/phone',
            '/app/bin/ispserver',
            '/app/bin/vaMain'
        ]
