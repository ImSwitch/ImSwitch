from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtWidgets
import pyqtgraph as pg
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QMutex
from scipy.fftpack import fft, ifft
from scipy.interpolate import interp1d
import tifffile as tif
import os
from datetime import datetime

from functools import partial
import numpy as np
import time

from imswitch.imcommon.model import initLogger, dirtools
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal
from skimage.transform import radon


class ScanControllerOpt(ImConWidgetController):
    """ OPT scan controller.
    """
    sigImageReceived = Signal(str, np.ndarray)  # (name, frame array)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)

        # Set up rotator in widget
        self._widget.initControls()

        # Local flags
        self.liveRecon = False
        self.saveOpt = True
        self.isOptRunning = False

        # get detectors, select first one, connect update
        # Should it be synchronized with recording selector?
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # connect updator, get rotators, populate combobox
        self._widget.scanPar['Rotator'].currentIndexChanged.connect(
            self.updateRotator)
        self.getRotators()
        for rotator in self.__rotators:
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

        # currently using local acquistion loop
        self._widget.scanPar['StartButton'].clicked.connect(self.initOpt)
        self._widget.scanPar['StopButton'].clicked.connect(self.stopOpt)

    # JA: method to add your metadata to recordings
    # TODO: metadata still not taken care of
    def setSharedAttr(self, rotatorName, meta1, meta2, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[
                (_attrCategory, rotatorName, meta1, meta2, attr)] = value
        finally:
            self.settingAttr = False

    #################
    # Main OPT scan #
    #################
    def initOpt(self):
        """ Initiate Opt scan.  """
        self.allFrames = []
        self.saveSubfolder = datetime.now().strftime("%Y_%m_%d-%H-%M-%S")
        self.sigImageReceived.connect(self.displayImage)

        # arduino stepper signal after move is finished.
        # TODO: confusing because I have signal move_done, which is used to run post_move on
        # the ArduinoRotatorManager
        # but I cannot connect second slot to it I think. In the end, for normal motor stepping
        # opt_step_done is emitted, but not connected, while in the case of OPT I connect it to the
        # post_step here.
        if self._widget.scanPar['MockOpt'].isChecked():
            self.prepareOptMock()
        else:
            self._logger.info('Preparing Real experiment')
            self._master.rotatorsManager[
                self.__rotators[self.motorIdx]]._motor.opt_step_done.connect(
                                                        self.post_step)
        self.__optSteps = self.getOptSteps()

        # Checking for divisability of motor steps and OPT steps.
        if self.__motor_steps % self.__optSteps != 0:
            retval = self.raiseStepMess()
            # hex value associated with Cancel button of QMessageBox
            if int(retval) == int(0x00400000):
                self.stopOpt()
                return

        # equidistant steps for the OPT scan in absolute values.
        self.opt_steps = np.linspace(0, self.__motor_steps, self.__optSteps,
                                     endpoint=False).astype(np.int_)

        # init intensity stability monitoring
        self.signalStability = Stability()

        # live reconstruction
        if self.liveRecon:
            self.reconIdx = self.updateLiveReconIdx()
            self.currentRecon = None  # avoid update_recon in the first step

        self.startOpt()

    def startOpt(self):
        """run OPT, set flags and move to step zero rotator position
        """
        self.detector.startAcquisition()
        self.enableWidget(False)
        if not self.isOptRunning:
            self.isOptRunning = True
            self.__currentStep = 0
            self.moveAbsRotator(self.__rotators[self.motorIdx],
                                self.opt_steps[self.__currentStep])

    def wait(self):
        self._logger.info('inside wait')
        self.mtx.unlock()

    def prepareOptMock(self):
        """
        Generate 3D phantom data and connects motor step
        finish to post_step_mock()
        """
        self._logger.info('Preparing Mock experiment')
        self.mtx = QMutex()
        self._master.rotatorsManager[
            self.__rotators[self.motorIdx]]._motor.opt_step_done.connect(
                                                    self.post_step_mock)

        # here generate stack of projections
        self.demo = DemoData(resolution=32, bin_factor=1)
        self.demo.sinoReady.connect(self.wait)
        # self.mtx.lock()
        time.sleep(2)
        self._widget.scanPar['OptStepsEdit'].setText('32')
        self._logger.info('waiting...')

    @pyqtSlot()
    def moveAbsRotator(self, name, dist):
        """ Move a specific rotator to an absolute position. """
        self._master.rotatorsManager[name].move_abs_steps(dist)

    def post_step(self, s):
        """Acquire image after motor step is done, move to next step """
        self.handleSnap()
        self.nextStep()

    def post_step_mock(self, s):
        """Get image from the demo sinogram data, call next step. """
        self.frame = self.demo.sinogram[self.__currentStep]
        self.optStack = self.demo.sinogram[:self.__currentStep]
        self.sigImageReceived.emit('OPT stack', self.optStack)
        self.nextStep()

    def nextStep(self):
        """
        Update live reconstruction, stop OPT in case of last step,
        otherwise move motor again.
        """
        # updating live reconstruction
        if self.liveRecon:
            self.updateLiveRecon()

        self.__currentStep += 1

        if self.__currentStep > len(self.opt_steps)-1:
            self.stopOpt()
        else:
            self.moveAbsRotator(self.__rotators[self.motorIdx],
                                self.opt_steps[self.__currentStep])

    def stopOpt(self):
        """
        Stop OPT acquisition and enable buttons.
        Update local flags and and disconnect signals.
        """
        self.detector.stopAcquisition()
        self.isOptRunning = False
        self.enableWidget(True)
        self.sigImageReceived.disconnect()
        self._master.rotatorsManager[
            self.__rotators[self.motorIdx]]._motor.opt_step_done.disconnect()
        self._logger.info("OPT stopped.")

    ##################
    # Image handling #
    ##################
    def handleSnap(self):
        """
        Get and process getLatestFrame() call. Concatenate
        to the OPT stack, save projection, update the stability plot.
        """
        self.frame = self.detector.getLatestFrame()
        if self.isOptRunning:
            self.allFrames.append(self.frame)

            self.optStack = np.array(self.allFrames)
            self.sigImageReceived.emit('OPT stack', self.optStack)

            if self.saveOpt:
                self.saveImage(self.frame,
                               self.saveSubfolder,
                               f'{self.__currentStep:04}')

            # update intensity monitoring plot, This should be there for the
            # mock too no? Needs refactoring
            self.signalStability.process_img(self.frame, self.__currentStep)
            self.updateStabilityPlot()

            self._widget.updateCurrentStep(self.__currentStep + 1)

    def displayImage(self, name, frame):
        """
        Display stack or image in the napari viewer.

        Args:
            name (str): napari layer name
            frame (np.ndarray): image or stack
        """
        # subsample stack
        if self.isOptRunning:
            self._widget.setImage(np.uint16(frame),
                                  colormap="gray",
                                  name=name,
                                  pixelsize=(1, 1),
                                  translation=(0, 0),
                                  step=self.__currentStep)
        else:
            self._widget.setImage(np.uint16(frame),
                                  colormap="gray",
                                  name=name,
                                  pixelsize=(1, 1),
                                  translation=(0, 0),
                                  )

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
                print(f'Creating a new reconstruction object. {self.__optSteps}')
                self.currentRecon = FBPlive(
                    self.frame[self.reconIdx, :],
                    self.__optSteps)
                self.__logger.info(f'Recon shape: {self.currentRecon.output.shape}')
            except IndexError:
                self._logger.warning('Index error, reconstruction will proceed on the central camera line')
                self.setLiveReconIdx(self.frame.shape[0]//2)
                self.currentRecon = FBPlive(
                    self.frame[self.reconIdx, :],
                    self.__optSteps)
        try:
            self.updateLiveReconPlot(self.currentRecon.output)
        except TypeError:
            self._logger.info(f'Wrong type: {type(self.currentRecon.output)}')

    def updateLiveReconPlot(self, image):
        """
        Dispaly current live reconstruction image.

        Args:
            image (np.ndarray): FBP live reconstruction
        """
        self._widget.liveReconPlot.clear()
        self._widget.liveReconPlot.setImage(image)
        self._widget.updateCurrentReconStep(self.__currentStep+1)

    ##################
    # Helper methods #
    ##################
    def enableWidget(self, value: bool) -> None:
        """
        Upon starting/stopping the OPT, widget
        editable fields get enabled from the bool value.

        Args:
            value (bool): enable value, False means disable
        """
        self._widget.scanPar['StartButton'].setEnabled(value)
        self._widget.scanPar['StopButton'].setEnabled(not value)
        self._widget.scanPar['SaveButton'].setEnabled(value)
        self._widget.scanPar['LiveReconIdxEdit'].setEnabled(value)
        self._widget.scanPar['OptStepsEdit'].setEnabled(value)
        self._widget.scanPar['GetDark'].setEnabled(value)
        self._widget.scanPar['GetFlat'].setEnabled(value)
        self._widget.scanPar['GetHotPixels'].setEnabled(value)
        self._widget.scanPar['AveragesEdit'].setEnabled(value)
        self._widget.scanPar['MockOpt'].setEnabled(value)

    def updateRotator(self):
        """
        Update rotator attributes when rotator is changed.
        setting an index of the motor, motor_steps describe
        number of steps per revolution (resolution of the motor),
        also displayed in the widget.
        """
        self.motorIdx = self._widget.getRotatorIdx()
        self.__motor_steps = self._master.rotatorsManager[
            self.__rotators[self.motorIdx]]._motor._steps_per_turn

        self._widget.scanPar['StepsPerRevLabel'].setText(
            f'{self.__motor_steps:d} steps/rev')

        self.__logger.debug(
            f'Rotator: {self.__rotators[self.motorIdx]}, {self.__motor_steps} steps/rev',
            )

    def getOptSteps(self):
        """ Get the total rotation steps for an OPT experiment. """
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
        """
        Set whether live reconstruction happenning.

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

    def updateStabilityPlot(self):
        """ Update OPT stability plot from 4 corners of the stack """
        self._widget.intensityPlot.clear()
        self._widget.intensityPlot.addLegend()

        colors = ['w', 'r', 'g', 'b']
        labels = ['UL', 'UR', 'LL', 'LR']
        for i in range(4):
            self._widget.intensityPlot.plot(
                self.signalStability.steps,
                self.signalStability.intensity[i],
                name=labels[i],
                pen=pg.mkPen(colors[i], width=1.5),
            )

    def updateLiveReconIdx(self):
        """ Get camera line index for the live reconstruction.

        Returns:
            int: Index of the image array
        """
        return self._widget.getLiveReconIdx()

    def setLiveReconIdx(self, value: int):
        """ Set camera line index for the live reconstruction

        Args:
            value (int): camera line index
        """
        self._widget.setLiveReconIdx(value)

    def getRotators(self):
        """ Get a list of all rotators."""
        self.__rotators = self._master.rotatorsManager.getAllDeviceNames()

    ###################
    # Message windows #
    ###################
    def raiseStepMess(self):
        """
        Warn user when selected number of OPT steps do divide the
        motor steps and will not be exactly equidistant.

        Returns:
            hex: hexadecimal value of the button pressed.
        """
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText("Motor steps not integer values.")
        text = "Steps per/rev should be divisable by number of OPT steps. \
            You can continue by casting the steps on integers and risk \
            imprecise measured angles. Or cancel scan."
        msg.setInformativeText(" ".join(text.split()))
        msg.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        btn_cancel = msg.button(QtWidgets.QMessageBox.Cancel)
        btn_cancel.setText('Cnacel scan')
        btn_measure = msg.button(QtWidgets.QMessageBox.Ok)
        btn_measure.setText('Cast on int and measure')
        retval = msg.exec_()
        return retval

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
        """
        Handles correction acquisition, connects
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
        """Triggered by recieving a signal nFrames that
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
        Automatic saving of the correction to the \Corrections folder.
        Based on the selected STD cutoff in the widget identifies pixels which
        have intensity higher than mean of all pixels + STD cutoff multiples of STD.
        Calculates and displays count of hot pixels and average intensity of both
        hot and non-hot pixels.
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

    def saveImage(self, frame, subfolder, filename="corr", fileExtension="tiff"):
        """
        Constructs saving path and saves the image. Method adapted from
        UC2/STORMreconController from https://github.com/openUC2 fork of
        imswitch.

        Args:
            frame (np.ndarray): image array
            subfolder (str): datetime string for unique folder identification
            filename (str, optional): part of the filename can be specified. Defaults to "corr".
            fileExtension (str, optional): Image format. Defaults to "tiff".
        """
        filePath = self.getSaveFilePath(
                            subfolder=subfolder,
                            filename=filename,
                            extension=fileExtension)

        self._logger.debug(filePath)
        tif.imwrite(filePath, frame, append=False)

    def getSaveFilePath(self, subfolder: str, filename: str, extension: str)-> os.path:
        """Sets datetime part of the filename, combines parts of the
        filename, ensures existance of the saving folder and returns
        the full savings path

        Args:
            subfolder (str): subfolder name
            filename (str): specific filename string part
            extension (str): image format extension

        Returns:
            os.path: save path
        """
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


class Stability():
    def __init__(self, n_pixels=50):
        self.n_pixels = n_pixels
        self.steps = []
        self.intensity = [[], [], [], []]

    def process_img(self, img, step):
        iUL = np.mean(img[:self.n_pixels, :self.n_pixels])
        iUR = np.mean(img[:self.n_pixels, -self.n_pixels:])
        iLL = np.mean(img[-self.n_pixels:, :self.n_pixels])
        iLR = np.mean(img[-self.n_pixels:, -self.n_pixels:])

        self.updateSeries(step, iUL, iUR, iLL, iLR)

    def updateSeries(self, step, iUL, iUR, iLL, iLR):
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
                    interpolant = interp1d(self.x, radon_filtered, kind='linear',
                                           bounds_error=False, fill_value=0)
                elif interpolation == 'cubic':
                    interpolant = interp1d(self.x, radon_filtered, kind='cubic',
                                           bounds_error=False, fill_value=0)
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
            t = self.ypr * np.cos(self.theta[step]) - self.xpr * np.sin(self.theta[step])
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
        '''size needs to be even
        Only ramp filter implemented
        '''
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


class DemoData(QObject):

    sinoReady = pyqtSignal()

    def __init__(self, resolution=128, bin_factor=1) -> None:
        super(QObject, self).__init__()
        self.size = resolution  # int
        self.idx = 0
        self.binning_factor = bin_factor  # not sure it can do hardware binning
        self.accum = False
        self.thread = QThread(parent=self)
        self.radon = Get_radon(self.size)
        self.radon.moveToThread(self.thread)
        self.thread.started.connect(self.radon.get_sinogram)
        # self.radon.get_sinogram()
        self.radon.finished.connect(self.sino)
        self.radon.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.quit)
        self.thread.start()

    def sino(self, data):
        """Setting sinogram variable of phantom
        data

        Args:
            data (np.ndarray):  Sinogram of 3D phantom
        """
        print('setting sino variable')
        self.sinogram = np.rollaxis(data, 2)
        self.sinoReady.emit()


class Get_radon(QObject):
    def __init__(self, size):
        super(QObject, self).__init__()
        self.size = size

    finished = pyqtSignal(np.ndarray)
    progress = pyqtSignal(int)

    def get_sinogram(self):
        data = shepp3d(self.size)  # shepp-logan 3D phantom
        sinogram = np.zeros(data.shape)  # preallocate sinogram array
        angles = np.linspace(0, 360, self.size, endpoint=False)  # angles
        # TODO make progress bar with loading data
        for i in range(self.size):
            self.progress.emit(int(i*100 / self.size))
            sinogram[i, :, :] = radon(data[i, :, :], theta=angles)
        mx = np.amax(sinogram)
        sinogram = (sinogram/mx*255).astype('int16')
        print('emitting', sinogram.shape)
        self.finished.emit(sinogram)

    def loading_message(self):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("Generating data for you")
        # msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        retval = msg.exec_()
        print(retval)
        return retval


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
