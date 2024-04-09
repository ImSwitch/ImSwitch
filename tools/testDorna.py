from dorna2 import Dorna
import time

# Create a Dorna object and connect to the robot
robot = Dorna()
robot.connect("192.168.178.41") # connect to the robot server at ws://10.0.0.10:443

# Define the list of coordinates and speed
# Each coordinate is a dictionary with joint positions (in degrees)
coordinates = [
    {"j0": 0, "j1": 45, "j2": 90, "j3": 45, "j4": 0},
    {"j0": 10, "j1": 50, "j2": 80, "j3": 50, "j4": 0},
    # Add more coordinates as needed
]

speed = 100  # Speed in percentage of the maximum speed

# Loop through each set of coordinates and move the robot
for coord in coordinates:
    # Move the robot using jmove
    robot.jmove(coord)
    
    # Wait for the robot to finish the movement
    while robot.busy():
        time.sleep(0.1)

# Disconnect the robot after the operation
robot.disconnect()