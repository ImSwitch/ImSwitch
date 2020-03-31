# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np

class WidgetController():
    def __init__(self, master, widget):
        self.master = master
        self.widget = widget
        
# Alignment control  

class ULensesController(WidgetController):
    def __init__(self, addFunc, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addFunc = addFunc
    def addPlot(self, plot):
        self.addFunc(plot)
    def getImageSize(self):
        return self.master.getImageSize()
        
class AlignXYController(WidgetController):
    def __init__(self, addFunc, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addFunc = addFunc
    def addROI(self, roi):
        self.addFunc(roi)
    def updateValue(self, roi): # TODO
        print('update Align XY')
        
class AlignAverageController(WidgetController):
    def __init__(self, addFunc, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addFunc = addFunc
    def addROI(self, roi):
        self.addFunc(roi)
    def updateValue(self, roi): # TODO
        print('Update value Align Z')
        
class AlignmentController(WidgetController):
    def __init__(self, addFunc, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addFunc = addFunc
    def addLine(self,line):
        self.addFunc(line)

class FFTController(WidgetController): # improve taking image
    def doFFT(self):
        im = np.fft.fftshift(np.log10(abs(np.fft.fft2(self.master.getImage()))))
        self.widget.setImage(im)
    
# Image control

class ViewController(WidgetController): # TODO Having the timers and call TempestaController that updates the update for every widget
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('View Controller Init')
    def liveview(self):
        print('liveview')
    def updateView(self):
        print('Update view')
       
class ImageController(WidgetController): # TODO
    def ROIchanged(self):
        print('ROI changed')
    def autoLevels(self):
        print('Auto levels')
    def addItemTovb(self, item):
        self.widget.addItemTovb(item)
    def removeItemFromvb(self, item):
        self.view.removeItemFromvb(item)
        
class RecorderController(WidgetController): # TODO
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('Recording Controller init')
    def openFolder(self):
        print('Open folder recorder')
    def specFile(self):
        print('Spec file')
    def snapTIFF(self):
        print('Snap TIFF')
    def startRecording(self):
        print('Start recording')
    def specFrames(self):
        print('Spec Frames')
    def specTime(self):
        print('Spec Time')
    def recScanOnce(self):
        print('Scan once')
    def recScanLapse(self):
        print('Scan lapse')
    def untilStop(self):
        print('Rec till stop')
    def filesizeupdate(self):
        print('File size update')

# Scan control

class ScanController(WidgetController): # TODO
    def __init__(self, master, widget):
        super().__init__(master, widget)
        self.multipleScanController = MultipleScanController(master, widget.multiScanWgt)
        print('Init Scan Controller')
    def saveScan(self):
        print('save scan')
    def loadScan(self):
        print('load scan')
    def scanParameterChanged(self, scanParam):
        print('Parameter' + scanParam + 'changed')
    def setScanMode(self, scanMode):
        print('Scan mode set to ' + scanMode)
    def setPrimScanDim(self, dim):
        print('Primary scan dimension set to ' + dim)
    def setScanOrNot(self, b):
        if b:
            print('Scan')
        else:
            print('Not Scan')
    def scanOrAbort(self):
        print('Scan or Abort')
    def previewScan(self):
        print('previewScan')
    def getSampleRate(self):
        return 10000
    
class MultipleScanController(WidgetController): # TODO
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('Init Multiple Scan Controller')
    def saveScan(self):
        print('save scan')
    def toggleCrossHair(self):
        print('toggle CrossHair')
    def analyzeWorker(self):
        print('Analyze')
    def find_fpWorker(self):
        print('Find fp')
    def change_illum_image(self):
        print('Change illum image')
    def nextBead(self):
        print('Next bead')
    def overlayWorker(self):
        print('Overlay Worker')
    def clear(self):
        print('Clear')
      
# Hardware control
        
class PositionerController(WidgetController): 
    def move(self, axis, dist):
        newPos = self.master.moveStage(axis, dist)
        self.widget.newPos(axis, newPos)

class LaserController(WidgetController): 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digMod = False
    def toggleLaser(self, laser, enable):
        if not self.digMod:
            if enable:
                self.master.toggleLaser(True, laser)
            else:
                self.master.toggleLaser(False, laser)
    def changeSlider(self, laser, value):
        if not self.digMod:
            magnitude =  value 
            self.master.changePower(magnitude, laser)
            self.widget.changeEdit(str(magnitude), laser)
    def changeEdit(self, laser, value):
        if not self.digMod:
            magnitude = value
            self.master.changePower(magnitude, laser)
            self.widget.changeSlider(magnitude, laser)
    def updateDigitalPowers(self, digital, powers, lasers):
        self.digMod = digital
        if digital:
            for i in np.arange(len(lasers)):
                self.master.changePower(powers[i], lasers[i])
            
    def GlobalDigitalMod(self, digital, powers, lasers):
        self.digMod = digital
        if digital:
            for i in np.arange(len(lasers)):
                self.master.digitalMod(True, powers[i], lasers[i])
        

        

        
        



        
        