# type: ignore


import numpy as np
from typing import Tuple


def get_center_coords(
        xp: float, 
        xo: float, 
        yp: float, 
        yo: float,
        nx_c: int, 
        ny_c: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates a grid pattern based on the parameters gathered from the localizer.
    
    Args:
        xp (float): Period along x-axis in pixels from localizer. 
        xo (float): Offset along x-axis in pixels from localizer. 
        yp (float): Period along y-axis in pixels from localizer. 
        yo (float): Offset along y-axis in pixels from localizer.
        nx_c (int): Number of foci along x-axis. 
        ny_c (int): Number of foci along y-axis. 
            
    Returns: 
        Tuple[np.ndarray, np.ndarray]: Tuple containing the flattened grid coordinates for X and Y, respectively.
    """
    x_stop = xo + (nx_c - 1) * xp 
    y_stop = yo + (ny_c - 1) * yp
    
    X, Y = np.meshgrid(np.linspace(xo, x_stop, nx_c), np.linspace(yo, y_stop, ny_c)) 
    
    return X.flatten(), Y.flatten()


def get_rectangles_coords(num_rects: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates X and Y pixel coordinates for a given number of concentric rectangles.
    
    Args:
        num_rects (int): Number of rectangles.

    Returns:
        Tuple[np.ndarray, np.ndarray]: X and Y-pixel coordinates for the rectangles.
    """
    num_rects += 1
    start = 1 - num_rects
    stop = num_rects
    steps = 1 
    
    X, Y = np.meshgrid(
        np.arange(start, stop, steps, dtype=float),
        np.arange(start, stop, steps, dtype=float)
    )
    
    return X.flatten(), Y.flatten()


def get_interp_coords(
        xp: float, 
        xo: float, 
        yp: float, 
        yo: float, 
        nx_c: int, 
        ny_c: int,
        num_cols: int, 
        num_rows: int,
        num_rects: int = 3
) -> Tuple[np.ndarray, np.ndarray]: 
    """
    Generates local interpolation coordinates around each grid focus center.

    Args:
        xp (float): X-axis period.
        xo (float): X-axis offset.
        yp (float): Y-axis period.
        yo (float): Y-axis offset.
        nx_c (int): Number of foci along x-axis. 
        ny_c (int): Number of foci along y-axis. 
        num_cols (int): Total number of columns in the frame.
        num_rows (int): Total number of rows in the frame.
        num_rects (int): Number of rectangles used to model the foci.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Flattened X and Y interpolation coordinates clipped to frame boundaries.
    """
    Xc, Yc = get_center_coords(xp, xo, yp, yo, nx_c, ny_c)
    Xr, Yr = get_rectangles_coords(num_rects)
    
    Xi = Xc.reshape((-1, 1)) + Xr 
    Yi = Yc.reshape((-1, 1)) + Yr
    
    Xi[Xi < 0] = 0
    Xi[Xi > num_cols - 1] = 0
    Yi[Yi < 0] = 0
    Yi[Yi > num_rows- 1] = 0
    
    return Xi.flatten(), Yi.flatten()


def _get_bases(
        nx_c: int, 
        ny_c: int, 
        nx_s: int, 
        ny_s: int, 
        scan_ori: str
) -> Tuple[np.ndarray, np.ndarray]: 
    """
    Creates base indices for rows and columns based on scan dimensions.

    Args:
        nx_c (int): Number of foci along x.
        ny_c (int): Number of foci along y.
        nx_s (int): Scanner steps along x.
        ny_s (int): Scanner steps along y.
        scan_ori (str): Scan orientation string.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Base indices for x and y.
    """
    x_start = 0 if scan_ori.find("+x") != -1 else nx_s - 1
    x_stop = x_start + nx_c * nx_s
    x_steps = nx_s

    y_start = 0 if scan_ori.find("+y") != -1 else ny_s - 1 
    y_stop = y_start + ny_c * ny_s
    y_steps = ny_s 

    xb = np.arange(x_start, x_stop, x_steps, dtype=int)
    yb = np.arange(y_start, y_stop, y_steps, dtype=int)

    return xb, yb

def _get_shifts(
        nx_s: int, 
        ny_s: int, 
        scan_ori: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Creates shift indices based on the scanning orientation sequence.

    Args:
        nx_s (int): Scanner steps along x.
        ny_s (int): Scanner steps along y.
        scan_ori (str): Scan orientation string.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Flattened x and y shift indices.
    """
    x_start = 0
    x_stop = nx_s 
    x_steps = 1 

    y_start = 0 
    y_stop = ny_s 
    y_steps = 1

    x_range = np.arange(x_start, x_stop, x_steps, dtype=int)
    y_range = np.arange(y_start, y_stop, y_steps, dtype=int)

    if scan_ori[1] == "y":
        ys, xs = np.meshgrid(y_range, x_range) 
    else: 
        xs, ys = np.meshgrid(x_range, y_range)

    xs = -xs if scan_ori.find("-x") != -1 else xs 
    ys = -ys if scan_ori.find("-y") != -1 else ys

    return xs.flatten(), ys.flatten()


def get_1d_indices(
        nx_c: int, 
        ny_c: int,
        nx_s: int, 
        ny_s: int, 
        scan_ori: str
) -> np.ndarray:
    """
    Calculates the final 1D index mapping for vectorized super-array updates.

    Args:
        nx_c (int): Number of foci along x.
        ny_c (int): Number of foci along y.
        nx_s (int): Scanner steps along x.
        ny_s (int): Scanner steps along y.
        scan_ori (str): Scan orientation string.

    Returns:
        np.ndarray: A 2D mapping of (scan_steps, foci_total) to flat 1D indices.
    """
    
    xb, yb = _get_bases(nx_c, ny_c, nx_s, ny_s, scan_ori)    
    xb = xb.reshape(1, 1, nx_c)
    yb = yb.reshape(1, ny_c, 1)

    xs, ys = _get_shifts(nx_s, ny_s, scan_ori)
    xs = xs.reshape(nx_s * ny_s, 1, 1)
    ys = ys.reshape(nx_s * ny_s, 1, 1)

    frame_inds = (yb + ys) * (nx_s * nx_c) + (xb + xs) 

    return frame_inds.reshape((nx_s * ny_s, nx_c * ny_c))

def get_orientation(
        nx_c: int, 
        ny_c: int,
        nx_s: int, 
        ny_s: int, 
        proc_pixels: np.ndarray
) -> str: 
    """
    Determines the scanning orientation for the provided processed pixels.

    Args:
        nx_c (int): Number of foci along x.
        ny_c (int): Number of foci along y.
        nx_s (int): Scanner steps along x.
        ny_s (int): Scanner steps along y.
        scan_ori (str): Scan orientation string.

    Returns:
        str: The determined scan orientation in the form +-x+-y or +-y+-x.
    """
    rec_x = nx_c * nx_s
    rec_y = ny_c * ny_s 
    rec_img = np.zeros((rec_y * rec_x), dtype=np.float32)

    orients = ("+x+y", "+x-y", "-x+y", "-x-y", "+y+x", "+y-x", "-y+x", "-y-x")
    score_arr = np.zeros((len(orients)), dtype=float)
    
    for i in range(len(orients)):
        frame_inds = get_1d_indices(nx_c, ny_c, nx_s, ny_s, scan_ori=orients[i])
        rec_img[frame_inds.flatten()] = proc_pixels.flatten()
        
        # total variation
        dx = np.abs(np.diff(rec_img.reshape((rec_y, rec_x)), axis=1), dtype=float)
        dy = np.abs(np.diff(rec_img.reshape((rec_y, rec_x)), axis=0), dtype=float)
        sum = np.sum(dx) + np.sum(dy)
        
        score_arr[i] = sum

    return orients[np.argmin(score_arr)]
    