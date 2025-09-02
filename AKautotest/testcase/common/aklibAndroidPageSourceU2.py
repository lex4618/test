# -*- coding: utf-8 -*-

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
from testcase.common.aklibAndroidBaseU2 import AndroidBaseU2
from libconfig.COMMON.libconfig_NORMAL import config_NORMAL
from typing import Optional
import itertools


class ElementAdapterU2(object):

    def __call__(self, **kwargs):
        return kwargs

    @staticmethod
    def xpath(xpath) -> str:
        return xpath


class AndroidPageSourceU2(object):
    """
    页面元素信息
    如果不同机型同一个元素的属性不同，那么可以继承重写该类，然后在base模块的__init__里面添加对应机型的PageSource实例即可
    """

    element_adapter = ElementAdapterU2()

    def __init__(self):
        """
        在init里面写元素信息
        元素控件命名规范： 控件名_控件类型
        按钮的类型： btn，输入框类型： edit，文本类型： text，列表类型： list

        元素信息格式： 支持resourceId， text, xpath等多种方式，text、resourceId和Xpath可以直接传入str类型
        如果是U2的格式，则可以直接从weditor复制过来
        例如：
        d(resourceId="com.akuvox.belahome:id/iv_login_qrcode")
        d(text="HyPanel012400")
        d(resourceId="android:id/title", text="HyPanel012400")
        d.xpath('//*[@resource-id="android:id/content"]/android.widget.RelativeLayout[1]')
        '//*[@resource-id="android:id/content"]/android.widget.RelativeLayout[1]'  # 直接传入xpath，str类型
        'HyPanel012400'  # 直接传入text文本，str类型
        'com.akuvox.belahome:id/iv_login_qrcode'  # 直接传入元素id，str类型

        如果要定位多个id或name组合后的，可以传入元组类型，主要用于不同机型或版本的元素id不一致时作兼容
        例如：
        (d(resourceId="com.akuvox.belahome:id/tv_login"), d(resourceId="com.akuvox.belahome:id/iv_login"))

        继承该类时使用方法：
        def __init__(self):
            super().__init__()
            d = ElementAdapterU2()
        """
        self.app: Optional[AndroidBaseU2] = None
        self.device_config: Optional[config_NORMAL] = None
        self.device_name = ''
        self.device_id = ''
        self.screen_width = 0
        self.screen_height = 0
        self.screen_clickable_area = None

    def init(self, app: Optional[AndroidBaseU2] = None):
        if app is not None:
            self.app = app
        self.device_name = getattr(self.app, 'device_name', '')
        self.device_config = self.app.get_device_config()
        self.screen_width = self.device_config.get_screen_width()
        self.screen_height = self.device_config.get_screen_height()
        self.screen_clickable_area = self.device_config.get_screen_clickable_area()

    def screen_shot(self):
        self.app.screen_shot()

    def get_translations(self, key, default=None, add_warn=False):
        """
        获取翻译词条
        Args:
            key (str): 原始词条名称
            default (str): 如果为空，则默认使用英语词条
            add_warn (bool): 是否添加警告
        """
        try:
            cur_lang = self.app.get_device_language(regain=False)
            translations = self.app.get_translations()
            value = None
            if translations:
                value = translations.get(key)
            if value:
                return value
            if default:
                if add_warn:
                    unittest_results(
                        ['warn', f'当前语言 {cur_lang} 缺少词条key: {key}, 使用默认翻译: {default}'])
                return default

            en_translations = self.app.get_translations('en')
            if en_translations:
                value = en_translations.get(key)
            if value:
                if add_warn:
                    unittest_results(
                        ['warn', f'当前语言 {cur_lang} 缺少词条key: {key}, 使用英文词条翻译: {value}'])
                return value

            # 如果仍为空，则将key作为英语词条，反向查找原始词条
            matching_keys = [k for k, v in en_translations.items() if v == key]  # 获取所有匹配的 key

            # 创建循环迭代器
            key_iterator = itertools.cycle(matching_keys) if matching_keys else None

            # 获取下一个 key
            if key_iterator:
                for i in range(len(matching_keys)):
                    key1 = next(key_iterator)
                    if translations:
                        value = translations.get(key1)
                    if value:
                        if add_warn:
                            unittest_results(
                                ['warn',
                                 f'当前语言 {cur_lang} 缺少词条key: {key}, 将key作为英语词条反向查找翻译: {value}'])
                        return value
            if add_warn:
                unittest_results(
                    ['warn', f'当前语言 {cur_lang} 缺少词条key: {key}, 直接将key作为英语词条翻译: {key}'])
            return key
        except Exception as e:
            unittest_results([False, f'获取词条 {key} 失败: {e}'])
            return None

    def get_device_language(self):
        return self.app.get_device_language()

    @property
    def user_info(self) -> dict:
        return self.app.user_info

    @user_info.setter
    def user_info(self, value):
        if self.app:
            self.app.user_info = value

    @property
    def device_fullname(self):
        return f'[{self.device_name}]'

    def wait_visible(self, locator, time_metrics=2, timeout=10):
        """增加性能指标，检查元素是否在指定的时间内加载完成"""
        if not self.app.wait_visible(
                locator, timeout=time_metrics):
            unittest_add_results(['warn', f'时间指标 {time_metrics} 秒之内没有显示 {locator}'], self)
            if not self.app.wait_visible(
                    locator, timeout=timeout):
                unittest_add_results([False, f'再等10秒仍没有显示 {locator}'], self)
                return False
        return True
