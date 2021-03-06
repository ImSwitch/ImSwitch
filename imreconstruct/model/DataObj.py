import os

import numpy as np
import h5py
import tifffile as tiff


class DataObj:
    def __init__(self, name, *, path=None, file=None):
        self.name = name
        self.dataPath = path
        self.darkFrame = None
        self._meanData = None
        self._file = file
        self._data = None
        self._attrs = None

    @property
    def data(self):
        if self._data is not None:
            return self._data

        if isinstance(self._file, h5py.File):
            self._data = np.array(self._file.get('data')[:])
        elif isinstance(self._file, tiff.TiffFile):
            self._data = self._file.asarray()

        return self._data

    @property
    def attrs(self):
        if self._attrs is not None:
            return self._attrs

        if isinstance(self._file, h5py.File):
            self._attrs = dict(self._file.attrs)

        return self._attrs

    @property
    def dataLoaded(self):
        return self.data is not None

    @property
    def numFrames(self):
        return np.shape(self.data)[0] if self.data is not None else None

    def checkAndLoadData(self):
        if not self.dataLoaded:
            try:
                self._file = loadFromPath(self.dataPath)
                if self.data is not None:
                    print('Data loaded')
            except:
                pass

    def checkAndLoadDarkFrame(self):
        pass

    def checkAndUnloadData(self):
        if self._file is not None:
            try:
                self._file.close()
            except:
                print('Error closing file')

        self._file = None
        self._data = None
        self._attrs = None
        self._meanData = None

    def getMeanData(self):
        if self._meanData is None:
            self._meanData = np.array(np.mean(self.data, 0), dtype=np.float32)

        return self._meanData


def loadFromPath(path):
    path = os.path.abspath(path)
    try:
        ext = os.path.splitext(path)[1]
        if ext in ['.hdf5', '.hdf']:
            return h5py.File(path, 'r')
        elif ext in ['.tiff', '.tif']:
            return tiff.TiffFile(path)
        else:
            raise ValueError(f'Unsupported file extension "{ext}"')
    except:
        print('Error while loading data')
        return None
