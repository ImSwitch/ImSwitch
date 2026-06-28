from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.interfaces.LeicaDMIHardware import createLeicaDMIHardware

from .PositionerManager import PositionerManager


class LeicaDMIZPositionerManager(PositionerManager):
    """Positioner adapter exposing Leica DMI Z through the Positioner API."""

    def __init__(self, positionerInfo, name, *args, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        if len(positionerInfo.axes) != 1:
            raise RuntimeError(
                f"{self.__class__.__name__} only supports one axis, "
                f"{len(positionerInfo.axes)} provided."
            )

        axis = positionerInfo.axes[0]
        super().__init__(positionerInfo, name, initialPosition={axis: 0})

        self._axis = axis
        self._hardware = None
        self._connectionError = None

        managerProperties = positionerInfo.managerProperties or {}
        rs232DeviceName = managerProperties.get("rs232device")
        if not rs232DeviceName:
            self._connectionError = "Missing managerProperties.rs232device."
            self.__logger.error(
                "Leica DMI Z positioner unavailable: missing "
                "managerProperties.rs232device."
            )
            return

        try:
            rs232Manager = lowLevelManagers["rs232sManager"][rs232DeviceName]
        except Exception as exc:
            self._connectionError = str(exc)
            self.__logger.error(
                "Leica DMI Z positioner unavailable: failed to access RS232 "
                f"device {rs232DeviceName!r}: {exc}"
            )
            return

        self._hardware = createLeicaDMIHardware(
            rs232Manager,
            managerProperties=managerProperties,
            logger=self.__logger,
        )

        if self._hardware is None:
            self._connectionError = "Leica DMI hardware interface unavailable."
            self.__logger.warning(
                "Leica DMI Z positioner unavailable. See Leica DMI hardware "
                "log entry above."
            )
            return

        if not self._hardware.has_z_position_um():
            self._connectionError = "Leica DMI Z micrometer conversion is unavailable."
            self.__logger.warning(
                "Leica DMI Z positioner unavailable: no calibration LUT is "
                "configured and command 71042 did not return a valid Z "
                "conversion factor."
            )
            return

        self.updatePosition()

    @property
    def isAvailable(self) -> bool:
        return bool(
            self._hardware is not None
            and self._hardware.isConnected()
            and self._hardware.has_z_position_um()
        )

    @property
    def resetOnClose(self) -> bool:
        return False

    @property
    def connectionError(self):
        if self._hardware is not None:
            return getattr(self._hardware, "connectionError", None)
        return self._connectionError

    def move(self, dist, axis=None):
        self._check_axis(axis)
        if not self.isAvailable:
            return self._position

        return self._call_hardware("move_z_relative_um", dist)

    def setPosition(self, position, axis=None):
        self._check_axis(axis)
        if not self.isAvailable:
            return self._position

        return self._call_hardware("set_z_position_um", position)

    def updatePosition(self):
        if not self.isAvailable:
            return self._position

        position = self._call_hardware(
            "get_z_position_um",
            updatePosition=False,
        )
        if position is not None:
            self._position[self._axis] = position
        return self._position

    def get_abs(self, axis=None):
        self._check_axis(axis)
        self.updatePosition()
        return self._position[self._axis]

    def get_pos_nm(self):
        if not self.isAvailable:
            return None
        return self._call_hardware("get_pos_nm", updatePosition=False)

    def set_pos_nm(self, pos_nm):
        if not self.isAvailable:
            return self._position

        result = self._call_hardware(
            "set_pos_nm",
            pos_nm,
            updatePosition=False,
        )
        self.updatePosition()
        return result

    def _call_hardware(self, methodName, *args, updatePosition=True):
        method = getattr(self._hardware, methodName)
        try:
            result = method(*args)
        except Exception as exc:
            self._connectionError = str(exc)
            self.__logger.warning(f"Leica DMI Z positioner command {methodName} failed: {exc}")
            return self._position if updatePosition else None

        if updatePosition:
            if result is not None:
                self._position[self._axis] = result
            return self._position

        return result

    def _check_axis(self, axis):
        if axis in (None, self._axis, 0):
            return

        raise ValueError(
            f"{self.__class__.__name__} only controls axis {self._axis}, "
            f"got {axis}."
        )
