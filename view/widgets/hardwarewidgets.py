# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import view.guitools as guitools
from .basewidgets import Widget

class PositionerWidget(Widget):
    """ Widget in control of the piezzo movement. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.xLabel = QtGui.QLabel(
            "<strong>x = {0:.2f} µm</strong>".format(0))
        self.xLabel.setTextFormat(QtCore.Qt.RichText)
        self.xUpButton = QtGui.QPushButton("+")
        self.xDownButton = QtGui.QPushButton("-")
        self.xStepEdit = QtGui.QLineEdit("0.05")
        self.xStepUnit = QtGui.QLabel(" µm")

        self.yLabel = QtGui.QLabel(
            "<strong>y = {0:.2f} µm</strong>".format(0))
        self.yLabel.setTextFormat(QtCore.Qt.RichText)
        self.yUpButton = QtGui.QPushButton("+")
        self.yDownButton = QtGui.QPushButton("-")
        self.yStepEdit = QtGui.QLineEdit("0.05")
        self.yStepUnit = QtGui.QLabel(" µm")

        self.zLabel = QtGui.QLabel(
            "<strong>z = {0:.2f} µm</strong>".format(0))
        self.zLabel.setTextFormat(QtCore.Qt.RichText)
        self.zUpButton = QtGui.QPushButton("+")
        self.zDownButton = QtGui.QPushButton("-")
        self.zStepEdit = QtGui.QLineEdit("0.05")
        self.zStepUnit = QtGui.QLabel(" µm")

        # Add elements to GridLayout
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.xLabel, 1, 0)
        layout.addWidget(self.xUpButton, 1, 1)
        layout.addWidget(self.xDownButton, 1, 2)
        layout.addWidget(QtGui.QLabel("Step"), 1, 3)
        layout.addWidget(self.xStepEdit, 1, 4)
        layout.addWidget(self.xStepUnit, 1, 5)
        layout.addWidget(self.yLabel, 2, 0)
        layout.addWidget(self.yUpButton, 2, 1)
        layout.addWidget(self.yDownButton, 2, 2)
        layout.addWidget(QtGui.QLabel("Step"), 2, 3)
        layout.addWidget(self.yStepEdit, 2, 4)
        layout.addWidget(self.yStepUnit, 2, 5)
        layout.addWidget(self.zLabel, 3, 0)
        layout.addWidget(self.zUpButton, 3, 1)
        layout.addWidget(self.zDownButton, 3, 2)
        layout.addWidget(QtGui.QLabel("Step"), 3, 3)
        layout.addWidget(self.zStepEdit, 3, 4)
        layout.addWidget(self.zStepUnit, 3, 5)

    def registerListener(self, controller):
        """ Manage interactions with PositionerController. """
        self.xUpButton.pressed.connect(lambda: controller.move(0, float(self.xStepEdit.text())))
        self.xDownButton.pressed.connect(lambda: controller.move(0, -float(self.xStepEdit.text())))
        self.yUpButton.pressed.connect(lambda: controller.move(1, float(self.yStepEdit.text())))
        self.yDownButton.pressed.connect(lambda: controller.move(1, -float(self.yStepEdit.text())))
        self.zUpButton.pressed.connect(lambda: controller.move(2, float(self.zStepEdit.text())))
        self.zDownButton.pressed.connect(lambda: controller.move(2, -float(self.zStepEdit.text())))


class LaserWidget(Widget):
    """ Laser widget containing digital modulation and normal control. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create laser modules
        actControl = LaserModule('<h3>405<h3>', 'mW', '405', color=(130, 0, 200), prange=(0, 200), tickInterval=5, singleStep=0.1, init_power = 10)
        offControl = LaserModule('<h3>488<h3>', 'mW', '488', color=(0, 247, 255), prange=(0, 200), tickInterval=100, singleStep=10, init_power = 10)
        excControl = LaserModule('<h3>473<h3>', 'V', '473', color=(0, 183, 255), prange=(0, 5), tickInterval=1, singleStep=0.1, init_power = 0.5)
        self.digModule = DigitalModule()

        self.laserModules = {'405': actControl, '488': offControl, '473': excControl}

        # Add modules to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(actControl, 0, 0, 4, 1)
        grid.addWidget(offControl, 0, 1, 4, 1)
        grid.addWidget(excControl, 0, 2, 4, 1)
        grid.addWidget(self.digModule, 4, 0, 2, 3)

    def registerListener(self, controller):
        """ Manage interactions with LaserController. """
        self.laserModules['405'].registerListener(controller)
        self.laserModules['488'].registerListener(controller)
        self.laserModules['473'].registerListener(controller)
        self.digModule.registerListener(controller)

class DigitalModule(QtGui.QFrame):
    """ Module from LaserWidget to handle digital modulation. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        title = QtGui.QLabel('<h3>Digital modulation<h3>')
        title.setTextFormat(QtCore.Qt.RichText)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:12px")
        title.setFixedHeight(20)
        ActPower = QtGui.QLineEdit('100')
        OffPower = QtGui.QLineEdit('100')
        ExcPower = QtGui.QLineEdit('0.5')
        self.powers = {'405' : ActPower, '488' : OffPower, '473' : ExcPower}
        self.DigitalControlButton = QtGui.QPushButton('Enable')
        self.DigitalControlButton.setCheckable(True)
        style = "background-color: rgb{}".format((160, 160, 160))
        self.DigitalControlButton.setStyleSheet(style)
        self.updateDigPowersButton = QtGui.QPushButton('Update powers')
        actUnit = QtGui.QLabel('mW')
        actUnit.setFixedWidth(20)

        actModFrame = QtGui.QFrame()
        actModGrid = QtGui.QGridLayout()
        actModFrame.setLayout(actModGrid)
        actModGrid.addWidget(ActPower, 0, 0)
        actModGrid.addWidget(actUnit, 0, 1)

        offUnit = QtGui.QLabel('mW')
        offUnit.setFixedWidth(20)
        offModFrame = QtGui.QFrame()
        offModGrid = QtGui.QGridLayout()
        offModFrame.setLayout(offModGrid)
        offModGrid.addWidget(OffPower, 0, 0)
        offModGrid.addWidget(offUnit, 0, 1)

        excUnit = QtGui.QLabel('V')
        excUnit.setFixedWidth(20)
        excModFrame = QtGui.QFrame()
        excModGrid = QtGui.QGridLayout()
        excModFrame.setLayout(excModGrid)
        excModGrid.addWidget(ExcPower, 0, 0)
        excModGrid.addWidget(excUnit, 0, 1)

        # Add elements to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(title, 0, 0)
        grid.addWidget(actModFrame, 1, 0)
        grid.addWidget(offModFrame, 1, 1)
        grid.addWidget(excModFrame, 1, 2)
        grid.addWidget(self.DigitalControlButton, 2, 0, 1, 3)

    def registerListener(self, controller):
        """ Manage interactions with LaserController. """
        self.powers['405'].textChanged.connect(lambda: controller.updateDigitalPowers(['405']))
        self.powers['488'].textChanged.connect(lambda: controller.updateDigitalPowers(['488']))
        self.powers['473'].textChanged.connect(lambda: controller.updateDigitalPowers(['473']))
        self.DigitalControlButton.clicked.connect(lambda: controller.GlobalDigitalMod(['405', '473', '488']))
        self.updateDigPowersButton.clicked.connect(lambda: controller.updateDigitalPowers(['405','473', '488']))


class LaserModule(QtGui.QFrame):
    """ Module from LaserWidget to handle a single laser. """
    def __init__(self, name,  units, laser, color, prange, tickInterval, singleStep, init_power,  *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.laser = laser
        self.name = QtGui.QLabel(name)
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        self.name.setStyleSheet("font-size:16px")
        self.name.setFixedHeight(40)
        self.init_power = init_power
        self.setPointLabel = QtGui.QLabel('Setpoint')
        self.setPointEdit = QtGui.QLineEdit(str(self.init_power))
        self.setPointEdit.setFixedWidth(50)
        self.setPointEdit.setAlignment(QtCore.Qt.AlignRight)
        self.powerLabel = QtGui.QLabel('Power')
        self.powerIndicator = QtGui.QLabel(str(self.init_power))
        self.powerIndicator.setFixedWidth(50)
        self.powerIndicator.setAlignment(QtCore.Qt.AlignRight)
        self.maxpower = QtGui.QLabel(str(prange[1]))
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)
        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
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

        self.enableButton = QtGui.QPushButton('ON')
        style = "background-color: rgb{}".format(color)
        self.enableButton.setStyleSheet(style)
        self.enableButton.setCheckable(True)

        # Add elements to GridLayout
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.name, 0, 0, 1, 2)
        self.grid.addWidget(powerFrame, 1, 0, 1, 2)
        self.grid.addWidget(self.enableButton, 8, 0, 1, 2)

    def registerListener(self, controller):
        """ Manage interactions with LaserController. """
        if not self.laser=='473': controller.changeEdit(self.laser)
        self.enableButton.toggled.connect(lambda: controller.toggleLaser(self.laser))
        self.slider.valueChanged[int].connect(lambda: controller.changeSlider(self.laser))
        self.setPointEdit.returnPressed.connect(lambda: controller.changeEdit(self.laser))

class BeadRecWidget(Widget):
    """ Displays the FFT transform of the image. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

            # Viewbox
        self.cwidget = pg.GraphicsLayoutWidget()
        self.vb = self.cwidget.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = pg.ImageItem()
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.cubehelixCM = pg.ColorMap(np.arange(0, 1, 1/256), guitools.cubehelix().astype(int))
        self.hist.gradient.setColorMap(self.cubehelixCM)
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.cwidget.addItem(self.hist, row=1, col=2)

        self.roiButton = QtGui.QPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.runButton = QtGui.QPushButton('Run')
        self.runButton.setCheckable(True)
        self.ROI = guitools.ROI((0, 0), (0, 0), handlePos=(1, 0),
                                handleCenter=(0, 1), color='y', scaleSnap=True,
                                translateSnap=True)

        # Add elements to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.cwidget, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.runButton, 1, 1, 1, 1)
        grid.setRowMinimumHeight(0, 300)

    def registerListener(self, controller):
        controller.addROI()
        self.roiButton.clicked.connect(controller.toggleROI)
        self.runButton.clicked.connect(controller.run)
