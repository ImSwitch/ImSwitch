import uvicorn
from fastapi import FastAPI, BackgroundTasks
import numpy as np
import pygame
import time
import os
import socket

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
mResolution = [800, 600]
unitCellSize = 3
camTriggerPin = 26
currentWavelength = 0  # 488=0, 635=1
nImages = 9
camTriggerPin = 37
    
if GPIO is not None:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(camTriggerPin, GPIO.OUT)
    
# Images path
try:
    mypath488 = "/home/pi/Desktop/Pattern_SIMMO/488"
    mypath635 = "/home/pi/Desktop/Pattern_SIMMO/635"
    myimg488 = [f for f in listdir(mypath488) if isfile(join(mypath488, f))]
    myimg635 = [f for f in listdir(mypath635) if isfile(join(mypath635, f))]
    myimg488.sort()
    myimg635.sort()
except:
    pass

def load_images(wl: int):
    images = []
    global isGenerateImage
    try:
        if wl == 488:    
            for i in range(nImages):
                images.append(pygame.image.load(join(myimg488, myimg488[i])))
        elif wl == 635:
            for i in range(nImages):
                images.append(pygame.image.load(join(myimg635, myimg635[i])))
    except:
        images = list(np.random.rand(nImages, mResolution[0], mResolution[1]))
        isGenerateImage = True
    return images

mImages488 = load_images(488)
mImages635 = load_images(635)

class Viewer:
    def __init__(self, update_func, display_size):
        self.update_func = update_func
        self.pattern_index = 0
        pygame.init()
        pygame.mouse.set_visible(False)
        self.display = pygame.display.set_mode(display_size, display=0)
        self.tWait = 0.01
        self.clock = pygame.time.Clock()
        global camTriggerPin
        self.camPin = camTriggerPin
    
    def set_title(self, title):
        pygame.display.set_caption(title)
    
    def set_twait(self, tWait):
        self.tWait = tWait
        
    def trigger(self, gpiopin):
        GPIO.output(gpiopin, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(gpiopin, GPIO.LOW)
        print("fire!")
        time.sleep(0.001)
        
    def start(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            Z = self.update_func(self.pattern_index)
            self.pattern_index = (self.pattern_index + 1) % len(mImages488)
            surf = pygame.surfarray.make_surface(Z)
            self.display.blit(surf, (0, 0))
            pygame.display.update()
            self.clock.tick()
            print(self.clock.get_fps())
            self.trigger(self.camPin)
            time.sleep(self.tWait)
        pygame.quit()

def update(index):
    global currentWavelength
    images = mImages488 if currentWavelength == 0 else mImages635
    pattern = np.uint8(images[index] * 255)

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
    background_tasks.add_task(run_viewer)
    return {"message": "Viewer started."}

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
