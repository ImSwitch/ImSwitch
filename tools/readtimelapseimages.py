# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 10:44:29 2023

@author: UC2
"""
import os
import numpy as np
import tifffile as tif
import cv2
import glob, os
mPath = '.\\ImSwitch\\ImSwitch\\recordings\\2023-02-21\\'
mPath = 'C:\\Users\\UC2\\Documents\\ImSwitchConfig\\recordings\\2023_03_06-10-39-29_AM\\'

mFolders = sorted(glob.glob(mPath+"*"), key=os.path.getmtime)
mAllfiles = []

for iFolder in mFolders:
	for file in glob.glob(iFolder+"\*.tif"):
		print(iFolder)
		tif.imwrite(os.path.join(mPath,"file.tif"), cv2.resize(tif.imread(file), dsize=None, fx=.25, fy=.25), append=True)
        
