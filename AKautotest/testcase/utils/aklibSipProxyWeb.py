#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import datetime
import time
import os

# 获取根目录
import traceback

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *


def check_sip_proxy_running():
    """
    检查环境下是否有proxy sip.
    """
    http_port = config_get_value_from_ini_file('environment', 'outbound_server_http_port')
    server_ip = config_get_value_from_ini_file('environment', 'outbound_server_ip')
    url = 'http://admin:1234@{}:{}/config/protocol'.format(server_ip, http_port)
    try:
        requests.get(url, timeout=5)
    except:
        return False
    else:
        return True


class SipProxyWeb(object):
    """
    需要安装interactive proxy server软件，并设置好http端口（8880）和sip端口（7070）,要跟config.ini中保持一致
    如果要测试Outbound功能，添加Server Plan为Elastix服务器（厦门这边公共的可以使用192.168.10.28），
    关闭Registration Routing功能，并设置	Forward REGISTERs为前面添加的ServerPlan。
    如果SipProxy要当做普通的SIP Server来使用，用于测试DTMF SIP INFO类型，需要开启Registration Routing功能
    不过，如果一个环境有多台设备同时在跑不同用例需要把服务器当做不同类型使用时会冲突，概率比较小先不考虑兼容，
    后续如有需要可以增加一个文件写入配置项（OutboundServer、SipServer, None），当前是作为什么服务器，如果要改成其他类型，则需要等待
    """

    def __init__(self, browser, url=None):
        self.browser = browser
        if url:
            self.url = url
        else:
            http_port = config_get_value_from_ini_file('environment', 'outbound_server_http_port')
            server_ip = config_get_value_from_ini_file('environment', 'outbound_server_ip')
            self.url = 'http://admin:1234@{}:{}/config/protocol'.format(server_ip, http_port)

    def browser_init(self):
        # self.browser.init()
        self.browser.init_headless()

    def browser_close_and_quit(self):
        self.browser.close_and_quit()

    def visit_url(self):
        for i in range(3):
            try:
                self.browser.visit_url(self.url)
                return True
            except:
                aklog_printf(traceback.format_exc())
                time.sleep(10)
                continue
        return False

    def set_registration_routing(self, option):
        """option: Yes, No"""
        selected_option = self.browser.get_selected_option_by_name('CacheRegistrations')
        if option != selected_option:
            self.browser.select_option_by_name('CacheRegistrations', option)
            self.click_apply()

    def click_apply(self):
        self.browser.click_btn_by_name('Apply')


def sip_proxy_set_as_outbound_server():
    """设置代理服务器作为Outbound服务器"""
    browser = libbrowser()
    sip_proxy = SipProxyWeb(browser)
    sip_proxy.browser_init()
    sip_proxy.visit_url()
    sip_proxy.set_registration_routing('No')
    time.sleep(1)
    sip_proxy.browser_close_and_quit()


def sip_proxy_set_as_sip_server():
    """设置代理服务器作为sip服务器"""
    browser = libbrowser()
    sip_proxy = SipProxyWeb(browser)
    sip_proxy.browser_init()
    sip_proxy.visit_url()
    sip_proxy.set_registration_routing('Yes')
    time.sleep(1)
    sip_proxy.browser_close_and_quit()


if __name__ == '__main__':
    print('测试代码')
    sip_proxy_set_as_sip_server()
