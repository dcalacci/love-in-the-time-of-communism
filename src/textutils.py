#!/usr/bin/env python

import mmap
import os
import re
import testimony.nameutils as nameutils
from testimony.preprocessing import cleanFile


transcript_dir = os.path.join("testimony/text/hearings")

interviewee_names = [f.replace(".txt", "") for f in os.listdir(transcript_dir)]
interviewee_names = map(lambda s: s.replace("-", " "), interviewee_names)


def get_interviewee_name_from_partial(partial):
    "tries to resolve a partial name to a full interviewee name."
    for name in interviewee_names:
        if partial.lower() in name:
            return name
    return partial

def get_speech_acts_from_file_as_list(filepath):
    """
    tuple of ([speaker, speaker...], [speechact, speechact...])

    for use in constructing a dataframe.
    """
    interviewee_name = os.path.basename(filepath).replace("-", " ").replace(".txt", "")

    # load transcript into memory
    file_as_string = ""

    with open(filepath, 'r+') as f:
        file_as_string = mmap.mmap(f.fileno(), 0)
    f.close()

    regex = re.compile("^(?:Mrs|Miss|Mr)(?:\.?)(?:\s?)(\w*?)[\.\s](.*?)\n",
                           re.MULTILINE)
    speaker_matches = regex.findall(file_as_string)

    # guess likely names from misspellngs using a frequency distribution
    dist = nameutils.name_distribution_from_matches(speaker_matches)

    # constructing the dataframe
    speakers = []
    speechacts = []
    
    for match in speaker_matches:
        speaker_name = match[0]
        speechact = match[1]
        likely_name = nameutils.find_likely_name(speaker_name.lower(), dist).lower()

        if not dist[likely_name] < 0.02: # don't use names that rarely appear.
            if likely_name.lower() in interviewee_name:
                realname = interviewee_name
            else:
                realname = get_interviewee_name_from_partial(likely_name)

            # realname is either the speaker name from the transcript, or is matched
            # with a name from the transcript files.
            speakers.append(realname)
            speechacts.append(speechact) # the speechact

    return (speakers, speechacts)
