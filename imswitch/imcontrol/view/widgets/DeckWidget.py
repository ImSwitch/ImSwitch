import csv
from typing import Dict

from PyQt5.QtCore import Qt
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.view import guitools as guitools
from qtpy import QtCore, QtWidgets

from .basewidgets import Widget


class DeckWidget(Widget):
    """ Widget in control of the piezo movement. """
    sigStepUpClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigStepDownClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigsetSpeedClicked = QtCore.Signal(str, str)  # (positionerName, axis)

    sigHomeClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigZeroClicked = QtCore.Signal(str, str)  # (positionerName, axis)

    sigGoToClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigAddCurrentClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigAddClicked = QtCore.Signal(str, str)  # (positionerName, axis)

    sigStepAbsoluteClicked = QtCore.Signal(str)
    sigHomeAxisClicked = QtCore.Signal(str, str)
    sigStopAxisClicked = QtCore.Signal(str, str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.numPositioners = 0
        self.pars = {}
        self.main_grid_layout = QtWidgets.QGridLayout()
        self.current_slot = None
        self.current_well = None
        self.current_offset = (None, None)
        self.current_z_focus = None
        self.current_absolute_position = (None, None, None)

        self.__logger = initLogger(self, instanceName="OpentronsDeckWidget")

    # https://stackoverflow.com/questions/12608835/writing-a-qtablewidget-to-a-csv-or-xls
    # Extra blank row issue: https://stackoverflow.com/questions/3348460/csv-file-written-with-python-has-blank-lines-between-each-row
    def handleSave(self):
        path = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save File', '', 'CSV(*.csv)')
        # if not path[0] != "":
        with open(path[0], 'w', newline='') as stream:
            writer = csv.writer(stream)
            for row in range(self.scan_list.rowCount()):
                rowdata = []
                for column in range(self.scan_list.columnCount()):
                    item = self.scan_list.item(row, column)
                    if item is not None:
                        rowdata.append(
                            item.text())
                    else:
                        rowdata.append('')
                writer.writerow(rowdata)
        # else:
        #     self.__logger.debug("Empty path: handleSave")

    def handleOpen(self):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open File', '', 'CSV(*.csv)')
        # if not path.isEmpty():
        with open(path[0], 'r') as stream:
            self.scan_list.setHorizontalHeaderLabels(["Slot", "Well", "Offset", "Z_focus", "Absolute"])
            self.scan_list.setRowCount(0)
            self.scan_list_items = 0
            for rowdata in csv.reader(stream):
                self.scan_list.insertRow(self.scan_list_items)
                for column, data in enumerate(rowdata):
                    item = QtWidgets.QTableWidgetItem(data)
                    self.scan_list.setItem(self.scan_list_items, column, item)
                self.scan_list_items += 1

    def select_well(self, well):
        for well_id, btn in self.wells.items():
            if isinstance(btn, guitools.BetterPushButton):
                if well_id == well:
                    btn.setStyleSheet("background-color: green; font-size: 14px")
                else:
                    btn.setStyleSheet("background-color: grey; font-size: 14px")

    def select_labware(self, slot):
        if hasattr(self, "_wells_group_box"):
            self.main_grid_layout.removeWidget(self._wells_group_box)
        self._wells_group_box = QtWidgets.QGroupBox(f"Labware layout: {slot}: {self._labware_dict[slot]}")
        layout = QtWidgets.QGridLayout()

        labware = self._labware_dict[slot]
        # Create dictionary to hold buttons
        self.wells = {}
        # Create grid layout for wells (buttons)
        well_buttons = {}
        rows = len(self._labware_dict[slot].rows())
        columns = len(self._labware_dict[slot].columns())
        for r in list(range(rows)):
            for c in list(range(columns)):
                well_buttons[c + 1] = (0, c + 1)
                well = labware.rows()[r][c]
                well_buttons[well.well_name] = (r + 1, c + 1)
            well_buttons[well.well_name[0]] = (r + 1, 0)
        well_buttons[""] = (0, 0)
        # Create wells (buttons) and add them to the grid layout
        for corrds, pos in well_buttons.items():
            if 0 in pos:
                self.wells[corrds] = QtWidgets.QLabel(text=str(corrds))  # QtWidgets.QPushButton(corrds)
                self.wells[corrds].setFixedSize(35, 25)
                self.wells[corrds].setStyleSheet("background-color: None; font-size: 12px")
            else:
                self.wells[corrds] = guitools.BetterPushButton(corrds)  # QtWidgets.QPushButton(corrds)
                self.wells[corrds].setFixedSize(35, 25)
                self.wells[corrds].setStyleSheet("background-color: grey; font-size: 14px")
            # Set style for empty cell
            # self.wells[corrds].setStyleSheet("background-color: none")
            # Add button/label to layout
            layout.addWidget(self.wells[corrds], pos[0], pos[1])

        # Change color of selected labware
        for slot_id, btn in self.deck_slots.items():
            if isinstance(btn, guitools.BetterPushButton):
                if slot_id == slot:
                    btn.setStyleSheet("background-color: blue; font-size: 14px")
                else:
                    btn.setStyleSheet("background-color: grey; font-size: 14px")

        self._wells_group_box.setMaximumHeight(300)
        self._wells_group_box.setLayout(layout)
        self.main_grid_layout.addWidget(self._wells_group_box, 3, 0, 1, 3)
        self.setLayout(self.main_grid_layout)

    def add_home(self, layout):
        self.home = guitools.BetterPushButton(text="HOME")  # QtWidgets.QPushButton(corrds)
        self.home.setFixedSize(50, 30)
        self.home.setStyleSheet("background-color: black; font-size: 14px")
        layout.addWidget(self.home)

    def add_zero(self, layout):
        # self.zero = guitools.BetterPushButton(text="ZERO")  # QtWidgets.QPushButton(corrds)
        # TODO: implement ZERO
        self.zero = QtWidgets.QLabel(text="ZERO")  # QtWidgets.QPushButton(corrds)
        self.zero.setFixedSize(50, 30)
        # self.zero.setStyleSheet("background-color: black; font-size: 14px")
        self.zero.setStyleSheet("background-color: None; font-size: 14px")
        layout.addWidget(self.zero)

    def initialize_deck(self, deck_dict: Dict, labwares_dict: Dict):
        self._deck_dict = deck_dict
        self._labware_dict = labwares_dict

        self._deck_group_box = QtWidgets.QGroupBox("Deck layout")
        layout = QtWidgets.QHBoxLayout()

        # Add home and zero buttons
        self.add_home(layout)
        self.add_zero(layout)

        # Create dictionary to hold buttons
        slots = [slot["id"] for slot in deck_dict["locations"]["orderedSlots"]]
        used_slots = list(labwares_dict.keys())
        self.deck_slots = {}

        # Create dictionary to store deck slots names (button texts)
        slots_buttons = {s: (0, i + 2) for i, s in enumerate(slots)}
        for corrds, pos in slots_buttons.items():
            if corrds in used_slots:
                # Do button if slot contains labware
                self.deck_slots[corrds] = guitools.BetterPushButton(corrds)  # QtWidgets.QPushButton(corrds)
                self.deck_slots[corrds].setFixedSize(30, 30)
                self.deck_slots[corrds].setStyleSheet("QPushButton"
                                                      "{"
                                                      "background-color : grey; font-size: 14px"
                                                      "}"
                                                      "QPushButton::pressed"
                                                      "{"
                                                      "background-color : red; font-size: 14px"
                                                      "}"
                                                      )
            else:
                self.deck_slots[corrds] = QtWidgets.QLabel(corrds)  # QtWidgets.QPushButton(corrds)
                self.deck_slots[corrds].setFixedSize(30, 30)
                self.deck_slots[corrds].setStyleSheet("background-color: None; font-size: 14px")
            layout.addWidget(self.deck_slots[corrds])
        self._deck_group_box.setFixedHeight(70)
        self._deck_group_box.setLayout(layout)
        self.main_grid_layout.addWidget(self._deck_group_box, 2, 0, 1, 3)
        self.setLayout(self.main_grid_layout)

    def addScanner(
            self):  # , detectorName, detectorModel, detectorParameters, detectorActions,supportedBinnings, roiInfos):
        self.scan_list = TableWidgetDragRows()
        self.scan_list.setColumnCount(5)
        self.scan_list.setHorizontalHeaderLabels(["Slot", "Well", "Offset", "Z_focus", "Absolute"])
        self.scan_list_items = 0
        # self.scan_list.setEditTriggers(self.scan_list.NoEditTriggers)

        self._actions_widget = QtWidgets.QGroupBox("Actions")

        actions_layout = QtWidgets.QVBoxLayout()
        self.goto_btn = guitools.BetterPushButton('GO TO')
        self.add_current_btn = guitools.BetterPushButton('ADD CURRENT')
        self.pos_in_well_lined = QtWidgets.QLineEdit("1")
        self.add_btn = guitools.BetterPushButton('ADD')
        self.buttonOpen = guitools.BetterPushButton('Open')
        self.buttonSave = guitools.BetterPushButton('Save')

        self.buttonOpen.clicked.connect(self.handleOpen)
        self.buttonSave.clicked.connect(self.handleSave)

        actions_layout.addWidget(self.goto_btn, 0)
        actions_layout.addWidget(self.add_current_btn, 1)
        actions_layout.addWidget(QtWidgets.QLabel("#Pos. in well"), 2)
        actions_layout.addWidget(self.pos_in_well_lined, 3)
        actions_layout.addWidget(self.add_btn, 4)
        actions_layout.addWidget(self.buttonOpen, 5)
        actions_layout.addWidget(self.buttonSave, 6)
        #
        # actions_layout.addWidget(self.goto_btn, 0, 0, 2, 2)
        # actions_layout.addWidget(self.add_current_btn, 0, 2, 2, 2)
        # actions_layout.addWidget(QtWidgets.QLabel("# Positions in well"), 0, 4, 1, 1)
        # actions_layout.addWidget(self.pos_in_well_lined, 0, 5, 1, 1)
        # actions_layout.addWidget(self.add_btn, 0, 6, 1, 1)
        # actions_layout.addWidget(self.buttonOpen, 0, 7, 1, 1)
        # actions_layout.addWidget(self.buttonSave, 0, 8, 1, 1)

        self._actions_widget.setFixedHeight(200)
        self._actions_widget.setFixedWidth(140)
        self._actions_widget.setLayout(actions_layout)
        self.scan_list.setFixedHeight(200)

        self.main_grid_layout.addWidget(self.scan_list, 1, 1, 1, 2)
        self.main_grid_layout.addWidget(self._actions_widget, 1, 0, 1, 1)

    def add_position_to_scan(self, slot, well, offset, z_focus, absolute_position):

        self.scan_list.insertRow(self.scan_list_items)
        self.scan_list.setItem(self.scan_list_items, 0, QtWidgets.QTableWidgetItem(str(slot)))
        self.scan_list.setItem(self.scan_list_items, 1, QtWidgets.QTableWidgetItem(str(well)))
        self.scan_list.setItem(self.scan_list_items, 2, QtWidgets.QTableWidgetItem(str(offset)))
        self.scan_list.setItem(self.scan_list_items, 3, QtWidgets.QTableWidgetItem(str(z_focus)))
        self.scan_list.setItem(self.scan_list_items, 4, QtWidgets.QTableWidgetItem(str(absolute_position)))
        self.scan_list_items += 1

    def add_current_position_to_scan(self):
        self.scan_list.insertRow(self.scan_list_items)
        self.scan_list.setItem(self.scan_list_items, 0, QtWidgets.QTableWidgetItem(str(self.current_slot)))
        self.scan_list.setItem(self.scan_list_items, 1, QtWidgets.QTableWidgetItem(str(self.current_well)))
        self.scan_list.setItem(self.scan_list_items, 2, QtWidgets.QTableWidgetItem(str(self.current_offset)))
        self.scan_list.setItem(self.scan_list_items, 3, QtWidgets.QTableWidgetItem(str(self.current_z_focus)))
        self.scan_list.setItem(self.scan_list_items, 4, QtWidgets.QTableWidgetItem(str(self.current_absolute_position)))
        self.scan_list_items += 1

    def getAbsPosition(self, positionerName, axis):
        """ Returns the absolute position of the  specified positioner axis in
        micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['AbsolutePosEdit' + parNameSuffix].text())

    def addPositioner(self, positionerName, axes, hasSpeed, hasHome=True, hasStop=True):
        self._positioner_widget = QtWidgets.QGroupBox("Positioners")
        layout = QtWidgets.QGridLayout()
        for i in range(len(axes)):
            axis = axes[i]
            parNameSuffix = self._getParNameSuffix(positionerName, axis)
            label = f'{positionerName} -- {axis}' if positionerName != axis else positionerName

            self.pars['Label' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{label}</strong>')
            self.pars['Label' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['Position' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{0:.2f} µm</strong>')
            self.pars['Position' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['UpButton' + parNameSuffix] = guitools.BetterPushButton('+')
            self.pars['DownButton' + parNameSuffix] = guitools.BetterPushButton('-')
            self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('1000')

            self.pars['AbsolutePosEdit' + parNameSuffix] = QtWidgets.QLineEdit('0')
            self.pars['AbsolutePosButton' + parNameSuffix] = guitools.BetterPushButton('Go!')

            layout.addWidget(self.pars['Label' + parNameSuffix], self.numPositioners, 0)
            layout.addWidget(self.pars['Position' + parNameSuffix], self.numPositioners, 1)
            layout.addWidget(self.pars['UpButton' + parNameSuffix], self.numPositioners, 2)
            layout.addWidget(self.pars['DownButton' + parNameSuffix], self.numPositioners, 3)
            layout.addWidget(QtWidgets.QLabel('Rel'), self.numPositioners, 4)
            layout.addWidget(self.pars['StepEdit' + parNameSuffix], self.numPositioners, 5)
            layout.addWidget(QtWidgets.QLabel('Abs'), self.numPositioners, 6)

            layout.addWidget(self.pars['AbsolutePosEdit' + parNameSuffix], self.numPositioners, 7)
            layout.addWidget(self.pars['AbsolutePosButton' + parNameSuffix], self.numPositioners, 8)

            if hasSpeed:
                self.pars['Speed' + parNameSuffix] = QtWidgets.QLabel('Speed:')
                self.pars['Speed' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
                self.pars['SpeedEdit' + parNameSuffix] = QtWidgets.QLineEdit('1000')

                layout.addWidget(self.pars['Speed' + parNameSuffix], self.numPositioners, 9)
                layout.addWidget(self.pars['SpeedEdit' + parNameSuffix], self.numPositioners, 10)

            if hasHome:
                self.pars['Home' + parNameSuffix] = guitools.BetterPushButton('Home ' + parNameSuffix)
                layout.addWidget(self.pars['Home' + parNameSuffix], self.numPositioners, 11)

                self.pars['Home' + parNameSuffix].clicked.connect(
                    lambda *args, axis=axis: self.sigHomeAxisClicked.emit(positionerName, axis)
                )

            if hasStop:
                self.pars['Stop' + parNameSuffix] = guitools.BetterPushButton('Stop ' + parNameSuffix)
                layout.addWidget(self.pars['Stop' + parNameSuffix], self.numPositioners, 12)

                self.pars['Stop' + parNameSuffix].clicked.connect(
                    lambda *args, axis=axis: self.sigStopAxisClicked.emit(positionerName, axis)
                )

            # Connect signals
            self.pars['UpButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            )
            self.pars['DownButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepDownClicked.emit(positionerName, axis)
            )
            self.pars['AbsolutePosButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepAbsoluteClicked.emit(axis)
            )

            self.numPositioners += 1

        self._positioner_widget.setFixedHeight(120)
        self._positioner_widget.setLayout(layout)
        self.main_grid_layout.addWidget(self._positioner_widget, 0, 0, 1, 3)

    @property
    def current_slot(self):
        return self._current_slot

    @current_slot.setter
    def current_slot(self, current_slot):
        self._current_slot = current_slot

    @property
    def current_well(self):
        return self._current_well

    @current_well.setter
    def current_well(self, current_well):
        self._current_well = current_well

    @property
    def current_offset(self):
        return self._current_offset

    @current_offset.setter
    def current_offset(self, current_offset):
        self._current_offset = current_offset

    @property
    def current_z_focus(self):
        return self._current_z_focus

    @current_z_focus.setter
    def current_z_focus(self, current_z_focus):
        self._current_z_focus = current_z_focus

    @property
    def current_absolute_position(self):
        return self._current_absolute_position

    @current_absolute_position.setter
    def current_absolute_position(self, current_absolute_position):
        self._current_absolute_position = current_absolute_position

    @property
    def positions_in_well(self):
        try:
            if int(self.pos_in_well_lined.text()) > 4:
                return 4
            else:
                return int(self.pos_in_well_lined.text())
        except ValueError:
            return 1

    def getStepSize(self, positionerName, axis):
        """ Returns the step size of the specified positioner axis in
        milimeters. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['StepEdit' + parNameSuffix].text())

    def setStepSize(self, positionerName, axis, stepSize):
        """ Sets the step size of the specified positioner axis to the
        specified number of milimeters. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['StepEdit' + parNameSuffix].setText(stepSize)

    def getSpeed(self, positionerName, axis):
        """ Returns the step size of the specified positioner axis in
        milimeters. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['SpeedEdit' + parNameSuffix].text())

    def setSpeedSize(self, positionerName, axis, speedSize):
        """ Sets the step size of the specified positioner axis to the
        specified number of micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['SpeedEdit' + parNameSuffix].setText(speedSize)

    def updatePosition(self, positionerName, axis, position):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['Position' + parNameSuffix].setText(f'<strong>{position:.2f} mm</strong>')

    def updateSpeed(self, positionerName, axis, speed):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['Speed' + parNameSuffix].setText(f'<strong>{speed:.2f} mm/s</strong>')

    def _getParNameSuffix(self, positionerName, axis):
        return f'{positionerName}--{axis}'


# From https://stackoverflow.com/questions/26227885/drag-and-drop-rows-within-qtablewidget
class TableWidgetDragRows(QtWidgets.QTableWidget):
    sigGoToTableClicked = QtCore.Signal(tuple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)


    def contextMenuEvent(self, event):
        if self.selectionModel().selection().indexes():
            for i in self.selectionModel().selection().indexes():
                row, column = i.row(), i.column()
            menu = QtWidgets.QMenu()
            goto_action = menu.addAction("Go To")
            delete_action = menu.addAction("Delete")

            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == goto_action:
                self.gotoAction(row)
                print(f"{row}, {column}")
            elif action == delete_action:
                self.deleteSelected(row)

    def gotoAction(self, row):
        # TODO: avoid hardcoded 4: Absolute
        if self.item(row, 4) is not None:
            absolute_position = tuple(map(float, self.item(row, 4).text().strip('()').split(',')))
        print(f"Go to position {absolute_position}")
        self.sigGoToTableClicked.emit(absolute_position)

    def deleteSelected(self, row):
        self.removeRow(row)
        print(f"Deleted row {row}")

    def dropEvent(self, event):
        if not event.isAccepted() and event.source() == self:
            drop_row = self.drop_on(event)

            rows = sorted(set(item.row() for item in self.selectedItems()))

            rows_to_move = []
            for row_index in rows:
                items = dict()
                for column_index in range(self.columnCount()):
                    # get the widget or item of current cell
                    widget = self.cellWidget(row_index, column_index)
                    if isinstance(widget, type(None)):
                        # if widget is NoneType, it is a QTableWidgetItem
                        items[column_index] = {"kind": "QTableWidgetItem",
                                               "item": QtWidgets.QTableWidgetItem(self.item(row_index, column_index))}
                    else:
                        # otherwise it is any other kind of widget. So we catch the widgets unique (hopefully) objectname
                        items[column_index] = {"kind": "QWidget",
                                               "item": widget.objectName()}

                rows_to_move.append(items)

            for row_index in reversed(rows):
                self.removeRow(row_index)
                if row_index < drop_row:
                    drop_row -= 1

            for row_index, data in enumerate(rows_to_move):
                row_index += drop_row
                self.insertRow(row_index)

                for column_index, column_data in data.items():
                    if column_data["kind"] == "QTableWidgetItem":
                        # for QTableWidgetItem we can re-create the item directly
                        self.setItem(row_index, column_index, column_data["item"])
                    else:
                        # for others we call the parents callback function to get the widget
                        _widget = self._parent.get_table_widget(column_data["item"])
                        if _widget is not None:
                            self.setCellWidget(row_index, column_index, _widget)

            event.accept()

        super().dropEvent(event)

    def drop_on(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return self.rowCount()

        return index.row() + 1 if self.is_below(event.pos(), index) else index.row()

    def is_below(self, pos, index):
        rect = self.visualRect(index)
        margin = 2
        if pos.y() - rect.top() < margin:
            return False
        elif rect.bottom() - pos.y() < margin:
            return True
        # noinspection PyTypeChecker
        return rect.contains(pos, True) and not (
                int(self.model().flags(index)) & Qt.ItemIsDropEnabled) and pos.y() >= rect.center().y()

    def addColumn(self, name):
        newColumn = self.columnCount()
        self.beginInsertColumns(Qt.QModelIndex(), newColumn, newColumn)
        self.headerdata.append(name)
        for row in self.arraydata:
            row.append('')
        self.endInsertColumns()

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
