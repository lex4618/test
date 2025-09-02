# -*- coding: UTF-8 -*-

import sys
import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")

if pos == -1:
    print("runtime error")
    exit(1)

root_path = root_path[0:pos + len("AKautotest")]

sys.path.append(root_path)


def check_snmp_connect_state(ip, port, model=1):
    # 检查SNMP 链接状态
    # model: 1   SNMP_V2
    # model: 0   SNMP_V1
    from pysnmp.entity.rfc3413.oneliner import cmdgen
    import pysnmp

    check_id = '1.3.6.1.2.1.37459.2.1.5.0'
    cg = cmdgen.CommandGenerator()
    var_1 = cmdgen.CommunityData('my-agent', 'public', model)
    var_2 = cmdgen.UdpTransportTarget((ip, port))
    result = cg.getCmd(var_1, var_2, check_id)
    return not isinstance(result[0], pysnmp.proto.errind.RequestTimedOut)
