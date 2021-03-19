# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 14:00:00 2021

@author: jonatanalvelid
"""

from .DetectorManager import (
    DetectorManager, DetectorNumberParameter, DetectorListParameter
)


class TISManager(DetectorManager):

    def __init__(self, webcamInfo, name, **_kwargs):
        self._camera = getTISObj(webcamInfo.managerProperties['cameraListIndex'])

        model = self._camera.model

        for propertyName, propertyValue in webcamInfo.managerProperties['tis'].items():
            self._camera.setPropertyValue(propertyName, propertyValue)

        fullShape = (self._camera.getPropertyValue('image_height'),
                     self._camera.getPropertyValue('image_width'))

        # Prepare parameters
        parameters = {
            'Exposure': DetectorNumberParameter(group='Misc', value=0, valueUnits='ms', editable=False),
            'Gain': DetectorNumberParameter(group='Misc', value=0, valueUnits='arb.u.', editable=False),
            'Brightness': DetectorNumberParameter(group='Misc', value=0, valueUnits='arb.u.', editable=False),
            'Image width': DetectorNumberParameter(group='Misc', value=0, valueUnits='arb.u.', editable=False),
            'Image height': DetectorNumberParameter(group='Misc', value=0, valueUnits='arb.u.', editable=False),
        }

        super().__init__(name, fullShape, [1], model, parameters)

    def getLatestFrame(self):
        return self._camera.grabFrame()

    def setParameter(self, name, value):
        """Sets a parameter value and returns the value.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""

        if name not in self.__parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        value = self.__mode.setPropertyValue(name, value)
        return value

    def getParameter(self, name):
        """Gets a parameter value and returns the value.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""

        if name not in self.__parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        value = self.__mode.getPropertyValue(name)
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
    
    def pixelSize(self):
        pass

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def show_dialog(self):
        "Manager: open camera settings dialog mock."
        pass

def getTISObj(cameraId):
    try:
        from model.interfaces.tiscamera import CameraTIS
        print('Trying to import camera', cameraId)
        camera = CameraTIS(cameraId)
        print('Initialized TIS Camera Object, model: ', camera.model)
        return camera
    except (OSError, IndexError):
        print('Initializing Mock TIS')
        from model.interfaces.mockers import MockCameraTIS
        return MockCameraTIS()
