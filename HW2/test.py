import pickle

from pickle_file_handler import PickleFileReader

f = open("dictionary.txt", "rb")
dic, total_document = pickle.load(f), pickle.load(f)
print(len(dic))
print(len(total_document))

reader = PickleFileReader("postings.txt")
total = 0
while reader.next() is not None:
    total += reader.current[1]
print(total)