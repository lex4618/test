# -*- coding: utf-8 -*-
import re
import sys
import os
import time
import traceback

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *


class AkubelaUserWeb:

    # <editor-fold desc="初始化">

    def __init__(self):
        self.device_info = None
        self.device_config = None
        self.connect_type = 'lan'
        self.browser = None
        self.device_ip = ''
        self.ele_info = None
        self.username = ''
        self.password = ''
        self.login_type = 'local'
        self.local_login_url = ''
        self.remote_login_url = ''

    def init(self, browser):
        """启动网页初始化"""
        self.browser = browser
        self.device_config = browser.get_device_config()
        self.device_info = browser.get_device_info()
        if self.device_info and 'ip' in self.device_info:
            if self.connect_type == 'lan':
                self.device_ip = self.device_info.get('ip')
            else:
                self.device_ip = self.device_info.get('wifi_ip')
            self.local_login_url = 'http://%s' % self.device_ip
        self.ele_info = self.device_config.get_normal_akubela_user_web_element_info('USERWEB1_0')

    def start_and_login(self, username=None, password=None, login_type=None):
        """
        打开浏览器并登录用户web
        默认会使用设备的内网IP，如果要使用云平台的地址去访问用户web，则要传入login_type=remote
        """
        self.browser.init()
        return self.login(username, password, login_type)

    def browser_close_and_quit(self):
        self.browser.close_and_quit()

    def reset_imgs(self):
        self.browser.reset_imgs()

    # </editor-fold>

    # <editor-fold desc="网页通用操作API">

    def menu_select_enter_page(self, menu_js_path, submenu_js_path):
        aklog_printf()
        for i in range(3):
            submenu_class_name = self.browser.get_attribute_by_js_path(submenu_js_path, 'className')
            if submenu_class_name and 'selected-item' in submenu_class_name:
                aklog_printf('当前已经进入页面')
                return True
            elif i == 2:
                aklog_printf('进入页面失败')
                self.browser.screen_shot()
                return False
            elif submenu_class_name is None:
                if not self.browser.click_btn_by_js_path(menu_js_path):
                    aklog_printf('网页显示可能有异常，重新登录')
                    self.browser.screen_shot()
                    self.retry_login()
                    self.browser.web_refresh(force=True)
                    time.sleep(2)
                    self.browser.click_btn_by_js_path(menu_js_path)
            self.browser.click_btn_by_js_path(submenu_js_path)
            time.sleep(1)
            continue

    def screen_shot(self):
        self.browser.screen_shot()

    # 读写配置
    def write_config(self, id_name_path, *values):
        """
        判断大部分的通用网页元素类型, 选择输入框、复选框或者下拉框的方法操作
        id_name_path: 用户web的基本上都是js_path
        ps:
            1) 针对下拉框,path定位到[@role='combobox']这一级即可
            如果下拉框为多项选择，则values可以传入多个
            下拉框选项value也可以传入选项序号，从0开始，这种主要用于Disabled和Enabled用0和1来表示
            2) 复选框, 勾选框： path定位到input[@type="checkbox"], value传入True/False，或者1和0
        """
        aklog_printf()
        try:
            if id_name_path.startswith('document'):
                ele = self.browser.get_element_by_js_path(id_name_path)
            else:
                ele = self.browser.adapt_element(id_name_path)
            if not ele:
                aklog_printf('元素不存在')
                return False
            elif not ele.is_enabled():
                aklog_printf('元素处于不可操作状态')
                return False

            if ele.get_attribute('type') == 'checkbox':
                value = values[0]
                # 复选框checkbox只需传入一个value
                if value is False or str(value) == '0':
                    value = False
                else:
                    value = True
                if ele.is_selected() != value:
                    # 复选框传入True/False 或者1和0（0表示取消勾选） 来选择勾选不勾选.
                    self.browser.click_ele(ele)
            elif ele.get_attribute('role') == 'combobox':
                # 下拉框选择，多项选择可以传入多个values
                self.browser.click_ele(ele)
                for value in values:
                    # 选项只能传序号数字，0表示第一个选项，1表示第二个选项，以此类推
                    if not str(value).isdigit():
                        aklog_printf('选项只能传序号数字')
                        continue
                    value = int(value) + 1
                    option_ele_path = id_name_path.replace('mwc-select").shadowRoot.querySelector("div > div")',
                                                           'mwc-select > mwc-list-item:nth-child(%s)")' % value)
                    # else:
                    #     option_ele_path = id_name_path.replace('mwc-select").shadowRoot.querySelector("div > div")',
                    #                                            'mwc-select > mwc-list-item[text()=\'%s\']")' % value)
                    option_ele = self.browser.get_element_by_js_path(option_ele_path)
                    self.browser.click_ele(option_ele)
            else:
                # 文本输入框
                value = values[0]
                ele.send_keys(Keys.CONTROL, 'a')
                ele.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
                if ele.get_attribute('value'):
                    ele.clear()
                    time.sleep(0.1)
                ele.send_keys(value)
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def read_config(self, id_name_path):
        """
        封装获取大部分网页控件的显示值, 输入框、复选框或者下拉框.
        id_name_path: 用户web的基本上都是js_path
        ps:
            1) 针对下拉框, 读取的是被选择的选项，path定位到combobox这一级即可
            2) 复选框, 勾选框： path定位到input[@type="checkbox"]
        """
        aklog_printf()
        try:
            if id_name_path.startswith('document'):
                ele = self.browser.get_element_by_js_path(id_name_path)
            else:
                ele = self.browser.adapt_element(id_name_path)
            if not ele:
                aklog_printf('元素不存在')
                return None
            if ele.get_attribute('type') == 'checkbox':
                value = ele.is_selected()
            elif ele.tag_name == 'label':
                value = ele.text
            elif ele.get_attribute('role') == 'combobox':
                value = ele.text
            elif ele.get_attribute('class') == 'ant-select-selection-selected-value':
                value = ele.text
            else:
                value = ele.get_attribute('value')
            aklog_printf('value: %s, Type: %s' % (value, type(value)))
            return value
        except:
            aklog_printf(traceback.format_exc())
            return None

    # </editor-fold>

    # <editor-fold desc="登录相关">

    def put_username_password(self, username, password):
        if username and password:
            self.username = username
            self.password = password

    def login(self, username=None, password=None, login_type=None, raise_enable=True):
        """login_type：local、remote，也可以传入具体的URL"""
        aklog_printf()
        if login_type:
            self.login_type = login_type
        if self.login_type == 'local':
            ret = self.__local_login(username, password, raise_enable)
        else:
            if self.login_type == 'remote':
                # 使用全球用户端入口地址
                self.remote_login_url = config_get_value_from_ini_file('akubela_cloud_info', 'cloud_global_user_addr')
                if not self.remote_login_url:
                    self.remote_login_url = 'https://my.uat.akubela.com'
            else:
                self.remote_login_url = login_type
            ret = self.__cloud_remote_login(username, password, raise_enable)
        return ret

    def __local_login(self, username=None, password=None, raise_enable=True):
        """本地地址登录用户web"""
        aklog_printf()
        self.browser.visit_url(self.local_login_url)
        self.browser.web_refresh(force=True)
        time.sleep(2)
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        print_trace = False
        for i in range(4):
            if i == 3:
                print_trace = True
            if self.browser.is_visible_ele_by_js_path(self.ele_info['login_username_input'], print_trace=print_trace):
                self.write_config(self.ele_info['login_username_input'], self.username)
                self.write_config(self.ele_info['login_password_input'], self.password)
                time.sleep(1)
                if not self.browser.get_ele_status_by_js_path(self.ele_info['login_login_btn']):
                    lock_time = self.browser.get_attribute_by_js_path(
                        self.ele_info['login_login_btn'], 'textContent')
                    if lock_time:
                        lock_time = re.sub(r'\D', '', lock_time)
                        if lock_time:
                            time.sleep(int(lock_time) + 2)
                self.browser.action_click_btn_by_js_path(self.ele_info['login_login_btn'])
                time.sleep(3)
                for j in range(3):
                    if self.browser.is_visible_ele_by_js_path(self.ele_info['logout_btn'], print_trace=print_trace):
                        aklog_printf('登录用户Web成功')
                        return True
                    else:
                        time.sleep(3)
                        continue

            elif self.browser.is_visible_ele_by_js_path(self.ele_info['logout_btn'], print_trace=print_trace):
                aklog_printf('用户Web已登录，无需再重新登录')
                return True

            if i < 3:
                aklog_printf('未登录成功，刷新页面重试')
                self.browser.web_refresh(force=True)
                time.sleep(2)
                continue
            else:
                aklog_printf('登录用户web失败')
                self.browser.screen_shot()
                if raise_enable:
                    self.browser_close_and_quit()
                    time.sleep(2)
                    raise RuntimeError
                else:
                    return False

    def __cloud_remote_login(self, username=None, password=None, raise_enable=True):
        """云平台远程登录用户web"""
        aklog_printf()
        self.browser.visit_url(self.remote_login_url)
        self.browser.web_refresh(force=True)
        time.sleep(2)
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        print_trace = False
        login_username_input = '//*[@id="loginLayout"]/div[1]/div/form/div[1]/div/div[1]/input'
        login_password_input = '//*[@id="loginLayout"]/div[1]/div/form/div[2]/div/div[1]/input'
        login_btn = '//*[@id="loginLayout"]/div[1]/div/form/div[4]/div/button'
        login_btn_text = '//*[@id="loginLayout"]/div[1]/div[1]/form/div[4]/div/button/span'
        for i in range(4):
            if i == 3:
                print_trace = True
            if self.browser.is_exist_and_visible_ele_by_xpath(login_username_input):
                self.write_config(login_username_input, self.username)
                self.write_config(login_password_input, self.password)
                time.sleep(0.5)
                self.browser.click_btn_by_xpath(login_btn)
                time.sleep(1)
                self.slide_puzzle_vcode()
                time.sleep(15)
                if not self.browser.is_exist_and_visible_ele_by_xpath(login_username_input):
                    for j in range(10):
                        if self.browser.is_visible_ele_by_js_path(self.ele_info['logout_btn'], print_trace=print_trace):
                            aklog_printf('登录用户Web成功')
                            return True
                        else:
                            time.sleep(3)
                            continue
            elif self.browser.is_visible_ele_by_js_path(self.ele_info['logout_btn'], print_trace=print_trace):
                aklog_printf('用户Web已登录，无需再重新登录')
                return True

            if i < 3:
                # 登录失败时，先判断是否仍在登录界面，登录按钮是否被限制
                if self.browser.get_ele_status_by_xpath(login_btn) is False:
                    lock_time = self.browser.get_attribute_by_xpath(login_btn_text, 'textContent')
                    if lock_time:
                        aklog_printf('登录被限制，需要等待 %s' % lock_time)
                        lock_time = re.sub(r'\D', '', lock_time)
                        if lock_time:
                            time.sleep(int(lock_time) + 2)
                # 有可能登录失败，需要点击Retry重新登录
                elif self.browser.is_visible_ele_by_js_path(
                        self.ele_info['login_failed_retry_btn'], print_trace=print_trace):
                    login_failed_text = self.browser.get_attribute_by_js_path(
                        self.ele_info['login_failed_text'], 'textContent')
                    aklog_printf('登录用户web异常: %s，点击Retry重新登录' % login_failed_text)
                    self.browser.screen_shot()
                    self.browser.click_btn_by_js_path(self.ele_info['login_failed_retry_btn'])
                    time.sleep(5)
                    if self.browser.is_visible_ele_by_js_path(self.ele_info['logout_btn'], print_trace=print_trace):
                        aklog_printf('登录用户Web成功')
                        return True

                aklog_printf('登录用户web异常，刷新页面再尝试登录')
                self.browser.screen_shot()
                self.browser.web_refresh(force=True)
                time.sleep(4)
                continue
            else:
                aklog_printf('登录用户web失败')
                self.browser.screen_shot()
                if raise_enable:
                    self.browser_close_and_quit()
                    time.sleep(2)
                    raise RuntimeError
                else:
                    return False

    def retry_login(self):
        aklog_printf()
        self.browser_close_and_quit()
        self.start_and_login()

    def logout(self):
        aklog_printf()
        self.browser.click_btn_by_js_path(self.ele_info['logout_btn'])

    def slide_puzzle_vcode(self):
        """滑动拼图验证码"""
        print_trace = False
        for i in range(4):
            if i == 3:
                print_trace = True
            canvas_ele = self.browser.get_element_visible(By.XPATH, '/html/body/div[2]/div/div[1]/canvas[1]',
                                                          print_trace=print_trace)
            if canvas_ele:
                len_x = self.browser.image.get_canvas_missing_piece_loc(canvas_ele)
                slide_btn = self.browser.get_element_visible(By.XPATH, '/html/body/div[2]/div/div[2]/div/div[2]/div')
                self.browser.drag_and_drop_by_offset(slide_btn, len_x, 0)
                time.sleep(2)
                continue
            elif i == 0:
                aklog_printf('没有弹出滑动拼图验证码')
                return True
            elif i < 2:
                aklog_printf('滑动拼图完成')
                return True
            else:
                aklog_printf('滑动拼图失败')
                return False

    # </editor-fold>

    # <editor-fold desc="场景相关">

    def enter_scenes_page(self):
        aklog_printf()
        self.menu_select_enter_page(self.ele_info['menu_scenes'], self.ele_info['submenu_scenes'])

    def click_scenes_play_btn_by_index(self, index=1):
        """点击手动执行场景的播放按钮"""
        aklog_printf()
        js_path = 'document.querySelector("body > home-assistant").' \
                  'shadowRoot.querySelector("div > home-assistant-main").' \
                  'shadowRoot.querySelector("app-drawer-layout > div > partial-panel-resolver > ha-panel-scenes").' \
                  'shadowRoot.querySelector("div.main-box > div.main-box-content > div > div:nth-child(%s) ' \
                  '> ha-automation-card").shadowRoot.querySelector("div > div > div > div.content-top-item__scene' \
                  ' > span.action > div.play")' % index
        self.browser.click_btn_by_js_path(js_path)

    def set_auto_scenes_by_index(self, active, index=1):
        """
        设置自动场景开关
        active: 0 or 1
        """
        aklog_printf()
        js_path = 'document.querySelector("body > home-assistant").' \
                  'shadowRoot.querySelector("div > home-assistant-main").' \
                  'shadowRoot.querySelector("app-drawer-layout > div > partial-panel-resolver > ha-panel-scenes").' \
                  'shadowRoot.querySelector("div.main-box > div.main-box-content > div > div:nth-child(%s)' \
                  ' > ha-automation-card").shadowRoot.querySelector("div > div > div > div.content-top-item__scene' \
                  ' > span.action > div.auto > img")' % index
        img_src = self.browser.get_attribute_by_js_path(js_path, 'src')
        if ('scene_disable' in img_src and (str(active) == '1' or active is True)) \
                or ('scene_off' in img_src and (str(active) == '0' or active is False)):
            self.browser.click_btn_by_js_path(js_path)
        else:
            aklog_printf('当前场景状态已经是 %s' % active)

    def add_scenes(self, scenes_name, trigger_type, conditions: list, tasks: list):
        """
        添加场景
        trigger_type：any, all
        conditions: list类型，元素为字典：
        {'manual': '1',
        'device': {'room': 'Others', 'device_name': 'Relay1', 'action': 'ON'},
        'time': {'time_type': 'Set Time', 'time_val': '12:22', 'date_repeat': ''},
        'security': 'home'}
        tasks: list类型，
        {'http': 'http://192.168.10.39/111'}
        """
        aklog_printf()
        self.enter_scenes_page()
        self.browser.click_btn_by_js_path(self.ele_info['add_btn'])
        # 如果场景比较多，那么打开添加窗口会比较慢，需要多等一些时间
        if self.browser.is_visible_ele_by_js_path(self.ele_info['scenes_add_name'], wait_time=30):
            for i in range(30):
                if self.browser.get_attribute_by_js_path(self.ele_info['scenes_add_name'], 'value') != 'undefined':
                    aklog_printf('场景添加窗口已加载完成')
                    break
                else:
                    aklog_printf('场景添加窗口加载中，请等待...')
                    time.sleep(2)
                    continue
        self.write_config(self.ele_info['scenes_add_name'], scenes_name)
        self.add_scenes_trigger_type(trigger_type)
        # 添加场景条件
        for condition in conditions:
            for condition_type in condition:
                if condition_type == 'manual':
                    self.add_scenes_condition_manual()
                elif condition_type == 'time':
                    self.add_scenes_condition_time(condition['time']['time_type'], condition['time']['time_val'])
        # 添加场景任务
        for task in tasks:
            for task_type in task:
                if task_type == 'http':
                    self.add_scenes_task_send_http(task['http'])
        # 点击保存并判断是否添加成功
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_save_btn'])
        if self.browser.is_visible_ele_by_js_path(self.ele_info['dialog_tips'], wait_time=10, print_trace=False):
            tips = self.browser.get_attribute_by_js_path(self.ele_info['dialog_tips'], 'textContent')
            self.browser.click_btn_by_js_path(self.ele_info['dialog_ok_btn'])
            time.sleep(2)
            if tips and 'success' in tips:
                aklog_printf('添加场景成功')
                return True
            else:
                aklog_printf('添加场景失败： %s' % tips)
                self.browser.screen_shot()
                self.browser.click_btn_by_js_path(self.ele_info['scenes_add_cancel_btn'])
                return tips

    def add_scenes_trigger_type(self, trigger_type):
        """
        添加场景：选择触发类型
        trigger_type: any, all
        """
        aklog_printf()
        if trigger_type == 'any':
            self.browser.click_btn_by_js_path(self.ele_info['scenes_add_trigger_any_condition'])
        else:
            self.browser.click_btn_by_js_path(self.ele_info['scenes_add_trigger_all_condition'])

    def add_scenes_condition_manual(self):
        """添加场景条件：手动点击"""
        aklog_printf()
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_condition_add_btn'])
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_condition_manual_item'])

    def add_scenes_condition_time(self, time_type, time_str=None, date_repeat=None):
        """
        添加场景条件：时间设置
        time_type: 0 1 2，或者 Set Time，Sunrise，Sunset
        time_str: 12:22
        date_repeat: everyday，weekdays，weekends，或者数字字符串: 0123456，123，60
        """
        aklog_printf()
        time_type_info = {'Set Time': 0, 'Sunrise': 1, 'Sunset': 2}
        if str(time_type) in time_type_info:
            time_type_index = time_type_info[str(time_type)]
        else:
            time_type_index = int(time_type)
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_condition_add_btn'])
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_condition_time_item'])
        self.write_config(self.ele_info['scenes_add_condition_time_type'], time_type_index)
        if time_str and time_type_index == 0:
            hour = time_str.split(':')[0]
            minute = time_str.split(':')[1]
            self.write_config(self.ele_info['scenes_add_condition_time_picker_hours'], hour)
            self.write_config(self.ele_info['scenes_add_condition_time_picker_minutes'], minute)
        if date_repeat and time_type_index == 0:
            if date_repeat.lower() == 'everyday':
                self.browser.click_btn_by_js_path(self.ele_info['scenes_add_condition_time_repeat_everyday'])
            elif date_repeat.lower() == 'weekdays':
                self.browser.click_btn_by_js_path(self.ele_info['scenes_add_condition_time_repeat_weekdays'])
            elif date_repeat.lower() == 'weekends':
                self.browser.click_btn_by_js_path(self.ele_info['scenes_add_condition_time_repeat_weekends'])
            elif date_repeat.isdigit():
                for day in date_repeat:
                    day_js_path = 'document.querySelector("body > home-assistant").' \
                                  'shadowRoot.querySelector("scene-conditions-dialog").' \
                                  'shadowRoot.querySelector("ha-dialog > div > ha-condition-time").' \
                                  'shadowRoot.querySelector("#repeat-picker > mwc-check-list-item:nth-child(%s)").' \
                                  'shadowRoot.querySelector("span.mdc-deprecated-list-item__meta > mwc-checkbox").' \
                                  'shadowRoot.querySelector("div > input")' % (int(day) + 1)
                    self.browser.check_box_by_js_path(day_js_path)
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_condition_time_ok_btn'])

    def add_scenes_condition_device(self, device_info):
        """
        添加场景条件：选择设备触发
        device_info: dict类型，{'room': 'Others', 'device_name': 'Relay1', 'action': 'ON'}
        """
        aklog_printf()
        room_js_path = 'document.querySelector("body > home-assistant").' \
                       'shadowRoot.querySelector("scene-conditions-dialog").' \
                       'shadowRoot.querySelector("ha-dialog > div > ha-condition-devices").' \
                       'shadowRoot.querySelector("div > ha-cus-collapse")'
        # 先获取房间数量
        room_num = self.browser.get_ele_counts_by_js_path(room_js_path)
        for i in range(1, room_num + 1):
            # 再遍历所有房间，找到对应名称的房间
            room_js_path = room_js_path[0:-2] + ':nth-child(%s)")' % i
            room_name_js_path = room_js_path[0:-2] + ' > div:nth-child(1) > mwc-list-item > span")'
            if self.browser.get_attribute_by_js_path(room_name_js_path, 'textContent') != device_info['room']:
                continue
            # 找到房间之后，判断是否已经展开设备列表，没有的话，点击展开
            room_expand_js_path = room_js_path[0:-2] + ' > div:nth-child(1)")'
            if self.browser.get_attribute_by_js_path(room_expand_js_path, 'className') != 'room-collapse-expend':
                self.browser.click_btn_by_js_path(room_expand_js_path)
            # 选择设备，也要先遍历所有设备，找到对应名称的设备
            device_js_path = room_js_path[0:-2] + '> div:nth-child(2) > div'
            device_num = self.browser.get_ele_counts_by_js_path(device_js_path)
            for j in range(1, device_num + 1):
                device_js_path = device_js_path[0:-2] + ':nth-child(%s)")' % j
                device_name_js_path = device_js_path[0:-2] + ' > ha-cus-collapse").shadowRoot.querySelector("div > ' \
                                                             'div > div > slot > mwc-list-item > div > span")'
                if self.browser.get_attribute_by_js_path(device_name_js_path, 'textContent') != \
                        device_info['device_name']:
                    continue
                # 找到设备之后，点击展开
                self.browser.click_btn_by_js_path(device_name_js_path)
                # 选择操作，也要先遍历所有操作，找到对应名称的操作
                action_js_path = device_js_path[0:-2] + ' > ha-cus-collapse > div > div > mwc-list > div'
                action_num = self.browser.get_ele_counts_by_js_path(action_js_path)
                for k in range(1, action_num + 1):
                    action_js_path = action_js_path[0:-2] + ':nth-child(%s) > mwc-list-item")' % k
                    if self.browser.get_attribute_by_js_path(action_js_path, 'textContent') == \
                            device_info['action']:
                        # 找到操作之后点击选择
                        self.browser.click_btn_by_js_path(action_js_path)
                        return True
                aklog_printf('设备 %s 未找到 %s 操作' % (device_info['device_name'], device_info['action']))
                return False
            aklog_printf('房间 %s 未找到 %s 设备' % (device_info['room'], device_info['device_name']))
            return False
        aklog_printf('未找到 %s 房间' % device_info['room'])
        return False

    def add_scenes_condition_security(self, security_mode):
        """添加场景条件：选择布防模式触发"""
        aklog_printf()
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_condition_add_btn'])
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_condition_security_item'])
        time.sleep(2)
        security_js_path = 'document.querySelector("body > home-assistant").' \
                           'shadowRoot.querySelector("scene-conditions-dialog").' \
                           'shadowRoot.querySelector("ha-dialog > div > ha-condition-security").' \
                           'shadowRoot.querySelector("div > div > div")'
        default_security_list = ['Home', 'Night', 'Away']
        if security_mode in default_security_list:
            security_js_path = security_js_path[0:-2] + \
                               ':nth-child(1) > ha-cus-collapse > div > div > mwc-list-item:nth-child(%s)")' \
                               % (default_security_list.index(security_mode) + 1)
            self.browser.click_btn_by_js_path(security_js_path)
            return True
        else:
            security_num = self.browser.get_ele_counts_by_js_path(security_js_path)
            for i in range(2, security_num + 1):
                security_js_path = security_js_path[0:-2] + ':nth-child(%s) > mwc-list-item")' % i
                if self.browser.get_attribute_by_js_path(security_js_path, 'textContent') == security_mode:
                    self.browser.click_btn_by_js_path(security_js_path)
                    return True
            aklog_printf('未找到自定义的 %s 布防模式' % security_mode)
            return False

    def add_scenes_task_send_http(self, http_url):
        """添加场景任务：发送HTTP请求"""
        aklog_printf()
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_task_add_btn'])
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_task_send_http_item'])
        self.write_config(self.ele_info['scenes_add_task_send_http_input'], http_url)
        self.browser.click_btn_by_js_path(self.ele_info['scenes_add_task_send_http_ok_btn'])

    # </editor-fold>

    # <editor-fold desc="安防相关">

    def enter_security_page(self):
        aklog_printf()
        self.menu_select_enter_page(self.ele_info['menu_scenes'], self.ele_info['submenu_security'])

    def set_arming_mode(self, mode):
        """设置Arming模式"""
        aklog_printf()
        img_src = self.browser.get_attribute_by_js_path(self.ele_info['security_%s_item' % mode], 'src')
        if img_src and 'security_%s_selected' % mode not in img_src:
            self.browser.click_btn_by_js_path(self.ele_info['security_%s_item' % mode])
        elif not img_src:
            aklog_printf('Arming模式状态获取失败')
            self.browser.screen_shot()
        else:
            aklog_printf('当前 %s 模式已经被设置' % mode)

    def get_arming_mode_status(self, mode):
        """获取Arming模式状态"""
        aklog_printf()
        img_src = self.browser.get_attribute_by_js_path(self.ele_info['security_%s_item' % mode], 'src')
        if img_src and 'security_%s_selected' % mode in img_src:
            return True
        elif not img_src:
            aklog_printf('Arming模式状态获取失败')
            self.browser.screen_shot()
            return None
        else:
            return False

    def add_custom_arming_mode(self, mode_name, ):
        pass
    # </editor-fold>


if __name__ == '__main__':
    device_info = {'device_name': 'X933H', 'ip': '192.168.88.133'}
    device_config = config_parse_device_config('config_X933H_NORMAL')
    user_web = AkubelaUserWeb()
    user_web.init(libbrowser(device_info, device_config))
