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
import time


class MyPBXServerWeb:
    """
    MyPBX服务器网页配置，主要配置TLS开关
    """

    def __init__(self, url, browser=None):
        if browser:
            self.browser = browser
        else:
            self.browser = libbrowser()
        if url:
            self.url = url
        self.username = 'admin'
        self.password = 'password'

    def browser_init(self):
        # self.browser.init()
        self.browser.init_headless()

    def browser_close_and_quit(self):
        self.browser.switch_iframe_to_default()
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

    def login(self):
        aklog_printf()
        self.visit_url()
        self.browser.input_edit_by_id('username', self.username)
        self.browser.input_edit_by_id('secret', self.password)
        self.browser.click_btn_by_id('login_button')
        time.sleep(2)
        self.browser.alert_confirm_accept(5)
        time.sleep(2)

    def menu_select(self, menu_id):
        """菜单选择"""
        self.browser.switch_iframe_to_default()
        self.browser.click_btn_by_id(menu_id, 2)
        self.browser.switch_iframe_by_name('mainscreen')

    def enter_sip_setting_page(self):
        aklog_printf()
        # self.menu_select('sipsetting')
        self.browser.switch_iframe_to_default()
        self.browser.click_btn_by_xpath('//a[text()="SIP Settings"]')
        self.browser.switch_iframe_by_name('mainscreen')

    def set_tls_config(self, verify_server='yes', verify_client='yes'):
        """
        设置TLS
        verify_server: yes no
        """
        self.enter_sip_setting_page()
        time.sleep(1)
        self.browser.select_option_value_by_id('tlsdontverifyserver', verify_server)
        self.browser.select_option_value_by_id('tlsverifyclient', verify_client)
        self.browser.click_btn_by_class_name('guiButtonEdit')
        time.sleep(5)
        self.browser.switch_iframe_to_default()
        self.browser.click_btn_by_id('applyChanges_Button')
        time.sleep(2)


def set_my_pbx_server_tls(verify_server='yes', verify_client='yes', pbx_url=None):
    """设置MYPBX服务器TLS配置项"""
    aklog_printf()
    if pbx_url:
        pbx_web = MyPBXServerWeb(url=pbx_url)
    else:
        pbx_web = MyPBXServerWeb(url='http://192.168.10.16')
    pbx_web.browser_init()
    pbx_web.login()
    time.sleep(3)
    pbx_web.set_tls_config(verify_server, verify_client)
    pbx_web.browser_close_and_quit()


if __name__ == '__main__':
    print('测试代码')
    set_my_pbx_server_tls('yes', 'yes')
