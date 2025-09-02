# -*- coding: utf-8 -*-
import re
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
from libconfig.COMMON.libconfig_NORMAL import config_NORMAL
from appium.webdriver.webdriver import WebDriver as AppiumWebDriver
from appium.options.android import UiAutomator2Options
from typing import Optional
import traceback


class AndroidConnect(object):

    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        self._isReady = False
        self._deviceCtrl: Optional[AppiumWebDriver] = None
        self._device_info: dict = device_info
        self._device_config: Optional[config_NORMAL] = device_config
        # 初始化不在device_info中指定本地端口，而是自动分配，localPort为奇数，bootstrap_port 加1为偶数
        if appium_port:
            # 有些安卓机型需要在不同应用切换（正常应用和工程模式），会重新实例化这个Device，如果要使用原来的端口就需要从base基类那边调用时把端口再重新传入进来
            self._localPort = appium_port
        else:
            self._localPort = config_get_appium_port()
        self._bootstrap_port = int(self._localPort) + 1
        self._appium_command = device_info.get('appium_command', self._device_config.appium_command)
        self._desiredCaps = dict()
        platformVersion = device_info.get('platformversion', self._device_config.platform_version)
        device_name = device_info.get('device_name')
        # 获取deviceid，如果device_info中缺少deviceid，将使用device_ip来组合
        self._device_ip = self._device_info.get('ip')
        self._device_id = self._device_info.get('deviceid')
        if not self._device_id and self._device_ip:
            self._device_id = '%s:5654' % self._device_ip
            self._device_info['deviceid'] = self._device_id
        elif self._device_ip and self._device_ip not in self._device_id:
            _, port = self._device_id.split(':', 1)
            self._device_id = f"{self._device_ip}:{port}"
            self._device_info['deviceid'] = self._device_id
        if not self._device_id:
            raise ValueError(f'device_info中, 设备 {device_name} 缺少deviceid')

        self._desiredCaps['platformVersion'] = str(platformVersion)
        self._desiredCaps['deviceName'] = device_name
        self._desiredCaps['udid'] = self._device_id
        self._desiredCaps['platformName'] = 'Android'
        self._desiredCaps['newCommandTimeout'] = 1800  # 30min
        self._desiredCaps['adbExecTimeout'] = 120000  # 120s
        self._desiredCaps['unicodeKeyboard'] = True
        self._desiredCaps['resetKeyboard'] = True
        self._desiredCaps['noReset'] = True
        if uiautomator2_system_port:
            # 有些安卓机型需要在不同应用切换（正常应用和工程模式），会重新实例化这个Device，如果要使用原来的端口就需要从base基类那边调用时把端口再重新传入进来
            self._desiredCaps['systemPort'] = uiautomator2_system_port
        else:
            self._desiredCaps['systemPort'] = config_get_uiautomator2_system_port()

        # Appium2.x+版本，desiredCaps改为了Options
        self.options = UiAutomator2Options()
        self.options.load_capabilities(self._desiredCaps)

        aklog_debug('AndroidConnect.__init__, local_port: %s, systemPort: %s, BootstrapPort: %s'
                    % (self._localPort, self._desiredCaps.get('systemPort'), self._bootstrap_port))

    def __del__(self):
        self._desiredCaps.clear()

    def __str__(self):
        return "localPort is " + self._localPort + " and Caps is " + str(self._desiredCaps)

    def Connect(self, keepAlive=True):
        connect_url = f'http://127.0.0.1:{self._localPort}/wd/hub'
        aklog_debug('Connect, url: %s, udid: %s' % (connect_url, self._desiredCaps['udid']))
        try:
            try:
                self._deviceCtrl = AppiumWebDriver(
                    connect_url, options=self.options, keep_alive=keepAlive)
            except:
                # python 3.12.0 + Appium-Python-Client  5.0.0
                self._deviceCtrl = AppiumWebDriver(connect_url, options=self.options)
        except:
            self._isReady = False
            aklog_debug(" connect failed!" + str(traceback.format_exc()))
        else:
            self._isReady = True
            aklog_debug(" connect success!")

    def Disconnect(self):
        aklog_debug('Disconnect')
        try:
            if self._deviceCtrl is not None:
                self._deviceCtrl.quit()
                aklog_debug(" disconnected!")
        except:
            aklog_debug('Disconnect failed')
            print(traceback.format_exc())
        finally:
            self._deviceCtrl = None
            self._isReady = False

    def IsReady(self):
        return self._isReady

    def GetDeviceName(self):
        if 'deviceName' not in self._desiredCaps:
            return 'unknown'
        return self._desiredCaps['deviceName']

    def GetPlatformName(self):
        return self._desiredCaps['platformName']

    def GetAutomationName(self):
        return self._desiredCaps['automationName']

    def GetLocalPort(self):
        return str(self._localPort)

    def GetBootstrapPort(self):
        return str(self._bootstrap_port)

    def get_uiautomator2_system_port(self):
        return str(self._desiredCaps['systemPort'])

    def GetAppiumCommand(self):
        return self._appium_command

    def GetDeviceId(self):
        return self._desiredCaps['udid']

    def GetDeviceAddr(self):
        if 'ip' not in self._device_info:
            return 'unknown'
        return self._device_info['ip']

    def GetDeviceCtrl(self) -> Optional[AppiumWebDriver]:
        return self._deviceCtrl

    def GetPlatformVersion(self):
        return self._desiredCaps['platformVersion']

    def GetDeviceInfo(self):
        return self._device_info

    def get_device_config(self):
        return self._device_config

    # R2X密码与其他设备不一致
    def GetDeviceSSHPassword(self):
        if 'SSHPassword' not in self._device_info:
            return 'nopasswd'
        return self._device_info['SSHPassword']
