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
    """ Widget controlling OPT alignment widget to acquire 2 pairs of
     counter-projections and analyze the motor shaft and sample alignment
     in respect to the camera's middle pixel.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.scanPar = {}

    def initControls(self):
        """ Initializes the controls for the widget. """
        self.widgetLayout()

        self.scanPar['StopButton'].setEnabled(True)
        self.scanPar['LineIdx'].setEnabled(False)
        self.scanPar['xShift'].setEnabled(False)
        self.scanPar['Threshold'].setEnabled(False)
        self.scanPar['CounterProjPair'].setEnabled(False)
        self.scanPar['Modality'].setEnabled(False)

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
        """ Returns the user-input shift for the horizontal cuts."""
        return self.scanPar['xShift'].value()

    def getExpModality(self) -> str:
        """ Returns the user-selected modality for the experiment."""
        return self.scanPar['Modality'].currentText()

    def getThreshold(self) -> float:
        """ Returns the user-input threshold for the horizontal cuts."""
        return self.scanPar['Threshold'].value()

    def getProjectionPairFlag(self) -> int:
        """ Returns the user-selected projection pair for the experiment."""
        return self.scanPar['CounterProjPair'].currentIndex()

    def getRotatorIdx(self) -> int:
        """Returns currently selected rotator for the OPT """
        return self.scanPar['Rotator'].currentIndex()

    def _clearPlots(self):
        """Clears all pyqtgraph plots."""
        self.plotHorCuts.clear()  # clear plotWidget first
        self.plotHorCuts.addLegend()
        self.plotHorCuts.setTitle('Horizontal cuts', color='b')

        self.plotCC.clear()  # clear plotWidget first
        self.plotCC.addLegend()
        self.plotCC.setTitle('Norm. cross-correlation', color='b')

    def _plotHorCuts(self, cor):
        """Plots horizontal cuts for user selected horizontal camera line
        pixel.

        Args:
            cor (object): AlignCOR class object containing all alignment data.
        """
        self.plotHorCuts.plot(
            self.normalize(cor.horCuts[0], '01'),
            name=f'single {cor.params["lineIdx"]}',
            pen=pg.mkPen('r'))
        self.plotHorCuts.plot(
            self.normalize(cor.horCuts[1], '01'),
            name=f'merge {cor.params["lineIdx"]}',
            pen=pg.mkPen('b'))

    def _plotCC(self, cor):
        """Plots normalized cross-correlation.

        Args:
            cor (object): AlignCOR class object containing all alignment data.
        """
        self.plotCC.plot(
            cor.crossCorr/np.amax(cor.crossCorr),
            name=f'{cor.params["lineIdx"]}',
        )

    # def _plotCumSum(self, cor):
    #     """Plot the cumulative sums of the horizontal cuts.

    #     Args:
    #         cor (object): AlignCOR class object containing all alignment data.
    #     """
    #     self.plotCumSum.createFigure(cor)

    def _plotThreshMiddle(self, cor):
        """Plot the thresholded middle pixel of the horizontal cuts.

        Args:
            cor (object): AlignCOR class object containing all alignment data.
        """
        self.plotThreshMiddle.createFigure2(cor)

    # TODO: this can be now refactored to just int
    def execPlots(self, cor: object) -> None:
        """
        Plot horizontal cuts and normalized cross-correlation.

        Args:
            idxList (list[int]): List of indices.
            cor (object): AlignCOR class object containing all alignment data.
        """
        self._clearPlots()

        self._plotHorCuts(cor)
        self._plotCC(cor)
        # self._plotCumSum(cor)
        self._plotThreshMiddle(cor)

        # plot center vertical line for cross correlations
        self.plotCC.addItem(
            pg.InfiniteLine(cor.center_px,
                            angle=90,
                            pen=pg.mkPen(width=2, color='r'))
        )

        # plot horizontal line for at 1
        self.plotCC.addItem(
            pg.InfiniteLine(1,
                            angle=0,
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
        self.plotHorCuts = pg.PlotWidget()
        self.plotCC = pg.PlotWidget()
        self.plotCumSum = CumSumCanvas()
        self.plotThreshMiddle = CumSumCanvas()

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

        # projection pair
        self.scanPar['CounterProjPair'] = QtWidgets.QComboBox()
        self.scanPar['CounterProjPair'].addItems(['Pair 1 (0, 180 deg)',
                                                  'Pair 2 (90, 270 deg)'])
        self.scanPar['CounterProjPair'].setToolTip(
            'Select a pair of counter projections which are analyzed'
        )

        # spinbox for threshold in percents
        self.scanPar['Threshold'] = QtWidgets.QDoubleSpinBox()
        self.scanPar['Threshold'].setRange(0, 100)
        self.scanPar['Threshold'].setValue(1.0)
        self.scanPar['Threshold'].setSingleStep(0.5)
        self.scanPar['Threshold'].setToolTip(
            'Intensity threshold for the sample center'
            ' calculation from the Horizontal cuts'
        )

        self.scanPar['Modality'] = QtWidgets.QComboBox()
        self.scanPar['Modality'].setToolTip(
            'Whether you use transmission or FL for alignment')
        self.scanPar['ModalityLabel'] = QtWidgets.QLabel('Modality')
        self.scanPar['Modality'].addItems(['Transmission', 'Fluorescence'])

        self.tabs = QtWidgets.QTabWidget()

        # first tab is the merge of counter projections
        self.tabMerge = QtWidgets.QWidget()
        self.grid1 = QtWidgets.QGridLayout()
        self.tabMerge.setLayout(self.grid1)
        self.grid1.addWidget(self.plotMerge, 0, 0)
        self.tabs.addTab(self.tabMerge, 'Merge')

        # 2. tab of horizontal cuts
        self.tabHorCuts = QtWidgets.QWidget()
        self.grid2 = QtWidgets.QGridLayout()
        self.tabHorCuts.setLayout(self.grid2)
        self.grid2.addWidget(self.plotHorCuts, 0, 0)
        # add tab to tabs
        self.tabs.addTab(self.tabHorCuts, 'Horizontal cuts')

        # 3. tab of cross-correlation
        self.tabCorr = QtWidgets.QWidget()
        self.grid3 = QtWidgets.QGridLayout()
        self.tabCorr.setLayout(self.grid3)
        self.grid3.addWidget(self.plotCC, 0, 0)
        # add tab to tabs
        self.tabs.addTab(self.tabCorr, 'Cross-correlation')
        # 4. tab of cumsum of intensities
        # self.tabCumSum = QtWidgets.QWidget()
        # self.grid4 = QtWidgets.QGridLayout()
        # self.tabCumSum.setLayout(self.grid4)
        # self.grid4.addWidget(self.plotCumSum, 0, 0)
        # self.tabs.addTab(self.tabCumSum, 'Cumulative Sums')

        # 5. tab of thresholded center px
        self.tabThreshMiddle = QtWidgets.QWidget()
        self.grid5 = QtWidgets.QGridLayout()
        self.tabThreshMiddle.setLayout(self.grid5)
        self.grid5.addWidget(self.plotThreshMiddle, 0, 0)
        self.tabs.addTab(self.tabThreshMiddle, 'Thresholded middle PX')

        # separator
        self.separatorLine = QtWidgets.QFrame()
        self.separatorLine.setFrameShape(QtWidgets.QFrame.HLine)

        currentRow = 0
        self.grid.addWidget(self.scanPar['StartButton'], currentRow, 0)
        self.grid.addWidget(self.scanPar['StopButton'], currentRow, 1)

        self.grid.addWidget(self.scanPar['RotatorLabel'], currentRow, 2)
        self.grid.addWidget(self.scanPar['Rotator'], currentRow, 3)

        currentRow += 1
        self.grid.addWidget(self.scanPar['ModalityLabel'], currentRow, 0)
        self.grid.addWidget(self.scanPar['Modality'], currentRow, 1)
        currentRow += 1

        # separator
        self.grid.addWidget(self.separatorLine, currentRow, 0, 1, -1)

        currentRow += 1
        self.grid.addWidget(QtWidgets.QLabel('Pair'), currentRow, 0)
        self.grid.addWidget(self.scanPar['CounterProjPair'], currentRow, 1)

        self.grid.addWidget(QtWidgets.QLabel('Line index'),
                            currentRow, 2)
        self.grid.addWidget(self.scanPar['LineIdx'], currentRow, 3)

        currentRow += 1

        self.grid.addWidget(self.scanPar['xShiftLabel'], currentRow, 0)
        self.grid.addWidget(self.scanPar['xShift'], currentRow, 1)

        self.grid.addWidget(QtWidgets.QLabel('Threshold (%)'), currentRow, 2)
        self.grid.addWidget(self.scanPar['Threshold'], currentRow, 3)

        currentRow += 1
        self.grid.addWidget(self.tabs, currentRow, 0, 1, -1)


class CumSumCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=6):
        self.fig = Figure(figsize=(width, height))
        self.ax1 = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    # def createFigure(self, cor) -> None:
    #     """Create the figure of the cumulative sums plots.

    #     Args:
    #         cor (object): AlignCOR class object containing alignment data.
    #     """
    #     self.ax1.clear()
    #     self.ax1.cla()

    #     # add plot 1, normalized by the first cumsum
    #     self.ax1.plot(cor.s1, lw=3, label='Proj')
    #     self.ax1.plot(cor.s2, label='Counter Proj')

    #     # plot middle indices
    #     self.ax1.axvline(cor.s1middle, color='C0', lw=1,
    #                      label=f'middle 1: {np.round(cor.s1middle, 2)}')
    #     self.ax1.axvline(cor.s2middle, color='C1', lw=1,
    #                      label=f'middle 2: {np.round(cor.s2middle, 2)}')

    #     self.ax1.legend()
    #     self.ax1.set_xlabel('pixel index')
    #     self.ax1.set_ylabel('Normalized cum Sum')
    #     self.ax1.set_title(f'diff={np.round(cor.diff, 2)}')

    #     # for plot updates
    #     self.fig.canvas.draw_idle()

    def createFigure2(self, cor) -> None:
        """Create the figure of the thresholded middle pixel plots.

        Args:
            cor (object): AlignCOR class object containing alignment middle
                pixel data.
        """
        self.ax1.clear()
        self.ax1.cla()

        # add plot 1
        self.ax1.plot(cor.invHorCuts[0], lw=3, label='_nolegend_')
        self.ax1.plot(cor.invHorCuts[1], lw=2, label='_nolegend_')
        # plot middle indices
        self.ax1.axvline(cor.s1meanIdx, color='C0', lw=1,
                         label=f'middle 1: {np.round(cor.s1meanIdx, 2)}')
        self.ax1.axvline(cor.s2meanIdx, color='C1', lw=1,
                         label=f'middle 2: {np.round(cor.s2meanIdx, 2)}')
        # plot threshold
        self.ax1.axhline(cor.img_thresh, color='b', lw=1, label='_nolegend_')

        self.ax1.legend()
        self.ax1.set_xlabel('pixel index')
        self.ax1.set_ylabel('camera counts')

        self.ax1.set_title(
            f'Middle PX = {np.round(len(cor.invHorCuts[0])/2, 1)}')

        self.fig.canvas.draw_idle()


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
