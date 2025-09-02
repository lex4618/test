# -*- coding: UTF-8 -*-

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


class DeviceAdapter:
    """
    各个系列机型设备适配模块，可以弃用test_main模块，弃用params全局变量传递对象的方式（原来的方式不影响）
    在各机型的ControlBase模块中调用，通过传入device_name找到对应的device_info，获取对应机型的操作模块实例对象（UI界面、web、接口等）
    这样每个机型可以调用其他任何机型的操作模块方法
    """
    @staticmethod
    def akubela_cloud_init(account_type, url, user=None, pwd=None, login=False, cloud_obj=None):
        """
        家居云初始化
        account_type: supermanage/distributor/installer
        使用方法(可以在ControlBase里调用):
        def akubela_cloud_supermanage_init(self, url, user=None, pwd=None, login=False):
            self.supermanage = DeviceAdapter.akubela_cloud_init(
                'supermanage', url=url, user=user, pwd=pwd, login=login, cloud_obj=self.supermanage)
            self.intercom_supermanage = self.supermanage.intercom_inf
            return self.supermanage
        """
        aklog_info()
        if not cloud_obj or not cloud_obj.device_info:
            cloud_base = get_base_module_by_class_name('base_AKUBELACLOUD_NORMAL')
            if account_type == 'supermanage':
                cloud_obj = cloud_base.supermanage_init()
            elif account_type == 'distributor':
                cloud_obj = cloud_base.distributor_init()
            elif account_type == 'installer':
                cloud_obj = cloud_base.installer_init()

        cloud_obj.init(url, user, pwd)
        cloud_obj.clear_headers()
        if login and user is not None and pwd is not None:
            cloud_obj.login()
        return cloud_obj

    @staticmethod
    def android_hypanel_init(device_name, ha_username=None, ha_password=None, login=False, web_env_init=False,
                             connect_type='lan', android_hypanel=None):
        """
        android_hyperpanel设备初始化
        使用方法(可以在ControlBase里调用):
        def hc_android_hypanel_init(self, ha_username=None, ha_password=None, login=False, web_env_init=False,
                            reinit=False, connect_type='lan'):
            self.hc_android_hypanel = DeviceAdapter.android_hypanel_init(
                'hc_android_hypanel', ha_username=ha_username, ha_password=ha_password, login=login,
                web_env_init=web_env_init, connect_type=connect_type)
            self.hc_android_hypanel_web = self.hc_android_hypanel.browser
            self.hc_android_hypanel_userweb_inf = self.hc_android_hypanel.user_web_inf
            return self.hc_android_hypanel
        """
        aklog_info()
        if not android_hypanel or not android_hypanel.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            ui_obj = AndroidBaseU2(device_info, device_config, wait_time=2)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            android_hypanel = get_base_module_by_device_config(device_config)
            android_hypanel.put_connect_type(connect_type)
            android_hypanel.init(ui_obj)

            android_hypanel_web = android_hypanel.browser
            android_hypanel_web.put_connect_type(connect_type)
            android_hypanel.browser_init(browser_obj, login=False)
        else:
            android_hypanel.put_connect_type(connect_type)
            android_hypanel.init()

            android_hypanel_web = android_hypanel.browser
            android_hypanel_web.put_connect_type(connect_type)
            android_hypanel.browser_init(login=False)

        if login:
            android_hypanel_web.start_and_login()
            if web_env_init:
                android_hypanel_web.web_env_init()

        android_hypanel_userweb_inf = android_hypanel.userweb_interface_init(ha_username, ha_password)
        android_hypanel_userweb_inf.put_login_type('local')
        return android_hypanel

    @staticmethod
    def android_hypanel_pro_init(device_name, ha_username=None, ha_password=None, login=False, web_env_init=False,
                                 connect_type='lan', android_hypanel_pro=None):
        """
        android_hypanel_pro设备初始化
        使用方法(可以在ControlBase里调用):
        def hc_android_hypanel_pro_init(self, ha_username=None, ha_password=None, login=False, web_env_init=False,
                            reinit=False, connect_type='lan'):
            self.hc_android_hypanel_pro = DeviceAdapter.android_hypanel_pro_init(
                'hc_android_hypanel_pro', ha_username=ha_username, ha_password=ha_password, login=login,
                web_env_init=web_env_init, connect_type=connect_type, android_hypanel_pro=self.hc_android_hypanel_pro)
            self.hc_android_hypanel_pro_web = self.hc_android_hypanel_pro.browser
            self.hc_android_hypanel_pro_userweb_inf = self.hc_android_hypanel_pro.user_web_inf
            return self.hc_android_hypanel_pro
        """
        aklog_info()
        if not android_hypanel_pro or not android_hypanel_pro.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            ui_obj = AndroidBaseU2(device_info, device_config, wait_time=2)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            android_hypanel_pro = get_base_module_by_device_config(device_config)
            android_hypanel_pro.put_connect_type(connect_type)
            android_hypanel_pro.init(ui_obj)

            android_hypanel_pro_web = android_hypanel_pro.browser
            android_hypanel_pro_web.put_connect_type(connect_type)
            android_hypanel_pro.browser_init(browser_obj, login=False)
        else:
            android_hypanel_pro.put_connect_type(connect_type)
            android_hypanel_pro.init()

            android_hypanel_pro_web = android_hypanel_pro.browser
            android_hypanel_pro_web.put_connect_type(connect_type)
            android_hypanel_pro.browser_init(login=False)

        if login:
            android_hypanel_pro_web.start_and_login()
            if web_env_init:
                android_hypanel_pro_web.web_env_init()

        android_hypanel_pro_userweb_inf = android_hypanel_pro.user_web_inf
        android_hypanel_pro.userweb_interface_init(ha_username, ha_password)
        # 用户web默认使用本地方式登录，每个需要用到用户web的用例，在调用这个control_base方法时都重新设置login_type
        android_hypanel_pro_userweb_inf.put_login_type('local')

        return android_hypanel_pro

    @staticmethod
    def android_smartpanel_init(device_name, ha_username=None, ha_password=None, login=False, web_env_init=False,
                                android_smartpanel=None):
        """
        android_smartpanel设备初始化，家庭中心
        使用方法(可以在ControlBase里调用):
        def slave1_android_smartpanel_init(self, ha_username, ha_password, login=False, web_env_init=False):
            self.hc_android_smartpanel = DeviceAdapter.android_smartpanel_init(
                'hc_android_smartpanel', ha_username=ha_username, ha_password=ha_password,
                login=login, web_env_init=web_env_init)
            self.hc_android_smartpanel_web = self.hc_android_smartpanel.browser
            self.hc_android_smartpanel_userweb_inf = self.hc_android_smartpanel.user_web_inf
            return self.hc_android_smartpanel
        """
        aklog_info()
        if not android_smartpanel or not android_smartpanel.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            ui_obj = AndroidBaseU2(device_info, device_config, wait_time=2)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            android_smartpanel = get_base_module_by_device_config(device_config)
            android_smartpanel.init(ui_obj)

            android_smartpanel_web = android_smartpanel.browser_init(browser_obj, login=False)
        else:
            android_smartpanel_web = android_smartpanel.browser

        android_smartpanel_userweb_inf = android_smartpanel.user_web_inf
        android_smartpanel.userweb_interface_init(ha_username, ha_password)
        # 用户web默认使用本地方式登录，每个需要用到用户web的用例，在调用这个control_base方法时都重新设置login_type
        android_smartpanel_userweb_inf.put_login_type('local')

        if login:
            android_smartpanel_web.start_and_login()
            if web_env_init:
                android_smartpanel_web.web_env_init()

        return android_smartpanel

    @staticmethod
    def linux_hypanel_init(device_name, login=False, web_env_init=False, linux_hypanel=None):
        """
        linux hyperpanel作为子网关设备初始化
        使用方法(可以在ControlBase里调用):
        def slave1_linux_hyperpanel_init(self, login=False, web_env_init=False):
            self.slave1_linux_hyperpanel = DeviceAdapter.linux_hypanel_init(
                'slave1_linux_hyperpanel', login=login, web_env_init=web_env_init,
                linux_hypanel=self.slave1_linux_hyperpanel)
            self.slave1_linux_hyperpanel_web = self.slave1_linux_hyperpanel.web
            return self.slave1_linux_hyperpanel
        """
        aklog_info()
        if not linux_hypanel or not linux_hypanel.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            linux_hypanel = get_base_module_by_device_config(browser_obj)
            linux_hypanel.init(browser_obj)

        linux_hypanel_web = linux_hypanel.web
        if login:
            linux_hypanel_web.start_and_login()
            if web_env_init:
                linux_hypanel_web.web_env_init()
        return linux_hypanel

    @staticmethod
    def belahome_init(device_name, username=None, password=None, server_name=None, belahome=None):
        """
        初始化belahome APP
        使用方法(可以在ControlBase里调用):
        def belahome_admin_init(self, username=None, password=None, server_name=None):
            self.belahome_admin = DeviceAdapter.belahome_init(
                'belahome_admin', username=username, password=password, server_name=server_name,
                belahome=self.belahome_admin)
            return self.belahome_admin
        """
        aklog_info()
        if not belahome or not belahome.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            ui_obj = AndroidBaseU2(device_info, device_config, wait_time=2)

            belahome = get_base_module_by_device_config(device_config)
            belahome.init(ui_obj)

        if username and password:
            belahome.put_username_password(username, password)
        if server_name:
            belahome.put_server_name(server_name)
        return belahome

    @staticmethod
    def belahome_ios_init(device_name, username=None, password=None, server_name=None, belahome=None):
        """
        初始化belahome APP
        使用方法(可以在ControlBase里调用):
        def belahome_admin_init(self, username=None, password=None, server_name=None):
            self.belahome_admin = DeviceAdapter.belahome_ios_init(
                'belahome_admin', username=username, password=password, server_name=server_name,
                belahome=self.belahome_admin)
            return self.belahome_admin
        """
        aklog_info()
        if not belahome or not belahome.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            ui_obj = IOSBaseU2(device_info, device_config, wait_time=2)

            belahome = get_base_module_by_device_config(device_config)
            belahome.init(ui_obj)

        if username and password:
            belahome.put_username_password(username, password)
        if server_name:
            belahome.put_server_name(server_name)
        return belahome

    @staticmethod
    def android_door_init(device_name, login=False, web_env_init=False, android_door=None):
        """
        android door设备初始化
        使用方法(可以在ControlBase里调用):
        def slave_android_door_init(self, login=False, web_env_init=False):
            self.slave_android_door = DeviceAdapter.android_door_init(
                'slave3_android_door', login=login, web_env_init=web_env_init,
                android_door=self.slave_android_door)
            self.slave_android_door_web = self.slave_android_door.browser
            return self.slave_android_door
        """
        aklog_info()
        if not android_door or not android_door.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            device_android_door = Android_Door(device_info, device_config)
            ui_obj = AndroidBase(device_android_door, wait_time=2)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            android_door = get_base_module_by_device_config(device_config)
            android_door.init(ui_obj)

            android_door_web = android_door.browser_init(browser_obj, login=False)
        else:
            android_door_web = android_door.browser

        if login:
            android_door_web.start_and_login()
            if web_env_init:
                android_door_web.web_env_init()
        return android_door

    @staticmethod
    def android_door_u2_init(device_name, login=False, web_env_init=False, android_door=None):
        """
        android_door初始化
        使用方法(可以在ControlBase里调用):
        def master_android_door_init(self, login=False, web_env_init=False):
            self.master_android_door = DeviceAdapter.android_door_u2_init(
                'master_android_door', login=login, web_env_init=web_env_init,
                 android_door=self.master_android_door)
            self.master_droid_indoor_web = self.master_android_door.browser
            return self.master_android_door
        """
        aklog_info()
        if not android_door or not android_door.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            ui_obj = AndroidBaseU2(device_info, device_config, wait_time=2)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            android_door = get_base_module_by_device_config(device_config)
            android_door.init(ui_obj)

            android_door_web = android_door.browser_init(browser_obj, login=False)
        else:
            android_door_web = android_door.browser
        if login:
            android_door_web.start_and_login()
            if web_env_init:
                android_door_web.web_env_init()
        return android_door

    @staticmethod
    def linux_door_init(device_name, login=False, web_env_init=False, linux_door=None):
        """
        linux_door初始化
        使用方法(可以在ControlBase里调用):
        def slave_linux_door_init(self, login=False):
            self.slave_linux_door = DeviceAdapter.linux_door_init(
                'slave_linux_door', login=login, linux_door=self.slave_linux_door)
            return self.slave_linux_door
        """
        aklog_info()
        if not linux_door or not linux_door.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            linux_door = get_base_module_by_device_config(device_config)
            linux_door.linux_door_init(browser_obj, login=False)

        if login:
            linux_door.start_and_login()
            if web_env_init:
                linux_door.web_env_init()
        return linux_door

    @staticmethod
    def linux_door_web40_init(device_name, login=False, linux_door=None):
        """
        linux_door初始化， web40版本，X912机型base不再继承web，初始化方法不太一样
        使用方法(可以在ControlBase里调用):
        def slave_linux_door_init(self, login=False):
            self.slave_linux_door = DeviceAdapter.linux_door_web40_init(
                'slave_linux_door', login=login, linux_door=self.slave_linux_door)
            self.slave_linux_door_web = self.slave_linux_door.browser
            return self.slave_linux_door
        """
        aklog_info()
        if not linux_door or not linux_door.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            linux_door = get_base_module_by_device_config(device_config)
            linux_door.linux_door_init(browser_obj, login=False)
            linux_door_web = linux_door.browser
        else:
            linux_door_web = linux_door.browser
        if login:
            linux_door_web.start_and_login()
        return linux_door

    @staticmethod
    def linux_indoor_init(device_name, login=False, linux_indoor=None):
        """
        linux_indoor初始化
        使用方法(可以在ControlBase里调用):

        """
        aklog_info()
        if not linux_indoor or not linux_indoor.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)
            linux_indoor = get_base_module_by_device_config(device_config)
            linux_indoor.init_without_start(browser_obj)
        if login:
            linux_indoor.start_and_login()
        return linux_indoor

    @staticmethod
    def linux_indoor_inf_init(device_name, login=False, web_env_init=False, linux_indoor=None):
        """
        linux_indoor 支持web4.0接口的机型，初始化
        使用方法(可以在ControlBase里调用):

        """
        aklog_info()
        if not linux_indoor or not linux_indoor.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            ui_obj = libbrowser(device_info, device_config, wait_time=2)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            linux_indoor = get_base_module_by_device_config(device_config)
            linux_indoor.init(ui_obj)
            linux_indoor_web = linux_indoor.browser_init(browser_obj, login=False, web_env_init=False)
            linux_indoor.web_interface_init()
        else:
            linux_indoor_web = linux_indoor.web

        if login:
            linux_indoor_web.start_and_login()
            if web_env_init:
                linux_indoor_web.web_env_init()

        return linux_indoor

    @staticmethod
    def android_indoor_init(device_name, login=False, web_env_init=False, android_indoor=None):
        """
        android_indoor初始化
        使用方法(可以在ControlBase里调用):
        def master_android_indoor_init(self, login=False, web_env_init=False):
            self.master_android_indoor = DeviceAdapter.android_indoor_init(
                'master_android_indoor', login=login, web_env_init=web_env_init,
                 android_indoor=self.master_android_indoor)
            self.master_android_indoor_web = self.master_android_indoor.browser
            return self.master_android_indoor
        """
        aklog_info()
        if not android_indoor or not android_indoor.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            device_android_indoor = Android_Indoor(device_info, device_config)
            ui_obj = AndroidBase(device_android_indoor, wait_time=2)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            android_indoor = get_base_module_by_device_config(device_config)
            android_indoor.init(ui_obj)

            android_indoor_web = android_indoor.browser_init(browser_obj, login=False)
        else:
            android_indoor_web = android_indoor.browser
        if login:
            android_indoor_web.start_and_login()
            if web_env_init:
                android_indoor_web.web_env_init()
        return android_indoor

    @staticmethod
    def android_indoor_u2_init(device_name, login=False, web_env_init=False, android_indoor=None):
        """
        android_indoor初始化
        使用方法(可以在ControlBase里调用):
        def master_android_indoor_init(self, login=False, web_env_init=False):
            self.master_android_indoor = DeviceAdapter.android_indoor_u2_init(
                'master_android_indoor', login=login, web_env_init=web_env_init,
                 android_indoor=self.master_android_indoor)
            self.master_android_indoor_web = self.master_android_indoor.browser
            return self.master_android_indoor
        """
        aklog_info()
        if not android_indoor or not android_indoor.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            ui_obj = AndroidBaseU2(device_info, device_config, wait_time=2)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            android_indoor = get_base_module_by_device_config(device_config)
            android_indoor.init(ui_obj)

            android_indoor_web = android_indoor.browser_init(browser_obj, login=False)
        else:
            android_indoor_web = android_indoor.browser
        if login:
            android_indoor_web.start_and_login()
            if web_env_init:
                android_indoor_web.web_env_init()
        return android_indoor

    @staticmethod
    def guard_phone_init(device_name, login=False, guard_phone=None):
        """
        guard_phone初始化
        使用方法(可以在ControlBase里调用):

        """
        aklog_info()
        if not guard_phone or not guard_phone.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            device_guard_phone = Android_Guard_Phone(device_info, device_config)
            ui_obj = AndroidBase(device_guard_phone, wait_time=2)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            guard_phone = get_base_module_by_device_config(device_config)
            guard_phone.init(ui_obj)

            guard_phone_web = guard_phone.web_init(browser_obj)
        else:
            guard_phone_web = guard_phone.web
        if login:
            guard_phone_web.start_and_login()
        return guard_phone

    @staticmethod
    def access_door_init(device_name, login=False, web_env_init=False, access_door=None):
        """
        AccessDoor初始化
        使用方法(可以在ControlBase里调用):

        """
        aklog_info()
        if not access_door or not access_door.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            access_door = get_base_module_by_device_config(device_config)
            access_door_web = access_door.init(browser_obj)
        else:
            access_door_web = access_door.web
        if login:
            access_door_web.start_and_login()
            if web_env_init:
                access_door_web.web_env_init()
                access_door_web.enter_test_page()
        return access_door

    @staticmethod
    def access_control_init(device_name, login=False, web_env_init=False, access_control=None):
        """
        access_control初始化
        使用方法(可以在ControlBase里调用):

        """
        aklog_info()
        if not access_control or not access_control.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            access_control = get_base_module_by_device_config(device_config)
            access_control_web = access_control.init(browser_obj)
        else:
            access_control_web = access_control.web
        if login:
            access_control_web.start_and_login()
            if web_env_init:
                access_control_web.web_env_init()
        return access_control

    @staticmethod
    def zigbee_tool_init(device_name, login=False, web_env_init=False, zigbee_tool=None):
        """
        ZigBee测具初始化
        使用方法(可以在ControlBase里调用):
        def zigbee_tool_init(self, login=False, web_env_init=False):
            self.zigbee_tool = DeviceAdapter.zigbee_tool_init(
                'zigbee_tool', login=login, web_env_init=web_env_init, zigbee_tool=self.zigbee_tool)
            self.zigbee_tool_web = self.zigbee_tool.web
            return self.zigbee_tool
        """
        aklog_info()
        if not zigbee_tool or not zigbee_tool.device_info:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            browser_obj = libbrowser(device_info, device_config, wait_time=2)

            zigbee_tool = get_base_module_by_device_config(device_config)
            zigbee_tool.init(browser_obj)
        zigbee_tool_web = zigbee_tool.web

        if login:
            zigbee_tool_web.start_and_login()
            if web_env_init:
                zigbee_tool_web.web_env_init()
        return zigbee_tool

    @staticmethod
    def sdmc_init(user=None, pwd=None, sdmc=None):
        """
        SDMC初始化
        """
        aklog_info()
        if sdmc is None:
            sdmc_dir = param_get_excel_data()['exe_info'][0]['sdmc_dir']
            sdmc = get_base_module_by_class_name('base_SDMC_NORMAL')
            sdmc.init(sdmc_dir, user, pwd)
        return sdmc

    @staticmethod
    def smart_plus_emu_init(smart_plus_emu=None):
        """
        SmartPlus模拟器初始化
        """
        aklog_info()
        if not smart_plus_emu:
            device_info = {'device_name': 'smart_plus_emu'}
            device_config = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
            smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                                  'AppEmulator.exe' % (root_path, param_get_cloud_version())
            win_obj = WindowBase(smart_plus_emu_path, device_info, device_config)

            smart_plus_emu = get_base_module_by_device_config(device_config)
            smart_plus_emu.init(win_obj)
        return smart_plus_emu

    @staticmethod
    def dev_emu_init(device_name, dev_emu=None):
        """
        设备模拟器初始化
        使用方法(可以在ControlBase里调用)：
        def dev_emu_init(self, device_name, dev_emu=None):
            self.dev_emu = DeviceAdapter.dev_emu_init(device_name, dev_emu=self.dev_emu)
            return self.dev_emu
        """
        aklog_info()
        if not dev_emu or not dev_emu.device_info:
            dev_emu_version_branch = param_get_version_branch_info()['DeviceEmulator_branch']
            model_name = param_get_model_name()
            device_info_master = get_device_info_by_device_name('master_android_indoor')
            master_device_ip = device_info_master['ip'].split('.')[3]
            emu_dir = os.path.join(root_path, 'tools', 'DeviceEmulator', dev_emu_version_branch,
                                   'Emulator_Door_for_%s_%s' % (model_name, master_device_ip))
            emu_path = os.path.join(emu_dir, 'EmulatorBase.exe')

            device_info_door_emulator = get_device_info_by_device_name(device_name)
            device_config_common = config_parse_device_config('config_NORMAL')
            win_obj = WindowBase(emu_path, device_info_door_emulator, device_config_common)

            dev_emu = get_base_module_by_class_name('base_DEVICEEMULATOR_NORMAL')
            dev_emu.init(win_obj)
        return dev_emu


    @staticmethod
    def smartplus_init(device_name, username=None, password=None, server_name=None, smartplus=None):
        """
        初始化smartplus APP
        使用方法(可以在ControlBase里调用):
        def slave1_smartplus_init(self, username=None, password=None, server_name=None):
            self.slave1_smartplus = DeviceAdapter.smartplus_init(
                'slave1_smartplus', username=username, password=password, server_name=server_name,
                smartplus=self.belahome_admin)
            return self.slave1_smartplus
        """
        aklog_info()
        if not smartplus:
            device_info = get_device_info_by_device_name(device_name)
            if not device_info:
                raise Exception('device_info中不存在设备 %s 的信息' % device_name)
            device_config = config_parse_device_config(device_info['config_module'], device_name)
            ui_obj = AndroidBaseU2(device_info, device_config, wait_time=2)

            smartplus = get_base_module_by_device_config(device_config)
            smartplus.init(ui_obj)

        if username and password:
            smartplus.put_username_password(username, password)
        if server_name:
            smartplus.put_server_name(server_name)
        return smartplus