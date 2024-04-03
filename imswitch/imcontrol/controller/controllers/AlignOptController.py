import numpy as np
from scipy.signal import correlate
import pyqtgraph as pg

from imswitch.imcommon.model import initLogger
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Thread

from .ScanControllerOpt import ScanOPTWorker


class AlignOptController(ImConWidgetController):
    """ OPT alignment controller.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)
        self.optStack = np.ones((1, 1, 1))
        self.counterProj = np.ones((1, 1, 1))
        self.cor = None

        # Set up rotator in widget
        self._widget.initControls()
        self.isOptRunning = False

        # select detectors, this does not update if detector in
        # recording changes, right?
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detectorName = allDetectorNames[0]
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # rotators list
        self.rotatorsList = self._master.rotatorsManager.getAllDeviceNames()
        self.rotator = None         # from rotatorsManager by rotatorName
        self.rotatorName = None   # from rotatorsManager

        self._widget.scanPar['Rotator'].currentIndexChanged.connect(self.updateRotator)
        self.updateRotator()

        for rotator in self.rotatorsList:
            self._widget.scanPar['Rotator'].addItem(rotator)

        self._widget.scanPar['xShift'].valueChanged.connect(self.replotAll)
        self.updateShift()

        # Scan loop control
        self._widget.scanPar['StartButton'].clicked.connect(self.prepareOPTScan)
        self._widget.scanPar['StopButton'].clicked.connect(self.requestInterruption)
        self._widget.scanPar['PlotHorCuts'].clicked.connect(self.plotHorCuts)

        # OPT worker thread
        self.optThread = Thread()
        self.optWorker = ScanOPTWorker(self._master,
                                       self.detectorName,
                                       self.rotatorName,
                                       )
        self.optWorker.moveToThread(self.optThread)

        self._commChannel.sigRotatorPositionUpdated.connect(
            lambda _: self.optWorker.postRotatorStep(),
            )

        self.optWorker.sigScanDone.connect(self.postScanEnd)
        self.optWorker.sigNewFrameCaptured.connect(self.processImage)

        # Thread signals connection
        self.optThread.started.connect(
            lambda: self.optWorker.preStart(self.optSteps),
            )

    def postScanEnd(self):
        """ Triggered after the end of the OPT scan. """

        self._logger.info('OPT scan finished.')
        self.optStack = np.array(self.allFrames)

        self.processAlign(self.optStack)
        self.optWorker.isInterruptionRequested = False  # reset interruption flag
        self.optThread.quit()  # stop the worker thread
        self.enableWidget(True)

    def prepareOPTScan(self):
        """ Makes preliminary checks for the OPT scan."""
        self.optWorker.demoEnabled = False
        self.optWorker.noRAM = True
        self.allFrames = []

        # equidistant steps for the OPT scan in absolute values.
        curPos = self._master.rotatorsManager[self.rotatorName].get_position()[0]
        counterPos = (curPos + self.stepsPerTurn//2) % self.stepsPerTurn
        self.optWorker.optSteps = [curPos, counterPos]
        self.optSteps = 2

        # starting scan
        self.enableWidget(False)
        self.optThread.start()

    ##################
    # Helper methods #
    ##################
    def enableWidget(self, value: bool) -> None:
        """ Upon starting/stopping the alignment scan, widget
        editable fields get (dis)enabled from the bool value.

        Args:
            value (bool): enable value, False means disable
        """
        self._widget.scanPar['StartButton'].setEnabled(value)
        self._widget.scanPar['StopButton'].setEnabled(not value)
        self._widget.scanPar['LineIdxsEdit'].setEnabled(value)
        self._widget.scanPar['xShift'].setEnabled(value)
        self._widget.scanPar['PlotHorCuts'].setEnabled(value)

    def requestInterruption(self):
        """ Request interruption of the OPT scan. """
        self.optWorker.isInterruptionRequested = True

    def getHorCutIdxs(self):
        return [int(k) for k in self._widget.getHorCutsIdxList().split()]

    def updateShift(self):
        self.xShift = self._widget.scanPar['xShift'].value()

    def updateRotator(self):
        """ Update rotator attributes when rotator is changed.
        setting an index of the motor, motor_steps describe
        number of steps per revolution (resolution of the motor),
        also displayed in the widget.
        """
        self.rotatorName = self.rotatorsList[self._widget.getRotatorIdx()]
        self.rotator = self._master.rotatorsManager[self.rotatorName]
        self.stepsPerTurn = self.rotator._stepsPerTurn

    ##################
    # Image handling #
    ##################
    def processImage(self, name: str, frame: np.ndarray) -> None:
        """
        Display stack or image in the napari viewer.

        Args:
            name (`str`): napari layer name
            frame (`np.ndarray`): image or stack
            step (`int`): current OPT scan step
        """
        if self.optWorker.isOPTScanRunning:
            self.allFrames.append(np.uint16(frame))

    def processAlign(self, arr):
        self.cor = AlignCOR('alignOPT', arr, self.xShift)
        self.cor.merge()
        self._widget.plotCounterProj(self.cor.merged)

    def normalize(self, data, mode='01'):  # other mode max
        """this works for positive cuts and images, ngative
        values are not reliably taken care of.

        Args:
            data (_type_): _description_
            mode (str, optional): _description_. Defaults to '01'.

        Returns:
            _type_: _description_
        """
        if mode == '01':
            return (data - np.amin(data))/abs(np.amax(data))
        elif mode == 'max':
            return data / np.amax(data)
        else:
            raise ValueError('Unknown mode of normalization')

    def plotHorCuts(self):
        # query the line indeces to get hor cuts.
        self.horIdxList = self.getHorCutIdxs()
        # process the hor cuts
        self.cor.processHorCuts(self.horIdxList)

        # plotting
        self._widget.plotHorCuts.clear()  # clear plotWidget first
        self._widget.plotHorCuts.addLegend()
        self._widget.plotHorCuts.setTitle('Horizontal cuts', color='b')
        for i, px in enumerate(self.horIdxList):
            self._widget.plotHorCuts.plot(
                    self.normalize(self.cor.horCuts[i][0], '01'),
                    name=f'single {px}',
                    pen=pg.mkPen('r'))
            self._widget.plotHorCuts.plot(
                    self.normalize(self.cor.horCuts[i][1], '01'),
                    name=f'merge {px}',
                    pen=pg.mkPen('b'))

        # plot CC
        self._widget.plotCC.clear()  # clear plotWidget first
        self._widget.plotCC.addLegend()
        self._widget.plotCC.setTitle('Norm. cross-correlation', color='b')
        # find
        for i, px in enumerate(self.horIdxList):
            # I plot it normalized
            self._widget.plotCC.plot(
                    self.cor.crossCorr[i]/np.amax(self.cor.crossCorr[i]),
                    name=f'{px}',
                    )
        # plot center Hor line
        self._widget.plotCC.addItem(
            pg.InfiniteLine(self.cor.center_px,
                            angle=90,
                            pen=pg.mkPen(width=2, color='r'))
        )

    def replotAll(self):
        self.updateShift()
        try:
            self.cor._updateShift(self.xShift)
            self._widget.plotCounterProj(self.cor.merged)
            self.plotHorCuts()
        except TypeError:
            self.__logger.info('No alignment stack available')


class AlignCOR():
    def __init__(self, name, img_stack, shift):
        self.name = name
        if len(img_stack) != 2:
            raise IndexError('Snap save mode should contain save to display')
        # img_stack is opt acquired at 0 and 180 deg
        self.img_stack_raw = img_stack
        self.shift = shift
        self.createShiftedStack()

        self.horCuts = []
        self.merged = None

    def _updateShift(self, value):
        self.shift = value
        self.recalcWithShift()

    def merge(self):
        self.merged = np.array(self.img_stack).mean(axis=0).astype(np.int16)

    def processHorCuts(self, idx_list):
        self.horCuts = []
        self.valid_idx = []
        for i in idx_list:  # idx is line of the detector
            try:
                # append tuple of first from stack and merged one at given idx
                self.horCuts.append((self.img_stack[0][i],
                                     self.merged[i]))
                self.valid_idx.append(i)
            except IndexError:
                # TODO: this has to update the valid idx list too
                print('Index out of range')

        # calculate cross-correlation between 0, 180 projs
        self.crossCorr = []
        for i in self.valid_idx:
            self.crossCorr.append(
                correlate(self.img_stack[0][i],
                          self.img_stack[1][i],
                          mode='full'),
                )
        # column dimension, which is center
        # of full cross correlation
        self.center_px = self.img_stack[0].shape[1]

    def recalcWithShift(self):
        """Called after shift value changes.
        """
        # first redo the stack
        self.createShiftedStack()

        # redo merge
        self.merge()

        # process cuts
        self.processHorCuts(self.valid_idx)

    def createShiftedStack(self):
        """This shfits the first of the two projections
        by self.shift
        """
        shifted = np.zeros(self.img_stack_raw[0].shape)

        if self.shift < 0:
            shifted[:, :self.shift] = np.roll(self.img_stack_raw[0],
                                              self.shift,
                                              axis=1,
                                              )[:, :self.shift]
        else:
            shifted[:, self.shift:] = np.roll(self.img_stack_raw[0],
                                              self.shift,
                                              axis=1,
                                              )[:, self.shift:]
        self.img_stack = [shifted[:, ::-1],
                          self.img_stack_raw[1]]


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
