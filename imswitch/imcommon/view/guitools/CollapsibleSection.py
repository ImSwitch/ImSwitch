from qtpy import QtCore, QtWidgets

class CollapsibleSection(QtWidgets.QWidget):
    def __init__(self, title="", parent=None,target_height=None,frame=True,
                 button_height = None, button_width = None, fontsize = 10):
        super().__init__(parent)

        # Toggle button
        self.toggleButton = QtWidgets.QToolButton(text=title, checkable=True, checked=False)

        if button_height:
            self.toggleButton.setFixedHeight(button_height)
        if button_width:
            self.toggleButton.setFixedWidth(button_width)

        self.toggleButton.setStyleSheet(f"""
                QToolButton {{
                    border: none;
                    font-size: {fontsize}px;
                    padding: 1px 1px;
                }}
            """)
        self.toggleButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(QtCore.Qt.RightArrow)
        self.toggleButton.clicked.connect(self._on_pressed)

        # Scroll area for content
        self.contentArea = QtWidgets.QScrollArea()
        self.contentArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.contentArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.contentArea.setWidgetResizable(True)
        self.contentArea.setMaximumHeight(0)  # start collapsed
        if not frame:
            self.contentArea.setStyleSheet("QScrollArea { border: none; }")

        # Main layout
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        # header layout as QHBoxLayout so that more widgets can be added next to the toggle button
        self.headerLayout = QtWidgets.QHBoxLayout()
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.setSpacing(2)
        self.headerLayout.addWidget(self.toggleButton)
        self.headerLayout.addStretch()  # push extra widgets to the right

        mainLayout.addLayout(self.headerLayout)
        mainLayout.addWidget(self.contentArea)

        # Animation for expand/collapse
        self.toggleAnimation = QtCore.QPropertyAnimation(self.contentArea, b"maximumHeight")
        self.toggleAnimation.setDuration(50)

        # Section size policy
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self.target_height = target_height

    def setContentLayout(self, contentLayout):
        """Set the inner layout for the collapsible section."""
        self.contentWidget = QtWidgets.QWidget()
        self.contentWidget.setLayout(contentLayout)
        self.contentWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.contentArea.setWidget(self.contentWidget)

    def addHeaderWidget(self, widget,position=None):
        """Add a widget to the right side of the section header."""
        if position is None:
            position = self.headerLayout.count()-1
        self.headerLayout.insertWidget(position, widget)

    def _on_pressed(self):
        checked = self.toggleButton.isChecked()
        self.toggleButton.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)
        self._expanded = checked

        # Recompute layout before reading sizeHint
        if self.contentWidget.layout():
            self.contentWidget.layout().activate()
        self.contentWidget.updateGeometry()

        if checked:
            if self.target_height is None:
                target_height = self.contentWidget.layout().sizeHint().height() 
            else:
                target_height = self.target_height 
        else:
            target_height = 0

        # Animate
        self.toggleAnimation.stop()
        start_val = self.contentArea.maximumHeight()
        self.toggleAnimation.setStartValue(start_val)
        self.toggleAnimation.setEndValue(target_height)
        self.toggleAnimation.start()
