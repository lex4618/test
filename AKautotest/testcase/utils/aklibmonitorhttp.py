# -*- coding: UTF-8 -*-

import sys
import os
import time
import subprocess

root_path = os.getcwd()
pos = root_path.find("AKautotest")

if pos == -1:
    print("runtime error")
    exit(1)

root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)
from akcommon_define import *

g_monitor_path = root_path + '\\tools\\monitorhttp'

__all__ = [
    "start_monitor_http",
    "stop_monitor_http",
    "get_monitor_ip_urllist",
]


def start_monitor_http():
    """启动监控http, 并清空url.txt"""
    clear_url_log()
    cmd_close_process_by_name('monitorHTTPtoPC.exe')
    sub_process_exec_command(g_monitor_path + '\\monitorHTTPtoPC.exe' + ' ' + g_monitor_path + '\\url.txt', timeout=5)


def clear_url_log():
    # 备份上一次的
    file = g_monitor_path + '\\url.txt'
    File_process.copy_file(file, file.replace('url.txt', 'url_bak.txt'))
    File_process.remove_file(file)


def stop_monitor_http():
    cmd_close_process_by_name('monitorHTTPtoPC.exe')


def get_monitor_ip_urllist(filterip):
    """
    获取一次后, 清空. 避免影响后续用例
    需要传入filterip:  ip.src==,  返回list
    eg: ['http://192.160.30.213/test.xml']
    """
    file = g_monitor_path + '\\url.txt'
    if not os.path.exists(file):
        return []
    with open(file, 'r', encoding='utf8') as f:
        content = f.read()
    retdict = {}
    for i in content.splitlines():
        ip, url = i.strip().split('-->')
        if ip.strip() not in retdict:
            retdict[ip.strip()] = [url.strip()]
        else:
            retdict[ip.strip()].append(url.strip())
    clear_url_log()
    return retdict.get(filterip, [])
