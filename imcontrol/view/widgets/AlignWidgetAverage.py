import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class AlignWidgetAverage(Widget):
    """ Alignment widget that shows the mean over a selected ROI."""

    sigShowROIToggled = QtCore.Signal(bool)  # (enabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.roiButton = guitools.BetterPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.resetButton = guitools.BetterPushButton('Reset graph')
        self.ROI = guitools.VispyROIVisual(rect_color='yellow', handle_color='orange')
        self.graph = guitools.SumpixelsGraph()
        self.resetButton.clicked.connect(self.graph.resetData)

        # Add items to GridLayout
        grid = QtWidgets.QGridLayout()
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
        self.ROI.position = position
        self.ROI.size = size
        self.ROI.show()

    def hideROI(self):
        self.ROI.hide()

    def updateGraph(self, value):
        self.graph.updateGraph(value)

    def updateDisplayState(self, showingROI):
        self.roiButton.setText('Show ROI' if showingROI else 'Hide ROI')
