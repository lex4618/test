# -*- coding: UTF-8 -*-

import sys
import os
import traceback

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *
# import time
import requests
import json
from requests.auth import HTTPDigestAuth, HTTPBasicAuth


# from urllib3.exceptions import ReadTimeoutError


class AkRequests(object):

    def __init__(self, url=None, user_name='admin', password='admin', time_out=20, user_agent=None):
        # requests.DEFAULT_RETRIES = 5
        self.session = requests.session()
        self.url = url
        self.user_name = user_name
        self.password = password
        self.auth_header = None
        self.headers = {}
        if user_agent:
            self.headers["User-Agent"] = user_agent
        else:
            self.headers["User-Agent"] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
                                         '(KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'
        self.time_out = time_out

    def get_auth_header(self, auth_method):
        if auth_method == 'Basic':
            auth_header = HTTPBasicAuth(self.user_name, self.password)
        elif auth_method == 'Digest':
            auth_header = HTTPDigestAuth(self.user_name, self.password)
        else:
            auth_header = None
        return auth_header

    def send_post(self, post_data, returncontent=False):
        """json格式发送数据"""
        aklog_printf()
        for i in range(2):
            try:
                self.headers['Content-Type'] = 'application/json'
                post_data_json = json.dumps(post_data)
                if 'https' in self.url:
                    resp = self.session.post(url=self.url, data=post_data_json, auth=self.auth_header,
                                             headers=self.headers,
                                             timeout=self.time_out,
                                             verify=False)
                else:
                    resp = self.session.post(url=self.url, data=post_data_json, auth=self.auth_header,
                                             headers=self.headers,
                                             timeout=self.time_out)
                if resp.status_code == 200:
                    if returncontent:
                        return resp.content
                    resp_text = resp.text
                    aklog_printf('resp_text: %s' % resp_text)
                    if resp_text and resp_text.strip():
                        resp_data = json_loads_2_dict(resp_text)
                        aklog_printf('resp_data: %r' % resp_data)
                        return resp_data
                    else:
                        return ''
                elif i == 0 and resp.reason == 'Unauthorized':
                    resp_header = resp.headers
                    auth_method_end_pos = resp_header['WWW-Authenticate'].find(' realm')
                    auth_method = resp_header['WWW-Authenticate'][0:auth_method_end_pos]
                    self.auth_header = self.get_auth_header(auth_method)
                    continue
                else:
                    aklog_error('send_post failed, status_code: %s' % resp.status_code)
                    return None
            except:
                if 'requests.exceptions.ReadTimeout' in traceback.format_exc():
                    aklog_error('post请求: 超时!!!')
                    aklog_debug(traceback.format_exc())
                    continue
                elif 'ssl.SSLCertVerificationError' in traceback.format_exc() and self.url.startswith('http://'):
                    self.url = self.url.replace('http://', 'https://')
                    continue
                else:
                    aklog_printf('遇到未知异常：%s' % traceback.format_exc())
                    self.session = requests.session()
                    return None

    def send_get(self, url=None, send_auth=True, user=None, pwd=None, print_resp=True, **kwargs):
        aklog_printf()
        for i in range(2):
            try:
                if not url:
                    url = self.url
                if '@' in url:
                    user_info = str_get_content_between_two_characters(url, '://', '@')
                    self.user_name = user_info.split(':')[0]
                    self.password = user_info.split(':')[1]
                if 'https' in url:
                    resp = self.session.get(
                        url=url, auth=self.auth_header, headers=self.headers, timeout=self.time_out, verify=False,
                        **kwargs)
                else:
                    resp = self.session.get(
                        url=url, auth=self.auth_header, headers=self.headers, timeout=self.time_out, **kwargs)
                if resp.status_code == 200:
                    resp_text = resp.text
                    # aklog_printf('resp_text: %s' % resp_text)
                    if resp_text and resp_text.strip():
                        resp_data = json_loads_2_dict(resp_text)
                        if print_resp:
                            aklog_printf('resp_data: %r' % resp_data)
                        return resp_data
                    else:
                        return ''
                elif i == 0 and send_auth and resp.reason == 'Unauthorized':
                    resp_header = resp.headers
                    auth_method_end_pos = resp_header['WWW-Authenticate'].find(' realm')
                    auth_method = resp_header['WWW-Authenticate'][0:auth_method_end_pos]
                    if user is not None:
                        self.user_name = user
                    if pwd is not None:
                        self.password = pwd
                    self.auth_header = self.get_auth_header(auth_method)
                    continue
                else:
                    aklog_error('send_get failed, status_code: %s' % resp.status_code)
                    return None
            except:
                if 'requests.exceptions.ReadTimeout' in traceback.format_exc():
                    aklog_error(f'get请求: {url} 超时!!!')
                    print(traceback.format_exc())
                    continue
                elif 'ssl.SSLCertVerificationError' in traceback.format_exc() and url.startswith('http://'):
                    if self.url:
                        self.url = self.url.replace('http://', 'https://')
                    url = url.replace('http://', 'https://')
                    continue
                else:
                    aklog_printf('遇到未知异常：%s' % traceback.format_exc())
                    return None

    def send_post_with_url(self, url, post_data, returncontent=False):
        """json格式发送数据"""
        aklog_printf()
        for i in range(2):
            try:
                self.headers['Content-Type'] = 'application/json'
                post_data_json = json.dumps(post_data)
                if 'https' in url:
                    resp = self.session.post(url=url, data=post_data_json, auth=self.auth_header,
                                             headers=self.headers,
                                             timeout=self.time_out,
                                             verify=False)
                else:
                    resp = self.session.post(url=url, data=post_data_json, auth=self.auth_header,
                                             headers=self.headers,
                                             timeout=self.time_out)
                if resp.status_code == 200:
                    if returncontent:
                        return resp.content
                    resp_text = resp.text
                    aklog_printf('resp_text: %s' % resp_text)
                    if resp_text and resp_text.strip():
                        resp_data = json_loads_2_dict(resp_text)
                        aklog_printf('resp_data: %r' % resp_data)
                        return resp_data
                    else:
                        return ''
                elif i == 0 and resp.reason == 'Unauthorized':
                    resp_header = resp.headers
                    auth_method_end_pos = resp_header['WWW-Authenticate'].find(' realm')
                    auth_method = resp_header['WWW-Authenticate'][0:auth_method_end_pos]
                    self.auth_header = self.get_auth_header(auth_method)
                    continue
                else:
                    aklog_error('send_post failed, status_code: %s' % resp.status_code)
                    return None
            except:
                if 'requests.exceptions.ReadTimeout' in traceback.format_exc():
                    aklog_error('post请求: 超时!!!')
                    print('~~~~~~~~~~')
                    print(post_data)
                    print('~~~~~~~~~~')
                    print(traceback.format_exc())
                    continue
                elif 'ssl.SSLCertVerificationError' in traceback.format_exc() and url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                    continue
                else:
                    aklog_printf('遇到未知异常：%s' % traceback.format_exc())
                    self.session = requests.session()
                    return None

    @staticmethod
    def download_file(local_file, url, **kwargs):
        aklog_printf('download_file, url: %s' % url)
        r = requests.get(url, **kwargs)
        with open(local_file, "wb") as f:
            f.write(r.content)

    def close(self):
        self.session.close()


class AkHTTPAPI(object):
    def __init__(self, ip, user_name='admin', password='admin', auth='None', prefix='http'):
        """
        用于 测试HTTP API
        参数: auth: None, Basic, Digest
        eg:  以Basic鉴权方式测试各种api
            b = AkHTTPAPI('192.168.1.97', 'admin', 'admin', 'Basic')
            b.send_get('/api/firmware/status')
            b.send_get('/api/system/info')
        """
        self.prefix = '{}://{}'.format(prefix, ip)
        self.session = requests.session()
        self.user_name = user_name
        self.password = password
        self.auth_header = self.get_auth_header(auth)
        self.timeout = 5
        self.headers = {}

    def get_auth_header(self, auth_method):
        """HTTP API 的鉴权方式"""
        if auth_method == 'Basic':
            auth_header = HTTPBasicAuth(self.user_name, self.password)
        elif auth_method == 'Digest':
            auth_header = HTTPDigestAuth(self.user_name, self.password)
        else:
            auth_header = None
        return auth_header

    def send_get(self, url):
        aklog_printf("send_get, url: %s" % url)
        try:
            url = self.prefix + url
            resp = self.session.get(url=url, auth=self.auth_header, headers=self.headers, timeout=self.timeout,
                                    verify=False)
            print(resp.text)
            if '403 Forbidden' in resp.text:
                return '403'
            elif '401 - Unauthorized' in resp.text:
                return '401'
            elif '401 Unauthorized' in resp.text:
                return '401'
            elif '500 Internal Server Error' in resp.text:
                return '500'
            else:
                return resp.json()
        except:
            aklog_printf('遇到未知异常：%s' % traceback.format_exc())
            return False

    def send_post(self, url, post_data):
        """json格式发送数据"""
        self.headers['Content-Type'] = 'application/json'
        post_data_json = json.dumps(post_data)
        try:
            url = self.prefix + url
            resp = self.session.post(url=url, data=post_data_json, auth=self.auth_header, headers=self.headers,
                                     timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
            else:
                return False
        except:
            return False


def check_auth_mode(ip, user_name='admin', password='admin', auth_mode='None'):
    """
    ret = check_auth_mode('192.168.1.97', auth_mode='Basic')
    # 检测设备配置成 Basic鉴权是否有效.
    """

    def get_auth_header(auth_method):
        """HTTP API 的鉴权方式"""
        if auth_method == 'Basic':
            aft_auth = HTTPBasicAuth(user_name, password)
        elif auth_method == 'Digest':
            aft_auth = HTTPDigestAuth(user_name, password)
        else:
            aft_auth = None
        return aft_auth

    auth_header = get_auth_header(auth_mode)
    try:
        if requests.session().get('http://%s/api/system/info' % ip, auth=auth_header).status_code == 401:
            return False
        else:
            return True
    except:
        return False


if __name__ == '__main__':
    http_api_key_s = {"target": 'autotest', "action": 'key', "data": {"keycode": 'S'}}
    http_api_key_c = {"target": 'autotest', "action": 'key', "data": {"keycode": 'C'}}

    http_api_ldr = {"target": 'autotest', "action": 'event', "data": {"type": "21", "code": "0", "value": "0"}}
    http_api_ir = {"target": 'autotest', "action": 'event', "data": {"type": "21", "code": "1", "value": "1"}}
    http_api_3aix = {"target": 'autotest', "action": 'event', "data": {"type": "21", "code": "2", "value": "1"}}
    http_api_input = {"target": 'autotest', "action": 'event', "data": {"type": "21", "code": "28", "value": "0"}}

    http_api_ic_card = {"target": 'autotest', "action": 'swipe_card', "data": {"type": "0x7000", "value": "12345678"}}
    http_api_id_card = {"target": 'autotest', "action": 'swipe_card', "data": {"type": "0x8000", "value": "12345678"}}
    http_api_wiegand26_card = {"target": 'autotest', "action": 'swipe_card',
                               "data": {"type": "0x9000", "value": "123456"}}
    http_api_wiegand34_card = {"target": 'autotest', "action": 'swipe_card',
                               "data": {"type": "0x9000", "value": "65432100"}}
    http_api_wiegand58_card = {"target": 'autotest', "action": 'swipe_card',
                               "data": {"type": "0x9000", "value": "9876543210000000"}}
    http_api_get_relay = {"target": 'relay', "action": 'status', "data": ""}

    data = {'Product_name': 'R29', 'Total_testcases': 4, 'Pass_testcases': 4, 'Pass_rate': '100.0%',
            'Take_time': '10:15:50', 'Test_date': '20200820', 'Product_version': '29.30.2.17'}

    ak_requests = AkRequests('http://192.168.88.189/api/')
    ak_requests.send_post(http_api_input)
    ak_requests.close()
