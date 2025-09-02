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

exe_path = root_path + '\\tools\\cmd_pnpserver\\python_ntpserver.exe'


def cmd_close_process_by_name(exe_name):
    aklog_printf("cmd_close_process_by_name: %s" % exe_name)
    for i in range(2):
        process_info = subprocess.getoutput('tasklist | findstr "%s"' % exe_name)
        if not process_info:
            aklog_printf('%s is closed' % exe_name)
            return True
        elif i == 1:
            aklog_printf('close process %s failed' % exe_name)
        else:
            sub_process_exec_command('taskkill /F /t /im "%s"' % exe_name)
            time.sleep(2)
            continue


def start_ntp_server(timestring=None):
    aklog_printf('准备开启ntp server')
    cmd_close_process_by_name('python_ntpserver.exe')
    time.sleep(5)
    if timestring is None or timestring == '':
        process = subprocess.Popen(exe_path, shell=True)
    else:
        process = subprocess.Popen(exe_path + ' ' + timestring, shell=True)


def stop_ntp_server():
    cmd_close_process_by_name('python_ntpserver.exe')

