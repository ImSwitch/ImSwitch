from pyqtgraph.Qt import QtCore, QtWidgets

from .basewidgets import Widget


class MotCorrWidget(Widget):
    """ Widget containing objective motorized correction collar interface. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.motcorrControl = QtWidgets.QFrame()
        self.motcorrControl.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Raised)

        self.motcorrControl.name = QtWidgets.QLabel('Glycerol motCorr [%]')
        self.motcorrControl.name.setTextFormat(QtCore.Qt.RichText)
        self.motcorrControl.name.setAlignment(QtCore.Qt.AlignCenter)

        self.motcorrControl.rangeLabel = QtWidgets.QLabel('Range: 0-100%')
        self.motcorrControl.rangeLabel.setFixedWidth(100)
        self.motcorrControl.setPointEdit = QtWidgets.QLineEdit(str(0))
        self.motcorrControl.setPointEdit.setFixedWidth(100)

        prange = (0, 100)
        self.motcorrControl.maxpower = QtWidgets.QLabel(str(prange[1]))
        self.motcorrControl.maxpower.setAlignment(QtCore.Qt.AlignCenter)
        self.motcorrControl.minpower = QtWidgets.QLabel(str(prange[0]))
        self.motcorrControl.minpower.setAlignment(QtCore.Qt.AlignCenter)
        self.motcorrControl.slider = QtWidgets.QSlider(QtCore.Qt.Vertical, self)
        self.motcorrControl.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.motcorrControl.slider.setMinimum(prange[0])
        self.motcorrControl.slider.setMaximum(prange[1])
        self.motcorrControl.slider.setTickInterval(5)
        self.motcorrControl.slider.setSingleStep(0.1)
        self.motcorrControl.slider.setValue(50)

        gridMotCorr = QtWidgets.QGridLayout()
        self.motcorrControl.setLayout(gridMotCorr)
        gridMotCorr.addWidget(self.motcorrControl.name, 0, 0)
        gridMotCorr.addWidget(self.motcorrControl.rangeLabel, 3, 0)
        gridMotCorr.addWidget(self.motcorrControl.setPointEdit, 4, 0)
        gridMotCorr.addWidget(self.motcorrControl.maxpower, 1, 1)
        gridMotCorr.addWidget(self.motcorrControl.slider, 2, 1, 5, 1)
        gridMotCorr.addWidget(self.motcorrControl.minpower, 7, 1)
        # gridMotCorr.setRowMinimumHeight(2, 60)
        # gridMotCorr.setRowMinimumHeight(6, 60)

        # GUI layout below
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.motcorrControl, 0, 0)
        # grid.setColumnMinimumWidth(0, 75)
        # grid.setRowMinimumHeight(0,75)


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
