#!/usr/bin/python3
import csv
import math
import pickle
import re

import nltk
from nltk.corpus import stopwords
import sys
import getopt
import multiprocessing as mp
from sklearn.preprocessing import normalize

import numpy as np

from scipy.sparse import csr_matrix, save_npz


useZone = True
ignoreStopWord = True
stop_words = set(stopwords.words('english'))

# extend cvs field size limit
maxInt = sys.maxsize
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 2)


def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


def string_process(string):
    return ''.join([c for c in string if c.isalpha()])


# multiprocess function to preprocess document and extract related terms
def mp_process(curr_row):
    js_code = re.findall(r'//<.*\n.*\n//]]>', curr_row["content"])
    for code in js_code:
        curr_row["content"] = curr_row["content"].replace(code, "")

    stemmer = nltk.PorterStemmer()
    raw_string = curr_row["title"] + "\n" + curr_row["court"] + "\n" + curr_row["content"] + "\n" + curr_row["date_posted"]
    lines = raw_string.split("\n")
    processed_terms = list()
    zone_terms = list()
    for i, line in enumerate(lines):
        for sent_tokens in nltk.sent_tokenize(line):
            for word in nltk.word_tokenize(sent_tokens):
                if ignoreStopWord and word in stop_words:
                    continue
                term = stemmer.stem(word).lower()
                term = string_process(term)
                if term == "":
                    continue
                else:
                    if useZone and i in (0, 1):
                        zone_terms.append(term)
                    
                    processed_terms.append(term)
    curr_row["processed_terms"] = processed_terms
    curr_row["zone_terms"] = zone_terms
    return curr_row


if __name__ == '__main__':
    input_file = output_file_dictionary = output_file_postings = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-i': # input directory
            input_file = a
        elif o == '-d': # dictionary file
            output_file_dictionary = a
        elif o == '-p': # postings file
            output_file_postings = a
        else:
            assert False, "unhandled option"

    if input_file is None or output_file_postings is None or output_file_dictionary is None:
        usage()
        sys.exit(2)

    doc_to_idx_dict = dict()
    term_to_idx_dict = dict()
    idx_to_doc_dict = dict()
    idx_to_term_dict = dict()

    print("Program start...")
    with open(input_file, "r", encoding="utf8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        rows = list(csv_reader)

    print("Reading data file finished, start preprocessing...")
    # preprocess using multiprocessing
    pool = mp.Pool(3)
    processed_rows = pool.map(mp_process, rows)

    print("Document preprocessing finished, calculating raw tf...")

    zone_posting_list = dict()

    # create indexing for doc and term
    indptr = [0]
    indices = []
    data = []
    for row in processed_rows:
        doc_id = (row['document_id'], row["court"])
        doc_idx = doc_to_idx_dict.setdefault(doc_id, len(doc_to_idx_dict))

        for term in row["processed_terms"]:
            term_idx = term_to_idx_dict.setdefault(term, len(term_to_idx_dict))
            indices.append(term_idx)
            data.append(1)
        
        indptr.append(len(indices))

        if useZone:
            for term in row['zone_terms']:
                term_idx = term_to_idx_dict.setdefault(term, len(term_to_idx_dict))

                if term_idx in zone_posting_list:
                    zone_posting_list[term_idx].add(doc_idx)
                else:
                    zone_posting_list[term_idx] = {doc_idx}

    # store zone postings to disk
    out_posting_file = open(output_file_postings, "wb")
    if useZone:
        pickle.dump(zone_posting_list, out_posting_file)
    out_posting_file.close()

    # calculate tf and idf with sparse matrix
    print("Calculating true tf...")
    sparse_doc_term_matrix = csr_matrix((data, indices, indptr))
    sparse_doc_term_matrix.sum_duplicates()
    sparse_doc_term_matrix.data = 1 + np.log10(sparse_doc_term_matrix.data)
    save_npz("tf", normalize(sparse_doc_term_matrix))
    print("Calculating idf...")
    sparse_doc_term_matrix = sparse_doc_term_matrix.tocsc()
    documents_num = len(doc_to_idx_dict)
    new_idf_dict = dict()
    for i in range(sparse_doc_term_matrix.shape[1]):
        new_idf_dict[i] = math.log10(documents_num / sparse_doc_term_matrix[:, i].nonzero()[0].shape[0])

    # build reversed dict
    for doc, idx in doc_to_idx_dict.items():
        idx_to_doc_dict[idx] = doc
    for term, idx in term_to_idx_dict.items():
        idx_to_term_dict[idx] = term

    # store dictionary to disk
    out_dictionary_file = open(output_file_dictionary, "wb")
    pickle.dump(doc_to_idx_dict, out_dictionary_file)
    pickle.dump(term_to_idx_dict, out_dictionary_file)
    pickle.dump(idx_to_doc_dict, out_dictionary_file)
    pickle.dump(idx_to_term_dict, out_dictionary_file)
    pickle.dump(new_idf_dict, out_dictionary_file)
    out_dictionary_file.close()

    print("Index finished!")