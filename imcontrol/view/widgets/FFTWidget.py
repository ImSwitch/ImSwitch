import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class FFTWidget(Widget):
    """ Displays the FFT transform of the image. """

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigChangePosClicked = QtCore.Signal()
    sigPosChanged = QtCore.Signal(float)  # (pos)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    sigResized = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.showCheck = QtWidgets.QCheckBox('Show FFT')
        self.showCheck.setCheckable = True
        self.changePosButton = guitools.BetterPushButton('Period (pix)')
        self.linePos = QtWidgets.QLineEdit('4')
        self.lineRate = QtWidgets.QLineEdit('0')
        self.labelRate = QtWidgets.QLabel('Update rate')

        # Vertical and horizontal lines
        self.vline = pg.InfiniteLine()
        self.hline = pg.InfiniteLine()
        self.rvline = pg.InfiniteLine()
        self.lvline = pg.InfiniteLine()
        self.uhline = pg.InfiniteLine()
        self.dhline = pg.InfiniteLine()

        # Viewbox
        self.cwidget = pg.GraphicsLayoutWidget()
        self.vb = self.cwidget.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = guitools.OptimizedImageItem(axisOrder='row-major')
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.hist.gradient.loadPreset('greyclip')
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.cwidget.addItem(self.hist, row=1, col=2)

        # Add lines to viewbox
        self.vb.addItem(self.vline)
        self.vb.addItem(self.hline)
        self.vb.addItem(self.lvline)
        self.vb.addItem(self.rvline)
        self.vb.addItem(self.uhline)
        self.vb.addItem(self.dhline)

        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.cwidget, 0, 0, 1, 6)
        grid.addWidget(self.showCheck, 1, 0, 1, 1)
        grid.addWidget(self.changePosButton, 2, 0, 1, 1)
        grid.addWidget(self.linePos, 2, 1, 1, 1)
        grid.addWidget(self.labelRate, 2, 2, 1, 1)
        grid.addWidget(self.lineRate, 2, 3, 1, 1)
        # grid.setRowMinimumHeight(0, 300)

        # Connect signals
        self.showCheck.toggled.connect(self.sigShowToggled)
        self.changePosButton.clicked.connect(self.sigChangePosClicked)
        self.linePos.textChanged.connect(
            lambda: self.sigPosChanged.emit(self.getPos())
        )
        self.lineRate.textChanged.connect(
            lambda: self.sigUpdateRateChanged.emit(self.getUpdateRate())
        )
        self.vb.sigResized.connect(self.sigResized)

    def getShowChecked(self):
        return self.showCheck.isChecked()

    def getPos(self):
        return float(self.linePos.text())

    def getUpdateRate(self):
        return float(self.lineRate.text())