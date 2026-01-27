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
        # You can choose "ms" for UI labels if you want. The actual storage is seconds.
        return "ms"

    # -----------------
    # Public API
    # -----------------

    def make_signal(self, parameterDict, setupInfo, scanInfoDict=None):
        if not self.parameterCompatibility(parameterDict):
            self._logger.error(
                "TTL parameters incompatible with LineStepPointScanTTLCycleDesigner."
            )
            return None

        Fs = setupInfo.scan.sampleRate

        # Graph preview (no scanInfo)
        if not scanInfoDict:
            return self._make_preview(parameterDict, Fs)

        return self._make_full_scan(parameterDict, setupInfo, scanInfoDict, Fs)

    # -----------------
    # Preview (graph)
    # -----------------

    def _make_preview(self, p, Fs):
        """
        Return per-target boolean arrays for plotting.
        We generate 1 line worth of TTL *for each linestep* and concatenate them.
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

    # -----------------
    # Full scan
    # -----------------

    def _make_full_scan(self, p, setupInfo, scanInfoDict, Fs):
        signal_dict = {}

        targets = p["target_device"]
        S = int(p["n_linesteps"])
        dwell_s = float(p["sequence_time"])
        advanced = bool(p["advanced_mode"])

        # Existing scan structure variables (kept close to your PointScan)
        n_steps_dx = scanInfoDict["img_dims"]
        axis_count = len(n_steps_dx)
        n_scan_samples_dx = scanInfoDict["scan_samples"]
        samples_total = scanInfoDict["scan_samples_total"]
        scan_axes_order = scanInfoDict["axis_names"]
        self.smooth_axes = scanInfoDict["smooth_axes"]

        zeropad_d2flyback = scanInfoDict["scan_samples_d2_period"] - n_scan_samples_dx[1]
        if zeropad_d2flyback < 0:
            zeropad_d2flyback = max(0, scanInfoDict["scan_samples_d2_period"] - n_scan_samples_dx[1])

        zeropad_settling = scanInfoDict["scan_throw_settling"]
        zeropad_start = scanInfoDict["scan_throw_startzero"]
        zeropad_startacc = scanInfoDict["scan_throw_startacc"]
        scan_pads_initpos = scanInfoDict["scan_pads_initpos"]

        pad_initpos = scan_pads_initpos[0] if len(scan_pads_initpos) > 0 else 0
        self.__initpad = np.zeros(zeropad_startacc + zeropad_settling + pad_initpos, dtype="bool")

        # New required pieces for intra-pixel pulses
        n_pixels_fast = int(scanInfoDict.get("n_pixels_fast", n_steps_dx[0]))
        samples_per_pixel = int(scanInfoDict.get("samples_per_pixel", 0))
        if samples_per_pixel <= 0:
            # Fall back to uniform division if not provided
            if n_pixels_fast <= 0:
                raise ValueError("n_pixels_fast must be >0 for advanced TTL.")
            if n_scan_samples_dx[1] % n_pixels_fast != 0:
                raise ValueError(
                    f"scan_samples for line ({n_scan_samples_dx[1]}) not divisible by n_pixels_fast ({n_pixels_fast})."
                )
            samples_per_pixel = n_scan_samples_dx[1] // n_pixels_fast

        Ny = int(n_steps_dx[1])
        line_len = int(n_scan_samples_dx[1])
        period_len = int(scanInfoDict["scan_samples_d2_period"])  # includes flyback

        # Expected d3 length if there are Ny line periods (last has no flyback)
        cand_Ny = (Ny - 1) * period_len + line_len
        # Expected d3 length if there are Ny*S line periods
        cand_NyS = (Ny * S - 1) * period_len + line_len

        d3_len_reported = int(n_scan_samples_dx[2])

        # If smoothing pads are used, d3_len_reported includes initpad sometimes; compensate roughly
        initpad_len = len(self.__initpad) if any(self.smooth_axes[:2]) else 0

        # Compare against reported length (minus initpad if present)
        d3_core = d3_len_reported - initpad_len

        # Choose whichever candidate is closer
        if abs(d3_core - cand_NyS) < abs(d3_core - cand_Ny):
            n_line_periods_total = Ny * S
        else:
            n_line_periods_total = Ny

        # Sanity
        if n_line_periods_total < 1:
            n_line_periods_total = Ny
        # Validate linestep expansion assumption
        # Here we assume the scan designer already expanded the line axis by S, i.e.
        # n_steps_dx[1] == n_lines_original * S OR equivalently we can map expanded_line_idx % S.
        # If that's not true in your scan designer, we can adjust later.
        if n_steps_dx[1] < S:
            raise ValueError("img_dims[1] (lines) must be >= n_linesteps.")

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
            signal_d3_base = np.array([], dtype="bool")
            for expanded_line_idx in range(n_line_periods_total - 1):
                s = expanded_line_idx % S

                if enable_mode == "per_step":
                    enabled_here = bool(enable_vec_raw[s])
                else:
                    # If you use per_expanded_line, it must match THIS loop length.
                    enabled_here = bool(enable_vec_raw[expanded_line_idx])

                signal_d3_base = np.append(
                    signal_d3_base,
                    cached_period_on[s] if enabled_here else cached_period_off
                )

            # last line without flyback
            last_idx = n_line_periods_total - 1
            s_last = last_idx % S

            if enable_mode == "per_step":
                enabled_last = bool(enable_vec_raw[s_last])
            else:
                enabled_last = bool(enable_vec_raw[last_idx])

            signal_d3_base = np.append(
                signal_d3_base,
                cached_line_on[s_last] if enabled_last else cached_line_off
            )

            # Pad extra bits for smooth axes (kept)
            if any(self.smooth_axes[:2]):
                signal_d3 = np.append(self.__initpad, signal_d3_base)
                init_added = True
            else:
                signal_d3 = signal_d3_base
                init_added = False

            # Adjust to d3 step length when smoothing
            if any(self.smooth_axes[:2]):
                zeropad_to_axislen = n_scan_samples_dx[2] - len(signal_d3)
                if zeropad_to_axislen > 0:
                    signal_d3 = np.append(signal_d3, np.zeros(zeropad_to_axislen, dtype="bool"))
                elif zeropad_to_axislen < 0:
                    signal_d3 = signal_d3[:zeropad_to_axislen]

            # Repeat higher axes (reuse your existing helper, with init pad behavior)
            signal = self.__repeat_remaining_axes(signal=signal_d3,
                                                 n_steps_dx=n_steps_dx,
                                                 n_scan_samples_dx=n_scan_samples_dx,
                                                 axis_start=2,
                                                 axis_end=axis_count,
                                                 init_added=init_added)

            # Pad initpos for higher axes, if any (kept)
            if len(scan_pads_initpos) > 1:
                if any(np.greater(scan_pads_initpos[1:], scan_pads_initpos[0])):
                    padlen = np.max(scan_pads_initpos[1:]) - scan_pads_initpos[0]
                    signal = np.append(np.zeros(padlen, dtype="bool"), signal)

            # Pad start zeros
            signal = np.append(np.zeros(zeropad_start, dtype="bool"), signal)

            # Adjust to same length as analog scanning
            zeropad_end = samples_total - len(signal)
            if zeropad_end > 0:
                signal = np.append(signal, np.zeros(zeropad_end, dtype="bool"))
            elif zeropad_end < 0:
                signal = signal[:zeropad_end]

            signal_dict[dev] = signal.astype(bool)

        clock_len = 10  # PointScan inherited default;
        n_steps_dx_clock = list(n_steps_dx)
        n_steps_dx_clock[1] = n_line_periods_total

        signal_dict["line_clock"] = self.__generate_frame_line_clock(
            n_scan_samples_dx=n_scan_samples_dx,
            n_steps_dx=n_steps_dx_clock,
            samples_total=samples_total,
            axis_count=axis_count,
            scan_pads_initpos=scan_pads_initpos,
            zeropad_start=zeropad_start,
            zeropad_d2flyback=zeropad_d2flyback,
            line=True,
            clock_len=clock_len,
        )

        signal_dict["frame_start_clock"] = self.__generate_frame_line_clock(
            n_scan_samples_dx=n_scan_samples_dx,
            n_steps_dx=n_steps_dx_clock,
            samples_total=samples_total,
            axis_count=axis_count,
            scan_pads_initpos=scan_pads_initpos,
            zeropad_start=zeropad_start,
            zeropad_d2flyback=zeropad_d2flyback,
            frame_start=True,
            clock_len=clock_len,
        )

        signal_dict["frame_end_clock"] = self.__generate_frame_line_clock(
            n_scan_samples_dx=n_scan_samples_dx,
            n_steps_dx=n_steps_dx_clock,
            samples_total=samples_total,
            axis_count=axis_count,
            scan_pads_initpos=scan_pads_initpos,
            zeropad_start=zeropad_start,
            zeropad_d2flyback=zeropad_d2flyback,
            frame_end=True,
            clock_len=clock_len,
        )

        return signal_dict

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
            raise ValueError("pulse_starts_s and pulse_ends_s must have same length per device per linestep.")

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
    # Helper: repeat higher axes (slight tweak to keep init_added explicit)
    # -----------------

    def __repeat_remaining_axes(self, signal, n_steps_dx, n_scan_samples_dx, axis_start, axis_end, init_added: bool):
        for axis in range(axis_start, axis_end):
            if axis > 2:
                zeropad_to_axislen = n_scan_samples_dx[axis] - len(signal)
                if zeropad_to_axislen > 0:
                    signal = np.append(signal, np.zeros(zeropad_to_axislen, dtype="bool"))
                elif zeropad_to_axislen < 0:
                    signal = signal[:zeropad_to_axislen]

            signal = np.tile(signal, n_steps_dx[axis])

            if not any(self.smooth_axes[:2]) and not init_added:
                signal = np.append(self.__initpad, signal)
                init_added = True

        return signal

    def __repeat_remaining_axes_clock(self, signal, n_steps_dx, n_scan_samples_dx, axis_start, axis_end):
        """Repeat a created clock signal for remaining axes."""
        for axis in range(axis_start, axis_end):
            if axis > 2:
                zeropad_to_axislen = n_scan_samples_dx[axis] - len(signal)
                if zeropad_to_axislen > 0:
                    signal = np.append(signal, np.zeros(zeropad_to_axislen, dtype='bool'))
                elif zeropad_to_axislen < 0:
                    signal = signal[:zeropad_to_axislen]

            signal = np.tile(signal, n_steps_dx[axis])

            # Match PointScan logic: add initpad only when smoothing requires it
            if not any(self.smooth_axes[:axis]) and self.smooth_axes[axis] and not self.__init_added:
                signal = np.append(self.__initpad, signal)
                self.__init_added = True

        return signal

    def __generate_frame_line_clock(
            self,
            n_scan_samples_dx,
            n_steps_dx,
            samples_total,
            axis_count,
            scan_pads_initpos,
            zeropad_start,
            zeropad_d2flyback,
            *,
            line=False,
            frame_start=False,
            frame_end=False,
            clock_len=10,
    ):
        """Generate frame and line clock signals (bool array length == samples_total)."""
        self.__init_added = False

        # one "line" worth of samples (fast-axis samples)
        signal_d2_step = np.zeros(n_scan_samples_dx[1], dtype='bool')

        if line:
            signal_d2_step[:clock_len] = True

        signal_d2_period = np.append(signal_d2_step, np.zeros(zeropad_d2flyback, dtype='bool'))

        # all lines except last (with flyback)
        signal_d2 = np.tile(signal_d2_period, n_steps_dx[1] - 1)

        # last line without flyback
        signal_d2 = np.append(signal_d2, signal_d2_step)

        if frame_start:
            signal_d2[:clock_len] = True
        if frame_end:
            signal_d2[-clock_len:] = True

        # smooth axes padding (same idea as PointScan)
        if any(self.smooth_axes[:2]):
            signal_d2 = np.append(self.__initpad, signal_d2)
            self.__init_added = True

        # adjust to axis length (d3)
        zeropad_to_axislen = n_scan_samples_dx[2] - len(signal_d2)
        if zeropad_to_axislen > 0:
            signal_d2 = np.append(signal_d2, np.zeros(zeropad_to_axislen, dtype='bool'))
        elif zeropad_to_axislen < 0:
            signal_d2 = signal_d2[:zeropad_to_axislen]

        # repeat for remaining axes
        signal = self.__repeat_remaining_axes_clock(
            signal=signal_d2,
            n_steps_dx=n_steps_dx,
            n_scan_samples_dx=n_scan_samples_dx,
            axis_start=2,
            axis_end=axis_count,
        )

        # pad initpos for higher axes, if any
        if len(scan_pads_initpos) > 1:
            if any(np.greater(scan_pads_initpos[1:], scan_pads_initpos[0])):
                padlen = np.max(scan_pads_initpos[1:]) - scan_pads_initpos[0]
                signal = np.append(np.zeros(padlen, dtype='bool'), signal)

        # pad start zeros
        signal = np.append(np.zeros(zeropad_start, dtype='bool'), signal)

        # adjust to total length
        zeropad_end = samples_total - len(signal)
        if zeropad_end > 0:
            signal = np.append(signal, np.zeros(zeropad_end, dtype='bool'))
        elif zeropad_end < 0:
            signal = signal[:zeropad_end]

        return signal

