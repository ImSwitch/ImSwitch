import time
import serial

from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager

class SerialDacZManager(PositionerManager):
    """
    Serial DAC Z actuator.

    This behaves like a virtual Z positioner:
        position [um-like units] -> DAC voltage

    Voltage = offset_voltage + position * volts_per_um
    """

    def __init__(self, positionerInfo, name, **lowLevelManagers):
        if len(positionerInfo.axes) != 1:
            raise RuntimeError(
                f"{self.__class__.__name__} only supports one axis, "
                f"{len(positionerInfo.axes)} provided."
            )

        
        self.__logger = initLogger(self, instanceName=name)

        axis = positionerInfo.axes[0]
        props = positionerInfo.managerProperties

        initial_position = float(props.get("initial_position", 0.0))

        super().__init__(
            positionerInfo,
            name,
            initialPosition={axis: initial_position},
        )

        self._axis = axis

        self._port = props.get("port", "COM13")
        self._baudrate = int(props.get("baudrate", 115200))
        self._timeout = float(props.get("timeout", 1.0))
        self._command_timeout = float(props.get("command_timeout", 2.0))

        self._offset_voltage = float(props.get("offset_voltage", 0.0))
        self._volts_per_um = float(props.get("volts_per_um", 0.005))

        self._min_voltage = float(props.get("min_voltage", -5.0))
        self._max_voltage = float(props.get("max_voltage", 5.0))
        self._clamp_voltage = bool(props.get("clamp_voltage", True))

        self._safe_voltage_on_close = props.get("safe_voltage_on_close", None)
        if self._safe_voltage_on_close is not None:
            self._safe_voltage_on_close = float(self._safe_voltage_on_close)

        self._prompt = props.get("prompt", ">>>").encode()
        self._dac_command = props.get("dac_command", "dac.SetDac({voltage})")

        self._ser = None
        self._is_available = False
        self._connection_error = None

        try:
            self._connect_and_initialize(initial_position)
        except Exception as exc:
            self._connection_error = str(exc)
            self.__logger.warning(
                f"Serial DAC Z manager unavailable on {self._port}: {exc}"
            )
            self._close_serial_safely()
            return

        self._is_available = True
        self.__logger.info("Serial DAC Z manager initialized")

    @property
    def isAvailable(self) -> bool:
        return self._is_available

    @property
    def connectionError(self):
        return self._connection_error

    def _connect_and_initialize(self, initial_position):
        self.__logger.info(
            f"Opening serial DAC Z connection on {self._port} "
            f"at {self._baudrate} baud"
        )

        self._ser = serial.Serial(
            self._port,
            baudrate=self._baudrate,
            timeout=self._timeout,
        )

        self.__logger.info(f"Serial port {self._port} opened")

        self.__logger.debug("Trying to enter MicroPython REPL")
        repl_reply = self._enter_repl()
        self.__logger.debug(f"MicroPython REPL reply:\n{repl_reply}")

        self.__logger.debug(
            f"Sending initial position {initial_position} "
            f"{self._axis} -> {self._position_to_voltage(initial_position)} V"
        )

        self._send_voltage(self._position_to_voltage(initial_position))

    def move(self, dist, axis=None):
        self._check_axis(axis)
        if not self.isAvailable:
            return self._position[self._axis]

        new_position = self._position[self._axis] + float(dist)
        return self.setPosition(new_position, self._axis)

    def setPosition(self, position, axis=None):
        self._check_axis(axis)
        if not self.isAvailable:
            return self._position[self._axis]

        position = float(position)
        voltage = self._position_to_voltage(position)

        try:
            self._send_voltage(voltage)
        except Exception as exc:
            self._connection_error = str(exc)
            self._is_available = False
            self.__logger.warning(
                f"Serial DAC Z communication failed on {self._port}: {exc}"
            )
            self._close_serial_safely()
            return self._position[self._axis]

        self._position[self._axis] = position
        return position

    def get_abs(self, axis=None):
        self._check_axis(axis)
        return self._position[self._axis]

    def updatePosition(self):
        # No hardware readback available; keep virtual position.
        return self._position

    def finalize(self):
        try:
            if self.isAvailable and self._safe_voltage_on_close is not None:
                self._send_voltage(self._safe_voltage_on_close)
        except Exception:
            pass

        self._close_serial_safely()

    def _close_serial_safely(self):
        try:
            if self._ser is not None and self._ser.is_open:
                self._ser.close()
        except Exception:
            pass
        self._is_available = False

    def _check_axis(self, axis):
        if axis is not None and axis != self._axis:
            raise ValueError(
                f"{self.__class__.__name__} only controls axis {self._axis}, "
                f"got {axis}."
            )

    def _position_to_voltage(self, position):
        voltage = self._offset_voltage + float(position) * self._volts_per_um

        if voltage < self._min_voltage or voltage > self._max_voltage:
            if self._clamp_voltage:
                voltage = max(self._min_voltage, min(self._max_voltage, voltage))
            else:
                raise ValueError(
                    f"Requested voltage {voltage} V is outside allowed range "
                    f"[{self._min_voltage}, {self._max_voltage}] V."
                )

        return voltage

    def _enter_repl(self):
        self.__logger.debug("Sending CTRL-B to leave raw REPL if needed")
        self._ser.write(b"\x02")
        self._ser.flush()
        time.sleep(0.1)

        last_error = ""

        for attempt in range(5):
            self.__logger.debug(
                f"Requesting MicroPython prompt, attempt {attempt + 1}/5"
            )

            self._ser.write(b"\r\n")
            self._ser.flush()

            try:
                reply = self._read_until_prompt()
                self.__logger.debug("MicroPython prompt detected")
                return reply
            except TimeoutError as e:
                last_error = str(e)
                self.__logger.warning(
                    f"No MicroPython prompt detected on attempt {attempt + 1}/5. "
                    f"Partial reply: {last_error!r}"
                )

        raise RuntimeError(
            f"Could not get MicroPython prompt {self._prompt!r} "
            f"from {self._port}. Last reply: {last_error!r}"
        )

    def _send_voltage(self, voltage):
        cmd = self._dac_command.format(voltage=voltage, U=voltage)
        if not cmd.endswith("\r\n"):
            cmd += "\r\n"

        self.__logger.debug(f"Sending DAC command: {cmd.strip()}")

        self._ser.write(cmd.encode("utf-8"))
        self._ser.flush()

        reply = self._read_until_prompt()
        self.__logger.debug(f"DAC command reply:\n{reply}")

        return reply
    
    def _read_until_prompt(self):
        deadline = time.time() + self._command_timeout
        buffer = b""

        while time.time() < deadline:
            waiting = getattr(self._ser, "in_waiting", 0)

            if waiting:
                chunk = self._ser.read(waiting)
                buffer += chunk

                self.__logger.debug(
                    f"Serial received chunk: {chunk.decode(errors='replace')!r}"
                )

                if self._prompt in buffer:
                    text = buffer.decode(errors="replace")
                    self.__logger.debug(
                        f"Serial received complete reply: {text!r}"
                    )
                    return text
            else:
                time.sleep(0.01)

        text = buffer.decode(errors="replace")
        self.__logger.warning(
            f"Timeout waiting for prompt {self._prompt!r}. "
            f"Partial reply: {text!r}"
        )
        raise TimeoutError(text)
