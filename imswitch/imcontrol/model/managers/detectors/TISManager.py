import numpy as np

from imswitch.imcommon.model import initLogger
from .DetectorManager import (
    DetectorManager, DetectorAction,
    DetectorNumberParameter, DetectorListParameter,
    ExposureTimeToUs)


class TISManager(DetectorManager):
    """ DetectorManager that deals with TheImagingSource cameras and the
    parameters for frame extraction from them.

    Manager properties:

    - ``cameraListIndex`` -- the camera's index in the TIS camera list (list
      indexing starts at 0); set this string to an invalid value, e.g. the
      string "mock" to load a mocker
    - ``tis`` -- dictionary of TIS camera properties
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        self._camera = self._getTISObj(
                            detectorInfo.managerProperties['cameraListIndex'])

        self._running = False
        self._adjustingParameters = False

        for propertyName, propertyValue in detectorInfo.managerProperties['tis'].items():
            self._camera.setPropertyValue(propertyName, propertyValue)

        fullShape = (self._camera.getPropertyValue('image_width'),
                     self._camera.getPropertyValue('image_height'))

        self.crop(hpos=0, vpos=0, hsize=fullShape[0], vsize=fullShape[1])

        # Prepare parameters
        parameters = {
            'exposure': DetectorNumberParameter(group='Misc',
                                                value=100,
                                                valueUnits='ms',
                                                editable=True),

            'gain': DetectorNumberParameter(group='Misc',
                                            value=1,
                                            valueUnits='arb.u.',
                                            editable=True),

            'brightness': DetectorNumberParameter(group='Misc',
                                                  value=1,
                                                  valueUnits='arb.u.',
                                                  editable=True),

            'video_format': DetectorListParameter(
                                group='Misc',
                                value='Y16 (320x240)',
                                options=self._camera.get_video_formats(),
                                editable=True),
        }

        # Prepare actions
        actions = {
            'More properties': DetectorAction(
                                    group='Misc',
                                    func=self._camera.openPropertiesGUI),

            'Device selection': DetectorAction(
                                    group='Misc',
                                    func=self._camera.openDevSelectionGUI),
        }

        super().__init__(detectorInfo, name, fullShape=fullShape,
                         supportedBinnings=[1],
                         model=self._camera.model, parameters=parameters,
                         actions=actions, croppable=True)

    @property
    def scale(self):
        return [1, 1]

    def getExposure(self) -> int:
        """ Get camera exposure time in microseconds. This
        manager uses milliseconds as the unit for exposure time.

        Returns:
            int: exposure time in microseconds
        """
        exposure = self._camera.getPropertyValue('exposure')
        return ExposureTimeToUs.convert(exposure, 'ms')

    def getLatestFrame(self, is_save=False):
        """
        Retrieves the latest frame from the camera.

        Args:
            is_save (bool, optional): Indicates whether to save the frame.
                Defaults to False.

        Returns:
            numpy.ndarray: The latest frame captured by the camera.
        """
        if not self._adjustingParameters:
            self.__image = self._camera.grabFrame()
        return self.__image

    def setParameter(self, name, value):
        """Sets a parameter value and returns the value.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""
        super().setParameter(name, value)

        if name not in self._DetectorManager__parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        value = self._camera.setPropertyValue(name, value)
        return value

    def getParameter(self, name):
        """Gets a parameter value and returns the value.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""

        if name not in self._parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        value = self._camera.getPropertyValue(name)
        return value

    def setBinning(self, binning):
        super().setBinning(binning)

    def getChunk(self):
        return self._camera.grabFrame()[np.newaxis, :, :]

    def flushBuffers(self):
        pass

    def startAcquisition(self):
        if not self._running:
            self._camera.start_live()
            self._running = True

    def stopAcquisition(self):
        if self._running:
            self._running = False
            self._camera.suspend_live()

    def stopAcquisitionForROIChange(self):
        self._running = False
        self._camera.stop_live()

    @property
    def pixelSizeUm(self):
        return [1, 1, 1]

    def crop(self, hpos, vpos, hsize, vsize):
        def cropAction():
            self._camera.setROI(hpos, vpos, hsize, vsize)

        self._performSafeCameraAction(cropAction)
        # TODO: unsure if frameStart is needed? Try without.
        # This should be the only place where self.frameStart is changed
        self._frameStart = (hpos, vpos)
        # Only place self.shapes is changed
        self._shape = (hsize, vsize)

    def _performSafeCameraAction(self, function):
        """ This method is used to change those camera properties that need
        the camera to be idle to be able to be adjusted.
        """
        self._adjustingParameters = True
        wasrunning = self._running
        self.stopAcquisitionForROIChange()
        function()
        if wasrunning:
            self.startAcquisition()
        self._adjustingParameters = False

    def openPropertiesDialog(self):
        self._camera.openPropertiesGUI()

    def _getTISObj(self, cameraId):
        try:
            from imswitch.imcontrol.model.interfaces.tiscamera import CameraTIS
            camera = CameraTIS(cameraId)
        except Exception:
            self.__logger.warning(
                f'Failed to initialize TIS camera {cameraId}, loading mocker')
            from imswitch.imcontrol.model.interfaces.tiscamera_mock import MockCameraTIS
            camera = MockCameraTIS()

        self.__logger.info(f'Initialized camera, model: {camera.model}')
        return camera

    def close(self):
        self.__logger.info(
                f'Shutting down camera, model: {self._camera.model}')
        pass


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
