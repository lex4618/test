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
import wx
import wx.lib.agw.customtreectrl as CT
import win32api


class MainFrame(wx.Frame):
    """程序主窗口类，继承自wx.Frame"""

    def __init__(self, app_title, size=(1280, 720)):
        """构造函数"""

        wx.Frame.__init__(self, None, -1, app_title, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER, size=size)
        # 默认style是下列项的组合：wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION |
        # wx.CLOSE_BOX | wx.CLIP_CHILDREN

        self.SetBackgroundColour(wx.Colour(224, 224, 224))
        self.size = size
        self.SetSize(size)
        self.Center()

        exe_name = win32api.GetModuleFileName(win32api.GetModuleHandle(None))
        icon = wx.Icon(exe_name, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

    def event_close(self, event):
        self.Bind(wx.EVT_CLOSE, event)

    @staticmethod
    def event_tree_item_checked(custom_tree, event):
        """树节点勾选触发事件"""
        custom_tree.Bind(CT.EVT_TREE_ITEM_CHECKED, event)

    def event_button(self, event, button_ctrl):
        """点击按钮触发事件"""
        self.Bind(wx.EVT_BUTTON, event, button_ctrl)

    def event_check_box(self, event, check_box_ctrl):
        """勾选框勾选触发事件"""
        self.Bind(wx.EVT_CHECKBOX, event, check_box_ctrl)

    def event_select_combo_box(self, event, combo_box_ctrl):
        """下拉框选择触发事件"""
        self.Bind(wx.EVT_COMBOBOX, event, combo_box_ctrl)

    def event_text(self, event, text_ctrl):
        """文本框内容变化绑定事件"""
        self.Bind(wx.EVT_TEXT, event, text_ctrl)

    def event_timer(self, event, timer):
        self.Bind(wx.EVT_TIMER, event, timer)

    @staticmethod
    def event_move_motion(event, ctrl):
        """控件鼠标悬停触发事件"""
        ctrl.Bind(wx.EVT_MOTION, event)

    @staticmethod
    def event_enter_window(event, ctrl):
        """鼠标移动到控件窗口触发事件"""
        ctrl.Bind(wx.EVT_ENTER_WINDOW, event)

    @staticmethod
    def event_leave_window(event, ctrl):
        """鼠标离开控件窗口触发事件"""
        ctrl.Bind(wx.EVT_LEAVE_WINDOW, event)

    def split_vertical_window(self, sash_position=200, min_pane_size=80):
        """将窗口分离成左右两个窗格面板"""
        splitter_window = wx.SplitterWindow(parent=self, id=-1)
        left_panel = wx.Panel(parent=splitter_window)
        right_panel = wx.Panel(parent=splitter_window)
        # 设置左右布局的分割窗口left和right
        splitter_window.SplitVertically(left_panel, right_panel, sashPosition=int(sash_position))
        # 设置最小窗格大小，左右布局指左边窗口大小
        splitter_window.SetMinimumPaneSize(min_pane_size)
        return left_panel, right_panel

    def split_horizontal_window(self, sash_position=200, min_pane_size=80):
        """将窗口分离成上下两个窗格面板"""
        splitter_window = wx.SplitterWindow(parent=self, id=-1)
        up_panel = wx.Panel(parent=splitter_window)
        down_panel = wx.Panel(parent=splitter_window)
        # 设置左右布局的分割窗口left和right
        splitter_window.SplitHorizontally(up_panel, down_panel, sashPosition=int(sash_position))
        # 设置最小窗格大小，左右布局指左边窗口大小
        splitter_window.SetMinimumPaneSize(min_pane_size)
        return up_panel, down_panel

    @staticmethod
    def split_horizontal_panel(panel, sash_position=200):
        """将面板再按照上下分割成两个面板"""
        splitter_panel = wx.SplitterWindow(parent=panel)
        box = wx.BoxSizer(wx.HORIZONTAL)  # 创建一个水平布局
        box.Add(splitter_panel, 1, wx.EXPAND)  # 将子分割窗布局延伸至整个panel空间
        panel.SetSizer(box)
        up_panel = wx.Panel(parent=splitter_panel)
        down_panel = wx.Panel(parent=splitter_panel)
        # 设置上下布局的分割窗口
        splitter_panel.SplitHorizontally(up_panel, down_panel, sashPosition=int(sash_position))
        return up_panel, down_panel

    @staticmethod
    def split_vertical_panel(panel, sash_position=200):
        """将面板再按照左右分割成两个面板"""
        splitter_panel = wx.SplitterWindow(parent=panel)
        box = wx.BoxSizer(wx.VERTICAL)  # 创建一个垂直布局
        box.Add(splitter_panel, 1, wx.EXPAND)  # 将子分割窗布局延伸至整个panel空间
        panel.SetSizer(box)
        left_panel = wx.Panel(parent=splitter_panel)
        right_panel = wx.Panel(parent=splitter_panel)
        # 设置左右布局的分割窗口
        splitter_panel.SplitVertically(left_panel, right_panel, sashPosition=int(sash_position))
        return left_panel, right_panel

    @staticmethod
    def create_horizontal_box_sizer():
        """水平方向"""
        h_box = wx.BoxSizer(wx.HORIZONTAL)
        return h_box

    @staticmethod
    def create_vertical_box_sizer():
        """垂直方向"""
        v_box = wx.BoxSizer(wx.VERTICAL)
        return v_box

    # def create_horizontal_static_box_sizer(self):
    #     """水平方向"""
    #     h_box = wx.StaticBoxSizer(wx.HORIZONTAL)
    #     return h_box

    # def create_vertical_static_box_sizer(self):
    #     """垂直方向"""
    #     v_box = wx.StaticBoxSizer(wx.VERTICAL)
    #     return v_box

    @staticmethod
    def set_panel_sizer(panel, box_sizer):
        """为窗格面板设置一个布局管理器"""
        panel.SetSizer(box_sizer)

    @staticmethod
    def box_sizer_add_ctrl(box_sizer, ctrl, flag, proportion=1, border=5):
        """给窗格添加控件"""
        box_sizer.Add(ctrl, proportion=proportion, flag=flag, border=border)

    @staticmethod
    def create_custom_tree(parent):
        """生成带勾选框的树"""
        custom_tree = CT.CustomTreeCtrl(parent=parent, agwStyle=wx.TR_DEFAULT_STYLE)
        # 通过wx.ImageList()创建一个图像列表imglist并保存在树中
        img_list = wx.ImageList(16, 16, True, 2)
        img_list.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, size=wx.Size(16, 16)))
        img_list.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, size=(16, 16)))
        custom_tree.AssignImageList(img_list)
        return custom_tree

    @staticmethod
    def create_tree_root(custom_tree, tree_root_name, state3=False):
        """创建树根节点"""
        tree_root_node = custom_tree.AddRoot(tree_root_name, ct_type=1, image=1, selImage=-1)
        if state3:
            custom_tree.SetItem3State(tree_root_node, True)
        return tree_root_node

    @staticmethod
    def create_tree_item(custom_tree: CT.CustomTreeCtrl, node, sub_node_name, state3=False):
        """创建树子节点"""
        sub_node = custom_tree.AppendItem(node, sub_node_name, ct_type=1, image=1, selImage=-1)
        if state3:
            custom_tree.SetItem3State(sub_node, True)
        return sub_node

    @staticmethod
    def create_tree_item_before(custom_tree: CT.CustomTreeCtrl, node, index, sub_node_name, state3=False):
        """插入树子节点"""
        sub_node = custom_tree.InsertItemByIndex(node, index, sub_node_name, ct_type=1, image=1, selImage=-1)
        if state3:
            custom_tree.SetItem3State(sub_node, True)
        return sub_node

    @staticmethod
    def is_checked_tree_node_by_item(custom_tree, item):
        """判断树节点是否勾选"""
        return custom_tree.IsItemChecked(item)

    @staticmethod
    def uncheck_tree_node_by_item(custom_tree, item):
        """树节点取消勾选"""
        custom_tree.CheckItem(item, False)

    def check_tree_node_by_item(self, custom_tree, item, status=True, child_check=False):
        """
        树节点勾选
        child_check: 子节点是否同步勾选或者取消勾选
        """
        # aklog_info()
        custom_tree.CheckItem(item, status)
        if not child_check:
            return
        for sub_item in item.GetChildren():
            if custom_tree.IsItemChecked(item):
                custom_tree.CheckChilds(item, checked=True)
            else:
                custom_tree.CheckChilds(item, checked=False)
            self.check_tree_node_by_item(custom_tree, sub_item, status, child_check)

    @staticmethod
    def set_tree_node_state(custom_tree, item, state=True):
        """设置树节点勾选框的状态，0 1 2， True False"""
        if custom_tree.IsItem3State(item):
            custom_tree.SetItem3StateValue(item, state)
        else:
            custom_tree.CheckItem(item, state)

    @staticmethod
    def get_tree_checkbox_state(custom_tree, item):
        """获取树节点复选框的状态"""
        if custom_tree.IsItem3State(item):
            state = custom_tree.GetItem3StateValue(item)
        else:
            state = custom_tree.IsItemChecked(item)
        return state

    @staticmethod
    def checked_item(custom_tree, event):
        """
        勾选树节点触发执行，只要树控件中的任意一个复选框状态有变化就会响应这个函数
        勾选时会把所有的子节点都同时勾选
        """
        event_item = event.GetItem()
        if event_item.GetChildren():
            if custom_tree.IsItemChecked(event_item):
                custom_tree.CheckChilds(event_item, checked=True)
            else:
                custom_tree.CheckChilds(event_item, checked=False)

    @staticmethod
    def get_tree_children(tree_item):
        """获取树节点的下一级所有子节点"""
        return tree_item.GetChildren()

    @staticmethod
    def get_text_tree_item(custom_tree, item):
        """获取树节点名称"""
        text = custom_tree.GetItemText(item)
        return text

    @staticmethod
    def get_text_tree_item_checked(custom_tree, item):
        """获取已勾选的树节点名称"""
        if custom_tree.IsItemChecked(item):
            return custom_tree.GetItemText(item)
        else:
            return None

    @staticmethod
    def create_text_ctrl(parent, pos=(0, 0), size=(112, 30)):
        """创建文本输入框"""
        text_ctrl = wx.TextCtrl(parent, pos=pos, size=size)
        return text_ctrl

    @staticmethod
    def get_text_by_ctrl(ctrl):
        """获取文本输入框的值"""
        return ctrl.GetValue()

    @staticmethod
    def create_button_ctrl(parent, ctrl_id=-1, label='Button', pos=(0, 0), size=(50, 30),
                           style=0, name=''):
        """创建按钮"""
        button_ctrl = wx.Button(parent=parent, id=ctrl_id, label=label, pos=pos, size=size,
                                style=style,  name=name)
        return button_ctrl

    @staticmethod
    def create_static_text_ctrl(parent, ctrl_id=-1, label='', pos=(0, 0), size=(112, 30),
                                style=0, name=''):
        """创建显示静态文本"""
        static_text_ctrl = wx.StaticText(parent=parent, id=ctrl_id, label=label, pos=pos, size=size,
                                         style=style, name=name)
        return static_text_ctrl

    @staticmethod
    def create_check_box(parent, ctrl_id=-1, label='', pos=(0, 0), size=(112, 30), style=wx.CHK_2STATE):
        """创建勾选框"""
        check_box = wx.CheckBox(parent=parent, id=ctrl_id, label=label, pos=pos, size=size, style=style)
        return check_box

    @staticmethod
    def get_checkbox_state_by_ctrl(ctrl):
        """获取勾选框状态"""
        return ctrl.GetValue()

    @staticmethod
    def create_combo_box(parent, choices, ctrl_id=-1, pos=(0, 0), size=(200, 30)):
        combo_box = wx.ComboBox(parent=parent, id=ctrl_id, pos=pos, size=size, choices=choices,
                                style=wx.CB_SORT)
        return combo_box

    @staticmethod
    def get_combo_box_selected_by_ctrl(ctrl):
        """获取下拉框选中的选项文本"""
        return ctrl.GetStringSelection()
