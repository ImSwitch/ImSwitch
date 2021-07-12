"""
Created on Sun Dec 06 20:14:02 2015

Downloaded from:
https://github.com/wavefrontshaping/slmPy

Converted to PyQt5 for ImSwitch.

@author: Sebastien Popoff
"""

import time

import numpy as np
import skimage
import skimage.transform
from qtpy import QtCore, QtGui, QtWidgets

from imswitch.imcommon.framework import Mutex


class SLMdisplay:
    """Interface for sending images to the display frame."""
    def __init__(self, monitor = 1, isImageLock = False):       
        self.isImageLock = isImageLock            
        self.monitor = monitor
        # Create the thread in which the window app will run
        # It needs its thread to continuously refresh the window
        self.eventLock = Mutex()
        if (self.isImageLock):
            self.eventLock = Mutex()

        self.frame = SLMframe(monitor = self.monitor, isImageLock = self.isImageLock)
        self.frame.show()
        
    def getSize(self):
        return self.frame._resX, self.frame._resY

    def updateArray(self, mask):
        """
        Update the SLM monitor with the supplied array.
        Note that the array is not the same size as the SLM resolution,
        the image will be deformed to fit the screen.
        """
        self.array = mask.image()

        # Padding: Like they do in the software
        pad = np.zeros((600, 8), dtype=np.uint8)
        self.array = np.append(self.array, pad, 1)

        #create a wx.Image from the array
        h,w = self.array.shape[0], self.array.shape[1]

        if len(self.array.shape) == 2:
            bw_array = self.array.copy()
            bw_array.shape = h, w, 1
            img = np.concatenate((bw_array,bw_array,bw_array), axis=2)
        else:
            img = self.array

        # Wait for the lock to be released (if isImageLock = True)
        # to be sure that the previous image has been displayed
        # before displaying the next one - it avoids skipping images
        if (self.isImageLock):
            self.eventLock.lock()
        # Wait (can bug when closing/opening the SLM too quickly otherwise)
        time.sleep(0.5)
        # Trigger the event (update image)
        self.frame.sigNewImage.emit(img, False, None, self.eventLock)
        
    def close(self):
        self.frame.close()


class SLMframe(QtWidgets.QLabel):
    sigNewImage = QtCore.Signal(object, bool, object, object)  # (img, color, oldImageLock, eventLock)

    """Frame used to display full screen image."""
    def __init__(self, monitor, isImageLock = True):   
        self.isImageLock = isImageLock
        # Create the frame
        super().__init__()
        self.SetMonitor(monitor)
        # Set the frame to the position and size of the target monitor
        self.setWindowTitle('SLM window')
        self.img = np.zeros((2,2))
        self.clientSize = self._resX, self._resY
        # Update the image upon receiving an event EVT_NEW_IMAGE
        self.sigNewImage.connect(self.UpdateImage)
        # Set full screen
        self.showFullScreen()
        self.setFocus()

    def InitBuffer(self):
        self.clientSize = self._resX, self._resY
        self.bmp = skimage.img_as_ubyte(
            skimage.transform.resize(self.img, (self.clientSize[1], self.clientSize[0]))
        )
        qimage = QtGui.QImage(
            self.bmp, self.bmp.shape[1], self.bmp.shape[0], self.bmp.shape[1] * 3,
            QtGui.QImage.Format_RGB888
        )
        qpixmap = QtGui.QPixmap(qimage)
        self.setPixmap(qpixmap)
        
    def UpdateImage(self, img, color, oldImageLock, eventLock):
        self.eventLock = eventLock
        self.img = img
        self.InitBuffer()
        self.ReleaseEventLock()
        
    def ReleaseEventLock(self):
        if self.eventLock:
            self.eventLock.tryLock()
            self.eventLock.unlock()
        
    def SetMonitor(self, monitor):
        app = QtWidgets.QApplication.instance()
        screens = app.screens()

        tryMonitor = monitor

        while tryMonitor > len(screens) - 1:
            tryMonitor -= 1  # Try other monitor

        if tryMonitor < 0:
            raise ValueError('Invalid monitor (monitor %d).' % monitor)

        screenSize = screens[tryMonitor].size()
        self._x0 = 0
        self._y0 = 0
        self._resX = screenSize.width()
        self._resY = screenSize.height()


# Copyright (C) 2020, 2021 TestaLab
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
