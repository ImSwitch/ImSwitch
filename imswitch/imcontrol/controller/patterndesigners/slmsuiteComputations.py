"""
slmsuite-based CGH computations.

First integration step:
- Uses slmsuite CompressedSpotHologram for vectorized spot targets.
- Uses a simulated FourierSLM as a computational scaffold.
- Returns the same complex SLM field format as the legacy CGH backend:
      np.exp(1j * phase)
"""

import traceback
import numpy as np


def _as_pitch_tuple(pixel_size_um, default=12.5):
    """
    slmsuite expects SLM pixel pitch as (pitch_x_um, pitch_y_um).
    ImSwitch usually stores one scalar pixel size.
    """
    if pixel_size_um is None:
        return (float(default), float(default))

    if isinstance(pixel_size_um, (tuple, list, np.ndarray)):
        if len(pixel_size_um) >= 2:
            return (float(pixel_size_um[0]), float(pixel_size_um[1]))
        if len(pixel_size_um) == 1:
            return (float(pixel_size_um[0]), float(pixel_size_um[0]))

    return (float(pixel_size_um), float(pixel_size_um))


def compressed_spot_hologram(
    target,
    comput_params=None,
    pixel_size_um=None,
    previous_pattern=None,
):
    """
    Compute a CGH for a vectorized spot target using slmsuite.

    Parameters
    ----------
    target:
        Target object exposing:
            target.spot_vectors_kxy : np.ndarray, shape (2, N)
            target.spot_amp         : np.ndarray, shape (N,)
            target.array            : preview array, used only for output shape

    comput_params : dict
        Reuses existing cgh_computation params where possible.
        Currently used keys:
            n_iterations
        Optional non-UI keys:
            slmsuite_method
            slmsuite_cuda
            slmsuite_verbose
            slmsuite_f_eff
            slmsuite_theta

    pixel_size_um : float or tuple
        SLM pixel size in microns.

    previous_pattern:
        Kept for API symmetry. Not used in this first minimal version.

    Returns
    -------
    field_slm : np.ndarray
        Complex SLM field, exp(1j * phase), shape (height, width)

    performances : list
        Empty list for now; slmsuite stats can be wired later.

    msg : str
        Optional warning/info message.

    err : str or None
        Traceback string if failed.
    """

    comput_params = comput_params or {}

    try:
        from slmsuite.hardware.slms.simulated import SimulatedSLM
        from slmsuite.hardware.cameras.simulated import SimulatedCamera
        from slmsuite.hardware.cameraslms import FourierSLM
        from slmsuite.holography.algorithms import CompressedSpotHologram
    except Exception:
        msg = (
            "Could not import slmsuite. Make sure slmsuite and a compatible "
            "CuPy/CUDA package are installed in the ImSwitch environment."
        )
        return None, None, msg, traceback.format_exc()

    try:
        spot_vectors = getattr(target, "spot_vectors_kxy", None)
        if spot_vectors is None:
            raise ValueError("Target does not expose spot_vectors_kxy.")

        spot_vectors = np.asarray(spot_vectors, dtype=np.float32)
        if spot_vectors.ndim != 2 or spot_vectors.shape[0] != 2:
            raise ValueError(
                f"spot_vectors_kxy must have shape (2, N), got {spot_vectors.shape}"
            )

        spot_amp = getattr(target, "spot_amp", None)
        if spot_amp is not None:
            spot_amp = np.asarray(spot_amp, dtype=np.float32)

        if getattr(target, "array", None) is not None:
            height, width = target.array.shape
        elif getattr(target, "section_size", None) is not None:
            height, width = target.section_size
        else:
            raise ValueError("Cannot infer target/section shape.")

        height = int(height)
        width = int(width)

        # slmsuite SimulatedSLM takes resolution as (width, height),
        # while numpy arrays are (height, width).
        pitch_um = _as_pitch_tuple(pixel_size_um)

        slm = None
        cam = None

        try:
            slm = SimulatedSLM((width, height), pitch_um=pitch_um)
            slm.set_source_analytic(sim=True)
            slm.set_source_analytic()

            # Camera is not used for experimental feedback here.
            # It is only needed to create the FourierSLM object required by
            # CompressedSpotHologram.
            cam = SimulatedCamera(
                slm,
                (width, height),
                pitch_um=(4, 4),
                gain=200,
            )

            fs = FourierSLM(cam, slm)

            # Analytic Fourier calibration scaffold.
            # For basis="kxy" and no camera feedback, this is mostly structural.
            f_eff = float(comput_params.get("slmsuite_f_eff", 80000.0))
            theta = float(comput_params.get("slmsuite_theta", 0.0))
            M, b = fs.fourier_calibration_build(f_eff=f_eff, theta=theta)
            cam.set_affine(M, b)
            fs.fourier_calibrate_analytic(M, b)

            method = comput_params.get("slmsuite_method", "WGS-Leonardo")
            maxiter = int(comput_params.get("n_iterations", 50))
            cuda = bool(comput_params.get("slmsuite_cuda", True))
            verbose = bool(comput_params.get("slmsuite_verbose", False))

            hologram = CompressedSpotHologram(
                spot_vectors=spot_vectors,
                basis="kxy",
                spot_amp=spot_amp,
                cameraslm=fs,
                cuda=cuda,
            )

            cuda_after_init = bool(getattr(hologram, "cuda", False))

            hologram.optimize(
                method=method,
                maxiter=maxiter,
                verbose=verbose,
            )

            cuda_after_opt = bool(getattr(hologram, "cuda", False))

            phase = hologram.get_phase()
            field_slm = np.exp(1j * phase).astype(np.complex128)

            # msg = (
            #     f"Computed with slmsuite CompressedSpotHologram "
            #     f"({method}, maxiter={maxiter}, "
            #     f"cuda init={cuda_after_init}, cuda final={cuda_after_opt})."
            # )
            msg=None

            performances = []
            return field_slm, performances, msg, None

        finally:
            # Keep cleanup explicit, like in your directSummation.py test.
            try:
                if cam is not None:
                    cam.close()
            except Exception:
                pass

            try:
                if slm is not None:
                    slm.close()
            except Exception:
                pass

    except Exception:
        return None, None, str(traceback.format_exc()), traceback.format_exc()