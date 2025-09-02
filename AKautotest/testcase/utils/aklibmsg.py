#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import io
import sys
import os
import struct
import six

root_path = os.getcwd()
pos = root_path.find("AKautotest")

if pos == -1:
    print("runtime error")
    exit(1)

root_path = root_path[0:pos + len("AKautotest")]

sys.path.append(root_path)

from akcommon_define import *

package_content_len_without_data = 4
content_len_index = 1


# 网络包相关的负载数据最大值为1500，会根据待发送数据和接收数据自动处理，无需指定数据长度
class akipc_msg_parse:
    __head = 0
    __len = 0
    __event_id = 0
    __mothod = 0
    __recv_event_id = 0
    __data = b''
    __check = 0
    __end = 0
    __state = 0
    __id = 0
    __param1 = 0
    __param2 = 0

    # 将设置好的msg进行封包
    def pack(self):
        aklog_printf("%s,pack" % self.__class__.__name__)
        fmt = '!BBBB%dsBB' % len(self.__data)
        str = struct.pack(fmt, self.__head, int(hex(self.__len), 16), int(hex(self.__event_id), 16),
                          int(hex(self.__mothod), 16), self.__data, self.__check, self.__end)
        return str

    # 对msg进行解包
    def unpack(self, str_data):
        aklog_printf("%s,unpack" % self.__class__.__name__)
        s = len(str_data)
        fmt = "!iiiii%ds" % (s - struct.calcsize("iiiii"))
        self.__id, self.__state, self.__param1, self.__param2, self.__len, self.__data = struct.unpack(fmt, str_data)
        aklog_printf("str:%s unpack to (%d,%d,%d,%d,%d,%s)" % (
            str_data, self.__id, self.__state, self.__param1, self.__param2, self.__len, self.__data))

    def set_head(self, head):
        # aklog_printf("%s,set_head" % (self.__class__.__name__));
        self.__head = head

    def get_head(self, head):
        # aklog_printf("%s,get_head" % (self.__class__.__name__));
        return self.__head

    def set_len(self, len):
        # aklog_printf("%s,set_len" % (self.__class__.__name__));
        # self.__len = six.int2byte(len);
        self.__len = len

    def get_len(self, len):
        # aklog_printf("%s,get_len" % (self.__class__.__name__));
        return self.__len

    def set_event_id(self, event_id):
        # aklog_printf("%s,set_event_id" % (self.__class__.__name__));
        self.__event_id = event_id

    def get_event_id(self):
        # aklog_printf("%s,get_event_id" % (self.__class__.__name__));
        return self.__event_id

    def set_mothod(self, mothod):
        # aklog_printf("%s,set_mothod" % (self.__class__.__name__));
        self.__mothod = mothod

    def get_mothod(self):
        # aklog_printf("%s,get_mothod" % (self.__class__.__name__));
        return self.__mothod

    def set_recv_event_id(self, recv_event_id):
        # aklog_printf("%s,set_recv_event_id" % (self.__class__.__name__));
        self.__recv_event_id = recv_event_id

    def get_recv_event_id(self):
        # aklog_printf("%s,get_recv_event_id" % (self.__class__.__name__));
        return self.__recv_event_id

    def set_data(self, data):
        # aklog_printf("%s,set_data :%s" % (self.__class__.__name__, data));
        self.__data = data

    def get_data(self):
        # aklog_printf("%s,get_data" % (self.__class__.__name__));
        return self.__data

    def set_check(self, check):
        # aklog_printf("%s,set_check :%s" % (self.__class__.__name__, data));
        self.__check = check

    def get_check(self):
        # aklog_printf("%s,get_check" % (self.__class__.__name__));
        return self.__check

    def set_end(self, end):
        # aklog_printf("%s,set_end :%s" % (self.__class__.__name__, data));
        self.__end = end

    def get_end(self):
        # aklog_printf("%s,get_end" % (self.__class__.__name__));
        return self.__end

    # 简易的解包函数


def akipc_msg_unpack(str_data):
    aklog_printf("akipc_msg_unpack")
    # s = len(str_data)
    fmt = "!BBBB%dsBB" % (str_data[content_len_index] - package_content_len_without_data)
    return struct.unpack(fmt, str_data)
