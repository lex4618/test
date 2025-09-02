#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import io
import sys
import os
import pymysql

root_path = os.getcwd();
pos = root_path.find("AKautotest");

if pos == -1:
    print("runtime error");
    exit(1);

root_path = root_path[0:pos + len("AKautotest")]

sys.path.append(root_path)

import akcommon_define
from akcommon_define import *


#### source code ######

class CAKsql:
    """Zentao mysql查询接口"""
    
    __db = ''
    __cursor = ''
    __zentao_addr = ""
    def __init__(self, host="", user_name="", passwd="", database_name=""):
        aklog_printf("%s host_port:%s" % (self.__class__.__name__, host));
        self.__host = host;
        self.__user = user_name;
        self.__passwd = passwd;
        self.__database_name = database_name;
               
    def __del__(self):
        if self.__db :
            self.__db.close()
        
    def connect(self):
        try:
            self.__db = pymysql.connect(self.__host, self.__user, self.__passwd, self.__database_name)             
        except:
            aklog_printf ("connect to %s failed!" % self.__host);
            return False;
            
        self.__cursor = self.__db.cursor()
        self.__cursor.execute("SELECT VERSION()")
        data = self.__cursor.fetchone()
        aklog_printf("Database version : %s " % data)
        
        return True;
    
    def _reConn (self,num = 28800,stime = 3): 
        _number = 0
        _status = True
        while _status and _number <= num:
            try:
                pings = self.__db.ping()
                aklog_printf ("ping res:%s" % pings);
                _status = False
            except:
                aklog_printf ('connect');
                if self.connect(): #重新连接,成功退出
                    _status = False
                    break
                _number += 1
                time.sleep(stime)

    def create_table(self, sql):
        sql = decode_sql(sql);
        aklog_printf("sql:%s " % (sql));

        try:
            self._reConn();
            self.__cursor.execute(sql)
            self.__db.commit()
        except:
            print("Error: unable to create table %s " % sql)

        return 0;

    def insert(self, sql):
        sql = decode_sql(sql);
        aklog_printf("sql:%s " % (sql));
        try:
            self._reConn();
            self.__cursor.execute(sql)
            self.__db.commit()
        except:
            print("Error: unable to add entry %s " % sql)

        return 0;

    def select_fetch(self, sql):
        sql = decode_sql(sql);
        aklog_printf ("sql:%s " % (sql));

        try:
            # 执行SQL语句
            self._reConn();
            self.__cursor.execute(sql)
            # 获取所有记录列表
            results = self.__cursor.fetchall()
            return results;
        except:
            aklog_printf ("Error: unable to fetch: %s " % sql)

        return False;

"""     
#测试代码
lsql = CAKsql("192.168.12.222", "root", "root", "zentao");

ret = lsql.connect();
if not ret :
    exit(1)

r = lsql.select_fetch("select * from zt_task where id = 12345")
print (type(r))
if isinstance(r, tuple) :
    print (r);
    
r = lsql.create_table("create table if not exists table_name(version text,revision text,svnprj text, jenkinsprj text, date date);")

r= lsql.insert("insert into table_name VALUES(\'%s\', \'%s\', \'%s\', \'%s\', \'%s\') " % ( rom_version, revision, svnprj, jenkins_prj, date"));

"""

'''demo
isql = CAKsql("192.168.12.40", "root", "root", "ak_version");
r = isql.connect();
select_sql = encode_sql("SELECT * FROM `akmodels`")
r = isql.select_fetch(select_sql);
aklog_printf(r);
'''