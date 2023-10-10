import numpy as np

from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter, DetectorListParameter, DetectorBooleanParameter


class VirtualCameraManager(DetectorManager):
    """ DetectorManager that deals with TheImagingSource cameras and the
    parameters for frame extraction from them.

    Manager properties:

    - ``cameraListIndex`` -- the camera's index in the Allied Vision camera list (list
      indexing starts at 0); set this string to an invalid value, e.g. the
      string "mock" to load a mocker
    - ``av`` -- dictionary of Allied Vision camera properties
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self.detectorInfo = detectorInfo
        try:
            self.VirtualMicroscope = _lowLevelManagers["rs232sManager"]["VirtualMicroscope"]
        except:
            return
        
        # assign the camera from the Virtual Microscope
        self._camera = self.VirtualMicroscope._camera

        # get the pixel size from the camera
        fullShape = (self._camera.SensorWidth,
                self._camera.SensorHeight)
        pixelSize = self._camera.PixelSize
        model = self._camera.model
        self._running = True

        # Prepare parameters
        parameters = {
            'exposure': DetectorNumberParameter(group='Misc', value=1, valueUnits='ms',
                                                editable=True),
            'gain': DetectorNumberParameter(group='Misc', value=5, valueUnits='arb.u.',
                                            editable=True),
            'blacklevel': DetectorNumberParameter(group='Misc', value=0, valueUnits='arb.u.',
                                            editable=True),
            'binning': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.',
                                               editable=True),
            'image_width': DetectorNumberParameter(group='Misc', value=fullShape[0], valueUnits='arb.u.',
                        editable=False),
            'image_height': DetectorNumberParameter(group='Misc', value=fullShape[1], valueUnits='arb.u.',
                        editable=False),
            'frame_rate': DetectorNumberParameter(group='Misc', value=-1, valueUnits='fps',
                                    editable=True),
            'flat_fielding': DetectorBooleanParameter(group='Misc', value=True, editable=True),            
            'binning': DetectorNumberParameter(group="Misc", value=1, valueUnits="arb.u.", editable=True),
            'trigger_source': DetectorListParameter(group='Acquisition mode',
                            value='Continous',
                            options=['Continous',
                                        'Internal trigger',
                                        'External trigger'],
                            editable=True),
            'Camera pixel size': DetectorNumberParameter(group='Miscellaneous', value=pixelSize,
                                                valueUnits='µm', editable=True)
            }

        # reading parameters from disk and write them to camrea
        for propertyName, propertyValue in detectorInfo.managerProperties['virtcam'].items():
            self._camera.setPropertyValue(propertyName, propertyValue)
            parameters[propertyName].value = propertyValue

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, actions=None, croppable=False)


    def _updatePropertiesFromCamera(self):
        self.setParameter('Real exposure time', self._camera.getPropertyValue('exposure_time')[0])
        self.setParameter('Internal frame interval',
                          self._camera.getPropertyValue('internal_frame_interval')[0])
        self.setParameter('Binning', self._camera.getPropertyValue('binning')[0])
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

    def getLatestFrame(self, is_save=False):
        frame = self._camera.getLast()
        return frame

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

    def getChunk(self):
        try:
            return self._camera.getLastChunk()
        except:
            return None

    def startAcquisition(self, liveView=False):
        pass 
    
    def stopAcquisition(self):
        pass
    
    def stopAcquisitionForROIChange(self):
        pass
    def finalize(self) -> None:
        super().finalize()
        self.__logger.debug('Safely disconnecting the camera...')

    @property
    def pixelSizeUm(self):
        umxpx = self.parameters['Camera pixel size'].value
        return [1, umxpx, umxpx]

    def setPixelSizeUm(self, pixelSizeUm):
        self.parameters['Camera pixel size'].value = pixelSizeUm

    def _performSafeCameraAction(self, function):
        pass 
    
    def openPropertiesDialog(self):
        self._camera.openPropertiesGUI()

    def closeEvent(self):
        pass
        
    def flushBuffers(self):
        pass
    
    def crop(self, hpos, vpos, hsize, vsize):
        pass

# Copyright (C) ImSwitch developers 2021
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
