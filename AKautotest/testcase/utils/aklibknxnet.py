# -*- coding: UTF-8 -*-

import os
import sys

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
if root_path not in sys.path:
    sys.path.append(root_path)

from akcommon_define import *
from testcase.utils.aklibknxutil import *
from abc import ABC, ABCMeta, abstractmethod
from enum import Enum
from collections import deque
import time
from typing import Dict

# # GVS IP下载器
# udp_ip = "192.168.88.206"
# udp_port = 3671
# gateway_ip = "192.168.88.100"

# 贝乐IP下载器
udp_ip = "192.168.10.100"
udp_port = 3671
gateway_ip = "192.168.10.107"

data_endpoint = (udp_ip, 0)  # for NAT
control_endpoint = (gateway_ip, 0)


def create_frame(service_type_descriptor, *data):
    frametype = ServiceTypeDescriptor.to_class(service_type_descriptor)
    if frametype is not None:
        return frametype.create_from_data(*data)


def decode_frame(frame):
    header = KnxnetHeader.create_from_frame(frame)
    frametype = ServiceTypeDescriptor.to_class(ServiceTypeDescriptor(header.service_type_descriptor))
    if frametype is not None:
        return frametype.create_from_frame(frame)


def write_data_to_group_addr(dest_group_addr, data, data_size, delay_time=2, timeout=30):
    """
        向目标组地址写入16进制数据
        "dest_group_addr": 目标组地址 -- 如9/1/2
        "data": None -- 16进制数据，如0x1F6A
        "data_size": 数据类型 -- 1bit-1，1byte-2，2byte-3，3byte-4，4byte-5
    """
    aklog_info()
    data_endpoint = (udp_ip, 0)  # for NAT
    control_enpoint = (gateway_ip, 0)

    # Connection request
    conn_req = create_frame(ServiceTypeDescriptor.CONNECTION_REQUEST,
                            control_enpoint,
                            data_endpoint)
    # print('==> Send connection request to {0}:{1}'.format(udp_ip, udp_port))
    # print("repr(conn_req):%s" %repr(conn_req))
    # print("conn_req:%s" % conn_req)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.bind(('', 3672)) #每个端口只能绑定一次
    sock.settimeout(timeout)
    sock.bind(control_endpoint)

    try:
        sock.sendto(conn_req.frame, (udp_ip, udp_port))

        # Connection response
        data_recv, addr = sock.recvfrom(1024)
        conn_resp = decode_frame(data_recv)
        # print('<== Received connection response:')
        # print(repr(conn_resp))
        # print(conn_resp)

        # Connection state request
        conn_state_req = create_frame(ServiceTypeDescriptor.CONNECTION_STATE_REQUEST,
                                      conn_resp.channel_id,
                                      control_enpoint)
        # print('==> Send connection state request to channel {0}'.format(conn_resp.channel_id))
        # print(repr(conn_state_req))
        # print(conn_state_req)
        sock.sendto(conn_state_req.frame, (udp_ip, udp_port))

        # Connection state response
        data_recv, addr = sock.recvfrom(1024)
        conn_state_resp = decode_frame(data_recv)
        # print('<== Received connection state response:')
        # print(repr(conn_state_resp))
        # print(conn_state_resp)

        # Tunnel request, apci to 0x2 = GroupValueWrite
        tunnel_req = create_frame(ServiceTypeDescriptor.TUNNELLING_REQUEST,
                                  dest_group_addr,
                                  conn_resp.channel_id,
                                  data,
                                  data_size,
                                  0x2)
        # print('==> Send tunnelling request to {0}:{1}'.format(udp_ip, udp_port))
        # print(repr(tunnel_req))
        # print(tunnel_req)
        sock.sendto(tunnel_req.frame, (udp_ip, udp_port))

        # # Read Tunnel ack
        # data_recv, addr = sock.recvfrom(1024)
        # ack = decode_frame(data_recv)
        # print('<== Received tunnelling ack:')
        # print(repr(ack))
        # print(ack)

        # Tunnel request confirm
        data_recv, addr = sock.recvfrom(1024)
        confirm_req = decode_frame(data_recv)
        # print('<== Received tunnelling request confirmation:')
        # print(repr(confirm_req))
        # print(confirm_req)

        # # 检查消息类型
        # if not hasattr(confirm_req, 'sequence_counter'):
        #     raise AttributeError("Received message does not have sequence_counter")

        # send Tunnel ack
        tunnel_ack = create_frame(ServiceTypeDescriptor.TUNNELLING_ACK,
                                  confirm_req.channel_id,
                                  0,
                                  confirm_req.sequence_counter)
        # print('==> Send tunnelling ack to {0}:{1}'.format(udp_ip, udp_port))
        # print(repr(tunnel_ack))
        # print(tunnel_ack)
        sock.sendto(tunnel_ack.frame, (udp_ip, udp_port))

        # Disconnect request
        disconnect_req = create_frame(ServiceTypeDescriptor.DISCONNECT_REQUEST,
                                      conn_resp.channel_id,
                                      control_enpoint)
        # print('==> Send disconnect request to channel {0}'.format(conn_resp.channel_id))
        # print(repr(disconnect_req))
        # print(disconnect_req)
        sock.sendto(disconnect_req.frame, (udp_ip, udp_port))

        # Disconnect response
        data_recv, addr = sock.recvfrom(1024)
        disconnect_resp = decode_frame(data_recv)
        # print('<== Received connection state response:')
        # print(repr(disconnect_resp))
        # print(disconnect_resp)
    except socket.timeout:
        aklog_info("等待KNX设备响应超时！")
        raise
    finally:
        sock.close()  # 确保在退出时关闭套接字
        time.sleep(delay_time)

def write_data_to_multi_group_addr(group_addr_list, data, data_size, timeout=2):
    """
    向多个组地址写入相同16进制数据
    Args:
        group_addr_list (list): 组地址列表，如["9/1/2", "9/1/3"]
        data: None -- 16进制数据，如0x1F6A
        data_size (int): 数据类型
        timeout (int): 超时时间
    Returns:
        dict: {组地址: True/False}
    """
    results = {}
    for addr in group_addr_list:
        result = write_data_to_group_addr(addr, data, data_size, timeout)
        results[addr] = result
    return results

def read_data_irrelevant_group_addr(dest_group_addr, data, data_size):
    data_endpoint = (udp_ip, 0)  # for NAT
    control_enpoint = (gateway_ip, 0)
    # data_endpoint = (gateway_ip, 53672)  # 不能指定端口
    # control_enpoint = (udp_ip, 3671)

    # Connection request
    conn_req = create_frame(ServiceTypeDescriptor.CONNECTION_REQUEST,
                            control_enpoint,
                            data_endpoint)
    # print('==> Send connection request to {0}:{1}'.format(udp_ip, udp_port))
    # print(repr(conn_req))
    # print(conn_req)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.bind(('', 3672)) #每个端口只能绑定一次
    sock.bind(control_endpoint)

    sock.sendto(conn_req.frame, (udp_ip, udp_port))

    # Connection response
    data_recv, addr = sock.recvfrom(1024)
    conn_resp = decode_frame(data_recv)
    # print('<== Received connection response:')
    # print(repr(conn_resp))
    # print(conn_resp)

    # Connection state request
    conn_state_req = create_frame(ServiceTypeDescriptor.CONNECTION_STATE_REQUEST,
                                  conn_resp.channel_id,
                                  control_enpoint)
    # print('==> Send connection state request to channel {0}'.format(conn_resp.channel_id))
    # print(repr(conn_state_req))
    # print(conn_state_req)
    sock.sendto(conn_state_req.frame, (udp_ip, udp_port))
    # Connection state response

    data_recv, addr = sock.recvfrom(1024)

    # print("data_recv:%s" % data_recv)
    conn_state_resp = decode_frame(data_recv)
    # print('<== Received connection state response:')
    # print(repr(conn_state_resp))
    # print(conn_state_resp)

    # Tunnel request, apci to 0 = GroupValueRead
    tunnel_req = create_frame(ServiceTypeDescriptor.TUNNELLING_REQUEST,
                              dest_group_addr,
                              conn_resp.channel_id,
                              data,
                              data_size,
                              0)
    # print('==> Send tunnelling request to {0}:{1}'.format(udp_ip, udp_port))
    # print(repr(tunnel_req))
    # print(tunnel_req)
    sock.sendto(tunnel_req.frame, (udp_ip, udp_port))

    # receive tunnel ack
    data_recv, addr = sock.recvfrom(1024)
    ack = decode_frame(data_recv)
    # print('<== Received tunnelling ack:')
    # print(repr(ack))
    # print(ack)

    # Tunnel request confirm
    data_recv, addr = sock.recvfrom(1024)
    confirm_req = decode_frame(data_recv)
    # print('<== Received tunnelling request confirmation:')
    # print(repr(confirm_req))
    # print(confirm_req)

    # send Tunnel ack
    tunnel_ack = create_frame(ServiceTypeDescriptor.TUNNELLING_ACK,
                              confirm_req.channel_id,
                              0,
                              confirm_req.sequence_counter)
    # print('==> Send tunnelling ack to {0}:{1}'.format(udp_ip, udp_port))
    # print(repr(tunnel_ack))
    # print(tunnel_ack)
    sock.sendto(tunnel_ack.frame, (udp_ip, udp_port))

    # Receive tunnelling request
    data_recv, addr = sock.recvfrom(1024)
    received_tunnelling_req = decode_frame(data_recv)
    # print('<== Received tunnelling req:')
    # print(repr(received_tunnelling_req))
    # print(received_tunnelling_req)
    hex_value = hex(received_tunnelling_req.data)
    print('===> DATA (hex): ', hex_value)

    # send disconnect request
    disconnect_req = create_frame(ServiceTypeDescriptor.DISCONNECT_REQUEST,
                                  conn_resp.channel_id,
                                  control_enpoint)
    # print('==> Send disconnect request to channel {0}'.format(conn_resp.channel_id))
    # print(repr(disconnect_req))
    # print(disconnect_req)
    sock.sendto(disconnect_req.frame, (udp_ip, udp_port))

    # Disconnect response
    data_recv, addr = sock.recvfrom(1024)
    disconnect_resp = decode_frame(data_recv)
    # print('<== Received connection state response:')
    # print(repr(disconnect_resp))
    # print(disconnect_resp)
    return hex_value


def is_read_data_from_group_addresses(group_addresses: Dict[str, list], check_recv=True, timeout=5) -> bool:
    """
    检查是否读取到对应组地址的报文
    Args:
        *group_addresses (dict): {'1/2/33': ['0x1388'], '1/2/32': ['0x66']}
        check_recv (bool): 当为False时，必须要所有的组地址都没有收到报文才会返回True,
            当为True时，必须要所有的组地址都收到对应的报文才会返回True
        timeout ():
    """
    aklog_info()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(control_endpoint)

    start_time = time.time()
    recv_data_info = {}
    received_frames = set()  # 用于去重的缓存
    conn_resp = None  # Initialize to handle cases where connection fails early
    recv_success = False

    def check_timeout():
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            raise socket.timeout("Timeout reached while waiting for data")

    try:
        # Connection request
        conn_req = create_frame(ServiceTypeDescriptor.CONNECTION_REQUEST,
                                control_endpoint, data_endpoint)
        sock.sendto(conn_req.frame, (udp_ip, udp_port))

        # Connection response with timeout
        check_timeout()
        sock.settimeout(timeout - (time.time() - start_time))
        data_recv, addr = sock.recvfrom(1024)
        conn_resp = decode_frame(data_recv)

        # Connection state request
        conn_state_req = create_frame(ServiceTypeDescriptor.CONNECTION_STATE_REQUEST,
                                      conn_resp.channel_id, control_endpoint)
        sock.sendto(conn_state_req.frame, (udp_ip, udp_port))

        # Connection state response with timeout
        check_timeout()
        sock.settimeout(timeout - (time.time() - start_time))
        data_recv, addr = sock.recvfrom(1024)
        conn_state_resp = decode_frame(data_recv)

        # Main data reception loop
        while True:
            check_timeout()
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time <= 0:
                raise socket.timeout("Timeout reached while waiting for data")
            sock.settimeout(remaining_time)

            data_recv, addr = sock.recvfrom(1024)
            decoded_frame = decode_frame(data_recv)

            if isinstance(decoded_frame, TunnellingRequest):
                # Send ACK immediately
                tunnel_ack = create_frame(ServiceTypeDescriptor.TUNNELLING_ACK,
                                          decoded_frame.channel_id, 0, decoded_frame.sequence_counter)
                sock.sendto(tunnel_ack.frame, (udp_ip, udp_port))

                frame_id = (str(decoded_frame.dest_addr_group), hex(decoded_frame.data))
                if frame_id in received_frames:
                    aklog_debug(f"忽略重复报文: {frame_id}")
                    continue
                received_frames.add(frame_id)

                addr = str(decoded_frame.dest_addr_group)
                if addr in group_addresses:
                    if addr not in recv_data_info:
                        recv_data_info[addr] = set()
                    recv_data_info[addr].add(hex(decoded_frame.data))

                if all(_addr in recv_data_info
                       and set(group_addresses[_addr]).issubset(recv_data_info[_addr])
                       for _addr in group_addresses):
                    aklog_info("报文接收成功")
                    recv_success = True
                    break

            elif isinstance(decoded_frame, TunnellingAck):
                aklog_debug(f"<== Received tunnelling ack: {decoded_frame}")
            else:
                aklog_warn(f"<== Received unexpected frame type: {decoded_frame}")

    except socket.timeout:
        aklog_warn(f"Timeout after {timeout} seconds")
    except Exception as e:
        aklog_warn(f'Exception error: {e}')
        aklog_debug(traceback.format_exc())
    finally:
        # Graceful disconnect
        if conn_resp is not None:
            disconnect_req = create_frame(ServiceTypeDescriptor.DISCONNECT_REQUEST,
                                          conn_resp.channel_id, control_endpoint)
            try:
                sock.sendto(disconnect_req.frame, (udp_ip, udp_port))
                # Brief wait for disconnect ack
                sock.settimeout(1)
                data_recv, _ = sock.recvfrom(1024)
                disconnect_resp = decode_frame(data_recv)
                aklog_debug(f'<== Received disconnect response: {disconnect_resp}')
            except Exception as e:
                aklog_warn(f"Disconnect error: {e}")
        sock.close()

    aklog_info(f'读取到的16进制数据: {recv_data_info}')
    return recv_success if check_recv else not recv_data_info


def read_second_data_from_group_addr(dest_group_addr):
    aklog_info()
    data_endpoint = (udp_ip, 0)  # for NAT
    control_endpoint = (gateway_ip, 0)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(control_endpoint)

    exit_program = False  # 增加一个全局退出标志
    start_time = time.time()  # 记录开始时间
    timeout_duration = 120  # 设置超时为2分钟（120秒）

    # Connection request
    conn_req = create_frame(ServiceTypeDescriptor.CONNECTION_REQUEST,
                            control_endpoint, data_endpoint)
    # print('==> Send connection request to {0}:{1}'.format(udp_ip, udp_port))
    sock.sendto(conn_req.frame, (udp_ip, udp_port))

    # Connection response
    data_recv, addr = sock.recvfrom(1024)
    conn_resp = decode_frame(data_recv)
    # print('<== Received connection response:', conn_resp)

    # Connection state request
    conn_state_req = create_frame(ServiceTypeDescriptor.CONNECTION_STATE_REQUEST,
                                  conn_resp.channel_id, control_endpoint)
    # print('==> Send connection state request to channel {0}'.format(conn_resp.channel_id))
    sock.sendto(conn_state_req.frame, (udp_ip, udp_port))

    # Connection state response
    data_recv, addr = sock.recvfrom(1024)
    conn_state_resp = decode_frame(data_recv)
    # print('<== Received connection state response:', conn_state_resp)

    # Tunnel request, apci to 0 = GroupValueRead    #去掉这条发送的报文即可读取
    # tunnel_req = create_frame(ServiceTypeDescriptor.TUNNELLING_REQUEST,
    #                                  dest_group_addr, conn_resp.channel_id, data, data_size, 0)
    # print('==> Send tunnelling request to {0}:{1}'.format(udp_ip, udp_port))
    # sock.sendto(tunnel_req.frame, (udp_ip, udp_port))

    decoded_frame = None
    buffer = deque()  # 创建一个缓冲区

    while True:
        # 使用 select 进行超时等待
        ready_to_read, _, _ = select.select([sock], [], [], timeout_duration)
        current_time = time.time()
        if ready_to_read:
            data_recv, addr = sock.recvfrom(1024)
            decoded_frame = decode_frame(data_recv)

            if isinstance(decoded_frame, TunnellingRequest):
                buffer.append(decoded_frame)  # 把接收到的数据插入缓冲区
                # print('<== Received tunnelling request and added to buffer:', decoded_frame)
                # print('===> DATA:', decoded_frame.data)

                # Send tunnelling ack
                tunnel_ack = create_frame(ServiceTypeDescriptor.TUNNELLING_ACK,
                                          decoded_frame.channel_id, 0, decoded_frame.sequence_counter)
                # print('==> Send tunnelling ack to {0}:{1}'.format(udp_ip, udp_port))
                sock.sendto(tunnel_ack.frame, (udp_ip, udp_port))

                match_count = 0  # 计数的变量

                # 执行缓冲区循环并修改逻辑
                for frame in buffer:
                    if str(frame.dest_addr_group) == str(dest_group_addr):
                        match_count += 1
                        if match_count == 2:  # 当满足条件的计数达到第二次时触发
                            # print('Buffered DATA:', decoded_frame.data)
                            # print('<== tunnelling_req.data:', hex(decoded_frame.data))
                            exit_program = True
                            break
                # Check if we should stop reading
                if exit_program:
                    break
            elif isinstance(decoded_frame, TunnellingAck):
                print('<== Received tunnelling ack:', decoded_frame)
            else:
                print('<== Received unexpected frame type:', decoded_frame)
        else:
            # Check if timeout has been reached
            if current_time - start_time >= timeout_duration:
                print("Timeout reached.")
                break

    # Send disconnect request
    disconnect_req = create_frame(ServiceTypeDescriptor.DISCONNECT_REQUEST,
                                  conn_resp.channel_id, control_endpoint)
    # print('==> Send disconnect request to channel {0}'.format(conn_resp.channel_id))
    sock.sendto(disconnect_req.frame, (udp_ip, udp_port))

    # Disconnect response
    data_recv, addr = sock.recvfrom(1024)
    disconnect_resp = decode_frame(data_recv)
    # print('<== Received disconnect response:', disconnect_resp)

    aklog_info("读取到的目标组地址:%s的16进制数据为%s" % (dest_group_addr, hex(decoded_frame.data)))
    return hex(decoded_frame.data)


def read_data_from_group_addr(dest_group_addr, timeout_duration=5):
    aklog_info()
    data_endpoint = (udp_ip, 0)  # for NAT
    control_endpoint = (gateway_ip, 0)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(control_endpoint)

    start_time = time.time()

    # Connection request
    conn_req = create_frame(ServiceTypeDescriptor.CONNECTION_REQUEST,
                            control_endpoint, data_endpoint)
    sock.sendto(conn_req.frame, (udp_ip, udp_port))

    # Connection response
    data_recv, addr = sock.recvfrom(1024)
    conn_resp = decode_frame(data_recv)

    # Connection state request
    conn_state_req = create_frame(ServiceTypeDescriptor.CONNECTION_STATE_REQUEST,
                                  conn_resp.channel_id, control_endpoint)
    sock.sendto(conn_state_req.frame, (udp_ip, udp_port))

    # Connection state response
    data_recv, addr = sock.recvfrom(1024)
    conn_state_resp = decode_frame(data_recv)

    buffer = deque()  # 创建一个缓冲区
    last_data: Optional[int] = None  # 用于存储最后一个读取到的数据

    while True:
        ready_to_read, _, _ = select.select([sock], [], [], timeout_duration)
        current_time = time.time()

        if ready_to_read:
            data_recv, addr = sock.recvfrom(1024)
            decoded_frame = decode_frame(data_recv)

            if isinstance(decoded_frame, TunnellingRequest):
                buffer.append(decoded_frame)

                # Send tunnelling ack
                tunnel_ack = create_frame(ServiceTypeDescriptor.TUNNELLING_ACK,
                                          decoded_frame.channel_id, 0, decoded_frame.sequence_counter)
                sock.sendto(tunnel_ack.frame, (udp_ip, udp_port))

                for frame in buffer:
                    if str(frame.dest_addr_group) == str(dest_group_addr):
                        last_data = frame.data  # 更新最后一个读取到的数据
                        aklog_info("读取到的目标组地址:%s的最新16进制数据为%s" % (dest_group_addr, hex(last_data)))
                        return hex(last_data)

            elif isinstance(decoded_frame, TunnellingAck):
                print('<== Received tunnelling ack:', decoded_frame)
            else:
                print('<== Received unexpected frame type:', decoded_frame)

        else:
            # Check if timeout has been reached
            if current_time - start_time >= timeout_duration:
                print("Timeout reached.")
                break

    # Send disconnect request
    disconnect_req = create_frame(ServiceTypeDescriptor.DISCONNECT_REQUEST,
                                  conn_resp.channel_id, control_endpoint)
    sock.sendto(disconnect_req.frame, (udp_ip, udp_port))

    # Disconnect response
    data_recv, addr = sock.recvfrom(1024)
    disconnect_resp = decode_frame(data_recv)

    if last_data is not None:
        aklog_info("读取到的目标组地址:%s的最新16进制数据为%s" % (dest_group_addr, hex(last_data)))
        return hex(last_data)
    else:
        aklog_info("未读取到目标组地址:%s的数据" % dest_group_addr)
        return None


def read_first_data_multiple_group_addr(dest_group_addrs, timeout_duration=20) -> Optional[list]:
    """
    读取多个组地址的第一个数据包

    2025/04/21 modify:修改超时方法
    Args:
        dest_group_addrs (list):
        timeout_duration ():
    """
    aklog_info()
    data_endpoint = (udp_ip, 0)  # for NAT
    control_endpoint = (gateway_ip, 0)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(control_endpoint)

    start_time = time.time()
    matched_addresses_data: list = [None] * len(dest_group_addrs)
    conn_resp = None  # Initialize to handle cases where connection fails early

    def check_timeout():
        elapsed = time.time() - start_time
        if elapsed >= timeout_duration:
            raise socket.timeout("Timeout reached while waiting for data")

    try:
        # Connection request
        conn_req = create_frame(ServiceTypeDescriptor.CONNECTION_REQUEST,
                                control_endpoint, data_endpoint)
        sock.sendto(conn_req.frame, (udp_ip, udp_port))

        # Connection response with timeout
        check_timeout()
        sock.settimeout(timeout_duration - (time.time() - start_time))
        data_recv, addr = sock.recvfrom(1024)
        conn_resp = decode_frame(data_recv)

        # Connection state request
        conn_state_req = create_frame(ServiceTypeDescriptor.CONNECTION_STATE_REQUEST,
                                      conn_resp.channel_id, control_endpoint)
        sock.sendto(conn_state_req.frame, (udp_ip, udp_port))

        # Connection state response with timeout
        check_timeout()
        sock.settimeout(timeout_duration - (time.time() - start_time))
        data_recv, addr = sock.recvfrom(1024)
        conn_state_resp = decode_frame(data_recv)

        # Main data reception loop
        while True:
            check_timeout()
            remaining_time = timeout_duration - (time.time() - start_time)
            if remaining_time <= 0:
                raise socket.timeout()
            sock.settimeout(remaining_time)

            data_recv, addr = sock.recvfrom(1024)
            decoded_frame = decode_frame(data_recv)

            if isinstance(decoded_frame, TunnellingRequest):
                # Send ACK immediately
                tunnel_ack = create_frame(ServiceTypeDescriptor.TUNNELLING_ACK,
                                          decoded_frame.channel_id, 0, decoded_frame.sequence_counter)
                sock.sendto(tunnel_ack.frame, (udp_ip, udp_port))

                # Process each target address
                for i, target_addr in enumerate(dest_group_addrs):
                    if (str(decoded_frame.dest_addr_group) == str(target_addr) and
                            matched_addresses_data[i] is None):
                        matched_addresses_data[i] = hex(decoded_frame.data)

                # Early exit if all data collected
                if all(data is not None for data in matched_addresses_data):
                    break

            elif isinstance(decoded_frame, TunnellingAck):
                print('<== Received tunnelling ack:', decoded_frame)
            else:
                print('<== Received unexpected frame type:', decoded_frame)

    except socket.timeout:
        print(f"Timeout after {timeout_duration} seconds")
    finally:
        # Graceful disconnect
        if conn_resp is not None:
            disconnect_req = create_frame(ServiceTypeDescriptor.DISCONNECT_REQUEST,
                                          conn_resp.channel_id, control_endpoint)
            try:
                sock.sendto(disconnect_req.frame, (udp_ip, udp_port))
                # Brief wait for disconnect ack
                sock.settimeout(1)
                data_recv, _ = sock.recvfrom(1024)
                disconnect_resp = decode_frame(data_recv)
                print('<== Received disconnect response:', disconnect_resp)
            except Exception as e:
                print(f"Disconnect error: {str(e)}")
        sock.close()

    aklog_info(f"读取到的目标组地址的16进制数据为{matched_addresses_data}")
    return matched_addresses_data


def read_first_data_from_group_addr(dest_group_addr, timeout=30):
    """
        读取目标组地址的第一个报文
        2025/04/21 modify:修改超时方法

        "dest_group_addr": 目标组地址 -- 如9/1/2
        "data":16进制数据，如0x1F6A
        "data_size": 数据类型 -- 1bit-1，1byte-2，2byte-3，3byte-4，4byte-5
    """
    aklog_info()
    start_time = time.time()
    data_endpoint = (udp_ip, 0)  # for NAT
    control_endpoint = (gateway_ip, 0)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(control_endpoint)
    conn_resp = None

    def check_timeout():
        remaining = timeout - (time.time() - start_time)
        if remaining <= 0:
            raise socket.timeout

    try:
        # Connection request
        conn_req = create_frame(ServiceTypeDescriptor.CONNECTION_REQUEST,
                                control_endpoint, data_endpoint)
        sock.sendto(conn_req.frame, (udp_ip, udp_port))

        # Connection response
        check_timeout()
        sock.settimeout(timeout - (time.time() - start_time))
        data_recv, addr = sock.recvfrom(1024)
        conn_resp = decode_frame(data_recv)

        # Connection state request
        conn_state_req = create_frame(ServiceTypeDescriptor.CONNECTION_STATE_REQUEST,
                                      conn_resp.channel_id, control_endpoint)
        sock.sendto(conn_state_req.frame, (udp_ip, udp_port))

        # Connection state response
        check_timeout()
        sock.settimeout(timeout - (time.time() - start_time))
        data_recv, addr = sock.recvfrom(1024)
        conn_state_resp = decode_frame(data_recv)

        while True:
            check_timeout()
            sock.settimeout(timeout - (time.time() - start_time))
            data_recv, addr = sock.recvfrom(1024)
            decoded_frame = decode_frame(data_recv)

            if isinstance(decoded_frame, TunnellingAck):
                continue
            else:
                # 发送Tunnelling Ack
                tunnel_ack = create_frame(ServiceTypeDescriptor.TUNNELLING_ACK,
                                          decoded_frame.channel_id, 0, decoded_frame.sequence_counter)
                sock.sendto(tunnel_ack.frame, (udp_ip, udp_port))

                if should_stop_reading(decoded_frame, dest_group_addr):
                    break

        # 断开连接流程
        disconnect_req = create_frame(ServiceTypeDescriptor.DISCONNECT_REQUEST,
                                      conn_resp.channel_id, control_endpoint)
        sock.sendto(disconnect_req.frame, (udp_ip, udp_port))

        check_timeout()
        sock.settimeout(timeout - (time.time() - start_time))
        data_recv, addr = sock.recvfrom(1024)
        disconnect_resp = decode_frame(data_recv)

        return hex(decoded_frame.data)

    except socket.timeout:
        # 超时处理：发送断开请求并返回None
        disconnect_req = create_frame(ServiceTypeDescriptor.DISCONNECT_REQUEST,
                                      conn_resp.channel_id if 'conn_resp' in locals() else 0, control_endpoint)
        try:
            sock.sendto(disconnect_req.frame, (udp_ip, udp_port))
        except:
            pass
        return None
    finally:
        sock.close()


def should_stop_reading(tunnelling_req, target_dest_group_addr):
    # Check the 'dest_addr_group' in the tunnelling request
    if str(tunnelling_req.dest_addr_group) == str(target_dest_group_addr):
        aklog_info('解析出的16进制报文数据为:%s' % hex(tunnelling_req.data))
        return True
    else:
        return False


def generate_test_cases(max_value, min_value=0):
    test_cases = set()

    # 确保输入有效
    if min_value > max_value:
        min_value, max_value = max_value, min_value

    # 核心边界值
    test_cases.update({min_value, max_value})

    # 中心点值（确保不越界）
    mid_value = min_value + (max_value - min_value) // 2
    test_cases.add(mid_value)

    # 添加临界值（边界附近）
    if min_value < max_value:
        test_cases.add(min_value + 1)
        test_cases.add(max_value - 1)

    # 随机值（确保不重复）
    import random
    num_samples = min(10, max_value - min_value + 1)
    if num_samples > 0:
        test_cases.update(random.sample(range(min_value, max_value + 1), num_samples))

    # 排序结果
    return sorted(test_cases)


class ServiceTypeDescriptor(Enum):
    CONNECTION_REQUEST = 0x0205
    CONNECTION_RESPONSE = 0x0206
    CONNECTION_STATE_REQUEST = 0x0207
    CONNECTION_STATE_RESPONSE = 0x0208
    DISCONNECT_REQUEST = 0x0209
    DISCONNECT_RESPONSE = 0x020a
    TUNNELLING_REQUEST = 0x0420
    TUNNELLING_ACK = 0x0421

    @staticmethod
    def to_class(x):
        return {
            ServiceTypeDescriptor.CONNECTION_REQUEST: ConnectionRequest,
            ServiceTypeDescriptor.CONNECTION_RESPONSE: ConnectionResponse,
            ServiceTypeDescriptor.CONNECTION_STATE_REQUEST: ConnectionStateRequest,
            ServiceTypeDescriptor.CONNECTION_STATE_RESPONSE: ConnectionStateResponse,
            ServiceTypeDescriptor.DISCONNECT_REQUEST: DisconnectRequest,
            ServiceTypeDescriptor.DISCONNECT_RESPONSE: DisconnectResponse,
            ServiceTypeDescriptor.TUNNELLING_REQUEST: TunnellingRequest,
            ServiceTypeDescriptor.TUNNELLING_ACK: TunnellingAck
        }[x]


class KnxnetFrame(ABC, metaclass=ABCMeta):

    def __init__(self):
        pass

    def __repr__(self):
        return str([hex(h) for h in self.frame])

    @classmethod
    @abstractmethod
    def create_from_frame(cls, frame):
        pass

    @classmethod
    @abstractmethod
    def create_from_data(cls, *data):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @property
    @abstractmethod
    def frame(self):
        pass


class KnxnetHeader(KnxnetFrame):
    HEADER_LENGTH = 0x06
    VERSION = 0x10

    def __init__(self, header_length, version, service_type_descriptor, frame_length):
        super().__init__()
        self.header_length = header_length
        self.version = version
        self.service_type_descriptor = service_type_descriptor
        self.frame_length = frame_length

    @classmethod
    def create_from_frame(cls, frame):
        if len(frame) < 6:
            raise KnxnetException('Frame size is < 6')
        header_length = frame[0]
        version = frame[1]
        service_type_descriptor = ServiceTypeDescriptor((frame[2] << 8) | frame[3])
        frame_length = (frame[4] << 8) | frame[5]
        return cls(header_length, version, service_type_descriptor, frame_length)

    @classmethod
    def create_from_data(cls, service_type_descriptor, frame_length):
        return cls(KnxnetHeader.HEADER_LENGTH,
                   KnxnetHeader.VERSION,
                   service_type_descriptor,
                   frame_length)

    @property
    def frame(self):
        """
        Create the KNXnet header frame (6 bytes)
        """
        frame = bytearray()
        frame.append(self.header_length)
        frame.append(self.version)
        frame.append((self.service_type_descriptor.value >> 8) & 0xff)
        frame.append(self.service_type_descriptor.value & 0xff)
        frame.append((self.frame_length >> 8) & 0xff)
        frame.append(self.frame_length & 0xff)
        return frame

    def __str__(self):
        out = '{:<25}'.format('header_length')
        out += '{:>10}\n'.format(hex(self.header_length))
        out += '{:<25}'.format('version')
        out += '{:>10}\n'.format(hex(self.version))
        out += '{:<25}'.format('service_type_descriptor')
        out += '{:>10}\n'.format(hex(self.service_type_descriptor.value))
        out += '{:<25}'.format('frame_length')
        out += '{:>10}\n'.format(hex(self.frame_length))
        return out

    def __repr__(self):
        return super().__repr__()


class TunnellingRequest(KnxnetFrame):
    """
    TunnellingRequest KNXnet/IP frame
    """

    def __init__(self, knxnet_header, dest_addr_group, channel_id, data, data_size, apci, data_service,
                 sequence_counter):
        super().__init__()
        self.header = knxnet_header
        self.dest_addr_group = dest_addr_group
        self.channel_id = channel_id
        self.data_service = data_service  # See Data Service under
        """
        FROM NETWORK LAYER TO DATA LINK LAYER
        – L_Raw.req 0x10
        – L_Data.req 0x11 Data Service. Primitive used for transmitting a data frame
        – L_Poll_Data.req 0x13 Poll Data Service
        FROM DATA LINK LAYER TO NETWORK LAYER
        – L_Poll_Data.con 0x25 Poll Data Service
        – L_Data.ind 0x29 Data Service. Primitive used for receiving a data frame
        – L_Busmon.ind 0x2B Bus Monitor Service
        – L_Raw.ind 0x2D
        – L_Data.con 0x2E Data Service. Primitive used for local confirmation that a frame was sent (does not indicate a successful receive though)
        – L_Raw.con 0x2F )
        """
        self.data = data
        self.data_size = data_size
        self.apci = apci  # (0x0 == group value read; 0x1 == group value response; 0x2 == group value write)
        self.sequence_counter = sequence_counter

    @classmethod
    def create_from_frame(cls, frame):
        """
        Create the Tunnelling request object from a frame
        :param frame: knx tunnelling request datagram frame (list of bytes)
        """
        if frame is None:
            raise KnxnetException('Tunnelling request frame is None')
        if len(frame) < 16:
            raise KnxnetException('Tunnelling request length is < 16')
        raw_header = frame[:6]
        raw_body = frame[6:]
        header = KnxnetHeader.create_from_frame(raw_header)
        if len(frame) != header.frame_length:
            raise KnxnetException('Invalid frame: effective total length != announced total length')
        channel_id = raw_body[1]
        sequence_counter = raw_body[2]
        data_service = raw_body[4]
        dest_addr_group = GroupAddress.from_bytes(raw_body[10:12])
        data_size = raw_body[12]
        # aklog_info("data_size:%s" % data_size)
        # if data_size > 2: #原来的底层方法data_size限制了，现把它开放出来
        #     raise KnxnetException('Invalid frame: Unsupported datapoint type (data size > 2')
        apci = (raw_body[13] & 3 << 2) | (raw_body[14] >> 6)
        # only two datapoint types are supported:

        if data_size == 1:  # 原先只能处理1bit数据，改为能处理4bit数据
            if hex(raw_body[14]).startswith('0x8'):
                char = str(hex(raw_body[14]))[-1]
                data = int(char, 16)
            else:
                data = raw_body[14] & 1
        elif data_size == 2:  # 1 bytes
            data = raw_body[15]
        elif data_size == 3:  # 2 bytes
            data = (raw_body[15] << 8) | raw_body[16]
        elif data_size == 4:  # 3 bytes
            data = (raw_body[15] << 16) | (raw_body[16] << 8) | raw_body[17]
        elif data_size == 5:  # 4 bytes
            data = (raw_body[15] << 24) | (raw_body[16] << 16) | raw_body[17] << 8 | raw_body[18]
        elif data_size == 7:  # 6 bytes
            data = (raw_body[15] << 40) | (raw_body[16] << 32) | (raw_body[17] << 24) | (raw_body[18] << 16) | (
                    raw_body[19] << 8) | raw_body[20]
        elif data_size == 15:  # 14 bytes
            data = (raw_body[15] << 104) | (raw_body[16] << 96) | (raw_body[17] << 88) | (raw_body[18] << 80) | (
                    raw_body[19] << 72) | (raw_body[20] << 64) | (raw_body[21] << 56) | (raw_body[22] << 48) | (
                           raw_body[23] << 40) | (raw_body[24] << 32) | (raw_body[25] << 24) | (raw_body[26] << 16) | (
                           raw_body[27] << 8) | raw_body[28]
        else:
            raise KnxnetException(f'Unsupported data size: {data_size}')
        return cls(header, dest_addr_group, channel_id, data, data_size, apci, data_service, sequence_counter)

    @classmethod
    def create_from_data(cls, dest_addr_group, channel_id, data, data_size, apci=0x2, data_service=0x11,
                         sequence_counter=0x0):
        """
        Create the Tunnelling request object from data
        :param dest_addr_group: GroupAddress object, or string
        :param channel_id: 1 byte with channel ID
        :param data: effective data
        :param data_size: data size in byte
        :param apci: APCI command. 0x2 is group value write    0 is group value read
        :param data_service:
        :param sequence_counter:
        """
        frame_length = 0x14 + data_size
        header = KnxnetHeader.create_from_data(ServiceTypeDescriptor.TUNNELLING_REQUEST, frame_length)
        if isinstance(dest_addr_group, GroupAddress):
            dest = dest_addr_group
        else:
            dest = GroupAddress.from_str(dest_addr_group)
        return cls(header, dest, channel_id, data, data_size, apci, data_service, sequence_counter)

    @property
    def frame(self):
        # KNXnet header
        frame = self.header.frame
        # Connection header
        frame.append(0x04)  # structure length
        frame.append(self.channel_id & 0xff)  # channel id
        frame.append(self.sequence_counter)  # sequence counter
        frame.append(0x00)  # reserved
        # cEMI
        frame.append(self.data_service)  # message code = data service transmitting
        frame.append(0x00)  # no additional info
        frame.append(0xbc)  # control byte
        frame.append(0xe0)  # DRL byte
        frame.append(0x00)  # Source address (filled by gateway)
        frame.append(0x00)
        frame += self.dest_addr_group.frame  # destination address group
        frame.append(self.data_size)  # routing (4 bits) + data size (4 bits)
        frame.append(0x0 | ((self.apci >> 2) & 3))  # The last 2 bits are the two msb for the APCI command

        # only two datapoint types are supported:
        if self.data_size == 1:  # 1bit
            frame.append(((self.apci & 3) << 6) | (self.data & 1) | (
                    self.data & 0xF))  # the first 2 bits are lsb APCI, bit 0 is data
        elif self.data_size == 2:  # 1byte
            frame.append((self.apci & 3) << 6)  # the first 2 bits are lsb APCI
            frame.append(self.data & 0xFF)  # data
        elif self.data_size == 3:  # 2byte
            frame.append((self.apci & 3) << 6)  # the first 2 bits are lsb APCI
            frame.append((self.data >> 8) & 0xFF)  # high byte of the data
            frame.append(self.data & 0xFF)  # low byte of the data
        elif self.data_size == 4:  # 3byte
            frame.append((self.apci & 3) << 6)  # the first 2 bits are lsb APCI
            frame.append((self.data >> 16) & 0xFF)  # highest byte of the data
            frame.append((self.data >> 8) & 0xFF)  # middle byte of the data
            frame.append(self.data & 0xFF)  # lowest byte of the data
        elif self.data_size == 5:  # 4byte
            frame.append((self.apci & 3) << 6)  # the first 2 bits are lsb APCI
            frame.append((self.data >> 24) & 0xFF)  # highest byte of the 32-bit data
            frame.append((self.data >> 16) & 0xFF)  # high byte of the 32-bit data
            frame.append((self.data >> 8) & 0xFF)  # middle byte of the 32-bit data
            frame.append(self.data & 0xFF)  # lowest byte of the 32-bit data
        elif self.data_size == 7:  # 6 bytes
            frame.append((self.apci & 3) << 6)  # the first 2 bits are lsb APCI
            frame.append((self.data >> 40) & 0xFF)  # the highest byte of the 6-byte data
            frame.append((self.data >> 32) & 0xFF)  # the second-highest byte
            frame.append((self.data >> 24) & 0xFF)  # the third-highest byte
            frame.append((self.data >> 16) & 0xFF)  # the fourth-highest byte
            frame.append((self.data >> 8) & 0xFF)  # the fifth-highest byte
            frame.append(self.data & 0xFF)  # the lowest byte of the 6-byte data
        elif self.data_size == 15:  # 14 bytes
            frame.append((self.apci & 3) << 6)  # the first 2 bits are lsb APCI
            frame.append((self.data >> 104) & 0xFF)  # the highest byte of the 14-byte data
            frame.append((self.data >> 96) & 0xFF)  # the second-highest byte
            frame.append((self.data >> 88) & 0xFF)
            frame.append((self.data >> 80) & 0xFF)
            frame.append((self.data >> 72) & 0xFF)
            frame.append((self.data >> 64) & 0xFF)
            frame.append((self.data >> 56) & 0xFF)
            frame.append((self.data >> 48) & 0xFF)
            frame.append((self.data >> 40) & 0xFF)
            frame.append((self.data >> 32) & 0xFF)
            frame.append((self.data >> 24) & 0xFF)
            frame.append((self.data >> 16) & 0xFF)
            frame.append((self.data >> 8) & 0xFF)
            frame.append(self.data & 0xFF)  # the lowest byte of the 14-byte data

        return frame

    def __str__(self):
        out = str(self.header)
        out += '{:<25}'.format('dest_addr_group')
        out += '{:>10}\n'.format(str(self.dest_addr_group))
        out += '{:<25}'.format('channel_id')
        out += '{:>10}\n'.format(hex(self.channel_id))
        out += '{:<25}'.format('sequence_counter')
        out += '{:>10}\n'.format(hex(self.sequence_counter))
        out += '{:<25}'.format('data_service')
        out += '{:>10}\n'.format(hex(self.data_service))
        out += '{:<25}'.format('data')
        out += '{:>10}\n'.format(hex(self.data))
        out += '{:<25}'.format('data_size')
        out += '{:>10}\n'.format(hex(self.data_size))
        out += '{:<25}'.format('apci')
        out += '{:>10}\n'.format(hex(self.apci))
        return out

    def __repr__(self):
        return super().__repr__()


class TunnellingAck(KnxnetFrame):
    """
    Tunnelling ack KNXnet/IP frame
    """

    def __init__(self, knxnet_header, channel_id, status, sequence_counter):
        super().__init__()
        self.header = knxnet_header
        self.channel_id = channel_id
        self.status = status
        self.sequence_counter = sequence_counter

    @classmethod
    def create_from_frame(cls, frame):
        if frame is None:
            raise KnxnetException('Tunnelling ack frame is None')
        if len(frame) != 10:
            raise KnxnetException('Tunnelling ack length must be 10 bytes')
        raw_header = frame[:6]
        raw_body = frame[6:]
        header = KnxnetHeader.create_from_frame(raw_header)
        if len(frame) != header.frame_length:
            raise KnxnetException('Invalid frame: effective total length != announced total length')
        channel_id = raw_body[1]
        sequence_counter = raw_body[2]
        status = raw_body[3]
        return cls(header, channel_id, status, sequence_counter)

    @classmethod
    def create_from_data(cls, channel_id, status, sequence_counter=0x0):
        frame_length = 10
        header = KnxnetHeader.create_from_data(ServiceTypeDescriptor.TUNNELLING_ACK, frame_length)
        return cls(header, channel_id, status, sequence_counter)

    @property
    def frame(self):
        frame = self.header.frame
        frame.append(0x04)  # structure length
        frame.append(self.channel_id)
        frame.append(self.sequence_counter)
        frame.append(self.status)
        return frame

    def __str__(self):
        out = str(self.header)
        out += '{:<25}'.format('channel_id')
        out += '{:>10}\n'.format(str(self.channel_id))
        out += '{:<25}'.format('sequence_counter')
        out += '{:>10}\n'.format(str(self.sequence_counter))
        out += '{:<25}'.format('status')
        out += '{:>10}\n'.format(str(self.status))
        return out

    def __repr__(self):
        return super().__repr__()


class ConnectionRequest(KnxnetFrame):
    """
    Connection_request KNXnet/IP frame
    """

    def __init__(self, knxnet_header, control_endpoint, data_endpoint):
        super().__init__()
        self.header = knxnet_header
        self.control_endpoint = control_endpoint
        self.data_endpoint = data_endpoint

    @classmethod
    def create_from_frame(cls, frame):
        if frame is None:
            raise KnxnetException('Connection request frame is None')
        if len(frame) < 24:
            raise KnxnetException('Connection request length must >= 24 bytes')
        raw_header = frame[:6]
        raw_body = frame[6:]
        header = KnxnetHeader.create_from_frame(raw_header)
        if len(frame) != header.frame_length:
            raise KnxnetException('Invalid frame: effective total length != announced total length')
        control_endpoint = Hpai.from_frame(raw_body[:8])
        data_endpoint = Hpai.from_frame(raw_body[8:20])
        return cls(header, control_endpoint, data_endpoint)

    @classmethod
    def create_from_data(cls, control_endpoint, data_endpoint):
        """
        :param control_endpoint Hpai object or tuple (ip, port)
        :param data_endpoint Hpai object or tuple (ip, port)
        """
        frame_length = 0x1A
        header = KnxnetHeader.create_from_data(ServiceTypeDescriptor.CONNECTION_REQUEST, frame_length)
        if isinstance(control_endpoint, Hpai):
            ctrl_endpt = control_endpoint
        else:
            ctrl_endpt = Hpai.from_data(control_endpoint[0], control_endpoint[1])
        if isinstance(data_endpoint, Hpai):
            data_endpt = data_endpoint
        else:
            data_endpt = Hpai.from_data(data_endpoint[0], data_endpoint[1])
        return cls(header, ctrl_endpt, data_endpt)

    @property
    def frame(self):
        # KNXnet header
        frame = self.header.frame
        # HPAI
        frame += self.control_endpoint.frame
        frame += self.data_endpoint.frame
        # CRI (Connection request info) to be defined
        frame.append(0x04)  # structure length
        frame.append(0x04)  # Tunnel Connection
        frame.append(0x02)  # KNX Tunnel link layer
        frame.append(0x00)  # Reserved
        return frame

    def __str__(self):
        out = str(self.header)
        out += '{:<25}'.format('control_endpoint')
        out += '{:>10}\n'.format(str(self.control_endpoint))
        out += '{:<25}'.format('data_endpoint')
        out += '{:>10}\n'.format(str(self.data_endpoint))
        return out

    def __repr__(self):
        return super().__repr__()


class ConnectionResponse(KnxnetFrame):
    """
    Connection_response KNXnet/IP frame
    """

    def __init__(self, knxnet_header, channel_id, status, data_endpoint):
        super().__init__()
        self.header = knxnet_header
        self.channel_id = channel_id
        self.status = status
        self.data_endpoint = data_endpoint

    @classmethod
    def create_from_frame(cls, frame):
        if frame is None:
            raise KnxnetException('Connection response frame is None')
        if len(frame) < 18:
            raise KnxnetException('Connection response length must be >= 18 bytes')
        raw_header = frame[:6]
        raw_body = frame[6:]
        header = KnxnetHeader.create_from_frame(raw_header)
        if len(frame) != header.frame_length:
            raise KnxnetException('Invalid frame: effective total length != announced total length')
        channel_id = raw_body[0]
        status = raw_body[1]
        data_endpoint = Hpai.from_frame(raw_body[2:10])
        return cls(header, channel_id, status, data_endpoint)

    @classmethod
    def create_from_data(cls, channel_id, status, data_endpoint):
        """
        :param channel_id  one byte
        :param status  one byte
        :param data_endpoint Hpai object or tuple (ip, port)
        """
        frame_length = 20
        header = KnxnetHeader.create_from_data(ServiceTypeDescriptor.CONNECTION_RESPONSE, frame_length)
        if isinstance(data_endpoint, Hpai):
            data_endpt = data_endpoint
        else:
            data_endpt = Hpai.from_data(data_endpoint[0], data_endpoint[1])
        return cls(header, channel_id, status, data_endpt)

    @property
    def frame(self):
        frame = self.header.frame
        frame.append(self.channel_id)
        frame.append(self.status)
        frame += self.data_endpoint.frame
        # CRD (connection response data) is to be defined
        frame.append(0x04)
        frame.append(0x04)
        frame.append(0xff)
        frame.append(0xff)
        return frame

    def __str__(self):
        out = str(self.header)
        out += '{:<25}'.format('channel_id')
        out += '{:>10}\n'.format(str(self.channel_id))
        out += '{:<25}'.format('status')
        out += '{:>10}\n'.format(str(self.status))
        out += '{:<25}'.format('data_endpoint')
        out += '{:>10}\n'.format(str(self.data_endpoint))
        return out

    def __repr__(self):
        return super().__repr__()


class ConnectionStateRequest(KnxnetFrame):
    """
    Connection state request KNXnet/IP frame
    """

    def __init__(self, knxnet_header, channel_id, control_endpoint):
        super().__init__()
        self.header = knxnet_header
        self.channel_id = channel_id
        self.control_endpoint = control_endpoint

    @classmethod
    def create_from_frame(cls, frame):
        if frame is None:
            raise KnxnetException('Connection state request frame is None')
        if len(frame) != 16:
            raise KnxnetException('Connection state request length must be 16 bytes')
        raw_header = frame[:6]
        raw_body = frame[6:]
        header = KnxnetHeader.create_from_frame(raw_header)
        if len(frame) != header.frame_length:
            raise KnxnetException('Invalid frame: effective total length != announced total length')
        channel_id = raw_body[0]
        control_endpoint = Hpai.from_frame(raw_body[2:10])
        return cls(header, channel_id, control_endpoint)

    @classmethod
    def create_from_data(cls, channel_id, control_endpoint):
        """
        :param channel_id  one byte
        :param control_endpoint  Hpai object or tuple (ip, port)
        """
        frame_length = 16
        header = KnxnetHeader.create_from_data(ServiceTypeDescriptor.CONNECTION_STATE_REQUEST, frame_length)
        if isinstance(control_endpoint, Hpai):
            ctrl_endpt = control_endpoint
        else:
            ctrl_endpt = Hpai.from_data(control_endpoint[0], control_endpoint[1])
        return cls(header, channel_id, ctrl_endpt)

    @property
    def frame(self):
        frame = self.header.frame
        frame.append(self.channel_id)
        frame.append(0x00)
        frame += self.control_endpoint.frame
        return frame

    def __str__(self):
        out = str(self.header)
        out += '{:<25}'.format('channel_id')
        out += '{:>10}\n'.format(str(self.channel_id))
        out += '{:<25}'.format('control_endpoint')
        out += '{:>10}\n'.format(str(self.control_endpoint))
        return out

    def __repr__(self):
        return super().__repr__()


class ConnectionStateResponse(KnxnetFrame):
    """
    Connection state response KNXnet/IP frame
    """

    def __init__(self, knxnet_header, channel_id, status):
        super().__init__()
        self.header = knxnet_header
        self.channel_id = channel_id
        self.status = status

    @classmethod
    def create_from_frame(cls, frame):
        if frame is None:
            raise KnxnetException('Connection state response frame is None')
        if len(frame) != 8:
            raise KnxnetException('Connection state response length must be 8 bytes')
        raw_header = frame[:6]
        raw_body = frame[6:]
        header = KnxnetHeader.create_from_frame(raw_header)
        if len(frame) != header.frame_length:
            raise KnxnetException('Invalid frame: effective total length != announced total length')
        channel_id = raw_body[0]
        status = raw_body[1]
        return cls(header, channel_id, status)

    @classmethod
    def create_from_data(cls, channel_id, status):
        frame_length = 8
        header = KnxnetHeader.create_from_data(ServiceTypeDescriptor.CONNECTION_STATE_RESPONSE, frame_length)
        return cls(header, channel_id, status)

    @property
    def frame(self):
        frame = self.header.frame
        frame.append(self.channel_id)
        frame.append(self.status)
        return frame

    def __str__(self):
        out = str(self.header)
        out += '{:<25}'.format('channel_id')
        out += '{:>10}\n'.format(str(self.channel_id))
        out += '{:<25}'.format('status')
        out += '{:>10}\n'.format(str(self.status))
        return out

    def __repr__(self):
        return super().__repr__()


class DisconnectRequest(KnxnetFrame):
    """
    Disconnect request KNXnet/IP frame
    """

    def __init__(self, knxnet_header, channel_id, control_endpoint):
        super().__init__()
        self.header = knxnet_header
        self.channel_id = channel_id
        self.control_endpoint = control_endpoint

    @classmethod
    def create_from_frame(cls, frame):
        if frame is None:
            raise KnxnetException('Disconnect request frame is None')
        if len(frame) != 16:
            raise KnxnetException('Disconnect request length must be 16 bytes')
        raw_header = frame[:6]
        raw_body = frame[6:]
        header = KnxnetHeader.create_from_frame(raw_header)
        if len(frame) != header.frame_length:
            raise KnxnetException('Invalid frame: effective total length != announced total length')
        channel_id = raw_body[0]
        control_endpoint = Hpai.from_frame(raw_body[2:10])
        return cls(header, channel_id, control_endpoint)

    @classmethod
    def create_from_data(cls, channel_id, control_endpoint):
        """
        :param channel_id  one byte
        :param control_endpoint  Hpai object or tuple (ip, port)
        """
        frame_length = 16
        header = KnxnetHeader.create_from_data(ServiceTypeDescriptor.DISCONNECT_REQUEST, frame_length)
        if isinstance(control_endpoint, Hpai):
            ctrl_endpt = control_endpoint
        else:
            ctrl_endpt = Hpai.from_data(control_endpoint[0], control_endpoint[1])
        return cls(header, channel_id, ctrl_endpt)

    @property
    def frame(self):
        frame = self.header.frame
        frame.append(self.channel_id)
        frame.append(0x00)
        frame += self.control_endpoint.frame
        return frame

    def __str__(self):
        out = str(self.header)
        out += '{:<25}'.format('channel_id')
        out += '{:>10}\n'.format(str(self.channel_id))
        out += '{:<25}'.format('control_endpoint')
        out += '{:>10}\n'.format(str(self.control_endpoint))
        return out

    def __repr__(self):
        return super().__repr__()


class DisconnectResponse(KnxnetFrame):
    """
    Disconnect response KNXnet/IP frame
    """

    def __init__(self, knxnet_header, channel_id, status):
        super().__init__()
        self.header = knxnet_header
        self.channel_id = channel_id
        self.status = status

    @classmethod
    def create_from_frame(cls, frame):
        if frame is None:
            raise KnxnetException('Disconnect response frame is None')
        if len(frame) != 8:
            raise KnxnetException('Disconnect response length must be 8 bytes')
        raw_header = frame[:6]
        raw_body = frame[6:]
        header = KnxnetHeader.create_from_frame(raw_header)
        if len(frame) != header.frame_length:
            raise KnxnetException('Invalid frame: effective total length != announced total length')
        channel_id = raw_body[0]
        status = raw_body[1]
        return cls(header, channel_id, status)

    @classmethod
    def create_from_data(cls, channel_id, status):
        frame_length = 8
        header = KnxnetHeader.create_from_data(ServiceTypeDescriptor.DISCONNECT_RESPONSE, frame_length)
        return cls(header, channel_id, status)

    @property
    def frame(self):
        frame = self.header.frame
        frame.append(self.channel_id)
        frame.append(self.status)
        return frame

    def __str__(self):
        out = str(self.header)
        out += '{:<25}'.format('channel_id')
        out += '{:>10}\n'.format(str(self.channel_id))
        out += '{:<25}'.format('status')
        out += '{:>10}\n'.format(str(self.status))
        return out

    def __repr__(self):
        return super().__repr__()


class KnxnetException(Exception):
    pass



if __name__ == '__main__':
    # aklog_info(generate_test_cases(281474976710655, 196608))
	# write_data_to_group_addr('2/2/1', 1, 1)   #开关
    # write_data_to_group_addr('16/1/11', 0xFF, 2)  #调亮度
    # read_data_from_group_addr('16/1/1', 0xCE2, 3)  # 读取温度
    # write_data_to_group_addr('11/1/6', 0x05B0, 3)  # 写入voc
    # write_data_to_group_addr('3/1/17', 0x73, 2)  # 写入亮度
    # read_data_from_group_addr('3/1/3', 0x00, 2) #读取窗帘百分比
    # write_data_to_group_addr('9/1/1', 0xA86836, 4)  # 写入3byte的颜色值
    # read_data_from_group_addr('9/1/1', 0, 4)  # 读取3byte的颜色值
    # write_data_to_group_addr('14/1/2', 0x4462, 4)
    write_data_to_multi_group_addr(['8/2/86', '8/2/89', '8/2/91', '8/2/93', '8/2/95',
    '8/2/97', '8/2/99', '8/2/101', '8/2/103', '8/2/105',
    '8/2/107', '8/2/109', '8/2/111', '8/2/113', '8/2/115',
    '8/2/117', '8/2/119', '8/2/121', '8/2/123', '8/2/125',
    '8/2/127', '8/2/129', '8/2/131', '8/2/133', '8/2/135',
    '8/2/137', '8/2/139', '8/2/141', '8/2/143','8/2/0', '8/2/1', '8/2/2', '8/2/3', '8/2/4', '8/2/5', '8/2/6', '8/2/7', '8/2/8', '8/2/9',
     '8/2/10', '8/2/11', '8/2/12', '8/2/13', '8/2/14', '8/2/15', '8/2/16', '8/2/17', '8/2/18', '8/2/19','8/2/20', '8/2/21', '8/2/22', '8/2/23', '8/2/24', '8/2/25', '8/2/26', '8/2/27', '8/2/28', '8/2/29',
     '8/2/30', '8/2/31', '8/2/32', '8/2/33', '8/2/34', '8/2/35', '8/2/36', '8/2/37', '8/2/38', '8/2/39','8/2/240', '8/2/241', '8/2/242', '8/2/243', '8/2/244', '8/2/245',
     '8/2/246', '8/2/247', '8/2/248', '8/2/249', '8/2/250', '8/2/251',
     '8/2/252', '8/2/253', '8/2/254', '8/2/255','8/2/86', '8/2/89', '8/2/91', '8/2/93', '8/2/95',
    '8/2/97', '8/2/99', '8/2/101', '8/2/103', '8/2/105',
    '8/2/107', '8/2/109', '8/2/111', '8/2/113', '8/2/115',
    '8/2/117', '8/2/119', '8/2/121', '8/2/123', '8/2/125',
    '8/2/127', '8/2/129', '8/2/131', '8/2/133', '8/2/135',
    '8/2/137', '8/2/139', '8/2/141', '8/2/143','8/2/0', '8/2/1', '8/2/2', '8/2/3', '8/2/4', '8/2/5', '8/2/6', '8/2/7', '8/2/8', '8/2/9',
     '8/2/10', '8/2/11', '8/2/12', '8/2/13', '8/2/14', '8/2/15', '8/2/16', '8/2/17', '8/2/18', '8/2/19','8/2/20', '8/2/21', '8/2/22', '8/2/23', '8/2/24', '8/2/25', '8/2/26', '8/2/27', '8/2/28', '8/2/29',
     '8/2/30', '8/2/31', '8/2/32', '8/2/33', '8/2/34', '8/2/35', '8/2/36', '8/2/37', '8/2/38', '8/2/39','8/2/240', '8/2/241', '8/2/242', '8/2/243', '8/2/244', '8/2/245',
     '8/2/246', '8/2/247', '8/2/248', '8/2/249', '8/2/250', '8/2/251',
     '8/2/252', '8/2/253', '8/2/254', '8/2/255','8/2/86', '8/2/89', '8/2/91', '8/2/93', '8/2/95',
    '8/2/97', '8/2/99', '8/2/101', '8/2/103', '8/2/105',
    '8/2/107', '8/2/109', '8/2/111', '8/2/113', '8/2/115',
    '8/2/117', '8/2/119', '8/2/121', '8/2/123', '8/2/125',
    '8/2/127', '8/2/129', '8/2/131', '8/2/133', '8/2/135',
    '8/2/137', '8/2/139', '8/2/141', '8/2/143','8/2/0', '8/2/1', '8/2/2', '8/2/3', '8/2/4', '8/2/5', '8/2/6', '8/2/7', '8/2/8', '8/2/9',
     '8/2/10', '8/2/11', '8/2/12', '8/2/13', '8/2/14', '8/2/15', '8/2/16', '8/2/17', '8/2/18', '8/2/19','8/2/20', '8/2/21', '8/2/22', '8/2/23', '8/2/24', '8/2/25', '8/2/26', '8/2/27', '8/2/28', '8/2/29',
     '8/2/30', '8/2/31', '8/2/32', '8/2/33', '8/2/34', '8/2/35', '8/2/36', '8/2/37', '8/2/38', '8/2/39','8/2/240', '8/2/241', '8/2/242', '8/2/243', '8/2/244', '8/2/245',
     '8/2/246', '8/2/247', '8/2/248', '8/2/249', '8/2/250', '8/2/251',
     '8/2/252', '8/2/253', '8/2/254', '8/2/255','8/2/86', '8/2/89', '8/2/91', '8/2/93', '8/2/95',
    '8/2/97', '8/2/99', '8/2/101', '8/2/103', '8/2/105',
    '8/2/107', '8/2/109', '8/2/111', '8/2/113', '8/2/115',
    '8/2/117', '8/2/119', '8/2/121', '8/2/123', '8/2/125',
    '8/2/127', '8/2/129', '8/2/131', '8/2/133', '8/2/135',
    '8/2/137', '8/2/139', '8/2/141', '8/2/143','8/2/0', '8/2/1', '8/2/2', '8/2/3', '8/2/4', '8/2/5', '8/2/6', '8/2/7', '8/2/8', '8/2/9',
     '8/2/10', '8/2/11', '8/2/12', '8/2/13', '8/2/14', '8/2/15', '8/2/16', '8/2/17', '8/2/18', '8/2/19','8/2/20', '8/2/21', '8/2/22', '8/2/23', '8/2/24', '8/2/25', '8/2/26', '8/2/27', '8/2/28', '8/2/29',
     '8/2/30', '8/2/31', '8/2/32', '8/2/33', '8/2/34', '8/2/35', '8/2/36', '8/2/37', '8/2/38', '8/2/39','8/2/240', '8/2/241', '8/2/242', '8/2/243', '8/2/244', '8/2/245',
     '8/2/246', '8/2/247', '8/2/248', '8/2/249', '8/2/250', '8/2/251',
     '8/2/252', '8/2/253', '8/2/254', '8/2/255','8/2/86', '8/2/89', '8/2/91', '8/2/93', '8/2/95',
    '8/2/97', '8/2/99', '8/2/101', '8/2/103', '8/2/105',
    '8/2/107', '8/2/109', '8/2/111', '8/2/113', '8/2/115',
    '8/2/117', '8/2/119', '8/2/121', '8/2/123', '8/2/125',
    '8/2/127', '8/2/129', '8/2/131', '8/2/133', '8/2/135',
    '8/2/137', '8/2/139', '8/2/141', '8/2/143','8/2/0', '8/2/1', '8/2/2', '8/2/3', '8/2/4', '8/2/5', '8/2/6', '8/2/7', '8/2/8', '8/2/9',
     '8/2/10', '8/2/11', '8/2/12', '8/2/13', '8/2/14', '8/2/15', '8/2/16', '8/2/17', '8/2/18', '8/2/19','8/2/20', '8/2/21', '8/2/22', '8/2/23', '8/2/24', '8/2/25', '8/2/26', '8/2/27', '8/2/28', '8/2/29',
     '8/2/30', '8/2/31', '8/2/32', '8/2/33', '8/2/34', '8/2/35', '8/2/36', '8/2/37', '8/2/38', '8/2/39','8/2/240', '8/2/241', '8/2/242', '8/2/243', '8/2/244', '8/2/245',
     '8/2/246', '8/2/247', '8/2/248', '8/2/249', '8/2/250', '8/2/251',
     '8/2/252', '8/2/253', '8/2/254', '8/2/255','8/2/86', '8/2/89', '8/2/91', '8/2/93', '8/2/95',
    '8/2/97', '8/2/99', '8/2/101', '8/2/103', '8/2/105',
    '8/2/107', '8/2/109', '8/2/111', '8/2/113', '8/2/115',
    '8/2/117', '8/2/119', '8/2/121', '8/2/123', '8/2/125',
    '8/2/127', '8/2/129', '8/2/131', '8/2/133', '8/2/135',
    '8/2/137', '8/2/139', '8/2/141', '8/2/143','8/2/0', '8/2/1', '8/2/2', '8/2/3', '8/2/4', '8/2/5', '8/2/6', '8/2/7', '8/2/8', '8/2/9',
     '8/2/10', '8/2/11', '8/2/12', '8/2/13', '8/2/14', '8/2/15', '8/2/16', '8/2/17', '8/2/18', '8/2/19','8/2/20', '8/2/21', '8/2/22', '8/2/23', '8/2/24', '8/2/25', '8/2/26', '8/2/27', '8/2/28', '8/2/29',
     '8/2/30', '8/2/31', '8/2/32', '8/2/33', '8/2/34', '8/2/35', '8/2/36', '8/2/37', '8/2/38', '8/2/39','8/2/240', '8/2/241', '8/2/242', '8/2/243', '8/2/244', '8/2/245',
     '8/2/246', '8/2/247', '8/2/248', '8/2/249', '8/2/250', '8/2/251',
     '8/2/252', '8/2/253', '8/2/254', '8/2/255'
                                    ,'8/2/86', '8/2/89', '8/2/91', '8/2/93', '8/2/95',
    '8/2/97', '8/2/99', '8/2/101', '8/2/103', '8/2/105',
    '8/2/107', '8/2/109', '8/2/111', '8/2/113', '8/2/115',
    '8/2/117', '8/2/119', '8/2/121', '8/2/123', '8/2/125',
    '8/2/127', '8/2/129', '8/2/131', '8/2/133', '8/2/135',
    '8/2/137', '8/2/139', '8/2/141', '8/2/143','8/2/0', '8/2/1', '8/2/2', '8/2/3', '8/2/4', '8/2/5', '8/2/6', '8/2/7', '8/2/8', '8/2/9',
     '8/2/10', '8/2/11', '8/2/12', '8/2/13', '8/2/14', '8/2/15', '8/2/16', '8/2/17', '8/2/18', '8/2/19','8/2/20', '8/2/21', '8/2/22', '8/2/23', '8/2/24', '8/2/25', '8/2/26', '8/2/27', '8/2/28', '8/2/29',
     '8/2/30', '8/2/31', '8/2/32', '8/2/33', '8/2/34', '8/2/35', '8/2/36', '8/2/37', '8/2/38', '8/2/39','8/2/240', '8/2/241', '8/2/242', '8/2/243', '8/2/244', '8/2/245',
     '8/2/246', '8/2/247', '8/2/248', '8/2/249', '8/2/250', '8/2/251',
     '8/2/252', '8/2/253', '8/2/254', '8/2/255','8/2/86', '8/2/89', '8/2/91', '8/2/93', '8/2/95',
    '8/2/97', '8/2/99', '8/2/101', '8/2/103', '8/2/105',
    '8/2/107', '8/2/109', '8/2/111', '8/2/113', '8/2/115',
    '8/2/117', '8/2/119', '8/2/121', '8/2/123', '8/2/125',
    '8/2/127', '8/2/129', '8/2/131', '8/2/133', '8/2/135',
    '8/2/137', '8/2/139', '8/2/141', '8/2/143','8/2/0', '8/2/1', '8/2/2', '8/2/3', '8/2/4', '8/2/5', '8/2/6', '8/2/7', '8/2/8', '8/2/9',
     '8/2/10', '8/2/11', '8/2/12', '8/2/13', '8/2/14', '8/2/15', '8/2/16', '8/2/17', '8/2/18', '8/2/19','8/2/20', '8/2/21', '8/2/22', '8/2/23', '8/2/24', '8/2/25', '8/2/26', '8/2/27', '8/2/28', '8/2/29',
     '8/2/30', '8/2/31', '8/2/32', '8/2/33', '8/2/34', '8/2/35', '8/2/36', '8/2/37', '8/2/38', '8/2/39','8/2/240', '8/2/241', '8/2/242', '8/2/243', '8/2/244', '8/2/245',
     '8/2/246', '8/2/247', '8/2/248', '8/2/249', '8/2/250', '8/2/251',
     '8/2/252', '8/2/253', '8/2/254', '8/2/255','8/2/86', '8/2/89', '8/2/91', '8/2/93', '8/2/95',
    '8/2/97', '8/2/99', '8/2/101', '8/2/103', '8/2/105',
    '8/2/107', '8/2/109', '8/2/111', '8/2/113', '8/2/115',
    '8/2/117', '8/2/119', '8/2/121', '8/2/123', '8/2/125',
    '8/2/127', '8/2/129', '8/2/131', '8/2/133', '8/2/135',
    '8/2/137', '8/2/139', '8/2/141', '8/2/143','8/2/0', '8/2/1', '8/2/2', '8/2/3', '8/2/4', '8/2/5', '8/2/6', '8/2/7', '8/2/8', '8/2/9',
     '8/2/10', '8/2/11', '8/2/12', '8/2/13', '8/2/14', '8/2/15', '8/2/16', '8/2/17', '8/2/18', '8/2/19','8/2/20', '8/2/21', '8/2/22', '8/2/23', '8/2/24', '8/2/25', '8/2/26', '8/2/27', '8/2/28', '8/2/29',
     '8/2/30', '8/2/31', '8/2/32', '8/2/33', '8/2/34', '8/2/35', '8/2/36', '8/2/37', '8/2/38', '8/2/39','8/2/240', '8/2/241', '8/2/242', '8/2/243', '8/2/244', '8/2/245',
     '8/2/246', '8/2/247', '8/2/248', '8/2/249', '8/2/250', '8/2/251',
     '8/2/252', '8/2/253', '8/2/254', '8/2/255','8/2/86', '8/2/89', '8/2/91', '8/2/93', '8/2/95',
    '8/2/97', '8/2/99', '8/2/101', '8/2/103', '8/2/105',
    '8/2/107', '8/2/109', '8/2/111', '8/2/113', '8/2/115',
    '8/2/117', '8/2/119', '8/2/121', '8/2/123', '8/2/125',
    '8/2/127', '8/2/129', '8/2/131', '8/2/133', '8/2/135',
    '8/2/137', '8/2/139', '8/2/141', '8/2/143','8/2/0', '8/2/1', '8/2/2', '8/2/3', '8/2/4', '8/2/5', '8/2/6', '8/2/7', '8/2/8', '8/2/9',
     '8/2/10', '8/2/11', '8/2/12', '8/2/13', '8/2/14', '8/2/15', '8/2/16', '8/2/17', '8/2/18', '8/2/19','8/2/20', '8/2/21', '8/2/22', '8/2/23', '8/2/24', '8/2/25', '8/2/26', '8/2/27', '8/2/28', '8/2/29',
     '8/2/30', '8/2/31', '8/2/32', '8/2/33', '8/2/34', '8/2/35', '8/2/36', '8/2/37', '8/2/38', '8/2/39','8/2/240', '8/2/241', '8/2/242', '8/2/243', '8/2/244', '8/2/245',
     '8/2/246', '8/2/247', '8/2/248', '8/2/249', '8/2/250', '8/2/251',
     '8/2/252', '8/2/253', '8/2/254', '8/2/255'
                                    ], 0x1, 1, 0.02)
    # read_first_data_multiple_group_addr(['3/1/1', '3/1/3', '3/1/5', '3/1/11'])