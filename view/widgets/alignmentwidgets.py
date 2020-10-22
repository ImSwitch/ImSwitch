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

class ULensesWidget(Widget):
    """ Alignment widget that shows a grid of points on top of the image in the viewbox."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical Elements
        self.ulensesButton = QtGui.QPushButton('uLenses')
        self.ulensesCheck = QtGui.QCheckBox('Show uLenses')
        self.xEdit = QtGui.QLineEdit('0')
        self.yEdit = QtGui.QLineEdit('0')
        self.pxEdit = QtGui.QLineEdit('157.5')
        self.upEdit = QtGui.QLineEdit('1182')
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

    def registerListener(self, controller):
        """ Manage interactions with ULensesController. """
        controller.addPlot()
        self.ulensesButton.clicked.connect(controller.updateGrid)
        self.ulensesCheck.stateChanged.connect(controller.show)


class AlignWidgetXY(Widget):
    """ Alignment widget that shows the mean over an axis of a selected ROI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.roiButton = QtGui.QPushButton('Show ROI')
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

    def registerListener(self, controller):
        """ Manage interactions with AlignXYController. """
        controller.addROI()
        self.roiButton.clicked.connect(controller.toggleROI)
        self.XButton.clicked.connect(lambda: controller.setAxis(0))
        self.YButton.clicked.connect(lambda: controller.setAxis(1))


class AlignWidgetAverage(Widget):
    """ Alignment widget that shows the mean over a selected ROI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.roiButton = QtGui.QPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.resetButton = QtGui.QPushButton('Reset graph')
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
        grid.setRowMinimumHeight(0, 300)


    def registerListener(self, controller):
        """ Manage interactions with AlignAverageController. """
        controller.addROI()
        self.roiButton.clicked.connect(controller.toggleROI)


class AlignmentLineWidget(Widget):
    """ Alignment widget that displays a line on top of the image in the viewbox."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.angleEdit = QtGui.QLineEdit('30')
        self.angle = np.float(self.angleEdit.text())
        self.alignmentCheck = QtGui.QCheckBox('Show Alignment Tool')
        self.alignmentLineMakerButton = QtGui.QPushButton('Alignment Line')
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

    def registerListener(self, controller):
        """ Manage interactions with AlignmentLineController. """
        controller.addLine()
        self.alignmentLineMakerButton.clicked.connect(controller.updateLine)
        self.alignmentCheck.stateChanged.connect(controller.show)


class FFTWidget(Widget):
    """ Displays the FFT transform of the image. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.showCheck = QtGui.QCheckBox('Show FFT')
        self.showCheck.setCheckable = True
        self.changePosButton = QtGui.QPushButton('Period (pix)')
        self.linePos = QtGui.QLineEdit('4')
        self.lineRate = QtGui.QLineEdit('10')
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
        grid.setRowMinimumHeight(0, 300)

    def registerListener(self, controller):
        """ Manage interactions with AlignmentLineController. """
        self.showCheck.stateChanged.connect(controller.showFFT)
        self.changePosButton.clicked.connect(controller.changePos)
        self.linePos.textChanged.connect(controller.changePos)
        self.lineRate.textChanged.connect(controller.changeRate)
