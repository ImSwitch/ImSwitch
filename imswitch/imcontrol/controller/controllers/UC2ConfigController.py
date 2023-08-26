import json
import os
import threading

import numpy as np

from imswitch.imcommon.model import dirtools, initLogger
from ..basecontrollers import ImConWidgetController


class UC2ConfigController(ImConWidgetController):
    """Linked to UC2ConfigWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        # Connect buttons to the logic handlers
        self._widget.setPositionsBtn.clicked.connect(self.set_positions)
        self._widget.autoEnableBtn.clicked.connect(self.set_auto_enable)
        self._widget.unsetAutoEnableBtn.clicked.connect(self.unset_auto_enable)
        self._widget.reconnectButton.clicked.connect(self.reconnect)
        self._widget.btpairingButton.clicked.connect(self.btpairing)
        
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]

    def set_motor_positions(self, a, x, y, z):
        # Add your logic to set motor positions here.
        print(f"Setting motor positions: A={a}, X={x}, Y={y}, Z={z}")
        # push the positions to the motor controller
        self.stages.setPositionOnDevice(value=float(a), axis="A")
        self.stages.setPositionOnDevice(value=float(x), axis="X")
        self.stages.setPositionOnDevice(value=float(y), axis="Y")
        self.stages.setPositionOnDevice(value=float(z), axis="Z")
        
        # retrieve the positions from the motor controller
        positions = self.stages.getPosition()
        self._widget.reconnectDeviceLabel.setText("Motor positions: A="+str(positions["A"])+", X="+str(positions["X"])+", \n Y="+str(positions["Y"])+", Z="+str(positions["Z"]))
        # update the GUI
        self._commChannel.sigUpdateMotorPosition.emit()

    def set_auto_enable(self):
        # Add your logic to auto-enable the motors here.
        # get motor controller
        self.stages.enalbeMotors(enableauto=True)

    def unset_auto_enable(self):
        # Add your logic to unset auto-enable for the motors here.
        self.stages.enalbeMotors(enableauto=False)

    def set_positions(self):
        a = self._widget.motorAEdit.text()
        x = self._widget.motorXEdit.text()
        y = self._widget.motorYEdit.text()
        z = self._widget.motorZEdit.text()
        self.set_motor_positions(a, x, y, z)

    def reconnectThread(self):
        self._master.UC2ConfigManager.initSerial()
        self._widget.reconnectDeviceLabel.setText("We are connected: "+str(self._master.UC2ConfigManager.isConnected()))
        
    def reconnect(self):
        self._logger.debug('Reconnecting to ESP32 device.')
        self._widget.reconnectDeviceLabel.setText("Reconnecting to ESP32 device.")
        mThread = threading.Thread(target=self.reconnectThread)
        mThread.start()

    def btpairing(self):
        self._logger.debug('Pairing BT device.')
        mThread = threading.Thread(target=self._master.UC2ConfigManager.pairBT)
        mThread.start()
        mThread.join()
        self._widget.reconnectDeviceLabel.updateFirmwareDeviceLabel.setText("Bring the PS controller into pairing mode")


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
