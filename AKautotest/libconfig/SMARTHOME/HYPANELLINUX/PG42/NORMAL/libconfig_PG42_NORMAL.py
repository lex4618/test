
from libconfig.SMARTHOME.HYPANELLINUX.NORMAL.libconfig_HYPANELLINUX_NORMAL import *


class config_PG42_NORMAL(config_HYPANELLINUX_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        self._product_model_name = 'HyPanel Elite 7'
        self._product_type_name = 'PANEL'
        self._rename_cfg_file = 'PG42reset.cfg'
        self._autop_cfg_file = 'r000000000042.cfg'
        self._old_firmware_file = 'PG42.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'PG42'
        self._model_id_NORMAL = '42'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'telnet'

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
