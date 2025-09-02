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
from testcase.common.aklibAndroidAppium import *
import time
import traceback
from appium.webdriver.webdriver import WebDriver as AppiumWebDriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from appium.webdriver.webelement import WebElement
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


class AndroidBase(object):

    # region 初始化连接

    def __init__(self, device, wait_time):
        self.driver: Optional[AppiumWebDriver] = None
        self._imgs = []
        self.image = None
        self.device = device
        self.appium_port = device.GetLocalPort()
        self.uiautomator2_system_port = device.get_uiautomator2_system_port()
        self.device_config = device.get_device_config()
        self.device_info = device.GetDeviceInfo()
        self.device_name = self.device_info['device_name']
        self.wait_time = wait_time
        self.appium = akAppium(device)
        self.screen_width = 0
        self.screen_height = 0
        if self.device_name and self.device_config and not self.device_config.get_device_name():
            self.device_config.put_device_name(self.device_name)

    def __EnvSetup(self):
        self.appium.Start()
        if not self.appium.IsReady():
            aklog_debug('设备[' + self.device.GetDeviceName() + ']的appium服务未准备完成, 无法正常测试!')
            self.appium.Stop()
            # self.appium = None
        else:
            self.device_connect()

    def device_connect(self):
        for i in range(0, 3):
            self.appium.remove_screen_saver()
            self.device.Connect(True)  # 长连接
            if not self.device.IsReady():
                aklog_debug('设备[' + self.device.GetDeviceName() + ']连接失败，重试: ' + str(i + 1))
                self.device.Disconnect()
                time.sleep(3)
                continue
            else:
                return True
        aklog_debug('设备[' + self.device.GetDeviceName() + ']本身未准备完成, 无法正常测试!')
        self.device.Disconnect()
        self.appium.Stop()
        # self.device = None
        return False

    def AppRun(self):
        for i in range(2):
            self.__EnvSetup()
            if not self.device.IsReady() or not self.appium.IsReady():
                if i == 0:
                    aklog_debug('环境未准备完成, 重试')
                    time.sleep(10)
                    continue
                aklog_error('Appium环境未准备完成, 无法继续测试, 异常退出!')
                param_put_failed_to_exit_enable(True)
                return False
            else:
                aklog_debug('环境准备完成')
                self.driver = self.device.GetDeviceCtrl()
                self.image = Image_process(self.driver)
                return True

    def AppStop(self):
        self.device.Disconnect()
        self.appium.Stop()
        return True

    def app_reconnect(self):
        aklog_debug('app_reconnect')
        if not self.device_connect():
            aklog_debug('环境未准备完成, 无法继续测试, 异常退出!')
            exit(1)
        else:
            aklog_debug('环境准备完成')
            self.driver = self.device.GetDeviceCtrl()
            self.image = Image_process(self.driver)

    def app_quit(self):
        aklog_debug('app_quit')
        self.driver.quit()

    def GetDriver(self):
        return self.driver

    def return_home(self):
        # 回到Smartplus的主页
        self.device.Connect(True)  # 长连接

    # endregion

    # region 设备信息

    def get_device_info(self):
        return self.device.GetDeviceInfo()

    def get_device_config(self):
        return self.device_config

    def get_appium_port(self):
        return self.appium_port

    def get_uiautomator2_system_port(self):
        return self.uiautomator2_system_port

    # 截图储存list
    def reset_imgs(self):
        self._imgs = []
        param_reset_screenshots_imgs()

    def get_imgs(self):
        return self._imgs

    # endregion

    # region 页面活动相关

    def check_driver_connected(self):
        try:
            ret = self.driver.page_source
            if ret:
                return True
            aklog_error('Error:　Android App is disconnected!!!')
            return False
        except:
            aklog_error('Error:　Android App is disconnected!!!')
            return

    def get_page_source(self):
        """获取页面资源，可用于判断设备是否连接正常"""
        aklog_debug('get_page_source')
        try:
            if self.driver:
                page_source = self.driver.page_source
                # aklog_debug('page_source: %s' % page_source)
                return page_source
            else:
                aklog_error('driver not connect')
                return None
        except:
            aklog_warn('get_page_source failed, %s' % traceback.format_exc())

            return None

    def get_current_package(self):
        aklog_debug('get_current_package')
        try:
            current_package = self.driver.current_package
            aklog_debug('current_package: %s' % current_package)
            return current_package
        except:
            aklog_debug('get current package failed, %s' % traceback.format_exc())
            return None

    def active_app_package(self, app_package):
        aklog_debug('active_app_package: %s' % app_package)
        try:
            self.driver.activate_app(app_package)
            return True
        except:
            return False

    def background_app_package(self, app_package, timeout=-1):
        aklog_debug('background_app_package: %s' % app_package)
        try:
            self.driver.background_app(timeout)
            return True
        except:
            return False

    def print_current_activity(self):
        """打印当前页面活动"""
        aklog_debug('current_activity : %s' % self.driver.current_activity)

    def get_current_activity(self):
        aklog_debug('get_current_activity')
        try:
            if hasattr(self, 'check_phone_process_alive'):
                self.check_phone_process_alive()
            current_activity = self.driver.current_activity
            aklog_debug('current_activity: %s' % current_activity)
            return current_activity
        except:
            aklog_debug('get current activity failed, %s' % traceback.format_exc())
            return None

    def is_correct_activity(self, app_package, app_activity):
        aklog_debug('is_correct_activity, app_activity: %s' % app_activity)
        current_activity = self.get_current_activity()
        if current_activity == app_activity or current_activity == app_package + app_activity:
            aklog_debug('current activity is correct')
            return True
        else:
            aklog_debug('current activity is error')
            return False

    def start_app_activity_ignore_error(self, app_package, app_activity):
        aklog_debug('start_app_activity_ignore_error, '
                    'app_package: %s, app_activity: %s' % (app_package, app_activity))
        try:
            self.driver.execute_script("mobile: startActivity", {
                "appPackage": app_package,
                "appActivity": app_activity
            })
            return True
        except:
            aklog_debug('打开 %s/%s 失败, %s' % (
                app_package, app_activity, str(traceback.format_exc())))
            return False

    def start_app_activity(self, app_package, app_activity, timeout=5, interval=1):
        aklog_debug('start_app_activity app_package: %s, app_activity: %s' % (
            app_package, app_activity))
        try:
            self.driver.execute_script("mobile: startActivity", {
                "appPackage": app_package,
                "appActivity": app_activity
            })
            if self.driver.wait_activity(app_activity, timeout, interval):
                aklog_debug('启动 %s/%s 成功' % (app_package, app_activity))
                time.sleep(2)
                return True
            else:
                aklog_debug('启动 %s/%s 失败' % (app_package, app_activity))
                return False
        except:
            aklog_debug('打开 %s/%s 失败, %s' % (
                app_package, app_activity, str(traceback.format_exc())))
            return False

    def wait_activity(self, app_activity, timeout=5, interval=1):
        aklog_debug('wait_activity, activity: %s' % app_activity)
        if self.driver.wait_activity(app_activity, timeout, interval):
            aklog_debug('enter activity %s success' % app_activity)
            return True
        else:
            aklog_debug('enter activity %s failed' % app_activity)
            return False

    def wait_activity_switch(self, app_package, app_activity, timeout=5, interval=1):
        """等待页面切换，间隔interval时间检查一次，超时时间为timeout"""
        aklog_debug('wait_activity_switch, app: %s, activity: %s' % (app_package, app_activity))
        activity = app_package + app_activity
        current_activity = self.get_current_activity()
        if app_package not in current_activity:
            if self.driver.wait_activity(app_activity, timeout, interval) or \
                    self.driver.wait_activity(activity, timeout, interval):
                aklog_debug('enter activity %s success' % app_activity)
                return True
            else:
                aklog_debug('enter activity %s failed' % app_activity)
                return False
        else:
            if self.driver.wait_activity(activity, timeout, interval) or \
                    self.driver.wait_activity(app_activity, timeout, interval):
                aklog_debug('enter activity %s success' % app_activity)
                return True
            else:
                aklog_debug('enter activity %s failed' % app_activity)
                return False

    def wait_activity_leave(self, activity, timeout=5):
        """
        等待页面切换，间隔interval时间检查一次，超时时间为timeout
        :param activity: 原来的页面活动名称
        :param timeout: 等待超时时间
        :return:
        """
        aklog_debug('wait_activity_leave, activity: %s' % activity)
        for i in range(timeout):
            if self.get_current_activity() == activity:
                time.sleep(1)
                continue
            else:
                aklog_debug('wait activity leave complete')
                return True
        aklog_debug('wait activity leave failed')
        return False

    # endregion

    # region 实体按键操作

    def press_key(self, key_code):
        aklog_debug('press_key %s' % key_code)
        try:
            self.driver.keyevent(key_code)
            return True
        except:
            aklog_debug('press_key %s failed' % key_code)
            return False

    def press_key_home(self):
        aklog_debug('press_key_home')
        for i in range(3):
            try:
                self.driver.keyevent(3)
                time.sleep(1)
                return True
            except:
                aklog_debug('press_key_home failed, reconnect' + str(traceback.format_exc()))
                self.app_reconnect()
        aklog_debug('press_key_home failed')
        return False

    def press_key_back(self):
        aklog_debug('press_key_back')
        try:
            self.driver.keyevent(4)
            time.sleep(1)
            return True
        except:
            aklog_debug('press_key_back failed')
            return False

    # endregion

    # region 输入框相关

    def input_edit_by_name(self, name, content):
        aklog_debug("input_edit_by_name : %s, content: %s" % (name, content))
        try:
            eleXpath = "//*[@text='" + name + "']"
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, eleXpath)))
            # 先清空输入框
            ele.clear()
            # 再次输入值
            ele.send_keys(content)
            time.sleep(0.2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_edit_by_id(self, eleId, content):
        aklog_debug("input_edit_by_id : %s, content: %s" % (eleId, content))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.visibility_of_element_located((By.ID, eleId)))
            # 先清空输入框
            ele.clear()
            # 再次输入值
            ele.send_keys(content)
            time.sleep(0.2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_edit_by_xpath(self, eleXpath, content):
        aklog_debug("input_edit_by_xpath :  %s, content: %s" % (eleXpath, content))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, eleXpath)))
            # 先清空输入框
            ele.clear()
            # 再次输入值
            ele.send_keys(content)
            time.sleep(0.2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_content_by_id(self, ele_id, content):
        """输入前不清空，可以用于seekbar滚动条设置"""
        aklog_debug("input_content_by_id : %s, content: %s" % (ele_id, content))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.visibility_of_element_located((By.ID, ele_id)))
            ele.send_keys(content)
            time.sleep(0.2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_content_by_xpath(self, eleXpath, content):
        """输入前不清空，可以用于seekbar滚动条设置"""
        aklog_debug("input_edit_by_xpath : %s, content: %s" % (eleXpath, content))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, eleXpath)))
            # 再次输入值
            ele.send_keys(content)
            time.sleep(0.2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_in_focused_edit(self, content):
        """在焦点输入框控件输入文本"""
        self.input_edit_by_xpath('.//android.widget.EditText[@focused="true"]', content)

    # 输入框复制、剪切、粘贴操作
    def copy_content_by_xpath(self, xpath):
        # 通过xpath复制指定内容
        self.driver.find_elements(AppiumBy.XPATH, xpath)[0].send_keys(Keys.CONTROL, 'c')
        time.sleep(1)

    def cut_content_by_xpath(self, xpath):
        # 通过xpath剪切指定内容
        self.driver.find_elements(AppiumBy.XPATH, xpath)[0].send_keys(Keys.CONTROL, 'x')
        time.sleep(1)

    def paste_content_by_xpath(self, xpath):
        # 通过xpath粘贴指定内容
        self.driver.find_elements(AppiumBy.XPATH, xpath)[0].send_keys(Keys.CONTROL, 'v')
        time.sleep(1)

    # endregion

    # region 点击操作

    def click_btn_by_id(self, eleId, sec=0.2, wait_time=None, ignore_error=False):
        aklog_debug("click_btn_by_id : %s" % eleId)
        try:
            if not wait_time:
                wait_time = self.wait_time

            if '|' not in eleId:
                WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.ID, eleId))).click()
            else:
                xpath = self.__get_id_list_expression(eleId)
                WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.XPATH, xpath))).click()
            time.sleep(sec)
            return True
        except TimeoutException:
            aklog_error(f'click btn failed by id: {eleId}, ele not found in timeout : {wait_time} !!')
            return False
        except:
            aklog_debug('click btn failed by id: {}'.format(eleId))
            if hasattr(self, 'check_phone_process_alive'):
                self.check_phone_process_alive()
            self.check_driver_connected()
            if not ignore_error:
                aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_by_xpath(self, eleXpath, sec=0.2, wait_time=None):
        aklog_debug("click_btn_by_xpath : %s" % eleXpath)
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((By.XPATH, eleXpath))).click()
            time.sleep(sec)
            return True
        except TimeoutException:
            aklog_error(f'click btn failed by xpath: {eleXpath}, ele not found in timeout : {wait_time} !!')
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            self.check_driver_connected()
            return False

    def click_btn_by_accessibility_id(self, ele_id, sec=0.2):
        """Content-desc类型的元素可以用这个来定位"""
        aklog_debug("click_btn_by_accessibility_id : %s" % ele_id)
        try:
            # ele_xpath = "//*[@content-desc='" + ele_id + "']"
            # WebDriverWait(self.driver, self.wait_time).until(
            #     EC.visibility_of_element_located((By.XPATH, ele_xpath))).click()
            WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id))).click()
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            self.check_driver_connected()
            return False

    def click_btn_by_name(self, name, sec=0.1, wait_time=None):
        aklog_debug("click_btn_by_name : %s" % name)
        try:
            if not wait_time:
                wait_time = self.wait_time
            if '|' in name:
                list1 = [i.strip() for i in name.split('|') if i.strip()]
                xpath1 = '//*['
                for i in list1:
                    xpath1 += '@text="{}"'.format(i)
                    if i != list1[-1]:
                        xpath1 += ' or '
                xpath1 += ']'
                eleXpath = xpath1
            else:
                eleXpath = "//*[@text='" + name + "']"
            WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((By.XPATH, eleXpath))).click()
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            self.check_driver_connected()
            return False

    def click_btn_by_contains_name(self, name, sec=0.1, wait_time=None):
        """匹配按钮部分名称，模糊匹配，点击按钮"""
        aklog_debug("click_btn_by_contains_name : %s" % name)
        try:
            if not wait_time:
                wait_time = self.wait_time
            eleXpath = "//*[contains(@text,'" + name + "')]"
            WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((By.XPATH, eleXpath))).click()
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            self.check_driver_connected()
            return False

    def click_btn_by_names(self, *names, sec=0.1, wait_time=None):
        """匹配多个不同名称点击按钮，names可以传入多个名称"""
        try:
            if not wait_time:
                wait_time = self.wait_time
            # 传入多个名称，组合成一个Xpath，只要一个名称匹配成功即可
            names_len = len(names)
            eleXpath = '//*['
            for i in range(names_len):
                eleXpath += '@text="%s"' % names[i]
                if i == names_len - 1:
                    eleXpath += ']'
                else:
                    eleXpath += ' or '
            aklog_debug("click_btn_by_names, xpath: %s" % eleXpath)
            WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((By.XPATH, eleXpath))).click()
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            self.check_driver_connected()
            return False

    def click_location(self, x, y, duration=None):
        aklog_debug()
        try:
            self.driver.tap([(x, y)], duration)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def tap_location(self, x, y, duration=None):
        aklog_debug()
        try:
            self.driver.tap([(x, y)], duration)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def tap_ele_by_location(self, eleid, times=1):
        """快速点击, 用于如门口机点击10次进入setting"""
        ret = self.get_ele_location_by_id(eleid)
        x = ret.get('x')
        y = ret.get('y')
        for i in range(times):
            sub_process_exec_command(
                'adb -s {} shell input tap {} {}'.format(self.device_info.get("deviceid"), x, y))

    def click_find_element_by_class_name_index(self, class_name, index):
        """尽量不使用该方法，容易受到界面改动影响，后期维护工作量较大"""
        aklog_debug()
        # index从0开始
        try:
            self.driver.find_elements(class_name)[index].click()
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def get_value_find_element_by_class_name_index(self, class_name, index):
        """尽量不使用该方法，容易受到界面改动影响，后期维护工作量较大"""
        aklog_debug()
        # index从0开始
        try:
            value = self.driver.find_elements(AppiumBy.CLASS_NAME, class_name)[index].text
            return value
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_value_by_id_index(self, eleId, index):
        aklog_debug()
        # index从0开始
        try:
            value = self.driver.find_elements(AppiumBy.ID, eleId)[index].text
            return value
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_len_by_id(self, elem_id):
        aklog_debug('get_value_by_id_index')
        try:
            all_elements = self.driver.find_elements(AppiumBy.ID, elem_id)
            return int(len(all_elements))
        except:
            aklog_debug(traceback.format_exc())
            return None

    def action_click_location(self, x, y):
        aklog_debug('click_location %s %s' % (x, y))
        try:
            self.tap_location(x, y)
        except:
            aklog_debug(traceback.format_exc())

    def click_screen_mid_location(self, mid_x_length=0.5, mid_y_length=0.5, duration=None):
        """
        点击屏幕坐标
        :param duration: 点击时间长短
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

        self.tap_location(screen_mid_x, screen_mid_y, duration)

    def click_btn_location_by_xpath(self, ele_xpath, duration=200, mid_x_length=0.5, mid_y_length=0.5):
        """点击元素内的某个坐标点，有些元素中心点无法点击时，可以用该方法"""
        aklog_debug("click_btn_location_by_xpath, ele_xpath: %s" % ele_xpath)
        try:
            ele_location = self.get_ele_location_by_xpath(ele_xpath)
            ele_size = self.get_ele_size_by_xpath(ele_xpath)
            ele_mid_x = ele_location['x'] + ele_size[0] * mid_x_length
            ele_mid_y = ele_location['y'] + ele_size[1] * mid_y_length
            self.driver.tap([(ele_mid_x, ele_mid_y)], duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_location_by_id(self, ele_id, duration=200, mid_x_length=0.5, mid_y_length=0.5):
        """点击元素内的某个坐标点，有些元素中心点无法点击时，可以用该方法"""
        aklog_debug("click_btn_location_by_id, ele_id: %s" % ele_id)
        try:
            ele_location = self.get_ele_location_by_id(ele_id)
            ele_size = self.get_ele_size_by_id(ele_id)
            ele_mid_x = ele_location['x'] + ele_size[0] * mid_x_length
            ele_mid_y = ele_location['y'] + ele_size[1] * mid_y_length
            self.driver.tap([(ele_mid_x, ele_mid_y)], duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_out_location_by_id(self, ele_id):
        """点击弹窗之外的地方来取消弹窗"""
        aklog_debug("click_btn_out_location_by_id, ele_id: %s" % ele_id)
        try:
            # 先获取弹窗窗口的左上角坐标和尺寸
            ele_location = self.get_ele_location_by_id(ele_id)
            ele_size = self.get_ele_size_by_id(ele_id)

            # 获取屏幕尺寸
            screen_width, screen_height = self.get_screen_size()

            # 先判断左右两边是否可以点击，如果左右两边都无法点击，则点击上下两边
            if ele_location['x'] > 1:
                x = int(ele_location['x'] / 2)
                y = int(screen_height / 2)
            elif ele_location['x'] + ele_size[0] < screen_width - 1:
                x = ele_location['x'] + ele_size[0] + int((screen_width - ele_location['x'] - ele_size[0]) / 2)
                y = int(screen_height / 2)
            else:
                x = int(screen_width / 2)
                if ele_location['y'] > 1:
                    y = int(ele_location['y'] / 2)
                elif ele_location['y'] + ele_size[1] < screen_height - 1:
                    y = ele_location['y'] + ele_size[1] + int((screen_height - ele_location['y'] - ele_size[1]) / 2)
                else:
                    y = 0
            aklog_debug('x: %s, y: %s' % (x, y))
            self.tap_location(x, y)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_quickly_by_xpath(self, eleXpath, times=1, duration=200):
        """快速多次点击元素"""
        aklog_debug("click_btn_quickly_by_xpath : %s, times: %s" % (eleXpath, times))
        try:
            ele_location = self.get_ele_location_by_xpath(eleXpath)
            ele_size = self.get_ele_size_by_xpath(eleXpath)
            ele_mid_x = ele_location['x'] + ele_size[0] * 0.5
            ele_mid_y = ele_location['y'] + ele_size[1] * 0.5
            for i in range(0, times):
                self.driver.tap([(ele_mid_x, ele_mid_y)], duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_quickly_by_id(self, eleID, times=1, duration=200):
        """快速多次点击元素"""
        aklog_debug("click_btn_quickly_by_id : %s, times: %s" % (eleID, times))
        try:
            ele_location = self.get_ele_location_by_id(eleID)
            ele_size = self.get_ele_size_by_id(eleID)
            ele_mid_x = ele_location['x'] + ele_size[0] * 0.5
            ele_mid_y = ele_location['y'] + ele_size[1] * 0.5
            for i in range(0, times):
                self.driver.tap([(ele_mid_x, ele_mid_y)], duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 按钮开关操作

    def set_checked_button_by_id(self, ele_id, status='Enable'):
        """ 设置按钮开启或关闭，Status可以设置为 Enable 和 Disable """
        aklog_debug()
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, ele_id)))
            if status == 'Enable' or status is True or str(status) == '1':
                if ele.get_attribute('checked') == 'false':
                    ele.click()
                    time.sleep(0.2)
                return True
            elif status == 'Disable' or status is False or str(status) == '0':
                if ele.get_attribute('checked') == 'true':
                    ele.click()
                    time.sleep(0.2)
                return True
            else:
                aklog_debug('Status参数值 %s 不正确')
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def Set_checked_Button_ById(self, eleId, Status='Enable'):
        return self.set_checked_button_by_id(eleId, Status)

    def set_checked_button_by_xpath(self, ele_xpath, status='Enable'):
        """ 设置按钮开启或关闭，Status可以设置为 Enable 和 Disable """
        aklog_debug()
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            if status == 'Enable' or status is True or str(status) == '1':
                if ele.get_attribute('checked') == 'false':
                    ele.click()
                    time.sleep(0.2)
                return True
            elif status == 'Disable' or status is False or str(status) == '0':
                if ele.get_attribute('checked') == 'true':
                    ele.click()
                    time.sleep(0.2)
                return True
            else:
                aklog_debug('Status参数值 %s 不正确')
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def Set_checked_Button_ByXpath(self, eleXpath, Status='Enable'):
        return self.set_checked_button_by_xpath(eleXpath, Status)

    # endregion

    # region 元素长按操作

    def long_press_by_xpath(self, ele_xpath, duration=2000):
        """
        通过xpath长按duration
        duration: 默认单位为毫秒，如果传入的值小于100，认为传入的是秒数
        """
        aklog_debug('long_press_by_xpath, ele_xpath: %s, duration: %s' % (ele_xpath, duration))
        try:
            # def center_rect(r):
            #     center_x = int(r['x'] + r['width'] / 2)
            #     center_y = int(r['y'] + r['height'] / 2)
            #     return center_x, center_y
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            # x, y = center_rect(ele.rect)
            if duration < 100:
                duration_sec = duration
            else:
                duration_sec = duration / 1000
            ActionChains(self.driver).click_and_hold(ele).pause(duration_sec).release(ele).perform()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def long_press_by_name(self, ele_name, duration=2000):
        """
        通过name长按duration
        duration: 默认单位为毫秒，如果传入的值小于100，认为传入的是秒数
        """
        aklog_debug('long_press_by_name, ele_name: %s, duration: %s' % (ele_name, duration))
        try:
            # def center_rect(r):
            #     center_x = int(r['x'] + r['width'] / 2)
            #     center_y = int(r['y'] + r['height'] / 2)
            #     return center_x, center_y
            ele_xpath = "//*[@text='" + ele_name + "']"
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            # x, y = center_rect(ele.rect)
            if duration < 100:
                duration_sec = duration
            else:
                duration_sec = duration / 1000
            ActionChains(self.driver).click_and_hold(ele).pause(duration_sec).release(ele).perform()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def long_press_by_id(self, ele_id, duration=2000):
        """
        长按
        duration: 默认单位为毫秒，如果传入的值小于100，认为传入的是秒数
        """
        aklog_debug('long_press_by_id, ele_id: %s, duration: %s' % (ele_id, duration))
        try:
            # def center_rect(r):
            #     center_x = int(r['x'] + r['width'] / 2)
            #     center_y = int(r['y'] + r['height'] / 2)
            #     return center_x, center_y
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.ID, ele_id)))
            # x, y = center_rect(ele.rect)
            if duration < 100:
                duration_sec = duration
            else:
                duration_sec = duration / 1000
            ActionChains(self.driver).click_and_hold(ele).pause(duration_sec).release(ele).perform()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 获取元素信息

    @staticmethod
    def __get_id_list_expression(id_list_str):
        xpath = '//*['
        idlist = [i.strip() for i in id_list_str.split('|')]
        for _id in idlist:
            xpath = xpath + '@resource-id="{}"'.format(_id)
            xpath = xpath + ' or '
        xpath = xpath.rstrip(' or ') + ']'
        return xpath

    def get_value_by_id(self, eleId, wait_time=None):
        """
        eleID:
            str.  支持输入多个ID, 同时or匹配,  用'|' 分隔
            eg:
                get_values_by_id('com.akuvox.phone:id/tv_group_child_name | com.akuvox.phone:id/tv_group_name')
        """
        aklog_debug("get_value_by_id : %s" % eleId)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            if '|' not in eleId:
                value = WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.ID, eleId))).text
                aklog_debug("text : %s" % value)
                return value
            else:
                xpath = self.__get_id_list_expression(eleId)
                value = WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                aklog_debug("text : %s" % value)
                return value
        except TimeoutException:
            aklog_error(f'get value failed by id: {eleId}, ele not found in timeout : {wait_time} !!')
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_value_by_xpath(self, eleXpath, wait_time=None):
        aklog_debug("get_value_by_xpath : %s" % eleXpath)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            value = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH, eleXpath))).text
            aklog_debug("text : %s" % value)
            return value
        except TimeoutException:
            aklog_error(f'get value failed by xpath: {eleXpath}, ele not found in timeout : {wait_time} !!')
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_values_by_xpath(self, eleXpath, wait_time=None):
        value = []
        aklog_debug("get_values_by_xpath : %s" % eleXpath)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            elelist = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_all_elements_located((By.XPATH, eleXpath)))
            for i in elelist:
                value.append(i.text)
            aklog_debug("text : %s" % value)
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_values_by_id(self, eleID, wait_time=None):
        """
        eleID:
            str.  支持输入多个ID, 同时or匹配,  用'|' 分隔
            eg:
                get_values_by_xpath('com.akuvox.phone:id/tv_group_child_name | com.akuvox.phone:id/tv_group_name')
        """
        value = []
        aklog_debug("get_values_by_id : %s" % eleID)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            if '|' not in eleID:
                elelist = WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_all_elements_located((By.ID, eleID)))
                for i in elelist:
                    value.append(i.text)
                aklog_debug("text : %s" % value)
                return value
            else:
                xpath = self.__get_id_list_expression(eleID)
                elelist = WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_all_elements_located((By.XPATH, xpath)))
                for i in elelist:
                    value.append(i.text)
                aklog_debug("text : %s" % value)
                return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_values_by_same_prefix_id(self, _id):
        """输入部分id内容, 获取包括该ID的元素内容"""
        aklog_debug("get_values_by_same_prefix_id : %s" % _id)
        ele_xpath = '//*[contains(@resource-id, "{}")]'.format(_id)
        try:
            ele_lists = WebDriverWait(self.driver, self.wait_time).until(
                lambda x: x.find_elements(AppiumBy.XPATH, ele_xpath))
            if ele_lists is None:
                aklog_debug('No found elements with prefix id: %s' % _id)
                return []
            values = [ele.text for ele in ele_lists if ele.text]
            aklog_debug("%s, texts: %s" % (ele_xpath, str(values)))
            return values
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_value_by_name(self, name, wait_time=None):
        aklog_debug("get_value_by_name : %s" % name)
        eleXpath = "//*[@text='" + name + "']"
        if wait_time is None:
            wait_time = self.wait_time
        try:
            value = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH, eleXpath))).text
            aklog_debug("text : %s" % value)
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_text_by_uiautomator(self, ele_uiautomator, wait_time=None):
        """new UiSelector().text("xx")"""
        aklog_debug("get_text_by_uiautomator : %s" % ele_uiautomator)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            value = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, ele_uiautomator))).text
            aklog_debug("text : %s" % value)
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_counts_by_xpath(self, eleXpath):
        """获取相同Xpath元素的数量"""
        aklog_debug("get_ele_counts_by_xpath : %s" % eleXpath)
        try:
            elements = self.driver.find_elements(AppiumBy.XPATH, eleXpath)
            counts = len(elements)
            aklog_debug('counts: %s' % counts)
            return counts
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_by_xpath(self, ele_xpath, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、password、selected，返回的是"true"和"false"的str类型
        2、.get_attribute("name")  返回的是‘content_desc’的值
        3、.get_attribute("className")  返回的是‘class’的值
        """
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            value = ele.get_attribute(attribute_type)
            aklog_debug('eleXpath: %s, attribute: %s, value: %s' %
                        (ele_xpath, attribute_type, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def Get_attribute_ByXpath(self, eleXpath, attribute_type):
        self.get_attribute_by_xpath(eleXpath, attribute_type)

    def get_attribute_by_id(self, eleId, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、password、selected，返回的是"true"和"false"的str类型
        2、.get_attribute("name")  返回的是‘content_desc’的值
        3、.get_attribute("className")  返回的是‘class’的值
        """
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, eleId)))
            value = ele.get_attribute(attribute_type)
            aklog_debug('eleId: %s, attribute: %s, value: %s' % (eleId, attribute_type, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def Get_attribute_ById(self, eleId, attribute_type):
        return self.get_attribute_by_id(eleId, attribute_type)

    def is_enabled_by_id(self, ele_id):
        """判断控件是否可以操作"""
        aklog_debug('is_enabled_by_id: %s' % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, ele_id)))
            enabled = ele.get_attribute('enabled')
            aklog_debug('enabled: %s' % enabled)
            if enabled == 'true':
                return True
            else:
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    # endregion

    # region 复选框相关

    def check_by_id(self, eleId):
        """ 勾选 """
        aklog_debug('check_by_id: %s' % eleId)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, eleId)))
            if ele.get_attribute('checked') == 'false':
                ele.click()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def check_by_xpath(self, ele_xpath):
        """ 勾选 """
        aklog_debug()
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            if ele.get_attribute('checked') == 'false':
                ele.click()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def uncheck_by_xpath(self, ele_xpath):
        """ 取消勾选 """
        aklog_debug()
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            if ele.get_attribute('checked') == 'true':
                ele.click()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def uncheck_by_id(self, eleId):
        """ 取消勾选 """
        aklog_debug('uncheck_by_id: %s' % eleId)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, eleId)))
            if ele.get_attribute('checked') == 'true':
                ele.click()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def is_checked_by_xpath(self, ele_xpath):
        """判断元素（单选框或复选框）是否选中"""
        aklog_debug()
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            if ele.get_attribute('checked') == 'true':
                aklog_debug('checked: true')
                return True
            else:
                aklog_debug('checked: false')
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def is_checked_eleByXpath(self, eleXpath):
        return self.is_checked_by_xpath(eleXpath)

    def is_checked_by_id(self, ele_id):
        """判断元素（单选框或复选框）是否选中"""
        aklog_debug('is_checked_by_id: %s' % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, ele_id)))
            if ele.get_attribute('checked') == 'true':
                aklog_debug('checked: true')
                return True
            else:
                aklog_debug('checked: false')
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 元素是否存在或可见

    def is_exist(self, id_xpath, wait_time=None):
        aklog_info()
        if id_xpath.startswith('/'):
            elexpath = id_xpath
        else:
            elexpath = '//*[@text="{}" or @resource-id="{}"]'.format(id_xpath, id_xpath)
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH, elexpath)))
            return True
        except:
            aklog_warn('%s is not exist' % elexpath)
            self.check_driver_connected()
            return False

    def is_exists(self, id_xpath, wait_time=None):
        return self.is_exist(id_xpath, wait_time)

    def is_exist_ele_by_id(self, eleId, wait_time=None, printlog=True):
        """统一U2接口名"""
        return self.is_exist_and_visible_ele_by_id(eleId, wait_time, printlog)

    def is_exist_ele_by_xpath(self, ele_xpath, wait_time=None):
        return self.is_exist_and_visible_ele_by_xpath(ele_xpath, wait_time)

    def is_exist_eleByXpath(self, ele_xpath):
        """判断元素是否存在"""
        aklog_debug('is_exist_eleByXpath, ele_xpath: %s' % ele_xpath)
        try:
            WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.XPATH, ele_xpath)))
            return True
        except:
            aklog_debug('%s is not exist' % ele_xpath)
            self.check_driver_connected()
            return False

    def is_exist_and_visible_ele_by_xpath(self, ele_xpath, wait_time=None):
        """判断元素是否存在并可见"""
        aklog_debug('is_exist_and_visible_ele_by_xpath, ele_xpath: %s' % ele_xpath)
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            return True
        except:
            aklog_debug('%s is not exist' % ele_xpath)
            self.check_driver_connected()
            return False

    def is_exist_and_visible_ele_by_name(self, ele_name, wait_time=None):
        """判断元素是否存在并可见"""
        aklog_debug('is_exist_and_visible_ele_by_name, ele_name: %s' % ele_name)
        ele_xpath = "//*[@text='" + ele_name + "']"
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            return True
        except:
            aklog_debug('%s is not exist' % ele_name)
            self.check_driver_connected()
            return False

    def is_exist_and_visible_ele_by_names(self, *ele_names, wait_time=None):
        """判断元素是否存在并可见"""
        # 传入多个名称，组合成一个Xpath，只要一个名称匹配成功即可
        names_len = len(ele_names)
        ele_xpath = '//*['
        for i in range(names_len):
            ele_xpath += '@text="%s"' % ele_names[i]
            if i == names_len - 1:
                ele_xpath += ']'
            else:
                ele_xpath += ' or '
        aklog_debug("is_exist_and_visible_ele_by_names, xpath: %s" % ele_xpath)
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            return True
        except:
            aklog_debug('%s is not exist' % ele_xpath)
            self.check_driver_connected()
            return False

    def is_exist_eleById(self, eleId, wait_time=None):
        """判断元素是否存在"""
        aklog_debug('is_exist_eleById, eleId: %s' % eleId)
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.ID, eleId)))
            return True
        except:
            aklog_debug('%s is not exist' % eleId)
            self.check_driver_connected()
            return False

    def is_exist_and_visible_ele_by_id(self, eleId, wait_time=None, printlog=True):
        """判断元素是否存在并可见"""
        aklog_debug('is_exist_and_visible_ele_by_id, eleId: %s' % eleId)
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.ID, eleId)))
            return True
        except:
            self.check_driver_connected()
            if printlog:
                aklog_debug('%s is not exist' % eleId)
            if hasattr(self, 'check_phone_process_alive'):
                self.check_phone_process_alive()
            return False

    def is_exist_ele_by_name(self, ele_name, wait_time=None):
        """统一U2接口名"""
        return self.is_exist_eleByName(ele_name, wait_time)

    def is_exist_eleByName(self, Name, wait_time=None):
        """判断元素是否存在"""
        aklog_debug('is_exist_eleByName, Name: %s' % Name)
        eleXpath = "//*[@text='" + Name + "']"
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.XPATH, eleXpath)))
            return True
        except:
            aklog_debug('%s is not exist' % Name)
            self.check_driver_connected()
            return False

    def wait_for_visible_by_id(self, ele_id, wait_time=5):
        aklog_debug('wait_for_visible_by_id, ele: %s' % ele_id)
        try:
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.ID, ele_id)))
            return True
        except:
            aklog_debug('%s is not found' % ele_id)
            return False

    # endregion

    # region 坐标点击或滑动

    def SwipeScreen(self, startX, startY, endX, endY, duration=2000):
        # 区域保护, 避免超出区域
        screen = self.get_screen_size()
        startX = startX + 1 if startX == 0 else startX - 1 if startX == screen[0] else startX
        startY = startY + 1 if startY == 0 else startY - 1 if startY == screen[1] else startY
        endX = endX + 1 if endX == 0 else endX - 1 if endX == screen[0] else endX
        endY = endY + 1 if endY == 0 else endY - 1 if endY == screen[1] else endY
        aklog_debug('(%s, %s) -> (%s, %s), duration: %s' % (startX, startY, endX, endY, duration))
        for i in range(0, 3):
            try:
                self.driver.swipe(startX, startY, endX, endY, duration)
            except:
                aklog_debug('遇到未知异常, 程序退出! ' + str(traceback.format_exc()))
            else:
                return True
            time.sleep(1)
        return False

    def touch_swipe(self, x, y, duration=1):  # 点击坐标  ,x1,x2,y1,y2,duration
        # method
        # explain: 点击坐标
        # parameter
        # explain：【x, y】坐标值,【duration】:给的值决定了点击的速度
        # Usage:
        # device.touch_coordinate(277, 431)  # 277.431为点击某个元素的x与y值
        screen_width = self.driver.get_window_size()['width']  # 获取当前屏幕的宽
        screen_height = self.driver.get_window_size()['height']  # 获取当前屏幕的高
        a = (float(x) / screen_width) * screen_width
        x1 = int(a)
        b = (float(y) / screen_height) * screen_height
        y1 = int(b)
        self.driver.swipe(x1, y1, x1, y1, duration)

    def swipe_right(self, element: Union[WebElement, str, None] = 'screen', duration=1000, length=0.5, y_offset=0.25,
                    sec=0.1):
        """
        如果element没有传参或者为'screen', 从屏幕最左侧向右滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果element有传入元素，则在元素框范围内从最左侧向右滑动
        y_offset: 滑动的位置: location['y'] + size['height'] * y_offset
        """
        aklog_debug('swipe_right')
        try:
            if element is None:
                aklog_debug('element is not exist')
                return False
            if element == 'screen':
                screen = self.get_screen_size()
                start_x = int(screen[0] * (1 - length) / 2)
                start_y = int(screen[1] * y_offset)
                end_x = int(screen[0] * (1 + length) / 2)
                end_y = int(screen[1] * y_offset)
            else:
                location = element.location
                size = element.size
                start_x = int(location['x'] + size['width'] * (1 - length) / 2)
                start_y = int(location['y'] + size['height'] * y_offset)
                end_x = int(location['x'] + size['width'] * (1 + length) / 2)
                end_y = int(location['y'] + size['height'] * y_offset)
            aklog_debug('(%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_left(self, element: Union[WebElement, str, None] = 'screen', duration=1000, length=0.5, y_offset=0.25,
                   sec=0.1):
        """
        如果element没有传参或者为'screen', 从屏幕最右侧向左滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果element有传入元素，则在元素框范围内从最右侧向左滑动
        y_offset: 滑动的位置: location['y'] + size['height'] * y_offset
        """
        aklog_debug('swipe_left')
        try:
            if element is None:
                aklog_debug('element is not exist')
                return False
            if element == 'screen':
                screen = self.get_screen_size()
                start_x = int(screen[0] * (1 + length) / 2)
                start_y = int(screen[1] * y_offset)
                end_x = int(screen[0] * (1 - length) / 2)
                end_y = int(screen[1] * y_offset)
            else:
                location = element.location
                size = element.size
                start_x = int(location['x'] + size['width'] * (1 + length) / 2)
                start_y = int(location['y'] + size['height'] * y_offset)
                end_x = int(location['x'] + size['width'] * (1 - length) / 2)
                end_y = int(location['y'] + size['height'] * y_offset)
            aklog_debug('(%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_down(self, element: Union[WebElement, str, None] = 'screen', duration=1000, length=0.5, x_offset=0.25,
                   sec=0.1):
        """
        如果element没有传参或者为'screen', 从屏幕1/4处向下滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果element有传入元素，则在元素框范围内从1/4处向下滑动
        x_offset: 滑动的位置: location['x'] + size['width'] * x_offset
        """
        aklog_debug('swipe_down')
        try:
            if element is None:
                aklog_debug('element is not exist')
                return False
            if element == 'screen':
                screen = self.get_screen_size()
                start_x = int(screen[0] * x_offset)
                start_y = int(screen[1] * (1 - length) / 2)
                end_x = int(screen[0] * x_offset)
                end_y = int(screen[1] * (1 + length) / 2)
            else:
                location = element.location
                size = element.size
                start_x = location['x'] + int(size['width'] * x_offset)
                start_y = location['y'] + int(size['height'] * (1 - length) / 2)
                end_x = location['x'] + int(size['width'] * x_offset)
                end_y = location['y'] + int(size['height'] * (1 + length) / 2)
            aklog_debug('(%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_up(self, element: Union[WebElement, str, None] = 'screen', duration=1000, length=0.5, x_offset=0.25,
                 sec=0.1):
        """
        如果element没有传参或者为'screen', 则从屏幕3/4处向上滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果element有传入元素，则在元素框范围内从3/4处向上滑动
        x_offset: 滑动的位置: location['x'] + size['width'] * x_offset
        """
        aklog_debug('swipe_up')
        try:
            if element is None:
                aklog_debug('element is not exist')
                return False
            if element == 'screen':
                screen = self.get_screen_size()
                start_x = int(screen[0] * x_offset)
                start_y = int(screen[1] * (1 + length) / 2)
                end_x = int(screen[0] * x_offset)
                end_y = int(screen[1] * (1 - length) / 2)
            else:
                location = element.location
                size = element.size
                start_x = location['x'] + int(size['width'] * x_offset)
                start_y = location['y'] + int(size['height'] * (1 + length) / 2)
                end_x = location['x'] + int(size['width'] * x_offset)
                end_y = location['y'] + int(size['height'] * (1 - length) / 2)

            aklog_debug('(%s, %s) -> (%s, %s)' % (start_x, start_y, end_x, end_y))
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_until_find_by_xpath(self, eleXpath, ele='screen', counts=10, length=0.5, direction='up', x_offset=0.25):
        """
        上下滑动直到找到元素并可见
        :param eleXpath: 选项xpath
        :param ele: 默认screen表示整个屏幕上下滑动，可以指定元素框，可以先用get_element_visible方法获取元素
        :param counts: 设置上滑或下滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指上滑的距离占元素框的比例
        :param direction: 先上滑还是下滑，up or down
        :param x_offset: 滑动的相对位置: 0-1
        :return:
        """
        for i in range(0, counts + 1):
            try:
                WebDriverWait(self.driver, 0.5).until(EC.visibility_of_element_located((By.XPATH, eleXpath)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'up':
                    self.swipe_up(element=ele, length=length, x_offset=x_offset)
                else:
                    self.swipe_down(element=ele, length=length, x_offset=x_offset)
        for i in range(0, counts + 1):
            try:
                WebDriverWait(self.driver, 0.5).until(EC.visibility_of_element_located((By.XPATH, eleXpath)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'up':
                    self.swipe_down(element=ele, length=length, x_offset=x_offset)
                else:
                    self.swipe_up(element=ele, length=length, x_offset=x_offset)
        aklog_debug('%s is not found' % eleXpath)
        self.screen_shot()
        return False

    def swipe_until_find_by_name(self, name, ele='screen', counts=10, length=0.5, direction='up', x_offset=0.25):
        """
        上下滑动直到找到元素并可见
        :param name: 选项名称
        :param ele: 默认screen表示整个屏幕上下滑动，可以指定元素框，可以先用get_element_visible方法获取元素
        :param counts: 设置上滑或下滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指上滑的距离占元素框的比例
        :param direction: 先上滑还是下滑，up or down
        :param x_offset: 滑动的相对位置: 0-1
        :return:
        """
        eleXpath = "//*[@text='" + name + "']"
        aklog_debug('swipe_until_find_by_name, name: %s' % name)
        for i in range(0, counts + 1):
            try:

                WebDriverWait(self.driver, 0.5).until(EC.visibility_of_element_located((By.XPATH, eleXpath)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'up':
                    self.swipe_up(element=ele, length=length, x_offset=x_offset)
                else:
                    self.swipe_down(element=ele, length=length, x_offset=x_offset)
                continue
        for i in range(0, counts + 1):
            try:
                WebDriverWait(self.driver, 0.5).until(EC.visibility_of_element_located((By.XPATH, eleXpath)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'up':
                    self.swipe_down(element=ele, length=length, x_offset=x_offset)
                else:
                    self.swipe_up(element=ele, length=length, x_offset=x_offset)
                continue
        aklog_debug('%s is not found' % name)
        self.screen_shot()
        return False

    def swipe_until_find_by_names(self, *names, ele='screen', counts=10, length=0.5, direction='up', x_offset=0.25):
        """
        上下滑动直到找到元素并可见
        :param names: 选项名称，可以传入多个name，只要有一个匹配成功即可
        :param ele: 默认screen表示整个屏幕上下滑动，可以指定元素框，可以先用get_element_visible方法获取元素
        :param counts: 设置上滑或下滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指上滑的距离占元素框的比例
        :param direction: 先上滑还是下滑，up or down
        :param x_offset: 滑动的相对位置: 0-1
        :return:
        """
        # 传入多个名称，组合成一个Xpath，只要一个名称匹配成功即可
        names_len = len(names)
        eleXpath = '//*['
        for i in range(names_len):
            eleXpath += '@text="%s"' % names[i]
            if i == names_len - 1:
                eleXpath += ']'
            else:
                eleXpath += ' or '
        aklog_debug("swipe_until_find_by_names, xpath: %s" % eleXpath)

        for i in range(0, counts + 1):
            try:

                WebDriverWait(self.driver, 0.5).until(EC.visibility_of_element_located((By.XPATH, eleXpath)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'up':
                    self.swipe_up(element=ele, length=length, x_offset=x_offset)
                else:
                    self.swipe_down(element=ele, length=length, x_offset=x_offset)
                continue
        for i in range(0, counts + 1):
            try:
                WebDriverWait(self.driver, 0.5).until(EC.visibility_of_element_located((By.XPATH, eleXpath)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'up':
                    self.swipe_down(element=ele, length=length, x_offset=x_offset)
                else:
                    self.swipe_up(element=ele, length=length, x_offset=x_offset)
                continue
        aklog_debug('%s is not found' % eleXpath)
        self.screen_shot()
        return False

    def swipe_vertical_until_find_by_id(self, ele_id, view_ele='screen', counts=10, length=0.5, direction='up',
                                        x_offset=0.25):
        """
        垂直方向，上下滑动直到找到元素并可见
        :param ele_id: 选项id
        :param view_ele: 默认screen表示整个屏幕上下滑动，可以指定元素框，可以先用get_element_visible方法获取元素
        :param counts: 设置上滑或下滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指上滑的距离占元素框的比例
        :param direction: 先上滑还是下滑，up or down
        :param x_offset: 滑动的相对位置: 0-1
        """
        aklog_debug('swipe_vertical_until_find_by_id, %s' % ele_id)
        for i in range(0, counts + 1):
            try:
                WebDriverWait(self.driver, 1).until(EC.visibility_of_any_elements_located((By.ID, ele_id)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'up':
                    self.swipe_up(element=view_ele, duration=500, length=length, x_offset=x_offset)
                else:
                    self.swipe_down(element=view_ele, duration=500, length=length, x_offset=x_offset)
                continue
        for i in range(0, counts + 1):
            try:
                WebDriverWait(self.driver, 1).until(EC.visibility_of_any_elements_located((By.ID, ele_id)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'up':
                    self.swipe_down(element=view_ele, duration=500, length=length, x_offset=x_offset)
                else:
                    self.swipe_up(element=view_ele, duration=500, length=length, x_offset=x_offset)
                continue
        aklog_debug('%s is not found' % ele_id)
        self.screen_shot()
        return False

    def swipe_left_right_until_find_by_name(self, name, view_ele='screen', counts=10, length=0.5, direction='left',
                                            y_offset=0.25):
        """
        左右滑动直到找到元素并可见
        ele: 滑动区域元素，默认全屏
        :param name: 选项名称
        :param view_ele: 默认screen表示整个屏幕左右滑动，可以指定元素框，可以先用get_element_visible方法获取元素
        :param counts: 设置左滑或右滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指左滑的距离占元素框的比例
        :param direction: 先左滑还是右滑，left or right
        :param y_offset: 滑动的相对位置: 0-1
        """
        for i in range(0, counts + 1):
            try:
                eleXpath = "//*[@text='" + name + "']"
                WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, eleXpath)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'left':
                    self.swipe_left(element=view_ele, length=length, y_offset=y_offset)
                else:
                    self.swipe_right(element=view_ele, length=length, y_offset=y_offset)
        for i in range(0, counts + 1):
            try:
                eleXpath = "//*[@text='" + name + "']"
                WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, eleXpath)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'left':
                    self.swipe_right(element=view_ele, length=length, y_offset=y_offset)
                else:
                    self.swipe_left(element=view_ele, length=length, y_offset=y_offset)
        aklog_debug('%s is not found' % name)
        self.screen_shot()
        return False

    def swipe_horizontal_until_find_by_id(self, ele_id, view_ele='screen', counts=10, length=0.5, direction='left',
                                          y_offset=0.25):
        """
        左右滑动直到找到元素并可见
        :param ele_id: 选项id
        :param view_ele: 默认screen表示整个屏幕左右滑动，可以指定元素框，可以先用get_element_visible方法获取元素
        :param counts: 设置左滑或右滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最左边滚动到最右边
        :param length: 手指左滑的距离占元素框的比例
        :param direction: 先左滑还是右滑，left or right
        :param y_offset: 滑动的相对位置: 0-1
        """
        aklog_debug('swipe_horizontal_until_find_by_id, %s' % ele_id)
        for i in range(0, counts + 1):
            try:
                WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.ID, ele_id)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'left':
                    self.swipe_left(element=view_ele, duration=500, length=length, y_offset=y_offset)
                else:
                    self.swipe_right(element=view_ele, duration=500, length=length, y_offset=y_offset)
                continue
        for i in range(0, counts + 1):
            try:
                WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.ID, ele_id)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'left':
                    self.swipe_right(element=view_ele, duration=500, length=length, y_offset=y_offset)
                else:
                    self.swipe_left(element=view_ele, duration=500, length=length, y_offset=y_offset)
                continue
        aklog_debug('%s is not found' % ele_id)
        self.screen_shot()
        return False

    def swipe_horizontal_until_find_by_xpath(self, ele_xpath, view_ele='screen', counts=10, length=0.5,
                                             direction='left', y_offset=0.25):
        """
        左右滑动直到找到元素并可见
        :param ele_xpath: 选项xpath
        :param view_ele: 默认screen表示整个屏幕左右滑动，可以指定元素框，可以先用get_element_visible方法获取元素
        :param counts: 设置左滑或右滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最左边滚动到最右边
        :param length: 手指左滑的距离占元素框的比例
        :param direction: 先左滑还是右滑，left or right
        :param y_offset: 滑动的相对位置: 0-1
        """
        aklog_debug('swipe_horizontal_until_find_by_xpath, %s' % ele_xpath)
        for i in range(0, counts + 1):
            try:
                WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, ele_xpath)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'left':
                    self.swipe_left(element=view_ele, duration=500, length=length, y_offset=y_offset)
                else:
                    self.swipe_right(element=view_ele, duration=500, length=length, y_offset=y_offset)
                continue
        for i in range(0, counts + 1):
            try:
                WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, ele_xpath)))
                return True
            except:
                if i == counts:
                    break
                if direction == 'left':
                    self.swipe_right(element=view_ele, duration=500, length=length, y_offset=y_offset)
                else:
                    self.swipe_left(element=view_ele, duration=500, length=length, y_offset=y_offset)
                continue
        aklog_debug('%s is not found' % ele_xpath)
        self.screen_shot()
        return False

    def swipe_counts_in_specifc_area(self, ele='screen', counts=10, length=0.5):
        """滑动指定的次数在特定的区域"""
        for i in range(0, counts):
            self.swipe_up(element=ele, length=length)

    # endregion

    # region 获取元素或屏幕尺寸、位置

    def get_ele_size_by_xpath(self, eleXpath):
        """获取元素的大小（宽和高）"""
        aklog_debug('get_ele_size_by_xpath, eleXpath: %s' % eleXpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.XPATH, eleXpath)))
            ele_size = ele.size
            ele_width = ele_size['width']
            ele_height = ele_size['height']
            return ele_width, ele_height
        except:
            return 0, 0

    def get_ele_size_by_id(self, ele_id):
        """获取元素的大小（宽和高）"""
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, ele_id)))
            ele_size = ele.size
            ele_width = ele_size['width']
            ele_height = ele_size['height']
            aklog_debug('get_ele_size_by_id, ele_id: %s, width: %s, height: %s' % (
                ele_id, ele_width, ele_height))
            return ele_width, ele_height
        except:
            aklog_debug('get_ele_size_by_id failed')
            return 0, 0

    def get_screen_size(self):
        """获取屏幕大小"""
        if self.screen_width == 0:
            try:
                screen_size = self.driver.get_window_size()
                screen_width = screen_size['width']  # 获取当前屏幕的宽
                screen_height = screen_size['height']  # 获取当前屏幕的高
            except:
                screen_width = 0
                screen_height = 0

            self.screen_width = screen_width
            self.screen_height = screen_height
        aklog_debug('screen_size: %s, %s' % (self.screen_width, self.screen_height))
        return self.screen_width, self.screen_height

    def check_screen_size(self):
        return self.get_screen_size()

    def get_ele_location_by_xpath(self, eleXpath):
        """获取元素的位置(左上角的坐标)"""
        aklog_debug('get_ele_location_by_xpath, eleXpath: %s' % eleXpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.XPATH, eleXpath)))
            return ele.location
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_location_by_id(self, ele_id):
        """获取元素的位置(左上角的坐标)"""
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, ele_id)))
            loc = ele.location
            aklog_debug('get_ele_location_by_id, ele_id: %s, location: %s' % (ele_id, loc))
            return loc
        except:
            aklog_debug(str(traceback.format_exc()))
            if 'socket hang up' in str(traceback.format_exc()):
                aklog_debug('~~~~~ lex ~~~~~~')
                self.appium.temp_check_appium_localport()
            return None

    def get_ele_mid_location_by_xpath(self, eleXpath):
        """
        获取元素的位置(中心点的坐标)
        :param eleXpath: 元素xpath
        :return: dict类型
        """
        aklog_debug('get_ele_mid_location_by_xpath: %s' % eleXpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.XPATH, eleXpath)))
            ele_location = ele.location  # 元素左上角的坐标
            # aklog_debug(ele_location)
            ele_size = ele.size
            ele_location['x'] += ele_size['width'] / 2
            ele_location['y'] += ele_size['height'] / 2
            # aklog_debug(ele_location)
            return ele_location
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_mid_location_by_name(self, ele_name):
        """
        获取元素的位置(中心点的坐标)
        :param ele_name: 元素ele_name
        :return: dict类型
        """
        aklog_debug('get_ele_mid_location_by_name: %s' % ele_name)
        try:
            ele_xpath = "//*[@text='" + ele_name + "']"
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            ele_location = ele.location
            ele_size = ele.size
            ele_location['x'] += ele_size['width'] / 2
            ele_location['y'] += ele_size['height'] / 2
            return ele_location
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_rect_by_id(self, ele_id):
        """获取元素尺寸和位置信息: x, y, width, height"""
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, ele_id)))
            rect = ele.rect
            aklog_debug('get_ele_rect_by_id, ele_id: %s, rect: %s' % (ele_id, rect))
            return rect
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_rect_by_xpath(self, ele_xpath):
        """获取元素尺寸和位置信息: x, y, width, height"""
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            rect = ele.rect
            aklog_debug('get_ele_rect_by_xpath, ele_xpath: %s, rect: %s' % (ele_xpath, rect))
            return rect
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_element_visible(self, Type, ele, wait_time=None):
        """Type 可以取值：By.XPATH、By.ID、By.CLASS_NAME等"""
        aklog_debug('get_element_visible, Type: %s, ele: %s' % (Type, ele))
        if wait_time:
            wtime = wait_time
        else:
            wtime = self.wait_time
        try:
            element = WebDriverWait(self.driver, wtime).until(EC.visibility_of_element_located((Type, ele)))
            return element
        except StaleElementReferenceException:
            time.sleep(1)
            try:
                element = WebDriverWait(self.driver, wtime).until(EC.visibility_of_element_located((Type, ele)))
                return element
            except:
                aklog_debug('%s is not found' % ele)
                return None
        except:
            aklog_debug('%s is not found' % ele)
            return None

    def get_elements_visible(self, Type, ele):
        """Type 可以取值：By.XPATH、By.ID、By.CLASS_NAME等"""
        aklog_debug('get_element_visible, Type: %s, ele: %s' % (Type, ele))
        time.sleep(1)
        for i in range(2):
            try:
                # 为了避免界面还未完全加载完，但已经获取到元素了，导致之后加载完全后，出现StaleElementReferenceException错误，先延时1秒
                element = WebDriverWait(self.driver, self.wait_time).until(
                    EC.visibility_of_any_elements_located((Type, ele)))
                return element
            except StaleElementReferenceException:
                if i == 1:
                    aklog_error('get_elements_visible failed 2 times')
                    return None
                else:
                    aklog_error('get_elements_visible failed first time, retrying....')
                    time.sleep(3)
            except:
                aklog_debug('%s is not found' % ele)
                return None

    # endregion

    # region 截图相关，图片对比

    def screen_shot_as_base64(self):
        """保存屏幕截图成base64编码，用于嵌入到HTML测试报告"""
        aklog_debug('screen_shot_as_base64, the screenshots is shown below: ')
        return self.image.screenshots_as_base64()

    def screen_shot(self):
        """截图,用于外部调用"""
        img_base64 = self.screen_shot_as_base64()
        if img_base64:
            # self._imgs.append(img_base64)
            param_append_screenshots_imgs(img_base64)
        else:
            # self._imgs.append('')
            param_append_screenshots_imgs('')

    def save_screen_shot_to_file(self, image_path=None):
        """保存整个屏幕截图"""
        if not image_path:
            image_path = root_path + '\\image.png'
        aklog_debug('save_screen_shot_to_file: %s' % image_path)
        image_dir, file_name = os.path.split(image_path)
        image_name, form = os.path.splitext(file_name)
        form = form.replace('.', '')
        File_process.remove_file(image_path)
        self.image.get_screenshot_as_file().write_to_file(image_dir, image_name, form)
        return image_path

    def save_element_image(self, element, image_dir=None, image_name='image', form='png'):
        """保存图片"""
        if not image_dir:
            image_dir = root_path
        self.image.get_screenshot_by_element(element).write_to_file(image_dir, image_name, form)

    def save_element_image_by_id(self, ele_id, image_path=None):
        if not image_path:
            image_path = root_path + '\\image.png'
        aklog_debug('save_screen_shot_to_file: %s' % image_path)
        image_dir, file_name = os.path.split(image_path)
        image_name, form = os.path.splitext(file_name)
        form = form.replace('.', '')
        File_process.remove_file(image_path)
        element = self.get_element_visible(By.ID, ele_id)
        self.image.get_screenshot_by_element(element).write_to_file(image_dir, image_name, form)
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
        aklog_debug('save_screen_shot_to_file: %s' % image_path)
        image_dir, file_name = os.path.split(image_path)
        image_name, form = os.path.splitext(file_name)
        form = form.replace('.', '')
        File_process.remove_file(image_path)
        self.image.get_screenshot_by_custom_size(*area).write_to_file(image_dir, image_name, form)

    def get_black_ratio(self, CLASS_NAME, ratio):
        """判断当前类下的图片黑色占比"""
        element = self.get_element_visible(By.CLASS_NAME, CLASS_NAME)
        value = self.image.check_screen_color(element)
        if value > ratio:
            return True
        else:
            return False

    def check_image_rgb_by_xpath(self, ele_xpath, ratio, fix_rgb):
        """检查元素图像某种颜色占比"""
        aklog_debug('check_image_rgb_by_xpath')
        element = self.get_element_visible(By.XPATH, ele_xpath)
        if not element:
            aklog_debug('%s is not found' % ele_xpath)
            return None
        if len(fix_rgb) == 4:
            value = self.image.check_screen_color_rgba(element, fix_rgb)
        else:
            value = self.image.check_screen_color(element, fix_rgb)
        aklog_debug('%r color proportion: %s' % (fix_rgb, value))
        if value is None:
            return None
        if value > ratio:
            return True
        else:
            return False

    def check_image_rgb_by_id(self, ele_id, ratio, fix_rgb):
        """检查元素图像某种颜色占比"""
        aklog_debug('check_image_rgb_by_id')
        element = self.get_element_visible(By.ID, ele_id)
        if not element:
            aklog_debug('%s is not found' % ele_id)
            return None
        if len(fix_rgb) == 4:
            value = self.image.check_screen_color_rgba(element, fix_rgb)
        else:
            value = self.image.check_screen_color(element, fix_rgb)
        aklog_debug('%r color proportion: %s' % (fix_rgb, value))
        if value is None:
            return None
        if value > ratio:
            return True
        else:
            return False

    def check_image_rgb_custom_area(self, area, ratio, fix_rgb):
        """
        检查某个区域图像某种颜色占比
        :param area: (start_x, start_y, end_x, end_y)
        :param ratio:
        :param fix_rgb:
        :return:
        """
        aklog_debug('check_image_rgb_custom_area')
        value = self.image.check_custom_area_color(area, fix_rgb)
        aklog_debug('%r color proportion: %s' % (fix_rgb, value))
        if value is None:
            return None
        if value > ratio:
            return True
        else:
            return False

    def is_pure_color_by_id(self, ele_id, percent):
        """判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色"""
        aklog_debug('is_pure_color_by_id, ele_id: %s, percent: %s' % (ele_id, percent))
        element = self.get_element_visible(By.ID, ele_id)
        if not element:
            aklog_debug('%s is not found' % ele_id)
            return None
        else:
            return self.image.is_pure_color(element, percent)

    def is_pure_color_by_xpath(self, ele_xpath, percent):
        """判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色"""
        aklog_debug('is_pure_color_by_xpath, ele_xpath: %s, percent: %s' % (ele_xpath, percent))
        element = self.get_element_visible(By.XPATH, ele_xpath)
        if not element:
            aklog_debug('%s is not found' % ele_xpath)
            return None
        else:
            return self.image.is_pure_color(element, percent)

    def is_correct_ele_image_by_xpath(self, ele_xpath, image_path, percent):
        """判断元素图片跟预期的图片是否一致"""
        aklog_debug('ele_xpath: %s, image_path: %s'
                    % (ele_xpath, image_path))
        try:
            load_image = self.image.load_image(image_path)
            element = self.get_element_visible(By.XPATH, ele_xpath)
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
            # load_image = self.image.load_image(image_path)
            element = self.get_element_visible(By.XPATH, ele_xpath)
            result = self.image.compare_image_after_convert_resolution(element, image_path, percent)
            return result
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def get_string_by_ocr_custom_area_image(self, area):
        """
        在指定区域内识别文字并输出（推荐使用get_text_by_ocr_custom_area_image方法）
        area: (start_x, start_y, end_x, end_y)
        """
        return self.image.get_screenshot_by_custom_size(*area).image_ocr_to_string()

    def get_text_by_ocr_custom_area_image(self, area):
        """
        在指定区域内识别文字并输出（推荐使用这种方法，更准确）
        area: (start_x, start_y, end_x, end_y)
        """
        return self.image.get_screenshot_by_custom_size(*area).image_easyocr_read_text()

    def ocr_text_by_id(self, ele_id):
        """
        有些元素的text属性为空，可以通过识别截图方式获取文字
        """
        aklog_debug()
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, ele_id)))
            return self.image.get_screenshot_by_element(ele).image_easyocr_read_text()
        except:
            aklog_debug(traceback.format_exc())
            return None

    # endregion

    # region SeekBar拖动条操作

    def slide_horizontal_seek_bar_by_id(self, ele_id, minimum, maximum, index, duration=3000):
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
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.visibility_of_element_located((By.ID, ele_id)))
            ele_location = ele.location
            ele_size = ele.size
            ele_width = ele_size['width']
            ele_height = ele_size['height']
            average_length = ele_width / (maximum - minimum)
            # print(average_length)
            start_x = ele_location['x'] + 1
            start_y = ele_location['y'] + ele_height * 0.5
            end_x = ele_location['x'] + int(average_length * (index - minimum + 0.4))
            # print(ele_width)
            # print(ele_location['x'])
            # print(end_x)
            end_y = ele_location['y'] + ele_height * 0.5
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_vertical_seek_bar_by_id(self, ele_id, minimum, maximum, index, duration=2000):
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
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.visibility_of_element_located((By.ID, ele_id)))
            ele_location = ele.location
            ele_size = ele.size
            ele_width = ele_size['width']
            ele_height = ele_size['height']
            average_length = ele_height / (maximum - minimum)
            start_x = ele_location['x'] + ele_width * 0.5
            start_y = ele_location['y'] + ele_height - 1
            end_x = ele_location['x'] + ele_width * 0.5
            end_y = ele_location['y'] + ele_height - average_length * (index - minimum + 0.8)
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 系统弹窗Toast控件

    def is_exist_toast(self, text):
        """判断系统弹窗是否存在"""
        aklog_debug('is_exist_toast: %s' % text)
        try:
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ".//*[contains(@text, %s)]" % text)))
            return True
        except:
            aklog_debug('%s toast is not exist' % text)
            self.check_driver_connected()
            return False

    def get_toast_message(self, wait_time=None, print_trace=False):
        """同步U2接口"""
        return self.get_toast_text(wait_time, print_trace)

    def get_toast_text(self, wait_time=None, print_trace=False):
        """获取系统弹窗的文本信息"""
        if not wait_time:
            wait_time = self.wait_time
        try:
            # 增加915 文本信息
            value = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@class="android.widget.Toast" or @resource-id="com.akuvox.phone:id/tv_tip_toast" or @resource-id="com.akuvox.phone:id/tv_tip_toast_user"]'))).get_attribute(
                'text')
            aklog_debug("get_toast_text: %s" % value)
            return value
        except:
            aklog_debug('toast not found')
            if print_trace:
                aklog_debug(str(traceback.format_exc()))
            return None

    # endregion

    # region webView类型元素操作，以下操作还有点问题
    def get_web_view_contexts(self):
        """获取可用的上下文信息"""
        return self.driver.contexts

    def switch_to_web_view(self, web_view):
        """切换到web view"""
        self.driver.switch_to.context(web_view)

    def switch_to_native_app(self):
        """切换回NATIVE APP"""
        self.driver.switch_to.context('NATIVE_APP')

    def get_web_view_context(self):
        return self.driver.context

    # endregion


if __name__ == '__main__':
    device_info = {'device_name': 'X915V2',
                   'ip': '192.168.88.100',  # MARK: 注意修改IP
                   'deviceid': '192.168.88.100:5654',
                   'platformversion': '9',
                   'appium_command': 'appium'}
    device_config = config_parse_device_config('config_X915V2_NORMAL')
    device = Android_Door(device_info, device_config)
    app = AndroidBase(device, 2)
    app.AppRun()
