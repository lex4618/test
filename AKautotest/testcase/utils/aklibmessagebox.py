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
import traceback
import ctypes
import win32con


def messagebox_with_timeout(msgcontent=None, timeout=60, msgtitle='提示', boxtype='yes no'):
    """
    半自动使用， 系统弹窗人工选择是否
    boxtype: yes no / yes no cancel
    """
    timeout = timeout * 1000  # 转换毫秒
    if boxtype == 'yes no':
        ret = ctypes.windll.user32.MessageBoxTimeoutW(0, msgcontent, msgtitle, win32con.MB_YESNO, 1, timeout)
    else:
        ret = ctypes.windll.user32.MessageBoxTimeoutW(0, msgcontent, msgtitle, win32con.MB_YESNOCANCEL, 1, timeout)
    if ret == 6:
        aklog_info('系统弹窗按下了： 【确认】')
        return True
    elif ret == 7:
        aklog_info('系统弹窗按下了： 【否】')
        return False
    else:
        aklog_info('系统弹窗按下了： 【取消】或超时退出')
        return None


def messagebox_with_input(tips="输入内容提示", timeout=60):
    file = root_path + '\\tools\\popInputString\\popInputString.txt'
    tool = root_path + '\\tools\\popInputString\\popInputString.exe'
    ret = sub_process_exec_command(tool + ' 标题 {} {}'.format(tips, file), timeout=timeout)
    if not ret:
        aklog_error('未在{}秒内输出文本!'.format(timeout))
        sub_process_exec_command('taskkill /f /im popInputString.exe')
        return False
    else:
        with open(file, 'r', encoding='utf8') as f:
            content = f.read()
        sub_process_exec_command('taskkill /f /im popInputString.exe')
        return content.strip()
