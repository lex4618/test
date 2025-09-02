# -*- coding: utf-8 -*-

import sys
import os

# 获取根目录
root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
if root_path not in sys.path:
    sys.path.append(root_path)

import time
import logging
import logging.handlers
import json
import html
import inspect
import importlib
import colorama
from types import ModuleType
from typing import List

__all__ = [
    'start_global_log',
    'close_global_log',
    'aklog_get_current_time',
    'aklog_get_cur_co_name',
    'aklog_init_common',
    'aklog_init',
    'aklog_console_init',
    'aklog_console_remove',
    'aklog_html_init',
    'aklog_html_remove',
    'akresult_init',
    'aklog_get_result_dir',
    'aklog_get_result_capture_file',
    'aklog_get_result_record_file',
    'aklog_get_report_file',
    'aklog_get_report_url',
    'aklog_write',
    'aklog_printf',
    'aklog_debug',
    'aklog_info',
    'aklog_warn',
    'aklog_error',
    'aklog_error_tag',
    'aklog_fatal',
    'akresult_printf',
    'aklog_remove',
    'sleep',
    'time_sleep',
    'generate_all_for_module'
]

colorama.init(autoreset=True)

# ANSI 控制台颜色映射
CONSOLE_COLORS = {
    # "INFO": colorama.Fore.GREEN,
    # "WARNING": colorama.Fore.YELLOW,
    # "ERROR": colorama.Fore.RED,
    # "CRITICAL": colorama.Fore.MAGENTA,
    "INFO": colorama.Back.GREEN + colorama.Fore.BLACK,
    "WARNING": colorama.Back.YELLOW + colorama.Fore.BLACK,
    "ERROR": colorama.Back.RED,
    "CRITICAL": colorama.Back.MAGENTA,
}

# HTML 颜色映射
HTML_COLORS = {
    "INFO": "log-info",
    "WARNING": "log-warning",
    "ERROR": "log-error",
    "CRITICAL": "log-critical",
}

# LOG等级简短缩写
LEVEL_NAME_MAP = {
    'DEBUG': 'DEBUG',
    'INFO': 'INFO',
    'WARNING': 'WARN',
    'ERROR': 'ERROR',
    'CRITICAL': 'FATAL',
}


class ShortLevelFormatter(logging.Formatter):
    """控制台格式化器"""

    def format(self, record):
        # 替换levelname为短名称并左对齐5位
        short_name = LEVEL_NAME_MAP.get(record.levelname, record.levelname)
        record.levelname = short_name.ljust(5, '-')
        return super().format(record)


class ColorConsoleFormatter(logging.Formatter):
    """控制台日志颜色格式化器"""

    def format(self, record):
        level_color = CONSOLE_COLORS.get(record.levelname, "")
        # 替换levelname为短名称并左对齐5位
        short_name = LEVEL_NAME_MAP.get(record.levelname, record.levelname)
        record.levelname = short_name.ljust(5, '-')
        message = super().format(record)
        if level_color:
            return f"{level_color}{message}{colorama.Style.RESET_ALL}"
        else:
            return message


class HTMLColorFormatter(logging.Formatter):
    """HTML 报告日志颜色格式化器"""

    def format(self, record):
        level_color = HTML_COLORS.get(record.levelname, "")
        # 替换levelname为短名称并左对齐5位
        short_name = LEVEL_NAME_MAP.get(record.levelname, record.levelname)
        record.levelname = short_name.ljust(5, '-')
        message = html.escape(super().format(record))
        if level_color:
            return f'<span class="{level_color}">{message}</span>'
        else:
            return message


# 创建logger
g_html_logger = logging.getLogger('HtmlLogger')
g_file_logger = logging.getLogger('FileLogger')
g_console_logger = logging.getLogger('ConsoleLogger')
g_result_logger = logging.getLogger('Result')
g_result_logger.propagate = False
g_console_logger.propagate = False
g_file_logger.propagate = False
g_html_logger.propagate = False  # 设置这个记录器的事件不会传递给高级别管理器去记录，否则有些异常情况下会导致log重复记录

# 创建handler
g_handler_file = logging.NullHandler()
g_common_handler_file = logging.NullHandler()
g_handler_html = logging.NullHandler()
g_result_handler_file = logging.NullHandler()
g_handler_console = logging.StreamHandler(stream=sys.stdout)

# 初始化控制台logger
g_console_logger.setLevel(logging.DEBUG)
console_formatter = ColorConsoleFormatter('%(asctime)s-%(levelname)s-%(message)s')
g_handler_console.setFormatter(console_formatter)
if g_handler_console not in g_console_logger.handlers:
    g_console_logger.addHandler(g_handler_console)

g_result_dir = ''
global_log_state = True


def __clear_duplicate_handlers(*loggers):
    for logger in loggers:
        handler_names = set()
        unique_handlers = []
        for handler in logger.handlers:
            handler_name = str(handler)
            if handler_name not in handler_names:
                handler_names.add(handler_name)
                unique_handlers.append(handler)
        logger.handlers = unique_handlers


# 清理重复处理器
__clear_duplicate_handlers(g_console_logger, g_html_logger, g_file_logger, g_result_logger)


def close_global_log(print_warning=True):
    if print_warning:
        aklog_warn('关闭log功能..')
    global global_log_state
    global_log_state = False


def start_global_log(print_warning=True):
    global global_log_state
    global_log_state = True
    if print_warning:
        aklog_warn('log功能恢复..')


def aklog_get_current_time():
    """[summary] 获取当前时间
    [description] 用time.localtime()+time.strftime()实现
    :returns: [description] 返回str类型
    """
    ct = time.time()
    local_time = time.localtime(ct)
    date_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    date_secs = (ct - int(ct)) * 1000
    time_stamp = "%s.%03d" % (date_head, date_secs)
    return time_stamp


def __aklog_create_result_dir(app_name):
    current_time = time.strftime("%H%M%S")  # 获取当前时间（时分秒）
    process_id = os.getpid()  # 获取当前进程 ID
    folder_name = f"{current_time}_{process_id}"  # 创建文件夹名称（时间_进程ID）
    result_path = os.path.join(root_path, 'outputs', 'Results', app_name,
                               str(time.strftime("%Y")), str(time.strftime("%m")), str(time.strftime("%d")),
                               folder_name)
    os.makedirs(result_path, exist_ok=True)
    aklog_info('result_dir: %s' % result_path)
    return result_path


def aklog_get_cur_co_name():
    """获取当前函数的名称"""
    return inspect.currentframe().f_back.f_code.co_name


def aklog_init_common(log_level=5):
    aklog_info()
    # 先移除handler_file，再重新添加
    global g_file_logger, g_handler_file, g_common_handler_file
    g_file_logger.removeHandler(g_handler_file)

    # 设置Log等级，控制台和输出到文件的等级默认一致
    if log_level == 5:
        logger_level = logging.DEBUG
    elif log_level == 4:
        logger_level = logging.INFO
    elif log_level == 3:
        logger_level = logging.WARNING
    elif log_level == 2:
        logger_level = logging.ERROR
    elif log_level == 1:
        logger_level = logging.CRITICAL
    else:
        logger_level = logging.DEBUG
    g_file_logger.setLevel(logger_level)

    # 如果已经保存log到文件了，那么就不需要再重新创建log目录保存
    if g_common_handler_file not in g_file_logger.handlers:
        log_path = os.path.join(root_path, 'outputs', 'Log',
                                str(time.strftime("%Y")), str(time.strftime("%m")), str(time.strftime("%d")),
                                str(time.strftime('%H%M%S')))
        if not os.path.exists(log_path):
            try:
                os.makedirs(log_path)
            except FileExistsError:
                pass
        log_file = log_path + '/Log.log'

        g_common_handler_file = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=100, encoding='utf-8')
        file_formatter = ShortLevelFormatter('%(asctime)s-%(levelname)s-%(message)s')
        g_common_handler_file.setFormatter(file_formatter)  # 为handler添加formatter

        # 为logger添加handler
        g_file_logger.addHandler(g_common_handler_file)


def aklog_init(app_name, log_level=5):
    """
    初始化Log，设置机型文件夹、Log等级，以及定义logger相关，level为1-5个等级，数字越大，等级越高，默认为5
    """
    aklog_info()
    # 先移除handler_file，再重新添加
    global g_handler_file, g_result_dir
    g_file_logger.removeHandler(g_common_handler_file)

    # 设置Log等级，控制台和输出到文件的等级默认一致
    if log_level == 5:
        logger_level = logging.DEBUG
    elif log_level == 4:
        logger_level = logging.INFO
    elif log_level == 3:
        logger_level = logging.WARNING
    elif log_level == 2:
        logger_level = logging.ERROR
    elif log_level == 1:
        logger_level = logging.CRITICAL
    else:
        logger_level = logging.DEBUG

    g_file_logger.setLevel(logger_level)
    g_html_logger.setLevel(logger_level)

    # 如果已经保存log到文件了，那么就不需要再重新创建log目录保存
    if g_handler_file not in g_file_logger.handlers:
        # create log file handler
        g_result_dir = __aklog_create_result_dir(app_name)
        log_file = g_result_dir + '/Log.log'
        # 实例化handler
        g_handler_file = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=100, encoding='utf-8')
        file_formatter = ShortLevelFormatter('%(asctime)s-%(levelname)s-%(message)s')
        g_handler_file.setFormatter(file_formatter)  # 为handler添加formatter

        # 为logger添加handler
        g_file_logger.addHandler(g_handler_file)


def aklog_console_init():
    """控制台输出初始化，可以将log输出到控制台显示，
    可以用于使用HTML方式执行自动化时，由于log被缓冲区捕获，无法在控制台实时显示情况下显示log"""
    if g_handler_console not in g_console_logger.handlers:
        g_console_logger.addHandler(g_handler_console)


def aklog_console_remove():
    """配合aklog_console_init使用，退出控制台显示log"""
    for handler in g_console_logger.handlers:
        g_console_logger.removeHandler(handler)


def aklog_html_init(outputBuffer):
    global g_handler_html
    if g_handler_html not in g_html_logger.handlers:
        g_handler_html = logging.StreamHandler(outputBuffer)
        html_formatter = HTMLColorFormatter('%(asctime)s-%(levelname)s-%(message)s')
        g_handler_html.setFormatter(html_formatter)  # 为handler添加formatter
        g_html_logger.addHandler(g_handler_html)


def aklog_html_remove():
    """配合aklog_console_init使用，退出控制台显示log"""
    for handler in g_html_logger.handlers:
        g_html_logger.removeHandler(handler)


def akresult_init():
    """创建result file handler，将每条用例的测试结果保存到Result.txt"""
    global g_result_handler_file
    g_result_logger.setLevel(logging.DEBUG)

    result_file = g_result_dir + '/Result.txt'
    g_result_handler_file = logging.handlers.RotatingFileHandler(result_file, maxBytes=1024 * 1024,
                                                                 backupCount=100)  # 实例化handler
    result_fmt_file = '%(asctime)s - %(message)s'
    result_formatter_file = logging.Formatter(result_fmt_file)  # 实例化formatter
    g_result_handler_file.setFormatter(result_formatter_file)  # 为handler添加formatter
    g_result_logger.addHandler(g_result_handler_file)


def aklog_get_result_dir():
    global g_result_dir
    if not g_result_dir:
        g_result_dir = __aklog_create_result_dir('COMMON')
    return g_result_dir


def aklog_get_result_capture_file(device_name=None):
    capture_time = time.strftime('%Y%m%d-%H%M%S', time.localtime(time.time()))
    if device_name:
        capture_dir = '{}\\{}\\{}'.format(aklog_get_result_dir(), 'Capture', device_name)
    else:
        capture_dir = '{}\\{}'.format(aklog_get_result_dir(), 'Capture')
    os.makedirs(capture_dir, exist_ok=True)
    capture_file = '{}\\capture-{}.jpg'.format(capture_dir, capture_time)
    return capture_file


def aklog_get_result_record_file(device_name=None):
    record_time = time.strftime('%Y%m%d-%H%M%S', time.localtime(time.time()))
    if device_name:
        record_dir = '{}\\{}\\{}'.format(aklog_get_result_dir(), 'Record', device_name)
    else:
        record_dir = '{}\\{}'.format(aklog_get_result_dir(), 'Record')
    os.makedirs(record_dir, exist_ok=True)
    record_file = '{}\\record-{}.mp4'.format(record_dir, record_time)
    return record_file


def aklog_get_report_file():
    global g_result_dir
    report_file = g_result_dir + '\\Report.html'
    return report_file


def aklog_get_report_url(root_path_url):
    global g_result_dir
    report_file = g_result_dir + '\\Report.html'
    if root_path_url.startswith('file:///'):
        report_file_url = root_path_url + report_file
    else:
        if root_path_url.endswith('/'):
            root_path_url = root_path_url[0:-1]
        report_file_url = report_file.replace(root_path, root_path_url)
    report_file_url = report_file_url.replace('\\', '/')
    return report_file_url


def __aklog_write(log=None, log_level=5, back_depth=2):
    if not global_log_state:
        # g_html_logger.debug('关闭了log功能！')
        return
    device_name = ''
    if back_depth == 3:
        f_back_frame = inspect.currentframe().f_back.f_back.f_back
    else:
        f_back_frame = inspect.currentframe().f_back.f_back
    if log is None:
        try:
            co_name = f_back_frame.f_code.co_name
            param_dict = f_back_frame.f_locals
            if 'self' in param_dict:
                try:
                    device_name = param_dict['self'].device_name
                except:
                    pass
                del param_dict['self']
            if param_dict:
                log = '{}, with params: {}'.format(co_name, str(param_dict))
            else:
                log = co_name
            if device_name:
                device_name_log = '[{}]'.format(device_name)
                if device_name_log not in log:
                    log = '{} {}'.format(device_name_log, log)
        except:
            pass
        log_with_func = '[{}-{}] {}'.format(os.path.basename(f_back_frame.f_code.co_filename),
                                            f_back_frame.f_lineno,
                                            log)
    else:
        param_dict = f_back_frame.f_locals
        if 'self' in param_dict:
            try:
                device_name = param_dict['self'].device_name
            except:
                pass
            if device_name:
                device_name_log = '[{}]'.format(device_name)
                if device_name_log not in str(log):
                    log = '{} {}'.format(device_name_log, log)

        log_with_func = '[{}-{}-{}] {}'.format(os.path.basename(f_back_frame.f_code.co_filename),
                                               f_back_frame.f_code.co_name,
                                               f_back_frame.f_lineno,
                                               log)

    if log_level == 5:
        if len(g_html_logger.handlers) > 0 and g_handler_html in g_html_logger.handlers:
            g_html_logger.debug(log_with_func)
        if len(g_console_logger.handlers) > 0 and g_handler_console in g_console_logger.handlers:
            g_console_logger.debug(log_with_func)
        if (len(g_file_logger.handlers) > 0 and
                g_handler_file in g_file_logger.handlers):
            g_file_logger.debug(log_with_func)
    elif log_level == 4:
        if len(g_html_logger.handlers) > 0 and g_handler_html in g_html_logger.handlers:
            g_html_logger.info(log_with_func)
        if len(g_console_logger.handlers) > 0 and g_handler_console in g_console_logger.handlers:
            g_console_logger.info(log_with_func)
        if (len(g_file_logger.handlers) > 0 and
                g_handler_file in g_file_logger.handlers):
            g_file_logger.info(log_with_func)
    elif log_level == 3:
        if len(g_html_logger.handlers) > 0 and g_handler_html in g_html_logger.handlers:
            g_html_logger.warning(log_with_func)
        if len(g_console_logger.handlers) > 0 and g_handler_console in g_console_logger.handlers:
            g_console_logger.warning(log_with_func)
        if (len(g_file_logger.handlers) > 0 and
                g_handler_file in g_file_logger.handlers):
            g_file_logger.warning(log_with_func)
    elif log_level == 2:
        if len(g_html_logger.handlers) > 0 and g_handler_html in g_html_logger.handlers:
            g_html_logger.error(log_with_func)
        if len(g_console_logger.handlers) > 0 and g_handler_console in g_console_logger.handlers:
            g_console_logger.error(log_with_func)
        if (len(g_file_logger.handlers) > 0 and
                g_handler_file in g_file_logger.handlers):
            g_file_logger.error(log_with_func)
    elif log_level == 1:
        if len(g_html_logger.handlers) > 0 and g_handler_html in g_html_logger.handlers:
            g_html_logger.critical(log_with_func)
        if len(g_console_logger.handlers) > 0 and g_handler_console in g_console_logger.handlers:
            g_console_logger.critical(log_with_func)
        if (len(g_file_logger.handlers) > 0 and
                g_handler_file in g_file_logger.handlers):
            g_file_logger.critical(log_with_func)


def aklog_write(log=None, log_level=5):
    """给cloud_CBB使用"""
    if log_level == 5:
        if len(g_html_logger.handlers) > 0 and g_handler_html in g_html_logger.handlers:
            g_html_logger.debug(log)
        if len(g_console_logger.handlers) > 0 and g_handler_console in g_console_logger.handlers:
            g_console_logger.debug(log)
        if (len(g_file_logger.handlers) > 0 and
                g_handler_file in g_file_logger.handlers):
            g_file_logger.debug(log)
    elif log_level == 4:
        if len(g_html_logger.handlers) > 0 and g_handler_html in g_html_logger.handlers:
            g_html_logger.info(log)
        if len(g_console_logger.handlers) > 0 and g_handler_console in g_console_logger.handlers:
            g_console_logger.info(log)
        if (len(g_file_logger.handlers) > 0 and
                g_handler_file in g_file_logger.handlers):
            g_file_logger.info(log)
    elif log_level == 3:
        if len(g_html_logger.handlers) > 0 and g_handler_html in g_html_logger.handlers:
            g_html_logger.warning(log)
        if len(g_console_logger.handlers) > 0 and g_handler_console in g_console_logger.handlers:
            g_console_logger.warning(log)
        if (len(g_file_logger.handlers) > 0 and
                g_handler_file in g_file_logger.handlers):
            g_file_logger.warning(log)
    elif log_level == 2:
        if len(g_html_logger.handlers) > 0 and g_handler_html in g_html_logger.handlers:
            g_html_logger.error(log)
        if len(g_console_logger.handlers) > 0 and g_handler_console in g_console_logger.handlers:
            g_console_logger.error(log)
        if (len(g_file_logger.handlers) > 0 and
                g_handler_file in g_file_logger.handlers):
            g_file_logger.error(log)
    elif log_level == 1:
        if len(g_html_logger.handlers) > 0 and g_handler_html in g_html_logger.handlers:
            g_html_logger.critical(log)
        if len(g_console_logger.handlers) > 0 and g_handler_console in g_console_logger.handlers:
            g_console_logger.critical(log)
        if (len(g_file_logger.handlers) > 0 and
                g_handler_file in g_file_logger.handlers):
            g_file_logger.critical(log)


def aklog_printf(log=None, log_level=5, json_format=False, back_depth=2):
    """
    可以设置打印log的等级，该等级会受到'aklog_init'中的'logger.setLevel'的控制，
    打印log时会先打印时间、Log等级、调用此函数的模块文件名、函数名称、行号
    不填level参数的话，默认log等级为5
    log如果为None，一般用于打印接口方法信息
    json_format: 打印dict或list类型，是否转成json格式美化输出
    """
    if json_format:
        try:
            log = json.dumps(log, ensure_ascii=False, indent=4)
            log = '\n' + log
        except:
            pass

    __aklog_write(log, log_level, back_depth)


def aklog_debug(log=None, back_depth=2):
    """基础通用库的log一般用这个等级"""
    __aklog_write(log, 5, back_depth)


def aklog_info(log=None, back_depth=2):
    """打印接口log"""
    __aklog_write(log, 4, back_depth)


def aklog_warn(log=None):
    """打印一些警告的log"""
    __aklog_write(log, 3)


def aklog_error(log=None):
    """打印错误、失败的log"""
    __aklog_write(log, 2)


def aklog_fatal(log=None):
    """打印严重错误的log，比如设备连接失败、网页访问失败、登录失败等会影响之后用例执行的"""
    __aklog_write(log, 1)


def akresult_printf(result):
    """
    保存结果到单独的文件
    """
    g_result_logger.debug(str(result))


def aklog_remove():
    """关闭保存log到文件"""
    global g_handler_file, g_common_handler_file
    g_file_logger.removeHandler(g_handler_file)  # log不在保存到机型测试Results目录下文件
    g_handler_file = logging.NullHandler()

    g_file_logger.addHandler(g_common_handler_file)  # log改为保存到通用log目录下文件

    global g_result_handler_file
    g_result_logger.removeHandler(g_result_handler_file)
    g_result_handler_file = logging.NullHandler()


def aklog_error_tag(log=None):
    """
    对讲终端过滤严重错误日志
    用在一些严重错误, 执行异常, 提示非自动化人员, 已知问题定位上.
    """
    from aklibparams import param_get_product_line_name
    if param_get_product_line_name() == 'INTERCOM':
        tag = ' -[对讲_特殊log]- '
        if not log:
            log = tag
        elif log and tag not in log:
            log = tag + log
        __aklog_write(log, 2)


def sleep(sleeptime, tips=None):
    if tips:
        aklog_info('sleep 等待 : {} 秒,  提示信息: {}'.format(sleeptime, tips), back_depth=3)
    else:
        aklog_debug('sleep 等待 : {} 秒'.format(sleeptime), back_depth=3)
    time.sleep(sleeptime)


def time_sleep(sleep_time, tips=None):
    if tips:
        aklog_printf(f'sleep 等待 : {sleep_time} 秒,  提示信息: {tips}', log_level=4, back_depth=3)
    else:
        aklog_printf(f'sleep 等待 : {sleep_time} 秒', back_depth=3)
    time.sleep(sleep_time)


def generate_all_for_module(module_name: str) -> List[str]:
    """
    扫描模块中公共类与函数（仅模块内定义），生成__all__列表（保持源码顺序，不含类方法）
    可以在要生成__all__的模块里使用：
    module_name = inspect.getmodulename(__file__)
    generate_all_for_module(module_name)
    Args:
        module_name (str): 模块名，例如 'mypkg.mymodule'

    Returns:
        list[str]: 模块中本地定义的公共类名和函数名，按源码顺序
    """

    def format_all_list(public_items: List[str]) -> str:
        """将 __all__ 列表格式化为多行字符串"""
        formatted = "__all__ = [\n"
        for name in public_items:
            formatted += f"    '{name}',\n"
        formatted += "]\n"
        return formatted

    # 动态导入模块
    module: ModuleType = importlib.import_module(module_name)
    print(f"已加载模块: {module_name}")

    # 获取源码文本并解析顺序（仅取顶层定义）
    source_lines = inspect.getsource(module).splitlines()
    defined_order = []
    for line in source_lines:
        stripped_line = line.lstrip()
        indent_level = len(line) - len(stripped_line)  # 缩进长度
        if indent_level == 0 and (stripped_line.startswith("def ") or stripped_line.startswith("class ")):
            name = stripped_line.split()[1].split("(")[0].split(":")[0]
            defined_order.append(name)

    # 用 inspect 验证并过滤
    member_map = dict(inspect.getmembers(module))
    public_items = []
    for name in defined_order:
        if name.startswith("_"):
            continue
        obj = member_map.get(name)
        if not obj:
            continue
        if (inspect.isfunction(obj) or inspect.isclass(obj)) and getattr(obj, "__module__", None) == module_name:
            public_items.append(name)

    print("公共API列表:\n" + format_all_list(public_items))
    return public_items
