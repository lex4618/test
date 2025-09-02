# -*- coding: UTF-8 -*-

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
import serial
import time
import threading
import re
import traceback
import serial.tools.list_ports as list_ports
from typing import Optional, List, Dict


class SerialPortHandler:
    def __init__(self, port: str, baudrate: int = 115200, timeout: int = 1, write_timeout: int = 3, device_name=''):
        """
        初始化串口操作类
        :param port: 串口号，例如 'COM3' 或 '/dev/ttyUSB0'
        :param baudrate: 波特率，默认 9600
        :param timeout: 读取超时时间，单位为秒
        :param write_timeout: 写入超时时间，单位为秒
        """
        self.device_name = device_name
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.ser: Optional[serial.Serial] = None
        self.is_running = False
        self.log_file = None
        self.buffer = []  # 用于存储读取到的数据
        self.buffer_lock = threading.Lock()
        self.serial_lock = threading.Lock()
        self._read_thread = None
        self._watch_log_thread = None
        self._watch_log_stop_event = None
        self._watch_log_list = []  # 匹配到的日志内容

    def put_device_name(self, device_name):
        self.device_name = device_name

    @staticmethod
    def is_port_available(port):
        """检查串口是否可用"""
        ports = [p.device for p in list_ports.comports()]
        return port in ports

    def connect(self):
        """
        连接串口，连接前先断开已有连接，确保端口资源可用。

        Raises:
            RuntimeError: 串口不可用或连接失败
        """
        # 直接调用disconnect，确保资源彻底释放
        self.disconnect()
        time.sleep(1)

        aklog_debug()
        # 检查串口是否可用
        if not self.is_port_available(self.port):
            aklog_error(f"串口 {self.port} 不可用，请检查设备连接或配置。")
            raise RuntimeError(f"串口 {self.port} 不可用，请检查设备连接或配置。")

        try:
            self.ser = serial.Serial(
                self.port, self.baudrate, timeout=self.timeout, write_timeout=self.write_timeout)
            self.is_running = True
            aklog_info(f"成功连接到串口 {self.port}，波特率 {self.baudrate}。")
        except serial.SerialException as e:
            aklog_error(f"连接串口 {self.port} 失败: {e}")
            self.ser = None
            self.is_running = False
            raise RuntimeError(f"连接串口 {self.port} 失败: {e}")
        except Exception as e:
            aklog_error(f"未知异常导致串口连接失败: {e}")
            self.ser = None
            self.is_running = False
            raise RuntimeError(f"未知异常导致串口连接失败: {e}")

    def disconnect(self):
        """
        断开串口连接，安全释放资源，停止读取线程。

        Raises:
            Exception: 断开过程中发生的异常
        """
        aklog_debug()
        # 停止数据读取线程
        try:
            self.stop_reading()
        except Exception as e:
            aklog_warn(f"停止读取线程异常: {e}")

        # 关闭串口连接
        try:
            if hasattr(self, 'ser') and self.ser:
                if self.ser.is_open:
                    self.ser.close()
                    aklog_debug(f"已断开串口 {self.port}。")
                self.ser = None
            self.is_running = False
        except Exception as e:
            aklog_error(f"断开串口 {self.port} 失败: {e}")
            # 不抛出异常，保证幂等性

    def __enter__(self):
        """支持with语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出with时自动关闭串口"""
        self.disconnect()

    def is_connected(self):
        """
        判断当前串口是否已连接
        """
        # 检查串口对象是否存在，并且是否处于打开状态
        return self.ser is not None and self.ser.is_open

    def is_communicable(self, probe_cmd: bytes = b'\r\n', wait_time: float = 1.0) -> bool:
        """
        判断串口是否真正可通信（设备未休眠）
        :param probe_cmd: 探测命令，默认发送换行符
        :param wait_time: 等待响应时间（秒）
        :return: True 表示设备响应，False 表示无响应（可能休眠）
        """
        if not self.is_connected():
            aklog_warn(f"串口未连接，无法通信判断")
            return False

        try:
            # 清空输入输出缓冲区
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            # 发送探测命令
            self.ser.write(probe_cmd)
            aklog_debug(f"发送探测命令: {probe_cmd}")

            # 等待响应
            time.sleep(wait_time)

            if self.ser.in_waiting:
                response = self.ser.read(self.ser.in_waiting)
                aklog_debug(f"收到响应: {response}")
                return True
            else:
                aklog_warn(f"无响应，可能设备休眠")
                return False

        except Exception as e:
            aklog_error(f"通信检测异常: {e}")
            return False

    def wait_serial_shell_ready(self, timeout=30, event: threading.Event = None) -> bool:
        """
        等待串口开始打印日志（从buffer读取）,检测到后设置ready_event
        :param timeout: 等待日志输出的最大时间（秒）
        :param event: 线程同步事件
        :return: True-可交互，False-超时未就绪
        """
        if not self.is_connected():
            aklog_warn("串口未连接，无法等待就绪")
            return False

        aklog_debug("等待串口开始打印新日志...")
        with self.buffer_lock:
            start_index = len(self.buffer)  # 记录当前buffer长度

        end_time = time.time() + timeout
        while time.time() < end_time:
            time.sleep(0.1)
            # 只在锁内做buffer快照，提升并发性能
            with self.buffer_lock:
                buffer_snapshot = list(self.buffer)
            new_lines = buffer_snapshot[start_index:]
            if new_lines:
                for line in new_lines:
                    if line:
                        aklog_debug(f"串口开始输出新日志: {line}")
                        if event:
                            event.set()  # 通知主线程
                        return True

        aklog_warn("串口在指定时间内无新日志输出")
        return False

    def wait_serial_sleep(self, sleep_flag=None, timeout=30, stable_time=5):
        """
        等待串口不再打印新的日志（设备休眠）

        Args:
            sleep_flag (str): 设备休眠的标志log
            timeout (int): 等待超时时间，单位秒。
            stable_time (int): 串口日志输出稳定（无新日志）的时间，单位秒。

        Returns:
            bool: 如果在超时时间内检测到串口稳定返回True，否则返回False。
        """
        aklog_debug()

        if not self.is_connected():
            aklog_warn("串口未连接，无法等待就绪")
            return False

        aklog_debug("等待串口停止打印新日志...")

        checked_line_idx = 0
        with self.buffer_lock:
            checked_line_idx = len(self.buffer)

        last_buffer_len = checked_line_idx  # 记录初始日志长度
        stable_start_time = None  # 稳定期起始时间
        end_time = time.time() + timeout  # 计算超时时间点

        while time.time() < end_time:
            time.sleep(0.1)  # 每100ms检查一次

            # 只在锁内做buffer快照，提升并发性能
            with self.buffer_lock:
                buffer_snapshot = list(self.buffer)
            current_buffer_len = len(buffer_snapshot)  # 当前日志长度

            # 检查是否出现休眠标志log
            if sleep_flag:
                # 只检查最新的日志内容，提升效率
                for i in range(checked_line_idx, current_buffer_len):
                    line = buffer_snapshot[i]
                    if sleep_flag in line:
                        aklog_debug(f"检测到休眠标志log: '{sleep_flag}'，判定设备休眠")
                        time.sleep(2)
                        return True
                checked_line_idx = current_buffer_len  # 更新已检查的行数

            if current_buffer_len == last_buffer_len:
                # 日志长度未变化，可能进入稳定期
                if stable_start_time is None:
                    stable_start_time = time.time()  # 记录稳定期开始时间
                elif time.time() - stable_start_time >= stable_time:
                    # 已经稳定足够时间
                    aklog_debug(f"串口日志已稳定{stable_time}秒，判定设备休眠")
                    return True
            else:
                # 日志有新输出，重置稳定期
                stable_start_time = None
                last_buffer_len = current_buffer_len  # 更新最新长度

        aklog_warn("串口未在指定时间内停止")
        return False

    def _try_reconnect(self, max_retry=5, retry_interval=2):
        """
        尝试自动重连串口
        :param max_retry: 最大重试次数
        :param retry_interval: 重试间隔（秒）
        :return: True-重连成功，False-重连失败
        """
        with self.serial_lock:
            aklog_warn("检测到串口未连接，尝试自动重连...")
            for i in range(max_retry):
                try:
                    self.connect()  # 你的串口连接方法
                    if self.ser and self.ser.is_open:
                        aklog_info(f"串口重连成功（第{i + 1}次）")
                        return True
                except Exception as e:
                    aklog_warn(f"第{i + 1}次重连串口失败: {e}")
                time.sleep(retry_interval)
            aklog_error("串口重连失败，已达到最大重试次数")
            return False

    def read_data(self):
        """
        持续读取串口数据，异常自动重试，提升健壮性
        :return: None
        """
        aklog_debug()
        retry_count = 0  # 异常重试计数
        max_retry = 5  # 最大连续异常次数
        retry_interval = 2  # 异常后等待时间（秒）

        while self.is_running:
            try:
                if not self.ser or not self.ser.is_open:
                    # 检测到串口未连接，自动重连
                    if not self._try_reconnect():
                        aklog_error("串口多次重连失败，终止读取线程。")
                        break
                    continue  # 重连成功后继续读取

                if self.ser.in_waiting > 0:  # 检查是否有数据可读
                    data = self.ser.readline()  # 读取一行数据
                    try:
                        decoded_data = data.decode('utf-8').strip()  # 尝试解码
                    except UnicodeDecodeError:
                        try:
                            decoded_data = data.decode('latin-1').strip()  # 使用 latin-1 解码
                        except UnicodeDecodeError as e:
                            aklog_warn(f'UnicodeDecodeError: {e}')
                            decoded_data = ''
                    timestamp = aklog_get_current_time()
                    log_line = f"[{timestamp}] {decoded_data}"
                    # 保存到缓冲区，增加线程锁，避免日志丢失
                    with self.buffer_lock:
                        self.buffer.append(log_line)
                    retry_count = 0  # 读取成功，异常计数清零
                else:
                    time.sleep(0.01)
            except Exception as e:
                aklog_error(f"Serial read error: {e}")
                retry_count += 1
                if retry_count >= max_retry:
                    aklog_error(f"Serial port连续{max_retry}次读取异常，终止读取线程。")
                    aklog_debug(traceback.format_exc())
                    break  # 达到最大重试次数，退出
                time.sleep(retry_interval)  # 等待后重试

    def get_log_buffer(self) -> str:
        with self.buffer_lock:
            return '\n'.join(self.buffer)

    def clear_log_buffer(self):
        with self.buffer_lock:
            self.buffer.clear()

    def write_data(self, data: str, end: str = '\n', write_timeout=None):
        """
        向串口发送数据（带写入超时与异常恢复）

        Args:
            data (str): 要发送的字符串内容
            end (str, optional): 命令结尾符，默认 '\\n'，可根据设备协议调整
            write_timeout (float, optional): 串口写入超时时间（秒），默认 3 秒
        """
        try:
            # 检查串口连接状态
            if not self.ser or not self.ser.is_open:
                raise Exception("Serial port is not open. Please connect first.")

            # 更新写入超时（确保每次调用都能动态调整）
            if write_timeout:
                self.ser.write_timeout = write_timeout

            # 自动补全结尾符（避免重复添加）
            if not data.endswith(end):
                data += end

            # 串口写入数据（可能会阻塞）
            self.ser.write(data.encode("utf-8"))  # 发送数据
            self.ser.flush()  # 确保数据实际写入
            aklog_info(f"Sent to serial: {repr(data)}")
            if write_timeout:
                self.ser.write_timeout = self.write_timeout  # 还原默认

        except serial.SerialTimeoutException:
            # 写入超时异常处理
            aklog_error(f"Serial write timeout after {write_timeout} seconds. Data: {repr(data)}")
            self._try_reconnect()

        except (serial.SerialException, OSError) as e:
            # 串口硬件/驱动异常
            aklog_error(f"Serial write failed due to hardware/driver error: {e}")
            self._try_reconnect()

        except Exception as e:
            # 兜底异常捕获
            aklog_fatal(f"Unexpected error while writing to serial: {e}")
            self._try_reconnect()

    def save_to_file(self, file_path: str, clear_buffer=True):
        """
        保存串口数据到文件
        :param file_path: 文件路径
        :param clear_buffer: 是否清理缓存的日志
        """
        if not self._read_thread or not self.is_running:
            aklog_debug('未开启串口日志抓取')
            return
        with self.buffer_lock:
            buffer_snapshot = list(self.buffer)
            if clear_buffer:
                self.buffer.clear()
        if not buffer_snapshot:
            aklog_debug('未获取到串口日志')
            return
        with open(file_path, "a", encoding="utf-8") as f:
            for line in buffer_snapshot:
                f.write(f'{line}\n')
        aklog_info(f"Save data to file: {file_path}")

    def check_log(
            self,
            *keywords,
            timeout: int = 60,
            clear_buffer=False,
            just_one=False,
            stop_flag=None,
            regex_mode=False,
            check_latest=False
    ) -> List[dict]:
        """
        检查串口是否打印特定日志，支持正则表达式匹配、出现stop_flag提前结束。

        Args:
            *keywords (str|re.Pattern): 要检查的关键字，可以为字符串或正则表达式。
            timeout (int): 超时时间，单位为秒。
            clear_buffer (bool): 是否先清理缓存的日志。
            just_one (bool): 如果关键字有多个，是否只找到一个即可返回。
            stop_flag (str): 结束检查的log标志，出现即提前结束。
            regex_mode (bool): 是否启用正则表达式匹配，默认True。
            check_latest (bool): 是否只检查最新的log，为False时，会从缓存的日志buffer[0]开始检查
        Returns:
            list: 返回找到关键字的那一行log或正则分组内容（如有），结构如下：
                [
                    {"keyword": <原始关键字>, "line": <日志行>, "match": <正则Match对象或None>, "groups": <分组内容或None>}
                ]
        """
        aklog_debug()

        checked_line_idx = 0  # 已检查的行数索引
        if clear_buffer:
            with self.buffer_lock:
                self.buffer.clear()
        elif check_latest:
            with self.buffer_lock:
                checked_line_idx = len(self.buffer)

        log_list = []
        keyword_checked = []
        end_time = time.time() + timeout

        # 预编译正则表达式
        compiled_keywords = []
        for kw in keywords:
            if regex_mode:
                if isinstance(kw, re.Pattern):
                    compiled_keywords.append(kw)
                else:
                    compiled_keywords.append(re.compile(re.escape(str(kw))))  # 加re.escape自动转义
            else:
                compiled_keywords.append(kw)

        while time.time() < end_time:
            time.sleep(0.1)

            # 检查读取线程健康状态
            if not self._read_thread or not self._read_thread.is_alive():
                aklog_warn("串口读取线程异常，尝试重启读取线程。")
                try:
                    self.start_reading()
                    aklog_info("串口读取线程已重启。")
                except Exception as e:
                    aklog_error(f"串口读取线程重启失败: {e}")

            # 只在锁内做buffer快照，提升并发性能
            with self.buffer_lock:
                buffer_snapshot = list(self.buffer)
            buffer_len = len(buffer_snapshot)

            # 检查stop_flag
            if stop_flag:
                for i in range(checked_line_idx, buffer_len):
                    line = buffer_snapshot[i]
                    if stop_flag in line:
                        aklog_debug(f"检测到停止标志log: '{stop_flag}'，提前结束检查")
                        return log_list

            # 检查关键字（支持正则）
            for idx, keyword in enumerate(compiled_keywords):
                if idx in keyword_checked:
                    continue
                for i in range(checked_line_idx, buffer_len):
                    line = buffer_snapshot[i]
                    if regex_mode:
                        match = keyword.search(line)
                        if match:
                            aklog_debug(f"正则匹配到关键字 '{keywords[idx]}' in log line: {line}")
                            log_list.append({
                                "keyword": keywords[idx],
                                "line": line,
                                "match": match,
                                "groups": match.groups() if match.groups() else match.group(0)
                            })
                            keyword_checked.append(idx)
                            if just_one:
                                return log_list
                            break
                    else:
                        if str(keyword) in line:
                            aklog_debug(f"Found keyword '{keywords[idx]}' in log line: {line}")
                            log_list.append({
                                "keyword": keywords[idx],
                                "line": line,
                                "match": None,
                                "groups": None
                            })
                            keyword_checked.append(idx)
                            if just_one:
                                return log_list
                            break

            checked_line_idx = buffer_len  # 更新已检查的行数

            # 如果找到所有关键字，直接返回
            if not just_one and len(log_list) == len(keywords):
                return log_list

        not_found_keywords = [keywords[i] for i in range(len(keywords)) if i not in keyword_checked]
        aklog_debug(f"Keyword [{not_found_keywords}] not found within {timeout} seconds.")
        return log_list

    def start_watch_log(self, *keywords, regex_mode=False):
        """
        开启子线程监控串口日志，发现关键字自动输出日志。

        Args:
            *keywords (str|re.Pattern): 需要监控的关键字，可以为字符串或正则表达式。
            regex_mode (bool): 是否启用正则表达式匹配，默认False。
        """
        # 如果已有监控线程在运行，先停止
        self.stop_watch_log()

        if self._watch_log_stop_event:
            self._watch_log_stop_event.clear()  # 清除停止标志
        self._watch_log_list = []

        def _watch_log_worker():
            """日志监控线程主函数"""
            checked_line_idx = 0  # 已检查的行数索引

            # 预编译正则表达式
            compiled_keywords = []
            for kw in keywords:
                if regex_mode:
                    if isinstance(kw, re.Pattern):
                        compiled_keywords.append(kw)
                    else:
                        compiled_keywords.append(re.compile(str(kw)))
                else:
                    compiled_keywords.append(kw)

            while not self._watch_log_stop_event.is_set():
                time.sleep(0.1)
                with self.buffer_lock:
                    buffer_snapshot = list(self.buffer)
                buffer_len = len(buffer_snapshot)

                for idx, keyword in enumerate(compiled_keywords):
                    for i in range(checked_line_idx, buffer_len):
                        line = buffer_snapshot[i]
                        if regex_mode:
                            match = keyword.search(line)
                            if match:
                                log_item = {
                                    "keyword": keywords[idx],
                                    "line": line,
                                    "match": match,
                                    "groups": match.groups() if match.groups() else match.group(0)
                                }
                                aklog_debug(f"[监控] 正则匹配到关键字 '{keywords[idx]}' in log: {line}")
                                self._watch_log_list.append(log_item)
                        else:
                            if str(keyword) in line:
                                log_item = {
                                    "keyword": keywords[idx],
                                    "line": line,
                                    "match": None,
                                    "groups": None
                                }
                                aklog_info(f"[监控] 发现关键字 '{keywords[idx]}' in log: {line}")
                                self._watch_log_list.append(log_item)
                checked_line_idx = buffer_len  # 更新已检查的行数

            aklog_debug("日志监控线程已停止")

        # 启动守护线程
        self._watch_log_thread = threading.Thread(
            target=_watch_log_worker, name="WatchLogThread", daemon=True)
        self._watch_log_thread.start()
        aklog_debug("已启动日志监控线程")

    def stop_watch_log(self):
        """
        停止监控日志线程。
        """
        if self._watch_log_thread and self._watch_log_thread.is_alive():
            self._watch_log_stop_event.set()  # 设置停止标志
            self._watch_log_thread.join(timeout=3)  # 等待线程退出
            if self._watch_log_thread.is_alive():
                aklog_warn("日志监控线程未能正常停止")
            else:
                aklog_debug("日志监控线程已成功停止")
        self._watch_log_thread = None

        # 返回所有已匹配到的日志内容
        log_list = list(self._watch_log_list)
        aklog_debug(f"本次监控共匹配到{len(log_list)}条日志，内容如下：")
        for item in log_list:
            aklog_debug(item)
        self._watch_log_list = []
        return log_list

    def get_log_lines(self, keyword: str, timeout: int = 60, require_num=1, clear_buffer=False) -> list:
        """
        从串口日志中获取指定关键字出现的行

        Args:
            keyword (str): 要检查的关键字
            timeout (int): 超时时间，单位为秒
            require_num (int): 关键字存在的行数必须要达到的数值
            clear_buffer (bool): 是否先清理缓存的日志

        Returns:
            list: 返回找到关键字的那一行log
        """
        aklog_debug()

        if not keyword:
            aklog_error("get_log_lines: keyword不能为空")
            return []

        if require_num < 1:
            aklog_warn(f"get_log_lines: require_num参数非法({require_num})，已自动修正为1")
            require_num = 1

        try:
            if clear_buffer:
                with self.buffer_lock:
                    self.buffer.clear()
                aklog_debug("串口日志缓存已清空")

            log_list = []
            end_time = time.time() + timeout
            checked_line_idx = 0  # 已检查的行数索引

            while time.time() < end_time:
                # 只在锁内做buffer快照，提升并发性能
                with self.buffer_lock:
                    buffer_snapshot = list(self.buffer)  # 快照当前buffer内容
                buffer_len = len(buffer_snapshot)
                for i in range(checked_line_idx, buffer_len):
                    line = buffer_snapshot[i]
                    if keyword in line:
                        log_list.append(line)  # 匹配到关键字，加入结果列表
                        aklog_debug(f"匹配到关键字[{keyword}]的日志行: {line.strip()}")
                checked_line_idx = buffer_len  # 更新已检查的行数

                if len(log_list) >= require_num:
                    aklog_info(f"已找到{len(log_list)}行包含关键字[{keyword}]的日志，提前返回")
                    return log_list

                time.sleep(0.1)  # 等待一段时间再检查

            # 超时未找到足够的日志
            if len(log_list) < require_num:
                aklog_warn(
                    f"超时{timeout}s，仅找到{len(log_list)}行包含关键字[{keyword}]的日志，未满足期望数量{require_num}")

            return log_list

        except Exception as e:
            aklog_error(f"get_log_lines执行异常: {e}")
            aklog_debug(traceback.format_exc())
            return []

    def start_reading(self):
        """启动读取线程"""
        if not self.ser or not self.ser.is_open:
            raise Exception("Serial port is not open. Please connect first.")

        self.buffer.clear()
        self.is_running = True

        with self.serial_lock:
            # 检查线程状态，避免重复启动
            if self._read_thread and self._read_thread.is_alive():
                aklog_debug("读取线程已在运行")
                return

            self._read_thread = threading.Thread(target=self.read_data, daemon=True)
            self._read_thread.start()
            aklog_debug("Started reading thread.")
            time.sleep(1)

    def stop_reading(self):
        """停止读取线程"""
        self.is_running = False
        if self._read_thread is None:
            return
        if self._read_thread.is_alive():
            self._read_thread.join()
        self._read_thread = None
        aklog_debug("Stopped reading thread.")


def write_data_to_serial_port(port, baudrate, data, timeout=1):
    aklog_info()
    # 打开串口
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        aklog_info(f'打开串口 {port} 成功')
    except serial.SerialException as e:
        aklog_error(f'无法打开串口 {port}: {e}')
        return

    try:
        # 写入数据
        hex_string = bytes.fromhex(data)
        ser.write(hex_string)
        aklog_info(f'发送数据: {hex_string}')

        # 等待应答
        time.sleep(1)  # 等待一段时间以接收应答

        # 读取应答
        response = ser.read_all()
        if response:
            aklog_info(f'接收到应答: {response}')
        else:
            aklog_error('未接收到应答')
    except serial.SerialException as e:
        aklog_error(f'串口通信错误: {e}')
    finally:
        # 关闭串口
        time.sleep(10)
        ser.close()
        aklog_info(f'关闭串口 {port}')


def read_data_from_serial_port(port, baudrate, timeout=1):
    # 串口配置

    # 打开串口
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print(f'打开串口 {port} 成功')
    except serial.SerialException as e:
        print(f'无法打开串口 {port}: {e}')
        return

    try:
        while True:
            try:
                # 读取数据
                data = ser.readline()  # 读取一行数据，直到遇到换行符
                if data:
                    # print(data)
                    print(f'接收到数据: {data.decode("utf-8", errors="ignore")}')  # 输出数据并去除换行符
                else:
                    print('未接收到数据')
            except Exception as e:
                print(e)
    except serial.SerialException as e:
        print(f'串口通信错误: {e}')
    except KeyboardInterrupt:
        print('用户中断')
    finally:
        # 关闭串口
        ser.close()
        print(f'关闭串口 {port}')


def generate_unique_mac():
    # 获取当前时间的时间戳，单位为微秒
    timestamp = int(time.time() * 1_000_000)

    # 将时间戳转换为十六进制字符串，并取后12个字符
    hex_timestamp = f"{timestamp:012x}"[-12:]

    # 确保每个十六进制字符串的第一位不是数字
    def ensure_alpha_first_char(hex_str):
        if hex_str[0].isdigit():
            # 将第一位替换为字母A-F中的随机一个
            hex_str = random.choice('abcdef') + hex_str[1:]
        return hex_str

    # 生成随机的前两个字节，以确保 MAC 地址的前缀不同
    random_prefix = f"{random.randint(0, 255):02x}{random.randint(0, 255):02x}"

    # 确保前缀和时间戳后缀的每个字节第一位不是数字
    random_prefix = ensure_alpha_first_char(random_prefix[:2]) + ensure_alpha_first_char(random_prefix[2:])
    hex_timestamp = ''.join(ensure_alpha_first_char(hex_timestamp[i:i + 2]) for i in range(0, 12, 2))

    # 合并随机前缀和时间戳后缀生成 MAC 地址
    mac_address = f"{random_prefix}{hex_timestamp}"

    # 格式化 MAC 地址为标准格式
    mac_address = ' '.join(mac_address[i:i + 2] for i in range(0, 12, 2))
    mac_address = 'e1 00 08 11 a3 ' + mac_address
    aklog_info(mac_address)
    return mac_address


def serial_port_check_log(port, baudrate, *log_flags, timeout=60):
    """检查串口是否打印特定日志"""
    port_handler = None
    try:
        port_handler = SerialPortHandler(port=port, baudrate=baudrate)
        # 连接串口
        port_handler.connect()
        # 开始读取数据
        port_handler.start_reading()

        # 检查是否打印了特定日志
        log_list = port_handler.check_log(*log_flags, timeout=timeout)

        # 停止读取数据
        port_handler.stop_reading()

    finally:
        # 断开串口连接
        if port_handler is not None:
            port_handler.disconnect()
    return log_list


if __name__ == '__main__':
    serial_handler = SerialPortHandler('COM11', 115200)
    serial_handler.connect()
    serial_handler.start_reading()
    serial_handler.wait_serial_sleep('system sleep now!')
