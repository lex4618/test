# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess
import traceback, time

root_path = os.getcwd()
pos = root_path.find("AKautotest")

if pos == -1:
    print("runtime error")
    exit(1)

root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)
from akcommon_define import *

exe_path = root_path + '\\tools\\cmd_tftpserver\\tftp_server.exe'
tftpserver_root_path = root_path + '\\tools\\cmd_tftpserver\\root_path'


def start_tftp_server(ip, root=None):
    if cmd_get_process_pid_by_port(69, False) and cmd_get_process_name_by_pid(
            cmd_get_process_pid_by_port(69, False)) == 'tftp_server.exe':
        return True
    result = subprocess.getoutput('netstat -ano | findstr ":%s" | findstr "UDP"' % 69)
    if result:
        aklog_info('69端口已经被占用!!!')
        aklog_info('端口信息如下： %s' % result)
        if cmd_get_process_name_by_pid(cmd_get_process_pid_by_port(69, False)) == 'python.exe':
            pass
        else:
            cmd_close_process_by_port(69, False)

    global tftpserver_root_path
    if root:
        aklog_printf('准备开启tftpserver, root地址: %s' % root)
        tftpserver_root_path = root
    else:
        root = tftpserver_root_path
        aklog_printf('准备开启tftpserver, root地址: %s' % tftpserver_root_path)

    process_info = subprocess.getoutput('tasklist | findstr "%s"' % 'tftp_server.exe')
    if not process_info:
        aklog_printf(exe_path + ' ' + ip + ' ' + root)
        sub_process_exec_command(exe_path + ' ' + ip + ' ' + root, timeout=3)
        tftpserver_root_path = root
        time.sleep(2)


def stop_tftp_server():
    cmd_close_process_by_name('tftp_server.exe')


def clear_tftp_root_dir():
    for i in os.listdir(tftpserver_root_path):
        if i == 'indoor_test.bin':
            pass
        else:
            for j in range(2):
                try:
                    os.remove(os.path.join(tftpserver_root_path, i))
                except:
                    print(traceback.format_exc())
                    time.sleep(1)
                else:
                    break


def get_tftp_root_dir_jpg_count():
    """
    返回tftp服务器下jpg文件个数
    """
    amount = 0
    for i in os.listdir(tftpserver_root_path):
        if i.endswith('.jpg'):
            amount += 1
    return amount
