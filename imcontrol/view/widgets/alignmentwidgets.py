import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import imcontrol.view.guitools as guitools
from .basewidgets import Widget


class ULensesWidget(Widget):
    """ Alignment widget that shows a grid of points on top of the image in the viewbox."""

    sigULensesClicked = QtCore.Signal()
    sigUShowLensesChanged = QtCore.Signal(bool)  # (enabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical Elements
        self.ulensesButton = guitools.BetterPushButton('uLenses')
        self.ulensesCheck = QtGui.QCheckBox('Show uLenses')
        self.xEdit = QtGui.QLineEdit(self._defaultPreset.uLenses.xOffset)
        self.yEdit = QtGui.QLineEdit(self._defaultPreset.uLenses.yOffset)
        self.pxEdit = QtGui.QLineEdit(self._defaultPreset.uLenses.pixelSize)
        self.upEdit = QtGui.QLineEdit(self._defaultPreset.uLenses.periodicity)
        self.ulensesPlot = pg.ScatterPlotItem()

        # Add elements to GridLayout
        ulensesLayout = QtGui.QGridLayout()
        self.setLayout(ulensesLayout)
        ulensesLayout.addWidget(QtGui.QLabel('Pixel Size'), 0, 0)
        ulensesLayout.addWidget(self.pxEdit, 0, 1)
        ulensesLayout.addWidget(QtGui.QLabel('Periodicity'), 1, 0)
        ulensesLayout.addWidget(self.upEdit, 1, 1)
        ulensesLayout.addWidget(QtGui.QLabel('X offset'), 2, 0)
        ulensesLayout.addWidget(self.xEdit, 2, 1)
        ulensesLayout.addWidget(QtGui.QLabel('Y offset'), 3, 0)
        ulensesLayout.addWidget(self.yEdit, 3, 1)
        ulensesLayout.addWidget(self.ulensesButton, 4, 0)
        ulensesLayout.addWidget(self.ulensesCheck, 4, 1)

        # Connect signals
        self.ulensesButton.clicked.connect(self.sigULensesClicked)
        self.ulensesCheck.toggled.connect(self.sigUShowLensesChanged)

    def getParameters(self):
        """ Returns the X offset, Y offset, pixel size, and periodicity
        parameters respectively set by the user."""
        return (np.float(self.xEdit.text()),
                np.float(self.yEdit.text()),
                np.float(self.pxEdit.text()),
                np.float(self.upEdit.text()))

    def getPlotGraphicsItem(self):
        return self.ulensesPlot

    def setData(self, x, y):
        """ Updates plot with new parameters. """
        self.ulensesPlot.setData(x=x, y=y, pen=pg.mkPen(None), brush='r', symbol='x')


class AlignWidgetXY(Widget):
    """ Alignment widget that shows the mean over an axis of a selected ROI."""

    sigShowROIToggled = QtCore.Signal(bool)  # (enabled)
    sigAxisChanged = QtCore.Signal(int)  # (axisNumber)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.roiButton = guitools.BetterPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.XButton = QtGui.QRadioButton('X dimension')
        self.YButton = QtGui.QRadioButton('Y dimension')
        self.ROI = guitools.ROI((50, 50), (0, 0), handlePos=(1, 0),
                                handleCenter=(0, 1), color=pg.mkPen(255, 0, 0),
                                scaleSnap=True, translateSnap=True)
        self.graph = guitools.ProjectionGraph()

        # Add elements to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.graph, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.XButton, 1, 1, 1, 1)
        grid.addWidget(self.YButton, 1, 2, 1, 1)

        # Connect signals
        self.roiButton.toggled.connect(self.sigShowROIToggled)
        self.XButton.clicked.connect(lambda: self.sigAxisChanged.emit(0))
        self.YButton.clicked.connect(lambda: self.sigAxisChanged.emit(1))

    def getROIGraphicsItem(self):
        return self.ROI

    def showROI(self, position, size):
        self.ROI.setPos(position)
        self.ROI.setSize(size)
        self.ROI.show()

    def hideROI(self):
        self.ROI.hide()

    def updateGraph(self, value):
        self.graph.updateGraph(value)

    def updateDisplayState(self, showingROI):
        self.roiButton.setText('Show ROI' if showingROI else 'Hide ROI')


class AlignWidgetAverage(Widget):
    """ Alignment widget that shows the mean over a selected ROI."""

    sigShowROIToggled = QtCore.Signal(bool)  # (enabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.roiButton = guitools.BetterPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.resetButton = guitools.BetterPushButton('Reset graph')
        self.ROI = guitools.ROI((50, 50), (0, 0), handlePos=(1, 0),
                                handleCenter=(0, 1), color=pg.mkPen(0, 255, 0),
                                scaleSnap=True, translateSnap=True)
        self.graph = guitools.SumpixelsGraph()
        self.resetButton.clicked.connect(self.graph.resetData)

        # Add items to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.graph, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.resetButton, 1, 1, 1, 1)
        # grid.setRowMinimumHeight(0, 300)

        # Connect signals
        self.roiButton.toggled.connect(self.sigShowROIToggled)

    def getROIGraphicsItem(self):
        return self.ROI

    def showROI(self, position, size):
        self.ROI.setPos(position)
        self.ROI.setSize(size)
        self.ROI.show()

    def hideROI(self):
        self.ROI.hide()

    def updateGraph(self, value):
        self.graph.updateGraph(value)

    def updateDisplayState(self, showingROI):
        self.roiButton.setText('Show ROI' if showingROI else 'Hide ROI')


class AlignmentLineWidget(Widget):
    """ Alignment widget that displays a line on top of the image in the viewbox."""

    sigAlignmentLineMakeClicked = QtCore.Signal()
    sigAlignmentCheckToggled = QtCore.Signal(bool)  # (enabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.angleEdit = QtGui.QLineEdit(self._defaultPreset.alignmentLine.lineAngle)
        self.alignmentCheck = QtGui.QCheckBox('Show Alignment Tool')
        self.alignmentLineMakerButton = guitools.BetterPushButton('Alignment Line')
        pen = pg.mkPen(color=(255, 255, 0), width=0.5,
                       style=QtCore.Qt.SolidLine, antialias=True)
        self.alignmentLine = pg.InfiniteLine(
            pen=pen, movable=True)

        # Add items to GridLayout
        alignmentLayout = QtGui.QGridLayout()
        self.setLayout(alignmentLayout)
        alignmentLayout.addWidget(QtGui.QLabel('Line Angle'), 0, 0)
        alignmentLayout.addWidget(self.angleEdit, 0, 1)
        alignmentLayout.addWidget(self.alignmentLineMakerButton, 1, 0)
        alignmentLayout.addWidget(self.alignmentCheck, 1, 1)

        # Connect signals
        self.alignmentLineMakerButton.clicked.connect(self.sigAlignmentLineMakeClicked)
        self.alignmentCheck.toggled.connect(self.sigAlignmentCheckToggled)

    def getAngleInput(self):
        return float(self.angleEdit.text())

    def setLineAngle(self, angle):
        self.alignmentLine.setAngle(angle)


class FFTWidget(Widget):
    """ Displays the FFT transform of the image. """

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigChangePosClicked = QtCore.Signal()
    sigPosChanged = QtCore.Signal(float)  # (pos)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    sigResized = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.showCheck = QtGui.QCheckBox('Show FFT')
        self.showCheck.setCheckable = True
        self.changePosButton = guitools.BetterPushButton('Period (pix)')
        self.linePos = QtGui.QLineEdit('4')
        self.lineRate = QtGui.QLineEdit('0')
        self.labelRate = QtGui.QLabel('Update rate')

        # Vertical and horizontal lines
        self.vline = pg.InfiniteLine()
        self.hline = pg.InfiniteLine()
        self.rvline = pg.InfiniteLine()
        self.lvline = pg.InfiniteLine()
        self.uhline = pg.InfiniteLine()
        self.dhline = pg.InfiniteLine()

        # Viewbox
        self.cwidget = pg.GraphicsLayoutWidget()
        self.vb = self.cwidget.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = guitools.OptimizedImageItem(axisOrder='row-major')
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.hist.gradient.loadPreset('greyclip')
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.cwidget.addItem(self.hist, row=1, col=2)

        # Add lines to viewbox
        self.vb.addItem(self.vline)
        self.vb.addItem(self.hline)
        self.vb.addItem(self.lvline)
        self.vb.addItem(self.rvline)
        self.vb.addItem(self.uhline)
        self.vb.addItem(self.dhline)

        # Add elements to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.cwidget, 0, 0, 1, 6)
        grid.addWidget(self.showCheck, 1, 0, 1, 1)
        grid.addWidget(self.changePosButton, 2, 0, 1, 1)
        grid.addWidget(self.linePos, 2, 1, 1, 1)
        grid.addWidget(self.labelRate, 2, 2, 1, 1)
        grid.addWidget(self.lineRate, 2, 3, 1, 1)
        # grid.setRowMinimumHeight(0, 300)

        # Connect signals
        self.showCheck.toggled.connect(self.sigShowToggled)
        self.changePosButton.clicked.connect(self.sigChangePosClicked)
        self.linePos.textChanged.connect(
            lambda: self.sigPosChanged.emit(self.getPos())
        )
        self.lineRate.textChanged.connect(
            lambda: self.sigUpdateRateChanged.emit(self.getUpdateRate())
        )
        self.vb.sigResized.connect(self.sigResized)

    def getShowChecked(self):
        return self.showCheck.isChecked()

    def getPos(self):
        return float(self.linePos.text())

    def getUpdateRate(self):
        return float(self.lineRate.text())

# Copyright (C) 2020, 2021 Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
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
