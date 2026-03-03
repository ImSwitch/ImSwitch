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
        
        # Pre-calculate interpolation coordinates
        x_interp, y_interp = get_interp_coords(args)
        self.x_interp = cp.array(x_interp)
        self.y_interp = cp.array(y_interp)
        
        # Pre-calculate weights for least-squares fitting
        self.lsq_weights, self.pts_per_focus = self._calculate_weights()
        
        # Pre-calculate 1D mapping for frame placement
        self.frame_inds = get_1d_indices(args, scan_ori)
        # self.frame_inds[0] -> indices for the first raw frame

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
        
        # Stack Gaussian signal and constant background components
        A = np.stack((gauss_vec, bg_vec))
        
        # Use pseudo-inverse to find weights for the Gaussian component
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
        # Calculate bounding integer coordinates for bilinear interpolation
        x0 = cp.clip(cp.floor(self.x_interp).astype(cp.int32), 0, self.num_cols - 1)
        x1 = cp.clip(x0 + 1, 0, self.num_cols - 1)
        y0 = cp.clip(cp.floor(self.y_interp).astype(cp.int32), 0, self.num_rows - 1)
        y1 = cp.clip(y0 + 1, 0, self.num_rows - 1)
        
        # Fractional distances for interpolation weights
        dx = self.x_interp - x0 
        dy = self.y_interp - y0
        
        # Perform bilinear interpolation
        interp_vals = (
            frame_gpu[y0, x0] * (1 - dx) * (1 - dy) 
            + frame_gpu[y1, x0] * (1 - dx) * dy
            + frame_gpu[y0, x1] * dx * (1 - dy)
            + frame_gpu[y1, x1] * dx * dy
        ).reshape((self.num_foci, self.pts_per_focus))

        # Dot product with LSQ weights to get the final focus values
        # AND return array as numpy array => CPU assignment later on
        return cp.asnumpy(cp.dot(interp_vals, self.lsq_weights))
    