from typing import Dict, List

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger


class RotatorController(ImConWidgetController):
    """ Linked to RotatorWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)

        # Set up rotator in widget
        self._widget.addRotator()

        # Connect PositionerWidget signals
        self._widget.sigMoveForwRelClicked.connect(lambda: self.moveRel(dir=1))
        self._widget.sigMoveBackRelClicked.connect(lambda: self.moveRel(dir=-1))
        self._widget.sigMoveAbsClicked.connect(self.moveAbs)

    def closeEvent(self):
        self._master.positionersManager.execOnAll(
            lambda p: [p.setPosition(0, axis) for axis in p.axes]
        )

    def move(self, positionerName, axis, dist):
        self._master.positionersManager[positionerName].move(dist, axis)
        self.updatePosition(positionerName, axis)

    def moveRel(self, dir=1):
        dist = dir * self._widget.getRelStepSize()
        self._master.standaMotorManager.move_rel(dist)
        self.updatePosition()

    def moveAbs(self):
        pos = self._widget.getAbsPos()
        self._master.standaMotorManager.move_abs(pos)
        self.updatePosition()

    def updatePosition(self):
        pos = self._master.standaMotorManager.position()
        self._widget.updatePosition(pos)


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
