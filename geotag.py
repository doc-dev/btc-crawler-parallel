import json
import random
from multiprocessing import Manager, Process
from time import sleep
import requests
import matplotlib.pyplot as plt

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
                sleep(10)


ports = [9050, 9060, 9070, 9080, 9090, 9100, 9110, 9120]
url = "https://geoip-db.com/json/"
headers = {'Connection': 'Keep-Alive',
               "User-Agent": 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0',
               'Keep-Alive': 'timeout=20'}


def geotag_parallel(q,l):
    while True:
        ip = q.get()
        if ip is None:
            exit(1)
        proxy = {
            'http': "socks5h://localhost:{}".format(random.choice(ports))
        }
        r = requests.get(url + ip, proxies=proxy).content
        data = json.loads(r)
        country = data["country_name"]
        if country in l:
            l[country] += 1
        else:
            l[country] =  1
        print("INFO : Remaining " + str(q.qsize()))

stats = Manager().dict()
queue = SmartQueue()
with open("snapshot-BitcoinNodes15-03-2019 07:08:05 1Q7RTVNX.txt" , "r") as f:
    lines = f.readlines()
    for line in lines:
        line = line.replace("\n","")
        queue.put(line)

print("READ " + str(queue.qsize()))
#adesso devo procedere con il geotagging, inizializzo tor
for i in range(40):
    p = Process(target=geotag_parallel, args=(queue, stats)).start()

sleep(10)
queue.join()


with open("geotag_chart.txt","w") as f:
    for k in stats:
        if k:
            f.write(k + ","+ str(stats[k]) +"\n")

plt.barh(range(len(stats)), list(stats.values()), align='center')
plt.yticks(range(len(stats)), list(stats.keys()))
plt.show()


