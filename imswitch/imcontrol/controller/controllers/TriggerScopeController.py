from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger


class TriggerScopeController(ImConWidgetController):
    """ Linked to TriggerScopeWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self)

        # Connect PositionerWidget signals
        self._widget.sigRunToggled.connect(self.run)
        self._master.triggerScopeManager.test()

    def run(self):
        self.__logger.debug("Run button clicked")
        self._master.triggerScopeManager.run()

