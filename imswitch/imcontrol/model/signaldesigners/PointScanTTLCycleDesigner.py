import numpy as np

from .basesignaldesigners import TTLCycleDesigner


class PointScanTTLCycleDesigner(TTLCycleDesigner):
    """ Line-based TTL cycle designer, for point-scanning applications. Treats
    input ms as lines.

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
        return 'lines'

    def make_signal(self, parameterDict, setupInfo, scanInfoDict=None):
        if not self.parameterCompatibility(parameterDict):
            print('TTL parameters seem incompatible, this error should not be \
                  since this should be checked at program start-up')
            return None

        if not scanInfoDict:
            return self.__make_signal_stationary(parameterDict, setupInfo.scan.sampleRate)
        else:
            signal_dict = {}

            # sample_rate = setupInfo.scan.sampleRate
            targets = parameterDict['target_device']
            # samples_pixel = parameterDict['sequence_time'] * sample_rate
            # pixels_line = scanInfoDict['pixels_line']
            samples_line = scanInfoDict['scan_samples_line']
            samples_total = scanInfoDict['scan_samples_total']

            # extra ON to make sure the laser is on at the start and end of the line (due to
            # rise/fall time) (if it is ON there initially)
            onepad_extraon = 2
            zeropad_syncdelay = 0  # extra delay to sync with actual galvo positions
            zeropad_lineflyback = (scanInfoDict['scan_samples_period'] -
                                   scanInfoDict['scan_samples_line'] -
                                   onepad_extraon)
            zeropad_initpos = scanInfoDict['scan_throw_initpos']
            zeropad_settling = scanInfoDict['scan_throw_settling']
            zeropad_start = scanInfoDict['scan_throw_startzero']
            zeropad_startacc = scanInfoDict['scan_throw_startacc']
            # zeropad_finalpos = scanInfoDict['scan_throw_finalpos']
            # Tile and pad TTL signals according to fast axis scan parameters
            for i, target in enumerate(targets):
                signal_line = np.zeros(samples_line, dtype='bool')
                for j, (start, end) in enumerate(zip(parameterDict['TTL_start'][i],
                                                     parameterDict['TTL_end'][i])):
                    start = start * 1e3
                    end = end * 1e3
                    start_on = min(np.int(np.round(start * samples_line)), samples_line)
                    end_on = min(np.int(np.round(end * samples_line)), samples_line)
                    signal_line[start_on:end_on] = True

                if signal_line[0]:
                    signal_line = np.append(np.ones(onepad_extraon, dtype='bool'), signal_line)
                else:
                    signal_line = np.append(np.zeros(onepad_extraon, dtype='bool'), signal_line)
                signal_period = np.append(signal_line, np.zeros(zeropad_lineflyback, dtype='bool'))
                # TODO: # only do 2D-scan for now, fix for 3D-scan

                # all lines except last
                signal = np.tile(signal_period, scanInfoDict['n_lines'] - 1)
                # add last line (does without flyback)
                signal = np.append(signal, signal_line)

                # pad a delay for synchronizing scan position with TTL
                signal = np.append(np.zeros(zeropad_syncdelay, dtype='bool'), signal)
                # pad first line acceleration
                signal = np.append(np.zeros(zeropad_startacc, dtype='bool'), signal)
                # pad start settling
                signal = np.append(np.zeros(zeropad_settling, dtype='bool'), signal)
                signal = np.append(np.zeros(zeropad_initpos, dtype='bool'), signal)  # pad initpos
                signal = np.append(np.zeros(zeropad_start, dtype='bool'), signal)  # pad start zeros
                zeropad_end = samples_total - len(signal)
                # pad end zeros to same length as analog scanning
                signal = np.append(signal, np.zeros(zeropad_end, dtype='bool'))

                signal_dict[target] = signal

            # return signal_dict, which contains bool arrays for each target
            return signal_dict

    def __make_signal_stationary(self, parameterDict, sample_rate):
        signal_dict_pixel = self.__pixel_stationary(parameterDict, sample_rate)
        return signal_dict_pixel

    def __pixel_stationary(self, parameterDict, sample_rate):
        targets = parameterDict['target_device']
        samples_cycle = parameterDict['sequence_time'] * sample_rate
        # if not samples_cycle.is_integer():
        #     print('WARNING: Non-integer number of sequence samples, rounding up')
        samples_cycle = np.int(np.ceil(samples_cycle))
        # print(samples_cycle)
        signalDict = {}
        tmpSigArr = np.zeros(samples_cycle, dtype='bool')
        for i, target in enumerate(targets):
            tmpSigArr[:] = False
            for j, start in enumerate(parameterDict['TTL_start'][i]):
                startSamp = np.int(np.round(start * sample_rate))
                endSamp = np.int(np.round(parameterDict['TTL_end'][i][j] * sample_rate))
                tmpSigArr[startSamp:endSamp] = True
            signalDict[target] = np.copy(tmpSigArr)
        # TODO: add zero-padding and looping of this signal here, as was previously done in
        #       ScanManager?
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
