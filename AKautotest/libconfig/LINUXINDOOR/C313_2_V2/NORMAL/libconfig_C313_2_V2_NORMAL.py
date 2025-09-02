# -*- coding: utf-8 -*-

from libconfig.LINUXINDOOR.NORMAL.libconfig_LINUXINDOOR_NORMAL import *


class config_C313_2_V2_NORMAL(config_LINUXINDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'C313_2_V2reset.cfg'
        self._autop_cfg_file = 'r000000000212.cfg'
        self._old_firmware_file = 'C313_2_V2.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'C313_2_V2'
        self._model_id_NORMAL = '212'
        self._oem = 'NORMAL'

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
