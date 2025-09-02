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
from testcase.common.aklibWebsocketClient import AkWSClient
from libconfig.COMMON.libconfig_NORMAL import config_NORMAL
from testcase.common.AkubelaBase.WebV3.aklibAkubelaDefine import CLOUD_PUBLIC_KEY
import time
import traceback
import json
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


class AkubelaWebInfBaseV3(object):

    # region 初始化

    def __init__(self):
        self.local_username = 'admin'
        self.local_password = 'Ak#123456'
        self.username = 'admin'
        self.password = 'Ak#123456'  # 默认登录密码
        self.new_pwd = 'Ak#123456'  # 强制修改的新密码
        self.port = 80
        self.original_url = ''
        self.original_remote_url = ''
        self.base_url = ''
        self.base_path = ''
        self.ws_base_url = ''
        self.login_type = 'local'
        self.access_token = ''
        self.token_type = ''
        self.refresh_token = ''
        self.account_id = ''
        self.ha_token = ''
        self.headers = {'User-Platform': 'pc'}
        self.ha_version = 0.0
        self.ws_client: Optional[AkWSClient] = None
        self.ws_pcap_client: Optional[AkWSClient] = None
        self.ws_pcap_old_url_list = []
        self.pcap_header_data = None
        self.ws_id = 1
        self.family_id = None
        self.ws_id_scan = None
        self.ws_id_scan_ecosystem = None
        self.api: Optional[ApiRequests] = None
        self.device_name = ''
        self._panel_name = ''
        self.device_info = None
        self.device_config: Optional[config_NORMAL] = None
        self.device_ip = ''
        self.device_id = ''
        self.device_mac = ''
        self.device_cfg_pnp = ''
        self.tln: Optional[TelnetConnection] = None
        self.ssh: Optional[SSHConnection] = None
        self.tln_ssh_port_list = None
        self.tln_ssh_pwd_list = None
        self.model_name = ''
        self.model = ''
        self.oem_name = ''
        self.test_file_root_path = ''
        self.version_branch = ''
        self.pcap_tmp_data = ''
        self.force_replace_old_version = True
        self._rom_version = ''
        self.capture_syslog_enable = False

    def init(self, device_info, device_config, username=None, password=None, port=None):
        """
        初始化用户web接口信息
        """
        aklog_info()
        self.device_config = device_config

        if username and password:
            self.username = username
            self.password = password

        if port:
            self.port = port

        self.device_info = device_info
        self.device_ip = device_info['ip']
        if 'MAC' in self.device_info:
            self.device_mac = self.device_info['MAC']
        elif 'mac' in self.device_info:
            self.device_mac = self.device_info['mac']
        if 'device_name' in device_info:
            self.device_name = device_info['device_name']
            self._panel_name = self.device_name
        if self.api is None:
            self.api = ApiRequests(f'{self.device_name}.api')

        if self.ws_client is None:
            self.ws_client = AkWSClient(device_name=f'{self.device_name}.ws')

        self.ws_pcap_old_url_list = [f'ws://{self.device_ip}/api/pcap']
        if self.ws_pcap_client is None:
            self.ws_pcap_client = AkWSClient(
                f'ws://{self.device_ip}:8089/', f'{self.device_name}.ws_pcap')

        self.original_url = f'http://{self.device_ip}:{self.port}'
        self.base_url = self.original_url

        self.tln_ssh_port_list = self.device_config.get_tln_ssh_port_list()
        self.tln_ssh_pwd_list = self.device_config.get_tln_or_ssh_pwd()
        if self.tln is None:
            self.tln = TelnetConnection()
        if self.ssh is None:
            self.ssh = SSHConnection()
        self.tln.init(self.device_ip, self.tln_ssh_port_list, 'root', self.tln_ssh_pwd_list,
                      f'{self.device_name}.tln')
        self.ssh.init(self.device_ip, self.tln_ssh_port_list, 'root', self.tln_ssh_pwd_list,
                      f'{self.device_name}.ssh')
        self.device_name = self.device_name + '.web'

        # 获取module机型分支目录下TestFile路径
        self.model_name = self.device_config.get_model_name()
        self.oem_name = self.device_config.get_oem_name()
        if self.test_file_root_path:
            self.test_file_root_path = config_get_series_module_sub_path(
                self.model_name, self.version_branch, 'TestFile')

        if self.device_config.get_autop_cfg_use_mac_enable():
            self.device_cfg_pnp = self.device_config.get_pnp_dir() + self.device_mac + '.cfg'
        else:
            self.device_cfg_pnp = self.device_config.get_devicecfg_pnp()

    def put_panel_name(self, panel_name):
        if panel_name:
            self._panel_name = panel_name

    @property
    def panel_name(self):
        return self._panel_name

    @panel_name.setter
    def panel_name(self, value):
        self._panel_name = value

    def put_rom_version(self, rom_version):
        self._rom_version = rom_version

    @property
    def rom_version(self):
        return self._rom_version

    @rom_version.setter
    def rom_version(self, value):
        self._rom_version = value

    # endregion

    # region Requests、WebSocket接口通用操作

    def api_get(self, path, params=None, fail_return_resp=False, print_trace=True):
        """发送get请求"""
        if path.startswith('/'):
            path = path[1:]
        if path.startswith('http://') or path.startswith('https://'):
            url = path
        else:
            url = '%s/%s' % (self.base_url, path)
        if params:
            resp = self.api.get(
                url=url, headers=self.headers, params=params,
                fail_return_resp=fail_return_resp, print_trace=print_trace)
        else:
            resp = self.api.get(
                url=url, headers=self.headers,
                fail_return_resp=fail_return_resp, print_trace=print_trace)
        if not resp:
            aklog_error('api get fail')
            return None
        try:
            ret = resp.json()
            if ret['success'] is True or ret['success'] == 'true':
                aklog_debug('api get OK')
                return ret
            else:
                aklog_error('api get fail')
                if fail_return_resp:
                    return ret
                else:
                    return None
        except:
            aklog_debug('api get Fail: ' + str(resp.text))
            if fail_return_resp:
                return resp
            else:
                return None

    def api_post(self, path, data, fail_return_resp=False, print_trace=True) -> Union[dict, bool]:
        """发送post请求"""
        if path.startswith('/'):
            path = path[1:]
        if path.startswith('http://') or path.startswith('https://'):
            url = path
        else:
            url = '%s/%s' % (self.base_url, path)
        if data and isinstance(data, dict):
            data = json.dumps(data)
        resp = self.api.post(
            url=url, headers=self.headers, data=data,
            fail_return_resp=fail_return_resp, print_trace=print_trace)
        if not resp:
            aklog_error('api post fail')
            return False
        try:
            ret = resp.json()
            if ret['success'] is True or ret['success'] == 'true':
                aklog_debug('api post OK')
                return ret
            else:
                aklog_error('api post fail')
                if fail_return_resp:
                    return ret
                else:
                    return False
        except:
            aklog_debug('api post fail: ' + str(resp.text))
            if fail_return_resp:
                return resp
            else:
                return False

    def api_post_file(self, path, file, fail_return_resp=False):
        """发送post请求上传文件"""
        if path.startswith('/'):
            path = path[1:]
        if path.startswith('http://') or path.startswith('https://'):
            url = path
        else:
            url = '%s/%s' % (self.base_url, path)
        file_name = os.path.split(file)[1]
        files = {'file': (file_name, open(file, 'rb'), 'application/octet-stream')}
        resp = self.api.post(url=url, headers=self.headers, files=files, fail_return_resp=fail_return_resp)
        if not resp:
            aklog_debug('api post file fail')
            return False
        try:
            ret = resp.json()
            if ret['success'] is True or ret['success'] == 'true':
                aklog_debug('api post file OK')
                return ret
            else:
                aklog_error('api post file fail')
                if fail_return_resp:
                    return ret
                else:
                    return False
        except:
            aklog_debug('api post file fail: ' + str(resp.text))
            if fail_return_resp:
                return resp
            else:
                return False

    def api_post_chunk_file(self, path, file_path, chunk_size=1024*1024*10, fail_return_resp=False):
        """分片上传文件"""
        if not os.path.exists(file_path):
            aklog_error('升级包 %s 不存在' % file_path)
            return False

        if path.startswith('/'):
            path = path[1:]
        if path.startswith('http://') or path.startswith('https://'):
            url = path
        else:
            url = '%s/%s' % (self.base_url, path)

        # 获取文件名
        file_name = os.path.basename(file_path)
        # 获取文件总大小
        file_size = os.path.getsize(file_path)

        # 打开文件
        with open(file_path, 'rb') as file:
            # 计算总分片数
            total_chunks = file_size // chunk_size + 1

            # 循环遍历每个分片
            for chunk_num in range(total_chunks):
                # 计算当前分片的起始位置和结束位置
                start_byte = chunk_num * chunk_size
                end_byte = min(start_byte + chunk_size, file_size)

                # 读取当前分片
                chunk_data = file.read(end_byte - start_byte)

                # 计算当前分片的MD5值
                md5_hash = hashlib.md5()
                md5_hash.update(chunk_data)
                chunk_md5 = md5_hash.hexdigest()

                # 设置请求头（包含MD5值）
                headers = {
                    'Content-Type': 'application/octet-stream',
                    'Content-Range': f'{chunk_num}/{total_chunks}',
                    'X-File-Md5': chunk_md5,
                    'X-File-Name': file_name,
                    'Refresh-Token': self.headers.get('Refresh-Token', ''),
                    'authorization': self.headers.get('authorization', ''),
                    'User-Platform': self.headers.get('User-Platform', '')
                }

                # 发送请求
                aklog_debug('post: url: %s, headers: %s' % (url, headers))
                resp = self.api.post(url=url, headers=headers, data=chunk_data, print_func_log=False,
                                     fail_return_resp=fail_return_resp)
                if not resp:
                    aklog_error('api post chunk file fail')
                    return False
                continue
        aklog_debug('api post chunk file complete')
        return True

    def api_delete(self, path, fail_return_resp=False):
        """家居云发送delete请求"""
        if path.startswith('/'):
            path = path[1:]
        if path.startswith('http://') or path.startswith('https://'):
            url = path
        else:
            url = '%s/%s' % (self.base_url, path)
        resp = self.api.delete(url=url, headers=self.headers, fail_return_resp=fail_return_resp)
        if not resp:
            aklog_error('api delete fail')
            return False
        try:
            if 300 <= resp.status_code < 400:
                aklog_debug(f'api delete move found, status code: {resp.status_code}')
                return resp

            ret = resp.json()
            if ret['success'] is True or ret['success'] == 'true':
                aklog_debug('api delete OK')
                return ret
            else:
                aklog_error('api delete fail')
                if fail_return_resp:
                    return ret
                else:
                    return False
        except:
            aklog_debug('api delete Fail: ' + str(resp.text))
            if fail_return_resp:
                return resp
            else:
                return False

    def api_download(self, path, params=None, save_path=None, fail_return_resp=False, **kwargs):
        """下载/导出文件"""
        if path.startswith('/'):
            path = path[1:]
        if path.startswith('http://') or path.startswith('https://'):
            url = path
        else:
            url = '%s/%s' % (self.base_url, path)
        resp = self.api.get(url=url, headers=self.headers, params=params, fail_return_resp=fail_return_resp, **kwargs)
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

    def ws_send_request(self, data, get_ret=True, timeout=30, return_id=False):
        """发送web socket请求"""
        try:
            if not self.ws_client or not self.ws_client.is_running() or not self.ws_client.is_ready():
                aklog_warn('WS未初始化连接，或者已断开连接，重新WS连接')
                if not self.ws_connect():
                    return False

            # 发送的请求，ID必须是递增的
            self.ws_id += 1
            if isinstance(data, dict):
                data['id'] = self.ws_id
            aklog_debug('send data: %s' % data)
            ret = self.ws_client.send_message(json.dumps(data))
            if not ret:
                aklog_error('WS未连接')
                return False
            # 获取结果
            if get_ret:
                msg = self.get_ws_resp_msg(data['id'], timeout)
                if msg:
                    return msg[0]
                else:
                    aklog_error('发送WS请求，获取结果失败')
                    return None
            elif return_id:
                return self.ws_id
            else:
                return True
        except:
            aklog_error('发送WS请求异常，请检查')
            aklog_debug(traceback.format_exc())
            return False

    def get_ws_resp_msg(self, ws_id=None, timeout=10) -> list:
        """获取ws接口请求接收到的消息"""
        end_time = time.time() + timeout
        while time.time() <= end_time:
            msgs = self.ws_client.get_msg(ws_id)
            if msgs:
                return msgs
            time.sleep(0.1)
            continue
        return []

    def clear_ws_msg(self, ws_id):
        self.ws_client.clear_msg(ws_id=ws_id)

    def ws_pcap_send_request(self, data, clear=False):
        """
        发送WS PCAP请求
        data: str类型
        """
        try:
            if not self.ws_pcap_client or not self.ws_pcap_client.is_running():
                aklog_warn('WS PCAP未初始化连接，或者已断开连接，重新WS PCAP连接')
                if not self.ws_pcap_connect():
                    return False

            # 发送请求前，先清空原来的数据
            if clear:
                self.ws_pcap_client.clear_msg()
            aklog_debug('send data: %s' % data)
            ret = self.ws_pcap_client.send_message(data)
            if not ret:
                aklog_error('WS PCAP发送请求失败')
                return False
            return True
        except:
            aklog_error('发送WS PCAP请求异常，请检查')
            aklog_debug(traceback.format_exc())
            return False

    def get_ws_pcap_resp_msg(self):
        """获取ws抓包数据"""
        return self.ws_pcap_client.get_msg()

    # endregion

    # region 登录登出相关

    def is_accessible(self):
        """检查网页是否可以访问"""
        path = 'invoke/config'
        data = {
            "item": [
                "status.general.firmware",
                "status.general.model"
            ]
        }
        resp = self.api_post(path, data, print_trace=False)
        if not resp:
            aklog_warn(f'{self.device_ip} is not accessible')
            return False
        aklog_info(f'{self.device_ip} is accessible')
        return True

    def wait_accessible(self, timeout=180):
        """等待网页可以访问"""
        aklog_info()
        path = 'invoke/config'
        data = {
            "item": [
                "status.general.firmware",
                "status.general.model"
            ]
        }
        end_time = time.time() + timeout
        while time.time() <= end_time:
            resp = self.api_post(path, data, print_trace=False)
            if resp:
                aklog_info(f'{self.device_ip} is accessible')
                return True
            time.sleep(5)
        aklog_warn(f'{self.device_ip} is not accessible')
        return False

    def interface_init(self, login_type=None, retry=3, print_trace=True, raise_enable=True, re_login=False,
                       fail_return_resp=False):
        """
        Requests和WS接口初始化
        login_type: local、global_manage、global_user、area_manage、area_user，或者直接传入url
        V2.1只能通过user地址访问
        """
        aklog_info()
        if login_type:
            self.login_type = login_type

        if self.login_type == 'local':
            self.base_url = self.original_url
        elif self.login_type == 'global_manage':
            self.original_remote_url = param_get_config_ini_data()['akubela_cloud_info']['cloud_global_user_addr']
        elif self.login_type == 'global_user':
            self.original_remote_url = param_get_config_ini_data()['akubela_cloud_info']['cloud_global_user_addr']
        elif self.login_type == 'area_manage':
            self.original_remote_url = param_get_config_ini_data()['akubela_cloud_info']['cloud_user_addr']
        elif self.login_type == 'area_user':
            self.original_remote_url = param_get_config_ini_data()['akubela_cloud_info']['cloud_user_addr']
        else:
            # 直接传入远程URL
            self.original_remote_url = self.login_type
            self.login_type = 'remote'

        if (not re_login and not login_type
                and self.ws_client and self.ws_client.is_running() and self.ws_client.is_ready()):
            aklog_info('已经登录')
            return True
        if self.username == self.local_username and self.login_type == 'local':
            login_ret = False
            for i in range(4):
                login_ret = self.__interface_login(
                    retry=1, print_trace=print_trace, raise_enable=raise_enable, fail_return_resp=fail_return_resp)
                if login_ret is True:
                    login_ret = self.ws_connect()
                
                if login_ret is not True:
                    #  登录失败，改用默认密码重新登录
                    if self.password != self.device_config.get_web_admin_passwd():
                        self.password = self.device_config.get_web_admin_passwd()
                    elif self.password != 'admin':
                        self.password = 'admin'
                    elif self.password != self.new_pwd:
                        self.password = self.new_pwd
                    continue
    
                user_info = self.get_project_user_info()
                if user_info and user_info.get('is_init_pwd') and not user_info.get('ignore'):
                    # 如果是初始化密码，并且不忽略，则修改密码
                    self.update_project_user_pwd(self.new_pwd)
                    continue
                break
        else:
            login_ret = self.__interface_login(
                retry=retry, print_trace=print_trace, raise_enable=raise_enable, fail_return_resp=fail_return_resp)
            if login_ret is True:
                login_ret = self.ws_connect()
        return login_ret

    def __interface_login(self, retry=1, print_trace=True, raise_enable=True, fail_return_resp=False):
        if self.login_type == 'local':
            self.base_url = self.original_url
            login_func = self.__interface_local_login
        else:
            self.base_url = self.original_remote_url
            login_func = self.__interface_remote_login

        is_raise = False
        login_ret = False
        for i in range(retry):
            if raise_enable and i == retry - 1:
                is_raise = True
            login_ret = login_func(print_trace=print_trace, raise_enable=is_raise, fail_return_resp=fail_return_resp)
            if login_ret is True:
                return True
            elif i < retry - 1:
                aklog_debug('尝试重新登录')
                time.sleep(5)
                continue
        if fail_return_resp:
            return login_ret
        else:
            return False
    
    def interface_logout(self):
        if self.login_type == 'local':
            self.__interface_local_logout()
        else:
            self.__interface_remote_logout()

    def logout(self):
        return self.interface_logout()

    def put_user_password(self, username, password):
        if username:
            self.username = username
        if password:
            self.password = password

    def put_login_type(self, login_type):
        self.login_type = login_type

    def reset_user_to_local(self):
        """恢复登录用户名为本地账户"""
        self.username = self.local_username
        self.password = self.local_password
        self.login_type = 'local'
        self.interface_init(re_login=True)

    def update_project_user_pwd(self, new_pwd, username='admin', cur_pwd='admin'):
        """
        修改web密码
        Args:
            cur_pwd (str):
            username (str):
            new_pwd (str):
        """
        aklog_info()
        data = {
            "type": "ak_account/project_user/update_pwd",
            "username": username,
            "cur_pwd": cur_pwd,
            "new_pwd": new_pwd
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success') and resp.get('result') == 'success':
            self.password = new_pwd
            if username == self.local_username:
                self.local_password = new_pwd
            return True
        else:
            aklog_error('update_project_user_pwd Fail')
            return False
    
    def get_project_user_info(self, username='admin'):
        """
        获取项目用户信息
        Args:
            username ():

        Returns:
        {
            "is_init_pwd": true,
            "ignore": false
        }
        """
        data = {
            "type": "ak_account/project_user/get",
            "username": username
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            ret = resp['result']
            aklog_debug(ret)
            return ret
        else:
            aklog_warn('get_project_user_info Fail')
            return None
    
    # 局域网方式登录用户web
    def __interface_local_login(self, print_trace=True, raise_enable=True, fail_return_resp=False):
        """接口方式登录"""
        aklog_info('__interface_local_login, user: %s, pwd: %s' % (self.username, self.password))
        try:
            path = 'invoke/auth-portal/method/login'
            login_data = {
                "account": self.username,
                "password": self.password
            }
            url = '%s/%s' % (self.base_url, path)
            login_data = json.dumps(login_data)
            headers = {'User-Platform': 'pc'}
            resp = self.api.post(url=url, headers=headers, data=login_data, fail_return_resp=True)
            ret = resp.json()
            if not ret or not ret['success']:
                aklog_error(f'接口方式登录失败: {ret}')
                if fail_return_resp:
                    return ret
                else:
                    return False
            resp_headers = resp.headers
            self.access_token = resp_headers.get('User-Token')
            self.refresh_token = resp_headers.get('Refresh-Token')
            self.headers['authorization'] = 'Bearer %s' % self.access_token
            self.headers['Refresh-Token'] = self.refresh_token
            self.account_id = ret['result']['account_id']
            aklog_info('接口方式登录成功')
            return True
        except Exception as e:
            aklog_error('接口方式登录异常，请检查: %s' % e)
            if print_trace:
                aklog_debug(traceback.format_exc())
            if raise_enable:
                raise e
            else:
                return False

    def __interface_local_logout(self):
        """接口方式登出"""
        aklog_info()
        self.ws_close()
        path = 'invoke/auth-portal/method/logout'
        resp = self.api_delete(path)
        if not resp:
            aklog_error('interface_local_logout Fail')
            return False
        else:
            aklog_info('interface_local_logout OK')
            return True

    def ws_connect(self):
        """WebSocket连接初始化"""
        aklog_info()
        self.ws_base_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
        self.ws_client.put_address('%s/api/websocket' % self.ws_base_url)
        for i in range(4):
            try:
                if not self.ws_client.run():
                    if i < 3:
                        aklog_error('WS连接失败，HTTP Requests重新登录尝试')
                        if not self.__interface_login(retry=1):
                            return False
                        time.sleep(1)
                        continue
                    else:
                        aklog_error('WS连接失败')
                        return False
                time.sleep(1)
                if not self.access_token:
                    if not self.__interface_login(retry=1):
                        return False
                login_data = {
                    "type": "auth",
                    "access_token": self.access_token
                }
                aklog_debug('ws send message: %s' % login_data)
                ret = self.ws_client.send_message(json.dumps(login_data))
                if not ret or not self.ws_client.is_running():
                    aklog_error('WS连接失败，HTTP Requests重新登录尝试')
                    if not self.__interface_login(retry=1):
                        return False
                    time.sleep(1)
                    continue
                if self.ws_client.wait_ready():
                    # 获取ha的版本号
                    msgs = self.get_ws_resp_msg()
                    if msgs:
                        for msg in msgs:
                            if 'ha_version' in msg:
                                ha_version = msg.get('ha_version')
                                aklog_debug(f'ha_version: {ha_version}')
                                versions = ha_version.split('.')
                                ha_version = versions[0] + '.' + '%03d' % int(versions[1]) + '%03d' % int(versions[2])
                                self.ha_version = float(ha_version)
                                break
                    aklog_info('WS连接成功')
                    return True
                else:
                    aklog_error('WS连接鉴权失败')
                    return False
            except Exception as e:
                if i < 3:
                    aklog_error(f'WS连接异常: {e}，HTTP Requests重新登录尝试')
                    if not self.__interface_login(retry=1):
                        return False
                    time.sleep(1)
                    continue
                else:
                    aklog_error('WS连接异常')
                    aklog_debug(traceback.format_exc())
                    return False
        aklog_error('WS连接失败')
        return False

    def ws_close(self):
        aklog_info()
        self.ws_client.close()

    def ws_pcap_connect(self):
        aklog_info()
        if self.ws_pcap_client.run():
            return True
        for old_url in self.ws_pcap_old_url_list:
            self.ws_pcap_client.put_address(old_url)
            if self.ws_pcap_client.run():
                return True
            continue
        return False

    def ws_pcap_close(self):
        aklog_info()
        self.ws_pcap_client.close()

    @staticmethod
    def dict_iter(d):
        for i in d.items():
            yield str(i).encode()

    @staticmethod
    def generate_rsa_encrypt(message, public_key):
        # 加密
        rsa_public_key = RSA.import_key(public_key)
        cipher = PKCS1_v1_5.new(rsa_public_key)
        cipher_text = cipher.encrypt(message.encode('utf-8'))

        # 使用 Base64 编码密文
        cipher_text_base64 = base64.b64encode(cipher_text).decode('utf-8')
        return cipher_text_base64

    # 远程穿透方式登录用户web
    def __interface_remote_login(self, print_trace=True, raise_enable=True, fail_return_resp=False):
        """全球管理地址入口远程登录用户web"""
        aklog_info('__interface_remote_login, user: %s, pwd: %s' % (self.username, self.password))
        try:
            password_base64 = self.generate_rsa_encrypt(self.password, CLOUD_PUBLIC_KEY)
            # 远程方式登录，先获取登录地址和ha_token
            login_data = {
                "account": self.username,
                'encrypt_algorithm': "RSA",
                "password": password_base64,
                "password_encrypt_enabled": True
            }
            if (self.login_type == 'global_manage' or self.login_type == 'global_user'
                    or (self.login_type == 'remote' and 'cloud' not in self.original_remote_url)):
                path = 'api/global-user-entry/v1.0/invoke/global-user-entry/method/global-auth/user/login'
            else:
                path = 'api/user-entry/v1.0/invoke/user-entry/method/account/user/login'
            
            headers = {'User-Platform': 'pc'}
            ret1 = None
            for i in range(2):
                url = '%s/%s' % (self.base_url, path)
                login_data = json.dumps(login_data)
                resp_1 = self.api.post(url=url, headers=headers, data=login_data, fail_return_resp=True)
                ret1 = resp_1.json()
                if not ret1 and self.login_type == 'remote':
                    if path == 'api/global-user-entry/v1.0/invoke/global-user-entry/method/global-auth/user/login':
                        path = 'api/user-entry/v1.0/invoke/user-entry/method/account/user/login'
                    else:
                        path = 'api/global-user-entry/v1.0/invoke/global-user-entry/method/global-auth/user/login'
                    continue
                else:
                    break
            if not ret1 or not isinstance(ret1, dict):
                aklog_error(f'远程接口方式登录失败: {ret1}')
                return False

            # 通过获取到的链接地址登录设备用户web
            self.ha_token = ret1['result']['token']
            remote_host = ret1['result']['remote_url']
            self.base_url = 'https://%s' % remote_host
            remote_url = 'https://%s/invoke/auth-portal/method/login' % remote_host
            data = json.dumps({"ha_token": self.ha_token})

            resp_2 = self.api.post(url=remote_url, headers=headers, data=data, fail_return_resp=True)
            resp_headers = resp_2.headers
            self.access_token = resp_headers.get('User-Token')
            self.refresh_token = resp_headers.get('Refresh-Token')
            self.headers['authorization'] = 'Bearer %s' % self.access_token
            self.headers['Refresh-Token'] = self.refresh_token
            ret2 = resp_2.json()
            if ret2 and ret2['success'] is True:
                self.account_id = ret2['result']['account_id']
                aklog_info('远程接口方式登录成功')
                return True
            else:
                aklog_error('远程接口方式登录失败')
                aklog_debug(ret)
                if fail_return_resp:
                    return ret2
                else:
                    return False
        except Exception as e:
            aklog_error('远程接口方式登录异常，请检查: %s' % e)
            if print_trace:
                aklog_debug(traceback.format_exc())
            if raise_enable:
                raise e
            else:
                return False

    def __interface_remote_logout(self):
        """接口方式登出"""
        aklog_info()
        self.ws_close()
        try:
            path = 'invoke/auth-portal/method/logout'
            resp = self.api_delete(path, fail_return_resp=True)
            if resp.status_code == 302 or 200 <= resp.status_code < 300:
                aklog_info('interface_remote_logout OK')
                return True
            else:
                aklog_error('interface_remote_logout Fail')
                return False
        except:
            aklog_error('interface_remote_logout Fail')
            aklog_debug(traceback.format_exc())
            return False

    @staticmethod
    def browser_close_and_quit():
        return True

    # endregion


if __name__ == '__main__':
    user_web_inf = AkubelaWebInfBaseV3()
    device_info = {
        'device_name': 'hc_android_hypanel',
        'ip': '192.168.88.103'
    }
    device_config = config_parse_device_config('config_PS51_NORMAL')
    user_web_inf.init(device_info, device_config)
    remote_url = 'https://my.uat.akubela.com'
    user_web_inf.interface_init()
    time.sleep(2)
    user_web_inf.interface_logout()
    # time.sleep(2)
    # user_web_inf.get_family_users_info()
