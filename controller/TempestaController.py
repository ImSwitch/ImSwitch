# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
from . import controllers
from .CommunicationChannel import CommunicationChannel
from .MasterController import MasterController
from .presets import Preset


class TempestaController:
    def __init__(self, model, view):
        self.__model = model
        self.__view = view

        defaultPreset = Preset.getDefault(self.__view.presetDir)

        # Connect view signals
        self.__view.loadPresetButton.pressed.connect(self.loadPreset)
        self.__view.closing.connect(self.closeEvent)

        # Init communication channel and master controller
        self.__commChannel = CommunicationChannel(self)
        __masterController = MasterController(self.__model, self.__commChannel)

        # List of Controllers for the GUI Widgets
        self.__factory = controllers.WidgetControllerFactory(
            model.setupInfo, defaultPreset, self.__commChannel, __masterController
        )

        self.imageController = self.__factory.createController(controllers.ImageController, self.__view.imageWidget)
        self.positionerController = self.__factory.createController(controllers.PositionerController, self.__view.positionerWidget)
        self.scanController = self.__factory.createController(controllers.ScanController, self.__view.scanWidget)
        self.laserController = self.__factory.createController(controllers.LaserController, self.__view.laserWidgets)
        self.recorderController = self.__factory.createController(controllers.RecorderController, self.__view.recordingWidget)
        self.viewController = self.__factory.createController(controllers.ViewController, self.__view.viewWidget)
        self.settingsController = self.__factory.createController(controllers.SettingsController, self.__view.settingsWidget)

        if model.setupInfo.availableWidgets.BeadRecWidget:
            self.beadController = self.__factory.createController(controllers.BeadController, self.__view.beadRecWidget)

        if model.setupInfo.availableWidgets.ULensesWidget:
            self.uLensesController = self.__factory.createController(controllers.ULensesController, self.__view.ulensesWidget)

        if model.setupInfo.availableWidgets.AlignWidgetXY:
            self.alignXYController = self.__factory.createController(controllers.AlignXYController, self.__view.alignWidgetXY)

        if model.setupInfo.availableWidgets.AlignWidgetAverage:
            self.alignAverageController = self.__factory.createController(controllers.AlignAverageController, self.__view.alignWidgetAverage)

        if model.setupInfo.availableWidgets.AlignmentLineWidget:
            self.alignmentLineController = self.__factory.createController(controllers.AlignmentLineController, self.__view.alignmentLineWidget)

        if model.setupInfo.availableWidgets.FFTWidget:
            self.fftController = self.__factory.createController(controllers.FFTController, self.__view.fftWidget)

        # Check widget compatibility
        __masterController.scanHelper._parameterCompatibility(self.scanController.parameterDict)

    def loadPreset(self):
        self.__factory.loadPresetForAllCreatedControllers(
            self.__view.presetDir, self.__view.presetsMenu.currentText()
        )

    def closeEvent(self):
        self.__factory.closeAllCreatedControllers()
