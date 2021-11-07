import numpy as np
mainWindow.setCurrentModule('imcontrol')

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