# type: ignore

from qtpy import QtCore
from tifffile import imwrite
import numpy as np
import os

class SaveWorker(QtCore.QObject):
    
    def __init__(
            self, 
            savePath: str,
            recImageBuffer: np.ndarray,  
    ):
        super().__init__()
        self.recImageBuffer = recImageBuffer
        self.savePath = savePath
        # create directory for the reconstructed timepoint images 
        try: 
            os.mkdir(self.savePath)
            print(f"DEBUG [SaveWorker] [__init__] >> Directory {self.savePath} has successfully been created")
        except Exception as e:
            print(f"ERROR [SaveWorker] [__init__] >> An error occured when trying to create the directory {self.savePath}: {e}")              

    @QtCore.Slot(int)
    def saveRecImage(self, timePointIndex: int):
        filePathName = os.path.join(self.savePath, "recImage_timepoint_" + str(timePointIndex) + "_.tiff") 
        imwrite(filePathName, self.recImageBuffer)
