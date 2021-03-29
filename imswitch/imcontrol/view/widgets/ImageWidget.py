import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools


class ImageWidget(pg.GraphicsLayoutWidget):
    """ Widget containing viewbox that displays the new detector frames.  """

    sigResized = QtCore.Signal()
    sigLevelsChanged = QtCore.Signal()
    sigUpdateLevelsClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.levelsButton = guitools.BetterPushButton('Update Levels')
        self.levelsButton.setEnabled(False)
        self.levelsButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                        QtWidgets.QSizePolicy.Expanding)
        proxy = QtWidgets.QGraphicsProxyWidget()
        proxy.setWidget(self.levelsButton)
        self.addItem(proxy, row=0, col=2)

        # Viewbox and related elements
        self.vb = self.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = guitools.OptimizedImageItem()
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.hist.gradient.loadPreset('greyclip')
        self.grid = guitools.Grid(self.vb)
        self.crosshair = guitools.Crosshair(self.vb)
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.addItem(self.hist, row=1, col=2)
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.addItem(self.hist, row=1, col=2)
        # x and y profiles
        xPlot = self.addPlot(row=0, col=1)
        xPlot.hideAxis('left')
        xPlot.hideAxis('bottom')
        self.xProfile = xPlot.plot()
        self.ci.layout.setRowMaximumHeight(0, 40)
        xPlot.setXLink(self.vb)
        yPlot = self.addPlot(row=1, col=0)
        yPlot.hideAxis('left')
        yPlot.hideAxis('bottom')
        self.yProfile = yPlot.plot()
        self.yProfile.rotate(90)
        self.ci.layout.setColumnMaximumWidth(0, 40)
        yPlot.setYLink(self.vb)

        # Connect signals
        self.vb.sigResized.connect(self.sigResized)
        self.hist.sigLevelsChanged.connect(self.sigLevelsChanged)
        self.levelsButton.clicked.connect(self.sigUpdateLevelsClicked)
        

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
