import warnings

from imswitch.imcommon.model import initLogger


class ThorlabsMFF:
    """Thorlabs MFF101/MFF102 flip mirror manager using pylablib."""

    def __init__(self, deviceInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        self.name = name
        self.deviceInfo = deviceInfo
        self.serial_number = self._read_info("serial_number")
        self.invert = bool(self._read_info("invert", False))
        self.initial_state = self._read_info("initial_state", None)
        self.state_names = self._normalize_state_names(
            self._read_info("state_names", None)
        )
        self._device = None
        self._connected = False
        self._last_error = None

        self._connect()

        if self.initial_state is not None and self.is_connected():
            self.move_to(int(self.initial_state))

    def _read_info(self, key, default=None):
        if hasattr(self.deviceInfo, key):
            value = getattr(self.deviceInfo, key)
            if value is not None:
                return value

        manager_properties = getattr(self.deviceInfo, "managerProperties", None) or {}
        return manager_properties.get(key, default)

    def _connect(self):
        self._last_error = None

        if not self.serial_number:
            self._connected = False
            self._last_error = "Missing serial_number"
            self.__logger.error(f"{self.name}: missing serial_number")
            return

        try:
            from pylablib.devices import Thorlabs

            # pylablib can warn if the reported model does not match the serial prefix.
            # For MFF002/MFF10x this can be harmless if move/get_state work.
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=r"model number .* doesn't match the device ID prefix.*",
                    category=UserWarning,
                )
                self._device = Thorlabs.MFF(str(self.serial_number))

            self._connected = True
            self.__logger.info(
                f"{self.name}: connected to Thorlabs MFF serial {self.serial_number}"
            )

        except Exception as e:
            self._device = None
            self._connected = False
            self._last_error = str(e)
            self.__logger.error(
                f"{self.name}: failed to connect to Thorlabs MFF "
                f"serial {self.serial_number}: {e}"
            )
    def _normalize_state_names(self, state_names):
        default = {0: "0", 1: "1"}

        if not state_names:
            return default

        return {
            0: str(state_names.get("0", state_names.get(0, "0"))),
            1: str(state_names.get("1", state_names.get(1, "1"))),
        }
    
    def is_connected(self):
        return self._connected and self._device is not None

    def get_last_error(self):
        return self._last_error

    def _to_hw_state(self, state):
        state = int(state)
        if state not in (0, 1):
            raise ValueError("Flip mirror state must be 0 or 1")
        return 1 - state if self.invert else state

    def _from_hw_state(self, state):
        state = int(state)
        return 1 - state if self.invert else state

    def move_to(self, state):
        if not self.is_connected():
            raise RuntimeError(f"{self.name}: flip mirror is not connected")

        hw_state = self._to_hw_state(state)
        self._device.move_to_state(hw_state)

    def get_state(self):
        if not self.is_connected():
            raise RuntimeError(f"{self.name}: flip mirror is not connected")

        return self._from_hw_state(self._device.get_state())

    def get_state_names(self):
        return dict(self.state_names)

    def close(self):
        if self._device is not None:
            try:
                self._device.close()
            except Exception as e:
                self.__logger.error(f"{self.name}: error while closing: {e}")

        self._device = None
        self._connected = False

    def reset_connection(self):
        self.close()
        self._connect()
        return self.is_connected()

    def finalize(self):
        self.close()