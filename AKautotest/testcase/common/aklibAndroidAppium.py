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
from typing import Optional
import time
import traceback
import subprocess


class akAppium(object):

    def __init__(self, device):
        self.__process = None
        self.__isReady = False
        self.__androidDevice: Optional[AndroidConnect] = device
        self._device_config = device.get_device_config()
        self._device_info = device.GetDeviceInfo()
        if 'device_name' in self._device_info:
            self._device_name = self._device_info['device_name']
        else:
            self._device_name = ''
        self.__ssh = None
        self.tln_ssh_port_list = self._device_config.get_tln_ssh_port_list()
        self.tln_ssn_pwd_list = self._device_config.get_tln_or_ssh_pwd()
        if self.__androidDevice.GetDeviceAddr() != 'unknown':
            self.__ssh = SSHConnection(self.__androidDevice.GetDeviceAddr(),
                                       port=self.tln_ssh_port_list,
                                       username='root',
                                       password=self.tln_ssn_pwd_list)

    def IsReady(self):
        return self.__isReady

    def Start(self):
        for i in range(0, 3):
            self.Stop()  # 停止上一次
            if ':' in self.__androidDevice.GetDeviceId():
                self.DisconnectAdb()  # 断开上一次adb连接
                if not self.ConnectAdb():  # 连adb
                    aklog_debug('Can\'t connect adb')
                    self.__isReady = False
                    if i == 2:
                        return self.__isReady
                    else:
                        time.sleep(3)
                        continue
            else:
                # aklog_debug('USB方式连接，不需要adb connect，跳过')
                self.connect_adb_by_usb()

            aklog_debug('Appium [127.0.0.1:%s] starting...'
                        % self.__androidDevice.GetLocalPort())
            # 启动appium服务
            appium_command = self.__androidDevice.GetAppiumCommand()
            if (appium_command == 'appium1.22.3'
                    or appium_command == 'appium1.4.16'
                    or int(self.__androidDevice.GetPlatformVersion().split('.')[0]) < 6):
                # 安卓5.x版本，要使用appium server 1.x版本
                command = appium_command \
                          + ' -a 127.0.0.1 -p ' + self.__androidDevice.GetLocalPort() \
                          + ' -bp ' + self.__androidDevice.GetBootstrapPort() \
                          + ' --log-level ' + self._device_config.GetLogLevel()
            else:
                # Appium Server2.x版本，启动命令不一样
                command = (f'appium -a 127.0.0.1 -p {self.__androidDevice.GetLocalPort()}'
                           f' --base-path /wd/hub --log-level {self._device_config.GetLogLevel()}')

            try:
                aklog_debug(command)
                self.__process = subprocess.Popen(command, shell=True)
            except:
                self.__isReady = False
            else:
                time.sleep(3)  # 等待appium服务起来
                for j in range(0, 20):
                    # 检查appium进程端口是否启用
                    netstat_command = 'netstat -ano | findstr "LISTENING" | findstr "127.0.0.1:%s"' \
                                      % self.__androidDevice.GetLocalPort()
                    stdout = sub_process_get_output(netstat_command)
                    aklog_debug('检查appium进程端口是否启用，结果: %s' % stdout)
                    if stdout:
                        self.__isReady = True
                        break
                    elif j == 9:
                        self.__isReady = False
                        break
                    else:
                        self.__isReady = False
                        aklog_debug('Appium [127.0.0.1:%s] starting...'
                                    % self.__androidDevice.GetLocalPort())
                        time.sleep(3)
                        continue

            if self.__isReady:
                # 检查设备adb连接状态
                adb_connect_status = sub_process_get_output(
                    'adb devices | findstr "%s"' % self.__androidDevice.GetDeviceId())
                aklog_debug('检查设备adb连接状态，结果: %s' % adb_connect_status)
                if adb_connect_status and '%s	device' % self.__androidDevice.GetDeviceId() in adb_connect_status:
                    self.__isReady = True
                    break
                else:
                    self.__isReady = False
                    aklog_debug('设备 %s adb连接失败，需要重连'
                                % (self.__androidDevice.GetDeviceId()))
                    continue

        if self.__isReady:
            aklog_debug('Appium [127.0.0.1:%s] started success!'
                        % self.__androidDevice.GetLocalPort())
        else:
            aklog_debug('Appium [127.0.0.1:%s] started failed!'
                        % self.__androidDevice.GetLocalPort())

        return self.__isReady

    def Stop(self):
        if self.__process is not None:
            self.__process.terminate()

        # 获取占用所需端口的进程pid
        netstat_cmd = 'netstat -ano | findstr "LISTENING" | findstr "127.0.0.1:%s"' \
                      % self.__androidDevice.GetLocalPort()
        netstat_out = sub_process_get_output(netstat_cmd)
        aklog_debug(netstat_out)
        if netstat_out:
            netstat_out = netstat_out.strip()
            pid = netstat_out.split(' ')[-1]
            aklog_debug('node pid: %s' % pid)
            kill_pid_command = 'taskkill /F /PID %s' % pid
            sub_process_exec_command(kill_pid_command, 10)
            aklog_debug('Appium [127.0.0.1:%s] stopped!'
                        % self.__androidDevice.GetLocalPort())
        else:
            aklog_debug('检测监听端口失败, 可能当前并不存在appium监听进程或stop失败')
        self.__process = None
        time.sleep(2)

    def StartAdbServer(self, retry_counts=10):
        if ':' not in self.__androidDevice.GetDeviceId():
            aklog_debug('USB方式连接，不需要启动adb server')
            return True
        for i in range(0, retry_counts):
            try:
                if not self.__ssh.connect():
                    aklog_debug('ssh连接失败，重试...')
                    time.sleep(5)
                    continue
                self.tln_ssh_port_list = self.__ssh.get_port_list()
                self.tln_ssn_pwd_list = self.__ssh.get_pwd_list()
                command_start_adbd = 'setprop service.adb.tcp.port 5654; stop adbd; start adbd'
                command_misc_adb_password = self._device_config.get_command_misc_adb_password()
                command_write_misc_adb = 'mkdir /data/misc/adb;echo %s > /data/misc/adb/adb_keys' \
                                         % command_misc_adb_password
                command_chown_adb = 'cd /data/misc/adb/; chown system:shell adb_keys'
                command_chmod_adb = 'chmod 640 /data/misc/adb/adb_keys'
                self.__ssh.exec_command(command_start_adbd)
                self.__ssh.exec_command(command_write_misc_adb)
                self.__ssh.exec_command(command_chown_adb)
                self.__ssh.exec_command(command_chmod_adb)
                self.__ssh.close()
                time.sleep(3)
                return True
            except:
                aklog_debug('遇到未知异常，等待重试...' + str(traceback.format_exc()))
                time.sleep(5)
        aklog_debug('Start Adb Server 失败')
        # param_put_failed_to_exit_enable(True)
        return False

    def send_command_to_edit_config(self, oldconfig, newconfig, path):
        """
        修改配置项
        oldconfig：旧的配置项
        newconfig：新的配置项
        path：配置项的文件夹
        """
        for i in range(0, 1):
            try:
                self.__ssh.connect()
                command = "sed -i s/%s/%s/g %s" % (oldconfig, newconfig, path)
                # command = ("'%s'" % (command))
                self.__ssh.exec_command_no_back(command)
                self.__ssh.close()
                return True
            except:
                aklog_debug('遇到未知异常，等待重试...' + str(traceback.format_exc()))
                time.sleep(1)
        aklog_debug('配置失败')

    def send_command(self, option):
        """
        发送ssh命令，无返回结果
        """
        for i in range(0, 2):
            try:
                for j in range(6):
                    if self.__ssh.connect():
                        break
                    else:
                        time.sleep(5)
                command = option
                self.__ssh.exec_command_no_back(command)
                self.__ssh.close()
                return True
            except:
                aklog_debug('遇到未知异常，等待重试...' + str(traceback.format_exc()))
                time.sleep(5)
        aklog_debug('配置失败')

    def send_command_back(self, option):
        """
        发送ssh命令，等待返回结果
        """
        for i in range(0, 2):
            try:
                for j in range(6):
                    if self.__ssh.connect():
                        break
                    else:
                        time.sleep(5)
                command = option
                self.__ssh.command_result(command)
                self.__ssh.close()
                return True
            except:
                aklog_debug('遇到未知异常，等待重试...' + str(traceback.format_exc()))
                time.sleep(5)
        aklog_debug('配置失败')

    def ConnectAdb(self):
        device_id = self.__androidDevice.GetDeviceId()
        commandConnect = 'adb connect %s' % device_id
        commandRoot = 'adb -s %s root' % device_id
        commandDisconnect = 'adb disconnect %s' % device_id
        for i in range(2):
            connect_ret = sub_process_get_output(commandConnect, 10)
            if connect_ret and 'connected to %s' % device_id in connect_ret:
                break
            else:
                sub_process_exec_command(commandDisconnect)
                continue
        for j in range(2):
            if self._device_info.get('adb_root') is None or self._device_info.get('adb_root') == '1':
                # GSM版本执行root会异常
                adb_root_ret = sub_process_get_output(commandRoot, 10)
                if adb_root_ret and 'as root' in adb_root_ret:
                    aklog_debug(commandConnect + ' with root success!')
                    return True
                else:
                    sub_process_exec_command(commandConnect)
                    continue
        return self.judge_adb_connect_status()

    def DisconnectAdb(self):
        commandDisconnect = 'adb disconnect %s' % self.__androidDevice.GetDeviceId()
        sub_process_exec_command(commandDisconnect, 10)
        devices = sub_process_get_output('adb devices')
        if devices and self.__androidDevice.GetDeviceId() not in devices:
            aklog_debug(commandDisconnect + ' success!')
            return True
        else:
            return False

    def connect_adb_by_usb(self):
        aklog_debug('USB方式连接adb')
        commandRoot = 'adb -s %s root' % self.__androidDevice.GetDeviceId()
        for i in range(3):
            stdout_root = sub_process_get_output(commandRoot, 10)
            if (stdout_root and 'adbd is already running as root' in stdout_root) or stdout_root == '':
                aklog_debug(commandRoot + ' success!')
                return True
            elif stdout_root and 'adbd cannot run as root in production builds' in stdout_root:
                break
            else:
                aklog_debug('adb root failed, %s, retry...' % stdout_root)
                continue
        aklog_debug('adb root failed')
        return False

        # self.DisconnectAdb()  # 断开上一次adb连接
        # if not self.ConnectAdb():  # 连adb
        #     aklog_debug('Can\'t connect adb')
        #     self.__isReady = False
        #     return self.__isReady
        # else:
        #     return True

    def judge_adb_connect_status(self):
        device_uid = self.__androidDevice.GetDeviceId()
        adb_devices_command = 'adb devices | findstr "%s"' % device_uid
        for i in range(3):
            devices = sub_process_get_output(adb_devices_command)
            if devices and '%s	device' % device_uid in devices:
                aklog_debug('设备 %s adb连接成功' % device_uid)
                return True
            else:
                aklog_debug('设备 %s adb连接失败，重试' % device_uid)
                time.sleep(5)
                continue
        aklog_debug('设备 %s adb连接失败' % device_uid)
        return False
        # if devices is None:
        #     if i < 2:
        #         time.sleep(3)
        #         continue
        #     else:
        #         aklog_debug('adb命令执行异常')
        #         return False
        # elif device_uid not in devices:
        #     if i < 2:
        #         aklog_debug('设备 %s adb连接失败，重试' % device_uid)
        #         time.sleep(5)
        #         continue
        #     else:
        #         aklog_debug('设备 %s adb连接失败' % device_uid)
        #         return False
        # else:
        #     aklog_debug('设备 %s adb连接成功' % device_uid)
        #     return True

    def adb_push_file(self, source_path, destination_path):
        """导入文件"""
        aklog_debug('adb_push_file, source_path: %s, destination_path: %s'
                    % (source_path, destination_path))
        if not self.ConnectAdb():
            self.DisconnectAdb()
            self.ConnectAdb()
        time.sleep(2)
        command_push_file = 'adb -s %s push %s %s' % (self.__androidDevice.GetDeviceId(), source_path, destination_path)
        stdout = sub_process_get_output(command_push_file, 300)
        if stdout and '1 file pushed' in stdout:
            aklog_debug(command_push_file + ' success!')
            return True
        else:
            aklog_debug('adb_push_file Failed!')
            return False

    def adb_pull_file(self, source_path, destination_path):
        """导出文件"""
        aklog_debug('adb_pull_file, source_path: %s, destination_path: %s'
                    % (source_path, destination_path))
        if not self.ConnectAdb():
            self.DisconnectAdb()
            self.ConnectAdb()
        time.sleep(2)

        command_pull_file = 'adb -s %s pull %s %s' % (self.__androidDevice.GetDeviceId(), source_path, destination_path)
        stdout = sub_process_get_output(command_pull_file, 300)
        if stdout and '1 file pulled' in stdout:
            aklog_debug('adb_pull_file success!')
            return True
        else:
            aklog_debug('adb_pull_file Failed!')
            return False

    @staticmethod
    def StopAllAppium():
        killShell = 'taskkill /F /IM node.exe'
        sub_process_exec_command(killShell)

    def get_screen_saver_status(self):
        """获取屏保状态"""
        screen_saver_flag = self._device_config.get_screen_saver_flag()
        command = 'adb -s %s shell dumpsys window policy | findstr "%s"' \
                  % (self.__androidDevice.GetDeviceId(), screen_saver_flag)

        screen_saver_status = sub_process_get_output(command, 10)
        if screen_saver_status:
            screen_saver_status = screen_saver_status.strip()
            if ' ' in screen_saver_status:
                screen_saver_status = str_get_content_between_two_characters(
                    screen_saver_status, '%s=' % screen_saver_flag, ' ')
            elif '=' in screen_saver_status:
                screen_saver_status = screen_saver_status.split('=')[1]
            if screen_saver_status:
                screen_saver_status = screen_saver_status.strip()
                aklog_debug('screen_saver_status: %s' % screen_saver_status)

        if screen_saver_status == 'true' or screen_saver_status == 'SCREEN_STATE_ON':
            screen_saver_status = True
        elif screen_saver_status == 'false' or screen_saver_status == 'SCREEN_STATE_OFF':
            screen_saver_status = False
        else:
            aklog_debug('get_screen_saver_status failed')
            screen_saver_status = None
        return screen_saver_status

    def get_screen_power_status(self):
        """获取屏幕电源状态"""
        screen_power_flag = self._device_config.get_screen_saver_flag()
        if screen_power_flag == 'screenState':
            command = 'adb -s %s shell dumpsys window policy | findstr /C:"%s"' \
                      % (self.__androidDevice.GetDeviceId(), screen_power_flag)
            screen_power_status = sub_process_get_output(command, 10)
            if screen_power_status and 'SCREEN_STATE_ON' in screen_power_status:
                screen_power_status = True
            elif screen_power_status and 'SCREEN_STATE_OFF' in screen_power_status:
                screen_power_status = False
            else:
                screen_power_status = None
        else:
            command = 'adb -s %s shell dumpsys power | findstr /C:"Display Power:"' % self.__androidDevice.GetDeviceId()
            screen_power_status = sub_process_get_output(command, 10)
            # aklog_debug('[%s]' % screen_power_status)
            if screen_power_status and 'state=ON' in screen_power_status:
                screen_power_status = True
            elif screen_power_status and 'state=OFF' in screen_power_status:
                screen_power_status = False
            else:
                screen_power_status = None
        return screen_power_status

    def get_screen_power_status_by_mAwake(self):
        """获取屏幕电源状态"""
        command = 'adb -s %s shell dumpsys window policy | findstr "mAwake=true"' % self.__androidDevice.GetDeviceId()

        screen_power_status = sub_process_get_output(command, 10)
        aklog_debug('[%s]' % screen_power_status)
        if screen_power_status and screen_power_status.strip():
            screen_power_status = True
        else:
            screen_power_status = False
        return screen_power_status

    def remove_screen_saver(self):
        """adb命令解除屏保状态"""
        aklog_debug('remove_screen_saver')
        press_key_home_command = 'adb -s %s shell input keyevent 3' % self.__androidDevice.GetDeviceId()
        tap_location_command = 'adb -s %s shell input tap 1 1' % self.__androidDevice.GetDeviceId()
        press_key_power_command = 'adb -s %s shell input keyevent 26' % self.__androidDevice.GetDeviceId()
        # 屏幕睡眠状态没有亮屏也没有屏保，先点亮屏幕
        for i in range(2):
            screen_power_status = self.get_screen_power_status()
            if screen_power_status is None:
                break
            elif not screen_power_status:
                if i == 0:
                    sub_process_exec_command(press_key_power_command)
                    time.sleep(1)
                    continue
                else:
                    aklog_debug('screen power on failed')
                    break
            else:
                aklog_debug('screen power on success')
                break

        # 屏幕已亮起，但处于屏保状态
        for i in range(3):
            screen_saver_status = self.get_screen_saver_status()
            if screen_saver_status is None:
                return False
            elif screen_saver_status:
                # 处于屏保状态时按下HOME键即可解除屏保状态，也可以模拟点击方式解除屏保
                if i == 0:
                    sub_process_exec_command(tap_location_command)
                    time.sleep(1)
                    continue
                if i == 1:
                    # 处于屏保状态时按下HOME键即可解除屏保状态
                    sub_process_exec_command(press_key_home_command)
                    time.sleep(1)
                    continue
                else:
                    aklog_debug('remove screen saver failed')
                    return False
            else:
                aklog_debug('remove screen saver success')
                return True

    def remove_screen_saver_by_mAwake(self):
        """adb命令解除屏保状态"""
        aklog_debug('remove_screen_saver')
        # press_key_home_command = 'adb -s %s shell input keyevent 3' % self.__androidDevice.GetDeviceId()
        tap_location_command = 'adb -s %s shell input tap 1 1' % self.__androidDevice.GetDeviceId()
        press_key_power_command = 'adb -s %s shell input keyevent 26' % self.__androidDevice.GetDeviceId()
        # 屏幕睡眠状态没有亮屏也没有屏保，先点亮屏幕
        for i in range(2):
            screen_power_status = self.get_screen_power_status_by_mAwake()
            if screen_power_status is None:
                break
            elif not screen_power_status:
                if i == 0:
                    sub_process_exec_command(press_key_power_command)
                    time.sleep(1)
                    continue
                else:
                    aklog_debug('screen power on failed')
                    break
            else:
                aklog_debug('screen power on success')
                break

        # 屏幕已亮起，但处于屏保状态
        for i in range(2):
            screen_saver_status = self.get_screen_saver_status()
            if screen_saver_status is None:
                return False
            elif screen_saver_status:
                # 处于屏保状态时按下HOME键即可解除屏保状态
                if i == 0:
                    sub_process_exec_command(tap_location_command)
                    time.sleep(1)
                    continue
                else:
                    aklog_debug('remove screen saver failed')
                    return False
            else:
                aklog_debug('remove screen saver success')
                return True

    def press_key_power_by_adb(self):
        """按电源键"""
        press_key_power_command = 'adb -s %s shell input keyevent 26' % self.__androidDevice.GetDeviceId()
        sub_process_exec_command(press_key_power_command)

    def press_key_home_by_adb(self):
        press_key_home_command = 'adb -s %s shell input keyevent 3' % self.__androidDevice.GetDeviceId()
        sub_process_exec_command(press_key_home_command)

    def press_key_back_by_adb(self):
        press_key_back_command = 'adb -s %s shell input keyevent 4' % self.__androidDevice.GetDeviceId()
        sub_process_exec_command(press_key_back_command)

    def send_key_event(self, key_event_commands):
        try:
            self.__ssh.connect()
            for command in key_event_commands:
                self.__ssh.exec_command(command)
            self.__ssh.close()
            return True
        except:
            aklog_debug('遇到未知异常，等待重试...' + str(traceback.format_exc()))
            time.sleep(5)

    def adb_install_package(self, package):
        aklog_debug('adb_install_package, package: %s' % package)
        adb_install_command = 'adb -s %s install %s' % (self.__androidDevice.GetDeviceId(), package)
        for i in range(3):
            result = sub_process_get_output(adb_install_command, 300)
            aklog_debug('install result: %s' % result)
            if result is None:
                if i < 2:
                    time.sleep(3)
                    continue
                else:
                    aklog_debug('adb命令执行异常')
                    return False
            elif 'Success' in result or 'INSTALL_FAILED_ALREADY_EXISTS' in result:
                aklog_debug('%s install success' % package)
                return True
            elif i < 2:
                aklog_debug('%s install failed, retry' % package)
                continue
            else:
                aklog_debug('%s 安装失败' % package)
                return False

    def adb_uninstall_package(self, package_name):
        aklog_debug('adb_uninstall_package, package: %s' % package_name)
        device_uid = self.__androidDevice.GetDeviceId()
        adb_devices_command = 'adb devices | findstr "%s"' % device_uid
        for i in range(4):
            devices = sub_process_get_output(adb_devices_command)
            if devices is None:
                if i < 3:
                    # sub_process_exec_command('adb kill-server')
                    # sub_process_exec_command('adb start-server')
                    time.sleep(3)
                    continue
                else:
                    aklog_debug('adb命令执行异常')
                    return False
            elif device_uid not in devices:
                if i < 3:
                    aklog_debug('设备 %s adb连接失败，重试' % device_uid)
                    time.sleep(10)
                    continue
                else:
                    aklog_debug('设备 %s adb连接失败' % device_uid)
                    return False
            else:
                aklog_debug('设备 %s adb连接成功' % device_uid)
                break

        adb_uninstall_command = 'adb -s %s uninstall %s' % (device_uid, package_name)
        adb_get_pm_list_command = 'adb -s %s shell pm list packages | findstr "%s"' \
                                  % (device_uid, package_name)
        sub_process_exec_command(adb_uninstall_command, 120)
        result = sub_process_get_output(adb_get_pm_list_command, 30)
        if result is not None and package_name not in result:
            aklog_debug('%s uninstall success' % package_name)
            return True
        else:
            aklog_debug('%s uninstall failed' % package_name)
            return False

    def adb_error_devices_reboot(self, error_id):
        """设备id变成0-F,需要重启"""
        aklog_debug('adb_error_devices_reboot, error_id: %s' % error_id)
        correct_id = self.__androidDevice.GetDeviceId()
        adb_error_devices_command = 'adb devices | findstr "%s"' % error_id
        adb_error_devices_reboot_command = 'adb -s %s shell reboot' % error_id
        adb_correct_devices_command = 'adb devices | findstr "%s"' % correct_id
        error_devices = sub_process_get_output(adb_error_devices_command)
        if error_devices and error_id in error_devices:
            sub_process_exec_command(adb_error_devices_reboot_command, 30)
            for j in range(60):
                correct_devices = sub_process_get_output(adb_correct_devices_command)
                if correct_devices and correct_id in correct_devices:
                    aklog_debug('重启设备获取正确的id，成功')
                    return True
                else:
                    time.sleep(5)
                    continue
            aklog_debug('重启设备获取正确的id，失败')
            return False
        else:
            correct_devices = sub_process_get_output(adb_correct_devices_command)
            if correct_devices and correct_id in correct_devices:
                aklog_debug('当前设备id已经是: %s' % correct_id)
                return True
            else:
                aklog_debug('当前找不到正确和错误id的设备')
                return False

    def adb_get_current_activity(self, device_id=None):
        aklog_debug('adb_get_current_activity')
        if device_id is None:
            device_id = self.__androidDevice.GetDeviceId()
        get_current_activity_command = 'adb -s %s shell dumpsys activity | findstr "mFocusedActivity"' % device_id
        activity_info = sub_process_get_output(get_current_activity_command)
        if not activity_info:
            get_current_activity_command = 'adb -s %s shell dumpsys activity | findstr "mResumedActivity"' % device_id
            activity_info = sub_process_get_output(get_current_activity_command)

        if activity_info and '/' in activity_info:
            current_activity = activity_info.split('/')[1].split(' ')[0]
            # current_app = activity_info.split('/')[0].split(' ')[-1]
            aklog_debug('current_activity: %s' % current_activity)
            return current_activity
        else:
            return None

    def adb_start_app_activity(self, app_package, app_activity, enter_activity=None):
        aklog_debug('adb_start_app_activity, app_package: %s, app_activity: %s'
                    % (app_package, app_activity))
        start_app_activity_command = 'adb -s %s shell am start -n %s/%s' \
                                     % (self.__androidDevice.GetDeviceId(), app_package, app_activity)
        for i in range(2):
            sub_process_exec_command(start_app_activity_command)
            time.sleep(2)
            current_activity = self.adb_get_current_activity()
            if enter_activity is None:
                if current_activity == app_activity:
                    return True
                else:
                    time.sleep(1)
                    continue
            else:
                if current_activity == enter_activity:
                    return True
                else:
                    time.sleep(1)
                    continue
        aklog_debug('start app activity failed')
        return False

    def adb_logcat_log(self):
        """adb logcat -d获取log"""
        command = 'adb -s %s logcat -d' % self.__androidDevice.GetDeviceId()
        log = sub_process_get_output(command)
        return log

    def temp_check_appium_localport(self):
        aklog_info()
        netstat_command = 'netstat -ano | findstr "LISTENING" | findstr "127.0.0.1:%s"' \
                          % self.__androidDevice.GetLocalPort()
        stdout = sub_process_get_output(netstat_command)
        aklog_debug('检查appium进程端口是否启用，结果: %s' % stdout)
        if stdout:
            aklog_info('~~~~~~~ lex ~~~~~~~~~~')
            aklog_info('appium: {}'.format(stdout))
        else:
            aklog_warn(stdout)


def get_device_id_by_adb_devices(index=1):
    """获取device id"""
    try:
        adb_devices_command = 'adb devices | findstr "device"'
        devices = sub_process_get_output(adb_devices_command)
        if devices and '\n' in devices:
            device_list = devices.split('\n')
            if len(device_list) > 1:
                device_id = device_list[index].split('\t')[0]
            else:
                device_id = None
        else:
            device_id = None
        aklog_debug(device_id)
        return device_id
    except:
        aklog_debug(traceback.format_exc())
        return None


if __name__ == '__main__':
    get_device_id_by_adb_devices()
