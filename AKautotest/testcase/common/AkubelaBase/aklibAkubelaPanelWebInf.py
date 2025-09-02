# -*- coding: utf-8 -*-

import sys
import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *
import hashlib
import time


class AkubelaPanelWebInf(object):

    # region 初始化

    def __init__(self):
        self.web_branch = 'PANELWEB1_0'
        self.username = 'admin'
        self.password = 'Ak#123456'
        self.new_pwd = 'Ak#123456'  # 强制修改的新密码
        self.encrypt_password = ''
        self.base_url = ''
        self.host = ''
        self.device_info = None
        self.device_name = ''
        self.device_ip = ''
        self.device_mac = ''
        self.device_config = None
        self.api: Optional[ApiRequests] = None
        self.headers = {}
        self.token = ''
        self.interface_info = None
        self.config_info = None
        self.enabled_option = None
        self._rom_version = ''
        self.tln: Optional[TelnetConnection] = None
        self.ssh: Optional[SSHConnection] = None
        self.tln_ssh_port_list = None
        self.tln_ssh_pwd_list = None
        self.version_branch = None
        self.force_replace_old_version = False
        self.model_name = ''
        self.oem_name = ''
        self.test_file_root_path = ''
        self.capture_syslog_enable = False

    def init(self, device_info, device_config):
        """
        初始化用户web接口信息
        """
        self.device_info = device_info
        self.device_name = self.device_info['device_name']
        self.device_ip = self.device_info.get('ip')
        if 'MAC' in self.device_info:
            self.device_mac = self.device_info['MAC']
        elif 'mac' in self.device_info:
            self.device_mac = self.device_info['mac']

        self.device_config = device_config
        self.username = self.device_config.get_web_admin_username()
        self.password = self.device_config.get_web_admin_passwd()
        self.model_name = self.device_config.get_model_name()
        self.oem_name = self.device_config.get_oem_name()

        self.interface_info = config_parse_web_interface_info_from_yaml(
            self.model_name, self.oem_name, self.web_branch)
        self.config_info = self.interface_info['web_config_info']
        self.enabled_option = self.interface_info['enable_option']

        self.host = 'http://%s' % self.device_ip
        self.base_url = 'http://%s/web' % self.device_ip
        self.api = ApiRequests(self.device_name)

        self.tln_ssh_port_list = self.device_config.get_tln_ssh_port_list()
        self.tln_ssh_pwd_list = self.device_config.get_tln_or_ssh_pwd()
        self.tln = TelnetConnection(
            self.device_ip, self.tln_ssh_port_list, 'root', self.tln_ssh_pwd_list, self.device_name)
        self.ssh = SSHConnection(
            self.device_ip, self.tln_ssh_port_list, 'root', self.tln_ssh_pwd_list, self.device_name)

        # 获取module机型分支目录下TestFile路径
        if not self.test_file_root_path and self.version_branch:
            self.test_file_root_path = config_get_series_module_sub_path(
                self.model_name, self.version_branch, 'TestFile')

    @property
    def rom_version(self):
        return self._rom_version

    @rom_version.setter
    def rom_version(self, value):
        self._rom_version = value

    def put_rom_version(self, rom_version):
        self._rom_version = rom_version

    def start_and_login(self):
        return self.login()

    def web_env_init(self):
        pass

    def browser_close_and_quit(self):
        pass

    # endregion

    # region 通用API

    def api_get(self, path: str, params=None, fail_return_resp=False):
        """发送get请求"""
        if path.startswith('/'):
            path = path[1:]
        url = f'{self.base_url}/{path}'
        if params:
            resp = self.api.get(url=url, headers=self.headers, params=params, fail_return_resp=fail_return_resp)
        else:
            resp = self.api.get(url=url, headers=self.headers, fail_return_resp=fail_return_resp)
        if not resp:
            aklog_error('api get fail')
            return None
        try:
            ret = resp.json()
            if ret['retcode'] == 0:
                aklog_debug('api get OK')
                return ret
            else:
                aklog_error('api get fail: ' + str(resp.text))
                if fail_return_resp:
                    return ret
                else:
                    return None
        except Exception as e:
            aklog_error('api get Fail: ' + str(resp.text))
            if fail_return_resp:
                raise e
            else:
                return None

    def api_post(self, data, path=None, timeout=60, fail_return_resp=False):
        """发送post请求"""
        if path:
            if path.startswith('/'):
                path = path[1:]
            url = f'{self.base_url}/{path}'
        else:
            url = self.base_url
        if data and isinstance(data, dict):
            data = json.dumps(data)
        resp = self.api.post(url=url, headers=self.headers, data=data, timeout=timeout,
                             fail_return_resp=fail_return_resp)
        if not resp:
            aklog_error('api post fail')
            return False
        try:
            ret = resp.json()
            if ret['retcode'] == 0:
                aklog_debug('api post OK')
                return ret
            else:
                aklog_error('api post fail: ' + str(resp.text))
                if fail_return_resp:
                    return ret
                else:
                    return False
        except Exception as e:
            aklog_error('api post Fail: ' + str(resp.text))
            if fail_return_resp:
                raise e
            else:
                return None

    def api_post_file(self, path, file, fail_return_resp=False, timeout=None):
        """发送post请求上传文件"""
        if path:
            if path.startswith('/'):
                path = path[1:]
            url = f'{self.base_url}/{path}'
        else:
            url = self.base_url

        file_name = os.path.split(file)[1]
        files = {'file': (file_name, open(file, 'rb'), 'application/octet-stream')}
        resp = self.api.post(url=url, headers=self.headers, files=files, timeout=timeout,
                             fail_return_resp=fail_return_resp)
        if not resp:
            aklog_debug('api post file fail')
            return False
        try:
            ret = resp.json()
            if int(ret['retcode']) == 0:
                aklog_debug('api post file OK')
                return ret
            else:
                aklog_debug('api post file Fail: %s' % resp.text)
                if fail_return_resp:
                    return ret
                else:
                    return False
        except Exception as e:
            aklog_error('api post file Fail: ' + str(resp.text))
            if fail_return_resp:
                raise e
            else:
                return None

    def api_download(self, path_or_url, save_path=None, **kwargs):
        """下载/导出文件"""
        if path_or_url.startswith('http'):
            url = path_or_url
        else:
            if path_or_url.startswith('/'):
                path_or_url = path_or_url[1:]
            url = f'{self.base_url}/{path_or_url}'
        resp = self.api.get(url=url, headers=self.headers, **kwargs)
        if not resp:
            aklog_error('api download fail')
            return False
        if save_path:
            with open(save_path, "wb") as f:
                f.write(resp.content)
            aklog_info('api download ok, file: %s' % save_path)
            return True
        # 如果不保存到文件，则返回下载的数据
        return resp

    # endregion

    # region 登录登出

    def login(self, return_resp=False) -> Union[dict, bool]:
        """登录"""
        self.get_web_status()
        # 判断是否已登录
        if self.token and self.headers and self.is_login():
            return True
        checked_pwd_list = []
        for i in range(3):
            self.encrypt_password = self.get_encrypt_password(self.password)
            if not self.encrypt_password:
                return False
            aklog_info('%s:%s 开始登录' % (self.username, self.password))
            checked_pwd_list.append(self.password)
            data = {
                "target": "login",
                "action": "login",
                "data": {
                    "userName": self.username,
                    "password": self.encrypt_password
                },
                "session": self.token,
                "web": "1"
            }
            resp = self.api_post(data, fail_return_resp=True)
            try:
                if resp and resp['retcode'] == 0:
                    self.token = resp['data']['token']
                    isFirstLogin = resp['data']['isFirstLogin']
                    self.headers['Cookie'] = 'onRemCookie=false; UserName=%s; Password=%s; token=%s' \
                                             % (self.username, self.encrypt_password, self.token)
                    aklog_info('%s:%s 登录成功, token: %s, isFirstLogin: %s'
                               % (self.username, self.password, self.token, isFirstLogin))
                    if return_resp:
                        return resp
                    else:
                        return True
                else:
                    old_pwd = self.password
                    if self.password != 'admin':
                        self.password = 'admin'
                    elif self.password != self.new_pwd:
                        self.password = self.new_pwd

                    if self.password in checked_pwd_list:
                        break
                    aklog_warn('%s:%s 登录失败，更换密码重新登录' % (self.username, old_pwd))
                    continue
            except Exception as e:
                aklog_error('%s:%s 登录异常' % (self.username, self.password))
                raise e
        aklog_error('%s:%s 登录失败' % (self.username, self.password))
        return False

    def is_login(self):
        """判断是否已经登录"""
        aklog_info()
        if not self.token:
            aklog_debug('未登录')
            return False
        data = {
            "target": "config",
            "action": "info",
            "configData": {
                "item": ['MODEL&29&1']
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp:
            aklog_info('当前已登录')
            return True
        else:
            aklog_error('登录失效')
            return False

    def get_web_status(self):
        """
        return:
                {
            "PhoneStatus": 1,
            "WebLang": 0,
            "ProductName": "S562",
            "WebTitle": "IP Phone"
        }
        """
        aklog_debug()
        path = 'status/get'
        params = {'session': self.token,
                  'web': '1'}
        resp = self.api_get(path, params)
        if resp and isinstance(resp, dict):
            result = resp['data']
            aklog_info(result)
            return result
        else:
            aklog_error('get_web_status Fail')
            return None

    def get_encrypt_password(self, password):
        """
        获取加密密码
        return:
                {
            "encrypt": "21232f297a57a5a743894a0e4a801fc3"
        }
        """
        aklog_debug()
        # password = 'rBd3mQ68jfEGo3K3' + password
        data = {
            "target": "login",
            "action": "set",
            "data": {
                "password": password
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp and isinstance(resp, dict):
            encrypt_password = resp['data']['encrypt']
            aklog_debug('encrypt_password: %s' % encrypt_password)
            return encrypt_password
        else:
            aklog_error('获取密码加密失败')
            return None

    def logout(self):
        """登出"""
        aklog_info()
        data = {
            "target": "login",
            "action": "logout",
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp and isinstance(resp, dict):
            aklog_info('登出成功')
            self.token = ''
            return True
        else:
            aklog_error('登出失败')
            self.token = ''
            return False

    @staticmethod
    def pwd_md5(pwd):
        m = hashlib.md5()
        m.update(pwd.encode("utf8"))
        return m.hexdigest()

    # endregion

    # region 配置项读写通用操作

    def read_config(self, *configs):
        """
        获取配置信息
        return:
        如果获取单个配置项的，直接返回配置项的值
        同时获取多个配置项的，返回字典类型
                {
            "MODEL": "S562",
            "WebLang": "0",
            "MAC": "A8:05:20:23:01:11",
            "FIRMWARE": "562.30.0.45",
            "HARDWARE": "562.0.18.0.0.0.0.0",
            "LANIPADDR": "192.168.88.195",
            "FirstLogin": "0"
        }
        """
        aklog_debug()
        data = {
            "target": "config",
            "action": "info",
            "configData": {
                "item": []
            },
            "session": self.token,
            "web": "1"
        }
        for config in configs:
            item_code = self.config_info.get(config)
            if item_code:
                data['configData']['item'].append(item_code)
            else:
                aklog_error('未找到 %s 配置，请检查web_interface_info.ini文件' % config)
                return False
        resp = self.api_post(data)
        if resp and isinstance(resp, dict):
            result = resp['data']
            if len(configs) == 1:
                # 如果获取单个配置项的，直接返回配置项的值
                item = configs[0].split('__')[-1]
                value = result[item]
                aklog_debug('[ %s ]: %s' % (item, value))
                return value
            else:
                # 同时获取多个配置项的，返回字典类型
                aklog_debug('read_config OK, result: %s' % result)
                return result
        else:
            aklog_error('read_config Fail')
            return None

    def edit_config(self, **kwargs):
        """
        修改配置项
        value: 勾选框可选 0、1， 下拉框可选：0、1、2
        """
        aklog_debug()
        data = {
            "target": "config",
            "action": "edit",
            "configData": {
                "item": []
            },
            "session": self.token,
            "web": "1"
        }
        for key in kwargs.keys():
            value = kwargs[key]
            code = self.parse_config_code(key)
            value_code = str(value) + code
            data['configData']['item'].append(value_code)
        resp = self.api_post(data)
        if resp and isinstance(resp, dict):
            aklog_debug('edit_config OK')
            return True
        else:
            aklog_error('edit_config Fail')
            return False

    def read_table_config(self, table_name, page_index=1):
        """
        获取表格数据
        return：
                {
            "retcode": 0,
            "action": "get",
            "message": "OK",
            "data": {
                "doorPhoneList": [
                    {
                        "deviceNumber": "1008",
                        "deviceName": "abc1008",
                        "address": "192.168.10.28",
                        "id": 1,
                        "userName": "",
                        "displayInCall": 1
                    }
                ],
                "webCameraList": [],
                "sum": 1,
                "pageNum": 10
            }
        }
        """
        path = f'{table_name}/get'
        params = {
            'page': str(page_index),
            'session': self.token,
            'web': '1'
        }
        resp = self.api_get(path, params)
        if resp and isinstance(resp, dict):
            aklog_info('read_table_config, OK')
            return resp['data']
        else:
            aklog_error('read_table_config Fail')
            return None

    def parse_config_code(self, config):
        """解析接口配置信息"""
        item_code = self.config_info.get(config)
        if item_code:
            item = item_code.split('&')[0]
            code = item_code.replace(item, '')
            return code
        return None

    @staticmethod
    def exchange_dict(option_data):
        """字典键值对互换"""
        return dict(zip(option_data.values(), option_data.keys()))

    # endregion

    # region Account Basic页面

    def register_sip(self, sip, sip_password, server_ip, server_port='5060', account_active=1, account=1,
                     transport=None, wait_register=True, **kwargs):
        """
        话机注册sip号功能
        account_active: 1 or 0
        kwargs: web_config_info接口配置文件中账号配置项，比如：DisplayName=xxx, RegisterName=xxx, Label=xxx
        """
        aklog_info()
        account_info = {
            'account%s__Enable' % account: account_active,
            'account%s__Label' % account: sip,
            'account%s__DisplayName' % account: sip,
            'account%s__RegisterName' % account: sip,
            'account%s__UserName' % account: sip,
            'account%s__Password' % account: sip_password,
            'account%s__SipServer1' % account: server_ip,
            'account%s__SipServerPort1' % account: server_port
        }
        if transport:
            transport = self.interface_info['transport_type_option'][transport]
            account_info['account%s__TransType' % account] = transport
        for key in kwargs.keys():
            account_info['account%s__%s' % (account, key)] = kwargs[key]

        self.edit_config(**account_info)
        if str(account_active) == '1' and wait_register:
            return self.wait_for_account_to_register_successfully(account=account)
        return None

    def wait_for_account_to_register_successfully(self, account=1, timeout=60):
        """等待帐号注册成功"""
        aklog_info()
        end_time = time.time() + timeout
        while time.time() < end_time:
            account_status = self.get_account_register_status(account)
            if account_status == 'Registered':
                aklog_info('sip account register success')
                return True
            elif account_status == 'Disabled':
                aklog_info('sip account status: %s' % account_status)
                return False
            time.sleep(3)
            continue
        aklog_error('sip account register failed')
        return False

    def get_account_register_status(self, account=1):
        """获取帐号注册状态"""
        status_code = self.read_config('account%s__Status' % account)
        status = self.exchange_dict(self.interface_info['register_status_option'])[status_code]
        aklog_info('account %s register status: %s' % (account, status))
        return status

    def clear_account(self, accounts='1'):
        """
        网页清除账号配置为默认配置
        :param accounts: '1', '2', '12'
        :return:
        """
        aklog_info()
        for account in str(accounts):
            account_info = {
                'account%s__Enable' % account: '0',
                'account%s__Label' % account: '',
                'account%s__DisplayName' % account: '',
                'account%s__RegisterName' % account: '',
                'account%s__UserName' % account: '',
                'account%s__Password' % account: '',
                'account%s__SipServer1' % account: '',
                'account%s__SipServerPort1' % account: '5060',
                'account%s__TransType' % account: '0'
            }
            self.edit_config(**account_info)

    # endregion

    # region Upgrade Basic升级基础页面

    # region 重启、恢复出厂

    def web_reboot(self):
        """重启设备"""
        aklog_info()
        data = {
            "target": "upgrade",
            "action": "set",
            "data": {
                "type": "Reboot"
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp:
            aklog_debug('reboot request success')
        else:
            aklog_error('reboot request failed')

        reboot_ret = cmd_waiting_for_device_reboot(
            self.device_ip, 60, self.device_config.get_reboot_default_time())
        re_login_ret = self.login()

        if reboot_ret and re_login_ret:
            aklog_info('重启完成')
            return True
        if not reboot_ret:
            aklog_error('重启失败')
        if not re_login_ret:
            aklog_error('重启之后重新登录失败')
        return False

    def web_reset_to_installer_setting(self):
        """恢复配置到installer"""
        aklog_info()
        data = {
            "target": "upgrade",
            "action": "set",
            "data": {
                "type": "ResetAppFactory"
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp:
            aklog_debug('reset request success')
        else:
            aklog_error('reset request failed')

        reboot_ret = cmd_waiting_for_device_reboot(
            self.device_ip, 60, self.device_config.get_reset_default_time())
        if not reboot_ret:
            aklog_error('恢复出厂，设备重启失败')
            return False

        if self.username == 'admin':
            self.password = self.device_config.get_web_admin_passwd()
        else:
            self.username = self.device_config.get_web_custom_username()
            self.password = self.device_config.get_web_custom_passwd()

        re_login_ret = self.login(return_resp=True)
        if not re_login_ret or re_login_ret.get('retcode') != 0:
            aklog_error('恢复出厂之后重新登录失败')
            return False
        elif re_login_ret['data']['isFirstLogin'] == 1:
            aklog_info('恢复出厂成功')
            return True
        else:
            aklog_error('恢复出厂失败，重新登录时不是第一次登录')
            return False

    def web_reset_to_factory_setting(self):
        """恢复出厂设置"""
        aklog_info()
        data = {
            "target": "upgrade",
            "action": "set",
            "data": {
                "type": "ResetFactory"
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp:
            aklog_debug('reset request success')
        else:
            aklog_error('reset request failed')

        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()
        reboot_ret = cmd_waiting_for_device_reboot(
            self.device_ip, 60, self.device_config.get_reset_default_time(), boot_time_after_get_ip)
        if not reboot_ret:
            aklog_error('恢复出厂，设备重启失败')
            return False

        if self.username == 'admin':
            self.password = self.device_config.get_web_admin_passwd()
        else:
            self.username = self.device_config.get_web_custom_username()
            self.password = self.device_config.get_web_custom_passwd()

        re_login_ret = self.login(return_resp=True)
        if not re_login_ret or re_login_ret.get('retcode') != 0:
            aklog_error('恢复出厂之后重新登录失败')
            return False
        elif re_login_ret['data']['isFirstLogin'] == 1:
            aklog_info('恢复出厂成功')
            return True
        else:
            aklog_error('恢复出厂失败，重新登录时不是第一次登录')
            return False

    # endregion

    # region 升级相关

    def get_firmware_version(self):
        return self.read_config('FIRMWARE')

    def upgrade_firmware(self, dst_version, firmware_file, re_upgrade=False):
        version_before_upgrade = self.get_firmware_version()
        if version_before_upgrade == dst_version and not re_upgrade:
            aklog_info('当前已是 %s 版本，不重复升级' % dst_version)
            return True
        self.edit_config(Reset=0)
        self._send_upgrade_request()
        self._upload_firmware_file(firmware_file)
        # 等待设备升级完成并重启
        cmd_waiting_for_device_reboot(self.device_ip, wait_time1=180)
        self.login()
        version_after_upgrade = self.get_firmware_version()
        if version_after_upgrade == dst_version:
            aklog_info('升级成功')
            return True
        else:
            aklog_error('升级失败')
            return False

    def _send_upgrade_request(self):
        """发送升级请求"""
        aklog_info()
        upgrade_data = {
            "target": "upgrade",
            "action": "set",
            "data": {
                "type": "firmware"
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(upgrade_data)
        if resp and isinstance(resp, dict):
            aklog_info('send_upgrade_request OK')
            return True
        else:
            aklog_error('send_upgrade_request Fail')
            return False

    def _upload_firmware_file(self, firmware_file):
        """上传升级包"""
        aklog_info()
        upload_url = f'upgrade/upload?session={self.token}&web=1'
        resp = self.api_post_file(upload_url, firmware_file, timeout=180)
        if resp and isinstance(resp, dict):
            aklog_info('upload_firmware_file OK')
            return True
        else:
            aklog_error('upload_firmware_file Fail')
            return False

    def upgrade_new_version(self):
        """升级到新版本"""
        ret = self.upgrade_firmware(
            self.rom_version, self.device_config.get_local_firmware_path(self.rom_version))
        return ret

    def upgrade_old_version(self):
        """升级到旧版本"""
        if self.rom_version:
            exclude_versions = [self.rom_version]
        else:
            exclude_versions = None
        self.device_config.get_old_firmware(
            force_replace=self.force_replace_old_version, exclude_versions=exclude_versions)  # 强制替换旧版本升级包
        old_firmware_version = self.device_config.get_old_firmware_version()
        old_firmware_path = '%s%s%s%s%s' % (self.device_config.get_upgrade_firmware_dir(True),
                                            self.device_config.get_firmware_prefix(),
                                            old_firmware_version,
                                            self.device_config.get_firmware_suffix(),
                                            self.device_config.get_firmware_ext())
        File_process.copy_file(self.device_config.get_old_firmware_path(), old_firmware_path)
        ret = self.upgrade_firmware(old_firmware_version, old_firmware_path)
        File_process.remove_file(old_firmware_path)
        return ret

    def upgrade_cover_old_version(self, firmware_version, firmware_path):
        """升级覆盖测试，检查从旧版本升级到新版本是否成功"""
        local_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(),
                                          firmware_version, self.device_config.get_firmware_ext())
        self.download_firmware_to_upgrade_dir(firmware_version, firmware_path)

        ret1 = self.upgrade_firmware(firmware_version, local_firmware_path)
        File_process.remove_file(local_firmware_path)
        if not ret1:
            aklog_error('升级到旧版本 %s 失败' % firmware_version)
            return False

        # aklog_info('升级新版本之前先导出autop配置文件')
        # autop_file_before_upgrade = self.export_autop_template('autop_file_before_upgrade.cfg')

        ret2 = self.upgrade_new_version()

        # aklog_info('升级后再对比autop配置文件')
        # config_ret = self.compare_autop_config_with_template(autop_file_before_upgrade)
        # if not config_ret:
        #     aklog_info('升级后autop配置项存在不同')
        # File_process.remove_file(autop_file_before_upgrade)
        return ret2

    def download_firmware_to_upgrade_dir(self, firmware_version, firmware_path):
        """将指定的升级包下载到本地Upgrade目录下"""
        local_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(),
                                          firmware_version, self.device_config.get_firmware_ext())
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
                download_result = ftp_client.download_file(local_firmware_path, ftp_info['remote_file'])
                ftp_client.close()
                if download_result:
                    break
                else:
                    ftp_connect_mode = False
                    continue
        else:
            aklog_info("将升级包拷贝到本地目录")
            for x in range(2):
                download_result = File_process.copy_file(firmware_path, local_firmware_path)
                if download_result:
                    break

        if download_result:
            return File_process.chmod_file_off_only_read(local_firmware_path)
        else:
            return False

    # endregion

    # endregion

    # region 8850隐藏页面 导log抓包

    def set_log_level(self, level=7):
        """设置log等级"""
        self.edit_config(LogLevel=level)

    def export_system_log(self, save_path=None, timeout=120):
        """导出log文件"""
        aklog_info()
        data = {
            "target": "maintenance",
            "action": "export",
            "data": {
                "type": "Log"
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data, timeout=timeout)
        if resp and resp.get('retcode') == 0:
            address = resp['data']['address']
            download_url = f'{self.host}/{address}'
            if not save_path:
                save_dir = root_path + '\\testfile\\Device_log\\%s' % self.model_name
                os.makedirs(save_dir, exist_ok=True)
                save_path = save_dir + '\\DevicesLog.tgz'
            ret = self.api_download(download_url, save_path)
            if ret:
                aklog_info('export log success')
                return True
        aklog_error('export log failed')
        return False

    def export_syslog_to_results_dir(self, case_name):
        """导出syslog并保存到Results目录下"""
        log_time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file_name = 'DeviceLog--{}--{}--{}.tgz'.format(case_name, self.device_name, log_time)
        log_file = '{}\\{}'.format(log_dir, log_file_name)
        os.makedirs(log_dir, exist_ok=True)
        self.export_system_log(log_file)
        # 如果开启保存到共享文件夹，则log文件路径增加HTTP访问URL
        report_dir_url = get_share_http_report_dir_url()
        if report_dir_url:
            log_file_url = '{}/device_log/{}'.format(report_dir_url, log_file_name)
            aklog_info(f'log_file_url: {log_file_url}')

    def start_pcap(self):
        """开始抓包"""
        aklog_info()
        data = {
            "target": "maintenance",
            "action": "start",
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp:
            aklog_info('pcap start success')
            return True
        else:
            aklog_error('pcap start failed')
            return False

    def stop_pcap(self):
        """停止抓包"""
        aklog_info()
        data = {
            "target": "maintenance",
            "action": "stop",
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp:
            aklog_info('pcap stop success')
            return True
        else:
            aklog_error('pcap stop failed')
            return False

    def export_pcap(self):
        """导出抓包"""
        aklog_info()
        data = {
            "target": "maintenance",
            "action": "export",
            "data": {
                "type": "PCAP"
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp:
            aklog_info('pcap export success')
            return True
        else:
            aklog_error('pcap export failed')
            return False

    def export_config_file(self):
        """导出配置文件"""
        aklog_info()
        data = {
            "target": "maintenance",
            "action": "export",
            "data": {
                "type": "config"
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp:
            aklog_info('config file export success')
            return True
        else:
            aklog_error('config file export failed')
            return False

    # endregion

    # region 8848隐藏页面 打开ssh配置

    def set_ssh_or_tln(self):
        """
        网页8848打开ssh
        """
        aklog_info()
        data = {
            "target": "hidden",
            "action": "set",
            "data": {
                "type": "ssh"
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(data)
        if resp:
            aklog_debug('set ssh open OK')
            return True
        else:
            aklog_error('set ssh open Fail')
            return False

    def web_open_ssh(self):
        return self.set_ssh_or_tln()

    # endregion

    # region Telnet/SSH命令通用操作

    def telnet_login(self):
        for i in range(5):
            if self.tln.login_host():
                self.tln_ssh_port_list = self.tln.get_port_list()
                self.tln_ssh_pwd_list = self.tln.get_pwd_list()
                return True
            elif i == 0:
                self.web_open_ssh()
                continue
            time.sleep(5)
            continue
        aklog_error('Telnet连接登录失败')
        return False

    def telnet_logout(self):
        self.tln.command_stop()
        self.tln.logout_host()

    def ssh_login(self):
        for i in range(5):
            if self.ssh.connect():
                self.tln_ssh_port_list = self.ssh.get_port_list()
                self.tln_ssh_pwd_list = self.ssh.get_pwd_list()
                return True
            elif i == 0:
                self.web_open_ssh()
                continue
            time.sleep(5)
            continue
        aklog_error('SSH连接登录失败')
        return False

    def ssh_logout(self):
        self.ssh.interactive_stop_command()
        self.ssh.close()

    def tln_or_ssh_login(self):
        if self.device_config.get_remote_connect_type() == 'telnet':
            self.telnet_login()
        else:
            self.ssh_login()

    def tln_or_ssh_logout(self):
        if self.device_config.get_remote_connect_type() == 'telnet':
            self.telnet_logout()
        else:
            self.ssh_logout()

    def get_value_by_ssh(self, command, timeout=60, print_result=True, ignore_error=False) -> Union[str, None]:
        """后台执行命令获取对应配置的值"""
        aklog_printf()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return None
        value = self.ssh.command_result(command, timeout=timeout, ignore_error=ignore_error, encoding='gbk')
        if print_result:
            aklog_printf('value: %s' % value)
        return value

    def get_result_by_telnet_command(self, command, timeout=60, print_result=True) -> Union[str, None]:
        """后台执行命令获取对应配置的值"""
        aklog_printf()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return None
        result = self.tln.command_result(command, timeout=timeout)
        if print_result:
            aklog_printf('result: %s' % result)
        return result

    def get_result_by_tln_or_ssh(
            self, command, timeout=60, print_result=True, ignore_error=False) -> Union[str, None]:
        """telnet或SSH执行命令并获取结果"""
        if self.device_config.get_remote_connect_type() == 'telnet':
            result = self.get_result_by_telnet_command(
                command, timeout=timeout, print_result=print_result)
        else:
            result = self.get_value_by_ssh(
                command, timeout=timeout, print_result=print_result, ignore_error=ignore_error)
        return result

    def exec_command_by_ssh(self, *commands, timeout=60):
        aklog_printf()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return False
        results = []
        for command in commands:
            ret = self.ssh.exec_command_no_back(command, timeout)
            results.append(ret)
            time.sleep(0.5)
        if False in results:
            return False
        else:
            return True

    def exec_command_by_tln(self, *commands, timeout=60):
        aklog_printf()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return False
        results = []
        for command in commands:
            ret = self.tln.exec_command(command, timeout)
            results.append(ret)
            time.sleep(0.5)
        if False in results:
            return False
        else:
            return True

    def command_by_tln_or_ssh(self, *commands, timeout=120):
        if self.device_config.get_remote_connect_type() == 'telnet':
            return self.exec_command_by_tln(*commands, timeout=timeout)
        else:
            return self.exec_command_by_ssh(*commands, timeout=timeout)

    def exec_command_by_interactive_ssh_thread(self, command):
        """ssh交互式子线程执行，需要与get_result_by_interactive_ssh_thread配合使用"""
        aklog_printf()
        for i in range(2):
            if self.ssh.is_connected() and self.ssh.start_chan():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return False
        time.sleep(0.5)
        self.ssh.thread_interactive_exec_command(command)
        return self.ssh

    def stop_interactive_ssh_command(self):
        self.ssh.interactive_stop_command()

    def get_result_by_interactive_ssh_thread(self, timeout=60):
        """获取SSH交互式子线程执行结果，需要与exec_command_by_interactive_ssh_thread配合使用"""
        return self.ssh.interactive_return_log(timeout=timeout)

    def ignore_previous_logs_by_interactive_ssh_thread(self, wait_time=3):
        """先获取一次结果，然后再次获取结果时就不会包含之前的结果，这样就不需要logcat -c清空掉之前的log了
        需要与exec_command_by_interactive_ssh_thread配合使用（该方法有点问题，先不要使用）"""
        result1 = self.ssh.interactive_return_log(wait_time)
        # result2 = self.interactive_tln_or_ssh.interactive_return_log(1)
        # result = result1 + result2
        return result1

    def exec_command_by_interactive_telnet_thread(self, command):
        """Telnet交互式子线程执行，需要与get_result_by_interactive_telnet_thread配合使用"""
        aklog_printf()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return False
        time.sleep(1)
        self.tln.thread_exec_command(command)
        return self.tln

    def get_result_by_interactive_telnet_thread(self, timeout=60):
        """获取Telnet交互式子线程执行结果，需要与exec_command_by_interactive_telnet_thread配合使用"""
        return self.tln.thread_stop_exec_output_result(timeout=timeout)

    def ssh_modify_mac(self, new_mac):
        """设备ssh连接执行命令"""
        aklog_info()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return
        self.ssh.modify_mac(new_mac)
        self.ssh.close()

    def monitor_screen_touch_log(self):
        """监控屏幕点击log"""
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return None
        ret = self.ssh.monitor_field_in_cat_output('getevent', '/dev/input/event0: 0003 0039 ffffffff')
        return ret

    def get_result_by_tln_sql(self, sqlcipher_path, db_path, db_key, sql, timeout=60):
        """telnet连接，进入数据库获取信息"""
        aklog_printf()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return None
        result = self.tln.exec_sql(
            sqlcipher_path, db_path, db_key, sql, timeout=timeout)
        return result

    # endregion

    # region Telnet/SSH命令

    def reboot_by_tln_or_ssh(self, wait_time_after_reboot=10):
        aklog_info()
        self.command_by_tln_or_ssh('reboot')
        return cmd_waiting_for_device_reboot(self.device_ip, wait_time1=30, sec=wait_time_after_reboot)

    def get_uptime_by_tln_or_ssh(self) -> Optional[int]:
        """获取开机时间"""
        aklog_info()
        uptime = None
        for i in range(2):
            uptime = self.get_result_by_tln_or_ssh('uptime')
            if uptime:
                break
            elif i == 0:
                time.sleep(3)
                continue
            else:
                return None

        def calculate_minutes(uptime_str):
            # 匹配 "X days, HH:MM"
            match = re.search(r'up +(\d+) +days?, +(\d+):(\d+),', uptime_str)
            if match:
                days = int(match.group(1))
                hours = int(match.group(2))
                minutes = int(match.group(3))
                return days * 24 * 60 + hours * 60 + minutes

            # 匹配 "X days, X min"
            match = re.search(r'up +(\d+) +days?, +(\d+) +min,', uptime_str)
            if match:
                days = int(match.group(1))
                minutes = int(match.group(2))
                return days * 24 * 60 + minutes

            # 匹配 "HH:MM"
            match = re.search(r'up +(\d+):(\d+),', uptime_str)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                return hours * 60 + minutes

            # 匹配 "X min"
            match = re.search(r'up +(\d+) +min,', uptime_str)
            if match:
                minutes = int(match.group(1))
                return minutes

            return None

        uptime_min = calculate_minutes(uptime)
        aklog_info('uptime: %s min' % uptime_min)
        return uptime_min

    def get_door_setting_config_by_tln_or_ssh(self, section, key):
        """获取/config/Door/Setting.conf配置文件里面的配置项"""
        return self.get_result_by_tln_or_ssh(
            '/app/bin/inifile_wr r /config/Door/Setting.conf %s %s ""' % (section, key))

    def wait_general_setting_config_by_tln_or_ssh(self, section, key, target_value, timeout=60):
        """获取/config/Door/Setting.conf配置文件里面的配置项"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            value = self.get_result_by_tln_or_ssh(
                '/app/bin/inifile_wr r /config/Phone/General/Setting.conf %s %s ""' % (section, key))
            if value and value.strip() == target_value:
                return True
            time.sleep(3)
        aklog_warn(f'配置项{section},{key} 值未变成: {target_value}')
        return False

    def start_adb_server_by_ssh(self, device_id, retry_counts=5):
        if ':' not in device_id:
            aklog_info('USB方式连接，不需要启动adb server')
            return True
        adb_server_port = device_id.split(':')[1]
        command_start_adbd = 'setprop service.adb.tcp.port %s; stop adbd; start adbd' % adb_server_port
        command_write_misc_adb = 'mkdir /data/misc/adb;echo %s > /data/misc/adb/adb_keys' \
                                 % self.device_config.get_command_misc_adb_password()
        command_chown_adb = 'cd /data/misc/adb/; chown system:shell adb_keys'
        command_chmod_adb = 'chmod 640 /data/misc/adb/adb_keys'
        for i in range(0, retry_counts):
            try:
                ret = self.exec_command_by_ssh(
                    command_start_adbd, command_write_misc_adb, command_chown_adb, command_chmod_adb
                )
                if ret:
                    time.sleep(3)
                    return True
                elif i < 2:
                    self.web_open_ssh()
                    continue
                else:
                    aklog_error('Start Adb Server 失败，重试...')
                    time.sleep(3)
                    continue
            except:
                aklog_error('遇到未知异常，等待重试...' + str(traceback.format_exc()))
                time.sleep(5)
                continue
        aklog_error('Start Adb Server 失败')
        return False

    def set_upgrade_idle_time(self, wait_time=30):
        """
        设置设备进入空闲状态的等待时间，准备升级
        wait_time: 秒
        """
        self.command_by_tln_or_ssh('settings put system akuvox_upgrade_idle_time  %s' % (wait_time * 1000))

    def push_file_by_tftp(self, file_path, dst_dir, tftp_timeout=300):
        """如果是手动开启的TFTP工具，需要将工具的根目录设置为要传输的文件目录"""
        aklog_debug()
        file_dir, file_name = os.path.split(file_path)
        if not dst_dir.startswith('/'):
            dst_dir = '/' + dst_dir
        dst_path = f'{dst_dir}/{file_name}'
        # 先判断文件是否存在和一致
        if self.check_remote_file_consistency(file_path, dst_path):
            return
        tftp_server = thread_start_tftp_server(file_dir)
        local_ip = get_local_host_ip()
        self.command_by_tln_or_ssh(
            f'tftp -g -r {file_name} -l {dst_path} {local_ip}:{tftp_server.tftp_port}',
            timeout=tftp_timeout)

    def pull_file_by_tftp(self, file_path, dst_dir=None, tftp_timeout=300):
        """tftp方式导出文件"""
        aklog_debug()
        file_name = os.path.basename(file_path)
        file_name, ext = os.path.splitext(file_name)
        _time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        dst_file_name = f'{file_name}--{_time}{ext}'
        if not dst_dir:
            aklog_warn('未手动开启TFTP服务器，并且没有传入目标文件夹，使用result目录下的tftp文件夹')
            dst_dir = aklog_get_result_dir() + '\\tftp'
        tftp_server = thread_start_tftp_server(dst_dir)
        time_sleep(10)
        local_ip = get_local_host_ip(self.device_ip)
        self.command_by_tln_or_ssh(
            f'tftp -p -l {file_path} -r {dst_file_name} {local_ip}:{tftp_server.tftp_port}',
            timeout=tftp_timeout)
        return dst_file_name

    def pull_db_files_by_tftp(self, dst_dir=None, tftp_timeout=300):
        """将tuya_db_files文件夹导出"""
        file_path = '/data/code/tuya_db_files'
        file_dir, file_name = os.path.split(file_path)
        tar_file = f'{file_name}.tar'
        tar_file_path = f'{file_dir}/{tar_file}'
        tar_cmd = f'cd {file_dir};rm {tar_file} -rf;tar -cf {tar_file} {file_name}'
        self.command_by_tln_or_ssh(tar_cmd)
        return self.pull_file_by_tftp(tar_file_path, dst_dir, tftp_timeout)

    def check_remote_file_consistency(self, local_file, remote_file):
        """
        校验本地文件与远程文件内容是否一致
        :param local_file: 本地文件路径
        :param remote_file: 远程文件路径
        :return: True一致，False不一致，None异常
        """
        try:
            # 1. 计算本地文件MD5
            local_md5 = File_process.get_file_md5(local_file)
            if not local_md5:
                aklog_warn("本地文件MD5计算失败。")
                return None
            aklog_debug(f"本地文件[{local_file}] MD5: {local_md5}")

            # 2. 获取远程文件MD5
            # Linux常用命令：md5sum /path/to/file | awk '{print $1}'
            remote_cmd = f"md5sum {remote_file} | awk '{{print $1}}'"
            remote_md5 = self.get_result_by_tln_or_ssh(remote_cmd)
            if not remote_md5 or "can't open" in remote_md5 or 'No such file or directory' in remote_md5:
                aklog_warn("远程文件MD5获取失败。")
                return None
            remote_md5 = remote_md5.strip()
            aklog_debug(f"远程文件[{remote_file}] MD5: {remote_md5}")

            # 3. 比较
            if local_md5 == remote_md5:
                aklog_debug("本地文件与远程文件内容一致。")
                return True
            else:
                aklog_warn("本地文件与远程文件内容不一致。")
                return False
        except Exception as e:
            aklog_error(f"文件一致性校验异常: {e}")
            aklog_debug(traceback.format_exc())
            return None

    def set_connect_akubela_test_url(self, test_url='https://my.uat.akubela.com'):
        """连接测试服务器，需要使用测试url"""
        # 设置连接测试服务器的URL
        if test_url and test_url != 'https://my.akubela.com':
            self.command_by_tln_or_ssh(f'echo {test_url}  > /data/code/test_url')

    # endregion

    # region telnet/SSH 进程相关

    def top_get_memory_info(self):
        """获取内存使用情况"""
        aklog_info('top_get_memory_info')
        memory_info = self.get_result_by_tln_or_ssh('top -b -n 1 | grep Mem: | grep -v grep')
        if memory_info is None:
            return None
        infos = memory_info.split('Mem:')[-1].split(',')
        memory_info_dict = {}
        for info in infos:
            if 'used' in info:
                memory_info_dict['used'] = info.strip().split(' ')[0]
            if 'free' in info:
                memory_info_dict['free'] = info.strip().split(' ')[0]
            if 'shrd' in info:
                memory_info_dict['shrd'] = info.strip().split(' ')[0]
            if 'buff' in info:
                memory_info_dict['buff'] = info.strip().split(' ')[0]
            if 'cached' in info:
                memory_info_dict['cached'] = info.strip().split(' ')[0]
        aklog_info('memory_info: %r' % memory_info_dict)
        return memory_info_dict

    def top_get_cpu_info(self):
        """获取cpu使用情况"""
        aklog_info('top_get_cpu_info')
        cpu_info = self.get_result_by_tln_or_ssh('top -b -n 1 | grep CPU: | grep -v grep')
        if cpu_info is None:
            return None
        infos = cpu_info.split('CPU:')[-1].strip().split('  ')
        cpu_info_dict = {}
        for info in infos:
            if 'usr' in info:
                cpu_info_dict['usr'] = info.strip().split(' ')[0]
            if 'sys' in info:
                cpu_info_dict['sys'] = info.strip().split(' ')[0]
            if 'nic' in info:
                cpu_info_dict['nic'] = info.strip().split(' ')[0]
            if 'idle' in info:
                cpu_info_dict['idle'] = info.strip().split(' ')[0]
            if 'io' in info:
                cpu_info_dict['io'] = info.strip().split(' ')[0]
            if 'irq' in info:
                cpu_info_dict['irq'] = info.strip().split(' ')[0]
            if 'sirq' in info:
                cpu_info_dict['sirq'] = info.strip().split(' ')[0]
        aklog_info('cpu_info: %r' % cpu_info_dict)
        return cpu_info_dict

    def top_get_process_info(self, *process_flag):
        """获取phone进程信息，返回字典"""
        aklog_info('top_get_process_info')
        attribute = self.get_result_by_tln_or_ssh('top -b -n 1 | grep "PID" | grep -v grep')
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_info('attribute_list: %r' % attribute_list)
        grep_command = ''
        for i in process_flag:
            grep_command += '| grep "%s" ' % i
        info = self.get_result_by_tln_or_ssh('top -b -n 1 | grep -v grep %s' % grep_command)
        if info is None:
            return None
        info = info.replace('\n#', '').strip()
        info = re.sub(' +', ' ', info)
        infos = info.split(' ')
        aklog_info('process infos: %r' % infos)

        process_info = {}
        for attribute in attribute_list:
            index = attribute_list.index(attribute)
            if attribute == 'PID':
                process_info['pid'] = infos[index]
            elif attribute == 'PPID':
                process_info['ppid'] = infos[index]
            elif attribute == 'USER':
                process_info['user'] = infos[index]
            elif attribute == 'STAT':
                process_info['stat'] = infos[index]
            elif attribute == 'RSS':
                process_info['rss'] = infos[index]
            elif attribute == 'VSZ':
                process_info['vsz'] = infos[index]
            elif attribute == '%VSZ':
                process_info['vsz%'] = infos[index]
            elif attribute == '%CPU':
                process_info['cpu%'] = infos[index]
            elif 'COMMAND' in attribute:
                if len(infos) > len(attribute_list):
                    process_info['command'] = ' '.join(infos[index:])
                else:
                    process_info['command'] = infos[index]

        aklog_info('process_info: %r' % process_info)
        return process_info

    def ps_get_process_info(self, *process_flag):
        """获取phone进程信息，返回字典"""
        aklog_info()
        attribute = self.get_result_by_tln_or_ssh('%s | grep "PID" | grep -v grep' % self.device_config.get_ps_cmd())
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_debug('attribute_list: %r' % attribute_list)
        grep_command = ''
        for i in process_flag:
            grep_command += '| grep "%s" ' % i
        info = self.get_result_by_tln_or_ssh('%s | grep -v grep %s' % (self.device_config.get_ps_cmd(), grep_command))
        if info is None or 'root' not in info:
            return None
        info = info.replace('\n#', '').strip()
        info = re.sub(' +', ' ', info)
        infos = info.split(' ')
        aklog_debug('process infos: %r' % infos)

        process_info = {}
        for attribute in attribute_list:
            index = attribute_list.index(attribute)
            if attribute == 'PID':
                process_info['pid'] = infos[index]
            elif attribute == 'USER':
                process_info['user'] = infos[index]
            elif attribute == 'VSZ':
                process_info['vsz'] = infos[index]
            elif attribute == 'STAT':
                process_info['stat'] = infos[index]
            elif 'COMMAND' in attribute:
                if len(infos) > len(attribute_list):
                    process_info['command'] = ' '.join(infos[index:])
                else:
                    process_info['command'] = infos[index]

        aklog_debug('process_info: %r' % process_info)
        return process_info

    def ps_get_all_info(self):
        info = self.get_result_by_tln_or_ssh(self.device_config.get_ps_cmd())
        return info

    def ps_judge_processes_is_running(self, *processes):
        """ps获取进程信息，判断多个进程是否都正在运行"""
        aklog_info()
        not_running_process_list = []
        for process in processes:
            ps_command = '%s | grep -v grep | grep "%s"' % (self.device_config.get_ps_cmd(), process)
            info = self.get_result_by_tln_or_ssh(ps_command)
            if info is None:
                return None
            info = info.replace('\n#', '').strip()
            if not info:
                not_running_process_list.append(process)

        if not not_running_process_list:
            aklog_info('所有进程都正在运行')
            return True
        else:
            aklog_warn('有进程未运行: %r' % not_running_process_list)
            return False

    def check_device_process_status(self):
        """检查设备进程的状态，是否都在运行，由于各机型的进程信息可能不一致，可以重写该方法"""
        aklog_info()
        status = self.ps_judge_processes_is_running(
            'com.akuvox.phone',
            'com.akuvox.upgradeui',
            'homeassistant/__main__.pyc',
            'sip',
            'autop',
            'api.fcgi fcgi'
        )
        return status

    def kill_process_by_ssh(self, *processes):
        """杀进程"""
        aklog_info()
        attribute = self.get_value_by_ssh('%s | grep "PID" | grep -v grep' % self.device_config.get_ps_cmd())
        if attribute is None:
            return
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_debug('attribute_list: %r' % attribute_list)
        pid_index = attribute_list.index('PID')
        for process in processes:
            ps_cmd = '%s | grep -v grep | grep "%s"' % (self.device_config.get_ps_cmd(), process)
            info = self.get_value_by_ssh(ps_cmd)
            if not info or process not in info:
                aklog_printf('%s 没有在运行' % process)
                continue

            lines = info.splitlines()
            for line in lines:
                if not line or process not in line:
                    continue
                line = line.replace('\n#', '').strip()
                line = re.sub(' +', ' ', line)
                info_list = line.split(' ')
                aklog_debug('process info: %r' % info_list)
                pid = info_list[pid_index]
                kill_cmd = 'kill -9 %s' % pid
                ret = self.exec_command_by_ssh(kill_cmd)
                if ret:
                    aklog_printf('杀进程 %s 完成' % process)
                else:
                    aklog_error('杀进程 %s 失败' % process)

    def kill_process_by_tln(self, *processes):
        """杀进程"""
        aklog_info()
        attribute = self.get_result_by_telnet_command(
            '%s | grep "PID" | grep -v grep' % self.device_config.get_ps_cmd())
        if attribute is None:
            return
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_debug('attribute_list: %r' % attribute_list)
        pid_index = attribute_list.index('PID')
        for process in processes:
            ps_cmd = '%s | grep -v grep | grep "%s"' % (self.device_config.get_ps_cmd(), process)
            info = self.get_result_by_telnet_command(ps_cmd)
            if not info or process not in info:
                aklog_printf('%s 没有在运行' % process)
                continue
            lines = info.splitlines()
            for line in lines:
                if not line or process not in line:
                    continue
                line = line.replace('\n#', '').strip()
                line = re.sub(' +', ' ', line)
                info_list = line.split(' ')
                aklog_debug('process info: %r' % info_list)
                pid = info_list[pid_index]
                kill_cmd = 'kill -9 %s' % pid
                ret = self.exec_command_by_tln(kill_cmd)
                if ret:
                    aklog_info('杀进程 %s 完成' % process)
                else:
                    aklog_error('杀进程 %s 失败' % process)

    def kill_process_by_tln_or_ssh(self, *processes):
        if self.device_config.get_remote_connect_type() == 'telnet':
            return self.kill_process_by_tln(*processes)
        else:
            return self.kill_process_by_ssh(*processes)

    def wait_process_start(self, *processes, timeout=600):
        """等待进程启动"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            process_ret = self.ps_judge_processes_is_running(*processes)
            if process_ret:
                return True
            time.sleep(5)
            continue
        aklog_warn(f'{processes} 进程未在运行')
        return False

    # endregion

    # region telnet/ssh log相关

    def clear_logs_by_ssh(self):
        """清理log缓存"""
        aklog_info('clear_logs_by_ssh')
        self.exec_command_by_ssh('logcat -G 2M', 'logcat -c')

    def clear_logs_by_tln(self):
        """清理log缓存"""
        aklog_info('clear_logs_by_tln')
        self.command_by_tln_or_ssh('rm /tmp/Messages* -f', 'echo "" > /tmp/Messages')

    def clear_logs_by_tln_or_ssh(self):
        """清理log缓存"""
        if self.device_config.get_remote_connect_type() == 'ssh':
            self.clear_logs_by_ssh()
        else:
            self.clear_logs_by_tln()

    def set_logcat_buffer_size(self, size='20M', *processes):
        """
        设置logcat缓冲区大小，避免因为缓冲区太小，短时间打印太多log导致logcat中断
        size: 2M
        """
        buffer_sizes = self.get_logcat_buffer_size()
        if not buffer_sizes:
            self.exec_command_by_ssh('logcat -G %s' % size)

        if processes:
            cmd_list = []
            for process in processes:
                if buffer_sizes.get(process) == size:
                    continue
                cmd = f'logcat -b {process} -G {size}'
                cmd_list.append(cmd)
            if cmd_list:
                self.exec_command_by_ssh(*cmd_list)
        else:
            flag = False
            for key, value in buffer_sizes.items():
                if value != size:
                    flag = True
                    break
            if flag:
                self.exec_command_by_ssh('logcat -G %s' % size)

    def get_logcat_buffer_size(self) -> Optional[dict]:
        try:
            # 执行 adb logcat -g 命令
            output = self.get_value_by_ssh('logcat -g')
            buffer_sizes = {}
            for line in output.splitlines():
                parts = line.split(':')
                if len(parts) == 2:
                    buffer_name = parts[0].strip()
                    size_info = parts[1].strip()
                    size = re.search(r'buffer is\s+(\d+)\s+MiB', size_info).group(1) + 'M'
                    buffer_sizes[buffer_name] = size
            aklog_debug(f'buffer_sizes: {buffer_sizes}')
            return buffer_sizes
        except Exception as e:
            aklog_debug(e)
            return None

    def get_dclient_msgs(self):
        """获取dclient的msg，将msg转换成字典"""
        aklog_info('get_dclient_msgs')
        command = 'logcat -d | grep "<" | cut -b 20- '
        dclient_msgs = []
        ssh_log = self.get_result_by_tln_or_ssh(command)
        ssh_log = ssh_log.replace('"', '##').replace('{', '**').replace('}', '**')
        # print(ssh_log)
        ssh_logs = ssh_log.split('</Msg>')
        # print(ssh_logs)
        for msg in ssh_logs:
            if not msg or not msg.strip():
                continue
            result_dict = parse_msg_to_dict(msg)
            dclient_msgs.append(result_dict)
        aklog_info(dclient_msgs)
        return dclient_msgs

    def get_dclient_msg_by_type(self, msg_type, dclient_msgs=None):
        if not dclient_msgs:
            dclient_msgs = self.get_dclient_msgs()
        for dc_msg in dclient_msgs:
            if not msg_type:
                return dc_msg
            elif msg_type == dc_msg['Msg'].get('Type'):
                return dc_msg
        return None

    def is_correct_print_log(self, flag):
        aklog_info('is_correct_print_log, flag: %s' % flag)
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d | grep -v grep | grep "%s"' % flag
        else:
            command = 'cat /tmp/Messages* | grep -v grep | grep "%s"' % flag
        ssh_log = self.get_result_by_tln_or_ssh(command)
        if ssh_log and flag in ssh_log:
            return True
        else:
            aklog_error('%s 日志不存在' % flag)
            return False

    def is_correct_log_level(self, log_level):
        """判断log等级打印是否正确"""
        logs = self.get_system_log_by_tln_or_ssh()
        ret = False
        if int(log_level) in [0, 1, 2]:
            ret = ',l3:' not in logs
        elif int(log_level) in [3, 4, 5, 6]:
            ret = ',l3:' in logs and ',l7:' not in logs and ',l%d:' % (int(log_level) + 1) not in logs
        elif int(log_level) == 7:
            ret = ',l3:' in logs and ',l7:' in logs
        if not ret:
            aklog_info(logs)
        return ret

    def get_counts_with_log_flag(self, flag):
        """获取指定log出现多少次"""
        aklog_info('get_counts_with_log_flag, flag: %s' % flag)
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d | grep -v grep | grep "%s"' % flag
        else:
            command = 'cat /tmp/Messages* | grep -v grep | grep "%s"' % flag
        ssh_log = self.get_result_by_tln_or_ssh(command)
        if ssh_log:
            counts = ssh_log.count(flag)
            # 结束时打印的log可能包含命令那一行，需要把这一行出现的次数去掉
            grep_counts = ssh_log.count('grep "%s"' % flag)
            counts -= grep_counts
        else:
            counts = 0
        aklog_info('%s 出现次数: %s' % (flag, counts))
        return counts

    def get_system_log_by_tln_or_ssh(self, log_flag=None):
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d'
        else:
            command = 'cat /tmp/Messages*'
        if log_flag:
            command += ' | grep "%s"' % log_flag
        ssh_log = self.get_result_by_tln_or_ssh(command, print_result=False)
        return ssh_log

    def upload_log_by_tln_or_ssh(self, case_name=None):
        """上传设备log到服务器"""
        get_cmd = self.device_config.get_upload_log_sh_get_cmd()
        self.command_by_tln_or_ssh(get_cmd)
        exec_cmd = self.device_config.get_upload_log_sh_exec_cmd()
        out = self.get_result_by_tln_or_ssh(
            exec_cmd, timeout=900, print_result=False, ignore_error=True)
        # 正则表达式模式用于匹配URL
        url_pattern = re.compile(r'http://\S+')
        # 查找所有匹配的URL
        urls = url_pattern.findall(out)
        if urls:
            url = urls[0]
            if not url.endswith('.tgz'):
                url += '.tgz'
            if case_name:
                aklog_info(f'{case_name}, log_url: {url}')
            else:
                aklog_info(f'log_url: {url}')
            return url
        aklog_warn(f'获取上传log的URL失败: {out}')
        return None

    def wait_get_syslog_by_tln_or_ssh(self, log_flag, timeout=30):
        """等待获取到指定的log"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            log = self.get_system_log_by_tln_or_ssh(log_flag)
            if log and log_flag in log:
                return log
            time.sleep(3)
            continue
        return None

    def get_ha_log_by_tln_or_ssh(self, log_flag=None):
        """获取HA的log"""
        command = 'cat /data/code/home-assistant.log'
        if log_flag:
            command += ' | grep "%s"' % log_flag
        ssh_log = self.get_result_by_tln_or_ssh(command, print_result=False)
        return ssh_log

    def export_syslog_to_results_dir_by_tln_or_ssh(self, case_name):
        """SSH或Telnet导出syslog并保存到Results目录下"""
        log_time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file_name = 'PhoneLog--{}--{}--{}.log'.format(case_name, self.device_name, log_time)
        log_file = '{}\\{}'.format(log_dir, log_file_name)
        os.makedirs(log_dir, exist_ok=True)
        log = self.get_system_log_by_tln_or_ssh()
        File_process.write_file(log_file, log, print_content=False)
        aklog_info(f'log_file: {log_file}')
        # 如果开启保存到共享文件夹，则log文件路径增加HTTP访问URL
        report_dir_url = get_share_http_report_dir_url()
        if report_dir_url:
            log_file_url = '{}/device_log/{}'.format(report_dir_url, log_file_name)
            aklog_info(f'log_file_url: {log_file_url}')

    def export_ha_log_to_results_dir_by_tln_or_ssh(self, case_name):
        """SSH或Telnet导出HA log并保存到Results目录下"""
        aklog_info()
        log_time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file_name = 'HAlog--{}--{}--{}.log'.format(case_name, self.device_name, log_time)
        log_file = '{}\\{}'.format(log_dir, log_file_name)
        os.makedirs(log_dir, exist_ok=True)
        log = self.get_ha_log_by_tln_or_ssh()
        File_process.write_file(log_file, log, print_content=False)
        aklog_info(f'ha_log_file: {log_file}')
        # 如果开启保存到共享文件夹，则log文件路径增加HTTP访问URL
        report_dir_url = get_share_http_report_dir_url()
        if report_dir_url:
            ha_log_file_url = '{}/device_log/{}'.format(report_dir_url, log_file_name)
            aklog_info(f'ha_log_file_url: {ha_log_file_url}')

    def start_logs_by_interactive_tln_or_ssh(self, log_flag=None):
        """
        开始交互式获取设备log，需要配合save_log_to_result_dir_by_tln_or_ssh使用
        log_flag: 如果要同时过滤多组字段全部显示，可以在多组字段中间加 |，比如：relay1 state|relay2 state
        grep要加参数 -E， 比如:grep -E "relay1 state|relay2 state"
        """
        aklog_info()
        if log_flag and '|' in log_flag:
            log_flag = ' | grep -E "%s"' % log_flag
        elif log_flag:
            log_flag = ' | grep "%s"' % log_flag
        else:
            log_flag = ''
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat%s' % log_flag
            # self.set_logcat_buffer_size()
            self.exec_command_by_interactive_ssh_thread(command)
        else:
            command = 'tail -F /tmp/Messages%s' % log_flag
            self.exec_command_by_interactive_telnet_thread(command)

    def get_logs_by_interactive_tln_or_ssh(self, timeout=60):
        """交互式获取设备log，需要配合start_logs_by_interactive_tln_or_ssh使用"""
        aklog_info()
        if self.device_config.get_remote_connect_type() == 'ssh':
            ret = self.get_result_by_interactive_ssh_thread(timeout)
        else:
            ret = self.get_result_by_interactive_telnet_thread(timeout)
        return ret

    def get_counts_with_interactive_log_flag(self, flag, ssh_log=None):
        """
        获取指定log出现多少次，需要配合start_logs_by_interactive_tln_or_ssh使用
        """
        aklog_info('get_counts_with_interactive_log_flag, flag: %s' % flag)
        if ssh_log is None:
            ssh_log = self.get_logs_by_interactive_tln_or_ssh()
        counts = 0
        if ssh_log:
            log_lines = ssh_log.split('\n')
            for line in log_lines:
                if flag in line and '| grep' not in line:
                    counts += 1
        else:
            aklog_warn('未获取到 %s 的指定 log' % flag)
        aklog_info('%s 出现次数: %s' % (flag, counts))
        return counts

    def save_logs_to_result_dir_by_tln_or_ssh(self, case_name, timeout=900):
        """保存交互式获取到的log到测试结果目录下，save_logs_to_result_dir_by_tln_or_ssh"""
        aklog_info()
        if self.device_config.get_remote_connect_type() == 'ssh':
            ret = self.get_result_by_interactive_ssh_thread(timeout)
        else:
            ret = self.get_result_by_interactive_telnet_thread(timeout)
        results = ret.split('\n')
        log_time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file_name = 'PhoneLog--{}--{}--{}.log'.format(case_name, self.device_name, log_time)
        log_file = '{}\\{}'.format(log_dir, log_file_name)
        os.makedirs(log_dir, exist_ok=True)
        with open(log_file, 'w') as f:
            f.writelines(results)
        aklog_info(f'log_file: {log_file}')
        # 如果开启保存到共享文件夹，则log文件路径增加HTTP访问URL
        report_dir_url = get_share_http_report_dir_url()
        if report_dir_url:
            log_file_url = '{}/device_log/{}'.format(report_dir_url, log_file_name)
            aklog_info(f'log_file_url: {log_file_url}')
        return log_file

    def get_upload_capture_time_by_log(self):
        """获取上传截图的时间"""
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d | grep -v grep | grep "nTimestamp=" | tail -1 | cut -d "=" -f 2'
        else:
            command = 'cat /tmp/Messages | grep -v grep | grep "nTimestamp=" | tail -1 | cut -d "=" -f 2'
        time_stamp = self.get_result_by_tln_or_ssh(command)
        if time_stamp:
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time_stamp)))
        else:
            time_str = None
        return time_str

    def start_capture_syslog(self):
        """开启抓取log统一方法"""
        aklog_info()
        if self.device_config.get_reboot_clear_syslog():
            self.start_logs_by_interactive_tln_or_ssh()
            self.capture_syslog_enable = True

    def export_syslog_to_result(self, case_name):
        """保存日志到测试结果目录"""
        export_syslog_type = self.device_config.get_default_export_syslog_type()
        if self.capture_syslog_enable:
            self.capture_syslog_enable = False
            self.save_logs_to_result_dir_by_tln_or_ssh(case_name)
        elif export_syslog_type == 'upload':
            self.upload_log_by_tln_or_ssh(case_name)
        elif export_syslog_type == 'logcat' or export_syslog_type == 'cat':
            self.export_syslog_to_results_dir_by_tln_or_ssh(case_name)
        else:
            self.export_syslog_to_results_dir(case_name)

    # endregion


if __name__ == '__main__':
    device_info = {'ip': '192.168.88.123', 'device_name': 'PG42'}
    device_config = config_parse_device_config('config_PG42_NORMAL')
    web_inf = AkubelaPanelWebInf()
    web_inf.init(device_info, device_config)
    ret = web_inf.login(return_resp=True)
    print(ret)
    web_inf.set_log_level()
