from qtpy import QtCore, QtWidgets

from imswitch.imcommon.view.guitools import naparitools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class ULensesWidget(NapariHybridWidget):
    """ Alignment widget that shows a grid of points on top of the image in the viewbox."""

    sigULensesClicked = QtCore.Signal()
    sigUShowLensesChanged = QtCore.Signal(bool)  # (enabled)
    sigLocalizeBtnClicked = QtCore.Signal()

    def __post_init__(self):
        # Graphical Elements
        self.ulensesButton = guitools.BetterPushButton('uLenses')
        self.ulensesCheck = QtWidgets.QCheckBox('Show uLenses')
        self.localizeBtn = guitools.BetterPushButton('Auto Localize')
        self.xEdit = QtWidgets.QLineEdit('0')
        self.yEdit = QtWidgets.QLineEdit('0')
        self.pxEdit = QtWidgets.QLineEdit('77')
        self.upxEdit = QtWidgets.QLineEdit('849')
        self.upyEdit = QtWidgets.QLineEdit('847')

        # Vispy visual to render in napari
        self.ulensesPlot = naparitools.VispyScatterVisual(color='red', symbol='x')
        self.ulensesPlot.hide()
        self.addItemToViewer(self.ulensesPlot)

        # Add elements to GridLayout
        ulensesLayout = QtWidgets.QGridLayout()
        self.setLayout(ulensesLayout)
        ulensesLayout.addWidget(QtWidgets.QLabel('Pixel Size'), 0, 0)
        ulensesLayout.addWidget(self.pxEdit, 0, 1)
        ulensesLayout.addWidget(QtWidgets.QLabel('Periodicity X'), 1, 0)
        ulensesLayout.addWidget(self.upxEdit, 1, 1)
        ulensesLayout.addWidget(QtWidgets.QLabel('Periodicity Y'), 2, 0)
        ulensesLayout.addWidget(self.upyEdit, 2, 1)
        ulensesLayout.addWidget(QtWidgets.QLabel('X offset'), 3, 0)
        ulensesLayout.addWidget(self.xEdit, 3, 1)
        ulensesLayout.addWidget(QtWidgets.QLabel('Y offset'), 4, 0)
        ulensesLayout.addWidget(self.yEdit, 4, 1)
        ulensesLayout.addWidget(self.ulensesButton, 5, 0)
        ulensesLayout.addWidget(self.ulensesCheck, 5, 1)
        ulensesLayout.addWidget(self.localizeBtn, 5, 2)

        # Connect signals
        self.ulensesButton.clicked.connect(self.sigULensesClicked)
        self.ulensesCheck.toggled.connect(self.sigUShowLensesChanged)
        self.localizeBtn.clicked.connect(self.sigLocalizeBtnClicked)

    def setParameters(self, x=None,y=None,px=None,upx=None,upy=None):
        """ Programatically updates parameters"""
        if x is not None:
            self.xEdit.setText(str(x))
        if y is not None:
            self.yEdit.setText(str(y))
        if px is not None:
            self.pxEdit.setText(str(px))
        if upx is not None:
            self.upxEdit.setText(str(upx))
        if upy is not None:
            self.upyEdit.setText(str(upy))
        


    def getParameters(self):
        """ Returns the X offset, Y offset, pixel size, and periodicity
        parameters respectively set by the user."""
        return (float(self.xEdit.text()),
                float(self.yEdit.text()),
                float(self.pxEdit.text()),
                float(self.upxEdit.text()),
                float(self.upyEdit.text()))

    def getPlotGraphicsItem(self):
        return self.ulensesPlot

    def setData(self, x, y):
        """ Updates plot with new parameters. """
        self.ulensesPlot.setData(x=x, y=y)

    def setULensesVisible(self, visible):
        """ Updates visibility of plot. """
        self.ulensesPlot.setVisible(visible)


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
