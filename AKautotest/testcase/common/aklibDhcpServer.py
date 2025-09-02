# -*- coding: UTF-8 -*-
import socket
import struct
import binascii
import logging
import platform
import os
from threading import Thread
from random import *
import time
g_Discover = 1
g_Offer = 2
g_Request = 3
g_ACK = 5
g_NACK = 6

logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(threadName)s: %(message)s')

class DHCPServer():
    """
    This class implements parts of RFC-2131
    Only DHCPDISCOVER and DHCPREQUEST allowed
    """
    def __init__(self, boot_file=None, server_ip=None, server_router=None, offer_ip=None, tftp_ip=None, ftp_ip=None, timeout=8000):
        Thread.__init__(self)
        self._port = 67
        self._boot_file = boot_file
        self._file_index = 0
        self._offer_ip = offer_ip
        self._tftp_ip = tftp_ip
        self._ftp_ip = ftp_ip
        self._timeout = timeout
        self.server_ip = server_ip
        self.server_router = server_router
        self.send_data_type = 0


    @property
    def server_ip(self):
        return self._server_ip

    @server_ip.setter
    def server_ip(self, server_ip):
        self._server_ip = server_ip
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.send_socket.bind((self._server_ip, self._port))

    @property
    def boot_file(self):
        return self._boot_file

    @boot_file.setter
    def boot_file(self, boot_file):
        if not isinstance(boot_file, list):
            boot_file = [boot_file]
        self._boot_file = boot_file
        self._file_index = 0

    @property
    def offer_ip(self):
        return self._offer_ip

    @offer_ip.setter
    def offer_ip(self, offer_ip):
        self._offer_ip = offer_ip

    def set_send_data_type(self, type):
        '''设置发送包，是正序还是乱序'''
        if type != 0 and type != 1 and type != 2:
            print("请正确设置DHCP包，设置1为乱序，0为正序")
            return False
        self.send_data_type = type
        return True

    def get_send_data_type(self):
        '''获取发送包，正序乱序类型'''
        return self.send_data_type

    def set_timeout(self, time_out):
        '''封装设置timeout函数'''
        self._timeout = time_out

    def get_timeout(self):
        '''封装获取timeout函数'''
        return self._timeout

    def check_msg(self, m):
        is_valid, msg_type, select_ip, request_op, offer_ip = False, None, None, None, None
        #dhcp包前几个字节固定解析，[236:240]存放DHCP
        if (m[0] == b'\x01' and
            m[1] == b'\x01' and
            m[2] == b'\x06' and
            m[3] == b'\x00' and
            m[10:12] == [b'\x00', b'\x00'] and
            m[12:16] == [b'\x00', b'\x00', b'\x00', b'\x00'] and
            m[16:20] == [b'\x00', b'\x00', b'\x00', b'\x00'] and
            m[20:24] == [b'\x00', b'\x00', b'\x00', b'\x00'] and
            m[236:240] == [b'\x63', b'\x82', b'\x53', b'\x63']
            ):
            logging.warning('Valid DHCP message')
            # Valid DHCPDISCOVER
            opt = (x for x in m[240:])
            while opt:
                try:
                    func_code = next(opt)
                    if func_code == b'\x00':
                        break
                    length = next(opt)
                    items = b''
                    for i in range(ord(length)):
                        items += next(opt)
                except StopIteration:
                    break
                else:
                    if func_code == b'\x35' and length == b'\x01':
                        if items == b'\x01':
                            logging.warning('DHCP Discover')
                            msg_type = 'DSCV'
                            is_valid = True
                        if items == b'\x03':
                            logging.warning('DHCP Request')
                            msg_type = 'RQST'

                    # Assure DHCP server selected
                    if func_code == b'\x36' and msg_type == 'RQST':
                        logging.warning('DHCP Server Identifier check')
                        select_ip = socket.inet_ntoa(items)

                    if func_code == b'\x32':
                        logging.warning('DHCP offer ip check')
                        request_op = func_code
                        offer_ip = socket.inet_ntoa(items)


            # Double check DHCP offer ip
            if request_op == b'\x32' and select_ip == self._server_ip:
                if offer_ip == self._offer_ip:
                    is_valid = True
                else:
                    logging.warning('Offer ip double check failed')

        return is_valid, msg_type

    def handle_msg(self, msg, addr, is_Ack=g_ACK):
        ret = False
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        send_socket.bind((self._server_ip, self._port))
        m = list(struct.unpack('c' * len(msg), msg))
        is_valid, msg_type = self.check_msg(m)
        if is_valid:
            logging.warning('Valid %s message, try to response' % msg_type)
            pass_sec = ord(m[8]) * 256 + ord(m[9])
            transaction_id = ''.join(['%02x' % ord(x) for x in m[4:8]])
            client_mac_id = ':'.join(['%02x' % ord(x) for x in m[28:34]])
            if msg_type:
                offer = Offer(transaction_id=transaction_id,
                              client_ip_offer=self._offer_ip,
                              server_ip=self._server_ip,
                              server_router=self.server_router,
                              client_mac_id=client_mac_id,
                              file_path=self._boot_file,
                              pass_sec=pass_sec,
                              msg_type=msg_type,
                              send_type=self.get_send_data_type(),
                              lease_time=self._timeout,
                              is_ack=is_Ack,
                              tftp_ip=self._tftp_ip,
                              ftp_ip=self._ftp_ip)
                send_socket.sendto(offer.packet, ('<broadcast>', 68))
                self._file_index += 1
            logging.warning('Respone done')
            ret = True
        else:
            logging.warning('Invalid message, discard...')
            ret = False
        send_socket.close()
        return ret, msg_type

    def serve_forever(self):
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        self.recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.recv_socket.bind(('', self._port))

        if self._boot_file:
            if self._file_index >= len(self._boot_file):
                self._file_index = 0

    def recv_and_send_NACK(self):
        """封装，接收Discover，回复offer，接收Request，应答NACK函数，并且重新处理ACK函数"""
        logging.warning('Waiting discovery...')
        msg, addr = self.recv_socket.recvfrom(8192)
        self.handle_msg(msg, addr)
        logging.warning('Send Offer...')

        logging.warning('Waiting request')
        msg, addr = self.recv_socket.recvfrom(8192)
        self.handle_msg(msg, addr, g_NACK)
        logging.warning('Send NACK...')

        # 应答NACK后，重新处理dhcp服务
        self.recv_and_send_ack()



    def recv_and_send_ack(self):
        """封装，接收Discover，回复offer，接收Request，应答ACK函数"""
        logging.warning('Waiting discovery...')
        msg, addr = self.recv_socket.recvfrom(8192)
        self.handle_msg(msg, addr)
        logging.warning('Send Offer...')

        logging.warning('Waiting request')
        msg, addr = self.recv_socket.recvfrom(8192)
        self.handle_msg(msg, addr, g_ACK)
        logging.warning('Send ACK...')

    def dhcp_ip_timeout_and_renewal(self, client_ip, timeout):
        """dhcp超时，并且客户端进行续租，服务端回复函数"""
        self.set_timeout(timeout)
        self.recv_and_send_ack()
        #加延时,确保客户端ip分配完成
        time.sleep(10)
        ret1 = ping(client_ip, 4)
        print("ret1 =", ret1)

        # 加延时,确保客户端ip超时释放
        time.sleep(timeout)
        ret2 = ping(client_ip, 4)
        print("ret2 =", ret2)

        time.sleep(10)
        logging.warning('Waiting discovery...')
        #重新对客户端进行续约，服务端一直Offer，应答有误的Discover请求，而ACK只发送一次
        while True:
            msg, addr = dhcp.recv_socket.recvfrom(8192)
            ret, msg_type = dhcp.handle_msg(msg, addr)
            if ret is True and msg_type == 'RQST':
                logging.warning('Waiting request')
                logging.warning('Send ACK...')
                break

            elif ret is False or msg_type == 'DSCV':
                logging.warning('Send Offer...')
                continue

        #重新续约后ping测试
        time.sleep(10)
        ret3 = ping(client_ip, 4)
        print("ret3 =", ret3)




class Offer():
    def __init__(self, transaction_id, client_ip_offer, server_ip, server_router, client_mac_id, file_path, pass_sec, msg_type, send_type, lease_time, is_ack=g_ACK, tftp_ip=None, ftp_ip=None):
        SERVER_NAME = ''
        self._server_ip = server_ip
        self._server_router = server_router
        self._offer_ip = client_ip_offer
        self._lease_time = lease_time
        self._is_ack = is_ack
        self._send_type = send_type
        self._tftp_ip = tftp_ip
        self._ftp_ip = ftp_ip
        if tftp_ip is None:
            self._tftp_ip = server_ip
        if ftp_ip is None:
            self._ftp_ip = server_ip
        if not file_path:
            file_path = ''
        pass_sec = struct.pack('!H', pass_sec)
        client_mac_id = binascii.unhexlify(client_mac_id.replace(':', ''))
        transaction_id = binascii.unhexlify(transaction_id)

        self.packet = b''
        self.packet += b'\x02'  # op
        self.packet += b'\x01'  # htype
        self.packet += b'\x06'  # hlen
        self.packet += b'\x00'  # hops
        self.packet += transaction_id
        self.packet += pass_sec # secs
        self.packet += b'\x00\x00'  # flags
        self.packet += b'\x00\x00\x00\x00'  # current client ip
        self.packet += socket.inet_aton(client_ip_offer)# offer ip
        self.packet += socket.inet_aton(server_ip)  # server ip
        self.packet += b'\x00\x00\x00\x00'  # gateway ip
        self.packet += client_mac_id # client mac id
        self.packet += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # client mac id padding
        self.packet += SERVER_NAME.encode('utf-8')
        self.packet += b'\x00'*(64-len(SERVER_NAME))
        self.packet += file_path.encode('utf-8')
        self.packet += b'\x00'*(128-len(file_path))
        self.packet += self.optional(msg_type)

    def optional(self, msg_type):
        magic = b'\x63\x82\x53\x63'
        opt = b''
        if self._send_type == 0:
            # 正常option规则
            # Message type
            if msg_type == 'DSCV':
                opt += self.encode_int(53, 1, g_Offer)
            if msg_type == 'RQST':
                opt += self.encode_int(53, 1, self._is_ack)
            # Server identifier
            opt += self.encode_ip(54, 4, self._server_ip)
            # Subnet mask
            opt += self.encode_ip(1, 4, '255.255.255.0')
            # Router
            opt += self.encode_ip(3, 4, self._server_router)
            # IP address lease time
            opt += self.encode_int(51, 4, self._lease_time)

            opt += (bytes([43, len(self._ftp_ip)]) + self._ftp_ip.encode())
            opt += (bytes([66, len(self._tftp_ip)]) + self._tftp_ip.encode())

            # Tail
            # TODO: find out why a b'\xff' for end
            opt += b'\xff'
            return magic+opt

        elif self._send_type == 1:
            # 乱序option规则
            list_tmp = []
            if msg_type == 'DSCV':
                list_tmp.append(self.encode_int(53, 1, g_Offer))
            if msg_type == 'RQST':
                list_tmp.append(self.encode_int(53, 1, self._is_ack))
            list_tmp.append(self.encode_ip(54, 4, self._server_ip))
            list_tmp.append(self.encode_ip(1, 4, '255.255.255.0'))
            list_tmp.append(self.encode_ip(3, 4, self._server_router))
            list_tmp.append(self.encode_int(51, 4, self._lease_time))
            list_tmp.append(bytes([43, len(self._ftp_ip)]) + self._ftp_ip.encode())
            list_tmp.append(bytes([66, len(self._tftp_ip)]) + self._tftp_ip.encode())
            shuffle(list_tmp)
            for string in list_tmp:
                opt += string
            # Tail
            # TODO: find out why a b'\xff' for end
            opt += b'\xff'
            return magic+opt

    def encode_int(self, func, length, item):
        m = {1: '!B', 2: '!H', 4: '!I'}
        s = b''
        s += (bytes([func, length]) + struct.pack(m[length], item))
        return s

    def encode_ip(self, func, length, item):
        s = b''
        s += bytes([func, length])
        s += socket.inet_aton(item)
        return s

def ping(des_ip, ping_count):
    '''封装ping函数'''
    for i in range(ping_count):
        ret = os.system("ping " + ("-n 1 " if platform.system().lower() == "windows" else "-c 1 ") + des_ip)
        if ret != 0:
            return False
    return True

# '''demo'''
# if __name__ == '__main__':
#     dhcp = DHCPServer(server_ip='192.168.1.100', server_router='192.168.1.12', offer_ip='192.168.1.222', tftp_ip='tftp://192.168.1.100',ftp_ip='ftp://192.168.1.100')
#     dhcp.serve_forever()
#     #测试乱序进行
#     dhcp.set_send_data_type(1)
#     #测试ack
#     dhcp.recv_and_send_ack()
#     #测试nack
#     dhcp.recv_and_send_NACK()
#     #测试续租
#     dhcp.dhcp_ip_timeout_and_renewal('192.168.1.222', 60)

