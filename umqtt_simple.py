import usocket as socket
import ustruct as struct
import utime


class MQTTClient:
    def __init__(
        self, client_id, server, port=1883, user=None, password=None, keepalive=0
    ):
        self.client_id = client_id
        self.sock = None
        self.server = server
        self.port = port
        self.user = user
        self.pswd = password
        self.keepalive = keepalive
        self.pid = 0
        self.cb = None
        self.lw_topic = None
        self.lw_msg = None
        self.lw_qos = 0
        self.lw_retain = False

    def _write(self, data):
        self.sock.write(data)

    def _send_str(self, s):
        self._write(struct.pack("!H", len(s)))
        self._write(s)

    def connect(self, clean_session=True):
        self.sock = socket.socket()
        addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        self.sock.connect(addr)
        premsg = bytearray(b"\x10\0\0\0\0\0")
        msg = bytearray(b"\x04MQTT\x04\x02\0\0")

        sz = 10 + 2 + len(self.client_id)
        msg[6] = clean_session << 1
        if self.user:
            sz += 2 + len(self.user) + 2 + len(self.pswd)
            msg[6] |= 0xC0
        if self.keepalive:
            msg[7] |= self.keepalive >> 8
            msg[8] |= self.keepalive & 0xFF

        i = 1
        while sz > 0x7F:
            premsg[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        premsg[i] = sz
        self._write(premsg[: i + 2])
        self._write(msg)
        self._send_str(self.client_id)
        if self.user:
            self._send_str(self.user)
            self._send_str(self.pswd)
        resp = self.sock.read(4)
        if resp[0] != 0x20 or resp[1] != 0x02:
            raise Exception("Invalid CONNACK")
        if resp[3] != 0:
            raise Exception("Connection refused code %d" % resp[3])
        return True

    def publish(self, topic, msg, retain=False, qos=0):
        pkt = bytearray(b"\x30\0\0")
        pkt[0] |= qos << 1 | retain
        sz = 2 + len(topic) + len(msg)
        if qos > 0:
            sz += 2
        i = 1
        while sz > 0x7F:
            pkt[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        pkt[i] = sz
        self._write(pkt[: i + 1])
        self._send_str(topic)
        if qos > 0:
            self.pid += 1
            pid = self.pid
            self._write(struct.pack("!H", pid))
        self._write(msg)

    def disconnect(self):
        self._write(b"\xe0\0")
        self.sock.close()
