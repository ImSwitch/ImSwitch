import enum
import glob
import cv2
import os
import re
import numpy as np
from PIL import Image
from scipy import signal as sg

from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger


class SIMManager(SignalInterface):
    sigSIMMaskUpdated = Signal(object)  # (maskCombined)

    def __init__(self, simInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        if simInfo is None:
            return

        self.__simInfo = simInfo
        self.__wavelength = self.__simInfo.wavelength
        self.__pixelsize = self.__simInfo.pixelSize
        self.__angleMount = self.__simInfo.angleMount
        self.__simSize = (self.__simInfo.width, self.__simInfo.height)
        self.__patternsDir = self.__simInfo.patternsDir
        self.isSimulation = self.__simInfo.isSimulation
        self.nRotations = self.__simInfo.nRotations
        self.nPhases = self.__simInfo.nPhases
        self.simMagnefication = self.__simInfo.nPhases
        self.isFastAPISIM = self.__simInfo.isFastAPISIM
        self.simPixelsize = self.__simInfo.simPixelsize
        self.simNA = self.__simInfo.simNA
        self.simN = self.__simInfo.simN # refr
        self.simETA = self.__simInfo.simETA

        
        
        self.isHamamatsuSLM = self.__simInfo.isHamamatsuSLM

        # Load all patterns
        if type(self.__patternsDir) is not list:
            self.__patternsDir = [self.__patternsDir]
        self.allPatterns = self.loadPatterns(self.__patternsDir)

        # define paramerters for fastAPI (optional)
        fastAPISIM_host = self.__simInfo.fastAPISIM_host
        fastAPISIM_port = self.__simInfo.fastAPISIM_port
        fastAPISIM_tWaitSequence = self.__simInfo.tWaitSequence 
        self.fastAPISIMParams = {"host":fastAPISIM_host, 
                                 "port":fastAPISIM_port,
                                 "tWaitSquence":fastAPISIM_tWaitSequence}
        
        self.isFastAPISIM = self.__simInfo.isFastAPISIM

    def loadPatterns(self, patternsDir, filetype="bmp"):
        # sort filenames numerically
        allPatterns = []
        allPatternsPerWavelength = []
        
        for iPatternDir in patternsDir:
            allPatternPaths = sorted(glob.glob(os.path.join(iPatternDir, "*."+filetype)))
            for iPatternPath in allPatternPaths:
                mImage = cv2.imread(iPatternPath)
                mImage = cv2.cvtColor(mImage, cv2.COLOR_BGR2GRAY)

                allPatternsPerWavelength.append(mImage)
            allPatterns.append(allPatternsPerWavelength)
            allPatternsPerWavelength = []
                
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
        #self.sigSIMMaskUpdated.emit(self.maskCombined)

        #returnmask = self.maskDouble 
        return None #returnmask.image()

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
