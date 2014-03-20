#!usr/bin/env python
import math, nltk.data, os
from nltk.tokenize.punkt import PunktWordTokenizer
from testimonyUtils import get_speech_acts



def get_sens_from_speechact(speechact):
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    return tokenizer.tokenize(speechact)

def get_tokens_from_speechact(speechact):
    return PunktWordTokenizer().tokenize(speechact)

def are_close(a, b):
    import Levenshtein
    return Levenshtein.ratio(a, b) > 0.6


def tf(word, doc):
    """
    augmented frequency tf.
    doc must be an iterable list of words.
    """
    def freq(w, d):
        count = 0
        for word in doc:
            if are_close(w, word):
                count+=1
        return count

    max_freq = max(map(lambda w: freq(w, doc), doc))

    return 0.5 + ((0.5 + freq(word, doc)) / max_freq)


def idf(word, docs):
    "each doc in docs must be an iterable list of words"
    def occurs(word, doc):
        for w in doc:
            if are_close(word, w):
                return True
        return False

    num_occurrences = map(lambda d: occurs(word, d), docs).count(True)
    return math.log(len(docs) / (1 + num_occurrences))

def tf_idf(word, doc, docs):
    return tf(word, doc) * idf(word, docs)

def tf_idf_speechacts(filepath):
    path = os.path.join(os.getcwd(), filepath)

    for f in os.listdir(filepath):
        f = os.path.join(path, f)
        speechacts = get_speech_acts(f)
        # s is a list of tuples: (name, speechacts) where speechacts
        # is a string, and each speech act is separated by a newline
        s = [(name, "\n".join(speech)) for name, speech in speechacts.items()]
        for t in s:
            words = get_tokens_from_speechact(t[1])
            name = t[0]
            
            
    # split all speechacts into words
    # go through each word, compute tf-idf score
    # go through top words, see if they mean anything in liwc.


    # maybe develop utilities
