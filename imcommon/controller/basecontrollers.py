import traceback
import weakref

from imcommon.framework import SignalInterface


class MainController:
    def closeEvent(self):
        pass


class WidgetController(SignalInterface):
    """ Superclass for all WidgetControllers. """

    def __init__(self, widget, factory, moduleCommChannel):
        self._widget = widget
        self._factory = factory
        self._moduleCommChannel = moduleCommChannel
        super().__init__()

    def closeEvent(self):
        pass


class WidgetControllerFactory:
    """ Factory class for creating a WidgetController object. """

    def __init__(self, moduleCommChannel, *args, **kwargs):
        self.__moduleCommChannel = moduleCommChannel
        self.__args = args
        self.__kwargs = kwargs
        self.__createdControllers = []

    def createController(self, controllerClass, widget, *args, **kwargs):
        controller = controllerClass(*self.__args, *args,
                                     widget=widget, factory=self,
                                     moduleCommChannel=self.__moduleCommChannel,
                                     **self.__kwargs, **kwargs)
        self.__createdControllers.append(weakref.ref(controller))
        return controller

    def closeAllCreatedControllers(self):
        for controllerRef in self.__createdControllers:
            controller = controllerRef()
            if controller is not None:
                try:
                    controller.closeEvent()
                except:
                    print(f'Error closing {type(controller).__name__}')
                    print(traceback.format_exc())

# Copyright (C) 2020, 2021 TestaLab
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License