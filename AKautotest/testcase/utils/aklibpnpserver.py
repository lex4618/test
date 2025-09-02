# -*- coding: UTF-8 -*-

import sys
import os
import time
import socket, threading
import traceback
import re

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *

globaldata = ''
globaladdr = ''
globalstate = True

def start_pnpserver(clientip, url):
    group_ip = '224.0.1.75'
    pnp_port = 5060
    cur_time = time.time()

    def test():
        global globaladdr, globaldata, globalstate
        try:
            pc_ip = get_local_host_ip()
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client.bind(("", pnp_port))
            client.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                              socket.inet_aton(group_ip) + socket.inet_aton(pc_ip))
            client.settimeout(600)
            while globalstate and time.time() - cur_time < 600:
                data, addr = client.recvfrom(1024)
                request_full_uri = data.decode().splitlines()[0]
                device_mac = re.search('MAC(.*)@', request_full_uri).group(1)
                if addr[0] == clientip and 'SUBSCRIBE' in request_full_uri:
                    aklog_printf('get PNP subscribe data from %s' % clientip)
                    pnp_server_response(device_mac, addr[0], pc_ip, url)
                    globaldata = data
                    return data
            aklog_printf('pnp环境未能成功')
        except:
            if time.time() - cur_time < 100:
                aklog_error('pnp环境启动异常')
                aklog_printf(traceback.format_exc())
            else:
                aklog_printf('pnp环境10分钟后关闭')
            return False

    a = threading.Thread(target=test)
    a.daemon = True
    a.start()


def stop_pnpserver():
    global globalstate
    globalstate = False


def pnp_server_response(mac, ip, pcip, url):
    aklog_info('pnp 服务器正常回复 -> {} '.format(ip))

    data = """NOTIFY sip:MAC{0}@192.168.3.7:5060 SIP/2.0
Via: SIP/2.0/UDP 192.168.10.110:5060;rport;branch=z9hG4bKEPSVBUS3fcfa055-1005-438f-a81d-633853f528dd
To: <sip:MAC{1}@224.0.1.75>;tag=325885303
From: <sip:MAC{2}224.0.1.75>;tag=141197489959ec9930-1005-4985-8cb0-65be66b35cc6
CSeq: 869 NOTIFY
Call-ID: 1147221869
Contact: <sip:{3}:5060>
Content-Type: application/url
User-Agent: Epygi Quadro SIP User Agent/v5.2.48 (QUADRO-2X)
Max-Forwards: 70
Event: ua-profile;profile-type="device";vendor="Akuvox";model="R20K";version="220.30.3.1"
Subscription-State: terminated;reason=timeout
Content-Length: {4}

{5}
    """.format(mac, mac, mac, pcip, len(url), url)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.sendto(data.encode(), (ip, 5060))

