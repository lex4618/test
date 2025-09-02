#!/usr/bin/env python3
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
from testcase.common.aklibAndroidConnect import AndroidConnect


class SmartPlus_Android(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'uiautomator2'
        self._desiredCaps['language'] = 'en'
        self._desiredCaps['locale'] = 'US'
        self._desiredCaps['uiautomator2ServerLaunchTimeout'] = 60000  # 60s
        self._desiredCaps['uiautomator2ServerInstallTimeout'] = 60000  # 60s
        self._desiredCaps['skipServerInstallation'] = True  # False为安装
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.akuvox.mobile.smartplus'
        self._desiredCaps['appActivity'] = 'com.akuvox.mobile.module.main.view.SplashActivity'


class openAPI_Android(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'uiautomator2'
        self._desiredCaps['language'] = 'en'
        self._desiredCaps['locale'] = 'US'
        self._desiredCaps['skipServerInstallation'] = True
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.akuvox.mobile.aktalk'
        self._desiredCaps['appActivity'] = 'com.akuvox.mobile.smartplussdk.view.HomeActivity'


class VFone_Android(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'uiautomator2'
        self._desiredCaps['language'] = 'en'
        self._desiredCaps['locale'] = 'US'
        self._desiredCaps['skipServerInstallation'] = True
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.akuvox.mobile.VFone'
        self._desiredCaps['appActivity'] = 'com.akuvox.mobile.module.main.view.activity.SplashActivity'


class Android_Indoor(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'uiautomator2'
        self._desiredCaps['uiautomator2ServerLaunchTimeout'] = 60000  # 60s
        self._desiredCaps['uiautomator2ServerInstallTimeout'] = 60000  # 60s
        # self._desiredCaps['adbExecTimeout'] = 60000     # 60s
        self._desiredCaps['skipServerInstallation'] = False
        # 目标活动
        self._desiredCaps['autoLaunch'] = False
        self._desiredCaps['appPackage'] = 'com.akuvox.phone'
        self._desiredCaps['appActivity'] = '.indoor.ui.activity.IdleActivity'


class Android_Indoor_X933(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'uiautomator2'
        self._desiredCaps['uiautomator2ServerLaunchTimeout'] = 60000  # 60s
        self._desiredCaps['uiautomator2ServerInstallTimeout'] = 60000  # 60s
        # self._desiredCaps['adbExecTimeout'] = 60000     # 60s
        # self._desiredCaps['skipServerInstallation'] = True
        # 目标活动
        self._desiredCaps['autoLaunch'] = False
        self._desiredCaps['appPackage'] = 'com.akuvox.phone'
        self._desiredCaps['appActivity'] = '.idle_ui.activity.IdleActivity'


class Android_Hyper_Panel(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'uiautomator2'
        self._desiredCaps['uiautomator2ServerLaunchTimeout'] = 60000  # 60s
        self._desiredCaps['uiautomator2ServerInstallTimeout'] = 60000  # 60s
        # self._desiredCaps['adbExecTimeout'] = 60000     # 60s
        # self._desiredCaps['skipServerInstallation'] = True
        # 目标活动
        self._desiredCaps['autoLaunch'] = False
        self._desiredCaps['appPackage'] = 'com.akubela.panel'
        self._desiredCaps['appActivity'] = '.idle_ui.activity.IdleActivity'
        # self._desiredCaps['appActivity'] = '.setting_ui.activity.AdvanceSettingActivity'


class Android_Indoor_X933_Factory(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'uiautomator2'
        self._desiredCaps['uiautomator2ServerLaunchTimeout'] = 60000  # 60s
        self._desiredCaps['uiautomator2ServerInstallTimeout'] = 60000  # 60s
        # self._desiredCaps['adbExecTimeout'] = 60000     # 60s
        # self._desiredCaps['skipServerInstallation'] = True
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.akuvox.factorytest'
        self._desiredCaps['appActivity'] = '.ui.activity.MainActivity'


class Android_Guard_Phone(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        if 'automationName' in device_info:
            self._desiredCaps['automationName'] = device_info['automationName']
        else:
            self._desiredCaps['automationName'] = 'Appium'
        self._desiredCaps['unicodeKeyboard'] = False
        self._desiredCaps['resetKeyboard'] = False
        self._desiredCaps['adbExecTimeout'] = 60000  # 60s
        self._desiredCaps['skipServerInstallation'] = False
        # 目标活动,该项目在49工程模式的时候要开
        if 'autoLaunch' in device_info:
            if device_info['autoLaunch'] == 'False':
                autoLaunch = False
            else:
                autoLaunch = True
            self._desiredCaps['autoLaunch'] = autoLaunch
        self._desiredCaps['appPackage'] = 'com.akuvox.phone'
        self._desiredCaps['appActivity'] = 'com.akuvox.guardphone.ui.activity.IdleActivity'


class Android_R48_Phone(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'Appium'
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.android.launcher3'
        self._desiredCaps['appActivity'] = '.Launcher'


class Android_R49_Phone(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'Appium'
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.android.launcher3'
        self._desiredCaps['appActivity'] = '.Launcher'


class Android_R48_Factory(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'Appium'
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.akuvox.factorytest'
        self._desiredCaps['appActivity'] = '.ui.activity.DialogActivity'


class Android_R47P_Phone(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'Appium'
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.akuvox.phone'
        self._desiredCaps['appActivity'] = '.ui.activity.HomeActivity'


class Android_R73_Phone(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'Appium'
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.akuvox.phone'
        self._desiredCaps['appActivity'] = '.ui.activity.HomeActivity'


class Android_R73_Factory(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'Appium'
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.akuvox.factorytest'
        self._desiredCaps['appActivity'] = '.ui.activity.DialogActivity'


class Android_Door(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'uiautomator2'
        self._desiredCaps['uiautomator2ServerLaunchTimeout'] = 60000  # 60s
        self._desiredCaps['uiautomator2ServerInstallTimeout'] = 60000  # 60s
        self._desiredCaps['adbExecTimeout'] = 60000  # 60s
        self._desiredCaps['autoLaunch'] = False
        # self._desiredCaps['noReset'] = True
        # self._desiredCaps['fullReset'] = False
        # self._desiredCaps['skipServerInstallation'] = True
        # self._desiredCaps['appWaitDuration'] = 60000
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.akuvox.phone'
        self._desiredCaps['appActivity'] = '.doorphone.ui.activity.StandbyActivity'
        # self._desiredCaps['appPackage'] = 'com.teslacoilsw.launcher'
        # self._desiredCaps['appActivity'] = 'com.teslacoilsw.launcher.NovaLauncher'


class Android_BelaHome(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'uiautomator2'
        self._desiredCaps['language'] = 'en'
        self._desiredCaps['locale'] = 'US'
        self._desiredCaps['uiautomator2ServerLaunchTimeout'] = 60000  # 60s
        self._desiredCaps['uiautomator2ServerInstallTimeout'] = 60000  # 60s
        self._desiredCaps['skipServerInstallation'] = False  # False为安装
        # 目标活动
        self._desiredCaps['appPackage'] = 'com.akuvox.belahome'
        self._desiredCaps['appActivity'] = 'com.akuvox.mobile.module_main.splash.ui.view.SplashActivity'


class Android_Smart_Panel(AndroidConnect):
    def __init__(self, device_info, device_config, appium_port=None, uiautomator2_system_port=None):
        AndroidConnect.__init__(self, device_info, device_config, appium_port, uiautomator2_system_port)
        self._desiredCaps['automationName'] = 'uiautomator2'
        self._desiredCaps['uiautomator2ServerLaunchTimeout'] = 60000  # 60s
        self._desiredCaps['uiautomator2ServerInstallTimeout'] = 60000  # 60s
        self._desiredCaps['adbExecTimeout'] = 60000     # 60s
        self._desiredCaps['skipServerInstallation'] = False
        # 目标活动
        self._desiredCaps['autoLaunch'] = False
        self._desiredCaps['appPackage'] = 'com.akubela.panel'
        self._desiredCaps['appActivity'] = '.idle_ui.activity.IdleActivity'
