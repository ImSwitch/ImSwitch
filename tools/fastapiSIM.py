import uvicorn
from fastapi import FastAPI
import numpy as np
import pygame
import threading
import time
import os

try:
    import RPi.GPIO as GPIO
except:
    print("Not running on Pi")
    GPIO = None

pygame.init()

# Screen resolution
mResolution = [1920, 1080]
unitCellSize = 3
camTriggerPin = 26
currentWavelength = 0  # 488=0, 635=1

# Configure GPIO if running on Raspberry Pi
if GPIO is not None:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(camTriggerPin, GPIO.OUT)

# Create a unit cell
mUnitCell = np.ones((unitCellSize * 2, unitCellSize * 2))
mUnitCell[:, 0:unitCellSize] = 0

xx = mResolution[0] // mUnitCell.shape[0] + 1
yy = mResolution[1] // mUnitCell.shape[1] + 1

# Initialize display
fullscreen = False
display = pygame.display.set_mode(mResolution)
myimg = np.tile(mUnitCell, (xx * 2, yy * 2))
myimg = myimg[:mResolution[0], :mResolution[1]]
surf = pygame.surfarray.make_surface(myimg * 255)
pygame.mouse.set_visible(False)

app = FastAPI()

tPause = 0.1
nImages = 9
isLooping = False
isGenerateImage = False

# Read images from a folder or generate random ones if not found
def load_images():
    images = []
    try:
        for i in range(nImages):
            images.append(pygame.image.load("images/image" + str(i) + ".png"))
    except:
        images = list(np.random.rand(nImages, mResolution[0], mResolution[1]))
    return images

mImages488 = load_images()
mImages635 = load_images()
# Combine image stacks
mImages = np.stack((np.array(mImages488), np.array(mImages635)), axis=0)

# Function to loop through images
def imageLooper():
    while isLooping:
        for i in range(nImages):
            get_image(i)
            time.sleep(tPause)

# Endpoint to start the loop
@app.get("/startLoop")
async def startLoop():
    global isLooping
    isLooping = True
    print("Start the loop")
    threading.Thread(target=imageLooper).start()

# Endpoint to stop the loop
@app.get("/stopLoop")
async def stopLoop():
    global isLooping
    print("Stop the loop")
    isLooping = False

# Endpoint to set pause time
@app.get("/set_pause/{pauseTime}")
async def set_pause(pauseTime: float):
    global tPause
    tPause = pauseTime
    return {"pauseTime": tPause}

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

# Function to generate a pattern based on inputNumber
def generatePattern(inputNumber):
    # ... pattern generation code ...
    return myimg

# Function to get image
def get_image(inputNumber: int):
    global currentWavelength, surf, isGenerateImage
    print(inputNumber)
    display.blit(surf, (0, 0))
    pygame.display.update()

    if isGenerateImage:
        myimg = generatePattern(inputNumber)
    else:
        # Read images from list
        myimg = mImages488[inputNumber] if currentWavelength == 0 else mImages635[inputNumber]

    surf = pygame.surfarray.make_surface(myimg * 255)

    if GPIO is not None:
        GPIO.output(camTriggerPin, True)
        time.sleep(0.01)
        GPIO.output(camTriggerPin, False)

    return {"success": inputNumber}

# Endpoint to get image based on inputNumber
@app.get("/{inputNumber}")
async def get_image_async(inputNumber: int):
    return get_image(inputNumber)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
