from qtpy import QtCore, QtWidgets, QtGui
from imswitch.imcontrol.view.guitools import CollapsibleSection, BetterPushButton
from .basewidgets import Widget
from imswitch.imcommon.model import initLogger
import re
import json

class SLMsWidget(Widget):
    """Widget containing SLM interface, patterns, and CGH controls."""

    sigConnectSLMusb = QtCore.Signal(str,bool) # slmName, state
    sigUpdatePattern = QtCore.Signal(str, dict)  # slm_key, params
    sigComputeCGH = QtCore.Signal(str, dict)     # slm_key, cgh_params


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.slmTabs = QtWidgets.QTabWidget()
        self.slmTabs.setTabPosition(QtWidgets.QTabWidget.North)
        self.slmTabs.setMovable(True)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.slmTabs)
        self.setLayout(layout)

        self._slmNames = {} #{slm_key: slmName}
        self._slm_widgets = {}  # store by slm_key
        self._slmInfos = {} # store by slm_key
        self._tab_names_dict={} # {slm_key: {tab_key: tab_name}} 
        self._param_definitions = {} # list of parameters stored by slm_key[tabKey][sectionName]

    def addSlm(self,slmName,slmInfo,*args,**kwargs):
        slmWidget = QtWidgets.QWidget()
        slmLayout = QtWidgets.QVBoxLayout(self)
        slmLayout.setSpacing(15)
        
        # slm_key is the cleaned slmName used for referencing and setting attributes
        # original slmName kept for display

        slm_key = cleanAttrName(slmName) 
        self._slmNames[slm_key] = slmName
        self._slmInfos[slm_key] = slmInfo
        self._param_definitions[slm_key] = {}
        self._tab_names_dict[slm_key] = {}

        self.createTopControls(slmLayout,slm_key=slm_key)
        self.createImageDisplay(slmLayout,slm_key=slm_key)
        
        self.buildTabSection(slmLayout,slm_key=slm_key,n_tabs=slmInfo.nSections,
                                 tab_names=slmInfo.sectionsNames,options=slmInfo.widgetOptions)
        
        self.createUpdateSection(slmLayout,slm_key=slm_key)

        slmWidget.setLayout(slmLayout)
        self.slmTabs.addTab(slmWidget,slmName) #here we give the original slmName to be displayed
        self._slm_widgets[slm_key] = slmWidget

        return slm_key
        
    # top controls
    def createTopControls(self, parent_layout, slm_key="slm"):
        """
        Create the top control row for a single SLM: Connect button + Save/Load buttons.
        """
        layout = QtWidgets.QHBoxLayout()

        # Connect button
        connectBtn = BetterPushButton("Connect to SLM")
        connectBtn.setCheckable(True)
        connectBtn.setMinimumHeight(28)
        setattr(self, f"{slm_key}_connectBtn", connectBtn)
        layout.addWidget(connectBtn)

        layout.addStretch()
        # Save / Load buttons
        saveConfigBtn = BetterPushButton("Save Config")
        loadConfigBtn = BetterPushButton("Load Config")
        setattr(self, f"{slm_key}_saveConfigBtn", saveConfigBtn)
        setattr(self, f"{slm_key}_loadConfigBtn", loadConfigBtn)
        layout.addWidget(saveConfigBtn)
        layout.addWidget(loadConfigBtn)

        parent_layout.addLayout(layout)

        # signal connections
        connectBtn.toggled.connect(lambda state, p=slm_key: self.sigConnectSLMusb.emit(p, state))

    # image display
    def createImageDisplay(self, parent_layout, slm_key="slm"):
        """
        Create the SLM display preview inside a collapsible section.
        """
        # Create the collapsible section
        imageSection = CollapsibleSection("SLM Preview")
        setattr(self, f"{slm_key}_imageSection", imageSection)  # store per SLM

        # Create the image label
        imageFrame = QtWidgets.QLabel("SLM Display Preview")
        imageFrame.setAlignment(QtCore.Qt.AlignCenter)
        imageFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        imageFrame.setMinimumSize(300, 200)
        imageFrame.setStyleSheet("""
            background-color: #222;
            border: 1px solid #555;
            color: #aaa;
            font-size: 14px;
        """)
        setattr(self, f"{slm_key}_imageFrame", imageFrame)  # store per SLM

        # Layout for the collapsible content
        imageLayout = QtWidgets.QVBoxLayout()
        imageLayout.setContentsMargins(0, 0, 0, 0)
        imageLayout.addWidget(imageFrame, stretch=1)

        # Assign layout to the collapsible section
        imageSection.setContentLayout(imageLayout)

        # Add the collapsible section to the parent layout
        parent_layout.addWidget(imageSection)

    def buildTabSection(self, parent_layout, slm_key="slm", n_tabs=1, tab_names=None,options={}):
        """
        Create N sub-tabs (e.g. for double-pass left/right).
        If N == 1, just builds the single SLM section directly.
        """
        if n_tabs is None:
            n_tabs == 1
            tab_names = ["Full SLM"]

        elif not tab_names:
            tab_names = [f"Section {i+1}" for i in range(n_tabs)]
        
        subTabs = QtWidgets.QTabWidget()
        for i,name in enumerate(tab_names):
            tab_key = f"tab{i}"
            self._tab_names_dict[slm_key][tab_key] = name
            section_widget = self.createSlmSection(slm_key,tab_key,options)
            subTabs.addTab(section_widget, name)
        
        # Allow user to rename tabs
        subTabs.tabBarDoubleClicked.connect(lambda index: self.renameTab(slm_key,subTabs, index))

        parent_layout.addWidget(subTabs)
    
    def createSlmSection(self, slm_key="slm",tab_key="tab0",options={}):
        """
        Create one complete SLM section.
        """
        self._param_definitions[slm_key][tab_key]={}

        container = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(container)

        # General
        self._param_definitions[slm_key][tab_key]["general"]=[]
        vbox.addWidget(self.createGeneralGroup(slm_key,tab_key))

        # Patterns
        self._param_definitions[slm_key][tab_key]["patterns"]=[]
        vbox.addWidget(self.createPatternsGroup(slm_key,tab_key,options.get("patterns")))

        # CGH
        if options.get("cgh",True):
            self._param_definitions[slm_key][tab_key]["cgh"]=[]
            vbox.addWidget(self.createCghGroup(slm_key,tab_key))

        # aberration correction
        if options.get("aberration",True):
            self._param_definitions[slm_key][tab_key]["aberration"]=[]
            vbox.addWidget(self.createAberrationGroup(slm_key,tab_key))

        vbox.addStretch()

        return container
    
    # General section
    def createGeneralGroup(self,slm_key="slm",tab_key="tab0"):
        group = CollapsibleSection("General")
        layout = QtWidgets.QGridLayout()
        params = [
            ('lineedit','Wavelength (nm)','488'),
            ('lineedit','Pupil Radius (px)', 0),
            ('lineedit','Center Offset X (px)', 0),
            ('lineedit','Center Offset Y (px)', 0),
        ]
        self.addParamGrid(slm_key, tab_key,"general",params, 0, layout, per_row=1,attr_prefix=None)
        group.setContentLayout(layout)
        return group

    # Patterns section
    def createPatternsGroup(self, slm_key="slm",tab_key="tab0", options=None):
        """
        Create the Patterns group with collapsible section.
        options: list of patterns to include, e.g. ["binary_grating", "sinusoidal_grating"]
        """
        if options is None:
            self.__logger.warning("No patterns options, using default settings")
            options = ["binary_grating", "linear_phase", "lens_phase"]

        group = CollapsibleSection("Patterns")
        layout = QtWidgets.QGridLayout()

        row = 0
        for pattern in options:
            builder = getattr(self, f"add{pattern}", None)
            if builder is not None:
                row = builder(layout, row, slm_key, tab_key)
            else:
                self.__logger.warning(f"Pattern '{pattern}' is requested but not implemented.")

        group.setContentLayout(layout)
        return group

    # Aberrations section
    def createAberrationGroup(self, slm_key="slm",tab_key="tab0"):
        group = CollapsibleSection("Aberrations")
        layout = QtWidgets.QGridLayout()
        row = 0
        # --- Load aberrations buttons ---
        setattr(self, f"{slm_key}_{tab_key}_load_aberrations_btn", BetterPushButton("Load"))
        setattr(self, f"{slm_key}_{tab_key}_load_aberrations_label", QtWidgets.QLabel("Loaded: None"))
        getattr(self, f"{slm_key}_{tab_key}_load_aberrations_label").setStyleSheet("color: #888;")
        layout.addWidget(getattr(self, f"{slm_key}_{tab_key}_load_aberrations_btn"), row, 0)
        layout.addWidget(getattr(self, f"{slm_key}_{tab_key}_load_aberrations_label"), row, 1)
        row += 1
        spacer = QtWidgets.QSpacerItem(0, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        layout.addItem(spacer, row, 0, 1, 2)
        row += 1
        
        # --- Column headers ---
        header_font = QtGui.QFont()
        header_font.setBold(True)

        lbl_aberr = QtWidgets.QLabel("Aberration")
        lbl_aberr.setFont(header_font)
        lbl_coeff = QtWidgets.QLabel("Coefficient (λ)")
        lbl_coeff.setFont(header_font)

        layout.addWidget(lbl_aberr, row, 0)
        layout.addWidget(lbl_coeff, row, 1)
        row += 1

        # --- Parameter rows ---
        params = [
            ('lineedit','Tilt',0),
            ('lineedit','Tip', 0),
            ('lineedit','Defocus', 0),
            ('lineedit','Spherical', 0),
            ('lineedit','Horizontal Coma', 0),
            ('lineedit','Vertical Coma', 0),
            ('lineedit','Horizontal Astigmatism',0),
            ('lineedit','Vertical Astigmatism',0)
        ]
        row = self.addParamGrid(slm_key, tab_key, "aberration", params, row, layout, per_row=1,attr_prefix=None)
        layout.addItem(spacer,row,0,1,2)
        row += 1

        # --- Save button ---
        setattr(self, f"{slm_key}_save_aberrations_btn", BetterPushButton("Save"))
        layout.addWidget(getattr(self, f"{slm_key}_save_aberrations_btn"), row, 0, 1, 1)

        group.setContentLayout(layout)
        return group


    # CGH patterns section
    def createCghGroup(self, slm_key="slm",tab_key="tab0"):
        group = CollapsibleSection("CGH Pattern")
        cghLayout = QtWidgets.QVBoxLayout()
        cghLayout.setSpacing(12)

        # --- 1. General Controls ---
        generalLayout = QtWidgets.QHBoxLayout()
        setattr(self, f"{slm_key}_use_cgh", QtWidgets.QCheckBox("Use CGH"))
        setattr(self, f"{slm_key}_{tab_key}_cgh_load_btn", BetterPushButton("Load Pattern"))
        setattr(self, f"{slm_key}_{tab_key}_cgh_loaded_label", QtWidgets.QLabel("Loaded: None"))
        getattr(self, f"{slm_key}_{tab_key}_cgh_loaded_label").setStyleSheet("color: #888;")

        generalLayout.addWidget(getattr(self, f"{slm_key}_use_cgh"))
        generalLayout.addStretch()
        generalLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_load_btn"))
        generalLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_loaded_label"))
        cghLayout.addLayout(generalLayout)
        
        self._param_definitions[slm_key][tab_key]["cgh"].append(
            ("checkbox","use_cgh",False, "use_cgh")
        )

        # --- 2. Target Source Controls ---
        targetSourceBox = QtWidgets.QGroupBox("Target Source")
        
        targetSourceLayout = QtWidgets.QVBoxLayout(targetSourceBox)
        targetSourceLayout.setSpacing(4)

        # row 1: load target + label
        loadTargetLayout = QtWidgets.QHBoxLayout()
        setattr(self, f"{slm_key}_{tab_key}_cgh_load_target_btn", BetterPushButton("Load Target"))
        setattr(self, f"{slm_key}_{tab_key}_cgh_loaded_target_label", QtWidgets.QLabel("Loaded: None"))
        getattr(self, f"{slm_key}_{tab_key}_cgh_loaded_target_label").setStyleSheet("color: #888;")

        loadTargetLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_load_target_btn"))
        loadTargetLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_loaded_target_label"))
        loadTargetLayout.addStretch()
        targetSourceLayout.addLayout(loadTargetLayout)

        # row 2: radio buttons for source choice
        radioLayout = QtWidgets.QHBoxLayout()
        setattr(self, f"{slm_key}_{tab_key}_cgh_use_loaded_target", QtWidgets.QRadioButton("Use Loaded Target"))
        setattr(self, f"{slm_key}_{tab_key}_cgh_use_manual_target", QtWidgets.QRadioButton("Use Manual Target Parameters"))
        getattr(self, f"{slm_key}_{tab_key}_cgh_use_manual_target").setChecked(True)
        radioLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_use_loaded_target"))
        radioLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_use_manual_target"))
        radioLayout.addStretch()
        targetSourceLayout.addLayout(radioLayout)

        self._param_definitions[slm_key][tab_key]["cgh"].extend([
            ("radio","use_loaded_target", False,"cgh_use_loaded_target"),
            ("radio","use_manual_target", False,"cgh_use_manual_target"),
            ]
        )

        cghLayout.addWidget(targetSourceBox)

        # --- 3. Target Definition Area ---
        targetBox = QtWidgets.QGroupBox("Target Definition (Manual)")
        targetLayout = QtWidgets.QVBoxLayout(targetBox)

        # target type + visualize button
        targets_list=["BFP spots", "Multi-Foci"]
        typeLayout = QtWidgets.QHBoxLayout()
        typeLayout.addWidget(QtWidgets.QLabel("Target Type:"))
        combo = QtWidgets.QComboBox()
        combo.addItems(targets_list)
        setattr(self, f"{slm_key}_{tab_key}_cgh_target_type", combo)
        typeLayout.addWidget(combo)

        self._param_definitions[slm_key][tab_key]["cgh"].append(
            ("combo","target_type", targets_list,"cgh_target_type"),
        )

        setattr(self, f"{slm_key}_{tab_key}_cgh_visualize_target_btn", BetterPushButton("Visualize Target"))
        typeLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_visualize_target_btn"))
        typeLayout.addStretch()
        targetLayout.addLayout(typeLayout)

        # stacked widget for parameters
        stack = QtWidgets.QStackedWidget()
        setattr(self, f"{slm_key}_{tab_key}_cghParamStack", stack)

        # populate sub-widgets
        bfpWidget = self.createCghBfpwidget(slm_key,tab_key)
        multifociWidget = self.createCghMultifociWidget(slm_key,tab_key)
        stack.addWidget(bfpWidget)
        stack.addWidget(multifociWidget)

        combo.currentIndexChanged.connect(lambda idx: stack.setCurrentIndex(idx))
        targetLayout.addWidget(stack)

        cghLayout.addWidget(targetBox)

        # --- 4. Computation Area ---
        computeBox = QtWidgets.QGroupBox("Computation Settings")
        computeLayout = QtWidgets.QVBoxLayout(computeBox)

        # algorithm parameters
        paramsLayout = QtWidgets.QHBoxLayout()
        setattr(self, f"{slm_key}_{tab_key}_cgh_weighted_gs", QtWidgets.QCheckBox("Weighted-GS"))
        setattr(self, f"{slm_key}_{tab_key}_cgh_iterations", QtWidgets.QLineEdit("20"))
        getattr(self, f"{slm_key}_{tab_key}_cgh_iterations").setFixedWidth(50)
        setattr(self, f"{slm_key}_{tab_key}_cgh_phase_fixing", QtWidgets.QCheckBox("Phase fixing"))
        setattr(self, f"{slm_key}_{tab_key}_cgh_phase_value", QtWidgets.QLineEdit("0"))
        getattr(self, f"{slm_key}_{tab_key}_cgh_phase_value").setFixedWidth(50)

        paramsLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_weighted_gs"))
        paramsLayout.addWidget(QtWidgets.QLabel("Iterations:"))
        paramsLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_iterations"))
        paramsLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_phase_fixing"))
        paramsLayout.addWidget(QtWidgets.QLabel("Phase:"))
        paramsLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_cgh_phase_value"))
        paramsLayout.addStretch()
        computeLayout.addLayout(paramsLayout)
        cghLayout.addWidget(computeBox)

        self._param_definitions[slm_key][tab_key]["cgh"].extend([
            ("checkbox","weighted_gs", False, f"cgh_weighted_gs"),
            ("lineedit","iterations", 20, f"cgh_iterations"),
            ("checkbox","phase_fixing", False, f"cgh_phase_fixing"),
            ("lineedit","phase_value", 0, f"cgh_phase_value"),
        ]
        )

        # --- 5. Compute + Save Row ---
        bottomBtnLayout = QtWidgets.QHBoxLayout()
        setattr(self, f"{slm_key}_{tab_key}_compute_cgh_btn", BetterPushButton("Compute CGH"))
        setattr(self, f"{slm_key}_{tab_key}_save_cgh_btn", BetterPushButton("Save CGH"))

        bottomBtnLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_compute_cgh_btn"),alignment=QtCore.Qt.AlignLeft)
        bottomBtnLayout.addWidget(getattr(self, f"{slm_key}_{tab_key}_save_cgh_btn"),alignment=QtCore.Qt.AlignLeft)
        bottomBtnLayout.addStretch()
        cghLayout.addLayout(bottomBtnLayout)

        # --- finalize group ---
        group.setContentLayout(cghLayout)

        # signal connection
        getattr(self, f"{slm_key}_{tab_key}_compute_cgh_btn").clicked.connect(
            lambda: self.onComputeCgh(slm_key, tab_key)
            )

        return group



    def createUpdateSection(self, parent_layout, slm_key="slm"):
        """
        Create the "Update SLM Pattern" section with per-slm controls.
        """
        layout = QtWidgets.QHBoxLayout()

        # Correction pattern checkbox
        applyCorrectionCheck = QtWidgets.QCheckBox("Correction pattern")
        applyCorrectionCheck.setChecked(True)
        setattr(self, f"{slm_key}_applyCorrectionCheck", applyCorrectionCheck)

        # Max value correction checkbox
        maxValueCheck = QtWidgets.QCheckBox("Max. value correction")
        maxValueCheck.setChecked(True)
        setattr(self, f"{slm_key}_maxValueCheck", maxValueCheck)

        # Update button
        updatePatternBtn = BetterPushButton("Update SLM Pattern")
        updatePatternBtn.setMinimumHeight(32)
        updatePatternBtn.setStyleSheet("font-weight: bold;")
        setattr(self, f"{slm_key}_updatePatternBtn", updatePatternBtn)

        # Add widgets to layout
        layout.addWidget(applyCorrectionCheck)
        layout.addWidget(maxValueCheck)
        layout.addStretch()
        layout.addWidget(updatePatternBtn)

        # Add the layout to the parent layout
        parent_layout.addLayout(layout)

        # signal connection
        updatePatternBtn.clicked.connect(lambda: self.onUpdatePattern(slm_key))



    #### PATTERNS UI BUILDER ####
    def addBinaryGrating(self, layout, row, slm_key,tab_key):
        params = [
            ("checkbox","Binary Grating", None, "checkbox"),
            ("label","Period",None, None),
            ("lineedit","X", 0, "period_x"),
            ("lineedit","Y", 0, "period_y"),
            ("label","Duty",None,None),
            ("lineedit","X", 0.5,"duty_x"),
            ("lineedit","Y", 0.5,"duty_y"),
        ]
        row = self.addParamGrid(slm_key, tab_key, "patterns", params, row, layout, per_row="all",attr_prefix="binary")
        return row

    def addSinusoidalGrating(self, layout, row, slm_key, tab_key):
        params = [
            ("checkbox","Sinusoidal Grating", None,"checkbox"),
            ("label","Period",None),
            ("lineedit","X", 0, "period_x"),
            ("lineedit","Y", 0, "period_y"),
            ("label","Power (sinⁿ)",None),
            ("lineedit","X", 1,"pwr_x"),
            ("lineedit","Y", 1,"pwr_y"),
        ]
        row = self.addParamGrid(slm_key,tab_key, "patterns", params, row, layout, per_row="all",attr_prefix="sinusoidal")
        return row

    def addLinearPhase(self, layout, row, slm_key, tab_key):
        params = [
            ("checkbox","Linear Phase", None, "checkbox"),
            ("label","Period",None,None),
            ("lineedit","X", 0, "period_x"),
            ("lineedit","Y", 0, "period_y"),
        ]
        row = self.addParamGrid(slm_key, tab_key, "patterns", params, row, layout, per_row="all",attr_prefix="linearphase")
        return row

    def addLensPhase(self, layout, row, slm_key,tab_key):
        params = [
            ("checkbox","Lens Phase", None, "checkbox"),
            ("lineedit","Focal Length (mm)", 225, "focal_mm"),
        ]
        row = self.addParamGrid(slm_key, tab_key, "patterns", params, row, layout, per_row="all",attr_prefix="lensphase")
        return row 


    #### HOLOGRAMS TARGETS UI  BUILDERS ####
    def createCghBfpwidget(self, slm_key="slm", tab_key="tab0"):
        """
        Build the BFP spots parameters widget for a CGH section.
        """
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(widget)

        params = [
            ("combo","Direction", ["X","Y"]),
            ("lineedit", "Target Size", 512),
            ("lineedit","Spot distance", "200"),
            ("lineedit","Offset", "0"),
            ("lineedit","Spot1 Intensity", "1.0"),
            ("lineedit","Spot2 Intensity", "1.0"),
        ]
        self.addParamGrid(slm_key, tab_key, "cgh", params, 0, layout, per_row=2, width=60, attr_prefix="cgh_bfpspots")
        return widget


    def createCghMultifociWidget(self, slm_key="slm",tab_key="tab0"):
        """
        Build the Multi-Foci parameters widget for a CGH section.
        Arranges parameters in 2 per row (4 columns).
        """
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(widget)

        params = [
            ("lineedit","Target size X", "512"),
            ("lineedit","Target size Y", "512"),
            ("lineedit","N foci", "3"),
            ("lineedit","Period", "10"),
        ]
        self.addParamGrid(slm_key,tab_key,"cgh", params, 0, layout, per_row=2, width=60,attr_prefix="cgh_multifoci")
        return widget

    ### GRID BUILDING HELPER FUNCTION ####
    def addParamGrid(self, slm_key, tab_key,section_name, params, start_row, layout, per_row="all", width=60,attr_prefix=None):
        """
        Generic UI grid builder that supports checkbox, lineedit, and combo widgets.
        Adds the parameters to existing QGridLayout starting at arg:`start_row`, 
        arg:`per_row` specify how many parameters per row ("all" = all params in one row)

        For each param, we set the attributes name.

        Each param is also added to self._param_definitions[slm_key][tab_key][base_name].

        params: list of tuples like:
            ("checkbox", "Binary Grating", None, "use_binary")
            ("lineedit", "X", "0", "binary_periodx")
            ("combo", "Direction", ["X", "Y"], "bfpspots_direction")
            ("label","Period",None,None)

        NOTE: except for `label` which is only a Qlabel, we always add object + label, e.g.
        ("combo", "Direction", ["X", "Y"]) ==> "Direction: " [Combo box with X,Y options]

        Returns the next available row index.
        """
        
        if per_row == "all" or per_row is None:
            per_row = 100

        row = start_row
        col = 0

        for p in params:

            if len(p)==3:
                ptype, label, default_or_items = p
                attrname = label # attribute will be set based on label
            elif len(p)==4:
                ptype, label, default_or_items, attrname = p
            else:
                raise ValueError(f"Invalid parameter definition: {p}")


            # label only
            if ptype == "label":
                lbl = QtWidgets.QLabel(label + ":")
                layout.addWidget(lbl, row, col,1,1)
                col += 1

            # Checkbox
            elif ptype == "checkbox":
                widget = QtWidgets.QCheckBox(label)
                layout.addWidget(widget, row, col, 1, 1)
                col += 1

            # LineEdit
            elif ptype == "lineedit":
                lbl = QtWidgets.QLabel(label + ":")
                widget = QtWidgets.QLineEdit(str(default_or_items))
                widget.setFixedWidth(width)
                layout.addWidget(lbl, row, col,1,1)
                layout.addWidget(widget, row, col + 1,1,1)
                col += 2

            # ComboBox
            elif ptype == "combo":
                lbl = QtWidgets.QLabel(label + ":")
                widget = QtWidgets.QComboBox()
                widget.addItems(default_or_items)
                layout.addWidget(lbl, row, col,1,1)
                layout.addWidget(widget, row, col + 1,1,1)
                col += 2

            else:   
                self.__logger.warning(f"Unknown parameter type '{ptype}' for '{label}'")
            
            if col > per_row:
                row+=1
                col = 0

            ### set attr and add in param_definitions ###
            if ptype not in ["label"] and attrname is not None:
                if attr_prefix is not None:
                    attrname = f"{attr_prefix}_{attrname}"
                full_attrname = cleanAttrName(f"{slm_key}_{tab_key}_{attrname}")
                setattr(self, full_attrname, widget)

                if section_name is not None:
                    self._param_definitions[slm_key][tab_key][section_name].append(
                        (ptype,label,default_or_items,cleanAttrName(attrname))
                    )


        # Return the next free row
        if col>0:
            row+=1

        return row

    ##### PARAMETER GETTING / SETTING #####
    def getParams(self):
        """ Gather all parameter values from the UI widgets according to
        the meta-structure stored in self._param_definitions."""

        all_params = {}
        for slm_key, tab_dict in self._param_definitions.items():
            all_params[slm_key] = {}

            for tab_key, section_dict in tab_dict.items():
                all_params[slm_key][tab_key] = {}

                for section_name, param_list in section_dict.items():
                    section_values = {}

                    for ptype, _, _, attrname in param_list:
                        # Build the attribute name used in the class
                        full_attrname = cleanAttrName(f"{slm_key}_{tab_key}_{attrname}")

                        widget = getattr(self, full_attrname, None)
                        if widget is None:
                            print("attribute not found: ", full_attrname)
                            # silently skip if widget not found
                            continue

                        # Read the value according to widget type
                        if ptype == "lineedit":
                            val = widget.text()
                            # Try to convert to numeric if possible
                            try:
                                val = json.loads(val)
                            except Exception:
                                pass
                        elif ptype == "checkbox":
                            val = widget.isChecked()
                        elif ptype == "combo":
                            val = widget.currentText()
                        elif ptype == "radio":
                            val = widget.isChecked()
                        else:
                            val = None

                        section_values[attrname] = val

                    all_params[slm_key][tab_key][section_name] = section_values

        return all_params


    def setParams(self, params_dict):
        """
        Restore all parameter values into the UI widgets from a dictionary
        matching the structure returned by getParams().
        """
        for slm_key, tab_dict in params_dict.items():
            if slm_key not in self._param_definitions:
                continue

            for tab_key, section_dict in tab_dict.items():
                if tab_key not in self._param_definitions[slm_key]:
                    continue

                for section_name, param_values in section_dict.items():
                    if section_name not in self._param_definitions[slm_key][tab_key]:
                        continue

                    for ptype, label, default_or_items, attrname in self._param_definitions[slm_key][tab_key][section_name]:
                        full_attrname = cleanAttrName(f"{slm_key}_{tab_key}_{attrname}")
                        widget = getattr(self, full_attrname, None)
                        if widget is None:
                            continue

                        if attrname not in param_values:
                            # value not provided in dict, skip
                            continue

                        val = param_values[attrname]

                        # --- Restore according to widget type ---
                        try:
                            if ptype == "lineedit":
                                widget.setText(str(val))

                            elif ptype == "checkbox":
                                widget.setChecked(bool(val))

                            elif ptype == "combo":
                                # try to set by text if available
                                idx = widget.findText(str(val))
                                if idx >= 0:
                                    widget.setCurrentIndex(idx)

                            elif ptype == "radio":
                                widget.setChecked(bool(val))

                        except Exception as e:
                            self.__logger.warning(
                                f"Failed to set {full_attrname} ({ptype}) value: {val}. Error: {e}"
                            )


    ###### LOGIC HANDLING #####    
    
    def renameTab(self,slm_key, tabWidget, index):
        """Open an input dialog to rename a tab."""
        if index < 0:
            return  # clicked outside any tab
        old_name = tabWidget.tabText(index)
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, "Rename Section", "Enter new section name:", text=old_name
        )
        if ok and new_name.strip():
            tabWidget.setTabText(index, new_name.strip())
            # update tab_names_dict
            keys = list(self._tab_names_dict[slm_key].keys())
            if index < len(keys):
                key = keys[index]
            self._tab_names_dict[slm_key][key] = new_name

    def onConnectionResult(self, slm_key: str, success: bool, serial: str):
        btn = getattr(self, f"{slm_key}_connectBtn")
        if success:
            btn.setText("Disconnect")
            QtWidgets.QMessageBox.information(self, "SLM Connection", f"Successfully connected to SLM {serial}")
        else:
            btn.blockSignals(True)  # prevent re-emitting toggled
            btn.setChecked(False)
            btn.blockSignals(False)
            btn.setText("Connect to SLM")
            QtWidgets.QMessageBox.warning(self, "SLM Connection", f"Connection to {self._slmNames[slm_key]} failed.")
    
    def onDisconnectionResult(self, slm_key: str, success: bool, msg: str):
        btn = getattr(self, f"{slm_key}_connectBtn")
        if success:
            btn.setText("Connect to SLM")
            QtWidgets.QMessageBox.information(self, "SLM Disconnected", msg)
        else:
            btn.blockSignals(True)  # prevent re-emitting toggled
            btn.setChecked(True)
            btn.blockSignals(False)
            QtWidgets.QMessageBox.warning(self, "SLM Disconnection", msg)
    
    def onUpdatePattern(self, slm_key):
        # get parameters for this slm
        all_params = self.getParams()
        params = all_params.get(slm_key, {})
        # add correction options
        apply_corr = getattr(self, f"{slm_key}_applyCorrectionCheck").isChecked()
        max_val_corr = getattr(self, f"{slm_key}_maxValueCheck").isChecked()
        params["correction_options"] = {
            "apply_correction": apply_corr,
            "max_value_correction": max_val_corr
        }
        self.sigUpdatePattern.emit(slm_key, params)

    def onComputeCgh(self,slm_key,tab_key):
        #get cgh params
        print(self._param_definitions[slm_key][tab_key]["cgh"])
        all_params = self.getParams()
        tab_params = all_params.get(slm_key, {}).get(tab_key, {})
        cgh_params = tab_params.get("cgh", {})
        if not cgh_params:
            self.__logger.warning(f"No CGH parameters found for {slm_key}:{tab_key}")
            return

        self.sigComputeCGH.emit(slm_key, cgh_params)

def cleanAttrName(label: str) -> str:
    """
    Convert a label string to a valid attribute name:
    - lowercase
    - remove spaces
    - replace spaces with underscores
    - remove any text in parentheses
    - remove other non-alphanumeric/underscore characters
    """
    # remove parentheses and their content
    label = re.sub(r"\(.*?\)", "", label)
    # remove any remaining non-alphanumeric/underscore chars
    label = re.sub(r"[^0-9a-zA-Z_ ]", "", label)
    # replace spaces with underscores and lowercase
    label = label.strip().replace(" ", "_").lower()
    return label