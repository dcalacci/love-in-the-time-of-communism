# love in the time of communism

This is code I wrote to analyze the transcripts from the
[HUAC](http://en.wikipedia.org/wiki/House_Un-American_Activities_Committee)
hollywood blacklist hearings.

[resulting paper here](http://dcalacci.net/more/papers/namingNamesCamReady.pdf)

I wish I could have used the initial github repository (100+ commits)
to keep up my activity street cred, but it was a total mess. (not that
this repo is much better)

It contains code that does the following:


## data cleaning of the original hearing transcripts

This includes OCRing the original transcripts, splitting the
testimonies into speech acts, and attributing speech acts to the
correct authors.

There's a bunch of logic related to fuzzy substring matching, to
account for poor OCR of the data, and to disambiguate names.

There's also a good deal of code that deals with anaphora resolution -
disambiguating pronoun references in the hearings.

And code to do named entity recognition with the stanford NER
processor.

The end result is a pandas dataframe with cleaned tokens attributed to
each author.

## sentiment analysis

Lexical sentiment analysis of the hearings, accounting for negation
and sentence structure. Produces a nice feature vector for each speech
act across various psychological categories outlined in the LIWC.

Needs the LIWC and a copy of stanford's corenlp stuff running on your
local machine. (maybe I'll provide better documentation for this in
the future).

## network analysis

Creates graphs that represent the naming and mentioning structure of
the hearings. Some code to do basic network analyses on the graphs.
