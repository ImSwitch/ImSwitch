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
        
        self.focusLockController = controllers.FocusLockController()
        self.scanController = controllers.ScanController()
        self.multiScanController = controllers.MultipleScanController()
        
        