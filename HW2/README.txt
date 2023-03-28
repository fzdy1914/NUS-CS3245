E0253741@u.nus.edu-E0253717@u.nus.edu
This is the README file for A0177381X-A0177357R's submission

== Python Version ==

We're using Python Version <3.8.5> for
this assignment.

== General Notes about this assignment ==

Give an overview of your program, describe the important algorithms/steps 
in your program, and discuss your experiments in general.  A few paragraphs 
are usually sufficient.

This program basically comprises two parts - indexing and searching, of which we will illustrate respectively in below.

- Indexing
First of all, we read from the training corpus. Text pre-processing includes using sentence and word tokenizer from nltk package, stemming using Porter Stemmer and setting all characters to lower case. In local block in memory, every encountered term is written in a dict data structure as [term : posting list of doc ids] pair. When the block size reaches a threshold, the current block will be store on disk.
After reading all postings, we perform k-way merging on all posting files without having them all loaded to memory. We use priority queue to facilitate merging here. Each item in the queue has the format (term, block_idx, pickle_file_reader), such that the priority queue is ordered by the term (alphabetical) then the block index. For every term when the merging is done, it's dumped to the final posting file, such that it does not consume local memory.
Finally, we will have a consolidated posting file for all terms in the the format [term : length of posting list :sorted doc id list]. We also create skip pointer indices list for all possible postings length, that is the (0, number of docs).

- Searching
The first step of searching is to parse the query after performing text pre-processing as stated in indexing phase. Shunting-yard algorithm is utilized here to produce a postfix notion of the query. To highlight, we would parse AND followed by NOT into a new special operation 'AND NOT' that will be dealt together. This is because when we have a query in the form 'a AND NOT b', it is computationally less costly to perform a subtraction of b's postings from a's postings, instead of computing 'NOT b' then intersect with a's postings.
We could then build an abstract syntax tree from the postfix expression, where all leave nodes are terms and intermediate nodes operators. However, the tree could be literally skewed such that there is large overhead if we perform operation in the original sequence. We optimize this by flattening a binary tree into a non-binary one in recursive manner and sorting child nodes according to computational cost.
    - NOT, no flattening could be done.
    - NOT NOT, is handled during parsing time.
    - OR
        \
         OR
           \
            OR
      OR could be merged with any child node at lower end that is also an OR.
    -   AND  |      AND     | AND       | AND
       /     |     /        |    \      |    \
     AND     | AND NOT      |     AND   |  AND NOT
      AND followed by AND or AND NOT could have their child nodes merged.
    -   AND NOT  |      AND NOTx
       /         |     /
     AND         |  AND NOT
      AND followed by AND or AND NOT could have their child nodes merged.
In the flattened tree, for each node, any child nodes in the operation list could be performed commutatively, such that we could start from the computationally cheapest one. For every term node, the cost would be the length of its posting list. For an operator nodes, the cost is the sum of costs of its child nodes.
Evaluation is performed on the optimized AST. For each of AND, OR, AND NOT, we have implemented intersect(), union() and diff() methods on two posting lists with skip pointers. The basic logic behind this step is to move the current position pointer on the posting list and pointer on the skip pointer indices when possible; when it comes to OR and AND NOT, operation, doc ids that should be included will be return with new pointers simultaneously.
For testing accuracy, we've done experiments comparing the results from the above mentioned methods with those using python set operations.

== Files included with this submission ==

List the files in your submission here and provide a short 1 line
description of each file.  Make sure your submission's files are named
and formatted correctly.
- index.py:
    create dictionary file; create and merge postings file
- pickle_file_handler.py:
    include auxiliary structure to facilitate reading from pickle file
- search.py:
    run search for queries based on generated dictionary and postings file in index.py
- abstract_syntax_tree.py:
    include auxiliary structure to flatten and optimize evaluation of the query
- dictionary.txt:
    include for all terms: [term: file location] pair; all doc id set; skip pointers indices for all possible length
- postings.txt:
    include for all terms: [term : length of posting list :sorted doc id list]
- README.txt:
    summary of the program

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[x] We, A0177381X-A0177357R, certify that I/we have followed the CS 3245 Information
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
shunting yard algorithm