from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
from imswitch.imcontrol.model.interfaces.pipython.pidevice import GCSDevice
from imswitch.imcontrol.model.interfaces.pipython.pidevice.gcs2 import gcs2pitools
from serial.serialutil import SerialException
from qtpy.QtCore import QTimer
from imswitch.imcommon.framework import Signal, SignalInterface

class PIStageManager(PositionerManager, SignalInterface):
    """ PositionerManager for control of a PI c-663 XY-stage through USB
    communication.

    One manager controls the two X and Y axes
    """
    sigJoystickStatusChanged = Signal(bool)

    def __init__(self, positionerInfo, name, *args, **lowLevelManagers):

        self.__logger = initLogger(self, instanceName=name)

        if (len(positionerInfo.axes) != 2
                or 'X' not in positionerInfo.axes or 'Y' not in positionerInfo.axes):
            raise RuntimeError(f'{self.__class__.__name__} requires two axes named X and Y'
                               f' respectively, {positionerInfo.axes} provided.')

        PositionerManager.__init__(self, positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes})
        SignalInterface.__init__(self)

        manager_properties = positionerInfo.managerProperties or {}
        self.device = manager_properties.get('device')
        if not self.device:
            raise ValueError(
                "PIStageManager requires 'device' in managerProperties (for example 'C-663.11')."
            )
        self.usb_description = self._resolve_usb_description(manager_properties)

        self.X = GCSDevice(self.device)
        self.Y = GCSDevice(self.device)
        self.rangeMin = 0
        self.rangeMax = 25 #in mm
        self.joystickStatus = False

        # Joystick pushbuttons toggles (fast/slow and enable/disable)
        # NOTE: configured for joystick Analog C-819.20 so that:
        #   - Fast/slow toggled by Y axis buttons
        #   - Able/Disable toggled by X axis button
        self.fastSpeed = 1.0
        self.slowSpeed = 0.2
        self.buttonPollIntervalMs = 200
        self.speedButtonPressed = None  # last known state
        self.speedButtonController = 'Y'
        self.enableButtonController = 'X'
        self.enableButtonPressed = False 
        self.buttonTimer = QTimer()
        self.buttonTimer.timeout.connect(self._pollButtons)

        try:
            self.connect()
            self.getJoystickEnabledStatus()
        except:
            self.__logger.debug('Could not initialize PI motorized stage.')
            self.device = None

    def _resolve_usb_description(self, manager_properties):
        configured_usb_description = manager_properties.get('usb_description')

        if configured_usb_description:
            self.__logger.debug(
                f'Using PI USB description from setup config: {configured_usb_description}'
            )
            return configured_usb_description

        finder = GCSDevice(self.device)
        try:
            usb_devices = finder.EnumerateUSB()
        except Exception as exc:
            raise RuntimeError(
                f'Failed to enumerate PI USB devices for {self.device!r}: {exc}'
            )
        finally:
            try:
                finder.CloseConnection()
            except Exception:
                pass
            try:
                finder.CloseDaisyChain()
            except Exception:
                pass

        if not usb_devices:
            raise RuntimeError(
                f'No PI USB devices found while searching for {self.device!r}.'
            )

        device_candidates = [self.device]
        if '.' in self.device:
            device_candidates.append(self.device.split('.', 1)[0])

        selected_device = next(
            (
                dev for dev in usb_devices
                if any(candidate in dev for candidate in device_candidates)
            ),
            None
        )
        if selected_device is None:
            raise RuntimeError(
                f'No enumerated PI USB device matched {self.device!r} '
                f'(candidates: {device_candidates}). '
                f'Found: {usb_devices}'
            )
        self.__logger.debug(f'Auto-selected PI USB device: {selected_device}')
        return selected_device

    def finalize(self) -> None:
        """ Close/cleanup positioner. """
        if self.device is not None:
            self.buttonTimer.stop()
            self.X.VEL(1, self.fastSpeed)
            self.Y.VEL(1, self.fastSpeed)
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
        
        try:
            self.X.VEL(1, self.slowSpeed)
            self.Y.VEL(1, self.slowSpeed)
            self.buttonTimer.start(self.buttonPollIntervalMs)
            self._pollButtons()
        except Exception as e:
            self.__logger.warning(f"Failed to initialize Joystick button allowing variable speed")

    def move(self, value, axis):
        # value from widget is in um, and we store values in self._position in um
        # We send values in mm to stage, so distance to move = (position + value) / 1000
        dist = self._position[axis] / 1000 + value / 1000
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

    def updatePosition(self):
        # qPOS gives value in mm but we store in um (widget convention)
        self._position["X"] = self.X.qPOS(1)[1] * 1000
        self._position["Y"] = self.Y.qPOS(1)[1] * 1000

    def setJoystickEnabled(self, enabled: bool):
        if enabled:
            self.activate_joystick()
        else:
            self.deactivate_joystick()

    def activate_joystick(self):
        if not self.joystickStatus:
            self.X.JON(1, True)
            self.Y.JON(1, True)
            self.joystickStatus = True
            self.sigJoystickStatusChanged.emit(True)
            self.__logger.debug('Joystick activated')

    def deactivate_joystick(self):
        if self.joystickStatus:
            self.X.JON(1, False)
            self.Y.JON(1, False)
            self.joystickStatus = False
            self.sigJoystickStatusChanged.emit(False)
            self.__logger.debug('Joystick deactivated')

    def getJoystickEnabledStatus(self):
        """
        Status of X axis joystick, assuming status is same for Y axis
        """
        self.joystickStatus = self.X.qJON()[1]


    def _getJoystickButtonState(self, which='X'):
        controller = self.X if which == 'X' else self.Y
        result = controller.qJBS(1, 1)

        try:
            return bool(result[1][1])
        except Exception:
            self.__logger.debug(f'Unexpected qJBS return format: {result}')
            return False

    def _setJoystickSpeed(self, speed):
        self.X.VEL(1, speed)
        self.Y.VEL(1, speed)

    def _pollButtons(self):
        if self.device is None:
            return

        try:
            # Button 1: fast/slow
            speed_pressed = self._getJoystickButtonState(self.speedButtonController)

            if speed_pressed != self.speedButtonPressed:
                if speed_pressed:
                    self._setJoystickSpeed(self.fastSpeed)
                    self.__logger.debug('Joystick speed set to FAST')
                else:
                    self._setJoystickSpeed(self.slowSpeed)
                    self.__logger.debug('Joystick speed set to SLOW')

                self.speedButtonPressed = speed_pressed

            # Button 2: toggle joystick on/off
            enable_pressed = self._getJoystickButtonState(self.enableButtonController)

            # Rising edge only: toggle once when button is pressed
            if enable_pressed and not self.enableButtonPressed:
                self.setJoystickEnabled(not self.joystickStatus)

            self.enableButtonPressed = enable_pressed

        except Exception as e:
            self.__logger.debug(f'Error while polling joystick buttons: {e}')

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
