import json
import time
from functools import partial
from typing import Optional

import numpy as np
from imswitch.imcommon.framework import Signal
from imswitch.imcommon.model import initLogger, APIExport
from imswitch.imcontrol.view import guitools as guitools
from opentrons.types import Point

from locai.deck.deck_config import DeckConfig
from ..basecontrollers import LiveUpdatedController
from ...model.SetupInfo import OpentronsDeckInfo

_attrCategory = 'Positioner'
_positionAttr = 'Position'
_speedAttr = "Speed"
_homeAttr = "Home"
_stopAttr = "Stop"
_objectiveRadius = 21.8 / 2
_objectiveRadius = 29.0 / 2  # Olympus


class DeckController(LiveUpdatedController):
    """ Linked to OpentronsDeckWidget.
    Safely moves around the OTDeck and saves positions to be scanned with OpentronsDeckScanner."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self, instanceName="DeckController")

        # Deck and Labwares definitions:
        self.objective_radius = _objectiveRadius
        ot_info: OpentronsDeckInfo = self._setupInfo.deck["OpentronsDeck"]
        deck_layout = json.load(open(ot_info.deck_file, "r"))

        self.deck_definition = DeckConfig(deck_layout, ot_info.labwares)
        self.default_positions_in_well = {key: tuple(value) for key,value in self._setupInfo.deck["OpentronsDeck"].default_positions.items()}
        self.translate_units = self._setupInfo.deck["OpentronsDeck"].translate_units
        # Has control over positioner
        self.initialize_positioners()
        #
        self.selected_slot = None
        self.selected_well = None
        # self.scanner = LabwareScanner(self.positioner, self.deck, self.labwares, _objectiveRadius)
        self._widget.initialize_deck(self.deck_definition.deck, self.deck_definition.labwares)
        self._widget.init_scan_list()
        self.connect_all_buttons()
        self._widget.scan_list.sigGoToTableClicked.connect(self.go_to_position_in_table)

    def go_to_position_in_table(self, absolute_position):
        self.move(new_position=Point(*absolute_position))

    @property
    def selected_well(self):
        return self._selected_well

    @selected_well.setter
    def selected_well(self, well):
        self._selected_well = well

    @property
    def selected_slot(self):
        return self._selected_slot

    @selected_slot.setter
    def selected_slot(self, slot):
        self._selected_slot = slot

    def connect_all_buttons(self):
        self.connect_home()
        self.connect_zero()
        self.connect_deck_slots()
        self.connect_add_current_position()
        self.connect_line_edit()

    def initialize_positioners(self):
        # Has control over positioner
        self.positioner_name = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positioner_name]
        # Set up positioners
        for pName, pManager in self._master.positionersManager:
            if not pManager.forPositioning:
                continue
            hasSpeed = hasattr(pManager, 'speed')
            hasHome = hasattr(pManager, 'home')
            hasStop = hasattr(pManager, 'stop')
            self._widget.addPositioner(pName, pManager.axes, hasSpeed, hasHome, hasStop)
            for axis in pManager.axes:
                self.setSharedAttr(axis, _positionAttr, pManager.position[axis])
                if hasSpeed:
                    self.setSharedAttr(axis, _speedAttr, pManager.speed[axis])
                if hasHome:
                    self.setSharedAttr(axis, _homeAttr, pManager.home[axis])
                if hasStop:
                    self.setSharedAttr(axis, _stopAttr, pManager.stop[axis])

        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigSetSpeed.connect(lambda speed: self.setSpeedGUI(speed))

        # Connect PositionerWidget signals
        self._widget.sigStepUpClicked.connect(self.stepUp)
        self._widget.sigStepDownClicked.connect(self.stepDown)
        self._widget.sigsetSpeedClicked.connect(self.setSpeedGUI)
        self._widget.sigStepAbsoluteClicked.connect(self.moveAbsolute)
        self._widget.sigHomeAxisClicked.connect(self.homeAxis)
        self._widget.sigStopAxisClicked.connect(self.stopAxis)

    def stopAxis(self, positionerName, axis):
        self.__logger.debug(f"Stopping axis {axis}")
        self._master.positionersManager[positionerName].forceStop(axis)

    def homeAxis(self, positionerName, axis):
        self.__logger.debug(f"Homing axis {axis}")
        self._master.positionersManager[positionerName].doHome(axis)

    def closeEvent(self):
        self._master.positionersManager.execOnAll(
            lambda p: [p.setPosition(0, axis) for axis in p.axes]
        )

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    def getSpeed(self):
        return self._master.positionersManager.execOnAll(lambda p: p.speed)

    @APIExport(runOnUIThread=True)
    def home(self) -> None:
        # TODO: fix home in PositionerManager
        self.positioner.doHome("X")
        time.sleep(0.1)
        self.positioner.doHome("Y")
        [self.updatePosition(axis) for axis in self.positioner.axes]

    @APIExport(runOnUIThread=True)
    def zero(self):
        # TODO: zero z-axis when first position focal plane found.
        _,_,self._widget.first_z_focus = self.positioner.get_position()
        try:
            self._commChannel.sigInitialFocalPlane.emit(self._widget.first_z_focus)
            print(f"Updated initial focus {self._widget.first_z_focus}")
        except Exception as e:
            print(f"Zeroing failed {e}")
        # self._commChannel.sigZeroZAxis.emit(self._widget.first_z_focus)

        # self.setPositioner(position=0, axis="Z")
        # self.positioner.zero()

    @APIExport(runOnUIThread=True)
    def move(self, new_position):
        """ Moves positioner to absolute position. """
        speed = [self._widget.getSpeed(self.positioner_name, axis) for axis in self.positioner.axes]
        self.positioner.move(new_position, "XYZ", is_absolute=True, is_blocking=False, speed=speed)
        [self.updatePosition(axis) for axis in self.positioner.axes]
        self.connect_add_current_position()

    def setPos(self, axis, position):
        """ Moves the positioner to the specified position in the specified axis. """
        self.positioner.setPosition(position, axis)
        self.updatePosition(axis)

    def moveAbsolute(self, axis):
        self.positioner.move(self._widget.getAbsPosition(self.positioner_name, axis), axis=axis, is_absolute=True,
                             is_blocking=False)
        [self.updatePosition(axis) for axis in self.positioner.axes]
        self.connect_add_current_position()

    def stepUp(self, positionerName, axis):
        shift = self._widget.getStepSize(positionerName, axis)
        # if self.scanner.objective_collision_avoidance(axis=axis, shift=shift):
        try:
            self.positioner.move(shift, axis, is_blocking=False)
            [self.updatePosition(axis) for axis in self.positioner.axes]
            self.connect_add_current_position()
        except Exception as e:
            self.__logger.info(f"Avoiding objective collision. {e}")

    def stepDown(self, positionerName, axis):
        shift = -self._widget.getStepSize(positionerName, axis)
        try:
            self.positioner.move(shift, axis, is_blocking=False)
            [self.updatePosition(axis) for axis in self.positioner.axes]
            self.connect_add_current_position()
        except Exception as e:
            self.__logger.info(f"Avoiding objective collision. {e}")

    def setSpeedGUI(self, axis):
        speed = self._widget.getSpeed(self.positioner_name, axis)
        self.setSpeed(speed=speed, axis=axis)

    def setSpeed(self, axis, speed=(12, 12, 8)):
        self.positioner.setSpeed(speed, axis)
        self._widget.updateSpeed(self.positioner_name, axis, speed)

    def updatePosition(self, axis):
        newPos = self.positioner.position[axis]
        self._widget.updatePosition(self.positioner_name, axis, newPos)
        self.setSharedAttr(axis, _positionAttr, newPos)

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 4 or key[0] != _attrCategory:
            return
        # positionerName = key[1]
        axis = key[2]
        if key[3] == _positionAttr:
            self.setPositioner(axis, value)

    def setPositioner(self, axis: str, position: float) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self.setPos(axis, position)

    def setSharedAttr(self, axis, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, self.positioner_name, axis, attr)] = value
        finally:
            self.settingAttr = False

    @APIExport()
    def get_labwares(self):
        return self.deck_definition.labwares

    @APIExport()
    def getAvailableLabwareSlots(self):
        return [slot for slot in self.deck_definition.labwares.keys()]

    @APIExport(runOnUIThread=True)
    def select_labware(self, slot):
        self.__logger.debug(f"Slot {slot}")
        self._widget.select_labware(slot)
        self.selected_slot = slot
        self.selected_well = None
        self.connect_wells()
        # self.connect_add_position()

    @APIExport(runOnUIThread=True)
    def select_well(self, well):
        self.__logger.debug(f"Well {well}")
        self.selected_well = well
        self._widget.select_well(well)
        self.connect_go_to()
        self.connect_add_position()

    def retranslate_position(self, position: Point, flip_xy=False):
        if flip_xy:  # TODO: avoid this by using normal coordinate system
            position = Point(position.y, position.x, position.z)
        if self.translate_units == "mm2um":
            return position * 0.001
        elif self.translate_units == "um2mm":
            return position * 1000
        elif self.translate_units is None:
            return position
        else:
            raise NotImplementedError(f"Not recognized units.")

    def translate_position(self, position: Point, flip_xy=False):
        if flip_xy:  # TODO: avoid this by using normal coordinate system
            position = Point(position.y, position.x, position.z)
        if self.translate_units == "mm2um":
            return position * 1000
        elif self.translate_units == "um2mm":
            return position * 0.001
        elif self.translate_units is None:
            return position
        else:
            raise NotImplementedError(f"Not recognized units.")

    @APIExport(runOnUIThread=True)
    def move_to_well(self, well: str, slot: Optional[str] = None):
        """ Moves positioner to center of selecterd well keeping the current Z-axis position. """
        self.__logger.debug(f"Move to {well} ({slot})")
        speed = [self._widget.getSpeed(self.positioner_name, axis) for axis in self.positioner.axes]
        well_position = self.deck_definition.get_well_position(slot=slot, well=well)
        well_position = self.translate_position(well_position)
        self.positioner.move(well_position[:2], "XY", is_absolute=True, is_blocking=False,
                             speed=speed[:2])
        [self.updatePosition(axis) for axis in self.positioner.axes]
        self.connect_add_current_position()

    def connect_line_edit(self):
        self._widget.pos_in_well_lined.textChanged.connect(self.connect_add_position)

    def current_slot(self):
        return self.deck_definition.get_slot(self.positioner.get_position())

    def get_position_in_deck(self):
        return Point(*self.positioner.get_position()) + self.deck_definition.corner_offset

    def update_values(self):
        current_position = Point(*self.positioner.get_position())
        try:
            current_position_deck = self.retranslate_position(current_position)
            current_slot = self.deck_definition.get_slot(current_position_deck)
            current_well = self.deck_definition.get_closest_well(current_position_deck)
            self._widget.current_slot = current_slot
            self._widget.current_well = current_well
            self._widget.current_absolute_position = current_position
            self._widget.current_z_focus = current_position.z
            well_position = self.deck_definition.get_well_position(current_slot, current_well)  # Deck measurement
            well_position = self.translate_position(well_position)  # Posioner value
            if self._widget.current_slot is not None and self._widget.current_well is not None:
                # Offset gets defined positively: when shifting an offset it should be shift = offset - current_position
                zero = self.translate_position(10e-4)  # Positioner value
                offset = tuple([a - b if np.abs(a - b) > zero else 0.00 for (a, b) in
                                zip(well_position,
                                    current_position)][:2])
                self._widget.current_offset = offset  # Positioner Values
        except Exception as e:
            self.__logger.debug(f"Error when updating values. {e}")

    def connect_add_current_position(self):
        if isinstance(self._widget.add_current_btn, guitools.BetterPushButton):
            try:
                self._widget.add_current_btn.disconnect()
            except Exception:
                pass
            self._widget.add_current_btn.clicked.connect(self.update_values)
            self._widget.add_current_btn.clicked.connect(self._widget.add_current_position_to_scan)
        else:
            slot, well, offset, z_focus, absolute_position = (0, "Z0", ("inf", "inf"), 0, ("inf", "inf", "inf"))
            if isinstance(self._widget.add_current_btn, guitools.BetterPushButton):
                try:
                    self._widget.add_current_btn.disconnect()
                except Exception:
                    pass
                self._widget.add_current_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, slot, well, offset, z_focus, absolute_position))

    def connect_add_position(self):
        if isinstance(self._widget.add_btn, guitools.BetterPushButton):
            try:
                self._widget.add_btn.disconnect()
            except Exception:
                pass
            x, y, _ = self.deck_definition.get_well_position(slot=self.selected_slot, well=self.selected_well)
            z = self._widget.current_z_focus or float(self.positioner.position["Z"])
            x, y, _ = self.translate_position(Point(x, y, z))  # Positioner value
            self._widget.current_z_focus = z
            if self._widget.positions_in_well == 1:
                offset = self.default_positions_in_well["center"]
                self._widget.add_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, self.selected_slot, self.selected_well, offset,
                            self._widget.current_z_focus, (x, y, z)))
            elif self._widget.positions_in_well == 2:
                self._widget.add_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, self.selected_slot, self.selected_well,
                            self.default_positions_in_well["left"], self._widget.current_z_focus, (x, y, z)))
                self._widget.add_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, self.selected_slot, self.selected_well,
                            self.default_positions_in_well["right"], self._widget.current_z_focus, (x, y, z)))
            elif self._widget.positions_in_well == 3:
                self._widget.add_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, self.selected_slot, self.selected_well,
                            self.default_positions_in_well["left"], self._widget.current_z_focus, (x, y, z)))
                self._widget.add_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, self.selected_slot, self.selected_well,
                            self.default_positions_in_well["right"], self._widget.current_z_focus, (x, y, z)))
                self._widget.add_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, self.selected_slot, self.selected_well,
                            self.default_positions_in_well["up"], self._widget.current_z_focus, (x, y, z)))
            elif self._widget.positions_in_well == 4:
                self._widget.add_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, self.selected_slot, self.selected_well,
                            self.default_positions_in_well["left"], self._widget.current_z_focus, (x, y, z)))
                self._widget.add_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, self.selected_slot, self.selected_well,
                            self.default_positions_in_well["right"], self._widget.current_z_focus, (x, y, z)))
                self._widget.add_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, self.selected_slot, self.selected_well,
                            self.default_positions_in_well["up"], self._widget.current_z_focus, (x, y, z)))
                self._widget.add_btn.clicked.connect(
                    partial(self._widget.add_position_to_scan, self.selected_slot, self.selected_well,
                            self.default_positions_in_well["down"], self._widget.current_z_focus, (x, y, z)))

            # offset = well.geometry.position - self.positioner.get_position()

    def connect_deck_slots(self):
        """Connect Deck Slots (Buttons) to the Sample Pop-Up Method"""
        # Connect signals for all buttons
        for slot, btn in self._widget.deck_slots.items():
            # Connect signals
            # self.pars['UpButton' + parNameSuffix].clicked.connect(
            #    lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            # )
            if isinstance(btn, guitools.BetterPushButton):
                btn.clicked.connect(partial(self.select_labware, slot))

    def connect_go_to(self):
        """Connect Wells (Buttons) to the Sample Pop-Up Method"""
        if isinstance(self._widget.goto_btn, guitools.BetterPushButton):
            try:
                self._widget.goto_btn.clicked.disconnect()
            except Exception:
                pass
            self._widget.goto_btn.clicked.connect(partial(self.move_to_well, self.selected_well, self.selected_slot))

    def connect_home(self):
        """Connect Wells (Buttons) to the Sample Pop-Up Method"""
        if isinstance(self._widget.home, guitools.BetterPushButton):
            self._widget.home.clicked.connect(self.home)

    def connect_zero(self):
        """Connect Wells (Buttons) to the Sample Pop-Up Method"""
        if isinstance(self._widget.zero, guitools.BetterPushButton):
            self._widget.zero.clicked.connect(self.zero)

    def connect_wells(self):
        """Connect Wells (Buttons) to the Sample Pop-Up Method"""
        # Connect signals for all buttons
        for well, btn in self._widget.wells.items():
            # Connect signals
            # self.pars['UpButton' + parNameSuffix].clicked.connect(
            #    lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            # )
            if isinstance(btn, guitools.BetterPushButton):
                btn.clicked.connect(partial(self.select_well, well))

#
# class LabwareScanner():
#     def __init__(self, positioner, deck, labwares, objective_radius):
#         self.__logger = initLogger(self, instanceName="DeckSlotScanner")
#
#         self.positioner = positioner
#         self.deck = deck
#         self.slots_list = self.deck["locations"]["orderedSlots"]
#         self.corner_offset = [abs(i) for i in self.deck["cornerOffsetFromOrigin"]]
#         self.deck_definition.labwares = labwares
#         self.objective_radius = objective_radius
#         self.default_positions_in_well = {"center": (0, 0), "left": (-0.01, 0),
#                                           "right": (0.01, 0), "up": (0, 0.01), "down": (0, -0.01)}
#         self.is_moving = False
#
#     def get_closest_well(self, loc=None):
#         """
#         :param loc: Absolute position
#         :return: Well
#         """
#         if loc is None:
#             xo, yo, _ = self.positioner.get_position()
#         elif isinstance(loc, Point):
#             xo, yo, _ = loc
#         else:
#             raise TypeError
#         slot = self.get_slot(loc=loc)
#         if slot is None:
#             return None
#         dist_to_well = 10 ** 5
#         closest_well = None
#
#         if slot not in self.deck_definition.labwares.keys():
#             self.__logger.debug("No defined labware in current slot.")
#             return None
#         for well in self.deck_definition.labwares[slot].wells():
#             radius = well.diameter / 2
#             x1, y1, _ = well.geometry.position + Point(*self.corner_offset)
#             dist = np.linalg.norm((xo - x1, yo - y1))
#             if dist < dist_to_well:
#                 dist_to_well = dist
#                 closest_well = well
#                 if x1 - radius < xo < x1 + radius and y1 - radius < yo < y1 + radius:
#                     self.__logger.debug(f"Currently in well {well}.")
#                     return well
#         return closest_well
#
#     def get_slot(self, loc=None):
#         """
#         :param loc: Absolute position
#         :return: Slot number
#         """
#         if loc is None:
#             xo, yo, _ = self.positioner.get_position()
#         elif isinstance(loc, Point):
#             xo, yo, _ = loc
#         else:
#             raise TypeError
#
#         for slot in self.slots_list:
#             slot_origin = [a + b for a, b in zip(slot["position"], self.corner_offset)]
#             slot_size = [v for v in slot["boundingBox"].values()]
#             x1, y1, _ = slot_origin
#             x2, y2, _ = [a + b for a, b in zip(slot_origin, slot_size)]
#             if x1 < xo < x2 and y1 < yo < y2:
#                 # self.__logger.debug(f"Currently in slot {slot['id']}.")
#                 return slot['id']
#         return None
#
#     def move_to_well(self, well, slot):
#         if not isinstance(well, Well):
#             well = self.deck_definition.labwares[slot].wells_by_name()[well]
#         x, y, _ = well.geometry.position
#         x_offset, y_offset, _ = self.corner_offset
#         new_pos = (x + abs(x_offset), y + abs(y_offset))
#         if self.objective_collision_avoidance(axis="XY", new_pos=new_pos, slot=slot):
#             self.__logger.debug(f"Moving to well: {well} in slot: {slot}. Abs. Pos.: {new_pos[0], new_pos[1]}")
#             self.moveToXY(new_pos[0], new_pos[1])
#         else:
#             self.__logger.info(f"Avoiding objective collision.")
#
#     # def valid_position(self, axis, shift):
#     #     if self.selected_slot is None:
#     #         current_slot = self.get_slot()
#     #         if current_slot is None:
#     #             return False
#     #         else:
#     #             slot = self.slots_list[current_slot]
#     #     else:
#     #         slot = self.slots_list[self.selected_slot]
#     #
#     #     slot_origin = [a + b for a, b in zip(slot["position"], self.corner_offset)]
#     #     slot_size = [v for v in slot["boundingBox"].values()]
#     #
#     #     x1, y1, _ = slot_origin
#     #     x2, y2, _ = [a + b for a, b in zip(slot_origin, slot_size)]
#     #
#     #     xo, yo, _ = self.positioner.get_position()  # Avoided using positionerName
#     #     if axis == "X":
#     #         xo = xo + shift
#     #     elif axis == "Y":
#     #         yo = yo + shift
#     #
#     #     if not x1 + self.objective_radius < xo < x2 - self.objective_radius \
#     #             or not y1 + self.objective_radius < yo < y2 - self.objective_radius:
#     #         return False
#     #     else:
#     #         return True
#
#     def check_position_in_well(self, well, pos):
#         if (abs(pos[0]) < well.diameter / 2) and (abs(pos[1]) < well.diameter / 2):
#             return
#         else:
#             raise ValueError("Position outside well.")
#
#     def objective_collision_avoidance(self, axis, new_pos=None, slot=None, shift=None):
#         xo, yo, z = self.positioner.get_position()
#         if axis == "Z":
#             if slot is not None:
#                 if slot == self.get_slot():  # Moving objective within a slot
#                     return True
#                 else:  # Apply collision avoidance
#                     return False
#             else:
#                 if self.get_slot() is not None:
#                     return True
#                 else:
#                     return False
#         else:
#             # Define XY shift
#             if axis == "X":
#                 new_x = new_pos if shift is None else xo + shift
#                 new_y = yo
#             elif axis == "Y":
#                 new_x = xo
#                 new_y = new_pos if shift is None else yo + shift
#             elif axis == "XY":
#                 new_x = new_pos[0] if shift is None else xo + shift[0]
#                 new_y = new_pos[1] if shift is None else yo + shift[1]
#
#             # Called with positioner arrows within one slot -> avoid collision and check borders
#             if slot is None and self.get_slot() is not None:
#                 slot_dict = self.slots_list[int(self.get_slot()) - 1]
#
#                 slot_origin = [a + b for a, b in zip(slot_dict["position"], self.corner_offset)]
#                 slot_size = [v for v in slot_dict["boundingBox"].values()]
#
#                 x1, y1, _ = slot_origin
#                 x2, y2, _ = [a + b for a, b in zip(slot_origin, slot_size)]
#
#                 if not x1 + self.objective_radius < new_x < x2 - self.objective_radius \
#                         or not y1 + self.objective_radius < new_y < y2 - self.objective_radius:
#                     return False
#                 else:
#                     return True
#             # Called with move_to_well, knows slot -> keep z and check borders
#             elif slot is not None and slot == self.get_slot():
#                 slot_dict = self.slots_list[int(self.get_slot()) - 1]
#
#                 slot_origin = [a + b for a, b in zip(slot_dict["position"], self.corner_offset)]
#                 slot_size = [v for v in slot_dict["boundingBox"].values()]
#
#                 x1, y1, _ = slot_origin
#                 x2, y2, _ = [a + b for a, b in zip(slot_origin, slot_size)]
#
#                 if not x1 + self.objective_radius < new_x < x2 - self.objective_radius \
#                         or not y1 + self.objective_radius < new_y < y2 - self.objective_radius:
#                     return False
#                 else:
#                     return True
#             # Called with move_to_well, knows slot -> avoid collision and check borders
#             elif slot is not None and slot != self.get_slot():
#                 slot_dict = self.slots_list[int(slot) - 1]
#
#                 slot_origin = [a + b for a, b in zip(slot_dict["position"], self.corner_offset)]
#                 slot_size = [v for v in slot_dict["boundingBox"].values()]
#
#                 x1, y1, _ = slot_origin
#                 x2, y2, _ = [a + b for a, b in zip(slot_origin, slot_size)]
#
#                 if not x1 + self.objective_radius < new_x < x2 - self.objective_radius \
#                         or not y1 + self.objective_radius < new_y < y2 - self.objective_radius:
#                     return False
#                 else:
#                     if z > 1:
#                         self.__logger.debug("Avoiding objective collision.")
#                         self.is_moving = True
#                         self.positioner.move(axis="XYZ", dist=(0, 0, -z), is_blocking=True)
#                         self.is_moving = False
#                     return True
#             else:
#                 raise ValueError
#
#     def shiftXYoffset(self, xy_offset, x_offset=None, y_offset=None):
#         if xy_offset is not None and x_offset is None and y_offset is None:
#             x_offset = xy_offset[0]
#             y_offset = xy_offset[1]
#         else:
#             raise ValueError
#         x, y, z = self.positioner.get_position()
#         self.positioner.move(axis="XY", dist=(x_offset + x, y_offset + y))
#         # is_blocking=False)  # , speed=5, is_blocking=True, is_absolute=True)
#         self.is_moving = False
#
#     def moveToXY(self, pos_X, pos_Y):
#         x, y, z = self.positioner.get_position()
#         self.positioner.move(axis="XY", dist=(pos_X - x, pos_Y - y))
#         # is_blocking=False)  # , speed=5, is_blocking=True, is_absolute=True)
#         self.is_moving = False
#
#     def setDirections(self, directions=(1, 1, 1)):
#         if (0):
#             self.positioner.set_direction(axis=1, sign=directions[0])
#             self.positioner.set_direction(axis=2, sign=directions[1])
#             self.positioner.set_direction(axis=3, sign=directions[2])
