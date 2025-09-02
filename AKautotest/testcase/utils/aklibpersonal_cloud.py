import json
import os
import re
import time
import traceback

import requests

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]

from akcommon_define import *
from testcase.module.cloud.cloud_CBB import *
from selenium import webdriver


# test

def kaisa(s, k=3):  # 定义函数 接受一个字符串s 和 一个偏移量k
    '''app 用户名加密算法，凯撒加密改造，数字也做偏移'''
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    num = '0123456789'
    before = string.ascii_letters + num
    after = lower[k:] + lower[:k] + upper[k:] + upper[:k] + num[k:] + num[:k]
    table = ''.maketrans(before, after)
    return s.translate(table)


def md5(string):
    m = hashlib.md5()
    m.update(string.encode("utf8"))
    return m.hexdigest()


def md5_2(str):
    '''app密码加密采用2次md5加密'''
    str1 = md5(str)
    str2 = md5(str1)
    return str2


class get_supermanager:
    def __init__(self, version, cloud_data):
        self.version = version
        self.cloud_data = cloud_data
        self.super_header = login_header(self.cloud_data['url'], 0,
                                         self.cloud_data['supermanage'],
                                         self.cloud_data['password'],
                                         0)
        self.super_device_operation = device_operation_interface(self.cloud_data['url'],
                                                                 self.super_header)

    def get_distributor_id(self, accountname):
        ret = self.super_device_operation.get_web_server_path(self.super_device_operation.common_web_path,
                                                              'distributor/getAll?Key={}'.format(accountname),
                                                              {})
        for i in ret.get('data'):
            if i.get('LoginAccount') == accountname:
                return i.get('ID')

    def get_installer_id(self, installername):
        distributorid = self.get_distributor_id(self.cloud_data.get('distributor'))
        ret = self.super_device_operation.get_web_server_path(self.super_device_operation.common_web_path,
                                                              'manage/getAllInstaller?DisID={}'.format(distributorid),
                                                              {})
        for i in ret.get('data'):
            if i.get('Name') == installername:
                return i.get('ID')

    def get_rom_version_id(self, romversion):
        suburl = 'version/getVersionList?searchKey=Version&searchValue={}&row=10&page=1'.format(romversion)
        ret = self.super_device_operation.get_web_server_path(self.super_device_operation.common_web_path,
                                                              suburl,
                                                              {})
        if ret.get('data') and ret.get('data').get('row'):
            for i in ret.get('data').get('row'):
                if i.get('Version') == romversion:
                    return i.get('ID')

    def check_support_upgrade_model(self, model):
        """
        检查云上是否已经支持目标机型的升级
        """
        support_list = []
        ret = self.super_device_operation.get_web_server_path(self.super_device_operation.common_web_path,
                                                              'version/getAllModel')
        print(ret)
        for i in ret.get('data'):
            support_list.append(i.get('VersionName'))
            support_list.append(i.get('VersionName').lower())
        ret = model.lower() in support_list
        if not ret:
            aklog_info('云上当前不支持设备: {} 升级'.format(model))
            return False
        return ret

    def delete_version(self, romversion):
        """
        删除云上版本号.
        """
        vid = self.get_rom_version_id(romversion)
        if vid:
            self.super_device_operation.post_web_server_path(self.super_device_operation.common_web_path,
                                                             'version/deleteVersion',
                                                             {'ID': vid})

    def get_model_name(self, model_id):
        """通过model id获取云上的model name"""
        ret = self.super_device_operation.get_web_server_path(self.super_device_operation.common_web_path,
                                                              'version/getAllModel')
        if not ret:
            return False
        for i in ret.get('data'):
            if model_id == i.get('VersionNumber'):
                return i.get('VersionName')
        return False

    def add_version(self, romversion, url, distributor):
        """
        添加云上版本号.
        """
        para = {
            'Log': 'autotest_upload_{}'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
            'Version': romversion,
            'Url': url,
            'ManageID': self.get_distributor_id(distributor),
            'Manage': '',
            'AllManage': 0
        }
        ret = self.super_device_operation.post_web_server_path(self.super_device_operation.common_web_path,
                                                               'version/addVersion', para)

    def trigger_upgrade(self, mac, romversion, model, reset=False):
        """触发设备10秒后升级版本"""
        para = {
            'ProjectType': 1,
            'ID': '',
            'Model': model,
            'Version': romversion,
            'UpdateTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + 10)),
            'Device[0]': mac.upper(),
            'IsNeedReset': 1 if reset else 0,
            'InsID': self.get_installer_id(self.cloud_data.get('installer')),
            'UpgradeType': 0
        }
        param_put_reboot_process_flag(True)
        ret = self.super_device_operation.post_web_server_path(self.super_device_operation.common_web_path,
                                                               'upgrade/add', para)
        return ret


class get_distributor:

    def __init__(self, version, cloud_data):
        self.version = version
        self.cloud_data = cloud_data
        aklog_info('登录dis账号中...')
        self.distributor_header = login_header(self.cloud_data['url'], 0,
                                               self.cloud_data['distributor'],
                                               self.cloud_data['pwd_distributor'],
                                               0)
        self.distributor_device_operation = device_operation_interface(self.cloud_data['url'],
                                                                       self.distributor_header)
        self.distributor_account_operation = account_operation_interface(self.cloud_data['url'],
                                                                         self.distributor_header)

    def add_mac(self, mac):
        return self.distributor_device_operation.add_mac_dis(mac)

    def del_mac(self, mac):
        return self.distributor_device_operation.del_mac_from_dis(mac)

    def check_connect_status_with_mac(self, mac):
        ret = self.distributor_device_operation.get_web_server_path(
            self.distributor_device_operation.community_web_path,
            'device/getList?searchKey=MAC&searchValue={}&type=0&row=10&page=1'.format(
                mac.replace(':', '')), {})
        if ret:
            for i in ret.get('data').get('detail'):
                return i.get('Status') == "1"
            return False
        else:
            return False

    def set_confusion(self, Confusion=0):
        ins_name = self.cloud_data.get('installer')
        return self.distributor_account_operation.edit_ins_dis(ins_name, Confusion=Confusion)

    def del_device(self, mac):
        """distributor层级可以直接删除各层级的device"""
        params = {
            'searchKey': 'MAC',
            'searchValue': mac,
            'type': '0',
            'row': '10',
            'page': '1',
        }
        r = self.distributor_device_operation.get_web_server_path(self.distributor_device_operation.community_web_path,
                                                                  'device/getList', params)
        if r:
            if r.get('data').get('total') != '0':
                id = r.get('data').get('detail')[0].get('ID')
                data = {
                    'ID': id
                }
                r = self.distributor_device_operation.post_web_server_path(
                    self.distributor_device_operation.common_web_path, 'device/delete', data)
                if not r:
                    aklog_info('设备:{}下云失败'.format(mac))
                    return False
                else:
                    aklog_info('设备:{}下云成功'.format(mac))
                    return True
            else:
                aklog_info('社区云中不存在设备: {}'.format(mac))

                # 个人云中.
                params = {
                    'searchKey': 'MAC',
                    'searchValue': mac,
                    'row': '10',
                    'page': '1',
                }
                r = self.distributor_device_operation.get_web_server_path(
                    self.distributor_device_operation.single_web_path,
                    'device/getList', params)
                if r:
                    if r.get('data').get('total') == '0':
                        aklog_info('个人云中不存在设备: {}'.format(mac))
                    else:
                        id = r.get('data').get('detail')[0].get('ID')
                        data = {
                            'ID': id
                        }
                        r = self.distributor_device_operation.post_web_server_path(
                            self.distributor_device_operation.single_web_path, 'device/delete', data)
                        if not r:
                            aklog_info('设备:{}下云失败'.format(mac))
                            return False
                        else:
                            aklog_info('设备:{}下云成功'.format(mac))
                            return True


class get_installer:
    def __init__(self, version, cloud_data):
        aklog_info('登录installer账号中...')
        self.version = version
        self.cloud_data = cloud_data
        self.installer_header = login_header(self.cloud_data['url'], 0,
                                             self.cloud_data['installer'],
                                             self.cloud_data['pwd_installer'],
                                             1, self.cloud_data['community_name'])
        self.installer_device_operation = device_operation_interface(self.cloud_data['url'],
                                                                     self.installer_header)
        self.installer_account_operation = account_operation_interface(self.cloud_data['url'],
                                                                       self.installer_header)
        self.installer_firm_upgrade = firmware_operation_interface(self.cloud_data['url'],
                                                                   self.installer_header)
        self.installer_call_operation = call_operation_interface(self.cloud_data['url'],
                                                                 self.installer_header)

        self.personal_header = ''
        # self.comm_master_user_header = login_header(self.cloud_data['url'], 1,
        #                                             self.cloud_data['user_community'],
        #                                             self.cloud_data['pwd_community'],
        #                                             0)
        # self.user_timezone = timezone_operation_interface(self.cloud_data['url'],
        #                                                   self.comm_master_user_header)
        # self.user_call_operation = call_operation_interface(self.cloud_data['url'],
        #                                                     self.comm_master_user_header)
        # self.user_log_operation = log_operation_interface(self.cloud_data['url'],
        #                                                   self.comm_master_user_header)

    def add_device_to_community(self, mac, location, devtype):
        mac = mac.replace(':', '').replace('-', '')
        ret = self.installer_device_operation.add_device_to_public_area_com(mac, location, devtype,
                                                                            building_name_lst=[])
        self.set_device_security_relay_dtmf(mac)
        return ret

    def add_device_to_building(self, mac, location, dev_type, buildingname=None):
        mac = mac.replace(':', '').replace('-', '')
        if buildingname:
            ret = self.installer_device_operation.add_device_to_building_public_device_com(buildingname, mac, location,
                                                                                           int(dev_type))
        else:
            ret = self.installer_device_operation.add_device_to_building_public_device_com(
                self.cloud_data['building_name'], mac, location, int(dev_type))
        self.set_device_security_relay_dtmf(mac)
        return ret

    def add_device_to_apt(self, mac, location, dev_type, buildingname=None, email=None):
        mac = mac.replace(':', '').replace('-', '')
        if not email:
            ret = self.installer_device_operation.add_device_to_com_apt(self.cloud_data['user_community'], mac,
                                                                        location, int(dev_type))
        else:
            ret = self.installer_device_operation.add_device_to_com_apt(email, mac, location, int(dev_type))
        self.set_device_security_relay_dtmf(mac)
        return ret

    def del_device(self, mac):
        params = {
            'searchKey': 'MAC',
            'searchValue': mac,
            'ID': 'all',
            'SortField': '',
            'Sort': '',
            'row': '10',
            'page': '1',
        }
        r = self.installer_device_operation.get_web_server_path(self.installer_account_operation.community_web_path,
                                                                'device/getListForIns', params)
        if r:
            if r.get('data').get('total') != '0':
                id = r.get('data').get('detail')[0].get('ID')
                data = {
                    'ID[0]': id
                }
                r = self.installer_device_operation.post_web_server_path(
                    self.installer_device_operation.community_web_path, 'device/delete', data)
                if not r:
                    aklog_info('设备:{}下云失败'.format(mac))
                    return False
                else:
                    aklog_info('设备:{}下云成功'.format(mac))
                    return True
            else:
                aklog_info('社区云中不存在设备: {}'.format(mac))

    def get_pm_sip_account(self, pm_email):
        comid = self.installer_account_operation.get_community_info_com(self.cloud_data.get('community_name'))
        if not comid:
            aklog_error('不存在社区: {}'.format(self.cloud_data.get('community_name')))
            return False
        r = self.installer_account_operation.get_web_server_path(self.installer_account_operation.common_web_path,
                                                                 'account/getPmInfoList?CommunityID={}'.format(
                                                                     comid.get('ID')))
        for i in r.get('data'):
            if i.get('Email') == pm_email:
                return i.get('PersonalAccount')
        aklog_error('不存在物业管理员app账号: {}'.format(pm_email))
        return False

    def change_pm_app_status(self, appenable=True):
        """
        installer修改物业管理员的app账号开关.
        """
        if appenable:
            appenable = 1
        else:
            appenable = 0
        ret = self.installer_account_operation.get_pm_info_com(self.cloud_data.get('property'))
        if not ret:
            aklog_error('社区中没有添加物业管理员: {}'.format(self.cloud_data.get('property')))
            return False
        else:
            comid = self.installer_account_operation.get_community_info_com(self.cloud_data.get('community_name'))
            if not comid:
                aklog_error('不存在社区: {}'.format(self.cloud_data.get('community_name')))
                return False
            data = {
                'ID': ret.get('ID'),
                'CommunityID': comid.get('ID'),
                'AppStatus': appenable
            }
            r = self.installer_account_operation.post_web_server_path(self.installer_device_operation.common_web_path,
                                                                      'account/changePmAppStatus', data)

    def get_apt_sip_group_number(self, aptno='', buildingname=''):
        email = self.cloud_data.get('user_community')
        return self.installer_account_operation.get_euc_detail_by_euc_email_com(email)

    def get_sip_account_by_mac(self, mac):
        """返回社区下设备对应的mac账号"""
        aklog_info()
        r = self.installer_device_operation.get_web_server_path(self.installer_device_operation.community_web_path,
                                                                'device/getListForIns?ID=all&searchKey=MAC&searchValue=&SortField=&Sort=&row=40&page=1')
        if r:
            for i in r.get('data').get('detail'):
                if i.get('MAC') == mac.replace(':', '').replace('-', '').upper():
                    return i.get('SipAccount')
        aklog_error(f'获取Mac: {mac} 对应云账号失败!!!')

    def get_device_info(self, mac):
        """获取设备的信息"""
        param = {
            "searchValue": mac,
            "searchKey": "MAC",
            "ID": "all",
            "SortField": "",
            "Sort": "",
            "page": "1",
            "row": "10"
        }
        log = self.installer_account_operation.get_web_server_path(self.installer_device_operation.community_web_path,
                                                                   'device/getListForIns', para=param)
        if not log:
            return False
        for i in log.get('data').get('detail'):
            if i.get('MAC') == mac:
                return i
        return False

    def get_apt_info(self, apt_name):
        """返回房间的信息"""
        aklog_info()
        data = {"Status": "all", "Active": "all", "searchValue": apt_name, "searchKey": "RoomNumber", "SortField": "",
                "Sort": "", "Build": "community", "page": "1", "row": "10"}
        r = self.installer_device_operation.get_web_server_path(self.installer_device_operation.community_web_path,
                                                                'user/getRoomListByIns', para=data)
        if r:
            for i in r.get('data').get('detail'):
                if i.get('RoomNumber') == apt_name:
                    return i
        aklog_error(f'获取apt info: {apt_name} 失败!!!')

    def set_sequence_call(self, apt_name, first_seq=None, second_seq=None, third_seq=None, reset=False):
        """
        云上设置顺序呼叫
        indoor：传入设备mac ; eg:{'indoor':'A83311112222'}
        app：传入房间名 ; eg:{'app':self.cloud_data['apt_name']} 指定的是房间的主账号
        phone：传入手机号（福州手机号前面+0）; eg:{'phone':'018888888888'}
        """
        aklog_info()
        # 获取房间的uuid
        apt_uuid = self.get_apt_info(apt_name).get('UUID')

        def get_sequence_str(sequence_dict, apt_uuid):
            """返回参数所需的uuid"""
            if sequence_dict is None:
                return ''
            seq_list = []
            for key, value in sequence_dict.items():
                if key == 'indoor':
                    indoor_uuid = self.get_device_info(value).get('UUID')
                    seq_list.append(f'IndoorMonitor:{indoor_uuid}')
                elif key == 'app':
                    seq_list.append(f'APP:{apt_uuid}')
                elif key == 'phone':
                    seq_list.append(f'Phone:{apt_uuid}_{value}')
                else:
                    aklog_info('参数错误')
            if not seq_list:
                return ''
            return ';'.join(seq_list)

        if reset:
            calltype = 0
        else:
            calltype = 1
        first_seq = get_sequence_str(first_seq, apt_uuid)
        second_seq = get_sequence_str(second_seq, apt_uuid)
        third_seq = get_sequence_str(third_seq, apt_uuid)

        return self.set_apt(self.cloud_data.get('apt_number'), AptCallType=calltype, FirstSequenceCall=first_seq,
                            SecondSequenceCall=second_seq, ThirdSequenceCall=third_seq)

    def set_apt(self, aptno, buildingname=None, **kwargs):
        """
        【修改房间】.  edit room
        RoomNumber: APT名字
        RoomName: APT号码
        EnableIpDirect: 1: 同一个网络.   0: 不同网络
        WebRelayID: webrelay   0-50
        Floor:  楼层号   0-128
        """
        if not buildingname:
            buildingname = self.cloud_data['building_name']
        return self.installer_account_operation.edit_apt_com(buildingname, aptno, **kwargs)

    def del_apt(self, aptno, buildingname=None):
        if not buildingname:
            buildingname = self.cloud_data['building_name']
        return self.installer_account_operation.del_apt_com(buildingname, aptno)

    def add_apt(self, apt_no, name, email=None):
        buildingname = self.cloud_data['building_name']
        floor = str(apt_no)[0] if len(str(apt_no)) == 3 else str(apt_no)[:2]
        first_name = name.split(' ')[0]
        last_name = name.split(' ')[1]
        return self.installer_account_operation.add_APT_EUC_prenium_COM(buildingname, apt_no, name, floor,
                                                                        FirstName=first_name, LastName=last_name,
                                                                        Email=email)

    def set_device(self, mac, **kwargs):
        """
        【修改设备信息】
        Location： 设备名
        StairShow:   6.5.1版本
            1: 房间号
            2. 房间号, 室内机, app
            3: 室内机, app
        Relay: '[{"name":"Relay1","dtmf":"#","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}},{"name":"Relay2","dtmf":"0","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}},{"name":"Relay3","dtmf":"1","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}},{"name":"Relay4","dtmf":"2","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}}]'
        SecurityRelay: '[{"name":"Security Relay1","dtmf":"#","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}},{"name":"Security Relay2","dtmf":"0","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}}]'
        """
        self.installer_device_operation.edit_device_com(mac, **kwargs)
        if kwargs and 'SecurityRelay' in kwargs:
            pass
        else:
            self.set_device_security_relay_dtmf(mac)

    def set_device_security_relay_dtmf(self, mac, relay1='6', relay2='7', relay3='8', relay4='9'):
        """
        自动化修改设备的security relay dtmf, 避免云上查看doorlog信息因sr影响而失败.
        """
        try:
            ret = self.installer_device_operation.get_device_row_com(mac)
            if 'SecurityRelay' not in ret:
                return False
            else:
                sr = ret.get('SecurityRelay')
                list1 = [relay1, relay2, relay3, relay4]

                def test(a):
                    ret = list1[0]
                    del list1[0]
                    return '"dtmf":"{}"'.format(ret)

                sr = re.sub('"dtmf":"."', test, sr)
                self.installer_device_operation.edit_device_com(mac, SecurityRelay=sr)
                return ret
        except:
            aklog_error('设置security relay dtmf失败')

    def remote_control_reboot(self, mac):
        param_put_reboot_process_flag(True)
        return self.installer_device_operation.device_reboot_COM(mac)

    def remote_control_reset(self, mac):
        param_put_reboot_process_flag(True)
        return self.installer_device_operation.device_reset_COM(mac)

    def remote_control_autop(self, mac, configlist):
        if type(configlist) == str:
            config = configlist
        else:
            config = '\n'.join(configlist)
        return self.installer_device_operation.device_autop_COM(mac, config, sip_type=1)

    def remote_control_once_autop(self, mac, configlist):
        if type(configlist) == str:
            config = configlist
        else:
            config = '\n'.join(configlist)
        return self.installer_device_operation.device_once_autop_COM(mac, config)

    def remote_control_set_transport(self, mac, transport='UDP'):
        transdict = {
            'udp': 0, 'tcp': 1, 'tls': 2
        }
        tport = str(transdict.get(transport.lower(), transport)) if type(transport) == str else transport,
        return self.installer_device_operation.device_autop_COM(mac, '', sip_type=tport)

    def remote_control_web(self, mac):
        try:
            chrome_driver_path = g_chrome_driver_path.replace('\\', '/')
            r = self.installer_device_operation.device_remote_COM(mac)
            if not r:
                aklog_error('云上没有设备: {}'.format(mac))
                return False
            remoteurl = r.get("url")
            aklog_info('尝试访问远程url: {}'.format(remoteurl))
            options = webdriver.ChromeOptions()
            options.add_argument('--ignore-certificate-errors')
            chrome_service = Service(chrome_driver_path)
            chrome_service.command_line_args()
            chrome_service.start()
            driver = webdriver.Chrome(options, chrome_service)
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(5)
            for test_count in range(2):
                driver.get(remoteurl)
                for i in range(3):
                    driver.refresh()
                    try:
                        try:
                            if driver.find_element('xpath', './/*[@class="ak-logout-label" or @id="tPageLogOut"]'):
                                driver.quit()
                                return True
                        except:
                            pass
                        eles = driver.find_elements('xpath', './/input')
                        if eles:
                            eles[0].send_keys('admin')
                            eles[1].send_keys('Aa12345678')
                            driver.find_element('xpath', './/*[@id="Login" or @class="ak-homepage-btn"]').click()
                            driver.find_element('xpath', './/*[@class="ak-logout-label" or @id="tPageLogOut"]')
                            driver.quit()
                            return True
                        else:
                            continue
                    except:
                        print(traceback.format_exc())
                        time.sleep(30)
            ret = driver.get_screenshot_as_base64()
            param_append_screenshots_imgs(ret)
            print(driver.page_source)
            driver.quit()
            return False
        except:
            try:
                print(driver.page_source)
                driver.quit()
            except:
                pass
            return False

    def set_community_detail(self, **kwargs):
        """
        【设置】: 物业管理员设置社区信息
        地址： Street, City, Location
        AptPinType: PIN模式
            0-> pin,
            1->APT+pin
        """
        community = self.cloud_data.get('community_name')
        self.installer_account_operation.edit_community_com(community, **kwargs)

    def set_apt_enable_ip_direct(self, euc_email, EnableIpDirect):
        '''
        设置房间走sip或ip
        eus_email：传入房间主人的邮箱地址
        EnableIpDirect：0，走sip；1，走ip
        '''
        return self.installer_call_operation.set_sip_ip_euc_by_com(euc_email, EnableIpDirect)

    def get_community_id(self):
        """获取社区的id"""
        para = {
            'ProjectType': '1'
        }
        ret = self.installer_device_operation.get_web_server_path(self.installer_device_operation.common_web_path,
                                                                  'upgrade/getSitesByIns', para)
        if not ret:
            return False
        for i in ret.get('data'):
            if i.get('Name') == self.cloud_data['community_name']:
                return i.get('ID')
        return False

    def trigger_upgrade(self, mac, romversion, model, reset=False):
        """触发设备10秒后升级版本"""
        para = {
            'ID': '',
            'Model': model,
            'Version': romversion,
            'UpdateTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + 10)),
            'Device[0]': mac.upper(),
            'changeLog': romversion,
            'updateTimeType': 1,
            'IsNeedReset': 1 if reset else 0,
            'ProjectType': 1,
            'ProjectId': self.get_community_id(),
            'UpgradeType': 1
        }
        ret = self.installer_device_operation.post_web_server_path(self.installer_device_operation.common_web_path,
                                                                   'upgrade/addByIns', para)
        return ret

    # 三方设备, 用于如室内机三方摄像头测试
    def get_third_cam(self, location):
        aklog_info()
        para = {
            "searchKey": "Location",
            "searchValue": location,
            "ID": "community",
            "SortField": "",
            "Sort": "",
            "row": "10",
            "page": "1"
        }
        r = self.installer_device_operation.get_web_server_path(self.installer_device_operation.community_web_path,
                                                                'thirdPartCamera/getListForIns', para)
        if r.get('data').get('total') == '0':
            aklog_info(f'不存在location为{location}的摄像头')
            return False
        return r.get('data').get('detail')[0]

    def add_third_cam_to_building(self, locationname, rtsp_ip, link_device=False, link_mac='',
                                  allow_enduser_monitor=True):
        """
        rtsp_ip: 输入ip, 组成rtspurl.
        link_device: 是否绑定门口机
        """
        if link_device:
            link_device = 1
        else:
            link_device = 0

        ret = self.installer_account_operation.get_building_info_com(self.cloud_data.get('building_name'))
        if not ret.get('ID'):
            aklog_error('未找到楼: {}'.format(self.cloud_data.get('building_name')))
            return False
        else:
            buildid = ret.get('ID')
        # 用第二路rtsp流，区别通话中的第一路流，log比较好区分
        data = {'Location': locationname,
                'RtspAddress': 'rtsp://{}/live/ch00_1'.format(rtsp_ip),
                'RtspUserName': 'admin',
                'RtspPwd': 'Aa12345678',
                'IsLinkDevice': link_device,
                'MAC': link_mac,
                'Grade': 2,
                'UnitID': buildid,
                'PersonalAccountUUID': '',
                # 'type': 'thirdPartyDevice',
                'AllowEndUserMonitor': 1 if allow_enduser_monitor else 0,
                'MonitoringPlatform': 1}
        return self.installer_device_operation.post_web_server_path(self.installer_device_operation.community_web_path,
                                                                    'thirdPartCamera/add', data)

    def edit_third_cam_in_building(self, location, **kwargs):
        """
        {'ID': '740',
         'UUID': 't8-0c63860065fe11f0964800163e0605c8',
         'ProjectUUID': 'na-3368e4660e5011edb5fa00163e0605c8',
         'UnitID': '3656',
         'PersonalAccountUUID': '',
         'Grade': '2',
         'Location': '1111',
         'RtspAddress': 'rtsp://192.168.88.254/live/ch00_1',
         'RtspUserName': 'admin',
         'RtspPwd': 'Aa12345678',
         'MAC': 'A81325011701',
         'VideoPt': '96',
         'VideoType': 'H264',
         'CreateTime': '07-21-2025 14:43:45',
         'UpdateTime': '07-21-2025 14:43:45',
         'VideoFmtp': '',
         'isEcToUc': '0',
         'AllowEndUserMonitor': '0',
         'MonitoringPlatform': '1',
         'UnitName': '1号楼',
         'RoomName': '--',
         'LevelID': '3656',
         'LinkDevice': 'slave_door',
         'IsLinkDevice': 1}
        """
        aklog_info()
        r = self.get_third_cam(location)
        if not r:
            return False
        for key, value in r.items():
            if key in kwargs:
                r[key] = kwargs[key]
        return self.installer_device_operation.post_web_server_path(self.installer_device_operation.community_web_path,
                                                                    'thirdPartCamera/edit', r)

    def del_third_cam_in_building(self, location):
        ret = self.installer_account_operation.get_building_info_com(self.cloud_data.get('building_name'))
        if not ret.get('ID'):
            aklog_error('未找到楼: {}'.format(self.cloud_data.get('building_name')))
            return False
        else:
            buildid = ret.get('ID')
        r = self.installer_account_operation.get_web_server_path(self.installer_device_operation.community_web_path,
                                                                 'thirdPartCamera/getListForIns?searchKey=Location&searchValue=&ID={}&SortField=&Sort=&row=10&page=1&Build={}&type=thirdPartyDevice'.format(
                                                                     buildid, buildid))
        uuidlist = []
        for i in r.get('data').get('row'):
            if i.get('Location') == location:
                uuidlist.append(i.get('UUID'))
        if not uuidlist:
            aklog_info('楼栋中不存在三方摄像头: {}'.format(location))
            return False
        else:
            ucount = 0
            data = {}
            for uuid in uuidlist:
                data['UUID[{}]'.format(ucount)] = uuid
            r = self.installer_account_operation.post_web_server_path(
                self.installer_device_operation.community_web_path,
                'thirdPartCamera/delete',
                data)

    # 个人云接口
    def personal_check_token_alive(self):
        if not self.personal_header:
            # 如果为空,installer重新登录了
            self.personal_header = login_header(self.cloud_data['url'], 0,
                                                self.cloud_data['installer'],
                                                self.cloud_data['pwd_installer'],
                                                0)
        # 如果不为空，检查返回是否有返回结果，有的话就不用重新登录
        try:
            installer_device_operation = device_operation_interface(self.cloud_data['url'], self.personal_header)
            email = self.cloud_data.get('personMasterEmail')
            rsp = installer_device_operation.get_eus_detail_sin(email, searchKey="Email")
            if type(rsp.get('total')) == int:
                ret = True
            else:
                ret = False
        except:
            ret = False
        finally:
            if not ret:
                self.personal_header = login_header(self.cloud_data['url'], 0,
                                                    self.cloud_data['installer'],
                                                    self.cloud_data['pwd_installer'],
                                                    0)

    def add_device_to_personal(self, mac, location, devtype):
        mac = mac.replace(':', '').replace('-', '')
        self.personal_check_token_alive()
        installer_device_operation = device_operation_interface(self.cloud_data['url'], self.personal_header)
        return installer_device_operation.add_device_to_sin(mac, location, self.cloud_data.get('personMasterEmail'),
                                                            devtype)

    def add_mac_to_personal(self, mac):
        self.personal_check_token_alive()
        installer_device_operation = device_operation_interface(self.cloud_data['url'], self.personal_header)
        data = {
            'MAC': mac,
            'ID': 'undefined',
        }
        r = installer_device_operation.post_web_server_path(self.installer_device_operation.single_web_path,
                                                            'macLibrary/add', data=data)
        if r:
            aklog_info('添加到个人云Mac库成功')
            return True
        else:
            aklog_error('添加到个人云Mac库失败')
            return False

    def personal_get_resident_info(self, email=None):
        if email is None:
            email = self.cloud_data.get('personMasterEmail')
        self.personal_check_token_alive()
        installer_device_operation = device_operation_interface(self.cloud_data['url'], self.personal_header)
        return installer_device_operation.get_eus_detail_sin(email, searchKey="Email")

    def personal_get_device_info(self, mac):
        """获取设备信息"""
        self.personal_check_token_alive()
        param = {
            "searchKey": "MAC",
            "searchValue": mac,
            "row": "10",
            "page": "1"
        }
        installer_device_operation = device_operation_interface(self.cloud_data['url'], self.personal_header)
        return \
            installer_device_operation.get_web_server_path(installer_device_operation.single_web_path, 'device/getList',
                                                           param).get('data').get('detail')[0]

    def personal_set_time(self, zone):
        self.personal_check_token_alive()
        installer_timezone = timezone_operation_interface(self.cloud_data['url'], self.personal_header)
        email = self.cloud_data.get('personMasterEmail')
        return installer_timezone.set_timezone_SIN(email, TimeZone=zone)

    def personal_set_call(self, EnableIpDirect=0):
        """
        个人云设置同一个网络/不同网络
        """
        self.personal_check_token_alive()
        installer_account_operation = account_operation_interface(self.cloud_data['url'], self.personal_header)
        r = installer_account_operation.edit_eus_sin(self.cloud_data.get('personMasterEmail'),
                                                     EnableIpDirect=EnableIpDirect)
        if r:
            return True

    def personal_set_device(self, mac, **kwargs):
        """
        个人云修改设置的location.
        只支持location
        """
        self.personal_check_token_alive()
        installer_device_operation = device_operation_interface(self.cloud_data['url'], self.personal_header)
        r = installer_device_operation.edit_device_sin(self.cloud_data.get('personMasterEmail'), mac, **kwargs)
        if r:
            return True

    def personal_set_video_record(self, enable=False):
        """设置视频录制"""
        self.personal_check_token_alive()
        uuid = self.personal_get_resident_info()['UUID']
        param = {
            "isEnable": enable,
            "single": uuid,
            "planType": "subscription",
            "storageDays": 30,
            "storedDevicesNum": "unlimited",
            "devices": {
                "isAll": True,
                "list": []
            },
            "isEnableCallAudio": True
        }
        installer_device_operation = device_operation_interface(self.cloud_data['url'], self.personal_header)
        project_uuid = installer_device_operation.get_web_server_path(installer_device_operation.common_web_path,
                                                                      'manage/getInsInfo').get('data').get('UUID')
        header = self.personal_header
        header['X-Project'] = project_uuid
        return installer_device_operation.post_web_server_path(
            'https://backend.test84.akuvox.com/web-server/v4/web/single', 'videoStorage/ins/update', param,
            headers=header)


class get_proper:
    def __init__(self, version, cloud_data):
        aklog_info('登录property账号中...')
        self.version = version
        self.cloud_data = cloud_data
        self.pm_header = login_header(self.cloud_data['url'], 0,
                                      self.cloud_data['property'],
                                      self.cloud_data['pwd_property'],
                                      2, self.cloud_data['community_name'])
        self.pm_message = message_operation_interface(self.cloud_data['url'], self.pm_header)
        self.pm_timezone = timezone_operation_interface(self.cloud_data['url'], self.pm_header)
        self.pm_key = key_operation_interface_COM(self.cloud_data['url'], self.pm_header)
        self.pm_log_operation = log_operation_interface(self.cloud_data['url'], self.pm_header)
        self.pm_account = account_operation_interface(self.cloud_data['url'], self.pm_header)
        self.pm_call_operation = call_operation_interface(self.cloud_data['url'], self.pm_header)

    def trig_relay(self, state=False, mac=None):
        if mac is None:
            mac = self.cloud_data['masterMAC']
        device_uuid = self.get_device_info(mac).get('UUID')
        param = {
            'Type': '1' if state else '0',
            'Devices': f'[{{"device": "{device_uuid}", "relay": [1, 2, 3, 4], "securityRelay": [1, 2]}}]',
            'ActionType': '1'
        }
        self.pm_key.post_web_server_path(self.pm_key.community_web_path,
                                         'device/emergencyAction', param)

    def add_access_group(self, name, type, mac=None, **kwargs):
        # 处理跨天的情况
        starttime = kwargs.get('StartTime')
        stoptime = kwargs.get('StopTime')
        curtime = time.strftime("%H:%M:%S", time.localtime(time.time()))
        if kwargs.get('StartTime') and kwargs.get('StopTime'):
            if int(starttime.split(':')[0]) > int(stoptime.split(':')[0]):
                if int(curtime.split(':')[0]) > int(stoptime.split(':')[0]):
                    stoptime = '23:59:59'
                else:
                    starttime = '00:00:00'
        if mac is None:
            mac = self.cloud_data.get("masterMAC")
        data = {
            'Name': name,
            'SchedulerType': str(type),
            'StartDay': kwargs.get('StartDay') or time.strftime('%Y-%m-%d'),
            'StopDay': kwargs.get('StopDay') or time.strftime('%Y-%m-%d', time.localtime(time.time() + 86400)),
            'StartTime': starttime or '00:00:00',
            'StopTime': stoptime or '23:59:59',
            'DateFlag': kwargs.get('DateFlag') or '0;1;2;3;4;5;6',
            'Device[0][MAC]': mac,
            'Device[0][Relay]': '0;1;2;3',
            'ID': '',
        }
        if type == 1:
            # 每天
            data['StartDay'] = ''
            data['StopDay'] = ''
            data['DateFlag'] = ''
        elif type == 2:
            # 每周
            data['StartDay'] = ''
            data['StopDay'] = ''
        else:
            # 不重复
            data['SchedulerType'] = '0'
            data['DateFlag'] = ''
        self.pm_key.add_access_group_COM(data)

    def edit_access_group(self, name, type, mac=None, **kwargs):
        """编辑云权限组"""
        starttime = kwargs.get('StartTime')
        stoptime = kwargs.get('StopTime')
        curtime = time.strftime("%H:%M:%S", time.localtime(time.time()))
        if kwargs.get('StartTime') and kwargs.get('StopTime'):
            if int(starttime.split(':')[0]) > int(stoptime.split(':')[0]):
                if int(curtime.split(':')[0]) > int(stoptime.split(':')[0]):
                    stoptime = '23:59:59'
                else:
                    starttime = '00:00:00'
        if mac is None:
            mac = self.cloud_data.get("masterMAC")
        data = {
            'ID': '',
            'Name': name,
            'SchedulerType': str(type),
            'StartDay': kwargs.get('StartDay') or time.strftime('%Y-%m-%d'),
            'StopDay': kwargs.get('StopDay') or time.strftime('%Y-%m-%d', time.localtime(time.time() + 86400)),
            'StartTime': starttime or '00:00:00',
            'StopTime': stoptime or '23:59:59',
            'DateFlag': kwargs.get('DateFlag') or '0;1;2;3;4;5;6',
            'Device[0][MAC]': mac,
            'Device[0][Relay]': '0;1;2;3',
        }
        if type == 1:
            # 每天
            data['StartDay'] = '1899-11-30'
            data['StopDay'] = '1899-11-30'
            data['DateFlag'] = ''
        elif type == 2:
            # 每周
            data['StartDay'] = '1899-11-30'
            data['StopDay'] = '1899-11-30'
        else:
            # 不重复
            data['SchedulerType'] = '0'
            data['DateFlag'] = ''
        return self.pm_key.edit_access_group_COM(name, data)

    def get_all_access_group(self):
        return self.pm_key.get_all_access_group_COM()

    def get_access_id_by_name(self, schedulename):
        ret = self.get_all_access_group()
        if ret:
            for i in ret:
                if i.get('Name') == schedulename:
                    return i.get('ID')
        return ''

    def del_access_group(self, name):
        return self.pm_key.del_access_group_COM(name)

    def edit_resident_access_group(self, *access_group):
        """传入schedule的名字"""
        return self.pm_key.edit_user_access_group_COM(self.cloud_data.get('user_community'), *access_group)

    def remove_access_people(self, schedulename, people):
        """
        权限组--> 移除人员
        """
        return self.pm_key.edit_access_group_remove_personal_COM(schedulename, people)

    def add_access_people(self, schedulename, people):
        """
        权限组--> 添加人员(对权限组进行操作，如果想对住户进行操作用edit_resident_access_group)
        """
        self.pm_key.edit_access_group_add_people_COM(schedulename, people)

    def add_tmp_key(self, name, type=1, bind_apt=True, **kwargs):
        aklog_info()
        """
        type:  1:每天, 2:每周,3:不重复,
        并返回添加的tmp key密码值
        默认过期时间为第二天。
        bind_apt: 创建tmpkey时, 是否指定楼栋+房间
        """
        if bind_apt:
            self.department_id = ''
            self.people_id = ''
            self.pm_key.get_building_id_room_id(self.cloud_data.get('building_name'), self.cloud_data.get('apt_number'))
            builid, aptid = [self.pm_key.building_id, self.pm_key.room_id]
        else:
            builid, aptid = ['', '']
        data = {
            'Build': builid,
            'Room': aptid,
            'Description': name,
            'BeginTime': kwargs.get('BeginTime') or '{} 00:00:00'.format(time.strftime('%Y-%m-%d')),
            'ExpireTime': kwargs.get('ExpireTime') or '{} 23:59:59'.format(
                time.strftime('%Y-%m-%d', time.localtime(time.time() + 86400))),
            'StartTime': kwargs.get('StartTime') or '00:00:00',
            'StopTime': kwargs.get('StopTime') or '23:59:59',
            'Allow': kwargs.get('Allow') or '1000',
            'MAC[0][MAC]': self.cloud_data.get('masterMAC'),
            'MAC[0][Relay]': '0;1;2;3',
            'IDNumber': '',
            'Delivery': '',
            'SchedulerType': type,
            'DateFlag': kwargs.get('DateFlag') or '0;1;2;3;4;5;6',
            'OfficeUserID': '',
        }
        if type == 1:
            # 每天
            data['DateFlag'] = ''
            data['Allow'] = ''
        elif type == 2:
            # 每周
            data['Allow'] = ''
            data['ExpireTime'] = ''
        else:
            # 不重复
            data['SchedulerType'] = '3'
            data['DateFlag'] = ''
            data['StartTime'] = ''
            data['StopTime'] = ''
        self.pm_key.building_id = ''
        self.pm_key.room_id = ''
        self.pm_key.add_tmp_key_COM(data)
        time.sleep(3)
        return self.pm_key.get_latest_tmp_key_COM()

    def del_tmp_key(self, code):
        return self.pm_key.del_tmp_key_COM(code)

    def add_delivery(self, name, pin, card, specify_access=None):
        # 指定楼栋添加快递
        if specify_access:
            return self.pm_key.add_delivery_key_COM(name, pin, card,
                                                    specify_access,
                                                    Floor=[""],
                                                    Build=self.pm_key.get_building_id(
                                                        self.cloud_data.get('building_name')))
        else:
            return self.pm_key.add_delivery_key_COM(name, pin, card,
                                                    'Resident-Building {}'.format(self.cloud_data.get('building_name')),
                                                    Floor=[""],
                                                    Build=self.pm_key.get_building_id(
                                                        self.cloud_data.get('building_name')))

    def edit_delivery(self, name, aftpin, aftcard, aftname=None):
        if aftname:
            return self.pm_key.edit_delivery_key_COM(name, PinCode=aftpin, CardCode=aftcard, Name=aftname)
        else:
            return self.pm_key.edit_delivery_key_COM(name, PinCode=aftpin, CardCode=aftcard)

    def del_delivery(self, name):
        return self.pm_key.del_delivery_key_COM(name)

    def add_staff(self, name, card, schedule=None, pin=''):
        if schedule:
            # return self.pm_key.add_staff_key_COM(name, card, schedule, Floor=[""], Build=[""])
            ret = self.pm_key.add_staff_key_COM(name, card, pin, schedule)
            return ret
        else:
            # return self.pm_key.add_staff_key_COM(name, card,'Resident-Building {}'.format(self.cloud_data.get('building_name')), Floor=[""], Build=[""])
            ret = self.pm_key.add_staff_key_COM(name, card, pin,
                                                'Resident-Building {}'.format(self.cloud_data.get('building_name')))
            return ret

    def edit_staff(self, name, aftcard):
        return self.pm_key.edit_staff_key_COM(name, CardCode=aftcard)

    def del_staff(self, name):
        return self.pm_key.del_staff_auth_COM(name)

    def add_pin(self, pin):
        return self.pm_key.add_user_pin_COM(self.cloud_data.get('user_community'), pin)

    def edit_pin(self, oldpin, newpin):
        return self.pm_key.edit_user_pin_COM(self.cloud_data.get('user_community'), oldpin, newpin)

    def del_pin(self, pin):
        return self.pm_key.del_user_pin_COM(self.cloud_data.get('user_community'), pin)

    def add_card(self, card):
        return self.pm_key.add_user_rf_COM(self.cloud_data.get('user_community'), card)

    def edit_card(self, oldcard, newcard):
        return self.pm_key.edit_user_rf_COM(self.cloud_data.get('user_community'), oldcard, newcard)

    def del_card(self, card):
        return self.pm_key.del_user_rf_COM(self.cloud_data.get('user_community'), card)

    def add_face(self, facefile):
        aklog_info()
        return self.pm_key.add_user_face_COM(self.cloud_data.get('user_community'), facefile)

    def del_face(self):
        aklog_info()
        return self.pm_key.del_user_face_COM(self.cloud_data.get('user_community'))

    def clear_card(self):
        try:
            idlist = []
            r = self.pm_key.get_web_server_path(self.pm_key.community_web_path,
                                                'key/getRfCardLibraryList?Building=all&Apt=all&Type=all&searchKey=RF+Card&searchValue=&row=40&page=1')
            for i in r.get('data').get('detail'):
                idlist.append(i.get('ID'))
            if not idlist:
                aklog_info('社区里没有门禁卡')
                return True
            r = self.pm_key.post_web_server_path(self.pm_key.community_web_path, 'key/delRfCardLibrary',
                                                 {'ID': ';'.join(idlist)})
            if r:
                aklog_info('清空社区下的card成功!')
                return True
        except:
            aklog_error('清空社区下的card异常失败!')
            return False

    def clear_pin(self):
        try:
            idlist = []
            r = self.pm_key.get_web_server_path(self.pm_key.community_web_path,
                                                'key/getPinLibraryList?Building=all&Apt=all&Type=all&searchKey=PIN&searchValue=&row=40&page=1')
            for i in r.get('data').get('detail'):
                idlist.append(i.get('ID'))
            if not idlist:
                aklog_info('社区里没有pin')
                return True
            r = self.pm_key.post_web_server_path(self.pm_key.community_web_path, 'key/delPinLibrary',
                                                 {'ID': ';'.join(idlist)})
            if r:
                aklog_info('清空社区下的pin')
                return True
        except:
            aklog_error('清空社区下的PIN异常失败')
            print(traceback.format_exc())
            return False

    def get_resident_info(self, email):
        return self.pm_message.get_personal_info_pm(email)

    def get_resident_info_by_pm(self, email):
        """
        https://test84.akuvox.com/web-server/v3/web/community/user/getListByNewPm?Build=all&Room=all&Role=all&Active=all&Status=all&searchKey=Name&searchValue=&Sort=&SortField=&row=10&page=1&_t=1744618188067
        """
        param = {
            'Build': 'all',
            'Room': 'all',
            'Role': 'all',
            'Active': 'all',
            'Status': 'all',
            'searchKey': '',
            'searchValue': '',
            'Sort': '',
            'SortField': '',
            'row': '10',
            'page': '1',
        }
        log = self.pm_key.get_web_server_path(self.pm_key.community_web_path, 'user/getListByNewPm', param).get('data')
        if log.get('total') < 1:
            aklog_info('可能不存在住户')
            return False
        for i in log.get('row'):
            if i.get('Email') == email:
                aklog_info('*' * 5 + 'resident info：' + str(i))
                return i
        aklog_info(f'没有找到符合email：{email}的住户')
        return False

    def edit_resident_info(self, email, aft_name=None, **kwargs):
        """
        UnitID: 3656
        RoomID: 74067
        FirstName: 801
        LastName: 主人1222
        Email: youjianan001@163.com
        PhoneCode: 86
        MobileNumber: 15759946369
        Phone: 015759946369
        Phone2:
        Phone3:
        DepartmentID:
        Role: 20
        IsMulti: 0
        Remark:
        ID: 80953
        """
        self.pm_key.get_building_id_room_id(self.cloud_data.get('building_name'), self.cloud_data.get('apt_number'))
        builid, aptid = [self.pm_key.building_id, self.pm_key.room_id]
        resident_info = self.get_resident_info_by_pm(email)
        if not resident_info:
            aklog_info('没有找到符合条件的住户')
            return False
        if aft_name is not None:
            firstname = aft_name.split(' ')[0]
            lastname = aft_name.split(' ')[1]
        else:
            firstname = resident_info.get('Name').split(' ')[0]
            lastname = resident_info.get('Name').split(' ')[1]

        phone = ''
        if kwargs.get('Phone'):
            phone = kwargs.get('Phone')
        elif resident_info.get('MobileNumber'):
            phone = '0' + resident_info.get('MobileNumber')
        param = {
            'UnitID': builid,
            'RoomID': aptid,
            'FirstName': firstname,
            'LastName': lastname,
            'Email': kwargs.get('Email') or resident_info.get('Email'),
            'PhoneCode': '86',
            'MobileNumber': kwargs.get('MobileNumber') or resident_info.get('MobileNumber'),
            'Phone': phone,
            'Phone2': kwargs.get('Phone2') or '',
            'Phone3': kwargs.get('Phone3') or '',
            'DepartmentID': kwargs.get('DepartmentID') or '',
            'Role': resident_info.get('Role'),
            'IsMulti': '0',
            'Remark': '',
            'ID': resident_info.get('ID')
        }
        self.pm_key.post_web_server_path(self.pm_key.community_web_path, 'user/editForPm', param)

    def edit_resident_access_floor(self, email, floor=[]):
        """下发住户可达楼层"""
        aklog_info()
        info = self.get_resident_info_by_pm(email)
        resident_id = info.get('ID')
        building_uuid = self.get_building_info(self.cloud_data['building_name']).get('UUID')
        if type(floor) == list:
            floor = ';'.join(floor)
        para = {
            'ID': resident_id,
            'AccessFloor[Access][0][Floor]': floor,
            'AccessFloor[Access][0][BuildingUUID]': building_uuid,
            'AccessFloor[Floor]': '',
            'AccessFloor[IsAll]': '0'
        }
        return self.pm_key.post_web_server_path(self.pm_key.community_web_path, 'user/editAccessFloor', para)

    def get_door_log(self):
        aklog_info()
        ret = self.pm_log_operation.get_latest_pm_door_logs()
        if ret:
            if ret.get('Response') == '1':
                ret['Response'] = 'Failed'
            elif ret.get('Response') == '0':
                ret['Response'] = 'Success'
            ret['RoomNum'] = ret['RoomNum'].split(' ')[0]  # 处理成不带floor no
            if 'PicName' in ret:
                ret['PicName'] = ret['PicName'].replace('_DD_', '_DoorDev_')
            return ret
        else:
            return {}

    def get_door_log2(self):
        aklog_info()
        ret = self.pm_log_operation.get_all_pm_door_logs()[1]
        if ret:
            if ret.get('Response') == '1':
                ret['Response'] = 'Failed'
            elif ret.get('Response') == '0':
                ret['Response'] = 'Success'
            ret['RoomNum'] = ret['RoomNum'].split(' ')[0]  # 处理成不带floor no
            if 'PicName' in ret:
                ret['PicName'] = ret['PicName'].replace('_DD_', '_DoorDev_')
            return ret
        else:
            return {}

    def get_call_log(self):
        aklog_info()
        return self.pm_log_operation.get_latest_pm_call_history()

    def get_motion_log(self):
        aklog_info()
        ret = self.pm_log_operation.get_latest_pm_motion()
        if not ret:
            return {}
        else:
            if 'PicName' in ret:
                ret['PicName'] = ret['PicName'].replace('_MD_', '_MotionDev_')
            return ret

    def get_alarm_log(self):
        aklog_info()
        return self.pm_log_operation.get_latest_pm_alarm()

    def get_arming_log(self):
        aklog_info()
        return self.pm_log_operation.get_latest_pm_arming()

    def get_community_detail(self):
        return self.pm_key.get_web_server_path(self.pm_key.community_web_path, 'communityData/getDetailForPM')

    def set_community_detail(self, **kwargs):
        ret = self.get_community_detail()
        if not ret:
            aklog_error('修改社区信息失败')
            return False
        else:
            curdata = ret.get('data')
            postkey = ['Location', 'Street', 'City', 'States', 'Country', 'PostalCode', 'EnableUserPin', 'AptPinType',
                       'DevOfflineNotify', 'EnableSIMWarning', 'PhoneCode', 'MobileNumber', 'LimitCreatePin',
                       'TriggerAction']
            postdata = {}
            for key in postkey:
                postdata[key] = curdata.get(key)
            postdata.update(kwargs)
            self.pm_key.post_web_server_path(self.pm_key.community_web_path, 'project/editProjectInfo', postdata)

    def set_time(self, zone, format):
        self.pm_timezone.set_timezone_PM_COM(zone, format)

    def set_face(self, enable=0):
        return self.pm_key.post_web_server_path(self.pm_key.community_web_path, 'communityData/setVisitor',
                                                {'IDCardVerification': 1, 'FaceEnrollment': enable})

    def set_motion(self, type, time):
        return self.pm_key.post_web_server_path(self.pm_key.community_web_path, 'communityData/setMotion',
                                                {'EnableMotion': type, 'MotionTime': time})

    def set_emergency_info(self, triggerdoor=False, send_noti=False, door=[], mac=None):
        """设置--紧急情况设置"""
        if mac:
            info = self.get_device_info(mac)
            if not info:
                aklog_info(f'不存在{mac}的设备')
                return False
            door_list = [i.replace(' ', '').replace('Relay', '') for i in door]
            relay_dict = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
            doorgroup = [
                {"Device": info.get('UUID'), "Relay": [relay_dict.get(i) for i in door_list], "SecurityRelay": []}]
        else:
            doorgroup = []
        param = {
            'TriggerAction': '1' if triggerdoor else '0',
            'IsSendEmergencyNotifications': '1' if send_noti else '0',
            'EmergencyDoorGroup': doorgroup,
            'IsAllEmergencyDoor': '1'
        }
        return self.pm_key.post_web_server_path(self.pm_key.community_web_path, 'project/editProjectEmergencyInfo',
                                                param)

    def set_apt(self, aptno, **kwargs):
        """物业管理员修改房间信息
        AptName: 房间名
        EnableIpDirect: 0: 不同网络下  1: 相同网络下.
        CallType: 呼叫方式   0: 小睿和室内机
        WebRelayID: webrelay
        """
        apt_no = aptno
        building_name = self.cloud_data.get('building_name')
        floor = str(apt_no)[0] if len(str(apt_no)) == 3 else str(apt_no)[:2]
        return self.pm_call_operation.set_call_setting_by_pm(building_name, apt_no, floor, **kwargs)

    def set_device(self, mac, **kwargs):
        """
        【修改设备信息】
        Location： 设备名
        StairShow:   6.5.1版本
            1: 房间号
            2. 房间号, 室内机, app
            3: 室内机, app
        Relay: '[{"name":"Relay1","dtmf":"#","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}},{"name":"Relay2","dtmf":"0","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}},{"name":"Relay3","dtmf":"1","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}},{"name":"Relay4","dtmf":"2","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}}]'
        SecurityRelay: '[{"name":"Security Relay1","dtmf":"#","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}},{"name":"Security Relay2","dtmf":"0","enable":1,"showHome":1,"showTalking":1,"accessControl":{"pin":1,"rf":1,"face":1,"ble":1,"nfc":1},"schedule":{"enable":0,"access":[]}}]'
        """
        self.pm_call_operation.edit_device_by_pm(mac, **kwargs)
        if kwargs and 'SecurityRelay' in kwargs:
            pass
        else:
            self.set_device_security_relay_dtmf(mac)

    def set_device_security_relay_dtmf(self, mac, relay1='6', relay2='7', relay3='8', relay4='9'):
        """
        自动化修改设备的security relay dtmf, 避免云上查看doorlog信息因sr影响而失败.
        """
        try:
            ret = self.pm_call_operation.get_device_row_by_pm(mac)
            if 'SecurityRelay' not in ret:
                return False
            else:
                sr = ret.get('SecurityRelay')
                list1 = [relay1, relay2, relay3, relay4]

                def test(a):
                    ret = list1[0]
                    del list1[0]
                    return '"dtmf":"{}"'.format(ret)

                sr = re.sub('"dtmf":"."', test, sr)
                self.pm_call_operation.edit_device_by_pm(mac, SecurityRelay=sr)
                return ret
        except:
            aklog_error('设置security relay dtmf失败')

    def edit_user_access_group(self, schedule_name_list):
        return self.pm_key.edit_user_access_group_COM(self.cloud_data.get('user_community'), *schedule_name_list)

    def send_message(self, title, content):
        self.pm_message.add_message_PM_COM(title, content, 0, [self.cloud_data['user_community']])

    def clear_message(self):
        self.pm_message.del_message_PM_COM()

    def get_door_sensor_status(self, mac):
        aklog_info()
        para = {"Build": "all",
                "Room": "all",
                "Status": "all",
                "Type": "all",
                "searchKey": "MAC",
                "searchValue": mac,
                "row": "10",
                "page": "1"}
        rst = self.pm_log_operation.get_web_server_path(self.pm_log_operation.community_web_path, 'device/getListForPm',
                                                        para)['data']
        if rst and rst['detail']:
            data = rst['detail'][0]['DoorRelayStatus'] + rst['detail'][0]['DoorSeRelayStatus']
            relay_list = ['relaya', 'relayb', 'relayc', 'relayd', 'securityrelaya', 'securityrelayb']
            sensor_status = {}
            index = 0
            for i in data:
                sensor_status[relay_list[index]] = i
                index += 1
            return sensor_status
        aklog_info('请求错误')
        return False

    def get_building_info(self, building_name):
        """获取楼栋的信息"""
        log = self.pm_key.get_web_server_path(self.pm_key.common_web_path, 'project/getBuildRoom')
        if not log:
            return False
        for i in log.get('data').get('build'):
            if i.get('UnitName') == building_name:
                return i
        return False

    def get_apt_info(self, apt_number):
        """获取房间的信息"""
        log = self.pm_key.get_web_server_path(self.pm_key.common_web_path, 'project/getBuildRoom')
        if not log:
            return False
        for i in log.get('data').get('room'):
            if i.get('RoomName') == apt_number:
                return i
        return False

    def get_device_info(self, mac):
        """获取设备的信息"""
        param = {
            'Build': 'all',
            'Room': 'all',
            'Status': 'all',
            'Type': 'all',
            'searchKey': mac,
            'searchValue': '',
            'Sort': '',
            'SortField': '',
            'row': '10',
            'page': '1',
        }
        log = self.pm_key.get_web_server_path(self.pm_key.community_web_path, 'device/getListForPm', param)
        if not log:
            return False
        for i in log.get('data').get('detail'):
            if i.get('MAC') == mac:
                return i
        return False

    def set_device_contact_visble_in_building(self, contact_list):
        """设置在楼栋公共下的设备联系人列表显示哪些联系人
        {"BuildingList":[],
        "AptList":[
        {"BuildingUUID":"na-f3a96b212faf11ef91a400163e0605c8","AptUUID":"cn-9d4d6dfc663c11eda0a100163e0605c8","PersonalUUID":"","DeviceUUID":""},
        {"BuildingUUID":"na-f3a96b212faf11ef91a400163e0605c8","AptUUID":"cn-0a7bfeaf663d11eda0a100163e0605c8","PersonalUUID":"","DeviceUUID":""}],
        "PersonalList":[],
        "DeviceList":[]
        }
        """

        def get_param_json(input_list):
            json_data = {
                "BuildingList": [],
                "AptList": [],
                "PersonalList": [],
                "DeviceList": []
            }

            for building_uuid, apt_uuid in input_list:
                apt_entry = {
                    "BuildingUUID": building_uuid,
                    "AptUUID": apt_uuid,
                    "PersonalUUID": "",
                    "DeviceUUID": ""
                }
                json_data["AptList"].append(apt_entry)
            return json.dumps(json_data)

        device_uuid = self.get_device_info(self.cloud_data['masterMAC']).get('UUID')
        uuid_list = []
        for building_name, apt_number in contact_list:
            building_info = self.get_building_info(building_name)
            apt_info = self.get_apt_info(apt_number)
            if not building_info or not apt_info:
                aklog_info(f'{building_name} {apt_number}:未找到对应楼栋或房间的uuid')
                continue
            uuid_list.append([building_info.get('UUID'), apt_info.get('PersonalAccountUUID')])
        aklog_info('uuid list:' + str(uuid_list))
        contact_uuid = f'{get_param_json(uuid_list)}'

        param = {
            'UUID': device_uuid,
            'ContactList': contact_uuid
        }
        ret = self.pm_key.post_web_server_path(self.pm_key.community_web_path, 'device/editContactList', param)
        return ret

    def set_video_record(self, enable=False):
        """设置视频录制"""
        community_uuid = self.get_community_detail().get('data').get('AccountUUID')
        param = {
            "isEnable": enable,
            "community": community_uuid,
            "planType": "subscription",
            "storageDays": 30,
            "storedDevicesNum": "unlimited",
            "devices": {
                "isAll": True,
                "list": []
            },
            "isEnableCallAudio": True
        }
        # param = json.dumps(param)
        header = self.pm_header
        header['X-Project'] = community_uuid
        return self.pm_key.post_web_server_path('https://backend.test84.akuvox.com/web-server/v4/web/community',
                                                'videoStorage/pm/update', param, headers=header)


class get_app:
    def __init__(self, username, password, server='test84.akuvox.com', api_version='6.8'):
        self.s = requests.Session()
        self.s.headers['api-version'] = api_version
        self.s.headers['User-Agent'] = 'SmartPlus'
        self.server = server
        self.token = self.get_app(username, password)

    def get_app(self, user, pwd):
        username = kaisa(user)
        password = md5_2(pwd)
        if self.server.replace('.', '').isdigit():
            r = self.s.get('http://{}:9999/login?user={}&passwd={}'.format(self.server, username, password))
        else:
            r = self.s.get('http://gate.{}:9999/login?user={}&passwd={}'.format(self.server, username, password))
        try:
            return r.json().get('datas').get('token')
        except:
            print(r.text)
            print(self.server, user, pwd)
            print(username, password)
            aklog_warn('app emu登录失败!!!')
            return False

    def open_relay(self, mac, relay='A'):
        relaydict = {'A': ' 0', 'B': ' 1', 'C': ' 2', 'D': ' 3'}
        url = 'http://{}:8080/opendoor?token={}'.format(self.server, self.token)
        r = self.s.post(url, json={'mac': mac.replace(":", '').upper(), 'relay': relaydict.get(relay)})
        print(r.text)


if __name__ == '__main__':
    pass
