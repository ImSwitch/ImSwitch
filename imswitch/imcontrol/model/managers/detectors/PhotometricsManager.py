import numpy as np

from imswitch.imcommon.model import initLogger
from .DetectorManager import (
    DetectorManager, DetectorNumberParameter, DetectorListParameter
)


class PhotometricsManager(DetectorManager):
    """ DetectorManager that deals with frame extraction for a Photometrics camera.

    Manager properties:

    - ``cameraListIndex`` -- the camera's index in the Photometrics camera list
      (list indexing starts at 0)
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__chunkFrameSize = 1
        self.__logger = initLogger(self, instanceName=name)

        self._camera = self._getCameraObj(detectorInfo.managerProperties['cameraListIndex'])
        self._binning = 1

        fullShape = self._camera.sensor_size

        model = self._camera.name
        self.scanLineTime = self._camera.scan_line_time
        self.__acquisition = False
        # Prepare parameters
        parameters = {
            'Set exposure time': DetectorNumberParameter(group='Timings', value=1,
                                                         valueUnits='ms', editable=True),
            'Real exposure time': DetectorNumberParameter(group='Timings', value=0,
                                                          valueUnits='ms', editable=False),
            'Readout time': DetectorNumberParameter(group='Timings', value=0,
                                                    valueUnits='ms', editable=False),
            'Trigger source': DetectorListParameter(group='Acquisition mode',
                                                    value='Internal trigger',
                                                    options=['Internal trigger',
                                                             'External "start-trigger"',
                                                             'External "frame-trigger"'],
                                                    editable=True),
            'Readout port': DetectorListParameter(group='ports',
                                                  value='Sensitivity',
                                                  options=['Sensitivity',
                                                           'Speed',
                                                           'Dynamic range'], editable=True),
            'Camera pixel size': DetectorNumberParameter(group='Miscellaneous', value=0.1,
                                                         valueUnits='µm', editable=True),
            'Number of frames per chunk': DetectorNumberParameter(group='Recording', value=self.__chunkFrameSize,
                                                         valueUnits='frames', editable=True)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1, 2, 4],
                         model=model, parameters=parameters, croppable=True)
        self._updatePropertiesFromCamera()

        super().setParameter('Set exposure time', self.parameters['Real exposure time'].value)
        if 'Photometrics' in detectorInfo.managerProperties:
            # Update the user-specific settings
            for key, value in detectorInfo.managerProperties['Photometrics'].items():
                self.__logger.info(f'Updating user-supplied value for {key}')
                self.setParameter(key, value)
            self._updatePropertiesFromCamera()
    @property
    def pixelSizeUm(self):
        umxpx = self.parameters['Camera pixel size'].value
        return [1, umxpx, umxpx]

    def getExposure(self) -> int:
        return self._camera.exp_time

    def getLatestFrame(self):
        try:
            status = self._camera.check_frame_status()
            if status == "READOUT_NOT_ACTIVE":
                return self.image
            else:
                return np.array(self._camera.poll_frame()[0]['pixel_data'])
        except RuntimeError:
            return self.image

    def getChunk(self):
        frames = []
        status = self._camera.check_frame_status()
        try:
            if not status == "READOUT_NOT_ACTIVE":
                for _ in range(self.__chunkFrameSize):
                    im = np.array(self._camera.poll_frame()[0]['pixel_data'])
                    frames.append(im)
        except RuntimeError:
            pass
        return frames

    def flushBuffers(self):
        pass

    def crop(self, hpos, vpos, hsize, vsize):
        """Method to crop the frame read out by the camera. """
        roi = (hpos, hpos + hsize, vpos, vpos + vsize)

        def cropAction():
            self._camera.roi = roi

        self._performSafeCameraAction(cropAction)
        # This should be the only place where self.frameStart is changed
        self._frameStart = (hpos, vpos)
        # Only place self.shapes is changed
        self._shape = (hsize, vsize)
        self.setParameter('Readout time', self.__scanLineTime * vsize / 1e6)

    def setBinning(self, binning):
        super().setBinning(binning)

        def binningAction():
            self._camera.binning = binning

        self._performSafeCameraAction(binningAction)

    def setParameter(self, name, value):
        super().setParameter(name, value)

        if name == 'Set exposure time':
            self._setExposure(value)
            self._updatePropertiesFromCamera()
        elif name == 'Trigger source':
            self._setTriggerSource(value)
        elif name == 'Readout port':
            self._setReadoutPort(value)
        elif name == 'Number of frames per chunk':
            self.__chunkFrameSize = int(value)
        return self.parameters

    def startAcquisition(self):
        self.__acquisition = True
        self._camera.start_live()

    def stopAcquisition(self):
        self.__acquisition = False
        self._camera.abort()
        self._camera.finish()

    def _setExposure(self, time):
        self._camera.exp_time = int(time)

    def _setTriggerSource(self, source):
        self.__logger.debug("Change trigger source")

        def triggerAction():
            self._camera.exp_mode = trigger_value

        if source == 'Internal trigger':
            trigger_value = 1792
            self._performSafeCameraAction(triggerAction)

        elif source == 'External "start-trigger"':
            trigger_value = 2048
            self._performSafeCameraAction(triggerAction)

        elif source == 'External "frame-trigger"':
            trigger_value = 2560
            self._performSafeCameraAction(triggerAction)
        else:
            raise ValueError(f'Invalid trigger source "{source}"')

    def _setReadoutPort(self, port):
        self.__logger.debug("Change readout port")

        def portAction():
            self._camera.readout_port = port_value

        def getScanTimeAction():
            self.__scanLineTime = self._camera.scan_line_time

        if port == 'Sensitivity':
            port_value = 0
            self._performSafeCameraAction(portAction)

        elif port == 'Speed':
            port_value = 1
            self._performSafeCameraAction(portAction)

        elif port == 'Dynamic range':
            port_value = 2
            self._performSafeCameraAction(portAction)
        else:
            raise ValueError(f'Invalid readout port "{port}"')
        self._performSafeCameraAction(getScanTimeAction)
        self.setParameter('Readout time', self.__scanLineTime * self._shape[0] / 1e6)

    def _performSafeCameraAction(self, function):
        """ This method is used to change those camera properties that need
        the camera to be idle to be able to be adjusted.
        """
        if self.__acquisition:
            self.stopAcquisition()
            function()
            self.startAcquisition()
        else:
            function()

    def _updatePropertiesFromCamera(self):
        self.setParameter('Real exposure time', self._camera.exp_time)
        triggerSource = self._camera.exp_mode
        if triggerSource == 1792:
            self.setParameter('Trigger source', 'Internal trigger')
        elif triggerSource == 2304:
            self.setParameter('Trigger source', 'External "start-trigger"')
        elif triggerSource == 2048:
            self.setParameter('Trigger source', 'External "frame-trigger"')

        readoutPort = self._camera.readout_port
        if readoutPort == 0:
            self.setParameter('Readout port', 'Sensitivity')
        elif readoutPort == 1:
            self.setParameter('Readout port', 'Speed')
        elif readoutPort == 2:
            self.setParameter('Readout port', 'Dynamic range')

    def finalize(self):
        self._camera.close()

    def _getCameraObj(self, cameraId):
        try:
            from pyvcam import pvc
            from pyvcam.camera import Camera

            pvc.init_pvcam()
            self.__logger.debug(f'Trying to initialize Photometrics camera {cameraId}')
            camera = next(Camera.detect_camera())
            camera.open()
        except Exception:
            self.__logger.warning(f'Failed to initialize Photometrics camera {cameraId},'
                                  f' loading mocker')
            from imswitch.imcontrol.model.interfaces import MockHamamatsu
            camera = MockHamamatsu()

        self.__logger.info(f'Initialized camera, model: {camera.name}')
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
