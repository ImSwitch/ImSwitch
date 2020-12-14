import os

import numpy as np
import h5py
import tifffile as tiff


class DataObj:
    def __init__(self, name: str, path: str) -> None:
        self.name = name
        self.data_path = path
        self.data = None
        self.data_loaded = False
        self.dark_frame = None
        self.frames = None
        self._meanData = None

    def checkAndLoadData(self):
        if self.data_loaded:
            pass
        else:
            try:
                self.data = load_data(self.data_path)  # DataIO_tools.load_binary(self.data_path, dtype=np.uint16)
                if not self.data is None:
                    print('Data loaded')
                    self.data_loaded = True
                    self.frames = np.shape(self.data)[0]
            except:
                pass

    def checkAndLoadDarkFrame(self):
        pass

    def checkAndUnloadData(self):
        try:
            if self.data_loaded:
                self.data = None
                self._meanData = None
            else:
                pass
        except:
            print('Error while unloading data')

        self.data_loaded = False

    def getMeanData(self):
        if self._meanData is None:
            self._meanData = np.array(np.mean(self.data, 0), dtype=np.float32)

        return self._meanData


def load_data(path):
    path = os.path.abspath(path)
    try:
        ext = os.path.splitext(path)[1]

        if ext in ['.hdf5', '.hdf']:
            with h5py.File(path, 'r') as datafile:
                data = np.array(np.array(datafile.get('data')[:]))

        elif ext in ['.tiff', '.tif']:
            with tiff.TiffFile(path) as datafile:
                data = datafile.asarray()

        return data
    except:
        print('Error while loading data')
        return None
