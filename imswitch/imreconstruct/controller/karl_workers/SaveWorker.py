# type: ignore 


import tifffile as tiff
import numpy as np 
from qtpy import QtCore


class SaveWorker(QtCore.QObject): 
    
    """ Saves reconstructions of a timelapse folder as a single .tiff file with shape (T, Y, X). """ 

    def __init__(self, save_path: str, recon_data: np.ndarray):
        super().__init__()
        self.save_path = save_path
        self.recon_data = recon_data

    @QtCore.Slot()
    def save_recons(self):
        tiff.imwrite(self.save_path + ".tiff", self.recon_data)