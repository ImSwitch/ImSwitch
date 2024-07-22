import numpy as np
from scipy.signal import correlate

from imswitch.imcommon.model import initLogger
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Thread
from typing import Tuple

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

        # try:
        self.cor._reCalcWithShift()
        self._widget.plotCounterProj(self.cor.merged)
        self._widget.execPlots(self.cor)
        # except (TypeError, AttributeError):
        #     self.__logger.info('No alignment stack available')


class AlignCOR():
    """Class to visualize alignment of the two pairs of 180 deg tomographic
    projections, i.e. 0, 90, 180, 270 deg. The class is used to calculate
    cumulative sums of the two projections

    and their cross-correlation.
    """
    def __init__(self):
        self.img_stack = {}
        self.img_stack_raw = {}
        self.params = {
            'shift': 0,
            'lineIdx': 0,
            'pairFlag': 'pair1',
            'threshold': 1.0,
            }

    def updateStack(self, stack):
        if len(stack) != 4:
            raise IndexError('Stack must contain exactly four images.')
        # img_stack is opt acquired at 0, 90, 180, 270 deg
        self.img_stack = {}
        self.img_stack_raw = {}

        self.img_stack_raw['pair1'] = [stack[0], stack[2]]
        self.img_stack_raw['pair2'] = [stack[1], stack[3]]

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
            np.roll(self.img_stack_raw['pair1'][0],
                    self.params['shift'],
                    axis=1)[:, ::-1],
            np.roll(self.img_stack_raw['pair1'][1],
                    self.params['shift'],
                    axis=1),
            ]

        self.img_stack['pair2'] = [
            np.roll(self.img_stack_raw['pair2'][0],
                    self.params['shift'],
                    axis=1)[:, ::-1],
            np.roll(self.img_stack_raw['pair2'][1],
                    self.params['shift'],
                    axis=1),
            ]
        self.merge()

    def processHorCuts(self) -> None:
        """Retrieve rows from the camera frames, mirror flip and merge
        the projections. Second part calculates cross-correlation of the
        cuts which should be ideally perfectly matching and central ->
        optimization enabler

        Args:
            idx_list (List[int]): indices of row for horizontal cuts.
        """
        self.horCuts = {}

        # evaluate if the idx is in the range of the detector

        # Check this in the update func
        if 0 <= self.params['lineIdx'] < self.img_stack[self.params['pairFlag']][0].shape[0]:
            i = self.params['lineIdx']
        else:
            i = 0
            print(f"Index {self.params['lineIdx']} out of camera's range, setting to {i}")

        self.horCuts = (
            self.img_stack[self.params['pairFlag']][0][i],
            self.img_stack[self.params['pairFlag']][1][i],
            )

        # correlation
        self.processCrossCorrelation(i)

        self.diff, self.s1, self.s2 = self.processCumSums(
            self.img_stack[self.params['pairFlag']][0][i],
            self.img_stack[self.params['pairFlag']][1][i],
            )

    # correlation
    def processCrossCorrelation(self, i: int) -> float:
        """PRocess cross-correlation of the horizontal cuts.
        Normalize the cross-correlation by the maximum value of the
        raw image cross-correlation.
        Find the center pixel of the image, which should coincide with
        the center of the cross-correlation.

        Args:
            i (int): Index of the row for horizontal cuts.

        Returns:
            None
        """
        corrNormFactor = np.amax(correlate(
            self.img_stack_raw[self.params['pairFlag']][0][i].astype(np.floating),
            self.img_stack_raw[self.params['pairFlag']][1][i].astype(np.floating),
            mode='full'))

        self.crossCorr = correlate(
            self.img_stack[self.params['pairFlag']][0][i].astype(np.floating),
            self.img_stack[self.params['pairFlag']][1][i].astype(np.floating),
            mode='full') / corrNormFactor

        self.center_px = self.img_stack[self.params['pairFlag']][0].shape[1]

    def processCumSums(self, arr1, arr2) -> Tuple[float, np.ndarray, np.ndarray]:
        """ Calculate sum of difference of cumsums of the counterprojections.
        This should be minimized for centering for the COR.
        """
        s1, s2 = np.cumsum(arr1), np.cumsum(arr2)

        # normalize by the value of first proj
        # this changes the dtype, therefore the division is not done inplace (s1 /= s1[-1])
        s2 = s2 / s1[-1]  # this division needs to be done first
        s1 = s1 / s1[-1]
        
        diff = abs(sum(s1 - s2))
        return diff, s1, s2

    # def calcFullImgDiff(self):
    #     s1 = np.cumsum(self.img_stack[self.params['pairFlag']][0].mean(axis=0))
    #     s2 = np.cumsum(self.img_stack[self.params['pairFlag']][1].mean(axis=0))
    #     return s1 - s2, abs(sum(s1 - s2))

    # def calcFullImgDiffRaw(self):
    #     s1 = np.cumsum(self.img_stack_raw[self.params['pairFlag']][0].mean(axis=0))
    #     s2 = np.cumsum(self.img_stack_raw[self.params['pairFlag']][1].mean(axis=0))
    #     return s1 - s2, abs(sum(s1 - s2))

    def _reCalcWithShift(self) -> None:
        """ Called after shift value changes. """
        # first redo the stack
        self.createShiftedStack()

        # process cuts
        self.processHorCuts()

    def _updateParams(self, parName: str, value):
        self.params[parName] = value


# class AlignCOR():
#     """Class to visualize alignment of the two pairs of 180 deg tomographic
#     projections, i.e. 0, 90, 180, 270 deg. The class is used to calculate
#     cumulative sums of the two projections

#     and their cross-correlation.
#     """
#     def __init__(self) -> None:
#         """Init class, check validity of the img_stack shape and calculate
#         shifted overlay stack

#         Args:
#             img_stack (np.ndarray): stack od two counter-projections
#             shift (int): shift of one of the projections in respect to the
#                 other one, in pixels.

#         Raises:
#             IndexError: In case of wrong array shape
#         """
#         self.img_stack = {}
#         self.img_stack_raw = {}
#         self.params = {'shift': 0,
#                        'lineIdx': 0,
#                        'pairFlag': 'pair1',
#                        }

#     def updateStack(self, stack):
#         if len(stack) != 4:
#             raise IndexError('Stack must contain exactly two images.')
#         # img_stack is opt acquired at 0, 90, 180, 270 deg
#         self.img_stack_raw['pair1'] = [stack[0], stack[2]]
#         self.img_stack_raw['pair2'] = [stack[1], stack[3]]

#         # invert one of the images and do overlay.
#         self.createShiftedStack()

#     def merge(self) -> None:
#         """ Merge of the two projections is their mean. """
#         self.merged = np.array(
#                         self.img_stack[self.params['pairFlag']]
#                         ).mean(axis=0).astype(np.int16)

#     def createShiftedStack(self):
#         """ This shifts the first of the two projections by self.shift,
#         first image in the stack is also mirrored around vertical center axis
#         """
#         self.img_stack['pair1'] = [
#             np.roll(self.img_stack_raw['pair1'][0],
#                     self.params['shift'],
#                     axis=1)[:, ::-1],
#             np.roll(self.img_stack_raw['pair1'][1],
#                     self.params['shift'],
#                     axis=1),
#             ]
#         self.img_stack['pair2'] = [
#             np.roll(self.img_stack_raw['pair2'][0],
#                     self.params['shift'],
#                     axis=1)[:, ::-1],
#             np.roll(self.img_stack_raw['pair2'][1],
#                     self.params['shift'],
#                     axis=1),
#             ]
#         self.merge()

#     def processHorCuts(self) -> None:
#         """Retrieve rows from the camera frames, mirror flip and merge
#         the projections. Second part calculates cross-correlation of the
#         cuts which should be ideally perfectly matching and central ->
#         optimization enabler

#         Args:
#             idx_list (List[int]): indices of row for horizontal cuts.
#         """
#         self.horCuts = {}

#         # evaluate if the idx is in the range of the detector

#         # Check this in the update func
#         if 0 <= self.params['lineIdx'] < self.img_stack[self.params['pairFlag']][0].shape[0]:
#             i = self.params['lineIdx']
#         else:
#             i = 0
#             print(f"Index {self.params['lineIdx']} out of camera's range, setting to {i}")

#         self.horCuts = (self.img_stack[self.params['pairFlag']][0][i],
#                         self.img_stack[self.params['pairFlag']][1][i],
#                         )

#         # correlation
#         self.crossCorr = correlate(
#                             self.img_stack[self.params['pairFlag']][0][i].astype(np.floating),
#                             self.img_stack[self.params['pairFlag']][1][i].astype(np.floating),
#                             mode='full')
#         # print('CC max min', np.amax(self.crossCorr), np.amin(self.crossCorr))
#         self.center_px = self.img_stack[self.params['pairFlag']][0].shape[1]

#         self.diff_raw, self.s1_raw, self.s2_raw = self.cumsumDiff(
#                             self.img_stack_raw[self.params['pairFlag']][0][i],
#                             self.img_stack_raw[self.params['pairFlag']][1][i],
#                             )

#         self.diff, self.s1, self.s2 = self.cumsumDiff(
#                             self.img_stack[self.params['pairFlag']][0][i],
#                             self.img_stack[self.params['pairFlag']][1][i],
#                             )

#     def cumsumDiff(self, arr1, arr2) -> Tuple[float, np.ndarray, np.ndarray]:
#         """ Calculate sum of difference of cumsums of the counterprojections.
#         This should be minimized for centering for the COR.
#         """
#         s1, s2 = np.cumsum(arr1), np.cumsum(arr2)
#         diff = abs(sum(s1 - s2))
#         return diff, s1, s2

#     def _reCalcWithShift(self) -> None:
#         """ Called after shift value changes. """
#         # first redo the stack
#         self.createShiftedStack()

#         # process cuts
#         self.processHorCuts()

#     def _updateParams(self, parName: str, value):
#         self.params[parName] = value
