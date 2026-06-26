import os
from datetime import datetime

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from qtpy import QtWidgets

from imswitch.imcommon.model import dirtools, initLogger
from imswitch.imcontrol.model import configfiletools
from imswitch.imcontrol.model.SetupInfo import (
    CalibrationsInfo,
    FociAffineCalibrationSetupInfo,
)
from imswitch.imcontrol.model.foci_affine import (
    autolocalize_grid_parameters,
    calibrate_foci_affine,
    load_calibration,
    save_calibration,
)
from imswitch.imcontrol.view import guitools
from ..basecontrollers import ImConWidgetController

try:
    from imswitch.imreconstruct.model.localizer import localizer
    LOCALIZER_AVAILABLE = True
except Exception:
    LOCALIZER_AVAILABLE = False


class FociAffineController(ImConWidgetController):
    """Linked to FociAffineWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self, tryInheritParent=True)

        self.referenceImage = None
        self.movingImage = None
        self.calibration = None
        self.currentCalibrationPath = None
        self.applyAffineEnabled = False
        self.visualizationDialog = None

        self.calibrationDir = os.path.join(
            dirtools.UserFileDirs.Root,
            'calibrations',
            'foci_affine',
        )
        os.makedirs(self.calibrationDir, exist_ok=True)

        if not self._commChannel.hasImageController():
            self._widget.replaceWithError(
                'Foci affine alignment requires the Image widget to be enabled.'
            )
            return

        self._widget.sigSnapReferenceClicked.connect(self.snapReference)
        self._widget.sigSnapMovingClicked.connect(self.snapMoving)
        self._widget.sigCalibrateClicked.connect(self.calibrate)
        self._widget.sigLoadCalibrationClicked.connect(self.loadCalibration)
        self._widget.sigSaveCalibrationClicked.connect(self.saveCalibration)
        self._widget.sigClearCalibrationClicked.connect(self.clearCalibration)
        self._widget.sigSetStartupCalibrationClicked.connect(self.setAsStartupCalibration)
        self._widget.sigVisualizeClicked.connect(self.visualize)
        self._widget.sigApplyAffineToggled.connect(self.setApplyAffine)
        self._widget.sigTargetLayerChanged.connect(self.targetLayerChanged)

        self._refreshTargetLayers()
        self._loadStartupCalibrationIfConfigured()

    def snapReference(self):
        image = self._getCurrentSnapshotImage()
        if image is None:
            self._widget.setReferenceStatus('Reference: no image available')
            return

        self.referenceImage = image
        self._widget.setReferenceStatus(f'Reference acquired: shape {image.shape}')

    def snapMoving(self):
        image = self._getCurrentSnapshotImage()
        if image is None:
            self._widget.setMovingStatus('Moving: no image available')
            return

        self.movingImage = image
        self._widget.setMovingStatus(f'Moving acquired: shape {image.shape}')

    def calibrate(self):
        if self.referenceImage is None or self.movingImage is None:
            self._widget.setCalibrationStatus('Acquire reference and moving images first')
            return

        n_rows, n_cols, detection_params, parameter_status = self._resolveCalibrationParameters()

        try:
            self.calibration = calibrate_foci_affine(
                reference_image=self.referenceImage,
                moving_image=self.movingImage,
                n_rows=n_rows,
                n_cols=n_cols,
                detection_params=detection_params,
                residual_threshold=self._widget.getResidualThreshold(),
            )
        except Exception as e:
            self.__logger.warning(f'Foci affine calibration failed: {e}')
            self._widget.setCalibrationStatus(f'Calibration failed: {e}')
            self._widget.setApplyEnabled(False)
            return

        self.currentCalibrationPath = None
        self._widget.setCalibrationStatus(f'Calibration ready ({parameter_status})')
        self._widget.setApplyEnabled(True)
        self._updateResidualSummary()
        self._refreshTargetLayers()

        if self.applyAffineEnabled:
            self._applyCalibrationToTargetLayers()

    def loadCalibration(self):
        path = guitools.askForFilePath(
            self._widget,
            'Load foci affine calibration',
            defaultFolder=self.calibrationDir,
            nameFilter='*.npz',
        )
        if not path:
            return

        self._loadCalibrationFromPath(path, status_prefix='Loaded calibration')

    def saveCalibration(self):
        if self.calibration is None:
            self._widget.setCalibrationStatus('No calibration to save')
            return

        path = self._askForCalibrationSavePath('Save foci affine calibration')
        if path is None:
            return

        if self._saveCalibrationToPath(path):
            self._widget.setCalibrationStatus(f'Saved calibration: {os.path.basename(path)}')

    def setAsStartupCalibration(self):
        if self.calibration is None:
            self._widget.setCalibrationStatus('No calibration loaded')
            return

        path = self.currentCalibrationPath
        saved_during_startup = False
        if not path or not os.path.isfile(path):
            path = self._askForCalibrationSavePath('Save foci affine startup calibration')
            if path is None:
                return
            if not self._saveCalibrationToPath(path):
                return
            saved_during_startup = True

        try:
            self._setStartupCalibrationPath(path)
        except Exception as e:
            self.__logger.warning(f'Failed to set startup foci affine calibration: {e}')
            QtWidgets.QMessageBox.warning(
                self._widget,
                'Startup calibration',
                f'Could not set startup calibration: {e}',
            )
            return

        if saved_during_startup:
            self._widget.setCalibrationStatus(f'Saved calibration: {os.path.basename(path)}')

        QtWidgets.QMessageBox.information(
            self._widget,
            'Startup calibration',
            f'{os.path.basename(path)} will be loaded at startup.',
        )

    def _askForCalibrationSavePath(self, title):
        default_name = datetime.now().strftime('%Y-%m-%d_%H%M%S_moving_to_reference.npz')
        suggested = os.path.join(self.calibrationDir, default_name)
        path = guitools.askForFilePath(
            self._widget,
            title,
            defaultFolder=suggested,
            nameFilter='*.npz',
            isSaving=True,
        )
        if not path:
            return None
        if not path.lower().endswith('.npz'):
            path += '.npz'

        return path

    def _saveCalibrationToPath(self, path):
        try:
            save_calibration(path, self.calibration)
        except Exception as e:
            self.__logger.warning(f'Failed to save foci affine calibration: {e}')
            self._widget.setCalibrationStatus(f'Save failed: {e}')
            return False

        self.currentCalibrationPath = path
        return True

    def _loadCalibrationFromPath(self, path, status_prefix):
        path = os.path.abspath(path)
        try:
            self.calibration = load_calibration(path)
        except Exception as e:
            self.__logger.warning(f'Failed to load foci affine calibration: {e}')
            self._widget.setCalibrationStatus(f'Load failed: {e}')
            self._widget.setApplyEnabled(False)
            return False

        self.currentCalibrationPath = path
        self._widget.setCalibrationStatus(f'{status_prefix}: {os.path.basename(path)}')
        self._widget.setApplyEnabled(True)
        self._updateResidualSummary()
        self._refreshTargetLayers()

        if self.applyAffineEnabled:
            self._applyCalibrationToTargetLayers()

        return True

    def _loadStartupCalibrationIfConfigured(self):
        startup_info = self._getFociAffineStartupInfo(create=False)
        if startup_info is None:
            return
        if not getattr(startup_info, 'auto_load', False):
            return

        calibration_file = getattr(startup_info, 'calibration_file', None)
        if not calibration_file:
            return

        path = self._resolveCalibrationFilePath(calibration_file)
        if not os.path.isfile(path):
            self.__logger.warning(f'Startup foci affine calibration not found: {path}')
            self._widget.setCalibrationStatus(
                f'Startup calibration not found: {os.path.basename(path)}'
            )
            return

        self._loadCalibrationFromPath(path, status_prefix='Loaded startup calibration')

    def _setStartupCalibrationPath(self, path):
        startup_info = self._getFociAffineStartupInfo(create=True)
        object.__setattr__(startup_info, 'auto_load', True)
        object.__setattr__(startup_info, 'calibration_file', os.path.abspath(path))
        configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)

    def _getFociAffineStartupInfo(self, create):
        calibrations = getattr(self._setupInfo, 'calibrations', None)
        if isinstance(calibrations, dict):
            calibrations = self._calibrationsInfoFromDict(calibrations)
            setattr(self._setupInfo, 'calibrations', calibrations)

        if calibrations is None:
            if not create:
                return None
            calibrations = CalibrationsInfo()
            setattr(self._setupInfo, 'calibrations', calibrations)

        startup_info = getattr(calibrations, 'foci_affine', None)
        if isinstance(startup_info, dict):
            startup_info = self._fociAffineStartupInfoFromDict(startup_info)
            object.__setattr__(calibrations, 'foci_affine', startup_info)

        if startup_info is None:
            if not create:
                return None
            startup_info = FociAffineCalibrationSetupInfo()
            object.__setattr__(calibrations, 'foci_affine', startup_info)

        return startup_info

    def _calibrationsInfoFromDict(self, calibrations):
        return CalibrationsInfo(
            foci_affine=self._fociAffineStartupInfoFromDict(
                calibrations.get('foci_affine', {})
            )
        )

    def _fociAffineStartupInfoFromDict(self, startup_info):
        if isinstance(startup_info, FociAffineCalibrationSetupInfo):
            return startup_info
        if not isinstance(startup_info, dict):
            startup_info = {}

        return FociAffineCalibrationSetupInfo(
            auto_load=bool(startup_info.get('auto_load', False)),
            calibration_file=startup_info.get('calibration_file'),
        )

    def _resolveCalibrationFilePath(self, calibration_file):
        path = os.path.expanduser(str(calibration_file))
        if not os.path.isabs(path):
            path = os.path.join(self.calibrationDir, path)

        return os.path.abspath(path)

    def clearCalibration(self):
        self._widget.setApplyChecked(False)
        self.setApplyAffine(False)
        self.calibration = None
        self.currentCalibrationPath = None
        self._widget.setApplyEnabled(False)
        self._widget.setCalibrationStatus('No calibration loaded')
        self._widget.setResidualSummary()

    def setApplyAffine(self, enabled):
        self.applyAffineEnabled = bool(enabled)

        if not self.applyAffineEnabled:
            self._commChannel.clearAllDisplayLayerAffines()
            return

        if self.calibration is None:
            self._widget.setApplyChecked(False)
            self.applyAffineEnabled = False
            self._widget.setCalibrationStatus('No calibration loaded')
            return

        self._applyCalibrationToTargetLayers()

    def targetLayerChanged(self):
        if self.applyAffineEnabled and self.calibration is not None:
            self._applyCalibrationToTargetLayers()

    def visualize(self):
        if self.calibration is None:
            return

        if self.referenceImage is None or self.movingImage is None:
            QtWidgets.QMessageBox.information(
                self._widget,
                'Foci affine visualization',
                'Acquire reference and moving images to visualize this calibration.',
            )
            return

        try:
            dialog = self._createVisualizationDialog()
        except Exception as e:
            self.__logger.warning(f'Could not visualize foci affine calibration: {e}')
            QtWidgets.QMessageBox.warning(
                self._widget,
                'Foci affine visualization',
                f'Visualization failed: {e}',
            )
            return

        if self.visualizationDialog is not None:
            self.visualizationDialog.close()
        self.visualizationDialog = dialog
        self.visualizationDialog.show()

    def _applyCalibrationToTargetLayers(self):
        target_layer = self._widget.getTargetLayerName()
        self._refreshTargetLayers()
        affine = self.calibration.matrix_yx_napari
        display_layers = self._commChannel.getDisplayImageLayerNames()

        self._commChannel.clearAllDisplayLayerAffines()
        if target_layer is None:
            self._commChannel.setAllDisplayLayerAffines(affine)
            return

        if target_layer not in display_layers:
            self.__logger.warning(f'Foci affine target layer unavailable: {target_layer}')
            self.applyAffineEnabled = False
            self._widget.setApplyChecked(False)
            return

        self._commChannel.setDisplayLayerAffine(target_layer, affine)

    def _resolveCalibrationParameters(self):
        manual_n_rows, manual_n_cols = self._widget.getGridShape()
        manual_detection_params = self._widget.getDetectionParams()

        if not self._widget.getAutolocalizeEnabled():
            return manual_n_rows, manual_n_cols, manual_detection_params, 'manual parameters'

        if not LOCALIZER_AVAILABLE:
            return (
                manual_n_rows,
                manual_n_cols,
                manual_detection_params,
                'manual parameters; autolocalize unavailable',
            )

        try:
            reference_localization = localizer(self.referenceImage)
            moving_localization = localizer(self.movingImage)
            n_rows, n_cols, min_distance = autolocalize_grid_parameters(
                reference_localization,
                moving_localization,
            )
        except Exception as e:
            self.__logger.warning(f'Foci affine autolocalize failed; using manual parameters: {e}')
            return (
                manual_n_rows,
                manual_n_cols,
                manual_detection_params,
                'manual parameters; autolocalize failed',
            )

        detection_params = dict(manual_detection_params)
        detection_params["min_distance"] = min_distance
        return (
            n_rows,
            n_cols,
            detection_params,
            f'autolocalized {n_rows}x{n_cols}',
        )

    def _getCurrentSnapshotImage(self):
        image = None

        if self._master.detectorsManager.hasDevices():
            try:
                image = self._master.detectorsManager.execOnCurrent(
                    lambda detector: detector.getLatestFrame()
                )
            except Exception as e:
                self.__logger.debug(f'Could not read current detector frame: {e}')

        snapshot = self._asSnapshotImage(image)
        if snapshot is not None:
            return snapshot

        try:
            image = self._commChannel.getActiveImageLayerData()
        except Exception as e:
            self.__logger.debug(f'Could not read active napari image layer: {e}')
            image = None

        return self._asSnapshotImage(image)

    def _asSnapshotImage(self, image):
        if image is None:
            return None

        image = np.asarray(image)
        image = np.squeeze(image)
        if image.ndim != 2 or image.size <= 1:
            return None

        return np.array(image, copy=True)

    def _updateResidualSummary(self):
        if self.calibration is None:
            self._widget.setResidualSummary()
            return

        residuals = np.asarray(self.calibration.residuals_px, dtype=float)
        self._widget.setResidualSummary(
            mean_px=float(np.mean(residuals)),
            median_px=float(np.median(residuals)),
            max_px=float(np.max(residuals)),
            n_points=int(len(residuals)),
        )

    def _refreshTargetLayers(self):
        try:
            display_layers = self._commChannel.getDisplayImageLayerNames()
        except Exception as e:
            self.__logger.debug(f'Could not refresh foci affine target layers: {e}')
            display_layers = []

        self._widget.setTargetLayerNames(display_layers)

    def _createVisualizationDialog(self):
        dialog = QtWidgets.QDialog(self._widget)
        dialog.setWindowTitle('Foci affine visualization')
        dialog.resize(1000, 520)

        layout = QtWidgets.QVBoxLayout(dialog)
        figure = Figure(figsize=(10, 5), dpi=100)
        canvas = FigureCanvas(figure)
        layout.addWidget(canvas)

        reference_axis, moving_axis = figure.subplots(1, 2)
        self._plotReferenceLocalization(reference_axis)
        self._plotMovingLocalization(moving_axis)
        figure.tight_layout()
        canvas.draw()

        return dialog

    def _plotReferenceLocalization(self, axis):
        axis.imshow(self.referenceImage, cmap='gray')
        reference_points = self.calibration.reference_points_xy
        axis.scatter(
            reference_points[:, 0],
            reference_points[:, 1],
            s=28,
            facecolors='none',
            edgecolors='lime',
            linewidths=1.0,
            label='reference spots',
        )
        self._formatImageAxis(axis, self.referenceImage, 'Reference image')
        axis.legend(loc='upper right', fontsize=8)

    def _plotMovingLocalization(self, axis):
        axis.imshow(self.movingImage, cmap='gray')
        moving_points = self.calibration.moving_points_xy
        axis.scatter(
            moving_points[:, 0],
            moving_points[:, 1],
            s=28,
            facecolors='none',
            edgecolors='cyan',
            linewidths=1.0,
            label='moving spots',
        )
        self._formatImageAxis(axis, self.movingImage, 'Moving image')
        axis.legend(loc='upper right', fontsize=8)

    def _formatImageAxis(self, axis, image, title):
        axis.set_title(title)
        axis.set_xlim(-0.5, image.shape[1] - 0.5)
        axis.set_ylim(image.shape[0] - 0.5, -0.5)
        axis.set_aspect('equal')


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
