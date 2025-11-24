from qtpy import QtCore, QtWidgets, QtGui
import os
from imswitch.imcontrol.view import guitools as guitools
from imswitch.imcommon.model import dirtools, initLogger
from .basewidgets import Widget


class RotationScanWidget(Widget):
    """ Widget in control of experiments where rotation mounts should be
    triggered to rotate during scans, between axis 2 steps (frames in XYT for example).
    TODO: Possible create a break in the scanning when rotators are moving. """

    sigActivate = QtCore.Signal(bool)
    sigCalibration = QtCore.Signal()
    sigManual = QtCore.Signal()
    sigPlus = QtCore.Signal()
    sigMinus = QtCore.Signal()

    def __init__(self, *args, **kwargs):

        self.__logger = initLogger(self, tryInheritParent=True)
        super().__init__(*args, **kwargs)
        self.numPositioners = 0
        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.enabled = True
        self.manual = False

        self.calibration_dir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_rotscan')
        if not os.path.exists(self.calibration_dir):
            os.makedirs(self.calibration_dir)


    def initControls(self):
        # Treat parameters as polarization rotation parameters.
        self.pars['RotStepLabel'] = QtWidgets.QLabel('Pol. rotation step')
        self.pars['RotStepEdit'] = QtWidgets.QLineEdit('10')
        self.pars['RotStepUnit'] = QtWidgets.QLabel(' deg')
        self.pars['RotStartLabel'] = QtWidgets.QLabel('Pol. rotation start')
        self.pars['RotStartEdit'] = QtWidgets.QLineEdit('0')
        self.pars['RotStartUnit'] = QtWidgets.QLabel(' deg')
        self.pars['RotStopLabel'] = QtWidgets.QLabel('Pol. rotation stop')
        self.pars['RotStopEdit'] = QtWidgets.QLineEdit('180')
        self.pars['RotStopUnit'] = QtWidgets.QLabel(' deg')
        self.pars['LoadCalibrateLabel'] = QtWidgets.QLabel('Calibration file')

        # Add all available calibrations to a dropdown list
        self.pars['LoadCalibrateEdit'] = QtWidgets.QComboBox()
        self.LoadCalibrationFiles = list()
        for calib in os.listdir(self.calibration_dir):
            if os.path.isfile(os.path.join(self.calibration_dir, calib)):
                calib = calib.split('.')[0]
                self.LoadCalibrationFiles.append(calib)
        self.pars['LoadCalibrateEdit'].addItems(self.LoadCalibrationFiles)
        self.pars['LoadCalibrateEdit'].setCurrentIndex(0)

        self.pars['ActivateButton'] = guitools.BetterPushButton('Activate during scan')
        self.pars['CalibrateButton'] = guitools.BetterPushButton('Calibrate polarization')
        self.pars['SaveCalibrationButton'] = guitools.BetterPushButton('Save calibration')
        self.pars['LoadCalibrationButton'] = guitools.BetterPushButton('Load calibration')  # we have a drop down list, but still need to load

        # Parameters for calibration routine
        self.pars['CalibrationPrompt'] = QtWidgets.QLineEdit('')
        self.pars['CalibrationPrompt'].setReadOnly(True)
        calibrationPromptPalette = QtGui.QPalette()
        calibrationPromptPalette.setColor(QtGui.QPalette.Text, QtGui.QColor(150, 150, 150))
        calibrationPromptPalette.setColor(QtGui.QPalette.Base, QtGui.QColor(60, 60, 60))
        self.pars['CalibrationPrompt'].setPalette(calibrationPromptPalette)

        # Grid layout definition

        # Create QLabel for section headers with larger and bold text
        calibrate_label = QtWidgets.QLabel('<strong>Calibration</strong>')
        parameters_label = QtWidgets.QLabel('<strong>Parameters</strong>')


        # Row 0: Calibrate section header
        self.grid.addWidget(calibrate_label, 0, 0, 1, 3)

        # Row 1: Calibration Load and related buttons
        self.grid.addWidget(self.pars['LoadCalibrateLabel'], 1, 0)
        self.grid.addWidget(self.pars['LoadCalibrateEdit'], 1, 1)
        self.grid.addWidget(self.pars['LoadCalibrationButton'], 1, 3)

        # Row 2-3: Calibration buttons and prompt
        self.grid.addWidget(self.pars['CalibrateButton'], 2, 3)
        self.grid.addWidget(self.pars['SaveCalibrationButton'], 3, 3)
        self.grid.addWidget(self.pars['CalibrationPrompt'], 2, 0, 1, 3)

        # Row 4: Parameters section header
        self.grid.addWidget(parameters_label, 4, 0, 1, 3)

        # Row 5-7: Pol Rotation Step, Start, Stop
        self.grid.addWidget(self.pars['RotStepLabel'], 5, 0)
        self.grid.addWidget(self.pars['RotStepEdit'], 5, 1)
        self.grid.addWidget(self.pars['RotStepUnit'], 5, 2)
        self.grid.addWidget(self.pars['RotStartLabel'], 6, 0)
        self.grid.addWidget(self.pars['RotStartEdit'], 6, 1)
        self.grid.addWidget(self.pars['RotStartUnit'], 6, 2)
        self.grid.addWidget(self.pars['RotStopLabel'], 7, 0)
        self.grid.addWidget(self.pars['RotStopEdit'], 7, 1)
        self.grid.addWidget(self.pars['RotStopUnit'], 7, 2)

        # Row 8: Activate button
        self.grid.addWidget(self.pars['ActivateButton'], 8, 3)

        # Manual Scan section
        manual_scan_label = QtWidgets.QLabel('<strong>Manual Scan</strong>')

        self.pars['PolPositionLabel'] = QtWidgets.QLabel('Pol. position')
        self.pars['PolPositionEdit'] = QtWidgets.QLineEdit('')
        self.pars['PolPositionEdit'].setReadOnly(True)
        self.pars['PolPositionUnit'] = QtWidgets.QLabel('deg')

        self.pars['ManualButton'] = guitools.BetterPushButton('Start manual scan')
        self.pars['PlusButton'] = guitools.BetterPushButton('+')
        self.pars['PlusButton'].setEnabled(False)  # Disable by default
        self.pars['MinusButton'] = guitools.BetterPushButton('-')
        self.pars['MinusButton'].setEnabled(False)  # Disable by default

        # Row 9: Manual Scan section header
        self.grid.addWidget(manual_scan_label, 9, 0, 1, 3)

        # Row 10: Pol Position, QLineEdit, and deg and Abs button
        self.grid.addWidget(self.pars['PolPositionLabel'], 10, 0)
        self.grid.addWidget(self.pars['PolPositionEdit'], 10, 1)
        self.grid.addWidget(self.pars['PolPositionUnit'], 10, 2)
        self.grid.addWidget(self.pars['ManualButton'], 10, 3)

        # Row 11-12:  +, and - buttons
        self.grid.addWidget(self.pars['PlusButton'], 11, 3)
        self.grid.addWidget(self.pars['MinusButton'], 12, 3)

        # Connect signals
        self.pars['ActivateButton'].clicked.connect(lambda: self.sigActivate.emit(not self.enabled))
        self.pars['CalibrateButton'].clicked.connect(lambda: self.sigCalibration.emit())
        self.pars['ManualButton'].clicked.connect(lambda: self.sigManual.emit())
        self.pars['PlusButton'].clicked.connect(lambda: self.sigPlus.emit())
        self.pars['MinusButton'].clicked.connect(lambda: self.sigMinus.emit())

    def getRotationStart(self):
        """ Returns the user-input polarization rotation start, in deg. """
        return float(self.pars['RotStartEdit'].text())

    def getRotationStop(self):
        """ Returns the user-input polarization rotation stop, in deg. """
        return float(self.pars['RotStopEdit'].text())

    def getRotationStep(self):
        """ Returns the user-input polarization rotation step, in deg. """
        return float(self.pars['RotStepEdit'].text())

    def enableInterface(self, enabled):
        """ For inactivating during scanning when ActivateButton pressed
        and waiting for a scan. When scan finishes, enable again. """
        self.pars['RotStartEdit'].setEnabled(enabled)
        self.pars['RotStopEdit'].setEnabled(enabled)
        self.pars['RotStepEdit'].setEnabled(enabled)
        self.enabled = enabled

    def enableManualInterface(self,enabled):
        """ For inactivating during scanning when ActivateButton pressed
        and waiting for a scan. When scan finishes, enable again. """
        self.pars['ManualButton'].setEnabled(enabled)
        self.pars['PlusButton'].setEnabled(enabled)
        self.pars['MinusButton'].setEnabled(enabled)


    def setActivateButtonText(self, text):
        """ Set text of activation button. """
        self.pars['ActivateButton'].setText(text)

    def setCalibrationPrompt(self, text):
        """ Set text of calibration prompt during calibration. """
        self.pars['CalibrationPrompt'].setText(text)

    def setCalibrationButtonText(self, text):
        """ Set text of calibration button during calibration. """
        self.pars['CalibrateButton'].setText(text)

    def setRotationParameters(self, rotationPars):
        """ Set text of rotation step, start and stop angle. """
        self.pars['RotStepEdit'].setText(rotationPars[0])
        self.pars['RotStartEdit'].setText(rotationPars[1])
        self.pars['RotStopEdit'].setText(rotationPars[2])
        
    def setPolPositionText(self, text): #WIP Simone, this should automatically show the polarization in a manual scan
        """ Set text of Pol position"""
        self.pars['PolPositionEdit'].setText(text)

    def setManualButtonText(self, text): #WIP Simone
        """ Set text of manual scan button"""
        self.pars['ManualButton'].setText(text)
        
    def setLoadCalibrate(self, calibname):
        # Find the index of the provided text
        index = self.pars['LoadCalibrateEdit'].findText(calibname)
        # Check if the text exists in the QComboBox
        if index == -1:
            self.__logger.error(f"'{calibname}' not found in the QComboBox")
        else:
            # Set the current index to the found index
            self.pars['LoadCalibrateEdit'].setCurrentIndex(index)



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
