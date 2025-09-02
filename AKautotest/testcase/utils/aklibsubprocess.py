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
if root_path not in sys.path:
    sys.path.append(root_path)

from akcommon_define import *
import subprocess
import threading
import traceback


def read_stream(stream, buffer):
    """读取子进程输出流并存储在缓冲区"""
    try:
        for line in iter(lambda: stream.readline(), b''):
            buffer.append(line.decode('utf-8', errors='ignore'))
        # aklog_debug('read stream stopped')
    except ValueError:
        aklog_debug("Stream is closed, stopping read.")


def sub_process_get_output(command, timeout=10, shell=True, get_err=True):
    """子进程获取命令执行结果"""
    aklog_printf()
    process = None
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   encoding='utf-8', errors="ignore", shell=shell)
        stdout, stderr = process.communicate(timeout=timeout)
        if process.poll() != 0:
            process.terminate()
        out = ''
        if stdout:
            out += stdout
        if stderr:
            aklog_debug(f'error: {stderr}')
            if get_err:
                out += stderr
        return out
    except:
        aklog_printf('sub_process_get_output failed, %s' % traceback.format_exc())
        try:
            process.terminate()
        except:
            pass
        return None


def sub_process_exec_command(command, timeout=10, shell=True, is_raise=False):
    """
    子进程执行命令
    命令执行失败时可以打印命令执行过程log和错误log，并可以选择抛出命令执行异常
    Args:
        command (str):
        timeout (int):
        shell (bool):
        is_raise (bool): 是否将异常直接抛出
    """
    aklog_debug()
    process = None
    stdout_thread = None
    stderr_thread = None
    result = False
    error = None
    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        # 创建缓冲区
        stdout_buffer = []
        stderr_buffer = []

        # 启动线程读取输出
        stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, stdout_buffer))
        stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, stderr_buffer))
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        stdout_thread.start()
        stderr_thread.start()

        # 等待子进程完成
        process.wait(timeout=timeout)
        stdout_thread.join(timeout=0.1)
        stderr_thread.join(timeout=0.1)

        # 检查返回码
        if process.returncode != 0:
            error_message = ''.join(stderr_buffer)
            if is_raise:
                raise Exception(error_message)
            aklog_printf(f'Command failed with return code {process.returncode}')
            aklog_printf(f'Stdout: {"".join(stdout_buffer)}')
            aklog_printf(f'Stderr: {error_message}')
        else:
            result = True
    except Exception as e:
        error = e
    finally:
        # 终止子进程
        try:
            process.terminate()
            process.wait(timeout=1)
        except:
            process.kill()
        # 等待线程结束
        if stdout_thread:
            stdout_thread.join(timeout=0.5)
        if stderr_thread:
            stderr_thread.join(timeout=0.5)

        if is_raise and error:
            raise error
        if error:
            aklog_debug(f'Exception Error: {error}')
    return result


if __name__ == "__main__":
    cmd = 'adb -s 192.168.88.103:5654 shell top'
    out = sub_process_exec_command(cmd, is_raise=False)
    aklog_debug(out)
