import numpy as np
import pyqtgraph as pg
from qtpy import QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class FocusLockWidget(Widget):
    """ Widget containing focus lock interface. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Focus lock
        self.kpEdit = QtWidgets.QLineEdit('0')
        self.kpLabel = QtWidgets.QLabel('kp')
        self.kiEdit = QtWidgets.QLineEdit('0')
        self.kiLabel = QtWidgets.QLabel('ki')

        self.lockButton = guitools.BetterPushButton('Lock')
        self.lockButton.setCheckable(True)
        self.lockButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Expanding)

        self.zStackBox = QtWidgets.QCheckBox('Z-stack')
        self.twoFociBox = QtWidgets.QCheckBox('Two foci')

        self.zStepFromEdit = QtWidgets.QLineEdit('40')
        self.zStepFromLabel = QtWidgets.QLabel('Min step (nm)')
        self.zStepToEdit = QtWidgets.QLineEdit('100')
        self.zStepToLabel = QtWidgets.QLabel('Max step (nm)')

        # self.focusDataBox = QtWidgets.QCheckBox('Save data')  # Connect to exportData
        self.camDialogButton = guitools.BetterPushButton('Camera Dialog')

        # Piezo absolute positioning
        self.positionLabel = QtWidgets.QLabel(
            'Position (µm)')  # Potentially disregard this and only use in the positioning widget?
        self.positionEdit = QtWidgets.QLineEdit('50')
        self.positionSetButton = guitools.BetterPushButton('Set')

        # Focus lock calibration
        self.calibFromLabel = QtWidgets.QLabel('From (µm)')
        self.calibFromEdit = QtWidgets.QLineEdit('49')
        self.calibToLabel = QtWidgets.QLabel('To (µm)')
        self.calibToEdit = QtWidgets.QLineEdit('51')
        self.focusCalibButton = guitools.BetterPushButton('Calib')
        self.focusCalibButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                            QtWidgets.QSizePolicy.Expanding)
        self.calibCurveButton = guitools.BetterPushButton('See calib')
        self.calibrationDisplay = QtWidgets.QLineEdit(
            'Previous calib: none')  # Edit this from the controller with calibration values
        self.calibrationDisplay.setReadOnly(True)
        # CREATE CALIBRATION CURVE WINDOW AND FOCUS CALIBRATION GRAPH SOMEHOW

        # Focus lock graph
        self.focusLockGraph = pg.GraphicsLayoutWidget()
        self.focusLockGraph.setAntialiasing(True)
        self.focusPlot = self.focusLockGraph.addPlot(row=1, col=0)
        self.focusPlot.setLabels(bottom=('Time', 's'), left=('Laser position', 'px'))
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
        grid.addWidget(self.focusLockGraph, 0, 0, 1, 9)
        grid.addWidget(self.webcamGraph, 0, 9, 4, 1)
        grid.addWidget(self.focusCalibButton, 1, 2, 2, 1)
        grid.addWidget(self.calibrationDisplay, 3, 0, 1, 2)
        grid.addWidget(self.kpLabel, 1, 3)
        grid.addWidget(self.kpEdit, 1, 4)
        grid.addWidget(self.kiLabel, 2, 3)
        grid.addWidget(self.kiEdit, 2, 4)
        grid.addWidget(self.lockButton, 1, 5, 2, 1)
        grid.addWidget(self.zStackBox, 4, 2)
        grid.addWidget(self.twoFociBox, 4, 6)
        grid.addWidget(self.zStepFromLabel, 3, 4)
        grid.addWidget(self.zStepFromEdit, 4, 4)
        grid.addWidget(self.zStepToLabel, 3, 5)
        grid.addWidget(self.zStepToEdit, 4, 5)
        # grid.addWidget(self.focusDataBox, 4, 0, 1, 2)
        grid.addWidget(self.calibFromLabel, 1, 0)
        grid.addWidget(self.calibFromEdit, 1, 1)
        grid.addWidget(self.calibToLabel, 2, 0)
        grid.addWidget(self.calibToEdit, 2, 1)
        grid.addWidget(self.calibCurveButton, 3, 2)
        grid.addWidget(self.positionLabel, 1, 6)
        grid.addWidget(self.positionEdit, 1, 7)
        grid.addWidget(self.positionSetButton, 2, 6, 1, 2)
        grid.addWidget(self.camDialogButton, 3, 6, 1, 2)

    def setKp(self, kp):
        self.kpEdit.setText(str(kp))

    def setKi(self, ki):
        self.kiEdit.setText(str(ki))


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
