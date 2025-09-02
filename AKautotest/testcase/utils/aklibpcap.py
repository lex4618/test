# -*- coding: UTF-8 -*-
import json
import sys
import os, asyncio
import threading
import time
import traceback
import shutil

from pyshark.capture.capture import TSharkCrashException
from scapy.utils import PcapReader, rdpcap
import pyshark
import re
import scapy.layers.l2
import scapy.layers.inet

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)
from akcommon_define import *

g_tshark_path = root_path + '\\tools\\WiresharkPortable\\App\\Wireshark\\tshark.exe'
del_state = False
live_capture_thread = None
need_backup_pcap = True  # 是否备份pcap.


def disable_backup_pcap():
    """
    关闭备份pcap功能, 用于如室内机30天抓包检测通话
    """
    global need_backup_pcap
    need_backup_pcap = False


def enable_backup_pcap():
    global need_backup_pcap
    need_backup_pcap = True


def copy_pcap_to_device_log(pcap):
    """
    复制phone.pcap到device_log路径下
    """
    if os.path.exists(pcap):
        result_file = aklog_get_result_dir() + '\\device_log\\' + time.strftime('%Y%m%d_%H%M%S') + '.pcap'
        try:
            if not os.path.exists(aklog_get_result_dir() + '\\device_log\\'):
                os.mkdir(aklog_get_result_dir() + '\\device_log\\')
            aklog_info('backup file ---> ' + result_file)
            shutil.copy(pcap, result_file)
        except:
            aklog_error(traceback.format_exc())


def copypcap2(pcapfile):
    """清空本次之前的记录， 只保持本次自动化的pcap文件"""
    global del_state
    if not del_state:
        aklog_debug('准备删除之前的pcap记录.')
        pcap_dir = os.path.dirname(pcapfile)
        phone_pcap = os.path.basename(pcapfile)
        if 'device_log' not in pcap_dir:
            for i in os.listdir(pcap_dir):
                if i.endswith('.pcap') and i != phone_pcap:
                    try:
                        os.remove(pcap_dir + '\\' + i)
                        aklog_printf('deleting old backup pcap file: %s' % i)
                    except:
                        pass
        del_state = True
    bak_file = os.path.dirname(pcapfile) + '\\' + time.strftime('%Y%m%d_%H%M%S') + '.pcap'
    if need_backup_pcap:
        copy_pcap_to_device_log(pcapfile)


def backup_pcap(fn):
    def test(*arg, **kwargs):
        ret = fn(*arg, **kwargs)
        for i in arg:
            if type(i) == str and i.endswith('.pcap'):
                if 'device_log' not in i:
                    copypcap2(i)
        for j in kwargs.values():
            if type(j) == str and j.endswith('.pcap'):
                if 'device_log' not in j:
                    copypcap2(j)
        return ret

    return test


def get_tshark_path():
    """
    由于V3.4版本的wireshark存在有些包无法解析的问题，所以安装了个绿色版再tools目录下，并指定tshark_path为这个绿色版的路径，该方法先弃用
    wireshark如果不是安装在C盘默认路径下，则需要在config.ini中指定路径，然后在调用pyshark.FileCapture，要加参数tshark_path
    """
    global g_tshark_path
    if not g_tshark_path:
        tshark_path = WindowsReg.reg_get_tshark_path()  # 先通过注册表获取tshark.exe路径，如果获取不到再通过config.ini指定
        if not tshark_path:
            config_ini_data = param_get_config_ini_data()
            if config_ini_data == 'unknown':
                config_ini_data = config_get_all_data_from_ini_file()
            if 'environment' in config_ini_data and 'tshark_path' in config_ini_data['environment']:
                tshark_path = config_ini_data['environment']['tshark_path']
                if not tshark_path or not os.path.exists(tshark_path):
                    tshark_path = None
            else:
                tshark_path = None
        g_tshark_path = tshark_path
    return g_tshark_path


# region 0. 基础接口
def return_pc_capture_file():
    aklog_info('电脑抓包文件路径: {}'.format(os.path.join(root_path, 'tools', 'cmd_ftpserver', 'test1.pcap')))
    return os.path.join(root_path, 'tools', 'cmd_ftpserver', 'test1.pcap')


def pcap_pc_start_capture(timeout=30):
    """调试中"""

    def test():
        File_process.remove_file(return_pc_capture_file())
        network_adapter = cmd_get_network_adapter_name()
        for i in range(2):
            try:
                new_loop = asyncio.ProactorEventLoop()
                asyncio.set_event_loop(new_loop)
                cap = pyshark.LiveCapture(interface=network_adapter, tshark_path=g_tshark_path, debug=False,
                                          output_file=return_pc_capture_file())
                # cap.load_packets()
                aklog_info('电脑抓包中')
                curtime = time.time()
                cap.sniff(timeout=timeout)
                if time.time() - curtime < timeout - 5:
                    aklog_error('电脑抓包失败, 时长没有到指定值就停止!!')
                    if i == 0:
                        try:
                            cap.close()
                        except:
                            pass
                        aklog_error('电话抓包失败, 等待10秒后重试..')
                        time.sleep(10)
                        continue
                    else:
                        return False
                else:
                    time.sleep(1)
                    try:
                        cap.close()
                    except:
                        pass
                    return True
            except:
                aklog_error('电脑抓包异常!')
                aklog_debug(traceback.format_exc())
                return False

    global live_capture_thread
    live_capture_thread = threading.Thread(target=test)
    live_capture_thread.daemon = True
    live_capture_thread.start()


def pcap_pc_stop_capture(timeout=120):
    global live_capture_thread
    if live_capture_thread:
        live_capture_thread.join(timeout)
        aklog_info('电脑停止抓包成功..')
        live_capture_thread = ''


def pcap_get_pc_capture(filter, decode_as=None):
    if not os.path.exists(return_pc_capture_file()):
        aklog_error('电脑抓包失败!')
        return False
    else:
        try:
            eventloop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(eventloop)
            cap = pyshark.FileCapture(return_pc_capture_file(), display_filter=filter, tshark_path=g_tshark_path,
                                      eventloop=eventloop,
                                      decode_as=decode_as)
            time.sleep(1)
            retlist = []
            for i in cap:
                retlist.append(i)
            try:
                cap.close()
            except:
                pass
            return retlist
        except:
            aklog_printf(traceback.format_exc())
            return []


@backup_pcap
def pcap_get_srcip_pcap(pcap, src_ip, protocol, decode_as=None, limit=None):
    retlist = []
    try:
        new_loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(new_loop)
        if src_ip:
            cap = pyshark.FileCapture(pcap, display_filter='ip.src=={} && ({})'.format(src_ip, protocol),
                                      tshark_path=g_tshark_path, decode_as=decode_as, eventloop=new_loop)
        else:
            cap = pyshark.FileCapture(pcap, display_filter='{}'.format(protocol),
                                      tshark_path=g_tshark_path, decode_as=decode_as, eventloop=new_loop)
        aklog_info('filter: {}'.format('ip.src=={} && ({})'.format(src_ip, protocol)))

        # cap.load_packets(timeout=60)
        time.sleep(1)
        _count = 0
        been_cut_state = False
        for i in cap:
            _count += 1
            if hasattr(i, '_ws.malformed'):
                if not been_cut_state:
                    been_cut_state = True
                    aklog_warn('抓包文件可能异常!!!   中间有出现被截断!!!')
            if not hasattr(i, 'icmp'):
                retlist.append(i)
            if limit and _count >= limit:
                break
        try:
            cap.close()
        except TSharkCrashException:
            aklog_error('解析pcap出现错误!!!')
            if 'bigger than' in traceback.format_exc():
                aklog_error('pcap文件可能出现damage报错')
        except:
            pass
        return retlist
    except TSharkCrashException:
        aklog_error('解析pcap出现错误!!!')
        if 'bigger than' in traceback.format_exc():
            aklog_error('pcap文件可能出现damage报错')
        try:
            cap.close()
        except:
            pass
        return retlist
    except:
        aklog_error('抓包未抓到指定条件报文: ip.src=={} && {}'.format(src_ip, protocol))
        aklog_printf(traceback.format_exc())
        try:
            cap.close()
        except:
            pass
        return []


@backup_pcap
def pcap_get_another_srcip_pcap(pcap, src_ip, protocol):
    print('ip.src!={} && {}'.format(src_ip, protocol))
    try:
        new_loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(new_loop)
        cap = pyshark.FileCapture(pcap, display_filter='ip.src!={} && {}'.format(src_ip, protocol),
                                  tshark_path=g_tshark_path, decode_as=None, eventloop=new_loop)
        # cap.load_packets(timeout=60)
        time.sleep(1)
        retlist = []
        for i in cap:
            retlist.append(i)
        try:
            cap.close()
        except:
            pass
        return retlist
    except:
        print(traceback.format_exc())
        try:
            cap.close()
        except:
            pass
        return []


def pcap_live_capture(interface=None, display_filter=None, packet_count=0, timeout=10, decode_as=None):
    """调试中"""
    network_adapter = cmd_get_network_adapter_name()
    new_loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(new_loop)
    cap = pyshark.LiveCapture(interface=interface, display_filter=display_filter,
                              decode_as=decode_as, tshark_path=g_tshark_path, debug=False,
                              output_file=r'D:\Users\Administrator\Desktop\live.pcap', eventloop=new_loop)
    # cap.load_packets()
    for packet in cap.sniff_continuously(packet_count=packet_count):
        print(packet.http)


# endregion

# region 1. sip抓包相关
def pcap_get_srcip_sip_pcap(pcap, src_ip=None):
    ret_list = []
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'sip')
    for i in cap:
        if not hasattr(i, 'icmp'):
            ret_list.append(i)
    if not ret_list:
        aklog_error('未抓包sip包!')
    return ret_list


@backup_pcap
# def get_first_invite_content(pcap, ip, port=5060, transport='UDP'):
def get_first_invite_content(pcap, ip, port=5060, transport=None):
    """
    返回传入的phone.pcap ==> 指定[发起方IP, 注册服务器端口号] 的第一个invite包
    """
    pcaps = rdpcap(pcap)
    if transport:
        for cap in pcaps:
            try:
                if str(cap[transport].dport) == str(port) and cap['IP'].src == ip:
                    if 'INVITE sip:' in cap['Raw'].load.decode(errors='ignore').split('\r\n')[0]:
                        return cap[transport].load.decode(errors='ignore')
                else:
                    continue
            except:
                continue
        return False
    else:
        for trans in ['UDP', 'TCP']:
            for cap in pcaps:
                try:
                    if str(cap[trans].dport) == str(port) and cap['IP'].src == ip:
                        if 'INVITE sip:' in cap['Raw'].load.decode(errors='ignore').split('\r\n')[0]:
                            return cap[trans].load.decode(errors='ignore')
                    else:
                        continue
                except:
                    continue
        return False


def get_first_invite_video_profile(pcap, ip, port=5060, transport='UDP'):
    r"""
    获取: 指定IP设备的主叫invite中的视频参数.
    返回字典如 :
        get_first_invite_video_profile(
        r'E:\automator_test\Python\AKautotest\testfile\Browser\Chrome_Download\R20K_V2\phone.pcap', '192.168.1.48')

       {'payload': '104',
        'codec': 'H264',
        'profile-level-id': '42e016',
        'max-br': '512'}
    """
    ret_dict = {}
    video_index = 0
    sip_content = get_first_invite_content(pcap, ip, port, transport)
    if not sip_content:
        aklog_warn('未抓包到指定sip invite包')
        return {}
    content_list = sip_content.split('\r\n')
    for content in content_list:
        if 'm=video' in content:
            video_index = content_list.index(content)
            break
    if video_index == 0:  # sdp没有视频codec信息
        return {}
        # return False
    for i in content_list[video_index:]:
        if 'a=rtpmap' in i:
            payload, codec = re.search(r'rtpmap:(\d*)? (.*)/', i).groups()
            if 'payload' not in ret_dict:
                ret_dict['payload'] = payload
            if 'codec' not in ret_dict:
                ret_dict['codec'] = codec
        elif 'profile-level-id=' in i:
            pld, br = re.search(r'profile-level-id=(.*?);.*max-br=(\d*)?;*', i).groups()
            ret_dict['profile-level-id'] = pld
            ret_dict['max-br'] = br
    return ret_dict


def pcap_get_h263_video_resolution(pcap, ip):
    """
    返回抓包的H263 codec分辨率:    QCIF, CIF, 4CIF, False
    """
    cap = pcap_get_srcip_pcap(pcap, ip, 'sip')
    for i in cap:
        if hasattr(i.sip, 'method') and i.sip.method == 'INVITE':
            media = str(i.sip.sdp_media_attr.fields)
            if 'H263' not in media:
                return False
            else:
                if '4CIF=1' in media:
                    ret = '4CIF'
                elif 'QCIF=1' in media and ' CIF=0' in media:
                    ret = 'QCIF'
                else:
                    ret = 'CIF'
                return ret


def pcap_get_sip_request_info(pcap, src_ip, method='INVITE', **kwargs):
    """
    获取SIP请求消息的所有信息
    kwargs: 其他过滤条件
    return:
        {
        "request_line": "INVITE sip:1005@192.168.10.28 SIP/2.0",
        "method": "INVITE",
        "r_uri": "sip:1005@192.168.10.28",
        "r_uri_user": "1005",
        "r_uri_host": "192.168.10.28",
        "resend": "0",
        "via": "SIP/2.0/UDP 192.168.10.154:5063;branch=z9hG4bK420842978",
        "via_transport": "UDP",
        "via_sent_by_address": "192.168.10.154",
        "via_sent_by_port": "5063",
        "via_branch": "z9hG4bK420842978",
        "from": "\"1004\" <sip:1004@192.168.10.28>;tag=1295517173",
        "display_info": "\"1004\"",
        "from_addr": "sip:1004@192.168.10.28",
        "from_user": "1004",
        "from_host": "192.168.10.28",
        "from_tag": "1295517173",
        "tag": "1295517173",
        "to": "<sip:1005@192.168.10.28>",
        "to_addr": "sip:1005@192.168.10.28",
        "to_user": "1005",
        "to_host": "192.168.10.28",
        "call_id": "136237150",
        "call_id_generated": "136237150",
        "cseq": "20 INVITE",
        "cseq_seq": "20",
        "cseq_method": "INVITE",
        "contact": "<sip:1004@192.168.10.154:5063>",
        "contact_uri": "sip:1004@192.168.10.154:5063",
        "contact_user": "1004",
        "contact_host": "192.168.10.154",
        "contact_port": "5063",
        "content_type": "application/sdp",
        "allow": "INVITE, INFO, PRACK, ACK, BYE, CANCEL, OPTIONS, NOTIFY, REGISTER, SUBSCRIBE, REFER, PUBLISH, UPDATE, MESSAGE",
        "max_forwards": "70",
        "user_agent": "Tiptel 3275 47.138.7.314 20110552cd14",
        "subject": "call invite",
        "supported": "replaces",
        "allow_events": "talk,hold,conference,refer,check-sync",
        "content_length": "307",
        "msg_body": "Message Body",
        "sdp_version": "0",
        "sdp_owner": "1004 5000 5000 IN IP4 192.168.10.154",
        "sdp_owner_username": "1004",
        "sdp_owner_sessionid": "5000",
        "sdp_owner_version": "5000",
        "sdp_owner_network_type": "IN",
        "sdp_owner_address_type": "IP4",
        "sdp_owner_address": "192.168.10.154",
        "sdp_session_name": "Talk",
        "sdp_connection_info": "IN IP4 192.168.10.154",
        "sdp_connection_info_network_type": "IN",
        "sdp_connection_info_address_type": "IP4",
        "sdp_connection_info_address": "192.168.10.154",
        "sdp_time": "0 0",
        "sdp_time_start": "0",
        "sdp_time_stop": "0",
        "sdp_media": "audio 11852 RTP/AVP 0 8 18 9 101",
        "sdp_media_media": "audio",
        "sdp_media_port_string": "11852",
        "sdp_media_port": "11852",
        "sdp_media_proto": "RTP/AVP",
        "sdp_media_format": "ITU-T G.711 PCMU",
        "sdp_media_attr": "ptime:20",
        "sdp_media_attribute_field": "ptime",
        "sdp_media_attribute_value": "20",
        "sdp_mime_type": "PCMU",
        "sdp_sample_rate": "8000",
        "sdp_fmtp_parameter": "annexb=no"
    }
    """
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    request_info = {}
    for i in cap:
        if getattr(i.sip, 'method', '') == method:
            flag = True
            for key in kwargs:
                key_info = getattr(i.sip, key, '')
                if key_info != kwargs[key]:
                    flag = False
                    break
            if not flag:
                continue
            sip_attr_list = i.sip.field_names
            for attr in sip_attr_list:
                if attr == 'msg_hdr':
                    continue
                attr_info = getattr(i.sip, attr)
                request_info[attr] = attr_info
            break
    return request_info


def pcap_get_sip_response_info(pcap, src_ip, status_code=200, cseq_method='INVITE', **kwargs):
    """
    获取SIP响应消息的所有信息
    kwargs: 其他过滤条件
    return:
        {
        "status_line": "SIP/2.0 200 OK",
        "status_code": "200",
        "resend": "0",
        "response_request": "6",
        "response_time": "5175",
        "via": "SIP/2.0/UDP 192.168.10.28:5060;branch=z9hG4bK7987b578;rport=5060",
        "via_transport": "UDP",
        "via_sent_by_address": "192.168.10.28",
        "via_sent_by_port": "5060",
        "via_branch": "z9hG4bK7987b578",
        "via_rport": "5060",
        "from": "\"1004\" <sip:1004@192.168.10.28>;tag=as2c1a1cda",
        "display_info": "\"1004\"",
        "from_addr": "sip:1004@192.168.10.28",
        "from_user": "1004",
        "from_host": "192.168.10.28",
        "from_tag": "as2c1a1cda",
        "tag": "as2c1a1cda",
        "to": "<sip:1005@192.168.10.183:5063>;tag=1416976005",
        "to_addr": "sip:1005@192.168.10.183:5063",
        "to_user": "1005",
        "to_host": "192.168.10.183",
        "to_port": "5063",
        "to_tag": "1416976005",
        "call_id": "3c08c5466456e1ae52060bf84fb55f25@192.168.10.28:5060",
        "call_id_generated": "3c08c5466456e1ae52060bf84fb55f25@192.168.10.28:5060",
        "cseq": "102 INVITE",
        "cseq_seq": "102",
        "cseq_method": "INVITE",
        "contact": "<sip:1005@192.168.10.183:5063>",
        "contact_uri": "sip:1005@192.168.10.183:5063",
        "contact_user": "1005",
        "contact_host": "192.168.10.183",
        "contact_port": "5063",
        "content_type": "application/sdp",
        "allow": "INVITE, INFO, PRACK, ACK, BYE, CANCEL, OPTIONS, NOTIFY, REGISTER, SUBSCRIBE, REFER, PUBLISH, UPDATE, MESSAGE",
        "user_agent": "akuvox VP-R47G 47.0.7.315 0C1105AD1345",
        "content_length": "212",
        "msg_body": "Message Body",
        "sdp_version": "0",
        "sdp_owner": "1005 5000 5000 IN IP4 192.168.10.183",
        "sdp_owner_username": "1005",
        "sdp_owner_sessionid": "5000",
        "sdp_owner_version": "5000",
        "sdp_owner_network_type": "IN",
        "sdp_owner_address_type": "IP4",
        "sdp_owner_address": "192.168.10.183",
        "sdp_session_name": "Talk",
        "sdp_connection_info": "IN IP4 192.168.10.183",
        "sdp_connection_info_network_type": "IN",
        "sdp_connection_info_address_type": "IP4",
        "sdp_connection_info_address": "192.168.10.183",
        "sdp_time": "0 0",
        "sdp_time_start": "0",
        "sdp_time_stop": "0",
        "sdp_media": "audio 11800 RTP/AVP 0 101",
        "sdp_media_media": "audio",
        "sdp_media_port_string": "11800",
        "sdp_media_port": "11800",
        "sdp_media_proto": "RTP/AVP",
        "sdp_media_format": "ITU-T G.711 PCMU",
        "sdp_media_attr": "ptime:20",
        "sdp_media_attribute_field": "ptime",
        "sdp_media_attribute_value": "20",
        "sdp_mime_type": "PCMU",
        "sdp_sample_rate": "8000",
        "sdp_fmtp_parameter": "0-16"
    }
    """
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    response_info = {}
    for i in cap:
        if getattr(i.sip, 'status_code', '') == str(status_code) \
                and getattr(i.sip, 'cseq_method', '') == cseq_method:
            flag = True
            for key in kwargs:
                key_info = getattr(i.sip, key, '')
                if key_info != kwargs[key]:
                    flag = False
                    break
            if not flag:
                continue
            sip_attr_list = i.sip.field_names
            for attr in sip_attr_list:
                if attr == 'msg_hdr':
                    continue
                attr_info = getattr(i.sip, attr)
                response_info[attr] = attr_info
            break
    return response_info


def pcap_get_rtp_port_from_sip(pcap, src_ip):
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    for i in cap:
        if hasattr(i.sip, 'method') and i.sip.method == 'INVITE':
            rtp_port = i.sip.sdp_media_port
            aklog_printf('rtp port: %s' % rtp_port)
            return rtp_port


@backup_pcap
def get_all_register_packet_timestamp(pcap, register_num):
    """
    获取指定username的所有register报文timestamp
    """
    ret_list = []
    pcaps = rdpcap(pcap)
    for cap in pcaps:
        try:
            content_list = cap['Raw'].load.decode(errors='ignore').split('\r\n')
            if 'REGISTER sip:' in content_list[0]:
                for i in content_list:
                    if 'Contact:' in i and '<sip:{}@'.format(register_num) in i:
                        # 如果时间靠太近, 是因为注册的鉴权重传, 就删除掉其中一个时间
                        new_time = float(cap.time)
                        if len(ret_list) > 0 and new_time - ret_list[-1] < 1.5:
                            ret_list[-1] = new_time
                        else:
                            ret_list.append(float(cap.time))
                        break
        except:
            continue
    return ret_list


def pcap_check_register_interval(pcap, register_num, interval):
    """检查指定账号的Register 报文发包间隔, 上下误差1.5"""
    time_stamp_list = get_all_register_packet_timestamp(pcap, register_num)
    # 如果只抓到两个包,  直接判断两个包在interval时间范围内. 要求设备抓包操作应该要在注册以后执行.
    if len(time_stamp_list) < 2:
        # 只抓到一个register包无法用于判断时间间隔
        return False
    else:
        for i in range(len(time_stamp_list) - 1):
            minus = time_stamp_list[i + 1] - time_stamp_list[i]
            if not interval - 1.5 < minus < interval + 1.5:
                return False
        return True


def pcap_get_sip_info_dtmf(pcap, src_ip):
    """
    获取DTMF Info类型信息
    :param pcap:
    :param src_ip:1
    :return: Content-Type， Message Body
    """
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    dtmf_info = []
    for i in cap:
        if hasattr(i.sip, 'method') and i.sip.method == 'INFO':
            content_type = i.sip.content_type
            info_data = i.sip.get('')
            dtmf_info.append({'content_type': content_type,
                              'info_data': info_data})
    aklog_printf(dtmf_info)
    return dtmf_info


def pcap_get_stun_pcap(pcap):
    """过滤stun报文"""
    return pcap_get_srcip_pcap(pcap, src_ip='', protocol='classicstun')


def pcap_get_stun_response_ip(pcap):
    ret = pcap_get_stun_pcap(pcap)
    if not ret:
        aklog_printf('没有stun报文')
        return False, False
    else:
        ip = ''
        port = ''
        for i in ret:
            # if i.classicstun.type == '0x00000101' and i.udp.dstport in ['5060', '5062', '5063']:  # 只过滤sip的nat
            #     return i.classicstun.att_ipv4, i.classicstun.att_port
            # elif i.classicstun.type == '0x00000101':
            #     return i.classicstun.att_ipv4, '5062'  # S567 没有用5062端口, 需要确认.
            if hasattr(i, 'classicstun') and i.classicstun.type == '0x00000101':
                # 有时候会比较慢, 10秒后回复另一个端口. 结合上注册也在10秒后, 就会出问题.
                ip = i.classicstun.att_ipv4
                port = i.classicstun.att_port
        if ip:
            return ip, port
        return False, False


def pcap_check_sip_nat(pcap, srcip, natip, natport):
    ret = pcap_get_srcip_sip_pcap(pcap, srcip)
    natport = str(natport)
    for i in ret:
        if hasattr(i.sip, 'request_line'):
            if (natip + ':' + natport not in i.sip.via) and ('@' + natip + ':' + natport not in i.sip.contact):
                aklog_error('NAT sip报文检查错误')
                aklog_printf(i.sip.via)
                aklog_printf(i.sip.contact)
                return False
    return True


def pcap_check_useragent(pcap, src_ip, agent):
    # 检查指定src ip的sip报文的user-agent
    # 如果传入的agent是'' , 即检查默认值的时候, 返回所有的agent 列表
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    if not cap:
        aklog_error('未抓到sip包')
        return False
    ret = []
    _count = 0
    if agent != '':
        for i in cap:
            _count += 1
            if i.sip.user_agent != agent:
                aklog_printf('get pcap useragent: %s' % i.sip.user_agent)
                return False
        if _count == 0:
            aklog_printf('未抓到sip包')
            return False
        return True
    else:
        for i in cap:
            _count += 1
            ret.append(i.sip.user_agent)
        if _count == 0:
            aklog_printf('未抓到sip包')
            return False
        return ret


def pcap_get_dnd_return_code(pcap, src_ip):
    """返回设备拒接来电的返回码:  486, 404, 603..."""
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    for i in cap:
        if hasattr(i.sip, 'status_code') and 'INVITE' in i.sip.cseq \
                and i.sip.status_code in ('480', '404', '603', '486'):
            return i.sip.status_code
    return False


def pcap_check_dnd_on_off_code(pcap, src_ip, code):
    """ 判断dnd oncode, off code是否正常发送, 特征码最好是*78 这样子的格式"""
    invite_list = []
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    for i in cap:
        if hasattr(i.sip, 'method') and i.sip.method == 'INVITE':
            invite_list.append(re.search(r'sip:(.*)@', i.sip.request_line).group(1))
    return code in invite_list


def pcap_get_all_invite_num(pcap, src_ip, filter_same=True):
    """返回所有invite包的号码: 测试群呼号码列表"""
    invite_list = []
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    if filter_same:
        for i in cap:
            if hasattr(i.sip, 'method') and i.sip.method == 'INVITE':
                invite_list.append(re.search(r'sip:(.*)@', i.sip.request_line).group(1))
        return list(set(invite_list))
    else:
        # 相同呼叫号码不过滤, 用于测试invite个数. (其中重传的要根据callid去掉):
        callidlist = []
        for i in cap:
            if hasattr(i.sip, 'method') and i.sip.method == 'INVITE':
                if i.sip.call_id not in callidlist:
                    invite_list.append(re.search(r'sip:(.*)@', i.sip.request_line).group(1))
                    callidlist.append(i.sip.call_id)
        return invite_list


def pcap_get_sip_all_invite_number(pcap, src_ip):
    """拿出所有的invite包号码. (不带服务器地址)"""
    invite_list = []
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    for i in cap:
        if hasattr(i.sip, 'method') and i.sip.method == 'INVITE':
            ret = re.search(r'sip:(.*)@', i.sip.request_line).group(1)
            if ret not in invite_list:
                invite_list.append(ret)
    return invite_list


def pcap_get_sip_all_invite_number_and_from_user(pcap, src_ip):
    """
    返回列表: [['1001', '1002'],['1001', '1000']].  测试呼出号码+from user的检查
    """
    invite_list = []
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    for i in cap:
        if hasattr(i.sip, 'method') and i.sip.method == 'INVITE':
            to_num = re.search(r'sip:(.*)@', i.sip.request_line).group(1)
            from_num = i.sip.from_user
            if [to_num, from_num] not in invite_list:
                invite_list.append([to_num, from_num])
    return invite_list


def pcap_check_sip_to_user_name(pcap, src_ip, to_user):
    """ 判断dnd oncode, off code是否正常发送, 特征码最好是*78 这样子的格式"""
    aklog_printf('pcap_check_sip_to_user_name: %s' % to_user)
    invite_list = []
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    for i in cap:
        if hasattr(i.sip, 'method') and i.sip.method == 'INVITE':
            invite_list.append(re.search(r'sip:(.*)@', i.sip.request_line).group(1))
    return to_user in invite_list


def pcap_check_local_sip_port(pcap, src_ip, min_port, max_port):
    """ 判断设备 local sip port 功能"""
    src_list = []
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    for i in cap:
        if hasattr(i, 'udp'):
            src_list.append(i.udp.srcport)
    if len(src_list) == 0:
        return False  # 没有抓到sip包
    for port in src_list:
        if int(port) not in range(min_port, max_port + 1):
            return False
    return True


def pcap_check_direct_ip_port(pcap, src_ip, check_port):
    """ 判断设备 direct ip port 功能"""
    src_list = []
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    for i in cap:
        src_list.append(i.udp.srcport)
    if len(src_list) == 0:
        return False  # 没有抓到sip包
    for port in src_list:
        if port == check_port:
            return True
    else:
        return False


def pcap_check_sip_transport(pcap, src_ip, transport):
    """
    判断sip报文的 transport type
    参数： transport: UDP, TCP.   无法支持TLS.
    """
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    if not cap:
        aklog_error('未抓到sip包')
        return False
    for i in cap:
        try:
            if transport.lower() != i.transport_layer.lower():
                return False
        except:
            # 没有sip包
            return False
    return True


def pcap_check_sip_call_id_with_host(pcap, src_ip):
    """
    判断SIP报文的Call-ID是否包含host
    :param pcap:
    :param src_ip:
    :return:
    """
    aklog_printf('pcap_check_sip_call_id_with_host')
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    for i in cap:
        try:
            if hasattr(i.sip, 'call_id') and src_ip in i.sip.call_id:
                return True
        except:
            # 没有sip包
            return False


def pcap_check_sip_call_id(pcap, src_ip):
    """
    检查所有sip请求中的callid包含室内机的ip地址
    """
    aklog_printf('pcap_check_sip_call_id')
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    if not cap:
        aklog_error('未抓到sip包')
        return False
    for i in cap:
        if hasattr(i.sip, 'request_line'):
            if src_ip not in i.sip.call_id:
                return False
    return True


def pcap_check_is_exist_rport(pcap_file, src_ip):
    """检测sip包中是否存在rport字段"""
    # aklog_printf('pcap_check_is_exist_rport, src_ip: %s' % src_ip)
    # cap = pcap_get_srcip_sip_pcap(pcap_file, src_ip)
    # for i in cap:
    #     if hasattr(i.sip, 'method') and i.sip.method == 'REGISTER' and 'rport;' in i.sip.via:
    #         return True
    # return False
    aklog_printf('pcap_check_is_exist_rport, src_ip: %s' % src_ip)
    cap = pcap_get_srcip_sip_pcap(pcap_file, src_ip)
    if not cap:
        aklog_printf('抓包中没有sip报文')
        return False
    for i in cap:
        if hasattr(i, 'sip') and 'rport;' in i.sip.via:
            return True
    return False


def pcap_get_udp_keep_alive_interval_list(pcap, src_ip, src_port):
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'udp.port == {}'.format(src_port))

    interval_list = []
    for i in cap:
        if not hasattr(i, 'sip'):
            interval_list.append(float(i.sniff_timestamp))
        else:
            interval_list.append('sip:' + str(float(i.sniff_timestamp)))
    aklog_printf('UDP keep alive: %s' % interval_list)
    # 如果都是sip报文, 不是udp keepalive报文, 则返回[], 用于检查udp keep alive关闭
    if not interval_list:
        return []
    udplist = [i for i in interval_list if 'sip' not in str(i)]
    if not udplist:
        return []
    return interval_list


def pcap_check_outbound(pcap, src_ip, sipserver, outbound, outbound2=None):
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    if not cap:
        return False
    else:
        if not outbound2:
            for i in cap:
                if i.ip.dst != outbound:
                    aklog_printf('destination没有发送outbound服务器')
                    aklog_printf(i.ip.dst)
                    return False
                if hasattr(i.sip, 'request_line') and i.sip.r_uri != 'sip:' + sipserver:
                    if '@' + sipserver not in i.sip.r_uri:
                        aklog_printf('sip报文中sipserver显示错误')
                        aklog_printf(i.sip.r_uri)
                        return False
            return True
        else:
            # 检查填写outbound2以后的主备切换, 尽量需要抓包时长>50秒
            outboundlist = []
            for i in cap:
                if hasattr(i.sip, 'request_line') and i.sip.r_uri != 'sip:' + sipserver:
                    if '@' + sipserver not in i.sip.r_uri:
                        aklog_printf('sip报文中sipserver显示错误')
                        aklog_printf(i.sip.r_uri)
                        return False
                outboundlist.append(i.ip.dst)
            if outbound not in outboundlist and outbound != outboundlist[0]:
                return False
            if outbound2 != outboundlist[-1]:
                return False
            return True


def pcap_check_udp_keep_alive_interval(pcap, src_ip, src_port=5060, interval=5, delta=3, slice=None):
    """
    检查udp keep alive 发包时间间隔
    """
    interval = int(interval)
    interval_list = pcap_get_udp_keep_alive_interval_list(pcap, src_ip, src_port)
    if not interval_list:
        aklog_printf('没有抓到 UDP Keep alive包')
        return False
    else:
        if slice:
            if len(interval_list) >= slice:
                interval_list = interval_list[len(interval_list) - slice:]
        for j in range(len(interval_list) - 1):
            # 部分机型: 如果发包间隔中出现sip包, 会影响发包间隔.
            if type(interval_list[j + 1]) == str or type(interval_list[j]) == str:
                intj1 = interval_list[j + 1] if type(interval_list[j + 1]) != str else float(
                    interval_list[j + 1].split(':')[1])
                intj = interval_list[j] if type(interval_list[j]) != str else float(
                    interval_list[j].split(':')[1])
                interval1 = intj1 - intj
                if interval1 < interval + delta:
                    continue
                else:
                    aklog_printf('发包间隔时间 %s 不正确' % interval1)
                    return False
            else:
                interval1 = interval_list[j + 1] - interval_list[j]
                if (interval - delta) <= interval1 <= (interval + delta):
                    continue
                else:
                    aklog_printf('发包间隔时间 %s 不正确' % interval1)
                    return False
        return True


def pcap_check_register_domain(pcap, src_ip, domain):
    # 存在register包发往指定域名地址
    ret = pcap_get_srcip_sip_pcap(pcap, src_ip)
    for i in ret:
        if hasattr(i.sip, 'r_uri'):
            if 'sip:' + domain == i.sip.r_uri:
                return True
    return False


def pcap_check_all_invite_dst_and_line(pcap, src_ip, dst1, line1, dst2=None, line2=None):
    """
    检查所有的invite报文的 destination和 request-line, 用于测试主备服务器invite
    """
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    invite_list = []
    for i in cap:
        if hasattr(i.sip, 'method') and i.sip.method == 'INVITE':
            invite_list.append(i)
    if not dst2:
        for j in invite_list:
            if j.ip.dst != dst1 or j.sip.r_uri != 'sip:' + line1:
                aklog_printf('invite 内容错误: ')
                aklog_printf(j.ip.dst)
                aklog_printf(j.sip.r_uri)
                return False
        return True
    else:
        for j in invite_list:
            if (j.ip.dst not in [dst1, dst2]) or (j.sip.r_uri not in ['sip:' + line1, 'sip:' + line2]):
                aklog_printf('invite 内容错误: ')
                aklog_printf(j.ip.dst)
                aklog_printf(j.sip.r_uri)
                return False
        return True


def pcap_check_all_register_dst_and_line(pcap, src_ip, dst1, line1, dst2=None, line2=None):
    """
    检查所有的Register报文的 destination和 request-line, 用于测试主备服务器invite
    """
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    reg_list = []
    for i in cap:
        if hasattr(i.sip, 'method') and i.sip.method == 'REGISTER':
            reg_list.append(i)
    if not dst2:
        for j in reg_list:
            if j.ip.dst != dst1 or j.sip.r_uri != 'sip:' + line1:
                aklog_printf('Register 内容错误: ')
                aklog_printf(j.ip.dst)
                aklog_printf(j.sip.r_uri)
                return False
        return True
    else:
        for j in reg_list:
            if (j.ip.dst not in [dst1, dst2]) or (j.sip.r_uri not in ['sip:' + line1, '`sip`:' + line2]):
                aklog_printf('Register 内容错误: ')
                aklog_printf(j.ip.dst)
                aklog_printf(j.sip.r_uri)
                return False
        return True


def pcap_check_sip_forward(pcap, src_ip):
    """
    检测设备发送302 转接, 和转接号码,
    返回:
        True, 1002@192.168.30.213
        False, False
    """
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    if not cap:
        return [False, False]
    for i in cap:
        if hasattr(i.sip, 'status_code') and i.sip.status_code == '302':
            return [True, i.sip.contact_uri.split(':')[1]]

    aklog_error('未抓到302转接包')
    return [False, False]


def pcap_check_sip_message(pcap, src_ip, filter_by_callid=True):
    """用于测试触发alarm事件会发送SIP Message"""
    # filter_by_callid: 去掉3cx 请求慢导致的重传影响
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    ret_list = []
    callidlist = []
    for i in cap:
        if hasattr(i.sip, 'method') and i.sip.method == 'MESSAGE':
            if filter_by_callid:
                if i.sip.call_id not in callidlist:
                    callidlist.append(i.sip.call_id)
                    list1 = []
                    list1.append(i.sip.to_user)
                    list1.append(getattr(i.sip, '').split("\\")[0])
                    ret_list.append(list1)
            else:
                list1 = []
                list1.append(i.sip.to_user)
                list1.append(getattr(i.sip, '').split("\\")[0])
                ret_list.append(list1)
    return ret_list


def pcap_check_video_transport_type(pcap, src_ip, checktype='sendrecv'):
    """
    2024.8.22 E门禁检查video transport type功能
    checktype: sendonly, recvonly, inactive, sendrecv
    """
    aklog_info()
    cap = pcap_get_srcip_sip_pcap(pcap, src_ip)
    if not cap:
        return False
    for i in cap:
        if i.sip.method == 'INVITE':
            fileds = i.sip.sdp_media_attr.fields
            return checktype == fileds[-1].showname_value
    return False


# endregion

# region 2. RTP抓包相关
def pcap_get_srcip_audio_rtp_pcap(pcap, src_ip, limit=None, decode_as=None):
    _count = 0
    ret_list = []
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'rtp && !h264', decode_as)
    for i in cap:
        _count += 1
        if limit and _count == limit:
            return ret_list
        if not hasattr(i, 'h264') and not hasattr(i, 'icmp'):
            # 2025.3.21 lex: 过滤预览包
            if i.udp.srcport in [60000, '60000'] or i.udp.dstport in [60000, '60000']:
                pass
            else:
                ret_list.append(i)
    aklog_printf('抓包rtp包 %s 个' % (len(ret_list)))
    if not ret_list:
        aklog_error('未抓到rtp包')
    return ret_list


def pcap_get_another_srcip_audio_rtp_pcap(pcap, src_ip, limit=None, remove_rtsp=True):
    _count = 0
    ret_list = []
    cap = pcap_get_another_srcip_pcap(pcap, src_ip, '(rtp && !h264)')
    for i in cap:
        if limit and _count == limit:
            return ret_list
        if remove_rtsp:
            if hasattr(i, 'udp') and int(i.udp.port) != 60000:
                if not hasattr(i, 'h264') and not hasattr(i, 'icmp'):
                    _count += 1
                    ret_list.append(i)
        else:
            if not hasattr(i, 'h264') and not hasattr(i, 'icmp'):
                _count += 1
                ret_list.append(i)
    aklog_printf('抓包rtp包 %s 个' % (len(ret_list)))
    return ret_list


@backup_pcap
def pcap_get_srcip_rtcp_pcap(pcap, src_ip):
    """获取rtcp包"""
    return pcap_get_srcip_pcap(pcap, src_ip, 'rtcp')


def pcap_get_audio_rtp_payload_type(pcap, src_ip, limit=None):
    rtp_cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip, limit=limit)
    payload_types = []
    for i in rtp_cap:
        i.rtp.pretty_print()
        print(i.rtp.field_names)
        if hasattr(i.rtp, 'p_type'):
            payload_type = i.rtp.p_type
            if payload_type not in payload_types:
                payload_types.append(payload_type)
    return payload_types


def pcap_check_dst_rtp_via_ip(pcap, src_ip, dst_ip):
    """
    检测云的rtp是通过IP方式: 所有设备在同一个网络上
    """
    aklog_printf('pcap_check_dst_rtp_via_ip, src_ip: %s, dst_ip: %s' % (src_ip, dst_ip))
    cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip, limit=3000)
    for i in cap:
        if i.ip.dst != dst_ip:
            return False
    return True


def pcap_check_dst_rtp_via_sip(pcap, src_ip, dst_ip):
    """
    检测云的RTP是通过SIP账号: 所有设备在不同网络上.
    """
    aklog_printf('pcap_check_dst_rtp_via_sip, src_ip: %s, dst_ip: %s' % (src_ip, dst_ip))
    cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip, limit=3000)
    for i in cap:
        if i.ip.dst == dst_ip:
            return False
    return True


def pcap_check_zrtp_in_pcap(pcap, src_ip):
    """
    检查抓包中有ZRTP的协商.
    """
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'zrtp')
    if cap:
        return True
    return False


def pcap_check_srtp_in_pcap(pcap, src_ip, percent=0.95):
    """
    指定包中， 指定源IP 有发送SRTP报文
    eg: 检测主测机发出的rtp是否是srtp报文
        pcap_check_strp_in_pcap(r'C:\\Users\\user\\Downloads\\phone.pcap', '192.168.1.111')
    返回: True, False
    """
    rtp_list = []
    srtp_list = []
    audio_cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip, limit=2000)  # # 如果报文操作很多费时, 只截取前2000个
    for i in audio_cap:
        rtp_list.append(i)
        if 'SRTP Auth Tag' in i.rtp.__str__():
            srtp_list.append(i)
    print('音频RTP数量: %s' % str(len(rtp_list)))
    print('音频SRTP数量: %s' % str(len(srtp_list)))
    if len(rtp_list) < 30:
        # 基本没有抓到几个包的直接出错了.  一秒钟有50个包. 没抓包2秒以上直接报错.
        # return False
        return 'Error'  # False ==> Error, 出现抓包数为0, 但需要判断为非SRTP的情况.
    return len(srtp_list) / len(rtp_list) > percent


def pcap_check_rtp_in_pcap(pcap, src_ip, pt_integer):
    """
    指定包中， 指定源IP和音频codec 有发送RTP报文
    eg: 检测主测机发出的rtp是否有包含audio_codec对应PT的报文
        pcap_check_trp_in_pcap(r'C:\\Users\\user\\Downloads\\phone.pcap', '192.168.1.111', '9')
    返回: True, False
    """
    audio_cap = pcap_get_srcip_pcap(pcap, src_ip, 'rtp && rtp.p_type == {}'.format(pt_integer))
    for i in audio_cap:
        try:
            if not hasattr(i, 'h264'):
                # 过滤rtp但不包含h264
                if i.rtp.p_type == pt_integer:
                    return True
        except:
            pass
    return False


def pcap_get_rtp_payload_length(pcap, src_ip):
    """
    获取RTP包或SRTP包的payload的长度，
    有些RTP包被加密了，但抓包仍显示为RTP，通过获取payload的长度来判断，
    SRTP包为senc_payload + sauth_tag两部分之和
    """
    audio_cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip, limit=100)  # # 如果报文操作很多费时, 只截取前2000个
    # 获取第100个包的payload长度
    if audio_cap:
        cap = audio_cap[-1]
        if hasattr(cap.rtp, 'sauth_tag'):
            enc_payload = cap.rtp.senc_payload.replace(':', '')
            auth_tag = cap.rtp.sauth_tag.replace(':', '')
            payload_length = len(enc_payload) + len(auth_tag)
        else:
            payload = cap.rtp.payload.replace(':', '')
            payload_length = len(payload)
    else:
        payload_length = None
    return payload_length


def pcap_check_rtpevent_in_pcap(pcap, src_ip=''):
    if src_ip:
        cap = pcap_get_srcip_pcap(pcap, src_ip, 'rtpevent')
    else:
        cap = pcap_get_srcip_pcap(pcap, '', 'rtpevent')
    dtmf = []
    payload = []
    continuous_state = False
    for i in cap:
        try:
            if i.rtpevent.end_of_event == '1':
                if not continuous_state:
                    dtmf.append(i.rtpevent.event_id)
                    payload.append(i.rtp.p_type)
                    continuous_state = True
            else:
                continuous_state = False
        except:
            pass
    return dtmf, payload


def pcap_check_localrtp(pcap, src_ip, min_port, max_port):
    """音频通话: 指定src ip的 rtp报文的UDP源端口在范围内"""
    cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip)
    udplist = []
    for i in cap:
        if int(i.udp.srcport) == 60000:
            # 视频预览
            pass
        else:
            udplist.append(int(i.udp.srcport) in range(int(min_port), int(max_port) + 1))
    return all(udplist)


def pcap_check_rtp_confusion(pcap, src_ip, decode_as=None):
    # 检查rtp混淆功能
    # 新的wireshark上显示为DTLS, 用该接口仍有效.
    cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip, limit=1000, decode_as=decode_as)
    if not cap:
        aklog_printf('没有rtp包')
        return False
    cap = cap[50:]  # 有时候刚开始的几个包还是会显示
    count = 0
    for i in cap:
        if hasattr(i.rtp, "payload"):
            # 会有个别包还是会显示，计算总数量
            count += 1
            if count >= 10:
                return False
    return True


def pcap_check_rtp_confusion_with_decode(pcap, src_ip):
    """
    检查rtp混淆功能，有些情况下抓包无法自动解析为RTP包，需要decode_as，需要从SIP信令获取RTP端口信息，因此只能用于UDP和TCP两种方式，TLS不行
    返回True表示混淆成功，False表示没有混淆
    """
    rtp_port = pcap_get_rtp_port_from_sip(pcap, src_ip)
    time.sleep(3)
    cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip, limit=1000, decode_as={'udp.port==%s' % rtp_port: 'rtp'})
    if not cap:
        aklog_printf('没有rtp包')
        return None
    for i in cap:
        if hasattr(i.rtp, "payload"):
            return False
    return True


def pcap_get_rtcp_port_list(pcap, src_ip, limit=None):
    """获取包中的rtcp端口"""
    cap = pcap_get_srcip_rtcp_pcap(pcap, src_ip)
    src_rtcp_port_list = []
    _count = 0
    for i in cap:
        if limit and _count == limit:
            return src_rtcp_port_list
        _count += 1
        src_rtcp_port_list.append(int(i.udp.srcport))
    return src_rtcp_port_list


def pcap_get_rtp_port_list(pcap, src_ip):
    """获取包中的rtp端口"""
    cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip)
    src_rtp_port_list = []
    for i in cap:
        src_rtp_port_list.append(int(i.udp.srcport))
    return src_rtp_port_list


def pcap_get_payload_rate(pcap, src_ip, remove_rtsp=True, cut_percent=0, is_check_remote=False):
    """
    cur_percent: 0~1.0
    is_check_remote ： True: 检查对向IP
    """
    aklog_info('抓包检查通话声音中...')
    aklog_info()
    if is_check_remote:
        cap = pcap_get_another_srcip_audio_rtp_pcap(pcap, src_ip, limit=3000)
    else:
        cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip, limit=3000)
    payload_str = ''
    for i in cap:
        if remove_rtsp:
            if hasattr(i, 'udp') and int(i.udp.port) != 60000:
                try:
                    payload_str = payload_str + i.rtp.payload + ':'
                except:
                    # 抓包出现unknwon rtp version 3
                    pass
        else:
            try:
                payload_str = payload_str + i.rtp.payload + ':'
            except:
                # 抓包出现unknwon rtp version 3
                pass
    if not payload_str:
        aklog_error('未抓到rtp')
        return 0
    else:
        payload_str = payload_str.strip(':')
    payload_str = payload_str.replace(':fe', ":ff").replace(':fd', ":ff").replace('fe:', "ff:").replace('fd:',
                                                                                                        "ff:").replace(
        ':7e', ":7d").replace('7e:', "7d:")  # fe=>ff
    payload_str = payload_str.replace(':55', ':d5').replace('55:', 'd5:')
    payload_list = payload_str.split(':')
    payload_list = payload_list[int(len(payload_list) * cut_percent):]
    all_payload_length = len(payload_list)
    all_payload_type = list(set(payload_list))
    all_payload_type = [i for i in all_payload_type if i]
    payload_dict = {}
    for i in all_payload_type:
        payload_dict[payload_list.count(i)] = i
    maxnum = max(list(payload_dict.keys()))
    aklog_info(
        f'payload字节数: {all_payload_length} - 最大payload字节数: {maxnum} - 最大payload字节占比: {maxnum / all_payload_length} - 对应payload: {payload_dict.get(maxnum)}')
    return maxnum / all_payload_length


def pcap_check_audio_rtp_codec(pcap, src_ip, codec):
    """
    :param codec: PCMA, PCMU, G722, G729
    :return:
    """
    codecdict = {
        'PCMU': '0',
        'PCMA': '8',
        'G722': '9',
        'G729': '18'
    }
    cap = pcap_get_srcip_audio_rtp_pcap(pcap, src_ip)
    if not cap:
        return False
    for i in cap:
        if i.rtp.p_type != codecdict.get(codec):
            aklog_warn(f'抓包检查rtp: {codec}, 抓包中有其他codec出现')
            print(i.rtp.p_type)
            return False
    return True


# endregion

# region 3. HTTP抓包相关
@backup_pcap
def pcap_get_srcip_http_pcap(pcap, src_ip):
    ret_list = []
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'http && tcp.port !=5654 && tcp.port != 5555')
    time.sleep(1)
    for i in cap:
        if not hasattr(i, 'icmp') and hasattr(i, 'http'):
            ret_list.append(i)
    aklog_printf('抓包http: %s 个' % (len(ret_list)))
    return ret_list


def pcap_get_action_url(pcap, src_ip, checklist: list, count=None):
    """
    要求配置的action url路径中要带有 help.xml
    ret_str = http://192.168.1.80/help.xml?mac=$mac:ip=$ip:model=$model:firmware=$firmware:
    active_url=$active_url:active_user=$active_user:callnumber=$remote:
    eg:
        pcap_get_action_url(pcap, ip, [['mac', '112233445566'],['model', 'R20']]
    """
    _count = 0
    cap = pcap_get_srcip_http_pcap(pcap, src_ip)
    ret_str = None
    ext = ''
    print('get_cap:%s ' % len(cap))
    for i in cap:
        try:
            if 'help.xml' in i.http.request_full_uri:
                if not i.http.request_version.startswith('HTTP'):
                    # X915model存在空格，wireshark解析的时候url空格后的会被当做version，手动进行拼接
                    ext = ' ' + ' '.join(i.http.request_version.split(' ')[:-1])
                if count:
                    # 指定第几个action url报文. count从1开始
                    _count += 1
                    if _count == count:
                        ret_str = i.http.request_full_uri + ext
                        break
                else:
                    ret_str = i.http.request_full_uri + ext
                    break
        except:
            pass
    if not ret_str:
        aklog_error('抓包中没有action URL内容')
        return False
    ret_str = ret_str + ':'
    for i in checklist:
        if i[0] == 'mac':
            if i[0] + '=' + i[1].replace(':', '') not in ret_str.replace(':', ''):
                aklog_error('Error: %s' % ret_str)
                aklog_error('check failed in %s' % i[0])
                return False
        else:
            if i[0] + '=' + i[1] not in ret_str:
                aklog_error('Error: %s' % ret_str)
                aklog_error('check failed in %s' % i[0])
                return False
    return True


def pcap_get_post_action_url(pcap, src_ip, index=None):
    """
    post方式的action url. 格式如:
    http://192.168.3.213/api/config/set/{"data":{"mac":"$mac", "ip":"$ip", "model":"$model", "firmware":"$firmware", "relay3status":"$relay3status"}}
    """
    cap = pcap_get_srcip_http_pcap(pcap, src_ip)
    _count = 0
    for i in cap:
        if hasattr(i, 'http') and hasattr(i.http, 'request_full_uri') and 'api/config/set' in i.http.request_full_uri:
            _count += 1
            if index:
                if _count == index:
                    return i.http.file_data
            else:
                return i.http.file_data
    return '{}'


def pcap_get_http_url(pcap, src_ip):
    """获取包中的http URL信息"""
    ret = pcap_get_srcip_http_pcap(pcap, src_ip)
    http_url = []
    for i in ret:
        if hasattr(i.http, 'request_full_uri'):
            url = i.http.request_full_uri
            http_url.append(url.replace(':8000', '').replace(':8001', '').replace(':80', ''))
    if http_url and len(http_url) < 100:
        aklog_debug('http 抓包如下: ')
        aklog_debug(str(http_url))
    return http_url


def pcap_return_http_auth_type(pcap, src_ip):
    """检测http的鉴权方式"""
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'http')
    for i in cap:
        if hasattr(i, 'http') and hasattr(i.http, 'authorization'):
            return i.http.authorization.split(' ')[0]
    return False


def pcap_return_http_json_data(pcap, src_ip):
    """获取http url中携带的json数据"""
    ret = pcap_get_srcip_http_pcap(pcap, src_ip)
    json_dict = {}
    for i in ret:
        if hasattr(i.http, 'content_type') and 'application/json' in i.http.content_type.lower():
            if hasattr(i.http, 'file_data'):
                json_data = i.http.file_data
            elif hasattr(i.http, 'response_body'):
                json_data = i.http.response_body
            else:
                continue
            try:
                json_data = re.sub(r'\\x[a-f0-9]', '', json_data)
                json_dict = json.loads(json_data)
                break
            except:
                continue
    return json_dict


def pcap_check_web_relay(pcap, src_ip, url, username, password):
    ret = pcap_get_srcip_http_pcap(pcap, src_ip)
    for i in ret:
        if hasattr(i.http, 'request_full_uri'):
            if i.http.request_full_uri == url or i.http.request_full_uri.replace(':80', '') == url:
                if hasattr(i.http, 'authbasic') and password:
                    aklog_printf('webrelay鉴权信息:' + i.http.authbasic)
                    return i.http.authbasic == (username + ':' + password)
                else:
                    return True
    aklog_printf('no web relay triggerd')
    return False


def pcap_check_ec32(pcap, src_ip, ec32_ip, username, password):
    """
    返回： All, 或者['1','3','5'].. 或者False
    """
    ret = pcap_get_srcip_http_pcap(pcap, src_ip)
    urllist = []
    for i in ret:
        if hasattr(i.http, 'request_full_uri'):
            if 'cdor.cgi?open' in i.http.request_full_uri:
                if 'cdor.cgi?open=9'.format(ec32_ip) in i.http.request_full_uri:
                    # 排除close all的请求
                    continue
                if password:
                    if i.http.authbasic != (username + ':' + password):
                        aklog_error('检测EC32的密码错误')
                        return False
                    else:
                        urllist.append(i.http.request_full_uri)
                else:
                    urllist.append(i.http.request_full_uri)
    if not urllist:
        aklog_printf('no ec32 triggerd')
        return []
    else:
        result = []
        for url in urllist:
            if 'http://{}/cdor.cgi?open=8'.format(ec32_ip) in urllist:
                return 'All'
            else:
                if ec32_ip in url:
                    result.append(url.split('door=')[1])
        return sorted(list(set(result)))


# endregion

# region 4. 其他
# region 4.1 syslog

def pcap_get_srcip_syslog_pcap(pcap, src_ip):
    ret_list = []
    _count = 0
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'syslog')
    for i in cap:
        if not hasattr(i, 'icmp'):
            _count += 1
            ret_list.append(i)
            if _count == 500:  # slice with amount 500
                return ret_list
    return ret_list


def pcap_check_syslog_level(pcap, src_ip, level):
    """测试log等级"""
    cap = pcap_get_srcip_syslog_pcap(pcap, src_ip)
    if len(cap) < 2:
        return False
    levellist = []
    for i in cap:
        levellist.append(i.syslog.get_field('level'))
    for j in levellist:
        # R20T30 log 等级功能不生效.
        if j > level:
            aklog_error('remote syslog log等级检查失败')
            return False
    return True


def pcap_check_send_syslog_server(pcap, src_ip):
    """测试send to syslog server"""
    cap = pcap_get_srcip_syslog_pcap(pcap, src_ip)
    return len(cap) > 10


# endregion

# region 4.2 dns
def pcap_get_srcip_dns_pcap(pcap, src_ip, domain):
    ret_list = []
    ret = pcap_get_srcip_pcap(pcap, src_ip, 'dns')
    for i in ret:
        if not hasattr(i, 'icmp') and domain in i.dns.qry_name:
            ret_list.append(i)
    return ret_list


def pcap_check_dns_srv(pcap, src_ip, domain):
    """
    检测baidu.com的dns-srv查询
    """
    ret = pcap_get_srcip_dns_pcap(pcap, src_ip, domain)

    if not ret:
        return False
    else:
        qry_name_list = []
        type_list = []
        for i in ret:
            qry_name_list.append(i.dns.qry_name)
            type_list.append(i.dns.qry_type)
        if domain not in qry_name_list:  # 没有dns记录
            return False
        for ii in ['35', '33', '1']:
            if ii not in type_list:
                aklog_printf('未进行完整的NAPTR查询.  35:naptr, 33:srv, 1:A')
                return False
        for j in ['_sip._udp.' + domain, '_sip._tcp.' + domain, '_sips._udp.' + domain, '_sips._tcp.' + domain]:
            if j not in qry_name_list:
                aklog_printf('未进行srv查询')
                return False
        # 检测有naptr, srv, a查询. 且域名正确.
        for k in ret:
            if k.dns.qry_type == '35':
                naptr_index = ret.index(k)
                if k.dns.qry_name != domain:
                    aklog_printf('NAPTR查询地址错误. 抓包: %s' % (k.dns.qry_name))
                    return False
            if k.dns.qry_type == '33':
                srv_index = ret.index(k)
                if srv_index < naptr_index:
                    aklog_printf('SRV查询顺序应该晚于NAPTR')
                    return False
                if k.dns.qry_name not in ['_sip._udp.' + domain, '_sip._tcp.' + domain, '_sips._udp.' + domain,
                                          '_sips._tcp.' + domain]:
                    aklog_printf('SRV查询地址错误. 抓包: %s' % (k.dns.qry_name))
            elif k.dns.qry_type == '1':
                a_index = ret.index(k)
                if a_index < srv_index:
                    aklog_printf('SRV查询顺序应该晚于NAPTR')
                    return False
                if k.dns.qry_name != domain:
                    aklog_printf('A查询地址错误. 抓包: %s' % (k.dns.qry_name))
                    return False
        return True


# endregion

# region 4.3 RTSP

def pcap_return_rtsp_auth_type(pcap, src_ip):
    """
    检测rtsp流的加密类型.   None, Basic, Digest
    """
    ret = ''
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'rtsp')
    for i in cap:
        if hasattr(i, 'rtsp') and hasattr(i.rtsp, 'status') and i.rtsp.status == '401':
            ret = i.rtsp.__str__()
            aklog_info(ret)
            break
    if ret:
        return re.search(r'WWW-Authenticate:.*(Basic|Digest)', ret).group(1)
    return ret


def pcap_return_mjpeg_auth_type(pcap, src_ip):
    """检测mjpeg的鉴权方式"""
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'http')
    for i in cap:
        if hasattr(i, 'http') and hasattr(i.http, 'authorization'):
            return i.http.authorization.split(' ')[0]
    return False


def pcap_get_rtsp_payload(pcap, src_ip, isremote=False):
    """
    isremote:
        False: ip.src==src_ip
        True: ip.dst ==src_ip   抓云端ip发送过来的rtsp报文

    通过payload判断是否有音频
    门口机：
        PCMU： 0
        L16： 97
        H264： 96
        H265： 98
        Mjpeg: 26
    """
    if not isremote:
        cap = pcap_get_srcip_pcap(pcap, src_ip, '(udp.port==60000 || udp.port == 60002)')
    else:
        # 云端走sip发过来的rtsp, 端口不是60000了.
        cap = pcap_get_another_srcip_audio_rtp_pcap(pcap, src_ip, limit=3000)
    retdict = {}
    for i in cap:
        if hasattr(i, 'rtp'):
            if i.rtp.p_type not in retdict:
                retdict[i.rtp.p_type] = 0
            retdict[i.rtp.p_type] += 1
    return retdict


def pcap_check_send_rtsp(pcap, src_ip, check_limit_count=100):
    """
    通过抓包判断是否有rtsp流
    """
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'udp.port==60000')
    send_count = 0
    for i in cap:
        send_count += 1
    aklog_info('RTSP流包个数: {}'.format(send_count))
    return send_count > check_limit_count


def pcap_return_rtsp_width_height(pcap, src_ip):
    """
    返回rtsp协商的width, height
    """
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'rtsp')
    for i in cap:
        if hasattr(i, 'rtsp') and hasattr(i.rtsp, 'h264_pic_height_in_map_units_minus1'):
            return i.rtsp.h264_pic_width_in_mbs_minus1, i.rtsp.h264_pic_height_in_map_units_minus1
    return False, False


def pcap_return_h264_width_height(pcap, src_ip):
    """
    返回h264的width, height
    """
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'h264')
    for i in cap:
        if hasattr(i, 'h264') and hasattr(i.h264, 'pic_width_in_mbs_minus1'):
            return i.h264.pic_width_in_mbs_minus1, i.h264.pic_height_in_map_units_minus1
    return False, False


def pcap_check_dst_rtsp_via_ip(pcap, src_ip, dst_ip):
    """检查rtsp是否走本地IP"""
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'rtsp')
    if not cap:
        aklog_warn('未抓到rtsp包')
        return False
    for i in cap:
        if i.ip.dst != dst_ip:
            return False
    return True


def pcap_check_rtsp_stream_via_ip(pcap, src_ip, dst_ip):
    """
    检查rtsp流: udp.port==60000 是走sip还是ip.   (室内机云端monitor测试)
    """
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'udp.port==60000')
    if not cap:
        aklog_warn('未抓到rtsp流包')
        return False
    for i in cap:
        if not hasattr(i, 'icmp'):
            if i.ip.dst != dst_ip:
                return False
    return True


def pcap_check_rtsp_stream_via_sip(pcap, src_ip, dst_ip):
    """
    只适用于门口机的工程: 因为是由门口机发起的rtsp!
    检查rtsp流: udp.port==60000 是走sip还是ip.
    src_ip = 门口机IP
    dst_ip = 室内机IP.
    """
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'udp.port==60000')
    if not cap:
        aklog_warn('未抓到rtsp流包')
        return False
    for i in cap:
        if not hasattr(i, 'icmp'):
            if i.ip.dst == dst_ip:
                return False
    return True


def pcap_indoor_check_rtsp_stream_via_sip(pcap, src_ip):
    """
    只适用于室内机的工程: 因为是由门口机发起的rtsp!
    检查rtsp流: udp.port==60000 是走sip还是ip.
    src_ip = 室内机IP.
    """
    cap = pcap_get_another_srcip_pcap(pcap, src_ip, 'udp.port==60000')
    # cap = pcap_get_another_srcip_audio_rtp_pcap(pcap, src_ip, limit=3000)
    if not cap:
        aklog_warn('未抓到rtsp流包')
        return False
    return True


@backup_pcap
def pcap_check_rtsp_bitrate(pcap, srcip, bitrate, rtsp_port=60000, ratio=0.25):
    """
    判断rtsp流的比特率
    bitrate: 传入整数的  128, 256, 1024, 2048
    rtsp_port: 60000 门口机固定rtsp流的端口是6000, 暂时先这么简单设计
    受限动态比特率,  画面在复杂程度下接口不准确.
    """
    bitrate = int(bitrate) * 1000
    cap = pcap_get_srcip_pcap(pcap, srcip, 'udp.port=={}'.format(rtsp_port))
    try:
        ret_dict = {}
        first_time = float(cap[1].sniff_timestamp)
        for i in cap:
            # 只截取1秒内的包. 出现次数最多的udp包的总帧大小
            cur_timestamp = float(i.sniff_timestamp)
            if cur_timestamp - first_time <= 1:
                if hasattr(i, 'udp'):
                    port = i.udp.port
                    if port in ret_dict:
                        ret_dict[port] = ret_dict[port] + int(i.frame_info.cap_len) * 8
                    else:
                        ret_dict[port] = int(i.frame_info.cap_len) * 8
            else:
                break
        ret = max(ret_dict.values())
        aklog_printf('Rtsp 比特率: %s kbps,  检查比特率: %s kbps' % (int(ret / 1000), bitrate / 1000))
        # 先设置误差范围上下20%
        # 如在夜间, 动态比特率也会变化比较大,  25%不够误差.
        range_min = int(bitrate * (1 - ratio)) if ratio < 1 else 0
        range_max = int(bitrate * (1 + ratio))
        if bitrate in [64000, 128000, 256000]:
            return ret in range(1000, 512000)
        else:
            return ret in range(range_min, range_max)
    except:
        aklog_printf(traceback.format_exc())
        aklog_printf('解析rtsp抓包失败')
        return None


def pcap_get_h264_bitrate(pcap, srcip, rtsp_port=60000):
    cap = pcap_get_srcip_pcap(pcap, srcip, 'udp.port=={} && rtp.p_type==96'.format(rtsp_port))  # h264
    try:
        ret = 0
        marker_count = 0
        for i in cap:
            # 只截取1秒内的包. 出现次数最多的udp包的总帧大小
            if marker_count > 24:
                break
            else:
                ret = ret + int(i.frame_info.cap_len) * 8
                if i.rtp.marker == '1':
                    marker_count += 1
        return int(ret / 1000)
    except:
        aklog_printf(traceback.format_exc())
        aklog_printf('解析rtsp抓包失败')
        return None


# endregion

# region 4.4 SMTP
@backup_pcap
def pcap_check_email(pcap, srcip, from_addr=None, sendto_addr=None, subject=None, content=None):
    """
    2023.6.16 检查有发送邮件， 不检查图片
    """
    cap = pcap_get_srcip_pcap(pcap, srcip, 'smtp')
    for i in cap:
        if hasattr(i, 'imf'):
            if from_addr and (from_addr not in i.imf.FROM):
                aklog_error('email发包检查 From Address 失败！')
                aklog_error(i.imf.FROM)
                return False
            if sendto_addr and sendto_addr not in i.imf.to:
                aklog_error('email发包检查 To Address 失败！')
                return False
            if subject and subject not in i.imf.__str__():
                aklog_error('email发包检查 subject 失败！')
                aklog_info(i.imf.__str__())
                return False
            if content:
                # 如果检查content, 有的机型content会base64加密以后才发送出去, 内容不确定. 暂时不检查content内容
                ret1 = content not in i.imf.__str__()
                ret2 = 'Content-Transfer-Encoding: base64' not in i.imf.__str__()
                if ret1 and ret2:
                    aklog_error('email发包检查 content 失败！')
                    aklog_info(i.imf.__str__())
                    return False
                else:
                    return True
            return True
    aklog_error('email检查抓包中没有IMF信息')
    return False


@backup_pcap
def pcap_check_email_send_image(pcap, srcip, sendto=None):
    """
    2022.5.13 检查抓包有发送image图片
    """
    cap = pcap_get_srcip_pcap(pcap, srcip, 'smtp')
    for i in cap:
        if hasattr(i, 'imf'):
            if hasattr(i.imf, 'mime_multipart_header_content_disposition'):
                upload_file = i.imf.mime_multipart_header_content_disposition
                if 'filename' in upload_file and 'smtp' in upload_file and '.jpg' in upload_file:
                    return True
                else:
                    ret = 'image/jpeg' in i.imf.__str__() and 'filename="smt' in i.imf.__str__()
                    if not ret:
                        aklog_error('上报email的附件可能不是一个截图文件!! 需确认!!!')
                    return ret
            else:
                if sendto:
                    if sendto not in i.imf.to:
                        aklog_error('email check: receiver failed')
                        return False
                return 'Content-Type: image/jpeg' in i.imf.__str__()
    return False


# endregion

# region 4.5 其他
@backup_pcap
def check_specify_pcap_port(pcap, check_port):
    """
    判断设备导出的pcap包中, 每一个报文都有一个指定的port
    用于测试specific port抓包
    """
    packets = rdpcap(pcap)
    if len(packets) == 0:
        return False
    for data in packets:
        if 'UDP' in data:
            if int(check_port) not in [data['UDP'].sport, data['UDP'].dport]:
                return False
        elif 'TCP' in data:
            if int(check_port) not in [data['TCP'].sport, data['TCP'].dport]:
                return False
        else:
            return False
    return True


@backup_pcap
def check_ports_in_pcap(pcap, port_list):
    """
    判断设备导出的pcap中, 包含了port_list里的各port包
    """
    ret_list = []
    packets = rdpcap(pcap)
    if len(packets) == 0:
        return False
    for data in packets:
        if 'UDP' in data:
            ret_list.append(data['UDP'].sport)
            ret_list.append(data['UDP'].dport)
        else:
            try:
                ret_list.append(data['TCP'].sport)
                ret_list.append(data['TCP'].dport)
            except IndexError:
                pass
    for port in port_list:
        if port not in ret_list:
            return False
    return True


@backup_pcap
def pcap_get_ntp_address(pcap, src_ip=None):
    """返回发包ntp server地址"""
    ret_list = []
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'ntp')
    for i in cap:
        if not hasattr(i, 'icmp'):
            ret_list.append(i.ip.dst)
    if not ret_list:
        aklog_error('未抓包ntp包!')
    return ret_list


@backup_pcap
def pcap_check_h264_profile(pcap, src_ip, profile='BP'):
    """检查S532机型H264 Profile类型"""
    profile_dict = {
        'BP': '66',
        'MP': '77',
        'HP': '100'
    }
    ret_list = []
    cap = pcap_get_srcip_pcap(pcap, src_ip, 'h264.nal_unit_hdr == 7')
    for i in cap:
        if not hasattr(i, 'icmp'):
            ret_list.append(i)
    if not ret_list:
        aklog_error('未抓包H264包!')
    for each in ret_list:
        if each.h264.profile_idc != profile_dict.get(profile):
            aklog_error('有H264报文Profile错误!')
            return False
    return True


@backup_pcap
def pcap_check_qos(pcap, src_ip, filter, qos, decode_as=None):
    cap = pcap_get_srcip_pcap(pcap, src_ip, protocol=filter)
    retlist = []
    for i in cap:
        if not hasattr(i, 'icmp'):
            retlist.append(i)
    if not retlist:
        aklog_error('未抓包到期望包!')
        return False
    else:
        for i in retlist:
            if i.ip.dsfield_dscp != str(qos):
                aklog_error('抓包中有qos与预期值不符合!')
                return False
        aklog_info('qos检查通过')
        return True


def pcap_check_dhcp_host_name(mac, hostname):
    cap = pcap_get_pc_capture(
        f'bootp && eth.src=={mac[0:2]}:{mac[2:4]}:{mac[4:6]}:{mac[6:8]}:{mac[8:10]}:{mac[10:12]}')
    retlist = []
    for i in cap:
        if hasattr(i.dhcp, 'option_hostname'):
            retlist.append(i.dhcp.option_hostname)
    if not retlist:
        aklog_error('检查dhcp host name失败, 未抓包到bootp或包中没有Option12 : Host Name字段')
        return False
    else:
        for j in retlist:
            if j.strip().lower() != hostname.lower():
                aklog_error('检查bootp包失败, 包含其他hostname. --> {}'.format(j))
                return False
        return True


def pcap_check_send_out_multicast(pcap, ip, dstip, dstport):
    """设备有 "发起" multicast组播: rtcp-->sender report"""
    ret = pcap_get_srcip_pcap(pcap, ip, 'udp')
    for i in ret:
        if hasattr(i, 'DATA') and i.DATA.data[:4] == '80c8':  # sender report
            # 检查目标ip和端口号.
            if i.ip.dst == dstip and i.udp.dstport == str(int(dstport) + 1):  # rtcp 端口实际是rtp端口+1
                return True
        else:
            if hasattr(i, 'rtcp') and i.rtcp.pt == '200':
                if i.ip.dst == dstip and i.udp.dstport == str(int(dstport) + 1):
                    return True
    aklog_error('设备未发起multicast组播包或者目标IP, 端口错误')
    return False


def pcap_check_send_out_multicast_stream(pcap, ip, dstip, dstport):
    """设备有multicast的rtp data包,  rtp包一秒钟要有50个以上. 依此判断"""
    ret = pcap_get_srcip_pcap(pcap, ip, 'udp')
    rtp_count = 0
    for i in ret:
        if i.ip.dst == dstip and i.udp.dstport == str(dstport):
            rtp_count += 1
    aklog_printf('multicast rtp 包个数: {}'.format(rtp_count))
    return rtp_count > 100


def pcap_check_send_out_multicast_bye(pcap, ip, dstip, dstport):
    """设备有 "挂断" multicast组播: rtcp-->receiver report goodbye"""
    ret = pcap_get_srcip_pcap(pcap, ip, 'udp')
    for i in ret:
        if hasattr(i, 'DATA') and i.DATA.data[:4] == '80c9' and i.DATA.data[18:20] == 'cb':  # receiver report + goodbye
            # 检查目标ip和端口号.
            if i.ip.dst == dstip and i.udp.dstport == str(int(dstport) + 1):  # rtcp 端口实际是rtp端口+1
                return True
        else:
            if hasattr(i, 'rtcp') and i.rtcp.pt == '201':
                if i.ip.dst == dstip and i.udp.dstport == str(int(dstport) + 1):
                    return True
    aklog_error('设备未发起multicast goodbye包或者目标IP, 端口错误')
    return False


def pcap_check_send_igmp(pcap, src_ip):
    """判断设备是否发送igmp包"""
    ret = pcap_get_srcip_pcap(pcap, src_ip, 'igmp')
    for i in ret:
        if i.ip.src == src_ip and i.igmp.maddr == '238.8.8.1':
            return True
    aklog_error('设备未为发送igmp包给238.8.8.1')
    return False


def pcap_check_zkt_lift_control(pcap, src_ip, dst_ip, floor, timeout):
    """判断zkt梯控的floor和timeout"""
    ret = pcap_get_srcip_pcap(pcap, src_ip, 'tcp.port==80')
    check_bit = ''
    check_list = []
    for i in ret:
        if i.ip.dst == dst_ip and i.tcp.seq == '1' and i.tcp.ack == '1' and i.tcp.len == '13':
            check_bit = i.tcp.payload
            ret_floor = check_bit.split(':')[6][1:] if check_bit.split(':')[6].startswith('0') else \
                check_bit.split(':')[6]
            ret_timeout = check_bit.split(':')[8][1:] if check_bit.split(':')[8].startswith('0') else \
                check_bit.split(':')[8]
            check_list.append([ret_floor, ret_timeout])
    if check_list == []:
        aklog_error('未抓到zkt梯控相关的包')
        return False
    else:
        ret_list = [hex(int(floor))[2:], hex(int(timeout))[2:]]
        if ret_list in check_list:
            return True
        else:
            aklog_error(f'zkt梯控梯控抓包:{check_list}')
            return False


def pcap_check_dclient_transport(pcap, src_ip, transport='TCP'):
    """
    安卓室内机抓包检查config on cloud开门的dclient是TCP, UDP.
    """
    ret = pcap_get_srcip_pcap(pcap, src_ip, 'tcp.port==8501 || udp.port == 8501')
    if not ret:
        aklog_error('未抓到dclient包')
        return False
    for i in ret:
        if transport == 'TCP':
            if hasattr(i, 'UDP'):
                return False
        else:
            if hasattr(i, 'TCP'):
                return False
    return True


# endregion


# endregion

if __name__ == '__main__':
    print('debug')
    # rtcp_port_list = pcap_get_rtcp_port_list(r'E:\SVN_Python\Develop\AKautotest\testfile\Browser\Chrome_Download\C315\phone.pcap',
    #                                          '192.168.88.109')
    # audio_rtcp_port = rtcp_port_list[0]
    # audio_rtp_port = int(audio_rtcp_port) - 1
    # print(audio_rtp_port)
    # time.sleep(3)
    ret = pcap_check_zkt_lift_control(r'F:\ChromeNew\phone.pcap', '192.168.88.61', '192.168.88.25', '4', '60')
    # ret = pcap_get_sip_request_info(
    #     r'D:\Users\Administrator\Desktop\register.pcap',
    #     '192.168.10.154', 'REGISTER')
    print(ret)
    # ret = pcap_check_is_exist_rport(
    #     r'E:\SVN_Python\Develop\AKautotest\testfile\Browser\Chrome_Download\C315\phone.pcap',
    #     '192.168.88.245')
    # ret = pcap_check_sip_call_id_with_host(r'D:\Users\Administrator\Desktop\phone.pcap', '192.168.88.109')
    # print(ret)
