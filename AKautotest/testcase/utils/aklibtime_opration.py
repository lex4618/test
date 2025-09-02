# -*- coding: utf-8 -*-

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
import time
import datetime as dt
import calendar
import locale
import traceback
import re

g_wait_time_begin = 0
now_time = 0


def sec2time(sec, n_msec=3):
    """ Convert seconds to 'D days, HH:MM:SS.FFF' """
    if hasattr(sec, '__len__'):  # 如果sec是个list，多个时间，则转化list里面的每个时间
        return [sec2time(s) for s in sec]
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if n_msec > 0:
        pattern = '%%02d:%%02d:%%0%d.%df' % (n_msec + 3, n_msec)

    else:
        pattern = '%02d:%02d:%02d'
    time_format = ''
    if d > 0:
        time_format += '%d Days, ' % d
    time_format += pattern % (h, m, s)
    return time_format


def sec2minute(sec, n_msec=1):
    """将秒数转换成分钟数，并保留几位小数"""
    if hasattr(sec, '__len__'):  # 如果sec是个list，多个时间，则转化list里面的每个时间
        return [sec2time(s) for s in sec]
    m = round(sec / 60, n_msec)
    return m


def time_2_sec_num(time_str):
    """将时间转成秒数，时间格式：01:11:22"""
    if time_str.count(':') == 1:
        # 只有小时和分钟
        hour = time_str.split(':')[0]
        minute = time_str.split(':')[1]
        sec_num = int(hour) * 3600 + int(minute) * 60
    elif time_str.count(':') == 2:
        hour = time_str.split(':')[0]
        minute = time_str.split(':')[1]
        sec = time_str.split(':')[2]
        sec_num = int(hour) * 3600 + int(minute) * 60 + int(sec)
    else:
        sec_num = 0
    aklog_printf('%s 的秒数为: %s' % (time_str, sec_num))
    return sec_num


def duration_to_seconds(duration):
    """将时长转换成秒数, duration: 5d10h5m30s"""
    # 定义正则表达式以匹配 d, h, m, s 的值
    pattern = re.compile(r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')
    match = pattern.fullmatch(duration.strip())

    if not match:
        raise ValueError(f"Invalid duration format: {duration}")

    days = int(match.group(1)) if match.group(1) else 0
    hours = int(match.group(2)) if match.group(2) else 0
    minutes = int(match.group(3)) if match.group(3) else 0
    seconds = int(match.group(4)) if match.group(4) else 0

    # 计算总秒数
    total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
    return total_seconds


def seconds_to_duration(seconds):
    """将秒数转成时长： 5d10h5m30s"""
    seconds = int(seconds)
    if seconds < 0:
        raise ValueError("Seconds cannot be negative")

    days = int(seconds // 86400)
    seconds %= 86400
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60

    duration_parts = []
    if days > 0:
        duration_parts.append(f"{days}d")
    if hours > 0:
        duration_parts.append(f"{hours}h")
    if minutes > 0:
        duration_parts.append(f"{minutes}m")
    if seconds > 0 or not duration_parts:
        duration_parts.append(f"{seconds}s")

    return ''.join(duration_parts)


def reformat_datetime(date_time, dst_fmt):
    """
    重新格式化时间戳
    :param date_time: 2020-09-05 09:0
    :param dst_fmt: %Y-%#m-%#d %#H:%#M
    :return:
    """
    aklog_printf()
    src_time = date_time
    try:
        date_time = date_time.strip().replace('/', '-')
        counts = date_time.count(':')  # 获取冒号字符串次数，来判断时间精确到时分秒
        if counts == 2:
            time_stamp = time.mktime(time.strptime(date_time, "%Y-%m-%d %H:%M:%S"))
        elif counts == 1:
            time_stamp = time.mktime(time.strptime(date_time, "%Y-%m-%d %H:%M"))
        else:
            time_stamp = time.mktime(time.strptime(date_time, "%Y-%m-%d %H"))

        new_date_time = time.strftime(dst_fmt, time.localtime(time_stamp))
        return new_date_time
    except:
        aklog_printf(traceback.format_exc())
        return src_time


def trans_time_fmt_to_24(time_str, dst_fmt=None):
    """
    12小时制转换成24小时制
    :param time_str: 格式为：%I:%M:%S%p，比如06:30:15PM, 06:30:15AM
    :param dst_fmt: 目标格式： %H:%M:%S or %#H:%M 小时位去掉前置补零
    :return: 时间格式为%H:%M:%S or %H:%M，不包含日期
    """
    aklog_printf('trans_time_fmt_to_24: %s' % time_str)
    src_time = time_str
    try:
        time_locale = locale.setlocale(locale.LC_TIME)
        # print(time_locale)
        locale.setlocale(locale.LC_TIME, 'en')
        if '-' in time_str or '/' in time_str:
            # 如果时间包含了日期，需要先把日期部分截掉
            if ' ' in time_str.split(':')[0]:
                date_str = time_str.split(':')[0].split(' ')[0]
            else:
                date_str = time_str.split(':')[0][0:-2]
            time_str = time_str.replace(date_str, '').strip()
        if 'PM' in time_str or 'AM' in time_str:
            time_str = time_str.replace(' ', '').strip()
            if time_str.count(':') == 2:
                trans_time = time.strptime(time_str, '%I:%M:%S%p')
                trans_time_str = time.strftime('%H:%M:%S', trans_time)
            else:
                trans_time = time.strptime(time_str, '%I:%M%p')
                trans_time_str = time.strftime('%H:%M', trans_time)
        else:
            trans_time_str = time_str

        # 默认输出格式为%H:%M:%S or %H:%M，如果有指定目标格式，则要再进行一次转换
        if dst_fmt:
            if trans_time_str.count(':') == 2:
                trans_time = time.strptime(trans_time_str, '%H:%M:%S')
                trans_time_str = time.strftime(dst_fmt, trans_time)
            else:
                trans_time = time.strptime(trans_time_str, '%H:%M')
                trans_time_str = time.strftime(dst_fmt, trans_time)

        locale.setlocale(locale.LC_TIME, time_locale)
        aklog_printf('24-hour time: %s' % trans_time_str)
        return trans_time_str
    except:
        aklog_printf(traceback.format_exc())
        return src_time


def trans_time_fmt_to_12(time_str, dst_fmt=None):
    """
    将时间转换成12小时制
    :param time_str: 格式为：%H:%M:%S or %H:%M，比如06:30:15, 06:30
    :param dst_fmt: 目标格式： %#I:%M:%S%p or %#I:%M%p 小时位去掉前置补零
    :return: 时间格式为%I:%M:%S%p or %I:%M%p，不包含日期
    """
    aklog_printf('trans_time_fmt_to_12: %s' % time_str)
    src_time = time_str
    try:
        time_locale = locale.setlocale(locale.LC_TIME)
        locale.setlocale(locale.LC_TIME, 'en')
        if '-' in time_str or '/' in time_str:
            # 如果时间包含了日期，需要先把日期部分截掉
            if ' ' in time_str.split(':')[0]:
                date_str = time_str.split(':')[0].split(' ')[0]
            else:
                date_str = time_str.split(':')[0][0:-2]
            time_str = time_str.replace(date_str, '').strip()
        if 'PM' not in time_str and 'AM' not in time_str:
            if time_str.count(':') == 2:
                trans_time = time.strptime(time_str, '%H:%M:%S')
                trans_time_str = time.strftime('%I:%M:%S%p', trans_time)
            else:
                trans_time = time.strptime(time_str, '%H:%M')
                trans_time_str = time.strftime('%I:%M%p', trans_time)
        else:
            time_str = time_str.replace(' ', '')
            if time_str.count(':') == 2:
                trans_time = time.strptime(time_str, '%I:%M:%S%p')
                trans_time_str = time.strftime('%I:%M:%S%p', trans_time)
            else:
                trans_time = time.strptime(time_str, '%I:%M%p')
                trans_time_str = time.strftime('%I:%M%p', trans_time)

        # 默认输出格式为%I:%M:%S%p or %I:%M%p，如果有指定目标格式，则要再进行一次转换
        if dst_fmt:
            if trans_time_str.count(':') == 2:
                trans_time = time.strptime(trans_time_str, '%I:%M:%S%p')
                trans_time_str = time.strftime(dst_fmt, trans_time)
            else:
                trans_time = time.strptime(trans_time_str, '%I:%M%p')
                trans_time_str = time.strftime(dst_fmt, trans_time)

        locale.setlocale(locale.LC_TIME, time_locale)
        aklog_printf('12-hour time: %s' % trans_time_str)
        return trans_time_str
    except:
        aklog_printf(traceback.format_exc())
        return src_time


def trans_time_format(time_str, time_fmt=None, is_need_blank=None):
    """
    转换12或24进制时间字符串格式，默认去掉小时位的0
    :param time_str: 格式为：%H(%I):%M:(%S)(%p)可前置小时位去0，比如06:30:15, 06:30, 5:20:18PM, 9:30AM
    :param time_fmt: None，接受 int 或 String 类型的 12 或 24，默认转换为 24 小时制
    :param is_need_blank: None，接受布尔值，为真时在 12 小时制 AM/PM 前面加空格
    :return: 时间格式为 %#H(%#I):%M:(%S)(%p)
    """
    if '\n' in time_str:
        time_str = time_str[:-1]
    if str(time_fmt) == '12':
        time_str_res = trans_time_fmt_to_12(time_str)
        if is_need_blank:
            time_str_res = list(time_str_res)
            time_str_res.insert(-2, " ")
            time_str_res = ''.join(time_str_res)
        aklog_debug("12-hour time: %s" % time_str_res)
    else:
        time_str_res = trans_time_fmt_to_24(time_str)
        aklog_debug("24-hour time: %s" % time_str_res)
    return time_str_res


def get_time_fmt(time_str):
    """获取时间格式"""
    time_fmt = ['%H:%M:%S', '%H:%M', '%I:%M:%S%p', '%I:%M%p', '%I:%M %p', "%I:%M:%s %p"]
    for x in time_fmt:
        try:
            time.strptime(time_str.strip(), x)
            time_fmt = x
            return time_fmt
        except:
            pass
    return None


def trans_date_fmt(src_date, src_fmt, dst_fmt='%Y-%m-%d'):
    """
    将日期转成对应格式
    :param src_date: 01-18-2021,
    :param src_fmt: %m-%d-%Y, 或者Y-M-D 或 YYYY-MM-DD
    :param dst_fmt: '%Y-%m-%d'
    :return:
    """
    aklog_printf()
    try:
        if src_fmt == 'Y-M-D' or src_fmt == 'YYYY-MM-DD':
            src_fmt = '%Y-%m-%d'
        elif src_fmt == 'M-D-Y' or src_fmt == 'MM-DD-YYYY':
            src_fmt = '%m-%d-%Y'
        elif src_fmt == 'D-M-Y' or src_fmt == 'DD-MM-YYYY':
            src_fmt = '%d-%m-%Y'
        dst_date = dt.datetime.strptime(src_date, src_fmt).strftime(dst_fmt)
        return dst_date
    except:
        aklog_printf(traceback.format_exc())
        return src_date


def trans_date_time_fmt(date_time, src_fmt, dst_fmt):
    """
    将日期时间转成对应格式
    :param date_time: 2021-11-25 15:30:20， str类型
    :param src_fmt: %Y-%m-%d %H:%M:%S, %d-%m-%Y %I:%M:%S %p
    :param dst_fmt: %d-%m-%Y %H:%M:%S
    :return:
    """
    aklog_printf('trans_date_time_fmt: %s' % date_time)
    try:
        src_date_time = dt.datetime.strptime(date_time, src_fmt)
        dst_date_time = src_date_time.strftime(dst_fmt)
        aklog_printf(dst_date_time)
    except:
        aklog_printf(traceback.format_exc())
        dst_date_time = date_time
    return dst_date_time


def get_current_date_format(date):
    """
    获取当前日期格式，返回Y-M-D，M-D-Y，D-M-Y
    :param date: 也是当前日期，2020/01/18， 01-18-2020，str类型
    :return:
    """
    date = date.replace('/', '-')
    date_list = date.split('-')
    current_date = time.strftime("%Y-%m-%d", time.localtime())
    current_date_list = current_date.split('-')
    year = current_date_list[0]
    month = current_date_list[1]
    day = current_date_list[2]
    for i in range(len(date_list)):
        if date_list[i] == year:
            date_list[i] = 'Y'
        elif date_list[i] == month:
            date_list[i] = 'M'
        elif date_list[i] == day or date_list[i] == "%02d" % (int(day) + 1) or date_list[i] == "%02d" % (int(day) - 1):
            date_list[i] = 'D'
    date_fmt = '-'.join(date_list)
    aklog_printf('date_fmt: %s' % date_fmt)
    return date_fmt


def get_week_day(week):
    """将中文星期转换为英文"""
    week_day_dict = {
        '星期一': 'Monday',
        'Monday': 'Monday',
        '星期二': 'Tuesday',
        'Tuesday': 'Tuesday',
        '星期三': 'Wednesday',
        'Wednesday': 'Wednesday',
        '星期四': 'Thursday',
        'Thursday': 'Thursday',
        '星期五': 'Friday',
        'Friday': 'Friday',
        '星期六': 'Saturday',
        'Saturday': 'Saturday',
        '星期天': 'Sunday',
        'Sunday': 'Sunday',
    }
    return week_day_dict[week]


def get_os_cur_date(date_format='YYYY-MM-DD'):
    """获取系统当前日期并按照选择的日期格式输出"""
    cur = dt.datetime.now()
    yyyy = cur.strftime('%Y')
    mm = cur.strftime('%m')
    dd = cur.strftime('%d')
    ww = get_week_day(cur.strftime('%A'))
    if date_format == 'YYYY-MM-DD':
        return '%s-%s-%s' % (yyyy, mm, dd)
    elif date_format == 'YYYY/MM/DD':
        return '%s/%s/%s' % (yyyy, mm, dd)
    elif date_format == 'DD-MM-YYYY':
        return '%s-%s-%s' % (dd, mm, yyyy)
    elif date_format == 'DD/MM/YYYY':
        return '%s/%s/%s' % (dd, mm, yyyy)
    elif date_format == 'WW-DD-MM':
        return '%s-%s-%s' % (ww, dd, mm)
    elif date_format == 'WW-MM-DD':
        return '%s-%s-%s' % (ww, mm, dd)
    elif date_format == 'MM-DD-YYYY':
        return '%s-%s-%s' % (mm, dd, yyyy)
    elif date_format == 'MM/DD/YYYY':
        return '%s/%s/%s' % (mm, dd, yyyy)
    elif date_format == 'WW DD/MM/YYYY':
        return '%s %s/%s/%s' % (ww, dd, mm, yyyy)
    else:
        pass


def get_os_current_date_time(time_fmt='%Y-%m-%d %H:%M:%S'):
    """获取系统当前时间，传入日期时间格式"""
    cur_time = dt.datetime.now().strftime(time_fmt)
    aklog_printf('current_time: %s' % cur_time)
    return cur_time


def get_date_add_delta(date_str, day_delta, date_fmt='%Y-%m-%d'):
    """
    获取日期增量后的日期
    :param date_str: 2022-03-24，格式为：'%Y-%m-%d'
    :param day_delta: 增加天数，可为负数
    :param date_fmt: '%Y-%m-%d'
    :return:
    """
    aklog_printf('get_date_add_delta, date_str: %s, day_delta: %s' % (date_str, day_delta))
    src_date = dt.datetime.strptime(date_str, date_fmt)
    end_date = src_date + dt.timedelta(days=int(day_delta))
    end_date_str = end_date.strftime(date_fmt)
    return end_date_str


def get_date_time_add_delta(date_time, delta, time_fmt='%Y-%m-%d %H:%M:%S'):
    """
    获取日期增量后的日期
    :param date_time: 2022-03-24，格式为：'%Y-%m-%d', 2022-03-24 18:11:22
    :param delta: 时间增量，可为负数，如果时间格式精确到天，则增量为天数，如果精确到秒，则增量为秒
    :param time_fmt: '%Y-%m-%d', %Y-%m-%d %H:%M:%S
    :return:
    """
    src_date_time = dt.datetime.strptime(date_time, time_fmt)
    if time_fmt.endswith('%d'):
        end_date_time = src_date_time + dt.timedelta(days=int(delta))
    elif time_fmt.endswith('%H'):
        end_date_time = src_date_time + dt.timedelta(hours=int(delta))
    elif time_fmt.endswith('%M'):
        end_date_time = src_date_time + dt.timedelta(minutes=int(delta))
    else:
        end_date_time = src_date_time + dt.timedelta(seconds=int(delta))
    end_date_time_str = end_date_time.strftime(time_fmt)
    aklog_printf('date_time: %s, delta: %s, target: %s' % (date_time, delta, end_date_time_str))
    return end_date_time_str


def get_time_add_delta(time_str, time_delta):
    """
    获取时间增量后的时间
    :param time_str: 08:28:33PM, 20:28
    :param time_delta: 如果时间没有秒数，则time_delta为增加多少分钟，如果时间有秒数，则time_delta为增加多少秒
    :return:
    """
    aklog_printf('get_time_add_delta, time_str: %s, time_delta: %s' % (time_str, time_delta))
    if 'AM' in time_str or 'PM' in time_str:
        is_12_fmt = True
    else:
        is_12_fmt = False
    time_str = time_str.strip()
    time_str = trans_time_fmt_to_24(time_str)
    date_str = get_os_current_date_time('%Y-%m-%d')
    date_time_str = date_str + ' ' + time_str
    # 加上当前日期，组合成完整的日期时间，可以用于加减
    if time_str.count(':') == 1:
        date_time = dt.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
        end_time = date_time + dt.timedelta(minutes=int(time_delta))
        end_time_str = end_time.strftime('%H:%M')
    else:
        date_time = dt.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = date_time + dt.timedelta(seconds=int(time_delta))
        end_time_str = end_time.strftime('%H:%M:%S')

    if is_12_fmt:
        # 再转换成12小时制
        end_time_str = trans_time_fmt_to_12(end_time_str)
    aklog_printf(end_time_str)
    return end_time_str


def cmp_time_with_current(cmp_time, time_fmt='%Y-%m-%d %H:%M:%S'):
    """比较时间跟当前时间相差多少秒"""
    cur_time = time.time()
    cmp_time = time.mktime(time.strptime(cmp_time, time_fmt))
    delta = int(abs(cmp_time - cur_time))
    return delta


def start_system_ntp():
    sub_process_exec_command('net stop w32time')
    time.sleep(2)
    sub_process_exec_command('net start w32time')


def set_system_time(date, time_str, date_fmt="%Y-%m-%d", time_fmt="%H:%M:%S"):
    """设置电脑时间"""
    global now_time
    if now_time == 0:
        now_time = time.time()
    date = dt.datetime.strptime(date, date_fmt)
    date = date.strftime('%Y-%m-%d')
    time2 = dt.datetime.strptime(time_str, time_fmt)
    time2 = time2.strftime('%H:%M:%S')
    sub_process_exec_command('time {}'.format(time2))
    sub_process_exec_command('date {}'.format(date))


def reset_system_time(wait=False):
    if not wait:
        sub_process_exec_command('net stop "windows time"')
        time.sleep(2)
        sub_process_exec_command('net start "windows time"')
        time.sleep(5)
    else:
        # global now_time
        # for _ in range(20):
        #     sub_process_exec_command('net stop "windows time"')
        #     time.sleep(2)
        #     sub_process_exec_command('net start "windows time"')
        #     time.sleep(5)
        #     if 0 < time.time() - now_time < 3600:
        #         now_time = 0
        #         return
        # aklog_printf('长时间无法恢复系统时间')
        # return False

        # 门口机rebootschedule修改本地pc时间后, 出现后续的用例长时间卡住等待时间到达.
        # 仍大概率不同步时间. 修改
        import ntplib
        c = ntplib.NTPClient()
        response = ''
        for url in ('0.pool.ntp.org', 'pool.ntp.org', '0.pool.ntp.org', 'pool.ntp.org'):
            try:
                response = c.request(url)
            except:
                pass
            else:
                break
        ts = response.tx_time
        _date = time.strftime('%Y-%m-%d', time.localtime(ts))
        _time = time.strftime('%X', time.localtime(ts))
        sub_process_exec_command('date {} && time {}'.format(_date, _time))


def compare_time(time1, time2, absolute=True):
    """
    比较两个时间相差多少秒，两个时间格式要一致
    time1和time2：2022-01-28 15:45:32、2022-01-28 15:45、 15:45、 15:45:32
    time_fmt: 传入的time1和time2的格式
    """
    aklog_printf('time1: %s, time2: %s' % (time1, time2))
    try:
        time_fmt = '%Y-%m-%d %H:%M:%S'
        if '-' in time1 or '/' in time1:
            # 带有日期的时间
            time1 = reformat_datetime(time1, '%Y-%m-%d %H:%M:%S')
        else:
            current_date = dt.datetime.now().strftime('%Y-%m-%d')
            if time1.count(':') == 1:
                time_fmt = '%Y-%m-%d %H:%M'
            time1 = '%s %s' % (current_date, time1)

        if '-' in time2 or '/' in time2:
            # 带有日期的时间
            time2 = reformat_datetime(time2, '%Y-%m-%d %H:%M:%S')
        else:
            current_date = dt.datetime.now().strftime('%Y-%m-%d')
            if time2.count(':') == 1:
                time_fmt = '%Y-%m-%d %H:%M'
            time2 = '%s %s' % (current_date, time2)

        time1 = time.mktime(time.strptime(time1, time_fmt))
        time2 = time.mktime(time.strptime(time2, time_fmt))
        if absolute:
            # 取绝对值
            delta = int(abs(time1 - time2))
            aklog_printf('delta: %s' % delta)
        else:
            delta = int(time1 - time2)
            aklog_printf('time1 - time2 = %s' % delta)
        return delta
    except:
        aklog_printf(traceback.format_exc())
        return None


def compare_time_DMY(time1, time2, absolute=True):
    """
    比较两个时间相差多少秒，两个时间格式要一致
    time1和time2：28-01-2022 15:45:32、28-01-2022 15:45、 15:45、 15:45:32
    time_fmt: 传入的time1和time2的格式
    """
    aklog_printf('time1: %s, time2: %s' % (time1, time2))
    try:
        time_fmt = '%d-%m-%Y %H:%M:%S'
        if '-' in time1 or '/' in time1:
            # 带有日期的时间
            time1 = reformat_datetime(time1, '%d-%m-%Y %H:%M:%S')
        else:
            current_date = dt.datetime.now().strftime('%d-%m-%Y')
            if time1.count(':') == 1:
                time_fmt = '%d-%m-%Y %H:%M'
            time1 = '%s %s' % (current_date, time1)

        if '-' in time2 or '/' in time2:
            # 带有日期的时间
            time2 = reformat_datetime(time2, '%d-%m-%Y %H:%M:%S')
        else:
            current_date = dt.datetime.now().strftime('%d-%m-%Y')
            if time2.count(':') == 1:
                time_fmt = '%d-%m-%Y %H:%M'
            time2 = '%s %s' % (current_date, time2)

        time1 = time.mktime(time.strptime(time1, time_fmt))
        time2 = time.mktime(time.strptime(time2, time_fmt))
        if absolute:
            # 取绝对值
            delta = int(abs(time1 - time2))
            aklog_printf('delta: %s' % delta)
        else:
            delta = int(time1 - time2)
            aklog_printf('time1 - time2 = %s' % delta)
        return delta
    except:
        aklog_printf(traceback.format_exc())
        return None


def calculate_time_difference(time1, time2, time_format=None, absolute=True):
    """
    计算两个时间字符串之间的差值（单位：秒）。

    :param time1: 第一个时间字符串，格式为 'YYYY-MM-DD HH:MM:SS.sss'
    :param time2: 第二个时间字符串，格式为 'YYYY-MM-DD HH:MM:SS.sss'
    :param time_format: 时间格式，"%Y-%m-%d %H:%M:%S"
    :param absolute:
    :return: 时间差值（秒），保留 3 位小数
    """
    # 定义时间格式
    if not time_format:
        time_format = "%Y-%m-%d %H:%M:%S"

    # 将时间字符串解析为 datetime 对象
    dt1 = dt.datetime.strptime(time1, time_format)
    dt2 = dt.datetime.strptime(time2, time_format)

    # 计算时间差
    if absolute:
        time_difference = abs((dt1 - dt2).total_seconds())  # 取绝对值，防止负数
    else:
        time_difference = (dt1 - dt2).total_seconds()
    return round(time_difference, 3)  # 保留 3 位小数


def get_week_of_month(date_str=None):
    """获取某天处于当月的第几周"""
    aklog_printf('get_week_of_month, %s' % date_str)
    if date_str and isinstance(date_str, str):
        if ':' not in date_str:
            now_time = dt.datetime.strptime(date_str + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        else:
            now_time = dt.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    else:
        now_time = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # 当月第一天
    one_time = now_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 当前日期处于本月第几周
    week_num = int(now_time.strftime('%W')) - int(one_time.strftime('%W')) + 1

    # 当前日期所在周的周一
    # week_start_time = now_time - dt.timedelta(days=now_time.weekday(), hours=now_time.hour, minutes=now_time.minute,
    #                                           seconds=now_time.second)

    # 当前日期所在周的周日
    # week_end_time = week_start_time + dt.timedelta(days=6, hours=23, minutes=59, seconds=59)

    # 当前所处月份
    # month_num = int(now_time.strftime('%m'))

    # 当前年份
    # year_num = int(now_time.strftime('%Y'))
    return week_num


def get_week_num_of_day(date_str=None):
    """
    获取某一天是星期几
    date_str: 格式： 2020-10-23
    return: 0 - 6，0表示星期天
    """
    if not date_str:
        week_num = datetime.datetime.today().strftime('%w')
    else:
        week_num = datetime.datetime.strptime(date_str, '%Y-%m-%d').strftime('%w')
    return int(week_num)


def get_time_zone_info(time_zone_name):
    """获取时区信息"""
    time_zone_data = param_get_time_zone_data()
    if time_zone_data == 'unknown':
        time_zone_data = xml_parse_time_zone()
        param_put_time_zone_data(time_zone_data)
    if time_zone_name in time_zone_data:
        return time_zone_data[time_zone_name]
    else:
        aklog_printf('%s 时区不存在' % time_zone_name)
        return None


def trans_week_fmt_to_date(mon, week_num, week, hour=0, minute=0, second=0):
    """
    转换日期格式，将今年某月第几个星期几几点的格式，转成%Y-%m-%d %H
    :param mon:6 (1-12)
    :param week_num:2 (1-5)
    :param week:1-7
    :param hour:2
    :param minute:
    :param second:
    :return: <class 'datetime.datetime'> 2021-06-09 02:00:00
    """
    aklog_printf('trans_week_fmt_to_date, mon: %s, week_num: %s, week: %s, hour: %s' % (mon, week_num, week, hour))
    try:
        # 要获取该月份有多少天，如果日期超过了月份天数，那么需要减去7天
        current_year = dt.datetime.now().strftime('%Y')
        first_day_week, month_len = calendar.monthrange(int(current_year), int(mon))
        target_day = (int(week_num) - 1) * 7 + int(week) - int(first_day_week)
        if target_day > month_len:
            target_day = target_day - 7

        # 然后再计算第几个星期几为本月几号
        target_date = dt.datetime.now().replace(month=int(mon), day=target_day, hour=int(hour),
                                                minute=minute, second=second, microsecond=0)
        aklog_printf(target_date)
        return target_date
    except:
        aklog_printf(traceback.format_exc())
        return None


def trans_time_to_time_zone(dst_tz, src_time_str=None, src_tz=8, dst_time_fmt='%Y-%m-%d %H:%M:%S',
                            daylight_saving=True):
    """
    将当前时间转成对应时区的时间，并计算夏令时，时区信息根据libconfig\\libconfig_xml\\resource\\TimeZone.xml文件
    :param dst_tz: 转换的目标时区，比如：GMT-10:00 Adak
    :param src_time_str: 原始时间，时间格式为：%Y-%m-%d %H:%M:%S
    :param src_tz: 原始时区，默认GMT+8
    :param dst_time_fmt: 目标时间格式：%Y-%m-%d %H:%M:%S
    :param daylight_saving: 是否计算夏令时
    :return:
    """
    aklog_printf('trans_time_to_time_zone, dst_tz: %s, src_time: %s, src_tz: %s' % (dst_tz, src_time_str, src_tz))
    try:
        # 获取时区信息
        time_zone_info = get_time_zone_info(dst_tz)

        # 获取原始时间
        if src_time_str and isinstance(src_time_str, str):
            src_time = dt.datetime.strptime(src_time_str, "%Y-%m-%d %H:%M:%S")
        else:
            src_time = dt.datetime.now()

        src_time_year = src_time.strftime("%Y")

        # 时差计算
        tz = dst_tz.split('GMT')[1].split(' ')[0]
        if '-' in tz:
            tz_hour = tz.split('-')[1].split(':')[0]
            tz_min = tz.split(':')[1]
            tz_delta_hour = -int(src_tz) - int(tz_hour)
            tz_delta_min = int(tz_min)
        else:
            tz_hour = tz.split('+')[1].split(':')[0]
            tz_min = tz.split(':')[1]
            tz_delta_hour = int(tz_hour) - int(src_tz)
            tz_delta_min = int(tz_min)

        trans_time = src_time + dt.timedelta(hours=tz_delta_hour, minutes=tz_delta_min)

        if not daylight_saving:
            pass
        elif not time_zone_info:
            aklog_printf('获取夏令时信息失败')
            pass
        elif time_zone_info.get('Type') == '1':
            # 将星期转换成日期
            start_time_mon = time_zone_info['Start'].split('/')[0]
            start_time_week_num = time_zone_info['Start'].split('/')[1]
            start_time_week = time_zone_info['Start'].split('/')[2]
            start_time_hour = time_zone_info['Start'].split('/')[3]
            start_time = trans_week_fmt_to_date(start_time_mon, start_time_week_num, start_time_week, start_time_hour)

            end_time_mon = time_zone_info['End'].split('/')[0]
            end_time_week_num = time_zone_info['End'].split('/')[1]
            end_time_week = time_zone_info['End'].split('/')[2]
            end_time_hour = time_zone_info['End'].split('/')[3]
            end_time = trans_week_fmt_to_date(end_time_mon, end_time_week_num, end_time_week, end_time_hour, 59, 59)

            # 比较当前时间是否在夏令时范围内
            if start_time <= trans_time <= end_time:
                trans_time = trans_time + dt.timedelta(minutes=int(time_zone_info['Offset']))
        elif time_zone_info.get('Type') == '0':
            start_time_mon = time_zone_info['Start'].split('/')[0]
            start_time_day = time_zone_info['Start'].split('/')[1]
            start_time_hour = time_zone_info['Start'].split('/')[2]
            start_time = '%s-%s-%s %s' % (src_time_year, start_time_mon, start_time_day, start_time_hour)
            start_time = dt.datetime.strptime(start_time, '%Y-%m-%d %H')

            end_time_mon = time_zone_info['End'].split('/')[0]
            end_time_day = time_zone_info['End'].split('/')[1]
            end_time_hour = time_zone_info['End'].split('/')[2]
            end_time = '%s-%s-%s %s' % (src_time_year, end_time_mon, end_time_day, end_time_hour)
            end_time = dt.datetime.strptime(end_time, '%Y-%m-%d %H')

            # 比较当前时间是否在夏令时范围内
            if start_time <= trans_time <= end_time:
                trans_time = trans_time + dt.timedelta(minutes=int(time_zone_info['Offset']))

        trans_time = trans_time.strftime(dst_time_fmt)
        aklog_printf(trans_time)
        return trans_time
    except:
        aklog_printf(traceback.format_exc())
        return None


def trans_time_zone_with_daylight_saving_time(time_zone):
    """
    当时区处于夏令时，转换时区为夏令时时区
    比如，GMT-10:00 Adak时区，在夏令时时间内，转成：GMT-9:00 Adak
    time_zone: 转换的目标时区，比如：GMT-10:00 Adak
    """
    aklog_printf('trans_time_zone_with_daylight_saving_time: time_zone: %s' % time_zone)
    try:
        # 转换当前时间为目标时区，并比较带夏令时和不带夏令时的两个时间，如果一致，说明当前未进入夏令时时间，时区不需要跟随夏令时改变
        time_tz_daylight = trans_time_to_time_zone(time_zone, daylight_saving=True)
        time_tz = trans_time_to_time_zone(time_zone, daylight_saving=False)
        if time_tz != time_tz_daylight:
            # 在夏令时范围内，计算偏移时间，一般是1个小时
            delta_s = compare_time(time_tz_daylight, time_tz, False)
            delta_m, delta_s = divmod(delta_s, 60)
            delta_h, delta_m = divmod(delta_m, 60)
            tz_h = str_get_content_between_two_characters(time_zone, 'GMT', ':')
            tz_m = str_get_content_between_two_characters(time_zone, ':', ' ')
            city = time_zone.split(' ')[1]
            dst_tz_h = int(tz_h) + delta_h
            dst_tz_m = int(tz_m) + delta_m
            if dst_tz_h > 0:
                dst_tz = 'GMT+%d:%02d %s' % (dst_tz_h, dst_tz_m, city)
            else:
                dst_tz = 'GMT%d:%02d %s' % (dst_tz_h, dst_tz_m, city)
        else:
            dst_tz = time_zone
        aklog_printf(dst_tz)
        return dst_tz
    except:
        aklog_printf(traceback.format_exc())
        return time_zone


def trans_month_to_num(month):
    """将月份名称或简写转换成数字"""
    time_locale = locale.setlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, 'en')
    if month in list(calendar.month_abbr):
        num = list(calendar.month_abbr).index(month)
    elif month in list(calendar.month_name):
        num = list(calendar.month_name).index(month)
    else:
        aklog_printf('月份名称或简写有误')
        num = None
    locale.setlocale(locale.LC_TIME, time_locale)
    return num


def trans_month_num_to_name(month_num):
    """将月份数字转成名称"""
    return calendar.month_name[int(month_num)]


def time_sleep_begin():
    """等待时间开始"""
    aklog_printf('time_sleep_begin')
    global g_wait_time_begin
    g_wait_time_begin = time.time()


def time_sleep_end(wait_time):
    """等待时间结束, 与time_sleep_begin配合使用，用于等待时间"""
    aklog_printf('time_sleep_end, wait_time: %s' % wait_time)
    global g_wait_time_begin
    already_wait_time = int(round(time.time() - g_wait_time_begin, 0))
    wait_time = int(wait_time)
    if wait_time > already_wait_time:
        time.sleep(wait_time - already_wait_time)


def sleep_to_end_time(end_time, time_delta=0):
    """
    等待到达某个时间点
    end_time: 14:20, 14:20:30
    time_delta: 到达时间后多等待几秒时间
    """
    now = dt.datetime.now()

    # 获取当前日期
    end_date = now.strftime('%Y-%m-%d')

    # 判断 end_time 格式
    if end_time.count(':') == 1:
        time_fmt = '%Y-%m-%d %H:%M'
    else:
        time_fmt = '%Y-%m-%d %H:%M:%S'

    # 组合当前日期和目标时间
    end_date_time = '%s %s' % (end_date, end_time)
    end_time_dt = dt.datetime.strptime(end_date_time, time_fmt)

    # 如果目标时间已经过去，说明是第二天的时间
    if end_time_dt <= now:
        end_time_dt += dt.timedelta(days=1)

    # 计算等待时间
    wait_time = (end_time_dt - now).total_seconds() + time_delta

    if wait_time > 0:
        aklog_printf('end_time: %s, sleep: %s 秒' % (end_time, int(wait_time)))
        time.sleep(wait_time)


def sleep_within_time_range(start_time_str, end_time_str, check_week='1234567'):
    """
    在时间段之内等待
    start_time_str: '12:30:00'
    end_time_str: '13:32:00'
    check_week: 检查是否为周几，12345表示周一至周五
    """
    aklog_printf()
    # 判断当前时间是否在午休时间段（周一至周五）
    cur_date_str = dt.datetime.now().strftime('%Y-%m-%d')
    start_date_time_str = '%s %s' % (cur_date_str, start_time_str)
    start_time = time.mktime(time.strptime(start_date_time_str, '%Y-%m-%d %H:%M:%S'))
    end_date_time_str = '%s %s' % (cur_date_str, end_time_str)
    end_time = time.mktime(time.strptime(end_date_time_str, '%Y-%m-%d %H:%M:%S'))
    # 获取当前时间和周几
    cur_time = time.time()
    cur_week = dt.datetime.now().strftime('%w')
    if start_time <= cur_time <= end_time and str(cur_week) in check_week:
        wait_time = int(end_time - cur_time)
        aklog_printf('等待 %s 秒后再继续执行' % wait_time)
        time.sleep(wait_time)


def judge_cur_time_within_time_range(start_time_str, end_time_str, check_week='1234567'):
    """
    检查当前时间是否在时间范围之内
    start_time_str: '12:30:00'
    end_time_str: '13:32:00'
    check_week: 检查是否为周几，12345表示周一至周五
    """
    # 判断当前时间是否在午休时间段（周一至周五）
    cur_date_str = dt.datetime.now().strftime('%Y-%m-%d')
    start_date_time_str = '%s %s' % (cur_date_str, start_time_str)
    start_time = time.mktime(time.strptime(start_date_time_str, '%Y-%m-%d %H:%M:%S'))
    end_date_time_str = '%s %s' % (cur_date_str, end_time_str)
    end_time = time.mktime(time.strptime(end_date_time_str, '%Y-%m-%d %H:%M:%S'))
    # 获取当前时间和周几
    cur_time = time.time()
    # cur_time_str = dt.datetime.now().strftime('%H:%M:%S')
    cur_week = dt.datetime.now().strftime('%w')
    if start_time <= cur_time <= end_time and str(cur_week) in check_week:
        wait_time = int(end_time - cur_time)
        # aklog_printf('当前时间 %s 在 %s 和 %s 范围内' % (cur_time_str, start_time_str, end_time_str))
        return wait_time
    else:
        # aklog_printf('当前时间 %s 不在 %s 和 %s 范围内' % (cur_time_str, start_time_str, end_time_str))
        return 0


def get_near_time_list(time_fmt='%H:%M', time_delta=60):
    """
    获取上下1分钟误差时间范围
    time_fmt: '%H:%M', '%I:%M %p'
    time_delta: 时间前后多少秒，60 、 120
    """
    curtime = time.time()
    nextmin = curtime + time_delta
    prevmin = curtime - time_delta
    return [time.strftime(time_fmt, time.localtime(x)) for x in [curtime, nextmin, prevmin]]


def get_time_zone_index(full_timezone):
    """
    'GMT-10:00 Honolulu' ==> -10
    得到跟+8时区差18小时
    """
    return int(re.search(r'GMT(.*):.*', full_timezone).group(1))


def get_strftime_range(timezone_index, hour_12=False, get_date=False, dateformat='%m-%d-%Y'):
    """
    返回如 -3时区, +11 时区现在的系统时间, 有+1 -1 时间误差.
    """
    ret_list = []
    cur_time = time.time()
    minus_time = 3600 * abs(8 - timezone_index)
    minus_time_m60 = minus_time - 60
    minus_time_a60 = minus_time + 60
    if not get_date:
        if not hour_12:
            fmat = '%H:%M'
        else:
            fmat = '%I:%M %p'
        if timezone_index > 8:
            ret_list.append(time.strftime(fmat, time.localtime(cur_time + minus_time)))
            ret_list.append(time.strftime(fmat, time.localtime(cur_time + minus_time_a60)))
            ret_list.append(time.strftime(fmat, time.localtime(cur_time + minus_time_m60)))
        else:
            ret_list.append(time.strftime(fmat, time.localtime(cur_time - minus_time)))
            ret_list.append(time.strftime(fmat, time.localtime(cur_time - minus_time_a60)))
            ret_list.append(time.strftime(fmat, time.localtime(cur_time - minus_time_m60)))
        # 有的设备端, 的首尾0不显示
        # ret_list = [i.lstrip('0') for i in ret_list]
        new_list = [i.lstrip('0') for i in ret_list]
        ret_list = ret_list + new_list
        return ret_list
    else:
        # 获取日期, 格式同R29设备端格式  Thu 02/10/2022
        if timezone_index > 8:
            ret_list = [
                time.strftime('%a {}'.format(dateformat), time.localtime(cur_time + minus_time)),  # R29 / 格式
                time.strftime('%a {}'.format(dateformat.replace("-", '/')), time.localtime(cur_time + minus_time))
                # 915 - 格式
            ]
            return ret_list
        else:
            ret_list = [
                time.strftime('%a {}'.format(dateformat), time.localtime(cur_time - minus_time)),  # R29 / 格式
                time.strftime('%a {}'.format(dateformat.replace("-", '/')), time.localtime(cur_time - minus_time))
                # 915 - 格式
            ]
            return ret_list


def judge_time_is_correct(timestring, checktimeformat=None, is_24hour=True, timezone=8):
    """
    1. 默认检测时间在+8时区内, 且时间正确 (误差+-2分钟). 可输入其他9, 7, -1时区.
    2. is_24hour: 检测时间是12小时/24小时.
    3. checktimeformat: 检测timestring是 %H:%M 或 %H:%M:%S' 或者None不检查
    ps:
        无视小时: 09或9 的区别
        timestring可不包含AM, PM.
    """

    def strftime(fmt, timestamp, strip_hour):
        ret = time.strftime(fmt, time.localtime(timestamp))
        if strip_hour:
            if ret.split(':')[0] == '00':
                ret = '0:' + ':'.join(ret.split(':')[1:])
            else:
                ret = ret.lstrip('0')
        return ret

    if is_24hour:
        timeformat = '%H:%M'
    else:
        timeformat = '%I:%M'

    curtime = time.time() + 3600 * (timezone - 8)
    range_list = [
        strftime(timeformat, curtime - 120, strip_hour=True),
        strftime(timeformat, curtime - 60, strip_hour=True),
        strftime(timeformat, curtime, strip_hour=True),
        strftime(timeformat, curtime + 60, strip_hour=True),
        strftime(timeformat, curtime + 120, strip_hour=True),
        strftime(timeformat, curtime - 120, strip_hour=False),
        strftime(timeformat, curtime - 60, strip_hour=False),
        strftime(timeformat, curtime, strip_hour=False),
        strftime(timeformat, curtime + 60, strip_hour=False),
        strftime(timeformat, curtime + 120, strip_hour=False),
    ]
    if 'am' in timestring.lower() or 'pm' in timestring.lower():
        # 如果传入字符中有am pm
        if 'am' in timestring.lower():
            if time.strftime('%p') == 'PM':
                aklog_error('检查时间: {} 失败.  当前{}时区时间应该是下午PM'.format(timestring, timezone))
                return False
        elif 'pm' in timestring.lower():
            if time.strftime('%p') == 'AM':
                aklog_error('检查时间: {} 失败.  当前{}时区时间应该是上午AM'.format(timestring, timezone))
                return False
    # 检查时间字符串的格式是 %H:%M或%H:%M:%S
    if checktimeformat:
        if checktimeformat == '%H:%M':
            if len(timestring.split(':')) != 2:
                aklog_error('检查时间: {} 失败.  格式不是: {}'.format(timestring, checktimeformat))
                return False
            if not re.search(r'\d+:\d', timestring):
                aklog_error('检查时间: {} 失败.  格式不是: {}'.format(timestring, checktimeformat))
                return False
        elif checktimeformat == '%H:%M:%S':
            if len(timestring.split(':')) != 3:
                aklog_error('检查时间: {} 失败.  格式不是: {}'.format(timestring, checktimeformat))
                return False
            if not re.search(r'\d+:\d+:\d+', timestring):
                aklog_error('检查时间: {} 失败.  格式不是: {}'.format(timestring, checktimeformat))
                return False
    # 检查时间在误差范围内

    aft_time = ':'.join(timestring.split(':')[:2])
    if aft_time not in range_list:
        if is_24hour:
            aklog_error(
                '检查时间: {} 失败. 时间不是{}时区内当前24小时制时间: {}'.format(timestring, timezone, range_list))
        else:
            aklog_error(
                '检查时间: {} 失败. 时间不是{}时区内当前12小时制时间: {}'.format(timestring, timezone, range_list))
        return False
    aklog_info('检查时间: {} 通过'.format(timestring))
    return True


def is_time_near(target_time_str, minutes_range=2):
    # 获取当前时间
    now = dt.datetime.now()

    # 将目标时间字符串转换为 datetime 对象
    target_time = dt.datetime.strptime(target_time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)

    # 计算时间范围
    start_time = target_time - datetime.timedelta(minutes=minutes_range)
    end_time = target_time + datetime.timedelta(minutes=minutes_range)
    aklog_debug(f'系统时间：{now}， 获取的文本时间：{target_time_str}')
    # 检查当前时间是否在范围内
    return start_time <= now <= end_time


def get_starttime_endtime_in_schedule(offset=3600, timeformat='%H:%M'):
    """
    用于返回StartTime, EndTime, 放到schedule里面. 需考虑跨天情况. 用于测试schedule.
    """
    starttime = time.strftime(timeformat, time.localtime(time.time() - offset))
    endtime = time.strftime(timeformat, time.localtime(time.time() + offset))
    if endtime < starttime:
        if timeformat == '%H:%M':
            endtime = '23:59:59'
        else:
            endtime = '23:59'
    return starttime, endtime


def get_starttime_endtime_out_of_schedule(offset=3600, timeformat='%H:%M'):
    """
    用于返回StartTime, EndTime, 放到schedule里面. 需考虑跨天情况. 用于测试schedule.
    """
    starttime = time.strftime(timeformat, time.localtime(time.time() - offset))
    endtime = time.strftime(timeformat, time.localtime(time.time() -(offset/2)))
    if endtime < starttime:
        if timeformat == '%H:%M':
            starttime = '20:00:00'
            endtime = '20:10:00'
        else:
            starttime = '20:00'
            endtime = '20:10'
    return starttime, endtime


if __name__ == "__main__":
    print('测试代码')
    print(calculate_time_difference('2025-02-28 14:57:01.232', '2025-02-28 14:56:58.414',
                                    time_format="%Y-%m-%d %H:%M:%S.%f"))
