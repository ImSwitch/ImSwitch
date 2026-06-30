from imswitch.imcommon.model import initLogger


class MockThorlabsMFF:
    """Mock flip mirror manager."""

    def __init__(self, deviceInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self.name = name
        self.deviceInfo = deviceInfo
        self._state = 0
        self._connected = True
        self._last_error = None

        initial_state = self._read_info("initial_state", None)
        if initial_state is not None:
            self._state = int(initial_state)
        
        self.state_names = self._normalize_state_names(
            self._read_info("state_names", None)
        )

        self.__logger.warning(f"{self.name}: using mock ThorlabsMFF")

    def _read_info(self, key, default=None):
        if hasattr(self.deviceInfo, key):
            value = getattr(self.deviceInfo, key)
            if value is not None:
                return value

        manager_properties = getattr(self.deviceInfo, "managerProperties", None) or {}
        return manager_properties.get(key, default)
    
    def _normalize_state_names(self, state_names):
        default = {0: "0", 1: "1"}

        if not state_names:
            return default

        return {
            0: str(state_names.get("0", state_names.get(0, "0"))),
            1: str(state_names.get("1", state_names.get(1, "1"))),
        }

    def get_state_names(self):
        return dict(self.state_names)

    def is_connected(self):
        return self._connected

    def get_last_error(self):
        return self._last_error

    def move_to(self, state):
        state = int(state)
        if state not in (0, 1):
            raise ValueError("Flip mirror state must be 0 or 1")
        self._state = state

    def get_state(self):
        return self._state

    def close(self):
        self._connected = False

    def reset_connection(self):
        self._connected = True
        self._last_error = None
        return True

    def finalize(self):
        self.close()