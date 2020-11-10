# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
from . import controllers
from .CommunicationChannel import CommunicationChannel
from .MasterController import MasterController


class TempestaController:
    def __init__(self, model, view):
        __model = model
        __view = view

        # Connect view signals
        __view.closing.connect(self.closeEvent)

        # Init communication channel and master controller
        self.__commChannel = CommunicationChannel(self)
        __masterController = MasterController(__model, self.__commChannel)

        # List of Controllers for the GUI Widgets
        factory = controllers.WidgetControllerFactory(
            model.setupInfo, self.__commChannel, __masterController
        )

        self.imageController = factory.createController(controllers.ImageController, __view.imageWidget)
        self.positionerController = factory.createController(controllers.PositionerController, __view.positionerWidget)
        self.scanController = factory.createController(controllers.ScanController, __view.scanWidget)
        self.laserController = factory.createController(controllers.LaserController, __view.laserWidgets)
        self.recorderController = factory.createController(controllers.RecorderController, __view.recordingWidget)
        self.viewController = factory.createController(controllers.ViewController, __view.viewWidget)
        self.settingsController = factory.createController(controllers.SettingsController, __view.settingsWidget)

        if model.setupInfo.availableWidgets.BeadRecWidget:
            self.beadController = factory.createController(controllers.BeadController, __view.beadRecWidget)

        if model.setupInfo.availableWidgets.ULensesWidget:
            self.uLensesController = factory.createController(controllers.ULensesController, __view.ulensesWidget)

        if model.setupInfo.availableWidgets.AlignWidgetXY:
            self.alignXYController = factory.createController(controllers.AlignXYController, __view.alignWidgetXY)

        if model.setupInfo.availableWidgets.AlignWidgetAverage:
            self.alignAverageController = factory.createController(controllers.AlignAverageController, __view.alignWidgetAverage)

        if model.setupInfo.availableWidgets.AlignmentLineWidget:
            self.alignmentLineController = factory.createController(controllers.AlignmentLineController, __view.alignmentLineWidget)

        if model.setupInfo.availableWidgets.FFTWidget:
            self.fftController = factory.createController(controllers.FFTController, __view.fftWidget)

        # Check widget compatibility
        __masterController.scanHelper._parameterCompatibility(self.scanController.parameterDict)

    def closeEvent(self):
        self.positionerController.closeEvent()
        self.laserController.closeEvent()
        self.viewController.closeEvent()
