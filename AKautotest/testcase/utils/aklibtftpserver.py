
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
import struct
import socket
import time
import traceback
import threading
from typing import Optional, Tuple

g_tftp_server_dir = root_path + '\\testfile\\tftp_server'


class TFTPServer:
    """TFTP服务器，支持多客户端并发上传/下载，支持自动关闭"""

    tftp_port = 69

    def __init__(self, directory_path: str, auto_shutdown: bool = False):
        """
        Args:
            directory_path (str): TFTP根目录
            auto_shutdown (bool): 文件传输完成后自动关闭服务
        """
        self.directory_path = os.path.abspath(directory_path)
        os.makedirs(self.directory_path, exist_ok=True)
        self._stop_event = threading.Event()
        self._server_socket: Optional[socket.socket] = None
        self._tftp_thread: Optional[threading.Thread] = None
        self._active_threads = set()
        self._lock = threading.Lock()
        self.auto_shutdown = auto_shutdown
        self._shutdown_triggered = False  # 防止多线程重复关闭
        aklog_debug(f"{self.__class__.__name__}.__init__, server dir: {self.directory_path},"
                    f" auto_shutdown={self.auto_shutdown}")

    def stop(self, wait_children: bool = True):
        """优雅关闭TFTP服务"""
        if self._stop_event.is_set():
            return  # 已关闭
        self._stop_event.set()
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception as e:
                aklog_warn(f"关闭socket异常: {e}")
        if self._tftp_thread:
            self._tftp_thread.join(timeout=5)
        if wait_children:
            with self._lock:
                threads = list(self._active_threads)
            for t in threads:
                t.join(timeout=10)
        aklog_debug("TFTPServer已关闭")

    def get_cur_tftp_port(self) -> int:
        return self.tftp_port

    @staticmethod
    def _ensure_parent_dir(file_path: str):
        parent_dir = os.path.dirname(file_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            aklog_debug(f"自动创建上传目录: {parent_dir}")

    def _auto_shutdown_check(self):
        """自动关闭服务，仅触发一次"""
        if self.auto_shutdown and not self._shutdown_triggered:
            self._shutdown_triggered = True
            aklog_debug("TFTPServer自动关闭")
            # 使用线程异步关闭，防止当前线程阻塞
            threading.Thread(target=self.stop, kwargs={'wait_children': False}, daemon=True).start()

    def upload_thread(self, file_path: str, client_info: Tuple[str, int]):
        """处理客户端上传文件"""
        aklog_debug()
        file_num = 0
        try:
            self._ensure_parent_dir(file_path)
            with open(file_path, 'wb') as f, \
                 socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(10)
                ack = struct.pack("!HH", 4, file_num)
                s.sendto(ack, client_info)
                file_num += 1
                while True:
                    try:
                        recv_data, addr = s.recvfrom(1024)
                    except socket.timeout:
                        aklog_warn(f"上传超时: {file_path}")
                        break
                    if len(recv_data) < 4:
                        aklog_warn("上传包长度异常")
                        continue
                    opcode, block = struct.unpack("!HH", recv_data[:4])
                    if opcode == 3 and block == file_num:
                        f.write(recv_data[4:])
                        ack = struct.pack("!HH", 4, file_num)
                        s.sendto(ack, addr)
                        file_num = (file_num + 1) % 65536
                        if len(recv_data) < 516:
                            aklog_debug(f"用户 {client_info}: 上传 {file_path} 完成")
                            self._auto_shutdown_check()  # 传输完成后自动关闭
                            break
                    else:
                        aklog_warn(f"上传包序号或操作码异常: opcode={opcode}, block={block}")
        except Exception as e:
            aklog_error(f"上传异常: {e}")

    def download_thread(self, file_path: str, client_info: Tuple[str, int]):
        """处理客户端下载文件"""
        aklog_debug()
        file_num = 0
        try:
            with open(file_path, 'rb') as f, \
                 socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(10)
                while True:
                    data = f.read(512)
                    file_num = (file_num + 1) % 65536
                    pkt = struct.pack('!HH', 3, file_num) + data
                    s.sendto(pkt, client_info)
                    if len(data) < 512:
                        aklog_debug(f"用户 {client_info}: 下载 {file_path} 完成")
                        self._auto_shutdown_check()  # 传输完成后自动关闭
                        break
                    try:
                        recv_data, addr = s.recvfrom(1024)
                    except socket.timeout:
                        aklog_warn(f"下载超时: {file_path}")
                        break
                    if len(recv_data) < 4:
                        aklog_warn("下载ACK包长度异常")
                        break
                    opcode, block = struct.unpack("!HH", recv_data[:4])
                    if opcode != 4 or block != file_num:
                        aklog_error("下载ACK包异常")
                        break
        except FileNotFoundError:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                error_pkt = struct.pack('!HHH', 5, 1, 0) + b'File not found\x00'
                s.sendto(error_pkt, client_info)
            aklog_error(f"文件不存在: {file_path}")
        except Exception as e:
            aklog_error(f"下载异常: {e}")

    def create_tftp_server(self):
        """主循环，支持多客户端并发"""
        aklog_debug()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            self._server_socket = s
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            for i in range(5):
                try:
                    s.bind(('', self.tftp_port))
                except OSError:
                    self.__class__.tftp_port += 1
                    aklog_warn('tftp 服务器端口号冲突.')
                else:
                    aklog_debug(f'tftp 服务器正常开启, 端口号: {self.tftp_port}')
                    break
            aklog_debug("tftp服务器成功启动! 正在运行中...")

            while not self._stop_event.is_set():
                try:
                    s.settimeout(1)
                    recv_data, client_info = s.recvfrom(1024)
                except socket.timeout:
                    continue
                except OSError:
                    break
                except Exception as e:
                    aklog_error(f"主循环接收异常: {e}")
                    continue

                # 解析请求
                if b'netascii' in recv_data or b'octet' in recv_data:
                    if len(recv_data) < 4:
                        aklog_warn("TFTP请求包长度异常")
                        continue
                    opcode = struct.unpack('!H', recv_data[:2])[0]
                    filename = recv_data[2:].split(b'\x00')[0].decode('utf-8', 'ignore')
                    file_path = os.path.join(self.directory_path, filename)
                    # aklog_info(f"收到请求: opcode={opcode}, file={file_path}, client={client_info}")
                    if opcode == 1:  # 下载
                        t = threading.Thread(
                            target=self._thread_wrapper,
                            args=(self.download_thread, file_path, client_info),
                            daemon=True)
                        self._register_thread(t)
                        t.start()
                    elif opcode == 2:  # 上传
                        t = threading.Thread(
                            target=self._thread_wrapper,
                            args=(self.upload_thread, file_path, client_info),
                            daemon=True)
                        self._register_thread(t)
                        t.start()
                    else:
                        aklog_warn(f"未知操作码: {opcode}")

    def _thread_wrapper(self, target, *args):
        """线程包装器，便于管理活跃线程"""
        t = threading.current_thread()
        try:
            target(*args)
        finally:
            with self._lock:
                self._active_threads.discard(t)

    def _register_thread(self, t: threading.Thread):
        """注册活跃线程"""
        with self._lock:
            self._active_threads.add(t)

    def thread_create_tftp_server(self):
        """以线程方式启动TFTP服务"""
        self._tftp_thread = threading.Thread(
            target=self.create_tftp_server, daemon=True)
        self._tftp_thread.start()


def thread_start_tftp_server(server_dir=None, auto_shutdown=True):
    """启动TFTP服务并返回实例
    Args:
        server_dir (str): TFTP根目录
        auto_shutdown (bool): 文件传输完成后自动关闭
    """
    if not server_dir:
        server_dir = g_tftp_server_dir
    tftp = TFTPServer(server_dir, auto_shutdown=auto_shutdown)
    tftp.thread_create_tftp_server()
    return tftp


def clear_tftp_server_dir(server_dir=None, file_ext='.jpg'):
    if not server_dir:
        server_dir = g_tftp_server_dir
    for i in os.listdir(server_dir):
        for j in range(2):
            try:
                if i.endswith(file_ext):
                    os.remove(os.path.join(server_dir, i))
            except:
                aklog_debug(traceback.format_exc())
                time.sleep(5)
            else:
                break


def get_tftp_server_jpg_amount(server_dir=None):
    if not server_dir:
        server_dir = g_tftp_server_dir
    amount = 0
    if os.path.exists(server_dir):
        for i in os.listdir(server_dir):
            if i.endswith('.jpg'):
                amount += 1
    return amount


"""demo"""
if __name__ == '__main__':
    thread_start_tftp_server()
    time.sleep(20)
