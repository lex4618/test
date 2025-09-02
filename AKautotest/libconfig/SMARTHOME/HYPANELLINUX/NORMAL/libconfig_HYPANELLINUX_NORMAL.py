
from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_HYPANELLINUX_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._web_basic_upgrade_default_time = 90
        self._autop_upgrade_default_time = 120
        self._reboot_default_time = 60
        self._reset_default_time = 90
        self._boot_time_after_get_ip = 30

        self._series_product_name = 'HYPANELLINUX'
        self._product_model_name = 'HyPanel Lite'
        self._remote_firmware_dir = [
            r'\\192.168.13.53\smartHome\NormalSpace',
            r'\\192.168.10.51\rom',
            r'\\192.168.10.51\rom2'
        ]
        self._log_file_name = 'DevicesLog.tgz'
        self._reboot_clear_syslog = True
        self._monkey_process_list = ['/app/bin/akbusybox monkey']
        self._monkey_sh_exec_cmd = '/app/bin/akbusybox monkey start 1 &'
        self._upload_log_sh_get_cmd = \
            ('ftpget -u akufile -p akufile!!2022 192.168.10.52 /data/upload_linuxlogs_new.sh'
             ' linux/script/upload_linuxlogs_new.sh;chmod 777 /data/upload_linuxlogs_new.sh')
        self._upload_log_sh_exec_cmd = '/data/upload_linuxlogs_new.sh'
        self._default_export_syslog_type = 'upload'  # web、logcat、tail、upload、pull

        # password相关
        self._setting_pwd = '123456'
        self._more_pwd = ''
        self._tln_or_ssh_pwd = 'yA@9^b8Zq-T+s'
        self._remote_connect_type = 'telnet'

        self._email_receivers = ['sweet.tang@akubela.com',
                                 'wish.chen@akubela.com',
                                 'joyce.su@akubela.com',
                                 'jason.huang@akubela.com',
                                 'dolly.chen@akubela.com',
                                 'andy@akubela.com']

        self._factory_dispaly_img_path = r'\IMG_compare\HYPANELLINUX\NORMAL\factory_dispaly'
        self._monitor_capture_img_path = r'\IMG_compare\HYPANELLINUX\NORMAL\monitor_capture'

    def get_setting_pwd(self):
        return self._setting_pwd

    def get_more_pwd(self):
        return self._more_pwd

    def get_tln_or_ssh_pwd(self):
        return self._tln_or_ssh_pwd

    def get_factory_dispaly_img_path(self):
        path = self._test_file_root_path + self._factory_dispaly_img_path
        return path

    def get_monitor_capture_img_path(self):
        path = self._test_file_root_path + self._monitor_capture_img_path
        return path

    # 浏览器相关
    def get_config_doorphone_url_manual_URL(self,doorphone_file):
        return 'Config.DoorPhone.Url = ' + self.get_manual_autop_URL() + doorphone_file

    def get_config_webcam_url_manual_URL(self,webcam_file):
        return 'Config.WebCam.Url = ' + self.get_manual_autop_URL() + webcam_file

    def get_monitor_export_file_path(self):
        return self.get_chrome_download_dir() + 'PhoneMonitor.tgz'

    def get_doorphone_import_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\doorstation.xml' % self._model_name

    def get_webcam_import_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\webcam.xml' % self._model_name

    def get_doorphone_import_error_xml_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_doorstation.xml' % self._model_name

    def get_webcam_import_error_xml_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_webcam.xml' % self._model_name

    def get_doorphone_import_error_csv_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_doorstation.csv' % self._model_name

    def get_webcam_import_error_csv_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_webcam.csv' % self._model_name

    def get_config_contact_url_manual_URL(self, contact_file):
        return 'Config.Contact.Url = ' + self.get_manual_autop_URL() + contact_file

    def get_contacts_export_file_path(self):
        return self.get_chrome_download_dir() + 'PhoneContacts.tgz'

    def get_contacts_import_xml_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\contact.xml' % self._model_name

    def get_contacts_import_csv_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\contact.csv' % self._model_name

    def get_contacts_import_error_xml_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_contact.xml' % self._model_name

    def get_contacts_import_error_csv_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_contact.csv' % self._model_name

    def get_auto_answer_allowlist_export_file_path(self):
        return self.get_chrome_download_dir() + 'PhoneAllowlist.tgz'

    def get_auto_answer_allowlist_import_error_xml_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_allowlist.xml' % self._model_name

    def get_auto_answer_allowlist_import_error_csv_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_allowlist.csv' % self._model_name

    def get_auto_answer_allowlist_import_xml_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\allowlist.xml' % self._model_name

    def get_auto_answer_allowlist_import_csv_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\allowlist.csv' % self._model_name

    def get_config_allowlist_url_manual_URL(self,allowlist_file):
        return 'Config.Allowlist.Url =  ' + self.get_manual_autop_URL() + allowlist_file

    def get_call_log_export_file_path(self):
        return self.get_chrome_download_dir() + 'PhoneCallLog.tgz'

    def get_blocklist_import_xml_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\Blocklist_max_20.xml' % self._model_name

    def get_blocklist_import_csv_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\Blocklist_max_20.csv' % self._model_name

    def get_blocklist_export_file_path(self):
        return self.get_chrome_download_dir() + 'PhoneBlockList.tgz'

    def get_blocklist_import_error_xml_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_blocklist.xml' % self._model_name

    def get_blocklist_import_error_csv_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_blocklist.csv' % self._model_name

    def get_config_blocklist_url_manual_URL(self,blocklist_file):
        return 'Config.Blocklist.Url = ' + self.get_manual_autop_URL() + blocklist_file

    def get_lift_hints_import_xml_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\LiftHints.xml' % self._model_name

    def get_lift_hints_import_error_xml_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\error_LiftHints.xml' % self._model_name

    def get_lift_hints_export_file_path(self):
        return self.get_chrome_download_dir() + 'LiftHint.tgz'

    def get_config_lift_hints_url_manual_URL(self, lift_hints_file):
        return 'Config.Hints.Url = ' + self.get_manual_autop_URL() + lift_hints_file

    def get_client_certificate_pem_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\client_certificate.pem' % self._model_name

    def get_error_client_certificate_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\wrong.pem' % self._model_name

    def get_error_web_server_certificate_file_path(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\wrong.' % self._model_name
