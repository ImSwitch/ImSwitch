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
        self.imgCounter = 1


    @QtCore.Slot()
    def addReconImgToDisplay(self):
        # D B T Z Y X
        # 0 1 2 3 4 5
        shape = self.dispArr.shape
        z_shape = shape[3]
        t_shape = shape[2]
        
        if self.imgCounter >= t_shape: 
            self.dispArr[0, 0, t_shape - 1, 0] = self.reconBuffer[0, 0, 0, 0]           
            self.dispArr = np.resize(self.dispArr, (*shape[:2], t_shape + 1, *shape[3:]))
            self.imgCounter += 1
            print(f"[ReconDisplayWorker] [addReconImgToDisplay] >> imgCounter = {self.imgCounter}")