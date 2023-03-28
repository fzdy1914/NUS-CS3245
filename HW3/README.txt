E0253741@u.nus.edu-E0253717@u.nus.edu
This is the README file for A0177381X-A0177357R's submission

== Python Version ==

I'm (We're) using Python Version <3.8.5> for
this assignment.

== General Notes about this assignment ==

Give an overview of your program, describe the important algorithms/steps 
in your program, and discuss your experiments in general.  A few paragraphs 
are usually sufficient.

This program basically comprises two parts - indexing and searching, of which we will illustrate respectively in below.

- Indexing
First of all, we read from the training corpus. Text pre-processing includes using sentence and word tokenizer from nltk package, stemming using Porter Stemmer and setting all characters to lower case. We count the term frequency for each term in a document. We then calculate and normalize the weight for the term in the document using lnc scheme, which id then stored to postings lists in disk. Store inverse document frequency in dictionary file as well.

- Searching
The first step of searching is to parse the query after performing text pre-processing as stated in indexing phase. Different to index phase, we calculate weights for terms in the queries using ltc scheme, where idf is included. We then rank the documents according to cosine similarity (tf* idf) using a min heap. We can build a heap in O(N) time, retrieve the best k results in O(k log N), where k equals 10 here.

== Files included with this submission ==

List the files in your submission here and provide a short 1 line
description of each file.  Make sure your submission's files are named
and formatted correctly.

- index.py:
    create postings files for documents where each term is weighted by lnc scheme
- pickle_file_handler.py:
    include auxiliary structure to facilitate reading from pickle file
- search.py:
    calculate weights for query terms and find (up tp) top 10 relevant documents
- dictionary.txt:
    include for all terms: inverse document frequency
- postings.txt:
    include for all terms: [term][doc_id]:[weighted frequency]
- README.txt:
    summary of the program

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[x] We, A0177381X-A0177357R, certify that we have followed the CS 3245 Information
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

<Please list any websites and/or people you consulted with for this
assignment and state their role>
