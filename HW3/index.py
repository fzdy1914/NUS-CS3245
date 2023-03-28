#!/usr/bin/python3
import math
import os
import pickle
import re
import nltk
import sys
import getopt


def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')

    posting_list_dict = dict()  # key: term, item: dict{key: doc_id, item: term_freq}

    stemmer = nltk.PorterStemmer()
    documents = os.listdir(in_dir)
    documents_num = len(documents)

    for document in documents:
        real_doc_path = os.path.join(in_dir, document)
        if not os.path.exists(real_doc_path):
            print("Document:", document, "not exist!")
            continue

        doc_id = int(document)
        f = open(real_doc_path, "r")
        lines = f.readlines()
        f.close()

        term_freq_dict = dict()
        for line in lines:
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

        # calculate and normalize weights for documents using lnc scheme
        logarithm_term_freq_dict = dict()
        for term in term_freq_dict:
            logarithm_term_freq_dict[term] = 1 + math.log10(term_freq_dict[term])

        # calculate document length
        document_term_freq_vector_length = 0
        for _, logarithm_term_freq in logarithm_term_freq_dict.items():
            document_term_freq_vector_length += logarithm_term_freq ** 2
        document_term_freq_vector_length = math.sqrt(document_term_freq_vector_length)

        # write normalized weights to posting list
        for term, logarithm_term_freq in logarithm_term_freq_dict.items():
            if term not in posting_list_dict:
                posting_list_dict[term] = dict()
            posting_list_dict[term][doc_id] = logarithm_term_freq / document_term_freq_vector_length

    out_postings_file = open(out_postings, "wb")
    current_file_loc = 0

    inverse_document_frequency_dict = dict()
    final_out_dictionary = dict()  # key: term, item: start entry location in pickle file

    # store posting lists and idf to disk
    for term, posting_list in posting_list_dict.items():
        final_out_dictionary[term] = current_file_loc
        inverse_document_frequency_dict[term] = math.log10(documents_num / len(posting_list))
        pickle.dump((term, posting_list), out_postings_file)
        current_file_loc = out_postings_file.tell()

    out_dictionary_file = open(out_dict, "wb")
    pickle.dump(final_out_dictionary, out_dictionary_file)
    pickle.dump(inverse_document_frequency_dict, out_dictionary_file)
    out_dictionary_file.close()


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory is None or output_file_postings is None or output_file_dictionary is None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
