"""
解压tgz文件
"""
import os
import re
import shutil
import tarfile
import traceback

from testcase.utils.aklibLog import aklog_printf


def extract_tgz_file(tgz_file, output_dir='output_dir'):
    """
    解压tgz文件. 传入tgz文件, 加导出文件夹路径.
    返回: 解压出来的文件夹路径
    """
    if ('\\' not in output_dir) and ('/' not in output_dir):
        base_dir = os.path.dirname(tgz_file)
        output_dir = os.path.join(base_dir, output_dir)
    try:
        shutil.rmtree(output_dir)
    except:
        pass
    # 非法字符
    pattern = r'[:*?"<>|]'
    try:
        # X915V2导出accesslog中有图片，图片文件名带冒号会抛出Invalid argument异常
        with tarfile.open(tgz_file, 'r:*') as tar:
            for member in tar.getmembers():
                # 替换不允许的字符
                safe_name = re.sub(pattern, '_', member.name)
                member.name = safe_name
                tar.extract(member, output_dir)
        # shutil.unpack_archive(tgz_file, output_dir)
        return output_dir
    except:
        aklog_printf(traceback.format_exc())
        return False
