"""
Direct-summation CGH backend for vectorized spot targets.

Purpose
-------
Small internal replacement for the slmsuite CompressedSpotHologram test path.

It supports:
    - vectorized floating-point spot coordinates, shape (2, N)
    - optional CuPy acceleration
    - weighted spot-amplitude feedback inside the iterative computation
    - same return format as cghComputations.gerchberg_saxton()

It intentionally does NOT support:
    - camera feedback
    - FourierSLM objects
    - slmsuite hardware abstractions
    - Zernike-per-spot corrections

Coordinate convention
---------------------
The input spot_vectors_kxy are interpreted as dimensionless k-space direction
coordinates.

The SLM phase term is:

    exp(± i 2π * (pixel_size_um / wavelength_um) * (kx*x + ky*y))

If pixel_size_um or wavelength_nm is missing, the scale falls back to 1.0.

This is meant to be close to the physical phase-ramp convention used by SLM
steering:
    phase = 2π / lambda * x_physical * kx
"""

import traceback
import numpy as np


def direct_spot_wgs_from_target(
    target,
    comput_params=None,
    previous_pattern=None,
    pixel_size_um=None,
    wavelength_nm=None,
):
    """
    Convenience wrapper for ImSwitch Target objects.

    Parameters
    ----------
    target:
        Target object exposing:
            target.spot_vectors_kxy : np.ndarray, shape (2, N)
            target.spot_amp         : np.ndarray, shape (N,), optional
            target.section_size     : tuple, computation shape as (height, width)
            target.array            : np.ndarray, fallback preview array for shape

    comput_params : dict
        Reuses the existing CGH computation params from the widget:
            n_iterations
            weighted_gs
            quad_phase
            quad_phase_coeff

        Additional optional keys, not yet exposed in the UI:
            cuda
            direct_cuda
            direct_kxy_scale
            direct_sign
            direct_feedback_exponent
            direct_seed
            direct_verbose
            direct_min_weight_update
            direct_max_weight_update

    previous_pattern:
        Previous phase or complex field used as initialization.

    pixel_size_um:
        SLM pixel size in microns. Can be scalar or (x, y).

    wavelength_nm:
        Wavelength in nm.

    Returns
    -------
    field_slm, performances, msg, err
    """

    comput_params = comput_params or {}

    spot_vectors_kxy = getattr(target, "spot_vectors_kxy", None)
    if spot_vectors_kxy is None:
        return None, None, getattr(
            target,
            "missing_calibration_message",
            "Target does not expose spot_vectors_kxy.",
        ), None

    spot_amp = getattr(target, "spot_amp", None)

    if getattr(target, "section_size", None) is not None:
        shape = target.section_size
    elif getattr(target, "array", None) is not None:
        shape = target.array.shape
    else:
        return None, None, "Cannot infer target shape.", None

    print("shape: ", shape)

    return direct_spot_wgs(
        spot_vectors_kxy=spot_vectors_kxy,
        shape=shape,
        spot_amp=spot_amp,
        previous_pattern=previous_pattern,
        pixel_size_um=pixel_size_um,
        wavelength_nm=wavelength_nm,
        **comput_params,
    )


def direct_spot_wgs(
    spot_vectors_kxy,
    shape,
    spot_amp=None,
    n_iterations=50,
    weighted_gs=True,
    initial_phase=None,
    previous_pattern=None,
    quad_phase=False,
    quad_phase_coeff=None,
    phase_fixing=False,
    phase_fixing_value=20,
    cuda=True,
    direct_cuda=None,
    direct_kxy_scale=None,
    direct_sign=-1,
    direct_feedback_exponent=0.8,
    direct_seed=1,
    direct_verbose=False,
    direct_min_weight_update=0.2,
    direct_max_weight_update=5.0,
    direct_free_gpu_memory=False,
    pixel_size_um=None,
    wavelength_nm=None,
    **unused_kwargs,
):
    """
    Compute a phase-only hologram for arbitrary spot coordinates by direct
    summation / nonuniform Fourier projection.

    Parameters
    ----------
    spot_vectors_kxy : np.ndarray, shape (2, N)
        Spot coordinates:
            spot_vectors_kxy[0, :] = kx
            spot_vectors_kxy[1, :] = ky

    shape : tuple
        Output SLM shape as (height, width).

    spot_amp : np.ndarray, shape (N,), optional
        Target spot amplitudes. If None, all spots have amplitude 1.

    n_iterations : int
        Number of WGS iterations.

    weighted_gs : bool
        If True, updates per-spot weights to improve uniformity.

    previous_pattern : np.ndarray, optional
        Previous phase or complex field used as initialization.

    direct_kxy_scale : None, float, or tuple
        If None:
            uses pixel_size_um / wavelength_um when available.
        If float:
            same scale for x and y.
        If tuple:
            (scale_x, scale_y).

    direct_sign : int or float
        Sign convention for forward projection. If the output is mirrored
        relative to the slmsuite result, try changing this from -1 to +1.

    Returns
    -------
    field_slm : np.ndarray
        Complex field, exp(1j * phase), shape (height, width)

    performances : list
        List of tuples:
            (efficiency_proxy, uniformity, normalized_std)

    msg : str
        Info/warning message.

    err : str or None
        Traceback if failed.
    """

    try:
        h, w = _validate_shape(shape)

        spot_vectors_kxy = np.asarray(spot_vectors_kxy, dtype=np.float32)
        if spot_vectors_kxy.ndim != 2 or spot_vectors_kxy.shape[0] != 2:
            raise ValueError(
                f"spot_vectors_kxy must have shape (2, N), got {spot_vectors_kxy.shape}"
            )

        n_spots = int(spot_vectors_kxy.shape[1])
        if n_spots <= 0:
            raise ValueError("spot_vectors_kxy contains no spots.")

        if spot_amp is None:
            spot_amp = np.ones(n_spots, dtype=np.float32)
        else:
            spot_amp = np.asarray(spot_amp, dtype=np.float32)

        if spot_amp.shape != (n_spots,):
            raise ValueError(
                f"spot_amp must have shape ({n_spots},), got {spot_amp.shape}"
            )

        spot_amp = np.maximum(spot_amp, 0).astype(np.float32)
        if np.max(spot_amp) <= 0:
            raise ValueError("spot_amp must contain at least one positive value.")

        # Existing widget uses 'cuda' nowhere explicitly, but allow both names.
        use_cuda = bool(cuda if direct_cuda is None else direct_cuda)
        xp, using_cuda, backend_msg = _get_array_module(use_cuda)

        dtype_complex = xp.complex64
        dtype_float = xp.float32

        kx = xp.asarray(spot_vectors_kxy[0, :], dtype=dtype_float)
        ky = xp.asarray(spot_vectors_kxy[1, :], dtype=dtype_float)
        amp_target = xp.asarray(spot_amp, dtype=dtype_float)
        amp_target = amp_target / (xp.mean(amp_target) + 1e-12)

        scale_x, scale_y = _resolve_kxy_scale(
            direct_kxy_scale=direct_kxy_scale,
            pixel_size_um=pixel_size_um,
            wavelength_nm=wavelength_nm,
        )

        scale_x = dtype_float(scale_x)
        scale_y = dtype_float(scale_y)

        # Centered SLM coordinates in pixels.
        x = xp.asarray(np.arange(w, dtype=np.float32) - (w - 1) / 2, dtype=dtype_float)
        y = xp.asarray(np.arange(h, dtype=np.float32) - (h - 1) / 2, dtype=dtype_float)

        sign = dtype_float(direct_sign)
        twopi = dtype_float(2 * np.pi)

        # Separable nonuniform Fourier basis.
        #
        # Forward:
        #   E_m = sum_y sum_x U[y,x] * exp(sign*i*2π*(kx*x + ky*y))
        #
        # Backward:
        #   U[y,x] = sum_m E_m * exp(-sign*i*2π*(kx*x + ky*y))
        #
        # If sign=-1, this is the common forward-minus / backward-plus convention.
        Ex_forward = xp.exp(
            1j * sign * twopi * (kx[:, None] * scale_x) * x[None, :]
        ).astype(dtype_complex)

        Ey_forward = xp.exp(
            1j * sign * twopi * (ky[:, None] * scale_y) * y[None, :]
        ).astype(dtype_complex)

        Ex_backward = xp.conj(Ex_forward)
        Ey_backward = xp.conj(Ey_forward)

        phase_slm = _initial_phase(
            shape=(h, w),
            xp=xp,
            previous_pattern=previous_pattern,
            initial_phase=initial_phase,
            quad_phase=quad_phase,
            quad_phase_coeff=quad_phase_coeff,
            seed=direct_seed,
            dtype_float=dtype_float,
        )

        weights = xp.ones(n_spots, dtype=dtype_float)
        source_amp = xp.ones((h, w), dtype=dtype_float)

        performances = []
        eps = dtype_float(1e-9)
        feedback_exponent = dtype_float(direct_feedback_exponent)

        min_update = dtype_float(direct_min_weight_update)
        max_update = dtype_float(direct_max_weight_update)

        for iteration in range(int(n_iterations)):
            # SLM field.
            U = source_amp * xp.exp(1j * phase_slm).astype(dtype_complex)

            # Forward direct summation at arbitrary spot coordinates.
            #
            # tmp[y, m] = sum_x U[y, x] * Ex_forward[m, x]
            tmp = U @ Ex_forward.T

            # spot_field[m] = sum_y tmp[y, m] * Ey_forward[m, y]
            spot_field = xp.sum(tmp.T * Ey_forward, axis=1)

            measured_amp = xp.abs(spot_field).astype(dtype_float)
            measured_phase = xp.angle(spot_field).astype(dtype_float)

            # Performance diagnostics.
            I = measured_amp**2
            I_mean = xp.mean(I)
            I_max = xp.max(I)
            I_min = xp.min(I)

            efficiency_proxy = xp.mean(I / (I_max + eps))
            uniformity = 1 - (I_max - I_min) / (I_max + I_min + eps)
            std = xp.std(I) / (I_mean + eps)

            performances.append(
                (
                    float(_to_numpy_scalar(efficiency_proxy, using_cuda)),
                    float(_to_numpy_scalar(uniformity, using_cuda)),
                    float(_to_numpy_scalar(std, using_cuda)),
                )
            )

            if direct_verbose:
                print(
                    f"Direct WGS iter {iteration + 1}/{n_iterations}: "
                    f"uniformity={performances[-1][1]:.4f}, "
                    f"std={performances[-1][2]:.4f}"
                )

            # Weighted-GS update on spot weights.
            if weighted_gs:
                measured_rel = measured_amp / (xp.mean(measured_amp) + eps)
                desired_rel = amp_target / (xp.mean(amp_target) + eps)

                update = (desired_rel / (measured_rel + eps)) ** feedback_exponent
                update = xp.clip(update, min_update, max_update)

                weights *= update
                weights /= xp.mean(weights) + eps

            # Enforce target amplitudes only at the vectorized spots.
            enforced_spots = (
                weights
                * amp_target
                * xp.exp(1j * measured_phase).astype(dtype_complex)
            )

            # Back-propagate from spots to SLM plane.
            #
            # A[y, m] = Ey_backward[m, y] * enforced_spots[m]
            A = Ey_backward.T * enforced_spots[None, :]

            # U_back[y, x] = sum_m A[y, m] * Ex_backward[m, x]
            U_back = A @ Ex_backward

            # Phase-only constraint.
            phase_slm = xp.angle(U_back).astype(dtype_float)

        field = xp.exp(1j * phase_slm).astype(dtype_complex)

        if using_cuda:
            field_np = field.get().astype(np.complex128)
            if direct_free_gpu_memory:
                try:
                    import cupy as cp
                    cp.get_default_memory_pool().free_all_blocks()
                except Exception:
                    pass
        else:
            field_np = np.asarray(field, dtype=np.complex128)

        msg = (
            f"Computed with internal direct-summation WGS "
            f"({backend_msg}, spots={n_spots}, shape={h}x{w}, "
            f"iterations={int(n_iterations)}, "
            f"kxy_scale=({float(scale_x):.6g}, {float(scale_y):.6g}), "
            f"sign={float(sign):.0f})."
        )

        # phase_fixing is accepted for compatibility with the existing UI,
        # but intentionally ignored in this first direct-summation backend.
        if phase_fixing:
            msg += " Note: phase_fixing is ignored by cghDirectSummation."

        return field_np, performances, msg, None

    except Exception as e:
        return None, None, str(e), traceback.format_exc()


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _validate_shape(shape):
    if shape is None or len(shape) != 2:
        raise ValueError(f"shape must be (height, width), got {shape}")

    h, w = int(shape[0]), int(shape[1])

    if h <= 0 or w <= 0:
        raise ValueError(f"Invalid shape: {shape}")

    return h, w


def _get_array_module(use_cuda):
    if not use_cuda:
        return np, False, "NumPy CPU"

    try:
        import cupy as cp

        # Force a tiny allocation to catch broken CUDA contexts early.
        _ = cp.zeros((1,), dtype=cp.float32)
        return cp, True, "CuPy GPU"

    except Exception as e:
        # Fallback is useful for debugging, but can be slow.
        return np, False, f"NumPy CPU fallback; CuPy unavailable or failed: {e}"


# def _resolve_kxy_scale(direct_kxy_scale=None, pixel_size_um=None, wavelength_nm=None):
#     """
#     Return (scale_x, scale_y).

#     If direct_kxy_scale is provided, use it directly.
#     Otherwise use pixel_size_um / wavelength_um when available.
#     """

#     if direct_kxy_scale is not None:
#         if isinstance(direct_kxy_scale, (tuple, list, np.ndarray)):
#             if len(direct_kxy_scale) >= 2:
#                 return float(direct_kxy_scale[0]), float(direct_kxy_scale[1])
#             if len(direct_kxy_scale) == 1:
#                 s = float(direct_kxy_scale[0])
#                 return s, s

#         s = float(direct_kxy_scale)
#         return s, s

#     if pixel_size_um is None or wavelength_nm is None:
#         return 1.0, 1.0

#     wavelength_um = float(wavelength_nm) / 1000.0
#     if wavelength_um <= 0:
#         return 1.0, 1.0

#     if isinstance(pixel_size_um, (tuple, list, np.ndarray)):
#         if len(pixel_size_um) >= 2:
#             return float(pixel_size_um[0]) / wavelength_um, float(pixel_size_um[1]) / wavelength_um
#         if len(pixel_size_um) == 1:
#             s = float(pixel_size_um[0]) / wavelength_um
#             return s, s

#     s = float(pixel_size_um) / wavelength_um
#     return s, s

def _resolve_kxy_scale(direct_kxy_scale=None, pixel_size_um=None, wavelength_nm=None):
    """
    Return (scale_x, scale_y).

    Convention:
        spot_vectors_kxy are cycles per SLM pixel.

    Therefore the direct-summation phase is:
        exp(± i 2π * (kx*x + ky*y))

    pixel_size_um and wavelength_nm are intentionally ignored here.
    They may be kept in the function signature for backward compatibility.
    """

    if direct_kxy_scale is not None:
        if isinstance(direct_kxy_scale, (tuple, list, np.ndarray)):
            if len(direct_kxy_scale) >= 2:
                return float(direct_kxy_scale[0]), float(direct_kxy_scale[1])
            if len(direct_kxy_scale) == 1:
                s = float(direct_kxy_scale[0])
                return s, s

        s = float(direct_kxy_scale)
        return s, s

    return 1.0, 1.0

def _initial_phase(
    shape,
    xp,
    previous_pattern=None,
    initial_phase=None,
    quad_phase=False,
    quad_phase_coeff=None,
    seed=1,
    dtype_float=None,
):
    h, w = shape
    dtype_float = dtype_float or xp.float32

    def valid_shape(arr):
        return arr is not None and tuple(arr.shape) == (h, w)

    if previous_pattern is not None:
        prev = np.asarray(previous_pattern)

        if valid_shape(prev):
            if np.iscomplexobj(prev):
                phase = np.angle(prev).astype(np.float32)
            else:
                # In your current controller, previous_pattern may already be
                # np.angle(complex_field), so treat real arrays as phase.
                phase = prev.astype(np.float32)

            return xp.asarray(phase, dtype=dtype_float)

    if initial_phase is not None:
        init = np.asarray(initial_phase)

        if valid_shape(init):
            if np.iscomplexobj(init):
                phase = np.angle(init).astype(np.float32)
            else:
                phase = init.astype(np.float32)

            return xp.asarray(phase, dtype=dtype_float)

    if quad_phase:
        coeff = 0.0 if quad_phase_coeff is None else float(quad_phase_coeff)

        x = np.arange(w, dtype=np.float32) - (w - 1) / 2
        y = np.arange(h, dtype=np.float32) - (h - 1) / 2
        X, Y = np.meshgrid(x, y)

        phase = coeff * (X**2 + Y**2)
        phase = ((phase + np.pi) % (2 * np.pi)) - np.pi

        return xp.asarray(phase, dtype=dtype_float)

    rng = np.random.default_rng(int(seed))
    phase = rng.random((h, w), dtype=np.float32) * 2 * np.pi - np.pi

    return xp.asarray(phase, dtype=dtype_float)


def _to_numpy_scalar(value, using_cuda):
    if using_cuda:
        return value.get()
    return value
