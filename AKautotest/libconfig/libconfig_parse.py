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
import traceback
import re
import yaml
from importlib import import_module


def config_get_series(model_name, index=0):
    """
    通过型号解析系列名称
    series_products.xml中，如果系列名称有分号分隔，说明该型号的系列名称有修改过，为了兼容，有些情况下需要使用旧的系列名称
    Args:
        model_name (str):
        index (int):
    """
    series_name = param_get_series_name_info(model_name)
    if series_name:
        return series_name
    series_products_config = param_get_series_products_config_data()
    if series_products_config == 'unknown':
        series_products_config = xml_read_sheet_data('%s\\product_oem_config\\series_products.xml' % g_config_path)
        param_put_series_products_config_data(series_products_config)
    series = None
    for line in series_products_config['series_products']:
        if model_name in line:
            series = line[model_name]
            break
    if series and ';' in series:
        # 如果有分号分隔，说明该型号的系列名称有修改过，为了兼容，有些情况下需要使用旧的系列名称
        series_list = series.split(';')
        if index >= len(series_list):
            index = -1
        series = series_list[index]
    return series


def config_get_product_line(series_name):
    product_line_config = param_get_product_line_config_data()
    if product_line_config == 'unknown':
        product_line_config = xml_read_sheet_data('%s\\product_oem_config\\product_line.xml' % g_config_path)
        param_put_product_line_config_data(product_line_config)
    product_line = None
    for line in product_line_config['product_line']:
        if series_name in line:
            product_line = line[series_name]
            break
    return product_line


def config_get_product_line_by_series_module_name(series_module_name):
    series_module_name_info = param_get_series_module_name_info()
    if series_module_name_info == 'unknown':
        series_module_name_info = xml_read_sheet_data('%s\\product_oem_config\\series_module_name.xml' % g_config_path)
        param_put_series_module_name_info(series_module_name_info)
    
    series_module_name_dict = {}
    for line in series_module_name_info['series_module_name']:
        series_module_name_dict.update(line)
    reversed_series_module_name_dict = {value: key for key, value in series_module_name_dict.items()}
    series_name = reversed_series_module_name_dict.get(series_module_name)
    
    product_line_config = param_get_product_line_config_data()
    if product_line_config == 'unknown':
        product_line_config = xml_read_sheet_data('%s\\product_oem_config\\product_line.xml' % g_config_path)
        param_put_product_line_config_data(product_line_config)
    product_line = None
    for line in product_line_config['product_line']:
        if series_name in line:
            product_line = line[series_name]
            break
    return product_line


def config_get_modelname(model_id=None):
    firmware_info = param_get_firmware_info()
    model_version_info = param_get_model_version_info()
    if not model_version_info:
        model_version_info = xml_parse_model_version_info()
        param_put_model_version_info(model_version_info)
    # 判断firmware info中的型号是否正确，是否跟model_id匹配
    model_name = firmware_info.get('model_name', '').strip()
    # FirmwareInfo中的型号，如果是禅道创建的，型号可能跟自动化命名不一致，需要匹配转换下
    readconfig = ReadConfig('%s\\product_oem_config\\model_name_map.ini' % g_config_path)
    model_name_map = readconfig.get_dict('model_name_map')
    if model_name in model_name_map:
        model_name = model_name_map[model_name]
    elif model_id and '%s(%s)' % (model_name, model_id) in model_name_map:
        model_name = model_name_map['%s(%s)' % (model_name, model_id)]
    
    # 如果FirmwareInfo中获取的型号不为空，并且根据型号获取的系列产品不为空，获取版本信息的model_id匹配
    if model_name and config_get_series(model_name) is not None \
            and model_version_info.get(model_name) \
            and (not model_id
                 or (model_version_info.get(model_name).get('model_id').isdigit()
                     and model_version_info.get(model_name).get('model_id') == model_id)
                 or not model_version_info.get(model_name).get('model_id').isdigit()):
        aklog_info('model_name: %s' % model_name)
        return model_name
    
    if model_id:
        aklog_warn(
            'FirmwareInfo中的型号 %s 跟版本号中的ModelID %s 不匹配，将根据ModelID重新获取' % (model_name, model_id))
        model_name_config = param_get_model_name_config_data()
        if model_name_config == 'unknown':
            model_name_config = xml_read_sheet_data('%s\\product_oem_config\\model_name.xml' % g_config_path)
            param_put_model_name_config_data(model_name_config)
        model_id = 'model_id_' + model_id
        if model_id in model_name_config['model_name'][0]:
            model_name = model_name_config['model_name'][0][model_id]
        else:
            model_name = 'unknown'
            aklog_printf(
                '获取型号失败，请检查model_name.xml和model_version_info.xml文件中的model名称和model id是否遗漏或错误')
        aklog_info('model_name: %s' % model_name)
        return model_name
    return None


def config_get_oemname(oem_id):
    firmware_info = param_get_firmware_info()
    if 'oem_name' in firmware_info:
        oem_name = firmware_info['oem_name']
    else:
        oem_name_config = param_get_oem_name_config_data()
        if oem_name_config == 'unknown':
            oem_name_config = xml_read_sheet_data('%s\\product_oem_config\\oem_name.xml' % g_config_path)
            param_put_oem_name_config_data(oem_name_config)
        oem_id = 'oem_id_' + oem_id
        if oem_id in oem_name_config['oem_name'][0]:
            oem_name = oem_name_config['oem_name'][0][oem_id]
        else:
            aklog_printf("%s isn't exist" % oem_id)
            oem_name = 'NORMAL'
    aklog_printf("oem_name: %s" % oem_name)
    return oem_name


def config_get_series_module_name(series):
    series_module_name_info = param_get_series_module_name_info()
    if series_module_name_info == 'unknown':
        series_module_name_info = xml_read_sheet_data('%s\\product_oem_config\\series_module_name.xml' % g_config_path)
        param_put_series_module_name_info(series_module_name_info)
    
    series_module_name = None
    for line in series_module_name_info['series_module_name']:
        if series in line:
            series_module_name = line[series]
            # aklog_printf('series: %s, module_name: %s' % (series, series_module_name))
            break
    return series_module_name


def config_get_series_module_root_path(model_name, version_branch) -> str:
    series_products = config_get_series(model_name)
    series_module_name = config_get_series_module_name(series_products)
    product_line_name = config_get_product_line(series_products)
    series_module_root_path = os.path.join(g_module_root_path, product_line_name, series_module_name, version_branch)
    if not os.path.exists(series_module_root_path):
        series_module_root_path = os.path.join(g_module_root_path, series_module_name, version_branch)
    return str(series_module_root_path)


def config_get_series_module_sub_path(model_name, version_branch, *sub_paths) -> str:
    """
    获取module系列机型下子目录
    Args:
        model_name (str):
        version_branch (str):
        *sub_paths (str):
    """
    series_module_root_path = config_get_series_module_root_path(model_name, version_branch)
    series_module_sub_path = series_module_root_path
    for sub_path in sub_paths:
        series_module_sub_path = os.path.join(series_module_sub_path, sub_path)
    return str(series_module_sub_path)


def config_get_cloud_upgrade_model(model_name):
    cloud_upgrade_model_config = param_get_cloud_upgrade_model_config_data()
    if cloud_upgrade_model_config == 'unknown':
        cloud_upgrade_model_config = xml_read_sheet_data('%s\\product_oem_config\\cloud_upgrade_model.xml'
                                                         % g_config_path)
        param_put_cloud_upgrade_model_config_data(cloud_upgrade_model_config)
    if model_name in cloud_upgrade_model_config['cloud_upgrade_model'][0]:
        cloud_upgrade_model = cloud_upgrade_model_config['cloud_upgrade_model'][0][model_name]
    else:
        aklog_printf("%s isn't exist" % model_name)
        cloud_upgrade_model = model_name
    return cloud_upgrade_model


def config_get_oem_not_upgrade(model_name):
    oem_not_upgrade_list = []
    oem_not_upgrade_config = param_get_oem_not_upgrade_config_data()
    if oem_not_upgrade_config == 'unknown':
        oem_not_upgrade_config = xml_read_sheet_data('%s\\product_oem_config\\oem_not_upgrade.xml' % g_config_path)
        param_put_oem_not_upgrade_config_data(oem_not_upgrade_config)
    for line in oem_not_upgrade_config['oem_not_upgrade']:
        if line['model_name'] == model_name:
            for key in line:
                if key == 'model_name':
                    continue
                oem_not_upgrade_list.append(str(key))
            return oem_not_upgrade_list
    return None


def config_parse_model_version_branch(model_name, firmware_version):
    """根据型号和版本号解析设备的版本分支"""
    aklog_printf()
    model_version_info = param_get_model_version_info()
    if not firmware_version:
        if model_name not in model_version_info:
            aklog_warn(f'版本分支信息缺少 {model_name} 型号，'
                       '请在 libconfig/libconfig_xml/model_version_info/ 目录下添加机型版本分支信息')
            raise ValueError(f'版本分支信息缺少 {model_name} 型号')

        version_branch = model_version_info[model_name]['default_branch']
        aklog_warn(f'{model_name} 版本号为空，使用默认分支: {version_branch}')
        return version_branch
    versions = firmware_version.split('.')
    oem_id = None
    if len(versions) == 3 and model_name in ['BELAHOME', 'BELAHOMEIOS']:
        # 家居APP版本号只有3位，前面两个表示大版本号
        version_num = '%s.%03d' % (versions[0], int(versions[1]))
    elif len(versions) == 3 and model_name in ['AKUBELASOLUTION']:
        # 家居解决方案的版本号只有3位
        version_num = '%s.%03d' % (versions[0], int(versions[1]+versions[2]))
    else:
        oem_id = versions[1]
        big_version = versions[-2]
        if len(big_version) > 2:
            # 如果大版本号大于100，则当成是拉的分支版本
            big_version = big_version[0:1]
        version_num = '%s.%03d' % (big_version, int(versions[-1]))
    version_num = float(version_num)
    aklog_printf(f'version_num: {version_num}')

    if not model_version_info:
        model_version_info = xml_parse_model_version_info()
        param_put_model_version_info(model_version_info)
    if model_name in model_version_info:
        version_branch_info = model_version_info[model_name]['version_branch_info']
        version_range_name = 'version_range__%s' % oem_id
        version_branch = ''
        for branch in version_branch_info:
            version_range = branch.get(version_range_name)
            if version_range is not None:
                aklog_printf('%s分支的 %s 版本范围: %s' % (branch['autotest_branch'], oem_id, version_range))
                # 如果有指定OEM的版本范围，则判断版本是否在OEM版本范围里，来获取分支
                if '-' in version_range:
                    version_range = version_range.replace('--', '-')
                    min_version = version_range.split('-')[0]
                    min_num = float('%s.%03d' % (min_version.split('.')[0], int(min_version.split('.')[-1])))
                    max_version = version_range.split('-')[-1]
                    if max_version:
                        max_num = float('%s.%03d' % (max_version.split('.')[0], int(max_version.split('.')[-1])))
                    else:
                        max_num = 0
                    
                    if (max_num and min_num and min_num <= version_num <= max_num) or \
                            (not max_num and min_num and min_num <= version_num) or \
                            (not max_num and not min_num):
                        version_branch = branch['autotest_branch']
                        break
                else:
                    # 如果版本范围为空，则表示该OEM所有版本都可以使用该分支
                    version_branch = branch['autotest_branch']
                    break
            else:
                # 如果没有指定的OEM，则判断版本是否在通用的版本范围里，来获取分支
                version_range = branch.get('version_range')
                aklog_printf('%s分支的所有版本范围: %s' % (branch['autotest_branch'], version_range))
                if '-' in version_range:
                    version_range = version_range.replace('--', '-')
                    min_version = version_range.split('-')[0]
                    min_num = float('%s.%03d' % (min_version.split('.')[0], int(min_version.split('.')[-1])))
                    max_version = version_range.split('-')[-1]
                    if max_version:
                        max_num = float('%s.%03d' % (max_version.split('.')[0], int(max_version.split('.')[-1])))
                    else:
                        max_num = 0
                    
                    if (max_num and min_num and min_num <= version_num <= max_num) or \
                            (not max_num and min_num and min_num <= version_num) or \
                            (not max_num and not min_num):
                        version_branch = branch['autotest_branch']
                        break
                else:
                    # 如果版本范围为空，则表示所有版本都可以使用该分支
                    version_branch = branch['autotest_branch']
                    break
        if not version_branch:
            version_branch = model_version_info[model_name]['default_branch']
            aklog_warn('分支未匹配到，使用默认分支: %s' % version_branch)
        else:
            aklog_printf('版本 %s 匹配到的分支: %s' % (firmware_version, version_branch))
        return version_branch
    else:
        aklog_warn(f'版本分支信息缺少 {model_name} 型号，'
                   '请在 libconfig/libconfig_xml/model_version_info/ 目录下添加机型版本分支信息')
        raise ValueError(f'版本分支信息缺少 {model_name} 型号')


def config_parse_sub_version_branch(firmware_version, sub_version_branch_info):
    """有些机型安全版本和非安全版本共用分支，通过子分支版本来区分，根据型号和版本号来解析子分支版本"""
    aklog_printf()
    if not sub_version_branch_info:
        return None
    
    version = firmware_version.split('.')
    oem_id = version[1]
    big_version = version[-2]
    if len(big_version) > 2:
        # 如果大版本号大于100，则当成是拉的分支版本
        big_version = big_version[0:1]
    version_num = '%s.%03d' % (big_version, int(version[-1]))
    version_num = float(version_num)
    
    version_range_name = 'version_range__%s' % oem_id
    version_branch = ''
    for branch in sub_version_branch_info:
        version_range = branch.get(version_range_name)
        if version_range is not None:
            aklog_printf('子分支 %s 的 %s 版本范围: %s' % (branch['sub_version_branch'], oem_id, version_range))
            # 如果有指定OEM的版本范围，则判断版本是否在OEM版本范围里，来获取分支
            if '-' in version_range:
                version_range = version_range.replace('--', '-')
                min_version = version_range.split('-')[0]
                min_num = float('%s.%03d' % (min_version.split('.')[0], int(min_version.split('.')[-1])))
                max_version = version_range.split('-')[-1]
                if max_version:
                    max_num = float('%s.%03d' % (max_version.split('.')[0], int(max_version.split('.')[-1])))
                else:
                    max_num = 0
                
                if (max_num and min_num and min_num <= version_num <= max_num) or \
                        (not max_num and min_num and min_num <= version_num) or \
                        (not max_num and not min_num):
                    version_branch = branch['sub_version_branch']
                    break
            else:
                # 如果版本范围为空，则表示该OEM所有版本都可以使用该分支
                version_branch = branch['sub_version_branch']
                break
        else:
            # 如果没有指定的OEM，则判断版本是否在通用的版本范围里，来获取分支
            version_range = branch.get('version_range')
            aklog_printf('子分支 %s 的所有版本范围: %s' % (branch['sub_version_branch'], version_range))
            if '-' in version_range:
                version_range = version_range.replace('--', '-')
                min_version = version_range.split('-')[0]
                min_num = float('%s.%03d' % (min_version.split('.')[0], int(min_version.split('.')[-1])))
                max_version = version_range.split('-')[-1]
                if max_version:
                    max_num = float('%s.%03d' % (max_version.split('.')[0], int(max_version.split('.')[-1])))
                else:
                    max_num = 0
                
                if (max_num and min_num and min_num <= version_num <= max_num) or \
                        (not max_num and min_num and min_num <= version_num) or \
                        (not max_num and not min_num):
                    version_branch = branch['sub_version_branch']
                    break
            else:
                # 如果版本范围为空，则表示所有版本都可以使用该分支
                version_branch = branch['sub_version_branch']
                break
    if not version_branch:
        version_branch = sub_version_branch_info[0]['sub_version_branch']
        aklog_printf('子分支版本未匹配到，使用第一个版本分支: %s' % version_branch)
    else:
        aklog_printf('匹配到的子分支版本: %s' % version_branch)
    return version_branch


def config_parse_upgrade_cover_data():
    """解析升级覆盖旧版本信息"""
    # 获取当前测试机型使用的分支版本，如果存在子分支，则使用子分支版本
    version_branch = param_get_version_branch()
    upgrade_cover_data = None
    if '.' in version_branch:
        sub_version_branch = version_branch.split('.')[1]
        upgrade_cover_data_name = 'UpgradeCover__%s' % sub_version_branch
        if upgrade_cover_data_name in param_get_excel_data():
            upgrade_cover_data = param_get_excel_data()[upgrade_cover_data_name]
    if not upgrade_cover_data:
        upgrade_cover_data = param_get_excel_data()['UpgradeCover']
    
    # 指定升级次数
    if param_get_upgrade_cover_counts() == 0:
        upgrade_cover_counts = len(upgrade_cover_data)
    else:
        upgrade_cover_counts = min(len(upgrade_cover_data), param_get_upgrade_cover_counts())
    upgrade_cover_data = upgrade_cover_data[0:upgrade_cover_counts]
    return upgrade_cover_data


def config_parse_web_version_branch(model_name, branch):
    """根据机型的版本分支，获取使用的web分支版本"""
    web_version_branch_info = xml_read_sheet_data('%s\\product_oem_config\\web_version_branch_info.xml' % g_config_path)
    for line in web_version_branch_info['web_version_branch_info']:
        if line['model_name'] == model_name:
            for key in line:
                if key == 'model_name':
                    continue
                versions = line[key].split('--')
                print(versions)
                minimum = float(versions[0])
                if len(versions) == 2 and versions[1] != '':
                    maximum = float(versions[1])
                else:
                    maximum = 100
                if minimum <= float(branch) <= maximum:
                    return key
    return 'WEB2_0'


def config_parse_module(file, modules, type_des):
    if not os.access(file, os.F_OK):
        aklog_printf("%s isn't exist" % file)
        return
    if os.path.splitext(file)[1] == '.txt':
        fi = open(file, mode="r", encoding="utf-8")
        if not fi:
            aklog_printf("%s isn't exist" % file)
            return
        
        while True:
            data = fi.readline()
            if not data:
                break
            data = data.strip()
            if data == '' or data[0] == '#':
                continue
            
            key_value = data.split('=')
            if len(key_value) != 2:
                continue
            module_name = key_value[0].strip()
            module_value = key_value[1].strip()
            aklog_printf("n:%s, v:%s :%s" % (module_name, module_value, type_des))
            if module_value == "1":
                modules[module_name] = type_des
            elif module_name in modules:
                del modules[module_name]
        aklog_printf(modules)
    
    elif os.path.splitext(file)[1] == '.xml':
        module_list = xml_parse_module_list(file)['module_list']
        
        # 是否使用套件中的测试用例
        use_suite = '0'
        if 'test_case_suite' in param_get_firmware_info_data() and not param_get_module_list():
            test_case_suite = param_get_firmware_info_data()['test_case_suite'][0]
            use_suite = test_case_suite['use_suite']
        
        if use_suite != '1':  # 如果不使用套件，则使用过滤条件来过滤测试用例，否则先解析所有测试用例，之后再挑选出套件中的用例
            # 获取测试用例过滤条件
            case_type = '0'
            module_priority = 'P2'
            if 'test_case_filter' in param_get_firmware_info_data() and not param_get_module_list():
                test_case_filter = param_get_firmware_info_data()['test_case_filter'][0]
                case_type = test_case_filter['case_type']
                module_priority = test_case_filter['module_priority']
            
            # 过滤用例类型，压测用例或者关键功能用例
            for module_name in module_list.keys():
                if module_list[module_name]['value'] == '1':
                    module_attribute = module_list[module_name]['attribute']
                    if case_type == '1' and module_attribute['KeyFeature'] != '1':
                        continue
                    elif case_type == '2' and module_attribute['StressTest'] != '1':
                        continue
                    elif case_type == '3' and module_attribute['StressTest'] == '1':
                        continue
                    elif case_type == '4' and module_attribute['UpgradeTest'] != '1':
                        continue
                    modules[module_name] = {'model_oem': type_des,
                                            'attribute': module_attribute}
                elif module_name in modules:
                    del modules[module_name]
            
            # 根据模块优先级过滤测试用例
            for module_name in list(modules.keys()):
                if module_priority == 'P0' and modules[module_name]['attribute']['Priority'] != 'P0':
                    del modules[module_name]
                elif module_priority == 'P1' and modules[module_name]['attribute']['Priority'] != 'P0' and \
                        modules[module_name]['attribute']['Priority'] != 'P1':
                    del modules[module_name]
        else:
            # 使用套件用例，先解析所有测试用例，之后再挑选出套件中的用例
            for module_name in list(module_list.keys()):
                if module_list[module_name]['value'] == '1':
                    module_attribute = module_list[module_name]['attribute']
                    modules[module_name] = {'model_oem': type_des,
                                            'attribute': module_attribute}
                    continue
                elif module_name in modules:
                    del modules[module_name]
                    continue
        aklog_printf(modules)


def config_parse(model_name, oem_name, version_branch, modules, modules_file='module_list.xml'):
    """根据机型OEM和版本分支，解析测试用例模块列表"""
    series_products = param_get_seriesproduct_name()
    # if '.' in version_branch:
    #     version_branch = version_branch.split('.')[0]
    aklog_printf("config_parse, series_products : %s, model_name : %s, oem_name : %s, version_branch: %s"
                 % (series_products, model_name, oem_name, version_branch))
    
    # 解析module_list.xml文件获取测试用例模块信息
    if model_name == "unknown":
        aklog_printf("model is error")
        return None, None
    module_list_root_path = config_get_series_module_sub_path(model_name, version_branch, 'ModuleList')
    if not os.path.exists(module_list_root_path):
        module_list_root_path = config_get_series_module_sub_path(model_name, version_branch,
                                                                  'Base', 'ModuleList')
    
    series_path = os.path.join(module_list_root_path, 'NORMAL')
    series_oem_path = os.path.join(module_list_root_path, oem_name)
    model_path = os.path.join(module_list_root_path, model_name, 'NORMAL')
    model_oem_path = os.path.join(module_list_root_path, model_name, oem_name)
    
    series_modules_file = os.path.join(series_path, modules_file)
    series_oem_modules_file = os.path.join(series_oem_path, modules_file)
    model_modules_file = os.path.join(model_path, modules_file)
    model_oem_modules_file = os.path.join(model_oem_path, modules_file)
    
    aklog_printf('config_parse_module %s : %s' % ('series_normal', series_products + '_NORMAL'))
    config_parse_module(series_modules_file, modules, series_products + '_NORMAL')
    
    aklog_printf('config_parse_module %s : %s' % ('series_oem', series_products + '_' + oem_name))
    config_parse_module(series_oem_modules_file, modules, series_products + '_' + oem_name)
    
    aklog_printf('config_parse_module %s : %s' % ('model_normal', model_name + '_NORMAL'))
    config_parse_module(model_modules_file, modules, model_name + '_NORMAL')
    
    aklog_printf('config_parse_module %s : %s' % ('model_oem', model_name + '_' + oem_name))
    config_parse_module(model_oem_modules_file, modules, model_name + '_' + oem_name)
    
    modules = dict(sorted(modules.items(), key=lambda d: d[0]))
    aklog_printf(modules)
    
    # 解析测试套件，不同机型OEM也跟module_list类似，测试套件下的用例会继承覆盖
    series_suite_file = os.path.join(series_path, 'suite_list.xml')
    model_suite_file = os.path.join(model_path, 'suite_list.xml')
    model_oem_suite_file = os.path.join(model_oem_path, 'suite_list.xml')
    
    suite_dict = dict()
    if os.access(series_suite_file, os.F_OK):
        suite_dict.update(xml_parse_suite_list(series_suite_file)['suite_list'])
    
    if os.access(model_suite_file, os.F_OK):
        suite_dict.update(xml_parse_suite_list(model_suite_file)['suite_list'])
    
    if os.access(model_oem_suite_file, os.F_OK):
        suite_dict.update(xml_parse_suite_list(model_oem_suite_file)['suite_list'])
    
    # 解析排除不进行测试的用例，不同机型OEM也跟module_list类似，用例模块下的用例列表会继承覆盖
    series_exclude_case_file = os.path.join(series_path, 'exclude_case_list.xml')
    model_exclude_case_file = os.path.join(model_path, 'exclude_case_list.xml')
    model_oem_exclude_case_file = os.path.join(model_oem_path, 'exclude_case_list.xml')
    
    exclude_case_info = dict()
    if os.access(series_exclude_case_file, os.F_OK):
        series_exclude_case_info = xml_parse_exclude_case_list(series_exclude_case_file)['exclude_case_list']
        exclude_case_info.update(series_exclude_case_info)
    
    if os.access(model_exclude_case_file, os.F_OK):
        model_normal_exclude_case_info = xml_parse_exclude_case_list(model_exclude_case_file)['exclude_case_list']
        exclude_case_info.update(model_normal_exclude_case_info)
    
    if os.access(model_oem_exclude_case_file, os.F_OK):
        model_oem_exclude_case_info = xml_parse_exclude_case_list(model_oem_exclude_case_file)['exclude_case_list']
        exclude_case_info.update(model_oem_exclude_case_info)
    param_put_exclude_case_list(exclude_case_info)
    
    # 如果使用套件，挑选出指定套件的测试用例
    if 'test_case_suite' in param_get_firmware_info_data() and not param_get_module_list():
        test_case_suite = param_get_firmware_info_data()['test_case_suite'][0]  # 获取FirmwareInfo.xml文件的测试套件信息
        use_suite = test_case_suite['use_suite']
        if use_suite == '1':
            suite_list = []
            new_modules = {}
            suites_name = test_case_suite['suite_name']
            suites_name = suites_name.strip()
            if suites_name != '' and suite_dict:
                suites_name = suites_name.replace(',', ';')
                suite_name_list = suites_name.split(';')
                for suite_name in suite_name_list:
                    suite_name = suite_name.strip()
                    if suite_name and suite_name in suite_dict.keys():
                        suite_list.append(suite_dict[suite_name])  # 将每一个测试套件的用例字典添加到suite_list
                        for module in suite_dict[suite_name].keys():
                            if module in modules:  # 如果测试套件的用例名称在前面获取到的所有用例模块里，用新的list存储
                                new_modules[module] = modules[module]
            
            if 'modules_name' in test_case_suite:
                modules_name = test_case_suite['modules_name']
                modules_name = modules_name.strip()
                if modules_name != '':
                    modules_name_list = modules_name.split(';')  # 获取FirmwareInfo.xml文件内的要执行的用例模块名称列表
                    temp_suite_dict = {}
                    for module in modules_name_list:
                        module = module.strip()
                        if not module:
                            continue
                        
                        # 如果FirmwareInfo.xml文件中的要执行的用例名称在前面获取到的所有用例模块里，用新的list存储
                        elif module in modules:
                            new_modules[module] = modules[module]
                            continue
                        
                        # 如果以 # 开头，将该用例模块移除，不进行测试
                        elif module.startswith('#'):
                            module = module.replace('#', '').strip()
                            if module in new_modules:
                                new_modules.pop(module)
                            if module in modules:
                                modules.pop(module)
                            continue
                        
                        # 如果用例模块名称后面带有#和数字，说明要让用例执行指定次数，添加到suite_list里面
                        elif '#' in module:
                            module_name = module.split('#')[0]
                            temp_suite_dict[module_name] = {'CasePriority': 'P2'}
                            if module.split('#')[1].isdigit():
                                TestCounts = int(module.split('#')[1])
                                temp_suite_dict[module_name]['TestCounts'] = TestCounts
                            elif re.compile(r'[dhms]', re.IGNORECASE).search(module.split('#')[1]):
                                TestDuration = module.split('#')[1]  # 测试时长：5d10h
                                temp_suite_dict[module_name]['TestDuration'] = TestDuration
                            new_modules[module_name] = modules[module_name]
                            continue
                        # 如果用例模块名称为json格式，包含一些属性，直接转成suite字典
                        elif module.startswith('{'):
                            module = module.replace("'", '"')
                            suite_info = json_loads_2_dict(module)
                            if isinstance(suite_info, dict):
                                temp_suite_dict.update(suite_info)
                            module_name = list(suite_info.keys())[0]
                            new_modules[module_name] = modules[module_name]
                            continue
                    
                    suite_list.append(temp_suite_dict)
            
            param_put_suite_list(suite_list)
            modules = new_modules
            aklog_printf('suite_list: %r' % suite_list)
    
    aklog_printf('test case modules: %r' % modules)
    return modules


def config_parse_config_module(model_name, oem_name):
    """获取主测设备config_module名称"""
    aklog_printf('config_parse_config_module, model_name: %s, oem_name: %s' % (model_name, oem_name))
    product_line = param_get_product_line_name()
    series_products = param_get_seriesproduct_name()
    
    if product_line:
        # series_module_name = config_get_series_module_name(series_products)
        # version_branch_info = param_get_version_branch_info()
        # version_branch = version_branch_info.get('%s_branch' % series_module_name)
        # if version_branch and '.' in version_branch:
        #     # 分支版本存在小数点，说明该分支版本有子分支版本区分，比如区分安全版本和非安全版本
        #     version_branch = version_branch.split('.')[0]
        # series_root_path = None
        # if product_line and series_module_name and version_branch:
        #     series_root_path = os.path.join(
        #         root_path, 'testcase', 'module', product_line, series_module_name, version_branch, 'Config')
        # if not series_root_path or not os.path.exists(series_root_path):
        series_root_path = os.path.join(g_config_path, product_line, series_products)
        if not os.path.exists(series_root_path):
            series_root_path = os.path.join(g_config_path, series_products)
    else:
        series_root_path = os.path.join(g_config_path, series_products)
    
    series_path = os.path.join(series_root_path, 'NORMAL')
    model_path = os.path.join(series_root_path, model_name, 'NORMAL')
    model_oem_path = os.path.join(series_root_path, model_name, oem_name)
    
    series_config_file = os.path.join(series_path, f'libconfig_{series_products}_NORMAL.py')
    model_config_file = os.path.join(model_path, f'libconfig_{model_name}_NORMAL.py')
    model_oem_config_file = os.path.join(model_oem_path, f'libconfig_{model_name}_{oem_name}.py')
    
    if os.access(model_oem_config_file, os.F_OK):
        config_module = 'config_%s_%s' % (model_name, oem_name)
    elif os.access(model_config_file, os.F_OK):
        config_module = 'config_%s_NORMAL' % model_name
    elif os.access(series_config_file, os.F_OK):
        config_module = 'config_%s_NORMAL' % series_products
    else:
        config_module = 'config_NORMAL'
    
    aklog_printf('config_module: %s' % config_module)
    return config_module


def config_parse_device_config_by_model_and_oem(model_name, oem_name, device_name=''):
    """根据机型OEM获取对应的device config类实例"""
    aklog_debug()
    config_class = None
    last_series_products = None
    if model_name:
        for i in range(10):
            series_products = config_get_series(model_name, index=i)
            if series_products is None:
                series_products = model_name
            if last_series_products == series_products:
                break
            last_series_products = series_products
            product_line = config_get_product_line(series_products)
            aklog_debug(f'series_products: {series_products}, product_line: {product_line}')
            
            if product_line:
                config_root_dir = os.path.join(g_config_path, product_line, series_products)
                config_root_path = 'libconfig.%s.%s' % (product_line, series_products)
                if not os.path.exists(config_root_dir):
                    config_root_path = 'libconfig.%s' % series_products
                    config_root_dir = os.path.join(g_config_path, series_products)
                # 如果config放在module目录下
                # series_module_name = config_get_series_module_name(series_products)
                # version_branch_info = param_get_version_branch_info()
                # if version_branch_info:
                #     version_branch = version_branch_info.get('%s_branch' % series_module_name)
                #     if version_branch:
                #         if '.' in version_branch:
                #             # 分支版本存在小数点，说明该分支版本有子分支版本区分，比如区分安全版本和非安全版本
                #             version_branch = version_branch.split('.')[0]
                #
                #         config_root_dir = ('%s\\testcase\\module\\%s\\%s\\%s\\Config'
                #                            % (root_path, product_line, series_module_name, version_branch))
                #         config_root_path = ('testcase.module.%s.%s.%s.Config'
                #                             % (product_line, series_module_name, version_branch))
                #
                # if not config_root_path or not config_root_dir or not os.path.exists(config_root_dir):
                #     config_root_dir = os.path.join(g_config_path, product_line, series_products)
                #     config_root_path = 'libconfig.%s.%s' % (product_line, series_products)
                #     if not os.path.exists(config_root_dir):
                #         config_root_path = 'libconfig.%s' % series_products
            else:
                config_root_path = 'libconfig.%s' % series_products
                config_root_dir = os.path.join(g_config_path, series_products)
            
            class_name_model_oem = f'config_{model_name}_{oem_name}'
            class_name_model_NORMAL = f'config_{model_name}_NORMAL'
            class_name_series_NORMAL = f'config_{series_products}_NORMAL'
            
            config_model_oem_path = f'{config_root_path}.{model_name}.{oem_name}'
            config_model_NORMAL_path = f'{config_root_path}.{model_name}.NORMAL'
            config_series_NORMAL_path = f'{config_root_path}.NORMAL'
            
            config_init_file = '%s\\__init__.py' % config_root_dir
            if os.path.exists(config_init_file):
                # 存在__init__.py，说明已经将config模块做成package包，可以通过包导入config模块
                def import_config_module(class_name, package=None, print_exception=False):
                    try:
                        tclass = getattr(package, class_name)
                    except Exception as e:
                        if print_exception:
                            aklog_warn('import %s, Fail: %s' % (class_name, e))
                        tclass = None
                    return tclass
                
                base_package = import_module(config_root_path)
                config_class = import_config_module(class_name_model_oem, base_package)
                if not config_class:
                    config_class = import_config_module(class_name_model_NORMAL, base_package)
                    if not config_class:
                        config_class = import_config_module(
                            class_name_series_NORMAL, base_package, print_exception=True)
            else:
                # 在libconfig模块下，不再将模块路径添加到sys.path环境变量
                def import_config_module(module_path, class_name, print_exception=False):
                    try:
                        module_name = 'lib' + class_name
                        base_module = import_module('%s.%s' % (module_path, module_name))
                        tclass = getattr(base_module, class_name)
                    except Exception as e:
                        if print_exception:
                            aklog_warn('import %s, Fail: %s' % (class_name, e))
                        tclass = None
                    return tclass
                
                config_class = import_config_module(config_model_oem_path, class_name_model_oem)
                if not config_class:
                    config_class = import_config_module(config_model_NORMAL_path, class_name_model_NORMAL)
                    if not config_class:
                        config_class = import_config_module(
                            config_series_NORMAL_path, class_name_series_NORMAL, print_exception=True)
            
            if config_class:
                param_put_series_name_info(model_name, series_products)
                break
    
    if not config_class:
        from libconfig.COMMON.libconfig_NORMAL import config_NORMAL
        config_class = config_NORMAL
    
    aklog_info('device_config: %r' % config_class)
    device_config = config_class(device_name)  # 类实例化
    return device_config


def config_parse_device_config(config_module: str, device_name=''):
    """
    获取device config类实例
    config_module: config_PS51_NORMAL
    """
    cuts = config_module.split('_')
    oem_name = cuts[-1]
    model_name = str_get_content_between_two_characters(config_module, 'config_', f'_{oem_name}')
    return config_parse_device_config_by_model_and_oem(model_name, oem_name, device_name)


def config_parse_manual_modules(modules):
    """解析手动测试模块，已弃用"""
    manual_modules_path = '%s\\manual_modules.txt' % g_config_path
    fp = open(manual_modules_path, mode="r", encoding="utf-8")
    case_lines = fp.readlines()
    fp.close()
    
    if case_lines:
        for case_line in case_lines:
            case_line = case_line.strip()
            if not case_line:
                break
            if '#' in case_line:
                continue
            keyvalue = case_line.split('=')
            module_name = keyvalue[0]
            module_value = keyvalue[1]
            modules[module_name] = module_value
    
    modules = dict(sorted(modules.items(), key=lambda d: d[0]))
    aklog_printf(modules)
    # aklog_printf('modules type is : %s' % (type(modules)))
    return modules


def config_parse_manual_cases(test_cases):
    """解析手动测试用例，已弃用"""
    manual_cases_path = '%s\\manual_cases.txt' % g_config_path
    fp = open(manual_cases_path, mode="r", encoding="utf-8")
    case_lines = fp.readlines()
    fp.close()
    
    if case_lines:
        for case_line in case_lines:
            case_line = case_line.strip()
            if not case_line:
                break
            keyvalue = case_line.split('_case.')
            module = __import__('lib' + keyvalue[0])
            tclass = getattr(module, keyvalue[0] + '_case')
            aklog_printf(tclass)
            testcase = tclass(keyvalue[1])
            test_cases.append(testcase)
    aklog_printf('test_cases : %r' % test_cases)
    return test_cases


def config_parse_modules_from_xml(module_list):
    """解析从firmwareInfo.xml文件中获取到的指定的测试用例模块，引用用例模块并获取测试用例名称信息"""
    aklog_printf('config_parse_modules_from_xml: %r' % module_list)
    modules_dict = {}
    if module_list:
        for case in module_list:
            if not case:
                break
            if '_case.' in case:
                keyvalue = case.split('_case.')
                module = __import__('lib' + keyvalue[0])
                test_class = getattr(module, keyvalue[0] + '_case')
                test_class_name = test_class.__name__
                test_class_cases_list = list(
                    filter(lambda m: m.startswith("test_") and callable(getattr(test_class, m)),
                           dir(test_class)))
                
                case_name = keyvalue[1].strip()
                for test_case in test_class_cases_list:
                    if case_name in test_case:
                        if not modules_dict.get(test_class_name):
                            modules_dict[test_class_name] = [test_case]
                        else:
                            modules_dict[test_class_name].append(test_case)
            else:
                keyvalue = case.split('_case')
                module = __import__('lib' + keyvalue[0])
                test_class = getattr(module, keyvalue[0] + '_case')
                test_class_name = test_class.__name__
                test_class_cases_list = list(
                    filter(lambda m: m.startswith("test_") and callable(getattr(test_class, m)),
                           dir(test_class)))
                
                # 排除掉一些指定不测试的用例
                if hasattr(test_class, 'module_name'):
                    module_name = test_class.module_name
                    if module_name in param_get_exclude_case_list():
                        for x in param_get_exclude_case_list()[module_name]:
                            for y in test_class_cases_list[::-1]:  # 移除列表中的元素可以倒序删除
                                if x in y:
                                    test_class_cases_list.remove(y)
                
                modules_dict[test_class_name] = test_class_cases_list
    
    # 对用例进行排序
    for case_class in modules_dict:
        modules_dict[case_class].sort()
    
    aklog_printf('modules_dict : %r' % modules_dict)
    return modules_dict


def config_parse_jenkins_job_module_list(jenkins_job_name):
    """获取jenkins节点用例列表，机型和OEM目录下的jenkins_module_list.xml会替换掉normal下的"""
    aklog_printf()
    try:
        model_name = param_get_model_name()
        oem_name = param_get_oem_name()
        version_branch = param_get_version_branch()
        if '.' in version_branch:
            version_branch = version_branch.split('.')[0]
        
        module_list_root_path = config_get_series_module_sub_path(model_name, version_branch, 'ModuleList')
        if not os.path.exists(module_list_root_path):
            module_list_root_path = config_get_series_module_sub_path(model_name, version_branch,
                                                                      'Base', 'ModuleList')
        
        jenkins_module_list_name = 'module_list__' + jenkins_job_name
        
        series_file = os.path.join(module_list_root_path, 'NORMAL', 'jenkins_module_list.xml')
        model_normal_file = os.path.join(module_list_root_path, model_name, 'NORMAL', 'jenkins_module_list.xml')
        model_oem_file = os.path.join(module_list_root_path, model_name, oem_name, 'jenkins_module_list.xml')
        
        if os.path.exists(model_oem_file):
            jenkins_job_module_dict = xml_parse_module_list(model_oem_file).get(jenkins_module_list_name)
        elif os.path.exists(model_normal_file):
            jenkins_job_module_dict = xml_parse_module_list(model_normal_file).get(jenkins_module_list_name)
        else:
            jenkins_job_module_dict = xml_parse_module_list(series_file).get(jenkins_module_list_name)
        
        jenkins_job_module_list = None
        if jenkins_job_module_dict:
            jenkins_job_module_list = list(jenkins_job_module_dict.keys())
        aklog_printf('%s 节点总用例模块列表: %s' % (jenkins_job_name, jenkins_job_module_list))
        return jenkins_job_module_list
    except:
        aklog_debug(traceback.format_exc())
        return None


def config_parse_jenkins_exec_job_exclude_only_init_case(jenkins_job_name, sub_job_modules_dict):
    """
    解析jenkins执行jib，排除掉只有初始化用例的job
    分布式构建，有些job只分配到一些初始化的用例，那么该job将不执行这个用例
    """
    if not sub_job_modules_dict:
        return sub_job_modules_dict
    modules = param_get_modules()
    series_products = param_get_seriesproduct_name()
    model_name = param_get_model_name()
    class_name_list = list(sub_job_modules_dict.keys())
    flag = True
    for class_name in class_name_list:
        if series_products in class_name:
            module_name = class_name.split('_' + series_products)[0]
        elif model_name in class_name:
            module_name = class_name.split('_' + model_name)[0]
        else:
            module_name = None
        # 判断是否存在非Init用例
        if module_name and module_name in modules:
            if modules[module_name]['attribute'].get('Init') is None:
                flag = False
                break
    if flag:
        aklog_info('当前job %s 只分配到Init用例，将不执行这个用例' % jenkins_job_name)
        return None
    else:
        return sub_job_modules_dict


def config_parse_jenkins_module_dict(jenkins_job_name, module_dict: dict):
    """从已经解析出来的module dict获取用例名称列表，用来匹配Jenkins节点下的用例名称列表"""
    aklog_printf('config_parse_jenkins_module_dict: %s' % jenkins_job_name)
    jenkins_job_module_list = config_parse_jenkins_job_module_list(jenkins_job_name)
    new_module_list = dict()
    if jenkins_job_module_list:
        series_products = param_get_seriesproduct_name()
        model_name = param_get_model_name()
        class_name_list = list(module_dict.keys())
        for class_name in class_name_list:
            if series_products in class_name:
                module_name = class_name.split('_' + series_products)[0]
            elif model_name in class_name:
                module_name = class_name.split('_' + model_name)[0]
            else:
                module_name = None
            
            if module_name and module_name in jenkins_job_module_list:
                new_module_list[class_name] = module_dict[class_name]
    
    aklog_printf('%s 节点执行的用例模块列表: %s' % (jenkins_job_name, new_module_list))
    return new_module_list


def config_parse_element_info(element_info_file, series_products, model_name, oem_name):
    """根据机型OEM解析设备界面或web元素信息"""
    aklog_printf('config_parse_element_info, element_info_file: %s, series_products: %s, model_name: %s, oem_name: %s'
                 % (element_info_file, series_products, model_name, oem_name))
    series_path = '%s\\%s\\%s' % (g_config_path, series_products, 'NORMAL')
    model_path = '%s\\%s\\%s\\%s' % (g_config_path, series_products, model_name, 'NORMAL')
    model_oem_path = '%s\\%s\\%s\\%s' % (g_config_path, series_products, model_name, oem_name)
    common_path = '%s\\%s' % (g_config_path, 'COMMON')
    
    series_file = os.path.join(series_path, element_info_file)
    model_file = os.path.join(model_path, element_info_file)
    model_oem_file = os.path.join(model_oem_path, element_info_file)
    common_file = os.path.join(common_path, element_info_file)
    element_info_type = os.path.splitext(element_info_file)[0]
    
    if os.access(model_oem_file, os.F_OK):
        aklog_printf('model_oem_file: %s' % model_oem_file)
        model_oem_element_info = xml_parse_element_info(model_oem_file)
    else:
        model_oem_element_info = {}
    
    if os.access(model_file, os.F_OK):
        aklog_printf('model_file: %s' % model_file)
        model_element_info = xml_parse_element_info(model_file)
    else:
        model_element_info = {}
    
    if os.access(series_file, os.F_OK):
        aklog_printf('series_file: %s' % series_file)
        series_element_info = xml_parse_element_info(series_file)
    else:
        series_element_info = {}
    
    if os.access(common_file, os.F_OK):
        aklog_printf('common_file: %s' % common_file)
        common_element_info = xml_parse_element_info(common_file)
    else:
        common_element_info = {}
    
    element_info = {}
    element_info.update(common_element_info)
    element_info.update(series_element_info)
    element_info.update(model_element_info)
    element_info.update(model_oem_element_info)
    aklog_printf('%s: %r' % (element_info_type, element_info))
    return element_info


def config_parse_akubela_cloud_interface_info_from_xml(version_branch, printinfo=False):
    """解析AkubelaCloud接口信息"""
    aklog_printf()
    interface_info_type = 'akubela_cloud_interface_info'
    interface_info_file = 'akubela_cloud_interface_info.xml'
    model_name = 'AKUBELACLOUD'
    interface_info_path = config_get_series_module_sub_path(model_name, version_branch, 'Base', 'InterfaceInfo')
    
    series_file = os.path.join(interface_info_path, 'NORMAL', interface_info_file)
    
    if os.access(series_file, os.F_OK):
        aklog_printf('series_file: %s' % series_file)
        series_interface_info = xml_parse_element_info(series_file)
    else:
        series_interface_info = {}
    
    interface_info = {}
    interface_info.update(series_interface_info)
    if printinfo:
        aklog_printf('%s: %r' % (interface_info_type, interface_info))
    return interface_info


def config_parse_ui_element_info_from_xml(model_name, oem_name, version_branch, printinfo=False):
    """根据机型OEM和分支版本，解析UI界面元素xml文件信息"""
    aklog_printf()
    element_info_type = 'ui_element_info'
    element_info_file = 'ui_element_info.xml'
    element_info_root_path = config_get_series_module_sub_path(model_name, version_branch, 'Base', 'ElementInfo')
    if not os.path.exists(element_info_root_path):
        element_info_root_path = config_get_series_module_sub_path(model_name, version_branch,
                                                                   'Base', 'ModuleList')
    
    series_file = os.path.join(element_info_root_path, 'NORMAL', element_info_file)
    model_file = os.path.join(element_info_root_path, model_name, 'NORMAL', element_info_file)
    model_oem_file = os.path.join(element_info_root_path, model_name, oem_name, element_info_file)
    
    if os.access(model_oem_file, os.F_OK):
        aklog_printf('model_oem_file: %s' % model_oem_file)
        model_oem_element_info = xml_parse_element_info(model_oem_file)
    else:
        model_oem_element_info = {}
    
    if os.access(model_file, os.F_OK):
        aklog_printf('model_file: %s' % model_file)
        model_element_info = xml_parse_element_info(model_file)
    else:
        model_element_info = {}
    
    if os.access(series_file, os.F_OK):
        aklog_printf('series_file: %s' % series_file)
        series_element_info = xml_parse_element_info(series_file)
    else:
        series_element_info = {}
    
    element_info = {}
    element_info.update(series_element_info)
    element_info.update(model_element_info)
    element_info.update(model_oem_element_info)
    if printinfo:
        aklog_printf('%s: %r' % (element_info_type, element_info))
    return element_info


def config_parse_web_element_info_from_xml(model_name, oem_name, version_branch, web_branch,
                                           element_info_type='web_element_info', printinfo=False):
    """
    根据机型OEM和分支版本，解析WEB界面元素xml文件信息
    Args:
        model_name (str):
        oem_name (str):
        version_branch (str):
        web_branch (str):
        element_info_type (str):
        printinfo (bool):
    """
    aklog_printf()
    element_info_file = element_info_type + '.xml'
    common_path = os.path.join(g_common_element_info_path, element_info_type, web_branch, 'NORMAL')
    common_file = os.path.join(common_path, element_info_file)
    
    element_info_root_path = config_get_series_module_sub_path(model_name, version_branch, 'Base', 'ElementInfo')
    if not os.path.exists(element_info_root_path):
        element_info_root_path = config_get_series_module_sub_path(model_name, version_branch,
                                                                   'Base', 'ModuleList')
    
    series_file = os.path.join(element_info_root_path, 'NORMAL', element_info_file)
    model_file = os.path.join(element_info_root_path, model_name, 'NORMAL', element_info_file)
    model_oem_file = os.path.join(element_info_root_path, model_name, oem_name, element_info_file)
    
    if os.access(model_oem_file, os.F_OK):
        aklog_printf('model_oem_file: %s' % model_oem_file)
        model_oem_element_info = xml_parse_element_info(model_oem_file)
    else:
        model_oem_element_info = {}
    
    if os.access(model_file, os.F_OK):
        aklog_printf('model_file: %s' % model_file)
        model_element_info = xml_parse_element_info(model_file)
    else:
        model_element_info = {}
    
    if os.access(series_file, os.F_OK):
        aklog_printf('series_file: %s' % series_file)
        series_element_info = xml_parse_element_info(series_file)
    else:
        series_element_info = {}
    
    if os.access(common_file, os.F_OK):
        aklog_printf('common_file: %s' % common_file)
        common_element_info = xml_parse_element_info(common_file)
    else:
        common_element_info = {}
    
    element_info = {}
    element_info.update(common_element_info)
    element_info.update(series_element_info)
    element_info.update(model_element_info)
    element_info.update(model_oem_element_info)
    if printinfo:
        aklog_printf('%s: %r' % (element_info_type, element_info))
    return element_info


def config_parse_normal_web_element_info_from_xml(web_branch, element_info_type='web_element_info', printinfo=False):
    """
    根据机型OEM和分支版本，解析通用WEB界面元素xml文件信息
    Args:
        web_branch (str):
        element_info_type (str):
        printinfo (bool):
    """
    aklog_printf()
    element_info_file = element_info_type + '.xml'
    common_path = os.path.join(g_common_element_info_path, element_info_type, web_branch, 'NORMAL')
    common_file = os.path.join(common_path, element_info_file)
    
    if os.access(common_file, os.F_OK):
        aklog_printf('common_file: %s' % common_file)
        common_element_info = xml_parse_element_info(common_file)
    else:
        common_element_info = {}
    
    element_info = {}
    element_info.update(common_element_info)
    if printinfo:
        aklog_printf('%s: %r' % (element_info_type, element_info))
    return element_info


def config_parse_common_web_interface_info_from_ini(
        web_branch, interface_info_type='web_interface_info', printinfo=False):
    """
    根据机型OEM和分支版本，解析通用WEB接口配置信息
    Args:
        web_branch (str):
        interface_info_type (str):
        printinfo (bool):
    """
    aklog_printf()
    interface_info_file = interface_info_type + '.ini'
    common_path = os.path.join(g_common_element_info_path, interface_info_type, web_branch, 'NORMAL')
    common_file = os.path.join(common_path, interface_info_file)
    
    if os.access(common_file, os.F_OK):
        aklog_printf('common_web_interface_info_file: %s' % common_file)
        readconfig = ReadConfig(common_file)
        all_config_data = readconfig.get_config_data()
    else:
        all_config_data = {}
    
    interface_info = {}
    interface_info.update(all_config_data)
    if printinfo:
        aklog_printf('%s: %r' % (interface_info_type, interface_info))
    return interface_info


def config_parse_web_interface_info_from_ini(model_name, oem_name, version_branch, web_branch,
                                             interface_info_type='web_interface_info', printinfo=False):
    """
    根据机型OEM和分支版本，解析WEB接口配置信息
    Args:
        model_name (str):
        oem_name (str):
        version_branch (str):
        web_branch (str):
        interface_info_type (str):
        printinfo (bool):
    """
    aklog_printf()
    interface_info_file = interface_info_type + '.ini'
    common_path = os.path.join(g_common_element_info_path, interface_info_type, web_branch, 'NORMAL')
    common_file = os.path.join(common_path, interface_info_file)
    
    interface_info_root_path = config_get_series_module_sub_path(model_name, version_branch,
                                                                 'Base', 'ElementInfo')
    if not os.path.exists(interface_info_root_path):
        interface_info_root_path = config_get_series_module_sub_path(model_name, version_branch,
                                                                     'Base', 'ModuleList')
    
    series_file = os.path.join(interface_info_root_path, 'NORMAL', interface_info_file)
    model_file = os.path.join(interface_info_root_path, model_name, 'NORMAL', interface_info_file)
    model_oem_file = os.path.join(interface_info_root_path, model_name, oem_name, interface_info_file)
    
    if os.access(model_oem_file, os.F_OK):
        aklog_printf('model_oem_file: %s' % model_oem_file)
        readconfig = ReadConfig(model_oem_file)
        model_oem_interface_info = readconfig.get_config_data()
    else:
        model_oem_interface_info = {}
    
    if os.access(model_file, os.F_OK):
        aklog_printf('model_file: %s' % model_file)
        readconfig = ReadConfig(model_file)
        model_interface_info = readconfig.get_config_data()
    else:
        model_interface_info = {}
    
    if os.access(series_file, os.F_OK):
        aklog_printf('series_file: %s' % series_file)
        readconfig = ReadConfig(series_file)
        series_interface_info = readconfig.get_config_data()
    
    else:
        series_interface_info = {}
    
    if os.access(common_file, os.F_OK):
        aklog_printf('common_file: %s' % common_file)
        readconfig = ReadConfig(common_file)
        common_interface_info = readconfig.get_config_data()
    else:
        common_interface_info = {}
    
    interface_info = {}
    # 要保证通用的接口信息分类是最全的：web_config_info、enable_option、register_status_option、transport_type_option
    interface_info.update(common_interface_info)
    for key in interface_info:
        if series_interface_info.get(key) is not None:
            interface_info[key].update(series_interface_info[key])
        if model_interface_info.get(key) is not None:
            interface_info[key].update(model_interface_info[key])
        if model_oem_interface_info.get(key) is not None:
            interface_info[key].update(model_oem_interface_info[key])
    if printinfo:
        aklog_printf('%s: %r' % (interface_info_type, interface_info))
    return interface_info


def config_parse_web_interface_info_from_yaml(model_name, oem_name, web_branch,
                                              interface_info_type='web_interface_info'):
    """加载web页面配置信息"""
    aklog_debug()

    def merge_dict(base: dict, override: dict) -> dict:
        """递归合并字典，override优先"""
        result = base.copy()
        for k, v in override.items():
            if isinstance(v, dict) and k in result and isinstance(result[k], dict):
                result[k] = merge_dict(result[k], v)
            else:
                result[k] = v
        return result

    interface_info_file = interface_info_type + '.yaml'
    config_path = os.path.join(
        g_common_element_info_path, interface_info_type, web_branch, 'NORMAL', interface_info_file)
    series_name = config_get_series(model_name)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    config_type = config.get('config_type', {})
    config_type_list = config_type.split(',')
    all_data = {}
    for _type in config_type_list:
        # 不同机型不同OEM版本继承覆盖
        base = config.get(f"{_type}", {})
        series_override = config.get(series_name, {}).get('NORMAL', {}).get(_type, {})
        series_data = merge_dict(base, series_override)
        model_normal_override = config.get(series_name, {}).get(model_name, {}).get('NORMAL', {}).get(_type, {})
        model_normal_data = merge_dict(series_data, model_normal_override)
        model_oem_override = config.get(series_name, {}).get(model_name, {}).get(oem_name, {}).get(_type, {})
        model_oem_data = merge_dict(model_normal_data, model_oem_override)
        all_data[_type] = model_oem_data
    return all_data


def config_get_value_from_ini_file(section, option):
    """获取config.ini文件中属性值"""
    config_ini_data = param_get_config_ini_data()
    if config_ini_data == 'unknown':
        config_ini_data = config_get_all_data_from_ini_file()
        param_put_config_ini_data(config_ini_data)
    try:
        value = config_ini_data[section].get(option)
    except:
        aklog_printf(traceback.format_exc())
        value = None
    aklog_printf('config_get_value_from_ini_file, [%s] %s = %s' % (section, option, value))
    return value


def config_get_all_data_from_ini_file():
    """获取config.ini文件所有信息"""
    aklog_printf('config_get_all_data_from_ini_file')
    config_ini_file = param_get_config_ini_file()
    if config_ini_file:
        config_file = os.path.join(g_config_path, config_ini_file)
        if not os.path.exists(config_file):
            aklog_printf('配置文件 %s 未找到，将使用默认的配置文件: %s' % (config_ini_file, g_config_ini_file))
            config_file = os.path.join(g_config_path, g_config_ini_file)
    else:
        config_file = os.path.join(g_config_path, g_config_ini_file)
    readconfig = ReadConfig(config_file)
    all_config_data = readconfig.get_config_data()
    del readconfig
    aklog_printf('config.ini all data: %r' % all_config_data)
    return all_config_data


def config_get_ini_data_and_set_params():
    """获取config.ini文件所有信息，并设置部分参数强制开启或关闭"""
    aklog_printf('config_get_ini_data_and_set_params')
    config_ini_data = param_get_config_ini_data()
    if config_ini_data == 'unknown':
        config_ini_data = config_get_all_data_from_ini_file()
        param_put_config_ini_data(config_ini_data)
    if config_ini_data['config']['browser_headless_enable'] is not None:
        param_put_browser_headless_enable(config_ini_data['config']['browser_headless_enable'])
    if config_ini_data['config']['send_test_results_summary_enable'] is not None:
        param_put_send_test_results_summary_enable(config_ini_data['config']['send_test_results_summary_enable'])
    if config_ini_data['config']['send_email_enable'] is not None:
        param_put_send_email_state(config_ini_data['config']['send_email_enable'])
    if config_ini_data['config'].get('pause_during_nap_time_enable') is not None:
        param_put_pause_during_nap_time_enable(config_ini_data['config']['pause_during_nap_time_enable'])
    if config_ini_data['config'].get('test_case_balance_enable') is not None:
        param_put_test_case_balance_enable(config_ini_data['config']['test_case_balance_enable'])
    if config_ini_data['config'].get('browser_in_second_screen') is not None:
        param_put_browser_in_second_screen(config_ini_data['config']['browser_in_second_screen'])


def config_get_appium_port():
    """从config.ini指定的appium开始端口分配未被使用的端口，端口为奇数，对应的bootstrap port加1"""
    if g_appium_ports:
        local_port = g_appium_ports[-1] + 2
        # start_local_port = g_appium_ports[0]
    else:
        config_ini_data = param_get_config_ini_data()
        if config_ini_data == 'unknown':
            config_ini_data = config_get_all_data_from_ini_file()
            param_put_config_ini_data(config_ini_data)
        start_local_port = int(config_ini_data['environment']['appium_start_port'])
        if (start_local_port % 2) == 0:
            # 如果指定的开始端口为偶数，那么分配开始端口为下一个奇数
            start_local_port += 1
        local_port = start_local_port
    # 由于结束测试时没有关闭掉node进程，没有释放掉端口，如果判断端口是否被占用，就会一直被占用
    # while local_port < start_local_port + 100:
    #     ret = sub_process_get_output('netstat -ano | findstr ":%s " | findstr "LISTENING"' % local_port)
    #     if ret:
    #         local_port += 2
    #     else:
    #         break
    g_appium_ports.append(local_port)
    return str(local_port)


def config_get_wda_port():
    """从config.ini指定的wda开始端口分配未被使用的端口，端口为奇数，对应的bootstrap port加1"""
    if g_wda_ports:
        local_port = g_wda_ports[-1] + 2
        # start_local_port = g_wda_ports[0]
    else:
        config_ini_data = param_get_config_ini_data()
        if config_ini_data == 'unknown':
            config_ini_data = config_get_all_data_from_ini_file()
            param_put_config_ini_data(config_ini_data)
        start_local_port = int(config_ini_data['environment']['wda_start_port'])
        if (start_local_port % 2) == 0:
            # 如果指定的开始端口为偶数，那么分配开始端口为下一个奇数
            start_local_port += 1
        local_port = start_local_port
    g_wda_ports.append(local_port)
    return str(local_port)


def config_get_uiautomator2_system_port():
    """从config.ini指定的system_port开始端口，然后检查端口是否被占用，并把使用的端口加入到全局变量列表"""
    if g_uiautomator2_system_ports:
        system_port = g_uiautomator2_system_ports[-1] + 1
        start_uiautomator2_system_port = g_uiautomator2_system_ports[0]
    else:
        config_ini_data = param_get_config_ini_data()
        if config_ini_data == 'unknown':
            config_ini_data = config_get_all_data_from_ini_file()
            param_put_config_ini_data(config_ini_data)
        start_uiautomator2_system_port = int(config_ini_data['environment']['uiautomator2_system_start_port'])
        system_port = start_uiautomator2_system_port
    while system_port < start_uiautomator2_system_port + 50:
        ret = sub_process_get_output('netstat -ano | findstr ":%s " | findstr "LISTENING"' % system_port)
        if ret:
            system_port += 1
        else:
            break
    g_uiautomator2_system_ports.append(system_port)
    return system_port


def config_get_ws_server_port(cur_port=None):
    """从config.ini指定的网关模拟器ws服务开始端口，然后检查端口是否被占用，并把使用的端口加入到全局变量列表"""
    if cur_port and not sub_process_get_output('netstat -ano | findstr ":%s " | findstr "LISTENING"' % cur_port):
        return cur_port
    if g_ws_server_ports:
        ws_server_port = g_ws_server_ports[-1] + 1
        ws_server_start_port = g_ws_server_ports[0]
    else:
        config_ini_data = param_get_config_ini_data()
        if config_ini_data == 'unknown':
            config_ini_data = config_get_all_data_from_ini_file()
            param_put_config_ini_data(config_ini_data)
        ws_server_start_port = int(config_ini_data['environment']['ws_server_start_port'])
        ws_server_port = ws_server_start_port
    while ws_server_port < ws_server_start_port + 100:
        ret = sub_process_get_output('netstat -ano | findstr ":%s " | findstr "LISTENING"' % ws_server_port)
        if ret:
            ws_server_port += 1
        else:
            break
    g_ws_server_ports.append(ws_server_port)
    return ws_server_port


def config_set_stop_exec_enable(temp_ini_file=None):
    if param_get_stop_exec_enable():
        aklog_warn('准备停止执行')
        return True
    if param_get_stop_process_event() and param_get_stop_process_event().is_set():
        aklog_warn('准备停止进程，退出执行')
        param_put_stop_exec_enable(True)
        return True
    if not temp_ini_file:
        temp_ini_file = param_get_temp_ini_file()
    if not temp_ini_file:
        return False
    readconfig = ReadConfig(temp_ini_file)
    stop_exec_enable = readconfig.get_value('config', 'stop_exec_enable')
    if stop_exec_enable is True:
        aklog_warn('temp.ini被设置手动停止，准备停止执行')
        param_put_stop_exec_enable(True)
        return True
    return False


def config_modify_temp_ini(temp_ini_file=None, **kwargs):
    """修改temp.ini文件"""
    if not temp_ini_file:
        temp_ini_file = param_get_temp_ini_file()
    if not temp_ini_file:
        return
    readconfig = ReadConfig(temp_ini_file)
    for key in kwargs:
        readconfig.modify_config('config', key, kwargs['key'])
    readconfig.write_config()


def config_add_exclusion_ip_to_temp_ini(*ips):
    """将排除IP添加到temp.ini文件"""
    aklog_info()
    if not ips:
        return
    temp_ini_file = os.path.join(g_config_path, 'temp.ini')
    readconfig = ReadConfig(temp_ini_file)
    cur_ip_temp_exclusion_range = readconfig.get_value('config', 'ip_temp_exclusion_range')
    cur_ip_temp_exclusion_list = []
    if cur_ip_temp_exclusion_range and isinstance(cur_ip_temp_exclusion_range, str):
        cur_ip_temp_list = cur_ip_temp_exclusion_range.split(',')
        for x in cur_ip_temp_list:
            x = x.strip('"').strip()
            cur_ip_temp_exclusion_list.append(x)
    elif isinstance(cur_ip_temp_exclusion_range, list):
        cur_ip_temp_exclusion_list = cur_ip_temp_exclusion_range
    
    for ip in ips:
        ip_4 = ip.split('.')[-1]
        if ip_4 not in cur_ip_temp_exclusion_list:
            cur_ip_temp_exclusion_list.append(ip_4)
    readconfig.modify_config('config', 'ip_temp_exclusion_range', cur_ip_temp_exclusion_list)
    readconfig.write_config()


def config_del_exclusion_ip_from_temp_ini(*ips):
    aklog_info()
    if not ips:
        return
    temp_ini_file = os.path.join(g_config_path, 'temp.ini')
    readconfig = ReadConfig(temp_ini_file)
    cur_ip_temp_exclusion_range = readconfig.get_value('config', 'ip_temp_exclusion_range')
    cur_ip_temp_exclusion_list = []
    if cur_ip_temp_exclusion_range and isinstance(cur_ip_temp_exclusion_range, str):
        cur_ip_temp_list = cur_ip_temp_exclusion_range.split(',')
        for x in cur_ip_temp_list:
            x = x.strip('"').strip()
            cur_ip_temp_exclusion_list.append(x)
    elif isinstance(cur_ip_temp_exclusion_range, list):
        cur_ip_temp_exclusion_list = cur_ip_temp_exclusion_range
    
    for ip in ips:
        ip_4 = ip.split('.')[-1]
        if ip_4 in cur_ip_temp_exclusion_list:
            cur_ip_temp_exclusion_list.remove(ip_4)
    readconfig.modify_config('config', 'ip_temp_exclusion_range', cur_ip_temp_exclusion_list)
    readconfig.write_config()


def config_set_app_info_before_test(master_name):
    """
    检查device_info中是否存在app的信息，如果没有，则从勾选列表中获取，
    只适用于扫描测试
    """
    aklog_info()
    # 执行app用例前，检查当前使用的app是否仍在线以及仍被勾选，则继续执行。如果不在勾选列表内，则将APP的状态改为unused，并且移除testdata中的app device_info
    devices_info = param_get_excel_data()['device_info']
    app_info_file = r'%s\testcase\apps\ScanNetworkAutoTest\device_info.xml' % root_path
    selected_app_info = xml_read_sheet_data(app_info_file)
    aklog_info(selected_app_info)
    checked_app_list = {}
    for app_info in selected_app_info['device_info']:
        app_name = app_info['device_name']
        checked_app_list[app_name] = app_info
    
    for device_info in devices_info:
        device_name = device_info['device_name']
        if 'app_' in device_name and device_info.get('status') == 'used':
            if device_name not in checked_app_list:
                param_get_excel_data()['device_info'].remove(device_info)
                aklog_info('device_info移除不在勾选列表内的APP信息')
                return None
            else:
                aklog_info(device_info)
                return device_info
    # 获取已勾选的app列表，看是否有存在已勾选但未使用的APP，然后将app的device_info加入进来测试。
    for app_name in checked_app_list:
        app_info = checked_app_list[app_name]
        if app_info.get('status') == 'unused':
            app_info['status'] = 'used'
            app_info['for_master_name'] = master_name
            param_get_excel_data()['device_info'].append(app_info)
            # 将for_master_name写入到device_info.xml文件中，并修改xml中的status
            xml_modify_specify_line_attribute(
                app_info_file, 'device_info', 'device_name', app_name, for_master_name=master_name, status='used')
            app_info_list = xml_read_sheet_data(app_info_file)['device_info']  # list类型
            aklog_info(app_info_list)
            return app_info
    aklog_info('未找到可以测试的手机APP')
    return None


def config_get_and_call_nested_attribute(attr_path, context=None, *args, **kwargs):
    """
    获取嵌套属性或调用嵌套方法。
    参数:
        attr_path -- 属性路径字符串，如 "self.is_not_multi_panel" 或 "control_base.is_not_multi_panel"
        context -- 上下文对象，若为None则在全局查找
        *args, **kwargs -- 传递给最终方法的参数
    返回:
        属性值或方法调用结果，路径无效返回 None
    """
    parts = attr_path.split('.')
    if not parts:
        aklog_warn("属性路径无效")
        return None

    # 处理 'cls.xxx' 或 'self.xxx'
    if parts[0] in ('cls', 'self'):
        if context is None:
            aklog_warn(f"{attr_path} 为类/实例方法，但未提供 context")
            return None
        obj = context
        attrs = parts[1:]
    else:
        # 处理全局或其他对象
        obj_name = parts[0]
        try:
            obj = globals()[obj_name] if context is None else getattr(context, obj_name)
        except (KeyError, AttributeError):
            aklog_warn(f"对象 {obj_name} 不存在")
            return None
        attrs = parts[1:]

    # 递归获取属性
    for attr in attrs:
        if hasattr(obj, attr):
            obj = getattr(obj, attr)
            # 不是最后一个属性且是可调用对象时调用
            if callable(obj) and attr != attrs[-1]:
                obj = obj()
        else:
            aklog_warn(f"属性路径 {attr_path} 无效，缺失 {attr}")
            return None

    # 最终对象可调用则调用
    return obj(*args, **kwargs) if callable(obj) else obj


def config_adb_get_android_apk_version(device_id, package_name):
    """adb方式获取安卓应用的版本号"""
    if not device_id:
        return None
    adb_devices_command = f'adb devices | findstr "{device_id}"'
    devices = sub_process_get_output(adb_devices_command)
    pattern = r'%s\s+device' % re.escape(device_id)
    if not devices or not re.search(pattern, devices):
        return None
    cmd = f'adb -s {device_id} shell dumpsys package {package_name} | findstr "versionName"'
    out = sub_process_get_output(cmd)
    if out and 'versionName=' in out:
        version = out.split('=')[1].strip()
        return version
    return None


if __name__ == '__main__':
    print('测试代码')
    all_data = config_parse_web_interface_info_from_yaml(
        'PS51', 'AKUBELA', 'PANELWEB1_0')
    print(all_data)
