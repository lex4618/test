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
from configobj import ConfigObj

'''
# import configparser
class iniConfigParser(configparser.RawConfigParser):
    def optionxform(self, optionstr):  # 重写方法，避免读写ini文件时key都变成小写
        return optionstr


class ReadConfig:
    
    def __init__(self, config_path):
        self.__config_path = config_path
        self.__config = iniConfigParser()
        self.__config.read(self.__config_path, encoding='utf-8')
    
    def get_value(self, section, option):
        value = self.__config.get(section, option)
        if value == 'True':
            value = True
        elif value == 'False':
            value = False
        elif value == 'None':
            value = None
        return value
    
    def get_dict(self, section):
        Dict = dict(self.__config.items(section))
        for key in Dict:
            if Dict[key] == 'True':
                Dict[key] = True
            elif Dict[key] == 'False':
                Dict[key] = False
            elif Dict[key] == 'None':
                Dict[key] = None
        return Dict

    def get_sections(self):
        sections = self.__config.sections()
        return sections

    def get_config_data(self):
        sections = self.__config.sections()
        config_data = {}
        for section in sections:
            config_data[section] = self.get_dict(section)
        return config_data

    def modify_config(self, section, option, value):
        """需要配合write_config方法才能修改写入ini文件"""
        self.__config.set(section, option, value)

    def write_config(self):
        """写入到ini文件，有新增追加在文件末尾"""
        self.__config.write(open(self.__config_path, "r+", encoding="utf-8"))

    def save_config_as(self, file_path):
        """将config另存为其他文件"""
        self.__config.write(open(file_path, "w", encoding="utf-8"))


if __name__ == '__main__':
    print('测试代码')
    path = os.path.join(g_config_path, g_config_ini_file)
    config = ReadConfig(path)
    # server_ip = config.get_value('config', 'send_email_enable')
    # print(server_ip)
    # print(type(server_ip))
    # dict1 = config.get_dict('config')
    # print(dict1)
    all_data = config.get_config_data()
    print(all_data)
'''


class ReadConfig:

    def __init__(self, config_path):
        self.__config_path = config_path

        try:
            self.__config = ConfigObj(self.__config_path, write_empty_values=True, encoding='GBK')
        except:
            self.__config = ConfigObj(self.__config_path, encoding='UTF-8')

    def get_value(self, section, option):
        try:
            value = self.__config.get(section).get(option)
            if value == 'True':
                value = True
            elif value == 'False':
                value = False
            elif value == 'None':
                value = None
            return value
        except:
            aklog_printf('%s %s is not exist' % (section, option))
            return None

    def get_dict(self, section):
        Dict = self.__config.get(section)
        for key in Dict:
            if Dict[key] == 'True':
                Dict[key] = True
            elif Dict[key] == 'False':
                Dict[key] = False
            elif Dict[key] == 'None':
                Dict[key] = None
        return Dict

    def get_sections(self):
        sections = self.__config.keys()
        return sections

    def get_config_data(self):
        sections = self.__config.keys()
        config_data = {}
        for section in sections:
            config_data[section] = self.get_dict(section)
        return config_data

    def is_exist_config(self, section, option):
        if section in self.__config:
            if option in self.__config[section]:
                return True
            else:
                aklog_printf('%s is not exist' % option)
                return False
        else:
            aklog_printf('%s is not exist' % section)
            return False

    def modify_config(self, section, option, value):
        """需要配合write_config方法才能修改写入ini文件"""
        if section not in self.__config:
            self.__config[section] = {}
        self.__config[section][option] = value
        return self

    def batch_modify_config(self, *items):
        """需要配合write_config方法才能修改写入ini文件"""
        for item in items:
            section, option, value = item
            if section not in self.__config:
                self.__config[section] = {}
            self.__config[section][option] = value
        return self

    def write_config(self):
        """写入到ini文件，有新增追加在文件末尾"""
        self.__config.write()

    def save_config_as(self, file_path):
        """将config另存为其他文件"""
        self.__config.write(file_path)


def batch_trans_web_interface_config(config_file, config_list):
    """
    转换网页接口配置，网页F12获取接口配置项列表，
    然后用该方法转换一下，保存到临时文件，然后再复制到web_interface_info.ini文件里面
    """
    if os.path.exists(config_file):
        os.remove(config_file)
    config_obj = ReadConfig(config_file)
    for item in config_list:
        key = item.split('&')[0]
        config_obj.modify_config('web_config_info', key, item)
    config_obj.write_config()


if __name__ == '__main__':
    config_file = r'D:\Users\Administrator\Desktop\test.ini'
    config_list = []
    batch_trans_web_interface_config(config_file, config_list)
