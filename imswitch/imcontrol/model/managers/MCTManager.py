import enum
import glob
import cv2
import os

import numpy as np
from PIL import Image
from scipy import signal as sg

from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger


class MCTManager(SignalInterface):
    sigMCTMaskUpdated = Signal(object)  # (maskCombined)

    def __init__(self, mctInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        if mctInfo is None:
            return

        self.__mctInfo = mctInfo
        self.__wavelength = self.__mctInfo.wavelength
        self.__pixelsize = self.__mctInfo.pixelSize
        self.__angleMount = self.__mctInfo.angleMount
        self.__mctSize = (self.__mctInfo.width, self.__mctInfo.height)
        self.__patternsDir = self.__mctInfo.patternsDir
        
        # Load all patterns
        self.allPatterns = self.loadPatterns(self.__patternsDir)

        self.update()

    def loadPatterns(self,patternsDir, filetype="bmp"):
        allPatternPaths = glob.glob(os.path.join(patternsDir, "*."+filetype))
        allPatterns = []
        for iPatternPath in allPatternPaths:
            mImage = cv2.imread(iPatternPath)
            mImage = cv2.cvtColor(mImage, cv2.COLOR_BGR2GRAY)
            allPatterns.append(mImage)
            print(iPatternPath)
        return allPatterns
        
        
    def saveState(self, state_general=None, state_pos=None, state_aber=None):
        if state_general is not None:
            self.state_general = state_general
        if state_pos is not None:
            self.state_pos = state_pos
        if state_aber is not None:
            self.state_aber = state_aber

    def update(self):
        #self.allPatternsPaths
        #self.maskDouble = self.__masks[0].concat(self.__masks[1])
        #self.maskCombined = self.maskDouble 
        #self.sigMCTMaskUpdated.emit(self.maskCombined)

        #returnmask = self.maskDouble 
        return None #returnmask.image()

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
