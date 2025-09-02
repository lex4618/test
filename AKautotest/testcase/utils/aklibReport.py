# -*- coding: utf-8 -*-

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
import datetime
import time
from string import Template


class akreport:
    __device_name = ''
    __ReportFile = ''
    __ReportDir = ''

    def __init__(self, device_name):
        self.__device_name = device_name
        self.__ReportDir = os.path.join(root_path, 'outputs', 'Report', self.__device_name, str(time.strftime("%Y")),
                                        str(time.strftime("%m")), str(time.strftime("%d")))
        if not os.path.exists(self.__ReportDir):
            # print('文件夹不存在，进行创建')
            os.makedirs(self.__ReportDir)
        self.__ReportFile = self.__ReportDir + '/' + str(datetime.date.today()) + '-' + str(
            time.strftime('%H%M%S')) + '--Report.html'

    def GetReportFile(self):
        return self.__ReportFile


class aklibreport_html(object):

    def __init__(self, browser, file_path):
        self.browser = browser
        self.url = file_path
        # self.browser.init_headless()
        self.file_dir, html_file = os.path.split(file_path)
        self.file_name = os.path.splitext(html_file)[0]

    def browser_init(self):
        # self.browser.init()
        self.browser.init_headless()

    def browser_close_and_quit(self):
        self.browser.close_and_quit()

    def visit_url(self):
        for i in range(3):
            try:
                self.browser.visit_url(self.url)
                return True
            except:
                aklog_printf(traceback.format_exc())
                time.sleep(10)
                continue
        return False

    def report_html_screenshot(self):
        try:
            self.browser_init()
            self.visit_url()
            time.sleep(10)
            if not self.browser.get_ele_counts_by_xpath('/html/body/iframe'):
                for i in range(10):
                    if not self.browser.get_value_by_id('testName'):
                        time.sleep(3)
                    else:
                        break

                if config_get_value_from_ini_file('config', 'report_only_view_failed'):
                    flag = 0
                    self.browser.click_btn_by_id('filterResult_chosen')
                    counts = self.browser.get_ele_counts_by_xpath('//*[@id="filterResult_chosen"]/div/ul/li')
                    if counts and counts >= 1:
                        for i in range(1, counts + 1):
                            select_ele_xpath = '//*[@id="filterResult_chosen"]/div/ul/li[%s]' % i
                            if self.browser.get_value_by_xpath(select_ele_xpath) == '失败':
                                self.browser.click_btn_by_xpath(select_ele_xpath)
                                flag = 1
                                break
                        if flag == 0:
                            self.browser.click_btn_by_id('filterResult_chosen')
                        time.sleep(3)
            self.browser.screen_shot_total_page_as_file(self.file_dir, self.file_name, form="png", height_limit=5400)
            report_img_file = os.path.join(self.file_dir, self.file_name + '.png')
            self.browser_close_and_quit()
            return report_img_file
        except:
            aklog_printf(traceback.format_exc())
            return None


def write_to_html_report(title, case_name, process_info):
    report_dir = aklog_get_result_dir()
    report_path = os.path.join(report_dir, "Report_Process.html")
    html_template = Template("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>$title</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .case-section { margin: 15px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            .case-name { color: #2c3e50; margin: 0 0 10px 0; }
            .process-table { width: 100%; border-collapse: collapse; }
            .process-table th, .process-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .process-table th { background-color: #f5f5f5; }
        </style>
    </head>
    <body>
        <h1> $title </h1>
        $case_entries
    </body>
    </html>
    """)
    case_entry_template = Template("""
    <div class="case-section">
        <h3 class="case-name" style="background-color: pink;">脚本名称：$case_name</h3>
        <table class="process-table">
            $process_rows
        </table>
    </div>
    """)
    process_rows = ""
    for proc in process_info:
        process_rows += f"""
        <tr>
            <td>{proc}</td>
        </tr>
        """

    current_case_html = case_entry_template.substitute(
        case_name=case_name,
        process_rows=process_rows,
        title=title
    )
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            existing_html = f.read()
        updated_html = existing_html.replace("</body>", f"{current_case_html}</body>")
    else:
        updated_html = html_template.substitute(case_entries=current_case_html, title=title)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(updated_html)
    aklog_debug(f"{title}报告：{report_path}")


"""
测试代码
"""
if __name__ == '__main__':
    print('测试代码')
    report_browser = libbrowser()
    report_file = r'E:/SVN_Python/Develop/AKautotest/outputs/Results/PS51/2022/12/20/220549/Report.html'
    report_img = aklibreport_html(report_browser, report_file).report_html_screenshot()
