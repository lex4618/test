#!/usr/bin/env python3
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

# 官网对应firmware url的机型名
model_id = {
    # 门口机
    "539": 'S539',
    "532": 'S532',
    "2915": 'X915V2',
    "915": 'X915',
    "916": 'X916',
    "912": 'X912',
    "910": 'X910',
    "29": 'R29',
    "228": 'R28SV823',
    "28": 'R28',
    "227": 'R27V2',  # 待确认
    "25": 'R25',
    "320": "R20SV823",
    "220": "R20T30",  # 待确认
    "18": "E18",
    "216": "E16V2",
    "116": "E16",
    "13": "E13",
    # "12": "E12",
    "312": "E12",
    "21": "E21",  # 待确认
    "120": "E20",
    '111': 'E11',
    '201': 'DB01',

    '567': 'S567',
    '565': 'S565',
    '563': 'S563',
    '562': 'S562',
    '560': 'S560',
    '88': 'IT88',
    '83': 'IT83',
    '82': 'IT82',
    '937': 'X937',
    '933': 'X933',
    '119': 'C319',
    '316': 'C316',
    '313': 'C313V3',
    '213': 'C313V2',
    '113': 'C313',
    '212': 'C313-2',
    '311': 'C313W-LP-2',
    '115': 'C315',
    '117': 'C317',

    # 门禁
    '108': 'A08',
    '205': 'A05V2',
    '105': 'A05',
    '101': 'A01/A02',
    '103': 'A03',
    '92': 'A094/A092',
    '33': 'EC33'
}


class GetReleaseVerFromAkuvox(object):
    """
    https://knowledge.akuvox.com/docs/firmware-7

    最新release: https://maintenance.akuvox.com/firmware/release/stable/?model_name=S539
    最新Beta:  https://maintenance.akuvox.com/firmware/release/beta/?model_name=S539

    从官方下载最新rom包, 用于测试: 从官方版本升级上来测试版本做测试. 只能用于Akuvox版本.
    1. 其他OEM版本要从//192.168.254.9里拿
    2. 网站上备注: 若只有beta版本没有release版本, 则需要联系人员才能下载, 此时无法从官方获取.
    """
    file_name = ''
    file_version = ''
    nowver_downloadfile_dict = {}

    def __init__(self, now_version):
        self.browser = libbrowser(wait_time=5)
        self.now_version = now_version
        modelid = self.now_version.split('.')[0]
        oemid = self.now_version.split('.')[1]
        modelname = model_id.get(modelid)
        if modelname and oemid in ['30']:
            self.browser_init()

    def browser_init(self):
        self.browser.init()
        # self.browser.init_headless()

    def browser_close_and_quit(self):
        self.browser.close_and_quit()

    def get_download_dir(self):
        return aklog_get_result_dir() + '\\ChromeDownload\\COMMON\\'

    def visit_url(self, url):
        for i in range(3):
            try:
                self.browser.visit_url(url)
                return True
            except:
                aklog_printf(traceback.format_exc())
                time.sleep(10)
                continue
        return False

    def get_akuvox_release_firmware(self):
        modelid = self.now_version.split('.')[0]
        oemid = self.now_version.split('.')[1]
        if oemid not in ['30']:
            aklog_error('OEM: {} 版本不从官网下载.'.format(oemid))
            return False

        modelname = model_id.get(modelid)
        if not modelname:
            aklog_error(f'model id : {modelid} 对应机型名没有维护!')
            return False
        ret = self.visit_url(f'https://maintenance.akuvox.com/firmware/release/stable/?model_name={modelname}')
        if not ret:
            aklog_info(f'model id : {modelid} 官网获取release版本失败, 尝试获取beta版本')
            ret = self.visit_url(f'https://maintenance.akuvox.com/firmware/release/beta/?model_name={modelname}')
            if not ret:
                aklog_error(f'model id : {modelid} 官网获取release/beta版本失败!!')
                return False
        rom_state = False
        download_xpath = '//tbody//tr[1]//a'
        romname_xpath = '//tbody//tr//*[@class="firmware-name"]//span'
        if self.browser.is_exist_ele_by_xpath(romname_xpath):
            rom_state = True
        else:
            if 'release/' in self.browser.get_current_url():
                ret = self.visit_url(f'https://maintenance.akuvox.com/firmware/release/beta/?model_name={modelname}')
                if ret and self.browser.is_exist_ele_by_xpath(romname_xpath):
                    rom_state = True
        if not rom_state:
            aklog_error(f'model id: {modelid} 官网上找不到对应rom包')
            return False

        romname = self.browser.get_value_by_xpath(romname_xpath)
        romurl = self.browser.get_element_visible('xpath', download_xpath).get_attribute('href')
        ret1 = self.visit_url(romurl)
        if ret1:
            aklog_info('准备从官网下载rom: {}文件...'.format(romname))
            self.browser.screen_shot_as_file(r'E:\\', '3333.png')
            ret = self.is_download_finished(romname)
            if ret:
                aklog_info('从官网下载rom: {} 成功'.format(romname))
                self.file_name = romname
                self.file_version = re.findall(r'\d+\.\d+\.\d+\.\d+', self.file_name)[0]
                GetReleaseVerFromAkuvox.nowver_downloadfile_dict[
                    self.now_version] = self.get_download_dir() + '\\' + romname
                return self.get_download_dir() + '\\' + romname
        aklog_error('从官网下载rom: {} 失败'.format(romname))
        return False

    def return_download_akuvox_release_file(self):
        if self.file_name:
            return self.get_download_dir() + '\\' + self.file_name
        return None

    def is_download_finished(self, romname):
        file = self.get_download_dir() + '\\' + romname
        for i in range(100):
            if os.path.exists(file):
                aklog_info(f'下载: {romname} -> {file} 完成')
                return True
            else:
                sleep(10)
        return False


def intercom_get_release_rom_file_from_akuvox_web(now_romversion):
    if now_romversion in GetReleaseVerFromAkuvox.nowver_downloadfile_dict:
        return GetReleaseVerFromAkuvox.nowver_downloadfile_dict.get(now_romversion)
    else:
        d = GetReleaseVerFromAkuvox(now_romversion)
        d.get_akuvox_release_firmware()
        d.browser_close_and_quit()
        return d.return_download_akuvox_release_file()


if __name__ == '__main__':
    ret = intercom_get_release_rom_file_from_akuvox_web('116.30.10.111')
    print('1111111111111~~~~~~~~~~~~~~~')
    print(ret)
