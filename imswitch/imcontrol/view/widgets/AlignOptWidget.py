from qtpy import QtWidgets
import pyqtgraph as pg
import numpy as np

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget

# import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas
)


class AlignOptWidget(Widget):
    """ Widget controlling OPT experiments where a rotation stage is triggered
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.scanPar = {}

    def initControls(self):
        """ Initializes the controls for the widget. """
        self.widgetLayout()

    def plotCounterProj(self, img: np.ndarray) -> None:
        """
        This method plots the counter projection image,
        which is a merge of the given image.

        Parameters:
        img (np.ndarray): The image to be plotted.

        Returns:
        None
        """
        self.plotMerge.setImage(img)

    def getHorCutsIdx(self) -> int:
        """ Returns the user-input list of indeces for horizontal cuts."""
        return self.scanPar['LineIdx'].value()

    def getShift(self) -> int:
        return self.scanPar['xShift'].value()

    def getProjectionPairFlag(self) -> int:
        return self.scanPar['CounterProjPair'].currentIndex()

    def getRotatorIdx(self) -> int:
        """Returns currently selected rotator for the OPT """
        return self.scanPar['Rotator'].currentIndex()

    def _clearPlots(self):
        self.plotHorCuts.clear()  # clear plotWidget first
        self.plotHorCuts.addLegend()
        self.plotHorCuts.setTitle('Horizontal cuts', color='b')

        self.plotCC.clear()  # clear plotWidget first
        self.plotCC.addLegend()
        self.plotCC.setTitle('Norm. cross-correlation', color='b')

    def _plotHorCuts(self, cor):
        self.plotHorCuts.plot(
            self.normalize(cor.horCuts[0], '01'),
            name=f'single {cor.params["lineIdx"]}',
            pen=pg.mkPen('r'))
        self.plotHorCuts.plot(
            self.normalize(cor.horCuts[1], '01'),
            name=f'merge {cor.params["lineIdx"]}',
            pen=pg.mkPen('b'))

    def _plotCC(self, cor):
        # I plot normalized, perhaps not great
        # Not working
        self.plotCC.plot(
            cor.crossCorr/np.amax(cor.crossCorr),
            name=f'{cor.params["lineIdx"]}',
        )

    def _plotCumSum(self, cor):
        self.plotCumSum.createFigure(cor)

    def _plotDiffCC(self, cor):
        self.plotCumSum.createFigure2(cor)

    # TODO: this can be now refactored to just int
    def execPlots(self, cor: object) -> None:
        """
        Plot horizontal cuts and normalized cross-correlation.

        Args:
            idxList (list[int]): List of indices.
            cor (object): Object containing horizontal cuts and
                cross-correlation data.
        """
        self._clearPlots()

        self._plotHorCuts(cor)
        self._plotCC(cor)
        self._plotCumSum(cor)
        self._plotDiffCC(cor)

        # plot center vertical line for cross correlations
        self.plotCC.addItem(
            pg.InfiniteLine(cor.center_px,
                            angle=90,
                            pen=pg.mkPen(width=2, color='r'))
        )

    def normalize(self, data: np.array, mode: str = '01') -> np.array:
        """this works for positive cuts and images, negative
        values are not reliably taken care of at this point.

        Args:
            data (_type_): _description_
            mode (str, optional): Mode of normalization.
                '01': normalizes between 0 and 1
                'max': just divides by max
                Defaults to '01'.

        Returns:
            np.array: normalized data, same shape as data
        """
        if mode == '01':
            mn = np.amin(data)
            return (data - mn)/abs(np.amax(data) - mn)
        elif mode == 'max':
            return data / np.amax(data)
        else:
            raise ValueError('Unknown mode of normalization')

    def widgetLayout(self):
        """ Layout of the widget """
        self.scanPar['StartButton'] = guitools.BetterPushButton('Acquire')
        self.scanPar['StartButton'].setToolTip(
            'Acquires 0 and 180 deg projections to compare and autocorrelate'
            ' horizontal cuts to allow for COR alignment.'
        )
        self.scanPar['StopButton'] = guitools.BetterPushButton('Stop')
        # tool tip
        self.scanPar['StopButton'].setToolTip('Interupt scan')
        self.scanPar['Rotator'] = QtWidgets.QComboBox()
        self.scanPar['Rotator'].setToolTip('Select rotator for the scan')
        self.scanPar['RotatorLabel'] = QtWidgets.QLabel('Rotator')

        self.plotMerge = pg.ImageView()
        self.plotMerge.setFixedWidth(400)
        self.plotMerge.setFixedHeight(300)
        self.plotHorCuts = pg.PlotWidget()
        self.plotCC = pg.PlotWidget()
        self.plotCumSum = CumSumCanvas()
        self.plotDiffCumSum = CumSumCanvas()

        self.scanPar['LineIdx'] = QtWidgets.QSpinBox()
        self.scanPar['LineIdx'].setRange(0, 10000)
        self.scanPar['LineIdx'].setValue(100)
        # tool tip
        self.scanPar['LineIdx'].setToolTip(
            'Index for horizontal cuts.'
        )
        self.scanPar['xShift'] = QtWidgets.QSpinBox()
        self.scanPar['xShift'].setValue(0)
        self.scanPar['xShift'].setRange(-70, 70)
        self.scanPar['xShift'].setSingleStep(1)
        self.scanPar['xShift'].setToolTip(
            'Shift the horizontal mirrored cut by this amount of pixels.'
            ' This provides idea how far off your COR is'
        )

        self.scanPar['xShiftLabel'] = QtWidgets.QLabel('x-Shift')
        self.scanPar['CounterProjPair'] = QtWidgets.QComboBox()
        self.scanPar['CounterProjPair'].addItems(['Pair 1 (0, 180 deg)',
                                                  'Pair 2 (90, 270 deg)'])
        self.scanPar['CounterProjPair'].setToolTip(
            'Select a pair of counter projections which hor cuts are analyzed'
        )

        self.tabs = QtWidgets.QTabWidget()

        # first tab of horizontal cuts
        self.tabHorCuts = QtWidgets.QWidget()
        self.grid2 = QtWidgets.QGridLayout()
        self.tabHorCuts.setLayout(self.grid2)
        self.grid2.addWidget(self.plotHorCuts, 0, 0)
        # add tab to tabs
        self.tabs.addTab(self.tabHorCuts, 'Horizontal cuts')

        # second tab of cross-correlation
        self.tabCorr = QtWidgets.QWidget()
        self.grid3 = QtWidgets.QGridLayout()
        self.tabCorr.setLayout(self.grid3)
        self.grid3.addWidget(self.plotCC, 0, 0)
        # add tab to tabs
        self.tabs.addTab(self.tabCorr, 'Cross-correlation')

        # third tab of cumsum of intensities
        self.tabCumSum = QtWidgets.QWidget()
        self.grid4 = QtWidgets.QGridLayout()
        self.tabCumSum.setLayout(self.grid4)
        self.grid4.addWidget(self.plotCumSum, 0, 0)
        self.tabs.addTab(self.tabCumSum, 'Cumulative Sums')

        # 4. tab of diff of cumsums
        self.tabDiffCumSum = QtWidgets.QWidget()
        self.grid5 = QtWidgets.QGridLayout()
        self.tabDiffCumSum.setLayout(self.grid5)
        self.grid5.addWidget(self.plotDiffCumSum, 0, 0)
        self.tabs.addTab(self.tabDiffCumSum, 'Diff Cum. Sums')

        currentRow = 0
        self.grid.addWidget(self.scanPar['StartButton'], currentRow, 0)
        self.grid.addWidget(self.scanPar['StopButton'], currentRow, 1)

        self.grid.addWidget(self.scanPar['RotatorLabel'], currentRow, 2)
        self.grid.addWidget(self.scanPar['Rotator'], currentRow, 3)

        currentRow += 1
        self.grid.addWidget(self.plotMerge, currentRow, 0, 1, -1)

        currentRow += 1
        self.grid.addWidget(QtWidgets.QLabel('Line index'),
                            currentRow, 0)
        self.grid.addWidget(self.scanPar['LineIdx'], currentRow, 1)

        # currentRow += 1
        self.grid.addWidget(QtWidgets.QLabel('Pair'), currentRow, 2)
        self.grid.addWidget(self.scanPar['CounterProjPair'], currentRow, 3)

        currentRow += 1
        self.grid.addWidget(self.scanPar['xShiftLabel'], currentRow, 0)
        self.grid.addWidget(self.scanPar['xShift'], currentRow, 1)

        currentRow += 1
        self.grid.addWidget(self.tabs, currentRow, 0, 1, -1)


class CumSumCanvas(FigureCanvas):
    def __init__(self, parent=None, width=400, height=300):
        self.fig = Figure(figsize=(width, height))
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def createFigure(self, cor) -> None:
        """Create report plot.

        Args:
            report (dict): report dictionary.
        """
        # self.ax1.clear()
        self.ax1.clear()
        self.ax2.clear()

        # add plot 1
        self.ax1.plot(cor.s1, lw=3, label='cumsum 1 mirr')
        self.ax1.plot(cor.s2, label='cumsum 2 mirr')

        self.ax1.legend()
        self.ax1.set_xlabel('pixel index')
        self.ax1.set_ylabel('camera counts')
        self.ax1.set_title(f'diff={cor.diff}')

        # add plot 2
        self.ax2.plot(cor.s1_raw, lw=3, label='cumsum 1 raw')
        self.ax2.plot(cor.s2_raw, label='cumsum 2 raw')

        self.ax2.legend()
        self.ax2.set_xlabel('pixel index')
        self.ax2.set_ylabel('camera counts')
        self.ax2.set_title(f'diff={cor.diff_raw}')

        self.fig.canvas.draw_idle()

    def createFigure2(self, cor) -> None:
        self.ax1.clear()
        self.ax2.clear()

        # add plot 1
        self.ax1.plot(abs(cor.s1 - cor.s2), lw=3, label='Diff cumsums')

        self.ax1.legend()
        self.ax1.set_xlabel('pixel index')
        self.ax1.set_ylabel('camera counts')
        self.ax1.set_title(f'diff={cor.diff}')

        # add plot 2
        self.ax2.plot(abs(cor.s1_raw - cor.s2_raw), lw=3, label='Diff cumsums')

        self.ax2.legend()
        self.ax2.set_xlabel('pixel index')
        self.ax2.set_ylabel('camera counts')
        self.ax2.set_title(f'diff={cor.diff_raw}')


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
