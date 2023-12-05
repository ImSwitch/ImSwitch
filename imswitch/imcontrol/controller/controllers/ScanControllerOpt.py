import os
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

# import matplotlib.pyplot as plt
import numpy as np
import pdb

from imswitch.imcommon.model import dirtools, initLogger
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal


class ScanControllerOpt(ImConWidgetController):
    """ OPT scan controller.
    """
    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)
        self.optStack = np.ones((1, 1, 1))

        # Set up rotator in widget
        self._widget.initControls()
        self.live_recon = False
        self.save_opt = False
        self.isOptRunning = False

        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # get rotators
        self.getRotators()
        self.__motor_steps = self._master.rotatorsManager[self.__rotators[0]]._motor._steps_per_turn
        self.__logger.debug(f'Your rotators {self.__rotators} with {self.__motor_steps} steps per revolution.')

        # Connect widget signals
        self._widget.scanPar['StartButton'].clicked.connect(self.startOpt)
        self.sigImageReceived.connect(self.displayImage)

        # Initiate parameters used during the experiment
        self.__opt_meta_filename = 'opt_metadata.json'
        self.__opt_dir = os.path.join(dirtools.UserFileDirs.Root,
                                      'imcontrol_optscan')
        if not os.path.exists(self.__opt_dir):
            os.makedirs(self.__opt_dir)

        # pdb.set_trace()

    def displayImage(self):
        # a bit weird, but we cannot update outside the main thread
        name = "OPT Stack"
        # subsample stack
        self._widget.setImage(np.uint16(self.optStack),
                              colormap="gray",
                              name=name,
                              pixelsize=(20, 1, 1),
                              translation=(0, 0, 0))

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

    def getRotators(self):
        """ Get a list of all rotators."""
        self.__rotators = self._master.rotatorsManager.getAllDeviceNames()

    def startOpt(self):
        """ Reset and initiate Opt scan. """
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

    def stopOpt(self):
        """Stop OPT acquisition and enable buttons
        """
        self.isOptRunning = False
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
        if self.__currentStep > len(self.opt_steps)-1:
            self.optStack = np.array(self.allFrames)
            self.sigImageReceived.emit()
            self.__logger.info(f'collected {len(self.optStack)} images')
            self.stopOpt()
        else:
            self.__logger.debug(f'post_step func, step{self.__currentStep}')
            self.moveAbsRotator(self.__rotators[0], self.opt_steps[self.__currentStep])


    #################
    ### old codes ###
    #################

    # def saveOptMeta(self):
    #     """ Save OPT metadata"""
    #     save_dict = {}
    #     save_dict['opt_steps'] = self.opt_steps
    #     for rotator, positions in enumerate(self.__rotPos):
    #         save_dict[f'pos{rotator}'] = positions

    #     with open(os.path.join(self.__opt_dir, self.__opt_meta_filename), 'w') as f:
    #         json.dump(save_dict, f, indent=4)

    def emitScanSignal(self, signal, *args):
        signal.emit(*args)

    def update_live_recon(self):
        self.live_recon = self._widget.scanPar['LiveReconButton'].isChecked()

    def update_save_opt(self):
        self.save_opt = self._widget.scanPar['SaveOptButton'].isChecked()

    def moveRelRotator(self, name, dist):
        """ Move a specific rotator to a certain position. """
        self._master.rotatorsManager[name].move_rel(dist)

    @pyqtSlot()
    def moveAbsRotator(self, name, dist):
        """ Move a specific rotator to a certain position. """
        self.__logger.debug(f'Scancontroller, dist to move: {dist}')
        self._master.rotatorsManager[name].move_abs_steps(dist)
        self.__logger.debug('Scancontroller, after move.')


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
