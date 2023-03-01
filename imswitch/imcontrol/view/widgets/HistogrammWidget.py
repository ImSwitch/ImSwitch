import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class HistogrammWidget(NapariHybridWidget):
    """ Displays the Histogramm transform of the image. """

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    sigSliderValueChanged = QtCore.Signal(float)  # (value)

    def __post_init__(self):

        # Focus lock graph
        self.HistogrammGraph = pg.GraphicsLayoutWidget()
        self.HistogrammGraph.setAntialiasing(True)
        self.histogrammPlot = self.HistogrammGraph.addPlot(row=1, col=0)
        self.histogrammPlot.setLabels(bottom=('Bins', 'D.U.'), left=('Intensity', 'A.U.'))
        self.histogrammPlot.showGrid(x=True, y=True)
        # update this (self.histogrammPlotCurve.setData(X,Y)) with update(focusSignal) function
        self.histogrammPlotCurve = self.histogrammPlot.plot(pen='y')
        
        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.HistogrammGraph, 0, 0, 1, 1)


    def setImage(self, im):
        if self.layer is None or self.layer.name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, name="Histogramm", blending='additive')
        self.layer.data = im


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
