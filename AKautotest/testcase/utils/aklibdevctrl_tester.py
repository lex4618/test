#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import io
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
from aklibdevctrl import *


# 用于控制测具的动作，主要有普通IO口的设置\获取，继电器控制，音频采集、通信总线交互，每个实例类需要根据硬件接法进行适配
class akdevctrl_tester(akdevctrl):
    # def __init__(self):
    #     aklog_printf("%s,__init__" % self.__class__.__name__)

    # def __del__(self):
    #     print("__del__")

    # 检查发送数据给测具后测试的ACK
    def check_ack(self, id, str_data):
        r = False
        if str_data != "":
            head, recv_len, event_id, recv_event_id, data, recv_check, end = akipc_msg_unpack(str_data)
            if head != package_head:
                aklog_printf("Receiving Package Header Error")
                return False

            if end != package_end:
                aklog_printf("Receiving Package End Error")
                return False

            check = recv_len ^ event_id ^ recv_event_id
            if data != "":
                for i in data:
                    check = check ^ i

            if check != recv_check:
                aklog_printf("check Error")
                return False

            if recv_event_id != id:
                aklog_printf("receive event != send event")
                return False

            if event_id == response_nack:
                aklog_printf('response NACK')
                return False
            elif event_id == response_ack:
                aklog_printf('response ACK')
                return True

    '''
    #检查向测具获取数据后的有效性
    def check_result(self, id, str_data):
        r = False;
        if str_data != "":
            t = akipc_msg_unpack(str_data);
            #aklog_printf("%d,%d,%d,%d,%d,%s" % (lid,state,param1,param2,len,bdata));
            aklog_printf(t);

            if t[0] != id or t[1] != dev_state_output:
                r = False;
            else:
                r = t;

        return r;
    '''

    # 设置音频通道采集切换
    def set_audio_level(self, index, data, retry_counts=3):
        """
        控制测具发送音频信号并检测信号结果
        :param index: 通道序号，用来判断是哪个通道发送的信号，0表示通道1, 1表示通道2，以此类推
        :param data: bytes类型，发送给测具的数据，
        比如：b'\x00\x01\x03\xe8'，x00表示通道1，x01表示通道2，x03和xe8表示发送的音频信号频率1KHZ
        这个data的意思是：python模拟udp客户端，发送udp包控制测具的通道1的SPK发送1KHZ音频信号给设备1的MIC，
        设备2的SPK会播放这个信号（通话正常时播放），测具的通道2的MIC接收到设备2的SPK发过来的信号，
        测具会将接收到的信号返回udp包给python的udp客户端，然后就可以判断该信号是否正常了
        :param retry_counts:
        :return:
        """
        aklog_printf("set_audio_level, index: %s, data: %s" % (index, data))

        id = dev_id_audio1 + int(index)
        str_data = self.data_set(id, data, method_audio_set, retry_counts)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(id, str_data)
        if not r:
            aklog_printf("set_audio_level failed!")

        return r

    # 设置bellin输出
    def set_bellin_data(self, mathod, data):
        aklog_printf("%s,set_bellin_data" % self.__class__.__name__)

        str_data = self.data_set(dev_id_bellin, data, mathod)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(dev_id_bellin, str_data)
        if not r:
            aklog_printf("set_bellin_data failed!")

        return r

    # 控制RS485输出数据
    def sendto_rs485(self, data):
        aklog_printf("%s,sendto_rs485" % self.__class__.__name__)

        str_data = self.data_set(dev_id_rs485, data, method_rs485_send)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(dev_id_rs485, str_data)
        if not r:
            aklog_printf("sendto_rs485 failed!")

        return r

        # 获取RS485接收的数据

    def recvfrom_rs485(self):
        aklog_printf("%s,recvfrom_rs485" % self.__class__.__name__)

        str_data = self.data_set(dev_id_rs485, "", method_rs485_recv)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(dev_id_rs485, str_data)
        if not r:
            aklog_printf("recvfrom_rs485 failed!")

        return r

    # 控制RS485输出数据
    def send_recv_rs485(self, data):
        aklog_printf("%s,send_recv_rs485" % self.__class__.__name__)

        str_data = self.data_set(dev_id_rs485, data, method_rs485_send_recv)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(dev_id_rs485, str_data)
        if not r:
            aklog_printf("send_recv_rs485 failed!")

        return r

        # 设置八防区通道状态

    def set_alarm_state(self, index, method, data):
        aklog_printf("%s,set_alarm_state" % self.__class__.__name__)

        id = dev_id_alarm1 + index
        str_data = self.data_set(id, data, method)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(id, str_data)
        if not r:
            aklog_printf("set_alarm_state failed!")

        return r

        # 设置继电器的状态

    def set_relay_level(self, index, method, data):
        aklog_printf("%s,set_relay_level" % self.__class__.__name__)

        id = dev_id_relay1NO + index
        str_data = self.data_set(id, data, method)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(id, str_data)
        if not r:
            aklog_printf("set_relay_level failed!")

        return r

        # 设置继电器的状态

    def get_relay_level(self, index, method):
        aklog_printf("%s,get_relay_level" % self.__class__.__name__)
        id = dev_id_relay1NO + index
        str_data = self.data_set(id, "", method)
        aklog_printf("str_data:%s" % str_data)
        r = self.check_ack(id, str_data)
        if not r:
            aklog_printf("set_relay_level failed!")
        relay_level = str_data[-3]
        aklog_printf('r: %s, relay_level: %s' % (r, relay_level))
        return r, relay_level

    '''
    # 设置继电器COM脚的状态
    def set_relayCOM_level(self, level):
        aklog_printf("%s,set_relayCOM_level" % (self.__class__.__name__));

        str_data = self.io_set(dev_id_relayCOM, level);
        aklog_printf("str_data:%s" % str_data);

        r = self.check_ack(dev_id_relayCOM, str_data);
        if not r:
            aklog_printf("set failed!");

        return r; 
    '''

    # 控制I2C发送数据
    def sendto_iic(self, index, data):
        aklog_printf("%s,set_audio_level" % self.__class__.__name__)

        id = dev_id_iic1 + index
        str_data = self.com_set(id, data)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(id, str_data)
        if not r:
            aklog_printf("set failed!")

        return r

        # 控制SPI发送数据

    def sendto_spi(self, index, data):
        aklog_printf("%s,set_audio_level" % self.__class__.__name__)

        id = dev_id_spi1 + index
        str_data = self.com_set(id, data)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(id, str_data)
        if not r:
            aklog_printf("set failed!")

        return r

        # 控制串口发送数据

    def sendto_uart(self, index, data):
        aklog_printf("%s,set_audio_level" % self.__class__.__name__)

        id = dev_id_uart1 + index
        str_data = self.com_set(id, data)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(id, str_data)
        if not r:
            aklog_printf("set failed!")

        return r

        # 控制IO输出口电平状态

    def set_io_level(self, index, level):
        aklog_printf("%s,set_audio_level" % self.__class__.__name__)

        id = dev_id_io_output1 + index
        str_data = self.io_set(id, level)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(id, str_data)
        if not r:
            aklog_printf("set failed!")

        return r

        # 获取IO电平状态

    def get_io_level(self, index, level):
        aklog_printf("%s,set_audio_level" % self.__class__.__name__)
        id = dev_id_io_input1 + index
        str_data = self.io_set(id, level)
        aklog_printf("str_data:%s" % str_data)

        r = self.check_ack(id, str_data)
        if not r:
            aklog_printf("set failed!")

        return r

    # 设置stm32mode
    def set_stm32_mode(self, data):
        aklog_printf("%s,set_stm32_mode" % self.__class__.__name__)
        id = dev_id_stm32mode
        str_data = self.data_set(id, data, method_stm32mode_set)
        aklog_printf("str_data:%s" % str_data)
        r = self.check_ack(id, str_data)
        if not r:
            aklog_printf("set_stm32_mode failed!")

        return r

# '''demo'''
#
# dev_tester = akdevctrl_tester();
# r = dev_tester.creat("192.168.12.63", 10);
# if not r :
#     aklog_printf("tester connect failed!");
# #r = dev_tester.set_stm32_mode(1);
# r = dev_tester.set_audio_level(0, bytes([0x00,0x00, 0x3, 0xe8]));
# r= dev_tester.set_alarm_state(1,1,1);
# print(r);
