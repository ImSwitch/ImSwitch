import numpy as np

from .basesignaldesigners import ScanDesigner
from imswitch.imcommon.model import initLogger

class BetaScanDesigner(ScanDesigner):
    """ Scan designer for X/Y/Z stages that move a sample.
    Designer params:
    - ``return_time`` -- time to wait between lines for the stage to return to
      the first position of the next line, in seconds.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)
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
            self._logger.error([*parameterDict])
            self._logger.error(self._expectedParameters)
            self._logger.error('Stage scan parameters seem incompatible, this error should not be'
                               ' since this should be checked at program start-up')
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

        # Retrieve step sizes
        [fast_axis_step_size, middle_axis_step_size, slow_axis_step_size] = \
            [(parameterDict['axis_step_size'][i] / convFactors[i]) for i in range(3)]

        # Retrive starting position
        [fast_axis_start, middle_axis_start, slow_axis_start] = \
            [(parameterDict['axis_startpos'][i][0] / convFactors[i]) for i in range(3)]

        fast_axis_positions = 1 if fast_axis_size == 0 or fast_axis_step_size == 0 else \
            1 + int(np.ceil(fast_axis_size / fast_axis_step_size))
        middle_axis_positions = 1 if middle_axis_size == 0 or middle_axis_step_size == 0 else \
            1 + int(np.ceil(middle_axis_size / middle_axis_step_size))
        slow_axis_positions = 1 if slow_axis_size == 0 or slow_axis_step_size == 0 else \
            1 + int(np.ceil(slow_axis_size / slow_axis_step_size))

        sampleRate = setupInfo.scan.sampleRate
        sequenceSamples = parameterDict['sequence_time'] * sampleRate
        returnSamples = parameterDict['return_time'] * sampleRate
        if not sequenceSamples.is_integer():
            self._logger.warning('Non-integer number of sequence samples, rounding up')
        sequenceSamples = int(np.ceil(sequenceSamples))
        if not returnSamples.is_integer():
            self._logger.warning('Non-integer number of return samples, rounding up')
        returnSamples = int(np.ceil(returnSamples))

        # Make fast axis signal
        rampSamples = fast_axis_positions * sequenceSamples
        lineSamples = rampSamples + returnSamples
        rampSignal = np.zeros(rampSamples)
        self._logger.debug(fast_axis_positions)
        rampValues = self.__makeRamp(fast_axis_start, fast_axis_size, fast_axis_positions)
        for s in range(fast_axis_positions):
            start = s * sequenceSamples
            end = s * sequenceSamples + sequenceSamples
            smooth = int(np.ceil(0.001 * sampleRate))
            settling = int(np.ceil(0.001 * sampleRate))
            rampSignal[start: end] = rampValues[s]
            if s is not fast_axis_positions - 1:
                if (end - smooth - settling) > 0:
                    rampSignal[end - smooth - settling: end - settling] = self.__smoothRamp(rampValues[s], rampValues[s + 1], smooth)
                    rampSignal[end - settling:end] = rampValues[s + 1]

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

        self.__plot_curves(plot=False, signals=[fastAxisSignal, middleAxisSignal, slowAxisSignal])

        return sig_dict, scanInfoDict['positions'], scanInfoDict

    def __makeRamp(self, start, end, samples):
        return np.linspace(float(start), float(end), num=samples)

    def __smoothRamp(self, start, end, samples):
        start = float(start)
        end = float(end)
        curve_half = 0.6
        n = int(np.floor(curve_half * samples))
        x = np.linspace(0, np.pi / 2, num=n, endpoint=True)
        signal = start + (end - start) * np.sin(x)
        signal = np.append(signal, end * np.ones(int(np.ceil((1 - curve_half) * samples))))
        return signal

    def __plot_curves(self, plot, signals):
        """ Plot all scan curves, for debugging. """
        if plot:
            import matplotlib.pyplot as plt
            plt.figure(1)
            plt.clf()
            for i, signal in enumerate(signals):
                plt.plot(signal - 0.01 * i)
            plt.show()

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