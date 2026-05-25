# type: ignore

from qtpy import QtCore
import numpy as np


class ProcessorWorker(QtCore.QObject): 
    
    numFramesProcessed = QtCore.Signal(int)       
    sigTriggerUIRefresh = QtCore.Signal()
    sigSaveChunk = QtCore.Signal(np.ndarray, np.ndarray, int)
    sigAddReconImgToDisplay = QtCore.Signal()    
    
    def __init__(
            self,
            processor, 
            reconObj, 
            rawDataBuffer,
            cupyAvailable = False,
            _commChannel = None
    ):
        super().__init__()
        self.processor = processor
        self.reconObj = reconObj
        self.rawDataBuffer = rawDataBuffer        
        
        self.cupyAvailable = cupyAvailable
        self.cp = None
        if self.cupyAvailable:
            try:
                import cupy as cp
                self.cp = cp
            except ImportError:
                print("WARNING [ProcessorWorker] [__init__] >> Error when trying to import CuPy")
                return

        self._commChannel = _commChannel


    @QtCore.Slot(int, int)
    def processChunk(self, start, end):        
        if QtCore.QThread.currentThread().isInterruptionRequested():
            # thread closing => exit processing 
            return
        
        chunk = self.rawDataBuffer[start:end]
        
        if self.cupyAvailable and self.cp:
            chunk = self.cp.asarray(chunk)
        
        chunkCoeffs = self.processor.process_chunk(chunk)
        chunkIndices = self.processor.frame_inds[start:end]
        
        self.reconObj.addLiveChunk(chunkCoeffs, chunkIndices)

        self.numFramesProcessed.emit(end)

        if end >= self.processor.num_frames_in_stack - 1: 
            self.sigTriggerUIRefresh.emit()
            self.sigAddReconImgToDisplay.emit()
            