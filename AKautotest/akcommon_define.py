# -*- coding: UTF-8 -*-
import locale
import sys
import os
import time
import subprocess
import shutil
import traceback
from pathlib import Path
from typing import Union, Optional, List

g_start_path = os.getcwd()
try:
    import vlc
    # 工作路径被改变会导致导入失败, 移动到这里导入
except:
    pass
finally:
    os.chdir(g_start_path)


# locale.setlocale(locale.LC_ALL, 'en')


def append_path(rootpath):
    for dir_or_file in os.listdir(rootpath):
        dir_path = os.path.join(rootpath, dir_or_file)
        if os.path.isdir(dir_path):
            if (dir_or_file == 'testfile'
                    or dir_or_file == 'outputs'
                    or dir_or_file == 'pip-install'
                    or dir_or_file == '__pycache__'
                    or dir_or_file == 'testdata'
                    or dir_or_file == 'tools'
                    or dir_or_file == 'module'
                    or dir_or_file == '.svn'
                    or dir_or_file == 'ModuleList'
                    or dir_or_file == 'element_info'
                    or dir_or_file == 'libconfig'
                    or dir_or_file.startswith('.')):
                continue
            if dir_path not in sys.path:
                sys.path.append(dir_path)
            append_path(dir_path)


pos = g_start_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = g_start_path[0:pos + len("AKautotest")]
append_path(root_path)

# 全局变量
g_params = {}
g_params_test_main = {}
g_config_path = '%s\\libconfig' % root_path
g_config_ini_file = 'config.ini'
g_robot_info_file = 'robot_info.ini'
g_outputs_root_path = '%s\\outputs' % root_path
g_common_element_info_path = '%s\\testcase\\common\\element_info' % root_path
g_module_root_path = '%s\\testcase\\module' % root_path
g_firmware_info_root_path = '%s\\testdata\\FirmwareInfo' % root_path
# g_start_path = '%s\\testcase\\apps' % root_path
g_screenshots_imgs = []
g_appium_ports = []
g_wda_ports = []
g_uiautomator2_system_ports = []
g_ws_server_ports = []
# manual_modules_file = 'manual_modules.txt'
g_test_results_summary = {
    "Product_name": "",
    "Total_testcases": 0,
    "Pass_testcases": 0,
    "Pass_rate": 0,
    "Take_time": "",
    "Test_date": "",
    "Product_version": ""
}
g_chrome_driver_path = '%s\\testcase\\apps\\chromedriver.exe' % root_path
g_nap_time_range = []


def append_module_path(rootpath, series_product, version_branch=''):
    """
    添加目录到sys.path环境变量
    """
    if rootpath == g_module_root_path:
        product_line = config_get_product_line_by_series_module_name(series_product)
        rootpath = os.path.join(g_module_root_path, product_line, series_product)
        if not os.path.exists(rootpath):
            rootpath = os.path.join(g_module_root_path, series_product)
    for dir_or_file in os.listdir(rootpath):
        dir_path = os.path.join(rootpath, dir_or_file)
        if os.path.isdir(dir_path):
            if (dir_or_file == '.svn'
                    or dir_or_file == 'ModuleList'
                    or dir_or_file == 'TestData'
                    or dir_or_file == 'TestFile'
                    or dir_or_file == '.idea'
                    or dir_or_file == '__pycache__'
                    or dir_or_file == 'Config'
                    or dir_or_file == 'Base'
                    or dir_or_file == 'ControlBase'
                    or dir_or_file.startswith('.')):
                continue
            # 只添加指定分支目录，其他分支目录都跳过，如果没有定义分支，则module下的机型目录都添加到环境变量
            if (version_branch != ''
                    and os.path.split(rootpath)[1] == series_product
                    and dir_or_file != version_branch):
                continue
            if dir_path not in sys.path:
                sys.path.append(dir_path)
            if series_product == 'cloud':  # 云平台目录只添加到云平台分支版本根目录
                continue
            append_module_path(dir_path, '', '')


from testcase.utils.aklibLog import *

from testcase.utils.aklibparams import *

from testcase.utils.aklibsubprocess import *

from testcase.utils.aklibstring_opration import *

import testcase.utils.aklibCloudMd5 as CloudMd5

import testcase.utils.aklibSystem as System

from testcase.utils.aklibExcelOperation import *

from testcase.utils.aklibXML_process import *

from testcase.utils.aklibtime_opration import *

from testcase.utils.aklibReadconfig import *

from testcase.utils.aklibMysql import *

from testcase.utils.aklibWorkWeixinRobot import *

from testcase.utils.aklibmsg import *

from testcase.utils.aklibudpclient import *

from testcase.utils.aklibudpserver import *

from testcase.utils.aklibdevctrl import *

from testcase.utils.aklibdevctrl_tester import *

from testcase.utils.aklibdecode_encode import *

from testcase.utils.aklibsql import *

from testcase.utils.aklibmisc import *

from libconfig.libconfig_parse import *

from testcase.utils.aklibthread import *

from testcase.utils.aklibReport import *

from testcase.utils.aklibunittest import *

from testcase.utils.aklibHTMLTestRunner import HTMLTestRunner

from testcase.utils.BeautifulReport import BeautifulReport, FIELDS, reset_fields

from testcase.utils.aklibEmail import *

from testcase.utils.aklibssh import *

from testcase.utils.aklibtelnet import *

from testcase.utils.aklibftpclient import *

from testcase.utils.aklibtftpserver import *

from testcase.utils.aklibcmdntpserver import *

import testcase.utils.aklibFile_process as File_process

from testcase.utils.aklibImage_process import *

from testcase.utils.aklibWindow_process import *

from testcase.utils.aklibadapter import *

from testcase.utils.aklibIntercomAdapter import IntercomAdapter

from testcase.utils.aklibWxFrame import MainFrame

import testcase.utils.aklibWindowsReg as WindowsReg

from testcase.utils.aklibpcap_operation import *

from testcase.utils.aklibpcap import *

from testcase.utils.aklibpnpserver import start_pnpserver, stop_pnpserver

from testcase.utils import aklibsel_remote_web

from testcase.utils.aklibtranscode import *

from testcase.utils.aklibhfsserver import *

from testcase.utils.aklibmonitorhttp import *

from testcase.utils.aklibmonitorsip import *

from testcase.utils.aklibftpserver import *

from testcase.utils.aklibcmdtftpserver import *

from testcase.utils.aklibrtsp import *

from testcase.utils.aklibonvif import *

import testcase.utils.aklibWebRelay as libWebRelay

from testcase.utils.aklibVideoCapture import *

from testcase.utils.aklibSyslogServer import *

from testcase.common.aklibAndroidAppium import *

from testcase.common.aklibApiRequests import ApiRequests

from testcase.common.aklibrequests import AkRequests, AkHTTPAPI

import testcase.utils.aklibChromeDriverUpdate as ChromeDriverUpdate

from testcase.common.aklibDClient_Decrypt import DClient_Decrypt

from testcase.common.aklibP2D_interface import P2D_interface

from testcase.common.aklibbrowser import *

from testcase.utils.aklibSipProxyWeb import *

from testcase.utils.aklibMonitorSwitchWeb import *

from testcase.utils.aklibMyPBXServerWeb import *

from testcase.common.aklibwin import *

from testcase.common.aklibAndroidConnect import *

from testcase.common.aklibAndroidBase import *

from testcase.common.aklibAndroidDevice import *

from testcase.common.aklibAndroidBaseU2 import *

from testcase.common.aklibIOSBaseU2 import *

from testcase.common.aklibWebsocketClient import AkWSClient

from testcase.common.aklibweb_device_NORMAL import web_device_NORMAL

from testcase.common.aklibweb_v3_device_NORMAL import web_v3_device_NORMAL

from testcase.common.aklibweb_v4_device_NORMAL import web_v4_device_NORMAL

from testcase.common.aklibweb_v4_device_intercom_NORMAL import web_v4_device_intercom_NORMAL

from testcase.common.aklibweb_son_device_NORMAL import web_son_device_NORMAL

from testcase.common.aklibweb_v4_son_device_NORMAL import web_v4_son_device_NORMAL

from testcase.common.aklibAkubelaPanelWeb import AkubelaPanelWeb

from testcase.common.aklibAkubelaUserWebInterface import *

from testcase.common.aklibAkubelaUserWebInterface_v2 import *

from testcase.common.aklibAkubelaUserWeb import AkubelaUserWeb

from testcase.common.aklibDeviceWebInterface import DeviceWebInterface

from testcase.common.aklibWindowBase import WindowBase

from testcase.common.aklibRtspClient import *

from testcase.utils.aklibtest_main import *

from testcase.utils.aklibtrigger_test import *

from testcase.utils.aklibDeviceAdapter import DeviceAdapter

from testcase.common.aklibAutoTestApp import AutoTestApp

from testcase.utils.aklibsnmp import check_snmp_connect_state

from testcase.utils.aklibserial import *

from testcase.utils.aklibpersonal_cloud import get_installer, get_proper, get_distributor, get_supermanager, get_app

try:
    from testcase.utils.aklibmiio import MiioDev
except:
    pass

from testcase.utils.aklibextract import extract_tgz_file

try:
    from testcase.utils.aklibplaysound import *
except:
    pass

from testcase.utils.aklibmessagebox import messagebox_with_timeout, messagebox_with_input

from testcase.utils.aklibknxnet import *

from testcase.utils.sdmcWin.aklibSDMCAPI import sdmcAPI
