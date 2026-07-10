"""
Computer Generated Holograms (CGH) using Gerchberg-Saxton algorithm and variants.
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
import traceback


from ...registries import register_cgh_algorithm

from imswitch.imcommon.model.paramDef import param
from typing import TYPE_CHECKING, Union, Tuple
if TYPE_CHECKING:
    from ..targets import Target

GERCHBERG_SAXTON_PARAMS = [
    param("weighted_gs", True, bool, "Weighted-GS"),
    param("n_iterations", 50, int, "Iterations", min_value=1, max_value=300),
    param("phase_fixing", True, bool, "Phase fixing"),
    param("phase_fixing_value", 30, int, "Phase", min_value=1),
    param("quad_phase", False, bool, "Quad. Init. Phase"),
    param("quad_phase_coeff", 0.004, float, "Coeff"),
]

@register_cgh_algorithm(
    "gerchberg_saxton",
    params=GERCHBERG_SAXTON_PARAMS,
)
def compute(
    target: Union[Target, np.ndarray],
    compute_params: dict=None,
    previous_pattern: np.ndarray =None,
) -> Tuple[np.ndarray, list, str, str]:
    """ 
    Performs the (weighted) Gerchberg-Saxton algorithm with optional cooperative stop.

    Args:
        target: np.array - dtype(np.uint8)
            image target
        comput_params: dict
            computation parameters (see below)
        previous_pattern: np.array, default=None
            result of previous feedback loop iteration as a complex field.If given, its phase
            is use as the algo initial phase (overriding compute_params["initial_phase]"
    
    Allowed compute_params keys:
        n_iterations: int, default=30
            number of iterations performed
        phase_fixing: bool, default=False
            whether to fix the phase in the image plane after `phase_fixing_value` iterations
        weighted_gs: bool, default=True
            whether to use weighted version of Gerchberg-Saxton algorithm
        initial_phase: np.array, default=None
            initial guess for the slm phase - only used if not using previous_pattern and quad_phase.
        quad_phase: bool, default = False
            if true, and no `previous_pattern`, sets the initial phase as a quadratic
            phase with a coefficient value `quad_phase_coeff`.
        quad_phase_coeff: float, default = None
            quad phase value coeffcient, only needed if `quad_phase` is True.
        

    Returns:
        field_slm: 2D array of complex amplitude exp(1j*phase) with phase between -pi and pi.
        performances: list of performances = [(efficiency, uniformity, std)] for each iteration.
        msg: str, error message if any.
    """
    
    weighted_gs = compute_params.get("weighted_gs", True)
    n_iterations = compute_params.get("n_iterations", 30)
    phase_fixing = compute_params.get("phase_fixing", True)
    phase_fixing_value = compute_params.get("phase_fixing_value", 20)
    initial_phase = compute_params.get("initial_phase", None)
    quad_phase = compute_params.get("quad_phase", False)
    quad_phase_coeff = compute_params.get("quad_phase_coeff", None)
    
    if not isinstance(target, np.ndarray):
        try:
            target = target.array
        except AttributeError as exc:
            raise ArithmeticError(
                f"Gerchberg-Saxton algorithm needs a np.ndarray or a " 
                f"valid Target object with a 'array' attribute"
            ) from exc

    size = target.shape

    if len(size) != 2:
        msg = "Target must be a 2D array."
        return None, None, msg, None

    target = normalize(target)
    performances = []

    u = np.zeros(size, dtype=complex)
    v = np.zeros(size, dtype=complex)
    weights = np.ones(size , dtype=float)
    source = np.ones(size)

    msg = ""
    err = None
    if previous_pattern is not None:
        if previous_pattern.shape == size:
            try:
                phase_slm = np.angle(previous_pattern)
                # print("using previous pattern phase as initial phase")
            except Exception as e:
                msg = f"Error when trying to convert previous pattern field to phase: {e}\nUsing random initial phase instead"
                err = traceback.format_exc()
                np.random.seed(1)
                phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
        else:
            msg = f"Previous pattern size {previous_pattern.shape} does not match target {target.shape}). Using random initial phase instead"
            np.random.seed(1)
            phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi

    elif quad_phase:
        if quad_phase_coeff is None:
            msg = "Quadratic Phase checked but no coefficient value given. Using random initial pahse instead."
            np.random.seed(1)
            phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
        else:
            # print("Using quadratic phase with coeff: ", quad_phase_coeff)
            phase_slm=quadratic_phase_generator(target.shape[0],target.shape[1],quad_phase_coeff)
    
    elif initial_phase is not None:
        if initial_phase.shape != size:
            msg = "Initial phase shape does not match target shape. Using random initial phase instead"
            np.random.seed(1)
            phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi
        else:
            phase_slm = initial_phase
    else:
        np.random.seed(1)
        phase_slm = (np.random.rand(*size)) * 2 * np.pi - np.pi

    try: 
        for k in range(n_iterations):

            s = f"\033[1A \x1b[2K GSW iteration number: {k+1}"
            # print(s)

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
        err = traceback.format_exc()
        return None, None, msg, err

    field_slm = np.exp(1j*phase_slm)
    return field_slm, performances, msg, err



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
