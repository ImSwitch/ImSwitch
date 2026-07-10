# patterndesigners/generalParams.py

from imswitch.imcommon.model.paramDef import param

# --- GENERAL PARAMETERS --- #

GENERAL_PARAMS = [
    param("wavelength_nm", 488, int, "Wavelength (nm)", min_value=350, max_value=1200),
    param("pupil_radius_px", 0, int, "Pupil Radius (px)", min_value=0),
    param("center_offset_x_px", 0, int, "Center Offset X (px)"),
    param("center_offset_y_px", 0, int, "Center Offset Y (px)"),
]

# --- CORRECTION PARAMETERS --- #

CORRECTION_PARAMS = [
    param("apply_correction_pattern", True, bool, "Apply correction pattern"),
    param("apply_twopi_value", True, bool, "Apply 2π value correction"),
]

