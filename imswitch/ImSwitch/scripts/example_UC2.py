import numpy as np
import time

mainWindow.setCurrentModule('imcontrol')

laserName = api.imcontrol.getLaserNames()
positioner = api.imcontrol.getPositionerNames()

#api.imcontrol.setLaserActive(laserName, True)
N_images = 40
dz = 1
axis = "Z"
api.imcontrol.movePositioner(positioner[0], axis, -N_images*dz/2)

for i_pos in range(N_images):
	api.imcontrol.movePositioner(positioner[0], axis, dz)
	time.sleep(1)
	api.imcontrol.snapImage() 
	
api.imcontrol.movePositioner(positioner[0], axis, -N_images*dz/2)



'''
values_405 = np.array([0, 0, 0, 0, 5, 10, 25, 50, 100, 200])
lasername_405 = api.imcontrol.getLaserNames()[0]

# Start Recording
api.imcontrol.startRecording()
for i in values_405:
	# Set Laser Value
	api.imcontrol.changeScanPower(lasername_405, i)
	# Run Scan
	api.imcontrol.runScan()
	# Wait for finish
	waitForScanningToEnd = getWaitForSignal(api.imcontrol.signals().scanEnded)
	waitForScanningToEnd()
	
api.imcontrol.stopRecording()'''