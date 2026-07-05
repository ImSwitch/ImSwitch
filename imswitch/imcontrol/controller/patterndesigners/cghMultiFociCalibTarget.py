import numpy as np
from .cghBaseTarget import TargetBase
from .cghUtils import fft_constrained_frequency_estimation, refine_foci_positions, crop_with_preview, sum_around
from .cghUtils import fft_frequency_estimation, estimate_lattice_offset
from .registries import register_target
import matplotlib.pyplot as plt
import cv2
import math

@register_target()
class MultiFociCalibTarget(TargetBase):
    """
    Multi-foci target - more user friendly:
        - User enters period in sample space directly
        - Can lock FOV or number of points
    """

    target_type = "multi_foci_calib"
    _needs_calibration = True
    _auto_update_param = True

    target_params = [
        ("period_x_nm", 750, int),
        ("period_y_nm", 750, int),
        ("fov_x_um", 35, int),
        ("fov_y_um", 35, int),
        ("n_foci_x", 31, int),
        ("n_foci_y", 31, int),
    ]
    
    def __init__(self, section_size=None, section_calibration=None, **params):
        super().__init__(section_size=section_size,
                         section_calibration=section_calibration,
                         **params)
    
    # @property
    # def calib_params(self):
    #     params = [
    #         ("Period X (nm)", 750, float),
    #         ("Period Y (nm)", 750, float),
    #         ("Period X (px)", 6, int),
    #         ("Period Y (px)", 6, int),
    #         ("Target size X", 512, int),
    #         ("Target size Y", 512, int),
    #     ]
    #     return params
    

    # --- param helpers --- #
    def _period_x_um(self):
        return self.period_x / 1000

    def _period_y_um(self):
        return self.period_y / 1000

    def _n_from_fov(self, fov_um, period_um):
        return int(math.floor(fov_um / period_um)) + 1

    def _fov_from_n(self, n, period_um):
        return (int(n) - 1) * period_um

    # ---- parameters ----- #
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

    @property
    def period_x_nm(self):
        return self.params["period_x_nm"]

    @period_x_nm.setter
    def period_x_nm(self, value):
        self.params["period_x_nm"] = float(value)
        # keep FOV fixed, update number of foci
        self.params["n_foci_x"] = self._n_from_fov(
            self.params["fov_x_um"],
            self._period_x_um(),
        )

    @property
    def period_y_nm(self):
        return self.params["period_y_nm"]
    

    @period_y_nm.setter
    def period_y_nm(self, value):
        self.params["period_y_nm"] = float(value)
        # keep FOV fixed, update number of foci
        self.params["n_foci_y"] = self._n_from_fov(
            self.params["fov_y_um"],
            self._period_y_um(),
        )

    @property
    def npx(self):
        return self.params["n_foci_x"]

    @npx.setter
    def npx(self, value):
        self.params["n_foci_x"] = float(value)
        self.params["fov_x_um"] = self._fov_from_n(
            self.params["n_foci_x"],
            self._period_x_um()
        )

    @property
    def npy(self):
        return self.params["n_foci_y"]

    @npy.setter
    def npy(self, value):
        self.params["n_foci_y"] = float(value)
        self.params["fov_y_um"] = self._fov_from_n(
            self.params["n_foci_y"],
            self._period_y_um()
        )


    # ---- general methods ----- #

    def _build_impl(self):
        raise NotImplementedError
        # # retrieve section size in each direction
        # sy, sx = self.section_size

        # # ratio r = target_size / 
        # rx = self._period_x_um() / self.conversion_factor_dict.get("x") 
        # ry = self._period_y_um() / self.conversion_factor_dict.get("y") 

        # px = math.ceil(rx * sy)
        # py = math.ceil(ry * sx)

        # w = round(px/rx)
        # h = round(py/ry)

        # w, h = self.width, self.height
        # target = np.zeros((h, w))
        # cx, cy = w / 2, h / 2

        # for j in range(self.npy):
        #     for i in range(self.npx):
        #         x = cx + (i - (self.npx-1)/2) * px
        #         y = cy + (j - (self.npy-1)/2) * py

        #         xi, yi = int(round(x)), int(round(y))
        #         if 0 <= xi < w and 0 <= yi < h:
        #             target[yi, xi] = 1.0

        # return target

    def create_target_name(self):
        periodstr = f"P{self.period_x}" if self.period_x == self.period_y else f"Px{self.period_x}-Py{self.period_y}"
        name = f"mf_{self.npx}x{self.npy}foci_{periodstr}_FOV{self.fov_x}x{self.fov_y}um"
        return name



    # ---- calibration methods ----- #
    
    # def _calibration_impl(self,calib_values):
    #     px_nm = calib_values.get("Period X (nm)")
    #     py_nm = calib_values.get("Period Y (nm)")
    #     px_pix = calib_values.get("Period X (px)")
    #     py_pix = calib_values.get("Period Y (px)")
    #     trgtx_pix = calib_values.get("Target X (px)")
    #     trgty_pix = calib_values.get("Target Y (px)")

    #     conv_x = px_nm * px_pix / trgtx_pix
    #     conv_y = py_nm * py_pix / trgty_pix
        
    #     return {"x": conv_x, "y": conv_y}
