import ctypes
import os
import sys
import time

import numpy as np

import constants


class SignalExtractor:
    """ This class takes the raw data together with pre-set
    parameters and recontructs and stores the final images (for the different
    bases).
    """

    def __init__(self):
        # TODO: Support non-Windows OS
        # This is needed by the DLL containing CUDA code.
        # ctypes.cdll.LoadLibrary(os.environ['CUDA_PATH_V9_0'] + '\\bin\\cudart64_90.dll')
        ctypes.cdll.LoadLibrary(
            os.path.join(constants.rootFolderPath, 'libs/cudart64_90.dll')
        )
        self.ReconstructionDLL = ctypes.cdll.LoadLibrary(
            os.path.join(constants.rootFolderPath, 'libs/GPU_acc_recon.dll')
        )

    def make3dPtrArray(self, inData):
        assert len(np.shape(inData)) == 3, 'Trying to make 3D ctypes.POINTER array out of non-3D data'

        data = inData
        slices = data.shape[0]

        pythPtrArray = []

        for j in range(0, slices):
            ptr = data[j].ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            pythPtrArray.append(ptr)
        cPtrArray = (ctypes.POINTER(ctypes.c_ubyte) * slices)(*pythPtrArray)
        return cPtrArray

    def make4dPtrArray(self, inData):
        assert len(np.shape(inData)) == 4, 'Trying to make 4D ctypes.POINTER array out of non-4D data'

        data = inData
        groups = data.shape[0]
        slices = data.shape[1]

        pythPtrArray = []

        for i in range(0, groups):
            tempPythPtrArray = []
            for j in range(0, slices):
                ptr = data[i][j].ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
                tempPythPtrArray.append(ptr)
            tempCPtrArray = (ctypes.POINTER(ctypes.c_ubyte) * slices)(*tempPythPtrArray)
            pythPtrArray.append(ctypes.cast(tempCPtrArray, ctypes.POINTER(ctypes.c_ubyte)))
        cPtrArray = (ctypes.POINTER(ctypes.c_ubyte) * groups)(*pythPtrArray)

        return cPtrArray

    def extractSignal(self, data, sigmas, pattern, dev):
        """Extracts the signal of the data according to given parameters.
        Output is a 4D matrix where first dimension is base and last three
        are frame and pixel coordinates."""

        print('Max in data = ', data.max())
        dataPtrArray = self.make3dPtrArray(data)
        p = ctypes.c_float * 4
        # Minus one due to different (1 or 0) indexing in C/Matlab
        cPattern = p(pattern[0], pattern[1], pattern[2], pattern[3])
        cNumBases = ctypes.c_int(np.size(sigmas))
        print('Sigmas = ', sigmas)
        sigmas = np.array(sigmas, dtype=np.float32)
        cSigmas = np.ctypeslib.as_ctypes(sigmas)  # s(1, 10)
        cGridRows = ctypes.c_int(0)
        cGridCols = ctypes.c_int(0)
        cImRows = ctypes.c_int(data.shape[1])
        cImCols = ctypes.c_int(data.shape[2])
        cImSlices = ctypes.c_int(data.shape[0])

        self.ReconstructionDLL.calc_coeff_grid_size(
            cImRows, cImCols,
            ctypes.byref(cGridRows), ctypes.byref(cGridCols),
            ctypes.byref(cPattern)
        )
        print('Coeff grid calculated')

        resCoeffs = np.zeros(dtype=np.float32, shape=(cNumBases.value, cImSlices.value,
                                                      cGridRows.value, cGridCols.value))
        resPtr = self.make4dPtrArray(resCoeffs)
        t = time.time()

        if dev == 'cpu':
            extractionFunction = self.ReconstructionDLL.extract_signal_CPU
        elif dev == 'gpu':
            extractionFunction = self.ReconstructionDLL.extract_signal_GPU
        else:
            raise ValueError(f'Device must be either "cpu" or "gpu"; {dev} given')

        extractionFunction(cImRows, cImCols,
                           cImSlices, ctypes.byref(cPattern),
                           cNumBases, ctypes.byref(cSigmas),
                           ctypes.byref(dataPtrArray), ctypes.byref(resPtr))

        elapsed = time.time() - t
        print('Signal extraction performed in', elapsed, 'seconds')
        return resCoeffs
