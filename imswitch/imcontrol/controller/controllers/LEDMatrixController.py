from typing import Dict, List
from functools import partial
from qtpy import QtCore, QtWidgets
import numpy as np

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcontrol.view import guitools as guitools
from imswitch.imcommon.model import initLogger, APIExport

class LEDMatrixController(ImConWidgetController):
    """ Linked to LEDMatrixWidget."""

    def __init__(self, nLedsX = 8, nLedsY=8, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        
        self.nLedsX = nLedsX
        self.nLedsY = nLedsY

        # get the name that looks like an LED Matrix
        self.ledmatrix_name = self._master.LEDMatrixsManager.getAllDeviceNames()[0]
        self.ledmatrix = self._master.LEDMatrixsManager[self.ledmatrix_name]
        
        # initialize the LEDMatrix device that holds all necessary states^
        self.LEDMatrixDevice = LEDMatrixDevice(self.ledmatrix,Nx=self.nLedsX,Ny=self.nLedsY)
        
        # set up GUI and "wire" buttons
        self._widget.add_matrix_view(self.nLedsX, self.nLedsY)
        self.connect_leds()
        
        self._widget.ButtonAllOn.clicked.connect(self.setLEDAllOn)      
        self._widget.ButtonAllOff.clicked.connect(self.setLEDAllOff)      
        self._widget.ButtonSubmit.clicked.connect(self.submitLEDPattern)
        self._widget.ButtonToggle.clicked.connect(self.toggleLEDPattern)
        self._widget.slider.valueChanged.connect(self.setIntensity)
        
        
    @APIExport()
    def setLEDAllOn(self):
        self.LEDMatrixDevice.setAllOn()
        
    @APIExport()
    def setLEDAllOff(self):
        self.LEDMatrixDevice.setAllOff()

    @APIExport()
    def submitLEDPattern(self):
        pass #  self.LEDMatrixDevice.setPattern()

    @APIExport()
    def toggleLEDPattern(self):
        pass #self.LEDMatrixDevice.toggleLEDPattern()
        
    @APIExport()
    def setIntensity(self, intensity=None):
        if intensity is None:
            intensity = int(self._widget.slider.value()//1)
        self.LEDMatrixDevice.setIntensity(intensity=intensity)
        
    @APIExport()
    def switchLED(self, LEDid):
        self.LEDMatrixDevice.switchLED(LEDid)

    def connect_leds(self):
        """Connect leds (Buttons) to the Sample Pop-Up Method"""
        # Connect signals for all buttons
        for coords, btn in self._widget.leds.items():
            # Connect signals
            if isinstance(btn, guitools.BetterPushButton):
                btn.clicked.connect(partial(self.switchLED, coords))
                

class LEDMatrixDevice():
    
    def __init__(self, ledMatrix, Nx=8, Ny=8):
        self.Nx=Nx
        self.Ny=Ny
        self.ledMatrix = ledMatrix 
        self.pattern = np.zeros((self.Nx*self.Ny,3))
        self.intensity = (255,255,255)
        self.state=None
        
        # Turn off LEDs
        self.ledMatrix.setAll(intensity=(0,0,0))
        
    def setIntensity(self, intensity=None):
        if intensity is None:
            intensity = self.intensity  
        self.intensity = (intensity,intensity,intensity)
        
    def setPattern(self, pattern):
        self.pattern = pattern
        self.ledMatrix.setPattern(self.pattern)
        self.state="pattern"
          
    def switchLED(self, index, intensity=None):
        if intensity is None:
            intensity = self.intensity
        index = int(index)
        if np.sum(self.pattern[index,:]):
            self.pattern[index,:] = (0,0,0) 
        else:
            self.pattern[index,:] = intensity
        self.ledMatrix.setLEDSingle(indexled=index, intensity=intensity)
    
    def setAllOn(self, intensity=None):
        if intensity is None:
            intensity = self.intensity
        self.pattern = np.ones((self.Nx*self.Ny, 3))*intensity
        self.ledMatrix.setAll(intensity=intensity)
    
    def setAllOff(self):
        self.pattern = np.zeros((self.Nx*self.Ny, 3))
        self.ledMatrix.setAll(intensity=(0,0,0))
    
    def toggleLEDPattern(self):
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
