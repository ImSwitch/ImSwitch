"""
Computer Generated Holograms (CGH) using Gerchberg-Saxton algorithm and variants.
"""

import numpy as np
import matplotlib.pyplot as plt
import traceback
import numpy as np
import traceback


def gerchberg_saxton(target, n_iterations=30, phase_fixing=False, phase_fixing_value=20, 
                     weighted_gs=True, initial_phase=None, previous_pattern=None, 
                     quad_phase=False, quad_phase_coeff=None,
                     relaxed_constraint=False, relax_factor=1.0, **kwargs):
    
    size = target.shape
    if len(size) != 2:
        return None, None, "Target must be a 2D array.", None

    target_max = np.max(target)
    if target_max == 0: target_max = 1
    target_norm = target / target_max
    
    mask_signal = target_norm > 1e-6
    mask_noise = ~mask_signal
    
    performances = []
    source_amp = np.ones(size) 
    weights = np.ones(size, dtype=float)

    msg = ""
    err = None
    
    if previous_pattern is not None and previous_pattern.shape == size:
        phase_slm = np.angle(previous_pattern)
    elif quad_phase:
        if quad_phase_coeff is None:
            phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
            msg = "Warning: Quadratic phase selected but no coeff provided. Using random."
        else:
            ny, nx = size
            y = np.arange(ny) - ny // 2
            x = np.arange(nx) - nx // 2
            X, Y = np.meshgrid(x, y)
            phase_slm = quad_phase_coeff * (X**2 + Y**2)
    elif initial_phase is not None and initial_phase.shape == size:
        phase_slm = initial_phase
    else:
        np.random.seed(1)
        phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi

    try: 
        u_slm = source_amp * np.exp(1j * phase_slm)

        for k in range(n_iterations):

            u_target = np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(u_slm)))
            
            A_calc = np.abs(u_target)
            Phi_calc = np.angle(u_target)
            
            E_total_calc = np.sum(A_calc**2)
            E_target_geom = np.sum(target_norm[mask_signal]**2) 
            if E_target_geom == 0: E_target_geom = 1
            
            scale = np.sqrt(E_total_calc / E_target_geom)
            
            A_new = A_calc.copy() 
            
            if weighted_gs:
                signal_intensity = A_calc**2
                current_val = signal_intensity[mask_signal]
                current_val[current_val < 1e-10] = 1e-10
                
                weights[mask_signal] *= np.sqrt(target_norm[mask_signal] * scale**2 / current_val)
                A_new[mask_signal] = weights[mask_signal] * target_norm[mask_signal] * scale
            else:
                A_new[mask_signal] = target_norm[mask_signal] * scale

            if relaxed_constraint:
                A_new[mask_noise] = A_calc[mask_noise] * relax_factor
            else:
                A_new[mask_noise] = 0.0

            u_target_update = A_new * np.exp(1j * Phi_calc)
            u_slm_update = np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(u_target_update)))
            
            phase_slm = np.angle(u_slm_update)
            u_slm = source_amp * np.exp(1j * phase_slm)

    except Exception as e:
        msg = str(e)
        err = traceback.format_exc()
        return None, None, msg, err

    field_slm = np.exp(1j * phase_slm)
    return field_slm, performances, msg, err



# def gerchberg_saxton(target, n_iterations=30, phase_fixing=False, phase_fixing_value=20, 
#                      weighted_gs=True, initial_phase=None, previous_pattern=None, 
#                      quad_phase=False, quad_phase_coeff=None,
#                      relaxed_constraint=False, relax_factor=0.9):
#     """ 
#     Performs the (weighted) Gerchberg-Saxton algorithm with optional cooperative stop
#     and Signal Domain Relaxation (DAF).

#     Args:
#         target: np.array - dtype(np.uint8)
#             image target
#         n_iterations: int, default=30
#             number of iterations performed
#         phase_fixing: bool, default=False
#             whether to fix the phase in the image plane after `phase_fixing_value` iterations
#         weighted_gs: bool, default=True
#             whether to use weighted version of Gerchberg-Saxton algorithm (inside signal region)
#         initial_phase: np.array, default=None
#             initial guess for the slm phase - only used if not using previous_pattern and quad_phase.
#         previous_pattern: np.array, default=None
#             result of previous feedback loop iteration.
#         quad_phase: bool, default = False
#             if true, sets the initial phase as a quadratic phase (lens-like).
#         quad_phase_coeff: float, default = None
#             coefficient for the quadratic phase.
#         relaxed_constraint: bool, default = False
#             If True, enables Signal Domain Relaxation (DAF). Instead of forcing the amplitude 
#             outside the target to 0, it allows it to float, reducing ringing inside the beam.
#         relax_factor: float, default = 0.9
#             Multipler for the amplitude outside the target region when relaxed_constraint is True.
#             Keeps the energy bounded.

#     Returns:
#         field_slm: 2D array of complex amplitude exp(1j*phase)
#         performances: list of performances
#         msg: str, error message
#     """
#     size = target.shape

#     if len(size) != 2:
#         msg = "Target must be a 2D array."
#         return None, None, msg, None

#     # Ensure target is normalized float for calculations
#     # Assuming user has a normalize function, otherwise simple max division:
#     # target = target / np.max(target) 
#     target = normalize(target) 
    
#     performances = []

#     # Pre-calculate boolean mask for the Signal Region (ROI)
#     target_mask = target > 1e-6 # Assumes normalized target, threshold for "inside beam"

#     weights = np.ones(size, dtype=float)
#     source = np.ones(size) # Assuming uniform source amplitude (standard GS)

#     # --- Initialization Logic (Unchanged) ---
#     msg = ""
#     err = None
#     if previous_pattern is not None:
#         if previous_pattern.shape == size:
#             try:
#                 phase_slm = np.angle(previous_pattern)
#             except Exception as e:
#                 msg = f"Error converting previous pattern: {e}\nUsing random phase."
#                 err = traceback.format_exc()
#                 np.random.seed(1)
#                 phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
#         else:
#             msg = f"Shape mismatch. Using random phase."
#             np.random.seed(1)
#             phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi

#     elif quad_phase:
#         if quad_phase_coeff is None:
#             msg = "Quad phase checked but no coeff. Using random phase."
#             np.random.seed(1)
#             phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
#         else:
#             # Assuming quadratic_phase_generator is defined elsewhere
#             phase_slm = quadratic_phase_generator(target.shape[0], target.shape[1], quad_phase_coeff)
    
#     elif initial_phase is not None:
#         if initial_phase.shape != size:
#             msg = "Initial phase shape mismatch. Using random phase."
#             np.random.seed(1)
#             phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
#         else:
#             phase_slm = initial_phase
#     else:
#         np.random.seed(1)
#         phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi

#     # --- Iteration Loop ---
#     try: 
#         for k in range(n_iterations):
            
#             # 1. Forward Propagation
#             u = source * np.exp(1j * phase_slm)
#             v = np.fft.fft2(u)
#             v = np.fft.fftshift(v)

#             # 2. Get Calculated Amplitude & Phase
#             amplitude_calc = np.abs(v)
            
#             if (phase_fixing and k < phase_fixing_value) or not phase_fixing:
#                 phase_calc = np.angle(v)
#             else:
#                 phase_calc = np.angle(v) 

#             # 3. Constraint Application (The modified part)
            
#             # Calculate Intensity for Weighting / Metrics
#             I = amplitude_calc**2
#             signal = normalize(I) # Normalization for weighting feedback
            
#             # A. Update Weights (Inside Signal Region Only)
#             if weighted_gs:
#                 # Avoid division by zero
#                 nonzero_signal = signal[target_mask]
#                 nonzero_signal[nonzero_signal == 0] = 1e-10 
#                 weights[target_mask] = weights[target_mask] * np.sqrt(target[target_mask] / nonzero_signal)

#             # B. Construct New Amplitude
#             total_source_energy = np.sum(amplitude_calc**2)
#             total_target_energy = np.sum(target) # Assuming target is Intensity (0 to 1)
#             scale_factor = np.sqrt(total_source_energy / total_target_energy)
#             new_amplitude = amplitude_calc.copy()

#             if weighted_gs:
#                 new_amplitude[target_mask] = weights[target_mask] * np.sqrt(target[target_mask])
#             else:
#                 new_amplitude[target_mask] = np.sqrt(target[target_mask])
            
#             new_amplitude[target_mask] = np.sqrt(target[target_mask]) * scale_factor

#             if relaxed_constraint:
#                 new_amplitude[~target_mask] = amplitude_calc[~target_mask] * relax_factor # Try 0.9 now
#             else:
#                 new_amplitude[~target_mask] = 0.0
            

#             # 4. Backward Propagation
#             v_update = new_amplitude * np.exp(1j * phase_calc)
            
#             v_update = np.fft.ifftshift(v_update)
#             u_update = np.fft.ifft2(v_update)
            
#             # Update SLM phase for next iteration
#             phase_slm = np.angle(u_update)

#             # Metrics
#             performances.append(eval_performances(signal, target))

#     except Exception as e:
#         msg = str(e)
#         err = traceback.format_exc()
#         return None, None, msg, err

#     field_slm = np.exp(1j * phase_slm)
#     return field_slm, performances, msg, err


# def gerchberg_saxton(target, n_iterations=30, phase_fixing=False, phase_fixing_value=20, 
#                      weighted_gs=True, initial_phase=None,previous_pattern=None, 
#                      quad_phase=False,quad_phase_coeff=None):
#     """ 
#     Performs the (weighted) Gerchberg-Saxton algorithm with optional cooperative stop.

#     Args:
#         target: np.array - dtype(np.uint8)
#             image target
#         n_iterations: int, default=30
#             number of iterations performed
#         phase_fixing: bool, default=False
#             whether to fix the phase in the image plane after `phase_fixing_value` iterations
#         weighted_gs: bool, default=True
#             whether to use weighted version of Gerchberg-Saxton algorithm
#         initial_phase: np.array, default=None
#             initial guess for the slm phase - only used if not using previous_pattern and quad_phase.
#         previous_pattern: np.array, default=None
#             result of previous feedback loop iteration as a complex field. If given, its phase
#             is use as the algo initial phase (overriding arg:`initial_phase`)
#         quad_phase: bool, default = False
#             if true, and no `previous_pattern`, sets the initial phase as a quadratic
#             phase with a coefficient value `quad_phase_coeff`.
#         quad_phase_coeff: float, default = None
#             quad phase value coeffcient, only needed if `quad_phase` is True.
        

#     Returns:
#         field_slm: 2D array of complex amplitude exp(1j*phase) with phase between -pi and pi.
#         performances: list of performances = [(efficiency, uniformity, std)] for each iteration.
#         msg: str, error message if any.
#     """
#     size = target.shape

#     if len(size) != 2:
#         msg = "Target must be a 2D array."
#         return None, None, msg, None

#     target = normalize(target)
#     performances = []

#     u = np.zeros(size, dtype=complex)
#     v = np.zeros(size, dtype=complex)
#     weights = np.ones(size , dtype=float)
#     source = np.ones(size)

#     msg = ""
#     err = None
#     if previous_pattern is not None:
#         if previous_pattern.shape == size:
#             try:
#                 phase_slm = np.angle(previous_pattern)
#                 # print("using previous pattern phase as initial phase")
#             except Exception as e:
#                 msg = f"Error when trying to convert previous pattern field to phase: {e}\nUsing random initial phase instead"
#                 err = traceback.format_exc()
#                 np.random.seed(1)
#                 phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
#         else:
#             msg = f"Previous pattern size {previous_pattern.shape} does not match target {target.shape}). Using random initial phase instead"
#             np.random.seed(1)
#             phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi

#     elif quad_phase:
#         if quad_phase_coeff is None:
#             msg = "Quadratic Phase checked but no coefficient value given. Using random initial pahse instead."
#             np.random.seed(1)
#             phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
#         else:
#             # print("Using quadratic phase with coeff: ", quad_phase_coeff)
#             phase_slm=quadratic_phase_generator(target.shape[0],target.shape[1],quad_phase_coeff)
    
#     elif initial_phase is not None:
#         if initial_phase.shape != size:
#             msg = "Initial phase shape does not match target shape. Using random initial phase instead"
#             np.random.seed(1)
#             phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
#         else:
#             phase_slm = initial_phase
#     else:
#         np.random.seed(1)
#         phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi

#     try: 
#         for k in range(n_iterations):

#             s = f"\033[1A \x1b[2K GSW iteration number: {k+1}"
#             # print(s)

#             u = source * np.exp(1j*phase_slm)
#             v = np.fft.fft2(u)
#             v = np.fft.fftshift(v)

#             amplitude = np.abs(v)

#             if (phase_fixing and k < phase_fixing_value) or not phase_fixing:
#                 phase = np.angle(v)

#             I = amplitude**2
#             signal = normalize(I)

#             if weighted_gs:
#                 weights[target != 0] = np.sqrt(target[target != 0] / signal[target != 0]) * weights[target != 0]
#                 v = weights * np.sqrt(target) * np.exp(1j*phase)
#             else:
#                 v = np.sqrt(target) * np.exp(1j*phase)

#             v = np.fft.ifftshift(v)
#             u = np.fft.ifft2(v)
#             phase_slm = np.angle(u)

#             performances.append(eval_performances(signal, target))

#     except Exception as e:
#         msg = str(e)
#         err = traceback.format_exc()
#         return None, None, msg, err

#     field_slm = np.exp(1j*phase_slm)
#     return field_slm, performances, msg, err

        



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




def quadratic_phase_generator(width: int,height: int,coeff: float):
    """
    Generate a quadratic phase map wrapped to [-pi, pi].

    Parameters
    ----------
    width, height : int
        Dimensions of the phase array.
    coeff : float
        Quadratic coefficient.
    centre : (float, float), optional
        Center of the phase pattern. Defaults to the array center.

    Returns
    -------
    phase : 2D np.ndarray of shape (height, width)
        Quadratic phase wrapped to [-pi, pi].
    """
    x0 = (width - 1) / 2
    y0 = (height - 1) / 2

    # coordinate grid
    x = np.arange(width) - x0
    y = np.arange(height) - y0
    X, Y = np.meshgrid(x, y)

    # quadratic phase
    phase = coeff * (X**2 + Y**2)

    # wrap to [-pi, pi]
    phase_wrapped = (phase + np.pi) % (2 * np.pi) - np.pi

    return phase_wrapped
