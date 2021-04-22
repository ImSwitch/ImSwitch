from imswitch.imcommon.controller import WidgetController, MainController
from imswitch.imcommon.model import generateAPI, SharedAttributes
from imswitch.imcontrol.view import guitools
from .CommunicationChannel import CommunicationChannel
from .MasterController import MasterController
from . import controllers


class ImConMainController(MainController):
    def __init__(self, options, setupInfo, mainView, moduleCommChannel):
        self.__options = options
        self.__setupInfo = setupInfo
        self.__mainView = mainView
        self.__moduleCommChannel = moduleCommChannel

        # Connect view signals
        self.__mainView.sigLoadParamsFromHDF5.connect(self.loadParamsFromHDF5)
        self.__mainView.sigClosing.connect(self.closeEvent)

        # Init communication channel and master controller
        self.__commChannel = CommunicationChannel(self)
        self.__masterController = MasterController(self.__setupInfo, self.__commChannel,
                                                   self.__moduleCommChannel)

        # List of Controllers for the GUI Widgets
        self.__factory = controllers.ImConWidgetControllerFactory(
            self.__setupInfo, self.__masterController, self.__commChannel, self.__moduleCommChannel
        )

        self.imageController = self.__factory.createController(controllers.ImageController, self.__mainView.imageWidget)
        self.positionerController = self.__factory.createController(
            controllers.PositionerController, self.__mainView.positionerWidget)
        self.scanController = self.__factory.createController(controllers.ScanController, self.__mainView.scanWidget)
        self.laserController = self.__factory.createController(controllers.LaserController, self.__mainView.laserWidgets)
        self.recorderController = self.__factory.createController(controllers.RecorderController, self.__mainView.recordingWidget)
        self.viewController = self.__factory.createController(controllers.ViewController, self.__mainView.viewWidget)
        self.settingsController = self.__factory.createController(controllers.SettingsController, self.__mainView.settingsWidget)

        if self.__setupInfo.availableWidgets.BeadRecWidget:
            self.beadController = self.__factory.createController(controllers.BeadController, self.__mainView.beadRecWidget)

        if self.__setupInfo.availableWidgets.ULensesWidget:
            self.uLensesController = self.__factory.createController(controllers.ULensesController, self.__mainView.ulensesWidget)

        if self.__setupInfo.availableWidgets.AlignWidgetXY:
            self.alignXYController = self.__factory.createController(controllers.AlignXYController, self.__mainView.alignWidgetXY)

        if self.__setupInfo.availableWidgets.AlignWidgetAverage:
            self.alignAverageController = self.__factory.createController(
                controllers.AlignAverageController, self.__mainView.alignWidgetAverage)

        if self.__setupInfo.availableWidgets.AlignmentLineWidget:
            self.alignmentLineController = self.__factory.createController(
                controllers.AlignmentLineController, self.__mainView.alignmentLineWidget)

        if self.__setupInfo.availableWidgets.FFTWidget:
            self.fftController = self.__factory.createController(controllers.FFTController, self.__mainView.fftWidget)

        if self.__setupInfo.availableWidgets.SLMWidget:
            self.slmController = self.__factory.createController(controllers.SLMController, self.__mainView.slmWidget)

        if self.__setupInfo.availableWidgets.FocusLockWidget:
            self.focuslockController = self.__factory.createController(controllers.FocusLockController, self.__mainView.focusLockWidget)

        if self.__setupInfo.availableWidgets.MotCorrWidget:
            self.motcorrController = self.__factory.createController(controllers.MotCorrController, self.__mainView.motCorrWidget)

        self.__mainView.setDetectorRelatedDocksVisible(
            self.__masterController.detectorsManager.hasDevices()
        )

        # Check widget compatibility
        self.__masterController.scanManager._parameterCompatibility(self.scanController.parameterDict)

        # Generate API
        self.__api = None
        apiObjs = [getattr(self, obj) for obj in dir(self)
                   if isinstance(getattr(self, obj), WidgetController)]
        apiObjs.append(self.__commChannel)
        self.__api = generateAPI(apiObjs)

    @property
    def api(self):
        return self.__api

    def loadParamsFromHDF5(self):
        """ Set detector, positioner, laser etc. params from values saved in a
        user-picked HDF5 snap/recording. """

        filePath = guitools.askForFilePath(self.__mainView, 'Open HDF5 file', nameFilter='*.hdf5')
        if not filePath:
            return

        attrs = SharedAttributes.fromHDF5File(filePath)
        self.__commChannel.sharedAttrs.update(attrs)

    def closeEvent(self):
        self.__factory.closeAllCreatedControllers()
        self.__masterController.closeEvent()


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

