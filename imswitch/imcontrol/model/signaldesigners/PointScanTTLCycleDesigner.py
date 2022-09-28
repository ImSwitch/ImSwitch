import numpy as np

from .basesignaldesigners import TTLCycleDesigner
from imswitch.imcommon.model import initLogger

class PointScanTTLCycleDesigner(TTLCycleDesigner):
    """ Line-based TTL cycle designer, for point-scanning applications. Treats
    input ms as lines.

    Designer params: None
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self)

        self._expectedParameters = ['target_device',
                                    'TTL_start',
                                    'TTL_end',
                                    'sequence_time']

    @property
    def timeUnits(self):
        return 'lines'

    def make_signal(self, parameterDict, setupInfo, scanInfoDict=None):
        if not self.parameterCompatibility(parameterDict):
            self._logger.error('TTL parameters seem incompatible, this error should not be since'
                               ' this should be checked at program start-up')
            return None

        if not scanInfoDict:
            return self.__make_signal_stationary(parameterDict, setupInfo.scan.sampleRate)
        else:
            signal_dict = {}

            # sample_rate = setupInfo.scan.sampleRate
            targets = parameterDict['target_device']
            # samples_pixel = parameterDict['sequence_time'] * sample_rate
            # pixels_line = scanInfoDict['pixels_line']
            n_steps_dx = scanInfoDict['img_dims']
            n_scan_samples_dx = scanInfoDict['scan_samples']
            samples_total = scanInfoDict['scan_samples_total']

            # extra ON to make sure the laser is on at the start and end of the line (due to
            # rise/fall time) (if it is ON there initially)
            onepad_extraon = 3
            zeropad_phasedelay = int(np.round(scanInfoDict['phase_delay'] * 0.1))
            zeropad_d2flyback = (scanInfoDict['scan_samples_d2_period'] -
                                   scanInfoDict['scan_samples'][1] -
                                   onepad_extraon -
                                   onepad_extraon)
            zeropad_initpos = scanInfoDict['scan_throw_initpos']
            zeropad_settling = scanInfoDict['scan_throw_settling']
            zeropad_start = scanInfoDict['scan_throw_startzero']
            zeropad_startacc = scanInfoDict['scan_throw_startacc']
            #zeropad_finalpos = scanInfoDict['scan_throw_finalpos']
            # Tile and pad TTL signals according to d=1 axis scan parameters
            for i, target in enumerate(targets):
                signal_d2_step = np.zeros(n_scan_samples_dx[1], dtype='bool')
                for (start, end) in zip(parameterDict['TTL_start'][i], parameterDict['TTL_end'][i]):
                    start = start * 1e3
                    end = end * 1e3
                    start_on = min(int(np.round(start * n_scan_samples_dx[1])), n_scan_samples_dx[1])
                    end_on = min(int(np.round(end * n_scan_samples_dx[1])), n_scan_samples_dx[1])
                    signal_d2_step[start_on:end_on] = True

                if signal_d2_step[0]:
                    #signal_line_extra = np.append(np.ones(onepad_extraon, dtype='bool'), signal_line)  # pad before
                    signal_d2_step_extra = np.append(np.ones(onepad_extraon, dtype='bool'), np.append(signal_d2_step, np.ones(onepad_extraon, dtype='bool')))  # pad before and after
                else:
                    #signal_line_extra = np.append(np.zeros(onepad_extraon, dtype='bool'), signal_line)  # pad before
                    signal_d2_step_extra = np.append(np.zeros(onepad_extraon, dtype='bool'), np.append(signal_d2_step, np.zeros(onepad_extraon, dtype='bool')))  # pad before and after
                signal_period = np.append(signal_d2_step_extra, np.zeros(zeropad_d2flyback, dtype='bool'))
                #self.__logger.debug(f'length of signal1: {len(signal_period)}')

                # all d2 steps except last
                signal = np.tile(signal_period, n_steps_dx[1] - 1)
                #self.__logger.debug(f'length of signal2: {len(signal)}')
                # add last d2 step (without flyback)
                signal = np.append(signal, signal_d2_step)
                #self.__logger.debug(f'length of signal3: {len(signal)}')

                # pad extra bits of smooth d2 curve: first step acc, start settling, and initial positioning
                signal = np.append(np.zeros(zeropad_startacc+zeropad_settling+zeropad_initpos, dtype='bool'), signal)
                #self.__logger.debug(f'length of signal5: {len(signal)}')
                # adjust to frame len 
                #self.__logger.debug(f'samples_d3_step: {samples_d3_step}, length of DO frame signal: {len(signal)}')
                zeropad_toframelen = n_scan_samples_dx[2] - len(signal)
                #self.__logger.debug(f'zeropad_toframelen: {zeropad_toframelen}')
                if zeropad_toframelen > 0:
                    signal = np.append(signal, np.zeros(zeropad_toframelen, dtype='bool'))
                elif zeropad_toframelen < 0:
                    signal = signal[-zeropad_toframelen:]  # TODO: looks strange? not right length? never enters here probably
                #self.__logger.debug(scanInfoDict)

                # repeat signal for all additional scan axes, if applicable
                axis_count_scan = len(n_steps_dx)
                for axis in range(2, axis_count_scan):
                    n_steps = n_steps_dx[axis]
                    signal = np.tile(signal, n_steps)
                
                # pad start zeros
                signal = np.append(np.zeros(zeropad_start, dtype='bool'), signal)
                # pad scanner phase delay to beginning to sync actual position with TTL
                signal = np.append(np.zeros(zeropad_phasedelay, dtype='bool'), signal)

                # adjust to same length as analog scanning
                zeropad_end = samples_total - len(signal)
                if zeropad_end > 0:
                    signal = np.append(signal, np.zeros(zeropad_end, dtype='bool'))
                elif zeropad_end < 0:
                    signal = signal[:zeropad_end]  # TODO: looks strange? not right length? never enters here probably

                signal_dict[target] = signal

            # return signal_dict, which contains bool arrays for each target
            import matplotlib.pyplot as plt
            plt.figure(1)
            for i, target in enumerate(targets):
                plt.plot(signal_dict[target]-0.01*i)
                #self.__logger.debug(np.max(signal_dict[target]))
            plt.show()

            return signal_dict

    def __make_signal_stationary(self, parameterDict, sample_rate):
        signal_dict_pixel = self.__pixel_stationary(parameterDict, sample_rate)
        return signal_dict_pixel

    def __pixel_stationary(self, parameterDict, sample_rate):
        targets = parameterDict['target_device']
        samples_cycle = parameterDict['sequence_time'] * sample_rate
        # if not samples_cycle.is_integer():
        #     self._logger.warning('Non-integer number of sequence samples, rounding up')
        samples_cycle = int(np.ceil(samples_cycle))
        # self._logger.debug(samples_cycle)
        signalDict = {}
        tmpSigArr = np.zeros(samples_cycle, dtype='bool')
        for i, target in enumerate(targets):
            tmpSigArr[:] = False
            for j, start in enumerate(parameterDict['TTL_start'][i]):
                startSamp = int(np.round(start * sample_rate))
                endSamp = int(np.round(parameterDict['TTL_end'][i][j] * sample_rate))
                tmpSigArr[startSamp:endSamp] = True
            signalDict[target] = np.copy(tmpSigArr)
        # TODO: add zero-padding and looping of this signal here, as was previously done in
        #       ScanManager?
        return signalDict


# Copyright (C) 2020-2022 ImSwitch developers
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
