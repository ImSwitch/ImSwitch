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
            numTimepoints: int = 1
    ):
        super().__init__()
        self.savePath = savePath 
        self.numTimepoints = numTimepoints
        self.numRows = numRows 
        self.numCols = numCols 
        self.zarrArray = None

    
    @QtCore.Slot()
    def run(self): 
        shape = (self.numTimepoints, 1, self.numRows, self.numCols)
        chunks = (1, 1, self.numRows, self.numCols)        
        try:
            zarrStore = zarr.DirectoryStore(self.savePath)
            self.zarrArray = zarr.open(
                zarrStore, 
                mode='w',
                shape=shape, 
                chunks=chunks,
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
        """ ... """
        print("DEBUG [ZarrSaveWorker] [saveRecImage] >> We've enterd the saveRecImage method")
        if self.zarrArray is not None: 
            # C pointer arithmetic under the hood: *timePointView = procChunksCoeffs => RAM[addressTozarrArray] = procChunkCoeffs
            if timePointIndex >= self.zarrArray.shape[0]:
                newShape = (timePointIndex + 1, 1, self.numRows, self.numCols)
                self.zarrArray.resize(newShape)
            self.zarrArray[timePointIndex, 0] = recImage