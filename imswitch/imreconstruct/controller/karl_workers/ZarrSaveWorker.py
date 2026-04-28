# type: ignore

from qtpy import QtCore
import zarr
import numpy as np


class ZarrSaveWorker(QtCore.QObject):
    
    sigFinished = QtCore.Signal()

    def __init__(
            self, 
            savePath: str,  
            numRows: int, 
            numCols: int,
    ):
        super().__init__()
        self.savePath = savePath 
        self.numRows = numRows 
        self.numCols = numCols 
        self.zarrArray = None

    
    @QtCore.Slot()
    def run(self):    
        try:
            zarrStore = zarr.DirectoryStore(self.savePath)
            self.zarrArray = zarr.open(
                zarrStore, 
                mode='w',
                shape=(1, 1, self.numRows, self.numCols), 
                chunks=(1, 1, self.numRows, self.numCols),
                dtype=np.float32
            )
            self.zarrArray.attrs["description"] = "Reconstructed stacks (timepoints) from Zarr Live Stream"
        except Exception as e:
            print(f"[ZarrSaveWorker] [run] >> Error initializing zarrSaveWorker {e}")


    @QtCore.Slot(np.ndarray, int)
    def saveRecImage(
            self, 
            recImage: np.ndarray, 
            timePointIndex: int
    ):
        """ Saves reconstructed timepoints as chunks in a zarr file """
        if self.zarrArray is not None: 
            if timePointIndex >= self.zarrArray.shape[0]:
                self.zarrArray.resize((timePointIndex + 1, 1, self.numRows, self.numCols))
            self.zarrArray[timePointIndex, 0] = recImage