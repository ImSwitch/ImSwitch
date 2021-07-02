from .DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter

import numpy as np


class TISManager(DetectorManager):
    def __init__(self, detectorInfo, name, **_kwargs):
        self._camera = getTISObj(detectorInfo.managerProperties['cameraListIndex'])

        model = self._camera.model
        self._running = False
        self._adjustingParameters = False

        for propertyName, propertyValue in detectorInfo.managerProperties['tis'].items():
            self._camera.setPropertyValue(propertyName, propertyValue)

        fullShape = (self._camera.getPropertyValue('image_width'),
                     self._camera.getPropertyValue('image_height'))

        self.crop(hpos=0, vpos=0, hsize=fullShape[0], vsize=fullShape[1])

        # Prepare parameters
        parameters = {
            'exposure': DetectorNumberParameter(group='Misc', value=100, valueUnits='ms', editable=True),
            'gain': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.', editable=True),
            'brightness': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.', editable=True),
        }

        # Prepare actions
        actions = {
            'More properties': DetectorAction(group='Misc',
                                              func=self._camera.openPropertiesGUI)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, actions=actions, croppable=True)

    def getLatestFrame(self):
        if not self._adjustingParameters:
            self.__image = self._camera.grabFrame()
        return self.__image

    def setParameter(self, name, value):
        """Sets a parameter value and returns the value.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""

        if name not in self._parameters:
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
        return self._camera.grabFrame()[np.newaxis,:,:]

    def flushBuffers(self):
        pass

    def startAcquisition(self):
        if not self._running:
            self._camera.start_live()
            self._running = True
            print('startlive')

    def stopAcquisition(self):
        if self._running:
            self._running = False
            self._camera.suspend_live()
            print('suspendlive')
    
    def stopAcquisitionForROIChange(self):
        self._running = False
        self._camera.stop_live()
        print('stoplive')

    @property
    def pixelSizeUm(self):
        return [1, 1, 1]

    def crop(self, hpos, vpos, hsize, vsize):
        def cropAction():
            #print(f'{self._camera.model}: crop frame to {hsize}x{vsize} at {hpos},{vpos}.')
            self._camera.setROI(hpos, vpos, hsize, vsize)
        
        self._performSafeCameraAction(cropAction)
        #TODO: unsure if frameStart is needed? Try without.
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


def getTISObj(cameraId):
    try:
        from imswitch.imcontrol.model.interfaces.tiscamera import CameraTIS
        print('Trying to import camera', cameraId)
        camera = CameraTIS(cameraId)
        print('Initialized TIS Camera Object, model: ', camera.model)
        return camera
    except:
        print('Initializing Mock TIS')
        from imswitch.imcontrol.model.interfaces.tiscamera_mock import MockCameraTIS
        return MockCameraTIS()


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
