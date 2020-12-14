import ctypes
import numpy as np
import os
import time


class SignalExtractor:
    """ This class takes the raw data together with pre-set
    parameters and recontructs and stores the final images (for the different
    bases). Final images stored in
    - self.images

    """

    def __init__(self, dll_path):
        self.images = np.array([])

        # This is needed by the DLL containing CUDA code.
        # ctypes.cdll.LoadLibrary(os.environ['CUDA_PATH_V9_0'] + '\\bin\\cudart64_90.dll')
        ctypes.cdll.LoadLibrary(os.path.join(os.getcwd(), 'dlls\cudart64_90.dll'))
        print(os.path.join(os.getcwd(), dll_path))
        self.ReconstructionDLL = ctypes.cdll.LoadLibrary(os.path.join(os.getcwd(), dll_path))

    def make_3d_ptr_array(self, in_data):
        assert (len(np.shape(in_data)) == 3,
                'Trying to make 3D ctypes.POINTER array out of non-3D data')

        data = in_data
        slices = data.shape[0]

        pyth_ptr_array = []

        for j in range(0, slices):
            ptr = data[j].ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            pyth_ptr_array.append(ptr)
        c_ptr_array = (ctypes.POINTER(ctypes.c_ubyte) * slices)(*pyth_ptr_array)
        return c_ptr_array

    def make_4d_ptr_array(self, in_data):
        assert (len(np.shape(in_data)) == 4,
                'Trying to make 4D ctypes.POINTER array out of non-4D data')

        data = in_data
        groups = data.shape[0]
        slices = data.shape[1]

        pyth_ptr_array = []

        for i in range(0, groups):
            temp_p_ptr_array = []
            for j in range(0, slices):
                ptr = data[i][j].ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
                temp_p_ptr_array.append(ptr)
            temp_c_ptr_array = (ctypes.POINTER(ctypes.c_ubyte) * slices)(*temp_p_ptr_array)
            pyth_ptr_array.append(ctypes.cast(temp_c_ptr_array, ctypes.POINTER(ctypes.c_ubyte)))
        c_ptr_array = (ctypes.POINTER(ctypes.c_ubyte) * groups)(*pyth_ptr_array)

        return c_ptr_array

    def extract_signal(self, data, sigmas, pattern, dev):
        """Extracts the signal of the data according to given parameters.
        Output is a 4D matrix where first dimension is base and last three
        are frame and pixel coordinates."""

        print('Max in data = ', data.max())
        data_ptr_array = self.make_3d_ptr_array(data)
        p = ctypes.c_float * 4
        # Minus one due to different (1 or 0) indexing in C/Matlab
        c_pattern = p(pattern[0], pattern[1], pattern[2], pattern[3])
        c_nr_bases = ctypes.c_int(np.size(sigmas))
        print('Sigmas = ', sigmas)
        sigmas = np.array(sigmas, dtype=np.float32)
        c_sigmas = np.ctypeslib.as_ctypes(sigmas)  # s(1, 10)
        c_grid_rows = ctypes.c_int(0)
        c_grid_cols = ctypes.c_int(0)
        c_im_rows = ctypes.c_int(data.shape[1])
        c_im_cols = ctypes.c_int(data.shape[2])
        c_im_slices = ctypes.c_int(data.shape[0])

        self.ReconstructionDLL.calc_coeff_grid_size(
            c_im_rows, c_im_cols,
            ctypes.byref(c_grid_rows), ctypes.byref(c_grid_cols),
            ctypes.byref(c_pattern)
        )
        print('Coeff_grid calculated')

        res_coeffs = np.zeros(dtype=np.float32, shape=(c_nr_bases.value, c_im_slices.value,
                                                       c_grid_rows.value, c_grid_cols.value))
        res_ptr = self.make_4d_ptr_array(res_coeffs)
        t = time.time()

        if dev == 'cpu':
            extractionFunction = self.ReconstructionDLL.extract_signal_CPU
        elif dev == 'gpu':
            extractionFunction = self.ReconstructionDLL.extract_signal_GPU
        else:
            raise ValueError(f'Device must be either "cpu" or "gpu"; {dev} given')

        extractionFunction(c_im_rows, c_im_cols,
                           c_im_slices, ctypes.byref(c_pattern),
                           c_nr_bases, ctypes.byref(c_sigmas),
                           ctypes.byref(data_ptr_array), ctypes.byref(res_ptr))

        elapsed = time.time() - t
        print('Signal extraction performed in', elapsed, 'seconds')
        return res_coeffs
