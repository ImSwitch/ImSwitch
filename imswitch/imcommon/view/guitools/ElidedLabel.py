from qtpy import QtCore, QtWidgets

class ElidedLabel(QtWidgets.QLabel):
    """QLabel that elides long text and exposes the full text as a tooltip."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)

        self._full_text = ""

        self.setMinimumWidth(50)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred,
        )

        self.set_full_text(text)

    def full_text(self) -> str:
        return self._full_text

    def set_full_text(self, text: str) -> None:
        self._full_text = str(text or "")
        self.setToolTip(self._full_text)
        self._update_elision()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_elision()

    def _update_elision(self) -> None:
        width = self.contentsRect().width()

        if width <= 0:
            super().setText(self._full_text)
            return

        text = self.fontMetrics().elidedText(
            self._full_text,
            QtCore.Qt.ElideRight,
            width,
        )
        super().setText(text)