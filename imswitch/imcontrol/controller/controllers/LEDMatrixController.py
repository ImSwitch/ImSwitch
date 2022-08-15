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
        self._widget.slider.valueChanged.connect(self.setIntensity)

    def setAllLEDOn(self):
        self.setAllLED(state=(1,1,1))

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
        self._widget.leds[str(LEDid)].setChecked(np.mean(pattern[int(LEDid)])>0)

    def connect_leds(self):
        """Connect leds (Buttons) to the Sample Pop-Up Method"""
        # Connect signals for all buttons
        for coords, btn in self._widget.leds.items():
            # Connect signals
            if isinstance(btn, guitools.BetterPushButton):
                btn.clicked.connect(partial(self.setLED, coords))

'''

class LEDMatrixDevice():

    def __init__(self, ledMatrix, Nx=8, Ny=8):
        self.Nx=Nx
        self.Ny=Ny
        self.ledMatrix = ledMatrix
        self.pattern = np.zeros((self.Nx*self.Ny,3))
        self.intensity = (255,255,255)
        self.state=None

        # set dimensions on the hardware side
        self.prepareLEDMatrix(self.Nx, self.Ny)

        # Turn off LEDs


    def setIntensity(self, intensity=None):
        if intensity is None or type(intensity)==bool:
            intensity = self.intensity
        self.pattern = (self.pattern>0)*(intensity,intensity,intensity)
        self.intensity = (intensity,intensity,intensity)
        self.ledMatrix.setPattern(self.pattern)

    def setPattern(self, pattern):
        self.pattern = pattern
        self.ledMatrix.setPattern(self.pattern)
        self.state="pattern"

    def setLED(self, index, intensity=None):
        if intensity is None or type(intensity)==bool:
            intensity = self.intensity
        index = int(index)
        if np.sum(self.pattern[index,:]):
            self.pattern[index,:] = (0,0,0)
        else:
            self.pattern[index,:] = intensity
        self.ledMatrix.setLEDSingle(indexled=index,intensity=self.pattern[index,:])
'''


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
