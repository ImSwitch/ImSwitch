from qtpy import QtCore,QtWidgets

class CollapsibleSection(QtWidgets.QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)

        self.toggleButton = QtWidgets.QToolButton(text=title, checkable=True, checked=False)
        self.toggleButton.setStyleSheet("""
            QToolButton {
                border: none;
                font-size: 9px;
                padding: 2px 2px;
            }
        """)
        self.toggleButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(QtCore.Qt.RightArrow)
        self.toggleButton.clicked.connect(self._on_pressed)

        self.headerLine = QtWidgets.QFrame()
        self.headerLine.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.headerLine.setVisible(False)

        self.contentArea = QtWidgets.QScrollArea(maximumHeight=0, minimumHeight=0)
        self.contentArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.contentArea.setFrameShape(QtWidgets.QFrame.NoFrame)

        # Main layout
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addWidget(self.toggleButton)
        mainLayout.addWidget(self.headerLine)
        mainLayout.addWidget(self.contentArea)

        self.toggleAnimation = QtCore.QParallelAnimationGroup(self)
        self.contentArea.setMaximumHeight(0)
        self.toggleAnimation.addAnimation(QtCore.QPropertyAnimation(self.contentArea, b"maximumHeight"))
        self.toggleAnimation.addAnimation(QtCore.QPropertyAnimation(self, b"minimumHeight"))
        self.toggleAnimation.addAnimation(QtCore.QPropertyAnimation(self, b"maximumHeight"))

    def setContentLayout(self, contentLayout):
        """Set the inner layout."""
        self.contentWidget = QtWidgets.QWidget()
        self.contentWidget.setLayout(contentLayout)
        self.contentWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self.contentArea.setWidget(self.contentWidget)
        self.contentArea.setWidgetResizable(True)
        self.contentArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
        contentHeight = contentLayout.sizeHint().height()

        for i in range(self.toggleAnimation.animationCount()):
            animation = self.toggleAnimation.animationAt(i)
            animation.setDuration(150)
            animation.setStartValue(collapsedHeight)
            animation.setEndValue(collapsedHeight + contentHeight)

    def _on_pressed(self):
        checked = self.toggleButton.isChecked()
        self.toggleButton.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)

        # Hide or show the separator line depending on collapse state
        self.headerLine.setVisible(checked)

        if checked:
            self.contentArea.setMaximumHeight(self.contentWidget.sizeHint().height())
        else:
            self.contentArea.setMaximumHeight(0)
