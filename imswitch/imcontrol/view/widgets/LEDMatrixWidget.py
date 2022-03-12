import numpy as np
import pyqtgraph as pg
from qtpy import QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class LEDMatrixWidget(Widget):
    """ Widget containing focus lock interface. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Focus lock
        self.focusButton = guitools.BetterPushButton('LEDMatrix')
        self.focusButton.setCheckable(True)
        self.focusButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Expanding)

        self.zStepRangeEdit = QtWidgets.QLineEdit('100')
        self.zStepRangeLabel = QtWidgets.QLabel('Focus search range (nm)')
        self.zStepSizeEdit = QtWidgets.QLineEdit('10')
        self.zStepSizeLabel = QtWidgets.QLabel('Stepsize (nm)')

        # self.focusDataBox = QtWidgets.QCheckBox('Save data')  # Connect to exportData
        #self.camDialogButton = guitools.BetterPushButton('Camera Dialog')

        # Piezo absolute positioning
        self.positionLabel = QtWidgets.QLabel(
            'Position (µm)')  # Potentially disregard this and only use in the positioning widget?
        self.positionEdit = QtWidgets.QLineEdit('50')
        #self.positionSetButton = guitools.BetterPushButton('Set')

        # Focus lock graph
        self.LEDMatrixGraph = pg.GraphicsLayoutWidget()
        self.LEDMatrixGraph.setAntialiasing(True)
        self.focusPlot = self.LEDMatrixGraph.addPlot(row=1, col=0)
        self.focusPlot.setLabels(bottom=('Motion', 'µm'), left=('Contrast', 'A.U.'))
        self.focusPlot.showGrid(x=True, y=True)
        # update this (self.focusPlotCurve.setData(X,Y)) with update(focusSignal) function
        self.focusPlotCurve = self.focusPlot.plot(pen='y')

        # Webcam graph
        self.webcamGraph = pg.GraphicsLayoutWidget()
        self.camImg = pg.ImageItem(border='w')
        self.camImg.setImage(np.zeros((100, 100)))
        self.vb = self.webcamGraph.addViewBox(invertY=True, invertX=False)
        self.vb.setAspectLocked(True)
        self.vb.addItem(self.camImg)

        # PROCESS DATA THREAD - ADD SOMEWHERE ELSE, NOT HERE, AS IT HAS NO GRAPHICAL ELEMENTS!

        # GUI layout below
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.LEDMatrixGraph, 0, 0, 1, 9)
        grid.addWidget(self.webcamGraph, 0, 9, 4, 1)
        grid.addWidget(self.focusButton, 1, 5, 2, 1)
        grid.addWidget(self.zStepRangeLabel, 3, 4)
        grid.addWidget(self.zStepRangeEdit, 4, 4)
        grid.addWidget(self.zStepSizeLabel, 3, 5)
        grid.addWidget(self.zStepSizeEdit, 4, 5)
        grid.addWidget(self.positionLabel, 1, 6)
        grid.addWidget(self.positionEdit, 1, 7)
        #grid.addWidget(self.positionSetButton, 2, 6, 1, 2)
        

# Copyright (C) 2020-2021 ImSwitch developers
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
