# type: ignore 

import os 
import time 
import zarr 
import numpy as np 
from qtpy import QtCore 

class ZarrStreamWorker(QtCore.QObject):
    """
    Specialized worker for imreconstruct: Monitor a growing Zarr store.
    An instance of this class should mimic the FileLoaderWorker's output to stay 
    compatible with the existing reconstruction pipeline.
    """
    # emits (data_chunk, virtual_filename)
    sigChunkLoaded = QtCore.Signal(np.ndarray, str)
    sigFinished = QtCore.Signal()

    def __init__(
            self, 
            zarr_path: str,
            frames_per_chunk: int = 1
    ) -> None: 
        super().__init__()
        self.path = zarr_path
        self.frames_per_chunk = 1
        self.running = False

    @QtCore.Slot()
    def run(self) -> None: 
        self.running = True
        last_index = 0

        array_path = os.path.join(self.path, "chunks")
        
        print(f"Zarr Worker waiting for data in {self.path}")

        if not os.path.exists(self.path):
            print(f"WORKER ERROR: Path {self.path} does not exist.")
            self.sigFinished.emit()
            return 

        while self.running: 
            try: 
                meta_path = os.path.join(array_path, ".zarray")
                if not os.path.exists(meta_path): 
                    print(f"DEBUG: meta_path does not exist!")
                    time.sleep(0.5)
                    continue
            
                z = zarr.open(array_path, mode='r')
                z._refresh_metadata()
    
                # print(f"DEBUG: Zarr shape: {z.shape}. Target Chunk: {self.frames_per_chunk}")

                current_size = z.shape[0]
                available = current_size - last_index 

                # if a full chunk is ready, then fetch it
                if available >= self.frames_per_chunk: 
                    data = z[last_index : last_index + self.frames_per_chunk]
                    # emit a 'filename' string so WatcherFrameController.onFileLoaded can
                    # log (display) on which part of the stream we are currently on
                    virtual_name = f"{os.path.basename(self.path)}_index_{last_index}"
                    self.sigChunkLoaded.emit(data, virtual_name)
                    last_index += self.frames_per_chunk
                else: 
                    # wait for writer to catch up
                    # TODO: replace with something that is more robust
                    time.sleep(0.1) 
                
                is_writing = z.attrs.get("writing", True)
                if not is_writing and last_index >= current_size:
                    self.running = False


            except Exception as e: 
                print(f"WORKER Exception: {e}")
                # if we end up here it's typically due to the writer currently locking the 
                # metadata file 
                # TODO: replace with something that is more robust
                time.sleep(0.5)
        
        self.sigFinished.emit()
    
    def stop(self): 
        self.running = False