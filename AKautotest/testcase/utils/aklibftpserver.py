# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess, traceback
import time
from threading import Thread

root_path = os.getcwd()
pos = root_path.find("AKautotest")

if pos == -1:
    print("runtime error")
    exit(1)

root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)
from akcommon_define import *

g_ftpserver_path = root_path + '\\tools\\cmd_ftpserver\\cmd_ftpserver.exe'
g_ftp_path = root_path + '\\tools\\cmd_ftpserver\\admin'
g_ftp_anonymous_path = root_path + '\\tools\\cmd_ftpserver\\anonymous'


def start_ftp_server(force_kill=True, mac=None):
    """
    如果传入mac, 就指定到mac路径下, 防止公共环境下ftp的错误影响
    """
    user = 'admin'
    password = '123456'
    if type(force_kill) == str:
        mac = force_kill
    if mac:
        mac = mac.lower().replace('-', '').replace(':', '')
        ftp_path = g_ftp_path + '\\' + mac
        if not os.path.exists(ftp_path):
            os.mkdir(ftp_path)
        else:
            for i in os.listdir(ftp_path):
                File_process.remove_file(ftp_path + '\\' + i)
    else:
        ftp_path = g_ftp_path

    if force_kill:
        cmd_close_process_by_port(21)
        time.sleep(3)
    if not cmd_get_process_pid_by_port(21):
        sub_process_exec_command(
            g_ftpserver_path + ' ' + user + ' ' + password + ' ' + ftp_path + ' ' + g_ftp_anonymous_path,
            timeout=5)
        time.sleep(3)
        aklog_info('当前21端口对应程序: ' + str(cmd_get_process_name_by_pid(cmd_get_process_pid_by_port(21))))


def stop_ftp_server():
    cmd_close_process_by_port(21)


def clear_ftp_server(mac=None):
    if mac:
        ftppath = g_ftp_path + '\\' + mac.lower().replace('-', '').replace(':', '')
    else:
        ftppath = g_ftp_path
    for i in os.listdir(ftppath):
        File_process.remove_file(os.path.join(ftppath, i))
    for d in os.listdir(g_ftp_anonymous_path):
        File_process.remove_file(os.path.join(g_ftp_path, d))


def return_ftp_server_path():
    return g_ftp_path


def return_ftp_server_mac_path(mac):
    return g_ftp_path + '\\' + mac.lower().replace('-', '').replace(':', '')


def get_ftp_server_jpg_amount(mac=None):
    if mac:
        ftppath = g_ftp_path + '\\' + mac.lower().replace('-', '').replace(':', '')
    else:
        ftppath = g_ftp_path
    amount = 0
    if os.path.exists(ftppath):
        for i in os.listdir(ftppath):
            if i.endswith('.jpg'):
                amount += 1
    return amount
