from qtpy import QtCore, QtWidgets, QtGui
from imswitch.imcontrol.view.guitools import CollapsibleSection, BetterPushButton, askForFilePath
import pyqtgraph as pg
from .basewidgets import Widget
from imswitch.imcommon.model import initLogger, dirtools
import re
import json
import os
import numpy as np
import matplotlib.pyplot as plt

class SLMsWidget(Widget):
    """Widget containing SLM interface, patterns, and CGH controls."""

    sigConnectSLMusb = QtCore.Signal(str,bool)              # slmName, state
    sigUpdatePattern = QtCore.Signal(str, dict)             # slmKey, params
    sigComputeCGH = QtCore.Signal(str, str,dict)            # slmKey, secKey, cgh_params

    sigVisualizeCghPerformances = QtCore.Signal(str, str)   # slmKey, secKey
    sigVisualizeTarget = QtCore.Signal(str, dict)           # target_type, target_params
    sigShowCghResult = QtCore.Signal(str, str, int)         # slmKey, secKey, pad_size
    
    sigLoadConfig = QtCore.Signal(str)                      # slmKey
    sigLoadAberr = QtCore.Signal(str,str)                   # slmKey, secKey
    sigLoadCgh = QtCore.Signal(str, str)                    # slmKey, secKey
    sigSaveConfig = QtCore.Signal(str,dict)                 # slmKey, parameters
    sigSaveAberr = QtCore.Signal(str,str,dict)              # slmKey, secKey, aberr_params
    sigSaveCgh = QtCore.Signal(str, str)                    # slmKey, secKey

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumSize(200,200)
        self.__logger = initLogger(self)

        # create main layout
        mainlayout = QtWidgets.QVBoxLayout(self)
        mainlayout.setSpacing(10)
        mainlayout.setContentsMargins(3, 3, 3, 3)
        self.setLayout(mainlayout)

        # create slmTabs widget
        self.slmTabs = QtWidgets.QTabWidget()
        self.slmTabs.setTabPosition(QtWidgets.QTabWidget.North)
        self.slmTabs.setMovable(True)
        mainlayout.addWidget(self.slmTabs)

        # init dictionaries
        self._slmNames = {}             # {slmKey: slmName}
        self._slm_widgets = {}          # {slmKey: widget}
        self._slmInfos = {}             # {slmKey: slmInfo}
        self._tab_names_dict={}         # {slmKey: {secKey: tab_name}} 
        self._slmSectionList = {}       # list of sections per slmKey {slmKey: [secKey1, secKey2,...]}
        self._param_definitions = {}    # list of parameters stored by slmKey[secKey][sectionName]


    def add_slm(self,slmName,slmInfo,full_registry,*args,**kwargs):
        
        # NOTE: slmKey is the cleaned slmName used for referencing 
        # and setting attributes - slmName is kept for display
        slmKey = clean_attr_name(slmName)
        self._slmSectionList[slmKey] = []
        self._slmNames[slmKey] = slmName
        self._param_definitions[slmKey] = {}
        self._tab_names_dict[slmKey] = {}

        # slm container
        slmContainer = QtWidgets.QWidget()
        slmLayout = QtWidgets.QVBoxLayout(slmContainer)
        slmLayout.setSpacing(10)
        slmLayout.setContentsMargins(0, 0, 0, 0)

        # middle container (scroll area)
        middlecontainer = QtWidgets.QWidget()
        middlelayout = QtWidgets.QVBoxLayout(middlecontainer)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scrollArea.setWidget(middlecontainer)
        scrollArea.setWidgetResizable(True)

        # top control => added to slmLayout
        self.create_top_controls(slmLayout,slmKey=slmKey)

        # image preview and tabs => added to middlelayout (scroll area)
        self.create_image_display(middlelayout,slmKey=slmKey)
        self.build_tab_section(middlelayout,slmKey=slmKey,n_tabs=slmInfo.nSections,
                            tab_names=slmInfo.sectionsNames,options=slmInfo.widgetOptions,
                            full_registry=full_registry)
        slmLayout.addWidget(scrollArea)
        
        # bottom controls added to slmLayout
        self.create_update_section(slmLayout,slmKey=slmKey)

        # finally: add to slmTabs
        slmContainer.setLayout(slmLayout)
        self.slmTabs.addTab(slmContainer,slmName) # here we give the original slmName to be displayed
        self._slm_widgets[slmKey] = slmContainer
        return slmKey
    
    # -------------------------------------------- #
    #           SLM SECTION TABS BUILDERS          #
    # -------------------------------------------- #

    def build_tab_section(self, parent_layout, slmKey="slm", n_tabs=1, tab_names=None,
                          options={}, full_registry={}):
        """
        Create N sub-tabs (e.g. for double-pass left/right).
        If N == 1, just builds the single SLM section directly.
        """
        if n_tabs is None:
            n_tabs = 1
            tab_names = ["Full SLM"]

        elif not tab_names:
            tab_names = [f"Section {i+1}" for i in range(n_tabs)]
        
        subTabs = QtWidgets.QTabWidget()
        subTabs.setDocumentMode(True)
        sectionsList = []
        for i,name in enumerate(tab_names):
            secKey = f"sec_{i}" #NOTE: sec_*number* is also used in patternEngine to reference sections
            sectionsList.append(secKey)
            self._tab_names_dict[slmKey][secKey] = name
            section_widget = self.create_slm_section(slmKey,secKey,options,full_registry)
            subTabs.addTab(section_widget, name)
        
        self._slmSectionList[slmKey] = sectionsList

        # store subtabs widget for later access
        setattr(self, f"{slmKey}_subTabs", subTabs)
        
        # Allow user to rename tabs
        subTabs.tabBarDoubleClicked.connect(lambda index: self.rename_tab(slmKey,subTabs, index))

        parent_layout.addWidget(subTabs)
    

    def create_slm_section(self, slmKey="slm",secKey="sec_0",options={},full_registry={}):
        """
        Create one complete SLM section.
        """
        self._param_definitions[slmKey][secKey]={}

        container = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(container)

        # General
        self._param_definitions[slmKey][secKey]["general"]=[]
        vbox.addWidget(self.create_general_group(slmKey,secKey))

        # Patterns
        self._param_definitions[slmKey][secKey]["patterns"]={}
        pattern_options = options.get("patterns", None)
        pattern_registry = full_registry.get("patterns",{})
        vbox.addWidget(self.create_patterns_group(slmKey,secKey,pattern_options,pattern_registry))

        # aberration correction
        if options.get("aberrations",True):
            self._param_definitions[slmKey][secKey]["aberrations"]=[]
            aberrations_registry = full_registry.get("aberrations",{})
            vbox.addWidget(self.create_aberrations_group(slmKey,secKey,aberrations_registry))

        # CGH
        if options.get("cgh",True):
            self._param_definitions[slmKey][secKey]["cgh"]={}
            vbox.addWidget(self.create_cgh_group(slmKey,secKey))

        vbox.addStretch()
        return container
    
    
    # -------------------------------------------- #
    #           GENERAL CONTROLS PANELS            #
    #  Connection, Image Display, Update Pattern   #
    # -------------------------------------------- #
        
    # --- 1. Top Controls (Connect, Save/Load Config) ----
    def create_top_controls(self, parent_layout, slmKey="slm"):
        """
        Create the top control row for a single SLM: Connect button + Save/Load buttons.
        """
        layout = QtWidgets.QHBoxLayout()

        # Connect button
        connectBtn = BetterPushButton("Connect to SLM")
        connectBtn.setCheckable(True)
        connectBtn.setMinimumHeight(28)
        setattr(self, f"{slmKey}_connectBtn", connectBtn)
        layout.addWidget(connectBtn)

        layout.addStretch()
        # Save / Load buttons
        saveConfigBtn = BetterPushButton("Save Config")
        loadConfigBtn = BetterPushButton("Load Config")
        setattr(self, f"{slmKey}_saveConfigBtn", saveConfigBtn)
        setattr(self, f"{slmKey}_loadConfigBtn", loadConfigBtn)
        layout.addWidget(saveConfigBtn)
        layout.addWidget(loadConfigBtn)

        parent_layout.addLayout(layout)

        # signal connections
        connectBtn.toggled.connect(lambda state, p=slmKey: self.sigConnectSLMusb.emit(p, state))
        saveConfigBtn.clicked.connect(lambda: self.on_save_config(slmKey))
        loadConfigBtn.clicked.connect(lambda: self.sigLoadConfig.emit(slmKey))


    # ---- 2. Image Display (Collapsible) ----
    def create_image_display(self, parent_layout, slmKey="slm"):
        """
        Create a pyqtgraph-based SLM image display with zoom, LUT, and pixel readout.
        """
        # Collapsible section
        imageSection = CollapsibleSection("SLM Preview", target_height=200,frame=False)
        imageSection.toggleButton.clicked.connect(
            lambda checked: self.on_image_preview_toggled(slmKey,checked)
        )
        setattr(self, f"{slmKey}_imageSection", imageSection)

        # Main pyqtgraph widget
        cwidget = pg.GraphicsLayoutWidget()
        setattr(self, f"{slmKey}_cwidget", cwidget)

        # ViewBox (interactive)
        vb = cwidget.addViewBox(row=1, col=1)
        vb.setMouseMode(pg.ViewBox.RectMode)
        vb.setAspectLocked(True)
        setattr(self, f"{slmKey}_vb", vb)

        # ImageItem for 2D numpy array
        img = pg.ImageItem(axisOrder='row-major')
        vb.addItem(img)
        setattr(self, f"{slmKey}_img", img)

        # Pixel info label
        pixelLabel = QtWidgets.QGraphicsTextItem("")
        pixelLabel.setDefaultTextColor(QtGui.QColor("white"))
        pixelLabel.setPos(0, 0)
        vb.scene().addItem(pixelLabel)
        setattr(self, f"{slmKey}_pixelLabel", pixelLabel)

        # reset button
        homeBtn = BetterPushButton("Reset View")
        homeBtn.clicked.connect(lambda: self.reset_view(slmKey))
        setattr(self, f"{slmKey}_homeBtn", homeBtn)
        homeBtn.setFixedHeight(imageSection.toggleButton.sizeHint().height())
        imageSection.addHeaderWidget(homeBtn,position=-1)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(cwidget,stretch=1)
        layout.setContentsMargins(30, 0, 30, 0)

        imageSection.setContentLayout(layout)
        parent_layout.addWidget(imageSection)

        # Mouse-over pixel info
        vb.scene().sigMouseMoved.connect(lambda pos, key=slmKey: self.mouseMoved(pos, key))

        # Store last image for zoom updates
        setattr(self, f"{slmKey}_currentPattern", None)



    # ---- 3. Update SLM Pattern section (bottom) ----
    def create_update_section(self, parent_layout, slmKey="slm"):
        """
        Create the "Update SLM Pattern" section with per-slm controls.
        """
        layout = QtWidgets.QHBoxLayout()

        # Correction pattern checkbox
        applyCorrectionCheck = QtWidgets.QCheckBox("Correction pattern")
        applyCorrectionCheck.setChecked(True)
        setattr(self, f"{slmKey}_applyCorrectionCheck", applyCorrectionCheck)

        # Max value correction checkbox
        twopiCheck = QtWidgets.QCheckBox("2Pi value correction")
        twopiCheck.setChecked(True)
        setattr(self, f"{slmKey}_twopiCheck", twopiCheck)

        # Update button
        updatePatternBtn = BetterPushButton("Update SLM Pattern")
        updatePatternBtn.setMinimumHeight(32)
        updatePatternBtn.setStyleSheet("font-weight: bold;")
        setattr(self, f"{slmKey}_updatePatternBtn", updatePatternBtn)

        # Add widgets to layout
        layout.addWidget(applyCorrectionCheck)
        layout.addWidget(twopiCheck)
        layout.addStretch()
        layout.addWidget(updatePatternBtn)

        # Add the layout to the parent layout
        parent_layout.addLayout(layout)

        # signal connection
        updatePatternBtn.clicked.connect(lambda: self.on_update_pattern(slmKey))



    # -------------------------------------------- #
    #           SPECIFIC GROUP BUILDERS:           #   
    #      General, Patterns, Aberrations, CGH     #
    # -------------------------------------------- #

    # General section
    def create_general_group(self,slmKey="slm",secKey="sec_0"):
        group = CollapsibleSection("General")
        layout = QtWidgets.QGridLayout()
        params = [
            ('lineedit','Wavelength (nm)','488'),
            ('lineedit','Pupil Radius (px)', 0),
            ('lineedit','Center Offset X (px)', 0),
            ('lineedit','Center Offset Y (px)', 0),
        ]
        self.add_param_grid(slmKey, secKey,"general",params, 0, layout, per_row=1)
        group.setContentLayout(layout)
        return group
    


    # Patterns section
    def create_patterns_group(self, slmKey="slm",secKey="sec_0", options=None, pattern_registry={}):
        """
        Create the Patterns group with collapsible section.
        """
        if options is None:
            self.__logger.warning("No patterns options, using all available patterns from registry.")

        group = CollapsibleSection("Patterns")
        layout = QtWidgets.QGridLayout()
        list_patterns = options

        row = 0
        for pattern in list_patterns:
            if pattern_registry.get(pattern) is None:
                self.__logger.warning(f"Pattern '{pattern}' is requested but not found in registry.")
                continue

            # first see if specific builder exists (overriding default registry-based one)
            builder = getattr(self, f"add{pattern}", None)
            if builder is not None:
                row = builder(layout, row, slmKey, secKey)

            # if not, use the generic pattern builder which uses the registry
            else:
                info = pattern_registry[pattern]
                row = self.add_generic_pattern(layout, row, slmKey, secKey, "patterns", 
                                               pattern, info["params"],) 

        spacer = QtWidgets.QSpacerItem(0, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        layout.addItem(spacer, row, 0)
        group.setContentLayout(layout)
        return group


    # Aberrations section
    def create_aberrations_group(self, slmKey="slm",secKey="sec_0",aberrations_registry={}):
        group = CollapsibleSection("Aberrations")
        layout = QtWidgets.QGridLayout()
        row = 0

        # checkbox to easily activate/deactivate correction
        use_aberr = QtWidgets.QCheckBox("Apply aberrations correction")
        group.addHeaderWidget(use_aberr)
        setattr(self, f"{slmKey}_{secKey}_aberrations_active", use_aberr)
        self._param_definitions[slmKey][secKey]["aberrations"].append(
            ("checkbox","aberrations_active",False, "aberrations_active")
        )

        # Save/Load buttons
        loadAberrBtn = BetterPushButton("Load")
        saveAberrBtn = BetterPushButton("Save")
        loadedLabel = QtWidgets.QLabel("Loaded: None")
        loadedLabel.setStyleSheet("color: #888;")

        setattr(self, f"{slmKey}_save_aberrations_btn", saveAberrBtn)
        setattr(self, f"{slmKey}_{secKey}_load_aberrations_btn", loadAberrBtn)
        setattr(self, f"{slmKey}_{secKey}_load_aberrations_label", loadedLabel)

        layout.addWidget(saveAberrBtn, row, 0)
        layout.addWidget(loadAberrBtn, row, 1)
        layout.addWidget(loadedLabel, row, 2)
        row += 1
        spacer = QtWidgets.QSpacerItem(0, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        layout.addItem(spacer, row, 0, 1, 2)
        row += 1
        
        # Column headers
        header_font = QtGui.QFont()
        header_font.setBold(True)

        lbl_aberr = QtWidgets.QLabel("Aberration")
        lbl_aberr.setFont(header_font)
        lbl_coeff = QtWidgets.QLabel("Coefficient (λ)")
        lbl_coeff.setFont(header_font)

        layout.addWidget(lbl_aberr, row, 0)
        layout.addWidget(lbl_coeff, row, 1)
        row += 1

        # Parameter rows
        for aberr_name, aberr_info in aberrations_registry.items():
            row = self.add_generic_pattern(layout, row, slmKey, secKey, "aberrations",aberr_name,aberr_info["params"],
                                           use_subsection=False, add_checkbox=False, single_param_mode=True)
        layout.addItem(spacer,row,0,1,2)

        # finalize group
        group.setContentLayout(layout)

        # signal connection
        loadAberrBtn.clicked.connect(lambda: self.sigLoadAberr.emit(slmKey,secKey))
        saveAberrBtn.clicked.connect(lambda: self.on_save_aberr(slmKey,secKey))

        return group


    # CGH patterns section
    def create_cgh_group(self, slmKey="slm",secKey="sec_0"):

        # NOTE: general cgh parameters stored in subsection "cgh_general":
        # ==> related attributes will be named accordingly:
        # self.{slmKey}_{secKey}_cgh_general_{attrname}

        group = CollapsibleSection("CGH Pattern")
        cghLayout = QtWidgets.QVBoxLayout()
        cghLayout.setSpacing(10)
        generalsubsec = "cgh_general"
        self._param_definitions[slmKey][secKey]["cgh"].setdefault(generalsubsec, [])

        # --- 1. General Controls ---

        # checkbox and label (next to header of collapsible section)
        use_cgh_checkbox = QtWidgets.QCheckBox("Use CGH")
        inUseLabelPrefix = QtWidgets.QLabel("In use:  ")
        inUseLabel = QtWidgets.QLabel("None")
        inUseLabel.setStyleSheet("color: #888;")

        group.addHeaderWidget(use_cgh_checkbox)
        group.addHeaderWidget(inUseLabelPrefix)
        group.addHeaderWidget(inUseLabel)
        generalLayout = QtWidgets.QHBoxLayout()

        setattr(self, f"{slmKey}_{secKey}_{generalsubsec}_active", use_cgh_checkbox)
        setattr(self, f"{slmKey}_{secKey}_cgh_in_use_label", inUseLabel)
        
        # save and load btn (inside collapsible section)
        loadPatternBtn = BetterPushButton("Load Pattern")
        saveCghBtn = BetterPushButton("Save CGH")

        setattr(self, f"{slmKey}_{secKey}_save_cgh_btn", saveCghBtn)
        setattr(self, f"{slmKey}_{secKey}_cgh_load_btn", loadPatternBtn)

        generalLayout.addWidget(loadPatternBtn)
        generalLayout.addWidget(saveCghBtn)
        generalLayout.addStretch()
        cghLayout.addLayout(generalLayout)

        self._param_definitions[slmKey][secKey]["cgh"][generalsubsec].append(
            ("checkbox","active",False, "active")
        )

        # --- 2. Target Definition Area ---
        targetBox = QtWidgets.QGroupBox("Target Definition")
        targetLayout = QtWidgets.QVBoxLayout(targetBox)

        # target type + visualize button
        targets_list=["Multi-Foci", "BFP spots"]
        typeLayout = QtWidgets.QHBoxLayout()
        typeLayout.addWidget(QtWidgets.QLabel("Target Type:"))
        combo = QtWidgets.QComboBox()
        combo.addItems(targets_list)
        setattr(self, f"{slmKey}_{secKey}_{generalsubsec}_target_type", combo)
        typeLayout.addWidget(combo)

        self._param_definitions[slmKey][secKey]["cgh"][generalsubsec].append(
            ("combo","target_type", targets_list, "target_type"),
        )

        visualizeTargetBtn = BetterPushButton("Visualize Target")
        setattr(self, f"{slmKey}_{secKey}_cgh_visualize_target_btn", visualizeTargetBtn)
        typeLayout.addWidget(visualizeTargetBtn)
        typeLayout.addStretch()
        targetLayout.addLayout(typeLayout)

        # stacked widget for parameters
        stack = QtWidgets.QStackedWidget()
        setattr(self, f"{slmKey}_{secKey}_cghParamStack", stack)

        # populate sub-widgets
        multifociWidget = self.create_cgh_multifoci_widget(slmKey,secKey)
        bfpWidget = self.create_cgh_bfp_widget(slmKey,secKey)
        stack.addWidget(multifociWidget)
        stack.addWidget(bfpWidget)

        combo.currentIndexChanged.connect(lambda idx: stack.setCurrentIndex(idx))
        targetLayout.addWidget(stack)

        cghLayout.addWidget(targetBox)

        # --- 3. Computation Area ---

        # computation parameters stored in subsection "cgh_computation":
        # ==> related attributes will be named accordingly:
        # self.{slmKey}_{secKey}_cgh_general_{attrname}

        computsubsec = "cgh_computation"
        self._param_definitions[slmKey][secKey]["cgh"].setdefault(computsubsec, [])
        computeBox = QtWidgets.QGroupBox("Computation Settings")
        computeLayout = QtWidgets.QVBoxLayout(computeBox)
        
        # algorithm parameters
        paramsLayout = QtWidgets.QHBoxLayout()
        weightedgsCheckbox=QtWidgets.QCheckBox("Weighted-GS")
        weightedgsCheckbox.setChecked(True)
        niterEdit = QtWidgets.QLineEdit("50")
        niterEdit.setFixedWidth(50)
        phaseFixingCheckbox = QtWidgets.QCheckBox("Phase fixing")
        phaseFixingCheckbox.setChecked(True)
        phaseFixingValue = QtWidgets.QLineEdit("30")
        phaseFixingValue.setFixedWidth(50)

        setattr(self, f"{slmKey}_{secKey}_{computsubsec}_weighted_gs", weightedgsCheckbox)
        setattr(self, f"{slmKey}_{secKey}_{computsubsec}_n_iterations", niterEdit)
        setattr(self, f"{slmKey}_{secKey}_{computsubsec}_phase_fixing", phaseFixingCheckbox)
        setattr(self, f"{slmKey}_{secKey}_{computsubsec}_phase_fixing_value", phaseFixingValue)

        paramsLayout.addWidget(weightedgsCheckbox)
        paramsLayout.addWidget(QtWidgets.QLabel("Iterations:"))
        paramsLayout.addWidget(niterEdit)
        paramsLayout.addWidget(phaseFixingCheckbox)
        paramsLayout.addWidget(QtWidgets.QLabel("Phase:"))
        paramsLayout.addWidget(phaseFixingValue)
        paramsLayout.addStretch()
        computeLayout.addLayout(paramsLayout)
        cghLayout.addWidget(computeBox)

        self._param_definitions[slmKey][secKey]["cgh"][computsubsec].extend([
            ("checkbox","weighted_gs", False, "weighted_gs"),
            ("lineedit","n_iterations", 20, "n_iterations"),
            ("checkbox","phase_fixing", False, "phase_fixing"),
            ("lineedit","phase_fixing_value", 0, "phase_fixing_value"),
        ]
        )

        # --- 4. Compute + Save Row ---
        bottomBtnLayout = QtWidgets.QHBoxLayout()
        computeCghBtn = BetterPushButton("Compute CGH")
        plotCghPerfBtn = BetterPushButton("Plot Perf")
        showResultBtn = BetterPushButton("Show Result (FFT)")
        padSizeLabel = QtWidgets.QLabel("Result Pad Size:")
        padSizeValue = QtWidgets.QLineEdit("1024")

        setattr(self, f"{slmKey}_{secKey}_compute_cgh_btn", computeCghBtn)
        setattr(self, f"{slmKey}_{secKey}_plot_cfg_perf_btn", plotCghPerfBtn)
        setattr(self, f"{slmKey}_{secKey}_show_cgh_result_btn", showResultBtn)
        setattr(self, f"{slmKey}_{secKey}_pad_size_cgh_result", padSizeValue)

        bottomBtnLayout.addWidget(computeCghBtn,alignment=QtCore.Qt.AlignLeft)
        bottomBtnLayout.addWidget(plotCghPerfBtn,alignment=QtCore.Qt.AlignLeft)
        bottomBtnLayout.addWidget(showResultBtn,alignment=QtCore.Qt.AlignLeft)
        bottomBtnLayout.addWidget(padSizeLabel,alignment=QtCore.Qt.AlignLeft)
        bottomBtnLayout.addWidget(padSizeValue,alignment=QtCore.Qt.AlignLeft)
        bottomBtnLayout.addStretch()
        cghLayout.addLayout(bottomBtnLayout)

        # --- finalize group ---
        group.setContentLayout(cghLayout)

        # signal connection
        computeCghBtn.clicked.connect(lambda: self.on_compute_cgh(slmKey, secKey))

        plotCghPerfBtn.clicked.connect(lambda: self.sigVisualizeCghPerformances.emit(slmKey, secKey))
        visualizeTargetBtn.clicked.connect(lambda: self.on_visualize_target(slmKey, secKey))
        showResultBtn.clicked.connect(lambda: self.sigShowCghResult.emit(
            slmKey, secKey, int(padSizeValue.text())))
        
        loadPatternBtn.clicked.connect(lambda: self.sigLoadCgh.emit(slmKey, secKey))
        saveCghBtn.clicked.connect(lambda: self.sigSaveCgh.emit(slmKey, secKey))

        return group



    # ----------------------------------- #
    #   Explicit UI BUILDER FUNCTIONS     #
    # ----------------------------------- #

    def create_cgh_bfp_widget(self, slmKey="slm", secKey="sec_0"):
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
        self.add_param_grid(slmKey, secKey, "cgh", params, 0, layout, per_row=2, width=60, sub_section="bfp_spots")
        return widget


    def create_cgh_multifoci_widget(self, slmKey="slm",secKey="sec_0"):
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
        self.add_param_grid(slmKey,secKey,"cgh", params, 0, layout, per_row=2, width=60,sub_section="multi_foci")
        return widget




    # ------------------------------------- #
    #       UI-BUILD HELPER FUNCTIONS       #
    # ------------------------------------- #


    def add_param_grid(self, slmKey, secKey,section_name, params, start_row, layout,sub_section=None,
                       per_row="all", width=60):
        """
        Add parameters to a QGridLayout, set the corresponding attributes on self, and update self._param_definitions.
        
        IMPORTANT NOTES:
        ----------------
        1/ `params` is a list of tuples defining each parameter with 3 or 4 elements:
            - (ptype, label, default_or_items, attrname), or:
            - (ptype, label, default_or_items) ==> attrname will be derived from label.
            where ptype is one of: "label", "checkbox", "lineedit", "combo".

        2/ attribute naming convention: 
                slmkey_secKey_[sub_section]_attrname
                e.g. "slm1_sec_0_binary_period_x"

        3/ the parameter is stored in self._param_definitions at:
                self._param_definitions[slmKey][secKey][section_name][sub_section] (sub_section optional)

            with paramName being the cleaned attrname without slmKey, secKey, section or sub_section prefixes.

            e.g.: self._param_definitions["slm1"]["sec_0"]["patterns"]["binary"] = "period_x"

        Parameters:
        ----------
        Mandatory:
            slmKey: identifier for the SLM.
            secKey: identifier for the tab section.
            section_name: name of the section (e.g. "patterns", "cgh", etc.)
            params: list of parameter definitions.
            start_row: row index to start adding parameters.
            layout: QGridLayout instance where parameters will be added.

        Optional:
            sub_section: optional sub-section name for grouping parameters.
            per_row: number of parameters per row, or "all" for single column layout.
            width: fixed width for line edit widgets.


        Returns:
        -------
        row: the next free row index after adding the parameters.

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

            # clean display label
            label = make_display_name(label)

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

                # full attribute name construction
                attr_parts = [slmKey, secKey]
                if sub_section is not None:
                    attr_parts.append(sub_section)
                attr_parts.append(attrname)
                full_attrname = clean_attr_name("_".join(attr_parts))

                # set attribute on self
                setattr(self, full_attrname, widget)

                # cleaned param name for storage in definitions
                paramName = clean_attr_name(attrname)
                # add to param definitions
                if section_name is None:
                    continue # skip if no section defined

                target_dict = self._param_definitions[slmKey][secKey].setdefault(section_name, {})
                if sub_section:
                    target_dict = target_dict.setdefault(sub_section, [])

                target_dict.append(
                    (ptype,label,default_or_items,paramName)
                )

        # Return the next free row
        if col>0:
            row+=1

        return row


    def add_generic_pattern(self, layout, row, slmKey, secKey, section_name, pattern_name, param_defs,
                          add_checkbox=True, single_param_mode = False, use_subsection=True,per_row="all"):
        
        """
        Auto-generate UI for a pattern using its registered param metadata, such as ("period_x", 0, "int"), 
        by preparing parameters to be sent to `add_param_grid`.
        
        IMPORTANT NOTES:
        ----------------

        1/ `single_param_mode` is used for patterns that have a single coefficient parameter only, e.g. Zernike modes:
            Horizontal Coma: [   ]
            Vertical Coma: [   ]
            ...

        2/ the widget type is deduced from the parameter type (ptype) in the registry, e.g.:
            - "float" or "int"  ==> lineedit
            - "choice"          ==> combo

        3/ certain parameters are hard-coded to be ignored (e.g. "wavelength_nm", "pixel_size_um"): those are parameters
        present in the registry because they are needed for the pattern computation, but already defined elsewhere in the
        UI (wavelength) or config file (pixel size).

        4/ if `use_subsection` is True, the pattern_name is used as sub-section name in the param_definitions structure.
        e.g.: ["slm1"]["sec_0"]["patterns"]["lens_phase"] 

        """

        
        _ignore = ["wavelength_nm","pixel_size_um"]  # patternparameters to ignore
        params = []

        # Add pattern activation checkbox
        if add_checkbox:
            params = [("checkbox", pattern_name, None, "active")]

        # Add one row per parameter
        for param_name, default, ptype in param_defs:

            if param_name in _ignore:
                continue

            if single_param_mode:
                param_name = pattern_name

            if ptype in ("float", "int",float, int):
                params.append(("lineedit", param_name, default, param_name))
            elif ptype == "choice":
                # Expect default to be a list of options
                params.append(("combo", param_name, default, param_name))
            else:
                # Fallback to string line edit
                params.append(("lineedit", param_name, str(default), param_name))

        sub_section = pattern_name if use_subsection else None

        # Add grid to layout, set attribute and update param definitions with add_param_grid
        row = self.add_param_grid(
            slmKey, secKey, section_name, params, row, layout,
            per_row=per_row, sub_section=sub_section
        )

        return row



    # ------------------------------------- #
    #       PARAMS GET/SET FUNCTIONS        #
    # ------------------------------------- #

    def get_params(self):
        """ Gather all parameter values from the UI widgets according to
        the meta-structure stored in self._param_definitions."""

        all_params = {}
        for slmKey, tab_dict in self._param_definitions.items():
            all_params[slmKey] = {}

            for secKey, section_dict in tab_dict.items():
                all_params[slmKey][secKey] = {}

                for section_name, param_list in section_dict.items():
                    section_values = {}

                    if isinstance(param_list, dict): # sub-sections
                        sub_section_dict = param_list
                        for sub_section_name, sub_section_param_list in sub_section_dict.items():
                            sub_section_values = {}
                            for ptype, _, _, attrname in sub_section_param_list:
                                val = self.get_widget_value(slmKey, secKey, f"{sub_section_name}_{attrname}", ptype)
                                if val is None:
                                    continue
                                sub_section_values[attrname] = val
                            
                            section_values[sub_section_name] = sub_section_values

                    else: # regular section
                        for ptype, _, _, attrname in param_list:
                            val = self.get_widget_value(slmKey, secKey, attrname, ptype)
                            if val is None:
                                continue

                            section_values[attrname] = val

                    all_params[slmKey][secKey][section_name] = section_values

        return all_params


    def set_params(self, params_dict):
        """
        Restore all parameter values into the UI widgets from a dictionary
        matching the structure returned by get_params().
        """
        for slmKey, tab_dict in params_dict.items():
            if slmKey not in self._param_definitions:
                self.__logger.warning(f"SLM key '{slmKey}' not found in param definitions, skipping...")
                continue

            for secKey, section_dict in tab_dict.items():
                if secKey not in self._param_definitions[slmKey]:
                    continue

                for section_name, param_values in section_dict.items():
                    if section_name not in self._param_definitions[slmKey][secKey]:
                        continue
                    
                    if isinstance(self._param_definitions[slmKey][secKey][section_name], dict): # sub-sections
                        sub_section_dict = param_values 
                        for sub_section_name, sub_section_param_values in sub_section_dict.items():
                            if sub_section_name not in self._param_definitions[slmKey][secKey][section_name]:
                                continue
                            for ptype, _, _, attrname in self._param_definitions[slmKey][secKey][section_name][sub_section_name]:
                                if attrname not in sub_section_param_values:
                                    continue
                                
                                self.set_widget_value(slmKey, secKey, f"{sub_section_name}_{attrname}", ptype, 
                                                    sub_section_param_values.get(attrname))

                    else: # regular section
                       for ptype, _, _, attrname in self._param_definitions[slmKey][secKey][section_name]:
                            if attrname not in param_values:
                                continue
                            self.set_widget_value(slmKey, secKey, attrname, ptype, param_values.get(attrname))


    def set_widget_value(self, slmKey, secKey, attrname, ptype, val):
        
        full_attrname = clean_attr_name(f"{slmKey}_{secKey}_{attrname}")
        widget = getattr(self, full_attrname, None)
        if widget is None:
            return

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

    def get_widget_value(self, slmKey, secKey, attrname, ptype):
        
        # Build the attribute name used in the class
        full_attrname = clean_attr_name(f"{slmKey}_{secKey}_{attrname}")

        widget = getattr(self, full_attrname, None)
        if widget is None:
            return None

        # Read the value according to widget type
        if ptype == "lineedit":
            val = widget.text()
            # try to convert to numeric
            try:
                val = json.loads(val)  
            except Exception:
                pass
            
        elif ptype == "checkbox":
            val = widget.isChecked()
        elif ptype == "combo":
            val = clean_attr_name(widget.currentText())
        elif ptype == "radio":
            val = widget.isChecked()
        else:
            val = None

        return val



    # ------------------------------------- #
    #       LOGIC HANDLING FUNCTIONS        #
    # ------------------------------------- #

    
    # --------- tab renaming --------
    def rename_tab(self,slmKey, tabWidget, index):
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
            keys = list(self._tab_names_dict[slmKey].keys())
            if index < len(keys):
                key = keys[index]
            self._tab_names_dict[slmKey][key] = new_name
    
    def update_tab_names(self,slmKey,tab_names):
        """Update the tab names in the UI based on the provided dictionary, used when loading a config file."""
        subtabs_widget = getattr(self, f"{slmKey}_subTabs", None)
        if subtabs_widget is None:
            return
        for i in range(subtabs_widget.count()):
            key = f"sec_{i}"
            if key in tab_names:
                new_name = tab_names[key]
                subtabs_widget.setTabText(i, new_name)
                self._tab_names_dict[slmKey][key] = new_name


    # --------- connection/disconnection --------
    def on_connection_result(self, slmKey: str, success: bool, serial: str):
        """Handle the result of a connection attempt."""
        btn = getattr(self, f"{slmKey}_connectBtn")
        if success:
            btn.setText("Disconnect")
            QtWidgets.QMessageBox.information(self, "SLM Connection", f"Successfully connected to SLM {serial}")
        else:
            btn.blockSignals(True)  # prevent re-emitting toggled
            btn.setChecked(False)
            btn.blockSignals(False)
            btn.setText("Connect to SLM")
            QtWidgets.QMessageBox.warning(self, "SLM Connection", f"Connection to {self._slmNames[slmKey]} failed.")
    
    def on_disconnection_result(self, slmKey: str, success: bool, msg: str):
        """Handle the result of a disconnection attempt."""
        btn = getattr(self, f"{slmKey}_connectBtn")
        if success:
            btn.setText("Connect to SLM")
            QtWidgets.QMessageBox.information(self, "SLM Disconnected", msg)
        else:
            btn.blockSignals(True)  # prevent re-emitting toggled
            btn.setChecked(True)
            btn.blockSignals(False)
            QtWidgets.QMessageBox.warning(self, "SLM Disconnection", msg)
    

    # --------- computing related --------- #
    def on_update_pattern(self, slmKey):
        """Gather pattern parameters and emit signal to update pattern on SLM."""
        all_params = self.get_params()
        params = all_params.get(slmKey, {})
        # add correction options
        apply_corr = getattr(self, f"{slmKey}_applyCorrectionCheck").isChecked()
        twopi_val_corr = getattr(self, f"{slmKey}_twopiCheck").isChecked()
        params["correction_options"] = {
            "apply_correction_pattern": apply_corr,
            "apply_twopi_value": twopi_val_corr
        }
        self.sigUpdatePattern.emit(slmKey, params)

    def on_compute_cgh(self,slmKey,secKey):
        """
        Gather CGH parameters, emits signal to compute CGH and 
        change state of ALL compute buttons. 
        """
        all_params = self.get_params()
        sec_params = all_params.get(slmKey, {}).get(secKey, {})
        cgh_params = sec_params.get("cgh", {})
        if not cgh_params:
            self.__logger.warning(f"No CGH parameters found for {slmKey}:{secKey}")
            self.on_cgh_computation_failed("No CGH parameters found.")
            return
        
        for slm,sectionsList in self._slmSectionList.items():
            for section in sectionsList:
                btn = getattr(self, f"{slm}_{section}_compute_cgh_btn", None)
                if btn:
                    btn.setText("Computing...")
                    btn.setEnabled(False)

        self.sigComputeCGH.emit(slmKey,secKey, cgh_params)
        
    
    def on_cgh_computation_result(self, slmKey,secKey, success, msg=None,cgh_name=None):
        """ Unblocks all compute buttons, update cgh label and optional msg display"""

        for slm,sectionsList in self._slmSectionList.items():
            for section in sectionsList:
                btn = getattr(self, f"{slm}_{section}_compute_cgh_btn", None)
                if btn:
                    btn.setText("Compute CGH")
                    btn.setEnabled(True)

        if success:
            cgh_name = "last computed" if cgh_name is None else cgh_name
            self.update_label(slmKey,secKey,"cgh_in_use_label",f"{cgh_name} (computed)")
            if msg is not None:
                self.show_message_box(title=f"CGH computation warning",
                                      message=msg,msg_type="warning")
                
        elif not success:
            self.show_message_box(title="CGH computation failed", message=msg,msg_type="error")
    
    # --------- saving/loading related -------- #

    def on_save_config(self, slmKey):
        """ Get all parameters and send signal to controller"""
        all_params = self.get_params()
        slm_params = all_params.get(slmKey, {})
        slm_params["tab_names"] = self._tab_names_dict.get(slmKey, {})
        self.sigSaveConfig.emit(slmKey,slm_params)
    
    def on_save_aberr(self,slmKey,secKey):
        # Get aberrations parameters
        all_params = self.get_params()
        slm_params = all_params.get(slmKey, {})
        sec_params = slm_params.get(secKey, {})
        aberr_params = sec_params.get("aberrations", {})
        self.sigSaveAberr.emit(slmKey,secKey,aberr_params)
    
    def on_config_loaded(self, slmKey, slm_params, msg_box=False):
        try:
            self.set_params({slmKey: slm_params})
            tab_names = slm_params.get("tab_names", {})
            if tab_names:
                self.update_tab_names(slmKey, tab_names)

        except Exception as e:
            self.__logger.error(f"Failed to load config: {e}")
            if msg_box:
                self.show_message_box(title="Error Loading Configuration",
                                      message=f"Could not load configuration:\n{e}",
                                      msg_type="error")   
    def on_aberr_loaded(self,slmKey,secKey,aberr_params,label_name,msg_box=False):
        try:
            self.set_params({slmKey: {secKey: {"aberrations": aberr_params}}})
            self.update_label(slmKey,secKey,"load_aberrations_label",f"Loaded: {label_name}")

        except Exception as e:
            self.__logger.error(f"Failed to load aberrations: {e}")
            if msg_box:
                self.show_message_box(title="Error Loading Aberrations",
                                      message=f"Could not load aberrations:\n{e}",
                                      msg_type="error")

    def update_label(self,slmKey,secKey,attr_suffix,label):
        label_widget = getattr(self,f"{slmKey}_{secKey}_{attr_suffix}",None)
        if label_widget:
            label_widget.setText(label)
        else:
            self.__logger.debug(f"Cannot find attribute {slmKey}_{secKey}_{attr_suffix}")
        



    # --------- display related --------
    def update_display(self, slmKey="slm", pattern=None):
        """
        Update the SLM display with a 2D numpy array.
        """
        if pattern is None:
            return

        if not isinstance(pattern, np.ndarray) or pattern.ndim != 2:
            raise ValueError("Pattern must be a 2D numpy array (grayscale)")

        img = getattr(self, f"{slmKey}_img")
        img.setImage(pattern, autoLevels=True)

        # Save current pattern for zooming reference
        setattr(self, f"{slmKey}_currentPattern", pattern)

    def mouseMoved(self, pos, slmKey="slm"):
        vb = getattr(self, f"{slmKey}_vb")
        img = getattr(self, f"{slmKey}_img")
        pixelLabel = getattr(self, f"{slmKey}_pixelLabel")

        mouse_point = vb.mapSceneToView(pos)
        x = int(mouse_point.x())
        y = int(mouse_point.y())

        data = img.image
        if data is not None and 0 <= x < data.shape[1] and 0 <= y < data.shape[0]:
            value = data[y, x]
            pixelLabel.setPlainText(f"({x}, {y}) = {value:.2f}")
        else:
            pixelLabel.setPlainText("")
    
    def on_image_preview_toggled(self,slmKey,checked):
        for key in self._slmNames.keys():
            if key == slmKey:
                continue
            else:
                imagePreview = getattr(self,f"{key}_imageSection")
                imagePreview.toggleButton.setChecked(checked)
                imagePreview._on_pressed()

            # force layout update
            tab_widget = self._slm_widgets[key]
            tab_widget.setUpdatesEnabled(False)
            tab_widget.adjustSize()
            tab_widget.updateGeometry()
            tab_widget.setUpdatesEnabled(True)

    def reset_view(self, key):
        vb = getattr(self, f"{key}_vb")
        img = getattr(self, f"{key}_img")
        pattern = getattr(self, f"{key}_currentPattern")

        if pattern is None:
            return

        img.setImage(pattern, autoLevels=False)
        vb.autoRange()

    
        
    # ----- plots and displays ----- #
    def on_visualize_target(self, slmKey, secKey):
        """Get target params and emits signal to request target visualization."""
        all_params = self.get_params()
        cgh_params = all_params.get(slmKey, {}).get(secKey, {}).get("cgh", {})
        target_type = cgh_params.get("cgh_general", {}).get("target_type", None)
        if target_type is None:
            return
        target_params = cgh_params.get(target_type, None)
        if target_params is None:
            return
        self.sigVisualizeTarget.emit(target_type, target_params)

    def plot_target(self,target):
        """Show target."""
        if target is None:
            return
        plt.figure("Target", figsize=(8, 5))
        plt.clf()
        plt.imshow(target, cmap='gray')
        plt.tight_layout()
        plt.show(block=False)

    def plot_cgh_performances(self,performances):
        """
        Plot efficiency, uniformity, and std vs iteration from a list of performance tuples.

        Parameters
        ----------
        performances : list of tuple(float, float, float)
            A list where each element is (efficiency, uniformity, std)
            for each iteration.
        """
        if not performances:
            self.__logger.debug("No performance data to plot.")
            self.show_message_box("No performance data to plot.", msg_type="warning")
            return
        
        efficiencies = [p[0] for p in performances]
        uniformities = [p[1] for p in performances]
        stds = [p[2] for p in performances]
        iterations = range(1, len(performances) + 1)

        plt.figure("Performances", figsize=(8, 5))
        plt.clf()
        plt.plot(iterations, efficiencies, label="Efficiency")
        plt.plot(iterations, uniformities, label="Uniformity")
        plt.plot(iterations, stds, label="STD")

        plt.title("Performance Metrics per Iteration")
        plt.xlabel("Iteration")
        plt.ylabel("Value")
        plt.legend()
        plt.tight_layout()
        
        plt.show(block=False)
    
    def plot_cgh_result(self,result):
        """Plot the resulting CGH pattern."""
        if result is None:
            self.show_message_box("No CGH result to plot.", msg_type="warning")
            return
        plt.figure("Expected CGH Result in sample plane", figsize=(8, 5))
        plt.clf()
        plt.imshow(result, cmap='gray')
        plt.title("FFT of CGH Pattern")
        plt.tight_layout()
        plt.show(block=False)

    

    # general msg box function
    def show_message_box(self, message: str, msg_type: str = "info", title=None):
        """Show a message box with the given title and message."""
        if title is None:
            title = "SLM Control"

        # title = f"<b>{title}<b>"
        if isinstance(message, Exception):
            message = str(message)

        if msg_type == "warning":
            QtWidgets.QMessageBox.warning(self, title, message)
        elif msg_type == "error":
            QtWidgets.QMessageBox.critical(self, title, message)
        else:
            QtWidgets.QMessageBox.information(self, title, message)

# ------------------------------------------------------------------ #
#       Helper functions to clean displayed/attributes names         # 
# ------------------------------------------------------------------ #
 
def clean_attr_name(label: str) -> str:
    """
    Convert a label string to a valid attribute name:
    - lowercase
    - replace spaces and parentheses with underscores
    - remove other non-alphanumeric/underscore characters
    - collapse multiple underscores into one
    """
    # remove parentheses but keep content
    label = label.replace("(", "").replace(")", "")
    # remove any non-alphanumeric/underscore/hyphen/space chars
    label = re.sub(r"[^0-9a-zA-Z_ \-]", "", label)
    # replace spaces and hyphens with underscores
    label = label.replace(" ", "_")
    label = label.replace("-", "_")
    # collapse multiple underscores into a single underscore
    label = re.sub(r"_+", "_", label)
    # lowercase
    label = label.lower()
    return label


def make_display_name(param_name: str) -> str:
    """
    Convert an internal attribute/key name (e.g. 'focal_length_mm')
    into a user-friendly display name ('Focal Length (mm)').
    Leaves strings that already look like display names unchanged.
    """
    _units = {"mm", "um", "nm", "px", "degrees", "deg", "rad", "radians"}

    # --- If it's already formatted, just return as-is ---
    if " " in param_name or "(" in param_name or re.search(r"[A-Z].*[A-Z]", param_name):
        return param_name

    # --- Otherwise, convert snake_case to displayable form ---
    parts = param_name.split("_")
    display_parts = [
        f"({p})" if p.lower() in _units else p.capitalize()
        for p in parts if p
    ]
    return " ".join(display_parts)
