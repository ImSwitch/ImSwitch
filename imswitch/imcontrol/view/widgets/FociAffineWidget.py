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
    sigSetStartupCalibrationClicked = QtCore.Signal()
    sigVisualizeClicked = QtCore.Signal()
    sigApplyAffineToggled = QtCore.Signal(bool)
    sigTargetLayerChanged = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.snapReferenceButton = guitools.BetterPushButton('Snap Reference')
        self.snapMovingButton = guitools.BetterPushButton('Snap Moving')
        self.referenceStatusLabel = QtWidgets.QLabel('Reference: not acquired')
        self.movingStatusLabel = QtWidgets.QLabel('Moving: not acquired')

        self._parameters = {
            "autolocalize": True,
            "n_rows": 10,
            "n_cols": 10,
            "min_distance": 10,
            "threshold_rel": 0.2,
            "refine_radius": 5,
            "gaussian_sigma": 1.0,
            "residual_threshold": 2.0,
        }
        self.editParametersButton = guitools.BetterPushButton('Edit Parameters')

        self.calibrateButton = guitools.BetterPushButton('Calibrate')
        self.visualizeButton = guitools.BetterPushButton('Visualize')
        self.loadCalibrationButton = guitools.BetterPushButton('Load')
        self.loadCalibrationButton.setToolTip('Load calibration')
        self.saveCalibrationButton = guitools.BetterPushButton('Save')
        self.saveCalibrationButton.setToolTip('Save calibration')
        self.clearCalibrationButton = guitools.BetterPushButton('Clear')
        self.clearCalibrationButton.setToolTip('Clear calibration')
        self.setStartupCalibrationButton = guitools.BetterPushButton('Set as startup calib')
        self.setStartupCalibrationButton.setToolTip(
            'Load this calibration automatically at startup'
        )
        self.setStartupCalibrationButton.setEnabled(False)

        self.applyAffineCheck = QtWidgets.QCheckBox('Apply Affine')
        self.applyAffineCheck.setEnabled(False)
        self.targetLayerCombo = QtWidgets.QComboBox()
        self.targetLayerCombo.addItem('all layers')
        self.targetLayerCombo.setMinimumWidth(140)

        self.calibrationStatusLabel = QtWidgets.QLabel('No calibration loaded')
        self.calibrationStatusLabel.setWordWrap(False)
        self._residualSummary = 'Residuals: n/a'

        self._setupLayout()
        self._connectSignals()

    def _setupLayout(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        actionLayout = QtWidgets.QGridLayout()
        actionLayout.addWidget(QtWidgets.QLabel('Reference image'), 0, 0)
        actionLayout.addWidget(self.snapReferenceButton, 0, 1)
        actionLayout.addWidget(self.referenceStatusLabel, 0, 2)
        actionLayout.addWidget(QtWidgets.QLabel('Moving image'), 1, 0)
        actionLayout.addWidget(self.snapMovingButton, 1, 1)
        actionLayout.addWidget(self.movingStatusLabel, 1, 2)
        actionLayout.addWidget(self.calibrateButton, 2, 0)
        actionLayout.addWidget(self.visualizeButton, 2, 1)
        actionLayout.addWidget(self.editParametersButton, 2, 2)
        actionLayout.addWidget(self.loadCalibrationButton, 3, 0)
        actionLayout.addWidget(self.saveCalibrationButton, 3, 1)
        actionLayout.addWidget(self.clearCalibrationButton, 3, 2)
        actionLayout.setColumnStretch(0, 1)
        actionLayout.setColumnStretch(1, 1)
        actionLayout.setColumnStretch(2, 1)
        layout.addLayout(actionLayout)

        statusLayout = QtWidgets.QHBoxLayout()
        statusLayout.addWidget(self.calibrationStatusLabel, 1)
        statusLayout.addWidget(self.applyAffineCheck)
        statusLayout.addWidget(QtWidgets.QLabel('Target:'))
        statusLayout.addWidget(self.targetLayerCombo)
        statusLayout.addWidget(self.setStartupCalibrationButton)
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
        self.setStartupCalibrationButton.clicked.connect(
            self.sigSetStartupCalibrationClicked
        )
        self.visualizeButton.clicked.connect(self.sigVisualizeClicked)
        self.applyAffineCheck.toggled.connect(self.sigApplyAffineToggled)
        self.targetLayerCombo.currentIndexChanged.connect(
            lambda *_: self.sigTargetLayerChanged.emit()
        )

    def setReferenceStatus(self, text):
        self.referenceStatusLabel.setText(str(text))

    def setMovingStatus(self, text):
        self.movingStatusLabel.setText(str(text))

    def setCalibrationStatus(self, text):
        self.calibrationStatusLabel.setText(str(text))

    def setResidualSummary(self, mean_px=None, median_px=None, max_px=None, n_points=None):
        if n_points is None:
            self._residualSummary = 'Residuals: n/a'
            self.calibrationStatusLabel.setToolTip(self._residualSummary)
            return

        self._residualSummary = (
            f'Residuals: mean {mean_px:.3f} px, median {median_px:.3f} px, '
            f'max {max_px:.3f} px, n {n_points}'
        )
        self.calibrationStatusLabel.setToolTip(self._residualSummary)

    def setApplyEnabled(self, enabled):
        self.applyAffineCheck.setEnabled(bool(enabled))
        self.setStartupCalibrationButton.setEnabled(bool(enabled))

    def setApplyChecked(self, checked):
        previous = self.applyAffineCheck.blockSignals(True)
        try:
            self.applyAffineCheck.setChecked(bool(checked))
        finally:
            self.applyAffineCheck.blockSignals(previous)

    def setTargetLayerNames(self, names):
        names = [str(name) for name in names]
        current = self.getTargetLayerName()

        previous = self.targetLayerCombo.blockSignals(True)
        try:
            self.targetLayerCombo.clear()
            self.targetLayerCombo.addItem('all layers')
            self.targetLayerCombo.addItems(names)

            if current in names:
                self.targetLayerCombo.setCurrentText(current)
            else:
                self.targetLayerCombo.setCurrentIndex(0)
        finally:
            self.targetLayerCombo.blockSignals(previous)

    def getTargetLayerName(self):
        if self.targetLayerCombo.currentIndex() <= 0:
            return None

        return self.targetLayerCombo.currentText()

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

    def getAutolocalizeEnabled(self):
        return bool(self._parameters.get("autolocalize", False))

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
            "autolocalize": bool(params.get("autolocalize", True)),
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
