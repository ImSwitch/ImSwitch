import numpy as np

from .basesignaldesigners import TTLCycleDesigner


class BetaTTLCycleDesigner(TTLCycleDesigner):
    """ TTL cycle designer for camera-based applications where each pulse
    scheme is one frame.

    Designer params: None
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._expectedParameters = ['target_device',
                                    'TTL_start',
                                    'TTL_end',
                                    'sequence_time']

    @property
    def timeUnits(self):
        return 'ms'

    def make_signal(self, parameterDict, setupInfo, scanInfoDict=None):

        if not self.parameterCompatibility(parameterDict):
            self._logger.error('TTL parameters seem incompatible, this error should not be since'
                               ' this should be checked at program start-up')
            return None

        sampleRate = setupInfo.scan.sampleRate
        targets = parameterDict['target_device']
        cycleSamples = parameterDict['sequence_time'] * sampleRate
        # self._logger.debug(f'DO sample rate: {sampleRate}, cycleSamples: {cycleSamples}')
        if not cycleSamples.is_integer():
            self._logger.warning('Non-integer number of sequence samples, rounding up')
        cycleSamples = int(np.ceil(cycleSamples))
        signalDict = {}
        tmpSigArr = np.zeros(cycleSamples, dtype='bool')
        for i, target in enumerate(targets):
            tmpSigArr[:] = False
            for j, start in enumerate(parameterDict['TTL_start'][i]):
                startSamp = int(np.round(start * sampleRate))
                endSamp = int(np.round(parameterDict['TTL_end'][i][j] * sampleRate))
                tmpSigArr[startSamp:endSamp] = True

            signalDict[target] = np.copy(tmpSigArr)

        if scanInfoDict is not None:
            positions = scanInfoDict['positions']
            returnTime = scanInfoDict['return_time']

            # Calculate samples to zero pad TTL signals with
            TTLZeroPadSamples = returnTime * sampleRate
            if not TTLZeroPadSamples.is_integer():
                self._logger.warning('Non-integer number of return samples, rounding up')
            TTLZeroPadSamples = int(np.ceil(TTLZeroPadSamples))

            # Tile and pad TTL signals according to sync parameters
            for target, signal in signalDict.items():
                signal = np.tile(signal, positions[0])
                signal = np.append(signal, np.zeros(TTLZeroPadSamples, dtype='bool'))
                signal = np.tile(signal, positions[1] * positions[2])

                signalDict[target] = signal

        return signalDict


# Copyright (C) 2020-2021 ImSwitch developers
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
