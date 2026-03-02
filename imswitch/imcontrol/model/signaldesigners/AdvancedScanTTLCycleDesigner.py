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
        Fs = setupInfo.scan.sampleRate
        if scanInfoDict is None:
            return self._make_preview(parameterDict, Fs)
        return self._make_full_scan(parameterDict, setupInfo, scanInfoDict, Fs)

    # -----------------
    # ScanInfo normalization (adapter layer)
    # -----------------
    def _normalize_scaninfo(self, p, setupInfo, scanInfoDict, Fs):
        """Normalize scanInfoDict to the contract expected by this TTL designer.

        Supports:
          - Galvo/PointScan-style scanInfoDict (already contains scan_samples*, img_dims, etc.)
          - Beta-style scanInfoDict that only provides: positions, return_time, n_linesteps

        Returns a *new dict* (does not mutate the input).
        """
        si_in = {} if scanInfoDict is None else dict(scanInfoDict)

        # If it already looks like the full PointScan contract, just ensure defaults.
        looks_full = (
            "img_dims" in si_in
            and "scan_samples" in si_in
            and "scan_samples_total" in si_in
            and "scan_samples_d2_period" in si_in
        )
        if looks_full:
            si = dict(si_in)

            img_dims = list(si.get("img_dims", []))

            axis_names = list(si.get("axis_names", []))
            if len(axis_names) < len(img_dims):
                axis_names = axis_names + [f"axis{j}" for j in range(len(axis_names), len(img_dims))]
            si["axis_names"] = axis_names

            smooth_axes = list(si.get("smooth_axes", []))
            if len(smooth_axes) < len(img_dims):
                smooth_axes = smooth_axes + [False] * (len(img_dims) - len(smooth_axes))
            si["smooth_axes"] = smooth_axes

            # Safe defaults for optional keys
            si.setdefault("scan_throw_settling", 0)
            si.setdefault("scan_throw_startzero", 0)
            si.setdefault("scan_throw_startacc", 0)
            si.setdefault("scan_pads_initpos", [0])

            return si

        # ---- Beta-style minimal contract adapter ---- if more options come later make this a switch than a hard fail
        if "positions" not in si_in:
            raise KeyError("scanInfoDict must contain 'positions' for Beta-style normalization.")

        positions = list(si_in["positions"])
        if len(positions) < 1:
            raise ValueError("scanInfoDict['positions'] must have at least one element (Nx).")

        Nx = int(positions[0])
        Ny = int(positions[1]) if len(positions) >= 2 else 1
        Nz = int(positions[2]) if len(positions) >= 3 else 1

        # Linesteps come from TTL parameters; fall back to scanInfoDict if present
        S = int(p.get("n_linesteps", si_in.get("n_linesteps", 1)))
        S = max(1, S)

        dwell_s = float(p.get("sequence_time", 0.0))
        if dwell_s <= 0:
            raise ValueError("TTL parameter 'sequence_time' must be > 0 for Beta-style scans.")

        return_time = float(si_in.get("return_time", 0.0))
        if return_time < 0:
            return_time = 0.0

        samples_per_pixel = max(1, int(round(dwell_s * Fs)))
        line_len = int(Nx * samples_per_pixel)
        flyback = int(round(return_time * Fs))
        if flyback < 0:
            flyback = 0
        period_len = int(line_len + flyback)

        # Define linestep as: repeat the fast-axis line S times per middle-axis position.
        n_line_periods_total = max(1, Ny) * S

        # One 2D frame worth of samples (with flyback between lines, except last)
        d3_len = (n_line_periods_total - 1) * period_len + line_len

        # Total samples includes Z by repeating the d3 block
        samples_total = d3_len * max(1, Nz) + flyback

        si = dict(si_in)
        # Internal dims: [x, expanded_y, z] so this TTL code can always index [2]
        si["img_dims"] = [Nx, n_line_periods_total, max(1, Nz)]
        si["axis_names"] = ["x", "y", "z"]

        # scan_samples convention used by this TTL file:
        #   scan_samples[1] == line_len (no flyback)
        #   scan_samples[2] == d3_len (one frame)
        si["scan_samples"] = [samples_per_pixel, line_len, d3_len]
        si["scan_samples_total"] = int(samples_total)
        si["scan_samples_d2_period"] = int(period_len)

        # No explicit throw/settling sections for Beta by default
        si["scan_throw_settling"] = 0
        si["scan_throw_startzero"] = 0
        si["scan_throw_startacc"] = 0
        si["scan_pads_initpos"] = [0]

        # No smoothing pads for Beta by default
        si["smooth_axes"] = [False, False, False]

        # Provide the intra-pixel pulse helpers explicitly
        si["n_pixels_fast"] = Nx
        si["samples_per_pixel"] = samples_per_pixel

        return si


    # -----------------
    # Preview (graph)
    # -----------------

    def _make_preview(self, p, Fs):
        """
        Return per-target boolean arrays for plotting.
        We generate 1 pixel worth of TTL *for each linestep* and concatenate them.
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
                enabled_here = enable_vec[s] if s < len(enable_vec) else False

                if not enabled_here:
                    pixel = np.zeros(samples_per_pixel, dtype="bool")
                elif not advanced:
                    pixel = np.ones(samples_per_pixel, dtype="bool")
                else:
                    starts_s = starts_steps[s] if s < len(starts_steps) else []
                    ends_s = ends_steps[s] if s < len(ends_steps) else []

                    # Match _build_one_line behavior:
                    # if enabled + advanced but no pulses defined -> full on
                    if (starts_s is None or len(starts_s) == 0) and (ends_s is None or len(ends_s) == 0):
                        pixel = np.ones(samples_per_pixel, dtype="bool")
                    else:
                        # Build pixel window(s)
                        starts_s = [] if starts_s is None else list(starts_s)
                        ends_s = [] if ends_s is None else list(ends_s)

                        if len(starts_s) != len(ends_s):
                            min_len = min(len(starts_s), len(ends_s))
                            starts_s = starts_s[:min_len]
                            ends_s = ends_s[:min_len]

                        pixel = np.zeros(samples_per_pixel, dtype="bool")
                        for a, b in zip(starts_s, ends_s):
                            if a is None or b is None:
                                continue
                            if a < 0 or b < 0 or a >= b:
                                raise ValueError(f"Invalid pulse window: start={a}, end={b}")
                            if b > dwell_s + 1e-12:
                                raise ValueError(f"Pulse end {b}s exceeds dwell time {dwell_s}s")

                            i0 = int(round(a * Fs))
                            i1 = int(round(b * Fs))
                            i0 = max(0, min(samples_per_pixel, i0))
                            i1 = max(0, min(samples_per_pixel, i1))
                            if i1 > i0:
                                pixel[i0:i1] = True

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
        scanInfo = self._normalize_scaninfo(p, setupInfo, scanInfoDict, Fs)
        for key in scanInfo.keys():
            scanInfoDict[key] = scanInfo[key]

        # Existing scan structure variables
        n_steps_dx = scanInfo["img_dims"]
        axis_count = len(n_steps_dx)

        # --- Use controller-provided axis/period model if available ---
        adv = (scanInfo.get("advanced_scan", None) or {})
        if adv:
            n_line_periods_total = int(adv["n_line_periods_total"])
        else:
            # Fallback to legacy assumptions (keeps older behavior)
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
            # Pad extra bits for smooth axes (kept)
            if any(self.smooth_axes[:2]):
                signal_d3 = np.append(self.__initpad, signal_d3_base)
                init_added = True
            else:
                signal_d3 = signal_d3_base
                init_added = False

            # Adjust to d3 step length when smoothing
            if any(self.smooth_axes[:2]):
                if has_d3:
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
        if len(n_steps_dx_clock) < 2:
            n_steps_dx_clock.append(n_line_periods_total)
        else:
            n_steps_dx_clock[1] = n_line_periods_total
        axis_count_clock = len(n_steps_dx_clock)

        signal_dict["line_clock"] = self.__generate_frame_line_clock(
            n_scan_samples_dx=n_scan_samples_dx,
            n_steps_dx=n_steps_dx_clock,
            samples_total=samples_total,
            axis_count=axis_count_clock,
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
            axis_count=axis_count_clock,
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
            axis_count=axis_count_clock,
            scan_pads_initpos=scan_pads_initpos,
            zeropad_start=zeropad_start,
            zeropad_d2flyback=zeropad_d2flyback,
            frame_end=True,
            clock_len=clock_len,
        )

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
            print("pulse_starts_s and pulse_ends_s do not have same length per device per linestep. Dropping extra!")

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
    # Helper: repeat higher axes (slight tweak to keep init_added explicit)
    # -----------------

    def __repeat_remaining_axes(self, signal, n_steps_dx, n_scan_samples_dx, axis_start, axis_end, init_added: bool):
        for axis in range(axis_start, axis_end):
            if axis >= 2:
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
            if axis >= 2:
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
        has_d3 = len(n_scan_samples_dx) > 2
        if has_d3:
            zeropad_to_axislen = n_scan_samples_dx[2] - len(signal_d2)
            if zeropad_to_axislen > 0:
                signal_d2 = np.append(signal_d2, np.zeros(zeropad_to_axislen, dtype='bool'))
            elif zeropad_to_axislen < 0:
                signal_d2 = signal_d2[:zeropad_to_axislen]
        else:
            signal_d2 = signal_d2

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

