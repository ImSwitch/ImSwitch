class MockCobolt06:
    """Stateful mock for the PyCobolt Cobolt06 driver API."""

    def __init__(self, port=None, serialnumber=None, baudrate=115200):
        self.port = port
        self.serialnumber = serialnumber or 'SIM-Cobolt06'
        self.modelnumber = '0000-06-0000-0000'
        self.baudrate = baudrate

        self._is_on = False
        self._is_paused = True
        self._mode = 'ConstantCurrent'
        self._state = 'AutostartLaserOff'
        self._power = 0.0
        self._current = 0.0
        self._modulation_power = 0.0
        self._modulation_current = 0.0
        self._modulation_digital_enabled = False
        self._modulation_analog_enabled = False

    @property
    def power(self):
        return self._power

    @property
    def paused(self):
        return self._is_paused

    def is_connected(self):
        return True

    def disconnect(self):
        return 'OK'

    def finalize(self):
        self.turn_off()
        return self.disconnect()

    def turn_on(self):
        self._is_on = True
        self._state = 'AutostartLaserOn'
        return 'OK'

    def turn_off(self):
        self._is_on = False
        self._is_paused = True
        self._state = 'AutostartLaserOff'
        return 'OK'

    def is_on(self):
        return self._is_on

    def constant_current(self, current=None):
        self._mode = 'ConstantCurrent'
        if current is not None:
            self._current = float(current)
        return 'OK'

    def constant_power(self, power=None):
        self._mode = 'ConstantPower'
        if power is not None:
            self._power = float(power)
        return 'OK'

    def set_power(self, power):
        self._power = float(power)
        return 'OK'

    def get_mode(self):
        return self._mode

    def get_state(self):
        return self._state

    def power_modulation_mode(self, digital_enabled=True, analog_enabled=False):
        self._mode = 'PowerModulation'
        self._modulation_digital_enabled = bool(digital_enabled)
        self._modulation_analog_enabled = bool(analog_enabled)
        return 'OK'

    def current_modulation_mode(self, digital_enabled=True, analog_enabled=False):
        self._mode = 'CurrentModulation'
        self._modulation_digital_enabled = bool(digital_enabled)
        self._modulation_analog_enabled = bool(analog_enabled)
        return 'OK'

    def set_modulation_power(self, power):
        self._modulation_power = float(power)
        return 'OK'

    def get_modulation_power(self):
        return self._modulation_power

    def set_modulation_current(self, current):
        self._modulation_current = float(current)
        return 'OK'

    def get_modulation_current(self):
        return self._modulation_current

    def get_modulation_state(self):
        return [
            '1' if self._modulation_digital_enabled else '0',
            '1' if self._modulation_analog_enabled else '0'
        ]

    def pause_emission(self):
        self._is_paused = True
        return 'OK'

    def resume_emission(self):
        self._is_paused = False
        return 'OK'
