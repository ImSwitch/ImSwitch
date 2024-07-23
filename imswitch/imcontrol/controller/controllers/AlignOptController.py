import numpy as np
from scipy.signal import correlate

from imswitch.imcommon.model import initLogger
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Thread
# from typing import Tuple

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
        self.cor = AlignCOR()

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

        # cross projection x-shift parameter
        self._widget.scanPar['xShift'].valueChanged.connect(self.plotAll)

        # this one can be done without updating the image.
        self._widget.scanPar['LineIdx'].valueChanged.connect(self.plotAll)
        self._widget.scanPar['CounterProjPair'].currentIndexChanged.connect(
                                                    self.plotAll)
        self._widget.scanPar['Threshold'].valueChanged.connect(self.plotAll)
        self._widget.scanPar['Modality'].currentIndexChanged.connect(self.plotAll)

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

        self.cor.updateStack(self.optStack)
        self.optWorker.isInterruptionRequested = False  # reset flag
        self.optThread.quit()  # stop the worker thread
        self.enableWidget(True)
        self.plotAll()

    def prepareOPTScan(self) -> None:
        """ Makes preliminary checks for the OPT scan.
        Sets experimental flags and generates steps array/list.
        In the end, worker OPT thread is started.
        """
        self.optWorker.demoEnabled = False
        self.optWorker.noRAM = True
        self.allFrames = []

        step = self.stepsPerTurn//4
        self.optWorker.optSteps = [0, step, 2*step, 3*step]
        self.optSteps = 4

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
        self._widget.scanPar['LineIdx'].setEnabled(value)
        self._widget.scanPar['xShift'].setEnabled(value)
        self._widget.scanPar['Threshold'].setEnabled(value)
        self._widget.scanPar['Modality'].setEnabled(value)
        self._widget.scanPar['CounterProjPair'].setEnabled(value)

    def requestInterruption(self) -> None:
        """ Request interruption of the OPT scan. """
        self.optWorker.isInterruptionRequested = True

    def getHorCutIdx(self) -> int:
        """Decodes field of indices for row cuts

        Returns:
            List[int]: integers used as row indices
        """
        return self._widget.getHorCutsIdx()

    def getThreshold(self) -> float:
        return self._widget.getThreshold()

    def getExpModality(self) -> str:
        return self._widget.getExpModality()

    def getShift(self) -> int:
        return self._widget.getShift()

    def getProjectionPairFlag(self) -> str:
        return 'pair1' if self._widget.getProjectionPairFlag() == 0 else 'pair2'

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

    def plotAll(self) -> None:
        """When xshift changes, replot the cuts, image
        overlay and the cross-correlation plots.
        """
        self.cor._updateParams('threshold', self.getThreshold())
        self.cor._updateParams('shift', self.getShift())
        self.cor._updateParams('lineIdx', self.getHorCutIdx())
        self.cor._updateParams('pairFlag', self.getProjectionPairFlag())
        self.cor._updateParams('modality', self.getExpModality())

        self.cor._reCalcWithShift()
        self._widget.plotCounterProj(self.cor.merged)
        self._widget.execPlots(self.cor)


class AlignCOR():
    """ Class to visualize alignment of the two pairs of 180 deg tomographic
    projections, i.e. 0, 90, 180, 270 deg. The class is used to calculate
    cumulative sums of the two projections, their cross-correlation, mean index
    of the thresholded horizontal cuts. All can be used for alignment
    procedures.
    """
    def __init__(self):
        self.img_stack = {}
        self.img_stack_raw = {}
        self.params = {
            'shift': 0,
            'lineIdx': 0,
            'pairFlag': 'pair1',
            'threshold': 1.0,
            'modality': 'Transmission',
            }

    def updateStack(self, stack) -> None:
        """ Update the stack of images for the alignment.

        Args:
            stack (List[np.ndarray]): list of four images, 0, 90, 180, 270 deg
        """
        if len(stack) != 4:
            raise IndexError('Stack must contain exactly four images.')

        # img_stack is opt acquired at 0, 90, 180, 270 deg
        self.img_stack = {}
        self.img_stack_raw = {}

        # separate the stack into two pairs
        self.img_stack_raw['pair1'] = [stack[0], stack[2]]
        self.img_stack_raw['pair2'] = [stack[1], stack[3]]

        # shift projections of both pairs by params['shift'] value
        self.createShiftedStack()

    def merge(self) -> None:
        """ Merge of the two projections is their mean. """
        self.merged = np.array(
                        self.img_stack[self.params['pairFlag']]
                        ).mean(axis=0).astype(np.int16)

    def createShiftedStack(self):
        """ This shifts the first of the two projections by self.shift,
        first image in the stack is also mirrored around vertical center axis
        """
        self.img_stack['pair1'] = [
            np.roll(
                self.img_stack_raw['pair1'][0],
                self.params['shift'],
                axis=1,
                )[:, ::-1],

            np.roll(
                self.img_stack_raw['pair1'][1],
                self.params['shift'],
                axis=1,
                ),
            ]

        self.img_stack['pair2'] = [
            np.roll(
                self.img_stack_raw['pair2'][0],
                self.params['shift'],
                axis=1,
                )[:, ::-1],

            np.roll(
                self.img_stack_raw['pair2'][1],
                self.params['shift'],
                axis=1,
                ),
            ]
        self.merge()

    def processHorCuts(self) -> None:
        """ Retrieve rows from the camera frames, mirror flip and merge
        the projections. Second part calculates cross-correlation of the
        cuts which should be ideally perfectly matching and central ->
        optimization enabler

        Args:
            idx_list (List[int]): indices of row for horizontal cuts.
        """
        self.horCuts = {}

        # evaluate if the idx is in the range of the detector
        # TODO: Check this in the update func, perhaps
        if 0 <= self.params['lineIdx'] < self.img_stack[self.params['pairFlag']][0].shape[0]:
            i = self.params['lineIdx']
        else:
            i = 0
            print(f"Index {self.params['lineIdx']} out of camera's range, setting to {i}")

        # horizontal cuts for the selected pair and row
        self.horCuts = (
            self.img_stack[self.params['pairFlag']][0][i],
            self.img_stack[self.params['pairFlag']][1][i],
            )

        # cross correlation of the projections
        self.processCrossCorrelation(i)

        # calculate normalized cumsums
        # and abs sum of their difference
        # self.diff, self.s1, self.s2 = self.processCumSums(
        #     self.img_stack[self.params['pairFlag']][0][i],
        #     self.img_stack[self.params['pairFlag']][1][i],
        #     )

        # calculate the indices of the middle of the image
        self.processImageValueIndices()

    # correlation
    def processCrossCorrelation(self, i: int) -> None:
        """ Process cross-correlation of the horizontal cuts.
        1. Normalize the cross-correlation by the maximum value of the
        raw image cross-correlation.
        2. Find the center pixel of the image, which should coincide with
        the center of the cross-correlation.

        Args:
            i (int): Index of the row for horizontal cuts.
        """
        corrNormFactor = np.amax(correlate(
            self.img_stack_raw[
                self.params['pairFlag']
                ][0][i].astype(np.floating),
            self.img_stack_raw[
                self.params['pairFlag']
                ][1][i].astype(np.floating),
            mode='full'))

        self.crossCorr = correlate(
            self.img_stack[self.params['pairFlag']][0][i].astype(np.floating),
            self.img_stack[self.params['pairFlag']][1][i].astype(np.floating),
            mode='full') / corrNormFactor

        self.center_px = self.img_stack[self.params['pairFlag']][0].shape[1]

    # def processCumSums(self, arr1, arr2,
    #                    ) -> Tuple[float, np.ndarray, np.ndarray]:
    #     """ Calculate normalized cumulative sums of the horizontal cuts.
    #     sum of difference of cumulative sums of the counter-projections.
    #     - This metric should be minimized for centering for the COR.

    #     Args:
    #         arr1 (np.ndarray): first horizontal cut
    #         arr2 (np.ndarray): second horizontal cut

    #     Returns:
    #         Tuple[float, np.ndarray, np.ndarray]: difference of the cumsums,
    #             cumsum of the first cut, cumsum of the second
    #     """
    #     # first invert the arrays in case of transmission modality
    #     if self.params['modality'] == 'Transmission':
    #         arr1, arr2 = -(arr1 - np.amax(arr1)), -(arr2 - np.amax(arr2))

    #     # calculate the cumsums
    #     s1, s2 = np.cumsum(arr1), np.cumsum(arr2)

    #     # normalize by the value of first proj
    #     # this changes the dtype, therefore the division
    #     # is not done inplace (s1 /= s1[-1])
    #     s2 = s2 / s1[-1]  # this division needs to be done first
    #     s1 = s1 / s1[-1]

    #     diff = abs(sum(s1 - s2))
    #     return diff, s1, s2

    def processImageValueIndices(self) -> None:
        """ Calculate the indices of the middle of the image.
        Calculate the indices of the middle of the cumsums.
        Calculate the indices of the thresholded cuts.
        """
        # argmin of the difference of the cumsums
        # self.s1middle = np.argmin(abs(self.s1 - self.s1[-1]/2))
        # self.s2middle = np.argmin(abs(self.s2 - self.s2[-1]/2))

        # invert horctus in case of transmission modality
        if self.params['modality'] == 'Transmission':
            self.invHorCuts = (-(self.horCuts[0] - np.amax(self.horCuts[0])),
                               -(self.horCuts[1] - np.amax(self.horCuts[1])))
        else:
            self.invHorCuts = self.horCuts

        # retrieve the thresholded cuts
        self.img_thresh = np.amax(self.invHorCuts[0]) * self.params['threshold'] / 100
        self.s1meanIdx = np.mean(
            [index for index, value in enumerate(self.invHorCuts[0])
             if value > self.img_thresh],
             )

        self.s2meanIdx = np.mean(
            [index for index, value in enumerate(self.invHorCuts[1])
             if value > self.img_thresh],
             )

    def _reCalcWithShift(self) -> None:
        """ Called after shift value changes. """
        # first redo the stack
        self.createShiftedStack()

        # process cuts
        self.processHorCuts()

    def _updateParams(self, parName: str, value) -> None:
        """ Update the parameters of the class.

        Args:
            parName (str): name of the parameter
            value (Any): value of the parameter
        """
        self.params[parName] = value

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
