import copy

from .basecontrollers import ImRecWidgetController


class ScanParamsController(ImRecWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._parDict = {
            'dimensions': [self._widget.r_l_text, self._widget.u_d_text, self._widget.b_f_text,
                           self._widget.timepoints_text],
            'directions': [self._widget.p_text, self._widget.p_text, self._widget.p_text],
            'steps': ['35', '35', '1', '1'],
            'step_sizes': ['35', '35', '35', '1'],
            'unidirectional': True
        }

        self._commChannel.sigScanParamsUpdated.connect(self.scanParamsUpdated)
        self._widget.sigApplyParams.connect(self.applyParams)

        self._widget.updateValues(self._parDict)

    def scanParamsUpdated(self, parDict):
        self._parDict = parDict
        self._widget.updateValues(self._parDict)

    def applyParams(self):
        self._parDict['dimensions'] = self._widget.getDimensions()
        self._parDict['directions'] = self._widget.getDirections()
        self._parDict['steps'] = self._widget.getSteps()
        self._parDict['step_sizes'] = self._widget.getStepSizes()
        self._parDict['unidirectional'] = self._widget.getUnidirectional()
        self._commChannel.sigScanParamsUpdated.emit(copy.deepcopy(self._parDict))
