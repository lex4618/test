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
from testcase.utils.aklibLog import *
import testcase.utils.aklibFile_process as File_process
from testcase.utils.aklibthread import AkThread

import time
import traceback
import re
import subprocess
import threading
import math
import uiautomator2 as u2
from uiautomator2.exceptions import ConnectError, UiObjectNotFoundError, XPathElementNotFoundError
from uiautomator2.xpath import XPathSelector, XMLElement
from uiautomator2 import UiObject
from uiautomator2 import Device
from typing import Union, Optional, List, Tuple


class AndroidBaseU2(object):

    # region 安卓设备连接初始化

    def __init__(self, device_info=None, device_config=None, wait_time=3):
        self._driver: Optional[Device] = None
        self.package_name = None
        self._imgs = []
        self.image: Optional[ImageProcessU2] = None
        self.wait_time = wait_time
        self.device_config: Optional[config_NORMAL] = None
        self._user_info = {}
        self.translations = {}
        self.language = 'en'
        self._device_info = {}
        self.device_name = ''
        self.screen_width = 0
        self.screen_height = 0
        self.screen_clickable_area = None
        self.cur_activity_use_u2 = None
        self._cmds_cache = set()
        self.scrcpy_process = None
        self.record_file = ''
        self.record_start_time = None
        self.video_start_time = None
        self.video_encoding_type = 'h264_qsv'
        self.init(device_info, device_config)

    def init(self, device_info=None, device_config: Optional[config_NORMAL] = None):
        if device_info:
            self._device_info = device_info
            self.device_name = self._device_info.get('device_name', '')
        if device_config:
            self.device_config = device_config
            self.package_name = self.device_config.get_package_name()
            self.screen_width = self.device_config.get_screen_width()
            self.screen_height = self.device_config.get_screen_height()
            self.screen_clickable_area = self.device_config.get_screen_clickable_area()
            if self.device_name and not self.device_config.get_device_name():
                self.device_config.put_device_name(self.device_name)
            if self.cur_activity_use_u2 is None:
                self.cur_activity_use_u2 = self.device_config.get_cur_activity_use_u2()

    @property
    def driver(self) -> Optional[Device]:
        if self._driver is None:
            self.device_connect()
        return self._driver

    @driver.setter
    def driver(self, value: Optional[Device]):
        self._driver = value

    def device_connect(self, force_init=False, fast_input=True):
        aklog_debug(f'{self.device_id} 开始连接')
        if force_init:
            self.__u2_connect_with_adb(is_raise=False)
        print_trace = False
        retry = 3
        for i in range(retry):
            if i == retry - 1:
                print_trace = True
            if self._driver and self.__is_connected(print_trace):
                aklog_debug(f'{self.device_id} U2连接成功')
                self._driver.implicitly_wait(self.wait_time)
                self.image = ImageProcessU2(self._driver, self.device_name)
                self.get_device_language()
                self.set_virtual_keyboard(1)
                self.set_fast_input_ime(fast_input)
                aklog_debug(f'{self.device_id} U2 - device connect 初始化完成')
                return True

            try:
                if i == 0:
                    # 先尝试连接一次
                    self.__u2_connect_with_adb()
                    continue
                elif i == retry - 1:
                    break
                # 第一次连不上，先检查adb连接
                if not self.__check_adb_connect():
                    aklog_error(f'{self.device_id} adb连接失败')
                    return False
                # 有些环境下使用uiautomator2 init安装的应用会导致InvalidVersion错误，先重新启动uiautomator自动安装应用
                aklog_debug('uiautomator服务未启动成功，重新启动uiautomator')
                self.__reset_uiautomator()
                continue
            except ConnectError as e:
                aklog_error(f'{self.device_id} adb连接失败: {e}')
                return False
            except Exception as e:
                if i < retry - 1:
                    aklog_debug(f'{self.device_id} 连接异常，重试: {e}')
                    time.sleep(3)
                    continue
                else:
                    aklog_error(f'{self.device_id} U2连接异常: {e}')
                    aklog_debug(traceback.format_exc())
                    return False
        aklog_error(f'{self.device_id} U2连接失败')
        return False

    def __is_connected(self, print_trace=False):
        """有些情况下adb异常，导致该方法会卡住，改用子线程方式执行，并设置超时时间"""
        aklog_debug()
        ret = False

        def is_connected(print_trace):
            nonlocal ret
            try:
                self.driver.window_size()
                self.driver.dump_hierarchy()
            except Exception as e:
                aklog_debug(e)
                if print_trace or not e:
                    aklog_debug(traceback.format_exc())
                ret = False
            else:
                ret = True

        try:
            thread = AkThread(target=is_connected, args=(print_trace,))
            thread.daemon = True  # 设置主线程结束后也结束子线程
            thread.start()
            thread.join(60)  # 设置主线程要等待子线程结束后才继续执行，并且设置子线程执行超时时间
            return ret
        except:
            aklog_debug(traceback.format_exc())
            return False

    def __uiautomator2_init(self):
        """uiautomator2初始化，U2 3.x+版本可以不用init了"""
        # 先判断adb是否正常，如果异常杀掉adb进程重启，此操作会断开所有设备adb连接
        aklog_debug()
        ret = None
        for j in range(2):
            ret = sub_process_get_output('uiautomator2 -d init -s %s' % self.device_id, timeout=60)
            if ret and 'Successfully init AdbDevice(serial=%s)' % self.device_id in ret:
                aklog_debug('uiautomator2初始化设备成功')
                return True
            elif ret and "adbutils.errors.AdbError: device '%s' not found" % self.device_id in ret:
                aklog_debug('uiautomator2初始化设备失败，可能是设备adb服务没有启动')
                return False
            elif j == 0:
                aklog_debug('uiautomator2初始化设备失败, 卸载uiautomator2应用，重新初始化')
                # 初始化失败时，卸载uiautomator2应用，重新初始化
                sub_process_get_output('uiautomator2 -s %s purge' % self.device_id, timeout=30)
                time.sleep(2)
                continue
        aklog_debug('uiautomator2初始化设备失败: %s' % ret)
        aklog_debug(r'可能是下载相关APK失败了，请检查电脑C盘用户目录(C:\Users\Administrator\.uiautomator2\cache)下是否有'
                    r'app-uiautomator.apk、app-uiautomator-test.apk、atx-agent、minicap、minitouch等文件，'
                    r'如果没有，可以从tools/uiautomator2复制过来，或者让电脑处于翻墙环境再尝试初始化下载(建议用这种方式)')
        return False

    def __u2_connect_with_adb(self, is_raise=True, print_trace=False):
        """uiautomator2连接设备，有可能会因为adb异常导致卡住，改用子线程方式执行，并设置超时时间"""
        ret = False

        def u2_connect_with_adb():
            nonlocal ret
            try:
                self._driver = u2.connect(self.device_id)
            except ConnectError as e:
                raise e
            except Exception as e:
                aklog_debug(e)
                if print_trace or not e:
                    aklog_debug(traceback.format_exc())
                ret = False
            else:
                ret = True

        thread = AkThread(target=u2_connect_with_adb)
        thread.daemon = True  # 设置主线程结束后也结束子线程
        thread.start()
        thread.join(60)  # 设置主线程要等待子线程结束后才继续执行，并且设置子线程执行超时时间
        if is_raise and thread.get_exit_code() != 0:
            raise thread.get_exception()
        aklog_debug(f'u2_connect: {ret}')
        return ret

    def __reset_uiautomator(self):
        aklog_debug()
        for i in range(2):
            try:
                self.driver.reset_uiautomator()
                return True
            except Exception as e:
                aklog_warn(e)
                if e and 'offline' in str(e):
                    return False
                if i == 0:
                    aklog_warn('uiautomator服务还是未启动成功，卸载应用，再次重新启动uiautomator')
                    sub_process_get_output('uiautomator2 -s %s purge' % self.device_id, timeout=30)
                    continue
        return False

    def get_atx_app_overlay_permission(self):
        """获取悬浮窗权限"""
        cmd = 'dumpsys package com.github.uiautomator | grep "android.permission.SYSTEM_ALERT_WINDOW:"'
        out = self.shell(cmd)
        if out and 'granted=true' in out:
            return True
        else:
            aklog_debug('atx app not installed or no overlay permission')
            return False

    def show_float_window(self, show=True):
        aklog_debug()
        """ 显示悬浮窗，提高uiautomator运行的稳定性，但会影响自动息屏，如果要测试息屏屏保功能，要关闭悬浮窗"""
        self.shell('am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER'
                   ' -n com.github.uiautomator/.ToastActivity')
        time.sleep(1)
        self.driver.show_float_window(show)

    def __check_adb_connect(self):
        for i in range(2):
            if self.judge_adb_server_status():
                break
            elif i == 0:
                aklog_debug('adb异常，重启adb.exe')
                cmd_close_process_by_name('adb.exe')
                time.sleep(5)
                continue
            else:
                aklog_debug('adb服务异常')
                return False
        if self.judge_adb_connect_status() or self.connect_adb(1):
            return True
        return False

    @staticmethod
    def judge_adb_server_status():
        """判断电脑adb是否正常"""
        aklog_debug()
        devices = sub_process_get_output('adb devices', timeout=60)
        if devices and 'List of devices attached' in devices:
            return True
        else:
            aklog_debug('adb异常')
            return False

    def connect_adb(self, retry=2):
        """
        连接ADB，自动判断是否需要执行adb root，提升兼容性和健壮性。

        Args:
            retry (int): 重试次数，默认2次。

        Returns:
            bool: 连接成功返回True，否则False。
        """
        aklog_debug()
        if ':' not in self.device_id:
            aklog_debug('USB方式连接，不需要连接adb')
            return True

        command_connect = f'adb connect {self.device_id}'
        command_root = f'adb -s {self.device_id} root'
        command_disconnect = f'adb disconnect {self.device_id}'

        for i in range(retry):
            # 先断开，确保连接状态干净
            sub_process_exec_command(command_disconnect)
            time.sleep(2)
            sub_process_exec_command(command_connect)
            time.sleep(2)

            # 检查/data/data目录权限，判断是否已root
            ret = sub_process_get_output(f'adb -s {self.device_id} shell ls /data/data')
            if ret:
                # 判断设备未连接或未找到
                if 'not found' in ret and 'device' in ret:
                    aklog_warn(f'设备未找到: {ret}')
                    continue
                # 判断GMS设备（如S567G等），不能执行adb root，会导致后续adb命令失败并且连不上
                if 'com.google.android.calendar' in ret:
                    aklog_debug('检测到GMS设备（如S567G），不支持adb root命令')
                # 判断已root（没有Permission denied）
                elif 'Permission denied' not in ret:
                    aklog_debug('设备已root或有足够权限，无需执行adb root')
                # 其他情况，尝试adb root
                else:
                    aklog_debug('尝试执行adb root命令')
                    sub_process_exec_command(command_root)
                    time.sleep(2)
            else:
                # ret为空，可能未连接或响应超时，尝试adb root
                aklog_warn('adb shell ls /data/data无返回，尝试adb root')
                sub_process_exec_command(command_root)
                time.sleep(2)

            # 检查adb连接状态
            if self.judge_adb_connect_status():
                aklog_info('ADB连接成功')
                return True
            else:
                aklog_warn('ADB连接失败，重试中...')
                continue

        aklog_error('ADB连接失败，超过最大重试次数')
        return False

    def judge_adb_connect_status(self):
        aklog_debug()
        adb_devices_command = 'adb devices | findstr "%s"' % self.device_id
        devices = sub_process_get_output(adb_devices_command)
        pattern = r'%s\s+device' % re.escape(self.device_id)
        if devices and re.search(pattern, devices):
            aklog_debug('设备 %s adb连接成功' % self.device_id)
            return True
        else:
            aklog_debug('设备 %s adb连接失败' % self.device_id)
            return False

    def uninstall_uiautomator_apk(self):
        """卸载uiautomator2相关apk：com.github.uiautomator，com.github.uiautomator.test"""
        sub_process_get_output('uiautomator2 -s %s purge' % self.device_id, timeout=30)

    def get_android_version(self):
        return self.shell('getprop ro.build.version.release')

    def get_app_version(self, app_package_name):
        """获取APP的版本号"""
        out = self.shell(f'dumpsys package {app_package_name} | grep versionName')
        if out and '=' in out:
            version = out.split('=')[1].strip()
            aklog_debug(f'{app_package_name} version: {version}')
            return version
        return None

    def get_android_device_ip(self, subnet: str) -> Optional[str]:
        """获取安卓设备ip地址，传入子网: 192.168.88"""
        # 获取设备的所有网络接口信息
        result = self.shell('ip addr show')
        if not result:
            return None
        # 使用正则表达式提取所有IP地址
        ip_addresses = re.findall(r'inet\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)[/,\\]24', result)
        if ip_addresses:
            for ip in ip_addresses:
                if ip.startswith(subnet):
                    aklog_debug(f'ip: {ip}')
                    return ip
        return None

    def get_device_language(self, regain=True):
        """获取设备语言"""
        if not regain:
            return self.language
        cmd = 'getprop persist.sys.locale'
        language = self.shell(cmd)
        if not language or not language.strip():
            aklog_debug(f'获取设备语言失败，使用默认语言：{self.language}')
            return self.language
        if '-' in language:
            language = language.split('-')[0]
        self.language = language
        aklog_debug(f'language: {language}')
        return language

    def get_device_config(self):
        return self.device_config

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
        """使用self.user_info = user_info代替"""
        self._user_info.clear()
        self._user_info.update(user_info)

    def get_user_info(self) -> dict:
        """获取当前语言的词条文件"""
        return self._user_info

    @property
    def user_info(self) -> dict:
        return self._user_info

    @user_info.setter
    def user_info(self, value: dict):
        self._user_info = value

    @property
    def device_info(self) -> dict:
        return self._device_info

    @device_info.setter
    def device_info(self, value: dict):
        self._device_info = value

    def get_device_info(self) -> dict:
        return self._device_info

    @property
    def device_id(self) -> str:
        return self._device_info.get('deviceid')

    @device_id.setter
    def device_id(self, value: dict):
        self._device_info['deviceid'] = value

    def put_device_id(self, device_id):
        self._device_info['deviceid'] = device_id

    def put_cur_activity_use_u2(self, value):
        self.cur_activity_use_u2 = value

    # 截图储存list
    def reset_imgs(self):
        self._imgs = []
        param_reset_screenshots_imgs()

    def get_imgs(self):
        return self._imgs

    # endregion

    # region APK安装卸载

    def app_install(self, app_path):
        """APK安装"""
        aklog_debug()
        try:
            self.driver.app_install(app_path)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def app_uninstall(self, package_name):
        aklog_debug()
        try:
            self.driver.app_uninstall(package_name)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    # endregion

    # region 页面活动相关

    def dump_hierarchy(self):
        """获取页面资源，可用于判断设备是否连接正常，也可以用于判断页面是否滚动到顶部或底部"""
        try:
            if self.driver:
                page_source = self.driver.dump_hierarchy()
                return page_source.replace('\xa0', '')
            else:
                aklog_error('driver not connect')
                return None
        except:
            aklog_debug('dump_hierarchy failed, %s' % traceback.format_exc())
            return None

    def dump_hierarchy_to_xml(self, xml_file):
        """获取页面资源，可用于判断设备是否连接正常，也可以用于判断页面是否滚动到顶部或底部"""
        aklog_debug()
        try:
            dump_hierarchy = self.driver.dump_hierarchy(compressed=True, pretty=True)
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(dump_hierarchy)
            return True
        except:
            aklog_debug('dump_hierarchy_to_xml failed, %s' % traceback.format_exc())
            return False

    def check_dump_hierarchy(self, hierarchy1, hierarchy2, check_package_only=True):
        """
        检查hierarchy是否一致，可以只检查当前package。
        只比较属于当前APP包名的节点内容，忽略systemui等其他package节点的变化。
        Args:
            hierarchy1 (str): 第一次dump的hierarchy字符串。
            hierarchy2 (str): 第二次dump的hierarchy字符串。
            check_package_only (bool): 是否只检查当前package的节点。
        Returns:
            bool: 一致返回True，否则返回False。
        """
        if not hierarchy1 or not hierarchy2:
            return False
        if hierarchy1 == hierarchy2:
            return True
        if not check_package_only or not self.package_name:
            return False

        # 正则提取所有属于当前APP包名的节点（包含属性行）
        pattern = re.compile(r'<[^>]*package="%s"[^>]*>' % re.escape(self.package_name))
        nodes1 = pattern.findall(hierarchy1)
        nodes2 = pattern.findall(hierarchy2)

        if len(nodes1) != len(nodes2):
            # aklog_debug(f'当前包名节点数量不同: {len(nodes1)} vs {len(nodes2)}')
            return False

        for idx, (n1, n2) in enumerate(zip(nodes1, nodes2)):
            if n1 != n2:
                # aklog_debug(f'第{idx + 1}个当前包名节点内容不一致\nnode1: {n1}\nnode2: {n2}')
                return False
        return True

    def wait_for_page_change(self, old_page_source, timeout=5, interval=0.5):
        """
        等待页面发生变化
        :param old_page_source: 点击前的页面结构
        :param timeout: 等待超时时间
        :param interval: 等待间隔时间
        :return: 如果页面变化返回 True，否则返回 False
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            new_page_source = self.driver.dump_hierarchy()
            if not self.check_dump_hierarchy(new_page_source, old_page_source):
                time.sleep(interval)
                return True  # 页面发生变化
            time.sleep(interval)
        return False  # 页面未发生变化

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

    def get_current_activity(self, print_activity=True):
        """有些安卓设备无法使用U2自带的app_current()方法获取activity，得用dumpsys activity"""
        if self.cur_activity_use_u2:
            try:
                activity_info = self.driver.app_current()
            except Exception as e:
                aklog_warn(e)
                return None
            current_package = activity_info.get('package')
            current_activity = activity_info.get('activity')
            if current_activity.startswith(current_package):
                current_activity = current_activity.replace(current_package, '')
            if print_activity:
                if hasattr(self, 'activity_dict') and self.activity_dict.get(current_activity):
                    aklog_debug(f'设备当前在界面: {self.activity_dict.get(current_activity)} ,'
                                f' activity: {current_activity}')
                else:
                    aklog_debug('current activity: %s' % current_activity)
            return current_activity
        else:
            get_current_activity_command = 'adb -s %s shell dumpsys activity | findstr "%s"' \
                                           % (self.device_id, self.device_config.get_current_activity_flag())
            for i in range(3):
                activity_info = sub_process_get_output(get_current_activity_command)
                if activity_info and '/' in activity_info:
                    current_activity = activity_info.split('/')[1].split(' ')[0]
                    if print_activity:
                        if hasattr(self, 'activity_dict') and self.activity_dict.get(current_activity):
                            aklog_debug(f'设备当前在界面: {self.activity_dict.get(current_activity)} ,'
                                        f' activity: {current_activity}')
                        else:
                            aklog_debug('current activity: %s' % current_activity)
                    return current_activity
                elif i <= 1:
                    aklog_debug('get current activity failed, remove screen saver and try again')
                    self.remove_screen_saver()
                    time.sleep(2)
                    continue
            aklog_debug('get current activity failed')
            return None

    def get_current_activity_with_package(self):
        """有些安卓设备无法使用U2自带的app_current()方法获取activity，得用dumpsys activity"""
        if self.cur_activity_use_u2:
            activity_info = self.driver.app_current()
            # current_package = activity_info.get('package')
            current_activity = activity_info.get('activity')
            # if current_activity.startswith(current_package):
            #     current_activity = current_activity.replace(current_package, '')
            if hasattr(self, 'activity_dict') and self.activity_dict.get(current_activity):
                aklog_debug(f'设备当前在界面: {self.activity_dict.get(current_activity)} ,'
                            f' activity: {current_activity}')
            else:
                aklog_debug('current activity: %s' % current_activity)
            return current_activity
        else:
            get_current_activity_command = 'adb -s %s shell dumpsys activity | findstr "%s"' \
                                           % (self.device_id, self.device_config.get_current_activity_flag())
            for i in range(3):
                activity_info = sub_process_get_output(get_current_activity_command)
                if activity_info and '/' in activity_info:
                    current_activity = activity_info.split('/')[1].split(' ')[0]
                    if hasattr(self, 'activity_dict') and self.activity_dict.get(current_activity):
                        aklog_debug(f'设备当前在界面: {self.activity_dict.get(current_activity)} ,'
                                    f' activity: {current_activity}')
                    else:
                        aklog_debug('current activity: %s' % current_activity)
                    return current_activity
                elif i <= 1:
                    aklog_debug('get current activity failed, remove screen saver and try again')
                    self.remove_screen_saver()
                    time.sleep(2)
                    continue
            aklog_debug('get current activity failed')
            return None

    def is_correct_activity(self, app_activity):
        aklog_debug()
        if self.get_current_activity() == app_activity:
            aklog_debug('current activity is correct')
            return True
        else:
            aklog_debug('current activity is error')
            return False

    def start_app_activity_ignore_error(self, app_package, app_activity):
        aklog_debug()
        try:
            self.driver.app_start(app_package, app_activity)
            return True
        except:
            aklog_debug('打开 %s/%s 失败, %s' % (
                app_package, app_activity, str(traceback.format_exc())))
            return False

    def start_app_activity(self, app_package, app_activity, timeout=5):
        aklog_debug('start_app_activity app_package: %s, app_activity: %s' % (
            app_package, app_activity))
        try:
            self.driver.app_start(app_package, app_activity)
            if self.driver.wait_activity(app_activity, timeout):
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

    def wait_activity(self, app_activity, timeout=5, interval=0.5, sec=0):
        """等待进入页面，间隔interval时间检查一次，超时时间为timeout"""
        aklog_debug()
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.get_current_activity(print_activity=False) == app_activity:
                aklog_debug('enter %s success' % app_activity)
                time.sleep(sec)
                return True
            else:
                time.sleep(interval)
                continue
        self.get_current_activity()
        aklog_warn('wait enter %s failed' % app_activity)
        return False

    def wait_activity_leave(self, app_activity, timeout=5, interval=0.5, sec=0):
        """
        等待页面切换，间隔interval时间检查一次，超时时间为timeout
        :param app_activity: 原来的页面活动名称
        :param timeout: 等待超时时间
        :param interval: 等待间隔时间
        :param sec: 页面切换后继续等待时间
        :return:
        """
        aklog_debug()
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.get_current_activity(print_activity=False) != app_activity:
                aklog_debug('leave %s success' % app_activity)
                time.sleep(sec)
                return True
            else:
                time.sleep(interval)
                continue
        aklog_warn('wait leave %s failed' % app_activity)
        return False

    def get_page_source(self):
        """获取页面资源，可用于判断设备是否连接正常"""
        aklog_debug()
        try:
            if self.driver:
                page_source = self.driver.dump_hierarchy()
                return page_source.replace('\xa0', '')
            else:
                aklog_error('driver not connect')
                return None
        except:
            aklog_warn('get_page_source failed, %s' % traceback.format_exc())
            return None

    # endregion

    # region 导入导出文件, adb shell执行命令

    def push(self, src, dst):
        """将本地文件推送到设备上"""
        aklog_debug()
        self.driver.push(src, dst)

    def pull(self, src, dst):
        """将设备上的文件导出到本地"""
        aklog_debug()
        self.driver.pull(src, dst)

    def adb_set_logcat_cache(self, size='2M', *processes):
        """设置logcat缓冲区大小"""
        aklog_debug()
        if processes:
            for process in processes:
                cmd = f'logcat -b {process} -G {size}'
                self.shell(cmd)
        else:
            self.shell(f'logcat -G {size}')

    def adb_logcat_log(self, file=None):
        command = f'adb -s {self.device_id} logcat -d -v time'
        if file:
            command += f' > {file}'
        return sub_process_get_output(command)

    def adb_exec_cmd_result(self, cmd):
        """adb执行命令"""
        command = 'adb -s %s %s' % (self.device_id, cmd)
        return sub_process_get_output(command)

    def adb_exec_cmd(self, cmd, timeout=10):
        """adb执行命令"""
        command = 'adb -s %s %s' % (self.device_id, cmd)
        return sub_process_exec_command(command, timeout=timeout)

    def adb_connect_wifi(self, wifi_name, password=None, timeout=30):  # 原生谷歌手机可用
        aklog_debug()
        if password:
            cmd = 'cmd wifi connect-network %s wpa2 %s' % (wifi_name, password)
        else:
            cmd = 'cmd wifi connect-network %s open' % wifi_name
        self.shell(cmd)
        time.sleep(3)
        end_time = time.time() + timeout
        while time.time() < end_time:
            cur_wifi_name = self.adb_get_cur_connected_wifi()
            if cur_wifi_name and cur_wifi_name == wifi_name:
                return True
            time.sleep(2)
            continue
        aklog_debug(f'connect wifi fail')
        return False

    def adb_get_cur_connected_wifi(self):
        cmd = 'cmd wifi status'
        ret = self.shell(cmd)
        match = re.search(r'Wifi is connected to "(.*)"', ret)
        if match:
            wifi_name = match.group(1)
            aklog_debug(wifi_name)
            return wifi_name
        return None

    def adb_is_exist_wifi(self, wifi_name):
        """检查当前网络下wifi地址是否存在"""
        aklog_debug()
        command = self.shell('cmd wifi list-scan-results | findstr "%s"' % wifi_name)
        aklog_debug(command)
        if command:
            aklog_debug('当前网络下Wifi存在')
            return True
        else:
            aklog_warn('当前网络下Wifi不存在')
            return False

    def adb_open_wifi(self):
        """adb打开wifi"""
        aklog_debug()
        cmds = ['cmd wifi set-wifi-enabled enabled',
                'svc wifi enable']
        self.exec_shell_from_cmds(cmds)

    def adb_close_wifi(self):
        """adb关闭wifi"""
        aklog_debug()
        cmds = ['cmd wifi set-wifi-enabled disabled',
                'svc wifi disable']
        self.exec_shell_from_cmds(cmds)

    def shell(self, cmdargs, timeout=60):
        aklog_debug()
        output = self.driver.adb_device.shell(cmdargs, timeout=timeout)
        return output

    def exec_shell_from_cmds(self, cmds: list, timeout=60, empty_ok=True) -> Optional[str]:
        """shell方式执行命令，不同机型相同操作执行的命令不一致，可以传入多个命令"""
        # 参数校验，避免空命令列表导致无意义的执行
        if not cmds:
            aklog_warn("传入的命令列表为空，未执行任何命令")
            return None

        # 初始化命令缓存，确保属性存在且为set类型
        if not hasattr(self, '_cmds_cache') or not isinstance(self._cmds_cache, set):
            self._cmds_cache = set()

        # 记录已尝试命令，避免重复执行
        tried_cmds = set()

        # 合并两段逻辑，优先尝试缓存命令，再尝试未缓存命令
        for cmd in cmds:
            if cmd in tried_cmds:
                continue  # 跳过已尝试命令
            tried_cmds.add(cmd)

            try:
                out = self.shell(cmd, timeout)  # 执行命令
            except Exception as e:
                aklog_error(f"执行命令异常: {cmd}, 异常信息: {e}")
                continue  # 异常时尝试下一个命令

            # 判断命令执行是否成功
            if self._is_cmd_exec_success(out, empty_ok):
                aklog_debug(f"命令执行成功: {cmd}")
                self._cmds_cache.add(cmd)  # 缓存可用命令
                return out  # 返回第一个成功的命令输出
            else:
                aklog_debug(f"命令无效或无权限: {cmd}, 输出: {out}")

        # 所有命令均失败，输出错误日志
        aklog_error(f"所有命令均失败，尝试命令: {cmds}")
        return None  # 明确返回None，语义更清晰

    @staticmethod
    def _is_cmd_exec_success(output, empty_ok=True):
        """
        判断命令是否执行成功
        Args:
            output (str): 命令输出
            empty_ok (bool): 输出为空也代表执行成功
        Returns:
            bool: True-成功，False-失败
        """
        # 常见失败关键字
        fail_keywords = [
            "Unknown command",
            "not have access",
            "SecurityException",
            "Exception",
            "error",
            "failed",
            "not found",
            "No such file or directory"
        ]
        # 若输出为空，通常表示命令执行成功（部分命令无输出）
        if not output or output.strip() == "":
            if empty_ok:
                return True
            else:
                return False
        # 若输出包含失败关键字，则判定为失败
        for keyword in fail_keywords:
            if keyword.lower() in output.lower():
                return False
        # 其他情况默认成功（可根据实际场景补充）
        return True

    # endregion

    # region 屏幕录制操作

    def start_record(self, record_file):
        """开启录制视频保存到文件"""
        aklog_debug()
        try:
            self.video_start_time = None
            self.record_start_time = None
            record_dir = os.path.dirname(record_file)
            os.makedirs(record_dir, exist_ok=True)
            self.record_file = record_file

            cmd = (f'scrcpy -s {self.device_id} '
                   f'--record {record_file} '
                   f'--no-audio '
                   f'--no-window')

            if self.scrcpy_process is not None:
                self.stop_record()

            self.scrcpy_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)

            def log_reader():
                for line in iter(self.scrcpy_process.stdout.readline, ''):
                    # aklog_debug(line.strip())
                    if "Recording started" in line and not self.record_start_time:
                        self.record_start_time = time.time()
                        aklog_debug(f"Recording started at {self.record_start_time}")
                aklog_debug('Record stopped')

            # 启动线程读取日志
            log_thread = threading.Thread(target=log_reader, daemon=True)
            log_thread.start()

            # 等待打印Recording started
            end_time = time.time() + 5
            while time.time() < end_time:
                if self.record_start_time:
                    break
                time.sleep(0.05)

            return True
        except Exception as e:
            aklog_error(f"Failed to start recording: {e}")
            if not e:
                aklog_debug(traceback.format_exc())
            self.scrcpy_process = None
            return False

    def stop_record(self, record_duration=None):
        """停止录制"""
        aklog_debug()
        try:
            if self.scrcpy_process is not None:
                # 等待录制时间
                if record_duration and self.video_start_time and self.record_start_time:
                    if self.video_start_time > self.record_start_time:
                        start_time = self.video_start_time
                    else:
                        start_time = self.record_start_time
                    if start_time:
                        remaining_time = record_duration - (time.time() - start_time)
                        if remaining_time > 0:
                            time_sleep(round(remaining_time, 3))
                # 检查进程是否仍在运行
                if self.scrcpy_process.poll() is None:
                    self._terminate_process_tree(
                        self.scrcpy_process.pid, ['adb.exe', 'scrcpy.exe'])
                else:
                    aklog_debug("Scrcpy process is not running.")
            else:
                aklog_debug("No scrcpy process to stop.")
            return True
        except Exception as e:
            aklog_warn(f"Failed to stop recording: {e}")
            return False
        finally:
            self.scrcpy_process = None

    @staticmethod
    def _terminate_process_tree(pid, process_order=None):
        """递归终止进程及其子进程"""
        try:
            parent = psutil.Process(pid)

            # 如果没有指定顺序，则按默认顺序终止
            if process_order is None:
                process_order = []

            # 按指定顺序终止子进程
            for process_name in process_order:
                children = parent.children(recursive=True)
                for child in children:
                    if child.name() == process_name:
                        aklog_debug(f"Terminating child process: {child.name()}, {child.pid}")
                        child.terminate()
                        # 等待进程终止
                        _, alive = psutil.wait_procs([child], timeout=5)
                        for p in alive:
                            aklog_debug(f"Killing process: {p.pid}")
                            p.kill()
                        break
                time.sleep(1)

            # 终止剩余的子进程
            children = parent.children(recursive=True)
            for child in children:
                aklog_debug(f"Terminating child process: {child.name()}, {child.pid}")
                child.terminate()

            # 终止父进程
            parent.terminate()

            # 等待进程终止
            _, alive = psutil.wait_procs([parent] + children, timeout=5)
            for p in alive:
                aklog_debug(f"Killing process: {p.pid}")
                p.kill()
        except psutil.NoSuchProcess:
            aklog_debug(f"Process {pid} does not exist.")
        except Exception as e:
            aklog_error(f"Failed to terminate process tree for PID {pid}: {e}")

    def set_video_start_time(self):
        self.video_start_time = time.time()
        aklog_debug(f"Video started at {self.video_start_time}")

    def cut_record_video(self, image_bounds=None, offset=0.0):
        """
        提供有效画面的坐标尺寸，剪切视频
        Args:
            image_bounds (tuple): 画面窗口的坐标尺寸：lx, ly, rx, ry
            offset (float): 负数，一般会在找到视频窗口元素的时间作为视频开始时间，但视频画面可能已经开始了0.x秒，需要加一些偏移
        """
        aklog_debug()
        try:
            if (not image_bounds or all(not x for x in image_bounds)) and not self.video_start_time:
                aklog_warn('bounds为空，并且视频开始时间为空，不进行剪切')
                return self.record_file

            # 构建 ffmpeg 命令
            cmd = f'ffmpeg -i "{self.record_file}" '

            # 提前开启录制，然后根据视频开始时间计算剪切开始时间
            if self.video_start_time and self.video_start_time - self.record_start_time > 0:
                start_offset = self.video_start_time - self.record_start_time + offset
                cmd += f'-ss {start_offset} '

            if image_bounds:
                lx, ly, rx, ry = image_bounds
                width = rx - lx
                height = ry - ly
                cmd += f'-vf "crop={width}:{height}:{lx}:{ly}" '

            # 设置剪切视频质量和效率
            cmd += f'-c:v {self.video_encoding_type} -preset fast '

            output_file = self.record_file.replace('.mp4', '--cut.mp4')
            cmd += f'"{output_file}"'

            # 执行剪切命令
            for i in range(2):
                cmd_ret = sub_process_exec_command(cmd, timeout=60)
                if cmd_ret and os.path.exists(output_file) and os.path.getsize(output_file) > 1024:
                    break
                else:
                    aklog_debug('视频剪切失败, 关闭硬件加速重新剪切')
                    cmd = cmd.replace(self.video_encoding_type, 'libx264')
                    self.video_encoding_type = 'libx264'
                    File_process.remove_file(output_file)

            File_process.rename_file(output_file, self.record_file)

        except subprocess.CalledProcessError as e:
            aklog_error(f"Failed to cut video: {e}")
        except Exception as e:
            aklog_error(f"An error occurred while cutting video: {e}")

        return self.record_file

    # endregion

    # region 屏幕相关操作

    def set_battery_unplug(self):
        """设置手机处于非充电状态"""
        self.shell('dumpsys battery unplug')

    def reset_battery(self):
        """恢复手机充电状态"""
        self.shell('dumpsys battery reset')

    def set_device_force_idle(self):
        """设置手机进入空闲状态"""
        self.shell('dumpsys deviceidle force-idle')

    def reset_device_exit_idle(self):
        """重置手机退出idle状态"""
        self.shell('dumpsys deviceidle unforce')

    def get_screen_power_status(self):
        if self.device_config.get_screen_power_use_u2():
            try:
                screen_power_status = self.driver.info.get('screenOn')
                aklog_debug('screen_power_status: %s' % screen_power_status)
                return screen_power_status
            except:
                aklog_debug(traceback.format_exc())
                return None
        else:
            return self.get_screen_lit_up_status()

    def screen_on(self):
        self.driver.screen_on()

    def screen_off(self):
        self.driver.screen_off()

    def get_wake_lock_state(self):
        """获取屏幕锁住常亮状态"""
        aklog_debug()
        out = self.shell('dumpsys power | grep "Wake Locks"')
        if out:
            if 'size=0' in out:
                return False
            else:
                return True
        return None

    def get_screen_saver_status(self):
        """获取屏保状态"""
        screen_saver_flag = self.device_config.get_screen_saver_flag()
        command = 'adb -s %s shell dumpsys window policy | findstr "%s"' \
                  % (self.device_id, screen_saver_flag)

        screen_saver_status = sub_process_get_output(command, 10)
        if (not screen_saver_status or not screen_saver_status.strip()
                or 'not found' in screen_saver_status or 'error' in screen_saver_status):
            aklog_debug('get_screen_saver_status failed')
            return None
        screen_saver_status = screen_saver_status.strip()
        if ' ' in screen_saver_status:
            screen_saver_status = str_get_content_between_two_characters(
                screen_saver_status, '%s=' % screen_saver_flag, ' ')
        elif '=' in screen_saver_status:
            screen_saver_status = screen_saver_status.split('=')[1]
        screen_saver_status = screen_saver_status.strip()

        if screen_saver_status == 'true' or screen_saver_status == 'SCREEN_STATE_ON':
            screen_saver_status = True
            aklog_debug('screen_saver_status: %s' % screen_saver_status)
        elif screen_saver_status == 'false' or screen_saver_status == 'SCREEN_STATE_OFF':
            screen_saver_status = False
            aklog_debug('screen_saver_status: %s' % screen_saver_status)

        return screen_saver_status

    def get_screen_lit_up_status(self):
        """ 获取屏幕是否亮屏的状态 """
        screen_power_flag = self.device_config.get_screen_power_flag()
        if screen_power_flag == 'mWakefulness=':
            command = 'adb -s %s shell dumpsys power | findstr /C:"%s"' % (self.device_id, screen_power_flag)
            screen_status = sub_process_get_output(command, 10)
            if not screen_status or not screen_status.strip():
                aklog_debug('get_screen_saver_status failed')
                screen_status = None
            if 'Awake' in screen_status:
                screen_status = True
                aklog_debug('screen_status: %s' % screen_status)
            elif 'Asleep' in screen_status:
                screen_status = False
                aklog_debug('screen_status: %s' % screen_status)
            return screen_status
        else:
            command = 'adb -s %s shell dumpsys power | findstr /C:"Display Power"' % self.device_id
            screen_status = sub_process_get_output(command, 10)
            if not screen_status or not screen_status.strip():
                aklog_debug('get_screen_saver_status failed')
                screen_status = None
            if screen_status == 'Display Power: state=ON':
                screen_status = True
                aklog_debug('screen_status: %s' % screen_status)
            elif screen_status == 'Display Power: state=OFF':
                screen_status = False
                aklog_debug('screen_status: %s' % screen_status)
            return screen_status

    def remove_screen_saver(self):
        """adb命令解除屏保状态"""
        aklog_debug('remove_screen_saver')
        # 屏幕睡眠状态没有亮屏也没有屏保，先点亮屏幕
        for i in range(2):
            screen_power_status = self.get_screen_power_status()
            if screen_power_status is None:
                return False
            elif not screen_power_status:
                if i == 0:
                    self.screen_on()
                    time.sleep(1)
                    continue
                else:
                    aklog_debug('screen power on failed')
                    break
            else:
                aklog_debug('screen power on success')
                break

        if self.screen_clickable_area:
            tap_location_command = 'adb -s %s shell input tap %s %s' % (
                self.device_id, self.screen_clickable_area[0] + 1, self.screen_clickable_area[1] + 1)
        else:
            tap_location_command = 'adb -s %s shell input tap 1 1' % self.device_id
        # 屏幕已亮起，但处于屏保状态
        for i in range(3):
            screen_saver_status = self.get_screen_saver_status()
            if screen_saver_status is None:
                return False
            elif not screen_saver_status:
                aklog_debug('remove screen saver success')
                return True
            # 处于屏保状态时按下HOME键即可解除屏保状态，也可以模拟点击方式解除屏保
            if i == 0:
                sub_process_exec_command(tap_location_command)
                time.sleep(1)
                continue
            if i == 1:
                # 处于屏保状态时按下HOME键即可解除屏保状态
                self.press_key_home()
                time.sleep(1)
                continue
        aklog_debug('remove screen saver failed')
        return False

    # endregion

    # region 实体按键操作

    def press_key(self, key_code, sec=1):
        aklog_debug('press_key %s' % key_code)
        try:
            self.driver.press(key_code)
            time.sleep(sec)
            return True
        except:
            aklog_debug('press_key %s failed' % key_code)
            return False

    def press_key_home(self, sec=1):
        aklog_debug()
        try:
            self.driver.press('home')
            time.sleep(sec)
            return True
        except:
            aklog_debug('press_key_home failed')
            return False

    def press_key_back(self, sec=1):
        aklog_debug()
        try:
            self.driver.press('back')
            time.sleep(sec)
            return True
        except:
            aklog_debug('press_key_back failed')
            return False

    def press_key_power(self, sec=1):
        aklog_debug()
        try:
            self.driver.press('power')
            time.sleep(sec)
            return True
        except:
            aklog_debug('press_key_power failed')
            return False

    # endregion

    # region 元素定位，是否可见或消失

    def find_element(self, locator: dict or str or tuple, get_lxml=False, timeout=None,
                     print_trace=False, is_raise=False) -> Union[UiObject, XPathSelector, XMLElement, None]:
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

        get_lxml: locator为xpath方式时才会用到，返回XMLElement类，主要用于获取Xpath元素的属性信息
        timeout: 等待元素出现的超时时间
        """
        try:
            if timeout is None:
                timeout = self.wait_time

            if isinstance(locator, dict):
                ele = self.driver(**locator)
                if ele.wait(timeout=timeout):
                    return ele  # 返回UiObject对象
            elif isinstance(locator, tuple):
                # 如果locator是元组类型，则表示多个id或者name（or关系）同时查找，要转换成xpath
                xpath = self.xpath_adapter(*locator)
                ele = self.driver.xpath(xpath)  # 返回XPathSelector对象
                wait_ret = ele.wait(timeout=timeout)
                if wait_ret is not None and wait_ret is not False:
                    if get_lxml:
                        ele = ele.get()  # 返回XMLElement对象
                    return ele
            elif isinstance(locator, str) and (locator.startswith('//') or locator.startswith('(//')
                                               or (locator.startswith('/') and 'android.widget' in locator)):
                # //开头表示xpath方式
                ele = self.driver.xpath(locator)  # 返回XPathSelector对象
                wait_ret = ele.wait(timeout=timeout)
                if wait_ret is not None and wait_ret is not False:
                    if get_lxml:
                        ele = ele.get()  # 返回XMLElement对象
                    return ele
            else:
                if ':id/' in locator:
                    # 直接传入元素id来定位
                    ele = self.driver(resourceId=locator)
                else:
                    # 直接传入元素text(name)来定位
                    ele = self.driver(text=locator)

                if ele.wait(timeout=timeout):
                    return ele  # 返回UiObject对象

            aklog_debug('%s is not found' % locator)
            if is_raise:
                if (isinstance(locator, tuple)
                        or (isinstance(locator, str)
                            and (locator.startswith('//') or locator.startswith('(//')
                                 or (locator.startswith('/') and 'android.widget' in locator)))):
                    raise XPathElementNotFoundError('%s is not found' % locator)
                else:
                    raise UiObjectNotFoundError('%s is not found' % locator)
            return None
        except Exception as e:
            aklog_error(e)
            if print_trace or not e:
                aklog_debug(traceback.format_exc())
            if is_raise:
                raise e
            return None

    def get_element(self, locator, timeout=None, get_lxml=True, is_raise=False) -> Union[UiObject, XMLElement, None]:
        """
        获取元素
        locator如果为xpath方式，返回XMLElement类，主要用于获取Xpath元素的属性信息
        """
        return self.find_element(locator, get_lxml=get_lxml, timeout=timeout, is_raise=is_raise)

    def get_elements(self, locator, timeout=None) -> List[Union[UiObject, XMLElement]]:
        """
        获取元素列表
        locator如果为xpath方式，返回XMLElement类，主要用于获取Xpath元素的属性信息
        """
        ele = self.find_element(locator, get_lxml=False, timeout=timeout)
        if ele is None:
            return []
        if isinstance(locator, dict):
            elements = []
            for i in range(ele.count):
                elements.append(ele[i])
            return elements
        else:
            if (locator.startswith('//') or locator.startswith('(//')
                    or (locator.startswith('/') and 'android.widget' in locator)):
                elements = ele.all()
            else:
                elements = []
                for i in range(ele.count):
                    elements.append(ele[i])
            return elements

    def wait_visible(self, locator, timeout=5, is_raise=False) -> bool:
        """等待元素出现"""
        aklog_debug()
        ele = self.find_element(locator, timeout=timeout, is_raise=is_raise)
        if ele is None:
            return False
        else:
            return True

    def wait_gone(self, locator, timeout=5, is_raise=False) -> bool:
        """等待元素消失"""
        aklog_debug()
        try:
            if isinstance(locator, dict):
                ret = self.driver(**locator).wait_gone(timeout=timeout)
            elif isinstance(locator, tuple):
                # 如果locator是元组类型，则表示多个id或者name（or关系）同时查找，要转换成xpath
                xpath = self.xpath_adapter(*locator)
                ret = self.driver.xpath(xpath).wait_gone(timeout=timeout)
            elif isinstance(locator, str) and (locator.startswith('//') or locator.startswith('(//')
                                               or (locator.startswith('/') and 'android.widget' in locator)):
                # //开头表示xpath方式
                ret = self.driver.xpath(locator).wait_gone(timeout=timeout)
            else:
                if ':id/' in locator:
                    # 直接传入元素id来定位
                    ret = self.driver(resourceId=locator).wait_gone(timeout=timeout)
                else:
                    # 直接传入元素text(name)来定位
                    ret = self.driver(text=locator).wait_gone(timeout=timeout)

            if not ret:
                aklog_debug('%s is not gone' % locator)
            return ret
        except Exception as e:
            aklog_error(e)
            if is_raise:
                raise e
            return False

    def is_exist(self, locator, timeout=3, is_raise=False) -> bool:
        """
        判断元素是否存在, 有等待. 和aklibAndroidbase中的同名.
        """
        aklog_debug()
        try:
            if isinstance(locator, dict):
                ele = self.driver(**locator)
            elif isinstance(locator, tuple):
                # 如果locator是元组类型，则表示多个id或者name（or关系）同时查找，要转换成xpath
                xpath = self.xpath_adapter(*locator)
                ele = self.driver.xpath(xpath)
            elif isinstance(locator, str) and (locator.startswith('//') or locator.startswith('(//')
                                               or (locator.startswith('/') and 'android.widget' in locator)):
                # //开头表示xpath方式
                ele = self.driver.xpath(locator)  # 返回XPathSelector对象
            else:
                if ':id/' in locator:
                    # 直接传入元素id来定位
                    ele = self.driver(resourceId=locator)
                else:
                    # 直接传入元素text(name)来定位
                    ele = self.driver(text=locator)
            ret = ele.wait(timeout=timeout)
            if not ret:
                aklog_debug(f'{locator} not found')
                # 2024.12.2 直接返回ret的话, 后面界面控件变化, ret也会跟着变化. 故直接返回True, False.
                return False
            return True
        except Exception as e:
            aklog_error(e)
            if is_raise:
                raise e
            return False

    def is_exists(self, locator, is_raise=False) -> bool:
        """判断元素是否存在，不进行等待"""
        aklog_debug()
        try:
            if isinstance(locator, dict):
                ele = self.driver(**locator)
            elif isinstance(locator, tuple):
                # 如果locator是元组类型，则表示多个id或者name（or关系）同时查找，要转换成xpath
                xpath = self.xpath_adapter(*locator)
                ele = self.driver.xpath(xpath)
            elif isinstance(locator, str) and (locator.startswith('//') or locator.startswith('(//')
                                               or (locator.startswith('/') and 'android.widget' in locator)):
                # //开头表示xpath方式
                ele = self.driver.xpath(locator)  # 返回XPathSelector对象
            else:
                if ':id/' in locator:
                    # 直接传入元素id来定位
                    ele = self.driver(resourceId=locator)
                else:
                    # 直接传入元素text(name)来定位
                    ele = self.driver(text=locator)

            ret = ele.exists
            if not ret:
                aklog_debug(f'{locator} not found')
                # 2024.12.2 直接返回ret的话, 后面界面控件变化, ret也会跟着变化. 故直接返回True, False.
                return False
            return True
        except Exception as e:
            aklog_error(e)
            if is_raise:
                raise e
            return False

    def wait_ele_stable(self, locator, interval=0.2, timeout=None, stable_count=3):
        """
        等待元素坐标稳定，认为页面加载完成

        Args:
            locator: 元素定位信息
            timeout: 最大等待时间（秒）
            interval: 检查间隔（秒）
            stable_count: 连续多少次坐标一致才认为稳定

        Returns:
            元素对象

        Raises:
            TimeoutError: 超时未稳定
        """
        aklog_debug()
        if not timeout:
            timeout = self.wait_time
        end_time = time.time() + timeout
        last_bounds = None
        stable_times = 0
        ele = None
        while time.time() < end_time:
            ele = self.get_element(locator)
            if ele is None:
                return None
            bounds = ele.info.get('bounds')
            if bounds == last_bounds:
                stable_times += 1
                if stable_times >= stable_count:
                    aklog_debug(f"元素坐标已稳定：{bounds}")
                    return ele
            else:
                stable_times = 1
                last_bounds = bounds
            time.sleep(interval)
        aklog_debug(f"等待元素坐标稳定超时，最后坐标：{last_bounds}")
        return ele

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
            if isinstance(locator, dict):
                if 'resourceId' in locator:
                    ele_xpath += '@resource-id="%s" or ' % locator['resourceId']
                elif 'text' in locator:
                    ele_xpath += '@text="%s" or ' % locator['text']
                elif 'description' in locator:
                    ele_xpath += '@text="%s" or ' % locator['description']
            else:
                # 也可以直接传入多个id或name的文本
                if ':id/' in locator:
                    ele_xpath += '@resource-id="%s" or ' % locator
                else:
                    ele_xpath += '@text="%s" or ' % locator
        ele_xpath = ele_xpath.rstrip(' or ') + ']'
        return ele_xpath

    # endregion

    # region 输入框相关

    def set_text(self, locator, content, click=False, clear=True, print_trace=True, exit_keyboard=False):
        """输入框输入文本"""
        aklog_debug()
        try:
            ele = self.find_element(locator, print_trace=print_trace)
            if ele is None:
                return False

            # 如果元素定位方式Xpath，会自动点击输入框激活焦点，并清空输入框再输入文本
            if isinstance(ele, UiObject):
                # 有些输入框需要先点击才能输入
                if click:
                    ele.click()
                    time.sleep(0.5)
                if clear:
                    ele.clear_text()
            ele.set_text(content)
            if exit_keyboard:
                self.exit_u2_keyboard()
            time.sleep(0.2)
            return True
        except Exception as e:
            aklog_error(e)
            if print_trace or not e:
                aklog_debug(traceback.format_exc())
            return False

    def input_edit_by_name(self, name, content, click=False, clear=True, exit_keyboard=False):
        aklog_debug()
        try:
            ele = self.driver(text=name)
            # 有些输入框需要先点击才能输入
            if click:
                ele.click()
                time.sleep(0.5)
            if clear:
                ele.clear_text()
            ele.set_text(content)
            if exit_keyboard:
                self.exit_u2_keyboard()
            time.sleep(0.2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_edit_by_id(self, ele_id, content, click=False, clear=True, exit_keyboard=False):
        aklog_debug()
        try:
            ele = self.driver(resourceId=ele_id)
            # 有些输入框需要先点击才能输入
            if click:
                ele.click()
                time.sleep(0.5)
            if clear:
                ele.clear_text()
            ele.set_text(content)
            if exit_keyboard:
                self.exit_u2_keyboard()
            time.sleep(0.2)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def input_edit_by_xpath(self, ele_xpath, content, click=False, clear=True, exit_keyboard=False):
        aklog_debug()
        try:
            ele = self.driver.xpath(ele_xpath)  # 返回的是代理对象，clear_text不可用
            ele_info = ele.info
            support_clear = False
            try:
                if ele_info.get('className') == 'android.widget.EditText' and ele_info.get("resourceId"):
                    ele_resource_id = ele_info.get("resourceId")
                    index = None
                    same_id_eles = self.get_elements(ele_resource_id)  # 获取相同id的元素
                    for i, same_ele in enumerate(same_id_eles):
                        # 根据元素坐标来确定填写哪个输入框
                        if abs(same_ele.info.get('bounds')['top'] - ele_info.get('bounds')['top']) < 5:
                            index = i
                            break
                    if index is not None:
                        ele = same_id_eles[index]
                        support_clear = True
                    else:
                        aklog_info("未找到目标索引，使用XPath元素")
                else:
                    aklog_info("控件类型不是EditText或没有ResourceId，无法定位到原生控件")
            except:
                aklog_info('获取元素信息异常，无法定位到原生控件')

            # 有些输入框需要先点击才能输入
            if click:
                ele.click()
                time.sleep(0.5)
            if clear and support_clear:
                ele.clear_text()
            ele.set_text(content)
            if exit_keyboard:
                self.exit_u2_keyboard()
            time.sleep(0.2)
            return True
        except:
            aklog_error(str(traceback.format_exc()))
            return False

    def input_content_by_id(self, ele_id, content):
        """输入前不清空，可以用于seekbar滚动条设置"""
        return self.input_edit_by_id(ele_id, content, clear=False)

    def input_content_by_xpath(self, ele_xpath, content):
        """xpath方式都会清空输入框"""
        return self.input_edit_by_xpath(ele_xpath, content)

    def input_in_focused_edit(self, content):
        """在焦点输入框控件输入文本"""
        self.input_edit_by_xpath('.//android.widget.EditText[@focused="true"]', content)

    def click_focused_edit(self):
        self.click_btn_by_xpath('//android.widget.EditText[@focused="true"]')

    def set_fast_input_ime(self, enable=True):
        """设置是否启用快速输入法，启用后不会弹出输入键盘"""
        try:
            self.driver.set_input_ime(enable)
        except Exception as e:
            aklog_error(f'设置输入法失败，可能是设备权限问题，请手动设置输入法为AdbKeyboard')
            raise e

    def exit_keyboard(self):
        """退出键盘"""
        if self.is_exists('android:id/inputArea'):
            self.press_key_back()

    def set_virtual_keyboard(self, enable=1):
        """
        设置是否启用虚拟键盘，有些模拟器如果不启用虚拟键盘，会导致使用Xpath定位的输入框无法输入文本
        enable: 1 or 0
        """
        # 只有模拟器才需要设置虚拟键盘，模拟器的device_id一般为127.0.0.1:5555或者emulator-5554
        if '127.0.0.1' not in self.device_id and '-' not in self.device_id:
            return
        aklog_debug()
        value = self.shell('settings get secure show_ime_with_hard_keyboard')
        if not value:
            return
        value = str(value).strip()
        if value in ['0', '1'] and value != str(enable):
            aklog_debug('将虚拟键盘设置为 %s' % enable)
            self.shell('settings put secure show_ime_with_hard_keyboard %s' % enable)

    def exit_u2_keyboard(self):
        """有些安卓模拟器的这个虚拟键盘会挡住控件，需要退出才能点击操作"""
        try:
            # 需要uiautomator2 3.3.0以上版本才支持
            self.driver.hide_keyboard()
            # 有些设备的密码输入框会启用安全键盘，需要手动按back键退出
            if self.wait_gone('android:id/inputArea', timeout=2):
                return True
            self.press_key_back()
        except:
            # 兼容需要uiautomator2低版本
            if self.is_exist('android:id/inputArea', timeout=1):
                self.press_key_back()

    # endregion

    # region 点击操作

    def click_btn(self, locator, sec=0.2, timeout=None, print_trace=False, is_raise=False) -> bool:
        """点击元素"""
        aklog_debug()
        try:
            if not timeout:
                timeout = self.wait_time

            ele = self.find_element(
                locator, timeout=timeout, print_trace=print_trace, is_raise=is_raise)
            if ele is None:
                return False

            ele.click(timeout=timeout)
            time.sleep(sec)
            return True
        except Exception as e:
            aklog_error(f'click error: {e}')
            if print_trace or not e:
                aklog_debug(traceback.format_exc())
            if is_raise:
                raise e
            return False

    def click_to_jump(self, locator, target_locator=None, target_activity=None, is_disappear=None,
                      timeout=3, retry=3, raise_on_fail=True) -> bool:
        """
        点击跳转页面或者弹出窗口，确保点击后页面跳转到目标页面

        Args:
            locator: 要点击的元素选择器
            target_locator: 目标页面的特定元素选择器，可以为空，只检查页面元素信息是否有变化
            target_activity: 也可以传入Activity，和target_locator二选一即可
            is_disappear: 点击后，当前点击的元素是否会消失，如果预期会消失，但实际没有消失说明点击失败，否则点击成功
            timeout: 等待目标元素出现的超时时间
            retry: 点击重试次数
            raise_on_fail: 是否在失败时抛出异常，默认为 True

        Returns:
            bool: 跳转是否成功
        """
        aklog_debug()
        if not timeout:
            timeout = 3

        base_interval = 0.2
        max_multiplier = 5
        interval = base_interval  # 初始重试间隔
        max_interval = base_interval * (2 ** max_multiplier)  # 最大重试间隔

        for attempt in range(retry):
            # 查找待点击元素
            ele = self.find_element(locator, timeout=timeout)
            if ele is None:
                if attempt > 0 and is_disappear:
                    # 预期点击后元素消失，实际已找不到，说明跳转成功
                    aklog_debug(f"点击成功，点击的元素已消失，页面已跳转 (尝试次数: {attempt})")
                    return True
                if raise_on_fail:
                    self.screen_shot()
                    raise RuntimeError(f"元素 {locator} 不存在，无法点击")
                return False

            try:
                old_page_source = None
                if not target_locator and not target_activity and not is_disappear:
                    # 如果没有指定目标元素或activity，后续用页面结构变化判断跳转
                    try:
                        old_page_source = self.driver.dump_hierarchy()
                    except Exception as e:
                        aklog_debug(f'dump_hierarchy failed: {e}')
                        return False

                try:
                    # 尝试点击元素，uiautomator2的click会再次查找元素，可能抛异常
                    ele.click(timeout=timeout)
                except Exception as click_e:
                    aklog_warn(f"第{attempt + 1}次点击元素 {locator} 失败: {click_e}")
                    if attempt == retry - 1 and raise_on_fail:
                        self.screen_shot()
                        raise RuntimeError(f"点击元素 {locator} 失败: {click_e}")
                    interval = min(interval * 2, max_interval)
                    continue

                time.sleep(interval)  # 等待页面响应

                # 检查目标页面的特定元素是否出现
                if target_locator and self.wait_visible(target_locator, timeout):
                    aklog_debug(f"点击成功，目标页面元素 {target_locator} 已加载 (尝试次数: {attempt + 1})")
                    return True

                # 检查是否切换到目标页面的activity
                if target_activity and self.wait_activity(target_activity, timeout):
                    aklog_debug(f"点击成功，已切换至页面 {target_activity} (尝试次数: {attempt + 1})")
                    return True

                # 检查点击的元素是否消失
                if is_disappear and self.wait_gone(locator, timeout):
                    aklog_debug(f"点击成功，点击的元素已消失，页面已跳转 (尝试次数: {attempt + 1})")
                    return True

                # 检查页面是否发生变化
                if old_page_source and self.wait_for_page_change(old_page_source, timeout):
                    aklog_debug(f"点击成功，页面已变化 (尝试次数: {attempt + 1})")
                    return True

                aklog_debug(f"点击后目标页面或元素未加载，重试 {attempt + 1}/{retry} 次...")
                interval = min(interval * 2, max_interval)
                continue

            except Exception as e:
                aklog_warn(f"第{attempt + 1}次查找或点击元素 {locator} 异常: {e}")
                if attempt == retry - 1 and raise_on_fail:
                    self.screen_shot()
                    aklog_error(f"点击后目标页面或元素 {target_activity or target_locator} 未加载，重试 {retry} 次失败。")
                    raise RuntimeError(
                        f"点击后目标页面或元素 {target_activity or target_locator} 未加载，重试 {retry} 次失败。"
                    )
                interval = min(interval * 2, max_interval)
                continue

        # 所有重试后仍未成功
        aklog_error(f"点击后目标页面或元素 {target_activity or target_locator} 未加载，重试 {retry} 次失败。")
        if raise_on_fail:
            self.screen_shot()
            raise RuntimeError(
                f"点击后目标页面或元素 {target_activity or target_locator} 未加载，重试 {retry} 次失败。"
            )
        return False

    def click_repeat_until_target(self, locator, target_locator=None, target_activity=None, is_disappear=None,
                                  timeout=2, retry=9, is_raise=False) -> bool:
        """
        多次点击按钮，直到目标出现，或者当前按钮消失
        比如要点击多次返回按键，直到某个页面
        target_locator/target_activity/is_disappear三选一即可
        Args:
            locator (): 要点击的元素选择器
            target_locator (): 目标页面的特定元素选择器，可以为空，只检查页面元素信息是否有变化
            target_activity (): 目标页面的Activity
            is_disappear (): 点击后，当前点击的元素是否会消失，如果预期会消失，但实际没有消失说明点击失败，否则点击成功
            timeout (): 等待目标元素出现的超时时间
            retry (): 点击重试次数
            is_raise (bool): 是否抛出异常
        """
        aklog_debug()
        try:
            interval = 0.5
            for attempt in range(retry):
                ele = self.find_element(locator, timeout=timeout, is_raise=is_raise)
                if ele is None:
                    if is_disappear:
                        return True
                    return False
                # 点击元素，前面几次点击间隔较短，如果还是没有退出，则增加点击间隔时间
                ele.click(timeout=timeout)
                if 3 <= attempt <= 5:
                    interval = 1
                elif 6 <= attempt <= retry:
                    interval = 2
                time.sleep(interval)

                # 检查目标页面的特定元素是否出现
                if target_locator and self.wait_visible(target_locator, timeout):
                    aklog_debug(f"重复点击成功，目标页面元素 {target_locator} 已加载 (尝试次数: {attempt + 1})")
                    return True
                # 检查是否切换到目标页面的activity
                if target_activity and self.wait_activity(target_activity, timeout):
                    aklog_debug(f"重复点击成功，已切换至页面 {target_activity} (尝试次数: {attempt + 1})")
                    return True
                # 检查点击的元素是否还存在
                if is_disappear and not self.wait_visible(locator, timeout):
                    aklog_debug(f"重复点击成功，点击的元素已消失，页面已跳转 (尝试次数: {attempt + 1})")
                    return True
                continue
            if target_locator:
                aklog_error(f"点击后目标元素 {target_locator} 未加载，重试 {retry} 次失败。")
            elif target_activity:
                aklog_error(f"点击后目标页面 {target_activity} 未加载，重试 {retry} 次失败。")
            elif is_disappear:
                aklog_error(f"点击后元素 {locator} 未消失，重试 {retry} 次失败。")
            return False
        except Exception as e:
            aklog_error(e)
            self.screen_shot()
            if is_raise:
                raise e
            return False

    def click_btn_location(self, locator, mid_x_length=0.5, mid_y_length=0.5, print_trace=False) -> bool:
        """点击元素内的某个坐标点，有些元素中心点无法点击时，可以用该方法"""
        aklog_debug()
        try:
            ele = self.find_element(locator, print_trace=print_trace)
            if ele is None:
                return False
            if isinstance(ele, UiObject):
                ele_mid_x, ele_mid_y = ele.center(offset=(mid_x_length, mid_y_length))
            else:
                ele_mid_x, ele_mid_y = ele.offset(mid_x_length, mid_y_length)
            self.driver.click(ele_mid_x, ele_mid_y)
            return True
        except Exception as e:
            aklog_error(e)
            if print_trace or not e:
                aklog_debug(traceback.format_exc())
            return False

    def click_btn_out_location(self, locator, sec=0.2, print_trace=False) -> bool:
        """点击弹窗之外的地方来取消弹窗"""
        aklog_debug()
        try:
            ele = self.get_element(locator)
            if ele is None:
                return False

            if isinstance(ele, UiObject):
                lx, ly, rx, ry = ele.bounds()
            else:
                lx, ly, rx, ry = ele.bounds

            # 获取屏幕尺寸
            screen_width, screen_height = self.get_screen_size()

            # 先判断左右两边是否可以点击，如果左右两边都无法点击，则点击上下两边
            if lx > 1:
                x = int(lx / 2)
                y = int(screen_height / 2)
            elif rx < screen_width - 1:
                x = int((screen_width + rx) / 2)
                y = int(screen_height / 2)
            else:
                x = int(screen_width / 2)
                if ly > 1:
                    y = int(ly / 2)
                elif ry < screen_height - 1:
                    y = int((screen_height + ry) / 2)
                else:
                    y = 0
            aklog_debug('x: %s, y: %s' % (x, y))
            self.click_location(x, y)
            time.sleep(sec)
            return True
        except Exception as e:
            aklog_error(e)
            if print_trace or not e:
                aklog_debug(traceback.format_exc())
            return False

    def multi_click_btn(self, locator, times=1, interval=0.2, print_trace=False) -> bool:
        """
        多次点击元素
        times: 点击次数
        interval: 间隔时间，单位: s
        """
        aklog_debug()
        try:
            ele = self.get_element(locator)
            if ele is None:
                return False

            ele_mid_x, ele_mid_y = ele.center()
            for i in range(0, times):
                self.driver.click(ele_mid_x, ele_mid_y)
                time.sleep(interval)
            return True
        except Exception as e:
            aklog_error(e)
            if print_trace or not e:
                aklog_debug(traceback.format_exc())
            return False

    def wait_clickable(self, locator, timeout=5) -> bool:
        """等待控件可点击"""
        aklog_debug()
        try:
            end_time = time.time() + timeout
            while time.time() < end_time:
                ele = self.get_element(locator)
                clickable = ele.info.get('clickable')
                if clickable is True or clickable == 'true':
                    return True
                time.sleep(1)
            aklog_error('%s 未变成可点击状态' % locator)
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_location(self, x, y) -> bool:
        aklog_debug()
        try:
            self.driver.click(x, y)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def click_left_top(self):
        """点击左上角(1, 1)，用于退出弹窗或者退出屏保"""
        if self.screen_clickable_area:
            x, y = self.screen_clickable_area[0] + 1, self.screen_clickable_area[1] + 1
        else:
            x, y = 1, 1
        return self.click_location(x, y)

    def click_ele_by_location(self, eleid, times=1):
        """快速点击, 用于如门口机点击10次进入setting"""
        ret = self.get_ele_location(eleid)
        x = ret.get('x')
        y = ret.get('y')
        for i in range(times):
            self.shell('input tap {} {}'.format(x, y))

    def click_circle(self, locator, angle, radius_percent, radius=None):
        """
            点击圆形里的任意点(以中心点的坐标为圆心)
            :param locator: 元素定位信息
            :param angle: 坐标系角度 0-360
            :param radius_percent: 半径的百分比, 0-100，有些情况下的控件宽高比圆大一些，因此如果点击倍数100%的，可能会点击到圆的外面，点击失败，
            尽量传入的倍数小于80%。
            :param radius: 半径长度，有些情况下的控件宽高比圆大一些，因此如果点击倍数100%的，可能会点击到圆的外面，点击失败，
            因此需要传入正确的半径长度
            :return: bool
        """
        aklog_debug()
        try:
            # 将角度转换为弧度
            lx, ly, rx, ry = self.get_ele_bounds(locator)
            center_x = (lx + rx) / 2
            center_y = (ly + ry) / 2
            if not radius:
                radius = (ry - ly) / 2  # 半径
            angle_rad = math.radians(-angle)

            # 计算点的直角坐标
            distance = radius_percent / 100 * radius
            x = int(center_x + distance * math.cos(angle_rad))
            y = int(center_y + distance * math.sin(angle_rad))

            self.driver.click(x, y)
            aklog_debug('%s location: (%s, %s)' % (locator, int(x), int(y)))
            return True
        except:
            aklog_debug(traceback.format_exc())
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

    def click_btn_by_id(self, ele_id, sec=0.2, wait_time=None, print_trace=True):
        aklog_debug()
        try:
            if not wait_time:
                wait_time = self.wait_time

            if '|' not in ele_id:
                self.driver(resourceId=ele_id).click(timeout=wait_time)
            else:
                ele_xpath = self.get_id_list_expression(ele_id)
                self.driver.xpath(ele_xpath).click(timeout=wait_time)
            time.sleep(sec)
            return True
        except Exception as e:
            aklog_debug('click btn failed by id: {}'.format(ele_id))
            if print_trace or not e:
                aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_by_xpath(self, ele_xpath, sec=0.2, wait_time=None, print_trace=True):
        aklog_debug()
        if ele_xpath.startswith('.//'):
            ele_xpath = ele_xpath[1:]
        if ele_xpath.startswith('(.//'):
            ele_xpath = '(' + ele_xpath[2:]
        try:
            if not wait_time:
                wait_time = self.wait_time
            self.driver.xpath(ele_xpath).click(timeout=wait_time)
            time.sleep(sec)
            return True
        except Exception as e:
            aklog_debug('click btn failed by xpath: {}'.format(ele_xpath))
            if print_trace or not e:
                aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_by_accessibility_id(self, ele_desc, sec=0.2):
        """Content-desc类型的元素可以用这个来定位"""
        aklog_debug()
        try:
            self.driver(description=ele_desc).click(timeout=self.wait_time)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_by_name(self, ele_name, sec=0.2, wait_time=None, print_trace=True, ignore_case=False):
        aklog_debug()
        try:
            if not wait_time:
                wait_time = self.wait_time
            if '|' in ele_name:
                list1 = [i.strip() for i in ele_name.split('|') if i.strip()]
                xpath1 = '//*['
                for i in list1:
                    xpath1 += '@text="{}"'.format(i)
                    if i != list1[-1]:
                        xpath1 += ' or '
                xpath1 += ']'
                self.driver.xpath(xpath1).click(timeout=wait_time)
            else:
                # 2024.12.19 补充无视大小写的设计.
                if ignore_case:
                    textlist = []
                    try:
                        str1 = self.driver.dump_hierarchy().replace('\xa0', '')
                        textlist = list(set(re.findall('text="(.*?)"', str1)))
                    except:
                        pass
                    if textlist and ele_name not in textlist:
                        for text in textlist:
                            if ele_name.lower() == text.lower():
                                ele_name = text
                                break
                self.driver(text=ele_name).click(timeout=wait_time)
            time.sleep(sec)
            return True
        except Exception as e:
            aklog_debug('click btn failed by name: {}'.format(ele_name))
            if print_trace or not e:
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
        except Exception as e:
            aklog_debug('click btn failed by desc: {}'.format(desc))
            if print_trace or not e:
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
        except Exception as e:
            aklog_debug('click btn failed by names: {}'.format(tuple(names)))
            if print_trace or not e:
                aklog_debug(str(traceback.format_exc()))
            return False

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

    def click_btn_location_by_id(self, ele_id, mid_x_length=0.5, mid_y_length=0.5):
        """点击元素内的某个坐标点，有些元素中心点无法点击时，可以用该方法"""
        aklog_debug("click_btn_location_by_id, ele_id: %s" % ele_id)
        try:
            ele = self.driver(resourceId=ele_id)
            ele_mid_x, ele_mid_y = ele.center(offset=(mid_x_length, mid_y_length))
            self.driver.click(ele_mid_x, ele_mid_y)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_location_by_name(self, ele_name, mid_x_length=0.5, mid_y_length=0.5):
        """点击元素内的某个坐标点，有些元素中心点无法点击时，可以用该方法"""
        aklog_debug("click_btn_location_by_name, ele_name: %s" % ele_name)
        try:
            ele = self.driver(text=ele_name)
            ele_mid_x, ele_mid_y = ele.center(offset=(mid_x_length, mid_y_length))
            self.driver.click(ele_mid_x, ele_mid_y)
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
            self.click_location(x, y)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_btn_quickly_by_xpath(self, ele_xpath, times=1, duration=200):
        """快速多次点击元素"""
        aklog_debug("click_btn_quickly_by_xpath : %s, times: %s" % (ele_xpath, times))
        try:
            ele = self.driver.xpath(ele_xpath).get()
            ele_mid_x, ele_mid_y = ele.center()
            for i in range(0, times):
                self.driver.click(ele_mid_x, ele_mid_y)
                time.sleep(duration / 1000)
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def click_btn_quickly_by_id(self, ele_id, times=1, duration=200):
        """快速多次点击元素"""
        aklog_debug("click_btn_quickly_by_id : %s, times: %s" % (ele_id, times))
        try:
            ele = self.driver(resourceId=ele_id)
            ele_mid_x, ele_mid_y = ele.center(offset=(0.5, 0.5))
            for i in range(0, times):
                self.driver.click(ele_mid_x, ele_mid_y)
                time.sleep(duration / 1000)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def click_circle_by_xpath(self, ele_xpath, angle, distance_multiple):
        """
            点击圆形里的任意点(以中心点的坐标为圆心)
            :param ele_xpath: 元素ele_xpath
            :param angle: 坐标系角度
            :param distance_multiple: 半径的倍数
            :return: dict类型
        """
        # 将角度转换为弧度
        ele_location = self.get_ele_mid_location_by_xpath(ele_xpath)
        center_x = ele_location['x']
        center_y = ele_location['y']
        ele_size = self.get_ele_rect_by_xpath(ele_xpath)
        radius = ele_size['width'] / 2
        angle_rad = math.radians(-angle)

        # 计算点的直角坐标
        distance = distance_multiple * radius
        x = center_x + distance * math.cos(angle_rad)
        y = center_y + distance * math.sin(angle_rad)
        try:
            self.driver.click(x, y)
            aklog_debug('%s location: (%s, %s)' % (ele_xpath, int(x), int(y)))
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def click_circle_by_id(self, ele_id, angle, distance_multiple):
        """
            点击圆形里的任意点(以中心点的坐标为圆心)
            :param ele_id: 元素ele_id
            :param angle: 坐标系角度
            :param distance_multiple: 半径的倍数
            :return: dict类型
        """
        # 将角度转换为弧度
        ele_location = self.get_ele_mid_location_by_xpath(ele_id)
        center_x = ele_location['x']
        center_y = ele_location['y']
        ele_size = self.get_ele_rect_by_xpath(ele_id)
        radius = ele_size['width'] / 2
        angle_rad = math.radians(-angle)

        # 计算点的直角坐标
        distance = distance_multiple * radius
        x = center_x + distance * math.cos(angle_rad)
        y = center_y + distance * math.sin(angle_rad)
        try:
            self.driver.click(x, y)
            aklog_debug('%s location: (%s, %s)' % (ele_id, int(x), int(y)))
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    # endregion

    # region 按钮开关操作、复选框相关

    def set_checked(self, locator, status='Enable'):
        """复选框操作，设置按钮开启或关闭，Status可以设置为 Enable/Disable， True/False， 1、0"""
        aklog_debug()
        try:
            ele = self.get_element(locator)
            if ele is None:
                return False

            if isinstance(ele, UiObject):
                ele_info = ele.info
            else:
                ele_info = ele.attrib
            if status == 'Enable' or status is True or str(status) == '1':
                if ele_info.get('checked') == 'false' or ele_info.get('checked') is False:
                    ele.click()
                    time.sleep(0.2)
                return True
            elif status == 'Disable' or status is False or str(status) == '0':
                if ele_info.get('checked') == 'true' or ele_info.get('checked') is True:
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

            if ele.info.get('checked') == 'true' or ele.info.get('checked') is True:
                aklog_debug('checked: true')
                return True
            else:
                aklog_debug('checked: false')
                return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def set_checked_button_by_id(self, ele_id, status='Enable'):
        """设置按钮开启或关闭，Status可以设置为 Enable/Disable， True/False， 1、0"""
        aklog_debug()
        try:
            ele = self.driver(resourceId=ele_id)
            ele_info = ele.info
            if status == 'Enable' or status is True or str(status) == '1':
                if ele_info.get('checked') == 'false' or ele_info.get('checked') is False:
                    ele.click()
                    time.sleep(0.2)
                return True
            elif status == 'Disable' or status is False or str(status) == '0':
                if ele_info.get('checked') == 'true' or ele_info.get('checked') is True:
                    ele.click()
                    time.sleep(0.2)
                return True
            else:
                aklog_debug('Status参数值 %s 不正确')
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

    def check_by_id(self, ele_id):
        """ 勾选 """
        aklog_debug()
        try:
            ele = self.driver(resourceId=ele_id)
            if ele.info.get('checked') == 'false' or ele.info.get('checked') is False:
                ele.click()
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

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

    def uncheck_by_id(self, ele_id):
        """ 取消勾选 """
        aklog_debug()
        try:
            ele = self.driver(resourceId=ele_id)
            if ele.info.get('checked') == 'true' or ele.info.get('checked') is True:
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

    def is_checked_by_id(self, ele_id):
        """判断元素（单选框或复选框）是否选中"""
        aklog_debug()
        try:
            ele = self.driver(resourceId=ele_id)
            if ele.info.get('checked') == 'true' or ele.info.get('checked') is True:
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

    def long_press(self, locator, duration=2, timeout=None):
        """
        长按
        duration: 秒数
        """
        aklog_debug()
        try:
            if not timeout:
                timeout = self.wait_time

            ele = self.get_element(locator, timeout=timeout)
            if ele is None:
                return False

            if isinstance(ele, UiObject):
                ele.long_click(duration=duration)
            else:
                ele_mid_x, ele_mid_y = ele.center()
                self.driver.long_click(ele_mid_x, ele_mid_y, duration)
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
            ele = self.driver.xpath(ele_xpath).get()
            ele_mid_x, ele_mid_y = ele.center()
            self.driver.long_click(ele_mid_x, ele_mid_y, duration)
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
            self.driver(text=ele_name).long_click(duration, timeout=self.wait_time)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def long_press_by_id(self, ele_id, duration=2):
        """
        长按
        duration: 秒数
        """
        aklog_debug()
        try:
            self.driver(resourceId=ele_id).long_click(duration=duration, timeout=self.wait_time)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    # endregion

    # region 滑动，滚动查找

    def scroll_v_until_find(self, locator, box_ele=None, counts=10, duration=0.3, length=0.5, direction='up',
                            x_offset=0.25, near='center', oneway=False, click=False, sec=0.5):
        """
        上下滑动直到找到元素并可见
        :param locator: 选项定位
        :param box_ele: 默认None表示整个屏幕上下滑动，可以指定元素框，可以先用get_element方法获取元素，也可以传入box元素的locator
        :param counts: 该参数弃用
        :param duration: 滑动步长
        :param length: 手指上滑的距离占元素框的比例
        :param direction: 先上滑还是下滑，up or down
        :param x_offset: 滑动的相对位置: 0-1
        :param oneway: 是否只查找单向，比如向上滑动10次后，就不再向下滑动继续查找了
        :param near: 靠近顶部或底部，默认为center，top表示查找的元素尽可能靠近顶部，bottom表示靠近底部，center表示靠近中间
        并且最好传入box_ele
        :param click: 找到元素后是否点击操作，要点击操作，near如果为None会修改为center
        :param sec: 点击后等待多长时间
        :return:
        """
        aklog_debug()
        if isinstance(box_ele, (str, dict, tuple)):
            box_ele = self.wait_ele_stable(box_ele)
        checked_direct = []  # 已检查的方向
        max_end_attempt = 3  # 连续几次页面结构未改变，认为滑动到底/顶
        end_attempt = 0
        last_hierarchy = None
        ret = False
        timeout = max(min(1800, int(counts) * 180), 120) if counts and isinstance(counts, int) else 1800
        end_time = time.time() + timeout
        while time.time() < end_time:  # 确保不会陷入死循环
            ret = self.is_exists(locator)
            if ret:
                break
            # 检查页面信息，判断是否已经滚动到底
            cur_hierarchy = self.dump_hierarchy()
            if not cur_hierarchy:
                aklog_warn('dump_hierarchy返回空，可能页面异常，直接返回False')
                return False
            if self.check_dump_hierarchy(cur_hierarchy, last_hierarchy, check_package_only=True):
                end_attempt += 1  # 连续未变次数+1
                aklog_debug(f'第{end_attempt}次滑动后页面未变化')
                if end_attempt >= max_end_attempt:
                    if direction not in checked_direct:
                        checked_direct.append(direction)
                    if len(checked_direct) >= 2:
                        aklog_warn(f'两个方向都滑到边，未找到 {locator}')
                        return False
                    if oneway:
                        aklog_warn(f'只查找单方向，已滑动到边，未找到 {locator}')
                        return False
                    # 切换方向
                    direction = 'down' if direction == 'up' else 'up'
                    aklog_debug(f'已经滑动到边，切换方向: {direction}')
                    end_attempt = 0  # 切换方向后重置计数器
            else:
                end_attempt = 0  # 页面有变化，重置计数器

            last_hierarchy = cur_hierarchy

            if direction == 'up':
                if not self.swipe_up(
                        box_ele=box_ele, duration=duration, length=length, x_offset=x_offset,
                        sec=0.5, check_safe=True):
                    aklog_warn('滑动异常，提前返回False')
                    return False
            else:
                if not self.swipe_down(
                        box_ele=box_ele, duration=duration, length=length, x_offset=x_offset,
                        sec=0.5, check_safe=True):
                    aklog_warn('滑动异常，提前返回False')
                    return False
            continue

        if ret:
            if box_ele is not None:
                box_bounds = box_ele.info.get('bounds')
                box_lx, box_ly = box_bounds['left'], box_bounds['top']
                box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
            else:
                box_lx, box_ly = 0, 0
                box_rx, box_ry = self.get_screen_size()

            if near == 'top':
                # 让查找的元素尽可能靠近滚动框的顶部
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                if ly - box_ly > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = max(box_ly + 50, min(ly, box_ry - 50))
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = start_y + (box_ly + 50 - ly)
                    self.swipe(start_x, start_y, end_x, end_y)
                    time.sleep(0.5)
            elif near == 'bottom':
                # 让查找的元素尽可能靠近滚动框的底部
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                if box_ry - ry > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = max(box_ly + 50, min(ry, box_ry - 50))
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = start_y + (box_ry - 50 - ry)
                    self.swipe(start_x, start_y, end_x, end_y)
                    time.sleep(0.5)
            elif near == 'center':
                # 让查找的元素尽可能靠近滚动框的中间
                box_mid_y = int((box_ly + box_ry) / 2)
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                ele_mid_y = int((ly + ry) / 2)
                box_width = int(box_rx) - int(box_lx)
                start_x = box_lx + int(box_width * x_offset)
                end_x = start_x
                delta = box_mid_y - ele_mid_y
                if abs(delta) > 50:
                    # 计算滑动距离，适当放大，避免滑动不足
                    swipe_distance = int(delta * 1.4)
                    # 限制滑动距离，避免越界
                    min_gap = 50
                    if swipe_distance > 0:
                        start_y = max(box_ly + min_gap, min(ele_mid_y, box_ry - min_gap))
                        end_y = min(start_y + swipe_distance, box_ry - min_gap)
                    else:
                        start_y = min(box_ry - min_gap, max(ele_mid_y, box_ly + min_gap))
                        end_y = max(start_y + swipe_distance, box_ly + min_gap)
                    # 防止滑动距离过小
                    if abs(end_y - start_y) > min_gap:
                        self.swipe(start_x, start_y, end_x, end_y)
                        time.sleep(0.5)
            elif box_ele is not None:
                # 滚动元素到列表框点击区域内
                for _ in range(3):
                    ele_mid_x, ele_mid_y = self.get_element(locator).center()
                    if box_ly < ele_mid_y < box_ry:
                        break
                    if ele_mid_y <= box_ly:
                        aklog_debug(
                            '元素中心点坐标 (%s, %s) 超出了列表框范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                        self.swipe_down(box_ele, duration=0.3, length=0.2, x_offset=x_offset)
                    elif ele_mid_y >= box_ry:
                        aklog_debug(
                            '元素中心点坐标 (%s, %s) 超出了列表框范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                        self.swipe_up(box_ele, duration=0.3, length=0.2, x_offset=x_offset)

            # 滚动元素到可点击区域
            if self.screen_clickable_area:
                for _ in range(3):
                    ele_mid_x, ele_mid_y = self.get_element(locator).center()
                    if self.screen_clickable_area[1] < ele_mid_y < self.screen_clickable_area[3]:
                        break
                    if ele_mid_y <= self.screen_clickable_area[1]:
                        aklog_debug(
                            '元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                        self.swipe_down(box_ele, duration=0.3, length=0.2, x_offset=x_offset)
                    elif ele_mid_y >= self.screen_clickable_area[3]:
                        aklog_debug(
                            '元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                        self.swipe_up(box_ele, duration=0.3, length=0.2, x_offset=x_offset)

            if click:
                time.sleep(0.5)
                return self.click_btn(locator, sec=sec)
            return True
        else:
            aklog_debug('%s is not found' % locator)
            return False

    def scroll_h_until_find(self, locator, box_ele=None, counts=10, duration=0.3, length=0.5, direction='left',
                            y_offset=0.25, near=None, oneway=False, click=False, sec=0.5):
        """
        左右滑动直到找到元素并可见
        :param locator: 选项定位
        :param box_ele: 默认None表示整个屏幕左右滑动，可以指定元素框，可以先用get_element方法获取元素
        :param counts: 该参数弃用
        :param duration: 滑动步长
        :param length: 手指左滑的距离占元素框的比例
        :param direction: 先左滑还是右滑，left or right
        :param y_offset: 滑动的相对位置: 0-1
        :param oneway: 是否只查找单向，比如向上滑动10次后，就不再向下滑动继续查找了
        :param near: 靠近最左边或最右边，默认为None找到即可，
        leftmost表示查找的元素尽可能靠近顶部，rightmost表示靠近底部，center表示靠近中间
        并且最好传入box_ele
        :param click: 找到元素后是否点击操作
        :param sec: 点击后等待多长时间
        :return:
        """
        aklog_debug()
        if isinstance(box_ele, (str, dict, tuple)):
            box_ele = self.wait_ele_stable(box_ele)

        checked_direct = []  # 已检查的方向
        max_end_attempt = 3  # 连续几次页面结构未改变，认为滑动到底/顶
        end_attempt = 0
        last_hierarchy = None
        ret = False
        timeout = max(min(1800, int(counts) * 180), 120) if counts and isinstance(counts, int) else 1800
        end_time = time.time() + timeout
        while time.time() < end_time:  # 确保不会陷入死循环
            ret = self.is_exists(locator)
            if ret:
                break
            # 检查页面信息，判断是否已经滚动到底
            cur_hierarchy = self.dump_hierarchy()
            if not cur_hierarchy:
                aklog_warn('dump_hierarchy返回空，可能页面异常，直接返回False')
                return False
            if self.check_dump_hierarchy(cur_hierarchy, last_hierarchy, check_package_only=True):
                end_attempt += 1  # 连续未变次数+1
                aklog_debug(f'第{end_attempt}次滑动后页面未变化')
                if end_attempt >= max_end_attempt:
                    if direction not in checked_direct:
                        checked_direct.append(direction)
                    if len(checked_direct) >= 2:
                        aklog_warn(f'两个方向都滑到边，未找到 {locator}')
                        return False
                    if oneway:
                        aklog_warn(f'只查找单方向，已滑动到边，未找到 {locator}')
                        return False
                    # 切换方向
                    direction = 'right' if direction == 'left' else 'left'
                    aklog_debug(f'已经滑动到边，切换方向: {direction}')
                    end_attempt = 0  # 切换方向后重置计数器
            else:
                end_attempt = 0  # 页面有变化，重置计数器

            last_hierarchy = cur_hierarchy

            if direction == 'left':
                if not self.swipe_left(
                        box_ele=box_ele, duration=duration, length=length, y_offset=y_offset,
                        sec=0.5, check_safe=True):
                    aklog_warn('滑动异常，提前返回False')
                    return False
            else:
                if not self.swipe_right(
                        box_ele=box_ele, duration=duration, length=length, y_offset=y_offset,
                        sec=0.5, check_safe=True):
                    aklog_warn('滑动异常，提前返回False')
                    return False
            continue

        if ret:
            if box_ele is not None:
                box_bounds = box_ele.info.get('bounds')
                box_lx, box_ly = box_bounds['left'], box_bounds['top']
                box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
            else:
                box_lx, box_ly = 0, 0
                box_rx, box_ry = self.get_screen_size()

            if near == 'leftmost':
                # 让查找的元素尽可能靠近滚动框的最左边
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                if lx - box_lx > 50:
                    box_height = int(box_ry) - int(box_ly)
                    start_y = box_ly + int(box_height * y_offset)
                    start_x = max(box_lx + 50, min(lx, box_rx - 50))
                    end_y = box_ly + int(box_height * y_offset)
                    end_x = start_x + (box_lx + 50 - lx)
                    self.swipe(start_x, start_y, end_x, end_y)
            elif near == 'rightmost':
                # 让查找的元素尽可能靠近滚动框的最右边
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                if box_rx - rx > 50:
                    box_height = int(box_ry) - int(box_ly)
                    start_y = box_ly + int(box_height * y_offset)
                    start_x = max(box_lx + 50, min(rx, box_rx - 50))
                    end_y = box_ly + int(box_height * y_offset)
                    end_x = start_x + (box_rx - 50 - rx)
                    self.swipe(start_x, start_y, end_x, end_y)
            elif near == 'center':
                # 让查找的元素尽可能靠近滚动框的中间
                box_mid_x = int((box_lx + box_rx) / 2)
                lx, ly, rx, ry = self.get_ele_bounds(locator)
                ele_mid_x = int((lx + rx) / 2)
                if abs(box_mid_x - ele_mid_x) > 50:
                    box_height = int(box_ry) - int(box_ly)
                    start_y = box_ly + int(box_height * y_offset)
                    start_x = max(box_lx + 50, min(ele_mid_x, box_rx - 50))
                    end_y = box_ly + int(box_height * y_offset)
                    end_x = start_x + (box_mid_x - ele_mid_x)
                    self.swipe(start_x, start_y, end_x, end_y)
            elif box_ele is not None:
                for _ in range(3):
                    ele_mid_x, ele_mid_y = self.get_element(locator).center()
                    if box_lx < ele_mid_x < box_rx:
                        break
                    if ele_mid_x <= box_lx:
                        aklog_debug(
                            '元素中心点坐标 (%s, %s) 超出了列表框范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                        self.swipe_right(box_ele, duration=0.3, length=0.2, y_offset=y_offset)
                    elif ele_mid_x >= box_rx:
                        aklog_debug(
                            '元素中心点坐标 (%s, %s) 超出了列表框范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                        self.swipe_left(box_ele, duration=0.3, length=0.2, y_offset=y_offset)
            # 滚动元素到可点击区域
            if self.screen_clickable_area:
                for _ in range(3):
                    ele_mid_x, ele_mid_y = self.get_element(locator).center()
                    if self.screen_clickable_area[0] < ele_mid_x < self.screen_clickable_area[2]:
                        break
                    if ele_mid_x <= self.screen_clickable_area[0]:
                        aklog_debug(
                            '元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                        self.swipe_right(box_ele, duration=0.3, length=0.2, y_offset=y_offset)
                    elif ele_mid_x >= self.screen_clickable_area[2]:
                        aklog_debug(
                            '元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                        self.swipe_left(box_ele, duration=0.3, length=0.2, y_offset=y_offset)

            if click:
                time.sleep(0.5)
                return self.click_btn(locator, sec=sec)
            return True
        else:
            aklog_debug('%s is not found' % locator)
            return False

    def drag_element(self, locator, direction='up', length=0.5, duration=0.3, sec=0.1):
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
        ret = self.swipe(start_x, start_y, end_x, end_y, duration)
        time.sleep(sec)
        return ret

    def swipe(self, fx, fy, tx, ty, duration=0.3, steps=None):
        """
        滑动操作，自动保护坐标边界，避免超出屏幕范围。
        当duration>0.2时，根据滑动距离动态调整steps，保证滑动速度均匀，避免惯性滚动。
        当duration<0.2时，保持duration对应的步长滑动速度
        Args:
            fx (int): 起始点X坐标。
            fy (int): 起始点Y坐标。
            tx (int): 终点X坐标。
            ty (int): 终点Y坐标。
            duration (float): 滑动持续时间（秒）。
            steps (int): 滑动的步长
        Returns:
            bool: 滑动成功返回True，失败返回False。
        """
        min_steps = 4  # 快速滑动时的最小步长，如果太小，会导致滑动效果没有被应用捕捉到，比如下滑刷新
        slow_min_steps = 10  # 慢速滑动时，避免惯性滑动的最小步长
        max_steps = 200  # 最大步长，避免滑动太慢
        distance = int(((tx - fx) ** 2 + (ty - fy) ** 2) ** 0.5)  # 计算滑动距离
        if not steps:
            if duration >= 0.2:
                # 当duration大于0.2时，为慢速滑动，保持匀速，要根据滑动距离来计算滑动步长，避免惯性滑动和长按
                speed = min(12.0, max(0.5, round(23.5 - (23 * duration), 1)))  # 当duration<0.5将达到最大12的速度
                steps = min(max_steps, max(slow_min_steps, int(distance / speed)))
            else:
                # 当duration<0.2时，保持原来的duration对应的步长和滑动速度，支持快速滑动
                steps = min(max_steps, max(int(duration * 200), min_steps))
        else:
            steps = min(max_steps, max(min_steps, int(steps)))  # 防止steps为0或负数
        speed = round(distance / steps, 1)

        # 获取屏幕尺寸
        screen_width, screen_height = self.get_screen_size()  # (width, height)

        # 坐标边界保护，确保不超出屏幕
        fx = max(1, min(fx, screen_width - 2))  # 保证在[1, width-2]区间
        fy = max(1, min(fy, screen_height - 2))  # 保证在[1, height-2]区间
        tx = max(1, min(tx, screen_width - 2))
        ty = max(1, min(ty, screen_height - 2))

        if fx == tx and ty > fy:
            direction = 'down'
        elif fx == tx and ty < fy:
            direction = 'up'
        elif fy == ty and tx < fx:
            direction = 'left'
        elif fy == ty and tx > fx:
            direction = 'right'
        else:
            direction = 'diagonal'
        aklog_debug(f'swipe {direction}: ({fx}, {fy}) -> ({tx}, {ty}),'
                    f' duration: {duration}, steps: {steps}, distance: {distance}px, speed: {speed}')

        try:
            # 执行滑动操作
            self.driver.swipe(fx, fy, tx, ty, steps=steps)
            return True
        except Exception as e:
            # 捕获异常并输出详细日志
            aklog_error(f'swipe操作异常: {e}\n{traceback.format_exc()}')
            return False

    def swipe_right(self, box_ele=None, duration=0.3, length=0.5, y_offset=0.25, sec=0.1, check_safe=False):
        """
        如果box_ele如果为None或'screen', 从屏幕最左侧向右滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果box_ele有传入元素，则在元素框范围内从最左侧向右滑动
        y_offset: 滑动的位置: ly + box_height * y_offset
        """
        try:
            if box_ele is None or box_ele == 'screen':
                width, height = self.get_screen_size()
                start_x = int(width * (1 - length) / 2)
                end_x = int(width * (1 + length) / 2)
                start_y = int(height * y_offset)
                end_y = int(height * y_offset)
                bounds = None
            else:
                if isinstance(box_ele, (str, dict, tuple)):
                    box_ele = self.get_element(box_ele)
                bounds = box_ele.info.get('bounds')
                lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                bounds = (lx, ly, rx, ry)
                width = int(rx) - int(lx)
                height = int(ry) - int(ly)
                start_x = int(lx + width * (1 - length) / 2)
                start_y = int(ly + height * y_offset)
                end_x = int(lx + width * (1 + length) / 2)
                end_y = int(ly + height * y_offset)

            if check_safe:
                seekbar_rects = self.get_seekbar_rects()
                start_x, start_y = self.find_safe_start_point(
                    width, height, start_x, start_y, end_x, end_y, seekbar_rects,
                    direction="horizontal", bounds=bounds
                )
                end_y = start_y

            self.swipe(start_x, start_y, end_x, end_y, duration=duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_left(self, box_ele=None, duration=0.3, length=0.5, y_offset=0.25, sec=0.1, check_safe=False):
        """
        如果box_ele如果为None或'screen', 从屏幕最右侧向左滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果box_ele有传入元素，则在元素框范围内从最右侧向左滑动
        y_offset: 滑动的位置: ly + size['height'] * y_offset
        """
        try:
            if box_ele is None or box_ele == 'screen':
                width, height = self.get_screen_size()
                start_x = int(width * (1 + length) / 2)
                end_x = int(width * (1 - length) / 2)
                start_y = int(height * y_offset)
                end_y = int(height * y_offset)
                bounds = None
            else:
                if isinstance(box_ele, (str, dict, tuple)):
                    box_ele = self.get_element(box_ele)
                bounds = box_ele.info.get('bounds')
                lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                bounds = (lx, ly, rx, ry)
                width = int(rx) - int(lx)
                height = int(ry) - int(ly)
                start_x = int(lx + width * (1 + length) / 2)
                end_x = int(lx + width * (1 - length) / 2)
                start_y = int(ly + height * y_offset)
                end_y = int(ly + height * y_offset)

            if check_safe:
                seekbar_rects = self.get_seekbar_rects()
                start_x, start_y = self.find_safe_start_point(
                    width, height, start_x, start_y, end_x, end_y, seekbar_rects,
                    direction="horizontal", bounds=bounds
                )
                end_y = start_y

            self.swipe(start_x, start_y, end_x, end_y, duration=duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_down(self, box_ele=None, duration=0.3, length=0.5, x_offset=0.25, sec=0.1,
                   y_offset=None, check_safe=False):
        """
        如果box_ele如果为None或'screen', 从屏幕1/4处向下滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果box_ele有传入元素，则在元素框范围内从1/4处向下滑动
        :param box_ele: 要移动的元素，如果为None或'screen', 从屏幕x_offset=1/4处向下滑动；
        :param duration: 滑动时间（秒）
        :param length: 滑动距离，相对屏幕宽或高的倍数，[0-1]
        :param sec: 下滑后缓冲time.sleep指定时长
        :param x_offset: X轴滑动的位置: lx + box_width * x_offset
        :param y_offset: 可选，Y轴开始滑动的位置，为None时则使用length方式计算
        :param check_safe: 是否检查页面滑动条，滑动位置要避开滑动条，
        """
        try:
            if box_ele is None or box_ele == 'screen':
                width, height = self.get_screen_size()
                start_x = int(width * x_offset)
                start_y = int(height * (1 - length) / 2)
                end_x = int(width * x_offset)
                end_y = int(height * (1 + length) / 2)
                if y_offset is not None:  # UPDATE：用于支持滑动到页面顶端
                    start_y = int(height * y_offset)
                    end_y = int(height * (y_offset + length))
                bounds = None
            else:
                if isinstance(box_ele, (str, dict, tuple)):
                    box_ele = self.get_element(box_ele)
                bounds = box_ele.info.get('bounds')
                lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                bounds = (lx, ly, rx, ry)
                width = int(rx) - int(lx)
                height = int(ry) - int(ly)
                start_x = lx + int(width * x_offset)
                start_y = ly + int(height * (1 - length) / 2)
                end_x = lx + int(width * x_offset)
                end_y = ly + int(height * (1 + length) / 2)

            if check_safe:
                seekbar_rects = self.get_seekbar_rects()
                start_x, start_y = self.find_safe_start_point(
                    width, height, start_x, start_y, end_x, end_y, seekbar_rects,
                    direction="vertical", bounds=bounds
                )
                end_x = start_x

            self.swipe(start_x, start_y, end_x, end_y, duration=duration)
            time.sleep(sec)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def swipe_up(self, box_ele=None, duration=0.3, length=0.5, x_offset=0.25, sec=0.1, check_safe=False):
        """
        如果box_ele如果为None或'screen', 则从屏幕3/4处向上滑动，参数duration为滑动时间，length为滑动距离（相对于屏幕宽或高的倍数）
        如果box_ele有传入元素，则在元素框范围内从3/4处向上滑动
        x_offset: 滑动的位置: lx + box_width * x_offset
        """
        try:
            if box_ele is None or box_ele == 'screen':
                width, height = self.get_screen_size()
                start_x = int(width * x_offset)
                start_y = int(height * (1 + length) / 2)
                end_x = int(width * x_offset)
                end_y = int(height * (1 - length) / 2)
                bounds = None
            else:
                if isinstance(box_ele, (str, dict, tuple)):
                    box_ele = self.get_element(box_ele)
                bounds = box_ele.info.get('bounds')
                lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                bounds = (lx, ly, rx, ry)
                width = int(rx) - int(lx)
                height = int(ry) - int(ly)
                start_x = lx + int(width * x_offset)
                start_y = ly + int(height * (1 + length) / 2)
                end_x = lx + int(width * x_offset)
                end_y = ly + int(height * (1 - length) / 2)

            if check_safe:
                seekbar_rects = self.get_seekbar_rects()
                start_x, start_y = self.find_safe_start_point(
                    width, height, start_x, start_y, end_x, end_y, seekbar_rects,
                    direction="vertical", bounds=bounds
                )
                end_x = start_x

            self.swipe(start_x, start_y, end_x, end_y, duration=duration)
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
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.3)
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
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.5)
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
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            return True
        else:
            aklog_debug('%s is not found' % ele_xpath)
            return False

    def swipe_until_find_by_name(self, ele_name, box_ele=None, counts=10, length=0.5, direction='up',
                                 x_offset=0.25, near=None):
        """
        上下滑动直到找到元素并可见
        :param ele_name: 选项名称.   [也可传入入列表用于匹配多个版本不同词条翻译的情况]
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
                if isinstance(ele_name, str):
                    # 2024.12.19 lex: 补充无视大小写的设计.
                    textlist = []
                    try:
                        str1 = self.driver.dump_hierarchy()
                        textlist = list(set(re.findall('text="(.*?)"', str1)))
                    except:
                        pass
                    if not textlist:
                        ret = self.driver(text=ele_name).exists
                    else:
                        if ele_name not in textlist:
                            for text in textlist:
                                if ele_name.lower() == text.lower():
                                    ele_name = text
                                    break
                        ret = self.driver(text=ele_name).exists
                else:
                    xpath = self.get_names_expression(*ele_name)
                    ret = self.driver.xpath(xpath).exists
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
                if isinstance(ele_name, str):
                    ele_mid_x, ele_mid_y = self.driver(text=ele_name).center()
                else:
                    ele_mid_x, ele_mid_y = self.driver.xpath(self.get_names_expression(*ele_name)).center()
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
                if isinstance(ele_name, str):
                    lx, ly, rx, ry = self.driver(text=ele_name).bounds()
                else:
                    lx, ly, rx, ry = self.driver.xpath(self.get_names_expression(*ele_name)).bounds()
                if ly - box_ly > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ly
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_ly + 50
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.3)
            elif near == 'bottom':
                # 让查找的元素尽可能靠近滚动框的底部
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                if isinstance(ele_name, str):
                    lx, ly, rx, ry = self.driver(text=ele_name).bounds()
                else:
                    lx, ly, rx, ry = self.driver.xpath(self.get_names_expression(*ele_name)).bounds()
                if box_ry - ry > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ry
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_ry - 50
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.5)
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
                if isinstance(ele_name, str):
                    lx, ly, rx, ry = self.driver(text=ele_name).bounds()
                else:
                    lx, ly, rx, ry = self.driver.xpath(self.get_names_expression(*ele_name)).bounds()
                ele_mid_y = int((ly + ry) / 2)
                if abs(box_mid_y - ele_mid_y) > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ele_mid_y
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_mid_y
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            return True
        else:
            aklog_debug('%s is not found' % ele_name)
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
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.3)
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
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.5)
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
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            return True
        else:
            aklog_debug('%s is not found' % ele_xpath)
            return False

    def swipe_vertical_until_find_by_id(self, ele_id, box_ele=None, counts=10, length=0.5, direction='up',
                                        x_offset=0.25, near=None):
        """
        垂直方向，上下滑动直到找到元素并可见
        :param ele_id: 选项id
        :param box_ele: 默认None表示整个屏幕上下滑动，可以指定元素框，可以先用get_element_by_id方法获取元素
        :param counts: 设置上滑或下滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最顶端滚动到最低端
        :param length: 手指上滑的距离占元素框的比例
        :param direction: 先上滑还是下滑，up or down
        :param x_offset: 滑动的相对位置: 0-1
        :param near: 靠近顶部或底部，默认为None找到即可，top表示查找的元素尽可能靠近顶部，bottom表示靠近底部，并且最好传入box_ele
        """
        aklog_debug()
        ret = False
        i = 0
        while i < counts * 3 + 1:
            try:
                ret = self.driver(resourceId=ele_id).exists
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
                ele_mid_x, ele_mid_y = self.driver(resourceId=ele_id).center()
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
                lx, ly, rx, ry = self.driver(resourceId=ele_id).bounds()
                if ly - box_ly > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ly
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_ly + 50
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.3)
            elif near == 'bottom':
                # 让查找的元素尽可能靠近滚动框的底部
                if box_ele is not None:
                    box_bounds = box_ele.info.get('bounds')
                    box_lx, box_ly = box_bounds['left'], box_bounds['top']
                    box_rx, box_ry = box_bounds['right'], box_bounds['bottom']
                else:
                    box_lx, box_ly = 0, 0
                    box_rx, box_ry = self.get_screen_size()
                lx, ly, rx, ry = self.driver(resourceId=ele_id).bounds()
                if box_ry - ry > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ry
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_ry - 50
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.5)
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
                lx, ly, rx, ry = self.driver(resourceId=ele_id).bounds()
                ele_mid_y = int((ly + ry) / 2)
                if abs(box_mid_y - ele_mid_y) > 50:
                    box_width = int(box_rx) - int(box_lx)
                    start_x = box_lx + int(box_width * x_offset)
                    start_y = ele_mid_y
                    end_x = box_lx + int(box_width * x_offset)
                    end_y = box_mid_y
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            return True
        else:
            aklog_debug('%s is not found' % ele_id)
            return False

    def scroll_horizontal_until_find_by_name(self, ele_name, box_ele=None, counts=10, length=0.5, direction='left',
                                             y_offset=0.25, near=None):
        """
        上下滑动直到找到元素并可见
        :param ele_name: 选项名称
        :param box_ele: 默认None表示整个屏幕左右滑动，可以指定元素框，可以先用get_element_by_id方法获取元素
        :param counts: 设置左滑或右滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最左端滚动到最右端
        :param length: 手指左滑的距离占元素框的比例
        :param direction: 先左滑还是右滑，left or right
        :param y_offset: 滑动的相对位置: 0-1
        :param near: 靠近最左边或最右边，默认为None找到即可，top表示查找的元素尽可能靠近顶部，bottom表示靠近底部，center表示靠近中间
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
                direction = 'right' if direction == 'left' else 'left'  # 如果先上滑没找到时改为下滑，反之先下滑没找到时改为上滑

            if direction == 'left':
                self.swipe_left(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset)
            else:
                self.swipe_right(box_ele=box_ele, duration=0.3, length=length, y_offset=y_offset)
            i += 1
            continue

        if ret:
            # 先滚动元素到可点击区域
            if self.screen_clickable_area:
                ele_mid_x, ele_mid_y = self.driver(text=ele_name).center()
                if ele_mid_y <= self.screen_clickable_area[1]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_right(box_ele, duration=0.3, length=0.1, y_offset=y_offset)
                elif ele_mid_y >= self.screen_clickable_area[3]:
                    aklog_debug('元素中心点坐标 (%s, %s) 超出了可点击范围，需要再滑动一点' % (ele_mid_x, ele_mid_y))
                    self.swipe_left(box_ele, duration=0.3, length=0.1, y_offset=y_offset)

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
                    start_x = box_lx + int(box_width * y_offset)
                    start_y = ly
                    end_x = box_lx + int(box_width * y_offset)
                    end_y = box_ly + 50
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.3)
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
                    start_x = box_lx + int(box_width * y_offset)
                    start_y = ry
                    end_x = box_lx + int(box_width * y_offset)
                    end_y = box_ry - 50
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.5)
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
                    start_x = box_lx + int(box_width * y_offset)
                    start_y = ele_mid_y
                    end_x = box_lx + int(box_width * y_offset)
                    end_y = box_mid_y
                    self.swipe(start_x, start_y, end_x, end_y, duration=0.5)
            return True
        else:
            aklog_debug('%s is not found' % ele_name)
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
        return False

    def swipe_horizontal_until_find_by_id(self, ele_id, box_ele=None, counts=10, length=0.5, direction='left',
                                          y_offset=0.25):
        """
        左右滑动直到找到元素并可见
        :param ele_id: 选项id
        :param box_ele: 默认None表示整个屏幕左右滑动，可以指定元素框，可以先用get_element_by_id方法获取元素
        :param counts: 设置左滑或右滑的次数，如果列表选项比较多，counts需要设置的比较大，确保可以从最左边滚动到最右边
        :param length: 手指左滑的距离占元素框的比例
        :param direction: 先左滑还是右滑，left or right
        :param y_offset: 滑动的相对位置: 0-1
        """
        aklog_debug()
        for i in range(0, counts + 1):
            try:
                ret = self.driver(resourceId=ele_id).exists
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
                ret = self.driver(resourceId=ele_id).exists
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
        aklog_debug('%s is not found' % ele_id)
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
        return False

    def two_finger_gesture(self, start1, start2, end1, end2, steps=100):
        """
        两指手势滑动
        start1, start2, end1, end2：元组类型， (100, 100), (150, 100), (100, 300), (150, 300)
        """
        self.driver().gesture(start1, start2, end1, end2, steps=steps)

    def scroll_to_name(self, ele_name, box_ele_xpath=None):
        """滚动到元素可见，该方法滚动会比较慢"""
        if box_ele_xpath:
            self.driver.xpath(box_ele_xpath).scroll_to(ele_name)
        else:
            self.driver.xpath.scroll_to(ele_name)

    def swipe_points(self, points, duration=0.5):
        """
        多用于九宫格解锁，提前获取到每个点的相对坐标（这里支持百分比）
        points: [(x0, y0), (x1, y1), (x2, y2)]
        duration: 每一次滑动时间
        """
        aklog_debug()
        self.driver.swipe_points(points, duration)

    def adb_input_swipe(self, fx, fy, tx, ty, duration=2000):
        """使用adb shell input swipe方式滑动"""
        # 区域保护, 避免超出区域
        screen_width, screen_height = self.get_screen_size()
        fx = max(1, min(fx, screen_width - 2))  # 保证在[1, width-2]区间
        fy = max(1, min(fy, screen_height - 2))  # 保证在[1, height-2]区间
        tx = max(1, min(tx, screen_width - 2))
        ty = max(1, min(ty, screen_height - 2))
        aklog_debug('swipe: (%s, %s) -> (%s, %s), duration: %s' % (fx, fy, tx, ty, duration))
        for i in range(0, 3):
            try:
                cmd = f'input swipe {fx} {fy} {tx} {ty} {duration}'
                self.shell(cmd)
            except:
                aklog_debug('遇到未知异常, 程序退出! ' + str(traceback.format_exc()))
            else:
                return True
            time.sleep(1)
        return False

    def get_seekbar_rects(self, bounds=None):
        """
        获取页面或指定区域内所有滑动条的矩形区域
        Args:
            bounds (tuple): (top, bottom)或(left, right)，用于限定区域，None为全屏
        Returns:
            list: [(lx, ly, rx, ry), ...]
        """
        seekbar_rects = []
        try:
            # 这里只以android.widget.SeekBar为例，实际可根据项目补充Slider等自定义控件
            seekbars = self.driver.xpath(
                '//*[name()="android.widget.SeekBar" or name()="android.widget.Slider"]').all()
            for sb in seekbars:
                info = sb.info
                b = info.get('bounds', {})
                lx, ly, rx, ry = b.get('left', 0), b.get('top', 0), b.get('right', 0), b.get('bottom', 0)
                if bounds:
                    # 如果有区域限定，只保留在区域内的滑动条
                    if ry < bounds[0] or ly > bounds[1]:
                        continue
                seekbar_rects.append((lx, ly, rx, ry))
        except Exception as e:
            aklog_warn(f"获取滑动条区域异常: {e}")
        return seekbar_rects

    @staticmethod
    def is_point_in_rects(x, y, rects):
        """
        判断点(x, y)是否落在任意一个矩形区域内
        Args:
            x (int): X坐标
            y (int): Y坐标
            rects (list): [(lx, ly, rx, ry), ...]
        Returns:
            bool: True-在区域内，False-不在
        """
        for lx, ly, rx, ry in rects:
            if lx <= x <= rx and ly <= y <= ry:
                return True
        return False

    def find_safe_start_point(
            self,
            width: int,
            height: int,
            start_x: int,
            start_y: int,
            end_x: int,
            end_y: int,
            seekbar_rects: list,
            direction: str = "horizontal",
            min_gap: int = 20,
            bounds: tuple = None  # 新增参数，限定滑动区域(left, top, right, bottom)
    ) -> tuple:
        """
        动态查找不落在滑动条区域内的安全起始点，支持横滑/竖滑，支持限定滑动区域。
        """
        # aklog_debug()
        # 处理限定区域
        if bounds:
            lx, ly, rx, ry = bounds
            min_x, max_x = lx + min_gap, rx - min_gap
            min_y, max_y = ly + min_gap, ry - min_gap
        else:
            min_x, max_x = min_gap, width - min_gap
            min_y, max_y = min_gap, height - min_gap

        # 优先尝试默认点
        if not self.is_point_in_rects(start_x, start_y, seekbar_rects) \
                and min_x <= start_x <= max_x and min_y <= start_y <= max_y:
            return start_x, start_y

        if direction == "horizontal":
            # 优先上下偏移y
            for offset in range(min_gap, int((max_y - min_y) * 0.4), 10):
                # 向上偏移
                new_y = max(start_y - offset, min_y)
                if (not self.is_point_in_rects(start_x, new_y, seekbar_rects)
                        and min_y <= new_y <= max_y):
                    return start_x, new_y
                # 向下偏移
                new_y = min(start_y + offset, max_y)
                if (not self.is_point_in_rects(start_x, new_y, seekbar_rects)
                        and min_y <= new_y <= max_y):
                    return start_x, new_y
            # 再左右偏移x
            for offset in range(min_gap, int((max_x - min_x) * 0.4), 10):
                new_x = max(start_x - offset, min_x)
                if (abs(new_x - end_x) > min_gap
                        and not self.is_point_in_rects(new_x, start_y, seekbar_rects)
                        and min_x <= new_x <= max_x):
                    return new_x, start_y
                new_x = min(start_x + offset, max_x)
                if (abs(new_x - end_x) > min_gap
                        and not self.is_point_in_rects(new_x, start_y, seekbar_rects)
                        and min_x <= new_x <= max_x):
                    return new_x, start_y
        elif direction == "vertical":
            # 优先左右偏移x
            for offset in range(min_gap, int((max_x - min_x) * 0.4), 10):
                new_x = max(start_x - offset, min_x)
                if (not self.is_point_in_rects(new_x, start_y, seekbar_rects)
                        and min_x <= new_x <= max_x):
                    return new_x, start_y
                new_x = min(start_x + offset, max_x)
                if (not self.is_point_in_rects(new_x, start_y, seekbar_rects)
                        and min_x <= new_x <= max_x):
                    return new_x, start_y
            # 再上下偏移y
            for offset in range(min_gap, int((max_y - min_y) * 0.4), 10):
                new_y = max(start_y - offset, min_y)
                if (abs(new_y - end_y) > min_gap
                        and not self.is_point_in_rects(start_x, new_y, seekbar_rects)
                        and min_y <= new_y <= max_y):
                    return start_x, new_y
                new_y = min(start_y + offset, max_y)
                if (abs(new_y - end_y) > min_gap
                        and not self.is_point_in_rects(start_x, new_y, seekbar_rects)
                        and min_y <= new_y <= max_y):
                    return start_x, new_y

        # 实在找不到，返回区域中心
        aklog_warn("未找到安全的滑动起始点，使用区域中心")
        return int((min_x + max_x) / 2), int((min_y + max_y) / 2)

    # endregion

    # region 元素是否存在或可见，等待元素出现或消失

    def is_exist_ele_by_xpath(self, ele_xpath, wait_time=None):
        """判断元素是否存在"""
        aklog_debug()
        if ele_xpath.startswith('.//'):
            ele_xpath = ele_xpath[1:]
        if ele_xpath.startswith('(.//'):
            ele_xpath = '(' + ele_xpath[2:]
        try:
            if not wait_time:
                wait_time = self.wait_time
            ret = self.driver.xpath(ele_xpath).wait(timeout=wait_time)
            if not ret:
                aklog_debug('%s is not exist' % ele_xpath)
                return False
            else:
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
            ret = self.driver.xpath(ele_xpath).wait(timeout=wait_time)
            if not ret:
                aklog_debug('%s is not exist' % ele_xpath)
                return False
            else:
                return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def is_exist_ele_by_id(self, ele_id, wait_time=None, print_trace=True):
        """判断元素是否存在"""
        aklog_debug()
        try:
            if not wait_time:
                wait_time = self.wait_time
            ret = self.driver(resourceId=ele_id).wait(timeout=wait_time)
            if not ret:
                aklog_debug('%s is not exist' % ele_id)
            return ret
        except Exception as e:
            if print_trace or not e:
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
                return False
            else:
                return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def is_exist_ele_by_desc(self, desc, wait_time=None):
        """判断元素是否存在"""
        aklog_debug()
        try:
            if not wait_time:
                wait_time = self.wait_time
            ret = self.driver(description=desc).wait(timeout=wait_time)
            if not ret:
                aklog_debug('%s is not exist' % desc)
            return ret
        except:
            aklog_debug(traceback.format_exc())
            return False

    def wait_for_visible_by_id(self, ele_id, timeout=5):
        """等待元素出现"""
        aklog_debug()
        try:
            ret = self.driver(resourceId=ele_id).wait(timeout=timeout)
            if not ret:
                aklog_debug('%s is not found' % ele_id)
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
                return False
            return True
        except:
            aklog_debug(traceback.format_exc())
            return False

    def wait_for_disappear_by_id(self, ele_id, timeout=5):
        """等待元素消失"""
        aklog_debug()
        try:
            ret = self.driver(resourceId=ele_id).wait_gone(timeout=timeout)
            if not ret:
                aklog_debug('%s is not disappear' % ele_id)
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

    def get_text(self, locator, timeout=None, print_trace=False) -> Optional[str]:
        """获取控件文本，如果text为空，会获取content-desc"""
        aklog_debug()
        try:
            ele = self.get_element(locator, timeout=timeout)
            if ele is None:
                return None

            if isinstance(ele, UiObject):
                text = ele.get_text()
                desc = ele.info.get('content-desc', '')
            else:
                text = ele.text
                desc = ele.attrib.get('content-desc', '')
            if desc and not text:
                text = desc
                aklog_debug("content-desc : %s" % text)
            else:
                aklog_debug("text : %s" % text)
            return text
        except Exception as e:
            aklog_error(e)
            if print_trace or not e:
                aklog_debug(str(traceback.format_exc()))
            return None

    def get_desc(self, locator, timeout=None, print_trace=False) -> Optional[str]:
        """获取控件content-desc文本"""
        aklog_debug()
        try:
            ele = self.get_element(locator, timeout=timeout)
            if ele is None:
                return None

            if isinstance(ele, UiObject):
                desc = ele.info.get('content-desc', '')
            else:
                desc = ele.attrib.get('content-desc', '')
            aklog_debug("content-desc : %s" % desc)
            return desc
        except Exception as e:
            aklog_error(e)
            if print_trace or not e:
                aklog_debug(str(traceback.format_exc()))
            return None

    def get_attr(self, locator, attr_type, timeout=None) -> Optional[str]:
        """
        1、attr_type：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、password、selected，返回的是true和false的str类型
        2、.get("name")  返回的是‘content-desc’的值
        3、.get("className")  返回的是‘class’的值
        """
        try:
            ele = self.get_element(locator, timeout=timeout)
            if ele is None:
                return None

            if isinstance(ele, UiObject):
                value = ele.info.get(attr_type)
            else:
                value = ele.attrib.get(attr_type)
            aklog_debug('locator: %s, attribute: %s, value: %s' % (locator, attr_type, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def is_enabled(self, locator) -> Optional[bool]:
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

    def get_ele_counts(self, locator) -> int:
        """获取相同定位信息元素的数量"""
        aklog_debug()
        try:
            ele = self.find_element(locator)
            if ele is None:
                return 0
            if isinstance(ele, UiObject):
                counts = ele.count
            else:
                counts = len(ele.all())
            aklog_debug('counts: %s' % counts)
            return counts
        except:
            aklog_debug(str(traceback.format_exc()))
            return 0

    def get_texts(self, locator, timeout=None) -> List[str]:
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
            ele = self.find_element(locator, timeout=timeout)
            if ele is None:
                return []
            texts = []
            elements = ele.all()
            for element in elements:
                texts.append(element.text)
            aklog_debug("texts : %s" % texts)
            return texts
        except:
            aklog_debug(str(traceback.format_exc()))
            return []

    @staticmethod
    def get_id_list_expression(id_list_str):
        """多个ID组成Xpath，一般用于不同版本或机型兼容"""
        xpath = '//*['
        id_list = [i.strip() for i in id_list_str.split('|')]
        for ele_id in id_list:
            xpath = xpath + '@resource-id="{}"'.format(ele_id)
            xpath = xpath + ' or '
        xpath = xpath.rstrip(' or ') + ']'
        return xpath

    @staticmethod
    def get_names_expression(*ele_names):
        """多个name组成Xpath，一般用于不同版本或机型兼容"""
        ele_xpath = '//*['
        for x in ele_names:
            ele_xpath += '@text="%s" or ' % x
        ele_xpath = ele_xpath.rstrip(' or ') + ']'
        return ele_xpath

    def get_ele_info_by_id(self, ele_id):
        try:
            return self.driver(resourceId=ele_id).info
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_ele_info_by_xpath(self, xpath):
        try:
            return self.driver.xpath(xpath).info
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_value_by_id(self, ele_id, timeout=None, print_trace=True):
        """
        eleID:
            str.  支持输入多个ID, 同时or匹配,  用'|' 分隔
            eg:
                get_value_by_id('com.akuvox.phone:id/tv_group_child_name | com.akuvox.phone:id/tv_group_name')
        """
        aklog_debug()
        try:
            if timeout is not None:
                timeout = self.wait_time
            if '|' not in ele_id:
                value = self.driver(resourceId=ele_id).get_text(timeout)
                aklog_debug("text : %s" % value)
                return value
            else:
                ele_xpath = self.get_id_list_expression(ele_id)
                value = self.driver.xpath(ele_xpath).get(timeout).text
                aklog_debug("text : %s" % value)
                return value
        except Exception as e:
            aklog_warn('get value failed by id: %s' % ele_id)
            if print_trace or not e:
                aklog_debug(str(traceback.format_exc()))
            return None

    def get_value_by_xpath(self, ele_xpath, timeout=None, print_trace=True):
        aklog_debug()
        if ele_xpath.startswith('.//'):
            ele_xpath = ele_xpath[1:]
        if ele_xpath.startswith('(.//'):
            ele_xpath = '(' + ele_xpath[2:]
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
        except Exception as e:
            aklog_warn('get value failed by xpath: %s' % ele_xpath)
            if print_trace or not e:
                aklog_debug(str(traceback.format_exc()))
            return None

    def get_values_by_xpath(self, ele_xpath):
        """获取多个相同Xpath的元素文本列表"""
        aklog_debug()
        if ele_xpath.startswith('.//'):
            ele_xpath = ele_xpath[1:]
        if ele_xpath.startswith('(.//'):
            ele_xpath = '(' + ele_xpath[2:]
        try:
            values = []
            self.driver.xpath(ele_xpath).wait(timeout=3)
            elements = self.driver.xpath(ele_xpath).all()
            for ele in elements:
                values.append(ele.text)
            aklog_debug("texts : %s" % values)
            return values
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_values_by_id(self, ele_id):
        """
        eleID:
            str.  支持输入多个ID, 同时or匹配,  用'|' 分隔
            eg:
                get_values_by_id('com.akuvox.phone:id/tv_group_child_name | com.akuvox.phone:id/tv_group_name')
        """
        aklog_debug()
        values = []
        try:
            ele_xpath = self.get_id_list_expression(ele_id)
            self.driver.xpath(ele_xpath).wait(timeout=3)
            ele_list = self.driver.xpath(ele_xpath).all()
            for ele in ele_list:
                values.append(ele.text)
            aklog_debug("texts : %s" % values)
            return values
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_values_by_same_prefix_id(self, ele_id):
        """输入部分id内容, 获取包括该ID的元素内容"""
        aklog_debug("get_values_by_same_prefix_id : %s" % ele_id)
        ele_xpath = '//*[contains(@resource-id, "{}")]'.format(ele_id)
        try:
            self.driver.xpath(ele_xpath).wait(timeout=3)
            ele_lists = self.driver.xpath(ele_xpath).all()
            if ele_lists is None:
                aklog_debug('No found elements with prefix id: %s' % ele_id)
                return []
            values = [ele.text for ele in ele_lists if ele.text]
            aklog_debug("%s, texts: %s" % (ele_xpath, str(values)))
            return values
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_counts_by_xpath(self, ele_xpath):
        """获取相同Xpath元素的数量"""
        aklog_debug()
        try:
            self.driver.xpath(ele_xpath).wait(timeout=3)
            elements = self.driver.xpath(ele_xpath).all()
            counts = len(elements)
            aklog_debug('counts: %s' % counts)
            return counts
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_counts_by_id(self, ele_id):
        """获取相同id元素的数量"""
        aklog_debug()
        try:
            counts = self.driver(resourceId=ele_id).count
            aklog_debug('counts: %s' % counts)
            return counts
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_by_xpath(self, ele_xpath, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、password、selected，返回的是true和false的str类型
        2、.get("name")  返回的是‘content-desc’的值
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

    def get_attribute_by_id(self, ele_id, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、password、selected，返回的是true和false的str类型
        2、.get("name")  返回的是‘content-desc’的值
        3、.get("className")  返回的是‘class’的值
        """
        try:
            ele = self.driver(resourceId=ele_id)
            value = ele.info.get(attribute_type)
            aklog_debug('eleId: %s, attribute: %s, value: %s' % (ele_id, attribute_type, value))
            return value
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_attribute_by_name(self, ele_name, attribute_type):
        """
        1、attribute_type可以选择：checkable、checked、clickable、enabled、focusable、focused、scollable、long-clickable、password、selected，返回的是true和false的str类型
        2、.get("name")  返回的是‘content-desc’的值
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

    def is_enabled_by_id(self, ele_id):
        """
        判断控件是否可以操作
        return: boolean类型, True or False
        """
        aklog_debug('is_enabled_by_id: %s' % ele_id)
        try:
            ele = self.driver(resourceId=ele_id)
            enabled = ele.info.get('enabled')
            aklog_debug('enabled: %s' % enabled)
            return enabled
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def is_enabled_by_xpath(self, elexpath):
        """
        判断控件是否可以操作
        return: boolean类型, True or False
        """
        aklog_debug()
        try:
            ele = self.driver.xpath(elexpath)
            enabled = ele.info.get('enabled')
            aklog_debug('enabled: %s' % enabled)
            return enabled
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def wait_for_clickable_by_id(self, ele_id, timeout=5):
        """等待控件可点击"""
        aklog_debug()
        try:
            ele = self.driver(resourceId=ele_id)
            end_time = time.time() + timeout
            while time.time() < end_time:
                clickable = ele.info.get('clickable')
                if clickable is True or clickable == 'true':
                    return True
            aklog_error('%s 未变成可点击状态' % ele_id)
            return False
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    @staticmethod
    def get_element_parent_xpath(element):
        """获取元素的父节点Xpath信息"""
        try:
            parent_xpath = element.parent().get_xpath()
            return parent_xpath
        except:
            aklog_debug(traceback.format_exc())
            return None

    # endregion

    # region 获取元素或屏幕尺寸、位置

    def get_ele_size(self, locator):
        """获取元素的大小（宽和高）"""
        try:
            ele = self.get_element(locator)
            if ele is None:
                return 0, 0

            if isinstance(ele, UiObject):
                lx, ly, rx, ry = ele.bounds()
            else:
                lx, ly, rx, ry = ele.bounds
            ele_width = int(rx) - int(lx)
            ele_height = int(ry) - int(ly)
            aklog_debug('get_ele_size, locator: %s, width: %s, height: %s' % (
                locator, ele_width, ele_height))
            return ele_width, ele_height
        except Exception as e:
            aklog_error(e)
            return 0, 0

    def get_ele_location(self, locator):
        """获取元素的位置(左上角的坐标)"""
        try:
            ele = self.get_element(locator)
            if ele is None:
                return None

            if isinstance(ele, UiObject):
                lx, ly, rx, ry = ele.bounds()
            else:
                lx, ly, rx, ry = ele.bounds
            ele_location = {'x': lx, 'y': ly}
            aklog_debug('get_ele_location, locator: %s, location: %s' % (locator, ele_location))
            return ele_location
        except Exception as e:
            aklog_error(e)
            return None

    def get_ele_rect(self, locator):
        """获取元素尺寸和位置信息: x, y, width, height"""
        try:
            ele = self.get_element(locator)
            if ele is None:
                return None

            if isinstance(ele, UiObject):
                lx, ly, rx, ry = ele.bounds()
            else:
                lx, ly, rx, ry = ele.bounds
            rect = {'x': lx,
                    'y': ly,
                    'width': int(rx) - int(lx),
                    'height': int(ry) - int(ly)}
            aklog_debug('get_ele_rect, locator: %s, rect: %s' % (locator, rect))
            return rect
        except Exception as e:
            aklog_error(e)
            return None

    def get_ele_bounds(self, locator) -> Tuple[int, int, int, int]:
        """获取元素左上角和左下角坐标: lx, ly, rx, ry"""
        try:
            ele = self.get_element(locator)
            if ele is None:
                return 0, 0, 0, 0

            if isinstance(ele, UiObject):
                lx, ly, rx, ry = ele.bounds()
            else:
                lx, ly, rx, ry = ele.bounds
            return lx, ly, rx, ry
        except Exception as e:
            aklog_error(e)
            return 0, 0, 0, 0

    def get_ele_center(self, locator):
        """
        获取元素的位置(中心点的坐标)
        :param locator: 元素定位
        :return: dict类型
        """
        try:
            ele = self.get_element(locator)
            ele_mid_x, ele_mid_y = ele.center()
            return ele_mid_x, ele_mid_y
        except:
            aklog_debug(str(traceback.format_exc()))
            return None, None

    def get_ele_size_by_xpath(self, ele_xpath):
        """获取元素的大小（宽和高）"""
        aklog_debug()
        try:
            ele = self.driver.xpath(ele_xpath).get()
            lx, ly, rx, ry = ele.bounds
            ele_width = int(rx) - int(lx)
            ele_height = int(ry) - int(ly)
            return ele_width, ele_height
        except:
            return 0, 0

    def get_ele_size_by_id(self, ele_id):
        """获取元素的大小（宽和高）"""
        try:
            ele = self.driver(resourceId=ele_id)
            lx, ly, rx, ry = ele.bounds()
            ele_width = int(rx) - int(lx)
            ele_height = int(ry) - int(ly)
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
                screen_width, screen_height = self.driver.window_size()
            except:
                screen_width = 0
                screen_height = 0

            self.screen_width = screen_width
            self.screen_height = screen_height
            aklog_debug('screen_size: %s, %s' % (self.screen_width, self.screen_height))
        return self.screen_width, self.screen_height

    def get_ele_location_by_xpath(self, ele_xpath):
        """获取元素的位置(左上角的坐标)"""
        try:
            ele = self.driver.xpath(ele_xpath).get()
            lx, ly, rx, ry = ele.bounds
            ele_location = {'x': lx, 'y': ly}
            aklog_debug('get_ele_location_by_xpath, ele_xpath: %s, location: %s' % (ele_xpath, ele_location))
            return ele_location
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_location_by_id(self, ele_id):
        """获取元素的位置(左上角的坐标)"""
        try:
            ele = self.driver(resourceId=ele_id)
            lx, ly, rx, ry = ele.bounds()
            ele_location = {'x': lx, 'y': ly}
            aklog_debug('get_ele_location_by_id, ele_id: %s, location: %s' % (ele_id, ele_location))
            return ele_location
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_mid_location_by_xpath(self, ele_xpath):
        """
        获取元素的位置(中心点的坐标)
        :param ele_xpath: 元素xpath
        :return: dict类型
        """
        try:
            ele = self.driver.xpath(ele_xpath).get()
            ele_mid_x, ele_mid_y = ele.center()
            ele_location = {'x': int(ele_mid_x), 'y': int(ele_mid_y)}
            aklog_debug('%s mid location: (%s, %s)' % (ele_xpath, int(ele_mid_x), int(ele_mid_y)))
            return ele_location
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_mid_location_by_name(self, ele_name):
        """
        获取元素的位置(中心点的坐标)
        :param ele_name: 元素ele_name
        :return: bool类型
        """
        try:
            ele = self.driver(text=ele_name)
            ele_mid_x, ele_mid_y = ele.center()
            ele_location = {'x': int(ele_mid_x), 'y': int(ele_mid_y)}
            aklog_debug('%s mid location: (%s, %s)' % (ele_name, int(ele_mid_x), int(ele_mid_y)))
            return ele_location
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_rect_by_id(self, ele_id):
        """获取元素尺寸和位置信息: x, y, width, height"""
        try:
            ele = self.driver(resourceId=ele_id)
            lx, ly, rx, ry = ele.bounds()
            rect = {'x': lx,
                    'y': ly,
                    'width': int(rx) - int(lx),
                    'height': int(ry) - int(ly)}
            aklog_debug('get_ele_rect_by_id, ele_id: %s, rect: %s' % (ele_id, rect))
            return rect
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    def get_ele_rect_by_xpath(self, ele_xpath):
        """获取元素尺寸和位置信息: x, y, width, height"""
        try:
            ele = self.driver.xpath(ele_xpath).get()
            lx, ly, rx, ry = ele.bounds
            rect = {'x': lx,
                    'y': ly,
                    'width': int(rx) - int(lx),
                    'height': int(ry) - int(ly)}
            aklog_debug('get_ele_rect_by_xpath, ele_xpath: %s, rect: %s' % (ele_xpath, rect))
            return rect
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    # endregion

    # region 获取元素

    def get_element_by_id(self, ele_id):
        aklog_debug()
        try:
            element = self.driver(resourceId=ele_id)
            if element.wait(timeout=self.wait_time):
                return element
            aklog_warn('控件: {} 不存在'.format(ele_id))
            return None
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
            self.driver.xpath(ele_xpath).wait(timeout=3)
            elements = self.driver.xpath(ele_xpath).all()
            return elements
        except:
            aklog_debug(str(traceback.format_exc()))
            return None

    # endregion

    # region 截图、录屏相关

    def screen_shot_as_base64(self, re_shot=True):
        """保存屏幕截图成base64编码，用于嵌入到HTML测试报告"""
        aklog_debug('screen_shot_as_base64, the screenshots is shown below: ')
        return self.image.screenshots_as_base64(re_shot)

    def screen_shot(self, re_shot=True):
        """截图,用于外部调用"""
        img_base64 = self.screen_shot_as_base64(re_shot)
        if img_base64:
            param_append_screenshots_imgs(img_base64)
        else:
            param_append_screenshots_imgs('')

    def save_screen_shot_to_file(self, image_path=None, remove_first=True):
        """
        保存整个屏幕截图
        ps:
            2025.5.21 在安卓门口机上验证, U2方式截图有所磨损,appium方式高清, 工程已有的图片比较会失败.
            R29V3_5: 工程图片都换成U2.
            其他: 使用IntercomBase-image_compare对比图片, 接口里使用adb截图保持高清.
        """
        if not image_path:
            image_path = root_path + '\\image.png'
        if remove_first:
            File_process.remove_file(image_path)
        aklog_debug('save_screen_shot_to_file: %s' % image_path)
        self.driver.screenshot(image_path)
        return image_path

    def save_element_image(self, locator, image_path=None):
        """
        保存元素图片

        ps:
            2025.5.21 在安卓门口机上验证, U2方式截图有所磨损,appium方式高清, 工程已有的图片比较会失败.
            R29V3_5: 工程图片都换成U2.
            其他: 使用IntercomBase-image_compare对比图片, 接口里使用adb截图保持高清.
        """
        aklog_debug()
        if not image_path:
            image_path = root_path + '\\image.png'
        ele = self.find_element(locator)
        if ele is None:
            return None
        try:
            ele.screenshot().save(image_path)
            return True
        except Exception as e:
            aklog_warn(e)
            return False

    def save_element_image_by_id(self, ele_id, image_path=None):
        """
        ps:
            2025.5.21 在安卓门口机上验证, U2方式截图有所磨损,appium方式高清, 工程已有的图片比较会失败.
            R29V3_5: 工程图片都换成U2.
            其他: 使用IntercomBase-image_compare对比图片, 接口里使用adb截图保持高清.
        """
        if not image_path:
            image_path = root_path + '\\image.png'
        aklog_debug()
        File_process.remove_file(image_path)
        self.driver(resourceId=ele_id).screenshot().save(image_path)
        return image_path

    def save_element_image_by_xpath(self, ele_xpath, image_path=None):
        """
        ps:
            2025.5.21 在安卓门口机上验证, U2方式截图有所磨损,appium方式高清, 工程已有的图片比较会失败.
            R29V3_5: 工程图片都换成U2.
            其他: 使用IntercomBase-image_compare对比图片, 接口里使用adb截图保持高清.
        """
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

    def screen_record_start(self, filename=None, time_limit=None):
        """屏幕录制，使用安卓自带命令"""
        aklog_debug()
        if time_limit:
            cmd = 'screenrecord /sdcard/tmp/%s --time-limit %s' % (filename, time_limit)
        else:
            cmd = 'screenrecord /sdcard/tmp/%s' % filename
        self.shell(cmd)

    def screen_record_stop(self):
        """停止录制"""
        aklog_debug()
        self.shell('am broadcast -a com.android.server.scrcmd.stoprecord')

    # endregion

    # region 图片对比，图像检查

    def check_image_rgb(self, locator, ratio, fix_rgb):
        """检查元素图像某种颜色占比"""
        aklog_debug()
        try:
            element = self.find_element(locator)
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

    def check_image_rgbs(self, locator, ratio, *fix_rgbs, save_path=None):
        """检查元素图像某几种颜色总共占比"""
        aklog_debug()
        try:
            element = self.find_element(locator)
            if not element:
                return None
            value = self.image.check_screen_colors(*fix_rgbs, element=element, save_path=save_path)
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

    def is_pure_color(self, locator, percent, save_path=None, re_shot=True):
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
                return self.image.is_pure_color(
                    element=element, percent=percent, save_path=save_path, re_shot=re_shot)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_normal_color(self, locator, threshold=10, save_path=None, re_shot=True):
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
                element=element, threshold=threshold, save_path=save_path, re_shot=re_shot)
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

    def is_light_color(self, locator, rgb_sum=300, percent=0.5, save_path=None):
        """检查图片是否为浅色，当rgb三个数值相加大于rgb_sum，占比超过percent时，认为是浅色"""
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            return self.image.is_light_color(
                element=element, rgb_sum=rgb_sum, percent=percent, save_path=save_path)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_similar_color(self, locator, color: Union[list, str] = None, lower_hsv=None, upper_hsv=None,
                         threshold=0.1, save_path=None) -> Optional[bool]:
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
            color (list or str): red/blue/green/orange/yellow/purple
            lower_hsv (list): [90, 50, 0]
            upper_hsv (list): [140, 255, 255]
            threshold (float): 颜色占比阈值
            save_path (str): 保存图片路径
        """
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            return self.image.is_similar_color(
                element=element, color=color, lower_hsv=lower_hsv, upper_hsv=upper_hsv,
                threshold=threshold, save_path=save_path)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_rgb_by_location(self, x, y):
        return self.image.get_rgb_by_location(x, y)

    def check_rgb_sum(self, locator, rgb_sum=300, save_path=None):
        """
        获取rgb_sum占比
        rgb_sum: rgb三种数值相加
        """
        aklog_debug()
        try:
            element = self.get_element(locator)
            if not element:
                return None
            return self.image.check_rgb_sum(element=element, rgb_sum=rgb_sum, save_path=save_path)
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

    def is_pure_color_by_id(self, ele_id, percent, save_path=None):
        """
        判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色
        save_path: 将截图数据保存到文件
        """
        aklog_debug()
        try:
            element = self.get_element_by_id(ele_id)
            if not element:
                aklog_debug('%s is not found' % ele_id)
                return None
            else:
                return self.image.is_pure_color(element=element, percent=percent, save_path=save_path)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_pure_color_by_xpath(self, ele_xpath, percent, save_path=None):
        """
        判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色
        save_path: 将截图数据保存到文件
        """
        aklog_debug()
        try:
            element = self.get_element_by_xpath(ele_xpath)
            if not element:
                aklog_debug('%s is not found' % ele_xpath)
                return None
            else:
                return self.image.is_pure_color(element=element, percent=percent, save_path=save_path)
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

    def is_normal_color_by_id(self, ele_id, threshold=10, save_path=None):
        """
        用OpenCV方式检查画面是否正常
        save_path: 将截图数据保存到文件
        """
        aklog_debug()
        try:
            element = self.get_element_by_id(ele_id)
            if not element:
                aklog_debug('%s is not found' % ele_id)
                return None
            return self.image.check_video_image_is_normal(
                element=element, threshold=threshold, save_path=save_path)
        except:
            aklog_debug(traceback.format_exc())
            return None

    def is_normal_color_by_xpath(self, ele_xpath, threshold=10, save_path=None):
        """
        用OpenCV方式检查画面是否正常（XPATH）
        save_path: 将截图数据保存到文件
        """
        aklog_debug()
        try:
            element = self.get_element_by_xpath(ele_xpath)
            if not element:
                aklog_debug('%s is not found' % ele_xpath)
                return None
            return self.image.check_video_image_is_normal(
                element=element, threshold=threshold, save_path=save_path)
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
            element = self.find_element(locator)
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

    # endregion

    # region SeekBar拖动条操作

    def slide_h_seek_bar(self, locator, minimum, maximum, index, cur_index=None, length_delta=0,
                         duration=1, from_cur_index=False, half=None, step_offset=None):
        """
        水平方向滑动拖动条，如果没有传入当前值，默认从中间位置开始滑动
        Args:
            locator (): 滚动条元素定位信息
            minimum (int or float): 拖动条最小值
            maximum (int or float): 拖动条最大值
            index (int or float): 设置的值
            cur_index (int or float): 当前值
            length_delta (float): 获取到的滑动条长度有些情况下要比实际的长一些，需要扣掉左右两边超出的部分，可以是小数0-1，表示滑动条的百分比
            duration (float): 拖动时间
            from_cur_index (bool): 是否强制从当前值开始滑动，如果为False，当差值大于10也会从当前值位置开始滑动
            half (str): left/right，有些滑动条为对称，两边向中间滑动，只需要滑动一半即可，
            step_offset (float): 滑动步长偏移量(0到1，length_delta长度的倍数)，有些滑动条，需要多滑动一些距离才能达到目标值
            如果中间为maximum，则应该传入left，如果中间为minimum，应该传入right
        """
        aklog_debug()
        try:
            if index < minimum:
                index = minimum
            elif index > maximum:
                index = maximum
            ele = self.get_element(locator)
            if isinstance(ele, UiObject):
                bounds = ele.bounds()
                lx, ly, rx, ry = bounds
            else:
                lx, ly, rx, ry = ele.bounds
            ele_width = rx - lx
            if 0 < length_delta < 1:
                length_delta = ele_width * length_delta

            if half == 'left':
                ele_width = int(ele_width / 2) + length_delta
                rx = lx + ele_width
            elif half == 'right':
                ele_width = int(ele_width / 2) + length_delta
                lx = rx - ele_width

            average_length = (ele_width - length_delta * 2) / (maximum - minimum)
            # 默认从中间位置开始滑动，如果有传入当前值，并且当强制从当前值开始滑动或者目标值与当前值间隔比较大时，会从当前值位置开始滑动
            if cur_index is not None and (from_cur_index or abs(cur_index - index) > 10):
                start_x = int(lx + length_delta + average_length * (max(cur_index - minimum, 1)))
            else:
                start_x = int((lx + rx) * 0.5)
            start_y = int((ly + ry) * 0.5)
            if step_offset is not None:
                # 有些滑动条，需要多滑动一些距离才能达到目标值，增加步长
                average_length_offset = (ele_width - length_delta * (2 - step_offset)) / (maximum - minimum)
                if index > cur_index:
                    end_x = lx + length_delta + average_length_offset * (index - minimum)
                else:
                    end_x = rx - length_delta - average_length_offset * (maximum - index)
            else:
                end_x = lx + length_delta + average_length * (index - minimum)
            # 如果滑动的目标值靠近最小值或最大值，需要多滑动一些
            if index == minimum:
                end_x -= average_length * 10
            elif index == maximum:
                end_x += average_length * 10
            elif index - minimum <= 2:
                end_x -= average_length * 1
            elif maximum - index <= 2:
                end_x += average_length * 1
            end_x = int(end_x)
            end_y = start_y
            self.swipe(start_x, start_y, end_x, end_y, duration=duration, steps=200)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_v_seek_bar(self, locator, minimum, maximum, index, cur_index=None, length_delta=0,
                         duration=1, from_cur_index=False):
        """
        垂直方向滑动拖动条，如果没有传入当前值，默认从中间位置开始滑动
        Args:
            locator (): 滚动条元素定位信息
            minimum (int or float): 拖动条最小值
            maximum (int or float): 拖动条最大值
            index (int or float): 设置的值
            cur_index (int or float): 当前值
            length_delta (float): 获取到的滑动条长度有些情况下要比实际的长一些，需要扣掉上下两边超出的部分，可以是小数0-1，表示滑动条的百分比
            duration (float): 拖动时间
            from_cur_index (bool): 是否强制从当前值位置开始滑动，如果为False，当差值大于10也会从当前值位置开始滑动
        """
        aklog_debug()
        try:
            if index < minimum:
                index = minimum
            elif index > maximum:
                index = maximum
            ele = self.get_element(locator)
            if isinstance(ele, UiObject):
                lx, ly, rx, ry = ele.bounds()
            else:
                lx, ly, rx, ry = ele.bounds
            ele_height = ry - ly
            if 0 < length_delta < 1:
                length_delta = ele_height * length_delta
            average_length = (ele_height - length_delta * 2) / (maximum - minimum)
            start_x = int((lx + rx) * 0.5)
            if cur_index is not None and (from_cur_index or abs(cur_index - index) > 10):
                start_y = int(ry - length_delta - average_length * (max(cur_index - minimum, 1)))
            else:
                start_y = int((ly + ry) * 0.5)
            end_x = start_x
            end_y = ry - length_delta - average_length * (index - minimum)
            if index == minimum:
                end_y += average_length * 2
            elif index == maximum:
                end_y -= average_length * 2
            elif index - minimum <= 2:
                end_y += average_length * 1
            elif maximum - index <= 2:
                end_y -= average_length * 1
            end_y = int(end_y)
            self.swipe(start_x, start_y, end_x, end_y, duration=duration, steps=200)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_horizontal_seek_bar_by_id(self, ele_id, minimum, maximum, index, duration=0.5,
                                        cur_index=None, length_delta=0):
        """
        水平方向滑动拖动条，如果没有传入当前值，默认从中间位置开始滑动
        :param ele_id: 滚动条元素ID
        :param minimum: 拖动条最小值，int或float类型
        :param maximum: 拖动条最大值，int或float类型
        :param index: 设置的值，int或float类型
        :param cur_index: 当前值，int或float类型
        :param length_delta: 获取到的滑动条长度有些情况下要比实际的长一些，需要扣掉上下两边超出的部分
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
            ele_width = rx - lx
            average_length = (ele_width - length_delta * 2) / (maximum - minimum)
            if cur_index is not None and abs(cur_index - index) > 10:
                start_x = int(lx + length_delta + average_length * (max(cur_index - minimum, 1)))
            else:
                start_x = int((lx + rx) * 0.5)
            start_y = int((ly + ry) * 0.5)
            end_x = lx + length_delta + average_length * (index - minimum)
            if index == minimum:
                end_x -= average_length * 2
            elif index == maximum:
                end_x += average_length * 2
            elif index - minimum <= 2:
                end_x -= average_length * 1
            elif maximum - index <= 2:
                end_x += average_length * 1
            end_x = int(end_x)
            end_y = int((ly + ry) * 0.5)
            self.swipe(start_x, start_y, end_x, end_y, duration=duration, steps=200)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_horizontal_seek_bar_by_xpath(self, ele_xpath, minimum, maximum, index, duration=0.5,
                                           cur_index=None, length_delta=0):
        """
        水平方向滑动拖动条，如果没有传入当前值，默认从中间位置开始滑动
        :param ele_xpath: 滚动条元素xpath
        :param minimum: 拖动条最小值，int或float类型
        :param maximum: 拖动条最大值，int或float类型
        :param index: 设置的值，int或float类型
        :param cur_index: 当前值，int或float类型
        :param length_delta: 获取到的滑动条长度有些情况下要比实际的长一些，需要扣掉上下两边超出的部分
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
            ele_width = rx - lx
            average_length = (ele_width - length_delta * 2) / (maximum - minimum)
            if cur_index is not None and abs(cur_index - index) > 10:
                start_x = int(lx + length_delta + average_length * (max(cur_index - minimum, 1)))
            else:
                start_x = int((lx + rx) * 0.5)
            start_y = int((ly + ry) * 0.5)
            end_x = lx + length_delta + average_length * (index - minimum)
            if index == minimum:
                end_x -= average_length * 2
            elif index == maximum:
                end_x += average_length * 2
            elif index - minimum <= 2:
                end_x -= average_length * 1
            elif maximum - index <= 2:
                end_x += average_length * 1
            end_x = int(end_x)
            end_y = int((ly + ry) * 0.5)
            self.swipe(start_x, start_y, end_x, end_y, duration=duration, steps=200)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_vertical_seek_bar_by_id(self, ele_id, minimum, maximum, index, duration=0.5,
                                      cur_index=None, length_delta=0):
        """
        垂直方向滑动拖动条，如果没有传入当前值，默认从中间位置开始滑动
        :param ele_id: 元素ID
        :param minimum: 拖动条最小值，int或float类型
        :param maximum: 拖动条最大值，int或float类型
        :param index: 设置的值，int或float类型
        :param cur_index: 当前值，int或float类型
        :param length_delta: 获取到的滑动条长度有些情况下要比实际的长一些，需要扣掉上下两边超出的部分
        :param duration: 拖动时间
        :return:
        """
        aklog_debug()
        try:
            if index < minimum:
                index = minimum
            elif index > maximum:
                index = maximum
            ele = self.driver(resourceId=ele_id)
            lx, ly, rx, ry = ele.bounds()
            ele_height = ry - ly
            average_length = (ele_height - length_delta * 2) / (maximum - minimum)
            start_x = int((lx + rx) * 0.5)
            if cur_index is not None and abs(cur_index - index) > 10:
                start_y = int(ry - length_delta - average_length * (max(cur_index - minimum, 1)))
            else:
                start_y = int((ly + ry) * 0.5)
            end_x = int((lx + rx) * 0.5)
            end_y = ry - length_delta - average_length * (index - minimum)
            if index == minimum:
                end_y += average_length * 2
            elif index == maximum:
                end_y -= average_length * 2
            elif index - minimum <= 2:
                end_y += average_length * 1
            elif maximum - index <= 2:
                end_y -= average_length * 1
            end_y = int(end_y)
            self.swipe(start_x, start_y, end_x, end_y, duration=duration, steps=200)
            return True
        except:
            aklog_debug(str(traceback.format_exc()))
            return False

    def slide_vertical_seek_bar_by_xpath(self, ele_xpath, minimum, maximum, index, duration=0.5,
                                         cur_index=None, length_delta=0):
        """
        垂直方向滑动拖动条，如果没有传入当前值，默认从中间位置开始滑动
        :param ele_xpath: 元素xpath
        :param minimum: 拖动条最小值，int或float类型
        :param maximum: 拖动条最大值，int或float类型
        :param index: 设置的值，int或float类型
        :param cur_index: 当前值，int或float类型
        :param length_delta: 获取到的滑动条长度有些情况下要比实际的长一些，需要扣掉上下两边超出的部分
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
            ele_height = ry - ly
            average_length = (ele_height - length_delta * 2) / (maximum - minimum)
            start_x = int((lx + rx) * 0.5)
            if cur_index is not None and abs(cur_index - index) > 10:
                start_y = int(ry - length_delta - average_length * (max(cur_index - minimum, 1)))
            else:
                start_y = int((ly + ry) * 0.5)
            end_x = int((lx + rx) * 0.5)
            end_y = ry - length_delta - average_length * (index - minimum)
            if index == minimum:
                end_y += average_length * 2
            elif index == maximum:
                end_y -= average_length * 2
            elif index - minimum <= 2:
                end_y += average_length * 1
            elif maximum - index <= 2:
                end_y -= average_length * 1
            end_y = int(end_y)
            self.swipe(start_x, start_y, end_x, end_y, duration=duration, steps=200)
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
            ret = self.driver.xpath(".//*[contains(@text, %s)]" % text).exists
            if not ret:
                aklog_debug('%s toast is not exist' % text)
            return ret
        except:
            aklog_debug(traceback.format_exc())
            return False

    def get_toast_text(self, wait_time=None, print_trace=False):
        """获取系统弹窗的文本信息"""
        if not wait_time:
            wait_time = self.wait_time
        try:
            # 增加915 文本信息
            ele = self.driver.xpath(
                '//*[@class="android.widget.Toast" or @resource-id="com.akuvox.phone:id/tv_tip_toast"]')
            ele.wait(timeout=wait_time)
            value = ele.get_text()
            aklog_debug("get_toast_text: %s" % value)
            return value
        except Exception as e:
            aklog_debug('toast not found')
            if print_trace or not e:
                aklog_debug(str(traceback.format_exc()))
            return None

    def reset_toast_message(self):
        self.driver.toast.reset()

    def get_toast_message(self, wait_time=None, print_trace=False):
        """获取系统弹窗的文本信息"""
        aklog_debug()
        if not wait_time:
            wait_time = self.wait_time
        try:
            value = self.driver.toast.get_message(wait_timeout=wait_time)
            aklog_debug("message: %s" % value)
            # 2025.5.14 需要做一次清空, 否则影响之后的toast. 但接口仍会在受期望以外的操作中出现的弹窗出现的toast记录影响.
            # 最好手动在操作终端业务接口前做一次reset才能保证接口效果.
            self.driver.toast.reset()
            return value
        except Exception as e:
            aklog_debug('toast not found')
            if print_trace or not e:
                aklog_debug(str(traceback.format_exc()))
            self.driver.toast.reset()
            return None

    # endregion

    # region 通知栏操作

    def open_notification(self):
        self.driver.open_notification()

    # endregion

    # region webView类型元素操作

    # endregion


if __name__ == '__main__':
    device_info = {'device_name': 'C319H',
                   'ip': '192.168.88.102',  # MARK: 注意修改IP
                   'deviceid': 'emulator-5554'}
    device_config = config_parse_device_config('config_BELAHOME_NORMAL')
    app = AndroidBaseU2(device_info, device_config)
    app.device_connect()
    app.dump_hierarchy_to_xml(r'D:\Users\Administrator\Desktop\window_dump.xml')
    # time.sleep(2)
    # app.click_btn('//*[@text="Me"]')
