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

def text_processer(document, stops,):
    """ Alot of python magic and helpers in this list comprehension
     If this is one area where a more precise C implementation would be amazing
     but alot of work compared to this """
    container = Counter()
    raw_strings = (document.lower()).split()
    memo = False
    for word in raw_strings:
        if len(word)>=2 and word not in stops:
            #bi grams
            if memo:
                container[tuple((memo,word))]+=1
            # Add single tokens
            container[(word)]+=1 
            # remember for bigram check
            memo = word
        else: memo = False
    return container


if __name__ == '__main__':
    pass

