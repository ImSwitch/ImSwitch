from qtpy import QtCore, QtWidgets, QtGui
from imswitch.imcontrol.view.guitools import CollapsibleSection
from .basewidgets import Widget


class SLMgridsWidget(Widget):
    """Widget containing SLM interface, patterns, and CGH controls."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setSpacing(15)

        # top_controls and image display
        self._create_top_controls(self.mainLayout)
        self._create_image_display(self.mainLayout)

        # Placeholder for the tabbed (or single) pattern section
        self.tabContainer = QtWidgets.QWidget()
        self.tabLayout = QtWidgets.QVBoxLayout(self.tabContainer)
        self.tabLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.tabContainer)

        # Update Pattern controls
        self._create_update_section(self.mainLayout)

        self.setLayout(self.mainLayout)

    # TOP CONTROLS
    def _create_top_controls(self, parent_layout):
        self.connectBtn = QtWidgets.QPushButton("Connect to SLM")
        self.connectBtn.setCheckable(True)
        self.connectBtn.setMinimumHeight(28)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.connectBtn)
        layout.addStretch()
        parent_layout.addLayout(layout)

    # IMAGE DISPLAY
    def _create_image_display(self, parent_layout):
        self.imageFrame = QtWidgets.QLabel("SLM Display Preview")
        self.imageFrame.setAlignment(QtCore.Qt.AlignCenter)
        self.imageFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.imageFrame.setMinimumSize(300, 200)
        self.imageFrame.setStyleSheet("""
            background-color: #222;
            border: 1px solid #555;
            color: #aaa;
            font-size: 14px;
        """)
        parent_layout.addWidget(self.imageFrame, stretch=1)

    # DYNAMIC TAB / SINGLE BUILDING
    def build_tab_section(self, n_tabs=1, tab_names=None):
        """
        Called by the controller to build the tabs or single layout dynamically.
        n_tabs: int
        tab_names: list of str (optional)
        """
        # Clear existing layout
        for i in reversed(range(self.tabLayout.count())):
            widget = self.tabLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Default tab names if not provided
        if tab_names is None:
            tab_names = [f"SLM {i+1}" for i in range(n_tabs)]

        # SINGLE TAB 
        if n_tabs == 1:
            section = self._create_slm_section(prefix="SLM1")
            self.tabLayout.addWidget(section)
            return

        # MULTIPLE TABS
        tabWidget = QtWidgets.QTabWidget()
        tabWidget.setTabPosition(QtWidgets.QTabWidget.North)
        tabWidget.setStyleSheet("QTabWidget::pane { border: 1px solid #666; }")

        for idx, name in enumerate(tab_names):
            prefix = f"SLM{idx+1}"
            section = self._create_slm_section(prefix=prefix)
            tabWidget.addTab(section, name)

        self.tabLayout.addWidget(tabWidget)
        self.tabWidget = tabWidget  # optional reference

    # SINGLE TAB CONTENT
    def _create_slm_section(self, prefix="SLM"):
        """
        Create one complete SLM section (with wavelength + patterns + CGH)
        """
        container = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(container)

        # Wavelength controls
        wl_layout = QtWidgets.QHBoxLayout()
        wl_label = QtWidgets.QLabel("Wavelength (nm):")
        setattr(self, f"{prefix}_wavelength", QtWidgets.QLineEdit("488"))
        getattr(self, f"{prefix}_wavelength").setFixedWidth(80)
        wl_layout.addWidget(wl_label)
        wl_layout.addWidget(getattr(self, f"{prefix}_wavelength"))
        wl_layout.addStretch()
        vbox.addLayout(wl_layout)

        # Add pattern and CGH collapsible sections
        vbox.addWidget(self._create_patterns_group(prefix))
        vbox.addWidget(self._create_cgh_group(prefix))
        vbox.addStretch()

        return container

    # PATTERNS SECTION
    def _create_patterns_group(self, prefix=""):
        group = CollapsibleSection("Patterns")
        layout = QtWidgets.QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        row = 0

        # ---- Binary Grating ----
        setattr(self, f"{prefix}_binary_check", QtWidgets.QCheckBox("Binary Grating"))
        bx = QtWidgets.QLineEdit("0")
        by = QtWidgets.QLineEdit("0")
        dx = QtWidgets.QLineEdit("0.5")
        dy = QtWidgets.QLineEdit("0.5")
        for w in [bx, by, dx, dy]: w.setFixedWidth(60)
        setattr(self, f"{prefix}_binary_periodx", bx)
        setattr(self, f"{prefix}_binary_periody", by)
        setattr(self, f"{prefix}_binary_dutyx", dx)
        setattr(self, f"{prefix}_binary_dutyy", dy)

        layout.addWidget(getattr(self, f"{prefix}_binary_check"), row, 0)
        layout.addWidget(QtWidgets.QLabel("Period:"), row, 1)
        layout.addWidget(QtWidgets.QLabel("X"), row, 2)
        layout.addWidget(bx, row, 3)
        layout.addWidget(QtWidgets.QLabel("Y"), row, 4)
        layout.addWidget(by, row, 5)
        layout.addWidget(QtWidgets.QLabel("Duty cycle:"), row, 6)
        layout.addWidget(QtWidgets.QLabel("X"), row, 7)
        layout.addWidget(dx, row, 8)
        layout.addWidget(QtWidgets.QLabel("Y"), row, 9)
        layout.addWidget(dy, row, 10)
        row += 1

        # ---- Sinusoidal Grating ----
        setattr(self, f"{prefix}_sin_check", QtWidgets.QCheckBox("Sinusoidal Grating"))
        sx = QtWidgets.QLineEdit("0")
        sy = QtWidgets.QLineEdit("0")
        px = QtWidgets.QLineEdit("1")
        py = QtWidgets.QLineEdit("1")
        for w in [sx, sy, px, py]: w.setFixedWidth(60)
        setattr(self, f"{prefix}_sin_periodx", sx)
        setattr(self, f"{prefix}_sin_periody", sy)
        setattr(self, f"{prefix}_sin_powerx", px)
        setattr(self, f"{prefix}_sin_powery", py)

        layout.addWidget(getattr(self, f"{prefix}_sin_check"), row, 0)
        layout.addWidget(QtWidgets.QLabel("Period:"), row, 1)
        layout.addWidget(QtWidgets.QLabel("X"), row, 2)
        layout.addWidget(sx, row, 3)
        layout.addWidget(QtWidgets.QLabel("Y"), row, 4)
        layout.addWidget(sy, row, 5)
        layout.addWidget(QtWidgets.QLabel("Power (sinⁿ):"), row, 6)
        layout.addWidget(QtWidgets.QLabel("X"), row, 7)
        layout.addWidget(px, row, 8)
        layout.addWidget(QtWidgets.QLabel("Y"), row, 9)
        layout.addWidget(py, row, 10)
        row += 1

        # ---- Linear Phase ----
        setattr(self, f"{prefix}_linear_check", QtWidgets.QCheckBox("Linear Phase"))
        lx = QtWidgets.QLineEdit("0")
        ly = QtWidgets.QLineEdit("0")
        for w in [lx, ly]: w.setFixedWidth(60)
        setattr(self, f"{prefix}_linear_periodx", lx)
        setattr(self, f"{prefix}_linear_periody", ly)

        layout.addWidget(getattr(self, f"{prefix}_linear_check"), row, 0)
        layout.addWidget(QtWidgets.QLabel("Period:"), row, 1)
        layout.addWidget(QtWidgets.QLabel("X"), row, 2)
        layout.addWidget(lx, row, 3)
        layout.addWidget(QtWidgets.QLabel("Y"), row, 4)
        layout.addWidget(ly, row, 5)

        group.setContentLayout(layout)
        return group

    # CGH SECTION
    def _create_cgh_group(self, prefix=""):
        group = CollapsibleSection("CGH")
        cghLayout = QtWidgets.QVBoxLayout()

        # --- First row: Use CGH + Target Type ---
        typeLayout = QtWidgets.QHBoxLayout()
        setattr(self, f"{prefix}_use_cgh", QtWidgets.QCheckBox("Use CGH"))
        typeLayout.addWidget(getattr(self, f"{prefix}_use_cgh"))
        typeLayout.addWidget(QtWidgets.QLabel("Target Type:"))
        combo = QtWidgets.QComboBox()
        combo.addItems(["BFP spots", "Multi-Foci"])
        setattr(self, f"{prefix}_target_type", combo)
        typeLayout.addWidget(combo)
        typeLayout.addStretch()
        cghLayout.addLayout(typeLayout)

        # --- Stack for parameter sets ---
        stack = QtWidgets.QStackedWidget()
        setattr(self, f"{prefix}_cghParamStack", stack)
        # self.cghParamStack = QtWidgets.QStackedWidget()

        # ---- BFP Spots ----
        bfpWidget = QtWidgets.QWidget()
        bfpLayout = QtWidgets.QGridLayout(bfpWidget)
        dir_combo = QtWidgets.QComboBox()
        dir_combo.addItems(["X", "Y"])
        bfpLayout.addWidget(QtWidgets.QLabel("Direction:"), 0, 0)
        bfpLayout.addWidget(dir_combo, 0, 1)
        setattr(self, f"{prefix}_bfp_direction", dir_combo)

        names = ["Target size","Spot distance", "Offset", "Spot1 Intensity", "Spot2 Intensity"]
        defaults = ["512","10", "0", "1.0", "1.0"]
        for i, (name, val) in enumerate(zip(names, defaults), start=0):
            field = QtWidgets.QLineEdit(val)
            field.setFixedWidth(60)
            setattr(self, f"{prefix}_bfp_{name.lower().replace(' ', '_')}", field)
            bfpLayout.addWidget(QtWidgets.QLabel(name + ":"), i // 3, 2 * (i % 3) + 2)
            bfpLayout.addWidget(field, i // 3, 2 * (i % 3) + 3)
        stack.addWidget(bfpWidget)
        # self.cghParamStack.addWidget(bfpWidget)

        # ---- Multi-Foci ----
        multiWidget = QtWidgets.QWidget()
        multiLayout = QtWidgets.QGridLayout(multiWidget)
        names = ["Target size X", "Target size Y","# foci", "Period", ]
        defaults = ["512", "512","3", "10"]
        for i, (name, val) in enumerate(zip(names, defaults)):
            field = QtWidgets.QLineEdit(val)
            field.setFixedWidth(60)
            setattr(self, f"{prefix}_multi_{name.lower().replace(' ', '_').replace('#', 'num')}", field)
            multiLayout.addWidget(QtWidgets.QLabel(name + ":"), 0, 2 * i)
            multiLayout.addWidget(field, 0, 2 * i + 1)

        # self.cghParamStack.addWidget(multiWidget)
        # cghLayout.addWidget(self.cghParamStack)

        stack.addWidget(multiWidget)
        cghLayout.addWidget(stack)

        # --- Compute CGH Section ---
        computeLayout = QtWidgets.QHBoxLayout()
        setattr(self, f"{prefix}_compute_cgh_btn", QtWidgets.QPushButton("Compute CGH"))
        setattr(self, f"{prefix}_weighted_gs", QtWidgets.QCheckBox("Weighted-GS"))
        setattr(self, f"{prefix}_iterations", QtWidgets.QLineEdit("20"))
        getattr(self, f"{prefix}_iterations").setFixedWidth(50)
        setattr(self, f"{prefix}_phase_fixing", QtWidgets.QCheckBox("Phase fixing"))
        setattr(self, f"{prefix}_phase_value", QtWidgets.QLineEdit("0"))
        getattr(self, f"{prefix}_phase_value").setFixedWidth(50)

        computeLayout.addWidget(getattr(self, f"{prefix}_compute_cgh_btn"))
        computeLayout.addWidget(getattr(self, f"{prefix}_weighted_gs"))
        computeLayout.addWidget(QtWidgets.QLabel("Iterations:"))
        computeLayout.addWidget(getattr(self, f"{prefix}_iterations"))
        computeLayout.addWidget(getattr(self, f"{prefix}_phase_fixing"))
        computeLayout.addWidget(getattr(self, f"{prefix}_phase_value"))
        computeLayout.addStretch()
        cghLayout.addLayout(computeLayout)

        # combo logic
        combo.currentIndexChanged.connect(lambda idx: stack.setCurrentIndex(idx))

        group.setContentLayout(cghLayout)
        return group

    # UPDATE SLM PATTERN SECTION
    def _create_update_section(self, parent_layout):
        layout = QtWidgets.QHBoxLayout()
        self.applyCorrectionCheck = QtWidgets.QCheckBox("Apply correction pattern")
        self.applyCorrectionCheck.setChecked(True)
        self.maxValueCheck = QtWidgets.QCheckBox("Max value correction")
        self.maxValueCheck.setChecked(True)
        self.updatePatternBtn = QtWidgets.QPushButton("Update SLM Pattern")
        self.updatePatternBtn.setMinimumHeight(32)
        self.updatePatternBtn.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.applyCorrectionCheck)
        layout.addWidget(self.maxValueCheck)
        layout.addStretch()
        layout.addWidget(self.updatePatternBtn)
        parent_layout.addLayout(layout)
