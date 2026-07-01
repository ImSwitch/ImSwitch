# type: ignore 

import zarr 
import numpy as np
import os
from qtpy import QtCore
from typing import Union



class ZarrStreamWorker(QtCore.QObject):
    
    """ Extracts and stores raw data in a buffer which the ProcessorWorker can access and process. """
   
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
        self.num_time_points_proc = 0

    @QtCore.Slot(str)
    def run(self, path: str):
        if not self.running:
            return

        z_arr = None 
        num_frames_proc = 0

        while self.running: 
            try: 
                if z_arr is not None: 
                    z_arr.store.close()
                z_arr_path = self._find_zarr_array(path)
                 
                z_arr = zarr.open(z_arr_path, mode='r')

                curr_num_frames = z_arr.shape[0]
                num_frames_in_chunk = z_arr.chunks[0] 

                while num_frames_in_chunk <= curr_num_frames - num_frames_proc:
                    start = num_frames_proc
                    end = start + num_frames_in_chunk
                    chunk = z_arr[start:end]
                    if chunk.size > 0: 
                        self.raw_data[start:end, :, :] = chunk
                        self._commChannel.sigLiveChunkReady.emit(start, end)
                        num_frames_proc += num_frames_in_chunk 

                if num_frames_proc >= self.num_frame_in_stack - 1: 
                    self.num_time_points_proc += 1 
                    break
                
                QtCore.QThread.msleep(100)  
            
            except Exception as e:
                # Errno 13 => windows file locking retry
                QtCore.QThread.msleep(100)
                pass

    def stop(self): 
        self.running = False
        self.num_time_points_proc = 0

    @QtCore.Slot(int)
    def decrement_num_timepoints(self, dec_val: int): 
        self.num_time_points -= dec_val

    def _find_zarr_array(self, zarr_path: str) -> Union[str, None]:
        for f in os.listdir(zarr_path):
            f_abs = os.path.join(zarr_path, f)
            if os.path.isdir(f_abs):
                d_abs = os.path.join(zarr_path, f)
                for ff in os.listdir(d_abs):
                    if ff.lower().endswith(".zarray"):
                        return d_abs
            elif f.lower().endswith(".zarray"):
                return zarr_path
        return None
