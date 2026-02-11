
from qtpy import QtCore, QtWidgets


class InfoButton(QtWidgets.QToolButton):
    """ Info button that displays pop up text when mouse hovering on button. """

    def __init__(self, parent=None, size=None):
        super().__init__(parent)
        if not size:
            size = (18,18)
            
        self._text = ""

        self.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation))
        self.setAutoRaise(True)
        self.setFixedSize(*size) 
        self.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
            }
            QToolButton:hover {
                background: transparent;
            }
        """)

        self.popup = QtWidgets.QFrame(None, QtCore.Qt.ToolTip)
        self.popup.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        layout = QtWidgets.QVBoxLayout(self.popup)
        layout.setContentsMargins(3, 3, 3, 3)

        self.label = QtWidgets.QLabel()
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        self.popup.hide()

    def setTextInfo(self, text):
        self._text = text or ""

    def enterEvent(self, event):
        if not self._text:
            return

        self.label.setText(self._text)
        self.popup.adjustSize()

        pos = self.mapToGlobal(QtCore.QPoint(0, self.height()))
        screen = QtWidgets.QApplication.screenAt(pos)
        geom = screen.geometry() if screen else QtWidgets.QApplication.primaryScreen().geometry()

        x, y = pos.x(), pos.y()

        if x + self.popup.width() > geom.right():
            x = geom.right() - self.popup.width() - 5
        if y + self.popup.height() > geom.bottom():
            y = pos.y() - self.popup.height() - self.height()

        self.popup.move(x, y)
        self.popup.show()

    def leaveEvent(self, event):
        self.popup.hide()