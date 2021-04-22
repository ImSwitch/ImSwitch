"""
Created on Fri Jan 08 14:00:00 2021

@author: jonatanalvelid
"""

from .DetectorManager import DetectorManager, DetectorNumberParameter


class TISManager(DetectorManager):
    def __init__(self, detectorInfo, name, **_kwargs):
        self._camera = getTISObj(detectorInfo.managerProperties['cameraListIndex'])

        model = self._camera.model

        for propertyName, propertyValue in detectorInfo.managerProperties['tis'].items():
            self._camera.setPropertyValue(propertyName, propertyValue)

        #fullShape = (self._camera.getPropertyValue('image_height')[0],
        #             self._camera.getPropertyValue('image_width')[0])

        fullShape = (self._camera.getPropertyValue('image_width'),
                     self._camera.getPropertyValue('image_height'))

        # Prepare parameters
        parameters = {
            'exposure': DetectorNumberParameter(group='Misc', value=100, valueUnits='ms', editable=True),
            'gain': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.', editable=True),
            'brightness': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.', editable=True),
            #'image_width': DetectorNumberParameter(group='Misc', value=0, valueUnits='arb.u.', editable=False),
            #'image_height': DetectorNumberParameter(group='Misc', value=0, valueUnits='arb.u.', editable=False)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1, 2],
                         model=model, parameters=parameters, croppable=False)

    def getLatestFrame(self):
        return self._camera.grabFrame()

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
        pass

    def flushBuffers(self):
        pass

    def startAcquisition(self):
        pass

    def stopAcquisition(self):
        pass
    
    @property
    def pixelSizeUm(self):
        return [1, 1, 1]

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def openPropertiesGUI(self):
        "Manager: open camera settings dialog."
        self._camera.openPropertiesGUI()

        
def getTISObj(cameraId):
    try:
        from imswitch.imcontrol.model.interfaces.tiscamera import CameraTIS
        print('Trying to import camera', cameraId)
        camera = CameraTIS(cameraId)
        print('Initialized TIS Camera Object, model: ', camera.model)
        return camera
    except (OSError, IndexError):
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
