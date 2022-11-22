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
        
        self._esp32 = self._rs232manager._esp32
        self._laser = self._rs232manager._esp32.laser
        self._motor = self._rs232manager._esp32.motor
        self._led = self._rs232manager._esp32.led
        
        self.power = 0
        self.channel_index = laserInfo.managerProperties['channel_index']
        
        # do we have a setup with a filter wheel?
        try:
            self.filter_change = laserInfo.managerProperties['filter_change']
            self.filter_position = laserInfo.managerProperties['filter_position']
            self.filter_axis = laserInfo.managerProperties['filter_axis']
            self.laser_position_init =  laserInfo.managerProperties['filter_position_init']
            self.__logger.debug("Filter change enabled")
        except:
            self.filter_change = False
            self.filter_position = 0
            self.filter_axis = -1
            self.laser_position_init =  None
            self.__logger.debug("Filter change disabled")

        # do we want to vary the laser intensity to despeckle the image?
        try:
            self.laser_despeckle_amplitude = laserInfo.managerProperties['laser_despeckle_amplitude']
            self.laser_despeckle_period = laserInfo.managerProperties['laser_despeckle_period']
            self.__logger.debug("Laser despeckle enabled")
        except:
            self.laser_despeckle_amplitude = 0. # %
            self.laser_despeckle_period = 10 # ms
            self.__logger.debug("Laser despeckle disabled")

        # 
        if self.filter_change:
           self.initFilter(nSteps=self.laser_position_init)

        # set the laser to 0
        self.enabled = False
        self.setEnabled(self.enabled)
        
    def initFilter(self, nSteps=None, speed=None):
        '''
        if self.filter_change:
            if nSteps is None:
                if self.laser_position_init is None:
                    nSteps = self._motor.filter_pos_init
                else:
                    nSteps = self._motor.laser_position_init
            if speed is None:
                speed = self._motor.filter_speed
            self._motor.init_filter(nSteps = nSteps, speed = speed, filter_axis = self.filter_axis)
        '''
        self.__logger.debug("Filter initialization not implemented yet")
        
    def setEnabled(self, enabled):
        """Turn on (N) or off (F) laser emission"""
        self.enabled = enabled
        if self.channel_index == "LED":
            if self.filter_change and (self.power*self.enabled)>0:
                self._motor.switch_filter(filter_pos=self.filter_position, filter_axis=self.filter_axis, is_blocking=True)
            self._led.setAll((self.power*self.enabled,self.power*self.enabled,self.power*self.enabled))
        else:
            self._laser.set_laser(self.channel_index, 
                                                int(self.power*self.enabled), self.filter_change, 
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
                self._led.setAll((int(self.power*self.enabled),self.power*self.enabled,self.power*self.enabled))
            else:
                self._laser.set_laser(self.channel_index, 
                                    int(self.power), 0*self.filter_change, 
                                    despeckleAmplitude = self.laser_despeckle_amplitude,
                                    despecklePeriod = self.laser_despeckle_period, 
                                    filter_axis = self.filter_axis, 
                                    filter_position = self.filter_position, 
                                    is_blocking=True)

    def sendTrigger(self, triggerId):
        self._esp32.digital.sendTrigger(triggerId)
    
    '''
    def sendScanner(self, scannernFrames=100, scannerXFrameMin=0, scannerXFrameMax=255,
        scannerYFrameMin=0, scannerYFrameMax=255, scannerEnable=0, scannerxMin=1, 
        scannerxMax=5, scanneryMin=1, scanneryMax=5, scannerXStep=25,
        scannerYStep=25, scannerLaserVal=32000, scannerExposure=500, scannerDelay=500):
        
        self._rs232manager._esp32.set_scanner_classic(scannernFrames, 
            scannerXFrameMin, scannerXFrameMax, scannerYFrameMin, scannerYFrameMax, 
            scannerEnable, scannerxMin, scannerxMax, scanneryMin, 
            scanneryMax, scannerXStep, scannerYStep, scannerLaserVal, 
            scannerExposure, scannerDelay)

    def sendScannerPattern(self, ismPatternIndex, scannernFrames=1,
            scannerLaserVal=32000, scannerExposure=500, scannerDelay=500, isBlocking=False):

        self._rs232manager._esp32.set_scanner_pattern(ismPatternIndex, scannernFrames,
            scannerLaserVal, scannerExposure, scannerDelay, isBlocking)
    '''



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
