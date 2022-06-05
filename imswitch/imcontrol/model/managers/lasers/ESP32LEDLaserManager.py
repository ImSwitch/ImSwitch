from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager

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
        self.power = 0
        self.channel_index = laserInfo.managerProperties['channel_index']
        
        try:
            self.filter_change = laserInfo.managerProperties['filter_change']
            self.filter_position = laserInfo.managerProperties['filter_position']
        except:
            self.filter_change = False
            self.filter_position = 0

        try:
            self.filter_axis = laserInfo.managerProperties['filter_axis']
        except:
            self.filter_axis = -1

        try:
            self.laser_despeckle_amplitude = laserInfo.managerProperties['laser_despeckle_amplitude']
        except:
            self.laser_despeckle_amplitude = 0. # %
            
        try:
            self.laser_despeckle_period = laserInfo.managerProperties['laser_despeckle_period']
        except:
            self.laser_despeckle_period = 10 # ms

        try:
            self.laser_position_init =  laserInfo.managerProperties['filter_position_init']
        except:
            self.laser_position_init =  None

        if self.filter_change:
           self.initFilter(nSteps=self.laser_position_init)

        self.enabled = False
        
    def initFilter(self, nSteps=None, speed=None):
        if self.filter_change:
            if nSteps is None:
                if self.laser_position_init is None:
                    nSteps = self._rs232manager._esp32.filter_pos_init
                else:
                    nSteps = self.laser_position_init
            if speed is None:
                speed = self._rs232manager._esp32.filter_speed
            self._rs232manager._esp32.init_filter(nSteps = nSteps, speed = speed, filter_axis = self.filter_axis)

    def setEnabled(self, enabled):
        """Turn on (N) or off (F) laser emission"""
        self.enabled = enabled
        if self.channel_index == "LED":
            if self.filter_change and (self.power*self.enabled)>0:
                self._rs232manager._esp32.switch_filter(filter_pos=self.filter_position, filter_axis=self.filter_axis, is_blocking=True)
            self._rs232manager._esp32.send_LEDMatrix_full((self.power*self.enabled,self.power*self.enabled,self.power*self.enabled))
        else:
            self._rs232manager._esp32.set_laser(self.channel_index, 
                                                self.power*self.enabled, self.filter_change, 
                                                despeckleAmplitude = self.laser_despeckle_amplitude,
                                                despecklePeriod = self.laser_despeckle_period, 
                                                filter_axis = self.filter_axis, 
                                                filter_position = self.filter_position, 
                                                is_blocking=True)

    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        self.power = power
        if self.enabled:
            if self.channel_index == "LED":
                if self.filter_change:
                    self._rs232manager._esp32.switch_filter(laserid=self.channel_index,  filter_axis=self.filter_axis)

                self._rs232manager._esp32.send_LEDMatrix_full((self.power,self.power,self.power))
            else:
                self._rs232manager._esp32.set_laser(self.channel_index, 
                                    self.power, self.filter_change, 
                                    despeckleAmplitude = self.laser_despeckle_amplitude,
                                    despecklePeriod = self.laser_despeckle_period, 
                                    filter_axis = self.filter_axis, 
                                    filter_position = self.filter_position, 
                                    is_blocking=True)

    def sendTrigger(self, triggerId):
        self._rs232manager._esp32.sendTrigger(triggerId)



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
