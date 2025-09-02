# -*- coding: utf-8 -*-

import socket as sk
import os
import sys
import time

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
if root_path not in sys.path:
    sys.path.append(root_path)

from akcommon_define import *


class SyslogServer:
    
    def __init__(self, port=514):
        self.port = port
        self.server = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        self.server.bind(('0.0.0.0', self.port))
        self.thread = None

    def syslog_serve_forever(self):
        logs = ''
        while param_get_thread_stop_flag() > 0:
            data = self.server.recvfrom(8092)
            (LogMsg, host) = data
            LogMsg = LogMsg.decode('utf-8').strip(b'\x00'.decode())
            print(LogMsg)
            logs += LogMsg
        # print('logs: %r' % logs)
        return logs

    def start_syslog_server(self):
        aklog_printf('start_syslog_server')
        self.thread = AkThread(target=self.syslog_serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop_syslog_server(self):
        aklog_printf('stop_syslog_server')
        try:
            # 设置子线程退出标志，子线程循环跳出
            param_put_thread_stop_flag(0)
            # 等待子线程执行完毕
            for i in range(10):
                if self.thread.is_alive():
                    time.sleep(1)
                    continue
                else:
                    break
            param_put_thread_stop_flag(10)
            return self.thread.get_result()  # 获取子线程执行结果
        except:
            param_put_thread_stop_flag(10)


if __name__ == '__main__':
    print('调试')
    syslog = SyslogServer()
    syslog.start_syslog_server()
    time.sleep(10)
    print(syslog.stop_syslog_server())
