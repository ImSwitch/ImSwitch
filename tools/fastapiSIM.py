import uvicorn
from fastapi import FastAPI
import numpy as np
from starlette.responses import StreamingResponse
import pygame
import numpy as np
import RPi.GPIO as GPIO
import time
import os

pygame.init()

# screen resolution
mResolution = [640, 360]
unitCellSize = 3
mUnitCells = []
camTriggerPin = 26

# Announce the trigger pin
GPIO.setmode(GPIO.BCM)
GPIO.setup(camTriggerPin, GPIO.OUT)

# Create a list of unit cells
mUnitCell = np.ones((unitCellSize*2,unitCellSize*2))
mUnitCell[:,0:unitCellSize] = 0
mUnitCells.append(mUnitCell)

xx = mResolution[0]//mUnitCell.shape[0]+1
yy = mResolution[1]//mUnitCell.shape[1]+1

# initialize the display
display = pygame.display.set_mode(mResolution,pygame.FULLSCREEN)
myimg = np.tile(mUnitCell,(xx*2,yy*2))
myimg = myimg[:mResolution[0],:mResolution[1]]
surf = pygame.surfarray.make_surface(myimg*255)
pygame.mouse.set_visible(False)

app = FastAPI()

@app.get("/{inputNumber}")
async def get_image(inputNumber: int):
    print(inputNumber)
    global surf
    display.blit(surf, (0, 0))
    pygame.display.update()
    myrot = inputNumber//4
    if (myrot%2==0):
        mUnitCell = np.ones((unitCellSize*2,unitCellSize*2))
        mUnitCell[0:unitCellSize,:] = 0
        myimg = np.tile(mUnitCell,(xx*2,yy*2))
        myimg = myimg[:mResolution[0],:mResolution[1]]
        myimg = np.roll(myimg,inputNumber%4,axis=0)
    else:
        mUnitCell = np.ones((unitCellSize*2,unitCellSize*2))
        mUnitCell[:,0:unitCellSize] = 0
        myimg = np.tile(mUnitCell,(xx*2,yy*2))

    surf = pygame.surfarray.make_surface(myimg*255)
    GPIO.output(camTriggerPin,True)
    time.sleep(0.01)
    GPIO.output(camTriggerPin,False)
    myrot = inputNumber//4
    
    # Return image as StreamingResponse
    return {"success": inputNumber}

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)

