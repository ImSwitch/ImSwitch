import numpy as np

from .base import Target
from ...registries import register_target


# @register_target(
#     "multi_foci_vector_2",
#     feedback=False,          # keep False for now; enable once feedback loop is implemented
#     calibration=False,
#     auto_update_param=False,
#     params=[
#         ("Target Size X", 512, int),      # preview / legacy raster size
#         ("Target Size Y", 512, int),      # preview / legacy raster size
#         ("N Foci X", 31, int),
#         ("N Foci Y", 31, int),
#         ("Period X kxy", 0.8e-3, float),
#         ("Period Y kxy", 0.8e-3, float),
#         ("Rotation Deg", 0.0, float),
#         ("Skew Deg", 0.0, float),
#         ("Offset X kxy", 0.0, float),
#         ("Offset Y kxy", 0.0, float),
#         ("Stagger", 0.0, float),
#     ],
# )
class MultiFociVectorTarget2(Target):
    """
    Vectorized multi-foci target.

    This target is designed for slmsuite-style spot holograms.

    Main outputs
    ------------
    self.spot_vectors_kxy : np.ndarray, shape (2, N), dtype float32
        Floating-point k-space coordinates:
            spot_vectors_kxy[0, :] = kx
            spot_vectors_kxy[1, :] = ky

    self.spot_amp : np.ndarray, shape (N,), dtype float32
        Per-spot target amplitudes. Initially all ones.

    self.array : np.ndarray, shape (height, width)
        2D raster preview only. This is kept for compatibility with the
        current Target / Visualize Target workflow. The slmsuite backend
        should use spot_vectors_kxy, not this raster array.
    """

    target_type = "multi_foci_vector"
    algorithm = "direct_summation"
    _supports_feedback = False
    _needs_calibration = False

    def __init__(self, section_size=None, **params):
        # Future feedback/correction state.
        # These must exist before Target.__init__ calls self.build().
        self.base_vectors_kxy = None
        self.spot_vectors_kxy = None
        self.local_offsets_kxy = None
        self.spot_amp = None
        self.lattice_indices = None

        super().__init__(section_size=section_size, **params)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def width(self):
        return int(self.params["target_size_x"])

    @width.setter
    def width(self, value):
        self.params["target_size_x"] = int(value)

    @property
    def height(self):
        return int(self.params["target_size_y"])

    @height.setter
    def height(self, value):
        self.params["target_size_y"] = int(value)

    @property
    def npx(self):
        return int(self.params["n_foci_x"])

    @npx.setter
    def npx(self, value):
        value = int(value)
        if value <= 0:
            raise ValueError(f"n_foci_x must be > 0, got {value}")
        self.params["n_foci_x"] = value

    @property
    def npy(self):
        return int(self.params["n_foci_y"])

    @npy.setter
    def npy(self, value):
        value = int(value)
        if value <= 0:
            raise ValueError(f"n_foci_y must be > 0, got {value}")
        self.params["n_foci_y"] = value

    @property
    def period_x_kxy(self):
        return float(self.params["period_x_kxy"])

    @period_x_kxy.setter
    def period_x_kxy(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError(f"period_x_kxy must be > 0, got {value}")
        self.params["period_x_kxy"] = value

    @property
    def period_y_kxy(self):
        return float(self.params["period_y_kxy"])

    @period_y_kxy.setter
    def period_y_kxy(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError(f"period_y_kxy must be > 0, got {value}")
        self.params["period_y_kxy"] = value

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
    def offset_x_kxy(self):
        return float(self.params.get("offset_x_kxy", 0.0))

    @offset_x_kxy.setter
    def offset_x_kxy(self, value):
        self.params["offset_x_kxy"] = float(value)

    @property
    def offset_y_kxy(self):
        return float(self.params.get("offset_y_kxy", 0.0))

    @offset_y_kxy.setter
    def offset_y_kxy(self, value):
        self.params["offset_y_kxy"] = float(value)

    @property
    def stagger(self):
        return float(self.params.get("stagger", 0.0))

    @stagger.setter
    def stagger(self, value):
        value = float(value)
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"stagger must be in [0, 1], got {value}")
        self.params["stagger"] = value

    @property
    def n_spots(self):
        return self.npx * self.npy

    # ------------------------------------------------------------------
    # Target hooks
    # ------------------------------------------------------------------

    def build(self):
        """
        Build vectorized kxy coordinates and return a 2D raster preview.
        """

        base_vectors = self._make_base_vectors_kxy()

        # Keep local offsets only if they still match the current number of spots.
        if (
            self.local_offsets_kxy is None
            or self.local_offsets_kxy.shape != base_vectors.shape
        ):
            self.local_offsets_kxy = np.zeros_like(base_vectors, dtype=np.float32)

        vectors = base_vectors + self.local_offsets_kxy

        # Keep amplitudes only if they still match the current number of spots.
        if self.spot_amp is None or self.spot_amp.shape != (self.n_spots,):
            self.spot_amp = np.ones(self.n_spots, dtype=np.float32)

        self.base_vectors_kxy = base_vectors.astype(np.float32)
        self.spot_vectors_kxy = vectors.astype(np.float32)

        return self._build_preview_array(self.spot_vectors_kxy)

    def create_target_name(self):
        name = (
            f"mfvec_{self.npx}x{self.npy}foci_"
            f"Px{self._fmt_float(self.period_x_kxy)}-"
            f"Py{self._fmt_float(self.period_y_kxy)}"
        )

        if self.rotation_deg != 0:
            name += f"_rot{self._fmt_float(self.rotation_deg)}deg"

        if self.skew_deg != 0:
            name += f"_skew{self._fmt_float(self.skew_deg)}deg"

        if self.offset_x_kxy != 0 or self.offset_y_kxy != 0:
            name += (
                f"_offx{self._fmt_float(self.offset_x_kxy)}"
                f"_offy{self._fmt_float(self.offset_y_kxy)}"
            )

        if self.stagger != 0:
            name += f"_stagg{self._fmt_float(self.stagger)}"

        if self.feedback_count != 0:
            name += f"_feedback{self.feedback_count}"

        return name

    def _set_param(self, key, value):
        """
        Route parameters through property setters for validation and casting.
        """

        if key == "target_size_x":
            self.width = value
        elif key == "target_size_y":
            self.height = value
        elif key == "n_foci_x":
            self.npx = value
        elif key == "n_foci_y":
            self.npy = value
        elif key == "period_x_kxy":
            self.period_x_kxy = value
        elif key == "period_y_kxy":
            self.period_y_kxy = value
        elif key == "rotation_deg":
            self.rotation_deg = value
        elif key == "skew_deg":
            self.skew_deg = value
        elif key == "offset_x_kxy":
            self.offset_x_kxy = value
        elif key == "offset_y_kxy":
            self.offset_y_kxy = value
        elif key == "stagger":
            self.stagger = value
        else:
            self.params[key] = value

    # ------------------------------------------------------------------
    # Vector construction
    # ------------------------------------------------------------------

    def _make_base_vectors_kxy(self):
        """
        Build the corrected global lattice in kxy coordinates.

        Transform order:
            1. centered rectangular grid
            2. optional stagger in the x-basis direction
            3. optional skew of the y-basis direction
            4. optional global rotation
            5. optional global kxy offset
        """

        # Centered lattice coordinates.
        ix = np.arange(self.npx, dtype=np.float32) - (self.npx - 1) / 2
        iy = np.arange(self.npy, dtype=np.float32) - (self.npy - 1) / 2

        I, J = np.meshgrid(ix, iy, indexing="xy")

        # Raw row index, useful for stagger parity.
        _, J_raw = np.meshgrid(
            np.arange(self.npx, dtype=np.int32),
            np.arange(self.npy, dtype=np.int32),
            indexing="xy",
        )

        skew_rad = np.deg2rad(self.skew_deg)

        # Skew convention:
        # - x basis remains horizontal
        # - y basis tilts toward x by skew_deg
        kx = I * self.period_x_kxy + J * self.period_y_kxy * np.sin(skew_rad)
        ky = J * self.period_y_kxy * np.cos(skew_rad)

        # Optional stagger: odd rows shifted along x basis.
        if self.stagger != 0:
            kx = kx + (J_raw % 2) * self.stagger * self.period_x_kxy

        # Optional global rotation.
        theta = np.deg2rad(self.rotation_deg)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        kx_rot = cos_t * kx - sin_t * ky
        ky_rot = sin_t * kx + cos_t * ky

        # Optional global offset.
        kx_rot = kx_rot + self.offset_x_kxy
        ky_rot = ky_rot + self.offset_y_kxy

        # Keep lattice indices for future matching/feedback.
        self.lattice_indices = np.vstack([I.ravel(), J.ravel()]).astype(np.float32)

        return np.vstack([kx_rot.ravel(), ky_rot.ravel()]).astype(np.float32)

    # ------------------------------------------------------------------
    # Preview raster
    # ------------------------------------------------------------------

    def _build_preview_array(self, vectors_kxy):
        """
        Convert floating kxy vectors into a simple 2D preview raster.

        This is only for visualization and compatibility with the current
        Target workflow. It should not be used by the slmsuite backend.
        """

        h, w = self.height, self.width
        target = np.zeros((h, w), dtype=np.float32)

        if vectors_kxy is None or vectors_kxy.size == 0:
            return target

        kx = vectors_kxy[0, :]
        ky = vectors_kxy[1, :]

        margin = 10
        usable_w = max(1, w - 2 * margin)
        usable_h = max(1, h - 2 * margin)

        span_x = float(kx.max() - kx.min())
        span_y = float(ky.max() - ky.min())

        if span_x == 0 and span_y == 0:
            x_pix = np.full_like(kx, w / 2)
            y_pix = np.full_like(ky, h / 2)
        else:
            scale_x = usable_w / span_x if span_x > 0 else np.inf
            scale_y = usable_h / span_y if span_y > 0 else np.inf
            scale = min(scale_x, scale_y)

            cx = w / 2
            cy = h / 2
            kx_center = 0.5 * (kx.max() + kx.min())
            ky_center = 0.5 * (ky.max() + ky.min())

            x_pix = cx + (kx - kx_center) * scale
            y_pix = cy + (ky - ky_center) * scale

        for x, y, amp in zip(x_pix, y_pix, self.spot_amp):
            xi = int(round(x))
            yi = int(round(y))

            if 0 <= xi < w and 0 <= yi < h:
                target[yi, xi] = max(target[yi, xi], float(amp))

        if target.max() > 0:
            target = target / target.max()

        return target

    # ------------------------------------------------------------------
    # Future feedback helpers
    # ------------------------------------------------------------------

    def set_spot_amp(self, spot_amp):
        """
        Set per-spot target amplitudes.

        Parameters
        ----------
        spot_amp : array-like, shape (N,)
            New target amplitudes for the vectorized spot hologram.
        """

        spot_amp = np.asarray(spot_amp, dtype=np.float32)

        if spot_amp.shape != (self.n_spots,):
            raise ValueError(
                f"spot_amp must have shape ({self.n_spots},), got {spot_amp.shape}"
            )

        self.spot_amp = spot_amp
        self.array = self._build_preview_array(self.spot_vectors_kxy)

    def set_local_offsets_kxy(self, offsets_kxy):
        """
        Set per-spot local kxy offsets.

        Parameters
        ----------
        offsets_kxy : array-like, shape (2, N)
            Per-spot displacement in kxy coordinates.
        """

        offsets_kxy = np.asarray(offsets_kxy, dtype=np.float32)

        expected = (2, self.n_spots)
        if offsets_kxy.shape != expected:
            raise ValueError(
                f"offsets_kxy must have shape {expected}, got {offsets_kxy.shape}"
            )

        self.local_offsets_kxy = offsets_kxy
        self.array = self.build()
        self.name = self.create_target_name()

    def add_local_offsets_kxy(self, delta_offsets_kxy, gain=1.0):
        """
        Add per-spot local kxy offsets.

        This will be useful later for geometry feedback:
            corrected_vectors = base_vectors + local_offsets
        """

        delta_offsets_kxy = np.asarray(delta_offsets_kxy, dtype=np.float32)

        expected = (2, self.n_spots)
        if delta_offsets_kxy.shape != expected:
            raise ValueError(
                f"delta_offsets_kxy must have shape {expected}, got {delta_offsets_kxy.shape}"
            )

        if self.local_offsets_kxy is None:
            self.local_offsets_kxy = np.zeros(expected, dtype=np.float32)

        self.local_offsets_kxy = self.local_offsets_kxy + float(gain) * delta_offsets_kxy
        self.array = self.build()
        self.name = self.create_target_name()

    def apply_power_feedback(self, measured_power, gain=1.0, eps=1e-9):
        """
        Simple intensity feedback helper.

        This does not analyze images. It only updates spot_amp from already
        measured per-spot powers.

        Parameters
        ----------
        measured_power : array-like, shape (N,)
            Measured intensity/power for each spot.
        gain : float
            Feedback gain. 1.0 applies full correction.
        eps : float
            Numerical stability term.
        """

        measured_power = np.asarray(measured_power, dtype=np.float32)

        if measured_power.shape != (self.n_spots,):
            raise ValueError(
                f"measured_power must have shape ({self.n_spots},), "
                f"got {measured_power.shape}"
            )

        correction = measured_power.mean() / (measured_power + eps)
        correction = correction.astype(np.float32)

        # Damped multiplicative update.
        correction = (1.0 - float(gain)) + float(gain) * correction

        self.spot_amp = self.spot_amp * correction
        self.spot_amp = self.spot_amp / (self.spot_amp.mean() + eps)

        self.array = self._build_preview_array(self.spot_vectors_kxy)

    def _feedback_reset(self, *args, **kwargs):
        """
        Future-proof feedback reset.

        Target.reset_feedback() calls build before this hook, so we rebuild
        once more after clearing vector feedback state.
        """

        self.local_offsets_kxy = None
        self.spot_amp = None
        self.array = self.build()
        self.name = self.create_target_name()

    # ------------------------------------------------------------------
    # Small utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_float(value, precision=4):
        """
        Compact float formatting for target names.
        """

        value = float(value)
        text = f"{value:.{precision}g}"
        return text.replace("+", "")