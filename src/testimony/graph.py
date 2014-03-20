#!/usr/bin/env python
import os
import pickle
import itertools
import networkx as nx
from config import graphs_dir

# class NamedGraph:
#     def __init__(self):
        
#         # list of graphs. temporary until you merge them
#         self.graphs = []
#         for p in os.listdir(graphs_dir):
#             self.graphs.append(pickle.load(open(p, "rb")))

#def clean_graph(d)

def find_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if not graph.has_key(start):
        return None
    for node in graph[start]:
        if node not in path:
            newpath = find_path(graph, node, end, path)
            if newpath: return newpath
    return None

def find_all_paths(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return [path]
    if not graph.has_key(start):
        return []
    paths = []
    for node in graph[start]:
        if node not in path:
            newpaths = find_all_paths(graph, node, end, path)
            for newpath in newpaths:
                paths.append(newpath)
    return paths

def get_intersection_graph(d, transcripts):
    graph = []
    for informer, nameds in d.items():
        datum = {}
        close_name = transcripts.get_closest_name(informer)
        print "informer: ", informer
        if close_name:
            datum["name"] = close_name
            datum["named"] = nameds
            graph.append(datum)
    return graph


def get_named_speechacts_list(datum, transcripts):
    named_data = []
    for data in datum:
        informer = data["name"]
        nameds = data["named"]
        print "examining : ", informer
        for name in nameds:
            speechacts = transcripts.get_speech_acts_by_speaker_and_phrase(informer, name)
            if speechacts:
                data = {}
                data['informer'] = informer
                data['named'] = name
                data['speechacts'] = speechacts
                named_data.append(data)
    return named_data

def get_named_speechacts(d, transcripts):
    "dict of who named whom, transcripts is a transcripts object."
    named_data = []
    for informer, named in d.items():
        print "examining : ", informer
        for name in named:
            speechacts = transcripts.get_speech_acts_by_speaker_and_phrase(informer, name)
            if speechacts:
                data = {}
                data['informer'] = informer
                data['named'] = name
                data['speechacts'] = speechacts
                named_data.append(data)
    return named_data

def __get_pickle(name):
    return pickle.load(open(os.path.join(graphs_dir, name+".p"), "rb"))

def get_named_graph(pickle_name):
    "makes unweighted, directed graph of naming"
    p = __get_pickle(pickle_name)
    
    named_graph = nx.DiGraph() # directed graph
    for d in p:
        for named in d['named']:
            named_graph.add_edge(d['name'], named)

    return named_graph

#    pos = nx.spring_layout(named_graph)

    #nx.draw_networkx(named_graph, pos)

# misc. utils. scratch, really.
def keep2(last, full):
    for word in full.split():
        if word == last:
            return True
    return False

def merge_dicts(d1, d2):
    new = {}
    for key, val in d1.items():
        newval = list(val)
        if key in d2.keys():
            newval.extend(d2[key])
#            print newval
            d2.pop(key, None) # remove it from d2
        newval = list(set(newval)) # remove dupes
        new[key] = newval

    for key, val in d2.items():
        new[key] = val

    return new
