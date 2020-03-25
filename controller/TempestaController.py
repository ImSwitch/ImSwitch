# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
import controller.controllers as controllers
from controller.MasterController import MasterController

class TempestaController():
    
    def __init__(self, model, view):
        
        self.model = model
        self.view = view
        
        self.masterController = MasterController()
        
        self.scanController = controllers.ScanController(self.masterController, self.view.scanWidget)
        self.focusLockController = controllers.FocusLockController(self.masterController, self.view.focusLockWidget)
        self.positionerController = controllers.PositionerController(self.masterController, self.view.positionerWidget) 
        self.uLensesController = controllers.ULensesController(self.masterController, self.view.ulensesWidget)
        self.alignXYController = controllers.AlignXYController(self.masterController, self.view.alignWidgetXY)
        self.alignAverageController = controllers.AlignAverageController(self.masterController, self.view.alignWidgetAverage)
        self.alignmentController = controllers.AlignmentController(self.masterController, self.view.alignmentWidget)
        self.laserController = controllers.LaserController(self.masterController, self.view.laserWidgets)
        self.fftController = controllers.FFTController(self.masterController, self.view.fftWidget)
        self.recorderController = controllers.RecorderController(self.masterController, self.view.recordingWidget)
        self.viewController = controllers.ViewController(self.masterController, self.view.viewCtrlWidget)
        self.imageController = controllers.ImageController(self.masterController, self.view.imageWidget)
