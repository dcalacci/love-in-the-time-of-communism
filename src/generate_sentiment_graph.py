#!/usr/bin/env python
import pandas as pd
import numpy as np
import corenlp_utils
import sentiment_utils
import networkx


G = networkx.read_gml('graphs/unweighted.gml')
df = pd.read_pickle('pickles/final_sentiment.p')

G_all_sent = G.copy()
n = 0
for edge in G.edges_iter():
    n += 1
    if n % 50 == 0:
        print n, "edges analyzed"

    a_name = unicode(G.node[edge[0]]['label'])
    b_name = unicode(G.node[edge[1]]['label'])

    sentiment = sentiment_utils.sent_from_a_to_b(df, a_name, b_name)
    #G_sent.add_edge(a_name, b_name, weight=sentiment)
    if sentiment:
        # I can't seem to get networkx to save this graph CORRECTLY as gml.
        # revisit later.
        G_all_sent.add_edge(a_name, b_name, weight=sentiment)        
