import numpy as np
from scipy.stats import multivariate_normal

import time


class MockCameraTIS:
    def __init__(self, isRGB=False, mocktype = None, mockstackpath=None):
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
            self.mocktype = "normal"
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
        self.isRGB = isRGB
        
        self.camera = Camera()
        
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
            
        if self.mocktype == "OffAxisHolo":
            # Parameters
            width, height = self.SensorWidth, self.SensorHeight  # Size of the simulation
            wavelength = 0.6328e-6  # Wavelength of the light (in meters, example: 632.8nm for He-Ne laser)
            k = 2 * np.pi / wavelength  # Wave number
            angle = np.pi / 10  # Tilt angle of the plane wave

            # Create a phase sample (this is where you define your phase object)
            # For demonstration, a simple circular phase object
            x = np.linspace(-np.pi, np.pi, width)
            y = np.linspace(-np.pi, np.pi, height)
            X, Y = np.meshgrid(x, y)
            mPupil = (X**2 + Y**2)<np.pi
            try:
                import NanoImagingPack as nip
                mSample = nip.readim()
                mSample = nip.extract(mSample, (width, height))/255
            except:
                mSample = (X**2 + Y**2)<50 # sphere with radius 50
            phase_sample = np.exp(1j * mSample)
            
            # Simulate the tilted plane wave
            tilt_x =  k * np.sin(angle)
            tilt_y = k * np.sin(angle)  # Change this if you want tilt in another direction
            X, Y = np.meshgrid(np.arange(width), np.arange(height))
            plane_wave = np.exp(1j * ((tilt_x * X) + (tilt_y * Y)))

            
            # Superpose the phase sample and the tilted plane wave
            filtered_phase_sample = np.fft.ifft2(np.fft.fftshift(mPupil) * np.fft.fft2(phase_sample))
            #filtered_phase_sample = nip.ift(mPupil * nip.ft(phase_sample))
            hologram = filtered_phase_sample + plane_wave
            if 0:
                import matplotlib.pyplot as plt
                plt.imshow(np.angle(hologram))
                plt.show()
                #plt.imshow(np.angle(np.conjugate(hologram)))
                #plt.show()
                plt.imshow(np.real(hologram*np.conjugate(hologram)))
                plt.show()
                plt.imshow(np.log(1+np.abs(nip.ft(hologram))))
                plt.show()

            #%%
            # Calculate the intensity image (interference pattern)
            self.holo_intensity_image = np.squeeze(np.real(hologram*np.conjugate(hologram)))




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
        elif self.mocktype=="OffAxisHolo":
            img = self.holo_intensity_image
            self.iFrame+=1
        elif self.mocktype=="normal":
            img = np.zeros((self.SensorHeight, self.SensorWidth)).astype('uint8')
            indices = np.random.randint(0, self.SensorHeight*self.SensorWidth, 1000)
            # Convert the flat indices to 2D indices
            indices_2d = np.unravel_index(indices, (self.SensorHeight, self.SensorWidth))
            img[indices_2d] = np.random.randint(0,255,1000)
        else:
            img = np.zeros((self.SensorHeight, self.SensorWidth))
            beamCenter = [int(np.random.randn() * 30 + 250), int(np.random.randn() * 30 + 300)]
            img[beamCenter[0] - 10:beamCenter[0] + 10, beamCenter[1] - 10:beamCenter[1] + 10] = 1
            img = np.random.randn(img.shape[0],img.shape[1])
        if self.isRGB:
            return np.stack([img, img, img], axis=2)
        else: 
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
    
    
class Camera(object):
    def __init__(self):
        self.Width = 100
        self.Height = 100
        pass

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
