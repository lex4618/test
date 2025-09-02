# -*- coding: utf-8 -*-
import traceback

import win32api
import sys
import os
import winreg
from netifaces import interfaces, ifaddresses, AF_INET, AF_INET6

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)


from akcommon_define import *

"""
该模块为windows系统注册表相关，主要用来通过注册表获取应用信息
"""


def reg_get_application_path(main_key, sub_key):
    """通过注册表获取程序安装路径"""
    try:
        key = winreg.OpenKey(main_key, sub_key)
    except FileNotFoundError:
        return '未安装'
    value, Type = winreg.QueryValueEx(key, "")  # 获取默认值
    value = value.replace('"', '')  # 将双引号去掉
    full_file_path = value.split(',')[0]  # 截去逗号后面的部分
    # [dir_name, file_name] = os.path.split(full_file_name)  # 分离文件名和路径
    return full_file_path


def reg_get_chrome_path():
    """获取chrome浏览器的安装路径"""
    ico_google = r"SOFTWARE\Clients\StartMenuInternet\Google Chrome\DefaultIcon"
    chrome_browser = WindowsReg.reg_get_application_path(winreg.HKEY_LOCAL_MACHINE, ico_google)
    return chrome_browser


def reg_get_current_user_chrome_path():
    """有些环境chrome没有安装在C盘的Program files里面，而是安装在当前用户的目录下"""
    start_menu_internet_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Clients\StartMenuInternet')
    browser_key = ''
    for i in range(10):
        try:
            browser_key = winreg.EnumKey(start_menu_internet_key, i)
            if 'Google Chrome' in browser_key:
                break
        except:
            aklog_printf('获取Google Chrome路径失败')
            break
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Clients\StartMenuInternet\%s\DefaultIcon' % browser_key)
    value, Type = winreg.QueryValueEx(key, "")  # 获取默认值
    full_file_path = value.split(',')[0]  # 截去逗号后面的部分
    aklog_printf('chrome_path: %s' % full_file_path)
    return full_file_path


def reg_get_tshark_path():
    """获取tshark.exe的安装路径"""
    try:
        ico_google = r"SOFTWARE\Classes\wireshark-capture-file\DefaultIcon"
        wireshark_path = reg_get_application_path(winreg.HKEY_LOCAL_MACHINE, ico_google)
        if wireshark_path:
            wireshark_dir = os.path.split(wireshark_path)[0]
            tshark_path = os.path.join(wireshark_dir, 'tshark.exe')
            if not os.path.exists(tshark_path):
                tshark_path = None
        else:
            tshark_path = None
        aklog_printf('tshark_path: %s' % tshark_path)
    except:
        aklog_printf('reg_get_tshark_path failed, %s' % traceback.format_exc())
        tshark_path = None
    return tshark_path


def reg_get_network_key(ifname):
    """定义获取Windows系统网卡接口的在注册表的键值的函数, ifname: 以太网"""
    # 获取所有网络接口卡的键值
    id = interfaces()
    # 存放网卡键值与键值名称的字典
    key_name = {}
    try:
        # 建立链接注册表，"HKEY_LOCAL_MACHINE"，None表示本地计算机
        reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        # 打开r'SYSTEM\CurrentControlSet\Control\Network\{4d36e972-e325-11ce-bfc1-08002be10318}'，固定的
        reg_key = winreg.OpenKey(reg,
                                 r'SYSTEM\CurrentControlSet\Control\Network\{4d36e972-e325-11ce-bfc1-08002be10318}')
    except:
        print('路径出错或者其他问题，请仔细检查')
        return None

    for i in id:
        try:
            # 尝试读取每一个网卡键值下对应的Name
            reg_subkey = winreg.OpenKey(reg_key, i + r'\Connection')
            # 如果存在Name，写入key_name字典
            key_name[winreg.QueryValueEx(reg_subkey, 'Name')[0]] = i
            # print(wr.QueryValueEx(reg_subkey , 'Name')[0])
        except FileNotFoundError:
            pass
    # print('所有接口信息字典列表： ' + str(key_name) + '\n')
    return key_name[ifname]


def reg_get_ip_address(ifname):
    """定义获取ipv4信息的函数, ifname: 以太网"""
    # 调用函数get_key，获取到了网卡的键值
    key = reg_get_network_key(ifname)
    if not key:
        return
    else:
        # 返回ipv4地址信息
        return ifaddresses(key)[AF_INET][0]['addr']


if __name__ == '__main__':
    print(reg_get_ip_address('以太网'))
