# -*- coding: utf-8 -*-
import json
from zipfile import ZipFile
import win32api
import sys
import os
import winreg

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *


# def get_path_by_reg(mainkey, subkey):
#     "通过注册表获取程序安装路径"
#     try:
#         key = winreg.OpenKey(mainkey, subkey)
#     except FileNotFoundError:
#         return '未安装'
#     value, Type = winreg.QueryValueEx(key, "")  # 获取默认值
#     full_file_path = value.split(',')[0]  # 截去逗号后面的部分
#     # [dir_name, file_name] = os.path.split(full_file_name)  # 分离文件名和路径
#     return full_file_path
#
#
# def get_current_user_chrome_path_by_reg():
#     """有些环境chrome没有安装在C盘的Program files里面，而是安装在当前用户的目录下"""
#     start_menu_internet_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Clients\StartMenuInternet')
#     browser_key = ''
#     for i in range(10):
#         try:
#             browser_key = winreg.EnumKey(start_menu_internet_key, i)
#             if 'Google Chrome' in browser_key:
#                 break
#         except:
#             aklog_printf('获取Google Chrome路径失败')
#             break
#     key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Clients\StartMenuInternet\%s\DefaultIcon' % browser_key)
#     value, Type = winreg.QueryValueEx(key, "")  # 获取默认值
#     full_file_path = value.split(',')[0]  # 截去逗号后面的部分
#     # aklog_printf('chrome_path: %s' % full_file_path)
#     return full_file_path


def get_file_properties(file_path):
    """
    Read all properties of the given file return them as a dictionary.
    """
    propNames = ('Comments', 'InternalName', 'ProductName',
                 'CompanyName', 'LegalCopyright', 'ProductVersion',
                 'FileDescription', 'LegalTrademarks', 'PrivateBuild',
                 'FileVersion', 'OriginalFilename', 'SpecialBuild')

    props = {'FixedFileInfo': None, 'StringFileInfo': None, 'FileVersion': None}

    try:
        # backslash as parm returns dictionary of numeric info corresponding to VS_FIXEDFILEINFO struc
        fixedInfo = win32api.GetFileVersionInfo(file_path, '\\')
        props['FixedFileInfo'] = fixedInfo
        props['FileVersion'] = "%d.%d.%d.%d" % (fixedInfo['FileVersionMS'] / 65536,
                                                fixedInfo['FileVersionMS'] % 65536, fixedInfo['FileVersionLS'] / 65536,
                                                fixedInfo['FileVersionLS'] % 65536)

        # \VarFileInfo\Translation returns list of available (language, codepage)
        # pairs that can be used to retreive string info. We are using only the first pair.
        lang, codepage = win32api.GetFileVersionInfo(file_path, '\\VarFileInfo\\Translation')[0]

        # any other must be of the form \StringfileInfo\%04X%04X\parm_name, middle
        # two are language/codepage pair returned from above

        strInfo = {}
        for propName in propNames:
            strInfoPath = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage, propName)
            # print str_info
            strInfo[propName] = win32api.GetFileVersionInfo(file_path, strInfoPath)

        props['StringFileInfo'] = strInfo
    except:
        pass

    return props


def get_chrome_version():
    """获取chrome浏览器版本号"""
    aklog_printf('get_chrome_version')
    # 获取chrome浏览器的安装路径
    ico_google = r"SOFTWARE\Clients\StartMenuInternet\Google Chrome\DefaultIcon"
    chrome_browser = WindowsReg.reg_get_application_path(winreg.HKEY_LOCAL_MACHINE, ico_google)
    if not os.path.exists(chrome_browser):
        chrome_browser = WindowsReg.reg_get_current_user_chrome_path()
    aklog_printf('chrome_path: %s' % chrome_browser)
    cb_dictionary = get_file_properties(chrome_browser)  # returns whole string of version (ie. 76.0.111)
    # print(cb_dictionary)
    chrome_version = cb_dictionary['FileVersion']
    aklog_printf('chrome_version: %s' % chrome_version)
    # chrome_big_version = chrome_version[:2]
    return chrome_version


def get_current_driver_version(driver_path):
    """获取当前驱动版本号"""
    aklog_printf('get_current_driver_version')
    cmd = driver_path + ' --version'
    ret = sub_process_get_output(cmd)
    if ret and 'ChromeDriver' in ret:
        driver_version = ret.split(' ')[1]
        aklog_printf('driver_version: %s' % driver_version)
        return driver_version
    else:
        return None


def download_driver(big_version):
    aklog_printf('download_driver')
    try:
        ak_requests = AkRequests()
        ret = None
        for i in range(3):
            ret = ak_requests.send_get('https://registry.npmmirror.com/-/binary/chromedriver', print_resp=False)
            if ret:
                break
            elif i < 2:
                aklog_printf('获取chromedriver页面信息失败，重试')
                time.sleep(10)
            else:
                aklog_printf('获取chromedriver页面信息失败')
                return None

        # 从获取到的页面信息提取下载路径
        download_url = ''
        if isinstance(ret, list):
            # 新的下载路径有改变
            for x in ret:
                if 'https://registry.npmmirror.com/-/binary/chromedriver/{}'.format(big_version) in x['url']:
                    download_url = x['url']
        # else:
        #     # 从获取到的页面信息提取下载路径
        #     if '"https://registry.npmmirror.com/-/binary/chromedriver/'.format(int(big_version) + 1) in ret:
        #         ret1 = str_get_content_between_two_characters(
        #             ret,
        #             '<a href="/mirrors/chromedriver/{}'.format(big_version),
        #             '<a href="/mirrors/chromedriver/{}'.format(int(big_version) + 1))
        #     else:
        #         ret1 = str_get_content_between_two_characters(ret,
        #                                                       '<a href="/mirrors/chromedriver/{}'.format(big_version),
        #                                                       '</a>')
        #     ret2 = ret1.split('\n')[-1]
        #
        #     if '<a href="/mirrors/chromedriver/{}'.format(big_version) in ret2:
        #         download_url = str_get_content_between_two_characters(ret2, '"/', '/"')
        #     else:
        #         download_url = 'mirrors/chromedriver/{}'.format(big_version) + ret2.split('/"')[0]

        if not download_url.endswith('/'):
            download_url = download_url + '/'
        new_driver_version = download_url.split('/')[-2]
        aklog_printf('new_driver_version: %s' % new_driver_version)

        driver_download_dir = root_path + '\\testfile\\Browser\\ChromeDriver\\%s' % big_version
        if not os.path.exists(driver_download_dir):
            os.makedirs(driver_download_dir)
        # 下载驱动文件
        driver_path = driver_download_dir + '\\chromedriver.exe'
        if os.path.exists(driver_path):
            current_driver_version = get_current_driver_version(driver_path)
        else:
            current_driver_version = ''

        if not new_driver_version or new_driver_version != current_driver_version:
            aklog_printf('下载新版本driver')
            file = driver_download_dir + '\\chromedriver_win32.zip'
            ak_requests.download_file(file, download_url + 'chromedriver_win32.zip')
            time.sleep(5)

            # 解压驱动文件并删除下载的zip包
            with ZipFile(file, 'r') as zipObj:
                zipObj.extractall(driver_download_dir)
            time.sleep(1)
            os.remove(file)
        else:
            aklog_printf('当前驱动版本已是最新，无需再重新下载')
        return driver_path
    except:
        aklog_printf('下载浏览器驱动失败: ' + str(traceback.format_exc()))
        return None


def download_driver_from_chrome_testing(big_version):
    aklog_printf('download_driver')
    try:
        ret = None
        proxies = None
        proxy_url = config_get_value_from_ini_file('environment', 'proxy_url')
        if not proxy_url:
            proxy_url = 'socks5://192.168.11.2:7891'
        for i in range(3):
            try:
                resp = requests.get(
                    "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json",
                    timeout=10, proxies=proxies
                )
                ret = resp.json()
                if ret:
                    break
                elif i < 2:
                    aklog_debug("获取chromedriver页面信息失败，重试")
                    time.sleep(10)
                else:
                    aklog_debug("获取chromedriver页面信息失败")
                    return None
            except:
                if i == 0:
                    aklog_debug("获取chromedriver页面信息异常，添加代理重试")
                    proxies = {
                        "http": proxy_url,
                        "https": proxy_url,
                    }
                    time.sleep(1)
                    continue
                else:
                    raise

        # 从获取到的页面信息提取下载路径
        download_url = ''
        driver_list = []
        new_driver_version = ''
        if isinstance(ret, dict):
            # 新的下载路径有改变
            for x in ret['versions']:
                if x['version'].startswith(big_version):
                    driver_list = x['downloads'].get('chromedriver')
                    if not driver_list:
                        continue
                    new_driver_version = x['version']

        for driver in driver_list:
            if driver.get('platform') == 'win64':
                download_url = driver['url']
        aklog_printf('new_driver_version: %s' % new_driver_version)
        aklog_printf('new_driver_url: %s' % download_url)

        driver_download_dir = root_path + '\\testfile\\Browser\\ChromeDriver\\%s' % big_version
        if not os.path.exists(driver_download_dir):
            os.makedirs(driver_download_dir)
        # 下载驱动文件
        driver_path = driver_download_dir + '\\chromedriver-win64\\chromedriver.exe'
        if os.path.exists(driver_path):
            current_driver_version = get_current_driver_version(driver_path)
        else:
            current_driver_version = ''

        if not new_driver_version or new_driver_version != current_driver_version:
            aklog_printf('下载新版本driver')
            file = driver_download_dir + '\\chromedriver-win64.zip'
            proxies = None
            r = None
            for i in range(3):
                try:
                    r = requests.get(download_url, timeout=120, proxies=proxies)
                    if r:
                        break
                    elif i < 2:
                        aklog_debug("下载chromedriver失败，重试")
                        continue
                    else:
                        aklog_debug("下载chromedriver失败")
                        return None
                except:
                    if i == 0:
                        aklog_debug("下载chromedriver异常，添加代理重试")
                        proxies = {
                            "http": proxy_url,
                            "https": proxy_url,
                        }
                        time.sleep(1)
                        continue
                    else:
                        raise

            with open(file, "wb") as f:
                f.write(r.content)
            time.sleep(5)

            # 解压驱动文件并删除下载的zip包
            with ZipFile(file, 'r') as zipObj:
                zipObj.extractall(driver_download_dir)
            time.sleep(1)
            os.remove(file)
        else:
            aklog_printf('当前驱动版本已是最新，无需再重新下载')
        return driver_path
    except:
        aklog_printf('下载浏览器驱动失败: ' + str(traceback.format_exc()))
        return None


def download_driver_from_huawei():
    """
    不通过代理华为云下载.
    """
    aklog_debug()
    base_url = "https://mirrors.huaweicloud.com/chromedriver/"
    version_list_url = base_url
    driver_filename = "chromedriver-win32.zip"
    chrome_version = get_chrome_version()
    big_version = chrome_version.split('.')[0]
    chrome_major = chrome_version.split('.')[0]
    aklog_debug(f"本地Chrome版本: {chrome_version}")
    try:
        try:
            response = requests.get(version_list_url, timeout=15)
        except:
            aklog_error(f"访问: {version_list_url} 失败!!!")
            return
        version_pattern = re.compile(rf'<a href="({chrome_major}\.\d+\.\d+\.\d+)/"')
        driver_versions = version_pattern.findall(response.text)
        if not driver_versions:
            aklog_error(f"华为云镜像中未找到Chrome {chrome_major} 对应的ChromeDriver版本")
            return

        # 选择与本地Chrome版本完全匹配的版本（若有多个，优先完全匹配）
        target_driver_version = None
        for ver in driver_versions:
            if ver == chrome_version:
                target_driver_version = ver
                break
        if not target_driver_version:
            driver_versions.sort(key=lambda x: tuple(map(int, x.split('.'))))
            target_driver_version = driver_versions[-1]
            aklog_debug(f"未找到完全匹配版本，使用该主版本最新版: {target_driver_version}")
        driver_url = f"{base_url}{target_driver_version}/{driver_filename}"
        aklog_debug(f"匹配到ChromeDriver下载链接: {driver_url}")
    except Exception as e:
        return f"获取匹配的ChromeDriver版本失败: {str(e)}"

    new_driver_version = target_driver_version
    url = driver_url
    driver_download_dir = root_path + '\\testfile\\Browser\\ChromeDriver\\%s' % big_version
    if not os.path.exists(driver_download_dir):
        os.makedirs(driver_download_dir)

    # 下载驱动文件
    driver_path = driver_download_dir + '\\chromedriver-win32\\chromedriver.exe'
    if os.path.exists(driver_path):
        current_driver_version = get_current_driver_version(driver_path)
    else:
        current_driver_version = ''

    if not new_driver_version or new_driver_version != current_driver_version:
        aklog_printf('下载新版本driver')
        file = driver_download_dir + '\\chromedriver_win32.zip'
        try:
            # 1. 解析文件名和保存路径
            filename = os.path.basename(url)
            aklog_debug(f"正在下载: {filename}")

            try:
                response = requests.get(url, stream=True, timeout=30)
            except:
                aklog_error(f'下载: {url} 失败!')
                return
            with open(file, 'wb') as f:
                f.write(response.content)

            with ZipFile(file, 'r') as zipObj:
                zipObj.extractall(driver_download_dir)
            time.sleep(1)
            shutil.copy(os.path.join(driver_download_dir, 'chromedriver-win32', 'chromedriver.exe'),
                        os.path.join(driver_download_dir, 'chromedriver.exe'))
            shutil.rmtree(os.path.join(driver_download_dir, 'chromedriver-win32'))
            try:
                os.remove(file)
            except:
                pass
            driver_name = "chromedriver.exe"
            driver_path = os.path.join(driver_download_dir, driver_name)
            if os.path.exists(driver_path):
                aklog_debug(f"ChromeDriver最终路径: {driver_path}")
                return driver_path
            else:
                aklog_error(f"解压后未找到驱动文件: {driver_name}")
                return ''
        except Exception as e:
            aklog_debug(traceback.format_exc())
            return


def chrome_driver_auto_update():
    aklog_printf('chrome_driver_auto_update')
    download_driver_path = ''
    try:
        download_driver_path = download_driver_from_huawei()
    except:
        pass
    if download_driver_path:
        download_state = True

    if download_state:
        File_process.copy_file(download_driver_path, root_path + '\\testcase\\apps\\chromedriver.exe')
    else:
        chrome_big_version = get_chrome_version().split('.')[0]
        aklog_printf('chrome_big_version: %s' % chrome_big_version)
        if int(chrome_big_version) > 114:
            driver_path = download_driver_from_chrome_testing(chrome_big_version)
        else:
            driver_path = download_driver(chrome_big_version)
        if driver_path:
            File_process.copy_file(driver_path, root_path + '\\testcase\\apps\\chromedriver.exe')
        else:
            aklog_printf('driver更新失败')


if __name__ == '__main__':
    chrome_driver_auto_update()
