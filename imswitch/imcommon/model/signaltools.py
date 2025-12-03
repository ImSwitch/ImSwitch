from qtpy import QtCore

class OneShotConnection(QtCore.QObject):
    """
    Temporarily connects a Qt signal to a slot and automatically disconnects
    when either:
        • the slot returns True (success), or
        • a timeout occurs.
        
    Parameters
    ----------
    signal : pyqtSignal
        The signal to connect temporarily.
    slot : callable
        Function called with the signal’s arguments.
        Must return True to trigger disconnection when wait_for_success=True.
    timeout_ms : int
        Maximum time to wait before force-disconnecting.
    parent : QObject, optional
        Parent object for Qt memory ownership.
    notify_timeout : bool, default=False
        If True, calls `slot._timeout_handler(timeout=True)` on timeout.
    wait_for_success : bool, default=True
        If True, disconnect only when slot returns True.
        If False, disconnect on first signal emission.

    Example
    -------
        def handle_frame(img, isCurrent):
            if not isCurrent:
                return False
            process(img)
            return True  # stop listening

        OneShotConnection(
            signal=camera.sigFrameReady,
            slot=lambda det, img, init, scale, cur: handle_frame(img, cur),
            timeout_ms=1000,
            notify_timeout=True
        )
    """

    def __init__(self, signal, slot, timeout_ms, parent=None,notify_timeout=False,wait_for_success=True):
        super().__init__(parent)
        self.signal = signal
        self.slot = slot
        self.notify_timeout = notify_timeout
        self.wait_for_success = wait_for_success

        # Slot wrapper
        self._wrapper = self._make_wrapper()
        self.signal.connect(self._wrapper)

        # Timeout timer
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._on_timeout)
        self.timer.start(timeout_ms)

    def _make_wrapper(self):
        def wrapper(*args):
            success = self.slot(*args)
            if (self.wait_for_success and success) or (not self.wait_for_success):
                try:
                    self.signal.disconnect(wrapper)
                except TypeError:
                    pass
                self.timer.stop()
                self.deleteLater()
        return wrapper

    def _on_timeout(self):
        """Timeout fired: disconnect and self-destruct."""
        try:
            self.signal.disconnect(self._wrapper)
        except TypeError:
            pass

        # Notify slot with timeout information if needed
        if self.notify_timeout and hasattr(self.slot, "__call__"):
            try:
                self.slot._timeout_handler(timeout=True)
            except:
                pass
        self.deleteLater()