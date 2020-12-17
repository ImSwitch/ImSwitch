# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import view.guitools as guitools
from .basewidgets import Widget


class PositionerWidget(Widget):
    """ Widget in control of the piezzo movement. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pars = {}
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

    def initControls(self, stagePiezzoInfos):
        for index, (stagePiezzoId, stagePiezzoInfo) in enumerate(stagePiezzoInfos.items()):
            self.pars['Label' + stagePiezzoId] = QtGui.QLabel("<strong>{} = {:.2f} µm</strong>".format(stagePiezzoId, 0))
            self.pars['Label' + stagePiezzoId].setTextFormat(QtCore.Qt.RichText)
            self.pars['UpButton' + stagePiezzoId] = guitools.BetterPushButton("+")
            self.pars['DownButton' + stagePiezzoId] = guitools.BetterPushButton("-")
            self.pars['StepEdit' + stagePiezzoId] = QtGui.QLineEdit("0")
            self.pars['StepUnit' + stagePiezzoId] = QtGui.QLabel(" µm")

            self.grid.addWidget(self.pars['Label' + stagePiezzoId], index, 0)
            self.grid.addWidget(self.pars['UpButton' + stagePiezzoId], index, 1)
            self.grid.addWidget(self.pars['DownButton' + stagePiezzoId], index, 2)
            self.grid.addWidget(QtGui.QLabel("Step"), index, 3)
            self.grid.addWidget(self.pars['StepEdit' + stagePiezzoId], index, 4)
            self.grid.addWidget(self.pars['StepUnit' + stagePiezzoId], index, 5)


class LaserWidget(Widget):
    """ Laser widget containing digital modulation and normal control. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.laserModules = {}
        self.digModule = DigitalModule()

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

    def initControls(self, laserInfos):
        self.laserModules = {}
        for index, (laserName, laserInfo) in enumerate(laserInfos.items()):
            control = LaserModule(name='<h3>{}<h3>'.format(laserName), units=laserInfo.getUnit(),
                                  laser=laserName, wavelength=laserInfo.wavelength,
                                  prange=(laserInfo.valueRangeMin, laserInfo.valueRangeMax),
                                  tickInterval=5, singleStep=laserInfo.valueRangeStep,
                                  init_power=laserInfo.valueRangeMin, isBinary=laserInfo.isBinary())

            self.laserModules[laserName] = control
            self.grid.addWidget(control, 0, index, 4, 1)

        self.digModule = DigitalModule()
        self.digModule.initControls(laserInfos)
        self.grid.addWidget(self.digModule, 4, 0, 2, -1)


class DigitalModule(QtGui.QFrame):
    """ Module from LaserWidget to handle digital modulation. """

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
        self.updateDigPowersButton = guitools.BetterPushButton('Update powers')
        self.grid.addWidget(self.DigitalControlButton, 2, 0, 1, -1)

    def initControls(self, laserInfos):
        self.powers = {}

        for index, (laserName, laserInfo) in enumerate(laserInfos.items()):
            power = QtGui.QLineEdit(str(laserInfo.valueRangeMin))
            unit = QtGui.QLabel(laserInfo.getUnit())
            unit.setFixedWidth(20)
            modFrame = QtGui.QFrame()
            modGrid = QtGui.QGridLayout()
            modFrame.setLayout(modGrid)
            modGrid.addWidget(power, 0, 0)
            modGrid.addWidget(unit, 0, 1)

            self.powers[laserName] = power
            self.grid.addWidget(modFrame, 1, index, 1, 1)
            if laserInfo.isBinary():
                sizePolicy = modFrame.sizePolicy()
                sizePolicy.setRetainSizeWhenHidden(True)
                modFrame.setSizePolicy(sizePolicy)
                modFrame.hide()


class LaserModule(QtGui.QFrame):
    """ Module from LaserWidget to handle a single laser. """

    def __init__(self, name, units, laser, wavelength, prange, tickInterval, singleStep, init_power,
                 isBinary, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.laser = laser

        self.name = QtGui.QLabel(name)
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        color = guitools.color_utils.wavelength_to_hex(wavelength)
        self.name.setStyleSheet(f'font-size:16px; border-bottom: 4px solid {color}')
        self.name.setFixedHeight(40)

        self.setPointLabel = QtGui.QLabel('Setpoint')
        self.setPointEdit = QtGui.QLineEdit(str(init_power))
        self.setPointEdit.setFixedWidth(50)
        self.setPointEdit.setAlignment(QtCore.Qt.AlignRight)

        self.powerLabel = QtGui.QLabel('Power')
        self.powerIndicator = QtGui.QLabel(str(init_power))
        self.powerIndicator.setFixedWidth(50)
        self.powerIndicator.setAlignment(QtCore.Qt.AlignRight)

        self.maxpower = QtGui.QLabel(str(prange[1]))
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)

        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        if not isBinary:
            self.slider.setMinimum(prange[0])
            self.slider.setMaximum(prange[1])
            self.slider.setTickInterval(tickInterval)
            self.slider.setSingleStep(singleStep)
            self.slider.setValue(0)

        self.minpower = QtGui.QLabel(str(prange[0]))
        self.minpower.setAlignment(QtCore.Qt.AlignCenter)

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


class BeadRecWidget(Widget):
    """ Displays the FFT transform of the image. """

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
        # grid.setRowMinimumHeight(0, 300)
