"""
Created on Sun Dec 06 20:14:02 2015

Downloaded from:
https://github.com/wavefrontshaping/slmPy

@author: Sebastien Popoff
"""

try:
    import wx
except ImportError:
    raise(ImportError,"The wxPython module is required to run this program.")
import threading
import numpy as np
import time

EVT_NEW_IMAGE = wx.PyEventBinder(wx.NewEventType(), 0)


class SLMdisplay:
    """Interface for sending images to the display frame."""
    def __init__(self, monitor = 1, isImageLock = False):       
        self.isImageLock = isImageLock            
        self.monitor = monitor
        # Create the thread in which the window app will run
        # It needs its thread to continuously refresh the window
        self.vt =  videoThread(self)      
        self.eventLock = threading.Lock()
        if (self.isImageLock):
            self.eventLock = threading.Lock()
        
    def getSize(self):
        return self.vt.frame._resX, self.vt.frame._resY

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
            color_array = np.concatenate((bw_array,bw_array,bw_array), axis=2)
            data = color_array.tostring()
        else :      
            data = self.array.tostring()   
        img = wx.ImageFromBuffer(width=w, height=h, dataBuffer=data)
        # Create the event
        event = ImageEvent()
        event.img = img
        event.eventLock = self.eventLock
        
        # Wait for the lock to be released (if isImageLock = True)
        # to be sure that the previous image has been displayed
        # before displaying the next one - it avoids skipping images
        if (self.isImageLock):
            event.eventLock.acquire()
        # Wait (can bug when closing/opening the SLM too quickly otherwise)
        time.sleep(0.5)
        # Trigger the event (update image)
        self.vt.frame.AddPendingEvent(event)
        
    def close(self):
        self.vt.frame.Close()


class ImageEvent(wx.PyCommandEvent):
    def __init__(self, eventType=EVT_NEW_IMAGE.evtType[0], id=0):
        wx.PyCommandEvent.__init__(self, eventType, id)
        self.img = None
        self.color = False
        self.oldImageLock = None
        self.eventLock = None


class SLMframe(wx.Frame):
    """Frame used to display full screen image."""
    def __init__(self, monitor, isImageLock = True):   
        self.isImageLock = isImageLock
        # Create the frame
        #wx.Frame.__init__(self,None,-1,'SLM window',pos = (self._x0, self._y0), size = (self._resX, self._resY)) 
        self.SetMonitor(monitor)
        # Set the frame to the position and size of the target monito
        wx.Frame.__init__(self,None,-1,'SLM window',pos = (self._x0, self._y0), size = (self._resX, self._resY)) 
        self.img = wx.EmptyImage(2,2)
        self.bmp = self.img.ConvertToBitmap()
        self.clientSize = self.GetClientSize()
        # Update the image upon receiving an event EVT_NEW_IMAGE
        self.Bind(EVT_NEW_IMAGE, self.UpdateImage)
        # Set full screen
        self.ShowFullScreen(not self.IsFullScreen(), wx.FULLSCREEN_ALL)
        self.SetFocus()

    def InitBuffer(self):
        self.clientSize = self.GetClientSize()
        self.bmp = self.img.Scale(self.clientSize[0], self.clientSize[1]).ConvertToBitmap()
        dc = wx.ClientDC(self)
        dc.DrawBitmap(self.bmp,0,0)

        
    def UpdateImage(self, event):
        self.eventLock = event.eventLock
        self.img = event.img
        self.InitBuffer()
        self.ReleaseEventLock()
        
    def ReleaseEventLock(self):
        if self.eventLock:
            if self.eventLock.locked():
                self.eventLock.release()
        
    def SetMonitor(self, monitor):
        tryMonitor = monitor

        while tryMonitor > wx.Display.GetCount() - 1:
            tryMonitor -= 1  # Try other monitor

        if tryMonitor < 0:
            raise ValueError('Invalid monitor (monitor %d).' % monitor)

        self._x0, self._y0, self._resX, self._resY = wx.Display(tryMonitor).GetGeometry()
        

class videoThread(threading.Thread):
    """Run the MainLoop as a thread. Access the frame with self.frame."""
    def __init__(self, parent,autoStart=True):
        threading.Thread.__init__(self)
        self.parent = parent
        # Set as deamon so that it does not prevent the main program from exiting
        self.setDaemon(1)
        self.start_orig = self.start
        self.start = self.start_local
        self.frame = None #to be defined in self.run
        self.lock = threading.Lock()
        self.lock.acquire() #lock until variables are set
        if autoStart:
            self.start() #automatically start thread on init
    def run(self):
        app = wx.App()
        frame = SLMframe(monitor = self.parent.monitor, isImageLock = self.parent.isImageLock)
        frame.Show(True)
        self.frame = frame
        self.lock.release()
        # Start GUI main loop
        app.MainLoop()

    def start_local(self):
        self.start_orig()
        # Use lock to wait for the functions to get defined
        self.lock.acquire()


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
