# -*- coding: UTF-8 -*-
import os
import io
import sys
import os
import socket

root_path = os.getcwd();
pos = root_path.find("AKautotest");

if pos == -1 :
    print("runtime error");
    exit(1);
    
root_path = root_path[0:pos+len("AKautotest")]

sys.path.append(root_path)    
    
import akcommon_define
from akcommon_define import *

#### source code ######

def is_valid_version(rom_version):
    
    return True;
    
#支持ipv4和ipv6的地址检查
def is_valid_ip(ip):
    if not ip or '\x00' in ip:
        return False
    try:
        res = socket.getaddrinfo(ip, 0, socket.AF_UNSPEC,
                                 socket.SOCK_STREAM,
                                 0, socket.AI_NUMERICHOST)
        return bool(res)
    except socket.gaierror as e:
        if e.args[0] == socket.EAI_NONAME:
            return False
        raise
    return True;
