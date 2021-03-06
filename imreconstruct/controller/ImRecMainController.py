from imcommon.controller import MainController
from .CommunicationChannel import CommunicationChannel
from .basecontrollers import ImRecWidgetControllerFactory
from .ImRecMainViewController import ImRecMainViewController


class ImRecMainController(MainController):
    def __init__(self, mainView, moduleCommChannel):
        self.__mainView = mainView
        self.__moduleCommChannel = moduleCommChannel

        # Connect view signals
        self.__mainView.sigClosing.connect(self.closeEvent)

        # Init communication channel and master controller
        self.__commChannel = CommunicationChannel()

        # List of Controllers for the GUI Widgets
        self.__factory = ImRecWidgetControllerFactory(
            self.__commChannel, self.__moduleCommChannel
        )

        self.mainViewController = self.__factory.createController(
            ImRecMainViewController, self.__mainView
        )

    def closeEvent(self):
        self.__factory.closeAllCreatedControllers()
