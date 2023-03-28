import pickle

from pickle_file_handler import PickleFileReader

f = open("dictionary.txt", "rb")
dic, idf = pickle.load(f), pickle.load(f)
print(len(dic))
print(len(idf))

reader = PickleFileReader("postings.txt")
# total = 0
# while reader.next() is not None:
#     total += reader.current[1]
# print(total)

# for term in dic:
#     print(term)
#     print(idf[term])
#     entry = reader.load_from_location(dic[term])
#     print(entry[1])
#     assert entry[0] == term
print(reader.load_from_location(dic["kick"]))