import numpy as np
import time
import NanoImagingPack as nip

class MockCameraPCO:
    def __init__(self):
        self.properties = {
            'image_height': 1024,
            'image_width': 1280,
            'subarray_vpos': 0,
            'subarray_hpos': 0,
            'exposure_time': 0.1,
            'subarray_vsize': 1024,
            'subarray_hsize': 1280,
            'SensorHeight': 1024,
            'SensorWidth': 1280
        }
        self.exposure = 100
        self.gain = 1
        self.brightness = 1
        self.model = 'mock'
        self.SensorHeight = 500
        self.SensorWidth = 500
        self.shape = (self.SensorHeight,self.SensorWidth)
        
        self.IIllu = np.ones((self.SensorHeight, self.SensorWidth))
        
        self.ISample = self.generateSample()

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

    def generateSample(self):
        if(0):
            Isample = np.zeros((self.SensorHeight, self.SensorWidth))
            Isample[np.random.random(Isample.shape)>0.999]=1
        else:
            Isample = nip.readim()
            Isample = nip.extract(Isample, (self.SensorHeight, self.SensorWidth))+np.abs(np.random.randn(self.SensorHeight, self.SensorWidth))*3

        return Isample
        
    def grabFrame(self, **kwargs):
        # simulate simple imaging system
        img = nip.gaussf(self.ISample*self.IIllu,2)#+np.random.randn(self.SensorHeight, self.SensorWidth)*.1
        img -= np.min(img)
        img /= np.max(img)
        time.sleep(0.1)
        return np.int8(img*255)

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

    

    ## SIM-simulation related
    
    def setIlluPattern(self, illuPattern):
        self.IIllu=illuPattern
        
    def setIlluPatternByID(self, iRot=0, iPhi=0, Nrot=3, Nphi=3):
        Nx,Ny=self.SensorHeight, self.SensorWidth
        #for iPhi in range(3):
        #    for iRot in range(3):
        IGrating = 1+np.sin(((iRot/Nrot)*nip.xx((Nx,Ny))+(Nrot-iRot)/Nrot*nip.yy((Nx,Ny)))*np.pi/2+2*np.pi*iPhi/Nphi)

        self.setIlluPattern(IGrating)
        return IGrating
                   


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
