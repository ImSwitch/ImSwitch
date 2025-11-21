"""
Aberration phase patterns.
"""

import numpy as np
from .registries import register_aberration
import matplotlib.pyplot as plt 

# list of available aberrations
ZERNIKE_DEFS = {
    "tilt_x":     {"noll": 2},
    "tilt_y":     {"noll": 3},
    "defocus":    {"noll": 4},
    "astig_obl":  {"noll": 5},
    "astig_vert": {"noll": 6},
    "coma_vert":  {"noll": 7},
    "coma_horiz": {"noll": 8},
    "trefoil_y":  {"noll": 9},
    "trefoil_x":  {"noll": 10},
    "spherical":  {"noll": 11}
}


# Loop through definitions to register each item
for key, data in ZERNIKE_DEFS.items():
    register_aberration(
        name=key,
        noll=data["noll"]
    )


class ZernikeGenerator:
    """
    Helper class to generate wavefronts from Zernike polynomials efficiently.
    
    Formalism:
    ----------
    1. Indexing: **Noll Indices** (j = 1, 2, 3...)
       - j=1: Piston (ignored usually)
       - j=2: Tilt X
       - j=3: Tilt Y
       - j=4: Defocus
       ...
       
    2. Normalization: **Noll / RMS Normalization**
       - The polynomials are orthonormal over the unit disk.
       - The normalization factors (e.g., sqrt(3) for defocus, sqrt(6) for astigmatism) 
         are included in the calculation.

        NOTE: In this formalism, the coefficient represents the RMS (Root Mean Square) 
        error, and not the Peak-to-Valley amplitude.
         
       Equation examples:
       - Defocus (j=4):   Z = sqrt(3) * (2*rho^2 - 1)
       - Astig   (j=5):   Z = sqrt(6) * rho^2 * sin(2*theta)

    3. Coordinates:
       - Defined on the unit circle (rho <= 1.0).
       - Coordinates are normalized by the specified `pupil_radius`.
    """

    def __init__(self):
        self._grid_cache = {} 

    def _get_grid(self, w, h, r, cx, cy):
        """
        Retrieves or generates the polar coordinate grid.
        Grid is cached to improve performance on repeated calls with same geometry.
        NOTE: cx and cy are relative offsets from the geometric center of the image.
        """
        key = (w, h, r, cx, cy)
        if key not in self._grid_cache:
            y, x = np.indices((h, w))
            # Normalize coordinates so the pupil_radius is 1.0 unit
            y = (y - h/2 - cy) / r
            x = (x - w/2 - cx) / r
            
            rho = np.sqrt(x**2 + y**2)
            theta = np.arctan2(y, x)
            
            self._grid_cache[key] = (rho, theta)
            
        return self._grid_cache[key]

    def compute_wavefront(self, coeffs, width, height, unit="waves", cx=0, cy=0, radius = None, 
                          wavelength_um=None, test_zernike_values=False,**kwargs):
        """
        Compute the complex field exp(1j * phase) using the zernike coefficients `coeffs`.

        Parameters
        ----------
        coeffs : dict
            Dictionary {noll_index (int): value (float)}.
        width: int
            Grid's width in pixel unit.
        height: int
            Grid's height in pixel unit.
        cx: int (optional)
            Horizontal relative offset from the geometric center of the image in pixel unit .
        cy: int (optional)
            Vertical relative offset from the geometric center of the image in pixel unit .
        radius : float (optional)
            Normalization radius in pixel unit.If None, defaults to min(width, height) / 2 (Full Inscribed Circle).
            NOTE: /!\ Changing the radius can affect drastically the calculation!
        unit : str (optional)
            "waves" (default): Coefficient 1.0 = 1 wavelength of aberration (2*pi phase).
            "rad": Coefficient 1.0 = 1 radian of phase.
            "um": Coefficient 1.0 = 1 micron optical path difference (requires wavelength_um).
        wavelength_um : float (optional)
            Wavelength in microns. Required only if unit="um".
        test_zernike_values: str (optional)
            Print sanity checks of the values (RMS value, min and max).
        """
        if not coeffs:
            return np.ones((height, width), dtype=complex)

        if radius is None or radius <= 0:
            radius = min(width, height) / 2.0

        rho, theta = self._get_grid(width, height, radius, cx, cy)
        total_phase = np.zeros((height, width), dtype=np.float64)


        scale_factor = 1.0        
        if unit == "waves":
            # 1 Wave RMS -> 2*pi Radians RMS
            scale_factor = 2 * np.pi
        elif unit == "um":
             # 1 micron OPD -> (2*pi / lambda) Radians
             if wavelength_um is None or wavelength_um == 0:
                 # Fallback to avoid division by zero
                 wavelength_um = 1.0 
             scale_factor = (2 * np.pi) / wavelength_um
        # If unit == "rad", scale_factor stays 1.0


        for noll, val in coeffs.items():

            if val == 0: 
                continue

            c = val * scale_factor
            term = 0.0
            
            # Noll Formalism Definitions
            if noll == 1:   term = 1.0
            elif noll == 2: term = 2 * rho * np.sin(theta)                          # Tilt X
            elif noll == 3: term = 2 * rho * np.cos(theta)                          # Tilt Y
            elif noll == 4: term = np.sqrt(3) * (2 * rho**2 - 1)                    # Defocus
            elif noll == 5: term = np.sqrt(6) * rho**2 * np.sin(2*theta)            # Astigmatism (Oblique)
            elif noll == 6: term = np.sqrt(6) * rho**2 * np.cos(2*theta)            # Astigmatism (Vertical)
            elif noll == 7: term = np.sqrt(8) * (3*rho**3 - 2*rho) * np.sin(theta)  # Coma (Vertical)
            elif noll == 8: term = np.sqrt(8) * (3*rho**3 - 2*rho) * np.cos(theta)  # Coma (Horizontal)
            elif noll == 9: term = np.sqrt(8) * rho**3 * np.sin(3 * theta)          # Trefoil Y
            elif noll == 10: term = np.sqrt(8) * rho**3 * np.cos(3 * theta)         # Trefoil X
            elif noll == 11:term = np.sqrt(5) * (6*rho**4 - 6*rho**2 + 1)           # Spherical
            
            total_phase += c * term

            if test_zernike_values:
                self.check_zernike(total_phase, radius,cx, cy)
            
        return np.exp(1j * total_phase)
    

    def check_zernike(self, phase, r, cx=0, cy=0):
        """
        Calculates statistics (RMS, Peak-to-Valley) of the phase pattern, 
        strictly masking pixels inside the unit circle (rho <= 1).

        This is critical because Zernike polynomials are mathematically undefined 
        (or explode to infinity) in the corners of a rectangular grid where rho > 1.

        Usage:
            Call this immediately after generating the aberration to verify scaling.
            params:
                phase: 2D numpy array of phase values (in Radians).
                r: The normalization radius used during generation (e.g., 540).
                cx, cy: Center offsets used during generation.

        Expected Result Example:
            If you input a coefficient of 0.5 waves (Noll normalization):
            - The RMS should be exactly ~0.50 waves (~3.14 radians).
            - The Peak-to-Valley will depend on the specific term (e.g., Defocus ~1.73 waves).
        """
        h, w = phase.shape
        y, x = np.indices((h, w))
        
        # Re-calculate the grid locally just for the mask
        y = (y - h/2 - cy) / r
        x = (x - w/2 - cx) / r
        rho = np.sqrt(x**2 + y**2)
        
        # Create a Boolean Mask for the valid unit disk
        mask = rho <= 1.0
        
        # Extract only valid pixels
        valid_phase = phase[mask]
        
        if valid_phase.size == 0:
            print("Error: No pixels inside the unit disk!")
            return

        # Calculate Stats
        min_val = np.min(valid_phase)
        max_val = np.max(valid_phase)
        pv = max_val - min_val
        
        # RMS calculation
        mean_val = np.mean(valid_phase)
        rms = np.sqrt(np.mean((valid_phase - mean_val)**2))
        
        print(f"--- Zernike Stats (Inside Unit Circle) ---")
        print(f"Min Phase: {min_val:.2f} rad")
        print(f"Max Phase: {max_val:.2f} rad")
        print(f"Peak-to-Valley: {pv:.2f} rad ({pv / (2*np.pi):.2f} waves)")
        print(f"Calculated RMS: {rms:.2f} rad ({rms / (2*np.pi):.2f} waves)")
        print("------------------------------------------")