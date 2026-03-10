# type: ignore

import numpy as np 
import tifffile as tiff
import h5py
import zarr
from qtpy import QtCore


class FileLoaderWorker(QtCore.QObject): 

    finished = QtCore.Signal(np.ndarray, str)                   
    error = QtCore.Signal(str)                                  
    sigFileLoaded = QtCore.Signal(np.ndarray, str)              

    def __init__(self, fullPath): 
        super().__init__()
        self.fullPath = fullPath

    @QtCore.Slot(str)
    def run(self, path):
        self.fullPath = path
        try:
            if self.fullPath.endswith((".tif", ".tiff")):
                data = tiff.imread(self.fullPath)
            elif self.fullPath.endswith((".h5", ".hdf5")):
                with h5py.File(self.fullPath, 'r') as f:
                    firstKey = list(f.keys())[0]
                    data = f[firstKey][:]                       
            elif self.fullPath.endswith(".zarr"):
                zarrFile = zarr.open(self.fullPath, mode='r')
                data = zarrFile[:]
            else:
                raise ValueError(f"Unsupported file format: {self.fullPath}")

            self.sigFileLoaded.emit(data, self.fullPath)

        except Exception as e:
            self.error.emit(str(e))