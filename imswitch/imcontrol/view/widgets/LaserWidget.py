from qtpy import QtCore, QtWidgets

from imswitch.imcommon.view.guitools import colorutils
from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class LaserWidget(Widget):
    """ Laser widget for setting laser powers etc. """

    sigEnableChanged = QtCore.Signal(str, bool)  # (laserName, enabled)
    sigValueChanged = QtCore.Signal(str, float)  # (laserName, value)
    
    sigModEnabledChanged = QtCore.Signal(str, bool) # (laserName, modulationEnabled)
    sigFreqChanged = QtCore.Signal(str, int)        # (laserName, frequency)
    sigDutyCycleChanged = QtCore.Signal(str, int)   # (laserName, dutyCycle)

    sigPresetSelected = QtCore.Signal(str)  # (presetName)
    sigLoadPresetClicked = QtCore.Signal()
    sigSavePresetClicked = QtCore.Signal()
    sigSavePresetAsClicked = QtCore.Signal()
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

        self.layout.addLayout(self.presetsBox, 1, 0)

    def addLaser(self, laserName, valueUnits, valueDecimals, wavelength, valueRange=None,
                 valueRangeStep=1, frequencyRange=None):
        """ Adds a laser module widget. valueRange is either a tuple
        (min, max), or None (if the laser can only be turned on/off).
        frequencyRange is either a tuple (min, max, initVal)
        or None (if the laser is not modulated in frequency)"""

        control = LaserModule(
            valueUnits=valueUnits, valueDecimals=valueDecimals, valueRange=valueRange,
            tickInterval=5, singleStep=valueRangeStep,
            initialPower=valueRange[0] if valueRange is not None else 0,
            frequencyRange=frequencyRange
        )
        control.sigEnableChanged.connect(
            lambda enabled: self.sigEnableChanged.emit(laserName, enabled)
        )
        control.sigValueChanged.connect(
            lambda value: self.sigValueChanged.emit(laserName, value)
        )

        if frequencyRange is not None:
            control.sigModEnabledChanged.connect(
                lambda enabled: self.sigModEnabledChanged.emit(laserName, enabled)
            )
            control.sigFreqChanged.connect(
                lambda frequency: self.sigFreqChanged.emit(laserName, frequency)
            )
            control.sigDutyCycleChanged.connect(
                lambda dutyCycle: self.sigDutyCycleChanged.emit(laserName, dutyCycle)
            )

        nameLabel = QtWidgets.QLabel(laserName)
        color = colorutils.wavelengthToHex(wavelength)
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
    
    def setModulationFrequency(self, laserName, value):
        """ Sets the modulation frequency of the specified laser. """
        self.laserModules[laserName].setModulationFrequency(value)

    def setModulationDutyCycle(self, laserName, value):
        """ Sets the modulation duty cycle of the specified laser. """
        self.laserModules[laserName].setModulationDutyCycle(value)

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

    def eventFilter(self, source, event):
        if source is self.lasersGridContainer and event.type() == QtCore.QEvent.Resize:
            # Set correct minimum width (otherwise things can go outside the widget because of the
            # scroll area)
            width = self.lasersGridContainer.minimumSizeHint().width() \
                    + self.scrollArea.verticalScrollBar().width()
            self.scrollArea.setMinimumWidth(width)
            self.setMinimumWidth(width)

        return False


class LaserModule(QtWidgets.QWidget):
    """ Module from LaserWidget to handle a single laser. """

    sigEnableChanged = QtCore.Signal(bool)  # (enabled)
    sigValueChanged = QtCore.Signal(float)  # (value)

    sigModEnabledChanged = QtCore.Signal(bool) # (modulation enabled)
    sigFreqChanged = QtCore.Signal(int)        # (frequency)
    sigDutyCycleChanged = QtCore.Signal(int)   # (duty cycle)

    def __init__(self, valueUnits, valueDecimals, valueRange, tickInterval, singleStep,
                 initialPower, frequencyRange, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.valueDecimals = valueDecimals

        isBinary = valueRange is None
        isModulated = frequencyRange is not None

        # Graphical elements
        self.setPointLabel = QtWidgets.QLabel(f'Setpoint [{valueUnits}]')
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

        self.powerGrid.addWidget(self.setPointLabel, 0, 0, 2, 1)
        self.powerGrid.addWidget(self.setPointEdit, 0, 1, 2, 1)
        self.powerGrid.addWidget(self.minpower, 0, 2, 2, 1)
        self.powerGrid.addWidget(self.slider, 0, 3, 2, 1)
        self.powerGrid.addWidget(self.maxpower, 0, 4, 2, 1)
        
        if isModulated:
            freqRangeMin, freqRangeMax, initialFrequency = frequencyRange
            # laser modulation widgets
            # enable button
            self.modulationEnable = guitools.BetterPushButton("ON")
            self.modulationEnable.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Expanding)
            self.modulationEnable.setCheckable(True)

            # frequency slider
            self.modulationFrequencyLabel = QtWidgets.QLabel("Frequency [Hz]")
            self.modulationFrequencyLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.modulationFrequencyEdit = QtWidgets.QLineEdit(str(initialFrequency))
            self.modulationFrequencyEdit.setFixedWidth(50)
            self.modulationFrequencyEdit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.modulationFrequencyMinLabel = QtWidgets.QLabel(str(freqRangeMin))
            self.modulationFrequencyMaxLabel = QtWidgets.QLabel(str(freqRangeMax))
            self.modulationFrequencySlider = guitools.BetterSlider(QtCore.Qt.Horizontal)
            self.modulationFrequencySlider.setRange(freqRangeMin, freqRangeMax)
            self.modulationFrequencySlider.setValue(initialFrequency)

            # duty cycle slider
            self.modulationDutyCycleLabel = QtWidgets.QLabel("Duty cycle [%]")
            self.modulationDutyCycleLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.modulationDutyCycleEdit = QtWidgets.QLineEdit(str(50))
            self.modulationDutyCycleEdit.setFixedWidth(50)
            self.modulationDutyCycleEdit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.modulationDutyCycleMinLabel = QtWidgets.QLabel(str(1))
            self.modulationDutyCycleMaxLabel = QtWidgets.QLabel(str(99))
            self.modulationDutyCycleMinLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.modulationDutyCycleMaxLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.modulationDutyCycleSlider = guitools.BetterSlider(QtCore.Qt.Horizontal)
            self.modulationDutyCycleSlider.setRange(1, 99)
            self.modulationDutyCycleSlider.setValue(50)

            self.modulationGroup = QtWidgets.QGroupBox("Frequency modulation")
            self.modulationLayout = QtWidgets.QGridLayout()

            self.modulationLayout.addWidget(self.modulationFrequencyLabel, 0, 0)
            self.modulationLayout.addWidget(self.modulationFrequencyEdit, 0, 1)
            self.modulationLayout.addWidget(self.modulationFrequencyMinLabel, 0, 2)
            self.modulationLayout.addWidget(self.modulationFrequencySlider, 0, 3)
            self.modulationLayout.addWidget(self.modulationFrequencyMaxLabel, 0, 4)

            self.modulationLayout.addWidget(self.modulationDutyCycleLabel, 1, 0)
            self.modulationLayout.addWidget(self.modulationDutyCycleEdit, 1, 1)
            self.modulationLayout.addWidget(self.modulationDutyCycleMinLabel, 1, 2)
            self.modulationLayout.addWidget(self.modulationDutyCycleSlider, 1, 3)
            self.modulationLayout.addWidget(self.modulationDutyCycleMaxLabel, 1, 4)
            self.modulationLayout.addWidget(self.modulationEnable, 0, 5, 2, 1)
            self.modulationGroup.setLayout(self.modulationLayout)

            self.powerGrid.addWidget(self.modulationGroup, 2, 0, 1, 5)
                
        self.enableButton = guitools.BetterPushButton('ON')
        self.enableButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                        QtWidgets.QSizePolicy.Expanding)
        self.enableButton.setCheckable(True)

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

        if isModulated:
            self.modulationEnable.toggled.connect(self.sigModEnabledChanged)
            self.modulationFrequencySlider.valueChanged.connect(
                lambda value: self.sigFreqChanged.emit(value)
            )
            self.modulationFrequencyEdit.returnPressed.connect(
                lambda: self.sigFreqChanged.emit(self.getFrequency())
            )
            self.modulationDutyCycleSlider.valueChanged.connect(
                lambda value: self.sigDutyCycleChanged.emit(value)
            )
            self.modulationDutyCycleEdit.returnPressed.connect(
                lambda: self.sigDutyCycleChanged.emit(self.getDutyCycle())
            )

    def isActive(self):
        """ Returns whether the laser is powered on. """
        return self.enableButton.isChecked()

    def getValue(self):
        """ Returns the value of the laser, in the units that the laser
        uses. """
        return float(self.setPointEdit.text())
    
    def getFrequency(self):
        """ Returns the selected frequency of the laser.
        """
        return int(self.modulationFrequencyEdit.text())
    
    def getDutyCycle(self):
        """ Returns the selected duty cycle of the laser.
        """
        return int(self.modulationDutyCycleEdit.text())

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
    
    def setModulationFrequency(self, value):
        """ Sets the laser modulation frequency. """
        self.modulationFrequencyEdit.setText(f"{value}")
        self.modulationFrequencySlider.setValue(value)
    
    def setModulationDutyCycle(self, value):
        """ Sets the laser modulation duty cycle. """
        self.modulationDutyCycleEdit.setText(f"{value}")
        self.modulationDutyCycleSlider.setValue(value)


# Copyright (C) 2017 Federico Barabas 2020-2021 ImSwitch developers
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
