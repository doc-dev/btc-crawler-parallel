import pylab as pl
import numpy as np


d = dict()

with open("geotag_chart.txt", "r") as f:
    c = f.readlines()
    for line in c:
        line = line.split(",")
        key = line[0]
        value = int(line[1])
        if value > 50:
            d[key] = value


X = np.arange(len(d))
pl.bar(X, d.values(), align='center', width=0.8)
pl.title("Geolocalizzazione Nodi Bitcoin")
pl.xticks(X, d.keys(), rotation='vertical')
ymax = max(d.values()) + 1
pl.ylim(0, ymax)
pl.show()