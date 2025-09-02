# -*- coding:utf-8 -*-

import sys
import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
if root_path not in sys.path:
    sys.path.append(root_path)

from akcommon_define import *
import time
import traceback
import lxml.etree as ET  # 使用该模块，可以读取注释，修改时也可以保留
import re


# 增加换行符
def __xml_indent(element, indent="\t", newline='\n', level=0):
    # indent = "\t"
    # newline = '\n'
    if len(element) == 0:  # 判断element是否有子元素
        element_text = element.text
        if element_text is not None:  # 如果内容本身就有换行，则每一行都进行换行缩进
            if '\n' in element_text:
                element_text_new = ''
                lines = element_text.split('\n')
                for line in lines:
                    if line.strip():
                        element_text_new += newline + indent * (level + 1) + line.strip()
                element_text_new += newline + indent * level
                element.text = element_text_new
            else:
                element.text = element_text.strip()
        # elif element_text is None or element_text.isspace():  # 如果element的text没有内容
        #     element.tail = newline + indent * level
    else:
        temp = list(element)  # 将element转成list
        if not element.text or not element.text.strip():
            element.text = newline + indent * (level + 1)  # 如果存在子节点，且text为空，需要增加换行缩进
        for sub_element in temp:
            if temp.index(sub_element) < (len(temp) - 1):  # 如果不是list的最后一个元素，说明下一个行是同级别元素的起始，缩进应一致
                sub_element.tail = newline + indent * (level + 1)
            else:  # 如果是list的最后一个元素， 说明下一行是母元素的结束，缩进应该少一个
                sub_element.tail = newline + indent * level
            __xml_indent(sub_element, indent, newline, level=level + 1)  # 对子元素进行递归操作
    return element


"""
def __xml_indent(elem, level=0):
    # 增加换行符
    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            __xml_indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
"""


def reformat_xml_file(src_file, out_file):
    """格式化xml文件，增加换行符"""
    tree = ET.parse(src_file)
    root = tree.getroot()
    __xml_indent(root)  # 增加换行符
    tree.write(out_file, encoding='utf-8', xml_declaration=True)


def xml_format_all_files(dir_path):
    """批量给目录下包括子目录下的XML文件格式化输出"""
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if os.path.splitext(file)[1] != '.xml':
                continue
            file_path = os.path.join(root, file)
            aklog_printf(file_path)
            tree = ET.parse(file_path)
            tree_root = tree.getroot()
            __xml_indent(tree_root)  # 增加换行符，格式化
            tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_write_from_excel_data(excel_data, dst_path):
    """
    把excel表格读取出来的数据写入到xml文件，一个工作表写一个文件
    :param excel_data: 从excel表格获取出来的数据，dict类型
    :param dst_path: xml文件保存的目录
    :return:
    """
    aklog_debug()
    for key in excel_data:
        root = ET.Element('root')  # 创建节点
        tree = ET.ElementTree(root)  # 创建文档

        sheet_element = ET.Element(str(key))
        root.append(sheet_element)

        for j in range(len(excel_data[key])):
            element = ET.Element('line')
            # element.set('index', str(j+1))

            for key2 in excel_data[key][j]:
                sub_element = ET.Element(str(key2))
                sub_element.text = excel_data[key][j][key2]
                element.append(sub_element)

            sheet_element.append(element)

        __xml_indent(root)  # 增加换行符
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        file_path = os.path.join(dst_path, key + '.xml')
        tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_add_line_attribute(file_path, sheet, tag, text):
    """xml文件增加属性和值"""
    tree = ET.parse(file_path)
    root = tree.getroot()

    for sheet_node in root:
        if sheet_node.tag != sheet:
            continue
        for line_node in sheet_node:
            attribute = line_node.find(tag)
            if attribute is None:
                attribute = ET.Element(tag)
                attribute.text = text
                line_node.append(attribute)
            else:
                aklog_printf('%s is already exist' % tag)

    __xml_indent(root)  # 增加换行符
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_add_line_attributes(file_path, sheet, attribute_dict):
    """xml文件批量增加属性和值，属性和值为字典类型"""
    tree = ET.parse(file_path)
    root = tree.getroot()

    for sheet_node in root:
        if sheet_node.tag != sheet:
            continue
        for line_node in sheet_node:
            if type(attribute_dict) != dict:
                aklog_printf('%s type is not dict' % attribute_dict)
                return False
            for tag in attribute_dict:
                attribute = line_node.find(tag)
                if attribute is None:
                    attribute = ET.Element(tag)
                    attribute.text = attribute_dict[tag]
                    line_node.append(attribute)

    __xml_indent(root)  # 增加换行符
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_add_all_files_line_attribute(dir_path, sheet, tag, text):
    """批量给目录包括子目录下xml文件增加属性"""
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if os.path.splitext(file)[1] != '.xml':
                continue
            file_path = os.path.join(root, file)
            aklog_printf(file_path)
            tree = ET.parse(file_path)
            tree_root = tree.getroot()

            for sheet_node in tree_root:
                if sheet_node.tag != sheet:
                    continue
                for line_node in sheet_node:
                    attribute = line_node.find(tag)
                    if attribute is None:
                        attribute = ET.Element(tag)
                        attribute.text = text
                        line_node.append(attribute)
                    else:
                        attribute.text = text

            __xml_indent(tree_root)  # 增加换行符
            tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_modify_line_attribute(file_path, sheet, tag, text):
    """修改xml文件中某个属性的值"""
    tree = ET.parse(file_path)
    tree_root = tree.getroot()

    for sheet_node in tree_root:
        if sheet_node.tag != sheet:
            continue
        for line_node in sheet_node:
            attribute = line_node.find(tag)
            if attribute is not None:
                attribute.text = text

    __xml_indent(tree_root)  # 增加换行符
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_modify_all_files_line_attribute(dir_path, sheet, tag, text):
    """批量修改目录包括子目录下xml文件中某个属性的值"""
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if os.path.splitext(file)[1] != '.xml':
                continue
            flag = False
            file_path = os.path.join(root, file)
            tree = ET.parse(file_path)
            tree_root = tree.getroot()
            for sheet_node in tree_root:
                if sheet_node.tag != sheet:
                    continue
                for line_node in sheet_node:
                    attribute = line_node.find(tag)
                    if attribute is not None and attribute.text != text:
                        flag = True
                        attribute.text = text
            if flag:
                aklog_printf(file_path)
                __xml_indent(tree_root)  # 增加换行符
                tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_modify_specify_line_attribute(file_path, sheet, specify_attr, specify_value, **kwargs):
    """修改xml文件中某个属性的值"""
    aklog_debug()
    tree = ET.parse(file_path)
    tree_root = tree.getroot()

    for sheet_node in tree_root:
        if sheet_node.tag != sheet:
            continue
        for line_node in sheet_node:
            sub_node = line_node.find(specify_attr)
            sub_text = sub_node.text
            if sub_text != specify_value:
                # aklog_debug(sub_text)
                continue
            for tag in kwargs.keys():
                attribute = line_node.find(tag)
                if attribute is None:
                    attribute = ET.Element(tag)
                    attribute.text = kwargs[tag]
                    line_node.append(attribute)
                else:
                    attribute.text = kwargs[tag]
                # aklog_debug(attribute.text)

    __xml_indent(tree_root)  # 增加换行符
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_del_specify_line(file_path, sheet, **kwargs):
    """删除xml文件指定的某一行"""
    aklog_debug()
    tree = ET.parse(file_path)
    tree_root = tree.getroot()

    for sheet_node in tree_root:
        if sheet_node.tag != sheet:
            continue
        del_line_node = None
        for line_node in sheet_node:
            flag = True
            for tag in kwargs.keys():
                sub_node = line_node.find(tag)
                sub_text = sub_node.text
                if sub_text != kwargs[tag]:
                    flag = False
                    break
            if not flag:
                continue
            else:
                del_line_node = line_node
        if del_line_node is not None and len(del_line_node) > 0:
            sheet_node.remove(del_line_node)

    __xml_indent(tree_root)  # 增加换行符
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_modify_attribute(file_path, sheet, **kwargs):
    """
    修改xml文件中某个属性的值
    **kwargs为tag=text，比如model_name='C317', firmware_version='117.30.2.643'
    """
    if not os.path.exists(file_path):
        aklog_printf('%s is not found' % file_path)
        return False
    tree = ET.parse(file_path)
    tree_root = tree.getroot()

    for sheet_node in tree_root:
        if sheet_node.tag != sheet:
            continue
        for tag in kwargs.keys():
            for line_node in sheet_node:
                attribute = line_node.find(tag)
                if attribute is not None:
                    attribute.text = kwargs[tag]

    __xml_indent(tree_root)  # 增加换行符
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_modify_all_files_attribute(dir_path, file_name, sheet, **kwargs):
    """
    批量修改目录包括子目录下xml文件中某个属性的值
    **kwargs为tag=text，比如model_name='C317', firmware_version='117.30.2.643'
    """
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file == file_name:
                flag = False
                file_path = os.path.join(root, file)
                tree = ET.parse(file_path)
                tree_root = tree.getroot()

                for sheet_node in tree_root:
                    if sheet_node.tag != sheet:
                        continue
                    for tag in kwargs.keys():
                        for line_node in sheet_node:
                            attribute = line_node.find(tag)
                            if attribute is not None and attribute.text != kwargs[tag]:
                                flag = True
                                attribute.text = kwargs[tag]
                if flag:
                    aklog_printf(file_path)
                    __xml_indent(tree_root)  # 增加换行符
                    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_add_attributes(file_path, sheet, *attributes):
    """
    xml文件添加或修改属性值
    :param file_path:
    :param sheet: root下一级节点名称
    :param attributes: 传入元组，每个元组是字典
    :return:
    """
    aklog_printf('xml_add_attributes, file_path: %s' % file_path)
    if not os.path.exists(file_path):
        aklog_printf('%s is not found' % file_path)
        return False
    try:
        tree = ET.parse(file_path)
        tree_root = tree.getroot()

        sheet_node = tree_root.find(sheet)
        if sheet_node is None:
            sheet_node = ET.Element(sheet)
            tree_root.append(sheet_node)

        line_node = sheet_node.find('line')
        if line_node is None:
            line_node = ET.Element('line')
            sheet_node.append(line_node)

        for attribute in attributes:
            for tag in attribute:
                sub_element = line_node.find(tag)
                if sub_element is None:
                    sub_element = ET.Element(tag)
                    sub_element.text = attribute[tag]
                    line_node.append(sub_element)
                else:
                    sub_element.text = attribute[tag]

        __xml_indent(tree_root)  # 增加换行符
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
    except:
        aklog_printf('出现异常，请检查: %s' % traceback.format_exc())
        return False


def xml_add_and_modify_all_files_attribute(dir_path, file_name, sheet, **kwargs):
    """
    批量添加或修改目录包括子目录下指定文件名的xml文件中某个属性的值
    比如批量修改testdata目录下version_branch.xml文件的云平台分支版本号：
    'E:/SVN_Python/Develop/AKautotest/testdata', 'version_branch.xml', 'version_branch', cloud_branch='cloudV6_3'
    """
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file == file_name:
                flag = False
                file_path = os.path.join(root, file)
                tree = ET.parse(file_path)
                tree_root = tree.getroot()

                for sheet_node in tree_root:
                    if sheet_node.tag != sheet:
                        continue
                    for tag in kwargs.keys():
                        for line_node in sheet_node:
                            attribute = line_node.find(tag)
                            if attribute is not None and attribute.text != kwargs[tag]:
                                flag = True
                                attribute.text = kwargs[tag]
                            elif attribute is None:
                                flag = True
                                sub_element = ET.Element(tag)
                                sub_element.text = kwargs[tag]
                                line_node.append(sub_element)
                if flag:
                    aklog_printf(file_path)
                    __xml_indent(tree_root)  # 增加换行符
                    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_delete_all_files_attribute(dir_path, file_name, sheet, *kwargs):
    """
    批量删除目录包括子目录下指定文件名的xml文件中某个属性
    """
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file == file_name:
                flag = False
                file_path = os.path.join(root, file)
                tree = ET.parse(file_path)
                tree_root = tree.getroot()

                for sheet_node in tree_root:
                    if sheet_node.tag != sheet:
                        continue
                    for tag in kwargs:
                        for line_node in sheet_node:
                            attribute = line_node.find(tag)
                            if attribute is not None and attribute.tag == tag:
                                flag = True
                                line_node.remove(attribute)
                if flag:
                    aklog_printf(file_path)
                    __xml_indent(tree_root)  # 增加换行符
                    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_delete_elements(tree_root, element_path):
    """
    递归遍历xml文件，找到所有path指定的节点并删除
    :param tree_root: 根节点
    :param element_path: /root/test_cases/line/cases
    :return:
    """
    elements = element_path.split('/')
    sub_node_path = element_path.replace('/' + elements[1], '')
    if len(elements) >= 3:
        nodes = tree_root.findall(elements[2])
        if nodes:
            for node in nodes:
                if len(elements) == 3:
                    tree_root.remove(node)
                xml_delete_elements(node, sub_node_path)


def xml_delete_attribute(file_path, element_path):
    """
    删除xml文件中path指定的节点
    :param file_path: xml文件路径
    :param element_path: /root/test_cases/line/cases
    :return:
    """
    tree = ET.parse(file_path)
    tree_root = tree.getroot()
    xml_delete_elements(tree_root, element_path)

    __xml_indent(tree_root)  # 增加换行符
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_read_all_config_device_info(env_name=None):
    """获取自动化环境下的device_info，给testdata目录下的device_info引用"""
    aklog_printf()
    data_list = []
    sheet_name_list = []
    file_dict = {}

    # 先获取文件列表
    device_info_dir = os.path.join(g_config_path, 'libconfig_xml', 'device_info')
    for file in os.listdir(device_info_dir):
        if not file.endswith('.xml'):
            continue
        file_path = os.path.join(device_info_dir, file)
        file_dict[file] = file_path

    if env_name:
        # 如果获取指定环境的device_info，则将文件列表清空，只保留该环境的device_info文件
        file_name = 'device_info__%s.xml' % env_name
        if file_name in file_dict:
            file_path = file_dict[file_name]
            file_dict.clear()
            file_dict[file_name] = file_path

    for file in file_dict:
        file_path = file_dict[file]
        tree = ET.parse(file_path)
        root = tree.getroot()
        device_info_dict = {}

        for sheet_node in root:
            sheet_node_tag = sheet_node.tag
            if type(sheet_node_tag) is not str:
                continue
            sheet_name_list.append(sheet_node_tag)
            for dev_node in sheet_node:
                dev_tag = dev_node.tag
                if not isinstance(dev_tag, str):
                    continue
                tag_list = []
                text_list = []
                for sub_node in dev_node:
                    sub_node_tag = sub_node.tag
                    if type(sub_node_tag) is not str:
                        continue
                    tag_list.append(sub_node_tag)
                    value = sub_node.text
                    if value is None:
                        value = ''
                    text_list.append(value)
                if not tag_list:
                    continue
                dev_dict = dict(zip(tag_list, text_list))
                device_info_dict[dev_tag] = dev_dict
        data_list.append(device_info_dict)
    excel_data_dict = dict(zip(sheet_name_list, data_list))

    # 读取xml文件中引用config.ini的数据
    config_ini_data = param_get_config_ini_data()
    if config_ini_data == 'unknown':
        config_ini_data = config_get_all_data_from_ini_file()

    if config_ini_data != 'unknown':
        for env_name in excel_data_dict:  # 遍历每个sheet
            for dev_id in excel_data_dict[env_name]:
                dev_info = excel_data_dict[env_name][dev_id]
                for sub_tag in dev_info:  # 遍历sheet中的每一行
                    if 'config--' in dev_info[sub_tag] and ':' in dev_info[sub_tag]:
                        if '[' in dev_info[sub_tag] and ']' in dev_info[sub_tag]:
                            # 如果是字符串部分需要引用config.ini中的属性值，则需要用[]号包起来
                            info_attribute = str_get_content_between_two_characters(dev_info[sub_tag], '[', ']')
                            dev_info[sub_tag] = dev_info[sub_tag].replace(
                                '[%s]' % info_attribute, '%s' % info_attribute)
                        else:
                            info_attribute = dev_info[sub_tag]
                        config_section = info_attribute.split('config--')[-1].split(':')[0]
                        config_key = info_attribute.split('config--')[-1].split(':')[1]
                        try:
                            info_attribute_data = config_ini_data[config_section][config_key]
                            dev_info[sub_tag] = dev_info[sub_tag].replace(info_attribute, info_attribute_data)
                        except:
                            aklog_error('%s 表格中的 <%s>%s<%s>引用config或cloud_info出错' % (
                                env_name, sub_tag, dev_info[sub_tag], sub_tag))
                            time.sleep(0.1)
                            raise

    aklog_printf(excel_data_dict)
    return excel_data_dict


def xml_read_all_excel_data(dir_path):
    """
    将目录下xml文件遍历读取，返回的数据跟之前的excel表格获取的一样
    :param dir_path: xml文件目录
    :return: dict类型
    """
    aklog_printf('xml_read_all_excel_data, dir_path: %s' % dir_path)
    data_list = []
    sheet_name_list = []
    for file in os.listdir(dir_path):
        if os.path.splitext(file)[1] != '.xml':
            continue
        file_path = os.path.join(dir_path, file)
        tree = ET.parse(file_path)
        root = tree.getroot()

        for sheet_node in root:
            sheet_list = []
            sheet_node_tag = sheet_node.tag
            if type(sheet_node_tag) is not str:
                continue
            sheet_name_list.append(sheet_node_tag)
            for line_node in sheet_node:
                if not isinstance(line_node.tag, str):
                    continue
                elif not len(line_node):
                    # 新的xml文件格式，用属性键值对来写数据
                    line_dict = dict(line_node.attrib)
                    if not line_dict:
                        continue
                else:
                    tag_list = []
                    text_list = []
                    for sub_node in line_node:
                        sub_node_tag = sub_node.tag
                        if type(sub_node_tag) is not str:
                            continue
                        tag_list.append(sub_node_tag)
                        value = sub_node.text
                        if value is None:
                            value = ''
                        text_list.append(value)
                    if not tag_list:
                        continue
                    line_dict = dict(zip(tag_list, text_list))

                    # 新的xml文件格式，用属性键值对来写数据，device_info的line属性里增加device_name，更新字典数据
                    line_attrib_dict = dict(line_node.attrib)
                    if line_dict:
                        line_dict.update(line_attrib_dict)

                sheet_list.append(line_dict)
            # aklog_printf(sheet_list)
            data_list.append(sheet_list)

    excel_data_dict = dict(zip(sheet_name_list, data_list))

    # 读取xml文件中引用config.ini的数据
    config_ini_data = param_get_config_ini_data()
    if config_ini_data != 'unknown':
        for i in excel_data_dict:  # 遍历每个sheet
            for j in excel_data_dict[i]:  # 遍历sheet中的每一行
                for k in j:
                    if 'config--' in j[k] and ':' in j[k]:
                        if '[' in j[k] and ']' in j[k]:  # 如果是字符串部分需要引用config.ini中的属性值，则需要用[]号包起来
                            info_attribute = str_get_content_between_two_characters(j[k], '[', ']')
                            j[k] = j[k].replace('[%s]' % info_attribute, '%s' % info_attribute)
                        else:
                            info_attribute = j[k]
                        config_section = info_attribute.split('config--')[-1].split(':')[0]
                        config_key = info_attribute.split('config--')[-1].split(':')[1]
                        info_attribute_data = config_ini_data[config_section][config_key]
                        j[k] = j[k].replace(info_attribute, info_attribute_data)

    # 读取xml文件中引用device_info中的数据，如果有指定环境名称，并且device_info有保存对应环境的信息，则采用对应的device_info
    autotest_env_name = config_ini_data['environment']['autotest_env_name']
    if not autotest_env_name or autotest_env_name == 'None':
        device_info_name = 'device_info'
    else:
        if autotest_env_name.startswith('device_info'):
            device_info_name = autotest_env_name
        else:
            device_info_name = 'device_info__%s' % autotest_env_name

        if device_info_name not in excel_data_dict:
            device_info_name = 'device_info'
    aklog_info('device_info_name: %s' % device_info_name)

    # 如果有指定device_info，那么则将device_info相关数据替换成保存的对应环境的数据
    if device_info_name != 'device_info':
        excel_data_dict['device_info'] = excel_data_dict[device_info_name]

    # device_info中的mac大小写都添加
    if 'device_info' in excel_data_dict:
        for info in excel_data_dict['device_info']:
            if 'MAC' in info:
                info['mac'] = info['MAC']
            elif 'mac' in info:
                info['MAC'] = info['mac']

    # 读取xml文件中引用device_info中的数据
    if 'device_info' in excel_data_dict:
        for i in excel_data_dict:  # 遍历每个sheet
            for j in excel_data_dict[i]:  # 遍历sheet中的每一行
                for k in j:
                    if '__' in j[k]:
                        if '[' in j[k] and ']' in j[k]:  # 如果是字符串部分需要引用device_info中的属性值，则需要用[]号包起来
                            info_attribute = str_get_content_between_two_characters(j[k], '[', ']')
                            j[k] = j[k].replace('[%s]' % info_attribute, '%s' % info_attribute)
                        else:
                            info_attribute = j[k]
                        attribute = info_attribute.split('__')[-1]
                        device_name = info_attribute.split('__')[0]
                        for info in excel_data_dict['device_info']:
                            if info['device_name'] == device_name:
                                j[k] = j[k].replace(info_attribute, info[attribute])

    # 将json格式的字符串转换成字典
    for i in excel_data_dict:  # 遍历每个sheet
        for j in excel_data_dict[i]:  # 遍历sheet中的每一行
            for k in j:
                j[k] = json_loads_2_dict(j[k])
    # aklog_printf('test data: %r' % excel_data_dict)
    return excel_data_dict


def xml_read_all_test_data(series_path, model_name, oem_name, specified_file=None):
    """
    将目录下xml文件遍历读取，返回的数据跟之前的excel表格获取的一样
    :param series_path: 系列产品通用xml文件目录
    :param model_name: 机型通用xml文件目录
    :param oem_name: 机型OEM的xml文件目录
    :param specified_file:
    :return: dict类型
    """
    aklog_printf()
    data_list = []
    sheet_name_list = []
    file_dict = {}

    series_normal_path = series_path + '\\NORMAL'
    model_normal_path = series_path + '\\' + model_name + '\\NORMAL'
    model_oem_path = series_path + '\\' + model_name + '\\' + oem_name
    # 遍历系列产品目录下通用和机型通用及机型OEM目录的XML文件，机型通用及机型OEM目录下有相同的文件，则会采用机型通用及机型OEM目录下的文件
    if os.path.exists(series_normal_path):
        for file in os.listdir(series_normal_path):
            if os.path.splitext(file)[1] != '.xml':
                continue
            file_path = os.path.join(series_normal_path, file)
            file_dict[file] = file_path

    if os.path.exists(model_normal_path):
        for file in os.listdir(model_normal_path):
            if os.path.splitext(file)[1] != '.xml':
                continue
            file_path = os.path.join(model_normal_path, file)
            file_dict[file] = file_path

    if os.path.exists(model_oem_path):
        for file in os.listdir(model_oem_path):
            if os.path.splitext(file)[1] != '.xml':
                continue
            file_path = os.path.join(model_oem_path, file)
            file_dict[file] = file_path

    if specified_file:  # 如果指定文件，则是读取该文件
        if specified_file in file_dict:
            return xml_read_sheet_data(file_dict[specified_file])
        else:
            aklog_printf('%s is not exists' % specified_file)
            return None

    aklog_debug('device_info.xml: {}'.format(file_dict.get('device_info.xml')))

    file_sheet_data = {}
    for file in file_dict:
        file_path = file_dict[file]
        tree = ET.parse(file_path)
        root = tree.getroot()
        file_sheet_data[file] = []
        for sheet_node in root:
            sheet_list = []
            sheet_node_tag = sheet_node.tag
            if type(sheet_node_tag) is not str:
                continue
            if sheet_node_tag in sheet_name_list:
                for x in file_sheet_data:
                    if sheet_node_tag in file_sheet_data[x]:
                        pre_file = x
                        aklog_warn('testdata，%s文件中%s数据跟%s文件重复 ，将不读取该文件的数据，请检查'
                                   % (file, sheet_node_tag, pre_file))
                        break
                continue
            file_sheet_data[file].append(sheet_node_tag)
            sheet_name_list.append(sheet_node_tag)
            for line_node in sheet_node:
                if not isinstance(line_node.tag, str):
                    continue
                elif not len(line_node):
                    # 新的xml文件格式，用属性键值对来写数据
                    line_dict = dict(line_node.attrib)
                    if not line_dict:
                        continue
                else:
                    tag_list = []
                    text_list = []
                    for sub_node in line_node:
                        sub_node_tag = sub_node.tag
                        if type(sub_node_tag) is not str:
                            continue
                        tag_list.append(sub_node_tag)
                        value = sub_node.text
                        if value is None:
                            value = ''
                        text_list.append(value)
                    if not tag_list:
                        continue
                    line_dict = dict(zip(tag_list, text_list))

                    # 新的xml文件格式，用属性键值对来写数据，device_info的line属性里增加device_name，更新字典数据
                    line_attrib_dict = dict(line_node.attrib)
                    if line_dict:
                        line_dict.update(line_attrib_dict)

                # device_info引用config目录的信息
                if 'device_identify' in line_dict:
                    dev_id = line_dict['device_identify']
                    line_dict.pop('device_identify')
                    new_line_dict = {}
                    all_config_device_info = param_get_all_config_device_info()
                    if not all_config_device_info:
                        all_config_device_info = xml_read_all_config_device_info()
                        param_put_all_config_device_info(all_config_device_info)
                    if all_config_device_info and sheet_node_tag in all_config_device_info:
                        config_device_info = all_config_device_info[sheet_node_tag]
                        if dev_id in config_device_info:  # 2025.6.16 新机型修改device_info__linuxindoor_1116, 主节点没有同步?失败.
                            new_line_dict.update(config_device_info[dev_id])
                        new_line_dict.update(line_dict)
                    if not new_line_dict:
                        new_line_dict = line_dict
                else:
                    new_line_dict = line_dict

                sheet_list.append(new_line_dict)
            # aklog_printf(sheet_list)
            data_list.append(sheet_list)
    excel_data_dict = dict(zip(sheet_name_list, data_list))

    # 读取xml文件中引用config.ini的数据
    config_ini_data = param_get_config_ini_data()
    if config_ini_data != 'unknown':
        for i in excel_data_dict:  # 遍历每个sheet
            for j in excel_data_dict[i]:  # 遍历sheet中的每一行
                for k in j:
                    if 'config--' in j[k] and ':' in j[k]:
                        if '[' in j[k] and ']' in j[k]:  # 如果是字符串部分需要引用config.ini中的属性值，则需要用[]号包起来
                            info_attribute = str_get_content_between_two_characters(j[k], '[', ']')
                            j[k] = j[k].replace('[%s]' % info_attribute, '%s' % info_attribute)
                        else:
                            info_attribute = j[k]
                        config_section = info_attribute.split('config--')[-1].split(':')[0]
                        config_key = info_attribute.split('config--')[-1].split(':')[1]
                        try:
                            info_attribute_data = config_ini_data[config_section][config_key]
                            j[k] = j[k].replace(info_attribute, info_attribute_data)
                        except:
                            aklog_error('%s 表格中的 <%s>%s<%s>引用config或cloud_info出错' % (i, k, j[k], k))
                            time.sleep(0.1)
                            raise

    # 读取xml文件中引用device_info中的数据，如果有指定环境名称，并且device_info有保存对应环境的信息，则采用对应的device_info
    autotest_env_name = config_ini_data['environment']['autotest_env_name']
    if not autotest_env_name or autotest_env_name == 'None':
        device_info_name = 'device_info'
    else:
        device_info_name = 'device_info__%s' % autotest_env_name
        if device_info_name not in excel_data_dict:
            device_info_name = 'device_info'
    aklog_info('device_info_name: %s' % device_info_name)

    # 如果有指定device_info，那么将device_info相关数据替换成保存的对应环境的数据
    if device_info_name != 'device_info':
        excel_data_dict['device_info'] = excel_data_dict[device_info_name]

    # device_info中的mac大小写都添加
    if 'device_info' in excel_data_dict:
        for info in excel_data_dict['device_info']:
            if 'MAC' in info:
                info['mac'] = info['MAC']
            elif 'mac' in info:
                info['MAC'] = info['mac']

    if 'device_info' in excel_data_dict:
        for i in excel_data_dict:  # 遍历每个sheet
            for j in excel_data_dict[i]:  # 遍历sheet中的每一行
                for k in j:
                    if '__' in j[k]:
                        if '[' in j[k] and ']' in j[k]:  # 如果是字符串部分需要引用device_info中的属性值，则需要用[]号包起来
                            info_attribute = str_get_content_between_two_characters(j[k], '[', ']')
                            j[k] = j[k].replace('[%s]' % info_attribute, info_attribute)
                        else:
                            info_attribute = j[k]
                        attribute = info_attribute.split('__')[-1]
                        device_name = info_attribute.split('__')[0]
                        replace_flag = False
                        for info in excel_data_dict['device_info']:
                            if info['device_name'] == device_name:
                                try:
                                    # 主要是mac, MAC大小写的不统一
                                    if attribute not in info.keys():
                                        for newkey in info.keys():
                                            if newkey.lower() == attribute.lower():
                                                attribute = newkey
                                                break
                                    j[k] = j[k].replace(info_attribute, info[attribute])
                                    replace_flag = True
                                    break
                                except:
                                    aklog_error('%s 表格中的 <%s>%s</%s> 引用device_info出错' % (i, k, j[k], k))
                                    time.sleep(0.1)
                                    raise
                        if not replace_flag:
                            aklog_warn('%s 表格中的 <%s>%s</%s> 引用device_info, 但缺少 %s 设备' %
                                       (i, k, j[k], k, device_name))

    # 将json格式的字符串转换成字典
    for i in excel_data_dict:  # 遍历每个sheet
        for j in excel_data_dict[i]:  # 遍历sheet中的每一行
            for k in j:
                j[k] = json_loads_2_dict(j[k])

    # aklog_printf('test data: %r' % excel_data_dict)
    return excel_data_dict


def xml_read_sheet_data(file_path):
    """
    读取单个文件，返回dict类型
    :param file_path: xml文件路径
    :return:
    """
    aklog_printf()
    if not os.path.exists(file_path):
        aklog_printf('%s is not exists' % file_path)
        return None
    tree = ET.parse(file_path)
    root = tree.getroot()
    sheet_name_list = []
    data_list = []
    for sheet_node in root:
        sheet_list = []
        sheet_node_tag = sheet_node.tag
        if type(sheet_node_tag) is not str:
            continue
        sheet_name_list.append(sheet_node_tag)
        for line_node in sheet_node:
            if not isinstance(line_node.tag, str):
                continue
            elif not len(line_node):
                # 新的xml文件格式，用属性键值对来写数据
                line_dict = dict(line_node.attrib)
                if not line_dict:
                    continue
            else:
                tag_list = []
                text_list = []
                for sub_node in line_node:
                    sub_node_tag = sub_node.tag
                    if type(sub_node_tag) is not str:
                        continue
                    tag_list.append(sub_node_tag)
                    value = sub_node.text
                    if value is None:
                        value = ''
                    text_list.append(value)
                if not tag_list:
                    continue
                line_dict = dict(zip(tag_list, text_list))

                # 新的xml文件格式，用属性键值对来写数据，device_info的line属性里增加device_name，更新字典数据
                line_attrib_dict = dict(line_node.attrib)
                if line_dict:
                    line_dict.update(line_attrib_dict)

            sheet_list.append(line_dict)
        data_list.append(sheet_list)
    excel_data_dict = dict(zip(sheet_name_list, data_list))
    # aklog_printf(excel_data_dict)
    return excel_data_dict


def get_device_info_attribute_value(device_info_attribute):
    """
    根据属性名称获取device_info中对应属性的值
    :param device_info_attribute: device_info中的device_name加上属性字段名称，比如slave1_android_indoor__ip
    :return:
    """
    if '__' in device_info_attribute:
        attribute = device_info_attribute.split('__')[-1]
        device_name = device_info_attribute.split('__' + attribute)[0]
        for line in param_get_excel_data()['device_info']:
            if line['device_name'] == device_name:
                return line[attribute]
        return device_info_attribute
    else:
        return device_info_attribute


def get_device_info_by_device_name(device_name):
    """根据device_name获取device_info整行信息"""
    for line in param_get_excel_data()['device_info']:
        if line['device_name'] == device_name:
            # 每个机型系列维护mac的大小写还不一样..
            if 'MAC' in line:
                line['mac'] = line['MAC']
            if 'mac' in line:
                line['MAC'] = line['mac']
            return line
    aklog_warn('device_info.xml 缺少 %s 设备信息，请确认是否需要补充，如果不需要可忽略' % device_name)
    return None


def get_line_by_line_flag(sheet_data, line_flag, flag_value):
    """根据行标识获取整行信息"""
    for line in sheet_data:
        if line[line_flag] == flag_value:
            return line
    return None


def xml_parse_module_list(file_path):
    """解析测试用例模块"""
    aklog_printf('xml_parse_module_list, file: %s' % file_path)
    if not os.path.exists(file_path):
        aklog_printf('%s is not exists' % file_path)
        return None
    tree = ET.parse(file_path)
    root = tree.getroot()
    sheet_name_list = []
    data_list = []
    for sheet_node in root:
        sheet_name_list.append(sheet_node.tag)
        tag_list = []
        text_list = []
        for module_node in sheet_node:
            for sub_node in module_node:
                tag_list.append(sub_node.tag)
                value = sub_node.text
                if value is None:
                    value = ''
                else:
                    value = value.strip()
                Priority = sub_node.get('Priority')
                KeyFeature = sub_node.get('KeyFeature')
                StressTest = sub_node.get('StressTest')
                UpgradeTest = sub_node.get('UpgradeTest')
                ID = sub_node.get('ID')
                Init = sub_node.get('Init')
                module = {'value': value,
                          'attribute': {'Priority': Priority,
                                        'KeyFeature': KeyFeature,
                                        'StressTest': StressTest,
                                        'UpgradeTest': UpgradeTest,
                                        'ID': ID
                                        }
                          }
                if Init:
                    module['attribute']['Init'] = Init
                text_list.append(module)
        sheet_dict = dict(zip(tag_list, text_list))
        data_list.append(sheet_dict)
    excel_data_dict = dict(zip(sheet_name_list, data_list))
    # aklog_printf(excel_data_dict)
    return excel_data_dict


def xml_parse_suite_list(file_path):
    """解析测试套件"""
    aklog_printf('xml_parse_suite_list, file: %s' % file_path)
    if not os.path.exists(file_path):
        aklog_printf('%s is not exists' % file_path)
        return None
    tree = ET.parse(file_path)
    root = tree.getroot()
    sheet_name_list = []
    data_list = []
    for sheet_node in root:
        sheet_name_list.append(sheet_node.tag)
        suite_name_list = []
        suite_list = []
        for suite_name_node in sheet_node:
            suite_name_list.append(suite_name_node.tag)
            module_name_list = []
            module_list = []
            for sub_node in suite_name_node:
                # 遍历获取一个套件下的用例
                module_name = sub_node.tag
                if not isinstance(module_name, str):
                    continue
                value = sub_node.text
                if value is None:
                    value = '0'
                else:
                    value = json_loads_2_dict(value)

                if value == '0':
                    continue
                elif module_name.startswith('suite__'):
                    # 如果是suite开头，表示包含其他套件
                    module = {'Enable': 1}
                else:
                    CasePriority = sub_node.get('CasePriority')
                    if not CasePriority:
                        CasePriority = 'P2'
                    module = {'CasePriority': CasePriority}
                    # 如果有存在ForcedOrder强制顺序属性，则该用例要优先按照指定顺序执行
                    ForcedOrder = sub_node.get('ForcedOrder')
                    if ForcedOrder:
                        module['ForcedOrder'] = int(ForcedOrder)

                    if str(value).isdigit():
                        module['TestCounts'] = int(value)
                    elif re.compile(r'[dhms]', re.IGNORECASE).search(str(value)):
                        module['TestDuration'] = value  # 如果带有d h m s，则表示测试时长
                module_list.append(module)
                module_name_list.append(module_name)
            # 将两个列表组合成字典，第一个列表的元素作为字典的key，第二个作为value
            suite_dict = dict(zip(module_name_list, module_list))
            suite_list.append(suite_dict)
        data_dict = dict(zip(suite_name_list, suite_list))

        # 遍历所有套件，如果套件嵌套了其他套件，则将嵌套的套件引用过来
        for x in data_dict.keys():
            module_or_suite_list = list(data_dict[x].keys())
            for y in module_or_suite_list:
                if y.startswith('suite__'):
                    suite_name = y.replace('suite__', '')
                    if suite_name == x:
                        continue
                    data_dict[x].pop(y)
                    data_dict[x].update(data_dict[suite_name])

        data_list.append(data_dict)
    excel_data_dict = dict(zip(sheet_name_list, data_list))  # 包含注释部分
    aklog_printf('suite list info: %r' % excel_data_dict)
    return excel_data_dict


def xml_parse_exclude_case_list(file_path):
    """解析需要排除掉不进行测试的用例列表"""
    aklog_printf('xml_parse_exclude_case_list, file: %s' % file_path)
    if not os.path.exists(file_path):
        aklog_printf('%s is not exists' % file_path)
        return None
    tree = ET.parse(file_path)
    root = tree.getroot()
    sheet_name_list = []
    data_list = []
    for sheet_node in root:
        sheet_name_list.append(sheet_node.tag)
        module_name_list = []
        module_list = []
        for module_name_node in sheet_node:
            module_name = module_name_node.tag
            if not isinstance(module_name, str):  # 排除掉注释
                continue
            module_name_list.append(module_name)
            case_name_list = []
            for sub_node in module_name_node:
                # 遍历获取一个模块下的用例
                case_name = sub_node.tag
                case_name_list.append(case_name)
            # 将两个列表组合成字典，第一个列表的元素作为字典的key，第二个作为value
            module_list.append(case_name_list)
        data_dict = dict(zip(module_name_list, module_list))
        data_list.append(data_dict)
    excel_data_dict = dict(zip(sheet_name_list, data_list))
    aklog_printf('exclude case list info: %r' % excel_data_dict)
    return excel_data_dict


def xml_parse_last_checked_case_list(file_path):
    """解析上次勾选的用例列表"""
    aklog_printf('xml_parse_last_checked_case_list, file: %s' % file_path)
    if not os.path.exists(file_path):
        aklog_printf('%s is not exists' % file_path)
        return None
    tree = ET.parse(file_path)
    root = tree.getroot()
    sheet_name_list = []
    data_list = []
    for sheet_node in root:
        sheet_name_list.append(sheet_node.tag)
        module_name_list = []
        module_list = []
        for module_name_node in sheet_node:
            module_name = module_name_node.tag
            if not isinstance(module_name, str):  # 排除掉注释
                continue
            module_name_list.append(module_name)
            case_name_list = []
            for sub_node in module_name_node:
                # 遍历获取一个模块下的用例
                case_name = sub_node.tag
                case_name_list.append(case_name)
            # 将两个列表组合成字典，第一个列表的元素作为字典的key，第二个作为value
            module_list.append(case_name_list)
        data_dict = dict(zip(module_name_list, module_list))
        data_list.append(data_dict)
    excel_data_dict = dict(zip(sheet_name_list, data_list))
    aklog_printf('last checked case list info: %r' % excel_data_dict['LastCheckedCase'])
    return excel_data_dict['LastCheckedCase']


def xml_write_last_checked_case_list(file_path, module_dict):
    """将勾选的用例列表写入到xml文件"""
    aklog_printf('xml_write_last_checked_case_list, file: %s' % file_path)
    root = ET.Element('root')  # 创建节点
    tree = ET.ElementTree(root)  # 创建文档

    sheet_element = ET.Element('LastCheckedCase')
    root.append(sheet_element)

    for module in module_dict:
        module_element = ET.Element(str(module))
        for case in module_dict[module]:
            sub_element = ET.Element(str(case))
            module_element.append(sub_element)
        sheet_element.append(module_element)

    __xml_indent(root)  # 增加换行符
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_parse_element_info(file_path):
    """
    解析元素信息文件
    """
    if not os.path.exists(file_path):
        aklog_printf('%s is not exists' % file_path)
        return None
    tree = ET.parse(file_path)
    root = tree.getroot()
    sheet_dict = {}
    for sheet_node in root:
        for page_node in sheet_node:
            tag_list = []
            text_list = []
            for sub_node in page_node:
                tag_list.append(sub_node.tag)
                value = sub_node.text
                if value is None:
                    value = ''
                else:
                    value = json_loads_2_dict(value)
                text_list.append(value)
            page_dict = dict(zip(tag_list, text_list))
            sheet_dict.update(page_dict)
    # aklog_printf(sheet_dict)
    return sheet_dict


def xml_parse_model_version_info():
    """解析机型分支版本信息，用于根据版本号判断测试机型应该用哪个分支"""
    file_dir = g_config_path + '\\libconfig_xml\\model_version_info'
    file_paths = []
    for root, dirs, files in os.walk(file_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.xml':
                file_path = os.path.join(root, file)
                file_paths.append(file_path)

    model_version_info = dict()
    for file_path in file_paths:
        tree = ET.parse(file_path)
        root = tree.getroot()
        model_version_info_node = root[0]
        for model_node in model_version_info_node:
            model_name = model_node.tag
            if not isinstance(model_name, str):
                continue
            if model_name in model_version_info:
                aklog_warn('model_version_info 存在相同的型号: %s' % model_name)
                continue
            model_id = model_node.get('model_id')
            default_branch = model_node.get('default_branch')
            version_branch_info = []
            for line_node in model_node:
                tag_list = []
                text_list = []
                for sub_node in line_node:
                    sub_node_tag = sub_node.tag
                    if not isinstance(sub_node_tag, str):
                        continue
                    tag_list.append(sub_node_tag)
                    value = sub_node.text
                    if value is None:
                        value = ''
                    text_list.append(value)
                if not tag_list:
                    continue
                version_info = dict(zip(tag_list, text_list))
                version_branch_info.append(version_info)

            model_version_info[model_name] = {'model_id': model_id,
                                              'default_branch': default_branch,
                                              'version_branch_info': version_branch_info}

    aklog_printf(model_version_info)
    return model_version_info


def xml_parse_time_zone():
    """解析time zone文件"""
    file_path = g_config_path + '\\TimeZone.xml'
    tree = ET.parse(file_path)
    root = tree.getroot()
    sheet_dict = {}
    for node in root:
        TimeZone = node.get('TimeZone')
        Name = node.get('Name')
        Type = node.get('Type')
        Start = node.get('Start')
        End = node.get('End')
        Offset = node.get('Offset')
        if TimeZone and Name:
            key = '%s %s' % (TimeZone, Name)
            sheet_dict[key] = {'Type': Type,
                               'Start': Start,
                               'End': End,
                               'Offset': Offset}
    # aklog_printf(sheet_dict)
    return sheet_dict


def xml_parse_contact_file(file_path, *contact_attrs):
    """
    解析联系人文件，返回联系人列表
    :param file_path: 联系人文件路径
    :param contact_attrs: 联系人属性，比如：'DisplayName', 'Number1'
    :return:
    """
    aklog_printf('xml_parse_contact_file: %s' % file_path)
    tree = ET.parse(file_path)
    root = tree.getroot()
    contact_list = []
    for group in root:
        for contact in group:
            contact_info = dict()
            if not contact_attrs:
                contact_attrs = ('DisplayName', 'Number1')
            for attr in contact_attrs:
                contact_info[attr] = contact.get(attr)
            contact_list.append(contact_info)
    # aklog_printf(contact_list)
    return contact_list


def xml_parse_codec_payload_type():
    """解析codec payload type文件"""
    file_path = g_config_path + '\\CodecPayloadType.xml'
    tree = ET.parse(file_path)
    root = tree.getroot()
    sheet_dict = {}
    for node in root:
        codec = node.tag
        payload_type = node.text
        sheet_dict[codec] = payload_type
    # aklog_printf(sheet_dict)
    return sheet_dict


def xml_parse_translations(file_path):
    """解析翻译文件"""
    tree = ET.parse(file_path)
    root = tree.getroot()
    sheet_dict = {}
    for node in root:
        name = node.get('name')
        trans = node.text
        sheet_dict[name] = trans
    # print(sheet_dict)
    return sheet_dict


def xml_generate_dial_plan_file(counts, dst_path, file_name):
    """生成DialPlan XML文件"""
    root = ET.Element('Dial')  # 创建根节点
    tree = ET.ElementTree(root)  # 创建文档

    DialReplace_element = ET.Element('DialReplace')
    root.append(DialReplace_element)

    for i in range(1, counts + 1):
        Data_element = ET.Element('Data')
        Data_element.set('ID', str(i))
        Data_element.set('Prefix', str(1000 + i))
        Data_element.set('Replace', str(3000 + i))
        Data_element.set('Replace2', '')
        Data_element.set('Replace3', '')
        Data_element.set('Replace4', '')
        Data_element.set('Line', '0')
        DialReplace_element.append(Data_element)

    __xml_indent(root)  # 增加换行符
    if not os.path.exists(dst_path):
        os.makedirs(dst_path)
    file_path = os.path.join(dst_path, file_name)
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def xml_modify_device_info_add_device_name_to_line(file):
    """
    修改device_info.xml文件，在line这个节点添加device_name属性，
    并将line下一级的device_name去掉，xml折叠时方便查找对应机型
    """
    aklog_printf()
    tree = ET.parse(file)
    root = tree.getroot()
    for device_info_node in root:
        for line_node in device_info_node:
            attribute = line_node.find('device_name')
            if attribute is not None:
                if not line_node.get('device_name'):
                    device_name = attribute.text
                    line_node.set('device_name', device_name)
                # 将line下一级的device_name去掉
                line_node.remove(attribute)
    __xml_indent(root)  # 增加换行符
    tree.write(file, encoding='utf-8', xml_declaration=True)


def xml_batch_modify_device_info_add_device_name_to_line(path):
    """
    批量修改指定目录下的所有device_info.xml文件，
    在line这个节点添加device_name属性，xml折叠时方便查找对应机型
    """
    file_paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file == 'device_info.xml':
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
    aklog_printf('file_paths: %r' % file_paths)

    for file in file_paths:
        xml_modify_device_info_add_device_name_to_line(file)


if __name__ == '__main__':
    print('测试代码')
    # xml_add_and_modify_all_files_attribute(r'E:\SVN_Python\Develop\AKautotest\testdata',
    #                                        'version_branch.xml', 'version_branch',
    #                                        cloud_branch='cloud_CBB')
    # xml_add_and_modify_all_files_attribute(r'E:\SVN_Python\Develop\AKautotest\testcase\module',
    #                                        'version_branch.xml', 'version_branch',
    #                                        cloud_branch='cloud_CBB')
    app_info_file = r'E:\SVN_Python\Develop\AKautotest\testcase\apps\ScanNetworkAutoTest\device_info.xml'
    xml_modify_specify_line_attribute(
        app_info_file, 'device_info', 'device_name', 'app_127.0.0.1:5555', for_master_name='PS51_168', status='used')
