from .PositionerManager import PositionerManager
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.interfaces.standa_multi_axis_positioner import get_multiaxis_positioner

class StandaStageManager(PositionerManager):

    def __init__(self, positionerInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        if len(positionerInfo.axes) != 3:
            raise RuntimeError(f'{self.__class__.__name__} only supports 3 axes,'
                               f' {len(positionerInfo.axes)} provided.')

        self._positioner = get_multiaxis_positioner(positionerInfo.axes)
        super().__init__(positionerInfo, name, initialPosition={
            axis: pos for pos, axis in zip(self._positioner.get_position(), positionerInfo.axes)
        }, initialSpeed={
            axis: sp for axis, sp in zip(positionerInfo.axes,
                                               positionerInfo.managerProperties["initialSpeed"])

        })
        self.__logger.debug(f'Initializing {positionerInfo.axes[0]} ')
        self.setSpeed(self._speed)

    def setSpeed(self, speed, axis = "XYZ"):
        if axis == "XYZ":
            self.__logger.debug(f"Setting stage speed {speed}. Previous speed {self.speed}")
            self._positioner.set_speed(speed)
            self.speed = speed
        elif axis == "X" or axis == "Y" or  axis == "Z":
            self.speed[axis] = speed
            self._positioner.set_speed(self.speed)
        else:
            raise ValueError("Invalid axis.")
        return

    def home(self):
        self.__logger.debug("Homing stage.")
        self._positioner.home()
        [self.setPosition(d, a) for a,d in zip(self.axes, self.get_position())]
        return

    def zero(self):
        self.__logger.debug("Zeroing stage.")
        self._positioner.zero()
        [self.setPosition(d, a) for a,d in zip(self.axes, self.get_position())]
        return

    def get_position(self):
        return self._positioner.get_position()

    def move(self, dist, axis, is_blocking=True):
        if axis == "XYZ":
            self._positioner.shift_on(dist)
            if is_blocking:
                self._positioner.wait_for_stop()
            new_pos = self._positioner.get_position()
            [self.setPosition(d, a) for a,d in zip(axis, new_pos)]
            return
        if axis == "XY":
            self._positioner.x_axis.shift_on(dist[0])
            self._positioner.y_axis.shift_on(dist[1])
            if is_blocking:
                self._positioner.wait_for_stop()
            x_new, y_new, _ = self._positioner.get_position()
            [self.setPosition(d, a) for a,d in zip(axis, [x_new, y_new])]
            return
        # With the widget it uses just one axis at a time:
        elif "Z" == axis:
            self._positioner.z_axis.shift_on(dist)
            if is_blocking:
                self._positioner.wait_for_stop()
        elif "X" == axis:
            self._positioner.x_axis.shift_on(dist)
            if is_blocking:
                self._positioner.wait_for_stop()
        elif "Y" == axis:
            self._positioner.y_axis.shift_on(dist)
            if is_blocking:
                self._positioner.wait_for_stop()
        else:
            raise ValueError("Invalid axis.")
        new_pos = self._positioner.get_position()
        [self.setPosition(d, a) for a, d in zip("XYZ", new_pos)]
        return

    def setPosition(self, position, axis):
        self._position[axis] = position

    @property
    def speed(self):
        return self._speed
    @speed.setter
    def speed(self, value):
        self._speed = value




