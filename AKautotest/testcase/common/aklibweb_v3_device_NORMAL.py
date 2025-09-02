#!/usr/bin/env python3
# -*- coding: utf-8 -*-

######## Import Start ########

# from import

# import as
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
from aklibweb_device_NORMAL import *


######## Import End ########


class web_v3_device_NORMAL(web_device_NORMAL):

    # 通用操作API
    def menu_expand_and_click(self, menu_id, submenu_id, ignore_error=True):
        aklog_info('[' + self.device_name + '] ' + 'menu_expand_and_click %s %s ' % (menu_id, submenu_id))
        if not self.login_status:
            aklog_info('login status is False')
            return False
        for i in range(3):
            if not self.browser.is_exist_and_visible_ele_by_id(menu_id):
                if i == 0 and self.browser.is_exist_alert():
                    self.browser.alert_confirm_accept()
                    continue
                elif i <= 1:
                    self.retry_login()
                    continue
                else:
                    aklog_error('menu_expand_and_click failed')
                    return False
            else:
                break
        if not self.browser.is_exist_and_visible_ele_by_id(submenu_id):
            self.browser.click_btn_by_id(menu_id)
            time.sleep(2)
        self.browser.click_btn_by_id(submenu_id)
        for j in range(3):
            if self.browser.get_attribute_by_id(submenu_id, 'style'):
                aklog_info('enter page success')
                break
            elif not ignore_error:
                aklog_error('menu_expand_and_click failed')
                return False

            if not self.browser.is_exist_and_visible_ele_by_id(submenu_id):
                if j == 0:
                    self.browser.click_btn_by_id(menu_id)
                    if self.browser.is_exist_alert():
                        self.browser.alert_confirm_accept()
                    continue
                elif j == 1:
                    self.retry_login()
                    continue
                else:
                    aklog_error('menu_expand_and_click failed')
                    return False
            else:
                self.browser.click_btn_by_id(submenu_id)
                if self.browser.is_exist_alert():
                    self.browser.alert_confirm_accept()
                continue
        return True

    def click_submit(self, sec=4):
        """点击提交按钮"""
        aklog_info('[' + self.device_name + '] ' + '点击提交按钮')
        self.click_btn_and_sleep_by_id("PageSubmit", sec)

    def is_checked_box_and_sleep_by_id(self, cmd, sec=0.2):
        """封装通过id进行判断勾选框是否勾选并延时"""
        aklog_info("%s,is_checked_box_and_sleep_by_id" % self.__class__.__name__)
        checked_status = self.browser.get_attribute_by_id(cmd, 'checked')
        time.sleep(sec)
        if checked_status == "true":
            return True
        else:
            return False

    def judge_and_check_labelbox_by_id(self, checkbox_id, label_id):
        """通过id勾选复选框(这个复选框是checkbox和label的结合，判断checkbox，点击label)"""
        aklog_info("%s,judge_and_check_labelbox_by_id" % self.__class__.__name__)
        if self.is_checked_box_and_sleep_by_id(checkbox_id) is not True:
            self.browser.check_box_by_id(label_id)

    def judge_and_uncheck_labelbox_by_id(self, checkbox_id, label_id):
        """通过id取消勾选复选框(这个复选框是checkbox和label的结合，判断checkbox，点击label)"""
        aklog_info("%s,judge_and_uncheck_labelbox_by_id" % self.__class__.__name__)
        if self.is_checked_box_and_sleep_by_id(checkbox_id) is True:
            self.browser.check_box_by_id(label_id)

    def judge_and_check_labelbox_by_xpath(self, checkbox_id, label_xpath):
        """通过xpath勾选复选框(这个复选框是checkbox和label的结合，判断checkbox，点击label)"""
        aklog_info("%s,judge_and_check_labelbox_by_xpath" % self.__class__.__name__)
        if self.is_checked_box_and_sleep_by_id(checkbox_id) is not True:
            self.browser.check_box_by_xpath(label_xpath)

    def judge_and_uncheck_labelbox_by_xpath(self, checkbox_id, label_xpath):
        """通过xpath取消勾选复选框(这个复选框是checkbox和label的结合，判断checkbox，点击label)"""
        aklog_info("%s,judge_and_uncheck_labelbox_by_xpath" % self.__class__.__name__)
        if self.is_checked_box_and_sleep_by_id(checkbox_id) is True:
            self.browser.check_box_by_xpath(label_xpath)

    def check_box_by_click_label(self, box_id, sec=0.2):
        """复选框被label覆盖，需要点击label才能勾选"""
        if not self.is_checked_box_and_sleep_by_id(box_id):
            self.browser.click_btn_by_xpath('//input[@id="%s"]/following-sibling::label[1]' % box_id)
        time.sleep(sec)

    def uncheck_box_by_click_label_by_id(self, box_id, sec=0.2):
        """复选框被label覆盖，需要点击label才能取消勾选"""
        aklog_info('uncheck_box_by_click_label')
        if self.is_checked_box_and_sleep_by_id(box_id):
            self.browser.click_btn_by_xpath('//input[@id="%s"]/following-sibling::label[1]' % box_id)
        time.sleep(sec)

    def judge_ele_id_status(self, ele_id):
        """判断ele_id是否可点击"""
        aklog_info("%s,judge_ele_id_status" % self.__class__.__name__)
        return self.browser.get_id_status(ele_id)

    def judge_ele_xpath_status(self, ele_xpath):
        """判断ele_xpath是否可点击"""
        aklog_info("%s,judge_ele_xpath_status" % self.__class__.__name__)
        return self.browser.get_ele_xpath_status(ele_xpath)

    # 登录相关
    def login(self, url=None):
        """登录网页"""
        aklog_info('[' + self.device_name + '] ' + 'login')
        if url is None:
            url = 'http://%s' % self.device_ip
        self.browser.visit_url(url)
        self.browser.web_refresh(force=True)
        login_counts = 0
        for i in range(0, 4):
            if self.browser.is_exist_and_visible_ele_by_id('username'):
                self.browser.input_edit_by_id("username", self.web_admin_username)
                self.browser.input_edit_by_id("password", self.web_admin_pwd)
                self.browser.click_btn_by_id("Login")
                login_counts += 1
                if self.browser.is_exist_and_visible_ele_by_id('tStatus') or \
                        self.browser.is_exist_and_visible_ele_by_id('cPhoneLanguage'):
                    aklog_info('[' + self.device_name + '] ' + '登录网页 %s 成功' % url)
                    self.modify_default_login_password()
                    self.login_status = True
                    return True

                # 多次登录失败限制登录，需要等待3分钟
                alert_text = self.browser.get_alert_text()
                if alert_text and '3 minutes' in alert_text:
                    self.browser.alert_confirm_accept()
                    time.sleep(190)

                # 如果登录失败，则更改密码重新登录
                if login_counts == 1:
                    aklog_error('[' + self.device_name + '] ' + '密码: %s 登录失败，改密重登' % self.web_admin_pwd)
                    self.browser.screen_shot()
                    # 第一次登录失败，改用客户定制的admin用户的密码来登录
                    self.web_admin_pwd = self.device_config.get_web_admin_passwd()
                    continue
                elif login_counts == 2:
                    aklog_error('[' + self.device_name + '] ' + '密码: %s 登录失败，改密重登' % self.web_admin_pwd)
                    self.browser.screen_shot()
                    # 第二次登录失败，改用客户定制的用户和密码来登录，如果没有定制用户，则密码改为admin来登录
                    if self.web_admin_username != self.device_config.get_web_custom_username():
                        self.web_admin_username = self.device_config.get_web_custom_username()
                        self.web_admin_pwd = self.device_config.get_web_custom_passwd()
                    else:
                        self.web_admin_pwd = 'admin'
                    continue
                else:
                    aklog_error('[' + self.device_name + '] ' + '登录网页 %s 失败' % url)
                    self.browser.screen_shot()
                    self.login_status = False
                    return False
            elif self.browser.is_exist_and_visible_ele_by_id('tStatus')or \
                        self.browser.is_exist_and_visible_ele_by_id('cPhoneLanguage'):
                aklog_info('[' + self.device_name + '] ' + '网页已登录，无需再重新登录')
                self.modify_default_login_password()
                self.login_status = True
                return True
            else:
                self.browser.web_refresh()
                continue
        aklog_error('[' + self.device_name + '] ' + '登录网页 %s 失败' % url)
        self.browser.screen_shot()
        self.login_status = False
        return False

    def retry_login(self):
        aklog_info('[' + self.device_name + '] ' + 'retry_login')
        alert_text = self.browser.get_alert_text()
        if alert_text and '3 minutes' in alert_text:
            self.browser.alert_confirm_accept()
            time.sleep(190)
        current_url = self.browser.get_current_url()
        self.browser.close_and_quit()
        time.sleep(2)
        self.browser.init()
        # self.clear_browser_cache_data()
        self.retry_visit_url(current_url)
        self.browser.web_refresh()

        for i in range(2):
            if self.browser.is_exist_and_visible_ele_by_id('username'):
                self.browser.input_edit_by_id("username", self.web_admin_username)
                self.browser.input_edit_by_id("password", self.web_admin_pwd)
                self.browser.click_btn_by_id("Login")
                time.sleep(1)
            if i == 0:
                self.modify_default_login_password()

        # 判断是否登录成功
        if self.browser.is_exist_and_visible_ele_by_id('tStatus')or \
                self.browser.is_exist_and_visible_ele_by_id('cPhoneLanguage'):
            aklog_info('[' + self.device_name + '] ' + '重登网页成功')
            self.login_status = True
            return True
        else:
            aklog_error('[' + self.device_name + '] ' + '重登网页失败')
            self.browser.screen_shot()
            self.login_status = False
            return False

    # 测试界面
    def enter_test_page(self):
        # linux室内机登入web UI自动化测试界面
        url = 'http://%s/fcgi/do?id=8849' % self.device_ip
        self.browser.visit_url(url)
        if self.browser.is_exist_ele_by_id('dlgid'):
            if self.browser.get_value_by_id("dlgid") == '172':
                self.browser.click_btn_by_id('ts')
                self.browser.click_btn_by_id('refresh')
            aklog_info('[' + self.device_name + '] ' + '正常进入测试界面')
            return True
        else:
            aklog_info('[' + self.device_name + '] ' + '没有正常进入测试界面')
            self.browser.screen_shot()
            self.retry_login()
            self.browser.visit_url(url)
            return False

    # Status页面相关 #
    def enter_Status_basic(self):
        """进入网页status界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页status界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Status')
        else:
            self.browser.click_btn_by_id('tMenu10')

    def web_get_current_version(self):
        """网页获取当前版本号"""
        aklog_info('[' + self.device_name + '] ' + '网页获取当前版本号')
        self.enter_Status_basic()
        firmware_version = self.browser.get_value_by_id('cFirmwareVersion')
        return firmware_version

    def get_version(self):
        """获取当前版本号"""
        aklog_info('[' + self.device_name + '] ' + '获取版本号')
        if self.browser.is_exist_and_visible_ele_by_id('tMenu10'):
            self.browser.click_btn_by_id('tMenu10')
            for i in range(0, 2):
                if self.browser.is_exist_and_visible_ele_by_id('tFirmwareVersion'):
                    firmware_version = self.browser.get_value_by_id('cFirmwareVersion')
                    for j in range(0, 60):
                        if firmware_version:
                            firmware_version = self.restore_firmware_version(firmware_version)  # 有些机型OEM版本有定制model id
                            aklog_info('[' + self.device_name + '] ' + 'firmware_version: %s' % firmware_version)
                            return firmware_version
                        else:
                            time.sleep(5)
                            self.browser.web_refresh()
                            firmware_version = self.browser.get_value_by_id('cFirmwareVersion')
                else:
                    aklog_error('[' + self.device_name + '] ' + '获取版本号失败，可能是status页面异常，重试...')
                    self.browser.screen_shot()
                    self.retry_login()
                    self.browser.click_btn_by_id('tStatus')
                    time.sleep(5)
        elif self.browser.is_exist_and_visible_ele_by_id('tStatus'):
            for i in range(0, 2):
                if self.browser.is_exist_and_visible_ele_by_id('tFirmwareVersion'):
                    firmware_version = self.browser.get_value_by_id('cFirmwareVersion')
                    for j in range(0, 60):
                        if firmware_version:
                            firmware_version = self.restore_firmware_version(firmware_version)  # 有些机型OEM版本有定制model id
                            aklog_info('[' + self.device_name + '] ' + 'firmware_version: %s' % firmware_version)
                            return firmware_version
                        else:
                            time.sleep(5)
                            self.browser.web_refresh()
                            firmware_version = self.browser.get_value_by_id('cFirmwareVersion')
                else:
                    aklog_error('[' + self.device_name + '] ' + '获取版本号失败，可能是status页面异常，重试...')
                    self.browser.screen_shot()
                    self.retry_login()
                    time.sleep(5)
        aklog_error('[' + self.device_name + '] ' + '获取版本号失败')
        self.browser.screen_shot()
        return None

    # upgrade basic页面
    def web_basic_upgrade(self, firmware_path):
        """网页基础升级"""
        aklog_info('[' + self.device_name + '] ' + 'web_basic_upgrade, firmware_path: %s' % firmware_path)
        self.login_upgrade_advanced()
        self.set_autop_mode('0')
        self.login_upgrade_basic()
        self.browser.upload_file_by_id('UpgradeB_UpgradeFile', firmware_path)
        self.browser.click_btn_by_id('UpgradeConfirmBtn')
        self.browser.alert_confirm_accept()
        time.sleep(5)
        # 判断是否处于升级状态
        for i in range(0, 100):
            if self.browser.is_exist_and_visible_ele_by_id('failedReboot'):
                aklog_error('[' + self.device_name + '] ' + '页面提示升级失败，请检查升级失败原因')
                self.browser.screen_shot()
                self.upgrade_failed_reboot()
                return False
            elif self.browser.is_exist_and_visible_ele_by_id('tCheckDuringUpgrade') \
                    or self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
                aklog_info('[' + self.device_name + '] ' + 'upgrade processing...')
                time.sleep(6)
            else:
                time.sleep(20)
                break
        # 判断是否返回升级基础页面
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('tUpgrade'):
                aklog_info('[' + self.device_name + '] ' + '网页基础升级完成')
                return True
            else:
                aklog_info('[' + self.device_name + '] ' + '升级后没有正常刷新到基础升级页面，需要重新加载')
                self.browser.screen_shot()
                self.retry_login()
                self.login_upgrade_basic()
        aklog_error('[' + self.device_name + '] ' + '网页升级失败，请检查原因')
        self.browser.screen_shot()
        return False

    def upgrade_failed_reboot(self):
        aklog_error('[' + self.device_name + '] ' + '提示升级失败，重启')
        self.browser.click_btn_by_id('failedReboot')
        for i in range(0, 100):
            if self.browser.is_exist_and_visible_ele_by_id('tPhoneUsingStatus'):
                aklog_info('[' + self.device_name + '] ' + 'reboot processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break
        # 判断是否返回升级基础页面
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('tUpgrade'):
                aklog_info('[' + self.device_name + '] ' + '重启完成')
                return True
            else:
                aklog_info('[' + self.device_name + '] ' + '重启后没有正常刷新到基础升级页面，需要重新加载')
                self.browser.screen_shot()
                self.retry_login()
                self.login_upgrade_basic()
        aklog_error('[' + self.device_name + '] ' + '重启失败，请检查原因')
        self.browser.screen_shot()
        return False

    def login_upgrade_basic(self):
        """home page界面登入Upgrade_basic界面"""
        aklog_info('[' + self.device_name + '] ' + 'home page界面登入Upgrade_basic界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Upgrade')
        self.menu_expand_and_click('tMenu60', 'tMenu61')

    def web_reset_to_factory_setting(self):
        """网页恢复出厂设置"""
        aklog_info('[' + self.device_name + '] ' + '网页恢复出厂设置')
        self.login_upgrade_basic()
        self.browser.click_btn_by_id('ResetFactory')
        self.browser.alert_confirm_accept()
        # 判断是否处于恢复出厂等待
        for i in range(0, 100):
            if self.browser.is_exist_and_visible_ele_by_id('tCheckDuringUpgrade'):
                aklog_info('[' + self.device_name + '] ' + 'reset processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break
        self.web_admin_pwd = self.device_config.get_web_admin_passwd()
        # 判断是否返回基础升级页面
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('tUpgrade'):
                aklog_info('[' + self.device_name + '] ' + '恢复出厂设置完成')
                # self.web_admin_pwd = self.device_config.get_web_admin_passwd()
                self.web_pwd_modify(self.web_admin_pwd, 'admin')
                return True
            else:
                aklog_info('[' + self.device_name + '] ' + '恢复出厂设置后没有正常刷新到基础升级页面，需要重新加载')
                self.browser.screen_shot()
                # 如果默认为静态ip，则恢复出厂配置后要用默认静态ip登录并修改为dhcp模式
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
                    # 导入配置文件将ip设置为DHCP模式
                    self.write_cfg_items_to_import_file('Config.Network.LAN.Type = 0')
                    self.import_config_file()
                    cmd_delete_ip_address(pc_ip_address)
                self.retry_login()
                self.login_upgrade_basic()
        aklog_error('[' + self.device_name + '] ' + '恢复出厂设置失败，请检查原因')
        self.browser.screen_shot()
        return False

    def web_reset_factory_except_userdata_setting(self):
        """网页恢复出厂配置(用户数据除外)"""
        if not self.login_status:
            aklog_info('login status is False')
            return False
        self.enter_upgrade_basic()
        self.browser.click_btn_by_id('ResetFactoryExceptUserData', 1)
        self.browser.alert_confirm_accept(wait_time=2)
        # 判断是否处于恢复出厂等待
        for i in range(0, 100):
            if self.browser.is_exist_and_visible_ele_by_id('tCheckDuringUpgrade'):
                aklog_info('[' + self.device_name + '] ' + 'reset processing...')
                time.sleep(6)
            else:
                time.sleep(10)
                break
        self.web_admin_pwd = self.device_config.get_web_admin_passwd()
        # 判断是否返回基础升级页面
        for i in range(0, 2):
            if self.browser.is_exist_and_visible_ele_by_id('tUpgrade'):
                aklog_info('[' + self.device_name + '] ' + '恢复出厂设置完成')
                # self.web_admin_pwd = self.device_config.get_web_admin_passwd()
                self.web_pwd_modify(self.web_admin_pwd, 'admin')
                return True
            else:
                aklog_info('[' + self.device_name + '] ' + '恢复出厂设置后没有正常刷新到基础升级页面，需要重新加载')
                self.browser.screen_shot()
                # 如果默认为静态ip，则恢复出厂配置后要用默认静态ip登录并修改为dhcp模式
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
                    # 导入配置文件将ip设置为DHCP模式
                    self.write_cfg_items_to_import_file('Config.Network.LAN.Type = 0')
                    self.import_config_file()
                    cmd_delete_ip_address(pc_ip_address)
                self.retry_login()
                self.login_upgrade_basic()
        aklog_error('[' + self.device_name + '] ' + '恢复出厂设置失败，请检查原因')
        self.browser.screen_shot()
        return False

    # upgrade advanced页面
    def login_upgrade_advanced(self):
        """登入Upgrade_advanced界面"""
        aklog_info('[' + self.device_name + '] ' + '登入Upgrade_advanced界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Upgrade')
        self.menu_expand_and_click('tMenu60', 'tMenu62')

    def disable_PNP(self):
        """disable PNP功能"""
        aklog_info('[' + self.device_name + '] ' + 'disable PNP功能')
        self.browser.swipe_down_by_xpath('//*[@id="UpgradeA_divPNP"]/div[2]/div/div[2]/input[1]',
                                         '//*[@id="UpgradeA_divPNP"]/div[2]/div/div[2]/div/ul/li[1]')
        self.browser.click_btn_by_xpath('//*[@id="UpgradeA_divPNP"]/div[2]/div/div[2]/div/ul/li[1]')

    def enable_PNP(self):
        """enable PNP功能"""
        aklog_info('[' + self.device_name + '] ' + 'disable PNP功能')
        self.browser.swipe_down_by_xpath('//*[@id="UpgradeA_divPNP"]/div[2]/div/div[2]/input[1]',
                                         '//*[@id="UpgradeA_divPNP"]/div[2]/div/div[2]/div/ul/li[2]')
        self.browser.click_btn_by_xpath('//*[@id="UpgradeA_divPNP"]/div[2]/div/div[2]/div/ul/li[2]')

    def clear_autop(self):
        """将autop相关配置项关闭或清空"""
        aklog_info('[' + self.device_name + '] ' + '清空autop配置项')
        self.login_upgrade_advanced()
        self.browser.click_btn_by_id('ClearMD5Btn')
        self.browser.set_implicitly_wait(10)
        self.disable_PNP()
        self.browser.restore_implicitly_wait()
        if self.browser.is_exist_and_visible_ele_by_name('cDHCPCustomOption'):
            self.browser.clear_edit_by_name('cDHCPCustomOption')
        if self.browser.is_exist_and_visible_ele_by_name('cDHCPOptionCustom'):
            self.browser.uncheck_box_by_name('cDHCPOptionCustom')
        if self.browser.is_exist_and_visible_ele_by_name('cDHCPOption43'):
            self.browser.uncheck_box_by_name('cDHCPOption43')
        if self.browser.is_exist_and_visible_ele_by_name('cDHCPOption66'):
            self.browser.uncheck_box_by_name('cDHCPOption66')
        self.browser.clear_edit_by_name('cManualUpdateURL')
        self.set_autop_mode('1')
        self.click_submit()

    def pnp_autop(self):
        aklog_info('[' + self.device_name + '] ' + 'start pnp_autop')
        self.clear_autop()
        self.enable_PNP()
        self.click_submit()
        self.start_autop()

    def edit_upgrade_log_level7(self):
        """网页upgrade高级界面修改log等级为7"""
        aklog_info('[' + self.device_name + '] ' + 'edit_upgrade_log_level7')
        self.menu_expand_and_click('tMenu140', 'tMenu141')
        self.browser.swipe_down_by_xpath('//*[@id="UpgradeA_divSystemLog"]/div[2]/div[1]/div/input[1]',
                                         '//*[@id="UpgradeA_divSystemLog"]/div[2]/div[1]/div/div/ul/li[8]')
        self.browser.click_btn_by_xpath('//*[@id="UpgradeA_divSystemLog"]/div[2]/div[1]/div/div/ul/li[8]')
        time.sleep(2)

    def export_system_log(self):
        """导出system log文件"""
        aklog_info('[' + self.device_name + '] ' + '导出system log文件')
        export_system_log_file = self.device_config.get_chrome_download_dir()
        self.menu_expand_and_click('tMenu140', 'tMenu141')
        self.browser.click_btn_by_id('BtnExportLog')
        aklog_info('[' + self.device_name + '] ' + '导出system log文件')
        time.sleep(20)
        # self.download_save()
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not os.path.exists(export_system_log_file):
                aklog_info('[' + self.device_name + '] ' + 'system log文件导出中...')
                time.sleep(3)
            else:
                time.sleep(3)
                return True
        aklog_error('[' + self.device_name + '] ' + 'system log文件导出导出失败')
        self.browser.screen_shot()
        return False

    def start_pcap(self):
        """开始网页抓包start_pcap"""
        aklog_info('[' + self.device_name + '] ' + '开始网页抓包start_pcap')
        self.menu_expand_and_click('tMenu140', 'tMenu142')
        self.browser.click_btn_by_id('StartPCAP')
        self.browser.alert_confirm_accept()

    def stop_pcap(self):
        """停止网页抓包stop_pcap"""
        aklog_info('[' + self.device_name + '] ' + '停止网页抓包stop_pcap')
        self.menu_expand_and_click('tMenu140', 'tMenu142')
        self.browser.alert_confirm_accept()
        self.browser.click_btn_by_id('StopPCAP')
        self.browser.alert_confirm_accept()

    def export_pcap(self):
        """导出pcap文件"""
        aklog_info('[' + self.device_name + '] ' + '导出pcap文件')
        export_pcap = self.device_config.get_chrome_download_dir()
        self.menu_expand_and_click('tMenu140', 'tMenu142')
        self.browser.click_btn_by_id('ExportPCAP')
        time.sleep(10)
        # self.download_save()
        # 判断文件是否导出成功
        for i in range(0, 20):
            if not os.path.exists(export_pcap):
                aklog_info('[' + self.device_name + '] ' + 'pacap文件导出中...')
                time.sleep(3)
            else:
                time.sleep(3)
                return True
        aklog_error('[' + self.device_name + '] ' + 'pacap文件导出导出失败')
        self.browser.screen_shot()
        return False

    # account basic页面
    def enter_Account_basic(self):
        """进入网页Account_basic界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Account_basic界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('SIP')
        else:
            self.menu_expand_and_click('tMenu20', 'tMenu21')

    def register_sip(self, sip, sip_password, server_ip, server_port='5060', Account_Active='1'):
        """话机注册sip号功能"""
        aklog_info("%s,register_sip" % self.__class__.__name__)
        time.sleep(0.2)
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('SIP')
        else:
            self.menu_expand_and_click('tMenu20', 'tAccountB')
        time.sleep(0.2)
        self.browser.click_btn_by_xpath("//*[@id=\"mid_cont2\"]/form[1]/div[2]/div[2]/div[3]/div/input[1]")
        time.sleep(0.2)
        if Account_Active == '1':
            self.browser.click_btn_by_xpath("//*[@id=\"mid_cont2\"]/form[1]/div[2]/div[2]/div[3]/div/div/ul/li[2]")
        else:
            self.browser.click_btn_by_xpath("//*[@id=\"mid_cont2\"]/form[1]/div[2]/div[2]/div[3]/div/div/ul/li[1]")
        time.sleep(0.2)
        self.browser.input_edit_by_id('cDisplayLabel', sip)
        self.browser.input_edit_by_id('cRegisterName', sip)
        self.browser.input_edit_by_id('cDisplayName', sip)
        self.browser.input_edit_by_id('cUserName', sip)
        self.browser.input_edit_by_id('cPassword', sip_password)
        self.browser.input_edit_by_id('cFirstSIPServerAddr', server_ip)
        self.browser.input_edit_by_id('cFirstSIPServerPort', server_port)
        self.browser.click_btn_by_id("PageSubmit")

    def clear_web_account(self):
        """网页清除账号1配置为默认配置"""
        aklog_info("%s,clear_web_account" % self.__class__.__name__)
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('SIP')
        else:
            self.menu_expand_and_click('tMenu20', 'tAccountB')
        self.browser.click_btn_by_xpath("//*[@id=\"mid_cont2\"]/form[1]/div[2]/div[2]/div[3]/div/input[1]")
        time.sleep(0.2)
        self.browser.click_btn_by_xpath("//*[@id=\"mid_cont2\"]/form[1]/div[2]/div[2]/div[3]/div/div/ul/li[1]")
        time.sleep(0.2)
        self.browser.input_edit_by_id('cDisplayLabel', '')
        self.browser.input_edit_by_id('cRegisterName', '')
        self.browser.input_edit_by_id('cDisplayName', '')
        self.browser.input_edit_by_id('cUserName', '')
        self.browser.input_edit_by_id('cPassword', '')
        self.browser.input_edit_by_id('cFirstSIPServerAddr', '')
        self.browser.input_edit_by_id('cFirstSIPServerPort', '5060')
        self.browser.input_edit_by_id('cSecSIPServerAddr', '')
        self.browser.input_edit_by_id('cSecSIPServerPort', '5060')
        self.browser.click_btn_by_id("PageSubmit")

    # account advanced页面
    def enter_Account_advanced(self):
        """进入网页Account_advanced界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Account_advanced界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('SIP')
            self.browser.click_btn_by_id('tMenu22')
        else:
            self.menu_expand_and_click('tMenu20', 'tMenu22')

    # Network Ethernet页面
    def enter_Network_Ethernet(self):
        """进入网页Network_Ethernet界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Network_Ethernet界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Network')
        else:
            self.menu_expand_and_click('tMenu30', 'tMenu31')

    # Network Wifi页面
    def enter_Network_Wifi(self):
        """进入网页Network_Wifi界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Network_Wifi界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Network')
            self.browser.click_btn_by_id('tMenu32')
        else:
            self.menu_expand_and_click('tMenu30', 'tMenu32')

    # device time页面
    def enter_Device_Time_lang(self):
        """进入网页Device_Time_lang界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Device_Time_lang界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Device')
        else:
            self.menu_expand_and_click('tMenu40', 'tMenu41')

    # device call feature页面
    def enter_Device_CallFeature(self):
        """进入网页Device_CallFeature界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Device_CallFeature界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Device')
            self.browser.click_btn_by_id('tMenu42')
        else:
            self.menu_expand_and_click('tMenu40', 'tMenu42')

    # device key/display页面
    def enter_Device_KeyDisplay(self):
        """进入网页Device_KeyDisplay界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Device_KeyDisplay界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Device')
            self.browser.click_btn_by_id('tMenu441')
        else:
            self.menu_expand_and_click('tMenu40', 'tMenu441')

    # device audio页面
    def enter_Device_Audio(self):
        """进入网页Device_Audio界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Device_Audio界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Device')
            self.browser.click_btn_by_id('tMenu45')
        else:
            self.menu_expand_and_click('tMenu40', 'tMenu45')

    # device intercom页面
    def enter_Device_Intercom(self):
        """进入网页Device_Intercom界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Device_Intercom界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Device')
            self.browser.click_btn_by_id('tMenu418')
        else:
            self.menu_expand_and_click('tMenu40', 'tMenu418')

    # device relay页面
    def enter_Device_Relay(self):
        """进入网页Device_Relay界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Device_Relay界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Device')
            self.browser.click_btn_by_id('tMenu420')
        else:
            self.menu_expand_and_click('tMenu40', 'tMenu420')

    # device multicast页面
    def enter_Device_MultiCast(self):
        """进入网页Device_MultiCast界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Device_MultiCast界面')
        url = 'http://%s//fcgi/do?id=4&id=12' % self.device_ip
        self.browser.visit_url(url)
        time.sleep(1)

    # Contact Address Book页面
    def enter_Contact_Address_Book(self):
        """进入网页Contact的AddressBook界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Contact的AddressBook界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Contact')
        else:
            self.menu_expand_and_click('tMenu50', 'tMenu51')

    # Contact call log页面
    def enter_Contact_calllog(self):
        """进入网页Contact的calllog界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Contact的calllog界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Contact')
            self.browser.click_btn_by_id('tMenu52')
        else:
            self.menu_expand_and_click('tMenu50', 'tMenu52')

    # Arming Zone Setting页面
    def enter_Arming_ZoneSetting(self):
        """进入网页Arming_ZoneSetting界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Arming_ZoneSetting界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Arming')
        else:
            self.menu_expand_and_click('aMenu9', 'tMenu112')

    # Arming Arming Mode页面
    def enter_Arming_ArmingMode(self):
        """进入网页Arming_ArmingMode界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Arming_ArmingMode界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Arming')
            self.browser.click_btn_by_id('tMenu113')
        else:
            self.menu_expand_and_click('aMenu9', 'tMenu113')

    # Arming Disarm Code页面
    def enter_Arming_DisarmCode(self):
        """进入网页Arming_DisarmCode界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Arming_DisarmCode界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Arming')
            self.browser.click_btn_by_id('tMenu114')
        else:
            self.menu_expand_and_click('aMenu9', 'tMenu114')

    # Arming Alarm Action页面
    def enter_Arming_AlarmAction(self):
        """进入网页Arming_AlarmAction界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Arming_AlarmAction界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Arming')
            self.browser.click_btn_by_id('tMenu118')
        else:
            self.menu_expand_and_click('aMenu9', 'tMenu118')

    # Diagnosis Syslog页面
    def enter_Diagnosis_Syslog(self):
        """进入网页Diagnosis_Syslog界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Diagnosis_Syslog界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Status')
            self.browser.click_btn_by_id('aMenu12')
        else:
            self.menu_expand_and_click('aMenu12', 'tMenu141')

    # Diagnosis Tools页面
    def enter_Diagnosis_Tools(self):
        """进入网页Diagnosis_Tools界面"""
        aklog_info('[' + self.device_name + '] ' + '进入网页Diagnosis_Tools界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Status')
            self.menu_expand_and_click('aMenu12', 'tMenu142')
        else:
            self.menu_expand_and_click('aMenu12', 'tMenu142')

    # Security basic页面
    def enter_Security_basic(self):
        """进入安全基础界面"""
        aklog_info('[' + self.device_name + '] ' + '进入安全基础界面')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Upgrade')
        self.menu_expand_and_click('tMenu70', 'tMenu71')

    def enter_security_basic(self):
        aklog_info('enter_security_basic')
        if self.browser.is_exist_ele_by_id('tStatus'):
            self.browser.click_btn_by_link_text('Upgrade')
        self.menu_expand_and_click(self.web_element_info['security_menu'],
                                   self.web_element_info['security_basic_submenu'])

    def get_account_registered_status(self):
        """网页status界面获取账号注册状态"""
        aklog_info('[' + self.device_name + '] ' + '网页status界面获取账号注册状态')
        # self.menu_expand_and_click('tMenu10', 'tMenu11')
        time.sleep(5)  # 网页设计要实时去获取当前账号状态，所以那边会稍微等点时间
        tag_name = self.browser.get_tag_name_by_id("cAccountStatus")
        if tag_name == "label":
            value = self.browser.get_value_by_id("cAccountStatus")
        elif tag_name == 'input':
            value = self.browser.get_attribute_value_by_id("cAccountStatus")
        else:
            value = ''
        return value

    def browser_close_and_quit(self):
        self.browser.close_and_quit()

    def reset_imgs(self):
        self.browser.reset_imgs()

    def start_and_login(self):
        self.browser.init()
        self.login()

    def click_device(self):
        # 点击device
        self.browser.click_btn_by_id('tMenu170')
        time.sleep(2)

    def click_LCD(self):
        # 点击LCD
        self.browser.click_btn_by_id('tLcd')
        time.sleep(2)
        self.browser.alert_confirm_accept()

    def get_screensaver_mode(self):
        """获取screensaver_mode值"""
        aklog_info('[' + self.device_name + '] ' + '获取screensaver_mode值')
        time.sleep(5)  # 网页设计要实时去获取当前账号状态，所以那边会稍微等点时间
        value = self.browser.get_attribute_value_by_xpath('//*[@id="mid_cont2"]/form[1]/div/div[2]/div[1]/div/input[1]')
        return value