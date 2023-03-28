from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
# serialport.py
from serial import Serial
from serial import SerialException
from serial import EIGHTBITS
from serial import PARITY_NONE
from serial import STOPBITS_ONE
from serial.tools import list_ports


class SerialPort:
    """
    A utility class for managing a RS232 serial connection using the pyserial library.

    """

    def __init__(self, com_port: str, baud_rate: int, report: bool = True):
        self.serial_port = Serial()
        self.com_port = com_port
        self.baud_rate = baud_rate
        # user feedback settings
        self.report = report
        self.print = self.report_to_console

    @staticmethod
    def scan_ports() -> list[str]:
        """Returns a sorted list of COM ports."""
        com_ports = [port.device for port in list_ports.comports()]
        com_ports.sort(key=lambda value: int(value[3:]))
        return com_ports

    def connect_to_serial(self, rx_size: int = 12800, tx_size: int = 12800, read_timeout: int = 1,
                          write_timeout: int = 1) -> None:
        """Connect to the serial port."""
        # serial port settings
        self.serial_port.port = self.com_port
        self.serial_port.baudrate = self.baud_rate
        self.serial_port.parity = PARITY_NONE
        self.serial_port.bytesize = EIGHTBITS
        self.serial_port.stopbits = STOPBITS_ONE
        self.serial_port.xonoff = False
        self.serial_port.rtscts = False
        self.serial_port.dsrdtr = False
        self.serial_port.write_timeout = write_timeout
        self.serial_port.timeout = read_timeout

        # set the size of the rx and tx buffers before calling open
        self.serial_port.set_buffer_size(rx_size, tx_size)

        # try to open the serial port
        try:
            self.serial_port.open()
        except SerialException:
            self.print(f"SerialException: can't connect to {self.com_port} at {self.baud_rate}!")

        if self.is_open():
            # clear the rx and tx buffers
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            # report connection status to user
            self.print("Connected to the serial port.")
            self.print(f"Serial port = {self.com_port} :: Baud rate = {self.baud_rate}")

    def disconnect_from_serial(self) -> None:
        """Disconnect from the serial port if it's open."""
        if self.is_open():
            self.serial_port.close()
            self.print("Disconnected from the serial port.")

    def is_open(self) -> bool:
        """Returns True if the serial port exists and is open."""
        # short circuits if serial port is None
        return self.serial_port and self.serial_port.is_open

    def report_to_console(self, message: str) -> None:
        """Print message to the output device, usually the console."""
        # useful if we want to output data to something other than the console (ui element etc)
        if self.report:
            print(message)

    def send_command(self, cmd: bytes) -> None:
        """Send a serial command to the device."""
        # always reset the buffers before a new command is sent
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()
        # send the serial command to the controller
        command = bytes(f"{cmd}\r", encoding="ascii")
        self.serial_port.write(command)
        self.print(f"Send: {command.decode(encoding='ascii')}")

    def read_response(self) -> str:
        """Read a line from the serial response."""
        response = self.serial_port.readline()
        response = response.decode(encoding="ascii")
        self.print(f"Recv: {response.strip()}")
        return response  # in case we want to read the response


class MS2000(SerialPort):
    """
    A utility class for operating the MS2000 from Applied Scientific Instrumentation.

    Move commands use ASI units: 1 unit = 1/10 of a micron.
    Example: to move a stage 1 mm on the x axis, use self.moverel(10000)

    Manual:
        http://asiimaging.com/docs/products/ms2000

    """

    # all valid baud rates for the MS2000
    # these rates are controlled by dip switches
    BAUD_RATES = [9600, 19200, 28800, 115200]

    def __init__(self, com_port: str, baud_rate: int = 115200, report: str = True):
        super().__init__(com_port, baud_rate, report)
        # validate baud_rate input
        if baud_rate in self.BAUD_RATES:
            self.baud_rate = baud_rate
        else:
            raise ValueError("The baud rate is not valid. Valid rates: 9600, 19200, 28800, or 115200.")

    # ------------------------------ #
    #     MS2000 Serial Commands     #
    # ------------------------------ #

    def moverel(self, x: int = 0, y: int = 0, z: int = 0) -> None:
        """Move the stage with a relative move."""
        self.send_command(f"MOVREL X={x} Y={y} Z={z}\r")
        self.read_response()

    def moverel_axis(self, axis: str, distance: int) -> None:
        """Move the stage with a relative move."""
        self.send_command(f"MOVREL {axis}={distance}\r")
        self.read_response()

    def move(self, x: int = 0, y: int = 0, z: int = 0) -> None:
        """Move the stage with an absolute move."""
        self.send_command(f"MOVE X={x} Y={y} Z={z}\r")
        self.read_response()

    def move_axis(self, axis: str, distance: int) -> None:
        """Move the stage with an absolute move."""
        self.send_command(f"MOVE {axis}={distance}\r")
        self.read_response()

    def set_max_speed(self, axis: str, speed: int) -> None:
        """Set the speed on a specific axis. Speed is in mm/s."""
        self.send_command(f"SPEED {axis}={speed}\r")
        self.read_response()

    def get_position(self, axis: str) -> int:
        """Return the position of the stage in ASI units (tenths of microns)."""
        self.send_command(f"WHERE {axis}\r")
        response = self.read_response()
        return int(response.split(" ")[1])

    def get_position_um(self, axis: str) -> float:
        """Return the position of the stage in microns."""
        self.send_command(f"WHERE {axis}\r")
        response = self.read_response()
        return float(response.split(" ")[1]) / 10.0

    # ------------------------------ #
    #    MS2000 Utility Functions    #
    # ------------------------------ #

    def is_axis_busy(self, axis: str) -> bool:
        """Returns True if the axis is busy."""
        self.send_command(f"RS {axis}?\r")
        return "B" in self.read_response()

    def is_device_busy(self) -> bool:
        """Returns True if any axis is busy."""
        self.send_command("/")
        return "B" in self.read_response()

    def wait_for_device(self, report: bool = False) -> None:
        """Waits for the all motors to stop moving."""
        if not report:
            print("Waiting for device...")
        temp = self.report
        self.report = report
        busy = True
        while busy:
            busy = self.is_device_busy()
        self.report = temp


class ASIPositionManager(PositionerManager):
    """ PositionerManager for ASI Stage.

    Manager properties:

    None
    """

    def __init__(self, positionerInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self.__logger.debug('Initializing')

        if len(positionerInfo.axes) != 1:
            raise RuntimeError(f'{self.__class__.__name__} only supports one axis,'
                               f' {len(positionerInfo.axes)} provided.')
                               
        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self.ms2k = MS2000("COM3", 115200)
        self.ms2k.connect_to_serial()

    def setPosition(self, position, axis):
        self._position[self.axes[0]] = position

    def move(self, dist, axis):
        dist = dist * 10 # convert to um from 1/10 um
        current_position = self.ms2k.get_position(axis) / 10
        self._position[axis] = current_position
        self.ms2k.moverel_axis(axis, dist)
        self.ms2k.wait_for_device()
        current_position = self.ms2k.get_position(axis) / 10
        self._position[axis] = current_position


    def finalize(self) -> None:
        self.ms2k.disconnect_from_serial()


# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
