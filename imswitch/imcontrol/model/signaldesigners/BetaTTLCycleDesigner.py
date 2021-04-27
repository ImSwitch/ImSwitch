import numpy as np

from .basesignaldesigners import TTLCycleDesigner


class BetaTTLCycleDesigner(TTLCycleDesigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._expectedParameters = ['target_device',
                                    'TTL_start',
                                    'TTL_end',
                                    'sequence_time',
                                    'sample_rate']

    @property
    def timeUnits(self):
        return 'ms'

    def make_signal(self, parameterDict, setupInfo, scanInfoDict=None):

        if not self.parameterCompatibility(parameterDict):
            print('TTL parameters seem incompatible, this error should not be \
                  since this should be checked at program start-up')
            return None

        targets = parameterDict['target_device']
        sampleRate = parameterDict['sample_rate']
        cycleSamples = parameterDict['sequence_time'] * sampleRate
        #print(f'DO sample rate: {sampleRate}, cycleSamples: {cycleSamples}')
        if not cycleSamples.is_integer():
            print('WARNING: Non-integer number of sequence samples, rounding up')
        cycleSamples = np.int(np.ceil(cycleSamples))
        signalDict = {}
        tmpSigArr = np.zeros(cycleSamples, dtype='bool')
        for i, target in enumerate(targets):
            tmpSigArr[:] = False
            for j, start in enumerate(parameterDict['TTL_start'][i]):
                startSamp = np.int(np.round(start * sampleRate))
                endSamp = np.int(np.round(parameterDict['TTL_end'][i][j] * sampleRate))
                tmpSigArr[startSamp:endSamp] = True

            signalDict[target] = np.copy(tmpSigArr)

        if scanInfoDict is not None:
            positions = scanInfoDict['positions']
            returnTime = scanInfoDict['return_time']

            # Calculate samples to zero pad TTL signals with
            TTLZeroPadSamples = returnTime * sampleRate
            if not TTLZeroPadSamples.is_integer():
                print('WARNING: Non-integer number of return samples, rounding up')
            TTLZeroPadSamples = np.int(np.ceil(TTLZeroPadSamples))

            # Tile and pad TTL signals according to sync parameters
            for target, signal in signalDict.items():
                signal = np.tile(signal, positions[0])
                signal = np.append(signal, np.zeros(TTLZeroPadSamples, dtype='bool'))
                signal = np.tile(signal, positions[1] * positions[2])

                signalDict[target] = signal

        return signalDict


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
