import json
import os
import threading
from imswitch import IS_HEADLESS
import numpy as np
from imswitch.imcommon.model import APIExport, initLogger
from ..basecontrollers import ImConWidgetController


class UC2ConfigController(ImConWidgetController):
    """Linked to UC2ConfigWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)


            self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]
        except Exception as e:
            self.__logger.error("No Stages found in the config file? " +e )
            self.stages = None
        # update the gui elements
        self._commChannel.sigUpdateMotorPosition.emit()

        '''
        # force updating the position
        # move motors by 1 step to get the current position #FIXME: This is a bug!
        if "X" in self.stages.speed.keys():
            self.stages.move(1, "X", is_absolute=False, is_blocking=True)
            self.stages.move(-1, "X", is_absolute=False, is_blocking=True)
        if "Y" in self.stages.speed.keys():
            self.stages.move(1, "Y", is_absolute=False, is_blocking=True)
            self.stages.move(-1, "Y", is_absolute=False, is_blocking=True)
        if "Z" in self.stages.speed.keys():
            self.stages.move(1, "Z", is_absolute=False, is_blocking=True)
            self.stages.move(-1, "Z", is_absolute=False, is_blocking=True)
        if "A" in self.stages.speed.keys():
            self.stages.move(1, "A", is_absolute=False, is_blocking=True)
            self.stages.move(-1, "A", is_absolute=False, is_blocking=True)
        '''
        self._commChannel.sigUpdateMotorPosition.emit()


        # register the callback to take a snapshot triggered by the ESP32
        self.registerCaptureCallback()

        # Connect buttons to the logic handlers
        if IS_HEADLESS:
            return
        # Connect buttons to the logic handlers
        self._widget.setPositionXBtn.clicked.connect(self.set_positionX)
        self._widget.setPositionYBtn.clicked.connect(self.set_positionY)
        self._widget.setPositionZBtn.clicked.connect(self.set_positionZ)
        self._widget.setPositionABtn.clicked.connect(self.set_positionA)

        self._widget.autoEnableBtn.clicked.connect(self.set_auto_enable)
        self._widget.unsetAutoEnableBtn.clicked.connect(self.unset_auto_enable)
        self._widget.reconnectButton.clicked.connect(self.reconnect)
        self._widget.closeConnectionButton.clicked.connect(self.closeConnection)
        self._widget.btpairingButton.clicked.connect(self.btpairing)
        self._widget.stopCommunicationButton.clicked.connect(self.interruptSerialCommunication)

        try:

    def registerCaptureCallback(self):
        # This will capture an image based on a signal coming from the ESP32
        def snapImage(value):
            self.detector_names = self._master.detectorsManager.getAllDeviceNames()
            self.detector = self._master.detectorsManager[self.detector_names[0]]
            mImage = self.detector.getLatestFrame()
            # save image
            #tif.imsave()

            # (detectorName, image, init, scale, isCurrentDetector)
            self._commChannel.sigUpdateImage.emit('Image', mImage, True, 1, False)

        def printCallback(value):
            self.__logger.debug(f"Callback called with value: {value}")
        try:
            self.__logger.debug("Registering callback for snapshot")
            # register default callback
            self._master.UC2ConfigManager.ESP32.message.register_callback(0, snapImage) # FIXME: Too hacky?
            for i in range(1, self._master.UC2ConfigManager.ESP32.message.nCallbacks):
                self._master.UC2ConfigManager.ESP32.message.register_callback(i, printCallback)

        except Exception as e:
            self.__logger.error(f"Could not register callback: {e}")

    def set_motor_positions(self, a, x, y, z):
        # Add your logic to set motor positions here.
        self.__logger.debug(f"Setting motor positions: A={a}, X={x}, Y={y}, Z={z}")
        # push the positions to the motor controller
        if a is not None: self.stages.setPositionOnDevice(value=float(a), axis="A")
        if x is not None:  self.stages.setPositionOnDevice(value=float(x), axis="X")
        if y is not None: self.stages.setPositionOnDevice(value=float(y), axis="Y")
        if z is not None: self.stages.setPositionOnDevice(value=float(z), axis="Z")

        # retrieve the positions from the motor controller
        positions = self.stages.getPosition()
        if not IS_HEADLESS: self._widget.reconnectDeviceLabel.setText("Motor positions: A="+str(positions["A"])+", X="+str(positions["X"])+", \n Y="+str(positions["Y"])+", Z="+str(positions["Z"]))
        # update the GUI
        self._commChannel.sigUpdateMotorPosition.emit()

    def interruptSerialCommunication(self):
        self._master.UC2ConfigManager.interruptSerialCommunication()
        if not IS_HEADLESS: self._widget.reconnectDeviceLabel.setText("We are intrrupting the last command")

    def set_auto_enable(self):
        # Add your logic to auto-enable the motors here.
        # get motor controller
        self.stages.enalbeMotors(enableauto=True)

    def unset_auto_enable(self):
        # Add your logic to unset auto-enable for the motors here.
        self.stages.enalbeMotors(enable=True, enableauto=False)

    def set_positionX(self):
        if not IS_HEADLESS: x = self._widget.motorXEdit.text() # TODO: Should be a signal for all motors
        self.set_motor_positions(None, x, None, None)

    def set_positionY(self):
        if not IS_HEADLESS: y = self._widget.motorYEdit.text()
        self.set_motor_positions(None, None, y, None)

    def set_positionZ(self):
        if not IS_HEADLESS: z = self._widget.motorZEdit.text()
        self.set_motor_positions(None, None, None, z)

    def set_positionA(self):
        if not IS_HEADLESS: a = self._widget.motorAEdit.text()
        self.set_motor_positions(a, None, None, None)

    def reconnectThread(self, baudrate=None):
        self._master.UC2ConfigManager.initSerial(baudrate=baudrate)
        self._widget.reconnectDeviceLabel.setText("We are connected: "+str(self._master.UC2ConfigManager.isConnected()))

    def closeConnection(self):
        self._master.UC2ConfigManager.closeSerial()
        self._widget.reconnectDeviceLabel.setText("Connection to ESP32 closed.")

    @APIExport(runOnUIThread=True)
    def reconnect(self):
        self._logger.debug('Reconnecting to ESP32 device.')
        if not IS_HEADLESS: self._widget.reconnectDeviceLabel.setText("Reconnecting to ESP32 device.")
        baudrate = self._widget.getBaudRateGui()
        if baudrate not in (115200, 500000):
            baudrate = None
        mThread = threading.Thread(target=self.reconnectThread, args=(baudrate,))
        mThread.start()

    @APIExport(runOnUIThread=True)
    def is_connected(self):
        return self._master.UC2ConfigManager.isConnected()

    @APIExport(runOnUIThread=True)
    def btpairing(self):
        self._logger.debug('Pairing BT device.')
        mThread = threading.Thread(target=self._master.UC2ConfigManager.pairBT)
        mThread.start()
        mThread.join()
        if not IS_HEADLESS: self._widget.reconnectDeviceLabel.setText("Bring the PS controller into pairing mode")


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
