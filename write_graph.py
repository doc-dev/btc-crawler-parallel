import networkx as nx

d = dict()

with open("snapshot-BitcoinNetwork15-03-2019 10:17:19 1Q7RTVNX.txt" , "r") as f:
    lines = f.readlines()
    for line in lines:
        values = list()
        line = line.split(",")
        key = line[0]
        line = line[1:]
        d[key] = line



G = nx.Graph()
G.add_nodes_from(d.keys())

for key in d:
    key = key.replace("\n", "")
    edges = list()
    for elem in d[key]:
        elem = elem.replace("\n","")
        edges.append((key,elem))
    G.add_edges_from(edges)


print("Deploying...")

nx.write_gexf(G, "test.gexf")