import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class ULensesWidget(Widget):
    """ Alignment widget that shows a grid of points on top of the image in the viewbox."""

    sigULensesClicked = QtCore.Signal()
    sigUShowLensesChanged = QtCore.Signal(bool)  # (enabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical Elements
        self.ulensesButton = guitools.BetterPushButton('uLenses')
        self.ulensesCheck = QtWidgets.QCheckBox('Show uLenses')
        self.xEdit = QtWidgets.QLineEdit(self._defaultPreset.uLenses.xOffset)
        self.yEdit = QtWidgets.QLineEdit(self._defaultPreset.uLenses.yOffset)
        self.pxEdit = QtWidgets.QLineEdit(self._defaultPreset.uLenses.pixelSize)
        self.upEdit = QtWidgets.QLineEdit(self._defaultPreset.uLenses.periodicity)
        self.ulensesPlot = pg.ScatterPlotItem()

        # Add elements to GridLayout
        ulensesLayout = QtWidgets.QGridLayout()
        self.setLayout(ulensesLayout)
        ulensesLayout.addWidget(QtWidgets.QLabel('Pixel Size'), 0, 0)
        ulensesLayout.addWidget(self.pxEdit, 0, 1)
        ulensesLayout.addWidget(QtWidgets.QLabel('Periodicity'), 1, 0)
        ulensesLayout.addWidget(self.upEdit, 1, 1)
        ulensesLayout.addWidget(QtWidgets.QLabel('X offset'), 2, 0)
        ulensesLayout.addWidget(self.xEdit, 2, 1)
        ulensesLayout.addWidget(QtWidgets.QLabel('Y offset'), 3, 0)
        ulensesLayout.addWidget(self.yEdit, 3, 1)
        ulensesLayout.addWidget(self.ulensesButton, 4, 0)
        ulensesLayout.addWidget(self.ulensesCheck, 4, 1)

        # Connect signals
        self.ulensesButton.clicked.connect(self.sigULensesClicked)
        self.ulensesCheck.toggled.connect(self.sigUShowLensesChanged)

    def getParameters(self):
        """ Returns the X offset, Y offset, pixel size, and periodicity
        parameters respectively set by the user."""
        return (np.float(self.xEdit.text()),
                np.float(self.yEdit.text()),
                np.float(self.pxEdit.text()),
                np.float(self.upEdit.text()))

    def getPlotGraphicsItem(self):
        return self.ulensesPlot

    def setData(self, x, y):
        """ Updates plot with new parameters. """
        self.ulensesPlot.setData(x=x, y=y, pen=pg.mkPen(None), brush='r', symbol='x')
        
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