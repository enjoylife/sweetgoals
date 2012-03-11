# -*- coding: UTF-8 -*-
from collections import Counter
from Stemmer import Stemmer

import numpy as np
import scipy.sparse as sp

from sklearn.datasets import fetch_20newsgroups

import sys
from time import time

from operator import itemgetter
from sklearn.datasets import fetch_20newsgroups
from sklearn.linear_model import RidgeClassifier
from sklearn.utils.extmath import density
from sklearn import metrics
from sklearn.preprocessing import normalize

testuser = {u'first_name': u'Matthew', u'last_name': u'Clemens', u'middle_name': u'Donavan', u'name': u'Matthew Donavan Clemens', u'locale': u'en_US', u'gender': u'male', u'link': u'http://www.facebook.com/people/Matthew-Donavan-Clemens/100000220742923', u'id': u'100000220742923'}
def doc_to_lib_format(documents):
    term_counts_per_doc = []
    counts = Counter()
    stops = gen_stops()
    proc = text_processer

    stemmer = Stemmer('english')
    stemy = stemmer.stemWord
    # parallelization 
    for doc in raw_documents:
        cnts = proc(doc,stops)
        counts.update(cnts)
        term_counts_per_doc.append(cnts)

    if  vocab:
        return _to_matrix(term_counts_per_doc, vocab)

    # convert to a document-token matrix
    vocab = dict((t, i) for i, t in enumerate(counts))

    tfidf = TfidfTransformer()
    X = _to_matrix(term_counts_per_doc , vocab)
    return vocab , tfidf.fit(X).transform(X, copy=False)

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

def gen_stops():
    english_ignore = []
    with open('stoplist.txt',  'r') as stops:
        for word in stops:
            english_ignore.append(word.strip())
    return frozenset(english_ignore)

def _to_matrix(term_count_dicts, vocabulary):
        i_indices = []
        j_indices = []
        values = []

        for i, term_count_dict in enumerate(term_count_dicts):
            for term, count in term_count_dict.iteritems():
                j = vocabulary.get(term)
                if j is not None:
                    i_indices.append(i)
                    j_indices.append(j)
                    values.append(count)
            # free memory as we go
            term_count_dict.clear()

        shape = (len(term_count_dicts), max(vocabulary.itervalues()) + 1)
        return sp.coo_matrix((values, (i_indices, j_indices)),
                             shape=shape, dtype=long)

def doc_to_td_idf_matrix(raw_documents,vocab=False):


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


    term_counts_per_doc = []
    counts = Counter()
    stops = gen_stops()

    stemmer = Stemmer('english')
    stemy = stemmer.stemWord
    # parallelization 
    for doc in raw_documents:
        cnts = text_processer(doc,stops)
        counts.update(cnts)
        term_counts_per_doc.append(cnts)

    if  vocab:
        return _to_matrix(term_counts_per_doc, vocab)

    # convert to a document-token matrix
    vocab = dict((t, i) for i, t in enumerate(counts))

    tfidf = TfidfTransformer()
    X = _to_matrix(term_counts_per_doc , vocab)
    return vocab , tfidf.fit(X).transform(X, copy=False)

class TfidfTransformer():
    """Transform a count matrix to a normalized tf or tf–idf representation

    Tf means term-frequency while tf–idf means term-frequency times inverse
    document-frequency. This is a common term weighting scheme in information
    retrieval, that has also found good use in document classification.

    The goal of using tf–idf instead of the raw frequencies of occurrence of a
    token in a given document is to scale down the impact of tokens that occur
    very frequently in a given corpus and that are hence empirically less
    informative than features that occur in a small fraction of the training
    corpus.

    In the SMART notation used in IR, this class implements several tf–idf
    variants. Tf is always "n" (natural), idf is "t" iff use_idf is given,
    "n" otherwise, and normalization is "c" iff norm='l2', "n" iff norm=None.

    Parameters
    ----------
    norm : 'l1', 'l2' or None, optional
        Norm used to normalize term vectors. None for no normalization.

    use_idf : boolean, optional
        Enable inverse-document-frequency reweighting.

    smooth_idf : boolean, optional
        Smooth idf weights by adding one to document frequencies, as if an
        extra document was seen containing every term in the collection
        exactly once. Prevents zero divisions.

    sublinear_tf : boolean, optional
        Apply sublinear tf scaling, i.e. replace tf with 1 + log(tf).

    Notes
    -----
    **References**:

    .. [Yates2011] `R. Baeza-Yates and B. Ribeiro-Neto (2011). Modern
                   Information Retrieval. Addison Wesley, pp. 68–74.`

    .. [MSR2008] `C.D. Manning, H. Schütze and P. Raghavan (2008). Introduction
                 to Information Retrieval. Cambridge University Press,
                 pp. 121–125.`
    """

    def __init__(self, norm='l2', use_idf=True, smooth_idf=True,
                 sublinear_tf=False):
        self.norm = norm
        self.use_idf = use_idf
        self.smooth_idf = smooth_idf
        self.sublinear_tf = sublinear_tf
        self.idf_ = None

    def fit(self, X, y=None):
        """Learn the idf vector (global term weights)

        Parameters
        ----------
        X: sparse matrix, [n_samples, n_features]
            a matrix of term/token counts
        """
        if self.use_idf:
            n_samples, n_features = X.shape
            df = np.bincount(X.nonzero()[1])
            if df.shape[0] < n_features:
                # bincount might return fewer bins than there are features
                df = np.concatenate([df, np.zeros(n_features - df.shape[0])])
            df += int(self.smooth_idf)
            self.idf_ = np.log(float(n_samples) / df)

        return self

    def transform(self, X, copy=True):
        """Transform a count matrix to a tf or tf–idf representation

        Parameters
        ----------
        X: sparse matrix, [n_samples, n_features]
            a matrix of term/token counts

        Returns
        -------
        vectors: sparse matrix, [n_samples, n_features]
        """
        X = sp.csr_matrix(X, dtype=np.float64, copy=copy)
        n_samples, n_features = X.shape

        if self.sublinear_tf:
            np.log(X.data, X.data)
            X.data += 1

        if self.use_idf:
            expected_n_features = self.idf_.shape[0]
            if n_features != expected_n_features:
                raise ValueError("Input has n_features=%d while the model"
                                 " has been trained with n_features=%d" % (
                                     n_features, expected_n_features))
            d = sp.lil_matrix((n_features, n_features))
            d.setdiag(self.idf_)
            # *= doesn't work
            X = X * d

        if self.norm:
            X = normalize(X, norm=self.norm, copy=False)

        return X


if __name__ == '__main__':
    # Load some categories from the training set
    categories = [
        'alt.atheism',
        'talk.religion.misc',
        'comp.graphics',
        'sci.space',
    ]
    # Uncomment the following to do the analysis on all the categories
    #categories = None

    print "Loading 20 newsgroups dataset for categories:"
    print categories if categories else "all"

    data_train = fetch_20newsgroups(subset='train', categories=categories,
                                   shuffle=True, random_state=42)

    data_test = fetch_20newsgroups(subset='test', categories=categories,
                                  shuffle=True, random_state=42)
    print 'data loaded'

    categories = data_train.target_names    # for case categories == None

    print "%d documents (training set)" % len(data_train.data)
    print "%d documents (testing set)" % len(data_test.data)
    print "%d categories" % len(categories)
    print

    # split a training set and a test set
    y_train, y_test = data_train.target, data_test.target

    print "Extracting features from the training dataset using a sparse vectorizer"
    t0 = time()
    vocab, X_train = doc_to_td_idf_matrix(data_train.data)
    print "done in %fs" % (time() - t0)
    print "n_samples: %d, n_features: %d" % X_train.shape
    print

    print "Extracting features from the test dataset using the same vectorizer"
    t0 = time()
    X_test = doc_to_td_idf_matrix(data_test.data, vocab)
    print "done in %fs" % (time() - t0)
    print "n_samples: %d, n_features: %d" % X_test.shape
    print

