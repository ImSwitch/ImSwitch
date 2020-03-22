# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
import controller.controllers as controllers
class TempestaController():
    
    def __init__(self, model, view):
        
        self.model = model
        self.view = view
        
        self.scanController = controllers.ScanController()
        self.multiScanController = controllers.MultipleScanController()
        self.focusLockController = controllers.FocusLockController()
        self.positionerController = controllers.PositionerController()
        self.uLensesController = controllers.ULensesController()
        self.alignXYController = controllers.AlignXYController()
        self.alignAverageController = controllers.AlignAverageController()
        self.alignmentController = controllers.AlignmentController()
        self.laserController = controllers.LaserController()
        self.fftController = controllers.FFTController()
        
        