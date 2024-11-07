import enum
import glob
import math
import os
import threading

import numpy as np
from PIL import Image
from scipy import signal as sg
import uc2rest as uc2
import json

from imswitch.imcommon.model import dirtools
from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger


class UC2ConfigManager(SignalInterface):

    def __init__(self, Info, lowLevelManagers, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        # TODO: HARDCODED!!
        try:
            self.ESP32 = lowLevelManagers["rs232sManager"]["ESP32"]._esp32
        except:
            return

    def saveState(self, state_general=None, state_pos=None, state_aber=None):
        if state_general is not None:
            self.state_general = state_general
        if state_pos is not None:
            self.state_pos = state_pos
        if state_aber is not None:
            self.state_aber = state_aber

    def setGeneral(self, general_info):
        pass

    def loadPinDefDevice(self):
        return self.ESP32.config.loadConfigDevice()

    def loadDefaultConfig(self):
        return self.ESP32.config.loadDefaultConfig()

    def setpinDef(self, pinDef_info):
        self.ESP32.config.setConfigDevice(pinDef_info)
        # check if setting pins was successfull
        pinDef_infoDevice = self.loadPinDefDevice()
        shared_items = {k: pinDef_info[k] for k in pinDef_info if
                        k in pinDef_infoDevice and pinDef_info[k] == pinDef_infoDevice[k]}
        return shared_items

    def update(self, maskChange=False, tiltChange=False, aberChange=False):
        pass

    def closeSerial(self):
        return self.ESP32.closeSerial()

    def isConnected(self):
        return self.ESP32.serial.is_connected

    def interruptSerialCommunication(self):
        self.ESP32.serial.interruptCurrentSerialCommunication()
        
    def initSerial(self, baudrate=None):
        try:
            self.ESP32.serial.reconnect(baudrate=baudrate)
        except:
            self.ESP32.serial.reconnect() # fall back to old version of UC2-REST
            
    def pairBT(self):
        self.ESP32.state.pairBT()

    def setDebug(self, debug):
        self.ESP32.serial.DEBUG = debug

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
