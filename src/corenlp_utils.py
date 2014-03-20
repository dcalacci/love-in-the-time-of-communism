#!/usr/bin/env python
import numpy as np
import jsonrpclib
from simplejson import loads

def get_named_people_from_sen(sen):
    """
    returns a list of annotated words that correspond to named entities in sen.
    sen must be an annotated sentence dict.

    each element of the returned list is a list of annotated words. Each list 
    corresponds to a single entity.

    result looks like:
        [[[u'Dan',
           {u'CharacterOffsetBegin': u'0',
            u'CharacterOffsetEnd': u'3',
            u'Lemma': u'Dan',
            u'NamedEntityTag': u'PERSON',
            u'PartOfSpeech': u'NNP'}],
          [u'Calacci',
           {u'CharacterOffsetBegin': u'4',
            u'CharacterOffsetEnd': u'11',
            u'Lemma': u'Calacci',
            u'NamedEntityTag': u'PERSON',
            u'PartOfSpeech': u'NNP'}]],
         [[u'Shane',
           {u'CharacterOffsetBegin': u'18',
            u'CharacterOffsetEnd': u'23',
            u'Lemma': u'Shane',
            u'NamedEntityTag': u'PERSON',
            u'PartOfSpeech': u'NNP'}],
          [u'Boissiere',
           {u'CharacterOffsetBegin': u'24',
            u'CharacterOffsetEnd': u'33',
            u'Lemma': u'Boissiere',
            u'NamedEntityTag': u'PERSON',
            u'PartOfSpeech': u'NNP'}]]]
    """
    wordlist = sen['words']
    entities = []

    named = []
    for index, word in enumerate(wordlist):
        if word[1]['NamedEntityTag'] == 'PERSON':
            named.append(word)
            
        try:
            next = wordlist[index+1]
        except:
            named = []
            break

        if next[1]['NamedEntityTag'] != 'PERSON':
            if named:
                entities.append(named)
            named = []

    return entities

def get_named_people_by_sentence(sen_dict):
    """
    produces a list of named people for each sentence in the annotated 
    sentence dict.

    each element of the list is a list of annotated words that correspond to
    named entities, as returned by 'get_named_people_from_sen'.

    if there are no named people in a sentence, that sentences' entry will be 
    an empty list.
    """
    named = [get_named_people_from_sen(sen) for sen in sen_dict['sentences']]
    return named

def get_named_people(sen_dict):
    """
    produces a list of all named people in the annotated sentence dict. 

    the result is a list of annotated words that correspond to named entities.
    """
    named = []
    for sen in sen_dict['sentences']:
        named.extend(get_named_people_from_sen(sen))
    return named

def annotated_words_from_ref(ref_info, sen_dict):
    """
    retrieves the annotated word objects from sen_dict that 
    correspond to the coreference information in ref_info.
    
    the coreference info must be in the same form that is returned by
    stanford-corenlp; something that looks like:

    [u'Dan Calacci', 0, 1, 0, 2]
    """
    sentence_index = ref_info[1]
    start_word_index = ref_info[3]
    end_word_index = ref_info[4]

    return sen_dict['sentences'][sentence_index]['words'][start_word_index:end_word_index]
    #for word in sen_dict['sentences'][sentence_index]['words']:
        
def coreferences_for(string, sen_dict):
    """
    returns the list of references to the given string that are in sen_dict.
    if the given string doesn't have any coreferences, it will return None.
    otherwise, it'll return a list, where each element is a coreference pair:

    [[[u'He', 1, 0, 0, 1], [u'Dan Calacci', 0, 1, 0, 2]],
    [[u'He', 2, 0, 0, 1], [u'Dan Calacci', 0, 1, 0, 2]]]

    where He -> Dan Calacci, and
          He -> Dan Calacci
    """
    if not sen_dict.has_key('coref'):
        return None
    for coref in sen_dict['coref']:
        for ref_pair in coref:
            for ref in ref_pair:
                if string in ref:
                    return coref

def cindices_of_references(string, sen_dict):
    """
    returns the character indices of all references to the given string.
    this includes the character indices for coreferences as well as actual
    references.
    returns a list of integer tuples that correspond to the indices:

    [(0, 11), (64, 66), (35, 37)]
    """
    indices = []
    coreferences = coreferences_for(string, sen_dict)
    for ref_pair in coreferences:
        for ref in ref_pair:
            annotated_refs = annotated_words_from_ref(ref, sen_dict)
            start_index = annotated_refs[0][1]['CharacterOffsetBegin']
            end_index = annotated_refs[-1][1]['CharacterOffsetEnd']
            interval = (int(start_index), int(end_index))
            indices.append(interval) 
    return list(set(indices))


def windices_of_name(string, sen_dict):
    """
    produces the list of word/sentence indices for the given string.
    This only works for exact matches of string in sen_dict.
    produces a list-wrapped tuple of [(sen_index, start_index, end_index)].

    if it's not found, it returns [(0, 0, 0)]
    """
    sentence_index   = 0
    start_word_index = 0
    end_word_index   = 0

    for sindex, sentence in enumerate(sen_dict['sentences']):
        for windex, word in enumerate(sentence['words']):
            if word[0] == string.split()[0]:
                matched = True
                for i, s in enumerate(string.split()[1:]):
                    if sentence['words'][windex+i+1][0] != s:
                        matched = False
                if matched:
                    start_word_index = windex
                    sentence_index = sindex
                    end_word_index = windex + len(string.split())
    return [(sentence_index, start_word_index, end_word_index)]
    

def windices_of_references(string, sen_dict):
    """
    returns a list of word/sentence indices for all coreferences to
    the given string in sen_dict.

    returns [(0,0,0)] if there were no coreferences found.
    """
    indices = []
    coreferences = coreferences_for(string, sen_dict)
    if not coreferences:
        return [(0, 0, 0)]
    for ref_pair in coreferences:
        for ref in ref_pair:
            sen_id = ref[1]
            start_index = ref[3]
            end_index = ref[4]
            interval = (int(sen_id), int(start_index), int(end_index))
            indices.append(interval) 
    return list(set(indices))
        
def windices_of_named_entities_and_references(sen_dict):
    """
    returns the word/sentence indices for each reference to every
    named entity in sen_dict.

    the result is a dictionary where the keys are the strings that were 
    recognized as named entities, and the values are a list of word/sentence
    index tuples:

    {u'Abarca': [(3, 0, 2), (3, 4, 5), (3, 3, 5)],
     u'Dan Calacci': [(0, 0, 2), (2, 0, 1), (1, 0, 1)],
     u'Shane Boissiere': [(0, 3, 5)]}
    """
    named_entities = get_named_people(sen_dict)
    entity_and_references = {}
    for name in named_entities:
        name_as_string = ""
        for index, token in enumerate(name):
            if index != 0:
                name_as_string += (" " + token[0])
            else:
                name_as_string += token[0]

        if coreferences_for(name_as_string, sen_dict):
            entity_and_references[name_as_string] = windices_of_references(name_as_string, sen_dict)
        else:
            entity_and_references[name_as_string] = windices_of_name(name_as_string, sen_dict)
    return entity_and_references

def get_corenlp_object(speech, server):
    if len(speech.split()) > 100:
        return None
    try:
        return loads(server.parse(speech))
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        return None

def mention_list_by_sentence_no_anaphora(obj):
    """
    returns a list of lists of mentions, where the nth index of the list
    corresponds to the nth sentence in obj:
    [['Andrea', 'Dan'], ['Shane'], []]

    this does not include mentions via anaphora.
    """
    indices_and_mentions =  windices_of_named_entities_and_references(obj)
    mentions_by_sentence = range(len(obj['sentences']))
    mentions_by_sentence = map(lambda i: [], mentions_by_sentence)
    for name, indices in indices_and_mentions.items():
        for index in indices:
            sen_index = index[0]
            mentions_by_sentence[sen_index].append(name)
            mentions_by_sentence[sen_index] = list(set(mentions_by_sentence[sen_index]))
    return mentions_by_sentence

def mention_list_by_sentence_with_anaphora(a_obj, prev_obj, server):
    """
    returns a list of lists of mentions, where the nth index of the list
    corresponds to the nth sentence in obj:
    [['Andrea', 'Dan'], ['Shane'], []]

    this includes mentions via anaphora.

    a_obj is the speechact to retrieve mentions from. prev_obj is the previous
    speechact.
    """
    len_prev = len(prev_obj['sentences'])

    a_text = " ".join([s['text'] for s in a_obj['sentences']])
    prev_text = " ".join([s['text'] for s in prev_obj['sentences']])
    
    combined_obj = get_corenlp_object(prev_text +" "+ a_text, server)
    if not combined_obj:
        return np.nan

    entities_and_refs = windices_of_named_entities_and_references(combined_obj)

    mentions_by_sentence = range(len(a_obj['sentences']))
    mentions_by_sentence = map(lambda i: [], mentions_by_sentence)

    for entity, references in entities_and_refs.items():
        for ref in references:
            sen_ref = ref[0]
            if sen_ref < len_prev: # previous speechat.
                continue
            else:
                mentions_by_sentence[sen_ref - len_prev].append(entity)
    return mentions_by_sentence

def mention_list_for_speechact_no_anaphora(obj):
    return windices_of_named_entities_and_references(obj).keys()
