class SharedAttributes:
    def __init__(self):
        self._data = {}

    def getHDF5Attributes(self):
        attrs = {}
        for key, value in self._data.items():
            attrs[':'.join(key)] = value
        return attrs

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self):
        yield from self._data.items()
