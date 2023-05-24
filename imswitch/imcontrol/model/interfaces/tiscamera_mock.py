import numpy as np
from scipy.stats import multivariate_normal

import time


class MockCameraTIS:
    def __init__(self, mocktype = None, mockstackpath=None):
        self.properties = {
            'image_height': 500,
            'image_width': 500,
            'subarray_vpos': 0,
            'subarray_hpos': 0,
            'exposure_time': 0.1,
            'subarray_vsize': 500,
            'subarray_hsize': 500,
            'SensorHeight': 500,
            'SensorWidth': 500,
            'pixelSize': 1
        }
        if mocktype is None:
            self.mocktype = "default"
        else:
            self.mocktype = mocktype
        
        if mockstackpath is not None:
            self.mockstackpath = mockstackpath
        self.exposure = 100
        self.gain = 1
        self.brightness = 1
        self.model = 'mock'
        self.SensorHeight = 500
        self.SensorWidth = 500
        self.shape = (self.SensorHeight,self.SensorWidth)
        self.pixelSize = 1
        self.iFrame = 0
        
        if self.mocktype == "STORM":
            import tifffile as tif

            # Open the TIFF file
            mFile = self.mockstackpath
            self.tifr = tif.TiffFile(mFile)
            dummyFrame = self.tifr.pages[0].asarray()
            self.SensorHeight = dummyFrame.shape[0]
            self.SensorWidth = dummyFrame.shape[0]
            self.properties['SensorHeight'] = self.SensorHeight
            self.properties['SensorWidth'] = self.SensorWidth


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

    def setBinning(self, binning):
        pass

    def grabFrame(self, **kwargs):
        
        if self.mocktype=="focus_lock":
            img = np.zeros((self.SensorHeight, self.SensorWidth))
            beamCenter = [int(np.random.randn() * 1 + 250), int(np.random.randn() * 30 + 300)]
            img[beamCenter[0] - 10:beamCenter[0] + 10, beamCenter[1] - 10:beamCenter[1] + 10] = 1
        elif self.mocktype=="random_peak":
            imgsize = (self.SensorHeight, self.SensorWidth)
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
        elif self.mocktype=="STORM":
            # Iterate over the pages in the TIFF file
            img = self.tifr.pages[self.iFrame%len(self.tifr.pages)].asarray()
            self.iFrame+=1
        elif self.mocktype=="default":
            img = np.random.randint(0, 255, (self.SensorHeight, self.SensorWidth, 3)).astype('uint8')
        else:
            img = np.zeros((self.SensorHeight, self.SensorWidth))
            beamCenter = [int(np.random.randn() * 30 + 250), int(np.random.randn() * 30 + 300)]
            img[beamCenter[0] - 10:beamCenter[0] + 10, beamCenter[1] - 10:beamCenter[1] + 10] = 1
            img = np.random.randn(img.shape[0],img.shape[1])
        return np.abs(img)

    def getLast(self, is_resize=False):
        return self.grabFrame()
    
    def getLastChunk(self):
        return np.expand_dims(self.grabFrame(),0)
    
    def setPropertyValue(self, property_name, property_value):
        return property_value

    def getPropertyValue(self, property_name):
        try:
            return self.properties[property_name]
        except Exception as e:
            return 0

    def openPropertiesGUI(self):
        pass
    
    def close(self):
        pass

    def close(self):
        pass
    
    def flushBuffer(self):
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
