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



class ViewerController:
    def __init__(self):
        self.context = zmq.Context()
        # Use REQ socket for request-reply pattern
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind("tcp://*:"+str(ZMQPORT))
    
    def send_command(self, command):
        try:self.socket.send_string(command, zmq.DONTWAIT)
        except Exception as e: print(f"Failed to send command: {e}")
        
    def send_command_and_receive(self, command):
        self.socket.send_string(command)
        # Block until a reply is received
        message = self.socket.recv_string()
        return message
    
    def display_pattern(self, pattern_id):
        self.send_command(f"display:{pattern_id}")

    def change_wavelength(self, wavelength):
        self.send_command(f"change_wavelength:{wavelength}")

# Part of the FastAPI application
app = FastAPI()
viewer_controller = ViewerController()

@app.get("/display_pattern/{pattern_id}")
async def display_pattern(pattern_id: int):
    viewer_controller.display_pattern(pattern_id)
    return {"message": f"Displaying pattern {pattern_id}."}

@app.get("/start_viewer/")
async def start_viewer():
    viewer_controller.send_command("start")
    return {"message": "Viewer started."}

@app.get("/stop_viewer/")
async def stop_viewer():
    viewer_controller.send_command("stop")
    return {"message": "Viewer stopped."}


# Corresponding FastAPI endpoint
@app.get("/change_wavelength/{wavelength}")
async def change_wavelength(wavelength: int):
    viewer_controller.change_wavelength(wavelength)
    return {"message": f"Wavelength changed to {wavelength}nm."}

@app.get("/start_viewer_single_loop/{i_cycle}")
async def start_viewer_single_loop(wavelength: int):
    viewer_controller.change_wavelength(wavelength)
    response = viewer_controller.send_command_and_receive("start_single_loop")
    return {"message": "Viewer started in single loop mode."}


# Implement other endpoints similarly, using viewer_controller to send appropriate commands

PATH_488 = "/Users/bene/ImSwitchConfig/imcontrol_sim/488"
PATH_635 = "/Users/bene/ImSwitchConfig/imcontrol_sim/635"
DISPLAY_SIZE = (1920, 1080)  

import threading
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    