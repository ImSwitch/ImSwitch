from typing import Dict, List
from functools import partial
from qtpy import QtCore, QtWidgets

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcontrol.view import guitools as guitools
from imswitch.imcommon.model import initLogger, APIExport
from opentrons.types import Point

class DeckController(ImConWidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self, instanceName="DeckController")

        self.positioner_name = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positioner_name]
        
        # Set up positioners
        '''
                for pName, pManager in self._master.positionersManager:
                if not pManager.forPositioning:
                continue
'''
        self._widget.add_deck_view()
        self.connect_slots()

        
        self.deck_slot_scanner = DeckSlotScanner(self.positioner, deck_pattern="9")
        self.deck_slot_scanner.setDirections(directions=(1,-1,1))

    @APIExport()
    def getDeckSlots(self):
        return self.deck_slot_scanner.slot_positions.items()

    @APIExport()
    def getSlotOrigin(self, slot_ID):
        return self.deck_slot_scanner.get_slot_origin(slot_ID)

    @APIExport(runOnUIThread=False)
    def moveToSlotID(self, slot_ID):
        self.__logger.debug(f"Move to slot {slot_ID}")
        self.deck_slot_scanner.moveToSlotID(slot_ID=slot_ID)
        #pos_xyz = self.positioner.position
        #self.__logger.debug("Move to "+str(coords))
        #absz_init = self._controller._master.positionersManager[self._controller.positioner].get_abs()[gAxis]

        
    def connect_slots(self):
        """Connect Deck Slots (Buttons) to the Sample Pop-Up Method"""
        # Connect signals for all buttons
        for coords, btn in self._widget.slots.items():
            # Connect signals
            #self.pars['UpButton' + parNameSuffix].clicked.connect(
            #    lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            #)
            if isinstance(btn, guitools.BetterPushButton):
                btn.clicked.connect(partial(self.moveToSlotID, coords))
                

class DeckSlotScanner():
    
    def __init__(self, positioner, deck_pattern="9", slot_size = (128.0,86.0),
                 xy_offset = (56.07, 4.43), homing_tolerance = (0.1, 0.1, 0.01)):
        self.__logger = initLogger(self, instanceName="DeckSlotScanner")

        self.positioner = positioner 
        self.is_moving = False
        self.xy_offset = xy_offset
        self.slot_dimensions = slot_size
        if deck_pattern=="9":
            # TODO: load from opentrons deck definition
            self.slot_positions = {
                "HOME": (0,0),
                "1": (1,1),  "2": (2,1),  "3": (3,1),
                "4": (1,2),  "5": (2,2),  "6": (3,2),
                "7": (1,3),  "8": (2,3),  "9": (3,3),
                }
            self.slot_spacing = (9.5, 9.5)
        else:
            self.slot_positions = None
            raise ValueError("Deck pattern unvalid.")
        self.is_homed = self.homed(homing_tolerance)
        self.current_slot = self.get_slot()

    def homed(self, tol = (0.1, 0.1, 0.01)):
        pos = self.positioner.get_position()
        if False in [i < j for i, j in zip(pos,tol)]:
            return False
        else:
            return True

    def get_slot(self, loc = None):
        """
        :param loc: Absolute position
        :return: Slot number
        """
        if loc == None:
            xo, yo, _ = self.positioner.get_position()
        elif isinstance(loc, Point):
            xo, yo, _ = loc
        else:
            raise TypeError
        if not self.is_homed:
            for name, slot in self.slot_positions.items():
                x1 = (slot[0] - 1) * (self.slot_dimensions[0]+self.slot_spacing[0]) + self.xy_offset[0]
                x2 = x1 + (self.slot_dimensions[0]+self.slot_spacing[0])
                y1 = (slot[1] - 1) * (self.slot_dimensions[1]+self.slot_spacing[1]) + self.xy_offset[1]
                y2 = y1 + (self.slot_dimensions[1]+self.slot_spacing[1])
                if x1<xo<x2 and y1<yo<y2:
                    self.__logger.debug(f"Currently in slot {name}.")
                    return name
        return None

    def get_slot_origin(self, slot_name):
        if slot_name == "HOME":
            return 0, 0
        slot = self.slot_positions[slot_name]
        x1 = (slot[0] - 1) * (self.slot_dimensions[0] + self.slot_spacing[0]) + self.xy_offset[0]
        y1 = (slot[1] - 1) * (self.slot_dimensions[1] + self.slot_spacing[1]) + self.xy_offset[1]
        return x1, y1

    def homing(self):
        self.__logger.debug("Homing.")
        self.is_moving = True
        self.positioner.home()
        x,y,z = self.positioner.get_position()
        self.positioner.setPosition(x, "X")
        self.positioner.setPosition(y, "Y")
        self.positioner.setPosition(z, "Z")
        self.is_moving = False
        self.is_homed = True
            
    def moveToSlotID(self, slot_ID="HOME"):
        if slot_ID == "HOME":
            self.homing()
            return
        if self.current_slot == slot_ID:
            self.__logger.debug(f"Already in slot {slot_ID}.")
            return
        self.__logger.debug(f"Moving to slot {slot_ID}.")
        slotID = self.slot_positions[slot_ID]
        pos_X = (slotID[0] - 1) * (self.slot_dimensions[0] + self.slot_spacing[0]) + self.xy_offset[0]
        pos_Y = (slotID[1] - 1) * (self.slot_dimensions[1] + self.slot_spacing[1]) + self.xy_offset[1]
        # Move to center of slot
        pos_X = pos_X + self.slot_dimensions[0]/2
        pos_Y = pos_Y + self.slot_dimensions[1]/2
        self.objective_collision_avoidance()
        self.moveToXY(pos_X, pos_Y)
        self.current_slot = self.get_slot()

    def objective_collision_avoidance(self):
        x,y,z = self.positioner.get_position()
        if z > 1:
            self.__logger.debug("Avoiding objective collision.")
            self.is_moving = True
            self.positioner.move(axis="XYZ", dist=(0, 0, -z), is_blocking=True)
            self.is_moving = False
        return

    def moveToXY(self, pos_X, pos_Y):
        self.__logger.debug(f"Moving to absolute position: {pos_X, pos_Y}.")
        x,y,z = self.positioner.get_position()
        self.positioner.move(axis="XYZ", dist=(pos_X-x, pos_Y-y, 0), is_blocking=False) #, speed=5, is_blocking=True, is_absolute=True)
        self.is_moving = False
        
    def setDirections(self, directions=(1,1,1)):
        if(0):
            self.positioner.set_direction(axis=1, sign=directions[0])
            self.positioner.set_direction(axis=2, sign=directions[1])
            self.positioner.set_direction(axis=3, sign=directions[2])

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
