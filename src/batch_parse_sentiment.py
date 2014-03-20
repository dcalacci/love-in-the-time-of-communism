#!/usr/bin/env python

import pickle
import os
import shutil
import pandas as pd
import numpy as np
from corenlp import batch_parse

corenlp_dir = '../src/external/corenlp-python/stanford-corenlp-full-2014-01-04'
init_dir = '../data/pickles/speechacts/'

num_files = len(os.listdir(init_dir))
count = 0
last_file_name = ''
sentiment = []

def wrapper(generator):
    while True:
        try:
            yield next(generator)
        # except StopIteration:
        #    raise
        except Exception as e:
            print "exception!"
            print(e)
            yield np.nan

def parse_directory(fpath, sentiment=[], count=0):
    parsed = batch_parse(fpath, corenlp_dir)
    last_file_name = ''
    for obj in wrapper(parsed):

        if not pd.isnull(obj):
            last_file_name = obj['file_name']

        # the wrapper will return np.nan when it dies from an error.
        if pd.isnull(obj):
            sentiment.append(np.nan)
            return (last_file_name, count, sentiment)

        # otherwise do the normal thing.
        count += 1
        if count % 500 == 0:
            print "analyzed", count, "speechacts."
            temp_pickle_name = "corenlp_sentiment" + str(count) + "_tmp.p"
            print "analyzed", count, "speechacts. Saving temporary pickle as", temp_pickle_name
            pickle.dump(sentiment, open("pickles/" + temp_pickle_name, 'wb'))
        # if count % 5001 == 0:
        #     print "did 5k, stopping for now..."
        #     break
        speechact_sent = {}
        sentences = obj['sentences']
        for sentence in sentences:
            # key is the sentence
            speechact_sent[sentence['text']] = (sentence['sentiment'], sentence['sentimentValue'])
            speechact_sent.append((sentence['sentiment'], sentence['sentimentValue']))
        sentiment[]
        sentiment.append(speechact_sent)
    return sentiment

def move_files_to_new_directory(fpath, last_file_name, newdir_name):
    print 'looking at:', last_file_name
    n = 0
    speech_files = os.listdir(fpath)
    newdir = os.path.join(fpath, newdir_name)
    os.mkdir(newdir)
    for file_name in speech_files:
        if file_name > last_file_name and n != 0:
            full_file_name = os.path.join(fpath, file_name)
            shutil.copy(full_file_name, newdir)
        n += 1
    return newdir
            

current_path = init_dir
sentiment = []
count = 0
while count < num_files:
    res = parse_directory(current_path, sentiment, count)
    if type(res) != list: # it failed, we have the last file name
        print "processing broke. Moving next files to new directory..."
        count += res[1]
        sentiment.extend(sentiment)
        current_path = move_files_to_new_directory(current_path, res[0], res[0] + "_dir")
    else:
        print "finished"
        temp_pickle_name = "corenlp_sentiment_FINAL.p"        
        print "analyzed", count, "speechacts. Saving final pickle as", temp_pickle_name
        pickle.dump(sentiment, open("pickles/corenlp_sentiment/" + temp_pickle_name, 'wb'))
