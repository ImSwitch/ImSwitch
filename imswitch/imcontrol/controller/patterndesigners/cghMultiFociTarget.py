import numpy as np
from .cghBaseTarget import TargetBase
from .cghUtils import fft_constrained_frequency_estimation, refine_foci_positions, crop_with_preview, sum_around
from .cghUtils import fft_frequency_estimation, estimate_lattice_offset
from .registries import register_target
import matplotlib.pyplot as plt

@register_target("multi_foci", feedback=True,
params=[
    ("Target Size X", 512, int),
    ("Target Size Y", 512, int),
    ("N Foci X",31, int),
    ("N Foci Y",31, int),
    ("Period X", 6, int),
    ("Period Y", 6, int),
    ("Stagger", 0.0, float),
])
class MultiFociTarget(TargetBase):
    """
    Multi-foci target.
    """
    target_type = "multi_foci"
    def __init__(self, **params):
        super().__init__(**params)
        self.analysis_prm = {
            "foci_integration_size": 7,
            "Threshold": 0.5,
            "Dilat_kernel_size":5,
            "auto_freq_finder": True,
            "period_x": None,
            "period_y": None,
            "freq_search_window_px": 0.1,
            "foci_loc_method": "max",
            "foci_search_window_px": 3,
            "auto_freq_blur_sigma":1.0,
            "auto_freq_exclude_frac":0.05,
            "auto_freq_peak_prom": 0.05,
        }

    # feedback allowed
    @property
    def supports_feedback(self):
        return True

    # ---- parameters ----- #
    @property
    def width(self):
        return self.params["target_size_x"]
    
    @width.setter
    def npx(self, value):
        self.params["target_size_x"] = value

    @property
    def height(self):
        return self.params["target_size_y"]
    
    @height.setter
    def height(self, value):
        self.params["target_size_y"] = value

    @property
    def npx(self):
        return self.params["n_foci_x"]

    @npx.setter
    def npx(self, value):
        self.params["n_foci_x"] = value

    @property
    def npy(self):
        return self.params["n_foci_y"]

    @npy.setter
    def npy(self, value):
        self.params["n_foci_y"] = value

    @property
    def period_x(self):
        return self.params["period_x"]

    @period_x.setter
    def period_x(self, value):
        self.params["period_x"] = value

    @property
    def period_y(self):
        return self.params["period_y"]

    @period_y.setter
    def period_y(self, value):
        self.params["period_y"] = value

    @property
    def stagger(self):
        return self.params.get("stagger", 0.0)

    @stagger.setter
    def stagger(self, value):
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"stagger must be in [0, 1], got {value}")
        self.params["stagger"] = value

    # ---- methods ----- #

    def build(self):
        w, h = self.width, self.height
        target = np.zeros((h, w))
        cx, cy = w / 2, h / 2

        for j in range(self.npy):
            for i in range(self.npx):
                x = cx + (i - (self.npx-1)/2) * self.period_x
                y = cy + (j - (self.npy-1)/2) * self.period_y

                if 0 < self.stagger < 1:
                    x += (j % 2) * self.stagger * self.period_x

                xi, yi = int(round(x)), int(round(y))
                if 0 <= xi < w and 0 <= yi < h:
                    target[yi, xi] = 1.0

        return target

    def create_target_name(self):
        targetstr = f"trgt{self.width}" if self.width == self.height else f"trgt{self.width}x{self.height}"
        periodstr = f"P{self.period_x}" if self.period_x == self.period_y else f"Px{self.period_x}-Py{self.period_y}"
        name = f"mf_{self.npx}x{self.npy}foci_{periodstr}_{targetstr}"
        if self.stagger != 0:
            name += f"_stagg{self.stagger}"
        if self.feedback_count != 0:
            name += f"_feedback{self.feedback_count}"
        return name


    def _analyze_result_impl(self, image, show_plot=True):
        # localize array and crop
        kernel_size = self.analysis_prm.get("Dilat_kernel_size")
        threshold = self.analysis_prm.get("Threshold")
        image_cropped,crop_preview = crop_with_preview(image, kernel_size, threshold)

        # frequency estimation
        if self.analysis_prm.get("auto_freq_finder",True):
            fx,fy = fft_frequency_estimation(image_cropped,self.analysis_prm.get("auto_freq_blur_sigma"),
                                             self.analysis_prm.get("auto_freq_exclude_frac"),
                                             self.analysis_prm.get("auto_freq_peak_prom"))
        else:
            period_x = self.analysis_prm.get("period_x","auto")
            period_y = self.analysis_prm.get("period_x","auto")
            if period_x is None or period_y is None:
                raise Exception("Period x and y needs to be specify if auto_freq_finder=False")

            fx_exp, fy_exp = 1.0 / period_x, 1.0 / period_y
            fx, fy = fft_constrained_frequency_estimation(image_cropped, fx_exp, fy_exp,
                                                        self.analysis_prm.get("freq_search_window_px"))
        
        # periods
        ax, ay = 1.0 / abs(fx), 1.0 / abs(fy)

        # offsets
        dx0, dy0 = estimate_lattice_offset(image_cropped,ax,ay,self.npx,self.npy)
        
        # base positions
        rx, ry = [], []
        for j in range(self.npy):
            for i in range(self.npx):
                rx.append(i * ax + dx0)
                ry.append(j * ay + dy0)
        rx, ry = np.array(rx), np.array(ry)

        # refined positions
        if self.analysis_prm.get("foci_search_window_px") !=0:
            rx, ry = refine_foci_positions(image_cropped, rx, ry,
                                        method=self.analysis_prm.get("foci_loc_method"),
                                        window=self.analysis_prm.get("foci_search_window_px"))

        # calculate trap_power and metrics
        img_for_preview = image_cropped.copy()
        trap_power = np.empty(self.npx*self.npy, dtype=float)
        for i in range(self.npx*self.npy):
            trap_power[i],img_for_preview = sum_around(img_for_preview, 
                                                       rx[i], ry[i],
                                                       self.analysis_prm.get("foci_integration_size"),
                                                       zero_out=True)

        trap_power = np.array([image_cropped[int(round(y)), int(round(x))] for x, y in zip(rx, ry)])
        efficiency = trap_power.sum() / image_cropped.sum()
        uniformity = 1 - (trap_power.max() - trap_power.min()) / (trap_power.max() + trap_power.min())
        std = trap_power.std() / trap_power.mean()

        analysis = {
            "refined_x": rx,
            "refined_y": ry,
            "trap_power": trap_power,
            "efficiency": efficiency,
            "uniformity": uniformity,
            "std": std
        }

        if show_plot:
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 4))
            ax1.imshow(crop_preview, vmin=0, cmap='gray')
            ax1.set_title('Crop area')

            ax2.imshow(image_cropped, vmin=0, cmap='gray')
            ax2.scatter(rx, ry, c='r', marker='x', s=50, label='Refined traps')
            ax2.set_title('Localized Foci')
            ax2.legend()

            ax3.imshow(img_for_preview,vmin=0,cmap='gray')
            ax3.set_title("Black square = summing region")

            plt.show()

        return analysis


    def _adapt_target_impl(self):
        
        if len(self.analysis_history)==0:
            return None, "No analysis performed yet"

        analysis = self.analysis_history[-1]

        if "trap_power" not in analysis:
            msg = "'Trap_power' not found in analysis results"
            return None, msg
        
        P = analysis["trap_power"]
        weights = P.mean() / (P + 1e-9)

        mask = self.array != 0

        # make weights 1D ==> 2D
        weights_2d = np.zeros_like(self.array, dtype=float)
        weights_2d[mask] = weights

        # Apply the weights
        new_target = self.array * weights_2d

        return new_target, None