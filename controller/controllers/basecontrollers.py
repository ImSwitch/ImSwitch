# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""

from pyqtgraph.Qt import QtCore
from controller.TempestaErrors import InvalidChildClassError


class WidgetControllerFactory():
    """Factory class for creating a WidgetController object. Factory checks
    that the new object is a valid WidgetController."""

    def __new__(cls, className, *args):
        widgetController = globals()[className](*args)
        if widgetController.isValidChild():
            return widgetController


class WidgetController(QtCore.QObject):
    """ Superclass for all WidgetControllers. 
            All WidgetControllers should have access to MasterController, CommunicationChannel and the linked Widget. """

    def __init__(self, comm_channel, master, widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Protected attributes, which should only be accessed from WidgetController and its subclasses
        self._master = master
        self._widget = widget
        self._comm_channel = comm_channel


class LiveUpdatedController(WidgetController):
    """ Superclass for those controllers that will update the widgets with an upcoming frame from the camera. 
            Should be either active or not, and have an update function. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = False

    def update(self, im, init):
        raise NotImplementedError


class SuperScanController(WidgetController):
    def __init__(self, comm_channel, master, widget):
        super().__init__(comm_channel, master, widget)
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
