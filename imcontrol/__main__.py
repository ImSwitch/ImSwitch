from imcommon import prepareApp, launchApp
from imcommon.controller import ModuleCommunicationChannel
import imcontrol


app = prepareApp()
moduleCommChannel = ModuleCommunicationChannel()
moduleCommChannel.register(imcontrol)
mainView, mainController = imcontrol.getMainViewAndController(moduleCommChannel)
launchApp(app, mainView, [mainController])
