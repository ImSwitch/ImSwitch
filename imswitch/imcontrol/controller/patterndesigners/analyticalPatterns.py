"""
Analytically defined phase patterns (gratings, lenses, etc.).
"""

import matplotlib.pyplot as plt
import numpy as np
from .registries import register_pattern
from .slmSectionCalibration import SLMSectionCalibration
from .paramDef import param
from .converters import PeriodDisplacementConverter
### binary grating ###
@register_pattern("binary_grating", params=[
    param("period_x", 0, int),
    param("period_y", 0, int),
    param("phase_offset",0, float),
    param("duty_x", 0.5, float),
    param("duty_y", 0.5, float),
])
def binary_grating(width, height, period_x, period_y,phase_offset=0, duty_x=0.5, duty_y=0.5,**kwargs):
    """
    1D/2D binary phase grating.
    Produces 0/π phase stripes along X and/or Y directions.
    """
    x = np.arange(width)
    y = np.arange(height)

    if period_x > 0:
        pattern_x = ((x % period_x) < (period_x * duty_x)).astype(float)
    else:
        pattern_x = np.ones(width)

    if period_y > 0:
        pattern_y = ((y % period_y) < (period_y * duty_y)).astype(float)
    else:
        pattern_y = np.ones(height)

    phase = (pattern_y[:, None] * pattern_x[None, :]) * np.pi
    phase += phase_offset
    return np.exp(1j * phase)

### sinusoidal grating ###
@register_pattern("sinusoidal_grating", params=[
    ("period_x", 0, int),
    ("period_y", 0, int),
    ("power_x", 1, int),
    ("power_y", 1, int),
])
def sinusoidal_grating(width, height, period_x, period_y, power_x=0.5, power_y=0.5,**kwargs):
    """
    1D/2D sinusoidal phase grating.
    """
    x = np.arange(width)
    y = np.arange(height)
    X, Y = np.meshgrid(x, y)


    if period_x == 0 and period_y == 0:
        phase = np.zeros(shape=(height,width))
        return np.exp(1j*phase)
    
    phase = np.ones(shape=(height,width))
    if period_x != 0:
        phase *= np.sin(2 * np.pi * X / period_x) ** power_x

    if period_y != 0:
        phase *= np.sin(2 * np.pi * Y / period_y) ** power_y

    return np.exp(1j*phase)



### linear phase (blazed grating) ###
@register_pattern(
    "linear_phase", 
    params=[
        param("period_x", 0, int,min_value=-4000,max_value=4000,
              metric_available=True,metric_label="Displacement X (um)",
              converter=PeriodDisplacementConverter(axis="x")),
        param("period_y", 0, int,min_value=-4000,max_value=4000,
              metric_available=True,metric_label="Displacement Y (um)",
              converter=PeriodDisplacementConverter(axis="y")),
    ]
)
def linear_phase(width, height, period_x, period_y,**kwargs):
    """
    Linear (blazed) phase ramp.
    Periods define the number of pixels for a 2π phase ramp.
    """

    x = np.arange(width)
    y = np.arange(height)
    X, Y = np.meshgrid(x, y)
    
    phase = np.zeros(shape=(height,width))
    if period_x!=0:
        phase += 2 * np.pi * (X / period_x)
    if period_y != 0:
        phase += 2 * np.pi * (Y / period_y)

    phase = np.mod(phase, 2 * np.pi)
    return np.exp(1j * phase)


@register_pattern("linear_phase_metric", params=[
    param("displacement_x_um", 0.0, float),
    param("displacement_y_um", 0.0, float),
])
def linear_phase_metric(width, height, displacement_x_um, displacement_y_um, **kwargs):
    """
    Linear phase ramp defined by requested physical displacement in um.
    """

    calibration = SLMSectionCalibration.from_dict(kwargs.get("section_calibration"))
    if not calibration.is_valid():
        raise ValueError(
            "linear_phase_metric requires a valid SLM section calibration. "
            "Use 'Calibrate linear phase' for this SLM section first."
        )

    kx, ky = calibration.um_to_kxy(displacement_x_um, displacement_y_um)
    x = np.arange(width)
    y = np.arange(height)
    X, Y = np.meshgrid(x, y)

    phase = 2 * np.pi * (kx * X + ky * Y)
    phase = np.mod(phase, 2 * np.pi)
    return np.exp(1j * phase)


### lens phase (spherical wavefront) ###
@register_pattern("lens_phase", params=[
    param("focal_mm", 225, float),
    param("wavelength_nm", 488, int),
    param("pixel_size_um", 12.5, float)
])
def lens_phase(width, height, focal_mm, wavelength_nm, pixel_size_um=12.5,**kwargs):
    """
    Lens phase (spherical wavefront) of a given focal length `focal_mm`.
    """
    # Convert all units to meters
    f = focal_mm * 1e-3
    wavelength = wavelength_nm * 1e-9
    px = pixel_size_um * 1e-6

    offset_x = kwargs.get("center_offset_x_px",0)
    offset_y = kwargs.get("center_offset_y_px",0)

    x = (np.arange(width) - width/2 - offset_x) * px
    y = (np.arange(height) - height/2 - offset_y) * px
    X, Y = np.meshgrid(x, y)
    r2 = X**2 + Y**2

    wavefront = np.sqrt(f**2 - r2) - f
    wavefront = np.abs(wavefront) + 1e-16

    k = 2 * np.pi / wavelength
    phase = -k * wavefront

    return np.exp(1j * phase)



### Vortex Phase (Spiral Phase Plate) ###
@register_pattern("vortex", params=[
    param("charge", 1, int),
])
def vortex(width, height, charge, **kwargs):
    """
    Vortex phase / Spiral Phase Plate.
    charge: Topological charge (integer).
            Determines how many 2π phase wraps occur around the center.
    """
    offset_x = kwargs.get("center_offset_x_px", 0)
    offset_y = kwargs.get("center_offset_y_px", 0)

    x = np.arange(width) - width/2 - offset_x
    y = np.arange(height) - height/2 - offset_y
    X, Y = np.meshgrid(x, y)

    # Calculate angle theta (-π to π)
    theta = np.arctan2(Y, X)

    # Phase = l * theta
    phase = charge * theta
    
    return np.exp(1j * phase)


### Top Hat (Circular Phase Piston) ###
@register_pattern("top_hat", params=[
   param("radius_px", 100, int),
   param("phase_shift", 3.14, float), # Default to pi
])
def top_hat(width, height, radius_px, phase_shift=3.14, **kwargs):
    """
    Top Hat / Circular Piston.
    Creates a circular region with a constant phase shift relative to the background.
    radius_px: Radius of the circle in pixels.
    phase_shift: The phase height of the hat in radians (default π).
    """
    offset_x = kwargs.get("center_offset_x_px", 0)
    offset_y = kwargs.get("center_offset_y_px", 0)

    x = np.arange(width) - width/2 - offset_x
    y = np.arange(height) - height/2 - offset_y
    X, Y = np.meshgrid(x, y)

    mask = (X**2 + Y**2) <= radius_px**2

    phase = np.zeros((height, width))
    phase[mask] = phase_shift

    return np.exp(1j * phase)


### Half Moon X (Vertical Split) ###
@register_pattern("half_moon_x", params=[
    param("phase_shift", 3.14, float),
])
def half_moon_x(width, height, phase_shift=3.14, **kwargs):
    """
    Half Moon X (Vertical Phase Step).
    Splits the screen horizontally: 0 phase on left, `phase_shift` on right.
    Used often for Hilbert transforms or edge detection.
    """
    offset_x = kwargs.get("center_offset_x_px", 0)
    
    # Create X grid centered at offset
    x = np.arange(width) - width/2 - offset_x
    
    # Create mask where X > 0 (Right side)
    mask = x > 0
    
    # Broadcast to 2D (height, width)
    phase = np.zeros((height, width))
    phase[:, mask] = phase_shift

    return np.exp(1j * phase)


### Half Moon Y (Horizontal Split) ###
@register_pattern("half_moon_y", params=[
    param("phase_shift", 3.14, float),
])
def half_moon_y(width, height, phase_shift=3.14, **kwargs):
    """
    Half Moon Y (Horizontal Phase Step).
    Splits the screen vertically: 0 phase on top, `phase_shift` on bottom.
    """
    offset_y = kwargs.get("center_offset_y_px", 0)
    
    # Create Y grid centered at offset
    y = np.arange(height) - height/2 - offset_y
    
    # Create mask where Y > 0 (Bottom side, assuming numpy coordinates increase downwards)
    mask = y > 0
    
    # Broadcast to 2D (height, width)
    phase = np.zeros((height, width))
    phase[mask, :] = phase_shift

    return np.exp(1j * phase)
