from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtWidgets
from scipy.fftpack import fft, ifft
from scipy.interpolate import interp1d

# import matplotlib.pyplot as plt
from functools import partial
import numpy as np
import pdb
import debugpy
import threading

from imswitch.imcommon.model import dirtools, initLogger
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal


class ScanControllerOpt(ImConWidgetController):
    """ OPT scan controller.
    """
    sigImageReceived = Signal(str, np.ndarray)  # (name, frame array)
    sigRequestSnap = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)

        # Set up rotator in widget
        self._widget.initControls()
        # self.active = True  # LiveupdateController attribute, flag for self.update

        # Local flags
        self.live_recon = False
        self.isOptRunning = False  # currently not used

        # select detectors
        # TODO: it would be useful to create a UI section, a combo box for example,
        # to select the desired detector to extract the data from
        # This is part of the recording widget
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        self._widget.scanPar['Rotator'].currentIndexChanged.connect(self.updateRotator)

        # get rotators
        self.getRotators()
        # populated widget comboBox, this triggers the updateRotator too
        for rotator in self.__rotators:
            self._widget.scanPar['Rotator'].addItem(rotator)

        # Connect widget signals
        self._widget.scanPar['GetHotPixels'].clicked.connect(self.exec_hot_pixels)
        self._widget.scanPar['GetDark'].clicked.connect(self.exec_dark_field)
        self._widget.scanPar['GetFlat'].clicked.connect(self.exec_flat_field)

        # Enable snapping
        self.sigRequestSnap.connect(self._commChannel.sigSnapImg)
        self._commChannel.sigMemorySnapAvailable.connect(self.handleSnap)

        self._commChannel.sigRecordingStarted.connect(self.startOpt)

        # used sigScanEnded, because sigRecordingEnded has been triggering stopOpt 2x
        # I do sigRecordingEnded in stopOpt
        self._commChannel.sigScanEnded.connect(self.stopOpt)

        # TODO: signal for when a new image is captured; either from live view or from recording;
        # DP: sigUpdateImage only from live view, not from recording!!!, not useful
        # this is triggered for every new incoming image from the detector: NO, only liveView
        # self._commChannel.sigUpdateImage.connect(self.displayImage)
        # Connect CommunicationChannel signals
        # self._commChannel.sigUpdateImage.connect(self.update)

        # TODO: there is a signal available for reading back recorded files, sigMemoryRecordingAvailable;
        # details on the content of the signal are listed in the displayRecording method docstring
        # DP: ONLY if i save on RAM or RAM+disk, and only after the whole experiment
        # not useful for me I think
        # self._commChannel.sigMemoryRecordingAvailable.connect(self.displayRecording)
        # pdb.set_trace()

    # DP: this signal is emitted only after sigRcordingEnded and on top only if I am not saving it on disk
    # not useful for me I think, because I am updating stack one by one.
    # def displayRecording(self, name, file, filePath, savedToDisk):
    #     """ Displays the latest performed recording. Method is triggered by the `sigMemoryRecordingAvailable`.

    #     Args:
    #         name (`str`): name of the generated file for the last recording;
    #         file (`Union[BytesIO, h5py.File, zarr.hierarchy.Group]`): 
    #             - if recording is saved to RAM, a reference to a BytesIO instance where the data is saved; 
    #             - otherwise a HDF or Zarr file object of the recorded stack (type is selected from the UI)
    #         filePath (`str`): path to the recording directory
    #         savedToDisk (`bool`): weather recording is saved to disk (`True`) or not (`False`)
    #     """
    #     self._logger.info('Reached displayRecording')
    #     print(name, file, filePath, savedToDisk)
    #     return
    
    # JA: method to add your metadata to recordings
    def setSharedAttr(self, rotatorName, meta1, meta2, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, rotatorName, meta1, meta2, attr)] = value
        finally:
            self.settingAttr = False

    def handleSnap(self, name, image, filePath, savedToDisk):
        """ Handles computation over a snapped image. Method is triggered by the `sigMemorySnapAvailable` signal.

        Args:
            name (`str`): key of the virtual table used to store images in RAM; format is "{filePath}_{channel}"
            image (`np.ndarray`): captured image snap data;
            filepath (`str`): path to the file stored on disk;
            savedToDisk (`bool`): weather the image is saved on disk (`True`) or not (`False`)
        """
        self._logger.debug('handling snap')
        self.frame = image
        if self.isOptRunning:
            self.allFrames.append(image)

            self.optStack = np.array(self.allFrames)
            self.sigImageReceived.emit('OPT stack', self.optStack)

    # DP: redundant, I do this in displayImage
    # def displayStack(self, detectorName, image, init, scale, isCurrentDetector):
    #     """ Displays captured image (via live view or recording) on napari.
    #     Method is triggered via the `sigUpdateImage` signal.

    #     Args:
    #         detectorName (`str`): name of the detector currently capturing
    #         image (`np.ndarray`): captured image
    #         init (`bool`): weather napari should initialize the layer on which data is displayed (True) or not (False)
    #         scale (`List[int]`): the pixel sizes in micrometers; see the `DetectorManager` class for details
    #     """
    #     # TODO: implement layer update functionality;
    #     # the method should only update the layer when a full image is constructed for each slice captured by the detector 
    #     self._logger.info('displayStack function')
    #     self._widget.setImage(np.uint16(self.optStack),
    #                           colormap="gray",
    #                           name=name,
    #                           pixelsize=(1, 1, 1),
    #                           translation=(0, 0, 0))

    def displayImage(self, name, frame):
        # subsample stack
        print('Shape: ', frame.shape)
        self._widget.setImage(np.uint16(frame),
                              colormap="gray",
                              name=name,
                              pixelsize=(1, 1),
                              translation=(0, 0))

    def emitScanSignal(self, signal, *args):
        signal.emit(*args)

    # def enableWidgetInterface(self, enableBool):
    #     self._widget.enableInterface(enableBool)

    def updateRotator(self):
        self.motorIdx = self._widget.getRotatorIdx()
        self.__motor_steps = self._master.rotatorsManager[self.__rotators[self.motorIdx]]._motor._steps_per_turn
        self._widget.scanPar['StepsPerRevLabel'].setText(f'{self.__motor_steps:d} steps/rev')
        self.__logger.debug(
            f'Rotator: {self.__rotators[self.motorIdx]}, {self.__motor_steps} steps/rev',
            )

    def getRotationSteps(self):
        """ Get the total rotation steps. """
        return self._widget.getRotationSteps()

    def getStdCutoff(self):
        """ Get the STD cutoff for Hot pixels correction. """
        return self._widget.getHotStd()

    def getAverages(self):
        """ Get number of averages for camera correction. """
        return self._widget.getAverages()

    def getLiveReconIdx(self):
        return self._widget.getLiveReconIdx()

    def getRotators(self):
        """ Get a list of all rotators."""
        self.__rotators = self._master.rotatorsManager.getAllDeviceNames()

    def updateLiveReconPlot(self, image):
        self._widget.liveReconPlot.setImage(image)

    def startOpt(self):
        """ Reset and initiate Opt scan. """
        self.allFrames = []
        # this is workaround for not showing the individual snaps.
        # I think It cannot be reconnected from this controller, or can it?
        # without reconnecting in stopOpt, snap from the recordingController will
        # snap but not show the image in the viewer.
        try:
            self._commChannel.sigMemorySnapAvailable.disconnect()
        except:
            pass
        self._commChannel.sigSetSnapVisualization.emit(False)
        self._commChannel.sigMemorySnapAvailable.connect(self.handleSnap)
        self.sigImageReceived.connect(self.displayImage)

        # arduino stepper signal after move is finished.
        # TODO: confusing because I have signal move_done, which is used to run post_move on
        # the ArduinoRotatorManager
        # but I cannot connect second slot to it I think. In the end, for normal motor stepping
        # opt_step_done is emitted, but not connected, while in the case of OPT I connect it to the
        # post_step here.
        self._master.rotatorsManager[self.__rotators[self.motorIdx]]._motor.opt_step_done.connect(self.post_step)
        self.__rot_steps = self.getRotationSteps()  # motor step per revolution

        # Checking for divisability of motor steps and OPT steps.
        if self.__motor_steps % self.__rot_steps != 0:
            retval = self.raiseStepMess()
            # hex value associated with Cancel button of QMessageBox
            if int(retval) == int(0x00400000):
                self.stopOpt()
                return

        # equidistant steps for the OPT scan in absolute values.
        self.opt_steps = np.linspace(0, self.__motor_steps, self.__rot_steps,
                                     endpoint=False).astype(np.int_)

        if self._widget.scanPar['LiveReconButton'].isChecked():
            self.live_recon = True
            self.reconIdx = self.getLiveReconIdx()

        # run OPT, set flags and move to step 0
        if not self.isOptRunning:
            self.isOptRunning = True
            self.__currentStep = 0
            self.moveAbsRotator(self.__rotators[self.motorIdx],
                                self.opt_steps[self.__currentStep])

    def stopOpt(self):
        """ Stop OPT acquisition and enable buttons. Method is triggered
        by the sigScanEnded signal.
        """
        self.isOptRunning = False
        print('disconnecting')
        self.emitScanSignal(self._commChannel.sigRecordingEnded)
        self.sigImageReceived.disconnect()
        self._master.rotatorsManager[self.__rotators[self.motorIdx]]._motor.opt_step_done.disconnect()
        self._logger.info("OPT stopped.")
        self._commChannel.sigSetSnapVisualization.emit(True)
        # debugpy.breakpoint()
        # print('debugger stops here')

    def post_step(self, s):
        """Acquire image after motor step is done, stop OPT in case of last step,
        otherwise move motor again.

        Both options using recording and snapping explored, none is without
        issues as commented below.
        """
        print(f'test string: {s}')
        # option using Recording
        # This has an advantage of startAcquisition only once. However it streams images and saving them,
        # No idea how ot prevent that.
        # even the ones I do not care about. Also asking for getLastFrame() for longer acquisition times
        # might mean that part of the exposure might be still while the motor is moving
        # This is not an issue, in snapping
        # Updating OPT stack in napari works
        # self.frame = self.detector.getLatestFrame()
        # if self.frame.shape[0] != 0:
        #     self.allFrames.append(self.frame)

        # option with snapping
        # In this case, no above issues, just right now, If I am writing the snaps to the disk
        # no napari update, because sigMemorySnapAvailable is not emitted in this mode.
        # If I save it to image display, I have updates of the OPT stack and single snaps populated
        # to napari. And they are not saved one by one.
        self.sigRequestSnap.emit()

        # updating live reconstruction
        if self.live_recon:
            self.updateLiveRecon()

        self.__currentStep += 1

        # TODO: stack images, do not generate full array after every step
        # uncomment this if used with Recording
        # self.optStack = np.array(self.allFrames)
        # self.sigImageReceived.emit('OPT stack', self.optStack)

        if self.__currentStep > len(self.opt_steps)-1:
            self.emitScanSignal(self._commChannel.sigScanEnded)
        else:
            self.__logger.debug(f'post_step func, step {self.__currentStep}')
            self.moveAbsRotator(self.__rotators[self.motorIdx], self.opt_steps[self.__currentStep])

    def updateLiveRecon(self):
        try:
            self.current_recon.update_recon(
                self.frame[self.reconIdx, :],
                self.__currentStep)
        except AttributeError:
            try:
                print('Creating a new reconstruction object.')
                self.current_recon = FBPlive(
                    self.frame[self.reconIdx, :],
                    self.__motor_steps)
            except IndexError as e:
                self._logger.warning('Index error, no live-recon')
                print(e)
                self.live_recon = False
                self.current_recon = None

        try:
            self.updateLiveReconPlot(self.current_recon.output)
        except TypeError:
            self._logger.info(f'Wrong image type: {type(self.current_recon.output)}')

    ###################
    # Message windows #
    ###################
    def raiseStepMess(self):
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
        Block camera message before acquisition
        of the dark-field counts, used for identification
        of hot pixels. This is separate operation from dark
        field correction.

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
        if btn.text() == 'Cancel':
            return

        self.sigImageReceived.connect(self.displayImage)
        self.nFrames.connect(
            partial(self._continue, corr_type=corr_type),
            )
        self.getNframes(n)

    def _continue(self, corr_type):
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
        self._widget.updateDarkMean(np.mean(self.dark_field))
        self._widget.updateDarkStd(np.std(self.dark_field))

        self.sigImageReceived.emit('dark_field', self.dark_field)

    def process_flat_field(self):
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
        while i < n:
            frame = self.detector.getLatestFrame()
            if frame.shape[0] != 0:
                frames.append(frame)
                i += 1
        print(np.array(frames).shape)
        self.current_frame = np.mean(np.array(frames), axis=0).astype(np.int16)
        self.nFrames.emit()

    def update_live_recon(self):
        self.live_recon = self._widget.scanPar['LiveReconButton'].isChecked()

    @pyqtSlot()
    def moveAbsRotator(self, name, dist):
        """ Move a specific rotator to a certain position. """
        self.__logger.debug(f'dist to move: {dist}')
        self._master.rotatorsManager[name].move_abs_steps(dist)


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
