E0253741@u.nus.edu-E0253717@u.nus.edu-E0260166@u.nus.edu
This is the README file for A0177381X-A0177357R-A0177660X's submission

== Python Version ==

We're using Python Version <3.9> for this assignment. The library included is for Python 3.9, manylinux, x86_64 only.

== General Notes about this assignment ==

This program basically comprises two parts - indexing and searching, of which we will illustrate respectively in below.

- Indexing
First of all, we read from the training corpus. To accelerate text pre-processing, we use multiprocessing to perform
sentence and word tokenization and stemming. We count the term frequency for each term in a document.

We then calculate and normalize the term frequency in the document using lnc scheme, which id then stored to postings
lists in disk. Store idf in dictionary file as well. Taken space constraints into consideration, we use sparse matrix
for computation.

- Searching
The first step of searching is to parse the query after performing text pre-processing as stated in indexing phase.
Then we calculate weights for terms in the queries using ltc scheme, where idf is included. We then rank the documents
according to cosine similarity (tf*idf), and relevant results are retrieved. Sparse matrix operations are also employed
in searching phase.

The usage of zone information, pseudo feedback, query expansion will be discussed in detail in BONUS.docx

== Files included with this submission ==

List the files in your submission here and provide a short 1 line
description of each file.  Make sure your submission's files are named
and formatted correctly.

- index.py:
    calculate document tf and term idf
- search.py:
    calculate weights for query terms and find relevant documents
- dictionary.txt:
    store doc_to_idx dict and term_to_idx dict and their reversed dict together with inverse document frequency dict
- postings.txt:
    store zone posting list
- tf.npz:
    store document tf matrix
- related_term.txt
    pre-compiled related term dict
- README.txt:
    summary of the program
- BONUS.txt:
    explanation of the query refinement

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[x] We, A0177381X-A0177357R-A0177660X, certify that we have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, I/we
expressly vow that I/we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] I/We, A0000000X, did not follow the class rules regarding homework
assignment, because of the following reason:

<Please fill in>

We suggest that we should be graded as follows:

<Please fill in>

== References ==

We actually tried out several techniques including Reflective Random Index, Neural Vector Spaces, etc.
However, none of them perform well in this specific task. So, we do not include the code of them in this submission.

We referred https://www.kaggle.com/jerrykuo7727/rocchio when doing Rocchio algorithm.