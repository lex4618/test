# -*- coding: UTF-8 -*-
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


def test_main_linux_door():
    config_module = param_get_config_module()
    linux_door_xml_data = param_get_excel_data()

    # 初始化主设备web端
    device_info_master = get_device_info_by_device_name('master_linux_door')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_door_browser_master(browser_master)

    # 初始化嵌入式室内机辅助设备web端
    device_info_slave1 = get_device_info_by_device_name('slave1_linux_indoor')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    browser_slave1 = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_linuxindoor_browser_slave1(browser_slave1)

    # 初始化辅助压测的门口机设备web端
    # device_info_door_slave2 = get_device_info_by_device_name('slave2_linux_door')
    # device_config_door_slave2 = config_parse_device_config(device_info_door_slave2['config_module'])
    # browser_door_slave2 = libbrowser(device_info_door_slave2, device_config_door_slave2, wait_time=2)
    # param_put_door_browser_slave2(browser_door_slave2)

    # 初始化辅助压测的门禁设备
    device_info_access_control_slave2 = get_device_info_by_device_name('slave2_access_control')
    device_config_access_control_slave2 = config_parse_device_config(
        device_info_access_control_slave2['config_module'])
    browser_access_control_slave2 = libbrowser(device_info_access_control_slave2,
                                               device_config_access_control_slave2, wait_time=2)
    param_put_access_control_browser_slave2(browser_access_control_slave2)

    # 初始化SDMC
    device_config_common = config_parse_device_config('config_NORMAL')
    sdmc_path = linux_door_xml_data['exe_info'][0]['exe_path']  # [0]表示选择的设备在第一行，[1]表示选择的设备在第二行，以此类推
    sdmc = akwin(sdmc_path, device_config_common, 'uia')
    param_put_sdmc(sdmc)

    # 初始化SDMC ServerManage
    sdmc_server_manage_path = linux_door_xml_data['exe_info'][0]['sdmc_server_manage_path']
    sdmc_server_manage = akwin(sdmc_server_manage_path, device_config_common, 'uia')
    param_put_sdmc_server_manage(sdmc_server_manage)

    # 初始化UpgradeTool
    upgrade_tool_path = device_config_common.get_upgrade_tool_path()
    upgrade_tool = akwin(upgrade_tool_path, device_config_common, 'uia')
    param_put_upgrade_tool(upgrade_tool)

    # 初始化自检工具
    selftestdassistant_path = device_config_master.get_selftestdassistant_path()
    selftestdassistant = akwin(selftestdassistant_path, device_config_master, 'uia')
    param_put_selftestdassistant(selftestdassistant)

    # 初始化管理机辅助设备
    device_info_slave1_video_phone = get_device_info_by_device_name('slave_management')
    device_config_slave1_video_phone = config_parse_device_config(device_info_slave1_video_phone['config_module'])
    device_slave1_video_phone = Android_Guard_Phone(device_info_slave1_video_phone,
                                                    device_config_slave1_video_phone)
    app_slave1_video_phone = AndroidBase(device_slave1_video_phone, wait_time=2)
    param_put_guardphone_app_slave1(app_slave1_video_phone)
    browser_slave1_video_phone = libbrowser(device_info_slave1_video_phone, device_config_slave1_video_phone,
                                            wait_time=2)
    param_put_guardphone_browser_slave1(browser_slave1_video_phone)

    # 初始化设备模拟器
    dev_emu_version_branch = param_get_version_branch_info()['DeviceEmulator_branch']
    model_name = param_get_model_name()
    master_device_ip = device_info_master['ip'].split('.')[3]
    emu_dir = os.path.join(root_path, 'tools', 'DeviceEmulator', dev_emu_version_branch,
                           'Emulator_Indoor_for_%s_%s' % (model_name, master_device_ip))
    emu_path = os.path.join(emu_dir, 'EmulatorBase.exe')
    indoor_emu_app = akwin(emu_path, device_config_common, 'uia')
    param_put_indoor_emulator(indoor_emu_app)

    # 初始化SmartPlus模拟器
    device_config_smart_plus_emu = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
    device_info_smart_plus_emu = {'device_name': 'smart_plus_emu'}
    smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                          'AppEmulator.exe' % (root_path, param_get_cloud_version())
    smart_plus_emu = WindowBase(smart_plus_emu_path, device_info_smart_plus_emu, device_config_smart_plus_emu)
    param_put_smart_plus_emu_slave1(smart_plus_emu)

    # 初始化音频测具
    Ip_Measuring_tool_device_info = get_device_info_by_device_name('Ip_Measuring_tool')
    if 'audio_test_enable' in device_info_master:
        audio_test_enable = int(device_info_master['audio_test_enable'])
    else:
        audio_test_enable = 0
    if Ip_Measuring_tool_device_info and audio_test_enable == 1:
        dev_tester = akdevctrl_tester()
        r = dev_tester.creat(Ip_Measuring_tool_device_info['ip'], 90)
        if not r:
            aklog_printf("tester connect failed!")
        param_put_devctrl(dev_tester)


def test_main_android_door():
    config_module = param_get_config_module()
    android_door_xml_data = param_get_excel_data()

    # 初始化梯口机设备
    device_info_master = get_device_info_by_device_name('master_android_door')
    if device_info_master:
        device_config_master = config_parse_device_config(config_module)
        param_put_device_config(device_config_master)

        device_master = Android_Door(device_info_master, device_config_master)
        androiddoor_app_master = AndroidBase(device_master, wait_time=2)
        # androiddoor_app_master.appium.StartAdbServer()
        # androiddoor_app_master.appium.connect_adb_by_usb()
        # androiddoor_app_master.AppRun()
        param_put_androiddoor_app_master(androiddoor_app_master)

        browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
        param_put_door_browser_master(browser_master)

    # 初始化室内机辅助设备1
    device_info_slave1 = get_device_info_by_device_name('slave1_android_indoor')
    if device_info_slave1:
        device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
        device_slave1_android_indoor = Android_Indoor(device_info_slave1, device_config_slave1)
        slave1_android_indoor = AndroidBase(device_slave1_android_indoor, wait_time=2)
        param_put_androidindoor_app_slave1(slave1_android_indoor)

        browser_slave1_android_indoor = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
        param_put_androidindoor_browser_slave1(browser_slave1_android_indoor)

    # 初始化室内机辅助设备2
    device_info_slave2 = get_device_info_by_device_name('slave2_android_indoor')
    if device_info_slave2:
        device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
        device_slave2_android_indoor = Android_Indoor(device_info_slave2, device_config_slave2)
        slave2_android_indoor = AndroidBase(device_slave2_android_indoor, wait_time=2)
        param_put_androidindoor_app_slave2(slave2_android_indoor)

        browser_slave2_android_indoor = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
        param_put_androidindoor_browser_slave2(browser_slave2_android_indoor)

    # 初始化嵌入式室内机辅助设备3 ,用于代替辅助设备2
    device_info_slave3 = get_device_info_by_device_name('slave3_linux_indoor')
    if device_info_slave3:
        device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
        browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
        param_put_linuxindoor_browser_slave3(browser_slave3)

    # 初始化SmartPlus端
    device_info_smartplus = get_device_info_by_device_name('slave_app_smartplus')
    if device_info_smartplus:
        device_config_smartplus = config_parse_device_config('config_SMARTPLUS_NORMAL')
        device_smartplus = SmartPlus_Android(device_info_smartplus, device_config_smartplus)
        smartplus_app = AndroidBase(device_smartplus, wait_time=2)
        # smartplus_app.AppRun()
        param_put_smartplus_app_slave1(smartplus_app)

    # 初始化SmartPlus模拟器
    device_config_smart_plus_emu = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
    if device_config_smart_plus_emu:
        device_info_smart_plus_emu = {'device_name': 'smart_plus_emu'}
        smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                              'AppEmulator.exe' % (root_path, param_get_cloud_version())
        smart_plus_emu = WindowBase(smart_plus_emu_path, device_info_smart_plus_emu, device_config_smart_plus_emu)
        param_put_smart_plus_emu_slave1(smart_plus_emu)

    # 初始化管理机辅助设备
    device_info_slave1_guardphone = get_device_info_by_device_name('slave_management')
    if device_info_slave1_guardphone:
        device_config_slave1_guardphone = config_parse_device_config(device_info_slave1_guardphone['config_module'])
        device_slave1_guardphone = Android_Guard_Phone(device_info_slave1_guardphone,
                                                       device_config_slave1_guardphone)
        app_slave1_guardphone = AndroidBase(device_slave1_guardphone, wait_time=2)
        param_put_guardphone_app_slave1(app_slave1_guardphone)
        browser_slave1_guardphone = libbrowser(device_info_slave1_guardphone, device_config_slave1_guardphone,
                                               wait_time=2)
        param_put_guardphone_browser_slave1(browser_slave1_guardphone)

    # 初始化辅助压测的门禁设备
    device_info_access_control_slave2 = get_device_info_by_device_name('slave2_access_control')
    if device_info_access_control_slave2:
        device_config_access_control_slave2 = config_parse_device_config(
            device_info_access_control_slave2['config_module'])
        browser_access_control_slave2 = libbrowser(device_info_access_control_slave2,
                                                   device_config_access_control_slave2, wait_time=2)
        param_put_access_control_browser_slave2(browser_access_control_slave2)

    # 初始化SDMC
    device_config_common = config_parse_device_config('config_NORMAL')
    if device_config_common:
        sdmc_path = android_door_xml_data['exe_info'][0]['exe_path']  # [0]表示选择的设备在第一行，[1]表示选择的设备在第二行，以此类推
        sdmc = akwin(sdmc_path, device_config_common, 'uia')
        param_put_sdmc(sdmc)

    # 初始化SDMC ServerManage
    sdmc_server_manage_path = android_door_xml_data['exe_info'][0]['sdmc_server_manage_path']
    sdmc_server_manage = akwin(sdmc_server_manage_path, device_config_common, 'uia')
    param_put_sdmc_server_manage(sdmc_server_manage)

    # 初始化设备模拟器
    dev_emu_version_branch = param_get_version_branch_info()['DeviceEmulator_branch']
    model_name = param_get_model_name()
    master_device_ip = device_info_master['ip'].split('.')[3]
    emu_dir = os.path.join(root_path, 'tools', 'DeviceEmulator', dev_emu_version_branch,
                           'Emulator_Indoor_for_%s_%s' % (model_name, master_device_ip))
    emu_path = os.path.join(emu_dir, 'EmulatorBase.exe')
    indoor_emu_app = akwin(emu_path, device_config_common, 'uia')
    param_put_indoor_emulator(indoor_emu_app)

    # 初始化音频测具
    Ip_Measuring_tool_device_info = get_device_info_by_device_name('Ip_Measuring_tool')
    if 'audio_test_enable' in device_info_master:
        audio_test_enable = int(device_info_master['audio_test_enable'])
    else:
        audio_test_enable = 0
    if Ip_Measuring_tool_device_info and audio_test_enable == 1:
        dev_tester = akdevctrl_tester()
        r = dev_tester.creat(Ip_Measuring_tool_device_info['ip'], 90)
        if not r:
            aklog_printf("tester connect failed!")
        param_put_devctrl(dev_tester)


def test_main_android_doorU2():
    config_module = param_get_config_module()
    android_door_xml_data = param_get_excel_data()

    # 初始化梯口机设备
    device_info_master = get_device_info_by_device_name('master_android_door')
    if device_info_master:
        device_config_master = config_parse_device_config(config_module)
        param_put_device_config(device_config_master)

        master_android_door = AndroidBaseU2(device_info_master, device_config_master, wait_time=2)
        param_put_androiddoor_app_master(master_android_door)
        browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
        param_put_door_browser_master(browser_master)

    # 初始化室内机辅助设备1
    device_info_slave1 = get_device_info_by_device_name('slave1_android_indoor')
    if device_info_slave1:
        device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
        device_slave1_android_indoor = Android_Indoor(device_info_slave1, device_config_slave1)
        slave1_android_indoor = AndroidBase(device_slave1_android_indoor, wait_time=2)
        param_put_androidindoor_app_slave1(slave1_android_indoor)

        browser_slave1_android_indoor = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
        param_put_androidindoor_browser_slave1(browser_slave1_android_indoor)

    # 初始化室内机辅助设备2
    device_info_slave2 = get_device_info_by_device_name('slave2_android_indoor')
    if device_info_slave2:
        device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
        device_slave2_android_indoor = Android_Indoor(device_info_slave2, device_config_slave2)
        slave2_android_indoor = AndroidBase(device_slave2_android_indoor, wait_time=2)
        param_put_androidindoor_app_slave2(slave2_android_indoor)

        browser_slave2_android_indoor = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
        param_put_androidindoor_browser_slave2(browser_slave2_android_indoor)

    # 初始化嵌入式室内机辅助设备3 ,用于代替辅助设备2
    device_info_slave3 = get_device_info_by_device_name('slave3_linux_indoor')
    if device_info_slave3:
        device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
        browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
        param_put_linuxindoor_browser_slave3(browser_slave3)

    # 初始化SmartPlus端
    device_info_smartplus = get_device_info_by_device_name('slave_app_smartplus')
    if device_info_smartplus:
        device_config_smartplus = config_parse_device_config('config_SMARTPLUS_NORMAL')
        device_smartplus = SmartPlus_Android(device_info_smartplus, device_config_smartplus)
        smartplus_app = AndroidBase(device_smartplus, wait_time=2)
        # smartplus_app.AppRun()
        param_put_smartplus_app_slave1(smartplus_app)

    # 初始化SmartPlus模拟器
    device_config_smart_plus_emu = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
    if device_config_smart_plus_emu:
        device_info_smart_plus_emu = {'device_name': 'smart_plus_emu'}
        smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                              'AppEmulator.exe' % (root_path, param_get_cloud_version())
        smart_plus_emu = WindowBase(smart_plus_emu_path, device_info_smart_plus_emu, device_config_smart_plus_emu)
        param_put_smart_plus_emu_slave1(smart_plus_emu)

    # 初始化管理机辅助设备
    device_info_slave1_guardphone = get_device_info_by_device_name('slave_management')
    if device_info_slave1_guardphone:
        device_config_slave1_guardphone = config_parse_device_config(device_info_slave1_guardphone['config_module'])
        device_slave1_guardphone = Android_Guard_Phone(device_info_slave1_guardphone,
                                                       device_config_slave1_guardphone)
        app_slave1_guardphone = AndroidBase(device_slave1_guardphone, wait_time=2)
        param_put_guardphone_app_slave1(app_slave1_guardphone)
        browser_slave1_guardphone = libbrowser(device_info_slave1_guardphone, device_config_slave1_guardphone,
                                               wait_time=2)
        param_put_guardphone_browser_slave1(browser_slave1_guardphone)

    # 初始化辅助压测的门禁设备
    device_info_access_control_slave2 = get_device_info_by_device_name('slave2_access_control')
    if device_info_access_control_slave2:
        device_config_access_control_slave2 = config_parse_device_config(
            device_info_access_control_slave2['config_module'])
        browser_access_control_slave2 = libbrowser(device_info_access_control_slave2,
                                                   device_config_access_control_slave2, wait_time=2)
        param_put_access_control_browser_slave2(browser_access_control_slave2)

    # 初始化SDMC
    device_config_common = config_parse_device_config('config_NORMAL')
    if device_config_common:
        sdmc_path = android_door_xml_data['exe_info'][0]['exe_path']  # [0]表示选择的设备在第一行，[1]表示选择的设备在第二行，以此类推
        sdmc = akwin(sdmc_path, device_config_common, 'uia')
        param_put_sdmc(sdmc)

    # 初始化SDMC ServerManage
    sdmc_server_manage_path = android_door_xml_data['exe_info'][0]['sdmc_server_manage_path']
    sdmc_server_manage = akwin(sdmc_server_manage_path, device_config_common, 'uia')
    param_put_sdmc_server_manage(sdmc_server_manage)

    # 初始化设备模拟器
    dev_emu_version_branch = param_get_version_branch_info()['DeviceEmulator_branch']
    model_name = param_get_model_name()
    master_device_ip = device_info_master['ip'].split('.')[3]
    emu_dir = os.path.join(root_path, 'tools', 'DeviceEmulator', dev_emu_version_branch,
                           'Emulator_Indoor_for_%s_%s' % (model_name, master_device_ip))
    emu_path = os.path.join(emu_dir, 'EmulatorBase.exe')
    indoor_emu_app = akwin(emu_path, device_config_common, 'uia')
    param_put_indoor_emulator(indoor_emu_app)

    # 初始化音频测具
    Ip_Measuring_tool_device_info = get_device_info_by_device_name('Ip_Measuring_tool')
    if 'audio_test_enable' in device_info_master:
        audio_test_enable = int(device_info_master['audio_test_enable'])
    else:
        audio_test_enable = 0
    if Ip_Measuring_tool_device_info and audio_test_enable == 1:
        dev_tester = akdevctrl_tester()
        r = dev_tester.creat(Ip_Measuring_tool_device_info['ip'], 90)
        if not r:
            aklog_printf("tester connect failed!")
        param_put_devctrl(dev_tester)


def test_main_android_indoor():
    # Android室内机
    config_module = param_get_config_module()
    ANDROIDINDOOR_excel_data = param_get_excel_data()

    # 初始化室内机主待测设备
    device_info_master = get_device_info_by_device_name('master_android_indoor')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    device_master_android_indoor = Android_Indoor(device_info_master, device_config_master)
    master_android_indoor = AndroidBase(device_master_android_indoor, wait_time=2)
    param_put_androidindoor_app_master(master_android_indoor)
    browser_master_android_indoor = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_androidindoor_browser_master(browser_master_android_indoor)

    # 初始化室内机辅助设备1
    device_info_slave1 = get_device_info_by_device_name('slave1_android_indoor')
    if device_info_slave1:
        device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
        device_slave1_android_indoor = Android_Indoor(device_info_slave1, device_config_slave1)
        slave1_android_indoor = AndroidBase(device_slave1_android_indoor, wait_time=2)
        param_put_androidindoor_app_slave1(slave1_android_indoor)
        browser_slave1_android_indoor = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
        param_put_androidindoor_browser_slave1(browser_slave1_android_indoor)

    # 初始化室内机辅助设备2
    device_info_slave2 = get_device_info_by_device_name('slave2_android_indoor')
    if device_info_slave2:
        device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
        device_slave2_android_indoor = Android_Indoor(device_info_slave2, device_config_slave2)
        slave2_android_indoor = AndroidBase(device_slave2_android_indoor, wait_time=2)
        param_put_androidindoor_app_slave2(slave2_android_indoor)
        browser_slave1_android_indoor = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
        param_put_androidindoor_browser_slave2(browser_slave1_android_indoor)

    # 初始化门口机网页
    device_info_slave3 = get_device_info_by_device_name('slave3_android_door')
    if device_info_slave3:
        device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
        browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
        param_put_door_browser_slave1(browser_slave3)
        device_slave3_android_door = Android_Door(device_info_slave3, device_config_slave3)
        slave3_android_door = AndroidBase(device_slave3_android_door, wait_time=2)
        param_put_androiddoor_app_slave1(slave3_android_door)

    # 初始化SmartPlus端
    device_info_smartplus = get_device_info_by_device_name('slave_smartplus')
    device_config_smartplus = config_parse_device_config('config_SMARTPLUS_NORMAL')
    device_smartplus = SmartPlus_Android(device_info_smartplus, device_config_smartplus)
    smartplus_app = AndroidBase(device_smartplus, wait_time=2)
    # smartplus_app.AppRun()
    param_put_smartplus_app_slave1(smartplus_app)

    # 初始化管理机辅助设备
    device_info_slave1_guardphone = get_device_info_by_device_name('slave_guard_phone')
    if device_info_slave1_guardphone:
        device_config_slave1_guardphone = config_parse_device_config(device_info_slave1_guardphone['config_module'])
        device_slave1_guardphone = Android_Guard_Phone(device_info_slave1_guardphone,
                                                       device_config_slave1_guardphone)
        app_slave1_guardphone = AndroidBase(device_slave1_guardphone, wait_time=2)
        param_put_guardphone_app_slave1(app_slave1_guardphone)
        browser_slave1_guardphone = libbrowser(device_info_slave1_guardphone, device_config_slave1_guardphone,
                                               wait_time=2)
        param_put_guardphone_browser_slave1(browser_slave1_guardphone)

    # 初始化辅助压测的门口机设备web端
    device_info_door_slave2 = get_device_info_by_device_name('slave2_linux_door')
    if device_info_door_slave2:
        device_config_door_slave2 = config_parse_device_config(device_info_door_slave2['config_module'])
        browser_door_slave2 = libbrowser(device_info_door_slave2, device_config_door_slave2, wait_time=2)
        param_put_door_browser_slave2(browser_door_slave2)

    # 初始化SDMC
    # exes = []
    device_config_common = config_parse_device_config('config_NORMAL')
    sdmc_path = ANDROIDINDOOR_excel_data['exe_info'][0]['exe_path']  # [0]表示选择的设备在第一行，[1]表示选择的设备在第二行，以此类推

    sdmc_master = akwin(sdmc_path, device_config_common, 'uia')
    param_put_sdmc(sdmc_master)

    # 初始化SDMC ServerManage
    sdmc_server_manage_path = ANDROIDINDOOR_excel_data['exe_info'][0]['sdmc_server_manage_path']
    sdmc_server_manage = akwin(sdmc_server_manage_path, device_config_common, 'uia')
    param_put_sdmc_server_manage(sdmc_server_manage)

    # 初始化设备模拟器
    dev_emu_version_branch = param_get_version_branch_info()['DeviceEmulator_branch']
    model_name = param_get_model_name()
    master_device_ip = device_info_master['ip'].split('.')[3]
    emu_dir = os.path.join(root_path, 'tools', 'DeviceEmulator', dev_emu_version_branch,
                           'Emulator_Door_for_%s_%s' % (model_name, master_device_ip))
    emu_path = os.path.join(emu_dir, 'EmulatorBase.exe')
    device_info_door_emulator = get_device_info_by_device_name('slave_door_emulator')
    if dev_emu_version_branch == 'V1_0':
        door_emu_app = akwin(emu_path, device_config_common, 'uia')
    elif dev_emu_version_branch == 'V2_0':
        door_emu_app = WindowBase(emu_path, device_info_door_emulator, device_config_common)
    else:
        aklog_printf('设备模拟器的分支版本错误，请检查version_branch.xml中DeviceEmulator_branch')
        door_emu_app = None
    param_put_door_emulator(door_emu_app)

    # 初始化SmartPlus模拟器
    device_config_smart_plus_emu = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
    device_info_smart_plus_emu = {'device_name': 'smart_plus_emu'}
    smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                          'AppEmulator.exe' % (root_path, param_get_cloud_version())
    smart_plus_emu = WindowBase(smart_plus_emu_path, device_info_smart_plus_emu, device_config_smart_plus_emu)
    param_put_smart_plus_emu_slave1(smart_plus_emu)

    # 初始化音频测具
    Ip_Measuring_tool_device_info = get_device_info_by_device_name('Ip_Measuring_tool')
    if 'audio_test_enable' in device_info_master:
        audio_test_enable = int(device_info_master['audio_test_enable'])
    else:
        audio_test_enable = 0
    if Ip_Measuring_tool_device_info and audio_test_enable == 1:
        dev_tester = akdevctrl_tester()
        r = dev_tester.creat(Ip_Measuring_tool_device_info['ip'], 90)
        if not r:
            aklog_printf("tester connect failed!")
        param_put_devctrl(dev_tester)

    # 初始化PCManager工具
    try:
        PCManager_path = ANDROIDINDOOR_excel_data['exe_info'][0]['PCManager_exe_path']
        PCManager_app = akwin(PCManager_path, device_config_common, 'uia')
        param_put_pcmanager(PCManager_app)
    except:
        aklog_warn('PC manager 工具路径未指定！！！')


def test_main_android_indoor_UI4_1():
    # Android室内机
    config_module = param_get_config_module()
    ANDROIDINDOOR_excel_data = param_get_excel_data()

    # 初始化室内机主待测设备
    device_info_master = get_device_info_by_device_name('master_android_indoor')
    if device_info_master:
        device_config_master = config_parse_device_config(config_module)
        param_put_device_config(device_config_master)
        master_android_indoor = AndroidBaseU2(device_info_master, device_config_master, wait_time=2)
        param_put_androidindoor_app_master(master_android_indoor)
        browser_master_android_indoor = libbrowser(device_info_master, device_config_master, wait_time=2)
        param_put_androidindoor_browser_master(browser_master_android_indoor)

    # 初始化室内机辅助设备1
    device_info_slave1 = get_device_info_by_device_name('slave1_android_indoor')
    if device_info_slave1:
        device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
        slave1_android_indoor = AndroidBaseU2(device_info_slave1, device_config_slave1, wait_time=2)
        param_put_androidindoor_app_slave1(slave1_android_indoor)
        browser_slave1_android_indoor = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
        param_put_androidindoor_browser_slave1(browser_slave1_android_indoor)

    # 初始化室内机辅助设备2
    device_info_slave2 = get_device_info_by_device_name('slave2_android_indoor')
    if device_info_slave2:
        device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
        slave2_android_indoor = AndroidBaseU2(device_info_slave2, device_config_slave2, wait_time=2)
        param_put_androidindoor_app_slave2(slave2_android_indoor)
        browser_slave2_android_indoor = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
        param_put_androidindoor_browser_slave2(browser_slave2_android_indoor)

    # 初始化门口机网页
    device_info_slave3 = get_device_info_by_device_name('slave3_android_door')
    if device_info_slave3:
        device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
        browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
        param_put_door_browser_slave1(browser_slave3)
        device_slave3_android_door = Android_Door(device_info_slave3, device_config_slave3)
        slave3_android_door = AndroidBase(device_slave3_android_door, wait_time=2)
        param_put_androiddoor_app_slave1(slave3_android_door)

    # 初始化管理机辅助设备
    device_info_slave1_guardphone = get_device_info_by_device_name('slave_guard_phone')
    if device_info_slave1_guardphone:
        device_config_slave1_guardphone = config_parse_device_config(device_info_slave1_guardphone['config_module'])
        device_slave1_guardphone = Android_Guard_Phone(device_info_slave1_guardphone,
                                                       device_config_slave1_guardphone)
        app_slave1_guardphone = AndroidBase(device_slave1_guardphone, wait_time=2)
        param_put_guardphone_app_slave1(app_slave1_guardphone)
        browser_slave1_guardphone = libbrowser(device_info_slave1_guardphone, device_config_slave1_guardphone,
                                               wait_time=2)
        param_put_guardphone_browser_slave1(browser_slave1_guardphone)

    device_info_door_slave2 = get_device_info_by_device_name('slave2_linux_door')
    if device_info_door_slave2:
        device_config_door_slave2 = config_parse_device_config(device_info_door_slave2['config_module'])
        browser_door_slave2 = libbrowser(device_info_door_slave2, device_config_door_slave2, wait_time=2)
        param_put_door_browser_slave2(browser_door_slave2)

    # 初始化SmartPlus模拟器
    device_config_smart_plus_emu = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
    device_info_smart_plus_emu = {'device_name': 'smart_plus_emu'}
    smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                          'AppEmulator.exe' % (root_path, param_get_cloud_version())
    smart_plus_emu = WindowBase(smart_plus_emu_path, device_info_smart_plus_emu, device_config_smart_plus_emu)
    param_put_smart_plus_emu_slave1(smart_plus_emu)

    # 初始化辅助压测的门口机设备web端
    # device_info_door_slave2 = get_device_info_by_device_name('slave2_linux_door')
    # device_config_door_slave2 = config_parse_device_config(device_info_door_slave2['config_module'])
    # browser_door_slave2 = libbrowser(device_info_door_slave2, device_config_door_slave2, wait_time=2)
    # param_put_door_browser_slave2(browser_door_slave2)

    # 初始化SDMC
    # exes = []
    device_config_common = config_parse_device_config('config_NORMAL')
    sdmc_path = ANDROIDINDOOR_excel_data['exe_info'][0]['exe_path']  # [0]表示选择的设备在第一行，[1]表示选择的设备在第二行，以此类推

    sdmc_master = akwin(sdmc_path, device_config_common, 'uia')
    param_put_sdmc(sdmc_master)

    # 初始化SDMC ServerManage
    sdmc_server_manage_path = ANDROIDINDOOR_excel_data['exe_info'][0]['sdmc_server_manage_path']
    sdmc_server_manage = akwin(sdmc_server_manage_path, device_config_common, 'uia')
    param_put_sdmc_server_manage(sdmc_server_manage)

    # 初始化设备模拟器
    dev_emu_version_branch = param_get_version_branch_info()['DeviceEmulator_branch']
    model_name = param_get_model_name()
    if device_info_master:
        master_device_ip = device_info_master['ip'].split('.')[3]
        emu_dir = os.path.join(root_path, 'tools', 'DeviceEmulator', dev_emu_version_branch,
                               'Emulator_Door_for_%s_%s' % (model_name, master_device_ip))
        emu_path = os.path.join(emu_dir, 'EmulatorBase.exe')
        device_info_door_emulator = get_device_info_by_device_name('slave_door_emulator')
        if dev_emu_version_branch == 'V1_0':
            door_emu_app = akwin(emu_path, device_config_common, 'uia')
        elif dev_emu_version_branch == 'V2_0':
            door_emu_app = WindowBase(emu_path, device_info_door_emulator, device_config_common)
        else:
            aklog_printf('设备模拟器的分支版本错误，请检查version_branch.xml中DeviceEmulator_branch')
            door_emu_app = None
        param_put_door_emulator(door_emu_app)

    # 初始化生产测试工具boot(引导界面)
    factory_tool_version_branch = param_get_version_branch_info()['FactoryTool_branch']
    factory_tool_path = os.path.join(root_path, 'tools', 'FactoryTool', factory_tool_version_branch, 'FactoryTool',
                                     'FactoryToolBoot.exe')
    device_config_factory_tool = config_parse_device_config('config_FACTORYTOOL_NORMAL')
    factory_tool_app = akwin(factory_tool_path, device_config_factory_tool, 'uia')
    param_put_factory_tool(factory_tool_app)


def test_main_android_indoor_UI4_0():
    if param_get_version_branch() in ['UI4_1', 'V10_0']:
        test_main_android_indoor_UI4_1()
        return
    # Android室内机
    config_module = param_get_config_module()
    ANDROIDINDOOR_excel_data = param_get_excel_data()

    # 初始化室内机主待测设备
    device_info_master = get_device_info_by_device_name('master_android_indoor')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    device_master_android_indoor = Android_Indoor_X933(device_info_master, device_config_master)
    master_android_indoor = AndroidBase(device_master_android_indoor, wait_time=2)
    param_put_androidindoor_app_master(master_android_indoor)
    browser_master_android_indoor = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_androidindoor_browser_master(browser_master_android_indoor)

    # 初始化室内机辅助设备1
    device_info_slave1 = get_device_info_by_device_name('slave1_android_indoor')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    device_slave1_android_indoor = Android_Indoor_X933(device_info_slave1, device_config_slave1)
    slave1_android_indoor = AndroidBase(device_slave1_android_indoor, wait_time=2)
    param_put_androidindoor_app_slave1(slave1_android_indoor)
    browser_slave1_android_indoor = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_androidindoor_browser_slave1(browser_slave1_android_indoor)

    # 初始化室内机辅助设备2
    device_info_slave2 = get_device_info_by_device_name('slave2_android_indoor')
    device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
    device_slave2_android_indoor = Android_Indoor_X933(device_info_slave2, device_config_slave2)
    slave2_android_indoor = AndroidBase(device_slave2_android_indoor, wait_time=2)
    param_put_androidindoor_app_slave2(slave2_android_indoor)
    browser_slave2_android_indoor = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
    param_put_androidindoor_browser_slave2(browser_slave2_android_indoor)

    # 初始化门口机网页
    device_info_slave3 = get_device_info_by_device_name('slave3_android_door')
    device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
    browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
    param_put_door_browser_slave1(browser_slave3)
    device_slave3_android_door = Android_Door(device_info_slave3, device_config_slave3)
    slave3_android_door = AndroidBase(device_slave3_android_door, wait_time=2)
    param_put_androiddoor_app_slave1(slave3_android_door)

    # 初始化管理机辅助设备
    device_info_slave1_guardphone = get_device_info_by_device_name('slave_guard_phone')
    device_config_slave1_guardphone = config_parse_device_config(device_info_slave1_guardphone['config_module'])
    device_slave1_guardphone = Android_Guard_Phone(device_info_slave1_guardphone,
                                                   device_config_slave1_guardphone)
    app_slave1_guardphone = AndroidBase(device_slave1_guardphone, wait_time=2)
    param_put_guardphone_app_slave1(app_slave1_guardphone)
    browser_slave1_guardphone = libbrowser(device_info_slave1_guardphone, device_config_slave1_guardphone,
                                           wait_time=2)
    param_put_guardphone_browser_slave1(browser_slave1_guardphone)

    # 初始化SmartPlus端
    device_info_smartplus = get_device_info_by_device_name('slave_smartplus')
    device_config_smartplus = config_parse_device_config('config_SMARTPLUS_NORMAL')
    device_smartplus = SmartPlus_Android(device_info_smartplus, device_config_smartplus)
    smartplus_app = AndroidBase(device_smartplus, wait_time=2)
    param_put_smartplus_app_slave1(smartplus_app)

    # 初始化SmartPlus模拟器
    device_config_smart_plus_emu = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
    device_info_smart_plus_emu = {'device_name': 'smart_plus_emu'}
    smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                          'AppEmulator.exe' % (root_path, param_get_cloud_version())
    smart_plus_emu = WindowBase(smart_plus_emu_path, device_info_smart_plus_emu, device_config_smart_plus_emu)
    param_put_smart_plus_emu_slave1(smart_plus_emu)

    # 初始化辅助压测的门口机设备web端
    device_info_door_slave2 = get_device_info_by_device_name('slave2_linux_door')
    if device_info_door_slave2:
        device_config_door_slave2 = config_parse_device_config(device_info_door_slave2['config_module'])
        browser_door_slave2 = libbrowser(device_info_door_slave2, device_config_door_slave2, wait_time=2)
        param_put_door_browser_slave2(browser_door_slave2)

    # 初始化SDMC
    # exes = []
    device_config_common = config_parse_device_config('config_NORMAL')
    sdmc_path = ANDROIDINDOOR_excel_data['exe_info'][0]['exe_path']  # [0]表示选择的设备在第一行，[1]表示选择的设备在第二行，以此类推

    sdmc_master = akwin(sdmc_path, device_config_common, 'uia')
    param_put_sdmc(sdmc_master)

    # 初始化SDMC ServerManage
    sdmc_server_manage_path = ANDROIDINDOOR_excel_data['exe_info'][0]['sdmc_server_manage_path']
    sdmc_server_manage = akwin(sdmc_server_manage_path, device_config_common, 'uia')
    param_put_sdmc_server_manage(sdmc_server_manage)

    # 初始化设备模拟器
    dev_emu_version_branch = param_get_version_branch_info()['DeviceEmulator_branch']
    model_name = param_get_model_name()
    master_device_ip = device_info_master['ip'].split('.')[3]
    emu_dir = os.path.join(root_path, 'tools', 'DeviceEmulator', dev_emu_version_branch,
                           'Emulator_Door_for_%s_%s' % (model_name, master_device_ip))
    emu_path = os.path.join(emu_dir, 'EmulatorBase.exe')
    device_info_door_emulator = get_device_info_by_device_name('slave_door_emulator')
    if dev_emu_version_branch == 'V1_0':
        door_emu_app = akwin(emu_path, device_config_common, 'uia')
    elif dev_emu_version_branch == 'V2_0':
        door_emu_app = WindowBase(emu_path, device_info_door_emulator, device_config_common)
    else:
        aklog_printf('设备模拟器的分支版本错误，请检查version_branch.xml中DeviceEmulator_branch')
        door_emu_app = None
    param_put_door_emulator(door_emu_app)

    # 初始化生产测试工具boot(引导界面)
    factory_tool_version_branch = param_get_version_branch_info()['FactoryTool_branch']
    factory_tool_path = os.path.join(root_path, 'tools', 'FactoryTool', factory_tool_version_branch, 'FactoryTool',
                                     'FactoryToolBoot.exe')
    device_config_factory_tool = config_parse_device_config('config_FACTORYTOOL_NORMAL')
    factory_tool_app = akwin(factory_tool_path, device_config_factory_tool, 'uia')
    param_put_factory_tool(factory_tool_app)


def test_main_android_indoor_x933_factory():
    # Android室内机
    config_module = param_get_config_module()
    ANDROIDINDOOR_excel_data = param_get_excel_data()

    # 初始化室内机主待测设备
    device_info_master = get_device_info_by_device_name('master_android_indoor')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    device_master_android_indoor = Android_Indoor_X933_Factory(device_info_master, device_config_master)
    master_android_indoor = AndroidBase(device_master_android_indoor, wait_time=2)
    # master_android_indoor.appium.StartAdbServer()
    # master_android_indoor.AppRun()
    param_put_androidindoor_app_master(master_android_indoor)

    browser_master_android_indoor = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_androidindoor_browser_master(browser_master_android_indoor)

    # 初始化室内机辅助设备1
    device_info_slave1 = get_device_info_by_device_name('slave1_android_indoor')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    device_slave1_android_indoor = Android_Indoor(device_info_slave1, device_config_slave1)
    slave1_android_indoor = AndroidBase(device_slave1_android_indoor, wait_time=2)
    # slave1_android_indoor.appium.StartAdbServer()
    # slave1_android_indoor.AppRun()
    param_put_androidindoor_app_slave1(slave1_android_indoor)

    browser_slave1_android_indoor = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_androidindoor_browser_slave1(browser_slave1_android_indoor)

    # 初始化室内机辅助设备2
    device_info_slave2 = get_device_info_by_device_name('slave2_android_indoor')
    device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
    device_slave2_android_indoor = Android_Indoor(device_info_slave2, device_config_slave2)
    slave2_android_indoor = AndroidBase(device_slave2_android_indoor, wait_time=2)
    # slave2_android_indoor.appium.StartAdbServer()
    # slave1_android_indoor.AppRun()
    param_put_androidindoor_app_slave2(slave2_android_indoor)

    browser_slave2 = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
    param_put_door_browser_slave2(browser_slave2)

    # 初始化门口机网页
    device_info_slave3 = get_device_info_by_device_name('slave3_android_door')
    device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
    browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
    param_put_door_browser_slave1(browser_slave3)
    device_slave3_android_door = Android_Door(device_info_slave3, device_config_slave3)
    slave3_android_door = AndroidBase(device_slave3_android_door, wait_time=2)
    param_put_androiddoor_app_slave1(slave3_android_door)

    # 初始化SmartPlus端
    device_info_smartplus = get_device_info_by_device_name('slave_smartplus')
    device_config_smartplus = config_parse_device_config('config_SMARTPLUS_NORMAL')
    device_smartplus = SmartPlus_Android(device_info_smartplus, device_config_smartplus)
    smartplus_app = AndroidBase(device_smartplus, wait_time=2)
    # smartplus_app.AppRun()
    param_put_smartplus_app_slave1(smartplus_app)

    # 初始化辅助压测的门口机设备web端
    # device_info_door_slave2 = get_device_info_by_device_name('slave2_linux_door')
    # device_config_door_slave2 = config_parse_device_config(device_info_door_slave2['config_module'])
    # browser_door_slave2 = libbrowser(device_info_door_slave2, device_config_door_slave2, wait_time=2)
    # param_put_door_browser_slave2(browser_door_slave2)

    # 初始化SDMC
    # exes = []
    device_config_common = config_parse_device_config('config_NORMAL')
    sdmc_path = ANDROIDINDOOR_excel_data['exe_info'][0]['exe_path']  # [0]表示选择的设备在第一行，[1]表示选择的设备在第二行，以此类推

    sdmc_master = akwin(sdmc_path, device_config_common, 'uia')
    param_put_sdmc(sdmc_master)

    # 初始化SDMC ServerManage
    sdmc_server_manage_path = ANDROIDINDOOR_excel_data['exe_info'][0]['sdmc_server_manage_path']
    sdmc_server_manage = akwin(sdmc_server_manage_path, device_config_common, 'uia')
    param_put_sdmc_server_manage(sdmc_server_manage)

    # 初始化设备模拟器
    dev_emu_version_branch = param_get_version_branch_info()['DeviceEmulator_branch']
    model_name = param_get_model_name()
    master_device_ip = device_info_master['ip'].split('.')[3]
    emu_dir = os.path.join(root_path, 'tools', 'DeviceEmulator', dev_emu_version_branch,
                           'Emulator_Door_for_%s_%s' % (model_name, master_device_ip))
    emu_path = os.path.join(emu_dir, 'EmulatorBase.exe')
    door_emu_app = akwin(emu_path, device_config_common, 'uia')
    param_put_door_emulator(door_emu_app)


def test_main_linux_indoor():
    config_module = param_get_config_module()
    LINUXINDOOR_excel_data = param_get_excel_data()

    # 初始化主设备
    device_info_master = get_device_info_by_device_name('master_linux_indoor')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_linuxindoor_browser_master(browser_master)

    # 初始化辅助室内机1
    device_info_slave1 = get_device_info_by_device_name('slave1_linux_indoor')
    if device_info_slave1:
        device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
        browser_slave1 = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
        param_put_linuxindoor_browser_slave1(browser_slave1)

    # 初始化辅助室内机2
    device_info_slave2 = get_device_info_by_device_name('slave2_linux_indoor')
    if device_info_slave2:
        device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
        browser_slave2 = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
        param_put_linuxindoor_browser_slave2(browser_slave2)

    # 初始化辅助室内机3
    # device_info_slave3 = get_device_info_by_device_name('slave3_linux_indoor')
    # device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
    # browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
    # param_put_linuxindoor_browser_slave3(browser_slave3)

    # 初始化辅助室内机4
    # device_info_slave4 = get_device_info_by_device_name('slave4_linux_indoor')
    # device_config_slave4 = config_parse_device_config(device_info_slave4['config_module'])
    # browser_slave4 = libbrowser(device_info_slave4, device_config_slave4, wait_time=2)
    # param_put_linuxindoor_browser_slave4(browser_slave4)

    # 初始化辅助室内机5
    # device_info_slave5 = get_device_info_by_device_name('slave5_linux_indoor')
    # device_config_slave5 = config_parse_device_config(device_info_slave5['config_module'])
    # browser_slave5 = libbrowser(device_info_slave5, device_config_slave5, wait_time=2)
    # param_put_linuxindoor_browser_slave5(browser_slave5)

    # 初始化辅助嵌入式门口机
    device_info_door_slave1 = get_device_info_by_device_name('slave_linux_door')
    if device_info_door_slave1:
        device_config_door_slave1 = config_parse_device_config(device_info_door_slave1['config_module'])
        browser_door_slave1 = libbrowser(device_info_door_slave1, device_config_door_slave1, wait_time=2)
        param_put_linuxdoor_browser_slave1(browser_door_slave1)

    # 初始化辅助安卓门口机网页
    device_info_slave_android_door = get_device_info_by_device_name('slave_android_door')
    if device_info_slave_android_door:
        device_config_slave_android_door = config_parse_device_config(device_info_slave_android_door['config_module'])
        browser_slave_android_door = libbrowser(device_info_slave_android_door, device_config_slave_android_door,
                                                wait_time=2)
        param_put_door_browser_slave1(browser_slave_android_door)
        device_slave_android_door = Android_Door(device_info_slave_android_door, device_config_slave_android_door)
        slave_android_door = AndroidBase(device_slave_android_door, wait_time=2)
        param_put_androiddoor_app_slave1(slave_android_door)

    # 初始化辅助SmartPlus
    device_info_smartplus = get_device_info_by_device_name('slave_smartplus')
    if device_info_smartplus:
        device_config_smartplus = config_parse_device_config(device_info_smartplus['config_module'])
        smartplus_app = AndroidBaseU2(device_info_smartplus, device_config_smartplus, wait_time=2)
        param_put_smartplus_app_slave1(smartplus_app)

    # 初始化SmartPlus模拟器
    device_config_smart_plus_emu = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
    device_info_smart_plus_emu = {'device_name': 'smart_plus_emu'}
    smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                          'AppEmulator.exe' % (root_path, param_get_cloud_version())
    smart_plus_emu = WindowBase(smart_plus_emu_path, device_info_smart_plus_emu, device_config_smart_plus_emu)
    param_put_smart_plus_emu_slave1(smart_plus_emu)

    # 初始化SDMC
    device_config_common = config_parse_device_config('config_NORMAL')
    sdmc_path = LINUXINDOOR_excel_data['exe_info'][0]['exe_path']  # [0]表示选择的设备在第一行，[1]表示选择的设备在第二行，以此类推
    sdmc = akwin(sdmc_path, device_config_common, 'uia')
    param_put_sdmc(sdmc)

    # 初始化测具
    dev_tester = akdevctrl_tester()
    device_ip_measuring_tool = get_device_info_by_device_name('Ip_Measuring_tool')
    if device_ip_measuring_tool:
        if dev_tester:
            r = dev_tester.creat(get_device_info_by_device_name('Ip_Measuring_tool')['ip'], 90)
        else:
            r = None
        if not r:
            aklog_printf("tester connect failed!")
        param_put_devctrl(dev_tester)
    # ret = dev_tester.set_stm32_mode(0)

    # 初始化SDMC ServerManage
    sdmc_server_manage_path = LINUXINDOOR_excel_data['exe_info'][0]['sdmc_server_manage_path']
    sdmc_server_manage = akwin(sdmc_server_manage_path, device_config_common, 'uia')
    param_put_sdmc_server_manage(sdmc_server_manage)

    # 初始化MACWRITE
    # device_config_macwrite = config_parse_device_config(config_module)
    macwrite_path = device_config_common.get_macwirte_path()
    macwrite = akwin(macwrite_path, device_config_common, 'uia')
    param_put_macwrite(macwrite)

    # 初始化MACCHECK
    # device_config_maccheck = config_parse_device_config(config_module)
    maccheck_path = device_config_common.get_maccheck_path()
    maccheck = akwin(maccheck_path, device_config_common, 'uia')
    param_put_maccheck(maccheck)

    # 初始化设备模拟器
    dev_emu_version_branch = param_get_version_branch_info()['DeviceEmulator_branch']
    model_name = param_get_model_name()
    master_device_ip = device_info_master['ip'].split('.')[3]
    emu_dir = os.path.join(root_path, 'tools', 'DeviceEmulator', dev_emu_version_branch,
                           'Emulator_Door_for_%s_%s' % (model_name, master_device_ip))
    emu_path = os.path.join(emu_dir, 'EmulatorBase.exe')
    door_emu_app = akwin(emu_path, device_config_common, 'uia')
    param_put_door_emulator(door_emu_app)


def test_main_linux_ipphone():
    config_module = param_get_config_module()

    # 获取设备信息
    device_info_master = get_device_info_by_device_name('master_linux_ipphone')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_ipphone_browser_master(browser_master)

    device_info_slave1 = get_device_info_by_device_name('slave1_linux_indoor')
    if device_info_slave1:
        device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
        browser_slave1 = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
        param_put_linuxindoor_browser_slave1(browser_slave1)

    device_info_slave2 = get_device_info_by_device_name('slave2_linux_ipphone')
    if device_info_slave2:
        device_config_slave2 = config_parse_device_config(config_module)
        browser_slave2 = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
        param_put_ipphone_browser_slave2(browser_slave2)

    device_info_slave3 = get_device_info_by_device_name('slave1_linux_door')
    if device_info_slave3:
        device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
        browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
        param_put_linuxdoor_browser_slave1(browser_slave3)


def test_main_smartplus():
    # parse_config_module_smartplus()
    config_module = param_get_config_module()

    # # 输入测试设备或browser的数量
    # test_apps_counts = 2

    # if test_apps_counts >= 1:
    device_info_master = get_device_info_by_device_name('master_smartplus')
    device_config_master = config_parse_device_config(config_module)
    device_master = SmartPlus_Android(device_info_master, device_config_master)
    app_master = AndroidBase(device_master, wait_time=2)
    # app_master.AppRun()
    param_put_smartplus_app_master(app_master)
    param_put_device_config(device_config_master)

    # if test_apps_counts >= 2:
    device_info_slave1 = get_device_info_by_device_name('slave1_smartplus')
    device_config_slave1 = config_parse_device_config(config_module)
    device_slave1 = SmartPlus_Android(device_info_slave1, device_config_slave1)
    app_slave1 = AndroidBase(device_slave1, wait_time=2)
    # app_slave1.AppRun()
    param_put_smartplus_app_slave1(app_slave1)

    # 初始化室内机
    slave1_device_info = get_device_info_by_device_name('slave1_android_indoor')
    slave1_device_config = config_parse_device_config(slave1_device_info['config_module'])
    device_slave1_android_indoor = Android_Indoor(slave1_device_info, slave1_device_config)
    slave1_android_indoor = AndroidBase(device_slave1_android_indoor, wait_time=2)
    param_put_androidindoor_app_slave1(slave1_android_indoor)
    browser_slave1 = libbrowser(slave1_device_info, slave1_device_config, wait_time=2)
    param_put_androidindoor_browser_slave1(browser_slave1)

    # 初始化门口机
    slave2_device_info = get_device_info_by_device_name('slave2_android_door')
    slave2_device_config = config_parse_device_config(slave2_device_info['config_module'])
    browser_slave2 = libbrowser(slave2_device_info, slave2_device_config, wait_time=2)
    param_put_door_browser_slave2(browser_slave2)


def test_main_guard_phone():
    """GuardPhone"""
    config_module = param_get_config_module()

    # 初始化视频话机
    device_info_master = get_device_info_by_device_name('master_guard_phone')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    device_master = Android_Guard_Phone(device_info_master, device_config_master)
    app_master = AndroidBase(device_master, wait_time=2)
    param_put_guardphone_app_master(app_master)
    browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_guardphone_browser_master(browser_master)

    # 初始化视频话机辅助设备1
    device_info_slave1 = get_device_info_by_device_name('slave1_guard_phone')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    device_slave1 = Android_Guard_Phone(device_info_slave1, device_config_slave1)
    app_slave1 = AndroidBase(device_slave1, wait_time=2)
    param_put_guardphone_app_slave1(app_slave1)
    browser_slave1 = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_guardphone_browser_slave1(browser_slave1)

    # 初始化视频话机辅助设备2
    device_info_slave2 = get_device_info_by_device_name('slave2_guard_phone')
    device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
    device_slave2 = Android_Guard_Phone(device_info_slave2, device_config_slave2)
    app_slave2 = AndroidBase(device_slave2, wait_time=2)
    param_put_guardphone_app_slave2(app_slave2)
    browser_slave2 = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
    param_put_guardphone_browser_slave2(browser_slave2)

    # 初始化室内机辅助设备
    device_info_slave1_android_indoor = get_device_info_by_device_name('slave1_android_indoor')
    device_config_slave1_android_indoor = config_parse_device_config(device_info_slave1_android_indoor['config_module'])
    device_slave1_android_indoor = Android_Indoor(device_info_slave1_android_indoor,
                                                  device_config_slave1_android_indoor)
    slave1_android_indoor = AndroidBase(device_slave1_android_indoor, wait_time=2)
    param_put_androidindoor_app_slave1(slave1_android_indoor)

    browser_slave1_android_indoor = libbrowser(device_info_slave1_android_indoor, device_config_slave1_android_indoor,
                                               wait_time=2)
    param_put_androidindoor_browser_slave1(browser_slave1_android_indoor)

    # 初始化安卓门口机辅助设备
    device_info_slave1_android_door = get_device_info_by_device_name('slave1_android_door')
    device_config_slave1_android_door = config_parse_device_config(device_info_slave1_android_door['config_module'])
    device_slave1_android_door = Android_Door(device_info_slave1_android_door, device_config_slave1_android_door)
    slave1_android_door = AndroidBase(device_slave1_android_door, wait_time=2)
    param_put_androiddoor_app_slave1(slave1_android_door)

    browser_slave1_android_door = libbrowser(device_info_slave1_android_door, device_config_slave1_android_door,
                                             wait_time=2)
    param_put_door_browser_slave1(browser_slave1_android_door)

    # 初始化SmartPlus端
    device_info_smartplus = get_device_info_by_device_name('slave1_app_smartplus')
    device_config_smartplus = config_parse_device_config('config_SMARTPLUS_NORMAL')
    device_smartplus = SmartPlus_Android(device_info_smartplus, device_config_smartplus)
    smartplus_app = AndroidBase(device_smartplus, wait_time=2)
    param_put_smartplus_app_slave1(smartplus_app)

    # 初始化SmartPlus模拟器
    device_config_smart_plus_emu = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
    device_info_smart_plus_emu = {'device_name': 'smart_plus_emu'}
    smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                          'AppEmulator.exe' % (root_path, param_get_cloud_version())
    smart_plus_emu = WindowBase(smart_plus_emu_path, device_info_smart_plus_emu, device_config_smart_plus_emu)
    param_put_smart_plus_emu_slave1(smart_plus_emu)

    # 初始化音频测具
    Ip_Measuring_tool_device_info = get_device_info_by_device_name('Ip_Measuring_tool')
    if 'audio_test_enable' in device_info_master:
        audio_test_enable = int(device_info_master['audio_test_enable'])
    else:
        audio_test_enable = 0
    if Ip_Measuring_tool_device_info and audio_test_enable == 1:
        dev_tester = akdevctrl_tester()
        r = dev_tester.creat(Ip_Measuring_tool_device_info['ip'], 90)
        if not r:
            aklog_printf("tester connect failed!")
        param_put_devctrl(dev_tester)


def test_main_video_phone_normal():
    """安卓视频话机普通版本"""
    config_module = param_get_config_module()

    # 初始化视频话机
    device_info_master = get_device_info_by_device_name('master_video_phone')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    device_master = Android_R49_Phone(device_info_master, device_config_master)
    app_master = AndroidBase(device_master, wait_time=2)
    # app_master.appium.StartAdbServer()
    # app_master.AppRun()
    param_put_videophone_app_master(app_master)
    browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_videophone_browser_master(browser_master)

    # 初始化视频话机辅助设备1
    device_info_slave1_video_phone = get_device_info_by_device_name('slave1_video_phone')
    device_config_slave1_video_phone = config_parse_device_config(device_info_slave1_video_phone['config_module'])
    device_slave1_video_phone = Android_R48_Phone(device_info_slave1_video_phone,
                                                  device_config_slave1_video_phone)
    app_slave1_video_phone = AndroidBase(device_slave1_video_phone, wait_time=2)
    param_put_videophone_app_slave1(app_slave1_video_phone)
    browser_slave1_video_phone = libbrowser(device_info_slave1_video_phone, device_config_slave1_video_phone,
                                            wait_time=2)
    param_put_videophone_browser_slave1(browser_slave1_video_phone)

    # 初始化视频话机辅助设备1
    device_info_slave2_video_phone = get_device_info_by_device_name('slave2_video_phone')
    device_config_slave2_video_phone = config_parse_device_config(device_info_slave2_video_phone['config_module'])
    device_slave2_video_phone = Android_R48_Phone(device_info_slave2_video_phone,
                                                  device_config_slave2_video_phone)
    app_slave2_video_phone = AndroidBase(device_slave2_video_phone, wait_time=2)
    param_put_videophone_app_slave2(app_slave2_video_phone)
    browser_slave2_video_phone = libbrowser(device_info_slave2_video_phone, device_config_slave2_video_phone,
                                            wait_time=2)
    param_put_videophone_browser_slave2(browser_slave2_video_phone)

    # 初始化室内机辅助设备
    device_info_slave1_android_indoor = get_device_info_by_device_name('slave1_android_indoor')
    device_config_slave1_android_indoor = config_parse_device_config(device_info_slave1_android_indoor['config_module'])
    device_slave1_android_indoor = Android_Indoor(device_info_slave1_android_indoor,
                                                  device_config_slave1_android_indoor)
    slave1_android_indoor = AndroidBase(device_slave1_android_indoor, wait_time=2)
    param_put_androidindoor_app_slave1(slave1_android_indoor)

    browser_slave1_android_indoor = libbrowser(device_info_slave1_android_indoor, device_config_slave1_android_indoor,
                                               wait_time=2)
    param_put_androidindoor_browser_slave1(browser_slave1_android_indoor)

    # 初始化安卓门口机辅助设备
    device_info_slave1_android_door = get_device_info_by_device_name('slave1_android_door')
    device_config_slave1_android_door = config_parse_device_config(device_info_slave1_android_door['config_module'])
    device_slave1_android_door = Android_Door(device_info_slave1_android_door, device_config_slave1_android_door)
    slave1_android_door = AndroidBase(device_slave1_android_door, wait_time=2)
    param_put_androiddoor_app_slave1(slave1_android_door)

    browser_slave1_android_door = libbrowser(device_info_slave1_android_door, device_config_slave1_android_door,
                                             wait_time=2)
    param_put_door_browser_slave1(browser_slave1_android_door)

    # 初始化SmartPlus端
    device_info_smartplus = get_device_info_by_device_name('slave1_app_smartplus')
    device_config_smartplus = config_parse_device_config('config_SMARTPLUS_NORMAL')
    device_smartplus = SmartPlus_Android(device_info_smartplus, device_config_smartplus)
    smartplus_app = AndroidBase(device_smartplus, wait_time=2)
    param_put_smartplus_app_slave1(smartplus_app)

    # 初始化音频测具
    Ip_Measuring_tool_device_info = get_device_info_by_device_name('Ip_Measuring_tool')
    if 'audio_test_enable' in device_info_master:
        audio_test_enable = int(device_info_master['audio_test_enable'])
    else:
        audio_test_enable = 0
    if Ip_Measuring_tool_device_info and audio_test_enable == 1:
        dev_tester = akdevctrl_tester()
        r = dev_tester.creat(Ip_Measuring_tool_device_info['ip'], 90)
        if not r:
            aklog_printf("tester connect failed!")
        param_put_devctrl(dev_tester)


def test_main_access_control():
    config_module = param_get_config_module()
    access_control_xml_data = param_get_excel_data()

    # 初始化主设备web端
    device_info_master = get_device_info_by_device_name('master_access_control')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_access_control_browser_master(browser_master)

    # 初始化辅助门禁设备
    device_info_slave1_access_control = get_device_info_by_device_name('slave1_access_control')
    device_config_slave1_access_control = config_parse_device_config(config_module)
    param_put_device_config(device_config_slave1_access_control)
    browser_slave1_access_control = libbrowser(device_info_slave1_access_control,
                                               device_config_slave1_access_control, wait_time=2)
    param_put_access_control_browser_slave1(browser_slave1_access_control)

    # 初始化嵌入式室内机辅助设备web端
    device_info_slave1 = get_device_info_by_device_name('slave1_linux_indoor')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    browser_slave1 = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_linuxindoor_browser_slave1(browser_slave1)

    # 初始化辅助压测的门禁设备
    device_info_access_control_slave2 = get_device_info_by_device_name('slave2_access_control')
    device_config_access_control_slave2 = config_parse_device_config(device_info_access_control_slave2['config_module'])
    browser_access_control_slave2 = libbrowser(device_info_access_control_slave2, device_config_access_control_slave2,
                                               wait_time=2)
    param_put_access_control_browser_slave2(browser_access_control_slave2)

    # # 初始化管理机辅助设备
    # device_info_slave1_guardphone = get_device_info_by_device_name('slave_management')
    # device_config_slave1_guardphone = config_parse_device_config(device_info_slave1_guardphone['config_module'])
    # device_slave1_guardphone = Android_Guard_Phone(device_info_slave1_guardphone,
    #                                                device_config_slave1_guardphone)
    # app_slave1_guardphone = AndroidBase(device_slave1_guardphone, wait_time=2)
    # param_put_guardphone_app_slave1(app_slave1_guardphone)
    # browser_slave1_guardphone = libbrowser(device_info_slave1_guardphone, device_config_slave1_guardphone,
    #                                        wait_time=2)
    # param_put_guardphone_browser_slave1(browser_slave1_guardphone)

    # 初始化安卓门口机辅助设备网页
    device_info_slave3 = get_device_info_by_device_name('slave3_android_door')
    device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
    browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
    param_put_door_browser_slave1(browser_slave3)
    device_slave3_android_door = Android_Door(device_info_slave3, device_config_slave3)
    slave3_android_door = AndroidBase(device_slave3_android_door, wait_time=2)
    param_put_androiddoor_app_slave1(slave3_android_door)

    # 初始化嵌入式门口机辅助设备网页
    device_info_linuxdoor_slave1 = get_device_info_by_device_name('slave1_linux_door')
    device_config_door_slave1 = config_parse_device_config(device_info_linuxdoor_slave1['config_module'])
    browser_door_slave1 = libbrowser(device_info_linuxdoor_slave1, device_config_door_slave1, wait_time=2)
    param_put_linuxdoor_browser_slave1(browser_door_slave1)

    # 初始化ACMS
    # device_config_acms = config_parse_device_config('config_ACMS_NORMAL')
    # acms_path = access_control_xml_data['acms_exe_info'][0]['acms_exe_path']
    # acms_app = akwin(acms_path, device_config_acms, 'uia')
    # param_put_acms(acms_app)

    # 初始化ACMS ServerManage
    # acms_server_manage_path = access_control_xml_data['acms_exe_info'][0]['acms_server_manage_path']
    # acms_server_manage = akwin(acms_server_manage_path, device_config_acms, 'uia')
    # param_put_acms_server_manage(acms_server_manage)

    # 初始化UpgradeTool
    # upgrade_tool_path = device_config_common.get_upgrade_tool_path()
    # upgrade_tool = akwin(upgrade_tool_path, device_config_common, 'uia')
    # param_put_upgrade_tool(upgrade_tool)

    # 初始化自检工具
    access_control_factory_tool_path = device_config_master.get_accesscontrolfactorytool_path()
    access_control_factory_tool = akwin(access_control_factory_tool_path, device_config_master, 'uia')
    param_put_access_control_factory_tool(access_control_factory_tool)

    # 初始化SmartPlus模拟器
    device_config_smart_plus_emu = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
    device_info_smart_plus_emu = {'device_name': 'smart_plus_emu'}
    smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                          'AppEmulator.exe' % (root_path, param_get_cloud_version())
    smart_plus_emu = WindowBase(smart_plus_emu_path, device_info_smart_plus_emu, device_config_smart_plus_emu)
    param_put_smart_plus_emu_slave1(smart_plus_emu)

    # 初始化音频测具
    Ip_Measuring_tool_device_info = get_device_info_by_device_name('Ip_Measuring_tool')
    if 'audio_test_enable' in device_info_master:
        audio_test_enable = int(device_info_master['audio_test_enable'])
    else:
        audio_test_enable = 0
    if Ip_Measuring_tool_device_info and audio_test_enable == 1:
        dev_tester = akdevctrl_tester()
        r = dev_tester.creat(Ip_Measuring_tool_device_info['ip'], 90)
        if not r:
            aklog_printf("tester connect failed!")
        param_put_devctrl(dev_tester)


def test_main_access_door():
    config_module = param_get_config_module()
    access_control_xml_data = param_get_excel_data()

    # 初始化主设备web端
    device_info_master = get_device_info_by_device_name('master_access_door')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_access_door_browser_master(browser_master)

    # 初始化辅助门禁设备
    device_info_slave1_access_door = get_device_info_by_device_name('slave1_access_door')
    device_config_slave1_access_door = config_parse_device_config(config_module)
    param_put_device_config(device_config_slave1_access_door)
    browser_slave1_access_door = libbrowser(device_info_slave1_access_door,
                                            device_config_slave1_access_door, wait_time=2)
    param_put_access_door_browser_slave1(browser_slave1_access_door)

    # 初始化嵌入式室内机辅助设备web端
    device_info_slave1 = get_device_info_by_device_name('slave1_linux_indoor')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    browser_slave1 = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_linuxindoor_browser_slave1(browser_slave1)

    # 初始化辅助压测的门禁设备
    device_info_access_control_slave2 = get_device_info_by_device_name('slave2_access_control')
    device_config_access_control_slave2 = config_parse_device_config(
        device_info_access_control_slave2['config_module'])
    browser_access_control_slave2 = libbrowser(device_info_access_control_slave2,
                                               device_config_access_control_slave2, wait_time=2)
    param_put_access_control_browser_slave2(browser_access_control_slave2)

    # 初始化管理机辅助设备
    device_info_slave1_guardphone = get_device_info_by_device_name('slave_management')
    device_config_slave1_guardphone = config_parse_device_config(device_info_slave1_guardphone['config_module'])
    device_slave1_guardphone = Android_Guard_Phone(device_info_slave1_guardphone,
                                                   device_config_slave1_guardphone)
    app_slave1_guardphone = AndroidBase(device_slave1_guardphone, wait_time=2)
    param_put_guardphone_app_slave1(app_slave1_guardphone)
    browser_slave1_guardphone = libbrowser(device_info_slave1_guardphone, device_config_slave1_guardphone,
                                           wait_time=2)
    param_put_guardphone_browser_slave1(browser_slave1_guardphone)

    # 初始化门口机网页
    device_info_slave3 = get_device_info_by_device_name('slave3_android_door')
    device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
    browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
    param_put_door_browser_slave1(browser_slave3)
    device_slave3_android_door = Android_Door(device_info_slave3, device_config_slave3)
    slave3_android_door = AndroidBase(device_slave3_android_door, wait_time=2)
    param_put_androiddoor_app_slave1(slave3_android_door)

    # 初始化ACMS
    device_config_acms = config_parse_device_config('config_ACMS_NORMAL')
    acms_path = access_control_xml_data['acms_exe_info'][0]['acms_exe_path']
    acms_app = akwin(acms_path, device_config_acms, 'uia')
    param_put_acms(acms_app)

    # 初始化ACMS ServerManage
    acms_server_manage_path = access_control_xml_data['acms_exe_info'][0]['acms_server_manage_path']
    acms_server_manage = akwin(acms_server_manage_path, device_config_acms, 'uia')
    param_put_acms_server_manage(acms_server_manage)

    # 初始化SmartPlus模拟器
    device_config_smart_plus_emu = config_parse_device_config('config_SMARTPLUSEMULATOR_NORMAL')
    device_info_smart_plus_emu = {'device_name': 'smart_plus_emu'}
    smart_plus_emu_path = '%s\\testcase\\module\\cloud\\%s\\cloud_emulator\\App_emulator\\AppEmulator\\' \
                          'AppEmulator.exe' % (root_path, param_get_cloud_version())
    smart_plus_emu = WindowBase(smart_plus_emu_path, device_info_smart_plus_emu, device_config_smart_plus_emu)
    param_put_smart_plus_emu_slave1(smart_plus_emu)

    # 初始化UpgradeTool
    # upgrade_tool_path = device_config_common.get_upgrade_tool_path()
    # upgrade_tool = akwin(upgrade_tool_path, device_config_common, 'uia')
    # param_put_upgrade_tool(upgrade_tool)

    # 初始化自检工具
    # selftestdassistant_path = device_config_master.get_selftestdassistant_path()
    # selftestdassistant = akwin(selftestdassistant_path, device_config_master, 'uia')
    # param_put_selftestdassistant(selftestdassistant)

    # 初始化音频测具
    Ip_Measuring_tool_device_info = get_device_info_by_device_name('Ip_Measuring_tool')
    if 'audio_test_enable' in device_info_master:
        audio_test_enable = int(device_info_master['audio_test_enable'])
    else:
        audio_test_enable = 0
    if Ip_Measuring_tool_device_info and audio_test_enable == 1:
        dev_tester = akdevctrl_tester()
        r = dev_tester.creat(Ip_Measuring_tool_device_info['ip'], 90)
        if not r:
            aklog_printf("tester connect failed!")
        param_put_devctrl(dev_tester)


def test_main_ACMS():
    aklog_printf('test_main_ACMS')
    config_module = param_get_config_module()
    ACMS_excel_data = param_get_excel_data()

    # 初始化ACMS
    device_config_ACMS = config_parse_device_config(config_module)
    param_put_device_config(device_config_ACMS)
    acms_path = ACMS_excel_data['exe_info'][0]['acms_exe_path']
    acms_app = akwin(acms_path, device_config_ACMS, 'uia')
    param_put_acms(acms_app)

    # 初始化ACMS ServerManage
    acms_server_manage_path = ACMS_excel_data['exe_info'][0]['acms_server_manage_path']
    acms_server_manage = akwin(acms_server_manage_path, device_config_ACMS, 'uia')
    param_put_acms_server_manage(acms_server_manage)

    # # 初始化辅助设备和web
    # device_info_master = SDMC_excel_data['device_info'][0]
    # device_config_master = config_parse_device_config(config_module)
    #
    # device_master = Android_Indoor(device_info_master, device_config_master)
    # app_master = AndroidBase(device_master, wait_time=2)
    # param_put_androidindoor_app_master(app_master)
    #
    # browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
    # param_put_androidindoor_browser_master(browser_master)


def test_main_sdmc():
    # parse_config_module_sdmc()
    config_module = param_get_config_module()

    # 从Excel表格中获取数据，会一次性把excel表格全部获取
    SDMC_excel_data = param_get_excel_data()
    # param_put_excel_data(SDMC_excel_data)

    # 初始化SDMC
    device_config_sdmc = config_parse_device_config(config_module)
    param_put_device_config(device_config_sdmc)

    sdmc_path = SDMC_excel_data['exe_info'][0]['exe_path']  # [0]表示选择的设备在第一行，[1]表示选择的设备在第二行，以此类推
    sdmc_master = akwin(sdmc_path, device_config_sdmc, 'uia')
    param_put_sdmc(sdmc_master)

    # 初始化SDMC ServerManage
    sdmc_server_manage_path = SDMC_excel_data['exe_info'][0]['sdmc_server_manage_path']
    sdmc_server_manage = akwin(sdmc_server_manage_path, device_config_sdmc, 'uia')
    param_put_sdmc_server_manage(sdmc_server_manage)

    # 初始化Android室内机辅助设备和web
    device_info_master = SDMC_excel_data['device_info'][0]
    device_config_master = config_parse_device_config(device_info_master['config_module'])

    device_master = Android_Indoor(device_info_master, device_config_master)
    app_master = AndroidBase(device_master, wait_time=2)
    param_put_androidindoor_app_master(app_master)
    # app_master.device_info['ip'] = '192.168.88.10'
    # app_master.device_info['deviceid'] = '192.168.88.10:5654'
    # print(SDMC_excel_data['device_info'][0]['ip'])
    # print(device_master.GetDeviceAddr())

    browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_androidindoor_browser_master(browser_master)

    # 初始化嵌入式室内机辅助设备web端
    device_info_slave1 = get_device_info_by_device_name('slave1_linux_indoor')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    browser_slave1 = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_linuxindoor_browser_slave1(browser_slave1)

    # 初始化嵌入式门口机辅助设备web端
    device_info_slave2 = get_device_info_by_device_name('slave2_linux_door')
    device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
    browser_slave2 = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
    param_put_door_browser_slave2(browser_slave2)

    # 初始化Android门口机辅助设备和web端
    device_info_slave3 = get_device_info_by_device_name('slave3_android_door')
    device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
    param_put_device_config(device_config_slave3)

    device_slave3 = Android_Door(device_info_slave3, device_config_slave3)
    androiddoor_app_slave3 = AndroidBase(device_slave3, wait_time=2)
    # androiddoor_app_master.appium.StartAdbServer()
    # androiddoor_app_master.appium.connect_adb_by_usb()
    # androiddoor_app_master.AppRun()
    param_put_androiddoor_app_master(androiddoor_app_slave3)

    browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
    param_put_door_browser_master(browser_slave3)


def test_main_linux_hyperpanel():
    """嵌入式HyperPanel Lite系列机型设备实例化"""
    version_branch_int = int(re.sub(r'\D', '', param_get_version_branch()))
    if version_branch_int >= 23:
        aklog_warn('当前分支 %s 不再使用test_main' % param_get_version_branch())
        return

    config_module = param_get_config_module()

    # 初始化主设备
    device_info_master = get_device_info_by_device_name('master_linux_hyperpanel')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    browser_master = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_linuxhyperpanel_browser_master(browser_master)

    # 实例化辅助家庭中心(Android SmartPanel，X933H，当HyperPanel作为子网关时，需要有家庭中心)
    device_info_slave1_android_smartpanel = get_device_info_by_device_name('slave1_android_smartpanel')
    device_config_slave1_android_smartpanel = config_parse_device_config(
        device_info_slave1_android_smartpanel['config_module'])
    slave1_android_smartpanel_app = AndroidBaseU2(device_info_slave1_android_smartpanel,
                                                  device_config_slave1_android_smartpanel, wait_time=2)
    param_put_androidsmartpanel_app_slave1(slave1_android_smartpanel_app)

    browser_slave1_android_smartpanel = libbrowser(device_info_slave1_android_smartpanel,
                                                   device_config_slave1_android_smartpanel)
    param_put_androidsmartpanel_browser_slave1(browser_slave1_android_smartpanel)

    browser_slave1_android_smartpanel_user_web = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_androidsmartpanel_user_web_slave1(browser_slave1_android_smartpanel_user_web)

    # 初始化辅助嵌入式门口机
    device_info_door_slave1 = get_device_info_by_device_name('slave_linux_door')
    device_config_door_slave1 = config_parse_device_config(device_info_door_slave1['config_module'])
    browser_door_slave1 = libbrowser(device_info_door_slave1, device_config_door_slave1, wait_time=2)
    param_put_linuxdoor_browser_slave1(browser_door_slave1)

    # 实例化BelaHome
    device_info_belahome = get_device_info_by_device_name('slave_belahome')
    device_config_belahome = config_parse_device_config(device_info_belahome['config_module'])
    belahome_app = AndroidBaseU2(device_info_belahome, device_config_belahome, wait_time=2)
    param_put_belahome_app_slave1(belahome_app)


def test_main_android_hyperpanel():
    # V3_0之后的分支，不再使用test_main
    version_branch_int = int(re.sub(r'\D', '', param_get_version_branch()))
    if version_branch_int >= 23:
        aklog_warn('当前分支 %s 不再使用test_main' % param_get_version_branch())
        return
    # Android室内机
    config_module = param_get_config_module()

    # 实例化AndroidHyperPanel主设备（可以作为家庭中心）
    device_info_master = get_device_info_by_device_name('master_android_hyperpanel')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    master_android_hyperpanel = AndroidBaseU2(device_info_master, device_config_master, wait_time=2)
    param_put_androidhyperpanel_app_master(master_android_hyperpanel)

    browser_master_android_hyperpanel = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_androidhyperpanel_browser_master(browser_master_android_hyperpanel)

    browser_master_android_hyperpanel_user_web = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_androidhyperpanel_userweb_master(browser_master_android_hyperpanel_user_web)

    # 实例化AndroidHyperPanel辅助设备1
    device_info_slave1 = get_device_info_by_device_name('slave1_android_hyperpanel')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    slave1_android_hyperpanel = AndroidBaseU2(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_androidhyperpanel_app_slave1(slave1_android_hyperpanel)

    browser_slave1_android_hyperpanel = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_androidhyperpanel_browser_slave1(browser_slave1_android_hyperpanel)

    # 实例化AndroidHyperPanel辅助设备2
    device_info_slave2 = get_device_info_by_device_name('slave2_android_hyperpanel')
    device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
    slave2_android_hyperpanel = AndroidBaseU2(device_info_slave2, device_config_slave2, wait_time=2)
    param_put_androidhyperpanel_app_slave2(slave2_android_hyperpanel)

    browser_slave2 = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
    param_put_androidhyperpanel_browser_slave2(browser_slave2)

    # 实例化辅助家庭中心(Android SmartPanel，X933H，当HyperPanel作为子网关时，需要有家庭中心)
    device_info_slave1_android_smartpanel = get_device_info_by_device_name('slave1_android_smartpanel')
    device_config_slave1_android_smartpanel = config_parse_device_config(
        device_info_slave1_android_smartpanel['config_module'])
    slave1_android_smartpanel_app = AndroidBaseU2(device_info_slave1_android_smartpanel,
                                                  device_config_slave1_android_smartpanel, wait_time=2)
    param_put_androidsmartpanel_app_slave1(slave1_android_smartpanel_app)

    browser_slave1_android_smartpanel = libbrowser(device_info_slave1_android_smartpanel,
                                                   device_config_slave1_android_smartpanel)
    param_put_androidsmartpanel_browser_slave1(browser_slave1_android_smartpanel)

    browser_slave1_android_smartpanel_user_web = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_androidsmartpanel_user_web_slave1(browser_slave1_android_smartpanel_user_web)

    # 初始化安卓门口机
    device_info_slave3 = get_device_info_by_device_name('slave3_android_door')
    device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
    browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
    param_put_door_browser_slave1(browser_slave3)
    device_slave3_android_door = Android_Door(device_info_slave3, device_config_slave3)
    slave3_android_door = AndroidBase(device_slave3_android_door, wait_time=2)
    param_put_androiddoor_app_slave1(slave3_android_door)

    # 实例化子网关(Linux HyperPanel，KS41)
    device_info_slave1_linux_hyperpanel = get_device_info_by_device_name('slave1_linux_hyperpanel')
    device_config_slave1_linux_hyperpanel = config_parse_device_config(
        device_info_slave1_linux_hyperpanel['config_module'])
    browser_slave1_linux_hyperpanel = libbrowser(device_info_slave1_linux_hyperpanel,
                                                 device_config_slave1_linux_hyperpanel)
    param_put_linuxhyperpanel_browser_slave1(browser_slave1_linux_hyperpanel)

    # 实例化BelaHome
    device_info_belahome = get_device_info_by_device_name('slave_belahome')
    device_config_belahome = config_parse_device_config(device_info_belahome['config_module'])
    belahome_app = AndroidBaseU2(device_info_belahome, device_config_belahome, wait_time=2)
    param_put_belahome_app_slave1(belahome_app)

    # 实例化ZigBee测具
    device_info_zigbee_tool = get_device_info_by_device_name('zigbee_tool')
    device_config_zigbee_tool = config_parse_device_config(device_info_zigbee_tool['config_module'])
    browser_zigbee_tool = libbrowser(device_info_zigbee_tool, device_config_zigbee_tool, wait_time=2)
    param_put_access_control_browser_slave1(browser_zigbee_tool)


def test_main_android_smartpanel():
    """家庭中心安卓设备"""
    version_branch_int = int(re.sub(r'\D', '', param_get_version_branch()))
    if version_branch_int >= 23:
        aklog_warn('当前分支 %s 不再使用test_main' % param_get_version_branch())
        return

    config_module = param_get_config_module()

    # 实例化家庭中心主设备
    device_info_master = get_device_info_by_device_name('master_android_smartpanel')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    master_android_smartpanel = AndroidBaseU2(device_info_master, device_config_master, wait_time=2)
    param_put_androidsmartpanel_app_master(master_android_smartpanel)

    browser_master_android_smartpanel = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_androidsmartpanel_browser_master(browser_master_android_smartpanel)

    browser_master_akubela_user_web = libbrowser(device_info_master, device_config_master, wait_time=2)
    param_put_androidsmartpanel_user_web_master(browser_master_akubela_user_web)

    # 实例化子网关(Android SmartPanel，X933H)
    device_info_slave1_android_smartpanel = get_device_info_by_device_name('slave1_android_smartpanel')
    device_config_slave1_android_smartpanel = config_parse_device_config(
        device_info_slave1_android_smartpanel['config_module'])
    slave1_android_smartpanel_app = AndroidBaseU2(device_info_slave1_android_smartpanel,
                                                  device_config_slave1_android_smartpanel, wait_time=2)
    param_put_androidsmartpanel_app_slave1(slave1_android_smartpanel_app)

    browser_slave1_android_smartpanel = libbrowser(device_info_slave1_android_smartpanel,
                                                   device_config_slave1_android_smartpanel)
    param_put_androidsmartpanel_browser_slave1(browser_slave1_android_smartpanel)

    # 实例化子网关(Linux HyperPanel，KS41)
    device_info_slave1_linux_hyperpanel = get_device_info_by_device_name('slave1_linux_hyperpanel')
    device_config_slave1_linux_hyperpanel = config_parse_device_config(
        device_info_slave1_linux_hyperpanel['config_module'])
    browser_slave1_linux_hyperpanel = libbrowser(device_info_slave1_linux_hyperpanel,
                                                 device_config_slave1_linux_hyperpanel)
    param_put_linuxhyperpanel_browser_slave1(browser_slave1_linux_hyperpanel)

    # 实例化子网关2(Linux HyperPanel，KS41)
    device_info_slave2_linux_hyperpanel = get_device_info_by_device_name('slave2_linux_hyperpanel')
    device_config_slave2_linux_hyperpanel = config_parse_device_config(
        device_info_slave2_linux_hyperpanel['config_module'])
    browser_slave2_linux_hyperpanel = libbrowser(device_info_slave2_linux_hyperpanel,
                                                 device_config_slave2_linux_hyperpanel)
    param_put_linuxhyperpanel_browser_slave2(browser_slave2_linux_hyperpanel)

    # 实例化BelaHome
    device_info_belahome = get_device_info_by_device_name('slave_belahome')
    device_config_belahome = config_parse_device_config(device_info_belahome['config_module'])
    belahome_app = AndroidBaseU2(device_info_belahome, device_config_belahome, wait_time=2)
    param_put_belahome_app_slave1(belahome_app)

    # 实例化BelaHome1
    device_info_belahome1 = get_device_info_by_device_name('slave1_belahome')
    device_config_belahome1 = config_parse_device_config(device_info_belahome['config_module'])
    belahome_app = AndroidBaseU2(device_info_belahome1, device_config_belahome1, wait_time=2)
    param_put_belahome_app_slave2(belahome_app)

    # 实例化BelaHome
    device_info_belahome2 = get_device_info_by_device_name('slave2_belahome')
    device_config_belahome2 = config_parse_device_config(device_info_belahome['config_module'])
    belahome_app = AndroidBaseU2(device_info_belahome2, device_config_belahome2, wait_time=2)
    param_put_belahome_app_slave3(belahome_app)

    # 实例化AndroidHyperPanel辅助设备1
    device_info_slave1 = get_device_info_by_device_name('slave1_android_hyperpanel')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    slave1_android_hyperpanel = AndroidBaseU2(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_androidhyperpanel_app_slave1(slave1_android_hyperpanel)

    browser_slave1_android_hyperpanel = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_androidhyperpanel_browser_slave1(browser_slave1_android_hyperpanel)

    # 初始化安卓门口机
    device_info_slave3 = get_device_info_by_device_name('slave_android_door')
    device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
    browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
    param_put_door_browser_slave1(browser_slave3)
    device_slave3_android_door = Android_Door(device_info_slave3, device_config_slave3)
    slave3_android_door = AndroidBase(device_slave3_android_door, wait_time=2)
    param_put_androiddoor_app_slave1(slave3_android_door)


def test_main_android_belahome():
    """BelaHome用户APP"""
    version_branch_int = int(re.sub(r'\D', '', param_get_version_branch()))
    if version_branch_int >= 23:
        aklog_warn('当前分支 %s 不再使用test_main' % param_get_version_branch())
        return

    config_module = param_get_config_module()

    # 初始化BelaHome
    device_info_master = get_device_info_by_device_name('belahome_admin')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    app_master_belahome = AndroidBaseU2(device_info_master, device_config_master, wait_time=2)
    param_put_belahome_app_master(app_master_belahome)

    # 初始化家庭中心设备
    device_info_slave_smartpanel = get_device_info_by_device_name('hc_android_smartpanel')
    device_config_slave_smartpanel = config_parse_device_config(device_info_slave_smartpanel['config_module'])
    slave_smartpanel_app = AndroidBaseU2(device_info_slave_smartpanel, device_config_slave_smartpanel, wait_time=2)
    param_put_androidsmartpanel_app_slave1(slave_smartpanel_app)

    browser_slave_smartpanel = libbrowser(device_info_slave_smartpanel, device_config_slave_smartpanel)
    param_put_androidsmartpanel_browser_slave1(browser_slave_smartpanel)

    slave_akubela_user_web = libbrowser(device_info_slave_smartpanel, device_config_slave_smartpanel)
    param_put_androidsmartpanel_user_web_slave1(slave_akubela_user_web)

    # 实例化家庭中心HyPanel设备
    device_info_slave1 = get_device_info_by_device_name('hc_android_hypanel')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    slave1_android_hyperpanel = AndroidBaseU2(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_androidhyperpanel_app_slave1(slave1_android_hyperpanel)

    browser_slave1_android_hyperpanel = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_androidhyperpanel_browser_slave1(browser_slave1_android_hyperpanel)

    # 实例化网关HyPanel设备
    device_info_slave2 = get_device_info_by_device_name('gw1_android_hypanel')
    device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
    slave2_android_hyperpanel = AndroidBaseU2(device_info_slave2, device_config_slave2, wait_time=2)
    param_put_androidhyperpanel_app_slave2(slave2_android_hyperpanel)

    browser_slave2 = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
    param_put_androidhyperpanel_browser_slave2(browser_slave2)

    # 实例化安卓门口机
    device_info_slave3 = get_device_info_by_device_name('slave_android_door')
    device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
    browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
    param_put_door_browser_slave1(browser_slave3)
    device_slave3_android_door = Android_Door(device_info_slave3, device_config_slave3)
    slave3_android_door = AndroidBase(device_slave3_android_door, wait_time=2)
    param_put_androiddoor_app_slave1(slave3_android_door)


def test_main_iOS_belahome():
    """BelaHome iOS用户APP"""
    version_branch_int = int(re.sub(r'\D', '', param_get_version_branch()))
    if version_branch_int >= 23:
        aklog_warn('当前分支 %s 不再使用test_main' % param_get_version_branch())
        return

    config_module = param_get_config_module()

    # 初始化BelaHome
    device_info_master = get_device_info_by_device_name('belahome_admin')
    device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)
    app_master_belahome = IOSBaseU2(device_info_master, device_config_master, wait_time=2)
    param_put_belahome_app_master(app_master_belahome)


def test_main_akubela_cloud():
    """家居云辅助设备实例化"""
    version_branch_int = int(re.sub(r'\D', '', param_get_version_branch()))
    if version_branch_int >= 23:
        aklog_warn('当前分支 %s 不再使用test_main' % param_get_version_branch())
        return
    # 实例化AndroidHyperPanel辅助设备1，家庭中心
    device_info_slave1 = get_device_info_by_device_name('hc_android_hypanel')
    device_config_slave1 = config_parse_device_config(device_info_slave1['config_module'])
    slave1_android_hyperpanel = AndroidBaseU2(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_androidhyperpanel_app_slave1(slave1_android_hyperpanel)

    browser_slave1_android_hyperpanel = libbrowser(device_info_slave1, device_config_slave1, wait_time=2)
    param_put_androidhyperpanel_browser_slave1(browser_slave1_android_hyperpanel)

    # 实例化AndroidHyperPanel辅助设备2，子网关
    device_info_slave2 = get_device_info_by_device_name('gw1_android_hypanel')
    device_config_slave2 = config_parse_device_config(device_info_slave2['config_module'])
    slave2_android_hyperpanel = AndroidBaseU2(device_info_slave2, device_config_slave2, wait_time=2)
    param_put_androidhyperpanel_app_slave2(slave2_android_hyperpanel)

    browser_slave2 = libbrowser(device_info_slave2, device_config_slave2, wait_time=2)
    param_put_androidhyperpanel_browser_slave2(browser_slave2)

    # 实例化安卓门口机
    device_info_slave3 = get_device_info_by_device_name('slave3_android_door')
    device_config_slave3 = config_parse_device_config(device_info_slave3['config_module'])
    browser_slave3 = libbrowser(device_info_slave3, device_config_slave3, wait_time=2)
    param_put_door_browser_slave1(browser_slave3)
    device_slave3_android_door = Android_Door(device_info_slave3, device_config_slave3)
    slave3_android_door = AndroidBase(device_slave3_android_door, wait_time=2)
    param_put_androiddoor_app_slave1(slave3_android_door)

    # 实例化BelaHome
    device_info_belahome = get_device_info_by_device_name('belahome_admin')
    device_config_belahome = config_parse_device_config(device_info_belahome['config_module'])
    belahome_app = AndroidBaseU2(device_info_belahome, device_config_belahome, wait_time=2)
    param_put_belahome_app_slave1(belahome_app)

    # 实例化BelaHome，从帐号
    device_info_belahome_fm1 = get_device_info_by_device_name('belahome_fm1')
    if device_info_belahome_fm1:
        device_config_belahome_fm1 = config_parse_device_config(device_info_belahome_fm1['config_module'])
        belahome_app_fm1 = AndroidBaseU2(device_info_belahome_fm1, device_config_belahome_fm1, wait_time=2)
        param_put_belahome_app_slave2(belahome_app_fm1)

    # 实例化ZigBee测具
    device_info_zigbee_tool = get_device_info_by_device_name('zigbee_tool')
    device_config_zigbee_tool = config_parse_device_config(device_info_zigbee_tool['config_module'])
    browser_zigbee_tool = libbrowser(device_info_zigbee_tool, device_config_zigbee_tool, wait_time=2)
    param_put_access_control_browser_slave1(browser_zigbee_tool)


def test_main_smart_home():
    """家居产品不再使用test_main"""
    pass


def parse_test_main():
    test_main = {
        'LINUXDOOR': test_main_linux_door,
        'R27': test_main_linux_door,
        'R27_V2': test_main_linux_door,
        'R20': test_main_linux_door,
        'R20_V2': test_main_linux_door,
        'R20K': test_main_linux_door,
        'R20K_V2': test_main_linux_door,
        'R20B_2': test_main_linux_door,
        'R26': test_main_linux_door,
        'R26_V2': test_main_linux_door,
        'R26B_V2': test_main_linux_door,
        'R28': test_main_linux_door,
        'E21_V2': test_main_linux_door,
        'E11': test_main_linux_door,
        'ANDROIDDOOR': test_main_android_door,
        'R29': test_main_android_door,
        'X916': test_main_android_door,
        'ANDROIDINDOOR': test_main_android_indoor,
        'C315': test_main_android_indoor,
        'C317': test_main_android_indoor,
        'IT82': test_main_android_indoor,
        'IT83': test_main_android_indoor,
        'IT88': test_main_android_indoor_UI4_1,
        'C319': test_main_android_indoor_UI4_1,
        'X933': test_main_android_indoor_UI4_1,
        'S567': test_main_android_indoor_UI4_1,
        'S563': test_main_android_indoor_UI4_1,
        'C316': test_main_android_indoor_UI4_1,
        'LINUXINDOOR': test_main_linux_indoor,
        'C313': test_main_linux_indoor,
        'C313_V2': test_main_linux_indoor,
        'C313_2_V2': test_main_linux_indoor,
        'S562': test_main_linux_indoor,
        'S560': test_main_linux_indoor,
        'IPPHONE': test_main_linux_ipphone,
        'AUSTCO': test_main_linux_ipphone,
        'R15': test_main_linux_ipphone,
        'R50': test_main_linux_ipphone,
        'R50V3': test_main_linux_ipphone,
        'R52': test_main_linux_ipphone,
        'R53': test_main_linux_ipphone,
        'R55': test_main_linux_ipphone,
        'R59': test_main_linux_ipphone,
        'R63': test_main_linux_ipphone,
        'R65': test_main_linux_ipphone,
        'R67': test_main_linux_ipphone,
        'SMARTPLUS': test_main_smartplus,
        'GUARDPHONE': test_main_guard_phone,
        'R48GP': test_main_guard_phone,
        'R49GP': test_main_guard_phone,
        'VIDEOPHONE': test_main_video_phone_normal,
        'R48': test_main_video_phone_normal,
        'R49': test_main_video_phone_normal,
        'ACCESSCONTROL': test_main_access_control,
        'A01': test_main_access_control,
        'A05': test_main_access_control,
        'A06': test_main_access_control,
        'A094': test_main_access_control,
        'ACCESSDOOR': test_main_access_door,
        'E16': test_main_access_door,
        'E18': test_main_access_door,
        'A02': test_main_access_control,
        'A03': test_main_access_control,
        'SMARTPANEL': test_main_android_smartpanel,
        'X933H': test_main_android_smartpanel,
        'HYPANELANDROID': test_main_android_hyperpanel,
        'PS51': test_main_android_hyperpanel,
        'HYPANELLINUX': test_main_linux_hyperpanel,
        'KS41': test_main_linux_hyperpanel,
        'BELAHOME': test_main_android_belahome,
        'AKUBELACLOUD': test_main_akubela_cloud,
        'SMARTHOME': test_main_smart_home
    }
    param_put_test_main(test_main)
