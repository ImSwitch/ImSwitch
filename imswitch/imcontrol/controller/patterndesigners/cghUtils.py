
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.signal import find_peaks
import cv2

def refine_frequency_1D(profile, f_expected, search_width=0.5):
    N = len(profile)
    freqs = np.fft.fftfreq(N)
    idx_exp = np.argmin(np.abs(freqs - f_expected))
    half_range = int(search_width * N)
    i1 = max(0, idx_exp - half_range)
    i2 = min(N, idx_exp + half_range)
    local = profile[i1:i2]
    local_freqs = freqs[i1:i2]
    peaks, _ = find_peaks(local)
    if len(peaks) == 0:
        return f_expected
    best = peaks[np.argmax(local[peaks])]
    return local_freqs[best]


def fft_frequency_estimation(arr, blur_sigma=1.0, exclude_frac=0.06,peak_prom=0.05):
    """
    Estimate dominant spatial frequencies from FFT peak detection.

    Parameters
    ----------
    arr : 2D array
        Input image.
    blur_sigma : float
        Gaussian blur applied before FFT to reduce noise.
    exclude_frac : float
        Fraction of FFT size to exclude around DC.
    peak_prom : float
        Peak prominence for detecting FFT peaks.

    Returns
    -------
    fx : float
        Dominant frequency along x (in cycles per pixel).
    fy : float
        Dominant frequency along y (in cycles per pixel).
    """

    # 1) Mild smoothing (denoise)
    arr_smooth = gaussian_filter(arr.astype(float), blur_sigma)

    # 2) FFT magnitude (centered)
    F = np.fft.fftshift(np.fft.fft2(arr_smooth))
    A = np.abs(F)
    h, w = A.shape
    cy, cx = h // 2, w // 2

    # 3) Mask central DC region (avoid huge peak)
    exclude_radius = int(exclude_frac * min(h, w))
    Y, X = np.ogrid[:h, :w]
    A_mask = A.copy()
    A_mask[(Y - cy)**2 + (X - cx)**2 < exclude_radius**2] = 0

    # 4) Extract central horizontal and vertical lines
    line_x = A_mask[cy, :]
    line_y = A_mask[:, cx]

    # Normalize to [0,1] (stable peak detection)
    line_x /= (line_x.max() + 1e-12)
    line_y /= (line_y.max() + 1e-12)

    # 5) Peak detection
    px, _ = find_peaks(line_x, prominence=peak_prom)
    py, _ = find_peaks(line_y, prominence=peak_prom)

    if len(px) == 0 or len(py) == 0:
        raise RuntimeError("Could not detect FFT peaks; adjust parameters.")

    # Highest-prominence peaks
    kx = px[np.argmax(line_x[px])]
    ky = py[np.argmax(line_y[py])]

    # Convert FFT index → frequency in cycles/pixel
    fx = (kx - cx) / w
    fy = (ky - cy) / h
    return fx, fy


def fft_constrained_frequency_estimation(arr, fx_exp, fy_exp, search_width=0.5):
    """
    Frequency estimator constrained around `fx_exp`, `fy_exp` with a window of `search_width`.
    """

    win = np.hanning(arr.shape[0])[:, None] * np.hanning(arr.shape[1])[None, :]
    A = arr * win
    F = np.fft.fft2(A)
    Fmag = np.abs(F)
    prof_x = gaussian_filter(np.sum(Fmag, axis=0), 2)
    prof_y = gaussian_filter(np.sum(Fmag, axis=1), 2)
    fx = refine_frequency_1D(prof_x, fx_exp, search_width)
    fy = refine_frequency_1D(prof_y, fy_exp, search_width)
    return fx, fy


def refine_foci_positions(arr, x_est, y_est, method='max', window=3, verbose=False):
    """
    Refine foci postitions based on "max" intensity or "cog" (center of gravity) method.
    """

    h, w = arr.shape
    x_refined = []
    y_refined = []
    
    for idx, (x0, y0) in enumerate(zip(x_est, y_est)):
        x1 = max(0, int(round(x0 - window)))
        x2 = min(w, int(round(x0 + window + 1)))
        y1 = max(0, int(round(y0 - window)))
        y2 = min(h, int(round(y0 + window + 1)))

        patch = arr[y1:y2, x1:x2]
        if patch.sum() == 0:
            x_refined.append(x0)
            y_refined.append(y0)
            continue

        yy, xx = np.meshgrid(np.arange(y1, y2), np.arange(x1, x2), indexing='ij')

        if method == 'cog':
            total = patch.sum()
            x_c = np.sum(xx * patch) / total
            y_c = np.sum(yy * patch) / total
        elif method == 'max':
            idx_patch = np.unravel_index(np.argmax(patch), patch.shape)
            y_c = y1 + idx_patch[0]
            x_c = x1 + idx_patch[1]
        else:
            raise ValueError("Unknown refinement method")

        x_refined.append(x_c)
        y_refined.append(y_c)

        move_distance = np.sqrt((x_c - x0)**2 + (y_c - y0)**2)
        if verbose and move_distance > 0.1:
            print(f"Trap {idx}: moved {move_distance:.2f} px from ({x0:.2f},{y0:.2f}) to ({x_c:.2f},{y_c:.2f})")
    
    return np.array(x_refined), np.array(y_refined)


def estimate_lattice_offset(arr, ax, ay, npx, npy, blur_sigma=1.0,
                            search_frac=0.5, search_steps=8):
    """
    Estimate the origin offset (dx0, dy0) for a periodic lattice pattern.
    Performs a grid search over integer pixel offsets and selects the one
    maximizing the average sampled intensity at expected lattice points.

    Parameters
    ----------
    arr : 2D array
        Input image.
    ax, ay : float
        Spatial periods along x and y.
    npx, npy : int
        Number of lattice peaks to evaluate along x and y.
    blur_sigma : float
        Gaussian blur applied before scoring.
    search_frac : float
        Fraction of min(ax, ay) defining max search radius.
    search_steps : int
        Number of steps across the search range (per axis).

    Returns
    -------
    dx0, dy0 : int
        Estimated integer pixel offset for the lattice origin.
    """
    search_steps=int(search_steps)
    
    # Smooth image for robustness
    arr_smooth = gaussian_filter(arr.astype(float), blur_sigma)
    h, w = arr.shape

    # Search radius in pixels
    search_r = int(min(ax, ay) * search_frac)
    if search_r < 1:
        return 0, 0

    # Steps in dx, dy
    step = max(1, search_r // search_steps)
    candidates = range(0, 2*search_r + 1, step)

    best_score = -np.inf
    best_offset = (0, 0)

    # Grid search over dx, dy
    for dy in candidates:
        for dx in candidates:

            score = 0.0
            count = 0

            # Sample lattice points
            for j in range(npy):
                for i in range(npx):

                    y = dy + j * ay
                    x = dx + i * ax

                    yi = int(round(y))
                    xi = int(round(x))

                    if 0 <= yi < h and 0 <= xi < w:
                        score += arr_smooth[yi, xi]
                        count += 1

            if count > 0:
                avg_score = score / count
                if avg_score > best_score:
                    best_score = avg_score
                    best_offset = (dx, dy)

    return best_offset



def crop_with_preview(arr, kernel_size, threshold1):
    """
    Crop the array based on threshold + dilation and return the cropped region
    as well as a preview image showing the crop rectangle.

    Parameters
    ----------
    arr : np.ndarray
        Input image (2D or 3D).
    kernel_size : int
        Kernel size used for dilation.
    threshold1 : float
        Fraction of maximum brightness used to binarize the image.

    Returns
    -------
    cropped : np.ndarray
        Cropped array.
    preview : np.ndarray (uint8)
        RGB preview image with the crop rectangle drawn.
    """

    binary = (arr > arr.max() * threshold1).astype("uint8")

    kernel = np.ones((kernel_size, kernel_size), dtype="uint8")
    arr_dilation = cv2.dilate(binary, kernel, iterations=1)

    nonzero_y, nonzero_x = np.nonzero(arr_dilation)
    if len(nonzero_y) == 0:
        # nothing detected → return original + no rectangle
        cropped = arr.copy()
        return cropped, arr

    y1, y2 = nonzero_y.min(), nonzero_y.max()
    x1, x2 = nonzero_x.min(), nonzero_x.max()

    cropped = arr[y1:y2, x1:x2].copy()

    preview = arr.copy()
    preview = cv2.rectangle(preview, (x1, y1), (x2, y2), (255, 255, 255), 2)

    return cropped, preview

def sum_around(array: np.ndarray, coord_x: float, coord_y: float, window_size: int, zero_out: bool = False):
    """
    Sample a square region of size n x n around given coordinates in an array,
    sum all the values (summing), and  optionnaly zero out that region for preview.

    Parameters
    ----------
    array : np.ndarray
        2D array to sample from.
    coord_x : float
        X-coordinate (column) around which to sample.
    coord_y : float
        Y-coordinate (row) around which to sample.
    window_size : int
        Size of the square integration region (window_size x window_size).
    zero_out: bool, default = False
        If true, modify array by putting all the values inside the integration
        region to zero
        
    Returns
    -------
    sampled_sum: float
        sum of the values inside the integration window
    preview: np.ndarray
        copy of array with zero-out 
    """
    h, w = array.shape
    sample_center = window_size // 2

    # Compute integer offset for top-left corner of sampling square
    off_x = int(round(coord_x - sample_center))
    off_y = int(round(coord_y - sample_center))

    # Create sampling grid
    s_x, s_y = np.meshgrid(np.arange(window_size), np.arange(window_size))
    s_x = s_x + off_x
    s_y = s_y + off_y

    # Clip to array boundaries
    s_x = np.clip(s_x, 0, w - 1)
    s_y = np.clip(s_y, 0, h - 1)

    # Sum sampled values
    sampled_sum = np.sum(array[s_y, s_x])

    if zero_out:
        array[s_y, s_x] = 0

    return float(sampled_sum), array