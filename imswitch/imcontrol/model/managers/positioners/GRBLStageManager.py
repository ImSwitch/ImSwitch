import serial
import time
from threading import Event
import serial.tools.list_ports
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.managers.positioners.PositionerManager import PositionerManager

    

BAUD_RATE = 115200

class GRBLController:
    def __init__(self, port, baud_rate=BAUD_RATE, debug=False):
        self.port = port
        self.ser = serial.Serial(self.port, BAUD_RATE)
        self.debug = debug
        self.send_wake_up()

    def send_wake_up(self):
        self.ser.write(str.encode("\r\n\r\n"))
        time.sleep(1)
        self.ser.flushInput()

    def send_gcode_command(self, command):
        cleaned_line = self.remove_eol_chars(self.remove_comment(command))
        if cleaned_line:
            print(f"Sending gcode: {cleaned_line}")
            self.ser.write(str.encode(cleaned_line + '\n'))
            self.wait_for_movement_completion(cleaned_line)
            grbl_out = self.ser.readline()
            if self.debug: print(f" : {grbl_out.strip().decode('utf-8')}")

    def wait_for_movement_completion(self, cleaned_line):
        Event().wait(1)
        if cleaned_line not in ['$X', '$$']:
            idle_counter = 0
            while True:
                self.ser.reset_input_buffer()
                self.ser.write(str.encode('?' + '\n'))
                grbl_out = self.ser.readline()
                grbl_response = grbl_out.strip().decode('utf-8')
                if grbl_response != 'ok' and 'Idle' in grbl_response:
                    idle_counter += 1
                if idle_counter > 10:
                    break

    @staticmethod
    def remove_comment(string):
        return string.split(';')[0] if ';' in string else string

    @staticmethod
    def remove_eol_chars(string):
        return string.strip()

    def move(self, x=None, y=None, z=None, is_absolute=True):
        mode_command = "G90" if is_absolute else "G91"
        self.send_gcode_command(mode_command)
        if x is not None:
            self.send_gcode_command(f"G1 X{x}")
        if y is not None:
            self.send_gcode_command(f"G1 Y{y}")
        if z is not None:
            self.send_gcode_command(f"G1 Z{z}")

    def home(self):
        self.send_gcode_command("$H")

    def get_position(self):
        self.ser.write(str.encode("?" + '\n'))
        grbl_out = self.ser.readline()
        response = grbl_out.strip().decode('utf-8')
        if self.debug: print(f"Current Position: {response}")
        if 'WPos:' in response:
            start = response.find('WPos:') + len('WPos:')
            end = response.find('|', start)
            wpos_str = response[start:end]
            x, y, z = map(float, wpos_str.split(','))
            return {'X': x, 'Y': y, 'Z': z}
        return None

    def close(self):
        self.ser.close()

def find_grbl_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'Arduino' in port.manufacturer:
            return port.device
    return None

class GRBLStageManager(PositionerManager):
    def __init__(self, positionerInfo, name, port=None,  **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={axis: 0 for axis in positionerInfo.axes})
        self.__logger = initLogger(self, instanceName=name)
        self.port = lowLevelManagers['rs232sManager'][positionerInfo.managerProperties['rs232device']]
        self._commChannel = lowLevelManagers['commChannel']
        if port is None:
            self.port = find_grbl_port()
        else:
            self.port = port
        if self.port:
            self.controller = GRBLController(self.port)
            self._position = self.get_position()
        else:
            raise Exception("GRBL controller not found")

    def move(self, value=0, axis="X", is_absolute=False, is_blocking=True, acceleration=None, speed=None, isEnable=None, timeout=1):
        if axis in ["X", "Y", "Z"]:
            coords = {'X': None, 'Y': None, 'Z': None}
            coords[axis] = value
            self.controller.move(**coords, is_absolute=is_absolute)
            self._position[axis] = self.controller.get_position()[axis]
            self._commChannel.sigUpdateMotorPosition.emit()

    def get_position(self):
        position = self.controller.get_position()
        self._commChannel.sigUpdateMotorPosition.emit()
        return position

    def do_home(self, axis, isBlocking=False):
        if axis in ["X", "Y", "Z"]:
            self.controller.home()
            self.set_position(0, axis)

    def set_position(self, value, axis):
        if axis in self._position:
            self._position[axis] = value
            self._commChannel.sigUpdateMotorPosition.emit()

    def force_stop(self, axis):
        # Placeholder for stopping functionality
        pass

    def close(self):
        self.controller.close()

if __name__ == "__main__":
    #port_path = find_grbl_port()
    port_path = '/dev/cu.wchusbserial110'
    if port_path:
        print(f"GRBL controller found at port: {port_path}")
        grbl_controller = GRBLController(port_path)
        grbl_controller.move(x=10)
        position = grbl_controller.get_position()
        print(position)
        grbl_controller.move(y=20, is_absolute=False)
        grbl_controller.move(z=5)
        grbl_controller.home()
        grbl_controller.close()
    else:
        print("GRBL controller not found")
