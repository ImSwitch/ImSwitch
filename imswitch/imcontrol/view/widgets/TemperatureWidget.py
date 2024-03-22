import pyqtgraph as pg
from qtpy import QtCore, QtWidgets
import pyqtgraph as pg

from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class TemperatureWidget(NapariHybridWidget):
    """ Displays the Temperature transform of the image. """

    sigPIDToggled = QtCore.Signal(bool)  # (enabled)
    sigsliderTemperatureValueChanged = QtCore.Signal(float)  # (value)
    sigShowTemperatureToggled = QtCore.Signal(bool)  # (enabled)
    
    def __post_init__(self):

        # PID Checkbox
        self.PIDCheck = QtWidgets.QCheckBox('Enable PID')
        self.PIDCheck.setCheckable(True)

        # Measurement Checkbox
        self.measureCheck = QtWidgets.QCheckBox('Enable Measurement')
        self.measureCheck.setCheckable(True)


        # PID Values
        self.labelP = QtWidgets.QLabel('P')
        self.valP = QtWidgets.QLineEdit('100')
        self.labelI = QtWidgets.QLabel('I')
        self.valI = QtWidgets.QLineEdit('0.5')
        self.labelD = QtWidgets.QLabel('D')
        self.valD = QtWidgets.QLineEdit('0.5')

        # Temperature Labels
        self.labelTemperature = QtWidgets.QLabel('Temperature (now):')
        self.valueTemperature = QtWidgets.QLabel('0')
        self.labelTemperatureTarget = QtWidgets.QLabel('Temperature (target):')
        self.valueTemperatureTarget = QtWidgets.QLineEdit("37")

        # Temperature Graph
        self.temperatureSenseGraph = pg.GraphicsLayoutWidget()
        self.temperatureSenseGraph.setAntialiasing(True)
        self.temperaturePlot = self.temperatureSenseGraph.addPlot(row=1, col=0)
        self.temperaturePlot.setLabels(bottom=('Time', 's'), left=('temperature', 'psi'))
        self.temperaturePlot.showGrid(x=True, y=True)
        self.temperaturePlotCurve = self.temperaturePlot.plot(pen='y')

        # Layout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)

        # Adding Widgets to Layout
        grid.addWidget(self.labelP, 1, 0)
        grid.addWidget(self.valP, 1, 1)
        grid.addWidget(self.labelI, 1, 2)
        grid.addWidget(self.valI, 1, 3)
        grid.addWidget(self.labelD, 1, 4)
        grid.addWidget(self.valD, 1, 5)
        grid.addWidget(self.labelTemperature, 2, 0)
        grid.addWidget(self.valueTemperature, 2, 1)
        grid.addWidget(self.labelTemperatureTarget, 2, 2)
        grid.addWidget(self.valueTemperatureTarget, 2, 3)
        grid.addWidget(self.PIDCheck, 2, 4)
        grid.addWidget(self.measureCheck, 2, 5)
        grid.addWidget(self.temperatureSenseGraph, 3, 0, 1, 6)

        # Connect signals
        self.PIDCheck.toggled.connect(self.sigPIDToggled)
        self.measureCheck.toggled.connect(self.sigShowTemperatureToggled)
        
        # on change of the target temperature value, emit the value
        self.valueTemperatureTarget.editingFinished.connect(
            lambda: self.sigsliderTemperatureValueChanged.emit(float(self.valueTemperatureTarget.text()))
        )
        
    def getPIDValues(self):
        return float(self.valP.text()), float(self.valI.text()), float(self.valD.text())
    
    def updateTemperature(self, temperature):
        self.valueTemperature.setText(str(temperature))
        
    def updateTargetTemperatureValue(self, temperature):
        self.valueTemperatureTarget.setText(str(temperature))

    def getPIDChecked(self):
        return self.PIDCheck.isChecked()

    def getTemperatureValue(self):
        return self.valueTemperatureTarget.text()


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
