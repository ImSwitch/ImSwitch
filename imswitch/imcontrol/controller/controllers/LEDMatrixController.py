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
        self._widget.add_matrix_view(self.nLedsX, self.nLedsY)
        self.connect_leds()

        # initialize matrix
        self.setAllLEDOff()

        self._widget.ButtonAllOn.clicked.connect(self.setAllLEDOn)
        self._widget.ButtonAllOff.clicked.connect(self.setAllLEDOff)
        self._widget.slider.sliderReleased.connect(self.setIntensity)
        self._widget.ButtonSpecial1.clicked.connect(self.setSpecial1)
        self._widget.ButtonSpecial2.clicked.connect(self.setSpecial2)
        

    @APIExport()
    def setAllLEDOn(self):
        self.setAllLED(state=(1,1,1))

    def setSpecial1(self):
        isChecked = self._widget.ButtonSpecial1.isChecked()
        self._widget.ButtonSpecial1.setChecked(not isChecked)
        isActive = self._widget.ButtonSpecial1.isChecked()
        SpecialPattern1 = self._master.LEDMatrixsManager._subManagers['ESP32 LEDMatrix'].SpecialPattern1
        intensity = 255 * isActive
        self.setSpecial(SpecialPattern1, intensity = intensity)
        
    def setSpecial2(self):
        isChecked = self._widget.ButtonSpecial2.isChecked()
        self._widget.ButtonSpecial2.setChecked(not isChecked)
        isActive = self._widget.ButtonSpecial2.isChecked()
        SpecialPattern2 = self._master.LEDMatrixsManager._subManagers['ESP32 LEDMatrix'].SpecialPattern2
        intensity = 255 * isActive
        self.setSpecial(SpecialPattern2, intensity = intensity)
                
    @APIExport()
    def setSpecial(self, pattern, intensity = 255, getReturn=False):
        self.setAllLEDOff()
        
        # set intensity in case it was changed
        for idLED in range(len(pattern)):
            pattern[idLED]['r'] = int(pattern[idLED]['r'] > 0) * intensity
            pattern[idLED]['g'] = int(pattern[idLED]['g'] > 0) * intensity
            pattern[idLED]['b'] = int(pattern[idLED]['b'] > 0) * intensity
        
        # send pattern
        r = self.ledMatrix.setIndividualPattern(pattern, getReturn = getReturn)
        return r
        

        
    @APIExport()
    def setAllLEDOff(self):
        self.setAllLED(state=(0,0,0))

    @APIExport()
    def setAllLED(self, state=None, intensity=None):
        if intensity is not None:
            self.setIntensity(intensity=intensity)
        self.ledMatrix.setAll(state=state)
        for coords, btn in self._widget.leds.items():
            if isinstance(btn, guitools.BetterPushButton):
                btn.setChecked(np.sum(state)>0)

    @APIExport()
    def setIntensity(self, intensity=None):
        if intensity is None:
            intensity = int(self._widget.slider.value()//1)
        else:
            # this is only if the GUI/API is calling this function
            intensity = int(intensity)

        self.ledMatrix.setLEDIntensity(intensity=(intensity,intensity,intensity))

    @APIExport()
    def setLED(self, LEDid, state=None):
        self._ledmatrixMode = "single"
        self.ledMatrix.setLEDSingle(indexled=int(LEDid), state=state)
        pattern = self.ledMatrix.getPattern()
        self._widget.leds[str(LEDid)].setChecked(state)

    def connect_leds(self):
        """Connect leds (Buttons) to the Sample Pop-Up Method"""
        # Connect signals for all buttons
        for coords, btn in self._widget.leds.items():
            # Connect signals
            if isinstance(btn, guitools.BetterPushButton):
                btn.clicked.connect(partial(self.setLED, coords))


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
