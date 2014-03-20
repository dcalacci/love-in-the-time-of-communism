#/usr/bin/env python
from lexicons.config import liwc_dir, pitt_dir, liu_dir
from stemming.porter2 import stem
import os

liwcfile = os.path.join(liwc_dir, "features.txt")
pittfile = os.path.join(pitt_dir, "data.txt")
pos_liufile = os.path.join(liu_dir, "positivewords.txt")
neg_liufile = os.path.join(liu_dir, "negativewords.txt")


class Lexicons:
    def __init__(self):
        self.liuDict = LiuDict()
        self.liwcDict = LiwcDict()
        self.pittDict = PittDict()

    def exists(self, word):
        "returns true if the given word is measured in any of the lexicons"
        return self.liuDict.exists(word) or self.liwcDict.exists(word) or self.pittDict.exists(word)

    def getCategories(self, word):
        "returns the list of liwc categories the given word is in"
        for liwcWord in self.wordmap.keys():
            if self.__matchesLiwcWord(liwcWord, word):
                return self.wordmap[liwcWord]
        return None

    def isPosCat(self, cat):
        "returns true if the category is in self.pos"
        return cat in self.pos

    def isNegCat(self, cat):
        "returns true if the category is in self.neg"
        return cat in self.neg

    def isPosWord(self, word):
        "returns true if the word is deemed to be positive "
        categories = self.getCategories(word)
        if categories:
            return any(map(self.isPosCat, categories))
        else:
            return []

    def isNegWord(self, word):
        "returns true if the word deemed to be negative"
        categories = self.getCategories(word)
        if categories:
            return any(map(self.isNegCat, categories))
        else:
            return []

    def positiveWords(self):
        "returns a list of positive-associated words from liwc"
        poswords = []
        for word, categories in self.wordmap:
            if any(p in categories for p in self.pos):
                poswords.append(word)
        return poswords

    def negativeWords(self):
        "returns a list of negative-associated words from liwc"
        negwords = []
        for word, categories in self.wordmap:
            if any(n in categories for n in self.neg):
                negwords.append(word)
        return negwords

    def getOppositeCategory(self, category):
        "returns the 'negated' or 'opposite' category of the given category"
        return self.liwcDict.getOppositeCategory(category)

        
    def isNegation(self, word):
        "returns true if the given word is a negation word"
        return self.liwcDict.isNegation(word)


class LiwcDict:
    def __init__(self, filepath=liwcfile):
        self.filepath = filepath
        self.wordmap = {}
        self.__parseFeatureFile()
        # Friends, Job included for liwc. May indicate collaboration.
        self.pos = ["Posemo", "Friends", "Job"]
        self.neg = ["Negemo", "Anx", "Anger", "Sad"]
        
    def __parseFeatureFile(self):
        "parses the feature file, populating the wordmap"
        with open(self.filepath) as f:
            for line in f.readlines():
                line = line.split(", ")
                category, words = line[0], line[1:]
                for word in words:
                    if self.wordmap.has_key(word):
                        self.wordmap[word].append(category)
                    else:
                        self.wordmap[word] = [category]

    def __matchesLiwcWord(self, liwc, word):
        "returns true if the given word matches the given liwc word"
        if liwc[-1] == "*":
            return word.startswith(liwc[:-1])
        else:
            return word == liwc

    
    def exists(self, word):
        "returns true if the given word is measured in liwc"
        for liwcWord in self.wordmap.keys():
            if self.__matchesLiwcWord(liwcWord, word):
                return True
        return False
        
    def getWordsInCategory(self, category):
        "returns the list of words that correspond to the given category"
        words = []
        for liwcWord, cat in self.wordmap.items():
            if cat == category:
                words.append(liwcWord)
        return set(words)

    def getCategories(self, word):
        "returns the list of liwc categories the given word is in"
        for liwcWord in self.wordmap.keys():
            if self.__matchesLiwcWord(liwcWord, word):
                return self.wordmap[liwcWord]
        return None

    def isPosCat(self, cat):
        "returns true if the category is in self.pos"
        return cat in self.pos

    def isNegCat(self, cat):
        "returns true if the category is in self.neg"
        return cat in self.neg

    def isPosWord(self, word):
        "returns true if the word is deemed to be positive "
        categories = self.getCategories(word)
        if categories:
            return any(map(self.isPosCat, categories))
        else:
            return []

    def isNegWord(self, word):
        "returns true if the word deemed to be negative"
        categories = self.getCategories(word)
        if categories:
            return any(map(self.isNegCat, categories))
        else:
            return []

    def positiveWords(self):
        "returns a list of positive-associated words from liwc"
        poswords = []
        for word, categories in self.wordmap:
            if any(p in categories for p in self.pos):
                poswords.append(word)
        return poswords

    def negativeWords(self):
        "returns a list of negative-associated words from liwc"
        negwords = []
        for word, categories in self.wordmap:
            if any(n in categories for n in self.neg):
                negwords.append(word)
        return negwords

    def getOppositeCategory(self, category):
        "returns the 'negated' or 'opposite' category of the given category"
        opps = {}
        opps["Posemo"] = "Negemo"
        opps["Negemo"] = "Posemo"
        
        if opps.has_key(category):
            return opps[category]
        else:
            return None
        
    def isNegation(self, word):
        "returns true if the given word is a negation word"
        cats = self.getCategories(word)
        if cats:
            return 'Negate' in cats
        return None


# there's some duplicated code between PittDict and LiuDict right now,
# but that's because not all of PittDict's functionality is being used
# right now.
class PittDict:
    def __init__(self, filepath=pittfile):
        self.filepath = filepath
        self.pos = []
        self.neg = []
        self.data = {}
        self.__parseDataFile()

    # this doesn't work, because the mpqa lexicon 
    # separates by part of speech, too, and that screws up
    # the dictionary.
    # temporary fix: a word is either positive or negative,
    # regardless of PoS
    def __parseDataFile(self):
        "parses the data file!"
        self.data = {}
        with open(self.filepath) as datafile:
            for line in datafile.readlines():
                line = line.split()
                d = dict((item.split("=")[0], item.split("=")[1]) for item in line)
                word = d['word1']
                d.pop('word1', None)

                if d['priorpolarity'] == "positive":
                    self.pos.append(word)
                elif d['priorpolarity'] == "negative":
                    self.neg.append(word)

#                self.data[word] = d
        datafile.close()

    def find_word(self, word):
        "returns a tuple of (word, info) if word matches a word in the list"
        s = stem(word)
        words = self.data.keys()
        
        # if we can get a full match
        full_matches = [w for w in words if word == w]
        if full_matches:
            return (full_matches[0], self.data[full_matches[0]])

        # otherwise, get words that match the stem:
        stem_matches = [w for w in words if word.startswith(s)]
        if stem_matches:
            return (stem_matches[0], self.data[stem_matches[0]])
        
        # if there's no match at all, return None
        return None

    def exists(self, word):
        return self.isPosWord(word) or self.isNegWord(word)
        
    def isPosWord(self, word):
        for w in self.pos:
            if w.startswith(stem(word)):
                return True
        return False
        # res = self.find_word(word)
        # if res:
        #     return res["priorpolarity"] == "positive"
        # return False

    def isNegWord(self, word):
        for w in self.neg:
            if w.startswith(stem(word)):
                return True
        return False
        # res = self.find_word(word)
        # if res:
        #     return res["priorpolarity"] == "negative"
        # return False

class LiuDict:
    def __init__(self, posFile=pos_liufile, negFile=neg_liufile):
        self.posFile = posFile
        self.negFile = negFile
        self.pos = []
        self.neg = []
        self.__parseDataFiles()

    def __parseDataFiles(self):
        with open(self.posFile) as f:
            self.pos = f.readlines()
        f.close()
        with open(self.negFile) as f:
            self.neg = f.readlines()
        f.close()

    def exists(self, word):

        return self.isPosWord(word) or self.isNegWord(word)

    def isPosWord(self, word):
        s = stem(word)
        for word in self.pos:
            if word.startswith(s):
                return True
        return False

    def isNegWord(self, word):
        s = stem(word)
        for word in self.neg:
            if word.startswith(s):
                return True
        return False
