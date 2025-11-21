"""
Computer Generated Holograms (CGH) using Gerchberg-Saxton algorithm and variants.
"""

import numpy as np
import matplotlib.pyplot as plt


def gerchberg_saxton(target, n_iterations=30, phase_fixing=False, phase_fixing_value=20, 
                     weighted_gs=True, initial_phase=None):
    """ 
    Performs the (weighted) Gerchberg-Saxton algorithm with optional cooperative stop.

    Args:
        target: np.array - dtype(np.uint8)
            image target
        n_iterations: int, default=30
            number of iterations performed
        phase_fixing: bool, default=False
            whether to fix the phase in the image plane after `phase_fixing_value` iterations
        weighted_gs: bool, default=True
            whether to use weighted version of Gerchberg-Saxton algorithm
        initial_phase: np.array, default=None
            initial guess for the slm phase

    Returns:
        field_slm: 2D array of complex amplitude exp(1j*phase) with phase between -pi and pi.
        performances: list of performances = [(efficiency, uniformity, std)] for each iteration.
        msg: str, error message if any.
    """
    size = target.shape

    if len(size) != 2:
        msg = "Target must be a 2D array."
        return None, None, msg

    target = normalize(target)
    performances = []

    u = np.zeros(size, dtype=complex)
    v = np.zeros(size, dtype=complex)
    weights = np.ones(size , dtype=float)
    source = np.ones(size)

    if initial_phase is None:
        phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
    else:
        if initial_phase.shape != size:
            msg = "Initial phase shape does not match target shape."
            return None, None, msg
        phase_slm = initial_phase

    try: 
        for k in range(n_iterations):

            print(f"\033[1A \x1b[2K GSW iteration number: {k+1}")  

            u = source * np.exp(1j*phase_slm)
            v = np.fft.fft2(u)
            v = np.fft.fftshift(v)

            amplitude = np.abs(v)

            if (phase_fixing and k < phase_fixing_value) or not phase_fixing:
                phase = np.angle(v)

            I = amplitude**2
            signal = normalize(I)

            if weighted_gs:
                weights[target != 0] = np.sqrt(target[target != 0] / signal[target != 0]) * weights[target != 0]
                v = weights * np.sqrt(target) * np.exp(1j*phase)
            else:
                v = np.sqrt(target) * np.exp(1j*phase)

            v = np.fft.ifftshift(v)
            u = np.fft.ifft2(v)
            phase_slm = np.angle(u)

            performances.append(eval_performances(signal, target))

    except Exception as e:
        msg = str(e)
        return None, None, msg

    field_slm = np.exp(1j*phase_slm)
    return field_slm, performances, None

        



def simulate_propagation_fft(cgh_pattern, padding=True, pad_size = 2048):
    """Simulate propagation of CGH pattern to sample plane using FFT.
    Expects cgh_pattern to be a 2D array of complex values (SLM plane).
    if padding: pads the input to max_pad size with zeros before propagation and then crops back.
    Returns normalized intensity pattern at sample plane."""

    if padding and pad_size is not None:
        h,w = cgh_pattern.shape
        pad_y = pad_size - h
        pad_x = pad_size - w
        if pad_x < 0 or pad_y < 0:
            padding = False
        else:
            cgh_pattern = np.pad(
                cgh_pattern,
                (
                    (pad_y // 2, (pad_y + 1) // 2),
                    (pad_x // 2, (pad_x + 1) // 2)
                ),
                mode='constant'
            )
    else:
        padding = False

    field_slm = cgh_pattern
    field_sample = np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(field_slm)))
    intensity_sample = np.abs(field_sample) ** 2
    intensity_sample = intensity_sample / np.max(intensity_sample)  # Normalize

    if padding:
        # crop back to original size
        h,w = cgh_pattern.shape
        start_y = (h - (h - pad_y)) // 2
        start_x = (w - (w - pad_x)) // 2
        intensity_sample = intensity_sample[start_y:start_y + (h - pad_y), start_x:start_x + (w - pad_x)]

    return intensity_sample



def normalize(array):
    """ Normalize array between [0; 1] """
    return (array - np.min(array)) / (np.max(array) - np.min(array))

def eval_performances(signal, target):
    """ Evaluate the performances of GS algorithm """
    I = signal[target!=0]
    efficiency = np.sum(I) / np.sum(signal)
    Imax = np.max(I)
    Imin = np.min(I)
    uniformity = 1 - (Imax - Imin) / (Imax + Imin) # 1 - (max(I) - min(I)) / (max(I) + min(I))
    Var = np.mean((I - np.mean(I)) ** 2)
    std = np.sqrt(Var) / np.mean(I) # sqrt(<(I - <I>) ^ 2>) / <I>
    # std = np.sqrt(np.mean((target[target!=0] - I) ** 2)) / np.mean(I)
    return efficiency, uniformity, std




# --- Targets --- #

def create_target(target_type, **target_params):
    """Create target pattern for CGH generation."""
    if target_type == "multi_foci":
        return focal_array(**target_params)
    elif target_type == "bfp_spots":
        return bfp_spots(**target_params)
    else:
        raise ValueError(f"Unknown target type '{target_type}'.")


def focal_array(target_size_x, target_size_y, n_foci, period):
    """Create a matrix of focal points arranged on a grid.

    Args:
        target_size_x (int): width of the target image in pixels.
        target_size_y (int): height of the target image in pixels.
        n_foci (int): number of points along each axis (n x n total).
        period (int): spacing between points, in pixels.

    Returns:
        np.ndarray: array of shape (target_size_y, target_size_x) 
                    with focal points (ones) at grid positions.
    """
    # Build one focal point
    focal = np.zeros((period, period))
    focal[period // 2, period // 2] = 1

    # Tile the pattern to create the foci grid
    grid = np.tile(focal, (n_foci, n_foci))

    # padding
    pad_y = target_size_y - grid.shape[0]
    pad_x = target_size_x - grid.shape[1]
    if pad_x < 0 or pad_y < 0:
        raise ValueError("Target size must be larger than n_foci * period in both dimensions.")
    padded = np.pad(
        grid,
        (
            (pad_y // 2, (pad_y + 1) // 2),
            (pad_x // 2, (pad_x + 1) // 2)
        ),
        mode='constant'
    )
    return padded


def bfp_spots(**kwargs):
    """Create back focal plane spots target pattern."""
    raise NotImplementedError("bfp_spots target pattern is not yet implemented.")



# ------- Testing-------- #
if __name__ == "__main__":
    
    target = focal_array(target_size_x=500, target_size_y=512, n_foci=50, period=6)
    plt.imshow(target, cmap='gray')
    plt.show()