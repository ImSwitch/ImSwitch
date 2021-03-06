from .basecontrollers import ImConWidgetController


class PositionerController(ImConWidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for pName, pManager in self._master.positionersManager:
            self._widget.addPositioner(pName)
            self.setSharedAttr(pName, 'Position', pManager.position)

        # Connect CommunicationChannel signals
        self._commChannel.sigMoveZStage.connect(lambda step: self.move('Z', step))

        # Connect PositionerWidget signals
        self._widget.sigStepUpClicked.connect(
            lambda positionerName: self.move(positionerName, self._widget.getStepSize(positionerName))
        )
        self._widget.sigStepDownClicked.connect(
            lambda positionerName: self.move(positionerName, -self._widget.getStepSize(positionerName))
        )

    def closeEvent(self):
        self._master.positionersManager.execOnAll(lambda p: p.setPosition(0))

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    def move(self, positionerName, dist):
        """ Moves the piezzos in x y or z (axis) by dist micrometers. """
        newPos = self._master.positionersManager[positionerName].move(dist)
        self._widget.updatePosition(positionerName, newPos)
        self.setSharedAttr(positionerName, 'Position', newPos)

    def setSharedAttr(self, positionerName, attr, value):
        self._commChannel.sharedAttrs[('Positioners', positionerName, attr)] = value
    
# Copyright (C) 2020, 2021 Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
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