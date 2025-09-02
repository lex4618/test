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
from testcase.common.AkubelaBase.aklibAkubelaWebInfAdapter import get_product_info_by_web_inf
import time
import traceback
import unittest
import random
import tempfile
import re
import requests
import datetime
from multiprocessing import Process
from filelock import FileLock, Timeout
from collections import defaultdict
from pathlib import Path

__report_dir_url = None


def smb_copy(reportfile, dstfile, server='192.168.254.9', username='IntercomSQA', password='Akuvox@2024',
             share_folder='对讲质量部'):
    aklog_debug()
    try:
        from smb.SMBConnection import SMBConnection
        server_name = 'xxx'
        local_name = ''
        conn = SMBConnection(username, password, local_name, server_name, use_ntlm_v2=True)
        connected = conn.connect(server, 445)
        if connected:
            dstpathlist = dstfile.split('\\')
            dstpath = ''
            for e in dstpathlist:
                if not (e.endswith('.html') or e.endswith('.zip')):
                    dstpath = dstpath + '\\' + e
                    try:
                        conn.createDirectory(share_folder, dstpath)
                    except:
                        pass
            file = open(reportfile, 'rb')
            conn.storeFile(share_folder, dstfile, file)
            file.close()
        else:
            aklog_warn('连接共享文件夹失败!')
            return False
    except:
        aklog_warn('复制文件到共享文件夹失败!')
        print(traceback.format_exc())
        return False


def is_intercom():
    product_line = param_get_product_line_name()
    return product_line == 'INTERCOM'


def intercom_copy_report_to_smb(reportdir, test_result_summary, skipcount=0, report_case_limit_count=20):
    r"""
    功能: 复制对讲终端的挂测报告到共享服务器, 并上报报告到对讲质量部网站.
    1. 过滤对讲终端
    2. 按日期存储.
    如: \\192.168.254.9\对讲质量部\05_测试报告\自动化测试报告\门口机\冒烟测试\2024-07-10\320.30.4.138
    # ps: 如果用例执行数少于20: 则认为是调试, 不去上传
    # 如果有出现libs\d\d 的用例, 认为是冒烟用例.
    # 其他为关键用例.
    """
    test_case_all_counts = test_result_summary['Total_testcases']
    try:
        if not is_intercom():
            return
        if test_case_all_counts < report_case_limit_count:
            # 执行用例数太少: 调试用例或者异常失败太多的用例不统计.
            aklog_warn('对讲终端报告: 执行用例太少, 不保存. ')
            return
        rom_version = param_get_rom_version()
        series_products = param_get_seriesproduct_name()
        if not os.path.exists(reportdir):
            return
        if 'Report.html' not in os.listdir(reportdir):
            return
        content = ''
        with open(os.path.join(reportdir, 'Result.txt'), encoding='utf8', errors='ignore') as f:
            content = f.read()
        if param_get_test_counts() > 1 or param_get_test_times() > 1:
            autotype = 'stress'
        else:
            if re.search(r'libs\d\d', content):
                autotype = 'smoke'
            else:
                autotype = 'keyfeature'

        netpath = r'05_测试报告\自动化测试报告\通用'
        if series_products.lower() in ['linuxdoor', 'androiddoor']:
            netpath = r'05_测试报告\自动化测试报告\门口机'
        elif series_products.lower() in ['androidindoor', 'androidindoorv6', 'linuxindoor']:
            netpath = r'05_测试报告\自动化测试报告\室内机'
        elif series_products.lower() in ['accessdoor', 'accesscontrol']:
            netpath = r'05_测试报告\自动化测试报告\门禁'
        if autotype == 'keyfeature':
            netpath += r'\关键功能'
        elif autotype == 'smoke':
            netpath += r'\冒烟测试'
        elif autotype == 'stress':
            netpath += r'\压测'

        model_name = param_get_model_name()
        netpath += '\\' + model_name + '\\' + time.strftime('%Y-%m-%d')

        # if os.path.exists(r'\\192.168.254.9\对讲质量部' + '\\' + netpath + '\\' + rom_version):
        #     aklog_printf('smb上已经有同版本记录!')
        #     netpath = netpath + '\\' + rom_version + '_{}'.format(time.strftime('%H%M%S'))
        # else:
        #     netpath = netpath + '\\' + rom_version

        aklog_info('准备复制对讲终端自动化报告到共享文件夹中...')
        curtime = time.strftime('%H%M%S')
        for i in os.listdir(reportdir):
            if 'report' in i.lower() and '.html' in i.lower():
                aklog_info('复制: {} -> {}'.format(os.path.join(reportdir, i), netpath + f'\\{curtime}\\'))
                smb_copy(os.path.join(reportdir, i), netpath + f'\\{curtime}\\' + i)  # jenkins分布任务会覆盖.
            elif i.lower() == 'device_log.zip':
                try:
                    smb_copy(os.path.join(reportdir, i), netpath + f'\\{curtime}\\' + i)
                except:
                    sub_process_exec_command('copy "{}" "{}"'.format(os.path.join(reportdir, i),
                                                                     r'\\192.168.254.9\对讲质量部' + '\\' + netpath + f'\\{curtime}\\' + i))
            if 'Result.txt' in i.lower():
                # 复制结果集到共享文件夹中
                aklog_info('复制: {} -> {}'.format(os.path.join(reportdir, i), netpath + f'\\{curtime}\\'))
                smb_copy(os.path.join(reportdir, i), netpath + f'\\{curtime}\\' + i)

    except:
        aklog_error('复制自动化报告到共享文件夹失败!')
        print(traceback.format_exc())


def intercom_report_to_server(reportdir, test_result_summary, skipcount=0, report_case_limit_count=20):
    """个人PC触发任务"""
    test_case_all_counts = test_result_summary['Total_testcases']
    if test_case_all_counts < report_case_limit_count:
        return
    test_case_pass_counts = test_result_summary['Pass_testcases']
    test_case_skip_counts = skipcount
    content = ''
    with open(os.path.join(reportdir, 'Result.txt'), encoding='utf8', errors='ignore') as f:
        content = f.read()
    if param_get_test_counts() > 1 or param_get_test_times() > 1:
        autotype = 'stress'
    else:
        if re.search(r'libs\d\d', content):
            autotype = 'smoke'
        else:
            autotype = 'keyfeature'

    send_data = {}
    for key, value in g_test_results_summary.items():
        if key == 'Test_type':
            continue
        elif key == 'Pass_rate':
            test_pass_rate = round((test_case_pass_counts + test_case_skip_counts) / test_case_all_counts * 100,
                                   1)  #
            send_data['Pass_rate'] = str(test_pass_rate) + '%'
        elif key == 'Take_time':
            send_data['Take_time'] = str(int(value)) + 'min'
        elif key == 'Test_date':
            send_data[key] = param_get_start_time()
        else:
            send_data[key] = value

    if autotype == 'smoke':
        # 冒烟
        send_data['Test_type'] = 3
    elif autotype == 'keyfeature':
        # 关键功能
        send_data['Test_type'] = 2
    elif autotype == 'allfeature':
        # 功能测试
        send_data['Test_type'] = 0
    else:
        # 压测
        send_data['Test_type'] = 1

    if send_data['Test_type'] == 1:
        ak_requests = AkRequests('http://192.168.10.11:8000/myadmin/autotest_stress/insert_json')
    else:
        ak_requests = AkRequests('http://192.168.10.11:8000/myadmin/autotest_function/insert_json')
    ak_requests.send_post(send_data)
    ak_requests.close()
    aklog_printf('发送测试结果汇总到服务器成功')


def intercom_report_to_server_by_jenkins(result_summary, report_case_limit_count=20):
    """合并jenkins上两个任务的通过率数据再上报给对讲质量部平台,
    ps: 测试starttime 和spendtime统计无法准确. 取个大概值"""

    firmwareinfo = param_get_firmware_info_data().get('firmware_info')[0]
    productname = firmwareinfo.get('model_name')
    Product_version = firmwareinfo.get('firmware_version')
    series_products = config_get_series(productname)
    product_line = config_get_product_line(series_products)
    if product_line != 'INTERCOM':
        return
    test_case_pass_counts = result_summary.get('test_case_pass_counts', 0)
    test_case_skip_counts = result_summary.get('test_case_skip_counts', 0)
    test_case_all_counts = result_summary.get('test_case_all_counts', 0)
    if test_case_all_counts < report_case_limit_count:
        return

    jenkins_merge_report_dir = param_get_jenkins_report_dir()
    content = ''
    for job_name in os.listdir(jenkins_merge_report_dir):
        sub_job_report_dir = os.path.join(jenkins_merge_report_dir, job_name)
        # 判断是否为目录，不是就跳过
        if not os.path.isdir(sub_job_report_dir):
            continue
        resulttxt = os.path.join(sub_job_report_dir, 'Result.txt')
        if not os.path.isfile(resulttxt):
            aklog_info(f"{resulttxt} 不存在")
            continue
        try:
            with open(resulttxt, encoding='utf8', errors='ignore') as f:
                content = f.read()
            break
        except Exception as e:
            aklog_error(f"读取 {resulttxt} 异常：{e}")

    timelist = re.findall(r'\d{4}-\d+-\d+ \d+:\d+:\d+', content)
    if timelist:
        Test_date = timelist[0]
        take_time = datetime.datetime.strptime(timelist[-1],
                                               "%Y-%m-%d %H:%M:%S").timestamp() - datetime.datetime.strptime(
            timelist[0], "%Y-%m-%d %H:%M:%S").timestamp()
        take_time = str(int(take_time / 60)) + 'min'
    else:
        Test_date = time.strftime('%Y-%m-%d %H:%M:%S')
        take_time = 'xx min'

    ret = re.findall('test.*lib.*case', content)
    if ret and len(ret) != len(list(set(ret))):
        autotype = 'stress'
    else:
        if re.search(r'libs\d\d', content):
            autotype = 'smoke'
        else:
            autotype = 'keyfeature'
    if autotype == 'smoke':
        # 冒烟
        testtype = 3
    elif autotype == 'keyfeature':
        # 关键功能
        testtype = 2
    elif autotype == 'allfeature':
        # 功能测试
        testtype = 0
    else:
        # 压测
        testtype = 1

    test_pass_rate = round((test_case_pass_counts + test_case_skip_counts) / test_case_all_counts * 100, 1)
    send_data = {
        'Product_name': 'Jenkins: ' + productname,
        'Product_version': Product_version,
        'Total_testcases': test_case_all_counts,
        'Pass_testcases': test_case_pass_counts,
        'Pass_rate': str(test_pass_rate) + '%',
        'Test_type': testtype,
        'Take_time': take_time,
        'Test_date': Test_date
    }

    if send_data['Test_type'] == 1:
        ak_requests = AkRequests('http://192.168.10.11:8000/myadmin/autotest_stress/insert_json')
    else:
        ak_requests = AkRequests('http://192.168.10.11:8000/myadmin/autotest_function/insert_json')
    ak_requests.send_post(send_data)
    ak_requests.close()
    aklog_printf('发送测试结果汇总到服务器成功')


def get_fold_head():
    head = """
    <head>
    <script>
    function toggleIframe(eid) {
      var iframe = document.getElementById(eid);
      if (iframe.style.display === 'none') {
        iframe.style.display = 'block';
      } else {
        iframe.style.display = 'none';
      }
    }
    </script>
    </head>
    """
    return head


def set_version_branch(master_version_branch, master_series_module_name, firmware_info):
    """获取辅助设备分支版本信息，并添加主设备测试用例所在目录到sys.path环境变量，这样才能导入用例模块"""
    model_name = param_get_model_name()
    oem_name = param_get_oem_name()
    series_products = param_get_seriesproduct_name()
    # 获取辅助设备版本分支信息
    if '.' in master_version_branch:
        main_version_branch = master_version_branch.split('.')[0]
    else:
        main_version_branch = master_version_branch
    if main_version_branch:
        control_base_version_branch_file = config_get_series_module_sub_path(
            model_name, main_version_branch, 'ControlBase', 'version_branch.xml')
        module_series_test_data_dir = config_get_series_module_sub_path(
            model_name, main_version_branch, 'TestData')
        if os.path.exists(control_base_version_branch_file):
            version_branch_info_data = xml_read_sheet_data(control_base_version_branch_file)
        elif os.path.exists(module_series_test_data_dir):
            version_branch_info_data = xml_read_all_test_data(module_series_test_data_dir,
                                                              model_name, oem_name, 'version_branch.xml')
        else:
            version_branch_info_data = xml_read_all_test_data('%s\\testdata\\%s\\%s'
                                                              % (root_path, series_products, main_version_branch),
                                                              model_name, oem_name, 'version_branch.xml')
    else:
        # 未拉分支版本的testdata数据
        version_branch_info_data = xml_read_sheet_data('%s\\testdata\\%s\\version_branch.xml'
                                                       % (root_path, series_products))

    # 设置辅助设备分支版本，并根据使用的云平台分支版本，使用对应版本的云平台地址信息
    aklog_printf('辅助设备分支版本信息: %s' % version_branch_info_data)
    series_branch_name = '%s_branch' % master_series_module_name
    if not version_branch_info_data:
        return None
    version_branch_info = version_branch_info_data['version_branch'][0]
    if len(version_branch_info_data['version_branch']) > 1:
        for branch_info in version_branch_info_data['version_branch']:
            if branch_info[series_branch_name] == master_version_branch:
                version_branch_info = branch_info
                break

    if not version_branch_info:
        return None

    for x in version_branch_info:
        if firmware_info and x in firmware_info:
            version_branch_info[x] = firmware_info[x]
            continue

    # 将主设备分支目录添加到sys.path环境变量
    append_module_path(g_module_root_path, master_series_module_name, main_version_branch)

    param_put_version_branch_info(version_branch_info)
    return version_branch_info


def get_device_module_root_path(series_module_name=None):
    if not series_module_name:
        series = param_get_seriesproduct_name()
        series_module_name = config_get_series_module_name(series)
    product_line = param_get_product_line_name()

    version_branch = param_get_version_branch()
    if '.' in version_branch:
        version_branch = version_branch.split('.')[0]

    series_module_root_path = os.path.join(g_module_root_path, product_line, series_module_name, version_branch)
    if not os.path.exists(series_module_root_path):
        series_module_root_path = os.path.join(g_module_root_path, series_module_name, version_branch)
    if not os.path.exists(series_module_root_path):
        series_module_root_path = os.path.join(g_module_root_path, series_module_name)

    aklog_printf('module_root_path: %s' % series_module_root_path)
    return series_module_root_path


def parse_firmware_version_from_xml(modules_file='module_list.xml', build_env='local'):
    """
    解析firmware info xml文件
    Args:
        modules_file (str):
        build_env (str): 构建环境，=local表示本地环境手动执行、=jenkins表示使用jenkins来构建
    """
    aklog_printf()

    # 检查outputs目录大小，并清理旧文件
    File_process.check_directory_size_and_del_old_files(os.path.join(root_path, 'outputs'))

    # 获取config_ini信息
    config_ini_data = param_get_config_ini_data()
    if config_ini_data == 'unknown':
        config_ini_data = config_get_all_data_from_ini_file()
        param_put_config_ini_data(config_ini_data)

    # 获取构建者信息
    if build_env == 'local':
        build_user = config_get_value_from_ini_file('config', 'build_user')
        if build_user and build_user.strip() and '@' in build_user:
            aklog_info(f'构建者: {build_user}')
            param_put_build_user(build_user)
        else:
            aklog_error('config.ini配置文件中build_user为空')
            raise Exception('config.ini配置文件中build_user为空')

    # 根据升级包路径获取版本号
    firmware_info_data = param_get_firmware_info_data()
    if firmware_info_data == 'unknown':
        firmware_info_data = xml_read_sheet_data(param_get_firmware_info_path())
        param_put_firmware_info_data(firmware_info_data)
    firmware_info = firmware_info_data['firmware_info'][0]  # 获取版本号、升级包信息、版本分支信息
    param_put_firmware_info(firmware_info)

    if 'firmware_path' in firmware_info:
        firmware_path = firmware_info['firmware_path']
        if firmware_path:
            firmware_path = firmware_path.strip()
        param_put_firmware_path(firmware_path)
    firmware_version = firmware_info.get('firmware_version', '')
    if firmware_version:
        firmware_version = firmware_version.strip()

    # 获取启动文件所处的分支版本
    start_file_version_branch = None
    if os.path.basename(g_start_path) == 'Apps':
        start_file_version_branch = os.path.basename(os.path.dirname(g_start_path))

    # 家居产品如果没有指定版本号，将自动根据设备型号和IP获取（从device_info中获取指定型号的第一个设备）
    if not firmware_version:
        aklog_info('xml启动文件缺少firmware_version，将从device_info中自动获取设备信息，然后从设备获取实际版本号')
        model_name = firmware_info.get('model_name')
        if not model_name:
            raise ValueError(f'xml启动文件缺少"model_name", 请确认')
        # 初始化Log，并创建Log目录及文件
        aklog_init(model_name, log_level=5)

        series_products = config_get_series(model_name)
        product_line = config_get_product_line(series_products)
        series_list = ['HYPANELANDROID', 'HYPANELLARGE', 'HYPANELLINUX', 'HYPANELPRO', 'HYPANELSUPREME',
                       'SMARTPANEL', 'AKUBELAGATEWAY', 'BELAHOME']
        if product_line == 'SMARTHOME' and series_products in series_list:
            # 获取device_info
            module_series_test_data_dir = config_get_series_module_sub_path(
                model_name, start_file_version_branch, 'TestData')
            autotest_env_name = config_ini_data['environment']['autotest_env_name']
            if not autotest_env_name or autotest_env_name == 'None':
                device_info_name = 'device_info'
            else:
                device_info_name = 'device_info__%s' % autotest_env_name
            device_info_file = os.path.join(module_series_test_data_dir, model_name, 'NORMAL',
                                            f'{device_info_name}.xml')
            if not os.path.exists(device_info_file):
                device_info_file = os.path.join(module_series_test_data_dir, model_name, 'NORMAL', 'device_info.xml')
                if not os.path.exists(device_info_file):
                    device_info_file = os.path.join(module_series_test_data_dir, 'NORMAL', f'{device_info_name}.xml')
                    if not os.path.exists(device_info_file):
                        device_info_file = os.path.join(module_series_test_data_dir, 'NORMAL', 'device_info.xml')
            excel_data = xml_read_sheet_data(device_info_file)
            master_device_info = None
            devices_info = excel_data.get(device_info_name) or excel_data.get('device_info')
            for device_info in devices_info:
                if device_info.get('config_module') and model_name in device_info.get('config_module'):
                    master_device_info = device_info
                    break
            # 获取设备版本号
            master_device_config = config_parse_device_config(
                master_device_info['config_module'], master_device_info['device_name'])
            if series_products == 'BELAHOME':
                firmware_version = config_adb_get_android_apk_version(
                    master_device_info.get('deviceid'), 'com.akuvox.belahome')
            else:
                product_info = get_product_info_by_web_inf(
                    master_device_info, master_device_config, timeout=10)
                if product_info:
                    firmware_version = product_info.get('Product').get('FirmwareVersion')
            if firmware_version:
                aklog_info(f'从设备获取的版本号: {firmware_version}')
                firmware_info['firmware_version'] = firmware_version
            else:
                raise ValueError(f'xml启动文件缺少"firmware_version", 并且获取版本号失败，请检查device_info中设备信息')
        else:
            aklog_warn('xml启动文件缺少firmware_version，请检查')

    if not firmware_version:
        raise ValueError(f'xml启动文件缺少"firmware_version", 请确认')

    param_put_rom_version(firmware_version)
    # 解决方案合并所有机型，如果要跑指定型号，需要在firmware_info添加master_model配置
    master_model = firmware_info.get('master_model')
    if master_model and master_model.strip():
        param_put_master_model(master_model)

    # 根据版本号获取机型名称、OEM名称、web密码等版本信息
    versions = firmware_version.split('.')
    if len(versions) == 4:
        model_id = versions[0]
        param_put_model_id(model_id)
    else:
        model_id = None
    model_name = config_get_modelname(model_id)
    param_put_model_name(model_name)

    if len(versions) == 4:
        oem_id = versions[1]
        oem_name = config_get_oemname(oem_id)
    else:
        oem_name = 'NORMAL'
    param_put_oem_name(oem_name)

    # 初始化Log，并创建Log目录及文件
    aklog_init(model_name, log_level=5)

    if firmware_info.get('series_name'):
        series_products = firmware_info.get('series_name')
    else:
        series_products = config_get_series(model_name)
    param_put_seriesproduct_name(series_products)
    param_put_series_name_info(model_name, series_products)

    product_line = config_get_product_line(series_products)
    param_put_product_line_name(product_line)

    cloud_upgrade_model = config_get_cloud_upgrade_model(model_name)
    param_put_cloud_upgrade_model(cloud_upgrade_model)

    # 获取config_xml目录获取device_info设备信息
    all_config_device_info = xml_read_all_config_device_info()
    param_put_all_config_device_info(all_config_device_info)

    # 获取主测试设备的系列module目录名称和版本分支
    series_module_name = config_get_series_module_name(series_products)
    series_branch_name = '%s_branch' % series_module_name
    if series_branch_name in firmware_info:
        master_version_branch = firmware_info['%s_branch' % series_module_name]
    else:
        master_version_branch = config_parse_model_version_branch(model_name, firmware_version)
    aklog_info('主测试设备的系列版本分支: %s' % master_version_branch)
    if '.' in master_version_branch:
        main_version_branch = master_version_branch.split('.')[0]
    else:
        main_version_branch = master_version_branch
    if start_file_version_branch and start_file_version_branch != main_version_branch:
        aklog_fatal(f'当前使用的分支版本 {main_version_branch} 跟启动文件所在目录 "{g_start_path}" 不一致')
    param_put_version_branch(master_version_branch)
    # 获取辅助设备版本分支信息
    version_branch_info = set_version_branch(master_version_branch, series_module_name, firmware_info)

    # 获取主测试设备的module根目录，包括指定分支版本
    device_module_root_path = get_device_module_root_path(series_module_name)
    param_put_device_module_root_path(device_module_root_path)

    # 获取云平台相关信息，地址、帐号等
    autotest_env_name = config_get_value_from_ini_file('environment', 'autotest_env_name')
    cloud_server_name = config_get_value_from_ini_file('environment', 'cloud_server_name')
    if not autotest_env_name or autotest_env_name == 'None':
        cloud_info_env_name = 'cloud_info'  # version;  13205之前版本的用法.
    else:
        cloud_info_env_name = 'cloud_info__%s' % autotest_env_name
    aklog_printf('~~~~~~~~~~~~~~~~')
    aklog_info('Using Cloud Info of : %s' % cloud_info_env_name)
    cloud_info_file = os.path.join(g_config_path, 'libconfig_xml', 'cloud_info', '%s.xml' % cloud_info_env_name)
    cloud_info_data = xml_read_sheet_data(cloud_info_file)
    if not cloud_info_data:
        aklog_warn(r'\libconfig\libconfig_xml\cloud_info\ 目录下不存在 %s.xml 文件' % cloud_info_env_name)
        cloud_info_file = os.path.join(g_config_path, 'libconfig_xml', 'cloud_info', 'cloud_info.xml')
        cloud_info_data = xml_read_sheet_data(cloud_info_file).get('cloud_info')
    else:
        cloud_info_data = cloud_info_data.get(cloud_info_env_name)

    cloud_info = None
    if version_branch_info and 'cloud_branch' in version_branch_info:
        cloud_branch = version_branch_info['cloud_branch']
        param_put_cloud_version(cloud_branch)
        for info in cloud_info_data:
            if cloud_branch == info['version_branch'] and \
                    cloud_server_name and cloud_server_name == info.get('cloud_server_name'):
                aklog_info('Using Cloud Info of Sever Name: %s' % cloud_server_name)
                cloud_info = info
                break
        if not cloud_info:
            for info in cloud_info_data:
                if cloud_branch == info['version_branch']:
                    aklog_warn(
                        '可能是对讲云帐号信息xml文件中服务器名称不匹配，当前使用的对讲云帐号，服务器名称：%s，云版本：%s' % (
                            info.get('cloud_server_name'), cloud_branch))
                    cloud_info = info
                    break

    if not cloud_info:
        cloud_info = cloud_info_data[0]
    param_put_cloud_info(cloud_info)
    param_get_config_ini_data()['cloud_info'] = cloud_info

    # sdmc_info
    if not autotest_env_name or autotest_env_name == 'None':
        sdmc_info_env_name = 'sdmc_info'  # version;  13205之前版本的用法.
    else:
        sdmc_info_env_name = 'sdmc_info__%s' % autotest_env_name
    aklog_printf('~~~~~~~~~~~~~~~~')
    aklog_info('Using SDMC Info of : %s' % sdmc_info_env_name)
    sdmc_info_file = os.path.join(g_config_path, 'libconfig_xml', 'sdmc_info', '%s.xml' % sdmc_info_env_name)
    sdmc_info_data = xml_read_sheet_data(sdmc_info_file)
    if not sdmc_info_data:
        aklog_warn(r'\libconfig\libconfig_xml\cloud_info\ 目录下不存在 %s.xml 文件' % cloud_info_env_name)
        sdmc_info_file = os.path.join(g_config_path, 'libconfig_xml', 'sdmc_info', 'sdmc_info.xml')
        sdmc_info_data = xml_read_sheet_data(sdmc_info_file).get('sdmc_info')
    else:
        sdmc_info_data = sdmc_info_data.get(sdmc_info_env_name)

    # 获取家居云云平台相关信息，地址、帐号等
    akubela_cloud_server_name = firmware_info.get('akubela_cloud_server_name')
    if not akubela_cloud_server_name:
        akubela_cloud_server_name = config_get_value_from_ini_file('environment', 'akubela_cloud_server_name')
    if not autotest_env_name or autotest_env_name == 'None':
        akubela_cloud_info_env_name = 'akubela_cloud_info'  # version;  13205之前版本的用法.
    else:
        akubela_cloud_info_env_name = 'akubela_cloud_info__%s' % autotest_env_name
    aklog_printf('~~~~~~~~~~~~~~~~')
    aklog_info('Using Akubela Cloud Info of : %s' % akubela_cloud_info_env_name)

    akubela_cloud_info_file = os.path.join(
        g_config_path, 'libconfig_xml', 'akubela_cloud_info', '%s.xml' % akubela_cloud_info_env_name)
    akubela_cloud_info_data = xml_read_sheet_data(akubela_cloud_info_file)
    if not akubela_cloud_info_data:
        aklog_warn(
            r'\libconfig\libconfig_xml\akubela_cloud_info\ 目录下不存在 %s.xml 文件' % akubela_cloud_info_env_name)
        akubela_cloud_info_file = os.path.join(
            g_config_path, 'libconfig_xml', 'akubela_cloud_info', 'akubela_cloud_info.xml')
        akubela_cloud_info_data = xml_read_sheet_data(akubela_cloud_info_file).get('akubela_cloud_info')
    else:
        akubela_cloud_info_data = akubela_cloud_info_data.get(akubela_cloud_info_env_name)

    akubela_cloud_info = None
    if version_branch_info and 'AkubelaCloud_branch' in version_branch_info:
        akubela_cloud_branch = version_branch_info['AkubelaCloud_branch']
        for akubela_info in akubela_cloud_info_data:
            if akubela_cloud_branch == akubela_info['cloud_version_branch'] and \
                    akubela_cloud_server_name and akubela_cloud_server_name == akubela_info.get('cloud_server_name'):
                akubela_cloud_info = akubela_info
                aklog_info('Using Akubela Cloud Info of Sever Name: %s' % akubela_cloud_server_name)
                break
        if not akubela_cloud_info:
            for akubela_info in akubela_cloud_info_data:
                if akubela_cloud_branch == akubela_info['cloud_version_branch']:
                    aklog_warn(
                        '可能是家居云帐号信息xml文件中服务器名称不匹配，当前使用的家居云帐号，服务器名称：%s，云版本：%s' % (
                            akubela_info.get('cloud_server_name'), akubela_cloud_branch))
                    aklog_warn('检查config.ini中autotest_env_name配置项跟akubela_cloud_info中对应的环境名称是否一致，'
                               '检查config.ini或者启动xml配置文件的akubela_cloud_server_name指定的服务器名称是否正确，'
                               '检查akubela_cloud_info中对应环境中指定服务器名称的信息里面cloud_version_branch是否正确')
                    akubela_cloud_info = akubela_info
                    break

    if not akubela_cloud_info:
        aklog_warn(
            '可能是家居云帐号信息xml文件中服务器名称或者云版本不匹配，当前使用的家居云帐号，服务器名称：%s，云版本：%s' %
            (akubela_cloud_info_data[0].get('cloud_server_name'),
             akubela_cloud_info_data[0].get('cloud_version_branch')))
        aklog_warn('检查config.ini中autotest_env_name配置项跟akubela_cloud_info中对应的环境名称是否一致，'
                   '检查config.ini或者启动xml配置文件的akubela_cloud_server_name指定的服务器名称是否正确，'
                   '检查akubela_cloud_info中对应环境中指定服务器名称的信息里面cloud_version_branch是否正确')
        akubela_cloud_info = akubela_cloud_info_data[0]
    # aklog_printf('akubela_cloud_info: %r' % akubela_cloud_info)
    param_put_akubela_cloud_info(akubela_cloud_info)
    param_get_config_ini_data()['akubela_cloud_info'] = akubela_cloud_info

    # 获取config.ini的数据并设置部分参数强制开启或关闭
    config_get_ini_data_and_set_params()

    # 获取升级覆盖版本数量
    upgrade_cover_counts = param_get_upgrade_cover_counts()
    if upgrade_cover_counts is None:
        upgrade_cover_counts = config_get_value_from_ini_file('config', 'upgrade_cover_counts')
        if upgrade_cover_counts is not None:
            upgrade_cover_counts = int(upgrade_cover_counts)
        param_put_upgrade_cover_counts(upgrade_cover_counts)

    # 从testdata目录获取所有XML测试数据信息
    if main_version_branch:
        module_series_test_data_dir = config_get_series_module_sub_path(
            model_name, main_version_branch, 'TestData')
        if os.path.exists(module_series_test_data_dir):
            excel_data = xml_read_all_test_data(module_series_test_data_dir, model_name, oem_name)
        else:
            excel_data = xml_read_all_test_data(
                '%s\\testdata\\%s\\%s' % (root_path, series_products, main_version_branch), model_name, oem_name)
    else:
        excel_data = xml_read_all_excel_data('%s\\testdata\\%s' % (root_path, series_products))

    if 'version_branch' in excel_data and version_branch_info:
        excel_data['version_branch'][0] = version_branch_info

    if 'device_info' in firmware_info_data and firmware_info_data['device_info']:
        # 如果启动firmware_info xml文件有带上device_info，则将testdata的device_info替换掉
        excel_data['device_info'] = firmware_info_data['device_info']

    param_put_excel_data(excel_data)
    param_get_excel_data()['sdmc_info'] = sdmc_info_data

    # 解析测试用例模块
    modules = {}
    modules = config_parse(model_name, oem_name, main_version_branch, modules, modules_file)
    param_put_modules(modules)

    # 解析主设备的device_config
    config_module = config_parse_config_module(model_name, oem_name)
    param_put_config_module(config_module)
    if master_model:
        if '+' in master_model:
            master_model = master_model.split('+')[0]
        device_config_master = config_parse_device_config_by_model_and_oem(master_model, 'NORMAL')
    else:
        device_config_master = config_parse_device_config(config_module)
    param_put_device_config(device_config_master)

    # 解析所有设备device_config，获取设备类型和型号数量
    check_device_count_enable = firmware_info_data['launch_config'][0].get('check_device_count_enable')
    check_device_count_enable = True if str(check_device_count_enable) == '1' else False
    param_put_check_device_count_enable(check_device_count_enable)
    if check_device_count_enable:
        device_count_info = {
            'default': {},
            'product_type': {},
            'product_model': {},
            'series': {},
            'model': {}
        }
        for device_info in param_get_excel_data()['device_info']:
            config_module = device_info.get('config_module')
            if not config_module:
                continue
            device_config = config_parse_device_config(config_module)
            product_type_name = device_config.get_product_type_name()
            product_model_name = device_config.get_product_model_name()
            series_product_name = device_config.get_series_product_name()
            model_name = device_config.get_model_name()
            if product_type_name:
                if product_type_name not in device_count_info['product_type']:
                    device_count_info['product_type'][product_type_name] = 1
                else:
                    device_count_info['product_type'][product_type_name] += 1
            if product_model_name:
                if product_model_name not in device_count_info['product_model']:
                    device_count_info['product_model'][product_model_name] = 1
                else:
                    device_count_info['product_model'][product_model_name] += 1
            if series_product_name:
                if series_product_name not in device_count_info['series']:
                    device_count_info['series'][series_product_name] = 1
                else:
                    device_count_info['series'][series_product_name] += 1
            if model_name:
                if model_name not in device_count_info['model']:
                    device_count_info['model'][model_name] = 1
                else:
                    device_count_info['model'][model_name] += 1
        if product_line == 'SMARTHOME':
            device_count_info['default']['USERWEB'] = 1  # 家居设备环境默认有一个家庭中心和USERWEB
        aklog_info(f'device_count_info: {device_count_info}')
        param_put_device_count_info(device_count_info)

    # 根据机型名称和OEM获取测试机型的基类模块
    base_module = base_module_adapter()
    param_put_base_module(base_module)
    # 实例化ControlBase
    control_base = control_base_adapter()
    if control_base:
        param_put_control_base(control_base)


def parse_get_upgrade_cover_data():
    upgrade_cover_data = param_get_excel_data()['UpgradeCover']
    if param_get_upgrade_cover_counts() == 0:
        upgrade_cover_counts = len(upgrade_cover_data)
    else:
        upgrade_cover_counts = min(len(upgrade_cover_data), param_get_upgrade_cover_counts())
    upgrade_cover_data = upgrade_cover_data[0:upgrade_cover_counts]
    return upgrade_cover_data


def __download_firmware(local_path, remote_path, rom_version=None):
    """将监控路径下的升级包拷贝到本地目录"""
    aklog_printf()
    if not rom_version:
        rom_version = param_get_rom_version()
    # 如果是从远程目录下载升级包，则增加文件锁，其他进程得等待该进程下载完成后，才能下载，也就是同一时间只能有一个在下载
    temp_dir = tempfile.gettempdir()
    lock_file_path = os.path.join(temp_dir, 'download_firmware.lock')
    lock_timeout = 3600
    lock = FileLock(lock_file_path, timeout=lock_timeout)  # 设置超时时间为3600秒

    local_dir, local_file_name = os.path.split(local_path)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    # 如果锁文件在启动前就已经存在，尝试删除旧的锁文件
    if os.path.exists(lock_file_path):
        try:
            lock_file_age = time.time() - os.path.getctime(lock_file_path)
            if lock_file_age > lock_timeout:
                aklog_printf(f"锁文件存在时间超过 {lock_timeout} 秒，删除旧的锁文件")
                os.remove(lock_file_path)
        except Exception as e:
            aklog_printf(f"无法删除旧的锁文件: {lock_file_path}, 错误: {e}")

    download_result = False
    try:
        with lock:
            aklog_info(f'准备开始下载升级包 {local_file_name}')

            # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
            if remote_path.startswith('ftp://') or remote_path.startswith(r'\\') or remote_path.startswith('//'):
                cmd_waiting_for_network_rate_to_drop()

            if 'ftp://' in remote_path:
                aklog_printf("将升级包从FTP服务器下载到本地目录")
                ftp_info = get_ftp_info_from_url(remote_path)
                ftp_connect_mode = False  # False为PORT模式
                for k in range(2):
                    ftp_client = FtpClient(ftp_info['host'], ftp_info['port'], ftp_info['user_name'],
                                           ftp_info['password'])
                    ftp_client.login(ftp_connect_mode)
                    download_result = ftp_client.download_file(local_path, ftp_info['remote_file'])
                    ftp_client.close()
                    if download_result:
                        break
                    else:
                        ftp_connect_mode = True
                        continue
            elif 'http://' in remote_path:
                aklog_info('从http服务器下载到本地目录')
                print(local_path)
                r = requests.get(remote_path, timeout=600)
                with open(local_path, 'wb') as f:
                    f.write(r.content)
                if os.path.exists(local_path):
                    download_result = True
            else:
                aklog_printf("将升级包拷贝到本地目录")
                remote_path = remote_path.replace('192.168.77.5', '192.168.10.75')

                if remote_path.startswith('//'):
                    # //也当做远程共享文件夹路径，转为反斜杠
                    remote_path = remote_path.replace('/', '\\')
                elif not remote_path.startswith('C:') and not remote_path.startswith('D:') and \
                        not remote_path.startswith('E:') and not remote_path.startswith('F:') and \
                        not remote_path.startswith('G:') and not remote_path.startswith('H:'):
                    # 如果不是电脑本地的路径，则当做远程路径
                    for i in range(3):
                        if remote_path.startswith('\\\\'):
                            break
                        remote_path = '\\' + remote_path
                        continue

                ext = os.path.splitext(local_path)[1]
                if remote_path.endswith(ext) and rom_version not in remote_path:
                    # 提供的升级包路径是完整的，但是错误的
                    aklog_warn('提供的升级包路径 %s 不正确，将从上一级目录开始遍历去查找' % remote_path)
                    remote_path = os.path.dirname(remote_path)

                if not remote_path.endswith(ext):
                    # 如果路径结尾不是文件扩展名，则提供的升级包路径不完整，要遍历目录查找
                    firmware_file = rom_version + ext
                    aklog_warn('提供的升级包路径 %s 不完整' % remote_path)
                    aklog_warn('将遍历整个目录及子目录查找 %s 升级包' % firmware_file)
                    full_remote_path = File_process.get_file_with_filename_from_path(remote_path, firmware_file)
                    if not full_remote_path:
                        # 递归往上遍历目录查找升级包
                        parent_path = os.path.dirname(remote_path)
                        while not full_remote_path and parent_path and os.path.dirname(parent_path) != parent_path:
                            aklog_warn('升级包未找到，在上一级目录 %s 重新遍历查找' % parent_path)
                            full_remote_path = File_process.get_file_with_filename_from_path(parent_path, firmware_file)
                            parent_path = os.path.dirname(parent_path)

                    if not full_remote_path:
                        aklog_warn('升级包未找到，可能是文件名带有前缀或后缀，重新查找')
                        full_remote_path = File_process.get_firmware_by_version_from_path(
                            remote_path, firmware_file)
                        if not full_remote_path:
                            # 递归往上遍历目录查找升级包
                            parent_path = os.path.dirname(remote_path)
                            while not full_remote_path and parent_path and os.path.dirname(parent_path) != parent_path:
                                aklog_warn('升级包未找到，在上一级目录 %s 重新遍历查找' % parent_path)
                                full_remote_path = File_process.get_firmware_by_version_from_path(
                                    parent_path, firmware_file)
                                parent_path = os.path.dirname(parent_path)

                    if not full_remote_path:
                        aklog_error(f'升级包 {local_file_name} 未找到')

                    else:
                        aklog_printf('查找到的升级包路径: %s' % full_remote_path)
                else:
                    full_remote_path = remote_path

                if full_remote_path:
                    for x in range(3):
                        download_result = File_process.copy_file(full_remote_path, local_path)
                        if download_result:
                            break
                        elif x == 0:
                            aklog_warn('如果升级包路径正确，但下载失败，可能是访问共享文件夹有异常，先用命令访问下')
                            try:
                                remote_root_path = re.match(r'^\\\\[^\\]+', full_remote_path).group()
                                sub_process_exec_command('net use %s' % remote_root_path)
                                sub_process_exec_command('net view %s' % remote_root_path)
                            except:
                                aklog_debug(traceback.format_exc())
                            continue
                        elif x == 1:
                            firmware_file = rom_version + ext
                            remote_path = os.path.dirname(remote_path)
                            aklog_warn("升级包下载失败，可能是升级包路径不正确")
                            aklog_warn('将递归往上遍历整个目录及子目录查找 %s 升级包' % firmware_file)
                            full_remote_path = File_process.get_file_with_filename_from_path(remote_path, firmware_file)
                            if not full_remote_path:
                                # 递归往上遍历目录查找升级包
                                parent_path = os.path.dirname(remote_path)
                                while not full_remote_path and parent_path and os.path.dirname(
                                        parent_path) != parent_path:
                                    aklog_warn('升级包未找到，在上一级目录 %s 重新遍历查找' % parent_path)
                                    full_remote_path = File_process.get_file_with_filename_from_path(
                                        parent_path, firmware_file)
                                    parent_path = os.path.dirname(parent_path)

                            if not full_remote_path:
                                aklog_error(f'升级包 {local_file_name} 未找到')
                                break
                            else:
                                aklog_printf('查找到的升级包路径: %s' % full_remote_path)
                                continue

            if download_result:
                aklog_printf(f'升级包 {local_file_name} 下载完成')
    except Timeout:
        aklog_printf(f"锁文件存在时间超过 {lock_timeout} 秒，无法获取锁")
    except Exception as e:
        aklog_printf(f"遇到未知异常, 程序退出! {e}")
    return download_result


def download_firmware(local_path, remote_path, rom_version=None):
    if isinstance(remote_path, list):
        for path in remote_path:
            ret = __download_firmware(local_path, path, rom_version)
            if ret:
                return True
        return False
    else:
        return __download_firmware(local_path, remote_path, rom_version)


def format_pass_rate(rate):
    for digits in range(2, 5):
        rounded = round(rate, digits)
        # 判断四舍五入后整数部分是否未多进一位
        if int(rounded) == int(rate):
            return f"{rounded:.{digits}f}%"
    # 如果都不满足，最后保留4位
    return f"{round(rate, 4):.4f}%"


def generate_jenkins_distribute_report_file():
    """生成分布式构建后合并的测试报告"""
    aklog_printf('分布式构建后合并测试报告')

    jenkins_merge_report_dir = param_get_jenkins_report_dir()
    result_summary = dict()
    body = ''
    body_iframe = ''
    module_results_content = ''
    case_results_content = ''
    html_count = 0

    for job_name in os.listdir(jenkins_merge_report_dir):
        sub_job_report_dir = os.path.join(jenkins_merge_report_dir, job_name)
        if not os.path.isdir(sub_job_report_dir):
            continue
        sub_job_report_file = os.path.join(sub_job_report_dir, 'jenkins-report.html')
        sub_job_result_summary_file = os.path.join(sub_job_report_dir, 'results_summary.txt')
        result_summary_file_lines = File_process.get_file_lines(sub_job_result_summary_file)
        # 获取测试结果并合计汇总
        if result_summary_file_lines:
            for line in result_summary_file_lines:
                if line and ':' in line:
                    key = line.split(':')[0].strip()
                    if not key or key == 'test_pass_rate':
                        continue
                    else:
                        value = int(line.split(':')[1].strip())
                        if key not in result_summary:
                            result_summary[key] = value
                        else:
                            result_summary[key] += value
            total_count_without_skip = result_summary['test_case_all_counts'] - result_summary['test_case_skip_counts']
            if total_count_without_skip > 0:
                result_summary['test_pass_rate'] = format_pass_rate(
                    result_summary['test_case_pass_counts'] / total_count_without_skip * 100)
            else:
                result_summary['test_pass_rate'] = 0.0

        # 获取Module用例模块级测试结果
        sub_job_result_file = os.path.join(sub_job_report_dir, 'module_results.txt')
        sub_job_result_file_lines = File_process.get_file_lines(sub_job_result_file)
        if sub_job_result_file_lines:
            for line in sub_job_result_file_lines:
                if line:
                    module_results_content += line

        # 获取用例级测试结果
        sub_job_case_result_file = os.path.join(sub_job_report_dir, 'case_results.txt')
        sub_job_case_result_file_lines = File_process.get_file_lines(sub_job_case_result_file)
        if sub_job_case_result_file_lines:
            for line in sub_job_case_result_file_lines:
                if line:
                    case_results_content += line

        report_file_list = File_process.get_files_with_ext_from_path(sub_job_report_dir, '.html')

        if len(report_file_list) > 1:
            # 如果html报告文件不止一个，说明当前报告已经因为较大而通过iframe方式合并了，那么需要将子文件直接添加到最终的报告文件里
            file2_lines = File_process.get_file_lines(sub_job_report_file)
            for line2 in file2_lines:
                if '<iframe' in line2:
                    html_count += 1
                    iframe_name = '''<p onclick="toggleIframe('Iframe%s')" style="background-color:#F1A058;">Jenkins工程名称: %s</p>''' % (
                        html_count, job_name)
                    body_iframe += iframe_name
                    new_line = line2.replace('<iframe src="',
                                             '<iframe id="Iframe%s" src="./%s/' % (html_count, job_name))
                    body_iframe += new_line
        elif len(report_file_list) == 1:
            html_count += 1
            iframe_name = '''<p onclick="toggleIframe('Iframe%s')" style="background-color:#F1A058;">Jenkins工程名称: %s</p>''' % (
                html_count, job_name)
            body_iframe += iframe_name
            sub_job_report_file_relative_path = './%s/%s' % (job_name, 'jenkins-report.html')
            iframe = '<iframe src="%s" width="1920" height="1080" id="Iframe%s"></iframe>\n' % (
                sub_job_report_file_relative_path, html_count)
            body_iframe += iframe

    intercom_report_to_server_by_jenkins(result_summary)

    report_ret = f"""<button style="background-color:#F1A058;" onclick="toggleIframe('count')">展开/折叠统计区</button>\n""" \
                 f'<div id="count">\n' \
                 f'<p>所有用例总数: {result_summary.get("total_case_counts")} </p>\n' \
                 f'<p>已执行用例数: {result_summary.get("test_case_all_counts")} </p>\n' \
                 f'<p>用例通过: {result_summary.get("test_case_pass_counts")} </p>\n' \
                 f'<p>用例失败: {result_summary.get("test_case_fail_counts")} </p>\n' \
                 f'<p>用例错误: {result_summary.get("test_case_error_counts")} </p>\n' \
                 f'<p>用例跳过: {result_summary.get("test_case_skip_counts")} </p>\n' \
                 f'<p>通过率: {result_summary.get("test_pass_rate")}%% </p>\n' \
                 f'</div>\n\n'
    body += report_ret
    body += body_iframe
    head = get_fold_head()
    report_content = """<html>\n<head>\n%s</head>\n<body>\n%s</body>\n</html>""" % (head, body)

    # 生成合并测试报告文件
    jenkins_merge_report_file = os.path.join(jenkins_merge_report_dir, 'jenkins-report.html')
    aklog_printf(jenkins_merge_report_file)
    with open(jenkins_merge_report_file, 'w', encoding='utf-8') as fp:
        fp.write(report_content)

    # 生成合并测试结果文件
    module_results_file = os.path.join(jenkins_merge_report_dir, 'module_results.txt')
    with open(module_results_file, 'w', encoding='utf-8') as fp:
        fp.write(module_results_content)

    case_results_file = os.path.join(jenkins_merge_report_dir, 'case_results.txt')
    with open(case_results_file, 'w', encoding='utf-8') as fp:
        fp.write(case_results_content)


def generate_jenkins_distribute_firmware_info_fail():
    aklog_printf('分布式构建后合并失败的FirmwareInfo XML文件')

    jenkins_merge_report_dir = param_get_jenkins_report_dir()
    merge_fail_modules = ''
    jenkins_merge_firmware_info_fail = os.path.join(jenkins_merge_report_dir, 'FirmwareInfo_Fail.xml')
    File_process.copy_file(param_get_firmware_info_path(), jenkins_merge_firmware_info_fail)
    for job_name in os.listdir(jenkins_merge_report_dir):
        sub_job_report_dir = os.path.join(jenkins_merge_report_dir, job_name)
        if not os.path.isdir(sub_job_report_dir):
            continue
        for file in os.listdir(sub_job_report_dir):
            if '_fail.xml' in file:
                sub_job_firmware_info_fail_file = os.path.join(sub_job_report_dir, file)
                firmware_info_data = xml_read_sheet_data(sub_job_firmware_info_fail_file)
                fail_modules = firmware_info_data['test_cases'][0]['modules']
                aklog_printf(fail_modules)
                merge_fail_modules += fail_modules
    if merge_fail_modules.strip():
        xml_add_attributes(jenkins_merge_firmware_info_fail, 'test_cases', {'modules': merge_fail_modules})
    else:
        aklog_printf('测试结果没有失败，删除FirmwareInfo_Fail.xml文件')
        File_process.remove_file(jenkins_merge_firmware_info_fail)


def send_email_test_report_by_jenkins_build(send_email_enable=True, send_work_weixin_enable=False):
    """HTML测试报告截图"""
    aklog_printf('发送测试报告邮件')
    model_name = param_get_model_name()
    oem_name = param_get_oem_name()
    rom_version = param_get_rom_version()
    device_config_master = param_get_device_config()
    report_file_url = param_get_jenkins_report_url()

    report_file = param_get_jenkins_report_dir() + 'jenkins-report.html'

    # 更新chrome driver
    if config_get_value_from_ini_file('config', 'chrome_driver_auto_update_enable'):
        ChromeDriverUpdate.chrome_driver_auto_update()

    report_browser = libbrowser()
    report_img_file = aklibreport_html(report_browser, report_file).report_html_screenshot()

    if param_get_email_receivers():  # 邮件接收人员由XML文件指定，否则用device_config默认名单
        email_receivers = param_get_email_receivers()
    else:
        email_receivers = device_config_master.get_email_receivers()
        if param_get_added_email_receivers():
            email_receivers.extend(param_get_added_email_receivers())  # 增加发送人员

    if send_email_enable:
        email_title = model_name + ' - ' + oem_name + ' - ' + rom_version + ' - 自动测试报告'
        email_content = '%s - %s - %s - 自动测试报告： <a href="%s">请点击链接查看</a>' \
                        % (model_name, oem_name, rom_version, report_file_url)
        send_email_html = SendEmailHandler()
        for i in range(0, 3):
            if not send_email_html.send_email_with_img_attachment(
                    email_receivers,
                    email_title,
                    email_content,
                    report_img_file):
                time.sleep(10)
            else:
                break

    # 是否发送企业微信消息
    if send_work_weixin_enable:
        msg_content = "%s - %s - %s - 自动测试报告:\n%s" \
                      % (model_name, oem_name, rom_version, report_file_url)
        robot_send_text_msg(msg_content, *email_receivers)
        robot_send_image(report_img_file, *email_receivers)


def get_share_http_report_dir_url():
    """
    获http访问测试报告目录的URL
    """
    global __report_dir_url
    if __report_dir_url is not None:
        return __report_dir_url
    if not param_get_send_work_weixin_state() and not param_get_send_email_state():
        return __report_dir_url
    root_path_url = config_get_value_from_ini_file('environment', 'root_path_url')
    shared_folder_root_dir = config_get_value_from_ini_file('environment', 'shared_folder_root_dir')
    if root_path_url.startswith('http://') and shared_folder_root_dir:
        root_path_url = root_path_url.rstrip('/')  # 去除末尾斜杠
        autotest_env_name = config_get_value_from_ini_file('environment', 'autotest_env_name')
        if autotest_env_name:
            # 如果有指定环境名称，将创建环境名称目录，区分不同报告文件夹
            root_path_url = f"{root_path_url}/{autotest_env_name}"
        __report_dir_url = aklog_get_result_dir().replace(root_path, root_path_url).replace('\\', '/')
    else:
        __report_dir_url = ''
    return __report_dir_url


def send_report_file_to_http_server(report_file):
    """
    将测试报告复制到共享文件夹，然后可以用HTTP方式直接在浏览器打开
    共享文件夹服务器必须要有HTTP服务器，且根目录一致
    会将outputs完整路径复制到共享文件夹
    Args:
        report_file ():
    """
    root_path_url = config_get_value_from_ini_file(
        'environment', 'root_path_url')
    shared_folder_root_dir = config_get_value_from_ini_file(
        'environment', 'shared_folder_root_dir')
    if root_path_url.startswith('http://') and shared_folder_root_dir:
        if root_path_url.endswith('/'):
            root_path_url = root_path_url[0:-1]
        if shared_folder_root_dir.endswith('\\'):
            shared_folder_root_dir = shared_folder_root_dir[0:-1]

        if root_path_url.split('/')[-1] != shared_folder_root_dir.split('\\')[-1]:
            root_path_url = root_path_url + '/' + shared_folder_root_dir.split('\\')[-1]

        autotest_env_name = config_get_value_from_ini_file(
            'environment', 'autotest_env_name')
        if autotest_env_name:
            # 如果有指定环境名称，将创建环境名称目录，区分不同报告文件夹
            root_path_url = root_path_url + '/' + autotest_env_name
            shared_folder_root_dir = shared_folder_root_dir + '\\' + autotest_env_name

        report_file_url = aklog_get_report_url(root_path_url)
        report_dir, report_file_name = os.path.split(report_file)

        # 将测试报告目录复制到该共享文件夹下，然后配合root_path_url，可以直接打开测试报告
        ret = File_process.copy_folder_to_network_share(
            report_dir, shared_folder_root_dir, root_path)
        if ret:
            aklog_info(f'测试报告链接： {report_file_url}')
            return report_file_url
    return ''


def parse_results_file(input_file: str, case_output_file: str, module_output_file: str):
    """解析测试结果文件并统计用例级和模块级执行次数、通过数、失败数、错误数、通过率

    Args:
        input_file (str): 输入文件路径，如 results.txt
        case_output_file (str): 按用例级输出文件路径，如 case_results.txt
        module_output_file (str): 按模块（用例类）输出文件路径，如 module_results.txt
    """
    # 用例级统计
    case_stats = defaultdict(lambda: {"pass": 0, "fail": 0, "error": 0})
    # 模块级统计
    module_stats = defaultdict(lambda: {"pass": 0, "fail": 0, "error": 0})

    # 匹配日志行的正则
    pattern = re.compile(
        r"-\s+(Pass|Fail|Error)\s+-\s+[^(]+\((?P<case_full>[^)]+)\)"
    )

    input_path = Path(input_file)
    if not input_path.exists():
        aklog_error(f"测试结果文件不存在: {input_file}")
        return

    aklog_debug(f"开始解析测试结果文件: {input_file}")

    with input_path.open("r", encoding="utf-8", errors='ignore') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                result = match.group(1).lower()  # pass/fail/error
                case_full = match.group("case_full")
                parts = case_full.split(".")

                if len(parts) >= 3:
                    module_name = parts[1]  # 类名
                    case_name = ".".join(parts[1:])  # 类名 + 方法名
                else:
                    aklog_error(f"无法解析行: {line.strip()}")
                    continue

                # 更新用例级统计
                if result in case_stats[case_name]:
                    case_stats[case_name][result] += 1

                # 更新模块级统计
                if result in module_stats[module_name]:
                    module_stats[module_name][result] += 1

    # 写入用例级结果
    case_path = Path(case_output_file)
    with case_path.open("w", encoding="utf-8") as out:
        for case_name, stats in case_stats.items():
            total = sum(stats.values())
            pass_count = stats["pass"]
            fail_count = stats["fail"]
            error_count = stats["error"]
            pass_rate = (pass_count / total * 100) if total > 0 else 0.0
            pass_rate = format_pass_rate(pass_rate)
            out.write(f"{case_name}:\n")
            out.write(f"执行次数: {total}\n")
            out.write(f"通过次数: {pass_count}\n")
            out.write(f"失败次数: {fail_count}\n")
            out.write(f"错误次数: {error_count}\n")
            out.write(f"通过率: {pass_rate}\n")

    # 写入模块级结果
    module_path = Path(module_output_file)
    with module_path.open("w", encoding="utf-8") as out:
        for module_name, stats in module_stats.items():
            total = sum(stats.values())
            pass_count = stats["pass"]
            fail_count = stats["fail"]
            error_count = stats["error"]
            pass_rate = (pass_count / total * 100) if total > 0 else 0.0
            pass_rate = format_pass_rate(pass_rate)
            out.write(f"{module_name}:\n")
            out.write(f"执行次数: {total}\n")
            out.write(f"通过次数: {pass_count}\n")
            out.write(f"失败次数: {fail_count}\n")
            out.write(f"错误次数: {error_count}\n")
            out.write(f"通过率: {pass_rate}\n")

    aklog_debug(f"用例统计结果已输出到: {case_output_file}")
    aklog_debug(f"模块统计结果已输出到: {module_output_file}")


def send_email_or_work_weixin(report_file, model_name, oem_name, rom_version, test_result=False, report_file_url=None):
    """发送邮件或者企业微信通知"""
    if not param_get_send_work_weixin_state() and not param_get_send_email_state():
        return
    email_receivers = param_get_email_receivers()
    build_user = param_get_build_user()
    if not email_receivers and not build_user:
        aklog_warn('收件人和构建者均为空，无法发送邮件或企业微信')
        return
    if build_user and build_user not in email_receivers:
        email_receivers.append(build_user.strip())

    if report_file_url is None:
        report_file_url = send_report_file_to_http_server(report_file)
    if not report_file_url:
        report_file_url = report_file

    autotest_env_name = config_get_value_from_ini_file('environment', 'autotest_env_name')

    # region Email发送测试报告
    report_img_file = None
    if param_get_send_email_state():
        # HTML测试报告截图
        time.sleep(5)
        report_browser = libbrowser()
        report_img_file = aklibreport_html(report_browser, report_file).report_html_screenshot()

        send_email_html = SendEmailHandler()
        email_title = model_name + ' - ' + oem_name + ' - ' + rom_version + ' - 自动测试报告'
        if test_result:
            email_title += '【成功】'
        else:
            email_title += '【失败】'
        send_email_report_type = config_get_value_from_ini_file('config', 'send_email_report_type')
        if send_email_report_type == 'file':  # file or url, 发送测试报告邮件是发送附件还是URL
            email_content = '%s - %s - %s - 自动测试报告' % (model_name, oem_name, rom_version)
            if autotest_env_name:
                email_content += f' ({autotest_env_name})'
            for i in range(0, 3):
                if not send_email_html.send_email_with_img_attachment(
                        email_receivers,
                        email_title,
                        email_content,
                        report_img_file,
                        report_file):
                    time.sleep(10)
                else:
                    break
        else:
            root_path_url = config_get_value_from_ini_file('environment', 'root_path_url')
            if root_path_url.startswith('file:///'):
                report_file_url = 'file:///{}'.format(report_file.replace('\\', '/'))
                email_content = """
                            %s - %s - %s - 自动测试报告
                            <a href="%s">请点击链接查看测试报告文件</a> 
                            (注意：此链接为构建者本地文件路径，非构建者无法打开)
                            """ % (model_name, oem_name, rom_version, report_file_url)
            else:
                email_content = """%s - %s - %s - 自动测试报告, <a href="%s">请点击链接查看</a>""" \
                                % (model_name, oem_name, rom_version, report_file_url)
            if autotest_env_name:
                email_content += f' ({autotest_env_name})'
            for i in range(0, 3):
                if not send_email_html.send_email_with_img_attachment(
                        email_receivers,
                        email_title,
                        email_content,
                        report_img_file):
                    time.sleep(10)
                else:
                    break
    # endregion

    # region 是否发送企业微信消息
    if param_get_send_work_weixin_state():
        msg_content = "%s - %s - %s - 自动测试报告" % (model_name, oem_name, rom_version)
        if test_result:
            msg_content += '【成功】'
        else:
            msg_content += '【失败】'
        if autotest_env_name:
            msg_content += f' ({autotest_env_name})'

        send_email_report_type = config_get_value_from_ini_file('config', 'send_email_report_type')
        if send_email_report_type == 'file':  # file or url, 发送测试报告给企业微信是发送附件还是URL
            robot_send_text_msg(msg_content, *email_receivers)
            robot_send_file(report_file, *email_receivers)
        else:
            # HTML测试报告截图
            if not report_img_file:
                report_browser = libbrowser()
                report_img_file = aklibreport_html(report_browser, report_file).report_html_screenshot()
            msg_content += f':\n{report_file_url}'
            robot_send_text_msg(msg_content, *email_receivers)
            robot_send_image(report_img_file, *email_receivers)
    # endregion


def check_stop_exec_enable():
    if param_get_stop_process_event() and param_get_stop_process_event().is_set():
        aklog_info('准备停止进程，退出执行')
        param_put_stop_exec_enable(True)
        return True
    if param_get_stop_exec_enable():
        aklog_info('退出执行')
        return True

    # 可以手动修改temp.ini配置文件，把stop_exec_enable设置为True，退出执行
    if not param_get_temp_ini_file():
        temp_config_file = os.path.join(g_config_path, 'temp.ini')
        param_put_temp_ini_file(temp_config_file)
    readconfig = ReadConfig(param_get_temp_ini_file())
    stop_exec_enable_config = readconfig.get_value('config', 'stop_exec_enable')
    if stop_exec_enable_config is True:
        aklog_printf('手动停止，退出执行')
        readconfig.modify_config('config', 'stop_exec_enable',
                                 'False').write_config()
        return True
    return False


def unittest_stop_run():
    aklog_remove()
    param_put_stop_exec_enable(False)
    if not param_get_scheduled_execution_enable():
        param_put_running_state(False)
        launch_window_app = param_get_launch_window_app()
        if launch_window_app:
            launch_window_app.trigger_restore()
            launch_window_app.trigger_pause_run('resume')


def auto_test_start():
    """用于触发测试直接执行，多机型一起测试环境，也用于Jenkins构建执行"""
    aklog_printf('准备开始测试')
    try:
        firmware_info_path = param_get_firmware_info_path()
        model_name = param_get_model_name()
        oem_name = param_get_oem_name()
        series_products = param_get_seriesproduct_name()
        product_line = param_get_product_line_name()
        rom_version = param_get_rom_version()
        report_model_name = param_get_firmware_info().get('report_model_name')
        if not report_model_name:
            report_model_name = model_name
        if param_get_master_model() and 'SOLUTION' not in param_get_master_model():
            report_model_name = param_get_master_model()
            if '+' in report_model_name:
                report_model_name = report_model_name.split('+')[0]
            if param_get_firmware_info().get(f'{report_model_name}_version'):
                rom_version = param_get_firmware_info().get(f'{report_model_name}_version')

        test_case_sql = SmartHomeTestCaseSql()

        # 是否发送邮件
        send_email_enable = param_get_send_email_state()

        # 设置测试次数, 主要用于手动测试，默认次数1，test_counts会把每次测试结果写入到同一个log和report文件里，适合单个用例压力测试
        g_test_counts = param_get_test_counts()

        # 测试多少遍，主要用于手动测试，默认次数1，test_times会每测试一遍都会创建新的Result目录写log和report文件，适合多个用例循环测试
        test_times = param_get_test_times()

        # 设置是否随机乱序执行
        test_random = param_get_test_random_state()

        # 设置用例是否均衡执行
        test_case_balance_enable = param_get_test_case_balance_enable()

        # 跳过下载升级包
        skip_download_firmware = param_get_skip_download_firmware_state()

        # 失败重测是否只保存最后一次结果到测试报告
        save_last_try = param_get_save_last_try_state()

        # 失败重测次数
        retry_counts = param_get_retry_counts()

        # 是否发送测试结果汇总到服务器
        send_test_results_summary_enable = param_get_send_test_results_summary_enable()

        # 是否单个用例执行完就写入测试报告，False表示整个用例类执行完才写入测试报告
        exec_one_case_to_report_enable = param_get_exec_one_case_to_report_enable()

        # 创建测试套件，并开始执行测试用例
        module_list = param_get_module_list()
        if module_list:
            modules_dict = config_parse_modules_from_xml(module_list)
        else:
            modules = param_get_modules()
            if not modules:
                aklog_printf("用例解析失败，请检查选择的测试用例或测试套件是否正确")
                aklog_remove()
                # 删除从监控目录复制到本地的xml文件
                File_process.remove_file(firmware_info_path)
                return False

            adapter = module_case_adapter()
            modules_dict = adapter.create_test_case_dict()

        aklog_printf('modules_dict : %r' % modules_dict)

        if not modules_dict:
            aklog_printf("用例解析失败，请检查选择的测试用例或测试套件是否正确")
            aklog_remove()
            # 删除从监控目录复制到本地的xml文件
            File_process.remove_file(firmware_info_path)
            return False

        # 过滤Jenkins节点用例名称列表
        if param_get_jenkins_distribute_enable():
            modules_dict = config_parse_jenkins_module_dict(param_get_jenkins_job_name(), modules_dict)

        # 如果modules_dict是Jenkins过滤之后才为空，不当成失败，返回True
        if not modules_dict:
            aklog_printf("用例解析失败，请检查选择的测试用例或测试套件是否正确")
            aklog_remove()
            # 删除从监控目录复制到本地的xml文件
            File_process.remove_file(firmware_info_path)
            return True

        # 获取总用例数量，只计算测试一遍的用例数量
        total_case_counts = 0
        for x in modules_dict:
            total_case_counts += len(modules_dict[x])
        module_class_list = sorted(modules_dict)  # 取key值并加到用例模块名称列表

        common_module_class_list = []
        common_module_list = []
        force_order_class_list = []
        force_order_class_info = {}
        if param_get_suite_list() != 'unknown':
            for tclass in module_class_list:
                if model_name in tclass:
                    module_name = tclass.split(f'_{model_name}')[0]
                else:
                    module_name = tclass.split(f'_{series_products}')[0]
                for module_info in param_get_suite_list():  # 测试套件给每个用例模块设置测试次数，会替换到全局测试次数
                    if module_name not in module_info:
                        continue
                    if module_info[module_name] != 1:
                        if module_info[module_name].get('ForcedOrder'):
                            forced_order = module_info[module_name]['ForcedOrder']
                            force_order_class_info[tclass] = forced_order
                        else:
                            common_module_class_list.append(tclass)
                            common_module_list.append(module_name)
                        break

        if force_order_class_info:
            force_order_class_list = sorted(force_order_class_info, key=force_order_class_info.get)

        aklog_printf(f'force_order_class_list: {force_order_class_list}')
        aklog_printf(f'common_module_class_list: {common_module_class_list}')

        if test_random:
            random.shuffle(common_module_class_list)  # 将列表中的元素打乱
            module_class_list = force_order_class_list + common_module_class_list
        elif test_case_balance_enable:
            test_case_sql.connect()
            case_list = test_case_sql.general_press_case_list_by_version(model_name, rom_version)
            new_common_module_class_list = []
            for case in case_list:
                for class_name in common_module_class_list:
                    if class_name.startswith(case):
                        new_common_module_class_list.append(class_name)
                        break
            module_class_list = force_order_class_list + new_common_module_class_list

        for module_class in module_class_list:
            aklog_printf(module_class)
        aklog_printf('总用例数量: %s' % total_case_counts)
        aklog_printf('测试次数: %s' % g_test_counts)
        if not param_get_start_by_upstream_project_enable():
            wait_time_before_test = int(config_get_value_from_ini_file('config', 'wait_time_before_start_test'))
            aklog_printf(
                '测试用例模块列表如上，如果有发现用例选择不正确，则可以停止运行，%s秒后开始执行' % wait_time_before_test)
            time.sleep(wait_time_before_test)
        aklog_printf('已选择测试用例，开始测试')

        # jenkins工作空间下的报告URL
        if param_get_jenkins_ws_report_root_url() != '':
            jenkins_ws_report_base_url = aklog_get_result_dir(). \
                replace(root_path, param_get_jenkins_ws_report_root_url()).replace('\\', '/')
            aklog_printf('jenkins工作目录下测试结果目录URL：\n%s' % jenkins_ws_report_base_url)

        # 根据机型执行设备初始化
        test_main = param_get_test_main()
        if isinstance(test_main, dict):
            if model_name in test_main:
                test_main_start = test_main[model_name]
                test_main_start()
            elif series_products in test_main:
                aklog_warn('test_main缺少型号: %s, 尝试使用系列产品的test main继续执行' % model_name)
                test_main_start = test_main[series_products]
                test_main_start()
            elif product_line in test_main:
                aklog_warn('test_main缺少系列: %s, 尝试使用产品线的test main继续执行' % series_products)
                test_main_start = test_main[product_line]
                test_main_start()
            else:
                aklog_warn('test_main缺少型号和系列产品: %s, %s' % (model_name, series_products))
                aklog_remove()
                # 删除从监控目录复制到本地的xml文件
                File_process.remove_file(firmware_info_path)
                return False
        else:
            aklog_printf('test_main获取错误')
            aklog_remove()
            # 删除从监控目录复制到本地的xml文件
            File_process.remove_file(firmware_info_path)
            return False

        device_config_master = param_get_device_config()

        # 测试报告标题
        if param_get_master_model() and 'SOLUTION' not in param_get_master_model():
            test_name = ('%s(%s) - %s - %s(%s)'
                         % (report_model_name, model_name, oem_name, rom_version, param_get_version_branch()))
        else:
            test_name = ('%s - %s - %s(%s)'
                         % (report_model_name, oem_name, rom_version, param_get_version_branch()))

        g_test_results_summary['Test_type'] = param_get_test_type()

        # 将监控路径下的升级包拷贝到本地目录
        if not skip_download_firmware:
            local_rom_file = device_config_master.get_local_firmware_path()
            rom_path = param_get_firmware_path()
            if rom_path == 'unknown':
                rom_path = device_config_master.get_remote_firmware_dir()
            if rom_path:
                # 先删除本地升级包
                File_process.delete_old_files(os.path.dirname(local_rom_file))
                time.sleep(2)
                download_result = download_firmware(local_rom_file, rom_path, rom_version)
                if not download_result:
                    aklog_error('升级包下载失败，退出测试')
                    aklog_remove()
                    # 删除从监控目录复制到本地的xml文件
                    File_process.remove_file(firmware_info_path)
                    return False
            else:
                aklog_printf(f'{model_name} 无需下载升级包')
        else:
            aklog_printf('跳过下载升级包，如果用例里面涉及到升级，可能会测试失败')

        # 更新chrome driver
        if config_get_value_from_ini_file('config', 'chrome_driver_auto_update_enable'):
            ChromeDriverUpdate.chrome_driver_auto_update()

        report_file_list = []  # 如果有超过5000条用例或者超过100M, 接口会修改成report名字列表. len判断是否有多个报告
        case_count_per_iframe = 0
        test_case_all_counts = 0
        test_case_pass_counts = 0
        test_case_fail_counts = 0
        test_case_error_counts = 0
        test_case_skip_counts = 0
        test_total_time = 0
        test_pass_rate = 0
        start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        test_date = time.strftime("%Y%m%d", time.localtime())
        param_put_start_time(start_time)

        # 初始化Log，并创建Log目录及文件
        aklog_init(model_name, log_level=5)
        akresult_init()

        # 将xml文件复制到Log目录下
        firmware_info_file_name = ''
        if firmware_info_path != 'unknown':
            firmware_info_file_name = os.path.split(firmware_info_path)[1]
            firmware_info_result_path = os.path.join(aklog_get_result_dir(), firmware_info_file_name)
            File_process.copy_file(firmware_info_path, firmware_info_result_path)

        report_file = aklog_get_report_file()  # 创建Report文件
        report_dir, report_file_name = os.path.split(report_file)
        # 2025.8.1 lex: 对讲增加进程监控报告
        report_process_file = os.path.join(report_dir, 'Report_Process.html')

        test_case_fail_result = ''
        test_module_fail_result = ''
        module_class_test_result = {}

        # 失败后退出执行的标志
        stop_exec_enable = False

        for j in range(test_times):
            selected_module_class_list = []
            selected_module_list = []
            while True:
                if check_stop_exec_enable():
                    stop_exec_enable = True
                    break
                module_test_type = 'function-test'
                module_class_name = None
                if test_case_balance_enable and product_line == 'SMARTHOME':
                    # 启用用例均衡，除了强制优先执行的，其他用例会计算权重排序执行
                    if len(selected_module_class_list) < len(force_order_class_list):
                        for tclass in force_order_class_list:
                            if tclass not in selected_module_class_list:
                                module_class_name = tclass
                                selected_module_class_list.append(tclass)
                                if model_name in tclass:
                                    module_name = tclass.split(f'_{model_name}')[0]
                                else:
                                    module_name = tclass.split(f'_{series_products}')[0]
                                selected_module_list.append(module_name)
                                break
                    else:
                        # 已选中执行的用例模块数量大于等于强制优先执行的数量，说明强制优先执行用例已执行完成
                        test_case_sql.connect()
                        # 用于多台设备同时执行相同用例时，选择未被执行或者执行次数最少的用例
                        module_name = test_case_sql.select_press_case_without_testing(
                            model_name, common_module_list, selected_module_list)
                        if not module_name:
                            break
                        for tclass in module_class_list:
                            if module_name in tclass:
                                module_class_name = tclass
                                break
                else:
                    for tclass in module_class_list:
                        if tclass not in selected_module_class_list:
                            module_class_name = tclass
                            selected_module_class_list.append(tclass)
                            break
                if not module_class_name:
                    break
                # 想要将测试结果及时写入到HTML测试报告里面，就需要每次调用BeautifulReport执行
                test_counts = g_test_counts
                test_duration = None
                if model_name in module_class_name:
                    module_name = module_class_name.split(f'_{model_name}')[0]
                else:
                    module_name = module_class_name.split(f'_{series_products}')[0]
                if param_get_suite_list() != 'unknown':
                    for module_info in param_get_suite_list():  # 测试套件给每个用例模块设置测试次数，会替换到全局测试次数
                        if module_name not in module_info:
                            continue
                        if module_info[module_name] != 1:
                            if g_test_counts == 1 and test_times == 1 and 'TestCounts' in module_info[module_name]:
                                test_counts = module_info[module_name]['TestCounts']
                            elif 'TestDuration' in module_info[module_name]:
                                test_duration = module_info[module_name]['TestDuration']
                            break

                # 如果使用用例均衡，用例执行前select_count要+1
                if test_case_balance_enable and module_name:
                    test_case_sql.connect()
                    test_case_sql.increase_press_case_select_count(model_name, module_name)

                aklog_printf('%s, test_counts: %s' % (module_class_name, test_counts))
                param_put_test_counts(test_counts)  # 将每个用例模块的测试次数赋值给全局变量，测试用例里面可以获取到测试次数
                if test_counts >= 10 or test_times >= 10 or test_duration is not None:
                    module_test_type = 'stress-test'
                    g_test_results_summary['Test_type'] = 'stress-test'

                if module_name and module_name not in module_class_test_result:
                    module_class_test_result[module_name] = {
                        'case_name': module_name,
                        'case_list': [],
                        'test_count': 0,
                        'pass_count': 0,
                        'fail_count': 0,
                        'error_count': 0,
                        'skip_count': 0,
                        'pass_rate': '',
                        'test_version': '',
                        'test_date': '',
                        'test_duration': 0,
                        'test_type': module_test_type
                    }

                module = __import__('lib' + module_class_name.split('_case')[0])
                module_class = getattr(module, module_class_name)
                # 将测试次数和测试时长设置为用例类的属性
                if not hasattr(module_class, 'unittest_attributes'):
                    setattr(module_class, 'unittest_attributes', {})
                if test_duration:
                    module_class.unittest_attributes['test_duration'] = test_duration
                if test_counts:
                    module_class.unittest_attributes['test_counts'] = test_counts

                case_name_list = modules_dict[module_class_name]
                test_suite_list = []
                if exec_one_case_to_report_enable:
                    # 执行完一个用例就写入报告，适合压测用例
                    for i in range(test_counts):
                        test_suite_case_list = []
                        for case_name in case_name_list:
                            suite = unittest.TestSuite()
                            suite.addTest(module_class(case_name))
                            test_suite_case_list.append(suite)
                        test_suite_list.append(test_suite_case_list)
                    # 每一条用例都会执行setUpClass和tearDownClass，因此test_counts要计算一个用例类有多条用例
                    param_put_test_counts(len(test_suite_list[0]) * test_counts)
                else:
                    # 执行完一个用例类的所有用例才写入报告
                    for i in range(test_counts):
                        test_suite_case_list = []
                        suite = unittest.TestSuite()
                        for case_name in case_name_list:
                            suite.addTest(module_class(case_name))
                        test_suite_case_list.append(suite)
                        test_suite_list.append(test_suite_case_list)

                for k in range(len(test_suite_list)):
                    aklog_printf('test count: %s' % (k + 1))
                    # 报告文件太大重命名后继续保存，之后再将多个报告合并放在iframe里
                    if File_process.get_file_size_mb(report_file) > 100 or case_count_per_iframe > 5000:
                        report_file_list = File_process.rename_file_to_list(report_file_list, report_file)
                        reset_fields()  # 清空BeautifulReport测试结果
                        case_count_per_iframe = 0

                    test_suite_case_list = test_suite_list[k]
                    for suite in test_suite_case_list:
                        if check_stop_exec_enable():
                            stop_exec_enable = True
                            break

                        beautiful_report = BeautifulReport(suite, retry=retry_counts,
                                                           save_last_try=save_last_try)
                        beautiful_report.report(description=test_name,
                                                filename=report_file_name,
                                                log_path=report_dir)

                        case_count_per_iframe += FIELDS['testAll']
                        test_case_all_counts += FIELDS['testAll']
                        test_case_pass_counts += FIELDS['testPass']
                        test_case_fail_counts += FIELDS['testFail']
                        test_case_error_counts += FIELDS['testError']
                        test_case_skip_counts += FIELDS['testSkip']
                        test_total_time += int(FIELDS['totalTime'])

                        # 获取测试失败的测试用例名称
                        for case_result in FIELDS['testResult']:
                            if case_result['status'] == '失败' or case_result['status'] == '错误':
                                fail_case_name = '%s.%s' % (
                                    case_result['className'], case_result['methodName'])
                                if fail_case_name not in test_case_fail_result:
                                    test_case_fail_result += fail_case_name + ';\n'
                                if case_result['className'] not in test_module_fail_result:
                                    test_module_fail_result += case_result['className'] + ';\n'

                        # 用例出现失败退出执行
                        if param_get_failed_to_exit_enable() and \
                                test_case_pass_counts != test_case_all_counts:
                            aklog_warn('~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~')
                            aklog_warn('用例出现失败退出执行')
                            stop_exec_enable = True
                            break

                    if stop_exec_enable:
                        break

                # 获取当前用例类执行结果信息
                if test_case_balance_enable and module_name:
                    # 如果使用用例均衡，用例执行完成后select_count要-1
                    test_case_sql.connect()
                    test_case_sql.decrease_press_case_select_count(model_name, module_name)

                # 家居产品需要上报测试结果到服务器数据库
                if product_line == 'SMARTHOME' and module_name:
                    # 获取该用例类中用例的数量
                    for case_result in FIELDS['testResult']:
                        className = case_result['className']
                        if className != module_class_name:
                            continue

                        method_name = case_result['methodName']
                        if method_name not in module_class_test_result[module_name]['case_list']:
                            module_class_test_result[module_name]['case_list'].append(method_name)
                        module_class_test_result[module_name]['test_count'] += 1
                        module_class_test_result[module_name]['test_duration'] += case_result['spendTime']
                        if case_result['status'] == '成功':
                            module_class_test_result[module_name]['pass_count'] += 1
                        elif case_result['status'] == '失败':
                            module_class_test_result[module_name]['fail_count'] += 1
                        elif case_result['status'] == '错误':
                            module_class_test_result[module_name]['error_count'] += 1
                        elif case_result['status'] == '跳过':
                            module_class_test_result[module_name]['skip_count'] += 1

                    if module_name in module_class_test_result:
                        # 将用例执行结果写入到数据库
                        module_class_test_result[module_name]['case_count'] = len(
                            module_class_test_result[module_name]['case_list'])
                        total_count_without_skip = (module_class_test_result[module_name]['test_count']
                                                    - module_class_test_result[module_name]['skip_count'])
                        if (module_class_test_result[module_name]['test_count'] != 0
                                and total_count_without_skip != 0):
                            pass_rate = round(
                                module_class_test_result[module_name]['pass_count'] /
                                total_count_without_skip * 100, 1)
                            module_class_test_result[module_name]['pass_rate'] = f'{pass_rate}%'
                        module_class_test_result[module_name]['test_version'] = rom_version
                        module_class_test_result[module_name]['test_date'] = test_date

                if stop_exec_enable:
                    break

            if stop_exec_enable:
                break

        aklog_printf('test_case_fail_result: %s' % test_case_fail_result)
        aklog_printf('test_module_fail_result: %s' % test_module_fail_result)

        # region 将执行失败的测试用例添加到xml文件
        if test_module_fail_result != '' and firmware_info_path != 'unknown':
            firmware_info_result_fail_file_name = firmware_info_file_name.replace('.xml',
                                                                                  '_module_fail.xml')
            firmware_info_result_fail_path = os.path.join(aklog_get_result_dir(),
                                                          firmware_info_result_fail_file_name)
            File_process.copy_file(firmware_info_path, firmware_info_result_fail_path)
            xml_add_attributes(firmware_info_result_fail_path, 'test_cases',
                               {'modules': test_module_fail_result})
            xml_add_attributes(firmware_info_result_fail_path, 'test_cases',
                               {'cases': '\n'})

        if test_case_fail_result != '' and firmware_info_path != 'unknown':
            # 有些用例没有必须要执行的用例，也可以单独跑出错的用例，所以生成两个xml文件，根据需要选择
            firmware_info_result_case_fail_file_name = firmware_info_file_name.replace('.xml',
                                                                                       '_case_fail.xml')
            firmware_info_result_case_fail_path = os.path.join(aklog_get_result_dir(),
                                                               firmware_info_result_case_fail_file_name)
            File_process.copy_file(firmware_info_path, firmware_info_result_case_fail_path)
            xml_add_attributes(firmware_info_result_case_fail_path, 'test_cases',
                               {'modules': '\n'})
            xml_add_attributes(firmware_info_result_case_fail_path, 'test_cases',
                               {'cases': test_case_fail_result})
        # endregion

        reset_fields()  # 清空BeautifulReport测试结果

        # region 将测试结果汇总写入到results_summary.txt文件，后面合并发送邮件使用
        results_summary = 'total_case_counts: %s\n' \
                          'test_case_all_counts: %s\n' \
                          'test_case_pass_counts: %s\n' \
                          'test_case_fail_counts: %s\n' \
                          'test_case_error_counts: %s\n' \
                          'test_case_skip_counts: %s\n' \
                          'test_pass_rate: %s' \
                          % (total_case_counts, test_case_all_counts, test_case_pass_counts, test_case_fail_counts,
                             test_case_error_counts, test_case_skip_counts, test_pass_rate)
        results_summary_file = report_dir + '\\results_summary.txt'
        aklog_printf('测试结果汇总写入到文件 %s 里' % results_summary_file)

        with open(results_summary_file, 'w', encoding='utf-8') as fp:
            fp.write(results_summary)
        # endregion

        # region 获取Module用例模块测试结果，并写入到module_results.txt文件
        result_file = os.path.join(report_dir, 'Result.txt')
        module_results_file = os.path.join(report_dir, 'module_results.txt')
        case_results_file = os.path.join(report_dir, 'case_results.txt')
        parse_results_file(result_file, case_results_file, module_results_file)
        # endregion

        # region 将多个重命名后的测试报告文件通过iframe的方式添加到一个HTML文件里
        # 2025.8.1 lex 对讲终端增加进程异常报告展示, 合并到report.html里展示.
        if os.path.exists(report_process_file):
            # 对讲终端有进程异常报告情况下, 处理Report_file_list, 以进入合并展示流程.
            if not report_file_list:
                report_file_list = ['Report_Process.html']
        if report_file_list:
            if report_file_list == ['Report_Process.html']:
                # 判断是原本只有一个Report.html的情况, 处理增加Report_Process.html的情况
                newfilelist = []
                File_process.rename_file_to_list(newfilelist, report_file)
                newfilelist.append('Report_Process.html')
                report_file_list = newfilelist[:]
            else:
                # 如果report_file_list已存在Report_Process.html，先移除，对报告列表重命名后，再添加回来
                if 'Report_Process.html' in report_file_list:
                    report_file_list.remove('Report_Process.html')
                File_process.rename_file_to_list(report_file_list, report_file)
                if os.path.exists(report_process_file):
                    report_file_list.append('Report_Process.html')
            body = ''
            if test_case_all_counts - test_case_skip_counts == 0:
                test_pass_rate = 0.0
            else:
                test_pass_rate = round(
                    test_case_pass_counts / (test_case_all_counts - test_case_skip_counts) * 100, 4)
            report_ret = '<p>用例总数: %s </p>\n' \
                         '<p>用例通过: %s </p>\n' \
                         '<p>用例失败: %s </p>\n' \
                         '<p>用例错误: %s </p>\n' \
                         '<p>用例跳过: %s </p>\n' \
                         '<p>通过率: %s </p>\n\n' \
                         % (test_case_all_counts, test_case_pass_counts, test_case_fail_counts, test_case_error_counts,
                            test_case_skip_counts, format_pass_rate(test_pass_rate))
            body += report_ret
            for file_name in report_file_list:
                if file_name == 'Report_Process.html':
                    iframe = '<p>Jenkins工程名称: %s</p>\n<iframe src="%s" width="1920" height="1080"></iframe>\n' \
                             % (param_get_jenkins_job_name(), 'Report_Process.html')
                    body += iframe
                else:
                    iframe = '<p>Jenkins工程名称: %s</p>\n<iframe src="%s" width="1920" height="1080"></iframe>\n' \
                             % (param_get_jenkins_job_name(), file_name)
                    body += iframe
            report_content = """<html>\n<body>\n%s</body>\n</html>""" % body
            with open(report_file, 'w', encoding='utf-8') as fp:
                fp.write(report_content)
        # endregion

        # region 获取测试结果汇总，并发送到服务器
        if test_case_all_counts != 0:
            if test_case_all_counts - test_case_skip_counts == 0:
                test_pass_rate = 0.0
            else:
                test_pass_rate = round(
                    test_case_pass_counts / (test_case_all_counts - test_case_skip_counts) * 100, 4)
        g_test_results_summary['Total_testcases'] = test_case_all_counts
        g_test_results_summary['Pass_testcases'] = test_case_pass_counts
        g_test_results_summary['Pass_rate'] = test_pass_rate
        g_test_results_summary['Test_date'] = test_date
        g_test_results_summary['Take_time'] = sec2minute(test_total_time, 1)
        g_test_results_summary['Product_name'] = report_model_name
        g_test_results_summary['Product_version'] = rom_version
        aklog_printf(f'g_test_results_summary: {g_test_results_summary}')

        # 发送测试结果汇总到服务器
        report_file_url = ''
        if send_test_results_summary_enable and product_line == 'SMARTHOME' and test_case_all_counts > 0:
            # 将测试报告复制到HTTP服务器，方便直接浏览器打开
            if not param_get_jenkins_report_url():
                report_file_url = send_report_file_to_http_server(report_file)

            # 上报测试结果到数据库
            aklog_info('send test results to sql')
            test_results_summary = {
                'test_count': test_case_all_counts,
                'pass_count': test_case_pass_counts,
                'fail_count': test_case_fail_counts,
                'error_count': test_case_error_counts,
                'skip_count': test_case_skip_counts,
                'pass_rate': f'{test_pass_rate}%',
                'test_version': rom_version,
                'test_date': test_date,
                'test_duration': seconds_to_duration(test_total_time),
            }
            test_case_sql.connect()
            if g_test_results_summary['Test_type'] == 'stress-test':
                for module_name in module_class_test_result:
                    if module_class_test_result[module_name]['test_type'] != 'stress-test':
                        continue
                    module_class_test_result[module_name]['test_duration'] = seconds_to_duration(
                        module_class_test_result[module_name]['test_duration']
                    )
                    test_case_sql.write_press_test_results(
                        report_model_name, module_class_test_result[module_name])
            else:
                test_case_sql.write_function_test_results(
                    report_model_name, test_results_summary)
            # test_results_summary_url = config_get_value_from_ini_file('config', 'test_results_summary_url')
            # ak_requests = AkRequests('%s/%s' % (test_results_summary_url, test_date))
            # ak_requests.send_post(g_test_results_summary)
            # ak_requests.close()
        # endregion

        aklog_printf('测试已全部完成, 可前往 {} 查询测试报告'.format(report_file))

        # region Email发送测试报告

        # 获取主设备的信息，在测试报告上显示主设备的MAC地址信息
        master_device_info = param_get_master_device_info()
        if master_device_info:
            master_mac = master_device_info.get('mac') or master_device_info.get('MAC') or ''
            if master_mac and 'SOLUTION' not in report_model_name:
                report_model_name = f'{report_model_name}({master_mac})'

        if param_get_jenkins_report_url() != '':
            report_file_url = param_get_jenkins_report_url()

        # jenkins工作空间下的报告URL
        jenkins_ws_report_url = ''
        if param_get_jenkins_ws_report_root_url() != '':
            jenkins_ws_report_url = aklog_get_report_url(param_get_jenkins_ws_report_root_url())
            aklog_printf('jenkins工作目录下测试报告：%s' % jenkins_ws_report_url)
            aklog_printf('jenkins工作目录下测试结果汇总：%s' % results_summary_file.replace(
                root_path, param_get_jenkins_ws_report_root_url()).replace('\\', '/'))

        report_img_file = None
        if param_get_email_receivers():  # 邮件接收人员由XML文件指定，否则用device_config默认名单
            email_receivers = param_get_email_receivers()
        else:
            email_receivers = device_config_master.get_email_receivers()
            if param_get_added_email_receivers():
                email_receivers.extend(param_get_added_email_receivers())  # 增加发送人员
        # 如果是上游工程构建分布式执行，要合并后再发送邮件
        if send_email_enable and (stop_exec_enable or not param_get_start_by_upstream_project_enable()):
            # HTML测试报告截图
            time.sleep(5)
            report_browser = libbrowser()
            report_img_file = aklibreport_html(report_browser, report_file).report_html_screenshot()

            send_email_html = SendEmailHandler()
            email_title = report_model_name + ' - ' + oem_name + ' - ' + rom_version + ' - 自动测试报告'
            test_result = True if (test_case_all_counts - test_case_pass_counts
                                   - test_case_skip_counts == 0) else False
            if not test_result:
                email_title += '【失败】'
            else:
                email_title += '【成功】'
            send_email_report_type = config_get_value_from_ini_file('config', 'send_email_report_type')
            if send_email_report_type == 'file':  # file or url, 发送测试报告邮件是发送附件还是URL
                email_content = '%s - %s - %s - 自动测试报告' % (report_model_name, oem_name, rom_version)
                for i in range(0, 3):
                    if not send_email_html.send_email_with_img_attachment(
                            email_receivers,
                            email_title,
                            email_content,
                            report_img_file,
                            report_file):
                        time.sleep(10)
                    else:
                        break
            else:
                email_content = '%s - %s - %s - 自动测试报告： <a href="%s">请点击链接查看</a>' \
                                % (report_model_name, oem_name, rom_version, report_file_url)
                if jenkins_ws_report_url:
                    email_content += '\n如果上一个链接无法打开，可以尝试打开工作空间URL： <a href="%s">请点击链接查看</a>' \
                                     % jenkins_ws_report_url
                for i in range(0, 3):
                    if not send_email_html.send_email_with_img_attachment(
                            email_receivers,
                            email_title,
                            email_content,
                            report_img_file):
                        time.sleep(10)
                    else:
                        break
        # endregion

        # region 是否发送企业微信消息
        if param_get_send_work_weixin_state() and \
                (stop_exec_enable or not param_get_start_by_upstream_project_enable()):
            send_email_report_type = config_get_value_from_ini_file('config', 'send_email_report_type')
            if send_email_report_type == 'file':  # file or url, 发送测试报告给企业微信是发送附件还是URL
                msg_content = '%s - %s - %s - 自动测试报告' % (report_model_name, oem_name, rom_version)
                robot_send_text_msg(msg_content, *email_receivers)
                robot_send_file(report_file, *email_receivers)
            else:
                # HTML测试报告截图
                if not report_img_file:
                    report_browser = libbrowser()
                    report_img_file = aklibreport_html(report_browser,
                                                       report_file).report_html_screenshot()
                msg_content = "%s - %s - %s - 自动测试报告:\n%s" \
                              % (report_model_name, oem_name, rom_version, report_file_url)
                if jenkins_ws_report_url:
                    msg_content += '\n如果上一个链接无法打开，可以尝试打开工作空间URL:\n%s' % jenkins_ws_report_url
                robot_send_text_msg(msg_content, *email_receivers)
                robot_send_image(report_img_file, *email_receivers)
        # endregion

        # region 处理测试报告目录文件到jenkins
        # 将测试报告目录下的文件夹（device_log等）进行打包，然后删除文件夹，方便jenkins存档
        if param_get_jenkins_report_dir():
            for x in os.listdir(report_dir):
                src = os.path.join(report_dir, x)
                if os.path.isdir(src):
                    dst_zip = os.path.join(report_dir, '%s.zip' % x)
                    File_process.zip_dir(src, dst_zip)
                    File_process.remove_dir(src)

            # 获取Jenkins测试报告路径
            jenkins_report_file = param_get_jenkins_report_dir() + 'jenkins-report.html'

            # 复制报告到对讲终端共享文件夹
            if product_line == 'INTERCOM':
                # intercom_copy_report_to_smb(report_dir, test_case_all_counts, test_case_skip_counts)
                intercom_copy_report_to_smb(report_dir, g_test_results_summary, test_case_skip_counts, 1)

            # 将测试报告复制到outputs\Report目录下，用于在Jenkins上显示测试报告
            File_process.copy_files_whole_dir(report_dir, param_get_jenkins_report_dir())
            File_process.rename_file(param_get_jenkins_report_dir() + 'Report.html', jenkins_report_file)
            time.sleep(2)
        # endregion

        # 停止保存log到文件
        aklog_remove()

        # 删除从监控目录复制到本地的xml文件
        File_process.remove_file(firmware_info_path)
        aklog_printf('%s %s %s' % ('-' * 100, 'End Test', '-' * 100))
        return True
    except:
        aklog_printf('遇到未知异常, 程序退出! ' + str(traceback.format_exc()))
        aklog_remove()
        return False


def unittest_start():
    """用于界面勾选用例执行"""
    try:
        aklog_printf('已选择测试用例，开始测试')

        # region 获取配置信息
        device_config_master = param_get_device_config()
        product_line = param_get_product_line_name()
        series_products = param_get_seriesproduct_name()
        model_name = param_get_model_name()
        oem_name = param_get_oem_name()
        rom_version = param_get_rom_version()
        report_model_name = param_get_firmware_info().get('report_model_name')
        if not report_model_name:
            report_model_name = model_name
        if param_get_master_model() and 'SOLUTION' not in param_get_master_model():
            report_model_name = param_get_master_model()
            if '+' in report_model_name:
                report_model_name = report_model_name.split('+')[0]
            if param_get_firmware_info().get(f'{report_model_name}_version'):
                rom_version = param_get_firmware_info().get(f'{report_model_name}_version')

        test_case_sql = SmartHomeTestCaseSql()

        # 测试多少遍，主要用于手动测试，默认次数1，test_rounds每一轮测试都会发送邮件
        test_rounds = param_get_test_rounds()

        # 测试多少遍，主要用于手动测试，默认次数1，test_times会每测试一遍都会创建新的Result目录写log和report文件，适合多个用例循环测试
        test_times = param_get_test_times()

        # 设置测试次数, 主要用于手动测试，默认次数1，test_counts会把每次测试结果写入到同一个log和report文件里，适合单个用例压力测试
        g_test_counts = param_get_test_counts()

        # 设置是否随机乱序执行
        test_random = param_get_test_random_state()

        # 是否发送测试结果汇总到服务器
        send_test_results_summary_enable = param_get_send_test_results_summary_enable()

        # 跳过下载升级包
        skip_download_firmware = param_get_skip_download_firmware_state()

        # 失败重测是否只保存最后一次结果到测试报告
        save_last_try = param_get_save_last_try_state()

        # 失败重测次数
        retry_counts = param_get_retry_counts()

        # 是否单个用例执行完就写入测试报告，False表示整个用例类执行完才写入测试报告
        exec_one_case_to_report_enable = param_get_exec_one_case_to_report_enable()
        # endregion

        g_test_results_summary['Test_type'] = 'function-test'

        # 将监控路径下的升级包拷贝到本地目录
        if not skip_download_firmware:
            local_rom_file = device_config_master.get_local_firmware_path()
            # 获取远程升级包路径
            rom_path = param_get_firmware_path()
            if rom_path == 'unknown':
                rom_path = device_config_master.get_remote_firmware_dir()
            if rom_path:
                # 先删除本地升级包
                File_process.delete_old_files(os.path.dirname(local_rom_file))
                time.sleep(2)
                download_result = download_firmware(local_rom_file, rom_path, rom_version)
                if not download_result:
                    aklog_error('升级包下载失败，退出测试')
                    unittest_stop_run()
                    return False
            else:
                aklog_printf(f'{model_name} 无需下载升级包')
        else:
            aklog_printf('跳过下载升级包，如果用例里面涉及到升级，可能会测试失败')

        # 更新chrome driver
        if config_get_value_from_ini_file('config', 'chrome_driver_auto_update_enable'):
            ChromeDriverUpdate.chrome_driver_auto_update()

        # 创建测试套件，并开始执行测试用例
        modules_dict = param_get_modules_dict()
        aklog_printf('modules_dict: %r' % modules_dict)

        # 获取总用例数量，只计算测试一遍的用例数量
        total_case_counts = 0
        for x in modules_dict:
            total_case_counts += len(modules_dict[x])
        aklog_printf('总用例数量: %s' % total_case_counts)

        module_class_list = sorted(modules_dict)  # 取key值并加到list

        # 测试报告标题描述
        if param_get_master_model() and 'SOLUTION' not in param_get_master_model():
            test_name = ('%s(%s) - %s - %s(%s)'
                         % (report_model_name, model_name, oem_name, rom_version, param_get_version_branch()))
        else:
            test_name = ('%s - %s - %s(%s)'
                         % (report_model_name, oem_name, rom_version, param_get_version_branch()))

        # 退出执行的标志
        stop_exec_enable = False

        # 初始化Log，并创建Log目录及文件
        aklog_init(model_name, log_level=5)
        akresult_init()

        report_file_list = []  # 如果有超过5000条用例或者超过100M, 接口会修改成report名字列表. len判断是否有多个报告
        case_count_per_iframe = 0
        test_case_all_counts = 0
        test_case_pass_counts = 0
        test_case_fail_counts = 0
        test_case_error_counts = 0
        test_case_skip_counts = 0
        test_total_time = 0
        test_pass_rate = 0
        failed_to_inform_counts = 0  # 失败发送通知次数
        start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        test_date = time.strftime("%Y%m%d", time.localtime())
        param_put_start_time(start_time)
        build_user = param_get_build_user()

        # 将xml文件复制到Log目录下
        firmware_info_path = param_get_firmware_info_path()
        firmware_info_file_name = ''
        if firmware_info_path != 'unknown':
            firmware_info_file_name = os.path.split(firmware_info_path)[1]
            firmware_info_result_path = os.path.join(aklog_get_result_dir(), firmware_info_file_name)
            File_process.copy_file(firmware_info_path, firmware_info_result_path)

        # BeautifulReport生成HTML测试报告方式
        report_file = aklog_get_report_file()  # 创建Report文件
        report_dir, report_file_name = os.path.split(report_file)
        # 2025.8.1 lex: 对讲增加进程监控报告
        report_process_file = os.path.join(report_dir, 'Report_Process.html')

        test_case_fail_result = ''
        test_module_fail_result = ''
        module_class_test_result = {}

        for x in range(test_rounds):
            for j in range(test_times):
                # 测试用例模块顺序打乱，注意要确保不同用例模块之间不会互相依赖，否则执行可能会失败
                if test_random:
                    random.shuffle(module_class_list)
                module_class_test_result.clear()  # 先清空，然后在新的一遍执行完成后，重新从FIELDS测试结果中获取数据

                for module_class_name in module_class_list:
                    if param_get_stop_exec_enable():
                        aklog_info('退出执行')
                        stop_exec_enable = True
                        break
                    # 想要将测试结果及时写入到HTML测试报告里面，就需要每次调用BeautifulReport执行
                    test_counts = g_test_counts
                    test_duration = None
                    module_test_type = 'function-test'

                    if model_name in module_class_name:
                        module_name = module_class_name.split(f'_{model_name}')[0]
                    else:
                        module_name = module_class_name.split(f'_{series_products}')[0]
                    # 如果要使用测试套件指定的测试次数，全局test counts需要保持默认的1
                    if param_get_suite_list() != 'unknown':
                        for module_info in param_get_suite_list():  # 测试套件给每个用例模块设置测试次数，会替换到全局测试次数
                            if module_name not in module_info:
                                continue
                            if module_info[module_name] != 1:
                                if g_test_counts == 1 and test_times == 1 and 'TestCounts' in module_info[module_name]:
                                    test_counts = module_info[module_name]['TestCounts']
                                elif 'TestDuration' in module_info[module_name]:
                                    test_duration = module_info[module_name]['TestDuration']
                                break

                    param_put_test_counts(test_counts)  # 将每个用例模块的测试次数赋值给全局变量，测试用例里面可以获取到测试次数
                    aklog_printf('%s, test_counts: %s' % (module_class_name, test_counts))
                    if test_counts >= 10 or test_times >= 10 or test_duration is not None:
                        module_test_type = 'stress-test'
                        g_test_results_summary['Test_type'] = 'stress-test'

                    if module_name and module_name not in module_class_test_result:
                        module_class_test_result[module_name] = {
                            'case_name': module_name,
                            'case_list': [],
                            'test_count': 0,
                            'pass_count': 0,
                            'fail_count': 0,
                            'error_count': 0,
                            'skip_count': 0,
                            'pass_rate': '',
                            'test_version': '',
                            'test_date': '',
                            'test_duration': 0,
                            'test_type': module_test_type
                        }

                    module = __import__('lib' + module_class_name.replace('_case', ''))
                    module_class = getattr(module, module_class_name)
                    # 将测试次数和测试时长设置为用例类的属性
                    if not hasattr(module_class, 'unittest_attributes'):
                        setattr(module_class, 'unittest_attributes', {})
                    if test_duration:
                        module_class.unittest_attributes['test_duration'] = test_duration
                    if test_counts:
                        module_class.unittest_attributes['test_counts'] = test_counts

                    case_name_list = modules_dict[module_class_name]
                    test_suite_list = []
                    if exec_one_case_to_report_enable:
                        # 执行完一个用例就写入报告，适合压测用例
                        for i in range(test_counts):
                            test_suite_case_list = []
                            # 如果压测用例执行多遍，并且勾选随机，则用例类里面的用例也随机执行，要保证每条用例独立互不影响和依赖
                            if test_random and test_counts > 1:
                                random.shuffle(case_name_list)
                            for case_name in case_name_list:
                                suite = unittest.TestSuite()
                                suite.addTest(module_class(case_name))
                                test_suite_case_list.append(suite)
                            test_suite_list.append(test_suite_case_list)
                        # 每一条用例都会执行setUpClass和tearDownClass，因此test_counts要计算一个用例类有多条用例
                        param_put_test_counts(len(test_suite_list[0]) * test_counts)
                    else:
                        # 执行完一个用例类的所有用例才写入报告
                        for i in range(test_counts):
                            test_suite_case_list = []
                            suite = unittest.TestSuite()
                            for case_name in case_name_list:
                                suite.addTest(module_class(case_name))
                            test_suite_case_list.append(suite)
                            test_suite_list.append(test_suite_case_list)

                    for k in range(len(test_suite_list)):
                        if len(test_suite_list) > 1:
                            aklog_printf('test count: %s' % (k + 1))
                        # 报告文件太大重命名后继续保存，之后再将多个报告合并放在iframe里
                        if os.path.exists(report_file):
                            aklog_printf('ReportFile: file:///{}'.format(report_file.replace('\\', '/')))
                            if File_process.get_file_size_mb(report_file) > 100 or case_count_per_iframe > 5000:
                                File_process.rename_file_to_list(report_file_list, report_file)
                                reset_fields()  # 清空BeautifulReport测试结果
                                case_count_per_iframe = 0

                        test_suite_case_list = test_suite_list[k]
                        param_put_test_suite_case_list(test_suite_case_list)  # 测试用例可以重写该list，让用例重新执行
                        for suite in test_suite_case_list:
                            if param_get_stop_exec_enable():
                                aklog_info('退出执行')
                                stop_exec_enable = True
                                break

                            # 可以手动修改temp.ini配置文件，把stop_exec_enable设置为True，退出执行
                            if not param_get_temp_ini_file():
                                temp_config_file = os.path.join(g_config_path, 'temp.ini')
                                param_put_temp_ini_file(temp_config_file)
                            readconfig = ReadConfig(param_get_temp_ini_file())
                            stop_exec_enable_config = readconfig.get_value('config', 'stop_exec_enable')
                            if stop_exec_enable_config is True:
                                aklog_info('手动停止，退出执行')
                                readconfig.modify_config('config', 'stop_exec_enable',
                                                         'False').write_config()
                                stop_exec_enable = True
                                break

                            beautiful_report = BeautifulReport(suite, retry=retry_counts,
                                                               save_last_try=save_last_try)
                            beautiful_report.report(description=test_name,
                                                    filename=report_file_name,
                                                    log_path=report_dir)

                            case_count_per_iframe += FIELDS['testAll']
                            test_case_all_counts += FIELDS['testAll']
                            test_case_pass_counts += FIELDS['testPass']
                            test_case_fail_counts += FIELDS['testFail']
                            test_case_error_counts += FIELDS['testError']
                            test_case_skip_counts += FIELDS['testSkip']
                            test_total_time += int(FIELDS['totalTime'])

                            # 获取测试失败的测试用例名称
                            for case_result in FIELDS['testResult']:
                                if case_result['status'] == '失败' or case_result['status'] == '错误':
                                    fail_case_name = '%s.%s' % (
                                        case_result['className'], case_result['methodName'])
                                    if fail_case_name not in test_case_fail_result:
                                        test_case_fail_result += fail_case_name + ';\n'
                                    if case_result['className'] not in test_module_fail_result:
                                        test_module_fail_result += case_result['className'] + ';\n'

                            # 用例出现失败退出执行
                            if param_get_failed_to_exit_enable() and \
                                    test_case_pass_counts != test_case_all_counts:
                                aklog_info('用例出现失败退出执行')
                                stop_exec_enable = True
                                break

                            # 用例出现失败发送邮件或企业微信通知
                            if param_get_failed_to_notification_enable() and \
                                    test_case_fail_counts + test_case_error_counts > failed_to_inform_counts:
                                aklog_info('用例执行失败，发送邮件或企业微信通知')
                                failed_to_inform_counts = test_case_fail_counts + test_case_error_counts
                                test_result = True if (test_case_all_counts - test_case_pass_counts
                                                       - test_case_skip_counts == 0) else False
                                send_email_or_work_weixin(
                                    report_file, report_model_name, oem_name, rom_version, test_result)

                        if stop_exec_enable:
                            break

                    # 家居产品需要上报测试结果到服务器数据库
                    if product_line == 'SMARTHOME' and module_name:
                        # 获取该用例类中用例的数量
                        for case_result in FIELDS['testResult']:
                            className = case_result['className']
                            if className != module_class_name:
                                continue

                            method_name = case_result['methodName']
                            if method_name not in module_class_test_result[module_name]['case_list']:
                                module_class_test_result[module_name]['case_list'].append(method_name)
                            module_class_test_result[module_name]['test_count'] += 1
                            module_class_test_result[module_name]['test_duration'] += case_result['spendTime']
                            if case_result['status'] == '成功':
                                module_class_test_result[module_name]['pass_count'] += 1
                            elif case_result['status'] == '失败':
                                module_class_test_result[module_name]['fail_count'] += 1
                            elif case_result['status'] == '错误':
                                module_class_test_result[module_name]['error_count'] += 1
                            elif case_result['status'] == '跳过':
                                module_class_test_result[module_name]['skip_count'] += 1

                        if module_name in module_class_test_result:
                            # 将用例执行结果写入到数据库
                            module_class_test_result[module_name]['case_count'] = len(
                                module_class_test_result[module_name]['case_list'])
                            total_count_without_skip = (module_class_test_result[module_name]['test_count']
                                                        - module_class_test_result[module_name]['skip_count'])
                            if (module_class_test_result[module_name]['test_count'] != 0
                                    and total_count_without_skip != 0):
                                pass_rate = round(
                                    module_class_test_result[module_name]['pass_count'] /
                                    total_count_without_skip * 100, 1)
                                module_class_test_result[module_name]['pass_rate'] = f'{pass_rate}%'

                    if stop_exec_enable:
                        break
                if stop_exec_enable:
                    break

            # region 每一轮测试完成后，都要重命名测试报告文件，之后再用iframe方式添加到一个HTML文件里面
            if test_rounds > 1 and x + 1 < test_rounds:
                if os.path.exists(report_file):
                    aklog_printf('ReportFile: file:///{}'.format(report_file.replace('\\', '/')))
                    File_process.rename_file_to_list(report_file_list, report_file)
                    reset_fields()  # 清空BeautifulReport测试结果
                    case_count_per_iframe = 0
                aklog_info('第 {} 轮测试完成, 可前往 file:///{} 查询测试报告'.format(
                    x + 1, report_file.replace('\\', '/')))
            # endregion

            # region 将多个重命名后的测试报告文件通过iframe的方式添加到一个HTML文件里

            # 2025.8.1 lex 对讲终端增加进程异常报告展示, 合并到report.html里展示.
            if os.path.exists(report_process_file):
                # 对讲终端有进程异常报告情况下, 处理Report_file_list
                if not report_file_list:
                    report_file_list = ['Report_Process.html']
            if report_file_list:
                if report_file_list == ['Report_Process.html']:
                    # 判断是原本只有一个Report.html的情况, 处理增加Report_Process.html的情况
                    newfilelist = []
                    File_process.rename_file_to_list(newfilelist, report_file)
                    newfilelist.append('Report_Process.html')
                    report_file_list = newfilelist[:]
                else:
                    # 如果report_file_list已存在Report_Process.html，先移除，对报告列表重命名后，再添加回来
                    if 'Report_Process.html' in report_file_list:
                        report_file_list.remove('Report_Process.html')
                    File_process.rename_file_to_list(report_file_list, report_file)
                    if os.path.exists(report_process_file):
                        report_file_list.append('Report_Process.html')

                body = ''
                head = get_fold_head()
                if test_case_all_counts - test_case_skip_counts == 0:
                    test_pass_rate = 0.0
                else:
                    test_pass_rate = round(
                        test_case_pass_counts / (test_case_all_counts - test_case_skip_counts) * 100, 4)
                body += f"""<button style="background-color:#F1A058;" onclick="toggleIframe('count')">展开/折叠统计区</button>\n"""
                report_ret = u'<div id="count">\n' \
                             '<p>用例总数: %s </p>\n' \
                             '<p>用例通过: %s </p>\n' \
                             '<p>用例失败: %s </p>\n' \
                             '<p>用例错误: %s </p>\n' \
                             '<p>用例跳过: %s </p>\n' \
                             '<p>通过率: %s </p>\n' \
                             '</div>\n' \
                             % (test_case_all_counts, test_case_pass_counts, test_case_fail_counts,
                                test_case_error_counts, test_case_skip_counts, format_pass_rate(test_pass_rate))
                body += report_ret

                _rindex = 0
                for file_name in report_file_list:
                    _rindex += 1
                    if file_name == 'Report_Process.html':
                        reporttitle = '''<h3 onclick="toggleIframe('Iframe%s')" style="background-color:#F1A058;">Report-%s.html -- 点击展开/折叠</h3>\n''' % (
                            '进程监控', '进程监控')
                        iframe = '<iframe id="Iframe%s" src="%s" width="1920" height="1080"></iframe>\n' % (
                            '进程监控', 'Report_Process.html')
                    else:
                        reporttitle = '''<h3 onclick="toggleIframe('Iframe%s')" style="background-color:#F1A058;">Report-%s.html -- 点击展开/折叠</h3>\n''' % (
                            _rindex, _rindex)
                        iframe = '<iframe id="Iframe%s" src="%s" width="1920" height="1080"></iframe>\n' % (
                            _rindex, file_name)
                    body += reporttitle
                    body += iframe
                report_content = """<html>\n%s\n<body>\n%s</body>\n</html>""" % (head, body)
                with open(report_file, 'w', encoding='gbk') as fp:
                    fp.write(report_content)
            # endregion

            if x < test_rounds - 1 and not stop_exec_enable:
                test_result = True if (test_case_all_counts - test_case_pass_counts
                                       - test_case_skip_counts == 0) else False
                send_email_or_work_weixin(
                    report_file, report_model_name, oem_name, rom_version, test_result)

            if stop_exec_enable:
                break

        reset_fields()  # 清空BeautifulReport测试结果
        aklog_printf('test_case_fail_result: %s' % test_case_fail_result)
        aklog_printf('test_module_fail_result: %s' % test_module_fail_result)

        # region 将执行失败的测试用例添加到xml文件
        if test_module_fail_result != '' and firmware_info_path != 'unknown':
            # 有些用例需要前面用例先执行，如果只执行模块下后几条用例可能会出错，所以整个模块用例再重复执行
            firmware_info_result_fail_file_name = firmware_info_file_name.replace('.xml',
                                                                                  '_module_fail.xml')
            firmware_info_result_fail_path = os.path.join(aklog_get_result_dir(),
                                                          firmware_info_result_fail_file_name)
            File_process.copy_file(firmware_info_path, firmware_info_result_fail_path)
            xml_add_attributes(firmware_info_result_fail_path, 'test_cases',
                               {'modules': test_module_fail_result})
            xml_add_attributes(firmware_info_result_fail_path, 'test_cases',
                               {'cases': '\n'})

        if test_case_fail_result != '' and firmware_info_path != 'unknown':
            # 有些用例没有必须要执行的用例，也可以单独跑出错的用例，所以生成两个xml文件，根据需要选择
            firmware_info_result_case_fail_file_name = firmware_info_file_name.replace('.xml',
                                                                                       '_case_fail.xml')
            firmware_info_result_case_fail_path = os.path.join(aklog_get_result_dir(),
                                                               firmware_info_result_case_fail_file_name)
            File_process.copy_file(firmware_info_path, firmware_info_result_case_fail_path)
            xml_add_attributes(firmware_info_result_case_fail_path, 'test_cases',
                               {'modules': '\n'})
            xml_add_attributes(firmware_info_result_case_fail_path, 'test_cases',
                               {'cases': test_case_fail_result})
        # endregion

        # region 获取测试结果汇总
        if test_case_all_counts != 0:
            if test_case_all_counts - test_case_skip_counts == 0:
                test_pass_rate = 0.0
            else:
                test_pass_rate = round(
                    test_case_pass_counts / (test_case_all_counts - test_case_skip_counts) * 100, 4)
        g_test_results_summary['Total_testcases'] = test_case_all_counts
        g_test_results_summary['Pass_testcases'] = test_case_pass_counts
        g_test_results_summary['Pass_rate'] = test_pass_rate
        g_test_results_summary['Test_date'] = test_date
        g_test_results_summary['Take_time'] = sec2minute(test_total_time, 1)
        g_test_results_summary['Product_name'] = report_model_name
        g_test_results_summary['Product_version'] = rom_version
        aklog_printf(f'g_test_results_summary: {g_test_results_summary}')
        # endregion

        # region 将测试结果汇总写入到results_summary.txt文件，后面合并发送邮件使用
        results_summary = 'total_case_counts: %s\n' \
                          'test_case_all_counts: %s\n' \
                          'test_case_pass_counts: %s\n' \
                          'test_case_fail_counts: %s\n' \
                          'test_case_error_counts: %s\n' \
                          'test_case_skip_counts: %s\n' \
                          'test_pass_rate: %s' \
                          % (total_case_counts, test_case_all_counts, test_case_pass_counts,
                             test_case_fail_counts,
                             test_case_error_counts, test_case_skip_counts, test_pass_rate)
        results_summary_file = report_dir + '\\results_summary.txt'
        aklog_printf('测试结果汇总写入到文件 file:///%s 里' % results_summary_file.replace('\\', '/'))
        with open(results_summary_file, 'w', encoding='utf-8') as fp:
            fp.write(results_summary)
        # endregion

        # region 获取Module用例模块测试结果，并写入到module_results.txt文件
        result_file = os.path.join(report_dir, 'Result.txt')
        module_results_file = os.path.join(report_dir, 'module_results.txt')
        case_results_file = os.path.join(report_dir, 'case_results.txt')
        parse_results_file(result_file, case_results_file, module_results_file)
        # endregion

        # region 发送测试结果汇总到服务器
        report_file_url = ''
        if send_test_results_summary_enable and product_line == 'SMARTHOME' and test_case_all_counts > 0:
            # 将测试报告复制到HTTP服务器，方便直接浏览器打开
            report_file_url = send_report_file_to_http_server(report_file)

            aklog_info('send test results to sql')
            test_results_summary = {
                'test_count': test_case_all_counts,
                'pass_count': test_case_pass_counts,
                'fail_count': test_case_fail_counts,
                'error_count': test_case_error_counts,
                'skip_count': test_case_skip_counts,
                'pass_rate': f'{test_pass_rate}%',
                'test_version': rom_version,
                'test_date': test_date,
                'test_duration': seconds_to_duration(test_total_time),
                'build_user': build_user,
                'url': report_file_url
            }

            test_case_sql.connect()
            if g_test_results_summary['Test_type'] == 'stress-test':
                for module_name in module_class_test_result:
                    if module_class_test_result[module_name]['test_type'] != 'stress-test':
                        continue
                    module_class_test_result[module_name]['test_duration'] = seconds_to_duration(
                        module_class_test_result[module_name]['test_duration']
                    )
                    module_class_test_result[module_name]['test_version'] = rom_version
                    module_class_test_result[module_name]['test_date'] = test_date
                    module_class_test_result[module_name]['build_user'] = build_user
                    module_class_test_result[module_name]['url'] = report_file_url
                    test_case_sql.write_press_test_results(
                        report_model_name, module_class_test_result[module_name])
            else:
                test_case_sql.write_function_test_results(
                    report_model_name, test_results_summary)
            # test_results_summary_url = config_get_value_from_ini_file('config', 'test_results_summary_url')
            # ak_requests = AkRequests('%s/%s' % (test_results_summary_url, test_date))
            # ak_requests.send_post(g_test_results_summary)
            # ak_requests.close()

        # endregion

        # 复制到共享文件夹存档
        if product_line == 'INTERCOM':
            intercom_report_to_server(aklog_get_result_dir(), g_test_results_summary, test_case_skip_counts, 20)
            intercom_copy_report_to_smb(aklog_get_result_dir(), g_test_results_summary, test_case_skip_counts, 20)

        # 发送测试报告
        test_result = True if (test_case_all_counts - test_case_pass_counts
                               - test_case_skip_counts == 0) else False
        send_email_or_work_weixin(
            report_file, report_model_name, oem_name, rom_version, test_result, report_file_url)

        aklog_info('测试已全部完成, 可前往 file:///{} 查询测试报告'.format(report_file.replace('\\', '/')))

        unittest_stop_run()
        return True
    except:
        aklog_error('############################################################')
        aklog_error('遇到未知异常, 程序退出! ' + str(traceback.format_exc()))
        aklog_error('############################################################')
        unittest_stop_run()
        return False


def start_in_sub_process_with_xml(
        process_name, firmware_info_path, temp_config_file=None, stop_event=None, queue=None, build_env='jenkins'):
    aklog_printf('start_in_sub_process_with_xml, %s, firmware_info_path: %s' % (process_name, firmware_info_path))
    intercom_send_email_addr = ''
    try:
        parse_test_main()
        param_put_firmware_info_path(firmware_info_path)
        firmware_info_sheet_data = xml_read_sheet_data(firmware_info_path)
        param_put_firmware_info_data(firmware_info_sheet_data)
        firmware_info = firmware_info_sheet_data['firmware_info'][0]
        param_put_firmware_info(firmware_info)
        firmware_version = firmware_info['firmware_version']
        if firmware_version:
            firmware_version = firmware_version.strip()

        # 根据版本号获取机型名称、OEM名称、web密码等版本信息
        version = firmware_version.split('.')
        model_id = version[0]
        model_name = config_get_modelname(model_id)

        series_products = config_get_series(model_name)
        param_put_seriesproduct_name(series_products)

        if series_products == 'LINUXINDOOR' and int(version[2]) > 100:
            aklog_printf('嵌入式室内机，版本 %s 为大包，退出测试' % firmware_version)
            return False

        product_line = config_get_product_line(series_products)
        param_put_product_line_name(product_line)
        if param_get_product_line_name().lower() == 'intercom':
            if not firmware_info.get("firmware_path"):
                if 'launch_config' in firmware_info_sheet_data:
                    launch_config = firmware_info_sheet_data['launch_config'][0]
                    send_email_addr = launch_config.get('send_email_addr')
                    if send_email_addr is not None and send_email_addr.strip() != '':
                        send_email_addr = send_email_addr.strip().replace('；', ';').strip('+')
                        robot_send_text_msg(
                            f'{firmware_version} : 禅道自动化触发任务, 测试单没有填写rom包路径, 退出测试',
                            send_email_addr)
                aklog_error('禅道自动化触发任务, 测试单没有填写rom包路径, 退出测试')
                return False

        aklog_init(model_name, log_level=5)

        # 获取启动配置参数
        if 'launch_config' in firmware_info_sheet_data:
            launch_config = firmware_info_sheet_data['launch_config'][0]

            test_times = launch_config.get('test_times')
            test_times = 1 if test_times is None else test_times
            param_put_test_times(int(test_times))

            test_counts = launch_config.get('test_counts')
            test_counts = 1 if test_counts is None else test_counts
            param_put_test_counts(int(test_counts))

            test_random = launch_config.get('test_random')
            test_random = True if test_random == '1' else False
            param_put_test_random_state(test_random)

            browser_headless_enable = launch_config.get('browser_headless_enable')
            browser_headless_enable = True if browser_headless_enable == '1' else False
            param_put_browser_headless_enable(browser_headless_enable)

            skip_download_firmware = launch_config.get('skip_download_firmware')
            skip_download_firmware = True if skip_download_firmware == '1' else False
            param_put_skip_download_firmware_state(skip_download_firmware)

            send_test_results_summary_enable = launch_config.get('send_test_results_summary_enable')
            send_test_results_summary_enable = True if send_test_results_summary_enable == '1' else False
            param_put_send_test_results_summary_enable(send_test_results_summary_enable)

            exec_one_case_to_report_enable = launch_config.get('exec_one_case_to_report_enable')
            exec_one_case_to_report_enable = True if exec_one_case_to_report_enable == '1' else False
            param_put_exec_one_case_to_report_enable(exec_one_case_to_report_enable)

            send_email_enable = launch_config.get('send_email_enable')
            send_email_enable = True if send_email_enable == '1' else False
            param_put_send_email_state(send_email_enable)

            send_work_weixin_enable = launch_config.get('send_work_weixin_enable')
            send_work_weixin_enable = True if send_work_weixin_enable == '1' else False
            param_put_send_work_weixin_state(send_work_weixin_enable)

            pause_during_nap_time_enable = launch_config.get('pause_during_nap_time_enable')
            pause_during_nap_time_enable = True if pause_during_nap_time_enable == '1' else False
            param_put_pause_during_nap_time_enable(pause_during_nap_time_enable)

            retry_counts = launch_config.get('retry_counts')
            retry_counts = 1 if retry_counts is None else retry_counts
            param_put_retry_counts(int(retry_counts))

            save_last_try = launch_config.get('save_last_try')
            save_last_try = True if save_last_try == '1' else False
            param_put_save_last_try_state(save_last_try)

            failed_to_exit = launch_config.get('failed_to_exit')
            failed_to_exit = True if failed_to_exit == '1' else False
            param_put_failed_to_exit_enable(failed_to_exit)

            test_case_balance_enable = launch_config.get('test_case_balance_enable')
            test_case_balance_enable = True if test_case_balance_enable == '1' else False
            param_put_test_case_balance_enable(test_case_balance_enable)

            upgrade_cover_counts = launch_config.get('upgrade_cover_counts')
            upgrade_cover_counts = None if upgrade_cover_counts is None else int(upgrade_cover_counts)
            param_put_upgrade_cover_counts(upgrade_cover_counts)

            send_email_addr = launch_config.get('send_email_addr')
            if send_email_addr is not None and send_email_addr.strip() != '':
                send_email_addr = send_email_addr.strip()
                send_email_addr = send_email_addr.replace('；', ';')
                aklog_printf(send_email_addr)
                if send_email_addr.startswith('+'):
                    send_email_addr = send_email_addr.replace('+', '')
                    email_receivers = send_email_addr.split(';')
                    new_email_receivers = []
                    for receiver in email_receivers:
                        receiver = receiver.strip()
                        if receiver != '':
                            new_email_receivers.append(receiver)
                    param_put_added_email_receivers(new_email_receivers)
                    aklog_printf('added email receivers: %r' % new_email_receivers)
                else:
                    email_receivers = send_email_addr.split(';')
                    new_email_receivers = []
                    for receiver in email_receivers:
                        receiver = receiver.strip()
                        if receiver != '':
                            new_email_receivers.append(receiver)
                    param_put_email_receivers(new_email_receivers)
                    aklog_printf('email receivers: %r' % new_email_receivers)

        # XML文件指定测试用例
        if 'test_cases' in firmware_info_sheet_data:
            test_cases = firmware_info_sheet_data['test_cases'][0]
            modules = test_cases.get('modules')
            if modules is not None and modules.strip() != '':
                module_list = modules.split(';')
                for i in range(len(module_list)):
                    module_list[i] = module_list[i].strip()
                    if module_list[i] == '':
                        module_list.pop(i)
            else:
                module_list = []

            cases = test_cases.get('cases')
            if cases is not None and cases.strip() != '':
                case_list = cases.split(';')
                for i in range(len(case_list)):
                    case_list[i] = case_list[i].strip()
                    if case_list[i] == '':
                        case_list.pop(i)
            else:
                case_list = []
            module_list.extend(case_list)
            aklog_printf('module_list: %r' % module_list)
            param_put_module_list(module_list)

        aklog_printf('检测到新版本，开始测试：%s' % firmware_info_path)
        parse_firmware_version_from_xml(build_env=build_env)
        if temp_config_file:
            param_put_temp_ini_file(temp_config_file)
        if stop_event:
            param_put_stop_process_event(stop_event)

        # 2025.8.12 对讲终端添加提示
        if param_get_product_line_name().lower() == 'intercom':
            if 'launch_config' in firmware_info_sheet_data:
                launch_config = firmware_info_sheet_data['launch_config'][0]
                intercom_send_email_addr = launch_config.get('send_email_addr')
                if intercom_send_email_addr is not None and intercom_send_email_addr.strip() != '':
                    intercom_send_email_addr = intercom_send_email_addr.strip().replace('；', ';').strip('+')
                    robot_send_text_msg(
                        f'{firmware_version} : 禅道自动化任务 {param_get_jenkins_job_name()} 准备开始执行!',
                        intercom_send_email_addr)
        ret = auto_test_start()
        if param_get_product_line_name().lower() == 'intercom' and intercom_send_email_addr:
            robot_send_text_msg(f'{firmware_version} : 禅道自动化任务 {param_get_jenkins_job_name()} 执行完成!',
                                intercom_send_email_addr)
        if queue:
            queue.put(ret)
        return ret
    except:
        aklog_printf('遇到未知异常, 程序退出! ' + str(traceback.format_exc()))
        if param_get_product_line_name().lower() == 'intercom' and intercom_send_email_addr:
            robot_send_text_msg(
                f'{firmware_version} : 禅道自动化任务  {param_get_jenkins_job_name()} 遇到未知异常, 程序退出!\n{str(traceback.format_exc())}',
                intercom_send_email_addr)
        if queue:
            queue.put(False)
        return False


def trigger_test_by_xml(event):
    try:
        if event.event_type != 'created':
            aklog_printf('don\'t trigger test because of no-created: ' + event.event_type)
            return True

        time.sleep(5)  # 当检测到文件改动后, 文件可能还处于拷贝过程, 等待一段时间后再开始
        if os.path.isfile(event.src_path) and event.src_path.find(".xml") != -1:  # 判断是个文件且格式为.xml
            pass
        else:
            aklog_printf('don\'t trigger test because of no-xml: ' + event.src_path)
            return True

        firmware_info_file_name = os.path.split(event.src_path)[1]
        local_firmware_info_path = '%s\\testfile\\Firmware\\FirmwareInfo\\%s' % (root_path, firmware_info_file_name)
        File_process.copy_file(event.src_path, local_firmware_info_path)
        time.sleep(2)
        p = Process(target=start_in_sub_process_with_xml, args=('auto test', local_firmware_info_path))
        p.start()
        p.join()  # 让主线程等待某一子进程结束，才继续执行主进程
        time.sleep(3)
        if p.is_alive():  # 判断进程是否是“活着”的状态
            p.terminate()
        File_process.remove_file(event.src_path)  # 测试完成后删除监控目录下的xml文件
        return True
    except:
        aklog_printf('遇到未知异常, 程序退出! ' + str(traceback.format_exc()))
        return False


def trigger_test_by_xml_without_mutex(event):
    try:
        if event.event_type != 'created':
            aklog_printf('don\'t trigger test because of no-created: ' + event.event_type)
            return True

        time.sleep(5)  # 当检测到文件改动后, 文件可能还处于拷贝过程, 等待一段时间后再开始
        if os.path.isfile(event.src_path) and event.src_path.find(".xml") != -1:  # 判断是个文件且格式为.xml
            pass
        else:
            aklog_printf('don\'t trigger test because of no-xml: ' + event.src_path)
            return True

        firmware_info_file_name = os.path.split(event.src_path)[1]
        local_firmware_info_path = '%s\\testfile\\Firmware\\FirmwareInfo\\%s' % (root_path, firmware_info_file_name)
        File_process.copy_file(event.src_path, local_firmware_info_path)
        time.sleep(2)
        File_process.remove_file(event.src_path)  # 测试完成后删除监控目录下的xml文件

        p = Process(target=start_in_sub_process_with_xml, args=('auto test', local_firmware_info_path))
        p.start()
        return True
    except:
        aklog_printf('遇到未知异常, 程序退出! ' + str(traceback.format_exc()))
        return False


def jenkins_build_start_by_xml(file_path, jenkins_job_name='', debug=False):
    """自动化执行解析xml文件"""
    aklog_info()
    try:
        # 将firmware info文件复制到本地路径
        if file_path.startswith('./AKautotest'):
            file_path = root_path + file_path.split('./AKautotest')[-1].replace('/', '\\')
        elif file_path.startswith('./FirmwareInfo'):
            if jenkins_job_name and jenkins_job_name in root_path:
                # 如果根目录包含了jenkins job 名称，说明不是自定义工作空间
                job_ws_path = root_path.split(jenkins_job_name)[0] + jenkins_job_name
            else:
                # 获取Jenkins工作空间根目录
                job_ws_path = os.path.split(root_path)[0]
            file_path = job_ws_path + file_path.replace('./', '\\').replace('/', '\\')

        aklog_printf('file_path: %s' % file_path)
        firmware_info_file = os.path.split(file_path)[1]
        file_name = os.path.splitext(firmware_info_file)[0]
        local_firmware_info_dir = '%s\\testfile\\Firmware\\FirmwareInfo\\%s\\' % (root_path, jenkins_job_name)
        if not os.path.exists(local_firmware_info_dir):
            os.makedirs(local_firmware_info_dir)
        local_firmware_info_path = local_firmware_info_dir + firmware_info_file
        File_process.remove_file(local_firmware_info_path)
        time.sleep(1)
        File_process.copy_file(file_path, local_firmware_info_path)
        time.sleep(1)
        if not debug:
            File_process.remove_file(file_path)  # 删除Jenkins上传的xml文件

        ret = start_in_sub_process_with_xml('AutoTest--' + file_name, local_firmware_info_path)
        if ret:
            time.sleep(5)
            return ret
        else:
            exit(-1)
    except:
        aklog_printf('遇到未知异常, 程序退出! ' + str(traceback.format_exc()))
        exit(-1)


def parse_jenkins_exec_job_list(file_path, sub_job_list: list):
    """根据用例解析jenkins分布式构建要执行用例的工程列表"""
    aklog_printf('parse_jenkins_exec_job_list')
    try:
        # 将firmware info文件复制到本地路径
        if file_path.startswith('./AKautotest'):
            file_path = root_path + file_path.split('./AKautotest')[-1].replace('/', '\\')
        elif file_path.startswith('./FirmwareInfo'):
            # 获取Jenkins工作空间根目录
            if '\\Develop\\AKautotest' in root_path:
                job_ws_path = root_path.replace('/', '\\').replace('\\Develop\\AKautotest', '')
            else:
                job_ws_path = os.path.split(root_path)[0]
            file_path = job_ws_path + file_path.replace('./', '\\').replace('/', '\\')

        if not os.path.exists(file_path):
            aklog_error('firmware_info XML文件不存在')
            exit(-1)
        aklog_printf('firmware_info_file_path: %s' % file_path)
        param_put_firmware_info_path(file_path)
        firmware_info_sheet_data = xml_read_sheet_data(file_path)

        firmware_info = firmware_info_sheet_data['firmware_info'][0]
        param_put_firmware_info(firmware_info)
        firmware_version = firmware_info['firmware_version']
        if firmware_version:
            firmware_version = firmware_version.strip()
        # 根据版本号获取机型名称、OEM名称、web密码等版本信息
        version = firmware_version.split('.')
        model_id = version[0]
        model_name = config_get_modelname(model_id)

        # 获取启动配置参数
        if 'launch_config' in firmware_info_sheet_data:
            launch_config = firmware_info_sheet_data['launch_config'][0]
            firmware_version = firmware_info['firmware_version']
            if firmware_version:
                firmware_version = firmware_version.strip()
            version = firmware_version.split('.')
            model_id = version[0]
            model_name = config_get_modelname(model_id)
            series_products = config_get_series(model_name)
            product_line = config_get_product_line(series_products)
            if product_line.lower() == 'intercom':
                # 判断jenkins上是否有活跃 重复的任务,
                # 避免禅道多次点击触发相同任务重复执行等待耗时.
                intercom_send_email_addr = launch_config.get('send_email_addr')
                if intercom_send_email_addr is not None and intercom_send_email_addr.strip() != '':
                    intercom_send_email_addr = intercom_send_email_addr.strip().replace('；', ';').strip('+')
                else:
                    intercom_send_email_addr = ''

                if series_products.lower() == 'androidindoor':
                    repeat_version, repeat_num = is_jenkins_task_repeat('AndroidIndoor', file_path)
                    if repeat_version:
                        if intercom_send_email_addr:
                            robot_send_text_msg(
                                f'禅道AndroidIndoor: {repeat_version}自动化任务已有重复任务在运行或等待, 创建号: {repeat_num}',
                                intercom_send_email_addr)
                        aklog_error_tag(
                            f'禅道AndroidIndoor: {repeat_version}自动化任务已有重复任务在运行或等待, 创建号: {repeat_num}')
                        aklog_remove()
                        raise repeatTaskError
                elif series_products.lower() == 'linuxindoor':
                    repeat_version, repeat_num = is_jenkins_task_repeat('LinuxIndoor', file_path)
                    if repeat_version:
                        if intercom_send_email_addr:
                            robot_send_text_msg(
                                f'禅道LinuxIndoor: {repeat_version}自动化任务已有重复任务在运行或等待, 创建号: {repeat_num}',
                                intercom_send_email_addr)
                        aklog_error_tag(
                            f'禅道LinuxIndoor: {repeat_version}自动化任务已有重复任务在运行或等待, 创建号: {repeat_num}')
                        aklog_remove()
                        raise repeatTaskError
                if intercom_send_email_addr:
                    robot_send_text_msg(f'{firmware_version} : 禅道自动化任务已经构建, 等待空闲后开始执行!',
                                        intercom_send_email_addr)

            test_times = launch_config.get('test_times')
            test_times = 1 if test_times is None else test_times
            param_put_test_times(int(test_times))

            test_counts = launch_config.get('test_counts')
            test_counts = 1 if test_counts is None else test_counts
            param_put_test_counts(int(test_counts))

            test_random = launch_config.get('test_random')

            test_random = True if test_random == '1' else False
            param_put_test_random_state(test_random)

            browser_headless_enable = launch_config.get('browser_headless_enable')
            browser_headless_enable = True if browser_headless_enable == '1' else False
            param_put_browser_headless_enable(browser_headless_enable)

            skip_download_firmware = launch_config.get('skip_download_firmware')
            skip_download_firmware = True if skip_download_firmware == '1' else False
            param_put_skip_download_firmware_state(skip_download_firmware)

            send_test_results_summary_enable = launch_config.get('send_test_results_summary_enable')
            send_test_results_summary_enable = True if send_test_results_summary_enable == '1' else False
            param_put_send_test_results_summary_enable(send_test_results_summary_enable)

            exec_one_case_to_report_enable = launch_config.get('exec_one_case_to_report_enable')
            exec_one_case_to_report_enable = True if exec_one_case_to_report_enable == '1' else False
            param_put_exec_one_case_to_report_enable(exec_one_case_to_report_enable)

            send_email_enable = launch_config.get('send_email_enable')
            send_email_enable = True if send_email_enable == '1' else False
            param_put_send_email_state(send_email_enable)

            retry_counts = launch_config.get('retry_counts')
            retry_counts = 1 if retry_counts is None else retry_counts
            param_put_retry_counts(int(retry_counts))

            save_last_try = launch_config.get('save_last_try')
            save_last_try = True if save_last_try == '1' else False
            param_put_save_last_try_state(save_last_try)

            failed_to_exit = launch_config.get('failed_to_exit')
            failed_to_exit = True if failed_to_exit == '1' else False
            param_put_failed_to_exit_enable(failed_to_exit)

            test_case_balance_enable = launch_config.get('test_case_balance_enable')
            test_case_balance_enable = True if test_case_balance_enable == '1' else False
            param_put_test_case_balance_enable(test_case_balance_enable)

            send_email_addr = launch_config.get('send_email_addr')
            if send_email_addr is not None and send_email_addr.strip() != '':
                send_email_addr = send_email_addr.replace('；', ';')
                email_receivers = send_email_addr.split(';')
                new_email_receivers = []
                for receiver in email_receivers:
                    receiver = receiver.strip()
                    if receiver != '':
                        new_email_receivers.append(receiver)
                param_put_email_receivers(new_email_receivers)
                aklog_printf('email receivers: %r' % new_email_receivers)

        # XML文件指定测试用例
        if 'test_cases' in firmware_info_sheet_data:
            test_cases = firmware_info_sheet_data['test_cases'][0]
            modules = test_cases.get('modules')
            if modules is not None and modules.strip() != '':
                module_list = modules.split(';')
                for i in range(len(module_list)):
                    module_list[i] = module_list[i].strip()
                    if module_list[i] == '':
                        module_list.pop(i)
            else:
                module_list = []

            cases = test_cases.get('cases')
            if cases is not None and cases.strip() != '':
                case_list = cases.split(';')
                for i in range(len(case_list)):
                    case_list[i] = case_list[i].strip()
                    if case_list[i] == '':
                        case_list.pop(i)
            else:
                case_list = []
            module_list.extend(case_list)
            aklog_printf('module_list: %r' % module_list)
            param_put_module_list(module_list)

        parse_firmware_version_from_xml(build_env='jenkins')

        # 创建测试套件
        module_list = param_get_module_list()
        if module_list:
            modules_dict = config_parse_modules_from_xml(module_list)
        else:
            modules = param_get_modules()
            if not modules:
                aklog_error("用例解析失败，请检查选择的测试用例或测试套件是否正确")
                aklog_remove()
                exit(-1)

            adapter = module_case_adapter()
            modules_dict = adapter.create_test_case_dict()

        aklog_printf('modules_dict : %r' % modules_dict)

        if not modules_dict:
            aklog_error("用例解析失败，请检查选择的测试用例或测试套件是否正确")
            aklog_remove()
            exit(-1)

        # 过滤Jenkins节点用例名称列表
        job_name_lines = ''
        job_exec_module_lines = ''
        job_name_list = []
        if param_get_jenkins_distribute_enable():
            for job_name in sub_job_list:
                aklog_printf('job_name: %s' % job_name)
                # 过滤自动化升级环境的Jenkins节点用例名称列表
                if 'AutotestUpgrade' in job_name and not job_name.endswith(model_name):
                    job_name_lines += '%s_enable=0\n' % job_name
                    continue

                sub_modules_dict = config_parse_jenkins_module_dict(job_name, modules_dict)
                sub_modules_dict = config_parse_jenkins_exec_job_exclude_only_init_case(job_name, sub_modules_dict)
                if not sub_modules_dict:
                    job_name_lines += '%s_enable=0\n' % job_name
                else:
                    job_name_list.append(job_name)
                    job_name_lines += '%s_enable=1\n' % job_name
                    job_exec_module_lines += '\n[%s] 节点执行用例列表:\n' % job_name
                    job_exec_module_lines += '\n'.join(sorted(sub_modules_dict.keys())) + '\n'

            # if len(job_name_list) == 1:
            #     aklog_info('解析出来只有一个job在运行，当做非分布式处理，所有用例只在这个job上执行')
            #     job_name_lines += 'distribute_enable=false\n'
            job_name_lines += 'start_by_upstream_project_enable=true\n'

        aklog_printf('jenkins_job_name_list: \n%s' % job_name_lines)
        if job_name_lines and 'enable=1' in job_name_lines:
            jenkins_job_name_list_file = param_get_jenkins_report_dir() + 'job_name_list.txt'
            # 该文件也包含了子工程执行jenkins_build_test.py的一些参数
            with open(jenkins_job_name_list_file, 'w', encoding='utf-8') as fp:
                fp.write(job_name_lines)
        elif job_name_lines and 'enable=1' not in job_name_lines:
            aklog_warn('没有可以执行该用例列表的job，请检查选择的用例是否只有Init用例，或者在子任务单独执行该用例')
            exit(-1)
        else:
            aklog_error('没有可以执行该用例列表的job，请检查jenkins_module_list.xml文件')
            exit(-1)

        wait_time_before_start_test = int(config_get_value_from_ini_file('config', 'wait_time_before_start_test'))
        aklog_printf(job_exec_module_lines)
        aklog_info(
            '测试用例模块列表如上，如果有发现用例选择不正确，则可以停止运行，%s秒后开始执行' % wait_time_before_start_test)
        time.sleep(wait_time_before_start_test)
        aklog_info('已选择测试用例，开始测试')
        return True
    except repeatTaskError:
        failed_info = traceback.format_exc()
        aklog_printf(failed_info)
        exit(-1)
    except:
        failed_info = traceback.format_exc()
        try:
            robot_send_text_msg(f'{firmware_version} : 禅道自动化任务构建异常停止!\n{failed_info}',
                                intercom_send_email_addr)
        except:
            pass
        aklog_printf(failed_info)
        exit(-1)


def continuous_running_thread():
    """持续运行监控目录，当目录下没有FirmwareInfo的xml文件时，复制XML文件到持续运行监控目录，继续执行"""
    aklog_printf('continuous_running_thread')
    while True:
        monitor_path = root_path + '\\testfile\\Monitor\\ContinuousRunning'
        firmware_info_path = root_path + '\\testdata\\FirmwareInfo\\ContinuousRunning'
        files = File_process.get_files_with_ext_from_path(monitor_path, '.xml')
        if not files:
            aklog_printf('监控目录不存在xml文件，复制xml文件到监控目录')
            File_process.copy_files_with_ext_from_path(firmware_info_path, monitor_path, '.xml')
        else:
            aklog_printf('监控目录还存在xml文件，在运行中')
            pass
        time.sleep(300)


def web_upgrade_new_version_by_branch(model_name, current_version, browser):
    versions = current_version.split('.')
    version4 = int(versions[3]) // 100
    branch = '%d.%d' % (int(versions[2]), int(version4))
    web_version = config_parse_web_version_branch(model_name, branch)
    if web_version == 'WEB4_0':
        device_web = web_v4_device_NORMAL()
    elif web_version == 'WEB3_0':
        device_web = web_v3_device_NORMAL()
    else:
        device_web = web_device_NORMAL()
    device_web.init(browser)
    device_web.login()
    device_web.upgrade_new_version()
    device_web.browser_close_and_quit()


def is_jenkins_task_repeat(branch='AndroidIndoor', firmware_xml_file_path=''):
    """
    判断jenkins任务是否有重复任务. 有的话返回对应创建号
    """
    try:
        with open(firmware_xml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            targetversion = re.search('<firmware_version>(.*)</firmware_version>', content).group(1)
            targetmodulestr = re.search('<modules_name>(.*)</modules_name>', content).group(1)
            targetmodulelist = sorted(list(set([i.strip() for i in targetmodulestr.split(';') if i.strip()])))

        version_modulelist_dict = {}
        url = 'http://192.168.10.14:8080/j_spring_security_check'
        data = {'j_username': 'irene', 'j_password': '123456', 'from': '/', 'Submit': "", 'remember_me': 'on'}
        if branch == 'linuxindoor':
            url2 = 'http://192.168.10.14:8080/job/LinuxIndoor_Start_Develop/'
            url3 = 'http://192.168.10.14:8080/job/LinuxIndoor_Start_Develop/{num}/parameters/parameter/.%2FFirmwareInfo%2FLinuxIndoor_Start_Develop%2FFirmwareInfo.xml/.%2FFirmwareInfo%2FLinuxIndoor_Start_Develop%2FFirmwareInfo.xml/*view*'
        else:
            url2 = 'http://192.168.10.14:8080/job/AndroidIndoor_Start_Develop/'
            url3 = 'http://192.168.10.14:8080/job/AndroidIndoor_Start_Develop/{num}/parameters/parameter/.%2FFirmwareInfo%2FAndroidIndoor_Start_Develop%2FFirmwareInfo.xml/.%2FFirmwareInfo%2FAndroidIndoor_Start_Develop%2FFirmwareInfo.xml/*view*'

        s = requests.Session()
        r = s.post(url, data=data, timeout=5)
        if '用户名或密码错误' in r.text:
            aklog_error('登录jenkin错误')
            return False, False

        r2 = s.get(url2, timeout=10)
        list2 = re.findall(r'href=\".*?/(\d{3,6})/.*(?=class="progress-bar)', r2.text)  # 运行中, 等待中的任务
        if not list2:
            aklog_info('当前没有正在运行或者等待任务')
            return False, False

        for i in list2:
            r3 = s.get(url3.format(num=i), timeout=10)
            version = re.search('<firmware_version>(.*)</firmware_version>', r3.text).group(1)
            modulestr = re.search('<modules_name>(.*)</modules_name>', r3.text).group(1)
            modulelist = sorted(list(set([i.strip() for i in modulestr.split(';') if i.strip()])))
            if version.strip() == targetversion.strip() and modulelist == targetmodulelist:
                aklog_error(f'jenkins有重复执行任务, 对应创建号: {i}')
                return version, i
        return False, False
    except:
        aklog_error('尝试判断jenkins任务状态异常')
        aklog_debug(traceback.format_exc())
        return False, False


class repeatTaskError(BaseException):
    def __init__(self, message="重复任务错误"):
        self.message = message
        super().__init__(self.message)
