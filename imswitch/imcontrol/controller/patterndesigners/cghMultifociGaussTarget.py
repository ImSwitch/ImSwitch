import numpy as np

from .cghBaseTarget import TargetBase
from .registries import register_target


_FEEDBACK_NOT_IMPLEMENTED_MSG = (
    "Custom feedback for multifoci_gauss is not implemented yet."
)


# @register_target(
#     "multifoci_gauss",
#     feedback=True,
#     params=[
#         ("Target Size X", 512, int),
#         ("Target Size Y", 512, int),
#         ("N Foci X", 31, int),
#         ("N Foci Y", 31, int),
#         ("Period X", 6, int),
#         ("Period Y", 6, int),
#         ("Gaussian Size Px", 3, int),
#     ],
# )
class MultifociGaussTarget(TargetBase):
    """
    Multi-foci target with finite Gaussian spots.
    """

    target_type = "multifoci_gauss"

    @property
    def supports_feedback(self):
        return True

    @property
    def width(self):
        return self.params["target_size_x"]

    @property
    def height(self):
        return self.params["target_size_y"]

    @property
    def npx(self):
        return self.params["n_foci_x"]

    @property
    def npy(self):
        return self.params["n_foci_y"]

    @property
    def period_x(self):
        return self.params["period_x"]

    @property
    def period_y(self):
        return self.params["period_y"]

    @property
    def gaussian_size_px(self):
        return self.params["gaussian_size_px"]

    def update_params(self, **new_params) -> bool:
        """
        Sanitize Gaussian target parameters before TargetBase sees changes.

        Gaussian size is always positive, odd, and small enough to avoid
        overlapping neighbouring foci for the current period.
        """
        params = dict(self.params)
        params.update(new_params)
        params = self._sanitize_params(params)

        changed = False
        for key, new_val in params.items():
            if self.params.get(key) != new_val:
                self.params[key] = new_val
                changed = True

        if changed and hasattr(self, "feedback_count") and self.supports_feedback:
            self.reset_feedback()

        return changed

    def build(self):
        w, h = self.width, self.height
        target = np.zeros((h, w), dtype=float)
        kernel = self._gaussian_kernel(self.gaussian_size_px)
        radius = self.gaussian_size_px // 2
        cx, cy = w / 2, h / 2

        for j in range(self.npy):
            for i in range(self.npx):
                x = cx + (i - (self.npx - 1) / 2) * self.period_x
                y = cy + (j - (self.npy - 1) / 2) * self.period_y

                xi, yi = int(round(x)), int(round(y))
                if 0 <= xi < w and 0 <= yi < h:
                    self._place_kernel(target, kernel, xi, yi, radius)

        return target

    def create_target_name(self):
        targetstr = (
            f"trgt{self.width}"
            if self.width == self.height
            else f"trgt{self.width}x{self.height}"
        )
        periodstr = (
            f"P{self.period_x}"
            if self.period_x == self.period_y
            else f"Px{self.period_x}-Py{self.period_y}"
        )
        name = (
            f"mfg_{self.npx}x{self.npy}foci_{periodstr}_"
            f"G{self.gaussian_size_px}_{targetstr}"
        )
        if self.feedback_count != 0:
            name += f"_feedback{self.feedback_count}"
        return name

    def analyze_result(self, *args, **kwargs):
        return False, _FEEDBACK_NOT_IMPLEMENTED_MSG

    def adapt_target(self, *args, **kwargs):
        return False, _FEEDBACK_NOT_IMPLEMENTED_MSG

    def _adapt_target_impl(self, *args, **kwargs):
        return None, _FEEDBACK_NOT_IMPLEMENTED_MSG

    def _analyze_result_impl(self, *args, **kwargs):
        raise NotImplementedError(_FEEDBACK_NOT_IMPLEMENTED_MSG)

    def _feedback_reset(self, *args, **kwargs):
        pass

    @classmethod
    def _sanitize_params(cls, params):
        sanitized = dict(params)
        sanitized["target_size_x"] = cls._positive_int(
            sanitized.get("target_size_x", 512), 512
        )
        sanitized["target_size_y"] = cls._positive_int(
            sanitized.get("target_size_y", 512), 512
        )
        sanitized["n_foci_x"] = cls._positive_int(sanitized.get("n_foci_x", 31), 31)
        sanitized["n_foci_y"] = cls._positive_int(sanitized.get("n_foci_y", 31), 31)
        sanitized["period_x"] = cls._positive_int(sanitized.get("period_x", 6), 6)
        sanitized["period_y"] = cls._positive_int(sanitized.get("period_y", 6), 6)

        max_gaussian_size = cls._odd_floor(
            min(sanitized["period_x"], sanitized["period_y"])
        )
        requested_size = cls._odd_floor(sanitized.get("gaussian_size_px", 3))
        sanitized["gaussian_size_px"] = min(requested_size, max_gaussian_size)
        return sanitized

    @staticmethod
    def _positive_int(value, default):
        try:
            value = int(float(value))
        except (TypeError, ValueError):
            value = default
        return max(1, value)

    @staticmethod
    def _odd_floor(value):
        value = max(1, int(value))
        if value % 2 == 0:
            value -= 1
        return max(1, value)

    @staticmethod
    def _gaussian_kernel(size):
        if size == 1:
            return np.ones((1, 1), dtype=float)

        radius = size // 2
        coords = np.arange(size) - radius
        xx, yy = np.meshgrid(coords, coords)
        sigma = size / 6.0
        kernel = np.exp(-0.5 * (xx**2 + yy**2) / (sigma**2))
        return kernel / kernel.max()

    @staticmethod
    def _place_kernel(target, kernel, x, y, radius):
        height, width = target.shape
        y0 = max(0, y - radius)
        y1 = min(height, y + radius + 1)
        x0 = max(0, x - radius)
        x1 = min(width, x + radius + 1)

        ky0 = y0 - (y - radius)
        ky1 = ky0 + (y1 - y0)
        kx0 = x0 - (x - radius)
        kx1 = kx0 + (x1 - x0)

        target[y0:y1, x0:x1] = np.maximum(
            target[y0:y1, x0:x1],
            kernel[ky0:ky1, kx0:kx1],
        )
