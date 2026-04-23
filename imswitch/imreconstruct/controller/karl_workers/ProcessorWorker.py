# type: ignore

from qtpy import QtCore
import numpy as np


class ProcessorWorker(QtCore.QObject): 
    
    numFramesProcessed = QtCore.Signal(int)       
    sigTriggerUIRefresh = QtCore.Signal()
    sigSaveChunk = QtCore.Signal(np.ndarray, np.ndarray, int)

    def __init__(
            self,
            processor, 
            reconObj, 
            buffer,
            cupyAvailable = False,
            _commChannel = None
    ):
        super().__init__()
        self._commChannel = _commChannel
        self.processor = processor
        self.reconObj = reconObj
        self.recImageBuffer = buffer
        self.timePointIndex = 0
        self.cupyAvailable = cupyAvailable
        self.cp = None
        if self.cupyAvailable:
            try:
                import cupy as cp
                self.cp = cp
            except ImportError:
                print("WARNING [ProcessorWorker] [__init__] >> GPU requested but CuPy not found => Defaulting to CPU processing")


    @QtCore.Slot(int)
    def process_frame(self, frameIndex): 
        frame = self.recImageBuffer[frameIndex]
        if self.cupyAvailable and self.cp: 
            frame = self.cp.asarray(frame)             

        coeffs = self.processor.process_frame(frame)
        frame_indices = self.processor.frame_inds[frameIndex]
        self.reconObj.addLiveFrame(coeffs, frame_indices)
        
        refreshRate = int(np.sqrt(len(frame_indices)))
        if frameIndex % refreshRate == 0 or frameIndex == self.processor.num_frames_in_stack - 1: 
            self.sigTriggerUIRefresh.emit()
            
        self.numFramesProcessed.emit(frameIndex)


    @QtCore.Slot(int, int)
    def process_chunk(self, startChunkIndex, endChunkIndex):        
        chunk = self.recImageBuffer[startChunkIndex:endChunkIndex]
        if self.cupyAvailable and self.cp:
            chunk = self.cp.asarray(chunk)
        
        chunkCoeffs = self.processor.process_chunk(chunk)
        chunkIndices = self.processor.frame_inds[startChunkIndex:endChunkIndex]
        
        self.reconObj.addLiveChunk(chunkCoeffs, chunkIndices)
        numFrames = endChunkIndex 
        self.numFramesProcessed.emit(numFrames)

        refreshRate = int(np.sqrt(chunkIndices.shape[1]))
        if numFrames % refreshRate == 0:
            self.sigTriggerUIRefresh.emit()

        if numFrames == self.processor.num_frames_in_stack - 1: 
            self.sigTriggerUIRefresh.emit()
            # --- SAVING RECONSTRUCTED DATA ---
            data = self.reconObj.reconstructed[0, 0, 0, 0]
            self._commChannel.sigSaveRecImage.emit(data, self.timePointIndex)
            self.timePointIndex += 1 