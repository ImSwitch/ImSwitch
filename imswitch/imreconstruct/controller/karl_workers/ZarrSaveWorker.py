from qtpy import QtCore
import zarr
import numpy as np


class ZarrSaveWorker(QtCore.QtObject):
    
    sigFinished = QtCore.Signal()

    def __init__(
            self, 
            savePath, 
            numTimepoints, 
            numRows, 
            numCols
    ):
        super().__init__()
        self.savePath = savePath 
        self.numTimepoints = numTimepoints
        self.numRows = numRows 
        self.numCols = numCols 
        self.zarrArray = None

    
    @QtCore.Slot()
    def run(self): 
        # (T, Z, Y, X) = (numTimepoints, 1, numRows, numCols)
        shape = (self.numTimepoints, 1, self.numRows, self.numCols)
        # 1 timepoint = 1 chunk => chunk.shape = (T, Z, Y, X)
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

    @QtCore.Slot(np.ndarray, np.ndarray, int)
    def processedChunk(
            self, 
            procChunkCoeffs, 
            chunkIndices, 
            timePointIndex
    ):
        """ ... """
        if self.zarrArray is not None: 
            # C pointer arithmetic under the hood: *timePointView = procChunksCoeffs => RAM[addressTozarrArray] = procChunkCoeffs
            timePointView = self.zarrArray[timePointIndex, 0].view().reshape(-1)
            timePointView[chunkIndices.ravel()] = procChunkCoeffs.ravel()