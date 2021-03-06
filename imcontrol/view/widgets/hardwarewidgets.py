# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import imcontrol.view.guitools as guitools
from .basewidgets import Widget


class PositionerWidget(Widget):
    """ Widget in control of the piezzo movement. """

    sigStepUpClicked = QtCore.Signal(str)  # (positionerName)
    sigStepDownClicked = QtCore.Signal(str)  # (positionerName)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 0
        self.pars = {}
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

    def addPositioner(self, positionerName):
        self.pars['Label' + positionerName] = QtGui.QLabel(f"<strong>{positionerName} = {0:.2f} µm</strong>")
        self.pars['Label' + positionerName].setTextFormat(QtCore.Qt.RichText)
        self.pars['UpButton' + positionerName] = guitools.BetterPushButton("+")
        self.pars['DownButton' + positionerName] = guitools.BetterPushButton("-")
        self.pars['StepEdit' + positionerName] = QtGui.QLineEdit("0.05")
        self.pars['StepUnit' + positionerName] = QtGui.QLabel(" µm")

        self.grid.addWidget(self.pars['Label' + positionerName], self.numPositioners, 0)
        self.grid.addWidget(self.pars['UpButton' + positionerName], self.numPositioners, 1)
        self.grid.addWidget(self.pars['DownButton' + positionerName], self.numPositioners, 2)
        self.grid.addWidget(QtGui.QLabel("Step"), self.numPositioners, 3)
        self.grid.addWidget(self.pars['StepEdit' + positionerName], self.numPositioners, 4)
        self.grid.addWidget(self.pars['StepUnit' + positionerName], self.numPositioners, 5)

        self.numPositioners += 1

        # Connect signals
        self.pars['UpButton' + positionerName].clicked.connect(
            lambda: self.sigStepUpClicked.emit(positionerName)
        )
        self.pars['DownButton' + positionerName].clicked.connect(
            lambda: self.sigStepDownClicked.emit(positionerName)
        )

    def getStepSize(self, positionerName):
        return float(self.pars['StepEdit' + positionerName].text())

    def updatePosition(self, positionerName, position):
        text = f"<strong>{positionerName} = {position:.2f} µm</strong>"
        self.pars['Label' + positionerName].setText(text)


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

        self.grid = QtGui.QGridLayout()
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


class DigitalModule(QtGui.QFrame):
    """ Module from LaserWidget to handle digital modulation. """

    sigDigitalModToggled = QtCore.Signal(bool)
    sigDigitalValueChanged = QtCore.Signal(str, float)  # (laserName, value)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.powers = {}

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

        title = QtGui.QLabel('<h3>Digital modulation<h3>')
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

        power = QtGui.QLineEdit(str(valueRange[0]) if valueRange is not None else '0')
        unit = QtGui.QLabel(valueUnits)
        modFrame = QtGui.QFrame()
        modGrid = QtGui.QGridLayout()
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


class LaserModule(QtGui.QFrame):
    """ Module from LaserWidget to handle a single laser. """

    sigEnableChanged = QtCore.Signal(bool)  # (enabled)
    sigValueChanged = QtCore.Signal(float)  # (value)

    def __init__(self, name, units, wavelength, valueRange, tickInterval, singleStep,
                 initialPower, *args, **kwargs):
        super().__init__(*args, **kwargs)
        isBinary = valueRange is None

        # Graphical elements
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)

        self.name = QtGui.QLabel(f'<h3>{name}<h3>')
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        color = guitools.colorutils.wavelengthToHex(wavelength)
        self.name.setStyleSheet(f'font-size:16px; border-bottom: 4px solid {color}')
        self.name.setFixedHeight(40)

        self.setPointLabel = QtGui.QLabel('Setpoint')
        self.setPointEdit = QtGui.QLineEdit(str(initialPower))
        self.setPointEdit.setFixedWidth(50)
        self.setPointEdit.setAlignment(QtCore.Qt.AlignRight)

        self.powerLabel = QtGui.QLabel('Power')
        self.powerIndicator = QtGui.QLabel(str(initialPower))
        self.powerIndicator.setFixedWidth(50)
        self.powerIndicator.setAlignment(QtCore.Qt.AlignRight)

        self.minpower = QtGui.QLabel()
        self.minpower.setAlignment(QtCore.Qt.AlignCenter)
        self.maxpower = QtGui.QLabel()
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)

        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
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

        powerFrame = QtGui.QFrame(self)
        self.powerGrid = QtGui.QGridLayout()
        powerFrame.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        powerFrame.setLayout(self.powerGrid)

        self.powerGrid.addWidget(self.setPointLabel, 1, 0, 1, 2)
        self.powerGrid.addWidget(self.setPointEdit, 2, 0)
        self.powerGrid.addWidget(QtGui.QLabel(units), 2, 1)
        self.powerGrid.addWidget(self.powerLabel, 3, 0, 1, 2)
        self.powerGrid.addWidget(self.powerIndicator, 4, 0)
        self.powerGrid.addWidget(QtGui.QLabel(units), 4, 1)
        self.powerGrid.addWidget(self.maxpower, 0, 3)
        self.powerGrid.addWidget(self.slider, 1, 3, 8, 1)
        self.powerGrid.addWidget(self.minpower, 9, 3)

        self.enableButton = guitools.BetterPushButton('ON')
        self.enableButton.setCheckable(True)

        # Add elements to GridLayout
        self.grid = QtGui.QGridLayout()
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


class BeadRecWidget(Widget):
    """ Displays the FFT transform of the image. """

    sigROIToggled = QtCore.Signal(bool)  # (enabled)
    sigRunClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Viewbox
        self.cwidget = pg.GraphicsLayoutWidget()
        self.vb = self.cwidget.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = pg.ImageItem(axisOrder='row-major')
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.hist.gradient.loadPreset('greyclip')
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.cwidget.addItem(self.hist, row=1, col=2)

        self.roiButton = guitools.BetterPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.runButton = QtGui.QCheckBox('Run')
        self.ROI = guitools.ROI((0, 0), (0, 0), handlePos=(1, 0),
                                handleCenter=(0, 1), color='y', scaleSnap=True,
                                translateSnap=True)

        # Add elements to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.cwidget, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.runButton, 1, 1, 1, 1)

        # Connect signals
        self.roiButton.toggled.connect(self.sigROIToggled)
        self.runButton.clicked.connect(self.sigRunClicked)

    def getROIGraphicsItem(self):
        return self.ROI

    def showROI(self, position, size):
        self.ROI.setPos(position)
        self.ROI.setSize(size)
        self.ROI.show()

    def hideROI(self):
        self.ROI.hide()

    def updateImage(self, image):
        self.img.setImage(image, autoLevels=False)

    def updateDisplayState(self, showingROI):
        self.roiButton.setText('Show ROI' if showingROI else 'Hide ROI')
