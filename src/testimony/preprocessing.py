#!/usr/bin/env python
import re, os

def cleanFile(filepath):
    "removes unwanted text from the given file"
    def regex_replace(filepath, regexes):
        """
        regexes is a list of (regex, replace)
        regex_replace replaces all the regexes with their 
        respective replace strings
        """
        import mmap
        str = ""
        with open(filepath, 'r+b') as f:

            data = mmap.mmap(f.fileno(), 0)
            for regex, replace in regexes:
                data = re.sub(regex, replace, data)
            str = data
        f.close()
        os.remove(filepath)
        with open(filepath, 'w') as f:
            f.write(str)
        f.close()

    r = []
    r.append(('COMMUNISM IN MOTION-PICTURE INDUSTRY', ''))
    r.append(('COMMUNISM IN MOTION-PICTURE', ''))
    r.append(('\n+(?!Mr|Miss\.?)', ' '))
    regex_replace(filepath, r)

def splitFileByTestimony(filepath):
    """
    Splits the file into parts based on who is giving the testimony.
    Produces a directory that mirrors the given file's name that contains
    files whose names correspond to individual's names
    """
    cleanFile(filepath)

    def findPersonDelimiters(filepath):
        """
        Finds the line number where an individual's testimony begins. 
        Returns a hash of the form 'name' => 'line number'
        """
        regex = re.compile("TESTIMONY OF (.+?)[,\n]")
        f=open(os.path.abspath(filepath))
        persons = {}
        for i, line in enumerate(f.readlines()):
            r = regex.findall(line)
            if r: # if we found anything3
                # if the name is already there and this line number is after
                # the one we found previously, we shouldn't change the hash.
                name = r[0].replace(' ', '-').lower()
                if not persons.has_key(name) or not i+1 > persons[name]:
                    persons[name] = i+1# make the hash: name -> line number
        f.close()
        return persons

    def findPageRanges(filepath):
        """
        returns a list of tuples of the form (name, start, end) where name is the
        name of the person being interviewed, start is the line number at the
        start of that persons' transcript, and end is the end of the interview.
        """
        persons = sorted(findPersonDelimiters(filepath).items(), key=lambda x: x[1])
        # list of tuples of the form (name, start, end). if it ends at EOF, 
        # end is -1. Sorted by beginning line number.
        sections = []
        for index, person in enumerate(persons): 
            t = (person[0], person[1])
            if index+1 == len(persons):
                t = t + ("-1",)
            else:
                t = t + (persons[index+1][1],)
            sections.append(t)
        return sections

    def makeSubFile(origFile, start, end, name):
        """
        Copies the lines between 'start' and 'end' in origFile to a new file
        with the suffix 'name' into a new file in a subdirectory with the same
        name as origFile. The name of the new file is 'name', with the same
        extension as the original file.
        """
        path, filename = os.path.split(origFile)
        basename, ext = os.path.splitext(filename)
        # file is stored in directory {original-path}/{basename}
        newPath = os.path.join(path, basename)
        if not os.path.exists(newPath):
            os.makedirs(newPath)
        outfile = open(os.path.join(newPath, 
                                    '{}{}'.format(name, ext)), 'a')
        with open(origFile, 'r') as f:
            for i, line in enumerate(f):
                if i == end:
                    outfile.close()
                    break;
                if i > start:
                    outfile.write(line)

    def separateTranscriptBySpeaker(filepath, persons):
        """
        Splits the transcript into separate files based on the tuple given - 
        the tuple is of the same form that findPageRanges returns. Each sub-file
        has a suffix that corresponds to the speaker ('person') in the tuple.
        """
        
        def get_file_name(person, persons):
            "gets the file name for this person. handles extension variants."
            names = []
            for p in persons:
                if p[0] in person[0].lower():
                    names.append(p[0])
            # shortest name variant in the list
            return min(names, key=len)
            
                
        for person in persons:
            name = get_file_name(person, persons)
            print "Adding testmony to:", name.strip()+".txt"
            makeSubFile(filepath, person[1], person[2], name)
            
    persons = findPageRanges(filepath)
    separateTranscriptBySpeaker(filepath, persons)
