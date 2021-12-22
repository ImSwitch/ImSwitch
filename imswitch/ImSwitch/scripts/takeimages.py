mainWindow.setCurrentModule('imcontrol')
import time
time.sleep(1)
for i in range(200):
	api.imcontrol.snapImage() 
	print(i)