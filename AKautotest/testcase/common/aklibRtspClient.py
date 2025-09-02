# -*- coding: UTF-8 -*-

import os
import sys
import time
import socket
import hashlib
import base64
import traceback
import cv2

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]

from akcommon_define import *


class RtspClient(object):

    def __init__(self, ip, username, password, port=554, timeout=3, server_path='/live/ch00_0'):
        """构造函数，初始化Rtsp变量，进行socket连接操作"""
        self.server_ip = ip  # RTSP服务器IP地址
        self.server_username = username  # RTSP用户名
        self.server_password = password  # RTSP密码
        self.server_port = port  # RTSP服务器使用端口
        self.send_timeout = timeout
        self.server_path = server_path  # URL中端口之后的部份，测试发现不同服务器对这部份接受的值是不一样的，也就是说自己使用时很可能得自己修改这部份的值
        self.cseq = 1  # RTSP使用的请求起始序列码，不需要改动
        self.user_agent = 'LibVLC/3.0.2 (LIVE555 Streaming Media v2016.11.28)'  # 自定义请求头部
        self.buffer_len = 1500  # 用于接收服务器返回数据的缓冲区的大小
        self.auth_method = None  # RTSP使用的认证方法，Basic/Digest
        self.header_normal_modify_allow = False  # 是否允许拼接其他协议规定的请求头的总开关，请些请求头的值为正常值（大多是RFC给出的示例）
        self.header_overload_modify_allow = False  # 是否允许拼接其他协议规定的请求头的总开关，请些请求头的值为超长字符串
        self.options_header_modify = True  # OPTIONS请求中，是否允许拼接其他协议规定的请求头的开关
        self.describe_header_modify = True  # 第一次DESCRIBE请求中，是否允许拼接其他协议规定的请求头的开关
        self.describe_auth_header_modify = True  # 第二次DESCRIBE请求中，是否允许拼接其他协议规定的请求头的开关
        self.setup_header_modify = True  # 第一次SETUP请求中，是否允许拼接其他协议规定的请求头的开关
        self.setup_session_header_modify = True  # 第二次SETUP请求中，是否允许拼接其他协议规定的请求头的开关
        self.play_header_modify = True  # PLAY请求中，是否允许拼接其他协议规定的请求头的开关
        self.get_parameter_header_modify = True  # GET PARAMETER请求中，是否允许拼接其他协议规定的请求头的开关
        self.teardown_header_modify = True  # TEARDOWN请求中，是否允许拼接其他协议规定的请求头的开关
        self.realm_value = ""
        self.nonce_value = ""
        self.session = ""
        self.url = 'rtsp://' + self.server_ip + ':' + str(self.server_port) + self.server_path
        self.socket_send = None
        # 创建Rtsp连接
        self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._hostname = socket.gethostname()  # 获取主机名
        self._host_ip = socket.gethostbyname(self._hostname)  # 获取本机IP
        self._host_port = 0
        self.rtp_socket.bind((self._host_ip, self._host_port))
        self.rtp_recv_flag = True

    def __del__(self):
        """析构函数，关闭socket连接操作"""
        if self.socket_send is not None:
            if self.socket_send.fileno() > 0:
                self.socket_send.close()
            if self.rtp_socket.fileno() > 0:
                self.rtp_socket.close()

    def connect_rtsp_server(self):
        print('connect_rtsp_server')
        self.socket_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_send.settimeout(self.send_timeout)
        try:
            self.socket_send.connect((self.server_ip, self.server_port))
            return True
        except:
            print('连接异常, %s' % traceback.format_exc())
            return False

    def close_socket(self):
        if self.socket_send is not None:
            if self.socket_send.fileno() > 0:
                self.socket_send.close()
            if self.rtp_socket.fileno() > 0:
                self.rtp_socket.close()

    def set_rtp_recv_flag(self, value):
        """设置rtp_recv_flag的值"""
        if value is True or value is False:
            self.rtp_recv_flag = value

    def set_header_normal_modify(self, value):
        """设置header_normal_modify_allow的值"""
        if value is True or value is False:
            self.header_normal_modify_allow = value

    def set_header_overload_modify(self, value):
        """设置header_overload_modify_allow的值"""
        if value is True or value is False:
            self.header_overload_modify_allow = value

    def set_options_header_modify(self, value):
        """设置options_header_modify的值"""
        if value is True or value is False:
            self.options_header_modify = value

    def set_describe_header_modify(self, value):
        """设置describe_header_modify的值"""
        if value is True or value is False:
            self.describe_header_modify = value

    def set_setup_header_modify(self, value):
        """设置setup_header_modify的值"""
        if value is True or value is False:
            self.setup_header_modify = value

    def play_header_modify(self, value):
        """设置play_header_modify的值"""
        if value is True or value is False:
            self.play_header_modify = value

    def set_get_parameter_header_modify(self, value):
        """设置get_parameter_header_modify的值"""
        if value is True or value is False:
            self.get_parameter_header_modify = value

    def set_teardown_header_modify(self, value):
        """设置teardown_header_modify的值"""
        if value is True or value is False:
            self.teardown_header_modify = value

    def get_response_value_by_digest(self, url, public_method, realm, nonce):
        """用于Digest认证方式时生成response的值"""
        frist_pre_md5_value = hashlib.md5(
            (self.server_username + ':' + realm + ':' + self.server_password).encode()).hexdigest()
        first_post_md5_value = hashlib.md5((public_method + ':' + url).encode()).hexdigest()
        response_value = hashlib.md5(
            (frist_pre_md5_value + ':' + nonce + ':' + first_post_md5_value).encode()).hexdigest()
        return response_value

    def get_options_header(self):
        """生成options请求头部"""
        str_options_header = 'OPTIONS rtsp://' + self.server_ip + ':' + str(
            self.server_port) + self.server_path + ' RTSP/1.0\r\n'
        str_options_header += 'CSeq: ' + str(self.cseq) + '\r\n'
        str_options_header += 'User-Agent: ' + self.user_agent + '\r\n'
        str_options_header += '\r\n'
        return str_options_header

    def get_describe_header(self, url, realm, nonce):
        """生成describe请求头部"""
        public_method = 'DESCRIBE'
        str_describe_header = 'DESCRIBE ' + self.url + ' RTSP/1.0\r\n'
        str_describe_header += 'CSeq: ' + str(self.cseq) + '\r\n'

        if self.auth_method == 'Basic':
            auth_64 = base64.b64encode(
                (self.server_username + ":" + self.server_password).encode("utf-8")).decode()
            str_describe_header += 'Authorization: Basic ' + auth_64 + ' \r\n'
        elif self.auth_method == 'Digest':
            response_value = self.get_response_value_by_digest(url, public_method, realm, nonce)
            str_describe_header += 'Authorization: Digest username="' + self.server_username + '", realm="' + realm + \
                                   '", nonce="' + nonce + '", uri="' + url + '", response="' + response_value + '"\r\n'
        str_describe_header += 'User-Agent: ' + self.user_agent + '\r\n'
        str_describe_header += 'Accept: application/sdp\r\n'
        str_describe_header += '\r\n'
        return str_describe_header

    def get_setup_header(self, url, realm, nonce):
        """生成setup请求头部"""
        public_method = 'SETUP'
        str_setup_header = 'SETUP rtsp://' + self.server_ip + ':' + str(
            self.server_port) + self.server_path + '/trackID=0 RTSP/1.0\r\n'
        str_setup_header += 'CSeq: ' + str(self.cseq) + '\r\n'

        if self.auth_method == 'Basic':
            auth_64 = base64.b64encode(
                (self.server_username + ":" + self.server_password).encode("utf-8")).decode()
            str_setup_header += 'Authorization: Basic ' + auth_64 + ' \r\n'
        elif self.auth_method == 'Digest':
            response_value = self.get_response_value_by_digest(url, public_method, realm, nonce)
            str_setup_header += 'Authorization: Digest username="' + self.server_username + '", realm="' + realm + \
                                '", nonce="' + nonce + '", uri="' + url + '", response="' + response_value + '"\r\n'
        str_setup_header += 'User-Agent: ' + self.user_agent + '\r\n'

        str_setup_header += 'Transport: RTP/AVP;unicast;client_port=62012-62013\r\n'
        str_setup_header += '\r\n'
        return str_setup_header

    def get_setup_session_header(self, url, realm, nonce, session):
        """生成setup请求头部，带有session"""
        public_method = 'SETUP'
        str_setup_session_header = 'SETUP rtsp://' + self.server_ip + ':' + str(
            self.server_port) + self.server_path + '/trackID=1 RTSP/1.0\r\n'
        str_setup_session_header += 'CSeq: ' + str(self.cseq) + '\r\n'

        if self.auth_method == 'Basic':
            auth_64 = base64.b64encode((self.server_username + ":" + self.server_password).encode("utf-8")).decode()
            str_setup_session_header += 'Authorization: Basic ' + auth_64 + ' \r\n'
        elif self.auth_method == 'Digest':
            response_value = self.get_response_value_by_digest(url, public_method, realm, nonce)
            str_setup_session_header += 'Authorization: Digest username="' + self.server_username + '", realm="' + \
                                        realm + '", nonce="' + nonce + '", uri="' + url + '", response="' + \
                                        response_value + '"\r\n'
        str_setup_session_header += 'User-Agent: ' + self.user_agent + '\r\n'

        str_setup_session_header += 'Transport: RTP/AVP;unicast;client_port=62002-62003\r\n'
        str_setup_session_header += 'Session: ' + session + '\r\n'
        str_setup_session_header += '\r\n'
        return str_setup_session_header

    def get_play_header(self, url, realm, nonce, session):
        """生成play请求头部"""
        public_method = 'PLAY'
        str_play_header = 'PLAY rtsp://' + self.server_ip + ':' + str(self.server_port) + \
                          self.server_path + ' RTSP/1.0\r\n'
        str_play_header += 'CSeq: ' + str(self.cseq) + '\r\n'

        if self.auth_method == 'Basic':
            auth_64 = base64.b64encode((self.server_username + ":" + self.server_password).encode("utf-8")).decode()
            str_play_header += 'Authorization: Basic ' + auth_64 + ' \r\n'
        elif self.auth_method == 'Digest':
            response_value = self.get_response_value_by_digest(url, public_method, realm, nonce)
            str_play_header += 'Authorization: Digest username="' + self.server_username + '", realm="' + realm + \
                               '", nonce="' + nonce + '", uri="' + url + '", response="' + response_value + '"\r\n'
        str_play_header += 'User-Agent: ' + self.user_agent + '\r\n'

        str_play_header += 'Session: ' + session + '\r\n'
        str_play_header += 'Range: npt=0.000-\r\n'
        str_play_header += '\r\n'
        return str_play_header

    def get_get_parameter_header(self, url, realm, nonce, session):
        """生成GET_PARAMETER请求头部"""
        public_method = 'GET_PARAMETER'
        str_get_parameter_header = 'GET_PARAMETER rtsp://' + self.server_ip + ':' + str(
            self.server_port) + self.server_path + ' RTSP/1.0\r\n'
        str_get_parameter_header += 'CSeq: ' + str(self.cseq) + '\r\n'

        if self.auth_method == 'Basic':
            auth_64 = base64.b64encode((self.server_username + ":" + self.server_password).encode("utf-8")).decode()
            str_get_parameter_header += 'Authorization: Basic ' + auth_64 + ' \r\n'
        elif self.auth_method == 'Digest':
            response_value = self.get_response_value_by_digest(url, public_method, realm, nonce)
            str_get_parameter_header += 'Authorization: Digest username="' + self.server_username + '", realm="' + \
                                        realm + '", nonce="' + nonce + '", uri="' + url + '", response="' + \
                                        response_value + '"\r\n'
        str_get_parameter_header += 'User-Agent: ' + self.user_agent + '\r\n'

        str_get_parameter_header += 'Session: ' + session + '\r\n'
        str_get_parameter_header += '\r\n'
        return str_get_parameter_header

    def get_teardown_header(self, url, realm, nonce, session):
        """生成teardown请求头部"""
        public_method = 'TEARDOWN'
        str_teardown_header = 'TEARDOWN rtsp://' + self.server_ip + ':' + str(
            self.server_port) + self.server_path + ' RTSP/1.0\r\n'
        str_teardown_header += 'CSeq: ' + str(self.cseq) + '\r\n'

        if self.auth_method == 'Basic':
            auth_64 = base64.b64encode((self.server_username + ":" + self.server_password).encode("utf-8")).decode()
            str_teardown_header += 'Authorization: Basic ' + auth_64 + ' \r\n'
        elif self.auth_method == 'Digest':
            response_value = self.get_response_value_by_digest(url, public_method, realm, nonce)
            str_teardown_header += 'Authorization: Digest username="' + self.server_username + '", realm="' + realm + \
                                   '", nonce="' + nonce + '", uri="' + url + '", response="' + response_value + '"\r\n'
        str_teardown_header += 'User-Agent: ' + self.user_agent + '\r\n'

        str_teardown_header += 'Session: ' + session + '\r\n'
        str_teardown_header += '\r\n'
        return str_teardown_header

    def add_normal_header_according_to_protocol(self, str_header):
        """拼接rtsp协议的其他请求头，以测试程序对这些请求头部的处理是否有问题；这个方法与add_overload_header_according_to_protocol是互斥的"""
        str_header = str_header[0:len(str_header) - 2]
        str_header += 'Accept: application/rtsl, application/sdp;level=-2'
        str_header += 'Accept-Encoding: gzip;q=1.0, identity; q=0.5, *;q=0\r\n'
        str_header += 'Accept-Language: da, en-gb;q=0.8, en;q=0.7\r\n'
        str_header += 'Bandwidth: 4000 \r\n'
        str_header += 'Blocksize: 4000 \r\n'
        str_header += 'Cache-Control: no-cache;max-stale \r\n'
        str_header += 'Conference: 199702170042.SAA08642@obiwan.arl.wustl.edu%20Starr \r\n'
        str_header += 'Connection: close\r\n'
        str_header += 'Content-Base: gzip\r\n'
        str_header += 'Content-Encoding: gzip\r\n'
        str_header += 'Content-Language: mi,en\r\n'
        str_header += 'Content-Length: 2034953454546565 \r\n'
        str_header += 'Content-Location: /etc/passwd\r\n'
        str_header += 'Content-Type: text/html; charset=ISO-8859-4gg\r\n'
        str_header += 'Date: Tue, 15 Nov 1995x 08:12:31 GMT\r\n'
        str_header += 'Expires: Thu, 01 Dec 1994 16:00:00 GMT \r\n'
        str_header += 'From: webmaster@w3.org\r\n'
        str_header += 'If-Modified-Since: Sat, 29 Oct 1994 19:43:31 GMT \r\n'
        str_header += 'Last-Modified: Tue, 15 Nov 1994 12:45:26 GMT\r\n'
        str_header += 'Proxy-Require: funky-feature\r\n'
        str_header += 'Referer: http://www.w3.org/hypertext/DataSources/Overview.html\r\n'
        str_header += 'Require: funky-feature \r\n'
        str_header += 'Scale: -3.5 \r\n'
        str_header += 'Speed: 2.5 \r\n'
        str_header += 'Transport: RTP/AVP;unicast;client_port=3456-3457;mode="PLAY" \r\n'
        str_header += 'Via: 1.0 fred, 1.1 nowhere.com (Apache/1.1)\r\n'
        str_header += 'Range: npt=2\r\n'
        str_header += '\r\n'
        return str_header

    def add_overload_header_according_to_protocol(self, str_header):
        """拼接rtsp协议的其他请求头，并将这些请求头的字赋为超长字符串，以测试程序对这些请求头部的处理是否有缓冲区溢出问题；这个方法与add_normal_header_according_to_protocol是互斥的"""
        str_header = str_header[0:len(str_header) - 2]
        str_header += 'Accept: application/rtsl012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789, application/sdp;level=-2012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789'
        str_header += 'Accept-Encoding: gzip01234567890123456789012345678901234567890123456789;q=1.0012345678901234567890123456789012345678901234567890123456789, identity; q=0.5012345678901234567890123456789, *;q=0012345678901234567890123456789\r\n'
        str_header += 'Accept-Language: da, en-gb;q=0.80123456789012345678901234567890123456789, en;q=0.7012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789\r\n'
        str_header += 'Bandwidth: 400001234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789 \r\n'
        str_header += 'Blocksize: 4000012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789 \r\n'
        str_header += 'Cache-Control: no-cache;max-stale \r\n'
        str_header += 'Conference: 199702170042.SAA08642@obiwan.arl.wustl.edu%20Starr01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789 \r\n'
        str_header += 'Connection: 01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789close\r\n'
        str_header += 'Content-Base: 0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789gzip\r\n'
        str_header += 'Content-Encoding: 01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789gzip\r\n'
        str_header += 'Content-Language: 01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789mi,en\r\n'
        str_header += 'Content-Length: 203495345454656501234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789 \r\n'
        str_header += 'Content-Location: /etc/passwd01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789\r\n'
        str_header += 'Content-Type: text/html012345678901234567890123456789012345678901234567890123456789; charset=012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789ISO-8859-4gg\r\n'
        str_header += 'Date: Tue, 15 Nov 1995x 08:12:310123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789 GMT\r\n'
        str_header += 'Expires: Thu, 01 Dec 1994 16012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789:00:00 GMT \r\n'
        str_header += 'From: webmaster@w30123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789.org\r\n'
        str_header += 'If-Modified-Since: Sat, 29 Oct 1994 19:43:31012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789 GMT \r\n'
        str_header += 'Last-Modified: Tue, 15 Nov 1994 120123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789:45:26 GMT\r\n'
        str_header += 'Proxy-Require: funky-feature\r\n'
        str_header += 'Referer: http://www.w3.org/hypertext/DataSources/Overview.html\r\n'
        str_header += 'Require: funky-feature0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789 \r\n'
        str_header += 'Scale: -0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567893.5 \r\n'
        str_header += 'Speed: 20123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789.5 \r\n'
        str_header += 'Transport: RTP/AVP;unicast;client_port=3456-345012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567897;mode="01234567890123456789PLAY" \r\n'
        str_header += 'Via: 1.0 fred, 0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567891.1 nowhere.com (Apache/0123456789012345678901234567891.1)\r\n'
        str_header += 'Range: npt=20123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789\r\n'
        str_header += '\r\n'
        return str_header

    def send_option_and_recv(self):
        """封装发送option并接收应答函数"""
        try:
            self.cseq = self.cseq + 1
            str_options_header = self.get_options_header()
            if self.header_normal_modify_allow & self.options_header_modify:
                str_options_header = self.add_normal_header_according_to_protocol(str_options_header)
            elif self.header_overload_modify_allow & self.options_header_modify:
                str_options_header = self.add_overload_header_according_to_protocol(str_options_header)
            self.socket_send.send(str_options_header.encode())
            msg_recv = self.socket_send.recv(self.buffer_len).decode()
            print("OPTION recv = \n", msg_recv)
            if msg_recv.find('200 OK') == -1:
                print('OPTIONS request is error')
                return False
            else:
                print('OPTIONS request is OK')
                return True
        except:
            print(traceback.format_exc())
            return False

    def send_describe_and_recv(self):
        """封装发送describe并接收应答函数"""
        for i in range(2):
            self.cseq = self.cseq + 1
            str_describe_header = self.get_describe_header(self.url, self.realm_value, self.nonce_value)
            if self.header_normal_modify_allow & self.describe_header_modify:
                str_describe_header = self.add_normal_header_according_to_protocol(str_describe_header)
            elif self.header_overload_modify_allow & self.describe_header_modify:
                str_describe_header = self.add_overload_header_according_to_protocol(str_describe_header)

            self.socket_send.send(str_describe_header.encode())
            msg_recv = self.socket_send.recv(self.buffer_len).decode()
            print("describe recv = \n", msg_recv)
            if msg_recv.find('401 Unauthorized') != -1:
                msg_recv_dict = msg_recv.split('\r\n')
                print('DESCRIBE request occur error: ')
                print(msg_recv_dict[0])
                # 获取服务端需要的Auth认证方式
                auth_pos = msg_recv.find('WWW-Authenticate:')
                auth_value_begin_pos = msg_recv.find(':', auth_pos) + 1
                auth_value_end_pos = msg_recv.find(' ', auth_value_begin_pos + 1)
                auth_value = msg_recv[auth_value_begin_pos:auth_value_end_pos]
                self.auth_method = auth_value.strip()
                # 获取服务端需要的realm
                realm_pos = msg_recv.find('realm')
                realm_value_begin_pos = msg_recv.find('"', realm_pos) + 1
                realm_value_end_pos = msg_recv.find('"', realm_pos + 8)
                self.realm_value = msg_recv[realm_value_begin_pos:realm_value_end_pos]
                # 获取服务端需要的nonce
                nonce_pos = msg_recv.find('nonce')
                nonce_value_begin_pos = msg_recv.find('"', nonce_pos) + 1
                nonce_value_end_pos = msg_recv.find('"', nonce_pos + 8)
                self.nonce_value = msg_recv[nonce_value_begin_pos:nonce_value_end_pos]
                continue
            else:
                print('DESCRIBE is ok')
                return True
        return False

    def send_setup_and_recv(self):
        """封装发送setup并接收应答函数"""
        self.cseq = self.cseq + 1
        str_setup_header = self.get_setup_header(self.url, self.realm_value, self.nonce_value)
        if self.header_normal_modify_allow & self.setup_header_modify:
            str_setup_header = self.add_normal_header_according_to_protocol(str_setup_header)
        elif self.header_overload_modify_allow & self.setup_header_modify:
            str_setup_header = self.add_overload_header_according_to_protocol(str_setup_header)
        self.socket_send.send(str_setup_header.encode())
        msg_recv = self.socket_send.recv(self.buffer_len).decode()
        print("setup recv = \n", msg_recv)
        if msg_recv.find('200 OK') == -1:
            msg_recv_dict = msg_recv.split('\r\n')
            print('first SETUP request occur error: ')
            print(msg_recv_dict[0])
            return False
        else:
            print('SETUP is ok')
            session_pos = msg_recv.find('Session')
            session_value_begin_pos = msg_recv.find(' ', session_pos + 8) + 1
            session_value_end_pos = msg_recv.find(';', session_pos + 8)
            self.session = msg_recv[session_value_begin_pos:session_value_end_pos]
            return True

    def send_setup_session_and_recv(self):
        """封装发送setup,包含session,并接收应答函数"""
        self.cseq = self.cseq + 1
        str_setup_session_header = self.get_setup_session_header(self.url, self.realm_value, self.nonce_value,
                                                                 self.session)
        if self.header_normal_modify_allow & self.setup_session_header_modify:
            str_setup_session_header = self.add_normal_header_according_to_protocol(str_setup_session_header)
        elif self.header_overload_modify_allow & self.setup_session_header_modify:
            str_setup_session_header = self.add_overload_header_according_to_protocol(str_setup_session_header)
        self.socket_send.send(str_setup_session_header.encode())
        msg_recv = self.socket_send.recv(self.buffer_len).decode()
        print("setup session recv = ", msg_recv)
        if msg_recv.find('200 OK') == -1:
            msg_recv_dict = msg_recv.split('\r\n')
            print('SETUP session request occur error: ')
            print(msg_recv_dict[0])
            return False
        else:
            print('SETUP session is ok')
            session_pos = msg_recv.find('Session')
            session_value_begin_pos = msg_recv.find(' ', session_pos + 8) + 1
            session_value_end_pos = msg_recv.find(';', session_pos + 8)
            self.session = msg_recv[session_value_begin_pos:session_value_end_pos]
            return True

    def send_play_and_recv(self):
        """封装发送play并接收应答函数"""
        self.cseq = self.cseq + 1
        str_play_header = self.get_play_header(self.url, self.realm_value, self.nonce_value, self.session)
        if self.header_normal_modify_allow & self.play_header_modify:
            str_play_header = self.add_normal_header_according_to_protocol(str_play_header)
        elif self.header_overload_modify_allow & self.play_header_modify:
            str_play_header = self.add_overload_header_according_to_protocol(str_play_header)
        self.socket_send.send(str_play_header.encode())
        msg_recv = self.socket_send.recv(self.buffer_len).decode()
        print("play recv = \n", msg_recv)
        if msg_recv.find('200 OK') == -1:
            msg_recv_dict = msg_recv.split('\r\n')
            print('PLAY request occur error: ')
            print(msg_recv_dict[0])
            return False
        else:
            print('PLAY is ok')
            return True

    def send_get_parameter_and_recv(self):
        """封装发送get_parameter并接收应答函数"""
        self.cseq = self.cseq + 1
        str_get_parameter_header = self.get_get_parameter_header(self.url, self.realm_value, self.nonce_value,
                                                                 self.session)
        if self.header_normal_modify_allow & self.get_parameter_header_modify:
            str_get_parameter_header = self.add_normal_header_according_to_protocol(str_get_parameter_header)
        elif self.header_overload_modify_allow & self.get_parameter_header_modify:
            str_get_parameter_header = self.add_overload_header_according_to_protocol(str_get_parameter_header)
        self.socket_send.send(str_get_parameter_header.encode())
        msg_recv = self.socket_send.recv(self.buffer_len).decode()
        msg_recv_dict = msg_recv.split('\r\n')
        print("get parameter = \n", msg_recv)
        if msg_recv.find('200 OK') == -1:
            print("GET_PARAMETER is error")
            return False
        else:
            print("GET_PARAMETER is ok")
            print('*10:' + msg_recv_dict[0])
            return True

    def send_teardown_and_recv(self):
        """封装发送teardown并接收应答函数"""
        self.cseq = self.cseq + 1
        str_teardown_header = self.get_teardown_header(self.url, self.realm_value, self.nonce_value, self.session)
        if self.header_normal_modify_allow & self.teardown_header_modify:
            str_teardown_header = self.add_normal_header_according_to_protocol(str_teardown_header)
        elif self.header_overload_modify_allow & self.teardown_header_modify:
            str_teardown_header = self.add_overload_header_according_to_protocol(str_teardown_header)
        self.socket_send.send(str_teardown_header.encode())
        msg_recv = self.socket_send.recv(self.buffer_len).decode()
        print("teardown_recv = \n", msg_recv)
        if msg_recv.find('200 OK') == -1:
            print("TEARDOWN is error")
            return False
        else:
            print("TEARDOWN is ok")
            return True

    def recv_rtp_stream(self):
        """封装接收rtp数据流"""
        while self.rtp_recv_flag:
            data, client_addr = self.rtp_socket.recvfrom(self.buffer_len)
            self.rtp_socket.sendto(data.upper(), client_addr)
            if 0 < len(data):
                self.rtp_recv_flag = False
                break


class VlcPlayer:
    """
        args:设置 options
    """

    def __init__(self, *args):
        if args:
            instance = vlc.Instance(*args)
            self.media = instance.media_player_new()
        else:
            self.media = vlc.MediaPlayer()

    # 设置待播放的url地址或本地文件路径，每次调用都会重新加载资源
    def set_uri(self, uri):
        self.media.set_mrl(uri)

    # 播放 成功返回0，失败返回-1
    def play(self, path=None):
        if path:
            self.set_uri(path)
            return self.media.play()
        else:
            return self.media.play()

    # 暂停
    def pause(self):
        self.media.pause()

    # 恢复
    def resume(self):
        self.media.set_pause(0)

    # 停止
    def stop(self):
        self.media.stop()

    # 释放资源
    def release(self):
        return self.media.release()

    # 是否正在播放
    def is_playing(self):
        return self.media.is_playing()

    # 已播放时间，返回毫秒值
    def get_time(self):
        return self.media.get_time()

    # 拖动指定的毫秒值处播放。成功返回0，失败返回-1 (需要注意，只有当前多媒体格式或流媒体协议支持才会生效)
    def set_time(self, ms):
        return self.media.set_time(ms)

    # 音视频总长度，返回毫秒值
    def get_length(self):
        return self.media.get_length()

    # 获取当前音量（0~100）
    def get_volume(self):
        return self.media.audio_get_volume()

    # 设置音量（0~100）
    def set_volume(self, volume):
        return self.media.audio_set_volume(volume)

    # 返回当前状态：正在播放；暂停中；其他
    def get_state(self):
        state = self.media.get_state()
        if state == vlc.State.Playing:
            return 1
        elif state == vlc.State.Paused:
            return 0
        else:
            return -1

    # 当前播放进度情况。返回0.0~1.0之间的浮点数
    def get_position(self):
        return self.media.get_position()

    # 拖动当前进度，传入0.0~1.0之间的浮点数(需要注意，只有当前多媒体格式或流媒体协议支持才会生效)
    def set_position(self, float_val):
        return self.media.set_position(float_val)

    def get_fps(self):
        return self.media.get_fps()

    def get_stats(self, stat):
        return self.media.get_stats(stat)

    # 获取当前文件播放速率
    def get_rate(self):
        return self.media.get_rate()

    # 设置播放速率（如：1.2，表示加速1.2倍播放）
    def set_rate(self, rate):
        return self.media.set_rate(rate)

    # 设置宽高比率（如"16:9","4:3"）
    def set_ratio(self, ratio):
        self.media.video_set_scale(0)  # 必须设置为0，否则无法修改屏幕宽高
        self.media.video_set_aspect_ratio(ratio)

    # 注册监听器
    def add_callback(self, event_type, callback):
        self.media.event_manager().event_attach(event_type, callback, self)

    # 移除监听器
    def remove_callback(self, event_type, callback):
        self.media.event_manager().event_detach(event_type, callback, self)


def my_call_back(event, p_md):
    print("call:", p_md.get_time())


def check_rtsp_stream_alive(ip, chn='0', username=None, password=None, timesleep=3):
    """
    检测rtsp是否可通, 有的机型用这种方式setup时 [无法通过鉴权], 如S539.   有rtsp的rtp流发送.
    """
    # 2024.10.23 替换掉看看结果
    # if not username:
    #     cap = cv2.VideoCapture("rtsp://{}/live/ch00_{}".format(ip, chn))
    # else:
    #     cap = cv2.VideoCapture("rtsp://{}:{}@{}/live/ch00_{}".format(username, password, ip, chn))
    # ret = cap.isOpened()
    # time.sleep(timesleep)
    # cap.release()
    # return ret
    return check_rtsp_by_monitor(ip, username, password, chn)


def check_rtsp_by_monitor(ip, username=None, password=None, chn=0):
    """
    check_rtsp_stream_alive有的机型 如S539 不可用的时候替换这个,  有rtsp的rtp流发送.
    """
    for i in range(2):
        if username:
            md2 = vlc.MediaPlayer(r'rtsp://{}:{}@{}/live/ch00_{}'.format(username, password, ip, chn))
        else:
            md2 = vlc.MediaPlayer(r'rtsp://{}/live/ch00_{}'.format(ip, chn))
        md2.play()
        time.sleep(3)
        ret = md2.get_fps() > 0
        md2.stop()
        if ret:
            return ret
        else:
            if i == 0:
                time.sleep(10)
                continue
            else:
                return False


def get_rtsp_resolution(ip, chn='0', username=None, password=None):
    if not username:
        cap = cv2.VideoCapture("rtsp://{}/live/ch00_{}".format(ip, chn))
    else:
        cap = cv2.VideoCapture("rtsp://{}:{}@{}/live/ch00_{}".format(username, password, ip, chn))
    time.sleep(5)
    width = int(cap.get(3))
    height = int(cap.get(4))
    cap.release()
    del cap
    aklog_info('get rtsp resolution: {} x {}'.format(width, height))
    return width, height


def get_rtsp_framerate(ip, chn='0', username=None, password=None):
    if not username:
        cap = cv2.VideoCapture("rtsp://{}/live/ch00_{}".format(ip, chn))
    else:
        cap = cv2.VideoCapture("rtsp://{}:{}@{}/live/ch00_{}".format(username, password, ip, chn))
    time.sleep(5)
    framerate = int(cap.get(5))
    cap.release()
    del cap
    return framerate


def return_rtsp_connect_list(ip, chn_list, username=None, password=None):
    ret_list = []
    for chn in chn_list:
        try:
            if not username:
                cap = cv2.VideoCapture("rtsp://{}/live/ch00_{}".format(ip, chn))
                ret_list.append(cap)
            else:
                cap = cv2.VideoCapture("rtsp://{}:{}@{}/live/ch00_{}".format(username, password, ip, chn))
                ret_list.append(cap)
        except:
            aklog_printf('设备rtsp连接失败')
            ret_list.append(False)
    return ret_list


def stop_rtsp_connect_list(connect_list):
    for i in connect_list:
        if i is not False:
            i.release()


def vlc_monitor(ip, username='', password='', chn=0):
    """打开vlc监控rtsp, 有实际rtsp流, 用于抓包测试"""
    # 不在这里做导入, 工作目录被换了, 无法成功导入.
    try:
        if username:
            md = vlc.MediaPlayer(r'rtsp://{}:{}@{}/live/ch00_{}'.format(username, password, ip, chn))
        else:
            md = vlc.MediaPlayer(r'rtsp://{}/live/ch00_{}'.format(ip, chn))
        md.play()
        return md
    except:
        aklog_error('vlc 监控出现异常！！！！')
        print(traceback.format_exc())
        return False


def stop_vlc_monitor(vlc):
    """关闭vlc监控"""
    vlc.stop()


def vlc_play_rtsp_start(ip, username=None, password=None, chn=0):
    if username:
        url = 'rtsp://{}:{}@{}/live/ch00_{}'.format(username, password, ip, chn)
    else:
        url = 'rtsp://{}/live/ch00_{}'.format(ip, chn)
    player = VlcPlayer()
    player.play(url)
    return player


def vlc_play_rtsp_stop(p_md):
    p_md.stop()


def start_vlc_exe(ip, username='', password='', chn=0):
    """
    室内机rtsp没有视频, cv2无法使用. 阻塞5秒后自动关闭.
    """
    if username:
        url = r'rtsp://{}:{}@{}/live/ch00_{}'.format(username, password, ip, chn)
    else:
        url = r'rtsp://{}/live/ch00_{}'.format(ip, chn)

    if sys.version_info[0] > 2:
        PYTHON3 = True
    else:
        PYTHON3 = False
    if PYTHON3:
        import winreg as w
    else:
        import _winreg as w
    plugin_path = None
    for r in w.HKEY_LOCAL_MACHINE, w.HKEY_CURRENT_USER:
        try:
            r = w.OpenKey(r, 'Software\\VideoLAN\\VLC')
            plugin_path, _ = w.QueryValueEx(r, 'InstallDir')
            w.CloseKey(r)
            break
        except w.error:
            pass
    if not plugin_path and 'VLC' in os.environ.get('path'):
        for i in os.environ.get('path').split(';'):
            if '\\VLC' in i:
                plugin_path = i
                break
    if plugin_path:
        sub_process_get_output('"{}\\vlc.exe" -vvv {}'.format(plugin_path, url), timeout=5)
        cmd_close_process_by_name('vlc.exe')
    else:
        aklog_error('未找到vlc.exe路径')
        return False


def check_rtsp_service(host, port=554):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((host, port))
        return sock
    except:
        return False


def get_rtsp_stream_pic(savefile, ip, chn='0', username=None, password=None):
    """
    打开rtsp, 并截取一张图片
    """
    if not username:
        cap = cv2.VideoCapture("rtsp://{}/live/ch00_{}".format(ip, chn))
    else:
        cap = cv2.VideoCapture("rtsp://{}:{}@{}/live/ch00_{}".format(username, password, ip, chn))
    # 默认读取的是第一帧，会出现水印还没刷新出来的情况
    sleep(3)
    for _ in range(20):  # 读10帧
        ret, frame = cap.read()
    # 截取第11帧
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(savefile, frame)
        cap.release()
        return True
    else:
        cap.release()
        return False


if __name__ == '__main__':
    # p_md = vlc_monitor('192.168.88.189')
    # stop_vlc_monitor(p_md)
    player = VlcPlayer()
    # 在线播放流媒体视频
    player.play('rtsp://192.168.88.189:554/live/ch00_0')
    time.sleep(3)
    player.stop()
