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
    sigChunkLoaded = QtCore.Signal(np.ndarray) # (chunk)
    sigZarrFileFinished = QtCore.Signal()

    def __init__(
            self, 
            numFramesInStack: int,
            rawDataBuffer: np.ndarray,
            _commChannel: object
    ): 
        super().__init__()
        self.numFramesInStack = numFramesInStack
        self.rawDataBuffer = rawDataBuffer
        self._commChannel = _commChannel
        self.running = True


    def _findArrayPath(self, zarrFilePath: str) -> Union[str, None]:
        """ Find the first subdirectory containing a .zarray file. """
        # check if the root (zarrFilePath) is a .zarray itself
        if os.path.exists(os.path.join(zarrFilePath, ".zarray")):
            return zarrFilePath

        # check if the root (zarrFilePath) contains a directory with a .zarray
        if os.path.isdir(zarrFilePath):
            for entry in os.listdir(zarrFilePath):
                subPath = os.path.join(zarrFilePath, entry)
                if os.path.isdir(subPath) and os.path.exists(os.path.join(subPath, ".zarray")):
                    return subPath
                
        return None


    @QtCore.Slot(str)
    def streamZarrFile(self, zarrFilePath: str):
        """ Called everytime WatcherFrameController.runNextFile pops a file from the queue. """
        numFramesProcessed = 0 
        zarrArrayPath = None
        zarrArray = None

        while self.running and zarrArrayPath is None and zarrArray is None: 
            try:
                zarrArrayPath = self._findArrayPath(zarrFilePath)
                zarrArray = zarr.open(zarrArrayPath, mode='r')
            except Exception as e: 
                # print(f"[ZarrStreamWorker] [run] Error when trying to open first Zarr file {e}")
                QtCore.QThread.msleep(100)

        while self.running: 
            if numFramesProcessed >= self.numFramesInStack - 1:
                self.sigZarrFileFinished.emit()
                break

            try: 
                if zarrArray is not None:
                    zarrArray.store.close()
                
                zarrArray = zarr.open(zarrArrayPath, mode='r')
                isWriting = zarrArray.attrs.get("writing", False)
                currentNumFrames = zarrArray.shape[0] - 1
                numFramesInChunk = zarrArray.chunks[0]     
                
                while not isWriting and numFramesInChunk <= currentNumFrames - numFramesProcessed:                
                    startChunkIndex = numFramesProcessed
                    endChunkIndex = startChunkIndex + numFramesInChunk
                    chunkToProcess = zarrArray[startChunkIndex:endChunkIndex]
                    
                    if chunkToProcess.size > 0: 
                        self.rawDataBuffer[startChunkIndex:endChunkIndex, :, :] = chunkToProcess
                        self._commChannel.sigLiveChunkReady.emit(startChunkIndex, endChunkIndex)
                        numFramesProcessed += numFramesInChunk
                    
                    if not self.running: 
                        break

            except RuntimeError:
                # [Errno13] Permission Denied => loop again
                pass
                
            except Exception as e:
                # print(f"[ZarrStreamWorker] [run] Error in streaming loop: {e}")
                pass
                             
                             
    def stop(self): 
        self.running = False
