# -*- coding: UTF-8 -*-
import time
import sys
import os
import time
import ddt

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

g_chrome_driver_path = '%s\\testcase\\apps\\chromedriver.exe' % root_path


def return_remote_web(url, username, password):
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--headless')
    chrome_driver_path = g_chrome_driver_path
    chrome_driver_path = chrome_driver_path.replace('\\', '/')
    a = webdriver.Chrome(options=chrome_options, executable_path=chrome_driver_path)
    a.set_page_load_timeout(30)
    a.implicitly_wait(10)
    a.get(url)
    login(a, username, password)
    time.sleep(5)
    return a


def login(driver, username, password):
    driver.find_element_by_name('username').send_keys(username)
    driver.find_element_by_name('password').send_keys(password)
    login_btn = '//*[@id="form"]/div[3]'
    driver.find_element_by_xpath(login_btn).click()


def enter_device_setting_panel(driver, mac):
    mac = mac.replace(':', '').upper()
    driver.refresh()
    driver.find_element_by_xpath('.//li[normalize-space(text())="社区设备"]').click()
    detail_btn = r"(.//*[text()='{}']/../../..//button)[3]".format(mac)
    driver.find_element_by_xpath(detail_btn).click()

    setting_btn = './/button//span[text()="设置"]'
    driver.find_element_by_xpath(setting_btn).click()


def remote_web_reboot(driver, mac):
    enter_device_setting_panel(driver, mac)
    driver.find_element_by_xpath('.//span[text()="重启"]').click()
    driver.find_element_by_xpath("//button//span[normalize-space(text())='确认']").click()


def remote_web_change_transport(driver, mac, transport):
    transport = transport.upper()
    enter_device_setting_panel(driver, mac)
    driver.find_element_by_xpath(r'.//*[@class="el-input__icon el-icon-caret-top"]').click()
    time.sleep(1)
    driver.find_element_by_xpath(
        r'.//*[@class="el-scrollbar__view el-select-dropdown__list"]//span[text()="{}"]'.format(transport)).click()
    driver.find_element_by_xpath("//button//span[normalize-space(text())='提交']").click()


def remote_web_autop(driver, mac, autop_content):
    enter_device_setting_panel(driver, mac)
    # driver.find_element_by_xpath("//button//span[normalize-space(text())='单次Autop']").click()
    # driver.find_element_by_xpath('(.//*[@class="el-textarea__inner"])[2]').send_keys(autop_content)
    # driver.find_element_by_xpath("(//button//span[normalize-space(text())='提交'])[2]").click()
    driver.find_element_by_xpath('.//textarea[@class="el-textarea__inner"]').clear()
    driver.find_element_by_xpath('.//textarea[@class="el-textarea__inner"]').send_keys(autop_content)
    driver.find_element_by_xpath("(//button//span[normalize-space(text())='提交'])[1]").click()


def remote_web_view(driver, mac, self=None):
    enter_device_setting_panel(driver, mac)
    driver.find_element_by_xpath("//button//span[normalize-space(text())='远程控制']").click()
    time.sleep(5)
    ret = driver.window_handles
    if len(ret) != 2:
        print('远程控制网页失败')
        return False
    else:
        driver.switch_to.window(ret[1])
        img_base64 = driver.get_screenshot_as_base64()
        if img_base64:
            if self:
                try:
                    param_append_screenshots_imgs(img_base64)
                except:
                    pass
        else:
            try:
                param_append_screenshots_imgs('')
            except:
                pass
        try:
            driver.find_element_by_id('username')
        except:
            return False
        else:
            return True
