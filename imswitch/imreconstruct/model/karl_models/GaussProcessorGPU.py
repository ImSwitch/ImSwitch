import cupy as cp
import numpy as np
from .geometry import get_rectangles, get_interp_coords, get_1d_indices
from typing import Dict, Tuple


class GaussProcessorGPU: 
    """
    Processor for GPU-accelerated image reconstruction using Gaussian 
    least-squares weighting and bilinear interpolation.
    """

    def __init__(
            self, 
            args: Dict, 
            scan_ori: str = "+x+y"
    ) -> None:
        """
        Initializes the GPU processor with scan parameters and pre-calculates 
        interpolation coordinates and reconstruction weights.

        Args:
            args (Dict): Dictionary containing grid parameters (xp, xo, yp, yo, etc.).
            scan_ori (str): String defining the scanning orientation (e.g., "+x+y").
        """
        self.num_rows = args["num_rows"]
        self.num_cols = args["num_cols"]
        self.num_foci = args["nx_c"] * args["ny_c"]
 
        x_interp, y_interp = get_interp_coords(args)
        self.x_interp = cp.array(x_interp)
        self.y_interp = cp.array(y_interp)
        
        self.lsq_weights, self.pts_per_focus = self._calculate_weights()
        
        self.frame_inds = get_1d_indices(args, scan_ori)
        self.num_frames_in_stack = args["nx_s"] * args["ny_s"]


    def _calculate_weights(self) -> Tuple[cp.ndarray, int]: 
        """
        Calculates the least-squares weights based on a Gaussian profile 
        to extract signal intensity from the background.

        Returns:
            Tuple[cp.ndarray, int]: A Tuple containing the 1D weight array (CuPy) 
                                   and the number of points per focus.
        """
        X_rec, Y_rec = get_rectangles(num_rects=6)
        sig = 2.0 
    
        gauss_vec = np.exp(-(X_rec**2 + Y_rec**2) / (2 * sig**2))
        bg_vec = np.ones(len(gauss_vec))
        A = np.stack((gauss_vec, bg_vec))
        
        lsq_weights = np.linalg.pinv(A)[:, 0] 
        
        return cp.array(lsq_weights), len(gauss_vec)
    

    def process_frame(self, frame_gpu: cp.ndarray) -> np.ndarray:
        """
        Performs bilinear interpolation on the input frame and applies 
        pre-calculated weights to reconstruct focus intensities.

        Args:
            frame_gpu (cp.ndarray): The 2D raw image frame (already on GPU).

        Returns:
            cp.ndarray: 1D array of reconstructed intensity values on the GPU.
        """
        x0 = cp.clip(cp.floor(self.x_interp).astype(cp.int32), 0, self.num_cols - 1)
        x1 = cp.clip(x0 + 1, 0, self.num_cols - 1)
        y0 = cp.clip(cp.floor(self.y_interp).astype(cp.int32), 0, self.num_rows - 1)
        y1 = cp.clip(y0 + 1, 0, self.num_rows - 1)
        
        dx = self.x_interp - x0 
        dy = self.y_interp - y0
        
        interp_vals = (
            frame_gpu[y0, x0] * (1 - dx) * (1 - dy) 
            + frame_gpu[y1, x0] * (1 - dx) * dy
            + frame_gpu[y0, x1] * dx * (1 - dy)
            + frame_gpu[y1, x1] * dx * dy
        ).reshape((self.num_foci, self.pts_per_focus))

        return cp.asnumpy(cp.dot(interp_vals, self.lsq_weights))
    
    def process_chunk(self, chunk_GPU: cp.ndarray) -> np.ndarray:
        """ Processes an entire 3D chunk (num_frames, Y, X) at once on the GPU. """
        x0 = cp.clip(cp.floor(self.x_interp).astype(cp.int32), 0, self.num_cols - 1)
        x1 = cp.clip(x0 + 1, 0, self.num_cols - 1)
        y0 = cp.clip(cp.floor(self.y_interp).astype(cp.int32), 0, self.num_rows - 1)
        y1 = cp.clip(y0 + 1, 0, self.num_rows - 1)
        
        dx = self.x_interp - x0 
        dy = self.y_interp - y0
    
        interp_vals = (
            chunk_GPU[:, y0, x0] * (1 - dx) * (1 - dy) 
            + chunk_GPU[:, y1, x0] * (1 - dx) * dy
            + chunk_GPU[:, y0, x1] * dx * (1 - dy)
            + chunk_GPU[:, y1, x1] * dx * dy
        ).reshape((chunk_GPU.shape[0], self.num_foci, self.pts_per_focus))

        return cp.asnumpy(cp.matmul(interp_vals, self.lsq_weights))