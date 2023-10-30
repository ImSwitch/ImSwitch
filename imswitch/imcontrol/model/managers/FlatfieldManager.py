import enum
import glob
import cv2
import os

import numpy as np
from PIL import Image
from scipy import signal as sg
import os 
from imswitch.imcommon.model import dirtools
import tifffile as tif

from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger


class FlatfieldManager(SignalInterface):
    sigFlatfieldMaskUpdated = Signal(object)  # (maskCombined)

    def __init__(self, FlatfieldInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        
        self.FlatfieldImage = None
        self.histoConfigFilename = "FlatfieldImage.tif"

        # get default configs
        self.defaultConfigPath = os.path.join(dirtools.UserFileDirs.Root, "flatfieldController")
        if not os.path.exists(self.defaultConfigPath):
            os.makedirs(self.defaultConfigPath)

        try:
            self.FlatfieldImage = cv2.imread(os.path.join(self.defaultConfigPath, self.histoConfigFilename))
        except Exception as e:
            self.__logger.error(f"Could not load default flatfield image from {self.defaultConfigPath}: {e}")

    def writeFlatfieldImage(self, data):
        tif.imsave(os.path.join(self.defaultConfigPath, self.histoConfigFilename), data)

    def update(self):
        return None #returnmask.image()
    
    def setFlatfieldImage(self, flatfieldImage):
        self.FlatfieldImage = flatfieldImage
        self.writeFlatfieldImage(self.FlatfieldImage)
        
    def getFlatfieldImage(self):
        return self.FlatfieldImage
    

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
