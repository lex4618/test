# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_HYPANELSUPREME_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # 系列机型相关配置项
        self._product_model_name = 'HyPanel Supreme'
        self._series_product_name = 'HYPANELSUPREME'
        self._tln_or_ssh_pwd = ["OSx=w$mGRr4!$3XT0('$", 'nopasswd']
        self._remote_connect_type = 'ssh'
        self._default_export_syslog_type = 'upload'
        self._ps_cmd = 'ps'
        self._screen_saver_flag = 'mAllowLockscreenWhenOnDisplays'
        self._current_activity_flag = 'mResumedActivity'
        self._cur_activity_use_u2 = True  # PS51机型uiautomator2框架无法使用app_current()方法获取activity，只能用dumpsys activity
        self._screen_size = (1024, 600)
        self._system_bar_rect = (0, 0, 1024, 46)
        self._screen_clickable_area = (20, 20, 2560, 1600)
        self._screen_width = 2560
        self._screen_height = 1600
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
        self._boot_time_after_get_ip = 45

        # password相关
        self._setting_pwd = '123456'
        self._more_pwd = ''

        self._email_receivers = [
            'sweet.tang@akubela.com',
            'wish.chen@akubela.com',
            'joyce.su@akubela.com',
            'jason.huang@akubela.com',
            'dolly.chen@akubela.com',
            'andy@akubela.com'
        ]

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
        return self.get_import_file('error_LiftHints.xml')

    def get_lift_hints_export_file_path(self):
        return self.get_chrome_download_dir() + 'LiftHint.tgz'

    def get_config_lift_hints_url_manual_URL(self, lift_hints_file):
        return 'Config.Hints.Url = ' + self.get_manual_autop_URL() + lift_hints_file

    def get_auto_answer_allowlist_export_file_path(self):
        return self.get_chrome_download_dir() + 'AllowList.tgz'

    def get_auto_answer_allowlist_import_error_xml_file_path(self):
        return self.get_import_file('error_allowlist.xml')

    def get_auto_answer_allowlist_import_error_csv_file_path(self):
        return self.get_import_file('error_allowlist.csv')

    def get_auto_answer_allowlist_import_xml_file_path(self):
        return self.get_import_file('allowlist.xml')

    def get_auto_answer_allowlist_import_csv_file_path(self):
        return self.get_import_file('allowlist.csv')

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
