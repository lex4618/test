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
import requests


class MonitorSwitchWeb:
    """
    web网管（监控镜像抓包）交换机（型号：TPLink TL-SG2008D）网页操作
    主要用于控制端口启用和禁用，以此来模拟设备断网情况
    """

    def __init__(self, url=None, browser=None):
        if browser:
            self.browser = browser
        else:
            self.browser = libbrowser()
        if url:
            self.url = url
        else:
            monitor_switch_ip = config_get_value_from_ini_file('environment', 'monitor_switch_ip')
            self.url = 'http://{}'.format(monitor_switch_ip)
        self.username = 'admin'
        self.password = 'admin'

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

    def login(self):
        aklog_printf()
        self.visit_url()
        self.browser.input_edit_by_id('username', self.username)
        self.browser.input_edit_by_id('password', self.password)
        self.browser.click_btn_by_id('logon')
        time.sleep(5)

    def menu_select(self, menu_id, submenu_id):
        """菜单选择"""
        self.browser.switch_iframe_to_default()
        self.browser.switch_iframe_by_name('bottomLeftFrame')
        if not self.browser.is_exist_and_visible_ele_by_id(submenu_id):
            self.browser.click_btn_by_id(menu_id, 0.5)
        self.browser.click_btn_by_id(submenu_id, 1)
        self.browser.switch_iframe_to_default()
        self.browser.switch_iframe_by_name('mainFrame')

    def enter_switching_port_setting_page(self):
        aklog_printf()
        self.menu_select('Switching', 'PortSettingRpm')

    def set_port_control(self, port, state, sec=3):
        """
        设置端口控制
        port: 1-8
        status: 0 or 1，禁用或启用
        """
        aklog_printf()
        self.enter_switching_port_setting_page()
        self.browser.select_option_value_by_id('portSel', str(port), 1)
        self.browser.select_option_value_by_name('state', str(state), 1)
        self.browser.click_btn_by_name('apply')
        time.sleep(sec)


def set_monitor_switch_port_disable_enable(switch_web, port, duration=5, sec=5):
    """
    设置监控交换机端口禁用，等待一段时间再启用
    需要先实例：switch_web = MonitorSwitchWeb()
    port: 1-8，端口号
    duration：禁用端口断网等待时间
    """
    aklog_printf()
    switch_web.browser_init()
    switch_web.login()
    switch_web.set_port_control(port, 0)
    aklog_printf('交换机端口禁用，断网等待%s秒...' % duration)
    time.sleep(duration)
    aklog_printf('重新启用交换机端口')
    switch_web.set_port_control(port, 1)
    switch_web.browser_close_and_quit()
    aklog_printf('交换机端口启用，等待%s秒重连...' % sec)
    time.sleep(sec)


def set_monitor_switch_port_disable(switch_web, port, sec=5):
    """
    设置监控交换机端口禁用，等待一段时间再启用
    需要先实例：switch_web = MonitorSwitchWeb()
    port: 1-8，端口号
    sec：禁用端口断网等待时间
    """
    aklog_printf()
    switch_web.browser_init()
    switch_web.login()
    switch_web.set_port_control(port, 0)
    aklog_printf('交换机端口禁用，断网等待%s秒...' % sec)
    time.sleep(sec)


def set_monitor_switch_port_enable(switch_web, port, sec=5, browser_quit=True):
    """
    设置监控交换机端口禁用，等待一段时间再启用
    需要先实例：switch_web = MonitorSwitchWeb()
    port: 1-8，端口号
    duration：禁用端口断网等待时间
    """
    aklog_printf()
    switch_web.set_port_control(port, 1)
    if browser_quit:
        switch_web.browser_close_and_quit()
    aklog_printf('交换机端口启用，等待%s秒重连...' % sec)
    time.sleep(sec)


class mercury:
    def __init__(self, ip, username='admin', password='admin'):
        self.ip = ip
        self.username = username
        self.password = password
        self.s = requests.Session()
        try:
            r = self.s.post(f'http://{self.ip}/logon.cgi', timeout=5,
                            data={'username': self.username, 'password': self.password, 'logon': '登录'})
        except:
            print(f'访问Mercury 交换机: {self.ip} 失败!!!')
            raise RuntimeError

    def close_port(self, portNum=1):
        try:
            self.s.get(
                f'http://{self.ip}/port_setting.cgi?portid={portNum}&state=0&speed=1&flowcontrol=0&apply=%E5%BA%94%E7%94%A8',
                timeout=5)
        except:
            print('关闭Mercury交换机端口{}失败'.format(portNum))

    def open_port(self, portNum=1):
        try:
            self.s.get(
                f'http://{self.ip}/port_setting.cgi?portid={portNum}&state=1&speed=1&flowcontrol=0&apply=%E5%BA%94%E7%94%A8')
        except:
            print('开启Mercury交换机端口{}失败'.format(portNum))


class MonitorSwitchInf:
    """
    web网管（监控镜像抓包）交换机（型号：TPLink TL-SG2008D）web接口操作
    主要用于控制端口启用和禁用，以此来模拟设备断网情况
    """

    def __init__(self, ip, username='admin', password='admin'):
        self.ip = ip
        self.username = username
        self.password = password
        self.s: Optional[requests.Session] = None

    def login(self):
        try:
            url = f'http://{self.ip}/logon.cgi'
            data = {'username': self.username,
                    'password': self.password,
                    'isIe': False,
                    'logon': '登录'}
            self.s = requests.Session()
            resp = self.s.post(url, data=data, timeout=5)
            if resp.status_code == 200:
                return True
            aklog_warn(f'访问TPLink TL-SG2008D 交换机: {self.ip} 失败!!!')
            aklog_debug(resp.text)
        except Exception as e:
            aklog_warn(f'访问TPLink TL-SG2008D 交换机: {self.ip} 失败!!!')
            raise e

    def close_port(self, portNum=1):
        try:
            self.s.get(
                f'http://{self.ip}/port_setting.cgi?portid={portNum}&state=0&speed=1&flowcontrol=0'
                f'&apply=%E5%BA%94%E7%94%A8',
                timeout=5)
        except:
            print('关闭Mercury交换机端口{}失败'.format(portNum))

    def open_port(self, portNum=1):
        try:
            self.s.get(
                f'http://{self.ip}/port_setting.cgi?portid={portNum}&state=1&speed=1&flowcontrol=0'
                f'&apply=%E5%BA%94%E7%94%A8')
        except:
            print('开启Mercury交换机端口{}失败'.format(portNum))


def close_mercury_port(ip='192.168.0.1', username='admin', password='admin', port=1):
    print('closing Mercury Switch: {}  Port: {}'.format(ip, port))
    try:
        a = mercury(ip, username, password)
        a.close_port(port)
    except:
        return False
    else:
        time.sleep(5)
        return True


def open_mercury_port(ip='192.168.0.1', username='admin', password='admin', port=1):
    print('opening Mercury Switch: {}  Port: {}'.format(ip, port))
    try:
        a = mercury(ip, username, password)
        a.open_port(port)
    except:
        return False
    else:
        time.sleep(5)
        return True


if __name__ == '__main__':
    print('测试代码')
    switch_web = MonitorSwitchInf('192.168.88.15')
    switch_web.login()
