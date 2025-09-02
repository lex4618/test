# -*- coding: utf-8 -*-
import locale
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
import win32gui
import win32con
import subprocess
import traceback
import re
import time
import socket
import win32api
import win32ui
import psutil
import netifaces
import pyautogui
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

pc_adapter_desc = ''
g_local_host_ip = ''


class Window_process(object):
    """Encapsulates some calls to the winapi for window management"""

    def __init__(self):
        """Constructor"""
        self._handle = None

    def find_window(self, class_name, window_name=None):
        """find a window by its class_name"""
        self._handle = win32gui.FindWindow(class_name, window_name)

    def _window_enum_callback(self, hwnd, wildcard):
        """Pass to win32gui.EnumWindows() to check all the opened windows"""
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        """
        获取窗口
        wildcard： app主窗口名称
        """
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)

    def set_foreground_and_restore(self):
        """将窗口前置，可以从最小化切换至前台"""
        done = False
        if self._handle > 0:
            win32gui.SendMessage(self._handle, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
            win32gui.SetForegroundWindow(self._handle)
            done = True
        return done

    def set_foreground_and_maximize(self):
        """将窗口切换之前台，并最大化"""
        done = False
        if self._handle > 0:
            win32gui.SendMessage(self._handle, win32con.WM_SYSCOMMAND, win32con.SC_MAXIMIZE, 0)
            win32gui.SetForegroundWindow(self._handle)
            done = True
        return done

    def set_foreground(self):
        """将窗口前置，但窗口必须打开，且不能最小化"""
        done = False
        if self._handle:
            win32gui.SetForegroundWindow(self._handle)
            done = True
        return done

    @staticmethod
    def upload_file(file_path):
        """
        实现非input标签上传文件,调用此方法需要打开windows上传文件的系统窗口再调用
        :param file_path:上传文件的路径
        :return:
        """
        dialog = win32gui.FindWindow("#32770", "打开")
        comboxex32 = win32gui.FindWindowEx(dialog, 0, "ComboBoxEx32", None)
        combox = win32gui.FindWindowEx(comboxex32, 0, "ComboBox", None)
        edit = win32gui.FindWindowEx(combox, 0, "Edit", None)
        button = win32gui.FindWindowEx(dialog, 0, "Button", "打开(&0)")
        win32gui.SendMessage(edit, win32con.WM_SETTEXT, None, file_path)
        time.sleep(1)
        win32gui.SendMessage(dialog, win32con.WM_COMMAND, 1, button)


def keyboard_tap(key, times=1, interval=0):
    """
    敲击，包括按下和弹起
    当要传入特殊按键，例如删除按钮的时候，输入参考backspace, enter
    要传入字符串时，正常传入即可，例如'13asd'

    """
    aklog_printf()
    try:
        pyautogui.press(key, presses=times, interval=interval)
        return True
    except:
        aklog_printf("keyboard_tap failed")
    return False


def keyboard_press_keys(keys: list):
    """按组合键，比如Ctrl+C, keys为： [ctrl, 'c']"""
    aklog_printf()
    try:
        pyautogui.hotkey(*keys)
        return True
    except:
        aklog_printf("keyboard_press_keys failed, %s" % traceback.format_exc())
        return False


def keyboard_press_ctrl_f5():
    """按Ctrl+F5刷新页面"""
    keyboard_press_keys(['ctrl', 'F5'])


def desktop_screenshot(root_path):
    """
    :param root_path: 截屏存放的路径
    :return: none
    """
    # 获取桌面
    hdesktop = win32gui.GetDesktopWindow()

    # 分辨率适配
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

    # 创建设备描述表
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)

    # 创建一个内存设备描述表
    mem_dc = img_dc.CreateCompatibleDC()
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)  # 为bitmap开辟空间
    mem_dc.SelectObject(screenshot)  # 将截图保存到Bitmap中
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)  # 截取从左上角（0，0）长宽为（w，h）的图片

    # 保存到文件
    time_tup = time.localtime(time.time())
    format_time = "%Y-%m-%d_w%a_%H-%M-%S"
    cur_time = time.strftime(format_time, time_tup)
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    screenshot.SaveBitmapFile(mem_dc, '{}/{}.bmp'.format(root_path, cur_time))

    # 释放内存
    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())


def is_valid_ip(ip):
    if not ip or '\x00' in ip:
        return False
    try:
        res = socket.getaddrinfo(ip, 0, socket.AF_UNSPEC,
                                 socket.SOCK_STREAM,
                                 0, socket.AI_NUMERICHOST)
        return bool(res)
    except socket.gaierror as e:
        if e.args[0] == socket.EAI_NONAME:
            return False
        raise


def get_iface_id_by_ip(ip):
    """获取网卡信息"""
    # 创建WMI客户端
    import wmi  # 如果在全局作用域中导入 wmi 模块时，这可能会导致在释放 COM 对象时出现问题。因此在函数内部导入
    c = wmi.WMI()

    # 获取所有激活的网络适配器配置
    network_configs = c.Win32_NetworkAdapterConfiguration(IPEnabled=True)

    # 查找与IP地址匹配的网络适配器配置
    adapter_guid = None
    for config in network_configs:
        if ip in config.IPAddress:
            # 获取网络适配器的GUID
            adapter_guid = config.SettingID
            aklog_info(f"IP Address: {ip}, Adapter GUID: {adapter_guid}")
            break
    del c
    return adapter_guid


def get_default_gateway_ip():
    """获取默认网关的接口IP"""
    try:
        gws = netifaces.gateways()
        default_gateway = gws['default'][netifaces.AF_INET][0]
        aklog_printf("Default Gateway IP: %s" % default_gateway)
        return default_gateway
    except:
        aklog_printf(traceback.format_exc())
        return None


def get_local_host_ip(ip_segment=None):
    """
    获取本机IP，有些情况下，一个网卡内填写了多个IP地址，可以传入网段来选择使用哪个IP，或者传入IP地址，获取到跟传入的IP地址同一个网段的
    默认使用跟默认网关同一个网段的IP
    """
    global g_local_host_ip
    if g_local_host_ip:
        return g_local_host_ip

    hostname = socket.gethostname()  # 获取主机名
    nameex = socket.gethostbyname_ex(hostname)
    host_ip = ''
    if len(nameex[2]) > 1:
        # 存在多张网卡，包括虚拟网卡
        try:
            import psutil
        except ModuleNotFoundError:
            aklog_printf('获取网卡名失败')
            return socket.gethostbyname(hostname)  # 获取本机IP
        else:
            if ip_segment:
                if len(ip_segment.split('.')) == 4:
                    # 如果传入的是完整的地址，则获取相同网段的，先解析出网段
                    ip_segment = ".".join(ip_segment.split(".")[:-1])
                ip_segment_list = [ip_segment]
            else:
                gateway_ip = get_default_gateway_ip()
                if gateway_ip:
                    ip_segment = ".".join(gateway_ip.split(".")[:-1])
                    ip_segment_list = [ip_segment]
                else:
                    ip_segment_list = []
            ip_segment_list.extend(['192.168', '10.0'])

            dic = psutil.net_if_addrs()

            for ip_prefix in ip_segment_list:
                for key, value in dic.items():
                    for addr_info in value:
                        address = addr_info.address
                        if address.startswith(ip_prefix):
                            host_ip = address
                            break
                    if host_ip:
                        if ip_prefix != ip_segment:
                            aklog_printf('当前电脑不存在 %s 网段的IP，获取到默认网段 %s 的IP: %s, 网卡: %s'
                                         % (ip_segment, ip_prefix, host_ip, key))
                        else:
                            aklog_printf("网卡: %s, IP: %s" % (key, host_ip))
                        break
                if host_ip:
                    break

    if not host_ip:
        host_ip = socket.gethostbyname(hostname)  # 获取本机IP
        aklog_printf("get_local_host_ip: %s" % host_ip)

    g_local_host_ip = host_ip
    return host_ip


def get_ip_segment_by_ip(ip_addr):
    """获取IP地址的网段（前三位）"""
    return ".".join(ip_addr.split(".")[:-1])


def cmd_get_result_by_exec_command(command):
    """cmd窗口执行命令并获取结果"""
    result = subprocess.getoutput(command)
    return result


def get_pc_network_info():
    """获取网卡信息"""
    aklog_printf()
    network_info_list = []
    import wmi  # 如果在全局作用域中导入 wmi 模块时，这可能会导致在释放 COM 对象时出现问题。因此在函数内部导入
    c = wmi.WMI()
    for interface in c.Win32_NetworkAdapterConfiguration(IPEnabled=1):
        network_info = dict()
        # print(interface)
        network_info["Description"] = interface.Description
        network_info["IPAddress"] = interface.IPAddress[0] if interface.IPAddress else None
        network_info["IPSubnet"] = interface.IPSubnet[0] if interface.IPSubnet else None
        network_info["Gateway"] = interface.DefaultIPGateway[0] if interface.DefaultIPGateway else None
        network_info["MAC"] = interface.MACAddress
        network_info_list.append(network_info)
    aklog_printf(network_info_list)
    del c
    return network_info_list


def cmd_get_network_adapter_name():
    """获取电脑网卡的名称"""
    get_adapter_name_command = 'ipconfig | findstr "以太网适配器"'
    adapter_name = subprocess.getoutput(get_adapter_name_command)
    adapter_name = adapter_name.split(' ', 1)[1].split(':')[0]
    aklog_printf('cmd_get_network_adapter_name: %s' % adapter_name)
    return adapter_name


def cmd_get_network_adapter_description():
    """获取电脑网卡的描述"""
    # get_adapter_name_command = 'ipconfig /all | findstr "描述" | findstr "Realtek"'
    # adapter_desc = subprocess.getoutput(get_adapter_name_command)
    # adapter_desc = adapter_desc.split(':')[1].strip()
    global pc_adapter_desc
    if not pc_adapter_desc:
        network_info = get_pc_network_info()[0]
        adapter_desc = network_info["Description"]
        pc_adapter_desc = adapter_desc
    aklog_printf('cmd_get_network_adapter_description: %s' % pc_adapter_desc)
    return pc_adapter_desc


def cmd_add_ip_address(ip_address):
    """电脑网卡添加静态IP地址，电脑需要先设置为静态IP"""
    aklog_printf('cmd_add_ip_address: %s' % ip_address)
    ip_list = ip_address.split('.')
    ip_prefix = '%s.%s.%s' % (ip_list[0], ip_list[1], ip_list[2])
    ipconfig_result = subprocess.getoutput('ipconfig | findstr "%s"' % ip_prefix)
    if ipconfig_result:
        aklog_printf('current ip address is: %s, no need to add again' % ip_address)
        return True
    adapter_name = cmd_get_network_adapter_name()
    add_ip_command = 'netsh interface ipv4 add address "%s" %s 255.255.255.0' % (adapter_name, ip_address)
    process = subprocess.Popen(add_ip_command, shell=True)
    process.wait(5)
    process.terminate()
    time.sleep(5)
    add_ip_result = subprocess.getoutput('ipconfig | findstr "%s"' % ip_address)
    aklog_printf(add_ip_result)
    if add_ip_result:
        aklog_printf('add ip address success')
        return True
    else:
        aklog_printf('add ip address failed')
        return False


def cmd_delete_ip_address(ip_address):
    """电脑网卡删除静态IP地址"""
    aklog_printf('cmd_delete_ip_address: %s' % ip_address)
    ipconfig_result = subprocess.getoutput('ipconfig | findstr "IPv4"')
    ipconfig_result2 = subprocess.getoutput('ipconfig | findstr "%s"' % ip_address)
    # if get_local_host_ip() == ip_address:
    if ipconfig_result2 and ipconfig_result == ipconfig_result2:
        aklog_printf('current ip address is: %s, can not delete' % ip_address)
        return True
    elif not ipconfig_result2:
        aklog_printf('ip %s is not exist, no need delete' % ip_address)
        return True
    adapter_name = cmd_get_network_adapter_name()
    delete_ip_command = 'netsh interface ipv4 delete address "%s" %s 255.255.255.0' % (adapter_name, ip_address)
    process = subprocess.Popen(delete_ip_command, shell=True)
    process.wait(5)
    process.terminate()
    time.sleep(5)
    delete_ip_result = subprocess.getoutput('ipconfig | findstr "%s"' % ip_address)
    if not delete_ip_result:
        aklog_printf('delete ip address success')
        return True
    else:
        aklog_printf('delete ip address failed')
        return False


def cmd_get_process_name_by_pid(process_pid):
    aklog_printf('cmd_get_process_name_by_pid: %s' % process_pid)
    result = subprocess.getoutput('tasklist | findstr "%s"' % process_pid)
    lines = result.splitlines()
    for line in lines:
        processes = line.split()
        pid = processes[1]
        if str(pid) == str(process_pid):
            process_name = processes[0]
            aklog_printf('process_name: %s' % process_name)
            return process_name
    aklog_printf('没有找到进程')
    return None


def cmd_get_process_id_by_name(process_name):
    try:
        process_id = None
        for proc in psutil.process_iter(['pid', 'name']):
            if process_name.lower() in proc.info['name'].lower():
                process_id = proc.info['pid']
                break
        aklog_printf('cmd_get_process_id_by_name, process_name: %s, process_id: %s' % (process_name, process_id))
        return process_id
    except Exception as e:
        aklog_printf("Error:", str(e))
        return None


def cmd_get_window_title_by_process_name(process_name):
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if process_name.lower() in proc.name().lower():
                window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                return window
        return None
    except Exception as e:
        print("Error:", str(e))
        return None


def cmd_get_pids_by_process_name(process_name):
    """通过进程名称获取id列表"""
    pids = []
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if process_name.lower() in proc.name().lower():
                process_id = proc.pid
                pids.append(process_id)
        return pids
    except Exception as e:
        aklog_printf("Error:", str(e))
        return []


def cmd_get_process_details(pid):
    try:
        process = psutil.Process(int(pid))
        details = {
            'pid': process.pid,
            'name': process.name(),
            'exe': process.exe(),
            'cmdline': process.cmdline()
        }
        return details
    except psutil.NoSuchProcess:
        return None


def cmd_close_process_by_pid(pid):
    aklog_printf("cmd_close_process_by_pid: %s" % pid)
    for i in range(2):
        process_info = sub_process_get_output('tasklist | findstr "%s"' % pid)
        if not process_info:
            aklog_printf('%s is closed' % pid)
            return True
        elif i == 1:
            aklog_printf('close process %s failed' % pid)
        else:
            sub_process_exec_command('taskkill /F /t /PID "%s"' % pid)
            time.sleep(3)
            continue


def cmd_close_process_by_port(close_port, listen=True):
    """CMD关闭占用的端口"""
    aklog_printf("cmd_close_process_by_port: %s" % close_port)
    if listen:
        result = subprocess.getoutput('netstat -ano | findstr ":%s " | findstr "LISTENING"' % close_port)
    else:
        result = subprocess.getoutput('netstat -ano | findstr ":%s "' % close_port)
    lines = result.splitlines()
    for line in lines:
        try:
            infos = line.split()
            port = infos[1].split(':')[1]
            if port == str(close_port):
                process_pid = infos[-1]
                aklog_printf('process_pid: %s' % process_pid)
                process_name = cmd_get_process_name_by_pid(process_pid)
                if process_name:
                    sub_process_exec_command('taskkill /pid %s /F' % process_pid)
                    aklog_printf("%s 进程已被终止" % process_name)
                    time.sleep(1)
        except:
            aklog_printf("存在异常错误, %s" % traceback.format_exc())
    aklog_printf("已关闭占用端口的进程")


def cmd_close_process_by_name(exe_name):
    aklog_printf("cmd_close_process_by_name: %s" % exe_name)
    for i in range(2):
        process_id = cmd_get_process_id_by_name(exe_name)
        if not process_id:
            aklog_printf('%s is closed' % exe_name)
            return True
        elif i == 1:
            aklog_printf('close process %s failed' % exe_name)
        else:
            sub_process_exec_command('taskkill /F /t /im "%s"' % exe_name)
            time.sleep(2)
            continue


def cmd_close_process_by_exe_path(exe_path, sec=1):
    aklog_printf()
    pids = cmd_get_pids_by_path(exe_path)
    if pids:
        for pid in pids:
            cmd_close_process_by_pid(pid)
        time.sleep(sec)
    else:
        aklog_printf('当前没有该程序在运行')


def cmd_get_process_pid_by_port(port, listening=True):
    """CMD查找占用端口的进程ID"""
    aklog_printf("cmd_get_process_pid_by_port: %s" % port)
    if listening:
        result = subprocess.getoutput('netstat -ano | findstr ":%s " | findstr "LISTENING"' % port)
    else:
        result = subprocess.getoutput('netstat -ano | findstr ":%s "' % port)
    lines = result.splitlines()
    for line in lines:
        try:
            info = line.split()
            port1 = info[1].split(':')[1]
            if port1 == str(port):
                process_pid = info[-1]
                aklog_printf('process_pid: %s' % process_pid)
                return process_pid
        except:
            aklog_printf("存在异常错误, %s" % traceback.format_exc())
            return None
    aklog_printf('未找到占用该端口的进程')
    return None


def cmd_get_process_path_by_port(port):
    """通过占用端口获取程序所在路径"""
    pid = cmd_get_process_pid_by_port(port)
    if not pid:
        return None
    details = cmd_get_process_details(int(pid))
    exe_path = details.get('exe')
    aklog_debug(f'process_path: {exe_path}')
    return exe_path


def cmd_get_pids_by_path(exe_path):
    pids = []
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if os.path.abspath(proc.exe()) == os.path.abspath(exe_path):
                pids.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    aklog_debug(f'{exe_path}, pids: {pids}')
    return pids


def cmd_get_ports_by_pids(pids):
    # 运行 netstat 命令并通过 findstr 筛选出包含 PID 的行
    if not pids:
        return []
    ports = []
    for pid in pids:
        command = f'netstat -ano | findstr "LISTENING" | findstr {pid}'
        result = subprocess.getoutput(command)
        lines = result.splitlines()
        for line in lines:
            # 使用正则表达式匹配端口号
            match = re.search(r':(\d+)\s+', line)
            if match:
                port = int(match.group(1))
                ports.append(port)
    aklog_debug(f'pids: {pids}, ports: {ports}')
    return ports


def cmd_get_ping_result(ip_address, ping_count=4, time_out=1000):
    if not ip_address or not is_valid_ip(ip_address):
        aklog_warn(f'IP地址错误: {ip_address}')
        return [0, 9999, 9999, 9999]

    def __ping(ip_address, ping_count=4, time_out=1000):
        ping_command = "ping %s -n %s -w %s" % (ip_address, ping_count, time_out)
        if sys.getdefaultencoding() == 'utf-8':
            p = subprocess.Popen(ping_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=False)
            out = p.stdout.read().decode('gbk')
        else:
            out = subprocess.getoutput(ping_command)
        return out

    def __parse_ping_result(out):
        reg_receive = r'已接收 = \d'
        match_receive = re.search(reg_receive, out)
        receive_count = -1

        if not match_receive:
            reg_receive = r'Received = \d'
            match_receive = re.search(reg_receive, out)
            reg_min_time = r'Minimum = \d+ms'
            reg_max_time = r'Maximum = \d+ms'
            reg_avg_time = r'Average = \d+ms'
            if match_receive:
                receive_count = int(match_receive.group()[11:])

            if receive_count > 0:
                try:
                    min_time = int(re.search(reg_min_time, out).group()[10:-2])
                    max_time = int(re.search(reg_max_time, out).group()[10:-2])
                    avg_time = int(re.search(reg_avg_time, out).group()[10:-2])
                except:
                    # 挂测有出现正则没匹配到的情况: 'NoneType' object has no attribute 'group'
                    min_time = 9999
                    max_time = 9999
                    avg_time = 9999
                result = [receive_count, min_time, max_time, avg_time]
                return result
            else:
                return [0, 9999, 9999, 9999]
        else:
            receive_count = int(match_receive.group()[6:])
            if receive_count > 0:
                try:
                    min_time = int(re.search(r'最短 = \d+ms', out).group()[5:-2])
                    max_time = int(re.search(r'最长 = \d+ms', out).group()[5:-2])
                    avg_time = int(re.search(r'平均 = \d+ms', out).group()[5:-2])
                except:
                    # 挂测有出现正则没匹配到的情况: 'NoneType' object has no attribute 'group'
                    min_time = 9999
                    max_time = 9999
                    avg_time = 9999
                result = [receive_count, min_time, max_time, avg_time]
                return result
            else:
                return [0, 9999, 9999, 9999]

    with ThreadPoolExecutor(max_workers=ping_count) as executor:
        futures = [executor.submit(__ping, ip_address, 1, time_out) for _ in range(ping_count)]
        results = [__parse_ping_result(future.result()) for future in futures]

    # 汇总结果
    receive_count = sum(result[0] for result in results)
    if receive_count > 0:
        min_time = min(result[1] for result in results)
        max_time = max(result[2] for result in results)
        avg_time = sum(result[3] for result in results) // ping_count
        result = [receive_count, min_time, max_time, avg_time]
        aklog_printf(f'ping {ip_address}, count: {ping_count}, result: {result}')
    else:
        aklog_printf(f'{ip_address} cannot be reached')
        result = [0, 9999, 9999, 9999]
    return result


def cmd_is_device_connected(ip_address, ping_count=4, allowed_loss=0, retry=1) -> bool:
    """通过ping方式判断设备连接状态"""
    for _ in range(retry):
        result = cmd_get_ping_result(ip_address, ping_count)
        if result[0] >= max(ping_count - allowed_loss, 1):
            return True
        time.sleep(1)
    return False


def cmd_is_device_disconnected(ip_address, ping_count=4, retry=1) -> bool:
    """通过ping方式判断设备是否断开连接"""
    for _ in range(retry):
        result = cmd_get_ping_result(ip_address, ping_count)
        if result[0] == 0:
            return True
        time.sleep(1)
    return False


def cmd_get_ping_result_packet_size(ip_address, ping_count=4, time_out=1000, packet_size=65500):
    '''
    #20240313-zhihais：增加了数据包大小的ping
    '''
    ping_command = "ping %s -n %s -w %s -l %s" % (ip_address, ping_count, time_out, packet_size)
    aklog_printf('ping command:%s' % str(ping_command))
    if sys.getdefaultencoding() == 'utf-8':
        p = subprocess.Popen(ping_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=False)
        out = p.stdout.read().decode('gbk')
    else:
        out = subprocess.getoutput(ping_command)
    reg_receive = r'已接收 = \d'
    match_receive = re.search(reg_receive, out)
    receive_count = -1

    if not match_receive:  # 系统是英文
        reg_receive = r'Received = \d'
        match_receive = re.search(reg_receive, out)
        print(match_receive)
        reg_min_time = r'Minimum = \d+ms'
        reg_max_time = r'Maximum = \d+ms'
        reg_avg_time = r'Average = \d+ms'
        if match_receive:
            receive_count = int(match_receive.group()[11:])

        if receive_count > 0:  # 接受到的反馈大于0，表示网络通
            match_min_time = re.search(reg_min_time, out)
            if match_min_time is None:
                aklog_printf('the target cannot be reached:%s' % str(ip_address))
                return [0, 9999, 9999, 9999]

            min_time = int(match_min_time.group()[10:-2])

            match_max_time = re.search(reg_max_time, out)
            max_time = int(match_max_time.group()[10:-2])

            match_avg_time = re.search(reg_avg_time, out)
            avg_time = int(match_avg_time.group()[10:-2])

            result = [receive_count, min_time, max_time, avg_time]
            aklog_printf('ping %s , result: %s' % (ip_address, result))
            return result
        else:
            aklog_printf('the target cannot be reached:%s' % str(ip_address))
            return [0, 9999, 9999, 9999]
    else:
        receive_count = int(match_receive.group()[6:])
        print(receive_count)

        if receive_count > 0:  # 接受到的反馈大于0，表示网络通
            reg_min_time = r'最短 = \d+ms'
            reg_max_time = r'最长 = \d+ms'
            reg_avg_time = r'平均 = \d+ms'
            #
            match_min_time = re.search(reg_min_time, out)
            print(match_min_time)
            if match_min_time is None:
                aklog_printf('the target cannot be reached:%s' % str(ip_address))
                return [0, 9999, 9999, 9999]

            min_time = int(match_min_time.group()[5:-2])
            #
            match_max_time = re.search(reg_max_time, out)
            max_time = int(match_max_time.group()[5:-2])
            #
            match_avg_time = re.search(reg_avg_time, out)
            avg_time = int(match_avg_time.group()[5:-2])

            result = [receive_count, min_time, max_time, avg_time]
            aklog_printf('ping %s , result: %s' % (ip_address, result))
            return result
        else:
            aklog_printf('the target cannot be reached:%s' % str(ip_address))
            return [0, 9999, 9999, 9999]


def cmd_get_ping_result_bool(ip_address, ping_count=4, time_out=1000, try_time=100):
    '''
    #20240229-zhihais：直接输出bool返回值
    '''
    while try_time:
        result = cmd_get_ping_result(ip_address, ping_count, time_out)
        if result == [0, 9999, 9999, 9999]:
            try_time = try_time - 1
            time.sleep(10)
        else:
            return True
    return False


def cmd_get_ping_result_packet_size_bool(ip_address, ping_count=4, time_out=1000, packet_size=65500, try_time=100):
    '''
    #20240313-zhihais：直接输出bool返回值
    '''
    while try_time:
        result = cmd_get_ping_result_packet_size(ip_address, ping_count, time_out, packet_size)
        if result == [0, 9999, 9999, 9999]:
            aklog_printf("ping packet size fail,try again")
            try_time = try_time - 1
            time.sleep(10)
        else:
            return True
    return False


def cmd_waiting_for_device_reboot(ip_address, wait_time1=900, wait_time2=900, sec=10):
    """
    等待设备重启
    :param ip_address: 设备IP
    :param wait_time1: 等待设备进入重启状态的时间
    :param wait_time2: 设备重新启动获取到IP的等待时间
    :param sec: 设备获取到IP地址后等待时间，有些设备获取到IP地址后，仍然无法正常访问，需要等待
    """
    aklog_info()
    aklog_info('检查设备需要在: {} 秒内进入重启状态, {} 秒内需重启后获取到IP.'.format(wait_time1, wait_time2))
    end_time1 = time.time() + wait_time1
    i = 0
    aklog_printf(f'wait {ip_address} to disconnect, pls wait...')
    while True:
        ping_result = cmd_get_ping_result(ip_address, ping_count=2)
        if ping_result[0] == 0:
            if i > 0:
                aklog_printf(f'{ip_address} has disconnected')
                break
            else:
                aklog_printf(f'{ip_address} has disconnected, reconfirm...')
                i += 1
                time.sleep(2)
                continue
        elif time.time() >= end_time1:
            aklog_warn(f'{ip_address} 未在时间 {wait_time1} 秒内重启!!')
            return False
        else:
            i = 0
            time.sleep(5)
            continue

    end_time2 = time.time() + wait_time2
    aklog_printf(f'wait {ip_address} to reconnect, pls wait...')
    while True:
        ping_result = cmd_get_ping_result(ip_address, ping_count=4)
        if ping_result[0] == 4:
            aklog_printf(f'{ip_address} has reconnected')
            if sec > 0:
                aklog_printf(f'设备已重启，继续等待 {sec} 秒')
                time.sleep(sec)
            return True
        elif time.time() >= end_time2:
            aklog_warn(f'{ip_address} 未在时间 {wait_time2} 秒内重启并获取到IP, 返回失败!!')
            return False
        else:
            time.sleep(3)
            continue


def cmd_wait_device_connected(ip_address, timeout=600, ping_count=4, ping_interval=3) -> bool:
    """
    等待设备连接
    Args:
        ip_address (str):
        timeout (int):
        ping_count (int):
        ping_interval (int):
    """
    if not is_valid_ip(ip_address):
        aklog_warn(f'IP地址错误: {ip_address}')
        return False
    end_time = time.time() + timeout
    aklog_printf(f'wait {ip_address} to connected within {timeout} seconds, pls wait...')
    while time.time() < end_time:
        ping_result = cmd_get_ping_result(ip_address, ping_count=ping_count)
        if ping_result[0] == ping_count:
            aklog_printf(f'{ip_address} has connected')
            return True
        time.sleep(ping_interval)
        continue
    aklog_warn(f'{ip_address} 未在 {timeout} 秒内连接')
    return False


def cmd_get_connectable_ip_from_device_info(device_info: dict, is_raise=False):
    """从device_info中获取可连接的ip，如果默认的ip不可用，将改为使用wifi_ip或者lan_ip"""
    device_name = device_info.get('device_name')
    device_ip = device_info.get('ip')
    checked_ip = set()
    for i in range(3):
        if device_ip:
            ping_ret = cmd_is_device_connected(device_ip, retry=3)
            if ping_ret:
                device_info['ip'] = device_ip
                return device_ip
            checked_ip.add(device_ip)
        if 'wifi_ip' in device_info and device_info.get('wifi_ip') not in checked_ip:
            device_ip = device_info.get('wifi_ip')
        elif 'lan_ip' in device_info and device_info.get('lan_ip') not in checked_ip:
            device_ip = device_info.get('lan_ip')
        else:
            break
    aklog_warn(f'设备 {device_name} ip {device_ip} 连接失败')
    if is_raise:
        raise ValueError(f'设备 {device_name} ip {device_ip} 连接失败')
    return None


def cmd_check_always_offline_by_ping(ip, timeout=300):
    """子线程方式，检查设备是否长时间断开连接，如果在超时时间范围内，一直ping不通，则认为设备已经离线或异常"""
    end_time = time.time() + timeout
    while time.time() < end_time:
        ping_ret = cmd_get_ping_result(ip, ping_count=2)
        if ping_ret[0] > 0:
            return False
        time.sleep(5)
        continue
    return True


def cmd_set_stop_exec_by_ping(ip):
    ret = cmd_get_ping_result(ip)
    if ret[0] == 0:
        param_put_stop_exec_enable(True)
        return True
    else:
        return False


class WindowsLangCode(Enum):
    """
    语言代码值参考：https://msdn.microsoft.com/en-us/library/cc233982.aspx
    """
    EN = 0x4090409
    ZH = 0x4090804


def change_lan(lan: WindowsLangCode):
    """
    修改当前激活窗口输入法
    :param lan: 语言类型
    :return: True 修改成功，False 修改失败
    """
    aklog_printf('change_lan: %s' % lan.name)
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    aklog_printf('当前窗口标题: %s' % title)
    # 获取系统输入法列表
    print(win32api.GetKeyboardLayoutName())
    im_list = win32api.GetKeyboardLayoutList()
    im_list = list(map(hex, im_list))
    # print(im_list)
    # 加载输入法
    if hex(lan.value) not in im_list:
        win32api.LoadKeyboardLayout('0000' + hex(lan.value)[-4:], 1)

    result = win32api.SendMessage(
        hwnd,
        win32con.WM_INPUTLANGCHANGEREQUEST,
        0,
        lan.value)
    if result == 0:
        aklog_printf('设置%s键盘成功！' % lan.name)
    return result == 0


def change_language(lang="EN", force=False):
    """
    切换语言输入法
    :param lang: EN––English; ZH––Chinese
    :param force: ，是否强制切换语言输入法，不进行当前语言输入法的判断，True, False
    :return: bool
    """
    aklog_info('~~~~~~~~~~~~~~~~~~~~~~~~~~ debug ~~~~~~~~~~~~~~~~')
    aklog_info(locale.getlocale())
    aklog_printf('change_language: %s' % lang)
    LANG = {
        "ZH": 0x0804,
        "EN": 0x0409
    }
    language = LANG[lang]
    cur_keyboard_language = str(win32api.GetKeyboardLayoutName())[-4:]
    aklog_printf('current keyboard language: %s' % cur_keyboard_language)
    dst_keyboard_language_str = str(hex(language)).split('0x')[-1].rjust(4, '0')
    aklog_printf('dst keyboard language: %s' % dst_keyboard_language_str)
    if force or cur_keyboard_language != dst_keyboard_language_str:
        # Jenkins执行Python是后台运行的，GetForegroundWindow获取到当前激活的窗口为空，设置输入法会失败
        # 打开一个Windows自带的软件notepad.exe，作为当前激活的窗口，即可设置输入法了
        sub_process_exec_command('start notepad.exe')
        time.sleep(2)
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        aklog_printf('当前窗口标题: %s' % title)

        result = win32api.SendMessage(
            hwnd,
            win32con.WM_INPUTLANGCHANGEREQUEST,
            0,
            language
        )
        # 关闭打开的notepad.exe
        sub_process_exec_command('taskkill /F /im notepad.exe')
        if result == 0:
            aklog_printf('设置%s键盘成功！' % lang)
        return result == 0
    else:
        aklog_printf('当前输入法已经为: %s' % lang)


def cmd_get_network_rate(sec=1):
    """获取一段时间内的网卡平均速率，sec=1时，即实时速率"""
    try:
        start_time = time.time()
        if not pc_adapter_desc:
            cmd_get_network_adapter_description()
        present_flow = sub_process_get_output(
            'wmic path Win32_PerfRawData_Tcpip_NetworkInterface where "name like \'%%%s%%\'" '
            'get BytesTotalPersec|findstr "\\<[0-9]"' % pc_adapter_desc, timeout=10)
        if present_flow:
            present_flow = present_flow.strip()
        else:
            present_flow = 0
        cmd_execute_time = time.time() - start_time  # 等待时间要扣除掉获取流量数据命令执行的时间
        if cmd_execute_time > sec:
            cmd_execute_time = sec
        time.sleep(sec - cmd_execute_time)

        per_last_present_flow = sub_process_get_output(
            'wmic path Win32_PerfRawData_Tcpip_NetworkInterface where "name like \'%%%s%%\'" '
            'get BytesTotalPersec|findstr "\\<[0-9]"' % pc_adapter_desc, timeout=10)
        if per_last_present_flow:
            per_last_present_flow = per_last_present_flow.strip()
        else:
            per_last_present_flow = 0
        present_network_flow = round((int(per_last_present_flow) - int(present_flow)) / 1024 / sec, 2)
        aklog_printf("当前速率为：{} KB/S".format(present_network_flow))
        # 有些电脑环境获取流量数据超时失败，会导致WMIC.exe进程没有正常退出
        if present_flow == 0 or per_last_present_flow == 0:
            cmd_close_process_by_name('WMIC.exe')
        return present_network_flow
    except:
        aklog_printf(traceback.format_exc())
        return 0


def cmd_waiting_for_network_rate_to_drop(rate=2000, sec=3):
    """判断当前网卡速率，如果比较大，表明当前正在传输，等待直到速率降下来, 速率单位kbps"""
    if not config_get_value_from_ini_file('config', 'waiting_for_network_rate_to_drop'):
        aklog_printf('config配置项waiting_for_network_rate_to_drop为False，不检测')
        return True
    aklog_printf('cmd_waiting_for_network_rate_to_drop, rate: %s, sec: %s' % (rate, sec))
    for i in range(100):
        network_rate = cmd_get_network_rate(sec)
        if network_rate < rate:
            network_rate = cmd_get_network_rate(sec)
            if network_rate < rate:
                break
            else:
                time.sleep(3)
                continue
        elif i < 99:
            time.sleep(3)
            continue
        else:
            aklog_printf('等待时间超时，速率一直大于 %s KB/S，不再继续等待，请检查' % rate)
            return False
    aklog_printf('当前速率小于 %s KB/S ，表明当前没有在传输' % rate)
    return True


def cmd_get_current_nodejs_version():
    """获取当前使用的nodejs版本"""
    aklog_printf('cmd_get_current_nodejs_version')
    nvm_list = sub_process_get_output('nvm list')
    nvm_list = nvm_list.strip()
    versions = nvm_list.split('\n')
    current_node_version = ''
    for version in versions:
        if '*' in version:
            current_node_version = version.strip().split(' ')[1]
    aklog_printf(current_node_version)
    return current_node_version


def cmd_get_all_nodejs_version():
    """获取所有已安装的nodejs版本"""
    aklog_printf('cmd_get_all_nodejs_version')
    nvm_list = sub_process_get_output('nvm list')
    nvm_list = nvm_list.strip()
    versions = nvm_list.split('\n')
    version_list = []
    for version in versions:
        version = version.strip()
        if '*' in version:
            version = version.split(' ')[1]
        version_list.append(version)
    aklog_printf(version_list)
    return version_list


def cmd_switch_nodejs_version(switch_version):
    aklog_printf('cmd_switch_nodejs_version: %s' % switch_version)
    for i in range(2):
        nvm_list = sub_process_get_output('nvm list')
        nvm_list = nvm_list.strip()
        versions = nvm_list.split('\n')
        current_node_version = ''
        version_list = []
        for version in versions:
            version = version.strip()
            if '*' in version:
                version = version.split(' ')[1]
                current_node_version = version
            version_list.append(version)
        if current_node_version == switch_version:
            aklog_printf('当前nodejs版本已切换至 %s 版本' % switch_version)
            return True
        elif switch_version in version_list and i == 0:
            sub_process_exec_command('nvm use %s' % switch_version)
            time.sleep(1)
            continue
        elif switch_version not in version_list:
            aklog_printf('当前安装的nodejs没有包含 %s 版本' % switch_version)
            return False
        else:
            aklog_printf('切换至 %s 版本失败' % switch_version)
            return False


def cmd_clear_python_error_site_packages():
    """安装python第三方库时，如果site_packages存在~波浪线开头的文件夹，更新pip会失败，导致pip.exe丢失，
    所以在更新前先检查该目录是否存在~波浪线开头的文件夹，如果有就删除"""
    aklog_printf('cmd_clear_python_error_site_packages')
    for i in range(2):
        pip_path = sub_process_get_output('where pip')
        if pip_path:
            pip_path = pip_path.strip()
            site_packages_path = pip_path.replace(r'Scripts\pip.exe', '') + r'Lib\site-packages'
            aklog_printf('site_packages_path: %s' % site_packages_path)
            clear_flag = False
            for package in os.listdir(site_packages_path):
                if package.startswith('~'):
                    package_path = os.path.join(site_packages_path, package)
                    File_process.remove_dir(package_path)
                    clear_flag = True
            if clear_flag:
                time.sleep(10)
            aklog_printf('site-packages目录清理完成')
            break
        elif i == 0:
            aklog_printf('找不到pip，重新安装pip')
            sub_process_exec_command('curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py', timeout=120)
            sub_process_exec_command('python get-pip.py')
            time.sleep(3)
            continue
        else:
            aklog_printf('找不到pip，请检查python环境')


"""
测试代码
"""
if __name__ == '__main__':
    ret = cmd_is_device_connected("192.168.88.103")
    print(ret)
