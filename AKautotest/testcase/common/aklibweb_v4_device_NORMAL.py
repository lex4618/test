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
from requests.adapters import SSLError


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


class web_v4_device_NORMAL(object):

    # <editor-fold desc="初始化相关">

    def __init__(self):
        self.web_branch = None
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
        self.firmware_version = ''
        self.model_name = ''
        self.model = ''
        self.oem_name = ''
        self.tln = None
        self.ssh = None
        self.tln_ssh_port_list = None
        self.tln_ssh_pwd_list = None
        self.page_menu_info = dict()  # 不同版本菜单目录兼容
        self.version_branch = ''
        self.force_replace_old_version = False
        self.test_file_root_path = ''
        self.original_process_info = dict()

    def init_without_start(self, browser):
        aklog_info('init_without_start')
        self.browser = browser
        self.device_config = browser.get_device_config()
        self.tmp_device_config = self.device_config
        self.device_info = browser.get_device_info()
        if 'device_name' in self.device_info:
            self.device_name = self.device_info['device_name']
            self.device_name_log = '[' + self.device_name + '] '
        if 'ip' in self.device_info:
            self.device_ip = self.device_info['ip']
            self.login_url = 'http://%s' % self.device_ip
        if 'MAC' in self.device_info:
            self.device_mac = self.device_info['MAC']
        elif 'mac' in self.device_info:
            self.device_mac = self.device_info['mac']
        self.rom_version = param_get_rom_version()
        self.model_name = self.device_config.get_model_name()
        self.oem_name = self.device_config.get_oem_name()

        if not self.version_branch:
            self.ele_info = config_parse_normal_web_element_info_from_xml('WEB4_0')
        else:
            self.ele_info = self.device_config.get_device_web_element_info(self.version_branch, 'WEB4_0')

        # 获取module机型分支目录下TestFile路径
        self.test_file_root_path = config_get_series_module_sub_path(
            self.model_name, self.version_branch, 'TestFile')

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
        self.browser.init()

    def start_and_login(self, url=None):
        if not self.is_opened_browser():
            self.browser.init()
        return self.login(url=url)

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

    def browser_close_and_reopen(self):
        if self.is_opened_browser():
            self.browser_close_and_quit()
        sleep(1)
        self.browser.init()

    def browser_close_and_reopen_login(self, url=None):
        if self.is_opened_browser():
            self.browser_close_and_quit()
        sleep(1)
        self.browser.init()
        return self.login(url=url)

    def reset_imgs(self):
        self.browser.reset_imgs()

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
        aklog_debug(self.device_name_log + 'restore_device_config')
        self.device_config = self.tmp_device_config

    def get_text_list_xpath(self, textlist):
        """
        返回: normalize-space(text())="3" or normalize-space(text())="4" or normalize-space(text())="5"
        """
        if type(textlist) == list:
            textxpath = ' or '.join(['normalize-space(text())="{}"'.format(i) for i in textlist])
        else:
            textxpath = 'normalize-space(text())="{}"'.format(textlist)
        return textxpath

    # </editor-fold>

    # <editor-fold desc="TestFile目录文件">

    def get_test_file(self, file_dir, file_name):
        series_file = '%s\\%s\\NORMAL\\%s' % (self.test_file_root_path, file_dir, file_name)
        model_normal_file = '%s\\%s\\%s\\NORMAL\\%s' % (self.test_file_root_path, file_dir, self.model_name, file_name)
        model_oem_file = '%s\\%s\\%s\\%s\\%s' % (self.test_file_root_path, file_dir, self.model_name,
                                                 self.oem_name, file_name)
        if os.access(model_oem_file, os.F_OK):
            test_file = model_oem_file
        elif os.access(model_normal_file, os.F_OK):
            test_file = model_normal_file
        elif os.access(series_file, os.F_OK):
            test_file = series_file
        else:
            test_file = ''
        if test_file.endswith('\\'):
            test_file = ''
        return test_file

    def get_image_cmp_file(self, file_name):
        return self.get_test_file('img_compare', file_name)

    def get_import_file(self, file_name):
        return self.get_test_file('config_file_import', file_name)

    def get_autop_config_file(self):
        autop_config_file = self.get_test_file('autop_config_file', 'autop.cfg')
        if not os.path.exists(autop_config_file):
            autop_config_file = self.device_config.get_autop_config_file()
        return autop_config_file

    # </editor-fold>

    # <editor-fold desc="网页通用操作API">

    @screenshot_when_except
    def menu_expand_and_click(self, menu_xpath, submenu_xpath, ignore_error=True):
        aklog_debug(self.device_name_log + 'menu_expand_and_click %s %s ' % (menu_xpath, submenu_xpath))
        if menu_xpath is None:
            aklog_error(self.device_name_log + '传入的菜单为None，请检查')
            return False
        self.browser.web_refresh(force=True)
        self.browser.switch_iframe_to_default()  # 门禁机型如果处于8849测试界面，需要先切换iframe回默认

        # 先判断是否已经在该界面了
        if submenu_xpath and '@href=' in submenu_xpath:
            try:
                url = self.browser.get_current_url()
                href = re.search('@href=[\"\'](.*)[\"\']', submenu_xpath).group(1)
                if url.endswith(href):
                    aklog_info('网页已经在目标页面')
                    return True
            except:
                pass
        # if menu_xpath:
        #     menu_class = self.browser.get_attribute_by_xpath(menu_xpath, 'className')
        #     if menu_class and 'ant-menu-submenu-selected' in menu_class:
        #         if 'ant-menu-submenu-open' not in menu_class:
        #             self.browser.click_btn_by_xpath(menu_xpath, 1)
        #         if submenu_xpath and self.browser.get_attribute_by_xpath(submenu_xpath, 'className') == \
        #                 self.ele_info['submenu_item_selected_class']:
        #             aklog_debug('当前已经处于 %s 界面' % submenu_xpath)
        #             return True
        #
        # for i in range(3):
        #     # 先判断是否存在菜单，如果不存在可能是有弹窗需要关闭或者在主页，或者页面显示异常，需要重新登录
        #     if not self.browser.is_exist_and_visible_ele_by_xpath(menu_xpath, 0.5):
        #         if i == 0 and self.browser.is_exist_alert():
        #             self.browser.alert_confirm_accept()
        #             continue
        #         elif i <= 1:
        #             self.retry_login()
        #             self.enter_menu_list_from_homepage()
        #             continue
        #         else:
        #             aklog_error(self.device_name_log + 'menu_expand_and_click failed')
        #             return False
        #     else:
        #         break
        # 有些页面没有子菜单或者不用再点击子菜单就进入了
        if not submenu_xpath:
            self.browser.click_btn_by_xpath(menu_xpath)
            menu_class = self.browser.get_attribute_by_xpath(menu_xpath, 'className')
            if not menu_class:
                aklog_debug('menu未找到，重新登录')
                self.browser.screen_shot()
                self.retry_login()
                self.enter_menu_list_from_homepage()
                menu_class = self.browser.get_attribute_by_xpath(menu_xpath, 'className')
            if menu_class and 'ant-menu-submenu-open' in menu_class:
                return True
            else:
                # status页面, 有时候重复进入, 或者8849界面进入, 需要两次点击才出现open.
                self.browser.click_btn_by_xpath(menu_xpath)
                menu_class = self.browser.get_attribute_by_xpath(menu_xpath, 'className')
                if menu_class and 'ant-menu-submenu-open' in menu_class:
                    return True
                aklog_error('%s 页面进入失败' % menu_xpath)
                return False

        for times in range(2):
            menu_class = self.browser.get_attribute_by_xpath(menu_xpath, 'className')
            if not menu_class:
                aklog_debug('menu未找到，重新登录')
                url = self.browser.get_current_url()
                if times == 0 and url in ['http://{}/#/'.format(self.device_ip),
                                          'https://{}/#/'.format(self.device_ip)]:
                    self.login()
                    self.enter_menu_list_from_homepage()
                    menu_class = self.browser.get_attribute_by_xpath(menu_xpath, 'className')
                else:
                    self.browser.screen_shot()
                    self.retry_login()
                    self.enter_menu_list_from_homepage()
                    menu_class = self.browser.get_attribute_by_xpath(menu_xpath, 'className')
            else:
                break

        if menu_class and 'ant-menu-submenu-open' not in menu_class:
            self.browser.click_btn_by_xpath(menu_xpath)

        if self.browser.get_attribute_by_xpath(submenu_xpath, 'className') == \
                self.ele_info['submenu_item_selected_class']:
            aklog_info('当前已经处于 %s 页面' % submenu_xpath)
            sleep(2)
            return True

        self.browser.click_btn_by_xpath(submenu_xpath)

        for i in range(3):
            # 判断是否进入页面
            self.browser.web_refresh()
            if self.browser.get_attribute_by_xpath(submenu_xpath, 'className') == \
                    self.ele_info['submenu_item_selected_class']:
                aklog_info('%s 页面进入成功' % submenu_xpath)
                sleep(1)
                return True
            elif not ignore_error:
                aklog_error('%s 页面进入失败' % submenu_xpath)
                self.browser.screen_shot()
                return False

            # 如果未进入页面，则再次点击菜单，如果还是未进入，则重新登录
            if not self.browser.is_exist_and_visible_ele_by_xpath(submenu_xpath, 0.5):
                if i == 0:
                    self.browser.click_btn_by_xpath(menu_xpath, 1)
                    self.browser.click_btn_by_xpath(submenu_xpath)
                    continue
                elif i == 1:
                    self.retry_login()
                    self.enter_menu_list_from_homepage()
                    if not self.browser.is_exist_and_visible_ele_by_xpath(submenu_xpath, 0.5):
                        self.browser.click_btn_by_xpath(menu_xpath, 1)
                    self.browser.click_btn_by_xpath(submenu_xpath)
                    continue
                else:
                    aklog_error('%s 页面进入失败' % submenu_xpath)
                    self.browser.screen_shot()
                    return False
            else:
                self.browser.click_btn_by_xpath(submenu_xpath)
                # # 安卓室内机系统弹窗都变成自定义样式弹窗,web_get_alert_text_and_confirm做了兼容
                self.web_get_alert_text_and_confirm()
                # if self.browser.is_exist_alert():
                #     self.browser.alert_confirm_accept()
                continue

    def web_refresh(self, wait_time=None, sec=1, force=False):
        if wait_time:
            sleep(wait_time)
        self.browser.web_refresh(sec, force)

    def screen_shot(self):
        self.browser.screen_shot()

    def clear_cache(self):
        """清空浏览器一小时的缓存"""
        url = self.browser.get_current_url()
        try:
            self.browser.driver.get('chrome://settings/clearBrowserData')
            sleep(2)
            self.browser.driver.execute_script(
                'document.querySelector("body > settings-ui").shadowRoot.querySelector("#main")'
                '.shadowRoot.querySelector("settings-basic-page")'
                '.shadowRoot.querySelector("#basicPage > settings-section:nth-child(11) > settings-privacy-page")'
                '.shadowRoot.querySelector("settings-clear-browsing-data-dialog")'
                '.shadowRoot.querySelector("#clearBrowsingDataConfirm").click()')
            sleep(5)
        except:
            aklog_error('清空缓存失败!!!')
        else:
            aklog_info('成功清空缓存')
        finally:
            self.browser.driver.get(url)
            self.retry_login()
            self.browser.driver.get(url)

    def get_web40_xpath(self, xpath, index=None, subfix=''):
        """
        subfix: 修正量, 接后续的xpath表达式
        """
        if xpath.startswith('/') or '//' in xpath:
            return xpath
        if '->' in xpath:
            title, sub = [i.strip() for i in xpath.split('->')]
            if '|' in xpath:
                if '|' in title:
                    t1, t2 = title.split('|')
                    prefix = '//label[normalize-space(text())="{}" or normalize-space(text())="{}"]'.format(t1.strip(),
                                                                                                            t2.strip())
                else:
                    prefix = '//label[normalize-space(text())="{}"]'.format(title)
                if '|' in sub:
                    s1, s2 = sub.split('|')
                    prefix = prefix + '/../..//*[(normalize-space(text())="{}" or normalize-space(text())="{}")and @class]/..//'.format(
                        s1.strip(),
                        s2.strip())
                else:
                    prefix = prefix + '/../..//*[normalize-space(text())="{}" and @class]/..//'.format(sub)
            else:
                prefix = '//label[normalize-space(text())="{}"]/../..//*[normalize-space(text())="{}" and @class]/..//'.format(
                    title, sub)
            eleXpath = prefix + 'input' + ' | ' + prefix + 'div[@role="combobox"]' + '|' + prefix + 'label[2][text()]'
            if index is None:
                return eleXpath + subfix
            else:
                return '(' + eleXpath + ')[{}]'.format(index + 1) + subfix
        else:
            if index is None:
                if '|' in xpath:
                    x1, x2 = xpath.split('|')
                    prefix = '//*[(normalize-space(text())="{}" or normalize-space(text())="{}")and @class]/..//'.format(
                        x1.strip(), x2.strip())
                else:
                    prefix = '//*[normalize-space(text())="{}" and @class]/..//'.format(xpath)
                eleXpath = prefix + 'input' + ' | ' + prefix + 'div[@role="combobox"]' + '|' + prefix + 'label[2][text()]'
                return eleXpath + subfix
            else:
                if '|' in xpath:
                    x1, x2 = xpath.split('|')
                    prefix = '//*[(normalize-space(text())="{}" or normalize-space(text())="{}")and @class]/..//'.format(
                        x1.strip(), x2.strip())
                else:
                    prefix = '//*[normalize-space(text())="{}" and @class]/..//'.format(xpath)
                eleXpath = '(' + prefix + 'input' + ' | ' + prefix + 'div[@role="combobox"]' + ' | ' + prefix + 'label[2][text()]' + ')[{}]'.format(
                    index + 1)
                return eleXpath + subfix

    def web_compare_image(self, xpath, pic, percent=0):
        aklog_info()
        if not os.path.exists(pic):
            aklog_error('不存在图片: {}'.format(pic))
            return False
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
                # File_process.remove_file(TEMP_FILE)
                return ret

                sleep(2)

    def wait_wan_connected(self, timeout=120):
        """等待设备网络可以连接上"""
        aklog_info()
        cur_time = time.time()
        for i in range(120):
            if time.time() - cur_time > timeout:
                return False
            try:
                requests.get('http://%s' % self.device_ip, timeout=2)
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

    # <editor-fold desc="点击按钮操作">

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

    def click_btn_by_id(self, eleid, sec=0.2, visible=True):
        aklog_debug()
        return self.browser.click_btn_by_id(eleid, sec, visible=visible)

    def click_btn_by_xpath(self, ele_xpath, sec=0.2, visible=True):
        aklog_debug()
        return self.browser.click_btn_by_xpath(ele_xpath, sec, visible=visible)

    def click_btn_and_sleep_by_xpath(self, ele_xpath, sec=0.2, visible=True):
        """封装通过xpath进行button操作并延时"""
        aklog_debug()
        return self.browser.click_btn_by_xpath(ele_xpath, sec, visible=visible)

    def click_btn_by_text(self, text, sec=0.2, title=None):
        """通过按钮的文本来定位，需要页面上按钮是唯一的才行，不能存在两个相同名称的按钮"""
        text = text.strip()
        if title:
            ele_xpath = '//*[normalize-space(text())="%s"]/../..//span[normalize-space(text())="%s"]/..' % (title, text)
        else:
            ele_xpath = '//span[normalize-space(text())="%s"]/..' % text
        return self.browser.click_btn_by_xpath(ele_xpath, sec)

    # </editor-fold>

    # <editor-fold desc="读写配置">

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
            if type(id_name_xpath) == str:
                ele = self.browser.adapt_element(id_name_xpath, timeout)
            else:
                ele = id_name_xpath
            if not ele:
                aklog_error(self.device_name_log + '元素不存在')
                return False
            elif not ele.is_enabled():
                aklog_warn(self.device_name_log + '元素处于不可操作状态')
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
                    originally_selected_ele_list = ele.find_elements('xpath',
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
                        value = value.strip()
                        if '|' in value:
                            list1 = value.split('|')
                            list1 = [i.strip() for i in list1 if i.strip()]
                            option_ele_xpath = '//div[@id="%s"]/ul/li[' % aria_controls
                            for i in list1:
                                option_ele_xpath += 'normalize-space(text())="%s"' % i
                                if i != list1[-1]:
                                    option_ele_xpath += ' or '
                            option_ele_xpath += ']'
                        else:
                            option_ele_xpath = '//div[@id="%s"]/ul/li[normalize-space(text())="%s"]' % (
                                aria_controls, value)
                    options_ele_xpath.append(option_ele_xpath)
                ret = self.browser.select_options_by_box_ele(ele, *options_ele_xpath)
                if not ret:
                    aklog_error('write config: {} -> {} 失败'.format(id_name_xpath, values))
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
                        value = value.strip()
                        option_ele_xpath = '//div[@id="%s"]/ul/li[normalize-space(text())="%s"]' % (
                            aria_controls, value)
                    options_ele_xpath.append(option_ele_xpath)
                self.browser.select_options_by_box_ele(combobox_ele, *options_ele_xpath)
            else:
                # 文本输入框
                value = values[0]
                # 有些输入框清空提交判断为空是否提示，不能用clear()方法，得用按键方式操作
                if not clear_input_by_keys:
                    ele.clear()
                    sleep(0.1)
                    if ele.get_attribute('value'):
                        ele.send_keys(Keys.CONTROL, 'a')
                        ele.send_keys(Keys.BACKSPACE)
                        sleep(0.1)
                else:
                    ele.send_keys(Keys.CONTROL, 'a')
                    ele.send_keys(Keys.BACKSPACE)
                    sleep(0.1)
                    if ele.get_attribute('value'):
                        ele.clear()
                        sleep(0.1)
                ele.send_keys(str(value))
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
            aklog_info(traceback.format_exc())
            return None

    def __get_tag(self, ele):
        if not ele:
            return False
        try:
            return ele.tag_name
        except:
            return False

    def __adapt_element(self, id_name_xpath, driver, timeout, log_xpath=None):
        """2022.5.31 915 web4.0上没有id和name属性的控件"""
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
            if file is not None:
                self.browser.upload_file_by_xpath(self.ele_info['select_file_input'], file)
            if accept:
                # 如果上传格式错误的文件，可能会直接弹出失败提示
                submit_tips1 = self.get_submit_tips(2)
                if submit_tips1:
                    if submit_tips1 == 'Upload File Finished':
                        return True
                    else:
                        self.click_select_file_cancel()
                        return submit_tips1
                # 点击上传，然后获取上传结果
                self.click_select_file_upload()
                # 安卓室内机系统弹窗都变成自定义样式弹窗,web_get_alert_text_and_confirm做了兼容
                self.web_get_alert_text_and_confirm(1)
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
            aklog_debug(traceback.format_exc())
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
            sleep(0.2)
            option_elements = self.browser.get_elements_by_xpath(option_ele_xpath)
            options_list = []
            for option_ele in option_elements:
                option_text = option_ele.text
                options_list.append(option_text)
            self.browser.click_ele(ele)
            sleep(0.2)
            aklog_debug('options_list: %s' % options_list)
            return options_list
        else:
            aklog_error('下拉框类型不一致，请检查')
            return None

    def get_text_by_label_name(self, label, title=None):
        """根据label名称获取对应的内容"""
        aklog_debug()
        label = label.strip()
        if title:
            xpath = '//label[normalize-space(text())="%s"]/../..//label[normalize-space(text())="%s"]/../label[2]' % (
                title, label)
        else:
            xpath = '//label[normalize-space(text())="%s"]/../label[2]' % label
        return self.browser.get_value_by_xpath(xpath)

    def input_edit_by_modal_label_name(self, label, content):
        """添加或编辑窗口，根据label，输入内容"""
        xpath = '//*[@class="ant-modal-body"]//label[normalize-space(text())="%s"]/../input' % label
        self.write_config(xpath, content)

    def select_by_modal_label_name(self, label, content):
        """添加或编辑窗口，根据label，下拉框选择"""
        xpath = '//*[@class="ant-modal-body"]//label[normalize-space(text())="%s"]/..//div[@role="combobox"]' % label
        self.write_config(xpath, content)

    def input_edit_and_sleep_by_id(self, edit_id, content, sec=0.2):
        """封装通过id输入edit操作并延时"""
        self.browser.input_edit_by_id(edit_id, content)
        sleep(sec)

    def input_edit_and_sleep_by_xpath(self, edit_xpath, content, sec=0.2):
        """封装通过id输入edit操作并延时"""
        self.write_config(edit_xpath, content)
        sleep(sec)

    def input_edit_and_sleep_by_name(self, edit_id, content, sec=0.2):
        """封装通过name输入edit操作并延时"""
        self.browser.input_edit_by_name(edit_id, content)
        sleep(sec)

    # </editor-fold>

    # <editor-fold desc="左右两个选择框相关操作">

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
            title = title.strip()
            enabled_options = '//label[normalize-space(text())="%s"]/../..' \
                              '//*[@class="ak-common-transfer-div"]/div/div[3]//li//input' % title
        else:
            enabled_options = '//*[@class="ak-common-transfer-div"]/div/div[3]//li//input'
        self.browser.check_multi_boxs_by_xpath(enabled_options)
        sleep(0.5)
        if title:
            left_btn = '//label[normalize-space(text())="%s"]/../..' \
                       '//*[@class="anticon anticon-left"]/..' % title
        else:
            left_btn = '//*[@class="anticon anticon-left"]/..'
        self.browser.click_btn_by_xpath(left_btn)
        if selects:
            if selects == 'all':
                if title:
                    disabled_options = '//label[normalize-space(text())="%s"]/../..' \
                                       '//*[@class="ak-common-transfer-div"]/div/div[1]//li//input' % title
                else:
                    disabled_options = '//*[@class="ak-common-transfer-div"]/div/div[1]//li//input'
                self.browser.check_multi_boxs_by_xpath(disabled_options)
                sleep(0.5)
            else:
                # 根据名称选择
                for select in selects:
                    if title:
                        disabled_options = '//label[normalize-space(text())="%s"]/../..//*[@class="ak-common-transfer-div"]' \
                                           '/div/div[1]//li[@title="%s"]//input' % (title, select)
                    else:
                        disabled_options = '//*[@class="ak-common-transfer-div"]/div/div[1]//li[@title="%s"]//input' \
                                           % select
                    self.browser.check_box_by_xpath(disabled_options)
                sleep(0.5)
            if title:
                right_btn = '//label[normalize-space(text())="%s"]/../..' \
                            '//*[@class="anticon anticon-right"]/..' % title
            else:
                right_btn = '//*[@class="anticon anticon-right"]/..'
            self.browser.click_btn_by_xpath(right_btn)

    def get_multi_unselected_options(self, title=None):
        """
        左右两个选择框（比如Audio Codecs），获取左边未选择的选项
        title: 如果一个页面存在多个这种选择框，则要传入标题
        """
        if title:
            enabled_options = '//label[text()="%s"]/../..' \
                              '//*[@class="ak-common-transfer-div"]/div/div[1]//li' % title
        else:
            enabled_options = '//*[@class="ak-common-transfer-div"]/div/div[1]//li'
        return self.browser.get_elements_attribute_by_xpath(enabled_options, 'title')

    def get_multi_selected_options(self, title=None):
        """
        左右两个选择框（比如Audio Codecs），获取右边已选择的选项
        title: 如果一个页面存在多个这种选择框，则要传入标题
        """
        if title:
            enabled_options = '//label[normalize-space(text())="%s"]/../..' \
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
            aklog_error('传入的option_list不是list类型')
            return False
        if title:
            up_btn = '//label[normalize-space(text())="%s"]/../..//*[@class="ak-common-transfer-button"]/button[1]' % title
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
                    enabled_option = '//label[normalize-space(text())="%s"]/../..//*[@class="ak-common-transfer-div"]' \
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

    # </editor-fold>

    # <editor-fold desc="表格翻页、删除相关">

    def click_page_prev(self, title=None):
        if title:
            ele_xpath = '//label[normalize-space(text())="%s"]/../..//span[normalize-space(text())="Prev"]/..' % title
        else:
            ele_xpath = '//span[normalize-space(text())="Prev"]/..'
        self.click_btn_by_xpath(ele_xpath)

    def click_page_next(self, title=None):
        if title:
            ele_xpath = '//label[normalize-space(text())="%s"]/../..//span[normalize-space(text())="Next"]/..' % title
        else:
            ele_xpath = '//span[normalize-space(text())="Next"]/..'
        self.click_btn_by_xpath(ele_xpath)

    def get_table_total_num(self, title=None, refresh=False):
        """
        获取列表所有数量
        cur_page： 有些列表无法获取总数量，那么只能获取当前页面的数量，注意列表总数量不能多于一页数量
        """
        aklog_debug()
        if title:
            ele_xpath = '//label[normalize-space(text())="%s"]/../..//*[@class="ak-common-table-footer"]/label[2]' % title
        else:
            ele_xpath = '//*[@class="ak-common-table-footer"]/label[2]'
        if refresh:
            self.web_refresh()
        total_num = self.browser.get_value_by_xpath(ele_xpath, print_trace=False)
        if total_num is not None and total_num is not False:
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
                aklog_debug('获取不到页数，通过计算行数来获取数量，只能计算一页')
                if title:
                    table_cow_xpath = '//label[normalize-space(text())="%s"]/../..//tbody/tr' % title
                else:
                    table_cow_xpath = '//tbody/tr'
                total_num = self.browser.get_ele_counts_by_xpath(table_cow_xpath)
        aklog_debug('total_num: %s' % total_num)
        return total_num

    def get_table_cur_page_row_num(self, title=None):
        """有些列表无法获取总数量，那么只能获取当前页面的数量"""
        if title:
            tr_xpath = '//label[normalize-space(text())="%s"]/../..//tbody/tr' % title
        else:
            tr_xpath = '//tbody/tr'
        counts = self.browser.get_ele_counts_by_xpath(tr_xpath)
        return counts

    def get_total_page_num(self, title=None):
        """获取列表页数"""
        aklog_debug()
        if title:
            ele_xpath = '//label[normalize-space(text())="%s"]/../..' \
                        '//*[@class="ak-common-table-footer"]/span[contains(text(), "/")]' % title
        else:
            ele_xpath = '//*[@class="ak-common-table-footer"]/span[contains(text(), "/")]'
        page_num = self.browser.get_value_by_xpath(ele_xpath, print_trace=False)
        if page_num is None:
            aklog_debug('当前列表不显示页数')
            return None
        total_page_num = int(page_num.split('/')[1].strip())
        aklog_debug('total_page_num: %s' % total_page_num)
        return total_page_num

    def get_cur_page_num(self, title=None):
        """获取当前位于第几页"""
        if title:
            ele_xpath = '//label[normalize-space(text())="%s"]/../..' \
                        '//*[@class="ak-common-table-footer"]/span[contains(text(), "/")]' % title
        else:
            ele_xpath = '//*[@class="ak-common-table-footer"]/span[contains(text(), "/")]'
        page_num = self.browser.get_value_by_xpath(ele_xpath)
        cur_page_num = int(page_num.split('/')[0].strip())
        return cur_page_num

    def get_table_attribute_info(self, attribute=None, title=None, **base_attr):
        """
        获取列表信息，根据某个属性（比如id或name），去获取其他属性的值
        attribute: 想要获取的属性值, 取列表标题th节点key值，也可以为空，表示获取整行信息，返回字典类型
        base_attr: 选择的根据属性，一般为id或者name，取列表标题th节点key值，id='1', 或 name='test'，传入一个即可
        title: 列表的标题
        """
        aklog_debug()
        total_num = self.get_table_total_num()
        if not total_num:
            aklog_error('列表为空')
            return None

        if title:
            next_ele_xpath = '//label[normalize-space(text())="%s"]/../..//span[normalize-space(text())="Next"]/..' % title
            key_ele_xpath = '//label[normalize-space(text())="%s"]/../..//thead/tr/th' % title
        else:
            next_ele_xpath = '//span[normalize-space(text())="Next"]/..'
            key_ele_xpath = '//thead/tr/th'

        # 获取标题列表
        key_list = self.browser.get_elements_attribute_by_xpath(key_ele_xpath, 'key')
        # 获取根据属性的key和value值
        base_key, base_value = tuple(base_attr.items())[0]
        # 然后获取根据属性位于列表中哪一列
        base_index = key_list.index(base_key) + 1

        counts = 1
        row = 1
        while counts <= total_num:
            value_list = []
            if title:
                base_ele_xpath = '//label[normalize-space(text())="%s"]/../..//tbody/tr[%s]/td[%s]//label' % (
                    title, row, base_index)
            else:
                base_ele_xpath = '//tbody/tr[%s]/td[%s]//label' % (row, base_index)

            get_base_value = self.browser.get_value_by_xpath(base_ele_xpath, 0.5)
            if get_base_value == str(base_value):
                for col in range(1, len(key_list) + 1):
                    if title:
                        value_ele_xpath = '//label[normalize-space(text())="%s"]/../..//tbody/tr[%s]/td[%s]//label' % (
                            title, row, col)
                    else:
                        value_ele_xpath = '//tbody/tr[%s]/td[%s]//label' % (row, col)
                    value = self.browser.get_value_by_xpath(value_ele_xpath, 0.5)
                    if value is None:
                        value = ''
                    value_list.append(value)
                row_info = dict(zip(key_list, value_list))
                aklog_printf(row_info)
                if attribute:
                    return row_info.get(attribute)
                else:
                    return row_info
            elif get_base_value is None and self.browser.get_ele_status_by_xpath(next_ele_xpath):
                self.click_btn_by_xpath(next_ele_xpath)
                row = 1
                continue
            else:
                counts += 1
                row += 1
                continue
        aklog_error('未找到')
        return None

    def click_table_edit_btn(self, title=None, **base_attr):
        """选择列表其中一条，点击编辑按钮"""
        aklog_debug()
        total_num = self.get_table_total_num()
        if not total_num:
            aklog_error('列表为空')
            return None

        if title:
            next_ele_xpath = '//label[normalize-space(text())="%s"]/../..//span[normalize-space(text())="Next"]/..' % title
            key_ele_xpath = '//label[normalize-space(text())="%s"]/../..//thead/tr/th' % title
        else:
            next_ele_xpath = '//span[normalize-space(text())="Next"]/..'
            key_ele_xpath = '//thead/tr/th'
        # 获取标题列表
        key_list = self.browser.get_elements_attribute_by_xpath(key_ele_xpath, 'key')
        # 获取根据属性的key和value值
        base_key, base_value = tuple(base_attr.items())[0]
        # 然后获取根据属性位于列表中哪一列
        base_index = key_list.index(base_key) + 1

        counts = 1
        row = 1
        while counts <= total_num:
            if title:
                base_ele_xpath = '//label[normalize-space(text())="%s"]/../..//tbody/tr[%s]/td[%s]//label' % (
                    title, row, base_index)
            else:
                base_ele_xpath = '//tbody/tr[%s]/td[%s]//label' % (row, base_index)

            get_base_value = self.browser.get_value_by_xpath(base_ele_xpath, 0.5)
            if get_base_value == str(base_value):
                if title:
                    edit_ele_xpath = '//label[normalize-space(text())="%s"]/../..//tbody/tr[%s]' \
                                     '//i[@tabindex="-1" and @class="anticon"]' % (title, row)
                else:
                    edit_ele_xpath = '//tbody/tr[%s]//i[@tabindex="-1" and @class="anticon"]' % row
                return self.browser.click_btn_by_xpath(edit_ele_xpath)
            elif get_base_value is None and self.browser.get_ele_status_by_xpath(next_ele_xpath):
                self.click_btn_by_xpath(next_ele_xpath)
                row = 1
                continue
            else:
                counts += 1
                row += 1
                continue
        aklog_error('未找到')
        return False

    def table_check_by_index(self, index, title=None):
        """列表根据序号勾选，index可以传入：'1', '123'"""
        if title:
            if type(title) == list:
                xpath = self.get_text_list_xpath(title)
                for i in str(index):
                    self.write_config('//label[%s]/../..//tbody/tr[%s]/td[1]//input' % (xpath, i), 1)
            else:
                for i in str(index):
                    self.write_config(
                        '//label[normalize-space(text())="%s"]/../..//tbody/tr[%s]/td[1]//input' % (title, i), 1)
        else:
            for i in str(index):
                self.write_config('//tbody/tr[%s]/td[1]//input' % i, 1)

    def go_to_page_by_index(self, index, title=None):
        if title:
            go_num_input_xpath = '//label[normalize-space(text())="%s"]/../..//input[@role="spinbutton"]' % title
            go_btn_xpath = '//label[normalize-space(text())="%s"]/../..//span[normalize-space(text())="Go"]/..' % title
        else:
            go_num_input_xpath = '//input[@role="spinbutton"]'
            go_btn_xpath = '//span[normalize-space(text())="Go"]/..'
        self.write_config(go_num_input_xpath, str(index))
        self.click_btn_by_xpath(go_btn_xpath)

    def table_page_turning_test(self, title=None):
        """列表翻页测试，需要事先添加超过一页的数量"""
        aklog_info()
        # 一个页面如果存在多个列表，那么需要根据标题选择
        if title:
            prev_btn_xpath = '//label[normalize-space(text())="%s"]/../..//span[normalize-space(text())="Prev"]/..' % title
            next_btn_xpath = '//label[normalize-space(text())="%s"]/../..//span[normalize-space(text())="Next"]/..' % title
        else:
            prev_btn_xpath = '//span[normalize-space(text())="Prev"]/..'
            next_btn_xpath = '//span[normalize-space(text())="Next"]/..'

        self.web_refresh()
        sleep(2)
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
        sleep(1)
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
        sleep(1)
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
        sleep(1)
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

    def click_table_add(self, title=None):
        if title is not None:
            if type(title) == list:
                textxpath = self.get_text_list_xpath(title)
                ele_xpath = '//label[{}]/../..//button//*[normalize-space(text())="Add"]'.format(textxpath)
            else:
                if type(title) == int:
                    ele_xpath = '(//*[@class="ak-common-table"])[%s]//*[normalize-space(text())="Add"]' % title
                else:
                    ele_xpath = '//label[normalize-space(text())="%s"]/../..//button//*[normalize-space(text())="Add"]' % title
        else:
            ele_xpath = '//*[@class="ak-common-table"]//button//*[normalize-space(text())="Add"]'
        return self.click_btn_by_xpath(ele_xpath)

    def click_table_export(self, title=None):
        if title:
            if type(title) == list:
                textxpath = self.get_text_list_xpath(title)
                ele_xpath = '//label[{}]/../..//button//*[normalize-space(text())="Export"]'.format(textxpath)
            else:
                if type(title) == int:
                    ele_xpath = '(//*[@class="ak-common-table"])[%s]//*[normalize-space(text())="Export"]' % title
                else:
                    ele_xpath = '//label[normalize-space(text())="%s"]/../..//button//*[normalize-space(text())="Export"]' % title
        else:
            ele_xpath = '//*[@class="ak-common-table"]//button//*[normalize-space(text())="Export"]'
        self.click_btn_by_xpath(ele_xpath)

    def click_table_import(self, title=None):
        if title:
            if type(title) == list:
                textxpath = self.get_text_list_xpath(title)
                ele_xpath = '//label[{}]/../..//button//*[normalize-space(text())="Import"]'.format(textxpath)
            else:
                if type(title) == int:
                    ele_xpath = '(//*[@class="ak-common-table"])[%s]//*[normalize-space(text())="Import"]' % title
                else:
                    ele_xpath = '//label[normalize-space(text())="%s"]/../..//button//*[normalize-space(text())="Import"]' % title
        else:
            ele_xpath = '//*[@class="ak-common-table"]//button//*[normalize-space(text())="Import"]'
        self.click_btn_by_xpath(ele_xpath)

    def click_table_delete(self, title=None):
        if title is not None:
            if type(title) == list:
                textxpath = self.get_text_list_xpath(title)
                ele_xpath = '//label[{}]/../..//*[@class="ak-common-table-footer-btn-label" and normalize-space(text())="Delete"]/..'.format(
                    textxpath)
            else:
                if type(title) == int:
                    ele_xpath = '(//*[@class="ak-common-table-footer-btn-label" and normalize-space(text())="Delete"])[%s]/..' % title
                else:
                    ele_xpath = '//label[normalize-space(text())="%s"]/../..' \
                                '//*[@class="ak-common-table-footer-btn-label" and normalize-space(text())="Delete"]/..' % title
        else:
            ele_xpath = '//*[@class="ak-common-table-footer-btn-label" and normalize-space(text())="Delete"]/..'
        self.click_btn_by_xpath(ele_xpath)

    def click_table_delete_all(self, title=None):
        if title is not None:
            if type(title) == list:
                textxpath = self.get_text_list_xpath(title)
                ele_xpath = '//label[{}]/../..//*[@class="ak-common-table-footer-btn-label" and normalize-space(text())="Delete All"]/..'.format(
                    textxpath)
            else:
                if type(title) == int:
                    ele_xpath = '(//*[@class="ak-common-table-footer-btn-label" and normalize-space(text())="Delete All"])[%s]/..' % title
                else:
                    ele_xpath = '//label[normalize-space(text())="%s"]/../..' \
                                '//*[@class="ak-common-table-footer-btn-label" and normalize-space(text())="Delete All"]/..' % title
        else:
            ele_xpath = '//*[@class="ak-common-table-footer-btn-label" and normalize-space(text())="Delete All"]/..'
        self.click_btn_by_xpath(ele_xpath)

    def delete_table_by_index(self, index, confirm=True, title=None):
        """列表根据序号选择删除, index可以传入：'1', '123'"""
        self.table_check_by_index(index, title)
        self.click_table_delete(title)
        if confirm:
            self.browser.alert_confirm_accept()
            sleep(1)
        else:
            self.browser.alert_confirm_cancel()

    def delete_table_all(self, title=None, refresh=True):
        """删除列表所有"""
        if title:
            delete_all_btn_xpath = '//label[normalize-space(text())="%s"]/../..//*[@class="ak-common-table-footer-btn-label" ' \
                                   'and normalize-space(text())="Delete All"]/..' % title
        else:
            delete_all_btn_xpath = '//*[@class="ak-common-table-footer-btn-label" and normalize-space(text())="Delete All"]/..'
        if refresh:
            self.web_refresh()
        if self.browser.get_ele_status_by_xpath(delete_all_btn_xpath):
            self.click_btn_by_xpath(delete_all_btn_xpath)
            self.browser.alert_confirm_accept()
            self.web_get_alert_text_and_confirm()
            sleep(0.5)
        else:
            aklog_info(self.device_name_log + 'Delete All不可点击，列表应该已被全部删除')

    def table_delete_test(self, title=None, refresh=True):
        """
        表格删除测试，需要先进入列表页面，且需要先添加至少2条以上数据
        有些列表无法获取总数量，那么只能获取当前页面的数量，注意列表总数量不能多于一页数量
        """
        aklog_info()
        if refresh:
            self.web_refresh()
            sleep(2)
        total_num1 = self.get_table_total_num(title)
        if total_num1 < 2:
            aklog_error('列表数量太少，请先添加至少大于2条')
            return False
        result = True
        self.delete_table_by_index('1', False, title)
        total_num2 = self.get_table_total_num(title, refresh)
        if total_num2 != total_num1:
            aklog_error('取消删除失败，仍被删除')
            result = False
        self.delete_table_by_index('1', True, title)
        total_num3 = self.get_table_total_num(title, refresh)
        if total_num3 >= total_num2:
            aklog_error('删除失败')
            result = False
        self.delete_table_all(title)
        total_num4 = self.get_table_total_num(title, refresh)
        if total_num4 != 0:
            aklog_error('删除所有失败')
            result = False
        return result

    # </editor-fold>

    # <editor-fold desc="弹窗相关">

    def alert_confirm_accept_and_sleep(self, sec=0.2):
        """封装web端弹窗确认操作并延时"""
        self.browser.alert_confirm_accept()
        sleep(sec)

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

    # </editor-fold>

    # <editor-fold desc="提交结果、输入框结果判断">
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
                aklog_info('不存在置红提示')
                return None
            red_tips = []
            ele_counts = len(elements)
            sleep(2)
            for i in range(ele_counts):
                for j in range(2):
                    self.browser.move_mouse_to_element(elements[i], 1)
                    red_tip = self.browser.get_visible_value_by_xpath(
                        '//*[contains(@class,"ant-tooltip ant-tooltip-placement") and '
                        'not(contains(@style,"display: none;"))]//span[@class="ak-tooltips-label"]')
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
                sleep(1)
                j += 1
                continue
            else:
                sleep(1)
                i += 1
                continue
        aklog_error('get submit tips failed')
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
                aklog_error(submit_tips)
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
        sleep(0.5)
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
        sleep(0.5)
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

    def get_import_file_format_tips(self, import_btn):
        """获取文件上传的格式提示语"""
        self.browser.click_btn_by_xpath(import_btn)
        sleep(1)
        format_tips = self.browser.get_visible_value_by_xpath('//*[@class="ak-modal-file-input-title-label"]')
        self.click_select_file_cancel()
        return format_tips

    # </editor-fold>

    # <editor-fold desc="时间日期输入框设置">

    def input_date_by_xpath(self, ele_xpath, date_str):
        """设置日期方法，date_str格式: 2022-02-28"""
        aklog_info(self.device_name_log + 'input_date_by_xpath, ele_xpath: %s, date: %s' % (ele_xpath, date_str))
        date_title1 = trans_date_fmt(date_str, '%Y-%m-%d', '%#d %B %Y')
        date_title2 = trans_date_fmt(date_str, '%Y-%m-%d', '%B %#d, %Y')
        self.click_btn_by_xpath(ele_xpath, 0.5)
        self.write_config('//*[@class="ant-calendar-date-input-wrap"]/input', date_str)
        sleep(0.5)
        self.click_btn_by_xpath('//*[@title="%s" or @title="%s"]' % (date_title1, date_title2))

    def input_time_by_xpath(self, ele_xpath, time_str):
        """设置时间方法，time_str格式：11:08 or 11:08:22"""
        aklog_info(self.device_name_log + 'input_time_by_xpath, ele_xpath: %s, time: %s' % (ele_xpath, time_str))
        self.browser.click_btn_by_xpath(ele_xpath)
        sleep(0.5)
        self.write_config('//*[@class="ant-time-picker-panel-input "]', '%s ' % time_str)
        sleep(0.5)
        self.click_btn_by_xpath('//*[@class="ant-time-picker-panel-addon"]/button')

    # </editor-fold>

    # <editor-fold desc="其他">

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

        sleep(10)
        for i in range(5):
            if self.browser.is_exist_ele_by_xpath(self.ele_info['login_username_xpath']):
                break
            else:
                self.browser.web_refresh(force=True)
                sleep(5)
                continue
        login_status = self.login_status
        result = self.login(url)
        self.login_status = login_status
        if close:
            self.browser.close_window()
            self.browser.switch_window(0)
        return result

    # </editor-fold>

    # </editor-fold>

    # <editor-fold desc="登录相关">
    def login(self, url=None, raise_enable=True):
        """登录网页"""
        aklog_info(self.device_name_log + 'login')
        if not url:
            url = self.login_url
        if not self.browser.visit_url(url):
            aklog_error('网页 %s 访问失败' % url)
            self.browser.screen_shot()
            self.login_status = False
            if raise_enable:
                self.browser_close_and_quit()
                sleep(2)
                raise RuntimeError
            else:
                return False
        self.browser.web_refresh(force=True)
        login_counts = 0
        web_admin_pwd_tmp = self.web_admin_pwd
        i = 0
        while i < 5:
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath']):
                self.write_config(self.ele_info['login_username_xpath'], self.web_admin_username)
                self.write_config(self.ele_info['login_password_xpath'], self.web_admin_pwd)
                self.browser.click_btn_by_class_name(self.ele_info['login_btn_class'])
                login_counts += 1

                if self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_logout_class']) or \
                        self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['change_pwd_window_title_xpath']) \
                        or self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_status_class']):
                    aklog_info(self.device_name_log + '登录网页 %s 成功' % url)
                    self.login_status = True
                    self.modify_default_login_password()
                    self.get_menu_xpath_info(True)
                    if self.web_admin_pwd == 'Aa12345678' or self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678'):
                        return True
                    else:
                        break

                # 如果登录失败，则更改密码重新登录
                if login_counts == 1:
                    aklog_error(self.device_name_log + '密码: %s 登录失败，改密重登' % self.web_admin_pwd)
                    self.browser.screen_shot()
                    # 第一次登录失败，改用客户定制的admin用户的密码来登录
                    self.web_admin_pwd = self.device_config.get_web_admin_passwd()
                    continue
                elif login_counts == 2:
                    aklog_error(self.device_name_log + '密码: %s 登录失败，改密重登' % self.web_admin_pwd)
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
                    sleep(190)
                    self.web_admin_username = 'admin'
                    self.web_admin_pwd = 'Ak12345678'
                    continue
                else:
                    aklog_fatal(self.device_name_log + '登录网页 %s 失败' % url)
                    self.browser.screen_shot()
                    self.login_status = False
                    if raise_enable:
                        self.browser_close_and_quit()
                        sleep(2)
                        raise RuntimeError
                    else:
                        return False
            elif self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_logout_class']) or \
                    self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['change_pwd_window_title_xpath']) \
                    or self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_status_class']):
                aklog_info(self.device_name_log + '网页已登录，无需再重新登录')
                self.login_status = True
                self.modify_default_login_password()
                self.get_menu_xpath_info(True)
                if self.web_admin_pwd == 'Aa12345678' or self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678'):
                    return True
                else:
                    break
            else:
                sleep(5)
                self.browser.web_refresh()
                i += 1
                continue
        aklog_fatal(self.device_name_log + '登录网页 %s 失败' % url)
        self.browser.screen_shot()
        self.web_admin_pwd = web_admin_pwd_tmp
        self.login_status = False
        if raise_enable:
            self.browser_close_and_quit()
            sleep(2)
            raise RuntimeError
        else:
            return False

    def retry_visit_url(self, url=None):
        aklog_info(self.device_name_log + 'retry_visit_url: %s' % url)
        if url and '/#/' in url:
            pass
        else:
            url = self.login_url
        return self.browser.visit_url(url)

    def retry_login(self, modify_default_pwd=True, raise_enable=True):
        aklog_info(self.device_name_log + 'retry_login')
        for j in range(3):
            if j == 1:
                sleep(int(self.device_config.get_reboot_default_time()))

            # 如果有弹窗，确定弹窗后返回登录界面说明登录超时需要等待3分钟
            alert_text = self.browser.get_alert_text()
            if alert_text:
                self.browser.alert_confirm_accept()
                if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath']):
                    sleep(190)

            if j == 2 and not alert_text:
                sleep(190)

            current_url = self.browser.get_current_url()
            self.browser.close_and_quit()
            sleep(j * 2 + 2)
            self.browser.init()

            if not self.retry_visit_url(current_url):
                aklog_fatal('重登网页失败')
                self.browser.screen_shot()
                self.login_status = False
                if raise_enable:
                    self.browser_close_and_quit()
                    sleep(2)
                    raise RuntimeError
                else:
                    return False

            self.browser.web_refresh(force=True)

            for i in range(2):
                if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath']):
                    self.write_config(self.ele_info['login_username_xpath'], self.web_admin_username)
                    self.write_config(self.ele_info['login_password_xpath'], self.web_admin_pwd)
                    self.browser.click_btn_by_class_name(self.ele_info['login_btn_class'])
                    sleep(1)
                    self.screen_shot()
                if i == 0 and modify_default_pwd:
                    self.modify_default_login_password()
                    continue

            # 判断是否登录成功
            if self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_logout_class']) or \
                    self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_status_class']):
                aklog_info(self.device_name_log + '重登网页成功')
                self.login_status = True
                return True
            elif j < 2:
                sleep(10)
                continue
            else:
                aklog_fatal(self.device_name_log + '重登网页失败')
                self.browser.screen_shot()
                self.login_status = False
                if raise_enable:
                    self.browser_close_and_quit()
                    sleep(2)
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

    def judge_in_modify_default_pwd_page(self):
        return self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['change_pwd_window_title_xpath'])

    def reset_login_password_and_ignore(self):
        aklog_info(self.device_name_log + 'reset_login_password_and_ignore')
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['change_pwd_window_title_xpath']):
            self.browser.click_btn_by_xpath(self.ele_info['change_pwd_window_cancel_btn_xpath'])

    def close_modify_default_pwd_page(self):
        """点击右上角关闭修改默认密码窗口"""
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['change_pwd_window_title_xpath']):
            self.browser.click_btn_by_xpath(self.ele_info['change_pwd_window_close_btn_xpath'])

    def modify_default_login_password(self):
        aklog_info(self.device_name_log + 'modify_default_login_password')
        new_pwd = 'Aa12345678'
        if new_pwd == self.web_admin_pwd:
            new_pwd = 'Ak12345678'
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['change_pwd_window_title_xpath']):
            self.write_config(self.ele_info['change_pwd_window_new_pwd_xpath'], new_pwd)
            sleep(2)
            self.write_config(self.ele_info['change_pwd_window_confirm_pwd_xpath'], new_pwd)
            self.browser.click_btn_by_xpath(self.ele_info['change_pwd_window_change_btn_xpath'])
            # self.browser.alert_confirm_accept()
            sleep(2)
            self.browser.web_refresh()
            self.web_admin_pwd = new_pwd
        else:
            aklog_info(self.device_name_log + 'No change to default password pops up')

    def modify_default_pwd(self, new_pwd, confirm_pwd):
        """重新封装，用于测试修改密码界面"""
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['change_pwd_window_title_xpath']):
            self.write_config(self.ele_info['change_pwd_window_new_pwd_xpath'], new_pwd)
            sleep(2)
            if self.browser.is_exist_and_visible_ele_by_xpath(
                    self.ele_info['change_pwd_window_new_pwd_fmt_tips1_xpath']):
                aklog_info(self.device_name_log + '密码不符合要求')
                return 'The password must'

            if not self.browser.get_ele_status_by_xpath(self.ele_info['change_pwd_window_confirm_pwd_xpath']):
                aklog_info(self.device_name_log + '确认密码不可填写')
                return 'confirm pwd edit is disabled'

            self.write_config(self.ele_info['change_pwd_window_confirm_pwd_xpath'], confirm_pwd)
            if self.browser.is_exist_and_visible_ele_by_xpath(
                    self.ele_info['change_pwd_window_confirm_pwd_tips_xpath']):
                aklog_error(self.device_name_log + '确认密码不一致')
                return 'The entered passwords do not match !'

            if not self.browser.get_ele_status_by_xpath(self.ele_info['change_pwd_window_change_btn_xpath']):
                aklog_info(self.device_name_log + 'change按钮不可点击')
                return 'change btn is disabled'
            else:
                self.browser.click_btn_by_xpath(self.ele_info['change_pwd_window_change_btn_xpath'])
                self.browser.alert_confirm_accept()
                self.web_admin_pwd = new_pwd
                self.web_logout()
                self.user_login(self.web_admin_username, self.web_admin_pwd)
                return not self.judge_in_login_page()
        else:
            aklog_info(self.device_name_log + '没有弹出修改默认密码界面')
            return False

    def web_logout(self):
        aklog_info(self.device_name_log + 'web_logout')
        if self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_logout_class']):
            self.browser.click_btn_by_class_name(self.ele_info['home_logout_class'])
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath']):
            aklog_info(self.device_name_log + '网页已登出')
            return True
        else:
            aklog_error(self.device_name_log + '网页登出失败')
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

    # <editor-fold desc="HomePage相关">
    def is_homepage(self):
        aklog_info(self.device_name_log + 'is_homepage')
        self.browser.web_refresh()
        return self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_status_class'], 0.5)

    def enter_homepage(self):
        aklog_info(self.device_name_log + 'enter_homepage')
        self.browser.switch_iframe_to_default()
        for i in range(3):
            if self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_status_class'], 0.5):
                aklog_info(self.device_name_log + 'enter homepage success')
                return True
            elif not self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_logout_class'], 0.5):
                self.retry_login()
                continue
            elif i == 2:
                aklog_error(self.device_name_log + 'enter homepage failed')
                break
            else:
                self.browser.click_btn_by_xpath(self.ele_info['menu_homepage_xpath'])
                continue
        return False

    def set_web_language_to_english(self):
        return self.set_web_language_on_homepage('English')

    def get_model_from_homepage(self, regain=True):
        if not self.model or regain:
            self.enter_homepage()
            self.model = self.browser.get_value_by_xpath(self.ele_info['home_status_model_xpath'])
        return self.model

    def get_firmware_version_from_homepage(self, regain=True):
        if not self.firmware_version or regain:
            self.enter_homepage()
            self.firmware_version = self.browser.get_value_by_xpath(self.ele_info['home_status_firmware_version_xpath'])
        return self.firmware_version

    # 设置网页语言
    def set_web_language(self, web_language):
        return self.set_web_language_on_homepage(web_language)

    def set_web_language_on_homepage(self, web_language):
        aklog_info()
        self.enter_homepage()
        for i in range(2):
            if self.read_config(self.ele_info['home_lang_box_xpath']) == web_language:
                if i == 0:
                    aklog_info('当前语言已经是 %s' % web_language)
                else:
                    aklog_info('切换语言为 %s 成功' % web_language)
                return True
            elif i == 0:
                self.write_config(self.ele_info['home_lang_box_xpath'], web_language)
                sleep(2)
                self.browser.web_refresh()
                sleep(1)
                continue
            else:
                aklog_error('切换语言为 %s 失败' % web_language)
                return False

    def set_web_language_on_top(self, web_language):
        """需要先进入有菜单界面"""
        aklog_info()
        for i in range(2):
            if self.read_config(self.ele_info['top_language_combobox_xpath']) == web_language:
                if i == 0:
                    aklog_info('当前语言已经是 %s' % web_language)
                else:
                    aklog_info('切换语言为 %s 成功' % web_language)
                return True
            elif i == 0:
                self.write_config(self.ele_info['top_language_combobox_xpath'], web_language)
                sleep(2)
                self.browser.web_refresh()
                sleep(1)
                continue
            else:
                aklog_error('切换语言为 %s 失败' % web_language)
                return False

    def get_web_language_on_top(self):
        return self.read_config(self.ele_info['top_language_combobox_xpath'])

    def get_web_language_list(self):
        return self.get_select_options_list_by_xpath(self.ele_info['top_language_combobox_xpath'])

    def get_home_status_title(self):
        self.enter_homepage()
        self.web_refresh()
        return self.browser.get_value_by_xpath(self.ele_info['home_status_title_xpath'])

    # 获取网页当前语言
    def check_web_language(self):
        aklog_info()
        self.enter_homepage()
        return self.read_config(self.ele_info['home_logout_xpath'])

    def get_menu_xpath_info(self, regain=False):
        aklog_debug()
        if regain:
            self.menu_xpath_info = dict()
            self.page_menu_info.clear()
        self.enter_menu_list_from_homepage()
        self.set_web_language_on_top('English')
        for j in range(2):
            if not self.menu_xpath_info:
                counts = self.browser.get_ele_counts_by_xpath(self.ele_info['menu_counts_xpath'])
                if not counts:
                    counts = self.browser.get_ele_counts_by_xpath('//*[@class="ak-left-menu-div"]/ul/li')
                if counts:
                    for i in range(1, counts + 1):
                        ele_xpath = '%s[%s]/div/span/span' % (self.ele_info['menu_counts_xpath'], i)
                        text = self.browser.get_value_by_xpath(ele_xpath)
                        if text:
                            self.menu_xpath_info[text] = '%s[%s]' % (self.ele_info['menu_counts_xpath'], i)
                else:
                    aklog_error('获取菜单列表异常')
                    self.screen_shot()
                    continue
            else:
                break
        aklog_debug(self.device_name_log + 'menu_dict: %r' % self.menu_xpath_info)
        if self.menu_xpath_info:
            return True
        else:
            return False

    def enter_menu_list_from_homepage(self):
        """从主页进入到有菜单列表的页面"""
        for i in range(2):
            if self.is_homepage():
                if not self.browser.click_btn_by_id(self.ele_info['home_network_id']):
                    self.browser.click_btn_by_id(self.ele_info['home_system_id'])
            if self.browser.is_exist_and_visible_ele_by_class_name('ak-top'):
                aklog_info('已进入有左侧菜单列表的页面')
                return True
            elif i == 0:
                aklog_info('未登录')
                self.screen_shot()
                self.retry_login()
                continue
            else:
                aklog_error('进入失败，请检查')
                self.screen_shot()
                return False

    # </editor-fold>

    # <editor-fold desc="Status页面相关">
    def enter_status_basic(self):
        aklog_info(self.device_name_log + 'enter_status_basic')
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_network_id'])

        if 'status_basic' in self.page_menu_info:
            if self.menu_expand_and_click(self.page_menu_info['status_basic'][0],
                                          self.page_menu_info['status_basic'][1], False):
                return True

        if not self.menu_expand_and_click(self.menu_xpath_info.get('Status'),
                                          self.ele_info['menu_status_basic_xpath'], False):
            aklog_info('不同版本目录有改动，重新进入')
            self.menu_expand_and_click(self.menu_xpath_info['Status'], None, False)
            self.page_menu_info['status_basic'] = [self.menu_xpath_info['Status'], None]

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

    def get_status_product_info(self):
        self.enter_status_basic()
        model = self.get_text_by_label_name('Model')
        mac_address = self.browser.get_value_by_xpath(self.ele_info['status_mac_address'])
        firmware_version = self.browser.get_value_by_xpath(self.ele_info['status_firmware_version'])
        hardware_version = self.browser.get_value_by_xpath(self.ele_info['status_hardware_version'])
        location = self.browser.get_value_by_xpath(self.ele_info['status_location'])
        room_number = self.browser.get_value_by_xpath(self.ele_info['status_room_number'])
        product_info = {'model': model,
                        'mac_address': mac_address,
                        'firmware_version': firmware_version,
                        'hardware_version': hardware_version,
                        'location': location,
                        'room_number': room_number}
        return product_info

    def get_status_network_info(self):
        self.enter_status_basic()
        network_type = self.get_text_by_label_name('Network Type')
        lan_port_type = self.browser.get_value_by_xpath(self.ele_info['status_lan_port_type'])
        link_status = self.browser.get_value_by_xpath(self.ele_info['status_link_status'])
        ip_address = self.browser.get_value_by_xpath(self.ele_info['status_ip_address'])
        subnet_mask = self.browser.get_value_by_xpath(self.ele_info['status_subnet_mask'])
        gateway = self.browser.get_value_by_xpath(self.ele_info['status_gateway'])
        dns1 = self.browser.get_value_by_xpath(self.ele_info['status_dns1'])
        dns2 = self.browser.get_value_by_xpath(self.ele_info['status_dns2'])
        ntp1 = self.browser.get_value_by_xpath(self.ele_info['status_ntp1'])
        ntp2 = self.browser.get_value_by_xpath(self.ele_info['status_ntp2'])
        network_info = {'network_type': network_type,
                        'lan_port_type': lan_port_type,
                        'link_status': link_status,
                        'ip_address': ip_address,
                        'subnet_mask': subnet_mask,
                        'gateway': gateway,
                        'dns1': dns1,
                        'dns2': dns2,
                        'ntp1': ntp1,
                        'ntp2': ntp2}
        return network_info

    def get_status_account_info(self):
        self.enter_status_basic()
        account1_username = self.browser.get_value_by_xpath(self.ele_info['status_account1_username'])
        account1_status = self.browser.get_value_by_xpath(self.ele_info['status_account1_status'])
        account2_username = self.browser.get_value_by_xpath(self.ele_info['status_account2_username'])
        account2_status = self.browser.get_value_by_xpath(self.ele_info['status_account2_status'])
        account_info = {'account1_username': account1_username,
                        'account1_status': account1_status,
                        'account2_username': account2_username,
                        'account2_status': account2_status}
        return account_info

    def get_status_account1_info(self):
        self.enter_status_basic()
        # account1_username = self.browser.get_value_by_xpath(self.ele_info['status_account1_username'])
        account1_status = self.browser.get_value_by_xpath(self.ele_info['status_account1_status'])
        # account2_username = self.browser.get_value_by_xpath(self.ele_info['status_account2_username'])
        # account2_status = self.browser.get_value_by_xpath(self.ele_info['status_account2_status'])
        account_info = {'account1_status': account1_status
                        }
        return account_info

    # </editor-fold>

    # <editor-fold desc="Account Basic相关">
    def enter_web_account_basic(self):
        aklog_info(self.device_name_log + 'enter_web_account_basic')
        # self.enter_menu_list_from_homepage()
        # self.menu_expand_and_click(self.menu_xpath_info['Account'], None)
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_account_id'])
        self.menu_expand_and_click(self.menu_xpath_info['Account'], self.ele_info['menu_account_basic_xpath'])

    def click_account(self):
        # 点击Account
        self.browser.click_btn_by_id('tMenu20')
        sleep(2)

    def click_account_basic(self):
        # 点击Account Basic
        self.menu_expand_and_click('tMenu20', 'tMenu21')

    def account_select(self, account='1'):
        account = 'Account' + str(account)
        self.write_config(self.ele_info['account_select_xpath'], account)
        sleep(1)

    def get_account_label_value(self):
        """获取Account的label值"""
        aklog_info(self.device_name_log + '获取Account的label值')
        value = self.browser.get_attribute_value_by_xpath(self.ele_info['account_display_label_xpath'])
        return value

    def get_account_status_value(self):
        # 获取AccountStatus的值
        for i in range(3):
            # 进入页面后刚开始有可能会获取不到状态，需要等待重试
            account_status = self.browser.get_value_by_xpath(self.ele_info['account_status_xpath'])
            if account_status == '':
                sleep(2)
                continue
            else:
                return account_status

    def get_account_sip_server_addr(self):
        """获取SIP服务器地址"""
        value = self.browser.get_attribute_value_by_xpath('//*[@id="cFirstSIPServerAddr"]')
        return value

    def get_account_username_value(self):
        aklog_info(self.device_name_log + 'get_account_username_value')
        self.enter_web_account_basic()
        self.browser.web_refresh()
        user_name = self.read_config(self.ele_info['account_user_name_xpath'])
        return user_name

    def web_enable_account_register(self, index=1):
        aklog_info()
        self.enter_web_account_basic()
        self.write_config(self.ele_info['account_select_xpath'], 'Account{}'.format(index))
        sleep(1)
        self.write_config(self.ele_info['account_enabled_xpath'], True)
        self.click_submit()

    def web_disable_account_register(self, index=1):
        aklog_info()
        self.enter_web_account_basic()
        self.write_config(self.ele_info['account_select_xpath'], 'Account{}'.format(index))
        sleep(1)
        self.write_config(self.ele_info['account_enabled_xpath'], False)
        self.click_submit()

    def register_sip(self, sip, sip_password, server_ip, server_port='5060', account_active=1, index=1,
                     transport='UDP', wait_register=True, **kwargs):
        """
        话机注册sip号功能
        index: 注册帐号1或账号2，'1'、'2'
        account_active: 1 or 0
        kwargs: display_name=xxx, register_name=xxx, label=xxx
        """
        aklog_info()

        label = kwargs.get('label') if kwargs.get('label') is not None else sip
        display_name = kwargs.get('display_name') if kwargs.get('display_name') is not None else sip
        register_name = kwargs.get('register_name') if kwargs.get('register_name') is not None else sip

        self.enter_web_account_basic()
        sleep(0.5)
        account = 'Account' + str(index)
        self.write_config(self.ele_info['account_select_xpath'], account)
        sleep(1)
        self.write_config(self.ele_info['account_enabled_xpath'], account_active)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_display_label_xpath']), label)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_display_name_xpath']), display_name)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_register_name_xpath']), register_name)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_user_name_xpath']), sip)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_pwd_xpath']), sip_password)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_sip_server_xpath']), server_ip)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_sip_port_xpath']), server_port)
        if transport:
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_trans_type']), transport)
        self.click_submit(accept=False)
        ret = self.get_submit_result(wait_time=4)
        if ret is True:
            if str(account_active) == '1' and wait_register:
                return self.wait_for_account_to_register_successfully(account=str(index))
        else:
            return ret

    def register_sip_with_device_info(self, account='1', **kwargs):
        """
        使用device info中的SIP帐号注册
        注意，device_info中的key值需要跟下面的一致
        account: 1 2 12
        kwargs: 比如：transport=TCP, display_name=xxx
        """
        aklog_info()
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
        self.account_select(account)
        sleep(2)
        self.write_config(self.ele_info['account_trans_type'], transport_type)
        self.click_submit()

    def unregister_sip_account(self, accounts='1', all=False):
        """
        网页注销帐号
        :param accounts: 帐号1或账号2，'1'、'2'、'12'
        """
        aklog_info(self.device_name_log + 'unregister_sip_account')
        self.enter_web_account_basic()
        if type(accounts) == bool and accounts:
            for x in ['2', '1']:
                account = 'Account' + x
                self.write_config(self.ele_info['account_select_xpath'], account)
                self.disabled_account()
                self.click_submit()
        else:
            if all == True:
                for x in ['2', '1']:
                    account = 'Account' + x
                    self.write_config(self.ele_info['account_select_xpath'], account)
                    self.disabled_account()
                    self.click_submit()
            else:
                for x in accounts:
                    account = 'Account' + x
                    self.write_config(self.ele_info['account_select_xpath'], account)
                    self.disabled_account()
                    self.click_submit()

    def clear_web_account(self, accounts='1'):
        """
        网页清除账号配置为默认配置
        :param accounts: '1', '2', '12'
        :return:
        """
        aklog_info(self.device_name_log + 'clear_web_account')
        self.enter_web_account_basic()
        for x in str(accounts):
            account = 'Account' + x
            self.write_config(self.ele_info['account_select_xpath'], account)
            sleep(1)
            self.write_config(self.ele_info['account_enabled_xpath'], 0)
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_display_label_xpath']), '')
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_display_name_xpath']), '')
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_register_name_xpath']), '')
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_user_name_xpath']), '')
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_pwd_xpath']), '')
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_sip_server_xpath']), '')
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_sip_port_xpath']), '5060')
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_trans_type']), 'UDP')
            try:
                # 尽可能关闭outbound, nat的影响.
                eles = self.browser.get_elements_by_xpath('.//input[@type="checkbox"]')
                for ele in eles:
                    if ele.is_selected():
                        ele.click()
            except:
                pass
            self.click_submit()

    def disabled_account(self):
        self.browser.uncheck_box_by_xpath(self.ele_info['account_enabled_xpath'])

    def enabled_account(self):
        self.browser.check_box_by_xpath(self.ele_info['account_enabled_xpath'])

    def wait_for_account_to_register_successfully(self, failure_to_wait_time=15, account='1'):
        aklog_info(self.device_name_log + 'wait_for_account_to_register_successfully')
        self.enter_web_account_basic()
        self.browser.web_refresh()
        self.account_select(account)
        i = 0
        while i < 30 + int(failure_to_wait_time / 5):
            account_status = self.get_account_status_value()
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
                sleep(4)
                i += 1
                continue
        aklog_error(self.device_name_log + 'sip account register failed')
        return False

    # def get_account_trans_type(self):
    #     return self.browser.get_value_by_xpath(self.ele_info['account_trans_type'])

    def judge_cloudconnect_status(self):
        """判断设备连接云的状态"""
        self.browser.web_refresh()
        self.enter_web_account_basic()
        status = self.get_account_status_value()
        return status

    def get_account_trans_type(self):
        """获取SIP传输类型"""
        aklog_info(self.device_name_log + 'get_account_trans_type')
        self.browser.web_refresh()
        self.enter_web_account_basic()
        trans_type = self.browser.get_value_by_xpath(self.ele_info['account_trans_type'])
        return trans_type

    def get_account_register_status(self, account=None):
        aklog_info(self.device_name_log + 'get_account_register_status')
        self.enter_web_account_basic()
        if account is not None:
            account = 'Account' + account
            self.write_config(self.ele_info['account_select_xpath'], account)
            sleep(1)
        register_status = self.get_account_status_value()
        return register_status

    def set_outbound_server(self, status, server1, server1_port, server2=None, server2_port=None, index=1):
        """网页设置outbound主次服务器地址"""
        self.enter_web_account_basic()
        account = 'Account' + str(index)
        self.write_config(self.ele_info['account_select_xpath'], account)
        sleep(1)
        self.write_config(self.ele_info['account_outbound_enable'], status)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_outbound_server']), server1)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_outbound_server_port']), server1_port)
        if server2 is not None:
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_outbound_backup_server']), server2)
        if server2_port is not None:
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_outbound_backup_server_port']),
                              server2_port)
        self.click_submit()

    def clear_outbound_server(self, accounts='1'):
        """
        清空outbound配置
        :param accounts: '1', '2', '12'
        :return:
        """
        self.enter_web_account_basic()
        for index in accounts:
            account = 'Account' + str(index)
            self.write_config(self.ele_info['account_select_xpath'], account)
            sleep(1)
            self.write_config(self.ele_info['account_outbound_enable'], 0)
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_outbound_server']), '')
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_outbound_server_port']), '5060')
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_outbound_backup_server']), '')
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_outbound_backup_server_port']),
                              '5060')
            self.click_submit()

    # </editor-fold>

    # <editor-fold desc="Account Advanced相关">
    def enter_account_advanced(self):
        aklog_info(self.device_name_log + 'enter_account_advanced')
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_account_id'])
        self.menu_expand_and_click(self.menu_xpath_info['Account'], self.ele_info['menu_account_advanced_xpath'])

    def set_cur_account_advanced(self, index=None):
        """设置当前配置账号，账号1或账号2"""
        aklog_info('set_cur_account_advanced')
        self.enter_account_advanced()
        if index:
            self.write_config(self.ele_info['current_account_xpath'], 'Account' + str(index))
        self.click_submit()

    def set_account_auto_answer(self, enable=1, account='1'):
        # 网页账号高级开启自动应答
        self.enter_account_advanced()
        self.account_select(account)
        self.write_config(self.ele_info['account_advanced_auto_answer_xpath'], enable)
        self.click_submit()

    def enable_auto_answer(self):
        # 网页账号高级开启自动应答
        self.enter_account_advanced()
        self.write_config(self.ele_info['account_advanced_auto_answer_xpath'], 1)
        self.click_submit()

    def disable_auto_answer(self):
        # 网页账号高级关闭自动应答
        self.enter_account_advanced()
        self.write_config(self.ele_info['account_advanced_auto_answer_xpath'], 0)
        self.click_submit()

    def enable_sip_hacking(self, index=1):
        # 网页账号高级开启SIP HACKING
        self.enter_account_advanced()
        self.account_select(str(index))
        self.write_config(self.ele_info['account_advanced_sip_hacking_xpath'], 1)
        self.click_submit()

    def disable_sip_hacking(self, index=1):
        # 网页账号高级关闭SIP HACKING
        self.enter_account_advanced()
        self.account_select(str(index))
        self.write_config(self.ele_info['account_advanced_sip_hacking_xpath'], 0)
        self.click_submit()

    def get_h264_codec_bit_rate(self):
        """获取h264码率"""
        self.enter_account_advanced()
        return self.get_selected_option_by_xpath(self.ele_info['account1_advanced_ritrate_xpath'])

    def set_audio_codecs(self, codecs, is_sort=False):
        """设置audio codecs"""
        self.enter_account_advanced()
        self.set_multi_selects_enable(codecs, 'Audio Codecs')
        if is_sort:
            self.move_multi_selects_sort(codecs, 'Audio Codecs')
        self.click_submit(accept=False)
        alert_text = self.web_get_alert_text_and_confirm()
        if alert_text:
            return alert_text
        else:
            return self.get_submit_result()

    def set_audio_codecs_sort(self, codec_list: list):
        """设置audio codecs顺序"""
        self.enter_account_advanced()
        self.move_multi_selects_sort(codec_list, 'Audio Codecs')
        self.click_submit()

    def get_enabled_audio_codec_list(self):
        self.enter_account_advanced()
        return self.get_multi_selected_options('Audio Codecs')

    def get_disabled_audio_codec_list(self):
        """封装获取disabled codec列表"""
        self.enter_account_advanced()
        return self.get_multi_unselected_options('Audio Codecs')

    def set_video_codecs(self, codecs, is_sort=False):
        """设置video codecs"""
        self.enter_account_advanced()
        self.set_multi_selects_enable(codecs, 'Video Codecs')
        if is_sort:  # 是否进行排序
            self.move_multi_selects_sort(codecs, 'Video Codecs')
        self.click_submit(accept=False)
        alert_text = self.web_get_alert_text_and_confirm()
        if alert_text:
            return alert_text
        else:
            return self.get_submit_result()

    def set_video_codecs_sort(self, codec_list: list):
        """设置video codecs顺序"""
        self.enter_account_advanced()
        self.move_multi_selects_sort(codec_list, 'Video Codecs')
        self.click_submit()

    def get_enabled_video_codec_list(self):
        self.enter_account_advanced()
        return self.get_multi_selected_options('Video Codecs')

    def enable_audio_codec(self, codeclist: list):
        """设置enabled codec里包含的code"""
        self.set_audio_codecs(codeclist)
        # self.enter_account_advanced()
        # # 先将已选择的codecs移到未选择
        # self.browser.click_multi_elements_by_xpath(self.ele_info['account_advanced_enabled_codecs_xpath'])
        # sleep(0.5)
        # self.browser.click_btn_by_xpath(self.ele_info['account_advanced_disable_codec_xpath'])
        # # 然后再根据codec名称选择
        # for codec in codeclist:
        #     self.browser.click_btn_by_xpath('//*[@title="%s"]' % codec)
        # sleep(0.5)
        # self.browser.click_btn_by_xpath(self.ele_info['account_advanced_enable_codec_xpath'])
        # self.click_submit()

    def enable_all_audio_codec(self):
        """封装开启所有的音频codec"""
        self.set_audio_codecs('all')
        # self.enter_account_advanced()
        # self.browser.click_multi_elements_by_xpath(self.ele_info['account_advanced_disabled_codecs_xpath'])
        # sleep(0.5)
        # self.browser.click_btn_by_xpath(self.ele_info['account_advanced_enable_codec_xpath'])
        # self.click_submit()

    def enable_all_video_codec(self):
        self.set_video_codecs('all')

    def move_audio_code_top(self, codec):
        """移动指定的codec的优先级为最高"""
        self.move_multi_selects_sort([codec], 'Audio Codecs')

    def set_account_dtmf(self, dtmf_mode, info_type=None, payload=None, account='1'):
        """设置账号dtmf"""
        aklog_info('set_account_dtmf: dtmf_mode: %s, info_type: %s, payload: %s' % (dtmf_mode, info_type, payload))
        self.enter_account_advanced()
        self.account_select(account)
        account = 'Account' + str(account)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_dtmf_type_xpath']), dtmf_mode)
        if info_type is not None:
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_dtmf_info_type_xpath']), info_type)
        if payload is not None:
            self.write_config(re.sub(r'Account\d', account, self.ele_info['account_dtmf_payload_edit_xpath']), payload)
        self.click_submit()

    def set_local_sip_port(self, min_sip_port, max_sip_port, account='1', accept=True):
        """设置本地sip端口"""
        aklog_info('set_local_sip_port')
        self.enter_account_advanced()
        self.account_select(account)
        account = 'Account' + str(account)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['max_local_sip_port_xpath']), max_sip_port)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['min_local_sip_port_xpath']), min_sip_port)
        self.click_submit(accept)

    def get_local_sip_port(self, account='1'):
        """获取本地sip端口"""
        aklog_info('get_local_sip_port')
        self.enter_account_advanced()
        self.account_select(account)
        account = 'Account' + str(account)
        return self.read_config(re.sub(r'Account\d', account, self.ele_info['max_local_sip_port_xpath']))

    def set_voice_encryption(self, encryption_type, account='1'):
        """设置语音加密类型"""
        aklog_info('set_voice_encryption(SRTP): %s' % encryption_type)
        self.enter_account_advanced()
        self.account_select(account)
        account = 'Account' + str(account)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['voice_encryption_srtp_xpath']), encryption_type)
        self.click_submit()

    def get_rport_enabled(self, account='1'):
        self.enter_account_advanced()
        self.account_select(account)
        return self.read_config(self.ele_info['account_rport_enabled'])

    def set_rport_enabled(self, enable=True, account='1'):
        """网页设置rport"""
        self.enter_account_advanced()
        self.account_select(account)
        self.write_config(self.ele_info['account_rport_enabled'], enable)
        self.click_submit()

    def get_user_agent(self, account='1'):
        """account: 1 or 2"""
        self.enter_account_advanced()
        self.account_select(account)
        account = 'Account' + str(account)
        return self.read_config(re.sub(r'Account\d', account, self.ele_info['account_user_agent']))

    def set_user_agent(self, agent, account='1'):
        """设置user agent, account: 1 or 2"""
        self.enter_account_advanced()
        self.account_select(account)
        account = 'Account' + str(account)
        self.write_config(re.sub(r'Account\d', account, self.ele_info['account_user_agent']), agent)
        self.click_submit()

    def get_default_user_agent(self):
        """通过status页面的型号, 版本, 组合出默认user-agent"""
        self.enter_homepage()
        model = self.read_config(self.ele_info['home_status_model_xpath'])
        rom = self.read_config(self.ele_info['home_status_firmware_version_xpath'])
        mac = self.read_config(self.ele_info['home_status_mac_xpath'])
        # 'Akuvox R20K 220.30.2.104 A81102210414'
        return 'Akuvox ' + model + ' ' + rom + ' ' + mac

    # </editor-fold>

    # <editor-fold desc="Deivce - Time/Lang页面">
    def enter_web_phone_time_page(self):
        aklog_info('enter_web_phone_time_page')
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_phone_id'])
        # self.menu_expand_and_click(self.menu_xpath_info['Device'], self.ele_info['menu_phone_time_xpath'])
        self.menu_expand_and_click(self.menu_xpath_info['Device'], '//a[contains(@href, "Time")]')

    def get_selected_time_format(self):
        """
        获取选择的时间格式
        :return: 12/24
        """
        aklog_info(self.device_name_log + 'get_selected_time_format')
        self.enter_web_phone_time_page()
        self.browser.web_refresh()
        time_format = self.browser.get_value_by_xpath(self.ele_info['phone_time_format_xpath'])
        if time_format:
            time_format = re.sub(r'\D', '', time_format)  # 正则表达式去除非数字字符串
        return time_format

    def get_selected_date_format(self, trans_fmt=True):
        """获取当前选择的日期格式，返回Y-M-D，M-D-Y，D-M-Y"""
        aklog_info(self.device_name_log + 'get_selected_date_format')
        self.enter_web_phone_time_page()
        self.browser.web_refresh()
        date_format = self.browser.get_value_by_xpath(self.ele_info['phone_date_format_xpath'])
        if trans_fmt:
            if 'YYYY' in date_format:
                date_format = date_format.replace('YYYY', 'Y').replace('MM', 'M').replace('DD', 'D').replace('/', '-')
            else:
                date_format = get_current_date_format(date_format)
        return date_format

    def set_time_params(self, auto_time=None, time_fmt=None, date_fmt=None, date_str=None, time_str=None,
                        time_zone=None, ntp_server=None, ntp_server2=None):
        """
        网页设置时间日期
        auto_time: 0 or 1
        date_str: 跟date_fmt格式要一致
        date_fmt: YYYY-MM-DD,DD-MM-YYYY
        time_fmt: 12 or 24
        time_str: 跟time_fmt格式要一致
        time_zone: GMT+8:00 Asia/Shanghai
        """
        aklog_info()
        self.enter_web_phone_time_page()
        if str(auto_time) == '1':
            self.write_config(self.ele_info['device_time_auto_time'], 1)
        elif str(auto_time) == '0':
            self.write_config(self.ele_info['device_time_auto_time'], 0)
            sleep(1)
            if date_str:
                self.write_config(self.ele_info['phone_date_format_xpath'], date_fmt)
                self.input_date_by_xpath(self.ele_info['device_time_manual_date_pick'], date_str)
            if time_str:
                self.write_config(self.ele_info['phone_time_format_xpath'], '%s-Hour Format' % time_fmt)
                self.input_time_by_xpath(self.ele_info['device_time_manual_time_pick'], time_str)
        if time_fmt and not time_str:
            self.write_config(self.ele_info['phone_time_format_xpath'], '%s-Hour Format' % time_fmt)
        if date_fmt and not date_str:
            self.write_config(self.ele_info['phone_date_format_xpath'], date_fmt)
        if time_zone:
            self.write_config(self.ele_info['device_time_time_zone'], time_zone)
        if ntp_server is not None:
            self.write_config(self.ele_info['device_time_ntp_server'], ntp_server)
        if ntp_server2 is not None:
            self.write_config(self.ele_info['device_time_ntp_server2'], ntp_server2)
        self.click_submit()
        if self.browser.is_exist_ele_by_xpath('//*[@class="ant-modal-confirm-body-wrapper"]'):
            self.browser.click_btn_by_xpath('//*[@class="ant-modal-confirm-body-wrapper"]//button[2]')
            # 网页服务重新启动，等待一下
            sleep(10)

    # </editor-fold>

    # <editor-fold desc="Device - Call Feature页面">

    def enter_web_phone_call_feature(self):
        aklog_info('enter_web_phone_call_feature')
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_phone_id'])
        # self.menu_expand_and_click(self.menu_xpath_info['Device'], self.ele_info['menu_phone_call_feature_xpath'])
        self.menu_expand_and_click(self.menu_xpath_info['Device'], '//a[contains(@href, "CallFeature")]')

    def set_indoor_auto_answer(self, enable='1'):
        """设置室内机自动应答"""
        self.enter_web_phone_call_feature()
        self.write_config(self.ele_info['indoor_auto_answer_xpath'], enable)
        self.click_submit()
        sleep(3)

    def get_current_return_code(self):
        """获取当前return code"""
        self.enter_web_phone_call_feature()
        return self.read_config(self.ele_info['call_feature_refuse_return_code'])

    def set_return_code_refuse(self, return_code):
        """
        设置Return Code
        :param return_code: 486 480 404 603
        :return:
        """
        return_code_info = {'486': '486(Busy Here)',
                            '480': '480(Temporarily Unavailable)',
                            '404': '404(Not Found)',
                            '603': '603(Decline)'}
        self.enter_web_phone_call_feature()
        self.write_config(self.ele_info['call_feature_refuse_return_code'], return_code_info[return_code])
        self.click_submit()

    def get_answer_tone(self):
        """获取answer tone状态"""
        return self.read_config('//*[@id="Config.Settings.AUDIO.AnswerTone"]/div[1]/div')

    def set_answer_tone(self, enable=1):
        """设置Answer Tone"""
        self.enter_web_phone_call_feature()
        self.write_config('//*[@id="Config.Settings.AUDIO.AnswerTone"]/div[1]/div', int(enable))
        self.click_submit()

    def set_auto_answer_delay(self, delay):
        """设置自动应答延迟"""
        self.enter_web_phone_call_feature()
        self.write_config(self.ele_info['call_feature_auto_answer_delay'], delay)
        self.click_submit()

    # </editor-fold>

    # <editor-fold desc="Device - Display Setting页面">
    def enter_device_display_setting(self):
        aklog_info('enter_device_display_setting')
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_phone_id'])
        # self.menu_expand_and_click(self.menu_xpath_info['Device'], self.ele_info['menu_phone_display_setting_xpath'])
        self.menu_expand_and_click(self.menu_xpath_info['Device'], '//a[contains(@href, "Display")]')

    # </editor-fold>

    # <editor-fold desc="Device - multicast页面">

    def enter_web_phone_multicast(self):
        aklog_info()
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_phone_id'])
        # self.menu_expand_and_click(self.menu_xpath_info['Device'],
        #                            self.ele_info['menu_phone_multicast_xpath'])
        self.menu_expand_and_click(self.menu_xpath_info['Device'],
                                   '//a[contains(@href, "Mul") and contains(@href, "cast")]')

    def set_multicast_group(self, group):
        """
        设置Multicast Group，如果要启用，需要先填写multicast list
        :param group: 0 - 3, 0表示全部禁用
        :return:
        """
        self.enter_web_phone_multicast()
        if int(group) in [1, 2, 3]:
            self.write_config(
                '//label[normalize-space(text())="Multicast List"]/../..//tbody/tr[%s]/td[3]//input' % group, 1)
        else:
            # 禁用所有Multicast Group
            for i in range(1, 4):
                self.write_config(
                    '//label[normalize-space(text())="Multicast List"]/../..//tbody/tr[%s]/td[3]//input' % group, 0)
        self.click_submit()

    def set_multicast_list(self, *multicast_list):
        """
        设置Multicast List地址
        :param multicast_list:传入参数为元组类型，比如：('224.1.6.11:51230', 1)，如果传入的不是元组类型，则Enabled不勾选
        注意三个群组，只能启用一个，如果启用多个，则最终只启用最后一个
        """
        self.enter_web_phone_multicast()
        group = 1
        for multicast_info in multicast_list:
            if isinstance(multicast_info, tuple):
                address = multicast_info[0]
                enable = multicast_info[1]
            else:
                address = multicast_info
                enable = 0
            self.write_config(
                '//label[normalize-space(text())="Multicast List"]/../..//tbody/tr[%s]/td[2]//input' % group, address)
            self.write_config(
                '//label[normalize-space(text())="Multicast List"]/../..//tbody/tr[%s]/td[3]//input' % group, enable)
            group += 1
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
            self.write_config('//label[normalize-space(text())="Listen List"]/../..//tbody/tr[%s]/td[2]//input' % group,
                              address)
            if label:
                self.write_config(
                    '//label[normalize-space(text())="Listen List"]/../..//tbody/tr[%s]/td[3]//input' % group, label)
            group += 1
        self.click_submit()

    # </editor-fold>

    # <editor-fold desc="Contacts - Local Contacts页面">

    # <editor-fold desc="Contacts - Local Contacts页面 - All Contacts">

    def enter_local_book(self):
        aklog_info()
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_contacts_id'])
        else:
            self.menu_expand_and_click(self.menu_xpath_info['Contacts'],
                                       self.ele_info['menu_contacts_local_contacts_xpath'])

    def dial_out_number_on_phone_book(self, number, account=None):
        """在本地联系人页面输入号码呼出"""
        self.write_config('//div[@class="ak-dial-input"]//input[1]', number)
        if account:
            self.write_config('//div[@class="ak-dial-input"]//div[@role="combobox"]', account)
        self.browser.click_btn_by_xpath('//div[@class="ak-dial-input"]/button[1]')
        # self.browser.alert_confirm_accept()
        self.web_get_alert_text_and_confirm()
        sleep(1)
        tips = self.get_submit_tips()
        if tips == 'Dial Out Success!':
            return True
        else:
            return tips

    def hang_up_call_on_phone_book(self):
        """在本地联系人页面挂断通话"""
        self.browser.click_btn_by_xpath('//div[@class="ak-dial-input"]/button[2]')
        self.browser.alert_confirm_accept()

    def web_add_contact(self, name, number, group=None, account=None, ringtone=None):
        """网页phonebook添加联系人"""
        aklog_info()
        self.enter_local_book()
        self.browser.click_btn_by_xpath(self.ele_info['contacts_add_btn'])
        self.write_config(self.ele_info['contacts_add_name'], name)
        self.write_config(self.ele_info['contacts_add_number'], number)
        if group is not None:
            self.write_config(self.ele_info['contacts_add_group'], group)
        if account is not None:
            self.write_config(self.ele_info['contacts_add_dial_account'], account)
        if ringtone is not None:
            self.write_config(self.ele_info['contacts_add_ringtone'], ringtone)
        self.click_modal_submit()
        return self.get_submit_result(is_modal=True)

    def web_edit_contact(self, name, new_name=None, number=None, group=None, account=None, ringtone=None):
        """编辑本地联系人"""
        aklog_info()
        self.enter_local_book()
        self.click_table_edit_btn('Local Contacts List', name=name)
        if new_name is not None:
            self.write_config(self.ele_info['contacts_add_name'], new_name)
        if number is not None:
            self.write_config(self.ele_info['contacts_add_number'], number)
        if group is not None:
            self.write_config(self.ele_info['contacts_add_group'], group)
        if account is not None:
            self.write_config(self.ele_info['contacts_add_dial_account'], account)
        if ringtone is not None:
            self.write_config(self.ele_info['contacts_add_ringtone'], ringtone)
        self.click_modal_submit()
        return self.get_submit_result(is_modal=True)

    def web_clear_contact(self):
        """网页清空联系人"""
        aklog_info()
        self.enter_local_book()
        if self.browser.get_ele_status_by_xpath('//span[normalize-space(text())="Delete All"]/..'):
            self.click_btn_by_text("Delete All")
            self.browser.alert_confirm_accept()
            sleep(3)
        else:
            aklog_debug('Delete All按钮不可点击，联系人已被清空')

    def web_del_contact(self, index=1):
        aklog_info()
        self.select_contact_group('All Contacts')
        self.delete_table_by_index(index, title='Local Contacts List')

    def get_contact_counts(self):
        self.select_contact_group('All Contacts')
        return self.get_table_total_num(title='Local Contacts List')

    def select_contact_group(self, group='All Contacts'):
        aklog_info()
        if self.read_config('//*[@id="contactListSelect"]/div[1]/div') == group:
            aklog_debug('当前选择的Contact Group已是：%s' % group)
            return True
        self.write_config('//*[@id="contactListSelect"]/div[1]/div', group)
        sleep(1)

    def get_contact_info(self, attribute=None, **base_attr):
        """
        获取联系人信息
        attribute: 要获取的属性，如果为空，则获取整行信息
        base_attr: 基于哪个属性获取联系人，一般为index, name，比如：index=1, name=xxx
        """
        aklog_info()
        self.select_contact_group('All Contacts')
        return self.get_table_attribute_info(attribute=attribute, title='Local Contacts List', **base_attr)

    def click_contact_search_btn(self):
        self.browser.click_btn_by_xpath(
            '//label[normalize-space(text())="Local Contacts List"]/../..//span[normalize-space(text())="Search"]/..')

    def reset_web_contact_search(self):
        """取消搜索联系人"""
        self.browser.click_btn_by_xpath(
            '//label[normalize-space(text())="Local Contacts List"]/../..//span[normalize-space(text())="Reset"]/..')

    def web_search_contact(self, search):
        """进入网页AddressBook界面,搜索联系人"""
        self.enter_local_book()
        self.write_config(
            '//label[normalize-space(text())="Local Contacts List"]/../..//label[normalize-space(text())="Search"]/../input',
            search)
        self.click_contact_search_btn()

    def import_contacts_file(self, file_path=None, file_type='xml'):
        """
        导入xml格式contacts文件
        file_type: xml or csv
        """
        aklog_info()
        if file_path is None:
            if file_type == 'xml':
                file_path = self.device_config.get_contacts_import_xml_file_path()
            else:
                file_path = self.device_config.get_contacts_import_csv_file_path()
        return self.upload_file(
            '//label[normalize-space(text())="Local Contacts List"]/../..//span[normalize-space(text())="Import"]/..',
            file_path)

    def export_contacts_file(self, export_type='xml'):
        """网页导出联系人"""
        contacts_export_file = self.device_config.get_contacts_export_file_path()
        aklog_info()
        File_process.remove_file(contacts_export_file)
        self.enter_local_book()
        self.write_config('//*[@title="Export"]/../..', export_type)
        sleep(5)
        for i in range(0, 10):
            if not os.path.exists(contacts_export_file):
                aklog_info('contacts文件导出中...')
                sleep(3)
            else:
                sleep(3)
                return True
        aklog_info('contacts文件导出失败')
        self.browser.screen_shot()
        return False

    def web_get_contact_info_by_name(self, name):
        aklog_info()
        self.enter_local_book()
        return self.web_get_table_row_values_dict('Name', name)

    # </editor-fold>

    # <editor-fold desc="Contacts - Local Contacts页面 - BlockList">

    def web_add_blocklist(self, name, number, account=None, ringtone=None):
        """网页phonebook添加联系人"""
        aklog_info()
        self.enter_local_book()
        self.browser.click_btn_by_xpath(self.ele_info['contacts_add_btn'])
        self.write_config(self.ele_info['contacts_add_name'], name)
        self.write_config(self.ele_info['contacts_add_number'], number)
        self.write_config(self.ele_info['contacts_add_group'], 'BlockList')
        if account is not None:
            self.write_config(self.ele_info['contacts_add_dial_account'], account)
        if ringtone is not None:
            self.write_config(self.ele_info['contacts_add_ringtone'], ringtone)
        self.click_modal_submit()
        return self.get_submit_result(is_modal=True)

    def web_edit_blocklist(self, name, new_name=None, number=None, group=None, account=None, ringtone=None):
        """编辑本地联系人黑名单"""
        aklog_info()
        self.enter_local_book()
        self.select_contact_group('BlockList')
        self.click_table_edit_btn('Local Contacts List', name=name)
        if new_name is not None:
            self.write_config(self.ele_info['contacts_add_name'], new_name)
        if number is not None:
            self.write_config(self.ele_info['contacts_add_number'], number)
        if group is not None:
            self.write_config(self.ele_info['contacts_add_group'], group)
        if account is not None:
            self.write_config(self.ele_info['contacts_add_dial_account'], account)
        if ringtone is not None:
            self.write_config(self.ele_info['contacts_add_ringtone'], ringtone)
        self.click_modal_submit()
        return self.get_submit_result(is_modal=True)

    def web_clear_blocklist(self):
        """网页清空联系人黑名单"""
        aklog_info()
        self.enter_local_book()
        self.select_contact_group('BlockList')
        if self.browser.get_ele_status_by_xpath('//span[normalize-space(text())="Delete All"]/..'):
            self.click_btn_by_text("Delete All")
            self.browser.alert_confirm_accept()
        else:
            aklog_debug('Delete All按钮不可点击，黑名单已被清空')

    def web_del_blocklist(self, index=1):
        aklog_info()
        self.select_contact_group('BlockList')
        self.delete_table_by_index(index, title='Local Contacts List')

    def get_blocklist_counts(self):
        self.select_contact_group('BlockList')
        return self.get_table_total_num(title='Local Contacts List')

    def get_blocklist_info(self, attribute=None, **base_attr):
        """
        获取联系人信息
        attribute: 要获取的属性，如果为空，则获取整行信息
        base_attr: 基于哪个属性获取联系人，一般为index, name，比如：index=1, name=xxx
        """
        aklog_info()
        self.select_contact_group('BlockList')
        return self.get_table_attribute_info(attribute=attribute, title='Local Contacts List', **base_attr)

    def get_contact_group_list(self):
        """获取联系人群组列表"""
        return self.get_select_options_list_by_xpath('//*[@id="contactListSelect"]/div[1]/div')

    def get_move_to_group_list(self):
        """获取移动到群组列表"""
        return self.get_select_options_list_by_xpath(
            '//label[normalize-space(text())="Local Contacts List"]/../..//label[normalize-space(text())="Move To"]/..//*[@role="combobox"]')

    def move_contact_to_blocklist(self, index='1'):
        """将联系人移到blocklist, index可以传入：'1', '123'同时勾选多个"""
        aklog_info()
        self.enter_local_book()
        self.select_contact_group('All Contacts')
        self.table_check_by_index(index, title='Local Contacts List')
        self.write_config(
            '//label[normalize-space(text())="Local Contacts List"]/../..//label[normalize-space(text())="Move To"]/..//*[@role="combobox"]',
            'BlockList')
        alert_text = self.web_get_alert_text_and_confirm()
        return alert_text

    def move_blocklist_to_contact(self, index='1'):
        """将blocklist移到联系人, index可以传入：'1', '123'同时勾选多个"""
        aklog_info()
        self.enter_local_book()
        self.select_contact_group('BlockList')
        self.table_check_by_index(index, title='Local Contacts List')
        self.write_config(
            '//label[normalize-space(text())="Local Contacts List"]/../..//label[normalize-space(text())="Move To"]/..//*[@role="combobox"]',
            'All Contacts')
        alert_text = self.web_get_alert_text_and_confirm()
        return alert_text

    # </editor-fold>

    # <editor-fold desc="Contacts - Local Contacts页面 - Contacts List Setting">

    def set_contacts_sort_mode(self, sort_mode):
        """
        设置联系人排序方式
        sort_mode: Default, ASCII Code, Created Time
        """
        aklog_info()
        self.enter_local_book()
        self.write_config('//*[@id="Config.Settings.CONTACT.SortMode"]/div[1]/div', sort_mode)
        self.click_submit()

    def get_contacts_sort_mode(self):
        """获取联系人排序方式"""
        return self.read_config('//*[@id="Config.Settings.CONTACT.SortMode"]/div[1]/div')

    def set_show_local_contact_only(self, enable):
        """
        设置是否只显示本地联系人
        enable: 0 or 1
        """
        aklog_info()
        self.enter_local_book()
        self.write_config('//*[@id="Config.Settings.CONTACT.ShowLocalContactsOnly"]/div[1]/div', enable)
        self.click_submit()

    def get_show_local_contact_only_status(self):
        """获取联系人排序方式"""
        return self.read_config('//*[@id="Config.Settings.CONTACT.ShowLocalContactsOnly"]/div[1]/div')

    # </editor-fold>

    # </editor-fold>

    # <editor-fold desc="Arming-Zone Setting页面相关">
    def enter_arming_zone_setting(self):
        aklog_info('enter_arming_zone_setting')
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_arming_id'])
        else:
            self.menu_expand_and_click(self.menu_xpath_info['Arming'],
                                       self.ele_info['menu_arming_zone_setting_xpath'])

    def enter_arming_mode(self):
        aklog_info()
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_arming_id'])
        self.menu_expand_and_click(self.menu_xpath_info['Arming'],
                                   self.ele_info['menu_arming_mode_xpath'])

    # </editor-fold>

    # <editor-fold desc="升级基础页面相关">
    def enter_upgrade_basic(self):
        aklog_info(self.device_name_log + 'enter_upgrade_basic')
        if self.is_homepage():
            if not self.browser.click_btn_by_id(self.ele_info['home_upgrade_id']):
                self.browser.click_btn_by_id(self.ele_info['home_system_id'])
        else:
            if 'upgrade_basic' in self.page_menu_info:
                if self.menu_expand_and_click(self.page_menu_info['upgrade_basic'][0],
                                              self.page_menu_info['upgrade_basic'][1], False):
                    return True
            if not self.menu_expand_and_click(self.menu_xpath_info.get('Upgrade'),
                                              self.ele_info['menu_upgrade_basic_xpath'], False):
                if 'System' in self.menu_xpath_info:
                    aklog_info('不同版本目录有改动，重新进入')
                    self.menu_expand_and_click(self.menu_xpath_info['System'],
                                               self.ele_info['menu_system_upgrade_xpath'], False)
                    self.page_menu_info['upgrade_basic'] = [self.menu_xpath_info['System'],
                                                            self.ele_info['menu_system_upgrade_xpath']]

    def get_version(self):
        """获取当前版本号"""
        aklog_info('获取版本号')
        self.web_refresh()
        self.enter_upgrade_basic()
        for i in range(0, 3):
            self.browser.web_refresh(force=True)
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_firmware_version_xpath']):
                for j in range(0, 60):
                    firmware_version = self.browser.get_value_by_xpath(
                        self.ele_info['upgrade_basic_firmware_version_xpath'])
                    if firmware_version:
                        firmware_version = self.restore_firmware_version(firmware_version)  # 有些机型OEM版本有定制model id
                        aklog_info('firmware_version: %s' % firmware_version)
                        return firmware_version
                    else:
                        sleep(5)
                        self.browser.web_refresh()
                        continue
            elif i == 0:
                aklog_error('获取版本号失败，可能是页面异常，重试...')
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
        aklog_error('获取版本号失败')
        self.browser.screen_shot()
        self.reboot_by_tln_or_ssh()
        return None

    def web_basic_upgrade(self, firmware_path, accept=True, reset=False):
        """网页基础升级，建议使用下面web_basic_upgrade_to_version这个方法"""
        aklog_info()
        version_before_upgrade = self.get_version()
        if not version_before_upgrade:
            aklog_error('获取版本号失败')
            return False
        # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
        cmd_waiting_for_network_rate_to_drop()

        self.enter_upgrade_advanced()
        self.set_autop_mode(0)
        self.enter_upgrade_basic()
        sleep(1)
        self.browser.click_btn_by_xpath(
            self.ele_info['upgrade_basic_import_xpath'] + '|' + '//*[normalize-space(text())="Import"]/..', 2)
        if not self.browser.is_exist_ele_by_xpath(
                self.ele_info['upgrade_basic_import_xpath'] + '|' + '//*[normalize-space(text())="Import"]/..', 2):
            self.browser.click_btn_by_xpath('//*[@class="ak-file-input-div"]/button[1]', 2)
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
            # self.enter_upgrade_basic()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_firmware_version_xpath']):
                aklog_info(self.device_name_log + '返回升级基础页面成功')
                return 1
            else:
                aklog_error(self.device_name_log + '返回升级基础页面失败')
                return 0
        sleep(30)
        # 判断是否处于升级状态
        begin_time = time.time()
        web_basic_upgrade_default_time = self.device_config.get_web_basic_upgrade_default_time()
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()  # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        reboot_ret = cmd_waiting_for_device_reboot(self.device_ip, wait_time1=web_basic_upgrade_default_time,
                                                   wait_time2=web_basic_upgrade_default_time / 2,
                                                   sec=boot_time_after_get_ip)  # 等待设备升级完成后重启
        # counts = int(round(web_basic_upgrade_default_time / 6, 0) + 10)
        # for i in range(0, counts):
        #     if self.browser.is_exist_and_visible_ele_by_id('failedReboot'):
        #         aklog_error(self.device_name_log + '页面提示升级失败，请检查升级失败原因')
        #         self.browser.screen_shot()
        #         self.upgrade_failed_reboot()
        #         return False
        #     elif self.browser.is_exist_and_visible_ele_by_id('tCheckDuringUpgrade') \
        #             or self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
        #         aklog_info(self.device_name_log + 'upgrade processing...')
        #         sleep(6)
        #     else:
        #         sleep(10)
        #         break
        # 判断是否返回升级基础页面

        # self.enter_upgrade_basic()
        # if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_firmware_version_xpath']):
        #     aklog_info(self.device_name_log + '返回升级基础页面')
        #     upgrade_status = True
        # else:
        #     aklog_info(self.device_name_log + '升级后没有正常刷新到升级基础页面，需要重新加载')
        #     self.browser.screen_shot()
        #     upgrade_status = False

        if not reboot_ret:
            for i in range(2):
                if not reset and self.retry_login(raise_enable=False):
                    break

                if i == 0:
                    # 小概率出现网页显示异常导致升级等待时间不够，则增加每个机型默认等待时间，如果小于默认时间则需要等待足够时间
                    wait_time = round(time.time() - begin_time)
                    if wait_time < web_basic_upgrade_default_time:
                        continue_wait_time = web_basic_upgrade_default_time - wait_time
                        aklog_error('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                        sleep(continue_wait_time)
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
                        self.modify_default_login_password()
                        self.switch_admin_user_login()
                        self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678')
                        self.switch_custom_user_login()
                        self.enter_upgrade_basic()
                    break
        else:
            self.retry_login(raise_enable=False)

        self.get_menu_xpath_info(True)
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
        aklog_info()
        current_version = self.get_version()
        if current_version:
            if current_version == dst_version:
                aklog_info(self.device_name_log + '当前版本已是: %s, 无需升级' % dst_version)
                return True
        else:
            aklog_error(self.device_name_log + '获取版本号失败')
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
        self.set_autop_mode(0)
        self.enter_upgrade_basic()
        sleep(1)
        self.browser.click_btn_by_xpath(
            self.ele_info['upgrade_basic_import_xpath'] + '|' + '//*[normalize-space(text())="Import"]/..', 2)
        if not self.browser.is_exist_ele_by_xpath(
                self.ele_info['upgrade_basic_import_xpath'] + '|' + '//*[normalize-space(text())="Import"]/..', 2):
            self.browser.click_btn_by_xpath('//*[@class="ak-file-input-div"]/button[1]', 2)
        if not self.browser.upload_file_by_xpath(self.ele_info['upgrade_basic_select_file_input_xpath'],
                                                 firmware_path, 1):
            aklog_error('可能是升级包不存在，请检查')
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_select_cancel_xpath'])
            return False
        reset_ele_exist = False  # 如果用了reset参数但是没有reset控件, 导致后续密码登录失败.
        if reset:
            if self.browser.is_exist_ele_by_xpath(self.ele_info['upgrade_basic_select_reset_to_factory_xpath']):
                reset_ele_exist = True
            self.write_config(self.ele_info['upgrade_basic_select_reset_to_factory_xpath'], 1)
        if accept:
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_select_submit_xpath'])
        else:
            # 点击取消
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_select_cancel_xpath'])
            # self.enter_upgrade_basic()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_firmware_version_xpath']):
                aklog_info(self.device_name_log + '返回升级基础页面成功')
                return 1
            else:
                aklog_error(self.device_name_log + '返回升级基础页面失败')
                return 0
        # self.browser.alert_confirm_accept()
        sleep(10)  # 升级直接失败的, 不需要30秒来等待重启. 加到wait_time1上.

        # 判断是否处于升级状态
        begin_time = time.time()
        web_basic_upgrade_default_time = self.device_config.get_web_basic_upgrade_default_time()
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()  # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        aklog_info('检查升级过程中设备升级过程所需耗时: {}'.format(web_basic_upgrade_default_time))
        reboot_ret = cmd_waiting_for_device_reboot(self.device_ip, wait_time1=web_basic_upgrade_default_time / 2 + 20,
                                                   wait_time2=web_basic_upgrade_default_time,
                                                   sec=boot_time_after_get_ip)  # 等待设备升级完成后重启
        # 等待设备升级完成后重启

        # counts = int(round(web_basic_upgrade_default_time / 6, 0) + 10)
        # for i in range(0, counts):
        #     if self.browser.is_exist_and_visible_ele_by_id('failedReboot'):
        #         aklog_error(self.device_name_log + '页面提示升级失败，请检查升级失败原因')
        #         self.browser.screen_shot()
        #         self.upgrade_failed_reboot()
        #         return False
        #     elif self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['upgrade_processing_class']):
        #         aklog_info(self.device_name_log + 'upgrade processing...')
        #         sleep(6)
        #     else:
        #         sleep(10)
        #         break
        # 判断是否返回升级基础页面

        # self.enter_upgrade_basic()
        # if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_firmware_version_xpath']):
        #     aklog_info(self.device_name_log + '网页基础升级完成')
        # else:
        #     aklog_info(self.device_name_log + '升级后没有正常刷新到基础升级页面，需要重新加载')
        #     self.browser.screen_shot()

        if reboot_ret:
            for i in range(2):
                if not reset and self.retry_login(raise_enable=False):
                    break

                if i == 0:
                    # 小概率出现网页显示异常导致升级等待时间不够，则增加每个机型默认等待时间，如果小于默认时间则需要等待足够时间
                    wait_time = round(time.time() - begin_time)
                    if wait_time < web_basic_upgrade_default_time:
                        continue_wait_time = web_basic_upgrade_default_time - wait_time
                        aklog_error('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                        sleep(continue_wait_time)
                    continue
                else:
                    self.get_device_config_by_version(dst_version)
                    # 有些OEM定制会在升级后恢复出厂，或者勾选了reset
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
        else:
            aklog_error('设备触发升级, 但未在时间内重启和获取IP, 截图...')
            self.screen_shot()
            self.retry_login(raise_enable=False)

        self.get_menu_xpath_info(True)
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
                sleep(6)
            else:
                sleep(10)
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
        aklog_error(self.device_name_log + '重启失败，请检查原因')
        self.browser.screen_shot()
        return False

    def upgrade_new_version(self, accept=True, reset=False, check_before=False):
        aklog_info(self.device_name_log + '网页升级新版本')
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        # 如果辅助设备要调用该方法，可以使用put_test_rom_version()将升级版本传入替换

        # 先判断是否要升级到过渡版本
        if check_before:
            try:
                if self.get_version() == self.rom_version:
                    return True
            except:
                pass
        if self.upgrade_to_transition_version(self.rom_version):
            reset = True

        upgrade_result = self.web_basic_upgrade_to_version(
            self.rom_version,
            self.device_config.get_local_firmware_path(self.rom_version),
            accept,
            reset)
        self.restore_device_config()
        self.screen_shot()
        param_put_reboot_process_flag(True)
        return upgrade_result

    def support_upgrade_old_version(self):
        """
        判断由于rom包未指定等问题导致的不支持升级旧版本.
        """
        aklog_info('旧版本文件: {}'.format(r'TestData\机型\NORMAL\UpgradeCover.xml'))

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
            aklog_warn('由于下载rom包失败等问题, 无法升级到新版本.')
            aklog_warn('rom文件放置路径: {}'.format(romfile))
            aklog_warn(
                'rom下载路径配置: xxx.xml/<firmware_path>配置ftp路径或者共享服务器地址, 并取消勾选skip download firmware')
            return False
        else:
            return True

    def upgrade_old_version(self, accept=True, reset=False):
        aklog_info(self.device_name_log + '网页升级旧版本')
        self.device_config.get_old_firmware(force_replace=self.force_replace_old_version)  # 强制替换旧版本升级包

        old_firmware_version = self.device_config.get_old_firmware_version()
        if old_firmware_version:

            # 先判断是否要升级到过渡版本
            if self.upgrade_to_transition_version(old_firmware_version):
                reset = True

            old_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(True),
                                            old_firmware_version, self.device_config.get_firmware_ext())
            File_process.copy_file(self.device_config.get_old_firmware_path(), old_firmware_path)
            upgrade_result = self.web_basic_upgrade_to_version(old_firmware_version,
                                                               old_firmware_path,
                                                               accept,
                                                               reset)
            File_process.remove_file(old_firmware_path)
        else:
            old_firmware_path = self.device_config.get_old_firmware_path()
            if not old_firmware_path:
                aklog_error('旧版本升级包不存在')
                return False
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
            aklog_info('获取版本号失败')
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
        test_data = self.device_config.get_test_data('TransitionVersion.xml', print_data=True)
        if not test_data or not test_data.get('TransitionVersion'):
            aklog_info('当前机型不存在过渡版本信息')
            return None

        firmware_version = ''
        firmware_path = ''
        transition_version_data = test_data.get('TransitionVersion')
        for data in transition_version_data:
            # 获取TransitionVersion中跟当前版本分支相同的升级包版本信息
            if 'version_branch' in data and data['version_branch'] == cur_version_branch:
                firmware_version = data['firmware_version']
                firmware_path = data['firmware_path']
                break
            if 'sub_version_branch' in data and data['sub_version_branch'] == cur_sub_version_branch:
                firmware_version = data['firmware_version']
                firmware_path = data['firmware_path']
                break
        if not firmware_version:
            aklog_info('升级的目标版本跟当前版本属于不同分支，但不需要经过过渡版本')
            return None

        aklog_info('升级的目标版本跟当前版本属于不同分支，并且需要经过过渡版本')
        current_version = self.get_version()
        if current_version and current_version != firmware_version:
            self.get_device_config_by_version(current_version)

            self.download_firmware_to_upgrade_dir(firmware_version, firmware_path)
            local_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(),
                                              firmware_version, self.device_config.get_firmware_ext())

            upgrade_ret = self.web_basic_upgrade_to_version(firmware_version, local_firmware_path)
            File_process.remove_file(local_firmware_path)
            if upgrade_ret:
                aklog_info('升级到过渡版本 %s 成功' % firmware_version)
            else:
                aklog_info('升级到过渡版本 %s 失败' % firmware_version)
                return False
        else:
            aklog_info('当前版本已是过渡版本: %s, 无需升级' % firmware_version)

        if not self.device_config.get_auto_reset_after_transition_upgrade_enable():
            # 升级完成后，删除config目录下配置文件，之后再升级，相当于升级后恢复出厂，这样升级后就可以使用默认密码去登录
            aklog_info('升级到过渡版本后，删除config目录下配置文件')
            self.web_open_ssh()
            self.command_by_tln_or_ssh('rm /config/* -rf')
        param_put_reboot_process_flag(True)
        return True

    def intercom_upgrade_last_release_version(self, accept=True, reset=True):
        """
        对讲终端根据共享文件夹获取同分支的上一个release版本.
        用于测试:  从一个发布版本升级到目标版本后, 不恢复出厂直接测试功能仍能正常.
        """
        aklog_info('准备升级到上一个发布版本. ')
        last_ver_file_path = self.device_config.intercom_get_last_release_romfile()
        if not last_ver_file_path:
            aklog_error('升级到上一个发布版本失败!')
            return False
        upgrade_result = self.web_basic_upgrade(last_ver_file_path, accept=accept, reset=reset)
        aklog_debug('升级结束!')
        param_put_reboot_process_flag(True)
        self.screen_shot()
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

    def web_reset_to_factory_setting(self, accept=True):
        """网页恢复出厂设置"""
        aklog_info(self.device_name_log + '网页恢复出厂设置')
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        self.enter_upgrade_basic()
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_factory_default_xpath'])
        if accept:
            self.browser.alert_confirm_accept()
            param_put_reboot_process_flag(True)
        else:
            self.browser.alert_confirm_cancel()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reset_config_xpath']):
                aklog_info(self.device_name_log + '返回基础升级页面完成')
                return 1
            else:
                aklog_error(self.device_name_log + '返回基础升级页面失败')
                return 0
        # 判断是否处于恢复出厂等待
        begin_time = time.time()
        reset_default_time = self.device_config.get_reset_default_time()
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()  # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        ret = cmd_waiting_for_device_reboot(self.device_ip, wait_time1=180, sec=boot_time_after_get_ip)  # 等待设备恢复出厂完成后重启
        if not ret:
            aklog_error(self.device_name_log + '恢复出厂，设备未重启或重启失败，请检查')
            self.browser.screen_shot()
            return False
        # counts = int(round(reset_default_time / 6, 0) + 10)
        # for i in range(0, counts):
        #     if self.browser.is_exist_and_visible_ele_by_id('tCheckDuringUpgrade'):
        #         aklog_info(self.device_name_log + 'reset processing...')
        #         sleep(6)
        #     else:
        #         sleep(10)
        #         break

        # 恢复出厂后，如果当前版本有定制web账户密码，则使用定制账户密码登录，否则使用admin账号登录
        if self.web_admin_username == 'admin':
            self.web_admin_pwd = self.device_config.get_web_admin_passwd()
        else:
            self.web_admin_username = self.device_config.get_web_custom_username()
            self.web_admin_pwd = self.device_config.get_web_custom_passwd()

        # 判断是否返回基础升级页面
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_factory_default_xpath']) \
                or self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath']) \
                or self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['change_pwd_window_title_xpath']):
            aklog_info(self.device_name_log + '恢复出厂设置完成')
        else:
            aklog_info(self.device_name_log + '恢复出厂设置后没有正常刷新到基础升级页面，需要重新加载')
            self.browser.screen_shot()
            wait_time = round(time.time() - begin_time)
            if wait_time < reset_default_time:
                continue_wait_time = reset_default_time - wait_time
                aklog_error('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                sleep(continue_wait_time)

        # 如果默认为静态ip，则恢复出厂配置后要用默认静态ip登录并修改为dhcp模式
        self.set_network_to_dhcp_after_reset()
        self.retry_login()
        self.enter_upgrade_basic()

        # 判断是否返回基础升级页面
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_factory_default_xpath']):
            self.switch_admin_user_login()
            self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678')
            self.switch_custom_user_login()
            aklog_info(self.device_name_log + '恢复出厂设置成功')
            return True
        else:
            aklog_error(self.device_name_log + '恢复出厂设置失败，请检查原因')
            self.browser.screen_shot()
            return False

    def web_reset_config_to_factory_setting(self, accept=True, retry_login=True):
        """网页恢复出厂设置"""
        aklog_info(self.device_name_log + 'web_reset_config_to_factory_setting')
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        self.enter_upgrade_basic()
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_reset_config_xpath'])
        if accept:
            self.browser.alert_confirm_accept()
            param_put_reboot_process_flag(True)
        else:
            self.browser.alert_confirm_cancel()
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reset_config_xpath']):
                aklog_info(self.device_name_log + '返回基础升级页面完成')
                return 1
            else:
                aklog_error(self.device_name_log + '返回基础升级页面失败')
                return 0
        # 判断是否处于恢复出厂等待
        begin_time = time.time()
        reset_default_time = self.device_config.get_reset_config_default_time()
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()  # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        ret = cmd_waiting_for_device_reboot(self.device_ip, wait_time1=180, sec=boot_time_after_get_ip)  # 等待设备恢复出厂完成后重启
        if not ret:
            aklog_error(self.device_name_log + '恢复出厂，设备未重启或重启失败，请检查')
            self.browser.screen_shot()
            return False
        # counts = int(round(reset_default_time / 6, 0) + 10)
        # for i in range(0, counts):
        #     if self.browser.is_exist_and_visible_ele_by_id('tCheckDuringUpgrade'):
        #         aklog_info(self.device_name_log + 'reset processing...')
        #         sleep(6)
        #     else:
        #         sleep(10)
        #         break

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
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reset_config_xpath']) \
                or self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['login_username_xpath']) \
                or self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['change_pwd_window_title_xpath']):
            aklog_info(self.device_name_log + '恢复出厂设置完成')
        else:
            aklog_info(self.device_name_log + '恢复出厂设置后没有正常刷新到基础升级页面，需要重新加载')
            self.browser.screen_shot()
            wait_time = round(time.time() - begin_time)
            if wait_time < reset_default_time:
                continue_wait_time = reset_default_time - wait_time
                aklog_error('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                sleep(continue_wait_time)

        # 如果默认为静态ip，则恢复出厂配置后要用默认静态ip登录并修改为dhcp模式
        self.set_network_to_dhcp_after_reset()
        self.retry_login()
        self.enter_upgrade_basic()

        # 判断是否返回基础升级页面
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['upgrade_basic_reset_config_xpath']):
            self.switch_admin_user_login()
            self.web_pwd_modify(self.web_admin_pwd, 'Aa12345678')
            self.switch_custom_user_login()
            aklog_info(self.device_name_log + '恢复出厂设置成功')
            return True
        else:
            aklog_error(self.device_name_log + '恢复出厂设置失败，请检查原因')
            self.browser.screen_shot()
            return False

    def web_reboot(self, accept=True):
        """网页进行重启"""
        aklog_info(self.device_name_log + '网页进行重启')
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        self.enter_upgrade_basic()
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_basic_reboot_xpath'])
        if accept:
            self.browser.alert_confirm_accept()
            param_put_reboot_process_flag(True)
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
        cmd_waiting_for_device_reboot(self.device_ip)
        # counts = int(round(reboot_default_time / 6, 0) + 10)
        # for i in range(0, counts):
        #     if self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
        #         aklog_info(self.device_name_log + 'reboot processing...')
        #         sleep(6)
        #     else:
        #         sleep(10)
        #         break

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
                    sleep(continue_wait_time)
                self.browser.screen_shot()
                self.retry_login()
                self.enter_upgrade_basic()
        aklog_error(self.device_name_log + '重启失败，请检查原因')
        self.browser.screen_shot()
        return False

    # </editor-fold>

    # <editor-fold desc="升级高级页面 Autop相关">
    def enter_upgrade_advanced(self):
        aklog_info(self.device_name_log + 'enter_upgrade_advanced')
        if self.is_homepage():
            if not self.browser.click_btn_by_id(self.ele_info['home_upgrade_id']):
                self.browser.click_btn_by_id(self.ele_info['home_system_id'])
        if 'upgrade_advanced' in self.page_menu_info:
            if self.menu_expand_and_click(self.page_menu_info['upgrade_advanced'][0],
                                          self.page_menu_info['upgrade_advanced'][1], False):
                return True
        if not self.menu_expand_and_click(self.menu_xpath_info.get('Upgrade'),
                                          self.ele_info['menu_upgrade_advanced_xpath'], False):
            aklog_info('不同版本目录有改动，重新进入')
            self.menu_expand_and_click(self.menu_xpath_info['System'],
                                       self.ele_info['menu_system_autop_xpath'], False)
            self.page_menu_info['upgrade_advanced'] = [self.menu_xpath_info['System'],
                                                       self.ele_info['menu_system_autop_xpath']]

    def set_autop_mode(self, option_value):
        """设置autop模式, Disabled, Power On, Repeatedly等，option_value取值0-4"""
        aklog_info(self.device_name_log + 'set_autop_mode %s' % option_value)
        self.enter_upgrade_advanced()
        if str(option_value).isdigit():
            # 如果传入的是数字，那么当成序号选择，否则传入下拉框选项文本：Power On、Disabled
            option_value = int(option_value)
        self.write_config(self.ele_info['autop_mode_box_xpath'], option_value)
        self.click_submit()

    def set_repeatedly_autop(self, schedule_week, hour, minu, power_on=False):
        """
        设置autop模式为repeatedly,并设置时间
        schedule_week: 0-7, str类型， 0表示Every Day，1-7表示Mon-Sun，可以多选，比如'123'，表示选择SomeDay，Mon/Tue/Wed
        """
        if not power_on:
            self.set_autop_mode('2')
        else:
            self.set_autop_mode('3')
        schedule_week = str(schedule_week)
        if len(schedule_week) == 1:
            self.write_config(self.ele_info.get(
                'autop_schedule_week_select') or '//*[@id="Config.Autoprovision.SCHEDULE.DayOfWeek"]/div[1]/div',
                              int(schedule_week))
        else:
            # 选择Some Day
            self.write_config(self.ele_info.get(
                'autop_schedule_week_select') or '//*[@id="Config.Autoprovision.SCHEDULE.DayOfWeek"]/div[1]/div', 7)
            sleep(0.5)
            for i in range(1, 8):
                if str(i) in schedule_week:
                    self.write_config('//*[@class="ak-common-checkboxMulti-div"]/div/label[%s]//input' % i, 1)
                else:
                    self.write_config('//*[@class="ak-common-checkboxMulti-div"]/div/label[%s]//input' % i, 0)
        if 0 <= int(hour) <= 23:
            self.write_config(
                self.ele_info.get('autop_schedule_hour') or '//*[@id="Config.Autoprovision.SCHEDULE.HourOfDay"]/input',
                hour)
        else:
            aklog_info(self.device_name_log + "传入的时间参数有误")
        if 0 <= int(minu) <= 59:
            self.write_config(self.ele_info.get(
                'autop_schedule_minute') or '//*[@id="Config.Autoprovision.SCHEDULE.MinuteOfHour"]/input', minu)
        else:
            aklog_info(self.device_name_log + "传入的分钟参数有误")
        self.click_submit()

    def set_autop_schedule_time(self, hour, minu):
        """设置Automatic Autop下的Schedule配置"""
        self.enter_upgrade_advanced()
        if 0 <= hour <= 23:
            self.write_config(self.ele_info['autop_schedule_hour'], hour)
        else:
            aklog_info(self.device_name_log + "传入的时间参数有误")
        if 0 <= minu <= 59:
            self.write_config(self.ele_info['autop_schedule_minute'], minu)
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
        self.enter_upgrade_advanced()
        if not self.browser.click_btn_by_xpath('//button//*[normalize-space(text())="Clear"]'):
            self.browser.click_btn_by_xpath(self.ele_info['autop_clear_md5_xpath'])

    def clear_autop(self):
        """将autop相关配置项关闭或清空"""
        aklog_info(self.device_name_log + '清空autop配置项')
        self.enter_upgrade_advanced()
        self.browser.click_btn_by_xpath(self.ele_info['autop_clear_md5_xpath'])
        sleep(1)
        self.browser.uncheck_box_by_xpath(self.ele_info['autop_pnp_xpath'])
        self.browser.clear_edit_by_xpath(self.ele_info['autop_dhcp_option_id_xpath'], by_keys=True)
        if self.browser.is_exist_ele_by_xpath(self.ele_info['autop_dhcp_custom_option_xpath'], 1):
            self.browser.uncheck_box_by_xpath(self.ele_info['autop_dhcp_custom_option_xpath'])
            self.browser.uncheck_box_by_xpath(self.ele_info['autop_dhcp_option43_xpath'])
            self.browser.uncheck_box_by_xpath(self.ele_info['autop_dhcp_option66_xpath'])
        self.browser.clear_edit_by_xpath(self.ele_info['autop_manual_url_xpath'], by_keys=True)
        self.write_config(self.ele_info['autop_mode_box_xpath'], 1)
        self.click_submit()

    def web_set_pnp(self, enable=True):
        """
        网页设置pnp配置
        """
        self.enter_upgrade_advanced()
        self.write_config(self.ele_info['autop_pnp_xpath'], enable)
        self.click_submit()

    def pnp_autop(self):
        aklog_info(self.device_name_log + 'start pnp_autop')
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        self.clear_autop()
        self.browser.check_box_by_xpath(self.ele_info['autop_pnp_xpath'])
        self.click_submit()
        self.start_autop()

    def dhcp_option43_autop(self):
        aklog_info(self.device_name_log + 'start dhcp_option43_autop')
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        self.clear_autop()
        if self.browser.is_exist_ele_by_xpath(self.ele_info['autop_dhcp_option43_xpath'], 1):
            self.browser.check_box_by_xpath(self.ele_info['autop_dhcp_option43_xpath'])
        self.click_submit()
        self.start_autop()

    def dhcp_option66_autop(self):
        aklog_info(self.device_name_log + 'start dhcp_option66_autop')
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        self.clear_autop()
        if self.browser.is_exist_ele_by_xpath(self.ele_info['autop_dhcp_option66_xpath'], 1):
            self.browser.check_box_by_xpath(self.ele_info['autop_dhcp_option66_xpath'])
        self.click_submit()
        self.start_autop()

    def dhcp_custom_option_autop(self):
        aklog_info(self.device_name_log + 'start dhcp_custom_option_autop')
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        self.clear_autop()
        self.write_config(self.ele_info['autop_dhcp_option_id_xpath'],
                          self.device_config.get_custom_option())
        if self.browser.is_exist_ele_by_xpath(self.ele_info['autop_dhcp_custom_option_xpath'], 1):
            self.browser.check_box_by_xpath(self.ele_info['autop_dhcp_custom_option_xpath'])
        self.click_submit()
        self.start_autop()

    def manual_URL_autop(self, clear=True, autop_timeout=None, use_protocol=None):
        aklog_info(self.device_name_log + 'start manual_URL_autop')
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        if clear:
            self.clear_autop()
        self.write_config('//*[@id="Config.Autoprovision.MODE.Mode"]/div[1]/div', 1)
        self.write_config(self.ele_info['autop_manual_url_xpath'],
                          self.device_config.get_manual_autop_URL(use_protocol))
        self.click_submit()
        self.start_autop(autop_timeout)

    def set_manual_URL(self, url=None, username=None, pwd=None):
        if url is None:
            url = self.device_config.get_manual_autop_URL()
        self.write_config(self.ele_info['autop_manual_url_xpath'], url)
        if username is not None:
            self.write_config(self.ele_info['autop_manual_username_xpath'], username)
        if pwd is not None:
            self.write_config(self.ele_info['autop_manual_pwd_xpath'], pwd)
        self.click_submit()

    def click_immediately_autop(self):
        self.browser.click_btn_by_xpath(self.ele_info['autop_immediately_autop_xpath'])

    def start_autop(self, autop_timeout=None):
        """点击立即autop，开始autop升级"""
        aklog_info(self.device_name_log + '点击立即autop，开始autop升级')
        # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
        cmd_waiting_for_network_rate_to_drop()

        self.enter_upgrade_advanced()
        self.browser.click_btn_by_xpath(self.ele_info['autop_immediately_autop_xpath'])
        # self.browser.alert_confirm_accept()
        self.web_get_alert_text_and_confirm()
        sleep(30)
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
        if not autop_timeout:
            autop_timeout = self.device_config.get_autop_upgrade_default_time()
        end_time = begin_time + autop_timeout
        while time.time() < end_time:
            if self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['upgrade_processing_class']):
                aklog_info(self.device_name_log + 'autop processing...')
                sleep(6)
            else:
                sleep(10)
                break

        # 判断是否返回升级高级页面
        sleep(10)
        # self.enter_upgrade_advanced()
        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['autop_immediately_autop_xpath']):
            aklog_info(self.device_name_log + '返回升级高级页面')
            autop_status = True
        else:
            aklog_error(self.device_name_log + 'Autop升级后无法再进入升级高级页面，请检查原因')
            self.browser.screen_shot()
            autop_status = False

        for i in range(2):
            if autop_status:
                if self.retry_login(raise_enable=False) or self.login(raise_enable=False):
                    self.enter_upgrade_advanced()
                    break
            if i == 0:
                # 小概率出现网页显示异常导致升级等待时间不够，则增加每个机型默认等待时间，如果小于默认时间则需要等待足够时间
                wait_time = round(time.time() - begin_time)
                if wait_time < autop_timeout:
                    continue_wait_time = autop_timeout - wait_time
                    aklog_error('网页显示异常，需要继续等待设备重启，继续等待时间：%s秒' % continue_wait_time)
                    sleep(continue_wait_time)
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
                break

        if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['autop_immediately_autop_xpath']):
            aklog_info(self.device_name_log + 'Autop升级完成')
            return True
        else:
            aklog_error(self.device_name_log + 'Autop升级失败，请检查原因')
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
                sleep(5)
                continue
        aklog_printf('%s is not reboot' % self.device_ip)
        return False

    def input_common_aes_key(self, key):
        """输入通用AES加密密码"""
        self.enter_upgrade_advanced()
        self.write_config(self.ele_info['autop_common_aes_key_xpath'], key)
        self.click_submit()

    def input_mac_aes_key(self, key):
        """输入MAC AES加密密码"""
        self.enter_upgrade_advanced()
        self.write_config(self.ele_info['autop_mac_aes_key_xpath'], key)
        self.click_submit()

    def export_autop_template(self, dst_file_name=None):
        """导出autop模板文件"""
        aklog_info(self.device_name_log + '导出autop模板文件')
        autop_export_file = self.device_config.get_autop_export_file_path()
        File_process.remove_file(autop_export_file)
        self.enter_upgrade_advanced()
        self.browser.click_btn_by_xpath(self.ele_info['autop_export_template_xpath'])
        aklog_info(self.device_name_log + '导出autop配置文件: %s' % autop_export_file)
        sleep(20)
        # self.download_save()
        # 判断文件是否导出成功
        for i in range(0, 20):
            if os.path.exists(autop_export_file):
                sleep(3)
                if dst_file_name:
                    dst_file = self.device_config.get_chrome_download_dir() + dst_file_name
                    File_process.rename_file(autop_export_file, dst_file)
                    return dst_file
                else:
                    return True
            else:
                aklog_info(self.device_name_log + 'autop模板文件导出中...')
                sleep(3)
                continue
        aklog_error(self.device_name_log + 'autop模板文件导出失败')
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
            aklog_error(self.device_name_log + '存在配置项autop升级失败')
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
            aklog_error(self.device_name_log + 'autop默认配置项跟模板不一致')
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

    def write_config_to_cfg_file(self, cfg_file, *configs):
        """写入autop配置项到cfg文件，可以同时写入多个配置项，比如：Config.Account1.GENERAL.Label = test1"""
        aklog_info(self.device_name_log + 'write_config_to_cfg_file')
        File_process.remove_file(cfg_file)
        config_content = ''
        for config in configs:
            config_content += config + '\n'
        config_content = f'# {str(time.time())}\n' + config_content
        File_process.write_file(cfg_file, config_content)

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
        aklog_info()
        File_process.rename_file(self.device_config.get_renamecfg_URL(), self.device_cfg_URL)
        return File_process.copy_file(self.get_autop_config_file(), self.device_cfg_URL)

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

    def copy_mac_aes_cfg_to_config_manual_URL(self, cfg_file=None):
        """将AES加密配置文件复制到手动URL的下载目录替换MAC文件"""
        File_process.remove_file(self.device_comm_cfg_URL)
        File_process.copy_file(self.device_config.get_aes_autop_config_file(cfg_file), self.device_cfg_URL)

    def copy_common_aes_cfg_to_config_manual_URL(self, cfg_file=None):
        """将AES加密配置文件复制到手动URL的下载目录替换Config文件"""
        File_process.remove_file(self.device_cfg_URL)
        File_process.copy_file(self.device_config.get_aes_autop_config_file(cfg_file), self.device_comm_cfg_URL)

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

    # </editor-fold>

    # <editor-fold desc="Upgrade Diagnosis页面 -> syslog模块">
    def enter_upgrade_diagnosis(self):
        aklog_info(self.device_name_log + 'enter_upgrade_diagnosis')
        if self.is_homepage():
            if not self.browser.click_btn_by_id(self.ele_info['home_upgrade_id']):
                self.browser.click_btn_by_id(self.ele_info['home_system_id'])
        if 'upgrade_diagnosis' in self.page_menu_info:
            if self.menu_expand_and_click(self.page_menu_info['upgrade_diagnosis'][0],
                                          self.page_menu_info['upgrade_diagnosis'][1], False):
                return True
        if self.menu_xpath_info.get('System'):
            self.menu_expand_and_click(self.menu_xpath_info['System'],
                                       self.ele_info['menu_system_maintenance_xpath'], False)
            self.page_menu_info['upgrade_diagnosis'] = [self.menu_xpath_info['System'],
                                                        self.ele_info['menu_system_maintenance_xpath']]
        else:
            self.menu_expand_and_click(self.menu_xpath_info.get('Upgrade'),
                                       self.ele_info['menu_upgrade_diagnosis_xpath'], False)

    def edit_upgrade_log_level7(self):
        """网页upgrade高级界面修改log等级为7"""
        aklog_info(self.device_name_log + 'edit_upgrade_log_level7')
        self.enter_upgrade_diagnosis()
        self.write_config(self.ele_info['upgrade_diagnosis_log_level_xpath'], '7')
        self.click_submit()

    def get_selected_log_level(self):
        """获取当前选择的log等级"""
        aklog_info(self.device_name_log + 'get_selected_log_level')
        self.enter_upgrade_diagnosis()
        return self.read_config(self.ele_info['upgrade_diagnosis_log_level_xpath'])

    def set_syslog_level(self, level=7):
        self.enter_upgrade_diagnosis()
        self.write_config(self.ele_info['upgrade_diagnosis_log_level_xpath'], str(level))
        sleep(1)
        self.click_submit()

    def export_system_log(self):
        """导出system log文件"""
        aklog_info(self.device_name_log + '导出system log文件')
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        export_system_log_file = self.device_config.get_chrome_download_dir() + self.device_config.get_log_file_name()
        File_process.remove_file(export_system_log_file)  # 先删除下载目录下的PhoneLog.tgz文件
        self.enter_upgrade_diagnosis()
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_log_export_xpath'])
        sleep(5)
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not os.path.exists(export_system_log_file):
                aklog_info(self.device_name_log + 'system log文件导出中...')
                sleep(3)
            else:
                aklog_info(self.device_name_log + 'system log文件导出成功')
                sleep(3)
                return True
        aklog_error(self.device_name_log + 'system log文件导出导出失败')
        self.browser.screen_shot()
        return False

    def export_syslog_to_results_dir(self, case_name):
        """网页导出syslog并保存到Results目录下"""
        # if not self.login_status:
        #     aklog_info(self.device_name_log + 'login status is False')
        #     return False
        aklog_info()
        if hasattr(self, 'api_hangup'):
            self.api_hangup()
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file = '{}\\PhoneLog--{}--{}--{}.tgz'.format(log_dir, case_name, self.device_name, log_time)
        File_process.create_dir(log_dir)
        export_system_log_file = self.device_config.get_chrome_download_dir() + self.device_config.get_log_file_name()
        self.export_system_log()
        File_process.copy_file(export_system_log_file, log_file)  # 将log文件保存到Results目录下

    def set_remote_syslog(self, enable=1, server=None):
        """
        设置远程系统日志,
        :param enable: 1, 0
        :param server: 远程syslog服务器地址
        """
        self.enter_upgrade_diagnosis()
        if server is None:
            server = self.device_config.get_server_address()
        if enable:
            aklog_info('set_remote_syslog: %s' % server)
            self.write_config(self.ele_info['upgrade_diagnosis_log_remote_syslog_enable'], 1)
            sleep(0.5)
            self.write_config(self.ele_info['upgrade_diagnosis_log_remote_syslog_server'], server)
        else:
            self.write_config(self.ele_info['upgrade_diagnosis_log_remote_syslog_enable'], 0)
        self.click_submit()

    def get_syslog_export_btn_status(self):
        self.enter_upgrade_diagnosis()
        return self.browser.get_ele_status_by_xpath(self.ele_info['upgrade_diagnosis_log_export_xpath'])

    def get_remote_syslog_edit_status(self):
        self.enter_upgrade_diagnosis()
        return self.browser.get_ele_status_by_xpath(self.ele_info['upgrade_diagnosis_log_remote_syslog_server'])

    def get_remote_syslog_status(self):
        self.enter_upgrade_diagnosis()
        return self.read_config(self.ele_info['upgrade_diagnosis_log_remote_syslog_enable'])

    # </editor-fold>

    # <editor-fold desc="Upgrade Diagnosis页面 -> PCAP模块">

    def set_pcap_port(self, pcap_port):
        """网页设置PCAP的端口"""
        self.enter_upgrade_diagnosis()
        self.write_config(self.ele_info['upgrade_diagnosis_pcap_port_xpath'], pcap_port)
        self.click_submit()

    def start_pcap(self, specify_port=''):
        """开始网页抓包start_pcap"""
        File_process.remove_file(self.get_pcap_file())  # 抓包前删除文件, 避免抓包失败导致的重复文件判断
        aklog_info(self.device_name_log + '开始网页抓包start_pcap')
        self.enter_upgrade_diagnosis()
        if specify_port is not None:
            cur_port = self.browser.get_attribute_value_by_xpath(self.ele_info['upgrade_diagnosis_pcap_port_xpath'])
            if cur_port != str(specify_port):
                self.write_config(self.ele_info['upgrade_diagnosis_pcap_port_xpath'], str(specify_port))
                self.click_submit()
                sleep(1)
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_pcap_start_xpath'])
        sleep(2)
        self.browser.alert_confirm_accept()

    def stop_pcap(self):
        """停止网页抓包stop_pcap"""
        aklog_info(self.device_name_log + '停止网页抓包stop_pcap')
        self.enter_upgrade_diagnosis()
        # self.browser.alert_confirm_accept()
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_pcap_stop_xpath'])
        sleep(2)
        self.browser.alert_confirm_accept()

        # 自动清空抓包端口过滤, 方便start_pcap的使用
        cur_port = self.browser.get_attribute_value_by_xpath(self.ele_info['upgrade_diagnosis_pcap_port_xpath'])
        if cur_port:
            self.write_config(self.ele_info['upgrade_diagnosis_pcap_port_xpath'], '')
            self.click_submit()
            sleep(1)

    def export_pcap(self):
        """导出pcap文件"""
        aklog_info(self.device_name_log + '导出pcap文件')
        export_pcap = self.device_config.get_export_pcap_file()
        File_process.remove_file(export_pcap)  # 先删除下载目录下的PhoneLog.tgz文件
        self.enter_upgrade_diagnosis()
        if not self.browser.get_ele_status_by_xpath(self.ele_info['upgrade_diagnosis_pcap_export_xpath']):
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_pcap_stop_xpath'])
            self.browser.alert_confirm_accept()
            sleep(1)
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_pcap_export_xpath'])
        sleep(3)
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not os.path.exists(export_pcap):
                aklog_info(self.device_name_log + 'pcap文件导出中...')
                sleep(3)
            else:
                aklog_info(self.device_name_log + '导出pcap文件成功')
                sleep(1)
                return True
        aklog_error(self.device_name_log + 'pcap文件导出导出失败')
        self.browser.screen_shot()
        return False

    def stop_and_export_pcap(self):
        self.stop_pcap()
        self.export_pcap()

    def get_pcap_file(self):
        """返回导出的pcap文件路径"""
        aklog_debug()
        return self.device_config.get_chrome_download_dir() + 'phone.pcap'

    def set_pcap_auto_refresh(self, value):
        """
        :param value: 1、0，或者True、False
        """
        self.enter_upgrade_diagnosis()
        self.write_config(self.ele_info['upgrade_diagnosis_pcap_auto_refresh_xpath'], value)
        self.click_submit()

    def judge_is_pcap_port_valid(self, port):
        """封装功能:  输入端口号, 并提交. 之后判断输入的pcap端口号是否合法"""
        self.enter_upgrade_diagnosis()
        self.write_config(self.ele_info['upgrade_diagnosis_pcap_port_xpath'], port)
        self.click_submit()
        sleep(2)
        return self.get_submit_result()

    def click_pcap_btn(self, btn):
        """
        封装功能: 点击pcap的几个按钮
        btn: Start, Stop, Export
        """
        btn_dict = {
            'Start': self.ele_info['upgrade_diagnosis_pcap_start_xpath'],
            'Stop': self.ele_info['upgrade_diagnosis_pcap_stop_xpath'],
            'Export': self.ele_info['upgrade_diagnosis_pcap_export_xpath']
        }
        self.browser.click_btn_by_xpath(btn_dict[btn])

    def get_pcap_btn_status(self, btn):
        """
        封装功能: 获取pcap按钮 是否可编辑状态
        """
        btn_dict = {
            'Start': self.ele_info['upgrade_diagnosis_pcap_start_xpath'],
            'Stop': self.ele_info['upgrade_diagnosis_pcap_stop_xpath'],
            'Export': self.ele_info['upgrade_diagnosis_pcap_export_xpath']
        }
        return self.browser.get_ele_status_by_xpath(btn_dict[btn])

    def wait_pcap_over_size(self, timeout=300):
        """
        等待PCAP抓包超出大小
        reenter: 是否重新进入pcap设置页面，如果为True，一般是在其他页面等待抓包超出大小，然后再进入PCAP设置页面
        """
        counts = int(round(timeout / 5, 0))
        alert_text = self.browser.get_alert_text()
        for i in range(counts):
            if alert_text:
                self.browser.alert_confirm_accept()
                break
            else:
                sleep(5)
                alert_text = self.browser.get_alert_text()
                continue
        self.enter_upgrade_diagnosis()
        if alert_text:
            if self.get_pcap_btn_status('Stop') is False:
                return alert_text
            else:
                aklog_info('没有自动停止抓包')
                return False
        else:
            if self.get_pcap_btn_status('Stop') is False:
                aklog_info('已自动停止抓包，但没有提示超过大小')
                return True
            else:
                aklog_info('没有自动停止抓包')
                return None

    @staticmethod
    def is_pcap_exist_port(pcap_file, device_ip, port):
        """判断抓包文件是否包含该设备的某端口"""
        pcap = pcap_operation()
        pcap.read_pcap(pcap_file)
        data1 = pcap.get_data_from_pcap(trans_type='TCP', src_ip=device_ip, src_port=port)
        data2 = pcap.get_data_from_pcap(trans_type='TCP', dst_ip=device_ip, dst_port=port)
        data3 = pcap.get_data_from_pcap(trans_type='UDP', src_ip=device_ip, src_port=port)
        data4 = pcap.get_data_from_pcap(trans_type='UDP', dst_ip=device_ip, dst_port=port)
        if data1 or data2 or data3 or data4:
            return True
        # for data in datas:
        #     data = data.decode('utf-8')
        #     aklog_info(data)
        #     if data:
        #         return True
        return False

    def save_pcap_to_results_dir(self, case_name=None):
        """保存PCAP文件到Results目录下"""
        log_time = time.strftime('%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        if case_name is None:
            case_name = ''
        pcap_file = '{}\\PhonePcap--{}--{}--{}.pcap'.format(log_dir, case_name, self.device_name, log_time)
        File_process.create_dir(log_dir)
        export_pcap = self.device_config.get_export_pcap_file()
        File_process.copy_file(export_pcap, pcap_file)

    # </editor-fold>

    # <editor-fold desc="Upgrade Diagnosis页面 -> Config导入导出模块">

    def import_config_file(self, config_file=None, error_ignore=True):
        """保持原用法基础上, 增加参数: cfg 用于如R20T30机型cfg文件不能包含数字字母以外字符"""
        aklog_info(self.device_name_log + 'import_config_file')
        self.enter_upgrade_diagnosis()
        if not config_file:
            config_file = self.device_config.get_config_import_file()
        else:
            if ':' not in config_file:  # 指定的路径也可以是相对于root_path的相对路径（Windows系统）
                config_file = root_path + config_file
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_config_import_btn'])
        self.browser.upload_file_by_xpath(self.ele_info['upgrade_diagnosis_config_select_file_input'], config_file)
        # 判断是否有右上角提交提示语，文件格式错误时会提示
        submit_tips1 = self.get_submit_tips()
        if submit_tips1:
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_config_select_cancel_btn'])
            return submit_tips1
        # 点击导入按钮
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_config_select_import_btn'])
        sleep(1)

        # 判断是否有右上角提交提示语，文件太大时会提示
        submit_tips2 = self.get_submit_tips()
        if submit_tips2:
            self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_config_select_cancel_btn'])
            return submit_tips2

        alert = self.get_alert_tips_and_confirm()
        if not error_ignore and alert != 'The phone will be reboot after import, make sure to import it?':
            # 如果不忽略错误，用于导入错误文件，判断弹窗提示并返回
            return alert

        sleep(5)
        # Processing等待中
        for i in range(0, 40):
            if self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['processing_class']):
                aklog_info(self.device_name_log + 'import config processing...')
                sleep(3)
                continue
            submit_tips3 = self.get_submit_tips()
            if submit_tips3:
                self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_config_select_cancel_btn'])
                return submit_tips2
            else:
                sleep(5)
                break
        # 重新登录
        if self.retry_login():
            aklog_info(self.device_name_log + '导入配置文件完成')
            return True
        else:
            aklog_error(self.device_name_log + '导入配置文件失败')
            self.screen_shot()
            return False

    def export_config_file(self):
        """导出config文件"""
        config_file = self.device_config.get_config_file_path()
        aklog_info(self.device_name_log + '导出config文件: %s' % config_file)
        File_process.remove_file(config_file)
        self.enter_upgrade_diagnosis()
        self.browser.click_btn_by_xpath(self.ele_info['upgrade_diagnosis_config_export_btn'])
        sleep(20)
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not os.path.exists(config_file):
                aklog_info(self.device_name_log + 'config文件导出中...')
                sleep(3)
            else:
                sleep(3)
                return True
        aklog_error(self.device_name_log + 'config文件导出失败')
        self.browser.screen_shot()
        return False

    # </editor-fold>

    # <editor-fold desc="Security Basic页面相关">
    def enter_security_basic(self):
        aklog_info(self.device_name_log + 'enter_security_basic')
        if self.is_homepage():
            if not self.browser.click_btn_by_id(self.ele_info['home_security_id']):
                self.browser.click_btn_by_id(self.ele_info['home_system_id'])
        if 'security_basic' in self.page_menu_info:
            if self.menu_expand_and_click(self.page_menu_info['security_basic'][0],
                                          self.page_menu_info['security_basic'][1], False):
                return True
        if not self.menu_expand_and_click(self.menu_xpath_info.get('Security'),
                                          self.ele_info['menu_security_basic_xpath'], False):
            aklog_info('不同版本目录有改动，重新进入')
            if 'System' in self.menu_xpath_info:
                self.menu_expand_and_click(self.menu_xpath_info['System'],
                                           self.ele_info['menu_system_security_xpath'], False)
                self.page_menu_info['security_basic'] = [self.menu_xpath_info['System'],
                                                         self.ele_info['menu_system_security_xpath']]

    def web_pwd_modify(self, current_pwd, new_pwd):
        """网页修改登录密码"""
        aklog_info()
        if current_pwd == new_pwd:
            aklog_info(self.device_name_log + 'current_pwd = new_pwd, not need modify')
            return True
        else:
            for i in range(2):
                self.enter_security_basic()
                if not self.browser.is_exist_and_visible_ele_by_class_name(self.ele_info['home_logout_class']) and \
                        not self.browser.is_exist_and_visible_ele_by_class_name(
                            self.ele_info['security_user_name_ctrl_id']):
                    self.retry_login()
                    continue
                else:
                    break
            if self.browser.is_exist_and_visible_ele_by_xpath(self.ele_info['security_change_pwd_btn_xpath']):
                self.write_config(self.ele_info['security_user_combobox_xpath'],
                                  self.web_admin_username)
                self.browser.click_btn_by_xpath(self.ele_info['security_change_pwd_btn_xpath'])
                self.write_config(self.ele_info['change_pwd_window_old_pwd_xpath'], current_pwd)
                self.write_config(self.ele_info['change_pwd_window_new_pwd_xpath'], new_pwd)
                sleep(0.5)
                self.write_config(self.ele_info['change_pwd_window_confirm_pwd_xpath'], new_pwd)
                self.browser.click_btn_by_xpath(self.ele_info['change_pwd_window_change_btn_xpath'])
                # self.browser.alert_confirm_accept()
                sleep(1)
                self.browser.web_refresh()
            # 登出网页，用新密码再重新登录
            self.web_admin_pwd = new_pwd
            if self.retry_login():
                return True
            else:
                self.web_admin_pwd = current_pwd
                aklog_error(self.device_name_log + 'modify pwd failed')
                self.browser.screen_shot()
                return False

    def change_password(self, old_pwd, new_pwd, confirm_pwd=None, user='admin'):
        """
        封装功能: 点击change password, 输入密码, 点击change
        用于测试修改密码功能过程中的提示语测试
        """
        aklog_info('change_password')
        self.enter_security_basic()
        self.write_config(self.ele_info['security_user_combobox_xpath'], user)
        self.click_btn_by_xpath(self.ele_info['security_change_pwd_btn_xpath'])
        self.input_edit_and_sleep_by_xpath(self.ele_info["change_pwd_window_old_pwd_xpath"], old_pwd)
        self.input_edit_and_sleep_by_xpath(self.ele_info["change_pwd_window_new_pwd_xpath"], new_pwd)
        sleep(1)

        # 错误提示 : ['×', '√', '×', '√']
        tips_list = self.browser.get_values_by_xpath('//*[@class="ak-modal-span"]/../../div/label')
        # 只获取new pwd的提示语
        flags_list = []
        for value in tips_list:
            if '×' in value:
                flags_list.append('×')
            elif '√' in value:
                flags_list.append('√')

        if not flags_list:
            if not confirm_pwd:
                self.input_edit_and_sleep_by_xpath(self.ele_info["change_pwd_window_confirm_pwd_xpath"], new_pwd)
            else:
                self.input_edit_and_sleep_by_xpath(self.ele_info["change_pwd_window_confirm_pwd_xpath"], confirm_pwd)
            self.click_btn_by_xpath(self.ele_info['change_pwd_window_change_btn_xpath'])
            return []
        else:
            self.click_btn_by_xpath(self.ele_info['change_pwd_window_cancel_btn_xpath'])
            return flags_list

    def get_select_mod_pwd_user_name(self):
        return self.read_config(self.ele_info['security_user_combobox_xpath'])

    def set_web_session_time_out(self, time_out):
        aklog_info(self.device_name_log + 'set_web_session_time_out, time_out: %s' % time_out)
        self.enter_security_basic()
        self.write_config(self.ele_info['security_session_timeout_xpath'], time_out)
        self.click_submit()

    def get_web_session_time_out(self):
        self.enter_security_basic()
        return self.read_config(self.ele_info['security_session_timeout_xpath'])

    def set_web_user_account(self, enable):
        """设置网页Account Status User用户是否开启, enable: 1 or 0"""
        self.enter_security_basic()
        self.write_config(self.ele_info['security_account_status_user_checkbox'], int(enable))
        self.click_submit()

    def get_web_user_account_status(self):
        """获取user用户是否开启，返回True or False"""
        self.enter_security_basic()
        user_account_status = self.read_config(self.ele_info['security_account_status_user_checkbox'])
        if user_account_status is True or user_account_status == 'Enabled':
            ret = True
        elif user_account_status is False or user_account_status == 'Disabled':
            ret = False
        else:
            ret = None
        return ret

    def get_web_admin_account_status(self):
        """获取Admin用户是否开启"""
        self.enter_security_basic()
        return self.read_config(self.ele_info['security_account_status_admin_label'])

    # </editor-fold>

    # <editor-fold desc="Security Advanced页面，Service Location">

    def enter_security_advanced(self):
        aklog_info()
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_security_id'])
        self.menu_expand_and_click(self.menu_xpath_info.get('Security'), self.ele_info['menu_security_advanced_xpath'])

    def get_service_location(self):
        return self.read_config('//*[@id="Config.Settings.SERVICE.Location"]/div[1]/div')

    def set_service_location(self, location):
        self.enter_security_advanced()
        self.write_config('//*[@id="Config.Settings.SERVICE.Location"]/div[1]/div', location)
        self.click_submit()

    # </editor-fold>

    # <editor-fold desc="8848隐藏页面相关">
    def enter_hide_page_8848(self):
        """进入隐藏页面"""
        url = '%s/#/8848' % self.login_url
        aklog_info(self.device_name_log + '打开页面: %s' % url)
        self.browser.visit_url(url)
        if self.browser.get_value_by_xpath(self.ele_info['hidden_page_title_xpath']) not in ['Hidden page',
                                                                                             'Hidden Page', '8848']:
            self.retry_login()
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
            sleep(2)
        result = self.set_ssh_or_tln('1')
        # self.enter_homepage()
        self.enter_web_account_basic()
        sleep(10)
        return result

    def web_ping_network(self, address):
        """验证网络连通性"""
        self.write_config('//*[@id="VerifyNetwork"]/input', address)
        self.click_btn_by_text('Ping')
        red_tips = self.get_edit_red_tips('//*[@id="VerifyNetwork"]/input')
        if red_tips:
            return red_tips
        sleep(15)
        result = ''
        for i in range(10):
            result = self.browser.get_attribute_value_by_xpath('//*[@class="ak-common-textarea ant-input"]')
            if not result:
                aklog_info('ping结果还未出来，继续等待...')
                sleep(3)
                continue
            sleep(3)
            result1 = self.browser.get_attribute_value_by_xpath('//*[@class="ak-common-textarea ant-input"]')
            if result1 == result:
                # 两次获取结果一致，说明ping结束
                break
            elif i == 9:
                aklog_info('ping没有结果')
                self.browser.screen_shot()
                break
            else:
                sleep(3)
                continue
        return result

    def get_web_ping_address_edit(self):
        return self.read_config('//*[@id="VerifyNetwork"]/input')

    def get_web_web_ping_result(self):
        return self.browser.get_attribute_value_by_xpath('//*[@class="ak-common-textarea ant-input"]')

    # </editor-fold>

    # <editor-fold desc="Network Basic页面">
    def enter_network_basic(self):
        aklog_info(self.device_name_log + 'enter_network_basic')
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_network_id'])
        else:
            self.menu_expand_and_click(self.menu_xpath_info['Network'],
                                       self.ele_info['menu_network_basic_xpath'])

    def set_network_to_dhcp(self):
        aklog_info(self.device_name_log + 'set_network_to_dhcp')
        self.enter_network_basic()
        self.browser.click_btn_by_xpath(self.ele_info['network_basic_dhcp_xpath'])
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

    # <editor-fold desc="Network Advanced页面">
    def enter_network_advanced(self):
        aklog_info(self.device_name_log + 'enter_network_advanced')
        if self.is_homepage():
            self.browser.click_btn_by_id(self.ele_info['home_network_id'])
        self.menu_expand_and_click(self.menu_xpath_info['Network'], self.ele_info['menu_network_advanced_xpath'])

    def get_location(self):
        """获取设备的location"""
        aklog_info("get_location")
        self.enter_network_advanced()
        location = self.browser.get_attribute_value_by_xpath('//*[@id="DeviceLocation" or @id="DisplayName"]/div/input')
        return location

    def get_connect_server_mode(self):
        aklog_info("get_connect_server_mode")
        self.enter_network_advanced()
        return self.browser.get_value_by_xpath(self.ele_info['network_connect_server_mode'])

    def set_discovery_mode(self, mode):
        """mode: 0 or 1"""
        self.enter_network_advanced()
        self.write_config(self.ele_info['network_connect_discovery_mode'], mode)
        self.click_submit()

    def get_discovery_mode(self):
        self.enter_network_advanced()
        return self.read_config(self.ele_info['network_connect_discovery_mode'])

    def get_device_node(self):
        node = ''
        for i in range(1, 6):
            address = self.read_config(self.ele_info['network_connect_device_address%s' % i])
            if address:
                node = node + '.' + address
        return node

    def set_device_node_address(self, node_address=None, extension=None, location=None, confirm=True):
        """
        node_address: 1.1.1.1.1
        """
        if node_address is not None:
            node_address = node_address.split('.')
            node_len = len(node_address)
            node1 = node2 = node3 = node4 = node5 = ''
            if node_len >= 1:
                node1 = node_address[0]
            if node_len >= 2:
                node2 = node_address[1]
            if node_len >= 3:
                node3 = node_address[2]
            if node_len >= 4:
                node4 = node_address[3]
            if node_len >= 5:
                node5 = node_address[4]
            self.write_config(self.ele_info['network_connect_device_address1'], node1)
            self.write_config(self.ele_info['network_connect_device_address2'], node2)
            self.write_config(self.ele_info['network_connect_device_address3'], node3)
            self.write_config(self.ele_info['network_connect_device_address4'], node4)
            self.write_config(self.ele_info['network_connect_device_address5'], node5)
        if extension is not None:
            self.write_config(self.ele_info['network_connect_device_extension'], extension)
        if location is not None:
            self.write_config(self.ele_info['network_connect_device_location'], location)
        self.click_submit(accept=confirm)

    def set_location_connect_setting(self, discovery_mode=None, node_address=None, extension=None, location=None):
        aklog_info()
        self.enter_network_advanced()
        if discovery_mode is not None:
            self.write_config(self.ele_info['network_connect_discovery_mode'], discovery_mode)
        self.set_device_node_address(node_address, extension, location)

    def get_address_edit_status(self):
        """获取address、extension、location的输入框状态"""
        self.enter_network_advanced()
        self.web_refresh()
        ret1 = self.browser.get_ele_status_by_xpath(self.ele_info['network_connect_device_address1'])
        ret2 = self.browser.get_ele_status_by_xpath(self.ele_info['network_connect_device_address2'])
        ret3 = self.browser.get_ele_status_by_xpath(self.ele_info['network_connect_device_address3'])
        ret4 = self.browser.get_ele_status_by_xpath(self.ele_info['network_connect_device_address4'])
        ret5 = self.browser.get_ele_status_by_xpath(self.ele_info['network_connect_device_address5'])
        ret6 = self.browser.get_ele_status_by_xpath(self.ele_info['network_connect_device_extension'])
        ret7 = self.browser.get_ele_status_by_xpath(self.ele_info['network_connect_device_location'])
        return [ret1, ret2, ret3, ret4, ret5, ret6, ret7]

    def get_web_min_rtp_port(self):
        """获取Starting RTP Port的值"""
        min_rtp_port = self.read_config(self.ele_info['network_local_rtp_min_port'])
        return min_rtp_port

    def get_web_max_rtp_port(self):
        """获取Max RTP Port的值"""
        max_rtp_port = self.read_config(self.ele_info['network_local_rtp_max_port'])
        return max_rtp_port

    def set_web_min_rtp_port(self, port):
        """网页设置Starting RTP Port"""
        self.write_config(self.ele_info['network_local_rtp_min_port'], port)

    def set_web_max_rtp_port(self, port):
        """网页设置Max RTP Port"""
        self.write_config(self.ele_info['network_local_rtp_max_port'], port)

    # </editor-fold>

    # <editor-fold desc="Telnet/SSH通用操作">

    def telnet_login(self):
        aklog_info()
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
                sleep(5)
                continue
            else:
                aklog_error('Telnet连接登录失败')
                return False

    def telnet_logout(self):
        self.tln.command_stop()
        self.tln.logout_host()

    def ssh_login(self):
        aklog_info()
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
                sleep(5)
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
            aklog_debug('result: %s' % value)
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
        try:
            result = self.tln.command_result(command)
        except Exception as e:
            # 概率出现is_connected()返回True,但实际提示主机中的软件中止了一个已建立的连接。
            aklog_info('error:' + str(e))
            self.telnet_login()
            result = self.tln.command_result(command)
        if print_result:
            aklog_debug('result:\n %s' % result)
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
            sleep(0.5)
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
            sleep(0.5)
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
        sleep(0.5)
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
        sleep(1)
        self.tln.thread_exec_command(command)
        return self.tln

    def get_result_by_interactive_telnet_thread(self, timeout=60):
        """获取Telnet交互式子线程执行结果，需要与exec_command_by_interactive_ssh_thread配合使用"""
        return self.tln.thread_stop_exec_output_result(timeout=timeout)

    # </editor-fold>

    # <editor-fold desc="Telnet/SSH命令">

    def reboot_by_tln_or_ssh(self, wait_reboot=True):
        aklog_info()
        self.command_by_tln_or_ssh('reboot')
        param_put_reboot_process_flag(True)
        if wait_reboot:
            cmd_waiting_for_device_reboot(self.device_info['ip'])

    def get_uptime_by_tln_or_ssh(self):
        """获取开机时间"""
        aklog_info()
        uptime = self.get_result_by_tln_or_ssh(
            'uptime | cut -d "p" -f 2 | cut -b "1-15"|sed "s/\\([^0-9][^0-9]*\\)//g"')
        aklog_info(self.device_name_log + 'uptime: %s min' % uptime)
        return uptime

    def start_adb_server_by_ssh(self, device_id=None, retry_counts=5):
        aklog_info()
        if not device_id:
            device_id = self.device_info.get('deviceid')
        if not device_id:
            aklog_error('device id 为空')
            return False
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
                    sleep(3)
                    return True
                elif i < 2:
                    self.web_open_ssh()
                    continue
                else:
                    aklog_error('Start Adb Server 失败，重试...')
                    sleep(3)
                    continue
            except:
                aklog_error('遇到未知异常，等待重试...' + str(traceback.format_exc()))
                sleep(5)
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
        aklog_info()
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
        """ps获取进程信息，判断多个进程是否都正在运行"""
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
        """如果是交互式获取log，可以使用ignore_previous_logs_by_interactive_ssh_thread代替"""
        aklog_info(self.device_name_log + 'clear_logs_by_ssh')
        self.exec_command_by_ssh('logcat -G 2M', 'logcat -c')

    def clear_logs_by_tln(self):
        aklog_info(self.device_name_log + 'clear_logs_by_tln')
        self.command_by_tln_or_ssh('rm /tmp/Messages* -f', 'echo "" > /tmp/Messages')

    def clear_logs_by_tln_or_ssh(self):
        """如果是交互式获取log，可以使用ignore_previous_logs_by_interactive_ssh_thread代替"""
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
            command += ' | grep -v grep | grep "%s"' % log_flag
        ssh_log = self.get_result_by_tln_or_ssh(command, print_result=False)
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
        aklog_info(self.device_name_log + 'save_logs_to_result_dir_by_tln_or_ssh')
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

    # </editor-fold>


if __name__ == '__main__':
    device_info = {'device_name': 'X933', 'ip': '192.168.3.121'}
    device_config = config_parse_device_config('config_X933_NORMAL')
    param_put_browser_headless_enable(True)  # 是否开启浏览器无头模式
    browser = libbrowser(device_info, device_config)
    web = web_v4_device_NORMAL()
    web.init_without_start(browser)
    print(web.top_get_process_info('system_server'))
