# ScanManagerAdvanced.py
import copy

from .ScanManagerBase import ScanManagerBase


class ScanManagerAdvanced(ScanManagerBase):
    """
    Thin wrapper around ScanManagerBase for the advanced scan mode.

    Purpose:
      - makes it explicit in the config that this scan mode is used
      - exposes optional UI helpers (preview boundaries) cleanly
      - keeps PointScan/MoNaLISA behavior via ScanManagerBase implementation
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def getTTLCyclePreviewStepBoundaries(self):
        """
        Optional UI helper: sample indices where linestep boundaries occur in the
        stationary TTL preview returned by AdvancedScanTTLCycleDesigner.
        """
        self._checkScanDefined()
        d = self._TTLCycleDesigner

        # preferred property (add it in the designer)
        if hasattr(d, "last_preview_step_boundaries"):
            try:
                return d.last_preview_step_boundaries
            except Exception:
                return None

        # fallback to internal attribute (as used in our draft)
        if hasattr(d, "_last_preview_step_boundaries"):
            return getattr(d, "_last_preview_step_boundaries")

        return None

    def getTTLCyclePreviewSignalsDict(self, TTLParameters):
        """UI preview: multi-pixel stationary TTL for plotting."""
        self._checkScanDefined()
        parameterDict = copy.deepcopy(self._setupInfo.scan.TTLCycleDesignerParams)
        parameterDict.update(TTLParameters)

        # Force preview behavior explicitly
        return self._TTLCycleDesigner._make_preview(parameterDict, self._setupInfo.scan.sampleRate)

    def getTTLCycleSignalsDict(self, TTLParameters, scanInfoDict=None):
        """
        Generates TTL cycle signals.

        Contract:
          - If scanInfoDict is None: return "single pixel" TTL waveforms (legacy expectation).
          - If scanInfoDict is provided: return full-scan TTL waveforms.
        """
        self._checkScanDefined()
        parameterDict = copy.deepcopy(self._setupInfo.scan.TTLCycleDesignerParams)
        parameterDict.update(TTLParameters)

        if scanInfoDict is None:
            # Legacy-safe path for getNumCamTTL()
            if hasattr(self._TTLCycleDesigner, "make_single_pixel_signal"):
                return self._TTLCycleDesigner.make_single_pixel_signal(parameterDict, self._setupInfo)

            # Fallback: if designer doesn't implement it, at least don't crash
            return self._TTLCycleDesigner.make_signal(parameterDict, self._setupInfo, None)

        # Normal full-scan generation
        return self._TTLCycleDesigner.make_signal(parameterDict, self._setupInfo, scanInfoDict)

