# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np
import view.guitools as guitools
import pyqtgraph as pg

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
        self._widget.tree.p.param('Model').setValue(self._master.cameraHelper.model)
        self.umxpx = self._widget.tree.p.param('Pixel size').value()
        framePar = self._widget.tree.p.param('Image frame')
        self.binPar = framePar.param('Binning')
        self.FrameMode = framePar.param('Mode')
        self.X0par = framePar.param('X0')
        self.Y0par = framePar.param('Y0')
        self.widthPar = framePar.param('Width')
        self.heightPar = framePar.param('Height')
        self.applyParam = framePar.param('Apply')
        self.NewROIParam = framePar.param('New ROI')
        self.AbortROIParam = framePar.param('Abort ROI')
        
        timingsPar = self._widget.tree.p.param('Timings')
        self.EffFRPar = timingsPar.param('Internal frame rate')
        self.expPar = timingsPar.param('Set exposure time')
        self.ReadoutPar = timingsPar.param('Readout time')
        self.RealExpPar = timingsPar.param('Real exposure time')
        self.FrameInt = timingsPar.param('Internal frame interval')
        self.RealExpPar.setOpts(decimals=5)
        
        acquisParam = self._widget.tree.p.param('Acquisition mode')
        self.trigsourceparam = acquisParam.param('Trigger source')
        
        self.applyParam.sigStateChanged.connect(self.adjustFrame)
        self.NewROIParam.sigStateChanged.connect(self.updateFrame)
        self.AbortROIParam.sigStateChanged.connect(self.abortROI)
        self.trigsourceparam.sigValueChanged.connect(self.changeTriggerSource)
        self.expPar.sigValueChanged.connect(self.setExposure)
        self.binPar.sigValueChanged.connect(self.setBinning)
        self.FrameMode.sigValueChanged.connect(self.updateFrame)
        self.expPar.sigValueChanged.connect(self.setExposure)            
            
    def adjustFrame(self):
        """ Crop camera and adjust frame. """
        binning = self.binPar.value()
        width = self.widthPar.value()
        height = self.heightPar.value()
        X0par = self.X0par.value()
        Y0par = self.Y0par.value()
        
        # Round to closest "divisable by 4" value.
        vpos = binning*X0par
        hpos = binning*Y0par
        vsize = binning*width
        hsize = binning*height
        
        # Only if the new FOV is not Full chip
        if not (vpos == 0 and hpos == 0 and vsize == 2048 and hsize == 2048):
            vpos = int(128 * np.ceil(vpos / 128))
            hpos = int(128 * np.ceil(hpos / 128))
            vsize = int(128 * np.ceil(vsize / 128))
            hsize = int(128 * np.ceil(hsize / 128))
            minroi = 64
            vsize = int(min(2048 - vpos, minroi * np.ceil(vsize / minroi)))
            hsize = int(min(2048 - hpos, minroi * np.ceil(hsize / minroi)))
        
        self._master.cameraHelper.changeParameter(lambda: self._master.cameraHelper.cropOrca(vpos, hpos, vsize, hsize))

        # Final shape values might differ from the user-specified one because of camera limitation x128
        width, height = self._master.cameraHelper.shapes
        self._comm_channel.adjustFrame(width, height)
        self._widget.ROI.hide()
        frameStart = self._master.cameraHelper.frameStart
        self.X0par.setValue(frameStart[0])
        self.Y0par.setValue(frameStart[1])
        self.widthPar.setValue(width)
        self.heightPar.setValue(height)
        self.updateTimings(self._master.cameraHelper.getTimings())
             
    def ROIchanged(self):
        """ Update parameters according to ROI. """
        frameStart = self._master.cameraHelper.frameStart
        pos = self._widget.ROI.pos()
        size = self._widget.ROI.size()
        self.X0par.setValue(frameStart[0] + int(pos[0]))
        self.Y0par.setValue(frameStart[1] + int(pos[1]))

        self.widthPar.setValue(int(size[0]))   # [0] is Width
        self.heightPar.setValue(int(size[1]))  # [1] is Height
        
    def abortROI(self):
        """ Cancel and reset parameters of the ROI. """
        self._widget.toggleROI(False)
        frameStart = self._master.cameraHelper.frameStart
        shapes = self._master.cameraHelper.shapes
        self.X0par.setValue(frameStart[0])
        self.Y0par.setValue(frameStart[1])
        self.widthPar.setValue(shapes[0])
        self.heightPar.setValue(shapes[1])
        
    def changeTriggerSource(self):
        """ Change trigger (Internal or External). """
        self._master.cameraHelper.changeTriggerSource(self._widget.trigsourceparam.value())
        
    def updateTimings(self, params):
        """ Update the real exposure times from the camera. """
        self.RealExpPar.setValue(params[0])
        self.FrameInt.setValue(params[1])
        self.ReadoutPar.setValue(params[2])
        self.EffFRPar.setValue(params[3])
        
    def setExposure(self):
        """ Update a new exposure time to the camera. """
        params = self._master.cameraHelper.setExposure(self.expPar.value())
        self.updateTimings(params)
        
    def setBinning(self):
        """ Update a new binning to the camera. """
        self._master.cameraHelper.setBinning(self.binPar.value())
        
    def updateFrame(self, controller):
        """ Change the image frame size and position in the sensor. """
        frameParam = self._widget.tree.p.param('Image frame')
        if frameParam.param('Mode').value() == 'Custom':
            self.X0par.setWritable(True)
            self.Y0par.setWritable(True)
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
            self.X0par.setWritable(False)
            self.Y0par.setWritable(False)
            self.widthPar.setWritable(False)
            self.heightPar.setWritable(False)

            # Change this to config File.
            if frameParam.param('Mode').value() == 'Full chip':
                self.X0par.setValue(0)
                self.Y0par.setValue(0)
                self.widthPar.setValue(2048)
                self.heightPar.setValue(2048)
               
                self.adjustFrame()
        
  
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
      

# Hardware control
        

class PositionerController(WidgetController): 
    """ Linked to PositionerWidget."""
    
    def move(self, axis, dist):
        """ Moves the piezzos in x y or z (axis) by dist micrometers. """
        newPos = self._master.moveStage(axis, dist)
        newText = "<strong>" + ['x', 'y', 'z'][axis] + " = {0:.2f} µm</strong>".format(newPos)
        
        getattr(self._widget, ['x', 'y', 'z'][axis] + "Label").setText(newText)

class LaserController(WidgetController): 
    """ Linked to LaserWidget."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digMod = False
        
    def toggleLaser(self, laser):
        """ Enable or disable laser (on/off)."""
        if not self.digMod:
            if self._widget.laserModules[laser].enableButton.isChecked():
                self._master.toggleLaser(True, laser)
            else:
                self._master.toggleLaser(False, laser)
                
    def changeSlider(self, laser):
        """ Change power with slider magnitude. """
        if not self.digMod:
            magnitude =  self._widget.laserModules[laser].slider.value() 
            self._master.changePower(magnitude, laser)
            self._widget.laserModules[laser].setPointEdit.setText(str(magnitude))
            
    def changeEdit(self, laser):
        """ Change power with edit magnitude. """
        if not self.digMod:
            magnitude = float(self._widget.laserModules[laser].setPointEdit.text())
            self._master.changePower(magnitude, laser)
            self._widget.laserModules[laser].slider.setValue(magnitude)
            
            
    def updateDigitalPowers(self, lasers):
        """ Update the powers if the digital mod is on. """
        self.digMod = self.digModule.DigitalControlButton.isChecked()
        if self.digMod:
            for i in np.arange(len(lasers)):
                laser = lasers[i]
                self._master.changePower(self._widget.digModule.powers[laser], laser)
            
    def GlobalDigitalMod(self, lasers):
        """ Start digital modulation. """
        self.digMod = self.digModule.DigitalControlButton.isChecked()
        if self.digMod:
            for i in np.arange(len(lasers)):
                laser = lasers[i]
                self._master.digModule(True, self._widget.digModule.powers[laser], laser)
        

# Scan control


class ScanController(WidgetController): # TODO
    def __init__(self, comm_channel, master, widget):
        super().__init__(comm_channel, master, widget)
        self.multipleScanController = MultipleScanController(comm_channel, master, widget.multiScanWgt)
        self.parameter_dictionary = None
        self.stageParameterList = []
        self.TTLcycleParameterList = []
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
    def parametersToSend(self):
        return (self.stageParameterList, self.TTLcycleParameterList) #Some list of parameters
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
    def toggleREC(self):
        if self._widget.recButton.isChecked():
            self._master.recordingHelper.startRecording()
        else:
            self._master.recordingHelper.endRecording()
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