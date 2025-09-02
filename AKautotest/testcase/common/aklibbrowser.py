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
import time
import traceback
import tempfile
import pyperclip as pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, \
    UnexpectedAlertPresentException, ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC  # available since 2.26.0
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from libconfig.COMMON.libconfig_NORMAL import config_NORMAL
import win32api, win32con


class libbrowser(object):
    """浏览器通用操作类，与设备无关"""

    # region 初始化相关

    def __init__(self, device_info=None, device_config=None, wait_time=2):
        self.driver = None
        self.chrome_service = None
        self.device_name = ''
        self.device_info = None
        self.device_config = config_NORMAL()
        self.image = None
        self._imgs = []
        # self.driver = ''
        self.web_width = 1920
        self.web_height = 1080
        # self.chrome_path = root_path + '\\testfile\\Browser\\Chrome\\chromedriver.exe'
        self.wait_time = wait_time
        self.chrome_prefs = None
        self.window_operation = None
        self.user_agent = ''
        self.device_info_init(device_info, device_config)

    def device_info_init(self, device_info=None, device_config=None):
        if device_info:
            self.device_info = device_info
            self.device_name = device_info['device_name']
        if device_config:
            self.device_config = device_config
        if self.device_name and self.device_config and not self.device_config.get_device_name():
            self.device_config.put_device_name(self.device_name)
        if self.device_config:
            self.chrome_prefs = self.device_config.get_chrome_prefs()

    def init(self):
        aklog_debug()
        if self.driver:
            aklog_debug('当前浏览器已启动')
            return
        chrome_options = webdriver.ChromeOptions()
        if self.chrome_prefs:
            chrome_prefs = self.chrome_prefs
            params = {'cmd': 'Page.setDownloadBehavior',
                      'params': {'behavior': 'allow',
                                 'downloadPath': self.chrome_prefs['download.default_directory']}}
        else:
            chrome_prefs = {'download.prompt_for_download': False,
                            'download.default_directory': root_path + '\\testfile\\Browser\\Chrome_Download\\COMMON'}
            params = {'cmd': 'Page.setDownloadBehavior',
                      'params': {'behavior': 'allow',
                                 'downloadPath': root_path + '\\testfile\\Browser\\Chrome_Download\\COMMON'}}
        # 关闭登录后提示保存密码弹窗
        chrome_prefs["credentials_enable_service"] = False
        chrome_prefs["profile.password_manager_enabled"] = False
        chrome_options.add_argument('--log-level=3')  # 3 = 只显示致命错误
        chrome_options.add_experimental_option('prefs', chrome_prefs)

        # 2025.4.8 新谷歌浏览器, 在类似注册sip账号的情况下会弹窗您刚才使用的密码遭遇了数据泄漏. google密码管理工具建议您立即更改密码
        # 禁用密码重用检测（部分版本可能有效）
        chrome_options.add_experimental_option("excludeSwitches", ["enable-password-reuse-detection"])
        # 启用隐身模式
        chrome_options.add_argument("--incognito")

        # 开启开发者模式
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        # 需要增加这个配置项，否则会提示请停用以开发者模式运行的扩展程序
        chrome_options.add_experimental_option('useAutomationExtension', False)
        if param_get_browser_headless_enable():
            chrome_options.add_argument("--headless")  # 无头模式（无界面模式，后台运行）
            chrome_options.add_argument('window-size=1920x1080')  # 指定浏览器分辨率
            chrome_options.add_argument('--window-size=1920x1080')  # 指定浏览器分辨率
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')  # 浏览器最大化
            # 替换UserAgent
            if self.user_agent:
                chrome_options.add_argument("user-agent=%s" % self.user_agent)
        else:
            chrome_options.add_argument('--start-maximized')  # 浏览器最大化

        # 禁用Chrome沙盒机制，解决部分权限受限或虚拟机环境下浏览器无法启动的问题。
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument('--disable-infobars')  # 禁用浏览器正在被自动化程序控制的提示
        # chrome_options.add_argument('--incognito')  # 启动进入隐身模式
        chrome_options.add_argument('--disable-gpu')  # 禁用GPU加速
        chrome_options.add_argument('--test-type')
        chrome_options.add_argument('--ignore-ssl-errors=yes')  # 忽略证书错误
        chrome_options.add_argument('--ignore-certificate-errors')  # https访问忽略证书错误
        chrome_options.add_argument('--disable-plugins')  # 禁用插件
        chrome_options.add_argument('--disable-popup-blocking')  # 禁用弹出拦截
        chrome_options.add_argument('no-default-browser-check')  # 不检查默认浏览器
        # 指定浏览器缓存目录，新版本Chrome浏览器会把缓存放在C:\Program Files
        chrome_options.add_argument('–disk-cache-dir="%s"' % tempfile.gettempdir())
        position = get_secondary_position()
        if position:
            chrome_options.add_argument(f'--window-position={position[0]},{position[1]}')  # 窗口显示在副屏上
        for i in range(3):
            try:
                chrome_driver_path = g_chrome_driver_path.replace('\\', '/')
                aklog_debug('chrome_driver_path: %s' % chrome_driver_path)
                self.chrome_service = Service(chrome_driver_path)
                self.chrome_service.command_line_args()
                # important 2025.6.18 lex: 4.33.0 上验证， 如果service.start(), 会起来一个chromedriver.exe. 再继续webdriver.Chrome(service)， 会起来第二个chromedriver.exe.
                # 后续的driver的pid实际上是第二个chromedriver.exe的, 第一个被浪费了资源. 且service.start()起来的chromedriver.exe 在self.driver.quit（）仍存活

                # 先注释以下start试试效果.
                # self.chrome_service.start()
                self.driver = webdriver.Chrome(chrome_options, self.chrome_service)
                # 不检查文件安全直接下载文件
                self.driver.command_executor.add_command(
                    "send_command", "POST", '/session/$sessionId/chromium/send_command')
                self.driver.execute("send_command", params)
                self.driver.set_page_load_timeout(60)
                self.driver.set_script_timeout(60)
                self.driver.implicitly_wait(self.wait_time)
                self.image = Image_process(self.driver)
                self.window_operation = Window_process()
                user_agent = self.driver.execute_script("return navigator.userAgent")
                self.user_agent = user_agent.replace('HeadlessChrome', 'Chrome')
                self.max_window()  # 2025.6.5 测试不调用max的话, chrome_options.add_argument('--start-maximized') 无效果, 设备有头模式下没有全屏显示.
                break
            except:
                aklog_debug('打开浏览器失败，重试...')
                aklog_debug(str(traceback.format_exc()))
                if 'OSError: [WinError 6] 句柄无效' in traceback.format_exc():
                    if i == 2:
                        self.close_and_quit()
                        time.sleep(5)
                        # param_put_failed_to_exit_enable(True)
                        raise RuntimeError('出现句柄无效问题. ')
                elif 'This version of ChromeDriver only' in traceback.format_exc():
                    # 2025.3.3 lex: 出现调试中也有出现谷歌浏览器升级.
                    aklog_error('运行中出现chromedriver和浏览器不匹配!!!')
                    self.close_and_quit()
                    if config_get_value_from_ini_file('config', 'chrome_driver_auto_update_enable'):
                        ChromeDriverUpdate.chrome_driver_auto_update()
                    else:
                        if i == 2:
                            self.close_and_quit()
                            time.sleep(5)
                            # param_put_failed_to_exit_enable(True)
                            raise RuntimeError('出现谷歌浏览器驱动不匹配. ')
                self.close_and_quit()
                time.sleep(5)
                continue

    def init_headless(self):
        """当前只用于打开测试报告"""
        aklog_debug()
        chrome_options = webdriver.ChromeOptions()
        # 禁用Chrome沙盒机制，解决部分权限受限或虚拟机环境下浏览器无法启动的问题。
        chrome_options.add_argument('--log-level=3')  # 3 = 只显示致命错误
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument('window-size=1920x1080')  # 指定浏览器分辨率
        chrome_options.add_argument('--disable-gpu')  # 禁用GPU加速
        chrome_options.add_argument('--disable-infobars')  # 禁用浏览器正在被自动化程序控制的提示
        chrome_options.add_argument('--ignore-certificate-errors')  # https访问忽略证书错误
        chrome_options.add_argument('--test-type')
        chrome_options.add_argument('--disable-plugins')  # 禁用插件
        chrome_options.add_argument('--disable-popup-blocking')  # 禁用弹出拦截
        chrome_options.add_argument('no-default-browser-check')  # 不检查默认浏览器
        chrome_options.add_argument('–disk-cache-dir="%s"' % tempfile.gettempdir())
        # 开启开发者模式
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        # 需要增加这个配置项，否则会提示请停用以开发者模式运行的扩展程序
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # 禁用密码重用检测（部分版本可能有效）
        chrome_options.add_experimental_option("excludeSwitches", ["enable-password-reuse-detection"])
        # 启用隐身模式
        # chrome_options.add_argument("--incognito")
        # chrome_options.add_argument('--start-maximized')
        # chrome_path = root_path + '\\testfile\\Browser\\Chrome\\chromedriver.exe'
        if self.driver is None:
            chrome_driver_path = g_chrome_driver_path
            chrome_driver_path = chrome_driver_path.replace('\\', '/')
            self.chrome_service = Service(chrome_driver_path)
            self.chrome_service.command_line_args()
            # self.chrome_service.start()
            self.driver = webdriver.Chrome(chrome_options, self.chrome_service)
            self.driver.set_page_load_timeout(120)
            self.driver.set_script_timeout(120)
            self.driver.implicitly_wait(self.wait_time)
            # self.driver.set_window_size(self.web_width, self.web_height)
            self.image = Image_process(self.driver)
            self.window_operation = Window_process()

    def driver_quit(self):
        try:
            self.driver.quit()
            time.sleep(1)
        except:
            aklog_debug(traceback.format_exc())

        # 关闭Service
        try:
            self.chrome_service.stop()
            time.sleep(1)
        except:
            aklog_debug(traceback.format_exc())
        self.driver = None

    def close_and_quit(self):
        aklog_debug('关闭所有浏览器窗口和驱动')
        if self.driver is None:
            aklog_debug('驱动已关闭')
            return True
        # 关闭浏览器窗口
        try:
            handles = self.driver.window_handles
            for handle in handles:
                self.driver.switch_to.window(handle)
                self.driver.close()
                time.sleep(0.2)
        except:
            aklog_debug(str(traceback.format_exc()))

        self.driver_quit()

    def get_driver(self):
        return self.driver

    def get_session_info(self, storage='localStorage'):
        """获取会话相关信息，比如Token
        storage: 是要从localStorage中获取还是要从sessionStorage中获取，具体看目标系统存到哪个中
        """
        session_info = self.driver.execute_script('return %s;' % storage)
        session_info = json_loads_2_dict(session_info)
        return session_info

    # 网页超时时间
    def get_wait_time(self):
        return self.wait_time

    def set_implicitly_wait(self, wait_time):
        if self.driver:
            self.driver.implicitly_wait(wait_time)

    def restore_implicitly_wait(self):
        if self.driver:
            self.driver.implicitly_wait(self.wait_time)

    # 设备信息
    def get_device_info(self):
        return self.device_info

    def get_device_config(self) -> config_NORMAL:
        return self.device_config

    # 截图保存list
    def reset_imgs(self):
        self._imgs = []
        param_reset_screenshots_imgs()

    def get_imgs(self):
        return self._imgs

    # 网页访问
    def get_current_url(self):
        for i in range(2):
            try:
                url = self.driver.current_url
                aklog_debug('current_url: %s' % url)
                return url
            except UnexpectedAlertPresentException:
                time.sleep(0.5)
                continue
            except:
                aklog_debug(str(traceback.format_exc()))
                return None

    def visit_url(self, url, timeout=None):
        # 2021.12.24 C313碰到visit url 8849超时的情况, 之后又继续操作通话相关的内容 导致超时
        if not self.driver:
            self.init()
        if timeout:
            self.driver.set_page_load_timeout(timeout)
        aklog_debug('visit url: %s' % url)
        try:
            self.driver.get(url)
            if timeout:
                self.driver.set_page_load_timeout(60)
            return True
        except:
            aklog_debug('visit url failed, ' + str(traceback.format_exc()))
            if timeout:
                self.driver.set_page_load_timeout(60)
            return False

    # endregion

    # region 窗口操作

    def close_window(self):
        aklog_debug('关闭浏览器当前窗口')
        try:
            self.driver.close()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def max_window(self):
        aklog_debug('max browser window')
        try:
            if param_get_browser_headless_enable():
                # headless下, 默认分辨率800*600, 即使chrome_options.add_argument('--window-size=1920,1080')后,
                # 调用maximize_window()后也会变成800 * 600, 导致S562, S565的8849显示截断, 换一种实现.
                self.driver.set_window_size(1920, 1080)
                # self.driver.execute_script("document.body.style.zoom = 1;")  # 设置缩放比例为100%
            else:
                self.driver.maximize_window()
            return True
        except:
            aklog_debug('max browser window failed')
            return False

    def new_window(self, window_name=None):
        aklog_debug('新建标签页')
        try:
            if self.driver.session_id is None:
                self.close_and_quit()
                time.sleep(1)
                self.init()
            if not window_name:
                window_name = 'new table'
            js = 'window.open("%s")' % window_name
            self.driver.execute_script(js)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def switch_window(self, index):
        aklog_debug('切换标签页 %s' % index)
        try:
            handles = self.driver.window_handles
            self.driver.switch_to.window(handles[index])
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def switch_last_window(self):
        aklog_debug('切换到最后一个标签页')
        try:
            handles = self.driver.window_handles
            self.driver.switch_to.window(handles[-1])
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 刷新、缓存操作

    def swipe_down(self):
        aklog_debug('下滑')
        try:
            js = "var q=document.documentElement.scrollTop=100000"
            self.driver.execute_script(js)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def web_refresh(self, sec=1, force=False):
        aklog_debug()
        t1 = time.time()
        try:
            if force:
                # 用js方式强制刷新，reload参数要设置为true才是强制刷新，否则会使用缓存
                self.driver.execute_script("location.reload(true);")
            else:
                self.driver.refresh()
            if time.time() - t1 > 20:
                aklog_error('设备刷新网页超过20秒响应!!!!!, 可能出现重启或卡顿!!!!')
            time.sleep(sec)
            return True
        except:
            if time.time() - t1 > 20:
                aklog_error('设备刷新网页超过20秒响应!!!!!, 可能出现重启或卡顿!!!!')
            aklog_debug(str(traceback.format_exc()))
            return False

    def delete_browser_all_cookies(self):
        aklog_debug('delete_browser_all_cookies')
        try:
            self.driver.delete_all_cookies()
            return True
        except:
            aklog_debug('delete_browser_all_cookies failed')
            return False

    # endregion

    # region iframe操作

    def switch_iframe_by_name(self, ele_name, timeout=None):
        """切换到子页面iframe"""
        aklog_debug('switch_iframe_by_name: %s' % ele_name)
        try:
            if timeout:
                self.set_implicitly_wait(timeout)
            self.driver.switch_to.frame(ele_name)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False
        finally:
            self.restore_implicitly_wait()

    def switch_iframe_to_default(self):
        """切换iframe到原来默认的"""
        aklog_debug('switch_iframe_to_default')
        try:
            self.driver.switch_to.default_content()
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    # endregion

    # region 输入框相关

    def input_edit_by_name(self, ele_name, content, sec=0.1):
        aklog_debug("input_edit_by_name : %s  %s" % (ele_name, content))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.NAME, ele_name)))
            ele.clear()
            time.sleep(0.1)
            # 有些输入框clear方法无法清空，用全选删除按键操作来清空
            if ele.get_attribute('value'):
                ele.send_keys(Keys.CONTROL, 'a')
                ele.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
            ele.send_keys(content)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_edit_by_id(self, ele_id, content, sec=0.1):
        aklog_debug("input_edit_by_id : %s  %s" % (ele_id, content))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.ID, ele_id)))
            ele.clear()
            time.sleep(0.1)
            # 有些输入框clear方法无法清空，用全选删除按键操作来清空
            if ele.get_attribute('value'):
                ele.send_keys(Keys.CONTROL, 'a')
                ele.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
            ele.send_keys(content)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_edit_by_class_name(self, ele_name, content, sec=0.1):
        aklog_debug("input_edit_by_class_name : %s  %s" % (ele_name, content))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.CLASS_NAME, ele_name)))
            ele.clear()
            time.sleep(0.1)
            # 有些输入框clear方法无法清空，用全选删除按键操作来清空
            if ele.get_attribute('value'):
                ele.send_keys(Keys.CONTROL, 'a')
                ele.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
            ele.send_keys(content)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_edit_by_xpath(self, ele_xpath, content, sec=0.1, by_keys=False):
        aklog_debug()
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            # 有些输入框清空提交判断为空是否提示，不能用clear()方法，得用按键方式操作
            if not by_keys:
                ele.clear()
                time.sleep(0.1)
                # 有些输入框clear方法无法清空，用全选删除按键操作来清空
                if ele.get_attribute('value'):
                    ele.send_keys(Keys.CONTROL, 'a')
                    ele.send_keys(Keys.BACKSPACE)
                    time.sleep(0.1)
            else:
                ele.send_keys(Keys.CONTROL, 'a')
                ele.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
                if ele.get_attribute('value'):
                    ele.clear()
                    time.sleep(0.1)
            ele.send_keys(content)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def clear_edit_by_name(self, ele_name, sec=0.1):
        aklog_debug("input_edit_by_name : %s" % ele_name)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.NAME, ele_name)))
            ele.clear()
            # 有些输入框clear方法无法清空，用全选删除按键操作来清空
            time.sleep(0.1)
            if ele.get_attribute('value'):
                ele.send_keys(Keys.CONTROL, 'a')
                ele.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def clear_edit_by_id(self, ele_id, sec=0.1):
        aklog_debug("input_edit_by_id : %s" % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.ID, ele_id)))
            ele.clear()
            # 有些输入框clear方法无法清空，用全选删除按键操作来清空
            time.sleep(0.1)
            if ele.get_attribute('value'):
                ele.send_keys(Keys.CONTROL, 'a')
                ele.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def clear_edit_by_xpath(self, ele_xpath, sec=0.1, by_keys=False):
        aklog_debug("clear_edit_by_xpath : %s" % ele_xpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            # 有些输入框清空提交判断为空是否提示，不能用clear()方法，得用按键方式操作
            if not by_keys:
                ele.clear()
                time.sleep(0.1)
                # 有些输入框clear方法无法清空，用全选删除按键操作来清空
                if ele.get_attribute('value'):
                    ele.send_keys(Keys.CONTROL, 'a')
                    ele.send_keys(Keys.BACKSPACE)
            else:
                ele.send_keys(Keys.CONTROL, 'a')
                ele.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
                if ele.get_attribute('value'):
                    ele.clear()
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def delete_edit_by_xpath(self, ele_xpath, sec=0.1):
        aklog_debug("delete_edit_by_xpath : %s" % ele_xpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            ele.send_keys(Keys.CONTROL + 'a')
            ele.send_keys(Keys.DELETE)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 日期时间控件操作

    def input_date_by_id(self, ele_id, date, sec=0.1):
        aklog_debug("input_date_by_id : %s  %s" % (ele_id, date))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.ID, ele_id)))
            # readonly_value = ele.get_attribute('readonly')
            remove_js = 'arguments[0].removeAttribute("readonly")'
            self.driver.execute_script(remove_js, ele)
            ele.clear()
            # 有些输入框clear方法无法清空，用全选删除按键操作来清空
            time.sleep(0.1)
            if ele.get_attribute('value'):
                ele.send_keys(Keys.CONTROL, 'a')
                ele.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
            ele.send_keys(date)
            # set_js = 'arguments[0].setAttribute("readonly", "%s")' % readonly_value
            # self.driver.execute_script(set_js, ele)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_date_by_xpath(self, ele_xpath, date_str, sec=0.1):
        aklog_debug("input_date_by_xpath : %s  %s" % (ele_xpath, date_str))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            # readonly_value = ele.get_attribute('readonly')
            remove_js = 'arguments[0].removeAttribute("readonly")'
            self.driver.execute_script(remove_js, ele)
            ele.clear()
            # 有些输入框clear方法无法清空，用全选删除按键操作来清空
            time.sleep(0.1)
            if ele.get_attribute('value'):
                ele.send_keys(Keys.CONTROL, 'a')
                ele.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
            ele.send_keys(date_str)
            # set_js = 'arguments[0].setAttribute("readonly", "%s")' % readonly_value
            # self.driver.execute_script(set_js, ele)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 文件导入操作

    def upload_file_by_id(self, ele_id, file_path, sec=1):
        aklog_debug("upload_file_by_id : %s  %s" % (ele_id, file_path))
        if not os.path.exists(file_path):
            aklog_warn('上传文件失败, 文件: {}不存在!!'.format(file_path))
            return False
        try:
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id))).send_keys(file_path)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def upload_file_by_name(self, ele_name, file_path, sec=1):
        aklog_debug("upload_file_by_name : %s  %s" % (ele_name, file_path))
        if not os.path.exists(file_path):
            aklog_warn('上传文件失败, 文件: {}不存在!!'.format(file_path))
            return False
        try:
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name))).send_keys(file_path)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def upload_file_by_xpath(self, ele_xpath, file_path, sec=1):
        """上传文件，增加判断input元素是否可见，如果不可见则需要js脚本修改属性"""
        aklog_debug("upload_file_by_xpath : %s  %s" % (ele_xpath, file_path))
        if not os.path.exists(file_path):
            aklog_warn('上传文件失败, 文件: {}不存在!!'.format(file_path))
            return False
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            if not ele.is_displayed():  # 如果元素是无效的，而且还是//input[@type = 'hidden' ] 的标签
                if ele.get_attribute("type") == 'hidden':
                    aklog_debug('type is hidden')
                    # 使用js 将他 type 修改为 text，让他生效。
                    js = 'arguments[0].setAttribute("type","text")'
                    self.driver.execute_script(js, ele)
                elif ele.get_attribute('style') == "display: none;":
                    aklog_debug('style is display: none;')
                    # 如果不是 //input[@type = 'hidden' ] 使用 display = none 或者 class 隐藏, 使用js让他显示
                    js = "arguments[0].style.display = 'block';"
                    self.driver.execute_script(js, ele)
                time.sleep(0.2)
            ele.send_keys(file_path)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def upload_file_from_window_by_xpath(self, ele_xpath, file_path, sec=0.2):
        """通过弹窗定位窗口填入文件路径方式来上传，不适用于无头模式，并且当电脑比较卡时无法及时打开窗口，会失败"""
        aklog_debug("upload_file_from_window_by_xpath : %s  %s"
                    % (ele_xpath, file_path))
        try:
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath))).click()
            time.sleep(10)
            self.window_operation.upload_file(file_path)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def upload_file_by_keyboard_by_xpath(self, ele_xpath, file_path):
        """使用 python 的 win32api，win32con 模拟按键输入，实现文件上传操作。也不适用于无头模式
        :param ele_xpath: 页面中的上传文件按钮
        :param file_path: 要上传的文件地址，绝对路径。如：D:\\timg (1).jpg
        """
        aklog_debug("upload_file_by_keyboard_by_xpath : %s  %s"
                    % (ele_xpath, file_path))
        try:
            pyperclip.copy(file_path)  # 复制文件路径到剪切板
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath))).click()
            time.sleep(10)  # 等待程序加载 时间 看你电脑的速度 单位(秒)
            # 发送 ctrl（17） + V（86）按钮
            win32api.keybd_event(17, 0, 0, 0)
            win32api.keybd_event(86, 0, 0, 0)
            win32api.keybd_event(86, 0, win32con.KEYEVENTF_KEYUP, 0)  # 松开按键
            win32api.keybd_event(17, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(1)
            win32api.keybd_event(13, 0, 0, 0)  # (回车)
            win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)  # 松开按键
            win32api.keybd_event(13, 0, 0, 0)  # (回车)
            win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 点击操作

    def click_btn_by_id(self, ele_id, sec=0.2, visible=True):
        for i in range(2):
            try:
                if visible:
                    ele = WebDriverWait(self.driver, self.wait_time).until(
                        EC.visibility_of_element_located((By.ID, ele_id)))
                else:
                    ele = WebDriverWait(self.driver, self.wait_time).until(
                        EC.presence_of_element_located((By.ID, ele_id)))
                value = ele.get_attribute('value')
                ele.click()
                if value and i == 0:
                    aklog_debug("click_btn_by_id : %s ,  value is %s " % (ele_id, value))
                elif i == 0:
                    aklog_debug("click_btn_by_id : %s" % ele_id)
                time.sleep(sec)
                return True
            except StaleElementReferenceException as e:
                if i == 0:
                    aklog_debug("click_btn_by_id : %s" % ele_id)
                # self.driver.refresh()
                time.sleep(1)
                continue
            except TimeoutException:
                if i == 1:
                    aklog_debug('%s not found' % ele_id)
                    return False
                time.sleep(1)
                continue
            # except UnexpectedAlertPresentException:
            #     self.alert_confirm_accept()
            #     continue
            except ElementClickInterceptedException:
                if i == 0:
                    aklog_debug("click_btn_by_id : %s" % ele_id)
                try:
                    ele = WebDriverWait(self.driver, self.wait_time).until(
                        EC.visibility_of_element_located((By.ID, ele_id)))
                    value = ele.get_attribute('value')
                    self.driver.execute_script("arguments[0].click();", ele)
                    if value and i == 0:
                        aklog_debug("click_btn_by_id : %s ,  value is %s " % (ele_id, value))
                    elif i == 0:
                        aklog_debug("click_btn_by_id : %s" % ele_id)
                    time.sleep(sec)
                    return True
                except:
                    aklog_debug(str(traceback.format_exc()))
                    return False
            except ElementNotInteractableException:
                # 2021.11.1 linl: R27 web_call以后, 点击upgrade页面失败: element zero size. 做一次滚动.

                if i == 0:
                    aklog_debug("click_btn_by_id : %s" % ele_id)
                    try:
                        ele = WebDriverWait(self.driver, self.wait_time).until(
                            EC.visibility_of_element_located((By.ID, ele_id)))
                        js4 = "arguments[0].scrollIntoView();"
                        self.driver.execute_script(js4, ele)
                    except:
                        pass
                else:
                    aklog_debug(str(traceback.format_exc()))
                    return False
            except:
                if i == 0:
                    aklog_debug("click_btn_by_id : %s" % ele_id)
                aklog_debug("click_btn_by_id : %s timeout, not found" % ele_id)
                aklog_debug(str(traceback.format_exc()))
                return False

    def click_btn_by_class_name(self, ele_classname, sec=0.2):
        aklog_debug("click_btn_by_class_name : %s" % ele_classname)
        for i in range(2):
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, ele_classname))).click()
                time.sleep(sec)
                return True
            except StaleElementReferenceException as e:
                print(e)
                # self.driver.refresh()
                time.sleep(1)
                continue
            # except UnexpectedAlertPresentException:
            #     self.alert_confirm_accept()
            #     continue
            except ElementClickInterceptedException:
                try:
                    ele = WebDriverWait(self.driver, self.wait_time).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, ele_classname)))
                    self.driver.execute_script("arguments[0].click();", ele)
                    time.sleep(sec)
                    return True
                except:
                    aklog_debug(str(traceback.format_exc()))
                    return False
            except:
                aklog_debug(str(traceback.format_exc()))
                return False

    def click_btn_by_xpath(self, ele_xpath, sec=0.2, visible=True):
        aklog_debug("click_btn_by_xpath : %s" % ele_xpath)
        for i in range(2):
            try:
                if visible:
                    ele = WebDriverWait(self.driver, self.wait_time).until(
                        EC.visibility_of_element_located((By.XPATH, ele_xpath)))
                else:
                    ele = WebDriverWait(self.driver, self.wait_time).until(
                        EC.presence_of_element_located((By.XPATH, ele_xpath)))
                ele.click()
                time.sleep(sec)
                return True
            except StaleElementReferenceException as e:
                print(e)
                # self.driver.refresh()
                time.sleep(1)
                continue
            # except UnexpectedAlertPresentException:
            #     self.alert_confirm_accept()
            #     continue
            except ElementNotInteractableException:
                try:
                    if visible:
                        ele = WebDriverWait(self.driver, self.wait_time).until(
                            EC.visibility_of_element_located((By.XPATH, ele_xpath)))
                    else:
                        ele = WebDriverWait(self.driver, self.wait_time).until(
                            EC.presence_of_element_located((By.XPATH, ele_xpath)))
                    self.driver.execute_script("arguments[0].click();", ele)
                    time.sleep(sec)
                    return True
                except:
                    aklog_debug(str(traceback.format_exc()))
                    return False
            except ElementClickInterceptedException:
                try:
                    if visible:
                        ele = WebDriverWait(self.driver, self.wait_time).until(
                            EC.visibility_of_element_located((By.XPATH, ele_xpath)))
                    else:
                        ele = WebDriverWait(self.driver, self.wait_time).until(
                            EC.presence_of_element_located((By.XPATH, ele_xpath)))
                    self.driver.execute_script("arguments[0].click();", ele)
                    time.sleep(sec)
                    return True
                except:
                    aklog_debug(str(traceback.format_exc()))
                    return False
            except TimeoutException:
                aklog_debug('%s not found' % ele_xpath)
                return False
            except:
                aklog_debug(str(traceback.format_exc()))
                return False

    def click_btn_by_name(self, ele_name, sec=0.2):
        aklog_debug("click_btn_by_name : %s" % ele_name)
        for i in range(2):
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.visibility_of_element_located((By.NAME, ele_name))).click()
                time.sleep(sec)
                return True
            except StaleElementReferenceException as e:
                print(e)
                # self.driver.refresh()
                time.sleep(1)
                continue
            # except UnexpectedAlertPresentException:
            #     self.alert_confirm_accept()
            #     continue
            except ElementClickInterceptedException:
                try:
                    ele = WebDriverWait(self.driver, self.wait_time).until(
                        EC.visibility_of_element_located((By.NAME, ele_name)))
                    self.driver.execute_script("arguments[0].click();", ele)
                    time.sleep(sec)
                    return True
                except:
                    aklog_debug(str(traceback.format_exc()))
                    return False
            except:
                aklog_debug(str(traceback.format_exc()))
                return False

    def click_multi_elements_by_xpath(self, ele_xpath, sec=0.2):
        """点击多个具有相同Xpath的元素"""
        aklog_debug("click_multi_elements_by_xpath : %s" % ele_xpath)
        try:
            elements = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_all_elements_located((By.XPATH, ele_xpath)))
            for ele in elements:
                self.driver.execute_script("arguments[0].scrollIntoView();", ele)
                time.sleep(0.2)
                ele.click()
                time.sleep(0.2)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    @staticmethod
    def click_elements(*elements, duration=0.2, sec=0.2):
        """点击多个元素，需要先获取元素，适合需要快速点击多个元素"""
        aklog_debug("click_elements")
        try:
            for ele in elements:
                ele.click()
                time.sleep(duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_by_link_text(self, link_text, sec=0.2):
        """web3.0:链接文本属性点击"""
        aklog_debug("click_btn_by_link_text : %s" % link_text)
        for i in range(2):
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.visibility_of_element_located((By.LINK_TEXT, link_text))).click()
                time.sleep(sec)
                return True
            except StaleElementReferenceException as e:
                print(e)
                # self.driver.refresh()
                time.sleep(1)
                continue
            # except UnexpectedAlertPresentException:
            #     self.alert_confirm_accept()
            #     continue
            except ElementClickInterceptedException:
                try:
                    ele = WebDriverWait(self.driver, self.wait_time).until(
                        EC.visibility_of_element_located((By.LINK_TEXT, link_text)))
                    self.driver.execute_script("arguments[0].click();", ele)
                    time.sleep(sec)
                    return True
                except:
                    aklog_debug(str(traceback.format_exc()))
                    return False
            except:
                aklog_debug(str(traceback.format_exc()))
                return False

    def click_btn_by_css_selector(self, ele_css_selector, sec=0.2):
        """
        浏览器设置相关的需要用到这个，需要先找到根节点，然后加 /deep/，这个deep可以添加多层目录，也可以不加中间目录层级，最后再加元素的id
        :param ele_css_selector: downloads-manager /deep/ downloads-item /deep/ [id=remove]
        :param sec: 操作后等待时间
        :return:
        """
        aklog_debug("click_btn_by_css_selector : %s" % ele_css_selector)
        for i in range(2):
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, ele_css_selector))).click()
                time.sleep(sec)
                return True
            except StaleElementReferenceException as e:
                print(e)
                # self.driver.refresh()
                time.sleep(1)
                continue
            # except UnexpectedAlertPresentException:
            #     self.alert_confirm_accept()
            #     continue
            except ElementClickInterceptedException:
                try:
                    ele = WebDriverWait(self.driver, self.wait_time).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, ele_css_selector)))
                    self.driver.execute_script("arguments[0].click();", ele)
                    time.sleep(sec)
                    return True
                except:
                    aklog_debug(str(traceback.format_exc()))
                    return False
            except:
                aklog_debug(str(traceback.format_exc()))
                return False

    def click_ele(self, ele, sec=0.1):
        try:
            ele.click()
            time.sleep(sec)
            return True
        except ElementClickInterceptedException:
            try:
                self.driver.execute_script("arguments[0].click();", ele)
                time.sleep(sec)
                return True
            except:
                aklog_debug(str(traceback.format_exc()))
                return False
        except ElementNotInteractableException:
            try:
                js4 = "arguments[0].scrollIntoView();"
                self.driver.execute_script(js4, ele)
                time.sleep(0.1)
                ele.click()
                time.sleep(sec)
                return True
            except:
                aklog_debug(str(traceback.format_exc()))
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_visible_ele_by_xpath(self, ele_xpath, sec=0.2):
        """页面存在多个相同Xpath的按钮，但只有一个是可见的，点击可见的按钮"""
        aklog_debug()
        try:
            elements = WebDriverWait(self.driver, self.wait_time). \
                until(EC.visibility_of_any_elements_located((By.XPATH, ele_xpath)))
            ele = elements[0]
            ele.click()
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 滑动条滑动操作

    def slide_bar_horizontal_by_id(self, ele_id, value, val_range: tuple, sec=0.2, click_hold=True):
        aklog_debug("slide_bar_horizontal_by_id, ele_id: %s, value: %s" % (ele_id, value))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.ID, ele_id)))
            ele_rect = ele.rect
            # 获取设置值的目标x轴相对于元素左上角X坐标的差值
            target_x = round(int(value) / (int(val_range[1]) - int(val_range[0]))
                             * ele_rect['width']) + 2
            # 移动鼠标到目标位置点击
            action_chains = ActionChains(self.driver)
            bigver = webdriver.__version__.split('.')[0]
            if bigver > '4' or (bigver == '4' and webdriver.__version__ != '4.0'):
                # 2025.4.11 lex: 4.0 以上版本, 以元素中心点为基准偏移. 4.0和以下则为左侧偏移.
                # 默认控件数值是左边-> 右边递增.
                wrange = int(val_range[1]) - int(val_range[0])
                step = int(ele_rect['width']) / wrange
                middle_value = wrange / 2
                offset = int(abs(int(value) - middle_value) * step)
                if value in [val_range[0], val_range[1]]:
                    if int(value) >= middle_value:
                        target_x = offset
                    else:
                        target_x = 0 - offset
                else:
                    if int(value) >= middle_value:
                        target_x = offset + 2
                    else:
                        target_x = 0 - (offset + 2)
                if click_hold:
                    action_chains.click_and_hold(ele).move_to_element_with_offset(ele, target_x, 0).release().perform()
                else:
                    action_chains.move_to_element_with_offset(ele, target_x, 0).click().perform()
            else:
                if click_hold:
                    action_chains.click_and_hold(ele).move_to_element_with_offset(ele, target_x, 0).release().perform()
                else:
                    action_chains.move_to_element_with_offset(ele, target_x, 0).click().perform()
            time.sleep(sec)
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 鼠标操作ActionChains
    def action_click_btn_by_xpath(self, ele_xpath, sec=0.2):
        aklog_debug("action_click_btn_by_xpath : %s" % ele_xpath)
        for i in range(2):
            try:
                ele = WebDriverWait(self.driver, self.wait_time).until(
                    EC.visibility_of_element_located((By.XPATH, ele_xpath)))
                ActionChains(self.driver).click(ele).perform()
                time.sleep(sec)
                return True
            except StaleElementReferenceException as e:
                print(e)
                # self.driver.refresh()
                time.sleep(1)
                continue
            # except UnexpectedAlertPresentException:
            #     self.alert_confirm_accept()
            #     continue
            except:
                aklog_debug(str(traceback.format_exc()))
                return False

    def click_and_hold_btn_by_xpath(self, ele_xpath, duration, sec=0.2):
        aklog_debug("click_and_hold_btn_by_xpath : %s" % ele_xpath)
        for i in range(2):
            try:
                ele = WebDriverWait(self.driver, self.wait_time).until(
                    EC.visibility_of_element_located((By.XPATH, ele_xpath)))
                action_chains = ActionChains(self.driver)
                action_chains.click_and_hold(ele).perform()
                action_chains.pause(duration).perform()
                action_chains.release(ele).perform()
                time.sleep(sec)
                return True
            except StaleElementReferenceException as e:
                print(e)
                # self.driver.refresh()
                time.sleep(1)
                continue
            # except UnexpectedAlertPresentException:
            #     self.alert_confirm_accept()
            #     continue
            except:
                aklog_debug(str(traceback.format_exc()))
                return False

    def click_and_hold_btn_by_id(self, ele_id, duration, sec=0.2):
        aklog_debug("click_and_hold_btn_by_id : %s" % ele_id)
        for i in range(2):
            try:
                ele = WebDriverWait(self.driver, self.wait_time).until(
                    EC.visibility_of_element_located((By.ID, ele_id)))
                action_chains = ActionChains(self.driver)
                action_chains.click_and_hold(ele).pause(duration).release().perform()
                time.sleep(sec)
                return True
            except StaleElementReferenceException as e:
                print(e)
                # self.driver.refresh()
                time.sleep(1)
                continue
            # except UnexpectedAlertPresentException:
            #     self.alert_confirm_accept()
            #     continue
            except:
                aklog_debug(str(traceback.format_exc()))
                return False

    def move_mouse_to_element(self, element, sec=0.5, alignToTop='true'):
        """鼠标移动到元素上悬停"""
        aklog_debug()
        try:
            # 有些元素不在可视范围内，需要先滚动页面到元素可见，才可以移动鼠标悬停
            self.driver.execute_script("arguments[0].scrollIntoView(%s);" % alignToTop, element)
            time.sleep(0.5)
            ActionChains(self.driver).move_to_element(element).perform()
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def move_mouse_by_offset(self, x_offset, y_offset, sec=0.5):
        """根据当前鼠标位置偏移量移动鼠标，注意鼠标移动后，再次调用该方法时，鼠标的起始位置已经改变"""
        aklog_debug()
        try:
            ActionChains(self.driver).move_by_offset(x_offset, y_offset).perform()
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def drag_and_drop_by_offset(self, element, x_offset, y_offset, sec=0.5):
        """按偏移量拖放元素"""
        aklog_debug()
        try:
            ActionChains(self.driver).drag_and_drop_by_offset(element, x_offset, y_offset).perform()
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_ele_by_offset(self, id_name_xpath, x_offset=0.5, y_offset=0.5, sec=0.5):
        """
        有些元素中心点无法点击，根据元素的左上角坐标偏移位置点击
        x_offset，y_offset: 相对于元素尺寸大小的比例，比如0.5表示中心位置
        """
        aklog_debug()
        xpath = id_name_xpath if id_name_xpath.startswith('/') else '//*[@id="%s" or @name="%s"]' % (
            id_name_xpath, id_name_xpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.XPATH, xpath)))
            ele_size = ele.size
            x_offset = int(ele_size['width'] * x_offset)
            y_offset = int(ele_size['height'] * y_offset)
            ActionChains(self.driver).move_to_element_with_offset(ele, x_offset, y_offset).perform()
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region JavaScript方式操作元素

    def click_by_js(self, ele):
        """js脚本方式点击"""
        aklog_debug('click_by_js')
        self.driver.execute_script("arguments[0].click();", ele)

    def scroll_into_view_by_js(self, option_ele, alignToTop='true'):
        """
        js脚本方式滚动元素到可见，多用于下拉框滚动
        alignToTop: true, false, str类型，True表示滚动元素显示靠近页面顶部，false表示滚动元素显示靠近页面底部
        """
        aklog_debug('scroll_into_view_by_js')
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(%s);" % alignToTop, option_ele)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def wait_ele_appear_by_js_path(self, js_path, wait_time=None):
        """等待元素出现，间隔1秒检查一次"""
        if wait_time is None:
            wait_time = self.wait_time
        for i in range(wait_time + 1):
            try:
                ele = self.driver.execute_script('return %s' % js_path)
                return ele
            except:
                if i < wait_time:
                    time.sleep(1)
                    continue
                else:
                    raise

    def set_attribute_by_id(self, ele_id, attribute, value, sec=0.2):
        """修改元素属性值"""
        aklog_debug("set_attribute_by_id, ele_id: %s, attribute: %s, value: %s"
                    % (ele_id, attribute, value))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id)))
            js = 'arguments[0].setAttribute("%s","%s")' % (attribute, value)
            self.driver.execute_script(js, ele)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def remote_attribute_by_xpath(self, ele_id_xpath, attribute):
        aklog_debug()
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_id_xpath)))
            js = 'arguments[0].removeAttribute("%s")' % attribute
            self.driver.execute_script(js, ele)
            time.sleep(1)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def set_attribute_by_xpath(self, ele_xpath, attribute, value, sec=0.2):
        """修改元素属性值"""
        aklog_debug()
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            js = 'arguments[0].setAttribute("%s","%s")' % (attribute, value)
            self.driver.execute_script(js, ele)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def get_element_by_js_path(self, js_path, wait_time=None, print_trace=True):
        """有些元素位于ShadowRoot(Open)之内，需要用js方式去定位元素"""
        try:
            return self.wait_ele_appear_by_js_path(js_path, wait_time)
            # return self.driver.execute_script('return %s' % js_path)
        except:
            aklog_debug('not found')
            if print_trace:
                aklog_debug(traceback.format_exc())
            return None

    def input_edit_by_js_path(self, js_path, content, wait_time=None, print_trace=True):
        aklog_debug()
        try:
            ele = self.wait_ele_appear_by_js_path(js_path, wait_time)
            self.driver.execute_script('arguments[0].value="%s"' % content, ele)
        except:
            aklog_debug('not found')
            if print_trace:
                aklog_debug(traceback.format_exc())
            return None

    def click_btn_by_js_path(self, js_path, sec=0.2):
        """有些元素位于ShadowRoot(Open)之内，需要用js方式去定位元素"""
        aklog_debug()
        try:
            ele = self.wait_ele_appear_by_js_path(js_path)
            self.driver.execute_script("arguments[0].click();", ele)
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def action_click_btn_by_js_path(self, js_path, sec=0.2):
        """有些元素位于ShadowRoot(Open)之内，需要用js方式去定位元素"""
        aklog_debug()
        try:
            ele = self.wait_ele_appear_by_js_path(js_path)
            ActionChains(self.driver).move_to_element(ele).move_by_offset(5, 5).click().perform()
            time.sleep(sec)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def get_attribute_by_js_path(self, js_path, attribute, print_trace=True):
        aklog_debug()
        try:
            ele = self.wait_ele_appear_by_js_path(js_path)
            value = ele.get_attribute(attribute)
            aklog_debug('%s : %s' % (attribute, value))
            return value
        except:
            aklog_debug('ele not found')
            if print_trace:
                aklog_debug(traceback.format_exc())
            return None

    def get_ele_status_by_js_path(self, js_path):
        """有些元素位于ShadowRoot(Open)之内，需要用js方式去定位元素"""
        aklog_debug()
        try:
            ele = self.wait_ele_appear_by_js_path(js_path)
            ret = ele.is_enabled()
            aklog_debug('enable: %s' % ret)
            return ret
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_ele_counts_by_js_path(self, js_path):
        """获取相同js元素数量"""
        aklog_debug()
        try:
            counts = self.driver.execute_script('return %s.length;' % js_path)
            aklog_debug('counts: %s' % counts)
            return counts
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_checked_box_by_js_path(self, js_path):
        """判断勾选框是否勾选"""
        aklog_debug()
        try:
            ele = self.wait_ele_appear_by_js_path(js_path)
            status = ele.is_selected()
            aklog_debug("checked status: %s" % status)
            return status
        except:
            aklog_debug(traceback.format_exc())
            return None

    def check_box_by_js_path(self, js_path):
        """复选框勾选"""
        aklog_debug()
        try:
            ele = self.wait_ele_appear_by_js_path(js_path)
            if not ele.is_selected():
                self.driver.execute_script("arguments[0].click();", ele)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def uncheck_box_by_js_path(self, js_path):
        """复选框取消勾选"""
        aklog_debug()
        try:
            ele = self.wait_ele_appear_by_js_path(js_path)
            if ele.is_selected():
                self.driver.execute_script("arguments[0].click();", ele)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def is_visible_ele_by_js_path(self, js_path, wait_time=None, print_trace=True):
        """判断元素是否存在并可见"""
        aklog_debug()
        try:
            self.wait_ele_appear_by_js_path(js_path, wait_time)
            return True
        except:
            aklog_debug('not found')
            if print_trace:
                aklog_debug(traceback.format_exc())
            return False

    # endregion

    # region 获取元素信息相关（下拉框、复选框等类型单独分类）

    @staticmethod
    def get_text_list_xpath(textlist):
        """
        返回: normalize-space(text())="3" or normalize-space(text())="4" or normalize-space(text())="5"
        """
        if isinstance(textlist, list):
            textxpath = ' or '.join(['normalize-space(text())="{}"'.format(i) for i in textlist])
        else:
            textxpath = 'normalize-space(text())="{}"'.format(textlist)
        return textxpath

    def get_value_by_id(self, ele_id):
        aklog_debug("get_value_by_id : %s" % ele_id)
        try:
            value = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id))).text
            aklog_debug("%s, text is %s" % (ele_id, value))
            return value
        except TimeoutException:
            aklog_debug('%s not found' % ele_id)
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_values_by_id(self, ele_id):
        aklog_debug("get_values_by_id : %s" % ele_id)
        try:
            ele_lists = WebDriverWait(self.driver, self.wait_time).until(lambda x: x.find_elements(By.ID, ele_id))
            values = [ele.text for ele in ele_lists]
            aklog_debug("%s, texts: %s" % (ele_id, str(values)))
            return values
        except TimeoutException:
            aklog_debug('%s not found' % ele_id)
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_value_by_xpath(self, ele_xpath, wait_time=None, print_trace=True):
        aklog_debug("get_value_by_xpath: %s" % ele_xpath)
        try:
            if wait_time is None:
                wait_time = self.wait_time
            value = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath))).text
            aklog_debug("%s, text: %s" % (ele_xpath, value))
            return value
        except TimeoutException:
            aklog_debug('%s not found' % ele_xpath)
            return False
        except:
            aklog_debug('%s not found' % ele_xpath)
            if print_trace:
                aklog_debug(traceback.format_exc())
            return None

    def get_visible_value_by_xpath(self, ele_xpath, wait_time=None):
        """页面存在多个相同Xpath的元素，但只有一个是可见的，可以用本方法来获取可见元素信息"""
        aklog_debug("get_visible_value_by_xpath: %s" % ele_xpath)
        try:
            if wait_time is None:
                wait_time = self.wait_time
            elements = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_any_elements_located((By.XPATH, ele_xpath)))
            ele = elements[0]
            value = ele.text
            aklog_debug("%s, text: %s" % (ele_xpath, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_values_by_xpath(self, ele_xpath, delnull=True, printlog=True):
        """获取所有相同Xpath元素的文本信息"""
        if printlog:
            aklog_debug("get_values_by_xpath : %s" % ele_xpath)
        try:
            ele_lists = WebDriverWait(self.driver, self.wait_time).until(lambda x: x.find_elements(By.XPATH, ele_xpath))
            if delnull:
                values = [ele.text for ele in ele_lists if ele.text]
            else:
                values = [ele.text for ele in ele_lists]
            if printlog:
                aklog_debug("%s, texts: %s" % (ele_xpath, str(values)))
            return values
        except TimeoutException:
            aklog_debug('%s not found' % ele_xpath)
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_values_by_same_prefix_id(self, ele_part_id):
        """输入部分id内容, 获取包括该ID的元素内容"""
        aklog_debug("get_values_by_same_prefix_id : %s" % ele_part_id)
        ele_xpath = '//*[contains(@id, "{}")]'.format(ele_part_id)
        try:
            ele_lists = WebDriverWait(self.driver, self.wait_time).until(lambda x: x.find_elements(By.XPATH, ele_xpath))
            values = [ele.text for ele in ele_lists if ele.text]
            aklog_debug("%s, texts: %s" % (ele_xpath, str(values)))
            return values
        except TimeoutException:
            aklog_debug('%s not found' % ele_part_id)
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_value_by_name(self, ele_name):
        aklog_debug("get_value_by_name : %s" % ele_name)
        try:
            value = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name))).text
            aklog_debug("%s, text is %s" % (ele_name, value))
            return value
        except TimeoutException:
            aklog_debug('%s not found' % ele_name)
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_tag_name_by_id(self, ele_id):
        """获取元素的标签：input, select等"""
        aklog_debug("get_tag_name_by_id : %s" % ele_id)
        try:
            tag_name = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id))).tag_name
            aklog_debug("%s, tag_name: %s" % (ele_id, tag_name))
            return tag_name
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_tag_name_by_name(self, ele_name):
        """获取元素的标签：input, select等"""
        aklog_debug("get_tag_name_by_name : %s" % ele_name)
        try:
            tag_name = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name))).tag_name
            aklog_debug("%s, tag_name: %s" % (ele_name, tag_name))
            return tag_name
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_tag_name_by_xpath(self, ele_xpath):
        """获取元素的标签：input, select等"""
        aklog_debug()
        try:
            tag_name = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath))).tag_name
            aklog_debug("%s, tag_name: %s" % (ele_xpath, tag_name))
            return tag_name
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_value_by_id(self, ele_id, wait_time=None):
        aklog_debug("get_attribute_value_by_id : %s" % ele_id)
        try:
            if wait_time is None:
                wait_time = self.wait_time
            value = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id))).get_attribute('value')
            aklog_debug("%s, value is %s" % (ele_id, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_value_by_name(self, ele_name):
        aklog_debug("get_attribute_value_by_name : %s" % ele_name)
        try:
            value = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name))).get_attribute('value')
            aklog_debug("%s, value is %s" % (ele_name, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_value_by_xpath(self, ele_xpath):
        aklog_debug("get_attribute_value_by_xpath : %s" % ele_xpath)
        try:
            value = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath))).get_attribute('value')
            aklog_debug("%s, value is %s" % (ele_xpath, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_href_by_xpath(self, ele_xpath):
        aklog_debug("get_attribute_value_by_xpath : %s" % ele_xpath)
        try:
            value = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath))).get_attribute('href')
            aklog_debug("%s, value is %s" % (ele_xpath, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_values_by_id(self, ele_id):
        """获取相同ID的元素的value属性值"""
        aklog_debug("get_attribute_values_by_id : %s" % ele_id)
        try:
            ele_lists = WebDriverWait(self.driver, self.wait_time).until(lambda x: x.find_elements(By.ID, ele_id))
            values = [ele.get_attribute('value') for ele in ele_lists]
            aklog_debug("%s, values: %s" % (ele_id, str(values)))
            return values
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_values_by_same_prefix_id(self, ele_part_id):
        """获取相同ID的元素的value属性值"""
        aklog_debug("get_attribute_values_by_same_prefix_id : %s" % ele_part_id)
        ele_xpath = '//*[contains(@id, "{}")]'.format(ele_part_id)
        try:
            ele_lists = WebDriverWait(self.driver, self.wait_time).until(lambda x: x.find_elements(By.XPATH, ele_xpath))
            values = [ele.get_attribute('value') for ele in ele_lists if ele.get_attribute('value')]
            aklog_debug("%s, values: %s" % (ele_xpath, str(values)))
            return values
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_values_by_xpath(self, ele_xpath):
        """获取相同xpath的元素的value属性值"""
        aklog_debug("get_attribute_values_by_xpath : %s" % ele_xpath)
        try:
            ele_lists = WebDriverWait(self.driver, self.wait_time).until(lambda x: x.find_elements(By.XPATH, ele_xpath))
            values = [ele.get_attribute('value') for ele in ele_lists]
            aklog_debug("%s, values: %s" % (ele_xpath, str(values)))
            return values
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_by_id(self, ele_id, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、password、selected，返回的是"true"和"false"的str类型
        2、.get_attribute("name")  返回的是‘content_desc’的值
        3、.get_attribute("className")  返回的是‘class’的值
        """
        aklog_debug("get_attribute_by_id, ele_id: %s, attribute_type: %s"
                    % (ele_id, attribute_type))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, ele_id)))
            value = ele.get_attribute(attribute_type)
            aklog_debug("%s, %s is %s" % (ele_id, attribute_type, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_by_name(self, ele_name, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、
        password、selected，返回的是"true"和"false"的str类型
        2、.get_attribute("name")  返回的是‘content_desc’的值
        3、.get_attribute("className")  返回的是‘class’的值
        """
        aklog_debug("get_attribute_by_name, ele_name: %s, attribute_type: %s"
                    % (ele_name, attribute_type))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.NAME, ele_name)))
            value = ele.get_attribute(attribute_type)
            aklog_debug("%s, %s is %s" % (ele_name, attribute_type, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_by_xpath(self, ele_xpath, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、
        password、selected，返回的是"true"和"false"的str类型
        2、.get_attribute("name")  返回的是‘content_desc’的值
        3、.get_attribute("className")  返回的是‘class’的值
        4、textContent，返回文本内容
        """
        aklog_debug("get_attribute_by_xpath, ele_xpath: %s, attribute_type: %s"
                    % (ele_xpath, attribute_type))
        try:
            ele = WebDriverWait(self.driver, self.wait_time). \
                until(EC.presence_of_element_located((By.XPATH, ele_xpath)))
            if not ele:
                aklog_debug('Error: no found element: %s ' % ele_xpath)
                return None
            value = ele.get_attribute(attribute_type)
            aklog_debug("%s, %s is %s" % (ele_xpath, attribute_type, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_elements_attribute_by_xpath(self, ele_xpath, attribute_type):
        """
        获取所有相同Xpath元素的属性值
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、
        password、selected，返回的是"true"和"false"的str类型
        2、.get_attribute("name")  返回的是‘content_desc’的值
        3、.get_attribute("className")  返回的是‘class’的值
        4、textContent，返回文本内容
        """
        aklog_debug("get_elements_attribute_by_xpath, ele_xpath: %s, attribute_type: %s"
                    % (ele_xpath, attribute_type))
        try:
            elements = WebDriverWait(self.driver, self.wait_time). \
                until(lambda x: x.find_elements(By.XPATH, ele_xpath))
            values = [ele.get_attribute(attribute_type) for ele in elements]
            aklog_debug("%s, %s: %s" % (ele_xpath, attribute_type, str(values)))
            return values
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_by_link_text(self, ele_link, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、
        password、selected，返回的是"true"和"false"的str类型
        2、.get_attribute("name")  返回的是‘content_desc’的值
        3、.get_attribute("className")  返回的是‘class’的值
        """
        aklog_debug("get_attribute_by_link_text, ele_link: %s, attribute_type: %s"
                    % (ele_link, attribute_type))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.LINK_TEXT,
                                                                                                   ele_link)))
            value = ele.get_attribute(attribute_type)
            aklog_debug("%s, %s is %s" % (ele_link, attribute_type, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_placeholder_by_id(self, ele_id):
        """获取输入框为空时默认显示内容"""
        aklog_debug("get_placeholder_by_id : %s" % ele_id)
        try:
            value = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id))).get_attribute('placeholder')
            aklog_debug("%s, placeholder is %s" % (ele_id, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_id_status(self, ele_id):
        return self.get_ele_status_by_id(ele_id)

    def get_xpath_status(self, ele_xpath):
        return self.get_ele_status_by_xpath(ele_xpath)

    def get_name_status(self, ele_name):
        return self.get_ele_status_by_name(ele_name)

    def get_ele_xpath_status(self, ele_xpath):
        return self.get_ele_status_by_xpath(ele_xpath)

    def get_ele_status_by_id(self, ele_id):
        """获取ele_id的状态，True：可点击，False：不可点击状态"""
        aklog_debug("get_ele_status_by_id : %s" % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.ID, ele_id)))
            ret = ele.is_enabled()
            aklog_debug('enable: %s' % ret)
            return ret
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_status_by_name(self, ele_name):
        """获取ele_name的状态，True：可点击，False：不可点击状态"""
        aklog_debug("get_ele_status_by_name : %s" % ele_name)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.NAME, ele_name)))
            ret = ele.is_enabled()
            aklog_debug('enable: %s' % ret)
            return ret
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_status_by_xpath(self, ele_xpath):
        """获取ele_xpath的状态，True：可点击，False：不可点击状态"""
        aklog_debug("get_ele_status_by_xpath : %s" % ele_xpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time). \
                until(EC.presence_of_element_located((By.XPATH, ele_xpath)))
            ret = ele.is_enabled()
            aklog_debug('enable: %s' % ret)
            return ret
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_counts_by_xpath(self, ele_xpath):
        """获取相同Xpath元素的数量"""
        aklog_debug("get_ele_counts_by_xpath : %s" % ele_xpath)
        try:
            eles = self.driver.find_elements(By.XPATH, ele_xpath)
            if eles:
                counts = len(eles)
            else:
                counts = 0
            aklog_debug("%s, counts is %s" % (ele_xpath, counts))
            return counts
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_elements_by_xpath(self, ele_xpath, wait_time=None):
        """获取有相同Xpath的所有元素，返回list"""
        aklog_debug()
        try:
            if wait_time is None:
                wait_time = self.wait_time
            elements = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_all_elements_located((By.XPATH, ele_xpath)))
            aklog_debug('element counts: %s' % len(elements))
            return elements
        except TimeoutException:
            aklog_debug('%s not found' % ele_xpath)
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_element_visible(self, locate_type, ele, print_trace=True, wait_time=None):
        """Type 可以取值：By.XPATH、By.ID、By.CLASS_NAME等"""
        aklog_debug()
        if not wait_time:
            wait_time = self.wait_time
        try:
            element = WebDriverWait(self.driver, wait_time). \
                until(EC.visibility_of_element_located((locate_type, ele)))
            return element
        except TimeoutException:
            aklog_debug('%s not found' % ele)
            return False
        except:
            aklog_debug('not found')
            if print_trace:
                aklog_debug(traceback.format_exc())
            return None

    def adapt_element(self, id_name_xpath, wait_time=None):
        xpath = id_name_xpath if (
                id_name_xpath.startswith('/') or '//' in id_name_xpath) else '//*[@id="%s" or @name="%s"]' % (
            id_name_xpath, id_name_xpath)
        try:
            if wait_time is None:
                wait_time = self.wait_time
            ele = WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.XPATH, xpath)))
            return ele
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_elements_visible(self, locate_type, ele):
        """获取多个元素，Type 可以取值：By.XPATH、By.ID、By.CLASS_NAME等"""
        aklog_debug()
        try:
            element = WebDriverWait(self.driver, self.wait_time). \
                until(EC.visibility_of_any_elements_located((locate_type, ele)))
            return element
        except TimeoutException:
            aklog_debug('%s not found' % ele)
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_size(self, id_name_xpath):
        """获取元素尺寸"""
        aklog_debug('get_ele_size: %s' % id_name_xpath)
        xpath = id_name_xpath if id_name_xpath.startswith('/') else '//*[@id="%s" or @name="%s"]' % (
            id_name_xpath, id_name_xpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, xpath)))
            ele_size = ele.size
            ele_size = (ele_size['width'], ele_size['height'])
            aklog_debug(ele_size)
            return ele_size
        except:
            aklog_debug(traceback.format_exc())
            return None

    # endregion

    # region 判断元素是否存在或可见

    def is_exist_ele_by_xpath(self, ele_xpath, wait_time=None):
        """判断元素是否存在"""
        self.set_implicitly_wait(0)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            aklog_debug('%s is exist...' % ele_xpath)
            self.restore_implicitly_wait()
            return True
        except:
            aklog_debug('%s is not exist!!!' % ele_xpath)
            self.restore_implicitly_wait()
            return False

    def is_exist_and_visible_ele_by_xpath(self, ele_xpath, wait_time=None, printlog=True):
        """判断元素是否存在并可见"""
        self.set_implicitly_wait(0)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            aklog_debug('%s is exist...' % ele_xpath)
            self.restore_implicitly_wait()
            return True
        except:
            if printlog:
                aklog_debug('%s is not exist!!!' % ele_xpath)
            self.restore_implicitly_wait()
            return False

    def is_exist_ele_by_id(self, ele_id, wait_time=None):
        """判断元素是否存在"""
        self.set_implicitly_wait(0)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.ID, ele_id)))
            aklog_debug('%s is exist...' % ele_id)
            self.restore_implicitly_wait()
            return True
        except:
            aklog_debug('%s is not exist!!!' % ele_id)
            # aklog_debug(traceback.format_exc())
            self.restore_implicitly_wait()
            return False

    def is_exist_and_visible_ele_by_id(self, ele_id, wait_time=None):
        """判断元素是否存在并可见"""
        self.set_implicitly_wait(0)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.ID, ele_id)))
            aklog_debug('%s is exist...' % ele_id)
            self.restore_implicitly_wait()
            return True
        except:
            aklog_debug('%s is not exist!!!' % ele_id)
            self.restore_implicitly_wait()
            return False

    def is_ele_gone(self, ele_id, wait_time=None):
        aklog_debug()
        if wait_time is None:
            wait_time = self.wait_time
        self.set_implicitly_wait(0)
        try:
            if ele_id.startswith('/'):
                if '|' in ele_id:
                    xpath1 = './/*['
                    list1 = ele_id.split('|')
                    list1 = [i.strip() for i in list1]
                    for i in list1:
                        xpath1 += '@id="{}" or @name="{}" or text()="{}"'.format(i, i, i)
                        if i != list1[-1]:
                            xpath1 = xpath1 + ' or '
                    xpath1 += ']'
                else:
                    xpath1 = './/*[@id="{}" or @name="{}" or text()="{}"]'.format(ele_id, ele_id, ele_id)
                WebDriverWait(self.driver, wait_time).until(EC.invisibility_of_element_located((By.XPATH, xpath1)))
            else:
                WebDriverWait(self.driver, wait_time).until(EC.invisibility_of_element_located((By.ID, ele_id)))
            self.restore_implicitly_wait()
            return True
        except:
            aklog_debug('%s is exist!' % ele_id)
            self.restore_implicitly_wait()
            return False

    def is_exist_ele_by_name(self, ele_name, wait_time=None):
        """判断元素是否存在"""
        self.set_implicitly_wait(0)
        aklog_debug("is_exist_ele_by_id : %s" % ele_name)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.NAME, ele_name)))
            self.restore_implicitly_wait()
            return True
        except:
            aklog_debug('%s is not exist' % ele_name)
            self.restore_implicitly_wait()
            return False

    def is_exist_and_visible_ele_by_name(self, ele_name, wait_time=None):
        """判断元素是否存在并可见"""
        self.set_implicitly_wait(0)
        aklog_debug("is_exist_and_visible_ele_by_name : %s" % ele_name)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.NAME, ele_name)))
            self.restore_implicitly_wait()
            return True
        except:
            aklog_debug('%s is not exist' % ele_name)
            self.restore_implicitly_wait()
            return False

    def is_exist_ele_by_class_name(self, ele_class, wait_time=None):
        """判断元素是否存在"""
        aklog_debug("is_exist_ele_by_class_name : %s" % ele_class)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, ele_class)))
            return True
        except:
            aklog_debug('%s is not exist' % ele_class)
            return False

    def is_exist_and_visible_ele_by_class_name(self, ele_class, wait_time=None):
        """判断元素是否存在并可见"""
        self.set_implicitly_wait(0)
        aklog_debug("is_exist_and_visible_ele_by_class_name : %s" % ele_class)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.CLASS_NAME,
                                                                                          ele_class)))
            self.restore_implicitly_wait()
            return True
        except:
            aklog_debug('%s is not exist' % ele_class)
            self.restore_implicitly_wait()
            return False

    def is_exist_ele_by_link_text(self, ele_link_text, wait_time=None):
        """判断元素是否存在"""
        aklog_debug("is_exist_ele_by_link_text : %s" % ele_link_text)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.LINK_TEXT,
                                                                                        ele_link_text)))
            return True
        except:
            aklog_debug('%s is not exist' % ele_link_text)
            return False

    def is_exist_and_visible_ele_by_link_text(self, ele_link_text, wait_time=None):
        """判断元素是否存在并可见"""
        aklog_debug("is_exist_and_visible_ele_by_link_text : %s" % ele_link_text)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.LINK_TEXT,
                                                                                          ele_link_text)))
            return True
        except:
            aklog_debug('%s is not exist' % ele_link_text)
            return False

    def is_exist_and_visible_ele_by_id_limit_time(self, ele_id, wait_time=None):
        """判断元素是否存在并可见,若无元素，则自由设置超时时间"""
        aklog_debug("is_exist_and_visible_ele_by_id : %s" % ele_id)
        if wait_time is None:
            wait_time = self.wait_time
        try:
            WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((By.ID, ele_id)))
            return True
        except:
            aklog_debug('%s is not exist' % ele_id)
            return False

    # endregion

    # region select下拉框相关

    def select_option_by_name(self, ele_name, option_text, sec=0.1):
        """下拉框选择选项文本"""
        aklog_debug("select_option_by_name %s : %s" % (ele_name, option_text))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.NAME, ele_name)))
            Select(ele).select_by_visible_text(option_text)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def select_option_by_id(self, ele_id, option_text, sec=0.1):
        """下拉框选择选项文本"""
        aklog_debug("select_option_by_name %s : %s" % (ele_id, option_text))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.ID, ele_id)))
            Select(ele).select_by_visible_text(option_text)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def select_option_value_by_name(self, ele_name, option_value, sec=0.1):
        """下拉框选择选项的Value值"""
        aklog_debug("select_option_value_by_name %s : %s" % (ele_name, option_value))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.NAME, ele_name)))
            Select(ele).select_by_value(str(option_value))
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def select_option_value_by_id(self, ele_id, option_value, sec=0.1):
        """下拉框通过id选择选项的Value值"""
        aklog_debug("select_option_value_by_id %s : %s" % (ele_id, option_value))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.ID, ele_id)))
            Select(ele).select_by_value(option_value)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def select_option_value_by_xpath(self, ele_xpath, option_value, sec=0.1):
        """下拉框选择选项的Value值"""
        aklog_debug("select_option_value_by_xpath %s : %s" % (ele_xpath, option_value))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, ele_xpath)))
            Select(ele).select_by_value(option_value)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def select_option_value_by_css_selector(self, ele_css_selector, option_value, sec=0.1):
        """
        下拉框选择选项的Value值,css_selector在浏览器系统设置会用到
        :param ele_css_selector: 'settings-ui/deep/[id=dropdownMenu]'
        :param option_value: str类型,0,1,2,3,4
        :param sec: 等待时间
        :return:
        """
        aklog_debug("select_option_value_by_css_selector %s : %s" % (
            ele_css_selector, option_value))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ele_css_selector)))
            Select(ele).select_by_value(option_value)
            time.sleep(sec)
            return True
        except:
            aklog_debug('select_option_value_by_css_selector failed, %s' % str(
                traceback.format_exc()))
            return False

    def select_multi_options_value_by_id(self, ele_id, option_values: tuple, sec=0.1):
        """多选下拉框通过id选择选项的Value值"""
        aklog_debug("select_multi_option_value_by_id %s : %s"
                    % (ele_id, option_values))
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.visibility_of_element_located((By.ID, ele_id)))
            select = Select(ele)
            for option_value in option_values:
                select.select_by_value(option_value)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def get_selected_option_by_name(self, ele_name):
        """获取被选中的option"""
        aklog_debug("get_selected_option_by_name %s" % ele_name)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name)))
            selected_option_text = Select(ele).first_selected_option.text
            aklog_debug("%s, selected option is %s" % (ele_name, selected_option_text))
            return selected_option_text
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_selected_option_by_id(self, ele_id):
        """获取被选中的option"""
        aklog_debug("get_selected_option_by_id %s" % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id)))
            selected_option_text = Select(ele).first_selected_option.text
            aklog_debug("%s, selected option is %s" % (ele_id, selected_option_text))
            return selected_option_text
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_multi_selected_options_by_id(self, ele_id):
        """获取多选下拉框所有被选中的options"""
        aklog_debug("get_multi_selected_options_by_id %s" % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id)))
            selected_options = Select(ele).all_selected_options
            selected_option_text_list = []
            for selected_option in selected_options:
                selected_option_text = selected_option.text
                selected_option_text_list.append(selected_option_text)
            aklog_debug("%s, selected options is %s"
                        % (ele_id, selected_option_text_list))
            return selected_option_text_list
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_multi_selected_options_by_name(self, ele_name):
        """获取多选下拉框所有被选中的options"""
        aklog_debug("get_multi_selected_options_by_name %s" % ele_name)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name)))
            selected_options = Select(ele).all_selected_options
            selected_option_text_list = []
            for selected_option in selected_options:
                selected_option_text = selected_option.text
                selected_option_text_list.append(selected_option_text)
            aklog_debug("%s, selected options is %s"
                        % (ele_name, selected_option_text_list))
            return selected_option_text_list
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_selected_option_value_by_name(self, ele_name):
        """获取被选中的option value"""
        aklog_debug("get_selected_option_value_by_name %s" % ele_name)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name)))
            selected_option_value = Select(ele).first_selected_option.get_attribute('value')
            aklog_debug("%s, selected option value is %s"
                        % (ele_name, selected_option_value))
            return selected_option_value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_selected_option_value_by_id(self, ele_id):
        """获取被选中的option value"""
        aklog_debug("get_selected_option_value_by_name %s" % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id)))
            selected_option_value = Select(ele).first_selected_option.get_attribute('value')
            aklog_debug("%s, selected option value is %s"
                        % (ele_id, selected_option_value))
            return selected_option_value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def swipe_down_by_xpath(self, box_xpath, element_xpath, sec=0.1):
        # 在指定区域下滑,box_xpath为指定的框，element_xpath为所要找的元素
        try:
            box_ele = WebDriverWait(self.driver, self.wait_time). \
                until(EC.visibility_of_element_located((By.XPATH, box_xpath)))
            box_ele.click()
            div = WebDriverWait(self.driver, self.wait_time). \
                until(EC.presence_of_element_located((By.XPATH, element_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView();", div)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def select_option_by_xpath(self, box_xpath, element_xpath, sec=0.2, wait_time=None):
        """在指定区域下滑,box_xpath为指定的框，element_xpath为所要找的元素"""
        aklog_debug('select_option_by_xpath, box_xpath: %s, element_xpath: %s'
                    % (box_xpath, element_xpath))
        if wait_time is None:
            wait_time = self.wait_time
        try:
            box_ele = WebDriverWait(self.driver, wait_time). \
                until(EC.visibility_of_element_located((By.XPATH, box_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView();", box_ele)
            box_ele.click()
            time.sleep(0.1)
        except ElementClickInterceptedException:
            try:
                box_ele = WebDriverWait(self.driver, wait_time). \
                    until(EC.visibility_of_element_located((By.XPATH, box_xpath)))
                self.driver.execute_script("arguments[0].click();", box_ele)
                time.sleep(0.1)
            except:
                aklog_debug(str(traceback.format_exc()))
                return False
        except:
            self.screen_shot()
            aklog_debug(' not found element: %s with value: %s' % (box_xpath, element_xpath))
            aklog_debug(str(traceback.format_exc()))
            return False

        try:
            option_ele = WebDriverWait(self.driver, wait_time). \
                until(EC.presence_of_element_located((By.XPATH, element_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView();", option_ele)
            time.sleep(0.2)
            option_ele.click()
            time.sleep(sec)
            return True
        except:
            self.screen_shot()
            aklog_debug(str(traceback.format_exc()))
            return False

    def select_options_by_box_ele(self, box_ele, *elements_xpath, sec=0.2, wait_time=None):
        """在指定区域下滑,box_xpath为指定的框，elements_xpath为所要找的元素，可以传入多个"""
        aklog_debug('select_options_by_box_ele')
        if wait_time is None:
            wait_time = self.wait_time
        try:
            self.driver.execute_script("arguments[0].scrollIntoView();", box_ele)
            box_ele.click()
            time.sleep(0.5)
        except ElementClickInterceptedException:
            try:
                self.driver.execute_script("arguments[0].click();", box_ele)
                time.sleep(0.1)
            except:
                aklog_debug(str(traceback.format_exc()))
                return False
        except:
            self.screen_shot()
            aklog_debug(str(traceback.format_exc()))
            return False

        for element_xpath in elements_xpath:
            try:
                option_ele = WebDriverWait(self.driver, wait_time). \
                    until(EC.presence_of_element_located((By.XPATH, element_xpath)))
                self.driver.execute_script("arguments[0].scrollIntoView();", option_ele)
                time.sleep(0.2)
                option_ele.click()
            except:
                self.screen_shot()
                aklog_debug(str(traceback.format_exc()))
                return False
        time.sleep(sec)
        return True

    def select_multi_option_by_xpath(self, box_xpath, *elements_xpath, sec=0.2):
        """多选下拉框，在指定区域下滑,box_xpath为指定的框，element_xpath为所要找的元素"""
        aklog_debug('select_multi_option_by_xpath, box_xpath: %s, element_xpath: %r'
                    % (box_xpath, elements_xpath))
        if not elements_xpath:
            aklog_debug('勾选的选项为空')
            return False
        try:
            box_ele = WebDriverWait(self.driver, self.wait_time). \
                until(EC.visibility_of_element_located((By.XPATH, box_xpath)))
            box_ele.click()
            time.sleep(0.1)
        except ElementClickInterceptedException:
            try:
                box_ele = WebDriverWait(self.driver, self.wait_time). \
                    until(EC.visibility_of_element_located((By.XPATH, box_xpath)))
                self.driver.execute_script("arguments[0].click();", box_ele)
                time.sleep(0.1)
            except:
                aklog_debug(str(traceback.format_exc()))
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

        for element_xpath in elements_xpath:
            try:
                option_ele = WebDriverWait(self.driver, self.wait_time). \
                    until(EC.presence_of_element_located((By.XPATH, element_xpath)))
                self.driver.execute_script("arguments[0].scrollIntoView();", option_ele)
                time.sleep(0.2)
                option_ele.click()
            except:
                aklog_debug(str(traceback.format_exc()))
                return False
        time.sleep(sec)
        return True

    def get_select_options_list_by_id(self, ele_id):
        """获取下拉框列表"""
        aklog_debug("get_select_options_list_by_id %s" % ele_id)
        options_list = []
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id)))
            options_ele = Select(ele).options
            for option_ele in options_ele:
                option_text = option_ele.text
                options_list.append(option_text)
            return options_list
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_select_options_list_by_xpath(self, ele_xpath):
        """获取下拉框列表"""
        aklog_debug("get_select_options_list_by_xpath %s" % ele_xpath)
        options_list = []
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            options_ele = Select(ele).options
            for option_ele in options_ele:
                option_text = option_ele.text
                options_list.append(option_text)
            return options_list
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_select_options_list_by_name(self, ele_name):
        """获取下拉框列表"""
        aklog_debug("get_select_options_list_by_name %s" % ele_name)
        options_list = []
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name)))
            options_ele = Select(ele).options
            for option_ele in options_ele:
                option_text = option_ele.text
                options_list.append(option_text)
            return options_list
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_select_options_value_list_by_id(self, ele_id):
        """获取下拉框列表"""
        aklog_debug("get_select_options_value_list_by_id %s" % ele_id)
        options_value_list = []
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id)))
            options_ele = Select(ele).options
            for option_ele in options_ele:
                option_value = option_ele.get_attribute('value')
                options_value_list.append(option_value)
            return options_value_list
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_select_options_value_list_by_name(self, ele_name):
        """获取下拉框列表"""
        aklog_debug("get_select_options_value_list_by_name %s" % ele_name)
        options_value_list = []
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name)))
            options_ele = Select(ele).options
            for option_ele in options_ele:
                option_value = option_ele.get_attribute('value')
                options_value_list.append(option_value)
            return options_value_list
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    # endregion

    # region 复选框相关

    def is_checked_box_by_xpath(self, ele_xpath):
        """判断勾选框是否勾选"""
        aklog_debug("is_checked_box_by_xpath : %s" % ele_xpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            status = ele.is_selected()
            aklog_debug("%s, checked status is %s" % (ele_xpath, status))
            return status
        except:
            aklog_debug('%s is not found' % ele_xpath)
            return None

    def is_checked_box_by_name(self, ele_name):
        """判断勾选框是否勾选"""
        aklog_debug("is_checked_box_by_name : %s" % ele_name)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name)))
            status = ele.is_selected()
            aklog_debug("%s, checked status is %s" % (ele_name, status))
            return status
        except:
            aklog_debug('%s is not found' % ele_name)
            return None

    def is_checked_box_by_id(self, ele_id):
        """判断勾选框是否勾选"""
        aklog_debug("is_checked_box_by_id %s" % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id)))
            status = ele.is_selected()
            aklog_debug("%s, checked status is %s" % (ele_id, status))
            return status
        except:
            aklog_debug('%s is not found' % ele_id)
            return None

    def check_box_by_name(self, ele_name, sec=0.1):
        """勾选"""
        aklog_debug("check_box_by_name %s" % ele_name)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name)))
            if not ele.is_selected():
                ele.click()
                time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def check_box_by_id(self, ele_id, sec=0.1):
        """勾选"""
        aklog_debug("check_box_by_id %s" % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id)))
            if not ele.is_selected():
                ele.click()
                time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def check_box_by_xpath(self, ele_xpath, sec=0.1):
        """勾选"""
        aklog_debug("check_box_by_xpath %s" % ele_xpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            if not ele.is_selected():
                self.click_ele(ele)
                time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def check_multi_boxs_by_xpath(self, ele_xpath, sec=0.1):
        """勾选多个相同Xpath的复选框"""
        aklog_debug("check_multi_boxs_by_xpath %s" % ele_xpath)
        try:
            elements = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_all_elements_located((By.XPATH, ele_xpath)))
            for ele in elements:
                if not ele.is_selected():
                    self.click_ele(ele)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def get_check_box_status(self, ele_id):
        return self.driver.find_element(By.ID, ele_id).is_selected()

    def get_check_box_status_by_xpath(self, ele_xpath):
        """通过ele_xpath判断checkbox是否被勾选，True：已勾选，False：未被勾选"""
        aklog_debug("get_check_box_status_by_xpath : %s" % ele_xpath)
        return self.driver.find_element(By.XPATH, ele_xpath).is_selected()

    def uncheck_box_by_name(self, ele_name, sec=0.1):
        """取消勾选"""
        aklog_debug("uncheck_box_by_name %s" % ele_name)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.NAME, ele_name)))
            if ele.is_selected():
                ele.click()
                time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def uncheck_box_by_id(self, ele_id, sec=0.1):
        """取消勾选"""
        aklog_debug("uncheck_box_by_id %s" % ele_id)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, ele_id)))
            if ele.is_selected():
                ele.click()
                time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def uncheck_box_by_xpath(self, ele_xpath, sec=0.1):
        """取消勾选"""
        aklog_debug("uncheck_box_by_xpath %s" % ele_xpath)
        try:
            ele = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.XPATH, ele_xpath)))
            if ele.is_selected():
                ele.click()
                time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 弹窗相关

    def is_exist_alert(self, wait_time=0.5):
        """判断是否存在弹窗"""
        aklog_debug("is_exist_alert")
        if wait_time is None:
            wait_time = self.wait_time
        try:
            alert = WebDriverWait(self.driver, wait_time).until(EC.alert_is_present())
            alert_text = alert.text
            aklog_info('alert text is: %s' % alert_text)
            return True
        except:
            aklog_debug('alert is not exist')
            return False

    def get_alert_text(self, wait_time=0.5):
        aklog_debug("get_alert_text")
        if wait_time is None:
            wait_time = self.wait_time
        try:
            alert = WebDriverWait(self.driver, wait_time).until(EC.alert_is_present())
            alert_text = alert.text
            aklog_info('alert text is: %s' % alert_text)
            return alert_text
        except:
            aklog_debug('get alert text failed')
            return None

    def alert_confirm_accept(self, wait_time=0.5):
        """弹窗确认"""
        aklog_debug("alert_confirm_accept")
        if wait_time is None:
            wait_time = self.wait_time
        try:
            alert = WebDriverWait(self.driver, wait_time).until(EC.alert_is_present())
            alert_text = alert.text
            aklog_info('alert text is: %s' % alert_text)
            alert.accept()
            return True
        except TimeoutException:
            aklog_error('未出alert现弹窗')
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def alert_confirm_cancel(self, wait_time=0.5):
        """弹窗取消"""
        aklog_debug("alert_confirm_cancel")
        if wait_time is None:
            wait_time = self.wait_time
        try:
            alert = WebDriverWait(self.driver, wait_time).until(EC.alert_is_present())
            alert_text = alert.text
            aklog_info('alert text is: %s' % alert_text)
            alert.dismiss()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 网页截图、画面检查

    def screen_shot_as_base64(self):
        """保存网页截图成base64编码，用于嵌入到HTML测试报告"""
        aklog_info('screen_shot_as_base64, the screenshots is shown below: ')
        for i in range(2):
            ret = self.image.screenshots_as_base64()
            if ret:
                return ret
            else:
                # 在系统弹窗的情况下会截图失败, 且调用截图后系统弹窗会自己消失
                continue

    def screen_shot(self):
        """截图,用于调用"""
        img_base64 = self.screen_shot_as_base64()
        if img_base64:
            # self._imgs.append(img_base64)
            param_append_screenshots_imgs(img_base64)
        else:
            # self._imgs.append('')
            param_append_screenshots_imgs('')

    def save_element_image(self, element, image_dir=None, image_name='image', form='png'):
        """保存图片"""
        if not image_dir:
            image_dir = root_path
        self.image.get_screenshot_by_element(element).write_to_file(image_dir, image_name, form)

    def check_image_rgb_by_id(self, ele_id, ratio, fix_rgb):
        """
        检查元素图像某种颜色占比
        :param ele_id:
        :param ratio: 0-1，颜色占比
        :param fix_rgb: 要对比的颜色RGB值，比如黑色：(0, 0, 0, 0),web一般是(0, 0, 0)
        :return:
        """
        aklog_debug('check_image_rgb_by_id')
        if '//' in ele_id:
            element = self.get_element_visible(By.XPATH, ele_id)
        else:
            element = self.get_element_visible(By.ID, ele_id)
        if element is None:
            aklog_debug('%s is not found' % ele_id)
            return None
        if len(fix_rgb) == 4:
            value = self.image.check_screen_color_rgba(element, fix_rgb)
        else:
            value = self.image.check_screen_color(element, fix_rgb)
        aklog_debug('%r color proportion: %s' % (fix_rgb, value))
        if value is None:
            return None
        if value >= ratio:
            return True
        else:
            return False

    def check_image_rgb_by_xpath(self, ele_xpath, ratio, fix_rgb):
        """
        检查元素图像某种颜色占比
        :param ele_xpath:
        :param ratio: 0-1，颜色占比
        :param fix_rgb: 要对比的颜色RGB值，比如黑色：(0, 0, 0, 0),web一般是(0, 0, 0)
        :return:
        """
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

    def screen_shot_as_file(self, image_dir, image_name, form="png"):
        """保存网页截图为文件"""
        aklog_debug('screen_shot_as_file')
        self.image.get_screenshot_as_file().write_to_file(image_dir, image_name, form=form)

    def screen_shot_total_page_as_file(self, image_dir, image_name, form="png", height_limit=None):
        """整个页面截图保存到文件，页面比较长也会一起截图"""
        aklog_debug('screen_shot_total_page_as_file')
        # width = self.driver.execute_script("return "
        #                                    "Math.max(document.body.scrollWidth,"
        #                                    "document.body.offsetWidth,"
        #                                    "document.documentElement.clientWidth,"
        #                                    "document.documentElement.scrollWidth,"
        #                                    "document.documentElement.offsetWidth);")

        height = self.driver.execute_script("return "
                                            "Math.max(document.body.scrollHeight,"
                                            "document.body.offsetHeight,"
                                            "document.documentElement.clientHeight,"
                                            "document.documentElement.scrollHeight,"
                                            "document.documentElement.offsetHeight);")
        if height_limit and height > height_limit:
            height = height_limit
        self.driver.set_window_size(self.web_width, height)
        # aklog_debug(str(self.driver.get_window_size()))
        time.sleep(2)
        self.image.get_screenshot_as_file().write_to_file(image_dir, image_name, form=form)

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

    # endregion


def get_secondary_position():
    """
    config.ini 中指定有头模式下浏览器是否要在第二个屏幕显示.
    browser_in_second_screen = True
    """
    if param_get_browser_headless_enable():
        # headless模式运行, 默认在主屏下运行.
        return False
    if not param_get_browser_in_second_screen():
        return False
    if len(win32api.EnumDisplayMonitors(None, None)) > 1:
        monitors = win32api.EnumDisplayMonitors(None, None)
        screens = []
        for i, monitor in enumerate(monitors):
            info = win32api.GetMonitorInfo(monitor[0])
            screen = {
                "id": i,
                "is_primary": info["Flags"] & win32con.MONITORINFOF_PRIMARY != 0,
                "bounds": info["Monitor"],
                "work_area": info["Work"]
            }
            screens.append(screen)
        secondary = [s for s in screens if not s["is_primary"]]
        return secondary[0].get('bounds')[0], secondary[0].get('bounds')[1]
    return False


if __name__ == '__main__':
    aklog_init_common()
    web = libbrowser()
    web.init()
    web.visit_url('https://czcloud.uat.akubela.com/portal/auth/#/login')
    time.sleep(2)
    web.input_edit_by_xpath('//*[@id="loginLayout"]/div[1]/div[1]/form/div[1]/div/div/input', 'hzs_installer2')
    web.input_edit_by_xpath('//*[@id="loginLayout"]/div[1]/div[1]/form/div[2]/div/div/input', 'p719ff37bc')
    web.click_btn_by_xpath('//*[@id="loginLayout"]/div[1]/div[1]/form/div[4]/div/button')
    time.sleep(1)
    for i in range(3):
        canvas_ele = web.get_element_visible(By.XPATH, '/html/body/div[2]/div/div[1]/canvas[1]')
        if not canvas_ele:
            print('登录成功')
            break
        # web.save_element_image(canvas_ele)
        x = web.image.get_canvas_missing_piece_loc(canvas_ele)
        btn = web.get_element_visible(By.XPATH, '/html/body/div[2]/div/div[2]/div/div[2]/div')
        web.drag_and_drop_by_offset(btn, x, 0)
        time.sleep(2)
        continue

    time.sleep(5)
    web.close_and_quit()
