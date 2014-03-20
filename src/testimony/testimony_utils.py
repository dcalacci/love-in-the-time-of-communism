#!/usr/bin/env python
import re
import os
import nameutils
import ner
import Levenshtein
from collections import defaultdict
from preprocessing import cleanFile
from config import transcript_dir


staff_names = ['frank s. tavenner', 'thomas w. beale', 'william a. wheeler', 'raphael i. nixon']

def switch_dict(d):
    newdict = {}
    for key, vals in d.items():
        for val in vals:
            if val in newdict.keys():
                newdict[val] += [key]
            else:
                newdict[val] = [key]
    return newdict

class Transcripts:
    def __init__(self):
        self.names = [f.replace(".txt", "") for f in os.listdir(transcript_dir)]
        self.speechacts = self.__get_all_speech_acts()
        self.tagger = ner.SocketNER(host='localhost', port=8080)
        #self.names = dict((k, self.get_entities(v)) for k, v in self.speechacts.items())

    def has_name(self, name):
        "returns true if there's a fuzzy match on name in the list of names"
        for informer in self.speechacts.keys():
            if nameutils.are_close_tokens(name, informer):
                return True
        return False

    def get_closest_name(self, n1, files=False):
        """
        Returns the speaker that is most similar to n1.
        If there aren't any that are close enough, return [].
        """
        #print "looking at: ", n1
        if files:
            namelist = self.speechacts.keys()
        else:
            namelist = [n.replace("-", " ") for n in self.names]
        maybes = []
        for name in namelist:#self.speechacts.keys():
            try: 
#                print ">>>", name
                if Levenshtein.ratio(unicode(name).lower(), unicode(n1).lower()) > 0.8:
#                    print "close: ", name, " / ", n1
                    maybes.append(name)
            except:
                break #still want to have prev. matches.
        if not maybes:
            return []
        best = max(maybes, key=lambda n: Levenshtein.ratio(unicode(n), unicode(n1)))
 #       print n1, " -> ", best
        return best

    # get speechacts by a particular speaker that mention ANY entities.
    # return a dict of entity -> speechacts that reference that entity.
    # then can use fuzzy matching to find entities.

    def get_speech_acts_by_speaker_and_mention(self, speaker, entity):
        speechacts_with_any_mention = self.get_speech_acts_by_speaker_with_any_mention(speaker)
        speechacts = []
        mentions = []

        for mentioned, speech in speechacts_with_any_mention.items():
            for mention in mentioned:
                if nameutils.are_close_tokens(mention, entity, 0.4):
                    speechacts.extend(speech)
                    mentions.append(mention)
        return (list(set(speechacts)), list(set(mentions))) # no duplicates
    
    def get_speech_acts_by_speaker_with_any_mention(self, speaker):
        "gets all speech acts by speaker that mention an entity"
        mention_speechacts = {}
        similar_ids = {}
        speechacts = self.get_speechacts_by_speaker(speaker)
        for speechact in speechacts:
            ents = self.tagger.get_entities(speechact)
            mentioned_people = []
            if 'PERSON' in ents.keys():
                mentioned_people = ents['PERSON']
            for person in mentioned_people:
                if mention_speechacts.has_key(person):
                    mention_speechacts[person] += [speechact]
                else:
                    mention_speechacts[person] = [speechact]
        mention_speechacts = dict((k, v) for k, v in mention_speechacts.items() if len(k) > 3)
        similar_names = self.chunk_names(mention_speechacts.keys())
        #print similar_names

        for i in range(len(similar_names)):
            similar_ids[i] = similar_names[i]

        for name in mention_speechacts.keys():
            for similars in similar_names:
                if name in similars:
                    mention_speechacts[tuple(similars)] = mention_speechacts[name]
        mention_speechacts = dict((k,v) for k, v in mention_speechacts.items() if type(k) == tuple)
        
        return mention_speechacts

    def chunk_names(self, names):
        "produces a list of lists of similar names, no repeats (means it's rough)"
        similar_names = []
        blacklist = []

        def find_similar(name, names):
            similar = [name]
            for n2 in names:
                if names.index(n2) in blacklist or n2 == name:
                    continue
                if nameutils.are_close_tokens(name, n2):
                    similar += [n2]
                    blacklist.append(names.index(n2))
            return similar

        for i in range(len(names)):
            if i in blacklist: 
                continue
            similar = find_similar(names[i], names)
            #print ">>", names[i]
            blacklist.append(i)
            #print "blacklist: ", blacklist
            similar_names += [similar]
        return similar_names


    def get_speech_acts_by_speaker_and_phrase(self, speaker, phrase):
        """
        speech acts, in general, that are spoken by speaker that mention
        the given phrase. Can be used to find speechacts with mentions
        of particular entities, too.
        """
        print "speaker: ", speaker, "; phrase: ", phrase
        speechacts_with_mention = []
        speechacts = self.get_speechacts_by_speaker(speaker)
        print "any speechacts? : ", len(speechacts)
        for speechact in speechacts:
            last = phrase.split()[-1]
            if nameutils.fuzzy_substring(last.lower(), speechact.lower()) < 3: # seems to be the magic number
                speechacts_with_mention.append(speechact)
        return speechacts_with_mention

    def get_speechacts_by_speaker(self, speaker):
        "uses fuzzy matching"
        name = self.get_closest_name(speaker)
        print speaker," ->> ", name
        if not name:
            return []
        else:
            return self.speechacts[name]

        # best = min(maybes, key=lambda n: min([nameutils.fuzzy_substring(name, speaker), 
        #                                       nameutils.fuzzy_substring(speaker, name)]))
        #best = min(maybes, key=lambda n: min(Levenshtein.ratio(name, speaker)))
        #if not Levenshtein.ratio(speaker, best) < 0.6:
        #if not nameutils.are_close_tokens(speaker, best): return []
        # print speaker, " -> ", best
        # return self.speechacts[best]

    def __get_all_speech_acts(self):
        """
        produces a dict of name -> list of speech acts for every speaker
        in all testimonies
        """
        def merge(dicts):
            "merges every dict in dicts. assumes that vals are lists"
            print "Merging..."
            result = defaultdict(lambda: [])
            for d in dicts:
                for (k,v) in d.items():
                    result[k] += v
            return result
                            
        dicts = []
        print "Getting speech acts..."
        for name in self.names:
            dicts.append(self.get_speech_acts_from_testimony(name))

        # remove bum keys, maybe later find appropriate
        # good keys to merge with.
        speechacts =  merge(dicts)
        for key in speechacts.keys():
            if len(key) < 3:
                del speechacts[key]

        # the distribution shouldn't be needed at the top level
#        dist = nameutils.name_distribution_from_dict(speechacts)

        # for (k, v) in speechacts.items():
        #     likely_name = nameutils.find_likely_name(k, dist)
        #     if not dist[likely_name] < .00001:
        #         print k, "->", likely_name
        #         speechacts[likely_name] += v
        #     if not likely_name == k:
        #         del speechacts[k]

        return speechacts

    def get_entities(self, speechacts):
        print "Getting entities..."
        def get_entities_from_string(text):
#            print text
            orig_ents = self.tagger.get_entities(text)

            # just a simple list of all the entities
            entities = [v[0] for k, v in orig_ents.items()]
            return entities

        entities = []
        for speechact in speechacts:
            entities += get_entities_from_string(speechact)
        return entities

    def get_speech_acts_from_testimony(self, name):
        "gets all the speech acts from the given actor's testimony."
        return self._get_speech_acts_from_file(os.path.join(transcript_dir, 
                                                            name+".txt"))

    def _get_full_name_from_last(self, last):
        # problem here is duplicate last names
        # or just simply names that are similar.
        for name in self.names:
            if last.lower() in name:
                return name.replace("-", " ").replace(".txt", "")
        return last

    def _get_speech_acts_from_file(self, filepath):
        "returns a hash of name -> list of speech acts for a particular file."
        cleanFile(filepath)
        
        name = os.path.basename(filepath).replace("-", " ").replace(".txt", "")
        str = ""
        with open(filepath, 'r+') as f:
            import mmap
            str = mmap.mmap(f.fileno(), 0)
        f.close()

        regex = re.compile("^(?:Mrs|Miss|Mr)(?:\.?)(?:\s?)(\w*?)[\.\s](.*?)\n",
                           re.MULTILINE)
        matches = regex.findall(str)

        # name distribution to guess likely names from mispellings
        dist = nameutils.name_distribution_from_matches(matches)
        # all last names
        speechacts = {}
        for match in matches:
            likely_name = nameutils.find_likely_name(match[0].lower(), dist).lower()
            if not dist[likely_name] < .01:
                if likely_name.lower() in name:
                    # print match[0].lower(), "->", name
                    realname = name
                else:
                    realname = self._get_full_name_from_last(likely_name)

                # if the likely name doesn't have a low occurrence rate:

                if speechacts.has_key(realname):
                    speechacts[realname].append(match[1])
                else:
                    speechacts[realname] = [match[1]]
        return speechacts

    def get_speech_acts_from_file_as_list(self, filepath):
        """
        list (in order) of tuples of:
        (speaker, speechact)
        """
