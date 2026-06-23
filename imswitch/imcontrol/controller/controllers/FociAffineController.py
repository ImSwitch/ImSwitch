import os
from datetime import datetime

import numpy as np

from imswitch.imcommon.model import dirtools, initLogger
from imswitch.imcontrol.model.foci_affine import (
    calibrate_foci_affine,
    load_calibration,
    save_calibration,
)
from imswitch.imcontrol.view import guitools
from ..basecontrollers import ImConWidgetController


class FociAffineController(ImConWidgetController):
    """Linked to FociAffineWidget."""

    _referenceSnapshotLayer = 'Foci affine: reference snapshot'
    _movingSnapshotLayer = 'Foci affine: moving snapshot'
    _referencePointsLayer = 'Foci affine: reference points'
    _movingPointsLayer = 'Foci affine: moving points'
    _transformedMovingPointsLayer = 'Foci affine: transformed moving points'
    _residualVectorsLayer = 'Foci affine: residual vectors'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self, tryInheritParent=True)

        self.referenceImage = None
        self.movingImage = None
        self.calibration = None
        self.applyAffineEnabled = False
        self.showLocalization = False
        self.showTransformedPoints = False
        self.showResidualVectors = False

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
        self._widget.sigApplyAffineToggled.connect(self.setApplyAffine)
        self._widget.sigShowLocalizationToggled.connect(self.setShowLocalization)
        self._widget.sigShowTransformedPointsToggled.connect(self.setShowTransformedPoints)
        self._widget.sigShowResidualVectorsToggled.connect(self.setShowResidualVectors)
        self._widget.sigClearLocalizationClicked.connect(self.clearLocalizationOverlay)

    def snapReference(self):
        image = self._getCurrentSnapshotImage()
        if image is None:
            self._widget.setReferenceStatus('Reference: no image available')
            return

        self.referenceImage = image
        self._commChannel.addOrUpdateNapariImageLayer(
            self._referenceSnapshotLayer,
            image,
            blending='additive',
        )
        self._widget.setReferenceStatus(f'Reference acquired: shape {image.shape}')

    def snapMoving(self):
        image = self._getCurrentSnapshotImage()
        if image is None:
            self._widget.setMovingStatus('Moving: no image available')
            return

        self.movingImage = image
        self._commChannel.addOrUpdateNapariImageLayer(
            self._movingSnapshotLayer,
            image,
            blending='additive',
        )
        self._widget.setMovingStatus(f'Moving acquired: shape {image.shape}')

    def calibrate(self):
        if self.referenceImage is None or self.movingImage is None:
            self._widget.setCalibrationStatus('Acquire reference and moving images first')
            return

        n_rows, n_cols = self._widget.getGridShape()
        detection_params = self._widget.getDetectionParams()

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

        self._widget.setCalibrationStatus('Calibration ready')
        self._widget.setApplyEnabled(True)
        self._updateResidualSummary()
        self._updateOverlays()

        if self.applyAffineEnabled:
            self._applyCalibrationToLiveLayers()

    def loadCalibration(self):
        path = guitools.askForFilePath(
            self._widget,
            'Load foci affine calibration',
            defaultFolder=self.calibrationDir,
            nameFilter='*.npz',
        )
        if not path:
            return

        try:
            self.calibration = load_calibration(path)
        except Exception as e:
            self.__logger.warning(f'Failed to load foci affine calibration: {e}')
            self._widget.setCalibrationStatus(f'Load failed: {e}')
            self._widget.setApplyEnabled(False)
            return

        self._widget.setCalibrationStatus(f'Loaded calibration: {os.path.basename(path)}')
        self._widget.setApplyEnabled(True)
        self._updateResidualSummary()
        self._updateOverlays()

        if self.applyAffineEnabled:
            self._applyCalibrationToLiveLayers()

    def saveCalibration(self):
        if self.calibration is None:
            self._widget.setCalibrationStatus('No calibration to save')
            return

        default_name = datetime.now().strftime('%Y-%m-%d_%H%M%S_moving_to_reference.npz')
        suggested = os.path.join(self.calibrationDir, default_name)
        path = guitools.askForFilePath(
            self._widget,
            'Save foci affine calibration',
            defaultFolder=suggested,
            nameFilter='*.npz',
            isSaving=True,
        )
        if not path:
            return
        if not path.lower().endswith('.npz'):
            path += '.npz'

        try:
            save_calibration(path, self.calibration)
        except Exception as e:
            self.__logger.warning(f'Failed to save foci affine calibration: {e}')
            self._widget.setCalibrationStatus(f'Save failed: {e}')
            return

        self._widget.setCalibrationStatus(f'Saved calibration: {os.path.basename(path)}')

    def clearCalibration(self):
        self._widget.setApplyChecked(False)
        self.setApplyAffine(False)
        self.calibration = None
        self._widget.setApplyEnabled(False)
        self._widget.setCalibrationStatus('No calibration loaded')
        self._widget.setResidualSummary()
        self.clearLocalizationOverlay()

    def setApplyAffine(self, enabled):
        self.applyAffineEnabled = bool(enabled)

        if not self.applyAffineEnabled:
            self._commChannel.clearAllLiveLayerAffines()
            return

        if self.calibration is None:
            self._widget.setApplyChecked(False)
            self.applyAffineEnabled = False
            self._widget.setCalibrationStatus('No calibration loaded')
            return

        self._applyCalibrationToLiveLayers()

    def setShowLocalization(self, enabled):
        self.showLocalization = bool(enabled)
        self._updateOverlays()

    def setShowTransformedPoints(self, enabled):
        self.showTransformedPoints = bool(enabled)
        self._updateOverlays()

    def setShowResidualVectors(self, enabled):
        self.showResidualVectors = bool(enabled)
        self._updateOverlays()

    def clearLocalizationOverlay(self):
        self.showLocalization = False
        self.showTransformedPoints = False
        self.showResidualVectors = False
        self._widget.setVisualizationChecked(
            localization=False,
            transformed=False,
            residuals=False,
        )

        for layer_name in (
            self._referencePointsLayer,
            self._movingPointsLayer,
            self._transformedMovingPointsLayer,
            self._residualVectorsLayer,
        ):
            self._commChannel.removeNapariLayer(layer_name)

    def _applyCalibrationToLiveLayers(self):
        self._commChannel.setAllLiveLayerAffines(self.calibration.matrix_yx_napari)
        self._widget.setCalibrationStatus('Affine applied to all live layers')

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

    def _updateOverlays(self):
        if self.calibration is None:
            self.clearLocalizationOverlay()
            return

        if self.showLocalization:
            self._commChannel.addOrUpdateNapariPointsLayer(
                self._referencePointsLayer,
                self.calibration.reference_points_xy[:, ::-1],
                symbol='ring',
                size=8,
                face_color='green',
                edge_color='green',
                protected=True,
            )
            self._commChannel.addOrUpdateNapariPointsLayer(
                self._movingPointsLayer,
                self.calibration.moving_points_xy[:, ::-1],
                symbol='disc',
                size=6,
                face_color='cyan',
                edge_color='cyan',
                protected=True,
            )
        else:
            self._commChannel.removeNapariLayer(self._referencePointsLayer)
            self._commChannel.removeNapariLayer(self._movingPointsLayer)

        if self.showTransformedPoints:
            self._commChannel.addOrUpdateNapariPointsLayer(
                self._transformedMovingPointsLayer,
                self.calibration.transformed_moving_points_xy[:, ::-1],
                symbol='cross',
                size=8,
                face_color='magenta',
                edge_color='magenta',
                protected=True,
            )
        else:
            self._commChannel.removeNapariLayer(self._transformedMovingPointsLayer)

        if self.showResidualVectors:
            lines = [
                np.stack([p_ref_xy[::-1], p_mov_xy[::-1]], axis=0)
                for p_ref_xy, p_mov_xy in zip(
                    self.calibration.reference_points_xy,
                    self.calibration.transformed_moving_points_xy,
                )
            ]
            self._commChannel.addOrUpdateNapariShapesLayer(
                self._residualVectorsLayer,
                lines,
                shape_type='line',
                edge_color='yellow',
                edge_width=1,
                protected=True,
            )
        else:
            self._commChannel.removeNapariLayer(self._residualVectorsLayer)


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
