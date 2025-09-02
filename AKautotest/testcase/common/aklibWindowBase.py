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
from libconfig.COMMON.libconfig_NORMAL import config_NORMAL

from appium.options.windows import WindowsOptions
from appium import webdriver as appium_webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebElement
import win32gui
import win32con
import pyautogui
import time
import traceback


class WindowBase(object):

    # region 初始化相关
    def __init__(self, exe_path=None, device_info=None, device_config=None, wait_time=5, debug=False):
        self.debug = debug
        self.exe_path = None
        self.exe_dir = None
        self.driver: Optional[appium_webdriver.Remote] = None
        self.appium_process = None
        self._imgs = []
        self.image: Optional[Image_process] = None
        self.window_process = None
        self.wait_time = 5
        self.device_config = config_NORMAL()
        self.device_info = None
        self.device_name = ''
        self.local_port = 4723
        self.system_port = 4724
        self.options = WindowsOptions()
        self.top_window_name = ''
        self.change_language_force_flag = True
        self.init(exe_path, device_info, device_config, wait_time)

    def init(self, exe_path=None, device_info=None, device_config=None, wait_time=5, debug=False):
        self.debug = debug
        if device_config:
            self.device_config = device_config
        if device_info:
            self.device_info = device_info
            self.device_name = device_info['device_name']
        self.wait_time = wait_time
        if exe_path:
            self.exe_dir = os.path.dirname(exe_path)
            self.exe_path = exe_path
            # 初始化不在device_info中指定本地端口，而是自动分配，localPort为奇数，bootstrap_port 加1为偶数
            self.local_port = int(config_get_appium_port())
            self.system_port = self.local_port + 1
            self.options.platform_name = 'Windows'
            self.options.automation_name = 'Windows'
            self.options.device_name = 'WindowsPC'
            self.options.set_capability('ms:waitForAppLaunch', 2)
            self.options.set_capability('createSessionTimeout', 30000)
            self.options.new_command_timeout = 600  # 600秒
            self.options.system_port = self.system_port
            aklog_debug('WindowBase.init, local_port: %s' % self.local_port)

    def get_exe_path(self):
        return self.exe_path

    def get_exe_dir(self):
        return self.exe_dir

    def get_device_config(self):
        return self.device_config

    def get_device_info(self):
        return self.device_info

    def reset_imgs(self):
        self._imgs = []
        param_reset_screenshots_imgs()

    def get_imgs(self):
        return self._imgs

    def set_wait_for_app_launch(self, wait_time):
        self.options.set_capability('ms:waitForAppLaunch', wait_time)  # 设置等待应用启动时间

    # endregion

    # region 连接关闭操作

    def start_appium_server(self, restart=False):
        """
        启动 Appium 服务
        """
        # 启动 Appium 服务的命令
        command = f'appium -a 127.0.0.1 -p {self.local_port} --base-path /wd/hub'
        for i in range(0, 10):
            # 检查appium进程端口是否启用
            appium_server_check = f'netstat -ano | findstr "LISTENING" | findstr "127.0.0.1:{self.local_port}"'
            stdout = sub_process_get_output(appium_server_check)
            if i == 0:
                if self.appium_process is not None and stdout and not restart:
                    aklog_debug(f'Appium [127.0.0.1:{self.local_port}] 已经在运行中')
                    return True
                else:
                    self.stop_appium_server()

                if self.debug:
                    command += ' --log-level debug'
                else:
                    command += ' --log-level error'
                aklog_debug(f'执行命令: {command}')
                self.appium_process = subprocess.Popen(command, shell=True)
                time.sleep(3)  # 等待 Appium 服务启动
                continue
            elif i < 9:
                if stdout:
                    aklog_debug(f'Appium [127.0.0.1:{self.local_port}] 启动成功')
                    time.sleep(5)
                    return True
                else:
                    aklog_debug(f'Appium [127.0.0.1:{self.local_port}] starting...')
                    time.sleep(3)
                    continue
        aklog_error(f'Appium [127.0.0.1:{self.local_port}] 启动失败')
        return False

    def stop_appium_server(self):
        """
        停止 Appium 服务端。
        """
        aklog_debug()
        if self.appium_process is not None:
            self.appium_process.terminate()
            self.appium_process.wait()
            self.appium_process = None
            time.sleep(1)
        for i in range(3):
            appium_server_check = f'netstat -ano | findstr "LISTENING" | findstr "127.0.0.1:{self.local_port}"'
            stdout = sub_process_get_output(appium_server_check)
            if not stdout:
                aklog_debug(f'Appium [127.0.0.1:{self.local_port}] 已停止运行')
                return True
            elif i < 2:
                stdout = stdout.strip()
                pid = stdout.split(' ')[-1]
                aklog_debug('node pid: %s' % pid)
                kill_pid_command = 'taskkill /F /PID %s' % pid
                sub_process_exec_command(kill_pid_command, 10)
                time.sleep(1)
                continue
        aklog_error(f'Appium [127.0.0.1:{self.local_port}] 停止运行失败')
        return False

    def start_win_app_driver(self):
        return self.start_appium_server()

    def stop_win_app_driver(self):
        return self.stop_appium_server()

    def get_win_app_driver_pid(self):
        """
        有些程序（比如WinAppDriver）多开后，进程名称都一样，监听端口也是用系统进程(id=4)，
        需要遍历获取所有进程id，然后通过id获取cmdline信息，来获取进程的监听端口对应关系
        """
        cmdline = 'WinAppDriver 127.0.0.1 %s/wd/hub' % self.local_port
        pids = cmd_get_pids_by_process_name('WinAppDriver.exe')
        for pid in pids:
            process_info = cmd_get_process_details(pid)
            if ' '.join(process_info['cmdline']) == cmdline:
                aklog_debug(f"Process listening on port {self.local_port}: WinAppDriver.exe (PID: {pid})")
                return pid
        aklog_debug('get_win_app_driver_pid failed')
        return None

    def app_run(self, change_language_force_flag=None):
        aklog_debug('app_run')
        try:
            if change_language_force_flag is None:
                change_language_force_flag = self.change_language_force_flag
            change_language('EN', change_language_force_flag)  # 修改输入法为EN，第一次强制修改
            self.change_language_force_flag = False
            self.options.app = self.exe_path
            self.driver = appium_webdriver.Remote(
                f'http://127.0.0.1:{self.local_port}/wd/hub', options=self.options)
            self.driver.implicitly_wait(5)
            self.image = Image_process(self.driver)
            self.window_process = Window_process()
            self.top_window_name = self.driver.title
            self.set_window_foreground()
            aklog_debug(f'app run [{self.top_window_name}] success')
            return True
        except Exception as e:
            aklog_error(e)
            aklog_debug(traceback.format_exc())
            return False

    def app_connect(self, window_name=None, change_top_window=True):
        """
        可以直接连接已经打开的APP
        """
        if window_name is None:
            window_name = self.top_window_name
        if not window_name:
            aklog_debug('窗口名称为空，无法连接')
            return False
        # 先检查当前是否已连接
        if (self.get_page_source()
                and (self.driver.title == window_name
                     or self.switch_to_window(window_name))):
            self.top_window_name = window_name
            self.set_window_foreground()
            aklog_debug(f'{window_name} 已连接')
            return True
        aklog_debug(f'app connect: {window_name}')
        try:
            # 使用 appTopLevelWindow 参数连接已运行的应用程序
            window_handle = win32gui.FindWindow(None, window_name)
            if not window_handle:
                aklog_warn("Failed to find window handle for the application")
                return False
            hex_handle = format(window_handle, 'x')
            if hasattr(self.options, 'app'):
                setattr(self.options, 'app', None)
            self.options.app_top_level_window = hex_handle
            self.driver = appium_webdriver.Remote(
                f'http://127.0.0.1:{self.local_port}/wd/hub', options=self.options)
            self.driver.implicitly_wait(5)
            self.image = Image_process(self.driver)
            self.window_process = Window_process()
            aklog_debug(f'window name: {self.driver.title}')
            if change_top_window:
                self.top_window_name = window_name
            self.set_window_foreground()
            aklog_debug(f'app connect [{window_name}] success')
            return True
        except:
            aklog_debug('app connect failed, %s' % traceback.format_exc())
            return False

    @staticmethod
    def get_foreground_window_name():
        """获取当前前置窗口的名称"""
        return win32gui.GetWindowText(win32gui.GetForegroundWindow())

    def app_close_quit(self):
        aklog_debug('app_close_quit')
        try:
            if self.driver is not None:
                self.driver.close()
                self.driver.quit()
                self.driver = None
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def get_page_source(self):
        """获取页面资源，可用于判断设备是否连接正常"""
        aklog_debug('get_page_source')
        try:
            if self.driver:
                page_source = self.driver.page_source
                # aklog_debug('page_source: %s' % page_source)
                return page_source
            else:
                aklog_debug('driver is None, get page source failed')
                return None
        except Exception as e:
            aklog_debug(f'get_page_source failed: {e}')
            if self.debug:
                aklog_debug(traceback.format_exc())
            return None

    # endregion

    # region 窗口操作
    def switch_to_window(self, window_name=None, timeout=10):
        """有些弹窗的根窗口名称改变，所以需要切换窗口"""
        aklog_debug()
        if window_name is None:
            window_name = self.get_foreground_window_name()
        try:
            end_time = time.time() + timeout
            window_handle = None
            while time.time() < end_time:
                window_handle = win32gui.FindWindow(None, window_name)
                if window_handle:
                    break
                time.sleep(1)

            if not window_handle:
                aklog_warn(f"未找到窗口: {window_name}，超时{timeout}s")  # 未找到窗口
                return False

            hex_handle = format(window_handle, 'x')
            # Appium窗口切换，增加超时保护
            try:
                # Appium部分可能阻塞，建议用多线程或信号量做超时保护（此处用简单方案）
                self.driver.switch_to.window(hex_handle)  # 切换窗口
            except Exception as e:
                aklog_error(f"Appium切换窗口异常: {window_name}, 错误: {e}")  # 捕获异常
                return False
        except Exception as e:
            aklog_debug(e)

        if self.driver.title == window_name:
            self.top_window_name = window_name
            aklog_debug(f'已切换至窗口: {window_name}')
            return True
        else:
            aklog_warn(f'切换窗口 {window_name} 失败')
            return False

    def switch_to_default_window(self):
        return self.app_connect(change_top_window=False)

    def set_window_foreground(self):
        """设置窗口前置，避免窗口被其他程序界面覆盖后操作异常"""
        aklog_debug(f'set_window_foreground: {self.top_window_name}')
        try:
            self.window_process.find_window_wildcard(self.top_window_name)
            self.window_process.set_foreground()
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def get_top_window_name(self):
        return self.top_window_name

    # endregion

    # region 元素定位

    def find_element(self, locator, wait_time=None, print_trace=False) -> Optional[WebElement]:
        """
        获取元素
        locator: 元组类型: (By.NAME, 'xxx'), (By.XPATH, 'xxx'), (AppiumBy.ACCESSIBILITY_ID, '1010')
        """
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located(locator))
            return ele
        except Exception as e:
            aklog_debug(e)
            if print_trace:
                aklog_debug(traceback.format_exc())
            return None

    # endregion

    # region 输入框填写

    def set_text(self, locator, content, wait_time=None, sec=0.2, print_trace=False):
        """输入框输入文本"""
        aklog_debug()
        try:
            ele = self.find_element(locator, wait_time, print_trace)
            if not ele:
                return False
            # 先清空输入框
            ele.send_keys(Keys.CONTROL, 'a')
            ele.send_keys(Keys.BACKSPACE)
            time.sleep(0.1)
            if ele.get_attribute('Value.Value'):
                ele.clear()
                time.sleep(0.1)
            # 再次输入值
            ele.send_keys(content)
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def input_edit_by_name(self, name, content, wait_time=None, sec=0.2):
        aklog_debug("input_edit_by_name : %s, content: %s" % (name, content))
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((By.NAME, name)))
            # 先清空输入框
            ele.send_keys(Keys.CONTROL, 'a')
            ele.send_keys(Keys.BACKSPACE)
            time.sleep(0.1)
            if ele.get_attribute('Value.Value'):
                ele.clear()
                time.sleep(0.1)
            # 再次输入值
            ele.send_keys(content)
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def input_edit_by_automation_id(self, ele_id, content, wait_time=None, sec=0.2):
        aklog_debug("input_edit_by_automation_id : %s, content: %s" % (ele_id, content))
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            # 先清空输入框
            ele.send_keys(Keys.CONTROL, 'a')
            ele.send_keys(Keys.BACKSPACE)
            time.sleep(0.1)
            if ele.get_attribute('Value.Value'):
                ele.clear()
                time.sleep(0.1)
            # 再次输入值
            ele.send_keys(content)
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def input_edit_by_xpath(self, ele_xpath, content, wait_time=None, sec=0.2):
        aklog_printf()
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((AppiumBy.XPATH, ele_xpath)))
            # 先清空输入框
            ele.clear()
            time.sleep(0.1)
            # 再次输入值
            ele.send_keys(content)
            time.sleep(sec)
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    @staticmethod
    def open_file(file_path):
        """打开文件"""
        aklog_debug()
        dialog = win32gui.FindWindow("#32770", "打开文件")
        comboxex32 = win32gui.FindWindowEx(dialog, 0, "ComboBoxEx32", None)
        combox = win32gui.FindWindowEx(comboxex32, 0, "ComboBox", None)
        edit = win32gui.FindWindowEx(combox, 0, "Edit", None)
        button = win32gui.FindWindowEx(dialog, 0, "Button", "打开(O)")
        win32gui.SendMessage(edit, win32con.WM_SETTEXT, None, file_path)
        time.sleep(1)
        win32gui.SendMessage(dialog, win32con.WM_COMMAND, 1, button)

    # endregion

    # region 点击操作

    def click(self, locator, wait_time=None, sec=0.2, print_trace=False):
        """元素点击"""
        aklog_debug()
        try:
            ele = self.find_element(locator, wait_time, print_trace)
            if ele is None:
                return False
            # 获取按钮的名称
            try:
                if locator[0] != AppiumBy.NAME:
                    value = ele.text
                    aklog_debug("click %s" % value)
            except:
                aklog_debug("click by %s" % locator[0])

            ele.click()
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def right_click(self, locator, wait_time=None, sec=0.2, print_trace=False):
        """右键点击"""
        aklog_debug()
        try:
            ele = self.find_element(locator, wait_time, print_trace)
            if ele is None:
                return False
            # 获取按钮的名称
            try:
                if locator[0] != AppiumBy.NAME:
                    value = ele.text
                    aklog_debug("right click %s" % value)
            except:
                aklog_debug("right click by %s" % locator[0])

            rect = ele.rect
            x_center = rect['x'] + rect['width'] / 2
            y_center = rect['y'] + rect['height'] / 2

            pyautogui.moveTo(x_center, y_center)  # 移动到元素中心
            pyautogui.click(button='right')  # 右键点击
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def double_click(self, locator, wait_time=None, sec=0.2, print_trace=False):
        """双击"""
        aklog_debug()
        try:
            ele = self.find_element(locator, wait_time, print_trace)
            if ele is None:
                return False
            # 获取按钮的名称
            try:
                if locator[0] != AppiumBy.NAME:
                    value = ele.text
                    aklog_debug("double click %s" % value)
            except:
                aklog_debug("double click by %s" % locator[0])

            # 获取元素绝对坐标（兼容Windows驱动特性）
            rect = ele.rect
            x_center = rect['x'] + rect['width'] / 2
            y_center = rect['y'] + rect['height'] / 2

            pyautogui.moveTo(x_center, y_center)  # 移动到元素中心
            pyautogui.doubleClick()  # 双击
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def multi_click(self, locator, counts=2, wait_time=None, sec=0.2, interval=0.1, print_trace=False):
        """多次点击"""
        aklog_printf()
        try:
            ele = self.find_element(locator, wait_time, print_trace)
            if not ele:
                return False
            # 获取按钮的名称
            try:
                value = ele.text
                aklog_printf("multi_click: %s, value: %s" % (locator[1], value))
            except:
                aklog_printf("multi_click: %s" % locator[1])

            for i in range(counts):
                ele.click()
                time.sleep(interval)
            time.sleep(sec)
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def click_btn_by_name(self, ele_name, wait_time=None, sec=0.2):
        aklog_debug()
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((By.NAME, ele_name)))
            ele.click()
            try:
                value = ele.text
                aklog_debug("click_btn_by_name: %s, value: %s" % (ele_name, value))
            except:
                aklog_debug("click_btn_by_name: %s" % ele_name)
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def click_btn_by_automation_id(self, ele_id, wait_time=None, sec=0.2):
        aklog_debug()
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            ele.click()
            try:
                value = ele.text
                aklog_debug("click_btn_by_automation_id: %s, value: %s" % (ele_id, value))
            except:
                aklog_debug("click_btn_by_automation_id: %s" % ele_id)
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def click_btn_by_xpath(self, ele_xpath, wait_time=None, sec=0.2):
        aklog_debug()
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            ele.click()
            try:
                value = ele.text
                aklog_debug("click_btn_by_xpath: %s, value: %s" % (ele_xpath, value))
            except:
                aklog_debug("click_btn_by_xpath: %s" % ele_xpath)
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def multi_click_btn_by_xpath(self, ele_xpath, counts=2, wait_time=None, sec=0.2, interval=0.1):
        """多次点击"""
        aklog_printf()
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            for i in range(counts):
                ele.click()
                time.sleep(interval)
            try:
                value = ele.text
                aklog_printf("multi_click_btn_by_xpath: %s, value: %s" % (ele_xpath, value))
            except:
                aklog_printf("multi_click_btn_by_xpath: %s" % ele_xpath)
            time.sleep(sec)
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    # endregion

    # region 复选框操作

    def set_checkbox(self, locator, enable, wait_time=None, sec=0.2, print_trace=False):
        """复选框勾选"""
        aklog_debug()
        try:
            ele = self.find_element(locator, wait_time, print_trace)
            if not ele:
                return False
            value = ele.get_attribute('Toggle.ToggleState')  # 获取到的值为1 or 0
            if ((not value and enable) or
                    (value and not enable)):
                ele.click()
                time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def check_by_automation_id(self, ele_id, wait_time=None, sec=0.2):
        """复选框勾选"""
        aklog_debug()
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            value = ele.get_attribute('Toggle.ToggleState')
            if not value:
                ele.click()
                time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def uncheck_by_automation_id(self, ele_id, wait_time=None, sec=0.2):
        """复选框取消勾选"""
        aklog_debug()
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            value = ele.get_attribute('Toggle.ToggleState')
            if value:
                ele.click()
                time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def set_checkbox_by_automation_id(self, ele_id, enable, wait_time=None, sec=0.2):
        """
        设置复选框
        enable: 1 or 0, True or False
        """
        aklog_debug()
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            value = ele.get_attribute('Toggle.ToggleState')  # 获取到的值为1 or 0
            if (not value and enable) or (value and not enable):
                ele.click()
                time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    # endregion

    # region 获取元素信息

    def get_attribute(self, locator, attribute, wait_time=None, print_trace=False):
        """获取属性"""
        aklog_debug()
        try:
            ele = self.find_element(locator, wait_time, print_trace)
            if not ele:
                return False
            value = ele.get_attribute(attribute)
            aklog_debug("%s: %s" % (attribute, value))
            return value
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_text(self, locator, wait_time=None, print_trace=False):
        """获取文本"""
        aklog_debug()
        try:
            ele = self.find_element(locator, wait_time, print_trace)
            if not ele:
                return False
            value = ele.text
            aklog_debug("text : %s" % value)
            return value
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_enabled(self, locator):
        """判断控件是否可以操作"""
        aklog_debug()
        try:
            ele = self.find_element(locator)
            if not ele:
                return False
            enabled = ele.get_attribute('IsEnabled')
            aklog_debug('enabled: %s' % enabled)
            if enabled == 'true':
                return True
            else:
                return False
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_attribute_by_automation_id(self, ele_id, attribute, wait_time=None):
        """获取属性"""
        aklog_debug("get_attribute_by_automation_id : ele_id: %s, attribute: %s"
                    % (ele_id, attribute))
        if wait_time is None:
            wait_time = self.wait_time
        try:
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            value = ele.get_attribute(attribute)
            aklog_debug("%s: %s" % (attribute, value))
            return value
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_text_by_automation_id(self, ele_id, wait_time=None):
        """该方法可以获取Value.Value和Name"""
        aklog_debug("get_text_by_automation_id : %s" % ele_id)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            value = ele.text
            aklog_debug("text : %s" % value)
            return value
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_text_by_xpath(self, ele_xpath, wait_time=None):
        """该方法可以获取Value.Value和Name"""
        aklog_debug("get_text_by_xpath : %s" % ele_xpath)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            ele = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            value = ele.text
            aklog_debug("text : %s" % value)
            return value
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_element(self, Type, ele, wait_time=None):
        """Type 可以取值：By.XPATH、By.ID、By.CLASS_NAME等"""
        aklog_debug('get_element, Type: %s, ele: %s' % (Type, ele))
        if wait_time is None:
            wait_time = self.wait_time
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((Type, ele)))
            return element
        except:
            aklog_debug('%s is not found' % ele)
            return None

    def is_enabled_by_automation_id(self, ele_id):
        """判断控件是否可以操作"""
        aklog_debug('is_enabled_by_automation_id: %s' % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            enabled = ele.get_attribute('IsEnabled')
            aklog_debug('enabled: %s' % enabled)
            if enabled == 'true':
                return True
            else:
                return False
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_process_id(self):
        aklog_debug()
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, '/Window')))
            process_id = ele.get_attribute('ProcessId')
            aklog_debug("process_id : %s" % process_id)
            return process_id
        except:
            aklog_debug(traceback.format_exc())
            return None

    # endregion

    # region 组合框选择

    def combobox_select(self, locator, option_name, wait_time=None, print_trace=False):
        """组合框选择"""
        aklog_debug()
        try:
            combo_box = self.find_element(locator, wait_time, print_trace)
            if not combo_box:
                return False

            # 选择 ComboBox 中的某一项
            combo_box.click()
            time.sleep(0.5)
            combo_box.find_element(AppiumBy.NAME, option_name).click()
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def combobox_select_by_automation_id(self, ele_id, option_name, wait_time=None):
        """组合框选择"""
        aklog_debug()
        if wait_time is None:
            wait_time = self.wait_time
        try:
            # 通过名称定位 ComboBox 控件
            combo_box = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))

            # 选择 ComboBox 中的某一项
            combo_box.click()
            time.sleep(0.5)
            combo_box.find_element(AppiumBy.NAME, option_name).click()
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def combobox_select_by_contain_option(self, ele_id, option_name, wait_time=None):
        """组合框选择，选项名称只传入部分"""
        aklog_debug()
        if wait_time is None:
            wait_time = self.wait_time
        try:
            # 通过名称定位 ComboBox 控件
            combo_box = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))

            # 选择 ComboBox 中的某一项
            combo_box.find_element(
                AppiumBy.XPATH, '//ComboBox[@AutomationId="%s"]/Button' % ele_id).click()
            time.sleep(0.5)
            combo_box.find_element(
                AppiumBy.XPATH,
                f'//ComboBox[@AutomationId="{ele_id}"]//ListItem[contains(@Name, "{option_name}")]').click()
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    # endregion

    # region 判断元素是否存在

    def is_visible(self, locator, wait_time=None):
        """判断元素是否存在并可见"""
        aklog_debug()
        ele = self.find_element(locator, wait_time)
        if ele is not None:
            return True
        return False

    def is_exists(self, locator):
        return self.is_visible(locator)

    def wait_visible(self, locator, timeout=5, print_trace=False):
        aklog_debug()
        return self.find_element(locator, timeout, print_trace=print_trace)

    def wait_disappear(self, locator, timeout=5):
        aklog_debug()
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(locator))
            return True
        except:
            aklog_debug('%s is not disappear' % locator[1])
            return False

    def is_visible_ele_by_automation_id(self, ele_id, wait_time=None):
        """判断元素是否存在并可见"""
        aklog_debug('is_visible_ele_by_automation_id, ele_id: %s' % ele_id)
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            return True
        except:
            aklog_debug('%s is not visible' % ele_id)
            return False

    def is_visible_ele_by_name(self, ele_name, wait_time=None):
        """判断元素是否存在并可见"""
        aklog_debug('is_visible_ele_by_name, ele_name: %s' % ele_name)
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((By.NAME, ele_name)))
            return True
        except:
            aklog_debug('%s is not visible' % ele_name)
            return False

    def is_exist_ele_by_automation_id(self, ele_id, wait_time=None):
        """判断元素是否存在"""
        aklog_debug('is_exist_ele_by_automation_id, ele_id: %s' % ele_id)
        try:
            if not wait_time:
                wait_time = self.wait_time
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            return True
        except:
            aklog_debug('%s is not visible' % ele_id)
            return False

    def wait_visible_by_name(self, ele_name, timeout=5):
        aklog_debug()
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.NAME, ele_name)))
            return True
        except:
            aklog_debug('%s is not visible' % ele_name)
            return False
    
    def wait_visible_by_xpath(self, ele_xpath, timeout=5):
        aklog_debug()
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            return True
        except:
            aklog_debug('%s is not visible' % ele_xpath)
            return False

    def wait_visible_by_automation_id(self, ele_id, timeout=5):
        aklog_debug()
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            return True
        except:
            aklog_debug('%s is not visible' % ele_id)
            return False

    def wait_disappear_by_automation_id(self, ele_id, timeout=5):
        aklog_debug()
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, ele_id)))
            return True
        except:
            aklog_debug('%s is not disappear' % ele_id)
            return False

    # endregion

    # region 截图相关，图片对比
    def screen_shot_as_base64(self):
        """保存屏幕截图成base64编码，用于嵌入到HTML测试报告"""
        if not self.image:
            aklog_debug('driver未初始化完成')
            return None
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

    def is_pure_color(self, locator, percent):
        """判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色"""
        aklog_debug()
        element = self.find_element(locator)
        if not element:
            return None

        return self.image.is_pure_color(element, percent)

    def check_image_rgb(self, locator, ratio, fix_rgb):
        """检查元素图像某种颜色占比"""
        aklog_debug()
        element = self.find_element(locator)
        if not element:
            return None

        if len(fix_rgb) == 4:
            value = self.image.check_screen_color_rgba(element, fix_rgb)
        else:
            value = self.image.check_screen_color(element, fix_rgb)
        aklog_debug('%r color proportion: %.30f' % (fix_rgb, value))
        if value is None:
            return None
        if value > ratio:
            return True
        else:
            return False

    def is_pure_color_by_automation_id(self, ele_id, percent):
        """判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色"""
        aklog_debug('is_pure_color_by_automation_id, ele_id: %s, percent: %s'
                    % (ele_id, percent))
        element = self.get_element(AppiumBy.ACCESSIBILITY_ID, ele_id)
        if not element:
            aklog_debug('%s is not found' % ele_id)
            return None
        else:
            return self.image.is_pure_color(element, percent)

    def is_pure_color_by_name(self, ele_name, percent=0.8):
        """判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色"""
        aklog_debug('is_pure_color_by_name, ele_name: %s, percent: %s' % (ele_name, percent))
        element = self.get_element(By.NAME, ele_name)
        if not element:
            aklog_debug('%s is not found' % ele_name)
            return None
        else:
            return self.image.is_pure_color(element, percent)

    def is_pure_color_by_xpath(self, ele_xpath, percent=0.8):
        """判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色"""
        aklog_debug('is_pure_color_by_xpath, ele_xpath: %s, percent: %s' % (ele_xpath, percent))
        element = self.get_element(By.XPATH, ele_xpath)
        if not element:
            aklog_debug('%s is not found' % ele_xpath)
            return None
        else:
            return self.image.is_pure_color(element, percent)

    def check_image_rgb_by_automation_id(self, ele_id, ratio, fix_rgb):
        """检查元素图像某种颜色占比"""
        aklog_printf()
        element = self.get_element(AppiumBy.ACCESSIBILITY_ID, ele_id)
        if not element:
            aklog_printf('%s is not found' % ele_id)
            return None
        if len(fix_rgb) == 4:
            value = self.image.check_screen_color_rgba(element, fix_rgb)
        else:
            value = self.image.check_screen_color(element, fix_rgb)
        aklog_printf('%r color proportion: %.30f' % (fix_rgb, value))
        if value is None:
            return None
        if value > ratio:
            return True
        else:
            return False

    def get_string_by_ocr_custom_area_image(self, area):
        """
        在指定区域内识别文字并输出
        area: (start_x, start_y, end_x, end_y)
        """
        return self.image.get_screenshot_by_custom_size(*area).image_easyocr_read_text()

    # endregion


if __name__ == '__main__':
    app = WindowBase(r'C:\Windows\System32\notepad.exe')
    # app.start_appium_server()
    app.app_run()
    # app.click((AppiumBy.NAME, '帮助(H)'))
    app.right_click((AppiumBy.NAME, '文本编辑器'))
    # app.app_connect('ETS5™ - Test Project KNXProduct-K32 20250309-1907')
    # aklog_info(app.get_page_source())
    # app.click_btn_by_xpath('//*[@HelpText="新建项目"]')
    # app.app_close_quit()
    # time.sleep(3)
    # app.stop_driver()

    app = WindowBase(r'C:\Users\Administrator\Desktop\AKUpgradeTool_V4.2.0.6\UpgradeTool.exe')
    app.start_appium_server()
    app.app_run()
