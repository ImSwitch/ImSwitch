# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
import controller.controllers as controllers
import controller.MasterController as MasterController

class TempestaController():
    
    def __init__(self, model, view):
        
        self.model = model
        self.view = view
        
        self.masterController = MasterController()
        
        self.scanController = controllers.ScanController(self.masterController, self.view.scanWidget)
        self.focusLockController = controllers.FocusLockController(self.masterController, self.view.focusLockwidget)
        self.positionerController = controllers.PositionerController(self.masterController, self.view.positionerWidget) 
        self.uLensesController = controllers.ULensesController(self.masterController, self.view.ulensesWidget)
        self.alignXYController = controllers.AlignXYController(self.masterController)
        self.alignAverageController = controllers.AlignAverageController(self.masterController)
        self.alignmentController = controllers.AlignmentController(self.masterController)
        self.laserController = controllers.LaserController(self.masterController)
        self.fftController = controllers.FFTController(self.masterController)
        self.recorderController = controllers.RecorderController(self.masterController)
        self.viewController = controllers.ViewController(self.masterController)
        self.imageController = controllers.ImageController(self.masterController)
        
        # master controller