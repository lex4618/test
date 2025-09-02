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

g_httpserver_path = root_path + '\\testfile\\python_httpserver.exe'
g_digest_httpserver_path = root_path + '\\testfile\\python_digest_httpserver.exe'
http_dir = root_path + '\\testfile'


def start_http_server(force_kill=True):
    """
    http://192.168.1.x/
    """
    ret = cmd_get_process_pid_by_port(80)
    if ret and ret == '4':
        return True

    bef_dir = os.getcwd()
    for i in range(2):
        try:
            if force_kill:
                # system进程启的80就不kill.
                cmd_close_process_by_port(80)
                time.sleep(3)
            if not cmd_get_process_pid_by_port(80):
                os.chdir(http_dir)
                sub_process_exec_command(g_httpserver_path + ' http', timeout=5)
                time.sleep(3)
                ret = cmd_get_process_name_by_pid(cmd_get_process_pid_by_port(80))
                if ret:
                    aklog_info('当前80端口对应程序: ' + str(ret))
                    os.chdir(bef_dir)
                    break
                else:
                    aklog_error("打开http server失败")
        finally:
            os.chdir(bef_dir)


def start_http_auth_server(username='admin', password='password', force_kill=False):
    """
    http://192.168.1.x:8000/
    """
    bef_dir = os.getcwd()
    try:
        if force_kill:
            cmd_close_process_by_port(8000)
        if not cmd_get_process_pid_by_port(8000):
            os.chdir(http_dir)
            sub_process_exec_command(g_httpserver_path + ' http ' + username + ' ' + password, timeout=5)
    finally:
        os.chdir(bef_dir)


def start_digest_http_server(username='admin', password='password', force_kill=False):
    """
    http://192.168.1.x:8001/
    """
    bef_dir = os.getcwd()
    try:
        if force_kill:
            cmd_close_process_by_port(8001)
        if not cmd_get_process_pid_by_port(8001):
            os.chdir(http_dir)
            sub_process_exec_command(g_digest_httpserver_path + ' ' + username + ' ' + password, timeout=5)
    finally:
        os.chdir(bef_dir)


def stop_http_server():
    cmd_close_process_by_port(80)
    cmd_close_process_by_port(8000)
    cmd_close_process_by_port(8001)


def stop_digest_http_server():
    cmd_close_process_by_port(8001)


def stop_https_server():
    cmd_close_process_by_port(443)
    cmd_close_process_by_port(444)


def start_https_server(force_kill=False):
    """
    https://192.168.1.x/
    """
    bef_dir = os.getcwd()
    try:

        if force_kill:
            cmd_close_process_by_port(443)
        if not cmd_get_process_pid_by_port(443):
            os.chdir(http_dir)
            sub_process_exec_command(g_httpserver_path + ' https ', timeout=5)
            time.sleep(3)
    finally:
        os.chdir(bef_dir)


def start_https_auth_server(username='admin', password='password', force_kill=False):
    """
    https://192.168.1.x:444/
    """
    bef_dir = os.getcwd()
    try:
        if force_kill:
            cmd_close_process_by_port(444)
        if not cmd_get_process_pid_by_port(444):
            os.chdir(http_dir)
            sub_process_exec_command(g_httpserver_path + ' https ' + username + ' ' + password, timeout=5)
            time.sleep(3)
    finally:
        os.chdir(bef_dir)


def wait_for_equal(expect_result, func_method_with_result, timeout=120, interval=10):
    close_global_log()
    cur_time = time.time()
    time.sleep(interval)
    for i in range(int(timeout / interval) + 2):
        if time.time() - cur_time > timeout:
            start_global_log()
            aklog_error('未能在timeout时间内正常同步配置, 返回失败')
            return ret
        ret = func_method_with_result()
        if ret == expect_result:
            start_global_log()
            aklog_info('获取到期望结果， 返回结果: {}'.format(expect_result))
            return ret
        else:
            time.sleep(interval)
    start_global_log()
    aklog_error('同步配置失败！')
    return ret


def wait_for_not_equal(compare_result, func_method_with_result, timeout=120, interval=10):
    close_global_log()
    cur_time = time.time()
    time.sleep(interval)
    for i in range(int(timeout / interval) + 2):
        if time.time() - cur_time > timeout:
            start_global_log()
            aklog_error('未能在timeout时间内正常同步配置, 返回失败')
            return ret
        ret = func_method_with_result()
        if ret != compare_result:
            start_global_log()
            aklog_info('获取到期望结果， 返回结果')
            return ret
        else:
            time.sleep(interval)
    start_global_log()
    aklog_error('同步配置失败！')
    return ret


if __name__ == '__main__':
    start_https_auth_server()
