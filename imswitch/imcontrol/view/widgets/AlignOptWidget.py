from qtpy import QtWidgets
import pyqtgraph as pg

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class AlignOptWidget(Widget):
    """ Widget controlling OPT experiments where a rotation stage is triggered
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.scanPar = {}

    def initControls(self):
        self.widgetLayout()

    def plotCounterProj(self, img):
        self.plotMerge.setImage(img)

    def getHorCutsIdxList(self):
        """ Returns the user-input list of indeces for horizontal cuts."""
        return self.scanPar['LineIdxsEdit'].text()

    def getRotatorIdx(self):
        """Returns currently selected rotator for the OPT
        """
        return self.scanPar['Rotator'].currentIndex()

    def widgetLayout(self):
        self.scanPar['StartButton'] = guitools.BetterPushButton('Acquire')
        self.scanPar['StartButton'].setToolTip(
            'Acquires 0 and 180 deg projections to compare and autocorrelate \
horizontal cuts to allow for COR alignment.'
        )
        self.scanPar['StopButton'] = guitools.BetterPushButton('Stop')
        self.scanPar['StopButton'].setToolTip('Interupt scan')
        self.scanPar['Rotator'] = QtWidgets.QComboBox()
        self.scanPar['Rotator'].setToolTip('Select rotator for the scan')
        self.scanPar['RotatorLabel'] = QtWidgets.QLabel('Rotator')

        self.plotMerge = pg.ImageView()
        self.plotHorCuts = pg.PlotWidget()
        self.plotCC = pg.PlotWidget()

        self.scanPar['LineIdxsEdit'] = QtWidgets.QLineEdit('100 50')
        self.scanPar['xShift'] = QtWidgets.QSpinBox()
        self.scanPar['xShift'].setValue(0)
        self.scanPar['xShift'].setRange(-50, 50)
        self.scanPar['xShift'].setSingleStep(1)

        self.scanPar['xShiftLabel'] = QtWidgets.QLabel('x-Shift')
        self.scanPar['PlotHorCuts'] = guitools.BetterPushButton('Plot')

        currentRow = 0
        self.grid.addWidget(self.scanPar['StartButton'], currentRow, 0)
        self.grid.addWidget(self.scanPar['StopButton'], currentRow, 1)

        self.grid.addWidget(self.scanPar['RotatorLabel'], currentRow, 2)
        self.grid.addWidget(self.scanPar['Rotator'], currentRow, 3)

        currentRow += 1
        self.grid.addWidget(self.plotMerge, currentRow, 0, 1, -1)

        currentRow += 1
        self.grid.addWidget(QtWidgets.QLabel('Line indeces'),
                            currentRow, 0)
        self.grid.addWidget(self.scanPar['LineIdxsEdit'], currentRow, 1)
        self.grid.addWidget(self.scanPar['PlotHorCuts'], currentRow, 2)

        currentRow += 1
        self.grid.addWidget(self.scanPar['xShiftLabel'], currentRow, 0)
        self.grid.addWidget(self.scanPar['xShift'], currentRow, 1)

        currentRow += 1
        self.grid.addWidget(self.plotHorCuts, currentRow, 0, 1, -1)

        currentRow += 1
        self.grid.addWidget(self.plotCC, currentRow, 0, 1, -1)


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
