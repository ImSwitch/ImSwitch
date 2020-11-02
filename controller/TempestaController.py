# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
from . import controllers
from .CommunicationChannel import CommunicationChannel
from .MasterController import MasterController


class TempestaController():

    def __init__(self, model, view):
        __model = model
        __view = view

        # Connect view signals
        __view.closing.connect(self.closeEvent)

        # Init communication channel and master controller
        self.__comm_channel = CommunicationChannel(self)
        __masterController = MasterController(__model, self.__comm_channel)

        # List of Controllers for the GUI Widgets
        self.imageController = controllers.ImageController(self.__comm_channel, __masterController, __view.imageWidget)
        self.scanController = controllers.ScanController(self.__comm_channel, __masterController, __view.scanWidget)
        self.beadController = controllers.BeadController(self.__comm_channel, __masterController, __view.beadRecWidget)
        self.positionerController = controllers.PositionerController(self.__comm_channel, __masterController, __view.positionerWidget) 
        self.uLensesController = controllers.ULensesController(self.__comm_channel, __masterController, __view.ulensesWidget)
        self.alignXYController = controllers.AlignXYController(self.__comm_channel, __masterController, __view.alignWidgetXY)
        self.alignAverageController = controllers.AlignAverageController(self.__comm_channel, __masterController, __view.alignWidgetAverage)
        self.alignmentLineController = controllers.AlignmentLineController(self.__comm_channel, __masterController, __view.alignmentLineWidget)
        self.laserController = controllers.LaserController(self.__comm_channel, __masterController, __view.laserWidgets)
        self.fftController = controllers.FFTController(self.__comm_channel, __masterController, __view.fftWidget)
        self.recorderController = controllers.RecorderController(self.__comm_channel, __masterController, __view.recordingWidget)
        self.viewController = controllers.ViewController(self.__comm_channel, __masterController, __view.viewWidget)
        self.settingsController = controllers.SettingsController(self.__comm_channel, __masterController, __view.settingsWidget)

        #Check widget compatibility
        __masterController.scanHelper._parameterCompatibility(self.scanController.parameterDict)

    def closeEvent(self):
        self.positionerController.closeEvent()
        self.laserController.closeEvent()
        self.viewController.closeEvent()
