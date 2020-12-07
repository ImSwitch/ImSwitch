from pyqtgraph.Qt import QtGui


class BetterPushButton(QtGui.QPushButton):
    """BetterPushButton is a QPushButton that does not become too small when
    styled."""

    def __init__(self, text, minMinWidth=20, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self._minMinWidth = minMinWidth
        self.updateMinWidth(text)

    def setText(self, text, *args, **kwargs):
        super().setText(text, *args, **kwargs)
        self.updateMinWidth(text)

    def updateMinWidth(self, text=None):
        if text is None:
            text = self.text()

        fontMetrics = QtGui.QFontMetrics(self.font())
        textWidth = fontMetrics.width(text)
        minWidth = max(self._minMinWidth, textWidth + 8)
        self.setStyleSheet(f'min-width: {minWidth}px')
