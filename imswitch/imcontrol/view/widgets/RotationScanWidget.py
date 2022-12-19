from qtpy import QtCore, QtWidgets, QtGui

from imswitch.imcontrol.view import guitools as guitools

from .basewidgets import Widget


class RotationScanWidget(Widget):
    """ Widget in control of experiments where rotation mounts should be
    triggered to rotate during scans, between axis 2 steps (frames in XYT).
    TODO: If possible with a break in the scanning, but it is easier without. """

    sigActivate = QtCore.Signal(bool)
    sigCalibration = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 0
        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.enabled = True

    def initControls(self):
        # Treat parameters as polarization rotation parameters.
        self.pars['RotStepLabel'] = QtWidgets.QLabel('Pol. rotation step')
        self.pars['RotStepEdit'] = QtWidgets.QLineEdit('10')
        self.pars['RotStepUnit'] = QtWidgets.QLabel(' deg')
        self.pars['RotStartLabel'] = QtWidgets.QLabel('Pol. rotation start')
        self.pars['RotStartEdit'] = QtWidgets.QLineEdit('0')
        self.pars['RotStartUnit'] = QtWidgets.QLabel(' deg')
        self.pars['RotStopLabel'] = QtWidgets.QLabel('Pol. rotation stop')
        self.pars['RotStopEdit'] = QtWidgets.QLineEdit('80')
        self.pars['RotStopUnit'] = QtWidgets.QLabel(' deg')

        self.pars['ActivateButton'] = guitools.BetterPushButton('Activate during scan')
        self.pars['CalibrateButton'] = guitools.BetterPushButton('Calibrate polarization')
        self.pars['SaveCalibrationButton'] = guitools.BetterPushButton('Save calibration')
        self.pars['LoadCalibrationButton'] = guitools.BetterPushButton('Load calibration')

        # Parameters for calibration routine
        self.pars['CalibrationPrompt'] = QtWidgets.QLineEdit('Calibration not active.')
        self.pars['CalibrationPrompt'].setReadOnly(True)
        calibrationPromptPalette = QtGui.QPalette()
        calibrationPromptPalette.setColor(QtGui.QPalette.Text, QtGui.QColor(200, 200, 200))
        calibrationPromptPalette.setColor(QtGui.QPalette.Base, QtGui.QColor(40, 40, 40))
        self.pars['CalibrationPrompt'].setPalette(calibrationPromptPalette)

        self.grid.addWidget(self.pars['RotStepLabel'], 0, 0)
        self.grid.addWidget(self.pars['RotStepEdit'], 0, 1)
        self.grid.addWidget(self.pars['RotStepUnit'], 0, 2)
        self.grid.addWidget(self.pars['RotStartLabel'], 1, 0)
        self.grid.addWidget(self.pars['RotStartEdit'], 1, 1)
        self.grid.addWidget(self.pars['RotStartUnit'], 1, 2)
        self.grid.addWidget(self.pars['RotStopLabel'], 2, 0)
        self.grid.addWidget(self.pars['RotStopEdit'], 2, 1)
        self.grid.addWidget(self.pars['RotStopUnit'], 2, 2)
        self.grid.addWidget(self.pars['ActivateButton'], 3, 0)
        self.grid.addWidget(self.pars['CalibrateButton'], 3, 1)
        self.grid.addWidget(self.pars['SaveCalibrationButton'], 3, 2)
        self.grid.addWidget(self.pars['LoadCalibrationButton'], 3, 3)
        self.grid.addWidget(self.pars['CalibrationPrompt'], 4, 0, 1, 4)

        # Connect signals
        self.pars['ActivateButton'].clicked.connect(lambda: self.sigActivate.emit(not self.enabled))
        self.pars['CalibrateButton'].clicked.connect(lambda: self.sigCalibration.emit())


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

    def setActivateButtonText(self, text):
        """ Set text of activation button. """
        self.pars['ActivateButton'].setText(text)

    def setCalibrationPrompt(self, text):
        """ Set text of calibration prompt during calibration. """
        self.pars['CalibrationPrompt'].setText(text)

    def setCalibrationButtonText(self, text):
        """ Set text of calibration button during calibration. """
        self.pars['CalibrateButton'].setText(text)


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
