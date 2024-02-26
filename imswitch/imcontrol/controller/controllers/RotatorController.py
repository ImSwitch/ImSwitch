from imswitch.imcommon.model import initLogger
from ..basecontrollers import ImConWidgetController


class RotatorController(ImConWidgetController):
    """ Linked to RotatorWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)

        # Set up rotator in widget
        for name, _ in self._master.rotatorsManager:
            self._widget.addRotator(name)

        # careful, breaks for more stages
        self.name = name

        # Connect Rotator Widget signals
        self._widget.sigMoveRelClicked.connect(lambda name, dir: self.moveRel(name, dir))
        self._widget.sigMoveAbsClicked.connect(lambda name: self.moveAbs(name))
        self._widget.sigSetZeroClicked.connect(lambda name: self.setZeroPos(name))
        self._widget.sigSetSpeedClicked.connect(lambda name: self.setSpeed(name))
        self._widget.sigStartContMovClicked.connect(lambda name: self.startContMov(name))
        self._widget.sigStopContMovClicked.connect(lambda name: self.stopContMov(name))

        # Connect commChannel signals
        self._commChannel.sigUpdateRotatorPosition.connect(
                                    lambda name: self.updatePosition(name))
        self._commChannel.sigSetSyncInMovementSettings.connect(
                                    lambda name,
                                    pos: self.setSyncInMovement(name, pos))
        self._commChannel.sigPositionUpdated.connect(
                                    lambda name: self.updatePosition(name)
        )
        
        # Update current position in GUI
        self.updatePosition(name)

    def closeEvent(self):
        pass

    def moveRel(self, name, dir=1):
        """Call manager to rotate angle relative to
        current position.

        Args:
            name (str): Qt element.
            dir (int, optional): clockwise is 1. Defaults to 1.
        """
        # this is in degrees
        dist = dir * self._widget.getRelStepSize(name)
        self.__logger.debug(f'angle to rotate: {dist}')
        self._master.rotatorsManager[name].move_rel(dist)

    def moveAbs(self, name):
        pos = self._widget.getAbsPos(name)
        self._master.rotatorsManager[name].move_abs(pos)

    def setZeroPos(self, name):
        self._master.rotatorsManager[name].set_zero_pos()
        self.updatePosition(name)

    def setSpeed(self, name):
        speed = self._widget.getSpeed(name)
        self._master.rotatorsManager[name].set_rot_speed(speed)

    def startContMov(self, name):
        self._master.rotatorsManager[name].start_cont_rot()

    def stopContMov(self, name):
        self._master.rotatorsManager[name].stop_cont_rot()
        self.updatePosition(name)

    def updatePosition(self, name):
        pos = self._master.rotatorsManager[name].get_position()
        self._widget.updatePosition(name, pos[1])

    def setSyncInMovement(self, name, pos):
        self._master.rotatorsManager[name].set_sync_in_pos(pos)


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
