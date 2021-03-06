import numpy as np

# try:
#    from .errors import InvalidChildClassError, IncompatibilityError
# except ModuleNotFoundError:
from .errors import InvalidChildClassError


class SignalDesignerFactory:
    """Factory class for creating a SignalDesigner object. Factory checks
    that the new object is compatible with the parameters that will we 
    be sent to its make_signal method."""

    def __new__(cls, setupInfo, configKeyName):
        scanDesignerName = getattr(setupInfo.designers, configKeyName)

        #        SignalDesigner = super().__new__(cls, 'SignalDesigner.'+scanDesignerName)
        signalDesigner = globals()[scanDesignerName]()
        if signalDesigner.isValidSignalDesigner():
            return signalDesigner


class SignalDesigner:
    """Parent class for any type of SignaDesigner. Any child should define
    self._expected_parameters and its own make_signal method."""

    def __init__(self):

        self.lastSignal = None
        self.lastParameterDict = None

        self._expectedParameters = None

        # Make non-overwritable functions
        self.isValidSignalDesigner = self.__isValidSignalDesigner
        self.parameterCompatibility = self.__parameterCompatibility

    @property
    def expectedParameters(self):
        if self._expectedParameters is None:
            raise ValueError('Value "%s" is not defined')
        else:
            return self._expectedParameters

    def __isValidSignalDesigner(self):
        if self._expectedParameters is None:
            raise InvalidChildClassError('Child of SignalDesigner should define \
                                 "self.expected_parameters" in __init__.')
        else:
            return True

    def make_signal(self, parameterDict, setupInfo):
        """ Method to be defined by child. Should return a dictionary with 
        {'target': signal} pairs. """
        raise NotImplementedError("Method not implemented in child")

    def __parameterCompatibility(self, parameterDict):
        """ Method to check the compatibility of parameter 'parameterDict'
        and the expected parameters of the object. """
        expected = set(self._expectedParameters)
        incoming = set([*parameterDict])

        return expected == incoming


class BetaStageScanDesigner(SignalDesigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._expectedParameters = ['Targets[x]',
                                    'Sizes[x]',
                                    'Step_sizes[x]',
                                    'Start[x]',
                                    'Sequence_time_seconds',
                                    'Sample_rate',
                                    'Return_time_seconds']

    def make_signal(self, parameterDict, setupInfo, returnFrames=False):

        if not self.parameterCompatibility(parameterDict):
            print([*parameterDict])
            print(self._expectedParameters)
            print('Stage scan parameters seem incompatible, this error should not be since this should be checked at program start-up')
            return None

        convFactors = [positioner.managerProperties['conversionFactor']
                       for positioner in setupInfo.positioners.values()]

        # Retrieve sizes
        [fast_axis_size, middle_axis_size, slow_axis_size] = \
            [(parameterDict['Sizes[x]'][i] / convFactors[i]) for i in range(3)]

        # Retrieve step sized
        [fast_axis_step_size, middle_axis_step_size, slow_axis_step_size] = \
            [(parameterDict['Step_sizes[x]'][i] / convFactors[i]) for i in range(3)]

        # Retrive starting position
        [fast_axis_start, middle_axis_start, slow_axis_start] = \
            [(parameterDict['Start[x]'][i] / convFactors[i]) for i in range(3)]

        fast_axis_positions = 1 + np.int(np.ceil(fast_axis_size / fast_axis_step_size))
        middle_axis_positions = 1 + np.int(np.ceil(middle_axis_size / middle_axis_step_size))
        slow_axis_positions = 1 + np.int(np.ceil(slow_axis_size / slow_axis_step_size))

        sequenceSamples = parameterDict['Sequence_time_seconds'] * parameterDict['Sample_rate']
        returnSamples = parameterDict['Return_time_seconds'] * parameterDict['Sample_rate']
        if not sequenceSamples.is_integer():
            print('WARNING: Non-integer number of sequence samples, rounding up')
        sequenceSamples = np.int(np.ceil(sequenceSamples))
        if not returnSamples.is_integer():
            print('WARNING: Non-integer number of return samples, rounding up')
        returnSamples = np.int(np.ceil(returnSamples))

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

        sig_dict = {parameterDict['Targets[x]'][0]: fastAxisSignal,
                    parameterDict['Targets[x]'][1]: middleAxisSignal,
                    parameterDict['Targets[x]'][2]: slowAxisSignal}

        if not returnFrames:
            return sig_dict
        else:
            return sig_dict, [fast_axis_positions, middle_axis_positions, slow_axis_positions]

    def __makeRamp(self, start, end, samples):
        return np.linspace(start, end, num=samples)

    def __smoothRamp(self, start, end, samples):
        curve_half = 0.6
        n = np.int(np.floor(curve_half * samples))
        x = np.linspace(0, np.pi / 2, num=n, endpoint=True)
        signal = start + (end - start) * np.sin(x)
        signal = np.append(signal, end * np.ones(int(np.ceil((1 - curve_half) * samples))))
        return signal


class BetaTTLCycleDesigner(SignalDesigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._expectedParameters = ['Targets[x]',
                                    'TTLStarts[x,y]',
                                    'TTLEnds[x,y]',
                                    'Sequence_time_seconds',
                                    'Sample_rate']

    def make_signal(self, parameterDict, setupInfo):

        if not self.parameterCompatibility(parameterDict):
            print('TTL parameters seem incompatible, this error should not be \
                  since this should be checked at program start-up')
            return None

        targets = parameterDict['Targets[x]']
        sampleRate = parameterDict['Sample_rate']
        cycleSamples = parameterDict['Sequence_time_seconds'] * sampleRate
        if not cycleSamples.is_integer():
            print('WARNING: Non-integer number of sequence samples, rounding up')
        cycleSamples = np.int(np.ceil(cycleSamples))
        signalDict = {}
        tmpSigArr = np.zeros(cycleSamples, dtype='bool')
        for i, target in enumerate(targets):
            tmpSigArr[:] = False
            for j, start in enumerate(parameterDict['TTLStarts[x,y]'][i]):
                startSamp = np.int(np.round(start * sampleRate))
                endSamp = np.int(np.round(parameterDict['TTLEnds[x,y]'][i][j] * sampleRate))
                tmpSigArr[startSamp:endSamp] = True

            signalDict[target] = np.copy(tmpSigArr)
        return signalDict
    
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
