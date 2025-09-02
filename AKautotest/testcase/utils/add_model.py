# -*- coding: UTF-8 -*-
import sys
import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos+len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *

"""
本模块用于添加机型升级自动化测试
自动修改的有：
1、创建testfile目录下的相关机型文件夹和文件，
2、修改model_name.xml和series_products.xml文件添加对应机型，
3、添加device config模块（但需要手动修改内容为对应机型）。

其他需要手动添加修改的有：
1、device_info.xml文件添加对应机型信息
2、upgrade_autotest目录下要添加入口文件

然后提交到SVN
"""

# 要先输入添加的机型型号、ID、产品系列，以及参照的机型
model_id = '313'
model_name = 'C313V3'
series_products = 'LINUXINDOOR'
series_module_name = 'LinuxIndoor'
version_branch = 'V10_0'
cmp_model_name = 'C313V3'
cmp_series_products = 'LINUXINDOOR'
cmp_version_branch = 'V10_0'


def create_model_dir_under_testfile():
    autop_config_template_dir = root_path + '/testfile/autop_config_template/' + model_name
    if not os.path.exists(autop_config_template_dir):
        os.makedirs(autop_config_template_dir)

    BatMonitor_dir = root_path + '/testfile/BatMonitor/' + model_name
    if not os.path.exists(BatMonitor_dir):
        os.makedirs(BatMonitor_dir)

    Chrome_Download_dir = root_path + '/testfile/Browser/Chrome_Download/' + model_name
    if not os.path.exists(Chrome_Download_dir):
        os.makedirs(Chrome_Download_dir)

    config_file_import_dir = root_path + '/testfile/config_file_import/' + model_name
    if not os.path.exists(config_file_import_dir):
        os.makedirs(config_file_import_dir)

    Device_log_dir = root_path + '/testfile/Device_log/' + model_name
    if not os.path.exists(Device_log_dir):
        os.makedirs(Device_log_dir)

    Firmware_dir = root_path + '/testfile/Firmware/' + model_name
    if not os.path.exists(Firmware_dir):
        os.makedirs(Firmware_dir)

    Monitor_dir = root_path + '/testfile/Monitor/' + model_name
    if not os.path.exists(Monitor_dir):
        os.makedirs(Monitor_dir)

    sdmc_upgrade_firmware_dir = root_path + '/testfile/sdmc_upgrade_firmware/' + model_name
    if not os.path.exists(sdmc_upgrade_firmware_dir):
        os.makedirs(sdmc_upgrade_firmware_dir)

    upgrade_firmware_dir = root_path + '/testfile/upgrade_firmware/' + model_name
    if not os.path.exists(upgrade_firmware_dir):
        os.makedirs(upgrade_firmware_dir)

    old_firmware_version_dir = root_path + '/testfile/old_firmware_version/' + model_name
    if not os.path.exists(old_firmware_version_dir):
        os.makedirs(old_firmware_version_dir)

    File_process.copy_file(root_path + '/testfile/autop_config_file/' + cmp_model_name + '.cfg',
                           root_path + '/testfile/autop_config_file/' + model_name + '.cfg')
    File_process.copy_file(root_path + '/testfile/autop_config_template/' + cmp_model_name +
                           '/autop_config_template_' + cmp_model_name + '_NORMAL.cfg',
                           root_path + '/testfile/autop_config_template/' + model_name +
                           '/autop_config_template_' + model_name + '_NORMAL.cfg')


def create_config():
    series_config_dir = os.path.join(g_config_path, series_products, 'NORMAL')
    if not os.path.exists(series_config_dir):
        os.makedirs(series_config_dir)
    cmp_series_config_dir = os.path.join(g_config_path, cmp_series_products, 'NORMAL')
    if not os.path.exists(series_config_dir + '/libconfig_' + series_products + '_NORMAL.py'):
        File_process.copy_file(cmp_series_config_dir + '/libconfig_' + cmp_series_products + '_NORMAL.py',
                               series_config_dir + '/libconfig_' + series_products + '_NORMAL.py')

    model_config_dir = os.path.join(g_config_path, series_products, model_name, 'NORMAL')
    if not os.path.exists(model_config_dir):
        os.makedirs(model_config_dir)
    cmp_model_config_dir = os.path.join(g_config_path, cmp_series_products, cmp_model_name, 'NORMAL')
    File_process.copy_file(cmp_model_config_dir + '/libconfig_' + cmp_model_name + '_NORMAL.py',
                           model_config_dir + '/libconfig_' + model_name + '_NORMAL.py')


def create_firmware_info():
    firmware_info_dir = root_path + '/testdata/FirmwareInfo/' + model_name
    if not os.path.exists(firmware_info_dir):
        os.makedirs(firmware_info_dir)
    cmp_firmware_info_file = root_path + '/testdata/FirmwareInfo/' + cmp_model_name + '/' + cmp_model_name + '.xml'
    firmware_info_file = firmware_info_dir + '/' + model_name + '.xml'
    File_process.copy_file(cmp_firmware_info_file, firmware_info_file)


def modify_model_name_xml():
    modelid = 'model_id_' + model_id
    file_path = g_config_path + '\\product_oem_config\\model_name.xml'
    xml_add_line_attribute(file_path, 'model_name', modelid, model_name)


def modify_series_products_xml():
    file_path = g_config_path + '\\product_oem_config\\series_products.xml'
    xml_add_line_attribute(file_path, 'series_products', model_name, series_products)


def modify_series_module_name():
    file_path = g_config_path + '\\product_oem_config\\series_module_name.xml'
    xml_add_line_attribute(file_path, 'series_module_name', series_products, series_module_name)


def modify_oem_name_xml(oem_list_file):
    """先从wiki上将OEMlist保存到文本，然后再从文本读取内容写入到XML文件，需要先把xml之前oemlist清空"""
    file_path = g_config_path + '\\product_oem_config\\oem_name.xml'
    lines = File_process.get_file_lines(oem_list_file)
    print(lines)
    for line in lines:
        if line and line != '\n' and '#' not in line:
            oem_id = 'oem_id_' + line.split('=')[-1].strip()
            print(oem_id)
            oem_name = line.split('OEMID_')[1].split('=')[0].strip()
            print(oem_name)
            xml_add_line_attribute(file_path, 'oem_name', oem_id, oem_name)


def create_test_data():
    """创建testdata目录，并复制device_info.xml和version_branch.xml"""
    test_data_series_dir = root_path + '\\testdata\\%s\\%s\\NORMAL' % (series_products, version_branch)
    test_data_model_dir = root_path + '\\testdata\\%s\\%s\\%s\\NORMAL' % (series_products, version_branch, model_name)
    if not os.path.exists(test_data_series_dir):
        os.makedirs(test_data_series_dir)
    if not os.path.exists(test_data_model_dir):
        os.makedirs(test_data_model_dir)
    cmp_test_data_series_dir = root_path + '\\testdata\\%s\\%s\\NORMAL' % (cmp_series_products, cmp_version_branch)
    cmp_test_data_model_dir = root_path + '\\testdata\\%s\\%s\\%s\\NORMAL' % (
        cmp_series_products, cmp_version_branch, cmp_model_name)

    if not os.path.exists(test_data_series_dir + '\\device_info.xml'):
        File_process.copy_file(cmp_test_data_series_dir + '\\device_info.xml',
                               test_data_series_dir + '\\device_info.xml')

    if not os.path.exists(test_data_series_dir + '\\version_branch.xml'):
        File_process.copy_file(cmp_test_data_series_dir + '\\version_branch.xml',
                               test_data_series_dir + '\\version_branch.xml')

    if not os.path.exists(test_data_model_dir + '\\device_info.xml'):
        File_process.copy_file(cmp_test_data_model_dir + '\\device_info.xml',
                               test_data_model_dir + '\\device_info.xml')


def create_module_base_dir():
    """创建module模块下Base目录和ModuleList"""
    module_series_modulelist_dir = '%s\\testcase\\module\\%s\\%s\\Base\\ModuleList\\NORMAL'\
                                   % (root_path, version_branch, series_module_name)
    if not os.path.exists(module_series_modulelist_dir):
        os.makedirs(module_series_modulelist_dir)


def add_series():
    modify_model_name_xml()
    modify_series_products_xml()
    modify_series_module_name()
    create_config()
    create_model_dir_under_testfile()
    create_firmware_info()
    create_test_data()
    create_module_base_dir()


def add_model():
    modify_model_name_xml()
    modify_series_products_xml()
    modify_series_module_name()
    create_config()
    create_model_dir_under_testfile()
    create_firmware_info()
    create_test_data()


if __name__ == '__main__':
    add_series()
    # modify_oem_name_xml('D:\\Users\\Administrator\\Desktop\\oemlist.txt')
