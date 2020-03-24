# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""

class ScanController():
    def __init__(self):
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

        
class MultipleScanController():
    def __init__(self):
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
        
class FocusLockController():
    def __init__(self):
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
        
class PositionerController():
    def __init__(self):
        print('Init Positioner Controller')
    def move(self, axis, dist):
        print('Move axis '+ axis)
       newPos = masterController.move(axis, dist)
       view.Positioner.newPos(axis, newPos)

class ULensesController():
    def __init__(self):
        print('Init ulenses controller')
    def ulensesToolAux(self):
        print('Draw microlenses')
  
class AlignXYController():
    def __init__(self):
        print('Init XY Alignment')
    def ROItoggle(self):
        print('Align XY ROI toggle')
    def updateValue(self):
        print('update Align XY')
        
class AlignAverageController():
    def __init__(self):
        print('Init Z Alignment')
    def ROItoggle(self):
        print('ROI toggle')
    def resetGraph(self):
        print('Reset Graph Z Alignment')
    def updateValue(self):
        print('Update value Align Z')
        
class AlignmentController():
    def __init__(self):
        print('Init Alignment Controller')
    def alignmentToolAux(self):
        print('Alignment tool aux')
        
class LaserController():
    def __init__(self):
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
        
class FFTController():
    def __init__(self):
        print('init FFT controller')
    def doFFT(self):
        print('Do FFT')
    def changePos(self):
        print('Change Pos')
        
class RecorderController():
    def __init__(self):
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
        
        
class ViewController():
    def __init__(self):
        print('View Controller Init')
    def liveview(self):
        print('liveview')
    def updateView(self):
        print('Update view')
       
class ImageController():
    def __init__(self):
        print('Init Image controller')
    def ROIchanged(self):
        print('ROI changed')
    def autoLevels(self):
        print('Auto levels')




        
        