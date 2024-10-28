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


class DPCManager(SignalInterface):
    sigDPCMaskUpdated = Signal(object)  # (maskCombined)

    def __init__(self, dpcInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        if dpcInfo is None:
            return

        self.__dpcInfo = dpcInfo
        self.rotations = self.__dpcInfo.rotations
        self.wavelength = self.__dpcInfo.wavelength
        self.pixelsize = self.__dpcInfo.pixelsize
        self.NA = self.__dpcInfo.NA
        self.NAi = self.__dpcInfo.NAi
        self.n = self.__dpcInfo.n # refr


    def update(self):
        return None 

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
