from typing import Dict, List
from functools import partial
import numpy as np

import imswitch
from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcontrol.view import guitools as guitools
from imswitch.imcommon.model import initLogger, APIExport

class LEDMatrixController(ImConWidgetController):
    """ Linked to LEDMatrixWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        # TODO: This must be easier?
        self.nLedsX = self._master.LEDMatrixsManager._subManagers['ESP32 LEDMatrix'].Nx
        self.nLedsY = self._master.LEDMatrixsManager._subManagers['ESP32 LEDMatrix'].Ny

        self._ledmatrixMode = ""

        # get the name that looks like an LED Matrix
        self.ledMatrix_name = self._master.LEDMatrixsManager.getAllDeviceNames()[0]
        self.ledMatrix = self._master.LEDMatrixsManager[self.ledMatrix_name]

        # set up GUI and "wire" buttons
        self.connect_leds()

        # initialize matrix
        self.setAllLEDOff()

        if imswitch.IS_HEADLESS:
            return
        self._widget.add_matrix_view(self.nLedsX, self.nLedsY)
        self._widget.ButtonAllOn.clicked.connect(self.setAllLEDOn)
        self._widget.ButtonAllOff.clicked.connect(self.setAllLEDOff)
        self._widget.slider.sliderReleased.connect(self.setIntensity)
        self._widget.ButtonSpecial1.clicked.connect(self.setSpecial1)
        self._widget.ButtonSpecial2.clicked.connect(self.setSpecial2)
        

    @APIExport()
    def setAllLEDOn(self, getReturn=True):
        self.setAllLED(state=(1,1,1), getReturn=getReturn)

    def setSpecial1(self):
        SpecialPattern1 = self._master.LEDMatrixsManager._subManagers['ESP32 LEDMatrix'].SpecialPattern1.copy()
        self.setSpecial(SpecialPattern1, intensity = intensity)
        if not imswitch.IS_HEADLESS: intensity = self._widget.slider.value()
        
    def setSpecial2(self):
        SpecialPattern2 = self._master.LEDMatrixsManager._subManagers['ESP32 LEDMatrix'].SpecialPattern2.copy()
        self.setSpecial(SpecialPattern2, intensity = intensity)
        if not imswitch.IS_HEADLESS: intensity = self._widget.slider.value()
                
    @APIExport()
    def setSpecial(self, pattern, intensity = 255, getReturn=False):
        #self.setAllLEDOff()
        
        # set intensity in case it was changed
        for idLED in range(len(pattern)):
            pattern[idLED]['r'] = int(pattern[idLED]['r'] > 0) * intensity
            pattern[idLED]['g'] = int(pattern[idLED]['g'] > 0) * intensity
            pattern[idLED]['b'] = int(pattern[idLED]['b'] > 0) * intensity
        
        # send pattern
        r = self.ledMatrix.setIndividualPattern(pattern, getReturn = getReturn)
        return r
        

        
    @APIExport()
    def setAllLEDOff(self, getReturn=True):
        self.setAllLED(state=(0,0,0),getReturn=getReturn)

    @APIExport()
    def setAllLED(self, state=None, intensity=None, getReturn=True):
        if intensity is not None:
            self.setIntensity(intensity=intensity)
        self.ledMatrix.setAll(state=state,getReturn=getReturn)
        if imswitch.IS_HEADLESS: return
        for coords, btn in self._widget.leds.items():
            if isinstance(btn, guitools.BetterPushButton):
                btn.setChecked(np.sum(state)>0)

    @APIExport()
    def setIntensity(self, intensity=None):
        if intensity is None:
            if not imswitch.IS_HEADLESS: intensity = int(self._widget.slider.value()//1)
        else:
            # this is only if the GUI/API is calling this function
            intensity = int(intensity)

        self.ledMatrix.setLEDIntensity(intensity=(intensity,intensity,intensity))

    @APIExport()
    def setLED(self, LEDid, state=None):
        self._ledmatrixMode = "single"
        self.ledMatrix.setLEDSingle(indexled=int(LEDid), state=state)
        pattern = self.ledMatrix.getPattern()
        if not imswitch.IS_HEADLESS: self._widget.leds[str(LEDid)].setChecked(state)

    def connect_leds(self):
        """Connect leds (Buttons) to the Sample Pop-Up Method"""
        # Connect signals for all buttons
        if imswitch.IS_HEADLESS: return
        for coords, btn in self._widget.leds.items():
            # Connect signals
            if isinstance(btn, guitools.BetterPushButton):
                btn.clicked.connect(partial(self.setLED, coords))

    def setEnabled(self, enabled) -> None:
        """ Sets the value of the LEDMatrix. """
        self.setAllLED(state=enabled, intensity=None)
    
    def setValue(self, value) -> None:
        """ Sets the value of the LEDMatrix. """
        self.setIntensity(intensity=value)
        self.setAllLED(state=(1,1,1), intensity=value)
    

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
