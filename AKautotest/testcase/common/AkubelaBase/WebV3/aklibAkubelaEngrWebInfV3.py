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
from testcase.common.AkubelaBase.WebV3.aklibAkubelaWebInfBaseV3 import AkubelaWebInfBaseV3
import time
import re
from typing import Union


class AkubelaEngrWebInfV3(AkubelaWebInfBaseV3):

    # region 通用API

    def get_config(self, *configs):
        """
        获取配置项
        configs: 可以同时获取多个配置项，比如： "status.general.model", "status.network.mac"
        return:
        如果获取单个配置项的，直接返回配置项的值
        同时获取多个配置项的，返回字典类型
        """
        aklog_debug()
        data = {
            "type": "ak_config/get",
            "device_id": self.device_id,
            "item": []
        }
        for config in configs:
            data['item'].append(config)
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            result = resp.get('result')
            if len(configs) == 1:
                # 如果获取单个配置项的，直接返回配置项的值
                item = configs[0]
                value = result[item]
                aklog_debug('[ %s ]: %s' % (item, value))
                return value
            else:
                # 同时获取多个配置项的，返回字典类型
                aklog_debug('get_config OK, result: %s' % result)
                return result
        else:
            aklog_error('get_config Fail')
            return None

    def update_config(self, configs):
        """
        修改配置项
        configs: dict类型: {'Settings.PCAP.SpecificPort': '5060'}
        """
        aklog_debug()
        data = {
            "type": "ak_config/update",
            "device_id": self.device_id,
            "item": configs
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_debug('update_config OK')
            return True
        else:
            aklog_error('update_config Fail')
            return False

    def set_setting_config(self, config, value):
        """设置配置项，8848页面"""
        data = {
            "type": "config/settings/set",
            "settings_type": config,
            "param": value,
            "device_id": self.device_id
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_debug('set_setting_config OK')
            return True
        else:
            aklog_error('set_setting_config Fail')
            return False

    def get_setting_config(self, *configs):
        data = {
            "type": "config/settings/get",
            "settings_type": [],
            "device_id": self.device_id
        }
        for config in configs:
            data['settings_type'].append(config)
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            result = resp.get('result')
            if len(configs) == 1:
                # 如果获取单个配置项的，直接返回配置项的值
                item = configs[0]
                value = result[item]
                aklog_debug('[ %s ]: %s' % (item, value))
                return value
            else:
                # 同时获取多个配置项的，返回字典类型
                aklog_debug('get_setting_config OK, result: %s' % result)
                return result
        else:
            aklog_error('get_setting_config Fail')
            return None

    def device_control(self, action):
        """设备控制，比如重启、恢复出厂等"""
        aklog_debug()
        data = {
            "type": "config/ak_device/ctrl",
            "action": action,
            "device_id": self.device_id
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            aklog_debug('device_control OK')
            return True
        else:
            aklog_error('device_control Fail')
            return False

    # endregion

    # region 登录

    def login(self, raise_enable=True):
        login_ret = self.interface_init(raise_enable=raise_enable)
        if login_ret:
            self.get_device_id(regain=True)
        return True

    def start_and_login(self):
        return self.login()
    
    def get_device_id(self, regain=False):
        """获取设备id信息"""
        if self.device_id and not regain:
            return self.device_id
        data = {
            "type": "config/ak_device/self"
        }
        resp = self.ws_send_request(data)
        if resp and resp.get('success'):
            self.device_id = resp['result']['device_id']
            aklog_info('device_id: %s' % self.device_id)
            return self.device_id
        else:
            aklog_error('get_device_id Fail')
            return None
    
    def web_env_init(self):
        self.web_open_ssh()

    def web_start_and_init(self):
        self.login()
        self.web_env_init()

    # endregion

    # region Account Basic页面

    def register_sip(self, user_name, password, server_addr, server_port='5060',
                     register_name=None, display_name=None, enable='1', period=1800):
        """
        注册SIP帐号
        enable: 0 or 1
        """
        aklog_info()
        if register_name is None:
            register_name = user_name
        if display_name is None:
            display_name = user_name
        data = {
            "Account2.GENERAL.Enable": enable,
            "Account2.GENERAL.DisplayName": display_name,
            "Account2.GENERAL.AuthName": register_name,
            "Account2.GENERAL.UserName": user_name,
            "Account2.GENERAL.Pwd": password,
            "Account2.SIP.Server": server_addr,
            "Account2.SIP.Port": server_port,
            "Account2.REG.Timeout": period,
        }
        ret = self.update_config(data)
        if not ret:
            aklog_error('注册SIP帐号出错，请检查：%s' % ret)
            return False
        # 检查是否注册成功
        register_ret = self.wait_sip_to_registered()
        return register_ret

    def wait_sip_to_registered(self):
        """
        等待帐号注册, failure_to_wait_time为显示注册失败后再继续等待的时间
        """
        aklog_info()
        timeout = 120
        deadline = time.time() + timeout
        while time.time() <= deadline:
            sip_status = self.get_sip_register_status()
            if sip_status == '2':
                aklog_info('sip account register success')
                return True
            elif sip_status == '0':
                aklog_warn('sip account is disabled')
                return False
            elif sip_status == '3':
                aklog_error('sip account register fail')
                return False
            else:
                time.sleep(3)
                continue
        aklog_error('sip account register fail')
        return False

    def get_sip_register_status(self):
        """
        return: 0: Disabled， 1： Registering， 2： Registered， 3： Registration Failed
        """
        return self.get_config('status.sip.status')

    def clear_web_sip(self):
        data = {
            "Account2.GENERAL.Enable": '0',
            "Account2.GENERAL.DisplayName": '',
            "Account2.GENERAL.AuthName": '',
            "Account2.GENERAL.UserName": '',
            "Account2.GENERAL.Pwd": '',
            "Account2.SIP.Server": '',
            "Account2.SIP.Port": '5060',
            "Account2.REG.Timeout": '1800',
        }
        self.update_config(data)

    # endregion

    # region Settings页面、升级、重启

    def get_firmware_version(self):
        """获取当前版本号"""
        version = None
        for i in range(2):
            version = self.get_config('status.general.firmware')
            if version:
                break
            time.sleep(1)
            continue
        aklog_info('firmware_version: %s' % version)
        return version

    def web_basic_upgrade_to_version(self, dst_version, firmware_path):
        """网页基础升级"""
        aklog_info()
        current_version = self.get_firmware_version()
        if current_version:
            if current_version == dst_version:
                aklog_info('当前版本已是: %s, 无需升级' % dst_version)
                return True
        else:
            aklog_error('获取版本号失败')
            return False
        self._upload_firmware_file(firmware_path)

        # 上传文件后，等待设备升级重启
        web_basic_upgrade_default_time = self.device_config.get_web_basic_upgrade_default_time()
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()  # 安卓机型获取到IP后仍需要等待一段时间才能正常访问设备
        cmd_waiting_for_device_reboot(
            self.device_ip, web_basic_upgrade_default_time, web_basic_upgrade_default_time,
            sec=boot_time_after_get_ip)  # 等待设备升级完成后重启

        # 等待网页可以访问
        self.wait_accessible()

        # 重新登录，获取版本号检查
        self.login()
        version_after_upgrade = self.get_firmware_version()
        if version_after_upgrade == dst_version:
            aklog_info('已升级到 %s 版本' % dst_version)
            return True
        else:
            aklog_error('网页升级失败')
            return False

    def _upload_firmware_file(self, firmware_file):
        """上传升级包"""
        aklog_debug()
        path = 'upgrade/upload'
        resp = self.api_post_chunk_file(path, firmware_file)
        if resp:
            aklog_info('upload_firmware_file OK')
            return True
        else:
            aklog_error('upload_firmware_file Fail')
            return False

    def upgrade_new_version(self):
        """网页升级新版本，一般只用于升级主测试设备"""
        aklog_info()
        # 如果辅助设备要调用该方法，可以使用put_test_rom_version()将升级版本传入替换
        upgrade_result = self.web_basic_upgrade_to_version(
            self.rom_version, self.device_config.get_local_firmware_path(self.rom_version))
        return upgrade_result

    def upgrade_old_version(self):
        aklog_info('网页升级旧版本')
        self.device_config.get_old_firmware(force_replace=self.force_replace_old_version)  # 强制替换旧版本升级包
        old_firmware_version = self.device_config.get_old_firmware_version()
        old_firmware_path = (self.device_config.get_upgrade_firmware_dir(True)
                             + old_firmware_version + self.device_config.get_firmware_ext())
        File_process.copy_file(self.device_config.get_old_firmware_path(), old_firmware_path)
        upgrade_result = self.web_basic_upgrade_to_version(old_firmware_version,
                                                           old_firmware_path)
        File_process.remove_file(old_firmware_path)
        return upgrade_result

    def upgrade_cover_old_version(self, firmware_version, firmware_path):
        """升级覆盖测试，检查从旧版本升级到新版本是否成功"""
        local_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(),
                                          firmware_version, self.device_config.get_firmware_ext())
        self.download_firmware_to_upgrade_dir(firmware_version, firmware_path)

        ret1 = self.web_basic_upgrade_to_version(firmware_version, local_firmware_path)
        File_process.remove_file(local_firmware_path)
        if not ret1:
            aklog_error('升级到旧版本 %s 失败' % firmware_version)
            return False

        ret2 = self.upgrade_new_version()
        return ret2

    def download_firmware_to_upgrade_dir(self, firmware_version, firmware_path):
        """将指定的升级包下载到本地Upgrade目录下"""
        local_firmware_path = '%s%s%s' % (self.device_config.get_upgrade_firmware_dir(),
                                          firmware_version, self.device_config.get_firmware_ext())
        download_result = False

        # 判断当前网卡速率，如果比较大，表明当前有设备正在升级下载升级包，则等待直到速率降下来
        cmd_waiting_for_network_rate_to_drop()

        if 'ftp://' in firmware_path:
            aklog_info("将升级包从FTP服务器下载到本地目录")
            ftp_info = get_ftp_info_from_url(firmware_path)
            ftp_connect_mode = True  # False为PORT模式
            for k in range(2):
                ftp_client = FtpClient(ftp_info['host'], ftp_info['port'], ftp_info['user_name'], ftp_info['password'])
                ftp_client.login(ftp_connect_mode)
                download_result = ftp_client.download_file(local_firmware_path, ftp_info['remote_file'])
                ftp_client.close()
                if download_result:
                    break
                else:
                    ftp_connect_mode = False
                    continue
        else:
            aklog_info("将升级包拷贝到本地目录")
            for x in range(2):
                download_result = File_process.copy_file(firmware_path, local_firmware_path)
                if download_result:
                    break

        if download_result:
            return File_process.chmod_file_off_only_read(local_firmware_path)
        else:
            return False

    def web_reboot(self):
        """网页进行重启"""
        self.device_control('reboot')
        cmd_waiting_for_device_reboot(
            self.device_ip, 30, self.device_config.get_reboot_default_time())
        # 等待网页可以访问
        ret = self.wait_accessible(timeout=60)
        return ret

    def web_reset_to_factory_setting(self):
        """网页恢复出厂设置"""
        self.device_control('reset_factory')
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()
        cmd_waiting_for_device_reboot(
            self.device_ip, 60, self.device_config.get_reset_default_time(), boot_time_after_get_ip)
        # 等待网页可以访问
        ret = self.wait_accessible()
        return ret

    def web_reset_to_installer_setting(self):
        """网页恢复到installer设置"""
        self.device_control('reset')
        boot_time_after_get_ip = self.device_config.get_boot_time_after_get_ip()
        cmd_waiting_for_device_reboot(
            self.device_ip, 60, self.device_config.get_reset_default_time(), boot_time_after_get_ip)
        # 等待网页可以访问
        ret = self.wait_accessible()
        return ret

    def get_system_country(self):
        return self.get_config('Settings.SYSTEM.Country')

    def get_hardware_version(self):
        version = self.get_config('status.general.hardware')
        aklog_info('hardware_version: %s' % version)
        return version

    def set_web_language(self, language):
        """
        language: 'zh-CN'
        """
        return self.update_config({'Settings.LANGUAGE.Type': language})

    def upgrade_sub_device(self, firmware_file):
        """升级子设备"""
        aklog_info()
        path = 'zigbee/upload'
        resp = self.api_post_chunk_file(path, firmware_file)
        if resp:
            aklog_debug('upload sub device firmware OK')
            return True
        else:
            aklog_error('upload sub device firmware Fail')
            return False

    # endregion

    # region autop升级

    def rename_all_cfg_file(self):
        File_process.rename_file(self.device_cfg_pnp, self.device_config.get_renamecfg_pnp())

    def copy_old_firmware_to_download_dir(self, protocol=None):
        """将机型对应OEM的旧版本复制到autop下载目录"""
        self.device_config.get_old_firmware(force_replace=self.force_replace_old_version)  # 强制替换旧版本升级包
        if protocol is None or protocol == 'http':
            File_process.copy_file(self.device_config.get_old_firmware_path(),
                                   self.device_config.get_http_dir() + self.device_config.get_old_firmware_file())
        if protocol is None or protocol == 'https':
            File_process.copy_file(self.device_config.get_old_firmware_path(),
                                   self.device_config.get_https_dir() + self.device_config.get_old_firmware_file())
        if protocol is None or protocol == 'tftp':
            File_process.copy_file(self.device_config.get_old_firmware_path(),
                                   self.device_config.get_tftp_dir() + self.device_config.get_old_firmware_file())
        if protocol is None or protocol == 'ftp':
            File_process.copy_file(self.device_config.get_old_firmware_path(),
                                   self.device_config.get_ftp_dir() + self.device_config.get_old_firmware_file())

    def write_cfg_to_upgrade_pnp(self, config_firmware_url=None):
        if not config_firmware_url:
            config_firmware_url = self.device_config.get_config_firmware_url_pnp()
        config_firmware_url = f'# {str(time.time())}\n' + config_firmware_url  # 写入时间戳，保证每次生成的文件MD5不一致
        File_process.rename_file(self.device_config.get_renamecfg_pnp(), self.device_cfg_pnp)
        File_process.write_file(self.device_cfg_pnp, config_firmware_url)

    # endregion

    # region 8850页面

    def set_log_level(self, level=7):
        """设置log等级"""
        self.update_config({'Settings.LOGLEVEL.Level': '%s' % level})

    def export_system_log(self, save_path=None, timeout=120):
        """导出log文件"""
        aklog_info()
        data = {
            "type": "diagnosis/export_log",
            "device_id": self.device_id
        }
        resp = self.ws_send_request(data, timeout=timeout)
        if resp and resp.get('success'):
            file_path = resp['result']['file_path']
            download_route = 'invoke/download'
            download_param = {'file': file_path,
                              'responseType': 'arraybuffer'}
            if not save_path:
                save_dir = root_path + '\\testfile\\Device_log\\%s' % self.model_name
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                save_path = save_dir + '\\PhoneLog.tgz'
            ret = self.api_download(download_route, download_param, save_path)
            if ret:
                aklog_info('export log success')
                return True
        aklog_error('export log failed')
        return False

    def export_syslog_to_results_dir(self, case_name):
        """导出syslog并保存到Results目录下"""
        log_time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file_name = 'DeviceLog--{}--{}--{}.tgz'.format(case_name, self.device_name, log_time)
        log_file = '{}\\{}'.format(log_dir, log_file_name)
        os.makedirs(log_dir, exist_ok=True)
        self.export_system_log(log_file)
        # 如果开启保存到共享文件夹，则log文件路径增加HTTP访问URL
        report_dir_url = get_share_http_report_dir_url()
        if report_dir_url:
            log_file_url = '{}/device_log/{}'.format(report_dir_url, log_file_name)
            aklog_info(f'log_file_url: {log_file_url}')

    def set_pcap_port(self, pcap_port):
        """网页设置PCAP的端口"""
        self.update_config({'Settings.PCAP.SpecificPort': str(pcap_port)})

    def pcap_begin(self, pcap_port=None):
        """开始抓包"""
        aklog_info()
        if pcap_port is not None:
            self.set_pcap_port(pcap_port)
            time.sleep(1)
        start_pcap_data = {
            "type": "diagnosis/pcap",
            "action": 1,
        }
        msg = self.ws_send_request(start_pcap_data)
        if msg.get('success'):
            return True
        aklog_warn(f'pcap begin fail: {msg}')
        return False

    def load_pcap(self):
        time.sleep(1)
        aklog_debug()
        if not self.ws_pcap_connect():
            aklog_error('ws_pcap run failed')
            return False
        # 开始抓包前，先清空抓包缓存
        self.clear_ws_pcap_cache()
        data = 'akuvoxpcap'
        self.ws_pcap_send_request(data, clear=False)
        msgs = self.ws_pcap_client.wait_msg(timeout=5)
        if msgs:
            aklog_info('start pcap success')
            return True
        else:
            aklog_error('start pcap failed')
            return False

    def stop_pcap(self):
        """停止抓包"""
        aklog_info()
        stop_pcap_data = {
            "type": "diagnosis/pcap",
            "action": 0,
        }
        msg = self.ws_send_request(stop_pcap_data)
        if msg.get('success'):
            return True
        aklog_warn(f'stop pcap fail: {msg}')
        return False

    def start_pcap(self, pcap_port=None):
        self.stop_pcap()
        time.sleep(1)
        self.pcap_begin(pcap_port)
        self.load_pcap()

    def export_pcap(self, save_path=None):
        """导出抓包"""
        aklog_info()
        msgs = self.get_ws_pcap_resp_msg()
        if not save_path:
            save_dir = self.device_config.get_chrome_download_dir()
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            save_path = save_dir + 'phone.pcap'
        if os.path.exists(save_path):
            os.remove(save_path)
        with open(save_path, "wb") as f:
            for msg in msgs:
                f.write(msg)
        time.sleep(0.2)
        self.clear_ws_pcap_cache()

    def clear_ws_pcap_cache(self):
        self.ws_pcap_client.clear_msg()

    def stop_and_export_pcap(self, save_path=None):
        self.stop_pcap()
        self.export_pcap(save_path)

    def save_pcap_to_results_dir(self, case_name=None):
        """保存PCAP文件到Results目录下"""
        log_time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        if case_name is None:
            case_name = ''
        pcap_file_name = 'Device--{}--{}--{}.pcap'.format(case_name, self.device_name, log_time)
        pcap_file = '{}\\{}'.format(log_dir, pcap_file_name)
        os.makedirs(log_dir, exist_ok=True)
        self.export_pcap(pcap_file)
        # 如果开启保存到共享文件夹，则pcap文件路径增加HTTP访问URL
        report_dir_url = get_share_http_report_dir_url()
        if report_dir_url:
            pcap_file_url = '{}/device_log/{}'.format(report_dir_url, pcap_file)
            aklog_info(f'pcap_file_url: {pcap_file_url}')

    # endregion

    # region 8848页面

    def set_ssh_or_tln(self, value='1'):
        """option_value 取值0和1"""
        if str(value) == '1':
            value = 'Enabled'
        else:
            value = 'Disabled'
        return self.set_setting_config('telnet', value)

    def web_open_ssh(self):
        """设备网页打开的ssh操作"""
        for i in range(2):
            if self.set_ssh_or_tln('1'):
                time.sleep(5)
                return True
            self.start_and_login()
            continue
        return False

    def set_connect_akubela_test_url(self, test_url='https://my.uat.akubela.com'):
        """连接测试服务器，需要使用测试url"""
        self.set_setting_config('test_url', test_url)

    # endregion

    # region Telnet/SSH命令通用操作

    def telnet_login(self):
        for i in range(5):
            if self.tln.login_host():
                self.tln_ssh_port_list = self.tln.get_port_list()
                self.tln_ssh_pwd_list = self.tln.get_pwd_list()
                return True
            elif i == 0:
                self.web_open_ssh()
                continue
            time.sleep(5)
            continue
        aklog_error('Telnet连接登录失败')
        return False

    def telnet_logout(self):
        self.tln.command_stop()
        self.tln.logout_host()

    def ssh_login(self):
        for i in range(5):
            if self.ssh.connect():
                self.tln_ssh_port_list = self.ssh.get_port_list()
                self.tln_ssh_pwd_list = self.ssh.get_pwd_list()
                return True
            elif i == 0:
                self.web_open_ssh()
                continue
            time.sleep(5)
            continue
        aklog_error('SSH连接登录失败')
        return False

    def ssh_logout(self):
        self.ssh.interactive_stop_command()
        self.ssh.close()

    def tln_or_ssh_login(self):
        if self.device_config.get_remote_connect_type() == 'telnet':
            self.telnet_login()
        else:
            self.ssh_login()

    def tln_or_ssh_logout(self):
        if self.device_config.get_remote_connect_type() == 'telnet':
            self.telnet_logout()
        else:
            self.ssh_logout()

    def get_value_by_ssh(self, command, timeout=60, print_result=True, ignore_error=False) -> Union[str, None]:
        """后台执行命令获取对应配置的值"""
        aklog_printf()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return None
        value = self.ssh.command_result(command, timeout=timeout, ignore_error=ignore_error, encoding='gbk')
        if print_result:
            aklog_printf('value: %s' % value)
        return value

    def get_result_by_telnet_command(self, command, timeout=60, print_result=True) -> Union[str, None]:
        """后台执行命令获取对应配置的值"""
        aklog_printf()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return None
        result = self.tln.command_result(command, timeout=timeout)
        if print_result:
            aklog_printf('result: %s' % result)
        return result

    def get_result_by_tln_or_ssh(
            self, command, timeout=60, print_result=True, ignore_error=False) -> Union[str, None]:
        """telnet或SSH执行命令并获取结果"""
        if self.device_config.get_remote_connect_type() == 'telnet':
            result = self.get_result_by_telnet_command(
                command, timeout=timeout, print_result=print_result)
        else:
            result = self.get_value_by_ssh(
                command, timeout=timeout, print_result=print_result, ignore_error=ignore_error)
        return result

    def exec_command_by_ssh(self, *commands, timeout=60):
        aklog_printf()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return False
        results = []
        for command in commands:
            ret = self.ssh.exec_command_no_back(command, timeout)
            results.append(ret)
            time.sleep(0.5)
        if False in results:
            return False
        else:
            return True

    def exec_command_by_tln(self, *commands, timeout=60):
        aklog_printf()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return False
        results = []
        for command in commands:
            ret = self.tln.exec_command(command, timeout)
            results.append(ret)
            time.sleep(0.5)
        if False in results:
            return False
        else:
            return True

    def command_by_tln_or_ssh(self, *commands, timeout=60):
        if self.device_config.get_remote_connect_type() == 'telnet':
            return self.exec_command_by_tln(*commands, timeout=timeout)
        else:
            return self.exec_command_by_ssh(*commands, timeout=timeout)

    def exec_command_by_interactive_ssh_thread(self, command):
        """ssh交互式子线程执行，需要与get_result_by_interactive_ssh_thread配合使用"""
        aklog_printf()
        for i in range(2):
            if self.ssh.is_connected() and self.ssh.start_chan():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return False
        time.sleep(0.5)
        self.ssh.thread_interactive_exec_command(command)
        return self.ssh

    def stop_interactive_ssh_command(self):
        self.ssh.interactive_stop_command()

    def get_result_by_interactive_ssh_thread(self, timeout=60):
        """获取SSH交互式子线程执行结果，需要与exec_command_by_interactive_ssh_thread配合使用"""
        return self.ssh.interactive_return_log(timeout=timeout)

    def ignore_previous_logs_by_interactive_ssh_thread(self, wait_time=3):
        """先获取一次结果，然后再次获取结果时就不会包含之前的结果，这样就不需要logcat -c清空掉之前的log了
        需要与exec_command_by_interactive_ssh_thread配合使用（该方法有点问题，先不要使用）"""
        result1 = self.ssh.interactive_return_log(wait_time)
        # result2 = self.interactive_tln_or_ssh.interactive_return_log(1)
        # result = result1 + result2
        return result1

    def exec_command_by_interactive_telnet_thread(self, command):
        """Telnet交互式子线程执行，需要与get_result_by_interactive_telnet_thread配合使用"""
        aklog_printf()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return False
        time.sleep(1)
        self.tln.thread_exec_command(command)
        return self.tln

    def get_result_by_interactive_telnet_thread(self, timeout=60):
        """获取Telnet交互式子线程执行结果，需要与exec_command_by_interactive_telnet_thread配合使用"""
        return self.tln.thread_stop_exec_output_result(timeout=timeout)

    def ssh_modify_mac(self, new_mac):
        """设备ssh连接执行命令"""
        aklog_info()
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return
        self.ssh.modify_mac(new_mac)
        self.ssh.close()

    def monitor_screen_touch_log(self):
        """监控屏幕点击log"""
        for i in range(2):
            if self.ssh.is_connected():
                break
            elif i == 0:
                self.ssh_login()
                continue
            else:
                return None
        ret = self.ssh.monitor_field_in_cat_output('getevent', '/dev/input/event0: 0003 0039 ffffffff')
        return ret

    def get_result_by_tln_sql(self, sqlcipher_path, db_path, db_key, sql, timeout=60):
        """telnet连接，进入数据库获取信息"""
        aklog_printf()
        for i in range(2):
            if self.tln.is_connected() or self.tln.command_stop():
                break
            elif i == 0:
                self.telnet_login()
                continue
            else:
                return None
        result = self.tln.exec_sql(
            sqlcipher_path, db_path, db_key, sql, timeout=timeout)
        return result

    # endregion

    # region Telnet/SSH命令

    def reboot_by_tln_or_ssh(self, wait_time_after_reboot=10):
        aklog_info()
        self.command_by_tln_or_ssh('reboot')
        return cmd_waiting_for_device_reboot(self.device_ip, wait_time1=30, sec=wait_time_after_reboot)

    def get_uptime_by_tln_or_ssh(self) -> Optional[int]:
        """获取开机时间"""
        aklog_info()
        uptime = None
        for i in range(2):
            uptime = self.get_result_by_tln_or_ssh('uptime')
            if uptime:
                break
            elif i == 0:
                time.sleep(3)
                continue
            else:
                return None
        
        def calculate_minutes(uptime_str):
            # 匹配 "X days, HH:MM"
            match = re.search(r'up +(\d+) +days?, +(\d+):(\d+),', uptime_str)
            if match:
                days = int(match.group(1))
                hours = int(match.group(2))
                minutes = int(match.group(3))
                return days * 24 * 60 + hours * 60 + minutes
            
            # 匹配 "X days, X min"
            match = re.search(r'up +(\d+) +days?, +(\d+) +min,', uptime_str)
            if match:
                days = int(match.group(1))
                minutes = int(match.group(2))
                return days * 24 * 60 + minutes
            
            # 匹配 "HH:MM"
            match = re.search(r'up +(\d+):(\d+),', uptime_str)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                return hours * 60 + minutes
            
            # 匹配 "X min"
            match = re.search(r'up +(\d+) +min,', uptime_str)
            if match:
                minutes = int(match.group(1))
                return minutes
            
            return None
        
        uptime_min = calculate_minutes(uptime)
        aklog_info('uptime: %s min' % uptime_min)
        return uptime_min

    def get_door_setting_config_by_tln_or_ssh(self, section, key):
        """获取/config/Door/Setting.conf配置文件里面的配置项"""
        return self.get_result_by_tln_or_ssh(
            '/app/bin/inifile_wr r /config/Door/Setting.conf %s %s ""' % (section, key))

    def wait_general_setting_config_by_tln_or_ssh(self, section, key, target_value, timeout=60):
        """获取/config/Door/Setting.conf配置文件里面的配置项"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            value = self.get_result_by_tln_or_ssh(
                '/app/bin/inifile_wr r /config/Phone/General/Setting.conf %s %s ""' % (section, key))
            if value and value.strip() == target_value:
                return True
            time.sleep(3)
        aklog_warn(f'配置项{section},{key} 值未变成: {target_value}')
        return False

    def start_adb_server_by_ssh(self, device_id, retry_counts=5):
        if ':' not in device_id:
            aklog_info('USB方式连接，不需要启动adb server')
            return True
        adb_server_port = device_id.split(':')[1]
        command_set_adbd = f'setprop service.adb.tcp.port {adb_server_port}'
        command_stop_adbd = 'nohup stop adbd > /dev/null 2>&1 &'
        command_start_adbd = 'nohup start adbd > /dev/null 2>&1 &'
        command_write_misc_adb = 'mkdir /data/misc/adb;echo %s > /data/misc/adb/adb_keys' \
                                 % self.device_config.get_command_misc_adb_password()
        command_chown_adb = 'cd /data/misc/adb/; chown system:shell adb_keys'
        command_chmod_adb = 'chmod 640 /data/misc/adb/adb_keys'
        for i in range(0, retry_counts):
            try:
                ret = self.exec_command_by_ssh(
                    command_set_adbd, command_stop_adbd, command_start_adbd,
                    command_write_misc_adb, command_chown_adb, command_chmod_adb
                )
                if ret:
                    time.sleep(3)
                    return True
                elif i < 2:
                    self.web_open_ssh()
                    continue
                else:
                    aklog_error('Start Adb Server 失败，重试...')
                    time.sleep(3)
                    continue
            except:
                aklog_error('遇到未知异常，等待重试...' + str(traceback.format_exc()))
                time.sleep(5)
                continue
        aklog_error('Start Adb Server 失败')
        return False

    def set_upgrade_idle_time(self, wait_time=30):
        """
        设置设备进入空闲状态的等待时间，准备升级
        wait_time: 秒
        """
        self.command_by_tln_or_ssh('settings put system akuvox_upgrade_idle_time  %s' % (wait_time * 1000))

    def push_file_by_tftp(self, file_path, dst_dir, tftp_timeout=300):
        """如果是手动开启的TFTP工具，需要将工具的根目录设置为要传输的文件目录"""
        aklog_debug()
        file_dir, file_name = os.path.split(file_path)
        if not dst_dir.startswith('/'):
            dst_dir = '/' + dst_dir
        dst_path = f'{dst_dir}/{file_name}'
        # 先判断文件是否存在和一致
        if self.check_remote_file_consistency(file_path, dst_path):
            return
        tftp_server = thread_start_tftp_server(file_dir)
        local_ip = get_local_host_ip()
        self.command_by_tln_or_ssh(
            f'tftp -g -r {file_name} -l {dst_path} {local_ip}:{tftp_server.tftp_port}',
            timeout=tftp_timeout)

    def pull_file_by_tftp(self, file_path, dst_dir=None, tftp_timeout=300):
        """tftp方式导出文件"""
        aklog_debug()
        file_name = os.path.basename(file_path)
        file_name, ext = os.path.splitext(file_name)
        _time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        dst_file_name = f'{file_name}--{_time}{ext}'
        if not dst_dir:
            aklog_warn('未手动开启TFTP服务器，并且没有传入目标文件夹，使用result目录下的tftp文件夹')
            dst_dir = aklog_get_result_dir() + '\\tftp'
        tftp_server = thread_start_tftp_server(dst_dir)
        time_sleep(10)
        local_ip = get_local_host_ip(self.device_ip)
        self.command_by_tln_or_ssh(
            f'tftp -p -l {file_path} -r {dst_file_name} {local_ip}:{tftp_server.tftp_port}',
            timeout=tftp_timeout)
        return dst_file_name

    def pull_db_files_by_tftp(self, dst_dir=None, tftp_timeout=300):
        """将tuya_db_files文件夹导出"""
        file_path = '/data/code/tuya_db_files'
        file_dir, file_name = os.path.split(file_path)
        tar_file = f'{file_name}.tar'
        tar_file_path = f'{file_dir}/{tar_file}'
        tar_cmd = f'cd {file_dir};rm {tar_file} -rf;tar -cf {tar_file} {file_name}'
        self.command_by_tln_or_ssh(tar_cmd)
        return self.pull_file_by_tftp(tar_file_path, dst_dir, tftp_timeout)

    def check_remote_file_consistency(self, local_file, remote_file):
        """
        校验本地文件与远程文件内容是否一致
        :param local_file: 本地文件路径
        :param remote_file: 远程文件路径
        :return: True一致，False不一致，None异常
        """
        try:
            # 1. 计算本地文件MD5
            local_md5 = File_process.get_file_md5(local_file)
            if not local_md5:
                aklog_warn("本地文件MD5计算失败。")
                return None
            aklog_debug(f"本地文件[{local_file}] MD5: {local_md5}")

            # 2. 获取远程文件MD5
            # Linux常用命令：md5sum /path/to/file | awk '{print $1}'
            remote_cmd = f"md5sum {remote_file} | awk '{{print $1}}'"
            remote_md5 = self.get_result_by_tln_or_ssh(remote_cmd)
            if not remote_md5 or "can't open" in remote_md5 or 'No such file or directory' in remote_md5:
                aklog_warn("远程文件MD5获取失败。")
                return None
            remote_md5 = remote_md5.strip()
            aklog_debug(f"远程文件[{remote_file}] MD5: {remote_md5}")

            # 3. 比较
            if local_md5 == remote_md5:
                aklog_debug("本地文件与远程文件内容一致。")
                return True
            else:
                aklog_warn("本地文件与远程文件内容不一致。")
                return False
        except Exception as e:
            aklog_error(f"文件一致性校验异常: {e}")
            aklog_debug(traceback.format_exc())
            return None

    # endregion

    # region telnet/SSH 进程相关

    def top_get_memory_info(self):
        """获取内存使用情况"""
        aklog_info('top_get_memory_info')
        memory_info = self.get_result_by_tln_or_ssh('top -b -n 1 | grep Mem: | grep -v grep')
        if memory_info is None:
            return None
        infos = memory_info.split('Mem:')[-1].split(',')
        memory_info_dict = {}
        for info in infos:
            if 'used' in info:
                memory_info_dict['used'] = info.strip().split(' ')[0]
            if 'free' in info:
                memory_info_dict['free'] = info.strip().split(' ')[0]
            if 'shrd' in info:
                memory_info_dict['shrd'] = info.strip().split(' ')[0]
            if 'buff' in info:
                memory_info_dict['buff'] = info.strip().split(' ')[0]
            if 'cached' in info:
                memory_info_dict['cached'] = info.strip().split(' ')[0]
        aklog_info('memory_info: %r' % memory_info_dict)
        return memory_info_dict

    def top_get_cpu_info(self):
        """获取cpu使用情况"""
        aklog_info('top_get_cpu_info')
        cpu_info = self.get_result_by_tln_or_ssh('top -b -n 1 | grep CPU: | grep -v grep')
        if cpu_info is None:
            return None
        infos = cpu_info.split('CPU:')[-1].strip().split('  ')
        cpu_info_dict = {}
        for info in infos:
            if 'usr' in info:
                cpu_info_dict['usr'] = info.strip().split(' ')[0]
            if 'sys' in info:
                cpu_info_dict['sys'] = info.strip().split(' ')[0]
            if 'nic' in info:
                cpu_info_dict['nic'] = info.strip().split(' ')[0]
            if 'idle' in info:
                cpu_info_dict['idle'] = info.strip().split(' ')[0]
            if 'io' in info:
                cpu_info_dict['io'] = info.strip().split(' ')[0]
            if 'irq' in info:
                cpu_info_dict['irq'] = info.strip().split(' ')[0]
            if 'sirq' in info:
                cpu_info_dict['sirq'] = info.strip().split(' ')[0]
        aklog_info('cpu_info: %r' % cpu_info_dict)
        return cpu_info_dict

    def top_get_process_info(self, *process_flag):
        """获取phone进程信息，返回字典"""
        aklog_info('top_get_process_info')
        attribute = self.get_result_by_tln_or_ssh('top -b -n 1 | grep "PID" | grep -v grep')
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_info('attribute_list: %r' % attribute_list)
        grep_command = ''
        for i in process_flag:
            grep_command += '| grep "%s" ' % i
        info = self.get_result_by_tln_or_ssh('top -b -n 1 | grep -v grep %s' % grep_command)
        if info is None:
            return None
        info = info.replace('\n#', '').strip()
        info = re.sub(' +', ' ', info)
        infos = info.split(' ')
        aklog_info('process infos: %r' % infos)

        process_info = {}
        for attribute in attribute_list:
            index = attribute_list.index(attribute)
            if attribute == 'PID':
                process_info['pid'] = infos[index]
            elif attribute == 'PPID':
                process_info['ppid'] = infos[index]
            elif attribute == 'USER':
                process_info['user'] = infos[index]
            elif attribute == 'STAT':
                process_info['stat'] = infos[index]
            elif attribute == 'RSS':
                process_info['rss'] = infos[index]
            elif attribute == 'VSZ':
                process_info['vsz'] = infos[index]
            elif attribute == '%VSZ':
                process_info['vsz%'] = infos[index]
            elif attribute == '%CPU':
                process_info['cpu%'] = infos[index]
            elif 'COMMAND' in attribute:
                if len(infos) > len(attribute_list):
                    process_info['command'] = ' '.join(infos[index:])
                else:
                    process_info['command'] = infos[index]

        aklog_info('process_info: %r' % process_info)
        return process_info

    def ps_get_process_info(self, *process_flag):
        """获取phone进程信息，返回字典"""
        aklog_info()
        attribute = self.get_result_by_tln_or_ssh('%s | grep "PID" | grep -v grep' % self.device_config.get_ps_cmd())
        if attribute is None:
            return None
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_debug('attribute_list: %r' % attribute_list)
        grep_command = ''
        for i in process_flag:
            grep_command += '| grep "%s" ' % i
        info = self.get_result_by_tln_or_ssh('%s | grep -v grep %s' % (self.device_config.get_ps_cmd(), grep_command))
        if info is None or 'root' not in info:
            return None
        info = info.replace('\n#', '').strip()
        info = re.sub(' +', ' ', info)
        infos = info.split(' ')
        aklog_debug('process infos: %r' % infos)

        process_info = {}
        for attribute in attribute_list:
            index = attribute_list.index(attribute)
            if attribute == 'PID':
                process_info['pid'] = infos[index]
            elif attribute == 'USER':
                process_info['user'] = infos[index]
            elif attribute == 'VSZ':
                process_info['vsz'] = infos[index]
            elif attribute == 'STAT':
                process_info['stat'] = infos[index]
            elif 'COMMAND' in attribute:
                if len(infos) > len(attribute_list):
                    process_info['command'] = ' '.join(infos[index:])
                else:
                    process_info['command'] = infos[index]

        aklog_debug('process_info: %r' % process_info)
        return process_info

    def ps_get_all_info(self):
        info = self.get_result_by_tln_or_ssh(self.device_config.get_ps_cmd())
        return info

    def ps_judge_processes_is_running(self, *processes):
        """ps获取进程信息，判断多个进程是否都正在运行"""
        aklog_info()
        not_running_process_list = []
        for process in processes:
            ps_command = '%s | grep -v grep | grep "%s"' % (self.device_config.get_ps_cmd(), process)
            info = self.get_result_by_tln_or_ssh(ps_command)
            if info is None:
                return None
            info = info.replace('\n#', '').strip()
            if not info:
                not_running_process_list.append(process)

        if not not_running_process_list:
            aklog_info('所有进程都正在运行')
            return True
        else:
            aklog_warn('有进程未运行: %r' % not_running_process_list)
            return False

    def check_device_process_status(self):
        """检查设备进程的状态，是否都在运行，由于各机型的进程信息可能不一致，可以重写该方法"""
        aklog_info()
        status = self.ps_judge_processes_is_running(
            'com.akuvox.phone',
            'com.akuvox.upgradeui',
            'homeassistant/__main__.pyc',
            'sip',
            'autop',
            'api.fcgi fcgi'
        )
        return status

    def kill_process_by_ssh(self, *processes):
        """杀进程"""
        aklog_info()
        attribute = self.get_value_by_ssh('%s | grep "PID" | grep -v grep' % self.device_config.get_ps_cmd())
        if attribute is None:
            return
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_debug('attribute_list: %r' % attribute_list)
        pid_index = attribute_list.index('PID')
        for process in processes:
            ps_cmd = '%s | grep -v grep | grep "%s"' % (self.device_config.get_ps_cmd(), process)
            info = self.get_value_by_ssh(ps_cmd)
            if not info or process not in info:
                aklog_printf('%s 没有在运行' % process)
                continue

            lines = info.splitlines()
            for line in lines:
                if not line or process not in line:
                    continue
                line = line.replace('\n#', '').strip()
                line = re.sub(' +', ' ', line)
                info_list = line.split(' ')
                aklog_debug('process info: %r' % info_list)
                pid = info_list[pid_index]
                kill_cmd = 'kill -9 %s' % pid
                ret = self.exec_command_by_ssh(kill_cmd)
                if ret:
                    aklog_printf('杀进程 %s 完成' % process)
                else:
                    aklog_error('杀进程 %s 失败' % process)

    def kill_process_by_tln(self, *processes):
        """杀进程"""
        aklog_info()
        attribute = self.get_result_by_telnet_command(
            '%s | grep "PID" | grep -v grep' % self.device_config.get_ps_cmd())
        if attribute is None:
            return
        attribute = attribute.replace('\n#', '').strip()
        attribute = re.sub(' +', ' ', attribute)
        attribute_list = attribute.split(' ')
        aklog_debug('attribute_list: %r' % attribute_list)
        pid_index = attribute_list.index('PID')
        for process in processes:
            ps_cmd = '%s | grep -v grep | grep "%s"' % (self.device_config.get_ps_cmd(), process)
            info = self.get_result_by_telnet_command(ps_cmd)
            if not info or process not in info:
                aklog_printf('%s 没有在运行' % process)
                continue
            lines = info.splitlines()
            for line in lines:
                if not line or process not in line:
                    continue
                line = line.replace('\n#', '').strip()
                line = re.sub(' +', ' ', line)
                info_list = line.split(' ')
                aklog_debug('process info: %r' % info_list)
                pid = info_list[pid_index]
                kill_cmd = 'kill -9 %s' % pid
                ret = self.exec_command_by_tln(kill_cmd)
                if ret:
                    aklog_info('杀进程 %s 完成' % process)
                else:
                    aklog_error('杀进程 %s 失败' % process)

    def kill_process_by_tln_or_ssh(self, *processes):
        if self.device_config.get_remote_connect_type() == 'telnet':
            return self.kill_process_by_tln(*processes)
        else:
            return self.kill_process_by_ssh(*processes)

    def wait_process_start(self, *processes, timeout=600, interval=5):
        """等待进程启动"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            process_ret = self.ps_judge_processes_is_running(*processes)
            if process_ret:
                return True
            time.sleep(interval)
            continue
        aklog_warn(f'{processes} 进程未在运行')
        return False

    def check_process_crash(self, *ignore_processes):
        """
        检查crash日志，过滤掉指定进程的crash，其他进程crash则判定用例失败。

        Args:
            ignore_processes (str): 要忽略的进程名（可变参数，支持多个）
        Returns:
            bool: True-无非忽略进程crash，False-有其他进程crash
        """
        # 获取crash日志
        crash_log = self.get_result_by_tln_or_ssh(
            'logcat -b crash -d', print_result=False)
        # 使用正则分割每个crash块
        crash_blocks = re.split(r'-+\s*beginning of crash', crash_log)
        # 标准化忽略进程名为小写，便于后续匹配
        ignore_list = [p.lower() for p in ignore_processes] if ignore_processes else []
        crash_proc = []
        for block in crash_blocks:
            # 查找Cmdline字段
            cmdline_match = re.search(r'Cmdline:\s*(.+)', block)
            if cmdline_match:
                cmdline = cmdline_match.group(1).strip()
                cmdline_lower = cmdline.lower()
                # 判断是否为忽略进程
                if any(ignore_proc in cmdline_lower for ignore_proc in ignore_list):
                    # 只要进程名包含在忽略列表中，则跳过
                    aklog_info(f"检测到忽略进程crash，忽略: {cmdline}")
                    continue  # 忽略指定进程crash
                else:
                    # 检测到非忽略进程crash，判定失败
                    unittest_results([1, f"检测到非忽略进程crash: {cmdline}"])
                    aklog_debug(f"crash详情:\n{block}")
                    crash_proc.append(cmdline)
        # 所有crash均为忽略进程或无crash
        if not crash_proc:
            aklog_info("crash日志检查通过，无非忽略进程crash")
            return True
        else:
            return False

    # endregion

    # region telnet/ssh log相关

    def clear_logs_by_ssh(self):
        """清理log缓存"""
        aklog_info('clear_logs_by_ssh')
        self.exec_command_by_ssh('logcat -G 2M', 'logcat -c')

    def clear_logs_by_tln(self):
        """清理log缓存"""
        aklog_info('clear_logs_by_tln')
        self.command_by_tln_or_ssh('rm /tmp/Messages* -f', 'echo "" > /tmp/Messages')

    def clear_logs_by_tln_or_ssh(self):
        """清理log缓存"""
        if self.device_config.get_remote_connect_type() == 'ssh':
            self.clear_logs_by_ssh()
        else:
            self.clear_logs_by_tln()

    def set_logcat_buffer_size(self, size='20M', *processes):
        """
        设置logcat缓冲区大小，避免因为缓冲区太小，短时间打印太多log导致logcat中断
        size: 2M
        """
        buffer_sizes = self.get_logcat_buffer_size()
        if not buffer_sizes:
            self.exec_command_by_ssh('logcat -G %s' % size)

        if processes:
            cmd_list = []
            for process in processes:
                if buffer_sizes.get(process) == size:
                    continue
                cmd = f'logcat -b {process} -G {size}'
                cmd_list.append(cmd)
            if cmd_list:
                self.exec_command_by_ssh(*cmd_list)
        else:
            flag = False
            for key, value in buffer_sizes.items():
                if value != size:
                    flag = True
                    break
            if flag:
                self.exec_command_by_ssh('logcat -G %s' % size)

    def get_logcat_buffer_size(self) -> Optional[dict]:
        try:
            # 执行 adb logcat -g 命令
            output = self.get_value_by_ssh('logcat -g')
            buffer_sizes = {}
            for line in output.splitlines():
                parts = line.split(':')
                if len(parts) == 2:
                    buffer_name = parts[0].strip()
                    size_info = parts[1].strip()
                    size = re.search(r'buffer is\s+(\d+)\s+MiB', size_info).group(1) + 'M'
                    buffer_sizes[buffer_name] = size
            aklog_debug(f'buffer_sizes: {buffer_sizes}')
            return buffer_sizes
        except Exception as e:
            aklog_debug(e)
            return None

    def get_dclient_msgs(self):
        """获取dclient的msg，将msg转换成字典"""
        aklog_info('get_dclient_msgs')
        command = 'logcat -d | grep "<" | cut -b 20- '
        dclient_msgs = []
        ssh_log = self.get_result_by_tln_or_ssh(command)
        ssh_log = ssh_log.replace('"', '##').replace('{', '**').replace('}', '**')
        # print(ssh_log)
        ssh_logs = ssh_log.split('</Msg>')
        # print(ssh_logs)
        for msg in ssh_logs:
            if not msg or not msg.strip():
                continue
            result_dict = parse_msg_to_dict(msg)
            dclient_msgs.append(result_dict)
        aklog_info(dclient_msgs)
        return dclient_msgs

    def get_dclient_msg_by_type(self, msg_type, dclient_msgs=None):
        if not dclient_msgs:
            dclient_msgs = self.get_dclient_msgs()
        for dc_msg in dclient_msgs:
            if not msg_type:
                return dc_msg
            elif msg_type == dc_msg['Msg'].get('Type'):
                return dc_msg
        return None

    def is_correct_print_log(self, flag):
        aklog_info('is_correct_print_log, flag: %s' % flag)
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d | grep -v grep | grep "%s"' % flag
        else:
            command = 'cat /tmp/Messages* | grep -v grep | grep "%s"' % flag
        ssh_log = self.get_result_by_tln_or_ssh(command)
        if ssh_log and flag in ssh_log:
            return True
        else:
            aklog_error('%s 日志不存在' % flag)
            return False

    def is_correct_log_level(self, log_level):
        """判断log等级打印是否正确"""
        logs = self.get_system_log_by_tln_or_ssh()
        ret = False
        if int(log_level) in [0, 1, 2]:
            ret = ',l3:' not in logs
        elif int(log_level) in [3, 4, 5, 6]:
            ret = ',l3:' in logs and ',l7:' not in logs and ',l%d:' % (int(log_level) + 1) not in logs
        elif int(log_level) == 7:
            ret = ',l3:' in logs and ',l7:' in logs
        if not ret:
            aklog_info(logs)
        return ret

    def get_counts_with_log_flag(self, flag):
        """获取指定log出现多少次"""
        aklog_info('get_counts_with_log_flag, flag: %s' % flag)
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d | grep -v grep | grep "%s"' % flag
        else:
            command = 'cat /tmp/Messages* | grep -v grep | grep "%s"' % flag
        ssh_log = self.get_result_by_tln_or_ssh(command)
        if ssh_log:
            counts = ssh_log.count(flag)
            # 结束时打印的log可能包含命令那一行，需要把这一行出现的次数去掉
            grep_counts = ssh_log.count('grep "%s"' % flag)
            counts -= grep_counts
        else:
            counts = 0
        aklog_info('%s 出现次数: %s' % (flag, counts))
        return counts

    def get_system_log_by_tln_or_ssh(self, log_flag=None):
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d'
        else:
            command = 'cat /tmp/Messages*'
        if log_flag:
            command += ' | grep "%s"' % log_flag
        ssh_log = self.get_result_by_tln_or_ssh(command, print_result=False)
        return ssh_log
    
    def upload_log_by_tln_or_ssh(self, case_name=None):
        """上传设备log到服务器"""
        get_cmd = self.device_config.get_upload_log_sh_get_cmd()
        self.command_by_tln_or_ssh(get_cmd)
        exec_cmd = self.device_config.get_upload_log_sh_exec_cmd()
        out = self.get_result_by_tln_or_ssh(
            exec_cmd, timeout=900, print_result=False, ignore_error=True)
        # 正则表达式模式用于匹配URL
        url_pattern = re.compile(r'http://\S+')
        # 查找所有匹配的URL
        urls = url_pattern.findall(out)
        if urls:
            url = urls[0]
            if not url.endswith('.tgz'):
                url += '.tgz'
            if case_name:
                aklog_info(f'{case_name}, log_url: {url}')
            else:
                aklog_info(f'log_url: {url}')
            return url
        aklog_warn(f'获取上传log的URL失败: {out}')
        return None
    
    def wait_get_syslog_by_tln_or_ssh(self, log_flag, timeout=30):
        """等待获取到指定的log"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            log = self.get_system_log_by_tln_or_ssh(log_flag)
            if log and log_flag in log:
                return log
            time.sleep(3)
            continue
        return None

    def get_ha_log_by_tln_or_ssh(self, log_flag=None):
        """获取HA的log"""
        command = 'cat /data/code/home-assistant.log'
        if log_flag:
            command += ' | grep "%s"' % log_flag
        ssh_log = self.get_result_by_tln_or_ssh(command, print_result=False)
        return ssh_log

    def export_syslog_to_results_dir_by_tln_or_ssh(self, case_name):
        """SSH或Telnet导出syslog并保存到Results目录下"""
        log_time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file_name = 'PhoneLog--{}--{}--{}.log'.format(case_name, self.device_name, log_time)
        log_file = '{}\\{}'.format(log_dir, log_file_name)
        os.makedirs(log_dir, exist_ok=True)
        log = self.get_system_log_by_tln_or_ssh()
        File_process.write_file(log_file, log, print_content=False)
        aklog_info(f'log_file: {log_file}')
        # 如果开启保存到共享文件夹，则log文件路径增加HTTP访问URL
        report_dir_url = get_share_http_report_dir_url()
        if report_dir_url:
            log_file_url = '{}/device_log/{}'.format(report_dir_url, log_file_name)
            aklog_info(f'log_file_url: {log_file_url}')

    def export_ha_log_to_results_dir_by_tln_or_ssh(self, case_name):
        """SSH或Telnet导出HA log并保存到Results目录下"""
        aklog_info()
        log_time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file_name = 'HAlog--{}--{}--{}.log'.format(case_name, self.device_name, log_time)
        log_file = '{}\\{}'.format(log_dir, log_file_name)
        os.makedirs(log_dir, exist_ok=True)
        log = self.get_ha_log_by_tln_or_ssh()
        File_process.write_file(log_file, log, print_content=False)
        aklog_info(f'ha_log_file: {log_file}')
        # 如果开启保存到共享文件夹，则log文件路径增加HTTP访问URL
        report_dir_url = get_share_http_report_dir_url()
        if report_dir_url:
            ha_log_file_url = '{}/device_log/{}'.format(report_dir_url, log_file_name)
            aklog_info(f'ha_log_file_url: {ha_log_file_url}')

    def start_logs_by_interactive_tln_or_ssh(self, log_flag=None):
        """
        开始交互式获取设备log，需要配合save_log_to_result_dir_by_tln_or_ssh使用
        log_flag: 如果要同时过滤多组字段全部显示，可以在多组字段中间加 |，比如：relay1 state|relay2 state
        grep要加参数 -E， 比如:grep -E "relay1 state|relay2 state"
        """
        aklog_info()
        if log_flag and '|' in log_flag:
            log_flag = ' | grep -E "%s"' % log_flag
        elif log_flag:
            log_flag = ' | grep "%s"' % log_flag
        else:
            log_flag = ''
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat%s' % log_flag
            # self.set_logcat_buffer_size()
            self.exec_command_by_interactive_ssh_thread(command)
        else:
            command = 'tail -F /tmp/Messages%s' % log_flag
            self.exec_command_by_interactive_telnet_thread(command)

    def get_logs_by_interactive_tln_or_ssh(self, timeout=60):
        """交互式获取设备log，需要配合start_logs_by_interactive_tln_or_ssh使用"""
        aklog_info()
        if self.device_config.get_remote_connect_type() == 'ssh':
            ret = self.get_result_by_interactive_ssh_thread(timeout)
        else:
            ret = self.get_result_by_interactive_telnet_thread(timeout)
        return ret

    def get_counts_with_interactive_log_flag(self, flag, ssh_log=None):
        """
        获取指定log出现多少次，需要配合start_logs_by_interactive_tln_or_ssh使用
        """
        aklog_info('get_counts_with_interactive_log_flag, flag: %s' % flag)
        if ssh_log is None:
            ssh_log = self.get_logs_by_interactive_tln_or_ssh()
        counts = 0
        if ssh_log:
            log_lines = ssh_log.split('\n')
            for line in log_lines:
                if flag in line and '| grep' not in line:
                    counts += 1
        else:
            aklog_warn('未获取到 %s 的指定 log' % flag)
        aklog_info('%s 出现次数: %s' % (flag, counts))
        return counts

    def save_logs_to_result_dir_by_tln_or_ssh(self, case_name, timeout=900):
        """保存交互式获取到的log到测试结果目录下，save_logs_to_result_dir_by_tln_or_ssh"""
        aklog_info()
        if self.device_config.get_remote_connect_type() == 'ssh':
            ret = self.get_result_by_interactive_ssh_thread(timeout)
        else:
            ret = self.get_result_by_interactive_telnet_thread(timeout)
        results = ret.split('\n')
        log_time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
        log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
        log_file_name = 'PhoneLog--{}--{}--{}.log'.format(case_name, self.device_name, log_time)
        log_file = '{}\\{}'.format(log_dir, log_file_name)
        os.makedirs(log_dir, exist_ok=True)
        with open(log_file, 'w') as f:
            f.writelines(results)
        aklog_info(f'log_file: {log_file}')
        # 如果开启保存到共享文件夹，则log文件路径增加HTTP访问URL
        report_dir_url = get_share_http_report_dir_url()
        if report_dir_url:
            log_file_url = '{}/device_log/{}'.format(report_dir_url, log_file_name)
            aklog_info(f'log_file_url: {log_file_url}')
        return log_file

    def get_upload_capture_time_by_log(self):
        """获取上传截图的时间"""
        if self.device_config.get_remote_connect_type() == 'ssh':
            command = 'logcat -d | grep -v grep | grep "nTimestamp=" | tail -1 | cut -d "=" -f 2'
        else:
            command = 'cat /tmp/Messages | grep -v grep | grep "nTimestamp=" | tail -1 | cut -d "=" -f 2'
        time_stamp = self.get_result_by_tln_or_ssh(command)
        if time_stamp:
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time_stamp)))
        else:
            time_str = None
        return time_str

    def start_capture_syslog(self):
        """开启抓取log统一方法"""
        aklog_info()
        if self.device_config.get_reboot_clear_syslog():
            self.start_logs_by_interactive_tln_or_ssh()
            self.capture_syslog_enable = True

    def export_syslog_to_result(self, case_name):
        """保存日志到测试结果目录"""
        export_syslog_type = self.device_config.get_default_export_syslog_type()
        if self.capture_syslog_enable:
            self.capture_syslog_enable = False
            self.save_logs_to_result_dir_by_tln_or_ssh(case_name)
        elif export_syslog_type == 'upload':
            self.upload_log_by_tln_or_ssh(case_name)
        elif export_syslog_type == 'logcat' or export_syslog_type == 'cat':
            self.export_syslog_to_results_dir_by_tln_or_ssh(case_name)
        else:
            self.export_syslog_to_results_dir(case_name)

    # endregion


if __name__ == '__main__':
    web_inf = AkubelaEngrWebInfV3()
    device_info = {
        'device_name': 'hc_android_hypanel',
        'ip': '192.168.88.103'
    }
    device_config = config_parse_device_config('config_PS51_NORMAL')
    web_inf.init(device_info, device_config)
    web_inf.login()
    web_inf.start_pcap()
    time.sleep(10)
    web_inf.stop_pcap()
    web_inf.export_pcap(r'D:\Users\Administrator\Desktop\phone.pcap')
