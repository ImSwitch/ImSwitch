from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger
import numpy as np

class TriggerScopeController(ImConWidgetController):
    """ Linked to TriggerScopeWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Connect PositionerWidget signals
        self._widget.sigRunToggled.connect(self.run)

    def run(self):
        self._master.triggerScopeManager.send("*", 1)
        self.increment = float(self._widget.incrementVoltage.text())
        self.slope = float(self._widget.setSlope.text())
        self.finalVoltage = float(self._widget.setVoltage.value())
        self._widget.currentVoltage.setText(str(round(self.finalVoltage, 3)))
        self.current = float(self._widget.currentVoltage.text())
        steps = int(np.ceil(np.abs(self.finalVoltage - self.current) / self.slope)) + 1
        dacarray = np.linspace(self.current, self.finalVoltage, steps)
        ttlarray = np.ones(steps, dtype=int)
        self._logger.debug(str(len(dacarray)))
        params = self.setParams(1, 1, len(dacarray), 0, 0, 1)
        self._master.triggerScopeManager.run_wave(dacarray, ttlarray, params)

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

