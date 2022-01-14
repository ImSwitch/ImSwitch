import numpy as np
from scipy.stats import multivariate_normal


class MockCameraTIS:
    def __init__(self):
        self.properties = {
            'image_height': 1024,
            'image_width': 1280,
            'subarray_vpos': 0,
            'subarray_hpos': 0,
            'exposure_time': 0.1,
            'subarray_vsize': 1024,
            'subarray_hsize': 1280
        }
        self.exposure = 100
        self.gain = 1
        self.brightness = 1
        self.model = 'mock'

    def start_live(self):
        pass

    def stop_live(self):
        pass

    def suspend_live(self):
        pass

    def prepare_live(self):
        pass

    def setROI(self, hpos, vpos, hsize, vsize):
        pass

    def grabFrame(self, **kwargs):
        mocktype = "widefield"
        if mocktype=="focus_lock":
            img = np.zeros((500, 600))
            beamCenter = [int(np.random.randn() * 1 + 250), int(np.random.randn() * 30 + 300)]
            img[beamCenter[0] - 10:beamCenter[0] + 10, beamCenter[1] - 10:beamCenter[1] + 10] = 1
        elif mocktype=="widefield":
            imgsize = (800, 800)
            peakmax = 60
            noisemean = 10
            # generate image
            img = np.zeros(imgsize)
            # add a random gaussian peak sometimes
            if np.random.rand() > 0.8:
                x, y = np.meshgrid(np.linspace(0,imgsize[1],imgsize[1]), np.linspace(0,imgsize[0],imgsize[0]))
                pos = np.dstack((x, y))
                xc = (np.random.rand()*2-1)*imgsize[0]/2 + imgsize[0]/2
                yc = (np.random.rand()*2-1)*imgsize[1]/2 + imgsize[1]/2
                rv = multivariate_normal([xc, yc], [[50, 0], [0, 50]])
                img = np.random.rand()*peakmax*317*rv.pdf(pos)
                img = img + 0.01*np.random.poisson(img)
            # add Poisson noise
            img = img + np.random.poisson(lam=noisemean, size=imgsize)
        return img

    def setPropertyValue(self, property_name, property_value):
        return property_value

    def getPropertyValue(self, property_name):
        return self.properties[property_name]

    def openPropertiesGUI(self):
        pass


# Copyright (C) 2020-2021 ImSwitch developers
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
