from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
from imswitch.imcontrol.model.interfaces.pipython.pidevice import GCSDevice
from imswitch.imcontrol.model.interfaces.pipython.pidevice.gcs2 import gcs2pitools
from serial.serialutil import SerialException


class PIStageManager(PositionerManager):
    """ PositionerManager for control of a PI c-663 XY-stage through USB
    communication.

    One manager controls the two X and Y axes
    """

    def __init__(self, positionerInfo, name, *args, **lowLevelManagers):

        self.__logger = initLogger(self, instanceName=name)

        if (len(positionerInfo.axes) != 2
                or 'X' not in positionerInfo.axes or 'Y' not in positionerInfo.axes):
            raise RuntimeError(f'{self.__class__.__name__} requires two axes named X and Y'
                               f' respectively, {positionerInfo.axes} provided.')

        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes})

        # TODO: device name and usb description not as hard value but either picked up from the config file or automatically found with the GSCdevice.enumarateUSB() command
        self.device = 'C-663.11'
        self.usb_description = '0205500074'

        self.X = GCSDevice(self.device)
        self.Y = GCSDevice(self.device)
        self.rangeMin = 0
        self.rangeMax = 25 #in mm
        self.joystickStatus = False

        try:
            self.connect()
            self.getJoystickEnabledStatus()
        except:
            self.__logger.debug('Could not initialize PI motorized stage.')
            self.device = None

    def finalize(self) -> None:
        """ Close/cleanup positioner. """
        if self.device is not None:
            self.activate_joystick()
            self.X.CloseDaisyChain()
            self.__logger.debug('PIstage connection closed, joystick activated')

    def connect(self):
        self.__logger.debug('Connecting PI stage...')
        self.X.OpenUSBDaisyChain(description=self.usb_description)
        daisychainid = self.X.dcid
        self.X.ConnectDaisyChainDevice(1, daisychainid)
        self.Y.ConnectDaisyChainDevice(2, daisychainid)
        gcs2pitools.startup(self.X)
        gcs2pitools.startup(self.Y)
        self.rangeMin = self.X.qTMN()['1'] #in mm
        self.rangeMax = self.X.qTMX()['1'] #in mm
        self._position['X'] = self.X.qPOS(1)[1]*1000 #converted to um for display in GUI
        self._position['Y'] = self.Y.qPOS(1)[1]*1000 #converted to um for display in GUI

        self.__logger.debug('PI stage connected')
        self.__logger.debug('\n{}:\n{}'.format(self.X.GetInterfaceDescription(), self.X.qIDN()))
        self.__logger.debug('\n{}:\n{}'.format(self.Y.GetInterfaceDescription(), self.Y.qIDN()))

    def move(self, value, axis):
        # value extracted from widget is in um, must be converted to mm to be passed to PI stage controller
        # self.'axis'.qPOS gives value in mm
        # Therefore, distance to move = self.'axis'.qPOS + value/1000
        if axis == "X":
            dist = self.X.qPOS(1)[1] + value / 1000
            self.setPosition(dist, axis)
        elif axis == "Y":
            dist = self.Y.qPOS(1)[1] + value / 1000
            self.setPosition(dist, axis)

    def setPosition(self, position: float, axis: str):

        if self.rangeMax >= position >= self.rangeMin:
            self.deactivate_joystick()
            if axis == 'X':
                self.X.MOV(1, position)
            if axis == 'Y':
                self.Y.MOV(1, position)
            self._position[axis] = position * 1000
        else:
            self.__logger.debug('Out of the stage range')



    def activate_joystick(self):
        if not self.joystickStatus:
            self.X.JON(1, True)
            self.Y.JON(1, True)
            self.joystickStatus = True
            self.__logger.debug('Joystick activated')

    def deactivate_joystick(self):
        if self.joystickStatus:
            self.X.JON(1, False)
            self.Y.JON(1, False)
            self.joystickStatus = False
            self._position['X'] = self.X.qPOS(1)[1] * 1000
            self._position['Y'] = self.Y.qPOS(1)[1] * 1000
            self.__logger.debug('Joystick deactivated')

    def getJoystickEnabledStatus(self):
        """
        Status of X axis joystick, assuming status is same for Y axis
        """
        self.joystickStatus = self.X.qJON()[1]

    """
    
    def move_to(self, axis, coord):

        if self.rangeMax >= coord >= self.rangeMin:
            if axis == 'X':
                if self.joystick_status == 'enabled':
                    self.deactivate_joystick()
                    self.X.MOV(1, coord)
                    self.deactivate_joystick()
                else:
                    self.X.MOV(1, coord)
                # self.PosX = coord
            if axis == 'Y':
                if self.rangeMax >= coord >= self.rangeMin:
                    if self.joystick_status == 'enabled':
                        self.deactivate_joystick()
                        self.Y.MOV(1, coord)
                        self.deactivate_joystick()
                    else:
                        self.Y.MOV(1, coord)
                    # self.PosY = coord
        else:
            self.__logger.debug('Out of the stage range')

    def move_to_x(self, x_coord):
        if self.rangeMax >= x_coord >= self.rangeMin:
            if self.joystick_status == 'enabled':
                self.deactivate_joystick()
                self.X.MOV(1, x_coord)
                self.deactivate_joystick()
            else:
                self.X.MOV(1, x_coord)
            # self.PosX = x_coord
        else:
            self.__logger.debug('Out of the stage range')

    def move_to_y(self, y_coord):
        if self.rangeMax >= y_coord >= self.rangeMin:
            if self.joystick_status == 'enabled':
                self.deactivate_joystick()
                self.X.MOV(1, y_coord)
                self.deactivate_joystick()
            else:
                self.X.MOV(1, y_coord)
            # self.PosX = x_coord
        else:
            self.__logger.debug('Out of the stage range')

    """

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
