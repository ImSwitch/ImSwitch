import numpy as np
from .geometry import get_center_coords
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.signal import find_peaks
from scipy.optimize import least_squares
from typing import Union, Dict, Tuple


def _find_best_peak_index(peaks: Tuple) -> int:
    """
    Finds the index of the peak with the greatest prominence in the peaks Tuple.
    
    Args:
        peaks (Tuple): Contains data of peaks gathered from scipy.signal find_peaks.
    
    Returns:
        int: Index of the peak with the greatest prominence.
    """
    prominences = peaks[1]["prominences"]
    heights = peaks[1]["peak_heights"]
    
    if len(prominences) < 2:
        return 0 # Fallback if only one peak exists

    # Get the indices of the top 2 peaks by prominence
    sorted_prom_indices = np.argsort(prominences)
    p1_index = sorted_prom_indices[-1]
    p2_index = sorted_prom_indices[-2]

    p1_prom = prominences[p1_index]
    p2_prom = prominences[p2_index]

    p1_height = heights[p1_index]
    p2_height = heights[p2_index]

    diff_prom = np.abs((p1_prom - p2_prom) / (p1_prom + p2_prom)) 
    diff_height = np.abs((p1_height - p2_height) / (p1_height + p2_height))
    
    # Selection logic for similar prominence but different heights
    tol = 0.2
    if (diff_prom < tol) and (diff_height < tol) and (p1_height < p2_height):
        return p2_index
    
    return p1_index

def _estimate_period(
        period_guess: float,
        input_data: np.ndarray
) -> float:
    """
    Estimates the dominant period in the 1D input data using FFT and Gaussian fitting.
    
    Args:
        period_guess (float): Initial period guess.
        input_data (np.ndarray): 1D data array (e.g., row or column averages).
    
    Returns:
        float: Refined estimate of the period.
    """
    data_size = input_data.size

    # --- Frequency Analysis ---
    fft_max_index = data_size // 2 
    abs_fft = np.abs(np.fft.fft(input_data)[0:fft_max_index])
    fft_freqs = np.fft.fftfreq(fft_max_index)
    
    # --- Frequency Thresholding ---
    target_freq = 2 / period_guess
    tol = 0.05
    abs_fft[fft_freqs < target_freq - tol] = 0
    abs_fft[fft_freqs > target_freq + tol] = 0
    
    # --- Peak Identification ---
    peaks = find_peaks(abs_fft, prominence=[0, np.inf], width=0, height=0)
    best_peak_index = _find_best_peak_index(peaks) 
    peak_index = peaks[0][best_peak_index]
    peak_width = peaks[1]["widths"][best_peak_index]
    
    # Define window for refinement
    peak_spread = 6 * peak_width 
    win_min = int(max(0, peak_index - peak_spread))
    win_max = int(min(peak_index + peak_spread, fft_max_index))
    win_range = np.arange(start=win_min, step=1, stop=win_max, dtype=int)

    # --- Refine Period via Gaussian Fit --- 
    def _gauss_fun(x0, x, y):
        a, b, mu, sigma = x0
        return (a + b*np.exp(-(x - mu)**2 / (2 * sigma**2))) - y

    x0_guesses = np.array([np.min(abs_fft), np.max(abs_fft) - np.min(abs_fft), peak_index, peak_width])
    res_gauss_fit = least_squares(_gauss_fun, x0_guesses, args=(win_range, abs_fft[win_range]), ftol=1e-12, xtol=1e-12)
    est_period = np.abs(data_size / res_gauss_fit.x[2])

    return est_period

def _estimate_offset(
        est_period: float, 
        input_data: np.ndarray
) -> float:
    """
    Estimates the phase offset in the 1D input data using a cosine fitting approach. 

    Args:
        est_period (float): Estimated period in the input data.
        input_data (np.ndarray): 1D data array.
    
    Returns:
        float: Estimated offset in pixels.
    """
    def _cos_fun(x0, x, y): 
        offset = x0
        return np.cos(np.pi*(x - offset) / est_period)**6 - y

    x_range = np.arange(input_data.size)
    res_cos_fit = least_squares(_cos_fun, x0=0.0, args=(x_range, input_data), ftol=1e-12, xtol=1e-12)
    est_offset = np.mod(res_cos_fit.x[0], est_period)

    return est_offset

def _optimize_parameters(
        est_period: float, 
        est_offset: float, 
        input_data: np.ndarray
) -> Tuple[float, float]:
    """
    Simultaneously optimizes both period and offset using least squares.
    
    Args:
        est_period (float): Initial period estimate.
        est_offset (float): Initial offset estimate.
        input_data (np.ndarray): 1D data array.
    
    Returns:
        Tuple[float, float]: Optimized (period, offset).
    """
    def _cos_fun(x0, x, y):
        period, offset = x0
        return np.cos(np.pi*(x - offset) / period)**6 - y 
    
    x0_guesses = np.array([est_period, est_offset])
    x_range = np.arange(input_data.size)
    res_cos_fit = least_squares(fun=_cos_fun, x0=x0_guesses, args=(x_range, input_data), ftol=1e-12, xtol=1e-12)
    
    opt_period = np.abs(res_cos_fit.x[0]) 
    opt_offset = np.mod(res_cos_fit.x[1], opt_period)
        
    return opt_period, opt_offset

def localizer(
        img_data: np.ndarray,
        xp_guess: float = 10.0,
        yp_guess: float = 10.0,
        plot: bool = False,
        dummy_mode: bool = False
) -> Dict[str, Union[int, float]]:
    """
    Finds grid periods and offsets in 2D image data. Handles both single 
    frames and summed image stacks.
    
    Args:
        img_data (np.ndarray): 2D frame or 3D stack of frames.
        xp_guess (float): Initial guess for x-period.
        yp_guess (float): Initial guess for y-period.
        plot (bool): If True, displays the grid localization results.
        dummy_mode (bool): return dummy values for testing.
        
    Returns:
        Dict[str, Union[int, float]]: Mapping of optimized grid parameters and dimensions.
    """
    if img_data.ndim == 3: 
        num_frames, num_rows, num_cols = img_data.shape
        img_stack_sum = np.double(img_data.sum(axis=0))
        img_stack_sum_plot = np.copy(img_stack_sum)
        nx_s = int(np.ceil(np.sqrt(num_frames)))
        ny_s = nx_s
    elif img_data.ndim == 2:
        num_frames = 1
        num_rows, num_cols = img_data.shape
        img_stack_sum = np.double(img_data)
        img_stack_sum_plot = np.copy(img_stack_sum)
    else:
        raise ValueError(f"Expected 2D or 3D array, got {img_data.ndim}D")

    # --- Pre-Filtering ---
    sigma_low = 2.0
    sigma_high = (xp_guess + yp_guess) / 2
    img_stack_sum -= gaussian_filter(img_stack_sum, sigma_high) # high pass
    img_stack_sum = gaussian_filter(img_stack_sum, sigma_low) # small blur
    img_stack_sum -= img_stack_sum.mean() 

    # --- Get Col and Row Averages ---
    x_img_avg = img_stack_sum.mean(axis=0) # cols 
    y_img_avg = img_stack_sum.mean(axis=1) # rows

    # --- Estimation ---
    xp_est = _estimate_period(xp_guess, x_img_avg)
    xo_est = _estimate_offset(xp_est, x_img_avg)
    
    yp_est = _estimate_period(yp_guess, y_img_avg)
    yo_est = _estimate_offset(yp_est, y_img_avg)

    # --- Optimization ---
    xp, xo = _optimize_parameters(xp_est, xo_est, x_img_avg)
    yp, yo = _optimize_parameters(yp_est, yo_est, y_img_avg)

    # --- Num of Foci in each dimension ---
    nx_c = int(np.ceil((num_cols - xo) / xp)) 
    ny_c = int(np.ceil((num_rows - yo) / yp))

    # --- Localizer Parameters to Return --- 
    loc_parms = {
        "num_rows": num_rows,
        "num_cols": num_cols,
        "xp": xp,
        "yp": yp,
        "xo": xo,
        "yo": yo,
        "nx_c": nx_c, 
        "ny_c": ny_c,
        "nx_s": nx_s, # should be removed in the future 
        "ny_s": ny_s  # should be removed in the future
    }

    # --- Plotting (debugging) --- 
    if plot:
        X, Y = get_center_coords(loc_parms)
        plt.imshow(img_stack_sum_plot, cmap="gray")
        plt.scatter(X.flatten(), Y.flatten(), s=5, c="red")
        plt.show()

    return loc_parms