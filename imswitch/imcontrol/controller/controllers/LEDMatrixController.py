from typing import Dict, List
from functools import partial
from qtpy import QtCore, QtWidgets

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

        self._widget.add_matrix_view(self.nLedsX, self.nLedsY)
        self.connect_leds()
        
        illuminatorList = self._master.lasersManager.getAllDeviceNames()
        index = [index for (index , item) in enumerate(illuminatorList) if (item.find("Matrix")>0)][0]
        self.ledmatrix_name = illuminatorList[index]
        self.ledmatrix = self._master.lasersManager[self.ledmatrix_name]
        
        self.LEDMatrixDevice = LEDMatrixDevice(self.ledmatrix)
        
        # Connect LaserWidget signals
        self._widget.ButtonAllOn.clicked.connect(self.setLEDAllOn)      
        self._widget.ButtonAllOff.clicked.connect(self.setLEDAllOn)      
        self._widget.ButtonSubmit.clicked.connect(self.submitLEDPattern)
        self._widget.ButtonToggle.clicked.connect(self.toggleLEDPattern)
        
        
    @APIExport()
    def setLEDAllOn(self):
        self.LEDMatrixDevice.setAllOn()
        
    @APIExport()
    def setLEDAllOff(self):
        self.LEDMatrixDevice.setAllOff()

    @APIExport()
    def submitLEDPattern(self):
        self.LEDMatrixDevice.setLEDPattern()

    @APIExport()
    def toggleLEDPattern(self):
        self.LEDMatrixDevice.toggleLEDPattern()
        
    @APIExport()
    def switchLED(self, LEDid):
        self.LEDMatrixDevice.switchLED(LEDid)

    def connect_leds(self):
        """Connect leds (Buttons) to the Sample Pop-Up Method"""
        # Connect signals for all buttons
        for coords, btn in self._widget.leds.items():
            # Connect signals
            #self.pars['UpButton' + parNameSuffix].clicked.connect(
            #    lambda *args, axis=axis: self.sigStepUpClicked.emit(ledMatrixName, axis)
            #)
            if isinstance(btn, guitools.BetterPushButton):
                btn.clicked.connect(partial(self.switchLED, coords))
                

class LEDMatrixDevice():
    
    def __init__(self, ledMatrix, platepattern="96"):
        
        self.ledMatrix = ledMatrix 
        self.pattern = None
        
          
    def switchLED(self, LEDid):
        pass
    
    def setAllOn(self):
        #self.ledMatrix.XX
        pass
    
    def setAllOff(self):
        pass
    
    def setLEDPattern(self):
        pass
    
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
