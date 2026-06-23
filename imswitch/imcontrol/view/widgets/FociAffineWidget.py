from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class FociAffineWidget(Widget):
    """User-facing controls for foci-array affine display calibration."""

    sigSnapReferenceClicked = QtCore.Signal()
    sigSnapMovingClicked = QtCore.Signal()
    sigCalibrateClicked = QtCore.Signal()
    sigLoadCalibrationClicked = QtCore.Signal()
    sigSaveCalibrationClicked = QtCore.Signal()
    sigClearCalibrationClicked = QtCore.Signal()
    sigApplyAffineToggled = QtCore.Signal(bool)
    sigShowLocalizationToggled = QtCore.Signal(bool)
    sigShowTransformedPointsToggled = QtCore.Signal(bool)
    sigShowResidualVectorsToggled = QtCore.Signal(bool)
    sigClearLocalizationClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.snapReferenceButton = guitools.BetterPushButton('Snap reference')
        self.snapMovingButton = guitools.BetterPushButton('Snap moving')
        self.referenceStatusLabel = QtWidgets.QLabel('Reference: not acquired')
        self.movingStatusLabel = QtWidgets.QLabel('Moving: not acquired')

        self._parameters = {
            "n_rows": 10,
            "n_cols": 10,
            "min_distance": 10,
            "threshold_rel": 0.2,
            "refine_radius": 5,
            "gaussian_sigma": 1.0,
            "residual_threshold": 2.0,
        }
        self.editParametersButton = guitools.BetterPushButton('Edit parameters')

        self.calibrateButton = guitools.BetterPushButton('Calibrate')
        self.loadCalibrationButton = guitools.BetterPushButton('Load')
        self.loadCalibrationButton.setToolTip('Load calibration')
        self.saveCalibrationButton = guitools.BetterPushButton('Save')
        self.saveCalibrationButton.setToolTip('Save calibration')
        self.clearCalibrationButton = guitools.BetterPushButton('Clear')
        self.clearCalibrationButton.setToolTip('Clear calibration')

        self.applyAffineCheck = QtWidgets.QCheckBox('Apply affine')
        self.applyAffineCheck.setEnabled(False)
        self.targetLabel = QtWidgets.QLabel('Target: all live layers')

        self.showLocalizationCheck = QtWidgets.QCheckBox('Show localization')
        self.showTransformedPointsCheck = QtWidgets.QCheckBox('Show transformed points')
        self.showResidualVectorsCheck = QtWidgets.QCheckBox('Show residual vectors')
        self.clearLocalizationButton = guitools.BetterPushButton('Clear overlay')
        self.clearLocalizationButton.setToolTip('Clear localization overlay')

        self.calibrationStatusLabel = QtWidgets.QLabel('No calibration loaded')
        self.residualSummaryLabel = QtWidgets.QLabel('Residuals: n/a')

        self._setupLayout()
        self._connectSignals()

    def _setupLayout(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        snapLayout = QtWidgets.QGridLayout()
        snapLayout.addWidget(QtWidgets.QLabel('Reference image'), 0, 0)
        snapLayout.addWidget(self.snapReferenceButton, 0, 1)
        snapLayout.addWidget(self.referenceStatusLabel, 1, 0, 1, 2)
        snapLayout.addWidget(QtWidgets.QLabel('Moving image'), 2, 0)
        snapLayout.addWidget(self.snapMovingButton, 2, 1)
        snapLayout.addWidget(self.movingStatusLabel, 3, 0, 1, 2)
        layout.addLayout(snapLayout)

        layout.addWidget(self.editParametersButton)

        calibrationLayout = QtWidgets.QHBoxLayout()
        calibrationLayout.addWidget(self.calibrateButton)
        calibrationLayout.addWidget(self.loadCalibrationButton)
        calibrationLayout.addWidget(self.saveCalibrationButton)
        calibrationLayout.addWidget(self.clearCalibrationButton)
        layout.addLayout(calibrationLayout)

        applyLayout = QtWidgets.QHBoxLayout()
        applyLayout.addWidget(self.applyAffineCheck)
        applyLayout.addWidget(self.targetLabel)
        applyLayout.addStretch()
        layout.addLayout(applyLayout)

        visualizationLayout = QtWidgets.QHBoxLayout()
        visualizationLayout.addWidget(self.showLocalizationCheck)
        visualizationLayout.addWidget(self.showTransformedPointsCheck)
        visualizationLayout.addWidget(self.showResidualVectorsCheck)
        visualizationLayout.addWidget(self.clearLocalizationButton)
        layout.addLayout(visualizationLayout)

        statusLayout = QtWidgets.QHBoxLayout()
        statusLayout.addWidget(self.calibrationStatusLabel, 1)
        statusLayout.addWidget(self.residualSummaryLabel, 1)
        layout.addLayout(statusLayout)
        layout.addStretch()

    def _connectSignals(self):
        self.snapReferenceButton.clicked.connect(self.sigSnapReferenceClicked)
        self.snapMovingButton.clicked.connect(self.sigSnapMovingClicked)
        self.editParametersButton.clicked.connect(self._editParameters)
        self.calibrateButton.clicked.connect(self.sigCalibrateClicked)
        self.loadCalibrationButton.clicked.connect(self.sigLoadCalibrationClicked)
        self.saveCalibrationButton.clicked.connect(self.sigSaveCalibrationClicked)
        self.clearCalibrationButton.clicked.connect(self.sigClearCalibrationClicked)
        self.applyAffineCheck.toggled.connect(self.sigApplyAffineToggled)
        self.showLocalizationCheck.toggled.connect(self.sigShowLocalizationToggled)
        self.showTransformedPointsCheck.toggled.connect(self.sigShowTransformedPointsToggled)
        self.showResidualVectorsCheck.toggled.connect(self.sigShowResidualVectorsToggled)
        self.clearLocalizationButton.clicked.connect(self.sigClearLocalizationClicked)

    def setReferenceStatus(self, text):
        self.referenceStatusLabel.setText(str(text))

    def setMovingStatus(self, text):
        self.movingStatusLabel.setText(str(text))

    def setCalibrationStatus(self, text):
        self.calibrationStatusLabel.setText(str(text))

    def setResidualSummary(self, mean_px=None, median_px=None, max_px=None, n_points=None):
        if n_points is None:
            self.residualSummaryLabel.setText('Residuals: n/a')
            return

        self.residualSummaryLabel.setText(
            f'Residuals: mean {mean_px:.3f} px, median {median_px:.3f} px, '
            f'max {max_px:.3f} px, n {n_points}'
        )

    def setApplyEnabled(self, enabled):
        self.applyAffineCheck.setEnabled(bool(enabled))

    def setApplyChecked(self, checked):
        previous = self.applyAffineCheck.blockSignals(True)
        try:
            self.applyAffineCheck.setChecked(bool(checked))
        finally:
            self.applyAffineCheck.blockSignals(previous)

    def setVisualizationChecked(self, localization=None, transformed=None, residuals=None):
        self._setCheckWithoutSignal(self.showLocalizationCheck, localization)
        self._setCheckWithoutSignal(self.showTransformedPointsCheck, transformed)
        self._setCheckWithoutSignal(self.showResidualVectorsCheck, residuals)

    def getGridShape(self):
        return int(self._parameters["n_rows"]), int(self._parameters["n_cols"])

    def getDetectionParams(self):
        return {
            "min_distance": int(self._parameters["min_distance"]),
            "threshold_rel": float(self._parameters["threshold_rel"]),
            "refine_radius": int(self._parameters["refine_radius"]),
            "gaussian_sigma": float(self._parameters["gaussian_sigma"]),
        }

    def getResidualThreshold(self):
        return float(self._parameters["residual_threshold"])

    def _editParameters(self):
        updated = guitools.JsonEditorDialog.edit_params(
            self,
            self._parameters,
            title='Edit foci affine parameters',
        )
        if updated is None:
            return

        try:
            self._parameters = self._normalizeParameters(updated)
        except (KeyError, TypeError, ValueError) as e:
            QtWidgets.QMessageBox.warning(
                self,
                'Invalid parameters',
                f'Could not apply parameters: {e}',
            )

    def _normalizeParameters(self, params):
        normalized = {
            "n_rows": int(params["n_rows"]),
            "n_cols": int(params["n_cols"]),
            "min_distance": int(params["min_distance"]),
            "threshold_rel": float(params["threshold_rel"]),
            "refine_radius": int(params["refine_radius"]),
            "gaussian_sigma": float(params["gaussian_sigma"]),
            "residual_threshold": float(params["residual_threshold"]),
        }

        if normalized["n_rows"] < 1 or normalized["n_cols"] < 1:
            raise ValueError('n_rows and n_cols must be at least 1')
        if normalized["min_distance"] < 1:
            raise ValueError('min_distance must be at least 1')
        if not 0 <= normalized["threshold_rel"] <= 1:
            raise ValueError('threshold_rel must be between 0 and 1')
        if normalized["refine_radius"] < 0:
            raise ValueError('refine_radius must be at least 0')
        if normalized["gaussian_sigma"] < 0:
            raise ValueError('gaussian_sigma must be at least 0')
        if normalized["residual_threshold"] <= 0:
            raise ValueError('residual_threshold must be greater than 0')

        return normalized

    def _setCheckWithoutSignal(self, checkbox, checked):
        if checked is None:
            return

        previous = checkbox.blockSignals(True)
        try:
            checkbox.setChecked(bool(checked))
        finally:
            checkbox.blockSignals(previous)


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
