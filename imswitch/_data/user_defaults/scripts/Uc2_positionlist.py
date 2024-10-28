import numpy as np
import time
import threading
mainWindow.setCurrentModule('imcontrol')

api.imcontrol.enalbeMotors(None, False)
# x,y,z
positions = [(0, 0, 0),
			(0, 10, 0),
			(0, 100, 0),
			(10, 100, 0),
			(100, 0, 0)]

positionerName = api.imcontrol.getPositionerNames()[0]
print(api.imcontrol.getPositionerPositions())

for position in positions:
	# X
	posX = position[0]
	api.imcontrol.movePositioner(positionerName, "X", posX, True, True)
	# Y
	posY = position[1]
	api.imcontrol.movePositioner(positionerName, "Y", posY, True, True)
	#Z
	posZ = position[2]
	api.imcontrol.movePositioner(positionerName, "Z", posZ, True, True)

	api.imcontrol.snapImageToPath(str(position)+"_posscreening")
