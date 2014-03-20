#!/usr/bin/env python
import networkx as nx
import pandas as pd
import numpy as np



def mention_graph_no_sentiment():

    df = pd.read_pickle('pickles/with_corenlp_mentions.p')

    G = nx.DiGraph()

    for n, row in df.iterrows():
        speaker = row['speaker']
        mentions = row['corenlp_mentions']
        for mention in mentions:
            G.add_edge(speaker, mentions)

    return G
