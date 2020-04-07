# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np
import view.guitools as guitools
import pyqtgraph as pg

class WidgetController():
    def __init__(self, comm_channel, master, widget):
        # Protected attributes, which should only be accessed from WidgetController and its subclasses
        self._master = master
        self._widget = widget
        self._comm_channel = comm_channel
        
class LiveUpdatedController(WidgetController):
    # Those controllers that will update the widgets with an upcoming frame from the camera 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = False
    def update(self):
        raise NotImplementedError

# Alignment control

class ULensesController(WidgetController):
    def addPlot(self):
        self._comm_channel.addItemTovb(self._widget.ulensesPlot)
        
    def ulensesToolAux(self):
        x = np.float(self._widget.xEdit.text())
        y = np.float(self._widget.yEdit.text())
        px = np.float(self._widget.pxEdit.text())
        up = np.float(self._widget.upEdit.text())
        size_x, size_y = self._master.cameraHelper.shapes
        pattern_x = np.arange(x, size_x, up/px)
        pattern_y = np.arange(y, size_y, up/px)
        self._widget.points = np.array(np.meshgrid(pattern_x, pattern_y)).T.reshape(-1,2)  
        self._widget.ulensesPlot.setData(x = self._widget.points[:,0], y = self._widget.points[:,1], pen=pg.mkPen(None), brush='r', symbol='x')
        self._widget.show()
        
    def show(self):
        if self._widget.ulensesCheck.isChecked():
            self._widget.ulensesPlot.show()
        else:
            self._widget.ulensesPlot.hide()
        
class AlignXYController(LiveUpdatedController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.axis = 0
        
    def addROI(self):
         self._comm_channel.addItemTovb(self._widget.ROI)
         
    def update(self):
        if self.active:
            value = np.mean(self._comm_channel.getROIdata(self._widget.ROI), self.axis) 
            self._widget.graph.updateGraph(value)
            
    def setAxis(self, axis):
        self.axis = axis
        
    def ROItoggle(self):
        if self._widget.roiButton.isChecked() is False:
            self._widget.ROI.hide()
            self.active = False
            self._widget.roiButton.setText('Show ROI')
        else:
            ROIsize = (64, 64)
            ROIcenter = self._comm_channel.centerROI()
            
            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                          ROIcenter[1] - 0.5 * ROIsize[1])
        
            self._widget.ROI.setPos(ROIpos)
            self._widget.ROI.setSize(ROIsize)
            self._widget.ROI.show()
            self.active = True
            self._widget.roiButton.setText('Hide ROI')        
        
class AlignAverageController(LiveUpdatedController):
    def addROI(self):
         self._comm_channel.addItemTovb(self._widget.ROI)
         
    def update(self): 
        if self.active:
            value = np.mean(self._comm_channel.getROIdata(self._widget.ROI))    
            self._widget.graph.updateGraph(value)
            
    def ROItoggle(self):
        if self._widget.roiButton.isChecked() is False:
            self._widget.ROI.hide()
            self.active = False
            self._widget.roiButton.setText('Show ROI')
        else:
            ROIsize = (64, 64)
            ROIcenter = self._comm_channel.centerROI()
            
            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                          ROIcenter[1] - 0.5 * ROIsize[1])
        
            self._widget.ROI.setPos(ROIpos)
            self._widget.ROI.setSize(ROIsize)
            self._widget.ROI.show()
            self._widget.ROI.show()
            self.active = True
            self._widget.roiButton.setText('Hide ROI')
        
class AlignmentController(WidgetController):
    def addLine(self):
         self._comm_channel.addItemTovb(self._widget.alignmentLine)
         
    def alignmentToolAux(self):
        self.angle = np.float(self._widget.angleEdit.text())
        self.alignmentLine.setAngle(self._widget.angle)
        self.show()
        
    def show(self):
        if self._widget.alignmentCheck.isChecked():
            self._widget.alignmentLine.show()
        else:
            self._widget.alignmentLine.hide()

class FFTController(LiveUpdatedController): 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updateRate = 10
        self.it = 0
        self.init = False
        
    def showFFT(self):
        self.active = self._widget.showCheck.isChecked()
        self.init = False
        
    def update(self):
        if self.active and (self.it == self.updateRate):
            self.it = 0
            self._widget.setImage(np.fft.fftshift(np.log10(abs(np.fft.fft2(self._master.cameraHelper.image)))), self.init)
            self.init = True
        elif self.active and (not (self.it == self.updateRate)):
            self.it += 1
            
    def changeRate(self):
        self.updateRate = float(self._widget.lineRate.text())
        self.it = 0
        
# Image control

class SettingsController(WidgetController):
    def addROI(self):
         self._comm_channel.addItemTovb(self._widget.ROI)
         
    def adjustFrame(self):
        binning = self._widget.binPar.value()
        width = self._widget.widthPar.value()
        height = self._widget.heightPar.value()
        X0par = self._widget.X0par.value()
        Y0par = self._widget.Y0par.value()
        # Round to closest "divisable by 4" value.
        #        vpos = int(4 * np.ceil(vpos / 4))
        #        hpos = int(4 * np.ceil(hpos / 4))
        # Following is to adapt to the V3 camera on Fra's setup
        vpos = binning*X0par
        hpos = binning*Y0par
        vsize = binning*width
        hsize = binning*height
        
        
        if not (vpos == 0 and hpos == 0 and vsize == 2048 and hsize == 2048):
            vpos = int(128 * np.ceil(vpos / 128))
            hpos = int(128 * np.ceil(hpos / 128))
            vsize = int(128 * np.ceil(vsize / 128))
            hsize = int(128 * np.ceil(hsize / 128))
            minroi = 64
            vsize = int(min(2048 - vpos, minroi * np.ceil(vsize / minroi)))
            hsize = int(min(2048 - hpos, minroi * np.ceil(hsize / minroi)))
            
        self._master.cameraHelper.cropOrca(vpos, hpos, vsize, hsize)

        # Final shape values might differ from the user-specified one because
        # of camera limitation x128
        
        width, height = self._master.cameraHelper.shapes
        self._comm_channel.adjustFrame(width, height)
        self._widget.ROI.hide()
        frameStart = self._master.cameraHelper.frameStart
        self._widget.X0par.setValue(frameStart[0])
        self._widget.Y0par.setValue(frameStart[1])
        self._widget.widthPar.setValue(width)
        self._widget.heightPar.setValue(height)
        self.updateTimings(self._master.cameraHelper.getTimings())
        
    def customROI(self):
        ROIsize = (64, 64)
        ROIcenter = self._comm_channel.centerROI()
        
        ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])
    
        self._widget.ROI.setPos(ROIpos)
        self._widget.ROI.setSize(ROIsize)
        self._widget.ROI.show()
        self.ROIchanged()  
        
    def ROIchanged(self):
        frameStart = self._master.cameraHelper.frameStart
        pos = self._widget.ROI.pos()
        size = self._widget.ROI.size()
        self._widget.X0par.setValue(frameStart[0] + int(pos[0]))
        self._widget.Y0par.setValue(frameStart[1] + int(pos[1]))

        self._widget.widthPar.setValue(int(size[0]))   # [0] is Width
        self._widget.heightPar.setValue(int(size[1]))  # [1] is Height
        
    def abortROI(self):
        self._widget.toggleROI(False)
        frameStart = self._master.cameraHelper.frameStart
        shapes = self._master.cameraHelper.shapes
        self._widget.X0par.setValue(frameStart[0])
        self._widget.Y0par.setValue(frameStart[1])
        self._widget.widthPar.setValue(shapes[0])
        self._widget.heightPar.setValue(shapes[1])
        
    def changeTriggerSource(self):
        self._master.cameraHelper.changeTriggerSource(self._widget.trigsourceparam.value())
        
    def setExposure(self):
        params = self._master.cameraHelper.setExposure(self._widget.expPar.value())
        self.updateTimings(params)
        
    def setBinning(self):
        self._master.cameraHelper.setBinning(self.binPar.value())
        
    def updateTimings(self, params):
        self._widget.RealExpPar.setValue(params[0])
        self._widget.FrameInt.setValue(params[1])
        self._widget.ReadoutPar.setValue(params[2])
        self._widget.EffFRPar.setValue(params[3])
  
class ViewController(WidgetController): 
    def liveview(self):
        if self._widget.liveviewButton.isChecked():
            self._master.cameraHelper.startAcquisition()
        else:
            self._master.cameraHelper.stopAcquisition()
            
    def updateGrid(self, width, height):
        self._widget.updateGrid(width, height)
       
class ImageController(LiveUpdatedController):
    def autoLevels(self, init=True):
        if not init:
            self._widget.levelsButton.setEnabled(True)
        self._widget.hist.setLevels(*guitools.bestLimits(self._widget.img.image))
        self._widget.hist.vb.autoRange()
        
    def addItemTovb(self, item):
        self._widget.vb.addItem(item)
        
    def removeItemFromvb(self, item):
        self._widget.vb.removeItem(item)
        
    def update(self):
        im = self._master.cameraHelper.image
        self._widget.img.setImage(im, autoLevels=False, autoDownsample=False)
        
    def adjustFrame(self, width, height):
        self._widget.vb.setLimits(xMin=-0.5, xMax=width - 0.5, minXRange=4,
                          yMin=-0.5, yMax=height - 0.5, minYRange=4)
        self._widget.vb.setAspectLocked()
        
    def getROIdata(self, roi):
        return roi.getArrayRegion(self._master.cameraHelper.image, self._widget.img)
        
    def centerROI(self):
        return (int(self._widget.vb.viewRect().center().x()),
                         int(self._widget.vb.viewRect().center().y()))
        
        
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
        self.parameter_dictionary = None
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
    def parametersToSend():
        return None #Some list of parameters
    def runScan(self):
        self._master.scanHelper.runScan(self.parameter_dictionary)
    
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
        newPos = self._master.moveStage(axis, dist)
        newText = "<strong>" + ['x', 'y', 'z'][axis] + " = {0:.2f} µm</strong>".format(newPos)
        
        getattr(self._widget, ['x', 'y', 'z'][axis] + "Label").setText(newText)

class LaserController(WidgetController): 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digMod = False
        
    def toggleLaser(self, laser, enable):
        if not self.digMod:
            if enable:
                self._master.toggleLaser(True, laser)
            else:
                self._master.toggleLaser(False, laser)
                
    def changeSlider(self, laser, value):
        if not self.digMod:
            magnitude =  value 
            self._master.changePower(magnitude, laser)
            self._widget.changeEdit(str(magnitude), laser)
            
    def changeEdit(self, laser, value):
        if not self.digMod:
            magnitude = value
            self._master.changePower(magnitude, laser)
            self._widget.changeSlider(magnitude, laser)
            
    def updateDigitalPowers(self, digital, powers, lasers):
        self.digMod = digital
        if digital:
            for i in np.arange(len(lasers)):
                self._master.changePower(powers[i], lasers[i])
            
    def GlobalDigitalMod(self, digital, powers, lasers):
        self.digMod = digital
        if digital:
            for i in np.arange(len(lasers)):
                self._master.digitalMod(True, powers[i], lasers[i])
        

        
        



        
        