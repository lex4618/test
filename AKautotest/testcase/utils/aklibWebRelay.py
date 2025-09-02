# -*- coding: utf-8 -*-

import socket
import time
import threading
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import base64

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
if root_path not in sys.path:
    sys.path.append(root_path)

from akcommon_define import *


class WebRelayResponse_401(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(401)
        self.send_header('Content-type', 'text/html')
        self.send_header('WWW-Authenticate', 'Basic realm=secure_control')
        self.end_headers()
        data = r'<HTML><HEAD><TITLE>XYTRONIX Relay</TITLE></HEAD><BODY><H2>HTTP 1.0 401 Error. Authentication ' \
               r'Required</H2>The requested URL requires a username and password.<HR><BR><I>CBW Web ' \
               r'Server<BR></BODY></HTML> '
        self.wfile.write(data.encode())


class WebRelayResponse_403(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(403)
        self.send_header('Content-type', 'text/html')
        self.send_header('WWW-Authenticate', 'Basic realm=secure_control')
        self.end_headers()
        data = r'<HTML><HEAD><TITLE>XYTRONIX Relay</TITLE></HEAD><BODY><H2>HTTP 1.0 403 forbidden' \
               r'</H2>The requested URL requires a username and password.<HR><BR><I>CBW Web ' \
               r'Server<BR></BODY></HTML> '
        self.wfile.write(data.encode())


class WebRelayResponse_200(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('WWW-Authenticate', 'Basic realm=secure_control')
        self.end_headers()
        data = r'<HTML><HEAD><TITLE>XYTRONIX Relay</TITLE></HEAD><BODY><H2>HTTP 1.0 200 OK' \
               r'</H2>The requested URL requires a username and password.<HR><BR><I>CBW Web ' \
               r'Server<BR></BODY></HTML> '
        self.wfile.write(data.encode())


class WebRelayResponseHandler(BaseHTTPRequestHandler):
    """
    该响应会根据接收到的认证信息是否正确，来回复200OK或者401 Unauthorized，
    可以调用set_authorization方法设置用户名密码，默认为admin,admin，目前只支持Basic认证方式
    """
    user = 'admin'
    password = 'admin'

    @classmethod
    def set_authorization(cls, user, password):
        cls.user = user
        cls.password = password

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('WWW-Authenticate', 'Basic realm="secure_control"')
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="secure_control"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        """ Present frontpage with user authentication. """
        # 获取http.client发送过来的header鉴权信息，并判断鉴权信息是否正确，然后再返回对应的值
        if self.headers.get('Authorization') is None:
            self.do_AUTHHEAD()
            data = '<HTML><HEAD><TITLE>Web Relay</TITLE></HEAD><BODY><H2>HTTP 1.0 401 Unauthorized' \
                   'Required</H2>The requested URL requires a username and password.<HR><BR><I>CBW Web ' \
                   'Server<BR></BODY></HTML> '
            self.wfile.write(data.encode())
            return False
        auth_info = '%s:%s' % (self.user, self.password)
        auth_info = base64.b64encode(auth_info.encode('utf-8')).decode('utf-8')
        if self.headers.get('Authorization') == 'Basic %s' % auth_info:
            self.do_HEAD()
            data_200OK = '<HTML><HEAD><TITLE>Web Relay</TITLE></HEAD><BODY><H2>HTTP 1.0 200 OK' \
                         '</H2>Open Relay Success.<HR><BR><I>CBW Web Server<BR></BODY></HTML> '
            self.wfile.write(data_200OK.encode('utf-8'))
            return True
        else:
            self.do_AUTHHEAD()
            data = '<HTML><HEAD><TITLE>Web Relay</TITLE></HEAD><BODY><H2>HTTP 1.0 401 Unauthorized' \
                   'Required</H2>The requested URL requires a username and password.<HR><BR><I>CBW Web ' \
                   'Server<BR></BODY></HTML> '
            self.wfile.write(data.encode())
            return False


class WebRelay(object):
    def __init__(self, response, host_ip='0.0.0.0', port=80, user='admin', password='admin'):
        self.__host_ip = host_ip
        self.__port = port
        self.__host = (host_ip, port)
        if hasattr(response, 'set_authorization'):
            response.set_authorization(user, password)  # 设置web server认证用户名密码
        self.__server = HTTPServer(self.__host, response)

    def serve_forever(self):
        """启动server"""
        aklog_printf("Start WebRelay Server, listen at: %s:%s" % self.__host)
        self.__server.serve_forever()

    def server_start(self, auto_close=True, timeout=10):
        """创建子线程运行HTTP server，然后再创建一个子线程等待超时关闭HTTP server"""
        thread1 = threading.Thread(target=self.serve_forever)
        thread1.daemon = True
        thread1.start()
        # 等待HTTP Server启动成功，监听端口
        for i in range(5):
            ret = sub_process_get_output('netstat -ano | findstr "LISTENING" | findstr "%s:%s"' % self.__host)
            if ret:
                aklog_printf(ret)
                time.sleep(1)
                break
            elif i == 4:
                aklog_printf('WebRelay Server Start Failed')
                break
            else:
                aklog_printf('WebRelay Server Starting')
                time.sleep(2)
                continue
        # 再创建一个子线程等待超时关闭HTTP server
        if auto_close:
            thread2 = threading.Thread(target=self.server_close, args=(thread1, timeout))
            thread2.daemon = True
            thread2.start()

    def server_close(self, thread=None, timeout=None):
        """判断server是否还在运行，如果还在运行超时时间结束后关闭server"""
        if thread and timeout:
            for i in range(int(timeout)):
                if thread.is_alive():
                    time.sleep(1)
                    # aklog_printf('server is running')
                else:
                    aklog_printf('The server has been shut down')
                    return

        aklog_printf('Stop WebRelay Server')
        self.__server.shutdown()
        self.__server.server_close()


if __name__ == '__main__':
    print('调试')

    web_relay = WebRelay(WebRelayResponse_200, host_ip='0.0.0.0', port=20080, user='test', password='test')
    web_relay.server_start(timeout=20)
    time.sleep(5)
    web_relay.server_close()
    time.sleep(5)
