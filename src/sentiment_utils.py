#!/usr/bin/env python
import difflib
import Levenshtein
import pandas as pd
import numpy as np
import lexicons.lexiconUtils as sentimentUtils
from collections import defaultdict
from corenlp_utils import *
liwc = sentimentUtils.LiwcDict()

def is_negated(w, sen):
    """
    sen is an annotated sentence object, word is the annotated word from sen.
    uses negation information from the annotated sentence.
    """
    wordindex = sen['words'].index(w) + 1
    dependencies = sen['indexeddependencies']
    for dependency in dependencies:
        if dependency[0] == 'neg':
            # words and indices are separated by a hyphen
            words_and_indices = map(lambda w: w.split("-"), dependency[1:])
            # if the word and index are the same, it's negated.
            try:
                for word, index in words_and_indices:
                    if word == w[0] and int(index) == wordindex:
                        return True
            except ValueError:
                return False
    return False

def categories_for_word(w, sen):
    "grabs all applicable categories for the given word"
    word_text = w[1]['Lemma']
    if liwc.exists(word_text):
        categories = liwc.getCategories(word_text)
        
        if (liwc.isPosWord(word_text) or liwc.isNegWord(word_text)) and is_negated(w, sen):
            def replace_category(c):
                opposite = liwc.getOppositeCategory(c)
                if opposite:
                    return opposite
                else:
                    return c
            categories = map(replace_category, categories)
        return categories
    return None

def is_neg_word(w, sen):
    categories = categories_for_word(w, sen)
    if categories:
        return any(map(liwc.isNegCat, categories))
    else:
        return False

def is_pos_word(w, sen):
    categories = categories_for_word(w, sen)
    if categories:
        return any(map(liwc.isPosCat, categories))
    else:
        return False

def sentiment_score_for_word(w, sen):
    score = 0
    if is_pos_word(w, sen):
        score = 1
    elif is_neg_word(w, sen):
        score = -1
    return score

def score_of_word_towards_index(w, index, sen):
    wordlist = sen['words']
    word_index = wordlist.index(w)
    distance = min(map(lambda i: abs(i - word_index), [index[0], index[1]-1]))
    sentiment_score = sentiment_score_for_word(w, sen)
    score = sentiment_score/float(distance) # normalize
    return score

def liwc_sen_score_towards_index(indices, sen):
    start_index = indices[0]
    end_index = indices[1]
    wordlist = sen['words']
    scores = []
    for index, w in enumerate(wordlist):
        if index >= start_index and index < end_index:
            continue
        scores.append(score_of_word_towards_index(w, indices, sen))
    return (float(sum(scores)) / len(sen))

def liwc_overall_sentiment_of_sen(sen):
    wordlist = sen['words']
    scores = []
    for w in wordlist:
        scores.append(sentiment_score_for_word(w,sen))
    return (float(sum(scores)) / len(sen))

def liwc_overall_sentiment_by_sentence(sen_dict):
    sens = sen_dict['sentences']
    return map(liwc_overall_sentiment_of_sen, sens)

def liwc_overall_sentiment_of_speechact(sen_dict):
    sens = sen_dict['sentences']
    if len(sens) == 0:
        return 0.0
    return sum([liwc_overall_sentiment_of_sen(sen) for sen in sens]) / float(len(sens))

def liwc_sentiment_towards_all_entities_in_speechact_no_anaphora(sen_dict):
    """
    produces two dictionaries of sentiment, one for a_obj, one for prev_obj.
    each dictionary is of the form:
    {entity: score, ...}
    these entities and scores do not include those named by anaphora.
    """
    entities_and_refs = windices_of_named_entities_and_references(sen_dict)
    entities_scores = {}
    for entity, refs in entities_and_refs.items():
        scores = []
        for ref in refs:
            sen = sen_dict['sentences'][ref[0]]
            sen_score = liwc_sen_score_towards_index(ref[1:], sen)
            scores.append(sen_score)
        entities_scores[entity] = (sum(scores) / len(scores))
    return entities_scores

def liwc_sent_from_a_to_b_in_dataframe(df, a_name, b_name):
    "df is a pandas dataframe. finds the overall sentiment from 'a_name' directed at 'b_name'"
    sentiment = []
    for index, row in df.iterrows():
        if pd.isnull(row['sentiment']):
            continue
        if difflib.get_close_matches(a_name, [row['speaker']]):
            try:
                mentioned_matches = difflib.get_close_matches(b_name, row['sentiment'].keys())
            except:
                continue
                # print 'no sentiment here'
            if mentioned_matches:
                closest = min(mentioned_matches, key=lambda s: Levenshtein.distance(b_name, s))
                sentiment.append(row['sentiment'][closest])
    if not sentiment:
        return None
    else:
        return sum(sentiment)

def liwc_sentiment_with_anaphora(a_obj, prev_obj, server):
    """
    produces two dictionaries of sentiment, one for a_obj, one for prev_obj.
    each dictionary is of the form:
    {entity: score, ...}
    and entities include those named by anaphora.
    a_obj and prev_obj are both corenlp objects.
    prev_obj should be the speech that comes before a_obj.
    returns a tuple of (a_sentiment, prev_sentiment)
    """
    len_prev = len(prev_obj['sentences'])
    a_text = " ".join([s['text'] for s in a_obj['sentences']])
    prev_text = " ".join([s['text'] for s in prev_obj['sentences']])
    
    combined_obj = get_corenlp_object(prev_text +" "+ a_text, server)
    if not combined_obj:
        return np.nan

    entities_and_refs = windices_of_named_entities_and_references(combined_obj)
    print entities_and_refs
    
    prev_sentiment = defaultdict(float)
    a_sentiment = defaultdict(float)

    for entity, references in entities_and_refs.items():
        #print "entity: ", entity
        for ref in references:
            sen_ref = ref[0]

            if sen_ref < len_prev:
                sentiment = liwc_sen_score_towards_index(ref[1:], prev_obj['sentences'][sen_ref])
                prev_sentiment[entity] += sentiment
            else:
                sentiment = liwc_sen_score_towards_index(ref[1:], combined_obj['sentences'][sen_ref]) #- len_prev])
                a_sentiment[entity] += sentiment

    return (a_sentiment, prev_sentiment)

def liwc_sentiment_towards_only_anaphora(a_obj, prev_obj, server):
    """
    a_obj and prev_obj are both corenlp objects.
    prev_obj should be the speech that comes before a_obj.
    returns a dict of a_obj's sentiment towards any anaphora.
    """
    len_prev = len(prev_obj['sentences'])
    sent = liwc_sentiment_with_anaphora(a_obj, prev_obj, server)

    a_text = " ".join([s['text'] for s in a_obj['sentences']])
    prev_text = " ".join([s['text'] for s in prev_obj['sentences']])
    
    combined_obj = get_corenlp_object(prev_text +" "+ a_text, server)
    if not combined_obj:
        return np.nan

    filtered_sent = tuple(sent)

    # for each entity we computed sentiment for, check if an anaphora actually
    # exists in a_text.
    for name in sent[0].keys():
        corefs = coreferences_for(name, combined_obj)
        if not corefs: # no coreferences, no anaphora
            filtered_sent[0].pop(name)
            continue
        # T/F for each coref pair
        corefs_in_a = [any([ref[1] >= len_prev for ref in pair]) for pair in corefs] 
        if not corefs: # no coreferences, no anaphora
            filtered_sent[0].pop(name)
        if not any(corefs_in_a): # no coreferences to name in a_text
            filtered_sent[0].pop(name)

    return filtered_sent

def liwc_categories_for_sen(sen):
    """
    Produces a dictionary of category scores for the given sentence, of the form
    {category: score, ...}
    """
    category_scores = defaultdict(int)
    for word in sen['words']:
        lemma = word[1]['Lemma']
        categories = liwc.getCategories(lemma)
        if not categories:
            continue
        for category in categories:
            category_scores[category] += 1

    for category, score in category_scores.items():
        category_scores[category] = float(score)/len(sen['words'])
    return category_scores

def liwc_categories_by_sentence(speechact):
    sens = speechact['sentences']
    categories = map(liwc_categories_for_sen, sens)
    return categories

def liwc_categories_for_speechact(speechact):
    """
    Produces a dictionary of category scores for speechact, of the form:
    {category: score, ...}
    """
    category_scores = defaultdict(int)
    sens = speechact['sentences']
    category_dicts = [liwc_categories_for_sen(sen) for sen in sens]
    for d in category_dicts:
        for category, score in d.items():
            category_scores[category] += score
    for category, score in category_scores.items():
        category_scores[category] = float(score)/len(sens)
    return category_scores
