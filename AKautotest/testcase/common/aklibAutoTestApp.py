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
import win32api
import wx
import time
import traceback
from requests.adapters import SSLError


class AutoTestApp(wx.App):

    def __init__(self, redirect=False, filename=None, useBestVisual=False, clearSigInt=True,
                 app_title='AutoTest', modules=None, trig_stop_exec=None, stop_event=None, processes=None):
        super().__init__(redirect, filename, useBestVisual, clearSigInt)
        if not modules:
            adapter = module_case_adapter()
            self.test_modules = adapter.create_modules_dict()  # 获取用例列表，用于生成用例树
        else:
            self.test_modules = modules
        process_id = os.getpid()  # 获取当前进程 ID
        if param_get_version_branch() and param_get_rom_version() != 'unknown':
            self.app_title = f'{app_title} - {process_id} 【{param_get_version_branch()} - {param_get_rom_version()}】'
        else:
            self.app_title = f'{app_title} - {process_id}'
        # 上一次勾选的用例列表文件
        self.last_selected_case_file = (
                g_outputs_root_path +
                f'\\Temp\\LastCheckedCase_{app_title}_{param_get_model_name()}_{param_get_version_branch()}.xml')
        # 获取缩放后的分辨率
        sX = win32api.GetSystemMetrics(0)  # 获得屏幕分辨率X轴
        sY = win32api.GetSystemMetrics(1)  # 获得屏幕分辨率Y轴
        self.pane_weight = int(sX * 0.75)
        self.pane_high = int(sY * 0.68)
        self.size = (self.pane_weight, self.pane_high)
        self.SetAppName(self.app_title)
        self.frame = MainFrame(self.app_title, self.size)
        self.test_stop_thread = None
        self.test_start_thread = None
        self.wait_finish_flag = False
        self.last_checked_case_info = None
        self.modules_dict = {}
        self.devices_info = {}
        self._trig_stop_exec = trig_stop_exec
        self._stop_event = stop_event
        if processes is None:
            processes = {}
        self._processes: dict = processes
        self._debounce_later = None  # wx.CallLater对象
        self._debounce_interval = 3000  # ms，内容稳定时间

        config_ini_data = param_get_config_ini_data()
        if config_ini_data == 'unknown':
            config_ini_data = config_get_all_data_from_ini_file()
            param_put_config_ini_data(config_ini_data)

        self.default_launch_config = config_ini_data['default_launch_config']

        if not self.default_launch_config.get('email_receivers'):
            if param_get_device_config() != 'unknown':
                email_receivers = param_get_device_config().get_email_receivers()
            else:
                email_receivers = []
        else:
            email_receivers = self.default_launch_config['email_receivers'].split(';')
        self.email_receiver_text = "\n".join(email_receivers)

        # 创建左右面板窗口
        left_panel, right_panel = self.frame.split_vertical_window(sash_position=self.pane_weight * 0.42)

        # 右面板再分成上下两个面板
        upper_right_panel, lower_right_panel = self.frame.split_horizontal_panel(right_panel,
                                                                                 sash_position=self.pane_high * 0.56)

        # 右上面板再分成左右两个面板
        upper_right_left_panel, upper_right_right_panel = self.frame.split_vertical_panel(
            upper_right_panel, sash_position=self.pane_weight * 0.38)

        launch_parameters_panel1, launch_parameters_panel2 = self.frame.split_vertical_panel(
            upper_right_left_panel, sash_position=self.pane_weight * 0.19)

        # 左面板创建用例树
        test_case_static_box = wx.StaticBox(parent=left_panel, label='Test Case')
        left_panel_sizer = wx.StaticBoxSizer(test_case_static_box, wx.VERTICAL)
        self.case_tree = self.frame.create_custom_tree(left_panel)
        self.case_tree_root_node = self.frame.create_tree_root(self.case_tree, 'cases')
        self.create_case_tree_item()
        self.frame.box_sizer_add_ctrl(left_panel_sizer, self.case_tree,
                                      flag=wx.EXPAND | wx.ALL, proportion=1, border=5)

        self.frame.set_panel_sizer(left_panel, left_panel_sizer)

        # 右上左侧面板创建Test Start布局管理器
        launch_parameters_static_box1 = wx.StaticBox(parent=launch_parameters_panel1, label='Launch Parameters')
        launch_parameters_sizer1 = wx.StaticBoxSizer(launch_parameters_static_box1, wx.VERTICAL)

        launch_parameters_static_box2 = wx.StaticBox(parent=launch_parameters_panel2, label='Launch Parameters')
        launch_parameters_sizer2 = wx.StaticBoxSizer(launch_parameters_static_box2, wx.VERTICAL)

        # Test Rounds输入框
        right_panel_h_sizer_test_rounds = self.frame.create_horizontal_box_sizer()
        self.test_rounds_static_text_ctrl = wx.StaticText(parent=launch_parameters_panel1, label='Test Rounds: ')
        self.test_rounds_text_ctrl = wx.TextCtrl(parent=launch_parameters_panel1)
        self.test_rounds_text_ctrl.SetValue(self.default_launch_config.get('test_rounds', '1'))  # 设置默认值1
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_test_rounds, self.test_rounds_static_text_ctrl,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_test_rounds, self.test_rounds_text_ctrl,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer1, right_panel_h_sizer_test_rounds,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        test_rounds_tooltip = wx.ToolTip('如果test_rounds>1表示测试多轮，'
                                         '每一轮测试完成后都会发送邮件或者企业微信通知（如果有勾选的话），'
                                         '可以再设置test_times或者test_counts（一般二选一即可），'
                                         '总计执行次数为test_rounds*test_times*test_counts。')
        self.test_rounds_static_text_ctrl.SetToolTip(test_rounds_tooltip)

        # Test Times输入框
        right_panel_h_sizer_test_times = self.frame.create_horizontal_box_sizer()
        self.test_times_static_text_ctrl = wx.StaticText(parent=launch_parameters_panel1, label='Test Times: ')
        self.test_times_text_ctrl = wx.TextCtrl(parent=launch_parameters_panel1)
        self.test_times_text_ctrl.SetValue(self.default_launch_config.get('test_times', '1'))  # 设置默认值1
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_test_times, self.test_times_static_text_ctrl,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_test_times, self.test_times_text_ctrl,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer1, right_panel_h_sizer_test_times,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        test_times_tooltip = wx.ToolTip('如果 test_rounds>1 并且 test_times>1，表示测试多轮，'
                                        '每一轮测试完成后都会发送邮件或者企业微信通知（如果有勾选的话），'
                                        'test_times表示每一轮执行多少遍，'
                                        '总计执行次数为test_times*test_rounds。'
                                        '也可以单独设置test_times>1，适合多个用例循环测试。')
        self.test_times_static_text_ctrl.SetToolTip(test_times_tooltip)

        # Test Counts输入框
        right_panel_h_sizer_test_counts = self.frame.create_horizontal_box_sizer()
        self.test_counts_static_text_ctrl = wx.StaticText(parent=launch_parameters_panel1, label='Test Counts: ')
        self.test_counts_text_ctrl = wx.TextCtrl(parent=launch_parameters_panel1)
        self.test_counts_text_ctrl.SetValue(self.default_launch_config.get('test_counts', '1'))  # 设置默认值1
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_test_counts, self.test_counts_static_text_ctrl,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_test_counts, self.test_counts_text_ctrl,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer1, right_panel_h_sizer_test_counts,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        test_counts_tooltip = wx.ToolTip('如果设置test_counts>1并且test_times=1，'
                                         '选择多个用例，会一个用例模块执行多遍后再执行另一个用例。'
                                         '如果想要一遍执行多个用例，然后执行多遍，可以同时或单独设置test_times>1。'
                                         '如果是单个用例模块执行多遍，设置test_counts即可。'
                                         '如果设置test_counts>1，则所有用例执行的测试测试都由该配置项指定，'
                                         '否则会按照测试套件指定用例的测试次数。')
        self.test_counts_static_text_ctrl.SetToolTip(test_counts_tooltip)

        # Retry Counts重试次数输入框
        right_panel_h_sizer_retry_counts = self.frame.create_horizontal_box_sizer()
        self.retry_counts_static_text_ctrl = wx.StaticText(parent=launch_parameters_panel1, label='Retry Counts: ')
        self.retry_counts_text_ctrl = wx.TextCtrl(parent=launch_parameters_panel1)
        self.retry_counts_text_ctrl.SetValue(self.default_launch_config.get('retry_counts', '0'))  # 设置默认值0
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_retry_counts, self.retry_counts_static_text_ctrl,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_retry_counts, self.retry_counts_text_ctrl,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer1, right_panel_h_sizer_retry_counts,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        retry_counts_tooltip = wx.ToolTip('Retry Counts表示测试失败重测次数，默认为0，表示不进行失败重测')
        self.retry_counts_static_text_ctrl.SetToolTip(retry_counts_tooltip)

        # Report Type下拉框
        right_panel_h_sizer_report_type = self.frame.create_horizontal_box_sizer()
        self.report_type_static_text = wx.StaticText(parent=launch_parameters_panel1, label='Report Type: ')
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_report_type, self.report_type_static_text,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        report_type_list = ['HTML', 'HTML+Console']
        self.report_type_combo_box = wx.ComboBox(parent=launch_parameters_panel1, choices=report_type_list)
        self.report_type_combo_box.SetStringSelection(self.default_launch_config.get('report_type', 'HTML+Console'))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_report_type, self.report_type_combo_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer1, right_panel_h_sizer_report_type,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        report_type_tooltip = wx.ToolTip('两种方式都会生成HTML报告，'
                                         'HTML+Console方式会在用例执行同时将log输出到控制台，便于调试。'
                                         'HTML方式在用例执行时，过程的log不会输出到控制台，只显示用例标题和结果。'
                                         '执行过程中可以切换，在下一个用例执行时开始起作用。')
        self.report_type_static_text.SetToolTip(report_type_tooltip)

        # Run Time 设置开始执行时间
        right_panel_h_sizer_run_time = self.frame.create_horizontal_box_sizer()
        self.run_time_static_text_ctrl = wx.StaticText(parent=launch_parameters_panel1, label='Run Time: ')
        self.run_time_text_ctrl = wx.TextCtrl(parent=launch_parameters_panel1)
        self.run_time_text_ctrl.SetValue('')
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_run_time, self.run_time_static_text_ctrl,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_run_time, self.run_time_text_ctrl,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer1, right_panel_h_sizer_run_time,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        run_time_tooltip = wx.ToolTip('Run Time可以设置等待时间到才开始执行，格式为HH:mm，比如21:00或者21:30:00')
        self.run_time_static_text_ctrl.SetToolTip(run_time_tooltip)

        # # Save Last Try勾选框，是否只保存最后一次重试结果到测试报告
        # right_panel_h_sizer_save_last_try = self.frame.create_horizontal_box_sizer()
        # self.save_last_try_check_box = wx.CheckBox(parent=launch_parameters_panel1,
        #                                            label='Save Last Try')
        # self.save_last_try_check_box.SetValue(
        #     self.get_check_type_by_bool(self.default_launch_config.get('save_last_try', True)))
        # self.frame.box_sizer_add_ctrl(right_panel_h_sizer_save_last_try, self.save_last_try_check_box,
        #                               flag=wx.ALL | wx.FIXED_MINSIZE)
        # self.frame.box_sizer_add_ctrl(launch_parameters_sizer1, right_panel_h_sizer_save_last_try,
        #                               flag=wx.ALL | wx.FIXED_MINSIZE, border=5)

        # Failed to Notification勾选框，是否测试失败就直接退出
        right_panel_h_sizer_failed_to_notification = self.frame.create_horizontal_box_sizer()
        self.failed_to_notification_check_box = wx.CheckBox(parent=launch_parameters_panel1,
                                                            label='Failed to Notification')
        self.failed_to_notification_check_box.SetValue(
            self.get_check_type_by_bool(self.default_launch_config.get('failed_to_notification', False)))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_failed_to_notification, self.failed_to_notification_check_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer1, right_panel_h_sizer_failed_to_notification,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        failed_to_notification_tooltip = wx.ToolTip('Failed to Notification 勾选表示测试失败时会发送邮件或者企业微信通知。'
                                                    '主要用于压测时，可以及时收到通知然后确认情况。')
        self.failed_to_notification_check_box.SetToolTip(failed_to_notification_tooltip)

        # Failed to Exit勾选框，是否测试失败就直接退出
        right_panel_h_sizer_failed_to_exit = self.frame.create_horizontal_box_sizer()
        self.failed_to_exit_check_box = wx.CheckBox(parent=launch_parameters_panel1,
                                                    label='Failed To Exit')
        self.failed_to_exit_check_box.SetValue(
            self.get_check_type_by_bool(self.default_launch_config.get('failed_to_exit', False)))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_failed_to_exit, self.failed_to_exit_check_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer1, right_panel_h_sizer_failed_to_exit,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        failed_to_exit_tooltip = wx.ToolTip('Failed to Exit 勾选表示测试失败时会发送邮件或者企业微信后直接退出测试。')
        self.failed_to_exit_check_box.SetToolTip(failed_to_exit_tooltip)

        # Pause During Nap Time勾选框，是否在午睡时间暂停执行
        if not g_nap_time_range:
            nap_start_time = config_get_value_from_ini_file('config', 'nap_start_time')
            nap_stop_time = config_get_value_from_ini_file('config', 'nap_stop_time')
            g_nap_time_range.append(nap_start_time)
            g_nap_time_range.append(nap_stop_time)
        right_panel_h_sizer_pause_during_nap_time = self.frame.create_horizontal_box_sizer()
        scheduled_execution_enable = config_get_value_from_ini_file(
            'config', 'scheduled_execution_enable')
        if scheduled_execution_enable:
            param_put_scheduled_execution_enable(scheduled_execution_enable)
            self.pause_during_nap_time_check_box = wx.CheckBox(parent=launch_parameters_panel1,
                                                               label='Scheduled Execution Enable')
            self.pause_during_nap_time_check_box.SetValue(
                self.get_check_type_by_bool(scheduled_execution_enable))
            pause_during_nap_time_tooltip = wx.ToolTip('Scheduled Execution Enable定时执行勾选之后，在时间段（%s-%s）内会暂停执行，'
                                                       '直到暂停结束再继续，可以手动点击Resume恢复执行，'
                                                       '但如果仍勾选了定时执行，下一个用例执行时仍会判断是否处于定时执行暂停阶段会继续暂停，'
                                                       '如果想要不再暂停，可以取消勾选定时执行，再点Resume按钮'
                                                       % (g_nap_time_range[0], g_nap_time_range[1]))
        else:
            self.pause_during_nap_time_check_box = wx.CheckBox(parent=launch_parameters_panel1,
                                                               label='Pause During Nap Time')
            self.pause_during_nap_time_check_box.SetValue(
                self.get_check_type_by_bool(self.default_launch_config.get('pause_during_nap_time_enable', True)))
            pause_during_nap_time_tooltip = wx.ToolTip('Pause During Nap Time午休暂停勾选之后，在午休时间段（%s-%s）内会暂停执行，'
                                                       '直到午休结束再继续，可以手动点击Resume恢复执行，'
                                                       '但如果仍勾选了午休暂停，下一个用例执行时仍会判断是否处于午休时间会继续暂停，'
                                                       '如果想要不再午休暂停，可以取消勾选午休暂停，再点Resume按钮'
                                                       % (g_nap_time_range[0], g_nap_time_range[1]))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_pause_during_nap_time, self.pause_during_nap_time_check_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer1, right_panel_h_sizer_pause_during_nap_time,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        self.pause_during_nap_time_check_box.SetToolTip(pause_during_nap_time_tooltip)

        # Test Random勾选框
        right_panel_h_sizer_test_random = self.frame.create_horizontal_box_sizer()
        self.test_random_check_box = wx.CheckBox(parent=launch_parameters_panel2, label='Test Random')
        self.test_random_check_box.SetValue(
            self.get_check_type_by_bool(self.default_launch_config.get('test_random', False)))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_test_random, self.test_random_check_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer2, right_panel_h_sizer_test_random,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        test_random_tooltip = wx.ToolTip('勾选表示将用例类打乱顺序执行，如果压测Test Counts大于1，'
                                         '并且同时勾选Exec one case to report，'
                                         '则用例类里面的用例也将随机顺序执行，需要要保证每条用例独立互不影响和依赖')
        self.test_random_check_box.SetToolTip(test_random_tooltip)

        # Exec one case to report勾选框
        right_panel_h_sizer_exec_one_case_to_report = self.frame.create_horizontal_box_sizer()
        self.exec_one_case_to_report_check_box = wx.CheckBox(parent=launch_parameters_panel2,
                                                             label='Exec one case to report')
        self.exec_one_case_to_report_check_box.SetValue(
            self.get_check_type_by_bool(self.default_launch_config.get('exec_one_case_to_report', False)))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_exec_one_case_to_report,
                                      self.exec_one_case_to_report_check_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer2, right_panel_h_sizer_exec_one_case_to_report,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        exec_one_case_to_report_tooltip = wx.ToolTip('是否单个用例执行完就写入测试报告，'
                                                     '不勾选表示整个用例类执行完才写入测试报告，适用于功能测试；'
                                                     '勾选表示单个用例执行完就写入测试报告，适用于压测，如果同时勾选Failed To Exit，'
                                                     '可以实现用例执行出错立即退出，不会等到该用例类所有用例都执行完才退出；'
                                                     '最好在压测用例添加unittest_exec_sc_and_tc_only_once装饰器配合使用。')
        self.exec_one_case_to_report_check_box.SetToolTip(exec_one_case_to_report_tooltip)

        # Send Email勾选框
        right_panel_h_sizer_send_email = self.frame.create_horizontal_box_sizer()
        self.send_email_check_box = wx.CheckBox(parent=launch_parameters_panel2, label='Send Email')
        self.send_email_check_box.SetValue(
            self.get_check_type_by_bool(self.default_launch_config.get('send_email_enable', False)))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_send_email, self.send_email_check_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer2, right_panel_h_sizer_send_email,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        send_email_tooltip = wx.ToolTip('勾选后，右边的Email Receivers将显示默认发送邮件人员，可以进行更改，'
                                        '同时也会自动勾选发送测试结果到汇总服务器')
        self.send_email_check_box.SetToolTip(send_email_tooltip)

        # Send work_weixin勾选框
        right_panel_h_sizer_send_work_weixin = self.frame.create_horizontal_box_sizer()
        self.send_work_weixin_check_box = wx.CheckBox(parent=launch_parameters_panel2, label='Send Work Weixin')
        self.send_work_weixin_check_box.SetValue(
            self.get_check_type_by_bool(self.default_launch_config.get('send_work_weixin_enable', False)))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_send_work_weixin, self.send_work_weixin_check_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer2, right_panel_h_sizer_send_work_weixin,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        send_work_weixin_tooltip = wx.ToolTip('勾选后，右边的Email Receivers将显示默认发送人员，'
                                              '会根据人员邮箱获取企业微信机器人ID进行发送，可以进行更改，'
                                              '同时也会自动勾选发送测试结果到汇总服务器\n'
                                              '企业微信添加机器人步骤：任意拉两个人建立一个群聊，然后踢掉，'
                                              '这样就可以创建一个只有一个人的群聊，之后添加机器人，并获取webhook链接中的key值，'
                                              '然后添加robot_info.ini文件里')
        self.send_work_weixin_check_box.SetToolTip(send_work_weixin_tooltip)

        # 发送测试结果到汇总服务器勾选框
        right_panel_h_sizer_send_test_results = self.frame.create_horizontal_box_sizer()
        self.send_test_results_check_box = wx.CheckBox(parent=launch_parameters_panel2,
                                                       label='Send Test Results To Server')
        self.send_test_results_check_box.SetValue(
            self.get_check_type_by_bool(self.default_launch_config.get('send_test_results_summary_enable', False)))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_send_test_results, self.send_test_results_check_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer2, right_panel_h_sizer_send_test_results,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        send_test_results_tooltip = wx.ToolTip('勾选后会发送测试结果到汇总服务器')
        self.send_test_results_check_box.SetToolTip(send_test_results_tooltip)

        # 是否启用浏览器无头模式勾选框
        right_panel_h_sizer_browser_headless_enable = self.frame.create_horizontal_box_sizer()
        self.browser_headless_enable_check_box = wx.CheckBox(parent=launch_parameters_panel2,
                                                             label='Enable Browser Headless')
        self.browser_headless_enable_check_box.SetValue(
            self.get_check_type_by_bool(self.default_launch_config.get('browser_headless_enable', True)))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_browser_headless_enable,
                                      self.browser_headless_enable_check_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer2, right_panel_h_sizer_browser_headless_enable,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        browser_headless_enable_tooltip = wx.ToolTip('勾选表示浏览器将使用无头模式，在后台运行')
        self.browser_headless_enable_check_box.SetToolTip(browser_headless_enable_tooltip)

        # 是否跳过下载升级包勾选框
        right_panel_h_sizer_skip_download_firmware = self.frame.create_horizontal_box_sizer()
        self.skip_download_firmware_check_box = wx.CheckBox(parent=launch_parameters_panel2,
                                                            label='Skip Download Firmware')
        self.skip_download_firmware_check_box.SetValue(
            self.get_check_type_by_bool(self.default_launch_config.get('skip_download_firmware', True)))
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_skip_download_firmware, self.skip_download_firmware_check_box,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer2, right_panel_h_sizer_skip_download_firmware,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)
        skip_download_firmware_tooltip = wx.ToolTip('勾选表示跳过下载升级包，如果有需要进行相关升级测试，最好不要跳过，'
                                                    '可能会导致升级测试失败')
        self.skip_download_firmware_check_box.SetToolTip(skip_download_firmware_tooltip)

        # Start和Stop按钮
        right_panel_h_sizer_start_and_stop = self.frame.create_horizontal_box_sizer()
        self.start_button = wx.Button(parent=launch_parameters_panel2, label='Start')
        self.pause_button = wx.Button(parent=launch_parameters_panel2, label='Pause')
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_start_and_stop, self.start_button,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(right_panel_h_sizer_start_and_stop, self.pause_button,
                                      flag=wx.ALL | wx.FIXED_MINSIZE)
        self.frame.box_sizer_add_ctrl(launch_parameters_sizer2, right_panel_h_sizer_start_and_stop,
                                      flag=wx.ALL | wx.FIXED_MINSIZE, border=5)

        self.frame.set_panel_sizer(launch_parameters_panel1, launch_parameters_sizer1)  # 将垂直布局管理器添加到右边面板
        self.frame.set_panel_sizer(launch_parameters_panel2, launch_parameters_sizer2)  # 将垂直布局管理器添加到右边面板

        # 右上的右边面板，设备列表
        device_list_static_box = wx.StaticBox(parent=upper_right_right_panel, label='Device List')
        upper_right_right_panel_sizer = wx.StaticBoxSizer(device_list_static_box, wx.VERTICAL)
        self.device_list_tree = self.frame.create_custom_tree(upper_right_right_panel)
        self.device_list_tree_root_node = self.frame.create_tree_root(self.device_list_tree, 'devices')
        self.frame.box_sizer_add_ctrl(upper_right_right_panel_sizer, self.device_list_tree,
                                      flag=wx.EXPAND | wx.ALL, proportion=1, border=5)
        self.frame.set_panel_sizer(upper_right_right_panel, upper_right_right_panel_sizer)

        # 右下面板，再分为左右两个面板
        lower_right_left_panel, lower_right_right_panel = self.frame.split_vertical_panel(
            lower_right_panel, sash_position=self.pane_weight * 0.38)

        # 右下面板，Case Selected文本框
        case_selected_static_box = wx.StaticBox(parent=lower_right_left_panel, label='Case Selected')
        lower_launch_parameters_sizer1 = wx.StaticBoxSizer(case_selected_static_box, wx.VERTICAL)
        self.case_selected_text_ctrl = wx.TextCtrl(lower_right_left_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        lower_launch_parameters_sizer1.Add(self.case_selected_text_ctrl, 1, flag=wx.EXPAND | wx.ALL, border=5)
        self.frame.set_panel_sizer(lower_right_left_panel, lower_launch_parameters_sizer1)

        # 右下的右下面板，Email list文本框，可以输入修改
        email_receivers_static_box = wx.StaticBox(parent=lower_right_right_panel, label='Email Receivers')
        upper_right_right_lower_panel_v_sizer = wx.StaticBoxSizer(email_receivers_static_box, wx.VERTICAL)
        self.email_list_static_text = wx.TextCtrl(lower_right_right_panel, style=wx.TE_MULTILINE)
        upper_right_right_lower_panel_v_sizer.Add(self.email_list_static_text, 1, flag=wx.EXPAND | wx.ALL, border=5)
        self.frame.set_panel_sizer(lower_right_right_panel, upper_right_right_lower_panel_v_sizer)

        # 默认勾选时，也要设置邮件发送人员列表
        self.params_default_setting()

        self.get_checked_modules_dict()
        # 绑定事件
        self.frame.event_tree_item_checked(self.case_tree, self.case_tree_checked_item)
        self.frame.event_tree_item_checked(self.device_list_tree, self.device_list_tree_checked_item)
        self.frame.event_button(self.start_test, self.start_button)
        self.frame.event_button(self.pause_test, self.pause_button)
        self.frame.event_check_box(self.checked_send_email, self.send_email_check_box)
        self.frame.event_check_box(self.checked_send_work_weixin, self.send_work_weixin_check_box)
        self.frame.event_check_box(self.get_pause_during_nap_time_state, self.pause_during_nap_time_check_box)
        self.frame.event_select_combo_box(self.get_report_type, self.report_type_combo_box)
        self.frame.event_check_box(self.get_failed_to_exit_state, self.failed_to_exit_check_box)
        self.frame.event_check_box(self.get_failed_to_notification_state, self.failed_to_notification_check_box)
        self.frame.event_check_box(self.get_send_test_results_state, self.send_test_results_check_box)
        self.frame.event_text(self.on_email_list_text_change, self.email_list_static_text)

        # 配置项说明显示
        self.frame.event_enter_window(self.view_start_btn_description,
                                      self.start_button)
        self.frame.event_enter_window(self.view_pause_btn_description,
                                      self.pause_button)

        self.frame.event_close(self.on_close)

        if not self._trig_stop_exec and isinstance(param_get_excel_data(), dict):
            device_list = param_get_excel_data().get('device_info')
            if device_list:
                self.create_device_tree_item(device_list)
        time.sleep(1)
        self.show_foreground()

    # region 界面初始化、关闭

    def show_foreground(self):
        """显示并前置窗口"""
        self.frame.Show()
        self.frame.Raise()

    def on_close(self, event):
        if not event:
            return
        if self._processes:
            dialog = wx.MessageDialog(
                None,
                '当前有子进程在运行，选择否将等待子进程结束，选择是将强制关闭',
                "确认退出",
                wx.YES_NO | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_QUESTION
            )
        else:
            if param_get_running_state():
                dialog_text = '当前有测试正在执行，选择否将等待当前用例执行完成，选择是将强制关闭'
            else:
                dialog_text = '是否关闭退出执行？'
            dialog = wx.MessageDialog(
                None,
                dialog_text,
                "确认退出",
                wx.YES_NO | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_QUESTION
            )

        result = dialog.ShowModal()
        dialog.Destroy()

        if result == wx.ID_YES:
            self.force_close()
            exit(0)
        elif result == wx.ID_NO:
            if self._processes:
                self.wait_for_processes_to_finish()
            elif param_get_running_state():
                param_put_stop_exec_enable(True)
                self.start_button.SetLabel('Resume')
                self.wait_case_exec_finish()
            else:
                if event.CanVeto():
                    event.Veto()
        elif result == wx.ID_CANCEL:
            if event.CanVeto():
                event.Veto()

    def wait_case_exec_finish(self, timeout=600):
        thread = threading.Thread(target=self._thread_wait_case_exec_finish, args=(timeout,))
        thread.daemon = True
        thread.start()

    def _thread_wait_case_exec_finish(self, timeout=600):
        """等待用例执行完成，Resume按钮变成Start"""
        end_time = time.time() + timeout
        while True:
            if self.start_button.GetLabel() == 'Start':
                aklog_info('测试完成，退出')
                break
            elif time.time() > end_time:
                aklog_warn(f'等待 {timeout} 秒后仍为执行完成，强制关闭')
                break
            time.sleep(3)
            continue
        time.sleep(2)
        wx.CallAfter(self.Destroy)

    def wait_for_processes_to_finish(self):
        aklog_info()
        if self._stop_event:
            self._stop_event.set()

        thread = threading.Thread(target=self.thread_wait_for_processes_to_finish)
        thread.daemon = True
        thread.start()

    def thread_wait_for_processes_to_finish(self):
        aklog_warn('准备停止，设备列表全部取消勾选')
        self.uncheck_all_device()

        wait_threads = []
        for name, process in list(self._processes.items()):
            thread = threading.Thread(target=self.wait_for_process, args=(process,))
            thread.daemon = True
            wait_threads.append(thread)
            thread.start()

        for thread in wait_threads:
            thread.join()

        time.sleep(2)
        wx.CallAfter(self.Destroy)

    @staticmethod
    def wait_for_process(process):
        if process.is_alive():
            aklog_printf(f"Waiting for process {process.pid} to stop")
            process.join(timeout=600)  # Wait for the process to finish
        else:
            aklog_printf(f"process {process.pid} is stopped")
            return

        if process.is_alive():
            aklog_printf(f"Force terminating process {process.pid}")
            process.terminate()
            process.join(timeout=1)

    @staticmethod
    def terminate_all_child_processes():
        parent_pid = os.getpid()
        parent = psutil.Process(parent_pid)
        children = parent.children(recursive=True)
        if not children:
            return
        for child in children:
            aklog_printf(f"Terminating child process ID: {child.pid}")
            child.terminate()
        gone, still_alive = psutil.wait_procs(children, timeout=1)
        for p in still_alive:
            aklog_printf(f"Killing child process ID: {p.pid}")
            p.kill()

    def force_close(self):
        aklog_info()
        try:
            if self._stop_event:
                self._stop_event.set()

            # Force terminate all processes
            for name, process in list(self._processes.items()):
                if process.is_alive():
                    aklog_printf(f"Force terminating process {process.pid}")
                    process.terminate()
                    process.join(timeout=1)
            self._processes.clear()  # Clear the process list

            self.terminate_all_child_processes()
        except Exception as e:
            aklog_printf(f"Exception occurred while force closing: {e}")

    @staticmethod
    def get_check_type_by_bool(value):
        """根据传入的bool类型来获取复选框的状态类型"""
        if value is True:
            check_type = bool(wx.CHK_CHECKED)
        else:
            check_type = bool(wx.CHK_UNCHECKED)
        return check_type

    # endregion

    # region 配置项参数设置

    def get_test_counts(self):
        test_counts = self.frame.get_text_by_ctrl(self.test_counts_text_ctrl)  # 获取输入框的测试次数
        param_put_test_counts(int(test_counts))
        return int(test_counts)

    def get_test_times(self):
        test_times = self.frame.get_text_by_ctrl(self.test_times_text_ctrl)  # 获取输入框的测试次数
        param_put_test_times(int(test_times))
        return int(test_times)

    def get_test_rounds(self):
        test_rounds = self.frame.get_text_by_ctrl(self.test_rounds_text_ctrl)  # 获取输入框的测试轮次
        param_put_test_rounds(int(test_rounds))
        return int(test_rounds)

    def get_skip_download_firmware_state(self):
        state = self.frame.get_checkbox_state_by_ctrl(self.skip_download_firmware_check_box)  # 获取勾选框状态，返回True或False
        aklog_info(f'param_put_skip_download_firmware_state: {state}')
        param_put_skip_download_firmware_state(state)
        return state

    def get_send_email_state(self, event=None):
        state = self.frame.get_checkbox_state_by_ctrl(self.send_email_check_box)
        if event:
            aklog_info(f'param_put_send_email_state: {state}')
            param_put_send_email_state(state)
        return state

    def get_send_work_weixin_state(self, event=None):
        state = self.frame.get_checkbox_state_by_ctrl(self.send_work_weixin_check_box)
        if event:
            aklog_info(f'param_put_send_work_weixin_state: {state}')
            param_put_send_work_weixin_state(state)
        return state

    def get_send_test_results_state(self, event=None):
        state = self.frame.get_checkbox_state_by_ctrl(self.send_test_results_check_box)
        if event:
            aklog_info(f'param_put_send_test_results_summary_enable: {state}')
            param_put_send_test_results_summary_enable(state)
        return state

    def get_email_receivers(self):
        email_receiver = self.email_list_static_text.GetValue()
        if not email_receiver:
            return
        email_receiver = (email_receiver.replace(';', '')
                          .replace('；', '').replace(',', ''))
        email_receiver = email_receiver.lower()
        # 如果有修改收件人列表，需要保存最后修改的内容
        if email_receiver and email_receiver != self.email_receiver_text:
            self.email_receiver_text = email_receiver
        email_receivers = email_receiver.split('\n')
        email_receivers_new = []
        for x in email_receivers:
            if x and x.strip():
                email_receivers_new.append(x.strip())
        aklog_printf('email_receivers: %s' % email_receivers_new)
        param_put_email_receivers(email_receivers_new)

    def get_test_random_state(self):
        state = self.frame.get_checkbox_state_by_ctrl(self.test_random_check_box)
        param_put_test_random_state(state)

    def get_browser_headless_enable_state(self):
        state = self.frame.get_checkbox_state_by_ctrl(self.browser_headless_enable_check_box)
        param_put_browser_headless_enable(state)

    def get_exec_one_case_to_report_enable(self):
        state = self.frame.get_checkbox_state_by_ctrl(self.exec_one_case_to_report_check_box)
        param_put_exec_one_case_to_report_enable(state)

    def get_report_type(self, event=None):
        report_type = self.frame.get_combo_box_selected_by_ctrl(self.report_type_combo_box)
        if event:
            aklog_info('param_put_report_type: %s' % report_type)
            param_put_report_type(report_type)
        return report_type

    def get_retry_counts(self):
        retry_counts = self.frame.get_text_by_ctrl(self.retry_counts_text_ctrl)  # 获取输入框的重测次数
        param_put_retry_counts(int(retry_counts))

    def get_save_last_try_state(self):
        # state = self.frame.get_checkbox_state_by_ctrl(self.save_last_try_check_box)  # 获取勾选框状态，返回True或False
        state = self.default_launch_config.get('save_last_try', True)
        param_put_save_last_try_state(state)

    def get_failed_to_exit_state(self, event=None):
        state = self.frame.get_checkbox_state_by_ctrl(self.failed_to_exit_check_box)  # 获取勾选框状态，返回True或False
        if event:
            param_put_failed_to_exit_enable(state)
        return state

    def get_failed_to_notification_state(self, event=None):
        state = self.frame.get_checkbox_state_by_ctrl(self.failed_to_notification_check_box)  # 获取勾选框状态，返回True或False
        if event:
            param_put_failed_to_notification_enable(state)
        return state

    def get_pause_during_nap_time_state(self, event=None):
        state = self.frame.get_checkbox_state_by_ctrl(
            self.pause_during_nap_time_check_box)  # 获取勾选框状态，返回True或False
        if event:
            # 如果config.ini配置文件里开启定时执行，午休暂停功能将被替换为定时执行
            scheduled_execution_enable = config_get_value_from_ini_file(
                'config', 'scheduled_execution_enable')
            if scheduled_execution_enable:
                param_put_scheduled_execution_enable(state)
            else:
                param_put_pause_during_nap_time_enable(state)
        return state

    def get_run_time(self):
        return self.frame.get_text_by_ctrl(self.run_time_text_ctrl)  # 获取输入框的开始执行时间

    def checked_send_email(self, event=None):
        """勾选触发显示邮件接收人员列表"""
        send_email_state = self.get_send_email_state(event)
        if send_email_state:
            email_receiver = self.email_receiver_text
        else:
            email_receiver = """"""
        self.email_list_static_text.SetValue(email_receiver)
        # 启动后再勾选，也要获取下收件人列表
        self.get_email_receivers()
        # 勾选发送邮件，同时自动勾选发送测试结果到服务器
        if event and not param_get_running_state():
            if send_email_state:
                self.send_test_results_check_box.SetValue(bool(wx.CHK_CHECKED))
                self.report_type_combo_box.SetStringSelection('HTML')
            else:
                self.send_test_results_check_box.SetValue(bool(wx.CHK_UNCHECKED))
                self.report_type_combo_box.SetStringSelection('HTML+Console')

            if (self.frame.get_combo_box_selected_by_ctrl(self.report_type_combo_box) !=
                    param_get_report_type()):
                self.get_report_type(True)

            if (self.frame.get_checkbox_state_by_ctrl(self.send_test_results_check_box) !=
                    param_get_send_test_results_summary_enable()):
                self.get_send_test_results_state(True)

    def checked_send_work_weixin(self, event=None):
        """勾选触发显示邮件接收人员列表"""
        send_work_weixin_state = self.get_send_work_weixin_state(event)
        if send_work_weixin_state:
            email_receiver = self.email_receiver_text
        else:
            email_receiver = """"""
        self.email_list_static_text.SetValue(email_receiver)
        # 启动后再勾选，也要获取下收件人列表
        self.get_email_receivers()
        # 勾选发送邮件，同时自动勾选发送测试结果到服务器
        if event and not param_get_running_state():
            if send_work_weixin_state:
                self.send_test_results_check_box.SetValue(bool(wx.CHK_CHECKED))
                self.report_type_combo_box.SetStringSelection('HTML')
            else:
                self.send_test_results_check_box.SetValue(bool(wx.CHK_UNCHECKED))
                self.report_type_combo_box.SetStringSelection('HTML+Console')

            if (self.frame.get_combo_box_selected_by_ctrl(self.report_type_combo_box) !=
                    param_get_report_type()):
                self.get_report_type(True)

            if (self.frame.get_checkbox_state_by_ctrl(self.send_test_results_check_box) !=
                    param_get_send_test_results_summary_enable()):
                self.get_send_test_results_state(True)

    def params_default_setting(self):
        send_email_state = self.frame.get_checkbox_state_by_ctrl(self.send_email_check_box)
        if send_email_state:
            self.checked_send_email(True)
        send_work_weixin_state = self.frame.get_checkbox_state_by_ctrl(self.send_work_weixin_check_box)
        if send_work_weixin_state:
            self.checked_send_work_weixin(True)

        if (self.frame.get_combo_box_selected_by_ctrl(self.report_type_combo_box) !=
                param_get_report_type()):
            self.get_report_type(True)

        if (self.frame.get_checkbox_state_by_ctrl(self.send_test_results_check_box) !=
                param_get_send_test_results_summary_enable()):
            self.get_send_test_results_state(True)

        if (self.frame.get_checkbox_state_by_ctrl(self.failed_to_exit_check_box) !=
                param_get_failed_to_exit_enable()):
            self.get_failed_to_exit_state(True)

        if (self.frame.get_checkbox_state_by_ctrl(self.failed_to_notification_check_box) !=
                param_get_failed_to_notification_enable()):
            self.get_failed_to_notification_state(True)

        if (self.frame.get_checkbox_state_by_ctrl(self.pause_during_nap_time_check_box) !=
                param_get_pause_during_nap_time_enable()):
            self.get_pause_during_nap_time_state(True)

    def on_email_list_text_change(self, event=None):
        """
        文本内容变更事件处理，重置防抖定时器
        Args:
            event: wx.EVT_TEXT事件对象
        """
        if not event:
            return
        # 每次内容变更都重置延迟回调
        if self._debounce_later:
            self._debounce_later.Stop()
        self._debounce_later = wx.CallLater(
            self._debounce_interval, self.on_email_list_stable)

    def on_email_list_stable(self):
        current_value = self.email_list_static_text.GetValue()
        if current_value != self.email_receiver_text:
            self.get_email_receivers()

    # endregion

    # region Device List设备列表
    def get_current_device_names(self, root):
        device_names = []
        item, cookie = self.device_list_tree.GetFirstChild(root)
        while item and item.IsOk():
            device_names.append(self.device_list_tree.GetItemText(item).split(' ')[0])  # 获取设备名称
            item, cookie = self.device_list_tree.GetNextChild(root, cookie)
        return device_names

    def create_device_tree_item(self, devices_info):
        """生成设备列表树"""
        try:
            if isinstance(devices_info, dict):
                self.devices_info = devices_info
                aklog_info(self.devices_info)
                device_status_map = {'unused': '未使用',
                                     'used': '测试中'}
                # 移除不存在的设备
                all_device_list = self.get_all_device_list()
                for device_name in all_device_list:
                    if device_name not in self.devices_info:
                        device_node = self.device_list_tree.FindItem(self.device_list_tree_root_node, device_name)
                        aklog_info('delete: %s' % device_name)
                        self.device_list_tree.Delete(device_node)

                current_device_names = self.get_current_device_names(self.device_list_tree_root_node)

                # 新增设备
                for device_name in sorted(self.devices_info.keys()):
                    device_node = self.device_list_tree.FindItem(self.device_list_tree_root_node, device_name)
                    if device_name in device_node.GetText():
                        continue
                    device_status = self.devices_info[device_name].get('status')
                    if device_status and device_status_map.get(device_status):
                        device_node_text = device_name + ' (%s)' % device_status_map.get(device_status)
                    else:
                        device_node_text = device_name

                    # 找到插入位置
                    insert_index = None
                    for i, name in enumerate(current_device_names):
                        if device_name < name:
                            insert_index = i
                            break
                    if insert_index is None:
                        insert_index = len(current_device_names)

                    # 插入设备节点
                    if insert_index < len(current_device_names):
                        device_node = self.frame.create_tree_item_before(
                            self.device_list_tree, self.device_list_tree_root_node, insert_index, device_node_text)
                    else:
                        device_node = self.frame.create_tree_item(
                            self.device_list_tree, self.device_list_tree_root_node, device_node_text)

                    self.device_list_tree.CheckItem(device_node, True)
                self.device_list_tree.Expand(self.device_list_tree_root_node)
            elif isinstance(devices_info, list):
                # 普通测试显示device_info的设备名称
                self.device_list_tree.SetItemText(self.device_list_tree_root_node, 'Devices(只是展示)')
                for device_info in devices_info:
                    device_name = device_info.get('device_name')
                    if device_name:
                        ip = device_info.get('ip')
                        model = device_info.get('model')
                        if ip and model:
                            device_node = self.frame.create_tree_item(
                                self.device_list_tree, self.device_list_tree_root_node,
                                f'{device_name}【{model}】【{ip}】')
                        elif ip:
                            device_node = self.frame.create_tree_item(
                                self.device_list_tree, self.device_list_tree_root_node,
                                f'{device_name}【{ip}】')
                        elif device_info.get('deviceid'):
                            device_node = self.frame.create_tree_item(
                                self.device_list_tree, self.device_list_tree_root_node,
                                f'{device_name}【{device_info.get("deviceid")}】')
                        else:
                            device_node = self.frame.create_tree_item(
                                self.device_list_tree, self.device_list_tree_root_node, device_name)
                        self.device_list_tree.CheckItem(device_node, True)
                self.device_list_tree.Expand(self.device_list_tree_root_node)
        except:
            aklog_error(traceback.format_exc())

    def device_list_tree_checked_item(self, event=None):
        """
        勾选树节点触发执行，只要树控件中的任意一个复选框状态有变化就会响应这个函数
        勾选时会把所有的子节点都同时勾选
        """
        self.frame.checked_item(self.device_list_tree, event)
        item = event.GetItem()
        if item:
            if self._trig_stop_exec and not self.device_list_tree.IsItemChecked(item):
                self._trig_stop_exec()

    def set_device_node_status(self, device_text, new_text):
        aklog_debug()
        device_node = self.device_list_tree.FindItem(self.device_list_tree_root_node, device_text)
        if device_text not in device_node.GetText():
            aklog_error(f'未找到节点: {device_text}')
            return
        self.device_list_tree.SetItemText(device_node, new_text)

    def set_device_node_check(self, device_text, enable=True):
        device_node = self.device_list_tree.FindItem(self.device_list_tree_root_node, device_text)
        if device_text not in device_node.GetText():
            aklog_error(f'未找到节点: {device_text}')
            return
        if enable and not self.device_list_tree.IsItemChecked(device_node):
            self.device_list_tree.CheckItem(device_node, True)
        elif not enable and self.device_list_tree.IsItemChecked(device_node):
            self.device_list_tree.CheckItem(device_node, False)

    def get_checked_device_list(self):
        """获取勾选的设备列表"""
        selected_devices_info = {}
        for device_node in self.device_list_tree_root_node.GetChildren():
            if self.device_list_tree.IsItemChecked(device_node):
                select_device = self.device_list_tree.GetItemText(device_node)
                if select_device.startswith('app_'):
                    continue
                select_device_name = select_device.split(' (')[0]
                selected_devices_info[select_device_name] = self.devices_info[select_device_name]
        return selected_devices_info

    def get_unchecked_device_list(self):
        """获取勾选的设备列表"""
        unselected_devices_info = {}
        for device_node in self.device_list_tree_root_node.GetChildren():
            if not self.device_list_tree.IsItemChecked(device_node):
                unselect_device = self.device_list_tree.GetItemText(device_node)
                if unselect_device.startswith('app_'):
                    continue
                unselect_device_name = unselect_device.split(' (')[0]
                unselected_devices_info[unselect_device_name] = self.devices_info[unselect_device_name]
        return unselected_devices_info

    def get_checked_app_list(self):
        """获取勾选的APP列表"""
        selected_apps_info = {}
        for app_node in self.device_list_tree_root_node.GetChildren():
            if self.device_list_tree.IsItemChecked(app_node):
                select_app = self.device_list_tree.GetItemText(app_node)
                if not select_app.startswith('app_'):
                    continue
                select_app_name = select_app.split(' (')[0]
                selected_apps_info[select_app_name] = self.devices_info[select_app_name]
        return selected_apps_info

    def get_unchecked_app_list(self):
        """获取取消勾选的APP列表"""
        unselected_apps_info = {}
        for app_node in self.device_list_tree_root_node.GetChildren():
            if not self.device_list_tree.IsItemChecked(app_node):
                unselect_app = self.device_list_tree.GetItemText(app_node)
                if not unselect_app.startswith('app_'):
                    continue
                unselect_app_name = unselect_app.split(' (')[0]
                unselected_apps_info[unselect_app_name] = self.devices_info[unselect_app_name]
        return unselected_apps_info

    def get_all_device_list(self):
        """获取所有的设备列表"""
        all_device_list = []
        for device_node in self.device_list_tree_root_node.GetChildren():
            device_name = self.device_list_tree.GetItemText(device_node)
            device_name = device_name.split(' (')[0]
            all_device_list.append(device_name)
        return all_device_list

    def uncheck_all_device(self):
        """所有设备取消勾选"""
        for device_node in self.device_list_tree_root_node.GetChildren():
            if self.device_list_tree.IsItemChecked(device_node):
                self.device_list_tree.CheckItem(device_node, False)

    # endregion

    # region 用例树
    def create_case_tree_item(self):
        """生成用例树"""
        # 用例数默认勾选
        if self.default_launch_config['save_last_checked_case']:
            self.last_checked_case_info = xml_parse_last_checked_case_list(self.last_selected_case_file)

        # 生成用例树
        for module in sorted(self.test_modules.keys(), key=lambda x: x.lower()):
            # 用例模块目录按照字母排序，增加参数key=str.lower忽略大小写
            module_node = self.frame.create_tree_item(self.case_tree, self.case_tree_root_node, module)
            for test_class in self.test_modules[module].keys():
                class_node = self.frame.create_tree_item(self.case_tree, module_node, test_class)
                # 根据上次保存的勾选用例列表，勾选用例树节点
                if self.last_checked_case_info and test_class in self.last_checked_case_info:
                    self.frame.check_tree_node_by_item(self.case_tree, class_node, True)
                for test_case in self.test_modules[module][test_class]:
                    case_node = self.frame.create_tree_item(self.case_tree, class_node, test_case)
                    # 根据上次保存的勾选用例列表，勾选用例树节点
                    if self.last_checked_case_info and test_class in self.last_checked_case_info and \
                            test_case in self.last_checked_case_info[test_class]:
                        self.frame.check_tree_node_by_item(self.case_tree, case_node, True)
            self.case_tree.Expand(module_node)
        self.case_tree.Expand(self.case_tree_root_node)
        # self.check_case_tree_parent_node()

    def check_case_tree_parent_node(self):
        """
        遍历用例树，如果子节点全部勾选，那么父节点也勾选，如果子节点部分勾选，则父节点也设为部分勾选状态
        需要复选框设置为3tate才行，还未完成
        """
        module_node_status = 0
        for module_node in self.case_tree_root_node.GetChildren():
            class_node_status = 0
            for class_node in module_node.GetChildren():
                case_check_status = 0
                for case_node in class_node.GetChildren():
                    print(self.frame.get_tree_checkbox_state(self.case_tree, case_node))
                    if self.frame.get_tree_checkbox_state(self.case_tree, case_node) == 1:
                        case_check_status = 1
                    elif case_check_status == 1:
                        self.frame.set_tree_node_state(self.case_tree, class_node, wx.CHK_UNDETERMINED)
                        break
                if self.frame.get_tree_checkbox_state(self.case_tree, class_node) == 1:
                    class_node_status = 1
                elif class_node_status == 1:
                    self.frame.set_tree_node_state(self.case_tree, module_node, wx.CHK_UNDETERMINED)
                    break
            if self.frame.get_tree_checkbox_state(self.case_tree, module_node) == 1:
                module_node_status = 1
            elif module_node_status == 1:
                self.frame.set_tree_node_state(self.case_tree, self.case_tree_root_node, wx.CHK_UNDETERMINED)
                break

    def check_include_last_checked_case_alert(self):
        """检查这次勾选的用例是否包含上次勾选的，并进行提醒"""
        flag = False
        if not self.last_checked_case_info or self.last_checked_case_info == self.modules_dict:
            return True
        for module_name in self.modules_dict:
            if module_name not in self.last_checked_case_info:
                continue
            for case_name in self.modules_dict[module_name]:
                if case_name in self.last_checked_case_info[module_name]:
                    flag = True
                    break
        if flag:
            toast = wx.MessageDialog(None,
                                     "当前选择的用例包含上次勾选保存的用例。\n"
                                     "确定是否继续？",
                                     "提示",
                                     wx.YES_NO | wx.ICON_QUESTION)
            toast_show_modal = toast.ShowModal()
            if toast_show_modal == wx.ID_YES:  # 如果点击了提示框的是按钮，则关闭提示框，但继续执行
                toast.Destroy()
                return True
            elif toast_show_modal == wx.ID_NO:  # 如果点击了提示框的否按钮，则关闭提示框返回界面
                toast.Destroy()
                return False
            return False
        else:
            return True

    def get_checked_modules_dict(self):
        """获取勾选的用例，输出字典类型"""
        modules_dict = {}
        for module in self.case_tree_root_node.GetChildren():
            for module_class in module.GetChildren():
                module_case_list = []
                module_class_text = self.frame.get_text_tree_item(self.case_tree, module_class)
                module_case_items = module_class.GetChildren()
                for module_case in module_case_items:
                    if self.frame.is_checked_tree_node_by_item(self.case_tree, module_case):
                        module_case_text = self.frame.get_text_tree_item(self.case_tree, module_case)
                        module_case_list.append(module_case_text)
                if module_case_list:
                    modules_dict[module_class_text] = module_case_list
        # print('modules_dict: %r' % modules_dict)

        self.modules_dict = modules_dict
        # 获取总用例数量，只计算测试一遍的用例数量
        total_case_counts = 0
        module_counts = 0

        module_str = """"""
        if self.modules_dict:
            for module in sorted(self.modules_dict.keys()):
                module_str = module_str + module + '\n'
                total_case_counts += len(self.modules_dict[module])
                module_counts += 1
            module_str = """用例模块数量: %s， 总用例数量: %s\n""" % (module_counts, total_case_counts) + module_str

        # case selected窗口打印出勾选的用例模块
        self.case_selected_text_ctrl.SetValue(module_str)
        return modules_dict

    def case_tree_checked_item(self, event=None):
        """
        勾选树节点触发执行，只要树控件中的任意一个复选框状态有变化就会响应这个函数
        勾选时会把所有的子节点都同时勾选
        """
        self.frame.checked_item(self.case_tree, event)
        self.get_checked_modules_dict()

    # endregion

    # region 开始和关闭
    def view_start_btn_description(self, event=None):
        if event:
            if not param_get_running_state():
                start_button_tooltip = wx.ToolTip('点击Start按钮开始测试，之后可以随时点击Stop按钮结束测试')
            elif self.start_button.GetLabel() == 'Resume':
                start_button_tooltip = wx.ToolTip('等待当前用例执行结束，也可以点击Resume恢复不退出执行')
            else:
                start_button_tooltip = wx.ToolTip('点击Stop按钮结束测试，会在当前用例执行完成后退出')
            self.start_button.SetToolTip(start_button_tooltip)

    def view_pause_btn_description(self, event=None):
        if event:
            if not param_get_pause_run():
                pause_button_tooltip = wx.ToolTip('点击Pause按钮暂停测试，会在当前用例执行完成后暂停')
            else:
                pause_button_tooltip = wx.ToolTip('点击Resume恢复执行')
            self.pause_button.SetToolTip(pause_button_tooltip)

    def intercom_check_master_alive_alert(self):
        if param_get_product_line_name() == 'INTERCOM':
            state = True
            productname = param_get_seriesproduct_name().lower()
            if productname in ['linuxdoor', 'accessdoor']:
                slave = 'slave1_linux_indoor'
            elif productname == 'androiddoor':
                slave = 'slave3_linux_indoor'
            elif productname == 'androidindoor':
                slave = 'slave2_linux_door'
            elif productname == 'linuxindoor':
                slave = 'slave_linux_door'
            else:
                slave = ''

            device_list = param_get_excel_data().get('device_info')
            tips = '当前设备网络不可达: \n'
            for device in device_list:
                device_name = device.get('device_name')
                device_ip = device.get('ip')
                if 'master' in device_name or device_name == slave:
                    if not check_wan_connected(device_ip):
                        tips += f'{device_name} - {device_ip}\n'
                        state = False
            tips += "确定是否继续？"
            if not state:
                toast = wx.MessageDialog(None,
                                         tips,
                                         "提示",
                                         wx.YES_NO | wx.ICON_QUESTION)
                toast_show_modal = toast.ShowModal()
                if toast_show_modal == wx.ID_YES:  # 如果点击了提示框的是按钮，则关闭提示框，但继续执行
                    toast.Destroy()
                    return True
                elif toast_show_modal == wx.ID_NO:  # 如果点击了提示框的否按钮，则关闭提示框返回界面
                    toast.Destroy()
                    return False
        return True

    def upgrade_case_alert(self):
        """检查用例当中是否存在升级相关用例，如果有则点击start按钮时判断是否勾选了跳过升级包下载，并进行提醒"""
        upgrade_flag = False
        for case_class in self.modules_dict:
            if 'upgrade' in case_class.lower() or 'AA' in case_class:
                upgrade_flag = True
                break
            for case in self.modules_dict[case_class]:
                if 'upgrade' in case.lower() or 'update' in case.lower():
                    upgrade_flag = True
                    break
            if upgrade_flag:
                break

        if self.get_skip_download_firmware_state() and upgrade_flag:
            toast = wx.MessageDialog(None,
                                     "当前选择用例可能存在升级相关，勾选Skip Download Firmware可能会导致升级失败。\n"
                                     "确定是否继续？",
                                     "提示",
                                     wx.YES_NO | wx.ICON_QUESTION)
            toast_show_modal = toast.ShowModal()
            if toast_show_modal == wx.ID_YES:  # 如果点击了提示框的是按钮，则关闭提示框，但继续执行
                toast.Destroy()
                return True
            elif toast_show_modal == wx.ID_NO:  # 如果点击了提示框的否按钮，则关闭提示框返回界面
                toast.Destroy()
                return False
            return False
        else:
            return True

    def stress_test_count_alert(self):
        """检查用例是否存在压测用例，如果有，则判断当前test_count是否设置数量，并提醒"""
        stress_flag = False
        for case_class in self.modules_dict:
            if 'stress' in case_class.lower() or 'pressure' in case_class.lower():
                stress_flag = True
                break
            for case in self.modules_dict[case_class]:
                if 'stress' in case.lower() or 'pressure' in case.lower():
                    stress_flag = True
                    break
            if stress_flag:
                break

        if (stress_flag and self.get_test_counts() == 1 and
                self.get_test_times() == 1 and self.get_test_rounds() == 1):
            toast = wx.MessageDialog(None,
                                     "当前选择用例可能是要进行压测，但Test Counts或Test Times或Test Rounds仍为1。\n"
                                     "确定是否继续？",
                                     "提示",
                                     wx.YES_NO | wx.ICON_QUESTION)
            toast_show_modal = toast.ShowModal()
            if toast_show_modal == wx.ID_YES:  # 如果点击了提示框的是按钮，则关闭提示框，但继续执行
                toast.Destroy()
                return True
            elif toast_show_modal == wx.ID_NO:  # 如果点击了提示框的否按钮，则关闭提示框返回界面
                toast.Destroy()
                return False
            return False
        else:
            return True

    def start_test(self, event=None):
        """点击Start执行，先获取勾选的用例，获取测试次数、乱序测试、发送邮件、测试报告类型，然后启动线程执行unittest_start"""
        if not event:
            return
        # 如果已经在执行中，则变成stop按钮，点击Stop可以停止执行
        if param_get_running_state():
            # 点击Stop停止执行
            self.trigger_pause_run('resume')
            if self.start_button.GetLabel() == 'Stop':
                aklog_info('点击Stop停止执行')
                param_put_stop_exec_enable(True)
                self.start_button.SetLabel('Resume')
                return
            # 点击Resume恢复执行
            if self.start_button.GetLabel() == 'Resume':
                aklog_info('点击Resume恢复执行')
                param_put_stop_exec_enable(False)
                self.start_button.SetLabel('Stop')
                return

        # 检查用例当中是否存在升级相关用例，如果有则点击start按钮时判断是否勾选了跳过升级包下载，并进行提醒
        if (not self.upgrade_case_alert() or
                not self.stress_test_count_alert() or
                not self.check_include_last_checked_case_alert() or
                not self.intercom_check_master_alive_alert()):
            return

        # 将勾选的用例写入到LastCheckedCase.xml文件
        if self.default_launch_config['save_last_checked_case']:
            xml_write_last_checked_case_list(self.last_selected_case_file, self.modules_dict)
        param_put_modules_dict(self.modules_dict)
        self.get_test_counts()
        self.get_test_times()
        self.get_test_rounds()
        self.get_test_random_state()
        self.get_email_receivers()
        self.get_browser_headless_enable_state()
        self.get_retry_counts()
        self.get_save_last_try_state()
        self.get_exec_one_case_to_report_enable()

        # 修改temp.ini配置文件，把stop_exec_enable设置为False
        temp_config_file = os.path.join(g_config_path, 'temp.ini')
        temp_config = ReadConfig(temp_config_file)
        stop_exec_enable = temp_config.get_value('config', 'stop_exec_enable')
        if stop_exec_enable is True:
            temp_config.modify_config('config', 'stop_exec_enable', 'False').write_config()

        run_time = self.get_run_time()
        if run_time:
            aklog_printf('等到 %s 再开始' % run_time)
            sleep_to_end_time(run_time)
        param_put_running_state(True)

        # 将Start按钮变成Stop按钮
        self.start_button.SetLabel('Stop')
        self.disable_ctrl_after_start()

        self.test_start_thread = AkThread(target=self.scheduled_execution_unittest_start)
        self.test_start_thread.daemon = True  # 将主线程设置为守护线程，主线程停止时，所有子线程也同时停止运行
        self.test_start_thread.start()  # 启用线程执行，避免界面假死未响应

    def pause_test(self, event=None):
        """点击Pause暂停执行"""
        if event:
            if not param_get_running_state():
                aklog_warn(f'当前还未开始执行，点击 {self.pause_button.GetLabel()} 无效')
                return
            if self.start_button.GetLabel() == 'Resume':
                aklog_warn(f'当前准备退出执行，点击 {self.pause_button.GetLabel()} 无效')
                return
            if param_get_scheduled_execution_enable():
                aklog_warn(
                    f'当前启用定期执行，点击 {self.pause_button.GetLabel()} 无效，请先取消勾选Scheduled Execution Enable')
                return
            if param_get_pause_run():
                # 当前处于暂停状态，按钮为Resume，点击Resume恢复执行，按钮重新变成Pause
                aklog_info('手动恢复执行')
                param_put_pause_run(False)
                param_put_stop_exec_enable(False)
                self.pause_button.SetLabel('Pause')
                # 重新获取午休暂停状态
                self.get_pause_during_nap_time_state(True)
            else:
                # 当前处于执行状态，按钮为Pause，点击Pause暂停执行，按钮重新变成Resume
                aklog_info('手动暂停执行')
                param_put_pause_run(True)
                self.pause_button.SetLabel('Resume')

    def trigger_pause_run(self, state='pause'):
        """
        午休暂停时，会改变勾选界面的Pause按钮为Resume
        state： pause/ resume
        """
        if state == 'pause':
            param_put_pause_run(True)
            self.pause_button.SetLabel('Resume')
        else:
            param_put_pause_run(False)
            self.pause_button.SetLabel('Pause')

    def trigger_restore(self):
        """
        执行完成后，将按钮变成Start
        """
        self.start_button.SetLabel('Start')
        self.enable_ctrl_after_stop()

    def disable_ctrl_after_start(self):
        """启动后，禁用控件"""
        if param_get_running_state():
            self.skip_download_firmware_check_box.Enable(False)
            self.test_rounds_text_ctrl.Enable(False)
            self.test_times_text_ctrl.Enable(False)
            self.test_counts_text_ctrl.Enable(False)
            self.retry_counts_text_ctrl.Enable(False)
            self.run_time_text_ctrl.Enable(False)
            self.test_random_check_box.Enable(False)
            self.exec_one_case_to_report_check_box.Enable(False)
            self.browser_headless_enable_check_box.Enable(False)

    def enable_ctrl_after_stop(self):
        """结束后，启用控件"""
        if not param_get_running_state():
            self.skip_download_firmware_check_box.Enable(True)
            self.test_rounds_text_ctrl.Enable(True)
            self.test_times_text_ctrl.Enable(True)
            self.test_counts_text_ctrl.Enable(True)
            self.retry_counts_text_ctrl.Enable(True)
            self.run_time_text_ctrl.Enable(True)
            self.test_random_check_box.Enable(True)
            self.exec_one_case_to_report_check_box.Enable(True)
            self.browser_headless_enable_check_box.Enable(True)

    def scheduled_execution_unittest_start(self):
        """定期执行"""
        if param_get_scheduled_execution_enable():
            while self.start_button.GetLabel() == 'Stop':
                # 当启用定时执行时，检查当前是否处于暂停执行期间
                wait_time = judge_cur_time_within_time_range(
                    g_nap_time_range[0], g_nap_time_range[1])
                if wait_time > 0:
                    wait_time_convert = sec2time(wait_time, n_msec=0)
                    aklog_warn('\n定期执行, %s 当前为暂停执行期间，等到 %s 之后再继续执行，等待时间: %s\n'
                               % (aklog_get_current_time(), g_nap_time_range[1], wait_time_convert))
                    self.trigger_pause_run('pause')
                    deadline = time.time() + wait_time
                    while param_get_pause_run() and time.time() < deadline:
                        time.sleep(1)
                    self.trigger_pause_run('resume')
                if not param_get_stop_exec_enable():
                    unittest_start()

            aklog_info('定期执行结束')
            param_put_running_state(False)
            self.trigger_restore()
            self.trigger_pause_run('resume')
            param_put_stop_exec_enable(False)
        else:
            unittest_start()

    # endregion


def check_wan_connected(ip):
    """等待设备网络可以连接上"""
    aklog_info()
    try:
        requests.get('http://%s' % ip, timeout=1)
    except:
        pass
    else:
        return True
    try:
        requests.get('https://%s' % ip, timeout=1, verify=False)
    except SSLError:
        # 2025.4.1 python 3.12 + 室内机, 使用这个会出现SSLError: HTTPSConnectionPool(host='192.168.30.138', port=443):
        # Max retries exceeded with url: / (Caused by SSLError(SSLError(1, '[SSL: DH_KEY_TOO_SMALL]
        # dh key too small (_ssl.c:1010)')))
        return True
    except:
        return False
    else:
        return True


if __name__ == "__main__":
    modules = {
        'module1': {'module1_class1': ['module1_class1_case1', 'module1_class1_case2', 'module1_class1_case3'],
                    'module1_class2': ['module1_class2_case1', 'module1_class2_case2', 'module1_class2_case3'],
                    'module1_class3': ['module1_class3_case1', 'module1_class3_case2', 'module1_class3_case3']},
        'module2': {'module2_class1': ['module2_class1_case1', 'module2_class1_case2', 'module2_class1_case3'],
                    'module2_class2': ['module2_class2_case1', 'module2_class2_case2', 'module2_class2_case3'],
                    'module2_class3': ['module2_class3_case1', 'module2_class3_case2', 'module2_class3_case3']},
        'module3': {'module3_class1': ['module3_class1_case1', 'module3_class1_case2', 'module3_class1_case3'],
                    'module3_class2': ['module3_class2_case1', 'module3_class2_case2', 'module3_class2_case3'],
                    'module3_class3': ['module3_class3_case1', 'module3_class3_case2', 'module3_class3_case3']}}

    app = AutoTestApp(modules=modules)
    param_put_launch_window_app(app)
    app.MainLoop()
