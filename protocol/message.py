import hashlib
import random
import struct
import time


class Message:
    magic = None
    command = None
    length = None
    checksum = None
    payload = None

    def __init__(self):
        self.magic = bytes.fromhex("F9BEB4D9")

    def makeGetaddrMessage(self):
        magic = bytes.fromhex("F9BEB4D9")
        command = "getaddr" + 5 * "\00"
        checksum = bytes.fromhex("5df6e0e2")

        return magic + bytes(command.encode("ascii")) + struct.pack("I", 0) + checksum

    def makePongMessage(self,prec_ping_nonce):
        magic = bytes.fromhex("F9BEB4D9")
        command = "pong" + 8 * "\00"
        payload = prec_ping_nonce
        length = len(payload)
        checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        return magic + bytes(command.encode("ascii")) + struct.pack("I", length) + checksum + payload

    def makeVerack(self):
        magic = bytes.fromhex("F9BEB4D9")
        command = "verack" + 6 * "\00"
        checksum = bytes.fromhex("5df6e0e2")
        return magic + bytes(command.encode("ascii")) + struct.pack("I", 0) + checksum


    def makeSendcmpctMessage(self):
        self.command = "sendcmpct" + 3 * "\00"
        self.payload = struct.pack("?",0) + struct.pack("<q",1)
        self.setLength()
        self.makeChecksum()
        return self.magic + bytes(self.command.encode("utf-8")) + bytes(self.length) + self.checksum + self.payload

    def makeVersion(self,ip):
        magic = bytes.fromhex("F9BEB4D9")
        command = bytes(("version" + 5 * "\00").encode("utf-8"))
        version = 70015
        services = 0
        timestamp = int(time.time())
        addr1 = b"127.0.0.1"
        addr2 = bytes(ip.encode())
        port = 8333
        agent = 0
        height = 565763
        nonce = random.getrandbits(64)
        payload = bytearray(86)

        struct.pack_into('=iQqQ16sHQ16sHQBi?', payload, 0, version, services,
                         timestamp, services, addr2, port, services, addr1, port,
                         nonce, agent, height, False)
        checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]

        return magic + command + struct.pack("I", len(payload)) + checksum + payload



    def makeVersionPayload(self, version, services, timestamp, addr_recv_services,
                           addr_recv_ip, addr_recv_port, addr_trans_services,
                           addr_trans_ip, addr_trans_port, user_agent_bytes,
                           starting_height):
        self.payload = struct.pack("i", version) + struct.pack("Q", services) + struct.pack("q", int(
            timestamp)) + struct.pack("Q", addr_recv_services) \
                       + struct.pack(">16s", addr_recv_ip) + struct.pack(">H", addr_recv_port) + struct.pack("Q",
                                                                                                             addr_trans_services) \
                       + struct.pack(">16s", addr_trans_ip) + struct.pack(">H", addr_trans_port) + struct.pack("Q",
                                                                                                               random.getrandbits(
                                                                                                                   64)) \
                       + struct.pack("B", user_agent_bytes) + struct.pack("i", starting_height) + struct.pack("?",
                                                                                                              False)

    def setLength(self):
        self.length = struct.pack("I", len(self.payload))

    def setCommand(self, command):
        self.command = command

    def makeChecksum(self):
        self.checksum = hashlib.sha256(hashlib.sha256(self.payload).digest()).digest()[:4]

    def getMsg(self):
        return self.magic + bytes(self.command.encode("utf-8")) + bytes(self.length) + self.checksum + self.payload

    def makePingMessage(self):
        self.command = "ping" + 8 * "\00"
        self.payload = struct.pack("Q",random.getrandbits(64))
        self.setLength()
        self.makeChecksum()

        return self.magic + bytes(self.command.encode("ascii")) + bytes(self.length) + self.checksum + self.payload

    def makeVerackMessage(self):
        self.command = "verack" + 6 * "\00"
        self.checksum = bytes.fromhex("5df6e0e2")

        return self.magic + bytes(self.command.encode("ascii")) + struct.pack("I", 0) + self.checksum


    def makeAddrMessage(self):
        self.command = "addr" + 8 * "\00"
        self.payload = struct.pack("i", 1) + struct.pack("q", int(time.time())) + struct.pack("q", int(time.time())) \
            + struct.pack("Q", 0) + struct.pack(">16s", b"127.0.0.1") + struct.pack(">H", 8333)
        self.length = len(self.payload)
        self.checksum = hashlib.sha256(hashlib.sha256(self.payload).digest()).digest()[:4]
        return self.magic + bytes(self.command.encode("ascii")) + struct.pack("I", self.length) + self.checksum \
            + self.payload


