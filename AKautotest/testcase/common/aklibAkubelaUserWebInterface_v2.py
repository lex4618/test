# -*- coding: utf-8 -*-

import sys
import os
import base64

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
import datetime


class AkubelaUserWebInterface_v2:

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
        self.scenes_info = {}
        self.scenes_list = []
        self.security_info = {}
        self.devices_list_info = {}
        self.family_id = None
        self.ws_id_scan = None
        self.ws_id_scan_ecosystem = None
        self.device_name = ''

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
            # self.get_contacts_info()
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

    @staticmethod
    def dict_iter(d):
        for i in d.items():
            yield str(i).encode()

    # 远程穿透方式登录用户web
    def __interface_remote_login(self, print_trace=True):
        """全球管理地址入口远程登录用户web"""
        aklog_info('__interface_remote_login, user: %s, pwd: %s' % (self.username, self.password))
        password = self.password.encode('utf-8')
        encoded_password = base64.b64encode(password)
        passwords = encoded_password.decode('utf-8')
        try:
            header1 = {'User-Platform': 'pc', 'Content-Type': 'application/json'}
            payload_1 = json.dumps({"account": self.username,
                                    "password": passwords,
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
            if resp_1.status_code != 200:
                return False
            result_1 = resp_1.json()
            aklog_info(result_1)
            user_token = result_1['result']['token']
            remote_url = result_1['result']['remote_url']
            # url_3 = 'https://%s/invoke/auth-portal/method/login' % remote_url
            # aklog_debug('requests.post: %s, data: %s' % (url_3, {"ha_token": user_token}))
            # resp_4 = requests.post(url=url_3, data={"ha_token": user_token}, timeout=30)
            # 获取响应头中名为"User-Token"的属性值（不区分大小写）
            # results1 = resp_4.json()
            # aklog_info(results1)
            # result_4 = resp_4.json()
            # code_result = result_4['result']

            url = "https://%s/invoke/auth-portal/method/login" % remote_url
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en,ja;q=0.9,zh;q=0.8,zh-CN;q=0.7",
                "Connection": "keep-alive",
                "Content-Type": "application/json;charset:UTF-8",
                "Origin": "https://%s" % remote_url,
                "Referer": "https://%s/?ha_token=%s" % (remote_url, user_token),
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "User-Platform": "pc",
                "sec-ch-ua": '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }

            data = {
                "ha_token": user_token
            }
            response5 = requests.post(url, headers=headers, json=data)
            aklog_info(response5.text)
            self.access_token = response5.headers.get('User-Token')
            self.base_url = 'wss://%s' % remote_url
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
        url1 = '%s/invoke/auth-portal/method/logout' % self.base_url
        url = url1.replace('wss://', 'https://').replace('ws://', 'http://')
        aklog_debug('requests.delete: %s, data: %r' % (url, revoke_token_data))
        resp = requests.delete(url=url, headers=header, data=m, timeout=30)
        aklog_debug('status_code: %s, result: %s' % (resp.status_code, resp.text))
        time.sleep(1)
        if resp.status_code == 302:
            aklog_info('登出成功')
            return True
        else:
            aklog_error('登出失败')
            return False

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
        aklog_info(resp)
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
        get_family_users_info = self.get_family_users_info(fm_email)
        fm_user_id = None
        if get_family_users_info is not None:
            fm_user_id = self.get_family_users_info(fm_email)['user_id']
            # users = self.get_family_users_info(fm_email)
            # for user in users:
            #     email_sub = user["email"]
            #     if email_sub == fm_email:
            #         fm_user_id = user["user_id"]
        aklog_info(fm_user_id)
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

    def del_account_and_transfer(self, main_email, user_email):
        """
        删除主帐号，然后将管理员转移给其他成员，如果存在多个家庭成员，需要指定转移的成员邮箱
        """
        aklog_info()
        family_id = self._get_family_id()
        family_users = self.get_family_users_info()
        user_id = None
        for fm_user in family_users:
            if fm_user['email'] == user_email:
                user_id = fm_user['user_id']
                continue
        main_id = None
        for fm_user in family_users:
            if fm_user['email'] == main_email:
                main_id = fm_user['user_id']
                continue
        data = {
            "type": "ak_account/users/delete",
            "id": self.ws_id,
            "unbind": True,
            "user_id": main_id,
            "family_id": family_id,
            "transfer_user_id": user_id
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('主账号删除并权限转移成功')
            return True
        else:
            aklog_error('主账号删除并权限转移失败')
            aklog_debug('resp: %s' % resp)
            return False

    def account_change_permission(self, user_email):
        """转移主账号权限给子账号"""
        aklog_info()
        family_users = self.get_family_users_info()
        user_id = None
        for fm_user in family_users:
            if fm_user['email'] == user_email:
                user_id = fm_user['user_id']
                continue
        data = {
            "type": "ak_account/permission",
            "id": self.ws_id,
            "user_id": user_id,
            "transfer_to_master": True}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('主账号权限转移成功')
            return True
        else:
            aklog_error('主账号权限转移失败')
            aklog_debug('resp: %s' % resp)
            return False

    def account_unbind_transfer(self, main_email, user_email):
        """解绑主账号并转移权限给子账号"""
        aklog_info()
        family_id = self._get_family_id()
        family_users = self.get_family_users_info()
        user_id = None
        for fm_user in family_users:
            if fm_user['email'] == user_email:
                user_id = fm_user['user_id']
                continue
        main_id = None
        for fm_user in family_users:
            if fm_user['email'] == main_email:
                main_id = fm_user['user_id']
                continue
        data = {
            "type": "ak_account/families/unbind",
            "id": self.ws_id,
            "unbind": True,
            "user_id": main_id,
            "family_id": family_id,
            "transfer_user_id": user_id
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('主账号解绑并权限转移成功')
            return True
        else:
            aklog_error('主账号解绑并权限转移失败')
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

    def add_sub_account(self, account_data):
        """
        添加子账号
        type   String类型   ak_account/users/create
        family_id  String类型  家庭ID
        data   Object类型  用户信息，根据需要填写
        data:[{
            first_name(String类型):用户首字母
            last_name(String类型):用户尾字母
            email(String类型):用户邮箱
            region(String类型):用户地区
            mobile(String类型):用户手机号
            land_line(String类型):用户固定电话
            authority(Int类型)：0:子账号（普通权限）;1:子账号（带管理员权限）;2:主账号
            intercom(Bool类型）:true: 绑定对讲  false: 未绑定对讲
        }]
        返回参数：
            "id":31,
            "type":"result",
            "success":true,
            result  Object类型[{
            family_id(String类型):家庭ID
            user_id(String类型):用户id
            username(String类型):用户名
        }]
        data数据参考：
           data = {
        "first_name": "tu3",
        "last_name": "wm3",
        "email": "twm_acc2444466@aktest.top",
        "region": "123123",
        "mobile": "123123",
        "land_line": "",
        "authority": 0,
        "intercom": False
    }
        """
        aklog_info()
        family_id = self._get_family_id()
        time.sleep(1)
        sub_account_data = account_data
        add_sub_data = {"type": "ak_account/users/create",
                        "family_id": family_id,
                        "data": sub_account_data}
        resp = self.ws_send_request(add_sub_data)
        if resp and resp.get('success'):
            aklog_info('添加子账号成功')
            return True
        else:
            aklog_error('添加子账号失败')
            aklog_error(resp)
            return False

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
        """
        设置开启脱云模式
        mode: True表示开启脱云模式，False表示关闭脱云模式
        """
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

    def get_devices_info(self, device_name=None):
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
        resp = self.ws_send_request({"type": "config/ak_device/list", "id": self.ws_id})
        if resp is None or isinstance(resp, bool):
            return resp
        results = resp.get('result')
        if device_name:
            for ret in results:
                if ret['name'] == device_name:
                    return ret
            aklog_warn('%s 未找到' % device_name)
            return None
        return results

    def get_contacts_info(self):
        """
        获取联系人信息，设备名称转成设备ID, 新版本没有该接口了
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
        contacts_info = {}
        for ret in results:
            contact_name = ret['name']
            contacts_info[contact_name] = ret
        # aklog_info(self.contacts_info)
        return contacts_info

    def get_contact_name_list(self):
        """获取设备名称列表"""
        contacts_info = self.get_contacts_info()
        contact_name_list = []
        for contact_name in contacts_info:
            contact_name_list.append(contact_name)
        aklog_debug('contact_name_list: %s' % contact_name_list)
        return contact_name_list

    def get_device_name_list(self, product_type=None):
        """获取设备名称列表"""
        devices_info = self.get_devices_info()
        device_name_list = []
        if devices_info and isinstance(devices_info, list):
            for device in devices_info:
                if product_type and device['product_type'] != product_type:
                    continue
                device_name_list.append(device['name'])
        aklog_debug('device_name_list: %s' % device_name_list)
        return device_name_list

    def get_devices_entity_id(self, device_name=None, device_type=None):
        """
        3.0版本获取家庭某个设备的控制的实体id的接口,传入设备名和设备的控制类型，如switch，lock
        """
        aklog_info()
        resp = self.ws_send_request({"type": "config/ak_device/list", "id": self.ws_id})
        if resp is None or isinstance(resp, bool):
            return resp
        results = resp.get('result')
        if device_name:
            for ret in results:
                if ret['name'] == device_name:
                    for enti in ret['attributes']:
                        if enti['domain'] == device_type:
                            return enti['entity_id']
            aklog_warn('%s 未找到' % device_name)
        return None

    def get_devices_entity_id_233(self, device_name=None, device_type=None):
        """
        获取家庭某个设备的控制的实体id的接口,传入设备名和设备的控制类型，如switch，lock
            {
            "id":88,
            "type":"result",
            "success":true,
            "result":[
        {
            "area_id":"",
            "device_id":"18f989d28588477a8f96dce28be1b087",
            "product_attributes":"relay",
            "product_type":"Switch",
            "name":"HyPanel-230354 - relay2",
            "location":"",
            "favorite":false,
            "version":"",
            "sort_id":1,
            "bypass":false,
            "bypass_time":"",
            "parent_device_id":"4ab159c5f54e493085698fbbad248cb1",
            "is_wire":false,
            "mac":"",
            "source":0,
            "relay_index":2,
            "ownership":"HyPanel-230354",
            "child_ids":[

            ],
            "product_model":"Switch",
            "detail":{
                "switch":{
                    "value":"off",
                    "entity_id":"switch.0b4cda78dd59420c9854b18aad23a822",
                    "entity_name":"Unnamed Device",
                    "timestamp":1687172472,
                    "format_device_time":"2023-06-19 11:01:12",
                    "alarm_timestamp":0,
                    "alarm_device_time":""
                },
                "energy":{
                    "value":"0.0",
                    "entity_id":"sensor.e20be4d7acc845c48dd2f6b3d3902fb3",
                    "entity_name":"",
                    "timestamp":1686906483,
                    "format_device_time":"2023-06-16 09:08:03",
                    "alarm_timestamp":0,
                    "alarm_device_time":""
                },
                "power":{
                    "value":"0",
                    "entity_id":"sensor.d050d04934404155b736bd6e9371410d",
                    "entity_name":"",
                    "timestamp":1686815350,
                    "format_device_time":"2023-06-15 07:49:10",
                    "alarm_timestamp":0,
                    "alarm_device_time":""
                },
                "online":true
                 }
             }
         ]
        }
        """
        aklog_info()
        resp = self.ws_send_request({"type": "config/ak_device/list", "id": self.ws_id})
        if resp is None or isinstance(resp, bool):
            return resp
        results = resp.get('result')
        if device_name:
            for ret in results:
                if ret['name'] == device_name:
                    return ret['detail'][device_type]['entity_id']
            aklog_warn('%s 未找到' % device_name)
        return None

    def control_device(self, entity_id=None, domain=None, service_type=None):
        """
        调用服务控制设备,
        domain ：‘switch’：switch类，‘light’: 灯类，'cover':窗帘，‘button’: 按键，’lock‘：锁
        service_type:控制类型 turn_on：打开，turn_off：关闭 ， unlock:解锁   lock：锁
        {
             "type":"call_service",
                "id":3,
                "domain":"switch",
                "service":"turn_on",
                "service_data":{
                 "entity_id":"switch.smart_plug"
             }
            }
        """
        aklog_info()
        resp = self.ws_send_request({"type": "call_service", "domain": domain, "service": service_type,
                                     "service_data": {"entity_id": entity_id}, "id": self.ws_id})
        aklog_info(resp)
        #return resp.get('success')
        return resp


    def get_devices_status(self, device_name=None, device_type=None):
        """
        获取家庭某个设备的开关状态的接口,传入设备名和设备的控制类型，如switch，lock
        """
        aklog_info()
        resp = self.ws_send_request({"type": "config/ak_device/list", "id": self.ws_id})
        if resp is None or isinstance(resp, bool):
            return resp
        results = resp.get('result')
        if device_name:
            for ret in results:
                if ret['name'] == device_name:
                    for status in ret['attributes']:
                        if status['domain'] == device_type:
                            return status['value']
            aklog_warn('%s 未找到' % device_name)
        return None

    def get_devices_status_233(self, device_name=None, device_type=None):
        """
        获取家庭某个设备的开关状态的接口,传入设备名和设备的控制类型，如switch，lock
            {
            "id":88,
            "type":"result",
            "success":true,
            "result":[
            {
            "area_id":"",
            "device_id":"18f989d28588477a8f96dce28be1b087",
            "product_attributes":"relay",
            "product_type":"Switch",
            "name":"HyPanel-230354 - relay2",
            "location":"",
            "favorite":false,
            "version":"",
            "sort_id":1,
            "bypass":false,
            "bypass_time":"",
            "parent_device_id":"4ab159c5f54e493085698fbbad248cb1",
            "is_wire":false,
            "mac":"",
            "source":0,
            "relay_index":2,
            "ownership":"HyPanel-230354",
            "child_ids":[

            ],
            "product_model":"Switch",
            "detail":{
                "switch":{
                    "value":"off",
                    "entity_id":"switch.0b4cda78dd59420c9854b18aad23a822",
                    "entity_name":"Unnamed Device",
                    "timestamp":1687172472,
                    "format_device_time":"2023-06-19 11:01:12",
                    "alarm_timestamp":0,
                    "alarm_device_time":""
                },
                "energy":{
                    "value":"0.0",
                    "entity_id":"sensor.e20be4d7acc845c48dd2f6b3d3902fb3",
                    "entity_name":"",
                    "timestamp":1686906483,
                    "format_device_time":"2023-06-16 09:08:03",
                    "alarm_timestamp":0,
                    "alarm_device_time":""
                },
                "power":{
                    "value":"0",
                    "entity_id":"sensor.d050d04934404155b736bd6e9371410d",
                    "entity_name":"",
                    "timestamp":1686815350,
                    "format_device_time":"2023-06-15 07:49:10",
                    "alarm_timestamp":0,
                    "alarm_device_time":""
                },
                "online":true
                 }
             }
         ]
        }
        """
        aklog_info()
        resp = self.ws_send_request({"type": "config/ak_device/list", "id": self.ws_id})
        if resp is None or isinstance(resp, bool):
            return resp
        results = resp.get('result')
        #aklog_info(results)
        if device_name:
            for ret in results:
                if ret['name'] == device_name:
                    aklog_info('%s 当前状态为:#####' % device_name)
                    aklog_info(ret['detail'][device_type]['value'])
                    return ret['detail'][device_type]['value']
            aklog_warn('%s 未找到' % device_name)
        return None

    def get_devices_status_233_AC(self, device_name=None, device_type=None):
        """
        获取家庭某个设备的开关状态的接口,传入设备名和设备的控制类型，如switch，lock
            {
            "id":88,
            "type":"result",
            "success":true,
            "result":[
            {
            "area_id":"",
            "device_id":"18f989d28588477a8f96dce28be1b087",
            "product_attributes":"relay",
            "product_type":"Switch",
            "name":"HyPanel-230354 - relay2",
            "location":"",
            "favorite":false,
            "version":"",
            "sort_id":1,
            "bypass":false,
            "bypass_time":"",
            "parent_device_id":"4ab159c5f54e493085698fbbad248cb1",
            "is_wire":false,
            "mac":"",
            "source":0,
            "relay_index":2,
            "ownership":"HyPanel-230354",
            "child_ids":[

            ],
            "product_model":"Switch",
            "detail":{
                "switch":{
                    "value":"off",
                    "entity_id":"switch.0b4cda78dd59420c9854b18aad23a822",
                    "entity_name":"Unnamed Device",
                    "timestamp":1687172472,
                    "format_device_time":"2023-06-19 11:01:12",
                    "alarm_timestamp":0,
                    "alarm_device_time":""
                },
                "energy":{
                    "value":"0.0",
                    "entity_id":"sensor.e20be4d7acc845c48dd2f6b3d3902fb3",
                    "entity_name":"",
                    "timestamp":1686906483,
                    "format_device_time":"2023-06-16 09:08:03",
                    "alarm_timestamp":0,
                    "alarm_device_time":""
                },
                "power":{
                    "value":"0",
                    "entity_id":"sensor.d050d04934404155b736bd6e9371410d",
                    "entity_name":"",
                    "timestamp":1686815350,
                    "format_device_time":"2023-06-15 07:49:10",
                    "alarm_timestamp":0,
                    "alarm_device_time":""
                },
                "online":true
                 }
             }
         ]
        }
        """
        aklog_info()
        resp = self.ws_send_request({"type": "config/ak_device/list", "id": self.ws_id})
        if resp is None or isinstance(resp, bool):
            return resp
        results = resp.get('result')
        aklog_info(results)
        if device_name:
            for ret in results:
                if ret['name'] == device_name:
                    return ret['detail'][device_type]['state']['value']
            aklog_warn('%s 未找到' % device_name)
        return None

    def ak_change_event(self):
        """
            "type": "subscribe_events"
            "id": 2
            "event_type": 'ak_device_event
        """
        aklog_info()
        resp = self.ws_send_request({"type": "subscribe_events", "event_type": 'ak_device_event', "id": self.ws_id})

        return None

    # </editor-fold>
    def add_room(self, room_name):
        """用户web添加房间接口"""
        resp_get = self.ws_send_request({"type": "config/ak_area/create",
                                         "id": self.ws_id,
                                         "name": room_name})
        aklog_info(resp_get)
        res = resp_get['success']
        return res

    def get_device_id(self, device_name):
        """通过设备名称获取device id"""
        aklog_info()
        devices_id = None
        resp = self.ws_send_request({"type": "config/ak_device/list", "id": self.ws_id})
        if resp is None or isinstance(resp, bool):
            return resp
        results = resp.get('result')
        for ret in results:
            if device_name == ret['name']:
                devices_id = ret['device_id']
                aklog_info(devices_id)
        return devices_id

    def start_scan_event(self):
        """用户web调用扫描事件订阅接口"""
        resp_get_start_event = self.ws_send_request({
            "event_type": "ak_scan_event",
            "id": self.ws_id,
            "type": "subscribe_events"
        })
        self.ws_id_scan = self.ws_id
        if resp_get_start_event and resp_get_start_event.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp_get_start_event)
            return False

    def stop_scan_event(self):
        """用户web调用关闭扫描订阅接口"""
        resp_get = self.ws_send_request({
            "type": "unsubscribe_events",
            "id": self.ws_id,
            "subscription": self.ws_id_scan - 1
        })
        if resp_get and resp_get.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp_get)
            return False

    def start_scan(self, device_name):
        """开启网关扫描zigbee设备接口"""
        device_id = self.get_device_id(device_name)
        resp_get = self.ws_send_request({
            "type": "config/ak_device/scan",
            "id": self.ws_id,
            "device_id": device_id
        })
        if resp_get and resp_get.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp_get)
            return False

    def stop_scan(self, device_name):
        """关闭网关扫描zigbee设备接口"""
        device_id = self.get_device_id(device_name)
        resp_get = self.ws_send_request({
            "type": "config/ak_device/cancel_scan",
            "id": self.ws_id,
            "device_id": device_id
        })
        if resp_get and resp_get.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp_get)
            return False

    def start_scan_by_type(self, device_name, device_type):
        """按照设备类型添加，开启网关扫描zigbee接口"""
        device_id = self.get_device_id(device_name)
        resp_get = self.ws_send_request({
            "type": "config/ak_device/scan",
            "id": self.ws_id,
            "device_id": device_id,
            "type_name": device_type
        })
        if resp_get and resp_get.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp_get)
            return

    def scan_ecosystem_even(self):
        """用户web调用扫描生态设备事件订阅接口"""
        resp = self.ws_send_request({
            "event_type": "ak_scan_ecosystem_event",
            "id": self.ws_id,
            "type": "subscribe_events"
        })
        self.ws_id_scan_ecosystem = self.ws_id
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def scan_ecosystem_start(self, device_name, device_type):
        """用户web调用开始扫描生态设备的接口"""
        device_id = self.get_device_id(device_name)
        resp = self.ws_send_request({
            "type": "config/ak_device/scan_ecosystem",
            "id": self.ws_id,
            "gateway_device_id": device_id,
            "type_name": device_type
        })
        self.ws_id_scan = self.ws_id
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def stop__ecosystem_even(self):
        """用户web关闭调用扫描生态设备事件订阅接口"""
        resp = self.ws_send_request({
            "type": "unsubscribe_events",
            "id": self.ws_id,
            "subscription": self.ws_id_scan_ecosystem - 1
        })
        self.ws_id_scan = self.ws_id
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

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
        # for i in range(len(conditions)):
        #     if conditions[i]['platform'] == 'device':
        #         conditions[i] = self.generate_scenes_condition_device_info(conditions[i])
        # scenes_add_data['trigger'] = conditions

        # for j in range(len(tasks)):
        #     if tasks[j].get('device_name'):
        #         tasks[j] = self.generate_scenes_task_device_info(tasks[j])
        #     if tasks[j].get('make_call'):
        #         tasks[j] = {"make_call": ["d0b76b6d6193651c201e750379cb7e74c"]}
        scenes_add_data['action'] = [{"delay": {"hours": 0, "minutes": 0, "seconds": 2, "milliseconds": 0}}]
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
        scenes_list = resp['result']
        aklog_info(scenes_list)
        return scenes_list

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
                return True
            else:
                aklog_info('场景 %s 不存在' % name)
                return False

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
        aklog_info(resp)
        scenes_record = resp['result']
        return scenes_record

    def update_scene_ws(self, scene_name):
        """websocket方式更新场景接口"""
        scene_id = None
        for scene in self.get_scenes_info():
            if scene["name"] == scene_name:
                scene_id = scene["scene_id"]
        resp = self.ws_send_request({
            "type": "ak_scenes/create_update",
            "id": self.ws_id,
            "scene_id": scene_id,
            "scene_data": {
                "type": 0,
                "manual": True,
                "favorite": False,
                "id": scene_id,
                "alias": "222",
                "trigger": [],
                "condition": [],
                "action": [
                    {
                        "delay": {
                            "hours": 0,
                            "milliseconds": 0,
                            "minutes": 0,
                            "seconds": 5
                        }
                    }
                ],
                "trigger_type": "or",
                "canvas_pos": "",
                "style": "scene",
                "support_long_press": False,
                "image": 114
            }
        })
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def add_time_scene(self):
        """websocket方式更创建日出的定时场景"""
        resp = self.ws_send_request({
            "type": "ak_scenes/create_update",
            "id": self.ws_id,
            "scene_id": "1703943436199",
            "scene_data": {
                "trigger_type": "or",
                "alias": "time",
                "description": "",
                "style": "scene",
                "type": 0,
                "manual": False,
                "trigger": [
                    {
                        "platform": "sun",
                        "event": "sunrise",
                        "offset": "0"
                    }
                ],
                "condition": [],
                "action": [
                    {
                        "send_notification": "sun rise time"
                    }
                ],
                "favorite": False,
                "mode": "single",
                "image": 103
            }
        })
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    # </editor-fold>

    # <editor-fold desc="布撤防相关">

    def add_security(self,scene_name, activatedDevices=None, isSirenOn=False, relays=None, callList=None,
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
            "id": self.ws_id,
            "security": {
                "name": scene_name,
                "activitedDevice": [],
                "type": "custom",
                "defenceDelay": 0,
                "isSilentOn": False,
                "isSirenOn": True,
                "isSendMessage": False,
                "messageContent": "",
                "isSendHttpCommand": False,
                "httpCommand": "",
                "relay": [],
                "isArm": False,
                "alarmDelay": 0,
                "callList": []
            }
        }

        resp = self.ws_send_request(add_security_data)
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

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

    def batch_set_security_silent_mode(self, isSirenOn=False):
        """批量设置所有布防模式静音状态，False为启用静音，True为关闭静音"""
        aklog_info()
        self.get_security_info()
        security_list = []
        for security in self.security_info:
            self.security_info[security]['isSirenOn'] = isSirenOn
            security_list.append(self.security_info[security])
        security_counts = len(security_list)

        batch_set_security_data = {"type": "config/ak_security/update", "securities": security_list,
                                   "silent": True, "id": self.ws_id}

        # 获取设置结果，判断是否设置成功
        resp = self.ws_send_request(batch_set_security_data)
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
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
        send_data = {
            "type": "config/ak_security/record",
            "record_type": "trigger",
            "id": self.ws_id,
            "page": 1,
            "page_size": 1000
        }
        resp = self.ws_send_request(send_data)
        aklog_info(resp)
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    # </editor-fold>

    # <editor-fold desc="照片墙相关">

    def add_photo(self, device_name):
        """
        添加照片墙
        """
        device_id = self.get_device_id(device_name)
        send_data = {
            "type": "ak_photo/device_add_image",
            "id": self.ws_id,
            "image": ",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",
            "device_id": device_id
        }
        resp = self.ws_send_request(send_data)
        return resp
        # if resp and resp.get('success'):
        #     return True
        # else:
        #     aklog_debug('resp: %s' % resp)
        #     return False

    def delete_photo(self, device_name, photo_url):
        """
        添加照片墙
        """
        device_id = self.get_device_id(device_name)
        send_data = {
            "type": "ak_photo/batch_delete",
            "id": self.ws_id,
            "image_url_list": [
                photo_url
            ],
            "device_id": device_id
        }
        resp = self.ws_send_request(send_data)
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    # </editor-fold>

    # <editor-fold desc="Setting相关">

    def set_language(self, language):
        """
        语言设置
        """
        set_lang = ""
        if language == 'CN':
            set_lang = "zh-CN"
        else:
            set_lang = "en-US"
        resp = self.ws_send_request({"type": "ak_config/update",
                                     "id": self.ws_id,
                                     "item": {
                                         "Settings.LANGUAGE.Type": set_lang}})
        res = resp['success']
        return res

    def set_device_Date(self):
        """日期时间设置"""
        date = str(datetime.date.today())
        time = datetime.time
        resp = self.ws_send_request({"type": "config/notice_change",
                                     "source": "web",
                                     "id": self.ws_id,
                                     "date": date,
                                     "time": "00:00:00",
                                     "Settings.TIME.Enabled24_HourTime": 1,
                                     "Settings.TIME.SetAutomaticallyEnabled": 0,
                                     "Settings.TIME.DateFormat": 5})
        res = resp['success']
        return res

    def set_security_code(self, code):
        """安防密码设置"""
        resp = self.ws_send_request({"id": self.ws_id,
                                     "type": "config/notice_change",
                                     "Settings.ALARM.Password": code,
                                     "source": "web"})
        res = resp['success']
        return res

    def set_sos(self, sos_staut):
        """SOS设置"""

        resp1 = self.ws_send_request({"type": "ak_config/update",
                                      "id": self.ws_id,
                                      "item": {
                                          "Settings.SOS.CallNumberList": "burglary"
                                      }})

        resp2 = self.ws_send_request({"type": "ak_config/update",
                                      "id": self.ws_id,
                                      "item": {
                                          "Settings.SOS.Burglary": "123123"
                                      }})

        resp = self.ws_send_request({"type": "ak_config/update",
                                     "id": self.ws_id,
                                     "item": {
                                         "Settings.SOS.Enabled": sos_staut,
                                         "Settings.SOS.CallNumberList": "burglary"
                                     }})
        res = resp['success']
        return res

    def set_feedback(self):
        """用户web设置feedback"""
        resp = self.ws_send_request({"type": "ak_feedback/record",
                                     "id": self.ws_id,
                                     "content": "自动化测试"})
        res = resp['success']
        return res

    def set_measurement_settings(self):
        """用户web接口设置温度单位"""
        set_tmp = ''
        resp_get = self.ws_send_request({"type": "ak_config/get",
                                         "id": self.ws_id,
                                         "item": [
                                             "Settings.SYSTEM.TemperatureUnit"
                                         ]})
        get_tmp = resp_get['result']['Settings.SYSTEM.TemperatureUnit']
        if get_tmp == '1':
            set_tmp = 0
        else:
            set_tmp = 1
        resp_set = self.ws_send_request({
            "type": "ak_config/update",
            "id": self.ws_id,
            "item": {
                "Settings.SYSTEM.TemperatureUnit": set_tmp
            }
        })
        res = resp_set['success']
        return res

    def get_energy(self):
        """用户web获取能源数据"""
        resp_get = self.ws_send_request({"type": "config/ak_energy/info",
                                         "id": self.ws_id,
                                         "mode": 1})
        aklog_info(resp_get)
        res = resp_get['success']
        return res

    # </editor-fold>


if __name__ == '__main__':
    # user_web_inf = AkubelaUserWebInterface_v2()
    # user_web_inf.init('192.168.88.149', 'hzs01_t_s_user2@aktest.top', 'pJMq45i8y7')
    # user_web_inf.interface_init()
    time.sleep(2)
    #
    # user_web_inf.add_photo("Home-2308E4家庭中心123")
    #
    # user_web_inf.interface_logout()


