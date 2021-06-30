import numpy as np

from .DetectorManager import (
    DetectorManager, DetectorNumberParameter, DetectorListParameter
)

class PhotometricsManager(DetectorManager):
    """ DetectorManager that deals with the Hamamatsu parameters and frame
    extraction for a Hamamatsu camera.

    Available manager properties:
    * cameraListIndex -- the camera's index in the Hamamatsu camera list (list indexing starts at
                         0); set this to an invalid value, e.g. the string "mock" to load a mocker
    * hamamatsu -- dictionary of DCAM API properties
    """

    def __init__(self, detectorInfo, name, **_kwargs):
        self._camera = getCameraObj(detectorInfo.managerProperties['cameraListIndex'])
        self._binning = 1

        #for propertyName, propertyValue in detectorInfo.managerProperties['hamamatsu'].items():
        #    self._camera.setParam( propertyName, propertyValue)

        fullShape = self._camera.sensor_size

        model = self._camera.name
        self.scanLineTime = self._camera.scan_line_time
        self.__acquisition = False
        # Prepare parameters
        parameters = {
            'Set exposure time': DetectorNumberParameter(group='Timings', value=0,
                                                         valueUnits='ms', editable=True),
            'Real exposure time': DetectorNumberParameter(group='Timings', value=0,
                                                          valueUnits='ms', editable=False),
            'Readout time' : DetectorNumberParameter(group='Timings', value=0,
                                                          valueUnits='ms', editable=False),
            'Trigger source': DetectorListParameter(group='Acquisition mode',
                                                    value='Internal trigger',
                                                    options=['Internal trigger',
                                                             'External "start-trigger"',
                                                             'External "frame-trigger"'], editable=True),
            'Readout port': DetectorListParameter(group='ports',
                                                    value='Sensitivity',
                                                    options=['Sensitivity',
                                                             'Speed',
                                                             'Dynamic range'], editable=True),
            'Camera pixel size': DetectorNumberParameter(group='Miscellaneous', value=0.1,
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
        if not status == "READOUT_NOT_ACTIVE":
            im = np.array(self._camera.poll_frame()[0]['pixel_data'])
            print('OK')
            frames.append(im)
        return frames

    def flushBuffers(self):
        pass

    def crop(self, hpos, vpos, hsize, vsize):
        """Method to crop the frame read out by the camera. """
        roi = (hpos, hpos+hsize, vpos, vpos+vsize)
        def cropAction():
            self._camera.roi = roi
        self._performSafeCameraAction(cropAction)
        # This should be the only place where self.frameStart is changed
        self._frameStart = (hpos, vpos)
        # Only place self.shapes is changed
        self._shape = (hsize, vsize)
        self.setParameter('Readout time', self.__scanLineTime*vsize/1e6)

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
        print("Change trigger source")
        def triggerAction():
            self._camera.exp_mode = trigger_value
        if source == 'Internal trigger':
            trigger_value = 1792
            self._performSafeCameraAction(triggerAction)

        elif source == 'External "start-trigger"':
            trigger_value = 2304
            self._performSafeCameraAction(triggerAction)

        elif source == 'External "frame-trigger"':
            trigger_value = 2048
            self._performSafeCameraAction(triggerAction)
        else:
            raise ValueError(f'Invalid trigger source "{source}"')

    def _setReadoutPort(self, port):
        print("Change readout port")
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
        self.setParameter('Readout time', self.__scanLineTime*self._shape[0]/1e6)
    
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
                
def getCameraObj(cameraId):
    try:
        from pyvcam import pvc
        from pyvcam.camera import Camera

        pvc.init_pvcam()
        print('Trying to import camera', cameraId)
        camera = next(Camera.detect_camera())
        camera.open()
        print('Initialized Hamamatsu Camera Object, model: ', camera.name)
        return camera
    except:
        print('Initializing Mock Hamamatsu')
        from imswitch.imcontrol.model.interfaces import MockHamamatsu
        return MockHamamatsu()

# Copyright (C) 2020, 2021 TestaLab
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

