import uvicorn
from fastapi import FastAPI, BackgroundTasks
import numpy as np
import pygame
import time
import os
import socket
from os import listdir
from os.path import isfile, join
from threading import Event


'''
import requests
x = requests.get('http://localhost:8000/stopLoop')
print(x.text)
'''

# Configure GPIO if running on Raspberry Pi
try:
    import RPi.GPIO as GPIO
except:
    print("Not running on Pi")
    GPIO = None

# Screen resolution
mResolution = [1920, 1080]
mResolution = [800, 600]
unitCellSize = 3
camTriggerPin = 26
currentWavelength = 0  # 488=0, 635=1
nImages = 9
camTriggerPin = 37
iFreeze = False
iPattern = 0
task_lock = True
iter = True
iLoop = True
iCycle = 100
TaskCompleted = False
    
if GPIO is not None:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(camTriggerPin, GPIO.OUT)
    
# Images path
try:
    mypath488 = "/home/pi/Desktop/Pattern_SIMMO/488"
    mypath635 = "/home/pi/Desktop/Pattern_SIMMO/635"
    # for windows debug
    #mypath488 = "C:\\Users\\admin\\Documents\\ImSwitchConfig\\imcontrol_sim\\488"
    #mypath635 = mypath488 # for windows debugging
    myimg488 = [f for f in listdir(mypath488) if isfile(join(mypath488, f))]
    myimg635 = [f for f in listdir(mypath635) if isfile(join(mypath635, f))]
    myimg488.sort()
    myimg635.sort()
except:
    pass

def load_images(wl: int):
    images = []
    global isGenerateImage, iNumber
    try:
        if wl == 488:    
            for i in range(nImages):
                images.append(pygame.image.load(join(mypath488, myimg488[i])))
        elif wl == 635:
            for i in range(nImages):
                images.append(pygame.image.load(join(mypath635, myimg635[i])))
        print("Found patterns")
    except:
        R_img = list(np.random.rand(nImages, mResolution[0], mResolution[1])*255)
        for i in range(nImages):
                images.append(pygame.surfarray.make_surface(np.int8(R_img[i])))
        isGenerateImage = True
        print("Not found the patterns, using random patterns")
    return images

mImages488 = load_images(488)
mImages635 = load_images(635)

class Viewer:
    def __init__(self, update_func, display_size):
        self.update_func = update_func
        self.pattern_index = 0
        pygame.init()
        pygame.mouse.set_visible(False)
        self.display = pygame.display.set_mode(display_size,  display=0) #pygame.FULLSCREEN,
        self.tWait = 0.05
        self.clock = pygame.time.Clock()
        global camTriggerPin, nImages, iLoop, iCycle
        self.camPin = camTriggerPin
        self.iNumber = nImages
        self.iLoop = iLoop
        self.iCycle = iCycle
        self.viewer_completed_event = Event()
    
    def set_title(self, title):
        pygame.display.set_caption(title)
    
    def set_twait(self, tWait):
        self.tWait = tWait
    
    def set_loop(self, iLoop):
        self.iLoop = iLoop
    
    def set_cycle(self, iCycle):
        self.iCycle = iCycle
        
    def trigger(self, gpiopin):
        GPIO.output(gpiopin, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(gpiopin, GPIO.LOW)
        time.sleep(0.001)
        
    def start(self):
        running = True
        irun = 0
        global iCycle, iLoop, TaskCompleted
        while running:
            surf = self.update_func(self.pattern_index)
            if not iLoop:
                if self.pattern_index == 8:
                    irun += 1
            self.pattern_index = (self.pattern_index + 1) % self.iNumber
            #surf = pygame.surfarray.make_surface(Z)
            self.display.blit(surf, (0, 0))
            pygame.display.update()
            self.clock.tick()
            print(self.clock.get_fps())
            #self.trigger(self.camPin)
            time.sleep(self.tWait)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:  # Press 'q' to quit
                        pygame.display.quit()
                        running = False
                        global task_lock
                        task_lock = True
            if irun >= iCycle:
                running = False
                pygame.display.quit()
                task_lock = True
                self.viewer_completed_event.set()

def update(index):
    global currentWavelength
    global iPattern
    if iFreeze == False:
        images = mImages488 if currentWavelength == 0 else mImages635
        #pattern = np.uint8(images[index])
        pattern = images[index]
    else:
        images = mImages488[iPattern] if currentWavelength == 0 else mImages635[iPattern]
        pattern = images
    return pattern

def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Hostname: {hostname}")
    print(f"IP Address: {ip_address}")
    print(f"Port: 80")
    return ip_address

# Call the function to print the IP address
get_ip_address()
    
app = FastAPI()
viewer = None

def run_viewer():
    global viewer
    viewer = Viewer(update, mResolution)
    viewer.start()

@app.get("/start_viewer/")
async def start_viewer(background_tasks: BackgroundTasks):
    global iFreeze, task_lock, iLoop, viewer
    if task_lock:
        background_tasks.add_task(run_viewer)
        task_lock = False
        
    iFreeze = False
    iLoop = True

    return {"message": "Viewer started."}

@app.get("/start_viewer_freeze/{i}")
async def start_viewer_freeze(background_tasks: BackgroundTasks, i:int):
    global iFreeze, iPattern, task_lock, iLoop, viewer
    if task_lock:
        background_tasks.add_task(run_viewer)
        task_lock = False
    
    iFreeze = True 
    iLoop = True
    iPattern = i
    return {"message": "show certain pattern."}

# it only works without pygame opened
@app.get("/start_viewer_single_loop/{i_cycle}")
async def start_viewer_single_loop(background_tasks: BackgroundTasks, i_cycle:int):
    global iFreeze, task_lock, viewer, iCycle, iLoop
    if task_lock:
        background_tasks.add_task(run_viewer)
        task_lock = False    
    iFreeze = False
    iLoop = False
    iCycle = i_cycle
    return {"message": "run certain cycle."}

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

@app.get("/wait_for_viewer_completion")
async def wait_for_viewer_completion():
    viewer.viewer_completed_event.wait()  # Wait for viewer completion
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
