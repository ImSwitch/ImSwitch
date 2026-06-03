# type: ignore

from qtpy import QtCore
import numpy as np


class ProcessorWorker(QtCore.QObject): 
    
    # numFramesProcessed = QtCore.Signal(int)        
    sigTriggerUIRefresh = QtCore.Signal()
    sigSaveChunk = QtCore.Signal(np.ndarray, np.ndarray, int)
    sigMoveTimeSlider = QtCore.Signal(int)    
    
    def __init__(
            self,
            processor, 
            rawData,
            reconObj, 
            cupyAvailable = False
    ):
        super().__init__()
        self.processor = processor
        self.rawData = rawData
        self.reconObj = reconObj
        
        self.updateRate = int(np.sqrt(len(self.processor.frame_inds)))
        self.timeIndex = 0        
        
        self.cp = None
        if cupyAvailable:
            try:
                import cupy as cp
                self.cp = cp
            except ImportError:
                print("WARNING [ProcessorWorker] [__init__] >> Error when trying to import CuPy")
                return

    @QtCore.Slot(int, int)
    def processChunk(self, start, end):        
        if QtCore.QThread.currentThread().isInterruptionRequested():
            # thread closing => exit processing 
            return
        
        # fetch raw data
        chunk = self.rawData[start:end]
        
        # process raw data
        if self.cp is not None:
            chunk = self.cp.asarray(chunk)
        procPixels = self.processor.process_chunk(chunk)
        pixelIndices = self.processor.frame_inds[start:end]

        # insert processed data into reconObj 
        flatReconView = self.reconObj.reconstructed[0, 0, self.timeIndex, 0].reshape(-1)
        flatReconView[pixelIndices.ravel()] = procPixels.ravel()
    
        # update view 
    
        # if end % self.updateRate == 0:
        #     self.sigTriggerUIRefresh.emit()

        if end >= self.processor.num_frames_in_stack - 1: 
            self.sigTriggerUIRefresh.emit()
            self.sigMoveTimeSlider.emit(self.timeIndex)
            self.timeIndex += 1 
