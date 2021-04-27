from imswitch.imcommon.model import APIExport
from .basecontrollers import ImConWidgetController


class PositionerController(ImConWidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settingAttr = False

        # Set up positioners
        for pName, pManager in self._master.positionersManager:
            self._widget.addPositioner(pName)
            self.setSharedAttr(pName, _positionAttr, pManager.position)

        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)

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
        self.setSharedAttr(positionerName, _positionAttr, newPos)

    def setPos(self, positionerName, position):
        """ Moves the piezzos in x y or z (axis) to the specified position. """
        newPos = self._master.positionersManager[positionerName].setPosition(position)
        self._widget.updatePosition(positionerName, newPos)
        self.setSharedAttr(positionerName, _positionAttr, newPos)

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 3 or key[0] != _attrCategory:
            return

        positionerName = key[1]
        if key[2] == _positionAttr:
            self.setPositioner(positionerName, value)

    def setSharedAttr(self, positionerName, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, positionerName, attr)] = value
        finally:
            self.settingAttr = False

    @APIExport
    def getPositionerNames(self):
        """ Returns the device names of all positioners. These device names can
        be passed to other positioner-related functions. """
        return self._master.positionersManager.getAllDeviceNames()

    @APIExport
    def getPositionerPositions(self):
        """ Returns the positions of all positioners. """
        return self.getPos()

    @APIExport
    def setPositionerStepSize(self, positionerName, stepSize):
        """ Sets the step size of the specified positioner to the specified
        number of micrometers. """
        self._widget.setStepSize(positionerName, stepSize)

    @APIExport
    def movePositioner(self, positionerName, dist):
        """ Moves the specified positioner by the specified number of
        micrometers. """
        self.move(positionerName, dist)

    @APIExport
    def setPositioner(self, positionerName, position):
        """ Moves the specified positioner to the specified position. """
        self.setPos(positionerName, position)

    @APIExport
    def stepPositionerUp(self, positionerName):
        """ Moves the specified positioner in positive direction by its set
        step size. """
        self.move(positionerName, self._widget.getStepSize(positionerName))

    @APIExport
    def stepPositionerDown(self, positionerName):
        """ Moves the specified positioner in negative direction by its set
        step size. """
        self.move(positionerName, -self._widget.getStepSize(positionerName))


_attrCategory = 'Positioner'
_positionAttr = 'Position'
    

# Copyright (C) 2020, 2021 TestaLab
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
