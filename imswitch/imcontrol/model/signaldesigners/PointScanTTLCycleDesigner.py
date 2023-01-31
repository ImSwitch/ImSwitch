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

        self._expectedParameters = ['target_device',
                                    'TTL_sequence',
                                    'TTL_sequence_axis']

    @property
    def timeUnits(self):
        pass

    def make_signal(self, parameterDict, setupInfo, scanInfoDict=None):
        """ Create TTL signals, based on parameter dictionary and scan info dictionary. """
        if not self.parameterCompatibility(parameterDict):
            self._logger.error('TTL parameters seem incompatible, this error should not be since'
                               ' this should be checked at program start-up')
            return None

        if not scanInfoDict:
            return self.__make_signal_stationary(parameterDict, setupInfo.scan.sampleRate)
        else:
            signal_dict = {}
            frame_line_clocks = {}

            targets = parameterDict['target_device']
            n_steps_dx = scanInfoDict['img_dims']
            axis_count = len(n_steps_dx)
            n_scan_samples_dx = scanInfoDict['scan_samples']
            samples_total = scanInfoDict['scan_samples_total']
            scan_axes_order = scanInfoDict['axis_names']
            # extra ON at the end of d2 step, to not turn off before line is finished
            onepad_extraon = 10 #int(np.round(scanInfoDict['extra_laser_on']))

            clock_len = 10  # length of line/frame clock pulses at the start of line/frame, in samples
  
            #zeropad_phasedelay = int(np.round(scanInfoDict['phase_delay']))
            zeropad_d2flyback = np.max([0,(scanInfoDict['scan_samples_d2_period'] -
                                   n_scan_samples_dx[1] -
                                   onepad_extraon)])
            zeropad_initpos = scanInfoDict['scan_throw_initpos']
            zeropad_settling = scanInfoDict['scan_throw_settling']
            zeropad_start = scanInfoDict['scan_throw_startzero']
            zeropad_startacc = scanInfoDict['scan_throw_startacc']
            self.zeropad_extrapad = scanInfoDict['padlens']
            # Tile and pad TTL signals according to d=1 axis scan parameters
            for i, target in enumerate(targets):
                # get sequence
                seq_axis_name = parameterDict['TTL_sequence_axis'][i]
                if seq_axis_name == 'None':
                    seq_axis = seq_axis_name
                else:
                    try:
                        seq_axis = scan_axes_order.index(seq_axis_name)
                    except:
                        seq_axis = 'None'
                seq_txt = parameterDict['TTL_sequence'][i]
                seq = self.__decode_sequence(seq_txt)
                if seq_axis == 'None':
                    # no ttl sequences along axes
                    # repeat start of sequence to d1 axis length
                    signal_d2_step = np.ones(n_scan_samples_dx[1] + onepad_extraon, dtype='bool') if seq[0] else np.zeros(n_scan_samples_dx[1] + onepad_extraon, dtype='bool')
                    signal_d2_period = np.append(signal_d2_step, np.zeros(zeropad_d2flyback, dtype='bool'))
                    # all d2 steps except last
                    signal_d2 = np.tile(signal_d2_period, n_steps_dx[1] - 1)
                    # add last d2 step (without flyback)
                    signal_d2 = np.append(signal_d2, signal_d2_step)
                    # pad extra bits of smooth d2 curve: first step acc, start settling, and initial positioning
                    signal_d2 = np.append(np.zeros(zeropad_startacc+zeropad_settling+zeropad_initpos, dtype='bool'), signal_d2)
                    # adjust to frame len 
                    zeropad_toframelen = n_scan_samples_dx[2] - len(signal_d2)
                    if zeropad_toframelen > 0:
                        signal_d2 = np.append(signal_d2, np.zeros(zeropad_toframelen, dtype='bool'))
                    elif zeropad_toframelen < 0:
                        signal_d2 = signal_d2[-zeropad_toframelen:]  # TODO: looks strange? not right length? never enters here probably
                    # repeat signal for all additional scan axes, if applicable
                    signal = self.__repeat_remaining_axes(signal=signal_d2, n_steps_dx=n_steps_dx, axis_start=2, axis_end=axis_count)
                elif seq_axis == 0:
                    # ttl sequence along first (pixel) axis
                    # repeat sequence to d1 axis length
                    signal_d2_step = np.resize(seq, n_steps_dx[0])
                    if n_scan_samples_dx[1] > n_steps_dx[0]:
                        signal_d2_step = np.repeat(signal_d2_step, (n_scan_samples_dx[1])/n_steps_dx[0]).astype(bool)
                    elif n_scan_samples_dx[1] < n_steps_dx[0]:
                        signal_d2_step = signal_d2_step[::int(n_steps_dx[0]/n_scan_samples_dx[1])].astype(bool)
                    append_start = np.ones(onepad_extraon, dtype='bool') if signal_d2_step[0] == 1 else np.zeros(onepad_extraon, dtype='bool')
                    signal_d2_step = np.append(append_start, signal_d2_step)
                    signal_d2_period = np.append(signal_d2_step, np.zeros(zeropad_d2flyback, dtype='bool'))
                    # all d2 steps except last
                    signal_d2 = np.tile(signal_d2_period, n_steps_dx[1] - 1)
                    # add last d2 step (without flyback)
                    signal_d2 = np.append(signal_d2, signal_d2_step)
                    # pad extra bits of smooth d2 curve: first step acc, start settling, and initial positioning
                    signal_d2 = np.append(np.zeros(zeropad_startacc+zeropad_settling+zeropad_initpos, dtype='bool'), signal_d2)
                    # adjust to d3 step len 
                    zeropad_toframelen = n_scan_samples_dx[2] - len(signal_d2)
                    if zeropad_toframelen > 0:
                        signal_d2 = np.append(signal_d2, np.zeros(zeropad_toframelen, dtype='bool'))
                    elif zeropad_toframelen < 0:
                        signal_d2 = signal_d2[-zeropad_toframelen:]
                    # repeat signal for all additional scan axes, if applicable
                    signal = self.__repeat_remaining_axes(signal=signal_d2, n_steps_dx=n_steps_dx, axis_start=2, axis_end=axis_count)
                elif seq_axis == 1:
                    # ttl sequence along second (line) axis
                    # repeat sequence to d2 axis length
                    seq = np.resize(seq, n_steps_dx[1])
                    # create ON and OFF d2 periods and steps to use when building d2 sequence
                    on_d2_period, on_d2_step = self.__create_d2_period(state=1, n_samples_d1=n_scan_samples_dx[1], samples_extra=onepad_extraon, samples_flyback=zeropad_d2flyback)
                    off_d2_period, off_d2_step = self.__create_d2_period(state=0, n_samples_d1=n_scan_samples_dx[1], samples_extra=onepad_extraon, samples_flyback=zeropad_d2flyback)
                    # build frame from seq
                    signal_d3 = np.array([])
                    for step in seq[:-1]:
                        signal_d3 = np.append(signal_d3, on_d2_period) if step else np.append(signal_d3, off_d2_period)
                    # add last d2 step (without flyback)
                    signal_d3 = np.append(signal_d3, on_d2_step) if seq[-1] else np.append(signal_d3, off_d2_step)
                    # pad extra bits of smooth d2 curve: first step acc, start settling, and initial positioning
                    signal_d3 = np.append(np.zeros(zeropad_startacc+zeropad_settling+zeropad_initpos, dtype='bool'), signal_d3)
                    # adjust to d3 step len 
                    zeropad_toframelen = n_scan_samples_dx[2] - len(signal_d3)
                    if zeropad_toframelen > 0:
                        signal_d3 = np.append(signal_d3, np.zeros(zeropad_toframelen, dtype='bool'))
                    elif zeropad_toframelen < 0:
                        signal_d3 = signal_d3[-zeropad_toframelen:]
                    # repeat signal for all additional scan axes, if applicable
                    signal = self.__repeat_remaining_axes(signal=signal_d3, n_steps_dx=n_steps_dx, axis_start=2, axis_end=axis_count)
                elif seq_axis == 2:
                    # ttl sequence along third (frame) axis
                    # repeat sequence to d3 axis length
                    seq = np.resize(seq, n_steps_dx[2])
                    # create ON and OFF d2 periods and steps
                    on_d2_period, on_d2_step = self.__create_d2_period(state=1, n_samples_d1=n_scan_samples_dx[1], samples_extra=onepad_extraon, samples_flyback=zeropad_d2flyback)
                    off_d2_period, off_d2_step = self.__create_d2_period(state=0, n_samples_d1=n_scan_samples_dx[1], samples_extra=onepad_extraon, samples_flyback=zeropad_d2flyback)
                    # create ON and OFF d3 steps, to use when building d3 sequence
                    on_d3_step = self.__create_d3_step(d2_period=on_d2_period, d2_step=on_d2_step, n_steps_d2=n_steps_dx[1], n_samples_d3=n_scan_samples_dx[2], samples_zeropad_step=zeropad_startacc+zeropad_settling+zeropad_initpos)
                    off_d3_step = self.__create_d3_step(d2_period=off_d2_period, d2_step=off_d2_step, n_steps_d2=n_steps_dx[1], n_samples_d3=n_scan_samples_dx[2], samples_zeropad_step=zeropad_startacc+zeropad_settling+zeropad_initpos)
                    # build d4 step from seq
                    signal_d4 = np.array([])
                    for step in seq:
                        signal_d4 = np.append(signal_d4, on_d3_step) if step else np.append(signal_d4, off_d3_step)
                    # adjust to d4 step len 
                    zeropad_toframelen = n_scan_samples_dx[3] - len(signal_d4)
                    if zeropad_toframelen > 0:
                        signal_d4 = np.append(signal_d4, np.zeros(zeropad_toframelen, dtype='bool'))
                    elif zeropad_toframelen < 0:
                        signal_d4 = signal_d4[-zeropad_toframelen:]
                    # repeat signal for all additional scan axes, if applicable
                    signal = self.__repeat_remaining_axes(signal=signal_d4, n_steps_dx=n_steps_dx, axis_start=3, axis_end=axis_count)
                elif seq_axis == 3:
                    # ttl sequence along fourth (timelapse) axis
                    # repeat sequence to d4 axis length
                    seq = np.resize(seq, n_steps_dx[3])
                    # create ON and OFF d2 periods and steps
                    on_d2_period, on_d2_step = self.__create_d2_period(state=1, n_samples_d1=n_scan_samples_dx[1], samples_extra=onepad_extraon, samples_flyback=zeropad_d2flyback)
                    off_d2_period, off_d2_step = self.__create_d2_period(state=0, n_samples_d1=n_scan_samples_dx[1], samples_extra=onepad_extraon, samples_flyback=zeropad_d2flyback)
                    # create ON and OFF d3 steps
                    on_d3_step = self.__create_d3_step(d2_period=on_d2_period, d2_step=on_d2_step, n_steps_d2=n_steps_dx[1], n_samples_d3=n_scan_samples_dx[2], samples_zeropad_step=zeropad_startacc+zeropad_settling+zeropad_initpos)
                    off_d3_step = self.__create_d3_step(d2_period=off_d2_period, d2_step=off_d2_step, n_steps_d2=n_steps_dx[1], n_samples_d3=n_scan_samples_dx[2], samples_zeropad_step=zeropad_startacc+zeropad_settling+zeropad_initpos)
                    # create ON and OFF d4 steps, to use when building d4 sequence
                    on_d4_step = self.__create_d4_step(d3_step=on_d3_step, n_steps_d3=n_steps_dx[2])
                    off_d4_step = self.__create_d4_step(d3_step=off_d3_step, n_steps_d3=n_steps_dx[2])
                    # build d5 step from seq
                    signal_d5 = np.array([])
                    for step in seq:
                        signal_d5 = np.append(signal_d5, on_d4_step) if step else np.append(signal_d5, off_d4_step)
                    # adjust to d5 step len 
                    zeropad_toframelen = n_scan_samples_dx[4] - len(signal_d5)
                    if zeropad_toframelen > 0:
                        signal_d5 = np.append(signal_d5, np.zeros(zeropad_toframelen, dtype='bool'))
                    elif zeropad_toframelen < 0:
                        signal_d5 = signal_d5[-zeropad_toframelen:]
                    # repeat signal for all additional scan axes, if applicable
                    signal = self.__repeat_remaining_axes(signal=signal_d5, n_steps_dx=n_steps_dx, axis_start=4, axis_end=axis_count)
                
                # pad start zeros
                signal = np.append(np.zeros(zeropad_start, dtype='bool'), signal)
                # pad scanner phase delay to beginning to sync actual position with TTL
                #signal = np.append(np.zeros(zeropad_phasedelay, dtype='bool'), signal)

                # adjust to same length as analog scanning
                zeropad_end = samples_total - len(signal)
                if zeropad_end > 0:
                    signal = np.append(signal, np.zeros(zeropad_end, dtype='bool'))
                elif zeropad_end < 0:
                    signal = signal[:zeropad_end]  # TODO: looks strange? not right length? never enters here probably

                signal_dict[target] = signal.astype(bool)

            # Generate frame and line clocks
            # line clock
            line_clock = self.__generate_frame_line_clock(n_scan_samples_dx, n_steps_dx, samples_total, axis_count, zeropad_startacc, zeropad_settling, zeropad_initpos, zeropad_start, zeropad_d2flyback, onepad_extraon, frame=False, line=True)
            signal_dict['line_clock'] = line_clock.astype(bool)
            # frame clock
            frame_clock = self.__generate_frame_line_clock(n_scan_samples_dx, n_steps_dx, samples_total, axis_count, zeropad_startacc, zeropad_settling, zeropad_initpos, zeropad_start, zeropad_d2flyback, onepad_extraon, frame=True, line=False)
            signal_dict['frame_clock'] = frame_clock.astype(bool)

            self.__plot_curves(plot=False, signals=signal_dict, targets=targets+['frame_clock','line_clock'])  # for debugging

            # return signal_dict, which contains bool arrays for each target
            return signal_dict

    def __generate_frame_line_clock(self, n_scan_samples_dx, n_steps_dx, samples_total, axis_count, zeropad_startacc, zeropad_settling, zeropad_initpos, zeropad_start, zeropad_d2flyback, onepad_extraon, frame=True, line=False, clock_len=10):
        """ Generate frame and line clock signals, to be returned in signal_dict and used if user wants frame/line clock at a digital output. """
        # zeros to d1 axis length
        signal_d2_step = np.zeros(n_scan_samples_dx[1] + onepad_extraon, dtype='bool')
        if line:
            # replace first part with a line clock pulse
            signal_d2_step[:clock_len] = 1
        signal_d2_period = np.append(signal_d2_step, np.zeros(zeropad_d2flyback, dtype='bool'))
        # all d2 steps except last
        signal_d2 = np.tile(signal_d2_period, n_steps_dx[1] - 1)
        # add last d2 step (without flyback)
        signal_d2 = np.append(signal_d2, signal_d2_step)
        if frame:
            # replace first part with a frame clock pulse
            signal_d2[:clock_len] = 1
        # pad extra bits of smooth d2 curve: first step acc, start settling, and initial positioning
        signal_d2 = np.append(np.zeros(zeropad_startacc+zeropad_settling+zeropad_initpos, dtype='bool'), signal_d2)
        # adjust to frame len 
        zeropad_toframelen = n_scan_samples_dx[2] - len(signal_d2)
        if zeropad_toframelen > 0:
            signal_d2 = np.append(signal_d2, np.zeros(zeropad_toframelen, dtype='bool'))
        elif zeropad_toframelen < 0:
            signal_d2 = signal_d2[-zeropad_toframelen:]  # TODO: looks strange? not right length? never enters here probably
        # repeat signal for all additional scan axes, if applicable
        signal = self.__repeat_remaining_axes(signal=signal_d2, n_steps_dx=n_steps_dx, axis_start=2, axis_end=axis_count)
        # pad start zeros
        signal = np.append(np.zeros(zeropad_start, dtype='bool'), signal)
        # adjust to same length as analog scanning
        zeropad_end = samples_total - len(signal)
        if zeropad_end > 0:
            signal = np.append(signal, np.zeros(zeropad_end, dtype='bool'))
        elif zeropad_end < 0:
            signal = signal[:zeropad_end]  # TODO: looks strange? not right length? never enters here probably
        return signal

    def __create_d2_period(self, state, n_samples_d1, samples_extra, samples_flyback):
        """ Create a full d2 step period of boolean state (on or off during d2 step, without flyback). """
        d2_step = np.ones(n_samples_d1 + samples_extra, dtype='bool') if state else np.zeros(n_samples_d1 + samples_extra, dtype='bool')
        return np.append(d2_step, np.zeros(samples_flyback, dtype='bool')), d2_step
    
    def __create_d3_step(self, d2_period, d2_step, n_steps_d2, n_samples_d3, samples_zeropad_step):
        """ Create a full d3 step signal. """
        d3_step = np.tile(d2_period, n_steps_d2 - 1)
        d3_step = np.append(d3_step, d2_step)
        d3_step = np.append(np.zeros(samples_zeropad_step, dtype='bool'), d3_step)
        zeropad_toframelen = n_samples_d3 - len(d3_step)
        if zeropad_toframelen > 0:
            d3_step = np.append(d3_step, np.zeros(zeropad_toframelen, dtype='bool'))
        elif zeropad_toframelen < 0:
            d3_step = d3_step[-zeropad_toframelen:]
        return d3_step

    def __create_d4_step(self, d3_step, n_steps_d3):
        """ Create a full d4 step signal. """
        return np.tile(d3_step, n_steps_d3)

    def __repeat_remaining_axes(self, signal, n_steps_dx, axis_start, axis_end):
        """ Repeat a created signal for the remaining axes, from axis_start to axis_end. """
        for axis in range(axis_start, axis_end):
            signal = np.append(signal, np.zeros(self.zeropad_extrapad[axis]))
            signal = np.tile(signal, n_steps_dx[axis])
        return signal

    def __make_signal_stationary(self, parameterDict, sample_rate):
        """ Make a signal for displaying in the signal graph, without scan parameters. """
        targets = parameterDict['target_device']
        seqs = parameterDict['TTL_sequence']
        signalDict = {}
        for i, target in enumerate(targets):
            seq = self.__decode_sequence(seqs[i])
            signalDict[target] = np.copy(seq)
        return signalDict

    def __decode_sequence(self, sequence_txt):
        """ Decode user-inputted string of TTL sequence into boolean list. 
        Input string should consist of comma-separated commands on the form
        "h#" or "l#", where h means high=on, l means low=off, and # is the
        number of axis steps. Example:
        "h1,l2,h3,l1"
        means on for 1 step, off for 2 steps, on for 3 steps, and off for 1 step.
        This will be repeated until reaching the axis length over the axis the 
        sequence is valid for."""
        seq_list = []  # list of inputted sequence - minimal length
        seq = sequence_txt.split(',')
        for step in seq:
            state = 0
            length = 0
            if step[0] == 'h':
                state = 1
            elif step[0] == 'l':
                state = 0
            length = int(step[1:])
            seq_list.append(np.repeat(state,length))
            if len(seq_list) > 1000:
                break
        return np.concatenate(seq_list)

    def __plot_curves(self, plot, signals, targets):
        """ Plot all TTL curves, for debugging. """
        if plot:
            import matplotlib.pyplot as plt
            plt.figure(1)
            for i, target in enumerate(targets):
                plt.plot(signals[target] - 0.01 * i)
                #self._logger.debug(f'Signal length {target}: {len(signals[target])}')
            plt.show()


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
