
from pyqtgraph.Qt import QtCore, QtWidgets

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class LaserWidget(Widget):
    """ Laser widget containing digital modulation and normal control. """

    sigEnableChanged = QtCore.Signal(str, bool)  # (laserName, enabled)
    sigValueChanged = QtCore.Signal(str, float)  # (laserName, value)

    sigDigitalModToggled = QtCore.Signal(bool)  # (enabled)
    sigDigitalValueChanged = QtCore.Signal(str, float)  # (laserName, value)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.laserModules = {}
        self.digModule = DigitalModule()

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.digModule = DigitalModule()
        self.grid.addWidget(self.digModule, 4, 0, 2, -1)

        # Connect signals
        self.digModule.sigDigitalModToggled.connect(self.sigDigitalModToggled)
        self.digModule.sigDigitalValueChanged.connect(self.sigDigitalValueChanged)

    def addLaser(self, laserName, valueUnits, wavelength, valueRange=None):
        """ Adds a laser module widget. valueRange is either a tuple
        (min, max), or None (if the laser can only be turned on/off). """

        control = LaserModule(
            name=laserName, units=valueUnits, wavelength=wavelength,
            valueRange=valueRange, tickInterval=5, singleStep=1,
            initialPower=valueRange[0] if valueRange is not None else 0
        )
        control.sigEnableChanged.connect(
            lambda enabled: self.sigEnableChanged.emit(laserName, enabled)
        )
        control.sigValueChanged.connect(
            lambda value: self.sigValueChanged.emit(laserName, value)
        )

        self.grid.addWidget(control, 0, len(self.laserModules), 4, 1)
        self.laserModules[laserName] = control

        self.digModule.addLaser(laserName, valueUnits, valueRange)

    def isDigModActive(self):
        return self.digModule.isActive()

    def isLaserActive(self, laserName):
        return self.laserModules[laserName].isActive()

    def getValue(self, laserName):
        return self.laserModules[laserName].getValue()

    def getDigValue(self, laserName):
        return self.digModule.getValue(laserName)

    def setDigModActive(self, digMod):
        self.digModule.setActive(digMod)

    def setLaserActive(self, laserName, active):
        self.laserModules[laserName].setActive(active)

    def setLaserActivatable(self, laserName, activatable):
        self.laserModules[laserName].setActivatable(activatable)

    def setLaserEditable(self, laserName, editable):
        self.laserModules[laserName].setEditable(editable)

    def setValue(self, laserName, value):
        self.laserModules[laserName].setValue(value)

    def setDigValue(self, laserName, value):
        self.digModule.setValue(laserName, value)


class DigitalModule(QtWidgets.QFrame):
    """ Module from LaserWidget to handle digital modulation. """

    sigDigitalModToggled = QtCore.Signal(bool)
    sigDigitalValueChanged = QtCore.Signal(str, float)  # (laserName, value)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.powers = {}

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        title = QtWidgets.QLabel('<h3>Digital modulation<h3>')
        title.setTextFormat(QtCore.Qt.RichText)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:12px")
        title.setFixedHeight(20)
        self.grid.addWidget(title, 0, 0, 1, -1)

        self.DigitalControlButton = guitools.BetterPushButton('Enable')
        self.DigitalControlButton.setCheckable(True)
        self.grid.addWidget(self.DigitalControlButton, 2, 0, 1, -1)

        # Connect signals
        self.DigitalControlButton.toggled.connect(self.sigDigitalModToggled)

    def addLaser(self, laserName, valueUnits, valueRange=None):
        isBinary = valueRange is None

        power = QtWidgets.QLineEdit(str(valueRange[0]) if valueRange is not None else '0')
        unit = QtWidgets.QLabel(valueUnits)
        modFrame = QtWidgets.QFrame()
        modGrid = QtWidgets.QGridLayout()
        modFrame.setLayout(modGrid)
        modGrid.addWidget(power, 0, 0)
        modGrid.addWidget(unit, 0, 1)

        self.grid.addWidget(modFrame, 1, len(self.powers), 1, 1)
        if isBinary:
            sizePolicy = modFrame.sizePolicy()
            sizePolicy.setRetainSizeWhenHidden(True)
            modFrame.setSizePolicy(sizePolicy)
            modFrame.hide()

        self.powers[laserName] = power

        # Connect signals
        power.textChanged.connect(
            lambda value: self.sigDigitalValueChanged.emit(laserName, float(value))
        )

    def isActive(self):
        return self.DigitalControlButton.isChecked()

    def getValue(self, laserName):
        return float(self.powers[laserName].text())

    def setActive(self, active):
        self.DigitalControlButton.setChecked(active)

    def setValue(self, laserName, value):
        self.powers[laserName].setText(str(value))


class LaserModule(QtWidgets.QFrame):
    """ Module from LaserWidget to handle a single laser. """

    sigEnableChanged = QtCore.Signal(bool)  # (enabled)
    sigValueChanged = QtCore.Signal(float)  # (value)

    def __init__(self, name, units, wavelength, valueRange, tickInterval, singleStep,
                 initialPower, *args, **kwargs):
        super().__init__(*args, **kwargs)
        isBinary = valueRange is None

        # Graphical elements
        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Raised)

        self.name = QtWidgets.QLabel(f'<h3>{name}<h3>')
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        color = guitools.colorutils.wavelengthToHex(wavelength)
        self.name.setStyleSheet(f'font-size:16px; border-bottom: 4px solid {color}')
        self.name.setFixedHeight(40)

        self.setPointLabel = QtWidgets.QLabel('Setpoint')
        self.setPointEdit = QtWidgets.QLineEdit(str(initialPower))
        self.setPointEdit.setFixedWidth(50)
        self.setPointEdit.setAlignment(QtCore.Qt.AlignRight)

        self.powerLabel = QtWidgets.QLabel('Power')
        self.powerIndicator = QtWidgets.QLabel(str(initialPower))
        self.powerIndicator.setFixedWidth(50)
        self.powerIndicator.setAlignment(QtCore.Qt.AlignRight)

        self.minpower = QtWidgets.QLabel()
        self.minpower.setAlignment(QtCore.Qt.AlignCenter)
        self.maxpower = QtWidgets.QLabel()
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Vertical, self)
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

        self.powerGrid.addWidget(self.setPointLabel, 1, 0, 1, 2)
        self.powerGrid.addWidget(self.setPointEdit, 2, 0)
        self.powerGrid.addWidget(QtWidgets.QLabel(units), 2, 1)
        self.powerGrid.addWidget(self.powerLabel, 3, 0, 1, 2)
        self.powerGrid.addWidget(self.powerIndicator, 4, 0)
        self.powerGrid.addWidget(QtWidgets.QLabel(units), 4, 1)
        self.powerGrid.addWidget(self.maxpower, 0, 3)
        self.powerGrid.addWidget(self.slider, 1, 3, 8, 1)
        self.powerGrid.addWidget(self.minpower, 9, 3)

        self.enableButton = guitools.BetterPushButton('ON')
        self.enableButton.setCheckable(True)

        # Add elements to GridLayout
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.name, 0, 0, 1, 2)
        self.grid.addWidget(powerFrame, 1, 0, 1, 2)
        if isBinary:
            sizePolicy = powerFrame.sizePolicy()
            sizePolicy.setRetainSizeWhenHidden(True)
            powerFrame.setSizePolicy(sizePolicy)
            powerFrame.hide()
        self.grid.addWidget(self.enableButton, 8, 0, 1, 2)

        # Connect signals
        self.enableButton.toggled.connect(self.sigEnableChanged)
        self.slider.valueChanged[int].connect(
            lambda value: self.sigValueChanged.emit(float(value))
        )
        self.setPointEdit.returnPressed.connect(
            lambda: self.sigValueChanged.emit(self.getValue())
        )

    def isActive(self):
        return self.enableButton.isChecked()

    def getValue(self):
        return float(self.setPointEdit.text())

    def setActive(self, active):
        self.enableButton.setChecked(active)

    def setActivatable(self, activatable):
        self.enableButton.setEnabled(activatable)

    def setEditable(self, editable):
        self.setPointEdit.setEnabled(editable)
        self.slider.setEnabled(editable)

    def setValue(self, value):
        self.setPointEdit.setText(str(value))
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

