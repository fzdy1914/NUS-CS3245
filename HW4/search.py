#!/usr/bin/python3
import pickle
import nltk
import sys
import getopt
import numpy as np
from nltk.corpus import stopwords

from index import string_process
from scipy.sparse import csr_matrix, load_npz
from sklearn.utils.extmath import safe_sparse_dot

ignoreStopWord = True
stop_words = set(stopwords.words('english'))
useZone = False
useRelatedTerm = True
usePseudoRelevanceFeedback = False

query_type_list = {"Native AND", "Native OR", "Ignore AND"}
query_type = "Ignore AND"


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
    doc_to_idx_dict = pickle.load(f)
    term_to_idx_dict = pickle.load(f)
    idx_to_doc_dict = pickle.load(f)
    idx_to_term_dict = pickle.load(f)
    idf_dict = pickle.load(f)
    f.close()

    f = open(postings_file, 'rb')
    zone_posting_list = pickle.load(f) if useZone else dict()
    f.close()

    f = open(queries_file, 'r')
    line = f.readline()
    f.close()

    related_term = pickle.load(open("related_term.txt", 'rb')) if useRelatedTerm else dict()

    doc_tf = load_npz("tf.npz")

    # query pre-processing
    if query_type == "Ignore AND":
        lines = [line.strip().replace("AND", "")]
    else:
        lines = line.strip().split("AND")

    doc_score_list = list()
    result_list = list()
    zone_docs = set()

    for line in lines:
        col = list()
        data = list()
        all_related_term_idxs = list()

        # query term processing, zone and related term used here
        for sent_tokens in nltk.sent_tokenize(line):
            for word in nltk.word_tokenize(sent_tokens):
                if ignoreStopWord and word in stop_words:
                    continue
                term = stemmer.stem(word).lower()
                term = string_process(term)
                if term in term_to_idx_dict:
                    term_idx = term_to_idx_dict[term]
                    all_related_term_idxs.append(term_idx)
                    if useZone and term_idx in zone_posting_list:
                        zone_docs |= set(zone_posting_list[term_idx])

                if useRelatedTerm and term in related_term:
                    for new_term in related_term[term]:
                        if new_term in term_to_idx_dict:
                            all_related_term_idxs.append(term_to_idx_dict[new_term])

        for term_idx in all_related_term_idxs:
            col.append(term_idx)
            data.append(1)

        # calculate query term tf idf
        col = np.array(col)
        data = np.array(data)
        row = np.zeros_like(col)
        term_tf_idf_vector = csr_matrix((data, (row, col)), shape=(1, len(term_to_idx_dict)))
        term_tf_idf_vector.sum_duplicates()
        term_tf_idf_vector.data = 1 + np.log10(term_tf_idf_vector.data)

        for term_idx in term_tf_idf_vector.nonzero()[1]:
            term_tf_idf_vector[0, term_idx] *= idf_dict[term_idx]

        # assign score for document
        doc_score = safe_sparse_dot(doc_tf, term_tf_idf_vector.T)
        non_zero_length = doc_score.nonzero()[0].shape[0]
        doc_score = doc_score.toarray().squeeze() * -1

        # Rocchio (Below is a param set called Ide Dec-Hi)
        if usePseudoRelevanceFeedback:
            alpha = 1
            beta = 0.5
            gamma = 0
            rel_count = 10  # Use top-10 relevant documents to update query vector.
            irel_count = 1  # Use only the most non-relevant document to update query vector.
            iters = 2

            rankings = np.argsort(doc_score, axis=0)
            for _ in range(iters):
                # update query term tf idf using rocchio
                rel_vecs = doc_tf[rankings[:rel_count]].mean(axis=0) # non-sparse matrix
                irel_vecs = doc_tf[rankings[-irel_count:]].mean(axis=0)
                term_tf_idf_vector = alpha * term_tf_idf_vector + beta * rel_vecs - gamma * irel_vecs

                doc_score = doc_tf.dot(term_tf_idf_vector.T)
                non_zero_length = doc_score.nonzero()[0].shape[0]
                doc_score = np.squeeze(np.asarray(doc_score)) * -1
                rankings = np.argsort(doc_score, axis=0)

        doc_score_list.append(doc_score)
        result_list.append(set(np.argsort(doc_score)[:non_zero_length].tolist()))

    doc_score_list = np.vstack(doc_score_list).sum(axis=0)
    ans_set = set(result_list[0])

    for result in result_list:
        if query_type == "Native OR":
            ans_set |= result
        else:
            ans_set &= result

    ans_list = list()
    for doc_idx in ans_set:
        ans_list.append((doc_score_list[doc_idx], doc_idx))

    # sort docs according score
    sorted_result = [p[1] for p in sorted(ans_list, key=lambda x: x[0])]

    # use zone information
    if useZone:
        in_zone = []
        out_zone = []
        for result in sorted_result:
            if result in zone_docs:
                in_zone.append(result)
            else:
                out_zone.append(result)
        print('number of docs moved to the front: ', len(in_zone))
        sorted_result = in_zone + out_zone
    
    final_result = [idx_to_doc_dict[p][0] for p in sorted_result]
    final_result = list(dict.fromkeys(final_result))

    f = open(results_file, 'w')
    f.write(" ".join([str(i) for i in final_result]))
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
