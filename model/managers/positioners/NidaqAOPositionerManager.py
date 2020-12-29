from .PositionerManager import PositionerManager


class NidaqAOPositionerManager(PositionerManager):
    def __init__(self, positionerInfo, name, **kwargs):
        self._nidaqManager = kwargs['nidaqManager']
        self._conversionFactor = positionerInfo.managerProperties['conversionFactor']
        self._minVolt = positionerInfo.managerProperties['minVolt']
        self._maxVolt = positionerInfo.managerProperties['maxVolt']
        super().__init__(name, initialPosition=0)

    def move(self, dist):
        return self.setPosition(self._position + dist)

    def setPosition(self, position):
        self._position = position
        self._nidaqManager.setAnalog(target=self._name,
                                     voltage=position / self._conversionFactor,
                                     min_val=self._minVolt,
                                     max_val=self._maxVolt)
        return position
