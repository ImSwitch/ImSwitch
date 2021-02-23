# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
from imcommon.controller import WidgetController, WidgetControllerFactory
from imcontrol.model import InvalidChildClassError


class ImConWidgetControllerFactory(WidgetControllerFactory):
    """ Factory class for creating a ImConWidgetController object. """

    def __init__(self, setupInfo, master, commChannel, moduleCommChannel):
        super().__init__(setupInfo=setupInfo, master=master, commChannel=commChannel,
                         moduleCommChannel=moduleCommChannel)


class ImConWidgetController(WidgetController):
    """ Superclass for all ImConWidgetController.
    All WidgetControllers should have access to the setup information,
    MasterController, CommunicationChannel and the linked Widget. """

    def __init__(self, setupInfo, commChannel, master, *args, **kwargs):
        # Protected attributes, which should only be accessed from controller and its subclasses
        self._setupInfo = setupInfo
        self._commChannel = commChannel
        self._master = master

        # Init superclass
        super().__init__(*args, **kwargs)


class LiveUpdatedController(ImConWidgetController):
    """ Superclass for those controllers that will update the widgets with an
    upcoming frame from the camera.  Should be either active or not, and have
    an update function. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = False

    def update(self, im, init):
        raise NotImplementedError


class SuperScanController(ImConWidgetController):
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
