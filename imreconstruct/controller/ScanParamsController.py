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

# Copyright (C) 2020, 2021 Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
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