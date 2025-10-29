import json
import os

import numpy as np
from pathlib import Path
from imswitch.imcommon.model import dirtools, initLogger
from imswitch.imcontrol.view import guitools
from ..basecontrollers import ImConWidgetController


class SLMsController(ImConWidgetController):
    """Linked to SLMsWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self._slmNames = {} #{slm_key (widget): slmName (Manager)}

        for slmName, slmManager in self._master.slmsManager:
            slm_key = self._widget.addSlm(slmName,slmManager.slmInfo)
            self._slmNames[slm_key]=slmName

        self._widget.sigConnectSLMusb.connect(self.connect)
        self._widget.sigUpdatePattern.connect(self.onUpdatePattern)
        self._widget.sigComputeCGH.connect(self.onComputeCgh)
    

    def onUpdatePattern(self, slm_key, params):
        print(f"[Controller] Update Pattern for {slm_key}")
        print(json.dumps(params, indent=2))

    def onComputeCgh(self, slm_key, cgh_params):
        print(f"[Controller] Compute CGH for {slm_key}")
        print(json.dumps(cgh_params, indent=2))

    def connect(self, slmKey: str, state: bool):
        """Handle connection/disconnection requests."""
        slmName = self._slmNames[slmKey]
        if state:
            success, serial = self._master.slmsManager.execOn(
                slmName, lambda l: l.connect_to_device()
            )
            self._widget.onConnectionResult(slmKey, success, serial)
        else:
            success, msg = self._master.slmsManager.execOn(
                slmName, lambda l: l.close_device()
            )
            self._widget.onDisconnectionResult(slmKey, success, msg)


    
