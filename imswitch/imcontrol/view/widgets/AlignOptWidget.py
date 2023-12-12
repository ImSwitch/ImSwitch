from qtpy import QtCore, QtWidgets
import numpy as np
import pyqtgraph as pg

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import NapariHybridWidget
from .basewidgets import Widget


class AlignOptWidget(Widget):
    """ Widget controlling OPT experiments where a rotation stage is triggered
    """

    # sigRotStepDone = QtCore.Signal()
    # sigRunScanClicked = QtCore.Signal()
    # sigScanDone = QtCore.Signal()

    # def __post_init__(self, *args, **kwargs):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.scanPar = {}
        self.enabled = True
        self.layer = None

    def initControls(self):
        # populate widget
        self.widgetLayout()

    def plotCounterProj(self, img):
        self.plotMerge.setImage(img)

    def getHorCutsIdxList(self):
        """ Returns the user-input list of indeces for horizontal cuts."""
        return self.scanPar['LineIdxsEdit'].text()

    def setRotStepEnable(self, enabled):
        """ For inactivating during scanning when ActivateButton pressed
        and waiting for a scan. When scan finishes, enable again. """
        self.scanPar['RotStepsEdit'].setEnabled(enabled)

    def widgetLayout(self):
        self.scanPar['StartButton'] = guitools.BetterPushButton('Start')
        self.scanPar['StopButton'] = guitools.BetterPushButton('Stop')
        self.plotMerge = pg.ImageView()
        self.plotHorCuts = pg.PlotWidget()

        self.scanPar['LineIdxsEdit'] = QtWidgets.QLineEdit('100 1000')
        self.scanPar['PlotHorCuts'] = guitools.BetterPushButton('Plot')

        currentRow = 0
        self.grid.addWidget(self.scanPar['StartButton'], currentRow, 0)
        self.grid.addWidget(self.scanPar['StopButton'], currentRow, 1)

        currentRow += 1
        self.grid.addWidget(self.plotMerge, currentRow, 0, 1, -1)

        currentRow += 1
        self.grid.addWidget(QtWidgets.QLabel('Line indeces'),
                            currentRow, 0)
        self.grid.addWidget(self.scanPar['LineIdxsEdit'], currentRow, 1)
        self.grid.addWidget(self.scanPar['PlotHorCuts'], currentRow, 2)

        currentRow += 1
        self.grid.addWidget(self.plotHorCuts, currentRow, 0, 1, -1)

        # self.grid.addItem(QtWidgets.QSpacerItem(10, 10,
        #                   QtWidgets.QSizePolicy.Minimum,
        #                   QtWidgets.QSizePolicy.Expanding),
        #                   currentRow+1, 0, 1, -1)


# Copyright (C) 2020-2022 ImSwitch developers
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
