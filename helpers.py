from collections import Counter


import sys
from time import time

from operator import itemgetter
testuser = {u'first_name': u'Matthew', u'last_name': u'Clemens', u'middle_name': u'Donavan', u'name': u'Matthew Donavan Clemens', u'locale': u'en_US', u'gender': u'male', u'link': u'http://www.facebook.com/people/Matthew-Donavan-Clemens/100000220742923', u'id': u'100000220742923'}

def gen_stops():
    english_ignore = []
    with open('stoplist.txt',  'r') as stops:
        for word in stops:
            english_ignore.append(word.strip())
    return frozenset(english_ignore)

def ngrams(tokens, MIN_N, MAX_N):
    n_tokens = len(tokens)
    for i in xrange(n_tokens):
        for j in xrange(i+MIN_N, min(n_tokens, i+MAX_N)+1):
            yield tokens[i:j]

def text_processer(document):
    """ Alot of python magic and helpers in this list comprehension
     If this is one area where a more precise C implementation would be amazing
     but more work."""
    raw_strings = tuple(document.lower().split())
    container = Counter(raw_strings)
    container.update([x for x in ngrams(raw_strings,2,4)])
    return container


if __name__ == '__main__':
    print text_processer('This is a test sencence with strings')

