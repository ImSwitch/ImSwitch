from PyQt5 import QtWidgets
from scipy.fftpack import fft, ifft
from scipy.interpolate import interp1d
import tifffile as tif
import os
from datetime import datetime
from collections import defaultdict

from functools import partial
import numpy as np
from typing import Tuple, List, Callable
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger, dirtools
from imswitch.imcommon.framework import Signal, Thread, Worker
from skimage.transform import radon


class ScanExecutionMonitor:
    """ Helper class dedicated to monitor the execution time of an OPT scan.
    It can be used to generate an experiment report with timing informations
    relative to each step of the scan execution. It is also saved in the
    metadata file of the experiment.
    """
    def __init__(self):
        # TODO: move this class to the utilities folder and extend its usage
        # to the rest of the application
        self.outputReport = {}
        self.report = defaultdict(lambda: [])

    def addStamp(self, key: str, idx: int, tag: str):
        """ Add a time stamp to the report.

        Args:
            key (`str`): identifier of the stamp; monitors the type of operation recorded.
            idx (`int`): index of the current OPT scan step.
            tag (`str`): tag to identify the beginning ("beg") or the end ("end") of the operation.
        """
        self.report[key].append((idx, tag, datetime.now()))

    def addStart(self) -> None:
        """ Adds a starting key to the report. """
        self.report['start'] = datetime.now()

    def addFinish(self) -> None:
        """ Adds an ending key to the report. """
        self.report['end'] = datetime.now()
        try:
            self.totalTime = (self.report['end'] - self.report['start']).total_seconds()
        except KeyError:
            # TODO: ??? why should there be an exception?
            # if the class is reused, and addStart() is not called before addFinish,
            # try will fail.
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

        report = {}
        report['Total'] = np.sum(diffs)                 # total time spent on the task
        report['Mean'] = np.mean(diffs)                 # mean time per step
        report['STD'] = np.std(diffs)                   # STD of time per step
        report['Tseries'] = np.array([steps, diffs]).T  # timeseries of times per step
        report['PercTime'] = np.sum(diffs)/self.totalTime * 100  # percentage of total exp. time

        # put the task dictionary into the report dictionary
        self.outputReport[key] = report


class ScanOPTWorker(Worker):
    """ OPT scan worker. The worker operates on a separate thread
    from the main application thread. It is responsible for the execution
    of the OPT scan (moving the rotator, acquiring an image, updating plots
    light intensity stability). The worker is also responsible for
    the live reconstruction of the acquired frames, if the option is enabled.

    Args:
        master (`MasterController`): reference to the master controller; used to access the
        detectorName (`str`): name identifier of the detector used for the OPT scan.
        rotatorName (`str`): name identifier of the rotator used for the OPT scan.
    """
    sigNewFrameCaptured = Signal(str, np.ndarray, int)  # (layerLabel, frame, optCurrentStep)
    sigNewStabilityTrace = Signal(object, object)  # (list: steps, list[list]: stabilityTraces)
    sigScanDone = Signal()

    def __init__(self, master, detectorName, rotatorName) -> None:
        super().__init__()
        self.master = master
        self.detectorName = detectorName
        self.rotatorName = rotatorName
        self.timeMonitor = ScanExecutionMonitor()
        self.signalStability = Stability()

        # rotator configuration values
        self.optSteps = None
        self.currentStep = 0

        # monitor flags
        self.isOPTScanRunning = False             # OPT scan running flag, default to False
        self.noRAM = False                    # Stack not saved to RAM and Viewwer to save memory
        self.isLiveRecon = False              # OPT live reconstruction flag, default to False
        self.isInterruptionRequested = False  # interruption request flag, set from the main thread; defaults to False
        self.frameStack = None                # OPT stack memory buffer

        # Demo parameters, synthetic phantom data are generated to emulate OPT scan
        self.demoEnabled = False         # Demo mode flag; if True synthetic data generated; defaults to False
        self.sinogram: np.ndarray = None # Demo sinogram; default to None

    def startOPTScan(self):
        """ Performs the first step of the OPT scan, triggering an asynchronous
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
        self.master.detectorsManager[self.detectorName].startAcquisition()
        self.isOPTScanRunning = True

        # TODO: how to save the final report in image metadata?
        self.timeMonitor.addStart()
        self.currentStep = 0

        # we select the frame retrieval method based off the demo flag
        self.getFrame: Callable = self.getFrameFromSino if self.demoEnabled else self.snapCamera

        # we move the rotator to the first position
        self.timeMonitor.addStamp('motor', self.currentStep, 'beg')
        self.master.rotatorsManager[self.rotatorName].move_abs(self.optSteps[self.currentStep], inSteps=True)

    def postRotatorStep(self):
        """ Triggered after emission of the `sigPositionUpdated` signal from
        the rotator. The method performs the following steps: 

        - captures the latest frame from the detector;
        - (optional) saves the frame if option is enabled;
        - updates the stability plot;
        - (optional) performs live reconstruction; 
        - triggers the next motor step.

        This workflow is repeated until all the rotational steps
        are completed, or when the `isInterruptionRequested` flag is raised
        by the main thread.
        """
        self.timeMonitor.addStamp('motor', self.currentStep, 'end')
        # DP: manual stepping also leads to here, continue only for OPT experiment
        if not self.isOPTScanRunning:
            return
        frame = self.getNextFrame()
        self.processFrameStability(frame, self.currentStep)
        self.saveCurrentFrame()
        if self.isInterruptionRequested:
            self.stopOPTScan()
        else:
            self.startNextStep()

    def snapCamera(self) -> np.ndarray:
        """Snap frame from the current camera.

        Returns:
            np.ndarray: frame array
        """
        return self.master.detectorsManager[self.detectorName].getLatestFrame()

    def getFrameFromSino(self) -> np.ndarray:
        """In case of demo experiment, frame is retrived
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
        """Appends frame to the stack (unless noRAM option), displays
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
        """ Processes the light stability of the incoming frame;
        the computed traces are then emitted to the main thread for display.

        Args:
            frame (`np.ndarray`): the incoming frame
            step (`int`): the current step of the OPT scan
        """
        self.timeMonitor.addStamp('stability', self.currentStep, 'beg')
        stepsList, intensityLists = self.signalStability.processStabilityTraces(frame, step)
        # TODO: sometimes not added to the dict
        self.timeMonitor.addStamp('stability', self.currentStep, 'end')
        self.sigNewStabilityTrace.emit(stepsList, intensityLists)

    def saveCurrentFrame(self) -> None:
        # TODO: implement
        # DP: You mean it should be on this thread,
        # instead of the handleSave in the ScanController, right?
        # JA: since it's part of the experiment workflow it makes sense;
        # JA: alternatively I can think of another solution with another thread...
        # JA: have to think about it a little
        pass

    def startNextStep(self):
        """
        Update live reconstruction, stop OPT in case of last step,
        otherwise move motor again.
        """
        # self._widget.updateCurrentStep(self.__currentStep + 1)

        # updating live reconstruction
        # TODO: live reconstruction section is unclear;
        # needs some details on the implementation to refactor
        # if self.liveRecon:
        #     self.timeMonitor.addStamp('live-recon', self.__currentStep, 'beg')
        #     self.updateLiveRecon()

        self.currentStep += 1

        if self.currentStep > len(self.optSteps) - 1:
            self.stopOPTScan()
        else:
            self.timeMonitor.addStamp('motor', self.currentStep, 'beg')
            self.master.rotatorsManager[self.rotatorName].move_abs(self.optSteps[self.currentStep], inSteps=True)

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

    def computeLiveReconstruction(self):
        # TODO: refactor old code here;
        pass


class ScanControllerOpt(ImConWidgetController):
    """ Optical Projection Tomography (OPT) scan controller.
    """
    sigImageReceived = Signal(str, np.ndarray)  # (name, frame array)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self)

        # Local flags
        self.liveRecon = False
        self.saveOpt = True

        # get detectors, select first one, connect update
        # Should it be synchronized with recording selector?
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detectorName = allDetectorNames[0]
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        self.rotatorsList = self._master.rotatorsManager.getAllDeviceNames()
        self.rotatorName = None
        self.stepsPerTurn = 0

        self._widget.scanPar['Rotator'].currentIndexChanged.connect(self.updateRotator)
        self.updateRotator()

        for rotator in self.rotatorsList:
            self._widget.scanPar['Rotator'].addItem(rotator)

        # Connect widget signals
        self._widget.scanPar['GetHotPixels'].clicked.connect(self.exec_hot_pixels)
        self._widget.scanPar['GetDark'].clicked.connect(self.exec_dark_field)
        self._widget.scanPar['GetFlat'].clicked.connect(self.exec_flat_field)
        self._widget.scanPar['LiveReconButton'].clicked.connect(self.updateLiveReconFlag)
        self.updateLiveReconFlag()

        # saving flag
        self._widget.scanPar['SaveButton'].clicked.connect(self.updateSaveFlag)
        self.updateSaveFlag()

        # live recon
        self._widget.scanPar['LiveReconIdxEdit'].valueChanged.connect(self.updateLiveReconIdx)
        self.updateLiveReconIdx()

        self._widget.scanPar['OptStepsEdit'].valueChanged.connect(self.updateOptSteps)

        # Scan loop control
        self._widget.scanPar['StartButton'].clicked.connect(self.prepareOPTScan)
        self._widget.scanPar['StopButton'].clicked.connect(self.requestInterruption)
        self._widget.scanPar['PlotReportButton'].clicked.connect(self.plotReport)

        # OPT worker thread
        self.optThread = Thread()
        self.optWorker = ScanOPTWorker(self._master,
                                       self.detectorName,
                                       self.rotatorName,
                                       )
        self.optWorker.moveToThread(self.optThread)

        # noRAM flag
        self._widget.scanPar['noRamButton'].clicked.connect(self.updateRamFlag)
        self.updateRamFlag()

        # Communication channel signals connection
        # sigRotatorPositionUpdated carries the name of the current rotator
        # that updated its position; we drop it because we control it via the UI
        self._commChannel.sigRotatorPositionUpdated.connect(
            lambda _: self.optWorker.postRotatorStep(),
            )

        # Worker signals connection
        self.optWorker.sigNewFrameCaptured.connect(self.displayImage)
        self.optWorker.sigNewStabilityTrace.connect(self.updateStabilityPlot)
        self.optWorker.sigScanDone.connect(self.postScanEnd)

        # Thread signals connection
        self.optThread.started.connect(self.optWorker.startOPTScan)

        # setup UI
        self.enableWidget(True)

    # JA: method to add your metadata to recordings
    # TODO: metadata still not taken care of, implement
    def setSharedAttr(self, rotatorName, meta1, meta2, attr, value):
        pass

    def requestInterruption(self):
        """ Request interruption of the OPT scan. """
        self.optWorker.isInterruptionRequested = True

    def postScanEnd(self):
        """ Triggered after the end of the OPT scan. """
        self._logger.info('OPT scan finished.')
        self.optWorker.isInterruptionRequested = False  # reset interruption flag
        self.optThread.quit()  # stop the worker thread
        self.enableWidget(True)

    #################
    # Main OPT scan #
    #################
    def prepareOPTScan(self):
        """ Initiate OPT scan. """

        def generateSyntheticSinogram(resolution: int = 128) -> np.ndarray:
            data = shepp3d(resolution)  # shepp-logan 3D phantom
            sinogram = np.zeros(data.shape)  # preallocate sinogram array
            angles = np.linspace(0, 360, resolution, endpoint=False)  # angles
            for i in range(resolution):
                sinogram[i, :, :] = radon(data[i, :, :], theta=angles)
            mx = np.amax(sinogram)
            return np.rollaxis((sinogram/mx*255).astype(np.uint8), 2)

        self.__optSteps = self.getOptSteps()

        if self._widget.scanPar['MockOpt'].isChecked():
            if not self._widget.requestMockConfirmation():
                return
            self._logger.info('Demo experiment: preparing synthetic data.')

            # here generate stack of projections
            self.optWorker.demoEnabled = True
            self.optWorker.sinogram = generateSyntheticSinogram(self.__optSteps)
            self._logger.info('Synthetic data ready.')
        else:
            # Checking for divisability of motor steps and OPT steps.
            if self.stepsPerTurn % self.__optSteps != 0:
                # ask for confirmation
                if not self._widget.requestOptStepsConfirmation():
                    return

        self.saveSubfolder = datetime.now().strftime("%Y_%m_%d-%H-%M-%S")
        self.sigImageReceived.connect(self.displayImage)

        # equidistant steps for the OPT scan in absolute values.
        optScanSteps = np.linspace(
                            0,
                            self.stepsPerTurn,
                            self.__optSteps,
                            endpoint=False,
                        ).astype(np.int_)
        self.optWorker.optSteps = optScanSteps

        # live reconstruction
        # if self.liveRecon:
        #     self.updateLiveReconIdx()
        #     self.currentRecon = None  # avoid update_recon in the first step
        self.enableWidget(False)
        self.optThread.start()

    def plotReport(self):
        self._widget.plotReport(self.optWorker.timeMonitor.getReport())

    ##################
    # Image handling #
    ##################
    # TODO: Call this in from
    def handleSave(self):
        if self.saveOpt:
            self.saveImage(self.frame,
                           self.saveSubfolder,
                           f'{self.__currentStep:04}')

    def displayImage(self, name: str, frame: np.ndarray) -> None:
        """
        Display stack or image in the napari viewer.

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
                                  # change because I do not want to put to the signal
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

    def updateLiveRecon(self):
        """
        Handles updating of the live Reconstruction plot.
        Safeguarding the possibility of index error when slice of camera
        is out of range. In that case center line of the image is used.
        """
        try:
            self.currentRecon.update_recon(
                self.frame[self.reconIdx, :],
                self.__currentStep)
        except AttributeError:
            try:
                self.__logger.info(f'Creating a new reconstruction object. {self.__optSteps}')
                self.currentRecon = FBPlive(
                    self.frame[self.reconIdx, :],
                    self.__optSteps)
            except (ValueError, IndexError):
                self._logger.warning(
                    'Index error, reconstructions changed to central line')
                self.setLiveReconIdx(self.frame.shape[0] // 2)
                print('recon idx',
                      self.reconIdx, self.frame.shape,
                      self.frame[self.reconIdx, :].shape,
                      )
                self.currentRecon = FBPlive(
                    self.frame[self.reconIdx, :],
                    self.__optSteps)
        try:
            self.updateLiveReconPlot(self.currentRecon.output)
        except TypeError:
            self._logger.info(f'Wrong type: {type(self.currentRecon.output)}')
        self.timeMonitor.addStamp('live-recon', self.__currentStep, 'end')

    def updateLiveReconPlot(self, image):
        """
        Dispaly current live reconstruction image.

        Args:
            image (np.ndarray): FBP live reconstruction
        """
        self._widget.liveReconPlot.clear()
        self._widget.liveReconPlot.setImage(image)
        self._widget.updateCurrentReconStep(self.__currentStep + 1)

    ##################
    # Helper methods #
    ##################
    def enableWidget(self, value: bool) -> None:
        """ Upon starting/stopping the OPT, widget
        editable fields get enabled from the bool value.

        Args:
            value (bool): enable value, False means disable
        """
        self._widget.scanPar['StartButton'].setEnabled(value)
        self._widget.scanPar['StopButton'].setEnabled(not value)
        self._widget.scanPar['PlotReportButton'].setEnabled(value)
        self._widget.scanPar['SaveButton'].setEnabled(value)
        self._widget.scanPar['LiveReconIdxEdit'].setEnabled(value)
        self._widget.scanPar['OptStepsEdit'].setEnabled(value)
        self._widget.scanPar['GetDark'].setEnabled(value)
        self._widget.scanPar['GetFlat'].setEnabled(value)
        self._widget.scanPar['GetHotPixels'].setEnabled(value)
        self._widget.scanPar['AveragesEdit'].setEnabled(value)
        self._widget.scanPar['MockOpt'].setEnabled(value)

    def updateRotator(self):
        """ Update rotator attributes when rotator is changed.
        setting an index of the motor, motor_steps describe
        number of steps per revolution (resolution of the motor),
        also displayed in the widget.
        """
        self.rotatorName = self.rotatorsList[self._widget.getRotatorIdx()]
        self.stepsPerTurn = self._master.rotatorsManager[self.rotatorName]._stepsPerTurn
        self._widget.scanPar['StepsPerRevLabel'].setText(f'{self.stepsPerTurn:d} steps/rev')

    def getOptSteps(self):
        """ Get the total number of rotation steps for an OPT experiment. """
        return self._widget.getOptSteps()

    def updateOptSteps(self):
        """ Get current number of OPT steps and update label """
        self.__optSteps = self.getOptSteps()
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
        self.liveRecon = self._widget.scanPar['LiveReconButton'].isChecked()
        # enable/disable live-recon index
        self._widget.scanPar['LiveReconIdxEdit'].setEnabled(self.liveRecon)

    def updateSaveFlag(self):
        """ Update saving flag from the widget value """
        self.saveOpt = self._widget.scanPar['SaveButton'].isChecked()

    def updateRamFlag(self):
        """ Update noRAM flag from the widget value """
        self.optWorker.noRAM = self._widget.scanPar['noRamButton'].isChecked()

    def updateStabilityPlot(self, steps: list, intensity: List[list]):
        """ Update OPT stability plot from 4 corners of the stack via
        widget function.

        Args:
            steps (list): list of OPT steps
            intensity (List[list]): list of intensity values for each corner
        """
        self._widget.updateStabilityPlot(steps, intensity)

    def updateLiveReconIdx(self) -> None:
        """ Get camera line index for the live reconstruction. """
        self.reconIdx = self._widget.getLiveReconIdx()

    def setLiveReconIdx(self, value: int):
        """ Set camera line index for the live reconstruction

        Args:
            value (int): camera line index
        """
        self._widget.setLiveReconIdx(value)

    ###################
    # Message windows #
    ###################
    def exec_hot_pixels(self):
        """
        Block camera message before acquisition of the dark-field counts,
        used for identification of hot pixels. This is separate operation
        from dark field correction.

        Returns:
            int: sys execution status.
        """
        # these two are call repeatedly, TODO: refactor
        std_cutoff = self.getStdCutoff()
        averages = self.getAverages()
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("Block Camera")
        text = f"Reinitialize camera with maximum exposure time possible.\
            Saved frame is a frame averaged {averages}x. Hot pixels will \
            be identified as intensity higher than {std_cutoff}x STD, and their count \
            shown for reference"
        msg.setInformativeText(" ".join(text.split()))
        msg.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        btn_measure = msg.button(QtWidgets.QMessageBox.Ok)
        btn_measure.setText('Acquire with current setting?')
        msg.buttonClicked.connect(
            partial(
                self.acquire_correction,
                corr_type='hot_pixels',
                n=averages))
        retval = msg.exec_()
        return retval

    def exec_dark_field(self):
        """
        Block camera message before acquisition of the dark-field
        counts, used for identification of hot pixels. This is
        separate operation from dark field correction.

        Returns:
            int: sys execution status.
        """
        averages = self.getAverages()
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("Block Camera")
        text = f"Acquire does {averages} averages at current exposure time.\
            Exposure time MUST be the same as for the\
            experiment you are going to perform."
        msg.setInformativeText(" ".join(text.split()))
        msg.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        btn_measure = msg.button(QtWidgets.QMessageBox.Ok)
        btn_measure.setText('Acquire NOW?')
        msg.buttonClicked.connect(
            partial(
                self.acquire_correction,
                corr_type='dark_field',
                n=averages))
        retval = msg.exec_()
        return retval

    def exec_flat_field(self):
        """
        Instruction message for the bright-field correction. Exposure
        time should be the same as for the dark-field and subsequent
        experiment. This is separate operation from bright-field correction.

        Returns:
            int: sys execution status.
        """
        averages = self.getAverages()
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("Unblock Camera")
        text = "Only for transmission mode.\
            You should have flat field illumination\
            within the linear regime. Acquisition will\
            perform 100x average at current exposure time.\
            The same as for dark-field."
        msg.setInformativeText(" ".join(text.split()))
        msg.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        btn_measure = msg.button(QtWidgets.QMessageBox.Ok)
        btn_measure.setText('Acquire with current setting?')
        msg.buttonClicked.connect(
            partial(
                self.acquire_correction,
                corr_type='flat_field',
                n=averages))
        retval = msg.exec_()
        return retval

    def acquire_correction(self, btn, corr_type, n):
        """ Handles correction acquisition, connects
        display signal and calls getNframes(n)

        Args:
            btn (pyqtbutton): button which user pressed
            corr_type (str): correction type selector
            n (int): number of frames for correction averaging
        """
        if btn.text() == 'Cancel':
            return

        self.sigImageReceived.connect(self.displayImage)
        self.nFrames.connect(
            partial(self._continue, corr_type=corr_type),
            )
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
        self._widget.updateDarkMean(np.mean(self.dark_field))
        self._widget.updateDarkStd(np.std(self.dark_field))

        self.sigImageReceived.emit('dark_field', self.dark_field)

    def process_flat_field(self):
        """
        Saves the correction, displays mean and STD of all the
        camera pixels.
        """
        self.saveImage(self.flat_field, 'Corrections', 'flat_field')
        self._widget.updateFlatMean(np.mean(self.flat_field))
        self._widget.updateFlatStd(np.std(self.flat_field))

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


class Stability:
    """ Helper container class to monitor and display the stability traces of the 
        intensity of the 4 corners of the OPT stack.

        iUL -> upper left
        iUR -> upper right
        iLL -> lower left
        iLR -> lower right
    """

    def __init__(self, n_pixels=50):
        # TODO: what does n_pixels mean?
        self.n_pixels = n_pixels  # size  in pixels of rectangle  to monitor mean intensity at 4 corners
        # TODO: DP, redo into a dictionary.
        self.steps = []
        self.intensity = [[], [], [], []]

    def clear(self):
        """Clear the lists between experiments. """
        self.steps.clear()
        self.intensity = [[], [], [], []]

    def processStabilityTraces(self, frame: np.ndarray, step: int) -> Tuple[list, List[list]]:
        """ Process the current frame's stability traces.

        Args:
            frame (`np.ndarray`): input frame
            step (`int`): current OPT scan step index

        Returns:
            Tuple[list, List[list]]: list of presently executed OPT scan steps and list of intensity traces
        """
        iUL = np.mean(frame[:self.n_pixels, :self.n_pixels])
        iUR = np.mean(frame[:self.n_pixels, -self.n_pixels:])
        iLL = np.mean(frame[-self.n_pixels:, :self.n_pixels])
        iLR = np.mean(frame[-self.n_pixels:, -self.n_pixels:])

        self.steps.append(step)
        if step == 0:
            # I append ones and save values as normalization factors
            self.norm_factors = (iUL, iUR, iLL, iLR)
            for i in range(4):
                self.intensity[i].append(1.)
        else:
            self.intensity[0].append(iUL/self.norm_factors[0])
            self.intensity[1].append(iUR/self.norm_factors[1])
            self.intensity[2].append(iLL/self.norm_factors[2])
            self.intensity[3].append(iLR/self.norm_factors[3])

        return self.steps, self.intensity


class FBPlive():
    def __init__(self, line, steps: int) -> None:
        self.line = line
        self.n_steps = steps
        if line.ndim > 1:  # 3D reconstruction
            self.sinogram = np.zeros((line.shape[1],
                                      steps))
            self.output_size = line.shape[1]
            self.output = np.zeros((line.shape[1],
                                    line.shape[1],
                                    line.shape[0]))
        else:
            self.sinogram = np.zeros((len(line), steps))
            self.output_size = len(line)
            self.output = np.zeros((len(line), len(line)))
        self.radon_img = self._sinogram_circle_to_square(self.sinogram)
        self.radon_img_shape = self.radon_img.shape[0]
        self.offset = (self.radon_img_shape-self.output_size)//2
        self.projection_size_padded = max(
                64,
                int(2 ** np.ceil(np.log2(2 * self.radon_img_shape))))
        self.radius = self.output_size // 2
        self.xpr, self.ypr = np.mgrid[:self.output_size,
                                      :self.output_size] - self.radius
        self.x = np.arange(self.radon_img_shape) - self.radon_img_shape // 2
        self.theta = np.deg2rad(
                        np.linspace(0., 360., self.n_steps, endpoint=False)
                        )
        self.update_recon(self.line, 0)

    def update_recon(self, line_in, step):
        self.line = line_in
        fourier_filter = self._get_fourier_filter(self.projection_size_padded)
        # padding line
        if self.line.ndim > 1:
            line = np.zeros((self.line.shape[0], self.projection_size_padded))
            line[:, self.offset:line_in.shape[1] + self.offset] = line_in
            # interpolation on the circle
            interpolation = 'linear'
            t = self.ypr * np.cos(self.theta[step]) - self.xpr * np.sin(self.theta[step])
            for i in range(len(self.line[:, 0])):
                # fft filtering of the line
                projection = fft(line[i, :]) * fourier_filter
                radon_filtered = np.real(ifft(projection)[:self.radon_img_shape])

                if interpolation == 'linear':
                    interpolant = interp1d(self.x,
                                           radon_filtered,
                                           kind='linear',
                                           bounds_error=False,
                                           fill_value=0)
                elif interpolation == 'cubic':
                    interpolant = interp1d(self.x,
                                           radon_filtered,
                                           kind='cubic',
                                           bounds_error=False,
                                           fill_value=0)
                else:
                    raise ValueError
                self.output[:, :, i] += interpolant(t) * (np.pi/(2*self.n_steps))
        else:
            line = np.zeros(self.projection_size_padded)
            line[self.offset:len(line_in)+self.offset] = line_in

            # fft filtering of the line
            projection = fft(line) * fourier_filter
            radon_filtered = np.real(ifft(projection)[:self.radon_img_shape])

            # interpolation on the circle
            interpolation = 'linear'
            t = (self.ypr * np.cos(self.theta[step]) -
                 self.xpr * np.sin(self.theta[step]))
            if interpolation == 'linear':
                interpolant = interp1d(self.x, radon_filtered, kind='linear',
                                       bounds_error=False, fill_value=0)
            elif interpolation == 'cubic':
                interpolant = interp1d(self.x, radon_filtered, kind='cubic',
                                       bounds_error=False, fill_value=0)
            else:
                raise ValueError
            self.output += interpolant(t) * (np.pi/(2*self.n_steps))

    def _get_fourier_filter(self, size):
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

    def _sinogram_circle_to_square(self, sinogram):
        diagonal = int(np.ceil(np.sqrt(2) * sinogram.shape[0]))
        pad = diagonal - sinogram.shape[0]
        old_center = sinogram.shape[0] // 2
        new_center = diagonal // 2
        pad_before = new_center - old_center
        pad_width = ((pad_before, pad - pad_before), (0, 0))
        return np.pad(sinogram, pad_width, mode='constant', constant_values=0)


# These functions are adapted from tomopy package
# https://tomopy.readthedocs.io/en/stable/
def _totuple(size, dim):
    """
    Converts size to tuple.
    """
    if not isinstance(size, tuple):
        if dim == 2:
            size = (size, size)
        elif dim == 3:
            size = (size, size, size)
    return size


def shepp3d(size=128, dtype='float32'):
    """
    Load 3D Shepp-Logan image array.

    Parameters
    ----------
    size : int or tuple, optional
        Size of the 3D data.
    dtype : str, optional
        The desired data-type for the array.

    Returns
    -------
    ndarray
        Output 3D test image.
    """
    size = _totuple(size, 3)
    shepp_params = _array_to_params(_get_shepp_array())
    return phantom(size, shepp_params, dtype).clip(0, np.inf)


def phantom(size, params, dtype='float32'):
    """
    Generate a cube of given size using a list of ellipsoid parameters.

    Parameters
    ----------
    size: tuple of int
        Size of the output cube.
    params: list of dict
        List of dictionaries with the parameters defining the ellipsoids
        to include in the cube.
    dtype: str, optional
        Data type of the output ndarray.

    Returns
    -------
    ndarray
        3D object filled with the specified ellipsoids.
    """
    # instantiate ndarray cube
    obj = np.zeros(size, dtype=dtype)

    # define coords
    coords = _define_coords(size)

    # recursively add ellipsoids to cube
    for param in params:
        _ellipsoid(param, out=obj, coords=coords)
    return obj


def _ellipsoid(params, shape=None, out=None, coords=None):
    """
    Generate a cube containing an ellipsoid defined by its parameters.
    If out is given, fills the given cube instead of creating a new one.
    """
    # handle inputs
    if shape is None and out is None:
        raise ValueError("You need to set shape or out")
    if out is None:
        out = np.zeros(shape)
    if shape is None:
        shape = out.shape
    if len(shape) == 1:
        shape = shape, shape, shape
    elif len(shape) == 2:
        shape = shape[0], shape[1], 1
    elif len(shape) > 3:
        raise ValueError("input shape must be lower or equal to 3")
    if coords is None:
        coords = _define_coords(shape)

    # rotate coords
    coords = _transform(coords, params)

    # recast as ndarray
    coords = np.asarray(coords)
    np.square(coords, out=coords)
    ellip_mask = coords.sum(axis=0) <= 1.
    ellip_mask.resize(shape)

    # fill ellipsoid with value
    out[ellip_mask] += params['A']
    return out


def _rotation_matrix(p):
    """
    Defines an Euler rotation matrix from angles phi, theta and psi.
    """
    cphi = np.cos(np.radians(p['phi']))
    sphi = np.sin(np.radians(p['phi']))
    ctheta = np.cos(np.radians(p['theta']))
    stheta = np.sin(np.radians(p['theta']))
    cpsi = np.cos(np.radians(p['psi']))
    spsi = np.sin(np.radians(p['psi']))
    alpha = [[cpsi * cphi - ctheta * sphi * spsi,
              cpsi * sphi + ctheta * cphi * spsi,
              spsi * stheta],
             [-spsi * cphi - ctheta * sphi * cpsi,
              -spsi * sphi + ctheta * cphi * cpsi,
              cpsi * stheta],
             [stheta * sphi,
              -stheta * cphi,
              ctheta]]
    return np.asarray(alpha)


def _define_coords(shape):
    """
    Generate a tuple of coords in 3D with a given shape.
    """
    mgrid = np.lib.index_tricks.nd_grid()
    cshape = np.asarray(1j) * shape
    x, y, z = mgrid[-1:1:cshape[0], -1:1:cshape[1], -1:1:cshape[2]]
    return x, y, z


def _transform(coords, p):
    """
    Apply rotation, translation and rescaling to a 3-tuple of coords.
    """
    alpha = _rotation_matrix(p)
    out_coords = np.tensordot(alpha, coords, axes=1)
    _shape = (3,) + (1,) * (out_coords.ndim - 1)
    _dt = out_coords.dtype
    M0 = np.array([p['x0'], p['y0'], p['z0']], dtype=_dt).reshape(_shape)
    sc = np.array([p['a'], p['b'], p['c']], dtype=_dt).reshape(_shape)
    out_coords -= M0
    out_coords /= sc
    return out_coords


def _get_shepp_array():
    """
    Returns the parameters for generating modified Shepp-Logan phantom.
    """
    shepp_array = [
        [1.,  .6900, .920, .810,   0.,     0.,   0.,   90.,   90.,   90.],
        [-.8, .6624, .874, .780,   0., -.0184,   0.,   90.,   90.,   90.],
        [-.2, .1100, .310, .220,  .22,     0.,   0., -108.,   90.,  100.],
        [-.2, .1600, .410, .280, -.22,     0.,   0.,  108.,   90.,  100.],
        [.1,  .2100, .250, .410,   0.,    .35, -.15,   90.,   90.,   90.],
        [.1,  .0460, .046, .050,   0.,     .1,  .25,   90.,   90.,   90.],
        [.1,  .0460, .046, .050,   0.,    -.1,  .25,   90.,   90.,   90.],
        [.1,  .0460, .023, .050, -.08,  -.605,   0.,   90.,   90.,   90.],
        [.1,  .0230, .023, .020,   0.,  -.606,   0.,   90.,   90.,   90.],
        [.1,  .0230, .046, .020,  .06,  -.605,   0.,   90.,   90.,   90.]]
    return shepp_array


def _array_to_params(array):
    """
    Converts list to a dictionary.
    """
    # mandatory parameters to define an ellipsoid
    params_tuple = [
        'A',
        'a', 'b', 'c',
        'x0', 'y0', 'z0',
        'phi', 'theta', 'psi']

    array = np.asarray(array)
    out = []
    for i in range(array.shape[0]):
        tmp = dict()
        for k, j in zip(params_tuple, list(range(array.shape[1]))):
            tmp[k] = array[i, j]
        out.append(tmp)
    return out

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
