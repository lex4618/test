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
import re
import stat
import shutil
import hashlib
import difflib
import time
import traceback
import filecmp
import zipfile
import tarfile
import tempfile
import json
from filelock import FileLock, Timeout
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class JsonFileCache(FileSystemEventHandler):
    """监控文件，只在文件变更时，才重新读取文件刷新缓存数据"""

    def __init__(self, file_path):
        self.file_path = os.path.abspath(file_path)
        self.file_name = os.path.basename(self.file_path)
        self._data = None
        self._lock = threading.Lock()
        self._last_content_hash = None
        self._load_data()
        self._start_watch()

    def _calc_file_hash(self):
        """计算文件内容hash"""
        try:
            with open(self.file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception as e:
            aklog_warn(f"计算文件hash失败: {e}")
            return None

    def _load_data(self):
        """加载文件内容到内存"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            self._last_content_hash = self._calc_file_hash()
            aklog_debug(f"{self.file_name} 缓存已刷新: {self.file_path}")
        except Exception as e:
            aklog_warn(f"加载 {self.file_name} 失败: {e}")

    def on_modified(self, event):
        """文件变更事件回调"""
        if event.src_path == self.file_path:
            with self._lock:
                new_hash = self._calc_file_hash()
                if new_hash and new_hash != self._last_content_hash:
                    aklog_debug(f"检测到 {self.file_name} 文件内容变更")
                    self._load_data()

    def _start_watch(self):
        """启动文件变更监听"""
        observer = Observer()
        observer.schedule(self, os.path.dirname(self.file_path), recursive=False)
        observer.daemon = True
        observer.start()

    @property
    def data(self):
        """获取缓存数据"""
        with self._lock:
            return self._data


def get_lock_file_path(file_path, lock_type='copy_file'):
    # 使用文件路径的哈希值生成锁文件名
    hash_object = hashlib.md5(file_path.encode())
    file_hash = hash_object.hexdigest()
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, f'{lock_type}_{file_hash}.lock')


def get_done_file_path(file_path, lock_type='copy_file'):
    # 使用文件路径的哈希值生成标志文件名
    hash_object = hashlib.md5(file_path.encode())
    file_hash = hash_object.hexdigest()
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, f'{lock_type}_{file_hash}.done')


def rename_file(old_file, new_file):
    aklog_printf('rename_file: %s, %s' % (old_file, new_file))
    try:
        if os.access(old_file, os.F_OK):
            if os.access(new_file, os.F_OK):
                os.remove(new_file)
            os.rename(old_file, new_file)
            return True
        aklog_debug(f'{old_file} not exists')
        return False
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def batch_copy_file(path, src_str, dst_str):
    aklog_printf('batch_copy_file')
    try:
        # dir_name = os.path.split(path)[-1]
        new_dir_path = os.path.join(os.path.split(path)[0], dst_str)
        if not os.path.exists(new_dir_path):
            os.makedirs(new_dir_path)
        for x in os.listdir(path):
            if src_str in x:
                file_path = os.path.join(path, x)
                new_file_name = x.replace(src_str, dst_str)
                new_file_path = os.path.join(new_dir_path, new_file_name)
                shutil.copyfile(file_path, new_file_path)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def get_file_lines(file):
    aklog_printf('get_file_lines: %s' % file)
    try:
        if os.access(file, os.R_OK):
            fp = open(file, 'r', encoding='utf-8')
            file_lines = fp.readlines()
            fp.close()
            if file_lines:
                return file_lines
            else:
                return None
    except UnicodeDecodeError:
        aklog_printf('utf-8 error')
        try:
            if os.access(file, os.R_OK):
                fp = open(file, 'r', encoding='utf-8', errors='ignore')
                file_lines = fp.readlines()
                fp.close()
                if file_lines:
                    # aklog_printf('file_lines: %r' % file_lines)
                    return file_lines
                else:
                    return None
        except:
            aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
            return None
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return None


def append_file(file, file_lines):
    aklog_printf('append_file, file: %s, file_lines: %s' % (file, file_lines))
    try:
        fp = open(file, 'a')
        fp.writelines(file_lines)
        fp.close()
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def write_file(file, file_lines, print_content=True):
    if print_content:
        aklog_printf('write_file, file: %s, file_lines: \n%s' % (file, file_lines))
    else:
        aklog_printf('write_file, file: %s' % file)
    try:
        fp = open(file, 'w')
        fp.writelines(file_lines)
        fp.close()
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def chmod_file_off_only_read(file_path):
    """windows下设置文件取消只读权限"""
    aklog_printf('chmod_file_off_only_read, file: %s' % file_path)
    try:
        if not os.access(file_path, os.F_OK):
            aklog_printf('%s is not found' % file_path)
            return False
        if not os.access(file_path, os.W_OK):
            aklog_printf('file have read-only permissions, not writable permissions')
            aklog_printf('Set the file to cancel read-only permissions')
            os.chmod(file_path, stat.S_IWRITE)
        else:
            aklog_printf('The file already has read and write access')
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def modify_file(file, old_str, new_str):
    """
    修改文件中的字符串
    :param file: 文件名
    :param old_str: 旧的字符串
    :param new_str: 新的字符串
    :return:
    """
    aklog_printf('modify_file, file: %s, old_str: %s, new_str: %s' % (file, old_str, new_str))
    try:
        file_data = ''
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                if old_str in line:
                    line = line.replace(old_str, new_str)
                file_data += line
        with open(file, 'w', encoding='utf-8') as f:
            f.write(file_data)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def batch_modify_file(path, file_name, old_str, new_str):
    """
        修改文件中的字符串
        :param path: 文件夹
        :param file_name: 文件名
        :param old_str: 旧的字符串
        :param new_str: 新的字符串
        :return:
        """
    aklog_printf('modify_file, file: %s, old_str: %s, new_str: %s' % (file_name, old_str, new_str))
    for root, dirs, files in os.walk(path):
        for file in files:
            if file == 'file_name':
                file_path = os.path.join(root, file)
                file_data = ''
                with open(file_path, 'r', encoding='utf-8') as fr:
                    for line in fr:
                        if old_str in line:
                            line = line.replace(old_str, new_str)
                        file_data += line
                with open(file_path, 'w', encoding='utf-8') as fw:
                    fw.write(file_data)


def modify_file_by_key(file, key, new_value):
    """
    文件中包含一些键值对，key = value
    匹配关键字，然后修改关键字等号后面的值，注意如果关键字存在多个相同的，会全部修改
    :param file:文件路径
    :param key:等号左值
    :param new_value:等号右值
    :return:
    """
    aklog_printf('modify_file_by_key, file: %s, key: %s, new_value: %s' % (file, key, new_value))
    try:
        file_data = ''
        with open(file, 'r') as f:
            for line in f:
                if key in line:
                    old_value = line.split('=')[1].split('\n')[0]
                    line = line.replace(old_value, ' ' + new_value)  # 在等号和value中间加空格
                file_data += line
        with open(file, 'w') as f:
            f.write(file_data)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def modify_file_by_section_key(file, section, key, new_value):
    """
    文件中包含一些键值对，key = value, 还包含一些[section]，比如ini文件
    找到section，再匹配关键字，然后修改关键字等号后面的值，考虑到不同section下的key值有可能相同，所以只会修改一次
    :param file:文件路径
    :param section:模块名称
    :param key:等号左值
    :param new_value:等号右值
    :return:
    """
    aklog_printf('modify_file, file: %s, key: %s, new_value: %s' % (file, key, new_value))
    try:
        file_data = ''
        section_dict = {section: None}
        replace_flag = False
        with open(file, 'r') as f:
            for (num, line) in enumerate(f):
                if replace_flag:
                    file_data += line
                    continue
                if '[' in line and ']' in line:
                    section_name = line.split('[')[1].split(']')[0].strip()
                    if section_name == section:
                        aklog_printf(section_name, num)
                        section_dict[section] = num
                if key in line and section_dict[section] is not None:
                    old_value = line.split('=')[1].split('\n')[0]
                    line = line.replace(old_value, ' ' + new_value)  # 在等号和value中间加空格
                    replace_flag = True
                file_data += line
        with open(file, 'w') as f:
            f.write(file_data)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def stop_handle_by_file_path(file):
    """
    删除使用中的文件, 如phone.pcap未被tshark释放。
    """
    execute = root_path + '\\tools\\handler\\handle.exe'
    ret = sub_process_get_output(execute + ' ' + '"' + file + '"')
    if ret and 'pid' in ret:
        from aklibWindow_process import cmd_close_process_by_pid
        pids = re.findall(r'pid.*?(\d+)', ret)
        aklog_debug('文件：{} 正被程序： {} 使用中.., 尝试停止'.format(file, pids))
        for pid in pids:
            cmd_close_process_by_pid(pid)
        return True
    else:
        aklog_debug('未找到文件：{} 句柄程序'.format(file))
        return False


#
# def remove_file(file, stop_handle=True):
#     if not os.path.exists(file):
#         return True
#     for i in range(2):
#         try:
#             os.remove(file)
#             aklog_printf('remove_file: %s 成功' % file)
#             return True
#         except PermissionError:
#             aklog_error('remove_file: %s 失败, 文件正被使用中' % file)
#             if stop_handle and i == 0:
#                 aklog_error('尝试关闭对应程序后重试')
#                 aklog_debug(traceback.format_exc())
#                 ret = stop_handle_by_file_path(file)
#                 # 2024.6.13 lex: 尝试, 出现多次handle超时未能删除的. 对删除phone.pcap的情况特殊处理.
#                 if not ret and file.endswith('.pcap'):
#                     aklog_warn('文件使用中, 但句柄查找失败, 暂时先kill tshark')
#                     sub_process_exec_command('taskkill /f /im tshark.exe')
#                 continue
#             else:
#                 return False
#         except:
#             aklog_error('remove_file: %s 失败' % file)
#             aklog_error('未知异常，请检查' + str(traceback.format_exc()))
#             return False

def remove_file(file, stop_handle=True):
    if not os.path.exists(file):
        return True
    for i in range(2):
        try:
            os.remove(file)
            aklog_printf('remove_file: %s 成功' % file)
            return True
        except PermissionError:
            aklog_error('remove_file: %s 失败, 文件正被使用中' % file)
            if stop_handle and i == 0 and file.endswith('.pcap'):
                # 2024.6.13 lex: 尝试, 出现多次handle超时未能删除的. 对删除phone.pcap的情况特殊处理.
                # 2024.9.2  挂测出现subprocess 句柄无效导致的后续任务失败, 去掉使用Handler方式挂测看看
                aklog_warn('.pcap文件使用中,暂时先kill tshark')
                sub_process_exec_command('taskkill /f /im tshark.exe')
                sleep(3)
                continue
            else:
                break
        except:
            aklog_error('remove_file: %s 失败' % file)
            aklog_error('未知异常，请检查' + str(traceback.format_exc()))
            return False
    aklog_error('remove_file: %s 失败' % file)
    return False


def remove_all_files(path):
    """删除目录下的文件和子文件夹"""
    aklog_printf('remove_all_files, path: %s' % path)
    try:
        ls = os.listdir(path)
        for i in ls:
            c_path = os.path.join(path, i)
            if os.path.isdir(c_path):
                if i == '.svn':
                    continue
                shutil.rmtree(c_path, True)
            else:
                os.remove(c_path)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def get_directory_size(directory, unit='GB'):
    """
    获取目录的总大小（包括子目录）
    Args:
        directory (str):
        unit (str): 文件大小单位
    """
    total_size = 0
    for root, dirs, files in os.walk(directory):
        for f in files:
            fp = os.path.join(root, f)
            total_size += os.path.getsize(fp)
    if unit == 'GB':
        total_size = total_size / (1024 ** 3)
    elif unit == 'MB':
        total_size = total_size / (1024 ** 2)
    elif unit == 'KB':
        total_size = total_size / 1024
    return total_size


def get_disk_free_space(directory, unit='GB'):
    """
    获取目录所在磁盘的剩余空间
    Args:
        directory (str):
        unit (str): 空间大小单位
    """
    total, used, free = shutil.disk_usage(directory)
    if unit == 'GB':
        free = free / (1024 ** 3)
    elif unit == 'MB':
        free = free / (1024 ** 2)
    elif unit == 'KB':
        free = free / 1024
    return free


def delete_old_files(directory, days=30):
    """
    递归删除目录及其所有子目录下的旧文件和空子目录。
    只有当文件的创建、访问、修改时间都早于指定天数，才会被删除。
    删除后如果子目录为空，也会尝试删除空子目录。

    Args:
        directory (str): 目标目录路径
        days (int): 文件/目录的时间阈值（天）

    Returns:
        bool: 删除操作是否成功
    """
    aklog_debug()
    try:
        if not os.path.exists(directory):
            aklog_debug(f'{directory} is not exists')
            return False

        now = time.time()
        cutoff = now - (days * 86400)  # 86400 秒 = 1 天

        # 递归遍历目录
        dir_count = 0
        file_count = 0
        for root, dirs, files in os.walk(directory, topdown=False):
            # 先处理文件
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    # 获取文件的创建、访问、修改时间
                    ctime = os.path.getctime(file_path)
                    atime = os.path.getatime(file_path)
                    mtime = os.path.getmtime(file_path)
                    # 判断所有时间都早于阈值才删除
                    if ctime < cutoff and atime < cutoff and mtime < cutoff:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            file_count += 1
                except Exception as fe:
                    aklog_warn(f"删除文件异常: {file_path}, {fe}")

            # 再处理目录（只删除空目录）
            for dirname in dirs:
                dir_path = os.path.join(root, dirname)
                try:
                    # 只有目录为空时才尝试删除
                    if os.path.isdir(dir_path) and not os.listdir(dir_path):
                        # 获取目录的创建时间
                        ctime = os.path.getctime(dir_path)
                        # 判断所有时间都早于阈值才删除
                        if ctime:
                            os.rmdir(dir_path)
                            dir_count += 1
                except Exception as de:
                    aklog_warn(f"删除目录异常: {dir_path}, {de}")
        aklog_debug(f'已删除{file_count}个文件，{dir_count}个文件夹')
        return True
    except Exception as e:
        aklog_warn(f"delete_old_files异常: {e}")
        return False


def check_directory_size_and_del_old_files(directory, days=30, space_required=20):
    """
    检查目录大小并删除旧文件，确保有足够的空间存储新的文件
    Args:
        directory (str): 检查的目录路径
        days (int): 要删除多少天前的文件
        space_required (int): 目录所在磁盘剩余空间要求，单位GB
    """
    aklog_debug()
    temp_dir = tempfile.gettempdir()
    lock_file_path = os.path.join(temp_dir, 'clear_outputs_old_files.lock')
    lock_timeout = 600
    lock = FileLock(lock_file_path, timeout=lock_timeout)  # 设置超时时间为600秒
    try:
        with lock:
            free_space = get_disk_free_space(directory)
            if free_space < space_required:
                directory_size = get_directory_size(directory)
                if directory_size < 2:
                    aklog_warn(f'磁盘剩余空间已不足{space_required}GB，'
                               f'并且目录{directory}占用空间小于2GB，其他目录文件占用较多空间，请检查')
                    return
                aklog_debug(f'磁盘剩余空间已小于要求的{space_required}GB，将删除 {directory} 目录下的旧文件')
                delete_old_files(directory, days)
    except Timeout:
        aklog_debug(f"锁文件存在时间超过 {lock_timeout} 秒，无法获取锁")
    except Exception as e:
        aklog_debug(f"遇到未知异常, 程序退出! {e}")


def remove_files_extension(path, extension):
    """删除目录下指定后缀的文件"""
    aklog_printf('remove_files_extension, path: %s, extension: %s' % (path, extension))
    try:
        for root, dirs, files in os.walk(path):
            for name in files:
                if name.endswith(extension):
                    os.remove(os.path.join(root, name))
                    aklog_printf("Delete File: " + os.path.join(root, name))
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def remove_files_by_file_name(path, file_name):
    """删除目录下指定文件名的文件"""
    aklog_printf('remove_files_by_file_name, path: %s, file_name: %s' % (path, file_name))
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file == file_name:
                    os.remove(os.path.join(root, file))
                    aklog_printf("Delete File: " + os.path.join(root, file))
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def remove_dirs_by_dir_name(path, dir_name):
    """删除目录下指定文件夹名称的文件夹"""
    aklog_printf('remove_dirs_by_dir_name, path: %s, dir_name: %s' % (path, dir_name))
    try:
        for root, dirs, files in os.walk(path):
            for x in dirs:
                if x == dir_name:
                    dir_path = os.path.join(root, x)
                    shutil.rmtree(dir_path, True)
                    aklog_printf("Delete Dir: " + dir_path)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def remove_dir(path):
    """删除整个目录，包括目录下的文件和子文件夹"""
    aklog_printf('remove_dir, path: %s' % path)
    if os.path.isdir(path):
        retry_counts = 5
        for i in range(retry_counts):
            try:
                shutil.rmtree(path)
                aklog_printf('remove dir success')
                return True
            except:
                if i < retry_counts - 1:
                    # 2024.6.20 lex: jenkins报告出现卡住的问题目前都跟phone.pcap有关， 先加一个尝试看看效果。
                    exc = traceback.format_exc()
                    if 'phone.pcap' in exc and '另一个程序正在使用此文件' in exc:
                        sub_process_exec_command('taskkill /f /im tshark.exe')
                    aklog_printf('remove dir failed, it could be that the file is already in use, retry...')
                    time.sleep(6)
                    continue
                else:
                    aklog_printf('remove dir failed, ' + traceback.format_exc())
                    return False
    else:
        aklog_printf('%s is not found' % path)
        return False


def create_dir(path):
    """递归创建目录"""
    aklog_printf('create_dir: %s' % path)
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return True
    except:
        aklog_printf(traceback.format_exc())
        return False


def copy_file(src_file, dst_file):
    aklog_printf('copy_file, from: %s, to: %s' % (src_file, dst_file))
    if not src_file:
        aklog_printf('源文件为空')
        return False
    if os.access(src_file, os.R_OK):
        if os.path.exists(dst_file):
            cmp_result = compare_file_metadata(src_file, dst_file)
            if cmp_result:
                aklog_printf('文件已存在并相同，无需再复制')
                return True
            try:
                os.remove(dst_file)
            except:
                pass
        dst_file_dir = os.path.split(dst_file)[0]
        if not os.path.exists(dst_file_dir):
            os.makedirs(dst_file_dir)
        retry_counts = 30
        for i in range(retry_counts):
            try:
                shutil.copy2(src_file, dst_file)
                aklog_printf('copy file success')
                return True
            except PermissionError:
                if i < 3:
                    aklog_printf('copy file failed: PermissionError, retry...')
                    time.sleep(6)
                    continue
                else:
                    aklog_printf('copy file failed, ' + traceback.format_exc())
                    return False
            except:
                if i < retry_counts - 1:
                    aklog_printf('copy file failed, retry...')
                    time.sleep(6)
                    continue
                else:
                    aklog_printf('copy file failed, ' + traceback.format_exc())
                    return False
    else:
        aklog_printf('%s is not found or unreadable' % src_file)
        return False


def copy_whole_dir(src_dir, dst_dir):
    """复制整个文件夹"""
    aklog_printf('copy_whole_dir, from: %s, to: %s' % (src_dir, dst_dir))
    dst_dir_parent = os.path.split(dst_dir)[0]
    if not os.path.exists(dst_dir_parent):
        os.makedirs(dst_dir_parent)
    if os.access(src_dir, os.R_OK):
        shutil.copytree(src_dir, dst_dir)
    else:
        aklog_printf('%s is not found or unreadable' % src_dir)
        return False


def copy_files_whole_dir(src_dir, dst_dir, *excludes):
    """复制整个文件夹下的所有文件到目标文件夹"""
    aklog_printf('copy_files_whole_dir, from: %s, to: %s' % (src_dir, dst_dir))
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    if os.access(src_dir, os.R_OK):
        for x in os.listdir(src_dir):
            if x in excludes:
                continue  # 排除文件不复制
            src = os.path.join(src_dir, x)
            target = os.path.join(dst_dir, x)
            if os.path.isdir(src):
                shutil.copytree(src, target)
            else:
                shutil.copyfile(src, target)
        return True
    else:
        aklog_printf('%s is not found or unreadable' % src_dir)
        return False


def copy_folder_to_network_share(local_folder, network_share, base_folder):
    # 将本地文件夹路径中的盘符和初始斜杠替换掉以适应网络共享路径
    relative_path = local_folder.replace(base_folder, "").lstrip("\\").lstrip("/")
    destination_folder = os.path.join(network_share, relative_path)

    # 如果目标目录已存在，先删除
    if os.path.exists(destination_folder):
        try:
            shutil.rmtree(destination_folder)
            aklog_printf(f"Deleted existing directory: {destination_folder}")
        except Exception as e:
            aklog_printf(f"Error deleting directory: {e}")
            return False

    # 复制整个文件夹内容到目标路径
    try:
        shutil.copytree(local_folder, destination_folder)
        aklog_printf(f"Successfully copied {local_folder} to {destination_folder}")
        return True
    except Exception as e:
        aklog_printf(f"Error copying folder: {e}")
        return False


def move_file(src_file, dst_file):
    aklog_printf('move_file, from: %s, to: %s' % (src_file, dst_file))
    dst_file_dir = os.path.split(dst_file)[0]
    if not os.path.exists(dst_file_dir):
        os.makedirs(dst_file_dir)
    if os.access(src_file, os.W_OK):
        retry_counts = 30
        for i in range(retry_counts):
            try:
                shutil.move(src_file, dst_file)
                aklog_printf('move file success')
                return True
            except:
                if i < retry_counts - 1:
                    aklog_printf('move file failed, it could be that the file is already in use, retry...')
                    time.sleep(6)
                    continue
                else:
                    aklog_printf('move file failed, ' + traceback.format_exc())
                    return False
    else:
        aklog_printf('%s is not found or unreadable' % src_file)
        return False


def copy_files_with_ext_from_path(src_dir, dst_dir, extension):
    """将目录下的所有指定后缀文件复制到目标目录下"""
    aklog_printf('copy_files_with_ext_from_path, ext: %s, from %s, to %s' % (extension, src_dir, dst_dir))
    try:
        src_files = get_files_with_ext_from_path(src_dir, extension)
        if not src_files:
            aklog_printf('目录下没有找到指定后缀格式的文件')
            return False
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for src_file in src_files:
            src_file_path = os.path.join(src_dir, src_file)
            dst_file_path = os.path.join(dst_dir, src_file)
            shutil.copyfile(src_file_path, dst_file_path)
            aklog_printf('copy file success, from: %s, to: %s' % (src_file_path, dst_file_path))
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def compare_file_content(file1, file2):
    aklog_printf('compare_file_content: %s, %s' % (file1, file2))
    try:
        file1_lines = get_file_lines(file1)
        file2_lines = get_file_lines(file2)
        diff = difflib.ndiff(file1_lines, file2_lines)
        sys.stdout.writelines(diff)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def compare_file(file1, file2, shallow=True):
    """比较文件，如果文件的大小和修改日期相同，则会认为两个文件是一致的，完成快速比较。
    如果不一致，则会再详细对比文件，如果是共享文件夹的文件，则会下载下来比较"""
    aklog_printf('compare_file: %s, %s' % (file1, file2))
    try:
        status = filecmp.cmp(file1, file2, shallow=shallow)
        # 为True表示两文件相同
        if status:
            aklog_printf("files are the same")
            return True
        # 为False表示文件不相同
        else:
            aklog_printf("files are different")
            return False
        # 如果两边路径头文件不都存在，抛异常
    except:
        aklog_printf("Error: File not found or failed to read. " + str(traceback.format_exc()))
        return None


def compare_file_metadata(file1, file2):
    aklog_printf()
    if not os.path.exists(file1) or not os.path.exists(file2):
        aklog_printf("files are not exists")
        return False
    stat1 = os.stat(file1)
    stat2 = os.stat(file2)
    if (stat1.st_size == stat2.st_size) and (stat1.st_mtime == stat2.st_mtime):
        aklog_printf('files are the same')
        return True
    else:
        aklog_printf("files are different")
        return False


def calculate_file_hash(file_path, hash_algorithm='md5'):
    hash_func = hashlib.new(hash_algorithm)
    with open(file_path, 'rb') as f:
        chunk = f.read(8192)
        while chunk:
            hash_func.update(chunk)
    return hash_func.hexdigest()


def compare_file_hashes(file1, file2, hash_algorithm='md5'):
    aklog_printf()
    hash1 = calculate_file_hash(file1, hash_algorithm)
    hash2 = calculate_file_hash(file2, hash_algorithm)
    if hash1 == hash2:
        aklog_printf('files are the same')
        return True
    else:
        aklog_printf("files are different")
        return False


def compare_config_value(cfg_file, template_file):
    """
    对比配置项autop升级是否成功
    也可以对比autop配置文件，判断配置项值是否被修改，比如判断升级后配置项值是否跟升级前一致
    注意不要包含url配置项，因为导出后url配置项会被清空
    """
    aklog_printf('compare_config_value: %s, %s' % (cfg_file, template_file))
    try:
        if not cfg_file or not template_file:
            return None
        diff = []
        file1_lines = get_file_lines(cfg_file)
        file2_lines = get_file_lines(template_file)
        counts = 0
        for line1 in file1_lines:
            # 过滤掉非配置项和一些url、密码的配置项
            if line1.startswith('#') or '=' not in line1 or '.url' in line1 \
                    or line1.startswith(';') or len(line1.split('=')[1].strip()) == 60:
                continue
            elif line1 in file2_lines:
                counts += 1
                continue
            else:
                counts += 1
                # 如果不相同再进一步判断
                line1_key = line1.split("=")[0].strip()
                line1_value = line1.split("=")[1].strip()
                for line2 in file2_lines:
                    if line2.startswith('#') or '=' not in line2:
                        continue
                    elif line1_key in line2 and line1_value != line2.split("=")[1].strip():
                        aklog_printf('存在不同配置项，cfg_file的配置项: %s，template_file的配置项：%s' % (line1, line2))
                        diff.append(line1)
                        break
        if counts == 0:
            # 如果可以进行升级的配置项数量为0，说明cfg配置文件有问题
            aklog_printf('可以进行autop配置的配置项数量为0，说明cfg配置文件有问题，请检查')
            return None
        else:
            return diff
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return None


def compare_config_key(cfg_file, template_file):
    """对比配置项autop升级是否成功"""
    aklog_printf('compare_config_key: %s, %s' % (cfg_file, template_file))
    try:
        diff = []
        file1_lines = get_file_lines(cfg_file)
        file2_lines = get_file_lines(template_file)
        for line1 in file1_lines:
            if line1.startswith('#') or '=' not in line1:
                continue
            contain_flag = 0
            for line2 in file2_lines:
                if line1.split(" ")[0].split("=")[0] in line2:
                    contain_flag = 1
                    break
            if contain_flag == 0:
                aklog_printf('不同配置项: %s' % line1)
                diff.append(line1)
        return diff
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return None


def compare_config_is_in_file(config, config_file):
    aklog_printf('compare_config_is_in_file: %s, %s' % (config, config_file))
    try:
        file_lines = get_file_lines(config_file)
        for line in file_lines:
            if '=' not in line:
                continue
            line = line.strip()
            if config == line:
                return True
            else:
                continue
        aklog_printf('%s not in config file' % config)
        return False
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def compare_default_config_value(export_file, template_file):
    aklog_printf('compare_default_config_value: %s, %s' % (export_file, template_file))
    try:
        diff_export = []
        diff_template = []
        export_file_lines = get_file_lines(export_file)
        template_file_lines = get_file_lines(template_file)
        # 判断导出文件内容是否都包含在模板文件里且一致
        for export_file_line in export_file_lines:
            if export_file_line[0] == '#':
                continue
            elif '=' not in export_file_line:
                continue
            elif len(export_file_line.split('=')[1]) == 62:
                continue
            elif export_file_line not in template_file_lines:
                aklog_printf('导出文件中不同配置项: %s' % export_file_line)
                diff_export.append(export_file_line)
        # 判断模板文件内容是否都包含在导出文件里且一致
        for template_file_line in template_file_lines:
            if template_file_line[0] == '#':
                continue
            if '=' not in template_file_line:
                continue
            elif len(template_file_line.split('=')[1]) == 62:
                continue
            elif template_file_line not in export_file_lines:
                aklog_printf('模板文件中不同配置项: %s' % template_file_line)
                diff_template.append(template_file_line)
        # if not diff_export and not diff_template:
        #     aklog_printf('配置文件相同')
        #     return [], []
        # else:
        #     aklog_printf('配置文件不同')
        return diff_export, diff_template
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return None, None


def get_file_md5(file_path):
    aklog_printf()
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        aklog_error(f"读取本地文件失败: {file_path}, 错误: {e}")
        aklog_debug(traceback.format_exc())
        return None


def get_files_from_path(path):
    """ 获取指定目录下所有文件的文件名列表，不包括子目录"""
    # os.listdir(path):获取目录下的所有文件或文件夹
    aklog_printf('get_files_from_path, %s' % path)
    if not os.path.exists(path):
        aklog_printf('%s is not exist' % path)
        return None
    files = []
    for i in os.listdir(path):
        file_path = os.path.join(path, i)
        if os.path.isfile(file_path):
            files.append(i)
    aklog_printf('files: %r' % files)
    return files


def get_files_with_ext_from_path(path, extension):
    """ 获取指定目录下的指定后缀的文件 """
    # os.listdir(path):获取目录下的所有文件或文件夹
    aklog_printf('get_files_with_ext_from_path, %s, ext: %s' % (path, extension))
    if not os.path.exists(path):
        aklog_printf('%s is not exist' % path)
        return None
    files = []
    for i in os.listdir(path):
        # os.path.splitext():分离文件名与扩展名
        if os.path.splitext(i)[1] == extension:  # extension扩展名包含点
            files.append(i)
    aklog_printf('files: %r' % files)
    return files


def get_file_with_ext_from_path(path, extension):
    """ 获取指定目录下的指定后缀的文件，如果有多个文件取第一个文件，用于这个目录下只有一个该格式的文件"""
    # os.listdir(path):获取目录下的所有文件或文件夹
    for i in os.listdir(path):
        # os.path.splitext():分离文件名与扩展名
        file_name, ext = os.path.splitext(i)
        if ext == extension:  # extension扩展名包含点
            aklog_printf('get_file_with_ext_from_path: %s' % file_name)
            return file_name
    return None


def get_file_path_with_ext_from_dir(path, extension):
    """ 获取指定目录下的指定后缀的文件，如果有多个文件取第一个文件，用于这个目录下只有一个该格式的文件"""
    # os.listdir(path):获取目录下的所有文件或文件夹
    for i in os.listdir(path):
        # os.path.splitext():分离文件名与扩展名
        file_name, ext = os.path.splitext(i)
        if ext == extension:  # extension扩展名包含点
            aklog_printf('get_file_path_with_ext_from_dir: %s' % i)
            return i
    return None


def get_dirs_from_path(path):
    """ 获取指定目录下的所有子文件夹路径，返回List """
    dir_paths = []
    for root, dirs, files in os.walk(path):
        for x in dirs:
            dir_path = os.path.join(root, x)
            dir_paths.append(dir_path)
    return dir_paths


def get_file_with_filename_from_path(path, file_name):
    """ 获取指定目录下的指定文件名的文件路径 """
    for root, dirs, files in os.walk(path):
        for file in files:
            if file == file_name:
                file_path = os.path.join(root, file)  # 合并成一个完整路径
                return file_path
    return None


def get_firmware_by_version_from_path(path, file_name):
    """ 获取指定目录下的指定文件名的文件路径, 只适用于搜索设备端版本号"""
    for root, dirs, files in os.walk(path):
        for file in files:
            version, ext = os.path.splitext(file_name)
            if (file.endswith(ext)
                    and re.sub(r'\D', '', file) == re.sub(r'\D', '', file_name)
                    and 'firmware' not in file):
                file_path = os.path.join(root, file)  # 合并成一个完整路径
                return file_path
    return None


def get_file_paths_with_ext_from_dir(path, extension, recursion=True):
    """ 获取指定目录下的指定文件名的文件路径 """
    aklog_printf('get_file_paths_with_ext_from_dir, path: %s, extension: %s' % (path, extension))
    if not os.path.exists(path):
        aklog_printf('%s is not exist' % path)
        return None
    file_paths = []
    if recursion:
        for root, dirs, files in os.walk(path):
            for file in files:
                if os.path.splitext(file)[1] == extension:
                    file_path = os.path.join(root, file)
                    file_paths.append(file_path)
    else:
        for file in os.listdir(path):
            # os.path.splitext():分离文件名与扩展名
            if os.path.splitext(file)[1] == extension:  # extension扩展名包含点
                file_path = os.path.join(path, file)
                file_paths.append(file_path)
    aklog_printf('file_paths: %r' % file_paths)
    return file_paths


def get_file_dirname_from_path(file_path):
    """根据完整路径获取目录名称"""
    if file_path:
        file_dir, file = os.path.split(file_path)
        file_dirname = os.path.split(file_dir)[1]
        return file_dirname
    else:
        return None


def get_diff_file_from_path(path, cmp_file):
    """从目录下获取不同文件名的其他文件路径，目录中只有两个文件"""
    aklog_printf("get_diff_file_from_path")
    for root, dirs, files in os.walk(path):
        for file in files:
            if file != cmp_file:
                file_path = os.path.join(root, file)
                file_name = os.path.splitext(file)[0]
                return file_name, file_path


def zip_dir(dir_path, zip_file):
    """
    将目录中的文件添加到zip包
    :param dir_path:
    :param zip_file: 绝对路径
    :return:
    """
    aklog_printf('zip_dir, dir_path: %s, zipfile_name: %s' % (dir_path, zip_file))
    filelist = []
    if os.path.isfile(dir_path):
        filelist.append(dir_path)
    else:
        for root, dirs, files in os.walk(dir_path):
            for name in files:
                filelist.append(os.path.join(root, name))
    zf = zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED)
    for tar in filelist:
        arcname = tar[len(dir_path):]
        # aklog_printf(arcname)
        zf.write(tar, arcname)
    zf.close()


def get_file_size_mb(file_path):
    """获取文件的大小,结果保留两位小数，单位为MB"""
    if os.path.isfile(file_path):
        f_size = os.path.getsize(file_path)
        f_size = round(f_size / float(1024 * 1024), 2)
        # aklog_printf('file size: %s MB' % f_size)
        return f_size
    else:
        aklog_printf('%s is not exist' % file_path)
        return 0


def get_file_size(file_path, unit='MB'):
    """获取文件的大小,结果保留两位小数"""
    if os.path.isfile(file_path):
        f_size = os.path.getsize(file_path)
        if unit == 'MB':
            f_size = round(f_size / float(1024 * 1024), 2)
            aklog_printf('file size: %s MB' % f_size)
        elif unit == 'KB':
            f_size = round(float(f_size) / 1024, 2)
            aklog_printf('file size: %s KB' % f_size)
        return f_size
    else:
        aklog_printf('%s is not exist' % file_path)
        return 0


def wait_for_file_upload_complete(file_path: str,
                                  check_interval: float = 1.0,
                                  stable_times: int = 5,
                                  timeout: float = 300.0) -> bool:
    """
    等待文件上传完成（通过判断文件大小是否稳定）

    :param file_path: 文件路径
    :param check_interval: 检查间隔时间（秒）
    :param stable_times: 连续多少次大小一致才认为完成
    :param timeout: 最大等待时间（秒）
    :return: True 表示上传完成，False 表示超时
    """
    end_time = time.time() + 5
    file_exists = False
    while time.time() < end_time:
        if os.path.exists(file_path):
            file_exists = True
            break
    if not file_exists:
        aklog_warn(f"文件不存在: {file_path}")
        return False

    aklog_debug(f"开始监控文件上传: {file_path}")
    start_time = time.time()
    last_size: Optional[int] = None
    stable_count = 0

    while time.time() - start_time < timeout:
        try:
            current_size = os.path.getsize(file_path)
        except Exception as e:
            aklog_error(f"获取文件大小失败: {e}")
            return False

        if current_size == last_size:
            stable_count += 1
            # aklog_debug(f"文件大小稳定: {current_size} bytes（{stable_count}/{stable_times}）")
            if stable_count >= stable_times:
                aklog_debug(f"文件上传完成: {file_path}，最终大小: {current_size} bytes")
                return True
        else:
            # aklog_debug(f"文件大小变化: {last_size} -> {current_size}")
            stable_count = 0
            last_size = current_size

        time.sleep(check_interval)

    aklog_warn(f"等待文件上传超时: {file_path}")
    return False


def rename_file_to_list(file_list: list, file_path):
    """重命名文件并返回文件名列表"""
    aklog_printf('rename_file_to_list, %s' % file_path)
    if os.path.exists(file_path):
        file_dir, file = os.path.split(file_path)
        file_name, ext = os.path.splitext(file)
        new_file_name = file_name + '-' + str(len(file_list) + 1)
        new_file = new_file_name + ext
        new_file_path = os.path.join(file_dir, new_file)
        rename_file(file_path, new_file_path)
        file_list.append(new_file)
    return file_list


def tar_file(fname):
    """压缩文件"""
    t = tarfile.open(fname + ".tar.gz", "w:gz")
    for root, _dir, files in os.walk(fname):
        print(root, _dir, files)
        for file in files:
            fullpath = os.path.join(root, file)
            t.add(fullpath)
    t.close()


def untar_file(fname, dirs):
    """解压文件"""
    t = tarfile.open(fname)
    t.extractall(path=dirs)
    t.close()


# 修改用例文件和基类文件
def modify_test_case_index(case_file, prefix='test_'):
    """
    修改测试用例序号，利用正则表达式匹配用例的名称开头格式：test_01_，然后按照顺序修改序号
    :param case_file: 用例文件路径
    :param prefix: 用例的前缀
    :return:
    """
    try:
        file_data = ''
        i = 1
        counts = 0
        with open(case_file, 'r', encoding='utf-8') as f:
            # 先获取用例的数量，如果用例数超过100个，则用例序号要改为001,002这样
            for line in f:
                flag = re.search(r'def %s.\d' % prefix, line)
                if flag:
                    if '#' in line or 'def %s00' % prefix in line:
                        continue
                    counts += 1
            aklog_printf('test case counts: %s' % counts)

        # 读取文件并修改用例序号
        with open(case_file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'def %s00' % prefix in line:
                    file_data += line
                    continue
                flag = re.search(r'def %s.\d' % prefix, line)
                if flag:
                    if '#' in line:
                        file_data += line
                        continue
                    if counts < 100:
                        new_line = re.sub(r'def %s.\d' % prefix, 'def %s%02d' % (prefix, i), line)
                    else:
                        new_line = re.sub(r'def %s.\d' % prefix, 'def %s%03d' % (prefix, i), line)
                    i += 1
                else:
                    new_line = line
                file_data += new_line
        # 写入文件
        with open(case_file, 'w', encoding='utf-8') as f:
            f.write(file_data)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def modify_test_case_control_base(case_file):
    """
    修改测试用例的setUpClass里面，使用control_base初始化设备方法
    :param case_file: 用例文件路径
    :return:
    """
    try:
        file_data = ''

        # 读取文件并修改control_base调用方法
        with open(case_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                line = lines[i]
                flag = re.search(r'cls\..*=.*control_base\..*_init\(', line)
                if flag and '_login' not in line:
                    # 匹配到调用control_base初始化方法这一行
                    line_space = line.split('cls.')[0]
                    key = line.split('control_base.')[0].replace('=', '').strip()

                    value = line.split('control_base.')[1].strip()
                    new_line = f'{line_space}control_base.{value}\n'

                    j = 0
                    # 如果不是)结尾，说明control_base初始化方法调用分多行了
                    if not line.strip().endswith(')'):
                        j = 1
                        # 如果结尾是逗号，说明有传参，并且还有参数在第二行，那么第二行需要修改缩进到跟第一行一样
                        if line.strip().endswith(','):
                            line2_space = ' ' * (len(new_line.split('(')[0]) + 1)

                        while True:
                            if line.strip().endswith(','):
                                new_line += line2_space + lines[i + j].strip() + '\n'
                            else:
                                new_line += lines[i + j]
                            if lines[i + j].strip().endswith(')'):
                                break
                            else:
                                j += 1
                    i += (j + 1)
                    value1 = key.replace('cls.', 'control_base.')
                    new_line += f'{line_space}{key} = {value1}\n'
                    file_data += new_line
                    continue
                else:
                    i += 1
                    file_data += line
                    continue

        # 写入文件
        with open(case_file, 'w', encoding='utf-8') as f:
            f.write(file_data)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def batch_modify_test_case_control_base(case_dir):
    file_paths = []
    for root, dirs, files in os.walk(case_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.py':
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
    aklog_printf('file_paths: %r' % file_paths)

    for file in file_paths:
        modify_test_case_control_base(file)


def modify_base_module_device_name_log(file):
    """基类文件里的方法增加device_name标志，log打印更清楚是哪一台设备的操作"""
    try:
        file_data = ''
        # 读取文件并修改
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'aklog_printf' in line and 'self.device_name_log' not in line and 'aklog_printf(\n' not in line:
                    new_line = line.replace('aklog_printf(', 'aklog_printf(self.device_name_log + ')
                else:
                    new_line = line
                file_data += new_line
        # 写入文件
        with open(file, 'w', encoding='utf-8') as f:
            f.write(file_data)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def modify_base_module_log_level_error(file):
    """
    基础库方法，打印失败、错误等log时，使用aklog_error等级，测试报告根据log等级进行着色
    思路：过滤aklog_printf这一行，计算左括号有几个，以及右括号几个，判断是否为最后一个右括号为行尾，如果是，判断打印的log中是否存在失败、错误等字眼，修改为aklog_error
    如果不是，则在下一行，继续计算左括号有几个，右括号有几个，判断是否为最后一个右括号为行尾，以此类推直到找到最后一个右括号

    """
    aklog_printf()
    try:
        new_lines = []
        log_error_count = 0
        # 读取文件并修改
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                j = 0
                if 'aklog_' in lines[i]:
                    left_bracket_count = 0
                    right_bracket_count = 0
                    log_line = ''
                    while j < len(lines):
                        left_bracket_count += lines[i + j].count('(')
                        right_bracket_count += lines[i + j].count(')')
                        log_line += lines[i + j]
                        if left_bracket_count == right_bracket_count and lines[i + j].endswith(')\n'):
                            if '失败' in log_line or 'fail' in log_line.lower() \
                                    or 'error' in log_line.lower() or '错误' in log_line \
                                    or '不正确' in log_line or '不一致' in log_line or '请检查' in log_line \
                                    or '无法' in log_line or '异常' in log_line or '不存在' in log_line \
                                    or 'traceback' in log_line:
                                if 'return True' in lines[i + j + 1]:
                                    # 如果打印log的下一行为return True，则不修改log等级
                                    print(log_line)
                                    new_lines.append(log_line)
                                    break
                                log_line = log_line.replace('aklog_info', 'aklog_error'). \
                                    replace('aklog_printf', 'aklog_error'). \
                                    replace('aklog_debug', 'aklog_error')
                                log_error_count += 1
                            new_lines.append(log_line)
                            break
                        else:
                            j += 1
                else:
                    new_lines.append(lines[i])
                i += j + 1
        print('log_error_count: %s' % log_error_count)
        file_data = ''.join(new_lines)
        # 写入文件
        with open(file, 'w', encoding='utf-8') as f:
            f.write(file_data)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def modify_base_module_log_level_info(file):
    """
    base web基类，除了通用相关改为debug之外，其他的都改为info
    思路：过滤aklog_printf这一行，计算左括号有几个，以及右括号几个，判断是否为最后一个右括号为行尾，如果是，判断打印的log中是否存在失败、错误等字眼，修改为aklog_error
    如果不是，则在下一行，继续计算左括号有几个，右括号有几个，判断是否为最后一个右括号为行尾，以此类推直到找到最后一个右括号

    """
    aklog_printf()
    try:
        new_lines = []
        log_info_count = 0
        log_debug_count = 0
        # 读取文件并修改
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                j = 0
                if '# <editor-fold desc="通用相关">' in lines[i] or '# <editor-fold desc="通用API">' in lines[i]:
                    while j < len(lines):
                        if 'aklog_printf' in lines[i + j]:
                            new_line = lines[i + j].replace('aklog_printf', 'aklog_debug')
                            log_debug_count += 1
                        else:
                            new_line = lines[i + j]
                        new_lines.append(new_line)
                        if '# </editor-fold>' in lines[i + j]:
                            break
                        j += 1
                else:
                    if 'aklog_printf' in lines[i + j]:
                        new_line = lines[i].replace('aklog_printf', 'aklog_info')
                        log_info_count += 1
                    else:
                        new_line = lines[i]
                    new_lines.append(new_line)
                i += j + 1
        print('log_debug_count: %s' % log_debug_count)
        print('log_info_count: %s' % log_info_count)
        file_data = ''.join(new_lines)
        # 写入文件
        with open(file, 'w', encoding='utf-8') as f:
            f.write(file_data)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def get_base_module_file_paths_from_dir(path, filename_prefix, file_folder):
    """获取base和web基类文件"""
    aklog_printf('get_file_paths_with_ext_from_dir, path: %s, filename_prefix: %s' % (path, filename_prefix))
    if not os.path.exists(path):
        aklog_printf('%s is not exist' % path)
        return None
    file_paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if os.path.splitext(file)[1] == '.py' and file.startswith(filename_prefix) and root.endswith(file_folder):
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
    aklog_printf('file_paths: %r' % file_paths)
    return file_paths


def modify_base_web_module_log_level(base_dir):
    """修改机型Base目录下base和web基类的log等级为info、error、debug"""
    base_file_paths = get_base_module_file_paths_from_dir(base_dir, 'libDistributorInterfaceBase_', 'Base')
    web_file_paths = get_base_module_file_paths_from_dir(base_dir, 'libInstallerInterfaceBase_', 'Base')
    control_base_file_paths = get_base_module_file_paths_from_dir(base_dir, 'libInterfaceBase_', 'Base')
    Operation_file_paths = get_base_module_file_paths_from_dir(base_dir, 'libOperationInterfaceBase_', 'Base')
    base_file_paths.extend(web_file_paths)
    base_file_paths.extend(control_base_file_paths)
    base_file_paths.extend(Operation_file_paths)
    for base_file in base_file_paths:
        modify_base_module_log_level_info(base_file)
        modify_base_module_log_level_error(base_file)


def modify_editor_fold_to_region(file):
    aklog_info()
    try:
        file_data = ''
        # 读取文件并修改
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                if '# <editor-fold desc="' in line:
                    new_line = line.replace('# <editor-fold desc="', '# region ').replace('">', '')
                elif '# </editor-fold>' in line:
                    new_line = line.replace('# </editor-fold>', '# endregion')
                else:
                    new_line = line
                file_data += new_line
        # 写入文件
        with open(file, 'w', encoding='utf-8') as f:
            f.write(file_data)
        return True
    except:
        aklog_printf('未知异常，请检查' + str(traceback.format_exc()))
        return False


def batch_modify_editor_fold_to_region(path):
    file_paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if os.path.splitext(file)[1] == '.py':
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
    aklog_printf('file_paths: %r' % file_paths)

    for file in file_paths:
        modify_editor_fold_to_region(file)


def batch_modify_files_series_name(base_dir, series_name, new_series_name):
    """
    批量修改文件名的系列名称
    series_name: ANDROIDINDOOR_NORMAL
    new_series_name: ANDROIDINDOORV6_NORMAL
    """
    file_paths = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.py' and series_name in file:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
    aklog_printf('file_paths: %r' % file_paths)
    for file in file_paths:
        new_file = file.replace(series_name, new_series_name)
        rename_file(file, new_file)


def clear_lock_file():
    temp_dir = tempfile.gettempdir()
    lock_files = get_file_paths_with_ext_from_dir(temp_dir, '.lock')
    for lock_file in lock_files:
        os.remove(lock_file)


if __name__ == "__main__":
    print('测试代码')
    src = r'\\192.168.13.53\tsHome\AndroidSpace\PSX\Rom-v31\rom-ps51_v31_akubela_release\51.1.31.57.zip'
    dst = r'E:\SVN_Python\Develop\AKautotest\testfile\Firmware\PS51\51.1.31.57.zip'
    compare_file(src, dst)
