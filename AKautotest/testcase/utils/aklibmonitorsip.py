# -*- coding: UTF-8 -*-

import sys
import os
import time
import subprocess

root_path = os.getcwd()
pos = root_path.find("AKautotest")

if pos == -1:
    print("runtime error")
    exit(1)

root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)
from akcommon_define import *

g_monitor_sip_path = root_path + '\\tools\\monitorsip'


# region 基础接口
def backup_siplog():
    file = g_monitor_sip_path + '\\sip.txt'
    if not os.path.exists(file):
        aklog_warn('不存在sip监控log.')
        return False
    result_file = aklog_get_result_dir() + '\\device_log\\' + time.strftime('%Y%m%d_%H%M%S') + '_sip.txt'
    if not os.path.exists(aklog_get_result_dir() + '\\device_log\\'):
        os.mkdir(aklog_get_result_dir() + '\\device_log\\')
    aklog_info('backup file ---> ' + result_file)
    shutil.copy(file, result_file)


def start_monitor_sip(port=5060):
    """
    启动监控sip, 并清空url.txt
    """
    clear_sip_log()
    cmd_close_process_by_name('monitorSIPtoPC.exe')
    sub_process_exec_command(
        g_monitor_sip_path + '\\monitorSIPtoPC.exe' + ' ' + g_monitor_sip_path + '\\sip.txt' + ' ' + str(port),
        timeout=5)


def clear_sip_log():
    file = g_monitor_sip_path + '\\sip.txt'
    File_process.remove_file(file)


def stop_monitor_sip():
    cmd_close_process_by_name('monitorSIPtoPC.exe')


def get_monitor_ip_sipinfo_dict(filterip, filter_req='', filter_direction='both'):
    """
    获取一次后, 清空. 避免影响后续用例
    返回:
        sip info数组.
    参数:
        filter_req : INVITE, REGISTER, INFO, MESSAGE等
        filter_direction: both, src, dst   过滤ip.src==设备IP/  ip.addr==设备ip / ip.dst ==设备ip
            both: 过滤电脑收+发的sip报文.
            src:  过滤设备--> 电脑的sip报文.
            dst:  过滤电脑--> 设备的sip报文.
    """
    """
{'ip_direction': 'src' / 'dst',
 'request_type': 'INVITE',
 'transport_type': 'UDP' / 'TCP'
 'port': 5062,   # 设备端的sip端口号. 
 'request_url': 'INVITE sip:1005@192.168.30.213 SIP/2.0',
 'Via': 'SIP/2.0/UDP 192.168.30.160:5062;branch=z9hG4bK763629487',
 'From': '"1000" <sip:1000@192.168.30.213>;tag=2096496079',
 'To': '<sip:1005@192.168.30.213>',
 'Call-ID': '1952264503@192.168.30.160',
 'CSeq': '21 INVITE',
 'Contact': '<sip:1000@192.168.30.160:5062>',
 'Proxy-Authorization': 'Digest username="1000", realm="3CXPhoneSystem", '
                        'nonce="414d535c1e2a093031:731e299de8e06a8bb3e21107fbc13fc8", '
                        'uri="sip:1005@192.168.30.213", '
                        'response="a7f39c1809e102f0799456c45d161aae", '
                        'algorithm=MD5',
 'Content-Type': 'application/sdp',
 'Allow': 'INVITE, INFO, PRACK, ACK, BYE, CANCEL, OPTIONS, NOTIFY, REGISTER, SUBSCRIBE, REFER, PUBLISH, UPDATE, MESSAGE',
 'Max-Forwards': '70',
 'User-Agent': 'Akuvox S565 565.30.255.55 0C1105260B3B',
 'Subject': 'call invite',
 'Supported': 'replaces',
 'Allow-Events': 'talk,hold,conference,refer,check-sync',
 'X-Caller': '',
 'Content-Length': '478',
 'sdp': ['v=0',
         'o=1000 5000 5000 IN IP4 192.168.30.160',
         's=Talk',
         'c=IN IP4 192.168.30.160',
         'b=AS:4000',
         't=0 0',
         'm=audio 11800 RTP/AVP 0 8 18 9 101',
         'a=ptime:20',
         'a=rtpmap:0 PCMU/8000',
         'a=rtpmap:8 PCMA/8000',
         'a=rtpmap:18 G729/8000',
         'a=fmtp:18 annexb=no',
         'a=rtpmap:9 G722/8000',
         'a=rtpmap:101 telephone-event/8000',
         'a=fmtp:101 0-15',
         'a=sendrecv',
         'm=video 11802 RTP/AVP 104',
         'a=ptime:20',
         'a=rtpmap:104 H264/90000',
         'a=fmtp:104 '
         'profile-level-id=42e01f;packetization-mode=0;max-br=2048;max-mbps=40500',
         'a=sendrecv']}
    """
    if filter_direction == '':
        filter_direction = 'both'
    file = g_monitor_sip_path + '\\sip.txt'
    if not os.path.exists(file):
        return []
    with open(file, 'r', encoding='utf8') as f:
        content = f.read()
    retdict = {}
    for i in content.split('----------SIP-------'):
        req_info = {}
        sdp_state = False
        write_state = True

        for j in i.splitlines():
            if not j.strip():
                continue
            if '-->' in j:
                ip, request_url = j.strip().split('-->')
                ip, direction, transport_type, port = ip.split(':')
                if filter_direction != 'both' and filter_direction != direction.strip():
                    # 过滤抓包方向
                    write_state = False
                else:
                    write_state = True
                if write_state:
                    if ip.strip() not in retdict:
                        retdict[ip.strip()] = []
                    if request_url.startswith('SIP/2.0'):
                        # 应答: request_type只回复status code
                        req_info['request_type'] = request_url.strip('SIP/2.0').strip().split(' ', 1)[0]
                        req_info['request_url'] = request_url
                        req_info['transport_type'] = transport_type
                        req_info['port'] = port
                    else:
                        # 请求
                        req_info['request_type'] = request_url.split(' ', 1)[0]
                        req_info['request_url'] = request_url
                        req_info['transport_type'] = transport_type
                        req_info['port'] = port
            else:
                if write_state:
                    j = j.strip()
                    if 'Content-Length' in j and j != 'Content-Length: 0':
                        # 最后一个是content length
                        sdp_state = True
                        req_info['Content-Length'] = j.split(':')[1].strip()
                    if not sdp_state:
                        key, value = j.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        req_info[key] = value
                    else:
                        # sdp的每行都直接添加到sdp里.
                        if 'sdp' not in req_info:
                            req_info['sdp'] = []
                        if 'Content-Length' not in j:
                            req_info['sdp'].append(j)
        if req_info:
            retdict[ip.strip()].append(req_info)

    clear_sip_log()
    if not retdict.get(filterip, []):
        return []

    newlist = retdict.get(filterip, [])
    if filter_req:
        retlist = []
        for i in newlist:
            if i.get('request_type').lower() == filter_req.lower():
                retlist.append(i)
        return retlist
    else:
        return newlist


# endregion


# region SIP业务接口
def monitor_check_is_exist_rport(deviceip):
    retlist = get_monitor_ip_sipinfo_dict(deviceip, '', 'src')
    if not retlist:
        aklog_error("监控sip抓包失败")
        return False
    for i in retlist:
        if 'rport;' not in i.get('Via'):
            aklog_error('检查Via中的rport字段失败!')
            return False
    return True


def monitor_check_useragent(deviceip, agent):
    retlist = get_monitor_ip_sipinfo_dict(deviceip, '', 'src')
    if not retlist:
        aklog_error("监控sip抓包失败")
        return False
    for i in retlist:
        if i.get('User-Agent') != agent:
            aklog_error("user agent检查失败!")
            return False
    return True


def monitor_check_outbound(deviceip, sipserver):
    """
    outbound地址需要是电脑IP地址才能检查
    """
    retlist = get_monitor_ip_sipinfo_dict(deviceip, '', 'src')
    if not retlist:
        aklog_error("监控sip抓包失败")
        return False
    for i in retlist:
        if '@' + sipserver not in i.get('To'):
            aklog_printf(f'sip报文中sipserver显示错误: {i.get("To")}')
            return False
    return True


def monitor_check_local_sip_port(deviceip, minport, maxport):
    retlist = get_monitor_ip_sipinfo_dict(deviceip, '', 'both')
    if not retlist:
        aklog_error("监控sip抓包失败")
        return False
    for i in retlist:
        if int(i.get('port')) < minport or int(i.get('port')) > maxport:
            aklog_error(f'sip报文中检查设备端sip port失败: {i.get("port")}')
            return False
    return True


def monitor_check_sip_transport(deviceip, transport='UDP'):
    retlist = get_monitor_ip_sipinfo_dict(deviceip, '', 'both')
    if not retlist:
        aklog_error("监控sip抓包失败")
        return False
    for i in retlist:
        if i.get('transport_type').lower() != transport.lower():
            aklog_error('SIP 抓包检测传输类型失败!')
            return False
    return True


# endregion
