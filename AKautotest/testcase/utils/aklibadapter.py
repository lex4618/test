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
import random
from importlib import import_module
from itertools import permutations


# region 用例适配

class module_case_adapter(object):
    """模块调用适配"""

    # def __init__(self, modules):
    #     self.modules = modules

    @staticmethod
    def creat_case(module_name):
        """根据模块名称获取并导入测试用例类，弃用"""
        aklog_printf("init module_case_adapter")
        modules = param_get_modules()
        if type(modules[module_name]) is dict:
            module = __import__('lib' + module_name + '_' + modules[module_name]['model_oem'])
            aklog_printf("%s %s" % (module_name, modules[module_name]['model_oem']))
            tclass = getattr(module, module_name + '_' + modules[module_name]['model_oem'] + '_case')
            aklog_printf(tclass)
            return tclass
        else:
            module = __import__('lib' + module_name + '_' + modules[module_name])
            aklog_printf(module)
            aklog_printf("%s %s" % (module_name, modules[module_name]))
            tclass = getattr(module, module_name + '_' + modules[module_name] + '_case')
            aklog_printf(tclass)
            return tclass

    @staticmethod
    def create_test_class():
        """创建测试用例类列表，弃用"""
        test_class_list = []
        modules = param_get_modules()
        for module_name in modules.keys():
            if type(modules[module_name]) is dict:
                aklog_printf("key:%s, value:%s" % (module_name, modules[module_name]['model_oem']))
                try:
                    module = __import__('lib' + module_name + '_' + modules[module_name]['model_oem'])
                except:
                    aklog_printf('%s 用例不存在' % module_name)
                    aklog_printf(traceback.format_exc())
                    continue
                # aklog_printf(module)
                # aklog_printf("%s %s" % (module_name, modules[module_name]['model_oem']))
                test_class = getattr(module, module_name + '_' + modules[module_name]['model_oem'] + '_case')
                # aklog_printf(test_class)
                test_class_list.append(test_class)
            else:
                aklog_printf("key:%s, value:%s" % (module_name, modules[module_name]))
                try:
                    module = __import__('lib' + module_name + '_' + modules[module_name])
                except:
                    aklog_printf('%s 用例不存在' % module_name)
                    continue
                # aklog_printf(module)
                # aklog_printf("%s %s" % (module_name, modules[module_name]))
                test_class = getattr(module, module_name + '_' + modules[module_name] + '_case')
                # aklog_printf(test_class)
                test_class_list.append(test_class)
        return test_class_list

    @staticmethod
    def create_test_case_dict():
        """创建测试用例类字典"""
        test_class_dict = {}
        modules = param_get_modules()
        master_device_config = None
        master_model = None
        master_models = None
        if param_get_master_model() and 'SOLUTION' not in param_get_master_model():
            if '+' in param_get_master_model():
                master_models = param_get_master_model().split('+')
                master_model = master_models[0]
            else:
                master_model = param_get_master_model()
            master_device_config = config_parse_device_config_by_model_and_oem(
                master_model, 'NORMAL')

        for module_name in modules.keys():
            if isinstance(modules[module_name], dict):
                aklog_printf("key:%s, value:%s" % (module_name, modules[module_name]['model_oem']))
                try:
                    module = __import__('lib' + module_name + '_' + modules[module_name]['model_oem'])
                except:
                    aklog_printf('%s 用例模块导入失败' % module_name)
                    aklog_printf(traceback.format_exc())
                    continue
                # aklog_printf(module)
                # aklog_printf("%s %s" % (module_name, modules[module_name]['model_oem']))
                test_class = getattr(module, module_name + '_' + modules[module_name]['model_oem'] + '_case')
                # aklog_printf(test_class)
                test_class_name = test_class.__name__

                # 遍历获取用例类的用例列表
                test_class_cases_list = []

                for x in dir(test_class):
                    if x.startswith("__") or not x.startswith("test_") or not callable(getattr(test_class, x)):
                        continue
                    instance_list = getattr(getattr(test_class, x), '__unittest_exec_instance_list__', None)
                    if not instance_list:
                        test_class_cases_list.append(x)
                        continue
                    # 检查用例的设备需求数量是否满足
                    check_pass_count = 0
                    for instance_name in instance_list:
                        if '*' in instance_name:
                            instance_name, instance_count = instance_name.split('*')
                            instance_count = int(instance_count)
                        else:
                            instance_count = 1
                        for _type, count_info in param_get_device_count_info().items():
                            if not count_info.get(instance_name):
                                continue
                            if count_info.get(instance_name) >= instance_count:
                                check_pass_count += 1
                                break
                    if param_get_check_device_count_enable() and check_pass_count != len(instance_list):
                        continue

                    if (not master_model or 'SOLUTION' in master_model) and not master_device_config:
                        test_class_cases_list.append(x)
                        continue
                    else:
                        master_product_type = master_device_config.get_product_type_name()
                        master_series = master_device_config.get_series_product_name()
                        if ((master_model in instance_list)
                                or (master_models and any(model in instance_list for model in master_models))
                                or (master_series and master_series != 'COMMON' and master_series in instance_list)
                                or (master_product_type and master_product_type in instance_list)):
                            test_class_cases_list.append(x)
                            continue
                if not test_class_cases_list:
                    continue

                # 根据优先级过滤测试用例
                case_priority = 'P2'
                use_suite = '0'

                if 'test_case_suite' in param_get_firmware_info_data():
                    test_case_suite = param_get_firmware_info_data()['test_case_suite'][0]
                    use_suite = test_case_suite['use_suite']

                if use_suite == '1':
                    for module_info in param_get_suite_list():
                        if module_name in module_info:
                            case_priority = module_info[module_name]['CasePriority']
                            break
                elif 'test_case_filter' in param_get_firmware_info_data():
                    test_case_filter = param_get_firmware_info_data()['test_case_filter'][0]
                    case_priority = test_case_filter['case_priority']

                if case_priority != 'P2':
                    # 过滤用例模块内用例的优先级，P2表示P0+P1+P2，P1表示P0+P1
                    for case in test_class_cases_list[::-1]:  # 移除列表中的元素可以倒序删除
                        if '__' in case:
                            priority = str_get_content_between_two_characters(case, '__', '__')
                            if priority not in ['P0', 'P1', 'P2']:  # 如果用例还包含其他的两个下划线，要排除掉
                                continue
                            elif case_priority == 'P0' and priority != 'P0':
                                test_class_cases_list.remove(case)
                            elif case_priority == 'P1' and priority != 'P0' and priority != 'P1':
                                test_class_cases_list.remove(case)

                # 排除掉一些指定不测试的用例
                if module_name in param_get_exclude_case_list():
                    for x in param_get_exclude_case_list()[module_name]:
                        for y in test_class_cases_list[::-1]:  # 移除列表中的元素可以倒序删除
                            if x in y:
                                test_class_cases_list.remove(y)

                test_class_dict[test_class_name] = test_class_cases_list
            else:
                # 现在modules[module_name]已经改为字典，该部分弃用
                aklog_printf("key:%s, value:%s" % (module_name, modules[module_name]))
                try:
                    module = __import__('lib' + module_name + '_' + modules[module_name])
                except:
                    aklog_printf('%s 用例不存在' % module_name)
                    continue
                # aklog_printf(module)
                # aklog_printf("%s %s" % (module_name, modules[module_name]))
                test_class = getattr(module, module_name + '_' + modules[module_name] + '_case')
                # aklog_printf(test_class)
                test_class_name = test_class.__name__
                test_class_cases_list = list(
                    filter(lambda m: m.startswith("test_") and callable(getattr(test_class, m)), dir(test_class)))

                test_class_dict[test_class_name] = test_class_cases_list
        aklog_printf('test_class_dict : %r' % test_class_dict)
        return test_class_dict

    @staticmethod
    def create_modules_dict():
        """创建用例模块字典，用于界面勾选生成用例树"""
        aklog_info('~~~~~~~~~~~~~~~~~~ 解析用例模块中.... ~~~~~~~~~~~~~~~~~~')
        modules_dict = {}
        modules = param_get_modules()
        master_device_config = None
        master_model = None
        master_models = None
        if param_get_master_model() and 'SOLUTION' not in param_get_master_model():
            if '+' in param_get_master_model():
                master_models = param_get_master_model().split('+')
                master_model = master_models[0]
            else:
                master_model = param_get_master_model()
            master_device_config = config_parse_device_config_by_model_and_oem(
                master_model, 'NORMAL')

        for module_name in modules.keys():
            test_class_dict = {}
            if isinstance(modules[module_name], dict):
                # aklog_printf("key:%s, value:%s" % (module_name, modules[module_name]['model_oem']))
                device_module_root_path = param_get_device_module_root_path()
                module_path = File_process.get_file_with_filename_from_path(device_module_root_path,
                                                                            'lib' + module_name + '_' +
                                                                            modules[module_name]['model_oem'] + '.py')
                if not module_path:
                    aklog_warn('未存在脚本文件: {}\\{}'.format(
                        device_module_root_path, 'lib' + module_name + '_' + modules[module_name]['model_oem'] + '.py'))
                    continue

                # 获取用例目录路径
                module_dir_path = os.path.split(module_path)[0]
                module_dirname = module_dir_path.replace(device_module_root_path, '').replace('TestCase', '') \
                    .strip('\\').replace('\\', '->')

                lib_module_name = 'lib' + module_name + '_' + modules[module_name]['model_oem']
                try:
                    module = __import__(lib_module_name)
                except Exception as e:
                    aklog_error('import %s failed: %s' % (lib_module_name, e))
                    # aklog_error(traceback.format_exc())
                    continue

                test_class = getattr(module, module_name + '_' + modules[module_name]['model_oem'] + '_case')
                test_class_name = test_class.__name__

                # 遍历获取用例类的用例列表
                test_class_cases_list = []

                for x in dir(test_class):
                    if x.startswith("__") or not x.startswith("test_") or not callable(getattr(test_class, x)):
                        continue
                    instance_list = getattr(getattr(test_class, x), '__unittest_exec_instance_list__', None)
                    if not instance_list:
                        test_class_cases_list.append(x)
                        continue
                    # 检查用例的设备需求数量是否满足
                    check_pass_count = 0
                    for instance_name in instance_list:
                        if '*' in instance_name:
                            instance_name, instance_count = instance_name.split('*')
                            instance_count = int(instance_count)
                        else:
                            instance_count = 1
                        for _type, count_info in param_get_device_count_info().items():
                            if not count_info.get(instance_name):
                                continue
                            if count_info.get(instance_name) >= instance_count:
                                check_pass_count += 1
                                break
                    if param_get_check_device_count_enable() and check_pass_count != len(instance_list):
                        # aklog_warn(f'device_info中的设备数量小于用例的设备数量需求，将跳过用例: {x}')
                        continue

                    if (not master_model or 'SOLUTION' in master_model) and not master_device_config:
                        test_class_cases_list.append(x)
                        continue
                    else:
                        master_product_type = master_device_config.get_product_type_name()
                        master_series = master_device_config.get_series_product_name()
                        if ((master_model in instance_list)
                                or (master_models and any(model in instance_list for model in master_models))
                                or (master_series and master_series != 'COMMON' and master_series in instance_list)
                                or (master_product_type and master_product_type in instance_list)):
                            test_class_cases_list.append(x)
                            continue
                if not test_class_cases_list:
                    continue
                # 根据优先级过滤测试用例
                case_priority = 'P2'
                use_suite = '0'

                if 'test_case_suite' in param_get_firmware_info_data():
                    test_case_suite = param_get_firmware_info_data()['test_case_suite'][0]
                    use_suite = test_case_suite['use_suite']

                if use_suite == '1':
                    for module_info in param_get_suite_list():
                        if module_name in module_info:
                            case_priority = module_info[module_name]['CasePriority']
                            break
                elif 'test_case_filter' in param_get_firmware_info_data():
                    test_case_filter = param_get_firmware_info_data()['test_case_filter'][0]
                    case_priority = test_case_filter['case_priority']

                if case_priority != 'P2':
                    # 过滤用例模块内用例的优先级，P2表示P0+P1+P2，P1表示P0+P1
                    for case in test_class_cases_list[::-1]:  # 移除列表中的元素可以倒序删除
                        if '__' in case:
                            priority = str_get_content_between_two_characters(case, '__', '__')
                            if priority not in ['P0', 'P1', 'P2']:  # 如果用例还包含其他的两个下划线，要排除掉
                                continue
                            if case_priority == 'P0' and priority != 'P0':
                                test_class_cases_list.remove(case)
                            elif case_priority == 'P1' and priority != 'P0' and priority != 'P1':
                                test_class_cases_list.remove(case)

                # 排除掉一些指定不测试的用例
                if module_name in param_get_exclude_case_list():
                    for x in param_get_exclude_case_list()[module_name]:
                        for y in test_class_cases_list[::-1]:  # 移除列表中的元素可以倒序删除
                            if x in y:
                                test_class_cases_list.remove(y)

                test_class_dict[test_class_name] = test_class_cases_list
                if module_dirname not in modules_dict:
                    modules_dict[module_dirname] = test_class_dict
                else:
                    modules_dict[module_dirname].update(test_class_dict)
            else:
                # 现在modules[module_name]已经改为字典，该部分弃用
                aklog_printf("key:%s, value:%s" % (module_name, modules[module_name]))
                device_module_root_path = param_get_device_module_root_path()
                module_path = File_process.get_file_with_filename_from_path(device_module_root_path,
                                                                            'lib' + module_name + '_' +
                                                                            modules[module_name] + '.py')
                if not module_path:
                    continue
                # module_dirname = File_process.get_file_dirname_from_path(module_path)  # 获取用例目录名称

                # 获取用例目录路径
                module_dir_path = os.path.split(module_path)[0]
                module_dirname = module_dir_path.replace(device_module_root_path, '').replace('TestCase', '') \
                    .strip('\\').replace('\\', '->')

                module = __import__('lib' + module_name + '_' + modules[module_name])  # 导入用例模块
                test_class = getattr(module, module_name + '_' + modules[module_name] + '_case')  # 获取用例类
                test_class_name = test_class.__name__  # 获取用例类名称
                # 获取用例类里面test_开头的测试用例名称列表
                test_class_cases_list = list(
                    filter(lambda m: m.startswith("test_") and callable(getattr(test_class, m)), dir(test_class)))

                test_class_dict[test_class_name] = test_class_cases_list
                if module_dirname not in modules_dict:
                    modules_dict[module_dirname] = test_class_dict
                else:
                    modules_dict[module_dirname].update(test_class_dict)

        aklog_info('用例模块: {}'.format(modules_dict))
        return modules_dict

# endregion


# region 模块适配

def module_creat_adapter(module_name):
    """模块调用适配"""
    modules = param_get_modules()
    if type(modules[module_name]) is dict:
        module = __import__('lib' + module_name + '_' + modules[module_name]['model_oem'])
        tclass = getattr(module, module_name + '_' + modules[module_name]['model_oem'])
        aklog_printf("%s %s cname:%s" % (module_name, modules[module_name]['model_oem'], tclass))
        return tclass
    else:
        module = __import__('lib' + module_name + '_' + modules[module_name])
        tclass = getattr(module, module_name + '_' + modules[module_name])
        aklog_printf("%s %s cname:%s" % (module_name, modules[module_name], tclass))
        return tclass


def base_module_adapter():
    model_name = param_get_model_name()
    if 'SOLUTION' in model_name:
        return None
    oem_name = param_get_oem_name()
    series = param_get_seriesproduct_name()
    series_module_name = config_get_series_module_name(series)
    product_line = config_get_product_line(series)
    version_branch = param_get_version_branch()
    aklog_debug(
        f'model name: {model_name}, oem name :{oem_name}, series: {series}, series module name: {series_module_name}, product_line: {product_line}, version_branch:{version_branch}')
    if '.' in version_branch:
        # 分支版本存在小数点，说明该分支版本有子分支版本区分，比如区分安全版本和非安全版本
        version_branch = version_branch.split('.')[0]

    class_name_model_oem = 'base_' + model_name + '_' + oem_name
    class_name_model_NORMAL = 'base_' + model_name + '_NORMAL'
    class_name_series_NORMAL = 'base_' + series + '_NORMAL'
    class_name_web_NORMAL = 'web_' + series + '_NORMAL'
    base_module_root_dir = ('%s\\testcase\\module\\%s\\%s\\%s\\Base'
                            % (root_path, product_line, series_module_name, version_branch))
    base_module_root_path = 'testcase.module.%s.%s.%s.Base' % (product_line, series_module_name, version_branch)
    if not os.path.exists(base_module_root_dir):
        base_module_root_dir = ('%s\\testcase\\module\\%s\\%s\\Base'
                                % (root_path, series_module_name, version_branch))
        base_module_root_path = 'testcase.module.%s.%s.Base' % (series_module_name, version_branch)
    base_module_init_file = '%s\\__init__.py' % base_module_root_dir

    if not os.path.exists(base_module_init_file):
        # 如果Base目录下不存在__init__.py，说明没有将Base模块做成package包
        def import_base_module(class_name, print_exception=False):
            try:
                module_name = 'lib' + class_name
                base_module = import_module('%s.%s' % (base_module_root_path, module_name))
                tclass = getattr(base_module, class_name)
            except Exception as e:
                if print_exception:
                    aklog_error('import %s, Fail: %s' % (class_name, e))
                tclass = None
            return tclass

        base_module_class = import_base_module(class_name_model_oem)
        if not base_module_class:
            base_module_class = import_base_module(class_name_model_NORMAL)
            if not base_module_class:
                base_module_class = import_base_module(class_name_series_NORMAL)
                if not base_module_class:
                    base_module_class = import_base_module(class_name_web_NORMAL, print_exception=True)
    else:
        # 存在__init__.py，说明已经将Base模块做成package包，可以通过包导入base模块
        def import_base_module(class_name, package=None, print_exception=False):
            try:
                tclass = getattr(package, class_name)
            except Exception as e:
                if print_exception:
                    aklog_error('import %s, Fail: %s' % (class_name, e))
                tclass = None
            return tclass

        base_package = import_module(base_module_root_path)
        base_module_class = import_base_module(class_name_model_oem, base_package)
        if not base_module_class:
            base_module_class = import_base_module(class_name_model_NORMAL, base_package)
            if not base_module_class:
                base_module_class = import_base_module(class_name_series_NORMAL, base_package)
                if not base_module_class:
                    base_module_class = import_base_module(class_name_web_NORMAL, base_package, print_exception=True)

    aklog_info('base_module_class: %s' % base_module_class)
    return base_module_class


def control_base_adapter():
    """
    获取ControlBase模块或包
    """
    try:
        model_name = param_get_model_name()
        oem_name = param_get_oem_name()
        series = param_get_seriesproduct_name()
        product_line = config_get_product_line(series)
        series_module_name = config_get_series_module_name(series)
        version_branch = param_get_version_branch()
        if '.' in version_branch:
            # 分支版本存在小数点，说明该分支版本有子分支版本区分，比如区分安全版本和非安全版本
            version_branch = version_branch.split('.')[0]

        control_base_model_oem = 'libControlBase_' + model_name + '_' + oem_name
        control_base_model_NORMAL = 'libControlBase_' + model_name + '_NORMAL'
        control_base_series_NORMAL = 'libControlBase_' + series + '_NORMAL'

        control_base_root_dir = ('%s\\testcase\\module\\%s\\%s\\%s\\ControlBase'
                                 % (root_path, product_line, series_module_name, version_branch))
        control_base_root_path = 'testcase.module.%s.%s.%s.ControlBase' % (
            product_line, series_module_name, version_branch)
        if not os.path.exists(control_base_root_dir):
            control_base_root_dir = ('%s\\testcase\\module\\%s\\%s\\ControlBase'
                                     % (root_path, series_module_name, version_branch))
            control_base_root_path = 'testcase.module.%s.%s.ControlBase' % (series_module_name, version_branch)
        if not os.path.exists(control_base_root_dir):
            control_base_root_dir = ('%s\\testcase\\module\\%s\\%s\\Base\\ControlBase'
                                     % (root_path, series_module_name, version_branch))
            control_base_root_path = 'testcase.module.%s.%s.Base.ControlBase' % (series_module_name, version_branch)
        control_base_init_file = '%s\\__init__.py' % control_base_root_dir

        if not os.path.exists(control_base_init_file):
            # 如果ControlBase目录下不存在__init__.py，说明没有将ControlBase模块做成package包
            def import_base_module(base_module_name, print_exception=False):
                try:
                    base_module = import_module('%s.%s' % (control_base_root_path, base_module_name))
                    tclass = getattr(base_module, base_module_name.replace('lib', ''))
                except Exception as e:
                    if print_exception:
                        aklog_error('import %s, Fail: %s' % (base_module_name, e))
                    tclass = None
                return tclass

            control_base_class = import_base_module(control_base_model_oem)
            if not control_base_class:
                control_base_class = import_base_module(control_base_model_NORMAL)
                if not control_base_class:
                    control_base_class = import_base_module(control_base_series_NORMAL, print_exception=True)

            aklog_info('ControlBase: %s' % control_base_class)
            control_base = control_base_class()
        else:
            # 存在__init__.py，说明已经将ControlBase模块做成package包，可以通过包导入ControlBase模块
            control_base_package = import_module(control_base_root_path)
            control_base = getattr(control_base_package, 'control_base')
            aklog_info('ControlBase: %s' % control_base)

        return control_base
    except:
        print(traceback.format_exc())
        return None


def control_base_parse():
    """
    获取ControlBase模块或包
    """
    try:
        model_name = param_get_model_name()
        oem_name = param_get_oem_name()
        series = param_get_seriesproduct_name()
        product_line = config_get_product_line(series)
        series_module_name = config_get_series_module_name(series)
        version_branch = param_get_version_branch()
        if '.' in version_branch:
            # 分支版本存在小数点，说明该分支版本有子分支版本区分，比如区分安全版本和非安全版本
            version_branch = version_branch.split('.')[0]

        control_base_model_oem = 'libControlBase_' + model_name + '_' + oem_name
        control_base_model_NORMAL = 'libControlBase_' + model_name + '_NORMAL'
        control_base_series_NORMAL = 'libControlBase_' + series + '_NORMAL'
        control_base_root_path = 'testcase.module.%s.%s.%s.ControlBase' % (
            product_line, series_module_name, version_branch)

        def import_base_module(base_module_name, print_exception=False):
            try:
                base_module = import_module('%s.%s' % (control_base_root_path, base_module_name))
                tclass = getattr(base_module, base_module_name.replace('lib', ''))
            except Exception as e:
                if print_exception:
                    aklog_error('import %s, Fail: %s' % (base_module_name, e))
                tclass = None
            return tclass

        control_base_class = import_base_module(control_base_model_oem)
        if not control_base_class:
            control_base_class = import_base_module(control_base_model_NORMAL)
            if not control_base_class:
                control_base_class = import_base_module(control_base_series_NORMAL, print_exception=True)

        aklog_debug('ControlBase: %s' % control_base_class)
        return control_base_class
    except:
        aklog_debug(traceback.format_exc())
        return None


def get_base_module_by_name(model_name):
    base_module_name = 'libbase_%s_NORMAL' % model_name
    class_name = 'base_%s_NORMAL' % model_name

    # 添加base模块目录到sys.path环境变量
    series = config_get_series(model_name)
    product_line = config_get_product_line(series)
    series_module_name = config_get_series_module_name(series)
    version_branch_info = param_get_version_branch_info()
    version_branch = version_branch_info['%s_branch' % series_module_name]
    if '.' in version_branch:
        # 分支版本存在小数点，说明该分支版本有子分支版本区分，比如区分安全版本和非安全版本
        version_branch = version_branch.split('.')[0]

    base_module_root_dir = ('%s\\testcase\\module\\%s\\%s\\%s\\Base'
                            % (root_path, product_line, series_module_name, version_branch))
    base_module_root_path = 'testcase.module.%s.%s.%s.Base' % (product_line, series_module_name, version_branch)
    if not os.path.exists(base_module_root_dir):
        base_module_root_dir = ('%s\\testcase\\module\\%s\\%s\\Base'
                                % (root_path, series_module_name, version_branch))
        base_module_root_path = 'testcase.module.%s.%s.Base' % (series_module_name, version_branch)
    base_module_init_file = '%s\\__init__.py' % base_module_root_dir

    if not os.path.exists(base_module_init_file):
        # 如果Base目录下不存在__init__.py，说明没有将Base模块做成package包
        base_module = import_module('%s.%s' % (base_module_root_path, base_module_name))
        base_class = getattr(base_module, class_name)
        aklog_printf('base_module_class: %s' % base_class)
    else:
        base_package = import_module(base_module_root_path)
        base_class = getattr(base_package, class_name)

    return base_class


def get_base_module_by_device_config(device_config, instance=True):
    """
    通过指定的device config获取辅助设备的基类
    :param device_config:
    :param instance: 是否返回实例化
    :return:
    """
    aklog_printf('get_base_module_by_device_config')
    model_name = device_config.get_model_name()
    oem_name = device_config.get_oem_name()
    series = device_config.get_series_product_name()
    product_line = config_get_product_line(series)
    series_module_name = config_get_series_module_name(series)
    version_branch_info = param_get_version_branch_info()
    version_branch = version_branch_info['%s_branch' % series_module_name]
    if '.' in version_branch:
        # 分支版本存在小数点，说明该分支版本有子分支版本区分，比如区分安全版本和非安全版本
        version_branch = version_branch.split('.')[0]

    class_name_model_oem = 'base_' + model_name + '_' + oem_name
    class_name_model_NORMAL = 'base_' + model_name + '_NORMAL'
    class_name_series_NORMAL = 'base_' + series + '_NORMAL'
    class_name_web_NORMAL = 'web_' + series + '_NORMAL'

    base_module_root_dir = ('%s\\testcase\\module\\%s\\%s\\%s\\Base'
                            % (root_path, product_line, series_module_name, version_branch))
    base_module_root_path = 'testcase.module.%s.%s.%s.Base' % (product_line, series_module_name, version_branch)
    if not os.path.exists(base_module_root_dir):
        base_module_root_dir = ('%s\\testcase\\module\\%s\\%s\\Base'
                                % (root_path, series_module_name, version_branch))
        base_module_root_path = 'testcase.module.%s.%s.Base' % (series_module_name, version_branch)
    base_module_init_file = '%s\\__init__.py' % base_module_root_dir

    if not os.path.exists(base_module_init_file):
        # 如果Base目录下不存在__init__.py，说明没有将Base模块做成package包
        def import_base_module(class_name, print_exception=False):
            try:
                module_name = 'lib' + class_name
                base_module = import_module('%s.%s' % (base_module_root_path, module_name))
                tclass = getattr(base_module, class_name)
            except Exception as e:
                if print_exception:
                    aklog_error('import %s, Fail: %s' % (class_name, e))
                tclass = None
            return tclass

        base_module_class = import_base_module(class_name_model_oem)
        if not base_module_class:
            base_module_class = import_base_module(class_name_model_NORMAL)
            if not base_module_class:
                base_module_class = import_base_module(class_name_series_NORMAL)
                if not base_module_class:
                    base_module_class = import_base_module(class_name_web_NORMAL, print_exception=True)
    else:
        # 存在__init__.py，说明已经将Base模块做成package包，可以通过包导入base模块
        def import_base_module(class_name, package=None, print_exception=False):
            try:
                tclass = getattr(package, class_name)
            except Exception as e:
                if print_exception:
                    aklog_error('import %s, Fail: %s' % (class_name, e))
                tclass = None
            return tclass

        base_package = import_module(base_module_root_path)
        base_module_class = import_base_module(class_name_model_oem, base_package)
        if not base_module_class:
            base_module_class = import_base_module(class_name_model_NORMAL, base_package)
            if not base_module_class:
                base_module_class = import_base_module(class_name_series_NORMAL, base_package)
                if not base_module_class:
                    base_module_class = import_base_module(class_name_web_NORMAL, base_package, print_exception=True)
    aklog_printf('base_module_class: %s' % base_module_class)

    if instance:  # 是否返回实例化
        base_module = base_module_class()
    else:
        base_module = base_module_class
    return base_module


def get_base_module_by_device_config_from_package(
        device_config, package, base_module_normal=None, instance=True):
    """
    通过指定的device config获取辅助设备的基类
    """
    model_name = device_config.get_model_name()
    oem_name = device_config.get_oem_name()
    series = device_config.get_series_product_name()
    aklog_printf('get_base_module_by_device_config_from_package, series: %s, model: %s, oem: %s'
                 % (series, model_name, oem_name))

    class_name_model_oem = 'base_' + model_name + '_' + oem_name
    class_name_model_NORMAL = 'base_' + model_name + '_NORMAL'
    class_name_series_NORMAL = 'base_' + series + '_NORMAL'

    def import_base_module(class_name, package, print_exception=False):
        try:
            tclass = getattr(package, class_name)
        except Exception as e:
            if print_exception:
                aklog_error('import %s, Fail: %s' % (class_name, e))
            tclass = None
        return tclass

    base_module_class = import_base_module(class_name_model_oem, package)
    if not base_module_class:
        base_module_class = import_base_module(class_name_model_NORMAL, package)
        if not base_module_class:
            base_module_class = import_base_module(class_name_series_NORMAL, package, print_exception=True)

    if (base_module_normal and
            base_module_class.__dict__['__module__'] == base_module_normal.__class__.__dict__['__module__']):
        aklog_printf('base模块仍是使用通用模块，不再重新实例化')
        return base_module_normal

    aklog_printf('base_module_class: %s' % base_module_class)
    if instance:  # 是否返回实例化
        base_module = base_module_class()
    else:
        base_module = base_module_class
    return base_module


def get_base_module_instance_by_app(app, instance=True):
    """
    通过指定的device config获取辅助设备的基类
    :param app: 对应设备的app or browser，比如: param_get_guardphone_app_slave1()
    :param instance: 是否返回实例化
    :return: 返回的是基类的实例
    """
    device_config = app.get_device_config()
    model_name = device_config.get_model_name()
    oem_name = device_config.get_oem_name()
    series = device_config.get_series_product_name()
    product_line = config_get_product_line(series)
    series_module_name = config_get_series_module_name(series)
    version_branch_info = param_get_version_branch_info()
    version_branch = version_branch_info['%s_branch' % series_module_name]
    if '.' in version_branch:
        # 分支版本存在小数点，说明该分支版本有子分支版本区分，比如区分安全版本和非安全版本
        version_branch = version_branch.split('.')[0]

    class_name_model_oem = 'base_' + model_name + '_' + oem_name
    class_name_model_NORMAL = 'base_' + model_name + '_NORMAL'
    class_name_series_NORMAL = 'base_' + series + '_NORMAL'
    class_name_web_NORMAL = 'web_' + series + '_NORMAL'

    base_module_root_dir = ('%s\\testcase\\module\\%s\\%s\\%s\\Base'
                            % (root_path, product_line, series_module_name, version_branch))
    base_module_root_path = 'testcase.module.%s.%s.%s.Base' % (product_line, series_module_name, version_branch)
    if not os.path.exists(base_module_root_dir):
        base_module_root_dir = ('%s\\testcase\\module\\%s\\%s\\Base'
                                % (root_path, series_module_name, version_branch))
        base_module_root_path = 'testcase.module.%s.%s.Base' % (series_module_name, version_branch)
    base_module_init_file = '%s\\__init__.py' % base_module_root_dir

    if not os.path.exists(base_module_init_file):
        # 如果Base目录下不存在__init__.py，说明没有将Base模块做成package包
        def import_base_module(class_name, print_exception=False):
            try:
                module_name = 'lib' + class_name
                base_module = import_module('%s.%s' % (base_module_root_path, module_name))
                tclass = getattr(base_module, class_name)
            except Exception as e:
                if print_exception:
                    aklog_error('import %s, Fail: %s' % (class_name, e))
                tclass = None
            return tclass

        base_module_class = import_base_module(class_name_model_oem)
        if not base_module_class:
            base_module_class = import_base_module(class_name_model_NORMAL)
            if not base_module_class:
                base_module_class = import_base_module(class_name_series_NORMAL)
                if not base_module_class:
                    base_module_class = import_base_module(class_name_web_NORMAL, print_exception=True)
    else:
        # 存在__init__.py，说明已经将Base模块做成package包，可以通过包导入base模块
        def import_base_module(class_name, package=None, print_exception=False):
            try:
                tclass = getattr(package, class_name)
            except Exception as e:
                if print_exception:
                    aklog_error('import %s, Fail: %s' % (class_name, e))
                tclass = None
            return tclass

        base_package = import_module(base_module_root_path)
        base_module_class = import_base_module(class_name_model_oem, base_package)
        if not base_module_class:
            base_module_class = import_base_module(class_name_model_NORMAL, base_package)
            if not base_module_class:
                base_module_class = import_base_module(class_name_series_NORMAL, base_package)
                if not base_module_class:
                    base_module_class = import_base_module(class_name_web_NORMAL, base_package, print_exception=True)

    aklog_printf('base_module_class: %s' % base_module_class)

    if instance:
        base_module = base_module_class()
    else:
        base_module = base_module_class
    return base_module


def get_base_module_by_class_name(class_name, module_name=None, instance=True):
    """
    获取模块基类
    :param class_name: 类名称
    :param module_name: 模块名称
    :param instance: 是否返回实例化
    :return:
    """
    if '_' in class_name and len(class_name.split('_')) > 2:
        model_name = class_name.split('_')[-2]
        series = config_get_series(model_name)
        if series is None:
            series = model_name
        product_line = config_get_product_line(series)
        series_module_name = config_get_series_module_name(series)
        version_branch_info = param_get_version_branch_info()
        version_branch = version_branch_info['%s_branch' % series_module_name]
        if '.' in version_branch:
            # 分支版本存在小数点，说明该分支版本有子分支版本区分，比如区分安全版本和非安全版本
            version_branch = version_branch.split('.')[0]

        base_module_root_dir = ('%s\\testcase\\module\\%s\\%s\\%s\\Base'
                                % (root_path, product_line, series_module_name, version_branch))
        base_module_root_path = 'testcase.module.%s.%s.%s.Base' % (product_line, series_module_name, version_branch)
        if not os.path.exists(base_module_root_dir):
            base_module_root_dir = ('%s\\testcase\\module\\%s\\%s\\Base'
                                    % (root_path, series_module_name, version_branch))
            base_module_root_path = 'testcase.module.%s.%s.Base' % (series_module_name, version_branch)
        base_module_init_file = '%s\\__init__.py' % base_module_root_dir

        if not os.path.exists(base_module_init_file):
            # 如果Base目录下不存在__init__.py，说明没有将Base模块做成package包
            if module_name is None:
                module_name = 'lib' + class_name
            base_module = import_module('%s.%s' % (base_module_root_path, module_name))
            base_class = getattr(base_module, class_name)
        else:
            base_package = import_module(base_module_root_path)
            base_class = getattr(base_package, class_name)
    else:
        # base_module模块名称格式不是系列名称和OEM名称拼接而成，表示通用模块，已添加目录到sys.path，可以直接使用模块名称导入
        if module_name is None:
            module_name = 'aklib' + class_name
        base_module = import_module(module_name)
        base_class = getattr(base_module, class_name)

    aklog_printf('base_module_class: %s' % base_class)
    if instance:
        base_module = base_class()
    else:
        base_module = base_class
    return base_module

# endregion


# region 随机选择

def select_with_priority(elements, num_selections):
    """从一个list中随机选择，优先选择没有被选中的元素"""
    # 确保输入的列表不为空
    if not elements:
        raise ValueError("The list of elements is empty.")

    # 如果需要的选择数小于等于列表长度，则直接随机选择，不重复
    num_selections = int(num_selections)
    if num_selections <= len(elements):
        selections = random.sample(elements, num_selections)
    else:
        # 首先，确保每个元素至少被选中一次
        selections = random.sample(elements, len(elements))
        remaining_selections = num_selections - len(elements)

        # 对剩余的选择，随机选择元素
        for _ in range(remaining_selections):
            selections.append(random.choice(elements))

    return selections


def choose_random_exclude_selected(elements, selected_list=None, clear=True):
    """
    从列表 elements 中随机选择一个元素，排除 selected_list 列表中的元素，在剩下的选项中选择后，会添加到selected_list里面，下次就不会再次选择
    Args:
        elements (list): 原始列表
        selected_list (list): 已选中的元素列表
        clear (bool): 当filtered_list为空时，是否清空selected_list，重新选择
    """
    if selected_list is None:
        selected_list = []
    filtered_list = [item for item in elements if item not in selected_list]

    if not filtered_list:
        if not clear:
            return None  # 如果没有可选元素，返回 None
        else:
            selected_list.clear()
            selected_item = random.choice(elements)
    else:
        selected_item = random.choice(filtered_list)
    if selected_item not in selected_list:
        selected_list.append(selected_item)
    return selected_item


def choose_random_element(elements, *excludes):
    """
    从列表 elements 中随机选择一个元素，排除 selected_list 列表中的元素，在剩下的选项中选择后，会添加到selected_list里面，下次就不会再次选择
    Args:
        elements (list): 原始列表
        excludes (list): 要排除的元素列表
    """
    if excludes:
        filtered_list = [item for item in elements if item not in excludes]
    else:
        filtered_list = elements
    if not filtered_list:
        return None  # 如果没有可选元素，返回 None
    return random.choice(filtered_list)


def remove_element_from_list(lst, element):
    """
    从列表中移除指定元素，并返回一个新的列表。如果元素不存在，返回原列表。

    参数:
    lst (list): 要操作的列表
    element: 要移除的元素

    返回:
    list: 移除了指定元素后的新列表
    """
    try:
        new_list = lst.copy()  # 创建列表的副本
        new_list.remove(element)
        return new_list
    except ValueError:
        # 元素不存在于列表中，返回原列表的副本
        return lst.copy()
    except Exception as e:
        aklog_warn(e)
        return []


def choose_random_device(device_list: list, *excludes, count=1, priority_select=None):
    """从设备实例列表里随机选择，也可以优先选择"""
    devices_info = {}
    for device in device_list:
        if hasattr(device, 'device_name'):
            device_name = device.device_name
            devices_info[device_name] = device

    if priority_select and priority_select in devices_info:
        return devices_info[priority_select]

    def __choose_random_excluding(device_list, *excludes, count=1):
        """
        从列表 device_list 中随机选择一个元素，排除 exclude 列表中的元素。
        :param device_list: 原始列表
        :param excludes: 要排除的元素列表
        :param count: 选择数量
        :return: 随机选择的元素，如果没有可选元素则返回 None
        """
        if excludes:
            filtered_list = [item for item in device_list if item not in excludes]
        else:
            filtered_list = device_list
        if not filtered_list:
            return [None] * count  # 如果没有可选元素，返回 None
        if count > 1:
            if count > len(filtered_list):
                return [None] * count  # 如果请求的数量大于可选元素数量，返回 None
            return random.sample(filtered_list, count)
        return [random.choice(filtered_list)]

    aklog_debug(f'random choose from: {list(devices_info.keys())}')
    devices = __choose_random_excluding(device_list, *excludes, count=count)
    if not devices or None in devices:
        raise unittest.SkipTest(f'未找到 {count} 个设备')

    if count == 1:
        return devices[0]
    return devices


def choose_random_number(ranges: list, *excludes, offset=None):
    """
    随机选择数字
    Args:
        ranges (list): 范围的头尾两个数字
        *excludes (int): 排除的数字
        offset (int): 如果excludes只给定一个数字，然后offset作为该数字的前后偏移量，比如exclude为50，offset=5，那么将排除45-55的数字
    """
    start = int(ranges[0])
    end = int(ranges[1])
    number_list = list(range(start, end+1))
    if excludes:
        if len(excludes) == 1 and offset:
            for x in range(excludes[0] - offset, excludes[0] + offset + 1):
                if x in number_list:
                    number_list.remove(x)
        else:
            for x in excludes:
                if x in number_list:
                    number_list.remove(x)
    number = random.choice(number_list)
    return number


def generate_random_combinations(lst, constraints=None, num_combinations=None,
                                 first_element=None, second_element=None, max_attempts=1000):
    """
    生成随机两两组合，满足：
    1. 组合中的两个元素不能相同
    2. num_combinations: 需要生成的有效组合数量（默认为None表示生成len(lst)数量），最小为1，最大可以超过lst长度
    3. 当生成数量等于lst长度时，lst的每个元素在组合的第一个位置和第二个位置各出现一次
    4. 当生成数量大于lst长度时，先满足每个元素在组合的第一个位置和第二个位置至少各出现一次，之后再随机组合，但所有组合不重复
    5. 输出顺序是随机的
    6. 支持自定义约束条件（约束某些元素不能成为组合），并且约束条件可能比较耗时，需要尽可能的减少约束条件的调用次数
    7. 可以传入第一个或第二个元素，然后从lst里找到另一个形成组合
    8. 满足上述条件情况下，尽量提高生成效率
    Args:
        lst (list): 用于生成组合的元素列表
        constraints (function): 自定义约束条件方法
        num_combinations (int): 生成组合数量
        first_element (str): 生成的组合指定第一个元素
        second_element (str): 生成的组合指定第二个元素
        max_attempts (int): 最大尝试次数
    """
    # 参数预处理
    n = len(lst)
    if n < 2:
        return []

    # 设置默认生成数量
    if num_combinations is None:
        num_combinations = n
    num_combinations = max(1, num_combinations)

    # 缓存约束检查结果
    constraint_cache = {}

    def passes_constraints(pair):
        if constraints is None:
            return True
        if pair not in constraint_cache:
            constraint_cache[pair] = constraints(pair)
        return constraint_cache[pair]

    def get_valid_combo(combo, num):
        results = []
        if constraints:
            for c in combo:
                if passes_constraints(c):
                    results.append(c)
                if len(results) == num:
                    break
        else:
            results = combo[:num]
        return results

    def _generate_base_combinations(lst, max_attempts, num_combinations):
        """
        生成基础组合（数量 <= n）
        """
        seen = set()
        results = []

        # 生成组合
        for _ in range(max_attempts):
            perm1 = random.sample(lst, n)
            perm2 = random.sample(lst, n)
            if any(a == b for a, b in zip(perm1, perm2)):
                continue

            combo = list(zip(perm1, perm2))
            valid_combo = get_valid_combo(combo, num_combinations)
            if len(valid_combo) >= num_combinations:
                combo_key = tuple(valid_combo)
                if combo_key not in seen:
                    seen.add(combo_key)
                    results.extend(valid_combo[:num_combinations - len(results)])
                    if len(results) >= num_combinations:
                        return results

        return results

    def _generate_extended_combinations(lst, max_attempts, num_combinations):
        """生成扩展组合（数量 > n）"""
        base = _generate_base_combinations(lst, max_attempts, len(lst))
        if not base:
            return []

        # 生成额外组合
        candidates = [p for p in permutations(lst, 2) if p[0] != p[1]]
        seen = set(base)
        results = list(base)

        attempts = 0
        while len(results) < num_combinations and attempts < max_attempts:
            attempts += 1
            candidate = random.choice(candidates)
            if candidate not in seen and (not constraints or passes_constraints(candidate)):
                results.append(candidate)
                seen.add(candidate)

        return results[:num_combinations]

    def _handle_single_fixed_element(lst, num, first=None, second=None):
        """优化后的固定单个元素处理方法"""
        # 生成候选组合时直接过滤基础约束
        if first:
            candidates = [(first, b) for b in lst if b != first]
        else:
            candidates = [(a, second) for a in lst if a != second]

        # 先随机打乱避免顺序偏好
        random.shuffle(candidates)

        # 带短路机制的约束检查
        valid = []
        for c in candidates:
            if not constraints or passes_constraints(c):
                valid.append(c)
                if len(valid) == num:  # 数量达标立即终止
                    break

        return valid

    # 元素定位处理
    if first_element is not None or second_element is not None:
        return _handle_single_fixed_element(lst, num_combinations, first_element, second_element)

    # 分情况生成策略
    if num_combinations <= n:
        return _generate_base_combinations(lst, max_attempts, num_combinations)
    else:
        return _generate_extended_combinations(lst, max_attempts, num_combinations)


def generate_minimal_test_cases(*args):
    """
    生成最小的单因子覆盖测试用例集。
    每个参数的所有取值都至少被覆盖一次，输出为参数值的组合。
    假如传入的多个因子列表，长度最长为4，那么只需要生成4个组合即可。
    Args:
        *args (): 任意数量的参数及其取值，例如:
                ["打开", "切换", "触发"], ["回家模式", "离家模式"]
    Returns: 最小的测试用例集，每个用例是一个完整的参数值组合。
    """
    # 如果参数列表为空，直接返回空列表
    if not args:
        return []

    # 随机打乱每个参数的取值列表
    values = [random.sample(v, len(v)) for v in args]

    # 获取最长的参数列表长度
    max_length = max(len(param) for param in values)

    # 生成最小的测试用例集
    test_cases = []
    for i in range(max_length):
        test_case = []
        for param in values:
            # 循环使用参数的取值
            test_case.append(param[i % len(param)])
        test_cases.append(test_case)

    # 随机打乱测试用例顺序（可选）
    random.shuffle(test_cases)

    # 返回测试用例集
    return test_cases

# endregion


def is_method_empty(method) -> bool:
    """
    判断方法是否为空实现（只包含 docstring、pass、注释、空行）
    """
    try:
        # 获取源代码行和起始行号
        source_lines, _ = inspect.getsourcelines(method)
        # 去除统一缩进
        source = textwrap.dedent(''.join(source_lines))
        lines = source.strip().splitlines()

        # 移除 def 行
        if not lines:
            return True
        lines = lines[1:]

        # 过滤空行、注释行
        code_lines = []
        in_docstring = False
        for line in lines:
            stripped = line.strip()

            # 跳过空行和注释
            if not stripped or stripped.startswith('#'):
                continue

            # 处理多行 docstring（""" 或 '''）
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                    if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                        in_docstring = False  # 单行 docstring
                else:
                    in_docstring = False
                continue

            if in_docstring:
                continue

            # 跳过 pass
            if stripped == 'pass':
                continue

            # 有其他代码，说明不是空实现
            code_lines.append(stripped)

        return len(code_lines) == 0

    except Exception as e:
        # 出错时保守认为不是空实现
        return False
