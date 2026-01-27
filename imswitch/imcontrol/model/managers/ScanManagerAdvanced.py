# ScanManagerAdvanced.py

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
