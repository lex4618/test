#!/usr/bin/env python3
# -*- coding: utf-8 -*-

######## Import Start ########

import xlrd
import shutil
import datetime
import csv
from xlutils.copy import copy
import time
import os
import sys
import xlsxwriter
import xlwt

# 获取根目录
root_path = os.getcwd();
pos = root_path.find("AKautotest");

if pos == -1 :
    print("runtime error");
    exit(1);

root_path = root_path[0:pos+len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *

######## Import End ########


def CreatReport(template_file):
    str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    report_dir = os.path.join(root_path,'outputs','Report','Cloud',str(time.strftime("%Y")),str(time.strftime("%m")),str(time.strftime("%d")))
    if os.path.exists(report_dir):
        os.makedirs(report_dir)
    report_file = report_dir + '/' + 'Report' + str + '.xls'
    shutil.copy(template_file,report_file) #copy文件并重命名

def WriteData(filename,sheet,rowx,colx,data):
    rb = xlrd.open_workbook(filename,formatting_info=True)
    # 复制excel
    wb = copy(rb)
    # 从复制的excel文件中，得到第三个sheet
    sheet = wb.get_sheet(sheet)
    sheet.write(rowx-1, colx-1, data)
    wb.save(filename)
    # oldWb = xlrd.open_workbook('CloudV4.3_Resulttemplate.xls', formatting_info=True);  # 先打开已存在的表
    # newWb = copy(oldWb)  # 复制
    # newWs = newWb.get_sheet(2);  # 取sheet表
    # newWs.write(2, 10, "helloworld");  # 写入 2行4列写入pass
    # newWb.save('CloudV4.3_Resulttemplate.xls');  # 保存至result路径
def ReadCSVData(filename_csv):
    f = open(filename_csv, 'r')
    csvreader = csv.reader(f)
    final_list = list(csvreader)
    # print(final_list)
    # print(len(final_list))
    li_MAC = []
    for i in range(1, len(final_list)):
        '''[['MAC'], ['0C1105133AEF'], ['0C1105134AEF'], ['0C1105135AEF'], ['0C1105136AEF'], ['0C1105137AEF']]
             6
            0C1105133AEF
            0C1105134AEF
            0C1105135AEF
            0C1105136AEF
            0C1105137AEF
            ['0C1105133AEF', '0C1105134AEF', '0C1105135AEF', '0C1105136AEF', '0C1105137AEF']'''
        MAC = final_list[i]
        # print(MAC)
        MAC = MAC[0]
        # print(MAC)
        li_MAC.append(MAC)
    # print(li_MAC)
    return li_MAC
def ReadExcelData(filename_excel,sheet,rowx,colx):
    # filename_excel = r"C:\\Users\\Administrator\\PycharmProjects\\cloudV4.3\\CloudV4.3_Resulttemplate.xls"
    bk = xlrd.open_workbook(filename_excel)  # 打开excel
    sh = bk.sheet_by_name(sheet)  # 选择sheet为test
    value = sh.cell_value(rowx - 1, colx - 1)
    return value
def DataOutputMass(filename_excel,sheet='CommonInformation'):
    bk=xlrd.open_workbook(filename_excel)#打开excel
    sh=bk.sheet_by_name(sheet)#选择sheet为test
    li_content=[]
    for i in range(1,35):
        cell_value=sh.row(i)[1]
        li_content.append(cell_value.value)
    # aklog_printf(li_content)
    li_Name=[]
    for j in range(1,35):
        cell_value=sh.row(j)[0]
        li_Name.append(cell_value.value)
    # aklog_printf(li_Name)
    list_dict=dict(map(lambda x,y:[x,y],li_Name,li_content))
    return list_dict

def get_all_data_from_excel(excel_file):
    bk = xlrd.open_workbook(excel_file)  # 打开excel
    sheets = bk.sheet_names()
    aklog_printf(sheets)
    sheet_list = []
    sheet_value_list = []
    for sheet in sheets:
        sheet_list.append(sheet)
        sh = bk.sheet_by_name(sheet)  # 选择sheet为test
        row = sh.nrows
        column = sh.ncols
        li_key = []
        for i in range(0, column):
            cell_value = sh.row(0)[i]
            li_key.append(cell_value.value)
        # aklog_printf(li_key)
        li = []
        for k in range(1, row):
            li_content = []
            for j in range(0, column):
                cell_value = sh.row(k)[j]
                li_content.append(cell_value.value)
            # aklog_printf(li_content)
            list_dict = dict(map(lambda x, y: [x, y], li_key, li_content))
            # print(list_dict)
            li.append(list_dict)
        aklog_printf(li)
        sheet_value_list.append(li)
    #aklog_printf(sheet_value_list)
    sheet_dict = dict(map(lambda x, y: [x, y],sheet_list, sheet_value_list))
    aklog_printf(sheet_dict)
    return sheet_dict

'''
测试代码

if __name__ == '__main__':
    file = root_path + '/testdata/AndroidIndoor.xls'
    phonecall_info = get_all_data_from_excel(file)
    print(phonecall_info['device_info'])
'''






