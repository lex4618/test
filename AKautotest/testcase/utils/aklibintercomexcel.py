import traceback

import xlwt
import json


class newexcel():
    def __init__(self):
        self.wb = xlwt.Workbook(encoding='utf-8')
        self.sheets = {}
        self.data_row_index = {}

    def addsheet(self, sheetname):
        self.sheets[sheetname] = self.wb.add_sheet(sheetname)
        self.data_row_index[sheetname] = 0

    def write_hearder(self, sheetname, headerlist=[]):
        _count = 0
        for head in headerlist:
            self.sheets[sheetname].write(0, _count, head)
            _count += 1
        self.data_row_index[sheetname] += 1

    def write_data(self, sheetname, data_list):
        """
        # 写多行多列数据,  传入二维列表
        """
        for data in data_list:
            column = 0
            for each_data in data:
                if len(str(each_data)) > 32767:
                    each_data = str(each_data)[:10000]  # 文本太长写不下会报错
                if type(each_data) == dict:
                    each_data = json.dumps(each_data, indent=4)
                    self.sheets[sheetname].write(self.data_row_index[sheetname], column, each_data)
                else:
                    try:
                        each_data = json.loads(str(each_data).replace("'", '"'))
                        each_data = json.dumps(each_data, indent=4)
                        self.sheets[sheetname].write(self.data_row_index[sheetname], column, each_data)
                    except:
                        self.sheets[sheetname].write(self.data_row_index[sheetname], column, str(each_data))
                column += 1
            self.data_row_index[sheetname] += 1

    def save(self, savepath):
        self.wb.save(savepath)
