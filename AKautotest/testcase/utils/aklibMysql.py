# -*- coding: UTF-8 -*-

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

import re
import time
import pymysql
import random
import pandas as pd
from numpy import double
from typing import Optional

__all__ = [
    'AkMysql',
    'SmartHomeTestCaseSql'
]


class AkMysql(object):
    """VersionSql mysql查询接口"""

    def __init__(self, host, user_name, passwd, database_name, table_name=None, port=3306):
        self.__host = host
        self.__port = port
        self.__user = user_name
        self.__passwd = passwd
        self.__database_name = database_name
        self.__table_name = table_name
        self.__db = None
        self.__cursor = None
        self.device_name = database_name

    def __del__(self):
        if self.__db:
            self.__db.close()

    def connect(self):
        try:
            self.__db = pymysql.connect(host=self.__host, port=self.__port, user=self.__user, password=self.__passwd,
                                        database=self.__database_name, charset='utf8')
            self.__cursor = self.__db.cursor()
            self.__cursor.execute("SELECT VERSION()")
            data = self.__cursor.fetchone()
            aklog_debug("Database version : %s " % data)
            return True
        except Exception as e:
            aklog_debug(f"connect to {self.__host} failed: {e}")
            aklog_debug(traceback.format_exc())
            return False

    def switch_table_name(self, table_name):
        self.__table_name = table_name

    def _reConn(self, num=28800, stime=3):
        _number = 0
        _status = True
        while _status and _number <= num:
            try:
                pings = self.__db.ping()
                # aklog_debug ("ping res:%s" % pings);
                _status = False
            except:

                # aklog_debug ('connect');
                if self.connect():  # 重新连接,成功退出
                    _status = False
                    break
                _number += 1
                time.sleep(stime)

    def create_column_text(self, column_name):
        # ALTER TABLE `Control4_test` ADD COLUMN `state` text NOT NULL  COMMENT '1';
        sql = "ALTER TABLE `%s` ADD COLUMN `%s` text NULL;" % (self.__table_name, column_name)
        aklog_debug(sql)
        try:
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
        except:
            aklog_debug("Error: unable to create table %s " % sql)

        return 0

    def create_column_int(self, column_name):
        # ALTER TABLE `Control4_test` ADD COLUMN `state` text NOT NULL  COMMENT '1';
        sql = "ALTER TABLE `%s` ADD COLUMN `%s` int;" % (self.__table_name, column_name)
        aklog_debug(sql)
        try:
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
        except:
            aklog_debug("Error: unable to create table %s " % sql)

        return 0

    def create_column_double(self, column_name):
        # ALTER TABLE `Control4_test` ADD COLUMN `state` text NOT NULL  COMMENT '1';
        sql = "ALTER TABLE `%s` ADD COLUMN `%s` double;" % (self.__table_name, column_name)
        aklog_debug(sql)
        try:
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
        except:
            aklog_debug("Error: unable to create table %s " % sql)

        return 0

    def insert_entry_values(self, l_data):
        '''把数据按列表完整插入到数据库
        '''
        aklog_debug(self.__table_name)
        aklog_debug('insert_entry_col: %s, %s' % (self.__table_name, l_data))
        r = self.table_exists()
        if not r:
            raise Exception("%s 表格不存在")

        # sql = "insert into `%s` VALUES(\'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\') " % (self.__table_name, str(revision), luser, checker, str(date), reason_short, reason, des, status, story_id)
        sql = "insert into `%s` VALUES(" % self.__table_name
        for data in l_data:
            if isinstance(data, int):
                sql = sql + "\'%d\'," % data
            elif isinstance(data, str):
                sql = sql + "\'%s\'," % data
            elif isinstance(data, float) or isinstance(data, double):
                sql = sql + "\'%f\'," % data
            else:
                raise Exception("插入数据库类型不对")

        sql = sql.strip(",")
        sql = sql + ')'

        aklog_debug(sql)
        try:
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
            return True
        except:
            aklog_debug("Error: unable to add entry %s " % sql)
            return False

    def insert_entry_col(self, l_colname, l_data):
        ''' 把数据按列名和值对应插入到数据库
            INSERT INTO `user` ( id, `name`) VALUES ('3','zszxz')
        '''
        aklog_debug('insert_entry_col: %s, %s, %s' % (self.__table_name, l_colname, l_data))
        r = self.table_exists()
        if not r:
            raise Exception("%s 表格不存在" % self.__table_name)

        sql = "insert into `%s` (" % self.__table_name
        for colname in l_colname:
            sql = sql + "%s," % colname

        sql = sql.strip(",")
        sql = sql + ") VALUES ("

        for data in l_data:
            if isinstance(data, int):
                sql = sql + "\'%d\'," % data
            elif isinstance(data, str):
                sql = sql + "\'%s\'," % data
            elif isinstance(data, float) or isinstance(data, double):
                sql = sql + "\'%f\'," % data
            else:
                raise Exception("插入数据库类型不对")

        sql = sql.strip(",")
        sql = sql + ')'

        aklog_debug(sql)
        try:
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
            return True
        except:
            aklog_debug("Error: unable to add entry %s " % sql)
            return False

    def is_col_exist(self, colname):
        sql = f"SELECT COUNT(*) AS column_exists FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{self.__table_name}' AND COLUMN_NAME = '{colname}'"
        self._reConn()
        self.__cursor.execute(sql)
        self.__db.commit()
        results = self.__cursor.fetchall()
        results_str = str(results)
        if results_str.find("1") >= 0:
            return True
        return False

    def update_entry(self, key, condition, colname, data, table_name=None):
        '''在主键存在的情况下更新数据，含自动创建不存在的列
        '''
        r = self.is_col_exist(colname)
        if isinstance(data, int):
            format = "\'%d\'"
            not r and self.create_column_int(colname)
        elif isinstance(data, str):
            format = "\'%s\'"
            not r and self.create_column_text(colname)
        elif isinstance(data, float) or isinstance(data, double):
            format = "\'%f\'"
            not r and self.create_column_double(colname)

        if not table_name:
            table_name = self.__table_name
        sql = f"UPDATE `{table_name}` SET `{colname}`='{data}' WHERE `{key}`='{condition}'"
        aklog_debug(sql)

        try:
            # 执行SQL语句
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
            return True
        except:
            aklog_debug("Error: unable to fetch data %s " % sql)
            return False

    def update_entry2(self, list_key, list_condition, colname, data):
        '''在主键存在的情况下更新数据，含自动创建不存在的列
        '''
        # 创建列名
        r = self.column_exists(colname)
        if isinstance(data, int):
            format = "\'%d\'"
            not r and self.create_column_int(colname)
        elif isinstance(data, str):
            format = "\'%s\'"
            not r and self.create_column_text(colname)
        elif isinstance(data, float) or isinstance(data, double):
            format = "\'%f\'"
            not r and self.create_column_double(colname)

        condition = ""
        if len(list_key) != len(list_condition):
            return False

        for i in range(len(list_key)):
            condition = condition + '`%s`="%s" and ' % (list_key[i], list_condition[i])
        condition = condition[:-4]
        aklog_debug("condition:%s" % condition)

        sql = f"UPDATE `{self.__table_name}` SET `{colname}`='{data}' WHERE {condition}"
        aklog_debug(sql)

        try:
            # 执行SQL语句
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
            return True
        except:
            aklog_debug("Error: unable to fetch data %s " % sql)
            return False

    def fetch(self, sql):
        '''通过sql直接搜
        '''
        aklog_debug(sql)

        try:
            # 执行SQL语句
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
            # 获取所有记录列表
            results = self.__cursor.fetchall()
            return results
        except:
            aklog_debug("Error: unable to fetch data %s " % sql)
            return False

    def create_table_by_string(self, table_name, sql_string):
        sql = "create table if not exists `%s`(%s);" % (table_name, sql_string)
        aklog_debug("sql:%s" % sql)

        try:
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
            self.__table_name = table_name
            return True
        except:
            aklog_debug("Error: unable to create table %s " % sql)
            return False

    def ensure_table_columns(self, table_name: str, table_keys):
        """检查并补齐数据库表字段

        Args:
            table_name (str): 数据表名
            table_keys (dict): 数据表字段信息
        """
        try:
            # 获取现有表字段
            self._reConn()
            self.__cursor.execute(f"SHOW COLUMNS FROM `{table_name}`;")
            existing_columns = {row[0] for row in self.__cursor.fetchall()}

            # 找出缺失字段
            missing_columns = {
                col: col_type
                for col, col_type in table_keys.items()
                if col not in existing_columns
            }

            # 如果有缺失字段则补齐
            for col, col_type in missing_columns.items():
                alter_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{col}` {col_type};"
                aklog_debug(f"[DB] 表 {table_name} 缺失字段 {col}，执行 SQL: {alter_sql}")
                self.__cursor.execute(alter_sql)
                self.__db.commit()

        except Exception as e:
            aklog_error(f"[DB] 检查/补齐字段失败: {e}")

    def create_table(self):
        # sql = "create table if not exists `%s`(revision int primary key,user text,checker text, date date, mergeinfo text, issueid text,issue text, modify text);" % self.__table_name;
        sql = "create table if not exists `%s`(revision int primary key,user text,reviewer text, date date, reason_short text, reason text,des text, status int, story_id int);" % self.__table_name
        aklog_debug("sql:%s" % sql)

        try:
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
            return 1
        except:
            aklog_debug("Error: unable to create table %s " % sql)
            return 0

    def table_exists(self, table_name=None):
        sql = "show tables;"
        self.__cursor.execute(sql)
        tables = [self.__cursor.fetchall()]
        table_list = re.findall('(\'.*?\')', str(tables))
        table_list = [re.sub("'", '', each) for each in table_list]
        if not table_name:
            table_name = self.__table_name
        if table_name in table_list:
            return 1
        else:
            return 0

    def column_exists(self, rep_name):
        sql = ("SELECT GROUP_CONCAT(COLUMN_NAME SEPARATOR ',') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = "
               "'%s' AND TABLE_NAME = '%s';") % (
                  self.__database_name, self.__table_name)

        self.__cursor.execute(sql)
        columns = [self.__cursor.fetchall()]
        columns_list = re.findall('(\'.*?\')', str(columns))
        columns_list = [re.sub("'", '', each) for each in columns_list]

        column_list = columns_list[0].split(',')
        # aklog_debug (column_list)

        if rep_name in column_list:
            return 1
        else:
            return 0

    def copy_table(self, table_name, new_table_name, copy_content=True):
        """复制表格"""
        if copy_content:
            content = '*'
        else:
            content = 'NULL'
        sql = (f'CREATE TABLE {new_table_name} AS'
               f' SELECT {content} FROM {table_name};')
        try:
            self._reConn()
            self.__cursor.execute(sql)
            self.__db.commit()
            return True
        except:
            aklog_debug("Error: unable to copy table %s " % sql)
            return False


class SmartHomeTestCaseSql(AkMysql):

    def __init__(self, host='192.168.10.52', user_name='root', passwd="CJNt{NT@o]",
                 database_name="sqa_testcase_press", table_name=None, port=3306):
        super().__init__(host, user_name, passwd, database_name, table_name, port)
        self.press_case_info_table_keys = {
            'case_name': 'text',
            'enable': 'int',
            'forced_order': 'int',
            'test_count': 'int',
            'test_duration': 'text',
            'select_count': 'int'
        }
        self.press_test_result_table_keys = {
            'case_name': 'text',
            'case_count': 'int',
            'test_count': 'int',
            'pass_count': 'int',
            'fail_count': 'int',
            'error_count': 'int',
            'skip_count': 'int',
            'pass_rate': 'text',
            'test_version': 'text',
            'test_date': 'text',
            'test_duration': 'text',
            'build_user': 'text',
            'url': 'text',
            'fixed': 'int',
            'assignTo': 'text'
        }
        self.function_test_result_table_keys = {
            'test_count': 'int',
            'pass_count': 'int',
            'fail_count': 'int',
            'error_count': 'int',
            'skip_count': 'int',
            'pass_rate': 'text',
            'test_version': 'text',
            'test_date': 'text',
            'test_duration': 'text',
            'build_user': 'text',
            'url': 'text',
            'fixed': 'int',
            'assignTo': 'text'
        }

    # region 版本号

    def read_sqa_versions_list(self) -> list:
        """读取启用的用例信息"""
        table_name = 'sqa_version_release'
        r = self.table_exists(table_name)
        if not r:
            aklog_warn('sqa_version_release表不存在')
            return []

        self.switch_table_name(table_name)
        sql_str = f"SELECT model_id, model_name, version FROM {table_name}"
        results = self.fetch(sql_str)
        versions_list = []
        for row in results:
            model_id, model_name, version = row
            version_info = {'model': model_id,
                            'model_name': model_name,
                            'test_version': version}
            versions_list.append(version_info)
        return versions_list

    # endregion

    # region 压测用例数据库处理

    def create_press_case_info_table(self, model_name):
        """创建压测用例信息表格，修改表格字段时，要同步修改"""
        sql_string = f"id int primary key AUTO_INCREMENT"
        for key, value in self.press_case_info_table_keys.items():
            sql_string += ', %s %s' % (key, value)
        table_name = f'{model_name}_press_case_info'
        self.create_table_by_string(table_name, sql_string)

    def create_press_test_result_table(self, model_name):
        """创建压测执行记录表格"""
        sql_string = f"id int primary key AUTO_INCREMENT"
        for key, value in self.press_test_result_table_keys.items():
            sql_string += ', %s %s' % (key, value)
        table_name = f'{model_name}_press_test_result'
        self.create_table_by_string(table_name, sql_string)

    def write_press_test_results(self, model_name, result: dict):
        """记录测试结果到数据库, result: 字典类型"""
        table_name = f'{model_name}_press_test_result'
        r = self.table_exists(table_name)
        if not r:
            self.create_press_test_result_table(model_name)
            time.sleep(1)
        else:
            # 检查并补齐字段
            self.ensure_table_columns(table_name, self.press_test_result_table_keys)

        result = {key: value for key, value in result.items() if key in self.press_test_result_table_keys}

        self.switch_table_name(table_name)
        keys = list(result.keys())
        values = list(result.values())
        self.insert_entry_col(keys, values)

    def read_press_test_results(self, model_name):
        """读取压测记录"""
        table_name = f'{model_name}_press_test_result'
        r = self.table_exists(table_name)
        if not r:
            self.create_press_test_result_table(model_name)
            time.sleep(1)

        self.switch_table_name(table_name)
        sql_str = "SELECT case_name, test_count, pass_count, test_version, test_date, test_duration FROM %s" % table_name
        results = self.fetch(sql_str)
        test_results = []
        for row in results:
            case_name, test_count, pass_count, test_version, test_date, test_duration = row
            result = {
                'case_name': case_name,
                'test_count': test_count,
                'pass_count': pass_count,
                'test_version': test_version,
                'test_date': test_date,
                'test_duration': test_duration,
            }
            test_results.append(result)
        return test_results

    def read_press_case_info(self, model_name):
        """读取启用的用例信息"""
        table_name = '%s_press_case_info' % model_name
        r = self.table_exists(table_name)
        if not r:
            # 如果用例信息表格不存在，则用通用机型复制过来
            common_press_case_info_table = 'COMMON_press_case_info'
            self.copy_table(common_press_case_info_table, table_name)

        self.switch_table_name(table_name)
        sql_str = "SELECT case_name, enable, test_count, test_duration, select_count, forced_order FROM %s" % table_name
        results = self.fetch(sql_str)
        case_info = {}
        for row in results:
            case_name, enable, test_count, test_duration, select_count, forced_order = row
            if not enable:
                continue
            if not select_count:
                select_count = 0
            case_info[case_name] = {'test_count': test_count,
                                    'test_duration': test_duration,
                                    'select_count': select_count,
                                    'forced_order': forced_order}
        return case_info

    def write_press_case_info(self, model_name, case_info: dict):
        """写入用例信息, case_info: 字典类型"""
        table_name = f'{model_name}_press_case_info'
        r = self.table_exists(table_name)
        if not r:
            # 如果用例信息表格不存在，则用通用机型复制过来
            common_press_case_info_table = 'COMMON_press_case_info'
            self.copy_table(common_press_case_info_table, table_name)

        for key in case_info.keys():
            if key not in self.press_case_info_table_keys.keys():
                del case_info[key]

        self.switch_table_name(table_name)
        keys = list(case_info.keys())
        values = list(case_info.values())
        self.insert_entry_col(keys, values)

    def general_press_case_list_by_version(self, model_name, version):
        """根据测试记录获取用例权重给用例排序，输出用例顺序列表"""
        aklog_info()
        results = self.read_press_test_results(model_name)
        case_info = self.read_press_case_info(model_name)
        press_result_data = {}
        version_branch = version.split('.')[2]
        for result in results:
            case_name = result.get('case_name')
            case_count = result.get('case_count')
            pass_count = result.get('pass_count')
            test_version = result.get('test_version')
            test_duration = result.get('test_duration')
            big_version = test_version.split('.')[2]
            if big_version != version_branch:
                continue
            if big_version not in press_result_data:
                press_result_data[big_version] = {}
            if case_name not in press_result_data[big_version]:
                press_result_data[big_version][case_name] = {}

            if 'test_count' not in press_result_data[big_version][case_name]:
                press_result_data[big_version][case_name]['test_count'] = 0
            if pass_count:
                if case_count:
                    pass_count = int(pass_count / case_count)
                press_result_data[big_version][case_name]['test_count'] += pass_count

            if 'test_duration' not in press_result_data[big_version][case_name]:
                press_result_data[big_version][case_name]['test_duration'] = 0
            if test_duration:
                test_duration = duration_to_seconds(test_duration)
                if case_count:
                    test_duration = int(test_duration / case_count)
                press_result_data[big_version][case_name]['test_duration'] += test_duration

        case_weight_data = {}
        # 从用例信息遍历每一个用例，获取已测试次数和用例要求次数的比值权重
        if version_branch in press_result_data:
            for case in case_info:
                if case not in press_result_data[version_branch]:
                    case_weight_data[case] = 0
                elif case_info[case].get('test_count'):
                    case_weight_data[case] = round(
                        press_result_data[version_branch][case]['test_count'] / case_info[case]['test_count'], 2)
                elif case_info[case].get('test_duration'):
                    duration = duration_to_seconds(case_info[case]['test_duration'])
                    case_weight_data[case] = round(
                        press_result_data[version_branch][case]['test_duration'] / duration, 2)
        else:
            for case in case_info:
                case_weight_data[case] = 0

        # 根据用例权重来进行从小到大排序
        def sort_key(key):
            nonlocal case_weight_data
            return case_weight_data[key], random.random()

        case_list = sorted(case_weight_data, key=sort_key)

        # 根据select_count从小到大再排序一次，如果select_count相同，则按照之前的权重排序
        def sort_case_list(case):
            return case_info[case]['select_count']

        case_list = sorted(case_list, key=sort_case_list)
        aklog_debug(case_list)
        return case_list

    def select_press_case_without_testing(self, model_name, all_case_list: list, selected_list: list):
        """
        选择未在测试中的用例
        用于多台设备同时执行相同用例时，选择未被执行或者执行次数最少的用例
        Args:
            model_name ():
            all_case_list ():
            selected_list ():

        Returns:

        """
        aklog_info()
        remain_case_list = []
        for case in all_case_list:
            if case not in selected_list:
                remain_case_list.append(case)
        if len(remain_case_list) == 0:
            return None
        case_info = self.read_press_case_info(model_name)
        minimum_select_case = remain_case_list[0]
        minimum_select_count = case_info[minimum_select_case]['select_count']
        for case in remain_case_list:
            if case_info[case]['select_count'] < minimum_select_count:
                minimum_select_count = case_info[case]['select_count']
                minimum_select_case = case
        selected_list.append(minimum_select_case)
        aklog_debug(minimum_select_case)
        return minimum_select_case

    def increase_press_case_select_count(self, model_name, select_case):
        """设置select_count递增"""
        aklog_info()
        case_info = self.read_press_case_info(model_name)
        select_count = case_info[select_case].get('select_count') + 1
        self.update_entry('case_name', select_case, 'select_count', select_count)
        return select_case

    def decrease_press_case_select_count(self, model_name, select_case):
        """设置select_count递减"""
        aklog_info()
        case_info = self.read_press_case_info(model_name)
        select_count = case_info[select_case].get('select_count') - 1
        if select_count < 0:
            select_count = 0
        self.update_entry('case_name', select_case, 'select_count', select_count)
        return select_case

    def general_press_modules_name_from_sql(self, model_name):
        """从mysql获取用例套件，然后写入到firmware_info.xml的modules_name里面"""
        case_info = self.read_press_case_info(model_name)
        modules_name = """"""
        for case_name in case_info:
            modules_info = {case_name: {'CasePriority': 'P2'}}
            if case_info[case_name].get('test_count'):
                modules_info[case_name]['TestCounts'] = case_info[case_name]["test_count"]
            elif case_info[case_name].get('test_duration'):
                modules_info[case_name]['TestDuration'] = case_info[case_name]["test_duration"]
            if case_info[case_name].get('forced_order'):
                modules_info[case_name]['ForcedOrder'] = case_info[case_name]["forced_order"]
            module_name = dict_dumps_2_json(modules_info)
            modules_name += '%s;\n' % module_name
        return modules_name

    # endregion

    # region 功能自动化用例数据库处理

    def create_function_test_result_table(self, model_name):
        """创建功能自动化执行记录表格"""
        sql_string = f"id int primary key AUTO_INCREMENT"
        for key, value in self.function_test_result_table_keys.items():
            sql_string += ', %s %s' % (key, value)
        table_name = f'{model_name}_function_test_result'
        self.create_table_by_string(table_name, sql_string)

    def write_function_test_results(self, model_name, result: dict):
        """记录测试结果到数据库, result: 字典类型"""
        table_name = f'{model_name}_function_test_result'
        r = self.table_exists(table_name)
        if not r:
            self.create_function_test_result_table(model_name)
            time.sleep(1)
        else:
            # 检查并补齐字段
            self.ensure_table_columns(table_name, self.function_test_result_table_keys)

        self.switch_table_name(table_name)

        result = {key: value for key, value in result.items() if key in self.function_test_result_table_keys}

        keys = list(result.keys())
        values = list(result.values())
        self.insert_entry_col(keys, values)

    def read_function_test_results(self, model_name):
        """
        读取功能自动化测试记录
        return: list
        """
        table_name = f'{model_name}_function_test_result'
        r = self.table_exists(table_name)
        if not r:
            self.create_function_test_result_table(model_name)
            time.sleep(1)

        self.switch_table_name(table_name)
        sql_str = "SELECT test_count, pass_count, test_version, test_date, test_duration FROM %s" % table_name
        results = self.fetch(sql_str)
        test_results = []
        for row in results:
            test_count, pass_count, test_version, test_date, test_duration = row
            result = {
                'test_count': test_count,
                'pass_count': pass_count,
                'test_version': test_version,
                'test_date': test_date,
                'test_duration': test_duration,
            }
            test_results.append(result)
        return test_results

    # endregion

    # region 手机APP压测记录

    def write_device_map_info(self, app_type, map_info):
        """写入设备id和手机型号对应信息, map_info: 字典类型"""
        table_name = f'APP{app_type}_device_map_info'
        r = self.table_exists(table_name)
        if not r:
            return
        self.switch_table_name(table_name)
        keys = list(map_info.keys())
        values = list(map_info.values())
        self.insert_entry_col(keys, values)

    def read_app_fastbot_test_results(self, model_name):
        """读取压测记录"""
        table_name = f'APP{model_name}_press_test_result'
        r = self.table_exists(table_name)
        if not r:
            return None

        self.switch_table_name(table_name)
        sql_str = "SELECT model_name, device_id, test_date, duration FROM %s" % table_name
        results = self.fetch(sql_str)
        test_results = []
        for row in results:
            model_name, device_id, test_date, duration = row
            result = {
                'model_name': model_name,
                'device_id': device_id,
                'test_date': test_date,
                'duration': duration,
            }
            test_results.append(result)
        return test_results

    # endregion


def get_stress_test_results_summary(month=None):
    """
    获取家居各个机型自动化执行结果
    """
    MODELS = ['PS51', 'PS52', 'PS51V2', 'RT61', 'CT61', 'KS53', 'PG71', 'PH81', 'PHX1', 'C319H', 'X933H', 'G31',
              'KS41', 'AKUBELACLOUD', 'BELAHOME', 'AKUBELASOLUTION']

    now = datetime.datetime.now().date()
    if not month:
        month = now.month
    else:
        month = int(month)
    # start_date = datetime.datetime(now.year, month, 1).date()
    # end_date = datetime.datetime(now.year, month, calendar.monthrange(now.year, month)[1]).date()

    sql = SmartHomeTestCaseSql()
    sql.connect()

    test_results_info = {}
    for model in MODELS:
        results = sql.read_press_test_results(model)
        result_info = {
            'model': model,
            'test_count': 0,
            'pass_count': 0,
            'pass_rate': '',
            'case_list': ''
        }
        case_list = []
        for result in results:
            test_date_month = int(result.get('test_date')[4:6])
            test_date_year = int(result.get('test_date')[0:4])
            if test_date_month != month or test_date_year != now.year:
                continue
            result_info['test_count'] += int(result.get('test_count'))
            result_info['pass_count'] += int(result.get('pass_count'))
            if result.get('case_name') not in case_list:
                case_list.append(result.get('case_name'))

        if case_list:
            result_info['case_list'] = ', '.join(case_list)

        if result_info['test_count'] == 0:
            result_info['pass_rate'] = '0%'
        else:
            result_info['pass_rate'] = '{}%'.format(
                round(result_info['pass_count'] / result_info['test_count'] * 100, 1))

        test_results_info[model] = result_info

    # 将字典转换为 DataFrame
    df = pd.DataFrame.from_dict(test_results_info, orient='index')
    # 指定 Excel 文件名
    excel_file = f'stress-test-results.xlsx'
    # 将 DataFrame 写入 Excel 文件
    df.to_excel(excel_file, index=False, columns=['model', 'test_count', 'pass_count', 'pass_rate', 'case_list'])
    print(f"数据已成功写入 {excel_file}")

    # aklog_debug(test_results_info)
    return test_results_info


def get_function_test_results_summary(month=None):
    """
    获取家居各个机型自动化执行结果
    """
    MODELS = ['PS51', 'PS52', 'PS51V2', 'RT61', 'CT61', 'KS53', 'PG71', 'PH81', 'PHX1', 'C319H', 'X933H', 'G31',
              'KS41', 'AKUBELACLOUD', 'BELAHOME']

    now = datetime.datetime.now().date()
    if not month:
        month = now.month
    else:
        month = int(month)

    sql = SmartHomeTestCaseSql()
    sql.connect()

    test_results_info = {}
    for model in MODELS:
        results = sql.read_function_test_results(model)
        result_info = {
            'model': model,
            'test_count': 0,
            'pass_count': 0,
            'pass_rate': '',
            'versions': ''
        }
        versions = []
        for result in results:
            test_date_month = int(result.get('test_date')[4:6])
            test_date_year = int(result.get('test_date')[0:4])
            if test_date_month != month or test_date_year != now.year:
                continue
            result_info['test_count'] += int(result.get('test_count'))
            result_info['pass_count'] += int(result.get('pass_count'))
            if result.get('test_version') not in versions:
                versions.append(result.get('test_version'))

        if versions:
            result_info['versions'] = ', '.join(versions)

        if result_info['test_count'] == 0:
            result_info['pass_rate'] = '0%'
        else:
            result_info['pass_rate'] = '{}%'.format(
                round(result_info['pass_count'] / result_info['test_count'] * 100, 1))

        test_results_info[model] = result_info

    # 将字典转换为 DataFrame
    df = pd.DataFrame.from_dict(test_results_info, orient='index')
    # 指定 Excel 文件名
    excel_file = f'function-test-results.xlsx'
    # 将 DataFrame 写入 Excel 文件
    df.to_excel(excel_file, index=False, columns=['model', 'test_count', 'pass_count', 'pass_rate', 'versions'])
    print(f"数据已成功写入 {excel_file}")

    # aklog_debug(test_results_info)
    return test_results_info


def get_stress_test_results_summary_by_week(end_date=None):
    """
    获取家居各个机型自动化执行结果
    获取今天之前的一周内记录
    end_date: 20240823
    """
    MODELS = ['PS51', 'PS52', 'PS51V2', 'RT61', 'CT61', 'KS53', 'PG71', 'PH81', 'PHX1', 'C319H', 'X933H', 'G31',
              'KS41', 'AKUBELACLOUD', 'BELAHOME', 'AKUBELASOLUTION', 'WEB']

    if end_date:
        end_date = datetime.datetime.strptime(end_date, "%Y%m%d")
    else:
        # 获取今天的日期
        end_date = datetime.datetime.now()
    # 计算前7天和前1天的日期
    seven_days_ago = end_date - datetime.timedelta(days=7)
    one_day_ago = end_date - datetime.timedelta(days=1)
    # 格式化日期为字符串
    end_date = end_date.strftime('%Y%m%d')
    start_date_int = int(seven_days_ago.strftime('%Y%m%d'))
    end_date_int = int(one_day_ago.strftime('%Y%m%d'))

    sql = SmartHomeTestCaseSql()
    sql.connect()

    test_results_info = {}
    for model in MODELS:
        results = sql.read_press_test_results(model)
        result_info = {
            'model': model,
            'test_version': '',
            'test_count': 0,
            'pass_rate': '',
            'test_duration': '',
            'case_list': ''
        }
        case_list = []
        test_versions = []
        pass_count = 0
        for result in results:
            test_date_int = int(result.get('test_date'))
            if test_date_int < start_date_int or test_date_int > end_date_int:
                continue
            result_info['test_count'] += int(result.get('test_count'))
            pass_count += int(result.get('pass_count'))
            if result.get('case_name') and result.get('case_name') not in case_list:
                case_list.append(result.get('case_name'))
            if result.get('test_version') not in test_versions:
                test_versions.append(result.get('test_version'))

        if result_info['test_count'] == 0:
            continue
        if case_list:
            result_info['case_list'] = ', '.join(case_list)
        if test_versions:
            result_info['test_version'] = ', '.join(test_versions)

        if result_info['test_count'] == 0:
            result_info['pass_rate'] = '0%'
        else:
            result_info['pass_rate'] = '{}%'.format(
                round(pass_count / result_info['test_count'] * 100, 1))

        test_results_info[model] = result_info

    # 将字典转换为 DataFrame
    df = pd.DataFrame.from_dict(test_results_info, orient='index')
    # 指定 Excel 文件名
    excel_dir = f'{os.getcwd()}\\test_result\\{end_date}'
    if not os.path.exists(excel_dir):
        os.makedirs(excel_dir)
    excel_file = f'{excel_dir}\\stress-test-results-{end_date}.xlsx'
    # 将 DataFrame 写入 Excel 文件
    df.to_excel(excel_file, index=False, columns=[
        'model', 'test_version', 'test_count', 'pass_rate', 'test_duration', 'case_list'])
    print(f"数据已成功写入 {excel_file}")

    # aklog_debug(test_results_info)
    return test_results_info


def get_function_test_results_summary_by_week(end_date=None):
    """
    获取家居各个机型自动化执行结果
    """
    MODELS = ['PS51', 'PS52', 'PS51V2', 'RT61', 'CT61', 'KS53', 'PG71', 'PH81', 'PHX1', 'C319H', 'X933H', 'G31',
              'KS41', 'AKUBELACLOUD', 'BELAHOME', 'AKUBELASOLUTION', 'WEB']

    if end_date:
        end_date = datetime.datetime.strptime(end_date, "%Y%m%d")
    else:
        # 获取今天的日期
        end_date = datetime.datetime.now()
    # 计算前7天和前1天的日期
    seven_days_ago = end_date - datetime.timedelta(days=7)
    one_day_ago = end_date - datetime.timedelta(days=1)
    # 格式化日期为字符串
    end_date = end_date.strftime('%Y%m%d')
    start_date_int = int(seven_days_ago.strftime('%Y%m%d'))
    end_date_int = int(one_day_ago.strftime('%Y%m%d'))

    sql = SmartHomeTestCaseSql()
    sql.connect()

    test_results_info = {}
    for model in MODELS:
        results = sql.read_function_test_results(model)
        result_info = {
            'model': model,
            'test_version': '',
            'test_count': 0,
            'pass_rate': '',
            'test_duration': '',
            'case_list': ''
        }
        # case_list = []
        versions = []
        pass_count = 0
        for result in results:
            test_date = result.get('test_date')
            try:
                date_obj = datetime.datetime.strptime(test_date, '%Y/%m/%d %H:%M:%S')
                test_date = date_obj.strftime('%Y%m%d')
            except:
                pass

            test_date_int = int(test_date)
            if test_date_int < start_date_int or test_date_int > end_date_int:
                continue
            result_info['test_count'] += int(result.get('test_count'))
            pass_count += int(result.get('pass_count'))
            if result.get('test_version') not in versions:
                versions.append(result.get('test_version'))
            # if result.get('case_name') and result.get('case_name') not in case_list:
            #     case_list.append(result.get('case_name'))
        
        if result_info['test_count'] == 0:
            continue
        # if case_list:
        #     result_info['case_list'] = ', '.join(case_list)
        if versions:
            result_info['test_version'] = ', '.join(versions)

        if result_info['test_count'] == 0:
            result_info['pass_rate'] = '0%'
        else:
            result_info['pass_rate'] = '{}%'.format(
                round(pass_count / result_info['test_count'] * 100, 1))

        test_results_info[model] = result_info

    # 将字典转换为 DataFrame
    df = pd.DataFrame.from_dict(test_results_info, orient='index')
    # 指定 Excel 文件名
    excel_dir = f'{os.getcwd()}\\test_result\\{end_date}'
    if not os.path.exists(excel_dir):
        os.makedirs(excel_dir)
    excel_file = f'{excel_dir}\\function-test-results-{end_date}.xlsx'
    # 将 DataFrame 写入 Excel 文件
    df.to_excel(excel_file, index=False, columns=[
        'model', 'test_version', 'test_count', 'pass_rate', 'test_duration'])
    print(f"数据已成功写入 {excel_file}")

    # aklog_debug(test_results_info)
    return test_results_info


def get_app_fastbot_test_results_summary_by_week(end_date=None):
    """
    获取手机Fastbot压测结果
    获取今天之前的一周内记录
    end_date: 20240823
    """
    MODELS = ['android', 'ios']

    if end_date:
        end_date = datetime.datetime.strptime(end_date, "%Y%m%d")
    else:
        # 获取今天的日期
        end_date = datetime.datetime.now()
    # 计算前7天和前1天的日期
    seven_days_ago = end_date - datetime.timedelta(days=7)
    one_day_ago = end_date - datetime.timedelta(days=1)
    # 格式化日期为字符串
    end_date = end_date.strftime('%Y%m%d')
    start_date_int = int(seven_days_ago.strftime('%Y%m%d'))
    end_date_int = int(one_day_ago.strftime('%Y%m%d'))

    sql = SmartHomeTestCaseSql()
    sql.connect()

    test_results_info = {}
    for model in MODELS:
        results = sql.read_app_fastbot_test_results(model)
        for result in results:
            test_date_int = int(re.sub(r'\D', '', result.get('test_date')[0:10]))
            if test_date_int < start_date_int or test_date_int > end_date_int:
                continue
            if result.get('device_id') and (':' in result.get('device_id') or '-' in result.get('device_id')):
                # 排除模拟器
                continue
            model_name = result.get('model_name')
            if model_name not in test_results_info:
                test_results_info[model_name] = {
                    'model_name': model_name,
                    'type': model,
                    'test_count': 0,
                    'test_duration': 0,
                }
            test_results_info[model_name]['test_count'] += 1
            test_duration = result.get('duration')
            if test_duration:
                test_duration = duration_to_seconds(test_duration)
            else:
                test_duration = 0
            test_results_info[model_name]['test_duration'] += test_duration
    # print(test_results_info)
    for model_name in test_results_info:
        test_results_info[model_name]['test_duration'] = seconds_to_duration(
            test_results_info[model_name]['test_duration'])
    if not test_results_info:
        return None
    # 将字典转换为 DataFrame
    df = pd.DataFrame.from_dict(test_results_info, orient='index')
    # 指定 Excel 文件名
    excel_dir = f'{os.getcwd()}\\test_result\\{end_date}'
    if not os.path.exists(excel_dir):
        os.makedirs(excel_dir)
    excel_file = f'{excel_dir}\\app-fastbot-test-results-{end_date}.xlsx'
    # 将 DataFrame 写入 Excel 文件
    df.to_excel(excel_file, index=False, columns=['model_name', 'type', 'test_count', 'test_duration'])
    print(f"数据已成功写入 {excel_file}")

    # aklog_debug(test_results_info)
    return test_results_info


def get_monkey_test_results_summary_by_week(end_date=None):
    """
    获取家居各个机型自动化执行结果
    获取今天之前的一周内记录
    end_date: 20240823
    """
    MODELS = ['PS51', 'PS52', 'PS51V2', 'RT61', 'CT61', 'KS53', 'PG71', 'PH81', 'PHX1', 'C319H', 'X933H', 'KS41']

    if end_date:
        end_date = datetime.datetime.strptime(end_date, "%Y%m%d")
    else:
        # 获取今天的日期
        end_date = datetime.datetime.now()
    # 计算前7天和前1天的日期
    seven_days_ago = end_date - datetime.timedelta(days=7)
    one_day_ago = end_date - datetime.timedelta(days=1)
    # 格式化日期为字符串
    end_date = end_date.strftime('%Y%m%d')
    start_date_int = int(seven_days_ago.strftime('%Y%m%d'))
    end_date_int = int(one_day_ago.strftime('%Y%m%d'))

    sql = SmartHomeTestCaseSql()
    sql.connect()

    test_results_info = {}
    for model in MODELS:
        results = sql.read_press_test_results(model)
        result_info = {
            'model': model,
            'test_count': 0,
            'test_duration': 0
        }
        for result in results:
            test_date_int = int(result.get('test_date'))
            if test_date_int < start_date_int or test_date_int > end_date_int:
                continue
            if result.get('case_name') != 'AutoTestMonkey':
                continue
            result_info['test_count'] += int(result.get('test_count'))
            test_duration = result.get('test_duration')
            if test_duration:
                test_duration = duration_to_seconds(test_duration)
            else:
                test_duration = 0
            result_info['test_duration'] += test_duration
        if result_info['test_count'] == 0:
            continue
        result_info['test_duration'] = seconds_to_duration(result_info['test_duration'])
        test_results_info[model] = result_info

    # 将字典转换为 DataFrame
    df = pd.DataFrame.from_dict(test_results_info, orient='index')
    # 指定 Excel 文件名
    excel_dir = f'{os.getcwd()}\\test_result\\{end_date}'
    if not os.path.exists(excel_dir):
        os.makedirs(excel_dir)
    excel_file = f'{excel_dir}\\monkey-test-results-{end_date}.xlsx'
    # 将 DataFrame 写入 Excel 文件
    df.to_excel(excel_file, index=False, columns=['model', 'test_count', 'test_duration'])
    print(f"数据已成功写入 {excel_file}")

    # aklog_debug(test_results_info)
    return test_results_info


if __name__ == '__main__':
    print('test')
    # sql = SmartHomeTestCaseSql()
    # sql.connect()
    # sql.write_press_case_info('PS51', {'case_name': 'A_AutoTestUpgradeInit', 'test_count': 500})
    # sql.write_press_case_info('PS51', {'case_name': 'AutoTestMonkey', 'test_duration': '5d'})
    # sql.update_entry('case_name', 'A_AutoTestUpgradeInit', 'case_count', 1, 'COMMON_press_case_info')
    get_function_test_results_summary_by_week()
    get_stress_test_results_summary_by_week()
    get_app_fastbot_test_results_summary_by_week()
    get_monkey_test_results_summary_by_week()
