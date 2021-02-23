import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class AlignWidgetXY(Widget):
    """ Alignment widget that shows the mean over an axis of a selected ROI."""

    sigShowROIToggled = QtCore.Signal(bool)  # (enabled)
    sigAxisChanged = QtCore.Signal(int)  # (axisNumber)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.roiButton = guitools.BetterPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.XButton = QtWidgets.QRadioButton('X dimension')
        self.YButton = QtWidgets.QRadioButton('Y dimension')
        self.ROI = guitools.ROI((50, 50), (0, 0), handlePos=(1, 0),
                                handleCenter=(0, 1), color=pg.mkPen(255, 0, 0),
                                scaleSnap=True, translateSnap=True)
        self.graph = guitools.ProjectionGraph()

        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
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