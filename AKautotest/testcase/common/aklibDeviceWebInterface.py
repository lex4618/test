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


class DeviceWebInterface(object):

    # region 初始化

    def __init__(self):
        self.web_branch = 'WEB4_0'
        self.username = 'admin'
        self.password = 'admin'
        self.encrypt_password = ''
        self.base_url = ''
        self.host = ''
        self.device_info = None
        self.device_name = ''
        self.device_ip = ''
        self.device_mac = ''
        self.device_config = None
        self.api = None
        self.headers = {}
        self.token = ''
        self.interface_info = None
        self.config_info = None
        self.enabled_option = None
        self.rom_version = ''
        self.tln = None
        self.ssh = None
        self.tln_ssh_port_list = None
        self.tln_ssh_pwd_list = None
        self.version_branch = None
        self.force_replace_old_version = False
        self.device_cfg_66 = ''
        self.device_cfg_43 = ''
        self.device_cfg_custom = ''
        self.device_cfg_pnp = ''
        self.device_cfg_URL = ''
        self.device_comm_cfg_66 = ''
        self.device_comm_cfg_43 = ''
        self.device_comm_cfg_custom = ''
        self.device_comm_cfg_pnp = ''
        self.device_comm_cfg_URL = ''
        self.device_config_dict_by_version = {}
        self.model_name = ''
        self.oem_name = ''
        self.test_file_root_path = ''

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

        if self.version_branch:
            self.interface_info = self.device_config.get_device_web_interface_info(
                self.version_branch, self.web_branch)
        else:
            self.interface_info = config_parse_common_web_interface_info_from_ini(self.web_branch)
        self.config_info = self.interface_info['web_config_info']
        self.enabled_option = self.interface_info['enable_option']

        self.host = 'http://%s' % self.device_ip
        self.base_url = 'http://%s/web' % self.device_ip
        self.api = ApiRequests(self.device_name)

        self.rom_version = param_get_rom_version()

        if self.device_config.get_autop_cfg_use_mac_enable():
            self.device_cfg_66 = self.device_config.get_dhcp_option_66_dir() + self.device_mac + '.cfg'
            self.device_cfg_43 = self.device_config.get_dhcp_option_43_dir() + self.device_mac + '.cfg'
            self.device_cfg_custom = self.device_config.get_dhcp_option_custom_dir() + self.device_mac + '.cfg'
            self.device_cfg_pnp = self.device_config.get_pnp_dir() + self.device_mac + '.cfg'
            self.device_cfg_URL = self.device_config.get_manual_URL_dir() + self.device_mac + '.cfg'
        else:
            self.device_cfg_66 = self.device_config.get_devicecfg_66()
            self.device_cfg_43 = self.device_config.get_devicecfg_43()
            self.device_cfg_custom = self.device_config.get_devicecfg_custom()
            self.device_cfg_pnp = self.device_config.get_devicecfg_pnp()
            self.device_cfg_URL = self.device_config.get_devicecfg_URL()

        self.device_comm_cfg_66 = self.device_config.get_devicecfg_66()
        self.device_comm_cfg_43 = self.device_config.get_devicecfg_43()
        self.device_comm_cfg_custom = self.device_config.get_devicecfg_custom()
        self.device_comm_cfg_pnp = self.device_config.get_devicecfg_pnp()
        self.device_comm_cfg_URL = self.device_config.get_devicecfg_URL()

        self.tln_ssh_port_list = self.device_config.get_tln_ssh_port_list()
        self.tln_ssh_pwd_list = self.device_config.get_tln_or_ssh_pwd()
        self.tln = TelnetConnection(
            self.device_ip, self.tln_ssh_port_list, 'root', self.tln_ssh_pwd_list, self.device_name)
        self.ssh = SSHConnection(
            self.device_ip, self.tln_ssh_port_list, 'root', self.tln_ssh_pwd_list, self.device_name)

        # 获取module机型分支目录下TestFile路径
        self.model_name = self.device_config.get_model_name()
        self.oem_name = self.device_config.get_oem_name()
        if self.test_file_root_path:
            self.test_file_root_path = config_get_series_module_sub_path(
                self.model_name, self.version_branch, 'TestFile')

    def web_env_init(self):
        self.set_session_timeout(14400)

    # endregion

    # region 通用API

    def api_get(self, url, params=None, fail_return_resp=False):
        """发送get请求"""
        if params:
            resp = self.api.get(url=url, headers=self.headers, params=params)
        else:
            resp = self.api.get(url=url, headers=self.headers)
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
        except:
            aklog_error('api get Fail: ' + str(resp.text))
            return None

    def api_post(self, url, data, fail_return_resp=False):
        """发送post请求"""
        if data and isinstance(data, dict):
            data = json.dumps(data)
        resp = self.api.post(url=url, headers=self.headers, data=data)
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
        except:
            aklog_error('api post fail: ' + str(resp.text))
            return False

    def api_post_file(self, url, file, fail_return_resp=False):
        """发送post请求上传文件"""
        file_name = os.path.split(file)[1]
        files = {'file': (file_name, open(file, 'rb'), 'application/octet-stream')}
        resp = self.api.post(url=url, headers=self.headers, files=files)
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
        except:
            aklog_debug('api post file Fail: ' + str(resp.text))
            return False

    def api_download(self, url, save_path=None, **kwargs):
        """下载/导出文件"""
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

    def login(self, return_resp=False):
        """登录"""
        self.get_web_status()
        # 判断是否已登录
        if self.token and self.headers and self.is_login():
            return True
        aklog_info('%s:%s 开始登录' % (self.username, self.password))
        self.encrypt_password = self.get_encrypt_password(self.password)
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
        resp = self.api_post(self.base_url, data=data)
        if resp and isinstance(resp, dict):
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
            aklog_error('%s:%s 登录失败' % (self.username, self.password))
            return False

    def is_login(self):
        """判断是否已经登录"""
        aklog_info()
        data = {
            "target": "config",
            "action": "info",
            "configData": {
                "item": ['MODEL&29&1']
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(self.base_url, data)
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
        aklog_info()
        url = '%s/status/get' % self.base_url
        params = {'session': self.token,
                  'web': '1'}
        resp = self.api_get(url, params)
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
        password = 'rBd3mQ68jfEGo3K3' + password
        data = {
            "target": "login",
            "action": "set",
            "data": {
                "password": password
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(self.base_url, data)
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
        resp = self.api_post(self.base_url, data=data)
        if resp and isinstance(resp, dict):
            aklog_info('登出成功')
            return True
        else:
            aklog_error('登出失败')
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
        resp = self.api_post(self.base_url, data)
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
        resp = self.api_post(self.base_url, data)
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
        path = self.base_url + '/%s/get' % table_name
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
        index: 注册帐号1或账号2，'1'、'2'
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

    def wait_for_account_to_register_successfully(self, account=1, timeout=60, failure_to_wait_time=15):
        """等待帐号注册成功"""
        aklog_info()
        begin_time = int(time.time())
        while True:
            account_status = self.get_account_register_status(account)
            if account_status == 'Registered':
                aklog_info('sip account register success')
                return True
            elif account_status == 'Disabled':
                aklog_info('sip account status: %s' % account_status)
                return False
            elif account_status == 'Registration Failed' and int(time.time()) - begin_time < timeout:
                # 有些情况会先显示注册失败，然后再等一段时间后再注册成功
                timeout = int(time.time()) - begin_time
                time.sleep(1)
                continue
            elif int(time.time()) - begin_time >= timeout + failure_to_wait_time:
                aklog_error('sip account register failed')
                return False
            else:
                time.sleep(3)
                continue

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

    def reboot(self):
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
        resp = self.api_post(self.base_url, data)
        if resp:
            aklog_debug('reboot request success')
        else:
            aklog_error('reboot request failed')

        reboot_ret = cmd_waiting_for_device_reboot(self.device_ip, 60, self.device_config.get_reboot_default_time())
        re_login_ret = self.login()

        if reboot_ret and re_login_ret:
            aklog_info('重启完成')
            return True
        if not reboot_ret:
            aklog_error('重启失败')
        if not re_login_ret:
            aklog_error('重启之后重新登录失败')
        return False

    def reset_config_to_factory_setting(self):
        """恢复配置到出厂设置"""
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
        resp = self.api_post(self.base_url, data)
        if resp:
            aklog_debug('reset request success')
        else:
            aklog_error('reset request failed')

        reboot_ret = cmd_waiting_for_device_reboot(self.device_ip, 60, self.device_config.get_reset_default_time())
        if not reboot_ret:
            aklog_error('恢复出厂，设备重启失败')
            return False

        if self.username == 'admin':
            self.password = self.device_config.get_web_admin_passwd()
        else:
            self.username = self.device_config.get_web_custom_username()
            self.password = self.device_config.get_web_custom_passwd()

        re_login_ret = self.login(return_resp=True)
        if not re_login_ret:
            aklog_error('恢复出厂之后重新登录失败')
            return False
        elif re_login_ret['data']['isFirstLogin'] == 1:
            aklog_info('恢复出厂成功')
            return True
        else:
            aklog_error('恢复出厂失败，重新登录时不是第一次登录')
            return False

    def reset_to_factory_setting(self):
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
        resp = self.api_post(self.base_url, data)
        if resp:
            aklog_debug('reset request success')
        else:
            aklog_error('reset request failed')

        reboot_ret = cmd_waiting_for_device_reboot(self.device_ip, 60, self.device_config.get_reset_default_time())
        if not reboot_ret:
            aklog_error('恢复出厂，设备重启失败')
            return False

        if self.username == 'admin':
            self.password = self.device_config.get_web_admin_passwd()
        else:
            self.username = self.device_config.get_web_custom_username()
            self.password = self.device_config.get_web_custom_passwd()

        re_login_ret = self.login(return_resp=True)
        if not re_login_ret:
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
        cmd_waiting_for_device_reboot(self.device_ip)
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
        resp = self.api_post(self.base_url, upgrade_data)
        if resp and isinstance(resp, dict):
            aklog_info('send_upgrade_request OK')
            return True
        else:
            aklog_error('send_upgrade_request Fail')
            return False

    def _upload_firmware_file(self, firmware_file):
        """上传升级包"""
        aklog_info()
        upload_url = '%s/upgrade/upload?session=%s&web=1' % (self.base_url, self.token)
        resp = self.api_post_file(upload_url, firmware_file)
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
        self.device_config.get_old_firmware(force_replace=self.force_replace_old_version)  # 强制替换旧版本升级包
        old_firmware_version = self.device_config.get_old_firmware_version()
        old_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(True), old_firmware_version,
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

    # region autop配置文件

    def get_test_file(self, file_dir, file_name):
        series_file = '%s\\%s\\NORMAL\\%s' % (self.test_file_root_path, file_dir, file_name)
        model_normal_file = '%s\\%s\\%s\\NORMAL\\%s' % (self.test_file_root_path, file_dir, self.model_name, file_name)
        model_oem_file = '%s\\%s\\%s\\%s\\%s' % (self.test_file_root_path, file_dir, self.model_name,
                                                 self.oem_name, file_name)
        if os.access(model_oem_file, os.F_OK):
            test_file = model_oem_file
        elif os.access(model_normal_file, os.F_OK):
            test_file = model_normal_file
        elif os.access(series_file, os.F_OK):
            test_file = series_file
        else:
            test_file = ''
        if test_file.endswith('\\'):
            test_file = ''
        return test_file

    def get_autop_config_file(self):
        autop_config_file = self.get_test_file('autop_config_file', 'autop.cfg')
        if not os.path.exists(autop_config_file):
            autop_config_file = self.device_config.get_autop_config_file()
        return autop_config_file

    def get_device_cfg_URL(self):
        return self.device_cfg_URL

    def rename_all_cfg_file(self):
        File_process.rename_file(self.device_cfg_66, self.device_config.get_renamecfg_66())
        File_process.rename_file(self.device_cfg_43, self.device_config.get_renamecfg_43())
        File_process.rename_file(self.device_cfg_URL, self.device_config.get_renamecfg_URL())
        File_process.rename_file(self.device_cfg_custom, self.device_config.get_renamecfg_custom())
        File_process.rename_file(self.device_cfg_pnp, self.device_config.get_renamecfg_pnp())

    def copy_old_firmware_to_download_dir(self):
        """将机型对应OEM的旧版本复制到autop下载目录"""
        self.device_config.get_old_firmware(force_replace=self.force_replace_old_version)  # 强制替换旧版本升级包
        File_process.copy_file(self.device_config.get_old_firmware_path(),
                               self.device_config.get_http_dir() + self.device_config.get_old_firmware_file())
        File_process.copy_file(self.device_config.get_old_firmware_path(),
                               self.device_config.get_https_dir() + self.device_config.get_old_firmware_file())
        File_process.copy_file(self.device_config.get_old_firmware_path(),
                               self.device_config.get_tftp_dir() + self.device_config.get_old_firmware_file())
        File_process.copy_file(self.device_config.get_old_firmware_path(),
                               self.device_config.get_ftp_dir() + self.device_config.get_old_firmware_file())

    def write_cfg_to_upgrade_pnp(self):
        config_firmware_url = self.device_config.get_config_firmware_url_pnp()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url
        File_process.rename_file(self.device_config.get_renamecfg_pnp(), self.device_cfg_pnp)
        File_process.write_file(self.device_cfg_pnp, config_firmware_url)

    def write_cfg_to_upgrade_43(self):
        config_firmware_url = self.device_config.get_config_firmware_url_43()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url
        File_process.rename_file(self.device_config.get_renamecfg_43(), self.device_cfg_43)
        File_process.write_file(self.device_cfg_43, config_firmware_url)

    def write_cfg_to_upgrade_66(self):
        config_firmware_url = self.device_config.get_config_firmware_url_66()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url
        File_process.rename_file(self.device_config.get_renamecfg_66(), self.device_cfg_66)
        File_process.write_file(self.device_cfg_66, config_firmware_url)

    def write_cfg_to_upgrade_custom(self):
        config_firmware_url = self.device_config.get_config_firmware_url_custom()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url
        File_process.rename_file(self.device_config.get_renamecfg_custom(), self.device_cfg_custom)
        File_process.write_file(self.device_cfg_custom, config_firmware_url)

    def write_cfg_to_upgrade_manual_URL(self):
        config_firmware_url = self.device_config.get_config_firmware_url_manual_URL()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url
        File_process.rename_file(self.device_config.get_renamecfg_URL(), self.device_cfg_URL)
        File_process.write_file(self.device_cfg_URL, config_firmware_url)

    def write_config_to_pnp_cfg(self, *configs):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        File_process.rename_file(self.device_config.get_renamecfg_pnp(), self.device_cfg_pnp)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        config_content = f'# {str(time.time())}\n' + config_content
        File_process.write_file(self.device_cfg_pnp, config_content)

    def write_config_to_option43_cfg(self, *configs):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        File_process.rename_file(self.device_config.get_renamecfg_43(), self.device_cfg_43)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        File_process.write_file(self.device_cfg_43, config_content)

    def write_config_to_option66_cfg(self, *configs):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        File_process.rename_file(self.device_config.get_renamecfg_66(), self.device_cfg_66)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        File_process.write_file(self.device_cfg_66, config_content)

    def write_config_to_custom_option_cfg(self, *configs):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        File_process.rename_file(self.device_config.get_renamecfg_custom(), self.device_cfg_custom)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        File_process.write_file(self.device_cfg_custom, config_content)

    def write_config_to_manual_URL_cfg(self, *configs, comm_or_mac='mac'):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        if comm_or_mac == 'mac':
            device_cfg = self.device_cfg_URL
        else:
            device_cfg = self.device_comm_cfg_URL
        File_process.rename_file(self.device_config.get_renamecfg_URL(), device_cfg)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        File_process.write_file(device_cfg, config_content)

    def copy_cfg_to_config_pnp(self):
        """将配置文件复制到手动URL的下载目录替换"""
        File_process.rename_file(self.device_config.get_renamecfg_pnp(), self.device_cfg_pnp)
        File_process.copy_file(self.device_config.get_autop_config_file(), self.device_cfg_pnp)

    def copy_cfg_to_config_43(self):
        """将配置文件复制到手动URL的下载目录替换"""
        File_process.rename_file(self.device_config.get_renamecfg_43(), self.device_cfg_43)
        File_process.copy_file(self.device_config.get_autop_config_file(), self.device_cfg_43)

    def copy_cfg_to_config_66(self):
        """将配置文件复制到手动URL的下载目录替换"""
        File_process.rename_file(self.device_config.get_renamecfg_66(), self.device_cfg_66)
        File_process.copy_file(self.device_config.get_autop_config_file(), self.device_cfg_66)

    def copy_cfg_to_config_custom(self):
        """将配置文件复制到手动URL的下载目录替换"""
        File_process.rename_file(self.device_config.get_renamecfg_custom(), self.device_cfg_custom)
        File_process.copy_file(self.device_config.get_autop_config_file(), self.device_cfg_custom)

    def copy_cfg_to_config_manual_URL(self):
        """将配置文件复制到手动URL的下载目录替换"""
        File_process.rename_file(self.device_config.get_renamecfg_URL(), self.device_cfg_URL)
        File_process.copy_file(self.device_config.get_autop_config_file(), self.device_cfg_URL)

    def copy_autop_export_file_to_config_import_file(self):
        """将autop导出模板复制到导入文件目录替换"""
        File_process.copy_file(self.device_config.get_autop_export_file_path(),
                               self.device_config.get_config_import_file())

    def copy_config_file_to_config_import_file(self):
        """将config导出文件复制到导入文件目录替换"""
        File_process.copy_file(self.device_config.get_config_file_path(),
                               self.device_config.get_config_import_file_tgz())

    def copy_mac_aes_cfg_to_config_manual_URL(self, ):
        """将AES加密配置文件复制到手动URL的下载目录替换MAC文件"""
        File_process.remove_file(self.device_comm_cfg_URL)
        File_process.copy_file(self.device_config.get_aes_autop_config_file(), self.device_cfg_URL)

    def copy_common_aes_cfg_to_config_manual_URL(self, ):
        """将AES加密配置文件复制到手动URL的下载目录替换Config文件"""
        File_process.remove_file(self.device_cfg_URL)
        File_process.copy_file(self.device_config.get_aes_autop_config_file(), self.device_comm_cfg_URL)

    def remove_mac_config_manual_URL(self):
        """移除手动URL的下载目录下的MAC config配置文件"""
        File_process.remove_file(self.device_cfg_URL)

    def remove_common_config_manual_URL(self):
        """移除手动URL的下载目录下的Common config配置文件"""
        File_process.remove_file(self.device_comm_cfg_URL)

    # endregion

    # region Upgrade Advanced升级高级页面

    # region Autop相关

    def clear_autop(self):
        """将autop相关配置项关闭或清空"""
        aklog_info()
        self.edit_config(PNPEnable='0', CustomOption='', AutopURL='',
                         AutopUserName='', AutopPassword='', AutopMode='1')
        self.clear_autop_md5()

    def clear_autop_md5(self):
        aklog_info()
        data = {
            "target": "autop",
            "action": "del",
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(self.base_url, data)
        if resp:
            aklog_info('clear_autop_md5 OK')
            return True
        else:
            aklog_error('clear_autop_md5 Fail')
            return False

    def start_autop(self, autop_type):
        """点击立即autop，开始autop升级"""
        data = {
            "target": "autop",
            "action": "start",
            "session": self.token,
            "web": "1"
        }
        self.api_post(self.base_url, data)
        self.is_autop()
        if autop_type == 'rom':
            cmd_waiting_for_device_reboot(self.device_ip)
            self.login()
            self.wait_autop_rom_finished()
        else:
            self.wait_autop_cfg_finished()

    def is_autop(self):
        """判断是否处于autop状态"""
        data = {
            "target": "autop",
            "action": "info",
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(self.base_url, data)
        if resp:
            aklog_info('is autop OK')
            return True
        else:
            aklog_error('is autop Fail')
            return False

    def wait_autop_rom_finished(self):
        """autop升级软件回到登录界面"""
        """ {
            "retcode": 0,
            "action": "get",
            "message": "OK",
            "data": {
                "PhoneStatus": 1,
                "WebLang": 0,
                "HardwareModel": "S562",
                "ProductName": "S562",
                "WebTitle": "IP Phone"
            }
        }
        """
        url = '%s/status/get' % self.base_url
        params = {'session': self.token,
                  'web': '1'}
        resp = self.api_get(url, params)
        if resp and isinstance(resp, dict):
            aklog_info('autop finished and in web login page OK')
            return True
        else:
            aklog_error('autop finished and in web login page Fail')
            return False

    def wait_autop_cfg_finished(self):
        """autop升级配置回到升级界面"""
        for i in range(20):
            resp = self.get_autop_status()
            if resp['data']['State']['AutopNowState'] != "5":
                aklog_info("AutopNowState:" + resp['data']['State']['AutopNowState'])
                aklog_info('in autop satus')
                time.sleep(5)
            else:
                aklog_info('not in autop satus')
                time.sleep(10)
                return True

    def get_autop_status(self):
        """获取autop状态"""
        """
        {
            "retcode":0,
            "action":"info",
            "message":"OK",
            "data":{
                "State":{
                    "AutopNowState":"5",
                    "AutopNowReason":""
                }
            }
        }
        """
        url = '%s/autop/info' % self.base_url
        params = {'session': self.token,
                  'web': '1'}
        resp = self.api_get(url, params)
        if resp and isinstance(resp, dict):
            aklog_info('get autop status OK')
            return resp
        else:
            aklog_error('get autop status Fail')
            return False

    def pnp_autop(self, autop_type='rom'):
        """PNP方式autop升级"""
        aklog_info('start pnp_autop')
        self.clear_autop()
        self.edit_config(PNPEnable='1')
        return self.start_autop(autop_type)

    def manual_URL_autop(self, autop_type='rom'):
        aklog_info('start manual_URL_autop')
        self.clear_autop()
        self.edit_config(AutopURL=self.device_config.get_manual_autop_URL())
        self.start_autop(autop_type)

    def export_autop_template(self):
        """导出autop模板文件"""
        aklog_info()
        data = {
            "target": "autop",
            "action": "export",
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(self.base_url, data)
        download_url = '%s%s' % (self.host, resp['data']['address'])
        export_file = self.device_config.get_autop_export_file_path()
        # 先删除文件
        File_process.remove_file(export_file)
        # 下载文件
        r = self.api_download(download_url, export_file)
        if r:
            aklog_info('autop template export success')
            return True
        else:
            aklog_error('autop template export failed')
            return False

    def compare_autop_config_with_template(self, cfg_file):
        aklog_info('对比autop升级配置项是否都升级成功')
        if not self.export_autop_template():
            return False
        export_file = self.device_config.get_autop_export_file_path()
        config_diff = File_process.compare_config_value(cfg_file, export_file)
        if config_diff is not None and len(config_diff) == 0:
            aklog_info('autop升级配置项成功')
            return True
        else:
            aklog_error('存在配置项autop升级失败')
            aklog_info('%s' % config_diff)
            return False

    # endregion

    # endregion

    # region Upgrade Diagnosis页面

    def set_log_level(self, level=7):
        """设置log等级"""
        self.edit_config(LogLevel=level)

    def export_system_log(self):
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
        resp = self.api_post(self.base_url, data)
        if resp:
            aklog_info('log export success')
            return True
        else:
            aklog_error('log export failed')
            return False

    def start_pcap(self):
        """开始抓包"""
        aklog_info()
        data = {
            "target": "maintenance",
            "action": "start",
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(self.base_url, data)
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
        resp = self.api_post(self.base_url, data)
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
        resp = self.api_post(self.base_url, data)
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
        resp = self.api_post(self.base_url, data)
        if resp:
            aklog_info('config file export success')
            return True
        else:
            aklog_error('config file export failed')
            return False

    # endregion

    # region Security Basic页面

    def set_session_timeout(self, timeout):
        """设置网页超时时间"""
        aklog_info()
        self.edit_config(SessionTimeout=timeout)

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
        resp = self.api_post(self.base_url, data)
        if resp:
            aklog_debug('set ssh open OK')
            return True
        else:
            aklog_error('set ssh open Fail')
            return False

    def web_open_ssh(self):
        return self.set_ssh_or_tln()

    # endregion

    # region Telnet/SSH命令

    def telnet_login(self):
        for i in range(5):
            if self.tln.login_host():
                self.tln_ssh_port_list = self.tln.get_port_list()
                self.tln_ssh_pwd_list = self.tln.get_pwd_list()
                return True
            elif i < 2:
                self.web_open_ssh()
                continue
            elif i < 4:
                time.sleep(5)
                continue
            else:
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
            elif i < 2:
                self.web_open_ssh()
                continue
            elif i < 4:
                time.sleep(5)
                continue
            else:
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

    def get_value_by_ssh(self, command, print_result=True):
        """后台执行命令获取对应配置的值"""
        aklog_debug()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return None
        value = self.ssh.command_result(command)
        if value:
            value = value.encode('gbk', 'ignore').decode('gbk')
        if print_result:
            aklog_debug('result: %s' % value)
        return value

    def get_result_by_telnet_command(self, command, print_result=True):
        """后台执行命令获取对应配置的值"""
        aklog_debug()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return None
        result = self.tln.command_result(command)
        if print_result:
            aklog_debug('result: %s' % result)
        return result

    def get_result_by_tln_or_ssh(self, command, print_result=True):
        """telnet或SSH执行命令并获取结果"""
        if self.device_config.get_remote_connect_type() == 'telnet':
            result = self.get_result_by_telnet_command(command, print_result)
        else:
            result = self.get_value_by_ssh(command, print_result)
        return result

    def exec_command_by_tln(self, *commands, timeout=10):
        aklog_debug()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return False
        for command in commands:
            self.tln.exec_command(command, timeout)
            time.sleep(0.5)
        return True

    def exec_command_by_ssh(self, *commands, timeout=60):
        aklog_debug()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return False
        for command in commands:
            self.ssh.exec_command_no_back(command, timeout)
            time.sleep(0.5)
        return True

    def command_by_tln_or_ssh(self, *commands, timeout=60):
        if self.device_config.get_remote_connect_type() == 'telnet':
            return self.exec_command_by_tln(*commands, timeout=timeout)
        else:
            return self.exec_command_by_ssh(*commands, timeout=timeout)

    def exec_command_by_interactive_ssh_thread(self, command):
        """ssh交互式子线程执行，需要与get_result_by_interactive_ssh_thread配合使用"""
        aklog_debug()
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

    def get_result_by_interactive_ssh_thread(self, timeout=60):
        """获取SSH交互式子线程执行结果，需要与exec_command_by_interactive_ssh_thread配合使用"""
        return self.ssh.interactive_return_log(timeout=timeout)

    def ignore_previous_logs_by_interactive_ssh_thread(self, wait_time=3):
        """先获取一次结果，然后再次获取结果时就不会包含之前的结果，这样就不需要logcat -c清空掉之前的log了
        需要与exec_command_by_interactive_ssh_thread配合使用（该方法有点问题，先不要使用）"""
        result1 = self.ssh.interactive_return_log(wait_time)
        return result1

    def exec_command_by_interactive_telnet_thread(self, command):
        """Telnet交互式子线程执行，需要与get_result_by_interactive_telnet_thread配合使用"""
        aklog_debug()
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
        """获取Telnet交互式子线程执行结果，需要与exec_command_by_interactive_ssh_thread配合使用"""
        return self.tln.thread_stop_exec_output_result(timeout=timeout)

    # endregion

    # region telnet/SSH 进程相关

    def top_get_memory_info(self):
        """获取内存使用情况"""
        aklog_info()
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
        aklog_info()
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
        aklog_info()
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
        attribute = self.get_result_by_tln_or_ssh('ps | grep "PID" | grep -v grep')
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_info('attribute_list: %r' % attribute_list)
        grep_command = ''
        for i in process_flag:
            grep_command += '| grep "%s" ' % i
        info = self.get_result_by_tln_or_ssh('ps | grep -v grep %s' % grep_command)
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

        aklog_info('process_info: %r' % process_info)
        return process_info

    def ps_get_all_info(self):
        info = self.get_result_by_tln_or_ssh('ps')
        return info

    def ps_judge_processes_is_running(self, *processes):
        """ps获取进程信息，判断多个进程是否都正在运行"""
        aklog_info()
        not_running_process_list = []
        for process in processes:
            ps_command = 'ps | grep -v grep | grep "%s"' % process
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
            aklog_info('有进程未运行: %r' % not_running_process_list)
            return False

    def check_device_process_status(self):
        """检查设备进程的状态，是否都在运行，由于各机型的进程信息可能不一致，可以重写该方法"""
        aklog_info()
        status = self.ps_judge_processes_is_running('/app/bin/sip',
                                                    '/app/bin/phone',
                                                    '/app/bin/netconfig',
                                                    '/app/bin/fcgiserver.fcgi',
                                                    '/app/bin/acgVoice',
                                                    '/app/bin/autop')
        return status

    # endregion

    # region telnet/ssh log相关
    def clear_logs_by_ssh(self):
        """如果是交互式获取log，可以使用ignore_previous_logs_by_interactive_ssh_thread代替"""
        aklog_info('clear_logs_by_ssh')
        self.exec_command_by_ssh('logcat -G 2M', 'logcat -c')

    def clear_logs_by_tln(self):
        aklog_info('clear_logs_by_tln')
        self.command_by_tln_or_ssh('rm /tmp/Messages* -f', 'echo "" > /tmp/Messages')

    def clear_logs_by_tln_or_ssh(self):
        """如果是交互式获取log，可以使用ignore_previous_logs_by_interactive_ssh_thread代替"""
        if self.device_config.get_remote_connect_type() == 'ssh':
            self.clear_logs_by_ssh()
        else:
            self.clear_logs_by_tln()

    def set_logcat_buffer_size(self, size='2M'):
        """
        设置logcat缓冲区大小，避免因为缓冲区太小，短时间打印太多log导致logcat中断
        size: 2M
        """
        self.exec_command_by_ssh('logcat -G %s' % size)

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
        if ssh_log:
            return True
        else:
            aklog_info('%s 日志不存在' % flag)
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
            command += ' | grep -v grep | grep "%s"' % log_flag
        ssh_log = self.get_result_by_tln_or_ssh(command, print_result=False)
        return ssh_log

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
            self.set_logcat_buffer_size()
            self.exec_command_by_interactive_ssh_thread(command)
        else:
            command = 'tail -F /tmp/Messages%s' % log_flag
            self.exec_command_by_interactive_telnet_thread(command)

    def get_logs_by_interactive_tln_or_ssh(self):
        """交互式获取设备log，需要配合start_logs_by_interactive_tln_or_ssh使用"""
        aklog_info()
        if self.device_config.get_remote_connect_type() == 'ssh':
            ret = self.get_result_by_interactive_ssh_thread()
        else:
            ret = self.get_result_by_interactive_telnet_thread()
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
        aklog_info('%s 出现次数: %s' % (flag, counts))
        return counts

    def save_logs_to_result_dir_by_tln_or_ssh(self, case_name):
        """保存交互式获取到的log到测试结果目录下，save_logs_to_result_dir_by_tln_or_ssh"""
        aklog_info()
        if self.device_config.get_remote_connect_type() == 'ssh':
            ret = self.get_result_by_interactive_ssh_thread()
        else:
            ret = self.get_result_by_interactive_telnet_thread()
        results = ret.split('\n')
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file = '{}\\PhoneLog--{}--{}--{}.txt'.format(log_dir, case_name, self.device_name, log_time)
        File_process.create_dir(log_dir)
        with open(log_file, 'w') as f:
            f.writelines(results)
        aklog_debug(f'log_file: {log_file}')

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

    # endregion


if __name__ == '__main__':
    device_info = {'ip': '1.0.0.128', 'device_name': 'master_linux_indoor'}
    device_config = config_parse_device_config('config_S562_NORMAL')
    web_inf = DeviceWebInterface()
    web_inf.init(device_info, device_config)
    web_inf.login()
    # web_inf.register_sip('1008', 'abc1008', '192.168.10.28')
    # web_inf.get_firmware_version()
    web_inf.export_autop_template()
    # web_inf.edit_config(account1_Label='12343', account1_DisplayName='abc')
    # web_inf.upgrade_firmware('562.30.0.45', r'D:\Users\Administrator\Desktop\562.30.0.45.rom')
