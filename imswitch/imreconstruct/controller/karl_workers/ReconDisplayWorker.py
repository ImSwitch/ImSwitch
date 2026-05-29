import numpy as np 
from qtpy import QtCore


class ReconDisplayWorker(QtCore.QObject):

    def __init__(
            self, 
            dispArr: object,
            reconBuffer: np.ndarray,
            parent=None,
    ):
        super().__init__(parent)
        self.dispArr = dispArr
        self.reconBuffer = reconBuffer
        self.imgCounter = 0

    @QtCore.Slot()
    def addReconImgToDisplay(self):
        # D B T Z Y X
        # 0 1 2 3 4 5
        num_timepoints = self.dispArr.shape[2]        
        if self.imgCounter <= num_timepoints: 
            self.dispArr[0, 0, self.imgCounter, 0, :, :] = self.reconBuffer[0, 0, 0, 0, :, :]           
            self.imgCounter += 1
