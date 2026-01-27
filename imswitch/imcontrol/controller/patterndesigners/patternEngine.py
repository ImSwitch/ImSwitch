import numpy as np
from .registries import PATTERNS_REGISTRY, ABERRATIONS_REGISTRY
from . import cghComputations as cgh
from .aberrationPatterns import ZernikeGenerator
from PyQt5.QtCore import QObject

class PatternEngine(QObject):
    """Class handling pattern generation for SLMs."""

    def __init__(self, slmInfo, *args, **kwargs):
        super().__init__()
        self.width = slmInfo.width
        self.height = slmInfo.height
        self.pixelSize = slmInfo.pixelSize
        self.nSections = getattr(slmInfo, "nSections", 1) or 1
        self.sectionKeys = [f"sec_{n}" for n in range(self.nSections)]

        self._sectionShapes = {f"sec_{n}": None for n in range(self.nSections)}
        self._sectionSlices = self.compute_section_slices()

        self._cachedSections = {
            secKey: {"analytic": None,"aberrations":None, "cgh": None, "combined": None}
            for secKey in self.sectionKeys
        }

        self.twoPieValues = {secKey: None for secKey in self.sectionKeys}
        self.correctionPatterns = {secKey: None for secKey in self.sectionKeys}

        self.zernikeGenerator = ZernikeGenerator()

    def set_new_cgh_pattern(self, sec_key, cgh_pattern):
        """
        Receives a new CGH pattern, pads and/or crops to fit the section size,
        stores it, and returns a warning if cropping occurs. 
        Returns a warning message if cropping occured, None otherwise.
        """

        target_h, target_w = self._sectionShapes[sec_key]
        cur_h, cur_w = cgh_pattern.shape
        cropped = False

        # Loop over dimensions: (current size, target size, axis)
        for cur_size, target_size, axis in [(cur_h, target_h, 0), (cur_w, target_w, 1)]:
            pad_vals, crop_start = self.get_pad_crop(cur_size, target_size)

            # Apply padding if needed
            if pad_vals is not None:
                # Ensure integers
                pad_vals = tuple(int(v) for v in pad_vals)
                pad_shape = [(0, 0), (0, 0)]
                pad_shape[axis] = pad_vals
                cgh_pattern = np.pad(cgh_pattern, pad_shape, mode='wrap')

            # Apply cropping if needed
            if crop_start is not None:
                if axis == 0:
                    cgh_pattern = cgh_pattern[crop_start:crop_start + target_size, :]
                else:
                    cgh_pattern = cgh_pattern[:, crop_start:crop_start + target_size]
                cropped = True

        # Store
        self._cachedSections[sec_key]["cgh"] = cgh_pattern

        if cropped:
            return "CGH pattern was cropped to fit section size, this might create artefacts."
        return None

    def compute_pattern(self,params):
        """Compute full SLM pattern according to dict params (except CGH)."""
        for n in range(self.nSections):
            sec_key = f"sec_{n}"
            sec_param = params.get(sec_key)
            if sec_param is not None:
                self.compute_section(sec_key=sec_key,params=sec_param)
            else:
                print(f"tab{n}'s parameters not found")

    def compute_section_slices(self):
        """Return slices for each section (for now, simple horizontal split) 
        and store sizes in self._sectionShapes."""
        slices = {}
        section_width = self.width // self.nSections
        for i in range(self.nSections):
            start_x = i * section_width
            end_x = (i + 1) * section_width if i < self.nSections - 1 else self.width
            slices[f"sec_{i}"] = (slice(0, self.height), slice(start_x, end_x))
            width = end_x - start_x
            self._sectionShapes[f"sec_{i}"] = (self.height,width)
        return slices

    def compute_section(self, sec_key, params):
        """Compute analytic + aberrations and add current CGH pattern for one section."""
        slice_y, slice_x = self._sectionSlices[sec_key]
        width = slice_x.stop - slice_x.start
        height = self.height 

        general_params = params.get("general",{})
        general_params["pixel_size_um"] = self.pixelSize
        offset_x = general_params.get("center_offset_x_px",0)
        offset_y = general_params.get("center_offset_y_px",0)

        # === Analytic patterns ===
        patterns_to_combine = []
        for pattern_name, pattern_params in params.get("patterns", {}).items():
            if pattern_params.get("active", False) and pattern_name in PATTERNS_REGISTRY:
                func = PATTERNS_REGISTRY[pattern_name].get("func")
                pattern = func(width, height, **pattern_params,**general_params)
                patterns_to_combine.append(pattern)

        analyticPatterns = (
            np.prod(patterns_to_combine, axis=0)
            if patterns_to_combine
            else np.ones((self.height, width), dtype=complex)
        )

        # === Aberrations ===
        aberrations = None
        if params.get("aberrations", {}).get("aberrations_active",True):
            zernike_coeffs = {}
            for name, coeff in params.get("aberrations", {}).items():
                if name in ABERRATIONS_REGISTRY:
                    noll = ABERRATIONS_REGISTRY[name]["noll"]
                    zernike_coeffs[noll] = coeff

            aberrations = self.zernikeGenerator.compute_wavefront(zernike_coeffs, width, height, 
                                                                  cx=offset_x, cy=offset_y)

        combined = analyticPatterns * (aberrations if aberrations is not None else 1)

        # === CGH ===
        if params.get("cgh", {}).get("cgh_general", {}).get("active", False):
            cgh_pattern = self._cachedSections[sec_key]["cgh"]
        else:
            cgh_pattern = None
        combined = combined * (cgh_pattern if cgh_pattern is not None else 1)
        
        # === Pupil === (only applied to combined for now)
        if general_params.get("pupil_radius_px",0) !=0:
            r=general_params.get("pupil_radius_px")
            combined = self.apply_pupil(combined,r,offset_y,offset_x)
        
        # store all results
        self._cachedSections[sec_key]["analytic"] = analyticPatterns
        self._cachedSections[sec_key]["aberrations"] = aberrations
        self._cachedSections[sec_key]["combined"] = combined
    

    def compose_full_frame(self):
        """Compose full SLM frame from all sections of the combined final 8bits patterns."""
        frame = np.zeros((self.height, self.width), dtype=np.uint8)
        for sec_key, sl in self._sectionSlices.items():
            frame[sl] = self._cachedSections[sec_key]["eightbits"]
        self._cachedFinalImage = frame
        return frame
    
    def get_cached_final_image(self):
        """
        Returns the last composed full-SLM 8-bit image if available.
        """
        if hasattr(self, "_cachedFinalImage"):
            return self._cachedFinalImage
        return None
    
    def phase_to_eightbits(self,apply_twopi_value = True, apply_correction_pattern=True):
        """" Convert phase patterns to 8bits for all sections with corrections. """
        
        for sec_key in self.sectionKeys:
            if apply_twopi_value and self.twoPieValues.get(sec_key) is not None:
                twopiValue = self.twoPieValues.get(sec_key)
            else:
                twopiValue = 255
            phase = np.angle(self._cachedSections[sec_key]["combined"]) # [-π, π]
            phase = phase + 2 * np.pi * (np.sign(phase) < 0)            # [0, 2π]  (negative values mapped to [π,2π])
            img = phase * twopiValue / (2 * np.pi)                      # gray levels [0, 2π-value]
            img = img.astype(np.uint16)

            if apply_correction_pattern:
                correctionPattern = self.correctionPatterns.get(sec_key)
                if correctionPattern is not None:
                    slice = self._sectionSlices.get(sec_key)
                    correctionPattern = correctionPattern[slice].astype(np.float64)
                    correctionPattern = (correctionPattern * twopiValue/255).astype(np.uint16)
                    img = (img + correctionPattern) % 255
            
            img = img.astype(np.uint8)
            self._cachedSections[sec_key]["eightbits"] = img

    def apply_transform(self, sec_key, transform_type, **kwargs):
        """Incremental transforms like translation."""
        arr = self._cachedSections[sec_key]["combined"]

        if transform_type == "translate":
            dx = kwargs.get("dx_px", 0)
            dy = kwargs.get("dy_px", 0)
            # translate phase
            phase = np.angle(arr)
            phase = np.roll(phase, shift=(dy, dx), axis=(0, 1))
            arr = np.exp(1j * phase)

        self._cachedSections[sec_key]["combined"] = arr
        self._cachedSections[sec_key]["eightbits"] = self.field_to_eightbits(arr)
    

    def apply_pupil(self,pattern,r,offset_y=0,offset_x=0):
        """ Apply a pupil of radius `r` (in pixel)"""
        height, width = pattern.shape
        x = (np.arange(width) - width/2 - offset_x)
        y = (np.arange(height) - height/2 - offset_y)
        X, Y = np.meshgrid(x, y)
        R2 = X**2 + Y**2 
        pupil_mask = R2 <= r**2 

        phase = np.angle(pattern)
        masked_phase = phase * pupil_mask
        return np.exp(1j*masked_phase)

    def update_twopi_value(self, secKey, value):
        if secKey in self.twoPieValues:
            self.twoPieValues[secKey] = value
        else:
            raise KeyError(f"section {secKey} does not exist in pattern engine")
        
    def update_correction_pattern(self, secKey, pattern):
        if secKey in self.correctionPatterns:
            self.correctionPatterns[secKey] = pattern
        else:
            raise KeyError(f"section {secKey} does not exist in pattern engine")

    
    # Helper Function to compute padding or cropping for one dimension
    def get_pad_crop(self,cur_size, target_size):
        if cur_size < target_size:
            b = (target_size - cur_size) // 2
            a = target_size - cur_size - b
            return (b, a), None
        elif cur_size > target_size:
            start = (cur_size - target_size) // 2
            return None, start
        else:
            return (0, 0), None