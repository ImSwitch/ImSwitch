# type: ignore

from qtpy import QtCore
import numpy as np


class ProcessorWorker(QtCore.QObject): 
    
    """
    ... 
    """

    sigTriggerUIRefresh = QtCore.Signal()
    sigSaveChunk = QtCore.Signal(np.ndarray, np.ndarray, int)
    sigMoveTimeSlider = QtCore.Signal(int)    
    sigProcessingFinished = QtCore.Signal()

    def __init__(
            self,
            processor: object, 
            raw_data: np.ndarray,
            recon_obj: object, 
            _commChannel: object, 
            cupy_available: bool = False
    ):
        super().__init__()
        self.processor = processor
        self.raw_data = raw_data
        self.recon_obj = recon_obj
        self._commChannel = _commChannel
        self.refresh_rate = int(np.sqrt(len(self.processor.frame_inds)))
        self.timepoint = 0        
        self.cp = None
        if cupy_available: 
            try:
                import cupy as cp
                self.cp = cp
            except ImportError:
                print("ERROR [ProcessorWorker] [__init__] >> Error when trying to import CuPy")
                return

    @QtCore.Slot(int, int)
    def processChunk(self, start, end):        
        if QtCore.QThread.currentThread().isInterruptionRequested():
            # thread closing => exit processing 
            return
        
        chunk = self.raw_data[start:end] 
        if self.cp != None:
            chunk = self.cp.asarray(chunk)
        proc_pixels = self.processor.process_chunk(chunk)
        pixel_indices = self.processor.frame_inds[start:end]
        flat_recon = self.recon_obj.reconstructed[0, 0, self.timepoint, 0].reshape(-1)
        flat_recon[pixel_indices.ravel()] = proc_pixels.ravel()
       
        # if end % self.refresh_rate == 0:
            # self.sigTriggerUIRefresh.emit()
        
        if end >= self.processor.num_frames_in_stack: 
            self.sigMoveTimeSlider.emit(self.timepoint)
            self.sigTriggerUIRefresh.emit()
            self._commChannel.sigProcessingFinished.emit()   
            self.timepoint += 1 

    @QtCore.Slot(int)
    def inc_timepoint(self, inc_val: int):
        self.timepoint += inc_val 