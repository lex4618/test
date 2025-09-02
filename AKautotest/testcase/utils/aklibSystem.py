#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import win32file  # pip install pypiwin32
import win32con
import shutil
import time
import threading
import traceback

from akcommon_define import *

ACTIONS = {
    1: "created",
    2: "deleted",
    3: "updated",
    4: "renamed from something",
    5: "renamed to something"
}

FILE_LIST_DIRECTORY = 0x0001


class event:
    def __init__(self, full_filename, action):
        self.src_path = full_filename
        self.event_type = action


def __MonitorPath(path, callback, mutex=None):
    for i in range(10):
        try:
            path_to_watch = path
            hDir = win32file.CreateFile(
                path_to_watch,
                FILE_LIST_DIRECTORY,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_FLAG_BACKUP_SEMANTICS,
                None
            )

            aklog_printf('开始监控路径 --- %s ' % path_to_watch)
            while True:
                results = win32file.ReadDirectoryChangesW(
                    hDir,
                    1024,
                    False,
                    win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                    win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                    win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                    win32con.FILE_NOTIFY_CHANGE_SIZE |
                    win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                    win32con.FILE_NOTIFY_CHANGE_SECURITY,
                    None,
                    None)

                results_new = []
                results_len = len(results)
                # print('results: %r' % results)
                for j in range(results_len)[::-1]:
                    action, filename = results[j]
                    if 'run' not in filename:
                        results_new.append(results[j])
                        results.pop(j)
                results_new.reverse()
                results_new.extend(results)
                aklog_printf('results_new: %r' % results_new)
                for action, filename in results_new:
                    full_filename = os.path.join(path_to_watch, filename)
                    if mutex:
                        mutex.acquire()
                    callback(event(full_filename, ACTIONS.get(action, "unknown")))
                    if mutex:
                        mutex.release()
        except:
            aklog_printf('遇到未知异常, 重新启动监控 --- %s, 当前异常次数为: %s' % (path, str(i + 1)))
            aklog_printf(traceback.format_exc())
            time.sleep(60)
            continue

    aklog_printf('遇到未知异常, 程序退出! ' + str(traceback.format_exc()))
    return False


def MonitorPath(paths, callback):
    mutex = threading.Lock()

    for path in paths:
        monitor_thread = threading.Thread(target=__MonitorPath, args=(path, callback, mutex))
        monitor_thread.name = path  # 将路径作为线程名称， paths即为线程名称组
        monitor_thread.start()

    check = threading.Thread(target=check_monitor_thread, args=(callback, paths, mutex, 180))  # 用来检测是否有线程down并重启down线程
    check.name = 'Thread:check'
    check.daemon = True
    check.start()


def MonitorPath_without_mutex(paths, callback):
    for path in paths:
        monitor_thread = threading.Thread(target=__MonitorPath, args=(path, callback, None))
        monitor_thread.name = path  # 将路径作为线程名称， paths即为线程名称组
        monitor_thread.start()

    check = threading.Thread(target=check_monitor_thread, args=(callback, paths, None, 180))  # 用来检测是否有线程down并重启down线程
    check.name = 'Thread:check'
    check.daemon = True
    check.start()


def check_monitor_thread(callback, initThreadsName, mutex, sleep_times=180):
    """每180s获取当前线程名，并跟初始线程组比较，某一线程停止后自动运行"""
    aklog_printf('check monitor thread')
    while True:
        nowThreadsName = []  # 用来保存当前线程名称
        now = threading.enumerate()  # 获取当前线程名
        for j in now:
            nowThreadsName.append(j.getName())  # 保存当前线程名称

        for thread_name in initThreadsName:
            if thread_name in nowThreadsName:
                pass  # 当前某线程名包含在初始化线程组中，可以认为线程仍在运行
            else:
                aklog_printf('=== %s stopped，now restart' % thread_name)
                t = threading.Thread(target=__MonitorPath, args=(thread_name, callback, mutex))
                t.name = thread_name  # 重设name
                t.start()
        time.sleep(sleep_times)  # 隔一段时间重新运行，检测有没有线程down


def ClearFolder(folder):
    try:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            time.sleep(5)  # 等待一下, 确保完全删除
    except:
        aklog_printf('ClearFolder[' + folder + ']执行失败!')
    else:
        os.mkdir(folder)
