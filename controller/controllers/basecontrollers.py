# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import traceback
import weakref
from pyqtgraph.Qt import QtCore
from controller.errors import InvalidChildClassError
from controller.presets import Preset


class WidgetControllerFactory:
    """Factory class for creating a WidgetController object. Factory checks
    that the new object is a valid WidgetController."""

    def __init__(self, setupInfo, defaultPreset, commChannel, masterController):
        self._setupInfo = setupInfo
        self._defaultPreset = defaultPreset
        self._commChannel = commChannel
        self._master = masterController
        self._createdControllers = []

    def createController(self, controllerClass, widget, *args, **kwargs):
        controller = controllerClass(self._setupInfo, self._defaultPreset, self._commChannel,
                                     self._master, widget, *args, **kwargs)

        self._createdControllers.append(weakref.ref(controller))
        return controller

    def loadPresetForAllCreatedControllers(self, presetDir, presetFileName):
        preset = Preset.fromFile(presetDir, presetFileName)

        for controllerRef in self._createdControllers:
            controller = controllerRef()
            if controller is not None:
                controller.loadPreset(preset)

    def closeAllCreatedControllers(self):
        for controllerRef in self._createdControllers:
            controller = controllerRef()
            if controller is not None:
                try:
                    controller.closeEvent()
                except:
                    print('Error closing ' + type(controller).__name__)
                    print(traceback.format_exc())


class WidgetController(QtCore.QObject):
    """ Superclass for all WidgetControllers.
    All WidgetControllers should have access to the setup information,
    MasterController, CommunicationChannel and the linked Widget. """

    def __init__(self, setupInfo, defaultPreset, commChannel, master, widget, *args, **kwargs):
        # Protected attributes, which should only be accessed from WidgetController and its subclasses
        self._setupInfo = setupInfo
        self._defaultPreset = defaultPreset
        self._commChannel = commChannel
        self._master = master
        self._widget = widget

        # Init superclass
        super().__init__(*args, **kwargs)

    def loadPreset(self, preset):
        pass

    def closeEvent(self):
        pass


class LiveUpdatedController(WidgetController):
    """ Superclass for those controllers that will update the widgets with an upcoming frame from the camera. 
            Should be either active or not, and have an update function. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = False

    def update(self, im, init):
        raise NotImplementedError


class SuperScanController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self._stageParameterDict = None
        # self._TTLParameterDict = None
        # Make non-overwritable functions
        self.isValidScanController = self.__isValidScanController
        self.isValidChild = self.isValidScanController

    # @property
    # def stageParameterList(self):
    #     if self._stageParameterDict is None:
    #         raise ValueError('Scan controller has no parameters defined')
    #     else:
    #         return [*self._stageParameterDict] #makes list of dict keys

    # @property
    # def TTLParameterList(self):
    #     if self._TTLParameterDict is None:
    #         raise ValueError('Scan controller has no parameters defined')
    #     else:
    #         return [*self._TTLParameterDict] #makes list of dict keys

    @property
    def parameterDict(self):
        return None

    def __isValidScanController(self):
        if self.parameterDict is None:
            raise InvalidChildClassError('ScanController needs to return a valid parameterDict')
        else:
            return True
