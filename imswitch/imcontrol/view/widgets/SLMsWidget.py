"""
SLMsWidget Notes
================
- One tab per SLM, multiple tabs for each section of the SLM (if applicable)
- SLM are referenced by their 'slmKey' (cleaned slmName)
- Section are referenced by 'secKey' (sec_0, sec_1, ...)
- Attributes and parameters are dynamically set based on slmKey and secKey, allowing a variable number of SLM and sections.
- A parameter registration system is used to keep track of all parameters exposed by the widget (see details below)
- New patterns can be added automatically via the pattern registry (imcontrol/controller/patterndesigners), or by creating custom builders.

------------------------------------------------------------
IMPORTANT: Parameter registration system (_param_definitions)
------------------------------------------------------------

All parameters exposed by the widget are registered in:
    self._param_definitions[slmKey][secKey]

NOTE: It is crucial to correctly register parameters in the `_param_definitions` structure.
It is used to loop over all parameters for saving/loading configurations, and for pattern updates.

The structure is:
    _param_definitions = {
        slmKey: {
            secKey: {
                groupName: {
                    subsection:
                        [(widget_type, attr_name), (widget_type, attr_name),... ] # list of parameters
                }
            }
        }
    }

Where:
- groupName : parameter group (e.g. "pattern", "aberrations", "output")
- subsection : optional further subdivision inside group (e.g. pattern name, "cgh_general", "cgh_computation")
- each parameter is defined by a tuple:
    * widget_type : one of ("checkbox", "combobox", "lineedit", ...)
    * attr_name : used to reference parameter
        ==> we expect to find it as self.[slmKey]_[secKey]_[subsection]_[attr_name]

        NOTE: the groupName is not used in the attribute name. This choice was made because it is redudant with
        the subsection name or the attribute name (e.g. self._slmKey_sec_key_general_wavelength ==> "general" not needed)

There are two ways of registering parameters:
    1. Automatic registration via add_param_grid(), which:
            * creates standard UI elements
            * register them in self_param_definitions
            * create corresponding attributes
            * connect widget changes to automatic pattern update scheduling (unless auto_update=False is given)
            * if lineedit, can also set validator based on valtype (int or float for now)

    2. Manual registration - for custom UI elements.
    In that case, you need to make sure that the param_definitions entries match the created attributes.
    e.g., for a checkbox named "use_correction", in the "correction_options" section:
            - create attribute: 
                    self.slmKey_secKey_use_correction
            - register param: 
                    self._param_definitions[slmKey][secKey]["correction_options"] = ("checkbox", "use_correction")

        /!\ Don't forget to connect the widget changes to self._schedulePatternUpdate(slmKey) to trigger pattern updates.
"""



from qtpy import QtCore, QtWidgets, QtGui
from imswitch.imcontrol.view.guitools import CollapsibleSection, BetterPushButton
from imswitch.imcommon.view.guitools.dialogtools import askForTextInput,askYesNoQuestion,askForTwoTextInputs
import pyqtgraph as pg
from .basewidgets import Widget
from imswitch.imcommon.model import initLogger
import re
import json
import numpy as np
import matplotlib.pyplot as plt
from functools import partial
import h5py
import os
import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from imswitch.imcontrol.model.SetupInfo import SLMInfo

_collaps_section_format = {
    "button_height": 20,
    "fontsize": 9,
}

# debounce time for SLM refresh when changing parameter
_DEBOUNCE_TIME = 800 # 800ms


class SLMsWidget(Widget):
    """Widget containing SLM interface, patterns, and CGH controls."""

    _transparentToolButtonStyle = """
        QToolButton {
            border: none;
            background: transparent;
        }
        QToolButton:hover {
            background: transparent;
        }
        QToolButton:pressed {
            background: transparent;
        }
    """

    inspectDialogFontPointSize = 10

    sigConnectSLMusb = QtCore.Signal(str,bool,bool)         # slmName, state, display_msg
    sigUpdatePattern = QtCore.Signal(str, dict)             # slmKey, params
    sigComputeCGH = QtCore.Signal(str, str,dict)            # slmKey, secKey, cgh_params

    sigVisualizeCghPerformances = QtCore.Signal(str, str)   # slmKey, secKey
    sigVisualizeTarget = QtCore.Signal(str,str)             # slmKey, secKey, target_type, target_params
    sigShowCghResult = QtCore.Signal(str, str, int)         # slmKey, secKey, pad_size

    sigDeleteConfig = QtCore.Signal(str,str)                # slmKey, config path
    sigRenameConfig = QtCore.Signal(str,str,str)            # slmKey, old name, new name
    sigDuplicateConfig = QtCore.Signal(str,str,str)         # slmKey, config path, new name
    sigSetStartupConfig = QtCore.Signal(str,str)            # slmKey, config path
    sigOpenConfigFolder = QtCore.Signal(str)                # slmKey
    sigLoadConfig = QtCore.Signal(str,str)                  # slmKey, config path
    sigLoadAberr = QtCore.Signal(str,str)                   # slmKey, secKey
    sigLoadCgh = QtCore.Signal(str, str)                    # slmKey, secKey
    sigSaveConfig = QtCore.Signal(str,str,str,bool)         # slmKey, config name, info, overwrite
    sigSaveAberr = QtCore.Signal(str,str,dict)              # slmKey, secKey, aberr_params
    sigSaveCgh = QtCore.Signal(str, str)                    # slmKey, secKey

    sigSnapFeedback = QtCore.Signal(str,str)                # slmKey, secKey
    sigAnalysisFeedback = QtCore.Signal(str,str)            # slmKey, secKey
    sigUpdateTarget = QtCore.Signal(str,str)                # slmKey, secKey
    sigResetFeedback = QtCore.Signal(str,str)               # slmKey, secKey
    sigAnalysisFeedbackPrm = QtCore.Signal(str,str)         # slmKey, secKey
    sigLoadFeedback = QtCore.Signal(str,str)                # slmKey, secKey

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
        self._currentConfigs = {}       # {slmKey: {"path": currentConfigPath, "date": date, "info": info}}

        # update timers
        self._slmUpdateTimers = {}      # { slmKey: QTimer }


    def add_slm(self,slmName: str,slmInfo: "SLMInfo", full_registry: dict,
                device_connection: bool = False,*args,**kwargs):
        
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
        slmLayout.setSpacing(3)
        slmLayout.setContentsMargins(0, 0, 0, 0)

        # middle container (scroll area)
        middlecontainer = QtWidgets.QWidget()
        middlelayout = QtWidgets.QVBoxLayout(middlecontainer)
        middlelayout.setContentsMargins(3, 3, 3, 3)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scrollArea.setWidget(middlecontainer)
        scrollArea.setWidgetResizable(True)

        # top control => added to slmLayout
        self.create_top_controls(slmLayout,slmKey=slmKey,add_connect_btn=device_connection)

        # image preview and tabs => added to middlelayout (scroll area)
        self.create_image_display(middlelayout,slmKey=slmKey)
        self.build_tab_section(middlelayout,slmKey=slmKey,n_tabs=slmInfo.nSections,
                            options=slmInfo.widgetOptions,full_registry=full_registry)
        slmLayout.addWidget(scrollArea)

        # finally: add to slmTabs
        slmContainer.setLayout(slmLayout)
        self.slmTabs.addTab(slmContainer,slmName) # here we give the original slmName to be displayed
        self._slm_widgets[slmKey] = slmContainer

        return slmKey
    
    # -------------------------------------------- #
    #           SLM SECTION TABS BUILDERS          #
    # -------------------------------------------- #

    def build_tab_section(self, parent_layout, slmKey="slm", n_tabs=1,
                          options={}, full_registry={}):
        """
        Create N sub-tabs (e.g. for double-pass left/right).
        If N == 1, just builds the single SLM section directly.
        """
        if n_tabs is None:
            n_tabs = 1
            tab_names = ["Full SLM"]

        else:
            tab_names = [f"Section {i+1}" for i in range(n_tabs)]
        
        subTabs = QtWidgets.QTabWidget()
        subTabs.setDocumentMode(True)
        sectionsList = []
        for i,name in enumerate(tab_names):
            secKey = f"sec_{i}" #NOTE: sec_*number* is also used in patternEngine to reference sections
            sectionsList.append(secKey)
            self._tab_names_dict[slmKey][secKey] = name
            section_options = options[secKey] if secKey in options else options # allows per section options, or common options for all sections 
            section_widget = self.create_slm_section(slmKey,secKey,section_options,full_registry)
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
            vbox.addWidget(self.create_cgh_group(slmKey,secKey,full_registry.get("cgh_targets")))

        # final correction options
        self._param_definitions[slmKey][secKey]["correction_options"]=[]
        vbox.addWidget(self.create_correction_options_group(slmKey,secKey))

        vbox.addStretch()
        return container
    
    
    # -------------------------------------------- #
    #           GENERAL CONTROLS PANELS            #
    #  Connection, Image Display, Update Pattern   #
    # -------------------------------------------- #
        
    # --- 1. Top Controls (Connect, Config management) ----
    def create_top_controls(self, parent_layout, slmKey="slm", add_connect_btn=True):
        """
        Create the top control row for a single SLM:
        Connect button (if requested) + Config selector + Load / Save buttons.
        """
        layout = QtWidgets.QHBoxLayout()

        # Connect button
        if add_connect_btn:
            connectBtn = BetterPushButton("Connect to SLM")
            connectBtn.setCheckable(True)
            connectBtn.setFixedHeight(20)
            setattr(self, f"{slmKey}_connectBtn", connectBtn)
            layout.addWidget(connectBtn)
        
        layout.addStretch()

        # Save / Load configs
        configLabel = QtWidgets.QLabel("Config:")
        layout.addWidget(configLabel)

        configCombo = QtWidgets.QComboBox()
        configCombo.setMinimumWidth(180)
        configCombo.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        configCombo.view().setMouseTracking(True)
        configCombo.view().viewport().setMouseTracking(True)
        configCombo.wheelEvent = lambda event: None  # disable wheel event
        setattr(self, f"{slmKey}_configCombo", configCombo)
        layout.addWidget(configCombo)

        # Info button
        infoBtn = QtWidgets.QToolButton()
        infoBtn.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation)
        )
        infoBtn.setAutoRaise(True)
        infoBtn.setFixedSize(18, 18)
        infoBtn.setToolTip("Open config inspector")
        infoBtn.setStyleSheet(self._transparentToolButtonStyle)
        setattr(self, f"{slmKey}_infoBtn", infoBtn)
        layout.addWidget(infoBtn)

        reloadBtn = QtWidgets.QToolButton()
        reloadBtn.setIcon(
            self.style().standardIcon(
                getattr(QtWidgets.QStyle, "SP_BrowserReload", QtWidgets.QStyle.SP_ArrowRight)
            )
        )
        reloadBtn.setAutoRaise(True)
        reloadBtn.setFixedSize(22, 22)
        reloadBtn.setToolTip("Reload selected config")
        reloadBtn.setStyleSheet(self._transparentToolButtonStyle)
        setattr(self, f"{slmKey}_reloadBtn", reloadBtn)
        layout.addWidget(reloadBtn)

        updateBtn = BetterPushButton("Update Config")
        updateBtn.setFixedHeight(20)
        setattr(self, f"{slmKey}_updateConfigBtn", updateBtn)
        layout.addWidget(updateBtn)

        # "More..." menu
        moreBtn = QtWidgets.QToolButton()
        moreBtn.setText("More")
        moreBtn.setFixedHeight(20)
        moreBtn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        setattr(self, f"{slmKey}_moreBtn", moreBtn)
        layout.addWidget(moreBtn)

        menu = QtWidgets.QMenu(moreBtn)
        saveAsAction = menu.addAction("Save as...", lambda p=slmKey: self.on_save_new_config_clicked(p))
        menu.addSeparator()
        renameAction = menu.addAction("Rename config...", lambda p=slmKey: self.on_rename_config(p))
        duplicateAction = menu.addAction("Duplicate config...", lambda p=slmKey: self.on_duplicate_config(p))
        deleteAction = menu.addAction("Delete config", lambda p=slmKey: self.on_delete_config(p))
        menu.addSeparator()
        startupAction = menu.addAction("Set as startup config", lambda p=slmKey: self.on_set_startup_config(p))
        openFolderAction = menu.addAction("Open config folder", lambda p=slmKey: self.sigOpenConfigFolder.emit(p))
        menu.addSeparator()
        settingsAction = menu.addAction("Settings...", lambda p=slmKey: self.show_config_settings_dialog(p))
        setattr(self, f"{slmKey}_saveAsAction", saveAsAction)
        setattr(self, f"{slmKey}_renameAction", renameAction)
        setattr(self, f"{slmKey}_duplicateAction", duplicateAction)
        setattr(self, f"{slmKey}_deleteAction", deleteAction)
        setattr(self, f"{slmKey}_startupAction", startupAction)
        setattr(self, f"{slmKey}_openFolderAction", openFolderAction)
        setattr(self, f"{slmKey}_settingsAction", settingsAction)
        moreBtn.setMenu(menu)
        moreBtn.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        parent_layout.addLayout(layout)

        # signal connections
        if add_connect_btn:
            connectBtn.toggled.connect(lambda state, p=slmKey: self.sigConnectSLMusb.emit(p, state, True))
        configCombo.currentIndexChanged.connect(lambda index, p=slmKey: self._on_config_index_changed(p, index))
        configCombo.activated.connect(lambda _, p=slmKey: self.on_config_selection_changed(p))
        infoBtn.clicked.connect(lambda _, p=slmKey: self.showInspectConfigsDialog(p))
        reloadBtn.clicked.connect(lambda _, p=slmKey: self.on_reload_config_clicked(p))
        updateBtn.clicked.connect(lambda _, p=slmKey: self.on_update_current_config_clicked(p))
        self._update_config_controls(slmKey)



    # ---- 2. Image Display (Collapsible) ----
    def create_image_display(self, parent_layout, slmKey="slm"):
        """
        Create a pyqtgraph-based SLM image display with zoom, LUT, and pixel readout.
        """
        # Collapsible section
        imageSection = CollapsibleSection("SLM Preview", target_height=200,frame=False, **_collaps_section_format)
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
        homeBtn.setFixedHeight(16)
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


    # -------------------------------------------- #
    #           SPECIFIC GROUP BUILDERS:           #   
    #      General, Patterns, Aberrations, CGH     #
    # -------------------------------------------- #

    # Correction options
    def create_correction_options_group(self, slmKey="slm",secKey="sec_0"):
        group = CollapsibleSection("Correction",**_collaps_section_format)
        layout = QtWidgets.QGridLayout()
        params = [
            ('checkbox', 'Apply correction pattern', True),
            ('checkbox', 'Apply 2π value correction', True, "apply_twopi_value"),
        ]
        self.add_param_grid(slmKey, secKey,"correction_options",params, 0, layout, per_row=0)
        group.setContentLayout(layout)
        return group

    # General section
    def create_general_group(self,slmKey="slm",secKey="sec_0"):
        group = CollapsibleSection("General",**_collaps_section_format)
        layout = QtWidgets.QGridLayout()
        params = [
            ('lineedit','Wavelength (nm)','488', 'Wavelength (nm)', int),
            ('lineedit','Pupil Radius (px)', 0, 'Pupil Radius (px)', int),
            ('lineedit','Center Offset X (px)', 0, 'Center Offset X (px)', int),
            ('lineedit','Center Offset Y (px)', 0, 'Center Offset Y (px)', int),
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

        group = CollapsibleSection("Patterns",**_collaps_section_format)
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
        group = CollapsibleSection("Aberrations",**_collaps_section_format)
        layout = QtWidgets.QGridLayout()
        row = 0

        # checkbox to easily activate/deactivate correction
        use_aberr = QtWidgets.QCheckBox("Apply aberrations correction")
        group.addHeaderWidget(use_aberr)
        setattr(self, f"{slmKey}_{secKey}_aberrations_active", use_aberr)
        self._param_definitions[slmKey][secKey]["aberrations"].append(
            ("checkbox","aberrations_active")
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
    def create_cgh_group(self, slmKey="slm",secKey="sec_0",registry=None):

        # NOTE: general cgh parameters stored in subsection "cgh_general":
        # ==> related attributes will be named accordingly:
        # self.{slmKey}_{secKey}_cgh_general_{attrname}

        group = CollapsibleSection("CGH Pattern",**_collaps_section_format)
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
            ("checkbox","active")
        )

        # --- 2. Target Definition Area ---
        targetBox = QtWidgets.QGroupBox("Target Definition")
        targetLayout = QtWidgets.QVBoxLayout(targetBox)

        # target type + visualize button
        targets_list=[make_display_name(target_name) for target_name in registry.keys()]
        typeLayout = QtWidgets.QHBoxLayout()
        typeLayout.addWidget(QtWidgets.QLabel("Target Type:"))
        combo = QtWidgets.QComboBox()
        combo.addItems(targets_list)
        setattr(self, f"{slmKey}_{secKey}_{generalsubsec}_target_type", combo)
        typeLayout.addWidget(combo)

        self._param_definitions[slmKey][secKey]["cgh"][generalsubsec].append(
            ("combo","target_type"),
        )

        visualizeTargetBtn = BetterPushButton("Visualize Target")
        setattr(self, f"{slmKey}_{secKey}_cgh_visualize_target_btn", visualizeTargetBtn)
        typeLayout.addWidget(visualizeTargetBtn)
        typeLayout.addStretch()
        targetLayout.addLayout(typeLayout)

        # target parameters based on registry
        stack = QtWidgets.QStackedWidget()
        setattr(self, f"{slmKey}_{secKey}_cghParamStack", stack)

        for target_name,infos in registry.items():
            _widget = QtWidgets.QWidget()
            layout = QtWidgets.QGridLayout(_widget)
            row = self.add_generic_pattern(layout, 0, slmKey, secKey, "cgh",target_name,infos["params"],
                                    add_checkbox=False, per_row=2,auto_update=False)
            if infos.get("feedback",False):
                spacer = QtWidgets.QSpacerItem(0, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
                layout.addItem(spacer, row, 0)
                self.add_feedback_buttons(layout,row,slmKey,secKey,target_name)
            stack.addWidget(_widget)

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
        weightedgsCheckbox=QtWidgets.QCheckBox("Weighted-GS")
        weightedgsCheckbox.setChecked(True)
        niterEdit = QtWidgets.QLineEdit("50")
        niterEdit.setFixedWidth(50)
        phaseFixingCheckbox = QtWidgets.QCheckBox("Phase fixing")
        phaseFixingCheckbox.setChecked(True)
        phaseFixingValue = QtWidgets.QLineEdit("30")
        phaseFixingValue.setFixedWidth(50)

        quadPhaseCheckBox = QtWidgets.QCheckBox("Quad. Init. Phase")
        quadPhaseCoeff = QtWidgets.QLineEdit("0.004")
        quadPhaseCoeff.setFixedWidth(50)

        setattr(self, f"{slmKey}_{secKey}_{computsubsec}_weighted_gs", weightedgsCheckbox)
        setattr(self, f"{slmKey}_{secKey}_{computsubsec}_n_iterations", niterEdit)
        setattr(self, f"{slmKey}_{secKey}_{computsubsec}_phase_fixing", phaseFixingCheckbox)
        setattr(self, f"{slmKey}_{secKey}_{computsubsec}_phase_fixing_value", phaseFixingValue)
        setattr(self, f"{slmKey}_{secKey}_{computsubsec}_quad_phase", quadPhaseCheckBox)
        setattr(self, f"{slmKey}_{secKey}_{computsubsec}_quad_phase_coeff", quadPhaseCoeff)


        # params layout
        paramsLayout = QtWidgets.QVBoxLayout()

        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(weightedgsCheckbox)
        row1.addWidget(QtWidgets.QLabel("Iterations:"))
        row1.addWidget(niterEdit)
        row1.addWidget(phaseFixingCheckbox)
        row1.addWidget(QtWidgets.QLabel("Phase:"))
        row1.addWidget(phaseFixingValue)
        row1.addStretch()

        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(quadPhaseCheckBox)
        row2.addWidget(QtWidgets.QLabel("Coeff:"))
        row2.addWidget(quadPhaseCoeff)
        row2.addStretch()

        paramsLayout.addLayout(row1)
        paramsLayout.addLayout(row2)
        computeLayout.addLayout(paramsLayout)
        cghLayout.addWidget(computeBox)

        self._param_definitions[slmKey][secKey]["cgh"][computsubsec].extend([
            ("checkbox","weighted_gs"),
            ("lineedit","n_iterations"),
            ("checkbox","phase_fixing"),
            ("lineedit","phase_fixing_value"),
            ("checkbox","quad_phase"),
            ("lineedit","quad_phase_coeff"),
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
        visualizeTargetBtn.clicked.connect(lambda: self.sigVisualizeTarget.emit(slmKey, secKey))
        showResultBtn.clicked.connect(lambda: self.sigShowCghResult.emit(
            slmKey, secKey, int(padSizeValue.text())))
        
        loadPatternBtn.clicked.connect(lambda: self.sigLoadCgh.emit(slmKey, secKey))
        saveCghBtn.clicked.connect(lambda: self.sigSaveCgh.emit(slmKey, secKey))

        use_cgh_checkbox.stateChanged.connect(lambda state, key=slmKey: self._schedulePatternUpdate(key))

        return group

    def add_feedback_buttons(self, layout, row, slmKey, secKey, target_name):
        """
        Adds feedback controls in 3 rows for targets supporting adaptive feedback,
        grouped in a CollapsibleSection titled 'Feedback'.
        """
        section = CollapsibleSection("Feedback",**_collaps_section_format)
        grid = QtWidgets.QGridLayout()
        counter = QtWidgets.QLabel("Feedback Rounds: 0")
        counter.setStyleSheet("color: #888;")
        setattr(self, f"{slmKey}_{secKey}_cgh_{target_name}_feedback_counter", counter)
        setattr(self, f"{slmKey}_{secKey}_cgh_feedback_counter", counter)
        resetbtn = BetterPushButton("Reset")
        setattr(self, f"{slmKey}_{secKey}_cgh_reset", resetbtn)
        section.addHeaderWidget(counter)
        section.addHeaderWidget(resetbtn)

        resetbtn.clicked.connect(lambda: self.on_feedback_reset(slmKey,secKey))

        rows = [
                [("1. Acquire Result:", "acquire_label", None),
                ("Snap", "snap_btn", self.sigSnapFeedback),
                ("Load", "load_btn", self.sigLoadFeedback)],

                [("2. Result analysis:", "analysis_label", None),
                ("Analyze", "analyze_btn", self.sigAnalysisFeedback),
                ("Modify parameters","analysis_prm", self.sigAnalysisFeedbackPrm)],

                [("3. Update target w/ feedback:", "define_label", None),
                ("Update","update_target_btn", self.sigUpdateTarget)]
            ]

        for r, row_buttons in enumerate(rows):
            col = 1  # buttons start at column 1
            for label, attr_suffix, signal in row_buttons:
                if "label" in attr_suffix:
                    widget = QtWidgets.QLabel(label)
                    widget.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                    grid.addWidget(widget, r, 0)  # all labels in column 0
                else:
                    widget = BetterPushButton(label)
                    widget.setFixedWidth(120)
                    if signal is not None:
                        widget.clicked.connect(lambda _, s=signal, k=slmKey, c=secKey: s.emit(k, c))
                    grid.addWidget(widget, r, col)
                    col += 1
                    setattr(self, f"{slmKey}_{secKey}_cgh_{target_name}_{attr_suffix}", widget)

        section.setContentLayout(grid)
        layout.addWidget(section, row, 0, 1, -1)
        return row + 1


    # ------------------------------------- #
    #       UI-BUILD HELPER FUNCTIONS       #
    # ------------------------------------- #


    def add_param_grid(self, slmKey, secKey,section_name, params, start_row, layout,sub_section=None,
                       per_row="all", width=60,auto_update=True):
        """
        Add parameters to a QGridLayout, set the corresponding attributes on self, and update self._param_definitions.
        Also connects signals to update pattern automatically when changed, unless arg:`auto_update` is set to False.

        IMPORTANT NOTES:
        ----------------
        1/ arg:`params` is a list of tuples defining each parameter with 3, 4, or 5 elements:
            - (ptype, label, default_or_items)                      ==> attrname will be derived from label.
            - (ptype, label, default_or_items, attrname)            ==> attrname is explicitly given.
            - (ptype, label, default_or_items, attrname, valtype)   ==> valtype is the type to convert the value to, 
                                                                        only used for lineedit validators if specified.

            where:
                - ptype is one of: "label", "checkbox", "lineedit", "combo".
                - label is the display name shown in the UI.
                - default_or_items is either the default value (for lineedit/checkbox) or list of items (for combo).
                - attrname is the attribute name to be set on self

        2/ attribute naming convention: 
                slmkey_secKey_[sub_section]_attrname
                e.g. "slm1_sec_0_binary_period_x"

        3/ the parameter is stored in self._param_definitions:
                self._param_definitions[slmKey][secKey][section_name][sub_section*] = (ptype, attrname) 
                *sub_section is optional

            e.g.: 
                self._param_definitions["slm1"]["sec_0"]["patterns"]["binary"] = ("lineedit", "period_x")
                NOTE: we keep only (ptype, attrname), the only one needed to reference the attribute later.

        Parameters:
        ----------
        Mandatory:
            slmKey: identifier for the SLM.
            secKey: identifier for the tab section.
            section_name: name of the section (e.g. "patterns", "cgh", etc.). Can be set to None to skip param_definitions update.
            params: list of parameter definitions.
            start_row: row index to start adding parameters.
            layout: QGridLayout instance where parameters will be added.

        Optional:
            sub_section: optional sub-section name for grouping parameters.
            per_row: number of parameters per row, or "all" for single column layout.
            width: fixed width for line edit widgets.
            auto_update: wether to connect param to on_update_pattern when parameter changed


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
                valtype = None

            elif len(p)==4:
                ptype, label, default_or_items, attrname = p
                valtype = None
            elif len(p)==5:
                ptype, label, default_or_items, attrname, valtype = p
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
                if isinstance(default_or_items, bool):
                    widget.setChecked(default_or_items)
                if auto_update:
                    widget.stateChanged.connect(lambda state, 
                                                key=slmKey: self._schedulePatternUpdate(key))
                col += 1

            # LineEdit
            elif ptype == "lineedit":
                lbl = QtWidgets.QLabel(label + ":")
                widget = QtWidgets.QLineEdit(str(default_or_items))
                widget.setFixedWidth(width)

                validator = self._make_validator(valtype, widget) if valtype is not None else None
                if validator is not None:
                    widget.setValidator(validator)
                    widget.setProperty("valtype", valtype)

                layout.addWidget(lbl, row, col,1,1)
                layout.addWidget(widget, row, col + 1,1,1)
                if auto_update:
                    widget.textChanged.connect(
                        lambda text, slmKey=slmKey: self._lineEditUpdate(text, slmKey)
                        )
                col += 2
                

            # ComboBox
            elif ptype == "combo":
                lbl = QtWidgets.QLabel(label + ":")
                widget = QtWidgets.QComboBox()
                widget.addItems(default_or_items)
                layout.addWidget(lbl, row, col,1,1)
                layout.addWidget(widget, row, col + 1,1,1)
                if auto_update:
                    widget.currentIndexChanged.connect(lambda key=slmKey: self._schedulePatternUpdate(key))
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

                target_dict.append((ptype,paramName))

        # Return the next free row
        if col>0:
            row+=1

        return row


    def add_generic_pattern(self, layout, row, slmKey, secKey, section_name, pattern_name, param_defs,
                          add_checkbox=True, single_param_mode = False, use_subsection=True,per_row="all",
                          auto_update=True):
        
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

        5/ param_defs is a list of tuples defining each parameter with 3 or 4 elements:
            - (param_name, default_value, ptype).

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
            
            # define attribute name
            attr_name = pattern_name if single_param_mode else param_name

            if ptype in ("float", "int",float, int):
                clean_type = resolve_type(ptype) # ensure type is correct
                params.append(("lineedit", attr_name, default, attr_name, clean_type))
            elif ptype == "choice":
                # Expect default to be a list of options
                params.append(("combo", attr_name, default, attr_name))
            else:
                # Fallback to string line edit
                params.append(("lineedit", attr_name, str(default), attr_name))

        sub_section = pattern_name if use_subsection else None

        # Add grid to layout, set attribute and update param definitions with add_param_grid
        row = self.add_param_grid(
            slmKey, secKey, section_name, params, row, layout,
            per_row=per_row, sub_section=sub_section,auto_update=auto_update
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
                            for ptype, attrname in sub_section_param_list:
                                val = self.get_widget_value(slmKey, secKey, f"{sub_section_name}_{attrname}", ptype)
                                if val is None:
                                    continue
                                sub_section_values[attrname] = val
                            
                            section_values[sub_section_name] = sub_section_values

                    else: # regular section
                        for ptype, attrname in param_list:
                            val = self.get_widget_value(slmKey, secKey, attrname, ptype)
                            if val is None:
                                self.__logger.warning(
                                    f"Failed to get value for {slmKey}_{secKey}_{attrname} ({ptype}), skipping..."
                                )
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
                            for ptype, attrname in self._param_definitions[slmKey][secKey][section_name][sub_section_name]:
                                if attrname not in sub_section_param_values:
                                    continue
                                
                                self.set_widget_value(slmKey, secKey, f"{sub_section_name}_{attrname}", ptype, 
                                                    sub_section_param_values.get(attrname))

                    else: # regular section
                       for ptype, attrname in self._param_definitions[slmKey][secKey][section_name]:
                            if attrname not in param_values:
                                continue
                            self.set_widget_value(slmKey, secKey, attrname, ptype, param_values.get(attrname))


    def set_widget_value(self, slmKey, secKey, attrname, ptype, val):
        
        full_attrname = clean_attr_name(f"{slmKey}_{secKey}_{attrname}")
        widget = getattr(self, full_attrname, None)
        if widget is None:
            return

        # --- Restore according to widget type ---
        combo_idx = -1
        try:
            with QtCore.QSignalBlocker(widget): # block signals to avoid triggering updates
                if ptype == "lineedit":
                    widget.setText(str(val))

                elif ptype == "checkbox":
                    widget.setChecked(bool(val))

                elif ptype == "combo":
                    # try to set by text if available
                    combo_idx = widget.findText(str(val))
                    if combo_idx < 0:
                        clean_val = clean_attr_name(str(val))
                        for idx in range(widget.count()):
                            if clean_attr_name(widget.itemText(idx)) == clean_val:
                                combo_idx = idx
                                break
                    if combo_idx >= 0:
                        widget.setCurrentIndex(combo_idx)

                elif ptype == "radio":
                    widget.setChecked(bool(val))

        except Exception as e:
            self.__logger.warning(
                f"Failed to set {full_attrname} ({ptype}) value: {val}. Error: {e}"
            )
            return

        if (
            ptype == "combo"
            and attrname == "cgh_general_target_type"
            and combo_idx >= 0
        ):
            stack = getattr(self, f"{slmKey}_{secKey}_cghParamStack", None)
            if stack is not None:
                stack.setCurrentIndex(combo_idx)

    def get_widget_value(self, slmKey, secKey, attrname, ptype):
        
        # Build the attribute name used in the class
        full_attrname = clean_attr_name(f"{slmKey}_{secKey}_{attrname}")

        widget = getattr(self, full_attrname, None)
        if widget is None:
            return None

        # Read the value according to widget type
        if ptype == "lineedit":
            text = widget.text()
            normalized_text = self._normalize_numeric_text(text)
            if normalized_text != text:
                with QtCore.QSignalBlocker(widget):
                    widget.setText(normalized_text)
            # try to convert to numeric
            try:
                val = json.loads(normalized_text)  
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


    def getCurrentTargetType(self,slmKey,secKey):
        """ Returns current target selected in combo box of slmKey, secKey """
        attrname = f"{slmKey}_{secKey}_cgh_general_target_type"
        if hasattr(self,attrname):
            return getattr(self,attrname).currentText()
        return None
    
    def get_cgh_params(self,slmKey,secKey):
        """ Returns current cgh params set in slmKey, secKey"""
        all_params = self.get_params()
        sec_params = all_params.get(slmKey, {}).get(secKey, {})
        cgh_params = sec_params.get("cgh", None)
        if cgh_params is not None:
            return cgh_params
        return None


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

    def get_tab_names(self, slmKey):
        """Return the current tab names as a dictionary."""
        return self._tab_names_dict.get(slmKey, {}).copy()


    # --------- connection/disconnection --------
    def on_connection_result(self, slmKey: str, success: bool, serial: str, 
                             display_msg: bool = True):
        """Handle the result of a connection attempt."""
        if not hasattr(self, f"{slmKey}_connectBtn"):
            raise RuntimeError("Connection button does not exist")
        
        btn = getattr(self, f"{slmKey}_connectBtn")
        if success:
            btn.setText("Disconnect")
            if not btn.isChecked():
                btn.setChecked(True)
            if display_msg:
                QtWidgets.QMessageBox.information(self, "SLM Connection", f"Successfully connected to SLM {serial}")
        else:
            btn.blockSignals(True)  # prevent re-emitting toggled
            btn.setChecked(False)
            btn.blockSignals(False)
            btn.setText("Connect to SLM")
            if display_msg:
                QtWidgets.QMessageBox.warning(self, "SLM Connection", f"Connection to {self._slmNames[slmKey]} failed.")
    
    def on_disconnection_result(self, slmKey: str, success: bool, msg: str,
                                display_msg: bool = True):
        """Handle the result of a disconnection attempt."""
        if not hasattr(self, f"{slmKey}_connectBtn"):
            raise RuntimeError("Connection button does not exist")
        
        btn = getattr(self, f"{slmKey}_connectBtn")
        if success:
            btn.setText("Connect to SLM")
            if display_msg:
                QtWidgets.QMessageBox.information(self, "SLM Disconnected", msg)
        else:
            btn.blockSignals(True)  # prevent re-emitting toggled
            btn.setChecked(True)
            btn.blockSignals(False)
            if display_msg:
                QtWidgets.QMessageBox.warning(self, "SLM Disconnection", msg)
    

    # --------- computing related --------- #
    def on_update_pattern(self, slmKey):
        """Gather pattern parameters and emit signal to update pattern on SLM."""
        all_params = self.get_params()
        params = all_params.get(slmKey, {})
        self.sigUpdatePattern.emit(slmKey, params)

    def on_compute_cgh(self,slmKey,secKey):
        """
        Gather CGH parameters, emits signal to compute CGH and 
        change state of ALL compute buttons. 
        """
        cgh_params = self.get_cgh_params(slmKey,secKey)
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
        """ Unblocks all compute buttons, update cgh label, updates slm pattern and optional msg display"""

        for slm,sectionsList in self._slmSectionList.items():
            for section in sectionsList:
                btn = getattr(self, f"{slm}_{section}_compute_cgh_btn", None)
                if btn:
                    btn.setText("Compute CGH")
                    btn.setEnabled(True)

        if success:
            cgh_name = "last computed" if cgh_name is None else cgh_name
            self.update_label(slmKey,secKey,"cgh_in_use_label",f"{cgh_name} (computed)")
            self.on_update_pattern(slmKey)
            if msg is not None:
                self.show_message_box(title=f"CGH computation warning",
                                      message=msg,msg_type="warning")
                
        elif not success:
            self.show_message_box(title="CGH computation failed", message=msg,msg_type="error")

    def on_feedback_reset(self,slmKey,secKey,emitSig=True):
        lbl = self._get_current_feedback_counter(slmKey, secKey)
        if lbl is not None:
            lbl.setText("Feedback Rounds: 0")
        if emitSig:
            self.sigResetFeedback.emit(slmKey,secKey)
    
    def update_feedback_count(self,slmKey,secKey,feedback_count):
        lbl = self._get_current_feedback_counter(slmKey, secKey)
        if lbl is not None:
            lbl.setText(f"Feedback Rounds: {feedback_count}")

    def _get_current_feedback_counter(self, slmKey, secKey):
        cgh_params = self.get_cgh_params(slmKey, secKey) or {}
        target_type = cgh_params.get("cgh_general", {}).get("target_type")
        if target_type:
            target_lbl = getattr(
                self,
                f"{slmKey}_{secKey}_cgh_{target_type}_feedback_counter",
                None,
            )
            if target_lbl is not None:
                return target_lbl

        return getattr(self, f"{slmKey}_{secKey}_cgh_feedback_counter", None)
    
    
    # --------- Config related -------- #

    def set_available_configs(self, slmKey, configs):
        """
        Populate config combo box (called from controller)
        configs: list of (display_name, full_path)
        """
        combo = getattr(self, f"{slmKey}_configCombo")
        current = self._currentConfigs.get(slmKey,{}).get("path", "")
        currentPath = os.path.abspath(current) if current else None
        combo.blockSignals(True)
        combo.clear()
        current_index = -1
        for i, (name, path) in enumerate(configs):
            combo.addItem(name, path)
            combo.setItemData(i, self._config_tooltip_text(path), QtCore.Qt.ToolTipRole)
            if currentPath is not None and os.path.abspath(path) == currentPath:
                current_index = i
        if current_index >= 0:
            combo.setCurrentIndex(current_index)
        else:
            combo.setCurrentIndex(-1)
        combo.blockSignals(False)
        self._on_config_index_changed(slmKey, combo.currentIndex())
    
    def on_config_loaded(self, slmKey, slm_params, update_pattern = False, 
                         config_dict={}, msg_box=False):
        """ Should be called every time a new config is loaded """
        try:
            self.set_params({slmKey: slm_params})
            tab_names = slm_params.get("tab_names", {})
            if tab_names:
                self.update_tab_names(slmKey, tab_names)
            if update_pattern:
                self.on_update_pattern(slmKey)
            self.current_config_changed(slmKey,config_dict)

        except Exception as e:
            self.__logger.error(f"Failed to load config: {e}")
            if msg_box:
                self.show_message_box(title="Error Loading Configuration",
                                      message=f"Could not load configuration:\n{e}",
                                      msg_type="error")   
    

    def current_config_changed(self,slmKey,config_dict):
        """ updates self._currentConfigs """
        self._currentConfigs[slmKey] = config_dict
        self._sync_current_config_combo(slmKey)
        self.update_config_info(slmKey)

    def _sync_current_config_combo(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo")
        current = self._currentConfigs.get(slmKey,{}).get("path")
        currentPath = os.path.abspath(current) if current else None
        currentIndex = -1

        if currentPath is not None:
            for index in range(combo.count()):
                itemPath = combo.itemData(index)
                if itemPath and os.path.abspath(itemPath) == currentPath:
                    currentIndex = index
                    break

        combo.blockSignals(True)
        try:
            combo.setCurrentIndex(currentIndex)
        finally:
            combo.blockSignals(False)
        self._on_config_index_changed(slmKey, currentIndex)
    
    def current_config_renamed(self,slmKey,new_path):
        """ updates current config path """
        self._currentConfigs.setdefault(slmKey, {})["path"] = new_path

    def current_config_deleted(self,slmKey):
        self._currentConfigs[slmKey] = {}

    def update_config_info(self,slmKey):
        """Update config controls after the current config changed."""
        infoBtn = getattr(self, f"{slmKey}_infoBtn")
        infoBtn.setToolTip("Open config inspector")
        self._update_config_controls(slmKey)

    # config buttons logic
    def _on_config_index_changed(self, slmKey, _index):
        combo = getattr(self, f"{slmKey}_configCombo")
        tooltip = combo.itemData(combo.currentIndex(), QtCore.Qt.ToolTipRole) or ""
        combo.setToolTip(tooltip)
        self._update_config_controls(slmKey)

    def _update_config_controls(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo", None)
        has_config = combo is not None and combo.currentData() is not None

        for attr in (f"{slmKey}_reloadBtn", f"{slmKey}_updateConfigBtn"):
            button = getattr(self, attr, None)
            if button is not None:
                button.setEnabled(has_config)

        for attr in (
                f"{slmKey}_renameAction", f"{slmKey}_duplicateAction",
                f"{slmKey}_deleteAction", f"{slmKey}_startupAction"):
            action = getattr(self, attr, None)
            if action is not None:
                action.setEnabled(has_config)

    def on_reload_config_clicked(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo")
        path = combo.currentData()
        if path:
            self.sigLoadConfig.emit(slmKey, path)

    def on_config_selection_changed(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo")
        path = combo.currentData()
        if path:
            self.sigLoadConfig.emit(slmKey, path)

    def on_save_new_config_clicked(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo")
        
        while True:
            name, info = askForTwoTextInputs("Save as...", "Config name:", "Config info:")
            if not name:
                return
            # Check for duplicate
            existing_names = [combo.itemText(i).split('.')[0] for i in range(combo.count())]
            if name.split('.')[0] in existing_names:
                self.show_message_box(
                    f"A configuration named '{name}' already exists.",
                    title="Save Config Error",
                    msg_type="error"
                )
                # loop again to give the user another chance
                continue

            self.sigSaveConfig.emit(slmKey, name, info, False)
            return

    def on_rename_config(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo")
        path = combo.currentData()
        if not path:
            return
        old_name = combo.currentText()
        new_name = askForTextInput(self, f"Rename config {old_name}", "New name:")
        if not new_name or new_name == old_name:
            return
        self.sigRenameConfig.emit(slmKey, path, new_name)

    def on_duplicate_config(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo")
        path = combo.currentData()
        if not path:
            return
        old_name = combo.currentText()
        suggested = os.path.splitext(old_name)[0] + "_copy"
        new_name = askForTextInput(self, f"Duplicate config {old_name}", "New name:", suggested=suggested)
        if not new_name:
            return
        self.sigDuplicateConfig.emit(slmKey, path, new_name)

    def on_delete_config(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo")
        path = combo.currentData()
        if not path:
            return
        name = combo.currentText()
        ok = askYesNoQuestion(self, "Delete config",
            f"Are you sure you want to delete the configuration '{name}'?"
        )
        if not ok:
            return
        self.sigDeleteConfig.emit(slmKey, path)


    def on_update_current_config_clicked(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo")
        path = combo.currentData()
        if not path:
            return
        name = os.path.basename(path)
        ext = os.path.splitext(path)[-1].lower()
        if ext == ".json":
            msg = "JSON configuration files are legacy format, saving is not supported. Choose 'save as new' to save as hdf5."
            self.show_message_box(msg,"error", title="Saving error")
            return
        changes = self._config_change_summary(slmKey, path)
        ok = self.showUpdateConfigDialog(name, changes)
        if not ok:
            return
        current_info = self._currentConfigs.get(slmKey,{}).get("info")
        _,new_info = askForTwoTextInputs("Update config info", "Config name:", "Config info:",
                                       default1=name,default2=current_info,readonly1=True)
        if new_info is None:
            return
        self.sigSaveConfig.emit(slmKey, path, new_info, True)

        
    def on_set_startup_config(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo")
        path = combo.currentData()
        if not path:
            return
        self.sigSetStartupConfig.emit(slmKey, path)

    def show_config_settings_dialog(self, slmKey):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("SLM config settings")
        dialog.resize(320, 120)

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addStretch(1)
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        buttonBox.rejected.connect(dialog.reject)
        layout.addWidget(buttonBox)

        self._execDialog(dialog)

    def showUpdateConfigDialog(self, config_name, changes):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Update SLM config")
        dialog.resize(560, 340)

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(QtWidgets.QLabel(f"This will overwrite '{config_name}'."))

        changesLabel = QtWidgets.QLabel("Changed values")
        font = QtGui.QFont(changesLabel.font())
        font.setBold(True)
        changesLabel.setFont(font)
        layout.addWidget(changesLabel)

        changesEdit = QtWidgets.QPlainTextEdit()
        changesEdit.setReadOnly(True)
        changesEdit.setPlainText(changes)
        layout.addWidget(changesEdit, 1)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Update")
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        layout.addWidget(buttonBox)

        return self._execDialog(dialog) == QtWidgets.QDialog.Accepted

    def showInspectConfigsDialog(self, slmKey):
        combo = getattr(self, f"{slmKey}_configCombo")
        dialog = QtWidgets.QDialog(self)
        slmName = self._slmNames.get(slmKey, slmKey)
        dialog.setWindowTitle(f"Inspect {slmName} configs")
        dialog.resize(760, 460)
        dialogFont = self._applyInspectDialogFont(dialog)

        mainLayout = QtWidgets.QHBoxLayout(dialog)

        configList = QtWidgets.QListWidget()
        configList.setMinimumWidth(220)
        for index in range(combo.count()):
            path = combo.itemData(index)
            if not path:
                continue
            item = QtWidgets.QListWidgetItem(combo.itemText(index))
            item.setData(QtCore.Qt.UserRole, path)
            item.setToolTip(combo.itemData(index, QtCore.Qt.ToolTipRole) or "")
            configList.addItem(item)
        mainLayout.addWidget(configList, 0)

        detailWidget = QtWidgets.QWidget()
        detailLayout = QtWidgets.QVBoxLayout(detailWidget)
        detailLayout.setContentsMargins(6, 0, 0, 0)

        nameLabel = QtWidgets.QLabel()
        nameFont = QtGui.QFont(dialogFont)
        nameFont.setBold(True)
        nameLabel.setFont(nameFont)
        detailLayout.addWidget(nameLabel)

        form = QtWidgets.QFormLayout()
        createdLabel = QtWidgets.QLabel()
        infoLabel = QtWidgets.QLabel()
        infoLabel.setWordWrap(True)
        form.addRow("Created:", createdLabel)
        form.addRow("Info:", infoLabel)
        detailLayout.addLayout(form)

        dumpLabel = QtWidgets.QLabel("Config dump")
        dumpFont = QtGui.QFont(dialogFont)
        dumpFont.setBold(True)
        dumpLabel.setFont(dumpFont)
        detailLayout.addWidget(dumpLabel)

        dumpEdit = QtWidgets.QPlainTextEdit()
        dumpEdit.setReadOnly(True)
        self._applyPlainTextEditFont(dumpEdit, dialogFont)
        detailLayout.addWidget(dumpEdit, 1)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        buttonBox.rejected.connect(dialog.reject)
        detailLayout.addWidget(buttonBox)

        mainLayout.addWidget(detailWidget, 1)

        def updateDetails(index):
            item = configList.item(index)
            if item is None:
                nameLabel.setText("No configs")
                createdLabel.setText("")
                infoLabel.setText("")
                dumpEdit.setPlainText("")
                return

            path = item.data(QtCore.Qt.UserRole)
            metadata = self._read_config_metadata(path)
            nameLabel.setText(os.path.basename(path))
            createdLabel.setText(
                format_creation_date(metadata.get("date")) if metadata.get("date") else "Unknown"
            )
            infoLabel.setText(metadata.get("info") or "")
            dumpEdit.setPlainText(self._config_dump_text(path))

        configList.currentRowChanged.connect(updateDetails)

        selectedRow = 0
        selectedPath = combo.currentData()
        if selectedPath:
            selectedPath = os.path.abspath(selectedPath)
            for row in range(configList.count()):
                itemPath = os.path.abspath(configList.item(row).data(QtCore.Qt.UserRole))
                if itemPath == selectedPath:
                    selectedRow = row
                    break

        if configList.count() > 0:
            configList.setCurrentRow(selectedRow)
        else:
            updateDetails(-1)

        self._execDialog(dialog)

    def _config_tooltip_text(self, path):
        lines = [os.path.basename(path)]
        metadata = self._read_config_metadata(path)

        date = metadata.get("date")
        if date:
            lines.append(f"Created: {format_creation_date(date)}")

        info = metadata.get("info")
        if info:
            lines.append(str(info))

        return "\n\n".join(lines)

    def _read_config_metadata(self, path):
        metadata = {"date": "", "info": ""}
        try:
            ext = os.path.splitext(path)[-1].lower()
            if ext in (".h5", ".hdf5"):
                with h5py.File(path, "r") as configFile:
                    metadata["date"] = self._attr_to_text(configFile.attrs.get("date", ""))
                    metadata["info"] = self._attr_to_text(configFile.attrs.get("info", ""))
            elif ext == ".json":
                metadata["info"] = "Legacy JSON configuration"
        except Exception as e:
            metadata["info"] = f"Could not read config metadata: {e}"
        return metadata

    def _config_dump_text(self, path):
        try:
            ext = os.path.splitext(path)[-1].lower()
            if ext == ".json":
                with open(path, "r", encoding="utf-8") as configFile:
                    return json.dumps(json.load(configFile), indent=2, sort_keys=True)

            if ext in (".h5", ".hdf5"):
                lines = []
                with h5py.File(path, "r") as configFile:
                    lines.append("File attributes:")
                    self._append_hdf5_attrs_dump(configFile, lines, indent="  ")

                    if "parameters" in configFile:
                        lines.append("")
                        lines.append("Parameters:")
                        self._append_hdf5_params_dump(configFile["parameters"], lines, indent="  ")

                    otherGroups = [name for name in sorted(configFile.keys()) if name != "parameters"]
                    if otherGroups:
                        lines.append("")
                        lines.append("Stored arrays and groups:")
                        for name in otherGroups:
                            self._append_hdf5_tree_dump(name, configFile[name], lines, indent="  ")

                return "\n".join(lines)

            return f"Unsupported config file type: {ext}"

        except Exception as e:
            return f"Could not read config:\n{e}"

    def _append_hdf5_attrs_dump(self, obj, lines, indent=""):
        for key in sorted(obj.attrs.keys()):
            value = self._json_load_attr(obj.attrs[key])
            lines.append(f"{indent}@{key}: {self._short_repr(value)}")

    def _append_hdf5_params_dump(self, grp, lines, indent=""):
        for key in sorted(grp.attrs.keys()):
            value = self._json_load_attr(grp.attrs[key])
            lines.append(f"{indent}{key}: {self._short_repr(value)}")

        for key in sorted(grp.keys()):
            lines.append(f"{indent}{key}:")
            self._append_hdf5_params_dump(grp[key], lines, indent=f"{indent}  ")

    def _append_hdf5_tree_dump(self, name, obj, lines, indent=""):
        if isinstance(obj, h5py.Dataset):
            lines.append(f"{indent}{name}: dataset shape={obj.shape} dtype={obj.dtype}")
            return

        lines.append(f"{indent}{name}:")
        self._append_hdf5_attrs_dump(obj, lines, indent=f"{indent}  ")
        for childName in sorted(obj.keys()):
            self._append_hdf5_tree_dump(childName, obj[childName], lines, indent=f"{indent}  ")

    def _config_change_summary(self, slmKey, path):
        try:
            savedParams = self._read_config_params(path)
            currentParams = self._current_config_params(slmKey)
            savedFlat = self._flatten_config_params(savedParams)
            currentFlat = self._flatten_config_params(currentParams)

            missing = object()
            lines = []
            for key in sorted(set(savedFlat.keys()) | set(currentFlat.keys())):
                oldValue = savedFlat.get(key, missing)
                newValue = currentFlat.get(key, missing)
                if oldValue == newValue:
                    continue
                if oldValue is missing:
                    lines.append(f"{key}: <not saved> => {self._short_repr(newValue)}")
                elif newValue is missing:
                    lines.append(f"{key}: {self._short_repr(oldValue)} => <removed>")
                else:
                    lines.append(
                        f"{key}: {self._short_repr(oldValue)} => {self._short_repr(newValue)}"
                    )

            if not lines:
                return "No parameter changes detected."

            maxLines = 60
            if len(lines) > maxLines:
                extra = len(lines) - maxLines
                lines = lines[:maxLines] + [f"... {extra} more changed values"]
            return "\n".join(lines)

        except Exception as e:
            return f"Could not compare saved config with current values:\n{e}"

    def _read_config_params(self, path):
        ext = os.path.splitext(path)[-1].lower()
        if ext == ".json":
            with open(path, "r", encoding="utf-8") as configFile:
                return json.load(configFile)

        if ext in (".h5", ".hdf5"):
            with h5py.File(path, "r") as configFile:
                if "parameters" not in configFile:
                    return {}
                return self._read_hdf5_params(configFile["parameters"])

        return {}

    def _current_config_params(self, slmKey):
        params = self.get_params().get(slmKey, {})
        tabNames = self.get_tab_names(slmKey)
        if tabNames:
            params["tab_names"] = tabNames
        return params

    def _read_hdf5_params(self, grp):
        params = {}
        for key, value in grp.attrs.items():
            params[key] = self._json_load_attr(value)
        for key in grp:
            params[key] = self._read_hdf5_params(grp[key])
        return params

    def _flatten_config_params(self, value, prefix=""):
        if isinstance(value, dict):
            flattened = {}
            for key in sorted(value.keys()):
                childPrefix = f"{prefix}.{key}" if prefix else str(key)
                flattened.update(self._flatten_config_params(value[key], childPrefix))
            return flattened
        return {prefix: value}

    def _json_load_attr(self, value):
        text = self._attr_to_text(value)
        try:
            return json.loads(text)
        except Exception:
            return text

    def _attr_to_text(self, value):
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, np.generic):
            value = value.item()
        if value is None:
            return ""
        return str(value)

    def _short_repr(self, value, maxLength=180):
        try:
            text = json.dumps(value, sort_keys=True)
        except Exception:
            text = repr(value)
        if len(text) > maxLength:
            return text[:maxLength - 3] + "..."
        return text

    def _applyInspectDialogFont(self, dialog):
        font = QtGui.QFont(dialog.font())
        font.setPointSize(self.inspectDialogFontPointSize)
        dialog.setFont(font)
        dialog.setStyleSheet(
            f"QDialog QWidget {{ font-size: {self.inspectDialogFontPointSize}pt; }}"
        )
        return font

    def _applyPlainTextEditFont(self, edit, font):
        edit.setFont(font)
        edit.document().setDefaultFont(font)

    def _execDialog(self, dialog):
        if hasattr(dialog, "exec_"):
            return dialog.exec_()
        return dialog.exec()

    # --------- aberration saving/loading -------- #
    
    def on_save_aberr(self,slmKey,secKey):
        # Get aberrations parameters
        all_params = self.get_params()
        slm_params = all_params.get(slmKey, {})
        sec_params = slm_params.get(secKey, {})
        aberr_params = sec_params.get("aberrations", {})
        self.sigSaveAberr.emit(slmKey,secKey,aberr_params)
    
                
    def on_aberr_loaded(self,slmKey,secKey,aberr_params,label_name,msg_box=False):
        try:
            self.set_params({slmKey: {secKey: {"aberrations": aberr_params}}})
            self.update_label(slmKey,secKey,"load_aberrations_label",f"Loaded: {label_name}")
            self.on_update_pattern(slmKey)
        except Exception as e:
            self.__logger.error(f"Failed to load aberrations: {e}")
            if msg_box:
                self.show_message_box(title="Error Loading Aberrations",
                                      message=f"Could not load aberrations:\n{e}",
                                      msg_type="error")

    def update_label(self,slmKey,secKey,attr_suffix,label):
        """ Helper function to change label names"""
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


    # --------- typing validators/formatting and auto-update -------- #

    def _get_slm_timer(self,slmKey):
        if slmKey not in self._slmUpdateTimers:
            timer = QtCore.QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(partial(self.on_update_pattern, slmKey))
            self._slmUpdateTimers[slmKey] = timer
        return self._slmUpdateTimers[slmKey]

    def _schedulePatternUpdate(self,slmKey):
        timer = self._get_slm_timer(slmKey)
        timer.start(_DEBOUNCE_TIME)

    def _lineEditUpdate(self, text, slmKey):
        """
        To avoid updating empty text.
        """
        if text.strip() == "":
            return  # skip empty input
        self._schedulePatternUpdate(slmKey)
    
    def _normalize_numeric_text(self, text):
        """
        Normalize numeric input for float fields. Doesn't change anything for int.
        """
        if not text:
            return None

        # user-friendly fixes
        text = text.strip()
        text = text.replace(",", ".")   # 0,3 -> 0.3
        if text.startswith("."):
            text = "0" + text           # .3 -> 0.3
        if text.endswith("."):
            text = text+'0'             # 3. -> 3.0
       
        return text


    def _make_validator(self, pythontype, widget):
        if pythontype is int:
            return QtGui.QIntValidator(widget)

        if pythontype is float:
            v = QtGui.QDoubleValidator(widget)
            v.setNotation(QtGui.QDoubleValidator.StandardNotation)
            v.setLocale(QtCore.QLocale(QtCore.QLocale.C))
            return v

        return None

# -------------------------------#
#       Helper functions         # 
# -------------------------------#
 
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


# Function to format the date nicely
def format_creation_date(iso_date_str):
    try:
        dt = datetime.datetime.fromisoformat(iso_date_str)
        # Format: Jan 29, 2026 03:23 PM
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return "Unknown date"

def resolve_type(ptype):
    """
    Convert str ("int", "float") or python type to actual Python type.
    Return None if unknown.
    """
    if ptype is None:
        return None
    if isinstance(ptype, type):  # already int/float
        return ptype
    if isinstance(ptype, str):
        ptype_lower = ptype.lower()
        if ptype_lower == "int":
            return int
        if ptype_lower == "float":
            return float
    return None

