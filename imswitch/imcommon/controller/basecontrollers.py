import traceback
import weakref

from imswitch.imcommon.framework import SignalInterface
from imswitch.imcommon.model import initLogger


class MainController:
    def closeEvent(self):
        pass


class WidgetController(SignalInterface):
    """ Superclass for all WidgetControllers. """

    def __init__(self, widget, factory, moduleCommChannel, *args, **kwargs):
        self._widget = widget
        self._factory = factory
        self._moduleCommChannel = moduleCommChannel
        self._logger = initLogger(self)
        super().__init__()

    def closeEvent(self):
        pass

    @classmethod
    def create(cls, widget, moduleCommChannel):
        """ Initialize a factory and create this controller with it. Returns
        the created controller. """
        factory = WidgetControllerFactory(moduleCommChannel)
        return factory.createController(cls, widget)


class WidgetControllerFactory:
    """ Factory class for creating a WidgetController object. """

    def __init__(self, moduleCommChannel, *args, **kwargs):
        self.__moduleCommChannel = moduleCommChannel
        self.__args = args
        self.__kwargs = kwargs
        self.__createdControllers = []

        self.__logger = initLogger(self, tryInheritParent=True)

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
                except Exception:
                    self.__logger.error(f'Error closing {type(controller).__name__}')
                    self.__logger.error(traceback.format_exc())


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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
