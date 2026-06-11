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
                z_arr = zarr.open(path, mode='r')

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
                    if self.num_time_points_proc >= self.num_time_points:
                        print(f"[ZarrStreamWorker] [run] >> Completed all timepoints => Folder Done")
                    else: 
                        print(f"[ZarrStreamWorker] [run] >> File completed => going to next file")
                    break
                
                QtCore.QThread.msleep(100)  
            
            except Exception as e:
                # Errno 13 => windows file locking retry
                print(f"[ZarrStreamWorker] [run] >> {e}") 
                QtCore.QThread.msleep(50)
                pass

    def stop(self): 
        self.running = False
        self.num_time_points_proc = 0
