import webbrowser

import psutil

import imswitch
from imswitch.imcommon.framework import Timer
from imswitch.imcommon.model import dirtools, modulesconfigtools, ostools, APIExport
from imswitch.imcommon.view import guitools
from .CheckUpdatesController import CheckUpdatesController
from .PickModulesController import PickModulesController
from .basecontrollers import WidgetController


class MultiModuleWindowController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pickModulesController = self._factory.createController(
            PickModulesController, self._widget.pickModulesDialog
        )
        self.checkUpdatesController = self._factory.createController(
            CheckUpdatesController, self._widget.checkUpdatesDialog
        )

        self._moduleIdNameMap = {}

        self._updateMemBarTimer = Timer()
        self._updateMemBarTimer.timeout.connect(self.updateRAMUsage)
        self._updateMemBarTimer.start(1000)

        self.updateRAMUsage()

        # Connect signals
        self._widget.sigPickModules.connect(self.pickModules)
        self._widget.sigOpenUserDir.connect(self.openUserDir)
        self._widget.sigShowDocs.connect(self.showDocs)
        self._widget.sigCheckUpdates.connect(self.checkUpdates)
        self._widget.sigShowAbout.connect(self.showAbout)

        self._widget.sigModuleAdded.connect(self.moduleAdded)

    def pickModules(self):
        """ Let the user change which modules are active. """

        self.pickModulesController.setModules(modulesconfigtools.getAvailableModules())
        self.pickModulesController.setSelectedModules(modulesconfigtools.getEnabledModuleIds())
        if not self._widget.showPickModulesDialogBlocking():
            return
        moduleIds = self.pickModulesController.getSelectedModules()
        if not moduleIds:
            return

        proceed = guitools.askYesNoQuestion(self._widget, 'Warning',
                                            'The software will restart. Continue?')
        if not proceed:
            return

        modulesconfigtools.setEnabledModuleIds(moduleIds)
        ostools.restartSoftware()

    def openUserDir(self):
        """ Shows the user files directory in system file explorer. """
        ostools.openFolderInOS(dirtools.UserFileDirs.Root)

    def showDocs(self):
        """ Opens the ImSwitch documentation in a web browser. """
        webbrowser.open(f'https://imswitch.readthedocs.io/en/v{imswitch.__version__}/')

    def checkUpdates(self):
        """ Checks if there are any updates to ImSwitch available and notifies
        the user. """
        self.checkUpdatesController.checkForUpdates()
        self._widget.showCheckUpdatesDialogBlocking()

    def showAbout(self):
        """ Shows an "about" dialog. """
        self._widget.showAboutDialogBlocking()

    def moduleAdded(self, moduleId, moduleName):
        self._moduleIdNameMap[moduleId] = moduleName

    def updateRAMUsage(self):
        self._widget.updateRAMUsage(psutil.virtual_memory()[2] / 100)

    @APIExport
    def setCurrentModule(self, moduleId: str) -> None:
        """ Sets the currently displayed module to the module with the
        specified ID (e.g. "imcontrol"). """
        moduleName = self._moduleIdNameMap[moduleId]
        self._widget.setSelectedModule(moduleName)
