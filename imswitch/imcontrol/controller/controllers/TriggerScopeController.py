from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger


class TriggerScopeController(ImConWidgetController):
    """ Linked to TriggerScopeWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Connect PositionerWidget signals
        self._widget.sigRunToggled.connect(self.run)

    def run(self):
        self._master.triggerScopeManager.send("*", 1)
        params = self.setParams(1, 1, 1, 0, 0, 1)
        self._master.triggerScopeManager.run_wave([1], [1], params)
        #self._master.triggerScopeManager.sendAnalog(1, 1)
        
    def setParams(self, analogLine, digitalLine, length, trigMode, delay, reps):
        params = dict([])
        params["analogLine"] = analogLine
        params["digitalLine"] = digitalLine
        params["length"] = length
        params["trigMode"] = trigMode
        params["delay"] = delay
        params["reps"] = reps
        return params

