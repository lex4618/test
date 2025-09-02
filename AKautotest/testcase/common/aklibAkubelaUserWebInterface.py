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
import random
import time
import traceback
import requests
import json
from requests_toolbelt import MultipartEncoder


class AkubelaUserWebInterface:

    # <editor-fold desc="初始化">

    def __init__(self):
        self.username = ''
        self.password = ''
        self.original_url = ''
        self.ws_original_url = ''
        self.original_remote_url = ''
        self.base_url = ''
        self.ws_base_url = ''
        self.login_type = 'local'
        self.access_token = ''
        self.token_type = ''
        self.refresh_token = ''
        self.ha_token = ''
        self.header = {}
        self.ws_client = None
        self.ws_id = 1
        self.devices_info = {}
        self.contacts_info = {}
        self.scenes_info = {}
        self.scenes_list = []
        self.security_info = {}
        self.devices_list_info = {}
        self.family_id = None

    def init(self, device_ip, username=None, password=None):
        """
        初始化用户web接口信息
        """
        aklog_info()
        if username and password:
            self.username = username
            self.password = password
        self.original_url = 'http://%s' % device_ip
        self.ws_original_url = 'ws://%s' % device_ip

    def clear_family_info(self):
        """清空家庭信息"""
        self.devices_info.clear()
        self.contacts_info.clear()
        self.scenes_info.clear()
        self.scenes_list.clear()
        self.security_info.clear()
        self.devices_list_info.clear()
        self.family_id = None

    # </editor-fold>

    # <editor-fold desc="Requests、WebSocket接口通用操作">

    def http_send_post(self, url, data, content_type=None):
        """HTTP Requests，post方式发送请求"""
        aklog_debug()
        data_json = json.dumps(data)
        if content_type is None:
            self.header['Content-Type'] = 'application/json'
        elif content_type == '' and 'Content-Type' in self.header:
            del self.header['Content-Type']
        else:
            self.header['Content-Type'] = content_type
        for i in range(2):
            resp = requests.post(url=url, headers=self.header, data=data_json, timeout=30)
            if resp.status_code == 200:
                resp_data = resp.json()
                aklog_debug('resp_data: %r' % resp_data)
                return resp_data
                # resp_text = resp.text
                # if resp_text and resp_text.strip():
                #     resp_data = json_loads_2_dict(resp_text)
                #     aklog_info('resp_data: %r' % resp_data)
                #     return resp_data
                # else:
                #     return ''
            elif i == 0 and resp.status_code == 401:
                aklog_error('http post请求鉴权失败，重新登录')
                self.__interface_login()
                continue
            else:
                aklog_error('send_post failed, status_code: %s' % resp.status_code)
                return None

    def http_send_get(self, url):
        """HTTP Requests，get方式发送请求"""
        aklog_debug()
        self.header['Content-Type'] = 'application/json'
        for i in range(2):
            resp = requests.get(url=url, headers=self.header, timeout=30)
            if resp.status_code == 200:
                resp_data = resp.json()
                aklog_debug('resp_data: %r' % resp_data)
                return resp_data
                # resp_text = resp.text
                # if resp_text and resp_text.strip():
                #     resp_data = json_loads_2_dict(resp_text)
                #     aklog_info('resp_data: %r' % resp_data)
                #     return resp_data
                # else:
                #     return ''
            elif i == 0 and resp.status_code == 401:
                aklog_error('http get请求鉴权失败，重新登录')
                self.__interface_login()
                continue
            else:
                aklog_error('send_get failed, status_code: %s' % resp.status_code)
                return None

    def http_send_delete(self, url):
        """HTTP Requests，delete方式发送删除请求"""
        aklog_debug()
        self.header['Content-Type'] = 'application/json'
        for i in range(2):
            resp = requests.delete(url=url, headers=self.header, timeout=30)
            if resp.status_code == 200:
                resp_data = resp.json()
                aklog_debug('resp_data: %r' % resp_data)
                return resp_data
                # resp_text = resp.text
                # if resp_text and resp_text.strip():
                #     resp_data = json_loads_2_dict(resp_text)
                #     aklog_info('resp_data: %r' % resp_data)
                #     return resp_data
                # else:
                #     return ''
            elif i == 0 and resp.status_code == 401:
                aklog_error('http delete请求鉴权失败，重新登录')
                self.__interface_login()
                continue
            else:
                aklog_error('send_delete failed, status_code: %s' % resp.status_code)
                return None

    def http_send_post_multipart(self, url, data, retry=2):
        """发送multipart/form-data类型的post请求"""
        aklog_debug()
        m = MultipartEncoder(fields=data)
        self.header['Content-Type'] = m.content_type
        for i in range(retry):
            resp = requests.post(url=url, headers=self.header, data=m, timeout=30)
            if resp.status_code == 200:
                resp_data = resp.json()
                aklog_debug('resp_data: %r' % resp_data)
                return resp_data
                # resp_text = resp.text
                # # aklog_info('resp_text: %s' % resp_text)
                # if resp_text and resp_text.strip():
                #     resp_data = json_loads_2_dict(resp_text)
                #     aklog_info('resp_data: %r' % resp_data)
                #     return resp_data
                # else:
                #     return ''
            elif i == 0 and retry >= 2 and resp.status_code == 401:
                aklog_error('http post请求鉴权失败，重新登录')
                self.__interface_login()
                continue
            else:
                aklog_error('send_post_multipart failed, status_code: %s' % resp.status_code)
                return None

    def ws_send_request(self, data, get_ret=True):
        """发送web socket请求"""
        for i in range(3):
            try:
                # 发送请求前，先清空原来的数据
                self.ws_client.clear_msg()
                # 指令ID必须要递增
                data['id'] = self.ws_id
                aklog_debug('send data: %s' % data)
                # 发送的请求，ID必须是递增的
                self.ws_id += 1
                ret = self.ws_client.send_message(json.dumps(data))
                if not ret:
                    aklog_error('WS未连接')
                    return False
                # 获取结果
                if get_ret:
                    time.sleep(1)
                    msg = self.get_ws_resp_msg(data['id'])
                    if msg:
                        return msg[0]
                    if i < 2:
                        aklog_error('发送WS请求失败，重新连接尝试')
                        time.sleep(2)
                        self.ws_connect()
                        continue
                    else:
                        aklog_error('发送WS请求，获取结果失败')
                        return None
                else:
                    return True
            except:
                if i < 2:
                    aklog_error('发送WS请求异常，重新连接尝试')
                    aklog_debug(traceback.format_exc())
                    time.sleep(2)
                    self.ws_connect()
                    continue
                else:
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

    # </editor-fold>

    # <editor-fold desc="登录登出相关">

    def interface_init(self, login_type=None, retry=3, print_trace=True):
        """
        Requests和WS接口初始化
        login_type: local、global_manage、global_user、area_manage、area_user，或者直接传入url
        V2.1只能通过user地址访问
        """
        aklog_info()
        self.clear_family_info()
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
        if self.ws_client and self.devices_info and self.get_devices_trigger_info(regain=True):
            aklog_info('已经登录')
            return True
        login_ret = self.__interface_login(retry=retry, print_trace=print_trace)
        if login_ret:
            self.ws_base_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            self.ws_client = AkWSClient('%s/api/websocket' % self.ws_base_url)
            self.ws_connect()
            self.get_devices_trigger_info()
            self.get_contacts_info()
        return login_ret

    def __interface_login(self, retry=3, print_trace=True):
        for i in range(retry):
            if self.login_type == 'local':
                self.base_url = self.original_url
                login_func = self.__interface_local_login
            else:
                self.base_url = self.original_remote_url
                login_func = self.__interface_remote_login

            if login_func(print_trace=print_trace):
                return True
            elif i < retry - 1:
                aklog_error('登录失败，重新登录')
                time.sleep(5)
                continue
            else:
                aklog_fatal('登录失败')
                return False

    def interface_logout(self):
        if self.login_type == 'local':
            self.__interface_local_logout()
        else:
            self.__interface_remote_logout()
        self.ws_client = None
        self.devices_info = {}

    def put_user_password(self, username, password):
        self.username = username
        self.password = password

    def put_login_type(self, login_type):
        self.login_type = login_type

    # 局域网方式登录用户web
    def __interface_local_login(self, print_trace=True):
        """接口方式登录"""
        aklog_info('__interface_local_login, user: %s, pwd: %s' % (self.username, self.password))
        try:
            url_1 = "%s/auth/login_flow" % self.base_url
            payload_1 = json.dumps({
                "client_id": self.base_url,
                "handler": ["homeassistant", None],
                "redirect_uri": "%s/profile?auth_callback=1" % self.base_url
            })
            aklog_debug('requests.post: %s, data: %s' % (url_1, payload_1))
            resp_1 = requests.post(url=url_1, data=payload_1, timeout=30)
            flow_id = resp_1.json()['flow_id']

            url_2 = "%s/auth/login_flow/%s" % (self.base_url, str(flow_id))
            payload_2 = json.dumps({
                "username": self.username,
                "password": self.password,
                "client_id": self.base_url})
            aklog_debug('requests.post: %s, data: %s' % (url_2, payload_2))
            resp_2 = requests.post(url=url_2, data=payload_2, timeout=30)
            code_result = resp_2.json()['result']

            # 用flow_id获取result，下面要用这个获取token
            url_3 = "%s/auth/token" % self.base_url
            payload_3 = {
                "client_id": self.base_url,
                "code": code_result,
                "grant_type": "authorization_code"
            }
            aklog_debug('requests.post: %s, data: %s' % (url_3, payload_3))
            resp_3 = requests.post(url=url_3, data=payload_3, timeout=30)
            result_3 = resp_3.json()
            self.access_token = result_3['access_token']
            self.token_type = result_3['token_type']  # Bearer
            self.refresh_token = result_3['refresh_token']
            self.header['authorization'] = '%s %s' % (self.token_type, self.access_token)
            aklog_info('接口方式登录成功')
            return True
        except:
            aklog_error('接口方式登录失败，请检查')
            if print_trace:
                aklog_debug(traceback.format_exc())
            return False

    def __interface_local_logout(self):
        """接口方式登出"""
        aklog_info()
        self.ws_close()
        revoke_token_data = {'action': 'revoke',
                             'token': self.refresh_token}
        m = MultipartEncoder(fields=revoke_token_data)
        header = {'Content-Type': m.content_type}
        url = '%s/auth/token' % self.base_url
        aklog_debug('requests.post: %s, data: %r' % (url, revoke_token_data))
        resp = requests.post(url=url, headers=header, data=m, timeout=30)
        aklog_debug('status_code: %s, result: %s' % (resp.status_code, resp.text))
        time.sleep(1)
        if resp.status_code == 200:
            aklog_info('登出成功')
            return True
        else:
            aklog_error('登出失败')
            return False

        # invoke_config_data = {"item": ["Settings.CONNECTIONTYPE.Mode"]}
        # self.http_send_post('%s/invoke/config' % self.base_url, invoke_config_data)
        #
        # login_flow_data = {"client_id": self.base_url,
        #                    "handler": ["homeassistant", None],
        #                    "redirect_uri": "%s/?auth_callback=1" % self.base_url}
        # self.http_send_post('%s/auth/login_flow' % self.base_url, login_flow_data,
        #                     content_type='text/plain;charset=UTF-8')

    def ws_connect(self):
        """WebSocket连接初始化"""
        aklog_info()
        for i in range(4):
            try:
                if not self.ws_client.run():
                    if i < 3:
                        aklog_error('WS连接失败，HTTP Requests重新登录尝试')
                        self.__interface_login()
                        time.sleep(2)
                        continue
                    else:
                        aklog_error('WS连接失败')
                        return False
                time.sleep(2)
                login_data = {
                    "type": "auth",
                    "access_token": self.access_token
                }
                aklog_debug('ws send message: %s' % login_data)
                ret = self.ws_client.send_message(json.dumps(login_data))
                if not ret and not self.ws_client.is_running():
                    aklog_error('WS连接失败，HTTP Requests重新登录尝试')
                    self.__interface_login()
                    time.sleep(2)
                    continue
                time.sleep(1)
                self.ws_client.clear_msg()
                aklog_info('WS连接成功')
                return True
            except:
                if i < 3:
                    aklog_error('WS连接异常，HTTP Requests重新登录尝试')
                    self.__interface_login()
                    time.sleep(2)
                    continue
                else:
                    aklog_error('WS连接异常')
                    aklog_debug(traceback.format_exc())
                    return False

    def ws_close(self):
        aklog_info()
        self.ws_client.close()

    # 远程穿透方式登录用户web
    def __interface_remote_login(self, print_trace=True):
        """全球管理地址入口远程登录用户web"""
        aklog_info('__interface_remote_login, user: %s, pwd: %s' % (self.username, self.password))
        try:
            header1 = {'User-Platform': 'pc', 'Content-Type': 'application/json'}
            payload_1 = json.dumps({"account": self.username,
                                    "password": self.password,
                                    "area": ""})
            resp_1 = None
            for i in range(2):
                if self.login_type == 'global_manage' or self.login_type == 'global_user' \
                        or (self.login_type == 'remote' and i == 0):
                    url_1 = "%s/api/global-auth/v1.0/invoke/global-auth/method/login" % self.base_url
                else:
                    url_1 = '%s/api/auth-portal/v1.0/invoke/auth-portal/method/login' % self.base_url
                aklog_debug('requests.post: %s, data: %s' % (url_1, payload_1))
                resp_1 = requests.post(url=url_1, data=payload_1, headers=header1, timeout=30)
                if resp_1.status_code == 200:
                    break
            result_1 = resp_1.json()['result']
            # print(resp_1.json())
            account_id = result_1['account_id']
            domain = result_1.get('domain')
            user_id = result_1['user_id']
            path = result_1['path']
            user_token = resp_1.headers['User-Token']

            if domain:
                self.base_url = 'https://%s' % domain
            url_2 = '%s/api/user-portal/v1.0/invoke/user-portal/method/device/account-resident-devices' \
                    '?account_id=%s&device_type=ak_homecenter' % (self.base_url, account_id)

            header2 = {'user-id': user_id,
                       'user-platform': 'pc',
                       'User-Token': user_token,
                       'referer': '%s%s' % (self.base_url, path)}
            time.sleep(1)
            aklog_debug('requests.get: %s, header: %s' % (url_2, header2))
            r_2 = requests.get(url=url_2, headers=header2, timeout=30)
            # print(r_2.json())
            device_id = r_2.json()['result'][0]['device_id']

            url_3 = "%s/api/user-portal/v1.0/invoke/user-portal/method/open-remote" % self.base_url
            payload_3 = json.dumps({"account_id": account_id,
                                    "device_id": device_id,
                                    "timezone": "UTC+8"})
            header2['content-type'] = 'application/json'
            time.sleep(1)
            aklog_debug('requests.post: %s, data: %s' % (url_3, payload_3))
            resp_3 = requests.post(url=url_3, data=payload_3, headers=header2, timeout=30)
            # print(resp_3.json())
            result_3 = resp_3.json()['result']
            self.ha_token = result_3['token']
            ha_domain = result_3['domain']
            self.base_url = 'https://%s' % ha_domain

            time.sleep(1)
            invoke_config_data = json.dumps({"item": ["Settings.CONNECTIONTYPE.Mode"]})
            requests.post(url='%s/invoke/config' % self.base_url, data=invoke_config_data, timeout=30)

            login_flow_data = json.dumps({"client_id": self.base_url,
                                          "handler": ["homeassistant", None],
                                          "redirect_uri": "%s/?ha_token=%s&auth_callback=1"
                                                          % (self.base_url, self.ha_token)})
            url_4 = '%s/auth/login_flow' % self.base_url
            time.sleep(1)
            aklog_debug('requests.post: %s, data: %s' % (url_4, login_flow_data))
            resp_4 = requests.post(url=url_4, data=login_flow_data, timeout=30)
            # print(resp_4.json())
            result_4 = resp_4.json()
            # flow_id = result_4['flow_id']
            code_result = result_4['result']

            # 用code_result获取token
            url_5 = "%s/auth/token" % self.base_url
            payload_5 = {
                "client_id": self.base_url,
                "code": code_result,
                "grant_type": "authorization_code"
            }
            m = MultipartEncoder(fields=payload_5)
            header5 = {'Content-Type': m.content_type}
            time.sleep(1)
            aklog_debug('requests.post: %s, data: %s' % (url_5, payload_5))
            resp_5 = requests.post(url=url_5, headers=header5, data=m, timeout=30)
            # print(resp_5.json())
            result_5 = resp_5.json()
            self.access_token = result_5['access_token']
            self.token_type = result_5['token_type']  # Bearer
            self.refresh_token = result_5['refresh_token']
            self.header['authorization'] = '%s %s' % (self.token_type, self.access_token)
            aklog_info('远程接口方式登录成功')
            return True
        except:
            aklog_error('远程接口方式登录失败，请检查')
            if print_trace:
                aklog_debug(traceback.format_exc())
            return False

    def __interface_remote_logout(self):
        """接口方式登出"""
        aklog_info()
        self.ws_close()
        revoke_token_data = {'action': 'revoke',
                             'token': self.refresh_token}
        m = MultipartEncoder(fields=revoke_token_data)
        header = {'Content-Type': m.content_type}
        url = '%s/auth/token' % self.base_url
        aklog_debug('requests.post: %s, data: %r' % (url, revoke_token_data))
        resp = requests.post(url=url, headers=header, data=m, timeout=30)
        aklog_debug('status_code: %s, result: %s' % (resp.status_code, resp.text))
        time.sleep(1)
        # if resp.status_code == 302:
        #     aklog_info('登出成功')
        #     return True
        # else:
        #     aklog_error('登出失败')
        #     return False

    # </editor-fold>

    # <editor-fold desc="帐号管理">

    def change_user_pwd(self, new_pwd, old_pwd=None):
        """修改用户密码"""
        aklog_info()
        if not old_pwd:
            old_pwd = self.password
        if new_pwd == old_pwd:
            aklog_info('密码相同，不用修改')
            return True
        change_pwd_data = {"type": "config/auth_provider/homeassistant/change_password",
                           "current_password": old_pwd,
                           "new_password": new_pwd,
                           "id": self.ws_id}
        resp = self.ws_send_request(change_pwd_data)
        if resp and resp.get('success'):
            aklog_info('change_user_pwd OK')
            self.password = new_pwd
            return True
        else:
            aklog_error('change_user_pwd Fail')
            aklog_debug('resp: %s' % resp)
            return False

    def unbind_fm_account(self, fm_email):
        """解绑家庭成员帐号"""
        aklog_info()
        if not self.family_id:
            self._get_family_id()
        fm_user_id = self.get_family_users_info(fm_email)['user_id']
        if not fm_user_id:
            return False
        data = {"type": "ak_account/families/unbind",
                "user_id": fm_user_id,
                "family_id": self.family_id,
                "unbind": True,
                "id": self.ws_id}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('unbind_fm_account OK')
            return True
        else:
            aklog_error('unbind_fm_account Fail')
            aklog_debug('resp: %s' % resp)
            return False

    def unbind_all_fm_account(self):
        """解绑所有家庭帐号"""
        aklog_info()
        cur_user_id = self.get_current_user_info()['id']
        if not self.family_id:
            self._get_family_id()
        family_users = self.get_family_users_info()
        for fm_user in family_users:
            fm_user_id = fm_user['user_id']
            if fm_user == cur_user_id:
                continue
            data = {"type": "ak_account/families/unbind",
                    "user_id": fm_user_id,
                    "family_id": self.family_id,
                    "unbind": True,
                    "id": self.ws_id}
            resp = self.ws_send_request(data)
            if resp and resp.get('success'):
                aklog_info('unbind_fm_account %s OK' % fm_user['email'])
                continue
            else:
                aklog_error('unbind_fm_account %s Fail' % fm_user['email'])
                aklog_debug('resp: %s' % resp)
                return False
        aklog_info('unbind_all_fm_account OK')
        return True

    def del_account_and_transfer(self, transfer_user_email=None):
        """
        删除主帐号，然后将管理员转移给其他成员，如果存在多个家庭成员，需要指定转移的成员邮箱
        """
        aklog_info()
        family_users = self.get_family_users_info()
        user_id = transfer_user_id = None
        for fm_user in family_users:
            if fm_user['email'] == self.username:
                user_id = fm_user['user_id']
                continue
            if not transfer_user_email or fm_user['email'] == transfer_user_email:
                transfer_user_id = fm_user['user_id']

        data = {"type": "ak_account/users/delete",
                "user_id": user_id,
                "family_id": self.family_id,
                "unbind": True,
                "id": self.ws_id}
        if transfer_user_id:
            data['transfer_user_id'] = transfer_user_id
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('del_account_and_transfer OK')
            return True
        else:
            aklog_error('del_account_and_transfer Fail')
            aklog_debug('resp: %s' % resp)
            return False

    def get_family_users_info(self, user_email=None):
        """
        获取家庭用户信息，包含主帐号和从帐号
        user_email: 默认为空表示获取所有用户，可以获取指定用户信息
        return: family_members
        {
            "family_id": "r908377cb2d9070d63dc07530abad9d0b",
            "family_member_num": 2,
            "family_members": [
                {
                    "user_id": "a3eef3c11f2cf0403759e34a5c1ccdf39",
                    "username": "hzs01_cbuat_user1@aktest.top",
                    "first_name": "cbuat_user1",
                    "last_name": "hzs01",
                    "email": "hzs01_cbuat_user1@aktest.top",
                    "mobile": "13255768777765",
                    "land_line": null,
                    "region": "",
                    "address": "",
                    "authority": 2,
                    "intercom": true,
                    "image": null
                },
                {
                    "user_id": "a47af5ad5ca0335541fbe04b65752cc44",
                    "username": "cbuat_fm103hzs01",
                    "first_name": "cbuat_fm103",
                    "last_name": "hzs01",
                    "email": "hzs01_cbuat_fm103@aktest.top",
                    "mobile": "1242346566776",
                    "land_line": "352434543",
                    "region": "中国(+86)",
                    "address": "",
                    "authority": 0,
                    "intercom": false,
                    "image": null
                }
            ]
        }
        """
        aklog_info()
        if not self.family_id:
            self._get_family_id()
        data = {"type": "ak_account/users/family_id",
                "family_id": self.family_id,
                "id": self.ws_id}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('get_family_users_info OK, counts: %s' % resp.get('result')['family_member_num'])
            family_members = resp.get('result')['family_members']
            if not user_email:
                return family_members
            else:
                for member in family_members:
                    if member['email'] == user_email:
                        return member
                aklog_error('%s not found' % user_email)
                aklog_debug(family_members)
                return None
        else:
            aklog_error('get_family_users_info Fail')
            aklog_debug('resp: %s' % resp)
            return None

    def get_current_user_info(self):
        """
        return:
        {
            "id": "a3eef3c11f2cf0403759e34a5c1ccdf39",
            "name": "hzs01_cbuat_user1@aktest.top",
            "is_owner": true,
            "is_admin": true,
            "credentials": [
                {
                    "auth_provider_type": "homeassistant",
                    "auth_provider_id": null
                }
            ],
            "mfa_modules": [
                {
                    "id": "totp",
                    "name": "Authenticator app",
                    "enabled": false
                }
            ]
        }
        """
        data = {"type": "auth/current_user",
                "id": self.ws_id}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('get_current_user_info OK')
            return resp.get('result')
        else:
            aklog_error('get_current_user_info Fail')
            aklog_debug('resp: %s' % resp)
            return None

    def _get_family_id(self):
        cur_user_id = self.get_current_user_info()['id']
        user_detail_info = self._get_user_detail_info(cur_user_id)
        self.family_id = user_detail_info['family_id']
        return self.family_id

    def _get_user_detail_info(self, user_id):
        """
        获取user信息
        return:
        {
            "user_id": "a3eef3c11f2cf0403759e34a5c1ccdf39",
            "username": "hzs01_cbuat_user1@aktest.top",
            "first_name": "cbuat_user1",
            "last_name": "hzs01",
            "email": "hzs01_cbuat_user1@aktest.top",
            "mobile": "13255768777765",
            "land_line": null,
            "region": "",
            "address": "",
            "authority": 2,
            "intercom": true,
            "image": null,
            "family_id": "r908377cb2d9070d63dc07530abad9d0b"
        }
        """
        aklog_info()
        data = {"type": "ak_account/users/user_id",
                "user_id": user_id,
                "id": self.ws_id}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('get_user_detail_info OK')
            return resp.get('result')
        else:
            aklog_error('get_user_detail_info Fail')
            aklog_debug('resp: %s' % resp)
            return None

    def _get_family_info(self):
        """
        return:
        {
            "account": "hzs_user",
            "family_id": "r908377cb2d9070d63dc07530abad9d0b",
            "family_address": "中国 福建省 厦门市 gr",
            "family_devices": 6,
            "family_rooms": 5,
            "offline": false,
            "appmode": "homeautomation"
        }
        """
        if not self.family_id:
            self._get_family_id()
        data = {"type": "ak_account/families/family_id",
                "family_id": self.family_id,
                "id": self.ws_id}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('get_family_info OK')
            return resp.get('result')
        else:
            aklog_error('get_family_info Fail')
            aklog_debug('resp: %s' % resp)
            return None

    # </editor-fold>

    # <editor-fold desc="设置">

    def get_cloud_mode(self):
        """获取当前连云/脱云模式"""
        aklog_info()
        data = {"type": "ak_config/get",
                "item": ["Settings.CONNECTIONTYPE.Mode"],
                "id": self.ws_id}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            cloud_mode = resp['result']['Settings.CONNECTIONTYPE.Mode']
            aklog_info('cloud_mode: %s' % cloud_mode)
            return cloud_mode
        else:
            aklog_error('get_cloud_mode Fail')
            aklog_debug('resp: %s' % resp)
            return None

    def set_cloudless_mode(self, mode=True):
        """设置开启脱云模式"""
        aklog_info()
        data = {"type": "ak_config/update",
                "item": {"Settings.CONNECTIONTYPE.Mode": mode},
                "id": self.ws_id}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('set_cloudless_mode OK')
            return True
        else:
            aklog_error('set_cloudless_mode Fail')
            aklog_debug('resp: %s' % resp)
            return False

    # </editor-fold>

    # <editor-fold desc="获取设备和联系人信息">

    def get_devices_trigger_info(self, regain=False):
        """
        获取全部设备触发器所需实体接口
        {
        'Relay1': {'device_id': 'dff3b23ca0d4b9946702ab1ca881db27d', 'name': 'Relay1', 'model': 'Switch', 'trigger':
            {'switch': 'switch.e994fadad0323ac164cee1faf8ec38de0'}, 'location': 'Living Room'}
        }
        """
        aklog_info()
        if regain:
            self.devices_info = {}
        if not self.devices_info:
            resp = self.ws_send_request({"type": "ak_scenes/triggers", "id": self.ws_id})
            if resp is None or isinstance(resp, bool):
                return resp
            results = resp.get('result')
            for ret in results:
                device_name = ret['name']
                self.devices_info[device_name] = ret
            aklog_debug(self.devices_info)
        return self.devices_info

    def get_devices_list_info(self, regain=False):
        """
        获取家庭中全部设备信息的接口
        {
        'Smart Plug': {"area_id": "rf6b46ee218f92ac53b096db654bb4497","device_id": "2c9cf1664dc0b04ad2ec46b485323079",
        "product_attributes": "Add-on","product_type": "Smart Plug","name": "Smart Plug","location": "Master Bedroom",
        "favorite": false,"version": 67,"sort_id": 23,"bypass": false,"bypass_time": "","parent_device_id": "",
        "is_wire": false,"mac": "ec1bbdfffea7153d","source": 0,"detail": {
        "outlet": {"value": "on","entity_id": "switch.c02b946386931c962889a916bd68e9bc","timestamp": 1669171207
        },
        "online": false
          }
         }
        }

        {
            "area_id": "",
            "device_id": "484ad948cb534059e16008b6c949637e",
            "product_attributes": "Add-on",
            "product_type": "Emergency Sensor",
            "name": "Emergency Sensor",
            "location": "",
            "favorite": false,
            "version": 67,
            "sort_id": 6,
            "bypass": false,
            "bypass_time": "",
            "parent_device_id": "",
            "is_wire": false,
            "mac": "847127fffea62946",
            "source": 0,
            "relay_index": 0,
            "ownership": "hc_android_hypanel_pro",
            "child_ids": [],
            "detail": {
                "safety": {
                    "value": "off",
                    "entity_id": "binary_sensor.e86554f8da22452ff76d630ec14c26c8",
                    "entity_name": "Safety",
                    "timestamp": 1677053011
                },
                "battery": {
                    "value": "100",
                    "entity_id": "sensor.e86554f8da22452ff76d630ec14c26c8",
                    "entity_name": "Battery",
                    "timestamp": 1677053011
                },
                "online": true
            }
        }
        """
        aklog_info()
        if regain:
            self.devices_list_info = {}
        if not self.devices_list_info:
            resp = self.ws_send_request({"type": "config/ak_device/list", "id": self.ws_id})
            if resp is None or isinstance(resp, bool):
                return resp
            results = resp.get('result')
            for ret in results:
                device_name = ret['name']
                self.devices_list_info[device_name] = ret
            aklog_info(self.devices_list_info)
        return self.devices_list_info

    def get_contacts_info(self):
        """
        获取联系人信息，设备名称转成设备ID
        return:
        {'master_android_hyperpanel':
            {'id': 'dbd1461dcf243551e7ab72b0a3f394a1f', 'name': 'master_android_hyperpanel', 'group': 'hzs room',
            'sip': '5928100041', 'ip': '192.168.88.145', 'mac': None, 'uuid': '93e2ae08ffa6419a9e807ac00ce5c4c8',
            'type': 'PS51', 'status': 1, 'intercom': True, 'video': False, 'icon': None}
        }
        """
        aklog_info()
        resp = self.ws_send_request({"type": "homeassistant/contacts", "source": "web", "id": self.ws_id})
        results = resp['result']
        for ret in results:
            contact_name = ret['name']
            self.contacts_info[contact_name] = ret
        # aklog_info(self.contacts_info)
        return self.contacts_info

    # </editor-fold>

    # <editor-fold desc="场景相关">

    def add_scenes(self, scene_name, trigger_type, manual, conditions=None, tasks=None, scene_id=None):
        """
        添加场景
        trigger_type: or / and
        manual: True / False
        scene_id: 默认为None，使用时间戳来作为scene_id，可以指定scene_id，如果指定scene_id已存在，会修改对应scene_id场景

        conditions 条件：list类型，子元素为字典：
        [{"platform": "device", "device_name": "Relay1", "type": "turned_on", "trigger_option": "switch"},
        {"platform": "device", "device_name": "Emergency Sensor", "type": "unsafe",
        "domain": "binary_sensor", "trigger_option": "safety"},
        {"platform": "time", "at": "00:00", "weekday": ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]},
        {"platform": "state", "entity_id": "automation.home", "to": "on"}]

        tasks 执行任务：list类型，子元素为字典：
        [{"device_name": "Relay1", "type": "turn_on"},
        {"delay": { "hours": 0, "minutes": 0, "seconds": 2, "milliseconds": 0}},
        {"send_message": "3232"},
        {"make_call": ["PS51"]},
        {"service": "automation.turn_on", "target": {"entity_id": "automation.home"}},
        {"service": "automation.trigger","target": {"entity_id": "automation.scenes_2"}},
        {"send_http_url": "232323"}]
        """
        if not scene_id:
            aklog_info()
        scenes_add_data = {
            "trigger_type": "%s" % trigger_type,
            "alias": "%s" % scene_name,
            "description": "",
            "style": "scene",
            "image": random.randint(101, 120),
            "type": 0,
            "manual": manual,
            "trigger": [],
            "condition": [],
            "action": [],
            "favorite": False,
            "mode": "single"
        }

        if conditions is None:
            conditions = []
        if tasks is None:
            tasks = []
        for i in range(len(conditions)):
            if conditions[i]['platform'] == 'device':
                conditions[i] = self.generate_scenes_condition_device_info(conditions[i])
        scenes_add_data['trigger'] = conditions

        for j in range(len(tasks)):
            if tasks[j].get('device_name'):
                tasks[j] = self.generate_scenes_task_device_info(tasks[j])
            if tasks[j].get('make_call'):
                tasks[j] = {"make_call": ["d0b76b6d6193651c201e750379cb7e74c"]}
        scenes_add_data['action'] = tasks
        if not scene_id:
            scene_id = str(time.time()).replace('.', '')[0:13]  # 用时间戳来作为scene_id
        url = "%s/api/config/automation/config/%s" % (self.base_url, scene_id)
        return self.http_send_post(url, scenes_add_data)

    def generate_scenes_condition_device_info(self, device_info):
        """添加场景，条件选择设备，生成设备信息"""
        device_name = device_info['device_name']
        trigger_option = device_info.get('trigger_option')
        device_id = self.devices_info[device_name]['device_id']
        if trigger_option:
            entity_id = self.devices_info[device_name]["trigger"][trigger_option]
        else:
            entity_id = self.devices_info[device_name]["trigger"]['switch']
        if 'domain' in device_info:
            domain = "%s" % device_info['domain']
        else:
            domain = "switch"
        condition_device_info = {
            "platform": "device",
            "type": "%s" % device_info['type'],
            "device_id": device_id,
            "entity_id": entity_id,
            "domain": domain}
        return condition_device_info

    def generate_scenes_task_device_info(self, device_info):
        """添加场景，任务选择设备，生成设备信息"""
        device_id = self.devices_info[device_info['device_name']]['device_id']
        entity_id = self.devices_info[device_info['device_name']]["trigger"]["switch"]
        task_device_info = {
            "type": "%s" % device_info['type'],
            "device_id": device_id,
            "entity_id": entity_id,
            "domain": "switch"}
        return task_device_info

    def generate_scenes_task_call(self, make_call_list):
        """呼叫列表，设备名称转成设备ID"""
        make_call_info = []
        for make_call in make_call_list:
            if make_call in self.devices_info:
                device_id = self.devices_info[make_call]['device_id']
                make_call_info.append(device_id)
            else:
                make_call_info.append(make_call)
        return make_call_info

    def get_scenes_info(self):
        """
        获取当前所有场景信息
        return:
        {'111':
            {'type': 0, 'image_type': 103, 'is_auto': True, 'manual': False, 'favorite': False,
            'scene_id': '1666943802163', 'name': '111', 'trigger_type': 'or', 'entity_id': 'automation.111',
             'auto_enabled': True, 'online': True, 'id': '1666943802163', 'alias': '111',
             'trigger': [{'platform': 'device', 'type': 'turned_on', 'device_id': 'd6c37f4bcfdfabb80d2c9430da2ef7d0c',
             'entity_id': 'switch.e85a27d19a5d795ef3475358b746e831a', 'domain': 'switch'}],
             'condition': [],
             'action': [{'send_http_url': '111'}]}
         }
        """
        aklog_info()
        resp = self.ws_send_request({"type": "ak_scenes/info", "id": self.ws_id})
        self.scenes_list = resp['result']
        scenes_info = {}
        for scene in self.scenes_list:
            scene_name = scene['name']
            scene_id = scene['scene_id']
            scene2 = self.__get_scene_info_by_id(scene_id)
            scene.update(scene2)  # update也会更新self.scenes_list内容
            scenes_info[scene_name] = scene
        self.scenes_info = scenes_info
        return self.scenes_info

    def __get_scene_info_by_id(self, scene_id):
        url = '%s/api/config/automation/config/%s' % (self.base_url, scene_id)
        return self.http_send_get(url)

    def edit_scenes(self, by_scenes_name, new_scenes_name, trigger_type=None, manual=None, conditions=None, tasks=None):
        """
        编辑场景，通过scenes_name获取对应的scene_id
        by_scenes_name: 原先的场景名称
        new_scenes_name：修改后的场景名称
        trigger_type: or / and
        manual: True / False

        conditions 条件：list类型，子元素为字典：
        [{"platform": "device", "device_name": "Relay1", "type": "turned_on"},
        {"platform": "time", "at": "00:00", "weekday": [ "sun", "mon", "tue", "wed", "thu", "fri", "sat"]},
        {"platform": "state", "entity_id": "automation.home", "to": "on"}]

        tasks 执行任务：list类型，子元素为字典：
        [{"device_name": "Relay1", "type": "turn_on",},
        {"delay": { "hours": 0, "minutes": 0, "seconds": 2, "milliseconds": 0}},
        {"send_message": "3232"},
        {"make_call": ["PS51"]},
        {"service": "automation.turn_on", "target": {"entity_id": "automation.home"}},
        {"service": "automation.trigger","target": {"entity_id": "automation.scenes_2"}},
        {"send_http_url": "232323"}]
        """
        aklog_info()
        self.get_scenes_info()
        if by_scenes_name in self.scenes_info:
            scene_id = self.scenes_info[by_scenes_name]['scene_id']
            if manual is None:
                manual = self.scenes_info[by_scenes_name]['manual']
            if trigger_type is None:
                trigger_type = self.scenes_info[by_scenes_name]['trigger_type']
            if conditions is None:
                conditions = self.scenes_info[by_scenes_name]['trigger']
            if tasks is None:
                tasks = self.scenes_info[by_scenes_name]['action']
            self.add_scenes(new_scenes_name, trigger_type, manual, conditions, tasks, scene_id)
        else:
            aklog_info('场景 %s 不存在' % by_scenes_name)

    def delete_scenes(self, *scenes_name):
        """删除场景，通过场景名称获取scene_id"""
        aklog_info()
        self.get_scenes_info()
        for name in scenes_name:
            if name in self.scenes_info:
                scene_id = self.scenes_info[name]['scene_id']
                delete_url = "%s/api/config/automation/config/%s" % (self.base_url, scene_id)
                self.http_send_delete(delete_url)
            else:
                aklog_info('场景 %s 不存在' % name)

    def delete_all_scenes(self):
        """删除所有场景"""
        aklog_info()
        self.get_scenes_info()
        for scene_name in self.scenes_info:
            scene_id = self.scenes_info[scene_name]['scene_id']
            delete_url = "%s/api/config/automation/config/%s" % (self.base_url, scene_id)
            self.http_send_delete(delete_url)

    def manual_trigger_scene(self, scene_name=None, scene_index=1):
        """
        手动触发场景执行
        scene_name不为None时，使用名称来选择场景操作，否则使用序号index来选择场景
        """
        aklog_info()
        self.get_scenes_info()
        if not scene_name:
            entity_id = self.scenes_list[scene_index - 1]['entity_id']
        elif scene_name and scene_name in self.scenes_info:
            entity_id = self.scenes_info[scene_name]['entity_id']
        else:
            aklog_info('场景 %s 不存在' % scene_name)
            return False
        trigger_data = {"type": "call_service", "domain": "automation", "service": "trigger",
                        "service_data": {"entity_id": entity_id}, "id": self.ws_id}
        resp = self.ws_send_request(trigger_data)
        aklog_info('手动触发场景执行结果：%s' % resp.get('success'))
        if not resp.get('success'):
            aklog_info(resp)
        return resp.get('success')

    def set_auto_scene_enable(self, scene_name, enable=1):
        """
        开启关闭自动化场景
        enable: 1 / 0，或者 True / False
        """
        aklog_info()
        self.get_scenes_info()
        if scene_name not in self.scenes_info:
            aklog_info('场景 %s 不存在' % scene_name)
            return False
        entity_id = self.scenes_info[scene_name]['entity_id']
        if str(enable) == '1' or enable is True:
            service = 'turn_on'
        else:
            service = 'turn_off'
        set_scene_data = {"type": "call_service", "domain": "automation", "service": service,
                          "service_data": {"entity_id": entity_id}, "id": 37}
        resp = self.ws_send_request(set_scene_data)
        aklog_info('设置场景 %s %s 结果： %s' % (scene_name, service, resp.get('success')))
        if not resp.get('success'):
            aklog_info(resp)
        return resp.get('success')

    def get_scenes_record(self, start_time=None, end_time=None):
        """
        获取场景执行记录
        start_time, end_time：格式：%Y-%m-%d %H:%M:%S
        return:
        [{'record_id': 19, 'scene_id': '1666943852714', 'name': '333', 'result': True,
        'start_time': '2022-10-28 18:21:35', 'finish_time': '2022-10-28 18:21:35', 'trigger_type': 0, 'data': {}}]
        """
        cur_date = get_os_current_date_time('%Y-%m-%d')
        if not start_time and not end_time:
            start_time = '%s 00:00:00' % get_date_add_delta(cur_date, -30)
            end_time = '%s 23:59:59' % cur_date
        aklog_info()
        resp = self.ws_send_request({"type": "ak_scenes/record_datetime", "style": "scene",
                                     "start_datetime": start_time,
                                     "end_datetime": end_time,
                                     "id": self.ws_id})
        scenes_record = resp['result']
        return scenes_record

    # </editor-fold>

    # <editor-fold desc="布撤防相关">

    def add_security(self, name, activatedDevices=None, isSirenOn=False, relays=None, callList=None,
                     messageContent=None, httpCommand=None, defenceDelay=0, alarmDelay=0):
        """
        添加布防模式
        isSirenOn：是否启用Alarm告警， True， False
        activated_devices: 触发设备列表（Zone1-8），list类型，
        ['Zone1', 'Zone2']

        relays: 触发Relay名称列表，list类型，
        ['Relay1', 'Relay2']

        callList: 呼叫号码列表，如果是设备，传入设备名称，转成设备id，list类型
        ["Burglary", "Panic", "Medical", "Fire", "Customize", "PS51"]
        """
        aklog_info()
        activatedDevices = [] if activatedDevices is None else activatedDevices
        relays = [] if relays is None else relays
        callList = [] if callList is None else callList
        if messageContent is None:
            isSendMessage = False
            messageContent = ''
        else:
            isSendMessage = True
        if httpCommand is None:
            isSendHttpCommand = False
            httpCommand = ''
        else:
            isSendHttpCommand = True

        relays_info = self.generate_security_relay_info(relays)
        activated_devices_info = self.generate_security_activated_device_info(activatedDevices)
        call_list = self.generate_security_call_list(callList)

        add_security_data = {
            "type": "config/ak_security/add",
            "security": {
                "name": name,
                "activitedDevice": activated_devices_info,
                "type": "custom",
                "defenceDelay": int(defenceDelay),
                "isSilentOn": True,
                "isSirenOn": isSirenOn,
                "isSendMessage": isSendMessage,
                "messageContent": messageContent,
                "isSendHttpCommand": isSendHttpCommand,
                "httpCommand": httpCommand,
                "relay": relays_info,
                "isArm": False,
                "alarmDelay": int(alarmDelay),
                "callList": call_list},
            "id": self.ws_id}

        resp = self.ws_send_request(add_security_data)
        aklog_info('添加布防模式 %s 结果：%s' % (name, resp.get('success')))
        if not resp.get('success'):
            aklog_info(resp)
        return resp.get('success')

    def generate_security_relay_info(self, relay_list):
        """根据relay名称列表生成Relay device_id信息"""
        relays_info = []
        for relay in relay_list:
            if relay in self.devices_info:
                relay_info = {"entity_id": self.devices_info[relay]["trigger"]["switch"],
                              "device_id": self.devices_info[relay]['device_id']}
                relays_info.append(relay_info)
            else:
                aklog_info('%s 不存在' % relay)
        return relays_info

    def generate_security_activated_device_info(self, device_list):
        """根据防区名称列表生成防区 device_id信息"""
        activated_device_info = []
        for device in device_list:
            if device in self.devices_info:
                device_info = {"entity_id": self.devices_info[device]["trigger"]["motion"],
                               "device_id": self.devices_info[device]['device_id']}
                activated_device_info.append(device_info)
            else:
                aklog_info('防区 %s 不存在或者未启用' % device)
        return activated_device_info

    def generate_security_call_list(self, call_list):
        """根据relay名称列表生成Relay device_id信息"""
        make_call_info = []
        for call_name in call_list:
            if call_name in self.contacts_info:
                contact_id = self.contacts_info[call_name]['id']
                make_call_info.append(contact_id)
            else:
                make_call_info.append(call_name)
        return make_call_info

    def edit_security(self, by_security_name, new_security_name, activatedDevices=None, isSirenOn=False, relays=None,
                      callList=None, messageContent=None, httpCommand=None, defenceDelay=0, alarmDelay=0):
        """修改布防模式，传入的参数格式跟添加布防模式一致"""
        aklog_info()
        self.get_security_info()
        if by_security_name not in self.security_info:
            aklog_info('布防模式 %s 不存在' % by_security_name)
            return None
        security_id = self.security_info[by_security_name]['id']
        entity_id = self.security_info[by_security_name]['entity_id']

        activatedDevices = [] if activatedDevices is None else activatedDevices
        relays = [] if relays is None else relays
        callList = [] if callList is None else callList
        if messageContent is None:
            isSendMessage = False
            messageContent = ''
        else:
            isSendMessage = True
        if httpCommand is None:
            isSendHttpCommand = False
            httpCommand = ''
        else:
            isSendHttpCommand = True

        relays_info = self.generate_security_relay_info(relays)
        activated_devices_info = self.generate_security_activated_device_info(activatedDevices)
        call_list = self.generate_security_call_list(callList)

        update_security_data = {
            "type": "config/ak_security/update",
            "securities": [{
                "id": security_id,
                "name": new_security_name,
                "type": "custom",
                "defenceDelay": int(defenceDelay),
                "isSilentOn": True,
                "activitedDevice": activated_devices_info,
                "isSirenOn": isSirenOn,
                "isSendMessage": isSendMessage,
                "messageContent": messageContent,
                "isSendHttpCommand": isSendHttpCommand,
                "httpCommand": httpCommand,
                "relay": relays_info,
                "isArm": False,
                "alarmDelay": int(alarmDelay),
                "callList": call_list,
                "entity_id": entity_id}],
            "id": self.ws_id}
        resp = self.ws_send_request(update_security_data)
        aklog_info('修改布防模式 %s 结果：%s' % (by_security_name, resp.get('success')))
        if not resp.get('success'):
            aklog_info(resp)
        return resp.get('success')

    def get_security_info(self):
        """
        获取布防模式信息
        return:
        {'Home':
            {'id': 'de66e8c3ccff452b833d1a36e6d92c40', 'name': 'Home', 'type': 'home', 'defenceDelay': 90,
            'isSilentOn': False, 'activitedDevice': [], 'isSirenOn': False, 'isSendMessage': False,
            'messageContent': '', 'isSendHttpCommand': False, 'httpCommand': '', 'relay': [], 'isArm': False,
            'alarmDelay': 0, 'callList': [], 'entity_id': 'automation.home'}
        }
        """
        aklog_info()
        resp = self.ws_send_request({"type": "config/ak_security/list", "id": self.ws_id})
        results = resp['result']
        for ret in results:
            security_name = ret['name']
            self.security_info[security_name] = ret
        # aklog_info(self.security_info)
        return self.security_info

    def get_security_arming_status(self, name):
        """获取防区的布撤防状态"""
        self.get_security_info()
        if name in self.security_info:
            return self.security_info[name]['isArm']
        else:
            aklog_info('找不到 %s 布防模式')
            return None

    def set_security_arming_status(self, by_security_name, arming=True, ignore=True):
        """
        设置布防模式启用禁用
        arming: True / False
        ignore: True / False
        """
        aklog_info()
        self.get_security_info()
        if by_security_name not in self.security_info:
            aklog_info('布防模式 %s 不存在' % by_security_name)
            return None
        security_id = self.security_info[by_security_name]['id']

        for i in range(2):
            set_security_data = {"type": "config/ak_security/arm", "arm": arming,
                                 "security_id": security_id, "id": self.ws_id}
            resp = self.ws_send_request(set_security_data)
            if i == 0 and resp['result']['isArm'] != arming and resp['result']['ignore_list']:
                # 启用时提示是否忽略状态错误的防区
                if ignore:
                    set_security_data['ignore'] = True
                    continue
                else:
                    aklog_error('存在状态错误的防区，不忽略，放弃设置布防模式')
                    return True
            elif resp['result']['isArm'] == arming:
                aklog_info('设置布防模式 %s 为 %s 成功' % (by_security_name, arming))
                return True
            else:
                aklog_error('设置布防模式 %s 为 %s 失败' % (by_security_name, arming))
                return False

    def batch_set_security_arming_status(self, arming=True, ignore=True):
        """批量设置布防模式启用和禁用"""
        aklog_info()
        # 先获取布防模式的ID列表
        self.get_security_info()
        security_id_list = []
        for security in self.security_info:
            security_id_list.append(self.security_info[security]['id'])

        for i in range(2):
            batch_set_security_data = {"type": "config/ak_security/batch_arm",
                                       "security_ids": security_id_list,
                                       "arm": arming,
                                       "id": self.ws_id}
            resp = self.ws_send_request(batch_set_security_data)
            is_arm_list = []
            for security_ret in resp['result']['ignore_lists']:
                is_arm_list.append(security_ret['isArm'])

            if i == 0 and (not arming) in is_arm_list:
                # 启用时提示是否忽略状态错误的防区
                if ignore:
                    batch_set_security_data['ignore'] = True
                    continue
                else:
                    aklog_error('存在状态错误的防区，不忽略，放弃设置布防模式')
                    return True
            elif (not arming) not in is_arm_list:
                aklog_info('批量设置布防模式为 %s 成功' % arming)
                return True
            else:
                aklog_error('批量设置布防模式为 %s 失败' % arming)
                return False

    def get_security_silent_mode(self, name):
        """获取防区的布撤防状态"""
        self.get_security_info()
        if name in self.security_info:
            return self.security_info[name]['isSilentOn']
        else:
            aklog_info('找不到 %s 布防模式')
            return None

    def set_security_silent_mode(self, security_name, isSilentOn=True):
        """设置布防模式静音状态，True为启用静音，False为关闭静音"""
        aklog_info()
        self.get_security_info()
        if security_name not in self.security_info:
            aklog_info('布防模式 %s 不存在' % security_name)
            return None
        security_data = self.security_info[security_name]
        security_data.pop('entity_id')
        security_data['isSilentOn'] = isSilentOn
        set_security_data = {"type": "config/ak_security/update", "securities": [security_data],
                             "silent": True, "id": self.ws_id}

        # 获取设置结果，判断是否设置成功
        resp = self.ws_send_request(set_security_data)
        for security in resp['result']:
            if security['name'] == security_name:
                if security['isSilentOn'] == isSilentOn:
                    aklog_info('设置布防模式 %s 的silent状态为 %s 成功' % (security_name, isSilentOn))
                    return True
                else:
                    aklog_error('设置布防模式 %s 的silent状态为 %s 失败' % (security_name, isSilentOn))
                    return False
        aklog_error('获取布防模式结果失败')
        return None

    def batch_set_security_silent_mode(self, isSilentOn=True):
        """批量设置所有布防模式静音状态，True为启用静音，False为关闭静音"""
        aklog_info()
        self.get_security_info()
        security_list = []
        for security in self.security_info:
            self.security_info[security]['isSilentOn'] = isSilentOn
            security_list.append(self.security_info[security])
        security_counts = len(security_list)

        batch_set_security_data = {"type": "config/ak_security/update", "securities": security_list,
                                   "silent": True, "id": self.ws_id}

        # 获取设置结果，判断是否设置成功
        resp = self.ws_send_request(batch_set_security_data)
        security_ret_list = []
        if resp.get('success') is False:
            aklog_error('批量设置所有布防模式的silent状态为 %s 失败' % isSilentOn)
            return False

        for security_ret in resp['result']:
            security_ret_list.append(security_ret['isSilentOn'])
        if security_ret_list == [isSilentOn] * security_counts:
            aklog_info('批量设置所有布防模式的silent状态为 %s 成功' % isSilentOn)
            return True
        else:
            aklog_error('批量设置所有布防模式的silent状态为 %s 失败' % isSilentOn)
            return False

    def delete_security(self, *security_names):
        """删除自定义布防模式"""
        aklog_info()
        self.get_security_info()
        security_id_list = []
        for name in security_names:
            if name not in self.security_info:
                aklog_info('布防模式 %s 不存在' % name)
                continue
            elif name in ['Home', 'Night', 'Away']:
                aklog_info('%s 模式为默认的，不能删除' % name)
                continue
            security_id = self.security_info[name]['id']
            security_id_list.append(security_id)

        delete_security_data = {"type": "config/ak_security/delete", "ids": security_id_list,
                                "id": self.ws_id}
        resp = self.ws_send_request(delete_security_data)
        aklog_info('删除布防模式 %s 结果：%s' % (tuple(security_names), resp.get('success')))
        if not resp.get('success'):
            aklog_info(resp)
        return resp.get('success')

    def delete_all_security(self):
        """删除所有自定义布防模式"""
        aklog_info()
        self.get_security_info()
        security_id_list = []
        for name in self.security_info:
            if name in ['Home', 'Night', 'Away']:
                aklog_info('%s 模式为默认的，不能删除' % name)
                continue
            security_id = self.security_info[name]['id']
            security_id_list.append(security_id)

        delete_security_data = {"type": "config/ak_security/delete", "ids": security_id_list,
                                "id": self.ws_id}
        resp = self.ws_send_request(delete_security_data)
        aklog_info('删除所有布防模式结果：%s' % resp.get('success'))
        if not resp.get('success'):
            aklog_info(resp)
        return resp.get('success')

    def get_security_record(self, start_time=None, end_time=None):
        """
        获取布防模式触发记录
        """
        cur_date = get_os_current_date_time('%Y-%m-%d')
        if not start_time and not end_time:
            start_time = '%s 00:00:00' % get_date_add_delta(cur_date, -30)
            end_time = '%s 23:59:59' % cur_date
        aklog_info()
        send_data = {"type": "config/ak_security/record", "record_type": "trigger", "page": 1, "page_size": 10000,
                     "start_datetime": start_time, "end_datetime": end_time, "id": self.ws_id}
        resp = self.ws_send_request(send_data)
        security_record = resp['result']
        return security_record

    # </editor-fold>


if __name__ == '__main__':
    user_web_inf = AkubelaUserWebInterface()
    user_web_inf.init('192.168.88.181', 'hzs01_cbuat_user1@aktest.top', 'Ak#123456')
    user_web_inf.interface_init('https://my.uat.akubela.com')
    time.sleep(2)
    # print(user_web_inf.get_security_info())
    # print(user_web_inf.get_scenes_info())

    # for i in range(1, 8):
    #     user_web_inf.add_scenes('scene_%s' % i, 'or', True, tasks=[{"send_http_url": "test111"}])
    #     user_web_inf.add_security('Arming%s' % i)
    # user_web_inf.add_scenes('444', 'or', False,
    #                         [{"platform": "device", "device_name": "sos", "type": "unsafe",
    #                           "domain": "binary_sensor", "trigger_option": "safety"}],
    #                         [{"send_message": "3232"}])
    # time.sleep(1)
    # res = user_web_inf.get_devices_list_info()
    # for i in res.values():
    #     print(i)
    #     print(i.get('name'))
    #     print(i.get('detail').get('online'))

    # time.sleep(1)
    user_web_inf.interface_logout()
