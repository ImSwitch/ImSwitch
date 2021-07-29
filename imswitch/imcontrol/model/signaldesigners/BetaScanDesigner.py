import numpy as np

from .basesignaldesigners import ScanDesigner


class BetaScanDesigner(ScanDesigner):
    """ Scan designer for X/Y/Z stages that move a sample.

    Designer params:

    - ``return_time`` -- time to wait between lines for the stage to return to
      the first position of the next line, in seconds.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._expectedParameters = ['target_device',
                                    'axis_length',
                                    'axis_step_size',
                                    'axis_startpos',
                                    'return_time']

    def checkSignalComp(self, scanParameters, setupInfo, scanInfo):
        """ Check analog scanning signals so that they are inside the range of
        the acceptable scanner voltages."""
        return True  # TODO

    def make_signal(self, parameterDict, setupInfo):

        if not self.parameterCompatibility(parameterDict):
            print([*parameterDict])
            print(self._expectedParameters)
            print('Stage scan parameters seem incompatible,'
                  ' this error should not be since this should be checked at program start-up')
            return None

        if len(parameterDict['target_device']) != 3:
            raise ValueError(f'{self.__class__.__name__} requires 3 target devices/axes')

        for i in range(3):
            if len(parameterDict['axis_startpos'][i]) > 1:
                raise ValueError(f'{self.__class__.__name__} does not support multi-axis'
                                 f' positioners')

        convFactors = [positioner.managerProperties['conversionFactor']
                       for positioner in setupInfo.positioners.values() if positioner.forScanning]

        # Retrieve sizes
        [fast_axis_size, middle_axis_size, slow_axis_size] = \
            [(parameterDict['axis_length'][i] / convFactors[i]) for i in range(3)]

        # Retrieve step sized
        [fast_axis_step_size, middle_axis_step_size, slow_axis_step_size] = \
            [(parameterDict['axis_step_size'][i] / convFactors[i]) for i in range(3)]

        # Retrive starting position
        [fast_axis_start, middle_axis_start, slow_axis_start] = \
            [(parameterDict['axis_startpos'][i][0] / convFactors[i]) for i in range(3)]

        fast_axis_positions = 1 + int(np.ceil(fast_axis_size / fast_axis_step_size))
        middle_axis_positions = 1 + int(np.ceil(middle_axis_size / middle_axis_step_size))
        slow_axis_positions = 1 + int(np.ceil(slow_axis_size / slow_axis_step_size))

        sampleRate = setupInfo.scan.sampleRate
        sequenceSamples = parameterDict['sequence_time'] * sampleRate
        print(sequenceSamples)
        returnSamples = parameterDict['return_time'] * sampleRate
        if not sequenceSamples.is_integer():
            print('WARNING: Non-integer number of sequence samples, rounding up')
        sequenceSamples = int(np.ceil(sequenceSamples))
        if not returnSamples.is_integer():
            print('WARNING: Non-integer number of return samples, rounding up')
        returnSamples = int(np.ceil(returnSamples))

        # Make fast axis signal
        rampSamples = fast_axis_positions * sequenceSamples
        lineSamples = rampSamples + returnSamples

        rampSignal = self.__makeRamp(fast_axis_start, fast_axis_size, rampSamples)
        returnRamp = self.__smoothRamp(fast_axis_size, fast_axis_start, returnSamples)
        fullLineSignal = np.concatenate((rampSignal, returnRamp))

        fastAxisSignal = np.tile(fullLineSignal, middle_axis_positions * slow_axis_positions)
        # Make middle axis signal
        colSamples = middle_axis_positions * lineSamples
        colValues = self.__makeRamp(middle_axis_start, middle_axis_size, middle_axis_positions)
        fullSquareSignal = np.zeros(colSamples)
        for s in range(middle_axis_positions):
            fullSquareSignal[s * lineSamples: s * lineSamples + rampSamples] = colValues[s]

            try:
                fullSquareSignal[s * lineSamples + rampSamples:(s + 1) * lineSamples] = \
                    self.__smoothRamp(colValues[s], colValues[s + 1], returnSamples)
            except IndexError:
                fullSquareSignal[s * lineSamples + rampSamples:(s + 1) * lineSamples] = \
                    self.__smoothRamp(colValues[s], middle_axis_start, returnSamples)

        middleAxisSignal = np.tile(fullSquareSignal, slow_axis_positions)

        # Make slow axis signal
        sliceSamples = slow_axis_positions * colSamples
        sliceValues = self.__makeRamp(slow_axis_start, slow_axis_size, slow_axis_positions)
        fullCubeSignal = np.zeros(sliceSamples)
        for s in range(slow_axis_positions):
            fullCubeSignal[s * colSamples:(s + 1) * colSamples - returnSamples] = sliceValues[s]

            try:
                fullCubeSignal[(s + 1) * colSamples - returnSamples:(s + 1) * colSamples] = \
                    self.__smoothRamp(sliceValues[s], sliceValues[s + 1], returnSamples)
            except IndexError:
                fullCubeSignal[(s + 1) * colSamples - returnSamples:(s + 1) * colSamples] = \
                    self.__smoothRamp(sliceValues[s], slow_axis_start, returnSamples)
        slowAxisSignal = fullCubeSignal

        sig_dict = {parameterDict['target_device'][0]: fastAxisSignal,
                    parameterDict['target_device'][1]: middleAxisSignal,
                    parameterDict['target_device'][2]: slowAxisSignal}

        # scanInfoDict, for parameters that are important to relay to TTLCycleDesigner and/or image
        # acquisition managers
        scanInfoDict = {
            'positions': [fast_axis_positions, middle_axis_positions, slow_axis_positions],
            'return_time': parameterDict['return_time']
        }
        return sig_dict, scanInfoDict['positions'], scanInfoDict

    def __makeRamp(self, start, end, samples):
        return np.linspace(start, end, num=samples)

    def __smoothRamp(self, start, end, samples):
        curve_half = 0.6
        n = int(np.floor(curve_half * samples))
        x = np.linspace(0, np.pi / 2, num=n, endpoint=True)
        signal = start + (end - start) * np.sin(x)
        signal = np.append(signal, end * np.ones(int(np.ceil((1 - curve_half) * samples))))
        return signal


# Copyright (C) 2020, 2021 TestaLab
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
