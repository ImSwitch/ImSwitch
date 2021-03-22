import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
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
        self.ROI = guitools.ROI((50, 50), (0, 0), handlePos=(1, 0),
                                handleCenter=(0, 1), color=pg.mkPen(0, 255, 0),
                                scaleSnap=True, translateSnap=True)
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
        self.ROI.setPos(position)
        self.ROI.setSize(size)
        self.ROI.show()

    def hideROI(self):
        self.ROI.hide()

    def updateGraph(self, value):
        self.graph.updateGraph(value)

    def updateDisplayState(self, showingROI):
        self.roiButton.setText('Show ROI' if showingROI else 'Hide ROI')
        

# Copyright (C) 2020, 2021 TestaLab
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
