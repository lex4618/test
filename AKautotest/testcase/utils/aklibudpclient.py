# -*- coding: UTF-8 -*-
import io
import sys
import os
import socket
import _thread
import threading
import select

root_path = os.getcwd()
pos = root_path.find("AKautotest")

if pos == -1:
    print("runtime error")
    exit(1)

root_path = root_path[0:pos + len("AKautotest")]

sys.path.append(root_path)

import akcommon_define
from akcommon_define import *

#### source code ######

'''udp客户端封装, 简单使用就是creat&send_recv'''


class akudp_client:
    __s = None

    def __init__(self, host, port, recv_len, recv_timeout):
        aklog_printf("%s,__init__ ,host:%s, port:%s" % (self.__class__.__name__, host, port))
        self.__host = host
        self.__port = port
        self.__recv_timeout = recv_timeout
        self.__recv_len = recv_len

    def __del__(self):
        print("%s,__del__" % self.__class__.__name__)
        if not self.__s:
            self.__s.close()

    # 创建UDP 客户端,成功返回True
    def creat(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        aklog_printf("udp socket create :%s" % s)

        try:
            s.connect((self.__host, self.__port))
        except socket.error:
            aklog_printf("connect  %s:%dfailed!" % (self.__host, self.__port))
            return False

        self.__s = s
        return True

    # 发送数据，并等待数据接收，数据等待超时返回失败，否则返回接收到的数据
    def send_recv(self, send_data):
        aklog_printf("%s,send_recv send_data:%s" % (self.__class__.__name__, send_data))

        self.__s.sendall(send_data)
        timeout = self.__recv_timeout  # 等等10s

        aklog_printf("%s,send_recv timeout:%s" % (self.__class__.__name__, timeout))
        self.__s.setblocking(0)
        ready = select.select([self.__s], [], [], timeout)
        if ready[0]:
            recv_data = self.__s.recv(1024)
            aklog_printf("recv data:%s" % recv_data)
            return recv_data

        return ""

    # 仅发送数据
    def send_only(self, send_dadta):
        aklog_printf("%s,send_only send_dadta:%s" % (self.__class__.__name__, send_dadta))

        self.__s.sendall(send_dadta)
        return True

    # 阻塞接收数据
    def recv_only(self):
        aklog_printf("%s,recv_only" % self.__class__.__name__)

        self.__s.setblocking(1)
        recv_data = self.__s.recv(self.__recv_len).strip('\x00')
        aklog_printf("recv data:%s" % recv_data)
        return recv_data


'''demo
udp_client = akudp_client(ip, self.__port, 1500, timeout);
r = udp_client.creat();
udp_client.send_only("demo");
'''
