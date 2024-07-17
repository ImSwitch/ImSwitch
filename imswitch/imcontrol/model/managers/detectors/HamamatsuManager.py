from imswitch.imcommon.model import initLogger
from .DetectorManager import (
    DetectorManager, DetectorNumberParameter, DetectorListParameter
)


class HamamatsuManager(DetectorManager):
    """ DetectorManager that deals with the Hamamatsu parameters and frame
    extraction for a Hamamatsu camera.

    Manager properties:

    - ``cameraListIndex`` -- the camera's index in the Hamamatsu camera list
      (list indexing starts at 0); set this to an invalid value, e.g. the
      string "mock" to load a mocker
    - ``hamamatsu`` -- dictionary of DCAM API properties to pass to the driver
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        self._camera = self._getCameraObj(detectorInfo.managerProperties['cameraListIndex'])
        self._binning = 1

        for propertyName, propertyValue in detectorInfo.managerProperties['hamamatsu'].items():
            self._camera.setPropertyValue(propertyName, propertyValue)

        fullShape = (self._camera.getPropertyValue('image_width')[0],
                     self._camera.getPropertyValue('image_height')[0])

        model = self._camera.camera_model.decode('utf-8')

        # Prepare parameters
        parameters = {
            'Set exposure time': DetectorNumberParameter(group='Timings', value=0,
                                                         valueUnits='s', editable=True),
            'Real exposure time': DetectorNumberParameter(group='Timings', value=0,
                                                          valueUnits='s', editable=False),
            'Internal frame interval': DetectorNumberParameter(group='Timings', value=0,
                                                               valueUnits='s', editable=False),
            'Readout time': DetectorNumberParameter(group='Timings', value=0,
                                                    valueUnits='s', editable=False),
            'Internal frame rate': DetectorNumberParameter(group='Timings', value=0,
                                                           valueUnits='fps', editable=False),
            'Trigger source': DetectorListParameter(group='Acquisition mode',
                                                    value='Internal trigger',
                                                    options=['Internal trigger',
                                                             'External "start-trigger"',
                                                             'External "frame-trigger"'],
                                                    editable=True),
            'Camera pixel size': DetectorNumberParameter(group='Miscellaneous', value=1.0,
                                                         valueUnits='µm', editable=True)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1, 2, 4],
                         model=model, parameters=parameters, croppable=True)
        self._updatePropertiesFromCamera()
        super().setParameter('Set exposure time', self.parameters['Real exposure time'].value)

    @property
    def pixelSizeUm(self):
        umxpx = self.parameters['Camera pixel size'].value
        return [1, umxpx, umxpx]

    def getLatestFrame(self, is_save=True):
        return self._camera.getLast()

    def getChunk(self):
        return self._camera.getFrames()[0]

    def flushBuffers(self):
        self._camera.updateIndices()

    def crop(self, hpos, vpos, hsize, vsize):
        """Method to crop the frame read out by the camera. """

        def cropAction():
            self._camera.setPropertyValue('subarray_vpos', 0)
            self._camera.setPropertyValue('subarray_hpos', 0)
            self._camera.setPropertyValue('subarray_vsize', self.fullShape[1])
            self._camera.setPropertyValue('subarray_hsize', self.fullShape[0])

            if (hsize, vsize) != self.fullShape:
                self._camera.setPropertyValue('subarray_vsize', vsize)
                self._camera.setPropertyValue('subarray_hsize', hsize)
                self._camera.setPropertyValue('subarray_vpos', vpos)
                self._camera.setPropertyValue('subarray_hpos', hpos)

        self._performSafeCameraAction(cropAction)

        # This should be the only place where self.frameStart is changed
        self._frameStart = (hpos, vpos)
        # Only place self.shapes is changed
        self._shape = (hsize, vsize)

    def setBinning(self, binning):
        super().setBinning(binning)

        binstring = f'{binning}x{binning}'
        coded = binstring.encode('ascii')

        self._performSafeCameraAction(
            lambda: self._camera.setPropertyValue('binning', coded)
        )

    def setParameter(self, name, value):
        super().setParameter(name, value)

        if name == 'Set exposure time':
            self._setExposure(value)
            self._updatePropertiesFromCamera()
        elif name == 'Trigger source':
            self._setTriggerSource(value)

        return self.parameters

    def startAcquisition(self):
        self._camera.startAcquisition()

    def stopAcquisition(self):
        self._camera.stopAcquisition()

    def _setExposure(self, time):
        self._camera.setPropertyValue('exposure_time', time)

    def _setTriggerSource(self, source):
        if source == 'Internal trigger':
            self._performSafeCameraAction(
                lambda: self._camera.setPropertyValue('trigger_source', 1)
            )

        elif source == 'External "start-trigger"':
            self._performSafeCameraAction(
                lambda: self._camera.setPropertyValue('trigger_source', 2)
            )
            self._performSafeCameraAction(
                lambda: self._camera.setPropertyValue('trigger_mode', 6)
            )

        elif source == 'External "frame-trigger"':
            self._performSafeCameraAction(
                lambda: self._camera.setPropertyValue('trigger_source', 2)
            )
            self._performSafeCameraAction(
                lambda: self._camera.setPropertyValue('trigger_mode', 1)
            )
        else:
            raise ValueError(f'Invalid trigger source "{source}"')

    def _performSafeCameraAction(self, function):
        """ This method is used to change those camera properties that need
        the camera to be idle to be able to be adjusted.
        """
        try:
            function()
        except Exception:
            self.stopAcquisition()
            function()
            self.startAcquisition()

    def _updatePropertiesFromCamera(self):
        self.setParameter('Real exposure time', self._camera.getPropertyValue('exposure_time')[0])
        self.setParameter('Internal frame interval',
                          self._camera.getPropertyValue('internal_frame_interval')[0])
        self.setParameter('Readout time', self._camera.getPropertyValue('timing_readout_time')[0])
        self.setParameter('Internal frame rate',
                          self._camera.getPropertyValue('internal_frame_rate')[0])

        triggerSource = self._camera.getPropertyValue('trigger_source')
        if triggerSource == 1:
            self.setParameter('Trigger source', 'Internal trigger')
        else:
            triggerMode = self._camera.getPropertyValue('trigger_mode')
            if triggerSource == 2 and triggerMode == 6:
                self.setParameter('Trigger source', 'External "start-trigger"')
            elif triggerSource == 2 and triggerMode == 1:
                self.setParameter('Trigger source', 'External "frame-trigger"')

    def _getCameraObj(self, cameraId):
        try:
            from imswitch.imcontrol.model.interfaces import HamamatsuCameraMR
            self.__logger.debug(f'Trying to initialize Hamamatsu camera {cameraId}')
            camera = HamamatsuCameraMR(cameraId)
        except Exception:
            self.__logger.warning(f'Failed to initialize Hamamatsu camera {cameraId},'
                                  f' loading mocker')
            from imswitch.imcontrol.model.interfaces import MockHamamatsu
            camera = MockHamamatsu()

        self.__logger.info(f'Initialized camera, model: {camera.camera_model}')
        return camera


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
