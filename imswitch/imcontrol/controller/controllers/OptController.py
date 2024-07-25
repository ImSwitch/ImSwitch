import os
import time
import json
from datetime import datetime
from collections import defaultdict
from functools import partial
import numpy as np

from scipy.fftpack import fft, ifft
from scipy.interpolate import interp1d
import tifffile as tif
from skimage.transform import radon

from imswitch.imcontrol.view import guitools as guitools
from typing import Tuple, List, Callable, Dict
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger, dirtools
from imswitch.imcommon.framework import Signal, Thread, Worker
from imswitch.imcommon.externals.tomopy import shepp3d

__author__ = "David Palecek", "Jacopo Abramo"
__credits__ = []
__maintainer__ = "David Palecek"
__email__ = "david@stanka.de"


class ScanExecutionMonitor:
    """
    Helper class dedicated to monitor the execution time of an OPT scan.
    It can be used to generate an experiment report with timing informations
    relative to each step of the scan execution. It is also saved in the
    metadata file of the experiment.
    """
    def __init__(self) -> None:
        """Empty report containers """
        # TODO: move this class to the utilities folder and extend its usage
        # to the rest of the application
        self.outputReport = {}
        self.report = defaultdict(lambda: [])

    def reinitContainers(self) -> None:
        """ Reinit empty reporting containers before experiment """
        self.outputReport = {}
        self.report = defaultdict(lambda: [])

    def addStamp(self, key: str, idx: int, tag: str) -> None:
        """ Add a time stamp to the report.

        Args:
            key (`str`): identifier of the stamp; monitors the
                type of operation recorded.
            idx (`int`): index of the current OPT scan step.
            tag (`str`): tag to identify the beginning ("beg") or the
                end ("end") of the operation.
        """
        self.report[key].append((idx, tag, datetime.now()))

    def addStart(self) -> None:
        """ Adds a starting key to the report. """
        self.report['start'] = datetime.now()

    def addFinish(self) -> None:
        """ Adds an ending key to the report. """
        self.report['end'] = datetime.now()
        try:
            self.totalTime = (self.report['end'] -
                              self.report['start']).total_seconds()
        except KeyError:
            # TODO: ??? why should there be an exception?
            # if the class is reused, and addStart() is not called
            # before addFinish, try will fail.
            print('Not possible to calculate total experimental time.')

    def getReport(self) -> dict:
        """ Returns the report dictionary. """
        return self.outputReport

    def makeReport(self):
        """ Creates a statistical report on the time spent
        on various tasks. This can be used to evaluate
        the scan timing performances.
        """
        self.outputReport = {}
        for k, _ in self.report.items():
            if k in ['start', 'end']:
                continue
            self.__processKey(k)

    def __processKey(self, key):
        """ :meta private: """
        idxs, tags, stamps = zip(*self.report[key])
        i = 0
        diffs, steps = [], []
        while i < len(stamps)-1:
            # subsequent timestamps need to have same key, and not beg/end
            if (idxs[i] == idxs[i+1] and tags[i] == 'beg' and tags[i+1] == 'end'):
                diffs.append((stamps[i+1] - stamps[i]).total_seconds())
                steps.append(idxs[i])  # append for time evolution
            i += 1
        if len(diffs) != len(stamps) // 2:
            print('Some data were not matched')

        # statistical metrics of the time series.
        report = {}
        report['Total'] = np.sum(diffs)                 # total time spent on the task
        report['Mean'] = np.mean(diffs)                 # mean time per step
        report['STD'] = np.std(diffs)                   # STD of time per step
        report['Tseries'] = np.array([steps, diffs]).tolist()  # timeseries of times per step
        report['PercTime'] = np.sum(diffs)/self.totalTime * 100  # percentage of total exp. time

        # put the task dictionary into the report dictionary
        self.outputReport[key] = report


class ScanOPTWorker(Worker):
    """
    OPT scan worker. The worker operates on a separate thread
    from the main application thread. It is responsible for the execution
    of the OPT scan (moving the rotator, acquiring an image, updating plots
    light intensity stability). The worker is also responsible for
    the live reconstruction of the acquired frames, if the option is enabled.

    Args:
        master (`MasterController`): reference to the master controller; used to access the hardware managers.
        detectorName (`str`): name identifier of the detector used for the OPT scan.
        rotatorName (`str`): name identifier of the rotator used for the OPT scan.
    """
    sigNewFrameCaptured = Signal(str, np.ndarray, int)  # (layerLabel, frame, optCurrentStep)
    sigNewStabilityTrace = Signal(object, object)   # (list: steps, list[list]: stabilityTraces)
    sigNewSinogramDataPoint = Signal(int)     # (int: sinogramGenerationStep)
    sigNewLiveRecon = Signal(np.ndarray, int)  # (reconstruction, step of reconstruction)
    sigScanDone = Signal()
    sigUpdateReconIdx = Signal(int)  # triggers change of live-recon index

    def __init__(self, master, detectorName, rotatorName) -> None:
        super().__init__()
        self.__logger = initLogger(self)
        self.master = master
        self.detectorName = detectorName    # detector identifier
        self.rotatorName = rotatorName      # rotator identifier
        self.timeMonitor = ScanExecutionMonitor()
        self.signalStability = Stability()

        # rotator configuration values
        self.optSteps = None            # number of experimental steps
        self.currentStep = 0            # current experimental step
        self.saveSubfolder = None       # save folder
        self.waitConst = None   # in ms, None to ensure it is set from controller

        # monitor flags
        self.saveOpt = False                  # save option for the OPT
        self.isOPTScanRunning = False         # OPT scan running flag, default to False
        self.noRAM = False                    # Stack not saved to RAM and Viewwer to save memory
        self.isLiveRecon = False              # OPT live reconstruction flag, default to False
        self.isInterruptionRequested = False  # interruption request flag, set from the main thread; defaults to False
        self.frameStack = None                # OPT stack memory buffer

        # Demo parameters, synthetic phantom data are generated to emulate OPT scan
        self.demoEnabled = False            # Demo mode flag; if True synthetic data generated; defaults to False
        self.sinogram: np.ndarray = None    # Demo sinogram; default to None

    def preStart(self, resolution: int = 128) -> None:
        """
        Utility method to be called before the start of the OPT scan.
        Generates the the sinogram for the demo experiment, if the demo
        mode is enabled, and updates the UI progress bar.

        Args:
            resolution (`int`): resolution of resulting sinogram, equivalent
                to the number of steps in the OPT scan.
        """
        def generateSyntheticSinogram(resolution: int) -> np.ndarray:
            """Generates sinogram of a 3D Shepp-Logan phantom. The resulting
            array is a cube with an edge of resolution pixels.

            Args:
                resolution (int): edge dimension of the data cube

            Returns:
                np.ndarray: shepp-logan sinogram in int8.
            """
            self.__logger.info('Demo experiment: preparing synthetic data.')
            data = shepp3d(resolution)          # shepp-logan 3D phantom
            sinogram = np.zeros(data.shape)     # preallocate sinogram array
            angles = np.linspace(0, 360, resolution, endpoint=False)  # angles

            # radon transform for each projection, converion to sinogram
            for i in range(resolution):
                self.sigNewSinogramDataPoint.emit(i)  # progress bar monitor
                sinogram[i, :, :] = radon(data[i, :, :], theta=angles)

            self.__logger.info('Synthetic data ready.')
            # normalize and return
            mx = np.amax(sinogram)
            return np.rollaxis((sinogram / mx * 255).astype(np.uint8), 2)

        # generate sinogram only if demo experiment chosen
        if self.demoEnabled:
            self.sinogram = generateSyntheticSinogram(resolution)

        self.startOPTScan()

    def startOPTScan(self):
        """
        Performs the first step of the OPT scan, triggering an asynchronous
        loop with the rotator. After the first motor step is finished,
        the rotator emits the signal `sigPositionUpdated`,
        which is handled by `postRotatorStep`.
        """
        # initialize memory buffer
        # TODO: make sure to get correct dtype from detector somehow...
        # DP: why important if dtypes corectly handled in the camera classes?
        # JA: it's important for numpy to correctly allocate memory if frames are stored in RAM;
        # JA: and also for correctly saving the frames to disk.
        # this needs to be changed at the API level at some point...
        self.frameStack = None
        self.signalStability.clear()  # clear lists inbetween experiments
        self.currentLiveRecon = None
        self.master.detectorsManager[self.detectorName].startAcquisition()

        # mock is caught in the prepareOPTScan in controller
        self.waitConst = self.master.detectorsManager[self.detectorName].getExposure()
        self.__logger.info(
            f'Wait constant equals exposure time: {self.waitConst} us.',
            )

        self.isOPTScanRunning = True

        self.timeMonitor.addStart()
        self.currentStep = 0

        # we select the frame retrieval method based off the demo flag
        self.getFrame: Callable = self.getFrameFromSino if self.demoEnabled else self.snapCamera

        # move the rotator to the first position
        self.timeMonitor.addStamp('motor', self.currentStep, 'beg')
        self.master.rotatorsManager[self.rotatorName].move_abs(
                                        self.optSteps[self.currentStep],
                                        inSteps=True)

    def postRotatorStep(self):
        """
        Triggered after emission of the `sigPositionUpdated` signal from
        the rotator. If only a rotational step was requested, returns.
        Otherwise, the method performs the following steps:

        - captures the latest frame from the detector;
        - updates the stability plot;
        - (optional) performs live reconstruction;
        - (optional) saves the frame if option is enabled;
        - triggers the next motor step.

        This workflow is repeated until all the rotational steps
        are completed, or when the `isInterruptionRequested` flag is raised
        by the main thread.
        """
        self.timeMonitor.addStamp('motor', self.currentStep, 'end')
        # manual stepping also leads to here, continue only for OPT scan
        if not self.isOPTScanRunning:
            return

        frame = self.getNextFrame()
        self.processFrameStability(frame, self.currentStep)

        # live reconstruction processsing
        if self.isLiveRecon:
            self.timeMonitor.addStamp('live-recon', self.currentStep, 'beg')
            self.computeLiveReconstruction(frame)
            self.sigNewLiveRecon.emit(self.currentLiveRecon.recon,
                                      self.currentLiveRecon.step)
            self.timeMonitor.addStamp('live-recon', self.currentStep, 'end')

        # save OPT frame, the flag is checked inside the method
        self.saveCurrentFrame(frame)

        # stop request
        if self.isInterruptionRequested:
            self.stopOPTScan()
        else:
            self.startNextStep()

    def snapCamera(self) -> np.ndarray:
        """Snap frame from the current camera.

        Returns:
            np.ndarray: frame array
        """
        # waitConst is always in us, so we need to convert it to seconds
        time.sleep(self.waitConst/1e6)
        return self.master.detectorsManager[self.detectorName].getLatestFrame()

    def getFrameFromSino(self) -> np.ndarray:
        """
        In case of demo experiment, frame is retrived
        from the synthetic synogram.

        Returns:
            np.ndarray: frame of synthetic sinogram.
        """
        return self.sinogram[self.currentStep]

    def getNextFrame(self) -> np.ndarray:
        """
        Captures the next frame from the detector. If live reconstruction
        is enabled, the frame will be stored in the local memory buffer;
        finally the frame will be displayed in the viewer (unless `noRAM` flag
        enabled).

        Returns:
            np.ndarray: the captured frame
        """
        self.timeMonitor.addStamp('snap', self.currentStep, 'beg')
        frame = self.getFrame()

        # add to optStack and display, this avoids repetition
        self.processFrame(frame)
        return frame

    def processFrame(self, frame: np.ndarray) -> None:
        """
        Appends frame to the stack (unless noRAM option), displays
        the last frame, or the full stack

        Args:
            frame (np.ndarray): last frame, from camera, or synthetic.
        """
        if self.noRAM:  # no volume in napari, only last frame
            self.sigNewFrameCaptured.emit(
                f'{self.detectorName}: latest frame',
                frame,
                self.currentStep,
                )

        else:  # volume in RAM and displayed in napari
            if self.frameStack is None:
                self.frameStack = np.array(frame)
            else:
                try:  # add 2D frame
                    self.frameStack = np.concatenate((self.frameStack,
                                                      frame[np.newaxis, :]),
                                                     )
                except ValueError:  # to add to a stack of only one image
                    self.frameStack = np.stack((self.frameStack, frame))

            self.sigNewFrameCaptured.emit(
                f'{self.detectorName}: OPT stack',
                self.frameStack,
                self.currentStep,
                )
        self.timeMonitor.addStamp('snap', self.currentStep, 'end')

    def processFrameStability(self, frame: np.ndarray, step: int) -> None:
        """
        Processes the light stability of the incoming frame;
        the computed traces are then emitted to the main thread for display.

        Args:
            frame (`np.ndarray`): the incoming frame
            step (`int`): the current step of the OPT scan
        """
        stepsList, intensityDict = self.signalStability.processStabilityTraces(
                                                            frame,
                                                            step,
                                                            )
        self.sigNewStabilityTrace.emit(stepsList, intensityDict)

    def saveCurrentFrame(self, frame: np.ndarray) -> None:
        """
        Save current camera frame if saving required. Only tiff
        format enabled, and this is a duplicate of the scan controller
        method

        Args:
            frame (np.ndarray): camera frame
        """
        if self.saveOpt:
            self.saveImage(frame,
                           self.saveSubfolder,
                           )

    def startNextStep(self):
        """
        Update live reconstruction, stop OPT in case of last step,
        otherwise move motor again.
        """
        # # updating live reconstruction (DP: doing it in processFrame)
        self.currentStep += 1

        if self.currentStep > len(self.optSteps) - 1:
            self.stopOPTScan()
        else:
            self.timeMonitor.addStamp('motor', self.currentStep, 'beg')
            self.master.rotatorsManager[self.rotatorName].move_abs(
                self.optSteps[self.currentStep], inSteps=True,
                )

    def stopOPTScan(self):
        """
        Ends the requested OPT scan. The scan can either naturally end,
        or the user may trigger the stop via the user interface.
        """
        self.timeMonitor.addFinish()
        self.master.detectorsManager[self.detectorName].stopAcquisition()
        self.isOPTScanRunning = False
        self.timeMonitor.makeReport()
        self.sigScanDone.emit()

    def computeLiveReconstruction(self, frame: np.ndarray):
        """
        Updates current live reconstruction object, which
        is FBPliveRecon class. In the first step, create new Recon object.
        Also ensures that the reconstruction index is within the limits
        of number of lines of the camera frame.

        Args:
            frame (np.ndarray): camera frame.
        """
        # check validity of the recon index user chose.
        if self.currentStep == 0:
            self.validateReconIdx(frame)

        try:  # update of existing reconstruction
            self.currentLiveRecon.update_recon(
                frame[self.reconIdx, :],
                self.currentStep)
        except AttributeError:  # in the first step, new recon object created.
            self.__logger.info(
                f'Creating a new reconstruction object. {len(self.optSteps)}',
                )

            self.currentLiveRecon = FBPliveRecon(
                frame[self.reconIdx, :],
                len(self.optSteps),
                )

    def validateReconIdx(self, frame: np.ndarray) -> None:
        """
        Check if reconstruction index is within the 
        limits of frame lines. If not, change the index to
        middle line of the frame, and trigger update of the 
        displayed number in the controller.

        Args:
            frame (np.ndarray): Snapped frame from the camera.
        """
        if 0 <= self.reconIdx < frame.shape[0]:  # recon index valid
            return

        # trigger update of the reconstruction index
        self.sigUpdateReconIdx.emit(frame.shape[0] // 2)
        self.__logger.warning(
            f'Live-reconstruction changed to {frame.shape[0] // 2}')

    def saveImage(self, frame: np.ndarray, fileExtension: str = "tiff"):
        """
        Constructs saving path and saves the image. Method adapted from
        UC2/STORMreconController from https://github.com/openUC2 fork of
        imswitch.

        Args:
            frame (np.ndarray): image array
            subfolder (str): datetime string for unique folder identification
            filename (str, optional): part of the filename can be specified.
                Defaults to "corr".
            fileExtension (str, optional): Image format. Defaults to "tiff".
        """
        filePath = self.getSaveFilePath(
                            subfolder=self.saveSubfolder,
                            filename=f'{self.currentStep:04}',
                            extension=fileExtension)

        tif.imwrite(filePath, frame, append=False)

    def getSaveFilePath(self, subfolder: str,
                        filename: str,
                        extension: str,
                        ) -> os.path:
        """ Sets datetime part of the filename, combines parts of the
        filename, ensures existance of the saving folder and returns
        the full savings path

        Args:
            subfolder (str): subfolder name
            filename (str): specific filename string part
            extension (str): image format extension

        Returns:
            os.path: save path
        """
        if subfolder == 'Corrections':
            date = datetime.now().strftime("%Y_%m_%d-%H-%M-%S")
        else:
            date = datetime.now().strftime("%H-%M-%S")
        mFilename = f"{date}_{filename}.{extension}"
        dirPath = os.path.join(dirtools.UserFileDirs.Root,
                               'recordings',
                               subfolder,
                               )

        newPath = os.path.join(dirPath, mFilename)

        if not os.path.exists(dirPath):
            os.makedirs(dirPath)

        return newPath


class OptController(ImConWidgetController):
    """ Optical Projection Tomography (OPT) scan controller. """
    sigImageReceived = Signal(str, np.ndarray)  # (name, frame array), used for corrections

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self)

        # Local flags
        self.saveOpt = True

        # select cameras based on the forOPt flag
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.forOptDetectorsList = [name for name in allDetectorNames if self._master.detectorsManager[name].forOpt]
        if self.forOptDetectorsList:
            self.detectorName = None
            self.detector = None
        else:
            self.__logger.error('No detector for OPT found.')

        # update detector list in the widget and connect update method
        self._widget.scanPar['Detector'].currentIndexChanged.connect(self.updateDetector)
        self.updateDetector()

        for detector in self.forOptDetectorsList:
            self._widget.scanPar['Detector'].addItem(detector)

        # rotators list
        self.rotatorsList = self._master.rotatorsManager.getAllDeviceNames()
        self.rotator = None         # from rotatorsManager by rotatorName
        self.rotatorName = None     # from rotatorsManager
        self.stepsPerTurn = 0  # rotator steps per turn (upper limit for OPT)

        self._widget.scanPar['Rotator'].currentIndexChanged.connect(
                                            self.updateRotator,
                                            )
        self.updateRotator()

        for rotator in self.rotatorsList:
            self._widget.scanPar['Rotator'].addItem(rotator)

        # Connect widget signals
        self._widget.scanPar['GetHotPixels'].clicked.connect(self.execHotPixelCorrection) # noqa
        self._widget.scanPar['GetDark'].clicked.connect(self.execDarkFieldCorrection)  # noqa
        self._widget.scanPar['GetFlat'].clicked.connect(self.execFlatFieldCorrection) # noqa
        self._widget.scanPar['LiveReconButton'].clicked.connect(self.updateLiveReconFlag) # noqa
        self._widget.scanPar['OptStepsEdit'].valueChanged.connect(self.updateOptSteps) # noqa

        # Scan loop control
        self._widget.scanPar['StartButton'].clicked.connect(self.prepareOPTScan) # noqa
        self._widget.scanPar['StopButton'].clicked.connect(self.requestInterruption) # noqa
        self._widget.scanPar['PlotReportButton'].clicked.connect(self.plotReport) # noqa

        # OPT worker thread
        self.optThread = Thread()
        self.optWorker = ScanOPTWorker(self._master,
                                       self.detectorName,
                                       self.rotatorName,
                                       )
        self.optWorker.moveToThread(self.optThread)
        self.updateLiveReconFlag()  # has to be after optWorker init

        # live recon, needs to be after worker init (DP: not so elegant
        # to put all flags to the worker no?)
        self._widget.scanPar['LiveReconIdxEdit'].valueChanged.connect(
                                                    self.getLiveReconIdx)

        # noRAM flag
        self._widget.scanPar['noRamButton'].clicked.connect(self.updateRamFlag)
        self.updateRamFlag()

        # saving flag, needs to be after worker init
        self._widget.scanPar['SaveButton'].clicked.connect(self.updateSaveFlag)
        self.updateSaveFlag()

        # Communication channel signals connection
        # sigRotatorPositionUpdated carries the name of the current rotator
        self._commChannel.sigRotatorPositionUpdated.connect(
            lambda _: self.optWorker.postRotatorStep(),
            )

        # Worker signals connection
        self.optWorker.sigNewFrameCaptured.connect(self.displayImage)
        self.optWorker.sigNewStabilityTrace.connect(self.updateStabilityPlot)
        self.optWorker.sigScanDone.connect(self.postScanEnd)
        self.optWorker.sigNewSinogramDataPoint.connect(
                                        self.checkSinogramProgress)
        self.optWorker.sigUpdateReconIdx.connect(self.setLiveReconIdx)
        self.optWorker.sigNewLiveRecon.connect(self.updateLiveReconPlot)

        # Thread signals connection
        self.optThread.started.connect(lambda: self.optWorker.preStart(
            self.optSteps))

        # setup UI
        self._widget.updateCurrentStep(0)
        self.enableWidget(True)

    #################
    # Main OPT scan #
    #################
    def prepareOPTScan(self):
        """ Makes preliminary checks for the OPT scan."""
        # resetting step count on UI
        self._widget.updateCurrentStep(0)

        self.optSteps = self.getOptSteps()
        self.setSharedAttr(self.rotatorName, 'nSteps', self.optSteps)
        self.setSharedAttr(self.rotatorName, 'stepsPerTurn', self.stepsPerTurn)

        if self._widget.scanPar['MockOpt'].isChecked():
            if not self._widget.requestMockConfirmation():
                return
            self._widget.setProgressBarVisible(True)
            self._widget.setProgressBarMaximum(self.optSteps)
            self.optWorker.demoEnabled = True
        else:
            # check if any HW is mock
            # TODO: Not HW agnostic, so added try except
            try:
                if self.detector.name == 'mock' or self.rotator.name == 'mock':
                    self.__logger.error(
                        'Select Demo, OPT cannot run with mock HW.')
                    return
            except:
                pass

            self.optWorker.demoEnabled = False
            # Checking for divisability of motor steps and OPT steps.
            if self.stepsPerTurn % self.optSteps != 0:
                # ask for confirmation
                if not self._widget.requestOptStepsConfirmation():
                    return

        self.setSharedAttr('scan', 'demo', self.optWorker.demoEnabled)
        self.optWorker.saveSubfolder = datetime.now().strftime(
                                            "%Y_%m_%d-%H-%M-%S",
                                            )
        self.sigImageReceived.connect(self.displayImage)

        # equidistant steps for the OPT scan in absolute values.
        self.optWorker.optSteps = np.linspace(0, self.stepsPerTurn,
                                              self.optSteps,
                                              endpoint=False,
                                              ).astype(np.int_)
        # tolist() because of the int32 conversion
        self.setSharedAttr('scan', 'absSteps', self.optWorker.optSteps.tolist())
        self.optWorker.timeMonitor.reinitContainers()

        # live reconstruction
        self.setSharedAttr('scan', 'liveRecon', self.optWorker.isLiveRecon)
        if self.optWorker.isLiveRecon:
            self.getLiveReconIdx()

        # starting scan
        self.enableWidget(False)
        self.optThread.start()

    def postScanEnd(self):
        """ Triggered after the end of the OPT scan. """
        # save metadata
        # Camera settings 
        self.setSharedAttr(self.detectorName, 'name', self.detector.name)
        self.setSharedAttr(self.detectorName,
                           'exposure',
                           self.detector.getExposure())
        self.setSharedAttr(self.detectorName, 'exposure unit', 'us')

        stab = self.optWorker.signalStability.getStabilityTraces()
        self.setSharedAttr('scan', 'stability', stab)
        self.setSharedAttr('scan', 'timeReport',
                           self.optWorker.timeMonitor.outputReport)
        self.saveMetadata()

        self._logger.info('OPT scan finished.')
        self.optWorker.isInterruptionRequested = False  # reset interrupt flag
        self.optThread.quit()  # stop the worker thread
        self.optWorker.waitConst = None  # reset wait constant
        self._widget.updateCurrentStep(0)
        self.enableWidget(True)

    def requestInterruption(self):
        """ Request interruption of the OPT scan. """
        self.optWorker.isInterruptionRequested = True

    ##################
    # Image handling #
    ##################
    def displayImage(self, name: str, frame: np.ndarray) -> None:
        """
        Display stack or image in the napari viewer.
        TODO: everything is converted to uint16, however it should
        follow the dtype of the incomming frames.

        Args:
            name (`str`): napari layer name
            frame (`np.ndarray`): image or stack
            step (`int`): current OPT scan step
        """
        # subsample stack
        if self.optWorker.isOPTScanRunning and not self.optWorker.noRAM:
            self._widget.setImage(np.uint16(frame),
                                  colormap="gray",
                                  name=name,
                                  pixelsize=(1, 1),
                                  translation=(0, 0),
                                  # change because otherwise current step needs to be part of emitted signal
                                  step=self.optWorker.currentStep)
        else:
            self._widget.setImage(np.uint16(frame),
                                  colormap="gray",
                                  name=name,
                                  pixelsize=(1, 1),
                                  translation=(0, 0),
                                  )

        if self.optWorker.isOPTScanRunning:
            # update labels step labels in the widget
            self._widget.updateCurrentStep(self.optWorker.currentStep + 1)

    def saveImage(self, frame, subfolder, filename="corr",
                  fileExtension="tiff"):
        """
        Constructs saving path and saves the image. Method adapted from
        UC2/STORMreconController from https://github.com/openUC2 fork of
        imswitch.

        Args:
            frame (np.ndarray): image array
            subfolder (str): datetime string for unique folder identification
            filename (str, optional): part of the filename can be specified.
                Defaults to "corr".
            fileExtension (str, optional): Image format. Defaults to "tiff".
        """
        filePath = self.getSaveFilePath(
                            subfolder=subfolder,
                            filename=filename,
                            extension=fileExtension)

        self._logger.debug(filePath)
        tif.imwrite(filePath, frame, append=False)

    def getSaveFilePath(self, subfolder: str,
                        filename: str,
                        extension: str,
                        ) -> os.path:
        """ Sets datetime part of the filename, combines parts of the
        filename, ensures existance of the saving folder and returns
        the full savings path

        Args:
            subfolder (`str`): subfolder name
            filename (`str`): specific filename string part
            extension (`str`): image format extension

        Returns:
            os.path: save path
        """
        if subfolder == 'Corrections':
            date = datetime.now().strftime("%Y_%m_%d-%H-%M-%S")
        else:
            date = datetime.now().strftime("%H-%M-%S")
        mFilename = f"{date}_{filename}.{extension}"
        dirPath = os.path.join(dirtools.UserFileDirs.Root,
                               'recordings',
                               subfolder,
                               )

        newPath = os.path.join(dirPath, mFilename)

        if not os.path.exists(dirPath):
            os.makedirs(dirPath)

        return newPath

    ################
    # Plot methods #
    ################
    def updateLiveReconPlot(self, image, step):
        """
        Dispaly current live reconstruction image.

        Args:
            image (np.ndarray): FBP live reconstruction
        """
        self._widget.liveReconPlot.clear()
        self._widget.liveReconPlot.setImage(image)
        self._widget.updateCurrentReconStep(step + 1)

    def plotReport(self):
        """Display an extra time monitor report plot in a separate widget.
        """
        self._widget.plotReport(self.optWorker.timeMonitor.getReport())

    ##################
    # Helper methods #
    ##################
    def checkSinogramProgress(self, step: int) -> None:
        """ Update the progress bar of the sinogram generation. """
        if step == self.optSteps - 1:
            self._widget.setProgressBarValue(0)
            self._widget.setProgressBarVisible(False)
        else:
            self._widget.setProgressBarValue(step)

    def setSharedAttr(self, HWName: str, attr: str, value) -> None:
        """
        Setting one shared attribute key, value pair. Key is a tuple of
        identifiers

        Args:
            HWName (str): hardware part
            attr (str): attribute name
            value (_type_): value of the attribute
        """
        self._commChannel.sharedAttrs[(_attrCategory, HWName, attr)] = value

    def saveMetadata(self) -> None:
        """ Get metadata and save them as json file to the experimental
        folder as metadata.json.
        """
        metadata = self._commChannel.sharedAttrs.getJSON()
        path = self.getSaveFilePath(self.optWorker.saveSubfolder,
                                    'metadata', 'json')
        with open(path, "w") as outfile:
            json.dump(metadata, outfile)

    def enableWidget(self, value: bool) -> None:
        """ Upon starting/stopping the OPT, widget
        editable fields get enabled from the bool value.

        Args:
            value (bool): enable value, False means disable
        """
        self._widget.scanPar['StartButton'].setEnabled(value)
        self._widget.scanPar['StopButton'].setEnabled(not value)
        self._widget.scanPar['PlotReportButton'].setEnabled(value)

        self._widget.scanPar['Detector'].setEnabled(value)
        self._widget.scanPar['Rotator'].setEnabled(value)

        self._widget.scanPar['OptStepsEdit'].setEnabled(value)
        self._widget.scanPar['GetDark'].setEnabled(value)
        self._widget.scanPar['GetFlat'].setEnabled(value)
        self._widget.scanPar['GetHotPixels'].setEnabled(value)
        self._widget.scanPar['AveragesEdit'].setEnabled(value)
        self._widget.scanPar['MockOpt'].setEnabled(value)

        self._widget.scanPar['LiveReconButton'].setEnabled(value)
        self._widget.scanPar['LiveReconIdxEdit'].setEnabled(value)

        self._widget.scanPar['SaveButton'].setEnabled(value)
        self._widget.scanPar['noRamButton'].setEnabled(value)

    def updateRotator(self):
        """ Update rotator attributes when rotator is changed.
        setting an index of the motor, motor_steps describe
        number of steps per revolution (resolution of the motor),
        also displayed in the widget.
        """
        self.rotatorName = self.rotatorsList[self._widget.getRotatorIdx()]
        self.rotator = self._master.rotatorsManager[self.rotatorName]
        self.stepsPerTurn = self.rotator._stepsPerTurn
        self._widget.scanPar['StepsPerRevLabel'].setText(
                                f'{self.stepsPerTurn:d} steps/rev',
                                )

    def updateDetector(self):
        """ Update detector attributes when detector is changed.
        Setting detectorName and detector object.
        """
        self.detectorName = self.forOptDetectorsList[
                                self._widget.getDetectorIdx()
                                ]
        self.detector = self._master.detectorsManager[self.detectorName]

    def getOptSteps(self):
        """ Get the total number of rotation steps for an OPT experiment. """
        return self._widget.getOptSteps()

    def updateOptSteps(self):
        """ Get current number of OPT steps and update label """
        self.optSteps = self.getOptSteps()
        self._widget.updateCurrentStep()
        self._widget.updateCurrentReconStep()

    def getStdCutoff(self):
        """ Get the STD cutoff for Hot pixels correction. """
        return self._widget.getHotStd()

    def getAverages(self):
        """ Get number of averages for camera correction. """
        return self._widget.getAverages()

    def setLiveReconButton(self, value: bool):
        """ Set live reconstruction Checkbox.

        Args:
            value (bool): True means live reconstruction active
        """
        self._widget.scanPar['LiveReconButton'].setChecked(value)

    def updateLiveReconFlag(self):
        """ Update live reconstruction flag based on the widget value """
        self.optWorker.isLiveRecon = self._widget.scanPar[
                                        'LiveReconButton'].isChecked()
        # enable/disable live-recon index
        self._widget.scanPar['LiveReconIdxEdit'].setEnabled(
                                        self.optWorker.isLiveRecon,
                                        )

    def updateSaveFlag(self):
        """ Update saving flag from the widget value """
        self.optWorker.saveOpt = self._widget.scanPar['SaveButton'].isChecked()

    def updateRamFlag(self):
        """ Update noRAM flag from the widget value """
        self.optWorker.noRAM = self._widget.scanPar['noRamButton'].isChecked()

    def updateStabilityPlot(self, steps: list, intensity: Dict[str, list]):
        """ Update OPT stability plot from 4 corners of the stack via
        widget function.

        Args:
            steps (list): list of OPT steps
            intensity (List[list]): list of intensity values for each corner
        """
        self._widget.updateStabilityPlot(steps, intensity)

    def getLiveReconIdx(self) -> None:
        """ Get camera line index for the live reconstruction. """
        self.optWorker.reconIdx = self._widget.getLiveReconIdx()

    def setLiveReconIdx(self, value: int):
        """ Set camera line index for the live reconstruction

        Args:
            value (int): camera line index
        """
        # triggers getLiveReconIdx via valueChange
        self._widget.setLiveReconIdx(value)

    ###################
    # Message windows #
    ###################
    def execHotPixelCorrection(self):
        """
        Block camera message before acquisition of the dark-field counts,
        used for identification of hot pixels. This acquires
        the correction, but does not correct data.
        """
        std_cutoff = self.getStdCutoff()
        averages = self.getAverages()
        self.setSharedAttr('scan', 'averagesHot', averages)
        if not self.requestHotPixelConfirmation(averages, std_cutoff):
            return
        self.acquireCorrection('hot_pixels', averages)

    def execDarkFieldCorrection(self):
        """
        Block camera message before acquisition of the dark-field
        counts, used for identification of hot pixels. This acquires
        the correction, but does not correct data.
        """
        averages = self.getAverages()
        self.setSharedAttr('scan', 'averagesDark', averages)
        if not self.requestDarkFieldConfirmation(averages):
            return
        self.acquireCorrection('dark_field', averages)

    def execFlatFieldCorrection(self):
        """
        Instruction message for the bright-field correction. Exposure
        time should be the same as for the dark-field and subsequent
        experiment. This acquires the correction, but does not correct
        the data.
        """
        averages = self.getAverages()
        self.setSharedAttr('scan', 'averagesFlat', averages)
        if not self.requestFlatFieldConfirmation(averages):
            return
        self.acquireCorrection('flat_field', averages)

    def requestHotPixelConfirmation(self, averages: int, cutoff: float):
        text = f"Reinitialize camera with maximum exposure time possible.\
            Saved frame is a frame averaged {averages}x. Hot pixels will \
            be identified as intensity higher than {cutoff}x STD, and \
            their count shown for reference"
        return guitools.askYesNoQuestion(self._widget,
                                         "Confirm Hot-pixel acquisition.",
                                         " ".join(text.split()))

    def requestDarkFieldConfirmation(self, averages: int):
        text = f"Acquire does {averages} averages at current exposure time.\
            Exposure time MUST be the same as for the\
            experiment you are going to perform."
        return guitools.askYesNoQuestion(self._widget,
                                         "Confirm Dark-field acquisition.",
                                         " ".join(text.split()))

    def requestFlatFieldConfirmation(self, averages: int):
        text = f"Only for transmission mode. You should have flat \
            field illumination within the linear regime. Acquisition will\
            perform {averages} averages at current exposure time.\
            It should be the same number of averages as for the dark-field."
        return guitools.askYesNoQuestion(self._widget,
                                         "Confirm Flat-field acquisition.",
                                         " ".join(text.split()))

    ##########################
    # Correction acquisition #
    ##########################
    def acquireCorrection(self, corr_type, n):
        self.sigImageReceived.connect(self.displayImage)
        self.nFrames.connect(partial(self._continue, corr_type=corr_type))
        self.getNframes(n)

    def _continue(self, corr_type):
        """ Triggered by recieving a signal nFrames that
        correction frame stack is ready. Calls specific correction
        processing method and disconnects acquisition signals.

        Args:
            corr_type (str): type of camera correction (hot_pixels, dark_field,
            flat_field)

        Raises:
            ValueError: In the case of unknown corr_type
        """
        exec(f'self.{corr_type} = self.current_frame')

        # process hot pixel acquisition
        if corr_type == 'hot_pixels':
            self.process_hot_pixels()
        elif corr_type == 'dark_field':
            self.process_dark_field()
        elif corr_type == 'flat_field':
            self.process_flat_field()
        else:
            raise ValueError
        self.nFrames.disconnect()
        self.sigImageReceived.disconnect()

    def process_hot_pixels(self):
        """
        Automatic saving of the correction to the /Corrections folder.
        Based on the selected STD cutoff in the widget identifies pixels which
        have intensity higher than mean of all pixels + STD cutoff multiples
        of STD. Calculates and displays count of hot pixels and average
        intensity of both hot and non-hot pixels.
        """
        self.saveImage(self.hot_pixels, 'Corrections', 'corr_hot')
        std_cutoff = self.getStdCutoff()
        std = np.std(self.hot_pixels, dtype=np.float64)
        mean = np.mean(self.hot_pixels, dtype=np.float64)
        # hot_std is the cutoff
        hot_vals = self.hot_pixels[self.hot_pixels > (mean + std_cutoff*std)]
        hot = np.ma.masked_greater(self.hot_pixels, mean + std_cutoff*std)

        self._widget.updateHotPixelCount(len(hot_vals))
        self._widget.updateHotPixelMean(np.mean(hot_vals))
        self._widget.updateNonHotPixelMean(np.mean(hot))

        self.sigImageReceived.emit('hot_pixels', self.hot_pixels)

    def process_dark_field(self):
        """
        Saves the correction, displays mean and STD of all the
        camera pixels.
        """
        self.saveImage(self.dark_field, 'Corrections', 'dark_field')
        mean, std = np.mean(self.dark_field), np.std(self.dark_field)
        self._widget.updateDarkMean(mean)
        self._widget.updateDarkStd(std)
        self.setSharedAttr('scan', 'darkMeanStd', (mean, std))

        self.sigImageReceived.emit('dark_field', self.dark_field)

    def process_flat_field(self):
        """
        Saves the correction, displays mean and STD of all the
        camera pixels.
        """
        self.saveImage(self.flat_field, 'Corrections', 'flat_field')
        mean, std = np.mean(self.flat_field), np.std(self.flat_field)
        self._widget.updateFlatMean(mean)
        self._widget.updateFlatStd(std)
        self.setSharedAttr('scan', 'flatMeanStd', (mean, std))

        self.sigImageReceived.emit('flat_field', self.flat_field)

    nFrames = Signal()

    def getNframes(self, n):
        """
        Button triggers acquisition of self.n_frames
        frames, each averaged or accumulated.

        In case of OPT acquisition, all these frames
        will be saved at each angle (motor step).
        """
        i = 0
        frames = []
        self.detector.startAcquisition()
        while i < n:
            frame = self.detector.getLatestFrame()
            # checking if valid frame received.
            if frame.shape[0] != 0:
                frames.append(frame)
                i += 1
        # averaging aver n frames
        self.current_frame = np.mean(np.array(frames),
                                     axis=0).astype(np.int16)
        self.detector.stopAcquisition()
        self.nFrames.emit()


_attrCategory = 'OPT'


class Stability:
    """ Helper container class to monitor and display the stability traces
    of the intensity of the 4 corners of the OPT stack.
    The size of the rectangle is defined by the n_pixels parameter,
    (optional, defaults to 50 pxs)

    iUL -> upper left
    iUR -> upper right
    iLL -> lower left
    iLR -> lower right
    """

    def __init__(self, n_pixels: int = 50) -> None:
        # rectangle size in pxs to monitor mean intensity at 4 corners
        self.n_pixels = n_pixels
        self.clear()

    def clear(self):
        """Clear the variables between experiments. """
        self.steps = []
        self.intensity = {'UL': [],
                          'UR': [],
                          'LL': [],
                          'LR': []}

    def getStabilityTraces(self) -> Tuple[List, Dict]:
        """Getter for the steps and stability traces.

        Returns:
            Tuple[List, Dict]: list of steps (x axis), second is dictionary of
            corner intensity traces for each step.
        """
        return self.steps, self.intensity

    def processStabilityTraces(self, frame: np.ndarray, step: int) -> Tuple[List, Dict[str, List]]:
        """ Process the current frame's stability traces.

        Args:
            frame (`np.ndarray`): input frame
            step (`int`): current OPT scan step index

        Returns:
            Tuple[list, Dict[str, list]]: list of presently executed OPT
                scan steps and dictionary of intensity traces
                for the four corners
        """
        mean_corners = [
            np.mean(frame[:self.n_pixels, :self.n_pixels]),    # UL
            np.mean(frame[:self.n_pixels, -self.n_pixels:]),   # UR
            np.mean(frame[-self.n_pixels:, :self.n_pixels]),   # LL
            np.mean(frame[-self.n_pixels:, -self.n_pixels:]),  # LR
        ]

        self.steps.append(step)
        if step == 0:
            # I append ones and save values as normalization factors
            self.norm_factors = tuple(mean_corners)
            for i in self.intensity.keys():
                self.intensity[i].append(1.)
        else:
            for i, key in enumerate(self.intensity.keys()):
                self.intensity[key].append(mean_corners[i] / self.norm_factors[i])

        return self.steps, self.intensity


class FBPliveRecon():
    def __init__(self, line: np.ndarray, steps: int) -> None:
        """Init function already called with the first projection (line)
        which will be reconstructed. This is because many preallocation
        methods depend on the knowledge of line dimension.

        Args:
            line (np.ndarray): single projection, i.e. slice of the sinogram.
            steps (int): number of total OPT steps. Crucial because angles
                has to be known in advance.

        Raises:
            ValueError: liveRecon class can handle only siblge slice projection
                therefore input has to be 1D array
        """
        if not isinstance(line, np.ndarray):
            try:
                self.line = np.array(line)
            except:
                raise TypeError(
                    f"{type(line)} cannot be converted to NumPy array",
                    )
        else:
            self.line = line        # experimental slice of single projection
        self.n_steps = steps    # total OPT steps
        self.step = 0           # counter of steps, emitted for update plot
        if self.line.ndim > 1:       # 3D reconstruction
            raise ValueError('Input data can be only 1D array')

        # preallocation
        self.sinogram = np.zeros((len(self.line), steps))
        self.recon_dim = len(self.line)
        self.recon = np.zeros((self.recon_dim, self.recon_dim))

        self.radon_img = self._sinogram_circle_to_square(self.sinogram)
        self.radon_img_shape = self.radon_img.shape[0]
        self.offset = (self.radon_img_shape - self.recon_dim)//2
        self.projection_size_padded = max(
                64,
                int(2 ** np.ceil(np.log2(2 * self.radon_img_shape))))
        self.radius = self.recon_dim // 2
        self.xpr, self.ypr = np.mgrid[:self.recon_dim,
                                      :self.recon_dim] - self.radius

        self.x = np.arange(self.radon_img_shape) - self.radon_img_shape // 2

        # convert to radians
        self.theta = np.deg2rad(
                        np.linspace(0., 360., self.n_steps, endpoint=False)
                        )
        self.update_recon(self.line, 0)

    def update_recon(self, line_in: np.ndarray,
                     step: int,
                     interp_mode='linear',
                     ) -> None:
        """
        Updates the reconstruction by adding a new line of data which is
        getting projected by inverse radon.

        Args:
            line_in (np.ndarray): The input line data.
            step (int): The current step in the reconstruction process.
            interp_mode (str, optional): The interpolation mode.
                Defaults to 'linear'.

        Returns:
            None
        """
        self.line = line_in
        self.step = step
        fourier_filter = self._get_fourier_filter(self.projection_size_padded)
        # padding line
        if self.line.ndim > 1:  # 3D reconstruction
            raise ValueError('Input data can be only 1D array')

        line = np.zeros(self.projection_size_padded)
        line[self.offset:len(line_in)+self.offset] = line_in

        # fft filtering of the line
        projection = fft(line) * fourier_filter
        radon_filtered = np.real(ifft(projection)[:self.radon_img_shape])

        # rotational transformation fo the projections
        t = (self.ypr * np.cos(self.theta[step]) -
             self.xpr * np.sin(self.theta[step]))

        # interpolation on the circle
        if interp_mode == 'cubic':
            interpolant = interp1d(self.x, radon_filtered, kind='cubic',
                                   bounds_error=False, fill_value=0)
        else:  # default interpolation is linear
            interpolant = interp1d(self.x, radon_filtered, kind='linear',
                                   bounds_error=False, fill_value=0)

        # superimposing onto previous projections
        self.recon += interpolant(t) * (np.pi/(2*self.n_steps))

    def _get_fourier_filter(self, size: int) -> np.ndarray:
        """ size needs to be even. Only ramp filter implemented """
        n = np.concatenate((np.arange(1, size / 2 + 1, 2, dtype=int),
                            np.arange(size / 2 - 1, 0, -2, dtype=int)))
        f = np.zeros(size)
        f[0] = 0.25
        f[1::2] = -1 / (np.pi * n) ** 2

        # Computing the ramp filter from the fourier transform of its
        # frequency domain representation lessens artifacts and removes a
        # small bias as explained in [1], Chap 3. Equation 61
        fourier_filter = 2 * np.real(fft(f))         # ramp filter
        return fourier_filter

    def _sinogram_circle_to_square(self, sinogram: np.ndarray) -> np.ndarray:
        """
        Converts a sinogram from circular to square shape.

        Parameters:
        sinogram (ndarray): The input sinogram in circular shape.

        Returns:
        ndarray: The sinogram in square shape.

        """
        diagonal = int(np.ceil(np.sqrt(2) * sinogram.shape[0]))
        pad = diagonal - sinogram.shape[0]
        old_center = sinogram.shape[0] // 2
        new_center = diagonal // 2
        pad_before = new_center - old_center
        pad_width = ((pad_before, pad - pad_before), (0, 0))
        return np.pad(sinogram, pad_width, mode='constant', constant_values=0)


# These functions are adapted from tomopy package
# https://tomopy.readthedocs.io/en/stable/


# Copyright (C) 2020-2024 ImSwitch developers
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
