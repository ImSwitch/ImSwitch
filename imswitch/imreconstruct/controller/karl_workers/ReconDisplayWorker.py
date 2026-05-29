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
        self.num_timepoints = dispArr.shape[2]
        self.reconBuffer = reconBuffer
        self.imgCounter = 1

    @QtCore.Slot()
    def addReconImgToDisplay(self):
        # D B T Z Y X
        # 0 1 2 3 4 5
        if self.imgCounter < self.num_timepoints: 
            self.reconBuffer[0, 0, self.imgCounter, 0] = self.reconBuffer[0, 0, 0, 0]           
            self.imgCounter += 1
