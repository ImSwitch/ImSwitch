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

class ViewerManager:
    def __init__(self):
        self.mResolution = [1920, 1080]
        self.camTriggerPin = 26
        self.currentWavelength = 0  # 488=0, 635=1
        self.nImages = 9
        self.iFreeze = False
        self.iPattern = 0
        self.iLoop = True
        self.iCycle = 100
        self.GPIO = None
        self.task_lock = True
        self.viewer_completed_event = Event()

        self.mypath488 = "/home/pi/Desktop/Pattern_SIMMO/488"
        self.mypath635 = "/home/pi/Desktop/Pattern_SIMMO/635"
        self.myimg488 = []
        self.myimg635 = []

        self.mImages488 = []
        self.mImages635 = []

        try:
            self.myimg488 = [f for f in listdir(self.mypath488) if isfile(join(self.mypath488, f))]
            self.myimg635 = [f for f in listdir(self.mypath635) if isfile(join(self.mypath635, f))]
            self.myimg488.sort()
            self.myimg635.sort()
        except:
            pass

        self.load_images()

    def load_images(self):
        try:
            for i in range(self.nImages):
                self.mImages488.append(pygame.image.load(join(self.mypath488, self.myimg488[i])))
                self.mImages635.append(pygame.image.load(join(self.mypath635, self.myimg635[i])))
            print("Found patterns")
        except:
            R_img = list(np.random.rand(self.nImages, self.mResolution[0], self.mResolution[1])*255)
            for i in range(self.nImages):
                self.mImages488.append(pygame.surfarray.make_surface(np.int8(R_img[i])))
                self.mImages635.append(pygame.surfarray.make_surface(np.int8(R_img[i])))
            print("Not found the patterns, using random patterns")

    def trigger_pin(self, gpiopin):
        if self.GPIO is not None:
            self.GPIO.output(gpiopin, self.GPIO.HIGH)
            time.sleep(0.001)
            self.GPIO.output(gpiopin, self.GPIO.LOW)
            time.sleep(0.001)

viewer_manager = ViewerManager()
app = FastAPI()

class Viewer:
    def __init__(self, update_func, display_size, viewer_manager):
        self.update_func = update_func
        self.pattern_index = 0
        os.environ["DISPLAY"] = ":0"
        pygame.display.init()
        pygame.init()
        pygame.mouse.set_visible(False)
        self.display = pygame.display.set_mode(display_size, pygame.FULLSCREEN, display=0)
        self.tWait = 0.1
        self.clock = pygame.time.Clock()
        self.viewer_manager = viewer_manager

    def trigger(self):
        self.viewer_manager.trigger_pin(self.viewer_manager.camTriggerPin)

    def start(self):
        running = True
        irun = 0
        while running:
            surf = self.update_func(self.pattern_index)
            print("iPattern: "+ str(self.pattern_index))
            self.pattern_index = (self.pattern_index + 1) % self.viewer_manager.nImages
            self.display.blit(surf, (0, 0))
            pygame.display.update()
            self.trigger()
            time.sleep(self.tWait)
            if not self.viewer_manager.iLoop:
                if self.pattern_index == 0:
                    irun += 1
                    viewer_manager.viewer_completed_event.set()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:  # Press 'q' to quit
                        pygame.display.quit()
                        running = False
                        viewer_manager.task_lock = True
            if irun >= self.viewer_manager.iCycle:
                running = False
                pygame.display.quit()
                self.viewer_manager.task_lock = True
                #self.viewer_completed_event.set()

def update(index):
    if viewer_manager.iFreeze == False:
        images = viewer_manager.mImages488 if viewer_manager.currentWavelength == 0 else viewer_manager.mImages635
        pattern = images[index]
    else:
        images = viewer_manager.mImages488[viewer_manager.iPattern] if viewer_manager.currentWavelength == 0 else viewer_manager.mImages635[viewer_manager.iPattern]
        pattern = images
    return pattern

def start_viewer():
    viewer = Viewer(update, viewer_manager.mResolution, viewer_manager)
    viewer.start()

@app.get("/start_viewer/")
async def start_view(background_tasks: BackgroundTasks):
    if viewer_manager.task_lock:
        background_tasks.add_task(start_viewer)
        viewer_manager.task_lock = False
        
    viewer_manager.iFreeze = False
    viewer_manager.iLoop = True

    return {"message": "Viewer started."}

@app.get("/start_viewer_freeze/{i}")
async def start_viewer_freeze(background_tasks: BackgroundTasks, i:int):
    if viewer_manager.task_lock:
        background_tasks.add_task(start_viewer)
        viewer_manager.task_lock = False
    
    viewer_manager.iFreeze = True 
    viewer_manager.iLoop = True
    viewer_manager.iPattern = i
    return {"message": "show certain pattern."}

# it only works without pygame opened
@app.get("/start_viewer_single_loop/{i_cycle}")
async def start_viewer_single_loop(background_tasks: BackgroundTasks, i_cycle:int):
    if viewer_manager.task_lock:
        background_tasks.add_task(start_viewer)
        viewer_manager.task_lock = False    
    viewer_manager.iFreeze = False
    viewer_manager.iLoop = False
    viewer_manager.iCycle = i_cycle
    # wait until we count up until patterns are completed or timeout occurs
    viewer_manager.viewer_completed_event.clear()
    print("cleaned")
    #viewer_manager.viewer_completed_event.wait()
    return {"message": "run certain cycle."}

@app.get("/send_trigger")
async def send_trigger():
    viewer.trigger()
    
# Endpoint to set pause time
@app.get("/set_pause/{pauseTime}")
async def set_pause(pauseTime: float):
    viewer.set_twait(pauseTime)

# Endpoint to set wavelength
@app.get("/set_wavelength/{wavelength}")
async def set_wavelength(wavelength: int):
    global currentWavelength
    print("Set wavelength to " + str(wavelength))
    currentWavelength = wavelength
    return {"wavelength": currentWavelength}

@app.get("/run_cycle/{icycle}")
async def run_cycle(icycle: int):
    global iter
    iter = not iter
    return {"wavelength": currentWavelength}

@app.get("/stop_loop/")
async def stop_loop():
    viewer_manager.iLoop = False
    viewer_manager.iCycle = 1
    return {"message": "Loop stopped"}

@app.get("/wait_for_viewer_completion")
async def wait_for_viewer_completion():
    #viewer.viewer_completed_event.wait()  # Wait for viewer completion
    return {"message": "Viewer completed"}

# Endpoint to toggle fullscreen mode
@app.get("/toggle_fullscreen")
async def toggle_fullscreen():
    global fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        pygame.display.set_mode(mResolution, pygame.FULLSCREEN)
    else:
        pygame.display.set_mode(mResolution)
    return {"fullscreen": fullscreen}

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)