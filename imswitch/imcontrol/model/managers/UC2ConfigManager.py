import enum
import glob
import math
import os

import numpy as np
from PIL import Image
from scipy import signal as sg

from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger


class UC2ConfigManager(SignalInterface):
    sigUC2ConfigMaskUpdated = Signal(object)  # (maskCombined)

    def __init__(self, UC2ConfigInfo, lowLevelManagers, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        if UC2ConfigInfo is None:
            return

        #TODO: HARDCODED!!
        self.ESP32 = lowLevelManagers["rs232sManager"]["ESP32"]._esp32

        #self.update(maskChange=True, tiltChange=True, aberChange=True)

    def saveState(self, state_general=None, state_pos=None, state_aber=None):
        if state_general is not None:
            self.state_general = state_general
        if state_pos is not None:
            self.state_pos = state_pos
        if state_aber is not None:
            self.state_aber = state_aber

    def setGeneral(self, general_info):
        pass
    
    def setpinDef(self, pinDef_info):
        self.ESP32.config.setpinDef(pinDef_info)
        pass
        
    def update(self, maskChange=False, tiltChange=False, aberChange=False):
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
