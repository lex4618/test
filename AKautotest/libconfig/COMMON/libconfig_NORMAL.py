from akcommon_define import *
import os.path
import re
import traceback
import socket
import configparser
import tempfile


class config_NORMAL:

    def __init__(self, device_name=''):
        self._device_name = device_name
        self._chrome_prefs = {}
        self._device_web_element_info = {}
        self._device_normal_web_element_info = {}
        self._device_ui_element_info = {}

        self._akubela_user_web_element_info = {}
        self._normal_akubela_user_web_element_info = {}
        self._device_web_interface_info = None
        self._old_firmware_path = ''

        # 设备端配置项相关
        self._rename_cfg_file = ''
        self._autop_cfg_file = ''
        self._autop_cfg_use_mac_enable = True
        self._old_firmware_file = ''
        self._firmware_ext = '.rom'
        self._firmware_prefix = ''
        self._firmware_suffix = ''
        self._product_type_name = ''
        self._series_product_name = 'COMMON'
        self._model_name = 'COMMON'
        self._model_id_NORMAL = '0'
        self._oem = 'NORMAL'
        self._product_model_name = ''
        self._web_basic_upgrade_default_time = 90
        self._autop_upgrade_default_time = 90
        self._reboot_default_time = 90
        self._reset_default_time = 90
        self._reset_config_default_time = 90
        self._boot_time_after_get_ip = 40
        self._reset_after_upgrade_enable = False
        self._auto_reset_after_transition_upgrade_enable = True  # 过渡版本升级到旧版本是否自动恢复出厂
        self._log_file_name = 'PhoneLog.tgz'
        self._screen_saver_flag = 'mShowingDream'
        self._screen_power_flag = 'Display Power'
        self._screen_power_use_u2 = True
        self._default_location = 'COMMON'
        self._current_activity_flag = 'mFocusedActivity'
        self._cur_activity_use_u2 = True  # uiautomator2框架是否使用app_current()方法获取activity，有些机型只能用dumpsys activity
        self._screen_clickable_area = None
        self._screen_width = 0
        self._screen_height = 0
        self._package_name = None

        # Appium连接相关配置
        self._platform_version = '9'
        self._appium_command = 'appium'

        # 设备端默认IP设置
        self._lan_port_type = 'dhcp'
        self._lan_port_ip_address = ''

        # 网页登录相关
        self._web_admin_username = 'admin'
        self._web_admin_passwd = 'admin'
        self._web_admin_password_changed = 'Aa12345678'
        self._web_custom_username = 'admin'
        self._web_custom_passwd = 'admin'
        self._web_user_username = 'user'
        self._web_user_passwd = 'user'

        # password相关
        self._setting_pwd = '123456'
        self._more_pwd = ''

        # 屏幕尺寸
        self._screen_size = (1024, 600)
        self._system_bar_rect = (0, 0, 1024, 46)

        # Telnet SSH
        self._remote_connect_type = 'ssh'
        self._tln_or_ssh_pwd = ''
        self._tln_ssh_port_list = [22]  # 设备SSH Telnet端口，新版本考虑安全性，修改了默认端口，可以在各自机型的config子类里面重写增加端口列表，比如[22, 2043]
        self._ps_cmd = 'ps'
        self._adb_port = 5654

        self._email_receivers = []
        self._remote_firmware_dir = ''
        self._selftestdassistant_path = r'\tools\SelftestdAssistant_1.0.0.12\SelftestdAssistant.exe'

        self._monkey_sh_get_cmd = ('ftpget -u akufile -p akufile!!2022 192.168.10.52 /data/monkeytest.sh'
                                   ' android/script/monkeytest.sh;'
                                   'chmod 777 /data/monkeytest.sh;cd /sdcard;')
        self._monkey_sh_exec_cmd = 'nohup /data/monkeytest.sh zhensen.huang 1 > /dev/null 2>&1 &'
        self._monkey_process_list = ['/data/monkeytest.sh', 'com.android.commands.monkey']
        self._upload_log_sh_get_cmd = (
            'ftpget -u akufile -p akufile!!2022 192.168.10.52 /data/upload_androidlog_autotest.sh'
            ' android/script/upload_androidlog_autotest.sh; chmod 777 /data/upload_androidlog_autotest.sh')
        self._upload_log_sh_exec_cmd = '/data/upload_androidlog_autotest.sh'
        self._reboot_clear_syslog = False
        self._default_export_syslog_type = 'web'  # web、logcat、tail、upload、pull

    def get_telnet_type(self, hostip):
        """
        2024.7.9  lex: 嵌入式门口机, 经常不同版本, 会有telnet, ssh. 做一个尝试.
        """
        portlist = self.get_tln_ssh_port_list()
        if 22 not in portlist and 23 not in portlist:
            return False
        client = None
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(1)
            client.connect((hostip, 22))
            client.close()
            aklog_info('get telnet type: {}:{}'.format('ssh', 22))
            return ('ssh', 22)
        except:
            client.close()
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(1)
            client.connect((hostip, 23))
            client.close()
            aklog_info('get telnet type: {}:{}'.format('telnet', 23))
            return ('telnet', 23)
        except:
            client.close()
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(1)
            client.connect((hostip, 2043))
            client.close()
            aklog_info('get telnet type: {}:{}'.format('ssh', 2043))
            return ('ssh', 2043)
        except:
            client.close()

    def put_device_name(self, device_name):
        self._device_name = device_name

    def get_device_name(self):
        return self._device_name

    def get_device_normal_web_element_info(self, web_branch, printinfo=False):
        if not self._device_normal_web_element_info:
            self._device_normal_web_element_info = config_parse_normal_web_element_info_from_xml(
                web_branch,
                printinfo=printinfo)
        return self._device_normal_web_element_info

    def get_device_web_element_info(self, version_branch, web_branch, printinfo=False):
        if not self._device_web_element_info:
            self._device_web_element_info = config_parse_web_element_info_from_xml(
                self.get_model_name(),
                self.get_oem_name(),
                version_branch,
                web_branch,
                printinfo=printinfo)
        return self._device_web_element_info

    def get_device_ui_element_info(self, version_branch, printinfo=False):
        if not self._device_ui_element_info:
            self._device_ui_element_info = config_parse_ui_element_info_from_xml(
                self.get_model_name(),
                self.get_oem_name(),
                version_branch,
                printinfo=printinfo)
        return self._device_ui_element_info

    def get_akubela_user_web_element_info(self, version_branch, web_branch, printinfo=False):
        if not self._akubela_user_web_element_info:
            self._akubela_user_web_element_info = config_parse_web_element_info_from_xml(
                self.get_model_name(),
                self.get_oem_name(),
                version_branch,
                web_branch,
                element_info_type='userweb_element_info',
                printinfo=printinfo)
        return self._akubela_user_web_element_info

    def get_normal_akubela_user_web_element_info(self, web_branch, printinfo=False):
        if not self._normal_akubela_user_web_element_info:
            self._normal_akubela_user_web_element_info = config_parse_normal_web_element_info_from_xml(
                web_branch,
                element_info_type='userweb_element_info',
                printinfo=printinfo)
        return self._normal_akubela_user_web_element_info

    def get_device_web_interface_info(self, version_branch, web_branch, printinfo=False):
        if not self._device_web_interface_info:
            self._device_web_interface_info = config_parse_web_interface_info_from_ini(
                self.get_model_name(),
                self.get_oem_name(),
                version_branch,
                web_branch,
                printinfo=printinfo)
        return self._device_web_interface_info

    def get_ps_cmd(self):
        return self._ps_cmd

    def get_upload_log_sh_get_cmd(self):
        return self._upload_log_sh_get_cmd

    def get_upload_log_sh_exec_cmd(self):
        return self._upload_log_sh_exec_cmd

    # appium 连接log
    _log_level = 'error'
    _clear_cache_before_start = True

    def GetLogLevel(self):
        return self._log_level

    def NeedClearCacheBeforeStart(self):
        return self._clear_cache_before_start

    # Email 相关
    _email_host = 'smtp.exmail.qq.com'
    _email_host_port = 465
    _email_username = 'tools-reports@akuvox.com'
    _email_password = 'StarNet1023'
    _email_enable = True

    def GetEmailHost(self):
        return self._email_host

    def GetEmailHostPort(self):
        return self._email_host_port

    def GetEmailUserName(self):
        return self._email_username

    def GetEmailPassword(self):
        return self._email_password

    def GetEmailEnable(self):
        return self._email_enable

    def get_web_admin_username(self):
        return self._web_admin_username

    def get_web_admin_passwd(self):
        return self._web_admin_passwd

    def get_web_admin_password_changed(self):
        return self._web_admin_password_changed

    def get_web_custom_username(self):
        return self._web_custom_username

    def get_web_custom_passwd(self):
        return self._web_custom_passwd

    def get_web_user_username(self):
        return self._web_user_username

    def get_web_user_passwd(self):
        return self._web_user_passwd

    def get_lan_port_type(self):
        return self._lan_port_type

    # 测试文件根目录
    _test_file_root_path = root_path + '\\testfile'

    def get_test_file_root_path(self):
        return self._test_file_root_path

    # 浏览器相关
    _chrome_path = '\\Browser\\Chrome\\chromedriver.exe'

    def get_chrome_path(self):
        return self._test_file_root_path + self._chrome_path

    def get_chrome_prefs(self):
        if not self._chrome_prefs:
            self._chrome_prefs = {'profile.default_content_settings.popups': 0,
                                  'download.prompt_for_download': False,
                                  'download.default_directory': self.get_chrome_download_dir(),
                                  # 'profile.password_manager_enabled': False,
                                  # 'credentials_enable_service': False,
                                  'safebrowsing.enabled': False
                                  }
        return self._chrome_prefs

    # custom_option选项
    _custom_option = '138'

    def get_custom_option(self):
        return self._custom_option

    # 服务器地址
    _host_ip = ''

    def get_server_address(self, ip_segment=None):
        if not self._host_ip or ip_segment:
            self._host_ip = get_local_host_ip(ip_segment)
        return self._host_ip

    # 下载目录
    _http_dir = '\\Download\\HTTP\\'
    _https_dir = '\\Download\\HTTPS\\'
    _tftp_dir = '\\Download\\TFTP\\'
    _ftp_dir = '\\Download\\FTP\\'

    def get_http_dir(self):
        return self._test_file_root_path + self._http_dir

    def get_https_dir(self):
        return self._test_file_root_path + self._https_dir

    def get_tftp_dir(self):
        return self._test_file_root_path + self._tftp_dir

    def get_ftp_dir(self):
        return self._test_file_root_path + self._ftp_dir

    # 下载URL
    _http_server_root_url = ''

    def get_http_server_root_url(self, ip_segment=None):
        # HTTP服务器的根目录最好设置为testfile目录
        if self._http_server_root_url == '' or ip_segment:
            self._http_server_root_url = config_get_value_from_ini_file('environment', 'http_server_root_url')
            server_ip = self._http_server_root_url.split('http://')[-1].split('/')[0]
            if not ip_segment:
                ip_list = server_ip.split('.')
                if len(ip_list) == 4:
                    ip_segment = server_ip.split('.' + server_ip.split('.')[-1])[0]
            if self.get_server_address(ip_segment) != server_ip:
                self._http_server_root_url = self._http_server_root_url.replace(server_ip, self.get_server_address())
        return self._http_server_root_url

    def get_http_url(self):
        return self.get_http_server_root_url() + '/Download/HTTP/'

    def get_https_url(self):
        return 'https://' + self.get_server_address() + ':443' + '/Download/HTTPS/'

    def get_tftp_url(self):
        return 'tftp://' + self.get_server_address() + '/'

    def get_ftp_url(self):
        return 'ftp://' + self.get_server_address() + '/'

    # autop下载使用协议
    _pnp_use_protocol = 'https'
    _dhcp_option_43_use_protocol = 'ftp'
    _dhcp_option_66_use_protocol = 'http'
    _dhcp_option_custom_use_protocol = 'tftp'
    _manual_URL_use_protocol = 'http'

    # 获取autop的URL
    def get_manual_autop_URL(self, use_protocol=None):
        if use_protocol is not None:
            # 升级时测试使用不同的下载协议
            if use_protocol == 'http':
                return self.get_http_url()
            elif use_protocol == 'https':
                return self.get_https_url()
            elif use_protocol == 'ftp':
                return self.get_ftp_url()
            elif use_protocol == 'tftp':
                return self.get_tftp_url()
        else:
            if self._manual_URL_use_protocol == 'http':
                return self.get_http_url()
            elif self._manual_URL_use_protocol == 'https':
                return self.get_https_url()
            elif self._manual_URL_use_protocol == 'ftp':
                return self.get_ftp_url()
            elif self._manual_URL_use_protocol == 'tftp':
                return self.get_tftp_url()

    def get_pnp_url(self):
        if self._pnp_use_protocol == 'http':
            return self.get_http_url()
        elif self._pnp_use_protocol == 'https':
            return self.get_https_url()
        elif self._pnp_use_protocol == 'ftp':
            return self.get_ftp_url()
        elif self._pnp_use_protocol == 'tftp':
            return self.get_tftp_url()

    def get_dhcp_option_43_url(self):
        if self._dhcp_option_43_use_protocol == 'http':
            return self.get_http_url()
        elif self._dhcp_option_43_use_protocol == 'https':
            return self.get_https_url()
        elif self._dhcp_option_43_use_protocol == 'ftp':
            return self.get_ftp_url()
        elif self._dhcp_option_43_use_protocol == 'tftp':
            return self.get_tftp_url()

    def get_dhcp_option_66_url(self):
        if self._dhcp_option_66_use_protocol == 'http':
            return self.get_http_url()
        elif self._dhcp_option_66_use_protocol == 'https':
            return self.get_https_url()
        elif self._dhcp_option_66_use_protocol == 'ftp':
            return self.get_ftp_url()
        elif self._dhcp_option_66_use_protocol == 'tftp':
            return self.get_tftp_url()

    def get_dhcp_option_custom_url(self):
        if self._dhcp_option_custom_use_protocol == 'http':
            return self.get_http_url()
        elif self._dhcp_option_custom_use_protocol == 'https':
            return self.get_https_url()
        elif self._dhcp_option_custom_use_protocol == 'ftp':
            return self.get_ftp_url()
        elif self._dhcp_option_custom_use_protocol == 'tftp':
            return self.get_tftp_url()

    # autop文件目录
    def get_manual_URL_dir(self):
        if self._manual_URL_use_protocol == 'http':
            return self.get_http_dir()
        elif self._manual_URL_use_protocol == 'https':
            return self.get_https_dir()
        elif self._manual_URL_use_protocol == 'ftp':
            return self.get_ftp_dir()
        elif self._manual_URL_use_protocol == 'tftp':
            return self.get_tftp_dir()

    def get_pnp_dir(self):
        if self._pnp_use_protocol == 'http':
            return self.get_http_dir()
        elif self._pnp_use_protocol == 'https':
            return self.get_https_dir()
        elif self._pnp_use_protocol == 'ftp':
            return self.get_ftp_dir()
        elif self._pnp_use_protocol == 'tftp':
            return self.get_tftp_dir()

    def get_dhcp_option_43_dir(self):
        if self._dhcp_option_43_use_protocol == 'http':
            return self.get_http_dir()
        elif self._dhcp_option_43_use_protocol == 'https':
            return self.get_https_dir()
        elif self._dhcp_option_43_use_protocol == 'ftp':
            return self.get_ftp_dir()
        elif self._dhcp_option_43_use_protocol == 'tftp':
            return self.get_tftp_dir()

    def get_dhcp_option_66_dir(self):
        if self._dhcp_option_66_use_protocol == 'http':
            return self.get_http_dir()
        elif self._dhcp_option_66_use_protocol == 'https':
            return self.get_https_dir()
        elif self._dhcp_option_66_use_protocol == 'ftp':
            return self.get_ftp_dir()
        elif self._dhcp_option_66_use_protocol == 'tftp':
            return self.get_tftp_dir()

    def get_dhcp_option_custom_dir(self):
        if self._dhcp_option_custom_use_protocol == 'http':
            return self.get_http_dir()
        elif self._dhcp_option_custom_use_protocol == 'https':
            return self.get_https_dir()
        elif self._dhcp_option_custom_use_protocol == 'ftp':
            return self.get_ftp_dir()
        elif self._dhcp_option_custom_use_protocol == 'tftp':
            return self.get_tftp_dir()

    # 是否发送邮件
    _send_email_enable = True

    def get_send_email_enable(self):
        return self._send_email_enable

    def get_email_receivers(self):
        return self._email_receivers

    # 是否启用调试，如果不启用，则输出结果到HTML报告中，否则在控制台显示
    _test_debug = False

    def get_test_debug(self):
        return self._test_debug

    # 是否启用手动测试模块，当启用时，会加载manual_modules.txt文档中的模块；默认为False，则自动加载模块测试
    _manual_test_module = False

    def get_manual_test_module(self):
        return self._manual_test_module

    # 是否启用手动测试用例，当启用时，会加载manual_cases.txt文档中的用例，可以同时启用手动测试模块和用例；默认为False，则加载模块测试
    _manual_test_case = False

    def get_manual_test_case(self):
        return self._manual_test_case

    # 设置测试次数, 主要用于手动测试，默认次数1
    _test_counts = 1

    def get_test_counts(self):
        return self._test_counts

    # 输入测试设备或browser的数量
    _test_browsers_counts = 1

    def get_test_browsers_counts(self):
        return self._test_browsers_counts

    _test_apps_counts = 1

    def get_test_apps_counts(self):
        return self._test_apps_counts

    # 设置输出测试报告的方式
    _report_type = 'BeautifulReport'  # HTMLTestRunner

    def get_report_type(self):
        return self._report_type

    _upgrade_tool_path = r'\tools\AkuvoxUpgradeTool\AkuvoxUpgradeTool.exe'

    def get_upgrade_tool_path(self):
        return root_path + self._upgrade_tool_path

    _adb_key = ''

    def get_command_misc_adb_password(self):
        if self._adb_key == '':
            user_path = os.environ['USERPROFILE']
            adb_key_file = user_path + '\\.android\\adbkey.pub'
            lines = File_process.get_file_lines(adb_key_file)
            if lines:
                self._adb_key = lines[0].split('=')[0] + '='
            else:
                self._adb_key = ''
        return self._adb_key

    def get_remote_connect_type(self):
        return self._remote_connect_type

    def get_tln_or_ssh_pwd(self):
        return self._tln_or_ssh_pwd

    def get_tln_ssh_port_list(self):
        if self.get_remote_connect_type() == 'telnet' and \
                isinstance(self._tln_ssh_port_list, list) and 23 not in self._tln_ssh_port_list:
            if 22 in self._tln_ssh_port_list:
                self._tln_ssh_port_list.remove(22)
            self._tln_ssh_port_list.append(23)
        return self._tln_ssh_port_list

    def get_monkey_sh_get_cmd(self):
        return self._monkey_sh_get_cmd

    def get_monkey_sh_exec_cmd(self):
        return self._monkey_sh_exec_cmd

    def get_monkey_process_list(self):
        return self._monkey_process_list

    def get_adb_port(self):
        return self._adb_port

    def get_lan_port_ip_address(self):
        return self._lan_port_ip_address

    def get_model_name(self):
        return self._model_name

    def get_model_id_NORMAL(self):
        return self._model_id_NORMAL

    def get_series_product_name(self):
        return self._series_product_name

    def get_oem_name(self):
        return self._oem

    def get_product_model_name(self):
        return self._product_model_name

    def get_product_type_name(self):
        return self._product_type_name

    def get_web_basic_upgrade_default_time(self):
        return self._web_basic_upgrade_default_time

    def get_autop_upgrade_default_time(self):
        return self._autop_upgrade_default_time

    def get_reboot_default_time(self):
        return self._reboot_default_time

    def get_reset_default_time(self):
        return self._reset_default_time

    def get_reset_config_default_time(self):
        return self._reset_config_default_time

    def get_boot_time_after_get_ip(self):
        return self._boot_time_after_get_ip

    def get_reset_after_upgrade_enable(self):
        return self._reset_after_upgrade_enable

    def get_auto_reset_after_transition_upgrade_enable(self):
        return self._auto_reset_after_transition_upgrade_enable

    def get_screen_saver_flag(self):
        return self._screen_saver_flag

    def get_screen_power_flag(self):
        return self._screen_power_flag

    def get_screen_power_use_u2(self):
        return self._screen_power_use_u2

    def get_default_location(self):
        return self._default_location

    def get_current_activity_flag(self):
        return self._current_activity_flag

    def get_cur_activity_use_u2(self):
        return self._cur_activity_use_u2

    def get_screen_clickable_area(self):
        return self._screen_clickable_area

    def get_screen_width(self):
        return self._screen_width

    def get_screen_height(self):
        return self._screen_height

    def get_setting_pwd(self):
        return self._setting_pwd

    def get_more_pwd(self):
        return self._more_pwd

    def get_screen_size(self):
        return self._screen_size

    def get_system_bar_rect(self):
        return self._system_bar_rect

    def get_package_name(self):
        return self._package_name

    @property
    def appium_command(self):
        return self._appium_command

    @property
    def platform_version(self):
        return self._platform_version

    # 升级相关配置
    def get_firmware_ext(self):
        return self._firmware_ext

    def get_firmware_prefix(self):
        return self._firmware_prefix

    def get_firmware_suffix(self):
        return self._firmware_suffix

    def get_autop_cfg_use_mac_enable(self):
        return self._autop_cfg_use_mac_enable

    def get_autop_cfg_file_name(self):
        return self._autop_cfg_file

    def get_renamecfg_66(self):
        return self.get_dhcp_option_66_dir() + self._rename_cfg_file

    def get_devicecfg_66(self):
        return self.get_dhcp_option_66_dir() + self._autop_cfg_file

    def get_config_firmware_url_66(self):
        return 'Config.Firmware.Url = ' + self.get_dhcp_option_66_url() + self._old_firmware_file

    def get_renamecfg_43(self):
        return self.get_dhcp_option_43_dir() + self._rename_cfg_file

    def get_devicecfg_43(self):
        return self.get_dhcp_option_43_dir() + self._autop_cfg_file

    def get_config_firmware_url_43(self):
        return 'Config.Firmware.Url = ' + self.get_dhcp_option_43_url() + self._old_firmware_file

    def get_renamecfg_URL(self):
        return self.get_manual_URL_dir() + self._rename_cfg_file

    def get_devicecfg_URL(self):
        return self.get_manual_URL_dir() + self._autop_cfg_file

    def get_config_firmware_url_manual_URL(self):
        return 'Config.Firmware.Url = ' + self.get_manual_autop_URL() + self._old_firmware_file

    def get_renamecfg_custom(self):
        return self.get_dhcp_option_custom_dir() + self._rename_cfg_file

    def get_devicecfg_custom(self):
        return self.get_dhcp_option_custom_dir() + self._autop_cfg_file

    def get_config_firmware_url_custom(self):
        return 'Config.Firmware.Url = ' + self.get_dhcp_option_custom_url() + self._old_firmware_file

    def get_renamecfg_pnp(self):
        return self.get_pnp_dir() + self._rename_cfg_file

    def get_devicecfg_pnp(self):
        return self.get_pnp_dir() + self._autop_cfg_file

    def get_config_firmware_url_pnp(self):
        return 'Config.Firmware.Url = ' + self.get_pnp_url() + self._old_firmware_file

    # 导入文件目录
    def get_import_file(self, file_name):
        series_file = '%s\\config_file_import\\%s\\NORMAL\\%s' \
                      % (self._test_file_root_path, self._series_product_name, file_name)
        model_normal_file = '%s\\config_file_import\\%s\\%s\\NORMAL\\%s' \
                            % (self._test_file_root_path, self._series_product_name, self._model_name, file_name)
        model_oem_file = '%s\\config_file_import\\%s\\%s\\%s\\%s' \
                         % (self._test_file_root_path, self._series_product_name, self._model_name,
                            self._oem, file_name)
        if os.access(model_oem_file, os.F_OK):
            import_file = model_oem_file
        elif os.access(model_normal_file, os.F_OK):
            import_file = model_normal_file
        elif os.access(series_file, os.F_OK):
            import_file = series_file
        else:
            import_file = '%s\\config_file_import\\COMMON\\%s' % (self._test_file_root_path, file_name)

        if import_file.endswith('\\'):  # 要导入的文件为空
            import_file = ''
        return import_file

    def get_android_chrome_driver(self):
        series_file = '%s\\testcase\\common\\AndroidChromeDriver\\%s\\NORMAL\\chromedriver.exe' \
                      % (root_path, self._series_product_name)
        model_normal_file = '%s\\testcase\\common\\AndroidChromeDriver\\%s\\%s\\NORMAL\\chromedriver.exe' \
                            % (root_path, self._series_product_name, self._model_name)
        model_oem_file = '%s\\testcase\\common\\AndroidChromeDriver\\%s\\%s\\%s\\chromedriver.exe' \
                         % (root_path, self._series_product_name, self._model_name, self._oem)
        if os.access(model_oem_file, os.F_OK):
            chrome_driver = model_oem_file
        elif os.access(model_normal_file, os.F_OK):
            chrome_driver = model_normal_file
        elif os.access(series_file, os.F_OK):
            chrome_driver = series_file
        else:
            chrome_driver = '%s\\testcase\\common\\AndroidChromeDriver\\COMMON\\chromedriver.exe' % root_path
        return chrome_driver

    def get_file_import_dir(self):
        """弃用"""
        if self._series_product_name == 'COMMON':
            return self._test_file_root_path + '\\config_file_import\\COMMON'
        else:
            return self._test_file_root_path + '\\config_file_import\\%s\\NORMAL' % self._series_product_name

    # 图片对比目录
    def get_image_cmp_file(self, file_name):
        series_file = '%s\\IMG_compare\\%s\\NORMAL\\%s' \
                      % (self._test_file_root_path, self._series_product_name, file_name)
        model_normal_file = '%s\\IMG_compare\\%s\\%s\\NORMAL\\%s' \
                            % (self._test_file_root_path, self._series_product_name, self._model_name, file_name)
        model_oem_file = '%s\\IMG_compare\\%s\\%s\\%s\\%s' % (self._test_file_root_path, self._series_product_name,
                                                              self._model_name, self._oem, file_name)
        if os.access(model_oem_file, os.F_OK):
            image_cmp_file = model_oem_file
        elif os.access(model_normal_file, os.F_OK):
            image_cmp_file = model_normal_file
        elif os.access(series_file, os.F_OK):
            image_cmp_file = series_file
        else:
            image_cmp_file = '%s\\IMG_compare\\COMMON\\%s' % (self._test_file_root_path, file_name)
        return image_cmp_file

    # 导入Autop配置文件
    def get_config_import_file(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\config_file_import.cfg' % self._model_name

    def get_config_import_file_R20(self):
        # R20 只支持文件名里有 英文+数字.
        return self._test_file_root_path + '\\config_file_import\\%s\\configfileimport.cfg' % self._model_name

    # 导入config配置文件
    def get_config_import_file_tgz(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\config_file_import.tgz' % self._model_name

    # 导入phonebook文件
    def get_phonebook_import_file(self):
        return self._test_file_root_path + '\\config_file_import\\%s\\phonebook.xml' % self._model_name

    # autop配置文件模板
    def get_autop_config_file(self):
        return self._test_file_root_path + '\\autop_config_file\\%s.cfg' % self._model_name

    def get_autop_config_template_file(self):
        return self._test_file_root_path + '\\autop_config_template\\%s\\autop_config_template_%s_%s.cfg' \
            % (self._model_name, self._model_name, self._oem)

    # autop AES加密配置文件
    def get_aes_autop_config_file(self, file=None):
        if not file:
            file = '%s.cfg' % self._model_name
        return self._test_file_root_path + '\\autop_aes_file\\%s' % file

    # 本地安装包的路径
    def get_local_firmware_path(self, version=None):
        if not version:
            version = param_get_rom_version()
        if version != 'unknown':
            local_firmware_path = (f'{self._test_file_root_path}\\Firmware\\{self._model_name}\\'
                                   f'{self._firmware_prefix}{version}{self._firmware_suffix}{self._firmware_ext}')
        else:
            local_firmware_path = (f'{self._test_file_root_path}\\Firmware\\{self._model_name}\\'
                                   f'{self._firmware_prefix}{self._model_id_NORMAL}'
                                   f'{self._firmware_suffix}{self._firmware_ext}')
        return local_firmware_path

    def get_local_firmware_http_url(self):
        """获取upgrade_firmware目录下升级包的HTTP URL，HTTP服务器跟目录为testfile"""
        http_url = self.get_local_firmware_path(). \
            replace(self._test_file_root_path, self.get_http_server_root_url()).replace('\\', '/')
        return http_url

    def get_upgrade_firmware_dir(self, device_name=False):
        upgrade_firmware_dir = '%s\\upgrade_firmware\\%s\\' % (self._test_file_root_path, self._model_name)
        if device_name:
            upgrade_firmware_dir = upgrade_firmware_dir + '%s\\' % self._device_name
        if not os.path.exists(upgrade_firmware_dir):
            os.makedirs(upgrade_firmware_dir)
        return upgrade_firmware_dir

    def get_upgrade_firmware_http_url(self, filename, device_name=False):
        """获取upgrade_firmware目录下升级包的HTTP URL，HTTP服务器跟目录为testfile"""
        http_url = self.get_upgrade_firmware_dir(device_name). \
            replace(self._test_file_root_path, self.get_http_server_root_url()).replace('\\', '/')
        http_url = http_url + filename
        return http_url

    # 默认的升级包路径，10.75 13.55等
    def get_remote_firmware_dir(self):
        return self._remote_firmware_dir

    def get_test_data(self, data_file=None, print_data=False):
        """获取系列机型对应的testdata"""
        version_branch_info = param_get_version_branch_info()
        if not version_branch_info:
            aklog_printf('缺少分支版本信息，获取旧版本失败')
            return None
        series_products = config_get_series(self._model_name)
        series_module_name = config_get_series_module_name(series_products)
        version_branch = version_branch_info.get('%s_branch' % series_module_name, '')
        if version_branch and '.' in version_branch:
            version_branch = version_branch.split('.')[0]
        series_module_root_path = config_get_series_module_sub_path(self._model_name, version_branch)
        test_data_dir = os.path.join(series_module_root_path, 'TestData')
        if not os.path.exists(test_data_dir):
            test_data_dir = os.path.join(root_path, 'testdata', series_products, version_branch)
        test_data = xml_read_all_test_data(test_data_dir, self._model_name, self._oem, data_file)
        if print_data:
            aklog_debug(test_data)
        return test_data

    def download_firmware_to_old_firmware_dir(self, firmware_version, firmware_path, old_firmware_dir):
        """将指定的升级包下载到本地Upgrade目录下"""
        aklog_debug()
        if not os.path.exists(old_firmware_dir):
            os.makedirs(old_firmware_dir)
        old_firmware_path = '%s\\%s_%s__%s%s' % (old_firmware_dir, self._model_name, self._oem,
                                                 firmware_version, self.get_firmware_ext())
        download_result = False

        # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
        cmd_waiting_for_network_rate_to_drop()

        if 'ftp://' in firmware_path:
            aklog_info("将升级包从FTP服务器下载到本地目录")
            ftp_info = get_ftp_info_from_url(firmware_path)
            ftp_connect_mode = True  # False为PORT模式
            for k in range(2):
                ftp_client = FtpClient(ftp_info['host'], ftp_info['port'], ftp_info['user_name'], ftp_info['password'])
                ftp_client.login(ftp_connect_mode)
                try:
                    download_result = ftp_client.download_file(old_firmware_path, ftp_info['remote_file'])
                except:
                    print(traceback.format_exc())
                    ftp_connect_mode = False
                    return None
                ftp_client.close()
                if download_result:
                    break
                else:
                    ftp_connect_mode = False
                    continue
        elif 'http://' in firmware_path:
            aklog_info("将升级包从http服务器下载到本地目录")
            try:
                r = requests.get(firmware_path, timeout=600)
                with open(old_firmware_path, 'wb') as f:
                    f.write(r.content)
                download_result = True
            except:
                print(traceback.format_exc())
                download_result = False
                return None
        else:
            aklog_info("将升级包拷贝到本地目录")
            for x in range(2):
                download_result = File_process.copy_file(firmware_path, old_firmware_path)
                if download_result:
                    break

        if download_result:
            return old_firmware_path
        else:
            return None

    # 网页升级到旧版本的升级包路径，autop升级时也会复制到autop下载目录
    def get_old_firmware(self, version=None, force_replace=False, exclude_versions=None):
        r"""
        获取旧版本升级包, 并下载文件到: \testfile\old_firmware_version\机型\分支版本下
        force_replace:
        Args:
            version (): 获取指定版本号的旧版本升级包
            force_replace (): 强制从UpgradeCover.xml下载替换
            exclude_versions (): 要排除的版本，比如新版本

        Returns: 旧版本升级包路径

        """
        aklog_printf()
        if self._model_name == 'COMMON':
            aklog_printf('缺少型号，如果是设备终端，可能需要继承重写对应型号的config模块，不是的话可忽略')
            return None
        else:
            version_branch_info = param_get_version_branch_info()
            if not version_branch_info:
                aklog_printf('缺少分支版本信息，获取旧版本失败')
                return None
            series_products = config_get_series(self._model_name)
            series_module_name = config_get_series_module_name(series_products)
            version_branch = version_branch_info.get('%s_branch' % series_module_name, '')
            # 先判断是否存在子分支版本
            sub_version_branch = ''
            if version_branch and '.' in version_branch:
                sub_version_branch = version_branch.split('.')[1]
                version_branch = version_branch.split('.')[0]
                aklog_printf('存在子分支版本：%s' % sub_version_branch)
            # 先获取分支目录下的升级包
            old_firmware_dir = os.path.join(self._test_file_root_path, 'old_firmware_version', self._model_name,
                                            version_branch)
            if not os.path.exists(old_firmware_dir):
                os.makedirs(old_firmware_dir)
            old_firmware_path = ''
            files = File_process.get_files_with_ext_from_path(old_firmware_dir, self._firmware_ext)
            new_files = []
            if files:
                for file in files:
                    if '%s_%s' % (self._model_name, self._oem) in file:
                        new_files.append(file)
                if not new_files:
                    for file in files:
                        if '%s_NORMAL' % self._model_name in file:
                            new_files.append(file)
                for file in new_files:
                    # 排除一些版本，比如新版本
                    if exclude_versions:
                        is_exclude = False
                        for exclude_version in exclude_versions:
                            if exclude_version in file:
                                is_exclude = True
                                break
                        if is_exclude:
                            continue
                    # 如果指定版本号，则使用指定版本号的升级包，否则使用第一个匹配型号和OEM的升级包
                    if not version or version in file:
                        old_firmware_path = os.path.join(old_firmware_dir, file)
                        break

            if force_replace or not old_firmware_path:
                # 分支目录下不存在升级包，先从UpgradeCover.xml文件获取相同分支的最新版本下载下来
                upgrade_cover_all_data = self.get_test_data('UpgradeCover.xml')
                upgrade_cover_data = None
                if sub_version_branch:
                    upgrade_cover_data_name = 'UpgradeCover__%s' % sub_version_branch
                    if upgrade_cover_data_name in upgrade_cover_all_data:
                        upgrade_cover_data = upgrade_cover_all_data[upgrade_cover_data_name]
                if not upgrade_cover_data:
                    upgrade_cover_data = upgrade_cover_all_data.get('UpgradeCover')

                if upgrade_cover_data:
                    for data in upgrade_cover_data:
                        if data['firmware_version'] == param_get_rom_version():
                            continue
                        if exclude_versions and data['firmware_version'] in exclude_versions:
                            continue
                        firmware_version = data['firmware_version']
                        firmware_path = data['firmware_path']
                        aklog_info('从UpgradeCover.xml获取到的旧版本号：%s' % firmware_version)

                        if old_firmware_path and os.path.exists(old_firmware_path) and \
                                firmware_version in old_firmware_path:
                            break
                        else:
                            if old_firmware_path and os.path.exists(old_firmware_path):
                                File_process.remove_file(old_firmware_path)
                            old_firmware_path = self.download_firmware_to_old_firmware_dir(
                                firmware_version, firmware_path, old_firmware_dir)
                            if not old_firmware_path:
                                # 如果从UpgradeCover中的链接下载升级包失败，则换一个版本
                                aklog_warn('%s 下载升级包失败' % firmware_path)
                                continue
                            else:
                                break
                else:
                    aklog_error('UpgradeCover信息为空，请检查')

            if not old_firmware_path:
                # 分支目录下不存在升级包，并且从UpgradeCover.xml文件下载失败，那么在机型目录下查找，然后将升级包移动到对应分支目录下
                version_branch_dir = old_firmware_dir
                old_firmware_dir = os.path.join(self._test_file_root_path, 'old_firmware_version', self._model_name)
                file_paths = File_process.get_file_paths_with_ext_from_dir(old_firmware_dir, self._firmware_ext)
                new_file_paths = []
                if file_paths:
                    for file_path in file_paths:
                        file = os.path.split(file_path)[-1]
                        if '%s_%s' % (self._model_name, self._oem) in file:
                            new_file_paths.append(file_path)
                    if not new_file_paths:
                        for file_path in file_paths:
                            file = os.path.split(file_path)[-1]
                            if '%s_NORMAL' % self._model_name in file:
                                new_file_paths.append(file_path)
                    for file_path in new_file_paths:
                        # 如果指定版本号，则使用指定版本号的升级包，否则使用第一个匹配型号和OEM的升级包
                        file = os.path.split(file_path)[-1]
                        if not version or version in file:
                            old_firmware_path = file_path
                            break
                    if version_branch_dir != old_firmware_dir:
                        File_process.create_dir(version_branch_dir)
                        dst_file = os.path.join(version_branch_dir, os.path.split(old_firmware_path)[-1])
                        if File_process.move_file(old_firmware_path, dst_file):  # 将升级包移动到分支版本目录下
                            old_firmware_path = dst_file

            if not old_firmware_path:
                # 如果没找到指定格式的升级包，默认先设置一个升级包路径做兼容
                old_firmware_path = os.path.join(old_firmware_dir, '%s%s' % (self._model_name, self._firmware_ext))
            if not os.path.exists(old_firmware_path):
                old_firmware_path = None
            aklog_printf('%s, %s, old_firmware_path: %s' % (self._model_name, self._oem, old_firmware_path))
            self._old_firmware_path = old_firmware_path
            return old_firmware_path

    def get_old_firmware_path(self, version=None, force_replace=False):
        if not self._old_firmware_path:
            self._old_firmware_path = self.get_old_firmware(version, force_replace)
        return self._old_firmware_path

    def get_old_firmware_file(self):
        return self._old_firmware_file

    def get_old_firmware_version(self, version=None, force_replace=False):
        if not self._old_firmware_path:
            self._old_firmware_path = self.get_old_firmware(version, force_replace)
        if not self._old_firmware_path:
            return ''
        if os.path.getsize(self._old_firmware_path) == 0:
            aklog_warn('old firmware 文件大小为0!!')
            return ''
        file_dir, file = os.path.split(self._old_firmware_path)
        file_name, ext = os.path.splitext(file)
        if '__' in file_name:
            version = file_name.split('__')[1]
        else:
            version = ''
        return version

    def get_ini_dict(self, file):
        """
        key: value,  key都处理成小写
        """
        # 先读之后去除bom文件的格式
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        if content.startswith('\ufeff'):
            content = content.replace('\ufeff', '')
        config = configparser.RawConfigParser()
        config.read_string(content)
        retdict = {}
        for each_section in config.sections():
            retdict[each_section] = {}
            for each_option in config.options(each_section):
                retdict[each_section][each_option.lower()] = config.get(each_section, each_option)
        return retdict

    def __intercom_get_version_branch(self, version):
        """
        x.x.10.1xx:  根据版本号获取分支版本
        """
        bigver = version.split('.')[2]
        subver = version.split('.')[-1]
        if len(subver) == 3:
            subver = subver[0]
        else:
            subver = '0'
        return bigver + '.' + subver

    def __intercom_get_shared_ini_config(self):
        """
        读取对讲终端: \\192.168.254.9\对讲质量部\00_自动化挂测配置\系列.ini文件
        {'R20SV823':
            {'release_ver_v1': 'http://10.38.255.1:18165/Rom/rom-R20_v11.0_AKCLOUDUNION_release.SV82X/320.30.11.6/320.30.11.6.rom',
            'release_ver_v10.1': '\\\\192.168.10.75\\AndroidSpace\\1.1.10.101.zip',
            'release_ver_v10.2': '\\\\192.168.10.75\\AndroidSpace\\1.1.10.201.zip'},
            }
        }
        """
        server = '192.168.254.9'
        username = 'IntercomSQA'
        password = 'Akuvox@2024'
        share_name = '对讲质量部'
        series = param_get_seriesproduct_name().lower()
        if 'indoor' in series:
            file_path = '00_自动化挂测配置/室内机.ini'
        elif 'access' in series:
            file_path = '00_自动化挂测配置/门禁.ini'
        else:
            file_path = '00_自动化挂测配置/门口机.ini'
        try:
            from smb.SMBConnection import SMBConnection
            server_name = 'xxx'
            local_name = ''
            conn = SMBConnection(username, password, local_name, server_name, use_ntlm_v2=True)
            connected = conn.connect(server, 445)
            if connected:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.ini', mode='w', dir=None, prefix='temp_',
                                                 encoding='utf-8') as temp_file:
                    temp_file_path = temp_file.name
                    with open(temp_file_path, 'wb') as file_obj:
                        conn.retrieveFile(share_name, file_path, file_obj)
                retdict = self.get_ini_dict(temp_file_path)
                File_process.remove_file(temp_file_path)
                return retdict
            else:
                aklog_warn('连接共享文件夹失败!')
                return False
        except:
            aklog_warn('访问对讲终端共享文件夹异常!!!!')
            print(traceback.format_exc())
            return False

    def __intercom_get_last_release_firmware_download_path(self, nowversion):
        """
        从共享文件夹\自动化运行配置, 获取非自动化人员指定的上一个release版本的http,ftp,共享文件夹路径.
        """
        model = param_get_model_name()
        if model == 'IPH81':
            # ph81 model 特殊
            model = 'PH81'
        ret = self.__intercom_get_shared_ini_config()
        if not ret:
            aklog_warn(r'获取: 共享文件夹\自动化运行配置信息失败!!!')
            return False
        if not ret.get(model):
            aklog_warn(r'获取: 共享文件夹\自动化运行配置\机型: {} 信息失败!!!'.format(model))
            return False
        branch = self.__intercom_get_version_branch(nowversion)
        if not ret.get(model).get('release_ver_v{}'.format(branch)):
            aklog_warn(r'获取: 共享文件夹\自动化运行配置\机型: {} 分支: {} 信息失败!!!'.format(model, branch))
            if not ret.get(model).get('release_ver_normal'):
                # 切分支或分支没有指定版本时，看看是否有release_ver_normal(LTS版本或推荐版本)可以用来升级
                aklog_warn('获取: 共享文件夹\自动化运行配置\机型: {} 分支: normal 信息失败!!!'.format(model))
                return False
            file_path = ret.get(model).get('release_ver_normal')
        else:
            file_path = ret.get(model).get('release_ver_v{}'.format(branch))
        if not file_path.endswith('.rom') and not file_path.endswith('.zip'):
            aklog_warn('共享文件夹: {} release信息没有指定到.rom/.zip'.format(model))
            return False
        else:
            aklog_info('共享文件夹配置上一个release信息: {}'.format(file_path))
            return file_path

    def __intercom_download_firmware(self, remote_filepath, local_filepath):
        """
        从 ftp, http, 共享文件夹下载文件.
        """
        if os.path.exists(local_filepath) and os.path.getsize(local_filepath) > 100:
            aklog_info('待下载文件: {} 已经存在'.format(local_filepath))
            return True
        os.makedirs(os.path.dirname(local_filepath), exist_ok=True)
        if 'ftp://' in remote_filepath:
            judge_auth = re.search('ftp://.*:.*@', remote_filepath)
            if not judge_auth:
                # 如果url不带账号密码
                username = "ftp-guest"
                password = "Akuvox2024!"
                remote_filepath = remote_filepath.replace("ftp://", f"ftp://{username}:{password}@")
                aklog_info('ftp下载路径为: ' + remote_filepath)
            ftp_info = get_ftp_info_from_url(remote_filepath)
            ftp_connect_mode = True  # False为PORT模式
            for k in range(2):
                ftp_client = FtpClient(ftp_info['host'], ftp_info['port'], ftp_info['user_name'], ftp_info['password'])
                ftp_client.login(ftp_connect_mode)
                try:
                    download_result = ftp_client.download_file(local_filepath, ftp_info['remote_file'])
                except:
                    print(traceback.format_exc())
                    ftp_connect_mode = False
                    return None
                ftp_client.close()
                if download_result:
                    break
                else:
                    ftp_connect_mode = False
                    continue
        elif 'http://' in remote_filepath:
            aklog_info('http下载路径为: ' + remote_filepath)
            try:
                r = requests.get(remote_filepath, timeout=600)
                r.raise_for_status()  # 如果下载包时not found或服务器错误，抛出异常
                with open(local_filepath, 'wb') as f:
                    f.write(r.content)
                download_result = True
            except:
                download_result = False
                print(traceback.format_exc())
                return None
        else:
            aklog_info('共享文件夹下载路径为: ' + remote_filepath)
            for x in range(2):
                download_result = File_process.copy_file(remote_filepath, local_filepath)
                if download_result:
                    break
        if download_result:
            return local_filepath
        else:
            return None

    def intercom_get_last_release_version(self):
        """从共享文件夹获取上一个发布版本的版本号"""
        aklog_debug()
        now_ver = param_get_rom_version()
        download_path = self.__intercom_get_last_release_firmware_download_path(now_ver)
        if not download_path:
            return False
        version = re.findall(r'\d+\.\d+\.\d+\.\d+', str(download_path))
        if not version:
            aklog_error('获取上一个release版本失败!')
            return False
        aklog_info('上一个release 版本号: {}'.format(version[-1]))
        return version[-1]

    def intercom_get_last_release_romfile(self):
        """从共享文件夹获取上一个发布版本的本地地址, 下载到 \\testfile\\last_release_version\\x.x.x.x.rom"""
        aklog_debug()
        now_ver = param_get_rom_version()
        download_path = self.__intercom_get_last_release_firmware_download_path(now_ver)
        if not download_path:
            aklog_error('下载上一个release版本失败!')
            return False
        try:
            file_name = re.search(r'.+(/|\\)(\d+\.\d+\.\d+\.\d+.*?(.rom|.zip))', str(download_path)).group(2)
        except:
            file_name = ''
        if not file_name:
            aklog_error('从下载url中获取文件名信息失败!!!')
            return False

        firmware_dir = os.path.join(self._test_file_root_path, 'last_release_version')
        for i in os.listdir(firmware_dir):
            if i == file_name:
                pass
            else:
                File_process.remove_file(os.path.join(firmware_dir, i))
        local_file_path = os.path.join(firmware_dir, file_name)
        result = self.__intercom_download_firmware(download_path, local_file_path)
        if not result:
            aklog_error('下载上一个release版本失败: {}'.format(download_path))
            return False
        aklog_info('成功下载上一个release版本到本地: {}'.format(local_file_path))
        return local_file_path

    # 本地BAT监控路径
    def get_bat_monitor_path(self):
        return self._test_file_root_path + '\\BatMonitor\\%s\\test%s' % (self._model_name, self._firmware_ext)

    # 浏览器相关
    def get_chrome_download_dir(self):
        """
        2023.6.27，Jason：相同机型在一个环境下同时跑，会存在网页导出文件互相覆盖的问题，
        因此将下载目录设置到Results目录下，每一次执行都会新建个保存log的目录，不会冲突
        """
        if aklog_get_result_dir():
            path = aklog_get_result_dir() + '\\ChromeDownload\\%s\\' % self._model_name
        else:
            path = self._test_file_root_path + '\\Browser\\Chrome_Download\\%s\\' % self._model_name

        if self._device_name:
            path = path + self._device_name + '\\'
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def get_autop_export_file_path(self):
        return self.get_chrome_download_dir() + 'autop_config_template.cfg'

    def get_config_file_path(self):
        return self.get_chrome_download_dir() + 'config.tgz'

    def get_phonebook_export_file_path(self):
        return self.get_chrome_download_dir() + 'PhoneContacts.tgz'

    def get_macwirte_path(self):
        macwirte_path = root_path + '\\tools\\MACWrite\\%s\\MACWriter.exe' % self._model_name
        return macwirte_path

    def get_maccheck_path(self):
        maccheck_path = root_path + '\\tools\\MACCheck\\%s\\MACCheck.exe' % self._model_name
        return maccheck_path

    def get_selftestdassistant_path(self):
        path = root_path + self._selftestdassistant_path
        return path

    def get_accesscontrolfactorytool_path(self):
        access_control_factory_tool_path = root_path + '\\tools\\AccessControlFactoryTool\\%s\\' \
                                                       '嵌入式楼宇产品生产测试工具.exe' % self._model_name
        return access_control_factory_tool_path

    def get_ringback_export_file_path(self):
        return self.get_chrome_download_dir() + 'RingBack.wav'

    def get_opensucc_export_file_path(self):
        return self.get_chrome_download_dir() + 'OpenDoor.wav'

    def get_openfailed_export_file_path(self):
        return self.get_chrome_download_dir() + 'OpenDoorFailed.wav'

    def get_openinside_export_file_path(self):
        return self.get_chrome_download_dir() + 'openlocksuccess.wav'

    def get_openinside_export_file_path_v62(self):
        return self.get_chrome_download_dir() + 'OpenDoorInside.wav'

    def get_trigger_manager_export_file_path(self):
        return self.get_chrome_download_dir() + 'TriggerButton.wav'

    def get_openoutside_export_file_path(self):
        return self.get_chrome_download_dir() + 'openlocksuccess.wav'

    def get_cardsetting_export_file_path(self):
        return self.get_chrome_download_dir() + 'RFkey.tgz'

    def get_export_pcap_file(self):
        return self.get_chrome_download_dir() + 'phone.pcap'

    def get_export_user_file(self):
        return self.get_chrome_download_dir() + 'UserData.tgz'

    # 导出的system log文件

    def get_reboot_clear_syslog(self):
        return self._reboot_clear_syslog

    def get_default_export_syslog_type(self):
        return self._default_export_syslog_type

    def get_device_log_file(self):
        return self._test_file_root_path + '\\Device_log\\%s\\' % self._model_name

    def get_log_file_name(self):
        return self._log_file_name

    def get_call_log_export_file_path(self):
        return self.get_chrome_download_dir() + 'CallLog.tgz'

    # 联系人导入文件
    def get_contacts_export_file_path(self):
        return self.get_chrome_download_dir() + 'PhoneContacts.tgz'

    def get_contacts_import_xml_file_path(self):
        return self.get_import_file('contact.xml')

    def get_contacts_import_csv_file_path(self):
        return self.get_import_file('contact.csv')

    def get_contacts_import_error_xml_file_path(self):
        return self.get_import_file('error_contact.xml')

    def get_contacts_import_error_csv_file_path(self):
        return self.get_import_file('error_contact.csv')

    # 截图文件导出
    def get_screenshots_export_file_path(self):
        return self.get_chrome_download_dir() + 'screenshots.png'
