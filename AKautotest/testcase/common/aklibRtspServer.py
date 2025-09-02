import socket
import hashlib
import base64
import time
import threading
import time
import inspect
import ctypes
from random import *

class RtspServer():

    def __init__(self, username="admin", password="admin", port=554):
        '''构造函数，初始化Rtsp变量，进行socket连接操作'''
        self.server_username = username                                        # RTSP用户名
        self.server_password = password                                        # RTSP密码
        self.server_port = port                                                # RTSP服务器使用端口
        self.cseq = 1                                                          # RTSP使用的请求起始序列码，不需要改动
        self.rtp_port = 60000
        self.rtcp_port = 60001
        self.client_rtp_port = 0
        self.client_rtcp_port = 0
        self.session_id = ""
        self.buffer_len = 8000                                                 # 用于接收服务器返回数据的缓冲区的大小
        self.socket_server = 0
        self.send_data_type = 0
        #创建Rtsp连接
        self._hostname = socket.gethostname()  # 获取主机名
        self._host_ip = socket.gethostbyname(self._hostname)  # 获取本机IP
        self.thread = 0

    def __del__(self):
        '''析构函数，关闭socket连接操作'''
        if self.socket_server.fileno() > 0:
            self.socket_server.close()

    def set_send_data_type(self, type):
        '''设置发送包，是正序还是乱序'''
        if type != 0 and type != 1 and type != 2:
            print("请正确设置RTSP包，设置0为正序，1为乱序，2为加长包")
            return False
        self.send_data_type = type
        return True

    def get_send_data_type(self):
        '''获取发送包，正序乱序类型'''
        return self.send_data_type

    def create_rtsp_server(self):
        '''创建socket, rtsp server线程'''
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_server.bind((self._host_ip, self.server_port))
        self.socket_server.listen(1)
        self.thread = threading.Thread(target=self.rtsp_server_thread, args=())
        self.thread.daemon = True
        self.thread.start()

    def rtsp_server_thread(self):
        '''rtsp server阻塞线程'''
        while True:
            client_socket, ip_port = self.socket_server.accept()  # 接受连接，获取连接对象
            while True:
                if client_socket:
                    recv_msg = client_socket.recv(self.buffer_len).decode('utf-8', 'ignore')
                    if recv_msg != "":
                        print("recv_msg = ", recv_msg)
                        if self.get_send_data_type() == 1:
                            send_msg = self.parse_msg_and_packet_error_data(recv_msg)
                        elif self.get_send_data_type() == 0:
                            send_msg = self.parse_msg_and_packet(recv_msg)
                        elif self.get_send_data_type() == 2:
                            send_msg = self.parse_msg_and_packet_long_data(recv_msg)

                        if send_msg != None:
                            print("send_msg = ", send_msg)
                            client_socket.send(send_msg.encode('gbk'))
                    else:
                        break

    def _async_raise(self, tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def stop_thread(self):
        '''结束线程'''
        self._async_raise(self.thread.ident, SystemExit)

    def parse_msg_and_packet(self, recv_msg):
        '''解析接收rtsp client的请求, 并且打包应答包'''
        list_tmp = recv_msg.split('\n')
        for string in list_tmp:
            if "CSeq: " in string:
                self.cseq = int(string.split("CSeq: ")[1].split('\r')[0])
            if "client_port" in string:
                port_list = string.split("client_port=")[1].split('\r')[0].split('-')
                self.client_rtp_port = int(port_list[0])
                self.client_rtcp_port = int(port_list[1])
                print("client_rtp_port = ", self.client_rtp_port)
                print("client_rtcp_port = ", self.client_rtcp_port)
        if "OPTIONS" in recv_msg:
            send_msg = ("RTSP/1.0 200 OK\r\nCSeq: %d\r\nServer: Easy Rtsp 1.0\r\nPublic: DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE, SET_PARAMETER, GET_PARAMETER\r\n\r\n" % self.cseq)
            return send_msg
        elif "DESCRIBE" in recv_msg:
            sdp_str = "v=0\r\no=- 1 1 IN IP4 127.0.0.1\r\ns=Easy Rtsp 1.0\r\ni=Easy\r\nc=IN IP4 0.0.0.0\r\nt=0 0\r\nm=video 0 RTP/AVP 96\r\nb=AS:5000\r\na=rtpmap:96 H264/90000\r\na=fmtp:96 profile-level-id=4D401F;packetization-mode=1;sprop-parameter-sets=Z01AH52oFAFuhAAAAwAEAAADAMoQ,aO48gA==\r\na=control:trackID=0\r\nm=audio 0 RTP/AVP 0\r\na=rtpmap:0 PCMU/8000\r\na=ptime:20\r\na=control:trackID=1\r\n"
            send_msg = "RTSP/1.0 200 OK\r\nCSeq: %d\r\nServer: Streaming Server v0.1\r\nContent-Base: rtsp://%s:554/live/ch00_0/\r\nContent-Type: application/sdp\r\nContent-Length: %d\r\n\r\n%s" % (self.cseq, self._host_ip, len(sdp_str), sdp_str)
            return send_msg
        elif "SETUP" in recv_msg:
            self.session_id = "".join([choice("0123456789ABCDEF") for i in range(20)])
            send_msg = "RTSP/1.0 200 OK\r\nCSeq: %d\r\nCache-Control: no-cache\r\nTransport: RTP/AVP;unicast;mode=play;client_port=%d-%d;server_port=%d-%d\r\nSession: %s\r\n\r\n" % (self.cseq, self.client_rtcp_port, self.client_rtp_port, self.rtcp_port, self.rtp_port, self.session_id)
            return send_msg
        elif "PLAY" in recv_msg:
            send_msg = "RTSP/1.0 200 OK\r\nCSeq: %d\r\nSession: %s\r\nRange: npt=now-\r\nRTP-Info: url=rtsp://%s:554/live/ch00_0//trackID=0;seq=0;rtptime=0\r\n\r\n" % (self.cseq, self.session_id, self._host_ip)
            return send_msg
        elif "GET_PARAMETER" in recv_msg:
            time_str = time.strftime('%a %b %d %H:%M:%S %Y', time.localtime(time.time()))
            send_msg = "RTSP/1.0 200 OK\r\nCSeq: %d\r\nDate: %s\r\n\r\n" % (self.cseq, time_str)
            return send_msg
        elif "TEARDOWN" in recv_msg:
            send_msg = "RTSP/1.0 200 OK\r\nCSeq: %d\r\n\r\n" % (self.cseq)
            return send_msg

    def parse_msg_and_packet_error_data(self, recv_msg):
        '''解析接收rtsp client的请求, 并且打包应答包,应答包内容为错误格式的包'''
        list_tmp = recv_msg.split('\n')
        for string in list_tmp:
            if "CSeq: " in string:
                self.cseq = int(string.split("CSeq: ")[1].split('\r')[0])
            if "client_port" in string:
                port_list = string.split("client_port=")[1].split('\r')[0].split('-')
                self.client_rtp_port = int(port_list[0])
                self.client_rtcp_port = int(port_list[1])
                print("client_rtp_port = ", self.client_rtp_port)
                print("client_rtcp_port = ", self.client_rtcp_port)

        str_response = "RTSP/1.0 200 OK\r\n"
        str_cseq = "CSeq: %d\r\n" % self.cseq
        if "OPTIONS" in recv_msg:
            list_method = ["DESCRIBE", "SETUP", "TEARDOWN", "PLAY", "PAUSE", "SET_PARAMETER", "GET_PARAMETER"]
            shuffle(list_method)
            str_public = "Public: "
            for i in range(len(list_method)):
                if i != len(list_method)-1:
                    str_public += list_method[i]
                    str_public += ", "
                else:
                    str_public += list_method[i]
                    str_public += "\r\n"
            list_send = [str_cseq, "Server: Easy Rtsp 1.0\r\n", str_public]
            shuffle(list_send)
            send_msg = str_response
            for string in list_send:
                send_msg += string
            send_msg += "\r\n"
            #send_msg = ("Public: DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE, SET_PARAMETER, GET_PARAMETER\r\n\r\n" % self.cseq)
            return send_msg

        elif "DESCRIBE" in recv_msg:
            #sdp_str = "v=0\r\no=- 1 1 IN IP4 127.0.0.1\r\ns=Easy Rtsp 1.0\r\ni=Easy\r\nc=IN IP4 0.0.0.0\r\nt=0 0\r\nm=video 0 RTP/AVP 96\r\nb=AS:5000\r\na=rtpmap:96 H264/90000\r\na=fmtp:96 profile-level-id=4D401F;packetization-mode=1;sprop-parameter-sets=Z01AH52oFAFuhAAAAwAEAAADAMoQ,aO48gA==\r\na=control:trackID=0\r\nm=audio 0 RTP/AVP 0\r\na=rtpmap:0 PCMU/8000\r\na=ptime:20\r\na=control:trackID=1\r\n"
            #乱序sdp_video
            str_video_sdp = "m=video 0 RTP/AVP 96\r\nb=AS:5000\r\n"
            list_video_sdp = ["b=AS:5000\r\n", "a=rtpmap:96 H264/90000\r\n", "a=fmtp:96 profile-level-id=4D401F;packetization-mode=1;sprop-parameter-sets=Z01AH52oFAFuhAAAAwAEAAADAMoQ,aO48gA==\r\n", "a=control:trackID=0\r\n"]
            shuffle(list_video_sdp)
            for string in list_video_sdp:
                str_video_sdp += string

            #乱序sdp_audio
            str_audio_sdp = "m=audio 0 RTP/AVP 0\r\n"
            list_audio_sdp = ["a=rtpmap:0 PCMU/8000\r\n", "a=ptime:20\r\n", "a=control:trackID=1\r\n"]
            shuffle(list_audio_sdp)
            for string in list_audio_sdp:
                str_audio_sdp += string

            #乱序整个sdp
            list_sdp = ["v=0\r\n", "o=- 1 1 IN IP4 127.0.0.1\r\n", "s=Easy Rtsp 1.0\r\n", "i=Easy\r\n", "c=IN IP4 0.0.0.0\r\n", "t=0 0\r\n", str_video_sdp, str_audio_sdp]
            shuffle(list_sdp)
            sdp_str = ""
            for string in list_sdp:
                sdp_str += string

            #乱序rtsp
            list_send = [str_cseq, "Server: Streaming Server v0.1\r\n", "Content-Base: rtsp://%s:554/live/ch00_0/\r\n" % self._host_ip, "Content-Type: application/sdp\r\n", "Content-Length: %d\r\n" % len(sdp_str)]
            shuffle(list_send)
            send_msg = str_response
            for string in list_send:
                send_msg += string
            send_msg += "\r\n"
            send_msg += sdp_str
            return send_msg

        elif "SETUP" in recv_msg:
            #乱序Transport, Transport: RTP/AVP必须置于数据库前端
            list_transport = ["unicast", "mode=play", "client_port=%d-%d" % (self.client_rtp_port, self.client_rtcp_port), "server_port=%d-%d" % (self.rtp_port, self.rtcp_port)]
            str_transport = "Transport: RTP/AVP;"
            shuffle(list_transport)
            for i in range(len(list_transport)):
                if i != len(list_transport) - 1:
                    str_transport += list_transport[i]
                    str_transport += ";"
                else:
                    str_transport += list_transport[i]
                    str_transport += "\r\n"

            # 乱序rtsp
            self.session_id = "".join([choice("0123456789ABCDEF") for i in range(20)])
            list_send = [str_cseq, str_transport, "Session: %s\r\n" % self.session_id]
            shuffle(list_send)
            send_msg = str_response
            for string in list_send:
                send_msg += string
            send_msg += "\r\n"
            return send_msg

        elif "PLAY" in recv_msg:
            list_send = [str_cseq, "Session: %s\r\n" % self.session_id, "Range: npt=now-\r\n", "RTP-Info: url=rtsp://%s:554/live/ch00_0//trackID=0;seq=0;rtptime=0\r\n" % self._host_ip]
            shuffle(list_send)
            send_msg = str_response
            for string in list_send:
                send_msg += string
            send_msg += "\r\n"
            return send_msg

        elif "GET_PARAMETER" in recv_msg:
            time_str = time.strftime('%a %b %d %H:%M:%S %Y', time.localtime(time.time()))
            list_send = [str_cseq, "Date: %s\r\n" % time_str]
            shuffle(list_send)
            send_msg = str_response
            for string in list_send:
                send_msg += string
            send_msg += "\r\n"
            return send_msg

        elif "TEARDOWN" in recv_msg:
            send_msg = "RTSP/1.0 200 OK\r\nCSeq: %d\r\n\r\n" % (self.cseq)
            return send_msg

    def parse_msg_and_packet_long_data(self, recv_msg):
        '''解析接收rtsp client的请求, 并且打包应答包,应答包内容为超长内容格式的包'''
        list_tmp = recv_msg.split('\n')
        for string in list_tmp:
            if "CSeq: " in string:
                self.cseq = int(string.split("CSeq: ")[1].split('\r')[0])
            if "client_port" in string:
                port_list = string.split("client_port=")[1].split('\r')[0].split('-')
                self.client_rtp_port = int(port_list[0])
                self.client_rtcp_port = int(port_list[1])
                print("client_rtp_port = ", self.client_rtp_port)
                print("client_rtcp_port = ", self.client_rtcp_port)

        str_response = "RTSP/1.0 200 OK\r\n"
        str_cseq = "CSeq: %d\r\n" % self.cseq
        if "OPTIONS" in recv_msg:
            list_method = ["DESCRIBE", "SETUP", "TEARDOWN", "PLAY", "PAUSE", "SET_PARAMETER", "GET_PARAMETER"]
            shuffle(list_method)
            str_public = "Public: "
            for i in range(len(list_method)):
                if i != len(list_method)-1:
                    str_public += list_method[i]
                    str_public += ", "
                else:
                    str_public += list_method[i]
                    str_public += "\r\n"
            list_send = [str_cseq, "Server: Easy Rtsp 1.0\r\n", str_public]
            shuffle(list_send)
            send_msg = str_response
            for string in list_send:
                send_msg += string
            send_msg += "\r\n111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111123111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111231111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111"
            #send_msg = ("Public: DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE, SET_PARAMETER, GET_PARAMETER\r\n\r\n" % self.cseq)
            return send_msg

        elif "DESCRIBE" in recv_msg:
            #sdp_str = "v=0\r\no=- 1 1 IN IP4 127.0.0.1\r\ns=Easy Rtsp 1.0\r\ni=Easy\r\nc=IN IP4 0.0.0.0\r\nt=0 0\r\nm=video 0 RTP/AVP 96\r\nb=AS:5000\r\na=rtpmap:96 H264/90000\r\na=fmtp:96 profile-level-id=4D401F;packetization-mode=1;sprop-parameter-sets=Z01AH52oFAFuhAAAAwAEAAADAMoQ,aO48gA==\r\na=control:trackID=0\r\nm=audio 0 RTP/AVP 0\r\na=rtpmap:0 PCMU/8000\r\na=ptime:20\r\na=control:trackID=1\r\n"
            #乱序sdp_video
            str_video_sdp = "m=video 0 RTP/AVP 96\r\nb=AS:5000\r\n"
            list_video_sdp = ["b=AS:5000\r\n", "a=rtpmap:96 H264/90000\r\n", "a=fmtp:96 profile-level-id=4D401F;packetization-mode=1;sprop-parameter-sets=Z01AH52oFAFuhAAAAwAEAAADAMoQ,aO48gA==\r\n", "a=control:trackID=0\r\n"]
            shuffle(list_video_sdp)
            for string in list_video_sdp:
                str_video_sdp += string

            #乱序sdp_audio
            str_audio_sdp = "m=audio 0 RTP/AVP 0\r\n"
            list_audio_sdp = ["a=rtpmap:0 PCMU/8000\r\n", "a=ptime:20\r\n", "a=control:trackID=1\r\n"]
            shuffle(list_audio_sdp)
            for string in list_audio_sdp:
                str_audio_sdp += string

            #乱序整个sdp
            list_sdp = ["v=0\r\n", "o=- 1 1 IN IP4 127.0.0.1\r\n", "s=Easy Rtsp 1.0\r\n", "i=Easy\r\n", "c=IN IP4 0.0.0.0\r\n", "t=0 0\r\n", str_video_sdp, str_audio_sdp]
            shuffle(list_sdp)
            sdp_str = ""
            for string in list_sdp:
                sdp_str += string

            #乱序rtsp
            list_send = [str_cseq, "Server: Streaming Server v0.1\r\n", "Content-Base: rtsp://%s:554/live/ch00_0/\r\n" % self._host_ip, "Content-Type: application/sdp\r\n", "Content-Length: %d\r\n" % len(sdp_str)]
            shuffle(list_send)
            send_msg = str_response
            for string in list_send:
                send_msg += string
            send_msg += "\r\n111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111123111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111231111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111"
            send_msg += sdp_str
            return send_msg

        elif "SETUP" in recv_msg:
            #乱序Transport, Transport: RTP/AVP必须置于数据库前端
            list_transport = ["unicast", "mode=play", "client_port=%d-%d" % (self.client_rtp_port, self.client_rtcp_port), "server_port=%d-%d" % (self.rtp_port, self.rtcp_port)]
            str_transport = "Transport: RTP/AVP;"
            shuffle(list_transport)
            for i in range(len(list_transport)):
                if i != len(list_transport) - 1:
                    str_transport += list_transport[i]
                    str_transport += ";"
                else:
                    str_transport += list_transport[i]
                    str_transport += "\r\n"

            # 乱序rtsp
            self.session_id = "".join([choice("0123456789ABCDEF") for i in range(20)])
            list_send = [str_cseq, str_transport, "Session: %s\r\n" % self.session_id]
            shuffle(list_send)
            send_msg = str_response
            for string in list_send:
                send_msg += string
            send_msg += "\r\n111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111123111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111231111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111"
            return send_msg

        elif "PLAY" in recv_msg:
            list_send = [str_cseq, "Session: %s\r\n" % self.session_id, "Range: npt=now-\r\n", "RTP-Info: url=rtsp://%s:554/live/ch00_0//trackID=0;seq=0;rtptime=0\r\n" % self._host_ip]
            shuffle(list_send)
            send_msg = str_response
            for string in list_send:
                send_msg += string
            send_msg += "\r\n111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111123111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111231111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111"
            return send_msg

        elif "GET_PARAMETER" in recv_msg:
            time_str = time.strftime('%a %b %d %H:%M:%S %Y', time.localtime(time.time()))
            list_send = [str_cseq, "Date: %s\r\n" % time_str]
            shuffle(list_send)
            send_msg = str_response
            for string in list_send:
                send_msg += string
            send_msg += "\r\n111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111123111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111231111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111"
            return send_msg

        elif "TEARDOWN" in recv_msg:
            send_msg = "RTSP/1.0 200 OK\r\nCSeq: %d\r\n\r\n111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111123111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111231111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112311111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111" % (self.cseq)
            return send_msg

if __name__ == '__main__':
    rtsp_server = RtspServer("admin", "admin")
    rtsp_server.set_send_data_type(2)
    rtsp_server.create_rtsp_server()
    while True:
        time.sleep(1)

