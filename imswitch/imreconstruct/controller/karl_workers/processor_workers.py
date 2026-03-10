# type: ignore

from qtpy import QtCore


class ProcessorWorker(QtCore.QObject): 
    
    numFramesProcessed = QtCore.Signal(int)       
    sigStackFinished = QtCore.Signal()

    def __init__(
            self,
            processor, 
            reconObj, 
            buffer,
            cupyAvailable = False
    ):
        super().__init__()
        self.processor = processor
        self.reconObj = reconObj
        self.buffer = buffer

        self.cupyAvailable = cupyAvailable
        self.cp = None
        if self.cupyAvailable:
            try:
                import cupy as cp
                self.cp = cp
            except ImportError:
                print("Warning: GPU requested, but CuPy not found.")

    @QtCore.Slot(int)
    def process_frame(self, frameIndex): 
        frame = self.buffer[frameIndex]
        if self.cupyAvailable and self.cp: 
            frame = self.cp.asarray(frame)             

        coeffs = self.processor.process_frame(frame)
        frame_indices = self.processor.frame_inds[frameIndex]
        self.reconObj.addLiveFrame(coeffs, frame_indices)
    
        if frameIndex == self.processor.num_frames_in_stack - 1:
            self.sigStackFinished.emit()
            
        self.numFramesProcessed.emit(frameIndex)