import os

from opentrons.types import Point
from opentrons.protocol_api.labware import Labware, Well
from opentrons.simulate import get_protocol_api
from opentrons.util.entrypoint_util import labware_from_paths
from opentrons_shared_data.deck import load

from typing import Dict, List
from functools import partial
from qtpy import QtCore, QtWidgets
import json

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController, LiveUpdatedController
from imswitch.imcontrol.view import guitools as guitools
from imswitch.imcommon.model import initLogger, APIExport
from imswitch.imcontrol.controller.controllers.PositionerController import PositionerController

_attrCategory = 'Positioner'
_positionAttr = 'Position'
_speedAttr = "Speed"
_objectiveRadius = 21.8/2

class OpentronsDeckController(LiveUpdatedController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self, instanceName="OpentronsController")
        # Has control over positioner
        self.positioner_name = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positioner_name]
        self.objective_radius = _objectiveRadius
        # Deck and Labwares definitions:
        self.selected_slot = None
        self.load_deck(self._setupInfo.deck["OpentronsDeck"])
        self.labwares = self.load_labwares(self._setupInfo.deck["OpentronsDeck"].labwares)
        self.initialize_positioners()
        self._widget.initialize_opentrons_deck(self.deck, self.labwares)
        self.connect_home()
        self.connect_zero()
        self.connect_deck_slots()
        self.scanner = LabwareScanner(self.positioner, self.deck, self.labwares)

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

        # Connect PositionerWidget signals
        self._widget.sigStepUpClicked.connect(self.stepUp)
        self._widget.sigStepDownClicked.connect(self.stepDown)
        self._widget.sigsetSpeedClicked.connect(self.setSpeedGUI)


    def closeEvent(self):
        self._master.positionersManager.execOnAll(
            lambda p: [p.setPosition(0, axis) for axis in p.axes]
        )

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    def getSpeed(self):
        return self._master.positionersManager.execOnAll(lambda p: p.speed)

    @APIExport(runOnUIThread=True)
    def home(self, positionerName: str) -> None:
        self.positioner.home()
        [self.updatePosition(positionerName, axis) for axis in self.positioner.axes]

    @APIExport(runOnUIThread=True)
    def zero(self):
        self.positioner.zero()

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

    def valid_position(self, positionerName, axis, shift):
        if self.selected_slot is None:
            current_slot = self.scanner.get_slot()
            if current_slot is None:
                return False
            else:
                slot = self.ordered_slots[current_slot]
        else:
            slot = self.ordered_slots[self.selected_slot]

        slot_origin = [a + b for a, b in zip(slot["position"], self.corner_offset)]
        slot_size = [v for v in slot["boundingBox"].values()]

        x1, y1, _ = slot_origin
        x2, y2, _ = [a + b for a, b in zip(slot_origin, slot_size)]

        xo, yo, _ = self.positioner.get_position() # Avoided using positionerName
        if axis == "X":
            xo = xo + shift
        elif axis == "Y":
            yo = yo + shift

        if not x1 + self.objective_radius < xo < x2 - self.objective_radius \
            or not y1 + self.objective_radius < yo < y2 - self.objective_radius:
            return False
        else:
            return True

    def stepUp(self, positionerName, axis):
        shift = self._widget.getStepSize(positionerName, axis)

        if self.valid_position(positionerName, axis, shift):
            self.move(positionerName, axis, shift)
        else:
            self.__logger.info(f"Avoiding objective collision.")

    def stepDown(self, positionerName, axis):
        shift = -self._widget.getStepSize(positionerName, axis)
        if self.valid_position(positionerName, axis, shift):
            self.move(positionerName, axis, shift)
        else:
            self.__logger.info(f"Avoiding objective collision.")

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
    def setPositionerStepSize(self, positionerName: str, axis: str, stepSize: float) -> None:
        """ Sets the step size of the specified positioner to the specified
        number of micrometers. """
        self._widget.setStepSize(positionerName, axis, stepSize)

    @APIExport(runOnUIThread=True)
    def movePositioner(self, positionerName: str, axis: str, dist: float) -> None:
        """ Moves the specified positioner axis by the specified number of
        micrometers. """
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


    def load_labwares(self, labwares):
        labwares_dict = {}
        if "custom" in labwares.keys():
            if labwares["custom"] is None:
                protocol = get_protocol_api("2.12")
            else:
                # Load custom/extra labware
                # c_labw = [os.sep.join([labwares["custom_labwares_path"],labw+".json"]) for labw in labwares["custom"].values()]
                self._custom_labware = labware_from_paths([labwares["custom_labwares_path"]])
                protocol = get_protocol_api("2.12", extra_labware=self._custom_labware)
                for slot, labware_file in labwares["custom"].items():
                    labwares_dict[slot] = protocol.load_labware(labware_file, slot)
        else:
            protocol = get_protocol_api("2.12")
        # Load standard labware
        for slot, labware_file in labwares["standard"].items():
            labwares_dict[slot] = protocol.load_labware(labware_file, slot)
        return labwares_dict

    def load_deck(self, deck):
        if deck.deck_name is None:
            deck_dict = load(name="ot2_standard", version=3)
        else:
            path = os.sep.join([deck.deck_path,deck.deck_name+".json"])
            deck_dict = json.load(open(path))
        self.deck = deck_dict
        self.ordered_slots = {slot["id"]: slot for i,slot in enumerate(self.deck["locations"]["orderedSlots"])}
        self.corner_offset = [abs(i) for i in self.deck["cornerOffsetFromOrigin"]]
        return

    @APIExport()
    def get_labwares(self):
        return self.labwares

    @APIExport()
    def getAvailableLabwareSlots(self):
        return [slot for slot in self.labwares.keys()]

    @APIExport()
    def select_labware(self, slot):
        self.__logger.debug(f"Slot {slot}")
        self._widget.select_labware(slot)
        # TODO: change color of selected slot button.
        self.selected_slot = slot
        self.connect_wells()

    @APIExport(runOnUIThread=True)
    def moveToWell(self, well, slot = None):
        if isinstance(well, Well):
            slot = well.parent.parent
            well = well.well_name
        self.__logger.debug(f"Move to {well}")
        self.scanner.moveToWell(well=well, slot= slot if slot is not None else self.selected_slot)
        [self.updatePosition(self.positioner_name, axis) for axis in self.positioner.axes]
        # TODO: change color of selected well button.


    def connect_deck_slots(self):
        """Connect Deck Slots (Buttons) to the Sample Pop-Up Method"""
        # Connect signals for all buttons
        for slot, btn in self._widget.deck_slots.items():
            # Connect signals
            #self.pars['UpButton' + parNameSuffix].clicked.connect(
            #    lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            #)
            if isinstance(btn, guitools.BetterPushButton):
                btn.clicked.connect(partial(self.select_labware, slot))

    def connect_home(self):
        """Connect Wells (Buttons) to the Sample Pop-Up Method"""
        if isinstance(self._widget.home, guitools.BetterPushButton):
            self._widget.home.clicked.connect(partial(self.home, self.positioner_name))
    def connect_zero(self):
        """Connect Wells (Buttons) to the Sample Pop-Up Method"""
        if isinstance(self._widget.zero, guitools.BetterPushButton):
            self._widget.home.clicked.connect(partial(self.zero, self.positioner_name))

    def connect_wells(self):
        """Connect Wells (Buttons) to the Sample Pop-Up Method"""
        # Connect signals for all buttons
        for well, btn in self._widget.wells.items():
            # Connect signals
            #self.pars['UpButton' + parNameSuffix].clicked.connect(
            #    lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            #)
            if isinstance(btn, guitools.BetterPushButton):
                btn.clicked.connect(partial(self.moveToWell, well, self.selected_slot))

class LabwareScanner():
    def __init__(self, positioner, deck, labwares):
        self.__logger = initLogger(self, instanceName="DeckSlotScanner")

        self.positioner = positioner
        self.deck = deck
        self.slots_list = self.deck["locations"]["orderedSlots"]
        self.corner_offset = [abs(i) for i in self.deck["cornerOffsetFromOrigin"]]
        self.labwares = labwares

        self.is_moving = False

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

        for slot in self.slots_list:
            slot_origin = [a+b for a,b in zip(slot["position"],self.corner_offset)]
            slot_size = [v for v in slot["boundingBox"].values()]
            x1, y1, _ = slot_origin
            x2, y2, _ = [a+b for a,b in zip(slot_origin,slot_size)]
            if x1<xo<x2 and y1<yo<y2:
                self.__logger.debug(f"Currently in slot {slot['id']}.")
                return slot['id']
        return None

    def moveToWell(self, well, slot = None):
        if not isinstance(well, Well):
            well = self.labwares[slot].wells_by_name()[well]
        # TODO: should receive Well/Labware class??
        self.__logger.debug(f"Moving to well: {well} in slot: {slot}.")
        x,y,_ = well.geometry.position
        x_offset, y_offset, _ =  self.corner_offset
        if slot != self.get_slot():
            self.objective_collision_avoidance()
        self.moveToXY(x + abs(x_offset), y + abs(y_offset))

    def objective_collision_avoidance(self):
        x, y, z = self.positioner.get_position()
        if z > 1:
            self.__logger.debug("Avoiding objective collision.")
            self.is_moving = True
            self.positioner.move(axis="XYZ", dist=(0, 0, -z), is_blocking=True)
            self.is_moving = False
        return

    def moveToXY(self, pos_X, pos_Y):
        self.__logger.debug(f"Moving to absolute position: {pos_X, pos_Y}.")
        x, y, z = self.positioner.get_position()
        self.positioner.move(axis="XY", dist=(pos_X - x, pos_Y - y),
                             is_blocking=False)  # , speed=5, is_blocking=True, is_absolute=True)
        # self.positioner.move(axis="XY", dist=(pos_X - x, pos_Y - y),
        #                      is_blocking=False)
        self.is_moving = False

    def setDirections(self, directions=(1, 1, 1)):
        if (0):
            self.positioner.set_direction(axis=1, sign=directions[0])
            self.positioner.set_direction(axis=2, sign=directions[1])
            self.positioner.set_direction(axis=3, sign=directions[2])