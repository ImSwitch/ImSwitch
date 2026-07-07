# patterndesigners/generalParams.py

from ....imcommon.model.paramDef import param

GENERAL_PARAMS = [
    param("wavelength_nm", 488, int, "Wavelength (nm)", min_value=350, max_value=1200),
    param("pupil_radius_px", 0, int, "Pupil Radius (px)", min_value=0),
    param("center_offset_x_px", 0, int, "Center Offset X (px)"),
    param("center_offset_y_px", 0, int, "Center Offset Y (px)"),
]


CORRECTION_PARAMS = [
    param("apply_correction_pattern", True, bool, "Apply correction pattern"),
    param("apply_twopi_value", True, bool, "Apply 2π value correction"),
]


CGH_COMPUTATION_PARAMS = [
    param("weighted_gs", True, bool, "Weighted-GS"),
    param("n_iterations", 50, int, "Iterations", min_value=1, max_value=300),
    param("phase_fixing", True, bool, "Phase fixing"),
    param("phase_fixing_value", 30, int, "Phase", min_value=1),
    param("quad_phase", False, bool, "Quad. Init. Phase"),
    param("quad_phase_coeff", 0.004, float, "Coeff"),
]


CGH_GENERAL_PARAMS = [
    param("active", False, bool, "Use CGH"),
    # target_type is special because choices come from TARGETS_REGISTRY
]