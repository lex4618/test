#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import io
import sys
import os
import binascii

root_path = os.getcwd()
pos = root_path.find("AKautotest")

if pos == -1:
    print("runtime error")
    exit(1)

root_path = root_path[0:pos + len("AKautotest")]

sys.path.append(root_path)

import akcommon_define
from akcommon_define import *

# ### source code ##### #

package_head = 0xaa
package_end = 0xbb

response_ack = 0xfb
response_nack = 0xfc

low = 0
high = 1

package_content_len_without_data = 4

method_bellin_set = 1
method_bellin_highpuls = 2
method_bellin_lowpuls = 3
method_rs485_send = 1
method_rs485_recv = 2
method_rs485_send_recv = 3
method_alarm_set = 1
method_alarm_puls_low = 2
method_alarm_puls_high = 3
method_alarm_period = 4
method_relay_set = 1
method_relay_get = 2
method_audio_set = 1
method_stm32mode_set = 1

# 类型ID定义，作为通信的唯一区别，相关数据类型也跟随固定，在不同测试下可以通过如下宏进行重定义来提高阅读性

dev_id_bellin = 1
dev_id_rs485 = 2
dev_id_alarm1 = 3
dev_id_alarm2 = 4
dev_id_alarm3 = 5
dev_id_alarm4 = 6
dev_id_alarm5 = 7
dev_id_alarm6 = 8
dev_id_alarm7 = 9
dev_id_alarm8 = 10
dev_id_audio1 = 14
dev_id_audio2 = 15
dev_id_audio3 = 16
dev_id_audio4 = 17
dev_id_audio5 = 18
dev_id_audio6 = 19
dev_id_audio7 = 20
dev_id_audio8 = 21
dev_id_audio9 = 22
dev_id_audio10 = 23
dev_id_audio11 = 24
dev_id_audio12 = 25
dev_id_iic1 = 26
dev_id_iic2 = 27
dev_id_iic3 = 28
dev_id_iic4 = 29
dev_id_spi1 = 30
dev_id_spi2 = 31
dev_id_spi3 = 32
dev_id_spi4 = 33
dev_id_uart1 = 34
dev_id_uart2 = 35
dev_id_uart3 = 36
dev_id_uart4 = 37
dev_id_io_output1 = 38
dev_id_io_output2 = 39
dev_id_io_output3 = 40
dev_id_io_output4 = 41
dev_id_io_output5 = 42
dev_id_io_output6 = 43
dev_id_io_output7 = 44
dev_id_io_output8 = 45
dev_id_io_output9 = 46
dev_id_io_output10 = 47
dev_id_io_output11 = 48
dev_id_io_output12 = 49
dev_id_io_output13 = 50
dev_id_io_output14 = 51
dev_id_io_output15 = 52
dev_id_io_output16 = 53
dev_id_io_output17 = 54
dev_id_io_output18 = 55
dev_id_io_output19 = 56
dev_id_io_output20 = 57
dev_id_io_input1 = 58
dev_id_io_input2 = 59
dev_id_io_input3 = 60
dev_id_io_input4 = 61
dev_id_io_input5 = 62
dev_id_io_input6 = 63
dev_id_io_input7 = 64
dev_id_io_input8 = 65
dev_id_io_input9 = 66
dev_id_io_input10 = 67
dev_id_io_input11 = 68
dev_id_io_input12 = 69
dev_id_io_input13 = 70
dev_id_io_input14 = 71
dev_id_io_input15 = 72
dev_id_io_input16 = 73
dev_id_io_input17 = 74
dev_id_io_input18 = 75
dev_id_io_input19 = 76
dev_id_io_input20 = 77
dev_id_relay1NO = 78
dev_id_relay1NC = 79
dev_id_relay1COM = 80
dev_id_relay2NO = 81
dev_id_relay2NC = 82
dev_id_relay2COM = 83
dev_id_relay3NO = 84
dev_id_relay3NC = 85
dev_id_relay3COM = 86
dev_id_relay4NO = 87
dev_id_relay4NC = 88
dev_id_relay4COM = 89
dev_id_stm32mode = 90

dev_state_output = 1
dev_state_input = 0


# 用于控制测具的动作，主要有普通IO口的设置\获取，继电器控制，音频采集、通信总线交互，每个实例类需要根据硬件接法进行适配
class akdevctrl(object):
    __port = 190

    def __init__(self):
        aklog_printf("%s,__init__" % self.__class__.__name__)
        self.__udp_client = None

    def __del__(self):
        print("%s,__del__" % self.__class__.__name__)
        if not self.__udp_client:
            del self.__udp_client

    # 创建UDP 连接
    def creat(self, ip, timeout):
        self.__udp_client = akudp_client(ip, self.__port, 1500, timeout)
        r = self.__udp_client.creat()
        return r

    # IO 电平类型的控制
    def data_set(self, id, data, mothod, retry_counts=3):
        aklog_printf("data_set, id: %s, data: %s, mothod: %s" % (id, data, mothod))
        if data != "":
            if isinstance(data, int):
                data = six.int2byte(data)
            elif isinstance(data, str):
                data = bytes(data, encoding="utf8")
        msg = akipc_msg_parse()
        msg.set_head(package_head)
        content_len = package_content_len_without_data + len(data)
        msg.set_len(content_len)
        msg.set_event_id(id)
        msg.set_mothod(mothod)
        check = content_len ^ id ^ mothod
        if data != "":
            msg.set_data(data)
            for i in data:
                check = check ^ i
        msg.set_check(check)
        msg.set_end(package_end)
        send_package = msg.pack()

        recv_package = ''
        for i in range(retry_counts):
            recv_package = self.__udp_client.send_recv(send_package)
            if recv_package != '':
                break

        return recv_package

    # IO 电平类型的控制
    def audio_set(self, id, data, mothod):
        aklog_printf("audio_set, id: %s, data: %s, mothod: %s" % (id, data, mothod))

        msg = akipc_msg_parse()
        msg.set_head(package_head)
        content_len = package_content_len_without_data + 4
        msg.set_len(content_len)
        msg.set_event_id(id)
        msg.set_mothod(mothod)
        check = content_len ^ id ^ mothod
        D = data & 0xff
        C = (data >> 8) & 0xff
        B = (data >> 16) & 0xff
        A = (data >> 24) & 0xff

        check = check ^ A ^ B ^ C ^ D

        msg.set_data(data)
        msg.set_check(check)
        msg.set_end(package_end)
        send_package = msg.pack()
        print("send_package = ", send_package)
        recv_package = ''
        for i in range(3):
            recv_package = self.__udp_client.send_recv(send_package)
            if recv_package != '':
                break

        return recv_package

    '''
    #通信总线数据输出
    def com_set(self, id, data):
        aklog_printf("%s,com_set" % (self.__class__.__name__));
        msg = akipc_msg_parse();
        msg.set_id(id);
        msg.set_state(dev_state_output);
        msg.set_data(data);
        str = msg.pack();

        for i in range(3):
            data = self.__udp_client.send_recv(str);
            if data != '':
                break;

        return data;
    
    #获取IO 状态或总线数据
    def get(self, id):
        aklog_printf("%s,com_get" % (self.__class__.__name__));
        msg = akipc_msg_parse();
        msg.set_id(id);
        msg.set_state(dev_state_input);
        str = msg.pack();

        for i in range(3):
            data = self.__udp_client.send_recv(str);
            if data != '':
                break;

        return data;
    '''
