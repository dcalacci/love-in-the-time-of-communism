#!/usr/bin/env python
import re
import ner
import nameutils

#d2 = dict((k, map(lambda n: " ".join(n.split()), v)) for (k,v) in d2.items())

def clean_whitespace(name):
    return " ".join(name.split())

def nametrans(name):
    # strip titles, crudely.
    titles = ["Mr. ", "mr ", "mr. ", "Mr ", "Mrs. ", "mrs ", "Mrs ", "Dr. ", "Dr "]
    for title in titles:
        newname = name.replace(title, "")
        if not newname == name:
            print name, " -> ", newname
            name = newname
            break

    curname = name.split(",")
    if len(curname) < 2:
        curname = name.split(".")
#    print curname
    try:
        last, first = curname[0], curname[1]
    except:
        return ""
    current_name = first + " " + last
    current_name = clean_whitespace(current_name)
    return current_name

def who_named_whom(filepath):
    "give it the filepath for the annual reports."
    namedict = {}
    named_regex = re.compile("(^(\s)?[A-Z]\w+[,|\.]\s*[A-Z]\w+(?:\s[A-Z])?(?:\.)?([\s+]\w+)?)(\s*\((.*)\))?",
                             re.MULTILINE)
    not_all_caps_regex = re.compile("([a-z])")
    testimony_identifying_regex = re.compile("Testimony identifying")
    tagger = ner.SocketNER(host='localhost', port=8080)

    f = open(filepath, "r")
    lines = f.readlines()

    for i in range(len(lines)):
        current_line = lines[i]
        current_name = ""
        matches = named_regex.findall(current_line)

        # if we don't have a named line, we don't care.
        if not matches:
            continue
        orig_name = matches[0][0]

        current_name = nametrans(orig_name) # normal First Last format
        # if it returns nothing, it's a bad name (no comma)
        if not current_name:
            continue

        # we also don't care if the transformed name isn't two tokens
        if not len(current_name) > 1:
            continue

        # # sometimes the regex confused locations for people
        # # the name is separated by a comma/period. NER works well for names
        # # in normal order (not with commas/periods)
        # name = current_name.split(",")
        # if len(name) < 2:
        #     name = current_name.split(".")

        # last, first = name[0], name[1]
        # current_name = first + " " + last
        # entities = tagger.get_entities(current_name)
        # if entities.has_key('LOCATION'):
        #     continue

        current_line = current_line.replace(orig_name, "")

        # remove anything in parens (...) on same line as name.
        # they are usually aliases.
        reg = re.compile("\(.*\)")
        current_line = re.sub(reg, "", current_line)
        
        # get all lines from current_line until the next named name.
        # could skip i to be where j is, but we can save that for later.
        named_lines = ""
        # go from current_line forward in the file
        for j in range(i+1, len(lines)):
            if named_regex.findall(lines[j]):
                break
            if not not_all_caps_regex.findall(lines[j]):
                break
            if testimony_identifying_regex.findall(lines[j]):
                break
            named_lines += lines[j]

        named_lines = current_line + named_lines # add the rest of the first line
        
        named_lines = named_lines.replace("\n", "")
#        print "named lines for ", current_name, "are:\n", named_lines

        # dealing with NER server errors
        got_result = None
        while got_result == None:
            try:
                entities = tagger.get_entities(named_lines)
                got_result = True
            except:
                pass
                
        # get the names!
        if not entities.has_key('PERSON'):
            continue
        names = entities['PERSON']
        names = map(clean_whitespace, names)

        # all real names are at least two tokens long.
        names = filter(lambda n: len(n.split()) > 1, names)

        # if this key doesn't have any real names associated with it, skip.
        if not names:
            continue
        print "named: ", current_name

        if namedict.has_key(current_name):
            namedict[current_name].append(names)
        else:
            namedict[current_name] = names
    return namedict

def fix_graph(graph, distribution):
    """
    Fixes mispelled names in the graph using name chunking and the
    name occurrence distribution.
    """
    distribution = nameutils.name_distribution_with_tokens(graph)
    new_graph = {}
    for name in graph.keys():
        print(name)
        mln = nameutils.most_likely_name(name, distribution)

        # I treat `informers` as a set because from looking at the
        # data, it seems that multiple occurrences is usually an
        # error.
        informers = set()
        for informer in graph[name]:
            if not isinstance(informer, basestring):
                continue
            informer_mln = nameutils.most_likely_name(informer, distribution)
            informers.add(informer_mln)

        if new_graph.has_key(mln):
            new_graph[mln].update(informers)
        else:
            new_graph[mln] = informers

    return new_graph
