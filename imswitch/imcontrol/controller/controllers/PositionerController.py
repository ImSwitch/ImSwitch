from typing import Dict, List

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger
import threading
import time 
class PositionerController(ImConWidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settingAttr = False

        self.__logger = initLogger(self, tryInheritParent=True)

        # Set up positioners
        for pName, pManager in self._master.positionersManager:
            if not pManager.forPositioning:
                continue

            hasSpeed = hasattr(pManager, 'speed')
            hasHome = hasattr(pManager, 'home')
            hasStop = hasattr(pManager, 'stop')
            self._widget.addPositioner(pName, pManager.axes, hasSpeed, hasHome, hasStop)
            for axis in pManager.axes:
                self.setSharedAttr(pName, axis, _positionAttr, pManager.position[axis])
                if hasSpeed:
                    self.setSharedAttr(pName, axis, _speedAttr, pManager.speed[axis])
                if hasHome:
                    self.setSharedAttr(pName, axis, _homeAttr, pManager.home[axis])
                if hasStop:
                    self.setSharedAttr(pName, axis, _stopAttr, pManager.stop[axis])

        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)

        # Connect PositionerWidget signals
        self._widget.sigStepUpClicked.connect(self.stepUp)
        self._widget.sigStepDownClicked.connect(self.stepDown)
        self._widget.sigStepAbsoluteClicked.connect(self.moveAbsolute)
        self._widget.sigHomeAxisClicked.connect(self.homeAxis)
        self._widget.sigStopAxisClicked.connect(self.stopAxis)

    def closeEvent(self):
        self._master.positionersManager.execOnAll(
            lambda p: [p.setPosition(0, axis) for axis in p.axes],
            condition = lambda p: p.resetOnClose
        )

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    def getSpeed(self):
        return self._master.positionersManager.execOnAll(lambda p: p.speed)

    def move(self, positionerName, axis, dist, isAbsolute=None, isBlocking=False):
        """ Moves positioner by dist micrometers in the specified axis. """
        if positionerName is None:
            positionerName = self._master.positionersManager.getAllDeviceNames()[0]

        # get all speed values from the GUI
        speed = self._widget.getSpeed(positionerName, axis)
        self.setSpeed(positionerName=positionerName, speed=speed, axis=axis)
        try:
            self._master.positionersManager[positionerName].move(dist, axis, isAbsolute, isBlocking)
        except:
            self._master.positionersManager[positionerName].move(dist, axis)
        #self.updatePosition()
        

    def setPos(self, positionerName, axis, position):
        """ Moves the positioner to the specified position in the specified axis. """
        self._master.positionersManager[positionerName].setPosition(position, axis)
        self.updatePosition(positionerName, axis)

    def moveAbsolute(self, positionerName, axis):
        self.move(positionerName, axis, self._widget.getAbsPosition(positionerName, axis), isAbsolute=True,
                  isBlocking=False)

    def stepUp(self, positionerName, axis):
        self.move(positionerName, axis, self._widget.getStepSize(positionerName, axis), isAbsolute=False,
                  isBlocking=False)

    def stepDown(self, positionerName, axis):
        self.move(positionerName, axis, -self._widget.getStepSize(positionerName, axis), isAbsolute=False,
                  isBlocking=False)

    def setSpeed(self, positionerName, axis, speed=(1000, 1000, 1000)):
        self._master.positionersManager[positionerName].setSpeed(speed, axis)
        self.setSharedAttr(positionerName, axis, _speedAttr, speed)
        self._widget.setSpeedSize(positionerName, axis, speed)
        
    def updatePosition(self, positionerName, axis):
        #newPos = self._master.positionersManager[positionerName].position[axis]#FIXME: Is this always pulling the latest position from the device?
        def grabPos():
            for i in range(10):
                newPos = self._master.positionersManager[positionerName].getPosition()[axis]
                self._widget.updatePosition(positionerName, axis, newPos)
                self.setSharedAttr(positionerName, axis, _positionAttr, newPos)
                time.sleep(.3)
        threading.Thread(target=grabPos).start()

    @APIExport(runOnUIThread=True)
    def homeAxis(self, positionerName, axis, isBlocking=False):
        self.__logger.debug(f"Homing axis {axis}")
        self._master.positionersManager[positionerName].doHome(axis)
        self.updatePosition(positionerName, axis)


    def stopAxis(self, positionerName, axis):
        self.__logger.debug(f"Stopping axis {axis}")
        self._master.positionersManager[positionerName].forceStop(axis)

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 4 or key[0] != _attrCategory:
            return

        positionerName = key[1]
        axis = key[2]
        if key[3] == _positionAttr:
            self.setPositioner(positionerName, axis, value)

    def setSharedAttr(self, positionerName, axis, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, positionerName, axis, attr)] = value
        finally:
            self.settingAttr = False

    def setXYPosition(self, x, y):
        positionerX = self.getPositionerNames()[0]
        positionerY = self.getPositionerNames()[1]
        self.__logger.debug(f"Move {positionerX}, axis X, dist {str(x)}")
        self.__logger.debug(f"Move {positionerY}, axis Y, dist {str(y)}")
        # self.move(positionerX, 'X', x)
        # self.move(positionerY, 'Y', y)

    def setZPosition(self, z):
        positionerZ = self.getPositionerNames()[2]
        self.__logger.debug(f"Move {positionerZ}, axis Z, dist {str(z)}")
        # self.move(self.getPositionerNames[2], 'Z', z)

    @APIExport(runOnUIThread=True)
    def enalbeMotors(self, enable=None, enableauto=None):
        try: 
            return self._master.positionersManager.enalbeMotors(enable=None, enableauto=None)
        except:
            pass


    @APIExport()
    def getPositionerNames(self) -> List[str]:
        """ Returns the device names of all positioners. These device names can
        be passed to other positioner-related functions. """
        return self._master.positionersManager.getAllDeviceNames()

    @APIExport()
    def getPositionerPositions(self) -> Dict[str, Dict[str, float]]:
        """ Returns the positions of all positioners. """
        return self.getPos()

    @APIExport(runOnUIThread=True)
    def setPositionerStepSize(self, positionerName: str, stepSize: float) -> None:
        """ Sets the step size of the specified positioner to the specified
        number of micrometers. """
        self._widget.setStepSize(positionerName, stepSize)

    @APIExport(runOnUIThread=True)
    def movePositioner(self, positionerName: str, axis: str, dist: float, isAbsolute: bool = False, isBlocking: bool=False) -> None:
        """ Moves the specified positioner axis by the specified number of
        micrometers. """
        try: # uc2 only
            self.move(positionerName, axis, dist, isAbsolute=isAbsolute, isBlocking=isBlocking)
        except:
            self.move(positionerName, axis, dist)

    @APIExport(runOnUIThread=True)
    def setPositioner(self, positionerName: str, axis: str, position: float) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self.setPos(positionerName, axis, position)

    @APIExport(runOnUIThread=True)
    def setPositionerSpeed(self, positionerName: str, axis: str, speed: float) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self.setSpeed(positionerName, axis, speed)

    @APIExport(runOnUIThread=True)
    def setMotorsEnabled(self, positionerName: str, is_enabled: int) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self._master.positionersManager[positionerName].setEnabled(is_enabled)

    @APIExport(runOnUIThread=True)
    def stepPositionerUp(self, positionerName: str, axis: str) -> None:
        """ Moves the specified positioner axis in positive direction by its
        set step size. """
        self.stepUp(positionerName, axis)

    @APIExport(runOnUIThread=True)
    def stepPositionerDown(self, positionerName: str, axis: str) -> None:
        """ Moves the specified positioner axis in negative direction by its
        set step size. """
        self.stepDown(positionerName, axis)


_attrCategory = 'Positioner'
_positionAttr = 'Position'
_speedAttr = "Speed"
_homeAttr = "Home"
_stopAttr = "Stop"

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
