# -*- coding: UTF-8 -*-
import io
import sys
import os
import socket
import _thread
import threading

root_path = os.getcwd();
pos = root_path.find("AKautotest");

if pos == -1:
    print("runtime error");
    exit(1);

root_path = root_path[0:pos + len("AKautotest")]

sys.path.append(root_path)

import akcommon_define
from akcommon_define import *


#### source code ######
#UDP 服务端事务处理，回调cb函数
class udp_server_thread(threading.Thread):
    def __init__(self, threadID, name, cb, client_socket, connected_addr):
        aklog_printf("%s,__init__" % (self.__class__.__name__));
        threading.Thread.__init__(self)
        self.__threadID = threadID
        self.__name = name
        self.__client_socket = client_socket
        self.__cb = cb;

    def run(self):
        aklog_printf("%s,run" % (self.__class__.__name__));
        self.__cb(self.__client_socket);
        self.__client_socket.close();

#UDP 服务端类(未测试)
class akudp_server():
    __s = None;

    def __init__(self, host, port, listen_num, cb):
        aklog_printf("%s,__init__ ,host:%s, port:%s" % (self.__class__.__name__, host, port));
        self.__host = host;
        self.__port = port;
        self.__listen_num = listen_num;
        self.__cb = cb;

    def __del__(self):
        aklog_printf("%s,__del__" % (self.__class__.__name__));
        if not self.__s:
            self.__s.close();

    #创建UDP 服务端并开始监听
    def creat(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
        aklog_printf("udp socket create :%s" % s);

        lhost = self.__host;

        if lhost != '':
            try:
                lhost = socket.gethostbyname(self.__host);
            except socket.gaierror:
                aklog_printf("Hostname:%s could not be resolved" % (self.__host));
                return False;

        try:
            aklog_printf("lhost:%s" % lhost);
            s.bind((lhost, self.__port))
        except:
            aklog_printf("Bind failed.");
            return False;

        s.listen(self.__listen_num);
        self.__s = s;
        return True;

    #监听是否有客户端连接，同时连接后创建线程进行并发处理，如果并发事务有临界区，自己在cb函数内加锁保护
    def run(self):
        aklog_printf("%s,run" % (self.__class__.__name__));
        id = 0;
        while True:
            clientsocket, addr = self.__s.accept()
            aklog_printf("连接地址: %s" % str(addr));

            id += 1;
            tid = "%s_%d" % (self.__host, id);
            tname = "%s%s" % (self.__host, str(addr));
            lthread = udp_server_thread(tid, tname, self.__cb, clientsocket, addr);
            lthread.start();

