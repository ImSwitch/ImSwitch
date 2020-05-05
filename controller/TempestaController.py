# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
import controller.controllers as controllers
from controller.MasterController import MasterController

class TempestaController():
    
    def __init__(self, model, view):
        
        __model = model 
        __view = view 
        
        self.__comm_channel = CommunicationChannel(self)
        __masterController = MasterController(__model, self.__comm_channel) 
        
        # List of Controllers for the GUI Widgets
        
        self.scanController = controllers.ScanController(self.__comm_channel, __masterController, __view.scanWidget)
        self.positionerController = controllers.PositionerController(self.__comm_channel, __masterController, __view.positionerWidget) 
        self.uLensesController = controllers.ULensesController(self.__comm_channel, __masterController, __view.ulensesWidget)
        self.alignXYController = controllers.AlignXYController(self.__comm_channel, __masterController, __view.alignWidgetXY)
        self.alignAverageController = controllers.AlignAverageController(self.__comm_channel, __masterController, __view.alignWidgetAverage)
        self.alignmentLineController = controllers.AlignmentLineController(self.__comm_channel, __masterController, __view.alignmentLineWidget)
        self.laserController = controllers.LaserController(self.__comm_channel, __masterController, __view.laserWidgets)
        self.fftController = controllers.FFTController(self.__comm_channel, __masterController, __view.fftWidget)
        self.recorderController = controllers.RecorderController(self.__comm_channel, __masterController, __view.recordingWidget)
        self.viewController = controllers.ViewController(self.__comm_channel, __masterController, __view.viewWidget)
        self.imageController = controllers.ImageController(self.__comm_channel, __masterController, __view.imageWidget)
        self.settingsController = controllers.SettingsController(self.__comm_channel, __masterController, __view.settingsWidget)
        
        
        #Check widget compatibility
        __masterController.scanHelper._parameterCompatibility(self.scanController.parameterDict)

    
class CommunicationChannel():
    # Communication Channel is a class that handles the communication between Master Controller and Widgets, or between Widgets 
    
    def __init__(self, main):
        self.__main = main
    
    def updateImage(self, init):
        # Called from Master Controller, it updates the Liveview and Liveview Updated Widgets
        self.__main.imageController.update()
        self.__main.fftController.update()
        self.__main.alignXYController.update()
        self.__main.alignAverageController.update()
        if not init:
            self.__main.imageController.autoLevels(init)
            
    def adjustFrame(self, width, height):
        self.__main.imageController.adjustFrame(width, height)
        
    def gridToggle(self):
        self.__main.imageController.gridToggle()
        
    def crosshairToggle(self):
        self.__main.imageController.crosshairToggle()
        
    def addItemTovb(self, item, *args, **kwargs):
        self.__main.imageController.addItemTovb(item, *args, **kwargs)

    def removeItemFromvb(self, item):
        self.__main.imageController.removeItemFromvb(item)
        
    def getROIdata(self, ROI):
        return  self.__main.imageController.getROIdata(ROI)
        
    def centerROI(self):
        # Returns the center of the VB to align the ROI
        return self.__main.imageController.centerROI()
        
    def endRecording(self):
        self.__main.recorderController.endRecording()
        
    def updateRecFrameNumber(self, f):
        self.__main.recorderController.updateRecFrameNumber(f)
        
    def updateRecTime(self, t):
        self.__main.recorderController.updateRecTime(t)
        
    def getCamAttrs(self):
        return self.__main.settingsController.getCamAttrs()
    
    def getScanAttrs(self):
        return self.__main.scanController.getScanAttrs()
        
    def prepareScan(self):
        self.__main.settingsController.setTriggerParam('External "frame-trigger"')
        self.__main.laserController.setDigitalButton(True)
        self.__main.scanController.setScanButton(True)
        
    def endScan(self):
        self.__main.settingsController.setTriggerParam('Internal trigger')
        self.__main.laserController.setDigitalButton(False)
        self.__main.scanController.setScanButton(False)
        
    def getStartPos(self):
        return self.__main.positionerController.getPos()        
        
    def moveZstage(self, step):
        self.__main.positionerController.move(2, step)
