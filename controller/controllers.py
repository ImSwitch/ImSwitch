# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np

class WidgetController():
    def __init__(self, comm_channel, master, widget):
        self.master = master
        self.widget = widget
        self.comm_channel = comm_channel
        
# Alignment control  

class ULensesController(WidgetController):
    def addPlot(self, plot):
        self.comm_channel.addItemTovb(plot)
    def getImageSize(self):
        return self.master.cameraHelper.getShapes()
        
class AlignXYController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__active = False
        self.__radio = 0
    def addROI(self, roi):
         self.comm_channel.addItemTovb(roi)
    def updateValue(self, im):
        if self.__active:
            ROI = self.widget.getROI()
            selected = ROI.getArrayRegion(im, self.comm_channel.getImg())
            value = np.mean(selected, self.__radio)    
            self.widget.updateValue(value)
    def updateActive(self, b):
        self.__active = b
    def setRadio(self, radio):
        self.__radio = radio
        
class AlignAverageController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__active = False
    def addROI(self, roi):
         self.comm_channel.addItemTovb(roi)
    def updateValue(self, im): 
        if self.__active:
            ROI = self.widget.getROI()
            selected = ROI.getArrayRegion(im, self.comm_channel.getImg())
            value = np.mean(selected)    
            self.widget.updateValue(value)
        
    def updateActive(self, b):
        self.__active = b
        
class AlignmentController(WidgetController):
    def addLine(self,line):
         self.comm_channel.addItemTovb(line)

class FFTController(WidgetController): 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__active = False
        self.__updateRate = 10
        self.__it = 0
        self.__init = False
    def showFFT(self, clicked):
        self.__active = clicked
        self.__init = False
    def updateImage(self, img):
        if self.__active and (self.__it == self.__updateRate):
            self.__it = 0
            self.widget.setImage(np.fft.fftshift(np.log10(abs(np.fft.fft2(img)))), self.__init)
            self.__init = True
            
        elif self.__active and (not (self.__it == self.__updateRate)):
            self.__it += 1
    def changeRate(self, rate):
        self.__updateRate = rate
        self.__it = 0
        
# Image control
class SettingsController(WidgetController):
    def adjustFrame(self, binPar, widthPar, heightPar, X0par, Y0par):
        binning = binPar.value()
        width = widthPar.value()
        height = heightPar.value()
        
        # Round to closest "divisable by 4" value.
        #        vpos = int(4 * np.ceil(vpos / 4))
        #        hpos = int(4 * np.ceil(hpos / 4))
        # Following is to adapt to the V3 camera on Fra's setup
        vpos = binning*X0par.value()
        hpos = binning*Y0par.value()
        vsize = binning*width
        hsize = binning*height
        
        
        if not (vpos == 0 and hpos == 0 and vsize == 2048 and hsize == 2048):
            vpos = int(128 * np.ceil(binning*X0par.value() / 128))
            hpos = int(128 * np.ceil(binning*Y0par.value() / 128))
            vsize = int(128 * np.ceil(binning*width / 128))
            hsize = int(128 * np.ceil(height / 128))
            minroi = 64
            vsize = int(min(2048 - vpos, minroi * np.ceil(vsize / minroi)))
            hsize = int(min(2048 - hpos, minroi * np.ceil(hsize / minroi)))
            
        self.master.cameraHelper.cropOrca(vpos, hpos, vsize, hsize)

        # Final shape values might differ from the user-specified one because
        # of camera limitation x128
        width, height = self.master.cameraHelper.getShapes()
        self.comm_channel.adjustFrame(width, height)
        frameStart = self.master.cameraHelper.getFrameStart()
        X0par.setValue(frameStart[0])
        Y0par.setValue(frameStart[1])
        widthPar.setValue(width)
        heightPar.setValue(height)
        self.widget.updateTimings(self.master.cameraHelper.getTimings())
        
    def ROIchanged(self, pos, size):
        self.widget.ROIchanged(self.master.cameraHelper.getFrameStart(), pos, size)
    def customROI(self):
        return self.comm_channel.customROI()
    def abortROI(self, X0par, Y0par, widthPar, heightPar):
        self.comm_channel.toggleROI(False)
        frameStart = self.master.cameraHelper.getFrameStart()
        shapes = self.master.cameraHelper.getShapes()
        X0par.setValue(frameStart[0])
        Y0par.setValue(frameStart[1])
        widthPar.setValue(shapes[0])
        heightPar.setValue(shapes[1])
    def changeTriggerSource(self, source):
        self.master.cameraHelper.changeTriggerSource(source)
    def setExposure(self, time):
        params = self.master.cameraHelper.setExposure(time)
        self.widget.updateTimings(params)
    def setBinning(self, binning):
        self.master.cameraHelper.setBinning(binning)
  
class ViewController(WidgetController): 
    def liveview(self, clicked):
        if clicked:
            self.master.cameraHelper.startAcquisition()
        else:
            self.master.cameraHelper.stopAcquisition()
    def updateGrid(self, width, height):
        self.widget.updateGrid(width, height)
       
class ImageController(WidgetController): 
    def toggleROI(self, b):
        self.widget.toggleROI(b)
    def autoLevels(self, init=True):
        self.widget.autoLevels(init)
    def addItemTovb(self, item):
        self.widget.addItemTovb(item)
    def removeItemFromvb(self, item):
        self.widget.removeItemFromvb(item)
    def updateImage(self, img):
        self.widget.updateImage(img)
    def adjustFrame(self, width, height):
        self.widget.adjustFrame(width, height)
    def customROI(self):
        [pos, size] = self.widget.customROI()
        return [self.master.cameraHelper.getFrameStart(), pos, size]
    def ROIchanged(self, pos, size):
        self.comm_channel.ROIchanged(pos, size)
    def getImg(self):
        return self.widget.getImg()
        
        
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
    def __init__(self, comm_channel, master, widget):
        super().__init__(comm_channel, master, widget)
        self.multipleScanController = MultipleScanController(comm_channel, master, widget.multiScanWgt)
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
        

        

        
        



        
        