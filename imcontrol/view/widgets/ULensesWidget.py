import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui

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
        self.ulensesCheck = QtGui.QCheckBox('Show uLenses')
        self.xEdit = QtGui.QLineEdit(self._defaultPreset.uLenses.xOffset)
        self.yEdit = QtGui.QLineEdit(self._defaultPreset.uLenses.yOffset)
        self.pxEdit = QtGui.QLineEdit(self._defaultPreset.uLenses.pixelSize)
        self.upEdit = QtGui.QLineEdit(self._defaultPreset.uLenses.periodicity)
        self.ulensesPlot = pg.ScatterPlotItem()

        # Add elements to GridLayout
        ulensesLayout = QtGui.QGridLayout()
        self.setLayout(ulensesLayout)
        ulensesLayout.addWidget(QtGui.QLabel('Pixel Size'), 0, 0)
        ulensesLayout.addWidget(self.pxEdit, 0, 1)
        ulensesLayout.addWidget(QtGui.QLabel('Periodicity'), 1, 0)
        ulensesLayout.addWidget(self.upEdit, 1, 1)
        ulensesLayout.addWidget(QtGui.QLabel('X offset'), 2, 0)
        ulensesLayout.addWidget(self.xEdit, 2, 1)
        ulensesLayout.addWidget(QtGui.QLabel('Y offset'), 3, 0)
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