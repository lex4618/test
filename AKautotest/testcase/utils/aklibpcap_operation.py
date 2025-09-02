# -*- coding: utf-8 -*-

import os
import sys
import time

from scapy.utils import rdpcap
from scapy.sendrecv import sniff, wrpcap

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
if root_path not in sys.path:
    sys.path.append(root_path)

from akcommon_define import *


class pcap_operation(object):
    def __init__(self):
        self.dpkt = None

    def get_pcap(self, ifs, filters=None, count=0, timeout=None):
        """
        开启抓包
        :param ifs: 网卡名称，比如：以太网
        :param filters:
        :param count:
        :param timeout:
        :return:
        """
        if filters:
            self.dpkt = sniff(iface=ifs, filter=filters, count=count, timeout=timeout)
        else:
            self.dpkt = sniff(iface=ifs, count=count, timeout=timeout)

    def save_to_pcap_file(self, file_path):
        wrpcap(file_path, self.dpkt)

    def read_pcap(self, pcap_file):
        self.dpkt = rdpcap(pcap_file)

    def get_data_from_pcap(self, src_mac=None, dst_mac=None, src_ip=None, dst_ip=None,
                           trans_type='TCP', src_port=None, dst_port=None, length=None):
        pkt_datas = []
        for pkt in self.dpkt:

            if 'Ether' in pkt:
                if src_mac and pkt['Ether'].src != src_mac.lower():
                    continue
                if dst_mac and pkt['Ether'].dst != dst_mac.lower():
                    continue
            elif src_mac or dst_mac:
                continue

            if 'IP' in pkt:
                if src_ip and pkt['IP'].src != src_ip:
                    continue
                if dst_ip and pkt['IP'].dst != dst_ip:
                    continue
                if length and (pkt['IP'].len < length or pkt['IP'].len <= 40):
                    continue
            elif src_ip or dst_ip:
                continue

            if trans_type in pkt:
                if dst_port and pkt[trans_type].dport != int(dst_port):
                    continue
                if src_port and pkt[trans_type].sport != int(src_port):
                    continue
            else:
                continue

            if 'Raw' in pkt:
                pkt_data = pkt['Raw'].load
                pkt_datas.append(pkt_data)
        # aklog_printf('pkt_datas: %r' % pkt_datas)
        return pkt_datas


def pcap_check_is_exist_rport(pcap_file, src_ip, dst_ip, trans_type, dst_port):
    """检测sip包中是否存在rport字段"""
    pcap = pcap_operation()
    pcap.read_pcap(pcap_file)
    datas = pcap.get_data_from_pcap(src_ip=src_ip, dst_ip=dst_ip, trans_type=trans_type, dst_port=dst_port)
    for data in datas:
        data = data.decode('utf-8')
        if 'rport;' in data:
            return True
    return False


def pcap_check_call_is_ip_or_sip(pcap_file, src_ip, dst_ip=None, trans_type='TCP', dst_port=5060):
    """检测SIP通话是IP直拨还是通过SIP帐号"""
    aklog_printf('pcap_check_call_is_ip_or_sip, src_ip: %s, dst_ip: %s, trans_type: %s, dst_port: %s'
                 % (src_ip, dst_ip, trans_type, dst_port))
    pcap = pcap_operation()
    pcap.read_pcap(pcap_file)
    datas = pcap.get_data_from_pcap(src_ip=src_ip, dst_ip=dst_ip, trans_type=trans_type, dst_port=dst_port)
    for data in datas:
        data = data.decode('utf-8')
        if 'INVITE' in data:
            return True
    aklog_printf(datas)
    return False


def pcap_check_monitor_is_lan_or_cloud(pcap_file, src_ip, dst_ip=None, dst_port=554, trans_type='TCP'):
    """检测监控是走局域网还是走云平台"""
    aklog_printf('pcap_check_monitor_is_lan_or_cloud, src_ip: %s, dst_ip: %s, dst_port: %s'
                 % (src_ip, dst_ip, dst_port))
    pcap = pcap_operation()
    pcap.read_pcap(pcap_file)
    datas = pcap.get_data_from_pcap(src_ip=src_ip, dst_ip=dst_ip, trans_type=trans_type, dst_port=dst_port)
    for data in datas:
        data = data.decode('utf-8')
        if 'RTSP' in data:
            return True
    aklog_printf(datas)
    return False


def pcap_check_http_action_url(pcap_file, action_url, src_ip, dst_port=80):
    """检查抓包是否包含了指定的action url请求"""
    pcap = pcap_operation()
    pcap.read_pcap(pcap_file)
    datas = pcap.get_data_from_pcap(src_ip=src_ip, dst_ip=get_local_host_ip(), trans_type='TCP', dst_port=dst_port)
    results = []
    for data in datas:
        data = data.decode(encoding='utf-8')
        if action_url in data:
            results.append(True)
    aklog_printf('抓包内容: %s' % datas)
    aklog_printf('results: %s' % results)
    return results


if __name__ == "__main__":
    print('测试代码')
