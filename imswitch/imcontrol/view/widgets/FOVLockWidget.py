import numpy as np
import pyqtgraph as pg
from qtpy import QtWidgets
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class FOVLockWidget(Widget):
    """ Widget containing fov lock interface. """
    sigSliderExpTValueChanged = QtCore.Signal(float)  # (value)
    sigSliderGainValueChanged = QtCore.Signal(float)  # (value)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # FOV lock
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
        self.zStepFromLabel = QtWidgets.QLabel('Min z-stack step (nm)')

        self.camDialogButton = guitools.BetterPushButton('Camera Dialog')

        # FOV lock calibration
        self.calibFromLabel = QtWidgets.QLabel('From (µm)')
        self.calibFromEdit = QtWidgets.QLineEdit('49')
        self.calibToLabel = QtWidgets.QLabel('To (µm)')
        self.calibToEdit = QtWidgets.QLineEdit('51')
        self.fovCalibButton = guitools.BetterPushButton('Calib')
        self.fovCalibButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                            QtWidgets.QSizePolicy.Expanding)
        self.calibCurveButton = guitools.BetterPushButton('See calib')
        self.calibrationDisplay = QtWidgets.QLineEdit('No calibration')
        self.calibrationDisplay.setReadOnly(True)
        self.fovCalibrationWindow = FOVCalibrationWindow()

        # FOV lock graph
        self.fovLockGraph = pg.GraphicsLayoutWidget()
        self.fovLockGraph.setAntialiasing(True)
        self.fovPlot = self.fovLockGraph.addPlot(row=1, col=0)
        self.fovPlot.setLabels(bottom=('Time', 's'), left=('Laser position', 'px'))
        self.fovPlot.showGrid(x=True, y=True)
        self.fovPlotCurveX = self.fovPlot.plot(pen='y') # update from FOVLockController
        self.fovPlotCurveY = self.fovPlot.plot(pen='r') # update from FOVLockController
        # Webcam graph
        self.webcamGraph = pg.GraphicsLayoutWidget()
        self.camImg = pg.ImageItem(border='w')
        self.camImg.setImage(np.zeros((100, 100)))
        self.vb = self.webcamGraph.addViewBox(invertY=True, invertX=False)
        self.vb.setAspectLocked(True)
        self.vb.addItem(self.camImg)

        # camera settings
        valueDecimals = 1
        valueRangeExpT = (1,1200)
        valueRangeGain = (0,30)
        tickInterval = 5
        singleStep = 1
        
        # exposure slider
        self.sliderExpT = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                           decimals=valueDecimals)
        self.sliderExpT.setFocusPolicy(QtCore.Qt.NoFocus)
        valueRangeMin, valueRangeMax = valueRangeExpT

        self.sliderExpT.setMinimum(valueRangeMin)
        self.sliderExpT.setMaximum(valueRangeMax)
        self.sliderExpT.setTickInterval(50)
        self.sliderExpT.setSingleStep(singleStep)
        self.sliderExpT.setValue(10)

        # exposure slider
        self.sliderGain = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                           decimals=valueDecimals)
        self.sliderGain.setFocusPolicy(QtCore.Qt.NoFocus)
        valueRangeMin, valueRangeMax = valueRangeGain

        self.sliderGain.setMinimum(valueRangeMin)
        self.sliderGain.setMaximum(valueRangeMax)
        self.sliderGain.setTickInterval(5)
        self.sliderGain.setSingleStep(singleStep)
        self.sliderGain.setValue(10)

        # GUI layout below
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.fovLockGraph, 0, 0, 1, 9)
        grid.addWidget(self.webcamGraph, 0, 9, 4, 1)
        grid.addWidget(self.fovCalibButton, 1, 2, 2, 1)
        grid.addWidget(self.calibrationDisplay, 3, 0, 1, 2)
        grid.addWidget(self.kpLabel, 1, 3)
        grid.addWidget(self.kpEdit, 1, 4)
        grid.addWidget(self.kiLabel, 2, 3)
        grid.addWidget(self.kiEdit, 2, 4)
        grid.addWidget(self.lockButton, 1, 5, 2, 1)
        grid.addWidget(self.zStackBox, 3, 6)
        grid.addWidget(self.twoFociBox, 2, 6)
        grid.addWidget(self.zStepFromLabel, 3, 4)
        grid.addWidget(self.zStepFromEdit, 3, 5)
        grid.addWidget(self.calibFromLabel, 1, 0)
        grid.addWidget(self.calibFromEdit, 1, 1)
        grid.addWidget(self.calibToLabel, 2, 0)
        grid.addWidget(self.calibToEdit, 2, 1)
        grid.addWidget(self.calibCurveButton, 3, 2)
        grid.addWidget(self.camDialogButton, 1, 6, 1, 2)

        grid.addWidget(self.sliderExpT, 4, 0, 1, 9)
        grid.addWidget(self.sliderGain, 5, 0, 1, 9)

        # Connect signals
        self.sliderGain.valueChanged.connect(
            lambda value: self.sigSliderGainValueChanged.emit(value)
        )
        self.sliderExpT.valueChanged.connect(
            lambda value: self.sigSliderExpTValueChanged.emit(value)
        )
        self.layer = None

    def setKp(self, kp):
        self.kpEdit.setText(str(kp))

    def setKi(self, ki):
        self.kiEdit.setText(str(ki))

    def showCalibrationCurve(self, data):
        self.fovCalibrationWindow.run(data)
        self.fovCalibrationWindow.show()


class FOVCalibrationWindow(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.__fovCalibGraph = FOVCalibrationGraph()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.__fovCalibGraph, 0, 0)

    def run(self, data):
        self.__fovCalibGraph.draw(data)


class FOVCalibrationGraph(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__()
        self.plot = self.addPlot(row=1, col=0)
        self.plot.setLabels(bottom=('Set z position', 'µm'),
                            left=('Laser spot position', 'px'))
        self.plot.showGrid(x=True, y=True)

    def draw(self, data):
        self.plot.clear()
        self.positionData = data['positionData']
        self.signalData = data['signalData']
        self.poly = data['poly']
        self.plot.plot(self.positionData,
                       self.signalData, pen=None, symbol='o')
        self.plot.plot(self.positionData,
                       np.polyval(self.poly, self.positionData), pen='r')


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
