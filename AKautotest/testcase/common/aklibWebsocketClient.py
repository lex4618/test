# -*- coding: utf-8 -*-
import json
import sys
import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *
import websocket  # pip install websocket-client==1.6.1
import time
import threading


class AkWebsocketClient(object):
    """docstring for WebsocketClient"""

    def __init__(self, address=None, message_callback=None, device_name=''):
        self.address = address
        self.message_callback = message_callback
        self.ready = False
        self.running = False
        self.ws_thread = None
        self.ws = None
        self.device_name = device_name

    def put_address(self, address):
        self.address = address

    def on_message(self, ws, message):
        if not ws:
            return
        if isinstance(message, str):
            # 去掉最外层的引号
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
                if '\\' in message:
                    message = message.replace('\\', '')
            message = json_loads_2_dict(message)
        if isinstance(message, dict):
            if message.get("type") == 'auth_required':
                aklog_debug('Websocket is required')
            if message.get('type') == 'auth_ok':
                aklog_debug('Websocket is ready')
                self.ready = True
        if self.message_callback:
            self.message_callback(message)

    @staticmethod
    def on_error(ws, error):
        if not ws:
            return
        aklog_printf("on_error: %s" % error)

    def on_close(self, ws, close_status_code, close_msg):
        if not ws:
            return
        aklog_printf("on_close: close_status_code: %s, close_msg: %s" % (close_status_code, close_msg))
        self.running = False
        self.ready = False

    def on_open(self, ws):
        if not ws:
            return
        aklog_printf('on_open')
        self.running = True

    def close_connect(self):
        if self.ws:
            self.ws.close()
            time.sleep(2)
        for i in range(3):
            if not self.running:
                break
            else:
                time.sleep(1)
                continue
        aklog_printf('ws closed')
        self.running = False
        self.ready = False
        self.ws = None

    def send_message(self, message):
        # aklog_printf('send msg: ', message)
        try:
            self.ws.send(message)
            return True
        except BaseException as err:
            aklog_printf(err)
            return False

    def run_forever(self):
        self.ws.run_forever(ping_interval=60, ping_timeout=10)

    def run(self, timeout=10):
        aklog_debug()
        # websocket.enableTrace(True)  # 有报错需要调试时可以开启
        self.close_connect()
        self.ws = websocket.WebSocketApp(
            self.address,
            on_open=lambda ws: self.on_open(ws),
            on_message=lambda ws, message: self.on_message(ws, message),
            on_error=lambda ws, error: self.on_error(ws, error),
            on_close=lambda ws, close_status_code, close_msg: self.on_close(ws, close_status_code, close_msg)
        )
        aklog_printf(f'Websocket connecting: {self.address} ...')
        self.ws_thread = threading.Thread(target=self.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        time.sleep(0.5)

        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.running:
                aklog_printf(f'Websocket connect {self.address} success')
                return True
            else:
                time.sleep(1)
                continue
        aklog_printf(f'Websocket connect {self.address} failed')
        return False


class AkWSClient(object):

    def __init__(self, address=None, device_name=''):
        self.msgs = []
        self.client = AkWebsocketClient(address, self.call_back, device_name)
        self.client_thread = None
        self.device_name = device_name

    def put_address(self, address):
        self.client.put_address(address)

    def put_device_name(self, device_name):
        self.device_name = device_name
        self.client.device_name = device_name

    def call_back(self, msg):  # 回调函数
        # print("dddd", msg)
        self.msgs.append(msg)

    def clear_msg(self, ws_id=None, index=None):
        if ws_id:
            for msg in self.msgs[::-1]:
                if msg.get('id') == ws_id:
                    self.msgs.remove(msg)
        elif index and len(self.msgs) > index:
            self.msgs = self.msgs[index:]
        else:
            self.msgs.clear()

    def wait_msg(self, timeout=5):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.msgs:
                return self.msgs
            time.sleep(0.1)
            continue
        return []

    def get_msg(self, ws_id=None) -> list:
        if ws_id is not None:
            if self.msgs:
                msgs = []
                for msg in self.msgs:
                    # 获取指定id的结果
                    if msg and msg.get('id') == ws_id:
                        msgs.append(msg)
                return msgs
            return []
        else:
            return self.msgs

    def is_running(self):
        return self.client.running

    def is_ready(self):
        return self.client.ready

    def wait_ready(self, timeout=20):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.client.ready:
                return True
            time.sleep(0.5)
            continue
        aklog_error('Websocket is not ready')
        return False

    def run(self, timeout=10):
        return self.client.run(timeout)

    def send_message(self, message):
        if isinstance(message, (list, dict)):
            message = json.dumps(message)
        return self.client.send_message(message)

    def close(self):
        self.client.close_connect()


if __name__ == "__main__":
    ws_client = AkWSClient("ws://192.168.88.133/api/websocket")
    ws_client.run()
    time.sleep(2)
    ws_client.close()
