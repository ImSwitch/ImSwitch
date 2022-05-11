import json
import os

import numpy as np

from imswitch.imcommon.model import dirtools, initLogger, APIExport
from ..basecontrollers import ImConWidgetController


class SIMController(ImConWidgetController):
    """Linked to SIMWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        self.simDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_sim')
        if not os.path.exists(self.simDir):
            os.makedirs(self.simDir)

        if self._setupInfo.sim is None:
            self._widget.replaceWithError('SIM is not configured in your setup file.')
            return

        self._widget.initSIMDisplay(self._setupInfo.sim.monitorIdx)
        # self.loadPreset(self._defaultPreset)

        # Connect CommunicationChannel signals
        self._commChannel.sigSIMMaskUpdated.connect(self.displayMask)

        # Connect SIMWidget signals
        self._widget.controlPanel.saveButton.clicked.connect(self.saveParams)
        self._widget.controlPanel.loadButton.clicked.connect(self.loadParams)

        self._widget.applyChangesButton.clicked.connect(self.applyParams)
        self._widget.sigSIMDisplayToggled.connect(self.toggleSIMDisplay)
        self._widget.sigSIMMonitorChanged.connect(self.monitorChanged)
        self._widget.sigPatternID.connect(self.patternIDChanged)
        
        self.patternID = 0

        # Initial SIM display
        #self.displayMask(self._master.simManager.maskCombined)

    def toggleSIMDisplay(self, enabled):
        self._widget.setSIMDisplayVisible(enabled)

    def monitorChanged(self, monitor):
        self._widget.setSIMDisplayMonitor(monitor)
        
    def patternIDChanged(self, patternID):
        self.patternID = patternID

    def displayMask(self, maskCombined):
        """ Display the mask in the SIM display. Originates from simPy:
        https://github.com/wavefrontshaping/simPy """

        arr = maskCombined.image()

        # Padding: Like they do in the software
        pad = np.zeros((600, 8), dtype=np.uint8)
        arr = np.append(arr, pad, 1)

        # Create final image array
        h, w = arr.shape[0], arr.shape[1]

        if len(arr.shape) == 2:
            # Array is grayscale
            arrGray = arr.copy()
            arrGray.shape = h, w, 1
            img = np.concatenate((arrGray, arrGray, arrGray), axis=2)
        else:
            img = arr

        self._widget.updateSIMDisplay(img)

    def saveParams(self):
        pass

    def loadParams(self):
        pass
    
    def applyParams(self):
        currentPattern = self._master.simManager.allPatterns[self.patternID]
        self.updateDisplayImage(currentPattern)
 
    def updateDisplayImage(self, image):
        image = np.fliplr(image.transpose())
        self._widget.img.setImage(image, autoLevels=True, autoDownsample=False)
        # self._logger.debug("Updated displayed image")

    @APIExport(runOnUIThread=True)
    def simPatternByID(self, patternID):
        currentPattern = self._master.simManager.allPatterns[patternID]
        self.updateDisplayImage(currentPattern)
    

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
