#!/usr/bin/python3
import pickle
import re
import nltk
import sys
import getopt

from abstract_syntax_tree import ASTNode, NodeType
from pickle_file_handler import PickleFileReader


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


# AND_NOT has a higher preference than AND
operator_precedence = {'NOT': 0, "AND_NOT": 1, 'AND': 2, 'OR': 3, "(": 4, ")": 5}


def parse_bool_expr(expr, remove_not_not=True, replace_and_not=True):
    parentheses = 0
    output_stack = []
    operator_stack = []

    stemmer = nltk.PorterStemmer()

    expr = expr.replace("(", " ( ").replace(")", " ) ")
    if remove_not_not:
        expr = expr.replace("NOT NOT", " ")
    if replace_and_not:
        expr = expr.replace("AND NOT", "AND_NOT")

    tokens = list(filter(lambda x: x != "", expr.split(" ")))

    # Shunting - yard algorithm: create a postfix list of expression
    for token in tokens:
        if token == '(':
            operator_stack.append(token)
            parentheses += 1
            continue
        if token == ')':
            assert parentheses > 0
            while operator_stack[-1] != '(':
                operator = operator_stack.pop()
                output_stack.append(operator)
            parentheses -= 1
            operator_stack.pop()
        elif token in operator_precedence:
            while len(operator_stack) \
                    and operator_precedence[token] >= operator_precedence[operator_stack[-1]] \
                    and token != "NOT":
                operator = operator_stack.pop()
                output_stack.append(operator)
            operator_stack.append(token)
        else:
            token = stemmer.stem(token).lower()
            output_stack.append(token)

    while len(operator_stack) > 0:
        operator = operator_stack.pop()
        output_stack.append(operator)

    return output_stack


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')

    f = open(dict_file, "rb")
    dictionary = pickle.load(f)
    all_documents_list = list(sorted(pickle.load(f)))
    skip_pointers_list = pickle.load(f)
    f.close()

    ASTNode.load_skip_pointers(skip_pointers_list)

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

        term_stack = list()
        tokens = parse_bool_expr(line, remove_not_not=True, replace_and_not=True)

        # build abstract syntax tree
        for token in tokens:
            if token not in operator_precedence:
                if token not in dictionary:
                    term_stack.append(ASTNode(token, NodeType.Term, evaluated=True))
                else:
                    entry = reader.load_from_location(dictionary[token])
                    assert entry[0] == token
                    term_stack.append(
                        ASTNode(token, NodeType.Term, result_list=entry[2], cost=entry[1], evaluated=True))
            else:
                if token == "NOT":
                    operand = term_stack.pop()
                    term_stack.append(ASTNode(token, NodeType.Operator, child_nodes=[operand]))
                else:
                    right_operand = term_stack.pop()
                    left_operand = term_stack.pop()
                    term_stack.append(ASTNode(token, NodeType.Operator, child_nodes=[left_operand, right_operand]))

        tree = term_stack.pop()
        tree.flatten(all_documents_list)
        tree.evaluate(all_documents_list)
        ans_list.append(" ".join([str(i) for i in tree.result_list]))

    f = open(results_file, 'w')
    f.write("\n".join(ans_list))
    f.close()
    print("search done!")


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

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
