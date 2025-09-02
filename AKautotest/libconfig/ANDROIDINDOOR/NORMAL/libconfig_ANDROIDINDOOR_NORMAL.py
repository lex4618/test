# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_ANDROIDINDOOR_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # 系列机型相关配置项
        self._series_product_name = 'ANDROIDINDOOR'
        self._tln_or_ssh_pwd = ['I8+R)#ui6T2^t', 'nopasswd', 'OjEEr3d%zyfc0']
        self._remote_connect_type = 'ssh'
        self._tln_ssh_port_list = [2043, 22]

        # 重启恢复出厂时间
        self._web_basic_upgrade_default_time = 1200
        self._autop_upgrade_default_time = 900
        self._reboot_default_time = 200
        self._reset_default_time = 500
        self._reset_config_default_time = 180

        self._remote_firmware_dir = r'\\192.168.10.75\AndroidSpace'

        self._doorbell_event = ['sendevent /dev/input/event0 1 28 1;' \
                                'sendevent /dev/input/event0 1 28 0;' \
                                'sendevent /dev/input/event0 0 0 0',
                                'sendevent /dev/input/event2 1 28 1;' \
                                'sendevent /dev/input/event2 1 28 0;' \
                                'sendevent /dev/input/event2 0 0 0'
                                ]

        # password相关
        self._setting_pwd = '123456'
        self._more_pwd = ''

        self._screen_size = (1024, 600)
        self._system_bar_rect = (0, 0, 1024, 46)

        self._email_receivers = [
            'helena.chen@akuvox.com',
            'wendy.su@akuvox.com',
            'irene.zhang@akuvox.com',
            'vicky.huang@akuvox.com',
            'joannes.jian@akuvox.com',
            'lrpei.li@akuvox.com'
        ]
        self.ps_command = 'busybox ps'
        self.check_ps_list = [
            'com.akuvox.phone',
            '/app/bin/dclient',
            '/app/bin/sip',
        ]

    def get_doorbell_event(self):
        return self._doorbell_event

    def get_setting_pwd(self):
        return self._setting_pwd

    def get_more_pwd(self):
        return self._more_pwd

    def get_screen_size(self):
        return self._screen_size

    def get_system_bar_rect(self):
        return self._system_bar_rect

    # 导入文件
    def get_lift_hints_import_xml_file_path(self):
        return self.get_import_file('LiftHints.xml')

    def get_lift_hints_import_error_xml_file_path(self):
        return self.get_import_file('error_fmt.txt')

    def get_lift_hints_export_file_path(self):
        return self.get_chrome_download_dir() + 'LiftHint.tgz'

    def get_config_lift_hints_url_manual_URL(self, lift_hints_file):
        return 'Config.Hints.Url = ' + self.get_manual_autop_URL() + lift_hints_file

    def get_auto_answer_allowlist_export_file_path(self):
        return self.get_chrome_download_dir() + 'AllowList.tgz'

    def get_auto_answer_allowlist_import_error_xml_file_path(self):
        return self.get_import_file('allowlist\\error_allowlist.xml')

    def get_auto_answer_allowlist_import_error_csv_file_path(self):
        return self.get_import_file('allowlist\\error_allowlist.csv')

    def get_auto_answer_allowlist_import_xml_file_path(self):
        return self.get_import_file('allowlist\\allowlist.xml')

    def get_auto_answer_allowlist_import_csv_file_path(self):
        return self.get_import_file('allowlist\\allowlist.csv')

    def get_config_allowlist_url_manual_URL(self, allowlist_file):
        return 'Config.Allowlist.Url =  ' + self.get_manual_autop_URL() + allowlist_file

    def get_wallpaper_import_file(self, file_name):
        return self.get_import_file('wallpaper\\%s' % file_name)

    def get_monitor_export_file_path(self):
        return self.get_chrome_download_dir() + 'PhoneMonitor.tgz'

    def get_door_monitor_import_file(self, file_name):
        return self.get_import_file('door_monitor\\%s' % file_name)

    def get_alarm_ring_tone_import_file(self, file_name):
        return self.get_import_file('alarm_ring_tone\\%s' % file_name)

    def get_client_certificate_pem_file_path(self):
        return self.get_import_file('web_cert_file\\client_certificate.pem')

    def get_error_client_certificate_file_path(self):
        return self.get_import_file('web_cert_file\\wrong.pem')

    def get_web_cert_import_file(self, file_name):
        return self.get_import_file('web_cert_file\\%s' % file_name)

    def get_web_logo_image_import_file(self, file_name):
        return self.get_import_file('logo\\web_logo\\%s' % file_name)

    def get_boot_logo_image_import_file(self, file_name):
        return self.get_import_file('logo\\boot_logo\\%s' % file_name)
