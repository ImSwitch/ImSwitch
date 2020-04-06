# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
import controller.controllers as controllers
from controller.MasterController import MasterController

class TempestaController():
    
    def __init__(self, model, view):
        
        __model = model # Private
        __view = view #Private
        
        self.__comm_channel = CommunicationChannel(self)
        __masterController = MasterController(__model, self.__comm_channel) # Private
        
        
        self.scanController = controllers.ScanController(self.__comm_channel, __masterController, __view.scanWidget)
        self.positionerController = controllers.PositionerController(self.__comm_channel, __masterController, __view.positionerWidget) 
        self.uLensesController = controllers.ULensesController(self.__comm_channel, __masterController, __view.ulensesWidget)
        self.alignXYController = controllers.AlignXYController(self.__comm_channel, __masterController, __view.alignWidgetXY)
        self.alignAverageController = controllers.AlignAverageController(self.__comm_channel, __masterController, __view.alignWidgetAverage)
        self.alignmentController = controllers.AlignmentController(self.__comm_channel, __masterController, __view.alignmentWidget)
        self.laserController = controllers.LaserController(self.__comm_channel, __masterController, __view.laserWidgets)
        self.fftController = controllers.FFTController(self.__comm_channel, __masterController, __view.fftWidget)
        self.recorderController = controllers.RecorderController(self.__comm_channel, __masterController, __view.recordingWidget)
        self.viewController = controllers.ViewController(self.__comm_channel, __masterController, __view.viewCtrlWidget)
        self.imageController = controllers.ImageController(self.__comm_channel, __masterController, __view.imageWidget)
        self.settingsController = controllers.SettingsController(self.__comm_channel, __masterController, __view.settingsWidget)

class CommunicationChannel():
    def __init__(self, main):
        self.__main = main
    def updateImage(self, init):
        self.__main.imageController.update()
        self.__main.fftController.update()
        self.__main.alignXYController.update()
        self.__main.alignAverageController.update()
        if not init:
            self.__main.imageController.autoLevels(init)
            
    def adjustFrame(self, width, height):
        self.__main.imageController.adjustFrame(width, height)
        self.__main.viewController.updateGrid(width, height)
        
    def addItemTovb(self, item):
        self.__main.imageController.addItemTovb(item)

    def removeItemFromvb(self, item):
        self.__main.imageController.removeItemFromvb(item)
        
    def getROIdata(self, ROI):
        return  self.__main.imageController.getROIdata(ROI)
        
    def centerROI(self):
        return self.__main.imageController.centerROI()
        
