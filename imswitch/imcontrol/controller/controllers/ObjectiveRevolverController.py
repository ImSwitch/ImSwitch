
from imswitch.imcommon.model import dirtools, modulesconfigtools, ostools, APIExport
from imswitch.imcommon.framework import Signal, Worker, Mutex, Timer
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.controller.basecontrollers import LiveUpdatedController
import imswitch

import time

class ObjectiveRevolverController(LiveUpdatedController):
    """ Linked to ObjectiveRevolverWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self, tryInheritParent=False)

        # connect camera and stage
        self.positionerName = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positionerName]
        self.revolverAxis = "A"
        self.posObjective1 = 0
        self.posObjective2 = 20000
        self.maxDistance = 30000
        self.offsetFromZero = 1000 
        self.speed = 25000
        self.incrementPosition = 50
        
        self.currentObjective = -1
        
        # initialize revolver 
        self.calibrateObjective()

        if imswitch.IS_HEADLESS:
            return

        # Connect signals to slots
        self._widget.btnObj1.clicked.connect(self.onObj1Clicked)
        self._widget.btnObj2.clicked.connect(self.onObj2Clicked)
        self._widget.btnCalibrate.clicked.connect(self.onCalibrateClicked)
        self._widget.btnMovePlus.clicked.connect(self.onMovePlusClicked)
        self._widget.btnMoveMinus.clicked.connect(self.onMoveMinusClicked)
        self._widget.btnSetPosObj1.clicked.connect(self.onSetPosObj1Clicked)
        self._widget.txtPosObj1.setText(str(self.posObjective1))
        self._widget.txtPosObj2.setText(str(self.posObjective2))
        
    @APIExport(runOnUIThread=True)
    def calibrateObjective(self):
        # Move the revolver to the most negative position and then to offsetFromZero in opposite direction
        self.positioner.move(value=-1.5*(self.offsetFromZero+self.posObjective2), speed=self.speed, axis=self.revolverAxis, is_absolute=False, is_blocking=False)
        self.positioner.move(value=self.offsetFromZero, speed=self.speed, axis=self.revolverAxis, is_absolute=False, is_blocking=False)
        self.positioner.setPositionOnDevice(axis=self.revolverAxis, value=0)
        self.currentObjective = 1
        self._widget.setCurrentObjectiveInfo(self.currentObjective)
        
    @APIExport(runOnUIThread=True)
    def moveToObjectiveID(self, objectiveID, posObjective1=None, posObjective2=None):
        if posObjective1 is not None and not imswitch.IS_HEADLESS:
            try:self.posObjective1 = int(self._widget.txtPosObj1.text())
            except:pass
        if posObjective2 is not None and not imswitch.IS_HEADLESS:
            try:self.posObjective2 = int(self._widget.txtPosObj2.text())
            except:pass
        # Move the revolver to the objectiveID
        if objectiveID == 1:
            self.positioner.move(value=self.posObjective1, speed=self.speed, axis=self.revolverAxis, is_absolute=True, is_blocking=False)
            self.currentObjective = 1
        elif objectiveID == 2:
            self.positioner.move(value=self.posObjective2, speed=self.speed, axis=self.revolverAxis, is_absolute=True, is_blocking=False)
            self.currentObjective = 2
        else:
            self._logger.error("Objective ID not valid")
        if not imswitch.IS_HEADLESS: self._widget.setCurrentObjectiveInfo(self.currentObjective)
        
    @APIExport(runOnUIThread=True)
    def getCurrentObjective(self):
        return self.currentObjective, self.positioner.getPosition()[self.revolverAxis]

    def onObj1Clicked(self):
        # move to objective 1
        self.moveToObjectiveID(1)

    def onObj2Clicked(self):
        # move to objective 2
        self.moveToObjectiveID(2)

    def onCalibrateClicked(self):
        # move to objective 1 after homing
        self.calibrateObjective()

    def onMovePlusClicked(self):
        # Define what happens when Move + is clicked
        self.positioner.move(value=self.incrementPosition, speed=self.speed, axis=self.revolverAxis, is_absolute=False, is_blocking=False)  

    def onMoveMinusClicked(self):
        # Define what happens when Move - is clicked
        self.positioner.move(value=-self.incrementPosition, speed=self.speed, axis=self.revolverAxis, is_absolute=False, is_blocking=False)

    def onSetPosObj1Clicked(self):
        # Define what happens when Set Position Objective 1 is clicked
        self.positioner.setPositionOnDevice(axis=self.revolverAxis, value=0)
        self.currentObjective = 1


    
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
