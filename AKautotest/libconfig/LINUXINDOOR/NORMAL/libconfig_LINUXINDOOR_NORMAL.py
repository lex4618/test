# -*- coding: utf-8 -*-

from libconfig.COMMON.libconfig_NORMAL import config_NORMAL


class config_LINUXINDOOR_NORMAL(config_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._series_product_name = 'LINUXINDOOR'
        self._remote_firmware_dir = r'\\192.168.10.75\NormalSpace'
        self._setting_pwd = '123456'
        self._more_pwd = ''
        self._tln_or_ssh_pwd = ['I8+R)#ui6T2^t', 'OjEEr3d%zyfc0', 'NopassWD702']
        self._remote_connect_type = 'telnet'
        self._tln_ssh_port_list = [23]

        self._auto_reset_after_transition_upgrade_enable = False
        self._web_basic_upgrade_default_time = 90
        self._autop_upgrade_default_time = 120
        self._reboot_default_time = 60
        self._reset_default_time = 90
        self._email_receivers = [
            'wendy.su@akuvox.com',
            'vicky.huang@akuvox.com',
            'yuanlin.li@akuvox.com',
            'snow.chen@akuvox.com',
            'joannes.jian@akuvox.com',
            'lrpei.li@akuvox.com'
        ]

        self.ps_command = 'ps'
        self.check_ps_list = [
            '/app/bin/vaMain',
            '/app/bin/dclient',
            '/app/bin/sip -a 0',
            '/app/bin/phone',
            # '/app/bin/netconfig',
            # '/app/bin/fcgiserver.fcgi',
            # '/app/bin/api.fcgi',
        ]
        self._factory_dispaly_img_path = r'\IMG_compare\LINUXINDOOR\NORMAL\factory_dispaly'
        self._monitor_capture_img_path = r'\IMG_compare\LINUXINDOOR\NORMAL\monitor_capture'

    def get_setting_pwd(self):
        return self._setting_pwd

    def get_more_pwd(self):
        return self._more_pwd

    def get_factory_dispaly_img_path(self):
        path = self._test_file_root_path + self._factory_dispaly_img_path
        return path

    def get_monitor_capture_img_path(self):
        path = self._test_file_root_path + self._monitor_capture_img_path
        return path

    def get_export_pcap_file_path(self):
        return self.get_chrome_download_dir() + 'phone.pcap'

    # 浏览器相关
    def get_config_doorphone_url_manual_URL(self, doorphone_file):
        return 'Config.DoorPhone.Url = ' + self.get_manual_autop_URL() + doorphone_file

    def get_config_webcam_url_manual_URL(self, webcam_file):
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

    def get_config_allowlist_url_manual_URL(self, allowlist_file):
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

    def get_config_blocklist_url_manual_URL(self, blocklist_file):
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
