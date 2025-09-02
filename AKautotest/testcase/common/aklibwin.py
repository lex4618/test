#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import io
import sys
import os
import time
import traceback
from PIL import Image
import base64
from io import BytesIO

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *
from pywinauto.application import Application
from pywinauto.controls.win32_controls import ComboBoxWrapper
from pywinauto.controls.win32_controls import ButtonWrapper
from pywinauto.controls.hwndwrapper import HwndWrapper
from pywinauto.controls.uia_controls import TreeItemWrapper
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.controls.common_controls import DateTimePickerWrapper
import pyautogui


class akwin(object):

    def __init__(self, exe_path, device_config=None, backend_type='uia'):
        # 初始化方法，初始化一个app
        self.__exe_path = exe_path
        self.device_config = device_config
        self.__type = backend_type
        self.img = None
        self.window_process = Window_process()
        self._imgs = []  # 用于保存每张截图的base64
        self.__app = None
        self.__root_window = None
        self.__root_window_name = None
        self.sleep_time = 1
        self.timeout = 10
        self.window_operation = None

    # 应用启动、连接、关闭
    def start(self, window_name, timeout=30):
        # 启动应用程序
        aklog_printf("%s,start [%s]" % (self.__class__.__name__, window_name))
        for i in range(0, 2):
            try:
                self.__app = Application(backend=self.__type).connect(path=self.__exe_path, timeout=timeout)
                self.__root_window = self.__app.window(title=window_name, control_type="Window")
            except:
                aklog_printf("connect failed")
            else:
                aklog_printf("[%s] connected" % window_name)
                time.sleep(2)
                return True

            try:
                self.__app = Application(backend=self.__type).start(self.__exe_path, timeout=timeout)
                self.__root_window = self.__app.window(title=window_name, control_type="Window")
                self.__root_window.wait('ready', timeout=timeout, retry_interval=None)
                self.max_window()
            except:
                aklog_printf("start failed" + str(traceback.format_exc()))
            else:
                aklog_printf("[%s] started" % window_name)
                time.sleep(2)
                return True
        return False

        # 以下两种均可以获取到具体的dlg
        # self.__root_window = self.__app.window(title=window_name)
        # self.print_all()

    def start_app(self, timeout=5, root_control_type="Window"):
        # 启动应用程序
        aklog_printf("%s,start_app" % self.__class__.__name__)
        change_language('EN')  # 修改输入法为ENG
        for i in range(0, 2):
            try:
                self.__app = Application(backend=self.__type).connect(path=self.__exe_path, timeout=timeout)
                self.__root_window_name = self.get_top_window_name()
                # self.__root_window = self.__app.window(title=self.__root_window_name, control_type=root_control_type)
                self.__root_window = self.__app.top_window()

                self.__root_window.wait('visible', timeout=timeout, retry_interval=None)
                # self.max_window()
            except:
                aklog_printf("connect failed, app may not have been started")
            else:
                aklog_printf("[%s] connected" % self.__root_window_name)
                time.sleep(2)
                self.window_operation = Window_process()
                return True

            try:
                self.__app = Application(backend=self.__type).start(self.__exe_path, timeout=timeout)
                self.__root_window_name = self.get_top_window_name()
                # self.__root_window = self.__app.window(title=self.__root_window_name, control_type=root_control_type)
                self.__root_window = self.__app.top_window()
                self.__root_window.wait('visible', timeout=timeout, retry_interval=None)
                # self.max_window()
            except:
                aklog_printf("start failed %s" % traceback.format_exc())
            else:
                aklog_printf("[%s] started" % self.__root_window_name)
                time.sleep(2)
                self.window_operation = Window_process()
                return True
        return False

    def connect(self, timeout=5):
        """
        连接应用程序
        """
        aklog_printf("%s,connect" % self.__class__.__name__)
        try:
            self.__root_window_name = self.get_top_window_name()
            # self.__root_window = self.__app.window(title=self.__root_window_name, control_type="Window")
            self.__root_window = self.__app.top_window()
            self.__root_window.wait('ready', timeout=timeout, retry_interval=None)
            # self.max_window()
            aklog_printf("[%s] connected" % self.__root_window_name)
            time.sleep(2)
            return True
        except:
            aklog_printf("connect failed %s" % traceback.format_exc())
            return False

    def connect_pane(self, timeout=5):
        """
        有些应用没有window，需要连接pane
        """
        aklog_printf("%s,connect_pane" % self.__class__.__name__)
        try:
            self.__root_window = self.__app.top_window()
            self.__root_window.wait('ready', timeout=timeout, retry_interval=None)
            aklog_printf("[%s] connected" % self.__root_window_name)
            time.sleep(2)
            return True
        except:
            aklog_printf("connect failed %s" % traceback.format_exc())
            return False

    def switch_root_window(self, window_name, root_control_type="Window"):
        """切换根窗口"""
        aklog_printf('switch_root_window: %s' % window_name)
        try:
            self.__root_window = self.__app.window(title=window_name, control_type=root_control_type)
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def switch_child_window(self, window_name, root_control_type="Window"):
        """切换根窗口"""
        aklog_printf('switch_root_window: %s' % window_name)
        try:
            self.__root_window = self.__app.child_window(title=window_name, control_type=root_control_type)
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def restore_root_window(self):
        """还原根窗口"""
        aklog_printf('restore_root_window')
        try:
            self.__root_window = self.__app.top_window()
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def close(self):
        """
        关闭应用程序
        """
        aklog_printf("%s,close" % self.__class__.__name__)
        try:
            self.__root_window.close()
            self.__root_window.wait_not('enabled')
            return True
        except:
            aklog_printf("close failed")
            return False

    def get_driver(self):
        return self.__app

    def get_process_id(self):
        process_id = self.__root_window.process_id()
        aklog_printf('process_id: %s' % process_id)
        return process_id

    # 截图储存list
    def reset_imgs(self):
        self._imgs = []
        param_reset_screenshots_imgs()

    def get_imgs(self):
        return self._imgs

    # 应用信息
    def get_exe_dir(self):
        # 获取工具所在路径
        exe_dir, exe_file = os.path.split(self.__exe_path)
        return exe_dir

    def get_device_config(self):
        return self.device_config

    # 获取窗口信息
    def get_rootwin(self):
        return self.__root_window

    def get_top_window_name(self):
        try:
            top_window = self.__app.top_window().texts()[0]
            aklog_printf("get_top_window_name: [%s]" % top_window)
            return top_window
        except:
            aklog_printf("get_top_window_name failed" + str(traceback.format_exc()))
            return None

    def get_root_window_name(self):
        try:
            aklog_printf("get_root_window_name: [%s]" % self.__root_window_name)
            return self.__root_window_name
        except:
            aklog_printf("get_root_window_name failed" + str(traceback.format_exc()))
            return None

    # 打印窗口或空间信息
    def print_top_window(self):
        try:
            self.__root_window.print_control_identifiers()
        except:
            aklog_printf("print_top_window failed" + str(traceback.format_exc()))

    def print_window(self, child_window):
        try:
            child_window.print_control_identifiers()
        except:
            aklog_printf("print_window failed" + str(traceback.format_exc()))

    def print_ctrl(self, window_name, ctrl):
        try:
            print((self.__app.window(title=window_name, control_type="Window")[ctrl].
                   wait('ready', timeout=self.timeout, retry_interval=None).rectangle()))
        except:
            aklog_printf("print_ctrl failed" + str(traceback.format_exc()))

    # 元素是否存在、可用
    def is_exist(self, window_name, ctrl, timeout=None):
        aklog_printf("%s,is_exist [%s] [%s]" % (self.__class__.__name__, window_name, ctrl))
        try:
            if not timeout:
                timeout = self.timeout
            rect = self.__app.window(title=window_name, control_type="Window")[ctrl]. \
                wait('exists', timeout=timeout, retry_interval=None).rectangle()
            if rect:
                aklog_printf(rect)
                return True
        except:
            aklog_printf('[%s] [%s] is not exist' % (window_name, ctrl))
            return False

    def is_exist_btn_by_name(self, ctrl):
        aklog_printf("%s,is_exist_btn_by_name [%s]" % (self.__class__.__name__, ctrl))
        try:
            rect = self.__root_window.child_window(title=ctrl, control_type="Button"). \
                wait('exists', timeout=self.timeout, retry_interval=None).rectangle()
            if rect:
                aklog_printf(rect)
                return True
        except:
            aklog_printf('[%s] is not exist %s' % (ctrl, traceback.format_exc()))
            return False

    def is_exist_btn_by_id(self, ele_id):
        aklog_printf("%s,is_exist_btn_by_id [%s]" % (self.__class__.__name__, ele_id))
        try:
            rect = self.__root_window.child_window(auto_id=ele_id, control_type="Button"). \
                wait('exists', timeout=self.timeout, retry_interval=None).rectangle()
            if rect:
                aklog_printf(rect)
                return True
        except:
            aklog_printf('[%s] is not exist %s' % (ele_id, traceback.format_exc()))
            return False

    def is_exist_by_name(self, ele_name, control_type=None, timeout=None):
        aklog_printf("%s,is_exist_by_name [%s]" % (self.__class__.__name__, ele_name))
        try:
            if timeout is None:
                timeout = self.timeout
            if control_type is None:
                rect = self.__root_window.child_window(title=ele_name). \
                    wait('exists', timeout=timeout, retry_interval=None).rectangle()
            else:
                rect = self.__root_window.child_window(title=ele_name, control_type=control_type). \
                    wait('exists', timeout=timeout, retry_interval=None).rectangle()
            if rect:
                aklog_printf(rect)
                return True
        except:
            aklog_printf('[%s] is not exist %s' % (ele_name, traceback.format_exc()))
            return False

    def is_exist_by_id(self, ele_id, control_type=None, timeout=None):
        aklog_printf("%s,is_exist_by_id [%s]" % (self.__class__.__name__, ele_id))
        try:
            if timeout is None:
                timeout = self.timeout
            if control_type is None:
                rect = self.__root_window.child_window(auto_id=ele_id). \
                    wait('exists', timeout=timeout, retry_interval=None).rectangle()
            else:
                rect = self.__root_window.child_window(auto_id=ele_id, control_type=control_type). \
                    wait('exists', timeout=timeout, retry_interval=None).rectangle()
            if rect:
                aklog_printf(rect)
                return True
        except:
            aklog_printf('[%s] is not exist %s' % (ele_id, traceback.format_exc()))
            return False

    def is_exist_by_ctrl(self, ctrl, timeout=None):
        aklog_printf("%s,is_exist_by_ctrl [%s]" % (self.__class__.__name__, ctrl))
        try:
            if timeout is None:
                timeout = self.timeout
            rect = self.__root_window[ctrl].wait('exists', timeout=timeout, retry_interval=None).rectangle()
            if rect:
                aklog_printf(rect)
                return True
        except:
            aklog_printf('[%s] is not exist %s' % (ctrl, traceback.format_exc()))
            return False

    def is_visible_by_ctrl(self, ctrl, timeout=None):
        aklog_printf("%s,is_visible_by_ctrl [%s]" % (self.__class__.__name__, ctrl))
        try:
            if timeout is None:
                timeout = self.timeout
            rect = self.__root_window[ctrl].wait('visible', timeout=timeout, retry_interval=None).rectangle()
            if rect:
                aklog_printf(rect)
                return True
        except:
            aklog_printf('[%s] is not visible')
            # aklog_printf(traceback.format_exc())
            return False

    def is_enabled_btn_by_id(self, ele_id):
        aklog_printf("%s,is_enabled_by_id [%s]" % (self.__class__.__name__, ele_id))
        try:
            status = self.__root_window.child_window(auto_id=ele_id, control_type="Button"). \
                wait('visible', timeout=self.timeout, retry_interval=None).is_enabled()
            aklog_printf('%s enabled status is %s' % (ele_id, status))
            return status
        except:
            aklog_printf('[%s] is not exist %s' % (ele_id, traceback.format_exc()))
            return None

    def is_enabled_edit_by_id(self, ele_id):
        aklog_printf("%s,is_enabled_edit_by_id [%s]" % (self.__class__.__name__, ele_id))
        try:
            status = self.__root_window.child_window(auto_id=ele_id, control_type="Edit"). \
                wait('visible', timeout=self.timeout, retry_interval=None).is_enabled()
            aklog_printf('%s enabled status is %s' % (ele_id, status))
            return status
        except:
            aklog_printf('[%s] is not exist %s' % (ele_id, traceback.format_exc()))
            return None

    # 窗口最大化、最小化
    def max_window(self):
        """
        最大化窗口
        """
        aklog_printf("%s,max_window" % self.__class__.__name__)
        try:
            self.__root_window.maximize()
            aklog_printf("max window success")
            return True
        except:
            aklog_printf("max window failed")
            return False

    def min_window(self):
        """
        最小化窗口
        """
        aklog_printf("%s,min_window" % self.__class__.__name__)
        try:
            self.__root_window.minimize()
            aklog_printf("min window success")
            return True
        except:
            aklog_printf("min window failed")
            return False

    def restore_window(self):
        """
        还原窗口
        """
        aklog_printf("%s,restore_window" % self.__class__.__name__)
        try:
            self.__root_window.restore()
            aklog_printf("restore_window success")
            return True
        except:
            aklog_printf("restore_window failed")
            return False

    def set_window_foreground(self):
        """设置窗口前置，避免窗口被其他程序界面覆盖后操作异常"""
        aklog_printf('set_window_foreground')
        try:
            self.window_process.find_window_wildcard(self.__root_window_name)
            self.window_process.set_foreground()
            return True
        except:
            aklog_printf(str(traceback.format_exc()))
            return False

    def set_window_foreground_and_maximize(self):
        """设置窗口前置并最大化，避免窗口被其他程序界面覆盖后操作异常"""
        aklog_printf('set_window_foreground_and_maximize')
        try:
            self.window_process.find_window_wildcard(self.__root_window_name)
            self.window_process.set_foreground_and_maximize()
            return True
        except:
            aklog_printf(str(traceback.format_exc()))
            return False

    def get_window_state(self):
        state = self.__root_window.is_minimized()
        aklog_printf("get_window_state: %s" % state)
        return state

    # 截图相关
    def get_screenshots_as_file(self, file_path):
        """获取窗口截图，并保存为文件"""
        aklog_printf('get_screenshots_as_file %s' % file_path)
        try:
            self.img = self.__root_window.capture_as_image()
            self.img.save(file_path, format="PNG")
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def get_screenshots_as_file_by_ctrl(self, file_path, ctrl):
        """获取窗口截图，并保存为文件"""
        aklog_printf('get_screenshots_as_file %s' % file_path)
        try:
            self.img = ctrl.capture_as_image()
            self.img.save(file_path, format="PNG")
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def get_screenshots_as_file_by_id(self, file_path, ele_id):
        """获取窗口截图，并保存为文件"""
        aklog_printf('get_screenshots_as_file %s' % file_path)
        try:
            self.img = self.__root_window.child_window(auto_id=ele_id).capture_as_image()
            self.img.save(file_path, format="PNG")
            return True
        except:
            return False

    def get_screenshots_as_base64(self):
        """获取整个窗口截图"""
        aklog_printf('get_screenshots_as_base64, the screenshots is shown below: ')
        try:
            self.img = self.__root_window.capture_as_image()
            output_buffer = BytesIO()
            self.img.save(output_buffer, format='PNG')
            base64_data = base64.b64encode(output_buffer.getvalue())
            img_base64 = base64_data.decode()
            return img_base64
        except:
            aklog_printf('get_screenshots_as_base64 failed')
            return None

    def get_screenshots_as_base64_by_ctrl(self, ctrl):
        """获取指定控件窗口截图"""
        aklog_printf('get_screenshots_as_base64_by_ctrl, the screenshots is shown below: ')
        try:
            self.img = ctrl.capture_as_image()
            output_buffer = BytesIO()
            self.img.save(output_buffer, format='PNG')
            base64_data = base64.b64encode(output_buffer.getvalue())
            img_base64 = base64_data.decode()
            return img_base64
        except:
            aklog_printf('get_screenshots_as_base64 failed')
            return None

    def get_screenshots_as_base64_by_id(self, ele_id):
        """获取指定控件窗口截图"""
        aklog_printf('get_screenshots_as_base64_by_id, the screenshots is shown below: ')
        try:
            self.img = self.__root_window.child_window(auto_id=ele_id).capture_as_image()
            output_buffer = BytesIO()
            self.img.save(output_buffer, format='PNG')
            base64_data = base64.b64encode(output_buffer.getvalue())
            img_base64 = base64_data.decode()
            return img_base64
        except:
            aklog_printf('get_screenshots_as_base64 failed')
            return None

    def is_pure_color_by_id(self, ele_id, percent):
        """判断图片是否为纯色，当某一种颜色占比超过指定值时，就认为是纯色, percent取值0-1"""
        aklog_printf('is_pure_color_by_id, ele_id: %s, percent: %s' % (ele_id, percent))
        try:
            self.img = self.__root_window.child_window(auto_id=ele_id).capture_as_image()
            output_buffer = BytesIO()
            self.img.save(output_buffer, format='PNG')
        except:
            output_buffer = None
        if not output_buffer:
            aklog_printf('截图失败')
            return None
        else:
            return check_image_is_pure_color(output_buffer, percent)

    def screen_shot(self):
        """截图,用于外部调用"""
        img_base64 = self.get_screenshots_as_base64()
        if img_base64:
            # self._imgs.append(img_base64)
            param_append_screenshots_imgs(img_base64)
        else:
            # self._imgs.append('')
            param_append_screenshots_imgs('')

    # 菜单选择
    def menu_click(self, window_name, menu):
        """
        菜单点击
        """
        aklog_printf("%s,menu_click [%s] [%s]" % (self.__class__.__name__, window_name, menu))

        for i in range(10):
            try:
                self.__app.window(title=window_name, control_type="Window").menu_select(menu)
                return True
            except:
                aklog_printf("menu_click failed")
                time.sleep(self.timeout / 10)
        return False

    def menu_select(self, menu_path):
        """
        菜单选择
        """
        aklog_printf("%s,menu_select [%s]" % (self.__class__.__name__, menu_path))
        try:
            self.__root_window.menu_select(menu_path)
            return True
        except:
            aklog_printf("menu_select failed")
            return False

    def context_menu_select(self, context_menu, menu_item):
        """
        上下文菜单选择
        :param context_menu: 菜单名称：'上下文'
        :param menu_item: 菜单选项
        :return:
        """
        aklog_printf('context_menu_select, context_menu: %s, menu_item: %s' % (context_menu, menu_item))
        try:
            self.__app.window(title=context_menu, control_type="Menu"). \
                child_window(title=menu_item, control_type="MenuItem"). \
                wait('ready', timeout=self.timeout, retry_interval=None).select()
            return True
        except:
            aklog_printf("context_menu_select failed %s" % str(traceback.format_exc()))
            return False

    # 下拉框相关
    def combox_select(self, window_name, combo, item):
        """
        菜单点击
        """
        aklog_printf("%s,combox_select [%s] [%s] [%s]" % (self.__class__.__name__, window_name, combo, item))
        try:
            self.__root_window[combo].select(item)
            return True
        except:
            aklog_printf("combox_select failed")
            return False

    def combobox_select_item(self, combobox_ctrl, item):
        """
        菜单点击
        """
        aklog_printf("%s,combobox_select_item [%s] [%s]" % (self.__class__.__name__, combobox_ctrl, item))
        try:
            combobox_ctrl.select(item)
            return True
        except:
            aklog_printf("combobox_select_item failed")
            return False

    def combobox_select_by_id(self, combo_id, item):
        """
        组合框选择，通过auto_id
        :param combo_id: 组合框id
        :param item: 组合框选项
        :return:
        """
        aklog_printf("%s,combobox_select_by_id [%s] [%s]" % (self.__class__.__name__, combo_id, item))
        try:
            combobox = self.__root_window.child_window(auto_id=combo_id, control_type="ComboBox"). \
                wait('ready', timeout=self.timeout, retry_interval=None)
            ComboBoxWrapper(combobox).select(item)
            # combobox.expand()
            # combobox.child_window(title=item, control_type="ListItem").select()
            return True
        except:
            aklog_printf("combobox_select_by_id failed %s" % str(traceback.format_exc()))
            return False

    def get_combobox_selected_text_by_id(self, combo_id):
        """
        获取组合框已选择的选项，通过auto_id
        :param combo_id: 组合框id
        :return:
        """
        try:
            combobox = self.__root_window.child_window(auto_id=combo_id, control_type="ComboBox"). \
                wait('visible', timeout=self.timeout, retry_interval=None)
            selected_text = ComboBoxWrapper(combobox).selected_text()
            aklog_printf("get_combobox_selected_text_by_id [%s]: %s" % (combo_id, selected_text))
            return selected_text
        except:
            aklog_printf("get_combobox_selected_text_by_id failed %s" % str(traceback.format_exc()))
            return None

    def get_combobox_text_by_id(self, combo_id):
        """
        获取组合框的所有选项，通过auto_id
        :param combo_id: 组合框id
        :return:
        """
        try:
            combobox = self.__root_window.child_window(auto_id=combo_id, control_type="ComboBox"). \
                wait('visible', timeout=self.timeout, retry_interval=None)
            text = ComboBoxWrapper(combobox).item_texts()
            aklog_printf("get_combobox_text_by_id [%s]: %s" % (combo_id, text))
            return text
        except:
            aklog_printf("get_combobox_text_by_id failed %s" % str(traceback.format_exc()))
            return None

    def combox_gettext(self, window_name, combo):
        # 未调试，可以使用get_combobox_selected_text_by_id方法
        aklog_printf("%s,combox_gettext [%s] [%d]" % (self.__class__.__name__, window_name, combo))
        for i in range(10):
            try:
                text = self.__app.window(title=window_name, control_type="Window")[combo].selected_text()
                return text
            except:
                aklog_printf("combox_gettext failed")
                time.sleep(self.timeout / 10)

        return False

    def select_by_ctrl_parent(self, ctrl):
        """有些控件不能直接选择，需要找到父节点ListItem类型"""
        aklog_printf('select_by_ctrl_parent [%s]' % ctrl)
        try:
            self.__root_window[ctrl].wait('ready', timeout=self.timeout, retry_interval=None).parent().select()
            return True
        except:
            aklog_printf('select_by_ctrl_parent failed' + str(traceback.format_exc()))
            return False

    # 父节点 子节点相关
    def get_parent_by_id(self, auto_id):
        """有些对话框Pane都没有名称，那么无法直接获取，需要通过子元素来获取"""
        aklog_printf('get_parent_by_id [%s]' % auto_id)
        try:
            parent = self.__root_window.window(auto_id=auto_id). \
                wait('exists', timeout=self.timeout, retry_interval=None).parent()
            return parent
        except:
            aklog_printf('get_parent_by_id failed' + str(traceback.format_exc()))
            return None

    def get_parent_by_title(self, title):
        """有些对话框Pane都没有名称，那么无法直接获取，需要通过子元素来获取"""
        aklog_printf('get_parent_by_title [%s]' % title)
        try:
            parent = self.__root_window.window(title=title, control_type='Text').parent()
            return parent
        except:
            aklog_printf('get_parent_by_title failed' + str(traceback.format_exc()))
            return None

    def get_child_by_title(self, parent_ctrl, title, control_type=None):
        """获取子节点"""
        aklog_printf('get_child_by_title [%s]' % title)
        try:
            if control_type is None:
                child = parent_ctrl.child_window(title=title)
            else:
                child = parent_ctrl.child_window(title=title, control_type=control_type)
            return child
        except:
            aklog_printf('get_child_by_title failed' + str(traceback.format_exc()))
            return None

    # list相关
    def get_list_children_by_id(self, auto_id):
        """获取list控件的子节点"""
        aklog_printf('get_list_children_by_id [%s]' % auto_id)
        try:
            children = self.__root_window.child_window(auto_id=auto_id, control_type="List"). \
                wait('exists', timeout=self.timeout, retry_interval=None).children()
            return children
        except:
            aklog_printf('get_list_children_by_id failed' + str(traceback.format_exc()))
            return None

    def click_list_child_btn_by_id(self, auto_id, btn_index):
        """通过按钮所在序号位置，点击list控件的子节点按钮"""
        aklog_printf('click_list_child_btn_by_id, auto_id: %s, btn_index: %s' % (auto_id, btn_index))
        try:
            children = self.__root_window.child_window(auto_id=auto_id, control_type="List"). \
                wait('exists', timeout=self.timeout, retry_interval=None).children()
            children[btn_index].click()
            return True
        except:
            aklog_printf('get_list_children_by_id failed' + str(traceback.format_exc()))
            return False

    # 输入框相关
    def input(self, window_name, edit, content):
        """
        输入内容
        """
        aklog_printf("%s,input [%s] [%s] %s" % (self.__class__.__name__, window_name, edit, content))
        for i in range(10):
            try:
                self.__app.window(title=window_name, control_type="Window")[edit].set_text(content)
                return True
            except:
                aklog_printf("input failed" + str(traceback.format_exc()))
                time.sleep(self.timeout / 10)
        return False

    def input_list(self):
        """
        输入内容
        """
        # aklog_printf("%s,input [%s] [%s] %s" % (self.__class__.__name__, window_name, edit, content))
        for i in range(2):
            try:
                self.__root_window.child_window(title='New Value', control_type="Text"). \
                    wait('ready', timeout=self.timeout, retry_interval=None).click()
                # self.__app.window(title=window_name, control_type="Pane")[edit].set_text(content)
                # return True
            except:
                aklog_printf("input failed" + str(traceback.format_exc()))
                time.sleep(self.timeout / 10)
        return False

    def input_edit_by_id(self, auto_id, content, pane_id=None, pane_name=None, sec=0.1):
        """
        编辑框输入
        :param auto_id: 编辑框id
        :param content: 编辑框输入的内容
        :param pane_id: 对话框的id
        :param pane_name: 对话框的name
        :param sec: 输入后等待时间
        :return:
        """
        aklog_printf("%s,input_edit_by_id [%s] %s" % (self.__class__.__name__, auto_id, content))
        try:
            if pane_id is None and pane_name is None:
                ele = self.__root_window.child_window(auto_id=auto_id, control_type="Edit"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            elif pane_id is None:
                ele = self.__root_window.child_window(title=pane_name, control_type="Pane"). \
                    child_window(auto_id=auto_id, control_type="Edit"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            elif pane_name is None:
                ele = self.__root_window.child_window(auto_id=pane_id, control_type="Pane"). \
                    child_window(auto_id=auto_id, control_type="Edit"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            else:
                ele = self.__root_window.child_window(title=pane_name, auto_id=pane_id, control_type="Pane"). \
                    child_window(auto_id=auto_id, control_type="Edit"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            # ele.select()
            ele.set_text(content)
            time.sleep(sec)
            return True
        except:
            aklog_printf("input_edit_by_id failed" + str(traceback.format_exc()))
            return False

    def input_edit_by_name(self, edit_name, content, sec=0.1):
        """
        编辑框输入
        :param edit_name: 编辑框名称
        :param content: 编辑框输入的内容
        :param sec: 输入后等待时间
        :return:
        """
        aklog_printf("%s,input_edit_by_name [%s] %s" % (self.__class__.__name__, edit_name, content))
        try:
            self.__root_window.child_window(title=edit_name, control_type="Edit"). \
                wait('ready', timeout=self.timeout, retry_interval=None).set_text(content)
            time.sleep(sec)
            return True
        except:
            aklog_printf("input_edit_by_name failed" + str(traceback.format_exc()))
            return False

    def type_keys_edit_by_id(self, auto_id, content, pane_id=None, pane_name=None, sec=0.5):
        """
        用敲击输入方式输入编辑框
        :param auto_id: 编辑框id
        :param content: 编辑框输入的内容
        :param pane_id: 对话框的id
        :param pane_name: 对话框的name
        :param sec: 输入后等待时间
        :return:
        """
        aklog_printf("%s,type_keys_edit_by_id [%s] %s" % (self.__class__.__name__, auto_id, content))
        try:
            if pane_id is None and pane_name is None:
                ele = self.__root_window.child_window(auto_id=auto_id, control_type="Edit"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            elif pane_id is None:
                ele = self.__root_window.child_window(title=pane_name, control_type="Pane"). \
                    child_window(auto_id=auto_id, control_type="Edit"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            elif pane_name is None:
                ele = self.__root_window.child_window(auto_id=pane_id, control_type="Pane"). \
                    child_window(auto_id=auto_id, control_type="Edit"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            else:
                ele = self.__root_window.child_window(title=pane_name, auto_id=pane_id, control_type="Pane"). \
                    child_window(auto_id=auto_id, control_type="Edit"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            ele.set_text('')
            ele.type_keys(content)
            time.sleep(sec)
            return True
        except:
            aklog_printf("type_keys_edit_by_id failed" + str(traceback.format_exc()))
            return False

    def get_edit_value_by_id(self, auto_id):
        """获取编辑框的value值"""
        aklog_printf("%s,get_edit_value_by_id [%s]" % (self.__class__.__name__, auto_id))
        try:
            value = self.__root_window.child_window(auto_id=auto_id). \
                wait('exists', timeout=self.timeout, retry_interval=None).get_value()
            aklog_printf('value: %s' % value)
            return value
        except:
            aklog_printf("get_edit_value_by_id failed", str(traceback.format_exc()))
            return None

    def get_edit_value_by_id_from_pane(self, auto_id, pane_ctrl):
        """获取编辑框的value值通过pane类型"""
        aklog_printf("get_edit_value_by_id_from_pane auto_id: %s, pane_ctrl: [%s]" % (auto_id, pane_ctrl))
        try:
            value = self.__root_window[pane_ctrl].child_window(auto_id=auto_id). \
                wait('exists', timeout=self.timeout, retry_interval=None).get_value()
            return value
        except:
            aklog_printf("get_text_by_id_from_pane failed", str(traceback.format_exc()))
            return None

    # 导入文件操作
    def import_file_by_id(self, btn_id, file, sec=0.1):
        aklog_printf('import_file_by_id, btn_id: %s, file: %s' % (btn_id, file))
        try:
            ele = self.__root_window.child_window(auto_id=btn_id, control_type="Button"). \
                wait('ready', timeout=self.timeout, retry_interval=None)
            ele.click()
            time.sleep(3)
            self.window_operation.upload_file(file)
            time.sleep(sec)
        except:
            aklog_printf("import_file_by_id failed" + str(traceback.format_exc()))
            return False

    # 获取控件文本信息
    def get_input_text(self, window_name, edit):
        """获取文本内容，返回list类型"""
        aklog_printf("%s,get_input_text [%s] [%s]" % (self.__class__.__name__, window_name, edit))
        try:
            text = self.__app.window(title=window_name, control_type="Window")[edit]. \
                wait('exists', timeout=self.timeout, retry_interval=None).texts()
            return text
        except:
            aklog_printf("input failed", str(traceback.format_exc()))
            return None

    def get_texts_by_ctrl(self, ctrl):
        """获取文本内容，返回list类型"""
        try:
            texts = ctrl.wait('exists', timeout=self.timeout, retry_interval=None).texts()
            aklog_printf("get_texts_by_ctrl, texts: %r" % texts)
            return texts
        except:
            aklog_printf("get_texts_by_ctrl failed", str(traceback.format_exc()))
            return None

    def get_text_by_name(self, ctrl_name):
        """获取文本内容，返回list类型"""
        aklog_printf("%s,get_text_by_name [%s]" % (self.__class__.__name__, ctrl_name))
        try:
            text = self.__root_window.child_window(title=ctrl_name). \
                wait('exists', timeout=self.timeout, retry_interval=None).texts()
            return text
        except:
            aklog_printf("get_text_by_name failed", str(traceback.format_exc()))
            return None

    def get_texts_by_id_from_pane(self, auto_id, pane_ctrl):
        """获取文本内容，返回list类型"""
        aklog_printf("get_text_by_id_from_pane auto_id: %s, pane_ctrl: [%s]" % (auto_id, pane_ctrl))
        try:
            text = self.__root_window[pane_ctrl].child_window(auto_id=auto_id). \
                wait('exists', timeout=self.timeout, retry_interval=None).texts()
            return text
        except:
            aklog_printf("get_text_by_id_from_pane failed", str(traceback.format_exc()))
            return None

    def get_text_by_id(self, auto_id, window_name=None, pane_name=None):
        """获取文本内容，返回list类型"""
        aklog_printf("get_text_by_id, auto_id=[%s], window_name=[%s], pane_name=[%s]"
                     % (auto_id, window_name, pane_name))
        try:
            if window_name is None and pane_name is None:
                text = self.__root_window.child_window(auto_id=auto_id). \
                    wait('exists', timeout=self.timeout, retry_interval=None).texts()
            elif pane_name is None:
                text = self.__root_window.child_window(title=window_name, control_type="Window"). \
                    child_window(auto_id=auto_id).wait('exists', timeout=self.timeout, retry_interval=None).texts()
            elif window_name is None:
                text = self.__root_window.child_window(title=pane_name, control_type="Pane"). \
                    child_window(auto_id=auto_id).wait('exists', timeout=self.timeout, retry_interval=None).texts()
            else:
                text = None
            aklog_printf('text: %s' % text)
            return text
        except:
            aklog_printf("get_text_by_id failed", str(traceback.format_exc()))
            return None

    def get_list_texts_by_item_name(self, item_name):
        """
        通过ListItem元素的子元素来获取整个List文本信息
        :param item_name: 子元素的title
        :return:
        """
        aklog_printf("%s,get_list_texts_by_item_name [%s]" % (self.__class__.__name__, item_name))
        try:
            text = self.__root_window.child_window(title=item_name, control_type='Text'). \
                wait('exists', timeout=self.timeout, retry_interval=None).parent().texts()
            return text
        except:
            aklog_printf("get_list_texts_by_item_name failed", str(traceback.format_exc()))
            return None

    def get_texts_by_list_item_name(self, list_id, item_name):
        """
        通过ListItem元素的子元素来获取整个List文本信息
        :param list_id: list的id
        :param item_name: 子元素的title
        :return:
        """
        aklog_printf("%s,get_texts_by_list_item_name list: [%s] item_name: [%s]"
                     % (self.__class__.__name__, list_id, item_name))
        try:
            texts = self.__root_window.window(auto_id=list_id, control_type="List"). \
                child_window(title=item_name, control_type='Text'). \
                wait('exists', timeout=self.timeout, retry_interval=None).parent().texts()
            aklog_printf(texts)
            return texts
        except:
            aklog_printf("get_list_texts_by_item_name failed", str(traceback.format_exc()))
            return None

    def get_list_count_by_id(self, auto_id, window_name=None, pane_name=None):
        """获取list列表数量"""
        aklog_printf("get_list_count_by_id, auto_id=[%s], window_name=[%s], pane_name=[%s]"
                     % (auto_id, window_name, pane_name))
        try:
            if window_name is None and pane_name is None:
                count = self.__root_window.child_window(auto_id=auto_id). \
                    wait('exists', timeout=self.timeout, retry_interval=None).item_count()
            elif pane_name is None:
                count = self.__root_window.child_window(title=window_name, control_type="Window"). \
                    child_window(auto_id=auto_id).wait('exists', timeout=self.timeout, retry_interval=None).item_count()
            elif window_name is None:
                count = self.__root_window.child_window(title=pane_name, control_type="Pane"). \
                    child_window(auto_id=auto_id).wait('exists', timeout=self.timeout, retry_interval=None).item_count()
            else:
                count = None
            return count
        except:
            aklog_printf("get_list_count_by_id failed", str(traceback.format_exc()))
            return None

    # 获取控件坐标和大小信息
    def get_pt(self, window_name, ctrl_name):
        """获取控件坐标和大小信息，L T R B"""
        aklog_printf("%s,get_pt [%s] [%s]" % (self.__class__.__name__, window_name, ctrl_name))
        for i in range(10):
            try:
                return self.__app.window(title=window_name, control_type="Window")[ctrl_name]. \
                    wait('visible', timeout=self.timeout, retry_interval=None).rectangle()
            except:
                aklog_printf("get_pt failed" + str(traceback.format_exc()))
                time.sleep(self.timeout / 10)
        return False

    def get_rect_by_id(self, ctrl_id, control_type=None):
        """获取控件坐标和大小信息，L T R B"""
        aklog_printf("get_rect_by_id [%s] [%s]" % (ctrl_id, control_type))
        try:
            if control_type:
                ele = self.__root_window.window(auto_id=ctrl_id, control_type=control_type). \
                    wait('visible', timeout=self.timeout, retry_interval=None)
            else:
                ele = self.__root_window.window(auto_id=ctrl_id). \
                    wait('visible', timeout=self.timeout, retry_interval=None)
            rect = ele.rectangle()
            return rect
        except:
            aklog_printf("get_rect_by_id failed" + str(traceback.format_exc()))
            return None

    def get_rect_by_name(self, title, control_type=None):
        """获取控件坐标和大小信息，L T R B"""
        aklog_printf("get_rect_by_name [%s] [%s]" % (title, control_type))
        try:
            if control_type:
                ele = self.__root_window.window(title=title, control_type=control_type). \
                    wait('visible', timeout=self.timeout, retry_interval=None)
            else:
                ele = self.__root_window.window(title=title). \
                    wait('visible', timeout=self.timeout, retry_interval=None)
            rect = ele.rectangle()
            aklog_printf('rect: %s' % rect)
            return rect
        except:
            aklog_printf("get_rect_by_name failed" + str(traceback.format_exc()))
            return None

    def get_ctrl_rect(self, ctrl):
        """获取控件坐标和大小信息，L T R B"""
        try:
            rect = ctrl.rectangle()
            aklog_printf("get_ctrl_rect: %s" % rect)
            return rect
        except:
            aklog_printf("get_ctrl_rect failed" + str(traceback.format_exc()))
            return None

    def get_list_child_rect_by_id(self, list_id, ctrl_index):
        """获取控件坐标和大小信息，L T R B"""
        aklog_printf("get_list_child_rect_by_id list_id: %s, ctrl_index: %s" % (list_id, ctrl_index))
        try:
            children = self.__root_window.child_window(auto_id=list_id, control_type="List"). \
                wait('exists', timeout=self.timeout, retry_interval=None).children()
            rect = children[ctrl_index].rectangle()
            return rect
        except:
            aklog_printf("get_list_child_rect_by_id failed" + str(traceback.format_exc()))
            return None

    def get_list_ctrl_rect(self, list_id, ctrl_name):
        """获取列表子元素控件坐标和大小信息，L T R B"""
        aklog_printf("%s,get_list_ctrl_rect [%s] [%s]" % (self.__class__.__name__, list_id, ctrl_name))
        for i in range(10):
            try:
                rect = self.__root_window.window(auto_id=list_id, control_type="List"). \
                    window(title=ctrl_name, control_type='Text'). \
                    wait('visible', timeout=self.timeout, retry_interval=None).rectangle()
                aklog_printf('rect: %s' % rect)
                return rect
            except:
                aklog_printf("get_list_ctrl_rect failed" + str(traceback.format_exc()))
                time.sleep(self.timeout / 10)
        return None

    def get_new_value_rect(self, list_id, ctrl_name):
        """获取控件坐标和大小信息，L T R B"""
        aklog_printf("%s,get_new_value_rect [%s] [%s]" % (self.__class__.__name__, list_id, ctrl_name))
        for i in range(10):
            try:
                rect = self.__root_window.window(auto_id=list_id, control_type="List")[ctrl_name].rectangle()
                return rect
            except:
                aklog_printf("get_list_ctrl_rect failed" + str(traceback.format_exc()))
                time.sleep(self.timeout / 10)
        return None

    # 鼠标点击操作
    def move_to_pt(self, x, y):
        try:
            pyautogui.moveTo(x, y)
            return True
        except:
            return False

    def move_and_click_pt(self, x, y):
        aklog_printf("move_and_click_pt {x:%s y:%s}" % (x, y))
        try:
            pyautogui.moveTo(int(x), int(y))
            pyautogui.click()
            return True
        except:
            return False

    def move_and_click(self, window_name, ctrl):
        aklog_printf("%s,move_and_click [%s] [%s]" % (self.__class__.__name__, window_name, ctrl))
        try:
            rect = self.__app.window(title=window_name, control_type="Window")[ctrl]. \
                wait('ready', timeout=self.timeout, retry_interval=None).rectangle()
            if rect:
                pt = rect.mid_point()
                pyautogui.moveTo(pt.x, pt.y)
                pyautogui.click()
                return True
        except:
            aklog_printf("move_and_click failed" + str(traceback.format_exc()))
            return False

    # 控件点击操作
    def click_ctrl(self, ctrl):
        """点击控件"""
        aklog_printf("click_ctrl")
        try:
            ctrl.click()
            return True
        except:
            aklog_printf("click_ctrl failed" + str(traceback.format_exc()))
            return False

    def click(self, window_name, ctrl, sec=0.1):
        """
        鼠标左键点击
        """
        aklog_printf("%s,click [%s] [%s]" % (self.__class__.__name__, window_name, ctrl))
        try:
            self.__app.window(title=window_name, control_type="Window")[ctrl]. \
                wait('ready', timeout=self.timeout, retry_interval=None).click()
            time.sleep(sec)
            return True
        except:
            aklog_printf("click failed" + str(traceback.format_exc()))
            return False

    def click_list(self, window_name, ctrl):
        """
        鼠标左键点击
        """
        aklog_printf("%s,click [%s] [%s]" % (self.__class__.__name__, window_name, ctrl))
        try:
            self.__app.window(title=window_name, control_type="List")[ctrl]. \
                wait('ready', timeout=self.timeout, retry_interval=None).click()
            return True
        except:
            aklog_printf("click failed" + str(traceback.format_exc()))
            return False

    def click_btn_by_name_from_pane(self, btn_name, pane_ctrl, sec=0.1):
        """
        鼠标左键点击指定pane对话框内的按钮
        """
        aklog_printf("click_btn_by_name_from_pane, btn_name=[%s], pane_ctrl=[%s]" % (btn_name, pane_ctrl))
        try:
            self.__root_window[pane_ctrl].child_window(title=btn_name, control_type="Button"). \
                wait('ready', timeout=self.timeout, retry_interval=None).click()
            time.sleep(sec)
            return True
        except:
            aklog_printf("click_btn_by_name_from_pane failed" + str(traceback.format_exc()))
            return False

    def click_btn_by_name(self, btn_name, window_name=None, pane_name=None, sec=0.1):
        """
        鼠标左键点击
        """
        aklog_printf("%s,click_btn_by_name window_name=[%s] pane_name=[%s] btn_name=[%s]"
                     % (self.__class__.__name__, window_name, pane_name, btn_name))
        try:
            if window_name is None and pane_name is None:
                self.__root_window.child_window(title=btn_name, control_type="Button"). \
                    wait('ready', timeout=self.timeout, retry_interval=None).click()
            elif pane_name is None:
                self.__root_window.child_window(title=window_name, control_type="Window"). \
                    child_window(title=btn_name, control_type="Button"). \
                    wait('ready', timeout=self.timeout, retry_interval=None).click()
            elif window_name is None:
                self.__root_window.child_window(title=pane_name, control_type="Pane"). \
                    child_window(title=btn_name, control_type="Button"). \
                    wait('ready', timeout=self.timeout, retry_interval=None).click()
            time.sleep(sec)
            return True
        except:
            aklog_printf("click_btn_by_name failed" + str(traceback.format_exc()))
            return False

    def click_btn_by_id(self, btn_id, window_name=None, pane_name=None, sec=0.1):
        """
        鼠标左键点击
        """
        aklog_printf("%s,click_btn_by_id window_name=[%s] pane_name=[%s] btn_id=[%s]"
                     % (self.__class__.__name__, window_name, pane_name, btn_id))
        try:
            ele = None
            if window_name is None and pane_name is None:
                ele = self.__root_window.child_window(auto_id=btn_id, control_type="Button"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            elif pane_name is None:
                ele = self.__root_window.child_window(title=window_name, control_type="Window"). \
                    child_window(auto_id=btn_id, control_type="Button"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            elif window_name is None:
                ele = self.__root_window.child_window(title=pane_name, control_type="Pane"). \
                    child_window(auto_id=btn_id, control_type="Button"). \
                    wait('ready', timeout=self.timeout, retry_interval=None)
            ele.click()
            time.sleep(sec)
            return True
        except:
            aklog_printf("click_btn_by_id failed" + str(traceback.format_exc()))
            return False

    def click_radio_btn_by_name(self, btn_name, sec=0.1):
        """
        鼠标左键点击单选框
        """
        aklog_printf("%s,click_radio_btn_by_name [%s]" % (self.__class__.__name__, btn_name))
        try:
            self.__root_window.child_window(title=btn_name, control_type="RadioButton"). \
                wait('ready', timeout=self.timeout, retry_interval=None).click()
            time.sleep(sec)
            return True
        except:
            aklog_printf("click_radio_btn_by_name failed" + str(traceback.format_exc()))
            return False

    def click_ctrl_by_id(self, ctrl_id, window_name=None, pane_name=None, sec=0.1, control_type=None):
        """
        鼠标左键点击
        """
        aklog_printf("%s,click_ctrl_by_id window_name=[%s] pane_name=[%s] ctrl_id=[%s]"
                     % (self.__class__.__name__, window_name, pane_name, ctrl_id))
        try:
            ele = None
            if control_type:
                if window_name is None and pane_name is None:
                    ele = self.__root_window.child_window(auto_id=ctrl_id, control_type=control_type). \
                        wait('ready', timeout=self.timeout, retry_interval=None)
                elif pane_name is None:
                    ele = self.__root_window.child_window(title=window_name, control_type="Window"). \
                        child_window(auto_id=ctrl_id, control_type=control_type). \
                        wait('ready', timeout=self.timeout, retry_interval=None)
                elif window_name is None:
                    ele = self.__root_window.child_window(title=pane_name, control_type="Pane"). \
                        child_window(auto_id=ctrl_id, control_type=control_type). \
                        wait('ready', timeout=self.timeout, retry_interval=None)
            else:
                if window_name is None and pane_name is None:
                    ele = self.__root_window.child_window(auto_id=ctrl_id).\
                        wait('ready', timeout=self.timeout, retry_interval=None)
                elif pane_name is None:
                    ele = self.__root_window.child_window(title=window_name, control_type="Window"). \
                        child_window(auto_id=ctrl_id).wait('ready', timeout=self.timeout, retry_interval=None)
                elif window_name is None:
                    ele = self.__root_window.child_window(title=pane_name, control_type="Pane"). \
                        child_window(auto_id=ctrl_id).wait('ready', timeout=self.timeout, retry_interval=None)
            ele.click()
            time.sleep(sec)
            return True
        except:
            aklog_printf("click_ctrl_by_id failed" + str(traceback.format_exc()))
            return False

    def click_input_by_id(self, ctrl_id, window_name=None, pane_name=None, sec=0.1, control_type=None):
        """
        鼠标左键点击
        """
        aklog_printf("%s,click_input_by_id window_name=[%s] pane_name=[%s] ctrl_id=[%s]"
                     % (self.__class__.__name__, window_name, pane_name, ctrl_id))
        try:
            ele = None
            if control_type is None:
                if window_name is None and pane_name is None:
                    ele = self.__root_window.child_window(auto_id=ctrl_id). \
                        wait('ready', timeout=self.timeout, retry_interval=None)
                elif pane_name is None:
                    ele = self.__root_window.child_window(title=window_name, control_type="Window"). \
                        child_window(auto_id=ctrl_id).wait('ready', timeout=self.timeout, retry_interval=None)
                elif window_name is None:
                    ele = self.__root_window.child_window(title=pane_name, control_type="Pane"). \
                        child_window(auto_id=ctrl_id).wait('ready', timeout=self.timeout, retry_interval=None)
            else:
                if window_name is None and pane_name is None:
                    ele = self.__root_window.child_window(auto_id=ctrl_id, control_type=control_type). \
                        wait('ready', timeout=self.timeout, retry_interval=None)
                elif pane_name is None:
                    ele = self.__root_window.child_window(title=window_name, control_type="Window"). \
                        child_window(auto_id=ctrl_id, control_type=control_type). \
                        wait('ready', timeout=self.timeout, retry_interval=None)
                elif window_name is None:
                    ele = self.__root_window.child_window(title=pane_name, control_type="Pane"). \
                        child_window(auto_id=ctrl_id, control_type=control_type). \
                        wait('ready', timeout=self.timeout, retry_interval=None)
            ele.click_input()
            time.sleep(sec)
            return True
        except:
            aklog_printf("click_input_by_id failed" + str(traceback.format_exc()))
            return False

    def click_input(self, window_name, ctrl):
        """
        鼠标左键点击
        """
        aklog_printf("%s,click_input [%s] [%s]" % (self.__class__.__name__, window_name, ctrl))
        try:
            self.__app.window(title=window_name, control_type="Window")[ctrl]. \
                wait('ready', timeout=self.timeout, retry_interval=None).click_input()
            return True
        except:
            aklog_printf("click_input failed" + str(traceback.format_exc()))
            return False

    def click_input_by_ctrl_name(self, ctrl, window_name=None, pane_name=None, sec=0.1):
        """
        鼠标左键点击
        """
        aklog_printf("click_input_by_ctrl_name [%s]" % ctrl)
        try:
            ele = None
            if window_name is None and pane_name is None:
                ele = self.__root_window[ctrl].wait('ready', timeout=self.timeout, retry_interval=None)
            elif pane_name is None:
                ele = self.__root_window.child_window(title=window_name, control_type="Window")[ctrl].\
                    wait('ready', timeout=self.timeout, retry_interval=None)
            elif window_name is None:
                ele = self.__root_window.child_window(title=pane_name, control_type="Pane")[ctrl].\
                    wait('ready', timeout=self.timeout, retry_interval=None)
            self.__root_window[ctrl].wait('ready', timeout=self.timeout, retry_interval=None)
            ele.click_input()
            time.sleep(sec)
            return True
        except:
            aklog_printf("click_input_by_ctrl_name failed" + str(traceback.format_exc()))
            return False

    def click_input_pane(self, pane_name, ctrl):
        """
        有些工具不是window，需要用到Pane的方法
        鼠标左键点击(单击)
        """
        aklog_printf("%s,click_input_pane [%s] [%s]" % (self.__class__.__name__, pane_name, ctrl))
        try:
            self.__app.window(title=pane_name, control_type="Pane")[ctrl]. \
                wait('ready', timeout=self.timeout, retry_interval=None).click_input()
            return True
        except:
            aklog_printf("click_input_pane failed" + str(traceback.format_exc()))
        return False

    def double_click_input(self, window_name, ctrl):
        """
        鼠标左键点击(双击)
        """
        aklog_printf("%s,double_click_input [%s] [%s]" % (self.__class__.__name__, window_name, ctrl))
        try:
            self.__app.window(title=window_name, control_type="Window")[ctrl]. \
                wait('ready', timeout=self.timeout, retry_interval=None).double_click_input()
            return True
        except:
            aklog_printf("double_click failed" + str(traceback.format_exc()))
            return False

    def double_click_input_pane(self, pane_name, ctrl):
        """
        有些工具不是window，需要用到Pane的方法
        鼠标左键点击(双击)
        """
        aklog_printf("%s,double_click_input [%s] [%s]" % (self.__class__.__name__, pane_name, ctrl))
        try:
            self.__app.window(title=pane_name, control_type="Pane")[ctrl]. \
                wait('ready', timeout=self.timeout, retry_interval=None).double_click_input()
            return True
        except:
            aklog_printf("double_click failed" + str(traceback.format_exc()))
        return False

    def right_click_by_id(self, window_name, ctrl):
        """
        鼠标右键点击
        window_name : 窗口名
        ctrl：控件名
        """
        aklog_printf("%s,right_click_input [%s] [%s]" % (self.__class__.__name__, window_name, ctrl))
        try:
            self.__root_window[ctrl].wait('ready', timeout=self.timeout, retry_interval=None).right_click()
            return True
        except:
            aklog_printf("right_click failed" + str(traceback.format_exc()))
            return False

    def right_click_input(self, window_name, ctrl):
        """
        鼠标右键点击
        window_name : 窗口名
        ctrl：控件名
        """
        aklog_printf("%s,right_click_input [%s] [%s]" % (self.__class__.__name__, window_name, ctrl))
        try:
            self.__app.window(title=window_name, control_type="Window")[ctrl]. \
                wait('ready', timeout=self.timeout, retry_interval=None).right_click_input()
            return True
        except:
            aklog_printf("right_click failed" + str(traceback.format_exc()))
            return False

    def right_click_input_pane(self, pane_name, ctrl):
        """
        有些工具不是window，需要用到Pane的方法
        鼠标右键点击
        pane_name : 页面名
        ctrl：控件名
        """
        aklog_printf("%s,right_click_input [%s] [%s]" % (self.__class__.__name__, pane_name, ctrl))
        try:
            self.__app.window(title=pane_name, control_type="Pane")[ctrl]. \
                wait('ready', timeout=self.timeout, retry_interval=None).right_click_input()
            return True
        except:
            aklog_printf("right_click failed" + str(traceback.format_exc()))
            return False

    # 树节点相关
    def expand_ctrl(self, ctrl):
        try:
            ctrl.wait('ready', timeout=self.timeout, retry_interval=None).expand()
            return True
        except:
            aklog_printf("expand ctrl failed" + str(traceback.format_exc()))
            return False

    def is_expanded_ctrl(self, ctrl):
        try:
            return ctrl.wait('ready', timeout=self.timeout, retry_interval=None).is_expanded()
        except:
            aklog_printf("is_expanded_ctrl failed" + str(traceback.format_exc()))
            return False

    def get_expand_state_ctrl(self, ctrl):
        aklog_printf('get_expand_state_ctrl')
        try:
            state = ctrl.wait('exists', timeout=self.timeout, retry_interval=None).get_expand_state()
            aklog_printf('get_expand_state: %s' % state)
            return state
        except:
            aklog_printf('get_expand_state_ctrl failed')
            return None

    def get_child_by_name(self, parent_ctrl, name):
        """通过子节点名称获取子节点控件"""
        aklog_printf('get_child_by_name [%s]' % name)
        try:
            child = parent_ctrl.get_child(name)
            return child
        except:
            aklog_printf('%s is not found' % name)
            return None

    def get_tree_item_by_path(self, tree, path):
        """
        通过子节点的路径获取tree子节点控件
        :param tree: tree控件
        :param path: 节点名称路径，反斜杠开头，比如'\\node\\sub_node\\sub_node2'
        :return:
        """
        aklog_printf('get_tree_item_by_path, path: %s' % path)
        try:
            child = tree.get_item(path)
            return child
        except:
            aklog_printf('%s is not found' % path)
            return None

    def get_tree_ctrl_by_id(self, tree_id):
        aklog_printf('get_tree_ctrl_by_id: %s' % tree_id)
        try:
            tree_ctrl = self.__root_window.child_window(auto_id=tree_id, control_type='Tree')
            return tree_ctrl
        except:
            aklog_printf('tree %s is not found' % tree_id)
            return None

    def get_text_tree_child_item_by_ctrl(self, ctrl, tree_item_title_re):
        """根据树的子节点部分名称，获取全部名称，返回str类型"""
        aklog_printf("get_text_tree_child_item_by_ctrl, tree_item_title_re: %r" % tree_item_title_re)
        try:
            children = ctrl.children()
            for i in children:
                child_name = i.texts()[0]
                if tree_item_title_re in child_name:
                    aklog_printf("child_name: %r" % child_name)
                    return child_name
            return None
        except:
            aklog_printf("get_texts_by_ctrl failed", str(traceback.format_exc()))
            return None

    # 复选框相关
    def get_check_state_by_name(self, ele_name):
        """
        获取复选框的状态
        :return:0 - unchecked, 1 - checked, 2 - indeterminate(有些复选框包含多个子复选框，子复选框只部分勾选，则父复选框状态就是indeterminate)
        """
        aklog_printf('get_check_state_by_name, %s' % ele_name)
        try:
            check_box = self.__root_window.child_window(title=ele_name, control_type="CheckBox"). \
                wait('exists', timeout=self.timeout, retry_interval=None)
            check_state = ButtonWrapper(check_box).get_check_state()
            aklog_printf('get_check_state_by_name, check_state: %s' % check_state)
            return check_state
        except:
            aklog_printf('get_check_state_by_name failed')
            return None

    def get_check_state_by_id(self, ele_id):
        """
        获取复选框的状态
        :return:0 - unchecked, 1 - checked, 2 - indeterminate(有些复选框包含多个子复选框，子复选框只部分勾选，则父复选框状态就是indeterminate)
        """
        aklog_printf('get_check_state_by_id, %s' % ele_id)
        try:
            check_box = self.__root_window.child_window(auto_id=ele_id, control_type="CheckBox"). \
                wait('exists', timeout=self.timeout, retry_interval=None)
            check_state = ButtonWrapper(check_box).get_check_state()
            aklog_printf('get_check_state_by_id, check_state: %s' % check_state)
            return check_state
        except:
            aklog_printf('get_check_state_by_id failed')
            return None

    def is_checked_by_name(self, ele_name):
        """
        判断复选框是否勾选
        :return: True or False
        """
        aklog_printf('is_checked_by_name, %s' % ele_name)
        try:
            check_box = self.__root_window.child_window(title=ele_name, control_type="CheckBox"). \
                wait('exists', timeout=self.timeout, retry_interval=None)
            check_state = ButtonWrapper(check_box).is_checked()
            aklog_printf('is_checked_by_name, check_state: %s' % check_state)
            return check_state
        except:
            aklog_printf('is_checked_by_name failed')
            return False

    def is_checked_by_id(self, ele_id):
        """
        判断复选框是否勾选
        :return: True or False
        """
        aklog_printf('is_checked_by_id, %s' % ele_id)
        try:
            check_box = self.__root_window.child_window(auto_id=ele_id, control_type="CheckBox"). \
                wait('exists', timeout=self.timeout, retry_interval=None)
            check_state = ButtonWrapper(check_box).is_checked()
            aklog_printf('is_checked_by_id, check_state: %s' % check_state)
            return check_state
        except:
            aklog_printf('is_checked_by_id failed')
            return False

    def check_box_by_name(self, ele_name):
        """复选框勾选"""
        aklog_printf('check_box_by_name, %s' % ele_name)
        try:
            check_box = self.__root_window.child_window(title=ele_name, control_type="CheckBox"). \
                wait('ready', timeout=self.timeout, retry_interval=None)
            check_state = ButtonWrapper(check_box).is_checked()
            if not check_state:
                ButtonWrapper(check_box).check()
            return True
        except:
            aklog_printf('check_box_by_name failed')
            return False

    def check_box_by_id(self, ele_id):
        """复选框勾选"""
        aklog_printf('check_box_by_id, %s' % ele_id)
        try:
            check_box = self.__root_window.child_window(auto_id=ele_id, control_type="CheckBox"). \
                wait('ready', timeout=self.timeout, retry_interval=None)
            check_state = ButtonWrapper(check_box).is_checked()
            if not check_state:
                ButtonWrapper(check_box).check()
            return True
        except:
            aklog_printf('check_box_by_id failed')
            return False

    def click_check_box_by_id(self, ele_id):
        """通过点击方式勾选复选框"""
        aklog_printf('click_check_box_by_id, %s' % ele_id)
        try:
            check_box = self.__root_window.child_window(auto_id=ele_id, control_type="CheckBox"). \
                wait('ready', timeout=self.timeout, retry_interval=None)
            check_state = ButtonWrapper(check_box).is_checked()
            if not check_state:
                check_box.click()
            return True
        except:
            aklog_printf('click_check_box_by_id failed')
            return False

    def uncheck_box_by_name(self, ele_name):
        """复选框取消勾选"""
        aklog_printf('uncheck_box_by_name, %s' % ele_name)
        try:
            check_box = self.__root_window.child_window(title=ele_name, control_type="CheckBox"). \
                wait('ready', timeout=self.timeout, retry_interval=None)
            check_state = ButtonWrapper(check_box).is_checked()
            if check_state:
                ButtonWrapper(check_box).uncheck()
            return True
        except:
            aklog_printf('uncheck_box_by_name failed')
            return False

    def uncheck_box_by_id(self, ele_id):
        """复选框取消勾选"""
        aklog_printf('uncheck_box_by_id, %s' % ele_id)
        try:
            check_box = self.__root_window.child_window(auto_id=ele_id, control_type="CheckBox"). \
                wait('ready', timeout=self.timeout, retry_interval=None)
            check_state = ButtonWrapper(check_box).is_checked()
            if check_state:
                ButtonWrapper(check_box).uncheck()
            return True
        except:
            aklog_printf('uncheck_box_by_id failed')
            return False

    def click_uncheck_box_by_id(self, ele_id):
        """通过点击方式取消勾选复选框"""
        aklog_printf('click_uncheck_box_by_id, %s' % ele_id)
        try:
            check_box = self.__root_window.child_window(auto_id=ele_id, control_type="CheckBox"). \
                wait('ready', timeout=self.timeout, retry_interval=None)
            check_state = ButtonWrapper(check_box).is_checked()
            if check_state:
                check_box.click()
            return True
        except:
            aklog_printf('click_uncheck_box_by_id failed')
            return False

    # 日历控件操作
    def set_date_time_by_id(self, ele_id, date=None, time=None):
        """
        设置日期时间
        :param ele_id: 日历控件id
        :param date: 年月日用'/'分隔
        :param time: 时分秒用':'分隔
        :return:
        """
        aklog_printf('set_date_time_by_id, ele_id: %s, date: %s, time: %s' % (ele_id, date, time))
        try:
            date_ctrl = self.__root_window.child_window(auto_id=ele_id, control_type="Pane"). \
                wait('exists', timeout=self.timeout, retry_interval=None)
            dateTimeFrom_win32 = DateTimePickerWrapper(date_ctrl)
            if date and '/' in date:
                date_list = date.split('/')
                if time is None:
                    dateTimeFrom_win32.set_time(year=int(date_list[0]), month=int(date_list[1]),
                                                day=int(date_list[2]))
                else:
                    time_list = time.split(':')
                    dateTimeFrom_win32.set_time(year=int(date_list[0]), month=int(date_list[1]),
                                                day=int(date_list[2]), hour=int(time_list[0]),
                                                minute=int(time_list[1]), second=int(time_list[2]))
            elif time and ':' in time:
                time_list = time.split(':')
                dateTimeFrom_win32.set_time(hour=int(time_list[0]), minute=int(time_list[1]),
                                            second=int(time_list[2]))
            else:
                aklog_printf('日期时间为空或者格式不正确, %s' % traceback.format_exc())
                return False
            return True
        except:
            aklog_printf('set date time failed, %s' % traceback.format_exc())
            return False

    # 键盘操作相关
    def keyboard_press(self, key):
        # 按下不松开
        aklog_printf("%s,keyboard_press %s" % (self.__class__.__name__, key))
        try:
            pyautogui.keyDown(key)
            return True
        except:
            aklog_printf("click failed")

        return False

    def keyboard_release(self, key):
        # 松开
        aklog_printf("%s,keyboard_release %s" % (self.__class__.__name__, key))
        try:
            pyautogui.keyUp(key)
            return True
        except:
            aklog_printf("click failed")

        return False

    def keyboard_tap(self, key, times=1, interval=0):
        """
        敲击，包括按下和弹起
        当要传入特殊按键，例如删除按钮的时候，输入参考backspace_key, enter_key（可以进入到PyKeyboard查看对应的名称）
        要传入字符串时，正常传入即可，例如'13asd'

        """
        aklog_printf("%s,keyboard_tap %s" % (self.__class__.__name__, key))
        try:
            pyautogui.press(key, presses=times, interval=interval)
            return True
        except:
            aklog_printf("click failed")
        return False

    def keyboard_tap_string(self, string: str):
        """键盘输入"""
        aklog_printf("%s,keyboard_tap_string %s" % (self.__class__.__name__, string))
        try:
            pyautogui.press(list(string))
            return True
        except:
            aklog_printf("click failed")

        return False

    def ctrl_c(self):
        pyautogui.hotkey('ctrl', 'c')

    def ctrl_v(self):
        pyautogui.hotkey('ctrl', 'v')

    def ctrl_a(self):
        pyautogui.hotkey('ctrl', 'a')
