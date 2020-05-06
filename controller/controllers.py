# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np
import view.guitools as guitools
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import sys
import subprocess
import os
import time
import configparser

class WidgetControllerFactory():
    """Factory class for creating a WidgetController object. Factory checks
    that the new object is a valid WidgetController."""
    def __new__(cls , className, *args):

        widgetController = eval(className+'(*args)')
        if widgetController.isValidChild():
            return widgetController
        
class WidgetController():
    """ Superclass for all WidgetControllers. 
            All WidgetControllers should have access to MasterController, CommunicationChannel and the linked Widget. """ 
            
    def __init__(self, comm_channel, master, widget):
        # Protected attributes, which should only be accessed from WidgetController and its subclasses
        self._master = master
        self._widget = widget
        self._comm_channel = comm_channel
    
        

class LiveUpdatedController(WidgetController):
    """ Superclass for those controllers that will update the widgets with an upcoming frame from the camera. 
            Should be either active or not, and have an update function. """
            
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = False
        
    def update(self):
        raise NotImplementedError
        
class SuperScanController(WidgetController):
    def __init__(self, comm_channel, master, widget):
        super().__init__(comm_channel, master, widget)
        # self._stageParameterDict = None
        # self._TTLParameterDict = None
        #Make non-overwritable functions
        self.isValidScanController = self.__isValidScanController
        self.isValidChild = self.isValidScanController
        
    # @property
    # def stageParameterList(self):
    #     if self._stageParameterDict is None:
    #         raise ValueError('Scan controller has no parameters defined')
    #     else:
    #         return [*self._stageParameterDict] #makes list of dict keys

    # @property
    # def TTLParameterList(self):
    #     if self._TTLParameterDict is None:
    #         raise ValueError('Scan controller has no parameters defined')
    #     else:
    #         return [*self._TTLParameterDict] #makes list of dict keys
        
    @property
    def parameterDict(self):
        return None
        
    def __isValidScanController(self):
        if self.parameterDict is None:
            raise InvalidChildClassError('ScanController needs to return a valid parameterDict')
        else:
            return True
            
    
        

# Alignment control

class ULensesController(WidgetController):
    """ Linked to ULensesWidget. """
    
    def addPlot(self):
        """ Adds ulensesPlot to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb(self._widget.ulensesPlot)
        
    def updateGrid(self):
        """ Updates plot with new parameters. """
        self.getParameters()
        size_x, size_y = self._master.cameraHelper.shapes
        pattern_x = np.arange(self.x, size_x, self.up/self.px)
        pattern_y = np.arange(self.y, size_y, self.up/self.px)
        grid = np.array(np.meshgrid(pattern_x, pattern_y)).T.reshape(-1,2)  
        self._widget.ulensesPlot.setData(x = grid[:,0], y = grid[:,1], pen=pg.mkPen(None), brush='r', symbol='x')
        if self._widget.ulensesCheck.isChecked(): self._widget.show()
        
    def show(self):
        """ Shows or hides grid. """
        if self._widget.ulensesCheck.isChecked():
            self._widget.ulensesPlot.show()
        else:
            self._widget.ulensesPlot.hide()
            
    def getParameters(self):
        """ Update new parameters from graphical elements in the widget."""
        self.x = np.float(self._widget.xEdit.text())
        self.y = np.float(self._widget.yEdit.text())
        self.px = np.float(self._widget.pxEdit.text())
        self.up = np.float(self._widget.upEdit.text())
  
        
class AlignXYController(LiveUpdatedController):
    """ Linked to AlignWidgetXY. """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.axis = 0
        
    def update(self):
        """ Update with new camera frame. """
        if self.active:
            value = np.mean(self._comm_channel.getROIdata(self._widget.ROI), self.axis) 
            self._widget.graph.updateGraph(value)
            
    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb(self._widget.ROI)
        
    def toggleROI(self):
        """ Show or hide ROI."""
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
            
    def setAxis(self, axis):
        """ Setter for the axis (X or Y). """
        self.axis = axis

        
class AlignAverageController(LiveUpdatedController):
    """ Linked to AlignWidgetAverage."""
    
    def update(self): 
        """ Update with new camera frame. """
        if self.active:
            value = np.mean(self._comm_channel.getROIdata(self._widget.ROI))    
            self._widget.graph.updateGraph(value)
            
    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb(self._widget.ROI)
         
    def toggleROI(self):
        """ Show or hide ROI."""
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
        
            
class AlignmentLineController(WidgetController):
    """ Linked to AlignmentLineWidget."""
    
    def addLine(self):
        """ Adds alignmentLine to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb(self._widget.alignmentLine)
         
    def updateLine(self):
        """ Updates line with new parameters. """
        self._widget.angle = np.float(self._widget.angleEdit.text())
        self._widget.alignmentLine.setAngle(self._widget.angle)
        self.show()
        
    def show(self):
        """ Shows or hides line. """
        if self._widget.alignmentCheck.isChecked():
            self._widget.alignmentLine.show()
        else:
            self._widget.alignmentLine.hide()

            
class FFTController(LiveUpdatedController):
    """ Linked to AlignmentLineWidget."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updateRate = 10
        self.it = 0
        self.init = False
        self.show = False
        
    def showFFT(self):
        """ Show or hide FFT. """
        self.active = self._widget.showCheck.isChecked()
        self.init = False
        
    def update(self):
        """ Update with new camera frame. """
        if self.active and (self.it == self.updateRate):
            self.it = 0
            im = np.fft.fftshift(np.log10(abs(np.fft.fft2(self._master.cameraHelper.image))))
            self._widget.img.setImage(im, autoLevels=False)
            if not self.init:
                self._widget.vb.setAspectLocked()
                self._widget.vb.setLimits(xMin=-0.5, xMax=self._widget.img.width(), minXRange=4,
                              yMin=-0.5, yMax=self._widget.img.height(), minYRange=4)
                self._widget.hist.setLevels(*guitools.bestLimits(im))
                self._widget.hist.vb.autoRange()
                self.init = True
        elif self.active and (not (self.it == self.updateRate)):
            self.it += 1
            
    def changeRate(self):
        """ Change update rate. """
        self.updateRate = float(self._widget.lineRate.text())
        self.it = 0
        
    def changePos(self):
        """ Change positions of lines.  """
        pos = float(self._widget.linePos.text())
        if (pos == self.show) or pos == 0:
            self._widget.vline.hide()
            self._widget.hline.hide()
            self._widget.rvline.hide()
            self._widget.lvline.hide()
            self._widget.uhline.hide()
            self._widget.dhline.hide()
            self.show = 0
        else:
            self.show = pos
            pos = float(1 / pos)
            imgWidth = self.img.width()
            imgHeight = self.img.height()
            self._widget.vb.setAspectLocked()
            self._widget.vb.setLimits(xMin=-0.5, xMax=imgWidth, minXRange=4,
                      yMin=-0.5, yMax=imgHeight, minYRange=4)
            self._widget.vline.setValue(0.5*imgWidth)
            self._widget.hline.setAngle(0)
            self._widget.hline.setValue(0.5*imgHeight)
            self._widget.rvline.setValue((0.5+pos)*imgWidth)
            self._widget.lvline.setValue((0.5-pos)*imgWidth)
            self._widget.dhline.setAngle(0)
            self._widget.dhline.setValue((0.5-pos)*imgHeight)
            self._widget.uhline.setAngle(0)
            self._widget.uhline.setValue((0.5+pos)*imgHeight)
            self._widget.vline.show()
            self._widget.hline.show()
            self._widget.rvline.show()
            self._widget.lvline.show()
            self._widget.uhline.show()
            self._widget.dhline.show()
            
            
# Image control


class SettingsController(WidgetController):
    """ Linked to SettingsWidget."""
    
    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb(self._widget.ROI)
     
    def toggleROI(self, b):
        """ Show or hide ROI. """
        if b:
            self._widget.ROI.show()
        else:
            self._widget.ROI.hide()
            
    def getParameters(self):
        """ Take parameters from the camera Tree map. """
        self.model = self._master.cameraHelper.model
        self._widget.tree.p.param('Model').setValue(self.model)
        self.umxpx = self._widget.tree.p.param('Pixel size')
        framePar = self._widget.tree.p.param('Image frame')
        self.binPar = framePar.param('Binning')
        self.frameMode = framePar.param('Mode')
        self.x0par = framePar.param('X0')
        self.y0par = framePar.param('Y0')
        self.widthPar = framePar.param('Width')
        self.heightPar = framePar.param('Height')
        self.applyParam = framePar.param('Apply')
        self.newROIParam = framePar.param('New ROI')
        self.abortROIParam = framePar.param('Abort ROI')
        
        timingsPar = self._widget.tree.p.param('Timings')
        self.effFRPar = timingsPar.param('Internal frame rate')
        self.expPar = timingsPar.param('Set exposure time')
        self.readoutPar = timingsPar.param('Readout time')
        self.realExpPar = timingsPar.param('Real exposure time')
        self.frameInt = timingsPar.param('Internal frame interval')
        self.realExpPar.setOpts(decimals=5)
        
        acquisParam = self._widget.tree.p.param('Acquisition mode')
        self.trigsourceparam = acquisParam.param('Trigger source')
        
        self.applyParam.sigStateChanged.connect(self.adjustFrame)
        self.newROIParam.sigStateChanged.connect(self.updateFrame)
        self.abortROIParam.sigStateChanged.connect(self.abortROI)
        self.trigsourceparam.sigValueChanged.connect(self.changeTriggerSource)
        self.expPar.sigValueChanged.connect(self.setExposure)
        self.binPar.sigValueChanged.connect(self.setBinning)
        self.frameMode.sigValueChanged.connect(self.updateFrame)
        self.expPar.sigValueChanged.connect(self.setExposure)            
            
    def adjustFrame(self):
        """ Crop camera and adjust frame. """
        binning = self.binPar.value()
        width = self.widthPar.value()
        height = self.heightPar.value()
        X0par = self.x0par.value()
        Y0par = self.y0par.value()
        
        # Round to closest "divisable by 4" value.
        hpos = binning*X0par
        vpos = binning*Y0par
        hsize = binning*width
        vsize = height
        
        hmodulus = 4
        vmodulus = 4
        vpos = int(vmodulus * np.ceil(vpos / vmodulus))
        hpos = int(hmodulus * np.ceil(hpos / hmodulus))
        vsize = int(vmodulus * np.ceil(vsize / vmodulus))
        hsize = int(hmodulus * np.ceil(hsize / hmodulus))
        
        self._master.cameraHelper.changeParameter(lambda: self._master.cameraHelper.cropOrca(vpos, hpos, vsize, hsize))

        # Final shape values might differ from the user-specified one because of camera limitation x128
        width, height = self._master.cameraHelper.shapes
        self._comm_channel.adjustFrame(width, height)
        self._widget.ROI.hide()
        frameStart = self._master.cameraHelper.frameStart
        self.x0par.setValue(frameStart[0])
        self.y0par.setValue(frameStart[1])
        self.widthPar.setValue(width)
        self.heightPar.setValue(height)
        self.updateTimings(self._master.cameraHelper.getTimings())
             
    def ROIchanged(self):
        """ Update parameters according to ROI. """
        frameStart = self._master.cameraHelper.frameStart
        pos = self._widget.ROI.pos()
        size = self._widget.ROI.size()
        self.x0par.setValue(frameStart[0] + int(pos[0]))
        self.y0par.setValue(frameStart[1] + int(pos[1]))

        self.widthPar.setValue(int(size[0]))   # [0] is Width
        self.heightPar.setValue(int(size[1]))  # [1] is Height
        
    def abortROI(self):
        """ Cancel and reset parameters of the ROI. """
        self._widget.toggleROI(False)
        frameStart = self._master.cameraHelper.frameStart
        shapes = self._master.cameraHelper.shapes
        self.x0par.setValue(frameStart[0])
        self.y0par.setValue(frameStart[1])
        self.widthPar.setValue(shapes[0])
        self.heightPar.setValue(shapes[1])
        
    def changeTriggerSource(self):
        """ Change trigger (Internal or External). """
        self._master.cameraHelper.changeTriggerSource(self.trigsourceparam.value())
        
    def setTriggerParam(self, source):
        self.trigsourceparam.setValue(source)
        
    def updateTimings(self, params):
        """ Update the real exposure times from the camera. """
        self.realExpPar.setValue(params[0])
        self.frameInt.setValue(params[1])
        self.readoutPar.setValue(params[2])
        self.effFRPar.setValue(params[3])
        
    def setExposure(self):
        """ Update a new exposure time to the camera. """
        params = self._master.cameraHelper.setExposure(self.expPar.value())
        self.updateTimings(params)
        
    def setBinning(self):
        """ Update a new binning to the camera. """
        self._master.cameraHelper.setBinning(self.binPar.value())
        
    def updateFrame(self, controller):
        """ Change the image frame size and position in the sensor. """
        if self.frameMode.value() == 'Custom':
            self.x0par.setWritable(True)
            self.y0par.setWritable(True)
            self.widthPar.setWritable(True)
            self.heightPar.setWritable(True) 
            
            ROIsize = (64, 64)
            ROIcenter = self._comm_channel.centerROI()
        
            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])
    
            self._widget.ROI.setPos(ROIpos)
            self._widget.ROI.setSize(ROIsize)
            self._widget.ROI.show()
            self.ROIchanged() 

        else:
            self.x0par.setWritable(False)
            self.y0par.setWritable(False)
            self.widthPar.setWritable(False)
            self.heightPar.setWritable(False)

            # Change this to config File.
            if self.frameMode.value() == 'Full chip':
                self.x0par.setValue(0)
                self.y0par.setValue(0)
                self.widthPar.setValue(2048)
                self.heightPar.setValue(2048)
               
                self.adjustFrame()
                
    def getCamAttrs(self):
        return  {'Camera_pixel_size': self.umxpx.value(), 'Camera_model': self.model, 'Camera_binning': self.binPar.value(), 'FOV_mode': self.frameMode.value(), 'Camera_exposure_time': self.realExpPar.value(), 'Camera_ROI': [self.x0par.value(), self.y0par.value(), self.widthPar.value(), self.heightPar.value()] }
  
class ViewController(WidgetController): 
    """ Linked to ViewWidget."""
    
    def liveview(self):
        """ Start liveview and activate camera acquisition. """
        self._widget.crosshairButton.setEnabled(True)
        self._widget.gridButton.setEnabled(True)
        if self._widget.liveviewButton.isChecked():
            self._master.cameraHelper.startAcquisition()
        else:
            self._master.cameraHelper.stopAcquisition()
          
    def gridToggle(self):
        """ Connect with grid toggle from Image Widget through communication channel. """
        self._comm_channel.gridToggle()
        
    def crosshairToggle(self):
        """ Connect with crosshair toggle from Image Widget through communication channel. """
        self._comm_channel.crosshairToggle()
    
       
class ImageController(LiveUpdatedController):
    """ Linked to ImageWidget."""
    
    def autoLevels(self, init=True):
        """ Set histogram levels automatically with current camera image."""
        if not init:
            self._widget.levelsButton.setEnabled(True)
        self._widget.hist.setLevels(*guitools.bestLimits(self._widget.img.image))
        self._widget.hist.vb.autoRange()
        
    def addItemTovb(self, item):
        """ Add item from communication channel to viewbox."""
        self._widget.vb.addItem(item)
        item.hide()
        
    def removeItemFromvb(self, item):
        """ Remove item from communication channel to viewbox."""
        self._widget.vb.removeItem(item)
        
    def update(self):
        """ Update new image in the viewbox. """
        im = self._master.cameraHelper.image
        self._widget.img.setImage(im, autoLevels=False, autoDownsample=False)
        
    def adjustFrame(self, width, height):
        """ Adjusts the viewbox to a new width and height. """
        self._widget.grid.update([width, height])
        self._widget.vb.setLimits(xMin=-0.5, xMax=width - 0.5, minXRange=4,
                          yMin=-0.5, yMax=height - 0.5, minYRange=4)
        self._widget.vb.setAspectLocked()
        
    def getROIdata(self, roi):
        """ Returns the cropped image within the ROI. """
        return roi.getArrayRegion(self._master.cameraHelper.image, self._widget.img)
        
    def centerROI(self):
        """ Returns center of viewbox to center a ROI. """
        return (int(self._widget.vb.viewRect().center().x()),
                         int(self._widget.vb.viewRect().center().y()))
        
    def gridToggle(self):
        """ Shows or hides grid. """
        self._widget.grid.toggle()
    
    def crosshairToggle(self):
        """ Shows or hides crosshair. """
        self._widget.crosshair.toggle()
     
        
class RecorderController(WidgetController): 
    """ Linked to RecordingWidget. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recMode = 0

    def isRecording(self):
        return self._widget.recButton.isChecked()
    def openFolder(self):
        """ Opens current folder in File Explorer. """
        try:
            if sys.platform == 'darwin':
                subprocess.check_call(['open', '', self._widget.folderEdit.text()])
            elif sys.platform == 'linux':
                subprocess.check_call(
                    ['gnome-open', '', self._widget.folderEdit.text()])
            elif sys.platform == 'win32':
                os.startfile(self._widget.folderEdit.text())

        except FileNotFoundError:
            if sys.platform == 'darwin':
                subprocess.check_call(['open', '', self._widget.dataDir])
            elif sys.platform == 'linux':
                subprocess.check_call(['gnome-open', '', self._widget.dataDir])
            elif sys.platform == 'win32':
                os.startfile(self._widget.dataDir)
                
    def specFile(self):
        """ Enables the ability to type a specific filename for the data to . """
        if self._widget.specifyfile.checkState():
            self._widget.filenameEdit.setEnabled(True)
            self._widget.filenameEdit.setText('Filename')
        else:
            self._widget.filenameEdit.setEnabled(False)
            self._widget.filenameEdit.setText('Current time')
            
    def snap(self):
        """ Take a snap and save it to a .tiff file. """
        folder = self._widget.folderEdit.text()
        if not os.path.exists(folder):
            os.mkdir(folder)
        time.sleep(0.01)
        name = os.path.join(folder, self.getFileName()) + '_snap.hdf5'
        savename = guitools.getUniqueName(name)
        attrs = self._comm_channel.getCamAttrs()
        self._master.recordingHelper.snap(savename, attrs)
        
    def toggleREC(self):
        """ Start or end recording. """
        if self._widget.recButton.isChecked():
            folder = self._widget.folderEdit.text()
            if not os.path.exists(folder):
                os.mkdir(folder)
            time.sleep(0.01)
            name = os.path.join(folder, self.getFileName()) + '_rec.hdf5'
            self.savename = guitools.getUniqueName(name)
            self.attrs = self._comm_channel.getCamAttrs()
            scan = self._comm_channel.getScanAttrs()
            self.attrs.update(scan)
            if self.recMode == 1:
                self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs, frames=int(self._widget.numExpositionsEdit.text()))
            elif self.recMode == 2:
                self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs, time=float(self._widget.timeToRec.text()))
            elif self.recMode == 3:
                self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs)
                self._comm_channel.prepareScan()
            elif self.recMode == 4:
                self._comm_channel.prepareScan()
                self.lapseTotal = int(self._widget.timeLapseEdit.text())
                self.lapseCurrent = 0
                self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs)
            elif self.recMode == 5:
                self._comm_channel.prepareScan()
                self.dimlapseTotal = int(self._widget.totalSlices.text())
                self.dimlapseCurrent = 0
                self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs)
            else:
                self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs)      
        else:
            self._master.recordingHelper.endRecording() 
        
                    
    def scanDone(self):
        if self._widget.recButton.isChecked(): 
            if self.recMode == 3:    
                self._widget.recButton.setChecked(False)
                self._master.recordingHelper.endRecording() 
                self._comm_channel.endScan()
            elif self.recMode == 4:
                if self.lapseCurrent < self.lapseTotal:
                    self.lapseCurrent += 1
                    self._widget.recButton.setChecked(True)
                    self._widget.currentLapse.setText(str(self.lapseCurrent) + ' / ')
                    self.timer = QtCore.QTimer(singleShot=True)
                    self.timer.timeout.connect(lambda: self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs))
                    self.timer.start(int(float(self._widget.freqEdit.text())*1000))
                else:
                    self._widget.recButton.setChecked(False)
                    self.lapseCurrent = 0
                    self._widget.currentLapse.setText(str(self.lapseCurrent) + ' / ')
                    self._master.recordingHelper.endRecording() 
            elif self.recMode == 5:
                if self.dimlapseCurrent < self.dimlapseTotal:
                    self.dimlapseCurrent += 1
                    self._widget.recButton.setChecked(True)
                    self._widget.currentSlice.setText(str(self.dimlapseCurrent) + ' / ')
                    self._comm_channel.moveZstage(float(self._widget.stepSizeEdit.text()))
                    self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs)
                else:
                    self._widget.recButton.setChecked(False)
                    self.dimlapseCurrent = 0
                    self._comm_channel.moveZstage(-self.dimlapseTotal*float(self._widget.stepSizeEdit.text()))
                    self._widget.currentSlice.setText(str(self.dimlapseCurrent) + ' / ')
                    self._master.recordingHelper.endRecording() 
                    

        
    def endRecording(self):
        self._widget.recButton.click()
        self._widget.currentFrame.setText('0 / ')
        
    def updateRecFrameNumber(self, f):
        self._widget.currentFrame.setText(str(f) +  ' /')
        
    def updateRecTime(self, t):
        self._widget.currentTime.setText(str(t) + ' /')
        
    def specFrames(self):
        self._widget.numExpositionsEdit.setEnabled(True)
        self._widget.timeToRec.setEnabled(False)
        self._widget.timeLapseEdit.setEnabled(False)
        self._widget.totalSlices.setEnabled(False)
        self._widget.freqEdit.setEnabled(False)
        self._widget.stepSizeEdit.setEnabled(False)
        self.recMode = 1
        
    def specTime(self):
        self._widget.numExpositionsEdit.setEnabled(False)
        self._widget.timeToRec.setEnabled(True)
        self._widget.timeLapseEdit.setEnabled(False)
        self._widget.totalSlices.setEnabled(False)
        self._widget.freqEdit.setEnabled(False)
        self._widget.stepSizeEdit.setEnabled(False)
        self.recMode = 2
        
    def recScanOnce(self):
        self._widget.numExpositionsEdit.setEnabled(False)
        self._widget.timeToRec.setEnabled(False)
        self._widget.timeLapseEdit.setEnabled(False)
        self._widget.totalSlices.setEnabled(False)
        self._widget.freqEdit.setEnabled(False)
        self._widget.stepSizeEdit.setEnabled(False)
        self.recMode = 3
        
    def recScanLapse(self):
        self._widget.numExpositionsEdit.setEnabled(False)
        self._widget.timeToRec.setEnabled(False)
        self._widget.timeLapseEdit.setEnabled(True)
        self._widget.totalSlices.setEnabled(False)
        self._widget.freqEdit.setEnabled(True)
        self._widget.stepSizeEdit.setEnabled(False)
        self.recMode = 4
        
    def dimLapse(self):
        self._widget.totalSlices.setEnabled(True)
        self._widget.numExpositionsEdit.setEnabled(False)
        self._widget.timeToRec.setEnabled(False)
        self._widget.timeLapseEdit.setEnabled(False)
        self._widget.freqEdit.setEnabled(False)
        self._widget.stepSizeEdit.setEnabled(True)
        self.recMode = 5
        
    def untilStop(self):
        self._widget.numExpositionsEdit.setEnabled(False)
        self._widget.timeToRec.setEnabled(False)
        self._widget.timeLapseEdit.setEnabled(False)
        self._widget.totalSlices.setEnabled(False)
        self._widget.freqEdit.setEnabled(False)
        self._widget.stepSizeEdit.setEnabled(False)
        self.recMode = 6
        
    def getFileName(self):
        """ Gets the filename of the data to save. """
        if self._widget.specifyfile.checkState():
            filename = self._widget.filenameEdit.text()

        else:
            filename = time.strftime('%Hh%Mm%Ss')

        return filename

# Hardware control

class PositionerController(WidgetController): 
    """ Linked to PositionerWidget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stagePos = [0, 0, 0]
        self.convFactors = [1.5870, 1.5907, 10]
        self.targets = ['Stage_X', 'Stage_Y', 'Stage_Z']
        
    def move(self, axis, dist):
        """ Moves the piezzos in x y or z (axis) by dist micrometers. """
        self.stagePos[axis] += dist
        self._master.nidaqHelper.setAnalog(self.targets[axis], self.stagePos[axis]/self.convFactors[axis])
        newText = "<strong>" + ['x', 'y', 'z'][axis] + " = {0:.2f} µm</strong>".format(self.stagePos[axis])
        
        getattr(self._widget, ['x', 'y', 'z'][axis] + "Label").setText(newText)
        
    def getPos(self):
        return {'X': self.stagePos[0], 'Y': self.stagePos[1], 'Z': self.stagePos[2]}

class LaserController(WidgetController): 
    """ Linked to LaserWidget."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digMod = False
        
    def toggleLaser(self, laser):
        """ Enable or disable laser (on/off)."""
        if self._widget.laserModules[laser].enableButton.isChecked():
            self._master.toggleLaser(True, laser)
        else:
            self._master.toggleLaser(False, laser)
                
    def changeSlider(self, laser):
        """ Change power with slider magnitude. """
        magnitude =  self._widget.laserModules[laser].slider.value() 
        self._master.changePower(magnitude, laser, self.digMod)
        self._widget.laserModules[laser].setPointEdit.setText(str(magnitude))
            
    def changeEdit(self, laser):
        """ Change power with edit magnitude. """
        magnitude = float(self._widget.laserModules[laser].setPointEdit.text())
        self._master.changePower(magnitude, laser, self.digMod)
        self._widget.laserModules[laser].slider.setValue(magnitude)
            
            
    def updateDigitalPowers(self, lasers):
        """ Update the powers if the digital mod is on. """
        self.digMod = self._widget.digModule.DigitalControlButton.isChecked()
        if self.digMod:
            for i in np.arange(len(lasers)):
                laser = lasers[i]
                self._master.changePower(int(self._widget.digModule.powers[laser].text()), laser, self.digMod)
            
    def GlobalDigitalMod(self, lasers):
        """ Start digital modulation. """
        self.digMod = self._widget.digModule.DigitalControlButton.isChecked()
        for i in np.arange(len(lasers)):
            laser = lasers[i]
            self._master.digitalMod(self.digMod, int(self._widget.digModule.powers[laser].text()), laser)
            if not self.digMod:
                self.changeEdit(laser)
    
    def setDigitalButton(self, b):
        self._widget.digModule.DigitalControlButton.setChecked(b)
        self.GlobalDigitalMod([405, 488])
        

# Scan control


class ScanController(SuperScanController): # TODO
    def __init__(self, comm_channel, master, widget):
        super().__init__(comm_channel, master, widget)
        
        self._stageParameterDict = {'Targets[3]': ['StageX', 'StageY', 'StageZ'], \
                  'Sizes[3]':[5,5,0], \
                  'Step_sizes[3]': [1,1,1], \
                  'Start[3]': [0, 0, 0], \
                  'Sequence_time_seconds': 0.005, \
                  'Sample_rate': 100000, \
                  'Return_time_seconds': 0.001}
        self._TTLParameterDict = {'Targets[x]': ['405', '473', '488', 'CAM'], \
                  'TTLStarts[x,y]': [[0.0012], [0.002], [0], [0]], \
                  'TTLEnds[x,y]': [[0.0015], [0.0025], [0], [0]], \
                  'Sequence_time_seconds': 0.005, \
                  'Sample_rate': 100000}
        print('Init Scan Controller')
    
    @property
    def parameterDict(self):
        stageParameterList = [*self._stageParameterDict]
        TTLParameterList = [*self._TTLParameterDict]
        
        return {'stageParameterList': stageParameterList,\
                'TTLParameterList': TTLParameterList}
           
    def getScanAttrs(self):      
        stage = self._stageParameterDict.copy()
        ttl = self._TTLParameterDict.copy()
        stage['Targets[3]'] = np.string_(stage['Targets[3]'])
        ttl['Targets[x]'] = np.string_(ttl['Targets[x]'])
    
        stage.update(ttl)
        return stage
        
    def saveScan(self):
        self.getParameters()
        config = configparser.ConfigParser()
        config.optionxform = str

        config['stageParameterDict'] = self._stageParameterDict
        config['TTLParameterDict'] = self._TTLParameterDict
        config['Modes'] = {'scan_or_not': self._widget.scanRadio.isChecked()}
        fileName = QtGui.QFileDialog.getSaveFileName(self._widget, 'Save scan',
                                                     self._widget.scanDir)
        if fileName == '':
            return

        with open(fileName, 'w') as configfile:
            config.write(configfile)
            
    def loadScan(self):
        config = configparser.ConfigParser()
        config.optionxform = str
    
        fileName = QtGui.QFileDialog.getOpenFileName(self._widget, 'Load scan',
                                                     self._widget.scanDir)
        if fileName == '':
            return
    
        config.read(fileName)
    
        for key in self._stageParameterDict:
            self._stageParameterDict[key] = eval(config._sections['stageParameterDict'][key])
    
        for key in self._TTLParameterDict:
            self._TTLParameterDict[key] = eval(config._sections['TTLParameterDict'][key])
    
        scanOrNot = (config._sections['Modes']['scan_or_not'] == 'True')
        
        
        if scanOrNot:
            self._widget.scanRadio.setChecked(True)
        else:
            self._widget.contLaserPulsesRadio.setChecked(True)

        self.setParameters()
        #self._widget.updateScan(self._widget.allDevices)
        #self._widget.graph.update()
        
    def setParameters(self):
        primDim = self._stageParameterDict['Targets[3]'][0].split('_')[1]
        secDim = self._stageParameterDict['Targets[3]'][1].split('_')[1]
        thirdDim = self._stageParameterDict['Targets[3]'][2].split('_')[1]
        
        axis = {'X' : 0, 'Y' : 1, 'Z' : 2}

        self._widget.primScanDim.setCurrentIndex(axis[primDim])
        self._widget.secScanDim.setCurrentIndex(axis[secDim])
        self._widget.thirdScanDim.setCurrentIndex(axis[thirdDim])
        
        self._widget.scanPar['size' + primDim].setText(str(round(self._stageParameterDict['Sizes[3]'][0], 3)))
        self._widget.scanPar['size' + secDim].setText(str(round(self._stageParameterDict['Sizes[3]'][1], 3)))
        self._widget.scanPar['size' + thirdDim].setText(str(round(self._stageParameterDict['Sizes[3]'][2], 3)))
        
        self._widget.scanPar['stepSize' + primDim].setText(str(round(self._stageParameterDict['Step_sizes[3]'][0], 3))) 
        self._widget.scanPar['stepSize' + secDim].setText(str(round(self._stageParameterDict['Step_sizes[3]'][1], 3))) 
        self._widget.scanPar['stepSize' + thirdDim].setText(str(round(self._stageParameterDict['Step_sizes[3]'][2], 3))) 

        for i in range(len(self._TTLParameterDict['Targets[x]'])):
            self._widget.pxParameters['sta' + self._TTLParameterDict['Targets[x]'][i]].setText(str(round(self._TTLParameterDict['TTLStarts[x,y]'][i][0], 3)))
            self._widget.pxParameters['end' + self._TTLParameterDict['Targets[x]'][i]].setText(str(round(self._TTLParameterDict['TTLEnds[x,y]'][i][0], 3)))
          
        self._widget.seqTimePar.setText(str(round(float(self._TTLParameterDict['Sequence_time_seconds'])*1000, 3)))
        
    def previewScan(self):
        print('previewScan')
    def runScan(self):
        self.getParameters()
        signalDic = self._master.scanHelper.make_full_scan(self._stageParameterDict, self._TTLParameterDict)
        self._master.nidaqHelper.runScan(signalDic)
        self._master.nidaqHelper.scanDoneSignal.connect(self.scanDone)
        
    def scanDone(self):
        self._comm_channel.endScan()
     
    def getParameters(self):
        primDim = self._widget.primScanDim.currentText()
        secDim = self._widget.secScanDim.currentText()
        thirdDim = self._widget.thirdScanDim.currentText()
        self._stageParameterDict['Targets[3]'] = ('Stage_'+primDim, 'Stage_'+secDim, 'Stage_'+thirdDim)
        self._stageParameterDict['Sizes[3]'] = (float(self._widget.scanPar['size' + primDim].text()), float(self._widget.scanPar['size' + secDim].text()), float(self._widget.scanPar['size' + thirdDim].text()))
        self._stageParameterDict['Step_sizes[3]'] = (float(self._widget.scanPar['stepSize' + primDim].text()), float(self._widget.scanPar['stepSize' + secDim].text()), float(self._widget.scanPar['stepSize' + thirdDim].text()))
        start = self._comm_channel.getStartPos()
        self._stageParameterDict['Start[3]'] = (start[primDim], start[secDim], start[thirdDim])   
        for i in range(len(self._TTLParameterDict['Targets[x]'])):
            self._TTLParameterDict['TTLStarts[x,y]'][i] = [float(self._widget.pxParameters['sta' + self._TTLParameterDict['Targets[x]'][i]].text())/1000]
            self._TTLParameterDict['TTLEnds[x,y]'][i] = [float(self._widget.pxParameters['end' + self._TTLParameterDict['Targets[x]'][i]].text())/1000]
        self._TTLParameterDict['Sequence_time_seconds'] = float(self._widget.seqTimePar.text())/1000
        self._stageParameterDict['Sequence_time_seconds'] = float(self._widget.seqTimePar.text())/1000
        
        
    def setScanButton(self, b):
        self._widget.scanButton.setChecked(b)
        if b: self.runScan()
    
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
      

        



        
