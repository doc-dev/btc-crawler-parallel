import datetime
import ipaddress
import socket
from threading import Timer
import socks
import struct
from termcolor import colored
import protocol.message as message


class Client:
    socket = None
    dest_ip = None
    dest_port = None
    magic = bytes.fromhex("F9BEB4D9")
    payload = None
    list = []
    real_number = 0
    security = None
    all_peers = []
    map = None
    proxy = None
    flag = 0
    queue = None
    h = 0

    def __init__(self, queue):
        self.map = queue

    def now(self):
        return "[" + str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")) + "]"

    def testIp(self, bytearr):
        # i primi 10 bytes sono a zero
        # i secondi 2 sono a uno
        # gli altri 4 sono ipv4
        x = bytearr[:16]
        mapped = x[-4:]
        hex = bytearr.hex()

        if "00000000000000000000ffff" in x.hex():
            return str(ipaddress.IPv4Address(mapped))
        elif "3132372e302e302e31" in hex or "302e302e302e30a" in hex:
            return str(ipaddress.IPv4Address(bytes(map(int, "127.0.0.1".split('.')))))
        else:
            return None

    def readuntilnext(self, socket):
        socket.settimeout(None)
        data = bytes()
        print(colored(
            (self.now() + "[WARNING] fragmentation detected, reading more data..."), "yellow"))
        while 1:
            x = socket.recv(4)
            if self.magic.hex() in x.hex():
                self.flag = 1
                self.h = -99
                print(
                    colored((self.now() + "[NOTICE] fragmentation recovery completed, read other " + str(
                        len(data)) + " bytes"), "green"))

                return data
            data += x

    def emergency_exit(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            pass
        print(colored(
            (self.now() + "[WARNING] Connection timed out "),
            "red"))

    def connect(self, dest_ip, dest_port, tor_id, security, timeout):
        self.dest_ip = str(dest_ip)
        self.dest_port = dest_port
        self.security = security
        print(self.now() +
              "[NOTICE] i'll try to connect with peer " + str(self.dest_ip))

        self.socket = socks.socksocket()
        if timeout is not None:
            self.socket.settimeout(timeout)
        if 1 == self.security:
            self.socket.setproxy(socks.PROXY_TYPE_SOCKS5, "localhost", tor_id)
        try:
            self.socket.connect((self.dest_ip, self.dest_port))
        except Exception as e:
            return None

        print(colored((self.now(
        ) + "[NOTICE] connection established with peer " + str(self.dest_ip)), "green"))
        return 1

    def newList(self):
        list = []
        c = 0
        p_bytes = None
        m = message.Message()
        version = m.makeVersion(self.dest_ip)
        self.socket.send(version)
        global timer
        timer = Timer(120.0, self.emergency_exit)
        timer.start()
        while True:
            if (self.flag):
                response = self.socket.recv(20)
                # leggo i primi 24 byte, e recupero la lunghezza del payload e il command
                rcv_command = bytearray.fromhex(response[0:12].hex()).decode()
                # print(colored((self.now() + "[COMMAND] : received command " + rcv_command.rstrip('\00')), "cyan"))

                length = int.from_bytes(response[16:20], byteorder="little")
                self.payload = self.socket.recv(length)
                self.flag = 0
            else:
                try:
                    response = self.socket.recv(24)
                except Exception as e:
                    return None
                if (response is None or len(response) == 0):
                    print(colored(
                        (self.now(
                        ) + "[NOTICE] connection closed by remote peer  " + str(self.dest_ip) + " Bye"),
                        "red"))
                    self.map[self.dest_ip] = ["Refused", ]
                    return None
                # leggo i primi 24 byte, e recupero la lunghezza del payload e il command
                try:
                    rcv_command = bytearray.fromhex(
                        response[4:16].hex()).decode()
                    # print(colored((self.now() + "[COMMAND] : received command " + rcv_command.rstrip('\00')), "cyan"))
                    length = int.from_bytes(
                        response[16:20], byteorder="little")
                    try:
                        self.payload = self.socket.recv(length)
                    except Exception as e:
                        return None
                except:
                    return None

            if "ping" in rcv_command:
                if c > 1:
                    self.map[self.dest_ip] = ["Timeout", ]
                    return None
                else:
                    c += 1
                m = message.Message()
                pong = m.makePongMessage(self.payload)
                self.socket.send(pong)
                # print(colored((self.now() + "[ACTION] : sent response as pong message"), "yellow"))

            elif "addr" in rcv_command and self.flag == 0:
                # il primo byte del payload mi dice il numero di ip presenti
                n_ip = struct.unpack('B', self.payload[0:1])[0]
                a = []
                # abbiamo un po' di casi da verificare :
                if (n_ip < int("fd", 16)):
                    # allora è il caso semplice
                    self.payload = self.payload[13:]
                    self.real_number = n_ip
                elif (n_ip == int("fd", 16)):
                    timer.cancel()
                    self.payload = self.payload[15:]
                    try:
                        b = self.readuntilnext(self.socket)
                        self.payload = self.payload + b
                    except Exception:
                        pass

                tmp = self.payload

                while tmp:
                    a.append(tmp[:30])
                    tmp = tmp[30:]

                if (self.h == -99):
                    self.socket.shutdown(socket.SHUT_RDWR)
                    self.socket.close()
                    for elem in a:
                        ip = self.testIp(elem)
                        if ip is not None:
                            if ip not in self.map:
                                list.append(ip)

                    for ip in list:
                        self.map[ip] = []
                    self.map[self.dest_ip] = list
                    print(
                        colored((self.now() + "[ACTION] : Work Finished"), "red"))

                    return list
                else:
                    for elem in a:
                        ip = self.testIp(elem)
                        if ip is not None:
                            if ip not in self.map:
                                list.append(ip)

            elif ("version" in rcv_command):
                # ho ricevuto un verack, quindi ne stampo il contenuto
                # print(self.now() + "[NOTICE] : verack received by " + str(self.dest_ip))
                # si ma chi sono io ?
                myaddr = ipaddress.IPv4Address((self.payload[28:44])[12:])
                print(colored(
                    (self.now() + "[NOTICE] : remote peer believes i am  " + str(myaddr)), "red"))

                # ora devo fare anche io un verack
                m = message.Message()
                verack = m.makeVerackMessage()
                self.socket.send(verack)
                # print(self.now() + "[NOTICE] : verack sent to peer " + str(self.dest_ip))
                # mando il get addr
                m = message.Message()
                getaddr = m.makeGetaddrMessage()
                self.socket.send(getaddr)
                # print(colored(self.now() + "[NOTICE] : getaddr sent to peer " + str(self.dest_ip), "red"))

            elif ("sendcmpct" in rcv_command):
                boolean = int.from_bytes(self.payload[0:1], byteorder="little")
                second_integer = int.from_bytes(
                    self.payload[1:9], byteorder="little")
                if (boolean == 1 and second_integer == 1):
                    # print(self.now() + "[NOTICE] : peer " + str(
                    # self.dest_ip) + " wants new block announcements as cmpctblock")
                    if (second_integer != 1):
                        k = message.Message()
                        self.socket.send(k.makeSendcmpctMessage())
                    # print(colored((self.now() + "[ACTION] : sent my sendcmpct message"), "yellow"))

            elif "pong" in rcv_command:
                # vedo se i bytes sono esatti
                if (p_bytes.hex() == self.payload.hex()):
                    # print(colored((self.now() + "[NOTICE] : received pong message for previous ping"), "yellow"))
                    a = 2 + 2

    def getNeigh(self):
        list = []
        c = 0
        m = message.Message()
        version = m.makeVersion(self.dest_ip)
        global timer
        timer = Timer(30.0, self.emergency_exit)
        timer.start()
        try:
            self.socket.send(version)
        except Exception:
            return ["Refused", ]
        while True:
            if (self.flag):
                try:
                    response = self.socket.recv(20)
                except Exception:
                    return ["Refused", ]
                rcv_command = bytearray.fromhex(response[0:12].hex()).decode()
                length = int.from_bytes(response[16:20], byteorder="little")
                self.payload = self.socket.recv(length)
                self.flag = 0
            else:
                try:
                    response = self.socket.recv(24)
                except Exception:
                    print(colored(
                        (self.now(
                        ) + "[NOTICE] connection closed by remote peer  " + str(self.dest_ip) + " Bye"),
                        "red"))
                    return ["Refused", ]
                try:
                    rcv_command = bytearray.fromhex(
                        response[4:16].hex()).decode()
                    length = int.from_bytes(
                        response[16:20], byteorder="little")
                    try:
                        self.payload = self.socket.recv(length)
                    except Exception as e:
                        return ["Error", ]
                except:
                    return ["Error", ]

                if "ping" in rcv_command:
                    m = message.Message()
                    pong = m.makePongMessage(self.payload)
                    self.socket.send(pong)
                    if c > 1:
                        return ["Timeout", ]
                    else:
                        c += 1
                    # print(colored((self.now() + "[ACTION] : sent response as pong message"), "yellow"))

                elif "addr" in rcv_command and self.flag == 0:
                    # il primo byte del payload mi dice il numero di ip presenti
                    n_ip = struct.unpack('B', self.payload[0:1])[0]
                    a = []
                    if (n_ip < int("fd", 16)):
                        self.payload = self.payload[13:]
                        self.real_number = n_ip

                    elif (n_ip == int("fd", 16)):
                        timer.cancel()
                        self.payload = self.payload[15:]
                        try:
                            b = self.readuntilnext(self.socket)
                            self.payload = self.payload + b
                        except Exception:
                            pass

                    tmp = self.payload

                    while tmp:
                        a.append(tmp[:30])
                        tmp = tmp[30:]

                    if (self.h == -99):
                        self.socket.shutdown(socket.SHUT_RDWR)
                        self.socket.close()
                        for elem in a:
                            ip = self.testIp(elem)
                            if ip is not None:
                                list.append(ip)

                        print(
                            colored((self.now() + "[ACTION] : Work Finished"), "red"))
                        return list

                    else:
                        for elem in a:
                            ip = self.testIp(elem)
                            if ip is not None:
                                list.append(ip)

                elif ("version" in rcv_command):

                    myaddr = ipaddress.IPv4Address((self.payload[28:44])[12:])
                    print(colored(
                        (self.now() + "[NOTICE] : remote peer believes i am  " + str(myaddr)), "red"))

                    # ora devo fare anche io un verack
                    m = message.Message()
                    verack = m.makeVerackMessage()
                    self.socket.send(verack)
                    # print(self.now() + "[NOTICE] : verack sent to peer " + str(self.dest_ip))
                    # mando il get addr
                    m = message.Message()
                    getaddr = m.makeGetaddrMessage()
                    self.socket.send(getaddr)
                    # print(colored(self.now() + "[NOTICE] : getaddr sent to peer " + str(self.dest_ip), "red"))

                elif ("sendcmpct" in rcv_command):
                    boolean = int.from_bytes(
                        self.payload[0:1], byteorder="little")
                    second_integer = int.from_bytes(
                        self.payload[1:9], byteorder="little")
                    if (boolean == 1 and second_integer == 1):
                        # print(self.now() + "[NOTICE] : peer " + str(
                        # self.dest_ip) + " wants new block announcements as cmpctblock")
                        if (second_integer != 1):
                            k = message.Message()
                            self.socket.send(k.makeSendcmpctMessage())
