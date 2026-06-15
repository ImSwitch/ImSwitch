from qtpy import QtCore, QtWidgets

from .basewidgets import Widget


class FlipMirrorWidget(Widget):
    """Widget for controlling binary flip mirrors."""

    sigStateChanged = QtCore.Signal(str, int)
    sigLinkChanged = QtCore.Signal(str, object)  # follower_name, master_name or None
    sigResetConnectionsClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rows = {}
        self._building = False

        self._build_ui()

    def _build_ui(self):
        self._firstDataRow = 1

        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(6, 6, 6, 6)
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(8)

        # Header row
        self.grid.addWidget(QtWidgets.QLabel("Name"), 0, 0, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.grid.addWidget(QtWidgets.QLabel("State"), 0, 1, alignment=QtCore.Qt.AlignCenter)
        self.grid.addWidget(QtWidgets.QLabel("Follow"), 0, 2, alignment=QtCore.Qt.AlignCenter)
        self.grid.addWidget(QtWidgets.QLabel("Master"), 0, 3, alignment=QtCore.Qt.AlignCenter)

        self.resetButton = QtWidgets.QPushButton("Reset")
        self.resetButton.setMinimumHeight(24)
        self.resetButton.setMaximumWidth(140)
        self.resetButton.clicked.connect(self.sigResetConnectionsClicked)

        self.grid.addWidget(self.resetButton, 0, 4, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # Equal column distribution across the full widget width
        # for col in range(5):
        #     self.grid.setColumnStretch(col, 1)
        #     self.grid.setColumnMinimumWidth(col, 60)

        # Column sizing: distribute the table across the full widget width
        self.grid.setColumnStretch(0, 2)  # Name
        self.grid.setColumnStretch(1, 4)  # State
        self.grid.setColumnStretch(2, 1)  # Follow
        self.grid.setColumnStretch(3, 4)  # Master
        self.grid.setColumnStretch(4, 1)  # Status

        self.grid.setColumnMinimumWidth(0, 40)
        self.grid.setColumnMinimumWidth(1, 60)
        self.grid.setColumnMinimumWidth(2, 20)
        self.grid.setColumnMinimumWidth(3, 60)
        self.grid.setColumnMinimumWidth(4, 20)

        rootLayout = QtWidgets.QVBoxLayout()
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.addLayout(self.grid)
        rootLayout.addStretch(1)

        self.setLayout(rootLayout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)

    def addFlipMirror(self, name, state_names=None):
        if name in self.rows:
            return
        
        if state_names is None:
            state_names = {0: "0", 1: "1"}

        state0_text = str(state_names.get(0, state_names.get("0", "0")))
        state1_text = str(state_names.get(1, state_names.get("1", "1")))

        row_index = len(self.rows) + self._firstDataRow

        nameLabel = QtWidgets.QLabel(name)

        state0Btn = QtWidgets.QPushButton(state0_text)
        state1Btn = QtWidgets.QPushButton(state1_text)
        state0Btn.setObjectName("state0Btn")
        state1Btn.setObjectName("state1Btn")
        state0Btn.setCheckable(True)
        state1Btn.setCheckable(True)
        state0Btn.setMinimumWidth(40)
        state1Btn.setMinimumWidth(40)
        state0Btn.setMaximumWidth(80)
        state1Btn.setMaximumWidth(80)
        state0Btn.setMinimumHeight(24)
        state1Btn.setMinimumHeight(24)

        buttonGroup = QtWidgets.QButtonGroup(self)
        buttonGroup.setExclusive(True)
        buttonGroup.addButton(state0Btn)
        buttonGroup.addButton(state1Btn)

        stateStyle = """
        QPushButton {
            padding: 2px 8px;
            border: 1px solid rgba(255,255,255,60);
        }

        QPushButton#state0Btn {
            border-top-left-radius: 5px;
            border-bottom-left-radius: 5px;
        }

        QPushButton#state1Btn {
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
        }

        QPushButton:hover {
            border: 1px solid rgba(255,255,255,120);
        }

        QPushButton:checked {
            background-color: rgba(120,180,255,120);
            border: 1px solid rgba(120,180,255,200);
        }

        QPushButton:disabled {
            color: rgba(255,255,255,70);
            border: 1px solid rgba(255,255,255,25);
        }
        """

        state0Btn.setStyleSheet(stateStyle)
        state1Btn.setStyleSheet(stateStyle)

        stateLayout = QtWidgets.QHBoxLayout()
        stateLayout.setContentsMargins(0, 0, 0, 0)
        stateLayout.setSpacing(0)
        stateLayout.addWidget(state0Btn)
        stateLayout.addWidget(state1Btn)

        stateWidget = QtWidgets.QWidget()
        stateWidget.setLayout(stateLayout)

        followCheck = QtWidgets.QCheckBox()
        masterCombo = QtWidgets.QComboBox()
        masterCombo.setMinimumWidth(60)
        masterCombo.setMaximumWidth(150)

        statusLabel = QtWidgets.QLabel("—")
        statusLabel.setMinimumWidth(20)

        self.grid.addWidget(nameLabel, row_index, 0, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.grid.addWidget(stateWidget, row_index, 1, alignment=QtCore.Qt.AlignCenter)
        self.grid.addWidget(followCheck, row_index, 2, alignment=QtCore.Qt.AlignCenter)
        self.grid.addWidget(masterCombo, row_index, 3, alignment=QtCore.Qt.AlignCenter)
        self.grid.addWidget(statusLabel, row_index, 4, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.rows[name] = {
            "nameLabel": nameLabel,
            "state0Btn": state0Btn,
            "state1Btn": state1Btn,
            "buttonGroup": buttonGroup,
            "stateWidget": stateWidget,
            "followCheck": followCheck,
            "masterCombo": masterCombo,
            "statusLabel": statusLabel,
        }

        state0Btn.clicked.connect(lambda checked=False, n=name: self.sigStateChanged.emit(n, 0))
        state1Btn.clicked.connect(lambda checked=False, n=name: self.sigStateChanged.emit(n, 1))

        followCheck.toggled.connect(lambda checked, n=name: self._onFollowToggled(n, checked))
        masterCombo.currentTextChanged.connect(lambda text, n=name: self._onMasterChanged(n, text))

    def _onFollowToggled(self, name, checked):
        if self._building:
            return

        row = self.rows[name]
        combo = row["masterCombo"]

        if checked:
            master = combo.currentText()

            # If no master is selected yet, auto-select the first available one.
            if master == "—":
                for i in range(combo.count()):
                    candidate = combo.itemText(i)
                    if candidate != "—":
                        combo.setCurrentIndex(i)
                        master = candidate
                        break

            # Still no valid master: revert checkbox.
            if master == "—":
                row["followCheck"].blockSignals(True)
                row["followCheck"].setChecked(False)
                row["followCheck"].blockSignals(False)
                return

            self.sigLinkChanged.emit(name, master)

        else:
            self.sigLinkChanged.emit(name, None)

    def _onMasterChanged(self, name, master):
        if self._building:
            return

        row = self.rows[name]
        if row["followCheck"].isChecked() and master != "—":
            self.sigLinkChanged.emit(name, master)

    def setState(self, name, state):
        if name not in self.rows:
            return

        row = self.rows[name]
        row["state0Btn"].blockSignals(True)
        row["state1Btn"].blockSignals(True)

        row["state0Btn"].setChecked(int(state) == 0)
        row["state1Btn"].setChecked(int(state) == 1)

        row["state0Btn"].blockSignals(False)
        row["state1Btn"].blockSignals(False)

    def setMasterChoices(self, name, choices, current_master=None):
        if name not in self.rows:
            return

        row = self.rows[name]
        combo = row["masterCombo"]

        self._building = True
        combo.blockSignals(True)

        combo.clear()
        combo.addItem("—")
        combo.addItems(list(choices))

        if current_master is not None:
            idx = combo.findText(current_master)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                combo.setCurrentIndex(0)
        else:
            combo.setCurrentIndex(0)

        combo.blockSignals(False)
        self._building = False

    def setLink(self, name, master_name):
        if name not in self.rows:
            return

        row = self.rows[name]

        self._building = True

        row["followCheck"].blockSignals(True)
        row["masterCombo"].blockSignals(True)

        is_linked = master_name is not None
        row["followCheck"].setChecked(is_linked)

        if is_linked:
            idx = row["masterCombo"].findText(master_name)
            if idx >= 0:
                row["masterCombo"].setCurrentIndex(idx)
        else:
            idx = row["masterCombo"].findText("—")
            if idx >= 0:
                row["masterCombo"].setCurrentIndex(idx)

        row["masterCombo"].setEnabled(is_linked)

        row["followCheck"].blockSignals(False)
        row["masterCombo"].blockSignals(False)

        self._building = False

    def setRowState(self, name, *, connected=True, state_enabled=True,
                link_enabled=True, status_text="OK"):
        if name not in self.rows:
            return

        row = self.rows[name]

        row["state0Btn"].setEnabled(bool(connected and state_enabled))
        row["state1Btn"].setEnabled(bool(connected and state_enabled))

        row["followCheck"].setEnabled(bool(connected and link_enabled))

        # Keep combo enabled whenever linking is allowed.
        # This lets the user select the master before checking Follow.
        row["masterCombo"].setEnabled(bool(connected and link_enabled))

        row["statusLabel"].setText(status_text)

    def setAllEnabled(self, enabled):
        for name in self.rows:
            self.setRowState(
                name,
                connected=enabled,
                state_enabled=enabled,
                link_enabled=enabled,
                status_text="OK" if enabled else "Disabled",
            )