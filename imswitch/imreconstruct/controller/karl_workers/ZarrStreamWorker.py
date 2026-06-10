# type: ignore 

import zarr 
import numpy as np 

import os 

from qtpy import QtCore 
from typing import Union

class ZarrStreamWorker(QtCore.QObject):
    
    """
    ... 
    """
   
    sigChunkLoaded = QtCore.Signal(np.ndarray) 
    sigZarrFileFinished = QtCore.Signal()

    def __init__(
            self, 
            num_frames_in_stack: int,
            raw_data: np.ndarray,
            _commChannel: object
    ): 
        super().__init__()
        self.num_frame_in_stack = num_frames_in_stack
        self.raw_data = raw_data
        self._commChannel = _commChannel
        self.running = True

    @QtCore.Slot(str)
    def run(self, path: str):
        z_arr = None
        num_frames_processed = 0 
        while self.running: 
            try: 
                if num_frames_processed >= self.num_frame_in_stack - 1:
                    self.sigZarrFileFinished.emit()
                    break     
                
                if z_arr != None:
                    z_arr.store.close()
                
                z_arr = zarr.open(path, mode='r') 
                curr_num_frames = z_arr.shape[0] 
                num_frames_in_chunk = z_arr.chunks[0]      
                
                while num_frames_in_chunk <= curr_num_frames - num_frames_processed:                
                    start = num_frames_processed
                    end = start + num_frames_in_chunk
                    chunk = z_arr[start:end]  
                    self.raw_data[start:end, :, :] = chunk
                    self._commChannel.sigLiveChunkReady.emit(start, end)
                    num_frames_processed += num_frames_in_chunk 

            except Exception:
                # [Errno13] File being written to => loop again
                # TODO: find a better way to check if the file is being written to or not  
                QtCore.QThread.msleep(10)
                pass
                              
    def stop(self): 
        self.running = False