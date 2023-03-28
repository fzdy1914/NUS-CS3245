#!/usr/bin/python3
import math
import os
import pickle
import re
import nltk
import sys
import getopt
from queue import PriorityQueue
from pickle_file_handler import PickleFileReader

def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')
    if not os.path.exists(in_dir):
        print("directory-of-documents path not exist!")
        sys.exit(2)

    stemmer = nltk.PorterStemmer()

    block_size = 100000  # hard-coding the block size to be 100000 but our method support different block size

    documents = os.listdir(in_dir)

    current_block_num = 0
    current_block_size = 0

    # In this assignment, we use SPIMI algorithm to process the document block
    # but instead of list, we use set to store posting_list
    # because we want to sort the list only at the merging step and do not need duplicate doc_id
    local_posting_set_dic = dict()  # key: term, item: set of doc_id

    for document in documents:
        real_doc_path = os.path.join(in_dir, document)
        if not os.path.exists(real_doc_path):
            print("Document:", document, "not exist!")
            continue

        doc_id = int(document)
        f = open(real_doc_path, "r")
        lines = f.readlines()
        f.close()

        for line in lines:
            for sent_tokens in nltk.sent_tokenize(line):
                for word in nltk.word_tokenize(sent_tokens):
                    term = stemmer.stem(word).lower()
                    # Add to the set if term exists or initialize with a set
                    if term in local_posting_set_dic:
                        local_posting_set_dic[term].add(doc_id)
                    else:
                        local_posting_set_dic[term] = {doc_id}

                    current_block_size += 1

                    # If the memory is full, save the postings to disk
                    if current_block_size == block_size:
                        local_posting_set_file = open("local_posting_set_dic_%s.txt" % current_block_num, "wb")
                        for term in sorted(local_posting_set_dic.keys()):
                            pickle.dump((term, local_posting_set_dic[term]), local_posting_set_file)
                        local_posting_set_file.close()
                        print("block", current_block_num, "finished!")
                        current_block_num += 1
                        local_posting_set_dic = dict()
                        current_block_size = 0

    # clean up final block
    if len(local_posting_set_dic) > 0:
        local_posting_set_file = open("local_posting_set_dic_%s.txt" % current_block_num, "wb")
        for term in sorted(local_posting_set_dic.keys()):
            pickle.dump((term, local_posting_set_dic[term]), local_posting_set_file)
        local_posting_set_file.close()
        print("block", current_block_num, "finished!")
        current_block_num += 1
    print("Index by block finished, start merging")

    pq = PriorityQueue()  # we use priority queue to help k-way merging， format: (term, block_idx, pickle_file_reader)

    #  initialize priority queque
    for block_idx in range(0, current_block_num):
        reader = PickleFileReader("local_posting_set_dic_%s.txt" % block_idx)
        if reader.next() is not None:
            pq.put((reader.current[0], block_idx, reader))
        else:
            reader.close()

    final_out_dictionary = dict()  # key: term, item: (term freq, start entry location in pickle file)
    final_doc_id_set = set()  # store all seen doc_id for future NOT operation

    out_postings_file = open(out_postings, "wb")

    current_term = pq.queue[0][0]  # Initialize with the first term in priority queue
    current_posting_set = set()
    current_file_loc = 0

    while pq.qsize() > 0:
        term, block_idx, reader = pq.get()
        if term != current_term:
            final_posting_list = list(sorted(current_posting_set))
            pickle.dump((current_term, len(final_posting_list), final_posting_list), out_postings_file)
            final_out_dictionary[current_term] = current_file_loc
            final_doc_id_set |= current_posting_set

            current_term = term
            current_posting_set = reader.current[1]
            current_file_loc = out_postings_file.tell()
        else:
            current_posting_set |= reader.current[1]

        # update priority queue
        if reader.next() is not None:
            pq.put((reader.current[0], block_idx, reader))
        else:
            reader.close()

    # clean up the final entry
    final_posting_list = list(sorted(current_posting_set))
    pickle.dump((current_term, len(final_posting_list), final_posting_list), out_postings_file)
    final_out_dictionary[current_term] = current_file_loc
    final_doc_id_set |= current_posting_set
    out_postings_file.close()

    # store final dictionary
    out_dictionary_file = open(out_dict, "wb")
    pickle.dump(final_out_dictionary, out_dictionary_file)
    pickle.dump(final_doc_id_set, out_dictionary_file)
    out_dictionary_file.close()

    print("index done, cleaning temp files...")

    for block_idx in range(0, current_block_num):
        os.remove("local_posting_set_dic_%s.txt" % block_idx)
    print("temp files cleaned!")


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
