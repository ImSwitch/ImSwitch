# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: Testa4
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
    def xMoveUp(self):
        print('x Move up')
    def xMoveDown(self):
        print('x Move down')
    def yMoveUp(self):
        print('y Move up')
    def yMoveDown(self):
        print('y Move down')
    def zMoveUp(self):
        print('z Move up')
    def zMoveDown(self):
        print('z Move down')

        
        