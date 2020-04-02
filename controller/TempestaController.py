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
        
        self.comm_channel = CommunicationChannel(self)
        
        __masterController = MasterController(__model, self.comm_channel) # Private
        
        
        self.scanController = controllers.ScanController(self.comm_channel, __masterController, __view.scanWidget)
        self.positionerController = controllers.PositionerController(self.comm_channel, __masterController, __view.positionerWidget) 
        self.uLensesController = controllers.ULensesController(self.comm_channel, __masterController, __view.ulensesWidget)
        self.alignXYController = controllers.AlignXYController(self.comm_channel, __masterController, __view.alignWidgetXY)
        self.alignAverageController = controllers.AlignAverageController(self.comm_channel, __masterController, __view.alignWidgetAverage)
        self.alignmentController = controllers.AlignmentController(self.comm_channel, __masterController, __view.alignmentWidget)
        self.laserController = controllers.LaserController(self.comm_channel, __masterController, __view.laserWidgets)
        self.fftController = controllers.FFTController(self.comm_channel, __masterController, __view.fftWidget)
        self.recorderController = controllers.RecorderController(self.comm_channel, __masterController, __view.recordingWidget)
        self.viewController = controllers.ViewController(self.comm_channel, __masterController, __view.viewCtrlWidget)
        self.imageController = controllers.ImageController(self.comm_channel, __masterController, __view.imageWidget)

class CommunicationChannel():
    def __init__(self, main):
        self.__main = main
        
    def updateImage(self, img):
        self.__main.imageController.updateImage(img)
        
    def addItemTovb(self, item):
        self.__main.imageController.addItemTovb(item)

    def removeItemFromvb(self, item):
        self.__main.imageController.removeItemFromvb(item)
