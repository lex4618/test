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
from typing import Optional

g_test_results = []


def param_put_test_main(test_main):
    g_params_test_main['test_main'] = test_main


def param_get_test_main():
    if 'test_main' in g_params_test_main:
        return g_params_test_main['test_main']
    else:
        return 'unknown'


def param_reset_g_params():
    g_params.clear()


def param_get_support_flag(flag):
    """
    主测机型支持的功能标志字典. 默认为True, 避免一些使用上出错的时候跳过了部分用例执行.
    """
    if 'support_flag' not in g_params:
        return True
    if flag not in g_params['support_flag']:
        return True
    return g_params['support_flag'].get(flag)


def param_put_support_flag(flag, value):
    """
    主测机型支持的功能标志字典.
    """
    if 'support_flag' not in g_params:
        g_params['support_flag'] = {}
    g_params['support_flag'][flag] = value


def param_put_thread_stop_flag(thread_stop_flag):
    g_params['thread_stop_flag'] = thread_stop_flag


def param_put_old_process_dict(pdict):
    g_params['old_process_dict'] = pdict


def param_get_old_process_dict():
    return g_params.get('old_process_dict', {})


def param_put_reboot_process_flag(flag=True):
    # 写入False: 未重启, 检查进程完整性和pid
    # 写入True: 有主动重启, 只检查进程完整性.
    # 恢复是自动恢复的, 故手动调用的只有 param_put_reboot_process_flag(True)
    if flag:
        aklog_info('设置重启标志位: True')
    else:
        aklog_info('设置重启标志位: False')
    g_params['reboot_process_flag'] = flag


def param_get_reboot_process_flag():
    return g_params.get('reboot_process_flag', False)


def param_get_thread_stop_flag():
    if 'thread_stop_flag' in g_params:
        return g_params['thread_stop_flag']
    else:
        return 10


def param_put_config_ini_file(config_ini_file):
    g_params['config_ini_file'] = config_ini_file


def param_get_config_ini_file():
    if 'config_ini_file' in g_params:
        return g_params['config_ini_file']
    else:
        return ''


def param_put_config_ini_data(config_ini_data):
    g_params['config_ini_data'] = config_ini_data


def param_get_config_ini_data():
    if 'config_ini_data' in g_params:
        return g_params['config_ini_data']
    else:
        return 'unknown'


def param_put_temp_ini_file(temp_ini_file):
    g_params['temp_ini_file'] = temp_ini_file


def param_get_temp_ini_file():
    if 'temp_ini_file' in g_params:
        return g_params['temp_ini_file']
    else:
        return ''


def param_put_stop_process_event(stop_process_event):
    g_params['stop_process_event'] = stop_process_event


def param_get_stop_process_event():
    if 'stop_process_event' in g_params:
        return g_params['stop_process_event']
    else:
        return None


def param_put_time_zone_data(time_zone_data):
    g_params['time_zone_data'] = time_zone_data


def param_get_time_zone_data():
    if 'time_zone_data' in g_params:
        return g_params['time_zone_data']
    else:
        return 'unknown'


def param_put_model_name_config_data(model_name_config_data):
    g_params['model_name_config_data'] = model_name_config_data


def param_get_model_name_config_data():
    if 'model_name_config_data' in g_params:
        return g_params['model_name_config_data']
    else:
        return 'unknown'


def param_put_oem_name_config_data(oem_name_config_data):
    g_params['oem_name_config_data'] = oem_name_config_data


def param_get_oem_name_config_data():
    if 'oem_name_config_data' in g_params:
        return g_params['oem_name_config_data']
    else:
        return 'unknown'


def param_put_product_line_config_data(product_line_config_data):
    g_params['product_line_config_data'] = product_line_config_data


def param_get_product_line_config_data():
    if 'product_line_config_data' in g_params:
        return g_params['product_line_config_data']
    else:
        return 'unknown'


def param_put_series_products_config_data(series_products_config_data):
    g_params['series_products_config_data'] = series_products_config_data


def param_get_series_products_config_data():
    if 'series_products_config_data' in g_params:
        return g_params['series_products_config_data']
    else:
        return 'unknown'


def param_put_series_module_name_info(series_module_name_info):
    g_params['series_module_name_info'] = series_module_name_info


def param_get_series_module_name_info():
    if 'series_module_name_info' in g_params:
        return g_params['series_module_name_info']
    else:
        return 'unknown'


def param_put_cloud_upgrade_model_config_data(cloud_upgrade_model_config_data):
    g_params['cloud_upgrade_model_config_data'] = cloud_upgrade_model_config_data


def param_get_cloud_upgrade_model_config_data():
    if 'cloud_upgrade_model_config_data' in g_params:
        return g_params['cloud_upgrade_model_config_data']
    else:
        return 'unknown'


def param_put_oem_not_upgrade_config_data(oem_not_upgrade_config_data):
    g_params['oem_not_upgrade_config_data'] = oem_not_upgrade_config_data


def param_get_oem_not_upgrade_config_data():
    if 'oem_not_upgrade_config_data' in g_params:
        return g_params['oem_not_upgrade_config_data']
    else:
        return 'unknown'


def param_put_cloud_info(cloud_info):
    g_params['cloud_info'] = cloud_info


def param_get_cloud_info():
    if 'cloud_info' in g_params:
        return g_params['cloud_info']
    else:
        return 'unknown'


def param_put_akubela_cloud_info(akubela_cloud_info):
    g_params['akubela_cloud_info'] = akubela_cloud_info


def param_get_akubela_cloud_info():
    if 'akubela_cloud_info' in g_params:
        return g_params['akubela_cloud_info']
    else:
        return None


def param_put_start_time(start_time):
    g_params['start_time'] = start_time


def param_get_start_time():
    if 'start_time' in g_params:
        return g_params['start_time']
    else:
        return 'unknown'


def param_put_test_total_time(test_total_time):
    g_params['test_total_time'] = test_total_time


def param_get_test_total_time():
    if 'test_total_time' in g_params:
        return g_params['test_total_time']
    else:
        return 'unknown'


def param_put_modules(modules):
    g_params['modules'] = modules


def param_get_modules():
    if 'modules' in g_params:
        return g_params['modules']
    else:
        return {}


def param_put_modules_dict(modules_dict):
    g_params['modules_dict'] = modules_dict


def param_get_modules_dict():
    if 'modules_dict' in g_params:
        return g_params['modules_dict']
    else:
        return 'unknown'


def param_put_module_list(module_list):
    g_params['module_list'] = module_list


def param_get_module_list():
    if 'module_list' in g_params:
        return g_params['module_list']
    else:
        return ''


def param_put_suite_list(suite_list):
    g_params['suite_list'] = suite_list


def param_get_suite_list():
    if 'suite_list' in g_params:
        return g_params['suite_list']
    else:
        return 'unknown'


def param_put_exclude_case_list(exclude_case_list):
    g_params['exclude_case_list'] = exclude_case_list


def param_get_exclude_case_list():
    if 'exclude_case_list' in g_params:
        return g_params['exclude_case_list']
    else:
        return 'unknown'


def param_put_config_module(config_module):
    g_params['config_module'] = config_module


def param_get_config_module():
    if 'config_module' in g_params:
        return g_params['config_module']
    else:
        return 'unknown'


def param_put_check_device_count_enable(check_device_count_enable):
    g_params['check_device_count_enable'] = check_device_count_enable


def param_get_check_device_count_enable():
    if 'check_device_count_enable' in g_params:
        return g_params['check_device_count_enable']
    else:
        return False


def param_put_device_count_info(device_count_info):
    g_params['device_count_info'] = device_count_info


def param_get_device_count_info():
    if 'device_count_info' in g_params:
        return g_params['device_count_info']
    else:
        return {}


def param_put_upgrade_cover_counts(upgrade_cover_counts):
    g_params['upgrade_cover_counts'] = upgrade_cover_counts


def param_get_upgrade_cover_counts():
    if 'upgrade_cover_counts' in g_params:
        return g_params['upgrade_cover_counts']
    else:
        return None


# 主测试设备的分支版本
def param_put_version_branch(version_branch):
    g_params['version_branch'] = version_branch


def param_get_version_branch():
    if 'version_branch' in g_params:
        return g_params['version_branch']
    else:
        return ''


def param_put_model_version_info(model_version_info):
    g_params['model_version_info'] = model_version_info


def param_get_model_version_info():
    if 'model_version_info' in g_params:
        return g_params['model_version_info']
    else:
        return None


# 所有使用的主设备和辅助设备的分支版本
def param_put_version_branch_info(version_branch_info):
    g_params['version_branch_info'] = version_branch_info


def param_get_version_branch_info():
    if 'version_branch_info' in g_params:
        return g_params['version_branch_info']
    else:
        return None


def param_put_cloud_upgrade_model(cloud_upgrade_model):
    g_params['cloud_upgrade_model'] = cloud_upgrade_model


def param_get_cloud_upgrade_model():
    if 'cloud_upgrade_model' in g_params:
        return g_params['cloud_upgrade_model']
    else:
        return 'unknown'


def param_put_master_model(master_model):
    g_params['master_model'] = master_model


def param_get_master_model():
    if 'master_model' in g_params:
        return g_params['master_model']
    else:
        return None


def param_put_master_device_info(master_device_info):
    g_params['master_device_info'] = master_device_info


def param_get_master_device_info():
    if 'master_device_info' in g_params:
        return g_params['master_device_info']
    else:
        return None


def param_put_master_oem(master_oem):
    g_params['master_oem'] = master_oem


def param_get_master_oem():
    if 'master_oem' in g_params:
        return g_params['master_oem']
    else:
        return None


def param_put_model_name(model_name):
    g_params['model_name'] = model_name


def param_get_model_name():
    if 'model_name' in g_params:
        return g_params['model_name']
    else:
        return 'unknown'


def param_put_model_id(model_id):
    g_params['model_id'] = model_id


def param_get_model_id():
    if 'model_id' in g_params:
        return g_params['model_id']
    else:
        return 'unknown'


def param_put_oem_name(oem_name):
    g_params['oem_name'] = oem_name


def param_get_oem_name():
    if 'oem_name' in g_params:
        return g_params['oem_name']
    else:
        return 'unknown'


def param_put_rom_version(rom_version):
    g_params['rom_version'] = rom_version


def param_get_rom_version():
    if 'rom_version' in g_params:
        return g_params['rom_version']
    else:
        return 'unknown'


def param_put_seriesproduct_name(seriesproduct_name):
    g_params['seriesproduct_name'] = seriesproduct_name


def param_get_seriesproduct_name() -> str:
    if 'seriesproduct_name' in g_params:
        return g_params['seriesproduct_name']
    else:
        return 'unknown'


def param_put_series_name_info(model_name, series_name):
    if 'series_name_info' not in g_params:
        g_params['series_name_info'] = {}
    g_params['series_name_info'][model_name] = series_name


def param_get_series_name_info(model_name):
    series_name_info = g_params.get('series_name_info')
    if series_name_info:
        return series_name_info.get(model_name)
    else:
        return None


def param_put_product_line_name(product_line_name):
    g_params['product_line_name'] = product_line_name


def param_get_product_line_name() -> Optional[str]:
    if 'product_line_name' in g_params:
        return g_params['product_line_name']
    else:
        return None


def param_put_jenkins_report_url(jenkins_report_url):
    g_params['jenkins_report_url'] = jenkins_report_url


def param_get_jenkins_report_url():
    if 'jenkins_report_url' in g_params:
        return g_params['jenkins_report_url']
    else:
        return ''


def param_put_jenkins_ws_report_root_url(jenkins_ws_report_root_url):
    g_params['jenkins_ws_report_root_url'] = jenkins_ws_report_root_url


def param_get_jenkins_ws_report_root_url():
    if 'jenkins_ws_report_root_url' in g_params:
        return g_params['jenkins_ws_report_root_url']
    else:
        return ''


def param_put_jenkins_report_dir(jenkins_report_dir):
    g_params['jenkins_report_dir'] = jenkins_report_dir


def param_get_jenkins_report_dir():
    if 'jenkins_report_dir' in g_params:
        return g_params['jenkins_report_dir']
    else:
        return ''


def param_put_jenkins_job_name(jenkins_job_name):
    g_params['jenkins_job_name'] = jenkins_job_name


def param_get_jenkins_job_name():
    if 'jenkins_job_name' in g_params:
        return g_params['jenkins_job_name']
    else:
        return ''


def param_put_jenkins_distribute_enable(jenkins_distribute_enable):
    g_params['jenkins_distribute_enable'] = jenkins_distribute_enable


def param_get_jenkins_distribute_enable():
    if 'jenkins_distribute_enable' in g_params:
        return g_params['jenkins_distribute_enable']
    else:
        return False


def param_put_start_by_upstream_project_enable(start_by_upstream_project_enable):
    g_params['start_by_upstream_project_enable'] = start_by_upstream_project_enable


def param_get_start_by_upstream_project_enable():
    if 'start_by_upstream_project_enable' in g_params:
        return g_params['start_by_upstream_project_enable']
    else:
        return False


def param_put_test_type(test_type):
    g_params['test_type'] = test_type


def param_get_test_type():
    if 'test_type' in g_params:
        return g_params['test_type']
    else:
        return 'function-test'


def param_put_test_suite_case_list(test_suite_case_list):
    g_params['test_suite_case_list'] = test_suite_case_list


def param_get_test_suite_case_list() -> list:
    if 'test_suite_case_list' in g_params:
        return g_params['test_suite_case_list']
    else:
        return []


def param_put_firmware_info(firmware_info):
    g_params['firmware_info'] = firmware_info


def param_get_firmware_info():
    if 'firmware_info' in g_params:
        return g_params['firmware_info']
    else:
        return {}


def param_put_firmware_info_path(firmware_info_path):
    g_params['firmware_info_path'] = firmware_info_path


def param_get_firmware_info_path():
    if 'firmware_info_path' in g_params:
        return g_params['firmware_info_path']
    else:
        return 'unknown'


def param_put_firmware_info_data(firmware_info_data):
    g_params['firmware_info_data'] = firmware_info_data


def param_get_firmware_info_data():
    if 'firmware_info_data' in g_params:
        return g_params['firmware_info_data']
    else:
        return 'unknown'


def param_put_cloud_version(cloud_version):
    g_params['cloud_version'] = cloud_version


def param_get_cloud_version():
    if 'cloud_version' in g_params:
        return g_params['cloud_version']
    else:
        return 'unknown'


def param_put_control_base(control_base):
    g_params['control_base'] = control_base


def param_get_control_base():
    if 'control_base' in g_params:
        return g_params['control_base']
    else:
        return None


def param_put_base_module(base_module):
    g_params['base_module'] = base_module


def param_get_base_module():
    if 'base_module' in g_params:
        return g_params['base_module']
    else:
        return None


def param_put_device_module_root_path(device_module_root_path):
    g_params['device_module_root_path'] = device_module_root_path


def param_get_device_module_root_path():
    if 'device_module_root_path' in g_params:
        return g_params['device_module_root_path']
    else:
        return 'unknown'


def param_put_firmware_path(firmware_path):
    g_params['firmware_path'] = firmware_path


def param_get_firmware_path():
    if 'firmware_path' in g_params:
        return g_params['firmware_path']
    else:
        return 'unknown'


def param_put_device_config(device_config):  # 传类的实例
    g_params['device_config'] = device_config


def param_get_device_config():
    if 'device_config' in g_params:
        return g_params['device_config']
    else:
        return 'unknown'


def param_put_excel_data(excel_data):
    g_params['excel_data'] = excel_data


def param_get_excel_data():
    if 'excel_data' in g_params:
        return g_params['excel_data']
    else:
        return 'unknown'


def param_put_all_config_device_info(all_config_device_info):
    g_params['all_config_device_info'] = all_config_device_info


def param_get_all_config_device_info():
    if 'all_config_device_info' in g_params:
        return g_params['all_config_device_info']
    else:
        return None


def param_put_devctrl(devctrl):
    g_params['devctrl'] = devctrl


def param_get_devctrl():
    if 'devctrl' in g_params:
        return g_params['devctrl']
    else:
        return None


def param_put_sdmc(sdmc):
    g_params['sdmc'] = sdmc


def param_get_sdmc():
    if 'sdmc' in g_params:
        return g_params['sdmc']
    else:
        return 'unknown'


def param_put_sdmc_server_manage(sdmc_server_manage):
    g_params['sdmc_server_manage'] = sdmc_server_manage


def param_get_sdmc_server_manage():
    if 'sdmc_server_manage' in g_params:
        return g_params['sdmc_server_manage']
    else:
        return 'unknown'


def param_put_pcmanager(pcmanager):
    g_params['pcmanager'] = pcmanager


def param_get_pcmanager():
    if 'pcmanager' in g_params:
        return g_params['pcmanager']
    else:
        return 'unknown'


def param_put_acms(acms):
    g_params['acms'] = acms


def param_get_acms():
    if 'acms' in g_params:
        return g_params['acms']
    else:
        return 'unknown'


def param_put_acms_server_manage(acms_server_manage):
    g_params['acms_server_manage'] = acms_server_manage


def param_get_acms_server_manage():
    if 'acms_server_manage' in g_params:
        return g_params['acms_server_manage']
    else:
        return 'unknown'


def param_put_smartplus_app_master(smartplus_app_master):
    g_params['smartplus_app_master'] = smartplus_app_master


def param_get_smartplus_app_master():
    if 'smartplus_app_master' in g_params:
        return g_params['smartplus_app_master']
    else:
        return 'unknown'


def param_put_smartplus_app_slave1(smartplus_app_slave1):
    g_params['smartplus_app_slave1'] = smartplus_app_slave1


def param_get_smartplus_app_slave1():
    if 'smartplus_app_slave1' in g_params:
        return g_params['smartplus_app_slave1']
    else:
        return 'unknown'


def param_put_smartplus_app_slave2(smartplus_app_slave2):
    g_params['smartplus_app_slave2'] = smartplus_app_slave2


def param_get_smartplus_app_slave2():
    if 'smartplus_app_slave2' in g_params:
        return g_params['smartplus_app_slave2']
    else:
        return 'unknown'


def param_put_smart_plus_emu_slave1(smart_plus_emu_slave1):
    g_params['smart_plus_emu_slave1'] = smart_plus_emu_slave1


def param_get_smart_plus_emu_slave1():
    if 'smart_plus_emu_slave1' in g_params:
        return g_params['smart_plus_emu_slave1']
    else:
        return None


def param_put_door_browser_master(door_browser_master):
    g_params['door_browser_master'] = door_browser_master


def param_get_door_browser_master():
    if 'door_browser_master' in g_params:
        return g_params['door_browser_master']
    else:
        return 'unknown'


def param_put_door_browser_slave1(door_browser_slave1):
    g_params['door_browser_slave1'] = door_browser_slave1


def param_get_door_browser_slave1():
    if 'door_browser_slave1' in g_params:
        return g_params['door_browser_slave1']
    else:
        return 'unknown'


def param_put_door_browser_slave2(door_browser_slave2):
    g_params['door_browser_slave2'] = door_browser_slave2


def param_get_door_browser_slave2():
    if 'door_browser_slave2' in g_params:
        return g_params['door_browser_slave2']
    else:
        return 'unknown'


def param_put_androiddoor_app_master(androiddoor_app_master):
    g_params['androiddoor_app_master'] = androiddoor_app_master


def param_get_androiddoor_app_master():
    if 'androiddoor_app_master' in g_params:
        return g_params['androiddoor_app_master']
    else:
        return 'unknown'


def param_put_androiddoor_app_slave1(androiddoor_app_slave1):
    g_params['androiddoor_app_slave1'] = androiddoor_app_slave1


def param_get_androiddoor_app_slave1():
    if 'androiddoor_app_slave1' in g_params:
        return g_params['androiddoor_app_slave1']
    else:
        return 'unknown'


def param_put_androiddoor_app_slave2(androiddoor_app_slave2):
    g_params['androiddoor_app_slave2'] = androiddoor_app_slave2


def param_get_androiddoor_app_slave2():
    if 'androiddoor_app_slave2' in g_params:
        return g_params['androiddoor_app_slave2']
    else:
        return 'unknown'


def param_put_linuxindoor_browser_master(linuxindoor_browser_master):
    g_params['linuxindoor_browser_master'] = linuxindoor_browser_master


def param_get_linuxindoor_browser_master():
    if 'linuxindoor_browser_master' in g_params:
        return g_params['linuxindoor_browser_master']
    else:
        return 'unknown'


def param_put_linuxindoor_browser_slave1(linuxindoor_browser_slave1):
    g_params['linuxindoor_browser_slave1'] = linuxindoor_browser_slave1


def param_get_linuxindoor_browser_slave1():
    if 'linuxindoor_browser_slave1' in g_params:
        return g_params['linuxindoor_browser_slave1']
    else:
        return 'unknown'


def param_put_linuxindoor_browser_slave2(linuxindoor_browser_slave2):
    g_params['linuxindoor_browser_slave2'] = linuxindoor_browser_slave2


def param_get_linuxindoor_browser_slave2():
    if 'linuxindoor_browser_slave2' in g_params:
        return g_params['linuxindoor_browser_slave2']
    else:
        return 'unknown'


def param_put_linuxindoor_browser_slave3(linuxindoor_browser_slave3):
    g_params['linuxindoor_browser_slave3'] = linuxindoor_browser_slave3


def param_get_linuxindoor_browser_slave3():
    if 'linuxindoor_browser_slave3' in g_params:
        return g_params['linuxindoor_browser_slave3']
    else:
        return 'unknown'


def param_put_linuxindoor_browser_slave4(linuxindoor_browser_slave4):
    g_params['linuxindoor_browser_slave4'] = linuxindoor_browser_slave4


def param_get_linuxindoor_browser_slave4():
    if 'linuxindoor_browser_slave4' in g_params:
        return g_params['linuxindoor_browser_slave4']
    else:
        return 'unknown'


def param_put_linuxindoor_browser_slave5(linuxindoor_browser_slave5):
    g_params['linuxindoor_browser_slave5'] = linuxindoor_browser_slave5


def param_get_linuxindoor_browser_slave5():
    if 'linuxindoor_browser_slave5' in g_params:
        return g_params['linuxindoor_browser_slave5']
    else:
        return 'unknown'


def param_put_linuxdoor_browser_slave1(linuxdoor_browser_slave1):
    g_params['linuxdoor_browser_slave1'] = linuxdoor_browser_slave1


def param_get_linuxdoor_browser_slave1():
    if 'linuxdoor_browser_slave1' in g_params:
        return g_params['linuxdoor_browser_slave1']
    else:
        return 'unknown'


def param_put_linuxhyperpanel_browser_master(linuxhyperpanel_browser_master):
    g_params['linuxhyperpanel_browser_master'] = linuxhyperpanel_browser_master


def param_get_linuxhyperpanel_browser_master():
    if 'linuxhyperpanel_browser_master' in g_params:
        return g_params['linuxhyperpanel_browser_master']
    else:
        return 'unknown'


def param_put_linuxhyperpanel_browser_slave1(linuxhyperpanel_browser_slave1):
    g_params['linuxhyperpanel_browser_slave1'] = linuxhyperpanel_browser_slave1


def param_get_linuxhyperpanel_browser_slave1():
    if 'linuxhyperpanel_browser_slave1' in g_params:
        return g_params['linuxhyperpanel_browser_slave1']
    else:
        return 'unknown'


def param_put_linuxhyperpanel_browser_slave2(linuxhyperpanel_browser_slave2):
    g_params['linuxhyperpanel_browser_slave2'] = linuxhyperpanel_browser_slave2


def param_get_linuxhyperpanel_browser_slave2():
    if 'linuxhyperpanel_browser_slave2' in g_params:
        return g_params['linuxhyperpanel_browser_slave2']
    else:
        return 'unknown'


def param_put_androidindoor_browser_master(androidindoor_browser_master):
    g_params['androidindoor_browser_master'] = androidindoor_browser_master


def param_get_androidindoor_browser_master():
    if 'androidindoor_browser_master' in g_params:
        return g_params['androidindoor_browser_master']
    else:
        return 'unknown'


def param_put_androidindoor_browser_slave1(androidindoor_browser_slave1):
    g_params['androidindoor_browser_slave1'] = androidindoor_browser_slave1


def param_get_androidindoor_browser_slave1():
    if 'androidindoor_browser_slave1' in g_params:
        return g_params['androidindoor_browser_slave1']
    else:
        return 'unknown'


def param_put_androidindoor_browser_slave2(androidindoor_browser_slave2):
    g_params['androidindoor_browser_slave2'] = androidindoor_browser_slave2


def param_get_androidindoor_browser_slave2():
    if 'androidindoor_browser_slave2' in g_params:
        return g_params['androidindoor_browser_slave2']
    else:
        return 'unknown'


def param_put_androidindoor_browser_slave3(androidindoor_browser_slave3):
    g_params['androidindoor_browser_slave3'] = androidindoor_browser_slave3


def param_get_androidindoor_browser_slave3():
    if 'androidindoor_browser_slave3' in g_params:
        return g_params['androidindoor_browser_slave3']
    else:
        return 'unknown'


def param_put_androidindoor_app_master(androidindoor_app_master):
    g_params['androidindoor_app_master'] = androidindoor_app_master


def param_get_androidindoor_app_master():
    if 'androidindoor_app_master' in g_params:
        return g_params['androidindoor_app_master']
    else:
        return 'unknown'


def param_put_androidindoor_app_slave1(androidindoor_app_slave1):
    g_params['androidindoor_app_slave1'] = androidindoor_app_slave1


def param_get_androidindoor_app_slave1():
    if 'androidindoor_app_slave1' in g_params:
        return g_params['androidindoor_app_slave1']
    else:
        return 'unknown'


def param_put_androidindoor_app_slave2(androidindoor_app_slave2):
    g_params['androidindoor_app_slave2'] = androidindoor_app_slave2


def param_get_androidindoor_app_slave2():
    if 'androidindoor_app_slave2' in g_params:
        return g_params['androidindoor_app_slave2']
    else:
        return 'unknown'


def param_put_androidindoor_factory_master(androidindoor_factory_master):
    g_params['androidindoor_factory_master'] = androidindoor_factory_master


def param_get_androidindoor_factory_master():
    if 'androidindoor_factory_master' in g_params:
        return g_params['androidindoor_factory_master']
    else:
        return 'unknown'


def param_put_videophone_app_master(videophone_app_master):
    g_params['videophone_app_master'] = videophone_app_master


def param_get_videophone_app_master():
    if 'videophone_app_master' in g_params:
        return g_params['videophone_app_master']
    else:
        return 'unknown'


def param_put_videophone_app_slave1(videophone_app_slave1):
    g_params['videophone_app_slave1'] = videophone_app_slave1


def param_get_videophone_app_slave1():
    if 'videophone_app_slave1' in g_params:
        return g_params['videophone_app_slave1']
    else:
        return 'unknown'


def param_put_videophone_app_slave2(videophone_app_slave2):
    g_params['videophone_app_slave2'] = videophone_app_slave2


def param_get_videophone_app_slave2():
    if 'videophone_app_slave2' in g_params:
        return g_params['videophone_app_slave2']
    else:
        return 'unknown'


def param_put_videophone_browser_master(videophone_browser_master):
    g_params['videophone_browser_master'] = videophone_browser_master


def param_get_videophone_browser_master():
    if 'videophone_browser_master' in g_params:
        return g_params['videophone_browser_master']
    else:
        return 'unknown'


def param_put_videophone_browser_slave1(videophone_browser_slave1):
    g_params['videophone_browser_slave1'] = videophone_browser_slave1


def param_get_videophone_browser_slave1():
    if 'videophone_browser_slave1' in g_params:
        return g_params['videophone_browser_slave1']
    else:
        return 'unknown'


def param_put_videophone_browser_slave2(videophone_browser_slave2):
    g_params['videophone_browser_slave2'] = videophone_browser_slave2


def param_get_videophone_browser_slave2():
    if 'videophone_browser_slave2' in g_params:
        return g_params['videophone_browser_slave2']
    else:
        return 'unknown'


def param_put_videophone_factory_master(videophone_factory_master):
    g_params['videophone_factory_master'] = videophone_factory_master


def param_get_videophone_factory_master():
    if 'videophone_factory_master' in g_params:
        return g_params['videophone_factory_master']
    else:
        return 'unknown'


def param_put_guardphone_app_master(guardphone_app_master):
    g_params['guardphone_app_master'] = guardphone_app_master


def param_get_guardphone_app_master():
    if 'guardphone_app_master' in g_params:
        return g_params['guardphone_app_master']
    else:
        return 'unknown'


def param_put_guardphone_app_slave1(guardphone_app_slave1):
    g_params['guardphone_app_slave1'] = guardphone_app_slave1


def param_get_guardphone_app_slave1():
    if 'guardphone_app_slave1' in g_params:
        return g_params['guardphone_app_slave1']
    else:
        return 'unknown'


def param_put_guardphone_app_slave2(guardphone_app_slave2):
    g_params['guardphone_app_slave2'] = guardphone_app_slave2


def param_get_guardphone_app_slave2():
    if 'guardphone_app_slave2' in g_params:
        return g_params['guardphone_app_slave2']
    else:
        return 'unknown'


def param_put_guardphone_browser_master(guardphone_browser_master):
    g_params['guardphone_browser_master'] = guardphone_browser_master


def param_get_guardphone_browser_master():
    if 'guardphone_browser_master' in g_params:
        return g_params['guardphone_browser_master']
    else:
        return 'unknown'


def param_put_guardphone_browser_slave1(guardphone_browser_slave1):
    g_params['guardphone_browser_slave1'] = guardphone_browser_slave1


def param_get_guardphone_browser_slave1():
    if 'guardphone_browser_slave1' in g_params:
        return g_params['guardphone_browser_slave1']
    else:
        return 'unknown'


def param_put_guardphone_browser_slave2(guardphone_browser_slave2):
    g_params['guardphone_browser_slave2'] = guardphone_browser_slave2


def param_get_guardphone_browser_slave2():
    if 'guardphone_browser_slave2' in g_params:
        return g_params['guardphone_browser_slave2']
    else:
        return 'unknown'


def param_put_ipphone_browser_master(ipphone_browser_master):
    g_params['ipphone_browser_master'] = ipphone_browser_master


def param_get_ipphone_browser_master():
    if 'ipphone_browser_master' in g_params:
        return g_params['ipphone_browser_master']
    else:
        return 'unknown'


def param_put_ipphone_browser_slave1(ipphone_browser_slave1):
    g_params['ipphone_browser_slave1'] = ipphone_browser_slave1


def param_get_ipphone_browser_slave1():
    if 'ipphone_browser_slave1' in g_params:
        return g_params['ipphone_browser_slave1']
    else:
        return 'unknown'


def param_put_ipphone_browser_slave2(ipphone_browser_slave2):
    g_params['ipphone_browser_slave2'] = ipphone_browser_slave2


def param_get_ipphone_browser_slave2():
    if 'ipphone_browser_slave2' in g_params:
        return g_params['ipphone_browser_slave2']
    else:
        return 'unknown'


def param_put_macwrite(macwrite):
    g_params['macwrite'] = macwrite


def param_get_macwrite():
    return g_params['macwrite']


def param_put_maccheck(maccheck):
    g_params['maccheck'] = maccheck


def param_get_maccheck():
    return g_params['maccheck']


def param_put_selftestdassistant(selftestdassistant):
    g_params['selftestdassistant'] = selftestdassistant


def param_get_selftestdassistant():
    return g_params['selftestdassistant']


def param_put_door_emulator(door_emulator):
    g_params['door_emulator'] = door_emulator


def param_get_door_emulator():
    return g_params['door_emulator']


def param_put_indoor_emulator(indoor_emulator):
    g_params['indoor_emulator'] = indoor_emulator


def param_get_indoor_emulator():
    return g_params['indoor_emulator']


def param_put_factory_tool(factory_tool):
    g_params['factory_tool'] = factory_tool


def param_get_factory_tool():
    if 'factory_tool' in g_params:
        return g_params['factory_tool']
    else:
        return 'unknown'


def param_put_test_counts(test_counts):
    g_params['test_counts'] = test_counts


def param_get_test_counts():
    if 'test_counts' in g_params:
        return g_params['test_counts']
    else:
        return 1


def param_put_test_times(test_times):
    g_params['test_times'] = test_times


def param_get_test_times():
    if 'test_times' in g_params:
        return g_params['test_times']
    else:
        return 1


def param_put_test_rounds(test_rounds):
    g_params['test_rounds'] = test_rounds


def param_get_test_rounds():
    if 'test_rounds' in g_params:
        return g_params['test_rounds']
    else:
        return 1


def param_put_retry_counts(retry_counts):
    g_params['retry_counts'] = retry_counts


def param_get_retry_counts():
    if 'retry_counts' in g_params:
        return g_params['retry_counts']
    else:
        return 0


def param_put_fail_case_count(fail_case):
    if 'fail_case_count' not in g_params:
        g_params['fail_case_count'] = {}
    if fail_case not in g_params['fail_case_count']:
        g_params['fail_case_count'][fail_case] = 0
    g_params['fail_case_count'][fail_case] += 1


def param_get_fail_case_count():
    if 'fail_case_count' in g_params:
        return g_params['fail_case_count']
    else:
        return {}


def param_put_pause_run(pause_run):
    g_params['pause_run'] = pause_run


def param_get_pause_run():
    if 'pause_run' in g_params:
        return g_params['pause_run']
    else:
        return False


def param_put_running_state(running_state):
    g_params['running_state'] = running_state


def param_get_running_state():
    if 'running_state' in g_params:
        return g_params['running_state']
    else:
        return False


def param_put_launch_window_app(launch_window_app):
    g_params['launch_window_app'] = launch_window_app


def param_get_launch_window_app():
    if 'launch_window_app' in g_params:
        return g_params['launch_window_app']
    else:
        return None


def param_put_failed_to_exit_enable(failed_to_exit_enable):
    aklog_warn('param_put_failed_to_exit_enable: %s' % failed_to_exit_enable)
    g_params['failed_to_exit_enable'] = failed_to_exit_enable


def param_get_failed_to_exit_enable():
    if 'failed_to_exit_enable' in g_params:
        return g_params['failed_to_exit_enable']
    else:
        return False


def param_put_stop_exec_enable(stop_exec_enable):
    aklog_warn('param_put_stop_exec_enable: %s' % stop_exec_enable)
    g_params['stop_exec_enable'] = stop_exec_enable


def param_get_stop_exec_enable():
    if 'stop_exec_enable' in g_params:
        return g_params['stop_exec_enable']
    else:
        return False


def param_put_scheduled_execution_enable(scheduled_execution_enable):
    aklog_info('param_put_scheduled_execution_enable: %s' % scheduled_execution_enable)
    g_params['scheduled_execution_enable'] = scheduled_execution_enable


def param_get_scheduled_execution_enable():
    if 'scheduled_execution_enable' in g_params:
        return g_params['scheduled_execution_enable']
    else:
        return False


def param_put_test_case_balance_enable(test_case_balance_enable):
    g_params['test_case_balance_enable'] = test_case_balance_enable


def param_get_test_case_balance_enable():
    if 'test_case_balance_enable' in g_params:
        return g_params['test_case_balance_enable']
    else:
        return False


def param_put_failed_to_notification_enable(failed_to_notification_enable):
    aklog_info('param_put_failed_to_notification_enable: %s' % failed_to_notification_enable)
    g_params['failed_to_notification_enable'] = failed_to_notification_enable


def param_get_failed_to_notification_enable():
    if 'failed_to_notification_enable' in g_params:
        return g_params['failed_to_notification_enable']
    else:
        return False


def param_put_pause_during_nap_time_enable(pause_during_nap_time_enable):
    aklog_info('pause_during_nap_time_enable: %s' % pause_during_nap_time_enable)
    g_params['pause_during_nap_time_enable'] = pause_during_nap_time_enable


def param_get_pause_during_nap_time_enable():
    if 'pause_during_nap_time_enable' in g_params:
        return g_params['pause_during_nap_time_enable']
    else:
        return False


def param_put_save_last_try_state(save_last_try_state):
    g_params['save_last_try_state'] = save_last_try_state


def param_get_save_last_try_state():
    if 'save_last_try_state' in g_params:
        return g_params['save_last_try_state']
    else:
        return True


def param_put_send_test_results_summary_enable(send_test_results_summary_enable):
    g_params['send_test_results_summary_enable'] = send_test_results_summary_enable


def param_get_send_test_results_summary_enable():
    if 'send_test_results_summary_enable' in g_params:
        return g_params['send_test_results_summary_enable']
    else:
        return False


def param_put_skip_download_firmware_state(skip_download_firmware_state):
    g_params['skip_download_firmware_state'] = skip_download_firmware_state


def param_get_skip_download_firmware_state():
    if 'skip_download_firmware_state' in g_params:
        return g_params['skip_download_firmware_state']
    else:
        return False


def param_put_send_email_state(send_email_state):
    g_params['send_email_state'] = send_email_state


def param_get_send_email_state():
    if 'send_email_state' in g_params:
        return g_params['send_email_state']
    else:
        return False


def param_put_send_work_weixin_state(send_work_weixin_state):
    g_params['send_work_weixin_state'] = send_work_weixin_state


def param_get_send_work_weixin_state():
    if 'send_work_weixin_state' in g_params:
        return g_params['send_work_weixin_state']
    else:
        return False


def param_put_robot_info(robot_info):
    g_params['robot_info'] = robot_info


def param_get_robot_info():
    if 'robot_info' in g_params:
        return g_params['robot_info']
    else:
        return None


def param_put_added_email_receivers(added_email_receivers):
    g_params['added_email_receivers'] = added_email_receivers


def param_get_added_email_receivers():
    if 'added_email_receivers' in g_params:
        return g_params['added_email_receivers']
    else:
        return None


def param_put_email_receivers(email_receivers):
    g_params['email_receivers'] = email_receivers


def param_get_email_receivers() -> Optional[list]:
    if 'email_receivers' in g_params:
        return g_params['email_receivers']
    else:
        return None


def param_put_build_user(build_user):
    g_params['build_user'] = build_user


def param_get_build_user() -> str:
    if 'build_user' in g_params:
        return g_params['build_user']
    else:
        return ''


def param_put_test_random_state(test_random_state):
    g_params['test_random_state'] = test_random_state


def param_get_test_random_state():
    if 'test_random_state' in g_params:
        return g_params['test_random_state']
    else:
        return False


def param_put_report_type(report_type):
    g_params['report_type'] = report_type


def param_get_report_type():
    if 'report_type' in g_params:
        return g_params['report_type']
    else:
        return 'HTML'


def param_put_browser_headless_enable(browser_headless_enable):
    g_params['browser_headless_enable'] = browser_headless_enable


def param_get_browser_headless_enable():
    if 'browser_headless_enable' in g_params:
        return g_params['browser_headless_enable']
    else:
        return False


def param_get_browser_in_second_screen():
    if 'browser_in_second_screen' in g_params:
        return g_params['browser_in_second_screen']
    else:
        return False


def param_put_browser_in_second_screen(enable):
    g_params['browser_in_second_screen'] = enable


def param_put_exec_one_case_to_report_enable(exec_one_case_to_report_enable):
    g_params['exec_one_case_to_report_enable'] = exec_one_case_to_report_enable


def param_get_exec_one_case_to_report_enable():
    if 'exec_one_case_to_report_enable' in g_params:
        return g_params['exec_one_case_to_report_enable']
    else:
        return False


def param_put_vfone_app_master(vfone_app_master):
    g_params['vfone_app_master'] = vfone_app_master


def param_get_vfone_app_master():
    if 'vfone_app_master' in g_params:
        return g_params['vfone_app_master']
    else:
        return 'unknown'


def param_put_upgrade_tool(upgrade_tool):
    g_params['upgrade_tool'] = upgrade_tool


def param_get_upgrade_tool():
    if 'upgrade_tool' in g_params:
        return g_params['upgrade_tool']
    else:
        return 'unknown'


def param_put_access_control_browser_master(access_control_browser_master):
    g_params['access_control_browser_master'] = access_control_browser_master


def param_get_access_control_browser_master():
    if 'access_control_browser_master' in g_params:
        return g_params['access_control_browser_master']
    else:
        return 'unknown'


def param_put_access_control_browser_slave1(access_control_browser_slave1):
    g_params['access_control_browser_slave1'] = access_control_browser_slave1


def param_get_access_control_browser_slave1():
    if 'access_control_browser_slave1' in g_params:
        return g_params['access_control_browser_slave1']
    else:
        return 'unknown'


def param_put_access_control_browser_slave2(access_control_browser_slave2):
    g_params['access_control_browser_slave2'] = access_control_browser_slave2


def param_get_access_control_browser_slave2():
    if 'access_control_browser_slave2' in g_params:
        return g_params['access_control_browser_slave2']
    else:
        return 'unknown'


def param_put_access_door_browser_master(access_door_browser_master):
    g_params['access_door_browser_master'] = access_door_browser_master


def param_get_access_door_browser_master():
    if 'access_door_browser_master' in g_params:
        return g_params['access_door_browser_master']
    else:
        return 'unknown'


def param_put_access_door_browser_slave1(access_door_browser_slave1):
    g_params['access_door_browser_slave1'] = access_door_browser_slave1


def param_get_access_door_browser_slave1():
    if 'access_door_browser_slave1' in g_params:
        return g_params['access_door_browser_slave1']
    else:
        return 'unknown'


def param_put_access_door_browser_slave2(access_door_browser_slave2):
    g_params['access_door_browser_slave2'] = access_door_browser_slave2


def param_get_access_door_browser_slave2():
    if 'access_door_browser_slave2' in g_params:
        return g_params['access_door_browser_slave2']
    else:
        return 'unknown'


def param_append_screenshots_imgs(img_base64):
    g_screenshots_imgs.append(img_base64)


def param_reset_screenshots_imgs():
    g_screenshots_imgs.clear()


def param_get_screenshots_imgs():
    return g_screenshots_imgs


def param_append_test_results(result: list):
    g_test_results.append(result)


def param_reset_test_results():
    g_test_results.clear()


def param_get_test_results():
    return g_test_results


def param_put_temp_images(*images):
    """将图片传递给全局变量，可以用于测试用例失败后在测试报告中显示截图"""
    if images:
        g_params['temp_images'] = list(images)
    else:
        g_params['temp_images'] = None


def param_get_temp_images():
    return g_params['temp_images']


def param_put_access_control_factory_tool(access_control_factory_tool):
    g_params['access_control_factory_tool'] = access_control_factory_tool


def param_get_access_control_factory_tool():
    return g_params['access_control_factory_tool']


def param_put_androidhyperpanel_browser_master(androidhyperpanel_browser_master):
    g_params['androidhyperpanel_browser_master'] = androidhyperpanel_browser_master


def param_get_androidhyperpanel_browser_master():
    if 'androidhyperpanel_browser_master' in g_params:
        return g_params['androidhyperpanel_browser_master']
    else:
        return 'unknown'


def param_put_androidhyperpanel_browser_slave1(androidhyperpanel_browser_slave1):
    g_params['androidhyperpanel_browser_slave1'] = androidhyperpanel_browser_slave1


def param_get_androidhyperpanel_browser_slave1():
    if 'androidhyperpanel_browser_slave1' in g_params:
        return g_params['androidhyperpanel_browser_slave1']
    else:
        return 'unknown'


def param_put_androidhyperpanel_browser_slave2(androidhyperpanel_browser_slave2):
    g_params['androidhyperpanel_browser_slave2'] = androidhyperpanel_browser_slave2


def param_get_androidhyperpanel_browser_slave2():
    if 'androidhyperpanel_browser_slave2' in g_params:
        return g_params['androidhyperpanel_browser_slave2']
    else:
        return 'unknown'


def param_put_androidhyperpanel_browser_slave3(androidhyperpanel_browser_slave3):
    g_params['androidhyperpanel_browser_slave3'] = androidhyperpanel_browser_slave3


def param_get_androidhyperpanel_browser_slave3():
    if 'androidhyperpanel_browser_slave3' in g_params:
        return g_params['androidhyperpanel_browser_slave3']
    else:
        return 'unknown'


def param_put_androidhyperpanel_app_master(androidhyperpanel_app_master):
    g_params['androidhyperpanel_app_master'] = androidhyperpanel_app_master


def param_get_androidhyperpanel_app_master():
    if 'androidhyperpanel_app_master' in g_params:
        return g_params['androidhyperpanel_app_master']
    else:
        return 'unknown'


def param_put_androidhyperpanel_app_slave1(androidhyperpanel_app_slave1):
    g_params['androidhyperpanel_app_slave1'] = androidhyperpanel_app_slave1


def param_get_androidhyperpanel_app_slave1():
    if 'androidhyperpanel_app_slave1' in g_params:
        return g_params['androidhyperpanel_app_slave1']
    else:
        return 'unknown'


def param_put_androidhyperpanel_app_slave2(androidhyperpanel_app_slave2):
    g_params['androidhyperpanel_app_slave2'] = androidhyperpanel_app_slave2


def param_get_androidhyperpanel_app_slave2():
    if 'androidhyperpanel_app_slave2' in g_params:
        return g_params['androidhyperpanel_app_slave2']
    else:
        return 'unknown'


def param_put_androidhyperpanel_userweb_master(androidhyperpanel_userweb_master):
    g_params['androidhyperpanel_userweb_master'] = androidhyperpanel_userweb_master


def param_get_androidhyperpanel_userweb_master():
    if 'androidhyperpanel_userweb_master' in g_params:
        return g_params['androidhyperpanel_userweb_master']
    else:
        return 'unknown'


def param_put_androidhyperpanel_userweb_slave1(androidhyperpanel_userweb_slave1):
    g_params['androidhyperpanel_userweb_slave1'] = androidhyperpanel_userweb_slave1


def param_get_androidhyperpanel_userweb_slave1():
    if 'androidhyperpanel_userweb_slave1' in g_params:
        return g_params['androidhyperpanel_userweb_slave1']
    else:
        return 'unknown'


def param_put_belahome_app_master(belahome_app_master):
    g_params['belahome_app_master'] = belahome_app_master


def param_get_belahome_app_master():
    if 'belahome_app_master' in g_params:
        return g_params['belahome_app_master']
    else:
        return 'unknown'


def param_put_belahome_app_slave1(belahome_app_slave1):
    g_params['belahome_app_slave1'] = belahome_app_slave1


def param_get_belahome_app_slave1():
    if 'belahome_app_slave1' in g_params:
        return g_params['belahome_app_slave1']
    else:
        return 'unknown'


def param_put_belahome_app_slave2(belahome_app_slave2):
    g_params['belahome_app_slave2'] = belahome_app_slave2


def param_get_belahome_app_slave2():
    if 'belahome_app_slave2' in g_params:
        return g_params['belahome_app_slave2']
    else:
        return 'unknown'


def param_put_belahome_app_slave3(belahome_app_slave3):
    g_params['belahome_app_slave3'] = belahome_app_slave3


def param_get_belahome_app_slave3():
    if 'belahome_app_slave3' in g_params:
        return g_params['belahome_app_slave3']
    else:
        return 'unknown'


def param_put_androidsmartpanel_app_master(androidsmartpanel_app_master):
    g_params['androidsmartpanel_app_master'] = androidsmartpanel_app_master


def param_get_androidsmartpanel_app_master():
    if 'androidsmartpanel_app_master' in g_params:
        return g_params['androidsmartpanel_app_master']
    else:
        return 'unknown'


def param_put_androidsmartpanel_app_slave1(androidsmartpanel_app_slave1):
    g_params['androidsmartpanel_app_slave1'] = androidsmartpanel_app_slave1


def param_get_androidsmartpanel_app_slave1():
    if 'androidsmartpanel_app_slave1' in g_params:
        return g_params['androidsmartpanel_app_slave1']
    else:
        return 'unknown'


def param_put_androidsmartpanel_browser_master(androidsmartpanel_browser_master):
    g_params['androidsmartpanel_browser_master'] = androidsmartpanel_browser_master


def param_get_androidsmartpanel_browser_master():
    if 'androidsmartpanel_browser_master' in g_params:
        return g_params['androidsmartpanel_browser_master']
    else:
        return 'unknown'


def param_put_androidsmartpanel_browser_slave1(androidsmartpanel_browser_slave1):
    g_params['androidsmartpanel_browser_slave1'] = androidsmartpanel_browser_slave1


def param_get_androidsmartpanel_browser_slave1():
    if 'androidsmartpanel_browser_slave1' in g_params:
        return g_params['androidsmartpanel_browser_slave1']
    else:
        return 'unknown'


def param_put_androidsmartpanel_user_web_master(androidsmartpanel_user_web_master):
    g_params['androidsmartpanel_user_web_master'] = androidsmartpanel_user_web_master


def param_get_androidsmartpanel_user_web_master():
    if 'androidsmartpanel_user_web_master' in g_params:
        return g_params['androidsmartpanel_user_web_master']
    else:
        return 'unknown'


def param_put_androidsmartpanel_user_web_slave1(androidsmartpanel_user_web_slave1):
    g_params['androidsmartpanel_user_web_slave1'] = androidsmartpanel_user_web_slave1


def param_get_androidsmartpanel_user_web_slave1():
    if 'androidsmartpanel_user_web_slave1' in g_params:
        return g_params['androidsmartpanel_user_web_slave1']
    else:
        return 'unknown'
