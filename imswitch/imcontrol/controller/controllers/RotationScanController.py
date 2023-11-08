import json
import os

import matplotlib.pyplot as plt
import numpy as np
import scipy.interpolate as interp

from imswitch.imcommon.model import dirtools, initLogger
from ..basecontrollers import ImConWidgetController


class RotationScanController(ImConWidgetController):
    """ Linked to RotationScanWidget. Requires the ability of the rotators to together create
    linear polarization states of different directions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)

        # Set up rotator in widget
        self._widget.initControls()

        # Connect widget signals
        self._widget.sigActivate.connect(lambda enableInterfaceBool: self.toggleExperiment(enableInterfaceBool))
        self._widget.sigCalibration.connect(lambda: self.calibrateRotationsInitiate())
        self._widget.pars['LoadCalibrationButton'].clicked.connect(lambda: self.loadCalibration())
        self._widget.pars['SaveCalibrationButton'].clicked.connect(lambda: self.saveCalibration())

        # Create signal function trigger handles
        self.__toggleExperimentHandle = lambda: self.toggleExperiment(True)
        self.__prepRotationHandle = lambda: self.prepRotationStep()

        # Initiate parameters used during the experiment
        self.__currentStep = 0

        # Initiate parameters used during calibration
        self.__calibrationPolSteps = np.arange(0,181,15).tolist()
        self.__calibration_filename = 'polarization_calibration.json'
        self.__calibration_dir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_rotscan')
        if not os.path.exists(self.__calibration_dir):
            os.makedirs(self.__calibration_dir)

    def closeEvent(self):
        pass

    def toggleExperiment(self, enableInterfaceBool):
        self.enableWidgetInterface(enableInterfaceBool)
        if not enableInterfaceBool:
            # initiate experiment
            self.initiateExperiment()
        else:
            # finalize experiment, disconnect signals
            self._commChannel.sigScanDone.disconnect(self.__toggleExperimentHandle)
            self._commChannel.sigNewFrame.disconnect(self.__prepRotationHandle)

    def enableWidgetInterface(self, enableBool):
        self._widget.enableInterface(enableBool)
        if enableBool:
            text = 'Activate during scan'
        elif not enableBool:
            text = 'Inactivate'
        self._widget.setActivateButtonText(text)

    def initiateExperiment(self):
        """ Initiate experiment to be run when scanning steps are taken. """
        self.__pol_rot_params = self.getPolRotationParams()
        pol_steps = np.arange(*self.__pol_rot_params)
        self.__rot_step_pos = self.getRotationStepPositions(pol_steps)
        self.__logger.debug(self.__rot_step_pos)
        self.getRotators()
        self.__currentStep = 0
        self.prepRotationStep()
        #TODO: After a step has been taken, prep the controller with the next step by calling self.prepRotationStep() like in the initiation here. For this to work, I need to know when a step has been taken, how do I find out???
        # Can I continuously check the position of the rotators in a separate thread and give a signal whenever they were updated? Use sync output of rotator controller - it is activated, but how do I read it, with a NiDAQ DI reading task?
        # For now, do this with a frame-finished signal from the APDManager, but this is very non general
        self._commChannel.sigScanDone.connect(self.__toggleExperimentHandle)
        self._commChannel.sigNewFrame.connect(self.__prepRotationHandle)  # TODO: this will only work for one APDdetector, and nothing else - if no APD it will never trigger, if multiple APD it will trigger multiple times

    def getPolRotationParams(self):
        """ Get the total polarization rotation (start, stop, step). """
        return (self._widget.getRotationStart(), self._widget.getRotationStop(), self._widget.getRotationStep())

    def getRotationStepPositions(self, pol_steps):
        """ Get the interpolated rotator step positions for each rotator in the experiment, as a list of lists. """
        rotator_step_pos = []
        for spline in self.__interp_splines:
            rotator_step_pos.append(interp.splev(pol_steps, spline))
        return rotator_step_pos

    def getRotators(self):
        """ Get a list of all rotators part of the polarization rotation experiment. """
        self.__rotators = self._master.rotatorsManager.getAllDeviceNames()

    def prepRotationStep(self):
        """ Called when a polarization rotation step needs to be prepped, i.e. just after one step has been taken. """
        for idx, rotator in enumerate(self.__rotators):
            self.__logger.debug([self.__currentStep, rotator, self.__rot_step_pos[idx][self.__currentStep]])
            self.moveAbsRotator(rotator, self.__rot_step_pos[idx][self.__currentStep])
            #self._commChannel.sigSetSyncInMovementSettings.emit(rotator, self.__rot_step_pos[idx][self.__currentStep+1])
            self._commChannel.sigUpdateRotatorPosition.emit(rotator)
        if self.__currentStep > len(self.__rot_step_pos[0]) - 2:
            self.__currentStep = 0
        else:
            self.__currentStep += 1

    def calibrateRotationsInitiate(self):
        """ Reset and initiate calibration of polarizer rotations. """
        self.__rotCalPos = []
        self.calibrationStep(step=0)

    def calibrateRotationsFinish(self):
        """ Finish calibration by interpolating/fitting the stored positions across the range of polarization rotations. """
        self.__interp_splines = []
        self.__rotCalPos = np.swapaxes(self.__rotCalPos,0,1).tolist()
        for rotator, positions in enumerate(self.__rotCalPos):
            # get spline interpolation of calibrated positions
            self.__interp_splines.append(interp.splrep(self.__calibrationPolSteps, positions))
            # evaluate and plot spline interpolations
            pol_eval = np.arange(0, self.__calibrationPolSteps[-1], 1)
            pos_eval = interp.splev(pol_eval, self.__interp_splines[rotator])
            plt.figure(rotator)
            plt.scatter(self.__calibrationPolSteps, positions)
            plt.plot(pol_eval, pos_eval)
            plt.show()

    def saveCalibration(self):
        """ Save calibration data to be able to load and interpolate the same spline interpolation in another instance. """
        save_dict = {}
        save_dict['pol_steps'] = self.__calibrationPolSteps
        for rotator, positions in enumerate(self.__rotCalPos):
            save_dict[f'pos{rotator}'] = positions

        with open(os.path.join(self.__calibration_dir, self.__calibration_filename), 'w') as f:
            json.dump(save_dict, f, indent=4)

    def loadCalibration(self):
        """ Load calibration data, to be used to interpolate the same spline interpolation in a new instance. """
        rotator_positions = []
        with open(os.path.join(self.__calibration_dir, self.__calibration_filename), 'r') as f:
            data = json.load(f)
        for idx, item in enumerate(data.items()):
            if idx == 0:
                polarization_steps = item[1]
            else:
                rotator_positions.append(item[1])
        self.__calibrationPolSteps = polarization_steps
        self.__rotCalPos = rotator_positions
        self.__logger.debug(self.__calibrationPolSteps)
        self.__logger.debug(self.__rotCalPos)

    def calibrationStep(self, step):
        """ Takes a step of the calibration routine, saving set rotations and preparing for the next step. """
        # save rotations just set to calibrations
        if step > 0:
            rot_pos_step = self._master.rotatorsManager.execOnAll(lambda rot: rot.position())
            self.__rotCalPos.append([pos for _,pos in rot_pos_step.items()])

        # set up prompt for next calibration step
        if step == len(self.__calibrationPolSteps):
            self.setCalibrationPrompt('Calibration routine finished.')
            self.calibrateRotationsFinish()
        else:
            if np.mod(self.__calibrationPolSteps[step], 90) == 0:
                if np.floor_divide(self.__calibrationPolSteps[step], 90) == 1:
                    prompt_add = 'vertical.'
                else:
                    prompt_add = 'horizontal.'
            else:
                prompt_add = f'rotated {self.__calibrationPolSteps[step]} deg.'
            prompt = 'Set polarization to linear, ' + prompt_add
            if step == 0:
                prompt = 'Calibration routine initiated. ' + prompt
            self.setCalibrationPrompt(prompt)

        # set up calibration button for next calibration step
        self._widget.sigCalibration.disconnect()
        if step < len(self.__calibrationPolSteps):
            self._widget.sigCalibration.connect(lambda: self.calibrationStep(step+1))
            self._widget.setCalibrationButtonText('Save, next position')
        else:
            self._widget.sigCalibration.connect(lambda: self.calibrateRotationsInitiate())
            self._widget.setCalibrationButtonText('Calibrate polarization')

    def moveAbsRotator(self, name, pos):
        """ Move a specific rotator to a certain position. """
        self._master.rotatorsManager[name].move_abs(pos)

    def setCalibrationPrompt(self, text):
        """ Set calibration prompt text in the widget, during calibration. """
        self._widget.setCalibrationPrompt(text)


# Copyright (C) 2020-2023 ImSwitch developers
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
