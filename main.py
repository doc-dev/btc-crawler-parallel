import random
import string
from datetime import datetime
from multiprocessing import Process, Manager, Queue
from time import sleep
import dns.resolver
from termcolor import colored
import queue
import protocol.client as c


list = [9050, 9060, 9070, 9080, 9090, 9100, 9110, 9120]


class SmartQueue():

    def __init__(self):
        self.mutex = Manager().Semaphore(1)
        self.list = Manager().list()

    def get(self):
        elem = None
        self.mutex.acquire()
        if len(self.list) > 0:
            elem = self.list.pop(0)
        self.mutex.release()
        return elem

    def put(self, elem):
        self.mutex.acquire()
        self.list.append(elem)
        self.mutex.release()

    def qsize(self):
        self.mutex.acquire()
        length = len(self.list)
        self.mutex.release()
        return length

    def join(self):
        while True:
            if self.qsize() == 0:
                return
            else:
                sleep(30)


def tree(q1, map):
    socks_port = random.choice(list)
    x = None
    if q1.empty():
        return
    try:
        ip = q1.get(timeout=10)
    except queue.Empty:
        print(colored("[INFO] Empty Queue", "magenta"))
        return
    if ip not in map:
        client = c.Client(map)
        try:
            x = client.connect(ip, 8333, socks_port, 1, 60)
        except:
            pass
        if x is not None:
            next_peers = client.newList()
            if next_peers is not None:
                for next in next_peers:
                    q1.put(next)
                    tree(q1, map)
    return


def getGraph(qu, graph):
    while True:
        socks_port = random.choice(list)
        x = random.randint(1, 100)
        ip = qu.get()
        if ip:
            try:
                if x > 64:
                    print(
                        colored(("[INFO] remaining to check  " + str(qu.qsize())), "blue"))
                client = c.Client(None)
                k = client.connect(ip, 8333, socks_port, 1, 30)
                if k is not None:
                    l = client.getNeigh()
                    graph[ip] = l
            except Exception as e:
                print(e)
                pass
        else:
            print(colored("[INFO] Empty Queue", "magenta"))
            exit(1)


if __name__ == '__main__':

    decorator = ''.join(
        [random.choice(string.ascii_letters + string.digits) for n in range(8)])
    decorator = decorator.upper()
    d = Manager().dict()
    peers_to_check = Queue()
    ps = []
    myResolver = dns.resolver.Resolver()
    myAnswers = myResolver.query("seed.bitcoin.sipa.be", "A")
    for ip in myAnswers:
        peers_to_check.put(str(ip))
    for i in range(len(myAnswers)):
        p = Process(target=tree, args=(peers_to_check, d))
        ps.append(p)
        p.start()

    for x in ps:
        x.join()

    x = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    filename = "snaps/snapshot-BitcoinNodes" + x + " "+decorator+".txt"

    with open(filename, "w") as f:
        for k in d:
            f.write(str(k) + "\n")

    print("Obtained all nodes in Bitcoin Network")
    print("Read " + str(len(d)) + " peers in total")
    print("Let's get the neighbourhood list for each peer")
    graph = Manager().dict()
    del peers_to_check
    peers = SmartQueue()
    workers = []
    for k in d:
        if len(d[k]) == 0:
            peers.put(k)

    for i in range(60):
        p = Process(target=getGraph, args=(peers, graph))
        workers.append(p)
        p.start()

    peers.join()

    print("Pruning deadwoods...")
    for p in workers:
        if p.is_alive():
            p.terminate()

    print("Final size  " + str(len(graph)))

    x = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    filename = "snaps/snapshot-BitcoinNetwork" + x + " " + decorator + ".txt"

    print("Obtained the neighbourhood list for each peer")

    with open(filename, "w") as f:
        for key in graph:
            f.write(key + "," + str(graph[key]).replace('\'',
                                                        '').replace('[', '').replace(']', '') + "\n")
