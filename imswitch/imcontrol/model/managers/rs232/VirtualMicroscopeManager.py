from imswitch.imcommon.model import initLogger
from imswitch.imcommon.model import APIExport

try:
    import NanoImagingPack as nip

    IS_NIP = True
except:
    IS_NIP = False
import numpy as np
import matplotlib.pyplot as plt
import threading
import time
import numpy as np
import cv2
import threading
import time
import numpy as np
import imswitch
import os
import math

try:
    from numba import njit, prange
except ModuleNotFoundError:
    prange = range

    def njit(*args, **kwargs):
        def wrapper(func):
            return func

        return wrapper

from nanopyx import eSRRF


class VirtualMicroscopeManager:
    """A low-level wrapper for TCP-IP communication (ESP32 REST API)"""

    def __init__(self, rs232Info, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self._settings = rs232Info.managerProperties
        self._name = name
        try:
            self._mode = rs232Info.managerProperties["mode"]
            self._imagePath = rs232Info.managerProperties['imagePath']
        except:
            self._mode = "example"
            package_dir = os.path.dirname(os.path.abspath(imswitch.__file__))

            self._imagePath = os.path.join(
                package_dir, "_data/images/histoASHLARStitch.jpg"
            )

        self._virtualMicroscope = VirtualMicroscopy(self._mode, self._imagePath)
        self._positioner = self._virtualMicroscope.positioner
        self._camera = self._virtualMicroscope.camera
        self._illuminator = self._virtualMicroscope.illuminator

        """
        # Test the functionality
        for i in range(10):
            microscope.positioner.move(x=5, y=5)
            microscope.illuminator.set_intensity(intensity=1.5)
            frame = microscope.get_frame()
            cv2.imshow("Microscope View", frame)
            cv2.waitKey(100)

        cv2.destroyAllWindows()
        """

    def finalize(self):
        self._virtualMicroscope.stop()


class Camera:
    def __init__(self, parent, mode, imagePath):
        self._parent = parent
        self.mode = mode
        self.image = np.mean(cv2.imread(imagePath), axis=2)

        self.image /= np.max(self.image)
        self.lock = threading.Lock()
        self.SensorWidth = 512  # self.image.shape[1]
        self.SensorHeight = 512  # self.image.shape[0]
        self.model = "VirtualCamera"
        self.PixelSize = 1.0
        self.isRGB = False
        self.frameNumber = 0
        self.return_raw = False
        # precompute noise so that we will save energy and trees
        if mode == "example":
            self.noiseStack = (
                np.random.randn(self.SensorHeight, self.SensorWidth, 100) * 0.15
            )

        print(self._parent)

    def produce_frame(
        self, x_offset=0, y_offset=0, light_intensity=1.0, defocusPSF=None
    ):
        """Generate a frame based on the current settings."""
        with self.lock:
            # add moise
            image = self.image.copy()
            # Adjust image based on offsets
            image = np.roll(
                np.roll(image, int(x_offset), axis=1), int(y_offset), axis=0
            )
            image = nip.extract(image, (self.SensorWidth, self.SensorHeight))

            # do all post-processing on cropped image
            if IS_NIP and defocusPSF is not None and not defocusPSF.shape == ():
                print("Defocus:" + str(defocusPSF.shape))
                image = np.array(np.real(nip.convolve(image, defocusPSF)))
            image = np.float32(image) / np.max(image) * np.float32(light_intensity)
            # image += self.noiseStack[:,:,np.random.randint(0,100)]

            # Adjust illumination
            image = image.astype(np.uint16)
            time.sleep(0.1)
            return np.array(image)

    def produce_smlm_frame(
        self, x_offset: int = 0, y_offset: int  = 0, n_photons: int = 5000, n_photons_std:int = 50
    ):
        """Generate a frame based on the current settings."""
        with self.lock:
            # add moise
            image = self.image.copy()
            # Adjust image based on offsets
            image = np.roll(
                np.roll(image, int(x_offset), axis=1), int(y_offset), axis=0
            )
            image = nip.extract(image, (self.SensorWidth, self.SensorHeight))

            yc_array, xc_array = self.binary2locs(image, density=0.05)
            photon_array = np.random.normal(n_photons, n_photons_std, size=len(xc_array))

            wavelenght = 6  # change to get it from microscope settings
            wavelenght_std = 0.5  # change to get it from microscope settings
            NA = 1.2  # change to get it from microscope settings
            sigma = 0.21*wavelenght / NA  # change to get it from microscope settings
            sigma_std = 0.21*wavelenght_std / NA  # change to get it from microscope settings
            sigma_array = np.random.normal(sigma, sigma_std, size=len(xc_array))

            ADC_per_photon_conversion = 1.0  # change to get it from microscope settings
            readout_noise = 50  # change to get it from microscope settings
            ADC_offset = 100  # change to get it from microscope settings

            out = FromLoc2Image_MultiThreaded(xc_array, yc_array, photon_array, sigma_array, self.SensorHeight, self.PixelSize)
            out = ADC_per_photon_conversion * np.random.poisson(out) + readout_noise * np.random.normal(size=(self.SensorHeight, self.SensorWidth)) + ADC_offset
            time.sleep(0.1)
            return np.array(out)

    def binary2locs(self, img: np.ndarray, density: float):
        all_locs = np.nonzero(img == 1)
        n_points = int(len(all_locs[0]) * density)
        selected_idx = np.random.choice(len(all_locs[0]), n_points, replace=False)
        filtered_locs = all_locs[0][selected_idx], all_locs[1][selected_idx]
        return filtered_locs

    def getLast(self, returnFrameNumber=False):
        position = self._parent.positioner.get_position()
        defocusPSF = np.squeeze(self._parent.positioner.get_psf())
        intensity = self._parent.illuminator.get_intensity(1)
        self.frameNumber += 1
        if self.mode == "example":
            if returnFrameNumber:
                return (
                    self.produce_frame(
                        x_offset=position["X"],
                        y_offset=position["Y"],
                        light_intensity=intensity,
                        defocusPSF=defocusPSF,
                    ),
                    self.frameNumber,
                )
            else:
                return self.produce_frame(
                    x_offset=position["X"],
                    y_offset=position["Y"],
                    light_intensity=intensity,
                    defocusPSF=defocusPSF,
                )
        elif self.mode == "SMLM":
            if returnFrameNumber:
                return (
                    self.produce_smlm_frame(
                        x_offset=position["X"],
                        y_offset=position["Y"],
                        n_photons=intensity,
                        n_photons_std=intensity*0.01
                    ),
                    self.frameNumber,
                )
            else:
                return self.produce_smlm_frame(
                    x_offset=position["X"],
                    y_offset=position["Y"],
                    n_photons=intensity,
                    n_photons_std=intensity*0.01
                )
        elif self.mode == "eSRRF":
            current_frame = self.produce_smlm_frame(
                x_offset=position["X"],
                y_offset=position["Y"],
                n_photons=intensity,
                n_photons_std=intensity*0.01
            )
            rgc_frame = np.asarray([eSRRF(current_frame, magnification=2, _force_run_type="threaded")[0]])
            rows, cols = rgc_frame.shape[-2:]
            rgc_frame = np.squeeze(rgc_frame).reshape(1, rows, cols)
            previous_frames = self._parent.get_rgc_maps()
            if previous_frames is not None:
                combined_rgc = np.concatenate((previous_frames[1:], rgc_frame))
                self._parent.set_acquired_frames(np.concatenate((self.get_acquired_frames(), current_frame)))
                self._parent.set_rgc_maps(combined_rgc)
                if self.return_raw:
                    return np.mean(combined_rgc, axis=0), np.squeeze(self._parent.get_acquired_frames())
                else:
                    return np.mean(combined_rgc, axis=0)

            else:
                self._parent.set_acquired_frames(current_frame)
                self._parent.set_rgc_maps(rgc_frame)
                if self.return_raw:
                    return np.squeeze(current_frame), np.squeeze(self._parent.get_acquired_frames())
                else:
                    return np.squeeze(current_frame)

    def setPropertyValue(self, propertyName, propertyValue):
        pass


class Positioner:
    def __init__(self, parent):
        self._parent = parent
        self.position = {"X": 0, "Y": 0, "Z": 0, "A": 0}
        self.mDimensions = (
            self._parent.camera.SensorWidth,
            self._parent.camera.SensorHeight,
        )
        self.lock = threading.Lock()
        if IS_NIP:
            self.psf = self.compute_psf(dz=0)
        else:
            self.psf = None

    def move(self, x=None, y=None, z=None, a=None, is_absolute=False):
        self._parent.acquired_frames = None
        with self.lock:
            if is_absolute:
                if x is not None:
                    self.position["X"] = x
                if y is not None:
                    self.position["Y"] = y
                if z is not None:
                    self.position["Z"] = z
                    self.compute_psf(self.position["Z"])
                if a is not None:
                    self.position["A"] = a
            else:
                if x is not None:
                    self.position["X"] += x
                if y is not None:
                    self.position["Y"] += y
                if z is not None:
                    self.position["Z"] += z
                    self.compute_psf(self.position["Z"])
                if a is not None:
                    self.position["A"] += a

    def get_position(self):
        with self.lock:
            return self.position.copy()

    def compute_psf(self, dz):
        dz = np.float32(dz)
        print("Defocus:" + str(dz))
        if IS_NIP and dz != 0:
            obj = nip.image(np.zeros(self.mDimensions))
            obj.pixelsize = (100.0, 100.0)
            paraAbber = nip.PSF_PARAMS()
            # aber_map = nip.xx(obj.shape[-2:]).normalize(1)
            paraAbber.aberration_types = [paraAbber.aberration_zernikes.spheric]
            paraAbber.aberration_strength = [np.float32(dz) / 10]
            psf = nip.psf(obj, paraAbber)
            self.psf = psf.copy()
            del psf
            del obj
        else:
            self.psf = None

    def get_psf(self):
        return self.psf


@njit(parallel=True)
def FromLoc2Image_MultiThreaded(xc_array, yc_array, photon_array, sigma_array, image_size, pixel_size):
    Image = np.zeros((image_size, image_size))
    for ij in prange(image_size*image_size):
        j = int(ij/image_size)
        i = ij - j*image_size
        for (xc, yc, photon, sigma) in zip(xc_array, yc_array, photon_array, sigma_array):
            # Don't bother if the emitter has photons <= 0 or if Sigma <= 0
            if (photon > 0) and (sigma > 0):
                S = sigma*math.sqrt(2)
                x = i*pixel_size - xc
                y = j*pixel_size - yc
                # Don't bother if the emitter is further than 4 sigma from the centre of the pixel
                if (x+pixel_size/2)**2 + (y+pixel_size/2)**2 < 16*sigma**2:
                    ErfX = math.erf((x+pixel_size)/S) - math.erf(x/S)
                    ErfY = math.erf((y+pixel_size)/S) - math.erf(y/S)
                    Image[j][i] += 0.25*photon*ErfX*ErfY
    return Image


class Illuminator:
    def __init__(self, parent):
        self._parent = parent
        self.intensity = 0
        self.lock = threading.Lock()

    def set_intensity(self, channel=1, intensity=0):
        with self.lock:
            self.intensity = intensity

    def get_intensity(self, channel):
        with self.lock:
            return self.intensity


class VirtualMicroscopy:
    def __init__(self, mode, imagePath):
        self.camera = Camera(self, mode, imagePath)
        self.positioner = Positioner(self)
        self.illuminator = Illuminator(self)
        self.acquired_frames = None
        self.rgc_maps = None

    def stop(self):
        pass

    def set_acquired_frames(self, img):
        self.acquired_frames = img

    def get_acquired_frames(self):
        return self.acquired_frames

    def set_rgc_maps(self, img):
        self.rgc_maps = img

    def get_rgc_maps(self):
        return self.rgc_maps


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Read the image locally
    mFWD = os.path.dirname(os.path.realpath(__file__)).split("imswitch")[0]
    imagePath = mFWD + "imswitch/_data/images/binary2.jpg"
    microscope = VirtualMicroscopy("eSRRF", imagePath)
    microscope.illuminator.set_intensity(intensity=5000)

    for i in range(10):
        microscope.positioner.move(x=i, y=i, z=i, is_absolute=True)
        frame = microscope.camera.getLast()
        plt.imsave(f"frame_{i}.png", frame)
    cv2.destroyAllWindows()

# Copyright (C) 2020-2023 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
