import numpy as np
from typing import Union, Dict, Tuple


# --- Coordinates ---
def get_center_coords(args: Dict[str, Union[int, float]]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates a grid pattern based on the parameters gathered from the localizer.
    
    Args:
        num_rows (int): Number of pixels along y-axis in raw frame.
        num_cols (int): Number of pixels along x-axis in raw frame. 
        xp (float): Period along x-axis in pixels from localizer. 
        xo (float): Offset along x-axis in pixels from localizer. 
        yp (float): Period along y-axis in pixels from localizer. 
        yo (float): Offset along y-axis in pixels from localizer.
        nx_c (int): Number of foci along x-axis. 
        ny_c (int): Number of foci along y-axis. 
            
    Returns: 
        Tuple[np.ndarray, np.ndarray]: Tuple containing the flattened grid 
        coordinates (X, Y) respectively.
    """
    xp = args["xp"]
    yp = args["yp"]
    xo = args["xo"]
    yo = args["yo"]    
    
    nx_c = args["nx_c"]
    ny_c = args["ny_c"]
    
    x_stop = xo + (nx_c - 1) * xp 
    y_stop = yo + (ny_c - 1) * yp
    
    X, Y = np.meshgrid(np.linspace(xo, x_stop, nx_c), np.linspace(yo, y_stop, ny_c)) # type: ignore

    return X.flatten(), Y.flatten()

def get_rectangles(
        start_w: float = 0.0, 
        start_h: float = 0.0, 
        num_rects: int = 1, 
        xoff: float = 0.0, 
        yoff: float = 0.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates a series of concentric rectangular coordinate shells.

    Args:
        start_w (float): Initial width of the innermost rectangle.
        start_h (float): Initial height of the innermost rectangle.
        num_rects (int): Number of concentric shells to generate.
        xoff (float): Constant offset to add to all x-coordinates.
        yoff (float): Constant offset to add to all y-coordinates.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Concatenated x and y coordinates of the rectangles.
    """
    all_x = []
    all_y = []
    for i in range(num_rects):
        w = start_w + (i * 2)
        h = start_h + (i * 2)
    
        x_l, x_r = -w/2, w/2
        y_b, y_t = -h/2, h/2
    
        top_x = np.arange(x_l, x_r + 1, 1)
        top_y = np.ones(len(top_x)) * y_t
    
        bot_x = np.arange(x_l, x_r + 1, 1)
        bot_y = np.ones(len(bot_x)) * y_b
    
        side_y = np.arange(y_b + 1, y_t, 1)
    
        right_x = np.ones(len(side_y)) * x_r
        right_y = side_y
    
        left_x = np.ones(len(side_y)) * x_l
        left_y = side_y
    
        all_x.extend([top_x, bot_x, left_x, right_x])
        all_y.extend([top_y, bot_y, left_y, right_y])
    
    final_x = np.concatenate(all_x) + xoff
    final_y = np.concatenate(all_y) + yoff
    
    return final_x, final_y

def get_interp_coords(args: Dict[str, Union[int, float]]) -> Tuple[np.ndarray, np.ndarray]: 
    """
    Generates local interpolation coordinates around each grid focus center.

    Args:
        num_rows (int): Total rows in the frame.
        num_cols (int): Total columns in the frame.
        xp (float): X-axis period.
        xo (float): X-axis offset.
        yp (float): Y-axis period.
        yo (float): Y-axis offset.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Flattened interpolation coordinates clipped to frame boundaries.
    """
    X_c, Y_c = get_center_coords(args)
    X_r, Y_r = get_rectangles(num_rects=6)

    X = X_c.reshape((-1, 1)) + X_r 
    Y = Y_c.reshape((-1, 1)) + Y_r

    X[X < 0] = 0
    X[X > args["num_cols"] - 1] = 0 # Clipped to -1 for safe indexing
    Y[Y < 0] = 0
    Y[Y > args["num_rows"] - 1] = 0

    return X.flatten(), Y.flatten()

# --- Indices ---
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
    if scan_ori.find("+x") != -1:
        x_b = np.arange(0, nx_s*nx_c, step=nx_s, dtype=int)
    else:
        x_b = np.arange((nx_s-1), nx_s*nx_c+(nx_s-1), step=nx_s, dtype=int)
    
    if scan_ori.find("+y") != -1:
        y_b = np.arange(0, ny_s*ny_c, step=ny_s, dtype=int)
    else:
        y_b = np.arange((ny_s-1), ny_s*ny_c+(ny_s-1), step=ny_s, dtype=int)

    return x_b, y_b

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
    if scan_ori[1] == "y": 
        y_s, x_s = np.meshgrid(np.arange(ny_s, dtype=int), np.arange(nx_s, dtype=int))
    else:
        x_s, y_s = np.meshgrid(np.arange(nx_s, dtype=int), np.arange(ny_s, dtype=int))
    
    if scan_ori.find("-x") != -1:
        x_s = -x_s
    
    if scan_ori.find("-y") != -1:
        y_s = -y_s 
    
    return x_s.flatten(), y_s.flatten()

def get_1d_indices(
        args: Dict[str, int],
        scan_ori: str="+x+y"
) -> np.ndarray:
    """
    Calculates the final 1D index mapping for vectorized super-array updates.

    Args:
        nx_c (int): Number of foci along x.
        ny_c (int): Number of foci along y.
        nx_s (int): Scanner steps along x.
        ny_s (int): Scanner steps along y.
        scan_ori (str): Scan orientation string. Defaults to "+x+y".

    Returns:
        np.ndarray: A 2D mapping of (scan_steps, foci_total) to flat 1D indices.
    """
    nx_c = args["nx_c"]
    ny_c = args["ny_c"]
    nx_s = args["nx_s"]
    ny_s = args["ny_s"]
    
    x_b, y_b = _get_bases(nx_c, ny_c, nx_s, ny_s, scan_ori)
    x_s, y_s = _get_shifts(nx_s, ny_s, scan_ori)
    x_b = x_b.reshape(1, 1, nx_c)
    y_b = y_b.reshape(1, ny_c, 1)

    x_s = x_s.reshape(nx_s*ny_s, 1, 1)
    y_s = y_s.reshape(nx_s*ny_s, 1, 1)

    frame_inds = (y_b + y_s) * (nx_s * nx_c) + (x_b + x_s) 

    return frame_inds.reshape((nx_s * ny_s, nx_c * ny_c))