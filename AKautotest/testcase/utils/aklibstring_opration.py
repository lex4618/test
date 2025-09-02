#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
if root_path not in sys.path:
    sys.path.append(root_path)

from akcommon_define import *
import json
import traceback
import random
import string
import re

import re


def str_get_content_between_two_characters(text: str, start_str: str, end_str: str, find_all=False):
    """
    截取字符串中两个字符中间的部分。

    :param text: 输入的字符串
    :param start_str: 起始字符或字符串
    :param end_str: 结束字符或字符串
    :param find_all: 是否提取所有匹配内容，默认为 False（只提取第一个匹配）
    :return: 提取的内容（字符串或列表），如果没有匹配则返回 None
    """
    if not text or not start_str or not end_str:
        raise ValueError("Input text, start_str, and end_str must not be empty.")

    # 构造正则表达式，确保起始和结束字符被正确转义
    pattern = rf"{re.escape(start_str)}(.*?){re.escape(end_str)}"

    if find_all:
        # 提取所有匹配的内容
        matches = re.findall(pattern, text)
        return matches if matches else None
    else:
        # 提取第一个匹配的内容
        match = re.search(pattern, text)
        return match.group(1) if match else None


def str_insert_separator(text, separator, interval_num):
    """
    字符串每隔几位插入分隔符，比如将MAC地址插入冒号
    :param text:
    :param separator: 分隔符，比如 :
    :param interval_num: 间隔位数
    :return:
    """
    string_list = list(text)
    length = len(string_list)
    new_str = ''
    for i in range(length):
        if i > 0 and (i % interval_num) == 0:
            new_str += separator + string_list[i]
        else:
            new_str += string_list[i]
    return new_str


def get_ip_from_text(text):
    """从字符串中获取IPV4地址"""
    pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    match = re.search(pattern, text)
    if match:
        ip_address = match.group()
        return ip_address
    else:
        return None


def generate_random_hex_str(random_length=32):
    """生成一个指定长度的随机字符串，16进制字符"""
    random_str = ''
    base_str = 'abcdef0123456789'
    length = len(base_str) - 1
    for i in range(random_length):
        random_str += base_str[random.randint(0, length)]
    return random_str


def generate_random_string(length=32, language=None):
    """
    生成指定语言的随机字符串，如果language为None，则生成随机字母数字特殊字符
    移除单引号和双引号，避免作为文本参与xpath，导致xpath失效问题
    :param language: 字符串语言类型，支持 'en'（英文）、'zh'（中文）、'jp'（日文）、'num'（数字）等
    :param length: 随机字符串的长度
    :return: 生成的随机字符串
    """
    if length <= 0:
        raise ValueError("Length must be greater than 0.")

    if language == 'en':
        # 英文字符集（大小写字母）
        charset = string.ascii_letters
    elif language == 'num':
        # 数字字符集
        charset = string.digits
    elif language == 'en_num':
        # 英文+数字字符集
        charset = string.ascii_letters + string.digits
    elif language == 'zh':
        # 中文字符集（常用汉字范围）
        charset = ''.join(chr(i) for i in range(0x4e00, 0x9fa5))
    elif language == 'jp':
        # 日文字符集（平假名+片假名）
        charset = ''.join(chr(i) for i in range(0x3040, 0x30ff))
    else:
        charset = string.ascii_letters + string.digits + string.punctuation
        charset = charset.replace("'", "").replace('"', "")  # 移除单引号和双引号
        charset = charset.replace("<", "")  # 移除尖括号，避免HTML报告日志颜色显示错乱

    # 随机选择字符生成字符串
    return ''.join(random.choice(charset) for _ in range(length))


def str_append_or_increment_tail_digit(s):
    """
    给字符串结尾加数字；如果结尾已是数字，则数字+1（1-9循环），保证新字符串与原字符串不同。

    Args:
        s (str): 原始字符串

    Returns:
        str: 修改后的字符串
    """
    if not s:
        return "1"

    # 检查最后字符是否为数字
    last_char = s[-1]
    if last_char.isdigit():
        num = int(last_char)
        # 数字循环递增：1->2->...->9->1
        new_num = 1 if num == 9 else num + 1
        return s[:-1] + str(new_num)
    else:
        return s + "1"


def generate_num_list(start, end, step=1.0):
    start = float(start)
    step = float(step)
    return [int(x) if x.is_integer() else x for x in [i * step for i in range(int(start / step), int(end / step) + 1)]]


def is_json(text):
    """判断字符串是否为json格式"""
    try:
        json.loads(text)
        return True
    except:
        return False


def json_loads_2_dict(json_string):
    """将json格式的字符串转换成python数据类型，list or dict"""
    out = json_string
    try:
        json_data = json.loads(json_string, strict=False)
        if isinstance(json_data, (dict, list)):
            out = json_data
    finally:
        return out


def dict_dumps_2_json(value):
    """将字典转换成json格式的字符串"""
    if type(value) is dict:
        json_string = json.dumps(value)
        return json_string
    else:
        return value


def parse_msg_to_dict(msg):
    """'
    MSG格式如下：
    <Msg>\r\n\t<Type>ReportArming</Type>\r\n\t<Protocal>2.0</Protocal>\r\n\t<Params>\r\n\t\t<FromName></FromName>\r\n\t\t<ToName></ToName>\r\n\t\t<From></From>\r\n\t\t<To></To>\r\n\t\t<Mode>1</Mode>\r\n\t\t<Sync>1</Sync>\r\n\t\t<Action>3</Action>\r\n\t</Params>\r\n</Msg>\r\n'
    """
    aklog_printf('parse_msg_to_dict')
    msg = msg.replace('"', '##').replace('{', '**').replace('}', '**')
    logs = msg.split('\n')
    # print(logs)
    results = """"""
    i = 0
    while i < len(logs):
        line = logs[i]
        # print('line: %r' % line.strip())
        if not line or not line.strip():
            i += 1
            continue
        key = str_get_content_between_two_characters(line, '<', '>')
        value = str_get_content_between_two_characters(line, '>', '<')
        count = line.count('<', 0, len(line))
        count1 = line.count('>', 0, len(line))
        if value or (count == 2 and count1 == 2):
            logs[i] = '"%s": "%s", ' % (key, value)
        elif key == 'Msg':
            logs[i] = '{"%s": {' % key
        elif i + 1 < len(logs) and logs[i + 1].strip() and logs[i + 1].strip()[0] == '<' \
                and logs[i].strip()[0:2] != '</':
            # 如果下一行的开头是<，说明是下一行的内容为该行key的value
            logs[i] = '"%s": {' % key
        elif i + 1 < len(logs) and logs[i + 1].strip() and logs[i + 1].strip()[0] != '<':
            # 如果下一行的开头不是<，说明下一行仍然是该行key的value（value多行）
            value = line[(line.index('>') + 1):]
            multilines = 1
            for j in range(i + 1, len(logs)):
                multilines += 1
                if logs[j].endswith('>'):
                    value += logs[j][:(logs[j].index('<') + 1)]
                    break
                else:
                    value += logs[j]
            logs[i] = '"%s": "%s", ' % (key, value)
            i += multilines - 1
        elif line.strip()[0:2] == '</':
            # 如果开头是</，说明是该字典的结尾
            logs[i] = '}'
        i += 1

    for line in logs:
        results += line
    count1 = results.count('{', 0, len(results))
    count2 = results.count('}', 0, len(results))
    for j in range(count1 - count2):
        results += '}'
    results = results.replace(', }', '}')
    # print(results)
    result_dict = json_loads_2_dict(results)
    aklog_printf('msg dict: %r' % result_dict)
    return result_dict


def increase_version(version: str) -> str:
    """
    将版本号最后一位+1

    Args:
        version (str): 版本号字符串，如'20.1.2.3'

    Returns:
        str: 新的版本号字符串
    """
    aklog_debug()
    parts = version.strip().split('.')
    if not parts or not parts[-1].isdigit():
        aklog_error(f"版本号格式错误: {version}")
        raise ValueError("版本号格式错误")
    parts[-1] = str(int(parts[-1]) + 1)  # 最后一位+1
    return '.'.join(parts)


if __name__ == "__main__":
    print('test')
    log = "[2025-02-21 18:37:40.222] U-Boot SPL 2013.07 (Feb 20 2025 - 21:01:19)"
    print(str_get_content_between_two_characters(log, '[', ']'))
