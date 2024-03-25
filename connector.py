import threading, json, time
import socket
import traceback

from share import gstore

IP = "127.0.0.1"
SERVER_PORT = 47554
BUFLEN = 1024


class Connector:
    def __init__(self):
        self.dataSocket = None
        self.connected = False

    def sendMsg(self, msgType: str, msgBody: dict):
        if not self.connected:
            return

        msgCode = f"{time.time()}"

        msgHeaderStr = f"BF01|{msgType}|0|{msgCode}$"
        msgBodyStr = json.dumps(msgBody)

        msgBytes = (msgHeaderStr + msgBodyStr).encode() + b"\x04"
        # print(msgBytes)
        self.dataSocket.sendall(msgBytes)

    def msg_decode(self, msgBytes: bytes):
        #     BF01|notify-to-frontend|0|1695899578730990${
        #     "device-sn":"aaaa0001","CO":0.05,"HCl":0.01,"SO2":0.01}
        msgStr = msgBytes.decode("ascii")
        parts = msgStr.split("$", maxsplit=1)
        if len(parts) != 2:
            raise Exception("消息格式错误，没有$分隔符")

        msgHeaderStr, msgBodyStr = parts
        parts = msgHeaderStr.split("|")
        if len(parts) != 4:
            raise Exception("消息头格式错误")

        version, msgType, isResend, msgCode = parts
        # print(msgBodyStr)
        msgBody = json.loads(msgBodyStr)

        return msgType, msgCode, msgBody

    def connectionRun(
        self,
    ):

        self.connected = False

        recvbuffer = b""
        # 实例化一个socket对象，指明协议
        self.dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 连接服务端socket
        self.dataSocket.connect((IP, SERVER_PORT))
        print("connection to server ok")
        self.connected = True

        while True:

            try:
                # 等待接收服务端的消息
                recved = self.dataSocket.recv(BUFLEN)
            except socket.timeout:
                continue
            except:
                print(traceback.format_exc())
                break

            # 如果返回空bytes，表示对方关闭了连接
            if not recved:
                print("server closed connection")
                break
            # 打印读取的信息

            recvbuffer += recved

            # 循环处理当前buffer里面的完整消息
            while True:

                endPos = recvbuffer.find(b"\x04")

                # 还没有接收到完整的消息
                if endPos < 0:
                    break

                # 接收到完整的消息
                msgBytes = recvbuffer[:endPos]
                # print('\n收到消息', msgBytes)
                recvbuffer = recvbuffer[endPos + 1 :]

                # 处理这个消息
                try:
                    msgType, msgCode, msgBody = self.msg_decode(msgBytes)
                except:
                    print(traceback.format_exc())
                    continue

                if msgType == "notify-to-frontend":
                    deviceSn = msgBody.get("device-sn")
                    if not deviceSn:
                        print("device-sn 字段缺失")
                        continue

                    if deviceSn == "stats":
                        gstore.main_window.dso.mdata_change.emit(msgBody)
                        continue

                    if deviceSn not in gstore.deviceSn_to_item:
                        # print(f'device-sn : {deviceSn} 不存在')
                        continue

                    gstore.deviceSn_to_item[deviceSn].dso.mdata_change.emit(msgBody)

        self.dataSocket.close()


connector = Connector()


def connectThread():
    while True:
        try:
            connector.connectionRun()
        except ConnectionRefusedError:
            pass
        except:
            print(traceback.format_exc())
            pass


def startCommunicationThread():
    thread = threading.Thread(target=connectThread, daemon=True)
    thread.start()
