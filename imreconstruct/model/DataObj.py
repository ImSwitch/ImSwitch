import os

import numpy as np
import h5py
import tifffile as tiff


class DataObj:
    def __init__(self, name, *, path=None, data=None, attrs=None):
        self.name = name
        self.dataPath = path
        self.data = data
        self.attrs = attrs
        self.darkFrame = None
        self._meanData = None

    @property
    def dataLoaded(self):
        return self.data is not None

    @property
    def numFrames(self):
        return np.shape(self.data)[0] if self.data is not None else None

    def checkAndLoadData(self):
        if self.dataLoaded:
            pass
        else:
            try:
                self.data, self.attrs = loadData(self.dataPath)  # DataIO_tools.load_binary(self.data_path, dtype=np.uint16)
                if self.data is not None:
                    print('Data loaded')
            except:
                pass

    def checkAndLoadDarkFrame(self):
        pass

    def checkAndUnloadData(self):
        try:
            if self.dataLoaded:
                self.data = None
                self._meanData = None
            else:
                pass
        except:
            print('Error while unloading data')

    def getMeanData(self):
        if self._meanData is None:
            self._meanData = np.array(np.mean(self.data, 0), dtype=np.float32)

        return self._meanData


def loadData(path):
    path = os.path.abspath(path)
    try:
        ext = os.path.splitext(path)[1]

        if ext in ['.hdf5', '.hdf']:
            with h5py.File(path, 'r') as datafile:
                data = np.array(datafile.get('data')[:])
                attrs = dict(datafile.attrs)

        elif ext in ['.tiff', '.tif']:
            with tiff.TiffFile(path) as datafile:
                data = datafile.asarray()
                attrs = None

        else:
            raise ValueError(f'Unsupported file extension "{ext}"')

        return data, attrs
    except:
        print('Error while loading data')
        return None
