import numpy as np
from scipy.signal import correlate

from imswitch.imcommon.model import initLogger
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Thread
from typing import List

from .OptController import ScanOPTWorker

__author__ = "David Palecek", "Jacopo Abramo"
__credits__ = []
__maintainer__ = "David Palecek"
__email__ = "david@stanka.de"


class AlignOptController(ImConWidgetController):
    """ OPT alignment controller. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)
        self.optStack = np.ones((1, 1, 1))
        self.counterProj = np.ones((1, 1, 1))
        self.cor = None

        # Set up rotator in widget
        self._widget.initControls()
        self.isOptRunning = False

        # TODO: no selector for detectors (not linked to the settings widget)
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detectorName = allDetectorNames[0]
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # rotators list
        self.rotatorsList = self._master.rotatorsManager.getAllDeviceNames()
        self.rotator = None       # from rotatorsManager by rotatorName
        self.rotatorName = None   # from rotatorsManager

        self._widget.scanPar['Rotator'].currentIndexChanged.connect(
            self.updateRotator)
        self.updateRotator()

        for rotator in self.rotatorsList:
            self._widget.scanPar['Rotator'].addItem(rotator)

        # Scan loop control
        self._widget.scanPar['StartButton'].clicked.connect(
            self.prepareOPTScan,
            )
        self._widget.scanPar['StopButton'].clicked.connect(
            self.requestInterruption,
            )
        self._widget.scanPar['PlotHorCuts'].clicked.connect(
            self.plotHorCuts,
            )

        # cross projection x-shift parameter
        self._widget.scanPar['xShift'].valueChanged.connect(self.replotAll)
        self.updateShift()

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

        # worker signals
        self.optWorker.sigScanDone.connect(self.postScanEnd)
        self.optWorker.sigNewFrameCaptured.connect(self.processImage)

        # Thread signals connection
        self.optThread.started.connect(
            lambda: self.optWorker.preStart(self.optSteps),
            )

    def postScanEnd(self) -> None:
        """ Triggered after the end of the OPT scan.
        It will process the projections, and quit the worker
        thread, enable widget fields.
        """
        self._logger.info('OPT scan finished.')
        self.optStack = np.array(self.allFrames)

        self.processAlign(self.optStack)
        self.optWorker.isInterruptionRequested = False  # reset flag
        self.optThread.quit()  # stop the worker thread
        self.enableWidget(True)

    def prepareOPTScan(self) -> None:
        """ Makes preliminary checks for the OPT scan.
        Sets experimental flags and generates steps array/list.
        In the end, worker OPT thread is started.
        """
        self.optWorker.demoEnabled = False
        self.optWorker.noRAM = True
        self.allFrames = []

        # equidistant steps for the OPT scan in absolute values.
        curPos = self._master.rotatorsManager[
                                self.rotatorName
                                ].get_position()[0]
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

    def requestInterruption(self) -> None:
        """ Request interruption of the OPT scan. """
        self.optWorker.isInterruptionRequested = True

    def getHorCutIdxs(self) -> List[int]:
        """Decodes field of indices for row cuts

        Returns:
            List[int]: integers used as row indices
        """
        return [int(k) for k in self._widget.getHorCutsIdxList().split()]

    def updateShift(self) -> None:
        """ Update x-shift value for alignment """
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

    def processAlign(self, arr: np.ndarray) -> None:
        """Plot counter projection using AlignCOR class

        Args:
            arr (np.ndarray): two-frame array
        """
        self.cor = AlignCOR('alignOPT', arr, self.xShift)
        self.cor.merge()
        self._widget.plotCounterProj(self.cor.merged)

    def plotHorCuts(self) -> None:
        """Create widget plot of the horizontal cuts
        and the crosscorrelations.
        """
        # query the line indeces to get hor cuts.
        self.horIdxList = self.getHorCutIdxs()
        # process the hor cuts
        self.cor.processHorCuts(self.horIdxList)

        # here call widget func
        self._widget.execPlotHorCuts(self.horIdxList, self.cor)

    def replotAll(self) -> None:
        """When xshift changes, replot the cuts, image
        overlay and the crosscorrelation plots.
        """
        self.updateShift()
        try:
            self.cor._updateShift(self.xShift)
            self._widget.plotCounterProj(self.cor.merged)
            self.plotHorCuts()
        except TypeError:
            self.__logger.info('No alignment stack available')


class AlignCOR():
    """Class to visualize alignment of the two 180 deg tomographic
    projections
    """
    def __init__(self, name: str, img_stack: np.ndarray, shift: int) -> None:
        """Init class, check validity of the img_stack shape and calculate
        shifted overlay stack

        Args:
            name (str): object name
            img_stack (np.ndarray): stack od two counter-projections
            shift (int): shift of one of the projections in respect to the
                other one, in pixels.

        Raises:
            IndexError: In case of wrong array shape
        """
        self.name = name
        if len(img_stack) != 2:
            raise IndexError('Stack must contain exactly two images.')
        # img_stack is opt acquired at 0 and 180 deg
        self.img_stack_raw = img_stack
        self.shift = shift

        # invert one of the images and do overlay.
        self.createShiftedStack()

        self.horCuts = []
        self.merged = None

    def _updateShift(self, value: int) -> None:
        """ Updates x-shift value between projections. Triggers
        recalculation of the merge

        Args:
            value (int): shift between projections in pixels.
        """
        self.shift = value
        self.recalcWithShift()

    def merge(self) -> None:
        """ Merge of the two projections is their mean. """
        self.merged = np.array(self.img_stack).mean(axis=0).astype(np.int16)

    def processHorCuts(self, idx_list: List[int]) -> None:
        """Retrive rows from the camera frames, mirror flip and merge
        the projections. Second part calculates cross-correlation of the
        cuts which should be ideally perfectly matching and central ->
        optimization enabler

        Args:
            idx_list (List[int]): indices of row for horizontal cuts.
        """
        self.horCuts = []
        self.valid_idx = []

        # add rows
        for i in idx_list:  # idx is row of the detector
            try:
                # append tuple of (first from stack, merged one) at given idx
                self.horCuts.append((self.img_stack[0][i],
                                     self.merged[i]))
                self.valid_idx.append(i)
            except IndexError:
                # TODO: this could update the valid idx list too
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
        # of full cross correlation, which is size 2n
        self.center_px = self.img_stack[0].shape[1]

    def recalcWithShift(self) -> None:
        """ Called after shift value changes. """
        # first redo the stack
        self.createShiftedStack()

        # redo merge
        self.merge()

        # process cuts
        self.processHorCuts(self.valid_idx)

    def createShiftedStack(self):
        """ This shifts the first of the two projections by self.shift,
        first image in the stack is also mirrored around vertical center axis
        """
        shifted = np.zeros(self.img_stack_raw[0].shape)

        # rolling around axis 1, which are columns
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
        # in the stack, first is shifted and mirrored
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
