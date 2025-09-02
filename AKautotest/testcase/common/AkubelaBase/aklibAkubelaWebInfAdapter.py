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
from testcase.common.aklibApiRequests import ApiRequests
from libconfig.COMMON.libconfig_NORMAL import config_NORMAL
import hashlib

__all__ = [
    'get_product_info_by_web_inf',
    'engr_web_open_ssh'
]


class AkubelaWebInfAdapter(object):

    # region 初始化

    def __init__(self):
        self.web_branch = 'WEB4_0'
        self.username = 'admin'
        self.password = 'admin'
        self.new_pwd = 'Ak#123456'  # 强制修改的新密码
        self.encrypt_password = ''
        self.base_url = ''
        self.host = ''
        self.device_info = None
        self.device_name = ''
        self.device_ip = ''
        self.device_mac = ''
        self.device_config: Optional[config_NORMAL] = None
        self.api: Optional[ApiRequests] = None
        self.headers = {}
        self.token = ''
        self.interface_info = None
        self.config_info = None
        self.enabled_option = None
        self.version_branch = None
        self.series_product_name = ''
        self.model_name = ''
        self.oem_name = ''
        self.test_file_root_path = ''

    def init(self, device_info, device_config: Optional[config_NORMAL] = None, timeout=60):
        """
        初始化用户web接口信息
        """
        self.device_info = device_info
        if self.device_info and 'device_name' in self.device_info:
            self.device_name = self.device_info.get('device_name')
        self.device_ip = self.device_info.get('ip')
        self.base_url = 'http://%s:8080/api' % self.device_ip
        self.api = ApiRequests(f'{self.device_name}.api', timeout=timeout)
        if device_config:
            self.device_config = device_config
            self.model_name = self.device_config.get_model_name()
            self.series_product_name = self.device_config.get_series_product_name()

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
        if not self.is_linux_panel():
            if not self.get_web_status() and not self.get_web_status_linux():
                return False
        else:
            if not self.get_web_status_linux() and not self.get_web_status():
                return False

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
            }
            if self.is_linux_panel():
                data['web'] = '1'
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
                old_pwd = self.password
                if self.password != 'admin':
                    self.password = 'admin'
                elif self.password != self.new_pwd:
                    self.password = self.new_pwd

                if self.password in checked_pwd_list:
                    break
                aklog_warn('%s:%s 登录失败，更换密码重新登录' % (self.username, old_pwd))
                continue
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
        }
        if self.is_linux_panel():
            data['web'] = '1'
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
        url = '%s/status/get?session=' % self.base_url
        resp = self.api_get(url)
        if resp and isinstance(resp, dict):
            result = resp['data']
            aklog_info(result)
            return result
        else:
            aklog_error('get_web_status Fail')
            return None

    def get_web_status_linux(self):
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
        self.base_url = 'http://%s/web' % self.device_ip
        url = '%s/status/get?session=&web=1' % self.base_url
        resp = self.api_get(url)
        if resp and isinstance(resp, dict):
            result = resp['data']
            aklog_info(result)
            self.model_name = result.get('ProductModel')
            return result
        else:
            aklog_error('get_web_status Fail')
            return None

    def get_device_info(self):
        if self.is_linux_panel():
            return self.get_device_info_linux()

        data = {
            "target": "status",
            "action": "info",
            "web": True,
            "session": self.token
        }
        resp = self.api_post(self.base_url, data=data)
        if resp and isinstance(resp, dict):
            result = resp['data']
            aklog_info(result)
            return result
        else:
            aklog_error('get_device_info fail')
            return None

    def get_device_info_linux(self):
        data = {
            "target": "config",
            "action": "info",
            "configData": {
                "item": [
                    "MODEL&29&1",
                    "MAC&29&16",
                    "ProdectModel&10&2",
                    "Firmware&29&2",
                    "HardWare&29&3",
                    "STATICIP&29&21",
                    "SUBNETMASK&29&22",
                    "GATEWAY&29&23",
                    "DNS1&29&24",
                    "DNS2&29&25"
                ]
            },
            "session": self.token,
            "web": "1"
        }
        resp = self.api_post(self.base_url, data=data)
        if resp and isinstance(resp, dict):
            result = resp['data']
            product_info = {
                'Product': {
                    'ProductName': result['ProdectModel'],
                    'HardwareModel': result['ProdectModel'],
                    'MACAddress': result['MAC'],
                    'FirmwareVersion': result['Firmware'],
                    'HardwareVersion': result['HardWare'],
                    'DeviceCode': '',
                    'WebLang': '0'
                }
            }
            aklog_info(product_info)
            return product_info
        else:
            aklog_error('get_device_info_ks41 fail')
            return None

    def is_linux_panel(self):
        if (self.model_name in ['KS41', 'PG42', 'R10']
                or self.series_product_name == 'HYPANELLINUX'
                or self.series_product_name == 'AKUBELAGATEWAY'
                or self.series_product_name == 'SWITCHGATEWAY'):
            return True
        return False

    # endregion

    # region 8848页面

    def web_open_ssh(self):
        """
        网页8848打开ssh
        """
        aklog_info()
        data = {
            "target": "phoneHidden",
            "action": "set",
            "configData": {
                "telnetEnable": "1"
            },
            "data": {
                "telnetEnable": "1",
            },
            "session": self.token
        }
        self.api_post(self.base_url, data)

    # endregion


def get_product_info_by_web_inf(device_info, device_config=None, timeout=60):
    """
    return:
        {
        "Product": {
            "ProductName": "CT61",
            "HardwareModel": "CT61",
            "MACAddress": "C2:08:24:04:02:01",
            "FirmwareVersion": "161.1.30.1",
            "HardwareVersion": "1.0",
            "DeviceCode": "",
            "WebLang": "0"
        },
        "Network": {
            "LANPortType": "0",
            "LinkStatus": "1",
            "IPAddress": "192.168.88.171",
            "SubnetMask": "255.255.255.0",
            "Gateway": "192.168.88.254",
            "PreferredDNS": "192.168.88.254",
            "AlternateDNS": "0.0.0.0"
        },
        "Accounts": [
            {
            "AccountName": "",
            "AccountServer": "",
            "AccountStatue": "0"
            },
            {
            "AccountName": "221",
            "AccountServer": "192.168.10.27",
            "AccountStatue": "2"
            }
        ],
        "FirstLogin": {
        "isFirstLogin": "3"
        }
    }
    """
    device_name = device_info.get('device_name', '')
    device_ip = device_info.get('ip', '')
    aklog_info(f'获取设备信息: {device_name}, {device_ip}')
    try:
        web_inf = AkubelaWebInfAdapter()
        web_inf.init(device_info, device_config, timeout=timeout)
        if not web_inf.login():
            return None
        return web_inf.get_device_info()
    except Exception as e:
        aklog_warn(e)
        return None


def engr_web_open_ssh(device_ip):
    aklog_info()
    try:
        device_info = {'ip': device_ip}
        web_inf = AkubelaWebInfAdapter()
        web_inf.init(device_info)
        web_inf.login()
        web_inf.web_open_ssh()
    except Exception as e:
        aklog_warn(e)


if __name__ == '__main__':
    engr_web_open_ssh('192.168.88.103')
