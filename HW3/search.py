#!/usr/bin/python3
import math
import pickle
import re
from queue import PriorityQueue
import heapq

import nltk
import sys
import getopt

from pickle_file_handler import PickleFileReader


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')

    stemmer = nltk.PorterStemmer()

    f = open(dict_file, "rb")
    dictionary = pickle.load(f)
    inverse_document_frequency_dict = pickle.load(f)
    f.close()

    reader = PickleFileReader(postings_file)
    f = open(queries_file, 'r')
    lines = f.readlines()
    f.close()

    ans_list = list()
    for line in lines:
        line = line.strip()
        if line == "":
            ans_list.append(line)
            continue

        term_freq_dict = dict()
        for sent_tokens in nltk.sent_tokenize(line):
            for word in nltk.word_tokenize(sent_tokens):
                term = stemmer.stem(word).lower()
                filtered = True
                for char in term:
                    if char.isalnum():
                        filtered = False
                        break
                if filtered:
                    continue
                if term not in term_freq_dict:
                    term_freq_dict[term] = 1
                else:
                    term_freq_dict[term] += 1

        # calculate and normalize weights for query using ltc scheme
        tf_idf_dict = dict()
        for term in term_freq_dict:
            if term in dictionary:
                logarithm_term_freq = 1 + math.log10(term_freq_dict[term])
                # include idf in cosine similarity
                tf_idf_dict[term] = logarithm_term_freq * inverse_document_frequency_dict[term]

        # calculate the document score as the sum of score for each term
        score_dict = dict()  # key: doc_id, item: score
        for term, tf_idf in tf_idf_dict.items():
            real_term, posting_list = reader.load_from_location(dictionary[term])
            assert real_term == term
            for doc_id, tf in posting_list.items():
                if doc_id not in score_dict:
                    score_dict[doc_id] = tf * tf_idf
                else:
                    score_dict[doc_id] += tf * tf_idf

        # use a minimum heap for finding the 10 most relevant result
        final_result = list()
        score_list = list((-score, doc_id) for doc_id, score in score_dict.items())
        heapq.heapify(score_list)
        for _ in range(10):
            if len(score_list) <= 0:
                break
            final_result.append(heapq.heappop(score_list)[1])

        ans_list.append(" ".join([str(i) for i in final_result]))

    f = open(results_file, 'w')
    f.write("\n".join(ans_list))
    f.close()
    print("search done!")


dictionary_file = postings_file = file_of_queries = file_of_output = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file is None or postings_file is None or file_of_queries is None or file_of_output is None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
