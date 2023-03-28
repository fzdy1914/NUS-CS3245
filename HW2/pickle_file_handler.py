import pickle


class PickleFileReader:
    """
    PickleFileReader is a helper class for reading data from a pickled file.
    """

    def __init__(self, path):
        self.path = path
        self.file = open(path, "rb")
        self.current = None

    def load_from_location(self, location):
        try:
            self.file.seek(location)
            self.current = pickle.load(self.file)
            return self.current
        except:
            self.current = None
            return None

    def next(self):
        try:
            self.current = pickle.load(self.file)
            return self.current
        except:
            self.current = None
            return None

    def close(self):
        self.file.close()
