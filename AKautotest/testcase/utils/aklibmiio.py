# -*- coding: UTF-8 -*-

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
import traceback
import time
from miio.device import Device


class MiioDev:

    def __init__(self, ip=None, token=None, device_name=''):
        """
        构造函数，初始化miio变量
        ip 小米智能插座ip
        token 小米智能插座token
        获取token方法：将插座添加到米家APP，然后通过miiocli cloud命令（需要输入米家的用户名密码），可以获取到该米家帐号下所有设备信息
        """
        self.ip = ip
        self.token = token
        self.device_name = device_name
        self.device: Optional[Device] = None
        if self.ip and self.token:
            self.device = Device(ip, token)

    def init(self, device_info):
        self.ip = device_info.get('ip')
        self.token = device_info.get('token')
        self.device_name = device_info.get('device_name') or ''
        self.device = Device(self.ip, self.token)

    def plug_on(self, times=10):
        """控制小米插座开"""
        for i in range(times):
            try:
                self.device.send("set_properties", [{'did': 'MYDID', 'siid': 2, 'piid': 1, 'value': True}])
                aklog_debug("插座已开启")
                return True  # 如果成功，则退出循环
            except:
                aklog_debug(f"重试{i + 1}次失败：" + str(traceback.format_exc()))
                if i == times - 1:
                    aklog_debug("重试结束，插座开启失败")
        return False

    def plug_off(self, times=10):
        """控制小米插座关"""
        for i in range(times):
            try:
                self.device.send("set_properties", [{'did': 'MYDID', 'siid': 2, 'piid': 1, 'value': False}])
                aklog_debug("插座已关闭")
                return True  # 如果成功，则退出循环
            except:
                aklog_debug(f"重试{i + 1}次失败：" + str(traceback.format_exc()))
                if i == times - 1:
                    aklog_debug("重试结束，插座关闭失败")
        return False

    def plug_delay_on(self, wait_time=5, times=10):
        """控制小米插座关后延时时间开"""
        self.plug_off(times)
        time.sleep(wait_time)
        self.plug_on(times)

    def plug_delay_off(self, wait_time=5, times=10):
        self.plug_on(times)
        time.sleep(wait_time)
        self.plug_off(times)


if __name__ == '__main__':
    print('测试代码')
    miio_dev = MiioDev("192.168.88.199", "a3efd69ca3e56e79a1b2b51d02372b61")  # 根据实际小米插座ip、token
    miio_dev.plug_delay_on()
