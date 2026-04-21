# type: ignore 

import os 
import zarr 
import numpy as np 
from qtpy import QtCore 
from typing import Union

class ZarrStreamWorker(QtCore.QObject):
    """
    Specialized worker for imreconstruct: Monitor a growing Zarr store.
    An instance of this class should mimic the FileLoaderWorker's output to stay 
    compatible with the existing reconstruction pipeline.
    """
    sigChunkLoaded = QtCore.Signal(np.ndarray, str) # (chunk, fileNameToWhichChunkBelong)
    sigFinished = QtCore.Signal()

    def __init__(
            self, 
            zarrFilePath: str,
            numFramesInStack: int,
            numFramesInChunk: int = 1
    ) -> None: 
        super().__init__()
        self.zarrFilePath = zarrFilePath
        self.numFramesInStack = numFramesInStack
        self.numFramesInChunk = numFramesInChunk
        self.zarrArrayPath = None
        self.numFramesProcessed = 0
        self.running = False


    def _findArrayPath(self) -> Union[str, None]:
        """ Find the first subdirectory containing a .zarray file. """
        # check if the root (zarrFilePath) is a .zarray itself
        if os.path.exists(os.path.join(self.zarrFilePath, ".zarray")):
            return self.zarrFilePath

        # check if the root (zarrFilePath) contains a directory with a .zarray
        if os.path.isdir(self.zarrFilePath):
            for entry in os.listdir(self.zarrFilePath):
                subPath = os.path.join(self.zarrFilePath, entry)
                if os.path.isdir(subPath) and os.path.exists(os.path.join(subPath, ".zarray")):
                    return subPath
                
        return None


    @QtCore.Slot()
    def run(self) -> None: 
        self.running = True
        
        while self.running and self.zarrArrayPath is None:
            self.zarrArrayPath = self._findArrayPath()
            if self.zarrArrayPath is None: 
                QtCore.QThread.msleep(50) # qt 50 ms sleep (prevent CPU spike)

        if not self.running:
            self.sigFinished.emit()
            return

        try: 
            zarrArray = zarr.open(self.zarrArrayPath, mode='r')
            while self.running:
                if self.numFramesProcessed >= self.numFramesInStack - 1:
                    # all frames in the stack have been processed => break loop
                    break

                zarrArray.store.close()
                zarrArray = zarr.open(self.zarrArrayPath, mode='r')
                
                currentNumFrames = zarrArray.shape[0] - 1     
                if currentNumFrames >= self.numFramesProcessed + self.numFramesInChunk:
                    startIndex = self.numFramesProcessed
                    endIndex = startIndex + self.numFramesInChunk
                    dataToProcess = zarrArray[startIndex:endIndex]
                
                    if dataToProcess.size > 0: 
                        self.sigChunkLoaded.emit(dataToProcess, self.zarrFilePath)
                        self.numFramesProcessed += self.numFramesInChunk
                
                else:
                    # no data => sleep
                    QtCore.QThread.msleep(1) # qt 1 ms sleep (prevent CPU spike)
                
                # QtCore.QThread.msleep(1) # uncomment if CPU issues arise
                    

        except Exception as e:
            print(f"ERROR [ZarrStreamWorker] [run] >> {e}")
        
        finally:
            self.running = False
            self.sigFinished.emit()


    def stop(self): 
        self.running = False
