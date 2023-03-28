import pickle
import random
import re
f = open("dictionary.txt", "rb")
dic, idf = pickle.load(f), pickle.load(f)

unseen_word = "_unseen_word_"
random_list = random.sample([i for i in dic.keys() if not bool(re.search(r'\d', i))], 99)
random_list.append(unseen_word)

list_of_list = list()
for i in range(100):
    lst = list()
    for j in range(100):
        word = random.choice(random_list)
        if word in lst:
            print("good")
        lst.append(word)
    list_of_list.append(" ".join(lst))

f = open("query.txt", 'w')
f.write("\n".join(list_of_list))
f.close()
