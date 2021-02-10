class SharedAttributes:
    def __init__(self):
        self.__data = {}

    def getHDF5Attributes(self):
        attrs = {}
        for key, value in self.__data.items():
            attrs[':'.join(key)] = value
        return attrs

    def __getitem__(self, key):
        return self.__data[key]

    def __setitem__(self, key, value):
        self.__data[key] = value

    def __iter__(self):
        yield from self.__data.items()
