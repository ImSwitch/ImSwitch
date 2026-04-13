import numpy as np

from ..signaldesigners.basesignaldesigners import TTLCycleDesigner


class AdvancedScanTTLCycleDesigner(TTLCycleDesigner):
    """
    TTL cycle designer for PointScan with:
      - Line-step gating: repeat each line S times (linesteps), each with its own device enable.
      - Optional intra-pixel pulse timing per device per linestep, within [0, dwell_time].

    ParameterDict (digitalParameterDict) expected:
      target_device: list[str]
      n_linesteps: int
      linestep_enable: dict[str, list[bool]]              # dev -> length S
      pulse_starts_s: dict[str, list[list[float]]]        # dev -> length S -> list starts (sec)
      pulse_ends_s:   dict[str, list[list[float]]]        # dev -> length S -> list ends (sec)
      sequence_time: float                                # dwell time per pixel (sec)
      advanced_mode: bool                                 # if False: ignore pulses, constant ON/OFF per linestep

    scanInfoDict expected (when scanning):
      img_dims: list[int]               # axis lengths in "steps" (pixels/lines/frames/...)
      axis_names: list[str]             # names, used only if you keep legacy features elsewhere
      scan_samples: list[int]           # samples per axis step-length (?) as in current PointScan
      scan_samples_total: int
      scan_samples_d2_period: int
      scan_throw_settling: int
      scan_throw_startzero: int
      scan_throw_startacc: int
      scan_pads_initpos: list[int]
      smooth_axes: list[bool]

      PLUS (needed for advanced intra-pixel pulses):
      samples_per_pixel: int            # number of digital samples per pixel dwell
      n_pixels_fast: int                # pixels per line on fast axis (should match img_dims[0])
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._expectedParameters = [
            "target_device",
            "n_linesteps",
            "linestep_enable",
            "pulse_starts_s",
            "pulse_ends_s",
            "sequence_time",
            "advanced_mode",
        ]

        # optional, for debug plotting upstream
        self._last_preview_step_boundaries = None

    @property
    def timeUnits(self):
        # The actual storage is seconds.
        return "ms"

    # -----------------
    # Public API
    # -----------------

    def make_signal(self, parameterDict, setupInfo, scanInfoDict=None):
        Fs = setupInfo.scan.sampleRate
        if scanInfoDict is None:
            return self._make_preview(parameterDict, Fs)
        return self._make_full_scan(parameterDict, setupInfo, scanInfoDict, Fs)


    # -----------------
    # Preview (graph)
    # -----------------

    def _make_preview(self, p, Fs):
        """
        Return per-target boolean arrays for plotting.
        We generate 1 pixel worth of TTL for each linestep and concatenate them.
        """
        targets = p["target_device"]
        S = int(p["n_linesteps"])
        dwell_s = float(p["sequence_time"])
        advanced = bool(p["advanced_mode"])

        # For preview, choose a reasonable pixel count & samples_per_pixel
        # (You can override later by passing these in p if you want.)
        n_pixels = 64
        samples_per_pixel = max(1, int(round(dwell_s * Fs)))
        line_len = n_pixels * samples_per_pixel

        signal_dict = {}
        step_boundaries = [0]
        for dev in targets:
            enable_vec = list(map(bool, p["linestep_enable"].get(dev, [False] * S)))
            starts_steps = p["pulse_starts_s"].get(dev, [[] for _ in range(S)])
            ends_steps = p["pulse_ends_s"].get(dev, [[] for _ in range(S)])

            parts = []
            for s in range(S):
                line = self._build_one_line(
                    enabled=enable_vec[s],
                    advanced=advanced,
                    starts_s=starts_steps[s] if s < len(starts_steps) else [],
                    ends_s=ends_steps[s] if s < len(ends_steps) else [],
                    dwell_s=dwell_s,
                    Fs=Fs,
                    n_pixels=n_pixels,
                    samples_per_pixel=samples_per_pixel,
                )
                parts.append(line)
                step_boundaries.append(step_boundaries[-1] + len(line))

            signal_dict[dev] = np.concatenate(parts).astype(bool)

        # stash boundaries so controller/widget can vline them if desired
        self._last_preview_step_boundaries = step_boundaries
        # (Optionally expose them via a method/property later.)

        return signal_dict


    def make_single_pixel_signal(self, parameterDict, setupInfo):
        """
        Return per-target boolean arrays for exactly ONE pixel worth of samples,
        concatenated across all linesteps.

        This is intended for legacy code paths (e.g. getNumCamTTL) that assume the
        TTL waveform represents a single pixel, not the full scan.
        """
        Fs = setupInfo.scan.sampleRate

        targets = parameterDict["target_device"]
        S = int(parameterDict["n_linesteps"])
        dwell_s = float(parameterDict["sequence_time"])
        advanced = bool(parameterDict["advanced_mode"])

        samples_per_pixel = max(1, int(round(dwell_s * Fs)))

        signal_dict = {}
        for dev in targets:
            enable_vec = list(map(bool, parameterDict["linestep_enable"].get(dev, [False] * S)))
            starts_steps = parameterDict["pulse_starts_s"].get(dev, [[] for _ in range(S)])
            ends_steps = parameterDict["pulse_ends_s"].get(dev, [[] for _ in range(S)])

            parts = []
            for s in range(S):
                pixel = self._build_one_line(
                    enabled=enable_vec[s] if s < len(enable_vec) else False,
                    advanced=advanced,
                    starts_s=starts_steps[s] if s < len(starts_steps) else [],
                    ends_s=ends_steps[s] if s < len(ends_steps) else [],
                    dwell_s=dwell_s,
                    Fs=Fs,
                    n_pixels=1,
                    samples_per_pixel=samples_per_pixel,
                )
                parts.append(pixel)

            signal_dict[dev] = np.concatenate(parts).astype(bool)

        return signal_dict

    # -----------------
    # Full scan
    # -----------------

    def _make_full_scan(self, p, setupInfo, scanInfoDict, Fs):
        signal_dict = {}

        targets = p["target_device"]
        S = int(p["n_linesteps"])
        dwell_s = float(p["sequence_time"])
        advanced = bool(p["advanced_mode"])

        # scanInfoDict is already a complete ScanInfoContract dict from the scan designer.
        scanInfo = scanInfoDict

        # Existing scan structure variables (img_dims is physical-only per ScanInfoContract)
        n_steps_dx = scanInfo["img_dims"]
        axis_count = len(n_steps_dx)

        n_lines_phys = int(n_steps_dx[1]) if len(n_steps_dx) > 1 else 1
        n_line_periods_total = n_lines_phys * S

        n_scan_samples_dx = scanInfo["scan_samples"]
        samples_total = scanInfo["scan_samples_total"]
        self.smooth_axes = scanInfo["smooth_axes"]

        zeropad_d2flyback = scanInfo["scan_samples_d2_period"] - n_scan_samples_dx[1]
        if zeropad_d2flyback < 0:
            zeropad_d2flyback = max(0, scanInfo["scan_samples_d2_period"] - n_scan_samples_dx[1])

        zeropad_settling = scanInfo["scan_throw_settling"]
        zeropad_start = scanInfo["scan_throw_startzero"]
        zeropad_startacc = scanInfo["scan_throw_startacc"]
        scan_pads_initpos = scanInfo["scan_pads_initpos"]

        pad_initpos = scan_pads_initpos[0] if len(scan_pads_initpos) > 0 else 0
        self.__initpad = np.zeros(zeropad_startacc + zeropad_settling + pad_initpos, dtype="bool")

        # New required pieces for intra-pixel pulses
        n_pixels_fast = int(scanInfo.get("n_pixels_fast", n_steps_dx[0]))
        samples_per_pixel = int(scanInfo.get("samples_per_pixel", 0))
        if samples_per_pixel <= 0:
            # Fall back to uniform division if not provided
            if n_pixels_fast <= 0:
                raise ValueError("n_pixels_fast must be >0 for advanced TTL.")
            if n_scan_samples_dx[1] % n_pixels_fast != 0:
                raise ValueError(
                    f"scan_samples for line ({n_scan_samples_dx[1]}) not divisible by n_pixels_fast ({n_pixels_fast})."
                )
            samples_per_pixel = n_scan_samples_dx[1] // n_pixels_fast

        has_d3 = len(n_scan_samples_dx) > 2

        for dev in targets:
            enable_vec_raw = list(map(bool, p["linestep_enable"].get(dev, [False] * S)))
            starts_steps = p["pulse_starts_s"].get(dev, [[] for _ in range(S)])
            ends_steps = p["pulse_ends_s"].get(dev, [[] for _ in range(S)])

            # Decide gating mode:
            # - legacy: enable_vec length == S => enable depends on linestep index s
            # - new:    enable_vec length == n_steps_dx[1] (expanded lines Ny*S) => enable per expanded line
            n_expanded_lines = int(n_line_periods_total)
            if len(enable_vec_raw) == S:
                enable_mode = "per_step"
            elif len(enable_vec_raw) == n_expanded_lines:
                enable_mode = "per_expanded_line"
            else:
                raise ValueError(
                    f"linestep_enable[{dev}] length must be S={S} or n_line_periods_total={n_expanded_lines}, "
                    f"got {len(enable_vec_raw)}"
                )

            # Cache the *ON* waveform per linestep (independent of enable gating)
            # We'll gate it per expanded line later (important for new mode).
            cached_period_on = []
            cached_line_on = []
            period_len = None
            for s in range(S):
                line_on = self._build_one_line(
                    enabled=True,  # always build ON waveform; actual enable is applied later
                    advanced=advanced,
                    starts_s=starts_steps[s] if s < len(starts_steps) else [],
                    ends_s=ends_steps[s] if s < len(ends_steps) else [],
                    dwell_s=dwell_s,
                    Fs=Fs,
                    n_pixels=n_pixels_fast,
                    samples_per_pixel=samples_per_pixel,
                )
                period_on = np.append(line_on, np.zeros(zeropad_d2flyback, dtype="bool"))
                cached_period_on.append(period_on)
                cached_line_on.append(line_on)
                period_len = len(period_on)

            # Cached OFF waveforms
            cached_period_off = np.zeros(period_len, dtype="bool")
            cached_line_off = np.zeros(len(cached_line_on[0]), dtype="bool")

            # Build the full frame/stack by iterating expanded lines
            # expanded_line_idx runs 0..n_steps_dx[1]-1, linestep = idx % S
            # Note: last line period is special (no flyback) just like original code.
            chunks = []

            for expanded_line_idx in range(n_line_periods_total - 1):
                s = expanded_line_idx % S

                if enable_mode == "per_step":
                    enabled_here = bool(enable_vec_raw[s])
                else:
                    # If you use per_expanded_line, it must match THIS loop length.
                    enabled_here = bool(enable_vec_raw[expanded_line_idx])
                chunks.append(cached_period_on[s] if enabled_here else cached_period_off)


            # last line without flyback
            last_idx = n_line_periods_total - 1
            s_last = last_idx % S

            if enable_mode == "per_step":
                enabled_last = bool(enable_vec_raw[s_last])
            else:
                enabled_last = bool(enable_vec_raw[last_idx])

            chunks.append(cached_line_on[s_last] if enabled_last else cached_line_off)
            signal_d3_base = np.concatenate(chunks).astype(bool)

            # Smooth-axis init pad
            if any(self.smooth_axes[:2]):
                signal_d3 = np.append(self.__initpad, signal_d3_base)
                init_added = True
                if has_d3:
                    signal_d3 = self.__fit_to_length(signal_d3, n_scan_samples_dx[2])
            else:
                signal_d3 = signal_d3_base
                init_added = False

            # Repeat higher axes, then outer padding and trim
            signal = self.__repeat_remaining_axes(signal=signal_d3,
                                                 n_steps_dx=n_steps_dx,
                                                 n_scan_samples_dx=n_scan_samples_dx,
                                                 axis_start=2,
                                                 axis_end=axis_count,
                                                 init_added=init_added)
            signal = self.__pad_and_trim_to_total(
                signal, scan_pads_initpos, zeropad_start, samples_total
            )
            signal_dict[dev] = signal.astype(bool)

        # --- Clock signals ---
        n_steps_dx_clock = list(n_steps_dx)
        if len(n_steps_dx_clock) < 2:
            n_steps_dx_clock.append(n_line_periods_total)
        else:
            n_steps_dx_clock[1] = n_line_periods_total

        signal_dict.update(self.__generate_all_clocks(
            n_scan_samples_dx=n_scan_samples_dx,
            n_steps_dx=n_steps_dx_clock,
            samples_total=samples_total,
            axis_count=len(n_steps_dx_clock),
            scan_pads_initpos=scan_pads_initpos,
            zeropad_start=zeropad_start,
            zeropad_d2flyback=zeropad_d2flyback,
        ))

        return signal_dict, scanInfoDict

    # -----------------
    # Line builder (core new piece)
    # -----------------

    def _build_one_line(
        self,
        *,
        enabled: bool,
        advanced: bool,
        starts_s,
        ends_s,
        dwell_s: float,
        Fs: float,
        n_pixels: int,
        samples_per_pixel: int,
    ):
        """
        Build boolean TTL for the *line samples only* (no flyback), length = n_pixels*samples_per_pixel.
        - If not enabled: all zeros.
        - If enabled and not advanced: all ones (constant on).
        - If enabled and advanced: per-pixel pulses repeated for each pixel.
        """
        total = n_pixels * samples_per_pixel
        if not enabled:
            return np.zeros(total, dtype="bool")

        if not advanced:
            return np.ones(total, dtype="bool")

        # Advanced: build one pixel waveform, then tile across pixels
        starts_s = [] if starts_s is None else list(starts_s)
        ends_s = [] if ends_s is None else list(ends_s)


        if len(starts_s) != len(ends_s):
            min_len = min(len(starts_s), len(ends_s))
            starts_s = starts_s[:min_len]
            ends_s = ends_s[:min_len]
            self._logger.warning("pulse_starts_s and pulse_ends_s length mismatch; dropping extra entries.")

        # If the device is enabled for this linestep but the user did not specify any pulse windows,
        # treat this as "full on" (advanced program is an override, not a requirement).
        if len(starts_s) == 0 and len(ends_s) == 0:
            return np.ones(total, dtype="bool")

        # Validate
        for a, b in zip(starts_s, ends_s):
            if a is None or b is None:
                continue
            if a < 0 or b < 0 or a >= b:
                raise ValueError(f"Invalid pulse window: start={a}, end={b}")
            if b > dwell_s + 1e-12:
                raise ValueError(f"Pulse end {b}s exceeds dwell time {dwell_s}s")

        pixel = np.zeros(samples_per_pixel, dtype="bool")
        for a, b in zip(starts_s, ends_s):
            if a is None or b is None:
                continue
            i0 = int(round(a * Fs))
            i1 = int(round(b * Fs))
            i0 = max(0, min(samples_per_pixel, i0))
            i1 = max(0, min(samples_per_pixel, i1))
            if i1 > i0:
                pixel[i0:i1] = True

        return np.tile(pixel, n_pixels).astype(bool)

    # -----------------
    # Shared helpers
    # -----------------

    @staticmethod
    def __fit_to_length(signal, target_len):
        """Pad or trim *signal* so its length equals *target_len*."""
        diff = target_len - len(signal)
        if diff > 0:
            return np.append(signal, np.zeros(diff, dtype="bool"))
        if diff < 0:
            return signal[:target_len]
        return signal

    def __pad_and_trim_to_total(self, signal, scan_pads_initpos, zeropad_start, samples_total):
        """Outer padding (higher-axis initpos, start zeros) then trim/extend to samples_total."""
        if len(scan_pads_initpos) > 1:
            if any(np.greater(scan_pads_initpos[1:], scan_pads_initpos[0])):
                padlen = np.max(scan_pads_initpos[1:]) - scan_pads_initpos[0]
                signal = np.append(np.zeros(padlen, dtype="bool"), signal)

        signal = np.append(np.zeros(zeropad_start, dtype="bool"), signal)
        return self.__fit_to_length(signal, samples_total)

    # -----------------
    # Repeat higher axes
    # -----------------

    def __repeat_remaining_axes(self, signal, n_steps_dx, n_scan_samples_dx, axis_start, axis_end, init_added: bool):
        for axis in range(axis_start, axis_end):
            if axis >= 2:
                signal = self.__fit_to_length(signal, n_scan_samples_dx[axis])
            signal = np.tile(signal, n_steps_dx[axis])

            if not any(self.smooth_axes[:2]) and not init_added:
                signal = np.append(self.__initpad, signal)
                init_added = True

        return signal

    def __repeat_remaining_axes_clock(self, signal, n_steps_dx, n_scan_samples_dx, axis_start, axis_end):
        """Repeat a created clock signal for remaining axes."""
        for axis in range(axis_start, axis_end):
            if axis >= 2:
                signal = self.__fit_to_length(signal, n_scan_samples_dx[axis])
            signal = np.tile(signal, n_steps_dx[axis])

            # Match PointScan logic: add initpad only when smoothing requires it
            if not any(self.smooth_axes[:axis]) and self.smooth_axes[axis] and not self.__init_added:
                signal = np.append(self.__initpad, signal)
                self.__init_added = True

        return signal

    # -----------------
    # Clock generation
    # -----------------

    def __generate_all_clocks(self, n_scan_samples_dx, n_steps_dx, samples_total,
                              axis_count, scan_pads_initpos, zeropad_start,
                              zeropad_d2flyback, clock_len=10):
        """Generate line, frame-start, and frame-end clocks in one pass.

        Returns dict with keys 'line_clock', 'frame_start_clock', 'frame_end_clock'.
        """
        line_len = n_scan_samples_dx[1]
        has_d3 = len(n_scan_samples_dx) > 2

        clocks = {}
        for key, line, frame_start, frame_end in [
            ("line_clock",        True,  False, False),
            ("frame_start_clock", False, True,  False),
            ("frame_end_clock",   False, False, True),
        ]:
            self.__init_added = False

            # one "line" worth of samples
            step = np.zeros(line_len, dtype="bool")
            if line:
                step[:clock_len] = True

            period = np.append(step, np.zeros(zeropad_d2flyback, dtype="bool"))

            # all lines except last (with flyback), then last without flyback
            signal_d2 = np.append(np.tile(period, n_steps_dx[1] - 1), step)

            if frame_start:
                signal_d2[:clock_len] = True
            if frame_end:
                signal_d2[-clock_len:] = True

            # smooth-axis init pad
            if any(self.smooth_axes[:2]):
                signal_d2 = np.append(self.__initpad, signal_d2)
                self.__init_added = True

            # adjust to d3 length
            if has_d3:
                signal_d2 = self.__fit_to_length(signal_d2, n_scan_samples_dx[2])

            # repeat higher axes
            signal = self.__repeat_remaining_axes_clock(
                signal=signal_d2,
                n_steps_dx=n_steps_dx,
                n_scan_samples_dx=n_scan_samples_dx,
                axis_start=2,
                axis_end=axis_count,
            )

            clocks[key] = self.__pad_and_trim_to_total(
                signal, scan_pads_initpos, zeropad_start, samples_total
            )

        return clocks

