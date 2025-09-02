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
from testcase.common.AkubelaBase.WebV3.aklibAkubelaWebInfBaseV3 import AkubelaWebInfBaseV3
from testcase.common.AkubelaBase.WebV3.aklibAkubelaDefine import *
from typing import Union, Optional
import time
import uuid
import random
from copy import deepcopy


class AkubelaUserWebInfV3(AkubelaWebInfBaseV3):

    # region 初始化

    def __init__(self):
        super().__init__()
        self.scenes_info = {}
        self.scenes_list = []
        self.scenes_detail_info = {}
        self.security_info = {}
        self.security_list = []
        self.devices_list_info = {}
        self.devices_list = []
        self.area_triggers_info = {}
        self.area_conditions_info = {}
        self.area_actions_info = {}
        self.device_triggers_info = {}
        self.device_conditions_info = {}
        self.device_actions_info = {}
        self.contacts_info = {}
        self.light_group_info = {}
        self.link_ctrl_info = {}
        self.doorphone_list = []

    def login(self, login_type=None, retry=3, print_trace=True, raise_enable=True, re_login=False):
        return self.interface_init(login_type, retry, print_trace, raise_enable, re_login)

    def login_with_user_pwd(self, username, password, login_type=None):
        if username:
            self.username = username
        if password:
            self.password = password
        return self.login(login_type, re_login=True)

    # endregion

    # region 帐号管理

    def change_user_pwd(self, new_pwd, old_pwd=None):
        """修改用户密码"""
        aklog_info()
        if not old_pwd:
            old_pwd = self.password
        if new_pwd == old_pwd:
            aklog_info('密码相同，不用修改')
            return True
        change_pwd_data = {"type": "config/auth_provider/homeassistant/change_password",
                           "current_password": old_pwd,
                           "new_password": new_pwd}
        resp = self.ws_send_request(change_pwd_data)
        aklog_info(resp)
        if resp and resp.get('success'):
            aklog_info('change_user_pwd OK')
            self.password = new_pwd
            return True
        else:
            aklog_error('change_user_pwd Fail')
            aklog_debug('resp: %s' % resp)
            return False

    def forget_pwd(self, email):
        """忘记密码"""
        path = 'api/auth/forgetpwd'
        data = {
            "email": email
        }
        resp = self.api_post(path, data)
        if resp and resp.get('success'):
            return True
        else:
            return False

    def unbind_fm_account(self, fm_email):
        """解绑家庭成员帐号"""
        aklog_info()
        if not self.family_id:
            self._get_family_id()
        get_family_users_info = self.get_family_users_info(fm_email)
        fm_user_id = None
        if get_family_users_info is not None:
            fm_user_id = self.get_family_users_info(fm_email)['user_id']
            # users = self.get_family_users_info(fm_email)
            # for user in users:
            #     email_sub = user["email"]
            #     if email_sub == fm_email:
            #         fm_user_id = user["user_id"]
        aklog_info(fm_user_id)
        if not fm_user_id:
            return False
        data = {"type": "ak_account/families/unbind",
                "user_id": fm_user_id,
                "family_id": self.family_id,
                "unbind": True}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('unbind_fm_account OK')
            return True
        else:
            aklog_error('unbind_fm_account Fail')
            aklog_debug('resp: %s' % resp)
            return False

    def unbind_all_fm_account(self):
        """解绑所有家庭从帐号"""
        aklog_info()
        # cur_user_id = self.get_current_user_info()['id']
        if not self.family_id:
            self._get_family_id()
        family_users = self.get_family_users_info()
        for fm_user in family_users:
            fm_user_id = fm_user['user_id']
            if fm_user == self.account_id:
                continue
            data = {"type": "ak_account/families/unbind",
                    "user_id": fm_user_id,
                    "family_id": self.family_id,
                    "unbind": True}
            resp = self.ws_send_request(data)
            if resp and resp.get('success'):
                aklog_info('unbind_fm_account %s OK' % fm_user['email'])
                continue
            else:
                aklog_error('unbind_fm_account %s Fail' % fm_user['email'])
                aklog_debug('resp: %s' % resp)
                return False
        aklog_info('unbind_all_fm_account OK')
        return True

    def del_account_and_transfer(self, main_email, user_email):
        """
        删除主帐号，然后将管理员转移给其他成员，如果存在多个家庭成员，需要指定转移的成员邮箱
        """
        aklog_info()
        family_id = self._get_family_id()
        family_users = self.get_family_users_info()
        user_id = None
        for fm_user in family_users:
            if fm_user['email'] == user_email:
                user_id = fm_user['user_id']
                continue
        main_id = None
        for fm_user in family_users:
            if fm_user['email'] == main_email:
                main_id = fm_user['user_id']
                continue
        data = {
            "type": "ak_account/users/delete",
            "unbind": True,
            "user_id": main_id,
            "family_id": family_id,
            "transfer_user_id": user_id
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('主账号删除并权限转移成功')
            return True
        else:
            aklog_error('主账号删除并权限转移失败')
            aklog_debug('resp: %s' % resp)
            return False

    def del_sub_account(self, main_email):
        """
        删除子帐号
        """
        aklog_info()
        family_id = self._get_family_id()
        family_users = self.get_family_users_info()
        main_id = None
        for fm_user in family_users:
            if fm_user['email'] == main_email:
                main_id = fm_user['user_id']
                continue
        data = {
            "type": "ak_account/users/delete",
            "unbind": True,
            "user_id": main_id,
            "family_id": family_id,
            # "transfer_user_id": user_id
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('主账号删除成功')
            return True
        else:
            aklog_error('主账号删除失败')
            aklog_debug('resp: %s' % resp)
            return False

    def account_change_permission(self, user_email):
        """转移主账号权限给子账号"""
        aklog_info()
        family_users = self.get_family_users_info()
        user_id = None
        for fm_user in family_users:
            if fm_user['email'] == user_email:
                user_id = fm_user['user_id']
                continue
        data = {
            "type": "ak_account/permission",
            "user_id": user_id,
            "transfer_to_master": True}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('主账号权限转移成功')
            return True
        else:
            aklog_error('主账号权限转移失败')
            aklog_debug('resp: %s' % resp)
            return False

    def account_unbind_transfer(self, main_email, user_email):
        """解绑主账号并转移权限给子账号"""
        aklog_info()
        family_id = self._get_family_id()
        family_users = self.get_family_users_info()
        user_id = None
        for fm_user in family_users:
            if fm_user['email'] == user_email:
                user_id = fm_user['user_id']
                continue
        main_id = None
        for fm_user in family_users:
            if fm_user['email'] == main_email:
                main_id = fm_user['user_id']
                continue
        data = {
            "type": "ak_account/families/unbind",
            "unbind": True,
            "user_id": main_id,
            "family_id": family_id,
            "transfer_user_id": user_id
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('主账号解绑并权限转移成功')
            return True
        else:
            aklog_error('主账号解绑并权限转移失败')
            aklog_debug('resp: %s' % resp)
            return False

    def get_family_users_info(self, user_email=None):
        """
        获取家庭用户信息，包含主帐号和从帐号
        user_email: 默认为空表示获取所有用户，可以获取指定用户信息
        return: family_members
        {
            "family_id": "r908377cb2d9070d63dc07530abad9d0b",
            "family_member_num": 2,
            "family_members": [
                {
                    "user_id": "a3eef3c11f2cf0403759e34a5c1ccdf39",
                    "username": "hzs01_cbuat_user1@aktest.top",
                    "first_name": "cbuat_user1",
                    "last_name": "hzs01",
                    "email": "hzs01_cbuat_user1@aktest.top",
                    "mobile": "13255768777765",
                    "land_line": null,
                    "region": "",
                    "address": "",
                    "authority": 2,
                    "intercom": true,
                    "image": null
                },
                {
                    "user_id": "a47af5ad5ca0335541fbe04b65752cc44",
                    "username": "cbuat_fm103hzs01",
                    "first_name": "cbuat_fm103",
                    "last_name": "hzs01",
                    "email": "hzs01_cbuat_fm103@aktest.top",
                    "mobile": "1242346566776",
                    "land_line": "352434543",
                    "region": "中国(+86)",
                    "address": "",
                    "authority": 0,
                    "intercom": false,
                    "image": null
                }
            ]
        }
        """
        aklog_info()
        if not self.family_id:
            self._get_family_id()
        data = {"type": "ak_account/users/family_id",
                "family_id": self.family_id}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('get_family_users_info OK, counts: %s' % resp.get('result')['family_member_num'])
            family_members = resp.get('result')['family_members']
            if not user_email:
                return family_members
            else:
                for member in family_members:
                    if member['email'] == user_email:
                        return member
                aklog_error('%s not found' % user_email)
                aklog_debug(family_members)
                return None
        else:
            aklog_error('get_family_users_info Fail')
            aklog_debug('resp: %s' % resp)
            return None

    def get_current_user_info(self):
        """
        该方法弃用
        return:
        {
            "id": "a3eef3c11f2cf0403759e34a5c1ccdf39",
            "name": "hzs01_cbuat_user1@aktest.top",
            "is_owner": true,
            "is_admin": true,
            "credentials": [
                {
                    "auth_provider_type": "homeassistant",
                    "auth_provider_id": null
                }
            ],
            "mfa_modules": [
                {
                    "id": "totp",
                    "name": "Authenticator app",
                    "enabled": false
                }
            ]
        }
        """
        data = {"type": "auth/current_user"}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            result = resp.get('result')
            aklog_info('get_current_user_info OK')
            aklog_debug(result)
            return result
        else:
            aklog_error('get_current_user_info Fail')
            aklog_debug('resp: %s' % resp)
            return None

    def _get_family_id(self):
        """获取家庭id"""
        user_detail_info = self._get_user_detail_info()
        self.family_id = user_detail_info['family_id']
        return self.family_id

    def _get_user_detail_info(self, user_id=None):
        """
        获取user信息
        return:
        {
            "user_id": "a3eef3c11f2cf0403759e34a5c1ccdf39",
            "username": "hzs01_cbuat_user1@aktest.top",
            "first_name": "cbuat_user1",
            "last_name": "hzs01",
            "email": "hzs01_cbuat_user1@aktest.top",
            "mobile": "13255768777765",
            "land_line": null,
            "region": "",
            "address": "",
            "authority": 2,
            "intercom": true,
            "image": null,
            "family_id": "r908377cb2d9070d63dc07530abad9d0b"
        }
        """
        aklog_info()
        if not user_id:
            user_id = self.account_id
        data = {"type": "ak_account/users/user_id",
                "user_id": user_id}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            ret = resp.get('result')
            aklog_info('get_user_detail_info OK')
            aklog_debug(ret)
            return ret
        else:
            aklog_error('get_user_detail_info Fail')
            aklog_debug('resp: %s' % resp)
            return None

    def _get_family_info(self):
        """
        return:
        {
            "account": "hzs_user",
            "family_id": "r908377cb2d9070d63dc07530abad9d0b",
            "family_address": "中国 福建省 厦门市 gr",
            "family_devices": 6,
            "family_rooms": 5,
            "offline": false,
            "appmode": "homeautomation"
        }
        """
        if not self.family_id:
            self._get_family_id()
        data = {"type": "ak_account/families/family_id",
                "family_id": self.family_id}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('get_family_info OK')
            return resp.get('result')
        else:
            aklog_error('get_family_info Fail')
            aklog_debug('resp: %s' % resp)
            return None

    def add_sub_account(self, account_data):
        """
        添加子账号
        type   String类型   ak_account/users/create
        family_id  String类型  家庭ID
        data   Object类型  用户信息，根据需要填写
        data:[{
            first_name(String类型):用户首字母
            last_name(String类型):用户尾字母
            email(String类型):用户邮箱
            region(String类型):用户地区
            mobile(String类型):用户手机号
            land_line(String类型):用户固定电话
            authority(Int类型)：0:子账号（普通权限）;1:子账号（带管理员权限）;2:主账号
            intercom(Bool类型）:true: 绑定对讲  false: 未绑定对讲
        }]
        返回参数：
            "id":31,
            "type":"result",
            "success":true,
            result  Object类型[{
            family_id(String类型):家庭ID
            user_id(String类型):用户id
            username(String类型):用户名
        }]
        data数据参考：
           data = {
        "first_name": "tu3",
        "last_name": "wm3",
        "email": "twm_acc2444466@aktest.top",
        "region": "123123",
        "mobile": "123123",
        "land_line": "",
        "authority": 0,
        "intercom": False
    }
        """
        aklog_info()
        family_id = self._get_family_id()
        time.sleep(1)
        sub_account_data = account_data
        add_sub_data = {"type": "ak_account/users/create",
                        "family_id": family_id,
                        "data": sub_account_data}
        resp = self.ws_send_request(add_sub_data)
        if resp and resp.get('success'):
            aklog_info('添加子账号成功')
            return True
        else:
            aklog_error('添加子账号失败')
            aklog_error(resp)
            return False

    # endregion

    # region 设置

    def get_cloud_mode(self):
        """获取当前连云/脱云模式"""
        aklog_info()
        data = {"type": "ak_config/get",
                "item": ["Settings.CONNECTIONTYPE.Mode"]}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            cloud_mode = resp['result']['Settings.CONNECTIONTYPE.Mode']
            aklog_info('cloud_mode: %s' % cloud_mode)
            return cloud_mode
        else:
            aklog_error('get_cloud_mode Fail')
            aklog_debug('resp: %s' % resp)
            return None

    def set_cloudless_mode(self, mode=True):
        """
        设置开启脱云模式
        mode: True表示开启脱云模式，False表示关闭脱云模式
        """
        aklog_info()
        data = {"type": "ak_config/update",
                "item": {"Settings.CONNECTIONTYPE.Mode": mode}}
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_info('set_cloudless_mode OK')
            return True
        else:
            aklog_error('set_cloudless_mode Fail')
            aklog_debug('resp: %s' % resp)
            return False

    # endregion

    # region 获取设备和联系人信息

    def get_panel_device_list(self):
        """获取面板设备列表"""
        aklog_info()
        data = {"type": "config/ak_device/panel/list"}
        resp = self.ws_send_request(data)
        if not resp:
            return None
        results = resp.get('result')
        return results

    def get_panel_devices_info(self, key_type='name'):
        """
        获取家庭中心和网关面板设备信息
        return:
        {"HyPanel012400":
            {
                "homecenter": true,
                "device_id": "d8c0298b95e1da6caa278e55fa5c12de4",
                "name": "HyPanel012400",
                "ip": "192.168.88.168",
                "model": "PS51",
                "software": "51.1.31.58",
                "hardware": "51.48.33.32.0.0.0.16.0.0.0.10.8.0.0.0",
                "online": true,
                "mac": "C20824012400",
                "ab_uid": "151C20824012400",
                "base_module": "R2-EU",
                "status": 1,
                "network": "Wired"
            }
        }
        """
        results = self.get_panel_device_list()
        if not results:
            return None
        panel_devices_info = {}
        for ret in results:
            key = ret.get(key_type)
            if key:
                panel_devices_info[key] = ret
        return panel_devices_info

    def get_devices_list_info(self, regain=True, key_type='name') -> dict:
        """
        获取家庭中全部设备信息的接口
        key_type: 作为devices_info字典的key（要保证唯一性），比如取result中的name, device_id的值作为key
        {
        'Hypanel012400': {
                "area_id": "",
                "device_id": "da133decf23894a869557625f8e13a3ec",
                "product_attributes": "panel",
                "product_type": "Panel",
                "device_type": "PS51",
                "name": "Hypanel012400",
                "location": "",
                "favorite": false,
                "version": "51.1.36.108",
                "sort_id": 1,
                "bypass": false,
                "bypass_time": "",
                "parent_device_id": "",
                "is_wire": false,
                "mac": "C20824012400",
                "source": 0,
                "relay_index": 0,
                "ownership": "Hypanel012400",
                "child_ids": [
                    "4d845da79c53476cb2e526d4e2b12689",
                    "9f060346b37746ecb1edfa95fe930f82"
                ],
                "product_model": "PS51",
                "has_new_version": false,
                "new_version": 0,
                "upgrade_status": 0,
                "upgrade_progress": 0,
                "online": true,
                "support_delete": false,
                "is_multi_channel_device": false,
                "icon": "",
                "fav": false,
                "group": "Gateway",
                "scene_dev_id": "",
                "support_update_type": true,
                "support_split": false,
                "attributes": [
                    {
                        "domain": "sensor",
                        "feature": "sensor_temperature",
                        "value": "29.5",
                        "entity_id": "sensor.f388ff23a5df4963978135d157ec7084",
                        "unit": "°C"
                    },
                    {
                        "domain": "sensor",
                        "feature": "sensor_humidity",
                        "value": "46.8",
                        "entity_id": "sensor.f4813751f0f44f7a833455b63c784092",
                        "unit": "%"
                    },
                    {
                        "domain": "online",
                        "feature": "online",
                        "value": true
                    }
                ]
            }
        }
        """
        aklog_info()
        if not regain and self.devices_list_info and self.devices_list_info.get('key_type') == key_type:
            return self.devices_list_info
        results = self.get_devices_list()
        for ret in results:
            key = ret[key_type]
            self.devices_list_info[key] = ret
        self.devices_list_info['key_type'] = key_type
        return deepcopy(self.devices_list_info)

    def get_devices_list(self, grep=None, regain=True, **kwargs) -> Union[list, bool, None]:
        """
        HA获取Devices设备列表
        :param grep: 筛选条件，按照devices_list的响应字段传入，默认为None
        :param regain: 是否重新获取
        :param kwargs: 同时传入多个过滤条件
        比如：area_id='xxxxx', device_type="Thermostat" 可以只获取该房间下指定类型的设备
        """
        if regain:
            self.devices_list.clear()
        if not self.devices_list:
            data = {
                "type": "config/ak_device/list"
            }
            resp = self.ws_send_request(data)
            if resp is None or isinstance(resp, bool):
                return resp
            self.devices_list = resp['result']
        if grep:
            grep_list = []
            for device in self.devices_list:
                grep_list.append(device[grep])
            return grep_list
        if kwargs:
            devices_info = [
                device for device in self.devices_list
                if all(device.get(key) == value for key, value in kwargs.items())
            ]
            return devices_info
        return deepcopy(self.devices_list)

    def get_device_id_by_name(self, device_name, regain=True):
        devices_info = self.get_devices_list(name=device_name, regain=regain)
        if len(devices_info) > 0:
            device_id = devices_info[0].get('device_id')
            aklog_debug(f'{device_name}, device_id: {device_id}')
            return device_id
        else:
            return None

    def get_device_name_list(self, product_type=None, product_model=None, device_type=None,
                             exclude_product_type=None, exclude_product_model=None, exclude_device_type=None,
                             regain=True, **kwargs):
        """
        获取设备名称列表
        Args:
            product_type (str or list): 可以传入多个product_type，list类型
            product_model (str or list):
            device_type (str or list):
            exclude_product_type (str or list): 排除的设备类型，可以传入多个product_type，list类型
            exclude_product_model (str or list):
            exclude_device_type (str or list):
            regain (bool):
            kwargs: 其他过滤条件
        """
        devices_list = self.get_devices_list(regain=regain)
        device_name_list = []
        if devices_list and isinstance(devices_list, list):
            for device in devices_list:
                if (device_type and isinstance(device_type, str)
                        and device.get('device_type') != device_type):
                    continue
                if (device_type and isinstance(device_type, list)
                        and device.get('device_type') not in device_type):
                    continue
                if (product_type and isinstance(product_type, str)
                        and device.get('product_type') != product_type):
                    continue
                if (product_type and isinstance(product_type, list)
                        and device.get('product_type') not in product_type):
                    continue
                if (product_model and isinstance(product_model, str)
                        and device.get('product_model') != product_model):
                    continue
                if (product_model and isinstance(product_model, list)
                        and device.get('product_model') not in product_model):
                    continue

                if (exclude_device_type and isinstance(exclude_device_type, str)
                        and device.get('device_type') == exclude_device_type):
                    continue
                if (exclude_device_type and isinstance(exclude_device_type, list)
                        and device.get('device_type') in exclude_device_type):
                    continue
                if (exclude_product_type and isinstance(exclude_product_type, str)
                        and device.get('product_type') == exclude_product_type):
                    continue
                if (exclude_product_type and isinstance(exclude_product_type, list)
                        and device.get('product_type') in exclude_product_type):
                    continue
                if (exclude_product_model and isinstance(exclude_product_model, str)
                        and device.get('product_model') == exclude_product_model):
                    continue
                if (exclude_product_model and isinstance(exclude_product_model, list)
                        and device.get('product_model') in exclude_product_model):
                    continue

                if kwargs:
                    if any(device.get(key) != value for key, value in kwargs.items()):
                        continue
                device_name_list.append(device['name'])
        aklog_debug('device_name_list: %s' % device_name_list)
        return device_name_list

    def get_relay_name_list(self):
        devices = self.get_devices_list()
        relay_names = [device['name'] for device in devices
                       if device.get('product_type') == 'Relay']
        aklog_info(relay_names)
        return relay_names

    def get_device_info(self, by_device_name=None, by_device_mac=None, attr=None, regain=True, **kwargs):
        """
        获取设备信息
        Args:
            by_device_name ():
            by_device_mac ():
            attr ():
            regain ():
            **kwargs (): 过滤条件，比如: device_id='xxx'
        """
        aklog_info()
        if by_device_name:
            kwargs['name'] = by_device_name
        if by_device_mac:
            kwargs['mac'] = by_device_mac
        by_device_id = kwargs.get('device_id')
        devices_list = self.get_devices_list(regain=regain, **kwargs)
        if not isinstance(devices_list, list) or not devices_list:
            return None
        if attr:
            value = devices_list[0].get(attr)
            aklog_debug(f'{by_device_name or by_device_mac or by_device_id}, attr: {attr}, value: {value}')
            return value
        aklog_debug(f'{by_device_name or by_device_mac or by_device_id}, device_info: {devices_list[0]}')
        return devices_list[0]

    def get_area_devices_info(self, area_id=None, area_name=None) -> list:
        """获取区域设备信息"""
        if area_id is None and area_name:
            room_list = self.get_room_list()
            for room in room_list:
                if room['name'] == area_name:
                    area_id = room['area_id']
                    break
        devices_list = self.get_devices_list()
        devices_info = []
        for device in devices_list:
            if device['area_id'] == area_id:
                devices_info.append(device)
        return devices_info

    def get_light_group_bind_devices(self, device_name=None, device_id=None, grep=None, regain=False):
        """
        获取灯组绑定的子设备信息
        Args:
            device_name ():
            device_id ():
            grep ():
            regain ():

        Returns:
        {
            "id": 530,
            "type": "result",
            "success": true,
            "result": [
                {
                    "device_id": "bc782aa120c94e4991a7abdcf9556319",
                    "name": "RGB Light-000002",
                    "device_type": "Light",
                    "is_bind": true
                },
                {
                    "device_id": "1b79fbe8f57040ffa3e10ac7f20455b3",
                    "name": "RGB Light-000003",
                    "device_type": "Light",
                    "is_bind": true
                },
                {
                    "device_id": "dcb0d7dce7ff46a8a8439fa735960a56",
                    "name": "yeelight blue Color-000002",
                    "device_type": "Light",
                    "is_bind": false
                }
            ]
        }
        """
        aklog_info()
        if not device_id:
            device_id = self.get_device_id_by_name(device_name, regain=regain)
        if regain:
            self.light_group_info.clear()
        if device_id not in self.light_group_info:
            data = {
                "type": "ak_device/light_group/support_devices",
                "device_id": device_id,
            }
            resp = self.ws_send_request(data)
            if resp is None or isinstance(resp, bool):
                return resp
            device_list = resp.get('result')
            self.light_group_info[device_id] = device_list
        else:
            device_list = self.light_group_info[device_id]

        if grep:
            grep_list = []
            for device in device_list:
                if device.get('is_bind'):
                    grep_list.append(device.get(grep))
            return grep_list
        bind_devices = []
        for device in device_list:
            if device.get('is_bind'):
                bind_devices.append(device)
        return bind_devices

    def get_zigbee_group_link_device(self, zigbee_group_name=None, device_id=None):
        """获取zigbee组绑定的子设备信息"""
        aklog_info()
        if not device_id:
            device_id = self.get_device_id_by_name(zigbee_group_name)
        data = {
            "type": "ak_device/zigbee_group/get_link_device",
            "device_id": device_id,
        }
        resp = self.ws_send_request(data)
        if resp is None or isinstance(resp, bool):
            return resp
        devices = resp.get('result')
        device_list = [device['name'] for device in devices]

        aklog_info(device_list)
        return device_list

    def get_link_ctrl_bind_devices(self, device_name=None, device_id=None, grep=None, regain=False):
        """
        获取多设备联动信息
        Args:
            device_name ():
            device_id ():
            grep ():
            regain ():

        Returns:
        {
            "id": 509,
            "type": "result",
            "success": true,
            "result": {
                "enabled": true,
                "device_list": [
                    {
                        "area_id": null,
                        "device_id": "1b79fbe8f57040ffa3e10ac7f20455b3",
                        "device_name": "RGB Light-000003",
                        "location": "",
                        "product_type": "Light",
                        "is_linked": true
                    }
                ]
            }
        }
        """
        aklog_info()
        if not device_id:
            device_id = self.get_device_id_by_name(device_name, regain=regain)
        if regain:
            self.link_ctrl_info.clear()
        if device_id not in self.link_ctrl_info:
            data = {
                "type": "device/link_ctrl/list",
                "device_id": device_id,
                "linked": True,
            }
            resp = self.ws_send_request(data)
            if resp is None or isinstance(resp, bool):
                return resp
            device_list = resp.get('result').get('device_list')
            self.link_ctrl_info[device_id] = device_list
        else:
            device_list = self.link_ctrl_info[device_id]

        if not device_list:
            return []
        if grep:
            grep_list = []
            for device in device_list:
                if device.get('is_linked'):
                    grep_list.append(device.get(grep))
            return grep_list
        bind_devices = []
        for device in device_list:
            if device.get('is_linked'):
                bind_devices.append(device)
        return bind_devices

    def get_device_support_features(self, device_name=None, device_id=None, regain=False):
        """
        获取设备支持的features
        Args:
            device_name ():
            device_id ():
            regain ():
        """
        kwargs = {}
        if device_id:
            kwargs['device_id'] = device_id
        attributes = self.get_device_info(device_name, attr='attributes', regain=regain, **kwargs)
        features = [attr.get('feature') for attr in attributes if attr.get('feature')]
        return features

    def is_simulator_device(self, device_name=None, device_id=None, check_online=True):
        """判断是被是否为模拟器的设备"""
        devices_list = self.get_devices_list(regain=False)
        device_info = None
        for device in devices_list:
            if ((device_name and device.get('name') == device_name)
                    or (device_id and device.get('device_id') == device_id)):
                device_info = device
                break
        if not device_info:
            aklog_debug(f'{device_name or device_id} 未找到')
            return None
        if check_online and not device_info.get('online'):
            aklog_debug(f'{device_name or device_id} 处于离线状态')
            return None
        gateway_info = None
        for device in devices_list:
            if device.get('name') == device_info.get('ownership'):
                gateway_info = device
                break
        if gateway_info.get('version') == 'xxx.xxx.xxx.xxx':
            aklog_debug(f'{device_name or device_id} 是模拟器上的设备')
            return True
        else:
            # aklog_debug(f'{device_name or device_id} 是真实设备')
            return False

    def get_device_info_by_id(self, device_id):
        """获取设备信息"""
        aklog_debug()
        data = {
            "type": "config/ak_device/device_id",
            "device_id": device_id
        }
        resp = self.ws_send_request(data)
        if resp is None or isinstance(resp, bool):
            return resp
        results = resp.get('result')
        return results

    def get_device_log(self, device_name):
        """获取设备最新触发的log时间"""
        aklog_debug()
        device_id = self.get_device_id_by_name(device_name)
        data = {
            "type": "config/ak_device/log",
            "device_id": device_id
        }
        resp = self.ws_send_request(data)
        if resp is None or isinstance(resp, bool):
            return resp
        results = resp.get('result')
        first_time = results[0]['format_device_time'] if data else None
        return first_time

    def get_devices_entity_id(self, device_name, domain=None, feature=None):
        """
        获取家庭某个设备的控制的实体id的接口,传入设备名和设备的控制类型，如switch，lock
        """
        aklog_info()
        self.get_devices_list_info()
        if not device_name:
            aklog_warn('device_name不能为空')
            return None
        device_info = self.devices_list_info.get(device_name)
        if not device_info:
            aklog_warn(f'{device_name} 未找到')
            return None
        for enti in device_info['attributes']:
            entity_id = enti.get('entity_id')
            if not entity_id:
                continue
            if not domain and not feature:
                aklog_debug(f'{device_name}, entity_id: {entity_id}')
                return entity_id
            if ((domain and enti['domain'] == domain)
                    or (feature and enti['feature'] == feature)):
                return entity_id
        # 如果传入domain和feature都未找到entity_id，可能是domain和feature有误
        aklog_warn(f'{device_name} domain: {domain}, feature: {feature} 未找到 entity_id')
        for enti in device_info['attributes']:
            entity_id = enti.get('entity_id')
            if entity_id:
                aklog_debug(f'entity_info: {enti}')
                return entity_id
        return None

    def control_device(self, entity_id=None, domain=None, service_type=None, **kwargs):
        """
        调用服务控制设备,
        domain ：‘switch’：switch类，‘light’: 灯类，'cover':窗帘，‘button’: 按键，’lock‘：锁
        service_type:控制类型 turn_on：打开，turn_off：关闭 ， unlock:解锁   lock：锁
        {
             "type":"call_service",
                "id":3,
                "domain":"switch",
                "service":"turn_on",
                "service_data":{
                 "entity_id":"switch.smart_plug"
             }
            }
        """
        aklog_info()
        data = {
            "type": "call_service",
            "domain": domain,
            "service": service_type,
            "service_data": {
                "entity_id": entity_id
            }
        }
        if kwargs:
            for key, value in kwargs.items():
                data['service_data'][key] = value
        resp = self.ws_send_request(data)
        ret = resp.get('success')
        if not ret:
            aklog_debug(f'resp: {resp}')
        return ret

    def control_dimming_light_by_name(self, device_name=None, service_type=None, brightness_pct=None):
        """
            通过名字控制dimming灯
        """
        aklog_info()
        domain = "light"
        entity_id = self.get_devices_entity_id(device_name, domain)
        data = {
            "type": "call_service",
            "domain": domain,
            "service": service_type,
            "service_data": {
                "brightness_pct": brightness_pct,
                "entity_id": entity_id,
            }
        }
        resp = self.ws_send_request(data)
        ret = resp.get('success')
        return ret

    def control_thermostat_hvac_mode_by_name(self, device_name=None, service_type=None, hvac_mode=None):
        """
            通过名字控制hvac_mode
        """
        aklog_info()
        domain = "climate"
        entity_id = self.get_devices_entity_id(device_name, domain)
        data = {
            "type": "call_service",
            "domain": domain,
            "service": service_type,
            "service_data": {
                "entity_id": entity_id,
                "hvac_mode": hvac_mode
            }
        }
        resp = self.ws_send_request(data)
        ret = resp.get('success')
        return ret

    def control_thermostat_preset_mode_by_name(self, device_name=None, service_type=None, preset_mode=None):
        """
            通过名字控制preset_mode
        """
        aklog_info()
        domain = "climate"
        entity_id = self.get_devices_entity_id(device_name, domain)
        data = {
            "type": "call_service",
            "domain": domain,
            "service": service_type,
            "service_data": {
                "entity_id": entity_id,
                "preset_mode": preset_mode
            }
        }
        resp = self.ws_send_request(data)
        ret = resp.get('success')
        return ret

    def control_thermostat_temperature_by_name(self, device_name=None, preset_temperature=None):
        """
            通过名字控制温度
        """
        aklog_info()
        domain = "climate"
        entity_id = self.get_devices_entity_id(device_name, domain)
        device_id = self.get_device_id(device_name)
        data = {
            "type": "config/ak_device/update_relay_climate",
            "entity_id": entity_id,
            "device_id": device_id,
            "preset_temperature": preset_temperature,
        }
        resp = self.ws_send_request(data)
        ret = resp.get('success')
        return ret

    def control_shade_position_by_name(self, device_name, position):
        """
            通过名字控制行程
        """
        aklog_info()
        domain = "cover"
        entity_id = self.get_devices_entity_id(device_name, domain)
        data = {
            "domain": domain,
            "type": "call_service",
            "service": "set_cover_position",
            "service_data": {
                "entity_id": entity_id,
                "position": position
            }
        }
        resp = self.ws_send_request(data)
        ret = resp.get('success')
        return ret

    def control_shade_by_name(self, device_name, status):
        """
            通过名字控制窗帘开关
            status:open/close/stop
        """
        aklog_info()
        domain = "cover"
        entity_id = self.get_devices_entity_id(device_name, domain)
        data = {
            "domain": domain,
            "type": "call_service",
            "service": f"{status}_cover",
            "service_data": {
                "entity_id": entity_id,
            }
        }
        resp = self.ws_send_request(data)
        ret = resp.get('success')
        return ret

    def control_plug_by_name(self, device_name, service_type=None):
        """
        控制智能插座
        Args:
            device_name (): 设备名称
            service_type (str): turn_on, turn_off
        """
        return self.control_device_by_name(
            device_name, domain='switch', feature='switch_state', service_type=service_type)

    def control_device_by_name(self, device_name, domain=None, service_type=None, feature=None, **kwargs):
        """
        控制设备
        Args:
            device_name (str):
            domain (str): 比如：switch
            feature (str): 比如：switch_state
            service_type (str): turn_on, turn_off
        """
        entity_id = self.get_devices_entity_id(device_name, domain, feature)
        if not entity_id:
            return False
        return self.control_device(entity_id, domain, service_type, **kwargs)

    def get_devices_status(self, device_name, domain=None, feature=None):
        """
        获取家庭某个设备的开关状态的接口,传入设备名和设备的控制类型，如switch，lock
        """
        aklog_info()
        results = self.get_devices_list()
        if not device_name or (not domain and not feature):
            aklog_warn('device_name and domain feature不能都为空')
            return None
        device_info = None
        for ret in results:
            if ret['name'] == device_name:
                device_info = ret
                break
        if not device_info:
            aklog_warn(f'{device_name} 未找到')
            return None

        for attr in device_info['attributes']:
            if domain and attr.get('domain') != domain:
                continue
            elif feature and attr.get('feature') != feature:
                continue
            status = attr.get('value')
            aklog_info(f'{device_name}, domain:{domain}, feature:{feature}, status: {status}')
            return status
        aklog_warn(f'domain {domain} or feature {feature} 不正确')
        return None

    def get_entity_state(self, entity_id):
        """获取设备实体状态"""
        devices_list = self.get_devices_list()
        for device_info in devices_list:
            for attr in device_info['attributes']:
                if attr.get('entity_id') != entity_id:
                    continue
                state = attr.get('value')
                aklog_debug(f'{entity_id} state: {state}')
                return state
        aklog_warn(f'{entity_id} not found')
        return None

    def get_devices_back_box(self, device_name):
        """
        获取设备底盒型号
        """
        aklog_info()
        device_id = self.get_device_id(device_name)
        data = {
            'device_id': device_id,
            "type": "ak_config/get",
            "item": [
                "status.general.firmware",
                "status.general.hardware",
                "status.network.ip",
                "status.network.wifi_name",
                "status.network.wifi_ip",
                "status.base_module.type",
                "status.network.mac",
                "status.network.link_type"
            ]
        }
        resp = self.ws_send_request(data)
        if resp is None or isinstance(resp, bool):
            return resp
        results = resp.get('result')
        return results['status.base_module.type']

    def get_devices_feature(self, device_name=None, feature=None):
        """
        获取家庭某个设备的开关状态的接口,传入设备名和设备的控制类型，如switch，lock
        """
        aklog_info()
        results = self.get_devices_list()
        if device_name:
            for ret in results:
                if ret['name'] == device_name:
                    for status in ret['attributes']:
                        if status['feature'] == feature:
                            aklog_info(status['value'])
                            return status['value']
            aklog_warn('%s 未找到' % device_name)
        return None

    def wait_device_to_state(self, device_name, state, domain=None, feature=None, offset=None, timeout=10):
        """
        等待设备的某个属性变成某个状态，比如等待锁设备开门
        Args:
            device_name (str):
            state (str):
            domain (str):
            feature (str):
            offset (int or list): 允许的误差偏移量
            timeout (int):
        """
        aklog_info()
        results = self.get_devices_list()
        device_info = None
        for ret in results:
            if ret['name'] == device_name:
                device_info = ret
                break
        if not device_info:
            unittest_results([-1, f'userweb检查: {device_name} 未找到'])
            return None
        device_id = device_info.get('device_id')

        end_time = time.time() + timeout
        while time.time() < end_time:
            attr_info = None
            for attr in device_info['attributes']:
                if domain and feature and attr.get('domain') == domain and attr.get('feature') == feature:
                    attr_info = attr
                    break
                if domain and not feature and attr.get('domain') == domain:
                    attr_info = attr
                    break
                if not domain and feature and attr.get('feature') == feature:
                    attr_info = attr
                    break
                if not domain and not feature and attr.get('feature') and '_state' in attr.get('feature'):
                    attr_info = attr
                    break
            if attr_info:
                value = attr_info.get('value')
                if value == state or str(value).lower() == str(state).lower():
                    aklog_info(f'{device_name}, {feature or domain or "state"} 已切换到 {state} 状态')
                    return True
                if (offset and str(value).isdigit()
                        and int(state) - int(offset) <= int(value) <= int(state) + int(offset)):
                    aklog_info(f'{device_name}, {feature or domain or "state"} 已切换到 {state} 左右，误差: {offset}')
                    return True
                if offset and isinstance(value, list):
                    flag = True
                    for i in range(len(value)):
                        if (int(value[i]) < int(state[i]) - int(offset[i])
                                or int(value[i]) > int(state[i]) + int(offset[i])):
                            flag = False
                            break
                    if flag:
                        aklog_info(f'{device_name}, {feature or domain or "state"} 已切换到 {state} 左右，误差: {offset}')
                        return True
            else:
                unittest_results(
                    [-1, f'userweb检查: 设备 {device_name} 没有找到 {feature or domain or "state"} 属性'])
                return None
            time.sleep(1)
            device_info = self.get_device_info_by_id(device_id)
            continue
        unittest_results(
            [1, f'userweb检查: {device_name}, {feature or domain or "state"} 未切换到 {state} 状态, 超时时间{timeout}秒',
             device_info])
        return False

    def get_device_version(self, device_id):
        """获取设备版本号"""
        device_info = self.get_device_info_by_id(device_id)
        version = device_info.get('version')
        return version

    def wait_device_update_to_version(self, product_model=None, to_version=None, timeout=300, device_name=None):
        """
        等待子设备升级到新版本
        Args:
            product_model (str or list): 可以传入单个，也可以传入多个product_model：比如 [2 Gang Switch, 1 Gang Switch]
            to_version (str): 要升级的目标版本
            timeout (int): 升级一台设备所需要的最长超时时间
            device_name (str or list): 可以指定要升级的设备名称，可以传入多个，list类型
        """
        aklog_info()
        if isinstance(product_model, str):
            product_model = [product_model]

        devices_list = []
        for i in range(2):
            devices_list = self.get_devices_list()
            if devices_list:
                break
            self.ws_connect()

        num = 0
        if product_model:
            num = sum(1 for device in devices_list if device.get('product_model') in product_model)
        elif device_name:
            for device in devices_list:
                if ((isinstance(device_name, str) and device.get('name') == device_name)
                        or (isinstance(device_name, list) and device.get('name') in device_name)):
                    num += 1
        if num < 1:
            aklog_warn(f'当前不存在 {product_model or device_name} 设备')
            return False
        end_time = time.time() + timeout * num
        time.sleep(3)
        while time.time() < end_time:
            devices_list = self.get_devices_list()
            if not devices_list or isinstance(devices_list, bool):
                time.sleep(3)
                continue
            update_results = []
            for device in devices_list:
                if product_model and device.get('product_model') not in product_model:
                    continue
                if device_name and isinstance(device_name, str) and device.get('name') != device_name:
                    continue
                if device_name and isinstance(device_name, list) and device.get('name') not in device_name:
                    continue
                version = device.get('version')
                if str(version) == str(to_version):
                    update_results.append(True)
            if len(update_results) == num:
                aklog_debug(f'所有的 {product_model or device_name} 都已升级到 {to_version} 版本')
                return True
            time.sleep(3)
            continue
        aklog_error(f'有存在部分 {product_model or device_name} 升级 {to_version} 版本失败')
        return False

    def change_switch_type_by_name(self, device_name=None, product_type=None):
        """通过名字切换switch类型"""
        aklog_info()
        device_id = self.get_device_id(device_name)
        data = {
            "device_id": device_id,
            "index": 1,
            "product_type": product_type,
            "type": "config/ak_device/update_switch_type",
        }
        resp = self.ws_send_request(data)
        ret = resp.get('success')
        return ret

    def get_contacts_info(self, regain=True):
        """
        获取联系人信息，设备名称转成设备ID
        return:
        {'Family Group': {
                "id": "r31bc29245772f31ac322ebd876dd39d3",
                "name": "Family Group",
                "group": "user2_room",
                "sip": "",
                "ip": "",
                "mac": "",
                "uuid": "",
                "type": "Group",
                "source": 3,
                "status": 1,
                "intercom": false,
                "video": false,
                "icon": "",
                "first_name": "",
                "last_name": ""
            }
        }
        """
        aklog_info()
        if not regain and self.contacts_info:
            return self.contacts_info
        self.contacts_info.clear()
        data = {
            "mode": 1,
            "type": "homeassistant/contacts_automation",
        }
        resp = self.ws_send_request(data)
        results = resp['result']

        for ret in results:
            contact_name = ret['name']
            self.contacts_info[contact_name] = ret
        # aklog_info(self.contacts_info)
        return self.contacts_info

    def get_contact_name_list(self, regain=True):
        """获取设备名称列表"""
        contacts_info = self.get_contacts_info(regain=regain)
        contact_name_list = []
        for contact_name in contacts_info:
            contact_name_list.append(contact_name)
        aklog_debug('contact_name_list: %s' % contact_name_list)
        return contact_name_list

    def subscribe_device_event(self):
        """
            "type": "subscribe_events"
            "id": 2
            "event_type": 'ak_device_event
        """
        aklog_info()
        data = {
            "type": "subscribe_events",
            "event_type": 'ak_device_event'
        }
        ws_id = self.ws_send_request(data, get_ret=False, return_id=True)
        return ws_id

    def get_device_event_states(self, ws_id, device_id=None, feature=None) -> List[str]:
        """获取设备监听事件状态数据，状态值转为str类型"""
        ws_msgs = self.get_ws_resp_msg(ws_id)
        state_list = []
        for msg in ws_msgs:
            if (msg.get('type') != 'event'
                    or msg.get('id') != ws_id
                    or msg.get('event').get('event_type') != 'ak_device_event'):
                continue
            if device_id and msg.get('event').get('data').get('payload').get('device_id') != device_id:
                continue
            attributes = msg.get('event').get('data').get('payload').get('attributes')
            if feature:
                for attr in attributes:
                    if attr.get('feature') == feature:
                        state_list.append(str(attr.get('value')))
                        break
            else:
                state_list.append(attributes)
        return state_list

    def wait_device_event_to_state(self, ws_id, device_id, feature, *target_states, timeout=10):
        """等待设备收到对应状态的监听事件"""
        aklog_info()
        end_time = time.time() + timeout
        state_list = []
        while time.time() < end_time:
            state_list = self.get_device_event_states(ws_id, device_id, feature)
            if all(str(_state) in state_list for _state in target_states):
                return [True]
            time.sleep(1)
            continue
        return ['warn', f'未获取到设备状态 {target_states} 监听事件', f'device event states: {state_list}']

    def get_area_triggers_info(self, regain=True):
        """
        获取空间触发列表信息
        return:
        {'Living Room':
            {
                "area_id": "r7e0aeacc631e4b6d953abad8ea2e5582",
                "area_name": "Living Room",
                "parent_id": null,
                "parent_name": "",
                "options": [
                    "motion",
                    "temperature",
                    "humidity",
                    "energy",
                    "light",
                    "switch"
                ],
                "climate_info": {}
            }
        }
        """
        aklog_info()
        if not regain and self.area_triggers_info:
            return self.area_triggers_info
        self.area_triggers_info.clear()
        data = {"type": "config/ak_area/triggers"}
        resp = self.ws_send_request(data)
        results = resp['result']

        for ret in results:
            area_name = ret['area_name']
            if not area_name:
                area_name = 'other'
            self.area_triggers_info[area_name] = ret
        return self.area_triggers_info

    def get_area_conditions_info(self, regain=True):
        """
        场景条件，空间信息列表
        { "Living Room":
            {
                "area_id": "r7e0aeacc631e4b6d953abad8ea2e5582",
                "area_name": "Living Room",
                "parent_id": null,
                "parent_name": "",
                "options": [
                    "temperature",
                    "humidity",
                    "energy",
                    "motion",
                    "switch",
                    "light",
                    "door",
                    "curtain",
                    "occupancy",
                    "music"
                ],
                "climate_info": {}
            }
        }
        """
        if not regain and self.area_conditions_info:
            return self.area_conditions_info
        self.area_conditions_info.clear()
        data = {"type": "config/ak_area/conditions"}
        resp = self.ws_send_request(data)
        results = resp['result']
        for ret in results:
            area_name = ret['area_name']
            if not area_name:
                area_name = 'other'
            self.area_conditions_info[area_name] = ret
        return self.area_conditions_info

    def get_area_actions_info(self, regain=True):
        """
        获取场景任务空间执行信息
        {"Living Room":
            {
                "area_id": "r7e0aeacc631e4b6d953abad8ea2e5582",
                "area_name": "Living Room",
                "parent_id": null,
                "parent_name": "",
                "options": [
                    "light",
                    "switch"
                ],
                "climate_info": {}
            }
        }
        """
        aklog_info()
        if not regain and self.area_actions_info:
            return self.area_actions_info
        self.area_actions_info.clear()
        data = {"type": "config/ak_area/actions"}
        resp = self.ws_send_request(data)
        results = resp['result']

        for ret in results:
            area_name = ret['area_name']
            if not area_name:
                area_name = 'other'
            self.area_actions_info[area_name] = ret
        return self.area_actions_info

    def get_device_triggers_info(self, regain=True, key_type='device_name'):
        """
        场景触发，设备列表信息
        key_type: device_id / device_name
        {"fibaro-000001 light":
            {
                "device_id": "883c48e0eb9f4a408e0d30ec6d3be98e",
                "info": [
                    {
                        "platform": "device",
                        "type": "turned_on",
                        "device_id": "883c48e0eb9f4a408e0d30ec6d3be98e",
                        "entity_id": "light.edabbda4898d4d6ab5401d999b776abe",
                        "domain": "light",
                        "entry_name": "fibaro-000001 light-light"
                    },
                    {
                        "platform": "device",
                        "type": "turned_off",
                        "device_id": "883c48e0eb9f4a408e0d30ec6d3be98e",
                        "entity_id": "light.edabbda4898d4d6ab5401d999b776abe",
                        "domain": "light",
                        "entry_name": "fibaro-000001 light-light"
                    },
                    {
                        "platform": "device",
                        "type": "changed_states",
                        "device_id": "883c48e0eb9f4a408e0d30ec6d3be98e",
                        "entity_id": "light.edabbda4898d4d6ab5401d999b776abe",
                        "domain": "light",
                        "entry_name": "fibaro-000001 light-light"
                    }
                ],
                "device_name": "fibaro-000001 light",
                "device_type": "Light",
                "area_id": "r23784b15e4b14613992e1e62f2fa80c7",
                "area_name": "Bedroom2",
                "icon": ""
            }
        }
        """
        aklog_debug()
        if not regain and self.device_triggers_info and self.device_triggers_info.get('key_type') == key_type:
            return self.device_triggers_info
        self.device_triggers_info.clear()
        data = {
            "type": "ak_device_automation/trigger/list",
        }
        resp = self.ws_send_request(data)
        result = resp['result']
        for device in result:
            key = device.get(key_type)
            self.device_triggers_info[key] = device
        self.device_triggers_info['key_type'] = key_type
        return self.device_triggers_info

    def get_device_conditions_info(self, regain=True):
        """
        场景条件，设备信息列表
        {"KS41-D1-US-000001-Dimmer":
            {
                "device_id": "c2825ba5f7794258b80f28398784220c",
                "info": [
                    {
                        "condition": "device",
                        "type": "is_on",
                        "device_id": "c2825ba5f7794258b80f28398784220c",
                        "entity_id": "light.4061e69074004db3820905d195f8e8a6",
                        "domain": "light",
                        "entry_name": ""
                    },
                    {
                        "condition": "device",
                        "type": "is_off",
                        "device_id": "c2825ba5f7794258b80f28398784220c",
                        "entity_id": "light.4061e69074004db3820905d195f8e8a6",
                        "domain": "light",
                        "entry_name": ""
                    }
                ],
                "device_name": "KS41-D1-US-000001-Dimmer",
                "device_type": "dimmer",
                "area_id": "ra3208308cf4e47899d6206d244ad758c",
                "area_name": "CusRoom01.04",
                "icon": ""
            }
        }
        """
        aklog_debug()
        if not regain and self.device_conditions_info:
            return self.device_conditions_info
        self.device_conditions_info.clear()
        data = {"type": "ak_device_automation/condition/list"}
        resp = self.ws_send_request(data)
        results = resp['result']
        for ret in results:
            device_name = ret['device_name']
            self.device_conditions_info[device_name] = ret
        return self.device_conditions_info

    def get_device_actions_info(self, regain=True):
        """
        获取场景任务动作设备信息列表
        {'KS41-D1-US-000001-Dimmer':
            {
                "device_id": "c2825ba5f7794258b80f28398784220c",
                "info": [
                    {
                        "type": "turn_on",
                        "device_id": "c2825ba5f7794258b80f28398784220c",
                        "entity_id": "light.4061e69074004db3820905d195f8e8a6",
                        "domain": "light",
                        "entry_name": ""
                    },
                    {
                        "type": "turn_off",
                        "device_id": "c2825ba5f7794258b80f28398784220c",
                        "entity_id": "light.4061e69074004db3820905d195f8e8a6",
                        "domain": "light",
                        "entry_name": ""
                    },
                    {
                        "type": "toggle",
                        "device_id": "c2825ba5f7794258b80f28398784220c",
                        "entity_id": "light.4061e69074004db3820905d195f8e8a6",
                        "domain": "light",
                        "entry_name": ""
                    },
                    {
                        "device_id": "c2825ba5f7794258b80f28398784220c",
                        "domain": "light",
                        "entity_id": "light.4061e69074004db3820905d195f8e8a6",
                        "type": "brightness"
                    },
                    {
                        "device_id": "c2825ba5f7794258b80f28398784220c",
                        "domain": "light",
                        "entity_id": "light.4061e69074004db3820905d195f8e8a6",
                        "type": "light_flash"
                    }
                ],
                "device_name": "KS41-D1-US-000001-Dimmer",
                "device_type": "dimmer",
                "area_id": "ra3208308cf4e47899d6206d244ad758c",
                "area_name": "CusRoom01.04",
                "icon": ""
            }
        }
        """
        aklog_debug()
        if not regain and self.device_actions_info:
            return self.device_actions_info
        self.device_actions_info.clear()
        data = {"type": "ak_device_automation/action/list"}
        resp = self.ws_send_request(data)
        results = resp['result']
        for ret in results:
            device_name = ret['device_name']
            self.device_actions_info[device_name] = ret
        return self.device_actions_info

    # endregion

    # region Device

    def get_device_id(self, device_name):
        """通过设备名称获取device id"""
        aklog_info()
        devices_id = None
        results = self.get_devices_list()
        for ret in results:
            if device_name == ret['name']:
                devices_id = ret['device_id']
                aklog_info(devices_id)
        return devices_id

    def start_scan_event(self):
        """用户web调用扫描事件订阅接口"""
        resp_get_start_event = self.ws_send_request({
            "event_type": "ak_scan_event",
            "type": "subscribe_events"
        })
        self.ws_id_scan = self.ws_id
        if resp_get_start_event and resp_get_start_event.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp_get_start_event)
            return False

    def stop_scan_event(self):
        """用户web调用关闭扫描订阅接口"""
        resp_get = self.ws_send_request({
            "type": "unsubscribe_events",
            "subscription": self.ws_id_scan - 1
        })
        if resp_get and resp_get.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp_get)
            return False

    def start_scan(self, device_name):
        """开启网关扫描zigbee设备接口"""
        device_id = self.get_device_id(device_name)
        resp_get = self.ws_send_request({
            "type": "config/ak_device/scan",
            "device_id": device_id
        })
        if resp_get and resp_get.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp_get)
            return False

    def stop_scan(self, device_name):
        """关闭网关扫描zigbee设备接口"""
        device_id = self.get_device_id(device_name)
        resp_get = self.ws_send_request({
            "type": "config/ak_device/cancel_scan",
            "device_id": device_id
        })
        if resp_get and resp_get.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp_get)
            return False

    def start_scan_by_type(self, device_name, device_type):
        """按照设备类型添加，开启网关扫描zigbee接口"""
        device_id = self.get_device_id(device_name)
        resp_get = self.ws_send_request({
            "type": "config/ak_device/scan",
            "device_id": device_id,
            "type_name": device_type
        })
        if resp_get and resp_get.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp_get)
            return

    def scan_ecosystem_even(self):
        """用户web调用扫描生态设备事件订阅接口"""
        resp = self.ws_send_request({
            "event_type": "ak_scan_ecosystem_event",
            "type": "subscribe_events"
        })
        self.ws_id_scan_ecosystem = self.ws_id
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def scan_ecosystem_start(self, device_name, device_type):
        """用户web调用开始扫描生态设备的接口"""
        device_id = self.get_device_id(device_name)
        resp = self.ws_send_request({
            "type": "config/ak_device/scan_ecosystem",
            "gateway_device_id": device_id,
            "type_name": device_type
        })
        self.ws_id_scan = self.ws_id
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def stop_ecosystem_even(self):
        """用户web关闭调用扫描生态设备事件订阅接口"""
        resp = self.ws_send_request({
            "type": "unsubscribe_events",
            "subscription": self.ws_id_scan_ecosystem - 1
        })
        self.ws_id_scan = self.ws_id
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def get_display_disable_privilege(self, device_id):
        """获取设备HomePage功能显示/隐藏的权限
        :param device_id: 设备ID。可通过
        :return 设备Display DisableList权限。例如'5;6;8;9'表示默认隐藏了Arming, Energy, Alarm Clock, Timer"""
        resp = self.ws_send_request({"type": "ak_config/get",
                                     "device_id": device_id,
                                     "item": ["settings.DISPLAY.DisableList"]})
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def delete_device(self, device_name=None):
        """
        删除设备
        """
        aklog_info()
        device_id = self.get_device_id(device_name)
        data = {
            "type": "config/ak_device/delete",
            "device_id": device_id
        }
        resp = self.ws_send_request(data)
        if resp and resp['success']:
            return True

    def set_display_disable_privilege(self, device_id=None, device_name=None, disable_list=None):
        """设置设备HomePage功能显示/隐藏的权限
        :param device_id: 设备ID。
        :param device_name: 设备名称。
        :param disable_list: 哪些功能入口需要被禁用。Arming, Energy, Alarm Clock, Timer"""
        if not device_id and device_name:
            device_id = self.get_device_id(device_name)
        func_num_info = {
            'Scene': '2',
            'Contacts': '4',
            'Arming': '5',
            'Energy': '6',
            'Alarm Clock': '8',
            'Timer': '9',
        }
        if disable_list:
            num_list = []
            for func in disable_list:
                num_list.append(func_num_info.get(func))
            disable_list_str = ';'.join(num_list)
        else:
            disable_list_str = ''
        data = {
            "type": "ak_config/update",
            "device_id": device_id,
            "item": {
                "settings.DISPLAY.DisableList": disable_list_str
            }
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def link_output_device(self, device_name, dependent_device_name):
        """
        关联设备
                {
          "type": "call_service",
          "id": 196,
          "domain": "binary_sensor",
          "service": "set_output_device",
          "service_data": {
            "entity_id": "binary_sensor.c20b25030300_281_16_1",
            "output_entity_id": "binary_sensor.c20b25030300_241_15_1",
            "output_device_id": "c20b25030300_241_15"
          }
        }
        """
        aklog_info()
        device_name_entity_id = self.get_devices_entity_id(device_name)
        dependent_device_name_entity_id = self.get_devices_entity_id(dependent_device_name)
        output_device_id = self.get_device_id(dependent_device_name)
        domain = device_name_entity_id.split('.')[0]

        trigger_data = {
            "type": "call_service",
            "domain": domain,
            "service": "set_output_device",
            "service_data": {
                "entity_id": device_name_entity_id,
                "output_entity_id": dependent_device_name_entity_id,
                "output_device_id": output_device_id
            }
        }
        resp = self.ws_send_request(trigger_data)
        ret = resp.get('success')
        aklog_info('关联设备结果：%s' % ret)
        if not ret:
            aklog_debug(f'resp: {resp}')
        return ret

    # endregion

    # region Room Space房间

    def add_room(self, room_name):
        """
        用户web添加房间接口
        Args:
            room_name (str):
        Returns:
            {
                "id": 171,
                "type": "result",
                "success": true,
                "result": {
                    "area_id": "r3565486939294532bd9a366a13ec2475",
                    "name": "ddda",
                    "sort_id": 6,
                    "parent_id": ""
                }
            }
        """
        aklog_info()
        data = {
            "type": "config/ak_area/create",
            "name": room_name
        }
        resp = self.ws_send_request(data)
        aklog_debug(f'resp: {resp}')
        if resp and resp['success']:
            return resp.get('result')
        return None

    def edit_room(self, room_name=None, area_id=None, new_room_name=None):
        """
        修改房间名称
        Args:
            room_name (str):
            area_id (str):
            new_room_name (str):
        Returns:
            {
                "id": 163,
                "type": "result",
                "success": true,
                "result": {
                    "area_id": "r7e051bdca66b4a1b8acaf7687efc651c",
                    "name": "Dinning Room22",
                    "sort_id": 3,
                    "parent_id": ""
                }
            }
        """
        aklog_info()
        if not area_id and room_name:
            room_list = self.get_room_list()
            for room in room_list:
                if room.get('name') == room_name:
                    area_id = room.get('area_id')
        if not area_id:
            aklog_error(f'{room_name} not found')
            return False
        data = {
            "type": "config/ak_area/update",
            "area_id": area_id,
            "name": new_room_name
        }
        resp = self.ws_send_request(data)
        if resp and resp['success']:
            return True
        aklog_error(f'edit room {room_name or area_id} fail')
        aklog_debug(f'resp: {resp}')
        return False

    def get_room_list(self, grep=None):
        """
        获取房间列表
        grep: 可以过滤出room_name
        Returns:
            {
                "id": 173,
                "type": "result",
                "success": true,
                "result": [
                    {
                        "area_id": "rc4dfc7ea2d114a229469d71949ca2411",
                        "name": "Living Room",
                        "sort_id": 1,
                        "parent_id": "",
                        "device_number": 0
                    }
                ]
            }
        """
        data = {
            "type": "config/ak_area/list",
        }
        resp = self.ws_send_request(data)
        if resp and resp['success']:
            room_list = resp.get('result')
            if grep:
                grep_list = [item.get(grep) for item in room_list]
                return grep_list
            return room_list
        aklog_debug(f'resp: {resp}')
        return None

    def delete_room(self, room_name=None, area_id=None):
        """
        删除房间
        Args:
            area_id (str):
            room_name (str):
        Returns:
            {
                "id": 178,
                "type": "result",
                "success": true,
                "result": "success"
            }
        """
        aklog_info()
        if not area_id and room_name:
            room_list = self.get_room_list()
            for room in room_list:
                if room.get('name') == room_name:
                    area_id = room.get('area_id')
        if not area_id:
            aklog_error(f'{room_name} not found')
            return False
        data = {
            "type": "config/ak_area/delete",
            "area_id": area_id
        }
        resp = self.ws_send_request(data)
        if resp and resp['success']:
            return True
        aklog_error(f'delete room {room_name or area_id} fail')
        aklog_debug(f'resp: {resp}')
        return False

    # endregion

    # region 场景相关

    def create_update_scenes(self, triggers=None, conditions=None, tasks=None, scene_name=None, manual=None,
                             scene_id=None, bind_areas=None, generated=False) -> Union[str, None]:
        """
        添加场景
        manual: True / False
        scene_id: 默认为None，使用时间戳来作为scene_id，可以指定scene_id，如果指定scene_id已存在，会修改对应scene_id场景

        trigger 触发: list类型，子元素为字典：
        [{"platform": "device", "device_name": "Relay1", "type": "turned_on"},
        {"platform": "device", "device_name": "CO Sensor", "type": "battery_level", "below": 27},
        {"platform": "time", "at": "00:00", "weekday": ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]},
        {"platform": "state", "entity_id": "automation.home", "to": "on"},
        {"platform": "space", "area_id": "all", "type": "temperature", "status": "below", "value": 20},]

        conditions 条件：list类型，子元素为字典：
        [{"condition": "device", "device_name": "Relay1", "type": "turned_on", "trigger_option": "switch"},
        {"condition": "device", "device_name": "Emergency Sensor", "type": "unsafe",
        "domain": "binary_sensor", "trigger_option": "safety"},
        {"condition": "time", "at": "00:00", "weekday": ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]},
        {"condition": "state", "entity_id": "automation.home", "to": "on"}]

        tasks 执行任务：list类型，子元素为字典：
        [{"device_name": "Relay1", "type": "turn_on"},
        {"delay": { "hours": 0, "minutes": 0, "seconds": 2, "milliseconds": 0}},
        {"send_message": "3232"},
        {"make_call": ["PS51"]},
        {"service": "automation.turn_on", "target": {"entity_id": "automation.home"}},
        {"service": "automation.trigger","target": {"entity_id": "automation.scenes_2"}},
        {"send_http_url": "http://192.168.88.1:18000/trigger"}]
        """
        aklog_info()
        self.clear_scene_needed_info()  # 先清空数据，重新获取，但添加过程只获取一次，相同数据不重复获取
        if not scene_id:
            # 新增场景
            scene_id = str(time.time()).replace('.', '')[0:13]  # 用时间戳来作为scene_id
            if not scene_name:
                scene_name = 'aktest_scene_%s' % uuid.uuid4().hex[-12:]
            image = random.randint(101, 120)
            favorite = False
            if manual is None:
                manual = True
            trigger_list = []
            condition_list = []
            action_list = []
            if bind_areas is None:
                bind_areas = ["all"]
        else:
            # 修改更新场景
            scene_info = self.get_scene_detail_info(scene_id, regain=False)
            if not scene_info:
                raise Exception('scene id error')
            if not scene_name:
                scene_name = scene_info['alias']
            image = scene_info['image_type']
            if manual is None:
                manual = scene_info['manual']
            favorite = scene_info['favorite']
            trigger_list = scene_info.get('trigger')
            condition_list = scene_info.get('condition')
            action_list = scene_info.get('action')
            if bind_areas is None:
                bind_areas = scene_info.get('bind_areas')

        data = {
            "type": "ak_scenes/create_update",
            "scene_id": scene_id,
            "scene_data": {
                "trigger_type": 'or',
                "alias": scene_name,
                "description": "",
                "style": "scene",
                "type": 0,
                "manual": manual,
                "trigger": trigger_list,
                "condition": condition_list,
                "action": action_list,
                "favorite": favorite,
                "mode": "single",
                "image": image,
            }
        }
        if bind_areas is not None and self.ha_version >= 3.001006:
            data['scene_data']['bind_areas'] = bind_areas

        if triggers:
            if isinstance(triggers, dict):
                # 如果传入的不是list，表示为追加
                data['scene_data']['trigger'].append(triggers)
            elif not generated:
                data['scene_data']['trigger'] = self.generate_scenes_trigger_info(triggers)
            else:
                data['scene_data']['trigger'] = triggers

        if conditions:
            if isinstance(conditions, dict):
                # 如果传入的不是list，表示为追加
                data['scene_data']['condition'].append(conditions)
            elif not generated:
                data['scene_data']['condition'] = self.generate_scenes_condition_info(conditions)
            else:
                data['scene_data']['condition'] = conditions

        if tasks:
            if isinstance(tasks, dict):
                # 如果传入的不是list，表示为追加
                data['scene_data']['action'].append(tasks)
            elif not generated:
                data['scene_data']['action'] = self.generate_scenes_task_info(tasks)
            else:
                data['scene_data']['action'] = tasks

        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_debug('create_update_scenes OK')
            self.get_scenes_info(regain=True)
            self.get_scene_detail_info(scene_id, regain=True)
            return scene_id
        else:
            aklog_error('create_update_scenes Fail')
            aklog_debug(f'resp: {resp}')
            return None

    def clear_scene_needed_info(self):
        self.scenes_info.clear()
        self.scenes_list.clear()
        self.scenes_detail_info.clear()
        self.security_info.clear()
        self.security_list.clear()
        self.area_triggers_info.clear()
        self.area_conditions_info.clear()
        self.area_actions_info.clear()
        self.device_triggers_info.clear()
        self.device_conditions_info.clear()
        self.device_actions_info.clear()
        self.contacts_info.clear()

    def _generate_scenes_trigger_device_info(self, **kwargs):
        """
        生成场景触发设备信息
        kwargs:
        {"platform": "device", "device_name": "Relay1", "type": "turned_on"}
        {"platform": "device", "device_name": "CO Sensor", "type": "battery_level", "below": 27}
        return:
        {
            "platform": "device",
            "type": "turned_on",
            "device_id": "20d716fc986a49ae9e648b7ca5dfcebc",
            "entity_id": "switch.22a65989c04d4774b3d20398a1f1ebdf",
            "domain": "switch",
            "entry_name": "1 Gang Switch-000001-switch"
        }
        """
        aklog_debug()
        self.get_device_triggers_info(regain=False)
        device_name = kwargs.get('device_name')
        if not device_name:
            trigger_info_key = list(self.device_triggers_info.keys())
            trigger_info_key.remove('key_type')
            device_name = random.choice(trigger_info_key)

        device_info = self.device_triggers_info[device_name]
        device_attributes = device_info.get('info')
        type_list = [x.get('type') for x in device_attributes]
        _type = kwargs.get('type')
        if not _type:
            _type = random.choice(type_list)

        data = None
        if _type in ['pressed', 'long_pressed']:
            button_index = kwargs.get('button_index')
            if not button_index:
                button_index = random.choice(['button1', 'button2', 'button3', 'button4'])
            for attr in device_attributes:
                if attr.get('type') == _type and button_index == attr.get('button_index'):
                    data = attr
                    break
        else:
            for attr in device_attributes:
                if attr.get('type') == _type:
                    data = attr
                    break

        # 如果有传入指定设备参数，则修改data数据
        keys_to_exclude = ["platform", "device_name", "type"]
        filtered_kwargs = {key: value for key, value in kwargs.items() if key not in keys_to_exclude}
        if filtered_kwargs:
            for key in filtered_kwargs:
                data[key] = filtered_kwargs[key]
        else:
            type_attr = SCENE_TRIGGER_DEVICE_PARAM.get(_type)
            if type_attr:
                if 'status' in type_attr:
                    key = random.choice(type_attr.get('status'))
                    value_range = type_attr.get('value')
                    if key == 'above':
                        value = random.choice(value_range[0:-1])
                    elif key == 'below':
                        value = random.choice(value_range[1:])
                    else:
                        value = random.choice(value_range)
                    data[key] = value

                for attr, _value in type_attr.items():
                    if attr in ['status', 'value']:
                        continue
                    if isinstance(_value, list):
                        data[attr] = random.choice(_value)
                    elif isinstance(_value, dict):
                        for _value_key, _value_value in _value.items():
                            if isinstance(_value_value, list):
                                data[attr][_value_key] = random.choice(_value_value)

        return data

    def _generate_scenes_trigger_space_info(self, **kwargs):
        """
        生成space trigger信息
        可以指定类型，如果都不传入信息，则将随机生成
        kwargs:
        {
            "area_name": "all",
            "type": "temperature",
            "status": "below",
            "value": 20
        }
        """
        aklog_debug()
        self.get_area_triggers_info(regain=False)
        all_options = []
        for area in self.area_triggers_info:
            options = self.area_triggers_info[area].get('options')
            for option in options:
                if option not in all_options:
                    all_options.append(option)

        trig_type = kwargs.get('type')
        area_name = kwargs.get('area_name')
        status = kwargs.get('status')
        value = kwargs.get('value')

        if trig_type and trig_type not in all_options:
            raise Exception('trig_type error')
        if area_name and area_name not in self.area_triggers_info:
            raise Exception('area_name error')

        if not trig_type:
            trig_type = random.choice(all_options)

        # 获取包含有trig_type的房间
        area_id_list = ['all']
        for area in self.area_triggers_info:
            options = self.area_triggers_info[area].get('options')
            if trig_type in options:
                _id = self.area_triggers_info[area].get('area_id')
                if _id and _id not in area_id_list:
                    area_id_list.append(_id)

        if not area_name:
            area_id = random.choice(area_id_list)
        elif area_name == 'all':
            area_id = 'all'
        elif area_name == 'others':
            area_id = 'others'
        else:
            area_id = self.area_triggers_info.get(area_name).get('area_id')
        if not area_id:
            area_id = random.choice(area_id_list)

        def get_random_scene_trigger_space_param(_type):
            param = SCENE_TRIGGER_SPACE_PARAM[_type]
            if 'status_value' in param:
                status, value = random.choice(param['status_value'])
            else:
                status = random.choice(param['status'])
                value_range = param['value']
                if status == 'above':
                    value = random.choice(value_range[0:-1])
                elif status == 'below':
                    value = random.choice(value_range[1:])
                else:
                    value = random.choice(value_range)
            return status, value

        param_status, param_value = get_random_scene_trigger_space_param(trig_type)
        data = {
            "platform": "space",
            "area_id": area_id,
            "type": trig_type,
            "status": param_status,
            "value": param_value
        }

        for attr, _value in SCENE_TRIGGER_SPACE_PARAM[trig_type].items():
            if attr in ['status', 'value', 'status_value']:
                continue
            data[attr] = random.choice(_value)

        if status:
            data['status'] = status
        if value is not None:
            data['value'] = value

        return data

    @staticmethod
    def _generate_scenes_trigger_time_info(**kwargs):
        """
        生成trigger 时间日期
        kwargs:
        {
            "at": "00:00",
            "platform": "time",
            "day": 26
        }
        {
            "platform": "sun",
            "event": "sunset",
            "offset": "0"
        }
        """
        aklog_debug()
        platform = kwargs.get('platform')
        if not platform:
            platform = random.choice(['sun', 'time'])

        if platform == 'time':
            data: Dict[str, Union[str, int]] = {
                "at": "%02d:%02d" % (random.randint(0, 23), random.randint(0, 59)),
                "platform": "time",
            }
            if 'at' in kwargs:
                data['at'] = kwargs.get('at')
            if 'day' not in kwargs and 'weekday' not in kwargs:
                if random.choice(['day', 'weekday']) == 'weekday':
                    data['weekday'] = random.sample(["sun", "mon", "tue", "wed", "thu", "fri", "sat"],
                                                    random.randint(1, 7))
                else:
                    data['day'] = random.randint(1, 28)
            elif 'day' in kwargs:
                data['day'] = kwargs.get('day')
            elif 'weekday' in kwargs:
                data['weekday'] = kwargs.get('weekday')
        else:
            data = {
                "platform": "sun",
                "event": random.choice(['sunrise', 'sunset']),
                "offset": "0"
            }
            event = kwargs.get('event')
            if event:
                data['event'] = event

        return data

    def _generate_scenes_trigger_automation_info(self, **kwargs):
        """
        生成Trigger， 场景控制、布防模式控制
        kwargs:
        {
            "platform": "state",
            "entity_id": "automation.aaaa",
            "from": "off",
            "to": "on"
            "attribute": "is_running",  # or is_alarm
        }
        """
        aklog_debug()
        self.get_scenes_info(regain=False)
        self.get_security_info(regain=False)
        scenes_entity_id_list = [scene['entity_id'] for scene in self.scenes_list]
        security_entity_id_list = [self.security_info[security]['entity_id'] for security in self.security_info]
        entity_id_list = scenes_entity_id_list + security_entity_id_list
        entity_id = kwargs.get('entity_id')
        if not entity_id:
            entity_id = random.choice(entity_id_list)

        to_state = kwargs.get('to')
        if not to_state:
            to_state = random.choice(['on', 'off'])
        if to_state == 'on':
            from_state = 'off'
        else:
            from_state = 'on'

        data = {
            "platform": "state",
            "entity_id": entity_id,
            "from": from_state,
            "to": to_state
        }
        attribute = kwargs.get('attribute')
        if attribute:
            data['attribute'] = attribute
        elif not kwargs.get('entity_id'):
            if entity_id in scenes_entity_id_list:
                attribute_list = ['is_running', None]
            else:
                attribute_list = ['is_alarm', None]
            attribute = random.choice(attribute_list)
            if attribute:
                data['attribute'] = attribute
        return data

    def generate_scenes_trigger_info(self, triggers: list) -> list:
        """
        triggers 触发: list类型，子元素为字典：
        [{"platform": "device", "device_name": "Relay1", "type": "turned_on"},
        {"platform": "device", "device_name": "CO Sensor", "type": "battery_level", "below": 27},
        {"platform": "time", "at": "00:00", "weekday": ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]},
        {"platform": "state", "entity_id": "automation.home", "to": "on"},
        {"platform": "space", "area_id": "all", "type": "temperature", "status": "below", "value": 20},]
        """
        triggers_info = []
        for trigger in triggers:
            info = None
            if trigger['platform'] == 'space':
                info = self._generate_scenes_trigger_space_info(**trigger)
            elif trigger['platform'] == 'device':
                info = self._generate_scenes_trigger_device_info(**trigger)
            elif trigger['platform'] == 'time' or trigger['platform'] == 'sun':
                info = self._generate_scenes_trigger_time_info(**trigger)
            elif trigger['platform'] == 'state':
                info = self._generate_scenes_trigger_automation_info(**trigger)

            if info:
                triggers_info.append(info)
        return triggers_info

    def _generate_scenes_condition_device_info(self, **kwargs):
        """添加场景，条件选择设备，生成设备信息"""
        aklog_debug()
        self.get_device_conditions_info(regain=False)
        device_name = kwargs.get('device_name')
        if not device_name:
            device_name = random.choice(list(self.device_conditions_info.keys()))

        device_info = self.device_conditions_info[device_name]
        device_attributes = device_info.get('info')
        type_list = [x.get('type') for x in device_attributes]
        _type = kwargs.get('type')
        if not _type:
            _type = random.choice(type_list)

        data = None
        for attr in device_attributes:
            if attr.get('type') == _type:
                data = attr
                break

        # 如果有传入指定设备参数，则修改data数据
        keys_to_exclude = ["condition", "device_name", "type"]
        filtered_kwargs = {key: value for key, value in kwargs.items() if key not in keys_to_exclude}
        if filtered_kwargs:
            for key in filtered_kwargs:
                data[key] = filtered_kwargs[key]
        else:
            type_attr = SCENE_CONDITION_DEVICE_PARAM.get(_type)
            if type_attr:
                key = random.choice(type_attr.get('status'))
                value_range = type_attr.get('value')
                if key == 'above':
                    value = random.choice(value_range[0:-1])
                elif key == 'below':
                    value = random.choice(value_range[1:])
                else:
                    value = random.choice(value_range)
                data[key] = value

                for attr, _value in type_attr.items():
                    if attr in ['status', 'value']:
                        continue
                    data[attr] = random.choice(_value)

        return data

    @staticmethod
    def _generate_scenes_condition_time_info(**kwargs):
        """
        生成trigger 时间日期
        kwargs:
        {
            "after": "00:00",
            "before": "00:00",
            "condition": "time",
            "day": 26
        }
        {
            "condition": "sun",
            "before": "sunrise",
            "after": "sunrise"
        }
        """
        aklog_debug()
        condition = kwargs.get('condition')
        if not condition:
            condition = random.choice(['sun', 'time'])

        if condition == 'time':
            data: Dict[str, Union[str, int]] = {
                "after": "00:00",
                "before": "23:59",
                "condition": "time",
            }
            day = kwargs.get('day')
            weekday = kwargs.get('weekday')
            after_day = kwargs.get('after_day')
            before_day = kwargs.get('before_day')

            if not day and not weekday and not after_day:
                time_type = random.choice(['day', 'weekday', 'after_day'])
                if time_type == 'weekday':
                    data['weekday'] = random.sample(["sun", "mon", "tue", "wed", "thu", "fri", "sat"],
                                                    random.randint(1, 7))
                elif time_type == 'day':
                    data['day'] = random.randint(1, 28)
                elif time_type == 'after_day':
                    cur_date = get_os_current_date_time('%Y-%m-%d')
                    data['after_day'] = cur_date
                    data['before_day'] = get_date_add_delta(cur_date, 1, '%Y-%m-%d')
            elif day:
                data['day'] = day
            elif weekday:
                data['weekday'] = weekday
            elif after_day:
                data['after_day'] = after_day
                data['before_day'] = before_day
        else:
            data = {
                "condition": "sun",
                "before": random.choice(['sunset', 'sunrise']),
                "after": random.choice(['sunset', 'sunrise'])
            }

        after = kwargs.get('after')
        if after:
            data['after'] = after
        before = kwargs.get('before')
        if before:
            data['before'] = before

        return data

    @staticmethod
    def _generate_scenes_condition_weather_info(**kwargs):
        """
        生成场景条件，天气信息
        kwargs:
        {'condition': 'weather', 'type', 'weather', 'equal': 'sunny'}
        return:
        {
            "condition": "weather",
            "type": "weather",
            "equal": "sunny"
        }
        """
        aklog_debug()
        _type = kwargs.get('type')
        if not _type:
            _type = random.choice(['weather', 'temperature', 'humidity', 'aqi'])
        data = {
            "condition": "weather",
            "type": _type,
        }
        if _type == 'weather':
            if kwargs.get('equal'):
                data['equal'] = kwargs.get('equal')
            else:
                data['equal'] = random.choice(['sunny', 'cloudy', 'rainy', 'snowy', 'foggy'])
        else:
            type_attr = SCENE_CONDITION_WEATHER_PARAM.get(_type)
            if type_attr:
                key = random.choice(type_attr.get('status'))
                value_range = type_attr.get('value')
                if key == 'above':
                    value = random.choice(value_range[0:-1])
                elif key == 'below':
                    value = random.choice(value_range[1:])
                else:
                    value = random.choice(value_range)
                data[key] = value

        return data

    def _generate_scenes_condition_space_info(self, **kwargs):
        """
        添加场景，条件选择空间，生成空间信息
        kwargs:
        {
            "area_name": "all",
            "type": "is_temperature",
            "status": "below",
            "value": 20
        }
        """
        aklog_debug()
        self.get_area_conditions_info(regain=False)
        all_options = []
        for area in self.area_conditions_info:
            options = self.area_conditions_info[area].get('options')
            for option in options:
                if option not in all_options:
                    all_options.append(option)

        _type = kwargs.get('type')
        area_name = kwargs.get('area_name')

        if _type and _type not in all_options:
            raise Exception('trig_type error')
        if area_name and area_name not in self.area_conditions_info:
            raise Exception('area_name error')

        if not _type:
            _type = random.choice(all_options)

        # 获取包含有_type的房间
        area_id_list = ['all']
        for area in self.area_conditions_info:
            options = self.area_conditions_info[area].get('options')
            if _type in options:
                _id = self.area_conditions_info[area].get('area_id')
                if _id and _id not in area_id_list:
                    area_id_list.append(_id)

        if not area_name:
            area_id = random.choice(area_id_list)
        elif area_name == 'all':
            area_id = 'all'
        elif area_name == 'others':
            area_id = 'others'
        else:
            area_id = self.area_conditions_info.get(area_name).get('area_id')
        if not area_id:
            area_id = random.choice(area_id_list)
        data = {
            "condition": "space",
            "area_id": area_id,
            "type": _type,
            "status": None,
            "value": None
        }

        type_attr = SCENE_CONDITION_SPACE_MAP[_type]
        data['status'] = random.choice(type_attr['status'])
        value_range = type_attr['value']
        if data['status'] == 'above':
            data['value'] = random.choice(value_range[0:-1])
        elif data['status'] == 'below':
            data['value'] = random.choice(value_range[1:])
        else:
            data['value'] = random.choice(value_range)

        for attr, _value in SCENE_CONDITION_SPACE_MAP[_type].items():
            if attr in ['status', 'value']:
                continue
            data[attr] = random.choice(_value)

        if kwargs.get('status'):
            data['status'] = kwargs.get('status')
        if kwargs.get('value') is not None:
            data['value'] = kwargs.get('value')

        return data

    def _generate_scenes_condition_automation_info(self, **kwargs):
        """
        生成condition， 场景控制、布防模式控制
        kwargs:
        {
            "condition": "state",
            "entity_id": "automation.aaaa",
            "state": "off",
            "attribute": "is_alarm"
        }
        """
        aklog_debug()
        self.get_scenes_info(regain=False)
        self.get_security_info(regain=False)
        scenes_entity_id_list = [scene['entity_id'] for scene in self.scenes_list]
        security_entity_id_list = [self.security_info[security]['entity_id'] for security in self.security_info]
        entity_id_list = scenes_entity_id_list + security_entity_id_list
        entity_id = kwargs.get('entity_id')
        if not entity_id:
            entity_id = random.choice(entity_id_list)

        state = kwargs.get('state')
        if not state:
            state = random.choice(['on', 'off'])

        data = {
            "condition": "state",
            "entity_id": entity_id,
            "state": state,
        }
        attribute = kwargs.get('attribute')
        if attribute:
            data['attribute'] = attribute
        elif not kwargs.get('entity_id'):
            if entity_id in security_entity_id_list:
                attribute_list = ['is_alarm', None]
                attribute = random.choice(attribute_list)
                if attribute:
                    data['attribute'] = attribute
        return data

    def generate_scenes_condition_info(self, conditions: list) -> list:
        """
        conditions：list类型，子元素为字典：
        [{"condition": "device", "device_name": "Relay1", "type": "turned_on"},
        {"condition": "device", "device_name": "Emergency Sensor", "type": "unsafe"},
        {"condition": "time", "at": "00:00", "weekday": ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]},
        {"condition": "state", "entity_id": "automation.home", "to": "on"}]
        """
        conditions_info = []
        for condition in conditions:
            info = None
            if condition['condition'] == 'device':
                info = self._generate_scenes_condition_device_info(**condition)
            elif condition['condition'] == 'time' or condition['condition'] == 'sun':
                info = self._generate_scenes_condition_time_info(**condition)
            elif condition['condition'] == 'weather':
                info = self._generate_scenes_condition_weather_info(**condition)
            elif condition['condition'] == 'space':
                info = self._generate_scenes_condition_space_info(**condition)
            elif condition['condition'] == 'state':
                info = self._generate_scenes_condition_automation_info(**condition)

            if info:
                conditions_info.append(info)
        return conditions_info

    def _generate_scenes_task_device_info(self, **kwargs):
        """
        添加场景，任务选择设备，生成设备信息
        {'action': 'device', 'device_name': 'xxx', 'type': 'turn_on',}
        """
        aklog_debug()
        self.get_device_actions_info(regain=False)
        device_name = kwargs.get('device_name')
        if not device_name:
            device_name = random.choice(list(self.device_actions_info.keys()))

        device_info = self.device_actions_info[device_name]
        device_attributes = device_info.get('info')
        # print(device_attributes)
        _type = kwargs.get('type')
        if not _type:
            type_list = [x.get('type') for x in device_attributes]
            _type = random.choice(type_list)

        data = None
        for attr in device_attributes:
            if attr.get('type') == _type:
                data = attr
                break

        # 如果有传入指定设备参数，则修改data数据
        keys_to_exclude = ["action", "device_name", "type"]
        filtered_kwargs = {key: value for key, value in kwargs.items() if key not in keys_to_exclude}
        if filtered_kwargs:
            for key in filtered_kwargs:
                data[key] = filtered_kwargs[key]
        else:
            type_attr = SCENE_ACTION_DEVICE_PARAM.get(_type)
            if type_attr:
                for attr, value_range in type_attr.items():
                    data[attr] = random.choice(value_range)
            else:
                # 有些设备（比如Climate）可以同时设置多个参数
                if _type == 'multi_ctrl' and 'options' in data:
                    action_options = []
                    multi_options = []
                    for option in data['options']:
                        if not option.startswith('set_'):
                            action_options.append(option)
                        else:
                            multi_options.append(option)
                    action_option = random.choice(action_options)
                    data['action'] = action_option

                    multi_options_select = random.sample(multi_options, random.randint(0, len(multi_options)))
                    for set_option in multi_options_select:
                        option_name = set_option.replace('set_', '')
                        option_range_name = option_name + 's'
                        option_range = data.get(option_range_name)
                        if not option_range:
                            continue
                        option_select = random.choice(option_range)
                        data[option_name] = option_select

        return data

    def _generate_scenes_task_space_info(self, **kwargs):
        """
        场景任务，生成空间任务信息
        kwargs:
        {'action': 'space', 'area_name': 'all', 'type': 'switch',}
        """
        aklog_debug()
        self.get_area_actions_info(regain=False)
        all_options = []
        for area in self.area_actions_info:
            options = self.area_actions_info[area].get('options')
            for option in options:
                if option not in all_options:
                    all_options.append(option)

        _type = kwargs.get('type')
        area_name = kwargs.get('area_name')

        if _type and _type not in all_options:
            raise Exception('trig_type error')
        if area_name and area_name not in self.area_actions_info:
            raise Exception('area_name error')

        if not _type:
            _type = random.choice(all_options)

        # 获取包含有_type的房间
        area_id_list = ['all']
        for area in self.area_actions_info:
            options = self.area_actions_info[area].get('options')
            if _type in options:
                _id = self.area_actions_info[area].get('area_id')
                if _id and _id not in area_id_list:
                    area_id_list.append(_id)

        if not area_name:
            area_id = random.choice(area_id_list)
        elif area_name == 'all':
            area_id = 'all'
        elif area_name == 'others':
            area_id = 'others'
        else:
            area_id = self.area_actions_info.get(area_name).get('area_id')
        if not area_id:
            area_id = random.choice(area_id_list)

        action = kwargs.get('action')
        if not action or action == 'space':
            action = random.choice(SCENE_ACTION_SPACE_MAP.get(_type).get('action'))

        data = {
            "space_control": {
                "area_id": area_id,
                "type": _type,
                "action": action,
            }
        }

        for attr, _value in SCENE_ACTION_SPACE_MAP[_type].items():
            if attr in ['action']:
                continue
            if ':' in attr:
                action_type, key = attr.split(':')
                if action_type == action:
                    data['space_control'][key] = random.choice(_value)
            else:
                data['space_control'][attr] = random.choice(_value)

        return data

    def _generate_scenes_task_message_info(self, **kwargs):
        """
        kwargs:
        {'action': 'message', 'message': 'xxx', 'targets': ['xxx', 'xxx']}
        """
        aklog_debug()
        contact_name_list = self.get_contact_name_list(regain=False)
        message = kwargs.get('message')
        if not message:
            message = generate_random_string(random.randint(1, 500))
        targets = kwargs.get('targets')
        if not targets:
            targets = random.sample(contact_name_list, random.randint(1, len(contact_name_list)))

        target_ids = []
        for contact_name in targets:
            if contact_name in self.contacts_info:
                _id = self.contacts_info[contact_name].get('id')
                if _id not in target_ids:
                    target_ids.append(_id)

        data = {
            "send_message": message,
            "target_ids": target_ids
        }
        return data

    def _generate_scenes_task_call_info(self, **kwargs):
        """
        呼叫列表，设备名称转成设备ID
        {'action': 'call', 'targets': ['xxx', 'xxx']}
        """
        self.get_contacts_info(regain=False)
        targets = kwargs.get('targets')
        if targets:
            make_call_ids = []
            for contact in targets:
                if contact in self.contacts_info:
                    _id = self.contacts_info[contact]['id']
                    if _id not in make_call_ids:
                        make_call_ids.append(_id)
        else:
            contact_num = random.randint(0, len(self.contacts_info))
            make_call_ids = []
            for contact in self.contacts_info:
                _id = self.contacts_info[contact]['id']
                if _id not in make_call_ids:
                    make_call_ids.append(_id)
                if len(make_call_ids) >= contact_num:
                    break

        data = {"make_call": make_call_ids}
        return data

    @staticmethod
    def _generate_scenes_task_notification_info(**kwargs):
        """
        {'action': 'notification', 'notification': 'xxx'}
        """
        aklog_debug()
        notification = kwargs.get('notification')
        if not notification:
            notification = generate_random_string(random.randint(1, 500))
        data = {"send_notification": notification}
        return data

    def _generate_scenes_task_scene_control_info(self, **kwargs):
        """
        {'action': 'scene', 'service': 'turn_on', 'target': 'xxx'}
        service: trigger, turn_on, turn_off
        """
        aklog_debug()
        self.get_scenes_info(regain=False)
        scenes_entity_id_list = [scene['entity_id'] for scene in self.scenes_list]
        target = kwargs.get('target')
        if not target:
            if not scenes_entity_id_list:
                return None
            target = random.choice(scenes_entity_id_list)
        elif not target.startswith('automation.') and target in self.scenes_info:
            # 如果target开头不是automation.，则当成场景名称
            target = self.scenes_info.get(target).get('entity_id')

        service = kwargs.get('service')
        if not service:
            service = random.choice(['trigger', 'turn_on', 'turn_off'])
        if not service.startswith('automation.'):
            service = 'automation.' + service

        data = {
            "service": service,
            "target": {
                "entity_id": target
            }
        }
        return data

    def _generate_scenes_task_security_control_info(self, **kwargs):
        """
        {'action': 'security', 'service': 'turn_off', 'target': 'xxx'}
        """
        aklog_debug()
        self.get_security_info(regain=False)
        security_entity_id_list = [self.security_info[security]['entity_id'] for security in self.security_info]
        target = kwargs.get('target')
        if not target:
            target = random.choice(security_entity_id_list)
        elif not target.startswith('automation.') and target in self.security_info:
            # 如果target开头不是automation.，则当成安防名称
            target = self.security_info.get(target).get('entity_id')

        service = kwargs.get('service')
        if not service:
            service = random.choice(['turn_on', 'turn_off'])
        if not service.startswith('automation.'):
            service = 'automation.' + service

        data = {
            "service": service,
            "data": {
                "entity_id": target
            }
        }
        return data

    @staticmethod
    def _generate_scenes_task_http_info(**kwargs):
        """
        {'action': 'http', 'url': 'http://xxx'}
        """
        aklog_debug()
        url = kwargs.get('url')
        if not url:
            url = 'http://%s' % generate_random_string(length=random.randint(3, 32), language='en_num')
        data = {
            "send_http_url": url
        }
        return data

    @staticmethod
    def _generate_scenes_task_delay_info(**kwargs):
        """
        {'action': 'delay', 'delay': 30}
        """
        aklog_debug()
        seconds = kwargs.get('delay')
        if not seconds:
            seconds = random.randint(1, 10000)
        else:
            seconds = float(seconds)
        hours = int(seconds // 3600)
        seconds %= 3600
        minutes = int(seconds // 60)
        seconds %= 60

        data = {
            "delay": {
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
                "milliseconds": 0
            }
        }
        return data

    def generate_scenes_task_info(self, tasks: list) -> list:
        """
        tasks 执行任务：list类型，子元素为字典：
        [{"device_name": "Relay1", "type": "turn_on"},
        {"delay": { "hours": 0, "minutes": 0, "seconds": 2, "milliseconds": 0}},
        {"send_message": "3232"},
        {"make_call": ["PS51"]},
        {"service": "automation.turn_on", "target": {"entity_id": "automation.home"}},
        {"service": "automation.trigger","target": {"entity_id": "automation.scenes_2"}},
        {"send_http_url": "http://192.168.88.1:18000/trigger"}]
        """
        actions_info = []
        for task in tasks:
            info = None
            if task.get('action') == 'space' or task.get('task') == 'space':
                info = self._generate_scenes_task_space_info(**task)
            elif task['action'] == 'call':
                info = self._generate_scenes_task_call_info(**task)
            elif task['action'] == 'message':
                info = self._generate_scenes_task_message_info(**task)
            elif task['action'] == 'device':
                info = self._generate_scenes_task_device_info(**task)
            elif task['action'] == 'notification':
                info = self._generate_scenes_task_notification_info(**task)
            elif task['action'] == 'scene':
                info = self._generate_scenes_task_scene_control_info(**task)
            elif task['action'] == 'security':
                info = self._generate_scenes_task_security_control_info(**task)
            elif task['action'] == 'http':
                info = self._generate_scenes_task_http_info(**task)
            elif task['action'] == 'delay':
                info = self._generate_scenes_task_delay_info(**task)

            if info:
                actions_info.append(info)
        return actions_info

    def get_scenes_info(self, regain=True):
        """
        获取当前所有场景信息
        return:
        {'111':
            {'type': 0, 'image_type': 103, 'is_auto': True, 'manual': False, 'favorite': False,
            'scene_id': '1666943802163', 'name': '111', 'trigger_type': 'or', 'entity_id': 'automation.111',
             'auto_enabled': True, 'online': True, 'id': '1666943802163', 'alias': '111',
             'trigger': [{'platform': 'device', 'type': 'turned_on', 'device_id': 'd6c37f4bcfdfabb80d2c9430da2ef7d0c',
             'entity_id': 'switch.e85a27d19a5d795ef3475358b746e831a', 'domain': 'switch'}],
             'condition': [],
             'action': [{'send_http_url': '111'}]}
         }
        """
        aklog_info()
        if not regain and self.scenes_info:
            return self.scenes_info
        self.scenes_info.clear()
        scenes_list = self.get_scenes_list(regain=regain)
        for scene in scenes_list:
            name = scene['name']
            self.scenes_info[name] = scene
        return self.scenes_info

    def get_scene_info_by_name(self, by_scenes_name):
        """
        获取指定场景信息
        """
        aklog_info()
        self.get_scenes_info()
        scene_id = self.scenes_info[by_scenes_name]['scene_id']
        scene_info = self.get_scene_detail_info(scene_id)
        aklog_debug(scene_info)
        return scene_info

    def get_scenes_list(self, regain=True, grep=None) -> list:
        """
        获取当前所有场景信息
        return:
        [{'type': 0, 'image_type': 103, 'is_auto': True, 'manual': False, 'favorite': False,
            'scene_id': '1666943802163', 'name': '111', 'trigger_type': 'or', 'entity_id': 'automation.111',
             'auto_enabled': True, 'online': True, 'id': '1666943802163', 'alias': '111',
             'trigger': [{'platform': 'device', 'type': 'turned_on', 'device_id': 'd6c37f4bcfdfabb80d2c9430da2ef7d0c',
             'entity_id': 'switch.e85a27d19a5d795ef3475358b746e831a', 'domain': 'switch'}],
             'condition': [],
             'action': [{'send_http_url': '111'}]}]
        """
        if regain:
            self.scenes_list.clear()
        if not self.scenes_list:
            data = {"type": "ak_scenes/info"}
            resp = self.ws_send_request(data)
            if resp and resp.get('success'):
                self.scenes_list = resp['result']
            else:
                aklog_error('get_security_list Fail')
                return []
        if grep:
            grep_list = []
            for scene in self.scenes_list:
                if grep in scene:
                    grep_list.append(scene.get(grep))
            return grep_list
        return self.scenes_list

    def get_scenes_name_list(self):
        """
        获取当前所有场景名字的集合
        return:
        """
        scenes = self.get_scenes_list()
        return {scene.get('name') for scene in scenes}

    def clear_scenes_list(self):
        self.scenes_list.clear()

    def get_scene_detail_info(self, scene_id, regain=True):
        """
        获取场景详情信息
        Args:
            scene_id (str):
            regain (bool):
        Returns:
            {
            "1728699809215": {
                "type": 0,
                "image_type": 118,
                "is_auto": false,
                "manual": true,
                "favorite": false,
                "id": "1728699809215",
                "alias": "turn off",
                "trigger": [],
                "condition": [],
                "action": [
                    {
                        "space_control": {
                            "area_id": "all",
                            "type": "light",
                            "action": "off"
                        }
                    },
                    {
                        "type": "turn_on",
                        "device_id": "e94e6137a0c1453baa17ff156e938d15",
                        "entity_id": "switch.cde8acd926f243968765582e6ae26108",
                        "domain": "switch",
                        "entry_name": "Smart Plug-000001-switch"
                    }
                ],
                "trigger_type": "or",
                "canvas_pos": "",
                "style": "scene",
                "support_long_press": false
            }
        }
        """
        if not regain and self.scenes_detail_info and scene_id in self.scenes_detail_info:
            return self.scenes_detail_info[scene_id]
        data = {
            "type": "ak_scenes/get",
            "scene_id": scene_id
        }
        resp = self.ws_send_request(data)
        scene_info = resp['result']
        self.scenes_detail_info[scene_id] = scene_info
        return scene_info

    def clear_scene_detail_info(self):
        self.scenes_detail_info.clear()

    def edit_scenes(self, by_scenes_name, new_scenes_name, trigger_type=None, manual=None, conditions=None, tasks=None):
        """
        弃用，编辑场景，通过scenes_name获取对应的scene_id
        by_scenes_name: 原先的场景名称
        new_scenes_name：修改后的场景名称
        trigger_type: or / and
        manual: True / False

        conditions 条件：list类型，子元素为字典：
        [{"platform": "device", "device_name": "Relay1", "type": "turned_on"},
        {"platform": "time", "at": "00:00", "weekday": [ "sun", "mon", "tue", "wed", "thu", "fri", "sat"]},
        {"platform": "state", "entity_id": "automation.home", "to": "on"}]

        tasks 执行任务：list类型，子元素为字典：
        [{"device_name": "Relay1", "type": "turn_on",},
        {"delay": { "hours": 0, "minutes": 0, "seconds": 2, "milliseconds": 0}},
        {"send_message": "3232"},
        {"make_call": ["PS51"]},
        {"service": "automation.turn_on", "target": {"entity_id": "automation.home"}},
        {"service": "automation.trigger","target": {"entity_id": "automation.scenes_2"}},
        {"send_http_url": "232323"}]
        """
        aklog_info()
        self.get_scenes_info()
        if by_scenes_name in self.scenes_info:
            scene_id = self.scenes_info[by_scenes_name]['scene_id']
            if manual is None:
                manual = self.scenes_info[by_scenes_name]['manual']
            if trigger_type is None:
                trigger_type = self.scenes_info[by_scenes_name]['trigger_type']
            if conditions is None:
                conditions = self.scenes_info[by_scenes_name]['trigger']
            if tasks is None:
                tasks = self.scenes_info[by_scenes_name]['action']
            self.create_update_scenes(new_scenes_name, trigger_type, manual, conditions, tasks, scene_id)
        else:
            aklog_info('场景 %s 不存在' % by_scenes_name)

    def delete_scenes(self, *scenes_name):
        """删除场景，通过场景名称获取scene_id"""
        aklog_info()
        self.get_scenes_info()
        scene_id_list = []
        for name in scenes_name:
            if name in self.scenes_info:
                scene_id = self.scenes_info[name]['scene_id']
                scene_id_list.append(scene_id)

        fail_list = []
        for scene_id in scene_id_list:
            data = {
                "type": "ak_scenes/delete",
                "scene_id": scene_id,
            }
            resp = self.ws_send_request(data)
            time.sleep(1)
            if not resp or not resp.get('success'):
                fail_list.append(scene_id)
            else:
                if scene_id in self.scenes_detail_info:
                    del self.scenes_detail_info[scene_id]
        if len(fail_list) > 0:
            aklog_warn(f'有场景删除失败: {fail_list}')
            return False
        else:
            return True

    def delete_scenes_by_contain_name(self, contain_name):
        """删除场景，通过场景名称获取scene_id"""
        aklog_info()
        self.get_scenes_list(True)
        scene_id_list = []
        for scene in self.scenes_list:
            if contain_name in scene.get('name'):
                scene_id_list.append(scene['scene_id'])

        fail_list = []
        for scene_id in scene_id_list:
            data = {
                "type": "ak_scenes/delete",
                "scene_id": scene_id,
            }
            resp = self.ws_send_request(data)
            time.sleep(1)
            if not resp or not resp.get('success'):
                fail_list.append(scene_id)
            else:
                if scene_id in self.scenes_detail_info:
                    del self.scenes_detail_info[scene_id]
        if len(fail_list) > 0:
            aklog_warn(f'有场景删除失败: {fail_list}')
            return False
        else:
            return True

    def delete_scenes_by_id(self, *ids):
        aklog_info()
        fail_list = []
        for scene_id in ids:
            data = {
                "type": "ak_scenes/delete",
                "scene_id": scene_id,
            }
            resp = self.ws_send_request(data)
            time.sleep(1)
            if not resp or not resp.get('success'):
                fail_list.append(scene_id)
        if len(fail_list) > 0:
            return False
        else:
            return True

    def delete_all_scenes(self):
        """删除所有场景"""
        aklog_info()
        self.get_scenes_info()
        for scene_name in self.scenes_info:
            scene_id = self.scenes_info[scene_name]['scene_id']
            data = {
                "type": "ak_scenes/delete",
                "scene_id": scene_id,
            }

            self.ws_send_request(data)

    def delete_amount_scenes(self, amount):
        """删除指定数量场景"""
        aklog_info()
        count = 0
        self.get_scenes_info()
        for scene_name in self.scenes_info:
            if count >= amount:
                break
            scene_id = self.scenes_info[scene_name]['scene_id']
            data = {
                "type": "ak_scenes/delete",
                "scene_id": scene_id,
            }

            self.ws_send_request(data)
            count += 1

    def manual_trigger_scene(self, scene_name=None, scene_index=1, scene_id=None):
        """
        手动触发场景执行
        scene_name不为None时，使用名称来选择场景操作，否则使用序号index来选择场景
        """
        aklog_info()
        self.get_scenes_info()
        entity_id = None
        if not scene_name and not scene_id:
            entity_id = self.scenes_list[scene_index - 1]['entity_id']
        elif scene_name and scene_name in self.scenes_info:
            entity_id = self.scenes_info[scene_name]['entity_id']
        elif scene_id:
            for scene in self.scenes_list:
                if scene.get('scene_id') == scene_id:
                    entity_id = scene.get('entity_id')
                    break

        if not entity_id:
            aklog_error('场景不存在')
            return False
        trigger_data = {
            "type": "call_service",
            "domain": "automation",
            "service": "trigger",
            "service_data": {
                "entity_id": entity_id,
                "skip_condition": False
            }
        }
        resp = self.ws_send_request(trigger_data)
        ret = resp.get('success')
        aklog_info('手动触发场景执行结果：%s' % ret)
        if not ret:
            aklog_debug(f'resp: {resp}')
        return ret

    def get_all_manual_scene_ids(self):
        self.get_scenes_list()
        scene_ids = []
        for scene in self.scenes_list:
            if scene.get('manual') is True:
                scene_ids.append(scene.get('scene_id'))
        return scene_ids

    def get_all_manual_scene_names(self):
        self.get_scenes_list()
        scene_names = []
        for scene in self.scenes_list:
            if scene.get('manual') is True:
                scene_names.append(scene.get('name'))
        return scene_names

    def set_auto_scene_enable(self, scene_name, enable=1):
        """
        开启关闭自动化场景
        enable: 1 / 0，或者 True / False
        """
        aklog_info()
        self.get_scenes_info()
        if scene_name not in self.scenes_info:
            aklog_info('场景 %s 不存在' % scene_name)
            return False
        entity_id = self.scenes_info[scene_name]['entity_id']
        if str(enable) == '1' or enable is True:
            service = 'turn_on'
        else:
            service = 'turn_off'
        set_scene_data = {"type": "call_service", "domain": "automation", "service": service,
                          "service_data": {"entity_id": entity_id}, "id": 37}
        resp = self.ws_send_request(set_scene_data)
        aklog_info('设置场景 %s %s 结果： %s' % (scene_name, service, resp.get('success')))
        if not resp.get('success'):
            aklog_info(resp)
        return resp.get('success')

    def get_scenes_record(self, start_time=None, end_time=None, grep=None) -> Optional[list]:
        """
        获取场景执行记录
        start_time, end_time：格式：%Y-%m-%d %H:%M:%S
        grep: 只返回指定属性列表，比如传入scene_id，只返回scene_id列表
        return:
        [{'record_id': 19, 'scene_id': '1666943852714', 'name': '333', 'result': True,
        'start_time': '2022-10-28 18:21:35', 'finish_time': '2022-10-28 18:21:35', 'trigger_type': 0, 'data': {}}]
        """
        aklog_debug()
        if not start_time and not end_time:
            cur_date = get_os_current_date_time('%Y-%m-%d')
            cur_time = get_os_current_date_time('%H:%M:%S')
            start_time = '%s %s' % (get_date_add_delta(cur_date, -90), cur_time)
            end_time = '%s %s' % (cur_date, cur_time)
        data = {
            "type": "ak_scenes/record_datetime",
            "style": "scene",
            "start_datetime": start_time,
            "end_datetime": end_time
        }
        resp = self.ws_send_request(data)
        scenes_record = resp.get('result')
        if scenes_record:
            if grep:
                record_grep_list = []
                for record in scenes_record:
                    if record.get(grep):
                        record_grep_list.append(record.get(grep))
                return record_grep_list
            return scenes_record
        return None

    def update_scene_ws(self, scene_name):
        """websocket方式更新场景接口"""
        scene_id = None
        for scene in self.get_scenes_info():
            if scene["name"] == scene_name:
                scene_id = scene["scene_id"]
        resp = self.ws_send_request({
            "type": "ak_scenes/create_update",
            "scene_id": scene_id,
            "scene_data": {
                "type": 0,
                "manual": True,
                "favorite": False,
                "id": scene_id,
                "alias": "222",
                "trigger": [],
                "condition": [],
                "action": [
                    {
                        "delay": {
                            "hours": 0,
                            "milliseconds": 0,
                            "minutes": 0,
                            "seconds": 5
                        }
                    }
                ],
                "trigger_type": "or",
                "canvas_pos": "",
                "style": "scene",
                "support_long_press": False,
                "image": 114
            }
        })
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def add_time_scene(self):
        """websocket方式更创建日出的定时场景"""
        resp = self.ws_send_request({
            "type": "ak_scenes/create_update",
            "scene_id": "1703943436199",
            "scene_data": {
                "trigger_type": "or",
                "alias": "time",
                "description": "",
                "style": "scene",
                "type": 0,
                "manual": False,
                "trigger": [
                    {
                        "platform": "sun",
                        "event": "sunrise",
                        "offset": "0"
                    }
                ],
                "condition": [],
                "action": [
                    {
                        "send_notification": "sun rise time"
                    }
                ],
                "favorite": False,
                "mode": "single",
                "image": 103
            }
        })
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def get_scene_action_devices(self, scene_id=None, scene_name=None) -> Optional[list]:
        """获取场景task任务的控制设备信息"""
        if not scene_id and scene_name:
            scenes_list = self.get_scenes_list()
            for scene in scenes_list:
                if scene['name'] == scene_name:
                    scene_id = scene['scene_id']
                    break
        if not scene_id:
            aklog_warn(f'场景 {scene_name or scene_id} 未找到')
            return None
        scene_info = self.get_scene_detail_info(scene_id, regain=False)
        actions = scene_info.get('action')
        device_actions = []
        for action in actions:
            if 'device_id' in action and 'entity_id' in action:
                device_actions.append(action)
        return device_actions

    def get_scene_action_space_controls(self, scene_id):
        """获取场景task任务的空间控制设备信息"""
        scene_info = self.get_scene_detail_info(scene_id, regain=False)
        actions = scene_info.get('action')
        space_controls = []
        for action in actions:
            if 'space_control' in action:
                space_controls.append(action['space_control'])
        return space_controls

    def get_scene_action_sub_scene_ids(self, scene_id=None, scene_name=None) -> Optional[list]:
        """
        获取场景触发后，执行其他场景的id信息，只获取当前场景的子场景，不递归获取
        Args:
            scene_id (str):
            scene_name (str):
        """
        if not scene_id and scene_name:
            scenes_list = self.get_scenes_list(regain=False)
            for scene in scenes_list:
                if scene['name'] == scene_name:
                    scene_id = scene['scene_id']
                    break
        if not scene_id:
            aklog_warn(f'场景 {scene_name or scene_id} 未找到')
            return None
        scene_info = self.get_scene_detail_info(scene_id, regain=False)
        actions = scene_info.get('action')
        target_entity_id_list = []
        for action in actions:
            if 'service' in action and 'target' in action:
                target_entity_id_list.append(action['target']['entity_id'])
        sub_scene_ids = []
        scenes_list = self.get_scenes_list(regain=False)
        for scene in scenes_list:
            if scene['entity_id'] in target_entity_id_list:
                sub_scene_ids.append(scene['scene_id'])
        if sub_scene_ids:
            aklog_debug(f'场景 {scene_name or scene_id} 包含子场景: {sub_scene_ids}')
        return sub_scene_ids

    def get_scene_action_all_scene_ids(
            self, scene_id=None, scene_name=None, scene_ids=None, print_log=True) -> list:
        """
        递归获取场景任务执行其他场景id信息，包括自身
        Args:
            scene_id (str):
            scene_name (str):
            scene_ids (list):
            print_log (bool):
        """
        if not scene_id and scene_name:
            scenes_list = self.get_scenes_list(regain=False)
            for scene in scenes_list:
                if scene['name'] == scene_name:
                    scene_id = scene['scene_id']
                    break
        if not scene_id:
            aklog_warn(f'场景 {scene_name or scene_id} 未找到')
            return []
        if scene_ids is None:
            scene_ids = []
        if scene_id not in scene_ids:
            scene_ids.append(scene_id)
        sub_scene_ids = self.get_scene_action_sub_scene_ids(scene_id, scene_name)
        for sub_scene_id in sub_scene_ids:
            self.get_scene_action_all_scene_ids(sub_scene_id, scene_ids=scene_ids, print_log=False)
        if print_log:
            aklog_info(f'场景 {scene_name or scene_id} task执行所有场景的id列表: {scene_ids}')
        return scene_ids

    def check_device_state_after_scene_run(self, scene_id=None, scene_name=None, old_devices_info=None,
                                           new_devices_info=None, check_offline=True) -> list:
        """
        场景执行完后，检查设备状态是否切换
        如果场景执行的action为toggle，那么需要传入场景执行前的设备状态信息
        Args:
            check_offline (bool):
            scene_id (str):
            scene_name (str):
            old_devices_info (dict): 场景执行前的设备状态信息，get_devices_list_info(key_type='device_id')方法获取
            new_devices_info (dict): 场景执行后的设备状态信息，get_devices_list_info(key_type='device_id')方法获取
        """
        fail_list = []
        if not scene_id or not scene_name:
            scenes_list = self.get_scenes_list(regain=False)
            if scene_name:
                for scene in scenes_list:
                    if scene['name'] == scene_name:
                        scene_id = scene['scene_id']
                        break
            elif scene_id:
                for scene in scenes_list:
                    if scene['scene_id'] == scene_id:
                        scene_name = scene['name']
                        break
        if not scene_id:
            aklog_error(f'场景 {scene_name or scene_id} 未找到')
            fail_list.append(f'场景 {scene_name or scene_id} 未找到')
            return fail_list
        device_actions = self.get_scene_action_devices(scene_id)
        if not device_actions:
            return []

        aklog_info(f'检查场景 {scene_name or scene_id} 执行后的设备状态')
        if not new_devices_info:
            new_devices_info = self.get_devices_list_info(key_type='device_id')
        for action_info in device_actions:
            checked_flag = False
            device_id = action_info.get('device_id')
            device_info = new_devices_info.get(device_id)
            if not device_info:
                aklog_warn(f'new_devices_info 中未找到设备 {device_id}')
                fail_list.append(f'new_devices_info 中未找到设备 {device_id}')
                continue
            device_name = device_info.get('name')
            attributes = device_info.get('attributes')
            if not device_info.get('online'):
                if not check_offline:
                    aklog_warn(f'设备 {device_name} 离线，不检查状态是否变化')
                else:
                    aklog_warn(f'设备 {device_name} 离线')
                    fail_list.append({'device_name': device_name, 'online': False})
                continue
            # 场景执行前的设备状态信息
            old_attributes: Optional[list] = None
            if old_devices_info:
                old_attributes = old_devices_info.get(device_id).get('attributes')

            entity_id = action_info.get('entity_id')
            entry_name = action_info.get('entry_name')
            if not entry_name:
                action_info['entry_name'] = device_name
                entry_name = device_name

            _type = action_info.get('type')
            if _type == 'toggle' and old_attributes:  # 如果有传入执行前的设备状态信息，则可以检查toggle动作是否有生效
                old_value = None
                for old_attr in old_attributes:
                    if old_attr.get('entity_id') == entity_id and '_state' in old_attr.get('feature'):
                        old_value = old_attr.get('value')
                        break
                if old_value is None:
                    aklog_warn(f'{entry_name} 状态为None，可能是该设备不支持状态获取')
                    fail_list.append(action_info)
                    continue
                value = None
                for attr in attributes:
                    if attr.get('entity_id') == entity_id and '_state' in attr.get('feature'):
                        value = attr.get('value')
                        break
                if value == old_value:
                    aklog_warn(f'{entry_name} 状态toggle失败, 原先状态: {old_value}, 当前状态：{value}')
                    fail_list.append(action_info)
                else:
                    aklog_debug(f'{entry_name} 状态toggle成功, 原先状态: {old_value}, 当前状态：{value}')
                checked_flag = True
            elif _type in ['media_next_track', 'media_previous_track'] and old_attributes:
                old_value = None
                for old_attr in old_attributes:
                    if old_attr.get('entity_id') == entity_id and old_attr.get('feature') == 'music_name':
                        old_value = old_attr.get('value')
                        break
                if old_value is None:
                    aklog_warn(f'{entry_name} 状态为None，可能是该设备不支持状态获取')
                    fail_list.append(action_info)
                    continue
                value = None
                for attr in attributes:
                    if attr.get('entity_id') == entity_id and attr.get('feature') == 'music_name':
                        value = attr.get('value')
                        break
                if value == old_value:
                    aklog_warn(f'{entry_name} 状态previous_next_track失败, 原先状态: {old_value}, 当前状态：{value}')
                    fail_list.append(action_info)
                else:
                    aklog_debug(f'{entry_name} 状态previous_next_track成功, 原先状态: {old_value}, 当前状态：{value}')
                checked_flag = True
            elif _type == 'multi_ctrl':  # Climate类型多个操作
                action = action_info.get('action')
                if action and action != 'toggle':
                    for attr in attributes:
                        if (attr.get('entity_id') != entity_id
                                or '_state' not in attr.get('feature')):
                            continue
                        if attr.get('value') not in action:
                            aklog_warn(
                                f'{entry_name}状态未切换成功，当前状态：{attr.get("value")}，目标状态： {action}')
                            fail_list.append(action_info)
                        else:
                            aklog_debug(f'{entry_name} 状态切换为 {_type} 成功')
                        checked_flag = True
                        break
                    if not checked_flag and _type not in SCENE_ACTION_DEVICE_STATE_MAP:
                        aklog_warn(f'{entry_name}, {_type} 在attributes中未找到，'
                                   f'可能需要补充到SCENE_ACTION_DEVICE_STATE_MAP')
                        fail_list.append(action_info)
                elif action == 'toggle' and old_attributes:
                    value = None
                    for attr in attributes:
                        if attr.get('entity_id') == entity_id and '_state' in attr.get('feature'):
                            value = attr.get('value')
                            break
                    old_value = None
                    for old_attr in old_attributes:
                        if old_attr.get('entity_id') == entity_id and '_state' in old_attr.get('feature'):
                            old_value = old_attr.get('value')
                            break
                    if value == old_value:
                        aklog_warn(f'{entry_name} 状态toggle失败, 原先状态: {old_value}, 当前状态：{value}')
                        fail_list.append(action_info)
                    else:
                        aklog_debug(f'{entry_name} 状态toggle成功, 原先状态: {old_value}, 当前状态：{value}')
                    checked_flag = True

                option_selected_list = []
                options = action_info.get('options')
                if options:
                    for option in action_info.get('options'):
                        if not option.startswith('set_'):
                            continue
                        option_name = option.replace('set_', '')
                        if option_name in action_info:
                            option_selected_list.append(option_name)
                for option_selected in option_selected_list:
                    checked_flag = False
                    action_value = action_info.get(option_selected)
                    if action_value is None:
                        continue
                    state_map = SCENE_ACTION_DEVICE_STATE_MAP.get(option_selected)
                    feature = None
                    if state_map:
                        feature = state_map.get('feature')
                    if not feature:
                        feature = option_selected
                    for attr in attributes:
                        if attr.get('entity_id') != entity_id or attr.get('feature') != feature:
                            continue
                        value = attr.get('value')
                        if ((value == action_value)
                                or (str(value) == str(action_value))
                                or (str(value).isdigit() and int(value) == int(action_value))):
                            aklog_debug(f'{entry_name}, {option_selected} 设置成功,'
                                        f' 目标状态: {action_value}, 当前状态：{value}')
                        else:
                            aklog_warn(f'{entry_name}, {option_selected} 未设置成功,'
                                       f' 目标状态: {action_value}, 当前状态：{value}')
                            fail_list.append(action_info)
                        checked_flag = True
                        break
                    if not checked_flag and option_selected not in SCENE_ACTION_DEVICE_STATE_MAP:
                        aklog_warn(f'{entry_name}, option: {option_selected} 在attributes中未找到，'
                                   f'可能需要补充到SCENE_ACTION_DEVICE_STATE_MAP')
                        fail_list.append(action_info)
            elif _type in ['turn_on', 'turn_off', 'open', 'close', 'media_play', 'media_pause']:
                for attr in attributes:
                    if attr.get('entity_id') != entity_id or '_state' not in attr.get('feature'):
                        continue
                    if attr.get('value') not in _type:
                        aklog_warn(f'{entry_name} 状态未切换成 {_type}, 当前状态: {attr.get("value")}')
                        fail_list.append(action_info)
                    else:
                        aklog_debug(f'{entry_name} 状态切换为 {_type} 成功')
                    checked_flag = True
                    break
            else:
                state_map = SCENE_ACTION_DEVICE_STATE_MAP.get(_type)
                feature = None
                value_key = None
                if state_map:
                    feature = state_map.get('feature')
                    value_key = state_map.get('value_key', feature)
                if not feature:
                    feature = _type
                action_value = state_map.get('value')
                if action_value is None and value_key:
                    action_value = action_info.get(value_key)
                for attr in attributes:
                    if attr.get('entity_id') != entity_id or attr.get('feature') != feature:
                        continue
                    value = attr.get('value')
                    if ((value == action_value)
                            or (str(value) == str(action_value))
                            or (str(value).isdigit() and int(value) == int(action_value))):
                        aklog_debug(f'{entry_name}, {_type} 设置成功,'
                                    f' 目标状态: {action_value}, 当前状态：{value}')
                    else:
                        aklog_warn(f'{entry_name}, {_type} 未设置成功,'
                                   f' 目标状态: {action_value}, 当前状态：{value}')
                        fail_list.append(action_info)
                    checked_flag = True
                    break

            # 有些任务设备动作feature跟设备attributes不匹配，需要报异常，之后添加到SCENE_ACTION_DEVICE_STATE_MAP
            if not checked_flag and _type not in SCENE_ACTION_DEVICE_STATE_MAP:
                aklog_warn(f'{entry_name}, {_type} 在attributes中未找到,'
                           f'可能需要补充到SCENE_ACTION_DEVICE_STATE_MAP')
                fail_list.append(action_info)
        return fail_list

    def check_space_device_state_after_scene_run(
            self, scene_id=None, scene_name=None, new_devices_list=None, check_offline=True) -> list:
        """
        场景执行完后，检查空间设备状态是否切换
        如果场景执行的action为toggle，那么需要传入场景执行前的设备状态信息
        实现思路：
        从场景action获取space_control信息，然后通过area_id获取该房间下的所有设备，检查action type状态是否切换
        Args:
            check_offline (bool):
            scene_id ():
            scene_name ():
            new_devices_list (list): 场景执行后的设备状态信息，get_devices_list()方法获取
        """
        fail_list = []
        if not scene_id or not scene_name:
            scenes_list = self.get_scenes_list(regain=False)
            if scene_name:
                for scene in scenes_list:
                    if scene['name'] == scene_name:
                        scene_id = scene['scene_id']
                        break
            elif scene_id:
                for scene in scenes_list:
                    if scene['scene_id'] == scene_id:
                        scene_name = scene['name']
                        break
        if not scene_id:
            aklog_error(f'场景 {scene_name or scene_id} 未找到')
            fail_list.append(f'场景 {scene_name or scene_id} 未找到')
            return fail_list
        space_controls = self.get_scene_action_space_controls(scene_id)
        if not space_controls:
            return []

        aklog_info(f'检查场景 {scene_name or scene_id} 执行后的空间设备状态')
        if not new_devices_list:
            new_devices_list = self.get_devices_list()
        for space_control in space_controls:
            # 先通过area_id和设备type获取该房间下的指定设备
            area_id = space_control['area_id']
            if area_id == 'others':
                area_id = ''
            space_dev_type = space_control['type']
            if space_dev_type in SCENE_ACTION_SPACE_DEVICE_TYPE_MAP:
                device_type = SCENE_ACTION_SPACE_DEVICE_TYPE_MAP[space_dev_type]
            else:
                device_type = space_dev_type.capitalize()
            devices_info = []
            for new_device in new_devices_list:
                if new_device.get('device_type') != device_type:
                    continue
                if area_id != 'all' and new_device.get('area_id') != area_id:
                    continue
                devices_info.append(new_device)

            for device_info in devices_info:
                checked_flag = False
                device_name = device_info.get('name')
                attributes = device_info.get('attributes')
                if not device_info.get('online'):
                    if not check_offline:
                        aklog_warn(f'设备 {device_name} 离线，不检查状态是否变化')
                    else:
                        aklog_warn(f'设备 {device_name} 离线')
                        fail_list.append({'device_name': device_name, 'online': False})
                    continue
                _action = space_control.get('action')

                if device_type == 'multi_climate':  # Climate类型多个操作
                    if _action and _action in ['on', 'off']:
                        for attr in attributes:
                            if '_state' not in attr.get('feature'):
                                continue
                            if attr.get('value') != _action:
                                aklog_warn(
                                    f'{device_name}状态未切换成功，当前状态：{attr.get("value")}，目标状态： {_action}')
                                fail_space_control = deepcopy(space_control)
                                fail_space_control['device_name'] = device_name
                                fail_list.append(fail_space_control)
                            else:
                                aklog_debug(f'{device_name} 状态切换为 {_action} 成功')
                            checked_flag = True
                            break
                        if not checked_flag and _action not in SCENE_ACTION_DEVICE_STATE_MAP:
                            aklog_warn(f'{device_name}, option: {_action} 在attributes中未找到,'
                                       f'可能需要补充到SCENE_ACTION_DEVICE_STATE_MAP')
                            fail_space_control = deepcopy(space_control)
                            fail_space_control['device_name'] = device_name
                            fail_list.append(fail_space_control)

                    option_selected_list = [key for key in space_control if key not in ['action', 'area_id', 'type']]
                    # temperature, hvac_mode, fan_mode
                    for option_selected in option_selected_list:
                        checked_flag = False
                        space_control_value = space_control.get(option_selected)
                        if space_control_value is None:
                            continue
                        state_map = SCENE_ACTION_DEVICE_STATE_MAP.get(option_selected)
                        feature = None
                        if state_map:
                            feature = state_map.get('feature')
                        if not feature:
                            feature = option_selected
                        for attr in attributes:
                            if attr.get('feature') != feature:
                                continue
                            value = attr.get('value')
                            if ((value == space_control_value)
                                    or (str(value) == str(space_control_value))
                                    or (str(value).isdigit() and int(value) == int(space_control_value))):
                                aklog_debug(f'{device_name}, {option_selected} 设置成功,'
                                            f' 目标状态: {space_control_value}, 当前状态：{value}')
                            else:
                                aklog_warn(f'{device_name}, {option_selected} 未设置成功,'
                                           f' 目标状态: {space_control_value}, 当前状态：{value}')
                                fail_space_control = deepcopy(space_control)
                                fail_space_control['device_name'] = device_name
                                fail_list.append(fail_space_control)
                            checked_flag = True
                            break
                        if not checked_flag and option_selected not in SCENE_ACTION_DEVICE_STATE_MAP:
                            aklog_warn(f'{device_name}, option: {option_selected} 在attributes中未找到，'
                                       f'可能需要补充到SCENE_ACTION_DEVICE_STATE_MAP')
                            fail_space_control = deepcopy(space_control)
                            fail_space_control['device_name'] = device_name
                            fail_list.append(fail_space_control)
                elif _action in ['on', 'off']:
                    if space_dev_type in SCENE_ACTION_SPACE_DEVICE_STATE_MAP:
                        target_state = SCENE_ACTION_SPACE_DEVICE_STATE_MAP.get(space_dev_type).get(_action)
                    else:
                        target_state = _action
                    for attr in attributes:
                        if '_state' not in attr.get('feature'):
                            continue
                        if attr.get('value') != target_state:
                            aklog_warn(f'{device_name} 状态未切换成 {target_state}, 当前状态: {attr.get("value")}')
                            fail_space_control = deepcopy(space_control)
                            fail_space_control['device_name'] = device_name
                            fail_list.append(fail_space_control)
                        else:
                            aklog_debug(f'{device_name} 状态切换为 {target_state} 成功')
                        checked_flag = True
                        break
                else:
                    state_map = SCENE_ACTION_DEVICE_STATE_MAP.get(_action)
                    feature = None
                    if state_map:
                        feature = state_map.get('feature')
                    if not feature:
                        feature = _action
                    space_control_value = space_control.get('value')
                    for attr in attributes:
                        if attr.get('feature') != feature:
                            continue
                        value = attr.get('value')
                        if ((value == space_control_value)
                                or (str(value) == str(space_control_value))
                                or (str(value).isdigit() and int(value) == int(space_control_value))):
                            aklog_debug(f'{device_name}, {_action} 设置成功,'
                                        f' 目标状态: {space_control_value}, 当前状态：{value}')
                        else:
                            aklog_warn(f'{device_name}, {_action} 未设置成功,'
                                       f' 目标状态: {space_control_value}, 当前状态：{value}')
                            fail_space_control = deepcopy(space_control)
                            fail_space_control['device_name'] = device_name
                            fail_list.append(fail_space_control)
                        checked_flag = True
                        break

                if not checked_flag and _action not in SCENE_ACTION_DEVICE_STATE_MAP:
                    aklog_warn(f'{device_name}, action: {_action} 在attributes中未找到,'
                               f' 可能需要补充到SCENE_ACTION_DEVICE_STATE_MAP')
                    fail_space_control = deepcopy(space_control)
                    fail_space_control['device_name'] = device_name
                    fail_list.append(fail_space_control)
        return fail_list

    def check_all_device_state_after_scene_run(
            self, scene_id=None, scene_name=None, old_devices_info=None, check_offline=True, print_log=True) -> bool:
        """
        场景执行后，等待设备状态变化
        会检查space control、执行其他场景的设备状态变化
        Args:
            check_offline (bool):
            old_devices_info (dict): 场景执行前的设备状态信息，由get_devices_list_info(key_type='device_id')方法获取
            scene_id (str):
            scene_name (str):
            print_log (bool): 是否打印相关日志
        """
        if not scene_id or not scene_name:
            scenes_list = self.get_scenes_list(regain=False)
            if scene_name:
                for scene in scenes_list:
                    if scene['name'] == scene_name:
                        scene_id = scene['scene_id']
                        break
            elif scene_id:
                for scene in scenes_list:
                    if scene['scene_id'] == scene_id:
                        scene_name = scene['name']
                        break
        if not scene_id:
            aklog_warn(f'场景 {scene_name or scene_id} 未找到')
            return False
        if print_log:
            aklog_info(f'检查场景 {scene_name or scene_id} 执行后的所有设备状态，包括空间设备和嵌套的子场景下的设备')
        # 获取子场景id信息
        sub_scene_ids = self.get_scene_action_sub_scene_ids(scene_id)
        fail_list = []
        # 检查主场景
        new_devices_info = self.get_devices_list_info(key_type='device_id')
        new_devices_list = self.get_devices_list(regain=False)
        device_fail_list = self.check_device_state_after_scene_run(
            scene_id, scene_name, old_devices_info, new_devices_info, check_offline=check_offline)
        if device_fail_list:
            fail_list.extend(device_fail_list)
        space_fail_list = self.check_space_device_state_after_scene_run(
            scene_id, scene_name, new_devices_list, check_offline=check_offline)
        if space_fail_list:
            fail_list.extend(space_fail_list)
        if len(fail_list) > 0:
            aklog_warn(f'场景 {scene_name or scene_id} 执行后，有设备状态未变化：{fail_list}')
            return False
        # 递归检查子场景
        for sub_scene_id in sub_scene_ids:
            aklog_debug(f'检查子场景 {scene_name or scene_id} 执行后的设备状态')
            ret = self.check_all_device_state_after_scene_run(
                sub_scene_id, old_devices_info=old_devices_info, check_offline=check_offline, print_log=False)
            if not ret:
                return False

        if print_log:
            aklog_info(f'场景 {scene_name or scene_id} 执行后，所有设备状态已切换')
        return True

    def wait_all_device_state_switch_after_scene_run(
            self, scene_id=None, scene_name=None, old_devices_info=None, check_offline=True, timeout=15) -> bool:
        """
        场景执行后，等待设备状态变化
        会检查space control、执行其他场景的设备状态变化
        Args:
            check_offline (bool): 是否检查离线设备，如果为True，离线设备也会当做失败
            old_devices_info (dict): 场景执行前的设备状态信息，由get_devices_list_info(key_type='device_id')方法获取
            scene_id (str):
            scene_name (str):
            timeout (int):
        """
        if not scene_id or not scene_name:
            scenes_list = self.get_scenes_list(regain=False)
            if scene_name:
                for scene in scenes_list:
                    if scene['name'] == scene_name:
                        scene_id = scene['scene_id']
                        break
            elif scene_id:
                for scene in scenes_list:
                    if scene['scene_id'] == scene_id:
                        scene_name = scene['name']
                        break
        if not scene_id:
            aklog_warn(f'场景 {scene_name or scene_id} 未找到')
            return False
        aklog_info(f'场景 {scene_name or scene_id} 执行后，等待所有设备状态切换，包括空间设备和嵌套的子场景设备')
        end_time = time.time() + timeout
        count = 0
        while time.time() < end_time or count < 2:
            ret = self.check_all_device_state_after_scene_run(
                scene_id, scene_name, old_devices_info, check_offline=check_offline)
            if ret:
                return True
            time.sleep(3)
            count += 1
            continue
        return False

    def get_scene_trigger_devices(self, scene_id=None, scene_name=None, device_id=None):
        """
        获取场景触发设备列表
        Args:
            scene_id (str):
            scene_name (str):
            device_id (str):
        Returns:
            [{
                "type": "co",
                "platform": "device",
                "device_id": "61601f40c1224e9c9ac31c181f41e8bc",
                "entity_id": "binary_sensor.251c6fadba064d6eb9f8fcd4082b244b",
                "domain": "binary_sensor",
                "device_class": "carbon_monoxide"
            }]
        """
        if not scene_id and scene_name:
            scenes_list = self.get_scenes_list()
            for scene in scenes_list:
                if scene['name'] == scene_name:
                    scene_id = scene['scene_id']
                    break
        if not scene_id:
            aklog_warn(f'场景 {scene_name or scene_id} 未找到')
            return None
        scene_info = self.get_scene_detail_info(scene_id, regain=False)
        triggers = scene_info.get('trigger')
        trigger_devices = []
        for trigger in triggers:
            if not trigger.get('platform') == 'device':
                continue
            if device_id and trigger.get('device_id') != device_id:
                continue
            trigger_devices.append(trigger)
        return trigger_devices

    def get_scene_task_devices(self, scene_id=None, scene_name=None, device_id=None):
        """
        获取场景task设备列表
        Args:
            scene_id (str):
            scene_name (str):
            device_id (str):
        Returns:
            [{
                "device_id": "26ce2a6197ed456cae03ac8eefa6ee9e",
                "domain": "light",
                "entity_id": "light.d12928e94a664c6bbeff9463fd5a26e5",
                "type": "brightness",
                "brightness_pct": 56
            }]
        """
        if not scene_id and scene_name:
            scenes_list = self.get_scenes_list()
            for scene in scenes_list:
                if scene['name'] == scene_name:
                    scene_id = scene['scene_id']
                    break
        if not scene_id:
            aklog_warn(f'场景 {scene_name or scene_id} 未找到')
            return None
        scene_info = self.get_scene_detail_info(scene_id, regain=False)
        tasks = scene_info.get('action')
        task_devices = []
        for task in tasks:
            if ((not device_id and task.get('device_id'))
                    or (device_id and task.get('device_id') == device_id)):
                task_devices.append(task)
        return task_devices

    def get_scene_ids_by_trigger_device(self, **kwargs) -> list:
        """
        获取有添加指定设备触发条件的场景id
        kwargs: 设备触发过滤条件，比如: device_id='xxx', type='co'
        """
        aklog_info()
        self.get_scenes_list()
        for scene in self.scenes_list:
            if not scene.get('is_auto') or not scene.get('auto_enabled'):
                continue
            scene_id = scene['scene_id']
            self.get_scene_detail_info(scene_id, regain=False)
        scene_ids = []
        for scene_info in self.scenes_detail_info.values():
            triggers = scene_info.get('trigger')
            for trigger in triggers:
                if trigger.get('platform') != 'device':
                    continue
                if kwargs and any(trigger.get(key) != value for key, value in kwargs.items()):
                    continue
                scene_ids.append(scene_info['id'])
        aklog_debug(f'scene_ids: {scene_ids}')
        return scene_ids

    def get_simulator_subdevice_trigger_action(self, trig_device_id, trig_type):
        """
        获取模拟器子设备的触发动作
        如果触发类型为changed_states，获取跟当前状态相反的触发类型
        """
        if trig_type == 'changed_states':
            self.get_device_triggers_info(key_type='device_id')
            triggers = self.device_triggers_info.get(trig_device_id).get('info')
            entity_id = None
            for trigger in triggers:
                if trigger.get('type') == 'changed_states':
                    entity_id = trigger.get('entity_id')
            _types = []
            for trigger in triggers:
                if (trigger.get('entity_id') == entity_id
                        and trigger.get('type') != 'changed_states'):
                    _types.append(trigger.get('type'))
            cur_state = self.get_entity_state(entity_id)
            for _type in _types:
                trigger_action = SCENE_DEVICE_SIMULATOR_TRIGGER_TYPE_MAP.get(_type)
                if list(trigger_action.get('reverse_action').values())[0] == cur_state:
                    trig_type = _type
        subdevice_trigger_action = SCENE_DEVICE_SIMULATOR_TRIGGER_TYPE_MAP.get(trig_type)
        return subdevice_trigger_action

    def get_subdevice_trigger_action(self, trigger_info) -> Optional[dict]:
        """
        获取子设备的触发动作（userweb接口方式）
        如果触发类型为changed_states，获取跟当前状态相反的触发类型
        """
        aklog_info()
        trigger_type = trigger_info.get('type')
        trigger_domain = trigger_info.get('domain')
        trigger_entity_id = trigger_info.get('entity_id')
        trigger_device_id = trigger_info.get('device_id')
        trigger_param_info = {}
        for key, value in trigger_info.items():
            if key not in ['device_id', 'domain', 'entity_id', 'entry_name', 'platform', 'type']:
                trigger_param_info[key] = value

        # 需要获取设备的当前状态
        cur_attributes = self.get_device_info(attr='attributes', device_id=trigger_device_id)
        if not cur_attributes:
            unittest_add_results([False, f'获取设备 {trigger_device_id} 信息失败'])
            return None

        is_reversal_required = False  # 是否需要反转操作
        trigger_action_params = {}
        trigger_reverse_action_params = {}
        trigger_reverse_service_type = None
        trigger_reverse_target_state = None
        trigger_feature = None

        if trigger_type == 'changed_states':
            # 如果触发类型为changed_states，只需要根据当前状态获取触发操作即可
            trigger_cur_state = None
            for attr in cur_attributes:
                if '_state' in attr.get('feature'):
                    trigger_cur_state = attr.get('value')
                    break
            trigger_action_info = SCENE_DEVICE_TRIGGER_CHANGED_STATES_ACTION_MAP.get(trigger_cur_state)
            if not trigger_action_info:
                unittest_results([False, f'SCENE_DEVICE_TRIGGER_CHANGED_STATES_ACTION_MAP 缺少参数: {trigger_cur_state}'])
                return None
            trigger_service_type = trigger_action_info.get('service_type')
            trigger_target_state = trigger_action_info.get('target_state')
        else:
            # 如果触发类型为其他的，判断当前状态是否在触发条件范围内，则需要反转操作
            trigger_action_info = SCENE_DEVICE_TRIGGER_ACTION_MAP.get(trigger_type)
            if not trigger_action_info:
                unittest_results([False, f'SCENE_DEVICE_TRIGGER_ACTION_MAP 缺少参数: {trigger_type}'])
                return None
            trigger_feature = trigger_action_info.get('feature')
            trigger_cur_state = None
            for attr in cur_attributes:
                if ((trigger_feature and attr.get('feature') == trigger_feature)
                        or (not trigger_feature and '_state' in attr.get('feature'))):
                    trigger_feature = attr.get('feature')
                    trigger_cur_state = attr.get('value')
                    break
            # 获取trigger设备执行触发操作后的目标状态
            trigger_service_type = trigger_action_info.get('service_type')
            trigger_target_state = trigger_action_info.get('target_state')

            # 获取trigger设备执行反向操作后的目标状态
            trigger_reverse_service_type = trigger_action_info.get('reverse_service_type')
            if trigger_reverse_service_type is None:
                trigger_reverse_service_type = trigger_service_type
            trigger_reverse_target_state = trigger_action_info.get('reverse_target_state')

            # 判断当前状态是否在触发范围内，是否需要反转操作
            if '_state' in trigger_feature:
                if (trigger_cur_state in trigger_type
                        or trigger_cur_state == trigger_target_state):
                    is_reversal_required = True

            # 获取trigger设备非state的数值操作的目标状态
            for key, value_range in trigger_action_info.items():
                if key in ['service_type', 'reverse_service_type', 'feature', 'target_state', 'reverse_target_state']:
                    continue
                if 'above' in trigger_param_info:
                    # 有些属性的trigger数值为百分比，但设备状态为具体的数值范围
                    trigger_value = trigger_param_info['above']
                    if trigger_value not in value_range and 0 <= trigger_value <= 100:
                        trigger_value = int((value_range[-1] - value_range[0]) * trigger_value / 100 + value_range[0])
                    _index = value_range.index(trigger_value)
                    trigger_target_state = random.choice(
                        value_range[min(_index + 1, len(value_range) - 1):])
                    trigger_action_params[key] = trigger_target_state
                    trigger_reverse_target_state = random.choice(
                        value_range[0:max(_index - 1, 1)])
                    trigger_reverse_action_params[key] = trigger_reverse_target_state
                    if int(trigger_cur_state) >= trigger_value:
                        is_reversal_required = True
                elif 'below' in trigger_param_info:
                    trigger_value = trigger_param_info['below']
                    if trigger_value not in value_range and 0 <= trigger_value <= 100:
                        trigger_value = int((value_range[-1] - value_range[0]) * trigger_value / 100 + value_range[0])
                    _index = value_range.index(trigger_value)
                    trigger_target_state = random.choice(
                        value_range[0:max(_index - 1, 1)])
                    trigger_action_params[key] = trigger_target_state
                    trigger_reverse_target_state = random.choice(
                        value_range[min(_index + 1, len(value_range) - 1):])
                    trigger_reverse_action_params[key] = trigger_reverse_target_state
                    if int(trigger_cur_state) < trigger_value:
                        is_reversal_required = True

        trigger_params = {
            'feature': trigger_feature,
            'target_state': trigger_target_state,
            'reverse_target_state': trigger_reverse_target_state,
            'action_params': {
                'entity_id': trigger_entity_id,
                'domain': trigger_domain,
                'service_type': trigger_service_type,
            },
            'reverse_action_params': None
        }
        trigger_params['action_params'].update(trigger_action_params)

        # 如果设备当前状态需要反转才能触发，需要返回反转操作数据
        if is_reversal_required:
            reverse_action_params = {
                'entity_id': trigger_entity_id,
                'domain': trigger_domain,
                'service_type': trigger_reverse_service_type,
            }
            reverse_action_params.update(trigger_reverse_action_params)
            trigger_params['reverse_action_params'] = reverse_action_params

        aklog_debug(f'trigger_params: {trigger_params}')
        return trigger_params

    def get_subdevice_task_action(self, task_info) -> Optional[dict]:
        """
        获取子设备的触发动作（userweb接口方式）
        如果触发类型为changed_states，获取跟当前状态相反的触发类型
        """
        aklog_info()
        task_type = task_info.get('type')
        task_domain = task_info.get('domain')
        task_entity_id = task_info.get('entity_id')
        task_device_id = task_info.get('device_id')
        # 获取设置数值等额外参数
        task_feature = None
        task_action_info = None
        if task_type not in ['toggle', 'light_flash']:
            task_action_info = SCENE_TASK_DEVICE_ACTION_MAP.get(task_type)
            if not task_action_info:
                unittest_results([False, f'SCENE_TASK_DEVICE_ACTION_MAP 缺少参数: {task_type}'])
                return None
            task_feature = task_action_info.get('feature')

        target_state = None
        reverse_target_state = None
        for key, value in task_info.items():
            if key not in ['device_id', 'domain', 'entity_id', 'entry_name', 'type']:
                if not task_feature:
                    task_feature = key
                target_state = value
        # 获取设备当前状态数据
        task_cur_state = None
        task_device_attributes = self.get_device_info(attr='attributes', device_id=task_device_id)
        for attr in task_device_attributes:
            if ((task_feature and task_feature == attr.get('feature'))
                    or (not task_feature and '_state' in attr.get('feature'))):
                task_feature = attr.get('feature')
                task_cur_state = attr.get('value')
                break
        # 获取场景执行后设备目标状态，以及事先需要的反转状态操作参数
        task_reverse_action_params = {}
        task_reverse_service_type = None
        if target_state is None or task_cur_state == target_state:
            if task_type == 'toggle':
                target_state = SCENE_TASK_DEVICE_TOGGLE_ACTION_MAP.get(task_cur_state).get('target_state')
            elif task_type == 'light_flash':
                target_state = task_cur_state
            else:
                if target_state is None:
                    target_state = task_action_info.get('target_state')
                reverse_target_state = task_action_info.get('reverse_target_state')

                task_reverse_service_type = task_action_info.get('reverse_service_type')
                for _key, value_range in task_action_info.items():
                    if _key not in ['reverse_service_type', 'feature', 'target_state', 'reverse_target_state']:
                        filtered_list = [item for item in value_range if str(item) != str(target_state)]
                        reverse_target_state = random.choice(filtered_list)
                        task_reverse_action_params[_key] = reverse_target_state

        # 生成task设备要检查的目标状态，以及需要反转状态操作的参数，并返回
        task_params = {
            'feature': task_feature,
            'target_state': target_state,
            'reverse_target_state': reverse_target_state,
            'reverse_params': None
        }

        if task_cur_state == target_state and task_type not in ['light_flash', 'toggle']:
            task_params['reverse_params'] = {
                'entity_id': task_entity_id,
                'domain': task_domain,
                'service_type': task_reverse_service_type,
            }
            task_params['reverse_params'].update(task_reverse_action_params)
        aklog_debug(task_params)
        return task_params

    def get_all_scene_trigger_devices_info(
            self, device_type=None, product_model=None, is_simulator=False) -> dict:
        """获取所有场景触发设备中的在线子设备"""
        aklog_info()
        self.get_scenes_list()
        self.get_devices_list()
        devices_list_info = {}
        for device in self.devices_list:
            devices_list_info[device['device_id']] = device
        all_trigger_devices = []
        for scene in self.scenes_list:
            if not scene.get('is_auto') or not scene.get('auto_enabled'):
                continue
            trigger_devices = self.get_scene_trigger_devices(scene.get('scene_id'))
            if trigger_devices:
                all_trigger_devices.extend(trigger_devices)
        trigger_devices_info = {}
        for trigger in all_trigger_devices:
            device_id = trigger.get('device_id')
            devices_info = devices_list_info.get(device_id)
            if not devices_info.get('online'):
                continue
            if device_type and devices_info.get('device_type') != device_type:
                continue
            if product_model and devices_info.get('product_model') != product_model:
                continue
            if is_simulator and not self.is_simulator_device(device_id=device_id):
                continue
            if device_id not in trigger_devices_info:
                trigger_devices_info[device_id] = []
            trigger_devices_info[device_id].append(trigger)
        return trigger_devices_info

    def is_enabled_auto_scene(self, scene_id):
        """检查自动场景是否启用"""
        self.get_scenes_list(regain=False)
        scene_info = None
        for scene in self.scenes_list:
            if scene.get('scene_id') == scene_id and scene.get('is_auto'):
                scene_info = scene
                break
        if not scene_info:
            aklog_warn(f'{scene_id} not found')
            return None
        return scene_info.get('auto_enabled')

    # endregion

    # region 布撤防相关

    def add_security(self, mode_name="auto add", **kwargs):
        """
        添加布防模式
        "name": "11",
        "activitedDevice": [{
            "name": "sos",
            "product_type": "Emergency Sensor",
            "device_id": "e2598684e96ef66476886126f0a4ac04",
            "entity_id": "binary_sensor.a090d8de07e388a5b7ab3903c541e597",
            "room": "",
            "selected": true
        }],
        "type": "custom",
        "defenceDelay": 30,
        "isSilentOn": false,
        "isSirenOn": 是否启用Alarm告警， True， False
        "isSendMessage": true,
        "messageContent": "Send Message",
        "isSendHttpCommand": true,
        "httpCommand": "http://192",
        "relay": [{
            "name": "Hypanel Lux081514 - dimmer",
            "device_id": "080e8db295e147d3a0769d4cc50a9cb0",
            "entity_id": "light.67d17f74c1934400bf8086923c2da4cc",
            "product_type": "dimmer"
        }],
        "isArm": false,
        "alarmDelay": 30,
        "callList": callList: 呼叫号码列表，如果是设备，传入设备名称，转成设备id，list类型
        ["Burglary", "Panic", "Medical", "Fire", "Customize", "PS51"]
        """
        aklog_info()
        activatedDevices_name = kwargs.get('activatedDevice', [])
        activated_devices_info = self._generate_security_activated_device_info(
            activatedDevices_name) if activatedDevices_name else []
        relays = kwargs.get('relays', [])
        relays_off = kwargs.get('relays_off', [])
        callList = kwargs.get('callList', [])

        relays_info = self._generate_security_relay_info(relays) if relays else []
        call_info = self._generate_security_call_list(callList) if callList else []

        add_security_data = {
            "type": "config/ak_security/add",
            "security": {
                "name": mode_name,
                "activitedDevice": activated_devices_info,
                "type": "custom",
                "defenceDelay": kwargs.get('defenceDelay', 0),
                "isSilentOn": kwargs.get('isSilentOn', False),
                "isSirenOn": kwargs.get('isSirenOn', True),
                "isSendMessage": kwargs.get('isSendMessage', False),
                "messageContent": kwargs.get('messageContent', ''),
                "isSendHttpCommand": kwargs.get('isSendHttpCommand', False),
                "httpCommand": kwargs.get('httpCommand', ''),
                "relay": relays_info,
                "isArm": kwargs.get('isArm', False),
                "alarmDelay": kwargs.get('alarmDelay', 0),
                "callList": call_info
            }
        }
        if self.ha_version >= 3.002:
            relays_off_info = self._generate_security_relay_info(relays_off, 'off') if relays_off else []
            add_security_data['security']['relay_off'] = relays_off_info

        resp = self.ws_send_request(add_security_data)
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def edit_security(self, by_security_name, new_security_name=None, activatedDevices=None, isSirenOn=False,
                      relays=None, relays_off=None, callList=None, messageContent=None, httpCommand=None,
                      defenceDelay=0, alarmDelay=0):
        """修改布防模式，传入的参数格式跟添加布防模式一致"""
        aklog_info()
        self.get_security_info()
        if by_security_name not in self.security_info:
            aklog_info('布防模式 %s 不存在' % by_security_name)
            return None
        if not new_security_name:
            new_security_name = by_security_name
        security_id = self.security_info[by_security_name]['id']
        entity_id = self.security_info[by_security_name]['entity_id']
        _type = self.security_info[by_security_name]['type']
        isSilentOn = self.security_info[by_security_name]['isSilentOn']
        isArm = self.security_info[by_security_name]['isArm']

        if messageContent is None:
            isSendMessage = False
            messageContent = ''
        else:
            isSendMessage = True
        if httpCommand is None:
            isSendHttpCommand = False
            httpCommand = ''
        else:
            isSendHttpCommand = True

        activated_devices_info = self._generate_security_activated_device_info(
            activatedDevices) if activatedDevices else []
        relays_info = self._generate_security_relay_info(relays) if relays else []
        call_info = self._generate_security_call_list(callList) if callList else []

        update_security_data = {
            "type": "config/ak_security/update",
            "securities": [{
                "id": security_id,
                "name": new_security_name,
                "type": _type,
                "defenceDelay": int(defenceDelay),
                "isSilentOn": isSilentOn,
                "activitedDevice": activated_devices_info,
                "isSirenOn": isSirenOn,
                "isSendMessage": isSendMessage,
                "messageContent": messageContent,
                "isSendHttpCommand": isSendHttpCommand,
                "httpCommand": httpCommand,
                "relay": relays_info,
                "isArm": isArm,
                "alarmDelay": int(alarmDelay),
                "callList": call_info,
                "entity_id": entity_id}]}
        if self.ha_version >= 3.002:
            relays_off_info = self._generate_security_relay_info(relays_off) if relays_off else []
            update_security_data['securities'][0]['relay_off'] = relays_off_info
        resp = self.ws_send_request(update_security_data)
        aklog_info('修改布防模式 %s 结果：%s' % (by_security_name, resp.get('success')))
        if not resp.get('success'):
            aklog_info(resp)
        return resp.get('success')

    def get_security_relay_list(self):
        data = {
            "type": "config/ak_device/security_relay_list",
        }
        resp = self.ws_send_request(data)
        if resp is None or isinstance(resp, bool):
            return resp
        return resp['result']

    def _generate_security_relay_info(self, relay_name_list, toggle='on'):
        """根据relay名称列表生成Relay device_id信息"""
        relay_list: List[dict] = self.get_security_relay_list()
        relays_info = []
        for relay in relay_list:
            if relay.get('name') not in relay_name_list:
                continue
            if toggle == 'off':
                relay_off = deepcopy(relay)
                if 'area_id' in relay_off:
                    relay_off.pop('area_id')
                if 'group' in relay_off:
                    relay_off.pop('group')
                relays_info.append(relay_off)
            else:
                relays_info.append(relay)
        return relays_info

    def get_security_trigger_list(self, grep=None):
        """HA获取security_trigger设备列表
        :param grep: 筛选条件，按照devices_list的响应字段传入，默认为None"""
        data = {
            "type": "config/ak_device/security_trigger_list"
        }
        resp = self.ws_send_request(data)
        if resp is None or isinstance(resp, bool):
            return resp
        devices_list = resp['result']
        if grep:
            devices_info = []
            for device in devices_list:
                devices_info.append(device[grep])
            return devices_info
        return devices_list

    def _generate_security_activated_device_info(self, device_list):
        """根据防区名称列表生成防区 device_id信息"""
        security_trigger_list_info = self.get_security_trigger_list()
        activatedDevice_list = []
        for device in security_trigger_list_info:
            if device["name"] in device_list:
                device['selected'] = True
                activatedDevice_list.append(device)
        return activatedDevice_list

    def get_security_sos_list(self):
        data = {
            "type": "config/sos_list",
        }
        resp = self.ws_send_request(data)
        if resp is None or isinstance(resp, bool):
            return resp
        return resp['result']

    def _generate_security_call_list(self, call_list):
        """根据relay名称列表生成Relay device_id信息"""
        sos_list = self.get_security_sos_list()
        make_call_info = []
        for sos in sos_list:
            if sos.get('name') in call_list:
                make_call_info.append(sos)
        return make_call_info

    def get_security_info(self, regain=True):
        """
        获取布防模式信息
        return:
        {'Home':
            {'id': 'de66e8c3ccff452b833d1a36e6d92c40', 'name': 'Home', 'type': 'home', 'defenceDelay': 90,
            'isSilentOn': False, 'activitedDevice': [], 'isSirenOn': False, 'isSendMessage': False,
            'messageContent': '', 'isSendHttpCommand': False, 'httpCommand': '', 'relay': [], 'isArm': False,
            'alarmDelay': 0, 'callList': [], 'entity_id': 'automation.home'}
        }
        """
        aklog_info()
        if not regain and self.security_info:
            return self.security_info
        self.security_info.clear()
        security_list = self.get_security_list()
        if security_list is None:
            return None
        for ret in security_list:
            security_name = ret['name']
            self.security_info[security_name] = ret
        # aklog_info(self.security_info)
        return self.security_info

    def get_security_list(self, regain=True, grep=None):
        """HA获取Security设备列表
        :param regain: 是否重新获取
        :param grep: 筛选条件，按照security_list的响应字段传入，默认为None"""
        aklog_info()
        if regain:
            self.security_list.clear()
        if not self.security_list:
            data = {
                "type": "config/ak_security/list"
            }
            resp = self.ws_send_request(data)
            if resp and resp.get('success'):
                self.security_list = resp['result']
            else:
                aklog_error('get_security_list Fail')
                return None
        if grep:
            security_info = []
            for security in self.security_list:
                security_info.append(security[grep])
            aklog_debug('security_list (grep: %s): %s' % (grep, security_info))
            return security_info
        return self.security_list

    def get_security_arming_status(self, name):
        """获取防区的布撤防状态"""
        self.get_security_info()
        if name in self.security_info:
            return self.security_info[name]['isArm']
        else:
            aklog_info('找不到 %s 布防模式')
            return None

    def set_security_arming_status(self, by_security_name, arming=True, ignore=True):
        """
        设置布防模式启用禁用
        arming: True / False
        ignore: True / False
        """
        aklog_info()
        self.get_security_info()
        if by_security_name not in self.security_info:
            aklog_info('布防模式 %s 不存在' % by_security_name)
            return None
        if self.security_info[by_security_name].get('isArm') == arming:
            aklog_debug(f'安防模式 {by_security_name} 当前状态已是：{arming}')
            return True
        security_id = self.security_info[by_security_name]['id']

        set_security_data = {
            "type": "config/ak_security/arm",
            "arm": arming,
            "security_id": security_id
        }
        for i in range(2):
            resp = self.ws_send_request(set_security_data)
            ignore_list = resp['result'].get('ignore_list')
            isArm = resp['result'].get('isArm')
            if i == 0 and isArm != arming and ignore_list:
                # 启用时提示是否忽略状态错误的防区
                if ignore:
                    set_security_data['ignore'] = True
                    continue
                else:
                    aklog_error('存在状态错误的防区，不忽略，放弃设置布防模式')
                    return True
            elif isArm == arming:
                aklog_info('设置布防模式 %s 为 %s 成功' % (by_security_name, arming))
                return True
            else:
                aklog_error('设置布防模式 %s 为 %s 失败' % (by_security_name, arming))
                return False

    def batch_set_security_arming_status(self, arming=True, ignore=True):
        """批量设置布防模式启用和禁用"""
        aklog_info()
        # 先获取布防模式的ID列表
        self.get_security_info()
        security_id_list = []
        for security in self.security_info:
            security_id_list.append(self.security_info[security]['id'])

        batch_set_security_data = {
            "type": "config/ak_security/batch_arm",
            "security_ids": security_id_list,
            "arm": arming
        }
        for i in range(2):
            resp = self.ws_send_request(batch_set_security_data)
            ignore_lists = resp['result']['ignore_lists']
            is_arm_list = []
            for security_ret in ignore_lists:
                is_arm_list.append(security_ret['isArm'])

            if i == 0 and (not arming) in is_arm_list:
                # 启用时提示是否忽略状态错误的防区
                if ignore:
                    batch_set_security_data['ignore'] = True
                    continue
                else:
                    aklog_error('存在状态错误的防区，不忽略，放弃设置布防模式')
                    return True
            elif (not arming) not in is_arm_list:
                aklog_info('批量设置布防模式为 %s 成功' % arming)
                return True
            else:
                aklog_error('批量设置布防模式为 %s 失败' % arming)
                return False

    def get_security_silent_mode(self, name):
        """获取防区的布撤防状态"""
        self.get_security_info()
        if name in self.security_info:
            return self.security_info[name]['isSilentOn']
        else:
            aklog_info('找不到 %s 布防模式')
            return None

    def set_security_silent_mode(self, security_name, isSilentOn=True):
        """设置布防模式静音状态，True为启用静音，False为关闭静音"""
        aklog_info()
        self.get_security_info()
        if security_name not in self.security_info:
            aklog_info('布防模式 %s 不存在' % security_name)
            return None
        security_data = self.security_info[security_name]
        security_data.pop('entity_id')
        security_data['isSilentOn'] = isSilentOn
        set_security_data = {"type": "config/ak_security/update", "securities": [security_data],
                             "silent": True}

        # 获取设置结果，判断是否设置成功
        resp = self.ws_send_request(set_security_data)
        for security in resp['result']:
            if security['name'] == security_name:
                if security['isSilentOn'] == isSilentOn:
                    aklog_info('设置布防模式 %s 的silent状态为 %s 成功' % (security_name, isSilentOn))
                    return True
                else:
                    aklog_error('设置布防模式 %s 的silent状态为 %s 失败' % (security_name, isSilentOn))
                    return False
        aklog_error('获取布防模式结果失败')
        return None

    def batch_set_security_silent_mode(self, isSirenOn=False):
        """批量设置所有布防模式静音状态，False为启用静音，True为关闭静音"""
        aklog_info()
        self.get_security_list()
        security_list = []
        for security in self.security_list:
            security['isSirenOn'] = isSirenOn
            security_list.append(security)

        batch_set_security_data = {"type": "config/ak_security/update",
                                   "securities": security_list,
                                   "silent": True}

        # 获取设置结果，判断是否设置成功
        resp = self.ws_send_request(batch_set_security_data)
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def delete_security(self, *security_names):
        """删除自定义布防模式"""
        aklog_info()
        self.get_security_info()
        security_id_list = []
        for name in security_names:
            if name not in self.security_info:
                aklog_warn('布防模式 %s 不存在' % name)
                continue
            elif name in ['Home', 'Night', 'Away']:
                aklog_warn('%s 模式为默认的，不能删除' % name)
                continue
            security_id = self.security_info[name]['id']
            security_id_list.append(security_id)
        if not security_id_list:
            return None
        delete_security_data = {"type": "config/ak_security/delete", "ids": security_id_list}
        resp = self.ws_send_request(delete_security_data)
        ret = resp.get('success')
        aklog_info('删除布防模式 %s 结果：%s' % (tuple(security_names), ret))
        if not ret:
            aklog_debug(f'resp: {resp}')
        return ret

    def delete_security_by_contain_name(self, contain_name):
        """删除自定义布防模式"""
        aklog_info()
        self.get_security_info()
        security_id_list = []
        for name in self.security_info:
            if name in ['Home', 'Night', 'Away']:
                aklog_warn('%s 模式为默认的，不能删除' % name)
                continue
            if contain_name not in name:
                continue
            security_id = self.security_info[name]['id']
            security_id_list.append(security_id)
        if not security_id_list:
            aklog_debug(f'未找到名称包含 {contain_name} 的安防模式')
            return None
        delete_security_data = {"type": "config/ak_security/delete", "ids": security_id_list}
        resp = self.ws_send_request(delete_security_data)
        ret = resp.get('success')
        aklog_info(f'删除名称中包含 {contain_name} 布防模式, 结果：{ret}')
        if not ret:
            aklog_debug(f'resp: {resp}')
        return ret

    def delete_all_security(self):
        """删除所有自定义布防模式"""
        aklog_info()
        self.get_security_info()
        security_id_list = []
        for name in self.security_info:
            if name in ['Home', 'Night', 'Away']:
                aklog_info('%s 模式为默认的，不能删除' % name)
                continue
            security_id = self.security_info[name]['id']
            security_id_list.append(security_id)
        if not security_id_list:
            aklog_warn('不存在自定义安防模式')
            return None
        delete_security_data = {"type": "config/ak_security/delete", "ids": security_id_list}
        resp = self.ws_send_request(delete_security_data)
        ret = resp.get('success')
        aklog_info('删除所有布防模式结果：%s' % ret)
        if not ret:
            aklog_debug(f'resp: {resp}')
        return ret

    def get_security_record(self, record_date=None, record_type='trigger'):
        """
        获取布防模式触发记录
        Args:
            record_date (str): 格式：%Y-%m-%d， 比如：2024-09-10
            record_type (str): 安防记录类型: trigger为安防模式触发记录， change为布撤防切换记录, alert为Sensor触发记录，bypass
        """
        aklog_info()
        send_data = {
            "type": "config/ak_security/record",
            "record_type": record_type,
            "page": 1,
            "page_size": 1000
        }
        if record_date:
            start_time = '%s 00:00:00' % record_date
            end_time = '%s 23:59:59' % record_date
            send_data['start_datetime'] = start_time
            send_data['end_datetime'] = end_time
        resp = self.ws_send_request(send_data)
        if resp and resp.get('success'):
            result = resp.get('result')
            return result
        else:
            aklog_debug('resp: %s' % resp)
            return None

    def get_security_names_by_activated_device(self, **kwargs) -> list:
        """
        获取有添加指定设备触发条件的场景id
        kwargs: 设备触发过滤条件，使用activitedDevice参数：
        {
            "device_id": "61601f40c1224e9c9ac31c181f41e8bc",
            "entity_id": "binary_sensor.251c6fadba064d6eb9f8fcd4082b244b",
            "product_type": "CO Sensor",
            "name": "CO Sensor-000001",
            "room": ""
        }
        """
        aklog_info()
        self.get_security_list()
        security_names = []
        for security in self.security_list:
            activatedDevices = security.get('activitedDevice')
            if not activatedDevices:
                continue
            for device in activatedDevices:
                if kwargs and all(device.get(key) == value for key, value in kwargs.items()):
                    security_names.append(security.get('name'))
                    break
        aklog_debug(f'security_names: {security_names}')
        return security_names

    def get_all_security_activated_simulator_devices(self) -> list:
        """先获取所有安防模式有添加模拟器设备触发的设备列表"""
        aklog_info()
        self.get_security_list()
        device_names = []
        for security in self.security_list:
            activatedDevices = security.get('activitedDevice')
            if not activatedDevices:
                continue
            for device in activatedDevices:
                device_name = device.get('name')
                if self.is_simulator_device(device_name=device_name):
                    device_names.append(device_name)
        aklog_debug(f'activated_simulator_devices: {device_names}')
        return device_names

    def check_device_state_after_security_run(
            self, security_id=None, security_name=None, new_devices_info=None, check_offline=True) -> list:
        """
        安防模式触发后，检查设备状态
        Args:
            security_id ():
            security_name ():
            new_devices_info (): 新设备信息，由get_devices_list_info(key_type='device_id')获取
            check_offline (): 是否检查离线设备
        """
        aklog_info(f'检查安防模式 {security_name or security_id} 执行后的设备状态')
        fail_list = []
        # 获取安防模式信息
        security_list = self.get_security_list(regain=False)
        security_info = None
        for security in security_list:
            if ((security_id and security.get('id') == security_id)
                    or (security_name and security.get('name') == security_name)):
                security_info = security
                break
        if not security_info:
            unittest_results([False, f'安防模式 {security_name or security_id} 未找到',
                              f'security_list: {security_list}'])
            return [False, f'安防模式 {security_name or security_id} 未找到']
        # 获取安防模式执行的设备列表
        relays = security_info.get('relay', [])
        relays_off = security_info.get('relay_off', [])
        if not relays and not relays_off:
            return [True, f'安防模式 {security_name or security_id} 没有执行设备操作']

        # 获取设备state状态检查
        if not new_devices_info:
            new_devices_info = self.get_devices_list_info(key_type='device_id')
        for relay_info in relays:
            device_id = relay_info.get('device_id')
            entity_id = relay_info.get('entity_id')
            device_info = new_devices_info.get(device_id)
            device_name = device_info.get('name')
            attributes = device_info.get('attributes')
            if not device_info.get('online'):
                if not check_offline:
                    aklog_warn(f'设备 {device_name} 离线，不检查状态是否变化')
                else:
                    aklog_warn(f'设备 {device_name} 离线')
                    fail_list.append({'device_name': device_name, 'online': False})
                continue
            for attr in attributes:
                if attr.get('entity_id') == entity_id and '_state' in attr.get('feature'):
                    if attr.get('value') not in ['on']:
                        aklog_warn(f'{device_name} 状态未切换成 on, 当前状态: {attr.get("value")}')
                        fail_list.append(relay_info)
                    else:
                        aklog_debug(f'{device_name} 状态切换为 on 成功')
                    break
        for relay_off_info in relays_off:
            device_id = relay_off_info.get('device_id')
            entity_id = relay_off_info.get('entity_id')
            device_info = new_devices_info.get(device_id)
            device_name = device_info.get('name')
            attributes = device_info.get('attributes')
            if not device_info.get('online'):
                if not check_offline:
                    aklog_warn(f'设备 {device_name} 离线，不检查状态是否变化')
                else:
                    aklog_warn(f'设备 {device_name} 离线')
                    fail_list.append({'device_name': device_name, 'online': False})
                continue
            for attr in attributes:
                if attr.get('entity_id') == entity_id and '_state' in attr.get('feature'):
                    if attr.get('value') not in ['off']:
                        aklog_warn(f'{device_name} 状态未切换成 off, 当前状态: {attr.get("value")}')
                        fail_list.append(relay_off_info)
                    else:
                        aklog_debug(f'{device_name} 状态切换为 off 成功')
                    break

        if len(fail_list) > 0:
            aklog_warn(f'存在设备状态未变化：{fail_list}')
            return [False, '安防模式执行后，存在设备状态未切换']
        return [True, '设备状态已全部切换']

    def wait_all_device_state_switch_after_security_run(
            self, security_id=None, security_name=None, check_offline=True, timeout=15) -> list:
        """
        场景执行后，等待设备状态变化
        会检查space control、执行其他场景的设备状态变化
        Args:
            check_offline (bool): 是否检查离线设备，如果为True，离线设备也会当做失败
            security_id (str):
            security_name (str):
            timeout (int):
        """
        aklog_info(f'安防模式 {security_name or security_id} 执行后，等待所有设备状态切换')
        end_time = time.time() + timeout
        count = 0
        result = []
        while time.time() < end_time or count < 2:
            result = self.check_device_state_after_security_run(
                security_id, security_name, check_offline=check_offline)
            if result[0]:
                aklog_info('所有设备状态已切换')
                break
            time.sleep(2)
            count += 1
            continue
        return result

    # endregion

    # region 日志信息

    # endregion

    # region 照片墙相关

    def add_photo(self, device_name):
        """
        添加照片墙
        """
        device_id = self.get_device_id(device_name)
        send_data = {
            "type": "ak_photo/device_add_image",
            "image": ",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",
            "device_id": device_id
        }
        resp = self.ws_send_request(send_data)
        return resp
        # if resp and resp.get('success'):
        #     return True
        # else:
        #     aklog_debug('resp: %s' % resp)
        #     return False

    def delete_photo(self, device_name, photo_url):
        """
        添加照片墙
        """
        device_id = self.get_device_id(device_name)
        send_data = {
            "type": "ak_photo/batch_delete",
            "image_url_list": [
                photo_url
            ],
            "device_id": device_id
        }
        resp = self.ws_send_request(send_data)
        if resp and resp.get('success'):
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    # endregion

    # region Setting相关

    def set_language(self, language):
        """
        语言设置
        """
        set_lang = ""
        if language == 'CN':
            set_lang = "zh-CN"
        else:
            set_lang = "en-US"
        resp = self.ws_send_request({"type": "ak_config/update",
                                     "item": {
                                         "Settings.LANGUAGE.Type": set_lang}})
        res = resp['success']
        return res

    def set_device_Date(self):
        """日期时间设置"""
        date = str(datetime.date.today())
        time = datetime.time
        resp = self.ws_send_request({"type": "config/notice_change",
                                     "source": "web",
                                     "date": date,
                                     "time": "00:00:00",
                                     "Settings.TIME.Enabled24_HourTime": 1,
                                     "Settings.TIME.SetAutomaticallyEnabled": 0,
                                     "Settings.TIME.DateFormat": 5})
        res = resp['success']
        return res

    def set_security_code(self, code):
        """安防密码设置"""
        resp = self.ws_send_request({"type": "config/notice_change",
                                     "Settings.ALARM.Password": code,
                                     "source": "web"})
        res = resp['success']
        return res

    def set_sos(self, sos_staut, sos_number="123123"):
        """SOS设置"""

        resp1 = self.ws_send_request({"type": "ak_config/update",
                                      "item": {
                                          "Settings.SOS.CallNumberList": "burglary"
                                      }})

        resp2 = self.ws_send_request({"type": "ak_config/update",
                                      "item": {
                                          "Settings.SOS.Burglary": sos_number
                                      }})

        resp = self.ws_send_request({"type": "ak_config/update",
                                     "item": {
                                         "Settings.SOS.Enabled": sos_staut,
                                         "Settings.SOS.CallNumberList": "burglary"
                                     }})
        res = resp['success']
        return res

    def set_reset(self):
        """用户web点击reset"""
        resp = self.ws_send_request({"type": "config/ak_device/ctrl",
                                     "action": "reset",
                                     "reset_all": True})
        res = resp['success']
        return res

    def set_feedback(self):
        """用户web设置feedback"""
        resp = self.ws_send_request({"type": "ak_feedback/record",
                                     "content": "自动化测试"})
        res = resp['success']
        return res

    def set_measurement_settings(self):
        """用户web接口设置温度单位"""
        set_tmp = ''
        resp_get = self.ws_send_request({"type": "ak_config/get",
                                         "item": [
                                             "Settings.SYSTEM.TemperatureUnit"
                                         ]})
        get_tmp = resp_get['result']['Settings.SYSTEM.TemperatureUnit']
        if get_tmp == '1':
            set_tmp = 0
        else:
            set_tmp = 1
        resp_set = self.ws_send_request({
            "type": "ak_config/update",
            "item": {
                "Settings.SYSTEM.TemperatureUnit": set_tmp
            }
        })
        res = resp_set['success']
        return res

    def get_energy(self):
        """用户web获取能源数据"""
        resp_get = self.ws_send_request({"type": "config/ak_energy/info",
                                         "mode": 1})
        aklog_info(resp_get)
        res = resp_get['success']
        return res

    def get_datetime(self):
        """用户web获取datetime"""
        resp_get = self.ws_send_request({"type": "config/datetime/get"})
        datetime = resp_get['result'].get('datetime')
        aklog_info(datetime)
        return datetime

    # endregion

    # region 联系人相关

    def get_doorphone_list(self):
        data = {
            "type": "config/ak_device/doorphone/list"
        }
        resp = self.ws_send_request(data)
        self.doorphone_list = resp['result']
        return self.doorphone_list

    def add_local_doorphone_contact(self, **kwargs):
        """ 添加本地联系人
            kwargs:
        {
            "contact_name": "xxx",
            "call_num": "sip/ip",
            "http_display_name": "xxx",
            "http_type": "0 or 1",
            "ip": "192.168.88.xx",
            "user": "xxx",
            "passwd": "xxx",
            "door": "1;2;3;4",
            "command": "http://192.168.88.216/api/relay/trig?mode=0&num=2&level=1&delay=10",
            "door": "1;2;3;4",
            "dtmf_name1": "xxx",
            "dtmf1": "#",
            "dtmf_name2": "xxx",
            "dtmf2": "1",
            "dtmf_name3": "xxx",
            "dtmf2": "2",
        }
        """

        resp = self.ws_send_request(
            {
                "type": "contact/local/add",
                "name": kwargs.get('contact_name', ''),
                "call_num": kwargs.get('call_num', ''),
                "unlock_via_http": [{
                    "name": kwargs.get('http_display_name', ''),
                    "type": kwargs.get('http_type', ''),
                    "ip": kwargs.get('ip', ''),
                    "user": kwargs.get('user', ''),
                    "passwd": kwargs.get('passwd', ''),
                    "door": kwargs.get('door', ''),
                    "command": kwargs.get('command', '')
                }],
                "unlock_via_dtmf": [{
                    "name": kwargs.get('dtmf_name1', ''),
                    "dtmf": kwargs.get('dtmf1', '')
                },
                    {
                        "name": kwargs.get('dtmf_name2', ''),
                        "dtmf": kwargs.get('dtmf2', '')
                    },
                    {
                        "name": kwargs.get('dtmf_name3', ''),
                        "dtmf": kwargs.get('dtmf3', '')
                    }
                ],
                "monitor": {
                    "url": kwargs.get('rtsp_url', ''),
                    "user": kwargs.get('rtsp_username', ''),
                    "passwd": kwargs.get('rtsp_passwd', ''),
                    "display_in_call": 0
                },
                "contact_type": 0
            }
        )
        if resp and resp.get('success'):
            aklog_info('本地联系人添加成功')
            return True
        else:
            aklog_debug('resp: %s' % resp)
            return False

    def get_local_contact_list(self):
        """
        获取当前所有本地联系人信息
        return:
        [{'type': 0, 'image_type': 103, 'is_auto': True, 'manual': False, 'favorite': False,
            'scene_id': '1666943802163', 'name': '111', 'trigger_type': 'or', 'entity_id': 'automation.111',
             'auto_enabled': True, 'online': True, 'id': '1666943802163', 'alias': '111',
             'trigger': [{'platform': 'device', 'type': 'turned_on', 'device_id': 'd6c37f4bcfdfabb80d2c9430da2ef7d0c',
             'entity_id': 'switch.e85a27d19a5d795ef3475358b746e831a', 'domain': 'switch'}],
             'condition': [],
             'action': [{'send_http_url': '111'}]}]
        """
        resp = self.ws_send_request({"type": "contact/local/get"})
        self.local_contact_list = resp['result']
        return self.local_contact_list

    def delete_local_contact(self, contact_name):
        """ 删除本地联系人 """
        aklog_info()
        self.get_local_contact_list()
        ids = None
        for item in self.local_contact_list:
            if item['name'] == contact_name:
                ids = item['id']
        data = {
            "type": "contact/local/del",
            "ids": [
                ids
            ],
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_debug('delete_local_contact OK')
            return True
        else:
            aklog_error('delete_local_contact Fail')
            return False

    # endregion

    def check_device_states(self, devices, domain='switch'):
        # 存储设备状态信息
        state_details = []
        states = set()
        inconsistent_devices = []

        for device in devices:
            device_id = device['device_id']
            device_name = device['name']

            # 查找switch_state
            switch_state = None
            for attr in device['attributes']:
                if attr['domain'] == domain and attr['feature'] == f'{domain}_state':
                    switch_state = attr['value']
                    break

            # 记录设备状态
            if switch_state is not None:
                states.add(switch_state)
                state_details.append({
                    'name': device_name,
                    'device_id': device_id,
                    'state': switch_state,
                    'location': device['location']
                })

        # 检查状态一致性
        if len(states) == 1:
            all_state = next(iter(states))
            aklog_info(f"✅ 所有设备状态一致：均为 {all_state}")
            return True
        else:
            aklog_info(f"⚠️ 发现不一致的设备状态: {', '.join(states)}")
            aklog_info("\n不同状态的设备列表:")

            # 按状态分组
            groups = {}
            for dev in state_details:
                if dev['state'] not in groups:
                    groups[dev['state']] = []
                groups[dev['state']].append(dev)

            # 打印每组设备详情
            for state, devices in groups.items():
                aklog_info(f"\n【状态: {state}】")
                for dev in devices:
                    aklog_info(f"  设备名称: {dev['name']}")
                    aklog_info(f"  设备ID: {dev['device_id']}")
                    aklog_info(f"  位置: {dev['location']}")
                    aklog_info("  " + "-" * 30)

            return False

if __name__ == '__main__':
    userweb = AkubelaUserWebInfV3()
    device_info = {
        'device_name': 'hc_android_hypanel',
        'ip': '192.168.88.216'
    }
    device_config = config_parse_device_config('config_PS51_NORMAL')
    userweb.init(device_info, device_config)
    userweb.interface_init()
    # ret = userweb.control_device('light.db7cd6370b50dea4491121573f5e8d96', 'light', 'turn_off')
    # print(ret)
    aklog_info(userweb.get_devices_entity_id('Smoke Sensor(from bus)'))
    aklog_info(userweb.get_devices_entity_id('Smoke Sensor(Non-KNX)'))
    userweb.link_output_device('Smoke Sensor(Non-KNX)', 'Smoke Sensor(from bus)')
    # aklog_info(userweb.get_devices_list_info())
    # devices_list_info = userweb.get_devices_feature('HyPanel Ultra030300', 'sensor_temperature')
    # aklog_info(devices_list_info)
    # aklog_info(userweb.get_devices_feature('HyPanel Ultra030300', 'sensor_humidity'))
    # time.sleep(3)
    # ret = userweb.get_device_info('RGB Light-000002', attr='attributes')
    # print(ret)
    # tasks = [{'action': 'http', 'url': 'http://xxx'}]
    # userweb.create_update_scenes(tasks=tasks)
