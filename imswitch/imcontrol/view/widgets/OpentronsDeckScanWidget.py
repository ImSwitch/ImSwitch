import os
import time

from qtpy import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QLine

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.view.widgets.StandaPositionerWidget import StandaPositionerWidget

class OpentronsDeckScanWidget(Widget):
    """ Widget in control of the piezo movement. """
    sigStepUpClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigStepDownClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigsetSpeedClicked = QtCore.Signal(str, str)  # (positionerName, axis)

    sigHomeClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigZeroClicked = QtCore.Signal(str, str)  # (positionerName, axis)

    sigGoToClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigAddCurrentClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigAddClicked = QtCore.Signal(str, str)  # (positionerName, axis)

    sigPresetSelected = QtCore.Signal(str)  # (presetName)
    sigLoadPresetClicked = QtCore.Signal()
    sigSavePresetClicked = QtCore.Signal()
    sigSavePresetAsClicked = QtCore.Signal()
    sigDeletePresetClicked = QtCore.Signal()
    sigPresetScanDefaultToggled = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.numPositioners = 0
        self.pars = {}
        self.main_grid_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_grid_layout)
        self.current_slot = None
        self.current_well = None
        self.current_offset = (None,None)

        # Presets box
        self.presetsBox = QtWidgets.QHBoxLayout()
        self.presetsLabel = QtWidgets.QLabel('Presets: ')
        self.presetsList = QtWidgets.QComboBox()
        self.presetsList.currentIndexChanged.connect(
            lambda i: self.sigPresetSelected.emit(self.presetsList.itemData(i))
        )
        self.loadPresetButton = guitools.BetterPushButton('Load selected')
        self.loadPresetButton.clicked.connect(self.sigLoadPresetClicked)
        self.savePresetButton = guitools.BetterPushButton('Save to selected')
        self.savePresetButton.clicked.connect(self.sigSavePresetClicked)
        self.savePresetAsButton = guitools.BetterPushButton('Save as…')
        self.savePresetAsButton.clicked.connect(self.sigSavePresetAsClicked)
        self.moreButton = QtWidgets.QToolButton()
        self.moreButton.setText('More…')
        self.moreButton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.deletePresetAction = QtWidgets.QAction('Delete selected')
        self.deletePresetAction.triggered.connect(self.sigDeletePresetClicked)
        self.moreButton.addAction(self.deletePresetAction)
        self.presetScanDefaultAction = QtWidgets.QAction('Make selected default for scanning')
        self.presetScanDefaultAction.triggered.connect(self.sigPresetScanDefaultToggled)
        self.moreButton.addAction(self.presetScanDefaultAction)

        self.setCurrentPreset(None)
        self.setScanDefaultPresetActive(False)

        self.presetsBox.addWidget(self.presetsLabel)
        self.presetsBox.addWidget(self.presetsList, 1)
        self.presetsBox.addWidget(self.loadPresetButton)
        self.presetsBox.addWidget(self.savePresetButton)
        self.presetsBox.addWidget(self.savePresetAsButton)
        self.presetsBox.addWidget(self.moreButton)

        self.main_grid_layout.addLayout(self.presetsBox)


        # Folder and filename fields -> from RecordingWidget
        baseOutputFolder = self._options.recording.outputFolder
        if self._options.recording.includeDateInOutputFolder:
            self.initialDir = os.path.join(baseOutputFolder, time.strftime('%Y-%m-%d'))
        else:
            self.initialDir = baseOutputFolder

        self.folderEdit = QtWidgets.QLineEdit(self.initialDir)
        self.openFolderButton = guitools.BetterPushButton('Open')
        self.specifyfile = QtWidgets.QCheckBox('Specify file name')
        self.filenameEdit = QtWidgets.QLineEdit('Current time')
        self.filenameEdit.setEnabled(False)


        self.__logger = initLogger(self, instanceName="OpentronsDeckScanWidget")


    def getCurrentPreset(self):
        """ Returns the name of the currently selected preset. """
        return self.presetsList.currentData()

    def setCurrentPreset(self, name):
        """ Sets the selected preset in the preset list. Pass None to unselect
        all presets. """
        anyPresetSelected = True if name else False

        if anyPresetSelected:
            nameIndex = self.presetsList.findData(name)
            if nameIndex > -1:
                self.presetsList.setCurrentIndex(nameIndex)
        else:
            self.presetsList.setCurrentIndex(-1)

        self.loadPresetButton.setEnabled(anyPresetSelected)
        self.savePresetButton.setEnabled(anyPresetSelected)
        self.deletePresetAction.setEnabled(anyPresetSelected)
        self.presetScanDefaultAction.setEnabled(anyPresetSelected)
        if not anyPresetSelected:
            self.presetScanDefaultAction.setChecked(False)

    def setScanDefaultPreset(self, name):
        """ Sets which preset that is default for scanning. Pass None if there
        is no default. """
        for i in range(self.presetsList.count()):
            self.presetsList.setItemText(i, self.presetsList.itemData(i))

        nameIndex = self.presetsList.findData(name)
        if nameIndex > -1:
            self.presetsList.setItemText(nameIndex, f'{name} [scan default]')

    def setScanDefaultPresetActive(self, active):
        """ Sets whether the preset that is default for scanning is active. """
        self.presetScanDefaultAction.setText(
            'Make selected default for scanning' if not active else 'Unset default for scanning'
        )

    def addPreset(self, name):
        """ Adds a preset to the preset list. """
        self.presetsList.addItem(name, name)
        self.presetsList.model().sort(0)

    def removePreset(self, name):
        """ Removes a preset from the preset list. """
        nameIndex = self.presetsList.findData(name)
        if nameIndex > -1:
            self.presetsList.removeItem(nameIndex)

    def select_well(self, well):
        for well_id, btn in self.wells.items():
            if isinstance(btn, guitools.BetterPushButton):
                if well_id == well:
                    btn.setStyleSheet("background-color: green; font-size: 14px")
                else:
                    btn.setStyleSheet("background-color: grey; font-size: 14px")



    def select_labware(self, slot):
        if hasattr(self,"_wells_group_box"):
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
                well_buttons[c+1] = (0, c+1)
                well = labware.rows()[r][c]
                well_buttons[well.well_name] = (r+1,c+1)
            well_buttons[well.well_name[0]] = (r+1, 0)
        well_buttons[""] = (0,0)
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

        self._wells_group_box.setLayout(layout)
        self.main_grid_layout.addWidget(self._wells_group_box)
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

    def initialize_opentrons_deck(self, deck_dict, labwares_dict):
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
        slots_buttons = {s: (0,i+2) for i,s in enumerate(slots)}
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

        self._deck_group_box.setLayout(layout)
        self.main_grid_layout.addWidget(self._deck_group_box)
        self.setLayout(self.main_grid_layout)

    def addScanner(self): #, detectorName, detectorModel, detectorParameters, detectorActions,supportedBinnings, roiInfos):
        self._scanner_widget = QtWidgets.QGroupBox("Scan list")
        main_layout = QtWidgets.QGridLayout()

        self.scan_list = QtWidgets.QTableWidget()
        self.scan_list.setColumnCount(3)
        self.scan_list.setHorizontalHeaderLabels(["Slot/Labware", "Well", "Offset"])
        self.scan_list_items = 0
        self.scan_list.setEditTriggers(self.scan_list.NoEditTriggers)

        self._actions_widget = QtWidgets.QGroupBox("Actions")

        actions_layout = QtWidgets.QGridLayout()
        self.goto_btn = guitools.BetterPushButton('GO TO')
        self.add_current_btn = guitools.BetterPushButton('ADD CURRENT')
        self.pos_in_well_lined = QtWidgets.QLineEdit("1")
        self.add_btn = guitools.BetterPushButton('ADD')

        actions_layout.addWidget(self.goto_btn, 0, 0, 2, 2)
        actions_layout.addWidget(self.add_current_btn, 0, 2, 2, 2)
        actions_layout.addWidget(QtWidgets.QLabel("# Positions in well"), 0, 4, 1, 1)
        actions_layout.addWidget(self.pos_in_well_lined, 0, 5, 1, 1)
        actions_layout.addWidget(self.add_btn, 0, 6, 1, 1)

        self._actions_widget.setLayout(actions_layout)


        main_layout.addWidget(self.scan_list)
        main_layout.addWidget(self._actions_widget)
        self._scanner_widget.setLayout(main_layout)
        self.main_grid_layout.addWidget(self._scanner_widget)

    def add_position_to_scan(self, slot, well, offset):

        self.scan_list.insertRow(self.scan_list_items)
        self.scan_list.setItem(self.scan_list_items, 0, QtWidgets.QTableWidgetItem(str(slot)))
        self.scan_list.setItem(self.scan_list_items, 1, QtWidgets.QTableWidgetItem(str(well)))
        self.scan_list.setItem(self.scan_list_items, 2, QtWidgets.QTableWidgetItem(str(offset)))

        self.scan_list_items += 1

    def add_current_position_to_scan(self):
        self.scan_list.insertRow(self.scan_list_items)
        self.scan_list.setItem(self.scan_list_items, 0, QtWidgets.QTableWidgetItem(str(self.current_slot)))
        self.scan_list.setItem(self.scan_list_items, 1, QtWidgets.QTableWidgetItem(str(self.current_well)))
        self.scan_list.setItem(self.scan_list_items, 2, QtWidgets.QTableWidgetItem(str(self.current_offset)))
        self.scan_list_items += 1

    def addPositioner(self, positionerName, axes, hasSpeed, initial_position, initial_speed ):
        self._positioner_widget = QtWidgets.QGroupBox("Positioners")
        layout = QtWidgets.QGridLayout()
        for i in range(len(axes)):
            axis = axes[i]
            parNameSuffix = self._getParNameSuffix(positionerName, axis)
            label = f'{axis}' if positionerName != axis else positionerName

            self.pars['Label' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{label}</strong>')
            self.pars['Label' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['Position' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{initial_position[axis]:.3f} mm</strong>')
            self.pars['Position' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['UpButton' + parNameSuffix] = guitools.BetterPushButton('+')
            self.pars['DownButton' + parNameSuffix] = guitools.BetterPushButton('-')
            self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('0')
            self.pars['StepUnit' + parNameSuffix] = QtWidgets.QLabel('mm')

            layout.addWidget(self.pars['Label' + parNameSuffix], self.numPositioners, 0)
            layout.addWidget(self.pars['Position' + parNameSuffix], self.numPositioners, 1)
            layout.addWidget(self.pars['UpButton' + parNameSuffix], self.numPositioners, 2)
            layout.addWidget(self.pars['DownButton' + parNameSuffix], self.numPositioners, 3)
            layout.addWidget(QtWidgets.QLabel('Step'), self.numPositioners, 4)
            layout.addWidget(self.pars['StepEdit' + parNameSuffix], self.numPositioners, 5)
            layout.addWidget(self.pars['StepUnit' + parNameSuffix], self.numPositioners, 6)

            # Connect signals
            self.pars['UpButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            )
            self.pars['DownButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepDownClicked.emit(positionerName, axis)
            )

            if hasSpeed:
                self.pars['Speed' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{initial_speed[axis]:.2f} mm/s</strong>')
                self.pars['Speed' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
                self.pars['ButtonSpeedEnter' + parNameSuffix] = guitools.BetterPushButton('Set')
                self.pars['SpeedEdit' + parNameSuffix] = QtWidgets.QLineEdit(f'{initial_speed[axis]}')
                self.pars['SpeedUnit' + parNameSuffix] = QtWidgets.QLabel('mm/s')
                layout.addWidget(self.pars['SpeedEdit' + parNameSuffix], self.numPositioners, 10)
                layout.addWidget(self.pars['SpeedUnit' + parNameSuffix], self.numPositioners, 11)
                layout.addWidget(self.pars['ButtonSpeedEnter' + parNameSuffix], self.numPositioners, 12)
                layout.addWidget(self.pars['Speed' + parNameSuffix], self.numPositioners, 7)


                self.pars['ButtonSpeedEnter'+ parNameSuffix].clicked.connect(
                    lambda *args, axis=axis: self.sigsetSpeedClicked.emit(positionerName, axis)
                )

            self.numPositioners += 1
        self._positioner_widget.setLayout(layout)
        self.main_grid_layout.addWidget(self._positioner_widget)

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
    def positions_in_well(self):
        return int(self.pos_in_well_lined.text())

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
