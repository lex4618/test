# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.NORMAL.libconfig_LINUXINDOOR_NORMAL import *


class config_Hager_Audio_NORMAL(config_LINUXINDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'Hager_Audioreset.cfg'
        self._autop_cfg_file = 'r000000000062.cfg'
        self._old_firmware_file = 'Hager_Audio.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'Hager_Audio'
        self._model_id_NORMAL = '62'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'
        self._tln_ssh_port_list = [23]
        self._tln_or_ssh_pwd = ['yA@9^b8Zq-T+s','Yhg#Z^q@78u']
        self._web_admin_passwd = '527dcec554a36de6a48b50703bed0f38'

    # 浏览器相关

    def get_doorphone_export_file_path(self):
        return self.get_chrome_download_dir() + 'doorphone_file.tgz'

    def get_webcam_export_file_path(self):
        return self.get_chrome_download_dir() + 'webcam_file.tgz'

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
