import numpy as np
import time

def snap_zstack(N_images=40, dz=2):
	axis = "Z"
	api.imcontrol.movePositioner(positioner[0], axis, -N_images*dz/2)

	for i_pos in range(N_images):
		api.imcontrol.movePositioner(positioner[0], axis, dz)
		time.sleep(.2)
		api.imcontrol.snapImage() 
	
	api.imcontrol.movePositioner(positioner[0], axis, -N_images*dz/2)

	
mainWindow.setCurrentModule('imcontrol')

laserName = api.imcontrol.getLaserNames()
positioner = api.imcontrol.getPositionerNames()

laser_488 = '488 Laser'
laser_635 = '635 Laser' 


# snap GFP
api.imcontrol.setLaserActive(laser_635, False)
api.imcontrol.setLaserActive(laser_488, True)

snap_zstack()
#api.imcontrol.snapImage() 

# snap AF647
api.imcontrol.setLaserActive(laser_488, False)
api.imcontrol.setLaserActive(laser_635, True)

#api.imcontrol.snapImage() 
snap_zstack()

# turn off lasers
api.imcontrol.setLaserActive(laser_488, False)
api.imcontrol.setLaserActive(laser_635, False)




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
	
api.imcontrol.stopRecording()
'''