# -*- coding: UTF-8 -*-
import threading
import time

try:
    from onvif import ONVIFCamera
except:
    pass
import traceback
import sys
import os
import socket

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)
from akcommon_define import *


def onvif_check_discoverable(ip, user='admin', password='Aa12345678'):
    """
    返回指定设备是否可以被onvif发现, 用于测试discoverable功能.
    915: 关闭以后, 不会被扫描到, 手动添加仍可以onvif使用, onvif_get_device_info也能用. (justa说)
    r20: 关闭以后, 不会被扫描到, 相当于把onvif功能整个关闭了.
    """
    ret = sub_process_get_output(f'onvif-cli devicemgmt GetDiscoveryMode --user {user} --password {password} --host {ip}', timeout=5)
    if not ret:
        onvif_get_scan_return_ip()
        time.sleep(1)
        onvif_send_scan_packet(ip)
        time.sleep(5)
        return ip in global_onvif_discoverable_list
    else:
        if 'Unknown fault occured' in ret:
            return False
        return 'NonDiscoverable' not in ret


def onvif_get_device_info(ip, onvifusername, onvifpassword):
    """
    1. 通过true false判断设备是否onvif可连接
    2. 返回设备信息: {
    'Manufacturer': 'Akuvox',
    'Model': 'R20K',
    'FirmwareVersion': '320.30.10.6',
    'SerialNumber': '320.0',
    'HardwareId': 'A81518230417'
}
    """
    aklog_info()
    try:
        retdict = {}
        a = ONVIFCamera(ip, 80, onvifusername, onvifpassword)
        d = a.create_devicemgmt_service()
        d.create_type('GetDeviceInformation')
        aklog_debug(d.GetDeviceInformation())
        ret = d.GetDeviceInformation()
        retdict['FirmwareVersion'] = ret.FirmwareVersion
        retdict['HardwareId'] = ret.HardwareId
        retdict['Manufacturer'] = ret.Manufacturer
        retdict['Model'] = ret.Model
        retdict['SerialNumber'] = ret.SerialNumber
        return retdict
    except:
        aklog_error('设备onvif鉴权错误或未开启')
        aklog_debug(traceback.format_exc())
        return False


def onvif_get_media(ip, onvifusername, onvifpassword):
    aklog_info()
    try:
        a = ONVIFCamera(ip, 80, onvifusername, onvifpassword)
        d = a.create_media_service()
        params = d.create_type('GetProfile')
        params.ProfileToken = 'Profile_Token'
        retinfo = d.GetProfile(params)
        retdict = {}
        retdict['codec'] = retinfo.VideoEncoderConfiguration.Encoding
        retdict['height'] = retinfo.VideoEncoderConfiguration.Resolution.Height
        retdict['width'] = retinfo.VideoEncoderConfiguration.Resolution.Width
        retdict['framerate'] = retinfo.VideoEncoderConfiguration.RateControl.FrameRateLimit
        retdict['bitrate'] = retinfo.VideoEncoderConfiguration.RateControl.BitrateLimit
        return retdict
    except:
        aklog_error('设备onvif鉴权错误或未开启')
        aklog_debug(traceback.format_exc())
        return False


def onvif_set_media(ip, onvifusername, onvifpassword, width=1280, height=720):
    """
    onvif上设置stream video
    """
    for i in range(2):
        try:
            a = ONVIFCamera(ip, 80, onvifusername, onvifpassword)
            d = a.create_media_service()
            params = d.create_type('SetVideoEncoderConfiguration')
            if i == 0:
                params.Configuration = {'Name': 'VE_Name', 'token': 'VEC_Token', 'UseCount': 1, 'Encoding': 'H264',
                                        'Resolution': {'Width': width, 'Height': height}, 'Quality': 3,
                                        'RateControl': {'FrameRateLimit': 30, 'EncodingInterval': 1,
                                                        'BitrateLimit': 2048},
                                        'Multicast': {'Address': {'Type': 'IPv4', 'IPv4Address': "0.0.0.0"},
                                                      'Port': 0,
                                                      'TTL': 0,
                                                      'AutoStart': 'false'},
                                        'SessionTimeout': 'PT10S'}
            else:
                params.Configuration = {'Name': 'VE_Name', 'token': 'VEC_Token', 'UseCount': 1, 'Encoding': 'H264',
                                        'Resolution': {'Width': width, 'Height': height}, 'Quality': 3,
                                        'RateControl': {'FrameRateLimit': 30, 'EncodingInterval': 1,
                                                        'BitrateLimit': 2048},
                                        'H264': {
                                            'GovLength': 30,
                                            'H264Profile': 'Baseline'},
                                        'Multicast': {'Address': {'Type': 'IPv4', 'IPv4Address': "0.0.0.0"},
                                                      'Port': 0,
                                                      'TTL': 0,
                                                      'AutoStart': 'false'},
                                        'SessionTimeout': 'PT10S'}
            params.ForcePersistence = 'true'
            d.SetVideoEncoderConfiguration(params)
        except:
            if i == 1:
                aklog_error('设备onvif鉴权错误或未开启1')
                aklog_debug(traceback.format_exc())
                return False
            else:
                continue


def onvif_trigger_relay(ip, relay, onvifusername, onvifpassword):
    """
    milestone enabled配置测试, 触发onvif方式开启relay
    """
    try:
        a = ONVIFCamera(ip, 80, onvifusername, onvifpassword)
        d = a.create_devicemgmt_service()
        params = d.create_type('SetRelayOutputState')
        params.RelayOutputToken = 'Relay' + relay
        params.LogicalState = 'active'
        d.SetRelayOutputState(params)
    except:
        aklog_error('设备onvif鉴权错误或未开启')
        aklog_debug(traceback.format_exc())


global_onvif_discoverable_list = []
onvif_random_port = 3702


def onvif_send_scan_packet(ip):
    global global_onvif_discoverable_list
    global_onvif_discoverable_list = []
    server_ip = ip
    server_port = 3702
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', onvif_random_port))
    try:
        message1 = '<?xml version="1.0" encoding="utf-8"?><Envelope xmlns:tds="http://www.onvif.org/ver10/device/wsdl" xmlns="http://www.w3.org/2003/05/soap-envelope"><Header><wsa:MessageID xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">uuid:5df83ec3-6346-43ac-a324-c16a16bd08d5</wsa:MessageID><wsa:To xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To><wsa:Action xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action></Header><Body><Probe xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery"><Types>tds:Device</Types><Scopes /></Probe></Body></Envelope>'
        message2 = '<?xml version="1.0" encoding="utf-8"?><Envelope xmlns:dn="http://www.onvif.org/ver10/network/wsdl" xmlns="http://www.w3.org/2003/05/soap-envelope"><Header><wsa:MessageID xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">uuid:242d4eab-329e-438f-9cea-dca58f77d52c</wsa:MessageID><wsa:To xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To><wsa:Action xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action></Header><Body><Probe xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery"><Types>dn:NetworkVideoTransmitter</Types><Scopes /></Probe></Body></Envelope>'
        # sock.sendto(message1.encode(), (server_ip, server_port))
        # sock.sendto(message2.encode(), (server_ip, server_port))
        sock.sendto(message1.encode(), ('239.255.255.250', server_port))
    except:
        sock.close()
        return False
    else:
        sock.close()
        return True


def onvif_get_scan_return_ip():
    global global_onvif_discoverable_list
    pc = get_local_host_ip()

    def test():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(5)
        sock.bind((pc, onvif_random_port))
        while True:
            # 接收数据报文
            try:
                data, addr = sock.recvfrom(40960)
                print(addr)
                global_onvif_discoverable_list.append(addr[0])
            except:
                sock.close()
                break
        try:
            sock.close()
        except:
            pass

    a = threading.Thread(target=test)
    a.daemon = True
    a.start()


def send_multicast(ip, port):
    """
    发送10秒.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # 设置TTL（Time To Live）
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    message1 = '808000006b4b33a5f79046affffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
    port = int(port)

    def test():
        cur_time = time.time()
        try:
            for i in range(300):
                sock.sendto(message1.encode(), (ip, port))
                time.sleep(0.1)
                if time.time() - cur_time > 10:
                    break
        except:
            sock.close()
            return False
        else:
            sock.close()
            return True

    a = threading.Thread(target=test)
    a.daemon = True
    a.start()
