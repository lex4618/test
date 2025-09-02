#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
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

from requests import ConnectTimeout
from akcommon_define import *


class web_son_device_NORMAL(web_device_NORMAL):

    # region 封装
    def menu_info_file_to_dict(self, file_path):
        menu_dict = {}
        cur_device = None
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # 逐行读取
                line = line.strip()
                if line.endswith(','):
                    # 去除最后的逗号
                    line = line[:-1]
                if line.startswith('[') and line.endswith(']'):
                    cur_device = line[1:-1]
                    menu_dict[cur_device] = {}
                elif ':' in line:
                    # 目录键值对
                    key, value = line.split(':', 1)
                    key = key.strip().strip("'").strip('"')
                    value = eval(value.strip())
                    menu_dict[cur_device][key] = value
        return menu_dict

    def web_refresh(self, force=True):
        self.browser.web_refresh(force=force)

    def web_get_table_row_values_dict(self, colname_index, colvalue=None, tableindex=1):
        """
        传入列名, 索引, 获取整行数据.
        """
        headers = self.browser.get_values_by_xpath(f'(//tbody)[{tableindex}]//tr[1]/td')
        if colname_index not in headers:
            aklog_error(f'未找到表的列: {colname_index}')
            return {}
        tdindex = headers.index(colname_index)

        tr_count = self.browser.get_elements_visible('xpath', f'(//tbody)[{tableindex}]//tr')
        if tr_count:
            tr_count = len(tr_count)
            for i in range(2, tr_count + 1):
                datalist = self.browser.get_values_by_xpath(f'(//tbody)[{tableindex}]//tr[{i}]/td', printlog=False)
                try:
                    if datalist[tdindex] == colvalue:
                        return dict(zip(headers, datalist))
                except:
                    continue
        aklog_error(f'未找到表: {colname_index} = {colvalue} 数据')
        return {}

    def web_get_table_current_page(self, tablename=1):
        return self.read_config('tCurPageInfo')

    def select_table_row_by_index(self, indexlist=1, checkboxid='cCheck'):
        """基础接口, 选择表格的行勾选"""
        if indexlist == 'All' or indexlist == ['All']:
            self.write_config_by_name(checkboxid + '0', True)
        else:
            if type(indexlist) == str or type(indexlist) == int:
                self.write_config_by_name(checkboxid + str(indexlist), True)
            else:
                for i in indexlist:
                    self.write_config_by_name(checkboxid + str(i), True)

    def deselect_table_row_by_index(self, indexlist: list = 1):
        """基础接口, 取消选择表格的行勾选"""
        if indexlist == 'All' or indexlist == ['All']:
            self.write_config_by_name('cCheck0', False)
        else:
            if type(indexlist) == str or type(indexlist) == int:
                self.write_config_by_name('cCheck%s' % indexlist, False)
            else:
                for i in indexlist:
                    self.write_config_by_name('cCheck%s' % i, False)

    def enable_transfer(self, titlename_or_id, enablelist=[]):
        """
        表格标题文本或者table标签xpath路径
        """
        try:
            if '//' in titlename_or_id:
                xpath = titlename_or_id
                enable_xpath = xpath + '//*[contains(@name, "Enable")]//option'
                disable_btn = xpath + '//*[@value="<<"]'
                enable_btn = xpath + '//*[@value=">>"]'
            else:
                xpath = './/*[@class="div_head"]//*[normalize-space(text())="{}"]/../..//table[.//*[@class="Nice_Btn"]]'.format(
                    titlename_or_id, titlename_or_id)
                enable_xpath = xpath + '//*[contains(@name, "Enable")]//option'
                disable_btn = xpath + '//*[@value="<<"]'
                enable_btn = xpath + '//*[@value=">>"]'
            eles = self.get_elements(enable_xpath)
            if eles:
                for ele in eles:
                    ele.click()
                    self.click(disable_btn)
            first_disabled = xpath + '//*[contains(@name, "All") or contains(@name, "Disable")]//option'
            if self.get_element(first_disabled).is_selected():
                self.click(first_disabled)
            for name in enablelist:
                self.web_get_alert_text_and_confirm()
                en_xpath = xpath + '//*[contains(@name, "All") or contains(@name, "Disable")]//option[contains(text(), "{}")]'.format(
                    name)
                self.click(en_xpath)
                self.click(enable_btn)
            self.web_get_alert_text_and_confirm()
        except:
            aklog_error('修改transfer: {} 失败!'.format(titlename_or_id))
            aklog_debug(traceback.format_exc())
            return False

    def enter_password_in_login_page(self, username, password):
        """
        登录界面输入账号, 密码.
        """
        for i in range(2):
            self.write_config_by_name('username', username)
            self.write_config_by_name('password', password)
            self.click('Login')
            if self.is_exist('tPageLogOut', wait_time=1):
                return True
            resultlabel = self.browser.get_value_by_id('cLoginResult')
            # resultlabel显示为'', 则认为是网页登录超时了. 可能设备调往了.
            if resultlabel.strip() == '':
                aklog_warn("可能网页登录时设备网络异常, 重试..")
                self.wait_wan_connnected()
                continue
            else:
                aklog_warn('网页登录提示: {}'.format(resultlabel))
                return False

    def modify_password_when_login(self):
        """login网页后, 若有弹窗就修改密码, 否则到security页面修改密码. admin -> Aa12345678"""
        aft_pwd = self.device_config.get_web_admin_password_changed()  # Aa12345678
        if self.is_exist('.//*[@id="cModifyPage_NewPasswd" or @id="cWebPwdModifyNewPasswd"]'):
            # 恢复出场后修改密码
            self.write_config_by_name('.//*[@id="cModifyPage_NewPasswd" or @id="cWebPwdModifyNewPasswd"]', aft_pwd)
            self.write_config_by_name('.//*[@id="cWebPwdModifyConfirmPasswd" or @id="cModifyPage_ConfirmPasswd"]',
                                      aft_pwd)
            self.click('.//*[@id="cModifyPage_Change" or @id="cChange"]')
            ret = self.web_get_alert_text_and_confirm()
            self.web_admin_pwd = aft_pwd
            aklog_info(ret)
            # if self.is_exist('//*[@id="Config.Settings.SECURITY.Question1"]/div[1]/div'):
            #     self.click(
            #         './/*[@class="ak-common-modal-footer-btn ak-common-modal-footer-cancel ant-btn ant-btn-danger"]')
        else:
            # security界面修改密码
            self.login_status = True  # 有设备被人工取消掉了首页的密码弹窗, login_status还是False, 会导致无法进入menu_expand
            self.web_pwd_modify('admin', aft_pwd)

    def login(self, url=None, raise_enable=True, remember=None, wait_connect=True):
        """登录网页"""
        aklog_info()
        if wait_connect:
            self.wait_wan_connected()  # 2024.12.20 如R25, 恢复出厂以后, 会获取到IP并刷新到登录界面, 后面会有一段时间网页无法访问, 之后才可以访问.
        if not url:
            url = 'http://%s' % self.device_ip
            self.browser.visit_url('http://%s' % self.device_ip)
        else:
            if url.endswith('.jpg') or url.endswith('.cgi'):
                url = 'http://%s' % self.device_ip
            elif url.endswith('8849'):
                url = 'http://%s' % self.device_ip
            self.browser.visit_url(url)
        for i in range(5):
            self.web_refresh(force=False)
            if self.is_exist('//*[@id="Login"]'):
                # 登录页面
                if i == 1:
                    password = self.device_config.get_web_admin_passwd()
                else:
                    password = self.device_config.get_web_admin_password_changed()
                self.enter_password_in_login_page('admin', password)
                alert = self.web_get_alert_text_and_confirm()
                if alert and 'limit' in alert.lower():
                    if i == 4:
                        aklog_error('登录网页失败多次, 停止登录!!!!')
                        if raise_enable:
                            self.browser_close_and_quit()
                            time.sleep(2)
                            raise RuntimeError
                        else:
                            return False
                    else:
                        aklog_error('网页密码登录失败多次, 需要等待3分钟!!')
                        time.sleep(190)
                        continue
                else:
                    if self.is_exist('tPageLogOut'):
                        self.web_admin_pwd = password

                        # 登录成功后, 判断是否需要修改密码, 否则开始下次循环判断是否登录成功
                        if password == self.device_config.get_web_admin_passwd():
                            aklog_info('网页密码为默认值, 需要修改..')
                            time.sleep(1)
                            self.modify_password_when_login()
                            # 修改密码成功后,判断是否需要填写密保问题
                            if self.is_exist(
                                    '//*[@id="divModifyQuestionPage_SetSecurityQuestion" or @id="securityQuestion_Panel"]'):
                                self.click('//*[@id="divModifyQuestionPage_cancel" or @id="cSecurityQuestion_Ignore"]')
                            continue
                        else:
                            if not self.is_exist('tMenu10') and self.is_exist(
                                    './/*[@id="tDeviceManagementLabel" or @id="tDevicecontrol"]'):
                                # 新版本首页页面
                                self.click('.//*[@id="tDeviceManagementLabel" or @id="tDevicecontrol"]')
                            self.login_status = True
                            aklog_info('登录网页成功')
                            return True
                    else:
                        if password == self.device_config.get_web_admin_passwd():
                            aklog_warn('使用admin也登录失败!!!!!')
                            self.screen_shot()
                        aklog_error('网页密码: {} 登录失败, 尝试重新登录!!!'.format(password))
                        sleep(1)
                        continue
            else:
                # 没有在登录界面的话, 就判断是否登录成功
                if self.is_exist('tPageLogOut'):
                    if not self.is_exist('tMenu10') and self.is_exist(
                            './/*[@id="tDeviceManagementLabel" or @id="tDevicecontrol"]'):
                        # 新版本首页页面
                        self.click('.//*[@id="tDeviceManagementLabel" or @id="tDevicecontrol"]')
                    self.login_status = True
                    aklog_info('登录网页成功')
                    return True
        aklog_error(self.device_name_log + '登录网页 %s 失败' % url)
        aklog_error_tag(self.device_name_log + '登录网页 %s 失败' % url)
        self.browser.screen_shot()
        self.login_status = False
        if raise_enable:
            self.browser_close_and_quit()
            time.sleep(2)
            raise RuntimeError
        else:
            return False

    def retry_login(self, modify_default_pwd=True, raise_enable=True):
        """
        重新打开浏览器, 重新登录
        """
        aklog_info('重新打开浏览器, 重新登录')
        for j in range(3):
            current_url = self.browser.get_current_url()
            self.browser.close_and_quit()
            self.browser.init()
            if self.login(url=current_url, raise_enable=raise_enable):
                return True

    def get_element(self, id_xpath, visible=True, log=True):
        """
        id+name+xpath定位.   text暂时不支持.  会影响如R20的登录
        """
        aklog_debug()
        if id_xpath.startswith('./') or id_xpath.startswith('/'):
            try:
                if visible:
                    element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                        EC.visibility_of_element_located((By.XPATH, id_xpath)))
                else:
                    element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                        EC.presence_of_element_located((By.XPATH, id_xpath)))
                return element
            except:
                aklog_error('Error: 未找到控件: {}'.format(id_xpath))
                return None
        else:
            id_xpath = './/*[@id="{}" or @name="{}"]'.format(id_xpath, id_xpath)
            try:
                if visible:
                    element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                        EC.visibility_of_element_located((By.XPATH, id_xpath)))
                else:
                    element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                        EC.presence_of_element_located((By.XPATH, id_xpath)))
                return element
            except:
                aklog_error('Error: 未找到控件: {}'.format(id_xpath))
                return None

    def get_elements(self, id_xpath, visible=True):
        if '//' not in id_xpath:
            id_xpath = './/*[@id="{}" or @name="{}"]'.format(id_xpath, id_xpath)
        try:
            if visible:
                element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                    EC.visibility_of_any_elements_located((By.XPATH, id_xpath)))
            else:
                element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                    EC.presence_of_all_elements_located((By.XPATH, id_xpath)))
            return element
        except:
            aklog_error('Error: 未找到控件: {}'.format(id_xpath))
            return None

    def get_values_by_same_prefix_id(self, eleid):
        aklog_debug()
        return self.browser.get_values_by_same_prefix_id(eleid)

    def get_option_list(self, eleid):
        aklog_debug()
        if eleid.startswith('(/') or eleid.startswith('/'):
            ret = self.get_select_options_list_by_xpath(eleid)
            return ret
        ret = self.get_select_options_list_by_id(eleid)
        if not ret:
            return self.get_select_options_list_by_name(eleid)
        else:
            return ret

    def go_to_page(self, page=1):
        self.write_config_by_name('tGoToPage', page)
        self.click('tGoToPageBtn')
        self.wait_process_finished()

    def get_xpath_by_text(self, text, prefix='//*['):
        """
        支持 |
        """
        if '//' in text or (text.startswith('/') or text.startswith('(/')):
            return text
        if '|' in text:
            list1 = text.split('|')
            list1 = [i.strip() for i in list1 if i.strip()]
            xpath = prefix
            for i in list1:
                xpath += 'normalize-space(text())="{}"'.format(i)
                if i != list1[-1]:
                    xpath += ' or '
            xpath = xpath + ']'
        else:
            xpath = '//*[normalize-space(text())="{}"]'.format(text)
        return xpath

    def get_tag(self, ele):
        if ele:
            return ele.tag_name
        else:
            return

    def adapt_element(self, id_name_xpath, driver, timeout):
        """
        id, name, xpath定位.
        支持 |
        """
        if '//' in id_name_xpath:
            xpath = id_name_xpath
        else:
            if '|' in id_name_xpath:
                xpath = './/*['
                list1 = id_name_xpath.split('|')
                list1 = [i.strip() for i in list1]
                for i in list1:
                    xpath += '@id="{}" or @name="{}"'.format(i, i)
                    if i != list1[-1]:
                        xpath = xpath + ' or '
                xpath += ']'
            else:
                xpath = './/*[@id="%s" or @name="%s"]' % (id_name_xpath, id_name_xpath)
        try:
            ele = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except:
            # 不报错, 避免影响后续的释放恢复动作.
            return False
        else:
            return ele

    def write_config_by_name(self, id_name, value, timeout=5, log=True):
        """
        id_name: 支持 | 匹配id和name
        value: select下拉框: 支持|, 支持无视大小写. 支持option value 定位
        """

        if log:
            aklog_debug()
        if value is None:
            aklog_info('write config value: None, Skip...')
            return True
        ele = self.adapt_element(id_name, self.browser.driver, timeout)
        if not ele:
            aklog_error('WriteConfig 失败!! 未找到控件: %s' % id_name)
            return False
        if not ele.is_enabled():
            aklog_error('WriteConfig 失败, 控件: %s 不可编辑状态!' % id_name)
            self.screen_shot()
            return False
        if self.read_config(id_name) == value:
            return True
        tag = self.get_tag(ele)
        try:
            self.browser.driver.execute_script("arguments[0].scrollIntoView();", ele)
        except:
            pass
        if tag not in ['select', 'input', 'textarea']:
            aklog_error('接口未封装范围: id_name: %s  tag: %s' % (id_name, tag))
            return False
        else:
            try:
                if tag == 'select':
                    if value is True or value is False:
                        value = 'Enabled' if value else 'Disabled'
                    else:
                        if type(value) == str:
                            value = value.strip()
                        elif type(value) == int:
                            value = str(value)
                    select = Select(ele)
                    select_list = [i.text.strip() for i in select.options]
                    # 无视下拉框选项的大小写
                    lower_case_select_list = [i.text.strip().lower() for i in select.options]
                    if '|' in value:
                        valuelist = [i.strip() for i in value.split('|')]
                        for tvalue in valuelist:
                            if tvalue.lower() in lower_case_select_list:
                                for i in select_list:
                                    if i.lower() == tvalue.lower():
                                        value = i
                                        break
                        select.select_by_visible_text(value)
                    elif value.lower() in lower_case_select_list:
                        if value not in select_list:
                            for i in select_list:
                                if i.lower() == value.lower():
                                    value = i
                                    break
                        select.select_by_visible_text(value)
                    else:
                        select.select_by_value(value)
                elif tag in ['input', 'textarea']:
                    if ele.get_attribute('type') in ('checkbox', 'radio', 'ratio'):
                        if value is False or str(value) == '0' or value in ('Disabled', 'Disable', 'OFF'):
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
                                self.click(label_xpath)
                    elif ele.get_attribute('class') == 'select_value':
                        # web 2.0下拉框不是select标签，需要用点击方式选择
                        self.browser.click_by_js(ele)
                        if type(value) != int and value in ['Enabled', 'ON', 'On', 'on', 'enabled', True]:
                            # 2.8及之前版本都是 Enabled, ON的开关下拉框
                            # 3.1及之后开关变成勾选框
                            option_ele_xpath = "//input[@id='%s' or @name='%s']/..//*[normalize-space(text())='ON' or normalize-space(text())='Enabled']" % (
                                id_name, id_name)
                        elif type(value) != int and value in ['Disabled', 'OFF', 'Off', 'off', 'disabled', False]:
                            # 2.8及之前版本都是 Enabled, ON的开关下拉框
                            # 3.1及之后开关变成勾选框
                            option_ele_xpath = "//input[@id='%s' or @name='%s']/..//*[normalize-space(text())='OFF' or text()='Disabled']" % (
                                id_name, id_name)
                        else:
                            value = str(value)
                            if '|' in value:
                                valuelist = [i.strip() for i in value.split('|')]
                                prefix = "//input[@id='%s' or @name='%s']/..//*" % (id_name, id_name)
                                substr = '['
                                for value in valuelist:
                                    substr += " normalize-space(text())='%s' or @option_value='%s' " % (value,
                                                                                                        value) + 'or'
                                substr = substr.rstrip('or').strip(' ')
                                substr += ']'
                                option_ele_xpath = prefix + substr
                            else:
                                option_ele_xpath = "//input[@id='%s' or @name='%s']/..//*[normalize-space(text())='%s' or @option_value='%s']" \
                                                   % (id_name, id_name, value, value)

                        option_ele = self.adapt_element(option_ele_xpath, self.browser.driver, timeout)
                        self.browser.scroll_into_view_by_js(option_ele)
                        self.browser.click_by_js(option_ele)
                    elif ele.get_attribute('class') == 'multiple_selected_value':
                        # 输入下拉框. 如Floor No.
                        self.browser.click_by_js(ele)
                        if type(value) in [str, int]:
                            value = [value]
                        for i in value:
                            option_ele_xpath = '//input[@id="%s" or @name="%s"]/..//li[normalize-space(text())="%s" or @value="%s"]/input' \
                                               % (id_name, id_name, i, i)
                            option_ele = self.adapt_element(option_ele_xpath, self.browser.driver, timeout)
                            self.browser.scroll_into_view_by_js(option_ele)
                            self.browser.click_by_js(option_ele)
                    else:
                        ele.clear()
                        ele.send_keys(value)
            except:
                aklog_error('Write Config: %s-->%s失败' % (id_name, value))
                aklog_debug(traceback.format_exc())
                return False
            else:
                return True

    def read_config_by_name(self, id_name, timeout=5):
        """
        封装获取大部分网页控件的显示值.
        ps: 下拉框类型的返回其翻译值. 非value
        """
        ele = self.adapt_element(id_name, self.browser.driver, timeout)
        if not ele:
            aklog_error('Read Config: 未找到控件: %s' % id_name)
        tag = self.get_tag(ele)
        if tag is None:
            return None
        if tag == 'select':
            select = Select(ele)
            select_dict = dict(
                zip([i.get_attribute('value') for i in select.options], [i.text for i in select.options]))
            value = ele.get_attribute('value')
            aklog_debug('[' + self.device_name + '] ' + "read config: %s=%s" % (id_name, select_dict.get(value)))
            return select_dict[value]
        elif tag in ['input', 'textarea']:
            if ele.get_attribute('type') == 'checkbox':  # 复选框
                aklog_debug('[' + self.device_name + '] ' + "read config: %s=%s" % (id_name, ele.is_selected()))
                return ele.is_selected()
            elif ele.get_attribute('type') == 'radio':  # 单选框
                aklog_debug('[' + self.device_name + '] ' + "read config: %s=%s" % (id_name, ele.is_selected()))
                return ele.is_selected()
            elif ele.get_attribute('class') == 'select_value':
                # web 2.0下拉框不是select标签
                ele_xpath = "//input[@id='%s' or @name='%s']/../input[1]" % (id_name, id_name)
                ele = self.adapt_element(ele_xpath, self.browser.driver, timeout)
                aklog_debug('read config: {}, value is : {}'.format(id_name, ele.get_attribute('value')))
            return ele.get_attribute('value')
        elif tag == 'label' or tag == 'lable' or tag == 'td':
            aklog_debug('[' + self.device_name + '] ' + "read config: %s=%s" % (id_name, ele.text))
            return ele.text
        else:
            aklog_error('接口未封装范围: id_name: %s  tag: %s' % (id_name, tag))
            return False

    def judge_input_int_range(self, id_name, write_data, min, max):
        """
        封装测试, 输入框有效范围是 min~ max
        eg:
            测试IP port有效范围是整数, 范围1~65535
        """
        write_data = str(write_data)
        self.write_config_by_name(id_name, write_data)
        self.click_submit()
        if write_data.isdigit() and int(write_data) in range(int(min), int(max) + 1):
            self.browser.web_refresh()
            ret = self.read_config_by_name(id_name)
            if not ret:
                aklog_error('元素: %s 输入了 %s 保存失败!' % (id_name, write_data))
            return ret == write_data
        else:
            ret = self.judge_is_note_warning()
            if not ret:
                aklog_info('元素: %s 输入了 %s, 不在有效范围内, 没有报错!' % (id_name, write_data))
            return ret

    def is_exist(self, id_or_text, wait_time=3, log=True):
        """
        id, name, 翻译
        """
        if '//' not in id_or_text:
            if '|' in id_or_text:
                xpath1 = './/*['
                list1 = id_or_text.split('|')
                list1 = [i.strip() for i in list1]
                for i in list1:
                    xpath1 += '@id="{}" or @name="{}" or normalize-space(text())="{}"'.format(i, i, i)
                    if i != list1[-1]:
                        xpath1 = xpath1 + ' or '
                xpath1 += ']'
            else:
                xpath1 = './/*[@id="{}" or @name="{}" or normalize-space(text())="{}"]'.format(id_or_text, id_or_text,
                                                                                               id_or_text)
        else:
            xpath1 = id_or_text
        return self.browser.is_exist_and_visible_ele_by_xpath(xpath1, wait_time=wait_time)

    def is_contains_text(self, text, wait_time=3):
        if '|' in text:
            list1 = text.split('|')
            list1 = [i.strip() for i in list1 if i.strip()]
            prefix = '//*['
            for i in list1:
                prefix += 'contains(text(), "{}")'.format(i)
                if i != list1[-1]:
                    prefix += ' or '
            prefix = prefix + ']'
            xpath = prefix
        else:
            xpath = './/*[contains(text(), "{}")]'.format(text)
        return self.browser.is_exist_and_visible_ele_by_xpath(xpath, wait_time=wait_time)

    def is_not_exist(self, id_or_text, wait_time=3):
        aklog_info()
        return self.browser.is_ele_gone(id_or_text, wait_time)

    def click(self, id_xpath, sec=0.2, visible=True):
        """
        id+name+name定位.   text暂时不支持.  会影响如R20的登录
        """
        aklog_debug()
        ele = self.get_element(id_xpath, visible=visible)
        try:
            self.browser.driver.execute_script("arguments[0].scrollIntoView();", ele)
        except:
            pass
        if ele:
            try:
                ele.click()
            except:
                try:
                    self.browser.driver.execute_script("arguments[0].click();", ele)  # 很多setting界面元素被上一层挡住
                    return True
                except:
                    aklog_error('Error: 找到元素, 但无法点击!')
                    return False
            time.sleep(sec)
            return True
        else:
            aklog_error('Error: 未找到元素, 无法点击!')
            return False

    def click_submit(self, accept=True):
        super().click_submit(accept)

    def get_pcap_file(self):
        """返回导出的pcap文件路径"""
        return self.device_config.get_export_pcap_file_path()

    def get_download_dir(self):
        return self.device_config.get_chrome_download_dir()

    def wait_process_finished(self):
        """ 封装: 等待网页processing提示消失"""
        aklog_debug()
        time.sleep(2)
        for i in range(0, 10):
            if self.browser.is_ele_gone('tPhoneUsingStatus'):
                break
            else:
                aklog_info('Processing, please wait...')
                time.sleep(2)

    def web_import(self, enter_func, file_widget, import_btn, file, check_text=True):
        aklog_info()
        enter_func()
        self.browser.upload_file_by_name(file_widget, file)
        self.click(import_btn)
        time.sleep(2)
        self.browser.alert_confirm_accept()
        if check_text:
            for i in range(0, 10):
                value = self.browser.get_alert_text()
                if value and ("success" in value):
                    self.browser.alert_confirm_accept()
                    aklog_info('导入文件完成')
                    return True
                elif i < 9:
                    ele = self.get_element('tShowForAutoP')
                    if ele and ele.text and 'success' in ele.text:
                        if self.is_exist('ConfigReboot'):
                            self.click('ConfigReboot')
                            sleep(15)
                            self.wait_wan_connected()
                            self.login()
                            return True
                        time.sleep(5)
                        aklog_info('导入文件完成')
                        return True
                    else:
                        if self.is_exist('ConfigReboot'):
                            self.click('ConfigReboot')
                            sleep(15)
                            self.wait_wan_connected()
                            self.login()
                            return True
                        try:
                            if self.get_element('tPhoneUsingStatus') and 'reboot' in self.get_element(
                                    'tPhoneUsingStatus').text.lower():
                                sleep(15)
                                self.wait_wan_connected()
                                sleep(15)
                                self.login()
                                return True
                        except:
                            pass
                        time.sleep(2)
                        continue
                else:
                    aklog_error('导入文件失败，请检查原因')
                    self.browser.screen_shot()
                    return False
        return True

    def web_export(self, enter_func, export_btn, filename):
        aklog_info()

        def check_file_exist(filename):
            if type(filename) == str:
                file_path = self.device_config.get_chrome_download_dir() + filename
                return os.path.exists(file_path)
            else:
                for i in filename:
                    file_path = self.device_config.get_chrome_download_dir() + i
                    if os.path.exists(file_path):
                        return True
                return False

        if type(filename) == str:
            file = self.device_config.get_chrome_download_dir() + filename
            File_process.remove_file(file)
        else:
            for i in filename:
                file = self.device_config.get_chrome_download_dir() + i
                File_process.remove_file(file)
        enter_func()
        if type(export_btn) == str:
            self.click(export_btn)
        else:
            # 如doorlog-->点击后, 选择xml, csv...
            self.write_config_by_name(export_btn[0], export_btn[1])
        time.sleep(2)
        for i in range(0, 20):
            if not check_file_exist(filename):
                aklog_debug('文件导出中...')
                time.sleep(3)
            else:
                time.sleep(3)
                aklog_info('{} 导出成功'.format(filename))
                return True
        aklog_error('文件导出失败, 截图当前页面')
        self.browser.screen_shot()
        return False

    def web_check_image_no_pure(self, xpath, percent=50, rgb_fix_range=20, file_name=None):
        """
        判断图片不是纯色
        """
        aklog_info()
        if file_name:
            TEMP_FILE = os.path.join(tempfile.gettempdir(), file_name)
        else:
            TEMP_FILE = os.path.join(tempfile.gettempdir(), "temp_screen.png")
        File_process.remove_file(TEMP_FILE)
        if hasattr(self, 'get_element'):
            ele = self.get_element(xpath)
        else:
            ele = self.browser.get_element_visible(By.XPATH, xpath)
        if not ele:
            aklog_error("不存在控件, 图片判断失败!!!!")
            return False
        else:
            ret = ele.screenshot(TEMP_FILE)
            if ret:
                ret = judge_no_pure_with_error_range(TEMP_FILE, percent=percent, rgb_error_range=rgb_fix_range)
                File_process.remove_file(TEMP_FILE)
                return ret

    def web_compare_image(self, xpath, pic, percent=0):
        """
        2025.5.21 废弃不用.  使用web_image_compare,    percent越高越相似
        pic可以是一张图片或者多张图片
        """
        aklog_info()
        TEMP_FILE = os.path.join(tempfile.gettempdir(), "temp_screen2.png")
        File_process.remove_file(TEMP_FILE)
        if hasattr(self, 'get_element'):
            ele = self.get_element(xpath)
        else:
            ele = self.browser.get_element_visible(By.XPATH, xpath)
        if not ele:
            aklog_error("不存在控件, 图片判断失败!!!!")
            return False
        else:
            ret = ele.screenshot(TEMP_FILE)
            if ret:
                ret = image_compare_after_convert_resolution(pic, TEMP_FILE, percent=percent)
                File_process.remove_file(TEMP_FILE)
                return ret

    def web_image_compare(self, xpath, image, percent=90, fx=None, fy=None, tx=None, ty=None, error_range=0):
        """
        2025.5.21 网页图片对比接口, percent越高要求越相似.
        percent: 可写90, 0.9
        image: 可对比多张备选图片
        error_range: 颜色误差, 0代表无误差, 尽量设置20以内.
        """
        aklog_info()
        TEMP_FILE = os.path.join(tempfile.gettempdir(), "temp_screen2.png")
        File_process.remove_file(TEMP_FILE)
        if param_get_browser_headless_enable():
            self.browser.driver.set_window_size(1920, 1080)  # init_headless
            sleep(1)
        if xpath.endswith('.png') or xpath.endswith('.jpg'):
            return intercom_compare_two_picture(xpath, image, percent, fx, fy, tx, ty, error_range)
        else:
            if hasattr(self, 'get_element'):
                ele = self.get_element(xpath)
            else:
                ele = self.browser.get_element_visible(By.XPATH, xpath)
            if not ele:
                aklog_error("不存在控件, 图片判断失败!!!!")
                return False
            else:
                ret = ele.screenshot(TEMP_FILE)
                if ret:
                    return intercom_compare_two_picture(TEMP_FILE, image, percent, fx, fy, tx, ty, error_range)

    def web_get_ele_pic_by_custom_size(self, xpath, start_x=0, start_y=0, end_x=0, end_y=0):
        TEMP_FILE = os.path.join(tempfile.gettempdir(), "temp_screen.png")
        File_process.remove_file(TEMP_FILE)
        if hasattr(self, 'get_element'):
            ele = self.get_element(xpath)
        else:
            ele = self.browser.get_element_visible(By.XPATH, xpath)
        if not ele:
            aklog_error("不存在控件, 图片判断失败!!!!")
            return False
        else:
            ele.screenshot(TEMP_FILE)

            if start_x and start_y and end_x and end_y:
                return True

            imp = Image_process(self.browser.driver)
            imp.get_temp_file_by_custom_size(start_x, start_y, end_x, end_y)

    def judge_is_wan_connected(self):
        """
        判断设备网络是否链接状态. 用于是否是重启状态检测.如reboot schedule功能
        """
        aklog_info()
        try:
            requests.get('http://%s' % self.device_ip, timeout=2, verify=False)
        except ConnectTimeout:
            pass
        else:
            return True
        try:
            requests.get('https://%s' % self.device_ip, timeout=2, verify=False)
        except ConnectTimeout:
            pass
        else:
            return True
        return False

    # endregion 封装

    # region 网页接口
    def browser_close_and_quit(self):
        super().browser_close_and_quit()
        # 2025.8.13 嵌入式门口机dropbear堆积出现的内存泄露， 待效果验证决定是否添加。
        if self.ssh:
            self.ssh.close()
        if self.tln:
            self.tln.close()

    def web_get_network_info(self):
        aklog_info()
        self.enter_status_basic()
        ip = self.read_config('cLANIPAddr')
        gateway = self.read_config('cLANGateWay')
        mask = self.read_config('cLANSubnetMask')
        dns1 = self.read_config('cPrimaryDNS')
        dns2 = self.read_config('cSecondryDNS')
        return {'ip': ip, 'gateway': gateway, 'mask': mask, 'dns1': dns1, 'dns2': dns2}

    def open_telnet_by_web(self):
        url = 'http://%s/fcgi/do?id=8848' % self.device_ip
        self.login()
        self.browser.visit_url(url)
        if self.get_element('cTelnetActive').get_attribute('type') == 'button':
            self.browser.click_btn_by_id('cTelnetActive')
        else:
            self.write_config('cTelnetActive', 'Enabled')
        ret = self.click_submit()
        time.sleep(3)
        return ret

    # region account-basic
    def register_sip(self, sip, sip_password, server_ip, server_port='5060', account_active='1', index=1,
                     transport='UDP', wait_register=True, server2='', server2_port='5060', outbound=False,
                     outbound1=None, outbound2=None, outbound1_port=None, outbound2_port=None,
                     nat=False, stun_server='', nat_port='3478'):
        aklog_info("register_sip, sip: %s, sip_password: %s, server_ip: %s, port： %s" % (
            sip, sip_password, server_ip, server_port))
        self.enter_web_account_basic()
        self.select_account_by_index(index)
        if account_active in ('1', True, 'Enabled', 1):
            active = True
        else:
            active = False
        self.write_config('cAccountActive', active)
        self.write_config('cDisplayLabel', sip)
        self.write_config('cDisplayName', sip)
        self.write_config('cRegisterName', sip)
        self.write_config('cUserName', sip)
        self.write_config('cPassword', sip_password)
        self.write_config('cFirstSIPServerAddr', server_ip)
        self.write_config('cFirstSIPServerPort', server_port)
        self.write_config('cAccountTransType', transport)
        self.write_config('cEnableOutbond', outbound)
        if outbound1:
            self.write_config('cOutbondProxyAddr', outbound1)
        if outbound2:
            self.write_config('cBakProxyAddr', outbound2)
        self.write_config('cOutbondProxyPort', outbound1_port)
        self.write_config('cBakProxyPort', outbound2_port)
        self.write_config('cEnableStun', nat)
        self.write_config('cStunServer', stun_server)
        self.write_config('cStunPort', nat_port)
        self.click_submit()
        if account_active in ('1', True, 'Enabled') and wait_register:
            sleep(3)
            return self.web_wait_registered()

    def web_wait_registered(self):
        """
        2022.6.1 等待accouNt-basic页面显示为registered
        """
        for i in range(5):
            self.web_refresh()
            time.sleep(1)
            ret = self.read_config('cAccountStatus')
            if ret is None:
                self.enter_web_account_basic()
            if ret == 'Registered':
                aklog_info('注册sip账号成功!!!')
                return True
            time.sleep(3)
        self.screen_shot()
        aklog_error('注册sip账号失败!!!')
        return False

    def web_judge_account_registered(self, index=1):
        aklog_info()
        self.enter_web_account_basic()
        self.select_account_by_index(index)
        return self.web_wait_registered()

    def web_enter_account_basic(self, index=1):
        aklog_info()
        self.enter_web_account_basic()
        self.select_account_by_index(index)

    def web_get_sip_display_name(self, index=1):
        aklog_info()
        self.enter_web_account_basic()
        self.select_account_by_index(index)
        return self.read_config('cDisplayName')

    def web_set_sip_display_name(self, name, index=1):
        aklog_info()
        self.enter_web_account_basic()
        self.select_account_by_index(index)
        self.write_config_by_name('cDisplayName', name)
        self.click_submit()

    def web_reset_sip_display_name(self, index=1):
        aklog_info()
        self.enter_web_account_basic()
        self.select_account_by_index(index)
        self.write_config_by_name('cDisplayName', '')
        self.click_submit()

    # endregion account-basic

    # region account-advanced
    def web_enter_account_advanced(self, index=1):
        """
        2024.6.5
        """
        aklog_info()
        self.enter_account_advanced()
        self.select_account_by_index(index)

    # endregion

    # region contacts-local contacts
    def web_enter_contact(self):
        aklog_info()
        return self.enter_local_book()

    def web_set_contacts_sort_by(self, sortby='Default'):
        aklog_info()
        self.web_enter_contact()
        if sortby.lower() == 'default':
            sortby = 0
        elif 'ascii' in sortby.lower():
            sortby = 1
        elif 'created' in sortby.lower():
            sortby = 2
        self.write_config_by_name('cSortMode', sortby)
        self.click_submit()

    def web_set_show_local_contact_only(self, enable=False):
        aklog_info()
        self.web_enter_contact()
        self.write_config_by_name('cShowLocalContactsOnly', enable)
        self.click_submit()

    # endregion local contacts

    # region network-advanced
    def web_enter_network_advanced(self):
        aklog_info()
        return self.enter_network_advanced()

    def web_set_control4_mode(self, enable=False):
        aklog_info()
        self.web_enter_network_advanced()
        self.write_config_by_name('cControl4Mode', enable)
        self.click_submit()
        self.web_get_alert_text_and_confirm()

    # endregion network-advanced

    def wait_for_web_reboot_finished(self, login=True):
        """
        用于等待网页reboot, reset结束: 在点击reboot后, 等待设备重启->获取到ip
        login: 重启后是否做登录网页操作.
        """
        if not self.wait_wan_disconnected(timeout=30):
            aklog_warn('设备未在30秒内重启')
            return False
        if not self.wait_wan_connected(timeout=self.device_config.get_reset_config_default_time()):
            aklog_warn('设备未在{}秒内启动'.format(self.device_config.get_reset_config_default_time()))
            return False

        sleep(20)
        cur_time = time.time()
        for i in range(15):
            if time.time() - cur_time > 120:
                break
            else:
                self.web_refresh(force=True)
                sleep(2)
                xpath1 = r'.//*[@id="Login"]'
                xpath2 = r'.//*[@id="tPageLogOut"]'
                if self.is_exist(xpath1):
                    aklog_info('设备重启结束, 在登录界面')
                    if login:
                        self.login()
                        self.enter_upgrade_basic()
                    return True
                elif self.is_exist('.//*[@id="cModifyPage_NewPasswd" or @id="cWebPwdModifyNewPasswd"]'):
                    if login:
                        self.login()
                        self.enter_upgrade_basic()
                    return True
                elif not self.is_exist(xpath2):
                    aklog_info('设备重启结束')
                    return True
        self.screen_shot()
        aklog_info('设备重启异常')
        return False

    def web_set_pnp(self, enable=False):
        aklog_info()
        self.enter_upgrade_advanced()
        self.write_config_by_name('cPNPConfig', enable)
        self.click_submit()

    # endregion 网页接口

    # region Telnet
    def web_open_ssh(self):
        self.enter_hide_page_8848()
        self.set_ssh_or_tln('1')

    def telnet(self, cmd):
        aklog_info()
        try:
            ret = self.get_result_by_tln_or_ssh(cmd)
            if ret is None:
                return ''
            return ret
        except:
            aklog_error('telnet命令出现异常!')
            aklog_debug(traceback.format_exc())
            return ''

    def get_value_by_ssh(self, command, print_result=True):
        """
        2025.8.15 lex: 改写逻辑, 减少is_connected开一个session后关闭, 之后马上执行exec_command容易出现channel close
        """
        aklog_debug()
        value = self.ssh.command_result(command)
        if value is not None:
            if print_result:
                aklog_debug('result: %s' % value)
            return value.encode('gbk', 'ignore').decode('gbk')
        else:
            self.ssh_login()  # web_open_ssh, web_open_telnet中, 各机型各自控制开启配置后多久可以telnet
            ret = self.ssh.is_connected()
            if not ret:
                aklog_error('telnet连接失败!!!')
                return ''
            value = self.ssh.command_result(command)
            if value:
                value = value.encode('gbk', 'ignore').decode('gbk')
            if print_result:
                aklog_debug('result: %s' % value)
            return value

    # endregion

    # region 进程检查
    """
    2025.7.30 检查对讲终端日常自动化的崩溃需求

    ps:    
        1. 在主动重启的接口如web_reboot, ui_reboot, reset, telnet(reboot)的地方设置标志位: param_put_reboot_process_flag(True), 
    用以只检查进程完整性, 不比对进程pid.
        2.  param_put_reboot_process_flag(False): 不需要主动调用, 会在setup前, teardown后主动恢复. 
            放在这位置也为了应对teardown, teardownclass中可能有的主动重启后被写了标志位, 下次测试的恢复. 
    """

    def intercom_get_process_column(self):
        """
        基础接口获取ps的列名 : PID USER STATE COMMAND
        """
        aklog_debug()
        ps_cmd = f'{self.device_config.ps_command} | grep "PID" | grep -v grep'
        title = self.telnet(ps_cmd)
        return re.findall(r'\w+', title)

    def intercom_get_process_pid_dict(self, checklist):
        """
        基础接口获取指定进程列表的pid.
        结合self.device_config.check_ps_list 使用
        return :
            {
                '/app/bin/api.fcgi': '1191',
                '/app/bin/vaMain': '1124'
            }
        """
        aklog_debug()
        retdict = {}
        try:
            PIDINDEX = self.intercom_get_process_column().index('PID')
        except:
            aklog_warn('ps未获取到PID索引')
            PIDINDEX = 0

        if type(checklist) == list:
            # 过滤那些不想看到进程, 只检查关键的进程.
            cmd = fr'{self.device_config.ps_command} | grep -vE "grep|dropbear|-sh|\["'
            ret = self.telnet(cmd).splitlines()
            for process in checklist:
                if process.lower() not in str(ret).lower():
                    aklog_error(f'{process} 进程不存在!')
                else:
                    for each in ret:
                        if process.lower() in each.lower():
                            retdict[process] = re.findall(r'\w+', each)[PIDINDEX]
            return retdict
        else:
            # 只想获取一个进程的时候
            process = checklist
            cmd = fr'{self.device_config.ps_command} | grep -i "{process}" | grep -v grep'
            ret = self.telnet(cmd)
            if not ret:
                aklog_debug(f'{process} 进程获取pid失败!')
            else:
                retdict[process] = re.findall(r'\w+', ret)[PIDINDEX]
            return retdict

    def intercom_get_process_pid_dict_until_completed(self, checklist, timeout=20):
        """
        基础接口: 若有一个进程退出未起来, 会影响到后续的比对. 在10秒内等待进程起来.
        结合self.device_config.check_ps_list 使用
        """
        aklog_debug()
        t1 = time.time()
        nowdict = {}
        for i in range(60):
            nowdict = self.intercom_get_process_pid_dict(checklist)
            if sorted(list(nowdict.keys())) == sorted(checklist):
                return nowdict
            else:
                if time.time() - t1 > timeout and i > 1:
                    aklog_error(f'{timeout}秒后设备进程启动都不完全!')
                    return nowdict
                else:
                    aklog_warn('进程未全部起来, 等待3秒重试...')
                    sleep(3)
                    continue
        aklog_error(f'设备进程启动都不完全!')
        return nowdict

    def intercom_get_first_process_dict(self):
        """
        只在所有套件开始的第一次获取进程状态. 需要获取到完整的进程状态.
        """
        aklog_debug()
        if not param_get_old_process_dict():
            checkpslist = self.device_config.check_ps_list
            nowdict = self.intercom_get_process_pid_dict_until_completed(checkpslist)
            param_put_old_process_dict(nowdict)

    def intercom_check_process_state(self):
        """
        对比测试前后的进程状态, 检查的进程在libconfig_机型/系列_NORMAL.py -- check_ps_list中定义.
        2025.7.30 检查对讲终端日常自动化的崩溃需求
        return: wrong_list为空,则是正常的. wrong_list有内容, 只是有问题的.

        1. 进程状态全局保存, 避免初始化过程中的问题导致的遗漏.
        2. 检查失败后, 保留新的进程状态. 需考虑某进程死掉未获取到pid, 影响到下次比对的情况.
        """
        aklog_info()
        wrong_list = []
        checkpslist = self.device_config.check_ps_list
        nowdict = self.intercom_get_process_pid_dict(checkpslist)

        # 1. 先检查当前进程是完整的
        complete_state = True
        for ps in checkpslist:
            if ps not in nowdict:
                complete_state = False
                aklog_error('进程: {} 检查失败, 进程不存在!'.format(ps))
                wrong_list.append('进程: {} 检查失败, 进程不存在!'.format(ps))

        # 如果碰到主动重启的, 不去做检查PID变化
        if param_get_reboot_process_flag():
            if not complete_state:
                # 进程状态不完整的等完整
                nowdict = self.intercom_get_process_pid_dict_until_completed(checkpslist)
            param_put_old_process_dict(nowdict)
            if not wrong_list:
                aklog_info('设备主动重启后, 检查进程完整.')
            else:
                aklog_error('设备主动重启后, 检查进程不完整!')
            return wrong_list

        # 2. 再检查进程pid变化
        append_all_list_info = False
        for pname, pid in nowdict.items():
            if pid != param_get_old_process_dict().get(pname):
                aklog_error(
                    '进程: {} 检查失败, 进程出现重启: 【{}】 -> 【{}】 !'.format(pname,
                                                                             param_get_old_process_dict().get(pname),
                                                                             pid))
                if not append_all_list_info:
                    append_all_list_info = True
                    wrong_list.append(f'检查进程信息: {";  ".join(checkpslist)}')
                wrong_list.append(
                    '进程: {} 检查失败, 进程出现重启: 【{}】 -> 【{}】 !'.format(pname,
                                                                             param_get_old_process_dict().get(pname),
                                                                             pid))

        if not complete_state:
            # 进程状态不完整的等完整
            nowdict = self.intercom_get_process_pid_dict_until_completed(checkpslist)
        param_put_old_process_dict(nowdict)
        if not wrong_list:
            aklog_info('设备检查进程正常!')
        else:
            aklog_error('检查检查进程失败!')
            title = self.telnet('uptime')
            aklog_info('【设备上电时间】:  {}'.format(title))
            wrong_list.append('【设备上电时间】:  {}'.format(title))
        return wrong_list

    # endregion


class NewTelnet:
    def __init__(self, ip, port=23, username='root', password='OjEEr3d%zyfc0', timeout=10):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.t = None

    def __del__(self):
        if self.t:
            self.t.close()

    def is_connected(self):
        """是否连接正常处于等待命令输入状态"""
        aklog_printf()
        if self.t is None:
            aklog_error('telnet连接还未建立')
            return False
        try:
            self.t.write(b'\n')
            index, match, output = self.t.expect([r'.*#\s$'.encode('utf-8')], timeout=2)
            if match is not None:
                aklog_info("telnet连接正常")
                return True
            else:
                aklog_error("telnet连接异常, 账号密码: {}:{}".format(self.username, self.password))
                return False
        except:
            aklog_error("telnet连接已关闭")
            return False

    def execute_cmd(self, command):
        aklog_info()
        self.t.write(command.encode() + b'\n')
        ret = self.t.expect([r'.*#\s*$'.encode()], timeout=10)[2].decode()
        list1 = ret.splitlines()
        return '\n'.join(list1[1:-1])

    def login(self):
        try:
            self.t = telnetlib.Telnet(host=self.ip, port=self.port, timeout=self.timeout)
        except:
            aklog_error('设备telnet链接失败!, 可能telnet配置未开启或者ssh方式')
            return None
        else:
            self.t.read_until(b'login:', timeout=10)
            self.t.write(self.username.encode('ascii') + b'\n')
            self.t.read_until(b'Password:', timeout=10)
            self.t.write(self.password.encode('ascii') + b'\n')
            time.sleep(1)
            command_result = self.t.read_very_eager().decode('ascii')
            if self.is_connected():
                return True
            return False
