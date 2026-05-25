# type: ignore 

from imswitch.imcommon.model import initLogger
from imswitch.imreconstruct.controller.karl_workers.ZarrWorkerUtils import findZarrArrayPath

import zarr 
import numpy as np 

from qtpy import QtCore 


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
        self._logger = initLogger(self)


    @QtCore.Slot(str)
    def streamZarrFile(self, zarrFilePath: str):
        numFramesProcessed = 0 
        zarrArrayPath = None
        zarrArray = None

        while self.running and zarrArrayPath is None and zarrArray is None: 
            try:
                zarrArrayPath = findZarrArrayPath(zarrFilePath)
                zarrArray = zarr.open(zarrArrayPath, mode='r')
            except: 
                QtCore.QThread().msleep(100)

        while self.running: 
            if numFramesProcessed >= self.numFramesInStack - 1:
                self.sigZarrFileFinished.emit()
                break

            try: 
                if zarrArray is not None:
                    zarrArray.store.close()
                
                zarrArray = zarr.open(zarrArrayPath, mode='r')
                
                currentNumFrames = zarrArray.shape[0] - 1
                numFramesInChunk = zarrArray.chunks[0]     
                
                while numFramesInChunk <= currentNumFrames - numFramesProcessed:                
                    startChunkIndex = numFramesProcessed
                    endChunkIndex = startChunkIndex + numFramesInChunk
                    chunkToProcess = zarrArray[startChunkIndex:endChunkIndex]
                    
                    if chunkToProcess.size > 0: 
                        self.rawDataBuffer[startChunkIndex:endChunkIndex, :, :] = chunkToProcess
                        self._commChannel.sigLiveChunkReady.emit(startChunkIndex, endChunkIndex)
                        numFramesProcessed += numFramesInChunk
                    
                    if not self.running: 
                        break

            except Exception:
                # [Errno13] Permission Denied (writing) => loop again
                QtCore.QThread().msleep(10)
                pass
                             
                             
    def stop(self): 
        self.running = False
