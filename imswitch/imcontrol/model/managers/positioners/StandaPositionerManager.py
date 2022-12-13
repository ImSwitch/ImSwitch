from .PositionerManager import PositionerManager
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.interfaces.standa_linear_positioner import get_linear_positioner

class StandaPositionerManager(PositionerManager):

    def __init__(self, positionerInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        if len(positionerInfo.axes) != 1:
            raise RuntimeError(f'{self.__class__.__name__} only supports one axis,'
                               f' {len(positionerInfo.axes)} provided.')

        self._speed = positionerInfo.managerProperties["initialSpeed"]
        self._positioner = get_linear_positioner(positionerInfo.axes[0])
        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self.__logger.debug(f'Initializing {positionerInfo.axes[0]} ')

    def move(self, dist, axis):
        self._positioner.shift_on(dist)
        self.setPosition(self._position[self.axes[0]] + dist, axis)

    def setPosition(self, position, axis):
        self._position[self.axes[0]] = position