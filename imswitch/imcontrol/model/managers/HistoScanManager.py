import enum
import glob
import cv2
import os

import numpy as np
from PIL import Image
from scipy import signal as sg
import os 
from imswitch.imcommon.model import dirtools

import json

from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger


class HistoScanManager(SignalInterface):

    def __init__(self, HistoScanInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        self.histoConfigFilename = "config.json"

        # get default configs
        self.defaultConfigPath = os.path.join(dirtools.UserFileDirs.Root, "histoController")
        if not os.path.exists(self.defaultConfigPath):
            os.makedirs(self.defaultConfigPath)

        try:
            with open(os.path.join(self.defaultConfigPath, self.histoConfigFilename)) as jf:
                self.defaultConfig = json.load(jf)
                self.offsetX = self.defaultConfig["offsetX"]
                self.offsetY = self.defaultConfig["offsetY"]
        except Exception as e:
            self.__logger.debug(f"Could not load default config from {self.defaultConfigPath}: {e}")
            self.__logger.debug("Setting default values to 0, need to save them later, once they are set and experiment is saved")
            self.offsetX = 0
            self.offsetY = 0

        
    def writeConfig(self, data):
        with open(os.path.join(self.defaultConfigPath, self.histoConfigFilename), "w") as outfile:
            json.dump(data, outfile, indent=4)

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
