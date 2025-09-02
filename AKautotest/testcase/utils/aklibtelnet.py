import sys
import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
if root_path not in sys.path:
    sys.path.append(root_path)

from akcommon_define import *
from testcase.utils.aklibthread import AkThread
import telnetlib
import time
import traceback


class TelnetConnection(object):

    def __init__(self, host=None, port=23, username=None, password=None, device_name=''):
        self.__tln_thread = None
        self.__telnet: Optional[telnetlib.Telnet] = None
        self.__prefix = ''
        self.__prefix_list = []
        self.stop_command_flag = False
        self.__host = None
        self.__port = 23
        self.__port_list = [23]
        self.__username = 'root'
        self.__password = ''
        self.__pwd_list = None
        self.device_name = ''
        self.rt_result = None
        if host and username:
            self.init(host, port, username, password, device_name)

    def init(self, host, port, username, password, device_name=''):
        self.__host = host
        self.device_name = device_name

        if isinstance(port, int):
            self.__port_list = [port]
            self.__port = port
            if 23 not in self.__port_list:
                self.__port_list.append(23)
        elif isinstance(port, list):
            self.__port_list = port
            self.__port = port[0]

        self.__username = username

        if isinstance(password, str):
            self.__pwd_list = [password]
            self.__password = password
        elif isinstance(password, list):
            self.__pwd_list = password
            self.__password = password[0]

    def close(self):
        if self.__telnet is not None:
            self.__telnet.close()
            self.__telnet = None

    # 此函数实现telnet登录主机
    def login_host(self, timeout=10):
        if self.__telnet is None:
            self.__telnet = telnetlib.Telnet()
        j = 1
        while True:
            try:
                aklog_printf('telnet连接: %s:%s' % (self.__host, self.__port))
                self.__telnet.open(self.__host, self.__port, timeout=timeout)
                self.sort_port_list()
                break
            except ConnectionRefusedError:
                aklog_printf('%s:%s 连接失败' % (self.__host, self.__port))
                if j < len(self.__port_list):
                    self.__port = self.__port_list[j]
                    j += 1
                    continue
                else:
                    aklog_printf('%s:%s 连接失败, %s' % (self.__host, self.__port, traceback.format_exc()))
                    self.__telnet = None
                    # 设备原本portlist[0]可以连接, 但因为突然重启等导致之后正确端口也无法连接, self.__port索引被拉到了最后, 需要复位原本的port以能够开始下次的循环
                    self.__port = self.__port_list[0]
                    return False
            except:
                aklog_printf('%s:%s 连接失败, %s' % (self.__host, self.__port, traceback.format_exc()))
                self.__telnet = None
                self.__port = self.__port_list[0]
                return False

        i = 1
        while True:
            try:
                aklog_printf('user: %s, password: %s' % (self.__username, self.__password))
                # 等待login出现后输入用户名，最多等待10秒
                self.__telnet.read_until(b'login: ', timeout=10)
                self.__telnet.write(self.__username.encode('utf-8') + b'\n')
                # 等待Password出现后输入用户名，最多等待10秒
                self.__telnet.read_until(b'Password: ', timeout=10)
                self.__telnet.write(self.__password.encode('utf-8') + b'\n')
                # 等待#号出现，说明登录成功，然后再回车一次，获取#号前的内容，最多等待10秒
                self.__telnet.read_until(b'#', timeout=5)
                self.__telnet.write(b'\n')
                time.sleep(0.5)
                # 获取登录结果
                # read_very_eager()获取到的是上次获取之后本次获取之前的所有输出 读取前需要等待时间
                command_result = self.__telnet.read_very_eager().decode('utf-8')
                self.__prefix = str(command_result).strip()  # #号前的内容，包含#号
                if not self.__prefix.encode('utf-8') in self.__prefix_list:
                    if '$' in self.__prefix:
                        # C310 $结尾也需要处理
                        self.__prefix = self.__prefix.replace(r'$', r'\$')
                    if '(' in self.__prefix and ')' in self.__prefix:
                        self.__prefix = self.__prefix.replace(r'(', r'\(').replace(r')', r'\)')
                    if '[' in self.__prefix and ']' in self.__prefix:
                        # E16V2 prefix: [root@RV1126_RV1109:~]#   每次都超时60秒
                        self.__prefix = self.__prefix.replace(r'[', r'\[').replace(r']', r'\]')
                    self.__prefix_list.append(self.__prefix.encode('utf-8'))
                if '~ ' in self.__prefix and ' #'.encode('utf-8') not in self.__prefix_list:
                    # 如果前缀带有~，说明前缀会显示目录，如果切换目录后，前缀会改变，因此等待前缀得增加#
                    self.__prefix_list.append(' #'.encode('utf-8'))
                if 'login: ' not in command_result:
                    aklog_printf(f'{self.__host} 登录成功, prefix: {self.__prefix}')
                    self.sort_pwd_list()
                    return True
                elif i < len(self.__pwd_list):
                    self.__password = self.__pwd_list[i]
                    self.__telnet.write(b'\n')
                    i += 1
                    continue
            except:
                aklog_printf('未知异常，请检查, %s' % traceback.format_exc())
                self.__telnet = None
                return False
        aklog_printf('%s登录失败，用户名或密码错误' % self.__host)
        self.__telnet = None
        return False

    def sort_port_list(self):
        # 重新排序端口列表，将连接成功的端口放在第一位
        self.__port_list.remove(self.__port)
        self.__port_list.insert(0, self.__port)

    def sort_pwd_list(self):
        # 重新排序密码列表，将连接成功的密码放在第一位
        self.__pwd_list.remove(self.__password)
        self.__pwd_list.insert(0, self.__password)

    def get_port_list(self):
        return self.__port_list

    def get_pwd_list(self):
        return self.__pwd_list

    def exec_command(self, command, timeout=2):
        """执行命令，不获取返回结果"""
        if not self.__telnet:
            return False
        # 执行命令
        aklog_printf()
        try:
            # 清空缓冲区，确保无历史残留
            self._clear_telnet_buffer()
            time.sleep(0.1)
            self.__telnet.write(command.encode('utf-8') + b'\n')
            self.__telnet.expect(self.__prefix_list, timeout=timeout)
            return True
        except Exception as e:
            aklog_error(e)
            return False

    def command_without_result(self, command, timeout=2):
        return self.exec_command(command, timeout)

    def command_result(self, command, timeout=10):
        """执行命令，并返回其执行结果"""
        if not self.__telnet:
            return None
        # 执行命令
        aklog_printf()
        try:
            # 清空缓冲区，确保无历史残留
            self._clear_telnet_buffer()
            time.sleep(0.1)
            self.__telnet.write(command.encode('utf-8') + b'\n')

            # 获取命令结果
            index, match, output = self.__telnet.expect(self.__prefix_list, timeout=timeout)
            result = output.decode('utf-8', errors='ignore')
            results = result.split('\r\n')
            # print(results)
            result_list = []
            command1 = ''
            for line in results:
                line = line.strip()
                command1 = command1 + line  # 前面几个元素拼接一起就是command，实际结果是在命令之后
                if command1 not in command and line != self.__prefix:
                    result_list.append(line)

            if len(result_list) > 1:  # 多行打印多行字符串，每一行都加回车
                result_str = "\n".join(result_list)
            else:
                result_str = "".join(result_list)
                if self.__prefix:
                    result_str = result_str.split(self.__prefix)[0]
            return result_str
        except:
            aklog_error('执行命令出现异常: %s' % traceback.format_exc())
            return None

    def _clear_telnet_buffer(self, retry=10):
        """
        清空telnet缓冲区，丢弃所有残留内容，防止提示符残留影响后续判断。
        连续两次读取都为空才认为彻底清空，sleep时间在第4次及以后逐步递增。

        Args:
            retry (int): 最大清理次数，防止死循环
        """
        empty_count = 0  # 连续空读计数
        max_sleep = 0.8
        for i in range(retry):
            data = self.__telnet.read_very_eager()
            if not data:
                empty_count += 1
                if empty_count >= 2:  # 连续两次都为空
                    return True
            else:
                empty_count = 0  # 只要有数据，计数清零

            # sleep递增策略：前3次0.1s，之后每次翻倍，最大0.8s
            if i < 3:
                sleep_time = 0.1
            else:
                sleep_time = min(0.1 * (2 ** (i - 2)), max_sleep)
            time.sleep(sleep_time)  # 等待设备可能的后续输出
        aklog_warn(f'尝试{retry}次后，仍未清空缓冲区')
        return False

    def exec_sql(self, sqlcipher_path, db_path, db_key, sql, timeout=10):
        """
        进入sqlcipher，执行SQL，返回结果
        Args:
            sqlcipher_path (str): sqlit3程序路径
            db_path (str): 数据库文件路径
            db_key (str): 数据库密钥
            sql (str): 要执行的SQL语句
            timeout (int):
        Returns:
            str: SQL执行结果
        """
        try:
            sql_prefix = b"sqlite>"
            # 清空缓冲区，确保无历史残留
            self._clear_telnet_buffer()
            time.sleep(0.1)
            # 进入sqlcipher
            self.__telnet.write(f"{sqlcipher_path} {db_path}\n".encode('utf-8'))
            time.sleep(1)
            self.__telnet.read_until(sql_prefix)  # 等待sqlite提示符
            # 输入密钥
            self.__telnet.write(f"PRAGMA key={db_key};\n".encode('utf-8'))
            time.sleep(0.5)
            self.__telnet.read_until(sql_prefix)
            # 执行SQL
            if not sql.endswith(';'):
                sql += ';\n'
            self.__telnet.write(sql.encode('utf-8'))
            time.sleep(1)
            output = self.__telnet.read_until(
                sql_prefix, timeout=timeout).decode('utf-8', errors='ignore')
            # 退出
            self.__telnet.write(b".exit\n")
            self.__telnet.write(b'\x03')
            self.__telnet.write(b'\x03')
            self.__telnet.write(b'\x03')
            return output
        except Exception as e:
            aklog_error(f"SQL执行失败: {e}")
            return None

    def is_connected(self):
        """是否连接正常处于等待命令输入状态"""
        aklog_debug()
        if self.__telnet is None:
            aklog_debug('telnet连接还未建立')
            return False
        try:
            # 清空缓冲区，确保无历史残留
            self._clear_telnet_buffer()
            time.sleep(0.1)
            self.__telnet.write(b'\n')
            index, match, output = self.__telnet.expect(self.__prefix_list, timeout=2)
            if match is not None:
                aklog_debug("telnet连接正常")
                return True
            else:
                aklog_debug("telnet连接异常，或者当前有命令在持续执行")
                return False
        except Exception as e:
            aklog_debug(f"telnet连接已关闭: {e}")
            try:
                self.__telnet.close()
            except:
                pass
            self.__telnet = None
            return False

    # 此函数实现执行传过来的命令，并输出其执行结果
    def command_result_all(self, command, timeout=60):
        """执行命令，并返回其执行结果"""
        if not self.__telnet:
            return None
        aklog_printf()
        self.__telnet.write(command.encode('utf-8') + b'\n')
        # time.sleep(2)
        # 获取命令结果
        index, match, output = self.__telnet.expect(self.__prefix_list, timeout=timeout)
        result = output.decode('utf-8', errors='ignore')
        # result = self.__telnet.read_very_eager().decode('utf-8')
        # result = result.split('\n')[1:-1]
        return result

    def command_real_time_result(self, command):
        """执行命令，并实时获取结果，需要使用子线程方式执行"""
        if not self.__telnet:
            return None
        aklog_printf()
        self.stop_command_flag = False
        self.__telnet.write(command.encode('utf-8') + b'\n')
        self.rt_result = ''
        while True:
            try:
                if self.stop_command_flag:
                    aklog_printf('命令停止执行')
                    break
                line = self.__telnet.read_until(b'\n', timeout=1).decode('utf-8', errors='ignore')
                if line:
                    self.rt_result += line
            except Exception as e:
                aklog_printf(f'命令停止执行: {e}')
                break
        return self.rt_result

    def thread_exec_command(self, command):
        """子线程连接telnet，并执行命令"""
        aklog_printf()
        self.__tln_thread = AkThread(target=self.command_real_time_result, args=(command,))
        self.__tln_thread.daemon = True  # 设置主线程结束后也结束子线程
        self.__tln_thread.start()

    def thread_stop_exec_output_result(self, file=None, timeout=60):
        """停止子线程执行的telnet命令，并输出结果，也可以保存到文件"""
        self.command_stop()
        self.stop_command_flag = True
        self.__tln_thread.join(timeout=timeout)
        if file:
            lines = self.rt_result.split('\n')
            with open(file, 'w') as f:
                f.writelines(lines)
        return self.rt_result

    def command_stop(self):
        """
        发送Ctrl+C停止命令执行，确保telnet命令行可继续输入。

        Returns:
            bool: True 表示命令成功停止，False 表示停止失败。
        """
        aklog_debug('开始执行command_stop，发送Ctrl+C停止命令')

        # 检查telnet连接是否已建立
        if self.__telnet is None:
            aklog_debug('telnet连接还未建立或者已关闭')
            return False

        max_retry = 3  # 最大重试次数

        for i in range(max_retry):
            try:
                # 连续发送两次Ctrl+C，确保终止命令
                self.__telnet.write(b'\x03')
                self.__telnet.write(b'\x03')
                time.sleep(1)  # 等待命令响应

                # 读取直到命令提示符或超时
                index, match, output = self.__telnet.expect(self.__prefix_list, timeout=2)
                ret = output.decode('utf-8', errors='ignore')

                # 特殊情况处理：有时^C会滞后返回
                if ret.strip() == '^C':
                    self.__telnet.write(b'\n')
                    index, match, output = self.__telnet.expect(self.__prefix_list, timeout=2)
                    ret = output.decode('utf-8', errors='ignore')

                # 判断是否已回到命令提示符
                if ret and ret.rstrip().endswith(self.__prefix):
                    aklog_debug('telnet命令执行已停止，可以继续执行命令')
                    self.__telnet.write(b'\n')  # 保证命令行整洁
                    return True
                else:
                    aklog_warn(f'停止命令未成功，当前返回内容: {ret}')
                    if i < max_retry - 1:
                        time.sleep(2)
                        aklog_debug(f'停止命令失败，准备第{i + 2}次重试...')
                        continue
                    else:
                        aklog_warn('telnet命令执行无法正常停止，已达最大重试次数')
                        break

            except Exception as e:
                aklog_warn(f'停止命令异常: {e}')
                if i < max_retry - 1:
                    time.sleep(2)
                    aklog_debug(f'异常后准备第{i + 2}次重试...')
                    continue
                else:
                    aklog_warn('停止命令异常，已达最大重试次数')
                    break

        # 多次尝试后仍未成功，执行登出操作
        aklog_warn('停止命令失败，准备登出telnet主机')
        self.logout_host()
        return False

    # 退出telnet
    def logout_host(self):
        """退出telnet连接"""
        aklog_printf('logout_host')
        if self.__telnet:
            try:
                try:
                    self.__telnet.write(b"exit\n")
                except Exception as e:
                    print(f"Telnet 发送 exit 命令失败: {e}")
                try:
                    self.__telnet.close()
                except Exception as e:
                    print(f"Telnet 关闭连接失败: {e}")
            finally:
                self.__telnet = None


if __name__ == '__main__':
    print('test')
    telnet = TelnetConnection('192.168.88.123', 23, 'root', 'yA@9^b8Zq-T+s')
    telnet.login_host()
    telnet.is_connected()
    result = telnet.command_result('ps | grep "PID" | grep -v grep')
    print(f'result: {result}')
