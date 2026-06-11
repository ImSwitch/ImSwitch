# type: ignore 

import zarr 
import numpy as np 

from qtpy import QtCore 

class ZarrStreamWorker(QtCore.QObject):
    
    """
    ... 
    """
   
    sigChunkLoaded = QtCore.Signal(np.ndarray) 
    sigZarrFileFinished = QtCore.Signal()
    sigFinishedDirectory = QtCore.Signal()

    def __init__(
            self,
            num_time_points: int,  
            num_frames_in_stack: int,
            raw_data: np.ndarray,
            _commChannel: object
    ): 
        super().__init__()
        self.num_time_points = num_time_points
        self.num_frame_in_stack = num_frames_in_stack
        self.raw_data = raw_data
        self._commChannel = _commChannel
        self.running = True
        self.num_timepoints_proc = 0


    @QtCore.Slot(str)
    def run(self, path: str):
        if not self.running:
            return
            
        try: 
            z_arr = zarr.open(path, mode='r') 
            curr_num_frames = z_arr.shape[0] 
            num_frames_in_chunk = z_arr.chunks[0]      

            num_frames_processed = 0

            while num_frames_in_chunk <= curr_num_frames - num_frames_processed:                
                start = num_frames_processed
                end = start + num_frames_in_chunk
                chunk = z_arr[start:end]  
                
                if chunk.size > 0:
                    self.raw_data[start:end, :, :] = chunk
                    self._commChannel.sigLiveChunkReady.emit(start, end)
                    num_frames_processed += num_frames_in_chunk 
            print(f"num_frames_processed = {num_frames_processed}")
            print(f"end = {end}") 
            if num_frames_processed >= self.num_frame_in_stack:
                self.num_time_points += 1 
                if self.num_timepoints_proc >= self.num_time_points:
                    self.sigFinishedDirectory.emit()
                else: 
                    print(f"path = {path}")
                    self.sigZarrFileFinished.emit()

        except Exception as e:
            # [Errno13] File being written to => loop again
            # TODO: find a better way to check if the file is being written to or not  
            pass
                              
    def stop(self): 
        self.running = False

