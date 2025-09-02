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
import time
import traceback
from selenium.webdriver.common.keys import Keys


class AkubelaPanelWeb:

    # <editor-fold desc="初始化相关">
    def __init__(self):
        self.web_branch = None
        self.browser = None
        self.connect_type = 'lan'
        self.device_config = None
        self.device_info = None
        self.device_mac = ''
        self.device_name = ''
        self.device_name_log = ''
        self.web_admin_username = 'admin'
        self.web_admin_pwd = 'admin'
        self._rom_version = ''
        self.device_ip = ''
        self.login_url = ''
        self.ele_info = None
        self.login_status = False
        self.device_cfg_66 = ''
        self.device_cfg_43 = ''
        self.device_cfg_custom = ''
        self.device_cfg_pnp = ''
        self.device_cfg_URL = ''
        self.device_comm_cfg_66 = ''
        self.device_comm_cfg_43 = ''
        self.device_comm_cfg_custom = ''
        self.device_comm_cfg_pnp = ''
        self.device_comm_cfg_URL = ''
        self.device_config_dict_by_version = {}
        self.menu_xpath_info = {}
        self.tmp_device_config = None
        self.interactive_tln_or_ssh = None
        self.firmware_version = ''
        self.model_name = ''
        self.tln = None
        self.ssh = None
        self.tln_ssh_port_list = None
        self.tln_ssh_pwd_list = None
        self.version_branch = ''
        self.force_replace_old_version = False
        self.web_http_port = '80'
        self.capture_syslog_enable = False

    def init_without_start(self, browser=None):
        if browser:
            self.browser = browser
        self.device_config = browser.get_device_config()
        self.tmp_device_config = self.device_config
        self.device_info = browser.get_device_info()
        if 'device_name' in self.device_info:
            self.device_name = self.device_info['device_name']
            self.device_name_log = '[' + self.device_name + '] '
        if self.connect_type == 'lan':
            self.device_ip = self.device_info.get('ip').strip()
        else:
            self.device_ip = self.device_info.get('wifi_ip').strip()
        self.login_url = 'http://%s:%s' % (self.device_ip, self.web_http_port)
        aklog_debug("self.login:%s" % self.login_url)
        if 'MAC' in self.device_info:
            self.device_mac = self.device_info['MAC']
        elif 'mac' in self.device_info:
            self.device_mac = self.device_info['mac']
        if not self.version_branch:
            self.ele_info = self.device_config.get_device_normal_web_element_info('PANELWEB1_0')
        else:
            self.ele_info = self.device_config.get_device_web_element_info(self.version_branch, 'PANELWEB1_0')
        self.rom_version = param_get_rom_version()

        if self.device_config.get_autop_cfg_use_mac_enable():
            self.device_cfg_66 = self.device_config.get_dhcp_option_66_dir() + self.device_mac + '.cfg'
            self.device_cfg_43 = self.device_config.get_dhcp_option_43_dir() + self.device_mac + '.cfg'
            self.device_cfg_custom = self.device_config.get_dhcp_option_custom_dir() + self.device_mac + '.cfg'
            self.device_cfg_pnp = self.device_config.get_pnp_dir() + self.device_mac + '.cfg'
            self.device_cfg_URL = self.device_config.get_manual_URL_dir() + self.device_mac + '.cfg'
        else:
            self.device_cfg_66 = self.device_config.get_devicecfg_66()
            self.device_cfg_43 = self.device_config.get_devicecfg_43()
            self.device_cfg_custom = self.device_config.get_devicecfg_custom()
            self.device_cfg_pnp = self.device_config.get_devicecfg_pnp()
            self.device_cfg_URL = self.device_config.get_devicecfg_URL()

        self.device_comm_cfg_66 = self.device_config.get_devicecfg_66()
        self.device_comm_cfg_43 = self.device_config.get_devicecfg_43()
        self.device_comm_cfg_custom = self.device_config.get_devicecfg_custom()
        self.device_comm_cfg_pnp = self.device_config.get_devicecfg_pnp()
        self.device_comm_cfg_URL = self.device_config.get_devicecfg_URL()

        self.tln_ssh_port_list = self.device_config.get_tln_ssh_port_list()
        self.tln_ssh_pwd_list = self.device_config.get_tln_or_ssh_pwd()
        self.tln = TelnetConnection(
            self.device_ip, self.tln_ssh_port_list, 'root', self.tln_ssh_pwd_list, self.device_name)
        self.ssh = SSHConnection(
            self.device_ip, self.tln_ssh_port_list, 'root', self.tln_ssh_pwd_list, self.device_name)

    def init(self, browser=None):
        self.init_without_start(browser)
        self.browser.init()

    def put_rom_version(self, rom_version):
        """如果多个机型都需要升级，则可以在升级前传入版本号"""
        self._rom_version = rom_version

    @property
    def rom_version(self):
        return self._rom_version

    @rom_version.setter
    def rom_version(self, value):
        self._rom_version = value

    def start_and_login(self, url=None):
        if not self.is_opened_browser():
            self.browser.init()
        return self.login(url=url)

    def web_env_init(self):
        self.web_open_ssh()
        self.set_syslog_level_7()

    def web_start_and_init(self, url=None):
        """打开浏览器登录网页，并进行环境初始化，比如打开SSH，设置log等级为7等"""
        self.start_and_login(url)
        self.web_env_init()

    def browser_close_and_quit(self):
        self.browser.close_and_quit()

    def is_opened_browser(self):
        aklog_info(self.device_name_log + 'is_opened_browser')
        try:
            if self.browser is not None and self.browser.get_driver() is not None:
                aklog_info(self.device_name_log + 'browser is already opened')
                return True
            else:
                aklog_info(self.device_name_log + 'browser is not opened')
                return False
        except:
            aklog_error(self.device_name_log + str(traceback.format_exc()))
            return False

    def browser_close_and_reopen(self):
        if self.is_opened_browser():
            self.browser_close_and_quit()
        time.sleep(1)
        self.browser.init()

    def reset_imgs(self):
        self.browser.reset_imgs()

    def get_device_config_by_version(self, firmware_version):
        aklog_debug(self.device_name_log + 'get_device_config_by_version, %s' % firmware_version)
        if firmware_version:
            if firmware_version not in self.device_config_dict_by_version:
                if firmware_version == self.rom_version:
                    self.device_config_dict_by_version[firmware_version] = self.tmp_device_config
                else:
                    oem_id = firmware_version.split('.')[1]
                    oem_name = config_get_oemname(oem_id)
                    model_name = self.device_config.get_model_name()
                    self.device_config_dict_by_version[firmware_version] = \
                        config_parse_device_config_by_model_and_oem(model_name, oem_name, self.device_name)
            self.device_config = self.device_config_dict_by_version[firmware_version]

    def restore_device_config(self):
        aklog_debug(self.device_name_log + 'restore_device_config')
        self.device_config = self.tmp_device_config

    def put_connect_type(self, connect_type):
        self.connect_type = connect_type

    # </editor-fold>

    # <editor-fold desc="网页通用操作API">
    def menu_expand_and_click(self, menu_xpath):
        aklog_debug()
        if menu_xpath is None:
            aklog_error(self.device_name_log + '传入的菜单为None，请检查')
            return False
        self.browser.web_refresh(force=True)
        if not self.browser.is_exist_and_visible_ele_by_xpath(menu_xpath):
            aklog_debug('menu未找到，重新登录')
            self.login()
        self.browser.click_btn_by_xpath(menu_xpath)
        menu_class = self.browser.get_attribute_by_xpath(menu_xpath, 'className')
        aklog_debug("menu_class:%s" % menu_class)
        if not menu_class:
            aklog_debug('menu未找到，重新登录')
            self.login()
            self.browser.click_btn_by_xpath(menu_xpath)
            menu_class = self.browser.get_attribute_by_xpath(menu_xpath, 'className')
        if menu_class or 'ant-menu-item-selected' in menu_class:
            aklog_debug('%s 页面进入成功' % menu_xpath)
            return True
        else:
            aklog_error('%s 页面进入失败' % menu_xpath)
            self.browser.screen_shot()
            return False

    def web_refresh(self, wait_time=None, sec=1):
        if wait_time:
            time.sleep(wait_time)
        self.browser.web_refresh(sec)

    def screen_shot(self):
        self.browser.screen_shot()

    # 点击按钮操作
    def click_submit(self, sec=0.2, accept=True):
        self.browser.click_btn_by_xpath(self.ele_info['page_submit_xpath'], sec)
        if accept:
            for i in range(2):
                if self.browser.is_exist_alert():
                    self.browser.alert_confirm_accept()
                self.browser.set_implicitly_wait(10)
                if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['page_submit_xpath']):
                    aklog_debug(self.device_name_log + 'click submit success')
                    self.browser.restore_implicitly_wait()
                    return True
                elif i == 0:
                    self.browser.set_implicitly_wait(10)
                    continue
                else:
                    aklog_error(self.device_name_log + 'click submit failed')
                    self.browser.screen_shot()
                    self.browser.restore_implicitly_wait()
                    return False

    def click_cancel(self):
        self.browser.click_btn_by_xpath(self.ele_info['page_cancel_xpath'])
        self.browser.set_implicitly_wait(10)
        for i in range(2):
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['page_cancel_xpath']):
                aklog_debug(self.device_name_log + 'click cancel success')
                self.browser.restore_implicitly_wait()
                return True
            elif i == 0:
                if self.browser.is_exist_alert():
                    self.browser.alert_confirm_accept()
                continue
            else:
                aklog_error(self.device_name_log + 'click cancel failed')
                self.browser.screen_shot()
                self.browser.restore_implicitly_wait()
                return False

    def click_dialog_submit(self):
        self.browser.click_btn_by_xpath('//*[@class="el-button el-button--primary"]/span[text()="Confirm"]')

    def click_dialog_cancel(self):
        self.browser.click_btn_by_xpath('//*[@class="el-button el-button--primary"]/span[text()="Cancel"]')

    def click_refresh(self):
        self.browser.click_btn_by_xpath(
            '//*[@class="el-button ak-right-button el-button--default"]/span[text()="Refresh"]')

    def click_modal_submit(self):
        """点击编辑窗口的提交按钮"""
        self.browser.click_visible_ele_by_xpath(self.ele_info['modal_submit_btn'])

    def click_modal_cancel(self):
        """点击编辑窗口的取消按钮"""
        self.browser.click_visible_ele_by_xpath(self.ele_info['modal_cancel_btn'])

    def click_select_file_cancel(self):
        self.browser.click_visible_ele_by_xpath(self.ele_info['select_file_cancel_btn'])

    def click_select_file_upload(self):
        self.browser.click_visible_ele_by_xpath(self.ele_info['select_file_upload_btn'])

    def click_btn_by_xpath(self, ele_xpath, sec=0.2, visible=True):
        aklog_debug()
        return self.browser.click_btn_by_xpath(ele_xpath, sec, visible=visible)

    def click_btn_and_sleep_by_xpath(self, ele_xpath, sec=0.2, visible=True):
        """封装通过xpath进行button操作并延时"""
        aklog_debug()
        return self.browser.click_btn_by_xpath(ele_xpath, sec, visible=visible)

    def click_btn_by_text(self, text, sec=0.2, title=None):
        """通过按钮的文本来定位，需要页面上按钮是唯一的才行，不能存在两个相同名称的按钮"""
        if title:
            ele_xpath = '//label[text()="%s"]/../..//span[text()="%s"]/..' % (title, text)
        else:
            ele_xpath = '//span[text()="%s"]/..' % text
        return self.browser.click_btn_by_xpath(ele_xpath, sec)

    # 读写配置
    def write_config(self, id_name_xpath, *values, timeout=None, clear_input_by_keys=True):
        """
        判断大部分的通用网页元素类型, 选择输入框、复选框或者下拉框的方法操作
        id_name_xpath: webV4基本传入的是Xpath
        ps:
            1) 针对下拉框,xpath定位到[@role='combobox']这一级即可，value传入下拉选项显示的文本（str类型）
            如果下拉框为多项选择，则values可以传入多个
            下拉框选项value也可以传入选项序号（int类型），从0开始，这种主要用于Disabled和Enabled用0和1来表示
            2) 复选框, 勾选框： Xpath定位到input[@type="checkbox"], value传入True/False，或者1和0
            WEB4.0 清空输入框操作，必须要用退格键，否则使用clear()，网页提交时会认为没有修改导致提交失败，clear_input_by_keys默认为True
        """
        aklog_debug()
        try:
            ele = self.browser.adapt_element(id_name_xpath, timeout)
            if not ele:
                aklog_error(self.device_name_log + '元素不存在')
                return False
            elif not ele.is_enabled():
                aklog_error(self.device_name_log + '元素处于不可操作状态')
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
                aria_controls = ele.get_attribute('aria-controls')
                if 'ant-select-selection--multiple' in ele.get_attribute('class'):
                    # 多项选择先查找当前已选择的选项并移除
                    originally_selected_ele_list = ele.find_elements_by_xpath(
                        '%s//li/span[@class="ant-select-selection__choice__remove"]' % id_name_xpath)
                    for remove_ele in originally_selected_ele_list[::-1]:
                        self.browser.click_ele(remove_ele, 0.2)

                options_ele_xpath = []
                for value in values:
                    if isinstance(value, int):
                        # 如果传入的value是int类型，则当做选项的序号来选择，0表示第一个选项，1表示第二个选项，以此类推
                        value = value + 1
                        option_ele_xpath = '//div[@id="%s"]/ul/li[%s]' % (aria_controls, value)
                    else:
                        option_ele_xpath = '//div[@id="%s"]/ul/li[text()="%s"]' % (aria_controls, value)
                    options_ele_xpath.append(option_ele_xpath)
                self.browser.select_options_by_box_ele(ele, *options_ele_xpath)
            elif ele.get_attribute('class') == 'ant-select-selection-selected-value':
                # 下拉框，如果定位的不是[@role='combobox']这一级，而是它的子元素，那么需要找到[@role='combobox']这一级父节点
                combobox_ele = ele.find_element(By.XPATH, '../..')
                aria_controls = combobox_ele.get_attribute('aria-controls')
                if not aria_controls:
                    aklog_error('下拉框定位Xpath不正确，最好定位到[@role="combobox"]这一级节点')
                    return False
                # if 'ant-select-selection--multiple' in combobox_ele.get_attribute('class'):
                #     # 多项选择先查找当前已选择的选项并移除
                #     originally_selected_ele_list = combobox_ele.find_elements_by_xpath(
                #         '//li/span[@class="ant-select-selection__choice__remove"]')
                #     for remove_ele in originally_selected_ele_list[::-1]:
                #         self.browser.click_ele(remove_ele, 0.2)
                options_ele_xpath = []
                for value in values:
                    if isinstance(value, int):
                        # 如果传入的value是int类型，则当做选项的序号来选择，0表示第一个选项，1表示第二个选项，以此类推
                        value = value + 1
                        option_ele_xpath = '//div[@id="%s"]/ul/li[%s]' % (aria_controls, value)
                    else:
                        option_ele_xpath = '//div[@id="%s"]/ul/li[text()="%s"]' % (aria_controls, value)
                    options_ele_xpath.append(option_ele_xpath)
                self.browser.select_options_by_box_ele(combobox_ele, *options_ele_xpath)
            else:
                # 文本输入框
                value = values[0]
                # 有些输入框清空提交判断为空是否提示，不能用clear()方法，得用按键方式操作
                if not clear_input_by_keys:
                    ele.clear()
                    time.sleep(0.1)
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
                ele.send_keys(value)
            return True
        except:
            aklog_error(traceback.format_exc())
            return False

    def read_config(self, id_name_xpath, timeout=None):
        """
        封装获取大部分网页控件的显示值, 输入框、复选框或者下拉框.
        id_name_xpath: webV4基本传入的是Xpath
        ps:
            1) 针对下拉框, 读取的是被选择的选项，xpath定位到combobox这一级即可
            2) 复选框, 勾选框： Xpath定位到input[@type="checkbox"]
        """
        aklog_debug()
        try:
            ele = self.browser.adapt_element(id_name_xpath, timeout)
            if not ele:
                aklog_error(self.device_name_log + '元素不存在')
                return None
            if ele.get_attribute('type') == 'checkbox':
                value = ele.is_selected()
            elif ele.tag_name == 'label':
                value = ele.text
            elif ele.get_attribute('role') == 'combobox':
                # 如果为多项选择，则获取返回列表
                if ele.get_attribute('class') == 'ant-select-selection ant-select-selection--multiple':
                    value = ele.text
                    value = value.split('\n')
                else:
                    value = ele.text
            elif ele.get_attribute('class') == 'ant-select-selection-selected-value':
                value = ele.text
            else:
                value = ele.get_attribute('value')
            aklog_debug(self.device_name_log + 'value: %s, Type: %s' % (value, type(value)))
            return value
        except:
            aklog_error(traceback.format_exc())
            return None

    def upload_file(self, btn_xpath, file, upload_time=15, accept=True):
        """
        封装通用的上传文件方法，注意该方法主要用于上传小文件
        btn_xpath: Import或Upload按钮，点击打开上传文件窗口
        upload_time: 上传文件等待时间
        """
        aklog_debug()
        try:
            btn_ele = self.browser.adapt_element(btn_xpath)
            if not btn_ele:
                aklog_error(self.device_name_log + '元素不存在')
                return False
            self.browser.click_ele(btn_ele, 0.5)
            if file:
                self.browser.upload_file_by_xpath(self.ele_info['select_file_input'], file)
            if accept:
                # 如果上传格式错误的文件，可能会直接弹出失败提示
                submit_tips1 = self.get_submit_tips(1)
                if submit_tips1:
                    if submit_tips1 == 'Upload File Finished':
                        return True
                    else:
                        self.click_select_file_cancel()
                        return submit_tips1
                # 点击上传，然后获取上传结果
                self.click_select_file_upload()
                if self.browser.is_exist_alert():
                    self.alert_confirm_accept_and_sleep(0.5)
                submit_tips2 = self.get_submit_tips(upload_time)
                if submit_tips2 in ['Upload File Finished', 'Import Success']:
                    return True
                else:
                    self.click_select_file_cancel()
                    return submit_tips2
            else:
                self.click_select_file_cancel()
                return 1
        except:
            aklog_error(traceback.format_exc())
            return False

    def get_selected_option_by_xpath(self, ele_xpath):
        """获取下拉框已选择项，xpath定位到[@role='combobox']这一级即可"""
        aklog_debug(self.device_name_log + 'get_selected_option_by_xpath  ele_xpath: %s' % ele_xpath)
        return self.browser.get_value_by_xpath(ele_xpath)

    def get_select_options_list_by_xpath(self, ele_xpath):
        """获取下拉框列表，xpath定位到[@role='combobox']这一级即可"""
        aklog_debug(self.device_name_log + 'get_select_options_list_by_xpath  ele_xpath: %s' % ele_xpath)
        ele = self.browser.adapt_element(ele_xpath)
        if ele.get_attribute('role') == 'combobox':
            aria_controls = ele.get_attribute('aria-controls')
            option_ele_xpath = '//*[@id="%s"]/ul/li' % aria_controls
            # 获取列表元素前要先点击下拉框，展开列表才行
            self.browser.click_ele(ele)
            time.sleep(0.2)
            option_elements = self.browser.get_elements_by_xpath(option_ele_xpath)
            options_list = []
            for option_ele in option_elements:
                option_text = option_ele.text
                options_list.append(option_text)
            self.browser.click_ele(ele)
            time.sleep(0.2)
            aklog_debug('options_list: %s' % options_list)
            return options_list
        else:
            aklog_error('下拉框类型不一致，请检查')
            return None

    def get_text_by_label_name(self, label, title=None):
        """根据label名称获取对应的内容"""
        aklog_debug()
        if title:
            xpath = '//label[text()="%s"]/../..//label[text()="%s"]/../label[2]' % (title, label)
        else:
            xpath = '//label[text()="%s"]/../label[2]' % label
        return self.browser.get_value_by_xpath(xpath)

    # 左右两个选择框相关操作
    def set_multi_selects_enable(self, selects, title=None):
        """
        左右两个选择框（比如Audio Codecs），先把右边选择框的全部移到左边，然后再选择左边的选项移动到右边的启用选择框里
        selects: None、all、名称列表，如果为None，则不选择，如果为all，则全部选择
        名称列表传入List类型，可以同时选择多个，如果为空list，则全部设置为未选择
        title: 如果一个页面存在多个这种选择框，则要传入标题
        """
        aklog_debug()
        if selects is None:
            aklog_debug('不进行选择')
            return
        # 先将已选择的移到未选择
        if title:
            enabled_options = '//label[text()="%s"]/../..' \
                              '//*[@class="ak-common-transfer-div"]/div/div[3]//li//input' % title
        else:
            enabled_options = '//*[@class="ak-common-transfer-div"]/div/div[3]//li//input'
        self.browser.check_multi_boxs_by_xpath(enabled_options)
        time.sleep(0.5)
        if title:
            left_btn = '//label[text()="%s"]/../..' \
                       '//*[@class="anticon anticon-left"]/..' % title
        else:
            left_btn = '//*[@class="anticon anticon-left"]/..'
        self.browser.click_btn_by_xpath(left_btn)
        if selects:
            if selects == 'all':
                if title:
                    disabled_options = '//label[text()="%s"]/../..' \
                                       '//*[@class="ak-common-transfer-div"]/div/div[1]//li//input' % title
                else:
                    disabled_options = '//*[@class="ak-common-transfer-div"]/div/div[1]//li//input'
                self.browser.check_multi_boxs_by_xpath(disabled_options)
                time.sleep(0.5)
            else:
                # 根据名称选择
                for select in selects:
                    if title:
                        disabled_options = '//label[text()="%s"]/../..//*[@class="ak-common-transfer-div"]' \
                                           '/div/div[1]//li[@title="%s"]//input' % (title, select)
                    else:
                        disabled_options = '//*[@class="ak-common-transfer-div"]/div/div[1]//li[@title="%s"]//input'
                    self.browser.check_box_by_xpath(disabled_options)
                time.sleep(0.5)
            if title:
                right_btn = '//label[text()="%s"]/../..' \
                            '//*[@class="anticon anticon-right"]/..' % title
            else:
                right_btn = '//*[@class="anticon anticon-right"]/..'
            self.browser.click_btn_by_xpath(right_btn)

    def get_multi_selected_options(self, title=None):
        """
        左右两个选择框（比如Audio Codecs），获取右边已选择的选项
        title: 如果一个页面存在多个这种选择框，则要传入标题
        """
        if title:
            enabled_options = '//label[text()="%s"]/../..' \
                              '//*[@class="ak-common-transfer-div"]/div/div[3]//li' % title
        else:
            enabled_options = '//*[@class="ak-common-transfer-div"]/div/div[3]//li'
        return self.browser.get_elements_attribute_by_xpath(enabled_options, 'title')

    def move_multi_selects_sort(self, option_list: list, title=None):
        """
        左右两个选择框（比如Audio Codecs），右边启用的选择框按上下按钮进行选项排序
        title：如果一个页面存在多个这种选择框，则要传入标题
        option_list: list类型，列表范围可以比当前选择框内选项列表少，如果少于当前选项列表，则只移动部分到前几个
        思路：
        获取当前的列表顺序，然后根据目标顺序的元素，依次将元素移动到目标顺序的位置，
        比如当前顺序为['PCMU', 'PCMA', 'G729', 'G722']，要设置成 ['G722', 'PCMA', 'PCMU', 'G729']
        先移动'G722'，原来位置4要移动到位置1，需要往上移动3步，顺序变成['G722', 'PCMU', 'PCMA', 'G729']
        然后移动PCMA，此时PCMA变成在位置3，目标位置2，需要往上移动1步，顺序变成['G722', 'PCMA', 'PCMU', 'G729']
        """
        aklog_debug()
        if not isinstance(option_list, list):
            aklog_debug('传入的option_list不是list类型')
            return False
        if title:
            up_btn = '//label[text()="%s"]/../..//*[@class="ak-common-transfer-button"]/button[1]' % title
        else:
            up_btn = '//*[@class="ak-common-transfer-button"]/button[1]'
        tmp_list = self.get_multi_selected_options(title)
        for x in option_list:
            if tmp_list != option_list:
                if x not in tmp_list:
                    continue
                delta = tmp_list.index(x) - option_list.index(x)
                if delta == 0:
                    continue
                # 目标元素一个个依次往上移动
                if title:
                    enabled_option = '//label[text()="%s"]/../..//*[@class="ak-common-transfer-div"]' \
                                     '/div/div[3]//li[@title="%s"]//input' % (title, x)
                else:
                    enabled_option = '//*[@class="ak-common-transfer-div"]/div/div[3]//li[@title="%s"]//input'
                self.browser.check_box_by_xpath(enabled_option)
                for i in range(abs(delta)):
                    self.browser.click_btn_by_xpath(up_btn)
                self.browser.uncheck_box_by_xpath(enabled_option)
                tmp_list = self.get_multi_selected_options(title)
                continue
            else:
                aklog_debug('排序完成')
                return True
        aklog_error('排序失败')
        return False

    def get_import_file_format_tips(self, import_btn):
        """获取文件上传的格式提示语"""
        self.browser.click_btn_by_xpath(import_btn)
        time.sleep(1)
        format_tips = self.browser.get_visible_value_by_xpath('//*[@class="ak-modal-file-input-title-label"]')
        self.click_select_file_cancel()
        return format_tips

    # 表格翻页、删除相关
    def click_page_prev(self, title=None):
        if title:
            ele_xpath = '//label[text()="%s"]/../..//span[text()="Prev"]/..' % title
        else:
            ele_xpath = '//span[text()="Prev"]/..'
        self.click_btn_by_xpath(ele_xpath)

    def click_page_next(self, title=None):
        if title:
            ele_xpath = '//label[text()="%s"]/../..//span[text()="Next"]/..' % title
        else:
            ele_xpath = '//span[text()="Next"]/..'
        self.click_btn_by_xpath(ele_xpath)

    def get_table_total_num(self, title=None, refresh=False):
        """
        获取列表所有数量
        cur_page： 有些列表无法获取总数量，那么只能获取当前页面的数量，注意列表总数量不能多于一页数量
        """
        aklog_info()
        if title:
            ele_xpath = '//label[text()="%s"]/../..//*[@class="ak-common-table-footer"]/label[2]' % title
        else:
            ele_xpath = '//*[@class="ak-common-table-footer"]/label[2]'
        if refresh:
            self.web_refresh()
        total_num = self.browser.get_value_by_xpath(ele_xpath)
        if total_num is not None:
            total_num = int(re.sub(r'\D', '', total_num))
        else:
            # 先获取总页数，如果大于1，那么获取下第一页的数量，然后切换到最后一页获取最后一页的数量，计算出总数量
            page_num = self.get_total_page_num(title)
            if page_num == 1:
                total_num = self.get_table_cur_page_row_num(title)
            elif page_num > 1:
                self.go_to_page_by_index(page_num, title)
                last_page_row_num = self.get_table_cur_page_row_num(title)
                self.go_to_page_by_index(1, title)
                first_page_row_num = self.get_table_cur_page_row_num(title)
                total_num = (page_num - 1) * first_page_row_num + last_page_row_num
            else:
                aklog_error('获取不到页数，无法计算数量')
        aklog_info('total_num: %s' % total_num)
        return total_num

    def get_table_cur_page_row_num(self, title=None):
        """有些列表无法获取总数量，那么只能获取当前页面的数量"""
        tr_xpath = '//tbody/tr'
        if title:
            tr_xpath = '//label[text()="%s"]/../..' + tr_xpath
        counts = self.browser.get_ele_counts_by_xpath(tr_xpath)
        return counts

    def get_total_page_num(self, title=None):
        """获取列表页数"""
        aklog_info()
        if title:
            ele_xpath = '//label[text()="%s"]/../..' \
                        '//*[@class="ak-common-table-footer"]/span[contains(text(), "/")]' % title
        else:
            ele_xpath = '//*[@class="ak-common-table-footer"]/span[contains(text(), "/")]'
        page_num = self.browser.get_value_by_xpath(ele_xpath)
        total_page_num = int(page_num.split('/')[1].strip())
        aklog_info('total_page_num: %s' % total_page_num)
        return total_page_num

    def get_cur_page_num(self, title=None):
        """获取当前位于第几页"""
        if title:
            ele_xpath = '//label[text()="%s"]/../..' \
                        '//*[@class="ak-common-table-footer"]/span[contains(text(), "/")]' % title
        else:
            ele_xpath = '//*[@class="ak-common-table-footer"]/span[contains(text(), "/")]'
        page_num = self.browser.get_value_by_xpath(ele_xpath)
        cur_page_num = int(page_num.split('/')[0].strip())
        return cur_page_num

    def get_table_attribute_info(self, attribute, title=None, **base_attr):
        """
        获取列表信息，根据某个属性（比如id或name），去获取其他属性的值
        attribute: 想要获取的属性值
        base_attr: 选择的根据属性，一般为id或者name，取列表标题th节点key值，id='1', 或 name='test'，传入一个即可
        title: 列表的标题
        """
        total_num = self.get_table_total_num()
        if not total_num:
            aklog_info('列表没有数据')
            return None
        if title:
            next_ele_xpath = '//label[text()="%s"]/../..//span[text()="Next"]/..' % title
            key_ele_xpath = '//label[text()="%s"]/../..//thead/tr/th' % title
        else:
            next_ele_xpath = '//span[text()="Next"]/..'
            key_ele_xpath = '//thead/tr/th'

        # 获取标题列表
        key_list = self.browser.get_elements_attribute_by_xpath(key_ele_xpath, 'key')
        # 获取根据属性的key和value值
        base_key, base_value = tuple(base_attr.items())[0]
        # 然后获取根据属性位于列表中哪一列
        base_index = key_list.index(base_key)

        row = 1
        while row <= total_num:
            value_list = []
            if title:
                base_ele_xpath = '//label[text()="%s"]/../..//tbody/tr[%s]/td[%s]//label' % (title, row, base_index)
            else:
                base_ele_xpath = '//tbody/tr[%s]/td[%s]//label' % (row, base_index)

            get_base_value = self.browser.get_value_by_xpath(base_ele_xpath, 0.5)
            if get_base_value == base_value:
                for col in range(1, len(key_list) + 1):
                    if title:
                        value_ele_xpath = '//label[text()="%s"]/../..//tbody/tr[%s]/td[%s]//label' % (title, row, col)
                    else:
                        value_ele_xpath = '//tbody/tr[%s]/td[%s]//label' % (row, col)
                    value = self.browser.get_value_by_xpath(value_ele_xpath, 0.5)
                    if value is None:
                        value = ''
                    value_list.append(value)
                row_info = dict(zip(key_list, value_list))
                return row_info.get(attribute)
            elif get_base_value is None and self.browser.get_ele_status_by_xpath(next_ele_xpath):
                self.click_btn_by_xpath(next_ele_xpath)
                continue
            else:
                row += 1
                continue
        aklog_info('未找到')
        return None

    def go_to_page_by_index(self, index, title=None):
        if title:
            go_num_input_xpath = '//label[text()="%s"]/../..//input[@role="spinbutton"]' % title
            go_btn_xpath = '//label[text()="%s"]/../..//span[text()="Go"]/..' % title
        else:
            go_num_input_xpath = '//input[@role="spinbutton"]'
            go_btn_xpath = '//span[text()="Go"]/..'
        self.write_config(go_num_input_xpath, str(index))
        self.click_btn_by_xpath(go_btn_xpath)

    def table_page_turning_test(self, title=None):
        """列表翻页测试，需要事先添加超过一页的数量"""
        aklog_info(self.device_name_log + 'page_turning_test')
        # 一个页面如果存在多个列表，那么需要根据标题选择
        if title:
            prev_btn_xpath = '//label[text()="%s"]/../..//span[text()="Prev"]/..' % title
            next_btn_xpath = '//label[text()="%s"]/../..//span[text()="Next"]/..' % title
        else:
            prev_btn_xpath = '//span[text()="Prev"]/..'
            next_btn_xpath = '//span[text()="Next"]/..'

        self.web_refresh()
        time.sleep(2)
        total_page_num = self.get_total_page_num(title)
        if total_page_num <= 1:
            aklog_error('当前页数没有超过1页，翻页测试失败，请检查是否添加足够数量')
            return False
        result = True
        # 在第一页时先检查Prev和Next按钮，检查当前页数
        if self.get_cur_page_num(title) != 1:
            aklog_error('当前不是在第一页')
            result = False
        page_prev_status = self.browser.get_ele_status_by_xpath(prev_btn_xpath)
        if page_prev_status:
            aklog_error('在第一页时Prev按钮应该为不可点击状态')
            result = False
        page_next_status = self.browser.get_ele_status_by_xpath(next_btn_xpath)
        if not page_next_status:
            aklog_error('在第一页时Next按钮应该为可点击状态')
            result = False

        # 切换到第二页，检查Prev按钮
        self.click_page_next(title)
        time.sleep(1)
        if self.get_cur_page_num(title) != 2:
            aklog_error('当前不是在第二页')
            result = False
        page_prev_status = self.browser.get_ele_status_by_xpath(prev_btn_xpath)
        if not page_prev_status:
            aklog_error('在第二页时Prev按钮应该为可点击状态')
            result = False
        page_next_status = self.browser.get_ele_status_by_xpath(next_btn_xpath)
        if total_page_num == 2 and page_next_status:
            aklog_error('在第二页，并且总页数只有2页，Next按钮应该为不可点击状态')
            result = False
        elif total_page_num > 2 and not page_next_status:
            aklog_error('在第二页，总页数超过2页，Next按钮应该为可点击状态')
            result = False

        # 跳转的方式跳到第一页
        self.go_to_page_by_index(1, title)
        time.sleep(1)
        if self.get_cur_page_num(title) != 1:
            aklog_error('当前不是在第一页')
            result = False
        page_prev_status = self.browser.get_ele_status_by_xpath(prev_btn_xpath)
        if page_prev_status:
            aklog_error('在第一页时Prev按钮应该为不可点击状态')
            result = False
        page_next_status = self.browser.get_ele_status_by_xpath(next_btn_xpath)
        if not page_next_status:
            aklog_error('在第一页时Next按钮应该为可点击状态')
            result = False

        # 跳转的方式跳到最后一页
        self.go_to_page_by_index(total_page_num, title)
        time.sleep(1)
        if self.get_cur_page_num(title) != total_page_num:
            aklog_error('当前不是在最后一页')
            result = False
        page_prev_status = self.browser.get_ele_status_by_xpath(prev_btn_xpath)
        if not page_prev_status:
            aklog_error('在最后一页时Prev按钮应该为可点击状态')
            result = False
        page_next_status = self.browser.get_ele_status_by_xpath(next_btn_xpath)
        if page_next_status:
            aklog_error('在最后一页，Next按钮应该为不可点击状态')
            result = False
        return result

    def click_table_delete(self, title=None):
        if title:
            ele_xpath = '//label[text()="%s"]/../..' \
                        '//span[@class="ak-common-table-footer-btn-label" and text()="Delete"]/..' % title
        else:
            ele_xpath = '//span[@class="ak-common-table-footer-btn-label" and text()="Delete"]/..'
        self.click_btn_by_xpath(ele_xpath)

    def click_table_delete_all(self, title=None):
        if title:
            ele_xpath = '//label[text()="%s"]/../..' \
                        '//span[@class="ak-common-table-footer-btn-label" and text()="Delete All"]/..' % title
        else:
            ele_xpath = '//span[@class="ak-common-table-footer-btn-label" and text()="Delete All"]/..'
        self.click_btn_by_xpath(ele_xpath)

    def delete_table_by_index(self, index, confirm=True, title=None):
        """列表根据序号选择删除, index可以传入：'1', '123'"""
        if title:
            for i in str(index):
                self.write_config('//label[text()="%s"]/../..//tbody/tr[%s]/td[1]//input' % (title, i), 1)
        else:
            for i in str(index):
                self.write_config('//tbody/tr[%s]/td[1]//input' % i, 1)
        self.click_table_delete(title)
        if confirm:
            self.browser.alert_confirm_accept()
        else:
            self.browser.alert_confirm_cancel()

    def delete_table_all(self, title=None):
        """删除列表所有"""
        if title:
            delete_all_btn_xpath = '//label[text()="%s"]/../..//span[@class="ak-common-table-footer-btn-label" ' \
                                   'and text()="Delete All"]/..' % title
        else:
            delete_all_btn_xpath = '//span[@class="ak-common-table-footer-btn-label" and text()="Delete All"]/..'
        self.web_refresh()
        if self.browser.get_ele_status_by_xpath(delete_all_btn_xpath):
            self.click_btn_by_xpath(delete_all_btn_xpath)
            self.browser.alert_confirm_accept()
            time.sleep(0.5)
        else:
            aklog_info(self.device_name_log + 'Delete All不可点击，列表应该已被全部删除')

    def table_delete_test(self, title=None):
        """
        表格删除测试，需要先进入列表页面，且需要先添加至少2条以上数据
        有些列表无法获取总数量，那么只能获取当前页面的数量，注意列表总数量不能多于一页数量
        """
        aklog_info()
        self.web_refresh()
        time.sleep(2)
        total_num1 = self.get_table_total_num(title)
        if total_num1 < 2:
            aklog_error('列表数量太少，请先添加至少大于2条')
            return False
        result = True
        self.delete_table_by_index('1', False, title)
        total_num2 = self.get_table_total_num(title, True)
        if total_num2 != total_num1:
            aklog_error('取消删除失败，仍被删除')
            result = False
        self.delete_table_by_index('1', True, title)
        total_num3 = self.get_table_total_num(title, True)
        if total_num3 >= total_num2:
            aklog_error('删除失败')
            result = False
        self.delete_table_all(title)
        total_num4 = self.get_table_total_num(title, True)
        if total_num4 != 0:
            aklog_error('删除所有失败')
            result = False
        return result

    # 弹窗相关
    def alert_confirm_accept_and_sleep(self, sec=0.2):
        """封装web端弹窗确认操作并延时"""
        self.browser.alert_confirm_accept()
        time.sleep(sec)

    def click_alert_ok(self):
        """封装web端弹窗确认操作，该弹窗不同于浏览器的弹窗确认"""
        aklog_info('click_alert_ok')
        self.browser.click_btn_by_xpath(self.ele_info['alert_ok'])

    def click_alert_cancel(self):
        """封装web端弹窗取消操作，该弹窗不同于浏览器的弹窗确认"""
        aklog_info('click_alert_cancel')
        self.browser.click_btn_by_xpath(self.ele_info['alert_cancel'])

    def get_alert_tips_and_confirm(self, wait_time=None):
        """网页获取弹窗消息并确认，该弹窗不同于浏览器的弹窗确认"""
        alert_tips = self.browser.get_value_by_xpath(self.ele_info['alert_tips'], wait_time)
        if alert_tips:
            self.click_alert_ok()
        return alert_tips

    def web_get_alert_text_and_confirm(self, wait_time=None):
        """网页获取弹窗消息并确认"""
        if wait_time:
            alert_text = self.browser.get_alert_text(wait_time)
        else:
            alert_text = self.browser.get_alert_text()
        if alert_text:
            self.browser.alert_confirm_accept()
        return alert_text

    # 提交结果、输入框结果判断
    def get_edit_red_tips(self, id_name_xpath=None):
        """
        获取输入框置红提示语，如果同时编辑多个输入框，可能会有多个置红提示
        id_name_xpath为None时，将获取页面所有的置红输入框的提示语
        """
        aklog_info()
        if id_name_xpath:
            ele = self.browser.adapt_element(id_name_xpath)
            if not ele:
                aklog_error('%s 元素不存在' % id_name_xpath)
                return None
            style = ele.get_attribute('style')
            if 'rgb(255, 86, 96)' in style:
                self.browser.move_mouse_to_element(ele, 1)
                red_tip = self.browser.get_visible_value_by_xpath('//span[@class="ak-tooltips-label"]')
                if red_tip is None:
                    self.screen_shot()
                return red_tip
            else:
                return None
        else:
            elements = self.browser.get_elements_by_xpath('//*[contains(@style, "rgb(255, 86, 96)")]')
            if not elements:
                aklog_error('不存在置红提示')
                return None
            red_tips = []
            ele_counts = len(elements)
            time.sleep(2)
            for i in range(ele_counts):
                for j in range(2):
                    self.browser.move_mouse_to_element(elements[i], 1)
                    red_tip = self.browser.get_visible_value_by_xpath(
                        '(//span[@class="ak-tooltips-label"])[%s]' % (i + 1))
                    if red_tip:
                        red_tips.append(red_tip)
                        break
                    if j == 0:
                        # 如果没获取到置红提示框，可能是置红输入框被覆盖住，导致鼠标移动悬停失败，先把鼠标移到左边然后再重新移动鼠标悬停
                        self.browser.move_mouse_by_offset(-600, 0, 1)
                        continue
                    else:
                        self.screen_shot()
                        break

            if len(red_tips) == 1:
                red_tips = red_tips[0]
            return red_tips

    def get_submit_tips(self, wait_time=None):
        """获取右上角提交提示语"""
        aklog_info()
        if wait_time:
            retry_counts = max(round(wait_time / 2), 1)
        else:
            retry_counts = 1
        i = j = 0
        while i < retry_counts:
            tips = self.browser.get_value_by_xpath(self.ele_info['submit_tips'], 2, print_trace=False)
            if tips:
                return tips
            elif tips == '' and j < 3:
                time.sleep(1)
                j += 1
                continue
            else:
                time.sleep(1)
                i += 1
                continue
        aklog_info('get submit tips failed')
        return None

    def is_exist_submit_successfully_tips(self, wait_time=None):
        return 'Submitted successfully!' == self.get_submit_tips(wait_time)

    def get_submit_result(self, id_name_xpath=None, is_modal=False, wait_time=None):
        """
        判断提交是否成功
        如果只判断一个输入框的提交结果，可以传入元素定位信息
        is_modal: 是否为编辑窗口，点击取消的按钮跟页面的Cancel不一致
        """
        aklog_info()
        submit_tips = self.get_submit_tips(wait_time)
        if submit_tips:
            if submit_tips == 'Submitted successfully!':
                aklog_info('提交保存成功')
                return True
            else:
                aklog_error('提交保存失败')
                return submit_tips

        red_tips = self.get_edit_red_tips(id_name_xpath)
        if red_tips:
            self.browser.screen_shot()
            if is_modal:
                self.click_modal_cancel()
            else:
                self.click_cancel()
            aklog_error('存在置红提示，提交保存失败')
            return red_tips

        alert_tips = self.get_alert_tips_and_confirm(wait_time)
        if alert_tips:
            aklog_error('存在弹窗提示，提交保存失败')
            return alert_tips

        alert_text = self.browser.get_alert_text()
        if alert_text:
            self.alert_confirm_accept_and_sleep()
            aklog_error('存在弹窗提示，提交保存失败')
            return alert_text
        else:
            if is_modal:
                self.click_modal_cancel()
            else:
                self.click_cancel()
            aklog_info('提交保存成功，但可能页面没有任何修改')
            self.browser.screen_shot()
            return True

    def judge_input_int_range(self, id_name_xpath, write_data, input_min, input_max, return_tips=False):
        """
        封装测试, 输入框有效范围是 min~ max
        eg:
            测试IP port有效范围是整数, 范围1~65535
            judge_input_int_range('cDirectIPPort',5060, 1, 65535)
        """
        write_data = str(write_data)
        self.write_config(id_name_xpath, write_data, clear_input_by_keys=True)
        time.sleep(0.5)
        self.click_submit(accept=False)
        if write_data.isdigit() and int(write_data) in range(int(input_min), int(input_max) + 1):
            self.browser.web_refresh()
            ret = self.read_config(id_name_xpath)
            if not ret:
                aklog_error(self.device_name_log + '元素: %s 输入了 %s 保存失败!' % (id_name_xpath, write_data))
                self.click_cancel()
            return ret == write_data
        else:
            ret = self.get_submit_result(id_name_xpath)
            if ret is True:
                aklog_info(self.device_name_log + '元素: %s 输入了 %s, 不在有效范围内, 没有报错!'
                           % (id_name_xpath, write_data))
                return False
            else:
                self.click_cancel()
                if return_tips:
                    return ret
                else:
                    return True

    def judge_input_submit_result(self, id_name_xpath, write_data, limit_length=None, return_tips=False):
        """
        封装测试输入框提交结果，limit_length为输入框限制长度
        return: True表示保存成功，False表示保存失败，如果return_tips为True，则保存失败返回提示语
        """
        write_data = str(write_data)
        self.write_config(id_name_xpath, write_data, clear_input_by_keys=True)
        time.sleep(0.5)
        self.click_submit(accept=False)
        submit_result = self.get_submit_result(id_name_xpath)
        if submit_result is True:
            self.browser.web_refresh()
            input_value = self.read_config(id_name_xpath)
            if input_value is None:
                aklog_error('保存失败，页面显示可能有异常')
                self.screen_shot()
                return False
            if limit_length:
                write_data = write_data[0:limit_length]
            if input_value == write_data:
                aklog_info(self.device_name_log + '保存成功')
                return True
            elif '***' in input_value or '...' in input_value:
                aklog_info(self.device_name_log + '密码保存成功')
                return True
            else:
                aklog_error(self.device_name_log + '保存结果跟输入不一致，或密码保存位数不正确')
                self.screen_shot()
                return False
        else:
            aklog_error(self.device_name_log + '保存失败，提示语：%s' % submit_result)
            if return_tips:
                # 返回提示语可以用来测试提交失败的情况
                return submit_result
            else:
                return False

    def input_edit_and_sleep_by_id(self, edit_id, content, sec=0.2):
        """封装通过id输入edit操作并延时"""
        self.browser.input_edit_by_id(edit_id, content)
        time.sleep(sec)

    def input_edit_and_sleep_by_xpath(self, edit_xpath, content, sec=0.2):
        """封装通过id输入edit操作并延时"""
        self.write_config(edit_xpath, content)
        time.sleep(sec)

    def input_edit_and_sleep_by_name(self, edit_id, content, sec=0.2):
        """封装通过name输入edit操作并延时"""
        self.browser.input_edit_by_name(edit_id, content)
        time.sleep(sec)

    # 时间日期输入框设置
    def input_date_by_xpath(self, ele_xpath, date_str):
        """设置日期方法，date_str格式: 2022-02-28"""
        aklog_info(self.device_name_log + 'input_date_by_xpath, ele_xpath: %s, date: %s' % (ele_xpath, date_str))
        date_title1 = trans_date_fmt(date_str, '%Y-%m-%d', '%#d %B %Y')
        date_title2 = trans_date_fmt(date_str, '%Y-%m-%d', '%B %#d, %Y')
        self.click_btn_by_xpath(ele_xpath, 0.5)
        self.write_config('//*[@class="ant-calendar-date-input-wrap"]/input', date_str)
        time.sleep(0.5)
        self.click_btn_by_xpath('//*[@title="%s" or @title="%s"]' % (date_title1, date_title2))

    def input_time_by_xpath(self, ele_xpath, time_str):
        """设置时间方法，time_str格式：11:08 or 11:08:22"""
        aklog_info(self.device_name_log + 'input_time_by_xpath, ele_xpath: %s, time: %s' % (ele_xpath, time_str))
        self.browser.click_btn_by_xpath(ele_xpath)
        time.sleep(0.5)
        self.write_config('//*[@class="ant-time-picker-panel-input "]', '%s ' % time_str)
        time.sleep(0.5)
        self.click_btn_by_xpath('//*[@class="ant-time-picker-panel-addon"]/button')

    def visit_cloud_remote_url_on_new_label(self, url, close=True):
        """访问云平台远程控制URL，并确认是否可以正常登录"""
        self.browser.new_window()
        self.browser.switch_window(1)
        for j in range(4):
            timeout = 60 * (j + 1)
            if self.browser.visit_url(url, timeout=timeout):
                break
            elif j == 3:
                aklog_error(self.device_name_log + '访问云平台远程控制URL失败')
                self.browser.close_window()
                self.browser.switch_window(0)
                return False

        for i in range(5):
            if self.browser.is_exist_ele_by_xpath(self.ele_info['login_username_xpath']):
                break
            else:
                time.sleep(3)
                self.browser.web_refresh()
                continue
        login_status = self.login_status
        result = self.login(url)
        self.login_status = login_status
        if close:
            self.browser.close_window()
            self.browser.switch_window(0)
        return result

    # </editor-fold>

    # <editor-fold desc="登录相关">
    def login(self, url=None, raise_enable=True):
        """登录网页"""
        aklog_info(self.device_name_log + 'login')
        if not url:
            url = self.login_url
        if not self.browser.visit_url(url):
            self.browser.screen_shot()
            self.login_status = False
            if raise_enable:
                self.browser_close_and_quit()
                time.sleep(2)
                raise RuntimeError
            else:
                return False
        self.browser.web_refresh(force=True)
        self.web_admin_pwd = self.device_config.get_web_admin_passwd()
        for i in range(3):
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath']):
                self.write_config(self.ele_info['login_username_xpath'], self.web_admin_username)
                self.write_config(self.ele_info['login_password_xpath'], self.web_admin_pwd)
                self.browser.click_btn_by_class_name(self.ele_info['login_btn_class'])
                time.sleep(0.5)
                submit_tips = self.get_submit_tips()
                if submit_tips == 'Incorrect password or username!':
                    aklog_error('登录用户名和密码错误，请检查')
                    break
                elif submit_tips == 'Login is limited, please wait for 3 minutes!':
                    aklog_info('登录3分钟限制，等待重试')
                    time.sleep(190)
                    continue
                elif self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['top_logout_class']):
                    aklog_info(self.device_name_log + '登录网页 %s 成功' % url)
                    self.login_status = True
                    return True
            elif self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['top_logout_class']):
                aklog_info(self.device_name_log + '网页已登录，无需再重新登录')
                self.login_status = True
                return True
            else:
                time.sleep(3)
                self.browser.web_refresh(force=True)
                continue

        aklog_fatal('登录网页 %s 失败' % url)
        self.browser.screen_shot()
        self.login_status = False
        if raise_enable:
            self.browser_close_and_quit()
            time.sleep(2)
            raise RuntimeError
        else:
            return False

    def user_login(self, username, password):
        """
        封装: 另外封装, 不去影响基础接口.
        输入username和password登陆界面. 用于测试user, admin登陆登出.
        """
        self.write_config(self.ele_info['login_username_xpath'], username)
        self.write_config(self.ele_info['login_password_xpath'], password)
        self.browser.click_btn_by_class_name(self.ele_info['login_btn_class'])

    def web_logout(self):
        aklog_info(self.device_name_log + 'web_logout')
        self.browser.web_refresh(force=True)
        if self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['top_logout_class']):
            self.browser.click_btn_by_class_name(self.ele_info['top_logout_class'])
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath']):
            aklog_info(self.device_name_log + '网页已登出')
            return True
        else:
            aklog_error(self.device_name_log + '网页登出失败')
            self.browser.screen_shot()
            return False

    def judge_in_login_page(self):
        """
        封装: 判断在登陆界面
        """
        ret = self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath'])
        # ret2 = self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_password_xpath'])
        # ret3 = self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['login_btn_class'])
        # return ret and ret2 and ret3
        return ret

    # </editor-fold>

    # <editor-fold desc="Status页面相关">
    def enter_status_basic(self):
        aklog_info()
        self.menu_expand_and_click(self.ele_info['menu_status'])

    def restore_firmware_version(self, firmware_version):
        """
        有些机型OEM版本有定制model id，比如NAG，要将获取到的软件版本还原成升级包的版本号
        :return: firmware_version
        """
        model_id = self.device_config.get_model_id_NORMAL()
        version = firmware_version.split('.')
        if model_id != '0' and model_id != version[0]:
            new_firmware_version = '%s.%s.%s.%s' % (model_id, version[1], version[2], version[3])
            return new_firmware_version
        else:
            return firmware_version

    def get_status_product_info(self):
        """获取产品型号等信息"""
        self.enter_status_basic()
        model = self.browser.get_value_by_xpath(self.ele_info['status_model'])
        mac_address = self.browser.get_value_by_xpath(self.ele_info['status_mac_address'])
        firmware_version = self.browser.get_value_by_xpath(self.ele_info['status_firmware_version'])
        hardware_version = self.browser.get_value_by_xpath(self.ele_info['status_hardware_version'])
        device_name = self.browser.get_value_by_xpath(self.ele_info['status_device_name'])

        product_info = {'model': model,
                        'mac_address': mac_address,
                        'firmware_version': firmware_version,
                        'hardware_version': hardware_version,
                        'device_name': device_name}
        return product_info

    # </editor-fold>

    # <editor-fold desc="Network Basic页面">
    def enter_network_basic(self):
        aklog_info()
        self.menu_expand_and_click(self.ele_info['menu_network'])

    def set_network_to_dhcp(self):
        aklog_info(self.device_name_log + 'set_network_to_dhcp')
        self.enter_network_basic()
        self.browser.check_box_by_xpath(self.ele_info['network_basic_dhcp_xpath'])
        self.click_submit()
        self.click_alert_ok()

    def set_network_to_static(self, ip_address, subnet_mask, gateway, dns1, dns2):
        aklog_info('set_network_to_static')
        self.enter_network_basic()
        self.browser.check_box_by_xpath(self.ele_info['network_basic_staticip_xpath'])
        self.write_config(self.ele_info['network_basic_ip_addr_xpath'], ip_address)
        self.write_config(self.ele_info['network_basic_subnet_mask_xpath'], subnet_mask)
        self.write_config(self.ele_info['network_basic_gateway_xpath'], gateway)
        self.write_config(self.ele_info['network_basic_dns1_xpath'], dns1)
        self.write_config(self.ele_info['network_basic_dns2_xpath'], dns2)
        self.click_submit()
        self.click_alert_ok()

    # </editor-fold>

    # <editor-fold desc="Account Basic页面">
    def enter_account_basic(self):
        aklog_info()
        self.menu_expand_and_click(self.ele_info['menu_account'])
        time.sleep(3)

    def get_sip_status(self):
        aklog_info()
        self.enter_account_basic()
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['account_sip_status_xpath']):
                for j in range(0, 60):
                    account_register_status = self.browser.get_value_by_xpath(
                        self.ele_info['account_sip_status_xpath'])
                    if account_register_status:
                        aklog_info(self.device_name_log + 'account_register_status: %s' % account_register_status)
                        return account_register_status
                    else:
                        time.sleep(5)
                        self.browser.web_refresh()
            elif i == 0:
                aklog_error(self.device_name_log + '获取账号注册状态失败，可能是页面异常，重试...')
                self.browser.screen_shot()
                self.login()
                self.enter_account_basic()
                time.sleep(5)
        aklog_error(self.device_name_log + '获取账号注册状态失败')
        self.browser.screen_shot()
        return None

    def register_sip_by_web(self, sip, sip_password, server_ip, server_port='5060'):
        """网页账号注册"""
        aklog_info("register_sip, sip: %s, sip_password: %s, server_ip: %s, server_port: %s"
                   % (sip, sip_password, server_ip, server_port))
        self.enter_account_basic()
        self.check_sip_account()
        self.input_account_display_name(sip)
        self.input_account_register_name(sip)
        self.input_account_user_name(sip)
        self.input_account_password(sip_password)
        self.input_sip_server_address(server_ip)
        self.input_sip_server_port(server_port)
        self.click_submit()
        self.wait_for_account_to_register_successfully()

    def wait_for_account_to_register_successfully(self, failure_to_wait_time=15):
        """
        等待帐号注册, failure_to_wait_time为显示注册失败后再继续等待的时间
        """
        aklog_info(self.device_name_log + 'wait_for_account_to_register_successfully')
        self.enter_account_basic()
        i = 0
        while i < 30 + int(failure_to_wait_time / 5):
            self.browser.web_refresh()
            account_status = self.get_sip_status()
            if account_status == 'Registered':
                aklog_info(self.device_name_log + 'sip account register success')
                return True
            elif account_status == 'Disabled':
                aklog_info(self.device_name_log + 'sip account status: %s' % account_status)
                return False
            elif account_status == 'Registration Failed' and i < 30:
                # 有些情况会先显示注册失败，然后再等一段时间后再注册成功
                i = 30
                continue
            else:
                time.sleep(4)
                i += 1
                continue
        aklog_info(self.device_name_log + 'sip account register failed')
        return False

    def clear_web_sip(self):
        """网页清除账号配置为默认配置"""
        self.enter_account_basic()
        self.uncheck_sip_account()
        self.input_account_display_name('')
        self.input_account_register_name('')
        self.input_account_user_name('')
        self.input_account_password('')
        self.input_sip_server_address('')
        self.input_sip_server_port('5060')
        self.click_submit()

    def check_sip_account(self):
        aklog_info()
        self.write_config(self.ele_info['account_enabled_xpath'], 1)

    def uncheck_sip_account(self):
        aklog_info()
        self.write_config(self.ele_info['account_enabled_xpath'], 0)

    def input_account_display_name(self, content):
        aklog_info()
        self.write_config(self.ele_info['account_display_name_xpath'], content)

    def input_account_register_name(self, content):
        aklog_info()
        self.write_config(self.ele_info['account_register_name_xpath'], content)

    def input_account_user_name(self, content):
        aklog_info()
        self.write_config(self.ele_info['account_user_name_xpath'], content)

    def input_account_password(self, content):
        aklog_info()
        self.write_config(self.ele_info['account_password_xpath'], content)

    def input_sip_server_address(self, content):
        aklog_info()
        self.write_config(self.ele_info['sip_server_address_xpath'], content)

    def input_sip_server_port(self, content):
        aklog_info()
        self.write_config(self.ele_info['sip_server_port_xpath'], content)

    def input_registration_period(self, content):
        aklog_info()
        self.write_config(self.ele_info['registration_period_xpath'], content)

    @staticmethod
    def get_random_registration_period():
        # 生产一个随机注册周期的数
        aklog_info()
        random_number = random.randint(30, 65535)
        return random_number

    def check_outbound_enabled(self):
        aklog_info()
        self.write_config(self.ele_info['outbound_enabled_xpath'], 1)

    def uncheck_outbound_enabled(self):
        aklog_info()
        self.write_config(self.ele_info['outbound_enabled_xpath'], 0)

    def input_preferred_outbound_server(self, content):
        aklog_info()
        self.write_config(self.ele_info['preferred_outbound_server_xpath'], content)

    def input_preferred_outbound_server_port(self, content):
        aklog_info()
        self.write_config(self.ele_info['preferred_outbound_server_port_xpath'], content)

    def input_alternate_outbound_server(self, content):
        aklog_info()
        self.write_config(self.ele_info['alternate_outbound_server_xpath'], content)

    def input_alternate_outbound_server_port(self, content):
        aklog_info()
        self.write_config(self.ele_info['alternate_outbound_server_port_xpath'], content)

    def enable_outbound_sever(self, outbound_server, server_port):
        aklog_info("outbound_server: %s, server_port: %s" % (outbound_server, server_port))
        self.enter_account_basic()
        self.check_outbound_enabled()
        self.input_preferred_outbound_server(outbound_server)
        self.input_preferred_outbound_server_port(server_port)
        self.click_submit()

    def disable_outbound_sever(self):
        self.enter_account_basic()
        self.check_outbound_enabled()
        self.input_alternate_outbound_server('')
        self.input_preferred_outbound_server('')
        # self.input_alternate_outbound_server_port('5060')
        self.click_submit()

    # </editor-fold>

    # <editor-fold desc="升级基础页面相关">
    def enter_settings_basic(self):
        aklog_info()
        self.menu_expand_and_click(self.ele_info['menu_settings'])

    def get_version(self):
        """获取当前版本号"""
        aklog_info(self.device_name_log + '获取版本号')
        self.enter_settings_basic()
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_firmware_version_xpath']):
                for j in range(0, 60):
                    firmware_version = self.browser.get_value_by_xpath(
                        self.ele_info['upgrade_basic_firmware_version_xpath'])
                    if firmware_version:
                        firmware_version = self.restore_firmware_version(firmware_version)  # 有些机型OEM版本有定制model id
                        aklog_info(self.device_name_log + 'firmware_version: %s' % firmware_version)
                        return firmware_version
                    else:
                        time.sleep(5)
                        self.browser.web_refresh()
            elif i == 0:
                aklog_error(self.device_name_log + '获取版本号失败，可能是页面异常，重试...')
                self.browser.screen_shot()
                self.login()
                self.enter_settings_basic()
                time.sleep(5)
        aklog_error(self.device_name_log + '获取版本号失败')
        self.browser.screen_shot()
        self.reboot_by_tln_or_ssh()
        return None

    def web_basic_upgrade(self, firmware_path, accept=True, reset=False):
        """网页基础升级，建议使用下面web_basic_upgrade_to_version这个方法"""
        aklog_info(self.device_name_log + 'web_basic_upgrade, firmware_path: %s' % firmware_path)
        version_before_upgrade = self.get_version()
        if not version_before_upgrade:
            aklog_error('获取版本号失败')
            return False
        # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
        cmd_waiting_for_network_rate_to_drop()
        self.enter_settings_basic()
        time.sleep(1)
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_import_xpath'], 2)
        if not self.browser.upload_file_by_xpath(self.ele_info['upgrade_basic_select_file_input_xpath'],
                                                 firmware_path, 1):
            aklog_error('可能是升级包不存在，请检查')
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_select_cancel_xpath'])
            return False
        if reset:
            self.write_config(self.ele_info['upgrade_basic_select_reset_to_factory_xpath'], 1)
        if accept:
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_select_submit_xpath'])
        else:
            # 点击取消
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_select_cancel_xpath'])
            # self.enter_settings_basic()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_firmware_version_xpath']):
                aklog_info(self.device_name_log + '返回升级基础页面成功')
                return 1
            else:
                aklog_error(self.device_name_log + '返回升级基础页面失败')
                return 0
        time.sleep(30)
        # 判断是否处于升级状态
        begin_time = time.time()
        web_basic_upgrade_default_time = self.device_config.get_web_basic_upgrade_default_time()
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()  # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        reboot_ret = cmd_waiting_for_device_reboot(self.device_ip, sec=boot_time_after_get_ip)  # 等待设备升级完成后重启
        if reboot_ret:
            for i in range(2):
                if not reset and self.login(raise_enable=False):
                    break

                if i == 0:
                    # 小概率出现网页显示异常导致升级等待时间不够，则增加每个机型默认等待时间，如果小于默认时间则需要等待足够时间
                    wait_time = round(time.time() - begin_time)
                    if wait_time < web_basic_upgrade_default_time:
                        continue_wait_time = web_basic_upgrade_default_time - wait_time
                        aklog_error('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                        time.sleep(continue_wait_time)
                    continue
                else:
                    # 有些OEM定制会在升级后恢复出厂，或者勾选了reset
                    if reset or self.device_config.get_reset_after_upgrade_enable():
                        # 恢复出厂后，如果当前版本有定制web账户密码，则使用定制账户密码登录，否则使用admin账号登录
                        if self.web_admin_username == 'admin':
                            self.web_admin_pwd = self.device_config.get_web_admin_passwd()
                        else:
                            self.web_admin_username = self.device_config.get_web_custom_username()
                            self.web_admin_pwd = self.device_config.get_web_custom_passwd()
                        self.set_network_to_dhcp_after_reset()
                        self.login()
                        self.enter_settings_basic()
                    break
        else:
            self.login(raise_enable=False)

        version_after_upgrade = self.get_version()
        if version_after_upgrade != version_before_upgrade:
            aklog_info('已升级到 %s 版本' % version_after_upgrade)
            self.get_device_config_by_version(version_after_upgrade)
            return True
        else:
            aklog_error(self.device_name_log + '网页升级失败，请检查原因')
            self.browser.screen_shot()
            self.get_device_config_by_version(version_before_upgrade)
            return False

    def web_basic_upgrade_to_version(self, dst_version, firmware_path, accept=True, reset=False):
        """网页基础升级"""
        aklog_info(self.device_name_log + 'web_basic_upgrade_to_version, dst_version: %s, firmware_path: %s'
                   % (dst_version, firmware_path))
        current_version = self.get_version()
        if current_version:
            if current_version == dst_version:
                aklog_info(self.device_name_log + '当前版本已是: %s, 无需升级' % dst_version)
                return True
        else:
            aklog_error(self.device_name_log + '获取版本号失败')
            return False
        self.get_device_config_by_version(current_version)

        # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
        cmd_waiting_for_network_rate_to_drop()

        self.enter_settings_basic()
        time.sleep(1)
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_import_xpath'], 2)
        if not self.browser.upload_file_by_xpath(self.ele_info['upgrade_basic_select_file_input_xpath'],
                                                 firmware_path, 1):
            aklog_error('可能是升级包不存在，请检查')
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_select_cancel_xpath'])
            return False
        if reset:
            self.write_config(self.ele_info['upgrade_basic_select_reset_to_factory_xpath'], 1)
        if accept:
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_select_submit_xpath'])
        else:
            # 点击取消
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_select_cancel_xpath'])
            # self.enter_settings_basic()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_firmware_version_xpath']):
                aklog_info(self.device_name_log + '返回升级基础页面成功')
                return 1
            else:
                aklog_error(self.device_name_log + '返回升级基础页面失败')
                return 0
        # self.browser.alert_confirm_accept()
        time.sleep(30)

        # 判断是否处于升级状态
        begin_time = time.time()
        web_basic_upgrade_default_time = self.device_config.get_web_basic_upgrade_default_time()
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()  # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        reboot_ret = cmd_waiting_for_device_reboot(self.device_ip, sec=boot_time_after_get_ip)  # 等待设备升级完成后重启
        if reboot_ret:
            for i in range(2):
                if not reset and self.login(raise_enable=False):
                    break

                if i == 0:
                    # 小概率出现网页显示异常导致升级等待时间不够，则增加每个机型默认等待时间，如果小于默认时间则需要等待足够时间
                    wait_time = round(time.time() - begin_time)
                    if wait_time < web_basic_upgrade_default_time:
                        continue_wait_time = web_basic_upgrade_default_time - wait_time
                        aklog_error('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                        time.sleep(continue_wait_time)
                    continue
                else:
                    self.get_device_config_by_version(dst_version)
                    # 有些OEM定制会在升级后恢复出厂，或者勾选了reset
                    if reset or self.device_config.get_reset_after_upgrade_enable():
                        # 恢复出厂后，如果当前版本有定制web账户密码，则使用定制账户密码登录，否则使用admin账号登录
                        if self.web_admin_username == 'admin':
                            self.web_admin_pwd = self.device_config.get_web_admin_passwd()
                        else:
                            self.web_admin_username = self.device_config.get_web_custom_username()
                            self.web_admin_pwd = self.device_config.get_web_custom_passwd()
                        self.set_network_to_dhcp_after_reset()
                        self.login()
                        self.enter_settings_basic()
                    break
        else:
            self.login(raise_enable=False)

        firmware_version = self.get_version()
        if firmware_version == dst_version:
            aklog_info(self.device_name_log + '已升级到 %s 版本' % dst_version)
            self.get_device_config_by_version(dst_version)
            return True
        else:
            aklog_error(self.device_name_log + '网页升级失败，请检查原因')
            self.browser.screen_shot()
            self.get_device_config_by_version(current_version)
            return False

    def upgrade_failed_reboot(self):
        aklog_error(self.device_name_log + '提示升级失败，重启')
        self.browser.click_btn_by_id('failedReboot')
        for i in range(0, 100):
            if self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
                aklog_info(self.device_name_log + 'reboot processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break
        # 判断是否返回升级基础页面
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('tUpgrade'):
                aklog_info(self.device_name_log + '重启完成')
                return True
            elif i == 0:
                aklog_info(self.device_name_log + '重启后没有正常刷新到基础升级页面，需要重新加载')
                self.browser.screen_shot()
                self.login()
                self.enter_settings_basic()
        aklog_error(self.device_name_log + '重启失败，请检查原因')
        self.browser.screen_shot()
        return False

    def upgrade_new_version(self, accept=True, reset=False):
        aklog_info(self.device_name_log + '网页升级新版本')
        # 如果辅助设备要调用该方法，可以使用put_test_rom_version()将升级版本传入替换
        upgrade_result = self.web_basic_upgrade_to_version(
            self.rom_version,
            self.device_config.get_local_firmware_path(self.rom_version),
            accept,
            reset)
        self.restore_device_config()
        return upgrade_result

    def upgrade_old_version(self, accept=True, reset=False):
        aklog_info(self.device_name_log + '网页升级旧版本')
        self.device_config.get_old_firmware(force_replace=self.force_replace_old_version)  # 强制替换旧版本升级包
        old_firmware_version = self.device_config.get_old_firmware_version()
        if old_firmware_version:
            old_firmware_path = self.device_config.get_upgrade_firmware_dir(True) \
                                + old_firmware_version + self.device_config.get_firmware_ext()
            File_process.copy_file(self.device_config.get_old_firmware_path(), old_firmware_path)
            upgrade_result = self.web_basic_upgrade_to_version(old_firmware_version,
                                                               old_firmware_path,
                                                               accept,
                                                               reset)
            File_process.remove_file(old_firmware_path)
        else:
            old_firmware_path = self.device_config.get_old_firmware_path()
            upgrade_result = self.web_basic_upgrade(old_firmware_path, accept, reset)
            if upgrade_result:
                # 如果旧版本升级包文件名格式不正确，在升级旧版本成功后，重命名旧版本升级包
                old_firmware_version = self.get_version()
                model_name = self.device_config.get_model_name()
                old_firmware_dir = os.path.split(old_firmware_path)[0]
                old_firmware_file = '%s_NORMAL__%s%s' % (model_name, old_firmware_version,
                                                         self.device_config.get_firmware_ext())
                old_firmware_path2 = os.path.join(old_firmware_dir, old_firmware_file)
                File_process.rename_file(old_firmware_path, old_firmware_path2)

        self.restore_device_config()
        return upgrade_result

    def upgrade_cover_old_version(self, firmware_version, firmware_path):
        """升级覆盖测试，检查从旧版本升级到新版本是否成功"""
        local_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(),
                                          firmware_version, self.device_config.get_firmware_ext())
        self.download_firmware_to_upgrade_dir(firmware_version, firmware_path)

        ret1 = self.web_basic_upgrade_to_version(firmware_version, local_firmware_path)
        File_process.remove_file(local_firmware_path)
        if not ret1:
            aklog_error('升级到旧版本 %s 失败' % firmware_version)
            return False

        ret2 = self.upgrade_new_version()
        return ret2

    def download_firmware_to_upgrade_dir(self, firmware_version, firmware_path):
        """将指定的升级包下载到本地Upgrade目录下"""
        local_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(),
                                          firmware_version, self.device_config.get_firmware_ext())
        download_result = False

        # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
        cmd_waiting_for_network_rate_to_drop()

        if 'ftp://' in firmware_path:
            aklog_info("将升级包从FTP服务器下载到本地目录")
            ftp_info = get_ftp_info_from_url(firmware_path)
            ftp_connect_mode = True  # False为PORT模式
            for k in range(2):
                ftp_client = FtpClient(ftp_info['host'], ftp_info['port'], ftp_info['user_name'], ftp_info['password'])
                ftp_client.login(ftp_connect_mode)
                download_result = ftp_client.download_file(local_firmware_path, ftp_info['remote_file'])
                ftp_client.close()
                if download_result:
                    break
                else:
                    ftp_connect_mode = False
                    continue
        else:
            aklog_info("将升级包拷贝到本地目录")
            for x in range(2):
                download_result = File_process.copy_file(firmware_path, local_firmware_path)
                if download_result:
                    break

        if download_result:
            return File_process.chmod_file_off_only_read(local_firmware_path)
        else:
            return False

    def copy_old_firmware_to_download_dir(self):
        """将机型对应OEM的旧版本复制到autop下载目录"""
        aklog_info(self.device_name_log + 'copy_old_firmware_to_download_dir')
        self.device_config.get_old_firmware(force_replace=self.force_replace_old_version)  # 强制替换旧版本升级包
        File_process.copy_file(self.device_config.get_old_firmware_path(),
                               self.device_config.get_http_dir() + self.device_config.get_old_firmware_file())
        File_process.copy_file(self.device_config.get_old_firmware_path(),
                               self.device_config.get_https_dir() + self.device_config.get_old_firmware_file())
        File_process.copy_file(self.device_config.get_old_firmware_path(),
                               self.device_config.get_tftp_dir() + self.device_config.get_old_firmware_file())
        File_process.copy_file(self.device_config.get_old_firmware_path(),
                               self.device_config.get_ftp_dir() + self.device_config.get_old_firmware_file())

    def set_network_to_dhcp_after_reset(self):
        aklog_info(self.device_name_log + 'set_network_to_dhcp_after_reset')
        if self.device_config.get_lan_port_type() == 'static':
            self.device_ip = self.device_config.get_lan_port_ip_address()
            ip_list = self.device_ip.split('.')
            if 1 <= int(ip_list[3]) < 254:
                pc_ip_address_4 = str(int(ip_list[3]) + 1)
            else:
                pc_ip_address_4 = str(int(ip_list[3]) - 1)
            pc_ip_address = '%s.%s.%s.%s' % (ip_list[0], ip_list[1], ip_list[2], pc_ip_address_4)
            cmd_add_ip_address(pc_ip_address)
            self.login()
            self.device_ip = self.device_info['ip']
            self.set_network_to_dhcp()  # 网页基础页面设置为DHCP模式
            cmd_delete_ip_address(pc_ip_address)
        else:
            aklog_info(self.device_name_log + 'network type is already dhcp')

    def web_reset_to_factory_setting(self, accept=True, boot_time_after_get_ip=None):
        """网页恢复出厂设置"""
        aklog_info(self.device_name_log + '网页恢复出厂设置')
        self.enter_settings_basic()
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_factory_default_xpath'])
        if accept:
            self.browser.alert_confirm_accept()
        else:
            self.browser.alert_confirm_cancel()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reset_to_installer_xpath']):
                aklog_info(self.device_name_log + '返回基础升级页面完成')
                return 1
            else:
                aklog_error(self.device_name_log + '返回基础升级页面失败')
                return 0
        time.sleep(3)
        # 判断是否处于恢复出厂等待
        begin_time = time.time()
        reset_default_time = self.device_config.get_reset_default_time()
        if not boot_time_after_get_ip:
            boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()
            # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        ret = cmd_waiting_for_device_reboot(self.device_ip, wait_time1=180, sec=boot_time_after_get_ip)
        if not ret:
            aklog_error(self.device_name_log + '恢复出厂，设备未重启或重启失败，请检查')
            self.browser.screen_shot()
            return False

        # 恢复出厂后，如果当前版本有定制web账户密码，则使用定制账户密码登录，否则使用admin账号登录
        if self.web_admin_username == 'admin':
            self.web_admin_pwd = self.device_config.get_web_admin_passwd()
        else:
            self.web_admin_username = self.device_config.get_web_custom_username()
            self.web_admin_pwd = self.device_config.get_web_custom_passwd()

        # 判断是否返回基础升级页面
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_factory_default_xpath']) \
                or self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath']):
            aklog_info(self.device_name_log + '恢复出厂设置完成')
        else:
            aklog_info(self.device_name_log + '恢复出厂设置后没有正常刷新到基础升级页面，需要重新加载')
            self.browser.screen_shot()
            wait_time = round(time.time() - begin_time)
            if wait_time < reset_default_time:
                continue_wait_time = reset_default_time - wait_time
                aklog_error('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                time.sleep(continue_wait_time)

        # 如果默认为静态ip，则恢复出厂配置后要用默认静态ip登录并修改为dhcp模式
        self.set_network_to_dhcp_after_reset()
        self.login()
        self.enter_settings_basic()

        # 判断是否返回基础升级页面
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_factory_default_xpath']):
            aklog_info(self.device_name_log + '恢复出厂设置成功')
            return True
        else:
            aklog_error(self.device_name_log + '恢复出厂设置失败，请检查原因')
            self.browser.screen_shot()
            return False

    def web_reset_to_installer_setting(self, accept=True, retry_login=True):
        """网页恢复到installer设置"""
        aklog_info()
        self.enter_settings_basic()
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_reset_to_installer_xpath'])
        if accept:
            self.browser.alert_confirm_accept()
        else:
            self.browser.alert_confirm_cancel()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reset_to_installer_xpath']):
                aklog_info(self.device_name_log + '返回基础升级页面完成')
                return 1
            else:
                aklog_error(self.device_name_log + '返回基础升级页面失败')
                return 0
        time.sleep(3)
        # 判断是否处于恢复出厂等待
        begin_time = time.time()
        reset_default_time = self.device_config.get_reset_config_default_time()
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()  # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        ret = cmd_waiting_for_device_reboot(self.device_ip, wait_time1=180, sec=boot_time_after_get_ip)  # 等待设备恢复出厂完成后重启
        if not ret:
            aklog_error(self.device_name_log + '恢复到installer，设备未重启或重启失败，请检查')
            self.browser.screen_shot()
            return False

        # 恢复出厂后，如果当前版本有定制web账户密码，则使用定制账户密码登录，否则使用admin账号登录
        if self.web_admin_username == 'admin':
            self.web_admin_pwd = self.device_config.get_web_admin_passwd()
        else:
            self.web_admin_username = self.device_config.get_web_custom_username()
            self.web_admin_pwd = self.device_config.get_web_custom_passwd()

        if not retry_login:
            aklog_info(self.device_name_log + '不重新登录')
            self.browser_close_and_reopen()
            return

        # 判断是否返回基础升级页面
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reset_to_installer_xpath']) \
                or self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath']):
            aklog_info(self.device_name_log + '恢复到installer设置完成')
        else:
            aklog_info(self.device_name_log + '恢复到installer设置后没有正常刷新到基础升级页面，需要重新加载')
            self.browser.screen_shot()
            wait_time = round(time.time() - begin_time)
            if wait_time < reset_default_time:
                continue_wait_time = reset_default_time - wait_time
                aklog_error('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                time.sleep(continue_wait_time)

        # 如果默认为静态ip，则恢复出厂配置后要用默认静态ip登录并修改为dhcp模式
        self.set_network_to_dhcp_after_reset()
        self.login()
        self.enter_settings_basic()

        # 判断是否返回基础升级页面
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reset_to_installer_xpath']):
            aklog_info(self.device_name_log + '恢复到installer设置成功')
            return True
        else:
            aklog_error(self.device_name_log + '恢复到installer设置失败，请检查原因')
            self.browser.screen_shot()
            return False

    def web_reboot(self, accept=True):
        """网页进行重启"""
        aklog_info(self.device_name_log + '网页进行重启')
        self.enter_settings_basic()
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_reboot_xpath'])
        if accept:
            self.browser.alert_confirm_accept()
        else:
            self.browser.alert_confirm_cancel()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reboot_xpath']):
                aklog_info(self.device_name_log + '返回基础升级页面完成')
                return 1
            else:
                aklog_error(self.device_name_log + '返回基础升级页面失败')
                return 0
        begin_time = time.time()
        reboot_default_time = self.device_config.get_reboot_default_time()
        cmd_waiting_for_device_reboot(self.device_ip, sec=40)

        # 判断是否返回升级基础页面
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reboot_xpath']):
                aklog_info(self.device_name_log + '重启完成')
                return True
            elif i == 0:
                aklog_info(self.device_name_log + '重启后没有正常刷新到基础升级页面，需要重新加载')
                wait_time = round(time.time() - begin_time)
                if wait_time < reboot_default_time:
                    continue_wait_time = reboot_default_time - wait_time
                    aklog_error('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                    time.sleep(continue_wait_time)
                self.browser.screen_shot()
                self.login()
                self.enter_settings_basic()
        aklog_error(self.device_name_log + '重启失败，请检查原因')
        self.browser.screen_shot()
        return False

    def rename_all_cfg_file(self):
        aklog_info(self.device_name_log + 'rename_all_cfg_file')
        File_process.rename_file(self.device_cfg_66, self.device_config.get_renamecfg_66())
        File_process.rename_file(self.device_cfg_43, self.device_config.get_renamecfg_43())
        File_process.rename_file(self.device_cfg_URL, self.device_config.get_renamecfg_URL())
        File_process.rename_file(self.device_cfg_custom, self.device_config.get_renamecfg_custom())
        File_process.rename_file(self.device_cfg_pnp, self.device_config.get_renamecfg_pnp())

    # </editor-fold>

    # <editor-fold desc="8848隐藏页面相关">
    def enter_hide_page_8848(self):
        """进入隐藏页面"""
        url = '%s/#/8848' % self.login_url
        aklog_info(self.device_name_log + '打开页面: %s' % url)
        self.browser.visit_url(url)
        if self.browser.get_value_by_xpath(self.ele_info['hidden_page_title_xpath']) != 'Hidden page':
            self.login()
            self.browser.visit_url(url)
        return True

    def set_ssh_or_tln(self, option_value):
        """option_value 取值0和1"""
        aklog_info(self.device_name_log + 'set_ssh_or_tln %s' % option_value)
        if str(option_value) == '1':
            option = 'Enabled'
        else:
            option = 'Disabled'
        self.write_config(self.ele_info['hidden_page_telnet_xpath'], option)
        self.click_submit()
        if self.get_submit_result() is not True:
            return False
        self.browser.web_refresh()
        tln_or_ssh_status = self.read_config(self.ele_info['hidden_page_telnet_xpath'])
        return tln_or_ssh_status == option

    def get_ssh_status(self):
        return self.read_config(self.ele_info['hidden_page_telnet_xpath'])

    def web_open_ssh(self, disable_first=False):
        """设备网页打开的ssh操作"""
        aklog_info()
        self.enter_hide_page_8848()
        if disable_first and self.get_ssh_status() == 'Enabled':
            self.set_ssh_or_tln('0')
            time.sleep(2)
        result = self.set_ssh_or_tln('1')
        time.sleep(10)
        return result

    def set_debug_setting_ip(self, ip_addr):
        self.enter_hide_page_8848()
        self.write_config('//*[@id="ipaddr"]/input', ip_addr)
        self.click_submit()

    def set_cloud_configuration(self, server):
        self.enter_hide_page_8848()
        self.write_config("//div[@title='custom']", server)
        self.click_submit()

    # </editor-fold>

    # <editor-fold desc="8850隐藏页面相关">

    def enter_hide_page_8850(self):
        """进入隐藏页面"""
        url = '%s/#/8850' % self.login_url
        aklog_info(self.device_name_log + '进入页面: %s' % url)
        for i in range(2):
            self.browser.visit_url(url)
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['diagnosis_syslog_level']):
                aklog_info('进入8850隐藏页面成功')
                return True
            else:
                self.login()
                continue
        aklog_error('进入8850隐藏页面失败')
        return False

    def set_syslog_level(self, level):
        self.enter_hide_page_8850()
        self.write_config(self.ele_info['diagnosis_syslog_level'], str(level))
        time.sleep(1)
        self.click_submit()

    def set_syslog_level_7(self):
        self.set_syslog_level(7)

    def export_system_log(self):
        """导出system log文件"""
        aklog_info(self.device_name_log + '导出system log文件')
        export_system_log_file = self.device_config.get_chrome_download_dir() + self.device_config.get_log_file_name()
        File_process.remove_file(export_system_log_file)  # 先删除下载目录下的PhoneLog.tgz文件
        self.enter_hide_page_8850()
        self.browser.click_btn_by_xpath(self.ele_info['diagnosis_syslog_export_btn'])
        time.sleep(5)
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not os.path.exists(export_system_log_file):
                aklog_info(self.device_name_log + 'system log文件导出中...')
                time.sleep(3)
            else:
                aklog_info(self.device_name_log + 'system log文件导出成功')
                time.sleep(3)
                return True
        aklog_error(self.device_name_log + 'system log文件导出导出失败')
        self.browser.screen_shot()
        return False

    def export_syslog_to_results_dir(self, case_name):
        """网页导出syslog并保存到Results目录下"""
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file = '{}\\PhoneLog--{}--{}--{}.tgz'.format(log_dir, case_name, self.device_name, log_time)
        File_process.create_dir(log_dir)
        export_system_log_file = self.device_config.get_chrome_download_dir() + self.device_config.get_log_file_name()
        self.export_system_log()
        File_process.copy_file(export_system_log_file, log_file)  # 将log文件保存到Results目录下

    def start_pcap(self, specify_port=''):
        """开始网页抓包start_pcap"""
        aklog_info(self.device_name_log + '开始网页抓包start_pcap')
        self.enter_hide_page_8850()
        if specify_port is not None:
            cur_port = self.browser.get_attribute_value_by_xpath(self.ele_info['diagnosis_pcap_port'])
            if cur_port != str(specify_port):
                self.write_config(self.ele_info['diagnosis_pcap_port'], str(specify_port))
                self.click_submit()
                time.sleep(1)
        self.browser.click_btn_by_xpath(self.ele_info['diagnosis_pcap_start_btn'])
        time.sleep(2)
        self.browser.alert_confirm_accept()

    def stop_pcap(self):
        """停止网页抓包stop_pcap"""
        aklog_info(self.device_name_log + '停止网页抓包stop_pcap')
        self.enter_hide_page_8850()
        # self.browser.alert_confirm_accept()
        self.browser.click_btn_by_xpath(self.ele_info['diagnosis_pcap_stop_btn'])
        time.sleep(2)
        self.browser.alert_confirm_accept()

    def export_pcap(self):
        """导出pcap文件"""
        aklog_info(self.device_name_log + '导出pcap文件')
        export_pcap = self.device_config.get_export_pcap_file()
        File_process.remove_file(export_pcap)  # 先删除下载目录下的PhoneLog.tgz文件
        self.enter_hide_page_8850()
        if not self.browser.get_ele_status_by_xpath(self.ele_info['diagnosis_pcap_export_btn']):
            self.browser.click_btn_by_xpath(self.ele_info['diagnosis_pcap_stop_btn'])
            self.browser.alert_confirm_accept()
            time.sleep(1)
        self.browser.click_btn_by_xpath(self.ele_info['diagnosis_pcap_export_btn'])
        time.sleep(10)
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not os.path.exists(export_pcap):
                aklog_info(self.device_name_log + 'pcap文件导出中...')
                time.sleep(3)
            else:
                aklog_info(self.device_name_log + '导出pcap文件成功')
                time.sleep(3)
                return True
        aklog_error(self.device_name_log + 'pcap文件导出导出失败')
        self.browser.screen_shot()
        return False

    def save_pcap_to_results_dir(self, case_name=None):
        """保存PCAP文件到Results目录下"""
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        if case_name is None:
            case_name = ''
        pcap_file = '{}\\PhonePcap--{}--{}--{}.pcap'.format(log_dir, case_name, self.device_name, log_time)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        export_pcap_file = self.device_config.get_chrome_download_dir() + 'phone.pcap'
        self.export_pcap()
        File_process.copy_file(export_pcap_file, pcap_file)

    # </editor-fold>

    # <editor-fold desc="Telnet/SSH命令通用操作">

    def telnet_login(self):
        for i in range(5):
            if self.tln.login_host():
                self.tln_ssh_port_list = self.tln.get_port_list()
                self.tln_ssh_pwd_list = self.tln.get_pwd_list()
                return True
            elif i == 0:
                self.web_open_ssh()
                continue
            elif i == 1:
                self.web_open_ssh(True)
            elif i < 4:
                time.sleep(5)
                continue
            else:
                aklog_error('Telnet连接登录失败')
                return False

    def telnet_logout(self):
        self.tln.command_stop()
        self.tln.logout_host()

    def ssh_login(self):
        for i in range(5):
            if self.ssh.connect():
                self.tln_ssh_port_list = self.ssh.get_port_list()
                self.tln_ssh_pwd_list = self.ssh.get_pwd_list()
                return True
            elif i == 0:
                self.web_open_ssh()
                continue
            elif i == 1:
                self.web_open_ssh(True)
            elif i < 4:
                time.sleep(5)
                continue
            else:
                aklog_error('SSH连接登录失败')
                return False

    def ssh_logout(self):
        self.ssh.interactive_stop_command()
        self.ssh.close()

    def tln_or_ssh_login(self):
        if self.device_config.get_remote_connect_type() == 'telnet':
            self.telnet_login()
        else:
            self.ssh_login()

    def tln_or_ssh_logout(self):
        if self.device_config.get_remote_connect_type() == 'telnet':
            self.telnet_logout()
        else:
            self.ssh_logout()

    def get_value_by_ssh(self, command, print_result=True):
        """后台执行命令获取对应配置的值"""
        aklog_info()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return None
        value = self.ssh.command_result(command)
        if value:
            value = value.encode('gbk', 'ignore').decode('gbk')
        if print_result:
            aklog_debug('value: %s' % value)
        return value

    def get_result_by_telnet_command(self, command, print_result=True):
        """后台执行命令获取对应配置的值"""
        aklog_info()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return None
        result = self.tln.command_result(command)
        if print_result:
            aklog_debug('result: %s' % result)
        return result

    def get_result_by_tln_or_ssh(self, command, print_result=True):
        """telnet或SSH执行命令并获取结果"""
        if self.device_config.get_remote_connect_type() == 'telnet':
            result = self.get_result_by_telnet_command(command, print_result)
        else:
            result = self.get_value_by_ssh(command, print_result)
        return result

    def exec_command_by_ssh(self, *commands, timeout=60):
        aklog_info()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return False
        for command in commands:
            self.ssh.exec_command_no_back(command, timeout)
            time.sleep(0.5)
        return True

    def exec_command_by_tln(self, *commands, timeout=60):
        aklog_info()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return False
        for command in commands:
            self.tln.exec_command(command, timeout)
            time.sleep(0.5)
        return True

    def command_by_tln_or_ssh(self, *commands, timeout=60):
        if self.device_config.get_remote_connect_type() == 'telnet':
            return self.exec_command_by_tln(*commands, timeout=timeout)
        else:
            return self.exec_command_by_ssh(*commands, timeout=timeout)

    def exec_command_by_interactive_ssh_thread(self, command):
        """ssh交互式子线程执行，需要与get_result_by_interactive_ssh_thread配合使用"""
        aklog_info(self.device_name_log + 'exec_command_by_interactive_ssh_thread, command: %s' % command)
        for i in range(2):
            if self.ssh.is_connected() and self.ssh.start_chan():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return False
        time.sleep(0.5)
        self.ssh.thread_interactive_exec_command(command)
        return self.ssh

    def stop_interactive_ssh_command(self):
        self.ssh.interactive_stop_command()

    def get_result_by_interactive_ssh_thread(self, timeout=60):
        """获取SSH交互式子线程执行结果，需要与exec_command_by_interactive_ssh_thread配合使用"""
        return self.ssh.interactive_return_log(timeout=timeout)

    def ignore_previous_logs_by_interactive_ssh_thread(self, wait_time=3):
        """先获取一次结果，然后再次获取结果时就不会包含之前的结果，这样就不需要logcat -c清空掉之前的log了
        需要与exec_command_by_interactive_ssh_thread配合使用（该方法有点问题，先不要使用）"""
        result1 = self.ssh.interactive_return_log(wait_time)
        # result2 = self.interactive_tln_or_ssh.interactive_return_log(1)
        # result = result1 + result2
        return result1

    def exec_command_by_interactive_telnet_thread(self, command):
        """Telnet交互式子线程执行，需要与get_result_by_interactive_telnet_thread配合使用"""
        aklog_info(self.device_name_log + 'exec_command_by_interactive_telnet_thread, command: %s' % command)
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return False
        time.sleep(1)
        self.tln.thread_exec_command(command)
        return self.tln

    def get_result_by_interactive_telnet_thread(self, timeout=60):
        """获取Telnet交互式子线程执行结果，需要与exec_command_by_interactive_telnet_thread配合使用"""
        return self.tln.thread_stop_exec_output_result(timeout=timeout)

    # </editor-fold>

    # <editor-fold desc="Telnet/SSH命令">

    def reboot_by_tln_or_ssh(self, wait_time_after_reboot=10):
        aklog_info()
        self.command_by_tln_or_ssh('reboot')
        return cmd_waiting_for_device_reboot(self.device_ip, wait_time1=30, wait_time2=300, sec=wait_time_after_reboot)

    def get_uptime_by_tln_or_ssh(self):
        """获取开机时间"""
        aklog_info()
        uptime = self.get_result_by_tln_or_ssh(
            'uptime | cut -d "p" -f 2 | cut -b "1-15"|sed "s/\\([^0-9][^0-9]*\\)//g"')
        aklog_info(self.device_name_log + 'uptime: %s min' % uptime)
        return uptime

    def get_door_setting_config_by_tln_or_ssh(self, section, key):
        """获取/config/Door/Setting.conf配置文件里面的配置项"""
        return self.get_result_by_tln_or_ssh(
            '/app/bin/inifile_wr r /config/Door/Setting.conf %s %s ""' % (section, key))

    def start_adb_server_by_ssh(self, device_id, retry_counts=5):
        if ':' not in device_id:
            aklog_info('USB方式连接，不需要启动adb server')
            return True
        adb_server_port = device_id.split(':')[1]
        command_start_adbd = 'setprop service.adb.tcp.port %s; stop adbd; start adbd' % adb_server_port
        command_write_misc_adb = 'mkdir /data/misc/adb;echo %s > /data/misc/adb/adb_keys' \
                                 % self.device_config.get_command_misc_adb_password()
        command_chown_adb = 'cd /data/misc/adb/; chown system:shell adb_keys'
        command_chmod_adb = 'chmod 640 /data/misc/adb/adb_keys'
        for i in range(0, retry_counts):
            try:
                ret = self.exec_command_by_ssh(command_start_adbd, command_write_misc_adb,
                                               command_chown_adb, command_chmod_adb)
                if ret:
                    time.sleep(3)
                    return True
                elif i < 2:
                    self.web_open_ssh()
                    continue
                else:
                    aklog_error('Start Adb Server 失败，重试...')
                    time.sleep(3)
                    continue
            except:
                aklog_error('遇到未知异常，等待重试...' + str(traceback.format_exc()))
                time.sleep(5)
                continue
        aklog_error('Start Adb Server 失败')
        return False

    def set_connect_akubela_test_url(self, test_url='https://my.uat.akubela.com'):
        """连接测试服务器，需要使用测试url"""
        self.command_by_tln_or_ssh('echo %s > /data/code/test_url' % test_url)

    def set_upgrade_idle_time(self, wait_time=30):
        """设置设备进入空闲状态的等待时间，准备升级"""
        self.command_by_tln_or_ssh('settings put system akuvox_upgrade_idle_time  %s' % (wait_time * 1000))

    # </editor-fold>

    # <editor-fold desc="telnet/SSH 进程相关">
    def top_get_memory_info(self):
        """获取内存使用情况"""
        aklog_info(self.device_name_log + 'top_get_memory_info')
        memory_info = self.get_result_by_tln_or_ssh('top -b -n 1 | grep Mem: | grep -v grep')
        if memory_info is None:
            return None
        infos = memory_info.split('Mem:')[-1].split(',')
        memory_info_dict = {}
        for info in infos:
            if 'used' in info:
                memory_info_dict['used'] = info.strip().split(' ')[0]
            if 'free' in info:
                memory_info_dict['free'] = info.strip().split(' ')[0]
            if 'shrd' in info:
                memory_info_dict['shrd'] = info.strip().split(' ')[0]
            if 'buff' in info:
                memory_info_dict['buff'] = info.strip().split(' ')[0]
            if 'cached' in info:
                memory_info_dict['cached'] = info.strip().split(' ')[0]
        aklog_info(self.device_name_log + 'memory_info: %r' % memory_info_dict)
        return memory_info_dict

    def top_get_cpu_info(self):
        """获取cpu使用情况"""
        aklog_info(self.device_name_log + 'top_get_cpu_info')
        cpu_info = self.get_result_by_tln_or_ssh('top -b -n 1 | grep CPU: | grep -v grep')
        if cpu_info is None:
            return None
        infos = cpu_info.split('CPU:')[-1].strip().split('  ')
        cpu_info_dict = {}
        for info in infos:
            if 'usr' in info:
                cpu_info_dict['usr'] = info.strip().split(' ')[0]
            if 'sys' in info:
                cpu_info_dict['sys'] = info.strip().split(' ')[0]
            if 'nic' in info:
                cpu_info_dict['nic'] = info.strip().split(' ')[0]
            if 'idle' in info:
                cpu_info_dict['idle'] = info.strip().split(' ')[0]
            if 'io' in info:
                cpu_info_dict['io'] = info.strip().split(' ')[0]
            if 'irq' in info:
                cpu_info_dict['irq'] = info.strip().split(' ')[0]
            if 'sirq' in info:
                cpu_info_dict['sirq'] = info.strip().split(' ')[0]
        aklog_info(self.device_name_log + 'cpu_info: %r' % cpu_info_dict)
        return cpu_info_dict

    def top_get_process_info(self, *process_flag):
        """获取phone进程信息，返回字典"""
        aklog_info(self.device_name_log + 'top_get_process_info')
        attribute = self.get_result_by_tln_or_ssh('top -b -n 1 | grep "PID" | grep -v grep')
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_info(self.device_name_log + 'attribute_list: %r' % attribute_list)
        grep_command = ''
        for i in process_flag:
            grep_command += '| grep "%s" ' % i
        info = self.get_result_by_tln_or_ssh('top -b -n 1 | grep -v grep %s' % grep_command)
        if info is None:
            return None
        info = info.replace('\n#', '').strip()
        info = re.sub(' +', ' ', info)
        infos = info.split(' ')
        aklog_info(self.device_name_log + 'process infos: %r' % infos)

        process_info = {}
        for attribute in attribute_list:
            index = attribute_list.index(attribute)
            if attribute == 'PID':
                process_info['pid'] = infos[index]
            elif attribute == 'PPID':
                process_info['ppid'] = infos[index]
            elif attribute == 'USER':
                process_info['user'] = infos[index]
            elif attribute == 'STAT':
                process_info['stat'] = infos[index]
            elif attribute == 'RSS':
                process_info['rss'] = infos[index]
            elif attribute == 'VSZ':
                process_info['vsz'] = infos[index]
            elif attribute == '%VSZ':
                process_info['vsz%'] = infos[index]
            elif attribute == '%CPU':
                process_info['cpu%'] = infos[index]
            elif 'COMMAND' in attribute:
                if len(infos) > len(attribute_list):
                    process_info['command'] = ' '.join(infos[index:])
                else:
                    process_info['command'] = infos[index]

        aklog_info(self.device_name_log + 'process_info: %r' % process_info)
        return process_info

    def ps_get_process_info(self, *process_flag):
        """获取phone进程信息，返回字典"""
        aklog_info()
        attribute = self.get_result_by_tln_or_ssh('%s | grep "PID" | grep -v grep' % self.device_config.get_ps_cmd())
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_info(self.device_name_log + 'attribute_list: %r' % attribute_list)
        grep_command = ''
        for i in process_flag:
            grep_command += '| grep "%s" ' % i
        info = self.get_result_by_tln_or_ssh('%s | grep -v grep %s' % (self.device_config.get_ps_cmd(), grep_command))
        if info is None:
            return None
        info = info.replace('\n#', '').strip()
        info = re.sub(' +', ' ', info)
        infos = info.split(' ')
        aklog_info(self.device_name_log + 'process infos: %r' % infos)

        process_info = {}
        for attribute in attribute_list:
            index = attribute_list.index(attribute)
            if attribute == 'PID':
                process_info['pid'] = infos[index]
            elif attribute == 'USER':
                process_info['user'] = infos[index]
            elif attribute == 'VSZ':
                process_info['vsz'] = infos[index]
            elif attribute == 'STAT':
                process_info['stat'] = infos[index]
            elif 'COMMAND' in attribute:
                if len(infos) > len(attribute_list):
                    process_info['command'] = ' '.join(infos[index:])
                else:
                    process_info['command'] = infos[index]

        aklog_info(self.device_name_log + 'process_info: %r' % process_info)
        return process_info

    def ps_get_all_info(self):
        info = self.get_result_by_tln_or_ssh(self.device_config.get_ps_cmd())
        return info

    def ps_judge_processes_is_running(self, *processes):
        """ps获取进程信息，判断多个进程是否都正在运行"""
        aklog_info()
        not_running_process_list = []
        for process in processes:
            ps_command = '%s | grep -v grep | grep "%s"' % (self.device_config.get_ps_cmd(), process)
            info = self.get_result_by_tln_or_ssh(ps_command)
            if info is None:
                return None
            info = info.replace('\n#', '').strip()
            if not info:
                not_running_process_list.append(process)

        if not not_running_process_list:
            aklog_info(self.device_name_log + '所有进程都正在运行')
            return True
        else:
            aklog_info(self.device_name_log + '有进程未运行: %r' % not_running_process_list)
            return False

    def check_device_process_status(self):
        """检查设备进程的状态，是否都在运行，由于各机型的进程信息可能不一致，可以重写该方法"""
        aklog_info(self.device_name_log + 'check_device_process_status')
        status = self.ps_judge_processes_is_running('com.akuvox.phone',
                                                    'com.akuvox.upgradeui',
                                                    'homeassistant/__main__.pyc',
                                                    'sip',
                                                    'autop',
                                                    'api.fcgi fcgi')
        return status

    def kill_process_by_ssh(self, *processes):
        """杀进程"""
        aklog_info()
        attribute = self.get_value_by_ssh('%s | grep "PID" | grep -v grep' % self.device_config.get_ps_cmd())
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_debug('attribute_list: %r' % attribute_list)
        pid_index = attribute_list.index('PID')
        for process in processes:
            ps_cmd = '%s | grep -v grep | grep "%s"' % (self.device_config.get_ps_cmd(), process)
            info = self.get_value_by_ssh(ps_cmd)
            if not info or process not in info:
                aklog_printf('%s 没有在运行' % process)
                continue

            lines = info.splitlines()
            for line in lines:
                if not line or process not in line:
                    continue
                line = line.replace('\n#', '').strip()
                line = re.sub(' +', ' ', line)
                info_list = line.split(' ')
                aklog_debug('process info: %r' % info_list)
                pid = info_list[pid_index]
                kill_cmd = 'kill -9 %s' % pid
                ret = self.exec_command_by_ssh(kill_cmd)
                if ret:
                    aklog_printf('杀进程 %s 完成' % process)
                else:
                    aklog_error('杀进程 %s 失败' % process)

    def kill_process_by_tln(self, *processes):
        """杀进程"""
        aklog_info()
        attribute = self.get_result_by_telnet_command(
            '%s | grep "PID" | grep -v grep' % self.device_config.get_ps_cmd())
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_debug('attribute_list: %r' % attribute_list)
        pid_index = attribute_list.index('PID')
        for process in processes:
            ps_cmd = '%s | grep -v grep | grep "%s"' % (self.device_config.get_ps_cmd(), process)
            info = self.get_result_by_telnet_command(ps_cmd)
            if not info or process not in info:
                aklog_printf('%s 没有在运行' % process)
                continue
            lines = info.splitlines()
            for line in lines:
                if not line or process not in line:
                    continue
                line = line.replace('\n#', '').strip()
                line = re.sub(' +', ' ', line)
                info_list = line.split(' ')
                aklog_debug('process info: %r' % info_list)
                pid = info_list[pid_index]
                kill_cmd = 'kill -9 %s' % pid
                ret = self.exec_command_by_tln(kill_cmd)
                if ret:
                    aklog_info('杀进程 %s 完成' % process)
                else:
                    aklog_error('杀进程 %s 失败' % process)

    def kill_process_by_tln_or_ssh(self, *processes):
        if self.device_config.get_remote_connect_type() == 'telnet':
            return self.kill_process_by_tln(*processes)
        else:
            return self.kill_process_by_ssh(*processes)

    def wait_process_start(self, *processes, timeout=600):
        """等待进程启动"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            process_ret = self.ps_judge_processes_is_running(*processes)
            if process_ret:
                return True
            time.sleep(5)
            continue
        aklog_warn(f'{processes} 进程未在运行')
        return False

    # </editor-fold>

    # <editor-fold desc="telnet/ssh log相关">
    def clear_logs_by_ssh(self):
        """清理log缓存"""
        aklog_info(self.device_name_log + 'clear_logs_by_ssh')
        self.exec_command_by_ssh('logcat -G 2M', 'logcat -c')

    def clear_logs_by_tln(self):
        """清理log缓存"""
        aklog_info(self.device_name_log + 'clear_logs_by_tln')
        self.command_by_tln_or_ssh('rm /tmp/Messages* -f', 'echo "" > /tmp/Messages')

    def clear_logs_by_tln_or_ssh(self):
        """清理log缓存"""
        if self.device_config.get_remote_connect_type() == 'ssh':
            self.clear_logs_by_ssh()
        else:
            self.clear_logs_by_tln()

    def set_logcat_buffer_size(self, size='2M'):
        """
        设置logcat缓冲区大小，避免因为缓冲区太小，短时间打印太多log导致logcat中断
        size: 2M
        """
        self.exec_command_by_ssh('logcat -G %s' % size)

    def get_dclient_msgs(self):
        """获取dclient的msg，将msg转换成字典"""
        aklog_info(self.device_name_log + 'get_dclient_msgs')
        command = 'logcat -d | grep "<" | cut -b 20- '
        dclient_msgs = []
        ssh_log = self.get_result_by_tln_or_ssh(command)
        ssh_log = ssh_log.replace('"', '##').replace('{', '**').replace('}', '**')
        # print(ssh_log)
        ssh_logs = ssh_log.split('</Msg>')
        # print(ssh_logs)
        for msg in ssh_logs:
            if not msg or not msg.strip():
                continue
            result_dict = parse_msg_to_dict(msg)
            dclient_msgs.append(result_dict)
        aklog_info(dclient_msgs)
        return dclient_msgs

    def get_dclient_msg_by_type(self, msg_type, dclient_msgs=None):
        if not dclient_msgs:
            dclient_msgs = self.get_dclient_msgs()
        for dc_msg in dclient_msgs:
            if not msg_type:
                return dc_msg
            elif msg_type == dc_msg['Msg'].get('Type'):
                return dc_msg
        return None

    def is_correct_print_log(self, flag):
        aklog_info(self.device_name_log + 'is_correct_print_log, flag: %s' % flag)
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d | grep -v grep | grep "%s"' % flag
        else:
            command = 'cat /tmp/Messages* | grep -v grep | grep "%s"' % flag
        ssh_log = self.get_result_by_tln_or_ssh(command)
        if ssh_log and flag in ssh_log:
            return True
        else:
            aklog_error(self.device_name_log + '%s 日志不存在' % flag)
            return False

    def is_correct_log_level(self, log_level):
        """判断log等级打印是否正确"""
        logs = self.get_system_log_by_tln_or_ssh()
        ret = False
        if int(log_level) in [0, 1, 2]:
            ret = ',l3:' not in logs
        elif int(log_level) in [3, 4, 5, 6]:
            ret = ',l3:' in logs and ',l7:' not in logs and ',l%d:' % (int(log_level) + 1) not in logs
        elif int(log_level) == 7:
            ret = ',l3:' in logs and ',l7:' in logs
        if not ret:
            aklog_info(logs)
        return ret

    def get_counts_with_log_flag(self, flag):
        """获取指定log出现多少次"""
        aklog_info(self.device_name_log + 'get_counts_with_log_flag, flag: %s' % flag)
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d | grep -v grep | grep "%s"' % flag
        else:
            command = 'cat /tmp/Messages* | grep -v grep | grep "%s"' % flag
        ssh_log = self.get_result_by_tln_or_ssh(command)
        if ssh_log:
            counts = ssh_log.count(flag)
            # 结束时打印的log可能包含命令那一行，需要把这一行出现的次数去掉
            grep_counts = ssh_log.count('grep "%s"' % flag)
            counts -= grep_counts
        else:
            counts = 0
        aklog_info(self.device_name_log + '%s 出现次数: %s' % (flag, counts))
        return counts

    def get_system_log_by_tln_or_ssh(self, log_flag=None):
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d'
        else:
            command = 'cat /tmp/Messages*'
        if log_flag:
            command += ' | grep "%s"' % log_flag
        ssh_log = self.get_result_by_tln_or_ssh(command, print_result=False)
        return ssh_log

    def wait_get_syslog_by_tln_or_ssh(self, log_flag, timeout=30):
        """等待获取到指定的log"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            log = self.get_system_log_by_tln_or_ssh(log_flag)
            if log and log_flag in log:
                return log
            time.sleep(3)
            continue
        return None

    def get_ha_log_by_tln_or_ssh(self, log_flag=None):
        """获取HA的log"""
        command = 'cat /data/code/home-assistant.log'
        if log_flag:
            command += ' | grep "%s"' % log_flag
        ssh_log = self.get_result_by_tln_or_ssh(command, print_result=False)
        return ssh_log

    def export_syslog_to_results_dir_by_tln_or_ssh(self, case_name):
        """SSH或Telnet导出syslog并保存到Results目录下"""
        aklog_info()
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file = '{}\\PhoneLog--{}--{}--{}.log'.format(log_dir, case_name, self.device_name, log_time)
        File_process.create_dir(log_dir)
        log = self.get_system_log_by_tln_or_ssh()
        File_process.write_file(log_file, log, print_content=False)

    def export_ha_log_to_results_dir_by_tln_or_ssh(self, case_name):
        """SSH或Telnet导出HA log并保存到Results目录下"""
        aklog_info()
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file = '{}\\home-assistant--{}--{}--{}.log'.format(log_dir, case_name, self.device_name, log_time)
        File_process.create_dir(log_dir)
        log = self.get_ha_log_by_tln_or_ssh()
        File_process.write_file(log_file, log, print_content=False)

    def start_logs_by_interactive_tln_or_ssh(self, log_flag=None):
        """
        开始交互式获取设备log，需要配合save_log_to_result_dir_by_tln_or_ssh使用
        log_flag: 如果要同时过滤多组字段全部显示，可以在多组字段中间加 |，比如：relay1 state|relay2 state
        grep要加参数 -E， 比如:grep -E "relay1 state|relay2 state"
        """
        aklog_info()
        if log_flag and '|' in log_flag:
            log_flag = ' | grep -E "%s"' % log_flag
        elif log_flag:
            log_flag = ' | grep "%s"' % log_flag
        else:
            log_flag = ''
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat%s' % log_flag
            self.set_logcat_buffer_size()
            self.exec_command_by_interactive_ssh_thread(command)
        else:
            command = 'tail -F /tmp/Messages%s' % log_flag
            self.exec_command_by_interactive_telnet_thread(command)

    def get_logs_by_interactive_tln_or_ssh(self, timeout=60):
        """交互式获取设备log，需要配合start_logs_by_interactive_tln_or_ssh使用"""
        aklog_info()
        if self.device_config.get_remote_connect_type() == 'ssh':
            ret = self.get_result_by_interactive_ssh_thread(timeout)
        else:
            ret = self.get_result_by_interactive_telnet_thread(timeout)
        return ret

    def get_counts_with_interactive_log_flag(self, flag, ssh_log=None):
        """
        获取指定log出现多少次，需要配合start_logs_by_interactive_tln_or_ssh使用
        """
        aklog_info(self.device_name_log + 'get_counts_with_interactive_log_flag, flag: %s' % flag)
        if ssh_log is None:
            ssh_log = self.get_logs_by_interactive_tln_or_ssh()
        counts = 0
        if ssh_log:
            log_lines = ssh_log.split('\n')
            for line in log_lines:
                if flag in line and '| grep' not in line:
                    counts += 1
        aklog_info(self.device_name_log + '%s 出现次数: %s' % (flag, counts))
        return counts

    def save_logs_to_result_dir_by_tln_or_ssh(self, case_name, timeout=60):
        """保存交互式获取到的log到测试结果目录下，save_logs_to_result_dir_by_tln_or_ssh"""
        aklog_info()
        if self.device_config.get_remote_connect_type() == 'ssh':
            ret = self.get_result_by_interactive_ssh_thread(timeout)
        else:
            ret = self.get_result_by_interactive_telnet_thread(timeout)
        results = ret.split('\n')
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file = '{}\\PhoneLog--{}--{}--{}.txt'.format(log_dir, case_name, self.device_name, log_time)
        File_process.create_dir(log_dir)
        with open(log_file, 'w') as f:
            f.writelines(results)
        aklog_debug(f'log_file: {log_file}')

    def get_upload_capture_time_by_log(self):
        """获取上传截图的时间"""
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d | grep -v grep | grep "nTimestamp=" | tail -1 | cut -d "=" -f 2'
        else:
            command = 'cat /tmp/Messages | grep -v grep | grep "nTimestamp=" | tail -1 | cut -d "=" -f 2'
        time_stamp = self.get_result_by_tln_or_ssh(command)
        if time_stamp:
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time_stamp)))
        else:
            time_str = None
        return time_str

    def start_capture_syslog(self):
        """开启抓取log统一方法"""
        aklog_info()
        if self.device_config.get_reboot_clear_syslog():
            self.start_logs_by_interactive_tln_or_ssh()
            self.capture_syslog_enable = True

    def export_syslog_to_result(self, case_name):
        """保存日志到测试结果目录"""
        aklog_info()
        export_syslog_type = self.device_config.get_default_export_syslog_type()
        if self.capture_syslog_enable:
            self.capture_syslog_enable = False
            self.save_logs_to_result_dir_by_tln_or_ssh(case_name)
        elif export_syslog_type == 'logcat' or export_syslog_type == 'cat':
            self.export_syslog_to_results_dir_by_tln_or_ssh(case_name)
        else:
            self.export_syslog_to_results_dir(case_name)

    # </editor-fold>

    # <editor-fold desc="其他">
    def get_belahome_email_password(self, akemail_url, email_address, password):
        self.browser.visit_url(akemail_url)
        self.browser.max_window()
        time.sleep(15)
        self.browser.input_edit_by_id('RainLoopEmail', email_address)
        self.browser.input_edit_by_id('RainLoopPassword', password)
        self.browser.click_btn_by_xpath('//*[@id="rl-center"]/div[5]/div/div[1]/center/div[3]/form/div[5]/button')
        time.sleep(5)
        self.browser.click_btn_by_xpath(
            '//*[@id="rl-sub-left"]/div/div[2]/div[4]/div[1]/div/div[9]/div/div/div[3]/div[5]')
        time.sleep(3)
        account = self.browser.get_value_by_xpath(
            '/html/body/div[3]/div[2]/div[3]/div[3]/div/div/div[2]/div/div[5]/div[2]/div[1]/div/div[2]/div[2]/div/div/div/table/tbody/tr/td[2]/table/tbody/tr[3]/td[2]/table/tbody/tr[6]/td/table/tbody/tr[7]/td[2]/table[1]/tbody/tr[1]/td[2]')
        passwd = self.browser.get_value_by_xpath(
            '/html/body/div[3]/div[2]/div[3]/div[3]/div/div/div[2]/div/div[5]/div[2]/div[1]/div/div[2]/div[2]/div/div/div/table/tbody/tr/td[2]/table/tbody/tr[3]/td[2]/table/tbody/tr[6]/td/table/tbody/tr[7]/td[2]/table[1]/tbody/tr[3]/td[2]')
        print(account, passwd)
        self.browser.close_and_quit()
        return [account, passwd]

    def get_forgot_password_link(self, akemail_url, email_address, email_password, new_password):
        self.browser.visit_url(akemail_url)
        self.browser.max_window()
        time.sleep(15)
        self.browser.input_edit_by_id('RainLoopEmail', email_address)
        self.browser.input_edit_by_id('RainLoopPassword', email_password)
        self.browser.click_btn_by_xpath('//*[@id="rl-center"]/div[5]/div/div[1]/center/div[3]/form/div[5]/button')
        time.sleep(10)
        self.browser.click_btn_by_xpath(
            '//*[@id="rl-sub-left"]/div/div[2]/div[4]/div[1]/div/div[9]/div/div/div[3]/div[5]')
        time.sleep(3)
        link = self.browser.get_attribute_href_by_xpath(
            "/html/body/div[3]/div[2]/div[3]/div[3]/div/div/div[2]/div/div[5]/div[2]/div[1]/div/div[2]/div[2]/div/div/div/table/tbody/tr/td[2]/table/tbody/tr[3]/td[2]/table/tbody/tr[3]/td/table/tbody/tr[8]/td[2]/a")
        print(link)
        self.browser.visit_url(link)
        self.browser.max_window()
        self.browser.input_edit_by_xpath('/html/body/div/div/div[2]/div[2]/form/div[1]/div/div/div/input', new_password)
        self.browser.input_edit_by_xpath('/html/body/div/div/div[2]/div[2]/form/div[2]/div/div/div/input', new_password)
        self.browser.click_btn_by_xpath('//*[@id="app"]/div/div[2]/div[3]/button[2]/span')
        self.browser.close_and_quit()
        return link

    # </editor-fold>


if __name__ == '__main__':
    device_info = {'device_name': 'PS51', 'ip': '192.168.31.179'}
    device_config = config_parse_device_config('config_PS51_NORMAL')
    param_put_browser_headless_enable(True)  # 是否开启浏览器无头模式

    web = AkubelaPanelWeb()
    web.init_without_start(libbrowser(device_info, device_config))

    web.enter_settings_basic()
    # web.start_logs_by_interactive_tln_or_ssh('ringtone via android.media.Ringtone.')
    time.sleep(5)
    web.browser_close_and_quit()
