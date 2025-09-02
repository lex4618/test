# -*- coding: utf-8 -*-

import os
import sys
from ctypes import *

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
if root_path not in sys.path:
    sys.path.append(root_path)

from akcommon_define import *


class DClient_Decrypt(object):
    def __init__(self):
        self.pcap = pcap_operation()
        dll_dir = root_path + '\\testcase\\utils\\AKDecrypt64'
        os.environ['path'] += ';%s' % dll_dir  # 添加dll依赖库目录到系统环境，否则相关的dll库会找不到
        dll_path = dll_dir + '\\AKDecrypt.dll'
        self.dll = WinDLL(dll_path)
        self.ifs = cmd_get_network_adapter_name()

    def decrypt_msg_from_pcap_file(self, pcap_file, src_mac, trans_type, dst_ip, dst_port):
        aklog_printf('decrypt_msg_from_pcap_file')
        msgs = []
        self.pcap.read_pcap(pcap_file)
        pkt_data_list = self.pcap.get_data_from_pcap(src_mac=src_mac, trans_type=trans_type, dst_ip=dst_ip,
                                                     dst_port=dst_port)
        for pkt_data in pkt_data_list:
            file = root_path + '\\testfile\\dclient_msg_tmp\\pcap_file_data'
            with open(file, "wb") as fp:  # 将PCAP获取的data原始数据保存到二进制文件
                fp.write(pkt_data[10:])

            """
            使用程序link.exe在dll中查看真实的函数名称。例如，link.exe在MSVC2010中位于此处：
            c:\\program files\\microsoft visual studio 10.0\\VC\bin\\link.exe
            使用：link /dump /exports yourFileName.dll 可以看到如下，这样就可以获取到函数在dll中的名称
            ordinal hint RVA      name
            0 00001190 ?AesDecryptFileByDefault@@YAHPEAD0@Z
            1 00001000 ?AesDecryptFileByMac@@YAHPEAD00@Z
            
            DLLTEST_API int AesDecryptFileByMac(char *pszFilePath, char *pszOut, char *pszMAC);
            DLLTEST_API int AesDecryptFileByDefault(char *pszFilePath, char *pszOut);
            两个方法都是传入指针参数，所以需要使用c_char_p方法生成指针
            """
            AesDecryptFileByMac = getattr(self.dll, '?AesDecryptFileByMac@@YAHPEAD00@Z')
            AesDecryptFileByDefault = getattr(self.dll, '?AesDecryptFileByDefault@@YAHPEAD0@Z')
            msg_out = ''
            p_msg_out = c_char_p(msg_out.encode("utf-8"))
            p_file = c_char_p(file.encode("utf-8"))
            for j in range(3):  # dclient加解密有三种方式
                if j == 0:
                    src_mac = src_mac.upper().replace(':', '')
                    p_src_mac = c_char_p(src_mac.encode("utf-8"))
                    AesDecryptFileByMac(p_file, p_msg_out, p_src_mac)
                elif j == 1:
                    default_mac = '0C11050000FF'
                    p_default_mac = c_char_p(default_mac.encode("utf-8"))
                    AesDecryptFileByMac(p_file, p_msg_out, p_default_mac)
                elif j == 2:
                    # print('AesDecryptFileByDefault')
                    AesDecryptFileByDefault(p_file, p_msg_out)
                else:
                    aklog_printf('解密失败')
                    break

                msg_after_decrypt = p_msg_out.value
                if b'<Msg>' in msg_after_decrypt:
                    msg_after_decrypt = msg_after_decrypt.decode('utf-8')
                    msg_dict = parse_msg_to_dict(msg_after_decrypt)
                    msgs.append(msg_dict)
                    break
                else:
                    continue
        aklog_printf('msgs: %r' % msgs)
        return msgs

    def decrypt_msg_from_scapy(self, src_mac, trans_type, dst_ip, dst_port, timeout=10):
        aklog_printf('decrypt_msg_from_scapy')
        msgs = []
        filters = "ether src host %s and %s and dst host %s and dst port %s" % (src_mac.lower(),
                                                                                trans_type.lower(),
                                                                                dst_ip,
                                                                                dst_port)
        self.pcap.get_pcap(self.ifs, filters=filters, timeout=timeout)
        pkt_data_list = self.pcap.get_data_from_pcap()
        # print(len(pkt_data_list))
        for pkt_data in pkt_data_list:
            # print(pkt_data)
            file = root_path + '\\testfile\\dclient_msg_tmp\\scapy_pcap_data'
            with open(file, "wb") as fp:  # 将PCAP获取的data原始数据保存到二进制文件
                fp.write(pkt_data[10:])
                fp.close()
            """
            使用程序link.exe在dll中查看真实的函数名称。例如，link.exe在MSVC2010中位于此处：
            c:\\program files\\microsoft visual studio 10.0\\VC\bin\\link.exe
            使用：link /dump /exports yourFileName.dll 可以看到如下，这样就可以获取到函数在dll中的名称
            ordinal hint RVA      name
            0 00001190 ?AesDecryptFileByDefault@@YAHPEAD0@Z
            1 00001000 ?AesDecryptFileByMac@@YAHPEAD00@Z

            DLLTEST_API int AesDecryptFileByMac(char *pszFilePath, char *pszOut, char *pszMAC);
            DLLTEST_API int AesDecryptFileByDefault(char *pszFilePath, char *pszOut);
            两个方法都是传入指针参数，所以需要使用c_char_p方法生成指针
            """
            AesDecryptFileByMac = getattr(self.dll, '?AesDecryptFileByMac@@YAHPEAD00@Z')
            AesDecryptFileByDefault = getattr(self.dll, '?AesDecryptFileByDefault@@YAHPEAD0@Z')
            msg_out = ''
            p_msg_out = c_char_p(msg_out.encode("utf-8"))
            p_file = c_char_p(file.encode("utf-8"))
            for j in range(4):  # dclient加解密有三种方式
                if j == 0:
                    src_mac = src_mac.upper().replace(':', '')
                    p_src_mac = c_char_p(src_mac.encode("utf-8"))
                    AesDecryptFileByMac(p_file, p_msg_out, p_src_mac)
                elif j == 1:
                    default_mac = '0C11050000FF'
                    p_default_mac = c_char_p(default_mac.encode("utf-8"))
                    AesDecryptFileByMac(p_file, p_msg_out, p_default_mac)
                elif j == 2:
                    # print('AesDecryptFileByDefault')
                    AesDecryptFileByDefault(p_file, p_msg_out)
                else:
                    aklog_printf('解密失败')
                    break

                msg_after_decrypt = p_msg_out.value
                if b'<Msg>' in msg_after_decrypt:
                    msg_after_decrypt = msg_after_decrypt.decode('utf-8')
                    msg_dict = parse_msg_to_dict(msg_after_decrypt)
                    msgs.append(msg_dict)
                    break
                else:
                    continue
            # File_process.remove_file(file)
            # time.sleep(0.5)
        aklog_printf('msgs: %r' % msgs)
        return msgs


if __name__ == '__main__':
    print('测试代码')
    dclient = DClient_Decrypt()
    # dclient.decrypt_msg_from_pcap_file(r"D:\Users\Administrator\Desktop\dclient2.pcap", src_mac='0c:11:05:0a:5f:58',
    #                                    trans_type='TCP', dst_ip='47.107.86.73', dst_port=8501)
    dclient.decrypt_msg_from_scapy(src_mac='0c:11:05:0a:5f:58',
                                   trans_type='TCP', dst_ip='47.107.86.73', dst_port=8501)
