import os
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtWidgets

# import matplotlib.pyplot as plt
from functools import partial
import numpy as np
import pdb

from imswitch.imcommon.model import dirtools, initLogger
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal


class ScanControllerOpt(ImConWidgetController):
    """ OPT scan controller.
    """
    sigImageReceived = Signal(str)
    sigRequestSnap = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)
        self.optStack = np.ones((1, 1, 1))
        # self.hotPixels = np.ones((1, 1))

        # Set up rotator in widget
        self._widget.initControls()
        self.live_recon = False
        self.save_opt = False
        self.isOptRunning = False

        # select detectors
        # TODO: it would be useful to create a UI section, a combo box for example,
        # to select the desired detector to extract the data from
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # get rotators
        # TODO: as for detectors, it would be useful to create a UI combo box to select the desired rotator
        self.getRotators()
        self.__motor_steps = self._master.rotatorsManager[self.__rotators[0]]._motor._steps_per_turn
        self.__logger.debug(f'Your rotators {self.__rotators} with {self.__motor_steps} steps per revolution.')

        # Connect widget signals
        self._widget.scanPar['StartButton'].clicked.connect(self.startOpt) # TODO: if using the communication channel signal, the start button is redundant
        self._widget.scanPar['GetHotPixels'].clicked.connect(self.exec_hot_pixels)
        self._widget.scanPar['GetDark'].clicked.connect(self.exec_dark_field)
        self._widget.scanPar['GetFlat'].clicked.connect(self.exec_flat_field)

        # Initiate parameters used during the experiment
        self.__opt_meta_filename = 'opt_metadata.json'
        self.__opt_dir = os.path.join(dirtools.UserFileDirs.Root,
                                      'imcontrol_optscan')
        if not os.path.exists(self.__opt_dir):
            os.makedirs(self.__opt_dir)

        
        self.sigRequestSnap.connect(self._commChannel.sigSnapImg)


        # TODO: signals to control behavior based on the starting/stopping of liveview/recording
        # FOR LIVEVIEW: use sigLiveStarted / sigLiveStopped (live acquisition started/stopped)
        # FOR RECORDING: use sigRecordingStarted / sigRecordingStopped (recording started/stopped);
        # it's also possible to use the same methods connected to different signal by adding a lambda function with pre-determined flags
        self._commChannel.sigLiveStarted.connect(lambda: self.startOpt(live=True))
        self._commChannel.sigLiveStopped.connect(lambda: self.stopOpt(live=True))
        self._commChannel.sigRecordingStarted.connect(lambda: self.startOpt(live=False))
        self._commChannel.sigRecordingStarted.connect(lambda: self.stopOpt(live=False))

        # TODO: signal for when a new image is captured; either from live view or from recording;
        # this is triggered for every new incoming image from the detector
        self._commChannel.sigUpdateImage.connect(self.displayStack)

        # TODO: there is a signal available for reading back recorded files, sigMemoryRecordingAvailable;
        # details on the content of the signal are listed in the displayRecording method docstring
        self._commChannel.sigMemoryRecordingAvailable.connect(self.displayRecording)

        # TODO: connect the following signals to local methods to eventually update other scanning parameters;
        # this can only work for a recording and not a live view acquisition
        # self._commChannel.sigUpdateRecFrameNum   (`int`, number of frames captured during an acquisition)
        # self._commChannel.sigUpdateRecTime       (`int`, recording time in seconds)

        # pdb.set_trace()

    def displayRecording(self, name, file, filePath, savedToDisk):
        """ Displays the latest performed recording. Method is triggered by the `sigMemoryRecordingAvailable`.

        Args:
            name (`str`): name of the generated file for the last recording;
            file (`Union[BytesIO, h5py.File, zarr.hierarchy.Group]`): 
                - if recording is saved to RAM, a reference to a BytesIO instance where the data is saved; 
                - otherwise a HDF or Zarr file object of the recorded stack (type is selected from the UI)
            filePath (`str`): path to the recording directory
            savedToDisk (`bool`): weather recording is saved to disk (`True`) or not (`False`)
        """
        # TODO: implement
        pass
    
    def handleSnap(self, name, image, filePath, savedToDisk):
        """ Handles computation over a snapped image. Method is triggered by the `sigMemorySnapAvailable` signal.

        Args:
            name (`str`): key of the virtual table used to store images in RAM; format is "{filePath}_{channel}"
            image (`np.ndarray`): captured image snap data;
            filepath (`str`): path to the file stored on disk;
            savedToDisk (`bool`): weather the image is saved on disk (`True`) or not (`False`)
        """

        snapData = image[self.detector]
        # TODO: snapData contains the image currently snapped on the specific detector;
        # implement how to handle it


    def displayStack(self, detectorName, image, init, scale, isCurrentDetector):
        """ Displays captured image (via live view or recording) on napari.
        Method is triggered via the `sigUpdateImage` signal.

        Args:
            detectorName (`str`): name of the detector currently capturing
            image (`np.ndarray`): captured image
            init (`bool`): weather napari should initialize the layer on which data is displayed (True) or not (False)
            scale (`List[int]`): the pixel sizes in micrometers; see the `DetectorManager` class for details
        """
        # TODO: implement layer update functionality;
        # the method should only update the layer when a full image is constructed for each slice captured by the detector 
        self._logger.info('displayStack function')
        self._widget.setImage(np.uint16(self.optStack),
                              colormap="gray",
                              name=name,
                              pixelsize=(1, 1, 1),
                              translation=(0, 0, 0))

    def displayImage(self, name):
        # subsample stack
        print('Shape: ', self.current_frame.shape)
        self._widget.setImage(np.uint16(self.current_frame),
                              colormap="gray",
                              name=name,
                              pixelsize=(1, 1),
                              translation=(0, 0))
        self.sigImageReceived.disconnect()

    def emitScanSignal(self, signal, *args):
        signal.emit(*args)

    def saveScanParamsToFile(self, filePath: str) -> None:
        """ Saves the set scanning parameters to the specified file. """
        self.getParameters()

    def loadScanParamsFromFile(self, filePath: str) -> None:
        """ Loads scanning parameters from the specified file. """
        self.setParameters()

    def enableWidgetInterface(self, enableBool):
        self._widget.enableInterface(enableBool)

    def getRotationSteps(self):
        """ Get the total rotation steps. """
        return self._widget.getRotationSteps()

    def getStdCutoff(self):
        """ Get the STD cutoff for Hot pixels correction. """
        return self._widget.getHotStd()
    
    def getAverages(self):
        """ Get number of averages for camera correction. """
        return self._widget.getAverages()

    def getRotators(self):
        """ Get a list of all rotators."""
        self.__rotators = self._master.rotatorsManager.getAllDeviceNames()

    def startOpt(self, live: bool):
        """ Sets up the OPT for scanning operation. Method is triggered by the sigAcquisitionStarted signal. """

        self._widget.scanPar['StartButton'].setEnabled(False)
        self._widget.scanPar['StopButton'].setEnabled(True)
        self._widget.scanPar['StartButton'].setText('Running')
        self._widget.scanPar['StopButton'].setText('Stop')
        self._widget.scanPar['StopButton'].setStyleSheet("background-color: red")
        self._widget.scanPar['StartButton'].setStyleSheet("background-color: green")

        self.__rot_steps = self.getRotationSteps()  # motor step per revolution

        # equidistant steps for the OPT scan in absolute values.
        self.opt_steps = np.linspace(0, self.__motor_steps, self.__rot_steps,
                                     endpoint=False)
        self.__logger.debug(f'OPT steps: {self.opt_steps}')
        self.allFrames = []
        # run OPT
        self.scanRecordOpt()

    def stopOpt(self, live: bool):
        """ Stop OPT acquisition and enable buttons. Method is triggered by the sigAcquisitionStopped signal.
        """
        self.isOptRunning = False
        self.sigImageReceived.disconnect()
        self._master.rotatorsManager[self.__rotators[0]]._motor.opt_step_done.disconnect()
        self._widget.scanPar['StartButton'].setEnabled(True)
        self._widget.scanPar['StopButton'].setEnabled(False)
        self._widget.scanPar['StartButton'].setText("Start")
        self._widget.scanPar['StopButton'].setText("Stopped")
        self._widget.scanPar['StopButton'].setStyleSheet("background-color: green")
        self._widget.scanPar['StartButton'].setStyleSheet("background-color: red")
        self._logger.info("OPT stopped.")

    def scanRecordOpt(self):
        """Initiaate OPT with step 0 and setting flags.
        """
        if not self.isOptRunning:
            self.isOptRunning = True
            self.__currentStep = 0

            self._master.rotatorsManager[self.__rotators[0]]._motor.opt_step_done.connect(self.post_step)
            self.moveAbsRotator(self.__rotators[0], self.opt_steps[self.__currentStep])

    def post_step(self):
        """Acquire image after motor step is done, stop OPT in case of last step,
        otherwise move motor again.
        """
        frame = self.detector.getLatestFrame()
        if frame.shape[0] != 0:
            self.allFrames.append(frame)

        self.__currentStep += 1
        # TODO: fix display after every step
        # self.sigImageReceived.emit('OPT stack')
        if self.__currentStep > len(self.opt_steps)-1:
            self.optStack = np.array(self.allFrames)
            self.sigImageReceived.emit('OPT stack')
            self.__logger.info(f'collected {len(self.optStack)} images')
            self.stopOpt()
        else:
            self.optStack = np.array(self.allFrames)
            self.displayStack('OPT stack')
            self.__logger.debug(f'post_step func, step {self.__currentStep}')
            self.moveAbsRotator(self.__rotators[0], self.opt_steps[self.__currentStep])

    def exec_hot_pixels(self):
        """
        Block camera message before acquisition
        of the dark-field counts, used for identification
        of hot pixels. This is separate operation from dark
        field correction.

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
        
        # saving
        # file_name = corr_type + self.get_time_now()
        # self.save_image(file_name)
        # self.append_history(corr_type + ' correction saved.')

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

        self.sigImageReceived.emit('hot_pixels')

    def process_dark_field(self):
        self._widget.updateDarkMean(np.mean(self.dark_field))
        self._widget.updateDarkStd(np.std(self.dark_field))

        self.sigImageReceived.emit('dark_field')

    def process_flat_field(self):
        self._widget.updateFlatMean(np.mean(self.flat_field))
        self._widget.updateFlatStd(np.std(self.flat_field))

        self.sigImageReceived.emit('flat_field')

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

    def update_save_opt(self):
        self.save_opt = self._widget.scanPar['SaveOptButton'].isChecked()

    @pyqtSlot()
    def moveAbsRotator(self, name, dist):
        """ Move a specific rotator to a certain position. """
        self.__logger.debug(f'Scancontroller, dist to move: {dist}')
        self._master.rotatorsManager[name].move_abs_steps(dist)
        self.__logger.debug('Scancontroller, after move.')


class LiveRecon():
    # copy from optac
    def __init__(self):
        return
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
