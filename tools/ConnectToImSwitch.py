#%%
!pip install https://github.com/openUC2/imswitchclient/archive/refs/heads/main.zip
#%%
import imswitchclient.ImSwitchClient as imc 
import numpy as np
import matplotlib.pyplot as plt
import time

# Initialize the client
client = imc.ImSwitchClient(host="192.168.137.1", isHttps=True, port=8002)

#%%
# Retrieve the first positioner's name and current position
positioner_names = client.positionersManager.getAllDeviceNames()
positioner_name = positioner_names[0]
print(positioner_name)

#%%
lastFrame = client.recordingManager.snapNumpyToFastAPI(0.5)
plt.imshow(lastFrame)
plt.show()

#%%
currentPositions = client.positionersManager.getPositionerPositions()[positioner_name]
initialPosition = (currentPositions["X"], currentPositions["Y"])
print(initialPosition)
#%%

# turn on illumination
mLaserName = client.lasersManager.getLaserNames()[0]
client.lasersManager.setLaserActive(mLaserName, True)
client.lasersManager.setLaserValue(mLaserName, 512)

#%%
dMove = 1000
for ix in range(3):
    for iy in range(3):
        # Define and move to a new position
        newPosition = (initialPosition[0] + ix*dMove, initialPosition[1] + iy*dMove)
        client.positionersManager.movePositioner(positioner_name, "X", newPosition[0], is_absolute=True, is_blocking=True)
        client.positionersManager.movePositioner(positioner_name, "Y", newPosition[1], is_absolute=True, is_blocking=True)
        
        # Acquire and display an image
        #time.sleep(0.5)  # Allow time for the move
        lastFrame = client.recordingManager.snapNumpyToFastAPI(0.2)
        plt.imshow(lastFrame)
        plt.show()
        
        newX, newY = process(lastFrame)
        
# Return the positioner to its initial position
client.positionersManager.movePositioner(positioner_name, "X", initialPosition[0], is_absolute=True, is_blocking=True)
client.positionersManager.movePositioner(positioner_name, "Y", initialPosition[1], is_absolute=True, is_blocking=True)

# %%
