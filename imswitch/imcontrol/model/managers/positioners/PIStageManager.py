from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
from pipython import GCSDevice, pitools
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
            axis: 12.5 for axis in positionerInfo.axes})

        #TO DO: device name and usb description not as hard value but either picked up from the config file or
        # automatically found with the GSCdevice.enumarateUSB() command
        self.device = 'C-663.11'
        self.usb_description = '0205500074'

        self.X = GCSDevice(self.device)
        self.Y = GCSDevice(self.device)
        self.joystick_status = 'enabled'
        self.rangeMin = 0
        self.rangeMax = 25

        try:
            self.connect()
        except SerialException:
            self.__logger.debug('Could not initialize PI Stage motorized stage, might not be switched on.')
            self.dev = None

    def connect(self):
        self.__logger.debug('Connecting PI stage...')
        self.X.OpenUSBDaisyChain(description=self.usb_description)
        daisychainid = self.X.dcid
        self.X.ConnectDaisyChainDevice(1, daisychainid)
        self.Y.ConnectDaisyChainDevice(2, daisychainid)
        pitools.startup(self.X)
        pitools.startup(self.Y)
        self.rangeMin = self.X.qTMN()['1']
        self.rangeMax = self.X.qTMX()['1']
        self.PosX = self.X.qPOS(1)[1]
        self.PosY = self.Y.qPOS(1)[1]

        self.__logger.debug('PI stage connected')
        self.__logger.debug('\n{}:\n{}'.format(self.X.GetInterfaceDescription(), self.X.qIDN()))
        self.__logger.debug('\n{}:\n{}'.format(self.Y.GetInterfaceDescription(), self.Y.qIDN()))


    def move(self, value, axis):


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
