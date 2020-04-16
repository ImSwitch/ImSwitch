# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
from controller.CameraHelper import CameraHelper
#from controller.ScanHelper import ScanHelper
from controller.RecordingHelper import RecordingHelper
from lantz import Q_

class MasterController():
    # This class will handle the communication between software and hardware, using the Helpers for each hardware set.
    def __init__(self, model, comm_channel):
        print('init master controller')
        self.__model = model
        self.stagePos = [0, 0, 0]
        self.__comm_channel = comm_channel
        self.cameraHelper = CameraHelper(self.__comm_channel, self.__model.cameras)
        self.recordingHelper = RecordingHelper(self.cameraHelper)
        #self.scanHelper = ScanHelper()  #Make sure compatibility 

       
    def moveStage(self, axis, dist):
        self.stagePos[axis] += dist
        return self.stagePos[axis]
        
    def toggleLaser(self, enable, laser):
        if enable:
            self.__model.lasers[laser].enabled = True
        else:
            self.__model.lasers[laser].enabled = False
        
    def changePower(self, power, laser):
        self.__model.lasers[laser].power_sp = power * Q_(1, 'mW')
        
    def digitalMod(self, digital, power, laser):
        laser = self.__model.lasers[laser]
        if digital:
            laser.enter_mod_mode()
            laser.power_mod = power * Q_(1, 'mW')
            print('Entered digital modulation mode with power :', power)
            print('Modulation mode is: ', laser.mod_mode)
        else:
            laser.digital_mod = False
            laser.query('cp')
            print('Exited digital modulation mode')
