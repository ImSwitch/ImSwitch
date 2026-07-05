import numpy as np
import math

from .cghBaseTarget import TargetBase
from .registries import register_target
from .slmSectionCalibration import SLMSectionCalibration


@register_target()
class MultiFociVectorTarget(TargetBase):
    """
    Metric multi-foci target for the direct-summation backend.

    The user-facing parameters define an ideal spot grid in physical units.
    The current SLM section calibration converts those metric coordinates into
    kxy vectors used by the direct-summation backend. The preview array is only
    for visualization and is not used for computation.
    """

    target_type = "multi_foci_vector"
    _needs_calibration = True
    _auto_update_param = True

    target_params = [
        ("period_x_nm", 750, int),
        ("period_y_nm", 750, int),
        ("fov_x_um", 35, int),
        ("fov_y_um", 35, int),
        ("n_foci_x", 31, int),
        ("n_foci_y", 31, int),
        ("rotation_deg", 0.0, float),
        ("skew_deg", 0.0, float)
    ]

    uses_direct_summation = True
    missing_calibration_message = (
        "No valid section calibration found. Calibrate linear phase first."
    )

    _preview_min_size_px = 32
    _preview_max_size_px = 2048

    def __init__(self, section_size=None, section_calibration=None, **params):
        self.spot_positions_um = None
        self.spot_vectors_kxy = None
        self.spot_amp = None
        self.lattice_indices = None

        super().__init__(section_size=section_size,
                         section_calibration=section_calibration,
                         **params)

    # --- param helpers --- #
    def _period_x_um(self):
        return self.period_x_nm / 1000

    def _period_y_um(self):
        return self.period_y_nm / 1000

    def _n_from_fov(self, fov_um, period_um):
        return int(math.floor(fov_um / period_um)) + 1

    def _fov_from_n(self, n, period_um):
        return (int(n) - 1) * period_um
    
    # ---- parameters ----- #

    # FOV
    @property
    def fov_x_um(self):
        return self.params["fov_x_um"]

    @fov_x_um.setter
    def fov_x_um(self, value):
        self.params["fov_x_um"] = float(value)
        self.params["n_foci_x"] = self._n_from_fov(
            self.params["fov_x_um"],
            self._period_x_um(),
        )

    @property
    def fov_y_um(self):
        return self.params["fov_y_um"]

    @fov_y_um.setter
    def fov_y_um(self, value):
        self.params["fov_y_um"] = float(value)
        self.params["n_foci_y"] = self._n_from_fov(
            self.params["fov_y_um"],
            self._period_y_um()
        )

    # Periods
    @property
    def period_x_nm(self):
        return self.params["period_x_nm"]

    @period_x_nm.setter
    def period_x_nm(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError(f"period_x_um must be > 0, got {value}")
        self.params["period_x_nm"] = value
        self.params["n_foci_x"] = self._n_from_fov(
            self.params["fov_x_um"],
            self._period_x_um(),
        )

    @property
    def period_y_nm(self):
        return self.params["period_y_nm"]

    @period_y_nm.setter
    def period_y_nm(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError(f"period_y_um must be > 0, got {value}")
        self.params["period_y_nm"] = value
        self.params["n_foci_y"] = self._n_from_fov(
            self.params["fov_y_um"],
            self._period_x_um(),
        )

    # number of foci
    @property
    def n_foci_x(self):
        return self.params["n_foci_x"]
    @n_foci_x.setter
    def n_foci_x(self, value):
        value = int(value)
        if value <= 0:
            raise ValueError(f"n_foci_y must be > 0, got {value}")
        self.params["n_foci_x"] = value
        self.params["fov_x_um"] = self._fov_from_n(
            self.params["n_foci_x"],
            self._period_x_um()
        )

    @property
    def n_foci_y(self):
        return self.params["n_foci_y"]

    @n_foci_y.setter
    def n_foci_y(self, value):
        value = int(value)
        if value <= 0:
            raise ValueError(f"n_foci_y must be > 0, got {value}")
        self.params["n_foci_y"] = value
        self.params["fov_y_um"] = self._fov_from_n(
            self.params["n_foci_y"],
            self._period_y_um()
        )

    @property
    def rotation_deg(self):
        return float(self.params.get("rotation_deg", 0.0))

    @rotation_deg.setter
    def rotation_deg(self, value):
        self.params["rotation_deg"] = float(value)

    @property
    def skew_deg(self):
        return float(self.params.get("skew_deg", 0.0))

    @skew_deg.setter
    def skew_deg(self, value):
        self.params["skew_deg"] = float(value)

    @property
    def n_spots(self):
        return self.n_foci_x * self.n_foci_y


    # TargetBase hooks

    def _build_impl(self):
        positions_um = self._make_spot_positions_um()
        self.spot_positions_um = positions_um

        if self.spot_amp is None or self.spot_amp.shape != (self.n_spots,):
            self.spot_amp = np.ones(self.n_spots, dtype=np.float32)

        self.spot_vectors_kxy = self._calibrated_vectors_kxy(positions_um)
        return self._build_preview_array(positions_um)

    def create_target_name(self):
        name = (
            f"mfvec_{self.n_foci_x}x{self.n_foci_y}foci_"
            f"Px{self._fmt_float(self.period_x_nm)}nm-"
            f"Py{self._fmt_float(self.period_y_nm)}nm"
        )

        if self.rotation_deg != 0:
            name += f"_rot{self._fmt_float(self.rotation_deg)}deg"

        if self.skew_deg != 0:
            name += f"_skew{self._fmt_float(self.skew_deg)}deg"

        if not self.has_valid_section_calibration:
            name += "_uncalibrated"

        return name

    def _on_target_changed(self, params_changed=None, *args, **kwargs):
        if params_changed:
            self.spot_amp = None


    # Metric grid and calibration

    def _make_spot_positions_um(self):
        ix = np.arange(self.n_foci_x, dtype=np.float32) - (self.n_foci_x - 1) / 2
        iy = np.arange(self.n_foci_y, dtype=np.float32) - (self.n_foci_y - 1) / 2

        I, J = np.meshgrid(ix, iy, indexing="xy")

        skew_rad = np.deg2rad(self.skew_deg)
        x_um = I * self._period_x_um() + J * self._period_y_um() * np.sin(skew_rad)
        y_um = J * self._period_y_um() * np.cos(skew_rad)

        theta = np.deg2rad(self.rotation_deg)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        x_rot = cos_t * x_um - sin_t * y_um
        y_rot = sin_t * x_um + cos_t * y_um

        self.lattice_indices = np.vstack([I.ravel(), J.ravel()]).astype(np.float32)
        return np.vstack([x_rot.ravel(), y_rot.ravel()]).astype(np.float32)

    def _calibrated_vectors_kxy(self, positions_um):
        if not self.has_valid_section_calibration:
            return None

        vectors = [
            self.section_calibration.um_to_kxy(x_um, y_um)
            for x_um, y_um in positions_um.T
        ]
        return np.asarray(vectors, dtype=np.float32).T

    # Preview raster
    def _build_preview_array(self, positions_um):
        if positions_um is None or positions_um.size == 0:
            return np.zeros(
                (self._preview_min_size_px, self._preview_min_size_px),
                dtype=np.float32,
            )

        x = positions_um[0, :]
        y = positions_um[1, :]

        x_min = float(np.min(x))
        x_max = float(np.max(x))
        y_min = float(np.min(y))
        y_max = float(np.max(y))

        span_x = max(x_max - x_min, 0.0)
        span_y = max(y_max - y_min, 0.0)

        margin_um = max(
            0.5 * max(self._period_x_um(), self._period_y_um()),
            0.08 * max(span_x, span_y),
            1.0,
        )

        width_um = max(span_x + 2 * margin_um, 2 * margin_um)
        height_um = max(span_y + 2 * margin_um, 2 * margin_um)

        scale = self._preview_scale(width_um, height_um)
        width_px = max(1, int(np.ceil(width_um * scale)))
        height_px = max(1, int(np.ceil(height_um * scale)))

        target = np.zeros((height_px, width_px), dtype=np.float32)

        x_pix = (x - x_min + margin_um) * scale
        y_pix = (y_max - y + margin_um) * scale

        spot_radius = self._preview_spot_radius(scale)
        for x_pos, y_pos, amp in zip(x_pix, y_pix, self.spot_amp):
            self._draw_preview_spot(target, x_pos, y_pos, spot_radius, amp)

        if target.max() > 0:
            target = target / target.max()

        return target

    def _preview_scale(self, width_um, height_um):
        largest = max(float(width_um), float(height_um), 1.0)
        scale = 1.0

        if largest > self._preview_max_size_px:
            scale = self._preview_max_size_px / largest
        elif largest < self._preview_min_size_px:
            scale = self._preview_min_size_px / largest

        return scale

    def _preview_spot_radius(self, scale):
        min_period = min(self._period_x_um(), self._period_y_um())
        return max(1, min(4, int(round(min_period * scale / 12.0))))

    @staticmethod
    def _draw_preview_spot(target, x_pos, y_pos, radius, amp):
        x_center = int(round(float(x_pos)))
        y_center = int(round(float(y_pos)))
        amp = float(amp)

        y0 = max(0, y_center - radius)
        y1 = min(target.shape[0], y_center + radius + 1)
        x0 = max(0, x_center - radius)
        x1 = min(target.shape[1], x_center + radius + 1)

        if y0 < y1 and x0 < x1:
            target[y0:y1, x0:x1] = np.maximum(target[y0:y1, x0:x1], amp)

    # Utilities

    @staticmethod
    def _fmt_float(value, precision=4):
        text = f"{float(value):.{precision}g}"
        return text.replace("+", "")
