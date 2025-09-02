# -*- coding: utf-8 -*-

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
import time
import traceback
import re
import paramiko  # SSH依赖库, 可用pip安装, 依次执行这命令即可: pip install paramiko.
import threading
from paramiko.ssh_exception import AuthenticationException, NoValidConnectionsError, SSHException
from typing import Optional


class SSHConnection:

    def __init__(self, hostname=None, port=None, username=None, password=None, device_name=''):
        self.__ssh: Optional[paramiko.SSHClient] = None
        self.__chan = None
        self.__ssh_thread = None
        self.__hostname = None
        self.device_name = ''
        self.__port_list = [22]
        self.__port = 22
        self.__username = 'root'
        self.__pwd_list = None
        self.__password = ''
        if hostname and username:
            self.init(hostname, port, username, password, device_name)

    def init(self, hostname, port, username, password, device_name=''):
        self.__hostname = hostname
        self.device_name = device_name

        if isinstance(port, int):
            self.__port_list = [port]
            self.__port = port
            if 2043 not in self.__port_list:
                self.__port_list.append(2043)
            if 22 not in self.__port_list:
                self.__port_list.append(22)
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

    # 连接
    def connect(self):
        try:
            if self.__ssh:
                self.close()
                sleep(0.5)
            aklog_error_tag('临时日志, 验证工程执行卡住问题0.')
            self.__ssh = paramiko.SSHClient()
            self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            aklog_error_tag('临时日志, 验证工程执行卡住问题1.')
            i = j = 0
            while True:
                try:
                    aklog_printf('ssh连接中 %s:%s@%s:%s ....'
                                 % (self.__username, self.__password, self.__hostname, self.__port))
                    self.__ssh.connect(hostname=self.__hostname, port=self.__port, username=self.__username,
                                       password=self.__password, timeout=300)
                    aklog_error_tag('临时日志, 验证工程执行卡住问题2.')
                    break
                except NoValidConnectionsError as e:
                    # 端口错误
                    aklog_printf('ssh连接 %s@%s:%s 失败, %s' %
                                 (self.__username, self.__hostname, self.__port, e))
                    if i == len(self.__port_list) - 1:
                        self.close()
                        return False
                    elif self.__port != self.__port_list[i]:
                        self.__port = self.__port_list[i]
                    elif i < len(self.__port_list) - 1:
                        self.__port = self.__port_list[i + 1]
                    i += 1
                    continue
                except AuthenticationException as e:
                    # 用户名密码错误
                    aklog_printf('ssh连接 %s:%s@%s 失败, %s' %
                                 (self.__username, self.__password, self.__hostname, e))
                    if j == len(self.__pwd_list) - 1:
                        self.close()
                        return False
                    elif self.__password != self.__pwd_list[j]:
                        self.__password = self.__pwd_list[j]
                    elif j < len(self.__pwd_list) - 1:
                        self.__password = self.__pwd_list[j + 1]
                    j += 1
                    continue
                except EOFError:
                    # 915 openssl升级
                    aklog_printf('ssh连接 %s@%s:%s 失败, %s, 尝试新版本openssh连接..' %
                                 (self.__username, self.__hostname, self.__port, str(traceback.format_exc())))
                    try:
                        disabled_algorithms = {
                            "kex": [
                                "curve25519-sha256@libssh.org",
                                "ecdh-sha2-nistp256",
                                "ecdh-sha2-nistp384",
                                "ecdh-sha2-nistp521",
                                "diffie-hellman-group16-sha512",
                                "diffie-hellman-group-exchange-sha256",
                                "diffie-hellman-group14-sha256",
                            ],
                            "keys": [
                                "ssh-ed25519",
                                "ecdsa-sha2-nistp256",
                                "ecdsa-sha2-nistp384",
                                "ecdsa-sha2-nistp521",
                                "rsa-sha2-256",
                                "rsa-sha2-512"
                            ],
                            "macs": [
                                "hmac-sha2-256",
                                "hmac-sha2-512",
                                "hmac-sha2-256-etm@openssh.com",
                                "hmac-sha2-512-etm@openssh.com",
                            ]

                        }
                        self.__ssh.connect(hostname=self.__hostname, port=self.__port, username=self.__username,
                                           password=self.__password, timeout=300,
                                           disabled_algorithms=disabled_algorithms)
                        aklog_printf('新方式openssh连接成功!!!!!!!!')
                        return True
                    except:
                        if i == len(self.__port_list) - 1:
                            self.close()
                            return False
                        elif self.__port != self.__port_list[i]:
                            self.__port = self.__port_list[i]
                        elif i < len(self.__port_list) - 1:
                            self.__port = self.__port_list[i + 1]
                        i += 1
                        continue
                except:
                    aklog_printf('ssh连接 %s@%s:%s 失败, %s' %
                                 (self.__username, self.__hostname, self.__port, str(traceback.format_exc())))
                    self.close()
                    return False
            self.__chan = self.__ssh.invoke_shell()  # 建立交互式shell连接
            aklog_printf('ssh连接 %s:%s@%s:%s 成功' % (self.__username, self.__password, self.__hostname, self.__port))
            self.sort_port_pwd()
            return True
        except:
            aklog_printf('ssh连接 %s:%s@%s:%s 失败, %s' % (self.__username, self.__password, self.__hostname,
                                                           self.__port, str(traceback.format_exc())))
            self.close()
            return False

    def start_chan(self):
        """退出上一次的命令，使处于等待输入命令状态"""
        aklog_printf()
        if not self.__ssh or not self.__chan:
            aklog_printf('SSH未连接')
            return False
        try:
            self.__chan.send(b'\x03')
            self.__chan.send('\n')
            return True
        except:
            aklog_printf('重新建立交互式shell连接')
            try:
                self.__chan = self.__ssh.invoke_shell()
                return True
            except:
                aklog_printf('SSH连接异常')
                return False

    def __is_connected(self):
        session = None
        try:
            transport = self.__ssh.get_transport()
            if transport is not None and transport.is_active():
                # 使用 open_session 检查连接
                transport.sock.settimeout(2)
                session = transport.open_session()
                session.settimeout(2)  # 设置超时时间
                session.exec_command("echo 'SSH connection successful'")
                output = session.recv(1024).decode().strip()
                if output == "SSH connection successful":
                    return True
                aklog_printf(f"错误: {output}")
                return False
            aklog_printf('SSH通道未处于活动状态')
            return False
        except AuthenticationException:
            aklog_printf("认证失败")
            return False
        except SSHException as e:
            aklog_printf("SSH 连接异常: %s" % e)
            return False
        except Exception:
            aklog_printf('SSH连接出现其他异常')
            aklog_printf(traceback.format_exc())
            return False
        finally:
            # 确保通道被关闭, 减少exec_command有较大概率channel close报错.
            if session is not None:
                try:
                    session.close()
                except Exception as e:
                    aklog_printf(f"关闭通道时发生异常: {str(e)}")

    def is_connected(self):
        if self.__ssh is None:
            aklog_printf('SSH连接还未建立')
            return False

        thread = AkThread(target=self.__is_connected)
        thread.daemon = True
        thread.start()
        thread.join(timeout=3)
        result = thread.get_result()
        return result

    def sort_port_pwd(self):
        # 重新排序端口列表，将连接成功的端口放在第一位
        self.__port_list.remove(self.__port)
        self.__port_list.insert(0, self.__port)
        # 重新排序密码列表，将连接成功的密码放在第一位
        self.__pwd_list.remove(self.__password)
        self.__pwd_list.insert(0, self.__password)

    def get_port_list(self):
        return self.__port_list

    def get_pwd_list(self):
        return self.__pwd_list

    # 执行命令
    def exec_command(self, command, timeout=60, ignore_error=False):
        aklog_printf('ssh执行命令: %s' % command)
        try:
            stdin, stdout, stderr = self.__ssh.exec_command(command, timeout=timeout)
            err_list = stderr.readlines()
            if not ignore_error and len(err_list) > 0:
                aklog_printf('ssh执行命令 [%s] 错误: %s' % (command, err_list[0]))
                return False
            else:
                aklog_printf('ssh执行命令 [%s] 成功: %s' % (command, stdout.read().decode('utf-8')))
                return True
        except:
            aklog_debug('ssh执行命令出现异常：%s' % traceback.format_exc())
            return False

    # 执行命令但不需要返回
    def exec_command_no_back(self, command, timeout=60):
        aklog_printf('ssh执行命令: %s' % command)
        try:
            self.__ssh.exec_command(command, timeout=timeout)
            return True
        except Exception as e:
            aklog_printf(f'ssh执行命令 {command} 失败: {e}')
            return False

    # 执行命令监控指定字段
    def monitor_field_in_cat_output(self, command, target_field, timeout=60):
        aklog_info()
        # 创建SSH客户端
        if self.is_connected():
            aklog_printf('SSH连接还未建立')
            self.connect()
        try:
            stdin, stdout, stderr = self.__ssh.exec_command(command, timeout=timeout)
            # 记录开始时间
            start_time = time.time()
            # 读取输出并监控目标字段
            while True:
                # 检查是否超时
                if time.time() - start_time > timeout:
                    aklog_info("超时退出")
                    self.close()
                    return False
                line = stdout.readline()
                aklog_info(line)
                if target_field in line:
                    aklog_info(f"目标字段 '{target_field}' 出现了")
                    self.close()
                    return True
                time.sleep(0.1)  # 避免CPU占用过高
        except:
            aklog_printf('ssh执行命令 %s 失败' % command)
            self.close()
            return False

    def monitor_field_in_cat_output1(self, command, target_field, timeout=60):
        aklog_info('开始监控...')
        # 创建SSH客户端
        if self.is_connected():
            aklog_printf('SSH连接还未建立')
            self.connect()
        try:
            stdin, stdout, stderr = self.__ssh.exec_command(command, timeout=timeout)
            # 记录开始时间
            start_time = time.time()
            occurrences = 0  # 记录目标字段出现的次数
            timestamps = []  # 记录目标字段出现的时间点
            short_intervals = 0  # 记录间隔小于30秒的次数

            # 读取输出并监控目标字段
            while True:
                # 检查是否超时
                if time.time() - start_time > timeout:
                    aklog_info("超时退出")
                    self.close()
                    aklog_info(f"目标字段 '{target_field}' 出现次数: {occurrences}")
                    aklog_info(f"时间点: {timestamps}")
                    aklog_info(f"间隔小于30秒的次数: {short_intervals}")
                    return occurrences, short_intervals, timestamps

                line = stdout.readline()
                if target_field in line:
                    occurrences += 1
                    current_time = time.time()
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
                    if timestamps:
                        last_time = time.mktime(time.strptime(timestamps[-1], '%Y-%m-%d %H:%M:%S'))
                        interval = current_time - last_time
                        if interval > 60:
                            short_intervals += 1
                    timestamps.append(timestamp)
                    aklog_info(f"目标字段 '{target_field}' 出现了,出现次数: {occurrences}")
                    aklog_info(f"{timestamp} - Found keyword '{target_field}' in log: {line.strip()}")
                    aklog_info(short_intervals)

                time.sleep(0.1)  # 避免CPU占用过高
        except Exception as e:
            aklog_printf(f'ssh执行命令 {command} 失败: {e}')
            self.close()
            return False

    # 执行命令并返回结果
    def command_result(self, command, timeout=60, ignore_error=False, encoding='utf-8'):
        for attempt in range(2):
            try:
                if self.__ssh is None:
                    self.connect()
                if self.__ssh._transport is None:
                    aklog_debug('ssh会话未开启, command_result执行异常.')
                    # 会话未打开的情况(telnet配置未开启),直接退出.不去走expect. web接口调用ssh_login()
                    return None
                aklog_printf(f'ssh(第{attempt}次)执行命令: {command}')
                stdin, stdout, stderr = self.__ssh.exec_command(command, timeout=timeout)
                err_list = stderr.readlines()
                if not ignore_error and len(err_list) > 0:
                    aklog_printf(f'ssh执行命令 [{command}] 错误: {err_list}')
                    return err_list[0]
                else:
                    return stdout.read().decode(encoding, "ignore")
            except SSHException as e:
                if attempt == 0:
                    aklog_printf("SSH 连接异常: %s, 重连..." % e)
                    self.connect()
                    continue
                else:
                    aklog_printf(f'执行命令获取结果异常，请检查: {e}')
                    aklog_printf(traceback.format_exc())
                    return None
            except Exception as e:
                aklog_printf(f'执行命令获取结果异常，请检查: {e}')
                aklog_printf(traceback.format_exc())
                return None
        return None

    # 文件上传
    def upload(self, src, dst):
        try:
            sftp = self.__ssh.open_sftp()
        except Exception as e:
            aklog_printf('开启sftp失败:', e)
            self.close()
            return False
        try:
            aklog_printf('上传文件: %s --> %s' % (src, dst))
            sftp.put(src, dst)
            sftp.close()
            return True
        except Exception as e:
            aklog_printf('上传文件失败:', e)
            self.close()
            return False

    # 文件下载
    def download(self, download_address, to_address):
        try:
            sftp = self.__ssh.open_sftp()
        except Exception as e:
            aklog_printf('开启sftp失败:', e)
            self.close()
            return False
        try:
            aklog_printf('下载文件: %s --> %s' % (download_address, to_address))
            sftp.get(download_address, to_address)
            sftp.close()
            return True
        except Exception as e:
            aklog_printf('下载文件失败:', e)
            self.close()
            return False

    # 修改mac
    def modify_mac(self, new_mac):
        file_path = '/info/network/interface'
        if not re.match(r'^[A-Fa-f0-9]{12}$', new_mac):
            raise ValueError("Invalid input format. Should be 14 hexadecimal characters.")

            # 按两位分组并用冒号连接
        formatted_mac = ':'.join(re.findall('..', new_mac))
        # 创建SSH客户端
        if self.is_connected():
            aklog_printf('SSH连接还未建立')
            self.connect()
        stdin, stdout, stderr = self.__ssh.exec_command(f'cat {file_path}')
        content = stdout.readlines()

        # 处理文件内容
        new_content = []
        for line in content:
            if 'eth0=' in line:
                new_line = f"eth0={formatted_mac}\n"
                new_content.append(new_line)
            else:
                new_content.append(line)
        # 将修改后的内容写回文件
        new_content_str = ''.join(new_content)
        self.__ssh.exec_command(f'rm -rf {file_path}')
        self.__ssh.exec_command(f'echo "{new_content_str}" > {file_path}')

        print("MAC 地址已修改")

    # 交互式执行命令
    def interactive_exec_command(self, command):
        aklog_printf('ssh执行命令: %s' % command)
        if not self.__chan or self.__chan.closed:
            self.connect()
        result = self.__chan.send(command + '\n')
        # res = str(self.__chan.recv(40960))  # 非必须，接受返回消息
        if result is None:
            aklog_printf('ssh执行命令: [%s] 错误' % command)
        else:
            aklog_printf('ssh执行命令: [%s] 成功' % command)

    # 交互式返回结果
    def interactive_return_log(self, recv=40960, wait_time=0.1, timeout=None):
        aklog_printf('获取ssh执行返回结果')
        time.sleep(wait_time)
        try:
            if timeout:
                self.__chan.settimeout(timeout)
            res = self.__chan.recv(recv).decode('UTF-8')  # 接受返回消息
            if timeout:
                self.__chan.settimeout(None)
            return res
        except:
            aklog_printf('')
            return None

    # 交互式执行命令,返回结果
    def interactive_command_result(self, command, recv=40960, sec=10):
        aklog_printf('ssh执行命令: %s' % command)
        result = self.__chan.send(command + '\n')
        time.sleep(sec)
        res = self.__chan.recv(recv).decode('UTF-8')  # 非必须，接受返回消息
        if result is None:
            aklog_printf('ssh执行命令: [%s] 错误' % command)
            return None
        else:
            aklog_printf('ssh执行命令: [%s] 成功' % command)
            return res

    # 交互式子线程方式执行命令
    def thread_interactive_exec_command(self, command):
        self.__ssh_thread = AkThread(target=self.interactive_exec_command, args=(command,))
        self.__ssh_thread.daemon = True  # 设置主线程结束后也结束子线程
        self.__ssh_thread.start()

    # 交互式停止命令
    def interactive_stop_command(self):
        aklog_printf()
        try:
            self.__chan.send(b'\x03')
        except:
            # print(traceback.format_exc())
            pass

    def chan_close(self):
        aklog_printf()
        if self.__chan:
            self.__chan.close()

    # 关闭连接
    def close(self):
        aklog_printf()
        try:
            if self.__chan:
                self.__chan.close()
            if self.__ssh:
                self.__ssh.close()
            time.sleep(1)
            return True
        except:
            aklog_printf('断开连接出现异常')
            return False

    def __del__(self):
        self.close()


class InteractiveSSHconnection:
    """交互式SSH连接，可以不用这个，直接用上面的SSHConnection类即可"""

    def __init__(self, hostname, port, username, password):
        self.__hostname = hostname
        if isinstance(port, int):
            self.__port_list = [port]
            self.__port = port
            if 2043 not in self.__port_list:
                self.__port_list.append(2043)
            if 22 not in self.__port_list:
                self.__port_list.append(22)
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

        self.__ssh = None
        self.__chan = None
        self.__ssh_thread = None
        aklog_printf(self.__port_list)
        aklog_printf(self.__pwd_list)

    # 连接
    def connect(self):
        try:
            self.__ssh = paramiko.SSHClient()
            self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            i = j = 0
            while True:
                try:
                    aklog_printf('ssh连接中 %s:%s@%s:%s ....'
                                 % (self.__username, self.__password, self.__hostname, self.__port))
                    self.__ssh.connect(hostname=self.__hostname, port=self.__port, username=self.__username,
                                       password=self.__password, timeout=300)
                    break
                except NoValidConnectionsError:
                    aklog_printf('ssh连接 %s@%s:%s 失败, %s' %
                                 (self.__username, self.__hostname, self.__port, str(traceback.format_exc())))
                    if i == len(self.__port_list) - 1:
                        self.close()
                        return False
                    elif self.__port != self.__port_list[i]:
                        self.__port = self.__port_list[i]
                    elif i < len(self.__port_list) - 1:
                        self.__port = self.__port_list[i + 1]
                    i += 1
                    continue
                except AuthenticationException:
                    aklog_printf('ssh连接 %s@%s 失败, %s' %
                                 (self.__username, self.__hostname, str(traceback.format_exc())))
                    if j == len(self.__pwd_list) - 1:
                        self.close()
                        return False
                    elif self.__password != self.__pwd_list[j]:
                        self.__password = self.__pwd_list[j]
                    elif j < len(self.__pwd_list) - 1:
                        self.__password = self.__pwd_list[j + 1]
                    j += 1
                    continue
                except:
                    aklog_printf('ssh连接 %s@%s:%s 失败, %s' %
                                 (self.__username, self.__hostname, self.__port, str(traceback.format_exc())))
                    self.close()
                    return False
            self.__chan = self.__ssh.invoke_shell()  # 建立交互式shell连接
            aklog_printf('ssh连接 %s@%s 成功' % (self.__username, self.__hostname))
            time.sleep(2)
            return True
        except:
            aklog_printf('ssh连接 %s@%s 失败, %s' % (self.__username, self.__hostname, str(traceback.format_exc())))
            self.close()
            return False

    def get_port_list(self):
        """重新排序端口列表，将连接成功的端口放在第一位"""
        self.__port_list.remove(self.__port)
        self.__port_list.insert(0, self.__port)
        return self.__port_list

    def get_pwd_list(self):
        """重新排序密码列表，将连接成功的密码放在第一位"""
        self.__pwd_list.remove(self.__password)
        self.__pwd_list.insert(0, self.__password)
        return self.__pwd_list

    # 执行命令
    def interactive_exec_command(self, command):
        aklog_printf('ssh执行命令: %s' % command)
        result = self.__chan.send(command + '\n')
        # res = str(self.__chan.recv(40960))  # 非必须，接受返回消息
        if result is None:
            aklog_printf('ssh执行命令: [%s] 错误' % command)
        else:
            aklog_printf('ssh执行命令: [%s] 成功' % command)

    # 返回结果
    def interactive_return_log(self, recv=40960, wait_time=3):
        aklog_printf('获取ssh执行返回结果')
        time.sleep(wait_time)
        res = self.__chan.recv(recv).decode('UTF-8')  # 接受返回消息
        return res

    # 执行命令,返回结果
    def interactive_command_result(self, command, recv=40960, sec=10):
        aklog_printf('ssh执行命令: %s' % command)
        result = self.__chan.send(command + '\n')
        time.sleep(sec)
        res = self.__chan.recv(recv).decode('UTF-8')  # 非必须，接受返回消息
        if result is None:
            aklog_printf('ssh执行命令: [%s] 错误' % command)
            return None
        else:
            aklog_printf('ssh执行命令: [%s] 成功' % command)
            return res

    def thread_interactive_exec_command(self, command):
        self.__ssh_thread = AkThread(target=self.interactive_exec_command, args=(command,))
        self.__ssh_thread.daemon = True  # 设置主线程结束后也结束子线程
        self.__ssh_thread.start()

    # 停止命令
    def interactive_stop_command(self):
        aklog_printf('ssh停止命令')
        try:
            self.__chan.send(b'\x03')
        except:
            # print(traceback.format_exc())
            pass

    # 关闭连接
    def close(self):
        if self.__chan:
            self.__chan.close()
        self.__ssh.close()


if __name__ == '__main__':
    print('测试')
    ssh = SSHConnection(
        '192.168.88.103', [22], 'root', "OSx=w$mGRr4!$3XT0('$", device_name='PS51')
    ssh.connect()
    aklog_printf(ssh.is_connected())
    # # command = 'ps'
    # # ssh.command_result(command)
    # # ssh.monitor_field_in_cat_output('cat /proc/kmsg', 'ILITEK: (ili_sleep_handler, 589): Sleep Mode = 2')
    # ssh.modify_mac('C2:09:24:08:21:19')
