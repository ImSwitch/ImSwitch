import serial
import time
from threading import Event, Thread
import serial.tools.list_ports

if not __name__ == "__main__":
    from imswitch.imcommon.model import initLogger
    from imswitch.imcontrol.model.managers.positioners.PositionerManager import PositionerManager
else: 
    PositionerManager = object

    

BAUD_RATE = 115200

class GRBLController:
    def __init__(self, port, baud_rate=BAUD_RATE, debug=False):
        self.port = port
        self.ser = serial.Serial(self.port, BAUD_RATE)
        self.ser.timeout = .5
        self.ser.write_timeout = .5
        self.debug = 1 #debug
        self.speed = {'X': 10000, 'Y': 10000, 'Z': 10000}
        self.idle_counter_limit = 3
        self.send_wake_up()

    def write(self, command):
        try:
            self.ser.write(command)
        except Exception as e:
            print(f"Error writing to serial port: {e}")

    def send_wake_up(self):
        self.write(("\r\n\r\n").encode())
        self.write(("$X" + '\n').encode())
        time.sleep(1)
        self.ser.flushInput()

    def send_gcode_command(self, command,  is_blocking=True):
        mThread = Thread(target=self.send_gcode_command_inThread, args=(command,))
        mThread.start()
        if is_blocking:
            mThread.join()

    def send_gcode_command_inThread(self, command):
        cleaned_line = self.remove_eol_chars(self.remove_comment(command))
        if cleaned_line:
            print(f"Sending gcode: {cleaned_line}")
            self.write((cleaned_line + '\n').encode())
            self.wait_for_movement_completion(cleaned_line)
            grbl_out = self.ser.readline()
            if self.debug: print(f" : {grbl_out.strip().decode('utf-8')}")

    def wait_for_movement_completion(self, cleaned_line, timeout=5):
        Event().wait(.1)
        if cleaned_line not in ['$X', '$$']:
            idle_counter = 0
            timenow = time.time()   
            while True:
                self.ser.reset_input_buffer()
                self.write(('?' + '\n').encode())
                grbl_out = self.ser.readline()
                grbl_response = grbl_out.strip().decode('utf-8')
                if self.debug: print(f"Response: {grbl_response}")
                if grbl_response != 'ok' and 'Idle' in grbl_response:
                    idle_counter += 1
                if grbl_response.find("Alarm") != -1:
                    self.write(("$X" + '\n').encode())
                if idle_counter > self.idle_counter_limit:
                    break
                if time.time() - timenow > timeout:
                    break

    @staticmethod
    def remove_comment(string):
        return string.split(';')[0] if ';' in string else string

    @staticmethod
    def remove_eol_chars(string):
        return string.strip()

    def move(self, x=None, y=None, z=None, is_absolute=True, is_blocking=False):
        '''
         $J=G21G91X100F10000
         '''
        mode_command = "G90" if is_absolute else "G91"
        #self.send_gcode_command(mode_command)
        if x is not None:
            self.send_gcode_command(f"G21{mode_command}X{x}F{self.speed['X']}", is_blocking=is_blocking)
        if y is not None:
            self.send_gcode_command(f"G21{mode_command}Y{y}F{self.speed['Y']}", is_blocking=is_blocking)
        if z is not None:
            self.send_gcode_command(f"G21{mode_command}Z{z}F{self.speed['Z']}", is_blocking=is_blocking)

    def home(self):
        self.send_gcode_command("$H")

    def get_position(self):
        self.write(("?" + '\n').encode())
        grbl_out = self.ser.readline()
        response = grbl_out.strip().decode('utf-8')
        if self.debug: print(f"Current Position: {response}")
        if 'WPos:' in response:
            start = response.find('WPos:') + len('WPos:')
            end = response.find('|', start)
            wpos_str = response[start:end]
            x, y, z = map(float, wpos_str.split(','))
            return {'X': x, 'Y': y, 'Z': z}
        elif 'MPos:' in response:
            start = response.find('MPos:') + len('MPos:')
            end = response.find('|', start)
            mpos_str = response[start:end]
            x, y, z = map(float, mpos_str.split(','))
            return {'X': x, 'Y': y, 'Z': z}
        else:
            return {'X': 0, 'Y': 0, 'Z': 0}


    def close(self):
        self.ser.close()

def find_grbl_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'Arduino' in port.manufacturer or 'CH340' in port.manufacturer or 'USB' in port.description: 
            print("Found GRBL controller at port: ", port.device)
            return port.device
    return None

class GRBLStageManager(PositionerManager):
    def __init__(self, positionerInfo, name, port=None,  **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={axis: 0 for axis in positionerInfo.axes})
        self.__logger = initLogger(self, instanceName=name)
        try:
            self.port = lowLevelManagers['rs232sManager'][positionerInfo.managerProperties['rs232device']]
        except Exception as e:
            self.__logger.error(e)
            self.port = None
        self._commChannel = lowLevelManagers['commChannel']
        
        for axis in positionerInfo.axes:
            self.speed[axis] = 10000
            
        if port is None:
            self.port = find_grbl_port()
        else:
            self.port = port
        if self.port:
            self.controller = GRBLController(self.port)
            self._position = self.getPosition()
        else:
            raise Exception("GRBL controller not found")
        
    def setSpeed(self, value=0, axis="X"):
        self.speed[axis] = value

    def moveForever(self, value=0, axis="X", speed=None, acceleration=None, isEnable=None):
        pass

    def move(self, value=0, axis="X", is_absolute=False, is_blocking=True, acceleration=None, speed=None, isEnable=None, timeout=1):
        if axis in ["X", "Y", "Z"]:
            coords = {'X': None, 'Y': None, 'Z': None}
            coords[axis] = value/1000.
            self.controller.move(x=coords["X"], y=coords['Y'], z=coords["Z"], is_absolute=is_absolute, is_blocking=is_blocking)
            self._position[axis] = self.controller.get_position()[axis]
            self._commChannel.sigUpdateMotorPosition.emit()
        elif axis == "XY":
            coords = {'X': None, 'Y': None, 'Z': None}
            coords['X'], coords['Y'] = value[0]/1000., value[1]/1000.
            self.controller.move(x=coords["X"], y=coords['Y'], z=coords["Z"], is_absolute=is_absolute, is_blocking=is_blocking)
            self._position['X'] = self.controller.get_position()['X']
            self._position['Y'] = self.controller.get_position()['Y']
            self._commChannel.sigUpdateMotorPosition.emit()

    def getPosition(self):
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
    port_path = 'COM8'
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
