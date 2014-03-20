import difflib
import testimony.nameutils as nameutils

def has_been_chunked_approximate(s, chunklist, threshold=3):
    for chunk in chunklist:
        approx_chunk = filter(lambda sliver: nameutils.are_close_tokens(s, sliver, threshold), chunk)
        if approx_chunk: return True
    return False

def has_been_chunked(s, chunklist):
    for chunk in chunklist:
        if s in chunk: return True
    return False

def chunk_list(l):
    chunklist = []
    for s in l:
        if has_been_chunked(s, chunklist):
            continue
        close_matches = difflib.get_close_matches(s, l, 200, 0.85)
        chunklist.append(close_matches)

    return chunklist
