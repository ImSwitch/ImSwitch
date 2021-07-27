from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget

from imswitch.imcommon.model import shortcut

import time

class LaserWidget(Widget):
    """ Laser widget for setting laser powers etc. """

    sigEnableChanged = QtCore.Signal(str, bool)  # (laserName, enabled)
    sigValueChanged = QtCore.Signal(str, float)  # (laserName, value)

    sigPresetSelected = QtCore.Signal(str)  # (presetName)
    sigLoadPresetClicked = QtCore.Signal()
    sigSavePresetClicked = QtCore.Signal()
    sigDeletePresetClicked = QtCore.Signal()
    sigPresetScanDefaultToggled = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.laserModules = {}

        self.setMinimumHeight(320)

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        # Lasers grid
        self.lasersGrid = QtWidgets.QGridLayout()
        self.lasersGrid.setContentsMargins(4, 4, 4, 4)

        self.lasersGridContainer = QtWidgets.QWidget()
        self.lasersGridContainer.setLayout(self.lasersGrid)

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidget(self.lasersGridContainer)
        self.scrollArea.setWidgetResizable(True)
        self.lasersGridContainer.installEventFilter(self)

        self.layout.addWidget(self.scrollArea, 0, 0)

        # Presets box
        self.presetsBox = QtWidgets.QHBoxLayout()
        self.presetsLabel = QtWidgets.QLabel('Presets: ')
        self.presetsList = QtWidgets.QComboBox()
        self.presetsList.currentIndexChanged.connect(
            lambda i: self.sigPresetSelected.emit(self.presetsList.itemData(i))
        )
        self.loadPresetButton = guitools.BetterPushButton('Load selected')
        self.loadPresetButton.clicked.connect(self.sigLoadPresetClicked)
        self.savePresetButton = guitools.BetterPushButton('Save values…')
        self.savePresetButton.clicked.connect(self.sigSavePresetClicked)
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
        self.presetsBox.addWidget(self.moreButton)

        self.layout.addLayout(self.presetsBox, 1, 0)

    def addLaser(self, laserName, valueUnits, valueDecimals, wavelength, valueRange=None,
                 valueRangeStep=1):
        """ Adds a laser module widget. valueRange is either a tuple
        (min, max), or None (if the laser can only be turned on/off). """

        control = LaserModule(
            valueUnits=valueUnits, valueDecimals=valueDecimals, valueRange=valueRange,
            tickInterval=5, singleStep=valueRangeStep,
            initialPower=valueRange[0] if valueRange is not None else 0
        )
        control.sigEnableChanged.connect(
            lambda enabled: self.sigEnableChanged.emit(laserName, enabled)
        )
        control.sigValueChanged.connect(
            lambda value: self.sigValueChanged.emit(laserName, value)
        )

        nameLabel = QtWidgets.QLabel(laserName)
        color = guitools.colorutils.wavelengthToHex(wavelength)
        nameLabel.setStyleSheet(
            f'font-size: 16px; font-weight: bold; padding: 0 6px 0 12px;'
            f'border-left: 4px solid {color}'
        )

        self.lasersGrid.addWidget(nameLabel, len(self.laserModules), 0)
        self.lasersGrid.addWidget(control, len(self.laserModules), 1)
        self.laserModules[laserName] = control

    def isLaserActive(self, laserName):
        """ Returns whether the specified laser is powered on. """
        return self.laserModules[laserName].isActive()

    def getValue(self, laserName):
        """ Returns the value of the specified laser, in the units that the
        laser uses. """
        return self.laserModules[laserName].getValue()

    def setEditable(self, editable):
        """ Sets whether the widget can be interacted with. """
        self.setEnabled(editable)

    def setLaserActive(self, laserName, active):
        """ Sets whether the specified laser is powered on. """
        self.laserModules[laserName].setActive(active)

    def setLaserActivatable(self, laserName, activatable):
        """ Sets whether the specified laser can be (de)activated by the user.
        """
        self.laserModules[laserName].setActivatable(activatable)

    def setLaserEditable(self, laserName, editable):
        """ Sets whether the specified laser's values can be edited by the
        user. """
        self.laserModules[laserName].setEditable(editable)

    def setValue(self, laserName, value):
        """ Sets the value of the specified laser, in the units that the laser
        uses. """
        self.laserModules[laserName].setValue(value)

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

    def eventFilter(self, source, event):
        if source is self.lasersGridContainer and event.type() == QtCore.QEvent.Resize:
            # Set correct minimum width (otherwise things can go outside the widget because of the
            # scroll area)
            width = self.lasersGridContainer.minimumSizeHint().width()\
                     + self.scrollArea.verticalScrollBar().width()
            self.scrollArea.setMinimumWidth(width)
            self.setMinimumWidth(width)

        return False


class LaserModule(QtWidgets.QWidget):
    """ Module from LaserWidget to handle a single laser. """

    sigEnableChanged = QtCore.Signal(bool)  # (enabled)
    sigValueChanged = QtCore.Signal(float)  # (value)

    def __init__(self, valueUnits, valueDecimals, valueRange, tickInterval, singleStep,
                 initialPower, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.valueDecimals = valueDecimals

        isBinary = valueRange is None

        # Graphical elements
        self.setPointLabel = QtWidgets.QLabel('Setpoint')
        self.setPointLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.setPointEdit = QtWidgets.QLineEdit(str(initialPower))
        self.setPointEdit.setFixedWidth(50)
        self.setPointEdit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.minpower = QtWidgets.QLabel()
        self.minpower.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.maxpower = QtWidgets.QLabel()
        self.maxpower.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.slider = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                           decimals=valueDecimals)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)

        if not isBinary:
            valueRangeMin, valueRangeMax = valueRange

            self.minpower.setText(str(valueRangeMin))
            self.maxpower.setText(str(valueRangeMax))

            self.slider.setMinimum(valueRangeMin)
            self.slider.setMaximum(valueRangeMax)
            self.slider.setTickInterval(tickInterval)
            self.slider.setSingleStep(singleStep)
            self.slider.setValue(0)

        powerFrame = QtWidgets.QFrame(self)
        self.powerGrid = QtWidgets.QGridLayout()
        powerFrame.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Plain)
        powerFrame.setLayout(self.powerGrid)

        self.powerGrid.addWidget(self.setPointLabel, 0, 0, 1, 2)
        self.powerGrid.addWidget(self.setPointEdit, 1, 0)
        self.powerGrid.addWidget(QtWidgets.QLabel(valueUnits), 1, 1)
        self.powerGrid.addWidget(self.minpower, 0, 2, 2, 1)
        self.powerGrid.addWidget(self.slider, 0, 3, 2, 4)
        self.powerGrid.addWidget(self.maxpower, 0, 8, 2, 1)

        self.enableButton = guitools.BetterPushButton('ON')
        self.enableButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.enableButton.setCheckable(True)
        self.enableButton.setEnabled(False)

        # Add elements to QHBoxLayout
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.layout.addWidget(powerFrame)
        if isBinary:
            sizePolicy = powerFrame.sizePolicy()
            sizePolicy.setRetainSizeWhenHidden(True)
            powerFrame.setSizePolicy(sizePolicy)
            powerFrame.hide()
        self.layout.addWidget(self.enableButton)

        # Connect signals
        self.enableButton.toggled.connect(self.sigEnableChanged)
        self.slider.valueChanged.connect(
            lambda value: self.sigValueChanged.emit(value)
        )
        self.setPointEdit.returnPressed.connect(
            lambda: self.sigValueChanged.emit(self.getValue())
        )

    def isActive(self):
        """ Returns whether the laser is powered on. """
        return self.enableButton.isChecked()

    def getValue(self):
        """ Returns the value of the laser, in the units that the laser
        uses. """
        return float(self.setPointEdit.text())

    def setActive(self, active):
        """ Sets whether the laser is powered on. """
        self.enableButton.setChecked(active)

    def setActivatable(self, activatable):
        """ Sets whether the laser can be (de)activated by the user. """
        self.enableButton.setEnabled(activatable)

    def setEditable(self, editable):
        """ Sets whether the laser's values can be edited by the user. """
        self.setPointEdit.setEnabled(editable)
        self.slider.setEnabled(editable)
        self.enableButton.setEnabled(editable)

    def setValue(self, value):
        """ Sets the value of the laser, in the units that the laser uses. """
        self.setPointEdit.setText(f'%.{self.valueDecimals}f' % value)
        self.slider.setValue(value)


# Copyright (C) 2017 Federico Barabas 2020, 2021 TestaLab
# This file is part of Tormenta and ImSwitch.
#
# Tormenta and ImSwitch are free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tormenta and Imswitch are distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

