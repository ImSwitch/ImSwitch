import numpy as np
import time
import threading
import os
import cv2
import tifffile as tif
#mainWindow.setCurrentModule('imcontrol')

api.imcontrol.enalbeMotors(None, False)
# x,y,z
positions = [(54000, 6500, -200),
				(54000, 7250, -200),
				(55000, 7250, -200),
				(55000, 6500, -200),
				(59750, 6500, 0),
				(59750, 4600, 0),
				(60500, 4600, 0),
				(60500, 3600, 0),
				(62500, 3600, 0),
				(62500, 5600, 0),
				(63000, 5600, 0)]

positionerName = api.imcontrol.getPositionerNames()[0]
print(api.imcontrol.getPositionerPositions())
api.imcontrol.setPositionerSpeed(positionerName, "X", 20000)
api.imcontrol.setPositionerSpeed(positionerName, "Y", 20000)
api.imcontrol.setPositionerSpeed(positionerName, "Z", 20000)

#api.imcontrol.homeAxis(positionerName, "X")
#api.imcontrol.homeAxis(positionerName, "Y")
#time.sleep(15)
# move to inital position

mPixelSize = 0.327 # mum
mFrameShape = api.imcontrol.snapImage(True, False).shape

xDim = mFrameShape[1]*mPixelSize
yDim = mFrameShape[0]*mPixelSize
mOverlap = 0.9 # 90% overlap at  the edges

print(xDim)
print(yDim)
mPath = r"C:\\Users\\T490\\Documents\\Anabel\\Bachelorarbeit\\Bilder\\"
LEDName = "LED"
api.imcontrol.setLaserValue(LEDName, 1023)
api.imcontrol.setLaserActive(LEDName, True)
time.sleep(0.5)
#a record dummy frame
ix=iy=0
mPos = (ix*xDim*mOverlap+58000,
 iy*yDim*mOverlap+23000)
api.imcontrol.movePositioner(positionerName, "XY", mPos, True, True)
mFrame = api.imcontrol.snapImage(True, False)

#raster
iiter = 0
for ix in range(2):
	for iy in range(2):
		mPos = (ix*xDim*mOverlap+58000,
		 iy*yDim*mOverlap+23000)
		
		api.imcontrol.movePositioner(positionerName, "XY", mPos, True, True)
		time.sleep(0.5)
		# api.imcontrol.snapImageToPath(str(ix)+"_"+str(iy))
		mFrame = api.imcontrol.snapImage(True, False)
		tif.imsave(mPath+str(iiter)+"_("+str(int(mPos[0]))+", "+str(int(mPos[1]))+")"+".tif", mFrame)
		iiter +=1
#
#def doScanning():
	#iiter = 0
	#while 1:
		#iPos = 0
		#for position in positions:
			#print(position)
			#posX = position[0]
			#api.imcontrol.movePositioner(positionerName, "X", posX, True, True)
			# Y
			#posY = position[1]
			#api.imcontrol.movePositioner(positionerName, "Y", posY, True, True)
			#Z
			#posZ = position[2]
			#api.imcontrol.movePositioner(positionerName, "Z", posZ, True, True)

			#time.sleep(1)

			#api.imcontrol.snapImageToPath(str(iPos)+"_posscreening")
			#iPos +=1
		#time.sleep(60)
		#iiter +=1
		#print(iiter)

#doScanning()


#labyrinth ablaufen
#def doScanning():
    #iPos = 0
    #for position in positions:
    #    posX, posY, posZ = position
        
    #    api.imcontrol.movePositioner(positionerName, "X", posX, True, True)
    #    api.imcontrol.movePositioner(positionerName, "Y", posY, True, True)
    #    api.imcontrol.movePositioner(positionerName, "Z", posZ, True, True)

    #    time.sleep(1)

    #    api.imcontrol.snapImageToPath(str(iPos)+"_posscreening")
    #    iPos += 1
	#time.sleep(60)

#doScanning()
