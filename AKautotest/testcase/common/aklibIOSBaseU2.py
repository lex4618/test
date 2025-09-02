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
from testcase.utils.aklibLog import *
from libconfig.COMMON.libconfig_NORMAL import config_NORMAL
from testcase.utils.aklibImage_process import ImageProcessIOS
import wda
import time
import traceback
from typing import Union, Optional, List
from wda import Selector, Element


class IOSBaseU2(object):

    # region iOS设备连接初始化
    def __init__(self, device_info=None, device_config=None, wait_time=2):
        self.driver: Optional[wda.Client] = None
        self._imgs = []
        self.image: Optional[ImageProcessIOS] = None
        self.device_config: Optional[config_NORMAL] = None
        self.device_info = None
        self.user_info = {}
        self.translations = {}
        self.language = 'en'
        self.device_id = ''
        self.device_name = ''
        self.port = ''
        self.wda_name = ''
        self.device_name_log = ''
        self.wait_time = wait_time
        self.screen_width = 0
        self.screen_height = 0
        self.screen_clickable_area = None
        self.web_driver_port = config_get_wda_port()
        self.web_driver = None  # webview相关
        self.init(device_info, device_config)

    def init(self, device_info=None, device_config=None):
        if device_info:
            self.device_info = device_info
            self.device_id = self.device_info['deviceid']
            self.wda_name = self.device_info['wda_name']
            # self.port = self.device_info['port']
            self.device_name = self.device_info['device_name']
            self.device_name_log = '[' + self.device_name + '] '
        if device_config:
            self.device_config = device_config
            self.screen_width = self.device_config.get_screen_width()
            self.screen_height = self.device_config.get_screen_height()
            self.screen_clickable_area = self.device_config.get_screen_clickable_area()
            if self.device_name and not self.device_config.get_device_name():
                self.device_config.put_device_name(self.device_name)

    def u2_connect_iOS(self):
        self.driver = wda.Client('http://localhost:%s' % self.web_driver_port)  # 该地址为weditor中连接真机的ip
        self.image = ImageProcessIOS(self.driver, self.device_name)

    def connect_wda(self):
        # 由于多次执行该命令会导致冲突，只需要首次执行，该方法还需要完善
        aklog_debug()
        commandConnect = f'tidevice -u {self.device_id} wdaproxy -B {self.wda_name} --port {self.web_driver_port}'
        subprocess.Popen(commandConnect, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def get_ios_product_version(self):
        command = 'tidevice -u %s info' % self.device_id
        input_string = sub_process_get_output(command)
        match = re.search(r'ProductVersion:\s*([\d.]+)', input_string)

        if match:
            product_version = match.group(1)
            aklog_debug("ProductVersion:%s" % product_version)
            version_parts = product_version.split('.')
            major_version = int(version_parts[0])
            if major_version >= 17:
                return True
            else:
                return False
        else:
            aklog_error("ProductVersion not found")

    def u2_connect_iOS17(self):
        self.driver = wda.Client('http://localhost:%s' % self.web_driver_port)  # 该地址为weditor中连接真机的ip
        self.image = ImageProcessIOS(self.driver, self.device_name)

    @staticmethod
    def tunnel_start():
        aklog_debug()
        commandConnect = 'ios tunnel start'
        subprocess.Popen(commandConnect, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def connect_wda_ios17(self):
        aklog_debug()
        commandConnect = (f'ios runwda --udid={self.device_id} --bundleid={self.wda_name} '
                          f'--testrunnerbundleid={self.wda_name} '
                          '--xctestconfig=WebDriverAgentRunner.xctest')
        aklog_debug(commandConnect)
        subprocess.Popen(commandConnect, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def forwarding_port(self):
        aklog_debug()
        commandConnect = 'ios --udid=%s forward %s 8100' % (self.device_id, self.web_driver_port)
        aklog_debug(commandConnect)
        subprocess.Popen(commandConnect, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def __EnvSetup_17(self):
        command = 'curl -X GET http://localhost:%s/status' % self.web_driver_port
        ret = sub_process_get_output(command)
        if ret and 'WebDriverAgent is ready to accept commands' in ret:
            aklog_debug('WebDriverAgent已启动')
            return True
        else:
            aklog_debug('WebDriverAgent端口未启动: %s' % self.web_driver_port)
            return False

    def AppRun_17(self):
        for i in range(2):
            ret = self.__EnvSetup_17()
            if not ret:
                if i == 0:
                    aklog_debug('环境未准备完成, 重试')
                    self.tunnel_start()
                    time.sleep(5)
                    self.connect_wda_ios17()
                    time.sleep(5)
                    self.forwarding_port()
                    time.sleep(5)
                    continue
                aklog_debug('环境未准备完成, 无法继续测试, 异常退出!')
                param_put_failed_to_exit_enable(True)
                return False
            else:
                aklog_debug('环境准备完成')
                self.u2_connect_iOS17()
                self.get_device_language()
                return True

    def __EnvSetup(self):
        command = 'curl -X GET http://localhost:%s/status' % self.web_driver_port
        ret = sub_process_get_output(command)

        if ret and 'WebDriverAgent is ready to accept commands' in ret:
            aklog_debug('WebDriverAgent已启动')
            return True
        else:
            aklog_debug('WebDriverAgent端口未启动: %s' % self.web_driver_port)
            return False

    def AppRun(self):
        for i in range(2):
            ret = self.__EnvSetup()
            if not ret:
                if i == 0:
                    aklog_debug('环境未准备完成, 重试')
                    self.connect_wda()
                    time.sleep(10)
                    continue
                aklog_debug('环境未准备完成, 无法继续测试, 异常退出!')
                param_put_failed_to_exit_enable(True)
                return False
            else:
                aklog_debug('环境准备完成')
                self.u2_connect_iOS()
                self.get_device_language()
                return True

    def web_driver_quit(self):
        self.web_driver.quit()

    def get_device_info(self):
        return self.device_info

    def get_device_config(self):
        return self.device_config

    def put_device_id(self, device_id):
        self.device_id = device_id

    def put_translations(self, language, translations: dict):
        self.translations[language] = translations

    def get_translations(self, language=None) -> dict:
        """获取当前语言的词条文件"""
        if language:
            return self.translations.get(language)
        elif self.language:
            return self.translations.get(self.language)
        else:
            return self.translations.get('en')

    def put_user_info(self, user_info: dict):
        self.user_info.clear()
        self.user_info.update(user_info)

    def get_user_info(self) -> dict:
        """获取当前语言的词条文件"""
        return self.user_info

    # 截图储存list
    def reset_imgs(self):
        self._imgs = []
        param_reset_screenshots_imgs()

    def get_imgs(self):
        return self._imgs

    # endregion

    # region APP打开关闭

    def get_current_package(self):
        aklog_debug('get_current_package')
        try:
            current_package = self.driver.app_current().get('package')
            aklog_debug('current_package: %s' % current_package)
            return current_package
        except:
            aklog_debug('get current package failed, %s' % traceback.format_exc())
            return None

    def active_app(self, app_package):
        aklog_debug()
        try:
            self.driver.app_start(app_package)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def stop_app(self, app_package):
        """关闭APP"""
        aklog_debug()
        try:
            self.driver.app_stop(app_package)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def swipe_down_from_top(self):
        """原生系统下滑查看通知"""
        aklog_debug()
        w, h = self.driver.window_size()
        try:
            self.driver.swipe(1, 1, 1, h - 1)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def deactivate(self, duration):
        """退到后台一定时间再拉起来"""
        aklog_debug()
        try:
            self.driver.deactivate(duration)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    # endregion

    # region go-ios命令

    def get_device_language(self, regain=True):
        """获取手机设备语言"""
        if not regain:
            return self.language
        out = sub_process_get_output(f'ios lang --udid {self.device_id}', get_err=False)
        if not out or not out.strip():
            aklog_warn('获取设备语言失败')
            return None
        json = json_loads_2_dict(out)
        language = json.get('Language')
        if language and '-' in language:
            language = language.split('-')[0]
        aklog_debug(f'language: {language}')
        self.language = language
        return language

    # endregion

    # region 屏幕相关操作

    def get_screen_power_status(self):
        try:
            screen_power_status = self.driver.info.get('screenOn')
            aklog_debug('screen_power_status: %s' % screen_power_status)
            return screen_power_status
        except:
            aklog_debug(traceback.format_exc())
            return None

    # endregion

    # region 实体按键操作

    def press_key(self, key_code):
        aklog_debug('press_key %s' % key_code)
        try:
            self.driver.press(key_code)
            return True
        except:
            aklog_debug('press_key %s failed' % key_code)
            return False

    def press_key_home(self):
        aklog_debug()
        try:
            self.driver.press('home')
            time.sleep(1)
            return True
        except:
            aklog_debug('press_key_home failed')
            return False

    def press_key_back(self):
        aklog_debug()
        try:
            self.driver.press('back')
            time.sleep(1)
            return True
        except:
            aklog_debug('press_key_back failed')
            return False

    def press_key_power(self):
        aklog_debug()
        try:
            self.driver.press('power')
            time.sleep(1)
            return True
        except:
            aklog_debug('press_key_power failed')
            return False

    # endregion

    # region 元素定位，是否可见或消失

    def find_element(self, locator: dict or str or tuple, get_ele=False, exists=True, timeout=None,
                     print_trace=False) -> Union[Selector, Element, None]:
        """
        获取元素
        locator: 元素定位信息，支持resourceId， text, xpath等多种方式，text、resourceId和Xpath可以直接传入str类型
        但建议从weditor复制过来，封装到PageSource类里面，通过ElementAdapterU2转换
        可以参考：testcase/module/AkuBelaHome/V3_0/Base/PageSource/libLoginPageSource_BELAHOME_NORMAL.py
        例如：
        d(resourceId="com.akuvox.belahome:id/iv_login_qrcode")
        d(text="HyPanel012400")
        d(resourceId="android:id/title", text="HyPanel012400")
        d.xpath('//*[@resource-id="android:id/content"]/android.widget.RelativeLayout[1]')
        '//*[@resource-id="android:id/content"]/android.widget.RelativeLayout[1]'  # 直接传入xpath，str类型
        'HyPanel012400'  # 直接传入text文本，str类型
        'com.akuvox.belahome:id/iv_login_qrcode'  # 直接传入元素id，str类型
        如果要定位多个id或name组合后的，可以传入元组类型，主要用于不同机型或版本的元素id不一致时作兼容
        PageSource类填写的格式:
        (d(resourceId="com.akuvox.belahome:id/tv_login"), d(resourceId="com.akuvox.belahome:id/iv_login"))
        转换后传入的格式:
        ({'resourceId': 'com.akuvox.belahome:id/tv_login'}, {'resourceId': 'com.akuvox.belahome:id/iv_login'})

        get_ele: locator为xpath方式时才会用到，返回XMLElement类，主要用于获取Xpath元素的属性信息
        timeout: 等待元素出现的超时时间
        """
        try:
            if timeout is None:
                timeout = self.wait_time

            if isinstance(locator, dict):
                selector = self.driver(**locator)
            elif isinstance(locator, tuple):
                # 如果locator是元组类型，则表示多个id或者name（or关系）同时查找，要转换成xpath
                xpath = self.xpath_adapter(*locator)
                selector = self.driver.xpath(xpath)  # 返回Selector对象
            elif isinstance(locator, str) and locator.startswith('//'):
                # //开头表示xpath方式
                selector = self.driver.xpath(locator)  # 返回Selector对象
            else:
                # 直接传入元素label(name)来定位
                selector = self.driver(label=locator)

            if exists:
                # 查找元素是否存在
                ele = selector.wait(timeout=timeout)  # 返回Element对象
                if ele is not None:
                    if get_ele:
                        return ele
                    return selector
                aklog_debug(f'{locator} not found')
                return None
            else:
                # 查找元素是否消失
                ret = selector.wait_gone(timeout=timeout)  # 返回bool
                return ret
        except Exception as e:
            aklog_error(e)
            if print_trace:
                aklog_debug(traceback.format_exc())
            return None

    def find_elements(self, locator: dict or str or tuple, print_trace=False) -> List[Element]:
        """查找多个相同locator的元素，返回列表"""
        try:
            if isinstance(locator, dict):
                selector = self.driver(**locator)
            elif isinstance(locator, tuple):
                # 如果locator是元组类型，则表示多个id或者name（or关系）同时查找，要转换成xpath
                xpath = self.xpath_adapter(*locator)
                selector = self.driver.xpath(xpath)  # 返回Selector对象
            elif isinstance(locator, str) and locator.startswith('//'):
                # //开头表示xpath方式
                selector = self.driver.xpath(locator)  # 返回Selector对象
            else:
                # 直接传入元素label(name)来定位
                selector = self.driver(label=locator)
            elements = selector.find_elements()
            return elements
        except Exception as e:
            aklog_error(e)
            if print_trace:
                aklog_debug(traceback.format_exc())
            return []

    def get_element(self, locator, timeout=None, print_trace=False) -> Optional[Element]:
        """
        获取元素
        locator如果为xpath方式，返回XMLElement类，主要用于获取Xpath元素的属性信息
        """
        return self.find_element(locator, get_ele=True, timeout=timeout, print_trace=print_trace)

    def wait_visible(self, locator, timeout=5) -> bool:
        """等待元素出现"""
        aklog_debug()
        ele = self.find_element(locator, timeout=timeout)
        if ele is None:
            return False
        else:
            return True

    def wait_gone(self, locator, timeout=5) -> bool:
        """等待元素消失"""
        aklog_debug()
        ret = self.find_element(locator, exists=False, timeout=timeout)
        if not ret:
            aklog_debug(f'{locator} is not gone')
            return False
        return True

    def is_exists(self, locator) -> bool:
        """判断元素是否存在，不进行等待"""
        aklog_debug()
        try:
            if isinstance(locator, dict):
                selector = self.driver(**locator)
            elif isinstance(locator, tuple):
                # 如果locator是元组类型，则表示多个id或者name（or关系）同时查找，要转换成xpath
                xpath = self.xpath_adapter(*locator)
                selector = self.driver.xpath(xpath)  # 返回Selector对象
            elif isinstance(locator, str) and locator.startswith('//'):
                # //开头表示xpath方式
                selector = self.driver.xpath(locator)  # 返回Selector对象
            else:
                # 直接传入元素label(name)来定位
                selector = self.driver(label=locator)

            ret = selector.exists
            if not ret:
                aklog_debug(f'{locator} not found')
            return ret
        except Exception as e:
            aklog_error(e)
            return False

    @staticmethod
    def xpath_adapter(*locators):
        """
        多个id或者name，转换成xpath，主要用于不同机型或版本的元素id不一致时作兼容
        locators:
        PageSource类填写的格式:
        (d(resourceId="com.akuvox.belahome:id/tv_login"), d(resourceId="com.akuvox.belahome:id/iv_login"))
        转换后传入的格式:
        {'resourceId': 'com.akuvox.belahome:id/tv_login'}, {'resourceId': 'com.akuvox.belahome:id/iv_login'}
        """
        ele_xpath = '//*['
        for locator in locators:
            if 'resourceId' in locator:
                ele_xpath += '@resource-id="%s" or ' % locator['resourceId']
            elif 'text' in locator:
                ele_xpath += '@text="%s" or ' % locator['text']
            elif 'description' in locator:
                ele_xpath += '@text="%s" or ' % locator['description']
        ele_xpath = ele_xpath.rstrip(' or ') + ']'
        return ele_xpath

    # endregion

    # region 输入框相关

    def set_text(self, locator, content, click=False, clear=True, print_trace=False):
        """输入框输入文本"""
        aklog_debug()
        try:
            ele = self.get_element(locator, print_trace=print_trace)
            if ele is None:
                return False

            if click:
                ele.click()
                time.sleep(0.5)
            if clear:
                ele.clear_text()

            ele.set_text(content)
            time.sleep(0.2)
            return True
        except Exception as e:
            aklog_error(e)
            if print_trace:
                aklog_debug(traceback.format_exc())
            return False

    def input_edit_by_name(self, name, content):
        aklog_debug()
        try:
            ele = self.driver(text=name)
            ele.clear_text()
            ele.set_text(content)
            time.sleep(0.2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_edit_by_xpath(self, ele_xpath, content):
        aklog_debug()
        try:
            ele = self.driver.xpath(ele_xpath)
            ele.clear_text()
            ele.set_text(content)
            time.sleep(0.2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_content_by_xpath(self, ele_xpath, content):
        """输入前不清空，可以用于seekbar滚动条设置"""
        aklog_debug()
        try:
            ele = self.driver.xpath(ele_xpath)
            ele.set_text(content)
            time.sleep(0.2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_in_focused_edit(self, content):
        """在焦点输入框控件输入文本"""
        self.input_edit_by_xpath('.//android.widget.EditText[@focused="true"]', content)

    # endregion

    # region 点击操作

    def click_btn(self, locator, sec=0.2, timeout=None, print_trace=False):
        """点击元素"""
        aklog_debug()
        try:
            if not timeout:
                timeout = self.wait_time

            ele = self.get_element(locator, timeout=timeout, print_trace=print_trace)
            if ele is None:
                return False

            ele.click()
            time.sleep(sec)
            return True
        except Exception as e:
            aklog_error(e)
            if print_trace:
                aklog_debug(traceback.format_exc())
            return False

    def click_btn_location(self, locator, mid_x_length=0.5, mid_y_length=0.5, print_trace=False):
        """点击元素内的某个坐标点，有些元素中心点无法点击时，可以用该方法"""
        aklog_debug()
        try:
            ele = self.get_element(locator, print_trace=print_trace)
            if ele is None:
                return False

            x, y, width, height = ele.bounds
            ele_mid_x = x + width * mid_x_length
            ele_mid_y = y + height + mid_y_length
            self.driver.click(ele_mid_x, ele_mid_y)
            return True
        except Exception as e:
            aklog_error(e)
            if print_trace:
                aklog_debug(traceback.format_exc())
            return False

    def click_btn_out_location(self, locator, print_trace=False):
        """点击弹窗之外的地方来取消弹窗"""
        aklog_debug()
        try:
            # 先获取弹窗窗口的左上角坐标和尺寸
            ele_location = self.get_ele_location(locator)
            ele_width, ele_height = self.get_ele_size(locator)

            # 获取屏幕尺寸
            screen_width, screen_height = self.get_screen_size()

            # 先判断左右两边是否可以点击，如果左右两边都无法点击，则点击上下两边
            if ele_location['x'] > 1:
                x = int(ele_location['x'] / 2)
                y = int(screen_height / 2)
            elif ele_location['x'] + ele_width < screen_width - 1:
                x = ele_location['x'] + ele_width + int((screen_width - ele_location['x'] - ele_width) / 2)
                y = int(screen_height / 2)
            else:
                x = int(screen_width / 2)
                if ele_location['y'] > 1:
                    y = int(ele_location['y'] / 2)
                elif ele_location['y'] + ele_height < screen_height - 1:
                    y = ele_location['y'] + ele_height + int((screen_height - ele_location['y'] - ele_height) / 2)
                else:
                    y = 0
            aklog_debug('x: %s, y: %s' % (x, y))
            self.click_location(x, y)
            return True
        except Exception as e:
            aklog_error(e)
            if print_trace:
                aklog_debug(traceback.format_exc())
            return False

    def multi_click_btn(self, locator, times=1, interval=0.2, print_trace=False):
        """
        多次点击元素
        times: 点击次数
        interval: 间隔时间，单位: s
        """
        aklog_debug()
        try:
            ele_mid_x, ele_mid_y = self.get_ele_center(locator)
            for i in range(0, times):
                self.driver.click(ele_mid_x, ele_mid_y)
                time.sleep(interval)
            return True
        except Exception as e:
            aklog_error(e)
            if print_trace:
                aklog_debug(traceback.format_exc())
            return False

    def click_location(self, x, y):
        aklog_debug()
        try:
            self.driver.click(x, y)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def click_btn_by_xpath(self, ele_xpath, sec=0.2, wait_time=None, print_trace=True):
        aklog_debug()
        try:
            if not wait_time:
                wait_time = self.wait_time
            self.driver.xpath(ele_xpath).click(timeout=wait_time)
            time.sleep(sec)
            return True
        except:
            aklog_debug('click btn failed by xpath: {}'.format(ele_xpath))
            if print_trace:
                aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_by_name(self, ele_name, sec=0.2, wait_time=None, print_trace=True):
        aklog_debug()
        try:
            if not wait_time:
                wait_time = self.wait_time
            self.driver(text=ele_name).click(timeout=wait_time)
            time.sleep(sec)
            return True
        except:
            aklog_debug('click btn failed by name: {}'.format(ele_name))
            if print_trace:
                aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_by_desc(self, desc, sec=0.2, wait_time=None, print_trace=True):
        aklog_debug()
        try:
            if not wait_time:
                wait_time = self.wait_time
            self.driver(description=desc).click(timeout=wait_time)
            time.sleep(sec)
            return True
        except:
            aklog_debug('click btn failed by desc: {}'.format(desc))
            if print_trace:
                aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_by_contains_name(self, name, sec=0.1, wait_time=None):
        """匹配按钮部分名称，模糊匹配，点击按钮"""
        aklog_debug("click_btn_by_contains_name : %s" % name)
        try:
            if not wait_time:
                wait_time = self.wait_time
            self.driver(textContains=name).click(timeout=wait_time)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_by_names(self, *names, sec=0.1, wait_time=None, print_trace=False):
        """匹配多个不同名称点击按钮，names可以传入多个名称"""
        try:
            if not wait_time:
                wait_time = self.wait_time
            ele_xpath = self.get_names_expression(*names)
            aklog_debug("click_btn_by_names, xpath: %s" % ele_xpath)
            self.driver.xpath(ele_xpath).click(timeout=wait_time)
            time.sleep(sec)
            return True
        except:
            aklog_debug('click btn failed by names: {}'.format(tuple(names)))
            if print_trace:
                aklog_debug(str(traceback.format_exc()))
            return False

    def click_screen_mid_location(self, mid_x_length=0.5, mid_y_length=0.5):
        """
        点击屏幕坐标
        :param mid_x_length: 0-1之间表示比例，大于1为具体坐标
        :param mid_y_length: 0-1之间表示比例，大于1为具体坐标
        :return:
        """
        screen_size = self.get_screen_size()
        if mid_x_length < 1:
            screen_mid_x = int(screen_size[0] * mid_x_length)
        else:
            screen_mid_x = int(mid_x_length)
        if mid_y_length < 1:
            screen_mid_y = int(screen_size[1] * mid_y_length)
        else:
            screen_mid_y = int(mid_y_length)
        aklog_debug('click_screen_mid_location： (%s, %s)' % (screen_mid_x, screen_mid_y))
        self.click_location(screen_mid_x, screen_mid_y)

    def click_btn_location_by_xpath(self, ele_xpath, mid_x_length=0.5, mid_y_length=0.5):
        """点击元素内的某个坐标点，有些元素中心点无法点击时，可以用该方法"""
        aklog_debug("click_btn_location_by_xpath, ele_xpath: %s" % ele_xpath)
        try:
            ele = self.driver.xpath(ele_xpath)
            ele_mid_x, ele_mid_y = ele.center(offset=(mid_x_length, mid_y_length))
            self.driver.click(ele_mid_x, ele_mid_y)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_quickly_by_xpath(self, ele_xpath, times=1, duration=200):
        """快速多次点击元素"""
        aklog_debug("click_btn_quickly_by_xpath : %s, times: %s" % (ele_xpath, times))
        try:
            ele = self.driver.xpath(ele_xpath)
            ele_mid_x, ele_mid_y = ele.center(offset=(0.5, 0.5))
            for i in range(0, times):
                self.driver.click(ele_mid_x, ele_mid_y)
                time.sleep(duration / 1000)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    # endregion

    # region 按钮开关操作

    def set_checked(self, locator, status='Enable'):
        """复选框操作，设置按钮开启或关闭，Status可以设置为 Enable/Disable， True/False， 1、0"""
        aklog_debug()
        try:
            ele = self.get_element(locator)
            if ele is None:
                return False

            value = ele.value
            if status == 'Enable' or status is True or str(status) == '1':
                if value != 1:
                    ele.click()
                    time.sleep(0.2)
                return True
            elif status == 'Disable' or status is False or str(status) == '0':
                if value == 1:
                    ele.click()
                    time.sleep(0.2)
                return True
            else:
                aklog_debug('Status参数值 %s 不正确' % status)
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def is_checked(self, locator):
        """判断元素（单选框或复选框）是否选中"""
        aklog_debug()
        try:
            ele = self.get_element(locator)
            if ele is None:
                return False

            if ele.value == 1:
                aklog_debug('checked: true')
                return True
            else:
                aklog_debug('checked: false')
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def set_checked_button_by_xpath(self, ele_xpath, status='Enable'):
        """设置按钮开启或关闭，Status可以设置为 Enable/Disable， True/False， 1、0"""
        aklog_debug()
        try:
            ele = self.driver.xpath(ele_xpath).get()
            ele_attrib = ele.attrib
            if status == 'Enable' or status is True or str(status) == '1':
                if ele_attrib.get('checked') == 'false' or ele_attrib.get('checked') is False:
                    ele.click()
                    time.sleep(0.2)
                return True
            elif status == 'Disable' or status is False or str(status) == '0':
                if ele_attrib.get('checked') == 'true' or ele_attrib.get('checked') is True:
                    ele.click()
                    time.sleep(0.2)
                return True
            else:
                aklog_debug('Status参数值 %s 不正确')
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 复选框相关

    def check_by_xpath(self, ele_xpath):
        """ 勾选 """
        aklog_debug()
        try:
            ele = self.driver.xpath(ele_xpath).get()
            if ele.attrib.get('checked') == 'false' or ele.attrib.get('checked') is False:
                ele.click()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def uncheck_by_xpath(self, ele_xpath):
        """ 取消勾选 """
        aklog_debug()
        try:
            ele = self.driver.xpath(ele_xpath).get()
            if ele.attrib.get('checked') == 'true' or ele.attrib.get('checked') is True:
                ele.click()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def is_checked_by_xpath(self, ele_xpath):
        """判断元素（单选框或复选框）是否选中"""
        aklog_debug()
        try:
            ele = self.driver.xpath(ele_xpath).get()
            if ele.attrib.get('checked') == 'true' or ele.attrib.get('checked') is True:
                aklog_debug('checked: true')
                return True
            else:
                aklog_debug('checked: false')
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 元素长按操作

    def long_press(self, locator, duration=2):
        """
        长按
        duration: 秒数
        """
        aklog_debug()
        try:
            ele_mid_x, ele_mid_y = self.get_ele_center(locator)
            self.driver.click(ele_mid_x, ele_mid_y, duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def long_press_by_xpath(self, ele_xpath, duration=2):
        """
        通过xpath长按duration
        duration: 默认单位为毫秒，如果传入的值小于100，认为传入的是秒数
        """
        aklog_debug('long_press_by_xpath, ele_xpath: %s, duration: %s' % (ele_xpath, duration))
        try:
            s = self.driver.session()
            elem = s(xpath=ele_xpath)  # 实际发送的时长要多1秒，因此-1
            elem.tap_hold(duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def tap_by_coordinates(self, x, y):
        """
        坐标点击（该方法暂未生效）
        """
        aklog_debug('tap_by_coordinates, x: %s, y: %s' % (x, y))
        try:
            s = self.driver.session()
            s.tap_hold(x, y)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def long_press_by_name(self, ele_name, duration=2):
        """
        通过name长按duration
        duration: 默认单位为毫秒，如果传入的值小于100，认为传入的是秒数
        """
        aklog_debug()
        try:
            s = self.driver.session()
            elem = s(text=ele_name)  # 实际发送的时长要多1秒，因此-1
            elem.tap_hold(duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 滑动，滚动查找

    def scroll_v_until_find(self, locator, box_ele: Optional[Element] = None, counts=10, length=0.5, direction='up',
                            x_offset=0.25, near=None, oneway=False, click=False):
        """
        上下滑动直到找到元素并可见
        :param locator: 选项定位
        :param box_ele: 默认None表示整个屏幕上下滑动，可以指定元素框，可以先用get_element方法获取元素
        :param counts: 设置上滑或下滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指上滑的距离占元素框的比例
        :param direction: 先上滑还是下滑，up or down
        :param x_offset: 滑动的相对位置: 0-1
        :param oneway: 是否只查找单向，比如向上滑动10次后，就不再向下滑动继续查找了
        :param near: 靠近顶部或底部，默认为None找到即可，top表示查找的元素尽可能靠近顶部，bottom表示靠近底部，center表示靠近中间
        并且最好传入box_ele
        :param click: 找到元素后是否点击操作，要点击操作，near如果为None会修改为center
        :return:
        """
        aklog_debug()
        if oneway:
            all_swipe_count = counts
        else:
            all_swipe_count = counts * 3
        ret = False
        i = 0

        while i < all_swipe_count + 1:
            ret = self.is_exists(locator)

            # 判断是否找到，如果未找到则改变滑动方向
            if ret or i == all_swipe_count:
                break
            elif i == counts and not oneway:
                direction = 'down' if direction == 'up' else 'up'  # 如果先上滑没找到时改为下滑，反之先下滑没找到时改为上滑

            if direction == 'up':
                self.swipe_up(box_ele=box_ele, duration=0.3, length=length, x_offset=x_offset, sec=0.5)
            else:
                self.swipe_down(box_ele=box_ele, duration=0.3, length=length, x_offset=x_offset, sec=0.5)
            i += 1
            continue

        if ret:
            # 先滚动元素到可点击区域
            if box_ele is not None:
                box_lx, box_ly, box_width, box_height = self.__get_ele_bounds(ele=box_ele)
                box_rx = box_lx + box_width
                box_ry = box_ly + box_height
                clickable_area = (box_lx, box_ly, box_rx, box_ry)
            else:
                clickable_area = self.screen_clickable_area
            if clickable_area:
                ele_mid_x, ele_mid_y = self.get_ele_center(locator)
                if ele_mid_y <= clickable_area[1]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_down(box_ele, duration=0.3, length=0.1, x_offset=x_offset)
                elif ele_mid_y >= clickable_area[3]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_up(box_ele, duration=0.3, length=0.1, x_offset=x_offset)

            # 要点击操作，near如果为None会修改为center，避免在边缘位置点击不到
            if click and near is None:
                near = 'center'

            if near == 'top':
                # 让查找的元素尽可能靠近滚动框的顶部
                if box_ele is not None:
                    box_lx, box_ly, box_width, box_height = self.__get_ele_bounds(ele=box_ele)
                    box_rx = box_lx + box_width
                    box_ry = box_ly + box_height
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                if ly - box_ly > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = max(box_ly + 50, min(ly, box_ry - 50))
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = start_y + (box_ly + 50 - ly)
                    aklog_debug('swipe to top: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=1)
            elif near == 'bottom':
                # 让查找的元素尽可能靠近滚动框的底部
                if box_ele is not None:
                    box_lx, box_ly, box_width, box_height = self.__get_ele_bounds(ele=box_ele)
                    box_rx = box_lx + box_width
                    box_ry = box_ly + box_height
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                if box_ry - ry > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = max(box_ly + 50, min(ry, box_ry - 50))
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = start_y + (box_ry - 50 - ry)
                    aklog_debug('swipe to bottom: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=1)
            elif near == 'center':
                # 让查找的元素尽可能靠近滚动框的中间
                if box_ele is not None:
                    box_lx, box_ly, box_width, box_height = self.__get_ele_bounds(ele=box_ele)
                    box_rx = box_lx + box_width
                    box_ry = box_ly + box_height
                    box_mid_y = int((box_ly + box_ry) / 2)
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                    box_mid_y = int((box_ly + box_ry) / 2)
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                ele_mid_y = int((ly + ry) / 2)
                if abs(box_mid_y - ele_mid_y) > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = max(box_ly + 50, min(ele_mid_y, box_ry - 50))
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = start_y + (box_mid_y - ele_mid_y)
                    aklog_debug('swipe to center: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=1)

            if click:
                time.sleep(0.5)
                return self.click_btn(locator, sec=0.5)
            return True
        else:
            aklog_debug('%s is not found' % locator)
            return False

    def scroll_h_until_find(self, locator, box_ele=None, counts=10, length=0.5, direction='left',
                            y_offset=0.25, near=None, oneway=False, click=False):
        """
        左右滑动直到找到元素并可见
        :param locator: 选项定位
        :param box_ele: 默认None表示整个屏幕左右滑动，可以指定元素框，可以先用get_element方法获取元素
        :param counts: 设置左滑或右滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最左端滚动到最右端
        :param length: 手指左滑的距离占元素框的比例
        :param direction: 先左滑还是右滑，left or right
        :param y_offset: 滑动的相对位置: 0-1
        :param oneway: 是否只查找单向，比如向上滑动10次后，就不再向下滑动继续查找了
        :param near: 靠近最左边或最右边，默认为None找到即可，
        leftmost表示查找的元素尽可能靠近顶部，rightmost表示靠近底部，center表示靠近中间
        并且最好传入box_ele
        :param click: 找到元素后是否点击操作
        :return:
        """
        aklog_debug()
        if oneway:
            all_swipe_count = counts
        else:
            all_swipe_count = counts * 3
        ret = False
        i = 0
        while i < all_swipe_count + 1:
            ret = self.is_exists(locator)

            # 判断是否找到，如果未找到则改变滑动方向
            if ret or i == all_swipe_count:
                break
            elif i == counts and not oneway:
                direction = 'right' if direction == 'left' else 'left'  # 如果先左滑没找到时改为下右滑，反之先右滑没找到时改为左滑

            if direction == 'left':
                self.swipe_left(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset, sec=0.5)
            else:
                self.swipe_right(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset, sec=0.5)
            i += 1
            continue

        if ret:
            # 先滚动元素到可点击区域
            if box_ele is not None:
                box_lx, box_ly, box_width, box_height = self.__get_ele_bounds(ele=box_ele)
                box_rx = box_lx + box_width
                box_ry = box_ly + box_height
                clickable_area = (box_lx, box_ly, box_rx, box_ry)
            else:
                clickable_area = self.screen_clickable_area
            if clickable_area:
                ele_mid_x, ele_mid_y = self.get_ele_center(locator)
                if ele_mid_x <= clickable_area[0]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_right(box_ele, duration=0.3, length=0.1, y_offset=y_offset)
                elif ele_mid_x >= clickable_area[2]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_left(box_ele, duration=0.3, length=0.1, y_offset=y_offset)

            if click and near is None:
                near = 'center'

            if near == 'leftmost':
                # 让查找的元素尽可能靠近滚动框的最左边
                if box_ele is not None:
                    box_lx, box_ly, box_width, box_height = self.__get_ele_bounds(ele=box_ele)
                    box_rx = box_lx + box_width
                    box_ry = box_ly + box_height
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                if lx - box_lx > 50:
                    box_height = int(box_ry) - int(box_ly)
                    start_y = box_ly + int(box_height * y_offset)
                    start_x = max(box_lx + 50, min(lx, box_rx - 50))
                    end_y = box_ly + int(box_height * y_offset)
                    end_x = start_x + (box_lx + 50 - lx)
                    aklog_debug('swipe to top: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            elif near == 'rightmost':
                # 让查找的元素尽可能靠近滚动框的最右边
                if box_ele is not None:
                    box_lx, box_ly, box_width, box_height = self.__get_ele_bounds(ele=box_ele)
                    box_rx = box_lx + box_width
                    box_ry = box_ly + box_height
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                if box_rx - rx > 50:
                    box_height = int(box_ry) - int(box_ly)
                    start_y = box_ly + int(box_height * y_offset)
                    start_x = max(box_lx + 50, min(rx, box_rx - 50))
                    end_y = box_ly + int(box_height * y_offset)
                    end_x = start_x + (box_rx - 50 - rx)
                    aklog_debug('swipe to bottom: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            elif near == 'center':
                # 让查找的元素尽可能靠近滚动框的中间
                if box_ele is not None:
                    box_lx, box_ly, box_width, box_height = self.__get_ele_bounds(ele=box_ele)
                    box_rx = box_lx + box_width
                    box_ry = box_ly + box_height
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                box_mid_x = int((box_lx + box_rx) / 2)
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                ele_mid_x = int((lx + rx) / 2)
                if abs(box_mid_x - ele_mid_x) > 50:
                    box_height = int(box_ry) - int(box_ly)
                    start_y = box_ly + int(box_height * y_offset)
                    start_x = max(box_lx + 50, min(ele_mid_x, box_rx - 50))
                    end_y = box_ly + int(box_height * y_offset)
                    end_x = start_x + (box_mid_x - ele_mid_x)
                    aklog_debug('swipe to center: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.5)

            if click:
                time.sleep(0.5)
                return self.click_btn(locator, sec=0.5)
            return True
        else:
            aklog_debug('%s is not found' % locator)
            return False

    def drag_element(self, locator, direction='up', length=0.5, duration=0.3):
        """
        拖动元素滑动
        length: 拖动距离，距离为屏幕宽度或高度的百分比
        比如方向为up/down, length=0.5，则 滑动距离为 0.5*屏幕高度
        如果方向为left/right, length=0.5，则 滑动距离为 0.5*屏幕宽度
        """
        aklog_debug()
        ele_mid_x, ele_mid_y = self.get_ele_center(locator)
        if ele_mid_x is None:
            return False
        screen_width, screen_height = self.get_screen_size()
        start_x = ele_mid_x
        start_y = ele_mid_y
        if direction == 'up':
            end_x = ele_mid_x
            end_y = ele_mid_y - screen_height / 2 + length  # 原先的方法从最底端划上去会出现负数
        elif direction == 'down':
            end_x = ele_mid_x
            end_y = ele_mid_y + screen_height + length
        elif direction == 'left':
            end_x = ele_mid_x - screen_width + length
            end_y = ele_mid_y
        else:
            end_x = ele_mid_x + screen_width + length
            end_y = ele_mid_y
        return self.swipe(start_x, start_y, end_x, end_y, duration)

    def swipe(self, startX, startY, endX, endY, duration=0.3):
        """滑动，duration为秒数"""
        # 区域保护, 避免超出区域
        screen = self.get_screen_size()
        startX = startX + 1 if startX == 0 else startX - 1 if startX == screen[0] else startX
        startY = startY + 1 if startY == 0 else startY - 1 if startY == screen[1] else startY
        endX = endX + 1 if endX == 0 else endX - 1 if endX == screen[0] else endX
        endY = endY + 1 if endY == 0 else endY - 1 if endY == screen[1] else endY
        aklog_debug('swipe: (%s, %s) -> (%s, %s), duration: %s' % (startX, startY, endX, endY, duration))
        try:
            self.driver.swipe(startX, startY, endX, endY, duration=duration)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def swipe_right(self, box_ele=None, duration=0.3, length=0.5, y_offset=0.25, sec=0.1):
        """
        如果box_ele如果为None或'screen', 从屏幕最左侧向右滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果box_ele有传入元素，则在元素框范围内从最左侧向右滑动
        y_offset: 滑动的位置: ly + box_height * y_offset
        """
        try:
            if box_ele is None or box_ele == 'screen':
                screen = self.get_screen_size()
                start_x = int(screen[0] * (1 - length) / 2)
                start_y = int(screen[1] * y_offset)
                end_x = int(screen[0] * (1 + length) / 2)
                end_y = int(screen[1] * y_offset)
            else:
                bounds = box_ele.info.get('bounds')
                lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                box_width = int(rx) - int(lx)
                box_height = int(ry) - int(ly)
                start_x = int(lx + box_width * (1 - length) / 2)
                start_y = int(ly + box_height * y_offset)
                end_x = int(lx + box_width * (1 + length) / 2)
                end_y = int(ly + box_height * y_offset)
            aklog_debug('swipe_right: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_left(self, box_ele=None, duration=0.3, length=0.5, y_offset=0.25, sec=0.1):
        """
        如果box_ele如果为None或'screen', 从屏幕最右侧向左滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果box_ele有传入元素，则在元素框范围内从最右侧向左滑动
        y_offset: 滑动的位置: ly + size['height'] * y_offset
        """
        try:
            if box_ele is None or box_ele == 'screen':
                screen = self.get_screen_size()
                start_x = int(screen[0] * (1 + length) / 2)
                start_y = int(screen[1] * y_offset)
                end_x = int(screen[0] * (1 - length) / 2)
                end_y = int(screen[1] * y_offset)
            else:
                bounds = box_ele.info.get('bounds')
                lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                box_width = int(rx) - int(lx)
                box_height = int(ry) - int(ly)
                start_x = int(lx + box_width * (1 + length) / 2)
                start_y = int(ly + box_height * y_offset)
                end_x = int(lx + box_width * (1 - length) / 2)
                end_y = int(ly + box_height * y_offset)
            aklog_debug('swipe_left: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_down(self, box_ele=None, duration=0.3, length=0.5, x_offset=0.25, sec=0.1):
        """
        如果box_ele如果为None或'screen', 从屏幕1/4处向下滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果box_ele有传入元素，则在元素框范围内从1/4处向下滑动
        x_offset: 滑动的位置: lx + box_width * x_offset
        """
        try:
            if box_ele is None or box_ele == 'screen':
                screen = self.get_screen_size()
                start_x = int(screen[0] * x_offset)
                start_y = int(screen[1] * (1 - length) / 2)
                end_x = int(screen[0] * x_offset)
                end_y = int(screen[1] * (1 + length) / 2)
            else:
                bounds = box_ele.info.get('bounds')
                lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                box_width = int(rx) - int(lx)
                box_height = int(ry) - int(ly)
                start_x = lx + int(box_width * x_offset)
                start_y = ly + int(box_height * (1 - length) / 2)
                end_x = lx + int(box_width * x_offset)
                end_y = ly + int(box_height * (1 + length) / 2)
            aklog_debug('swipe_down: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_up(self, box_ele=None, duration=0.5, length=0.5, x_offset=0.25, sec=0.1):
        """
        如果box_ele如果为None或'screen', 则从屏幕3/4处向上滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果box_ele有传入元素，则在元素框范围内从3/4处向上滑动
        x_offset: 滑动的位置: lx + box_width * x_offset
        """
        try:
            if box_ele is None or box_ele == 'screen':
                screen = self.get_screen_size()
                start_x = int(screen[0] * x_offset)
                start_y = int(screen[1] * (1 + length) / 2)
                end_x = int(screen[0] * x_offset)
                end_y = int(screen[1] * (1 - length) / 2)
            else:
                self.image.get_screenshot_by_element(box_ele)
                bounds = box_ele.bounds
                lx, ly, rx, ry = bounds[0] * 3, bounds[1] * 3, bounds[2] * 3, bounds[3] * 3
                h = int(ry)
                w = int(rx)

                # bounds = box_ele.info.get('bounds')
                # lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                # box_width = int(rx) - int(lx)
                # box_height = int(ry) - int(ly)
                start_x = lx + int(w * x_offset)
                start_y = ly + int(h * (1 + length) / 2)
                end_x = lx + int(w * x_offset)
                end_y = ly + int(h * (1 - length) / 2)

            aklog_debug('swipe_up: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_until_find_by_xpath(self, ele_xpath, box_ele=None, counts=10, length=0.5, direction='up',
                                  x_offset=0.25, near=None):
        """
        上下滑动直到找到元素并可见
        :param ele_xpath: 选项xpath
        :param box_ele: 默认None表示整个屏幕上下滑动，可以指定元素框，可以先用get_element_by_id方法获取元素
        :param counts: 设置上滑或下滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指上滑的距离占元素框的比例
        :param direction: 先上滑还是下滑，up or down
        :param x_offset: 滑动的相对位置: 0-1
        :param near: 靠近顶部或底部，默认为None找到即可，top表示查找的元素尽可能靠近顶部，bottom表示靠近底部，center表示靠近中间
        并且最好传入box_ele
        :return:
        """
        aklog_debug()
        ret = False
        i = 0
        while i < counts * 3 + 1:
            try:
                ret = self.driver.xpath(ele_xpath).exists
            except:
                ret = False
            # 判断是否找到，如果未找到则改变滑动方向
            if ret or i == counts * 3:
                break
            elif i == counts:
                direction = 'down' if direction == 'up' else 'up'  # 如果先上滑没找到时改为下滑，反之先下滑没找到时改为上滑

            if direction == 'up':
                self.swipe_up(box_ele=box_ele, duration=0.3, length=length, x_offset=x_offset)
            else:
                self.swipe_down(box_ele=box_ele, duration=0.3, length=length, x_offset=x_offset)
            i += 1
            continue

        if ret:
            # 先滚动元素到可点击区域
            if self.screen_clickable_area:
                ele_mid_x, ele_mid_y = self.driver.xpath(ele_xpath).get().center()
                if ele_mid_y <= self.screen_clickable_area[1]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_down(box_ele, duration=0.3, length=0.1, x_offset=x_offset)
                elif ele_mid_y >= self.screen_clickable_area[3]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_up(box_ele, duration=0.3, length=0.1, x_offset=x_offset)

            if near == 'top':
                # 让查找的元素尽可能靠近滚动框的顶部
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.driver.xpath(ele_xpath).get().bounds
                if ly - box_ly > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ly
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_ly + 50
                    aklog_debug('swipe to top: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.3)
            elif near == 'bottom':
                # 让查找的元素尽可能靠近滚动框的底部
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.driver.xpath(ele_xpath).get().bounds
                if box_ry - ry > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ry
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_ry - 50
                    aklog_debug('swipe to bottom: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            elif near == 'center':
                # 让查找的元素尽可能靠近滚动框的中间
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                    box_mid_y = int((box_ly + box_ry) / 2)
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                    box_mid_y = int((box_ly + box_ry) / 2)
                lx, ly, rx, ry = self.driver.xpath(ele_xpath).get().bounds
                ele_mid_y = int((ly + ry) / 2)
                if abs(box_mid_y - ele_mid_y) > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ele_mid_y
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_mid_y
                    aklog_debug('swipe to center: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            return True
        else:
            aklog_debug('%s is not found' % ele_xpath)
            # self.screen_shot()
            return False

    def swipe_until_find_by_name(self, ele_name, box_ele=None, counts=10, length=0.5, direction='up',
                                 x_offset=0.25, near=None):
        """
        上下滑动直到找到元素并可见
        :param ele_name: 选项名称
        :param box_ele: 默认None表示整个屏幕上下滑动，可以指定元素框，可以先用get_element_by_id方法获取元素
        :param counts: 设置上滑或下滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指上滑的距离占元素框的比例
        :param direction: 先上滑还是下滑，up or down
        :param x_offset: 滑动的相对位置: 0-1
        :param near: 靠近顶部或底部，默认为None找到即可，top表示查找的元素尽可能靠近顶部，bottom表示靠近底部，center表示靠近中间
        并且最好传入box_ele
        :return:
        """
        aklog_debug()
        ret = False
        i = 0
        while i < counts * 3 + 1:
            try:
                ret = self.driver(text=ele_name).exists
            except:
                ret = False
            # 判断是否找到，如果未找到则改变滑动方向
            if ret or i == counts * 3:
                break
            elif i == counts:
                direction = 'down' if direction == 'up' else 'up'  # 如果先上滑没找到时改为下滑，反之先下滑没找到时改为上滑

            if direction == 'up':
                self.swipe_up(box_ele=box_ele, duration=0.3, length=length, x_offset=x_offset)
            else:
                self.swipe_down(box_ele=box_ele, duration=0.3, length=length, x_offset=x_offset)
            i += 1
            continue

        if ret:
            # 先滚动元素到可点击区域
            if self.screen_clickable_area:
                ele_mid_x, ele_mid_y = self.driver(text=ele_name).center()
                if ele_mid_y <= self.screen_clickable_area[1]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_down(box_ele, duration=0.3, length=0.1, x_offset=x_offset)
                elif ele_mid_y >= self.screen_clickable_area[3]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_up(box_ele, duration=0.3, length=0.1, x_offset=x_offset)

            if near == 'top':
                # 让查找的元素尽可能靠近滚动框的顶部
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.driver(text=ele_name).bounds()
                if ly - box_ly > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ly
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_ly + 50
                    aklog_debug('swipe to top: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.3)
            elif near == 'bottom':
                # 让查找的元素尽可能靠近滚动框的底部
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.driver(text=ele_name).bounds()
                if box_ry - ry > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ry
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_ry - 50
                    aklog_debug('swipe to bottom: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            elif near == 'center':
                # 让查找的元素尽可能靠近滚动框的中间
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                    box_mid_y = int((box_ly + box_ry) / 2)
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                    box_mid_y = int((box_ly + box_ry) / 2)
                lx, ly, rx, ry = self.driver(text=ele_name).bounds()
                ele_mid_y = int((ly + ry) / 2)
                if abs(box_mid_y - ele_mid_y) > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ele_mid_y
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_mid_y
                    aklog_debug('swipe to center: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            return True
        else:
            aklog_debug('%s is not found' % ele_name)
            self.screen_shot()
            return False

    def swipe_until_find_by_names(self, *names, box_ele=None, counts=10, length=0.5, direction='up',
                                  x_offset=0.25, near=None):
        """
        上下滑动直到找到元素并可见
        :param names: 选项名称，可以传入多个name，只要有一个匹配成功即可
        :param box_ele: 默认None表示整个屏幕上下滑动，可以指定元素框，可以先用get_element_by_id方法获取元素
        :param counts: 设置上滑或下滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指上滑的距离占元素框的比例
        :param direction: 先上滑还是下滑，up or down
        :param x_offset: 滑动的相对位置: 0-1
        :param near: 靠近顶部或底部，默认为None找到即可，top表示查找的元素尽可能靠近顶部，bottom表示靠近底部，center表示靠近中间
        并且最好传入box_ele
        :return:
        """
        # 传入多个名称，组合成一个Xpath，只要一个名称匹配成功即可
        ele_xpath = self.get_names_expression(*names)
        aklog_debug()
        ret = False
        i = 0
        while i < counts * 3 + 1:
            try:
                ret = self.driver.xpath(ele_xpath).exists
            except:
                ret = False
            # 判断是否找到，如果未找到则改变滑动方向
            if ret or i == counts * 3:
                break
            elif i == counts:
                direction = 'down' if direction == 'up' else 'up'  # 如果先上滑没找到时改为下滑，反之先下滑没找到时改为上滑

            if direction == 'up':
                self.swipe_up(box_ele=box_ele, duration=0.3, length=length, x_offset=x_offset)
            else:
                self.swipe_down(box_ele=box_ele, duration=0.3, length=length, x_offset=x_offset)
            i += 1
            continue

        if ret:
            # 先滚动元素到可点击区域
            if self.screen_clickable_area:
                ele_mid_x, ele_mid_y = self.driver.xpath(ele_xpath).get().center()
                if ele_mid_y <= self.screen_clickable_area[1]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_down(box_ele, duration=0.3, length=0.1, x_offset=x_offset)
                elif ele_mid_y >= self.screen_clickable_area[3]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_up(box_ele, duration=0.3, length=0.1, x_offset=x_offset)

            if near == 'top':
                # 让查找的元素尽可能靠近滚动框的顶部
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.driver.xpath(ele_xpath).get().bounds
                if ly - box_ly > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ly
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_ly + 50
                    aklog_debug('swipe to top: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.3)
            elif near == 'bottom':
                # 让查找的元素尽可能靠近滚动框的底部
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.driver.xpath(ele_xpath).get().bounds
                if box_ry - ry > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ry
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_ry - 50
                    aklog_debug('swipe to bottom: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            elif near == 'center':
                # 让查找的元素尽可能靠近滚动框的中间
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                    box_mid_y = int((box_ly + box_ry) / 2)
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                    box_mid_y = int((box_ly + box_ry) / 2)
                lx, ly, rx, ry = self.driver.xpath(ele_xpath).get().bounds
                ele_mid_y = int((ly + ry) / 2)
                if abs(box_mid_y - ele_mid_y) > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ele_mid_y
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_mid_y
                    aklog_debug('swipe to center: (%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            return True
        else:
            aklog_debug('%s is not found' % ele_xpath)
            self.screen_shot()
            return False

    def swipe_horizontal_until_find_by_name(self, ele_name, box_ele=None, counts=10, length=0.5, direction='left',
                                            y_offset=0.25):
        """
        左右滑动直到找到元素并可见
        ele: 滑动区域元素，默认全屏
        :param ele_name: 选项名称
        :param box_ele: 默认None表示整个屏幕左右滑动，可以指定元素框，可以先用get_element_by_id方法获取元素
        :param counts: 设置左滑或右滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指左滑的距离占元素框的比例
        :param direction: 先左滑还是右滑，left or right
        :param y_offset: 滑动的相对位置: 0-1
        """
        aklog_debug()
        for i in range(0, counts + 1):
            try:
                ret = self.driver(text=ele_name).exists
            except:
                ret = False
            if ret:
                return True
            if i == counts:
                break
            if direction == 'left':
                self.swipe_left(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset)
            else:
                self.swipe_right(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset)
            continue

        for i in range(0, counts + 1):
            try:
                ret = self.driver(text=ele_name).exists
            except:
                ret = False
            if ret:
                return True
            if i == counts:
                break
            if direction == 'left':
                self.swipe_right(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset)
            else:
                self.swipe_left(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset)
            continue

        aklog_debug('%s is not found' % ele_name)
        self.screen_shot()
        return False

    def swipe_horizontal_until_find_by_xpath(self, ele_xpath, box_ele=None, counts=10, length=0.5,
                                             direction='left', y_offset=0.25):
        """
        左右滑动直到找到元素并可见
        :param ele_xpath: 选项xpath
        :param box_ele: 默认None表示整个屏幕左右滑动，可以指定元素框，可以先用get_element_by_id方法获取元素
        :param counts: 设置左滑或右滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最左边滚动到最右边
        :param length: 手指左滑的距离占元素框的比例
        :param direction: 先左滑还是右滑，left or right
        :param y_offset: 滑动的相对位置: 0-1
        """
        aklog_debug()
        for i in range(0, counts + 1):
            try:
                ret = self.driver.xpath(ele_xpath).exists
            except:
                ret = False
            if ret:
                return True
            if i == counts:
                break
            if direction == 'left':
                self.swipe_left(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset)
            else:
                self.swipe_right(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset)
            continue

        for i in range(0, counts + 1):
            try:
                ret = self.driver.xpath(ele_xpath).exists
            except:
                ret = False
            if ret:
                return True
            if i == counts:
                break
            if direction == 'left':
                self.swipe_right(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset)
            else:
                self.swipe_left(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset)
            continue

        aklog_debug('%s is not found' % ele_xpath)
        self.screen_shot()
        return False

    # endregion

    # region 元素是否存在或可见，等待元素出现或消失

    def is_exist_ele_by_xpath(self, ele_xpath, wait_time=None):
        """判断元素是否存在"""
        aklog_debug()
        try:
            if not wait_time:
                wait_time = self.wait_time
            ele = self.driver.xpath(ele_xpath).wait(timeout=wait_time)
            if not ele:
                aklog_debug('%s is not exist' % ele_xpath)
                return False
            else:
                aklog_debug('%s is exist' % ele_xpath)
                return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def is_exist_ele_by_names(self, *ele_names, wait_time=None):
        """判断元素是否存在并可见"""
        # 传入多个名称，组合成一个Xpath，只要一个名称匹配成功即可
        ele_xpath = self.get_names_expression(*ele_names)
        aklog_debug("is_exist_ele_by_names, xpath: %s" % ele_xpath)
        try:
            if not wait_time:
                wait_time = self.wait_time
            ele = self.driver.xpath(ele_xpath).wait(timeout=wait_time)
            if not ele:
                aklog_debug('%s is not exist' % ele_xpath)
                return False
            else:
                return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def is_exist_ele_by_name(self, ele_name, wait_time=None):
        """判断元素是否存在"""
        aklog_debug()
        try:
            if not wait_time:
                wait_time = self.wait_time
            ret = self.driver(text=ele_name).wait(timeout=wait_time)
            if not ret:
                aklog_debug('%s is not exist' % ele_name)
            return ret
        except:
            aklog_debug(traceback.format_exc())
            return False

    def wait_for_visible_by_name(self, ele_name, timeout=5):
        """等待元素出现"""
        aklog_debug()
        try:
            ret = self.driver(text=ele_name).wait(timeout=timeout)
            if not ret:
                aklog_debug('%s is not found' % ele_name)
            return ret
        except:
            aklog_debug(traceback.format_exc())
            return False

    def wait_for_visible_by_xpath(self, ele_xpath, timeout=5):
        """等待元素出现"""
        aklog_debug()
        try:
            ret = self.driver.xpath(ele_xpath).wait(timeout=timeout)
            if not ret:
                aklog_debug('%s is not found' % ele_xpath)
            return ret
        except:
            aklog_debug(traceback.format_exc())
            return False

    def wait_for_disappear_by_name(self, ele_name, timeout=5):
        """等待元素消失"""
        aklog_debug()
        try:
            ret = self.driver(text=ele_name).wait_gone(timeout=timeout)
            if not ret:
                aklog_debug('%s is not disappear' % ele_name)
            return ret
        except:
            aklog_debug(traceback.format_exc())
            return False

    def wait_for_disappear_by_xpath(self, ele_xpath, timeout=5):
        """等待元素消失"""
        aklog_debug()
        try:
            ret = self.driver.xpath(ele_xpath).wait_gone(timeout=timeout)
            if not ret:
                aklog_debug('%s is not disappear' % ele_xpath)
            return ret
        except:
            aklog_debug(traceback.format_exc())
            return False

    # endregion

    # region 获取元素信息

    def get_text(self, locator, timeout=None, print_trace=False):
        """获取控件文本"""
        aklog_debug()
        try:
            ele = self.get_element(locator, timeout=timeout)
            if ele is None:
                return None
            text = ele.text
            aklog_debug("text : %s" % text)
            return text
        except Exception as e:
            aklog_error(e)
            if print_trace:
                aklog_debug(str(traceback.format_exc()))
            return None

    def get_attr(self, locator, attr_type):
        """
        attr_type：id, name, label, value, text, className, enabled, displayed, visible, accessible, accessibilityContainer
        """
        try:
            ele = self.get_element(locator)
            if ele is None:
                return None
            value = ele.info.get(attr_type)
            aklog_debug('locator: %s, attribute: %s, value: %s' % (locator, attr_type, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def is_enabled(self, locator):
        """
        判断控件是否可以操作
        return: boolean类型, True or False
        """
        aklog_debug()
        try:
            ele = self.get_element(locator)
            if ele is None:
                return None

            enabled = ele.info.get('enabled')
            aklog_debug('enabled: %s' % enabled)
            return enabled
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_counts(self, locator):
        """获取相同定位信息元素的数量"""
        aklog_debug()
        try:
            elements = self.find_elements(locator)
            count = len(elements)
            aklog_debug('count: %s' % count)
            return count
        except:
            aklog_debug(str(traceback.format_exc()))
            return 0

    def get_texts(self, locator) -> list:
        """
        获取多个相同定位的元素文本列表
        locator: 建议传入xpath，也可以传入的是多个id的元组类型，会自动转换成xpath
        PageSource类填写的格式:
        (d(resourceId="com.akuvox.belahome:id/tv_login"), d(resourceId="com.akuvox.belahome:id/iv_login"))
        转换后传入的格式:
        ({'resourceId': 'com.akuvox.belahome:id/tv_login'}, {'resourceId': 'com.akuvox.belahome:id/iv_login'})
        """
        aklog_debug()
        try:
            elements = self.find_elements(locator)
            texts = []
            for element in elements:
                texts.append(element.text)
            aklog_debug("texts : %s" % texts)
            return texts
        except:
            aklog_debug(str(traceback.format_exc()))
            return []

    @staticmethod
    def get_names_expression(*ele_names):
        """多个name组成Xpath，一般用于不同版本或机型兼容"""
        ele_xpath = '//*['
        for x in ele_names:
            ele_xpath += '@text="%s" or ' % x
        ele_xpath = ele_xpath.rstrip(' or ') + ']'
        return ele_xpath

    def get_value_by_xpath(self, ele_xpath, timeout=None, print_trace=True):
        aklog_debug()
        try:
            if not timeout:
                timeout = self.wait_time
            ele = self.driver.xpath(ele_xpath).get(timeout)
            if ele:
                value = ele.text
                aklog_debug("text : %s" % value)
                return value
            else:
                aklog_debug('get value failed by xpath: %s' % ele_xpath)
                return None
        except:
            aklog_debug('get value failed by xpath: %s' % ele_xpath)
            if print_trace:
                aklog_debug(str(traceback.format_exc()))
            return None

    def get_values_by_xpath(self, ele_xpath):
        """获取多个相同Xpath的元素文本列表"""
        aklog_debug()
        try:
            values = []
            elements = self.driver.xpath(ele_xpath).all()
            for ele in elements:
                values.append(ele.text)
            aklog_debug("texts : %s" % values)
            return values
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_counts_by_xpath(self, ele_xpath):
        """获取相同Xpath元素的数量"""
        aklog_debug()
        try:
            elements = self.driver.xpath(ele_xpath).find_elements()
            # elements = self.driver.xpath(ele_xpath).child(className='Cell').find_elements()
            counts = len(elements)
            aklog_debug('counts: %s' % counts)
            return counts
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_by_xpath(self, ele_xpath, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、password、selected，返回的是"true"和"false"的str类型
        2、.get("name")  返回的是‘content_desc’的值
        3、.get("className")  返回的是‘class’的值
        """
        try:
            ele = self.driver.xpath(ele_xpath).get()
            value = ele.attrib.get(attribute_type)
            aklog_debug('ele_xpath: %s, attribute: %s, value: %s, Type: %s' %
                        (ele_xpath, attribute_type, value, type(value)))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_by_name(self, ele_name, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、password、selected，返回的是"true"和"false"的str类型
        2、.get("name")  返回的是‘content_desc’的值
        3、.get("className")  返回的是‘class’的值
        """
        try:
            ele = self.driver(text=ele_name)
            value = ele.info.get(attribute_type)
            aklog_debug('ele_name: %s, attribute: %s, value: %s' % (ele_name, attribute_type, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    # endregion

    # region 获取元素或屏幕尺寸、位置

    def __get_ele_bounds(self, locator=None, ele=None):
        if ele is None and locator:
            ele = self.get_element(locator)
        if ele is None:
            return 0, 0, 0, 0
        lx, ly, width, height = ele.bounds
        return lx*3, ly*3, width*3, height*3

    def get_ele_size(self, locator):
        """获取元素的大小（宽和高）"""
        try:
            lx, ly, width, height = self.__get_ele_bounds(locator)
            aklog_debug(f'locator: {locator}, width: {width}, height: {height}')
            return width, height
        except Exception as e:
            aklog_error(e)
            return 0, 0

    def get_ele_location(self, locator):
        """获取元素的位置(左上角的坐标)"""
        try:
            lx, ly, width, height = self.__get_ele_bounds(locator)
            ele_location = {'x': lx, 'y': ly}
            aklog_debug(f'locator: {locator}, location: {ele_location}')
            return ele_location
        except Exception as e:
            aklog_error(e)
            return None

    def get_ele_rect(self, locator):
        """获取元素尺寸和位置信息: x, y, width, height"""
        try:
            lx, ly, width, height = self.__get_ele_bounds(locator)
            rect = {
                'x': lx,
                'y': ly,
                'width': width,
                'height': height
            }
            aklog_debug(f'locator: {locator}, rect: {rect}')
            return rect
        except Exception as e:
            aklog_error(e)
            return None

    def get_ele_bounds(self, locator):
        """获取元素左上角和左下角坐标: lx, ly, rx, ry"""
        try:
            lx, ly, width, height = self.__get_ele_bounds(locator)
            rx = lx + width
            ry = ly + height
            return lx, ly, rx, ry
        except Exception as e:
            aklog_error(e)
            return None

    def get_ele_center(self, locator):
        """
        获取元素的位置(中心点的坐标)
        :param locator: 元素定位
        :return: dict类型
        """
        try:
            ele = self.get_element(locator)
            if ele is None:
                return None, None
            ele_mid_x, ele_mid_y = ele.bounds.center
            return ele_mid_x*3, ele_mid_y*3
        except:
            aklog_debug(str(traceback.format_exc()))
            return None, None

    def get_screen_size(self):
        """获取屏幕大小"""
        if self.screen_width == 0:
            try:
                screen_width, screen_height = self.driver.window_size()
            except:
                screen_width = 0
                screen_height = 0

            self.screen_width = screen_width*3
            self.screen_height = screen_height*3
            aklog_debug('screen_size: %s, %s' % (self.screen_width, self.screen_height))
        return self.screen_width, self.screen_height

    # endregion

    # region 获取元素

    def get_element_by_id(self, ele_id):
        aklog_debug()
        try:
            element = self.driver(resourceId=ele_id)
            return element
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_element_by_xpath(self, ele_xpath):
        aklog_debug()
        try:
            element = self.driver.xpath(ele_xpath).get()
            return element
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_elements_by_xpath(self, ele_xpath):
        """获取相同xpath元素列表，该方法有点问题，获取的元素不全"""
        aklog_debug()
        try:
            elements = self.driver.xpath(ele_xpath).all()
            return elements
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    # endregion

    # region 截图相关

    def screen_shot_as_base64(self):
        """保存屏幕截图成base64编码，用于嵌入到HTML测试报告"""
        aklog_debug('screen_shot_as_base64, the screenshots is shown below: ')
        return self.image.screenshots_as_base64()

    def screen_shot(self):
        """截图,用于外部调用"""
        img_base64 = self.screen_shot_as_base64()
        if img_base64:
            param_append_screenshots_imgs(img_base64)
        else:
            param_append_screenshots_imgs('')

    def save_screen_shot_to_file(self, image_path=None, remove_first=True):
        """保存整个屏幕截图"""
        if not image_path:
            image_path = root_path + '\\image.png'
        if remove_first:
            File_process.remove_file(image_path)
        aklog_debug('save_screen_shot_to_file: %s' % image_path)
        aa = self.driver.screenshot(image_path)
        aklog_printf(aa)
        param_append_screenshots_imgs(aa)
        return image_path

    @staticmethod
    def save_element_image(element, image_path=None):
        """保存图片"""
        if not image_path:
            image_path = root_path + '\\image.png'
        element.screenshot().save(image_path)

    def save_element_image_by_id(self, ele_id, image_path=None):
        if not image_path:
            image_path = root_path + '\\image.png'
        aklog_debug()
        File_process.remove_file(image_path)
        self.driver(resourceId=ele_id).screenshot().save(image_path)
        return image_path

    def save_element_image_by_xpath(self, ele_xpath, image_path=None):
        if not image_path:
            image_path = root_path + '\\image.png'
        aklog_debug()
        File_process.remove_file(image_path)
        self.driver.xpath(ele_xpath).screenshot().save(image_path)
        return image_path

    def save_custom_area_image(self, area, image_path=None):
        """
        保存指定区域截图
        :param area: 坐标元组: (start_x, start_y, end_x, end_y)
        :param image_path:
        :return:
        """
        if not image_path:
            image_path = root_path + '\\image.png'
        aklog_debug('save_custom_area_image: %s' % image_path)
        File_process.remove_file(image_path)
        self.driver.screenshot(format='pillow').crop(area).save(image_path)

    # endregion

    # region 图片对比，图像检查

    def check_image_rgb(self, locator, ratio, fix_rgb):
        """检查元素图像某种颜色占比"""
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            value = self.image.check_screen_color(element=element, fix_rgb=fix_rgb)
            aklog_debug('%r color proportion: %s' % (fix_rgb, value))
            if value is None:
                return None
            if value > ratio:
                return True
            else:
                return False
        except:
            aklog_debug(traceback.format_exc())
            return None

    def check_image_rgbs(self, locator, ratio, *fix_rgbs):
        """检查元素图像某几种颜色总共占比"""
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            value = self.image.check_screen_colors(*fix_rgbs, element=element)
            aklog_debug('%r color proportion: %s' % (fix_rgbs, value))
            if value is None:
                return None
            if value > ratio:
                return True
            else:
                return False
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_pure_color(self, locator, percent, save_path=None):
        """
        判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色
        save_path: 将截图数据保存到文件
        """
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            else:
                return self.image.is_pure_color(element=element, percent=percent, save_path=save_path)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_normal_color(self, locator, threshold=10, save_path=None):
        """
        用OpenCV方式检查画面是否正常
        save_path: 将截图数据保存到文件
        """
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            return self.image.check_video_image_is_normal(
                element=element, threshold=threshold, save_path=save_path)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_same_ele_image(self, locator, image_path, percent):
        """判断元素图片跟预期的图片是否一致"""
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            result = self.image.compare_image_after_convert_resolution(element, image_path, percent)
            return result
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def is_light_color(self, locator, rgb_sum=300, percent=0.5):
        """检查图片是否为浅色，当rgb三个数值相加大于rgb_sum，占比超过percent时，认为是浅色"""
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            return self.image.is_light_color(element=element, rgb_sum=rgb_sum, percent=percent)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_similar_color(self, locator, color=None, lower_hsv=None, upper_hsv=None, threshold=0.1):
        """
        检查颜色跟哪一种比较相似，比如可以区分元素的颜色是橙色还是蓝色
        偏蓝色的HSV范围：
        下限：H = 90, S = 50, V = 0
        上限：H = 140, S = 255, V = 255
        偏橙黄色的HSV范围：
        下限：H = 10, S = 100, V = 100
        上限：H = 35, S = 255, V = 255
        Args:
            locator ():
            color (str): red/blue/green/orange/yellow/purple
            lower_hsv (list): [90, 50, 0]
            upper_hsv (list): [140, 255, 255]
            threshold (float): 颜色占比阈值
        """
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            return self.image.is_similar_color(
                element=element, color=color, lower_hsv=lower_hsv, upper_hsv=upper_hsv, threshold=threshold)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def check_rgb_sum(self, locator, rgb_sum=300):
        """
        获取rgb_sum占比
        rgb_sum: rgb三种数值相加
        """
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            return self.image.check_rgb_sum(element=element, rgb_sum=rgb_sum)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def check_image_rgb_by_xpath(self, ele_xpath, ratio, fix_rgb):
        """检查元素图像某种颜色占比"""
        aklog_debug()
        try:
            element = self.driver.xpath(ele_xpath).get()
            if not element:
                aklog_debug('%s is not found' % ele_xpath)
                return None
            value = self.image.check_screen_color(element=element, fix_rgb=fix_rgb)
            aklog_debug('%r color proportion: %s' % (fix_rgb, value))
            if value is None:
                return None
            if value > ratio:
                return True
            else:
                return False
        except:
            aklog_debug(traceback.format_exc())
            return None

    def check_image_rgb_by_id(self, ele_id, ratio, fix_rgb):
        """检查元素图像某种颜色占比"""
        aklog_debug()
        try:
            element = self.driver(resourceId=ele_id)
            if element is None:
                aklog_debug('%s is not found' % ele_id)
                return None
            value = self.image.check_screen_color(element=element, fix_rgb=fix_rgb)
            aklog_debug('%r color proportion: %s' % (fix_rgb, value))
            if value is None:
                return None
            if value > ratio:
                return True
            else:
                return False
        except:
            aklog_debug(traceback.format_exc())
            return None

    def check_image_rgb_custom_area(self, area, ratio, fix_rgb):
        """
        检查某个区域图像某种颜色占比
        :param area: (start_x, start_y, end_x, end_y)
        :param ratio:
        :param fix_rgb:
        :return:
        """
        aklog_debug()
        value = self.image.check_screen_color(area=area, fix_rgb=fix_rgb)
        aklog_debug('%r color proportion: %s' % (fix_rgb, value))
        if value is None:
            return None
        if value > ratio:
            return True
        else:
            return False

    def is_pure_color_by_id(self, ele_id, percent):
        """判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色"""
        aklog_debug()
        try:
            element = self.get_element_by_id(ele_id)
            if not element:
                aklog_debug('%s is not found' % ele_id)
                return None
            else:
                return self.image.is_pure_color(element=element, percent=percent)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_pure_color_by_xpath(self, ele_xpath, percent):
        """判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色"""
        aklog_debug()
        try:
            element = self.get_element_by_xpath(ele_xpath)
            if not element:
                aklog_debug('%s is not found' % ele_xpath)
                return None
            else:
                return self.image.is_pure_color(element=element, percent=percent)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_correct_ele_image_by_xpath(self, ele_xpath, image_path, percent):
        """判断元素图片跟预期的图片是否一致"""
        aklog_debug('ele_xpath: %s, image_path: %s'
                    % (ele_xpath, image_path))
        try:
            load_image = self.image.load_image(image_path)
            element = self.driver.xpath(ele_xpath).get()
            result = self.image.get_screenshot_by_element(element).same_as(load_image, percent)
            return result
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def is_same_ele_image_by_xpath(self, ele_xpath, image_path, percent):
        """判断元素图片跟预期的图片是否一致"""
        aklog_debug('is_same_ele_image_by_xpath, ele_xpath: %s, image_path: %s'
                    % (ele_xpath, image_path))
        try:
            element = self.driver.xpath(ele_xpath).get()
            result = self.image.compare_image_after_convert_resolution(element, image_path, percent)
            return result
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def is_light_color_by_xpath(self, ele_xpath, rgb_sum=300, percent=0.5):
        """检查图片是否为浅色，当rgb三个数值相加大于rgb_sum，占比超过percent时，认为是浅色"""
        aklog_debug()
        try:
            element = self.get_element_by_xpath(ele_xpath)
            if not element:
                aklog_debug('%s is not found' % ele_xpath)
                return None
            else:
                return self.image.is_light_color(element=element, rgb_sum=rgb_sum, percent=percent)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_light_color_by_id(self, ele_id, rgb_sum=300, percent=0.5):
        """检查图片是否为浅色，当rgb三个数值相加大于rgb_sum，占比超过percent时，认为是浅色"""
        aklog_debug()
        try:
            element = self.get_element_by_id(ele_id)
            if not element:
                aklog_debug('%s is not found' % ele_id)
                return None
            else:
                return self.image.is_light_color(element=element, rgb_sum=rgb_sum, percent=percent)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_normal_color_by_id(self, ele_id, threshold=10):
        """用OpenCV方式检查画面是否正常"""
        aklog_debug()
        try:
            # 获取元素的坐标和大小
            element = self.get_element_by_id(ele_id)
            if not element:
                aklog_debug('%s is not found' % ele_id)
                return None
            return self.image.check_video_image_is_normal(element=element, threshold=threshold)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_normal_color_by_xpath(self, ele_xpath, threshold=10):
        """用OpenCV方式检查画面是否正常"""
        aklog_debug()
        try:
            # 获取元素的坐标和大小
            element = self.get_element_by_xpath(ele_xpath)
            if not element:
                aklog_debug('%s is not found' % ele_xpath)
                return None
            return self.image.check_video_image_is_normal(element=element, threshold=threshold)
        except:
            aklog_debug(traceback.format_exc())
            return None

    # endregion

    # region 图片识别文本

    def get_texts_by_ocr(self, locator) -> Optional[list]:
        """
        有些元素的text属性为空，可以通过识别截图方式获取文字
        """
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return []
            return self.image.get_screenshot_by_element(element).image_ocr_to_texts()
        except Exception as e:
            aklog_error(f'Exception: {e}')
            return []

    def get_string_by_ocr_custom_area_image(self, area):
        """
        在指定区域内识别文字并输出（推荐使用get_text_by_ocr_custom_area_image方法）
        area: (start_x, start_y, end_x, end_y)
        """
        return self.image.get_screenshot_by_custom_size(*area).image_ocr_to_texts()

    def get_text_by_ocr_custom_area_image(self, area):
        """
        在指定区域内识别文字并输出（推荐使用这种方法，更准确）
        area: (start_x, start_y, end_x, end_y)
        """
        return self.image.get_screenshot_by_custom_size(*area).image_ocr_to_texts()

    def ocr_text_by_id(self, ele_id):
        """
        有些元素的text属性为空，可以通过识别截图方式获取文字
        """
        aklog_debug()
        try:
            element = self.driver(resourceId=ele_id)
            return self.image.get_screenshot_by_element(element).image_ocr_to_texts()
        except:
            aklog_debug(traceback.format_exc())
            return None

    def ocr_text_by_xpath(self, ele_xpath):
        """
        有些元素的text属性为空，可以通过识别截图方式获取文字
        """
        aklog_debug()
        try:
            element = self.driver(resourceXpath=ele_xpath)
            return self.image.get_screenshot_by_element(element).image_ocr_to_texts()
        except:
            aklog_debug(traceback.format_exc())
            return None

    # endregion

    # region SeekBar拖动条操作

    def slide_h_seek_bar(self, locator, minimum, maximum, index, duration=0.3):
        """
        水平方向滑动拖动条
        :param locator: 滚动条元素定位信息
        :param minimum: 拖动条最小值，int或float类型
        :param maximum: 拖动条最大值，int或float类型
        :param index: 设置的值，int或float类型
        :param duration: 拖动时间
        :return:
        """
        aklog_debug()
        try:
            if index < minimum:
                index = minimum
            elif index > maximum:
                index = maximum
            lx, ly, width, height = self.__get_ele_bounds(locator)

            average_length = width / (maximum - minimum)
            start_x = lx + 1
            start_y = ly + int(height * 0.5)
            end_y = start_y
            end_x = lx + int(average_length * (index - minimum + 0.4))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_v_seek_bar(self, locator, minimum, maximum, index, duration=0.5):
        """
        垂直方向滑动拖动条
        :param locator: 元素xpath
        :param minimum: 拖动条最小值，int或float类型
        :param maximum: 拖动条最大值，int或float类型
        :param index: 设置的值，int或float类型
        :param duration: 拖动时间
        :return:
        """
        aklog_debug()
        try:
            if index < minimum:
                index = minimum
            elif index > maximum:
                index = maximum
            lx, ly, width, height = self.__get_ele_bounds(locator)
            average_length = height / (maximum - minimum)
            start_x = lx + int(width * 0.5)
            start_y = int(ly + height - 1)
            end_x = start_x
            end_y = int(ly + height - average_length * (index - minimum + 0.8))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_horizontal_seek_bar_by_id(self, ele_id, minimum, maximum, index, duration=0.3):
        """
        水平方向滑动拖动条
        :param ele_id: 滚动条元素ID
        :param minimum: 拖动条最小值，int或float类型
        :param maximum: 拖动条最大值，int或float类型
        :param index: 设置的值，int或float类型
        :param duration: 拖动时间
        :return:
        """
        aklog_debug('slide_horizontal_seek_bar_by_id, ele_id: %s, minimum: %s, maximum: %s,'
                    ' index: %s' % (ele_id, minimum, maximum, index))
        try:
            if index < minimum:
                index = minimum
            elif index > maximum:
                index = maximum
            ele = self.driver(resourceId=ele_id)
            lx, ly, rx, ry = ele.bounds()
            ele_width = int(rx) - int(lx)
            average_length = ele_width / (maximum - minimum)
            start_x = lx + 1
            start_y = int((ly + ry) * 0.5)
            end_x = lx + int(average_length * (index - minimum + 0.4))
            end_y = int((ly + ry) * 0.5)
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_horizontal_seek_bar_by_xpath(self, ele_xpath, minimum, maximum, index, duration=0.3):
        """
        水平方向滑动拖动条
        :param ele_xpath: 滚动条元素xpath
        :param minimum: 拖动条最小值，int或float类型
        :param maximum: 拖动条最大值，int或float类型
        :param index: 设置的值，int或float类型
        :param duration: 拖动时间
        :return:
        """
        aklog_debug()
        try:
            if index < minimum:
                index = minimum
            elif index > maximum:
                index = maximum
            ele = self.driver.xpath(ele_xpath).get()
            lx, ly, rx, ry = ele.bounds
            ele_width = int(rx) - int(lx)
            average_length = ele_width / (maximum - minimum)
            start_x = lx + 1
            start_y = int((ly + ry) * 0.5)
            end_x = lx + int(average_length * (index - minimum + 0.4))
            end_y = int((ly + ry) * 0.5)
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_vertical_seek_bar_by_id(self, ele_id, minimum, maximum, index, duration=0.5):
        """
        垂直方向滑动拖动条
        :param ele_id: 元素ID
        :param minimum: 拖动条最小值，int或float类型
        :param maximum: 拖动条最大值，int或float类型
        :param index: 设置的值，int或float类型
        :param duration: 拖动时间
        :return:
        """
        aklog_debug('slide_vertical_seek_bar_by_id, ele_id: %s, minimum: %s, maximum: %s,'
                    ' index: %s' % (ele_id, minimum, maximum, index))
        try:
            if index < minimum:
                index = minimum
            elif index > maximum:
                index = maximum
            ele = self.driver(resourceId=ele_id)
            lx, ly, rx, ry = ele.bounds()
            ele_height = int(ry) - int(ly)
            average_length = ele_height / (maximum - minimum)
            start_x = int((lx + rx) * 0.5)
            start_y = int(ly + ele_height - 1)
            end_x = int((lx + rx) * 0.5)
            end_y = int(ly + ele_height - average_length * (index - minimum + 0.8))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_vertical_seek_bar_by_xpath(self, ele_xpath, minimum, maximum, index, duration=0.5):
        """
        垂直方向滑动拖动条
        :param ele_xpath: 元素xpath
        :param minimum: 拖动条最小值，int或float类型
        :param maximum: 拖动条最大值，int或float类型
        :param index: 设置的值，int或float类型
        :param duration: 拖动时间
        :return:
        """
        aklog_debug()
        try:
            if index < minimum:
                index = minimum
            elif index > maximum:
                index = maximum
            ele = self.driver.xpath(ele_xpath).get()
            lx, ly, rx, ry = ele.bounds
            ele_height = int(ry) - int(ly)
            average_length = ele_height / (maximum - minimum)
            start_x = int((lx + rx) * 0.5)
            start_y = int(ly + ele_height - 1)
            end_x = int((lx + rx) * 0.5)
            end_y = int(ly + ele_height - average_length * (index - minimum + 0.8))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 系统弹窗Toast控件

    def get_alert_text(self, timeout):
        """获取系统弹窗的文本信息"""
        aklog_debug()
        try:
            self.driver.alert.wait(timeout)
            text = self.driver.alert.text
            aklog_debug("text: %s" % text)
            return text
        except:
            aklog_debug('alert not found')
            return None

    # endregion


if __name__ == '__main__':
    print('debug')
    device_info = {
        'device_name': 'BELAHOMEIOS',
        'deviceid': '00008110-00161DD20138801E',
        'wda_name': 'com.facebook.WebDriverAgentRunner2024043017.xctrunner'
    }
    device_config = config_parse_device_config('config_BELAHOMEIOS_NORMAL')
    app = IOSBaseU2(device_info, device_config)
    app.AppRun_17()
    # app.active_app('com.akuvox.belahome')
    # time.sleep(2)
    app.get_screen_size()
