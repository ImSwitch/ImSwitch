from pyqtgraph.Qt import QtCore, QtWidgets

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class PositionerWidget(Widget):
    """ Widget in control of the piezzo movement. """

    sigStepUpClicked = QtCore.Signal(str)  # (positionerName)
    sigStepDownClicked = QtCore.Signal(str)  # (positionerName)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 0
        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

    def addPositioner(self, positionerName):
        self.pars['Label' + positionerName] = QtWidgets.QLabel(f"<strong>{positionerName} = {0:.2f} µm</strong>")
        self.pars['Label' + positionerName].setTextFormat(QtCore.Qt.RichText)
        self.pars['UpButton' + positionerName] = guitools.BetterPushButton("+")
        self.pars['DownButton' + positionerName] = guitools.BetterPushButton("-")
        self.pars['StepEdit' + positionerName] = QtWidgets.QLineEdit("0.05")
        self.pars['StepUnit' + positionerName] = QtWidgets.QLabel(" µm")

        self.grid.addWidget(self.pars['Label' + positionerName], self.numPositioners, 0)
        self.grid.addWidget(self.pars['UpButton' + positionerName], self.numPositioners, 1)
        self.grid.addWidget(self.pars['DownButton' + positionerName], self.numPositioners, 2)
        self.grid.addWidget(QtWidgets.QLabel("Step"), self.numPositioners, 3)
        self.grid.addWidget(self.pars['StepEdit' + positionerName], self.numPositioners, 4)
        self.grid.addWidget(self.pars['StepUnit' + positionerName], self.numPositioners, 5)

        self.numPositioners += 1

        # Connect signals
        self.pars['UpButton' + positionerName].clicked.connect(
            lambda: self.sigStepUpClicked.emit(positionerName)
        )
        self.pars['DownButton' + positionerName].clicked.connect(
            lambda: self.sigStepDownClicked.emit(positionerName)
        )

    def getStepSize(self, positionerName):
        return float(self.pars['StepEdit' + positionerName].text())

    def updatePosition(self, positionerName, position):
        text = f"<strong>{positionerName} = {position:.2f} µm</strong>"
        self.pars['Label' + positionerName].setText(text)
        

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
