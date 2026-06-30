# type: ignore 


import tifffile as tiff
import numpy as np 
import os
from qtpy import QtCore


class SaveWorker(QtCore.QObject): 
    """
    ...
    """ 

    sigSaveReconTimepoint = QtCore.Signal(np.ndarray, int) 

    def __init__(self, save_path: str, directory_name: str):
        super().__init__()
        self.save_path = save_path
        self.directory_name = directory_name

    def save_recon_timepoint(self, recon_data: np.ndarray, timepoint: int):
        path = os.path.join(self.save_path, f"{self.directory_name}_t{timepoint}.tiff")
        tiff.imwrite(path, recon_data)