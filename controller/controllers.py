# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np
import pyqtgraph as pg

class WidgetController():
    def __init__(self, master, widget):
        self.master = master
        self.widget = widget
        
class ScanController(WidgetController):
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
    
class MultipleScanController(WidgetController):
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
        
class FocusLockController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('Init Focus Lock Controller')
    def unlockFocus(self):
        print('Unlock focus')
    def toggleFocus(self):
        print('Toggle focus')
    def movePZT(self):
        print('Move PZT')
    def focusCalibThreadStart(self):
        print('Focus calib thread Start')
    def showCalibCurve(self):
        print('Focus calib curve')
        
class PositionerController(WidgetController):
    def move(self, axis, dist):
        newPos = self.master.moveStage(axis, dist)
        self.widget.newPos(axis, newPos)

class ULensesController(WidgetController):
    def addPlot(self, plot):
        self.master.addItemTovb(plot)
    def getImageSize(self, plot):
        return self.master.getImageSize()
        
class AlignXYController(WidgetController):
    def addROI(self, roi):
        self.master.addItemTovb(roi)
    def updateValue(self):
        print('update Align XY')
        
class AlignAverageController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('Init Z Alignment')
    def ROItoggle(self):
        print('ROI toggle')
    def resetGraph(self):
        print('Reset Graph Z Alignment')
    def updateValue(self):
        print('Update value Align Z')
        
class AlignmentController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('Init Alignment Controller')
    def alignmentToolAux(self):
        print('Alignment tool aux')
        
class LaserController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('Laser Controller init')
    def toggleLaser(self, laser):
        print('Laser toggle'+str(laser))
    def changeSlider(self, laser):
        print('Change slider'+str(laser))
    def changeEdit(self, laser):
        print('Change edit'+str(laser))
    def updateDigitalPowers(self):
        print('update digital powers')
    def GlobalDigitalMod(self):
        print('Global Digital Mod')
    def getPower(laser):
        return 200
        
class FFTController(WidgetController):
    def doFFT(self):
        im = np.fft.fftshift(np.log10(abs(np.fft.fft2(self.master.getImage()))))
        self.widget.setImage(im)
        
class RecorderController(WidgetController):
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
        
        
class ViewController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('View Controller Init')
    def liveview(self):
        print('liveview')
    def updateView(self):
        print('Update view')
       
class ImageController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('Init Image controller')
    def ROIchanged(self):
        print('ROI changed')
    def autoLevels(self):
        print('Auto levels')




        
        