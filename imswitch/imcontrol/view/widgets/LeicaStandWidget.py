from qtpy import QtCore, QtWidgets

from .basewidgets import Widget


class LeicaStandWidget(Widget):
    """Minimal Leica stand control widget."""

    sigModeChanged = QtCore.Signal(str)
    sigCubeChanged = QtCore.Signal(str)
    sigPortSideChanged = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        # Title
        title = QtWidgets.QLabel("Leica DMI8 Control")
        title.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        font = title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 4)
        title.setFont(font)
        title.setContentsMargins(0, 6, 0, 2)

        # Thin separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setMaximumHeight(12)

        # Controls
        self.modeFluoBtn = QtWidgets.QPushButton("FLUO")
        self.modeCSBtn = QtWidgets.QPushButton("CS")
        self.modeFluoBtn.setObjectName("fluoBtn")
        self.modeCSBtn.setObjectName("csBtn")

        self.modeFluoBtn.setCheckable(True)
        self.modeCSBtn.setCheckable(True)

        self.modeButtonGroup = QtWidgets.QButtonGroup(self)
        self.modeButtonGroup.setExclusive(True)
        self.modeButtonGroup.addButton(self.modeFluoBtn)
        self.modeButtonGroup.addButton(self.modeCSBtn)

        self.modeFluoBtn.setChecked(True)

        self.modeFluoBtn.setToolTip("FLUO mode: widefield with LEDs illumination")
        self.modeCSBtn.setToolTip("CS mode: for MoNaLISA imaging")

        self.cubeLabel = QtWidgets.QLabel("Cube:")
        self.cubeCombo = QtWidgets.QComboBox()

        self.portLabel = QtWidgets.QLabel("Port:")
        self.portCombo = QtWidgets.QComboBox()
        self.portCombo.addItems(["Left", "Right"])

        # Sizes
        self.modeFluoBtn.setMinimumHeight(32)
        self.modeCSBtn.setMinimumHeight(32)
        self.modeFluoBtn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.modeCSBtn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.cubeCombo.setMinimumHeight(26)
        self.portCombo.setMinimumHeight(26)
        self.cubeCombo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.portCombo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # Instrument-style combo styling
        controlStyle = """
            QComboBox {
                padding: 2px 8px 2px 6px;
                border-radius: 3px;
            }

            QComboBox::drop-down {
                width: 16px;
                border: none;
            }

            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
            }

            QComboBox:hover {
                border: 1px solid rgba(255,255,255,60);
            }

            QComboBox:focus {
                border: 1px solid rgba(120,180,255,180);
            }
        """
        self.cubeCombo.setStyleSheet(controlStyle)
        self.portCombo.setStyleSheet(controlStyle)

        modeStyle = """
        QPushButton {
            padding: 6px 16px;
            border: 1px solid rgba(255,255,255,60);
        }

        QPushButton#fluoBtn {
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
        }

        QPushButton#csBtn {
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }

        QPushButton:hover {
            border: 1px solid rgba(255,255,255,120);
        }

        QPushButton:checked {
            background-color: rgba(120,180,255,120);
            border: 1px solid rgba(120,180,255,200);
        }
        """
        self.modeFluoBtn.setStyleSheet(modeStyle)
        self.modeCSBtn.setStyleSheet(modeStyle)

        # Mode buttons layout
        modeLayout = QtWidgets.QHBoxLayout()
        modeLayout.setContentsMargins(0, 0, 0, 0)
        modeLayout.setSpacing(0)
        modeLayout.addWidget(self.modeFluoBtn, 1)
        modeLayout.addWidget(self.modeCSBtn, 1)

        modeWidget = QtWidgets.QWidget()
        modeWidget.setLayout(modeLayout)

        # One-line controls row
        controlsLayout = QtWidgets.QGridLayout()
        controlsLayout.setContentsMargins(0, 0, 0, 0)
        controlsLayout.setHorizontalSpacing(6)
        controlsLayout.setVerticalSpacing(0)

        controlsLayout.addWidget(modeWidget, 0, 0)
        controlsLayout.addWidget(self.cubeLabel, 0, 1)
        controlsLayout.addWidget(self.cubeCombo, 0, 2)
        controlsLayout.addWidget(self.portLabel, 0, 3)
        controlsLayout.addWidget(self.portCombo, 0, 4)

        controlsLayout.setColumnStretch(0, 4)  # toggle
        controlsLayout.setColumnStretch(2, 4)  # cube
        controlsLayout.setColumnStretch(4, 2)  # port

        controlsWidget = QtWidgets.QWidget()
        controlsWidget.setLayout(controlsLayout)

        # Root layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.setContentsMargins(6, 6, 6, 6)
        mainLayout.setSpacing(6)

        mainLayout.addWidget(title)
        mainLayout.addWidget(separator)
        mainLayout.addWidget(controlsWidget)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)

        # Important: wide but compact vertically
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.setMaximumHeight(95)

        self.setConnected(False)

    def _connect_signals(self):
        self.modeFluoBtn.clicked.connect(lambda: self.sigModeChanged.emit("FLUO"))
        self.modeCSBtn.clicked.connect(lambda: self.sigModeChanged.emit("CS"))

        self.cubeCombo.currentTextChanged.connect(self.sigCubeChanged)
        self.portCombo.currentTextChanged.connect(self.sigPortSideChanged)

    def setConnected(self, connected):
        self.setEnabled(bool(connected))

    # def setMode(self, mode):
    #     self.modeCombo.blockSignals(True)
    #     idx = self.modeCombo.findText(mode)
    #     if idx >= 0:
    #         self.modeCombo.setCurrentIndex(idx)
    #     self.modeCombo.blockSignals(False)
    def setMode(self, mode):
        self.modeFluoBtn.blockSignals(True)
        self.modeCSBtn.blockSignals(True)

        if mode == "FLUO":
            self.modeFluoBtn.setChecked(True)
        else:
            self.modeCSBtn.setChecked(True)

        self.modeFluoBtn.blockSignals(False)
        self.modeCSBtn.blockSignals(False)

    def setCubeChoices(self, cube_names):
        current = self.cubeCombo.currentText()

        self.cubeCombo.blockSignals(True)
        self.cubeCombo.clear()
        self.cubeCombo.addItems(cube_names)

        idx = self.cubeCombo.findText(current)
        if idx >= 0:
            self.cubeCombo.setCurrentIndex(idx)
        elif self.cubeCombo.count() > 0:
            self.cubeCombo.setCurrentIndex(0)

        self.cubeCombo.blockSignals(False)

    def setCurrentCube(self, cube_name):
        if cube_name is None:
            return

        self.cubeCombo.blockSignals(True)
        idx = self.cubeCombo.findText(cube_name)
        if idx >= 0:
            self.cubeCombo.setCurrentIndex(idx)
        self.cubeCombo.blockSignals(False)

    def setCurrentPortSide(self, side):
        self.portCombo.blockSignals(True)
        idx = self.portCombo.findText(side)
        if idx >= 0:
            self.portCombo.setCurrentIndex(idx)
        self.portCombo.blockSignals(False)
