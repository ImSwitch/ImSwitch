import numpy as np

from .basesignaldesigners import ScanDesigner, ScanInfoContract
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
                                    'axis_centerpos',
                                    'return_time']

    def checkSignalComp(self, scanParameters, setupInfo, scanInfo):
        """ Check analog scanning signals so that they are inside the range of
        the acceptable scanner voltages."""
        return True  # TODO

    def make_signal(self, parameterDict, setupInfo):
        n_linesteps = int(parameterDict.get("n_linesteps", 1))
        n_linesteps = max(1, n_linesteps)
        positioner_line_program = self.__normalize_positioner_line_program(
            parameterDict, n_linesteps
        )

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

        # Retrieve starting position
        [fast_axis_start, middle_axis_start, slow_axis_start] = \
            [(parameterDict['axis_startpos'][i][0] / convFactors[i]) for i in range(3)]
        
        # Retrieve center positions and deduce new starting positions
        [fast_axis_center, middle_axis_center, slow_axis_center] = \
            [(parameterDict['axis_centerpos'][i] / convFactors[i]) for i in range(3)]
        
        fast_axis_start = fast_axis_start - fast_axis_center
        middle_axis_start = middle_axis_start - middle_axis_center
        slow_axis_start = slow_axis_start - slow_axis_center

        fast_axis_positions = 1 if fast_axis_size == 0 or fast_axis_step_size == 0 else \
            int(np.ceil(fast_axis_size / fast_axis_step_size)) # Removed 1 + to make it compatible with new scan designer, to be checked!
        middle_axis_positions = 1 if middle_axis_size == 0 or middle_axis_step_size == 0 else \
            int(np.ceil(middle_axis_size / middle_axis_step_size))
        slow_axis_positions = 1 if slow_axis_size == 0 or slow_axis_step_size == 0 else \
            int(np.ceil(slow_axis_size / slow_axis_step_size))

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
        self._logger.debug(rampValues)
        for s in range(fast_axis_positions):
            start = s * sequenceSamples
            end = s * sequenceSamples + sequenceSamples
            smooth = int(np.ceil(0.002 * sampleRate))
            settling = int(np.ceil(0.002 * sampleRate))
            rampSignal[start: end] = rampValues[s]
            if s != fast_axis_positions - 1:
                if (end - smooth - settling) > 0:
                    rampSignal[end - smooth - settling: end - settling] = self.__smoothRamp(rampValues[s], rampValues[s + 1], smooth)
                    rampSignal[end - settling:end] = rampValues[s + 1]

        fast_axis_offset = self.__make_intrapixel_line_offset(
            positioner_line_program,
            parameterDict['target_device'][0],
            fast_axis_positions,
            sequenceSamples,
            sampleRate,
            convFactors[0],
        )
        if fast_axis_offset is not None:
            rampSignal += fast_axis_offset

        #rampSignal = self.__makeRamp(fast_axis_start, fast_axis_size, rampSamples)
        returnRamp = self.__smoothRamp(fast_axis_size+fast_axis_start, fast_axis_start, returnSamples)
        fullLineSignal = np.concatenate((rampSignal, returnRamp))

        fastAxisSignal = np.tile(fullLineSignal, middle_axis_positions * n_linesteps * slow_axis_positions)

        # Make middle axis signal
        colValues = self.__makeRamp(middle_axis_start, middle_axis_size, middle_axis_positions)

        colSamples = middle_axis_positions * n_linesteps * lineSamples
        fullSquareSignal = np.zeros(colSamples)
        middle_axis_offset = self.__make_intrapixel_line_offset(
            positioner_line_program,
            parameterDict['target_device'][1],
            fast_axis_positions,
            sequenceSamples,
            sampleRate,
            convFactors[1],
        )

        for s in range(middle_axis_positions):
            for r in range(n_linesteps):
                block0 = (s * n_linesteps + r) * lineSamples
                block1 = block0 + lineSamples

                # hold during the pixel ramp portion
                fullSquareSignal[block0: block0 + rampSamples] = colValues[s]
                if middle_axis_offset is not None:
                    fullSquareSignal[block0: block0 + rampSamples] += middle_axis_offset

                # return portion:
                if r < n_linesteps - 1:
                    # stay at same middle position for repeats
                    fullSquareSignal[block0 + rampSamples: block1] = colValues[s]
                else:
                    # only on the last repeat: ramp to next middle position (or wrap)
                    next_val = colValues[s + 1] if (s + 1) < middle_axis_positions else middle_axis_start
                    fullSquareSignal[block0 + rampSamples: block1] = self.__smoothRamp(colValues[s], next_val,
                                                                                       returnSamples)

        middleAxisSignal = np.tile(fullSquareSignal, slow_axis_positions)

        # Make slow axis signal
        sliceSamples = slow_axis_positions * colSamples
        sliceValues = self.__makeRamp(slow_axis_start, slow_axis_size, slow_axis_positions)
        self._logger.debug(sliceValues)
        fullCubeSignal = np.zeros(sliceSamples)
        slow_axis_offset = self.__make_intrapixel_line_offset(
            positioner_line_program,
            parameterDict['target_device'][2],
            fast_axis_positions,
            sequenceSamples,
            sampleRate,
            convFactors[2],
        )
        for s in range(slow_axis_positions):
            fullCubeSignal[s * colSamples:(s + 1) * colSamples - returnSamples] = sliceValues[s]
            if slow_axis_offset is not None:
                slice0 = s * colSamples
                for line_idx in range(middle_axis_positions * n_linesteps):
                    line0 = slice0 + line_idx * lineSamples
                    fullCubeSignal[line0: line0 + rampSamples] += slow_axis_offset

            try:
                fullCubeSignal[(s + 1) * colSamples - returnSamples:(s + 1) * colSamples] = \
                    self.__smoothRamp(sliceValues[s], sliceValues[s + 1], returnSamples)
            except IndexError:
                fullCubeSignal[(s + 1) * colSamples - returnSamples:(s + 1) * colSamples] = \
                    self.__smoothRamp(sliceValues[s], slow_axis_start, returnSamples)
        slowAxisSignal = fullCubeSignal

        if slow_axis_size > 0:
            sig_dict = {parameterDict['target_device'][0]: fastAxisSignal,
                        parameterDict['target_device'][1]: middleAxisSignal,
                        parameterDict['target_device'][2]: slowAxisSignal}
            positions = [fast_axis_positions, middle_axis_positions, slow_axis_positions]
        else:
            sig_dict = {parameterDict['target_device'][0]: fastAxisSignal,
                        parameterDict['target_device'][1]: middleAxisSignal}
            positions = [fast_axis_positions, middle_axis_positions]

        # Build complete scanInfoDict via ScanInfoContract
        img_dims = list(positions)
        img_axes_phys = ["x", "y", "z"][:len(img_dims)]
        pixel_sizes = [parameterDict['axis_step_size'][i] for i in range(len(img_dims))]

        scan_samples = [sequenceSamples, rampSamples]
        if slow_axis_size > 0:
            scan_samples.append(colSamples)

        contract = ScanInfoContract(
            img_dims=img_dims,
            img_axes_phys=img_axes_phys,
            pixel_sizes=pixel_sizes,
            scan_samples=scan_samples,
            scan_samples_total=len(fastAxisSignal),
            scan_samples_d2_period=lineSamples,
            n_pixels_fast=fast_axis_positions,
            samples_per_pixel=sequenceSamples,
            dwell_time=parameterDict['sequence_time'],
            scan_time_step=1.0 / sampleRate,
            n_linesteps=n_linesteps,
            positions=positions,
            return_time=parameterDict['return_time'],
        )
        scanInfoDict = contract.to_dict()
        scanInfoDict["positioner_line_program"] = positioner_line_program
        self._last_positioner_line_program = positioner_line_program

        self.__plot_curves(plot=False, signals=[fastAxisSignal, middleAxisSignal, slowAxisSignal])

        return sig_dict, positions, scanInfoDict

    def __make_intrapixel_line_offset(self, positioner_line_program, target_device,
                                      n_pixels, sequence_samples, sample_rate, conv_factor):
        """Build one fast-line additive offset for a target axis.

        The advanced positioner program is authored per pixel dwell. This returns
        one full active-line offset, tiled across all fast-axis pixels. Return
        values are already converted from micrometres to the scan signal units.
        """
        starts_s, ends_s, steps_um = self.__get_axis_intrapixel_commands(
            positioner_line_program, target_device
        )
        if not starts_s or not ends_s:
            return None

        sequence_samples = int(sequence_samples)
        pixel_offset = np.zeros(sequence_samples, dtype=float)
        for command_idx, start_s in enumerate(starts_s):
            if command_idx >= len(ends_s):
                continue

            if command_idx < len(steps_um):
                step_um = float(steps_um[command_idx])
            elif steps_um:
                step_um = float(steps_um[-1])
            else:
                step_um = 0.0

            start_sample = int(round(float(start_s) * sample_rate))
            end_sample = int(round(float(ends_s[command_idx]) * sample_rate))
            start_sample = max(0, min(sequence_samples, start_sample))
            end_sample = max(0, min(sequence_samples, end_sample))
            if start_sample >= sequence_samples or end_sample <= start_sample:
                continue

            pixel_offset[start_sample:end_sample] += step_um / conv_factor

        if not np.any(pixel_offset):
            return None

        return np.tile(pixel_offset, int(n_pixels))

    @staticmethod
    def __get_axis_intrapixel_commands(positioner_line_program, target_device):
        """Return the first enabled line-step commands for *target_device*."""
        program = positioner_line_program or {}
        if not program.get("enabled", False):
            return [], [], []
        if target_device not in program.get("target_device", []):
            return [], [], []

        n_linesteps = int(program.get("n_linesteps", 1))
        enable_vec = list(program.get("linestep_enable", {}).get(target_device, []))
        starts_steps = list(program.get("movement_starts_s", {}).get(target_device, []))
        ends_steps = list(program.get("movement_ends_s", {}).get(target_device, []))
        step_steps = list(program.get("step_size_um", {}).get(target_device, []))

        for step_idx in range(n_linesteps):
            enabled = enable_vec[step_idx] if step_idx < len(enable_vec) else False
            starts_s = starts_steps[step_idx] if step_idx < len(starts_steps) else []
            ends_s = ends_steps[step_idx] if step_idx < len(ends_steps) else []
            if not enabled and not (starts_s and ends_s):
                continue

            steps_um = step_steps[step_idx] if step_idx < len(step_steps) else []
            return list(starts_s or []), list(ends_s or []), list(steps_um or [])

        return [], [], []

    def __normalize_positioner_line_program(self, parameterDict, n_linesteps):
        """Return intra-pixel positioner movement params in scan-designer shape.

        The advanced line-program UI stores positioner movements beside TTL
        pulse settings. The TTL designer ignores these fields; this scan
        designer normalizes them so analog curve generation can consume them.
        Times are seconds, step sizes are micrometres.
        """
        enabled = bool(parameterDict.get("intra_pixel_positioner_movement", False))
        targets = list(parameterDict.get("positioner_target_device", []) or [])
        starts_by_dev = parameterDict.get("positioner_movement_starts_s", {}) or {}
        ends_by_dev = parameterDict.get("positioner_movement_ends_s", {}) or {}
        steps_by_dev = parameterDict.get("positioner_step_size_um", {}) or {}
        enable_by_dev = parameterDict.get("positioner_linestep_enable", {}) or {}

        program = {
            "enabled": enabled,
            "target_device": [],
            "n_linesteps": int(n_linesteps),
            "linestep_enable": {},
            "movement_starts_s": {},
            "movement_ends_s": {},
            "step_size_um": {},
        }

        if not enabled:
            return program

        for dev in targets:
            starts_steps = self.__normalize_nested_float_lists(
                starts_by_dev.get(dev, []), n_linesteps
            )
            ends_steps = self.__normalize_nested_float_lists(
                ends_by_dev.get(dev, []), n_linesteps
            )
            step_sizes = self.__normalize_step_size_lists(
                steps_by_dev.get(dev, []), n_linesteps
            )

            enable_vec_raw = enable_by_dev.get(dev, None)
            if enable_vec_raw is None:
                enable_vec = [
                    bool(starts_steps[s] and ends_steps[s])
                    for s in range(n_linesteps)
                ]
            else:
                enable_vec = self.__normalize_bool_vector(
                    enable_vec_raw, n_linesteps
                )

            if not any(enable_vec):
                continue

            program["target_device"].append(dev)
            program["linestep_enable"][dev] = enable_vec
            program["movement_starts_s"][dev] = starts_steps
            program["movement_ends_s"][dev] = ends_steps
            program["step_size_um"][dev] = step_sizes

        return program

    @staticmethod
    def __normalize_nested_float_lists(value, n_steps):
        out = []
        value = list(value or [])
        for i in range(n_steps):
            if i < len(value) and value[i] is not None:
                out.append([float(v) for v in list(value[i] or [])])
            else:
                out.append([])
        return out

    @staticmethod
    def __normalize_step_size_lists(value, n_steps):
        if value is None:
            value = []
        elif not isinstance(value, (list, tuple)):
            value = [value]
        else:
            value = list(value)

        out = []
        for i in range(n_steps):
            if i >= len(value) or value[i] is None:
                out.append([])
                continue

            item = value[i]
            if isinstance(item, (list, tuple)):
                out.append([float(v) for v in item])
            else:
                out.append([float(item)])

        return out

    @staticmethod
    def __normalize_float_vector(value, n_steps, default=0.0):
        value = list(value or [])
        out = []
        for i in range(n_steps):
            if i < len(value):
                out.append(float(value[i]))
            else:
                out.append(float(default))
        return out

    @staticmethod
    def __normalize_bool_vector(value, n_steps):
        value = list(value or [])
        out = []
        for i in range(n_steps):
            out.append(bool(value[i]) if i < len(value) else False)
        return out

    def __makeRamp(self, start, size, samples):
        #return np.linspace(start, end, num=samples)
        end = start + size
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
