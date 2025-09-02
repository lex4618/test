# -*- coding: UTF-8 -*-
from akcommon_define import *
import cv2
import threading
import numpy as np
from random import choices, randrange
import os
import sys
import string
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
from twisted.protocols.basic import LineReceiver
import subprocess

root_path = os.getcwd()
pos = root_path.find("AKautotest")

if pos == -1:
    print("runtime error")
    exit(1)

root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

class RTSPProtocol(LineReceiver):
    def __init__(self, mp4_path, response_headers=None, result=None):
        self.state = "COMMAND"
        self.buffer = b""
        self.session = ''.join(choices(string.ascii_lowercase + string.digits, k=9))
        self.process = None
        self.client_port = None
        self._mp4_path = mp4_path
        self.response_headers = response_headers or {}  # Store response headers
        self.initial_seq = random.randint(0, 65535)
        self.initial_rtptime = random.randint(0, 4294967295)
        self.result = result

    def dataReceived(self, data):
        self.buffer += data
        while self.buffer:
            if self.buffer.startswith(b'$'):
                if len(self.buffer) < 4:
                    break  # Wait for more data
                length = int.from_bytes(self.buffer[2:4], byteorder='big')
                rtp_packet_length = 4 + length
                if len(self.buffer) < rtp_packet_length:
                    break  # Wait for more data
                rtp_packet = self.buffer[:rtp_packet_length]
                self.buffer = self.buffer[rtp_packet_length:]
                self.handleRTPPacket(rtp_packet)
            else:
                line, sep, self.buffer = self.buffer.partition(b'\r\n')
                if sep:
                    self.lineReceived(line)
                else:
                    break  # Wait for more data

    def lineReceived(self, line):
        print("Received line:", line)
        if line.strip() == b"":
            self.handleCommandComplete()
        else:
            self.buffer += line + b'\r\n'

    def handleRTPPacket(self, packet):
        print("Received RTP packet:", packet)
        if len(packet) < 4:
            return
        length = int.from_bytes(packet[2:4], byteorder='big')
        rtp_packet_length = 4 + length
        if len(packet) >= rtp_packet_length:
            rtp_data = packet[4:rtp_packet_length]
            print("Processed RTP packet data:", rtp_data)

    def handleCommandComplete(self):
        try:
            lines = self.buffer.decode('utf-8').split('\r\n')
        except UnicodeDecodeError:
            print("Failed to decode buffer:", self.buffer)
            self.sendError(400, "Bad Request")
            self.buffer = b""
            return

        if len(lines) < 1:
            self.sendError(400, "Bad Request")
            return

        request_line = lines[0].split()

        if len(request_line) < 3:
            self.sendError(400, "Bad Request")
            return

        self.method = request_line[0]
        self.uri = request_line[1]
        self.version = request_line[2]

        headers = {}
        for line in lines[1:]:
            if line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        if self.method == "OPTIONS":
            self.handleOptions(headers)
        elif self.method == "DESCRIBE":
            self.handleDescribe(headers)
        elif self.method == "SETUP":
            self.handleSetup(headers)
        elif self.method == "PLAY":
            self.handlePlay(headers)
        elif self.method == "PAUSE":
            self.handlePause(headers)
        elif self.method == "TEARDOWN":
            self.handleTeardown(headers)
        else:
            self.sendError(501, "Not Implemented")

        self.result.put(self.method)
        self.buffer = b""

    def handleOptions(self, headers):
        response_headers = self.response_headers.get("OPTIONS", {})
        if not response_headers:
            response_headers = {
                "Public": "OPTIONS, DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE, SET_PARAMETER, GET_PARAMETER"
            }
        self.sendResponse(200, "OK", response_headers)

    def handleDescribe(self, headers):
        default_sdp = """v=0
o=- 0 0 IN IP4 127.0.0.1
s=No Name
c=IN IP4 0.0.0.0
t=0 0
a=tool:libavformat 61.1.100
m=video 8000 RTP/AVP 96
a=rtpmap:96 H264/90000
a=fmtp:96 packetization-mode=1; sprop-parameter-sets=Z2QAKKwbGoB4Aiflm4KAgoPCIRuA,aOpDyw==; profile-level-id=640028"""
        sdp = self.response_headers.get("DESCRIBE", {}).get("sdp", default_sdp)
        sdp = sdp.replace('\n', '\r\n')
        describe_info = self.response_headers.get("DESCRIBE", {})
        # 排除 'sdp' 键并构建新的字典
        response_headers = {key: value for key, value in describe_info.items() if key != "sdp"}
        if not response_headers:
            response_headers = {
                "Content-Base": self.uri,
                "Content-Type": "application/sdp",
                "Content-Length": str(len(sdp))
            }
        response_headers["Content-Length"] = str(len(sdp))
        aklog_info(response_headers)
        self.sendResponse(200, "OK", response_headers, sdp)

    def handleSetup(self, headers):
        transport = headers.get("Transport", "")
        if "client_port" in transport:
            client_port = transport.split("client_port=")[-1].split("-")
            self.client_port = (int(client_port[0]), int(client_port[1]))
            transport_response = f"RTP/AVP;unicast;client_port={self.client_port[0]}-{self.client_port[1]};server_port=8000-8001"
        elif "interleaved" in transport:
            interleaved = transport.split("interleaved=")[-1].split("-")
            self.client_port = (int(interleaved[0]), int(interleaved[1]))
            transport_response = f"RTP/AVP/TCP;unicast;interleaved={self.client_port[0]}-{self.client_port[1]}"
        else:
            self.sendError(400, "Bad Request")
            return

        response_headers = self.response_headers.get("SETUP", {})
        if not response_headers:
            response_headers = {
                "Transport": transport_response,
                "Session": self.session
            }
        self.sendResponse(200, "OK", response_headers)

    def handlePlay(self, headers):
        if not self.process:
            self.process = subprocess.Popen([
                "ffmpeg",
                "-re",
                "-i", self._mp4_path,
                "-an",
                "-c:v", "copy",
                "-f", "rtp",
                f"rtp://127.0.0.1:{self.client_port[0]}"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        response_headers = self.response_headers.get("PLAY", {})
        if not response_headers:
            response_headers = {
                "RTP-Info": f"url={self.uri};seq={self.initial_seq};rtptime={self.initial_rtptime}",
                "Session": self.session
            }
        self.sendResponse(200, "OK", response_headers)

    def handlePause(self, headers):
        if self.process:
            self.process.terminate()
            self.process = None
        response_headers = self.response_headers.get("PAUSE", {})
        if not response_headers:
            response_headers = {
                "Session": self.session
            }
        self.sendResponse(200, "OK", response_headers)

    def handleTeardown(self, headers):
        if self.process:
            self.process.terminate()
            self.process = None
        response_headers = self.response_headers.get("TEARDOWN", {})
        if not response_headers:
            response_headers = {
                "Session": self.session
            }
        self.sendResponse(200, "OK", response_headers)

    def sendResponse(self, code, message, headers={}, body=None):
        response = "RTSP/1.0 {} {}\r\n".format(code, message)
        for header, value in headers.items():
            response += "{}: {}\r\n".format(header, value)
        response += "\r\n"
        if body:
            response += body
        self.transport.write(response.encode('utf-8'))

    def sendError(self, code, message):
        self.sendResponse(code, message)


class RTSPFactory(Factory):
    def __init__(self, mp4_path, response_headers=None, result=None):
        self.mp4_path = mp4_path
        self.response_headers = response_headers  # Store response headers
        self.result = result

    def buildProtocol(self, addr):
        return RTSPProtocol(self.mp4_path, self.response_headers, self.result)

def start_rtsp_server(mp4_path, port=8554, response_headers=None, result=None):
    reactor.listenTCP(port, RTSPFactory(mp4_path, response_headers, result))
    reactor.run(installSignalHandlers=False)

def run_server_in_process(mp4_path, port=8554, response_headers=None, result=None):
    server_process = Process(target=start_rtsp_server, args=(mp4_path, port, response_headers, result))
    server_process.start()
    return server_process

if __name__ == '__main__':
    mp4_path = "C:\\Users\\Administrator\\Videos\\Captures\\video1.mp4"
    response_headers = {
        "OPTIONS": {"Custom-Header-Options": "CustomValueOptions"},
        "DESCRIBE": {"Custom-Header-Describe": "CustomValueDescribe"},
        "SETUP": {"Custom-Header-Setup": "CustomValueSetup"},
        "PLAY": {"Custom-Header-Play": "CustomValuePlay"},
        "PAUSE": {"Custom-Header-Pause": "CustomValuePause"},
        "TEARDOWN": {"Custom-Header-Teardown": "CustomValueTeardown"}
    }
    reactor.listenTCP(8554, RTSPFactory(mp4_path, response_headers))
    reactor.run()
