# -*- coding: UTF-8 -*-﻿
import io
import sys
import os
import pymysql
import urllib
import re
import chardet
from html.parser import HTMLParser
from urllib import request, response,error,parse
from urllib.parse import quote,unquote

root_path = os.getcwd();
pos = root_path.find("AKautotest");

if pos == -1 :
    print("runtime error");
    exit(1);

root_path = root_path[0:pos+len("AKautotest")]

sys.path.append(root_path);

import akcommon_define
from akcommon_define import *

#### source code ######

'''用来对sql语句编码，确保在传递时正确'''
def encode_sql(sql):
    return quote(sql, 'utf-8');

'''用来对编码后的sql语句进行解码'''
def decode_sql(sql):
    return unquote(sql, 'utf-8');