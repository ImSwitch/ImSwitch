from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.interfaces.LeicaDMIHardware import createLeicaDMIHardware


class LeicaDMIStandManager:
    """Stand-facing Leica DMI manager.

    This manager owns stand semantics and delegates serial commands to the
    Leica DMI hardware interface.
    """

    def __init__(self, deviceInfo, *args, **lowLevelManagers):
        self.__logger = initLogger(self)
        self._hardware = None
        self._connectionError = None

        self._cube_slot_to_name = {}
        self._cube_name_to_slot = {}
        self._load_cube_config(deviceInfo)

        managerProperties = getattr(deviceInfo, "managerProperties", None) or {}

        try:
            rs232Manager = lowLevelManagers["rs232sManager"][deviceInfo.rs232device]
        except Exception as exc:
            self._connectionError = str(exc)
            self.__logger.error(
                "Leica DMI stand unavailable: failed to access RS232 device "
                f"{deviceInfo.rs232device!r}: {exc}"
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
                "Leica DMI stand unavailable. See Leica DMI hardware log entry above."
            )

    # ------------------------------------------------------------------
    # Availability and config
    # ------------------------------------------------------------------

    def isConnected(self):
        return bool(self._hardware is not None and self._hardware.isConnected())

    @property
    def isAvailable(self):
        return self.isConnected()

    @property
    def connectionError(self):
        if self._hardware is not None:
            return getattr(self._hardware, "connectionError", None)
        return self._connectionError

    def _load_cube_config(self, deviceInfo):
        try:
            cube_map = (deviceInfo.managerProperties or {}).get("availableCubes", {})
        except Exception:
            cube_map = {}

        parsed = {}
        for slot, name in cube_map.items():
            try:
                parsed[int(slot)] = str(name)
            except Exception:
                self.__logger.warning(
                    f"Ignoring invalid Leica cube config entry: {slot} -> {name}"
                )

        self._cube_slot_to_name = dict(sorted(parsed.items()))
        self._cube_name_to_slot = {
            name: slot for slot, name in self._cube_slot_to_name.items()
        }

    def getAvailableCubes(self):
        return dict(self._cube_slot_to_name)

    # ------------------------------------------------------------------
    # Hardware delegation
    # ------------------------------------------------------------------

    def _call_hardware(self, methodName, *args):
        if self._hardware is None:
            self.__logger.warning(
                f"Cannot run Leica DMI command {methodName}: hardware unavailable."
            )
            return None

        method = getattr(self._hardware, methodName)
        try:
            return method(*args)
        except Exception as exc:
            self._connectionError = str(exc)
            self.__logger.warning(f"Leica DMI command {methodName} failed: {exc}")
            return None

    # ------------------------------------------------------------------
    # Z and legacy positioner-compatible commands
    # ------------------------------------------------------------------

    def move(self, value, *args):
        return self._call_hardware("move", value, *args)

    def setPosition(self, value, *args):
        return self._call_hardware("setPosition", value, *args)

    def move_z_relative_device_units(self, value):
        return self._call_hardware("move_z_relative_device_units", value)

    def set_z_position_device_units(self, value):
        return self._call_hardware("set_z_position_device_units", value)

    def get_z_position_device_units(self):
        return self._call_hardware("get_z_position_device_units")

    def get_pos_nm(self):
        return self._call_hardware("get_pos_nm")

    def set_pos_nm(self, pos_nm):
        return self._call_hardware("set_pos_nm", pos_nm)

    def returnMod(self, reply):
        if self._hardware is None:
            return reply
        return self._call_hardware("returnMod", reply)

    def position(self, *args):
        return self._call_hardware("position", *args)

    def motCorrPos(self, value):
        return self._call_hardware("motCorrPos", value)

    # ------------------------------------------------------------------
    # Stand commands
    # ------------------------------------------------------------------

    def setFLUO(self, *args):
        return self._call_hardware("setFLUO", *args)

    def setCS(self, *args):
        return self._call_hardware("setCS", *args)

    def setILshutter(self, value):
        return self._call_hardware("setILshutter", value)

    def setTLshutter(self, value):
        return self._call_hardware("setTLshutter", value)

    def getIlluminationMode(self):
        return self._call_hardware("getIlluminationMode")

    def getCube(self):
        return self._call_hardware("getCube")

    def setCube(self, slot):
        return self._call_hardware("setCube", slot)

    def setCubeByName(self, cube_name):
        slot = self._cube_name_to_slot.get(cube_name)
        if slot is None:
            self.__logger.warning(f"Unknown Leica cube name: {cube_name}")
            return None
        return self.setCube(slot)

    def getSidePort(self):
        return self._call_hardware("getSidePort")

    def setSidePort(self, value):
        return self._call_hardware("setSidePort", value)

    def setEyepiecePort(self):
        return self._call_hardware("setEyepiecePort")

    def setCameraPort(self):
        return self._call_hardware("setCameraPort")

    def getMagnChanger(self):
        return self._call_hardware("getMagnChanger")

    def setMagnChanger(self, value):
        return self._call_hardware("setMagnChanger", value)

    def setMagn1(self):
        return self._call_hardware("setMagn1")

    def setMagnScan(self):
        return self._call_hardware("setMagnScan")

    def getILFieldDiaphragm(self):
        return self._call_hardware("getILFieldDiaphragm")

    def setILFieldDiaphragm(self, value):
        return self._call_hardware("setILFieldDiaphragm", value)

    def getILApertureDiaphragm(self):
        return self._call_hardware("getILApertureDiaphragm")

    def setILApertureDiaphragm(self, value):
        return self._call_hardware("setILApertureDiaphragm", value)

    def create_lut_from_calib(self, calib_csv_path):
        return self._call_hardware("create_lut_from_calib", calib_csv_path)
