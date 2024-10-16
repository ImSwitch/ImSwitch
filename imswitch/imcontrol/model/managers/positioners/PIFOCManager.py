import pipython  # PI Python wrapper, ensure it's installed via pip (pip install pipython)
import time

from .PositionerManager import PositionerManager
from pipython import GCSDevice, GCSError

class PIFOCManager(PositionerManager):
    """ PositionerManager for control of a PI Voice Coil V-308 stage through USB communication.
    
    Manager properties:

    - ``serialnum`` -- serial number of the usb device
	- ``vel`` -- velocity for the movement (m/s), default to 100 mm/s
    - ``min_pos`` -- min position of the stage (in mm)
    - ``max_pos`` -- max position of the stage (in mm)
    - ``tolerance`` -- Tolérance pour la position (en mm)

    """

    def __init__(self, positionerInfo, name, *args, **lowLevelManagers):
        if len(positionerInfo.axes) != 1:
            raise RuntimeError(f'{self.__class__.__name__} only supports one axis,'
                               f' {len(positionerInfo.axes)} provided.')

        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })

        #Initialize communication with the PI stage
        self._serialnum = positionerInfo.managerProperties['serialnum']
        self._axis=1 # assuming axis ID is 1
        self._axis_name = list(positionerInfo.axes)[0]  # Use the name of the axis, e.g., 'Z'
        self._vel = positionerInfo.managerProperties['vel']
        self._min_pos = positionerInfo.managerProperties['min_pos']
        self._max_pos = positionerInfo.managerProperties['max_pos']
        self._tolerance = positionerInfo.managerProperties['tolerance']

        # Initialize position as a dictionary
        self._position = {self._axis_name: 0}

        try:
            self._device = GCSDevice()
            self._device.ConnectUSB(serialnum=self._serialnum)

            # Check communication with the device
            if not self._device.IsConnected():
                raise RuntimeError(f"No response from the USB device {self._serialnum}.")

            # Set the velocity based on manager property
            self.set_velocity(self._vel)

            self.homing()  # Perform homing

        except GCSError as e:
            raise RuntimeError(f"Communication error with device: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"An error occurred while initializing the device: {e}")
    
    def set_velocity(self, velocity):
        #Set the movement velocity for the axis.
        try:
            self._device.VEL(self._axis, velocity)
        except GCSError as e:
            raise RuntimeError(f"Error setting velocity: {str(e)}")
    
    def homing(self):
        try:
            # Activate servo control before homing
            self.set_servo_state(1)

            print(f"Starting reference move for device: {self._serialnum}")
            self._device.RON(self._axis, 1)  # Activer le mode de référencement automatique
            self._device.FRF(self._axis)  # Find reference (homing)

            self.wait_until_motion_complete(0)  # Wait for motion to complete
            print("Homing completed, checking final status...")

            # Check error after homing
            final_error_code = self._device.qERR()
            if final_error_code != 0:
                raise RuntimeError(f"Error after homing: Error code {final_error_code}")

            # Move to the maximum position after homing
            self.setPosition(self._max_pos*1000, None)

            # Update position to 0 after homing
            #self._position[self._axis] = 0
            print(f"Homing completed successfully for axis {self._axis}. Final position: {self._max_pos}")
        except GCSError as e:
            raise RuntimeError(f"Error performing homing: {str(e)}")
        except RuntimeError as e:
            print(f"Runtime error occurred: {str(e)}")
            raise
        
    def set_servo_state(self, state):
        #Activate or deactivate the servo for the axis
        try:
            self._device.SVO(self._axis, state)  # Activer (1) ou désactiver (0) le servo
        except GCSError as e:
            raise RuntimeError(f"Error setting servo state: {str(e)}")
        
    def wait_until_motion_complete(self, target):
        #Wait for the motion to complete by querying the IsMoving() method.
        try:
            start_time = time.time()
            timeout = 30  # Maximum time to wait for motion to complete (in seconds)
           
            while self._device.IsMoving(self._axis):  # While the axis is moving
                current_position = self.get_abs()  # Get the current position

                # Check for errors during motion
                error_code = self._device.qERR()
                if error_code != 0:
                    raise RuntimeError(f"Error during homing: Error code {error_code}")

                # Check for timeout
                if time.time() - start_time > timeout:
                    print("Homing is taking too long, stopping the device...")
                    self.stop()  # Arrêter le mouvement si ça prend trop de temps
                    raise RuntimeError("Homing timeout exceeded")
                
                # Check if the position is within the tolerance
                if abs(current_position - target) < self._tolerance:
                    break

                time.sleep(0.5)  # Attendre 500 ms avant de revérifier   
                
        except GCSError as e:
            raise RuntimeError(f"Error during motion wait: {str(e)}")

    def move(self, value, _):
        #Move the stage by a relative value.
        if value == 0:
            return

        new_position = self._position[self._axis] + float(value)/1000 # Convert target value from µm to mm

        # Check position limits
        if new_position < self._min_pos or new_position > self._max_pos:
            raise RuntimeError(f"Movement out of bounds: {new_position} is not within [{self._min_pos}, {self._max_pos}]")

        try:      
            self._device.MOV(self._axis, new_position)
            self.wait_until_motion_complete(new_position)  # Wait for motion to complete
            self._position[self._axis] = new_position  # Update the position
            print(f"Moved to relative position {new_position} on axis {self._axis}")
        except GCSError as e:
            raise RuntimeError(f"Error during move: {str(e)}")

    def setPosition(self, value, _):
        #Move the stage to an absolute position.
        value_mm = value / 1000  # Convert value from µm to mm
        if value_mm < self._min_pos or value_mm > self._max_pos:
            raise RuntimeError(f"Movement out of bounds: {value_mm} is not within [{self._min_pos}, {self._max_pos}]")

        try:
            self._device.MOV(self._axis, float(value_mm))
            self.wait_until_motion_complete(value_mm)  # Wait for motion to complete
            self._position[self._axis] = float(value_mm)
            print(f"Moved to absolute position {value_mm} on axis {self._axis}")
        except GCSError as e:
            raise RuntimeError(f"Error setting position: {str(e)}")
        
    def stop(self):
        #Stop the motion of the stage.
        try:
            print("Stopping the device...")
            self._device.STP()  # Stop all movements immediately
        except GCSError as e:
            raise RuntimeError(f"Error stopping the device: {str(e)}")

    @property
    def position(self):
        #Get the current position of the stage.
        _ = self.get_abs()
        return self._position

    def get_abs(self):
        #Query the absolute position from the device.
        try:
            reply = self._device.qPOS(self._axis)
            if reply is None or self._axis not in reply:
                raise RuntimeError(f"Invalid response from the device")
            self._position[self._axis] = reply[self._axis]
            return reply[self._axis]
        except GCSError as e:
            raise RuntimeError(f"Error querying position: {str(e)}")   
            
    def check_overflow(self):
        # Check for overflow and handle it if necessary.
        try:
            error_code = self._device.qERR()
            if error_code != 0:
                print(f"Error detected: Error code {error_code}")
                self.handle_overflow()
        except GCSError as e:
            raise RuntimeError(f"Error checking overflow: {str(e)}")
    
    def handle_overflow(self):
        # Handle overflow by stopping the device, switching to open-loop, and retrying homing.
        try:
            self.stop()  # Stop all movements immediately
            self.set_servo_state(0)  # Disable the servo (open-loop)
            time.sleep(1)  # Wait a short time
            self.set_servo_state(1)  # Enable the servo (close-loop)
            self.homing()  # Retry homing
        except GCSError as e:
            raise RuntimeError(f"Error handling overflow: {str(e)}")
        
    def finalize(self):
        # Close the connection to the device.
        try:
            self._device.CloseConnection()
            print(f"Connection to device with serial number {self._serialnum} closed.")
        except GCSError as e:
            raise RuntimeError(f"Error closing connection: {str(e)}")

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
