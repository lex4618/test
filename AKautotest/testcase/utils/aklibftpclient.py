#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ftplib
import os
import socket
import traceback
from akcommon_define import *


class FtpClient(object):

    def __init__(self, host, port, username, password):
        self.__host = host
        self.__port = int(port)
        self.__username = username
        self.__password = password
        self.__ftp = ftplib.FTP()
        self.__ftp.encoding = 'gbk'
        self.file_list = []

    # 连接登录
    def login(self, mode=True):
        try:
            if mode:
                aklog_printf('ftp connect mode: PASV')
            else:
                aklog_printf('ftp connect mode: PORT')
            # timeout = 60
            # socket.setdefaulttimeout(timeout)
            self.__ftp.set_pasv(mode)  # True为PASV模式，False为PORT模式
            # 打开调试级别2，显示详细信息
            # self.__ftp.set_debuglevel(2)
            self.__ftp.connect(self.__host, self.__port, 60)
            self.__ftp.login(self.__username, self.__password)
            aklog_printf('ftp connect success')
            return True
        except:
            aklog_printf('ftp connect failed: %s' % traceback.format_exc())
            return False

    def close(self):
        """ 退出ftp"""
        aklog_printf("close()---> FTP退出")
        try:
            self.__ftp.quit()
            self.__ftp.close()
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def download_file(self, local_file, remote_file):
        """从ftp下载文件
            参数:
                local_file: 本地文件
                remote_file: 远程文件
        """
        aklog_printf("download_file, local_path = %s ,remote_path = %s" % (local_file, remote_file))

        is_same = self.compare_ftp_file(local_file, remote_file)
        if is_same:
            aklog_printf('%s 文件大小、修改日期和哈希值都相同，无需下载' % local_file)
            return True
        elif is_same is None:
            return False
        else:
            try:
                aklog_printf('>>>>>>>>>>>>下载文件 %s ... ...' % local_file)
                buf_size = 1024
                file_handler = open(local_file, 'wb')
                self.__ftp.retrbinary('RETR %s' % remote_file, file_handler.write, buf_size)
                file_handler.close()
                aklog_printf('下载文件成功')
                return True
            except:
                try:
                    file_handler.close()
                except:
                    pass
                aklog_error('下载文件%s出错，出现异常：%s ' % (remote_file, traceback.format_exc()))
                return False

    def download_file_tree(self, local_path, remote_path):
        """从远程目录下载多个文件到本地目录
                       参数:
                         local_path: 本地路径
                         remote_path: 远程路径
                """
        aklog_printf("download_file_dir, local_path = %s ,remote_path = %s" % (local_path, remote_path))
        try:
            self.__ftp.cwd(remote_path)
        except Exception as err:
            aklog_printf('远程目录%s不存在，继续...' % remote_path + " ,具体错误描述为：%s" % err)
            return

        if not os.path.isdir(local_path):
            aklog_printf('本地目录%s不存在，先创建本地目录' % local_path)
            os.makedirs(local_path)

        aklog_printf('切换至目录: %s' % self.__ftp.pwd())

        self.file_list = []
        # 方法回调
        self.__ftp.dir(self.get_file_list)

        remote_names = self.file_list
        aklog_printf('远程目录 列表: %s' % remote_names)
        for item in remote_names:
            file_type = item[0]
            file_name = item[1]
            local = os.path.join(local_path, file_name)
            if file_type == 'd':
                aklog_printf("download_file_tree()---> 下载目录： %s" % file_name)
                self.download_file_tree(local, file_name)
            elif file_type == '-':
                aklog_printf("download_file()---> 下载文件： %s" % file_name)
                self.download_file(local, file_name)
            self.__ftp.cwd("..")
            aklog_printf('返回上层目录 %s' % self.__ftp.pwd())
        return True

    def upload_file(self, local_file, remote_file):
        """从本地上传文件到ftp
           参数:
             local_path: 本地文件
             remote_path: 远程文件
        """
        if not os.path.isfile(local_file):
            aklog_printf('%s 不存在' % local_file)
            return

        if self.is_same_size(local_file, remote_file):
            aklog_printf('跳过相等的文件: %s' % local_file)
            return

        buf_size = 1024
        file_handler = open(local_file, 'rb')
        self.__ftp.storbinary('STOR %s' % remote_file, file_handler, buf_size)
        file_handler.close()
        aklog_printf('上传: %s' % local_file + "成功!")

    def upload_file_tree(self, local_path, remote_path):
        """从本地上传目录下多个文件到ftp
           参数:
             local_path: 本地路径
             remote_path: 远程路径
        """
        if not os.path.isdir(local_path):
            aklog_printf('本地目录 %s 不存在' % local_path)
            return

        self.__ftp.cwd(remote_path)
        aklog_printf('切换至远程目录: %s' % self.__ftp.pwd())

        local_name_list = os.listdir(local_path)
        for local_name in local_name_list:
            src = os.path.join(local_path, local_name)
            if os.path.isdir(src):
                try:
                    self.__ftp.mkd(local_name)
                except Exception as err:
                    aklog_printf("目录已存在 %s ,具体错误描述为：%s" % (local_name, err))
                aklog_printf("upload_file_tree()---> 上传目录： %s" % local_name)
                self.upload_file_tree(src, local_name)
            else:
                aklog_printf("upload_file_tree()---> 上传文件： %s" % local_name)
                self.upload_file(src, local_name)
        self.__ftp.cwd("..")

    def get_file_list(self, line):
        """ 获取文件列表
            参数：
                line：
        """
        file_arr = self.get_file_name(line)
        # 去除  . 和  ..
        if file_arr[1] not in ['.', '..']:
            self.file_list.append(file_arr)

    @staticmethod
    def get_file_name(line):
        """ 获取文件名
            参数：
                line：
        """
        pos1 = line.rfind(':')
        while line[pos1] != ' ':
            pos1 += 1
        while line[pos1] == ' ':
            pos1 += 1
        file_arr = [line[0], line[pos1:]]
        return file_arr

    def is_same_size(self, local_file, remote_file):
        """判断远程文件和本地文件大小是否一致
           参数:
             local_file: 本地文件
             remote_file: 远程文件
        """
        try:
            remote_file_size = self.__ftp.size(remote_file)
            aklog_printf('remote_file_size: %s' % remote_file_size)
        except:
            aklog_printf('remote_file %s not found' % remote_file)
            return None

        try:
            local_file_size = os.path.getsize(local_file)
        except:
            local_file_size = -1
        aklog_printf('local_file_size: %s' % local_file_size)
        if remote_file_size == local_file_size:
            return True
        else:
            return False

    def get_file_remote_names(self):
        """获取ftp服务器远程目录列表名字文件"""
        self.file_list = []
        # 方法回调
        self.__ftp.dir(self.get_file_list)
        remote_names = self.file_list
        aklog_printf('远程目录 列表: %s' % remote_names)
        return remote_names

    def get_ftp_file_metadata(self, ftp_file_path):
        # 获取文件大小
        size = self.__ftp.size(ftp_file_path)
        # 获取修改时间
        modified_time = self.__ftp.sendcmd(f"MDTM {ftp_file_path}")[4:].strip()
        return size, modified_time

    def calculate_ftp_file_hash(self, ftp_file_path, hash_algorithm='md5'):
        hash_func = hashlib.new(hash_algorithm)

        def handle_binary(more_data):
            hash_func.update(more_data)

        self.__ftp.retrbinary(f"RETR {ftp_file_path}", handle_binary)
        return hash_func.hexdigest()

    def compare_ftp_file_metadata(self, local_file_path, ftp_file_path):
        try:
            local_stat = os.stat(local_file_path)
        except FileNotFoundError:
            return False
        ftp_size, ftp_modified_time = self.get_ftp_file_metadata(ftp_file_path)
        try:
            local_modified_time = os.path.getmtime(local_file_path)
        except FileNotFoundError:
            return False
        return (local_stat.st_size == ftp_size) and (local_modified_time == ftp_modified_time)

    def compare_ftp_file_hashes(self, local_file_path, ftp_file_path, hash_algorithm='md5'):
        if not os.path.exists(local_file_path):
            return False
        local_hash = self.calculate_file_hash(local_file_path, hash_algorithm)
        ftp_hash = self.calculate_ftp_file_hash(ftp_file_path, hash_algorithm)
        return local_hash == ftp_hash

    def compare_ftp_file(self, local_file_path, ftp_file_path):
        metadata_ret = self.compare_ftp_file_metadata(local_file_path, ftp_file_path)
        hashes_ret = self.compare_ftp_file_hashes(local_file_path, ftp_file_path)
        return metadata_ret and hashes_ret

    @staticmethod
    def calculate_file_hash(local_file_path, hash_algorithm='md5'):
        hash_func = hashlib.new(hash_algorithm)
        with open(local_file_path, 'rb') as f:
            chunk = f.read(8192)
            while chunk:
                hash_func.update(chunk)
        return hash_func.hexdigest()


def get_ftp_info_from_url(ftp_url):
    url1 = ftp_url.split('@')
    ftp_user_password = url1[0].split('://')[1]
    user_name = ftp_user_password.split(':')[0]
    password = ftp_user_password.split(':')[1]
    host = url1[1].split('/')[0]
    remote_file = ftp_url.split(host)[1]
    if ':' not in host:
        host_name = host
        port = 21
    else:
        host_name = host.split(':')[0]
        port = int(host.split(':')[1])
    ftp_info = {'host': host_name,
                'port': port,
                'user_name': user_name,
                'password': password,
                'remote_file': remote_file}
    return ftp_info


if __name__ == '__main__':
    url = 'ftp://fm:Akuvox2133!@192.168.79.211:60021/IT8X-Android/C315/rom-c315_v2.6_akcloudunion_release/' \
          '115.30.201.602/115.30.201.602.zip'
    ftp_info = get_ftp_info_from_url(url)
    print(ftp_info)
    ftp_mode = True
    ftp_client = FtpClient(ftp_info['host'], ftp_info['port'], ftp_info['user_name'], ftp_info['password'])
    ftp_client.login(ftp_mode)
    result = ftp_client.download_file('E:\\115.zip',
                                      ftp_info['remote_file'])

    ftp_client.close()
