from imswitch.imcommon.model import initLogger
from .LEDMatrixManager import LEDMatrixManager
from imswitch.imcontrol.model.interfaces.ESP32Client import ESP32Client
import numpy as np

class ESP32LEDMatrixManager(LEDMatrixManager):
    """ LEDMatrixManager for controlling LEDs and LEDMatrixs connected to an 
    ESP32 exposing a REST API
    Each LEDMatrixManager instance controls one LED.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place
    - ``channel_index`` -- LEDMatrix channel (A to H)
    """

    def __init__(self, LEDMatrixInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self.power = 0
        self.I_max = 255
        self.N_leds = 4
        self.setEnabled = False
        self.intesnsity=0

        self.pattern = np.array((np.reshape(np.random.randint(0,self.I_max ,self.N_leds**2),(self.N_leds,self.N_leds)),
                       np.reshape(np.random.randint(0,self.I_max ,self.N_leds**2),(self.N_leds,self.N_leds)),
                       np.reshape(np.random.randint(0,self.I_max ,self.N_leds**2),(self.N_leds,self.N_leds))))
        

        self._rs232manager = lowLevelManagers['rs232sManager'][
            LEDMatrixInfo.managerProperties['rs232device']
        ]
            
        self.esp32 = self._rs232manager._esp32
        super().__init__(LEDMatrixInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)

    def setAll(self, intensity=0):
        self.intesnsity=intensity
        #self.esp32.setLEDMatrixAll(intensity=intensity)
        pass
    
    def setPattern(self, pattern):
        self.pattern=pattern
        #self.esp32.setLEDMatrixPattern(self.pattern)
        pass
        
    def setEnabled(self, enabled):
        """Turn on (N) or off (F) LEDMatrix emission"""
        self.setEnabled = enabled
        #self.esp32.setLEDMatrixPattern(self.pattern*self.setEnabled)

    def setLEDSingle(self, indexled=0, intensity=(255,255,255)):
        """Handles output power.
        Sends a RS232 command to the LEDMatrix specifying the new intensity.
        """
        self.esp32.send_LEDMatrix_single(indexled, intensity, timeout=1)
        

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
