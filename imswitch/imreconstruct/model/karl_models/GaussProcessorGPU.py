import cupy as cp
import numpy as np
from .geometry import get_rectangles_coords, get_interp_coords, get_1d_indices
from typing import Tuple


class GaussProcessorGPU: 
    """
    Processor for GPU-accelerated image reconstruction using Gaussian least-squares weighting and bilinear interpolation.
    
    Args:
        xp (float): X-axis period.
        xo (float): X-axis offset.
        yp (float): Y-axis period.
        yo (float): Y-axis offset.
        nx_c (int): Number of foci along x.
        ny_c (int): Number of foci along y.
        nx_s (int): Scanner steps along x.
        ny_s (int): Scanner steps along y.
        num_cols (int): Total number of columns in the frame.
        num_rows (int): Total number of rows in the frame.
        num_rects (int): Number of rectangles used to model the foci, which defaults to 3.
        scan_ori (str): Scan orientation string, which defaults to "+x+y".
    """
    def __init__(
            self, 
            xp: float, 
            xo: float, 
            yp: float, 
            yo: float, 
            nx_c: int, 
            ny_c: int,
            nx_s: int,
            ny_s: int, 
            num_cols: int,
            num_rows: int,
            num_rects: int = 3, 
            scan_ori: str = "+x+y"
    ) -> None:
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.num_foci = nx_c * ny_c
        self.num_rects = num_rects
        self.scan_ori = scan_ori
        x_interp, y_interp = get_interp_coords(xp, xo, yp, yo, nx_c, ny_c, num_cols, num_rows, num_rects)
        self.x_interp = cp.array(x_interp)
        self.y_interp = cp.array(y_interp)
        self.lsq_weights, self.pts_per_focus = self._calculate_weights(num_rects)
        self.frame_inds = get_1d_indices(nx_c, ny_c, nx_s, ny_s, scan_ori)
        self.num_frames_in_stack = nx_s * ny_s


    def _calculate_weights(self, num_rects: int) -> Tuple[cp.ndarray, int]: 
        """
        Calculates the least-squares weights based on a Gaussian profile 
        to extract signal intensity from the background.

        Args:
            num_rects (int): Number of rectangles used to model the foci.
        
        Returns:
            Tuple[cp.ndarray, int]: A Tuple containing the 1D weight array (CuPy) and the number of points per focus.
        """
        Xr, Yr = get_rectangles_coords(num_rects)
        sigma = 2.0 
        gauss_vec = np.exp(-(Xr**2 + Yr**2) / (2 * sigma**2))
        bg_vec = np.ones(len(gauss_vec))
        A_mat = np.stack((gauss_vec, bg_vec))
        lsq_weights = np.linalg.pinv(A_mat)[:, 0] 
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
        """ 
        Processes an entire 3D chunk (num_frames, Y, X) at once on the GPU. 
        
        Args:
            chunk_GPU (cp.ndarray): A sub-stack (chunk) of raw frames. 
        
        Returns:
            np.ndarray: Processed pixels for each raw frame in the chunk.
        """
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
        ).reshape((-1, self.num_foci, self.pts_per_focus))

        return cp.asnumpy(cp.matmul(interp_vals, self.lsq_weights))
    

    def update_frame_inds(
            self,
            nx_c: int, 
            ny_c: int,
            nx_s: int, 
            ny_s: int, 
            scan_ori: str
    ): 
        """ 
        Updates the frame inds for the processor.
        
        Args:
            nx_c (int): Number of foci along x.
            ny_c (int): Number of foci along y.
            nx_s (int): Scanner steps along x.
            ny_s (int): Scanner steps along y.
            scan_ori (str): Scan orientation string.
        """
        self.frame_inds = get_1d_indices(nx_c, ny_c, nx_s, ny_s, scan_ori)
        