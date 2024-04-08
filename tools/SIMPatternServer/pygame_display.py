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

# Part of the FastAPI application

class ViewerController:
    def __init__(self):
        self.context = zmq.Context()
        # Use REQ socket for request-reply pattern
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("tcp://localhost:"+str(ZMQPORT))
    
    def send_command(self, command):
        self.socket.send_string(command)
        
    def send_command_and_receive(self, command):
        self.socket.send_string(command)
        # Block until a reply is received
        message = self.socket.recv_string()
        return message
    
    def display_pattern(self, pattern_id):
        self.send_command(f"display:{pattern_id}")

    def change_wavelength(self, wavelength):
        self.send_command(f"change_wavelength:{wavelength}")

viewer_controller = ViewerController()

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


class PygameViewer:
    def __init__(self, display_size, path_488, path_635):
        self.display_size = display_size
        self.loader = ImageLoader(path_488, path_635)
        # Initialization of pygame and zmq as before
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("tcp://localhost:"+str(ZMQPORT))
        self.current_images = self.loader.images_488  # Default to 488nm images
        self.tWait = 0  # Default time to wait between patterns
    
    def run(self):
        pygame.init()
        self.display = pygame.display.set_mode(self.display_size)#, pygame.FULLSCREEN)
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
                    message = self.socket.recv_string()
                    reply = self.handle_message(message)
                    # Send reply back to client
                    self.socket.send_string(reply)

                except zmq.Again:
                    pass  # No message received

                pygame.display.flip()  # Update the full display surface to the screen
                pygame.time.wait(20)  # Small delay to prevent high CPU usage
    
    def handle_message(self, message):
        response = ""
        if message.startswith("display:"):
            pattern_id = int(message.split(":")[1])
            self.display_pattern(pattern_id)
        elif message.startswith("change_wavelength:"):
            wavelength = int(message.split(":")[1])
            self.change_wavelength(wavelength)
        elif message == "stop":
            self.running = False
        elif message == "start_single_loop":
            self.start_single_loop()
            response = "Current pattern info or any other data"
        return response
    
    def trigger(self):
        # Perform trigger action
        pass
    
    def display_pattern(self, pattern_id):
        if pattern_id < len(self.current_images):
            image = self.current_images[pattern_id]
            self.display.blit(image, (0, 0))  # Draw the image to the display
            pygame.display.flip()  # Refresh the display
        else:
            print("Pattern ID out of range")
    
    def change_wavelength(self, wavelength):
        if wavelength == 488:
            self.current_images = self.loader.images_488
        elif wavelength == 635:
            self.current_images = self.loader.images_635
        else:
            print("Unsupported wavelength")

    def start_single_loop(self):
        # display each pattern once and perform a trigger action
        for i in range(len(self.current_images)):
            self.display_pattern(i)
            self.trigger()
            time.sleep(self.tWait)
        

PATH_488 = "/Users/bene/ImSwitchConfig/imcontrol_sim/488"
PATH_635 = "/Users/bene/ImSwitchConfig/imcontrol_sim/635"
DISPLAY_SIZE = (1920, 1080)  


if __name__ == "__main__":
    def startViewer():
        viewer = PygameViewer(DISPLAY_SIZE, PATH_488, PATH_635)
        viewer.run()        
    startViewer()
    
    
    
    