# -*- coding: UTF-8 -*-

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
from testcase.common.aklibAndroidBase import *
from testcase.common.aklibAndroidBaseU2 import *
from testcase.common.aklibbrowser import *
from testcase.common.aklibAndroidAppium import akAppium
from testcase.common.aklibAndroidDevice import *


class IntercomAdapter:
    """
    2024.6.7 Lex
    """
    appium_model_list = ['c315', 'it82', 'c317', 'it83']

    @classmethod
    def get_base(cls, device_name, login=True, web_env_init=True, package=None):
        """
        扩展根据device_info.xml 的 config_module来指定配合机base.
        之后做统一接口名, 来实现配合机不用指定机型.
        """
        device_info = get_device_info_by_device_name(device_name)
        if not device_info:
            aklog_error('设备：{} 未在device_info.xml找到对应device_name：{}信息！！！！'.format(device_name, device_name))
            return False

        device_config = config_parse_device_config(device_info['config_module'], device_name)
        series = device_config.get_series_product_name()
        if 'linux' in series.lower() or 'accessdoor' in series.lower() or 'accesscontrol' in series.lower():
            return cls.get_linux_base(device_name, login, web_env_init, package)
        elif 'android' in series.lower() or 'guard' in series.lower():
            model_name = device_config.get_model_name()
            if model_name.lower() in cls.appium_model_list:
                return cls.get_appium_base(device_name, login, web_env_init, package)
            else:
                return cls.get_u2_base(device_name, login, web_env_init, package)
        else:
            aklog_warn('需要确认设备系列')
            return False

    @classmethod
    def get_u2_base(cls, device_name, login=True, web_env_init=True, package=None):
        """
        使用u2的安卓设备.   androidindoor
        login: 设备是否登录网页, 或者在之后调用start_and_login.
        package:
            None: version_branch.xml指定版本.
                  导入不同分支版本的Base来指定不同设备的分支.
        """
        aklog_info()
        device_info = get_device_info_by_device_name(device_name)
        if not device_info:
            raise Exception('device_info中不存在设备 %s 的信息' % device_name)
        else:
            if not device_info.get('ip'):
                raise Exception('device_info中设备 %s 的IP信息没有填写.' % device_name)
            else:
                aklog_info('初始化设备: {}-{}-{}'.format(device_info.get('device_name'), device_info.get('model'),
                                                         device_info.get('ip')))

        device_config = config_parse_device_config(device_info['config_module'], device_name)
        ui_obj = AndroidBaseU2(device_info, device_config, wait_time=2)
        browser_obj = libbrowser(device_info, device_config, wait_time=2)
        if package:
            device = get_base_module_by_device_config_from_package(device_config, package=package)
            deviceBaseName = str(device).lower()
        else:
            device = get_base_module_by_device_config(device_config)
            deviceBaseName = str(device).lower()
        device.init(ui_obj)

        if 'androidindoor' in deviceBaseName:
            device.browser_init(browser_obj, login=False)
            if login:
                device.browser.start_and_login()
                if web_env_init:
                    device.browser.web_env_init()
                device.TestStart()
        elif 'guardphone' in deviceBaseName:
            # device.browser.browser_init(browser_obj, login=False)
            device.browser_init(browser_obj, login=False)
            if login:
                device.browser.start_and_login()
                if web_env_init:
                    device.browser.web_env_init()
                device.TestStart()
        elif 'androiddoor' in deviceBaseName:
            device.browser_init(browser_obj)
            device.TestStart()
        else:
            aklog_error('获取设备错误!')
            return False
        return device

    @classmethod
    def get_appium_base(cls, device_name, login=True, web_env_init=True, package=None):
        """
        使用appium的安卓设备.   androiddoor(R29V3.2以上可用), androidindoorv6, guardphone
        login: 设备是否登录网页, 或者在之后调用start_and_login.
        package:
            None: version_branch.xml指定版本.
                  导入不同分支版本的Base来指定不同设备的分支.
        """
        aklog_info()
        device_info = get_device_info_by_device_name(device_name)
        if not device_info:
            raise Exception('device_info中不存在设备 %s 的信息' % device_name)
        else:
            if not device_info.get('ip'):
                raise Exception('device_info中设备 %s 的IP信息没有填写.' % device_name)
            else:
                aklog_info('初始化设备: {}-{}-{}'.format(device_info.get('device_name'), device_info.get('model'),
                                                         device_info.get('ip')))

        device_config = config_parse_device_config(device_info['config_module'], device_name)
        browser_obj = libbrowser(device_info, device_config, wait_time=2)
        if package:
            device = get_base_module_by_device_config_from_package(device_config, package=package)
            deviceBaseName = str(device).lower()
        else:
            device = get_base_module_by_device_config(device_config)
            deviceBaseName = str(device).lower()
        if 'androiddoor' in deviceBaseName:
            device_android_door = Android_Door(device_info, device_config)
            ui_obj = AndroidBase(device_android_door, wait_time=2)
            device.init(ui_obj)
            device.browser_init(browser_obj, login=False)
            if login:
                device.browser.start_and_login()
                if web_env_init:
                    device.browser.web_env_init()
                device.TestStart()
        elif 'androidindoorv6' in deviceBaseName or 'androidindoor' in deviceBaseName:
            device_android_indoor = Android_Indoor(device_info, device_config)
            ui_obj = AndroidBase(device_android_indoor, wait_time=2)
            device.init(ui_obj)
            device.browser_init(browser_obj, login=False)
            if login:
                device.browser.start_and_login()
                if web_env_init:
                    device.browser.web_env_init()
                device.TestStart()
        elif 'guardphone' in deviceBaseName:
            device_guard_phone = Android_Guard_Phone(device_info, device_config)
            ui_obj = AndroidBase(device_guard_phone, wait_time=2)
            device.init(ui_obj)
            device.web.web_init(browser_obj, login=False)
            if login:
                device.web.start_and_login()
                device.TestStart()
        else:
            aklog_error('获取设备错误!')
            return False
        return device

    @classmethod
    def get_linux_base(cls, device_name, login=True, web_env_init=True, package=None):
        """
        linuxdoor(包括X912), linuxindoor, accessdoor, accesscontrol
        login: 设备是否登录网页, 或者在之后调用start_and_login.
        package:
            None: version_branch.xml指定版本.
                  导入不同分支版本的Base来指定不同设备的分支.
        """
        aklog_info()
        device_info = get_device_info_by_device_name(device_name)
        if not device_info:
            raise Exception('device_info中不存在设备 %s 的信息' % device_name)
        else:
            if not device_info.get('ip'):
                raise Exception('device_info中设备 %s 的IP信息没有填写.' % device_name)
            else:
                aklog_info('初始化设备: {}-{}-{}'.format(device_info.get('device_name'), device_info.get('model'),
                                                         device_info.get('ip')))

        device_config = config_parse_device_config(device_info['config_module'], device_name)
        browser_obj = libbrowser(device_info, device_config, wait_time=2)
        if package:
            device = get_base_module_by_device_config_from_package(device_config, package=package)
            deviceBaseName = str(device).lower()
        else:
            device = get_base_module_by_device_config(device_config)
            deviceBaseName = str(device).lower()

        if 'linuxdoor' in deviceBaseName:
            device.linux_door_init(browser_obj, login)
            if login:
                device.start_and_login()
                device.web_env_init()
        elif 'linuxindoor' in deviceBaseName:
            # web1.0, web2.0
            device.init_without_start(browser_obj)
            if login:
                device.start_and_login()
                try:
                    device.enter_home()
                except:
                    pass
        elif 'accessdoor' in deviceBaseName:
            device.init(browser_obj)
            if login:
                device.browser.start_and_login()
                if web_env_init:
                    device.browser.web_env_init()
                    device.browser.enter_test_page()
        elif 'accesscontrol' in deviceBaseName:
            device.init(browser_obj)
            if login:
                device.browser.start_and_login()
                if web_env_init:
                    device.browser.web_env_init()
        else:
            aklog_error('获取设备错误!')
            return False
        return device
