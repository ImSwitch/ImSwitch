from typing import Dict, List

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.controller.controllers import PositionerController

class StandaStageController(ImConWidgetController):
    """ Linked to StandaStageWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settingAttr = False
        self.initialize_positioners()
        self.__logger = initLogger(self, tryInheritParent=True)

    @APIExport()
    def home(self):
        self._master.positionersManager.home()

    def initialize_positioners(self):
        # Set up positioners
        for pName, pManager in self._master.positionersManager:
            if not pManager.forPositioning:
                continue
            hasSpeed = hasattr(pManager, 'speed')
            self._widget.addPositioner(pName, pManager.axes, hasSpeed, pManager.position, pManager.speed)
            for axis in pManager.axes:
                self.setSharedAttr(pName, axis, _positionAttr, pManager.position[axis])
                if hasSpeed:
                    self.setSharedAttr(pName, axis, _speedAttr, pManager.speed[axis])


        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigSetSpeed.connect(lambda speed: self.setSpeedGUI(speed))

        # TODO: Can I overwrite these definitions with the OTDeckController? Then this would be completely independant,
        #  unless the OTDeckController is present.
        # Connect PositionerWidget signals
        self._widget.sigStepUpClicked.connect(self.stepUp)
        self._widget.sigStepDownClicked.connect(self.stepDown)
        self._widget.sigsetSpeedClicked.connect(self.setSpeedGUI)

    def move(self, positionerName, axis, dist):
        """ Moves positioner by dist micrometers in the specified axis. """
        if positionerName is None:
            positionerName = self._master.positionersManager.getAllDeviceNames()[0]

        self._master.positionersManager[positionerName].move(dist, axis)
        self.updatePosition(positionerName, axis)

    def setPos(self, positionerName, axis, position):
        """ Moves the positioner to the specified position in the specified axis. """
        self._master.positionersManager[positionerName].setPosition(position, axis)
        self.updatePosition(positionerName, axis)

    def stepUp(self, positionerName, axis):
        shift = self._widget.getStepSize(positionerName, axis)
        self.move(positionerName= positionerName, axis=axis, dist=shift)
        # if self.scanner.objective_collision_avoidance(axis=axis, shift=shift):
        #     self.move(positionerName, axis, shift)
        #     self.connect_add_current_position()
        # else:
        #     self.__logger.info(f"Avoiding objective collision.")

    def stepDown(self, positionerName, axis):
        shift = -self._widget.getStepSize(positionerName, axis)
        self.move(positionerName= positionerName, axis=axis, dist=shift)
        # if self.scanner.objective_collision_avoidance(axis=axis, shift=shift):
        #     self.move(positionerName, axis, shift)
        # else:
        #     self.__logger.info(f"Avoiding objective collision.")

    def setSpeedGUI(self, positionerName, axis):
        speed = self._widget.getSpeed(positionerName, axis)
        self.setSpeed(positionerName=positionerName, speed=speed, axis=axis)

    def setSpeed(self, positionerName, axis, speed=(12, 12, 8)):
        self._master.positionersManager[positionerName].setSpeed(speed, axis)
        self._widget.updateSpeed(positionerName, axis, speed)

    def updatePosition(self, positionerName, axis):
        newPos = self._master.positionersManager[positionerName].position[axis]
        self._widget.updatePosition(positionerName, axis, newPos)
        self.setSharedAttr(positionerName, axis, _positionAttr, newPos)

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

    def setPositioner(self, positionerName: str, axis: str, position: float) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self.setPos(positionerName, axis, position)


_attrCategory = 'Positioner'
_positionAttr = 'Position'
_speedAttr = "Speed"


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
