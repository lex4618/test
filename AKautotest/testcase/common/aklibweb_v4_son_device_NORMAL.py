# -*- coding: utf-8 -*-
import re
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
from requests import ConnectTimeout
from requests.adapters import SSLError


class web_v4_son_device_NORMAL(web_v4_device_intercom_NORMAL):
    """
    2024.4.12 多加一层, 用于统一不同机型的接口名称.
    """
    menu_xpath_dict = {}

    # region 初始化相关
    def __init__(self):
        super().__init__()

    def get_tag(self, ele):
        if not ele:
            return False
        try:
            return ele.tag_name
        except:
            return False

    def adapt_element(self, id_name_xpath, driver, timeout, log_xpath=None):
        xpath = id_name_xpath if (
                id_name_xpath.startswith('/') or '//' in id_name_xpath) else './/*[@id="%s" or @name="%s"]' % (
            id_name_xpath, id_name_xpath)
        try:
            ele = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
            return ele
        except:
            if log_xpath:
                aklog_error('未找到元素: %s' % log_xpath)
            else:
                aklog_error('未找到元素: %s' % id_name_xpath)
            return None

    def get_download_dir(self):
        return self.device_config.get_chrome_download_dir()

    def get_xpath_by_text(self, text, prefix='//*['):
        '文本翻译中的 | ==> xpath定位'

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
            xpath = prefix + 'normalize-space(text())="{}"]'.format(text)
            # xpath = '//*[normalize-space(text())="{}"]'.format(text)
        return xpath

    def get_xpath_by_id(self, eleid, prefix='//*['):
        eleid = str(eleid)
        if '//' in eleid or (eleid.startswith('/') or eleid.startswith('(/')):
            return eleid
        if '|' in eleid:
            list1 = eleid.split('|')
            list1 = [i.strip() for i in list1 if i.strip()]
            xpath = prefix
            for i in list1:
                xpath += '@id="{}"'.format(i)
                if i != list1[-1]:
                    xpath += ' or '
            xpath = xpath + ']'
        else:
            xpath = prefix + '@id="{}"]'.format(eleid)
        return xpath

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

    def browser_close_and_quit(self):
        super().browser_close_and_quit()
        # 2025.8.13 嵌入式门口机dropbear堆积出现的内存泄露， 待效果验证决定是否添加。
        if self.ssh:
            self.ssh.close()
        if self.tln:
            self.tln.close()

    # endregion 初始化相关

    # region 网页通用操作API
    def get_translated_text(self, text):
        """从当前界面, 获取输入text的翻译, 以忽视大小写的影响， 空格仍是需要输入的。"""
        try:
            ret = self.browser.driver.find_element('xpath', '//html').text
            ret1 = re.search(r"(^$|\W+)" + "(" + text.replace(' ', r'\s*') + ")", ret, re.I)
            if ret1:
                try:
                    return ret1.group(2)
                except:
                    return text
            else:
                return text
        except:
            return text

    def click(self, text_xpath, prefixname=None, index=None):
        """
        翻译文本(支持|) 或者xpath
        1. 相同text + index: index从0开始
        2. text_xpath + prefix.
        """
        aklog_debug()
        if '//' in text_xpath or (text_xpath.startswith('/') or text_xpath.startswith('(/')):
            xpath = text_xpath
            ret = self.browser.click_btn_by_xpath(xpath, visible=False)
            return ret
        else:
            if prefixname:
                xpath1 = self.get_xpath_by_text(prefixname)
                xpath2 = self.get_xpath_by_text(text_xpath)
                xpath = f'{xpath1}/following-sibling::*{xpath2}'
                ret = self.browser.click_btn_by_xpath(xpath)
                return ret
            else:
                if index is None:
                    xpath = self.get_xpath_by_text(text_xpath)
                    ret = self.browser.click_btn_by_xpath(xpath)
                    return ret
                else:
                    xpath = self.get_xpath_by_text(text_xpath)
                    ele = self.get_elements(xpath)
                    self.browser.driver.execute_script("arguments[0].scrollIntoView();", ele[index])
                    if ele:
                        ele[index].click()
                    else:
                        aklog_error('未找到控件button: {}'.format(text_xpath))

    def click_submit(self, sec=0.2, accept=True):
        self.click(self.ele_info['page_submit_xpath'], sec)
        if accept:
            for i in range(2):
                # if self.browser.is_exist_alert():
                ret = self.web_get_alert_text_and_confirm()
                if ret:
                    aklog_warn('Submit tips: ' + ret)
                    continue
                if self.is_exist(r'.//*[@role="menu"]', wait_time=1):
                    if 'rgb(255, 86, 96)' not in self.browser.driver.page_source:
                        aklog_debug('click submit success')
                        return True
                    else:
                        aklog_error('网页保存失败, 有配置框显示红色违法输入!!!')
                        self.screen_shot()
                        return False
            aklog_error('click submit failed')
            return False

    def get_element(self, text_xpath, visible=True):
        aklog_info()
        text_xpath = self.get_web40_xpath(text_xpath)
        try:
            if visible:
                element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                    EC.visibility_of_element_located((By.XPATH, text_xpath)))
            else:
                element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                    EC.presence_of_element_located((By.XPATH, text_xpath)))
            return element
        except:
            aklog_error('Error: 未找到控件: {}'.format(text_xpath))
            return None

    def get_elements(self, text_xpath, visible=True):
        text_xpath = self.get_web40_xpath(text_xpath)
        try:
            if visible:
                element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                    EC.visibility_of_any_elements_located((By.XPATH, text_xpath)))
            else:
                element = WebDriverWait(self.browser.driver, self.browser.wait_time).until(
                    EC.presence_of_all_elements_located((By.XPATH, text_xpath)))
            return element
        except:
            aklog_error('Error: 未找到控件: {}'.format(text_xpath))
            return None

    def get_web40_xpath(self, xpath, index=None, subfix=''):
        """
        subfix: 修正量, 接后续的xpath表达式
        """
        if '//' in xpath or (xpath.startswith('/') or xpath.startswith('(/')):
            if index is not None:
                xpath = '(' + xpath + ')[{}]'.format(index + 1)
            return xpath
        if '->' in xpath:
            title, sub = [i.strip() for i in xpath.split('->')]
            prefix1 = self.get_xpath_by_text(title, prefix='//label[')
            prefix = self.get_xpath_by_text(sub, prefix=prefix1 + '/../..//*[')
            prefix = prefix + '/..//'
            eleXpath = prefix + 'input' + ' | ' + prefix + 'div[@role="combobox"]' + '|' + prefix + 'label[2][text()]'
            if index is None:
                return eleXpath + subfix
            else:
                return '(' + eleXpath + ')[{}]'.format(index + 1) + subfix
        else:
            if index is None:
                prefix = self.get_xpath_by_text(xpath)
                prefix = prefix + '/..//'
                eleXpath = prefix + 'input' + ' | ' + prefix + 'div[@role="combobox"]' + '|' + prefix + 'label[2][text()]'
                return eleXpath + subfix
            else:
                prefix = self.get_xpath_by_text(xpath)
                prefix = prefix + '/..//'
                eleXpath = '(' + prefix + 'input' + ' | ' + prefix + 'div[@role="combobox"]' + ' | ' + prefix + 'label[2][text()]' + ')[{}]'.format(
                    index + 1)
                return eleXpath + subfix

    def get_web40_element(self, xpath, index=None, timeout=5):
        if not isinstance(xpath, str):
            return xpath
        if ('//' in xpath or (xpath.startswith('/') or xpath.startswith('(/'))) and index is None:
            ele = self.adapt_element(xpath, self.browser.driver, timeout, xpath)
            return ele
        xpath = self.get_web40_xpath(xpath, index)
        ele = self.adapt_element(xpath, self.browser.driver, timeout, xpath)
        if not ele:
            return False
        tag = self.get_tag(ele)
        if tag not in ['input', 'div', 'label', 'span', 'td']:
            aklog_error(('接口未封装范围: xpath: %s  tag: %s' % (xpath, tag)))
            return False
        return ele

    def is_exist(self, xpath, wait_time=3, printlog=True):
        """
        翻译, xpath
        翻译支持: |
        """
        if not (xpath.startswith("./") or xpath.startswith("/")):
            xpath = self.get_xpath_by_text(xpath)
        return self.browser.is_exist_and_visible_ele_by_xpath(xpath, wait_time=wait_time, printlog=printlog)

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

    def is_exist_alert(self, wait_time=0.5, ret_text=False):
        """判断是否存在弹窗"""
        aklog_debug()
        if wait_time is None:
            wait_time = 0.5
        for i in range(2):
            try:
                alert = WebDriverWait(self.browser.driver, wait_time).until(EC.alert_is_present())
                alert_text = alert.text
                aklog_info('alert text is: %s' % alert_text)
                if not ret_text:
                    return True
                else:
                    return alert_text
            except UnexpectedAlertPresentException:
                sleep(0.5)
                continue
            except:
                aklog_info('alert is not exist')
                return False

    def judge_exist_title(self, titlename):
        """2022.7.7 页面下存在的小标题控件"""
        aklog_debug()
        xpath = r'.//*[@class="ak-conetnt-title"]//*[text()="{}"]'.format(titlename)
        return self.is_exist(xpath)

    def judge_is_red_by_xpath(self, xpath, index=None):
        """
        2022.6.6 判断控件是红色输入错误状态
        """
        aklog_info()
        ele = self.get_web40_element(xpath, index=index)
        if not ele:
            return False
        return 'color: rgb(255, 86, 96)' in ele.get_attribute(
            'style') or 'color: rgb(242, 146, 147)' in ele.get_attribute('style')

    def judge_red_tips_by_xpath(self, xpath, tips, timeout=2, index=None):
        """
        2022.7.5 鼠标悬浮在控件上， 并传入tips内容做对比
        """
        aklog_info()
        ele = self.get_web40_element(xpath, index=index, timeout=timeout)
        if not ele:
            aklog_error('未找到控件： %s' % xpath)
            return None
        self.browser.move_mouse_to_element(ele)
        sleep(1)
        return self.is_exist('.//*[@class="ak-tooltips-label" and text()="{}"]'.format(tips))

    def judge_input_int_range(self, xpath, data, min, max):
        """
        2022.6.7 判断输入框范围
        """
        aklog_info()
        write_data = str(data)
        xpath = self.get_web40_xpath(xpath)
        self.write_config(xpath, write_data)
        self.click_submit()
        if write_data.isdigit() and int(write_data) in range(int(min), int(max) + 1):
            self.web_refresh()
            ret = self.read_config(xpath)
            if not ret:
                aklog_error('元素: %s 输入了 %s 保存失败!' % (xpath, write_data))
            return ret == write_data
        else:
            ret = self.judge_is_red_by_xpath(xpath)
            if not ret:
                aklog_error('元素: %s 输入了 %s, 不在有效范围内, 没有报错!' % (xpath, write_data))
            return ret

    def read_config_by_name(self, xpath, timeout=5, index=None, printlog=True):
        if printlog:
            aklog_debug()
        ele = self.get_web40_element(xpath, index, timeout)
        if not ele:
            aklog_error('no found ele : %s' % xpath)
            return None
        tag = self.get_tag(ele)
        if tag == 'div':
            if ele.get_attribute('role') == 'combobox':
                value = ele.text
                if printlog:
                    aklog_debug('read_config : %s ,  value is : %s' % (xpath, value))
                return value
        elif tag == 'input':
            if ele.get_attribute('type') == 'checkbox':  # 复选框
                value = ele.is_selected()
                if printlog:
                    aklog_debug('read_config : %s ,  value is : %s' % (xpath, value))
                return value
            value = ele.get_attribute('value')
            if printlog:
                aklog_debug('read_config : %s ,  value is : %s' % (xpath, value))
            return value
        elif tag in ['label', 'lable', 'span', 'td']:
            value = ele.text
            if printlog:
                aklog_debug('read_config : %s ,  value is : %s' % (xpath, value))
            return value
        else:
            aklog_error('接口未封装范围: id_name: %s  tag: %s' % (xpath, tag))
            return None

    def write_time_config(self, xpathlist, value):
        """
        写日期相关控件的配置.
        xpathlist = [外层input,  点开控件后的内层input]
        """
        xpath1 = xpathlist[0]
        xpath2 = xpathlist[1]
        self.click(xpath1)
        sleep(1)
        self.write_config_by_name(xpath2, value)
        self.click(xpath1)

    def write_config_by_name(self, xpath, value=None, timeout=5, index=None, by_js=False, ignore_unit=False):
        """
        value : index从0开始
        value : 字符串,    字符串1 | 字符串2
        ignore_unit: 忽视下拉框选项的单位. 如只填入90,  在下拉框中的90s, 90 sec, 90second就会被选择.
        """
        if value is None:
            return
        aklog_debug()
        cur_value = self.read_config_by_name(xpath, index=index, printlog=False)
        if cur_value is None:
            return False
        elif cur_value == value:
            return True
        ele = self.get_web40_element(xpath, index, timeout)
        if not ele:
            aklog_error('write config失败!, 不存在控件: %s' % xpath)
            return False
        elif ele.size and ele.size.get('height') == 0:
            aklog_error('控件: %s 不可见!!' % xpath)
            return False
        tag = self.get_tag(ele)
        try:
            self.browser.driver.execute_script("arguments[0].scrollIntoView();", ele)
        except:
            pass
        try:
            if tag in ['input']:
                if ele.get_attribute('type') == 'checkbox':
                    if value in ['Enabled', 'Enable', 'Disable', 'Disabled', '1', 1, '0', 0]:
                        value = True if value in ['Enabled', 'Enable', '1', 1] else False
                    if ele.is_selected() != value:
                        try:
                            if by_js:
                                self.browser.driver.execute_script('arguments[0].click();', ele)
                            else:
                                try:
                                    ele.click()
                                except:
                                    self.browser.driver.execute_script('arguments[0].click();', ele)
                                time.sleep(0.1)
                        except:
                            aklog_error('write config失败!!!')
                            aklog_debug(traceback.format_exc())
                            return False
                else:
                    ele.send_keys(Keys.CONTROL, 'a')
                    time.sleep(0.1)
                    ele.send_keys(Keys.BACKSPACE)
                    time.sleep(0.1)
                    if ele.get_attribute('value'):
                        ele.clear()
                        time.sleep(0.1)
                    ele.send_keys(value)
                    time.sleep(0.1)
                return True
            elif tag == 'div':
                # 下拉框
                if type(value) == bool:
                    self.browser.click_ele(ele)
                    if value is True:
                        value = 'Enabled'
                    else:
                        value = 'Disabled'
                    option_xpath = '//*[@role="listbox"]/li[normalize-space(text())="{}"]'.format(value)
                elif type(value) == str and '|' in value:
                    self.browser.click_ele(ele)
                    list1 = value.split('|')
                    list1 = [i.strip() for i in list1 if i.strip()]
                    option_xpath = '//*[@role="listbox"]/li['
                    for i in list1:
                        option_xpath += 'normalize-space(text())="{}"'.format(i)
                        if i != list1[-1]:
                            option_xpath += ' or '
                    option_xpath += ']'
                elif type(value) == str:
                    if value in ['0', '1']:
                        self.browser.click_ele(ele)
                        if value == '0':
                            option_xpath = '//*[@role="listbox"]/li[normalize-space(text())="{}" or normalize-space(text())="{}"]'.format(
                                value, 'Disabled')
                        else:
                            option_xpath = '//*[@role="listbox"]/li[normalize-space(text())="{}" or normalize-space(text())="{}"]'.format(
                                value, 'Enabled')
                    else:
                        if ignore_unit:
                            if re.search(r'^\d+', value):
                                optionlist = self.get_option_list(xpath)
                                for i in optionlist:
                                    if re.search(r'^\d+', i):
                                        if re.search(r'^\d+', value).group() == re.search(r'^\d+', i).group():
                                            value = i
                                            break
                        self.browser.click_ele(ele)
                        option_xpath = '//*[@role="listbox"]/li[normalize-space(text())="{}"]'.format(value)
                else:
                    self.browser.click_ele(ele)
                    sleep(1)
                    option_xpath = '//*[@role="listbox"]/li[{}]'.format(value + 1)
                elelist = self.browser.driver.find_elements('xpath', option_xpath)
                for ele in elelist:
                    if ele.is_displayed():
                        try:
                            if by_js:
                                self.browser.driver.execute_script('arguments[0].click();', ele)
                            else:
                                ele.click()
                        except ElementClickInterceptedException:
                            self.browser.driver.execute_script('arguments[0].click();', ele)
                        sleep(0.5)  # 连续write两个下拉框, 动画间隔会导致失败
                        return True
                # 如果下拉框列表超过个数, 点击其他地方(右上角语言)让下拉框消失
                sleep(0.5)  # 连续write两个下拉框, 动画间隔会导致失败
                aklog_error('  write config %s failed with value: %s' % (xpath, value))
                return False
        except:
            self.click('//*[@id="app"]/div/div/section/section/header/div/div[1]/div')
            aklog_error('  write config %s failed with value: %s' % (xpath, value))
            aklog_debug(traceback.format_exc())
            return False
        aklog_error('  write config %s failed with value: %s' % (xpath, value))
        return False

        # endregion

    def get_option_list(self, text_xpath):
        """
        2022.6.7 获取下拉列表词条翻译列表
        """
        aklog_debug()
        xpath = self.get_web40_xpath(text_xpath)
        self.click(xpath)
        aftxpath = '//*[@role="listbox"]//li'
        ret = self.browser.get_values_by_xpath(aftxpath)
        self.click(xpath)
        if ret is None:
            aklog_error('获取下拉列表选项失败!')
            return []
        return ret

    def web_get_alert_text_and_confirm(self, wait_time=2):
        """网页获取弹窗消息并确认, 兼容系统弹窗和非系统弹窗. 如S565机型网页确认回复出厂, 弹窗从系统弹窗变成非系统弹窗了."""
        # 2025.7.16 X915也变成了自定义弹窗.
        aklog_debug()
        alert_text = self.browser.get_alert_text(wait_time)
        if alert_text:
            self.browser.alert_confirm_accept()
            return alert_text
        else:
            # 912 access door log关闭的弹窗
            popxpath = './/*[@class="ant-modal-confirm-title" or @class="ant-modal-confirm-content" or @class="el-message-box"]'
            msgxpath = './/*[@class="ant-modal-confirm-title" or @class="ant-modal-confirm-content" or @class="el-message-box__message"]'
            okxpath = ".//*[@class='ant-modal-content']//button[@class='ant-btn ant-btn-primary'] | //*[@class='el-message-box__btns']//*[normalize-space(@class)='el-button el-button--default el-button--small el-button--primary']"
            if self.is_exist(popxpath, wait_time=0.5):
                ret = self.browser.get_value_by_xpath(msgxpath)
                self.click(okxpath)
                return ret

    def enable_transfer(self, titlename, enablelist=[], index=None):
        """双select列表"""
        if not index:
            enablexpath = './/*[text()="{}"]/../..//*[@class = "ant-transfer-list"][2]//input'.format(titlename)
            disablexpath = './/*[text()="{}"]/../..//*[@class = "ant-transfer-list"][1]'.format(titlename)
            enablebtn = './/*[text()="{}"]/../..//*[@class = "anticon anticon-right"]'.format(titlename)
            disablebtn = './/*[text()="{}"]/../..//*[@class = "anticon anticon-left"]'.format(titlename)
            table_xpath = './/*[text()="{}"]/../..//*[@class = "ant-transfer-list"]'.format(titlename)
        else:
            enablexpath = '(.//*[text()="{}"]/../..//*[@class = "ant-transfer-list"][2]//input)[{}]'.format(titlename,
                                                                                                            str(index))
            disablexpath = '(.//*[text()="{}"]/../..//*[@class = "ant-transfer-list"][1])[{}]'.format(titlename,
                                                                                                      str(index))
            enablebtn = '(.//*[text()="{}"]/../..//*[@class = "anticon anticon-right"])[{}]'.format(titlename,
                                                                                                    str(index))
            disablebtn = '(.//*[text()="{}"]/../..//*[@class = "anticon anticon-left"])[{}]'.format(titlename,
                                                                                                    str(index))
            table_xpath = '(.//*[text()="{}"]/../..//*[@class = "ant-transfer-list"])[{}]'.format(titlename, str(index))
        if not self.is_exist(table_xpath):
            aklog_error('不存在transfer: {}'.format(titlename))
            return False
        eles = self.browser.driver.find_elements('xpath', enablexpath)
        for i in eles:
            self.write_config(i, True)
        self.click(disablebtn)
        for j in enablelist:
            xpath = disablexpath + '//*[contains(text(), "{}")]'.format(j)
            self.click(xpath)
        self.click(enablebtn)

    def web_export(self, enterpage_func, btnxpath, filename, checksize=False, timeout=30):
        """
        checksize: 检查文件大小>1KB. 可适当检测文件导出是否正常
        """

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

        aklog_debug('导出%s文件' % filename)
        if type(filename) == str:
            file_path = self.device_config.get_chrome_download_dir() + filename
            File_process.remove_file(file_path)
        else:
            for i in filename:
                file_path = self.device_config.get_chrome_download_dir() + i
                File_process.remove_file(file_path)
        enterpage_func()
        sleep(1)
        if type(btnxpath) != list:
            self.click(btnxpath)
        else:
            for i in btnxpath:
                self.click(i)
                sleep(0.5)
        sleep(5)
        # 判断文件是否导出成功
        curtime = time.time()
        for i in range(0, 60):
            if time.time() - curtime > timeout:
                aklog_error('%s文件导出失败' % filename)
                return False
            if not check_file_exist(filename):
                aklog_info('%s文件导出中...' % filename)
                sleep(3)
            else:
                self.web_get_alert_text_and_confirm()
                # if self.browser.is_exist_alert():
                #     # self.alert_confirm_accept_and_sleep()
                #     self.web_get_alert_text_and_confirm()
                if checksize and type(checksize) == bool:
                    return os.path.getsize(file_path) > 1000
                elif checksize and type(checksize) == int:
                    ret = os.path.getsize(file_path) > checksize
                    if ret:
                        aklog_info('导出文件{}成功'.format(filename))
                        return True
                    aklog_info('导出文件大小判断错误')
                    return False
                else:
                    aklog_info('导出文件{}成功'.format(filename))
                    return True
        self.web_get_alert_text_and_confirm()
        # if self.browser.is_exist_alert():
        #     # self.alert_confirm_accept_and_sleep()
        #     self.web_get_alert_text_and_confirm()
        aklog_error('%s文件导出失败' % filename)
        return False

    def web_import(self, enterpage_func, btnxpath, file, uploadbtn=None):
        aklog_info()
        if not uploadbtn:
            uploadbtn = './/*[@class="ak-common-modal-footer-btn ak-common-modal-footer-confirm ant-btn ant-btn-primary"]'

        enterpage_func()
        self.click(btnxpath)
        sleep(2)
        self.browser.upload_file_by_xpath('(.//*[@type="file"])[last()]', file)
        uploads = self.get_elements(uploadbtn)
        for ele in uploads:
            js = 'arguments[0].removeAttribute("disabled")'
            self.browser.driver.execute_script(js, ele)
        self.click(uploadbtn)
        sleep(2)
        if self.web_get_alert_text_and_confirm():
            pass
        # if self.browser.is_exist_alert(2):
        #     # self.browser.alert_confirm_accept(2)
        #     self.web_get_alert_text_and_confirm()
        else:
            ret = self.get_submit_tips(2)
            return ret

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
                ret1 = False
            except:
                ret2 = True
            else:
                ret2 = False

            if ret1 and ret2:
                return True
            else:
                time.sleep(2)

    def judge_is_wan_connected(self):
        """
        判断设备网络是否链接状态. 用于是否是重启状态检测.如reboot schedule功能
        """
        aklog_info()
        try:
            requests.get('http://%s' % self.device_ip, timeout=2, verify=False)
        except ConnectTimeout:
            pass
        except SSLError:
            # 2025.4.1 python 3.12 + 室内机, 使用这个会出现SSLError: HTTPSConnectionPool(host='192.168.30.138', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLError(1, '[SSL: DH_KEY_TOO_SMALL] dh key too small (_ssl.c:1010)')))
            return True
        else:
            return True
        try:
            requests.get('https://%s' % self.device_ip, timeout=2, verify=False)
        except ConnectTimeout:
            pass
        except SSLError:
            # 2025.4.1 python 3.12 + 室内机, 使用这个会出现SSLError: HTTPSConnectionPool(host='192.168.30.138', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLError(1, '[SSL: DH_KEY_TOO_SMALL] dh key too small (_ssl.c:1010)')))
            return True
        else:
            return True
        return False

    def judge_reboot_in_3min(self, timeout=180, reboottimeout=300):
        """2022.02.11 设备3min会重启, 且等待重启成功. 测试reboot schedule"""
        aklog_info()
        ret = self.wait_wan_disconnected(timeout)
        self.wait_wan_connected(reboottimeout)
        return ret

    def menu2_expand_and_click(self, menu_xpath, submenu_xpath, ignore_error=True):
        """
        ps:
            1. 可以传入菜单翻译:  字符串 , list.
            2. 可以传入menu_dict定义好的key.
        menu_xpath: 传入第一级菜单的词条翻译.
        submenu: 传入第二季菜单的词条翻译.
        """
        aklog_debug()
        self.web_refresh()
        sleep(1)
        if not self.judge_login_success(refresh=False):
            self.login()  # 登录会点击id=account, 以保持在菜单界面
        if self.is_exist('.//*[@class="ak-left-menu-div"]'):
            pass
        else:
            if self.is_exist(r'.//*[@class="ak-homepage-div"]', wait_time=1, printlog=False):
                # 在登录后首页页面
                ele = self.get_element('.//*[@id="account" or @id="device_management_bg"]')
                if ele and 'management' in ele.get_attribute('id').lower():
                    self.is_community_discovery = True
                    self.click('.//*[@id="account" or @id="device_management_bg"]')
                    sleep(2)
                else:
                    self.is_community_discovery = False
                    self.click('.//*[@id="account" or @id="device_management_bg"]')
                    sleep(2)
        if hasattr(self, 'is_community_discovery') and self.is_community_discovery == True and menu_xpath != 'Homepage':
            # 自组网版本需要处理
            device_manager_index = 3
            device_manager_xpath = rf'//*[@class="ak-left-menu-div"]/ul/li[{device_manager_index}]'
            menuprefix = rf'//*[@class="ak-left-menu-div"]/ul/li[{device_manager_index}]/ul/li[%s]'
            subprefix = rf'//*[@class="ak-left-menu-div"]/ul/li[{device_manager_index}]/ul/li[%s]/ul/li[%s]'
            state = self.browser.get_attribute_by_xpath(device_manager_xpath, 'class')

            # 展开device manager
            if 'open' not in state.lower():
                self.click(device_manager_xpath)
                sleep(2)
            try:
                menu_label_list = self.browser.get_values_by_xpath(
                    rf'.//*[@class="ak-left-menu-div"]/ul/li[{device_manager_index}]//ul//span[text()]')
                menu_label_list = [i.replace(' ', '').lower() for i in menu_label_list]
            except:
                menu_label_list = []
        else:
            menuprefix = r'//*[@class="ak-left-menu-div"]/ul/li[%s]'
            subprefix = r'//*[@class="ak-left-menu-div"]/ul/li[%s]/ul/li[%s]'
            # 2024.10.24 X915有的版本有holiday, 有的版本没有, 会影响到HTTP API的index. 先做名字的适配, 不行再通过手动维护的menu_xpath_dict来适配.
            # 先尝试通过词条翻译获取第一级菜单
            try:
                menu_label_list = self.browser.get_values_by_xpath(
                    './/*[@class="ak-left-menu-div"]/ul/li//span[text()]')
                menu_label_list = [i.replace(' ', '').lower() for i in menu_label_list]
            except:
                menu_label_list = []

        menuindex = -1
        if type(menu_xpath) == str:
            if menu_xpath.lower().replace(' ', '') in menu_label_list:
                menuindex = menu_label_list.index(menu_xpath.lower().replace(' ', '')) + 1
                aklog_debug('找到网页第一级菜单: 【{}】 索引: 【{}】'.format(menu_xpath, menuindex))
        elif type(menu_xpath) == list:
            for i in menu_xpath:
                if i.lower().replace(' ', '') in menu_label_list:
                    menuindex = menu_label_list.index(i.lower().replace(' ', '')) + 1
                    aklog_debug('找到网页第一级菜单: 【{}】 索引: 【{}】'.format(menu_xpath, menuindex))
                    break
        if menuindex == -1:
            if type(menu_xpath) == str:
                aklog_debug('未找到网页第一级菜单: 【{}】 索引!! 将使用事先写好的索引..'.format(menu_xpath))
                menuindex = self.menu_xpath_dict.get(menu_xpath).get('Menu')
            else:
                aklog_debug('未找到网页第一级菜单: 【{}】 索引!! 将使用事先写好的索引..'.format(menu_xpath))
                for kk in menu_xpath:
                    for keys in self.menu_xpath_dict.keys():
                        if kk.lower().replace(' ', '') == keys.lower().replace(' ', ''):
                            menuindex = self.menu_xpath_dict.get(keys).get('Menu')
                            menu_xpath = keys
                            break

        aft_menu_xpath = menuprefix % menuindex

        # 2024.10.24 先展开第一级菜单
        submenu = submenu_xpath
        for times in range(3):
            state = self.browser.get_attribute_by_xpath(aft_menu_xpath, 'class')
            if not state:
                self.web_refresh()
                sleep(5)
                continue
            elif 'open' not in state:
                # 展开第一级菜单
                self.click(aft_menu_xpath)
                sleep(2)
                if not submenu_xpath:  # 如果不传入二级菜单, 直接退出
                    return True
            else:
                # 已经是展开状态.
                pass

            # 尝试通过词条翻译去获取第二级菜单
            try:
                submenu_label_list = self.browser.get_values_by_xpath(aft_menu_xpath + '/ul/li')
                submenu_label_list = [i.replace(' ', '').lower() for i in submenu_label_list]
            except:
                submenu_label_list = []

            if not submenu_label_list and times != 2:
                # 有时候一级菜单展开了， 但是class里没有open
                aklog_warn('有时候一级菜单展开了， 但是class里没有open')
                aklog_info('~~~~~~~~~~~~~~~~~')
                aklog_info('一级菜单： {}'.format(state))
                self.screen_shot()
                continue

            submenuindex = -1
            if type(submenu_xpath) == str:
                if submenu_xpath.lower().replace(' ', '') in submenu_label_list:
                    submenuindex = submenu_label_list.index(submenu_xpath.lower().replace(' ', '')) + 1
                    aklog_debug('找到网页第二级菜单: 【{}】 索引: 【{}】'.format(submenu_xpath, submenuindex))
            elif type(submenu_xpath) == list:
                for i in submenu_xpath:
                    if i.lower().replace(' ', '') in submenu_label_list:
                        submenuindex = submenu_label_list.index(i.lower().replace(' ', '')) + 1
                        aklog_debug('找到网页第二级菜单: 【{}】 索引: 【{}】'.format(submenu_xpath, submenuindex))
                        break
            if submenuindex == -1:
                aklog_warn('未找到网页第二级菜单: 【{}】 索引!! 将使用事先写好的索引..'.format(submenu_xpath))
                if type(submenu_xpath) == str:
                    aklog_warn('未找到网页第二级菜单: 【{}】 索引!! 将使用事先写好的索引..'.format(submenu_xpath))
                    submenuindex = self.menu_xpath_dict.get(menu_xpath).get(submenu_xpath)
                else:
                    aklog_warn('未找到网页第二级菜单: 【{}】 索引!! 将使用事先写好的索引..'.format(submenu_xpath))
                    for kk in submenu_xpath:
                        for keys in self.menu_xpath_dict.get(menu_xpath):
                            if kk.lower().replace(' ', '') == keys.lower().replace(' ', ''):
                                print(keys)
                                submenuindex = self.menu_xpath_dict.get(menu_xpath).get(keys)
                                submenu_xpath = keys
                                break
            submenu_xpath = subprefix % (menuindex, submenuindex)
            self.click(submenu_xpath)
            sleep(1)
            state = self.browser.get_attribute_by_xpath(submenu_xpath, 'class')
            if state and 'selected' in state:
                aklog_info('进入页面： %s -> %s 成功！' % (menu_xpath, submenu))
                return True
            else:
                if times == 2:
                    aklog_error(' 进入子菜单%s 失败2次, 退出尝试!!' % submenu)
                    return False
                aklog_error(' 进入子菜单%s 失败, 重试ing...' % submenu)
                self.screen_shot()

    def web_wait_registered(self):
        """
        2022.6.1 等待accouNt-basic页面显示为registered
        """
        xpath = r'//*[@class="ak-common-page-div"]/div[2]/div[2]/div/label[2]'
        # self.web_refresh()
        for i in range(5):
            sleep(1)
            ret = self.read_config_by_name(xpath)
            if ret is None:
                self.enter_web_account_basic()
            if ret == 'Registered':
                aklog_info('注册sip账号成功!!!')
                return True
            sleep(3)
        self.screen_shot()
        aklog_error('注册sip账号失败!!!')
        return False

    # region 表格

    def get_table_xpath(self, tablename, row=1, column=1, subfix=None):
        """
        获取table里的单元格输入框, 下拉框的xpath.
            tablename : 索引, 翻译字符串, 翻译数组. 可忽视大小写
            column: 索引, 列名翻译字符串, 列名翻译数组.
        """
        if type(column) == int:
            columnindex = column
        else:
            columnindex = self.web_get_table_column_index(column, tablename)
        if not columnindex:
            aklog_error('网页写表格配置失败!')
            return False
        table = self.get_table_xpath_by_title(tablename)
        prefix = table + f'//tbody//tr[{row}]//td[{columnindex}]//'
        eleXpath = prefix + 'input' + '|' + prefix + 'div[@role="combobox"]'
        if subfix:
            return eleXpath + subfix
        return eleXpath

    def get_table_xpath_by_title(self, table_index_name):
        """
        table_index_name: 索引, 字符串（可忽视大小写）, 字符串数组
        """
        if type(table_index_name) == int:
            xpath = '(.//table)[' + str(table_index_name) + ']'
        else:
            if type(table_index_name) == list:
                xpath = './/*[@class="ak-conetnt-title"]//*['
                for i in table_index_name:
                    i = self.get_translated_text(i)
                    xpath += f'text()="{i}" or '
                xpath = xpath.strip().strip('or')
                xpath += ']/../..//table'
            else:
                table_index_name = self.get_translated_text(table_index_name)
                xpath = f'.//*[@class="ak-conetnt-title"]//*[text()="{table_index_name}"]/../..//table'
        return xpath

    def read_table_value(self, name, row, column):
        """
        根据表格标题, 行, 列 读配置
        name:  索引, 翻译字符串, 翻译数组.
        column:  索引, 列名翻译字符串
        """
        xpath = self.get_table_xpath_by_title(name)
        if type(column) == str:
            column = self.web_get_table_column_index(column, name)
        prefix = xpath + '//tbody//tr[{}]//td[{}]//'.format(row, column)
        eleXpath = prefix + 'input' + '|' + prefix + 'div[@role="combobox"]' + ' | ' + prefix + 'label'
        tdXpath = prefix.rstrip('//')
        ret = self.read_config_by_name(eleXpath)
        if ret is None:
            return self.read_config_by_name(tdXpath)
        else:
            return ret

    def write_table_value(self, name, row, column, value, by_js=False):
        """
        根据表格标题, 行, 列 写配置. 从1开始
            name:  表格名索引, 翻译字符串, 翻译数组.
            column:  索引, 列名翻译字符串, 列名翻译数组.
        """
        # prefix = r'.//*[text()="{}"]/../..//tbody//tr[{}]//td[{}]//'.format(name, row, column)
        # eleXpath = prefix + 'input' + '|' + prefix + 'div[@role="combobox"]'
        eleXpath = self.get_table_xpath(name, row, column)
        return self.write_config_by_name(eleXpath, value, by_js=by_js)

    def web_get_table_current_page(self, tablename=1):
        """
        获取表格当前在哪一个页, tablename: 可无视大小写
        """
        if type(tablename) == int:
            prefix = f'(//*[@class="ak-common-table"])[{tablename}]'
        else:
            if type(tablename) == list:
                prefix = './/*[@class="ak-conetnt-title"]//*['
                for i in tablename:
                    i = self.get_translated_text(i)
                    prefix += f'text()="{i}" or '
                prefix = prefix.strip().strip('or')
                prefix += ']/../..'
            else:
                table_index_name = self.get_translated_text(tablename)
                prefix = f'.//*[@class="ak-conetnt-title"]//*[text()="{table_index_name}"]/../..'
        xth = prefix + '//*[@class="ak-common-table-footer"]//span[contains(text(), "/") and not(contains(text(), "Selected"))]'.format(
            tablename)
        return self.get_element(xth).text.strip()

    def web_set_table_page(self, tablename, page):
        """
        表格跳转
        """
        if type(tablename) == str:
            self.write_config(
                './/label[text()="{}"]/../..//*[@class="ak-common-table-footer"]//input'.format(tablename),
                page)
            self.click(
                './/label[text()="{}"]/../..//*[@class="ak-common-table-footer"]//button//*[text()="Go"]'.format(
                    tablename))
        else:
            self.write_config('(//*[@class="ak-common-table-footer"])[{}]//input'.format(tablename), page)
            self.click(
                '(//*[@class="ak-common-table-footer"])[{}]//button//*[text()="Go"]'.format(tablename))

    def web_get_table_value_row_index(self, colname, colvalue, tableindex=1):
        """
        X915V2 网页根据colname 和 colvalue 返回在第几行row. 用于如联系人列表点击对应联系人的edit按钮
        """
        colvalue = str(colvalue)
        col_index = self.web_get_table_column_index(colname, tableindex)
        if type(tableindex) == int:
            elelist = self.get_elements(r'(//*[@class="ant-table-tbody"])[%s]/tr' % tableindex)
        else:
            xpath = self.get_table_xpath_by_title(tableindex) + '//tbody//tr'
            elelist = self.get_elements(xpath)
        if not elelist:
            aklog_info('No table data')
            return
        rowcounts = len(elelist)
        for i in range(1, rowcounts + 1):
            if type(tableindex) == int:
                xpath = r'(//*[@class="ant-table-tbody"])[%s]/tr[%s]/td[%s]' % (tableindex, i, col_index)
            else:
                xpath = self.get_table_xpath_by_title(tableindex) + '//tbody//tr[%s]/td[%s]' % (i, col_index)
            if self.browser.get_value_by_xpath(xpath) == colvalue:
                return i
        aklog_error(' no found colname: %s, colvalue: %s' % (colname, colvalue))
        return

    def select_table_row_by_index(self, indexlist: list = 1, tableindex=1):
        """2022.6.17 基础接口, 选择表格的行勾选"""
        if indexlist == 'All' or indexlist == ['All']:
            xpath = self.get_table_xpath_by_title(tableindex) + '//tbody'
            self.write_config(xpath + '//*[@type="checkbox"]', True)
        else:
            xpath = self.get_table_xpath_by_title(tableindex) + '//tbody'
            if type(indexlist) == str or type(indexlist) == int:
                self.write_config(xpath + '//tr[%s]//*[@type="checkbox"]' % indexlist, True)
            else:
                for i in indexlist:
                    self.write_config(xpath + '//tr[%s]//*[@type="checkbox"]' % i, True)
        sleep(1)

    def web_click_table_checkbox_by_index(self, indexlist=[], tableindex=1):
        """
        点击表格多行
        """
        if type(tableindex) != int:
            txpath = self.get_table_xpath_by_title(tableindex) + '//tbody'
            if type(indexlist) == int:
                xpath = txpath + '//tr[%s]//*[@type="checkbox"]' % (indexlist)
                self.click(xpath)
            else:
                for i in indexlist:
                    xpath = txpath + '//tr[%s]//*[@type="checkbox"]' % (i)
                    self.click(xpath)
        else:
            txpath = self.get_table_xpath_by_title(tableindex) + '//tbody'
            if type(indexlist) == int:
                xpath = txpath + '//tr[%s]//*[@type="checkbox"]' % indexlist
                self.click(xpath)
            else:
                for i in indexlist:
                    xpath = txpath + '//tr[%s]//*[@type="checkbox"]' % i
                    self.click(xpath)

    def web_click_table_checkbox(self, colname, colvaluelist, tableindex=1):
        """
        点击表格的多行. 根据列索引.
        self.web_click_table_checkbox('Name', ['lex', 'ceshi'])
        """
        if type(colvaluelist) == str:
            editindex = self.web_get_table_value_row_index(colname, colvaluelist, tableindex)
            xpath = self.get_table_xpath_by_title(tableindex) + '//tbody'
            # xpath = xpath + '//tr[%s]//i' % editindex
            xpath = xpath + '//tr[%s]//*[@type="checkbox"]' % editindex
            self.click(xpath)
        else:
            xpath = self.get_table_xpath_by_title(tableindex) + '//tbody'
            for i in colvaluelist:
                editindex = self.web_get_table_value_row_index(colname, i, tableindex)
                if editindex:
                    # xpath = xpath + '//tr[%s]//i' % editindex
                    xpath = xpath + '//tr[%s]//*[@type="checkbox"]' % editindex
                    self.click(xpath)

    def web_click_table_edit(self, colname, colvalue, tableindex=1):
        """
        点击表格的edit按钮.
        """
        editindex = self.web_get_table_value_row_index(colname, colvalue, tableindex)
        aklog_info('click button "Edit" in line:%s' % editindex)
        xpath = self.get_table_xpath_by_title(tableindex)
        xpath = xpath + r'//tbody//tr[%s]//i' % editindex
        self.click(xpath)

    def web_click_table_edit_by_index(self, index=1, tableindex=1):
        """
        点击表格的edit按钮.
        """
        aklog_info('click button "Edit" in line:%s' % index)
        xpath = self.get_table_xpath_by_title(tableindex)
        xpath = xpath + r'//tbody//tr[%s]//i' % index
        self.click(xpath)

    def web_get_table_column_values(self, colname, tableindex=1):
        """
        传入表格的列名, 获取 一列 的信息.
        eg: web_get_contact_name_list
        """
        ret = self.web_get_table_column_index(colname, tableindex)
        if not ret:
            aklog_error(' 未能获取表格: %s , 列名: %s 的数据!!' % (tableindex, colname))
            return []
        else:
            # xpath = '(//*[@class="ant-table-tbody"])[%s]//*[@class="ant-table-row-cell-break-word"][%s]' % (tableindex, ret)
            # 有的表格index列不是ant-table-row-cell-break-word
            xpath = self.get_table_xpath_by_title(tableindex) + '//tr/td[%s]' % ret
            values = self.browser.get_values_by_xpath(xpath)
            if not values:
                return []
            return values

    def web_change_dict_key_name(self, valuedict, oldnamelist, newnamelist):
        """
        外部不调用.
        """
        if not valuedict:
            return valuedict
        if type(oldnamelist) == str:
            if oldnamelist not in valuedict:
                aklog_error(' 修改字典数据key名字失败, 不存在key: %s' % oldnamelist)
                return valuedict
            else:
                return valuedict.update({newnamelist: valuedict.pop(oldnamelist)})
        else:
            valuekeys = list(valuedict.keys())
            valuekeys = [value.replace(' ', '').lower() for value in valuekeys]
            print(valuekeys)
            for i in range(len(oldnamelist)):
                if oldnamelist[i].lower().replace(' ', '') not in valuekeys:
                    aklog_error(' 修改字典数据key名字失败, 不存在key: %s' % oldnamelist[i])
                else:
                    for j, k in valuedict.items():
                        if j.replace(' ', '').lower() == oldnamelist[i].replace(' ', '').lower():
                            valuedict.update({newnamelist[i]: valuedict.pop(j)})
                            break
            return valuedict

    def web_get_table_column_index(self, colname, tableindex=1):
        """
        外部不调用:
        tableindex: index, 翻译, 翻译数组.
        通过表名+列名, 返回要操作的td index..
        """
        # colnamelist = self.web_get_table_column_name_list(tableindex)
        # colnamelist = [i.replace(' ', '').lower() for i in colnamelist]
        # if colnamelist:
        #     if colname.replace(' ', '').lower() not in colnamelist:
        #         aklog_error(' 表格中没有列名: %s' % colname)
        #     else:
        #         return colnamelist.index(colname.replace(' ', '').lower()) + 1
        xpath = self.get_table_xpath_by_title(tableindex)
        head = xpath + '//*[@class="ant-table-thead"]//th'
        eles = self.get_elements(head)
        _count = 0
        for i in eles:
            _count += 1
            if i.text.replace(' ', '').lower() == colname.replace(' ', '').lower():
                return _count
        aklog_error(' 表格中没有列名: %s' % colname)

    def web_get_table_column_name_list(self, tableindex=1):
        """外部不调用:
        获取表格列名.  tableindex: 序号, 翻译字符串, 翻译数组.
        """
        xpath = self.get_table_xpath_by_title(tableindex)
        head = xpath + '//*[@class="ant-table-thead"]'
        try:
            colnamelist = self.get_element(head).text.splitlines()
            return colnamelist
        except:
            aklog_error(' 页面没有表格或表格个数错误')

    def web_get_table_row_values_dict(self, colname_index, colvalue=None, tableindex=1):
        """
        browser.web_get_table_row_values_dict('Name', '55555')
            # Name==55555的行记录字典
            # colname_index: 1, colvalue: None: 行数索引.
            # tableindex: 从1开始, 或者表格名.
        """
        tablexpath = self.get_table_xpath_by_title(tableindex)
        rxpath = tablexpath + '//*[@class="ant-table-tbody"]/tr'
        table_row_list = self.get_elements(rxpath)
        if not table_row_list:
            aklog_error(' 表格中不存在数据记录')
            return {}
        if colvalue is None and type(colname_index) == int:
            colvalue_xpath = rxpath + f'[{colname_index}]/td'
            rowvalue = self.browser.get_values_by_xpath(colvalue_xpath, delnull=False)  # 列值为空也需要保存
            if not rowvalue:
                return {}
            table_row_value_list = rowvalue
            table_row_value_list = [i.strip() for i in table_row_value_list]
            # 去除勾选框列
            if table_row_value_list[0] == '':
                table_row_value_list.pop(0)
            colnamelist = self.web_get_table_column_name_list(tableindex)
            ret_dict = dict(zip(colnamelist, table_row_value_list))
            return ret_dict
        else:
            colvalue = str(colvalue)
            colnamelist = self.web_get_table_column_name_list(tableindex)
            ret = self.web_get_table_column_values(colname_index, tableindex)
            if ret.count(colvalue):
                trindex = ret.index(colvalue) + 1
                colvalue_xpath = rxpath + f'[{trindex}]/td[@class != "ant-table-selection-column"]'
                rowvalue = self.browser.get_values_by_xpath(colvalue_xpath, delnull=False)  # 列值为空也需要保存
                ret_dict = dict(zip(colnamelist, rowvalue))
                return ret_dict
            else:
                aklog_error(' 未能找到表格记录！！ 列名: %s, 列值: %s' % (colname_index, colvalue))
                return {}

    # endregion 表格

    # region 图片
    def web_compare_image(self, xpath, pic, percent=0):
        """
        2025.5.21 废弃不用.  使用web_image_compare,    percent越高越相似
        pic可以是一张图片或者多张图片
        """
        aklog_info()
        if type(pic) == str and not os.path.exists(pic):
            aklog_error('不存在图片: {}'.format(pic))
            return False
        TEMP_FILE = os.path.join(tempfile.gettempdir(), "temp_screen2.png")
        File_process.remove_file(TEMP_FILE)
        self.browser.switch_iframe_to_default()
        # headless下, 默认分辨率800*600, 即使chrome_options.add_argument('--window-size=1920,1080')后,
        # 调用maximize_window()后也会变成800 * 600, 导致S562, S565的8849显示截断, 换一种实现.
        self.browser.max_window()
        self.browser.driver.execute_script("document.body.style.zoom = 1;")  # 设置缩放比例为100%
        sleep(1)
        if hasattr(self, 'get_element'):
            ele = self.get_element(xpath)
        else:
            ele = self.browser.get_element_visible(By.XPATH, xpath)
        if not ele:
            aklog_error("不存在控件, 图片判断失败!!!!")
            return False
        else:
            ele.screenshot(r'E:\\111.png')
            ret = ele.screenshot(TEMP_FILE)
            self.web_refresh()  # 恢复原有的缩放比例
            if ret:
                if type(pic) == str:
                    ret = image_compare_after_convert_resolution(pic, TEMP_FILE, percent=percent)
                    # File_process.remove_file(TEMP_FILE)
                    return ret
                else:
                    # 多张图片
                    for p in pic:
                        ret = image_compare_after_convert_resolution(p, TEMP_FILE, percent=percent)
                        if ret:
                            return True
                        else:
                            continue

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
            self.browser.switch_iframe_to_default()
            # 网页变化为跟有头一样后再对比
            self.browser.max_window()
            self.browser.driver.execute_script("document.body.style.zoom = 1;")  # 设置缩放比例为100%
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

    def web_check_image_no_pure(self, xpath, percent=50, rgb_fix_range=20):
        """
        判断图片不是纯色
        """
        aklog_info()
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

    # endregion 图片

    # endregion

    # region 登录相关
    def enter_password_in_login_page(self, username, password):
        """
        登录界面输入账号, 密码.
        """
        # self.write_config_by_name('(//div[@class="ak-login-modal-div"]//input)[1]', username)
        # self.write_config_by_name('(//div[@class="ak-login-modal-div"]//input)[2]', password)
        # self.click('.//*[@class="ak-homepage-btn"]')
        self.user_login(username, password)

    def web_login(self, username, password):
        self.user_login(username, password)

    def user_login(self, username, password):
        """
        登陆界面输入账号密码. 用于测试user, admin登陆登出.
        """
        self.write_config_by_name('(//div[@class="ak-login-modal-div"]//input)[1]', username)
        self.write_config_by_name('(//div[@class="ak-login-modal-div"]//input)[2]', password)
        self.click('.//*[@class="ak-homepage-btn"]')
        # self.screen_shot()

    def modify_password_when_login(self):
        """login网页后, 若有弹窗就修改密码, 否则到security页面修改密码. admin -> Aa12345678"""
        aft_pwd = self.device_config.get_web_admin_password_changed()  # Aa12345678
        # if self.is_exist(self.ele_info['change_pwd_window_title_xpath']):
        if self.is_exist('//*[@class="ant-modal-title"]'):
            # 恢复出厂后修改密码
            self.write_config('(.//*[@class="ant-modal-body"]//input)[2]', aft_pwd)
            self.write_config('(.//*[@class="ant-modal-body"]//input)[3]', aft_pwd)
            if not self.click('.//button//*[text()="Change" or text()="修 改" or text()="确 定"]'):
                self.click(
                    './/*[@class="ak-common-modal-footer-btn ak-common-modal-footer-confirm ant-btn ant-btn-primary" or @class="ant-btn ant-btn-primary ak-common-modal-footer-whole-btn ak-common-modal-footer-confirm"]')
            ret = self.get_submit_tips()
            if ret and ('talk' in ret.lower() or '通话' in ret.lower()):
                aklog_fatal('设备初始化可能失败!!!, 设备在通话中!!!')
            self.web_admin_pwd = aft_pwd
            if self.is_exist('//*[@id="Config.Settings.SECURITY.Question1"]/div[1]/div'):
                self.click(
                    './/*[@class="ak-common-modal-footer-btn ak-common-modal-footer-cancel ant-btn ant-btn-danger"]')
        else:
            # security界面修改密码
            self.login_state = True
            self.get_menu_xpath_info(True)
            self.web_pwd_modify('admin', aft_pwd)

    def login(self, url=None, raise_enable=True, change_pwd=True, wait_connect=True):
        """不打开浏览器, 登录网页, 如果密码不是Aa12345678, 会默认修改密码"""
        aklog_info()
        if not url:
            #url = self.login_url
            current_url = self.browser.get_current_url()
            if current_url:
                current_url = current_url.lstrip('data:,').strip()
            url = current_url or self.login_url
        else:
            # 如果重新登录的地址是jpg, 就不处理
            if url.endswith('.jpg') or url.endswith('.cgi'):
                url = self.login_url
        self.browser.visit_url(url)
        for i in range(5):
            self.web_refresh(force=True)
            sleep(1)
            if self.is_exist('//div[@class="ak-login-modal-div"]', wait_time=2):
                # 登录页面
                if i == 1:
                    password = self.device_config.get_web_admin_passwd()
                else:
                    password = self.web_admin_pwd
                    if password == self.device_config.get_web_admin_passwd():
                        aklog_error_tag(f'web_admin_pwd 被改成 admin !!!! , 需要定位')
                        password = self.device_config.get_web_admin_password_changed()
                        aklog_info(password)

                self.enter_password_in_login_page('admin', password)
                # E16V2:登录后画面比例不对，logout会被挤出画面，增加ak-homepage-head元素的判断
                if not self.is_exist('.//*[@class="ak-logout-label" or @class="ak-homepage-head"]', wait_time=2):
                    submittips = self.browser.get_value_by_xpath('//*[@class="ant-notification-notice-message"]', 2,
                                                                 print_trace=False)
                    if submittips and ('limit' in submittips or '受限' in submittips):
                        if i == 4:
                            aklog_error('登录网页失败多次, 停止登录!!!!')
                            if raise_enable:
                                self.browser_close_and_quit()
                                sleep(2)
                                raise RuntimeError
                            else:
                                return False
                        else:
                            aklog_error('网页密码登录失败多次, 需要等待3分钟!!')
                            sleep(190)
                            continue
                    else:
                        aklog_error('网页密码: {} 登录失败, 尝试重新登录!!!'.format(password))
                        sleep(6)
                        self.screen_shot()
                        continue
                else:
                    # 登录成功后, 判断是否需要修改密码, 否则开始下次循环判断是否登录成功
                    if change_pwd:
                        if password == self.device_config.get_web_admin_passwd():
                            aklog_info('网页登录成功! 网页密码为默认值, 需要修改..')
                            sleep(2)
                            self.modify_password_when_login()
                            sleep(1)
                            # 修改密码成功后,不确定有没有密保弹窗，再刷新一下
                            self.web_refresh()
                            # 并设置网页语言为英语.
                            self.set_web_language_to_english()
                    self.login_state = True
                    continue
            else:
                # 没有在登录界面的话, 就判断是否登录成功
                if self.is_exist('.//*[@class="ak-logout-label"]'):
                    if 'home' in self.browser.get_current_url().lower():
                        self.click('.//*[@id="account" or @id="upgrade"]')  # s567 一些特殊版本没有account
                    self.login_status = True
                    self.get_menu_xpath_info(True)
                    aklog_info('登录网页成功')
                    return True
                else:
                    self.screen_shot()
        aklog_error('登录网页失败！！')
        self.screen_shot()
        if raise_enable:
            self.browser_close_and_quit()
            sleep(2)
            raise RuntimeError
        else:
            return False

    def retry_visit_url(self, url=None):
        aklog_info('retry_visit_url: %s' % url)
        if url and '/#/' in url:
            pass
        else:
            url = self.login_url
        self.browser.visit_url(url)

    def retry_login(self, modify_default_pwd=True, raise_enable=True):
        """
        重新打开浏览器, 重新登录
        """
        aklog_info(f'重新打开浏览器, 重新登录')
        for j in range(3):
            current_url = self.login_url
            self.browser.close_and_quit()
            self.browser.init()
            if self.login(url=current_url, raise_enable=raise_enable):
                return True

    def web_logout(self):
        aklog_info('web_logout')
        username = r'//input[@placeholder="Username" or @placeholder="User Name" or @placeholder="username" or  @placeholder="用户名"]'
        if self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_logout_class']):
            self.browser.click_btn_by_class_name(self.ele_info['home_logout_class'])
        if self.browser.is_exist_and_visible_ele_by_xpath(username):
            aklog_info('网页已登出')
            return True
        else:
            aklog_error('网页登出失败')
            self.browser.screen_shot()
            return False

    # endregion

    # region 网页业务接口
    # region 其他
    def judge_login_failed(self):
        """
        封装: 判断登陆界面登陆失败
        """
        aklog_debug()
        ret = self.get_submit_tips()
        if ret:
            aklog_info(ret)
            return True
        return False

    def judge_in_login_page(self):
        """判断设备在登出状态"""
        aklog_debug()
        username = r'//input[@placeholder="Username" or @placeholder="User Name" or @placeholder="username"]'
        loginbtn = r'//*[@class="ak-homepage-btn" and text()="Login"]'
        ret1 = self.is_exist(username)
        ret3 = self.is_exist(loginbtn)
        return ret1 and ret3

    def judge_login_success(self, refresh=False):
        """
        判断是在登录上的界面
        """
        aklog_debug()
        if refresh:
            self.web_refresh()
        return self.is_exist('.//*[@class= "ak-logout-label"]')

    def web_get_network_info(self):
        aklog_info()
        self.enter_status_basic()
        type = self.read_config_by_name('Port Type | Type | LAN Port Type')
        status = self.read_config_by_name('Link Status | Status | LAN Link Status')
        ip = self.read_config_by_name('IP Address | LAN IP Address')
        mask = self.read_config_by_name('Subnet Mask | LAN Subnet Mask')
        gateway = self.read_config_by_name('Gateway | LAN Gateway')
        dns1 = self.read_config_by_name('Preferred DNS Server | Preferred DNS')
        dns2 = self.read_config_by_name('Alternate DNS Server | Alternate DNS')
        return {'type': type, 'status': status, 'ip': ip, 'mask': mask, 'gateway': gateway, 'dns1': dns1, 'dns2': dns2}

    # endregion 其他

    # region Account-Basic
    def web_enter_account_basic(self):
        return self.enter_web_account_basic()

    def select_account_by_index(self, index=1):
        """
        2022.6.1 网页account--切换操作账号
        """
        aklog_info()
        if index == '0':
            index = 1
        if index == '1':
            index = 2
        if self.read_config_by_name('//*[@id="currentAccount"]/div[1]/div') != 'Account%s' % index:
            self.write_config_by_name('//*[@id="currentAccount"]/div[1]/div', 'Account%s' % index)
            sleep(1)

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
        self.write_config_by_name(
            '//*[@id="app"]/div/div/section/section/main/div/div/div[2]/div[4]/div/label[2]/span/input', active)
        self.write_config_by_name(f'//*[@id="Config.Account{index}.GENERAL.Label"]/input | //*[@id="Label"]/div/input',
                                  sip)
        self.write_config_by_name(
            f'//*[@id="Config.Account{index}.GENERAL.DisplayName"]/input | //*[@id="DisplayName"]/div/input', sip)
        self.write_config_by_name(
            f'//*[@id="Config.Account{index}.GENERAL.AuthName"]/input | //*[@id="RegisterName"]/div/input', sip)
        self.write_config_by_name(
            f'//*[@id="Config.Account{index}.GENERAL.UserName"]/input | //*[@id="UserName"]/div/input', sip)
        self.write_config_by_name(f'//*[@id="Config.Account{index}.GENERAL.Pwd"]/input | //*[@id="Password"]/div/input',
                                  sip_password)
        self.write_config_by_name(
            f'//*[@id="Config.Account{index}.SIP.Server"]/input | //*[@id="SipServer1"]/div/input', server_ip)
        self.write_config_by_name(
            f'//*[@id="Config.Account{index}.SIP.Port"]/input | //*[@id="SipServerPort1"]/div/input', server_port)
        self.write_config_by_name(
            f'//*[@id="Config.Account{index}.SIP.TransType"]/div[1]/div | //*[@id="TransType"]/div/div', transport)
        self.write_config_by_name('Outbound Enabled', outbound)
        if outbound1:
            self.write_config_by_name(
                f'//*[@id="Config.Account{index}.OUTPROXY.Server"]/input | //*[@id="OutboundServer"]/div/input',
                outbound1)
        if outbound2:
            self.write_config_by_name(
                f'//*[@id="Config.Account{index}.OUTPROXY.BakServer"]/input | //*[@id="OutboundBackupServer"]/div/input',
                outbound2)
        self.write_config_by_name(
            f'//*[@id="OutboundPort"]/div/input | //*[@id="Config.Account{index}.OUTPROXY.Port"]/input', outbound1_port)
        self.write_config_by_name(
            f'//*[@id="OutboundBackupPort"]/div/input | //*[@id="Config.Account{index}.OUTPROXY.BakPort"]/input',
            outbound2_port)
        self.write_config_by_name('NAT', nat)
        self.write_config_by_name(
            f'//*[@id="Config.Account{index}.STUN.Server"]/input | //*[@id="ServerAddress"]/div/input', stun_server)
        self.write_config_by_name(f'//*[@id="Config.Account{index}.STUN.Port"]/input | //*[@id="ServerPort"]/div/input',
                                  nat_port)
        self.click_submit()
        if account_active in ('1', True, 'Enabled') and wait_register:
            sleep(3)
            return self.web_wait_registered()

    def web_judge_account_registered(self, index=1):
        aklog_info()
        self.enter_web_account_basic()
        self.select_account_by_index(index)
        return self.web_wait_registered()

    # endregion

    # region upgrade-basic
    def web_enter_upgrade_basic(self):
        return self.enter_upgrade_basic()

    def wait_for_web_reboot_finished(self, login=True):
        """
        用于等待网页reboot, reset结束: 在点击reboot后, 等待设备重启->获取到ip
        login: 重启后是否做登录网页操作.
        """
        if not self.wait_wan_disconnected(timeout=60):
            aklog_warn('设备未在60秒内重启')
            return False
        else:
            aklog_debug('设备已进入重启状态..')
        if not self.wait_wan_connected(timeout=self.device_config.get_reset_default_time()):
            aklog_warn('设备未在{}秒内启动'.format(self.device_config.get_reset_default_time()))
            return False
        else:
            aklog_debug('设备重新获取到IP..')

        sleep(20)
        cur_time = time.time()
        for i in range(15):
            if time.time() - cur_time > 120:
                break
            else:
                self.web_refresh(force=True)
                sleep(2)
                xpath1 = r'.//*[@class="ak-login-logo"]'
                xpath2 = r'.//*[@class="ak-processing-modal-label"]'
                if self.is_exist(xpath1):
                    aklog_info('设备重启结束, 在登录界面')
                    if login:
                        self.login()
                        self.enter_upgrade_basic()
                    return True
                elif self.is_exist(self.ele_info['change_pwd_window_title_xpath']):
                    if login:
                        self.login()
                        self.enter_upgrade_basic()
                    return True
                elif self.is_exist('//*[@class="ak-logout-label"]'):
                    self.retry_login()
                    aklog_info('设备重启结束, 在登录界面')
                    return True
                # elif not self.is_exist(xpath2):
                #     aklog_info('设备重启结束')
                #     return True
        self.screen_shot()
        aklog_info('设备重启异常')
        return False

    def web_reboot(self, accept=True):
        """网页进行重启"""
        aklog_info()
        self.enter_upgrade_basic()
        self.click('Reboot', 'Reboot')  # 933网页多了Except the start-up settings, 影响了整个页面按钮顺序
        if accept:
            # self.browser.alert_confirm_accept(wait_time = 2)
            self.web_get_alert_text_and_confirm(wait_time=2)
            param_put_reboot_process_flag(True)
        else:
            self.browser.alert_confirm_cancel()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reboot_xpath']):
                aklog_info('返回基础升级页面完成')
                return 1
            else:
                aklog_error('返回基础升级页面失败')
                return 0
        return self.wait_for_web_reboot_finished()

    def web_reset_config_to_factory_setting(self, accept=True, retry_login=True):
        """网页reset config出厂设置"""
        aklog_info()
        self.enter_upgrade_basic()
        if self.is_exist('.//*[contains(text(),"Reset Configuration")]'):
            ele = self.get_web40_element('.//*[contains(text(),"Reset Configuration")]/..')
            tag = self.get_tag(ele)
            if tag == 'span':
                # A0X多了一层span
                xpath = './/*[contains(text(),"Reset Configuration")]/../following-sibling::*//*[normalize-space(text())="Reset"]'
            else:
                xpath = './/*[contains(text(),"Reset Configuration")]/..//*[normalize-space(text())="Reset"]'
            self.click(xpath)
        else:
            self.click('Reset', 'Reset Config')  # 933网页多了Except the start-up settings, 影响了整个页面按钮顺序
        if accept:
            # self.browser.alert_confirm_accept(wait_time = 2)
            self.web_get_alert_text_and_confirm(wait_time=2)
            param_put_reboot_process_flag(True)
        else:
            self.browser.alert_confirm_cancel()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reset_config_xpath']):
                aklog_info('返回基础升级页面完成')
                return 1
            else:
                aklog_error('返回基础升级页面失败')
                return 0
        ret = self.wait_for_web_reboot_finished(
            False)  # 2025.5.23 X915机型， 恢复出场后， 自动化login， 第二次输入密码admin不会正常登录上去。 做一次浏览器重启。
        self.retry_login()
        return ret

    def web_reset_to_factory_setting(self, accept=True, login=True):
        """
        2024.8.8  网页恢复出厂设置
        login: 回复出厂后是否去登录网页.
        """
        aklog_info('网页恢复出厂设置')
        self.enter_upgrade_basic()
        if self.is_exist('.//*[contains(text(),"Reset To") or contains(text(), "Factory Default")]'):
            # 兼容A0X
            ele = self.get_web40_element('.//*[contains(text(),"Reset To") or contains(text(), "Factory Default")]/..')
            tag = self.get_tag(ele)
            if tag == 'span':
                # A0X多了一层span
                xpath = './/*[contains(text(),"Reset To") or contains(text(), "Factory Default")]/../following-sibling::*//*[normalize-space(text())="Reset"]'
            else:
                xpath = './/*[contains(text(),"Reset To") or contains(text(), "Factory Default")]/..//*[normalize-space(text())="Reset"]'
            self.click(xpath)
        else:
            self.browser.click_btn_by_xpath(self.ele_info[
                                                'upgrade_basic_factory_default_xpath'])  # 933网页多了Except the start-up settings, 影响了整个页面按钮顺序, 暂不根据词条定位.
        if accept:
            # if not self.browser.alert_confirm_accept(wait_time = 2):
            if not self.web_get_alert_text_and_confirm(wait_time=2):
                self.screen_shot()
            param_put_reboot_process_flag(True)
        else:
            self.browser.alert_confirm_cancel()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reset_config_xpath']):
                aklog_info('返回基础升级页面完成')
                return 1
            else:
                aklog_error('返回基础升级页面失败')
                return 0
        ret = self.wait_for_web_reboot_finished(login=False)
        # 2025.5.23 X915机型， 恢复出场后， 自动化login， 第二次输入密码admin不会正常登录上去。 做一次浏览器重启。
        if login:
            self.retry_login()
        else:
            self.browser.close_and_quit()
            self.browser.init()
            self.browser.visit_url(self.login_url)
        return ret

    # endregion

    # region Security-basic
    def web_enter_security_basic(self):
        self.enter_security_basic()

    def web_pwd_modify(self, current_pwd, new_pwd):
        """
        在security basic页面修改密码
        """
        aklog_info()
        if current_pwd == new_pwd:
            aklog_info('current_pwd = new_pwd, not need modify')
            return True
        else:
            self.web_enter_security_basic()
            self.write_config(self.ele_info['security_user_combobox_xpath'], self.web_admin_username)
            self.browser.click_btn_by_xpath(self.ele_info['security_change_pwd_btn_xpath'])
            self.write_config(self.ele_info['change_pwd_window_old_pwd_xpath'], current_pwd)
            self.write_config(self.ele_info['change_pwd_window_new_pwd_xpath'], new_pwd)
            sleep(0.5)
            self.write_config(self.ele_info['change_pwd_window_confirm_pwd_xpath'], new_pwd)
            self.browser.click_btn_by_xpath(self.ele_info['change_pwd_window_change_btn_xpath'])
            sleep(1)
            self.browser.web_refresh()
            # 登出网页，用新密码再重新登录
            self.web_admin_pwd = new_pwd
            if self.retry_login():
                return True
            else:
                # self.web_admin_pwd = current_pwd
                aklog_error('modify pwd failed')
                self.browser.screen_shot()
                return False

    # endregion

    # region Security-advanced
    def web_enter_security_advanced(self):
        return self.enter_security_advanced()

    # endregion

    # endregion

    # region Telnet
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

    def telnet(self, cmd):
        aklog_info()
        try:
            return self.get_result_by_tln_or_ssh(cmd)
        except:
            return ''

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


if __name__ == '__main__':
    # device_info = {'device_name': 'X933', 'ip': '192.168.3.121'}
    # device_config = config_parse_device_config('config_X933_NORMAL')
    # param_put_browser_headless_enable(True)  # 是否开启浏览器无头模式
    # browser = libbrowser(device_info, device_config)
    # web = web_v4_device_NORMAL()
    # web.init_without_start(browser)
    # print(web.top_get_process_info('system_server'))

    print(sys.path)
    device_info = {'device_name': 'X915', 'ip': '192.168.3.121'}
    device_config = config_parse_device_config('config_X915_HARGER')
    print(device_config.testname)
