from imswitch.imcommon.view import guitools
from imswitch.imcommon.model import modulesconfigtools, ostools
from .basecontrollers import WidgetController


class MultiModuleWindowController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Connect signals
        self._widget.sigPickModules.connect(self.pickModules)

    def pickModules(self):
        """ Let the user change which modules are active. """

        moduleIds = guitools.PickModulesDialog.showAndWaitForResult(
            parent=self._widget, moduleIdsAndNamesDict=modulesconfigtools.getAvailableModules(),
            preselectedModules=modulesconfigtools.getEnabledModuleIds()
        )
        if moduleIds is None:
            return

        proceed = guitools.askYesNoQuestion(self._widget, 'Warning',
                                            'The software will restart. Continue?')
        if not proceed:
            return

        modulesconfigtools.setEnabledModuleIds(moduleIds)
        ostools.restartSoftware()
