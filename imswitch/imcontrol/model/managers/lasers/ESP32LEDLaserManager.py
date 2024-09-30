from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager
import numpy as np

class ESP32LEDLaserManager(LaserManager):
    """ LaserManager for controlling LEDs and LAsers connected to an
    ESP32 exposing a REST API
    Each LaserManager instance controls one LED.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place

    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)
        self._rs232manager = lowLevelManagers['rs232sManager'][
            laserInfo.managerProperties['rs232device']
        ]
        self.__logger = initLogger(self, instanceName=name)

        self._esp32 = self._rs232manager._esp32
        self._laser = self._rs232manager._esp32.laser
        self._motor = self._rs232manager._esp32.motor
        self._led = self._rs232manager._esp32.led

        # preset the pattern
        self._led.ledpattern = np.ones(self._led.ledpattern.shape)
        self.ledIntesity = 0
        self._led.Intensity = self.ledIntesity

        self.power = 0
        self.channel_index = laserInfo.managerProperties['channel_index']

        # do we want to vary the laser intensity to despeckle the image?
        try:
            self.laser_despeckle_amplitude = laserInfo.managerProperties['laser_despeckle_amplitude']
            self.laser_despeckle_period = laserInfo.managerProperties['laser_despeckle_period']
            self.__logger.debug("Laser despeckle enabled")
        except:
            self.laser_despeckle_amplitude = 0. # %
            self.laser_despeckle_period = 10 # ms
            self.__logger.debug("Laser despeckle disabled")

        # set the laser to 0
        self.enabled = False
        self.setEnabled(self.enabled)

    def setEnabled(self, enabled,  getReturn=False):
        """Turn on (N) or off (F) laser emission"""
        self.enabled = enabled
        if self.channel_index == "LED":
            #self._led.send_LEDMatrix_full(intensity = (self.power*self.enabled,self.power*self.enabled,self.power*self.enabled), getReturn=getReturn)
            #self._led.setIntensity(intensity=(self.power*self.enabled,self.power*self.enabled,self.power*self.enabled), getReturn=getReturn)
            self._led.setAll(state=self.enabled, intensity=(self.power, self.power, self.power), getReturn=getReturn)
        else:
            self._laser.set_laser(self.channel_index,
                                                int(self.power*self.enabled),
                                                despeckleAmplitude = self.laser_despeckle_amplitude,
                                                despecklePeriod = self.laser_despeckle_period,
                                                is_blocking=getReturn)

    def setValue(self, power, getReturn=False):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        self.power = power
        if self.enabled:
            
            if self.channel_index == "LED":
                # ensure that in case it's not initialized yet, we display an all-on pattern
                if self._led.ledpattern[0,0]==-1:
                    self._led.ledpattern[:]=1
                self._led.setAll(state=1, intensity=(self.power, self.power, self.power), getReturn=getReturn)
                #self._led.setAll(intensity=(self.power*self.enabled,self.power*self.enabled,self.power*self.enabled), getReturn=getReturn)
                self.ledIntesity=self.power
                #self._led.send_LEDMatrix_full(intensity = (self.power*self.enabled,self.power*self.enabled,self.power*self.enabled), getReturn=getReturn)
            else:
                self._laser.set_laser(self.channel_index,
                                    int(self.power),
                                    despeckleAmplitude = self.laser_despeckle_amplitude,
                                    despecklePeriod = self.laser_despeckle_period,
                                    is_blocking=getReturn)

    def sendTrigger(self, triggerId):
        self._esp32.digital.sendTrigger(triggerId)

    def setGalvo(self,channel=1, frequency=1, offset=0, amplitude=1, clk_div=0, phase=0, invert=1, timeout=1):
        self._rs232manager._esp32.galvo.set_dac(
            channel=channel, frequency=frequency, offset=offset, amplitude=amplitude, clk_div=clk_div, 
            phase=phase, invert=invert, timeout=timeout)

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
