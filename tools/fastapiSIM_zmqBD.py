import zmq
import numpy as np
import pygame
import time
import os
import socket
from os import listdir
from os.path import isfile, join
from threading import Thread, Event
from fastapi import FastAPI, BackgroundTasks
import uvicorn

ZMQPORT = 5555
IS_FULLSCREEN = False
nImages = 9
CAM_TRIGGER_PIN = 37

# Configure GPIO if running on Raspberry Pi
try:
    import RPi.GPIO as GPIO
except:
    print("Not running on Pi")
    GPIO = None
    
if GPIO is not None:
    # List of pins your application uses
    pins_to_cleanup = [CAM_TRIGGER_PIN]

    # Clean up specific pins
    GPIO.setmode(GPIO.BOARD)  # or GPIO.BOARD, depending on your pin numbering
    for pin in pins_to_cleanup:
        GPIO.setup(pin, GPIO.IN)  # Set pin to input to safely unexport it
    GPIO.cleanup(pins_to_cleanup)  # Clean up only the pins you plan to use

    # Now, set up your GPIO pins as usual
    print("Setting up pin: ")
    GPIO.setup(CAM_TRIGGER_PIN, GPIO.OUT)

class ViewerController:
    def __init__(self):
        self.context = zmq.Context()
        # Use REQ socket for request-reply pattern
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind("tcp://*:"+str(ZMQPORT))
        self.tWait = 0.1
        
    def send_stop_continous(self):
        self.isRunningContinous = False
        try:
            self.mThread.join(timeout=1)
        except Exception as e:
            print(e)
        
    def send_stop_viewer(self):
        self.send_command("stop")
        
    def send_command(self, command):
        return self.send_command_and_receive(command)
        
    def send_command_and_receive(self, command):
        # clear messages in the socket
        while self.socket.poll(0):
            print(self.socket.recv_string(zmq.NOBLOCK))
        
        self.socket.send_string(command)
        # Block until a reply is received
        message = self.socket.recv_string()
        return message
    
    def display_continous(self):
        self.isRunningContinous = True
        def runPatternDisplayThreadFunction():
            while(self.isRunningContinous):
                for pattern_id in range(nImages): #len(self.current_images)):
                    if not self.isRunningContinous:
                        return
                    self.display_pattern(pattern_id)
                    self.send_trigger()
                    print(str(pattern_id))
                    time.sleep(self.tWait)
        self.mThread = threading.Thread(target=runPatternDisplayThreadFunction).start()
                    
    def display_pattern(self, pattern_id):
        self.send_command(f"display:{pattern_id}")

    def change_wavelength(self, wavelength):
        self.send_command(f"change_wavelength:{wavelength}")
        
    def set_wait_time(self, tWait):
        self.tWait = tWait
    
    def start_single_loop(self, i_cycle):
        self.send_command(f"start_single_loop:{i_cycle}")

    def send_trigger(self):
        self.send_command(f"trigger")
        
class ImageLoader:
    def __init__(self, path_488, path_635, n_images=9):
        self.path_488 = path_488
        self.path_635 = path_635
        self.n_images = n_images
        self.images_488 = self.load_images(self.path_488)
        self.images_635 = self.load_images(self.path_635)

    def load_images(self, path):
        images = []
        try:
            image_files = sorted([f for f in listdir(path) if isfile(join(path, f))])
            for i in range(self.n_images):
                images.append(pygame.image.load(join(path, image_files[i])))
            print("Images loaded successfully.")
        except Exception as e:
            print(f"Failed to load images: {e}")
            # Handle error or generate random patterns
        return images

app = FastAPI()
viewer_controller = ViewerController()

class PygameViewer:
    def __init__(self, display_size, path_488, path_635):
        self.display_size = display_size
        self.loader = ImageLoader(path_488, path_635)
        # Initialization of pygame and zmq as before
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("tcp://localhost:"+str(ZMQPORT))
        self.current_images = self.loader.images_488  # Default to 488nm images
        self.tWait = 0.1  # Default time to wait between patterns
        self.isRunningContinous = False
        self.mLock = threading.Lock()
        
    def run(self):
        os.environ["DISPLAY"] = ":0"
        pygame.display.init()
        pygame.init()
        if IS_FULLSCREEN:
            self.display = pygame.display.set_mode(self.display_size, pygame.FULLSCREEN)
        else:
            self.display = pygame.display.set_mode(self.display_size)
        pygame.mouse.set_visible(False)
        self.running = True
        while self.running:
                # Check for Pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:  # Allows quitting by closing the window
                        self.running = False

                # Non-blocking check for a message from ZMQ
                try:
                    # Wait for next request from client
                    message = self.socket.recv_string(zmq.NOBLOCK)
                    reply = self.handle_message(message)
                    # Send reply back to client
                    self.socket.send_string(reply)

                except zmq.Again:
                    pass  # No message received

                pygame.display.flip()  # Update the full display surface to the screen
                pygame.time.wait(10)  # Small delay to prevent high CPU usage
    
    def handle_message(self, message):
        response = ""
        if message.startswith("display:"):
            pattern_id = int(message.split(":")[1])
            self.display_pattern(pattern_id)
        elif message.startswith("change_wavelength:"):
            wavelength = int(message.split(":")[1])
            self.change_wavelength(wavelength)
        elif message == "start":
            self.start()
            # hreading.Thread(target=self.start).start()
        elif message == "stop":
            self.running = False
        elif message == "trigger":
            self.trigger()
        elif message.startswith("start_single_loop"):
            self.start_single_loop(int(message.split(":")[1]))
            response = "Current pattern info or any other data"
        return response
    
    def trigger(self, gpiopin=CAM_TRIGGER_PIN):
        # Perform trigger action
        GPIO.output(gpiopin, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(gpiopin, GPIO.LOW)
        time.sleep(0.001)
        
    
    def display_pattern(self, pattern_id):
        with self.mLock:
            if pattern_id < len(self.current_images):
                image = self.current_images[pattern_id]
                self.display.blit(image, (0, 0))  # Draw the image to the display
                #pygame.display.flip()  # Refresh the display seems not work
                pygame.display.update()
            else:
                print("Pattern ID out of range")
    
    def change_wavelength(self, wavelength):
        if wavelength == 488:
            self.current_images = self.loader.images_488
        elif wavelength == 635:
            self.current_images = self.loader.images_635
        else:
            print("Unsupported wavelength")
            
    def start(self): # how to deal with it
        self.isRunningContinous = True
        def runPatternDisplayThreadFunction():
            while(self.isRunningContinous):
                for i in range(len(self.current_images)):
                    if not self.isRunningContinous: break
                    self.display_pattern(i)
                    self.trigger()
                    print(str(i))
                    time.sleep(self.tWait)
        #threading.Thread(target=runPatternDisplayThreadFunction).start()
        #runPatternDisplayThreadFunction()
        
    def start_single_loop(self, cycle):
        # display each pattern once and perform a trigger action
        print("Start Single Loop: "+str(cycle))
        for cyc in range(cycle):
            for i in range(len(self.current_images)):
                self.display_pattern(i)
                self.trigger()
                print(str(i))
                time.sleep(self.tWait)

        
@app.get("/display_pattern/{pattern_id}")
async def display_pattern(pattern_id: int):
    viewer_controller.display_pattern(pattern_id)
    return {"message": f"Displaying pattern {pattern_id}."}

@app.get("/start_viewer/")
async def start_viewer():
    #def startContinousFct():
    #    viewer_controller.send_command("start")
    #threading.Thread(target=startContinousFct).start()
    #startContinousFct()
    viewer_controller.display_continous()
    return {"message": "Viewer started."}

@app.get("/stop_viewer/")
async def stop_viewer():
    viewer_controller.send_stop_continous()
    return {"message": "Viewer stopped."}

# Corresponding FastAPI endpoint
@app.get("/change_wavelength/{wavelength}")
async def change_wavelength(wavelength: int):
    viewer_controller.change_wavelength(wavelength)
    return {"message": f"Wavelength changed to {wavelength}nm."}

@app.get("/start_viewer_single_loop/{i_cycle}")
async def start_viewer_single_loop(i_cycle: int):
    viewer_controller.start_single_loop(i_cycle)
    #response = viewer_controller.send_command_and_receive("start_single_loop")
    return {"message": "Viewer started in single loop mode."}

@app.get("/set_wait_time/{tWait}") # fix it
async def set_wait_time(tWait: float):
    viewer_controller.set_wait_time(tWait)
    return {"message": f"Wait time set to {tWait}."}

# Implement other endpoints similarly, using viewer_controller to send appropriate commands

PATH_488 = "/home/pi/Desktop/Pattern_SIMMO/488"
PATH_635 = "/home/pi/Desktop/Pattern_SIMMO/635"
DISPLAY_SIZE = (1920, 1080)  

import threading
if __name__ == "__main__":
    def startServer():
        uvicorn.run(app, host="0.0.0.0", port=8000)
    
    def startViewer():
        viewer = PygameViewer(DISPLAY_SIZE, PATH_488, PATH_635)
        viewer.run()        
    threading.Thread(target=startServer).start()
    startViewer()
    
    
    
    