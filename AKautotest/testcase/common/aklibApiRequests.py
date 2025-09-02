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
import traceback
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures

urllib3.disable_warnings()  # 移除绕过证书验证告警


class ApiRequests(object):
    """
    Requests接口通用模块
    """

    def __init__(self, device_name='', timeout=60):
        self.device_name = device_name
        retry_strategy = Retry(
            total=3,  # 最大重试次数
            connect=2,  # 当连接失败时，最大的重试次数
            backoff_factor=2,  # 在重试之间等待 2 秒
            # status_forcelist=[502, 503, 504]  # 在遇到 HTTP 状态码为 500、502、503 或 504 时重试
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.requests_session = requests.Session()
        self.requests_session.mount('http://', adapter)
        self.requests_session.mount('https://', adapter)
        self.timeout = timeout

    def get(self, url, verify=True, fail_return_resp=False, timeout=None,
            print_func_log=True, print_trace=True, **kwargs):
        if print_func_log:
            aklog_debug()
        try:
            if not timeout:
                timeout = self.timeout
            response = self.requests_session.get(url, verify=verify, timeout=timeout, **kwargs)
            response.encoding = "utf-8"
            status = response.status_code
            if 200 <= status < 300:
                aklog_debug('Request Get OK, Status_Code:' + str(status))
                return response
            else:
                aklog_debug('Request Get Fail, Status_Code: %s, Resp Text: %s' % (status, response.text))
                if fail_return_resp:
                    return response
                return False
        except Exception as e:
            if print_trace:
                aklog_debug(traceback.format_exc())
            else:
                aklog_debug(e)
            if fail_return_resp:
                raise e
            else:
                return False

    def post(self, url, *args, verify=True, fail_return_resp=False, timeout=None,
             print_func_log=True, print_trace=True, **kwargs):
        if print_func_log:
            aklog_debug()
        try:
            if not timeout:
                timeout = self.timeout
            response = self.requests_session.post(url, *args, verify=verify, timeout=timeout, **kwargs)
            response.encoding = "utf-8"
            status = response.status_code
            if 200 <= status < 300:
                aklog_debug('Request Post OK, Status_Code:' + str(status))
                return response
            else:
                aklog_debug('Request Post Fail, Status_Code: %s, Resp Text: %s' % (status, response.text))
                if fail_return_resp:
                    return response
                else:
                    return False
        except Exception as e:
            if print_trace:
                aklog_debug(traceback.format_exc())
            else:
                aklog_debug(e)
            if fail_return_resp:
                raise e
            else:
                return False

    def patch(self, url, *args, verify=True, fail_return_resp=False, timeout=None,
              print_func_log=True, print_trace=True, **kwargs):
        if print_func_log:
            aklog_debug()
        try:
            if not timeout:
                timeout = self.timeout
            response = self.requests_session.patch(url, *args, verify=verify, timeout=timeout, **kwargs)
            response.encoding = "utf-8"
            status = response.status_code
            if 200 <= status < 300:
                aklog_debug('Request Patch OK, Status_Code:' + str(status))
                return response
            else:
                aklog_debug('Request Patch Fail, Status_Code: %s, Resp Text: %s' % (status, response.text))
                if fail_return_resp:
                    return response
                else:
                    return False
        except Exception as e:
            if print_trace:
                aklog_debug(traceback.format_exc())
            else:
                aklog_debug(e)
            if fail_return_resp:
                raise e
            else:
                return False

    def put(self, url, *args, verify=True, fail_return_resp=False, timeout=None,
            print_func_log=True, print_trace=True, **kwargs):
        if print_func_log:
            aklog_debug()
        try:
            if not timeout:
                timeout = self.timeout
            response = self.requests_session.put(url, *args, verify=verify, timeout=timeout, **kwargs)
            response.encoding = "utf-8"
            status = response.status_code
            if 200 <= status < 300:
                aklog_debug('Request Put OK, Status_Code:' + str(status))
                return response
            else:
                aklog_debug('Request Put Fail, Status_Code: %s, Resp Text: %s' % (status, response.text))
                if fail_return_resp:
                    return response
                else:
                    return False
        except Exception as e:
            if print_trace:
                aklog_debug(traceback.format_exc())
            else:
                aklog_debug(e)
            if fail_return_resp:
                raise e
            else:
                return False

    def delete(self, url, verify=True, fail_return_resp=False, timeout=None,
               print_func_log=True, print_trace=True, **kwargs):
        if print_func_log:
            aklog_debug()
        try:
            if not timeout:
                timeout = self.timeout
            response = self.requests_session.delete(url, verify=verify, timeout=timeout, **kwargs)
            response.encoding = "utf-8"
            status = response.status_code
            if 200 <= status < 300:
                aklog_debug('Request Delete OK, Status_Code:' + str(status))
                return response
            elif 300 <= status < 400:
                aklog_debug('Request Delete Move Found, Status_Code:' + str(status))
                return response
            else:
                aklog_debug('Request Delete Fail, Status_Code: %s, Resp Text: %s' % (status, response.text))
                if fail_return_resp:
                    return response
                else:
                    return False
        except Exception as e:
            if print_trace:
                aklog_debug(traceback.format_exc())
            else:
                aklog_debug(e)
            if fail_return_resp:
                raise e
            else:
                return False

    def concurrent_get(self, urls_with_params, max_workers=100):
        """并发请求"""

        def send_get(url_with_param):
            try:
                url, kwargs = url_with_param
                response = self.requests_session.get(url, timeout=self.timeout, **kwargs)
                status = response.status_code
                aklog_printf('url: %s, kwargs: %r, status_code: %s' % (url, kwargs, status))
                return response.status_code
            except:
                aklog_debug(traceback.format_exc())
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(send_get, urls_with_params))
        return results

    def concurrent_post(self, urls_with_params, max_workers=100):
        """并发请求"""

        def send_post(url_with_param):
            try:
                url, args, kwargs = url_with_param
                response = self.requests_session.post(url, *args, timeout=self.timeout, **kwargs)
                status = response.status_code
                aklog_printf('url: %s, args: %r, kwargs: %r, status_code: %s' % (url, args, kwargs, status))
                return status
            except:
                aklog_debug(traceback.format_exc())
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(send_post, urls_with_params))
        return results

    def put_device_name(self, device_name):
        self.device_name = device_name
