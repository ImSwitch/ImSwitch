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
        })
        # , initialSpeed={
        #             axis: sp for axis, sp in zip(positionerInfo.axes,
        #                                                positionerInfo.managerProperties["initialSpeed"])
        #
        #         }
        self.__logger.debug(f'Initializing {positionerInfo.axes} ')
        self.setSpeed(self._speed)

    def setSpeed(self, speed, axis = "XYZ"):
        self.__logger.debug(f"Setting stage speed {speed}. Previous speed {self.speed}")
        if axis == "XYZ":
            self.speed = speed
        elif axis == "XY":
            self.speed["X"] = speed[0]
            self.speed["Y"] = speed[1]
        elif axis == "X" or axis == "Y" or  axis == "Z":
            self.speed[axis] = speed
        else:
            raise ValueError("Invalid axis.")
        self._positioner.set_speed(self.speed)


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
    # TODO: duplicated, refactor with ImSwitch camel style?
    def getPosition(self):
        return self._position
    def get_position(self):
        return self._positioner.get_position()

    # TODO: adapt to new Positioner signature (from ESP32StageManager):
    #  move(self, value=0, axis="X", speed=None, is_absolute=False, is_blocking=False, timeout=np.inf):
    def move(self, dist, axis, speed=None, is_blocking=False, is_absolute=False):
        if speed is not None:
            self.setSpeed(speed,axis)

        current_position = self._positioner.get_position()
        if axis == "XYZ":
            self._positioner.shift_on(dist)
            if is_blocking:
                self._positioner.wait_for_stop()
            self.setPosition(current_position[0]+dist[0], "X")
            self.setPosition(current_position[1]+dist[1], "Y")
            self.setPosition(current_position[2]+dist[2], "Z")
        elif axis == "XY":
            self._positioner.x_axis.shift_on(dist[0])
            self._positioner.y_axis.shift_on(dist[1])
            if is_blocking:
                self._positioner.wait_for_stop()
            self.setPosition(current_position[0]+dist[0], "X")
            self.setPosition(current_position[1]+dist[1], "Y")
        # With the widget it uses just one axis at a time:
        elif "Z" == axis:
            if is_absolute:
                self._positioner.z_axis.move_to(dist)
                if is_blocking:
                    self._positioner.wait_for_stop()
                self.setPosition(dist, "Z")
                # self._position[axis] = value
            else:
                self._positioner.z_axis.shift_on(dist)
                if is_blocking:
                    self._positioner.wait_for_stop()
                self.setPosition(current_position[2] + dist, "Z")
                # self._position[axis] = self._position[axis] + value
        elif "X" == axis:
            self._positioner.x_axis.shift_on(dist)
            if is_blocking:
                self._positioner.wait_for_stop()
            self.setPosition(current_position[0]+dist, "X")
        elif "Y" == axis:
            self._positioner.y_axis.shift_on(dist)
            if is_blocking:
                self._positioner.wait_for_stop()
            self.setPosition(current_position[1]+dist, "Y")
        else:
            raise ValueError("Invalid axis.")
        return

    def setPosition(self, position, axis):
        self._position[axis] = position

    @property
    def speed(self):
        return self._speed
    @speed.setter
    def speed(self, value):
        self._speed = value

    @property
    def position(self):
        return {
            axis: pos for pos, axis in zip(self._positioner.get_position(), self.axes)
        }



