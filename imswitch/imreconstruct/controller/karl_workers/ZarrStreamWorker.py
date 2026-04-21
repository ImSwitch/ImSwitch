# type: ignore 

import os 
import zarr 
import numpy as np 
from qtpy import QtCore 
from typing import Union

class ZarrStreamWorker(QtCore.QObject):
    """
    Specialized worker for imreconstruct: Monitor a growing Zarr store.
    An instance of this class should mimic the FileLoaderWorker's output to stay 
    compatible with the existing reconstruction pipeline.
    """
    sigChunkLoaded = QtCore.Signal(np.ndarray) # (chunk)
    sigFinished = QtCore.Signal()

    def __init__(
            self, 
            zarrFilePath: str,
            numFramesInStack: int,
            numFramesInChunk: int = 1
    ) -> None: 
        super().__init__()
        self.zarrFilePath = zarrFilePath
        self.numFramesInStack = numFramesInStack
        self.numFramesInChunk = numFramesInChunk
        self.zarrArrayPath = None
        self.numFramesProcessed = 0
        self.running = False


    def _findArrayPath(self) -> Union[str, None]:
        """ Find the first subdirectory containing a .zarray file. """
        # check if the root (zarrFilePath) is a .zarray itself
        if os.path.exists(os.path.join(self.zarrFilePath, ".zarray")):
            return self.zarrFilePath

        # check if the root (zarrFilePath) contains a directory with a .zarray
        if os.path.isdir(self.zarrFilePath):
            for entry in os.listdir(self.zarrFilePath):
                subPath = os.path.join(self.zarrFilePath, entry)
                if os.path.isdir(subPath) and os.path.exists(os.path.join(subPath, ".zarray")):
                    return subPath
                
        return None


    @QtCore.Slot()
    def run(self) -> None: 
        self.running = True
        while self.running and self.zarrArrayPath is None:
            self.zarrArrayPath = self._findArrayPath()
            if self.zarrArrayPath is None: 
                QtCore.QThread.msleep(50) 

        if not self.running:
            self.sigFinished.emit()
            return

        try: 
            # --- INITAL LOOP ---
            zarrArray = None
            while self.running and zarrArray is None: 
                try:
                    zarrArray = zarr.open(self.zarrArrayPath, mode='r')
                except Exception as e:
                    print(f"[ZarrStreamWorker] [run] >> {e}") 
                    QtCore.QThread.msleep(100)
            
            if not self.running:
                return

            # --- MAIN LOOP --- 
            while self.running:
                if self.numFramesProcessed >= self.numFramesInStack - 1:
                    # all frames in the stack have been processed => break loop
                    break
                
                try: 
                    zarrArray.store.close()
                    zarrArray = zarr.open(self.zarrArrayPath, mode='r')
                    isWriting = zarrArray.attrs.get("writing", False)
                    currentNumFrames = zarrArray.shape[0] - 1     
                    while not isWriting and self.numFramesInChunk <= currentNumFrames - self.numFramesProcessed:                
                        startIndex = self.numFramesProcessed
                        endIndex = startIndex + self.numFramesInChunk
                        
                        dataToProcess = zarrArray[startIndex:endIndex]
                        if dataToProcess.size > 0: 
                            self.sigChunkLoaded.emit(dataToProcess)
                            self.numFramesProcessed += self.numFramesInChunk

                        if not self.running: 
                            break

                except Exception as e:
                    # if we get [Errno13] Permission denied loop again
                    pass
                     
        except Exception as e:
            print(f"ERROR [ZarrStreamWorker] [run] >> {e}")
        
        finally:
            self.running = False
            try: 
                # check if zarrSteamWorker/Thread-object in WatcherFrameController is alive before emitting 
                self.sigFinished.emit()
            except RuntimeError:
                # object has already been deleted => nothing to emit a signal to
                pass


    def stop(self): 
        self.running = False
