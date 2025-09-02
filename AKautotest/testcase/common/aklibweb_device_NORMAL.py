#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import datetime as dt
import traceback

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *
import requests
from requests.adapters import SSLError
from requests import ConnectTimeout


def screenshot_when_except(func):
    @wraps(func)
    def test1(self, *arg, **kwargs):
        try:
            return func(self, *arg, **kwargs)
        except:
            aklog_info(f'{func.__name__}执行异常, 准备截图')
            self.browser.screen_shot()
            aklog_debug(traceback.format_exc())

    return test1

class web_device_NORMAL(object):

    def __init__(self):
        self.browser = None
        self.device_config = None
        self.device_info = None
        self.device_mac = ''
        self.device_name = ''
        self.device_name_log = ''
        self.web_admin_username = 'admin'
        self.web_admin_pwd = 'Aa12345678'
        self.rom_version = ''
        self.device_ip = ''
        self.url = ''
        self.web_element_info = None
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
        self.tmp_device_config = None
        self.tln = None
        self.ssh = None
        self.tln_ssh_port_list = None
        self.tln_ssh_pwd_list = None
        self.version_branch = ''
        self.force_replace_old_version = False
        self.original_process_info = dict()

    # <editor-fold desc="初始化相关">

    def init_without_start(self, browser):
        self.browser = browser
        self.device_config = browser.get_device_config()
        self.tmp_device_config = self.device_config
        self.device_info = browser.get_device_info()
        if 'device_name' in self.device_info:
            self.device_name = self.device_info['device_name']
            self.device_name_log = '[' + self.device_name + '] '
        if 'ip' in self.device_info:
            self.device_ip = self.device_info['ip']
            self.url = 'http://%s' % self.device_ip
        if 'MAC' in self.device_info:
            self.device_mac = self.device_info['MAC']
        elif 'mac' in self.device_info:
            self.device_mac = self.device_info['mac']
        self.rom_version = param_get_rom_version()
        # self.device_config_dict_by_version[self.rom_version] = self.device_config
        if not self.version_branch:
            self.web_element_info = self.device_config.get_device_normal_web_element_info('WEB2_0')
        else:
            self.web_element_info = self.device_config.get_device_web_element_info(self.version_branch, 'WEB2_0')

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

    def init(self, browser):
        self.init_without_start(browser)
        time.sleep(1)
        self.browser.init()

    def start_and_login(self, url=None):
        if not self.is_opened_browser():
            self.browser.init()
        self.login(url)

    def web_env_init(self):
        pass

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
            aklog_info(self.device_name_log + str(traceback.format_exc()))
            return False

    def reset_imgs(self):
        self.browser.reset_imgs()

    def screen_shot(self):
        self.browser.screen_shot()

    def get_device_config_by_version(self, firmware_version):
        aklog_info(self.device_name_log + 'get_device_config_by_version, %s' % firmware_version)
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
        aklog_info(self.device_name_log + 'restore_device_config')
        self.device_config = self.tmp_device_config

    # </editor-fold>

    # <editor-fold desc="网页通用操作API">
    def is_exist(self, id_xpath, timeout=3):
        if id_xpath.startswith('./') or id_xpath.startswith('/'):
            return self.browser.is_exist_and_visible_ele_by_xpath(id_xpath, wait_time=timeout)
        else:
            id_xpath = './/*[text()="{}" or @id="{}" or @name="{}"]'.format(id_xpath, id_xpath, id_xpath)
            return self.browser.is_exist_and_visible_ele_by_xpath(id_xpath, wait_time=timeout)

    def get_element(self, id_xpath, log=True):
        if '//' in id_xpath:
            xpath = id_xpath
        else:
            if '|' in id_xpath:
                xpath = './/*['
                list1 = id_xpath.split('|')
                list1 = [i.strip() for i in list1]
                for i in list1:
                    xpath += '@id="{}" or @name="{}"'.format(i, i)
                    if i != list1[-1]:
                        xpath = xpath + ' or '
                xpath += ']'
            else:
                xpath = './/*[@id="%s" or @name="%s"]' % (id_xpath, id_xpath)
        try:
            element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                EC.visibility_of_element_located((By.XPATH, xpath
                                                  )))
            return element
        except:
            if log:
                aklog_error('Error: 未找到控件: {}'.format(id_xpath))
            return None

    def get_elements(self, id_xpath):
        if '//' not in id_xpath:
            id_xpath = './/*[@id="{}" or @name="{}"]'.format(id_xpath, id_xpath)
        try:
            element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                EC.visibility_of_any_elements_located((By.XPATH, id_xpath)))
            return element
        except:
            aklog_error('Error: 未找到控件: {}'.format(id_xpath))
            return None

    def click(self, id_xpath, sec=0.2):
        aklog_info()
        ele = self.get_element(id_xpath)
        try:
            self.browser.driver.execute_script("arguments[0].scrollIntoView();", ele)
        except:
            pass
        if ele:
            try:
                ele.click()
            except:
                try:
                    self.browser.driver.execute_script("arguments[0].click();", ele)
                except:
                    aklog_error('Error: 找到元素, 但无法点击!')
                    return False
                else:
                    time.sleep(sec)
                    return True
            else:
                time.sleep(sec)
                return True
        else:
            aklog_error('Error: 未找到元素, 无法点击!')
            return False

    def select_table_row_by_index(self, indexlist: list = 1):
        """基础接口, 选择表格的行勾选"""
        if indexlist == 'All' or indexlist == ['All']:
            self.write_config('cCheck0', True)
        else:
            if type(indexlist) == str or type(indexlist) == int:
                self.write_config('cCheck%s' % indexlist, True)
            else:
                for i in indexlist:
                    self.write_config('cCheck%s' % i, True)

    def deselect_table_row_by_index(self, indexlist: list = 1):
        """基础接口, 取消选择表格的行勾选"""
        if indexlist == 'All' or indexlist == ['All']:
            self.write_config('cCheck0', False)
        else:
            if type(indexlist) == str or type(indexlist) == int:
                self.write_config('cCheck%s' % indexlist, False)
            else:
                for i in indexlist:
                    self.write_config('cCheck%s' % i, False)

    def web_import(self, enter_func, file_widget, import_btn, file):
        aklog_info()
        enter_func()
        self.browser.upload_file_by_name(file_widget, file)
        self.click(import_btn)
        time.sleep(2)
        self.browser.alert_confirm_accept()
        for i in range(0, 10):
            value = self.browser.get_alert_text()
            if value and ("success" in value):
                self.browser.alert_confirm_accept()
                aklog_info('导入文件完成')
                return True
            elif i < 9:
                ele = self.get_element('tShowForAutoP')
                if ele and ele.text and 'success' in ele.text:
                    time.sleep(5)
                    aklog_info('导入文件完成')
                    return True
                else:
                    time.sleep(2)
                    continue
            else:
                aklog_error('导入文件失败，请检查原因')
                self.browser.screen_shot()
                return False

    def web_export(self, enter_func, export_btn, filename):
        aklog_info()
        file = self.device_config.get_chrome_download_dir() + filename
        File_process.remove_file(file)
        enter_func()
        if type(export_btn) == str:
            self.click(export_btn)
        else:
            # 如doorlog-->点击后, 选择xml, csv...
            self.write_config(export_btn[0], export_btn[1])
        time.sleep(10)
        for i in range(0, 20):
            if not os.path.exists(file):
                aklog_info('文件导出中...')
                time.sleep(3)
            else:
                time.sleep(3)
                aklog_info('{} 导出成功'.format(filename))
                return True
        aklog_error('文件导出失败')
        return False

    def web_refresh(self, force=True):
        self.browser.web_refresh(force)

    def wait_wan_connected(self, timeout=120):
        """等待设备网络可以连接上"""
        aklog_info()
        cur_time = time.time()
        for i in range(120):
            if time.time() - cur_time > timeout:
                return False
            try:
                requests.get('http://%s' % self.device_ip, timeout=2, verify=False)
            except:
                pass
            else:
                aklog_info('设备网络连接成功.')
                return True
            try:
                requests.get('https://%s' % self.device_ip, timeout=2, verify=False)
            except SSLError:
                # 2025.4.1 python 3.12 + 室内机, 使用这个会出现SSLError: HTTPSConnectionPool(host='192.168.30.138', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLError(1, '[SSL: DH_KEY_TOO_SMALL] dh key too small (_ssl.c:1010)')))
                return True
            except:
                pass
            else:
                aklog_info('设备网络连接成功.')
                return True
            time.sleep(10)
        return False

    def wait_wan_connnected(self, timeout=120):
        return self.wait_wan_connected(timeout)

    def wait_wan_disconnected(self, timeout=30):
        aklog_info()
        cur_time = time.time()
        for i in range(120):
            if time.time() - cur_time > timeout:
                return False
            try:
                requests.get('http://%s' % self.device_ip, timeout=1)
            except:
                ret1 = True
            else:
                ret1 = False
            try:
                requests.get('https://%s' % self.device_ip, timeout=1, verify=False)
            except SSLError:
                # 2025.4.1 python 3.12 + 室内机, 使用这个会出现SSLError: HTTPSConnectionPool(host='192.168.30.138', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLError(1, '[SSL: DH_KEY_TOO_SMALL] dh key too small (_ssl.c:1010)')))
                ret2 = False
            except:
                ret2 = True
            else:
                ret2 = False
            if ret1 and ret2:
                return True
            else:
                time.sleep(2)

    def judge_reboot_in_3min(self, timeout=180, reboottimeout=300):
        """2022.02.11 设备3min会重启, 且等待重启成功. 测试reboot schedule"""
        aklog_info()
        ret = self.wait_wan_disconnected(timeout)
        self.wait_wan_connected(reboottimeout)
        return ret

    def click_submit(self, accept=True):
        # 2021/6/9 不影响默认功能下, 添加accpet参数, 只保存但不处理弹窗.
        if not self.browser.click_btn_by_id('fPageSubmit'):
            self.browser.click_btn_by_id('PageSubmit')
        if accept:
            for i in range(2):
                if self.browser.is_exist_alert():
                    alert_text = self.browser.get_alert_text()
                    self.browser.alert_confirm_accept()
                    return alert_text
                try:
                    ret = self.browser.driver.page_source
                    if 'in talk now' in ret.lower():
                        aklog_error('设备通话中, 保存配置失败!!!!!')
                        return False
                except:
                    pass
                if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['logout']):
                    # or self.browser.is_exist_and_visible_ele_by_id('username'):
                    aklog_info(self.device_name_log + 'click submit success')
                    self.browser.restore_implicitly_wait()
                    return True
                elif i == 0:
                    self.browser.set_implicitly_wait(10)
                    continue
                else:
                    aklog_info(self.device_name_log + 'click submit failed')
                    self.browser.screen_shot()
                    self.browser.restore_implicitly_wait()
                    return False

    def click_submit2(self, accept=True):
        # 2021/6/9 不影响默认功能下, 添加accpet参数, 只保存但不处理弹窗.
        self.browser.click_btn_by_id('PageSubmit2')
        if accept:
            for i in range(2):
                if self.browser.is_exist_alert():
                    self.browser.alert_confirm_accept()
                if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['logout']):
                    # or self.browser.is_exist_and_visible_ele_by_id('username'):
                    aklog_info(self.device_name_log + 'click submit success')
                    self.browser.restore_implicitly_wait()
                    return True
                elif i == 0:
                    self.browser.set_implicitly_wait(10)
                    continue
                else:
                    aklog_info(self.device_name_log + 'click submit failed')
                    self.browser.screen_shot()
                    self.browser.restore_implicitly_wait()
                    return False

    def menu_expand_and_click(self, menu_id, submenu_id, ignore_error=True, retry_time=3):
        aklog_debug(self.device_name_log + 'menu_expand_and_click %s %s ' % (menu_id, submenu_id))
        if not self.login_status:
            aklog_error(self.device_name_log + 'login status is False!!!')
            return False
        for i in range(retry_time):
            if not self.browser.is_exist_and_visible_ele_by_id(menu_id):
                # 2024.12.18 lex: 嵌入式室内机, 门口机网页都新增了一层device managenment层级
                if i == 0:
                    if self.browser.is_exist_alert():
                        self.browser.alert_confirm_accept()
                        continue
                    elif self.is_exist('tMenu102'):
                        self.click('tMenu102')
                        sleep(1)
                        continue
                    elif self.is_exist('.//*[@id="tDeviceManagementLabel" or @id="tDevicecontrol"]'):
                        self.click('.//*[@id="tDeviceManagementLabel" or @id="tDevicecontrol"]')
                        sleep(1)
                        continue
                    else:
                        self.retry_login()
                        continue
                elif i <= 1:
                    self.retry_login()
                    continue
                else:
                    aklog_info(self.device_name_log + 'menu_expand_and_click failed')
                    return False
            else:
                break
        if not self.browser.is_exist_and_visible_ele_by_id(submenu_id):
            self.browser.click_btn_by_id(menu_id)
            time.sleep(2)
        self.browser.click_btn_by_id(submenu_id)
        for i in range(retry_time):
            if self.browser.get_attribute_by_id(submenu_id, 'style'):
                aklog_info(self.device_name_log + 'enter page success')
                break
            elif not ignore_error:
                aklog_info(self.device_name_log + 'menu_expand_and_click failed')
                return False
            if not self.browser.is_exist_and_visible_ele_by_id(submenu_id):
                if i <= 1:
                    self.retry_login()
                    continue
                else:
                    aklog_info(self.device_name_log + 'menu_expand_and_click failed')
                    return False
            else:
                self.browser.click_btn_by_id(submenu_id)
                if self.browser.is_exist_alert():
                    self.browser.alert_confirm_accept()
                continue
        return True

    def click_cancel(self):
        if not self.browser.click_btn_by_id('fPageCancel'):
            self.browser.click_btn_by_id('PageCancel')
        # self.browser.set_implicitly_wait(10)
        # if self.browser.is_exist_and_visible_ele_by_id('fPageCancel') \
        #         or self.browser.is_exist_and_visible_ele_by_id('PageCancel'):
        #     aklog_info(self.device_name_log + 'click cancel success')
        #     self.browser.restore_implicitly_wait()
        #     return True
        # aklog_info(self.device_name_log + 'click cancel failed')
        # self.browser.screen_shot()
        # self.browser.restore_implicitly_wait()
        # return False

    def click_btn_and_sleep_by_id(self, cmd, sec=0.2, alert_accept=False):
        """封装通过id进行button操作并延时"""
        self.browser.click_btn_by_id(cmd)
        if alert_accept:
            self.browser.alert_confirm_accept(wait_time=1)
        time.sleep(sec)

    def input_edit_and_sleep_by_id(self, edit_id, content, sec=0.2):
        """封装通过id输入edit操作并延时"""
        self.browser.input_edit_by_id(edit_id, content)
        time.sleep(sec)

    def input_edit_and_sleep_by_name(self, edit_id, content, sec=0.2):
        """封装通过name输入edit操作并延时"""
        self.browser.input_edit_by_name(edit_id, content)
        time.sleep(sec)

    def click_btn_and_sleep_by_xpath(self, cmd, sec=0.2):
        """封装通过xpath进行button操作并延时"""
        self.browser.click_btn_by_xpath(cmd)
        time.sleep(sec)

    def is_checked_box_and_sleep_by_id(self, cmd, sec=0.2):
        """封装通过id进行判断勾选框是否勾选并延时"""
        checked_status = self.browser.get_attribute_by_id(cmd, 'checked')
        time.sleep(sec)
        if checked_status == "true":
            return True
        else:
            return False

    def judge_and_check_labelbox_by_id(self, checkbox_id, label_id):
        """通过id勾选复选框(这个复选框是checkbox和label的结合，判断checkbox，点击label)"""
        if self.is_checked_box_and_sleep_by_id(checkbox_id) is not True:
            self.browser.check_box_by_id(label_id)

    def judge_and_uncheck_labelbox_by_id(self, checkbox_id, label_id):
        """通过id取消勾选复选框(这个复选框是checkbox和label的结合，判断checkbox，点击label)"""
        if self.is_checked_box_and_sleep_by_id(checkbox_id) is True:
            self.browser.check_box_by_id(label_id)

    def check_box_and_sleep_by_id(self, cmd, sec=0.2):
        """封装通过id勾选并延时"""
        if self.browser.is_exist_and_visible_ele_by_id(cmd):
            self.browser.check_box_by_id(cmd)
        elif not self.is_checked_box_and_sleep_by_id(cmd):
            self.browser.click_btn_by_xpath('//input[@id="%s"]/following-sibling::label[1]' % cmd)
        time.sleep(sec)

    def uncheck_box_and_sleep_by_id(self, cmd, sec=0.2):
        """封装通过id取消勾选并延时"""
        if self.browser.get_ele_status_by_id(cmd):
            if self.browser.is_exist_and_visible_ele_by_id(cmd):
                self.browser.uncheck_box_by_id(cmd)
            elif self.is_checked_box_and_sleep_by_id(cmd):
                self.browser.click_btn_by_xpath('//input[@id="%s"]/following-sibling::label[1]' % cmd)
            time.sleep(sec)

    def check_radio_preceding_label_by_id(self, ele_id):
        """封装通过label的id勾选单选框，单选框input在label前面"""
        self.browser.click_btn_by_id(ele_id)
        input_ele_xpath = '//label[@id="%s"]/preceding-sibling::input[1]' % ele_id
        checked_status = self.browser.get_attribute_by_xpath(input_ele_xpath, 'checked')
        if checked_status == "true":
            return True
        else:
            self.browser.click_btn_by_xpath(input_ele_xpath)

    def get_value_and_sleep_by_id(self, cmd, sec=0.2):
        """封装通过id进行获取value值"""
        value = self.browser.get_value_by_id(cmd)
        time.sleep(sec)
        return value

    def get_value_and_sleep_by_xpath(self, cmd, sec=0.2):
        value = self.browser.get_value_by_xpath(cmd)
        time.sleep(sec)
        return value

    def get_values_and_sleep_by_xpath(self, cmd, sec=0.2):
        value_list = self.browser.get_values_by_xpath(cmd)
        time.sleep(sec)
        return value_list

    def get_ele_counts_by_xpath_and_sleep(self, ele_xpath, sec=0.2):
        """封装web端获取相同Xpath元素的数量并延时"""
        counts = self.browser.get_ele_counts_by_xpath(ele_xpath)
        time.sleep(sec)
        return counts

    def alert_confirm_accept_and_sleep(self, sec=0.2):
        """封装web端弹窗确认操作并延时"""
        self.browser.alert_confirm_accept()
        time.sleep(sec)

    def web_get_alert_text_and_confirm(self, wait_time=None):
        """网页获取弹窗消息并确认"""
        if wait_time:
            alert_text = self.browser.get_alert_text(wait_time)
        else:
            alert_text = self.browser.get_alert_text()
        if alert_text:
            self.alert_confirm_accept_and_sleep()
        return alert_text

    def select_option_by_name_web_v1v2(self, ele_name, option_text):
        aklog_info(
            self.device_name_log + 'select_option_by_name_web_v1v2  ele_name: %s  option_text: %s' % (
                ele_name, option_text))
        if self.browser.get_tag_name_by_name(ele_name) == 'select':
            self.browser.select_option_by_name(ele_name, option_text)
        else:
            self.browser.select_option_by_xpath("//input[@name='%s']/../input[1]" % ele_name,
                                                "//input[@name='%s']/..//*[text()='%s']"
                                                % (ele_name, option_text))

    def select_option_by_id_web_v1v2(self, ele_id, option_text):
        aklog_info(
            self.device_name_log + 'select_option_by_id_web_v1v2  ele_id: %s  option_text: %s' % (
                ele_id, option_text))
        if self.browser.get_tag_name_by_id(ele_id) == 'select':
            self.browser.select_option_by_id(ele_id, option_text)
        else:
            self.browser.select_option_by_xpath("//input[@id='%s']/../input[1]" % ele_id,
                                                "//input[@id='%s']/..//*[text()='%s']"
                                                % (ele_id, option_text))

    def select_option_title_by_id_web_v1v2(self, ele_id, option_title):
        aklog_info(
            self.device_name_log + 'select_option_title_by_id_web_v1v2  ele_id: %s  option_title: %s' % (
                ele_id, option_title))
        if self.browser.get_tag_name_by_id(ele_id) == 'select':
            self.browser.select_option_by_id(ele_id, option_title)
        else:
            self.browser.select_option_by_xpath("//input[@id='%s']/../input[1]" % ele_id,
                                                "//input[@id='%s']/..//*[@title='%s']"
                                                % (ele_id, option_title))

    def select_option_title_by_name_web_v1v2(self, ele_name, option_title):
        aklog_info(
            self.device_name_log + 'select_option_title_by_name_web_v1v2  ele_name: %s  option_title: %s' % (
                ele_name, option_title))
        if self.browser.get_tag_name_by_name(ele_name) == 'select':
            self.browser.select_option_by_name(ele_name, option_title)
        else:
            self.browser.select_option_by_xpath("//input[@name='%s']/../input[1]" % ele_name,
                                                "//input[@name='%s']/..//*[@title='%s']"
                                                % (ele_name, option_title))

    def select_option_value_by_name_web_v1v2(self, ele_name, option_value):
        aklog_info(
            self.device_name_log + 'select_option_value_by_name_web_v1v2  ele_name: %s  option_value: %s' % (
                ele_name, option_value))
        if self.browser.get_tag_name_by_name(ele_name) == 'select':
            self.browser.select_option_value_by_name(ele_name, option_value)
        else:
            self.browser.select_option_by_xpath("//input[@name='%s']/../input[1]" % ele_name,
                                                "//input[@name='%s']/..//*[@option_value='%s']"
                                                % (ele_name, option_value))

    def select_option_value_by_id_web_v1v2(self, ele_id, option_value):
        aklog_info(
            self.device_name_log + 'select_option_value_by_id_web_v1v2  ele_id: %s  option_value: %s' % (
                ele_id, option_value))
        if self.browser.get_tag_name_by_id(ele_id) == 'select':
            self.browser.select_option_value_by_id(ele_id, option_value)
        else:
            self.browser.select_option_by_xpath("//input[@id='%s']/../input[1]" % ele_id,
                                                "//input[@id='%s']/..//*[@option_value='%s']" % (ele_id, option_value))
            # self.browser.click_btn_by_xpath("//input[@id='%s']/../input[1]" % ele_id)
            # self.browser.click_btn_by_xpath("//input[@id='%s']/..//*[@option_value='%s']" % (ele_id, option_value))

    def select_multi_options_value_by_id_web_v1v2(self, ele_id, option_values: tuple):
        """
        多选下拉框
        :param ele_id: 下拉框元素id
        :param option_values: 元组类型，比如: (1, 2)
        :return:
        """
        aklog_info(
            self.device_name_log + 'select_multi_options_value_by_id_web_v1v2  ele_id: %s  option_value: %r' % (
                ele_id, option_values))
        if self.browser.get_tag_name_by_id(ele_id) == 'select':
            self.browser.select_multi_options_value_by_id(ele_id, option_values)
        else:
            # 先获取所有option value值
            options_value_list = self.get_select_options_value_list_by_id(ele_id)
            new_options_ele_xpath = []
            # 然后判断选项是否被勾选，如果未被勾选并且不在选择的范围内或者被勾选但在选择的范围内，则不选择该选项
            for option_value in options_value_list:
                checkbox_ele_xpath = "//input[@id='%s']/..//*[@option_value='%s']/input" % (ele_id, option_value)
                if not self.browser.is_checked_box_by_xpath(checkbox_ele_xpath):
                    if int(option_value) not in option_values and str(option_value) not in option_values:
                        continue
                elif int(option_value) in option_values or str(option_value) in option_values:
                    continue
                # 获取要被勾选的选项Xpath
                option_ele_xpath = "//input[@id='%s']/..//*[@option_value='%s']" % (ele_id, option_value)
                new_options_ele_xpath.append(option_ele_xpath)
            self.browser.select_multi_option_by_xpath("//input[@id='%s']/../input[1]" % ele_id,
                                                      *new_options_ele_xpath)

    def is_exist_ele_by_id_web_v1v2(self, ele_id):
        aklog_info(
            self.device_name_log + 'select_option_value_by_id_web_v1v2  ele_id: %s' %
            ele_id)
        if self.browser.is_exist_and_visible_ele_by_id(ele_id):
            return True
        if self.browser.is_exist_and_visible_ele_by_xpath("//input[@id='%s']/../input[1]" % ele_id):
            return True
        else:
            return False

    def get_selected_option_by_name_web_v1v2(self, ele_name):
        aklog_info(self.device_name_log + 'get_selected_option_by_name_web_v1v2  ele_name: %s' % ele_name)
        tag_name = self.browser.get_tag_name_by_name(ele_name)
        if tag_name is None:
            aklog_info('元素不存在')
            return None
        elif tag_name == 'select':
            selected_option = self.browser.get_selected_option_by_name(ele_name)
        else:
            selected_option = self.browser.get_attribute_value_by_xpath("//input[@name='" + ele_name + "']/../input[1]")
        return selected_option

    def get_selected_option_by_id_web_v1v2(self, ele_id):
        aklog_info(self.device_name_log + 'get_selected_option_by_id_web_v1v2  ele_id: %s' % ele_id)
        tag_name = self.browser.get_tag_name_by_id(ele_id)
        if tag_name is None:
            aklog_info('元素不存在')
            return None
        elif tag_name and tag_name == 'select':
            selected_option = self.browser.get_selected_option_by_id(ele_id)
        else:
            selected_option = self.browser.get_attribute_value_by_xpath("//input[@id='" + ele_id + "']/../input[1]")
        return selected_option

    def get_selected_option_value_by_name_web_v1v2(self, ele_name):
        aklog_info(self.device_name_log + 'get_selected_option_value_by_name_web_v1v2  ele_name: %s'
                   % ele_name)
        tag_name = self.browser.get_tag_name_by_name(ele_name)
        if tag_name is None:
            aklog_info('元素不存在')
            return None
        elif tag_name == 'select':
            selected_option_value = self.browser.get_selected_option_value_by_name(ele_name)
        else:
            selected_option_value = self.browser.get_attribute_value_by_name(ele_name)
        return selected_option_value

    def get_selected_value_by_name(self, ele_name):
        return self.browser.get_attribute_value_by_xpath("//input[@name='" + ele_name + "']/")

    def get_multi_selected_options_by_name_web_v1v2(self, ele_name):
        """
        获取多选下拉框选中的选项
        :param ele_name:
        :return: list类型
        """
        aklog_info(self.device_name_log + 'get_multi_selected_option_by_name_web_v1v2  ele_name: %s'
                   % ele_name)
        if self.browser.get_tag_name_by_name(ele_name) == 'select':
            selected_options = self.browser.get_multi_selected_options_by_name(ele_name)
        else:
            # 先获取所有option value值
            options_value_list = self.get_select_options_value_list_by_name(ele_name)
            selected_options = []
            # 然后判断选项是否被勾选，如果未被勾选并且不在选择的范围内或者被勾选但在选择的范围内，则不选择该选项
            for option_value in options_value_list:
                checkbox_ele_xpath = "//input[@name='%s']/..//*[@option_value='%s']/input" % (ele_name, option_value)
                if self.browser.is_checked_box_by_xpath(checkbox_ele_xpath):
                    label_ele_xpath = "//input[@name='%s']/..//*[@option_value='%s']/label" % (ele_name, option_value)
                    option = self.browser.get_attribute_by_xpath(label_ele_xpath, 'textContent')
                    selected_options.append(option)
        return selected_options

    def get_multi_selected_options_by_id_web_v1v2(self, ele_id):
        """
        获取多选下拉框选中的选项
        :param ele_id:
        :return: list类型
        """
        aklog_info(self.device_name_log + 'get_multi_selected_options_by_id_web_v1v2  ele_id: %s'
                   % ele_id)
        if self.browser.get_tag_name_by_id(ele_id) == 'select':
            selected_options = self.browser.get_multi_selected_options_by_id(ele_id)
        else:
            # 先获取所有option value值
            options_value_list = self.get_select_options_value_list_by_id(ele_id)
            selected_options = []
            # 然后判断选项是否被勾选，如果未被勾选并且不在选择的范围内或者被勾选但在选择的范围内，则不选择该选项
            for option_value in options_value_list:
                checkbox_ele_xpath = "//input[@id='%s']/..//*[@option_value='%s']/input" % (ele_id, option_value)
                if self.browser.is_checked_box_by_xpath(checkbox_ele_xpath):
                    label_ele_xpath = "//input[@id='%s']/..//*[@option_value='%s']/label" % (ele_id, option_value)
                    option = self.browser.get_attribute_by_xpath(label_ele_xpath, 'textContent')
                    selected_options.append(option)
        return selected_options

    def get_select_options_value_list_by_name(self, ele_name):
        """获取下拉框option value列表"""
        aklog_info(self.device_name_log + 'get_select_options_value_list_by_name  ele_name: %s' % ele_name)
        if self.browser.get_tag_name_by_name(ele_name) == 'select':
            options_value_list = self.browser.get_select_options_value_list_by_name(ele_name)
        else:
            ele_counts = self.browser.get_ele_counts_by_xpath('//*[@name="%s"]/../div/ul/li' % ele_name)
            options_value_list = []
            for i in range(1, ele_counts + 1):
                option_value = self.browser.get_attribute_by_xpath('//*[@name="%s"]/../div/ul/li[%s]' % (ele_name, i),
                                                                   'option_value')
                options_value_list.append(option_value)
        return options_value_list

    def get_select_options_value_list_by_id(self, ele_id):
        """获取下拉框option value列表"""
        aklog_info(self.device_name_log + 'get_select_options_value_list_by_id  ele_id: %s' % ele_id)
        if self.browser.get_tag_name_by_id(ele_id) == 'select':
            options_value_list = self.browser.get_select_options_value_list_by_id(ele_id)
        else:
            ele_counts = self.browser.get_ele_counts_by_xpath('//*[@id="%s"]/../div/ul/li' % ele_id)
            options_value_list = []
            for i in range(1, ele_counts + 1):
                option_value = self.browser.get_attribute_by_xpath('//*[@id="%s"]/../div/ul/li[%s]' % (ele_id, i),
                                                                   'option_value')
                options_value_list.append(option_value)
        return options_value_list

    def get_select_options_list_by_name(self, ele_name):
        """获取下拉框option列表"""
        aklog_info(self.device_name_log + 'get_select_options_list_by_name  ele_name: %s' % ele_name)
        if self.browser.get_tag_name_by_name(ele_name) == 'select':
            options_list = self.browser.get_select_options_list_by_name(ele_name)
        else:
            ele_counts = self.browser.get_ele_counts_by_xpath('//*[@name="%s"]/../div/ul/li' % ele_name)
            options_list = []
            for i in range(1, ele_counts + 1):
                option = self.browser.get_attribute_by_xpath('//*[@name="%s"]/../div/ul/li[%s]' % (ele_name, i),
                                                             'textContent')
                options_list.append(option)
        return options_list

    def get_select_options_list_by_xpath(self, ele_xpath):
        """获取下拉框option列表"""
        aklog_info()
        if self.browser.get_tag_name_by_xpath(ele_xpath) == 'select':
            options_list = self.browser.get_select_options_list_by_xpath(ele_xpath)
        else:
            ele_counts = self.browser.get_ele_counts_by_xpath('%s/../div/ul/li' % ele_xpath)
            options_list = []
            for i in range(1, ele_counts + 1):
                option = self.browser.get_attribute_by_xpath('%s/../div/ul/li[%s]' % (ele_xpath, i),
                                                             'textContent')
                options_list.append(option)
        return options_list

    def get_select_options_list_counts_by_name(self, ele_name):
        """获取下拉框option列表数"""
        aklog_info(self.device_name_log + 'get_select_options_list_counts_by_name  ele_name: %s' % ele_name)
        ele_counts = self.browser.get_ele_counts_by_xpath('//*[@name="%s"]/../div/ul/li' % ele_name)
        return ele_counts

    def get_select_options_list_by_id(self, ele_id):
        """获取下拉框option列表"""
        aklog_info(self.device_name_log + 'get_select_options_list_by_id  ele_id: %s' % ele_id)
        if self.browser.get_tag_name_by_id(ele_id) == 'select':
            options_list = self.browser.get_select_options_list_by_id(ele_id)
        else:
            ele_counts = self.browser.get_ele_counts_by_xpath('//*[@id="%s"]/../div/ul/li' % ele_id)
            options_list = []
            for i in range(1, ele_counts + 1):
                option = self.browser.get_attribute_by_xpath('//*[@id="%s"]/../div/ul/li[%s]' % (ele_id, i),
                                                             'textContent')
                options_list.append(option)
        return options_list

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

        time.sleep(10)
        for i in range(0, 10):
            if self.browser.is_exist_and_visible_ele_by_id('username'):
                break
            else:
                self.browser.web_refresh(force=True)
                time.sleep(5)
                continue
        login_status = self.login_status
        result = self.login(url)
        self.login_status = login_status
        if close:
            self.browser.close_window()
            self.browser.switch_window(0)
        return result

    def wait_process_finished(self):
        """ 封装: 等待网页processing提示消失"""
        for i in range(0, 10):
            if self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
                aklog_info(self.device_name_log + 'Processing, please wait...')
                time.sleep(2)
            else:
                time.sleep(2)
                break

    def wait_autop_show_finished(self):
        """等待网页提示消失，并获取最后获取到的提示语"""
        last_show_text = None
        for i in range(0, 20):
            show_text = self.browser.get_value_by_id('tShowForAutoP')
            if show_text:
                aklog_info(self.device_name_log + 'Processing, please wait...')
                last_show_text = show_text
                time.sleep(1)
                continue
            else:
                time.sleep(2)
                break
        return last_show_text

    def wait_upload_finished(self):
        """封装:  等待文件按上传完成, 返回上传结果你"""
        for i in range(0, 10):
            if self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
                aklog_info(self.device_name_log + 'Processing, please wait...')
                time.sleep(2)
            else:
                time.sleep(2)
                break
        value = self.browser.get_alert_text()
        if "File uploaded success!" in value:
            self.browser.alert_confirm_accept()
            aklog_info(self.device_name_log + '导入文件完成')
            self.browser.screen_shot()
            return True
        else:
            aklog_info(self.device_name_log + '导入文件失败，请检查原因')
            self.browser.screen_shot()
            return False

    def get_wait_process_prompt(self):
        """获取网页等待提示语"""
        return self.browser.get_value_by_id('tPhoneUsingStatus')

    def judge_is_red_edit_by_id(self, ele_id):
        """判断输入框是否置红"""
        style = self.browser.get_attribute_by_id(ele_id, 'style')
        return style and 'background-color' in style

    def judge_is_red_by_id(self, ele_id):
        """判断元素是否置红"""
        ele = self.__adapt_element(ele_id, self.browser.driver, 2)
        if not ele:
            aklog_info('元素不存在')
            return False
        if ele.tag_name == 'input' and ele.get_attribute('class') == 'select_value':
            style = self.browser.get_attribute_by_xpath("//input[@id='" + ele_id + "']/../input[1]", 'style')
        else:
            style = ele.get_attribute('style')
        if not style:
            return False
        return style and 'background-color' in style

    def judge_is_note_warning(self, other=None):
        """
        判断右侧Note中warning是否出现: Please check your data in pink, it may contain invalid characters (&,%,',=) or its
        data range is wrong
        """
        submit_text = self.get_value_and_sleep_by_id('WarningDiv')
        if other:
            ret1 = "Please check your data in pink, it may contain invalid characters (&,%,',=) or " \
                   "its data range is wrong" in submit_text
            ret2 = other in submit_text
            return ret1 and ret2
        else:
            if submit_text:
                return "Please check your data in pink, it may contain invalid characters (&,%,',=) or " \
                       "its data range is wrong" in submit_text
            else:
                return False

    def is_exist_warning_text(self):
        """检测网页右侧导航栏Warning是否出现提示"""
        return self.browser.is_exist_and_visible_ele_by_id('WarningDiv')

    def get_warning_text(self):
        """获取网页置红提示语"""
        return self.browser.get_value_by_id('WarningDiv')

    def is_exist_phone_using_status_tip(self):
        """检测网页是否出现设备正在通话提示"""
        value = self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['phone_using_status'])
        return value

    def get_phone_using_status_tip(self):
        """获取网页设备正在通话页面的提示内容"""
        value = self.is_exist_phone_using_status_tip()
        if value:
            tip_text = self.browser.get_value_by_id(self.web_element_info['phone_using_status'])
            return tip_text
        else:
            return None

    def write_config(self, id_name, value, timeout=5):
        """
        判断大部分的通用网页元素类型, 选择输入框或者下拉框的方法操作.
        ps:
            1) 针对下拉框, value优先选择显示的文本, 否则使用value去选择.
            2) 复选框, 勾选框： value传入True/False，或者1和0
        """
        if value is None:
            return
        aklog_debug(self.device_name_log + "write config: %s with value: %s" % (id_name, value))
        ele = self.__adapt_element(id_name, self.browser.driver, timeout)
        if not ele:
            return False
        tag = self.__get_tag(ele)
        if tag not in ['select', 'input', 'textarea']:
            raise RuntimeError('接口未封装范围: id_name: %s  tag: %s' % (id_name, tag))
        else:
            if tag == 'select':
                value = value.strip()
                select = Select(ele)
                select_list = [i.text.strip() for i in select.options]
                if value in select_list:
                    select.select_by_visible_text(value)
                else:
                    select.select_by_value(value)
            elif tag in ['input', 'textarea']:
                if ele.get_attribute('type') == 'checkbox':
                    if value is False or str(value) == '0':
                        value = False
                    else:
                        value = True
                    if ele.is_selected() != value:
                        if ele.is_displayed():
                            # 复选框传入True/False 或者1和0（0表示取消勾选） 来选择勾选不勾选.
                            ele.click()
                        else:
                            # web 2.0复选框隐藏在label下面，需要点击label才行
                            label_xpath = "//input[@id='%s' or @name='%s']/following-sibling::label[1]" \
                                          % (id_name, id_name)
                            self.browser.click_btn_by_xpath(label_xpath)

                elif ele.get_attribute('class') == 'select_value':
                    # web 2.0下拉框不是select标签，需要用点击方式选择
                    if value is True:
                        value = 'Enabled'
                    elif value is False:
                        value = 'Disabled'
                    box_ele_xpath = "//input[@id='%s' or @name='%s']/../input[1]" % (id_name, id_name)
                    option_ele_xpath = "//input[@id='%s' or @name='%s']/..//*[text()='%s' or @option_value='%s']" \
                                       % (id_name, id_name, value, value)
                    self.browser.select_option_by_xpath(box_ele_xpath, option_ele_xpath, wait_time=5)
                    # box_ele = self.__adapt_element(box_ele_xpath, self.browser.driver, timeout)
                    # self.browser.click_by_js(box_ele)
                    # option_ele = self.__adapt_element(option_ele_xpath, self.browser.driver, timeout)
                    # self.browser.scroll_into_view_by_js(option_ele)
                    # self.browser.click_by_js(option_ele)
                else:
                    try:
                        ele.clear()
                        ele.send_keys(value)
                    except:
                        aklog_error('write config : {} - {} 失败'.format(id_name, value))
                        return False

    def read_config(self, id_name, timeout=5):
        """
        封装获取大部分网页控件的显示值.
        ps: 下拉框类型的返回其翻译值. 非value
        """
        ele = self.__adapt_element(id_name, self.browser.driver, timeout)
        if not ele:
            aklog_info('not found web element: %s' % id_name)
            return
        tag = self.__get_tag(ele)
        if tag == 'select':
            select = Select(ele)
            select_dict = dict(
                zip([i.get_attribute('value') for i in select.options], [i.text for i in select.options]))
            value = ele.get_attribute('value')
            aklog_info('read config: {}, value is : {}'.format(id_name, select_dict[value]))
            return select_dict[value]
        elif tag in ['input', 'textarea']:
            if ele.get_attribute('type') == 'checkbox':  # 复选框
                aklog_info('read config: {}, value is : {}'.format(id_name, ele.is_selected()))
                return ele.is_selected()
            elif ele.get_attribute('class') == 'select_value':
                # web 2.0下拉框不是select标签
                ele_xpath = "//input[@id='%s' or @name='%s']/../input[1]" % (id_name, id_name)
                ele = self.__adapt_element(ele_xpath, self.browser.driver, timeout)
            aklog_info('read config: {}, value is : {}'.format(id_name, ele.get_attribute('value')))
            return ele.get_attribute('value')
        elif tag == 'label':
            aklog_info('read config: {}, value is : {}'.format(id_name, ele.text))
            return ele.text
        else:
            raise RuntimeError('接口未封装范围: id_name: %s  tag: %s' % (id_name, tag))

    def __get_tag(self, ele):
        return ele.tag_name

    def __adapt_element(self, id_name_xpath, driver, timeout):
        xpath = id_name_xpath if '//' in id_name_xpath else './/*[@id="%s" or @name="%s"]' % (
            id_name_xpath, id_name_xpath)
        try:
            ele = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
            return ele
        except:
            return None  # 不报错, 避免影响后续的释放恢复动作.
            # raise RuntimeError('找不到元素: %s' % xpath)

    def judge_input_int_range(self, id_name, write_data, min, max):
        """
        封装测试, 输入框有效范围是 min~ max
        eg:
            测试IP port有效范围是整数, 范围1~65535
            judge_input_int_range('cDirectIPPort',5060, 1, 65535)
        """
        write_data = str(write_data)
        self.write_config(id_name, write_data)
        self.click_submit()
        if write_data.isdigit() and int(write_data) in range(int(min), int(max) + 1):
            self.browser.web_refresh()
            ret = self.read_config(id_name)
            if not ret:
                aklog_info(self.device_name_log + '元素: %s 输入了 %s 保存失败!' % (id_name, write_data))
            return ret == write_data
        else:
            ret = self.judge_is_note_warning()
            if not ret:
                aklog_info(self.device_name_log + '元素: %s 输入了 %s, 不在有效范围内, 没有报错!')
            return ret

    def get_current_page(self):
        """列表当前所处的页数"""
        all_page = self.browser.get_value_by_id('tCurPageInfo')
        current_page = all_page.split('/')[0]
        return current_page

    def get_list_max_page(self):
        """列表最大页数"""
        all_page = self.browser.get_value_by_id('tCurPageInfo')
        max_page = all_page.split('/')[1]
        return max_page

    def jump_to_list_page(self, page):
        """跳转到列表对应页数"""
        self.browser.input_edit_by_id('tGoToPage', page)
        self.browser.click_btn_by_id('tGoToPageBtn')
        time.sleep(1)

    def web_compare_image(self, xpath, pic, percent=0):
        aklog_info()
        TEMP_FILE = os.path.join(tempfile.gettempdir(), "temp_screen2.png")
        File_process.remove_file(TEMP_FILE)
        if xpath.startswith('/'):
            ele = self.browser.get_element_visible(By.XPATH, xpath)
        else:
            ele = self.browser.get_element_visible(By.ID, xpath)
        if not ele:
            aklog_error("不存在控件, 图片判断失败!!!!")
            return False
        else:
            ret = ele.screenshot(TEMP_FILE)
            if ret:
                ret = image_compare_after_convert_resolution(pic, TEMP_FILE, percent=percent)
                # File_process.remove_file(TEMP_FILE)
                return ret

    # </editor-fold>

    # <editor-fold desc="登录相关">
    def login(self, url=None, raise_enable=True, remember=None):
        """登录网页"""
        aklog_info()
        if url is None:
            url = 'http://%s' % self.device_ip
        if not self.browser.visit_url(url):
            aklog_error('网页 %s 访问失败' % url)
            self.login_status = False
            self.browser.screen_shot()
            if raise_enable:
                self.browser_close_and_quit()
                time.sleep(2)
                raise RuntimeError
            else:
                return False
        self.browser.web_refresh(force=True)
        login_counts = 0
        web_admin_pwd_tmp = self.web_admin_pwd
        i = 0
        while i < 5:
            if self.browser.is_exist_and_visible_ele_by_id('username'):
                if remember is False:
                    self.uncheck_box_and_sleep_by_id('cCheckSaveCookie')
                self.browser.input_edit_by_id("username", self.web_admin_username)
                self.browser.input_edit_by_id("password", self.web_admin_pwd)
                if remember:
                    time.sleep(0.5)
                    self.check_box_and_sleep_by_id('cCheckSaveCookie')
                self.browser.click_btn_by_id("Login")

                login_counts += 1

                # 多次登录失败限制登录，需要等待3分钟
                alert_text = self.browser.get_alert_text()
                if alert_text:
                    self.browser.alert_confirm_accept()
                    time.sleep(190)
                    continue

                if (self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['logout'])
                    and self.browser.is_exist_and_visible_ele_by_id('leftMenu')) or \
                        self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['modify_default_pwd_pane']) \
                        or ('security_change_pwd_alert_title_id_V6' in self.web_element_info and
                            self.browser.is_exist_and_visible_ele_by_id(
                                self.web_element_info['security_change_pwd_alert_title_id_V6'])):
                    aklog_info(self.device_name_log + '登录网页 %s 成功' % url)
                    self.login_status = True
                    self.modify_default_login_password()
                    if self.web_admin_pwd == 'Aa12345678' or self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678'):
                        return True
                    else:
                        break

                # 如果登录失败，则更改密码重新登录
                if login_counts == 1:
                    aklog_info(self.device_name_log + '密码: %s 登录失败，改密重登' % self.web_admin_pwd)
                    self.browser.screen_shot()
                    # 第一次登录失败，改用客户定制的admin用户的密码来登录
                    self.web_admin_pwd = self.device_config.get_web_admin_passwd()
                    continue
                elif login_counts == 2:
                    aklog_info(self.device_name_log + '密码: %s 登录失败，改密重登' % self.web_admin_pwd)
                    self.browser.screen_shot()
                    # 第二次登录失败，改用客户定制的用户和密码来登录，如果没有定制用户，则密码改为admin来登录
                    if self.web_admin_username != self.device_config.get_web_custom_username():
                        self.web_admin_username = self.device_config.get_web_custom_username()
                        self.web_admin_pwd = self.device_config.get_web_custom_passwd()
                    else:
                        self.web_admin_pwd = 'admin'
                    continue
                elif login_counts == 3:
                    # 第三次登录失败，需要等待3分钟
                    time.sleep(190)
                    self.web_admin_username = 'admin'
                    self.web_admin_pwd = 'Ak12345678'
                    continue
                else:
                    aklog_info(self.device_name_log + '登录网页 %s 失败' % url)
                    self.browser.screen_shot()
                    self.login_status = False
                    if raise_enable:
                        self.browser_close_and_quit()
                        time.sleep(2)
                        raise RuntimeError
                    else:
                        return False
            elif (self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['logout'])
                  and self.browser.is_exist_and_visible_ele_by_id('leftMenu')) or \
                    self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['modify_default_pwd_pane']) \
                    or ('security_change_pwd_alert_title_id_V6' in self.web_element_info and
                        self.browser.is_exist_and_visible_ele_by_id(
                            self.web_element_info['security_change_pwd_alert_title_id_V6'])):
                aklog_info(self.device_name_log + '网页已登录，无需再重新登录')
                self.login_status = True
                self.modify_default_login_password()
                if self.web_admin_pwd == 'Aa12345678' or self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678'):
                    return True
                else:
                    break
            else:
                time.sleep(5)
                self.browser.web_refresh()
                i += 1
                continue
        aklog_error(self.device_name_log + '登录网页 %s 失败' % url)
        self.browser.screen_shot()
        self.web_admin_pwd = web_admin_pwd_tmp
        self.login_status = False
        if raise_enable:
            self.browser_close_and_quit()
            time.sleep(2)
            raise RuntimeError
        else:
            return False

    def user_login(self, username, password, remember=None):
        """
        封装: 另外封装, 不去影响基础接口.
        输入username和password登陆界面. 用于测试user, admin登陆登出.
        """
        if remember is False:
            self.uncheck_box_and_sleep_by_id('cCheckSaveCookie')
        self.input_edit_and_sleep_by_id('username', username)
        self.input_edit_and_sleep_by_id('password', password)
        if remember:
            time.sleep(0.5)
            self.check_box_and_sleep_by_id('cCheckSaveCookie')
        self.click_btn_and_sleep_by_id('Login')

    def judge_is_web_login_page(self):
        """判断是否处于登录界面"""
        return self.browser.is_exist_and_visible_ele_by_id('Login')

    def judge_in_login_page(self):
        """
        封装: 判断在登陆界面
        """
        ret = self.browser.is_exist_and_visible_ele_by_id('username', wait_time=2)
        ret2 = self.browser.is_exist_and_visible_ele_by_id('password', wait_time=1)
        ret3 = self.browser.is_exist_and_visible_ele_by_id('Login', wait_time=1)
        return ret and ret2 and ret3

    def judge_login_success(self, refresh=False):
        """
        判断是在登录上的界面
        """
        aklog_debug()
        if refresh:
            self.web_refresh()
        return self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['logout'])

    def judge_login_failed(self):
        """
        封装: 判断登陆界面登陆失败
        """
        ele_id = 'cLoginResult'
        ret = self.browser.is_exist_and_visible_ele_by_id(ele_id, wait_time=2)
        ret2 = self.get_value_and_sleep_by_id(ele_id) == 'Login failed!'
        return ret and ret2

    def browser_close_and_reopen(self):
        if self.is_opened_browser():
            self.browser_close_and_quit()
        time.sleep(1)
        self.browser.init()

    def retry_visit_url(self, url=None):
        aklog_info()
        # current_url = self.browser.get_current_url()
        if url and '/fcgi/do?' in url:
            url_id = url.split('&RefRand')[0].split('/fcgi/do?')[1]
            url = 'http://%s/fcgi/do?%s' % (self.device_ip, url_id)
        else:
            url = 'http://%s' % self.device_ip
        return self.browser.visit_url(url)

    def retry_login(self, modify_default_pwd=True, raise_enable=True):
        aklog_info(self.device_name_log + 'retry_login')
        # 如果有弹窗，确定弹窗后返回登录界面说明登录超时需要等待3分钟
        alert_text = self.browser.get_alert_text()
        if alert_text:
            self.browser.alert_confirm_accept()
            if self.browser.is_exist_and_visible_ele_by_id('username'):
                time.sleep(190)
        current_url = self.browser.get_current_url()
        self.browser.close_and_quit()
        time.sleep(2)
        self.browser.init()
        # self.clear_browser_cache_data()
        if not self.retry_visit_url(current_url):
            aklog_fatal('重登网页失败')
            self.login_status = False
            self.browser.screen_shot()
            if raise_enable:
                self.browser_close_and_quit()
                time.sleep(2)
                raise RuntimeError
            else:
                return False

        self.browser.web_refresh(force=True)

        for i in range(2):
            if self.browser.is_exist_and_visible_ele_by_id('username'):
                self.browser.input_edit_by_id("username", self.web_admin_username)
                self.browser.input_edit_by_id("password", self.web_admin_pwd)
                self.browser.click_btn_by_id("Login")
                time.sleep(1)
            if i == 0 and modify_default_pwd:
                self.modify_default_login_password()
                continue

        # 判断是否登录成功
        self.web_refresh()
        sleep(3)
        if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['logout']) or \
                self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['status']):
            aklog_info(self.device_name_log + '重登网页成功')
            self.login_status = True
            return True
        else:
            aklog_info(self.device_name_log + '重登网页失败')
            self.browser.screen_shot()
            self.login_status = False
            if raise_enable:
                self.browser_close_and_quit()
                time.sleep(2)
                raise RuntimeError
            else:
                return False

    def judge_in_modify_default_pwd_page(self):
        return self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['modify_default_pwd_pane'])

    def reset_login_password_and_ignore(self):
        aklog_info(self.device_name_log + 'reset_login_password_and_ignore')
        if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['modify_default_pwd_pane']):
            self.browser.click_btn_by_id(self.web_element_info['security_modifymage_change_btn'])

    def close_modify_default_pwd_page(self):
        """点击右上角关闭修改默认密码窗口"""
        if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['modify_default_pwd_pane']):
            self.browser.click_btn_by_xpath('//input[@value="x" and @type="button"]')

    def modify_default_login_password(self):
        aklog_info(self.device_name_log + 'modify_default_login_password')
        new_pwd = 'Aa12345678'
        if new_pwd == self.web_admin_pwd:
            new_pwd = 'Ak12345678'
        if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['modify_default_pwd_pane']):
            self.browser.input_edit_by_id(self.web_element_info['security_modifymage_newpwd'], new_pwd)
            time.sleep(2)
            self.browser.input_edit_by_id(self.web_element_info['security_modifymage_confirmpwd'], new_pwd)
            # self.browser.click_btn_by_id(self.web_element_info['security_modifymage_change_btn'])
            self.browser.click_btn_by_xpath('//*[@id="cChange1" or @id="cChange" or @id="cModifyPage_Change"]')
            self.browser.alert_confirm_accept()
            time.sleep(2)
            self.browser.web_refresh()
            self.web_admin_pwd = new_pwd
        elif self.browser.is_exist_and_visible_ele_by_id('tChangePwdHint'):
            self.browser.input_edit_by_name('cNewPasswd', new_pwd)
            time.sleep(2)
            self.browser.input_edit_by_name('cConfirmPasswd', new_pwd)
            self.click_submit()
            time.sleep(3)
            self.browser.web_refresh()
            self.web_admin_pwd = new_pwd
        # 2021/6/10  linl: 新增的对原有doorphone登陆有影响, 先规避, 待同事确认.
        elif 'security_change_pwd_alert_title_id_V6' in self.web_element_info and \
                self.browser.is_exist_and_visible_ele_by_id(
                    self.web_element_info['security_change_pwd_alert_title_id_V6']):
            self.browser.input_edit_by_id(self.web_element_info['security_modifymage_newpwd_V6'], new_pwd)
            self.browser.input_edit_by_id(self.web_element_info['security_modifymage_confirmpwd_V6'], new_pwd)
            # self.browser.click_btn_by_id(self.web_element_info['security_modifymage_change_btn_V6'])
            self.browser.click_btn_by_xpath('//*[@id="cChange1" or @id="cChange" or @id="cModifyPage_Change"]')
            self.browser.alert_confirm_accept()
            time.sleep(1)
            self.browser.web_refresh()
            self.web_admin_pwd = new_pwd
        else:
            aklog_info(self.device_name_log + 'No change to default password pops up')

    def modify_default_pwd(self, new_pwd, confirm_pwd):
        """重新封装，用于测试修改密码界面"""
        if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['modify_default_pwd_pane']):
            self.browser.input_edit_by_id(self.web_element_info['security_modifymage_newpwd'], new_pwd)
            time.sleep(2)
            if self.browser.is_exist_and_visible_ele_by_id('trModifyPage_Condition0'):
                aklog_info(self.device_name_log + '密码不符合要求')
                return 'The password must'

            if not self.browser.get_ele_status_by_id(self.web_element_info['security_modifymage_confirmpwd']):
                aklog_info(self.device_name_log + '确认密码不可填写')
                return 'confirm pwd edit is disabled'

            self.browser.input_edit_by_id(self.web_element_info['security_modifymage_confirmpwd'], confirm_pwd)
            if self.browser.is_exist_and_visible_ele_by_id('trModifyPage_MatchAlert'):
                aklog_info(self.device_name_log + '确认密码不一致')
                return 'The entered passwords do not match !'

            if not self.browser.get_ele_status_by_id(self.web_element_info['security_modifymage_change_btn']):
                aklog_info(self.device_name_log + 'change按钮不可点击')
                return 'change btn is disabled'
            else:
                self.browser.click_btn_by_id(self.web_element_info['security_modifymage_change_btn'])
                self.browser.alert_confirm_accept()
                self.web_admin_pwd = new_pwd
                self.web_logout()
                self.user_login(self.web_admin_username, self.web_admin_pwd)
                return not self.judge_is_web_login_page()
        else:
            aklog_info(self.device_name_log + '没有弹出修改默认密码界面')
            return False

    def web_logout(self):
        aklog_info(self.device_name_log + 'web_logout')
        if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['logout']):
            self.browser.click_btn_by_id(self.web_element_info['logout'])
        if self.browser.is_exist_and_visible_ele_by_id('username'):
            aklog_info(self.device_name_log + '网页已登出')
            return True
        else:
            aklog_info(self.device_name_log + '网页登出失败')
            self.browser.screen_shot()
            return False

    def switch_custom_user_login(self):
        """有些OEM客户有定制web账户，需要切换到客户定制的账户去测试"""
        aklog_info(self.device_name_log + 'switch_custom_user_login')
        if self.web_admin_username != self.device_config.get_web_custom_username():
            self.web_admin_username = self.device_config.get_web_custom_username()
            self.web_admin_pwd = self.device_config.get_web_custom_passwd()
            self.retry_login()
        else:
            aklog_info(self.device_name_log + '帐号相同，无需切换')

    def switch_admin_user_login(self):
        """切换到admin账户"""
        aklog_info(self.device_name_log + 'switch_admin_user_login')
        if self.web_admin_username != self.device_config.get_web_admin_username():
            self.web_admin_username = self.device_config.get_web_admin_username()
            self.web_admin_pwd = self.device_config.get_web_admin_passwd()
            self.retry_login()
        else:
            aklog_info(self.device_name_log + '帐号相同，无需切换')

    # </editor-fold>

    # <editor-fold desc="Status页面相关">
    def enter_status_basic(self):
        aklog_info(self.device_name_log + 'enter_status_basic')
        self.menu_expand_and_click(self.web_element_info['status'], self.web_element_info['status_basic'])

    def put_rom_version(self, rom_version):
        """如果多个机型都需要升级，则可以在升级前传入版本号"""
        self.rom_version = rom_version

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

    def get_connect_status(self):
        self.enter_status_basic()
        connect_status = self.browser.get_value_by_id('cLANLinkStatus')
        aklog_info(self.device_name_log + 'get_connect_status, status: %s' % connect_status)
        return connect_status

    def web_connect_lan_link(self):
        aklog_info(self.device_name_log + 'web_connect_lan_link')
        self.enter_status_basic()
        for i in range(2):
            connect_status = self.browser.get_value_by_id('cLANLinkStatus')
            if connect_status == 'Connected':
                aklog_info(self.device_name_log + '设备已连接')
                return True
            elif i == 0:
                aklog_info(self.device_name_log + '设备连接异常，重启')
                self.web_reboot()
                continue
            else:
                aklog_info(self.device_name_log + '重启后，设备连接仍然异常')
                return False

    def web_get_current_version(self):
        """网页获取当前版本号"""
        self.menu_expand_and_click(self.web_element_info['status'], self.web_element_info['status_basic'])
        firmware_version = self.browser.get_value_by_id('cFirmwareVersion')
        return firmware_version

    def get_account_registered_status(self, account='1'):
        """网页status界面获取账号注册状态"""
        aklog_info(self.device_name_log + '网页status界面获取账号注册状态')
        time.sleep(5)
        self.menu_expand_and_click(self.web_element_info['status'], self.web_element_info['status_basic'])
        if account == '1':
            account_registered_status = self.browser.get_value_by_xpath(
                self.web_element_info['status_account1_register_status'])
            return account_registered_status
        elif account == '2':
            account_registered_status = self.browser.get_value_by_xpath(
                self.web_element_info['status_account2_register_status'])
            return account_registered_status

    def get_ip_by_status(self):
        """ 网页status界面获取ip地址 """
        aklog_info(self.device_name_log + '网页status界面获取ip地址')
        time.sleep(5)
        self.menu_expand_and_click(self.web_element_info['status'], self.web_element_info['status_basic'])
        ip = self.browser.get_value_by_xpath('//*[@id="cLANIPAddr"]')
        return ip

    def get_default_user_agent(self):
        """通过status页面的型号, 版本, 组合出默认user-agent"""
        self.enter_status_basic()
        model = self.browser.get_value_by_id(self.web_element_info['status_model'])
        if not model:
            model = self.browser.get_value_by_id('cPhoneModel')
        rom = self.browser.get_value_by_id(self.web_element_info['status_firmware_version'])
        mac = self.browser.get_value_by_id(self.web_element_info['status_mac_address'])
        vendor = self.device_config.get_oem_name()
        if vendor == 'NORMAL':
            vendor = 'Akuvox'
        # 'Akuvox C313W 113.30.6.82 A81102210414'
        return '%s %s %s %s' % (vendor, model, rom, mac)

    # </editor-fold>

    # <editor-fold desc="升级基础页面相关">
    def enter_upgrade_basic(self):
        aklog_info(self.device_name_log + 'enter_upgrade_basic')
        # self.enter_status_basic()
        self.menu_expand_and_click(self.web_element_info['upgrade_menu'],
                                   self.web_element_info['upgrade_basic_submenu'])

    def get_version(self):
        """获取当前版本号"""
        aklog_info('获取版本号')
        if not self.login_status:
            aklog_info('login status is False')
            return None
        self.enter_upgrade_basic()
        for i in range(0, 3):
            self.browser.web_refresh(force=True)
            if self.browser.is_exist_and_visible_ele_by_id('tFirmwareVersion'):
                for j in range(0, 60):
                    # 有些机型版本获取比较慢，需要等待一段时间，并刷新网页
                    firmware_version = self.browser.get_value_by_id('cFirmwareVersion')
                    if firmware_version:
                        firmware_version = self.restore_firmware_version(firmware_version)  # 有些机型OEM版本有定制model id
                        aklog_info(self.device_name_log + 'firmware_version: %s' % firmware_version)
                        return firmware_version
                    else:
                        time.sleep(5)
                        self.browser.web_refresh()
                break
            elif i == 0:
                aklog_info('获取版本号失败，可能是页面异常，重试...')
                self.browser.screen_shot()
                self.retry_login()
                self.enter_upgrade_basic()
                continue
            elif i == 1:
                aklog_info('网页获取版本号仍然失败，telnet或SSH重启设备')
                self.reboot_by_tln_or_ssh()
                self.retry_login()
                self.enter_upgrade_basic()
                continue
        aklog_info('获取版本号失败')
        self.browser.screen_shot()
        return None

    def web_basic_upgrade(self, firmware_path, reset=False):
        """网页基础升级，建议使用下面web_basic_upgrade_to_version这个方法"""
        aklog_info()
        # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
        cmd_waiting_for_network_rate_to_drop()

        self.enter_upgrade_advanced()
        self.set_autop_mode('0')
        self.enter_upgrade_basic()
        time.sleep(2)
        if reset:
            self.browser.click_btn_by_id('cResetAfterUpgrade', 1)
        self.browser.upload_file_by_id('UpgradeB_UpgradeFile', firmware_path, 3)
        self.browser.click_btn_by_id('UpgradeConfirmBtn', 1)
        self.browser.alert_confirm_accept(wait_time=2)
        time.sleep(5)

        # 判断是否处于升级状态
        begin_time = time.time()
        web_basic_upgrade_default_time = self.device_config.get_web_basic_upgrade_default_time()
        # end_time = begin_time + web_basic_upgrade_default_time
        # while time.time() < end_time:
        #     if self.browser.is_exist_and_visible_ele_by_id('failedReboot'):
        #         aklog_info(self.device_name_log + '页面提示升级失败，请检查升级失败原因')
        #         self.browser.screen_shot()
        #         self.upgrade_failed_reboot()
        #         return False
        #     elif self.browser.is_exist_and_visible_ele_by_id('tCheckDuringUpgrade') \
        #             or self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
        #         aklog_info(self.device_name_log + 'upgrade processing...')
        #         time.sleep(6)
        #     else:
        #         time.sleep(10)
        #         break
        sleep(20)
        # 判断是否处于升级状态
        begin_time = time.time()
        web_basic_upgrade_default_time = self.device_config.get_web_basic_upgrade_default_time()
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()  # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        cmd_waiting_for_device_reboot(self.device_ip, wait_time1=web_basic_upgrade_default_time,
                                      wait_time2=web_basic_upgrade_default_time / 2,
                                      sec=boot_time_after_get_ip)  # 等待设备升级完成后重启

        # 判断是否返回升级基础页面
        self.enter_upgrade_basic()
        if self.browser.is_exist_and_visible_ele_by_id('tUpgrade'):
            aklog_info(self.device_name_log + '返回升级基础页面')
            upgrade_status = True
        else:
            aklog_info(self.device_name_log + '升级后没有正常刷新到升级基础页面，需要重新加载')
            self.browser.screen_shot()
            upgrade_status = False

        for i in range(2):
            if upgrade_status:
                if self.retry_login():
                    self.enter_upgrade_basic()
                    break
            if i == 0:
                # 小概率出现网页显示异常导致升级等待时间不够，则增加每个机型默认等待时间，如果小于默认时间则需要等待足够时间
                wait_time = round(time.time() - begin_time)
                if wait_time < web_basic_upgrade_default_time:
                    continue_wait_time = web_basic_upgrade_default_time - wait_time
                    aklog_info('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                    time.sleep(continue_wait_time)
                upgrade_status = True
                continue
            else:
                # 恢复出厂后，如果当前版本有定制web账户密码，则使用定制账户密码登录，否则使用admin账号登录
                self.restore_device_config()
                if reset or self.device_config.get_reset_after_upgrade_enable():
                    if self.web_admin_username == 'admin':
                        self.web_admin_pwd = self.device_config.get_web_admin_passwd()
                    else:
                        self.web_admin_username = self.device_config.get_web_custom_username()
                        self.web_admin_pwd = self.device_config.get_web_custom_passwd()
                    self.set_network_to_dhcp_after_reset()
                    self.login()
                    self.modify_default_login_password()
                    self.switch_admin_user_login()
                    self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678')
                    self.switch_custom_user_login()
                    self.enter_upgrade_basic()
                break

        if self.browser.is_exist_and_visible_ele_by_id('tUpgrade'):
            aklog_info(self.device_name_log + '网页基础升级完成')
            return True
        else:
            aklog_info(self.device_name_log + '网页升级失败，请检查原因')
            self.browser.screen_shot()
            return False

    def web_basic_upgrade_to_version(self, dst_version, firmware_path, reset=False):
        """网页基础升级"""
        aklog_info()
        current_version = self.get_version()
        if current_version:
            if current_version == dst_version:
                aklog_info(self.device_name_log + '当前版本已是: %s, 无需升级' % dst_version)
                return True
        else:
            aklog_info(self.device_name_log + '获取版本号失败')
            return False

        if not os.path.exists(firmware_path):
            aklog_error('升级版本失败, rom文件不存在!! : {}'.format(firmware_path))
            return False
        else:
            if os.path.getsize(firmware_path) == 0:
                aklog_error('升级版本失败, rom文件大小为0 !!!: {}'.format(firmware_path))
                return False

        self.get_device_config_by_version(current_version)

        # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
        cmd_waiting_for_network_rate_to_drop()

        # 开始升级，先Disable autop
        self.enter_upgrade_advanced()
        self.set_autop_mode('0')
        self.enter_upgrade_basic()
        time.sleep(2)
        reset_ele_exist = False
        if reset:
            if self.is_exist('cResetAfterUpgrade'):
                reset_ele_exist = True
            self.browser.click_btn_by_id('cResetAfterUpgrade', 1)
        self.browser.upload_file_by_id('UpgradeB_UpgradeFile', firmware_path, 3)
        self.browser.click_btn_by_id('UpgradeConfirmBtn', 1)
        self.browser.alert_confirm_accept(wait_time=3)
        alert_text = self.browser.get_alert_text()
        if alert_text:
            if 'error' in alert_text.lower() or 'fail' in alert_text.lower():
                aklog_error('升级弹窗有异常!!!  Alert: {}'.format(alert_text))
            self.browser.alert_confirm_accept()
        sleep(20)
        # 判断是否处于升级状态
        begin_time = time.time()
        web_basic_upgrade_default_time = self.device_config.get_web_basic_upgrade_default_time()
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()  # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        # end_time = begin_time + web_basic_upgrade_default_time
        # while time.time() < end_time:
        #     if self.browser.is_exist_and_visible_ele_by_id('failedReboot'):
        #         aklog_info(self.device_name_log + '页面提示升级失败，请检查升级失败原因')
        #         self.browser.screen_shot()
        #         self.upgrade_failed_reboot()
        #         return False
        #     elif self.browser.is_exist_and_visible_ele_by_id('tCheckDuringUpgrade') \
        #             or self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
        #         aklog_info(self.device_name_log + 'upgrade processing...')
        #         sleep(6)
        #     else:
        #         if time.time() - begin_time < 30:
        #             # 2024.12.16 补充设备升级很快退出的截图.
        #             aklog_error('点击升级后30秒, 没有升级失败, 也没有升级中的提示...可能出现异常!!!')
        #             self.screen_shot()
        #             aklog_debug('~~~~~~~~~~')
        #             aklog_debug(self.browser.driver.page_source)
        #             aklog_debug('~~~~~~~~~~')
        #         sleep(10)
        #         break
        cmd_waiting_for_device_reboot(self.device_ip, wait_time1=web_basic_upgrade_default_time,
                                      wait_time2=web_basic_upgrade_default_time / 2,
                                      sec=boot_time_after_get_ip)  # 等待设备升级完成后重启

        # 判断是否返回升级基础页面
        if self.browser.is_exist_and_visible_ele_by_id('tUpgrade') or self.judge_is_web_login_page():
            aklog_info(self.device_name_log + '网页基础升级完成')
            upgrade_status = True
        else:
            aklog_info(self.device_name_log + '升级后没有正常刷新到基础升级页面，需要重新加载')
            self.browser.screen_shot()
            upgrade_status = False

        for i in range(2):
            if upgrade_status:
                if self.retry_login():
                    self.enter_upgrade_basic()
                    break
            if i == 0:
                # 小概率出现网页显示异常导致升级等待时间不够，则增加每个机型默认等待时间，如果小于默认时间则需要等待足够时间
                wait_time = round(time.time() - begin_time)
                if wait_time < web_basic_upgrade_default_time:
                    continue_wait_time = web_basic_upgrade_default_time - wait_time
                    aklog_info('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                    time.sleep(continue_wait_time)
                upgrade_status = True
                continue
            else:
                self.get_device_config_by_version(dst_version)
                # 有些OEM定制会在升级后恢复出厂
                if (reset and reset_ele_exist) or self.device_config.get_reset_after_upgrade_enable():
                    # 恢复出厂后，如果当前版本有定制web账户密码，则使用定制账户密码登录，否则使用admin账号登录
                    if self.web_admin_username == 'admin':
                        self.web_admin_pwd = self.device_config.get_web_admin_passwd()
                    else:
                        self.web_admin_username = self.device_config.get_web_custom_username()
                        self.web_admin_pwd = self.device_config.get_web_custom_passwd()
                    self.set_network_to_dhcp_after_reset()
                    self.login()
                    self.modify_default_login_password()
                    self.switch_admin_user_login()
                    self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678')
                    self.switch_custom_user_login()
                    self.enter_upgrade_basic()
                break

        firmware_version = self.get_version()
        if firmware_version == dst_version:
            aklog_info(self.device_name_log + '已升级到 %s 版本' % dst_version)
            self.get_device_config_by_version(dst_version)
            return True
        else:
            aklog_info(self.device_name_log + '网页升级失败，请检查原因')
            self.browser.screen_shot()
            self.get_device_config_by_version(current_version)
            return False

    def upgrade_failed_reboot(self):
        aklog_info(self.device_name_log + '提示升级失败，重启')
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
                self.retry_login()
                self.enter_upgrade_basic()
        aklog_info(self.device_name_log + '重启失败，请检查原因')
        self.browser.screen_shot()
        return False

    def support_upgrade_old_version(self):
        """
        判断由于rom包未指定等问题导致的不支持升级旧版本.
        """
        ret = self.device_config.get_old_firmware_version()
        if not ret:
            aklog_warn('由于下载rom包失败等问题, 无法升级到旧版本.')
            return False
        else:
            old_rom_version = self.device_config.get_old_firmware_version()
            return old_rom_version

    def support_upgrade_last_release_version(self):
        """
        对讲终端替换upgradecover.xml维护, 用于替换升级到旧版本的操作.
        返回版本号信息 或 False
        """
        aklog_info()
        version = self.device_config.intercom_get_last_release_version()
        if not version:
            return False
        # 做一次下载确认能正常下载到.
        ret = self.device_config.intercom_get_last_release_romfile()
        if not ret:
            return False
        return version

    def support_upgrade_new_version(self):
        romfile = self.device_config.get_local_firmware_path()
        if not os.path.exists(romfile):
            aklog_warn('由于下载rom包失败等问题, 无法升级到旧版本.')
            aklog_warn('rom文件放置路径: {}'.format(romfile))
            aklog_warn('rom下载路径配置: xxx.xml/firmware_path, 并取消勾选skip download firmware')
            return False
        else:
            return True

    def upgrade_new_version(self, reset=False, check_before=False):
        if check_before:
            try:
                if self.get_version() == self.rom_version:
                    return True
            except:
                pass
        aklog_info(self.device_name_log + '网页升级新版本')
        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        # 先判断是否要升级到过渡版本
        if self.upgrade_to_transition_version(self.rom_version):
            reset = True

        # 如果辅助设备要调用该方法，可以使用put_test_rom_version()将升级版本传入替换
        upgrade_result = self.web_basic_upgrade_to_version(
            self.rom_version,
            self.device_config.get_local_firmware_path(self.rom_version),
            reset=reset)
        self.restore_device_config()
        param_put_reboot_process_flag(True)
        return upgrade_result

    def upgrade_old_version(self, reset=False):
        """
        1.路径1:  E:\\aktest\\02.AutoTest\\Python\\AKautotest\\testfile\\old_firmware_version\\R20SV823\\BranchV1_1
                self.device_config.get_old_firmware(self.force_replace_old_version)
        """

        aklog_info(self.device_name_log + '网页升级旧版本')
        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        self.device_config.get_old_firmware(force_replace=self.force_replace_old_version)  # 强制替换旧版本升级包
        old_firmware_version = self.device_config.get_old_firmware_version()
        if old_firmware_version:

            # 先判断是否要升级到过渡版本
            if self.upgrade_to_transition_version(old_firmware_version):
                reset = True

            old_firmware_path = self.device_config.get_upgrade_firmware_dir(True) \
                                + old_firmware_version + self.device_config.get_firmware_ext()
            File_process.copy_file(self.device_config.get_old_firmware_path(), old_firmware_path)
            upgrade_result = self.web_basic_upgrade_to_version(old_firmware_version,
                                                               old_firmware_path,
                                                               reset=reset)
            File_process.remove_file(old_firmware_path)
        else:
            old_firmware_path = self.device_config.get_old_firmware_path()
            upgrade_result = self.web_basic_upgrade(old_firmware_path, reset=reset)
            if upgrade_result:
                old_firmware_version = self.get_version()
                model_name = self.device_config.get_model_name()
                old_firmware_dir = os.path.split(old_firmware_path)[0]
                old_firmware_file = '%s_NORMAL__%s%s' % (model_name, old_firmware_version,
                                                         self.device_config.get_firmware_ext())
                old_firmware_path2 = os.path.join(old_firmware_dir, old_firmware_file)
                File_process.move_file(old_firmware_path, old_firmware_path2)
        self.restore_device_config()
        param_put_reboot_process_flag(True)
        return upgrade_result

    def upgrade_cover_old_version(self, firmware_version, firmware_path):
        """升级覆盖测试，检查从旧版本升级到新版本是否成功"""
        local_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(),
                                          firmware_version, self.device_config.get_firmware_ext())
        self.download_firmware_to_upgrade_dir(firmware_version, firmware_path)
        ret1 = self.web_basic_upgrade_to_version(firmware_version, local_firmware_path)
        File_process.remove_file(local_firmware_path)
        if not ret1:
            aklog_info('升级到旧版本 %s 失败' % firmware_version)
            return False

        aklog_info('升级新版本之前先导出autop配置文件')
        autop_file_before_upgrade = self.export_autop_template('autop_file_before_upgrade.cfg')

        ret2 = self.upgrade_new_version()

        aklog_info('升级后再对比autop配置文件')
        config_ret = self.compare_autop_config_with_template(autop_file_before_upgrade)
        if not config_ret:
            aklog_info('升级后autop配置项存在不同')
        File_process.remove_file(autop_file_before_upgrade)
        return ret2 and config_ret

    def upgrade_to_transition_version(self, dst_version):
        """获取当前版本，并判断是否要升级到过渡版本，才升级到目标版本"""
        aklog_info()
        # 先获取版本
        current_version = self.get_version()
        if current_version:
            if current_version == dst_version:
                aklog_info('当前版本已是: %s, 无需升级' % dst_version)
                return None
        else:
            aklog_error('获取当前版本号失败, 不升级过渡版本.')
            return False
        self.get_device_config_by_version(current_version)

        # 判断当前版本属于哪个分支，是否跟目标版本相同分支
        cur_version_branch = config_parse_model_version_branch(self.device_config.get_model_name(), current_version)
        dst_version_branch = config_parse_model_version_branch(self.device_config.get_model_name(), dst_version)
        cur_sub_version_branch = ''
        if '.' in cur_version_branch and cur_version_branch == dst_version_branch:
            aklog_info('升级的目标版本跟当前版本属于同个分支，也属于同个子分支，不需要经过过渡版本')
            return None
        if cur_version_branch == dst_version_branch:
            # 只看到R29有这个文件, 其他机型都没有这个文件. 大部分通过version_model_info去维护.
            sub_version_branch_info = self.device_config.get_test_data('SubVersionBranch.xml', print_data=True)
            if not sub_version_branch_info or not sub_version_branch_info.get('SubVersionBranch'):
                aklog_info('当前机型不存在子分支版本信息，升级的目标版本跟当前版本属于同个分支，不需要经过过渡版本')
                return None
            sub_version_branch_info = sub_version_branch_info.get('SubVersionBranch')
            cur_sub_version_branch = config_parse_sub_version_branch(current_version, sub_version_branch_info)
            dst_sub_version_branch = config_parse_sub_version_branch(dst_version, sub_version_branch_info)
            if cur_sub_version_branch == dst_sub_version_branch:
                aklog_info('升级的目标版本跟当前版本属于同个子分支，不需要经过过渡版本')
                return None

        # 然后在TransitionVersion.xml文件中检查当前版本所属分支是否存在过渡版本，如果存在，说明当前版本要升级到目标版本需要先升级过渡版本
        aklog_info(
            '当前版本: {}, 目标版本: {}, 属于不同分支, 判断是否需要过渡版本...'.format(current_version, dst_version))
        test_data = self.device_config.get_test_data('TransitionVersion.xml', print_data=True)
        if not test_data or not test_data.get('TransitionVersion'):
            aklog_info('当前机型不存在过渡版本信息.  ps: 文件: TransitionVersion.xml')
            return None

        transition_version = ''
        transition_firmware_path = ''
        transition_version_data = test_data.get('TransitionVersion')
        for data in transition_version_data:
            # 获取TransitionVersion中跟当前版本分支相同的升级包版本信息
            if 'version_branch' in data and data['version_branch'] == cur_version_branch:
                transition_version = data['firmware_version']
                transition_firmware_path = data['firmware_path']
                break
            if 'sub_version_branch' in data and data['sub_version_branch'] == cur_sub_version_branch:
                transition_version = data['firmware_version']
                transition_firmware_path = data['firmware_path']
                break
        if not transition_version:
            aklog_info('升级的目标版本跟当前版本属于不同分支，但不存在过渡版本，不需要经过过渡版本')
            return None

        aklog_info('升级的目标版本跟当前版本属于不同分支，并且需要经过过渡版本')

        if current_version and current_version != transition_version:
            self.get_device_config_by_version(current_version)

            self.download_firmware_to_upgrade_dir(transition_version, transition_firmware_path)
            local_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(),
                                              transition_version, self.device_config.get_firmware_ext())

            upgrade_ret = self.web_basic_upgrade_to_version(transition_version, local_firmware_path)
            File_process.remove_file(local_firmware_path)
            if upgrade_ret:
                aklog_info('升级到过渡版本 %s 成功' % transition_version)
            else:
                aklog_info('升级到过渡版本 %s 失败' % transition_version)
                return False
        else:
            aklog_info('当前版本已是过渡版本: %s, 无需升级' % transition_version)

        if not self.device_config.get_auto_reset_after_transition_upgrade_enable():
            # 升级完成后，删除config目录下配置文件，之后再升级，相当于升级后恢复出厂，这样升级后就可以使用默认密码去登录
            aklog_info('升级到过渡版本后，删除config目录下配置文件')
            self.web_open_ssh()
            self.command_by_tln_or_ssh('rm /config/* -rf')
        param_put_reboot_process_flag(True)
        return True

    def intercom_upgrade_last_release_version(self, reset=True):
        """
        对讲终端根据共享文件夹获取同分支的上一个release版本.
        用于测试:  从一个发布版本升级到目标版本后, 不恢复出厂直接测试功能仍能正常.
        """
        aklog_info('准备升级到上一个发布版本. ')
        last_ver_file_path = self.device_config.intercom_get_last_release_romfile()
        if not last_ver_file_path:
            aklog_error('升级到上一个发布版本失败!')
            return False
        upgrade_result = self.web_basic_upgrade(last_ver_file_path, reset=reset)
        aklog_debug('升级结束!')
        self.screen_shot()
        param_put_reboot_process_flag(True)
        return upgrade_result

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
        elif 'http://' in firmware_path:
            aklog_info("将升级包从http服务器下载到本地目录")
            try:
                r = requests.get(firmware_path, timeout=600)
                with open(local_firmware_path, 'wb') as f:
                    f.write(r.content)
                download_result = True
            except:
                print(traceback.format_exc())
                download_result = False
                return None
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

    def copy_last_release_firmware_to_download_dir(self):
        """
        对讲终端修改旧版本为上一个发布版本来测试.
        """
        aklog_info()
        ret = self.device_config.intercom_get_last_release_romfile()
        if ret:
            last_release_file = self.device_config.intercom_get_last_release_romfile()
            File_process.copy_file(last_release_file,
                                   self.device_config.get_http_dir() + self.device_config.get_old_firmware_file())
            File_process.copy_file(last_release_file,
                                   self.device_config.get_https_dir() + self.device_config.get_old_firmware_file())
            File_process.copy_file(last_release_file,
                                   self.device_config.get_tftp_dir() + self.device_config.get_old_firmware_file())
            File_process.copy_file(last_release_file,
                                   self.device_config.get_ftp_dir() + self.device_config.get_old_firmware_file())

    def copy_new_firmware_to_download_dir(self):
        """将机型对应OEM的待测版本复制到autop下载目录"""
        aklog_info(self.device_name_log + 'copy_new_firmware_to_download_dir')
        File_process.copy_file(self.device_config.get_local_firmware_path(),
                               self.device_config.get_http_dir() + self.device_config.get_old_firmware_file())
        File_process.copy_file(self.device_config.get_local_firmware_path(),
                               self.device_config.get_https_dir() + self.device_config.get_old_firmware_file())
        File_process.copy_file(self.device_config.get_local_firmware_path(),
                               self.device_config.get_tftp_dir() + self.device_config.get_old_firmware_file())
        File_process.copy_file(self.device_config.get_local_firmware_path(),
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
            # 导入配置文件将ip设置为DHCP模式
            # self.write_cfg_items_to_import_file('Config.Network.LAN.Type = 0')
            # self.import_config_file()
            cmd_delete_ip_address(pc_ip_address)
        else:
            aklog_info(self.device_name_log + 'network type is already dhcp')

    def web_reset_to_factory_setting(self):
        """网页恢复出厂设置"""
        aklog_info(self.device_name_log + '网页恢复出厂设置')
        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        self.enter_upgrade_basic()
        self.browser.click_btn_by_id('ResetFactory', 1)
        self.browser.alert_confirm_accept(wait_time=2)
        # 判断是否处于恢复出厂等待
        begin_time = time.time()
        reset_default_time = self.device_config.get_reset_default_time()
        end_time = begin_time + reset_default_time
        while time.time() < end_time:
            if self.browser.is_exist_and_visible_ele_by_id('tCheckDuringUpgrade'):
                aklog_info(self.device_name_log + 'reset processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break
        self.wait_wan_connected()
        sleep(5)
        self.web_refresh()
        # 恢复出厂后，如果当前版本有定制web账户密码，则使用定制账户密码登录，否则使用admin账号登录
        if self.web_admin_username == 'admin':
            self.web_admin_pwd = self.device_config.get_web_admin_passwd()
        else:
            self.web_admin_username = self.device_config.get_web_custom_username()
            self.web_admin_pwd = self.device_config.get_web_custom_passwd()
        # 判断是否返回基础升级页面
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('tUpgrade') \
                    or self.browser.is_exist_and_visible_ele_by_id('tChangePwdHint') \
                    or self.browser.is_exist_and_visible_ele_by_id('username'):
                aklog_info(self.device_name_log + '恢复出厂设置完成')
                # 如果默认为静态ip，则恢复出厂配置后要用默认静态ip登录并修改为dhcp模式
                if i == 0:
                    self.set_network_to_dhcp_after_reset()
                self.modify_default_login_password()
                self.switch_admin_user_login()
                self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678')
                self.switch_custom_user_login()
                param_put_reboot_process_flag(True)
                return True
            elif i == 0:
                aklog_info(self.device_name_log + '恢复出厂设置后没有正常刷新到基础升级页面，需要重新加载')
                wait_time = round(time.time() - begin_time)
                if wait_time < reset_default_time:
                    continue_wait_time = reset_default_time - wait_time
                    aklog_info('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                    time.sleep(continue_wait_time)
                self.browser.screen_shot()
                # 如果默认为静态ip，则恢复出厂配置后要用默认静态ip登录并修改为dhcp模式
                self.set_network_to_dhcp_after_reset()
                self.retry_login()
                self.enter_upgrade_basic()
                continue
        aklog_info(self.device_name_log + '恢复出厂设置失败，请检查原因')
        self.browser.screen_shot()
        return False

    def web_reset_config_to_factory_setting(self, retry_login=True):
        """网页恢复出厂设置"""
        aklog_info(self.device_name_log + 'web_reset_config_to_factory_setting')
        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        self.enter_upgrade_basic()
        self.browser.click_btn_by_id('ResetAppFactory', 1)
        self.browser.alert_confirm_accept(wait_time=2)
        begin_time = time.time()
        reset_default_time = self.device_config.get_reset_config_default_time()
        end_time = begin_time + reset_default_time
        while time.time() < end_time:
            if self.browser.is_exist_and_visible_ele_by_id('tCheckDuringUpgrade'):
                aklog_info(self.device_name_log + 'reset processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break

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
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('tUpgrade') \
                    or self.browser.is_exist_and_visible_ele_by_id('tChangePwdHint') \
                    or self.browser.is_exist_and_visible_ele_by_id('username'):
                aklog_info(self.device_name_log + '恢复出厂设置完成')
                # 如果默认为静态ip，则恢复出厂配置后要用默认静态ip登录并修改为dhcp模式
                if i == 0:
                    self.set_network_to_dhcp_after_reset()
                self.modify_default_login_password()
                self.switch_admin_user_login()
                self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678')
                self.switch_custom_user_login()
                param_put_reboot_process_flag(True)
                return True
            elif i == 0:
                aklog_info(self.device_name_log + '恢复出厂设置后没有正常刷新到基础升级页面，需要重新加载')
                wait_time = round(time.time() - begin_time)
                if wait_time < reset_default_time:
                    continue_wait_time = reset_default_time - wait_time
                    aklog_info('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                    time.sleep(continue_wait_time)
                self.browser.screen_shot()
                # 如果默认为静态ip，则恢复出厂配置后要用默认静态ip登录并修改为dhcp模式
                self.set_network_to_dhcp_after_reset()
                self.retry_login()
                self.enter_upgrade_basic()
                continue
        aklog_info(self.device_name_log + '恢复出厂设置失败，请检查原因')
        self.browser.screen_shot()
        return False

    def web_reboot(self):
        """网页进行重启"""
        aklog_info(self.device_name_log + '网页进行重启')
        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        self.enter_upgrade_basic()
        self.browser.click_btn_by_id('Reboot', 1)
        self.browser.alert_confirm_accept(wait_time=2)
        begin_time = time.time()
        reboot_default_time = self.device_config.get_reboot_default_time()
        end_time = begin_time + reboot_default_time
        time.sleep(10)
        while time.time() < end_time:
            if self.browser.is_exist_and_visible_ele_by_xpath(
                    '//*[@id="tPhoneUsingStatus" or @id="tCheckDuringUpgrade"]'):
                aklog_info(self.device_name_log + 'reboot processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break
        # 判断是否返回升级基础页面
        self.web_refresh()
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('tUpgrade'):
                aklog_info(self.device_name_log + '重启完成')
                param_put_reboot_process_flag(True)
                return True
            elif self.browser.is_exist_and_visible_ele_by_id('username'):
                aklog_info(self.device_name_log + '重启完成, 并回到了登录页面')
                self.login()
                param_put_reboot_process_flag(True)
                return True
            elif i == 0:
                aklog_info(self.device_name_log + '重启后没有正常刷新到基础升级页面，需要重新加载')
                wait_time = round(time.time() - begin_time)
                if wait_time < reboot_default_time:
                    continue_wait_time = reboot_default_time - wait_time
                    aklog_info('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                    time.sleep(continue_wait_time)
                self.browser.screen_shot()
                self.retry_login()
                self.enter_upgrade_basic()
        aklog_info(self.device_name_log + '重启失败，请检查原因')
        self.browser.screen_shot()
        return False

    def wait_reboot_finished(self):
        """等待reboot结束"""
        begin_time = time.time()
        reboot_default_time = self.device_config.get_reboot_default_time()
        end_time = begin_time + reboot_default_time
        while time.time() < end_time:
            if self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
                aklog_info(self.device_name_log + 'reboot processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('tUpgrade'):
                aklog_info(self.device_name_log + '重启完成')
                return True
            elif i == 0:
                aklog_info(self.device_name_log + '重启后没有正常刷新到基础升级页面，需要重新加载')
                wait_time = round(time.time() - begin_time)
                if wait_time < reboot_default_time:
                    time.sleep(reboot_default_time - wait_time)
                self.retry_login()
        aklog_info(self.device_name_log + '重启失败，请检查原因')
        return False

    # </editor-fold>

    # <editor-fold desc="升级高级页面 Autop相关">
    def enter_upgrade_advanced(self):
        aklog_info()
        return self.menu_expand_and_click(self.web_element_info['upgrade_menu'],
                                          self.web_element_info['upgrade_advanced_submenu'])

    def set_autop_mode(self, option_value):
        """设置autop模式, Disabled, Power On, Repeatedly等"""
        aklog_info(self.device_name_log + 'set_autop_mode %s' % option_value)
        if not self.enter_upgrade_advanced():
            return False
        self.select_option_value_by_name_web_v1v2('cWhenToCheckNewFirm', str(option_value))
        # if self.browser.is_exist_and_visible_ele_by_name('cWhenToCheckNewFirm'):
        #     self.browser.select_option_value_by_name('cWhenToCheckNewFirm', option_value)
        # else:
        #     option_value = str(int(option_value) + 1)
        #     self.browser.click_btn_by_xpath("//input[@id='cWhenToCheckNewFirm']/../input[1]")
        #     self.browser.click_btn_by_xpath(
        #         "//input[@id='cWhenToCheckNewFirm']/../div[1]/ul[1]/li[" + option_value + "]")
        self.click_submit()

    def set_repeatedly_autop(self, option_value, hour, minu, power_on=False):
        """设置autop模式为repeatedly,并设置时间"""
        if not power_on:
            self.set_autop_mode('2')
        else:
            self.set_autop_mode('3')
        self.browser.set_implicitly_wait(10)
        if self.browser.is_exist_and_visible_ele_by_name(self.web_element_info['upgrade_advanced_autop_schedule']):
            self.browser.select_option_value_by_name(self.web_element_info['upgrade_advanced_autop_schedule'],
                                                     option_value)
        else:
            option_value = str(int(option_value) + 1)
            self.browser.click_btn_by_xpath("//input[@name='cScheduleDayOfWeek']/../input[1]")
            self.browser.click_btn_by_xpath(
                "//input[@name='cScheduleDayOfWeek']/../div[1]/ul[1]/li[" + option_value + "]")
        if 0 <= hour <= 23:
            self.input_edit_and_sleep_by_id(self.web_element_info['upgrade_advanced_autop_schedule_hour'], hour)
        else:
            aklog_info(self.device_name_log + "传入的时间参数有误")
        if 0 <= minu <= 59:
            self.input_edit_and_sleep_by_id(self.web_element_info['upgrade_advanced_autop_schedule_minu'], minu)
        else:
            aklog_info(self.device_name_log + "传入的分钟参数有误")
        self.click_submit()

    def set_automatic_autop_schedule(self, hour, minu):
        """设置Automatic Autop下的Schedule配置"""
        if not self.enter_upgrade_advanced():
            return False
        if 0 <= hour <= 23:
            self.input_edit_and_sleep_by_id(self.web_element_info['upgrade_advanced_autop_schedule_hour'], hour)
        else:
            aklog_info(self.device_name_log + "传入的时间参数有误")
        if 0 <= minu <= 59:
            self.input_edit_and_sleep_by_id(self.web_element_info['upgrade_advanced_autop_schedule_minu'], minu)
        else:
            aklog_info(self.device_name_log + "传入的分钟参数有误")
        self.click_submit()

    def rename_all_cfg_file(self):
        aklog_info(self.device_name_log + 'rename_all_cfg_file')
        File_process.rename_file(self.device_cfg_66, self.device_config.get_renamecfg_66())
        File_process.rename_file(self.device_cfg_43, self.device_config.get_renamecfg_43())
        File_process.rename_file(self.device_cfg_URL, self.device_config.get_renamecfg_URL())
        File_process.rename_file(self.device_cfg_custom, self.device_config.get_renamecfg_custom())
        File_process.rename_file(self.device_cfg_pnp, self.device_config.get_renamecfg_pnp())

    def click_clear_md5_btn(self):
        """点击清除MD5按钮"""
        if not self.enter_upgrade_advanced():
            return False
        self.browser.click_btn_by_id('ClearMD5Btn')
        self.browser.set_implicitly_wait(10)

    def input_manual_url(self):
        """输入手动url"""
        if not self.enter_upgrade_advanced():
            return False
        self.browser.input_edit_by_name(self.web_element_info['upgrade_advanced_mannal_url'],
                                        self.device_config.get_manual_autop_URL())
        self.click_submit()

    def clear_autop(self):
        """将autop相关配置项关闭或清空"""
        aklog_info(self.device_name_log + '清空autop配置项')
        self.enter_upgrade_advanced()
        self.browser.click_btn_by_id('ClearMD5Btn')
        self.browser.set_implicitly_wait(10)
        self.select_option_value_by_name_web_v1v2('cPNPConfig', '0')
        self.browser.restore_implicitly_wait()

        if self.browser.is_exist_and_visible_ele_by_name('cDHCPCustomOption'):
            self.browser.clear_edit_by_name('cDHCPCustomOption')

        if self.browser.is_checked_box_by_name('cDHCPOptionCustom') is True:
            if self.browser.is_exist_and_visible_ele_by_name('cDHCPOptionCustom'):
                self.browser.uncheck_box_by_name('cDHCPOptionCustom')
            else:
                self.browser.click_btn_by_id('tDhcpOption0')

        if self.browser.is_checked_box_by_name('cDHCPOption43') is True:
            if self.browser.is_exist_and_visible_ele_by_name('cDHCPOption43'):
                self.browser.uncheck_box_by_name('cDHCPOption43')
            else:
                self.browser.click_btn_by_id('tDhcpOption1')

        if self.browser.is_checked_box_by_name('cDHCPOption66') is True:
            if self.browser.is_exist_and_visible_ele_by_name('cDHCPOption66'):
                self.browser.uncheck_box_by_name('cDHCPOption66')
            else:
                self.browser.click_btn_by_id('tDhcpOption2')

        self.browser.clear_edit_by_name('cManualUpdateURL')
        self.select_option_value_by_name_web_v1v2('cWhenToCheckNewFirm', '1')
        self.click_submit()

    def clear_pnp_config(self):
        """关闭pnp"""
        if not self.enter_upgrade_advanced():
            return False
        self.select_option_value_by_name_web_v1v2('cPNPConfig', '0')
        self.browser.restore_implicitly_wait()

    def clear_dhcp_config(self):
        """将dhcp option相关配置项关闭或清空"""
        if not self.enter_upgrade_advanced():
            return False
        if self.browser.is_exist_and_visible_ele_by_name('cDHCPCustomOption'):
            self.browser.clear_edit_by_name('cDHCPCustomOption')

        if self.browser.is_checked_box_by_name('cDHCPOptionCustom') is True:
            if self.browser.is_exist_and_visible_ele_by_name('cDHCPOptionCustom'):
                self.browser.uncheck_box_by_name('cDHCPOptionCustom')
            else:
                self.browser.click_btn_by_id('tDhcpOption0')

        if self.browser.is_checked_box_by_name('cDHCPOption43') is True:
            if self.browser.is_exist_and_visible_ele_by_name('cDHCPOption43'):
                self.browser.uncheck_box_by_name('cDHCPOption43')
            else:
                self.browser.click_btn_by_id('tDhcpOption1')

        if self.browser.is_checked_box_by_name('cDHCPOption66') is True:
            if self.browser.is_exist_and_visible_ele_by_name('cDHCPOption66'):
                self.browser.uncheck_box_by_name('cDHCPOption66')
            else:
                self.browser.click_btn_by_id('tDhcpOption2')
        self.click_submit()

    def clear_manual_url(self):
        """清空手动url"""
        if not self.enter_upgrade_advanced():
            return False
        self.browser.clear_edit_by_name(self.web_element_info['upgrade_advanced_mannal_url'])
        self.click_submit()

    def pnp_autop(self):
        aklog_info(self.device_name_log + 'start pnp_autop')
        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        self.clear_autop()
        self.select_option_value_by_name_web_v1v2('cPNPConfig', '1')
        self.select_option_value_by_name_web_v1v2('cWhenToCheckNewFirm', '1')
        self.click_submit()
        self.start_autop()

    def dhcp_option43_autop(self):
        aklog_info(self.device_name_log + 'start dhcp_option43_autop')
        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        self.clear_autop()
        if self.browser.is_checked_box_by_name('cDHCPOption43') is False:
            if self.browser.is_exist_and_visible_ele_by_name('cDHCPOption43'):
                self.browser.check_box_by_name('cDHCPOption43')
            else:
                self.browser.click_btn_by_id('tDhcpOption1')
        self.click_submit()
        self.start_autop()

    def dhcp_option66_autop(self):
        aklog_info(self.device_name_log + 'start dhcp_option66_autop')
        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        self.clear_autop()
        if self.browser.is_checked_box_by_name('cDHCPOption66') is False:
            if self.browser.is_exist_and_visible_ele_by_name('cDHCPOption66'):
                self.browser.check_box_by_name('cDHCPOption66')
            else:
                self.browser.click_btn_by_id('tDhcpOption2')
        self.click_submit()
        self.start_autop()

    def dhcp_custom_option_autop(self):
        aklog_info(self.device_name_log + 'start dhcp_custom_option_autop')
        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        self.clear_autop()
        self.browser.input_edit_by_name('cDHCPCustomOption', self.device_config.get_custom_option())
        if self.browser.is_checked_box_by_name('cDHCPOptionCustom') is False:
            if self.browser.is_exist_and_visible_ele_by_name('cDHCPOptionCustom'):
                self.browser.check_box_by_name('cDHCPOptionCustom')
            else:
                self.browser.click_btn_by_id('tDhcpOption0')
        self.click_submit()
        self.start_autop()

    def manual_URL_autop(self, clear=True, autop_timeout=None, use_protocol=None):
        # clear: 是否清空md5, url等
        aklog_info(self.device_name_log + 'start manual_URL_autop')
        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        if clear:
            self.clear_autop()
        self.browser.input_edit_by_name(self.web_element_info['upgrade_advanced_mannal_url'],
                                        self.device_config.get_manual_autop_URL(use_protocol))
        self.click_submit()
        self.start_autop(autop_timeout)

    def no_clear_md5_manual_URL_autop(self):

        if not self.login_status:
            aklog_info(self.device_name_log + 'login status is False')
            return False
        self.clear_pnp_config()
        self.clear_dhcp_config()
        self.set_autop_mode('1')
        self.browser.input_edit_by_name(self.web_element_info['upgrade_advanced_mannal_url'],
                                        self.device_config.get_manual_autop_URL())
        self.click_submit()
        self.start_autop()

    def input_common_aes_key(self, key):
        """输入通用AES加密密码"""
        self.enter_upgrade_advanced()
        self.browser.input_edit_by_name(self.web_element_info['upgrade_advanced_common_aes_key'], key)
        self.click_submit()

    def input_mac_aes_key(self, key):
        """输入MAC AES加密密码"""
        self.enter_upgrade_advanced()
        self.browser.input_edit_by_name(self.web_element_info['upgrade_advanced_mac_aes_key'], key)
        self.click_submit()

    def start_autop(self, autop_timeout=None):
        """点击立即autop，开始autop升级"""
        aklog_info(self.device_name_log + '点击立即autop，开始autop升级')
        # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
        cmd_waiting_for_network_rate_to_drop()

        self.enter_upgrade_advanced()
        self.browser.click_btn_by_id('AutoPConfirmBtn')
        self.browser.alert_confirm_accept()

        if self.device_config.get_reset_after_upgrade_enable():
            # 当设备重启时，重命名cfg文件
            results = thread_start_with_join(
                (self.wait_autop_finished, (autop_timeout,)),
                self.check_device_upgrading_and_rename_cfg_file
            )
            return results == [True, True]
        else:
            return self.wait_autop_finished(autop_timeout)

    def wait_autop_finished(self, autop_timeout=None):
        """等待autop升级完成"""
        # 判断是否处于autop升级等待页面
        begin_time = time.time()
        if autop_timeout is None:
            autop_timeout = self.device_config.get_autop_upgrade_default_time()
        time.sleep(5)
        end_time = begin_time + autop_timeout
        i = 0
        while time.time() < end_time:
            if self.browser.is_exist_and_visible_ele_by_id('tShowForAutoP'):
                aklog_info(self.device_name_log + 'autop processing...')
                time.sleep(6)
                i += 1
                continue
            else:
                if i == 0:
                    self.browser.screen_shot()
                time.sleep(10)
                break

        # 判断是否返回升级高级页面
        self.enter_upgrade_advanced()
        if self.browser.is_exist_and_visible_ele_by_id('AutoPConfirmBtn'):
            aklog_info(self.device_name_log + '返回升级高级页面')
            autop_status = True
        else:
            aklog_info(self.device_name_log + 'Autop升级后无法再进入升级高级页面，请检查原因')
            self.browser.screen_shot()
            autop_status = False

        for i in range(2):
            if autop_status:
                if self.login():
                    self.enter_upgrade_advanced()
                    break
            if i == 0:
                # 小概率出现网页显示异常导致升级等待时间不够，则增加每个机型默认等待时间，如果小于默认时间则需要等待足够时间
                wait_time = round(time.time() - begin_time)
                if wait_time < autop_timeout:
                    continue_wait_time = autop_timeout - wait_time
                    aklog_info('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                    time.sleep(continue_wait_time)
                autop_status = True
                continue
            else:
                self.restore_device_config()
                # 有些机型OEM会升级后进行恢复出厂，如果当前版本有定制web账户密码，则使用定制账户密码登录，否则使用admin账号登录
                if self.web_admin_username == 'admin':
                    self.web_admin_pwd = self.device_config.get_web_admin_passwd()
                else:
                    self.web_admin_username = self.device_config.get_web_custom_username()
                    self.web_admin_pwd = self.device_config.get_web_custom_passwd()
                self.set_network_to_dhcp_after_reset()
                self.login()
                self.modify_default_login_password()
                self.switch_admin_user_login()
                self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678')
                self.switch_custom_user_login()
                self.enter_upgrade_advanced()

        if self.browser.is_exist_and_visible_ele_by_id('AutoPConfirmBtn'):
            aklog_info(self.device_name_log + 'Autop升级完成')
            return False
        else:
            aklog_info(self.device_name_log + 'Autop升级失败，请检查原因')
            self.browser.screen_shot()
            return False

    def check_device_upgrading_and_rename_cfg_file(self):
        """有些机型OEM版本，autop升级版本，也会进行恢复出厂，autop MD5会被清空，导致升级后会再次进入autop升级，
        因此当设备在升级重启时，将cfg文件改掉，这样就下载不到cfg文件了"""
        begin_time = int(time.time())
        end_time = begin_time + self.device_config.get_autop_upgrade_default_time()
        while time.time() < end_time:
            ping_result = cmd_get_ping_result(self.device_ip, ping_count=2)
            if ping_result[0] == 0:
                aklog_printf('设备重启中，重命名cfg文件')
                self.rename_all_cfg_file()
                return True
            else:
                time.sleep(5)
                continue
        aklog_printf('%s is not reboot' % self.device_ip)
        return False

    def get_alert_disable_autop(self):
        """disable模式下点击立即autop"""
        self.set_autop_mode('0')
        self.browser.click_btn_by_id(self.web_element_info['upgrade_advanced_autop_immediately'])
        alert = self.browser.get_alert_text()
        self.browser.alert_confirm_accept()
        return alert

    def export_autop_template(self, dst_file_name=None):
        """导出autop模板文件"""
        aklog_info(self.device_name_log + '导出autop模板文件')
        autop_export_file = self.device_config.get_autop_export_file_path()
        File_process.remove_file(autop_export_file)
        self.enter_upgrade_advanced()
        self.browser.click_btn_by_id('ExportTemplate')
        aklog_info(self.device_name_log + '导出autop配置文件: %s' % autop_export_file)
        time.sleep(20)
        # 判断文件是否导出成功
        for i in range(0, 20):
            if os.path.exists(autop_export_file):
                aklog_info('autop模板文件导出成功')
                time.sleep(3)
                if dst_file_name:
                    dst_file = self.device_config.get_chrome_download_dir() + dst_file_name
                    File_process.rename_file(autop_export_file, dst_file)
                    return dst_file
                else:
                    return True
            else:
                aklog_info(self.device_name_log + 'autop模板文件导出中...')
                time.sleep(3)
                continue
        aklog_info(self.device_name_log + 'autop模板文件导出失败')
        self.browser.screen_shot()
        return False

    def compare_autop_config_with_template(self, cfg_file):
        aklog_info(self.device_name_log + '对比autop升级配置项是否都升级成功')
        if not self.export_autop_template():
            return False
        export_file = self.device_config.get_autop_export_file_path()
        config_diff = File_process.compare_config_value(cfg_file, export_file)
        if config_diff is not None and len(config_diff) == 0:
            aklog_info(self.device_name_log + 'autop升级配置项成功')
            return True
        else:
            aklog_info(self.device_name_log + '存在配置项autop升级失败')
            aklog_info(self.device_name_log + '%s' % config_diff)
            return False

    def compare_autop_default_config(self):
        aklog_info(self.device_name_log + '对比autop默认配置项')
        if not self.export_autop_template():
            return False
        export_file = self.device_config.get_autop_export_file_path()
        template_file = self.device_config.get_autop_config_template_file()
        diff_export, diff_template = File_process.compare_default_config_value(export_file, template_file)
        # aklog_info(self.device_name_log + 'diff_export: %s, diff_template: %s'
        #              % (diff_export, diff_template))
        if diff_export == [] and diff_template == []:
            aklog_info(self.device_name_log + 'autop默认配置项跟模板一致')
            return True
        else:
            aklog_info(self.device_name_log + 'autop默认配置项跟模板不一致')
            return False

    def judge_autop_config_update_result(self, config_item):
        """对比autop升级配置项是否都升级成功，config_item可以传入多个配置项，用换行分隔"""
        aklog_info(self.device_name_log + 'judge_autop_config_update_result')
        if not self.export_autop_template():
            return None
        export_file = self.device_config.get_autop_export_file_path()
        config_item = config_item.strip()
        if '\n' in config_item:
            config_list = config_item.split('\n')
            result = False
            for item in config_list:
                item = item.strip()
                result = File_process.compare_config_is_in_file(item, export_file)
        else:
            result = File_process.compare_config_is_in_file(config_item, export_file)
        return result

    def export_config_file(self):
        """导出config文件"""
        aklog_info(self.device_name_log + '导出config文件')
        config_file = self.device_config.get_config_file_path()
        File_process.remove_file(config_file)
        self.enter_upgrade_advanced()
        self.browser.click_btn_by_id('ExportConfig')
        sleep(2)
        alerttext = self.browser.get_alert_text()
        if alerttext:
            aklog_error(alerttext)
            if 'is busy' in alerttext.lower():
                aklog_error('导出config.tgz失败!')
                return False
        aklog_info(self.device_name_log + '导出config文件: %s' % config_file)
        time.sleep(20)
        # self.download_save()
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not os.path.exists(config_file):
                aklog_info(self.device_name_log + 'config文件导出中...')
                time.sleep(3)
            else:
                time.sleep(3)
                return True
        aklog_info(self.device_name_log + 'config文件导出失败')
        self.browser.screen_shot()
        return False

    def autop_manual_config(self, path, *data):
        """
        autop手动升级配置
        :param path: cfg配置文件路径
        :param data: 可以传入多个配置项
        :return:
        """
        self.enter_upgrade_advanced()
        config_list = []
        for config in data:
            config = config.strip() + '\n'
            config_list.append(config)

        File_process.write_file(path, config_list)
        self.manual_URL_autop()

    # </editor-fold>

    # <editor-fold desc="autop配置文件">
    def get_device_cfg_URL(self):
        return self.device_cfg_URL

    def write_cfg_to_upgrade_pnp(self):
        aklog_info(self.device_name_log + 'write_cfg_to_upgrade_pnp')
        config_firmware_url = self.device_config.get_config_firmware_url_pnp()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url
        File_process.rename_file(self.device_config.get_renamecfg_pnp(), self.device_cfg_pnp)
        File_process.write_file(self.device_cfg_pnp, config_firmware_url)

    def write_cfg_to_upgrade_43(self):
        aklog_info(self.device_name_log + 'write_cfg_to_upgrade_43')
        config_firmware_url = self.device_config.get_config_firmware_url_43()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url
        File_process.rename_file(self.device_config.get_renamecfg_43(), self.device_cfg_43)
        File_process.write_file(self.device_cfg_43, config_firmware_url)

    def write_cfg_to_upgrade_66(self):
        aklog_info(self.device_name_log + 'write_cfg_to_upgrade_66')
        config_firmware_url = self.device_config.get_config_firmware_url_66()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url
        File_process.rename_file(self.device_config.get_renamecfg_66(), self.device_cfg_66)
        File_process.write_file(self.device_cfg_66, config_firmware_url)

    def write_cfg_to_upgrade_custom(self):
        aklog_info(self.device_name_log + 'write_cfg_to_upgrade_custom')
        config_firmware_url = self.device_config.get_config_firmware_url_custom()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url
        File_process.rename_file(self.device_config.get_renamecfg_custom(), self.device_cfg_custom)
        File_process.write_file(self.device_cfg_custom, config_firmware_url)

    def write_cfg_to_upgrade_manual_URL(self):
        aklog_info(self.device_name_log + 'write_cfg_to_upgrade_manual_URL')
        config_firmware_url = self.device_config.get_config_firmware_url_manual_URL()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url
        File_process.rename_file(self.device_config.get_renamecfg_URL(), self.device_cfg_URL)
        File_process.write_file(self.device_cfg_URL, config_firmware_url)

    def write_config_to_pnp_cfg(self, *configs):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        aklog_info(self.device_name_log + 'write_config_to_pnp_cfg')
        File_process.rename_file(self.device_config.get_renamecfg_pnp(), self.device_cfg_pnp)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        config_content = f'# {str(time.time())}\n' + config_content
        File_process.write_file(self.device_cfg_pnp, config_content)

    def write_config_to_option43_cfg(self, *configs):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        aklog_info(self.device_name_log + 'write_config_to_option43_cfg')
        File_process.rename_file(self.device_config.get_renamecfg_43(), self.device_cfg_43)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        config_content = f'# {str(time.time())}\n' + config_content
        File_process.write_file(self.device_cfg_43, config_content)

    def write_config_to_option66_cfg(self, *configs):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        aklog_info(self.device_name_log + 'write_config_to_option66_cfg')
        File_process.rename_file(self.device_config.get_renamecfg_66(), self.device_cfg_66)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        config_content = f'# {str(time.time())}\n' + config_content
        File_process.write_file(self.device_cfg_66, config_content)

    def write_config_to_custom_option_cfg(self, *configs):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        aklog_info(self.device_name_log + 'write_config_to_custom_option_cfg')
        File_process.rename_file(self.device_config.get_renamecfg_custom(), self.device_cfg_custom)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        config_content = f'# {str(time.time())}\n' + config_content
        File_process.write_file(self.device_cfg_custom, config_content)

    def write_config_to_manual_URL_cfg(self, *configs, comm_or_mac='mac'):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        aklog_info(self.device_name_log + 'write_config_to_manual_URL_cfg')
        if comm_or_mac == 'mac':
            device_cfg = self.device_cfg_URL
        else:
            device_cfg = self.device_comm_cfg_URL
        File_process.rename_file(self.device_config.get_renamecfg_URL(), device_cfg)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        config_content = f'# {str(time.time())}\n' + config_content
        File_process.write_file(device_cfg, config_content)

    def copy_cfg_to_config_pnp(self):
        """将配置文件复制到手动URL的下载目录替换"""
        aklog_info(self.device_name_log + 'copy_cfg_to_config_pnp')
        File_process.rename_file(self.device_config.get_renamecfg_pnp(), self.device_cfg_pnp)
        File_process.copy_file(self.device_config.get_autop_config_file(), self.device_cfg_pnp)

    def copy_cfg_to_config_43(self):
        """将配置文件复制到手动URL的下载目录替换"""
        aklog_info(self.device_name_log + 'copy_cfg_to_config_43')
        File_process.rename_file(self.device_config.get_renamecfg_43(), self.device_cfg_43)
        File_process.copy_file(self.device_config.get_autop_config_file(), self.device_cfg_43)

    def copy_cfg_to_config_66(self):
        """将配置文件复制到手动URL的下载目录替换"""
        aklog_info(self.device_name_log + 'copy_cfg_to_config_66')
        File_process.rename_file(self.device_config.get_renamecfg_66(), self.device_cfg_66)
        File_process.copy_file(self.device_config.get_autop_config_file(), self.device_cfg_66)

    def copy_cfg_to_config_custom(self):
        """将配置文件复制到手动URL的下载目录替换"""
        aklog_info(self.device_name_log + 'copy_cfg_to_config_custom')
        File_process.rename_file(self.device_config.get_renamecfg_custom(), self.device_cfg_custom)
        File_process.copy_file(self.device_config.get_autop_config_file(), self.device_cfg_custom)

    def copy_cfg_to_config_manual_URL(self):
        """将配置文件复制到手动URL的下载目录替换"""
        aklog_info(self.device_name_log + 'copy_cfg_to_config_manual_URL')
        File_process.rename_file(self.device_config.get_renamecfg_URL(), self.device_cfg_URL)
        File_process.copy_file(self.device_config.get_autop_config_file(), self.device_cfg_URL)

    def copy_autop_export_file_to_config_import_file(self):
        """将autop导出模板复制到导入文件目录替换"""
        aklog_info(self.device_name_log + 'copy_autop_export_file_to_config_import_file')
        File_process.copy_file(self.device_config.get_autop_export_file_path(),
                               self.device_config.get_config_import_file())

    def copy_config_file_to_config_import_file(self):
        """将config导出文件复制到导入文件目录替换"""
        aklog_info(self.device_name_log + ' copy_config_file_to_config_import_file')
        File_process.copy_file(self.device_config.get_config_file_path(),
                               self.device_config.get_config_import_file_tgz())

    def copy_mac_aes_cfg_to_config_manual_URL(self, ):
        """将AES加密配置文件复制到手动URL的下载目录替换MAC文件"""
        File_process.remove_file(self.device_comm_cfg_URL)
        File_process.copy_file(self.device_config.get_aes_autop_config_file(), self.device_cfg_URL)

    def copy_common_aes_cfg_to_config_manual_URL(self, ):
        """将AES加密配置文件复制到手动URL的下载目录替换Config文件"""
        File_process.remove_file(self.device_cfg_URL)
        File_process.copy_file(self.device_config.get_aes_autop_config_file(), self.device_comm_cfg_URL)

    def remove_mac_config_manual_URL(self):
        """移除手动URL的下载目录下的MAC config配置文件"""
        File_process.remove_file(self.device_cfg_URL)

    def remove_common_config_manual_URL(self):
        """移除手动URL的下载目录下的Common config配置文件"""
        File_process.remove_file(self.device_comm_cfg_URL)

    # </editor-fold>

    # <editor-fold desc="升级高级页面">
    def write_cfg_items_to_import_file(self, *config_items):
        aklog_info(self.device_name_log + 'write_cfg_items_to_import_file')
        config_list = []
        for config in config_items:
            config = config.strip() + '\n'
            config_list.append(config)
        File_process.write_file(self.device_config.get_config_import_file(), config_list)

    def import_config_file(self, cfg=None, error_ignore=True):
        """保持原用法基础上, 增加参数: cfg 用于如R20T30机型cfg文件不能包含数字字母以外字符"""
        aklog_info(self.device_name_log + 'import_config_file')
        self.enter_upgrade_advanced()
        if not cfg:
            self.browser.upload_file_by_id('importConfigFile', self.device_config.get_config_import_file())
        else:
            if ':' not in cfg:  # 指定的路径也可以是相对于root_path的相对路径（Windows系统）
                cfg = root_path + cfg
            self.browser.upload_file_by_id('importConfigFile', cfg)
        self.browser.click_btn_by_id('ImportConfig')
        if error_ignore:
            self.browser.alert_confirm_accept()
        else:
            # 如果不忽略错误，用于导入错误文件，判断弹窗提示并返回
            time.sleep(1)
            alert = self.browser.get_alert_text()
            if alert != 'The original config file will be overwritten, make sure to upload it?':
                self.browser.alert_confirm_accept()
                return alert
        time.sleep(5)
        # 等待显示重启按钮
        for i in range(20):
            if self.browser.is_exist_and_visible_ele_by_id('ConfigReboot'):
                self.browser.click_btn_by_id('ConfigReboot')
                break
            else:
                time.sleep(3)
        # 判断是否处于重启等待页面
        for i in range(0, 50):
            if self.browser.is_exist_and_visible_ele_by_id('tShowForAutoP'):
                aklog_info(self.device_name_log + 'reboot processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break
        # 判断是否返回升级高级页面
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('ImportConfig'):
                aklog_info(self.device_name_log + '导入配置文完成')
                return True
            elif i == 0:
                aklog_info(self.device_name_log + '导入配置文件后无法再进入升级高级页面，重新登录')
                self.browser.screen_shot()
                self.retry_login()
        aklog_info(self.device_name_log + '导入配置文件失败，请检查原因')
        self.browser.screen_shot()
        return False

    def import_config_file_tgz(self):
        aklog_info(self.device_name_log + 'import_config_file_tgz')
        self.enter_upgrade_advanced()
        self.browser.upload_file_by_id('importConfigFile', self.device_config.get_config_import_file_tgz())
        self.browser.click_btn_by_id('ImportConfig')
        self.browser.alert_confirm_accept()
        time.sleep(5)
        # 等待显示重启按钮
        for i in range(20):
            if self.browser.is_exist_and_visible_ele_by_id('ConfigReboot'):
                self.browser.click_btn_by_id('ConfigReboot')
                break
            else:
                time.sleep(3)
        # 判断是否处于重启等待页面
        for i in range(0, 50):
            if self.browser.is_exist_and_visible_ele_by_id('tShowForAutoP'):
                aklog_info(self.device_name_log + 'reboot processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break
        # 判断是否返回升级高级页面
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('ImportConfig'):
                aklog_info(self.device_name_log + '导入配置文完成')
                return True
            elif i == 0:
                aklog_info(self.device_name_log + '导入配置文件后无法再进入升级高级页面，重新登录')
                self.browser.screen_shot()
                self.retry_login()
        aklog_info(self.device_name_log + '导入配置文件失败，请检查原因')
        self.browser.screen_shot()
        return False

    def open_telnet_by_import_config(self):
        self.write_cfg_items_to_import_file('Config.Settings.OTHERS.Telnet = 1')
        self.import_config_file()

    def get_selected_log_level(self):
        """获取当前选择的log等级"""
        aklog_info(self.device_name_log + 'get_selected_log_level')
        self.enter_upgrade_advanced()
        return self.get_selected_option_by_name_web_v1v2('cSystemLogLevel')

    def set_syslog_level(self, level):
        self.enter_upgrade_advanced()
        self.select_option_value_by_id_web_v1v2('cSystemLogLevel', str(level))
        time.sleep(1)

    def edit_upgrade_log_level7(self):
        """网页upgrade高级界面修改log等级为7"""
        aklog_info(self.device_name_log + 'edit_upgrade_log_level7')
        self.enter_upgrade_advanced()
        self.select_option_value_by_id_web_v1v2('cSystemLogLevel', '7')
        time.sleep(1)

    def set_log_level7_on_hidden_page(self):
        aklog_info(self.device_name_log + 'set_log_level7_on_hidden_page')
        self.browser.visit_url('http://%s/fcgi/do?id=6&id=3' % self.device_ip)
        self.menu_expand_and_click(self.web_element_info['upgrade_menu'],
                                   self.web_element_info['upgrade_basic_submenu'])
        self.browser.select_option_value_by_name('cSystemLogLevel', '7')
        time.sleep(1)
        self.browser.visit_url('http://%s/fcgi/do?id=1' % self.device_ip)
        time.sleep(1)

    def enable_Remote_System_Log(self):
        """开启远程log"""
        aklog_info(self.device_name_log + '开启远程log')
        self.enter_upgrade_advanced()
        self.select_option_value_by_id_web_v1v2('cRemoteSystemLog', '1')
        self.browser.input_edit_by_id('cRemoteSystemServer', self.device_config.get_server_address())
        self.click_submit()

    def disable_Remote_System_Log(self):
        """关闭远程log"""
        aklog_info(self.device_name_log + '关闭远程log')
        self.enter_upgrade_advanced()
        self.select_option_value_by_id_web_v1v2('cRemoteSystemLog', '0')
        self.click_submit()

    def get_selected_remote_syslog(self):
        self.enter_upgrade_advanced()
        return self.get_selected_option_by_name_web_v1v2('cRemoteSystemLog')

    def get_syslog_export_btn_status(self):
        self.enter_upgrade_advanced()
        return self.browser.get_ele_status_by_id('BtnExportLog')

    def get_remote_syslog_edit_status(self):
        self.enter_upgrade_advanced()
        return self.browser.get_ele_status_by_id('cRemoteSystemServer')

    def export_system_log(self):
        """导出system log文件"""
        aklog_info(self.device_name_log + '导出system log文件')
        if not self.login_status:
            return False
        export_system_log_file = self.device_config.get_chrome_download_dir() + 'PhoneLog.tgz'
        export_system_log_file2 = self.device_config.get_chrome_download_dir() + 'Log.tgz'
        File_process.remove_file(export_system_log_file)  # 先删除下载目录下的PhoneLog.tgz文件
        File_process.remove_file(export_system_log_file2)  # 先删除下载目录下的PhoneLog.tgz文件
        self.enter_upgrade_advanced()
        self.browser.click_btn_by_id('BtnExportLog')
        time.sleep(5)
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not (os.path.exists(export_system_log_file) or os.path.exists(export_system_log_file2)):
                aklog_info(self.device_name_log + 'system log文件导出中...')
                time.sleep(3)
            else:
                aklog_info(self.device_name_log + 'system log文件导出成功')
                time.sleep(3)
                return True
        aklog_info(self.device_name_log + 'system log文件导出导出失败')
        self.browser.screen_shot()
        return False

    def export_syslog_to_results_dir(self, case_name):
        """网页导出syslog并保存到Results目录下"""
        if not self.login_status:
            return False
        if hasattr(self, 'api_hangup'):
            self.api_hangup()
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file = '{}\\PhoneLog--{}--{}--{}.tgz'.format(log_dir, case_name, self.device_name, log_time)
        File_process.create_dir(log_dir)
        export_system_log_file = self.device_config.get_chrome_download_dir() + 'PhoneLog.tgz'
        export_system_log_file2 = self.device_config.get_chrome_download_dir() + 'Log.tgz'
        self.export_system_log()
        if os.path.exists(export_system_log_file):
            File_process.copy_file(export_system_log_file, log_file)  # 将log文件保存到Results目录下
        if os.path.exists(export_system_log_file2):
            File_process.copy_file(export_system_log_file2, log_file)  # 将log文件保存到Results目录下

    def save_pcap_to_results_dir(self, case_name):
        """保存PCAP文件到Results目录下"""
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        pcap_file = '{}\\PhonePcap--{}--{}--{}.pcap'.format(log_dir, case_name, self.device_name, log_time)
        File_process.create_dir(log_dir)
        export_pcap_file = self.device_config.get_export_pcap_file()
        File_process.copy_file(export_pcap_file, pcap_file)

    def start_pcap(self, specify_port=''):
        """开始网页抓包start_pcap"""
        aklog_info(self.device_name_log + '开始网页抓包start_pcap')
        self.enter_upgrade_advanced()
        if specify_port is None:
            # 保持原默认功能基础上, 增加清空端口号功能
            self.input_edit_and_sleep_by_id(self.web_element_info['upgrade_pcap_specific_port_edit'], '')
            self.click_submit()
        else:
            # 增加指定端口号抓包功能，默认将端口清空 -- 2021.11.8
            cur_port = self.browser.get_attribute_value_by_id(self.web_element_info['upgrade_pcap_specific_port_edit'])
            if cur_port != specify_port:
                self.input_edit_and_sleep_by_id(self.web_element_info['upgrade_pcap_specific_port_edit'],
                                                str(specify_port))
                self.click_submit()
        self.browser.click_btn_by_id('StartPCAP')
        time.sleep(2)
        self.browser.alert_confirm_accept()

    def stop_pcap(self):
        """停止网页抓包stop_pcap"""
        aklog_info(self.device_name_log + '停止网页抓包stop_pcap')
        self.enter_upgrade_advanced()
        # self.browser.alert_confirm_accept()
        self.browser.click_btn_by_id('StopPCAP')
        time.sleep(2)
        self.browser.alert_confirm_accept()

    def export_pcap(self):
        """导出pcap文件"""
        aklog_info(self.device_name_log + '导出pcap文件')
        export_pcap = self.device_config.get_export_pcap_file()
        File_process.remove_file(export_pcap)  # 先删除下载目录下的PhoneLog.tgz文件
        self.enter_upgrade_advanced()
        if not self.is_exist('ExportPCAP'):
            if hasattr(self, 'web_enter_system_maintenance'):
                self.web_enter_system_maintenance()
        self.browser.click_btn_by_id('ExportPCAP')
        aklog_info(self.device_name_log + '导出pcap文件')
        time.sleep(10)
        # self.download_save()
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not os.path.exists(export_pcap):
                aklog_debug(self.device_name_log + 'pcap文件导出中...')
                time.sleep(3)
            else:
                aklog_info(self.device_name_log + '导出pcap文件成功')
                time.sleep(3)
                return True
        aklog_error(self.device_name_log + 'pcap文件导出导出失败')
        self.browser.screen_shot()
        return False

    def stop_and_export_pcap(self):
        self.stop_pcap()
        self.export_pcap()

    def get_pcap_file(self):
        """返回导出的pcap文件路径"""
        aklog_info()
        return self.device_config.get_chrome_download_dir() + 'phone.pcap'

    def web_set_pcap_port(self, pcap_port):
        """网页设置PCAP的端口"""
        self.enter_upgrade_advanced()
        if not self.is_exist('StartPCAP'):
            if hasattr(self, 'web_enter_system_maintenance'):
                self.web_enter_system_maintenance()
        self.input_edit_and_sleep_by_id(self.web_element_info['upgrade_pcap_specific_port_edit'], pcap_port)
        self.click_submit()

    def select_pcap_auto_refresh(self, value='0'):
        self.select_option_value_by_id_web_v1v2('cPCAPEnableRefresh', str(value))
        self.wait_process_finished()

    def judge_is_pcap_port_valid(self, port):
        """封装功能:  输入端口号, 并提交. 之后判断输入的pcap端口号是否合法"""
        self.enter_upgrade_advanced()
        self.input_edit_and_sleep_by_id(self.web_element_info['upgrade_pcap_specific_port_edit'], str(port))
        self.click_submit()
        time.sleep(2)
        self.wait_process_finished()
        submit_text = self.get_value_and_sleep_by_id('WarningDiv')
        if type(port) == int and int(port) in range(1, 65536):
            return '' == submit_text
        return "Please check your data in pink, it may contain invalid characters (&,%,',=) or " \
               "its data range is wrong" == submit_text

    def click_pcap_btn(self, btn):
        """
        封装功能: 点击pcap的几个按钮
        btn: Start, Stop, Export
        """
        btn_dict = {
            'Start': 'StartPCAP',
            'Stop': 'StopPCAP',
            'Export': 'ExportPCAP'
        }
        self.click_btn_and_sleep_by_id(btn_dict[btn])

    def get_pcap_btn_status(self, btn):
        """
        封装功能: 获取pcap按钮 是否可编辑状态
        """
        btn_dict = {
            'Start': 'StartPCAP',
            'Stop': 'StopPCAP',
            'Export': 'ExportPCAP'
        }
        return self.browser.get_id_status(btn_dict[btn])

    def wait_pcap_over_size(self, timeout=300):
        """等待PCAP抓包超出大小"""
        counts = int(round(timeout / 5, 0))
        for i in range(counts):
            alert_text = self.browser.get_alert_text()
            if alert_text:
                self.browser.alert_confirm_accept()
                if not self.browser.get_ele_status_by_id('StopPCAP'):
                    return alert_text
                else:
                    aklog_info(self.device_name_log + '没有自动停止抓包')
                    return False
            else:
                time.sleep(5)
                continue
        aklog_info(self.device_name_log + '没有提示超过大小')
        return False

    # </editor-fold>

    # <editor-fold desc="Security Basic页面相关">
    def enter_security_basic(self):
        aklog_info(self.device_name_log + 'enter_security_basic')
        self.menu_expand_and_click(self.web_element_info['security_menu'],
                                   self.web_element_info['security_basic_submenu'])

    def web_pwd_modify(self, current_pwd, new_pwd):
        """网页修改登录密码"""
        aklog_info(
            self.device_name_log + 'web_pwd_modify, current_pwd: %s, new_pwd: %s' % (current_pwd, new_pwd))
        if current_pwd == new_pwd:
            aklog_info(self.device_name_log + 'current_pwd = new_pwd, not need modify')
            return True
        else:
            for i in range(2):
                self.enter_security_basic()
                if not self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['logout']):
                    self.retry_login()
                    continue
                else:
                    if self.web_admin_pwd == new_pwd:
                        aklog_info(self.device_name_log + 'Password has been changed')
                        return True
                    else:
                        break
            if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['security_change_pwd_btn_id']):
                self.select_option_value_by_name_web_v1v2('cUserName', self.web_admin_username)
                self.browser.click_btn_by_id(self.web_element_info['security_change_pwd_btn_id'])
                self.browser.input_edit_by_id(self.web_element_info['security_modifymage_oldpwd'], current_pwd)
                self.browser.input_edit_by_id(self.web_element_info['security_modifymage_newpwd'], new_pwd)
                self.browser.input_edit_by_id(self.web_element_info['security_modifymage_confirmpwd'], new_pwd)
                self.browser.click_btn_by_id(self.web_element_info['security_modifymage_change_btn'])
                self.browser.alert_confirm_accept()
                time.sleep(1)
                self.browser.web_refresh()
            elif 'security_change_pwd_btn_id_V6' in self.web_element_info and \
                    self.browser.is_exist_and_visible_ele_by_id(
                        self.web_element_info['security_change_pwd_btn_id_V6']):
                self.select_option_value_by_name_web_v1v2('cUserName', self.web_admin_username)
                self.browser.click_btn_by_id(self.web_element_info['security_change_pwd_btn_id_V6'])
                self.browser.input_edit_by_id(self.web_element_info['security_modifymage_oldpwd_V6'], current_pwd)
                self.browser.input_edit_by_id(self.web_element_info['security_modifymage_newpwd_V6'], new_pwd)
                self.browser.input_edit_by_id(self.web_element_info['security_modifymage_confirmpwd_V6'], new_pwd)
                self.browser.click_btn_by_id(self.web_element_info['security_modifymage_change_btn_V6'])
                self.browser.alert_confirm_accept()
                time.sleep(1)
                self.browser.web_refresh()
            else:
                self.select_option_value_by_name_web_v1v2('cUserName', self.web_admin_username)
                self.browser.input_edit_by_name('cCurrentPasswd', current_pwd)
                self.browser.input_edit_by_name('cNewPasswd', new_pwd)
                self.browser.input_edit_by_name('cConfirmPasswd', new_pwd)
                self.click_submit()
                time.sleep(1)
            # 登出网页，用新密码再重新登录
            self.web_admin_pwd = new_pwd
            if self.retry_login():
                return True
            else:
                self.web_admin_pwd = current_pwd
                aklog_info(self.device_name_log + 'modify pwd failed')
                self.browser.screen_shot()
                self.retry_login()
                return False

    def set_web_session_time_out(self, time_out):
        aklog_info(self.device_name_log + 'set_web_session_time_out, time_out: %s' % time_out)
        self.enter_security_basic()
        self.input_edit_and_sleep_by_id("cSessionTimeOutValue", time_out)
        self.click_submit()

    def get_web_session_time_out_value(self):
        """获取网页session time out时间"""
        self.enter_security_basic()
        return self.browser.get_attribute_value_by_id(self.web_element_info['security_session_time_out_value'])

    # </editor-fold>

    # <editor-fold desc="Security Advanced页面相关">
    def enter_security_advanced(self):
        aklog_info(self.device_name_log + 'enter_security_advanced')
        self.menu_expand_and_click(self.web_element_info['security_menu'],
                                   self.web_element_info['security_advanced_submenu'])

    def client_certificate_upload(self, cert_file=None):
        """上传Client Certificate"""
        if not cert_file:
            cert_file = self.device_config.get_client_certificate_pem_file_path()
        self.browser.upload_file_by_id(self.web_element_info['FPhoneCert'], cert_file)
        self.click_btn_and_sleep_by_id(self.web_element_info['PhoneCert_submit'])
        time.sleep(2)
        # self.alert_confirm_accept_and_sleep()
        for i in range(10):
            if self.browser.is_exist_alert():
                self.alert_confirm_accept_and_sleep()
                break
        time.sleep(2)
        if self.judge_is_exist_client_certificate():
            aklog_info("client certificate导入成功")
            return True
        else:
            aklog_info("client certificate导入失败")
            return False

    def judge_is_exist_client_certificate(self):
        """判断是否存在客户端证书"""
        self.enter_security_advanced()
        if self.browser.get_id_status(self.web_element_info['PhoneCert_deleteall']):
            return True
        else:
            return False

    def no_select_client_certificate_file_click_submit(self):
        """未选择文件直接点击上传"""
        self.click_btn_and_sleep_by_id(self.web_element_info['PhoneCert_submit'], 2)
        alert_text = self.browser.get_alert_text(2)
        self.alert_confirm_accept_and_sleep()
        return alert_text

    def upload_error_client_certificate_file(self):
        """导入错误client_certificate_file文件"""
        self.browser.upload_file_by_id(self.web_element_info['FPhoneCert'],
                                       self.device_config.get_error_client_certificate_file_path())
        self.click_btn_and_sleep_by_id(self.web_element_info['PhoneCert_submit'], 3)
        alert_text = self.browser.get_alert_text(3)
        self.alert_confirm_accept_and_sleep()
        return alert_text

    def upload_client_certificate_pem_return_filename(self):
        """选中client_certificate文件后返回被选中的文件名"""
        self.browser.upload_file_by_id(self.web_element_info['FPhoneCert'],
                                       self.device_config.get_client_certificate_pem_file_path())
        filename = self.browser.get_value_by_id(self.web_element_info['PhoneCert_inputFileText1'])
        return filename

    def client_certificate_upload_return_filename(self):
        """返回client_certificate导入界面的文件选择框中的内容"""
        filename = self.browser.get_value_by_id(self.web_element_info['PhoneCert_inputFileText1'])
        return filename

    def client_certificate_upload_and_click_cancel(self):
        """client_certificate导入,点击界面的cancel按钮"""
        self.browser.upload_file_by_id(self.web_element_info['FPhoneCert'],
                                       self.device_config.get_client_certificate_pem_file_path())
        self.browser.click_btn_by_id(self.web_element_info['PhoneCert_cancel'])

    def upload_client_certificate_select_index(self, index='Auto'):
        """选择index上传证书文件"""
        self.select_option_by_name_web_v1v2(self.web_element_info['Client_Cert_IndexSelect'], index)

    def delete_all_client_certificate(self):
        """删除所有的 client证书文件"""
        if self.judge_is_exist_client_certificate():
            self.click_btn_and_sleep_by_id(self.web_element_info['PhoneCert_deleteall'])
            self.alert_confirm_accept_and_sleep(2)
        else:
            aklog_info('There is no client certificate')

    def judge_is_index_exist_client_certificate(self, index):
        """判断哪一行是否存在证书文件"""
        index_id = re.sub(r'\d', str(index - 1), self.web_element_info['PhoneCert_CheckPCert0'])
        if self.judge_is_exist_client_certificate() and self.browser.get_id_status(index_id):
            return True
        else:
            aklog_info('The index  is no client certificate')
            return False

    def web_select_client_certificate_index_and_delete(self, index):
        """网页选择client_certificate列表并点击删除按钮"""
        index_id = re.sub(r'\d', str(index - 1), self.web_element_info['PhoneCert_CheckPCert0'])
        self.check_box_and_sleep_by_id(index_id)
        self.click_btn_and_sleep_by_id(self.web_element_info['PhoneCert_delete'], 2)

    def select_Only_Accept_Trusted_disabled(self):
        """OnlyAcceptTrusted设置为disabled"""
        self.enter_security_advanced()
        self.select_option_value_by_name_web_v1v2(self.web_element_info['OnlyAcceptTrusted'],
                                                  self.web_element_info['option_value_Disabled'])
        self.click_btn_and_sleep_by_id(self.web_element_info['OnlyAcceptTrusted_PageSubmit2'])
        alert_text = self.browser.get_alert_text()
        self.alert_confirm_accept_and_sleep()
        return alert_text

    def select_Only_Accept_Trusted_enabled(self):
        """OnlyAcceptTrusted设置为enabled"""
        self.enter_security_advanced()
        self.select_option_value_by_name_web_v1v2(self.web_element_info['OnlyAcceptTrusted'],
                                                  self.web_element_info['option_value_Enabled'])
        self.click_btn_and_sleep_by_id(self.web_element_info['OnlyAcceptTrusted_PageSubmit2'])
        alert_text = self.browser.get_alert_text()
        self.alert_confirm_accept_and_sleep()
        return alert_text

    def get_Only_Accept_Trusted_config(self):
        """获取_Only_Accept_Trusted的配置信息"""
        self.enter_security_advanced()
        return self.get_selected_option_by_name_web_v1v2(self.web_element_info['OnlyAcceptTrusted'])

    def get_CertIssuedBy_name(self):
        """获取web CertIssuedBy name"""
        return self.get_value_and_sleep_by_id(self.web_element_info['CertIssuedBy'])

    def web_server_certificate_upload(self, cert_file=None):
        """上传web server Certificate"""
        if not cert_file:
            cert_file = self.device_config.get_client_certificate_pem_file_path()
        self.browser.upload_file_by_id(self.web_element_info['WebCert_select'],
                                       cert_file)
        self.click_btn_and_sleep_by_id(self.web_element_info['Webcert_submit'])
        time.sleep(2)
        self.alert_confirm_accept_and_sleep()
        for i in range(10):
            if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['PhoneUsingStatus']):
                aklog_info('[' + self.device_name + '] ' + 'reboot processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break
        if self.judge_is_exist_web_server_certificate():
            aklog_info("web sever certificate导入成功")
            return True
        else:
            aklog_info("web sever certificate导入失败")
            return False

    def judge_is_exist_web_server_certificate(self):
        """判断是否存在网页端证书"""
        self.enter_security_advanced()
        if self.browser.get_id_status(self.web_element_info['webcert_delete']):
            return True
        else:
            return False

    def no_select_web_server_certificate_file_click_submit(self):
        """未选择文件直接点击上传"""
        self.click_btn_and_sleep_by_id(self.web_element_info['Webcert_submit'], 2)
        alert_text = self.browser.get_alert_text(2)
        self.alert_confirm_accept_and_sleep()
        return alert_text

    def upload_error_web_server_certificate_file(self):
        """导入错误web_server_certificate_file文件"""
        self.browser.upload_file_by_id(self.web_element_info['WebCert_select'],
                                       self.device_config.get_error_client_certificate_file_path())
        self.click_btn_and_sleep_by_id(self.web_element_info['Webcert_submit'])
        self.alert_confirm_accept_and_sleep()
        alert_text = self.web_get_alert_text_and_confirm(10)
        return alert_text

    def upload_error_web_server_certificate(self, file_suffix):
        """导入错误web_server_certificate_file文件"""
        self.browser.upload_file_by_id(self.web_element_info['WebCert_select'],
                                       self.device_config.get_web_cert_import_file('wrong.%s' % file_suffix))
        self.click_btn_and_sleep_by_id(self.web_element_info['Webcert_submit'], 3)
        alert_text = self.browser.get_alert_text(3)
        self.alert_confirm_accept_and_sleep()
        return alert_text

    def web_server_certificate_upload_and_click_cancel(self):
        """web_server_certificate导入,点击界面的cancel按钮"""
        self.browser.upload_file_by_id(self.web_element_info['WebCert_select'],
                                       self.device_config.get_client_certificate_pem_file_path())
        self.browser.click_btn_by_id(self.web_element_info['webcert_cancel'])

    def delete_web_server_certificate(self):
        """删除所有的 client证书文件"""
        if self.judge_is_exist_web_server_certificate():
            self.click_btn_and_sleep_by_id(self.web_element_info['webcert_delete'])
            self.alert_confirm_accept_and_sleep(2)
        else:
            aklog_info('There is no web server certificate')

    # </editor-fold>

    # <editor-fold desc="隐藏页面相关">
    def enter_test_page(self):
        # linux室内机登入web UI自动化测试界面
        url = 'http://%s/fcgi/do?id=8849' % self.device_ip
        self.browser.visit_url(url)
        if self.browser.is_exist_ele_by_id(self.web_element_info['logout']):
            aklog_info(self.device_name_log + '正常进入测试界面')
            return True
        else:
            aklog_info(self.device_name_log + '没有正常进入测试界面')
            self.browser.screen_shot()
            ret = self.retry_login()
            return ret

    def enter_hide_page_8848(self):
        """进入隐藏页面"""
        url = 'http://%s/fcgi/do?id=8848' % self.device_ip
        aklog_info(self.device_name_log + '打开页面: %s' % url)
        for i in range(2):
            self.browser.visit_url(url)
            if self.browser.get_value_by_id('tInnerTitle') != 'Internal Hidden Page':
                if i < 1:
                    self.retry_login()
                    continue
                else:
                    aklog_info(self.device_name_log + '进入8848隐藏页面失败')
                    self.screen_shot()
                    return False
            else:
                return True

    def set_ssh_or_tln(self, option_value):
        aklog_info(self.device_name_log + 'set_ssh_or_tln %s' % option_value)
        self.select_option_value_by_name_web_v1v2('cTelnetActive', option_value)
        self.click_submit()
        tln_or_ssh_status = self.get_selected_option_by_name_web_v1v2('cTelnetActive')
        if tln_or_ssh_status == 'Enabled':
            return True
        else:
            return False

    def web_open_ssh(self):
        """设备网页打开的ssh操作"""
        self.enter_hide_page_8848()
        result = self.set_ssh_or_tln('1')
        self.enter_status_basic()
        time.sleep(5)
        return result

    def set_product_mode(self, option_value):
        aklog_info(self.device_name_log + 'set_product_mode %s' % option_value)
        self.enter_hide_page_8848()
        self.select_option_value_by_name_web_v1v2('cProductModeActive', option_value)
        self.click_submit()

    def web_ping_network(self, host):
        """网页8848隐藏页面ping操作"""
        self.browser.input_edit_by_id('cPingIpAddress', host)
        self.browser.click_btn_by_id('cStartPing')
        if self.is_exist_warning_text():
            return None
        time.sleep(10)
        result = ''
        for i in range(10):
            result = self.browser.get_value_by_id('cPingResult')
            if not result:
                aklog_info('ping结果还未出来，继续等待...')
                time.sleep(3)
                continue
            time.sleep(3)
            result1 = self.browser.get_value_by_id('cPingResult')
            if result1 == result:
                break
            elif i == 9:
                aklog_info('ping没有结果')
                self.browser.screen_shot()
                break
            else:
                time.sleep(3)
                continue
        return result

    def get_web_ping_address_edit(self):
        return self.browser.get_attribute_value_by_id('cPingIpAddress')

    def get_web_web_ping_result(self):
        return self.browser.get_value_by_id('cPingResult')

    # </editor-fold>

    # <editor-fold desc="下载页面相关">
    def download_save(self):
        """有些文件（比如cfg）会被chrome浏览器当成危险文件，警告提示是否保留或放弃，则需要进入下载页面强制点保留下载
        chrome新版本该方法不适用，修改browser初始化参数方法解决了危险文件问题"""
        aklog_info(self.device_name_log + 'download_save, skip')
        # aklog_info(self.device_name_log + '进入下载页面点击保留')
        # self.browser.new_window()
        # self.browser.switch_window(1)
        # self.browser.visit_url('chrome://downloads')
        # self.browser.set_implicitly_wait(10)
        # self.browser.click_btn_by_css_selector('downloads-manager /deep/ downloads-item /deep/ [id=save]')
        # self.browser.restore_implicitly_wait()
        # self.browser.alert_confirm_accept()
        # self.browser.click_btn_by_css_selector('downloads-manager /deep/ downloads-item /deep/ [id=remove]')
        # self.browser.close_window()
        # self.browser.switch_window(0)

    def clear_browser_cache_data(self):
        self.browser.new_window()
        self.browser.switch_window(1)
        self.browser.visit_url('chrome://settings/clearBrowserData')
        self.browser.select_option_value_by_css_selector('settings-ui/deep/settings-basic-page/deep/'
                                                         'settings-clear-browsing-data-dialog-tabs/deep/'
                                                         '[id=dropdownMenu]', '4')
        self.browser.set_implicitly_wait(10)
        self.browser.click_btn_by_css_selector('settings-ui/deep/settings-basic-page/deep/'
                                               'settings-clear-browsing-data-dialog-tabs/deep/'
                                               '[id=clearBrowsingDataConfirm]')
        self.browser.restore_implicitly_wait()
        self.browser.close_window()
        self.browser.switch_window(0)

    # </editor-fold>

    # <editor-fold desc="Account Basic相关">
    def enter_web_account_basic(self):
        aklog_info(self.device_name_log + 'enter_web_account_basic')
        self.menu_expand_and_click(self.web_element_info['account'], self.web_element_info['account_basic'])

    def select_account_by_index(self, account=1):
        """
        传入: 1, 2
        或者 '0', '1'  # 原用法
        """
        if type(account) == int:
            account = int(account) - 1
        elif type(account) == str and account.isdigit():
            account = int(account)
        self.write_config('cCurAccount', account)

    def click_account(self):
        # 点击Account
        self.browser.click_btn_by_id(self.web_element_info['account'])
        time.sleep(2)

    def click_account_basic(self):
        # 点击Account Basic
        self.menu_expand_and_click(self.web_element_info['account'], self.web_element_info['account_basic'])

    def get_account_label_value(self):
        """获取Account的label值"""
        aklog_info(self.device_name_log + '获取Account的label值')
        time.sleep(5)  # 网页设计要实时去获取当前账号状态，所以那边会稍微等点时间
        value = self.browser.get_attribute_value_by_id('cDisplayLabel')
        return value

    def get_sip_account_label(self, account=None):
        """获取account label"""
        self.enter_web_account_basic()
        if account is not None:
            self.select_option_value_by_name_web_v1v2('cCurAccount', str(int(account) - 1))
        return self.browser.get_attribute_value_by_id('cDisplayLabel')

    def get_account_username_value(self):
        """获取Account的username值"""
        aklog_info(self.device_name_log + '获取Account的username值')
        time.sleep(5)  # 网页设计要实时去获取当前账号状态，所以那边会稍微等点时间
        value = self.browser.get_attribute_value_by_id('cUserName')
        return value

    def get_account_status_value(self, wait_time=3):
        # 获取AccountStatus的值
        time.sleep(wait_time)  # 网页设计要实时去获取当前账号状态，所以那边会稍微等点时间
        tag_name = self.browser.get_tag_name_by_id("cAccountStatus")
        if tag_name == "label":
            status = self.browser.get_value_by_id("cAccountStatus")
        elif tag_name == 'input':
            status = self.browser.get_attribute_value_by_id("cAccountStatus")
        else:
            status = ''
        return status

    def get_account_sip_server_addr(self):
        # 获取AccountStatus的值
        time.sleep(5)  # 网页设计要实时去获取当前账号状态，所以那边会稍微等点时间
        value = self.browser.get_attribute_value_by_xpath('//*[@id="cFirstSIPServerAddr"]')
        return value

    def register_sip(self, sip, sip_password, server_ip, server_port='5060', account_active='1', index=None,
                     transport='UDP', wait_register=True, **kwargs):
        """
        话机注册sip号功能
        2021/6/8 不修改默认功能的情况下, 增加index, 指定注册账号几.
        kwargs: display_name=xxx, register_name=xxx, label=xxx
        """
        aklog_info(self.device_name_log + "register_sip, sip: %s, sip_password: %s, server_ip: %s, server_port: %s"
                   % (sip, sip_password, server_ip, server_port))

        label = kwargs.get('label') if kwargs.get('label') is not None else sip
        display_name = kwargs.get('display_name') if kwargs.get('display_name') is not None else sip
        register_name = kwargs.get('register_name') if kwargs.get('register_name') is not None else sip

        self.enter_web_account_basic()
        time.sleep(0.2)
        if index:
            self.select_option_value_by_name_web_v1v2('cCurAccount', str(int(index) - 1))
            self.wait_process_finished()  # 出现接口切换账号后, 实际上账号开门未能修改成功.
        self.write_config('cAccountActive', account_active)
        self.browser.input_edit_by_id('cDisplayLabel', label)
        self.browser.input_edit_by_id('cRegisterName', display_name)
        self.browser.input_edit_by_id('cDisplayName', register_name)
        self.browser.input_edit_by_id('cUserName', sip)
        if not self.browser.input_edit_by_id('cPassword', sip_password):
            self.browser.input_edit_by_id('cAccountPwd', sip_password)
        self.browser.input_edit_by_id('cFirstSIPServerAddr', server_ip)
        self.browser.input_edit_by_id('cFirstSIPServerPort', server_port)
        if transport:
            transport_dict = {'UDP': '0', 'TCP': '1', 'TLS': '2', 'DNS-SRV': '3'}
            self.select_option_value_by_name_web_v1v2('cAccountTransType', transport_dict.get(transport))
        self.click_submit()
        if account_active == '1' and wait_register:
            return self.wait_for_account_to_register_successfully()

    def register_sip_with_device_info(self, account='1', **kwargs):
        """
        使用device info中的SIP帐号注册
        注意，device_info中的key值需要跟下面的一致
        account: 1 2 12
        kwargs: 比如：transport=TCP, display_name=xxx
        """
        if 'sip_server_port' not in self.device_info:
            sip_server_port = '5060'
        else:
            sip_server_port = self.device_info['sip_server_port']

        for x in str(account):
            if x == '1':
                self.register_sip(self.device_info['sip'],
                                  self.device_info['sip_password'],
                                  self.device_info['sip_server'],
                                  sip_server_port,
                                  index=1,
                                  **kwargs)
            elif x == '2':
                # 第二个SIP帐号注册到帐号2上
                self.register_sip(self.device_info['sip2'],
                                  self.device_info['sip2_password'],
                                  self.device_info['sip_server'],
                                  sip_server_port,
                                  index=2,
                                  **kwargs)

    def register_sip_with_device_info_to_elastix(self, **kwargs):
        """
        使用device info中的SIP帐号注册
        注意，device_info中的key值需要跟下面的一致
        """
        self.register_sip(self.device_info['sip_elastix'],
                          self.device_info['sip_password_elastix'],
                          self.device_info['sip_server_elastix'],
                          self.device_info['sip_server_port_elastix'],
                          **kwargs)

    def register_sip_with_device_info_to_sip_proxy(self, **kwargs):
        """把sip proxy当做SIP服务器，将帐号注册到该服务器"""
        server_ip = config_get_value_from_ini_file('environment', 'outbound_server_ip')
        server_port = config_get_value_from_ini_file('environment', 'outbound_server_port')
        self.register_sip(self.device_info['sip'],
                          self.device_info['sip_password'],
                          server_ip,
                          server_port,
                          **kwargs)

    def set_account_transport_type(self, transport_type, account='1'):
        """
        设置sip账号的传输方式
        :param transport_type:
        :param account: 1 - 2
        :return:
        """
        self.enter_web_account_basic()
        account = int(account) - 1
        self.select_option_value_by_name_web_v1v2('cCurAccount', account)
        time.sleep(2)
        self.select_option_by_name_web_v1v2('cAccountTransType', transport_type)
        self.click_submit()

    def modify_register_expire(self, expire):
        """"""
        aklog_info(self.device_name_log + 'modify_register_expire, expire: %s' % expire)
        if 30 <= int(expire) <= 65535:
            self.enter_web_account_basic()
            self.browser.input_edit_by_id('cFirstRegisterExpire', expire)
            self.click_submit()
        else:
            aklog_info(self.device_name_log + 'expire超出范围')

    def wait_for_account_to_register_successfully(self, failure_to_wait_time=15):
        """
        等待帐号注册, failure_to_wait_time为显示注册失败后再继续等待的时间
        """
        aklog_info(self.device_name_log + 'wait_for_account_to_register_successfully')
        self.enter_web_account_basic()
        i = 0
        while i < 30 + int(failure_to_wait_time / 5):
            self.browser.web_refresh()
            account_status = self.get_account_status_value(0)
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
        aklog_error(self.device_name_log + 'sip account register failed')
        return False

    def enabled_account(self, index=1):
        self.enter_web_account_basic()
        self.select_account_by_index(index)
        self.write_config('cAccountActive', 1)
        self.click_submit()

    def disabled_account(self, index=1):
        self.enter_web_account_basic()
        self.select_account_by_index(index)
        self.write_config('cAccountActive', 0)
        self.click_submit()

    def unregister_sip_account(self, accounts=1, all=False):
        """
        注销sip账号. 不影响默认功能下, 增加注销所有账号参数: all.
        """
        if type(accounts) == bool:
            all = accounts

        def test():
            self.select_option_value_by_name_web_v1v2('cAccountActive', '0')
            self.click_submit()

        aklog_info(self.device_name_log + 'unregister_sip_account')
        self.enter_web_account_basic()
        if all:
            account_list = self.get_select_options_list_by_id("cCurAccount")
            for acc in account_list:
                self.write_config('cCurAccount', acc)
                self.wait_process_finished()
                test()
            self.write_config('cCurAccount', account_list[0])
        else:
            if not type(accounts) == bool:
                self.select_option_value_by_name_web_v1v2('cCurAccount', str(int(accounts) - 1))
            test()

    def clear_web_account(self, accounts='1'):
        """
        网页清除账号配置为默认配置
        :param accounts: '1', '2', '12'
        :return:
        """
        aklog_info(self.device_name_log + 'clear_web_account')
        self.enter_web_account_basic()
        for account in str(accounts):
            self.select_option_value_by_name_web_v1v2('cCurAccount', str(int(account) - 1))
            time.sleep(1)
            self.write_config('cAccountActive', '0')
            self.browser.input_edit_by_id('cDisplayLabel', '')
            self.browser.input_edit_by_id('cRegisterName', '')
            self.browser.input_edit_by_id('cDisplayName', '')
            self.browser.input_edit_by_id('cUserName', '')
            self.write_config('//*[@id="cPassword" or @id="cAccountPwd"]', '')
            self.browser.input_edit_by_id('cFirstSIPServerAddr', '')
            self.browser.input_edit_by_id('cFirstSIPServerPort', '5060')
            self.select_option_value_by_name_web_v1v2('cAccountTransType', '0')
            self.write_config('cEnableOutbond', 0)
            self.write_config('cEnableStun', 0)
            self.browser.click_btn_by_id("PageSubmit")

    def judge_cloudconnect_status(self):
        """判断设备连接云的状态"""
        self.enter_web_account_basic()
        status = self.get_account_status_value()
        return status

    def get_account_trans_type(self):
        """获取SIP传输类型"""
        aklog_info(self.device_name_log + 'get_account_trans_type')
        self.enter_web_account_basic()
        trans_type = self.get_selected_option_by_name_web_v1v2(self.web_element_info['account_trans_type_name'])
        return trans_type

    def get_account_register_status(self, account=None):
        aklog_info(self.device_name_log + 'get_account_register_status')
        self.enter_web_account_basic()
        if account is not None:
            self.select_option_value_by_name_web_v1v2('cCurAccount', str(int(account) - 1))
            time.sleep(1)
        register_status = self.get_account_status_value()
        return register_status

    def get_location(self):
        """获取帐号DisplayName，该方法主要是给云平台下发注册帐号，DisplayName显示的是设备的location"""
        aklog_info(self.device_name_log + "get_location")
        self.enter_web_account_basic()
        location = self.browser.get_attribute_value_by_id('cDisplayName')
        return location

    def set_outbound_server(self, status, server1, server1_port, server2=None, server2_port=None, index=1):
        """网页设置outbound主次服务器地址"""
        self.enter_web_account_basic()
        self.select_option_value_by_name_web_v1v2('cCurAccount', int(index) - 1)
        time.sleep(1)
        self.select_option_value_by_name_web_v1v2('cEnableOutbond', status)
        self.browser.input_edit_by_name('cOutbondProxyAddr', server1)
        self.browser.input_edit_by_name('cOutbondProxyPort', server1_port)
        if server2 is not None:
            self.browser.input_edit_by_name('cBakProxyAddr', server2)
        if server2_port is not None:
            self.browser.input_edit_by_name('cBakProxyPort', server2_port)
        self.click_submit()

    def clear_outbound_server(self, accounts='1'):
        """
        清空outbound配置
        :param accounts: '1', '2', '12'
        :return:
        """
        self.enter_web_account_basic()
        for account in accounts:
            self.select_option_value_by_name_web_v1v2('cCurAccount', account)
            time.sleep(1)
            self.select_option_value_by_name_web_v1v2('cEnableOutbond', '0')
            self.browser.input_edit_by_name('cOutbondProxyAddr', '')
            self.browser.input_edit_by_name('cOutbondProxyPort', '5060')
            self.browser.input_edit_by_name('cBakProxyAddr', '')
            self.browser.input_edit_by_name('cBakProxyPort', '5060')
            self.click_submit()

    # </editor-fold>

    # <editor-fold desc="Account Advanced相关">
    def enter_account_advanced(self):
        aklog_info(self.device_name_log + 'enter_account_advanced')
        self.menu_expand_and_click(self.web_element_info['account'], self.web_element_info['account_advanced'])

    def select_sipHacking(self, status, account='1'):
        # 选择sipHacking的状态
        aklog_info()
        self.enter_account_advanced()
        time.sleep(0.2)
        self.select_option_value_by_name_web_v1v2(self.web_element_info['sip_account_choice'], str(int(account) - 1))
        time.sleep(2)
        self.select_option_by_name_web_v1v2('cPreventSIPHacking', status)
        # self.browser.click_btn_by_xpath('//*[@id="AccountA_trPreventSIPHacking"]/div/input[1]')
        # if status == 'Enabled':
        #     self.browser.click_btn_by_xpath('//*[@id="AccountA_trPreventSIPHacking"]/div/div/ul/li[2]')
        # elif status == 'Disabled':
        #     self.browser.click_btn_by_xpath('//*[@id="AccountA_trPreventSIPHacking"]/div/div/ul/li[1]')
        self.click_submit()

    def enable_auto_answer(self, enable='1'):
        # 网页账号高级开启自动应答
        self.enter_account_advanced()
        self.select_option_value_by_name_web_v1v2('cAutoAnswer', enable)
        self.click_submit()

    def disable_auto_answer(self):
        # 网页账号高级关闭自动应答
        self.enter_account_advanced()
        self.select_option_value_by_name_web_v1v2('cAutoAnswer', '0')
        self.click_submit()

    def enable_rport(self):
        # 网页账号高级开启rport
        self.enter_account_advanced()
        self.select_option_value_by_name_web_v1v2('cRPort', '1')
        self.click_submit()

    def disable_rport(self):
        # 网页账号高级关闭rport
        self.enter_account_advanced()
        self.select_option_value_by_name_web_v1v2('cRPort', '0')
        self.click_submit()

    def click_account_advance(self):
        # 进入账号高级界面
        self.menu_expand_and_click(self.web_element_info['account'], self.web_element_info['account_advanced'])

    def get_enabled_audio_codec_list(self):
        """封装获取enabled codec 列表"""
        self.enter_account_advanced()
        return self.get_value_and_sleep_by_id('cEnableCodecs').split('\n')

    def get_disabled_audio_codec_list(self):
        """封装获取disabled codec列表"""
        self.enter_account_advanced()
        return self.get_value_and_sleep_by_id('cDisableCodecs').split('\n')

    def enable_audio_codec(self, codeclist: list, accept=False, reverse_order=True):
        """设置enabled codec里包含的code"""
        self.enter_account_advanced()
        codec_sel = self.browser.get_element_visible(By.NAME, 'cEnableCodecs')
        select = Select(codec_sel)
        select.deselect_all()
        for i in select.options:
            i.click()
        self.browser.driver.find_element('xpath', './/input[@value="<<"]').click()
        time.sleep(1)

        disabled_codec_sel = self.browser.get_element_visible(By.NAME, 'cDisableCodecs')
        select = Select(disabled_codec_sel)
        select.deselect_all()
        if not reverse_order:
            # Codec List要倒序选择，这样保存的codec顺序才会跟codeclist一致
            codeclist = codeclist[::-1]
        for codec in codeclist:
            select.select_by_visible_text(codec)
            self.browser.driver.find_element('xpath', './/input[@value=">>"]').click()
        self.click_submit(accept=accept)

    def enable_all_audio_codec(self):
        """封装开启所有的音频codec"""
        self.enter_account_advanced()
        codec_sel = self.browser.get_element_visible(By.NAME, 'cDisableCodecs')
        select = Select(codec_sel)
        select.deselect_all()
        for i in select.options:
            i.click()
        self.browser.driver.find_element('xpath', './/input[@value=">>"]').click()
        self.click_submit(accept=False)

    def move_audio_code_top(self, codec):
        """移动指定的codec的优先级为最高"""
        codec_sel = self.browser.get_element_visible(By.NAME, 'cEnableCodecs')
        select = Select(codec_sel)
        select.deselect_all()
        select.select_by_visible_text(codec)
        ele = self.browser.driver.find_element('xpath', './/input[@value="↑"]')
        for _ in range(5):
            ele.click()
        self.click_submit()

    def get_enabled_video_codec_list(self):
        """封装获取enabled video codec 列表"""
        self.enter_account_advanced()
        return self.get_value_and_sleep_by_id('cEnableVideoCodecs').split('\n')

    def get_disabled_video_codec_list(self):
        """封装获取disabled video codec 列表"""
        self.enter_account_advanced()
        return self.get_value_and_sleep_by_id('cDisableVideoCodecs').split('\n')

    def enable_video_codec(self, codeclist: list, accept=False, reverse_order=True):
        """设置enabled video codec里包含的codec"""
        self.enter_account_advanced()
        codec_sel = self.browser.get_element_visible(By.NAME, 'cEnableVideoCodecs')
        select = Select(codec_sel)
        select.deselect_all()
        for i in select.options:
            i.click()
        self.browser.driver.find_element('xpath', '//*[@id="AccountA_divVideoCodecs"]//input[@value="<<"]').click()
        time.sleep(1)

        disabled_codec_sel = self.browser.get_element_visible(By.NAME, 'cDisableVideoCodecs')
        select = Select(disabled_codec_sel)
        select.deselect_all()
        if not reverse_order:
            # Codec List要倒序选择，这样保存的codec顺序才会跟codeclist一致
            codeclist = codeclist[::-1]
        for codec in codeclist:
            select.select_by_visible_text(codec)
            self.browser.driver.find_element('xpath', '//*[@id="AccountA_divVideoCodecs"]//input[@value=">>"]').click()
        self.click_submit(accept=accept)

    def enable_all_video_codec(self, accept=False):
        """封装开启所有的video codec"""
        self.enter_account_advanced()
        codec_sel = self.browser.get_element_visible(By.NAME, 'cDisableVideoCodecs')
        select = Select(codec_sel)
        select.deselect_all()
        for i in select.options:
            i.click()
        self.browser.driver.find_element('xpath', '//*[@id="AccountA_divVideoCodecs"]//input[@value=">>"]').click()
        self.click_submit(accept=accept)

    def move_video_code_top(self, codec):
        """移动指定的codec的优先级为最高"""
        codec_sel = self.browser.get_element_visible(By.NAME, 'cEnableVideoCodecs')
        select = Select(codec_sel)
        select.deselect_all()
        select.select_by_visible_text(codec)
        ele = self.browser.driver.find_element('xpath', '//*[@id="AccountA_divVideoCodecs"]//input[@value="↑"]')
        for _ in range(3):
            ele.click()
        self.click_submit()

    def get_h264_codec_bit_rate(self):
        """获取h264码率"""
        self.enter_account_advanced()
        return self.get_selected_option_by_id_web_v1v2('cH264CodecBitRate')

    def get_user_agent_by_choice_account(self, account):
        """获取账号user agent"""
        self.enter_account_advanced()
        self.select_option_value_by_name_web_v1v2(self.web_element_info['sip_account_choice'], account)
        time.sleep(2)
        return self.browser.get_attribute_value_by_id(self.web_element_info['user_agent'])

    def input_user_agent(self, account, user_agent):
        """
        修改账号的user agent
        :param account: 0、1、2 ...
        :param user_agent:
        :return:
        """
        self.enter_account_advanced()
        self.select_option_value_by_name_web_v1v2(self.web_element_info['sip_account_choice'], str(account))
        time.sleep(2)
        self.input_edit_and_sleep_by_id(self.web_element_info['user_agent'], user_agent)
        self.click_submit()

    def get_rport_status(self):
        """获取rport状态"""
        self.enter_account_advanced()
        rport_status = self.browser.get_attribute_value_by_name(self.web_element_info['rport'])
        return rport_status

    def set_web_rport_status(self, status):
        """
        网页设置rport状态
        :param status: 0 or 1, 0表示关闭，1表示开启
        :return:
        """
        self.enter_account_advanced()
        self.select_option_value_by_name_web_v1v2(self.web_element_info['rport'], status)
        self.click_submit()

    def set_local_sip_port(self, min, max, accept=True, index=1):
        """
        设置 account->advanced的 Min Local SIP Port, MAX Local SIP Port
        """
        self.enter_account_advanced()
        self.select_account_by_index(index)
        self.write_config('.//*[@id="cMaxLocalSipPort" or @id="cMaxLocalSIPPort"]', max)
        self.write_config('.//*[@id="cMinLocalSipPort" or @id="cMinLocalSIPPort"]', min)
        self.click_submit(accept)

    def set_dtmf_info(self, type='RFC2833', notify=None, payload=None, index=1):
        """
        封装设置account-advanced-dtmf配置
        """
        self.enter_account_advanced()
        self.select_option_value_by_name_web_v1v2(self.web_element_info['sip_account_choice'], str(index - 1))
        ele = self.web_element_info
        self.write_config(ele['dtmf_type'], type)
        # self.select_option_by_id_web_v1v2(ele['dtmf_type'], type)
        if notify:
            self.write_config(ele['dtmf_notify'], notify)
            # self.select_option_by_id_web_v1v2(ele['dtmf_notify'], notify)
        if payload:
            self.write_config(ele['dtmf_payload'], payload)
            # self.browser.input_edit_by_id(ele['dtmf_payload'], payload)
        self.click_submit()

    def set_voice_encryption(self, encryption_type):
        """设置语音加密类型"""
        aklog_info(self.device_name_log + 'set_voice_encryption(SRTP): %s' % encryption_type)
        self.enter_account_advanced()
        self.select_option_value_by_name_web_v1v2('cVoiceEncry', encryption_type)
        self.click_submit()

    # </editor-fold>

    # <editor-fold desc="网络基础页面">
    def enter_network_basic(self):
        aklog_info(self.device_name_log + 'enter_network_basic')
        self.menu_expand_and_click(self.web_element_info['network'], self.web_element_info['network_basic'])

    def click_network(self):
        # 点击Network
        self.browser.click_btn_by_id('tMenu30')

    def set_network_to_dhcp(self):
        aklog_info(self.device_name_log + 'set_network_to_dhcp')
        self.enter_network_basic()
        self.check_radio_preceding_label_by_id(self.web_element_info['network_basic_dhcp_id'])
        self.click_submit()
        # self.alert_confirm_accept_and_sleep()

    def set_network_to_static(self, ip_address, subnet_mask, gateway, dns1, dns2):
        aklog_info(self.device_name_log + 'set_network_to_static')
        self.enter_network_basic()
        self.check_radio_preceding_label_by_id(self.web_element_info['network_basic_static_id'])
        self.browser.input_edit_by_id(self.web_element_info['network_basic_ip_addr_id'], ip_address)
        self.browser.input_edit_by_id(self.web_element_info['network_basic_subnet_mask_id'], subnet_mask)
        self.browser.input_edit_by_id(self.web_element_info['network_basic_gateway_id'], gateway)
        self.browser.input_edit_by_id(self.web_element_info['network_basic_dns1_id'], dns1)
        self.browser.input_edit_by_id(self.web_element_info['network_basic_dns2_id'], dns2)
        self.click_submit()
        # self.alert_confirm_accept_and_sleep()

    def get_lan_port_type(self):
        """封装获取LAN Port Type函数"""
        aklog_info(self.device_name_log + "get_lan_port_type")
        self.enter_network_basic()
        return self.get_value_and_sleep_by_id(self.web_element_info['status_lan_port_type'])

    # </editor-fold>

    # <editor-fold desc="网络高级页面">
    def enter_network_advanced(self):
        aklog_info(self.device_name_log + 'enter_network_advanced')
        self.menu_expand_and_click(self.web_element_info['network'], self.web_element_info['network_advanced_submenu'])

    def click_network_advanced(self):
        # 点击Network_Advanced
        self.browser.click_btn_by_id(self.web_element_info['network_advanced_submenu'])

    def get_server_type(self):
        aklog_info(self.device_name_log + 'get_server_type')
        self.enter_network_advanced()
        tag_name = self.browser.get_tag_name_by_id(self.web_element_info['network_connect_type_id'])
        if tag_name == 'label':
            server_type = self.browser.get_value_by_id(self.web_element_info['network_connect_type_id'])
        elif tag_name == 'select':
            server_type = self.browser.get_selected_option_by_name(self.web_element_info['network_connect_type_id'])
        else:
            server_type = ''
        aklog_info(self.device_name_log + 'server_type: %s' % server_type)
        return server_type

    def set_server_type(self, server_type='None'):
        """
        设置连接类型
        :param server_type: 'None' or 'SDMC' or 'Cloud'
        :return:
        """
        aklog_info(self.device_name_log + 'set_server_type, server_type: %s' % server_type)
        if server_type == 'None':
            self.select_option_value_by_name_web_v1v2(self.web_element_info['network_connect_type_id'], '0')
        elif server_type == 'SDMC':
            self.select_option_value_by_name_web_v1v2(self.web_element_info['network_connect_type_id'], '1')
        elif server_type == 'Cloud':
            self.select_option_value_by_name_web_v1v2(self.web_element_info['network_connect_type_id'], '2')
        else:
            aklog_info(self.device_name_log + 'server type error')

    def set_discovery_mode(self, mode='Enabled'):
        """
        启用或禁用discovery mode
        :param mode: 'Enabled' or 'Disabled', 0 or 1
        :return:
        """
        if mode == 'Enabled' or str(mode) == '1':
            self.write_config(self.web_element_info['network_discovery_mode_name'], '1')
        elif mode == 'Disabled' or str(mode) == '0':
            self.write_config(self.web_element_info['network_discovery_mode_name'], '0')
        else:
            aklog_info(self.device_name_log + 'discovery mode error')

    def get_discovery_mode(self):
        self.enter_network_advanced()
        return self.get_selected_option_by_name_web_v1v2(self.web_element_info['network_discovery_mode_name'])

    def set_device_node_address(self, node_address):
        """
        设置节点地址
        :param node_address: 1.1.1.1.1
        :return:
        """
        if node_address:
            node_address = node_address.split('.')
        node_len = len(node_address)
        if 1 > node_len > 5:
            aklog_info(self.device_name_log + 'node_address is error')
            return False
        self.browser.clear_edit_by_id(self.web_element_info['network_device_node_addr1_id'])
        self.browser.clear_edit_by_id(self.web_element_info['network_device_node_addr2_id'])
        self.browser.clear_edit_by_id(self.web_element_info['network_device_node_addr3_id'])
        self.browser.clear_edit_by_id(self.web_element_info['network_device_node_addr4_id'])
        self.browser.clear_edit_by_id(self.web_element_info['network_device_node_addr5_id'])
        if node_len >= 1:
            self.browser.input_edit_by_id(self.web_element_info['network_device_node_addr1_id'], node_address[0])
        if node_len >= 2:
            self.browser.input_edit_by_id(self.web_element_info['network_device_node_addr2_id'], node_address[1])
        if node_len >= 3:
            self.browser.input_edit_by_id(self.web_element_info['network_device_node_addr3_id'], node_address[2])
        if node_len >= 4:
            self.browser.input_edit_by_id(self.web_element_info['network_device_node_addr4_id'], node_address[3])
        if node_len == 5:
            self.browser.input_edit_by_id(self.web_element_info['network_device_node_addr5_id'], node_address[4])

    def get_device_node_address(self):
        aklog_info(self.device_name_log + 'get_device_node_address')
        address1 = self.browser.get_attribute_value_by_id(self.web_element_info['network_device_node_addr1_id'])
        address2 = self.browser.get_attribute_value_by_id(self.web_element_info['network_device_node_addr2_id'])
        address3 = self.browser.get_attribute_value_by_id(self.web_element_info['network_device_node_addr3_id'])
        address4 = self.browser.get_attribute_value_by_id(self.web_element_info['network_device_node_addr4_id'])
        address5 = self.browser.get_attribute_value_by_id(self.web_element_info['network_device_node_addr5_id'])
        address_list = [address1, address2, address3, address4, address5]
        for address in address_list:
            if address is not None and address == '':
                address_list.remove(address)
        node_address = '.'.join(address_list)
        return node_address.strip('.')

    def set_device_extension(self, extension):
        self.browser.input_edit_by_id(self.web_element_info['network_device_extension_id'], extension)

    def get_device_extension(self):
        aklog_info(self.device_name_log + 'get_device_extension')
        self.enter_network_advanced()
        return self.browser.get_attribute_value_by_id(self.web_element_info['network_device_extension_id'])

    def set_device_location(self, location):
        self.browser.input_edit_by_id(self.web_element_info['network_device_location_id'], location)

    def get_device_location(self):
        aklog_info(self.device_name_log + 'get_device_location')
        self.enter_network_advanced()
        return self.browser.get_attribute_value_by_id(self.web_element_info['network_device_location_id'])

    def set_connect_setting(self, data):
        aklog_info()
        self.enter_network_advanced()
        self.set_discovery_mode(data['discovery_mode'])
        self.set_device_node_address(data['node_address'])
        self.click_submit()
        self.set_device_extension(data['extension'])
        self.set_device_location(data['location'])
        self.click_submit()

    def set_location_connect_setting(self, discovery_mode=None, node_address=None, extension=None, location=None):
        aklog_info()
        self.enter_network_advanced()
        if discovery_mode is not None:
            self.set_discovery_mode(discovery_mode)
        if node_address is not None:
            self.set_device_node_address(node_address)
        if extension is not None:
            self.set_device_extension(extension)
        if location is not None:
            self.set_device_location(location)
        self.click_submit()

    def modify_device_location(self, location):
        self.enter_network_advanced()
        self.set_device_location(location)
        self.click_submit()

    def get_connect_type_value(self):
        # 获取连接的类型
        value = self.browser.get_value_by_id('lConnectType')
        return value

    def get_device_location_value(self):
        # 获取Device Location的值
        value = self.browser.get_attribute_value_by_xpath('//*[@id="inDeviceNodeLocation"]')
        return value

    def get_web_min_rtp_port(self):
        """获取Starting RTP Port的值"""
        min_rtp_port = self.browser.get_attribute_value_by_name(self.web_element_info['input_starting_rtp_port'])
        return min_rtp_port

    def get_web_max_rtp_port(self):
        """获取Max RTP Port的值"""
        max_rtp_port = self.browser.get_attribute_value_by_name(self.web_element_info['input_max_rtp_port'])
        return max_rtp_port

    def set_web_min_rtp_port(self, data):
        """网页设置Starting RTP Port"""
        self.browser.input_edit_by_name(self.web_element_info['input_starting_rtp_port'], data)

    def set_web_max_rtp_port(self, data):
        """网页设置Max RTP Port"""
        self.browser.input_edit_by_name(self.web_element_info['input_max_rtp_port'], data)

    # </editor-fold>

    # <editor-fold desc="phone相关">
    def click_phone(self):
        # 点击Phone
        self.browser.click_btn_by_id('tMenu40')
        time.sleep(1)

    def click_relay(self):
        # 点击Relay
        self.menu_expand_and_click('tMenu40', 'tMenu420')

    def click_select_relays_value(self):
        # 点击Softkey In Talking Page-Key 0的Relay
        self.browser.click_btn_by_xpath('//*[@id="tableTalkingPage"]/tbody/tr[2]/td[4]/div/input[1]')

    def select_relays_remote_relay_dtmf1(self):
        # 选择Softkey In Talking Page-Key 0的Remote Relay DTMF1
        self.browser.click_btn_by_xpath('//*[@id="tableTalkingPage"]/tbody/tr[2]/td[4]/div/div/ul/li[2]')

    def input_edit_dtmf_code_value(self, value):
        # 编辑Remote Relay-DTMF code1
        self.browser.input_edit_by_id('cDTMFCodeValue', value)

    def click_intercom(self):
        # 点击Intercom
        self.browser.click_btn_by_id('tMenu130')

    def click_intercom_advanced(self):
        # 点击Intercom Advanced
        self.browser.click_btn_by_id('tMenu1305')

    def click_standby_mode(self):
        # 点击Intercom Advanced
        self.browser.click_btn_by_xpath('//*[@id="text"]')

    def click_standby_mode_select(self, mode):
        # 选择Standby Mode
        # mode = 1 表示None、mode = 1 表示Blank、mode = 2 表示Image
        mode = int(mode)
        self.browser.click_btn_by_xpath('//*[@id="divStandBy"]/div[2]/div[1]/div/div/ul/li[' + str(mode) + ']')

    def enter_web_phone_key_display(self):
        aklog_info(self.device_name_log + 'enter_web_phone_key_display')
        self.menu_expand_and_click('tMenu40', 'tMenu441')

    def enter_web_phone_ring_tones(self):
        aklog_info(self.device_name_log + 'enter_web_phone_ring_tones')
        self.menu_expand_and_click('tMenu40', 'tMenu45')

    def enter_web_phone_action_url(self):
        aklog_info(self.device_name_log + 'enter_web_phone_action_url')
        self.menu_expand_and_click('tMenu40', 'tMenu410')

    def enter_web_phone_album(self):
        aklog_info(self.device_name_log + 'enter_web_phone_album')
        self.menu_expand_and_click('tMenu40', 'tMenu413')

    def enter_web_phone_intercome(self):
        aklog_info(self.device_name_log + 'enter_web_phone_intercome')
        self.menu_expand_and_click('tMenu40', 'tMenu418')

    def enter_web_phone_lift(self):
        aklog_info(self.device_name_log + 'enter_web_phone_lift')
        self.menu_expand_and_click('tMenu40', 'tMenu421')

    def enter_web_phone_dialplan(self):
        aklog_info(self.device_name_log + 'enter_web_phone_dialplan')
        self.menu_expand_and_click('tMenu40', 'tMenu47')

    def clear_replace_rule(self):
        """网页dial plan清空replace rule"""
        self.enter_web_phone_dialplan()
        self.select_option_value_by_id_web_v1v2('cCurGroup', '0')
        self.check_box_and_sleep_by_id('cCheck0')
        value = self.browser.get_id_status('Delete')
        if value:
            self.click_btn_and_sleep_by_id('Delete')
            self.alert_confirm_accept_and_sleep()

    def set_replace_rule(self, prefix_value, replace_value):
        """网页dial plan配置replace rule"""
        self.enter_web_phone_dialplan()
        self.select_option_value_by_id_web_v1v2('cCurGroup', '0')
        self.click_btn_and_sleep_by_id('Add')
        self.browser.input_edit_by_id('cEditValue1', prefix_value)
        self.browser.input_edit_by_id('cEditValue2', replace_value)
        self.click_btn_and_sleep_by_id('rulesSubmit')

    def clear_dial_now(self):
        """网页dial plan清空dial_now"""
        self.enter_web_phone_dialplan()
        self.select_option_value_by_id_web_v1v2('cCurGroup', '1')
        self.check_box_and_sleep_by_id('cCheck0')
        value = self.browser.get_id_status('Delete')
        if value:
            self.click_btn_and_sleep_by_id('Delete')
            self.alert_confirm_accept_and_sleep()

    def set_dial_now(self, dialnow_value):
        """网页dial plan配置dial now"""
        self.enter_web_phone_dialplan()
        self.select_option_value_by_id_web_v1v2('cCurGroup', '1')
        self.click_btn_and_sleep_by_id('Add')
        self.browser.input_edit_by_id('cEditValue1', dialnow_value)
        self.click_btn_and_sleep_by_id('rulesSubmit')

    def disable_all_dial_delay(self):
        """网页dial plan关闭All Dial Delay"""
        self.enter_web_phone_dialplan()
        self.select_option_value_by_id_web_v1v2('cDialAllDelay', '0')
        self.click_submit()

    # </editor-fold>

    # <editor-fold desc="Phone - Time/Lang页面">
    def enter_web_phone_time_page(self):
        aklog_info(self.device_name_log + 'enter_web_phone_time_page')
        self.menu_expand_and_click('tMenu40', 'tMenu41')

    def enter_web_language(self):
        """进入网页端language界面"""
        self.menu_expand_and_click("tMenu40", "tMenu41")

    def set_time_zone_8(self):
        aklog_info(self.device_name_log + 'set_time_zone_8')
        self.enter_web_phone_time_page()
        self.select_option_value_by_name_web_v1v2('cTimeZone', '375')
        self.click_submit()
        time.sleep(2)

    def set_web_language_to_english(self):
        aklog_info(self.device_name_log + 'set_web_language_to_english')
        self.enter_web_phone_time_page()
        self.select_option_value_by_name_web_v1v2('cWebLanguage', '0')
        self.click_submit()

    def set_web_language(self, option_value):
        """弃用，改用set_web_language_by_option_value这个方法"""
        self.set_web_language_by_option_value(option_value)

    def set_web_language_by_option_value(self, option_value):
        """设置网页语言，通过option value"""
        aklog_info(self.device_name_log + 'set_web_language_by_option_value: %s' % option_value)
        self.enter_web_phone_time_page()
        self.select_option_value_by_name_web_v1v2('cWebLanguage', option_value)

    def set_lcd_language_by_option_value(self, option_value):
        aklog_info(self.device_name_log + 'set_web_language_by_option_value: %s' % option_value)
        self.enter_web_phone_time_page()
        self.select_option_value_by_name_web_v1v2('cLCDLanguage', option_value)

    def set_web_language_by_option_name(self, language):
        """设置网页语言"""
        aklog_info(self.device_name_log + 'set_web_language_by_option_name: %s' % language)
        self.enter_web_phone_time_page()
        self.select_option_by_name_web_v1v2('cWebLanguage', language)

    def get_web_language_list(self):
        """获取网页全部语言选项"""
        self.enter_web_phone_time_page()
        value = self.get_select_options_list_by_name('cWebLanguage')
        return value

    def get_current_web_language(self):
        """获取网页当前语言选项"""
        self.enter_web_phone_time_page()
        value = self.get_selected_option_by_name_web_v1v2('cWebLanguage')
        return value

    def get_web_language_title(self):
        """获取web language标题翻译，用来判断语言切换是否成功"""
        self.enter_web_phone_time_page()
        return self.browser.get_value_by_id('tWebLanguage')

    def get_web_current_language(self):
        """封装获取当前网页语言"""
        aklog_info(self.device_name_log + 'get_web_current_language')
        self.enter_web_phone_time_page()
        value = self.get_selected_option_by_name_web_v1v2('cWebLanguage')
        return value

    def judge_change_language(self, data):
        """封装语言切换是否生效"""
        aklog_info(self.device_name_log + 'judge_change_language')
        value = self.get_web_current_language()
        return value == data

    def get_selected_time_zone(self):
        aklog_info(self.device_name_log + 'get_selected_time_zone')
        self.enter_web_phone_time_page()
        self.browser.web_refresh()
        time_zone = self.get_selected_option_by_name_web_v1v2(self.web_element_info['phone_time_zone'])
        return time_zone

    def get_time_zone_options(self):
        """获取时区列表"""
        aklog_info(self.device_name_log + 'get_time_zone_options')
        self.enter_web_phone_time_page()
        self.browser.web_refresh()
        tz_list = self.get_select_options_list_by_name(self.web_element_info['phone_time_zone'])
        return tz_list

    def get_selected_time_format(self):
        """
        获取选择的时间格式
        :return: 12/24
        """
        aklog_info(self.device_name_log + 'get_selected_time_format')
        self.enter_web_phone_time_page()
        self.browser.web_refresh()
        time_format = self.get_selected_option_by_name_web_v1v2(self.web_element_info['phone_time_format'])
        if time_format:
            time_format = re.sub(r'\D', '', time_format)  # 正则表达式去除非数字字符串
        return time_format

    def set_time_format(self, time_format):
        """设置时间格式"""
        aklog_info(self.device_name_log + 'set_time_format: %s' % time_format)
        self.enter_web_phone_time_page()
        self.select_option_by_name_web_v1v2(self.web_element_info['phone_time_format'], time_format)
        self.click_submit()

    def get_selected_date_format(self, trans_fmt=True):
        """获取当前选择的日期格式，返回Y-M-D，M-D-Y，D-M-Y"""
        aklog_info(self.device_name_log + 'get_selected_date_format')
        self.enter_web_phone_time_page()
        self.browser.web_refresh()
        date_format = self.get_selected_option_by_name_web_v1v2(self.web_element_info['phone_date_format'])
        if trans_fmt:
            if 'YYYY' in date_format:
                date_format = date_format.replace('YYYY', 'Y').replace('MM', 'M').replace('DD', 'D').replace('/', '-')
            else:
                date_format = get_current_date_format(date_format)
        return date_format

    def set_date_format(self, date_format):
        """设置日期格式"""
        aklog_info(self.device_name_log + 'set_date_format: %s' % date_format)
        self.enter_web_phone_time_page()
        self.select_option_by_name_web_v1v2(self.web_element_info['phone_date_format'], date_format)
        self.click_submit()

    def web_set_time_format(self, data):
        """网页端设置时间格式"""
        self.select_option_value_by_name_web_v1v2(self.web_element_info['time_format_choice'], data)
        self.click_submit()

    def web_get_time_format(self):
        """网页端获取当前时间格式"""
        self.enter_web_language()
        cur_time_format = self.get_selected_option_by_name_web_v1v2(self.web_element_info['time_format_choice'])
        return cur_time_format

    def web_set_date_format(self, date_format):
        """网页端设置日期格式"""
        self.select_option_by_name_web_v1v2(self.web_element_info['date_format_choice'], date_format)
        self.click_submit()

    def web_get_date_format(self):
        """网页端获取当前日期格式"""
        self.enter_web_language()
        cur_date_format = self.get_selected_option_by_name_web_v1v2(self.web_element_info['date_format_choice'])
        return cur_date_format

    def web_set_time_zone(self, time_zone):
        """网页设置时区，可以传入option_value或文本"""
        self.enter_web_language()
        if 'GMT' in time_zone:
            self.select_option_by_name_web_v1v2(self.web_element_info['time_zone_choice'], time_zone)
        else:
            self.select_option_value_by_name_web_v1v2(self.web_element_info['time_zone_choice'], time_zone)
        self.click_submit()

    def get_os_cur_time(self, time_format):
        """获取系统当前时间并按照选择的时间格式输出"""
        cur = datetime.datetime.now()
        if time_format == '0':
            return cur.strftime('%I:%M %p')
        elif time_format == '1':
            return cur.strftime('%H:%M')

    def get_date_format_list(self):
        """网页获取日期格式列表"""
        date_format_list = self.get_select_options_list_by_name(self.web_element_info['date_format_choice'])
        return date_format_list

    def web_check_manual_time(self):
        """勾选手动时间"""
        self.check_box_and_sleep_by_id(self.web_element_info['manual_time_check_id'])

    def web_input_date_time(self, year, month, day, hour, minute, second):
        """手动时间开启时，网页输入日期和时间"""
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_date_year'], year)
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_date_month'], month)
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_date_day'], day)
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_time_hour'], hour)
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_time_minute'], minute)
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_time_second'], second)
        self.click_submit()

    def web_set_manual_time(self, date_time):
        """时间格式：%Y-%m-%d %H:%M:%S"""
        self.enter_web_phone_time_page()
        self.check_box_and_sleep_by_id(self.web_element_info['manual_time_check_id'])
        time.sleep(0.5)
        src_date_time = dt.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
        year = src_date_time.strftime('%Y')
        month = src_date_time.strftime('%m')
        day = src_date_time.strftime('%d')
        hour = src_date_time.strftime('%H')
        minute = src_date_time.strftime('%M')
        second = src_date_time.strftime('%S')
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_date_year'], year)
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_date_month'], month)
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_date_day'], day)
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_time_hour'], hour)
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_time_minute'], minute)
        self.input_edit_and_sleep_by_name(self.web_element_info['manual_time_second'], second)
        self.click_submit()

    def web_check_auto_time(self):
        """网页端设置为自动获取时间模式"""
        checked_status = self.is_checked_box_and_sleep_by_id(self.web_element_info['auto_time_check_id'])
        if checked_status is False:
            self.check_box_and_sleep_by_id(self.web_element_info['auto_time_check_id'])
            self.click_submit()
        else:
            pass

    def is_web_auto_time(self):
        """网页端检测是否为自动获取时间模式"""
        self.enter_web_phone_time_page()
        return self.is_checked_box_and_sleep_by_id(self.web_element_info['auto_time_check_id'])

    def get_ntp_primary_server(self):
        """网页获取ntp主服务器地址"""
        self.enter_web_phone_time_page()
        return self.browser.get_attribute_value_by_id(self.web_element_info['ntp_primary_server'])

    def get_ntp_secondary_server(self):
        """网页获取ntp次服务器地址"""
        self.enter_web_phone_time_page()
        return self.browser.get_attribute_value_by_id(self.web_element_info['ntp_secondary_server'])

    def get_ntp_update_interval(self):
        """网页获取ntp 更新时间间隔"""
        self.enter_web_phone_time_page()
        return self.browser.get_attribute_value_by_id(self.web_element_info['ntp_update_interval'])

    def web_set_ntp_server(self, ntp_primary_server, ntp_secondary_server):
        """网页设置ntp服务器"""
        self.enter_web_phone_time_page()
        self.input_edit_and_sleep_by_id(self.web_element_info['ntp_primary_server'], ntp_primary_server)
        self.input_edit_and_sleep_by_id(self.web_element_info['ntp_secondary_server'], ntp_secondary_server)
        self.click_btn_and_sleep_by_id('fPageSubmit')

    # </editor-fold>

    # <editor-fold desc="Phone Logo页面">
    def enter_web_phone_logo(self):
        """"进入网页Phone Logo页面"""
        self.menu_expand_and_click(self.web_element_info['phone'], self.web_element_info['phone_logo_page'])

    def get_boot_logo_format(self):
        """获取boot logo的格式提示"""
        boot_logo_format = self.browser.get_value_by_id(self.web_element_info['boot_logo_format_tip'])
        return boot_logo_format

    def get_web_logo_format(self):
        """获取web logo的格式提示"""
        web_logo_format = self.browser.get_value_by_id(self.web_element_info['web_logo_format_tip'])
        return web_logo_format

    def boot_logo_upload(self, path):
        """网页boot logo上传"""
        self.browser.upload_file_by_id(self.web_element_info['boot_logo_upload_select'], path)
        self.boot_logo_upload_submit()

    def boot_logo_upload_submit(self):
        """网页boot logo上传点击提交"""
        self.click_btn_and_sleep_by_id(self.web_element_info['boot_logo_upload_submit'])

    def web_logo_upload(self, path):
        """网页web logo上传"""
        self.browser.upload_file_by_id(self.web_element_info['web_logo_upload_select'], path)
        self.web_logo_upload_submit()

    def web_logo_upload_submit(self):
        """网页web logo上传点击提交"""
        self.click_btn_and_sleep_by_id(self.web_element_info['web_logo_upload_submit'])

    # </editor-fold>

    # <editor-fold desc="Phone - Audio页面">
    def enter_web_phone_audio_page(self):
        aklog_info(self.device_name_log + 'enter_web_phone_audio_page')
        self.menu_expand_and_click('tMenu40', 'tMenu43')

    def set_audio_volume(self, ring_volume=0, talk_volume=0, mic_volume=1, tone_volume=1):
        aklog_info(self.device_name_log + 'set_audio_volume')
        self.browser.input_edit_by_id('cRingVolume', ring_volume)  # Ring Volume
        self.browser.input_edit_by_id('cHandoffTalkVolume', talk_volume)  # Talk Volume
        self.browser.input_edit_by_id('5', mic_volume)  # Mic Volume
        self.browser.input_edit_by_id('cToneVolume', tone_volume)  # Tone Volume

    def set_audio_volume_mute(self):
        aklog_info(self.device_name_log + 'set_audio_volume_mute')
        self.enter_web_phone_audio_page()
        self.set_audio_volume()
        self.click_submit()

    # </editor-fold>

    # <editor-fold desc="Phone Call Features页面">
    def enter_web_phone_call_feature(self):
        aklog_info(self.device_name_log + 'enter_web_phone_call_feature')
        return self.menu_expand_and_click('tMenu40', 'tMenu42')

    def set_intercom_preview(self, enable='1'):
        """设置假预览, enable: 0 or 1"""
        self.enter_web_phone_call_feature()
        self.select_option_value_by_id_web_v1v2('cIntercomPreview', enable)
        self.click_submit()

    def get_current_return_code(self):
        """获取当前return code"""
        self.enter_web_phone_call_feature()
        return self.get_selected_option_by_id_web_v1v2('cReturnCodeRefuse')

    def set_return_code_refuse(self, return_code):
        """
        设置Return Code
        :param return_code: 486 480 404 603
        :return:
        """
        # return_code_info = {'486': '486(Busy Here)',
        #                     '480': '480(Temporarily Unavailable)',
        #                     '400': '404(Not Found)',
        #                     '603': '603(decline)'}
        self.enter_web_phone_call_feature()
        self.select_option_value_by_id_web_v1v2('cReturnCodeRefuse', return_code)
        self.click_submit()

    def set_allowed_ip_list(self, ip_list):
        """设置allowed ip list"""
        self.enter_web_phone_call_feature()
        self.browser.input_edit_by_name('cAllowedIPList', ip_list)
        self.click_submit()

    def get_allowed_ip_list(self):
        """获取allowed_ip_list"""
        self.enter_web_phone_call_feature()
        return self.browser.get_attribute_value_by_name('cAllowedIPList')

    def get_answer_tone(self):
        """获取answer tone状态"""
        return self.get_selected_option_by_id_web_v1v2('cAnswerTone')

    def set_answer_tone(self, enable='1'):
        """设置Answer Tone"""
        self.enter_web_phone_call_feature()
        self.select_option_value_by_id_web_v1v2('cAnswerTone', enable)
        self.click_submit()

    # </editor-fold>

    # <editor-fold desc="alarm action页面">
    def enter_web_alarm_action_page(self):
        """进入alarm action 页面"""
        aklog_info(self.device_name_log + 'enter_web_alarm_action_page')
        self.menu_expand_and_click("tMenu90", "tMenu91")

    def set_alarm_sendCall_status(self, CallNumber, zone, make_call_active='Enabled', alarm_siren_active='Enabled'):
        """
        设置alarm_sendCall的状态
        :param CallNumber:
        :param zone: 1 - 8
        :param make_call_active:
        :param alarm_siren_active:
        :return:
        """
        aklog_info(self.device_name_log + 'set_alarm_sendCall_status')
        self.enter_web_alarm_action_page()
        self.browser.input_edit_by_id('cCallNumber', CallNumber)
        zone = int(zone) - 1

        if make_call_active == 'Enabled':
            make_call_active = '1'
        elif make_call_active == 'Disabled':
            make_call_active = '0'
        self.select_option_value_by_id_web_v1v2('tMakeCallEnable%s' % zone, make_call_active)

        if alarm_siren_active == 'Enabled':
            alarm_siren_active = '1'
        elif alarm_siren_active == 'Disabled':
            alarm_siren_active = '0'
        self.select_option_value_by_id_web_v1v2('tAlarmSirenEnable%s' % zone, alarm_siren_active)
        self.click_submit()

    def set_alarm_siren_status(self, zone, Alarm_Siren_Active='Enabled'):
        """
        设置alarm_siren的状态
        :param zone: 1 - 8
        :param Alarm_Siren_Active:
        :return:
        """
        aklog_info(self.device_name_log + 'set_alarm_siren_status')
        self.enter_web_alarm_action_page()
        zone = int(zone) - 1
        if Alarm_Siren_Active == 'Enabled':
            Alarm_Siren_Active = '1'
        elif Alarm_Siren_Active == 'Disabled':
            Alarm_Siren_Active = '0'
        self.select_option_value_by_id_web_v1v2('tAlarmSirenEnable%s' % zone, Alarm_Siren_Active)
        self.click_submit()

    def set_alarm_sipMessage(self, MessageAccount, zone, MessageContent, Sip_Message_Active):
        """
        设置alarm_sipMessage的状态
        :param MessageAccount:
        :param zone: 1 - 8
        :param MessageContent:
        :param Sip_Message_Active:
        :return:
        """
        aklog_info(self.device_name_log + 'set_alarm_sipMessage')
        self.enter_web_alarm_action_page()
        time.sleep(0.2)
        zone = int(zone) - 1
        self.browser.input_edit_by_id('cMessageAccount', MessageAccount)
        self.browser.input_edit_by_id('tSIPMessage%s' % zone, MessageContent)
        if Sip_Message_Active == 'Enabled':
            Sip_Message_Active = '1'
        elif Sip_Message_Active == 'Disabled':
            Sip_Message_Active = '0'
        self.select_option_value_by_id_web_v1v2('tSendMessageEnable%s' % zone, Sip_Message_Active)
        self.click_submit()

    def set_http_command(self, zone, http_command, Send_Http_Active):
        """
        设置alarm_http_command的状态
        :param zone: 1 - 8
        :param http_command:
        :param Send_Http_Active:
        :return:
        """
        aklog_info(self.device_name_log + 'set_http_command')
        self.enter_web_alarm_action_page()
        zone = int(zone) - 1
        self.browser.input_edit_by_id('tHttpCommand%d' % zone, http_command)
        if Send_Http_Active == 'Enabled':
            Send_Http_Active = '1'
        elif Send_Http_Active == 'Disabled':
            Send_Http_Active = '0'
        self.select_option_value_by_id_web_v1v2('tSendHttpEnable%s' % zone, Send_Http_Active)
        self.click_submit()

    def set_alarm_trigger_local_relay(self, *alarm_trigger_relay_info):
        """
        设置alarm action触发本地Relay
        可以传入多个元组，同时设置多个zone: (1, 1, 1), (3, 2, 0)，元组的三个元素分别表示zone_num, relay_num, enable
        """
        aklog_info(self.device_name_log + 'set_alarm_trigger_local_relay')
        self.enter_web_alarm_action_page()
        for info in alarm_trigger_relay_info:
            zone_num, relay_num, enable = info
            zone_num = int(zone_num) - 1
            self.select_option_value_by_id_web_v1v2('tLocalRelay%sEnable%s' % (relay_num, zone_num), enable)
        self.click_submit()

    def open_webAlarm(self):
        """设备网页打开alarm操作"""
        self.enter_web_phone_key_display()
        if self.is_exist_ele_by_id_web_v1v2('cMoreArea4'):
            self.select_option_value_by_id_web_v1v2('cMoreArea4', '5')
        if self.is_exist_ele_by_id_web_v1v2('cPage2DisplayType4'):  # 最新版本的id和alarm值都改了
            self.select_option_value_by_id_web_v1v2('cPage2DisplayType4', '2')
        self.click_submit()

    # </editor-fold>

    # <editor-fold desc="phonebook页面">
    def enter_local_book(self):
        """进入网页AddressBook界面"""
        self.menu_expand_and_click("tMenu50", "tMenu51")
        for i in range(2):
            if self.get_selected_option_value_by_name_web_v1v2(self.web_element_info['contacts']) != \
                    self.web_element_info['select_allcontact_value']:
                if i < 1:
                    self.select_option_value_by_name_web_v1v2(self.web_element_info['contacts'],
                                                              self.web_element_info['select_allcontact_value'])
                else:
                    aklog_info(self.device_name_log + '未进入AllContacts设置页面')
            else:
                aklog_info(self.device_name_log + '已进入AllContacts设置页面')
                break

    def enter_web_addressbook(self):
        """进入网页AddressBook界面"""
        self.enter_local_book()

    def enter_call_log(self):
        self.menu_expand_and_click("tMenu50", "tMenu52")

    def web_get_first_call_history(self):
        """网页通话记录获取第一条数据的号码"""
        self.enter_call_log()
        first_call_history = self.browser.get_value_by_xpath('//*[@id="cNumber1"]')
        first_call_history_value = "".join(first_call_history.split()).rstrip()
        return first_call_history_value

    def web_get_call_history(self, name):
        """网页通话记录获取第某条数据的Name字段"""
        self.enter_call_log()
        first_call_history = self.browser.get_value_by_xpath('//*[@id="cName%d"]' % name)
        first_call_history_value = "".join(first_call_history.split()).rstrip()
        return first_call_history_value

    def web_get_call_history_number(self, name):
        """网页通话记录获取第某条数据的number字段"""
        self.enter_call_log()
        call_history_number = self.browser.get_value_by_xpath('//*[@id="cNumber%d"]' % name)
        print(call_history_number)
        call_history_number_value = "".join(call_history_number.split()).rstrip()
        return call_history_number_value

    def web_clear_call_history(self):
        """网页清空通话记录"""
        self.enter_call_log()
        self.click_btn_and_sleep_by_id("DeleteAll")
        self.browser.alert_confirm_accept()

    def web_add_contact(self, contact):
        """网页phonebook添加联系人"""
        self.enter_local_book()
        self.browser.input_edit_by_id('cEditName', contact)
        self.browser.input_edit_by_id('cEditOffice', contact)
        self.click_btn_and_sleep_by_id("Contact_Add")
        self.click_submit()

    def web_add_local_contact(self, name=None, number1=None, number2=None, number3=None,
                              group=None, ring=None, account=None):
        """网页添加联系人"""
        self.enter_web_addressbook()
        if name is not None:
            self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_name'], name)
        if number1 is not None:
            self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_num1'], number1)
        if number2 is not None:
            self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_num2'], number2)
        if number3 is not None:
            self.input_edit_and_sleep_by_id('cEditOther', number3)
        if group is not None:
            self.select_option_value_by_id_web_v1v2(self.web_element_info['add_contact_group'], group)
        if ring is not None:
            self.select_option_value_by_id_web_v1v2(self.web_element_info['add_contact_ring'], ring)
        if account is not None:
            self.select_option_value_by_id_web_v1v2(self.web_element_info['add_contact_account'], account)
        self.click_btn_and_sleep_by_id(self.web_element_info['add_contact_btn'])
        # self.wait_process_finished()
        alert = self.browser.get_alert_text(3)
        if alert:
            aklog_info(self.device_name_log + '添加联系人失败，请检查弹窗提示')
            self.browser.alert_confirm_accept()
            self.browser.click_btn_by_id('CancelContact')
            return alert
        elif not self.judge_is_note_warning():
            return True
        else:
            aklog_info(self.device_name_log + '添加联系人失败，请检查输入框')
            self.browser.click_btn_by_id('CancelContact')
            return False

    def web_edit_contact(self, bef_name, aft_name=None, number=None, group=None, floor=None, account=None):
        aklog_info()
        self.enter_web_addressbook()
        try:
            index = self.browser.get_attribute_by_xpath(
                './/*[contains(@id, "cContactName") and text()="%s"]' % bef_name, 'id')
            index = re.search(r'\d+', index).group()
        except:
            aklog_info('未能找到name: %s 的数据' % bef_name)
            return {}
        else:
            self.select_table_row_by_index([int(index)])
            if aft_name:
                self.write_config('cEditName', aft_name)
            if number:
                self.write_config('.//*[@id="cEditMobile" or @id="cEditOffice"]', number)
            if group:
                self.write_config('cEditGroup', group)
            if floor:
                self.click('floorNumText')
                if self.read_config('floorNumText') == 'None':
                    # 取消选择Floor
                    # self.write_config('floorNumText', 'None')
                    self.write_config(
                        './/input[@type="Checkbox"]/../../*[text()="{}"]//input[@type="Checkbox"]'.format('None'),
                        False)
                for floorno in floor:
                    # self.write_config('floorNumText', floorno)  # 取消选择Floor
                    self.write_config(
                        './/input[@type="Checkbox"]/../../*[text()="{}"]//input[@type="Checkbox"]'.format(floorno),
                        True)
                self.click('floorNumText')
                # self.write_config('floorNumText', ['None'])
                # for floorno in floor:
                #     self.write_config('floorNumText', floorno)
            if account:
                self.write_config('cEditAccount', account)
            self.click('Contact_Edit')

    def check_first_index_contact(self):
        """网页Local Contacts页面勾选第一条联系人所在位置的index"""
        self.check_box_and_sleep_by_id(self.web_element_info['first_contact_index_checkbox'])

    def check_index_contact(self, *index):
        """网页Local Contacts页面勾选第几条联系人所在位置的index"""
        for i in index:
            ele_id = re.sub(r'\d', str(i), self.web_element_info['first_contact_index_checkbox'])
            self.check_box_and_sleep_by_id(ele_id)

    def delete_choice_index_contact(self, index):
        """网页Local Contacts页面勾选第几条联系人所在位置的index并删除该联系人"""
        self.check_index_contact(index)
        self.click_btn_and_sleep_by_id(self.web_element_info['delete_contact'])
        self.alert_confirm_accept_and_sleep()
        time.sleep(2)

    def click_delete_contact(self):
        """网页Local Contacts页面点击删除联系人按钮"""
        self.click_btn_and_sleep_by_id(self.web_element_info['delete_contact'])
        self.alert_confirm_accept_and_sleep()
        time.sleep(2)

    def is_click_contact_add_btn(self):
        """判断网页联系人界面的add按钮是否可点击"""
        return self.browser.get_ele_status_by_id(self.web_element_info['add_contact_btn'])

    def is_click_contact_edit_btn(self):
        """判断网页联系人界面的add按钮是否可点击"""
        return self.browser.get_ele_status_by_id(self.web_element_info['edit_contact_btn'])

    def edit_first_web_contact(self, number1, number2, editname):
        """网页编辑第一条联系人"""
        self.enter_web_addressbook()
        self.check_first_index_contact()
        self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_name'], editname)
        self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_num1'], number1)
        self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_num2'], number2)
        self.click_btn_and_sleep_by_id(self.web_element_info['edit_contact_btn'])
        # self.wait_process_finished()
        alert = self.browser.get_alert_text(3)
        if alert:
            aklog_info(self.device_name_log + '编辑联系人失败，请检查弹窗提示')
            self.browser.alert_confirm_accept()
            self.browser.click_btn_by_id('CancelContact')
            return alert

        elif not self.judge_is_note_warning():
            return True
        else:
            aklog_info(self.device_name_log + '编辑联系人失败，请检查输入框')
            self.browser.click_btn_by_id('CancelContact')
            return False

    def web_call_by_contact(self):
        """网页phonebook呼叫联系人"""
        self.enter_local_book()
        self.click_btn_and_sleep_by_id("cContactOfficeNum1")
        self.browser.alert_confirm_accept()
        self.click_submit()

    def web_clear_contact(self):
        """网页清空联系人"""
        self.enter_local_book()
        self.click_btn_and_sleep_by_id("DeleteAll")
        self.browser.alert_confirm_accept()

    def clear_web_contact(self):
        """网页清空联系人列表"""
        if self.judge_is_exsit_contact():
            self.click_btn_and_sleep_by_id(self.web_element_info['delete_all_contact'], 2)
            self.alert_confirm_accept_and_sleep(4)

    def web_clear_contact_group(self):
        """网页清空联系人群组"""
        self.enter_local_book()
        self.click_btn_and_sleep_by_id("DeleteAllGp")
        self.browser.alert_confirm_accept()

    def search_web_contact(self, ele):
        """进入网页AddressBook界面,搜索联系人"""
        self.enter_web_addressbook()
        self.input_edit_and_sleep_by_id(self.web_element_info['contact_search_input'], ele)
        self.click_btn_and_sleep_by_id(self.web_element_info['contact_search_btn'])

    def get_alert_search_null_web_contact(self, ele):
        """进入网页AddressBook界面,搜索的联系人字段为空,获取提示语"""
        self.search_web_contact(ele)
        alert_text = self.browser.get_alert_text()
        self.alert_confirm_accept_and_sleep()
        return alert_text

    def reset_web_contact_search(self):
        """取消搜索联系人"""
        self.click_btn_and_sleep_by_id(self.web_element_info['contact_search_reset_btn'])

    def export_phonebook_file(self):
        """网页导出联系人"""
        aklog_info(self.device_name_log + "%s,export_phonebook_file" % self.__class__.__name__)
        aklog_info(self.device_name_log + '导出联系人文件')
        phonebook_export_file = self.device_config.get_phonebook_export_file_path()
        File_process.remove_file(phonebook_export_file)
        self.enter_local_book()
        self.browser.click_btn_by_id('ExportContacts')
        aklog_info(self.device_name_log + '导出联系人文件: %s' % phonebook_export_file)
        time.sleep(20)
        # self.download_save()
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not os.path.exists(phonebook_export_file):
                aklog_info(self.device_name_log + '联系人文件导出中...')
                time.sleep(3)
            else:
                time.sleep(3)
                return True
        aklog_info(self.device_name_log + '联系人文件导出失败')
        self.browser.screen_shot()
        return False

    def import_phonebook_file(self, file_path=None):
        aklog_info(self.device_name_log + "%s,import_phonebook_file" % self.__class__.__name__)
        aklog_info(self.device_name_log + '导入联系人文件')
        self.enter_local_book()
        if not file_path:
            file_path = self.device_config.get_phonebook_import_file()
        self.browser.upload_file_by_name('importContactsFile', file_path)
        self.browser.click_btn_by_id('ImportContacts')
        time.sleep(2)
        self.browser.alert_confirm_accept()
        # 判断是否处于等待页面
        # for i in range(0, 10):
        #     if self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
        #         aklog_info(self.device_name_log + 'Processing, please wait...')
        #         time.sleep(2)
        #     else:
        #         time.sleep(2)
        #         break
        for i in range(0, 10):
            value = self.browser.get_alert_text()
            if value and "File uploaded success!" in value:
                self.browser.alert_confirm_accept()
                aklog_info(self.device_name_log + '导入文件完成')
                self.browser.screen_shot()
                return True
            elif i < 9:
                time.sleep(2)
                continue
            else:
                aklog_info(self.device_name_log + '导入文件失败，请检查原因')
                self.browser.screen_shot()
                return False

    def export_xml_contacts_file(self):
        """网页导出xml格式联系人"""
        aklog_info(self.device_name_log + '导出xml联系人文件')
        contacts_export_file = self.device_config.get_contacts_export_file_path()
        File_process.remove_file(contacts_export_file)
        self.enter_local_book()
        self.browser.click_btn_by_id('ExportContacts')
        aklog_info(self.device_name_log + '导出xml格式的contacts文件: %s' % contacts_export_file)
        time.sleep(10)
        for i in range(0, 10):
            if not os.path.exists(contacts_export_file):
                aklog_info(self.device_name_log + 'contacts文件导出中...')
                time.sleep(3)
            else:
                time.sleep(3)
                return True
        aklog_info(self.device_name_log + 'contacts文件导出失败')
        self.browser.screen_shot()
        return False

    def export_csv_contacts_file(self):
        """网页导出csv格式联系人"""
        aklog_info(self.device_name_log + '导出csv联系人文件')
        contacts_export_file = self.device_config.get_contacts_export_file_path()
        File_process.remove_file(contacts_export_file)
        self.enter_local_book()
        self.browser.click_btn_by_id('ExportCsvContacts')
        aklog_info(self.device_name_log + '导出csv格式的contacts文件: %s' % contacts_export_file)
        time.sleep(10)
        for i in range(0, 10):
            if not os.path.exists(contacts_export_file):
                aklog_info(self.device_name_log + 'contacts文件导出中...')
                time.sleep(3)
            else:
                time.sleep(3)
                return True
        aklog_info(self.device_name_log + 'contacts文件导出失败')
        self.browser.screen_shot()
        return False

    def import_xml_contacts_file(self, file=None):
        """导入xml格式contacts文件"""
        if not file:
            file = self.device_config.get_contacts_import_xml_file_path()
        self.browser.upload_file_by_id(self.web_element_info['contacts_select_file'], file)
        self.click_btn_and_sleep_by_id(self.web_element_info['contacts_import'])
        time.sleep(2)
        self.alert_confirm_accept_and_sleep()
        for i in range(10):
            if self.browser.is_exist_alert():
                self.alert_confirm_accept_and_sleep()
                break
        time.sleep(2)
        if self.judge_is_exsit_contact():
            aklog_info(self.device_name_log + "xml格式联系人导入成功")
            return True
        else:
            aklog_info(self.device_name_log + "xml格式联系人导入失败")
            return False

    def import_csv_contacts_file(self, file=None):
        """导入csv格式contacts文件"""
        if not file:
            file = self.device_config.get_contacts_import_csv_file_path()
        self.browser.upload_file_by_id(self.web_element_info['contacts_select_file'], file)
        self.click_btn_and_sleep_by_id('ImportCsvContacts')
        time.sleep(2)
        self.alert_confirm_accept_and_sleep()
        for i in range(10):
            if self.browser.is_exist_alert():
                self.alert_confirm_accept_and_sleep()
                break
        time.sleep(2)
        if self.judge_is_exsit_contact():
            aklog_info(self.device_name_log + "csv格式联系人导入成功")
            return True
        else:
            aklog_info(self.device_name_log + "csv格式联系人导入失败")
            return False

    def judge_is_exsit_contact(self):
        """判断网页是否存在联系人"""
        self.enter_local_book()
        first_contact_name = self.get_value_and_sleep_by_id(self.web_element_info['first_contact_name'])
        if first_contact_name:
            aklog_info(self.device_name_log + "contact列表不为空")
            return True
        else:
            aklog_info(self.device_name_log + "contact列表为空")
            return False

    def get_first_contact_number1(self):
        """网页AddressBook界面获取第一条联系人的number1值"""
        first_contact_number1 = self.browser.get_value_by_id(self.web_element_info['first_contact_number1'])
        aklog_info(self.device_name_log + "first_contact_number1:" + str(first_contact_number1))
        return first_contact_number1

    def get_first_contact_number2(self):
        """网页AddressBook界面获取第一条联系人的number2值"""
        first_contact_number2 = self.browser.get_value_by_id(self.web_element_info['first_contact_number2'])
        aklog_info(self.device_name_log + "first_contact_number1:" + str(first_contact_number2))
        return first_contact_number2

    def get_first_contact_name(self):
        """网页AddressBook界面获取第一条联系人的name值"""
        first_contact_name = self.browser.get_value_by_id(self.web_element_info['first_contact_name'])
        aklog_info(self.device_name_log + "first_contact_name:" + str(first_contact_name))
        return first_contact_name

    def get_index_contact_number(self, index, number):
        """网页AddressBook界面获取第几条联系人的number值"""
        if number == 'number1':
            index_contact_number = self.browser.get_value_by_id(self.web_element_info['index_contact_number1'] % index)
        elif number == 'number2':
            index_contact_number = self.browser.get_value_by_id(self.web_element_info['index_contact_number2'] % index)
        else:
            aklog_info(self.device_name_log + "参数2传值错误，应传值number1或number2")
            index_contact_number = None
        return index_contact_number

    def get_contacts_total_data(self):
        """网页AddressBook界面获取联系人总数"""
        contacts_page = self.browser.get_value_by_id(self.web_element_info['contact_page'])
        contacts_total_data = contacts_page.split('/')[1]
        return contacts_total_data

    def click_contacts_next_btn(self):
        """点击contacts列表的下一页按钮"""
        self.browser.click_btn_by_id(self.web_element_info['contact_next_btn'])

    def click_contacts_pre_btn(self):
        """点击contacts列表的上一页按钮"""
        self.browser.click_btn_by_id(self.web_element_info['contact_pre_btn'])

    def get_contacts_current_page(self):
        """网页联系人界面获取联系人列表当前页数"""
        contacts_page = self.browser.get_value_by_id(self.web_element_info['contact_page'])
        contacts_page_current_page = contacts_page.split('/')[0]
        return contacts_page_current_page

    def contact_input_page_and_jump(self, page):
        self.input_edit_and_sleep_by_id(self.web_element_info['contact_input_page'], page)
        self.browser.click_btn_by_id(self.web_element_info['contact_page_btn'])
        time.sleep(2)

    def contacts_import_click_cancel(self):
        """点击contact导入界面的cancel按钮"""
        self.browser.click_btn_by_id(self.web_element_info['contacts_import_cancel'])

    def import_error_xml_format_contacts_file(self):
        """导入错误xml格式的contacts文件"""
        self.browser.upload_file_by_id(self.web_element_info['contacts_select_file'],
                                       self.device_config.get_contacts_import_error_xml_file_path())
        self.click_btn_and_sleep_by_id(self.web_element_info['contacts_import'], 2)
        self.alert_confirm_accept_and_sleep(2)
        alert_text = self.browser.get_alert_text(30)
        self.alert_confirm_accept_and_sleep()
        return alert_text

    def import_error_csv_format_contacts_file(self):
        """导入错误csv格式的contacts文件"""
        self.browser.upload_file_by_id(self.web_element_info['contacts_select_file'],
                                       self.device_config.get_contacts_import_error_csv_file_path())
        self.click_btn_and_sleep_by_id('ImportCsvContacts', 2)
        self.alert_confirm_accept_and_sleep(2)
        alert_text = self.browser.get_alert_text(30)
        self.alert_confirm_accept_and_sleep()
        return alert_text

    def contacts_import_and_no_choose_file(self):
        """未选择文件直接点击contacts导入按钮"""
        self.click_btn_and_sleep_by_id(self.web_element_info['contacts_import'], 2)
        alert_text = self.browser.get_alert_text(2)
        self.alert_confirm_accept_and_sleep()
        return alert_text

    def import_contacts_return_filename(self):
        """选中contacts文件后返回被选中的文件名"""
        self.browser.upload_file_by_id(self.web_element_info['contacts_select_file'],
                                       self.device_config.get_contacts_import_xml_file_path())
        filename = self.browser.get_value_by_id(self.web_element_info['contacts_import_file_text'])
        return filename

    def contacts_import_return_filename(self):
        """返回contacts导入界面的文件选择框中的内容"""
        filename = self.browser.get_value_by_id(self.web_element_info['contacts_import_file_text'])
        return filename

    def dial_out_number_on_phone_book(self, number, account=None):
        """在本地联系人页面输入号码呼出"""
        self.browser.input_edit_by_id('cWebCallNumber', number)
        if account:
            self.select_option_value_by_id_web_v1v2('cWebCallAccount', account)
        self.browser.click_btn_by_id('DialOut')
        self.browser.alert_confirm_accept()
        time.sleep(2)
        alert = self.browser.get_alert_text()
        if alert:
            self.browser.alert_confirm_accept()
        if alert == 'Send Success!':
            return True
        else:
            return alert

    def hang_up_call_on_phone_book(self):
        """在本地联系人页面挂断通话"""
        self.browser.click_btn_by_id('HangUp')
        self.browser.alert_confirm_accept()

    # </editor-fold>

    # <editor-fold desc="Phone Book BlockList黑名单">
    def judge_web_contacts_is_contain_blockist(self):
        """判断网页是否含有黑名单选项"""
        value = self.get_select_options_value_list_by_name(self.web_element_info['contacts'])
        if self.web_element_info['select_blocklist_value'] in value:
            aklog_info(self.device_name_log + "网页联系人选项含有黑名单群组")
            return True
        else:
            aklog_info(self.device_name_log + "网页联系人群组不包含黑名单")
            return False

    def judge_web_contacts_is_contain_move_to_blockist(self):
        """判断网页是否还有网页move to黑名单项"""
        value = self.get_select_options_value_list_by_name(self.web_element_info['select_moveto'])
        if self.web_element_info['select_blocklist_value'] in value:
            aklog_info(self.device_name_log + "网页联系人移动编辑含有黑名单群组")
            return True
        else:
            aklog_info(self.device_name_log + "网页联系人群组移动编辑不包含黑名单")
            return False

    def judge_web_contacts_is_contain_import_blockist(self):
        """判断网页是否还有网页导入黑名单项"""
        if self.browser.is_exist_and_visible_ele_by_id(self.web_element_info['blocklist_import']):
            aklog_info(self.device_name_log + "网页联系人含有黑名单导入按钮")
            return True
        else:
            aklog_info(self.device_name_log + "网页联系人没有黑名单导入按钮")
            return False

    def enter_web_blocklist_setting(self):
        """进入网页黑名单设置界面"""
        self.menu_expand_and_click("tMenu50", "tMenu51")
        for i in range(2):
            if self.get_selected_option_value_by_name_web_v1v2(self.web_element_info['contacts']) != \
                    self.web_element_info['select_blocklist_value']:
                if i < 1:
                    self.select_option_value_by_name_web_v1v2(self.web_element_info['contacts'],
                                                              self.web_element_info['select_blocklist_value'])
                else:
                    aklog_info(self.device_name_log + '未进入黑名单设置页面')
            else:
                aklog_info(self.device_name_log + '已进入黑名单设置页面')
                break

    def web_add_blocklist(self, name=None, num1=None, num2=None, num3=None, account=None):
        """网页添加黑名单"""
        self.enter_web_blocklist_setting()
        if name is not None:
            self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_name'], name)
        if num1 is not None:
            self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_num1'], num1)
        if num2 is not None:
            self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_num2'], num2)
        if num3 is not None:
            self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_num3'], num3)
        if account is not None:
            self.select_option_value_by_name_web_v1v2(self.web_element_info['select_account'], account)
        self.click_btn_and_sleep_by_id(self.web_element_info['add_contact_btn'])
        alert = self.browser.get_alert_text(3)
        if alert:
            aklog_info(self.device_name_log + '添加黑名单失败，请检查弹窗提示')
            self.browser.alert_confirm_accept()
            self.browser.click_btn_by_id(self.web_element_info['cancel_contact_btn'])
            return alert

        elif not self.judge_is_note_warning():
            return True
        else:
            aklog_info(self.device_name_log + '添加黑名单失败，请检查输入框')
            self.browser.click_btn_by_id(self.web_element_info['cancel_contact_btn'])
            return False

    def web_clear_blocklist(self):
        """网页清除黑名单"""
        self.enter_web_blocklist_setting()
        if self.browser.get_id_status(self.web_element_info['delete_all_contact']):
            self.click_btn_and_sleep_by_id(self.web_element_info['delete_all_contact'], 2)
            self.alert_confirm_accept_and_sleep(4)

    def choose_index1_blocklist_edit_name(self, name):
        """选择第一个黑名单编辑名字"""
        self.enter_web_blocklist_setting()
        self.browser.check_box_by_id(self.web_element_info['index1_checkbox'])
        self.input_edit_and_sleep_by_id(self.web_element_info['add_contact_name'], name)
        self.click_btn_and_sleep_by_id(self.web_element_info['contact_edit_btn'])
        alert = self.browser.get_alert_text(3)
        if alert:
            aklog_info(self.device_name_log + '编辑黑名单失败，请检查弹窗提示')
            self.browser.alert_confirm_accept()
            self.browser.click_btn_by_id('CancelContact')
            return alert

        elif not self.judge_is_note_warning():
            return True
        else:
            aklog_info(self.device_name_log + '编辑黑名单失败，请检查输入框')
            self.browser.click_btn_by_id('CancelContact')
            return False

    def choose_index1_contact_move_to_blocklist(self):
        """选择第一个联系人移动到黑名单"""
        self.enter_web_addressbook()
        self.browser.check_box_by_id(self.web_element_info['index1_checkbox'])
        self.select_option_value_by_name_web_v1v2(self.web_element_info['select_moveto'],
                                                  self.web_element_info['select_blocklist_value'])
        if self.browser.is_exist_alert():
            alert_text = self.browser.get_alert_text()
            self.browser.alert_confirm_accept()
            return alert_text
        else:
            aklog_info(self.device_name_log + 'There is no alert')
            return None

    def select_index_contact_move_to_blocklist(self, index):
        """选择多个联系人移动到黑名单"""
        self.enter_web_addressbook()
        for i in range(index):
            self.browser.check_box_by_id(self.web_element_info['index_checkbox'] % (i + 1))
        self.select_option_value_by_name_web_v1v2(self.web_element_info['select_moveto'],
                                                  self.web_element_info['select_blocklist_value'])
        if self.browser.is_exist_alert():
            alert_text = self.browser.get_alert_text()
            self.browser.alert_confirm_accept()
            return alert_text
        else:
            aklog_info(self.device_name_log + 'There is no alert')
            return None

    def choose_index1_blocklist_move_to_contact(self):
        """选择第一个黑名单移动到联系人群组"""
        self.enter_web_blocklist_setting()
        self.browser.check_box_by_id(self.web_element_info['index1_checkbox'])
        self.select_option_value_by_name_web_v1v2(self.web_element_info['select_moveto'],
                                                  self.web_element_info['select_allcontact_value'])
        if self.browser.is_exist_alert():
            alert_text = self.browser.get_alert_text()
            self.browser.alert_confirm_accept()
            return alert_text
        else:
            aklog_info(self.device_name_log + 'There is no alert')
            return None

    def select_index_blocklist_move_to_contact(self, index):
        """选择多个黑名单移动到联系人"""
        self.enter_web_blocklist_setting()
        for i in range(index):
            self.browser.check_box_by_id(self.web_element_info['index_checkbox'] % (i + 1))
        self.select_option_value_by_name_web_v1v2(self.web_element_info['select_moveto'],
                                                  self.web_element_info['select_allcontact_value'])
        if self.browser.is_exist_alert():
            alert_text = self.browser.get_alert_text()
            self.browser.alert_confirm_accept()
            return alert_text
        else:
            aklog_info(self.device_name_log + 'There is no alert')
            return None

    def judge_is_exsit_blocklist(self):
        """判断网页是否存在黑名单"""
        self.enter_web_blocklist_setting()
        first_contact_name = self.get_value_and_sleep_by_id(self.web_element_info['first_contact_name'])
        if first_contact_name:
            aklog_info(self.device_name_log + "blocklist列表不为空")
            return True
        else:
            aklog_info(self.device_name_log + "blocklist列表为空")
            return False

    def web_get_first_contact_name(self):
        """网页获取第一个联系人的名字"""
        return self.get_value_and_sleep_by_id(self.web_element_info['first_contact_name'])

    # </editor-fold>

    # <editor-fold desc="PhoneBook - Call Log页面">
    def enter_web_call_log(self):
        """封装话机进入网页Call Log界面"""
        self.menu_expand_and_click("tMenu50", "tMenu52")

    def call_history_select(self, option_value):
        """判断网页call log界面筛选去电通话记录"""
        self.enter_web_call_log()
        self.select_option_value_by_id_web_v1v2(self.web_element_info['call_history_drop_down_box'], option_value)
        time.sleep(2)

    def is_exsit_call_type_by_index(self, index, call_type):
        """判断网页call log界面第几条通话记录是否是去电/已接/未接/前转通话记录"""
        self.enter_web_call_log()
        call_log_type = self.get_value_and_sleep_by_id(self.web_element_info['call_log_index'] % index)
        if call_log_type == call_type:
            return True
        else:
            return False

    def export_call_log_file(self):
        """网页导出call log文件"""
        aklog_info(self.device_name_log + '网页导出通话记录')
        call_log_export_file = self.device_config.get_call_log_export_file_path()
        File_process.remove_file(call_log_export_file)
        self.enter_web_call_log()
        self.click_btn_and_sleep_by_id(self.web_element_info['call_log_export'])
        aklog_info(self.device_name_log + '网页导出通话记录文件: %s' % call_log_export_file)
        for i in range(0, 10):
            if not os.path.exists(call_log_export_file):
                aklog_info(self.device_name_log + 'call log文件导出中...')
                time.sleep(3)
            else:
                time.sleep(3)
                return True
        aklog_info(self.device_name_log + 'call log文件导出失败')
        self.browser.screen_shot()
        return False

    def input_page_and_jump(self, page):
        self.input_edit_and_sleep_by_id(self.web_element_info['call_log_input_page'], page)
        self.browser.click_btn_by_id(self.web_element_info['call_log_page_btn'])
        time.sleep(2)

    def click_call_log_next_btn(self):
        """点击call log列表的下一页按钮"""
        self.browser.click_btn_by_id(self.web_element_info['call_log_next_btn'])

    def click_call_log_pre_btn(self):
        """点击call log列表的上一页按钮"""
        self.browser.click_btn_by_id(self.web_element_info['call_log_pre_btn'])

    def get_call_log_current_page(self):
        """网页call log界面获取通话记录当前页数"""
        call_log_page = self.browser.get_value_by_id(self.web_element_info['call_log_page'])
        call_log_page_current_page = call_log_page.split('/')[0]
        return call_log_page_current_page

    def check_first_index_call_log(self):
        """网页call log界面勾选第一条通话记录"""
        self.check_box_and_sleep_by_id(self.web_element_info['call_log_first_index_checkbox'])

    def click_call_log_delete_btn(self):
        """网页call log界面点击通话记录的删除按钮"""
        self.browser.click_btn_by_id(self.web_element_info['call_log_delete_btn'])
        self.alert_confirm_accept_and_sleep(4)

    def delete_all_call_log(self):
        """封装话机网页删除所有Call Log操作"""
        self.enter_web_call_log()
        self.click_btn_and_sleep_by_id("DeleteAll")
        self.alert_confirm_accept_and_sleep()

    def is_exsit_call_log(self):
        """网页call log界面判断是否存在通话记录"""
        self.enter_web_call_log()
        first_call_log = self.get_value_and_sleep_by_id(self.web_element_info['first_call_log_type'])
        if first_call_log:
            aklog_info(self.device_name_log + "通话记录不为空")
            return True
        else:
            aklog_info(self.device_name_log + "通话记录为空")
            return False

    # </editor-fold>

    # <editor-fold desc="Phone multicast页面">
    def enter_web_phone_multicast(self):
        aklog_info(self.device_name_log + 'enter_web_phone_multicast')
        self.menu_expand_and_click('tMenu40', 'tMenu412')

    def set_multicast_group(self, group):
        """
        设置Multicast Group
        :param group: 0 - 3, 0表示禁用
        :return:
        """
        self.enter_web_phone_multicast()
        self.select_option_value_by_id_web_v1v2('cMulticastGroup', group)
        self.click_submit()

    def set_multicast_list(self, address1=None, address2=None, address3=None):
        """设置Multicast List地址"""
        self.enter_web_phone_multicast()
        if address1 is not None:
            self.input_multicast_address('1', address1)
        if address2 is not None:
            self.input_multicast_address('2', address2)
        if address3 is not None:
            self.input_multicast_address('3', address3)
        self.click_submit()

    def set_listen_list(self, *listen_list):
        """
        设置监听地址
        :param listen_list:如果传入参数为元组类型，则包含address和label，否则不包含label
        :return:
        """
        self.enter_web_phone_multicast()
        group = 1
        for listen_info in listen_list:
            if isinstance(listen_info, tuple):
                address = listen_info[0]
                label = listen_info[1]
            else:
                address = listen_info
                label = None
            self.input_listen_list_address(group, address, label)
            group += 1
        self.click_submit()

    def click_multicast(self):
        # 点击Multicast
        self.browser.click_btn_by_id('tMenu412')

    def click_multicast_setting(self):
        # 点击Multicast Setting
        self.browser.click_btn_by_xpath('//*[@id="PhoneMulticast_divVoiceMonitor"]/div[2]/div/div')

    def click_multicast_setting_select(self, group):
        # 点击Multicast Setting
        # group = 0 表示Disable、group = 1 表示group1、group = 2 表示group2、group = 3 表示group3
        group = int(group) + 1
        self.browser.click_btn_by_xpath(
            '//*[@id="PhoneMulticast_divVoiceMonitor"]/div[2]/div/div/div/ul/li[' + str(group) + ']')

    def input_multicast_address(self, group, multicast_address):
        # 输入Multicast 监听地址
        # group = 1 表示group1、group = 2 表示group2、group = 3 表示group3
        group = int(group) - 1
        self.browser.input_edit_by_id('cCastAddr' + str(group), multicast_address)

    def input_listen_list_address(self, group, listen_address, label=None):
        # 输入Listen List被监听地址
        # group = 1 表示group1、group = 2 表示group2、group = 3 表示group3
        group = int(group) - 1
        self.browser.input_edit_by_id('cListeningAddr' + str(group), listen_address)
        if label is not None:
            self.browser.input_edit_by_id('cListeningLabel' + str(group), label)

    def get_multicast_address_value(self, group):
        # 获取Multicast 监听地址
        # group = 1 表示group1、group = 2 表示group2、group = 3 表示group3
        group = int(group) - 1
        value = self.browser.get_attribute_value_by_xpath('//*[@id="cCastAddr' + str(group) + '"]')
        return value

    def get_listen_list_address_value(self, group):
        # 获取Listen List被监听地址
        # group = 1 表示group1、group = 2 表示group2、group = 3 表示group3
        group = int(group) - 1
        value = self.browser.get_attribute_value_by_xpath('//*[@id="cListeningAddr' + str(group) + '"]')
        return value

    # </editor-fold>

    # <editor-fold desc="Device Setting Basic页面">
    def enter_device_setting_basic_page(self):
        """进入网页Device Setting页面"""
        self.menu_expand_and_click('tMenu122', 'tMenu123')

    def set_power_output(self, enable):
        """
        设置PON输出启用或关闭
        :param enable: '0' or '1'
        :return:
        """
        self.enter_device_setting_basic_page()
        self.select_option_value_by_id_web_v1v2('cPowerOutputEnable', enable)
        self.click_submit()
        self.wait_process_finished()

    # </editor-fold>

    # <editor-fold desc="Telnet/SSH通用API">
    def telnet_login(self):
        for i in range(5):
            if self.tln.login_host():
                self.tln_ssh_port_list = self.tln.get_port_list()
                self.tln_ssh_pwd_list = self.tln.get_pwd_list()
                return True
            elif i < 2:
                self.web_open_ssh()
                continue
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
            elif i < 2:
                self.web_open_ssh()
                continue
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
        aklog_debug()
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
            aklog_debug("get command:%s->result as below:" % str(command))
            aklog_debug('%s' % value)
        return value

    def get_result_by_telnet_command(self, command, print_result=True):
        """后台执行命令获取对应配置的值"""
        aklog_debug()
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
            aklog_debug('result: \n %s' % result)
        return result

    def get_result_by_tln_or_ssh(self, command, print_result=True):
        """telnet或SSH执行命令并获取结果"""
        if 'reboot' in command:
            param_put_reboot_process_flag(True)
        if self.device_config.get_remote_connect_type() == 'telnet':
            result = self.get_result_by_telnet_command(command, print_result)
        else:
            result = self.get_value_by_ssh(command, print_result)
        return result

    def exec_command_by_tln(self, *commands, timeout=10):
        aklog_debug()
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

    def exec_command_by_ssh(self, *commands, timeout=60):
        aklog_debug()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return False
        for command in commands:
            self.ssh.exec_command(command, timeout)
            time.sleep(0.5)
        return True

    def command_by_tln_or_ssh(self, *commands, timeout=60):
        if self.device_config.get_remote_connect_type() == 'telnet':
            return self.exec_command_by_tln(*commands, timeout=timeout)
        else:
            return self.exec_command_by_ssh(*commands, timeout=timeout)

    def exec_command_by_interactive_ssh_thread(self, command):
        """ssh交互式子线程执行，需要与get_result_by_interactive_ssh_thread配合使用"""
        aklog_debug()
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
        return result1

    def exec_command_by_interactive_telnet_thread(self, command):
        """Telnet交互式子线程执行，需要与get_result_by_interactive_telnet_thread配合使用"""
        aklog_debug()
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
        """获取Telnet交互式子线程执行结果，需要与exec_command_by_interactive_ssh_thread配合使用"""
        return self.tln.thread_stop_exec_output_result(timeout=timeout)

    # </editor-fold>

    # <editor-fold desc="Telnet/SSH操作">
    def reboot_by_tln_or_ssh(self, wait_reboot=True, wait_time_after_reboot=10):
        aklog_info(self.device_name_log + 'reboot_by_tln_or_ssh')
        self.command_by_tln_or_ssh('reboot')
        param_put_reboot_process_flag(True)
        if wait_reboot:
            return cmd_waiting_for_device_reboot(
                self.device_info['ip'],
                wait_time1=30,
                wait_time2=self.device_config.get_reboot_default_time(),
                sec=wait_time_after_reboot)
        return

    def get_uptime_by_tln_or_ssh(self):
        """获取开机时间"""
        aklog_info(self.device_name_log + 'get_uptime_by_tln_or_ssh')
        uptime = self.get_result_by_tln_or_ssh(
            'uptime | cut -d "p" -f 2 | cut -b "1-15"|sed "s/\\([^0-9][^0-9]*\\)//g"')
        uptime = uptime.strip()
        aklog_info('uptime: %s min' % uptime)
        return uptime

    def start_adb_server_by_ssh(self, device_id=None, retry_counts=5):
        aklog_info()
        if not device_id:
            device_id = self.device_info.get('deviceid')
        if not device_id:
            aklog_error('device id 为空')
            return False
        if device_id and ':' not in device_id:
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

    def edit_config_by_tln_or_ssh(self, old_config, new_config, path):
        """
        修改配置项
        old_config：旧的配置项
        new_config：新的配置项
        path：配置项的文件夹
        """
        aklog_info()
        command = "sed -i s/%s/%s/g %s" % (old_config, new_config, path)
        return self.command_by_tln_or_ssh(command)

    def get_door_setting_config_by_tln_or_ssh(self, section, key):
        """获取/config/Door/Setting.conf配置文件里面的配置项"""
        return self.get_result_by_tln_or_ssh(
            '/app/bin/inifile_wr r /config/Door/Setting.conf %s %s ""' % (section, key))

    # </editor-fold>

    # <editor-fold desc="Telnet/SSH 进程相关">
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
        aklog_info()
        attribute = self.get_result_by_tln_or_ssh('top -b -n 1 | grep "PID" | grep -v grep')
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_debug('attribute_list: %r' % attribute_list)
        grep_command = ''
        for i in process_flag:
            grep_command += '| grep "%s" ' % i
        info = self.get_result_by_tln_or_ssh('top -b -n 1 | grep -v grep %s' % grep_command)
        if info is None:
            return None
        info = info.replace('\n#', '').strip()
        info = re.sub(' +', ' ', info)
        infos = info.split(' ')
        aklog_debug('process infos: %r' % infos)

        process_info = {}
        index_interval = 0
        for attribute in attribute_list:
            index = attribute_list.index(attribute) + index_interval
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
            elif attribute == 'VSZ':  # 内存值
                if not re.sub(r'\D', '', infos[index]):  # 如果不是数字，则说明该项不是内存值，仍为前面一项的数值
                    # process_info[attribute_list[index - 1].lower()] += infos[index]
                    process_info['vsz'] = infos[index + 1]
                    index_interval = 1
                else:
                    process_info['vsz'] = infos[index]
            elif attribute == '%VSZ':  # 内存使用率
                process_info['vsz%'] = infos[index]
            elif attribute == '%MEM':  # 内存使用率
                process_info['mem%'] = infos[index]
            elif attribute == '%CPU':  # CPU使用率
                process_info['cpu%'] = infos[index]
            elif 'COMMAND' in attribute:
                if len(infos) + index_interval > len(attribute_list):
                    process_info['command'] = ' '.join(infos[index:])
                else:
                    process_info['command'] = infos[index]

        aklog_info('process_info: %r' % process_info)
        return process_info

    def ps_get_process_info(self, *process_flag):
        """获取phone进程信息，返回字典"""
        aklog_info(self.device_name_log + 'ps_get_process_info')
        attribute = self.get_result_by_tln_or_ssh('ps | grep "PID" | grep -v grep')
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_info(self.device_name_log + 'attribute_list: %r' % attribute_list)
        grep_command = ''
        for i in process_flag:
            grep_command += '| grep "%s" ' % i
        info = self.get_result_by_tln_or_ssh('ps | grep -v grep %s' % grep_command)
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
        info = self.get_result_by_tln_or_ssh('ps')
        return info

    def ps_judge_processes_is_running(self, *processes):
        """
        ps获取进程信息，判断多个进程是否都正在运行
        :param processes: 元组类型，各个进程字段
        :return:
        """
        aklog_info(self.device_name_log + 'ps_judge_processes_is_running')
        not_running_process_list = []
        for process in processes:
            ps_command = 'ps | grep -v grep | grep "%s"' % process
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
        status = self.ps_judge_processes_is_running('/app/bin/sip',
                                                    '/app/bin/phone',
                                                    '/app/bin/netconfig',
                                                    '/app/bin/fcgiserver.fcgi',
                                                    '/app/bin/acgVoice',
                                                    '/app/bin/autop')
        return status

    def check_linuxindoor_device_process_status(self):
        """检查设备进程的状态，是否都在运行，由于各机型的进程信息可能不一致，可以重写该方法"""
        aklog_info(self.device_name_log + 'check_linuxindoor_device_process_status')
        status = self.ps_judge_processes_is_running('{main} /app/bin/sip -a 0',
                                                    '{main} /app/bin/phone',
                                                    '{StartTimer} /app/bin/netconfig',
                                                    '{main} /app/bin/fcgiserver.fcgi',
                                                    '{va_main} /app/bin/vaMain',
                                                    '{TimerThread} /app/bin/dclient')
        return status

    def put_original_process_info(self, process_name, process_info):
        """
        原始进程信息，用于后续判断进程是否异常
        process_name: sip, phone
        process_info：dict类型
        {'pid': '1234', 'mem': '200'}
        """
        self.original_process_info = {process_name: process_info}

    def judge_phone_process_is_normal(self):
        """检查phone进程是否正常，该方法适用于安卓室内机，其他机型可以重写该方法"""
        aklog_info()
        phone_top_info = self.top_get_process_info('com.akuvox.phone')
        if not phone_top_info:
            aklog_error('获取phone进程信息失败，请检查')
            return False
        if not self.original_process_info.get('phone'):
            self.put_original_process_info('phone', phone_top_info)
        ret = True
        # 检查Phone进程是否重启过
        if self.original_process_info['phone'].get('pid') != phone_top_info['pid']:
            aklog_error('phone进程ID变化，存在进程重启问题')
            # 当出现一次phone进程失败，重新设置原始进程信息作为对比
            self.put_original_process_info('phone', phone_top_info)
            ret = False
        # 检查Phone进程的Views数量
        phone_views = self.get_result_by_tln_or_ssh(
            "dumpsys meminfo com.akuvox.phone | grep ' Views' | awk -F'[: ]+' '{print $3}'")
        phone_views = int(phone_views.strip())
        if phone_views > 2000:
            aklog_error('phone进程的Views数超过2000，存在异常')
            ret = False
        # 检查Phone进程的Activities数量
        phone_activities = self.get_result_by_tln_or_ssh(
            "dumpsys meminfo com.akuvox.phone | grep 'Activities' | awk -F'[: ]+' '{print $5}'")
        phone_activities = int(phone_activities.strip())
        if phone_activities > 20:
            aklog_error('phone进程的Activities数超过20，存在异常')
            ret = False
        # 检查Phone进程的内存
        phone_top_info = self.top_get_process_info('com.akuvox.phone')
        phone_mem_info = phone_top_info['vsz']
        phone_mem_num = int(re.sub(r'\D', '', phone_mem_info))
        if phone_mem_num > 2000:
            aklog_error('phone进程的内存超过2000m，存在异常')
            ret = False
        # 检查Phone进程的线程数量
        thread_num = self.get_result_by_tln_or_ssh('cat proc/%s/status | grep Threads' % phone_top_info['pid'])
        thread_num = int(re.sub(r'\D', '', thread_num))
        if thread_num > 400:
            aklog_error('phone进程的线程数超过400，存在异常')
            ret = False

        return ret

    # </editor-fold>

    # <editor-fold desc="telnet/ssh log相关">
    def clear_logs_by_ssh(self):
        aklog_info(self.device_name_log + 'clear_logs_by_ssh')
        self.exec_command_by_ssh('logcat -G 2M', 'logcat -c')

    def clear_logs_by_tln(self):
        aklog_info(self.device_name_log + 'clear_logs_by_tln')
        self.command_by_tln_or_ssh('rm /tmp/Messages.* -f')
        self.command_by_tln_or_ssh('echo "" > /tmp/Messages')

    def clear_logs_by_tln_or_ssh(self):
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
        aklog_info(self.device_name_log + str(dclient_msgs))
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
        if ssh_log:
            return True
        else:
            aklog_info(self.device_name_log + '%s 日志不存在' % flag)
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

    def get_system_log_by_tln_or_ssh(self):
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d'
        else:
            command = 'cat /tmp/Messages*'
        ssh_log = self.get_result_by_tln_or_ssh(command)
        return ssh_log

    def start_logs_by_interactive_tln_or_ssh(self, log_flag=None):
        """
        开始交互式获取设备log，需要配合save_log_to_result_dir_by_tln_or_ssh使用
        log_flag: 如果要同时过滤多组字段全部显示，可以在多组字段中间加 |，比如：relay1 state|relay2 state
        grep要加参数 -E， 比如:grep -E "relay1 state|relay2 state"
        """
        aklog_info(self.device_name_log + 'start_logs_by_interactive_tln_or_ssh: %s' % log_flag)
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

    def get_logs_by_interactive_tln_or_ssh(self):
        """交互式获取设备log，需要配合start_logs_by_interactive_tln_or_ssh使用"""
        aklog_info(self.device_name_log + 'get_logs_by_interactive_tln_or_ssh')
        if self.device_config.get_remote_connect_type() == 'ssh':
            ret = self.get_result_by_interactive_ssh_thread()
        else:
            ret = self.get_result_by_interactive_telnet_thread()
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

    def save_logs_to_result_dir_by_tln_or_ssh(self, case_name):
        """保存交互式获取到的log到测试结果目录下，save_logs_to_result_dir_by_tln_or_ssh"""
        aklog_info(self.device_name_log + 'start_logs_by_interactive_tln_or_ssh')
        if self.device_config.get_remote_connect_type() == 'ssh':
            ret = self.get_result_by_interactive_ssh_thread()
        else:
            ret = self.get_result_by_interactive_telnet_thread()
        results = ret.split('\n')
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file = '{}\\PhoneLog--{}--{}--{}.txt'.format(log_dir, case_name, self.device_name, log_time)
        File_process.create_dir(log_dir)
        with open(log_file, 'w') as f:
            f.writelines(results)

    # </editor-fold>

    # <editor-fold desc="其他">
    def click_display(self):
        # 点击display
        self.browser.click_btn_by_id('tMenu441')
        time.sleep(1)

    def click_arming(self):
        # 点击arming
        self.browser.click_btn_by_xpath('//*[@id="tablePage2Display"]/tbody/tr[6]/td[2]/div/div/ul/li[9]')
        time.sleep(1)

    def click_sos(self):
        # 点击sos
        self.browser.click_btn_by_xpath('//*[@id="tablePage1Display"]/tbody/tr[2]/td[2]/div/div/ul/li[10]')
        time.sleep(1)

    def click_area5(self):
        # 点击area5区域
        self.browser.click_btn_by_xpath('//*[@id="tablePage2Display"]/tbody/tr[6]/td[2]/div/input[1]')
        time.sleep(1)

    def click_homepage_area1(self):
        # 点击homepage_area1区域
        self.browser.click_btn_by_xpath('//*[@id="tablePage1Display"]/tbody/tr[2]/td[2]/div/input[1]')
        time.sleep(1)

    def open_sos(self):
        """设备网页打开sos操作"""
        self.click_phone()
        self.click_display()
        self.click_homepage_area1()
        self.click_sos()
        self.click_submit()
        time.sleep(1)
        self.browser.close_and_quit()

    def login_email_get_verificationCode(self, email_url, e_mail, passwd):
        """登录网易邮箱网页获取验证码"""
        aklog_info(self.device_name_log + 'login_email')
        self.browser.visit_url(email_url)
        self.browser.click_btn_by_id("switchAccountLogin")
        time.sleep(2)
        self.browser.driver.switch_to.frame(0)
        self.browser.input_edit_by_name("email", e_mail)
        self.browser.input_edit_by_name("password", passwd)
        time.sleep(2)
        self.browser.click_btn_by_id("dologin")
        time.sleep(10)
        self.browser.click_btn_by_xpath(
            "//*[@id='_dvModuleContainer_mbox.ListModule_0']/div/div/div/div[3]/div[2]/div/div[2]/span")
        time.sleep(3)
        self.browser.driver.switch_to.frame(1)
        code = self.browser.get_value_by_xpath(
            '//*[@id="content"]/table/tbody/tr/td[2]/table/tbody/tr[4]/td[2]/table/tbody/tr[6]/td/table/tbody/'
            'tr/td[2]/table/tbody/tr[5]/td/label')
        self.browser.close_and_quit()
        return code

    def login_email_get_password(self, email_url, Email, passwd):
        """登录网易邮箱网页获取密码"""
        aklog_info(self.device_name_log + 'login_email')
        self.browser.visit_url(email_url)
        time.sleep(5)
        self.browser.click_btn_by_id("switchAccountLogin")
        time.sleep(3)
        self.browser.driver.switch_to.frame(0)
        self.browser.input_edit_by_name("email", Email)
        self.browser.input_edit_by_name("password", passwd)
        time.sleep(2)
        self.browser.click_btn_by_id("dologin")
        time.sleep(10)
        self.browser.click_btn_by_xpath(
            "//*[@id='_dvModuleContainer_mbox.ListModule_0']/div/div/div/div[3]/div[2]/div/div[2]/span")
        time.sleep(3)
        self.browser.driver.switch_to.frame(1)
        # code = self.browser.get_value_by_xpath(
        #     '//*[@id="content"]/table/tbody/tr/td[2]/table/tbody/tr[4]/td[2]/table/tbody/tr[6]/td/table/tbody/'
        #     'tr/td[2]/table/tbody/tr[8]/td/label')
        self.browser.close_and_quit()

    def login_email_change_password(self, email_url, email, email_passwd, new_passwd, confirm_passwd):
        """登录网易126邮箱网页修改密码"""
        aklog_info(self.device_name_log + 'login_email')
        self.browser.visit_url(email_url)
        time.sleep(5)
        # self.browser.click_btn_by_id("switchAccountLogin")
        time.sleep(3)
        self.browser.driver.switch_to.frame(0)
        self.browser.input_edit_by_name("email", email)
        self.browser.input_edit_by_name("password", email_passwd)
        time.sleep(2)
        self.browser.click_btn_by_id("dologin")
        time.sleep(10)
        self.browser.click_btn_by_id('_mail_component_140_140')
        time.sleep(3)
        self.browser.click_btn_by_xpath(
            "/html/body/div[2]/div[1]/div[2]/div/div/div/div[4]/div[2]/div/div[2]/span")
        time.sleep(15)
        self.browser.driver.switch_to.frame(2)
        time.sleep(15)
        self.browser.click_btn_by_xpath(
            '/html/body/div/table/tbody/tr/td[2]/table/tbody/tr[4]/td[2]/table/tbody/'
            'tr[6]/td/table/tbody/tr/td[2]/table/tbody/tr[5]/td/a')
        time.sleep(10)
        self.browser.driver.switch_to.default_content()
        time.sleep(5)
        self.browser.click_btn_by_xpath('/html/body/div[9]/div/div[3]/a[2]')
        time.sleep(10)
        windows = self.browser.driver.window_handles
        print(windows)
        self.browser.driver.switch_to.window(windows[-1])
        self.browser.input_edit_by_id("New", new_passwd)
        self.browser.input_edit_by_id("Confirm", confirm_passwd)
        time.sleep(2)
        self.browser.click_btn_by_id("submit")

    # </editor-fold>


if __name__ == '__main__':
    device_info = {'device_name': 'IT82', 'ip': '192.168.88.103'}
    device_config = config_parse_device_config('config_IT82_NORMAL')
    param_put_browser_headless_enable(True)  # 是否开启浏览器无头模式
    web = web_device_NORMAL()
    web.init_without_start(libbrowser(device_info, device_config))
    web.start_adb_server_by_ssh('192.168.88.103:5654')
