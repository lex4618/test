# -*- coding: utf-8 -*-

import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]

from akcommon_define import *


class P2D_interface(object):
    def __init__(self, ip, user_name='admin', password='admin', time_out=20):
        url = 'http://%s/dclient/mockipc' % ip
        self.http_client = AkRequests(url, user_name, password, time_out)
        self.dclient_decrypt = DClient_Decrypt()
        self.dclient_decrypt_thread = None

    def close(self):
        self.http_client.close()

    def http_send_post(self, post_data):
        self.http_client.send_post(post_data)

    def decrypt_msg_from_scapy(self, src_mac, trans_type, dst_ip, dst_port, timeout=10):
        self.dclient_decrypt_thread = AkThread(target=self.dclient_decrypt.decrypt_msg_from_scapy,
                                               args=(src_mac, trans_type, dst_ip, dst_port, timeout))
        self.dclient_decrypt_thread.daemon = True  # 将主线程设置为守护线程，主线程停止时，所有子线程也同时停止运行
        self.dclient_decrypt_thread.start()  # 启用线程执行，避免界面假死未响应

    def get_decrypt_msg(self):
        self.dclient_decrypt_thread.join()
        return self.dclient_decrypt_thread.get_result()


if __name__ == '__main__':
    print('测试代码')
    # interface1 = P2D_interface('192.168.88.196')
    interface2 = P2D_interface('192.168.88.196')
    data = {"ipc_id": "F1001E",
				"param1": 0,
				"param2": 0,
				"lpdata": {
					"nSequenceNum": 1,
					"szDTMF": "1",
					"szFrom": "1",
					"szTo": "1"}}

    # interface1.http_send_post(data)
    interface2.http_send_post(data)
