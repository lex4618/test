# -*- coding: UTF-8 -*-
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
from . import Web, Base

__all__ = [
    'WebLinuxDoor',
    'WebLinuxInDoor',
    'BaseLinuxDoor'
]


class WebLinuxDoor(Web):
    """
    嵌入式门口机, 网页接口统一命名.
    ps: 自动化人员维护.
    """

    def __init__(self, webObj):
        super().__init__(webObj)


class WebLinuxInDoor(Web):
    """
    嵌入式室内机, 网页接口统一命名.
    ps: 自动化人员维护.
    """

    def __init__(self, webObj):
        super().__init__(webObj)

    def web_enter_call_feature(self):
        """features->feature"""
        self.enter_web_phone_call_feature()


class BaseLinuxDoor(Base):
    """
    嵌入式门口机, 终端接口统一命名.
    ps: 自动化人员维护.
    """

    def __init__(self, baseObj):
        super().__init__(baseObj)
    def return_home_page(self):
        self.hang_up_call()

class BaseAndroidDoor(Base):
    def callout(self, number):
        return self.ui_callout(number)
