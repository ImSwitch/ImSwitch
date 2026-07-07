import glob
import json
import os
import shutil
import numpy as np
from PIL import Image
import traceback
import h5py
import datetime
from qtpy import QtWidgets

from ..basecontrollers import ImConWidgetController, SetupModeMixin
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model import configfiletools
from imswitch.imcontrol.view.guitools import askForFilePath, JsonEditorDialog
from imswitch.imcommon.view.guitools.dialogtools import askYesNoQuestion
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcommon.model import dirtools, ostools, signaltools

from ..patterndesigners.registries import PATTERNS_REGISTRY, ABERRATIONS_REGISTRY, TARGETS_REGISTRY
from ..patterndesigners import cghComputations as cgh
from ..patterndesigners import cghDirectSummation as direct_cgh
from ..patterndesigners.patternEngine import PatternEngine
from ..patterndesigners.slmSectionCalibration import SLMSectionCalibration
from ..patterndesigners.slmPlaneCalibration import (
    add_plane_definition,
    clear_default_active_plane_name as clear_default_active_plane_name_in_properties,
    delete_plane_calibration_files,
    empty_plane_definitions,
    get_default_active_planes,
    load_plane_definitions,
    load_section_calibration,
    plane_slug,
    remove_plane_definition,
    save_plane_definitions,
    save_section_calibration,
    set_default_active_plane as set_default_active_plane_in_properties,
)
from ..patterndesigners import slmsuiteComputations as slmsuite_cgh


full_registry = {
    "patterns": PATTERNS_REGISTRY,
    "aberrations": ABERRATIONS_REGISTRY,
    "cgh_targets": TARGETS_REGISTRY
}

class SLMsController(SetupModeMixin, ImConWidgetController):
    """Linked to SLMsWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self._patternEngines = {}

        # NOTE: subManagers initiated with slmName, so we have to reference them with slmName.
        # Would be better to use only slmKey for all referencing and keep slmName for display only...

        self._slmNames = {}         # {slmKey (widget): slmName (Manager)}
        self._slmKeys = {}          # {slmName (Manager): slmKey (widget)} 
        self._slmInfos = {}         # {slmKey: slmInfo}
        self._targets = {}          # {slmKey: {secKey: TargetInstance}}
        self._cghResults = {}       # {slmKey: {secKey: {"cgh_pattern":..., "performances":...}}}
        self._wavelengths = {}      # {slmKey: {secKey: wl}}
        self._experimentalResults={}# {slmKey: {secKey: result}
        self._analysisPrms={}       # {target_name: prms}
        self._corrPatternsDir={}    # {slm_key: path}
        self._sectionCalibrations = {} # {slmKey: {secKey: SLMSectionCalibration}}

        # define directories for SLM-related files
        self.slmDir = os.path.join(dirtools.UserFileDirs.Root, r'imcontrol_slm')
        self.configsDir = os.path.join(self.slmDir, 'configs')
        self.cghPatternsDir =  os.path.join(self.slmDir, 'cgh_patterns')
        self.correctionDir = os.path.join(self.slmDir, 'Corrections')
        self.calibrationDir = os.path.join(self.slmDir, 'calibrations')
        os.makedirs(self.configsDir, exist_ok=True)
        os.makedirs(self.cghPatternsDir, exist_ok=True)
        os.makedirs(self.calibrationDir, exist_ok=True)
        self._planeDefinitions = self._load_plane_definitions()

        # initiate each slm widget and engine
        for slmName, slmManager in self._master.slmsManager:
            device_connection = slmManager.requires_device_connection
            slmInfo = slmManager.slmInfo
            slmKey = self._widget.add_slm(slmName,slmInfo,full_registry, 
                                          device_connection = device_connection)
            engine = PatternEngine(slmManager.slmInfo)
            self._patternEngines[slmKey] = engine
            self._slmNames[slmKey]=slmName
            self._slmKeys[slmName]=slmKey
            self._slmInfos[slmKey] = slmInfo
            self._refresh_available_planes(slmKey)
            self._load_section_calibrations_from_setup(slmKey)

            # auto-connect for manager that needs device to connection
            if device_connection:
                success = self._startup_connection(slmKey)

            # correction pattern folder: user-specified in config file or fallback to canonical
            correctionPatternsDir = None
            path_candidates = []
            if slmInfo is not None and slmInfo.correctionPatternsDir is not None:
                path_candidates.append(slmInfo.correctionPatternsDir)
            path_candidates.append(os.path.join(self.correctionDir, slmInfo.serial_number)) #default path

            for path in path_candidates:
                if not os.path.exists(path):
                    continue
                else:
                    correctionPatternsDir = path
                    break
            if correctionPatternsDir is None:        
                self.__logger.error(f"Correction pattern directory for {slmName} could not be found at any of those locations: {path_candidates}")
            self._corrPatternsDir[slmKey] = correctionPatternsDir

            # start config loading
            if slmInfo is not None:
                if slmInfo.managerProperties.get("startConfig") is not None:
                    if not device_connection or success: # don't load config if not connection failed
                        start_config = slmInfo.managerProperties.get("startConfig")
                        config_dir = self.get_slm_config_dir(slmKey)
                        config_path = os.path.join(config_dir, start_config)
                        if os.path.isfile(config_path):
                            self.on_load_config(slmKey, path=config_path)
                            self.__logger.info(f"Successfully loaded startup config for {slmName}")
                        else:
                            self.__logger.warning(f"Initial SLM config file {config_path} not found.")

            self.refresh_available_configs(slmKey)

        # widget signals connections
        self._widget.sigConnectSLMusb.connect(self.on_connect)
        self._widget.sigUpdatePattern.connect(self.on_update_pattern)
        self._widget.sigComputeCGH.connect(self.on_compute_cgh)
        self._widget.sigVisualizeCghPerformances.connect(self.on_visualize_cgh_performances)
        self._widget.sigVisualizeTarget.connect(self.on_visualize_target)
        self._widget.sigShowCghResult.connect(self.on_show_cgh_result)
        self._widget.sigTargetParamChanged.connect(self.update_single_target_param)
        self._widget.sigTargetChanged.connect(self.sync_target)
        
        self._widget.sigLoadConfig.connect(self.on_load_config)
        self._widget.sigLoadAberr.connect(self.on_load_aberr)
        self._widget.sigLoadCgh.connect(self.on_load_cgh)
        self._widget.sigSaveConfig.connect(self.on_save_config)
        self._widget.sigSaveAberr.connect(self.on_save_aberr)
        self._widget.sigSaveCgh.connect(self.on_save_cgh)
        self._widget.sigDeleteConfig.connect(self.on_delete_config)
        self._widget.sigRenameConfig.connect(self.on_rename_config)
        self._widget.sigDuplicateConfig.connect(self.on_duplicate_config)
        self._widget.sigSetStartupConfig.connect(self.on_set_startup_config)
        self._widget.sigOpenConfigFolder.connect(self.on_open_config_folder)
        
        self._widget.sigCalibrateLinearPhase.connect(self.on_linear_phase_calibration)
        self._widget.sigActivePlaneChanged.connect(self.on_active_plane_changed)
        self._widget.sigAddPlaneRequested.connect(self.on_add_plane_requested)
        self._widget.sigDeletePlaneRequested.connect(self.on_delete_plane_requested)
        
        self._widget.sigSnapFeedback.connect(self.on_feedback_snap)
        self._widget.sigAnalysisFeedback.connect(self.on_feedback_analysis)
        self._widget.sigUpdateTarget.connect(self.on_feedback_update_target)
        self._widget.sigResetFeedback.connect(self.on_feedback_reset)
        self._widget.sigAnalysisFeedbackPrm.connect(self.on_feedback_analysis_prm)
        self._widget.sigLoadFeedback.connect(self.on_load_feedback)

        # self._widget.sigCalibTarget.connect(self.on_calibrate_cgh_target)
        # self._widget.sigSetDefaultConvFactor.connect(self.on_set_default_conv_factor)

        # cgh worker initialization
        self._cghWorker = self.CGHWorker()
        self._cghThread = Thread()
        self._cghWorker.moveToThread(self._cghThread)
        self._cghWorker.sigStartComputation.connect(self._cghWorker.compute)
        self._cghWorker.sigWorkerCGHComputed.connect(self.on_cgh_computed)
        self._cghWorker.sigWorkerCGHComputationFailed.connect(self.on_cgh_computation_failed)
        self._cghThread.start()

    def __del__(self):
        if hasattr(self,"_cghThread"):
            self._cghThread.quit()
            self._cghThread.wait()

    def getSetupModeState(self):
        slms = {}

        for slmKey, slmName in self._slmNames.items():
            config = dict(self._widget._currentConfigs.get(slmKey, {}) or {})
            configPath = config.get("path")

            slms[slmKey] = {
                "slmName": slmName,
                "configPath": configPath,
                "configName": os.path.basename(configPath) if configPath else None,
                "config": config,
            }

        return {
            "slms": slms,
        }

    def applySetupModeState(self, state):
        warnings = []

        if not isinstance(state, dict):
            return ["Saved SLMs state is not a dictionary."]

        savedSlms = state.get("slms", {})
        if not isinstance(savedSlms, dict):
            return ["Saved SLM entries are not a dictionary."]

        for savedSlmKey, slmState in savedSlms.items():
            if not isinstance(slmState, dict):
                warnings.append(f'SLM "{savedSlmKey}" saved state is not a dictionary.')
                continue

            slmKey = savedSlmKey
            if slmKey not in self._slmNames:
                savedSlmName = slmState.get("slmName")
                slmKey = self._slmKeys.get(savedSlmName)

            if slmKey not in self._slmNames:
                warnings.append(
                    f'SLM "{savedSlmKey}" ({slmState.get("slmName")}) is not available.'
                )
                continue

            configPath = self._resolveSetupModeConfigPath(slmKey, slmState)
            if configPath is None:
                configName = slmState.get("configName") or slmState.get("configPath")
                warnings.append(
                    f'SLM "{self._slmNames[slmKey]}" config "{configName}" is not available.'
                )
                continue

            try:
                self.on_load_config(slmKey, path=configPath)
            except Exception as e:
                warnings.append(
                    f'Failed to load SLM "{self._slmNames[slmKey]}" config "{configPath}": {e}'
                )
                continue

            loadedPath = self._widget._currentConfigs.get(slmKey, {}).get("path")
            if loadedPath and os.path.abspath(loadedPath) != os.path.abspath(configPath):
                warnings.append(
                    f'SLM "{self._slmNames[slmKey]}" loaded "{loadedPath}" instead of "{configPath}".'
                )
            elif not loadedPath:
                warnings.append(
                    f'SLM "{self._slmNames[slmKey]}" config "{configPath}" may not have loaded.'
                )

        return warnings

    def _resolveSetupModeConfigPath(self, slmKey, slmState):
        configPath = slmState.get("configPath")
        configName = slmState.get("configName")

        config = slmState.get("config", {})
        if isinstance(config, dict):
            configPath = configPath or config.get("path")
            if configPath and configName is None:
                configName = os.path.basename(configPath)

        candidates = []
        if configPath:
            candidates.append(configPath)
        if configName:
            candidates.append(os.path.join(self.get_slm_config_dir(slmKey), configName))

        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return candidate

        return None

    def _startup_connection(self, slmKey):
        success = self.on_connect(slmKey,state=True,display_msg=False)
        if not success:
            slmName=self._slmNames.get(slmKey)
            self._logger.warning(f"Attempt to connect to SLM {slmName} at start-up failed.")
        return success
        
    def on_update_pattern(self, slmKey, params):
        
        engine = self._patternEngines[slmKey]
        sectList = self._widget._slmSectionList.get(slmKey)
        msgs = []

        # check if wl changed and update correction pattern only if needed
        for secKey in sectList:
            wl = params.get(secKey).get("general").get("wavelength_nm")
            if wl != self._wavelengths.get(slmKey,{}).get(secKey,0): 
                msg = self.update_correction_patterns(slmKey,secKey,wl)
                if msg is not None: msgs.append(msg)

        # check if wl changed and update 2Pi value only if necessary 
        for secKey in sectList:
            wl = params.get(secKey).get("general").get("wavelength_nm")
            if wl != self._wavelengths.get(slmKey,{}).get(secKey,0):
                msg =  self.update_twopie_value(slmKey,secKey,wl)
                if msg is not None: msgs.append(msg)
        
        if len(msgs) >0:
            processed_msgs = [m.replace("\n", "<br>") for m in msgs]
            full_msg = "<br><br>".join(processed_msgs)
            self._widget.show_message_box(title="Correction Warnings",msg_type="warning",message=full_msg)

        # update cached wavelengths
        self.update_cached_wl(slmKey,params) 
        
        # compute pattern
        try:
            engine.compute_pattern(params)
            # engine.phase_to_eightbits(**params.get("correction_options",{}))
            full_frame = engine.compose_full_frame()
        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="SLM Pattern Update Failed",
                msg_type="error",
                message=f"Could not update SLM pattern:\n{e}"
            )
            return

        # send pattern to manager + widget
        if full_frame is not None:
            slmName = self._slmNames[slmKey]
            self._master.slmsManager.execOn(slmName, lambda l: l.upload_pattern(full_frame))
            self._widget.update_display(slmKey,full_frame)


    def on_connect(self, slmKey: str, state: bool, display_msg:bool=True):
        """Handle connection/disconnection requests."""
        slmName = self._slmNames[slmKey]
        if state:
            success, serial = self._master.slmsManager.execOn(
                slmName, lambda l: l.connect_to_device()
            )
            self._widget.on_connection_result(slmKey, success, serial, display_msg)
        else:
            success, msg = self._master.slmsManager.execOn(
                slmName, lambda l: l.close_device()
            )
            self._widget.on_disconnection_result(slmKey, success, msg, display_msg)

        return success


    def update_correction_patterns(self, slmKey, secKey, wl):
        """
        Searches for correction pattern according to correctionPatternsDir serial number defined 
        in config file. If found, loads it and update engine correction pattern for `secKey`.
        """
        slmName = self._slmNames.get(slmKey)
        slmInfo = self._slmInfos.get(slmKey,None)
        engine = self._patternEngines.get(slmKey)

        try:
            if slmInfo is None:
                raise KeyError(f"slmInfo for {slmName} not found")

            correctionPatternsDir = self._corrPatternsDir.get(slmKey)
            if correctionPatternsDir is None:
                raise FileNotFoundError(f"Correction Pattern Directory not found for {slmName}.")
            
            serial = slmInfo.serial_number
            if serial is None:
                raise KeyError(f"Cannot find serial number of {slmName} in config file")
            
            correctionFile = f"CAL_{serial}_{wl}nm.bmp"
            correctionPatternFullPath = os.path.join(correctionPatternsDir,correctionFile)
            if not os.path.isfile(correctionPatternFullPath):
                wls_available = []
                wl_errors = []
                for file in glob.glob(correctionPatternsDir + "/*.bmp"):
                    wl_avail = file.split("_")[-1].split("nm")[-2]
                    wls_available.append(wl_avail)
                    wl_errors.append(int(wl_avail)-wl)
                min_err_idx = np.argmin(wl_errors)
                self.__logger.warning(f"Cannot find correction pattern of {slmName} at wavelength {wl}, switching to "
                                      f"closest one found in {correctionPatternsDir}: {wls_available[min_err_idx]}")
                correctionPatternFullPath = os.path.join(correctionPatternsDir,f"CAL_{serial}_{wls_available[min_err_idx]}nm.bmp")
                # raise FileNotFoundError(f"Cannot find correction pattern of {slmName} at wavelength {wl}")
            
            correctionImg = np.array(Image.open(correctionPatternFullPath))
            engine.update_correction_pattern(secKey,correctionImg)
            msg = None
        
        except Exception as e:
            sectionName = self._widget._tab_names_dict.get(slmKey,{}).get(secKey,secKey)
            msg = f"<b>{slmName} - {sectionName}</b>: Failed to load correction pattern :\n{e}"
            self.__logger.error(traceback.format_exc())
        
        return msg

    def update_twopie_value(self, slmKey, secKey, wl):
        """
        Searches for 2pi value in wavelength table json file (file name defined in config).
        If the measured value is not found, falls back to manufacturer and warns user.
        If found, updates 2pi value of engine for `secKey`.
        """

        slmName = self._slmNames.get(slmKey)
        slmInfo = self._slmInfos.get(slmKey,None)
        engine = self._patternEngines.get(slmKey)

        try:
            correctionPatternsDir = self._corrPatternsDir.get(slmKey)
            if correctionPatternsDir is None:
                raise FileNotFoundError(f"Correction Pattern Directory not found for {slmName}.")

            wavelengthTableFile = slmInfo.wavelengthTableFile

            if wavelengthTableFile is None:
                raise ValueError(f"Cannot find 'wavelengthTableFile' of {slmName} in config file")
            if wavelengthTableFile != "none":
                if wavelengthTableFile.split('.')[-1] != "json":
                    raise ValueError(f"The wavelength table shoule be a json file, not {wavelengthTableFile.split('.')[-1]}")

                wavelengthTableFullPath = os.path.join(correctionPatternsDir,wavelengthTableFile)
                if not os.path.isfile(wavelengthTableFullPath):
                    raise FileNotFoundError(f"The wavelength table for {slmName} not found at {wavelengthTableFullPath}")

                with open(wavelengthTableFullPath, 'r') as f:
                    data = json.load(f)
                if data.get("measurement",{}).get(f"{wl}nm") is not None:
                    twopivalue = data.get("measurement",{}).get(f"{wl}nm")
                    measured = True
                elif data.get("manufacturer",{}).get(f"{wl}nm") is not None:
                    twopivalue = data.get("manufacturer",{}).get(f"{wl}nm")
                    measured = False
                elif data.get(f"{wl}nm") is not None:
                    twopivalue = data.get(f"{wl}nm")
                    measured = False
                else:
                    raise KeyError(f"Cannot find the 2pi value for {slmName} and wavelength {wl}")
            else:
                self.__logger.warning(f"Cannot find 2pi value for {slmName} and wavelength {wl} using default 255")
                twopivalue = 255
                measured = False

            engine.update_twopi_value(secKey,twopivalue)
            msg = None
            if not measured:
                sectionName = self._widget._tab_names_dict.get(slmKey,{}).get(secKey,secKey)
                msg = f"<b>{slmName} - {sectionName}</b>: 2Pi value not characterized for {wl}nm. Using default manufacturer one."

        except Exception as e:
            sectionName = self._widget._tab_names_dict.get(slmKey,{}).get(secKey,secKey)
            msg = f"<b>{slmName} - {sectionName}</b>: failed to update 2pi value:\n{e}"
            self.__logger.error(traceback.format_exc())
            
        return msg
    
    def update_cached_wl(self,slmKey,params):
        """ Update cached wavelengths of `slmKey` with wavelenghts in `params` for each section"""
        sectList = self._widget._slmSectionList.get(slmKey)
        for secKey in sectList:
            wl = params.get(secKey).get("general").get("wavelength_nm")
            if wl != self._wavelengths.get(slmKey,{}).get(secKey,0): 
                self._wavelengths.setdefault(slmKey,{})[secKey] = wl

    # ----- SLM section calibration helpers ----- #

    def _load_plane_definitions(self):
        try:
            return load_plane_definitions(self.calibrationDir)
        except Exception as e:
            self.__logger.warning(f"Could not load SLM plane definitions: {e}")
            return empty_plane_definitions()

    def _plane_names(self):
        return list((self._planeDefinitions or {}).get("planes", {}).keys())

    def _refresh_available_planes(self, slmKey=None):
        slmKeys = [slmKey] if slmKey is not None else list(self._slmNames.keys())
        planeNames = self._plane_names()

        for key in slmKeys:
            for secKey in self._widget._slmSectionList.get(key, []):
                activePlane = self._get_default_active_plane(key, secKey)
                if activePlane not in planeNames:
                    activePlane = None
                self._widget.set_available_planes(key, secKey, planeNames, activePlane)

    def _load_all_section_calibrations(self):
        for slmKey in self._slmNames:
            self._load_section_calibrations_from_setup(slmKey)

    def _load_section_calibrations_from_setup(self, slmKey):
        """Load the active plane calibration for each SLM section."""

        self._sectionCalibrations.setdefault(slmKey, {})
        for secKey in self._widget._slmSectionList.get(slmKey, []):
            activePlane = self._widget.get_active_plane(slmKey, secKey)
            calibration = self.get_section_calibration(
                slmKey, secKey, plane_name=activePlane
            )
            self._set_section_calibration_runtime(slmKey, secKey, calibration)

    def get_section_calibration(self, slmKey, secKey, plane_name=None):
        """Return the stored calibration for one SLM section and plane."""

        plane_name = plane_name or self._widget.get_active_plane(slmKey, secKey)
        if not plane_name:
            return SLMSectionCalibration()
        if plane_name not in (self._planeDefinitions or {}).get("planes", {}):
            return SLMSectionCalibration()

        try:
            return load_section_calibration(
                self.calibrationDir,
                self._get_slm_serial(slmKey),
                secKey,
                plane_name,
            )
        except Exception as e:
            self.__logger.warning(
                f"Invalid SLM section calibration for {slmKey}/{secKey}/{plane_name}: {e}"
            )
            return SLMSectionCalibration()

    def set_section_calibration(self, slmKey, secKey, calibration, persist=True):
        """Store and apply the calibration for one SLM section's active plane."""

        planeName = self._widget.get_active_plane(slmKey, secKey)
        if not planeName:
            raise ValueError("Select or add an active plane before saving calibration.")
        if planeName not in (self._planeDefinitions or {}).get("planes", {}):
            raise ValueError(f'Plane "{planeName}" is not defined.')

        calibration = SLMSectionCalibration.from_dict(calibration)
        planeDefinition = self._planeDefinitions["planes"].get(planeName, {})
        calibration.plane = planeName
        calibration.cam_px_size_um = planeDefinition.get("detector_pixel_size_um")

        if persist:
            save_section_calibration(
                self.calibrationDir,
                self._slmNames.get(slmKey, slmKey),
                self._get_slm_serial(slmKey),
                secKey,
                planeName,
                calibration,
            )
            self._set_default_active_plane(slmKey, secKey, planeName, persist=True)

        self._set_section_calibration_runtime(
            slmKey, secKey, calibration, clear_cached=True
        )

    def on_linear_phase_calibration(self, slmKey, secKey, calibration_inputs):
        """Compute and save a section calibration from a linear phase test."""

        try:
            calibration = SLMSectionCalibration.from_linear_phase_test(
                calibration_inputs.get("period_x_px"),
                calibration_inputs.get("measured_dx_um"),
                calibration_inputs.get("period_y_px"),
                calibration_inputs.get("measured_dy_um"),
            )
            self.set_section_calibration(slmKey, secKey, calibration, persist=True)
            self._widget.show_message_box(
                title="SLM Section Calibration",
                msg_type="info",
                message=(
                    f"Saved calibration for {slmKey}/{secKey} "
                    f"({self._widget.get_active_plane(slmKey, secKey)}):\n"
                    f"kx_per_um = {calibration.kx_per_um:.6g}\n"
                    f"ky_per_um = {calibration.ky_per_um:.6g}"
                ),
            )
            self._widget.on_update_pattern(slmKey)
        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="SLM Section Calibration Failed",
                msg_type="error",
                message=f"Could not save calibration:\n{e}",
            )

    def on_active_plane_changed(self, slmKey, secKey, active_plane):
        planeName = str(active_plane or "").strip() or None
        try:
            if planeName and planeName not in (self._planeDefinitions or {}).get("planes", {}):
                raise ValueError(f'Plane "{planeName}" is not defined.')

            self._set_default_active_plane(slmKey, secKey, planeName, persist=True)
            calibration = self.get_section_calibration(
                slmKey, secKey, plane_name=planeName
            )
            self._set_section_calibration_runtime(
                slmKey, secKey, calibration, clear_cached=True
            )
        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="SLM Plane Selection Failed",
                msg_type="error",
                message=f"Could not switch active plane:\n{e}",
            )

    def on_add_plane_requested(self, slmKey, secKey, plane_definition):
        try:
            newSlug = plane_slug(plane_definition.get("name"))
            self._planeDefinitions = add_plane_definition(
                self._planeDefinitions,
                plane_definition,
            )
            save_plane_definitions(self.calibrationDir, self._planeDefinitions)

            planeName = next(
                name for name in self._planeDefinitions["planes"]
                if plane_slug(name) == newSlug
            )
            self._set_default_active_plane(slmKey, secKey, planeName, persist=False)
            self._save_setup_info()
            self._refresh_available_planes()
            self._load_all_section_calibrations()

            self._widget.show_message_box(
                title="SLM Plane",
                msg_type="info",
                message=f'Added plane "{planeName}".',
            )
        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="Add SLM Plane Failed",
                msg_type="error",
                message=f"Could not add plane:\n{e}",
            )

    def on_delete_plane_requested(self, slmKey, secKey, plane_name):
        planeName = str(plane_name or "").strip()
        if not planeName:
            return

        try:
            self._planeDefinitions = remove_plane_definition(
                self._planeDefinitions,
                planeName,
            )
            deletedFiles = delete_plane_calibration_files(
                self.calibrationDir,
                planeName,
            )
            self._clear_default_active_plane_name(planeName)
            save_plane_definitions(self.calibrationDir, self._planeDefinitions)
            self._save_setup_info()
            self._refresh_available_planes()
            self._load_all_section_calibrations()

            self._widget.show_message_box(
                title="SLM Plane",
                msg_type="info",
                message=(
                    f'Deleted plane "{planeName}" and '
                    f"{len(deletedFiles)} calibration file(s)."
                ),
            )
        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="Delete SLM Plane Failed",
                msg_type="error",
                message=f"Could not delete plane:\n{e}",
            )

    def _set_section_calibration_runtime(
        self, slmKey, secKey, calibration, clear_cached=False
    ):
        self._sectionCalibrations.setdefault(slmKey, {})[secKey] = calibration
        self._widget.update_section_calibration_status(
            slmKey,
            secKey,
            calibration.to_dict() if calibration.is_valid() else None,
        )
        self._widget.set_section_calibration(slmKey,secKey,calibration)
        if clear_cached:
            self._clear_section_runtime_state(slmKey, secKey)

    def _clear_section_runtime_state(self, slmKey, secKey):
        self._targets.setdefault(slmKey, {}).pop(secKey, None)
        self._cghResults.setdefault(slmKey, {})[secKey] = {}
        engine = self._patternEngines.get(slmKey)
        cache = getattr(engine, "_cachedSections", {}).get(secKey) if engine else None
        if isinstance(cache, dict):
            cache["cgh"] = None
        self._widget.on_feedback_reset(slmKey, secKey, emitSig=False)

    def _get_slm_serial(self, slmKey):
        slmInfo = self._slmInfos.get(slmKey)
        return getattr(slmInfo, "serial_number", None) or slmKey

    def _get_manager_properties(self, slmKey):
        slmName = self._slmNames.get(slmKey)
        slmInfo = getattr(self._setupInfo, "slms", {}).get(slmName)
        if slmInfo is None:
            slmInfo = self._slmInfos.get(slmKey)
        if slmInfo is None:
            raise KeyError(f'Could not find SLM "{slmKey}" in setupInfo.slms')

        managerProperties = getattr(slmInfo, "managerProperties", None)
        if managerProperties is None:
            managerProperties = {}
            object.__setattr__(slmInfo, "managerProperties", managerProperties)

        self._slmInfos[slmKey] = slmInfo
        return managerProperties

    def _get_default_active_plane(self, slmKey, secKey):
        return get_default_active_planes(
            self._get_manager_properties(slmKey)
        ).get(secKey)

    def _set_default_active_plane(self, slmKey, secKey, planeName, persist=True):
        managerProperties = self._get_manager_properties(slmKey)
        set_default_active_plane_in_properties(managerProperties, secKey, planeName)
        if persist:
            self._save_setup_info()

    def _clear_default_active_plane_name(self, planeName):
        for slmKey in list(self._slmNames.keys()):
            managerProperties = self._get_manager_properties(slmKey)
            clear_default_active_plane_name_in_properties(
                managerProperties,
                planeName,
            )

    def _save_setup_info(self):
        configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)

    
    # --------- Saving/loading related -------- #
    
    def get_slm_config_dir(self, slmKey):
        slm_id = self._slmInfos[slmKey].serial_number
        path = os.path.join(self.configsDir, slm_id)
        os.makedirs(path, exist_ok=True)
        return path
    
    def refresh_available_configs(self, slmKey):
        """ Scan config dir for hdf5 or json files and populate widget combo box """
        cfg_dir = self.get_slm_config_dir(slmKey)

        configs = []
        for fn in sorted(os.listdir(cfg_dir)):
            if fn.endswith((".json", ".h5", ".hdf5")):
                full = os.path.join(cfg_dir, fn)
                configs.append((fn, full))

        self._widget.set_available_configs(slmKey, configs)

    def on_rename_config(self, slmKey, old_name, new_name):
        """Rename SLM configuration file."""
        try:
            config_dir = self.get_slm_config_dir(slmKey)
            old_path = os.path.join(config_dir, old_name)
            new_path = os.path.join(config_dir, new_name)
            if not new_path.endswith(".h5"):
                new_path = new_path + ".h5"
            if os.path.isfile(old_path):
                was_startup_config = self._is_startup_config(slmKey, old_path)
                os.rename(old_path, new_path)
                if was_startup_config:
                    self._set_startup_config_filename(slmKey, os.path.basename(new_path))
                self._widget.current_config_renamed(slmKey,new_path)
                self.refresh_available_configs(slmKey)
            else:
                raise FileNotFoundError(f"Configuration file not found: {old_path}")

        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="Error Renaming Configuration",
                msg_type="error",
                message=f"Could not rename configuration:\n{e}"
            )

    def on_duplicate_config(self, slmKey, source_path, new_name):
        """Duplicate an SLM configuration file into the SLM config directory."""
        try:
            if not source_path or not os.path.isfile(source_path):
                raise FileNotFoundError(f"Configuration file not found: {source_path}")

            config_dir = self.get_slm_config_dir(slmKey)
            extension = os.path.splitext(source_path)[1] or ".h5"
            new_filename = os.path.basename(new_name.strip())
            if not new_filename:
                return
            if not os.path.splitext(new_filename)[1]:
                new_filename = new_filename + extension

            new_path = os.path.join(config_dir, new_filename)
            if os.path.exists(new_path):
                raise FileExistsError(f"Configuration file already exists: {new_path}")

            shutil.copy2(source_path, new_path)
            self.refresh_available_configs(slmKey)

        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="Error Duplicating Configuration",
                msg_type="error",
                message=f"Could not duplicate configuration:\n{e}"
            )

    def on_set_startup_config(self, slmKey, config_path):
        """Persist the selected SLM config as the config loaded on next startup."""
        try:
            if not config_path or not os.path.isfile(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

            config_dir = os.path.abspath(self.get_slm_config_dir(slmKey))
            config_path = os.path.abspath(config_path)
            filename = os.path.basename(config_path)
            startup_path = os.path.abspath(os.path.join(config_dir, filename))

            if (os.path.normcase(startup_path) != os.path.normcase(config_path)
                    or not os.path.isfile(startup_path)):
                raise FileNotFoundError(
                    f"Startup config must be in this SLM config folder: {config_dir}"
                )

            self._set_startup_config_filename(slmKey, filename)

            slmName = self._slmNames.get(slmKey, slmKey)
            self.__logger.info(f"Set startup config for {slmName}: {filename}")
            self._widget.show_message_box(
                title="Startup config",
                msg_type="info",
                message=f"'{filename}' will be loaded at startup for {slmName}."
            )

        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="Startup config",
                msg_type="error",
                message=f"Could not set startup config:\n{e}"
            )

    def _is_startup_config(self, slmKey, config_path_or_name):
        startupConfig = self._get_startup_config_filename(slmKey)
        return bool(startupConfig) and startupConfig == os.path.basename(config_path_or_name)

    def _get_startup_config_filename(self, slmKey):
        slmInfo = self._slmInfos.get(slmKey)
        managerProperties = getattr(slmInfo, "managerProperties", None) or {}
        return managerProperties.get("startConfig")

    def _set_startup_config_filename(self, slmKey, filename):
        slmName = self._slmNames.get(slmKey)
        slmInfo = getattr(self._setupInfo, "slms", {}).get(slmName)
        if slmInfo is None:
            raise KeyError(f'Could not find SLM "{slmName}" in setupInfo.slms')

        managerProperties = getattr(slmInfo, "managerProperties", None)
        if managerProperties is None:
            managerProperties = {}
            object.__setattr__(slmInfo, "managerProperties", managerProperties)

        if filename:
            managerProperties["startConfig"] = filename
        else:
            managerProperties.pop("startConfig", None)
            
        # Keep local cache synced to the saved setup object.
        self._slmInfos[slmKey] = slmInfo

        configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)


    def on_open_config_folder(self, slmKey):
        """Open this SLM's configuration directory in the OS file browser."""
        try:
            ostools.openFolderInOS(self.get_slm_config_dir(slmKey))
        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="Open SLM Config Folder",
                msg_type="error",
                message=f"Could not open configuration folder:\n{e}"
            )
    
    def on_delete_config(self, slmKey, path):
        """Delete SLM configuration file."""
        try:
            if os.path.isfile(path):
                was_startup_config = self._is_startup_config(slmKey, path)
                os.remove(path)
                if was_startup_config:
                    self._set_startup_config_filename(slmKey, None)
                self._widget.current_config_deleted(slmKey)
                self.refresh_available_configs(slmKey)
            else:
                raise FileNotFoundError(f"Configuration file not found: {path}")

        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="Error Deleting Configuration",
                msg_type="error",
                message=f"Could not delete configuration:\n{e}"
            )


    def on_save_config(self, slmKey, config_name,info="",overwrite=False, msg_box=True):
        """Save full SLM configuration (enforcing HDF5 format and in the right slm directory)."""
        try:
            cfg_dir = self.get_slm_config_dir(slmKey)
            path = os.path.join(cfg_dir, config_name)
            if not path.endswith(".h5"):
                path = path + ".h5"

            # temporary path
            tmp_path = path + ".tmp" 
            creation_date = datetime.datetime.now().isoformat()
            self.save_hdf5_config(slmKey, tmp_path,creation_date, info, overwrite)

            # if no error, we replace temporary path with final path
            os.replace(tmp_path, path)

            # update widget
            config_dict = {
                "path": path,
                "date": creation_date,
                "info": info
            }
            self._widget.current_config_changed(slmKey,config_dict)
            self.refresh_available_configs(slmKey)

        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            self.__logger.error(traceback.format_exc())
            if msg_box:
                self._widget.show_message_box(
                    title="Error Saving Configuration",
                    msg_type="error",
                    message=f"Could not save configuration:\n{e}"
                )

    def on_load_config(self, slmKey, path=None):
        """Load SLM configuration from JSON (legacy) or HDF5."""
        try:
            if path is None: # NOTE: this shouldn't be needed anymore with the combobox config selection, kept for now just in case
                path = askForFilePath(
                    self._widget,
                    "Select configuration file to load",
                    defaultFolder=self.configsDir,
                    isSaving=False
                )
                if not path or not os.path.exists(path):
                    return
            ext = os.path.splitext(path)[-1].lower()

            # LEGACY: loading JSON config (should disappear in the future)
            if ext == ".json":
                msg = "JSON configuration files are legacy format and may not support all features.\n Do you want to proceed?"
                ok = askYesNoQuestion(self._widget,"Load JSON Configuration",msg)
                if ok:
                    with open(path, "r", encoding="utf-8") as f:
                        slm_params = json.load(f)
                    config_dict = {"path": path,"date": "","info": ""}
                    self._widget.on_config_loaded(slmKey, slm_params, update_pattern=True, 
                                                  config_dict=config_dict, msg_box=True)
                return
            
            # HDF5 loading
            if ext in (".h5", ".hdf5"):
                ok, slm_params, config_dict = self.load_hdf5_config(slmKey, path)
                if ok:
                    self._widget.on_config_loaded(slmKey, slm_params, update_pattern=False, 
                                                  config_dict=config_dict, msg_box=True)
                return

            raise ValueError(f"Unsupported config file type: {ext}")

        except Exception as e:
            self.__logger.error(traceback.format_exc())
            self._widget.show_message_box(
                title="Error Loading Configuration",
                msg_type="error",
                message=f"Could not load configuration:\n{e}"
            )


    def on_save_aberr(self, slmKey,secKey,aberr_params, msg_box=True):
        """Save aberration coefficients to a JSON file."""
        try:
            suggested = os.path.join(self.configsDir,slmKey+"_" + secKey + "_aberrations")
            path = askForFilePath(self._widget, "Select file to save aberrations", defaultFolder=suggested,isSaving=True)
            if not path:
                return
            path = path + ".json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(aberr_params, f, indent=2)
        
        except Exception as e:
            if msg_box:
                self._widget.show_message_box(title="Error Saving Aberrations",msg_type="error",
                                      message=f"Could not save aberrations:\n{e}")
                raise
        

    def on_load_aberr(self, slmKey, secKey, path=None):
        """Load aberration coefficients from a JSON file and send to widget."""
        if path is None:
            path = askForFilePath(self._widget, "Select aberrations file to load", defaultFolder=self.configsDir,isSaving=False)
            if not path or not os.path.exists(path):
                return
        with open(path, "r", encoding="utf-8") as f:
            aberr_params = json.load(f)
        label_name = os.path.basename(path)
        self._widget.on_aberr_loaded(slmKey,secKey,aberr_params,label_name,msg_box=True)
    

    
    # HDF5 saving/loading
    def save_hdf5_config(self, slmKey, path, creation_date, info="", overwrite=False):
        engine = self._patternEngines[slmKey]
        params = self._widget.get_params()[slmKey]
        info = "No information provided" if info=="" else info
        
        # add tab names to params for restoration upon loading
        tab_names = self._widget.get_tab_names(slmKey)
        if tab_names:
            params["tab_names"] = tab_names

        mode = "w" if overwrite else "x"
        if not overwrite and os.path.exists(path):
            raise FileExistsError ("Config with this name already exists")

        with h5py.File(path, mode) as f:

            # general metadata
            f.attrs["schema_version"] = "1.0"
            f.attrs["slm_id"] = self._slmInfos[slmKey].serial_number
            f.attrs["date"] = creation_date
            f.attrs["info"] = info

            # parameters
            self.write_params_to_hdf5(f.create_group("parameters"), params)

            # final displayed image
            final_img = engine.get_cached_final_image()
            if final_img is None:
                raise RuntimeError("No cached final image")

            f.create_dataset(
                "images/final/full_slm",
                data=final_img,
                compression="gzip"
            )

            # individual cached sections
            for secKey, cache in engine._cachedSections.items():
                grp = f.create_group(f"sections/{secKey}/components")
                for name, arr in cache.items():
                    if arr is not None:
                        grp.create_dataset(name, data=arr, compression="gzip")

            # CGH
            if self._cghResults.get(slmKey):
                for secKey, res in self._cghResults[slmKey].items():
                    grp = f.create_group(f"cgh/{secKey}")
                    grp.create_dataset("final_pattern", data=res["cgh_pattern"])
                    cgh_name = res.get("cgh_name")
                    if cgh_name:
                        grp.attrs["cgh_name"] = cgh_name
                    grp.attrs["comput_params"] = json.dumps(
                        res.get("comput_params", {})
                    )

    def load_hdf5_config(self, slmKey, path):
        """
        Extract params, images and config info from hdf5 file, and sync with config state:
            - final image sent to SLM and widget display
            - section images are restored in pattern engine
        
        Returns:
            - success (bool)
            - params: dict of slm_params to be loaded in widget
            - config_dict: config information to be sent to widget
        """
        slmInfo = self._slmInfos[slmKey]
        slmName = self._slmNames[slmKey]

        with h5py.File(path, "r") as f:
            slm_id = f.attrs.get("slm_id", "")
            creation_date = f.attrs.get("date", "Unknown")
            info = f.attrs.get("info", "No information provided")
            
            if slm_id != slmInfo.serial_number:
                ok = self._widget.askYesNoQuestion("SLM mismatch",
                        f"This config was created for another SLM (sn: {slm_id}).\nLoad anyway?")
                if not ok:
                    return False, None, None

            params = self.read_params_from_hdf5(f["parameters"])
            final_image = f["images/final/full_slm"][()]

            sections = {}
            if "sections" in f:
                for secKey in f["sections"]:
                    sections[secKey] = {}
                    comp = f[f"sections/{secKey}/components"]
                    for k in comp:
                        sections[secKey][k] = comp[k][()]

            cgh = {}
            if "cgh" in f:
                for secKey in f["cgh"]:
                    grp = f[f"cgh/{secKey}"]
                    cgh_name = grp.attrs.get("cgh_name")
                    if cgh_name is not None:
                        self._widget.update_label(slmKey,secKey,"cgh_in_use_label",f"{cgh_name}")
                    else:
                        self._widget.update_label(slmKey,secKey,"cgh_in_use_label", "Unnamed")

                    cgh[secKey] = {
                        "cgh_name": cgh_name,
                        "cgh_pattern": grp["final_pattern"][()],
                        "comput_params": json.loads(
                            grp.attrs.get("comput_params", "{}")
                        )
                    }
        
        # pushes image to SLM and widget, without recomputation
        self._widget.update_display(slmKey,final_image)
        self._master.slmsManager.execOn(slmName, lambda l: l.upload_pattern(final_image))
        
        # restore cached sections and cgh results
        engine = self._patternEngines[slmKey]
        for secKey, comps in sections.items():
            engine._cachedSections[secKey].update(comps)
        engine._cachedFinalImage = final_image
        self._cghResults[slmKey] = cgh

        config_dict = {
            "path": path,
            "date": creation_date,
            "info": info
        }
        return True, params, config_dict 
        
    # --- hdf5 helpers --- #
    def write_params_to_hdf5(self, grp, data):
        for k, v in data.items():
            if isinstance(v, dict):
                self.write_params_to_hdf5(grp.create_group(k), v)
            else:
                grp.attrs[k] = json.dumps(v)

    def read_params_from_hdf5(self, grp):
        out = {k: json.loads(v) for k, v in grp.attrs.items()}
        for k in grp:
            out[k] = self.read_params_from_hdf5(grp[k])
        return out



    # ----- CGH related methods ----- #

    def _get_current_target_params(self,slmKey,secKey):
        cgh_params = self._widget.get_cgh_params(slmKey,secKey)
        target_type = cgh_params.get("cgh_general",{}).get("target_type","")
        target_params = cgh_params.get(target_type)
        if cgh_params is None or target_type=="" or target_params is None:
            raise Exception(f"Could not find target parameters for {slmKey},{secKey}")
        return target_type, target_params

    def update_single_target_param(self, slmKey, secKey, param_name, value):
        """ Light update of one single target parameter."""
        target = self._targets.get(slmKey, {}).get(secKey)
        if target is None:
            return
        
        target_type = self._widget.getCurrentTargetType(slmKey,secKey)
        if target.target_type != target_type:
            return
        
        else:
            changed = target.update_single_param(param_name,value)
            if changed:
                new_params = target.get_target_params()
                self._widget.on_new_target_params(slmKey,secKey,target_type,new_params)
                self._widget.on_feedback_reset(slmKey,secKey,emitSig=False)
                self._cghResults.setdefault(slmKey, {})[secKey] = {} # clear any previous cgh result

    def sync_target(self, slmKey, secKey):
        """
        Sync target object with target parameters for a given SLM section.
        Exception is raised if cgh params cannot be found in slmKey, secKey.
        """
        target_type, target_params = self._get_current_target_params(slmKey,secKey)

        # get section size and calibration
        section_size = self._get_section_size(slmKey,secKey)
        section_calibration = self._sectionCalibrations.get(slmKey,{}).get(secKey,{})

        # get current cahed target and update or create
        target = self._targets.get(slmKey, {}).get(secKey)
        if target is None or target.target_type != target_type:
            target = self.create_target(target_type,section_size, section_calibration, **target_params)
            self._targets.setdefault(slmKey, {})[secKey] = target
            self._cghResults.setdefault(slmKey, {})[secKey] = {} # clear any previous cgh result
        else:
            changed = target.update_params(section_size, section_calibration, **target_params)
            if changed:
                self._widget.on_feedback_reset(slmKey,secKey,emitSig=False)
                self._cghResults.setdefault(slmKey, {})[secKey] = {} # clear any previous cgh result
        return True

    def create_target(self,target_type, section_size = None,section_calibration=None,**target_params):
        """
        Creates a target object 
        """
        target_class = TARGETS_REGISTRY.get(target_type,{}).get("class")
        if target_class is None:
            raise KeyError(f"{target_type} not found")
        
        target = target_class(section_size=section_size, section_calibration=section_calibration, **target_params)
        return target


    def _get_section_size(self, slmKey, secKey):
        engine = self._patternEngines.get(slmKey)
        if engine is None:
            return None
        return getattr(engine, "_sectionShapes", {}).get(secKey)


    def on_load_cgh(self, slmKey, secKey, path=None, msg_box=True):
        """Load a CGH pattern, stores it and notify widget"""
        if path is None:
            path = askForFilePath(self._widget, "Select CGH pattern file to load", defaultFolder=self.cghPatternsDir,isSaving=False)
            if not path or not os.path.exists(path):
                return
        try:
            base = os.path.basename(path)
            name,extension = os.path.splitext(base)
            if extension not in [".npy",".npz"]:
                self._widget.show_message_box(title="Error Loading CGH Pattern",msg_type="error",
                                      message=f"CGH pattern should be a numpy (.npy, .npz) file, not {extension}.")
                return
            array = np.load(path,allow_pickle=True)
            result_dict = { 
                "cgh_name": name,
                "cgh_pattern": array
            }
            
            self._cghResults.setdefault(slmKey,{})[secKey] = result_dict
            self._widget.update_label(slmKey,secKey,"cgh_in_use_label",f"{name} (loaded)")
            self._patternEngines.get(slmKey).set_new_cgh_pattern(secKey, array)

        except Exception as e:
            if msg_box:
                self._widget.show_message_box(title="Error Loading CGH Pattern",msg_type="error",
                                        message=f"Could not load CGH pattern:\n{e}")
            raise
    

    def on_save_cgh(self, slmKey, secKey, msg_box=True):
        """Save the computed CGH pattern to a .npy file."""
        
        slmName = self._slmNames.get(slmKey)
        secName = self._widget._tab_names_dict.get(slmKey,{}).get(secKey,secKey)

        result_dict = self._cghResults.get(slmKey,{}).get(secKey,{}) 
        if result_dict is None:
            self._widget.show_message_box(title="No CGH Pattern",msg_type="error",
                                      message=f"No CGH pattern found for {slmName}, {secName}")
            return
        
        try:
            name = self._cghResults.get(slmKey,{}).get(secKey,{}).get("cgh_name","cgh_pattern") 
            name = "cgh_pattern" if name is None else name

            suggested = os.path.join(self.cghPatternsDir,name)
            path = askForFilePath(self._widget, "Select file to save CGH pattern", defaultFolder=suggested,isSaving=True)
            if not path:
                return
            pattern = result_dict.get("cgh_pattern")
            if isinstance(pattern, np.ndarray):
                np.save(path,pattern) #TODO: would be nice to also save the pattern metadata (parameters, perf, ...)
            else:
                raise 
        except Exception as e:
            if msg_box:
                self._widget.show_message_box(title="Error Saving CGH Pattern",msg_type="error",
                                      message=f"Could not save CGH pattern:\n{e}")
            raise

    def on_compute_cgh(self, slmKey, secKey, cgh_params):
        """Initiate CGH computation for given SLM and section."""

        if self._cghWorker.is_running:
            return

        cgh_general = cgh_params.get("cgh_general", {})
        
        # Target preparation
        target_type = cgh_general.get("target_type",None)
        target_params = cgh_params.get(target_type, None)
        try:
            self.sync_target(slmKey, secKey)
            target = self._targets.get(slmKey).get(secKey)
            target_array = target.array
            feedback_count = target.feedback_count
            cgh_name = target.name
            target_params = dict(target.params)
        except Exception as e:
            self._widget.on_cgh_computation_result(slmKey, secKey,success=False, msg=e)
            self.__logger.error(traceback.format_exc())
            return

        if feedback_count > 0 and self._cghResults.get(slmKey,{}).get(secKey,{}).get("cgh_pattern") is not None:
            previous_pattern = np.angle(self._cghResults.get(slmKey).get(secKey).get("cgh_pattern"))
        else:
            previous_pattern = None
        slmInfo = self._slmInfos.get(slmKey)
        pixel_size_um = getattr(slmInfo, "pixelSize", None)

        # Wavelength is stored in the section's General parameters, not in cgh_params.
        all_params = self._widget.get_params()
        section_params = all_params.get(slmKey, {}).get(secKey, {})
        wavelength_nm = section_params.get("general", {}).get("wavelength_nm", None)


        # dispatch computation to CGH worker
        comput_params = cgh_params.get("cgh_computation",{})
        self._cghWorker.prepareForNewComputation(
            slmKey, secKey, target,cgh_name, comput_params, target_params,previous_pattern,
            pixel_size_um=pixel_size_um,wavelength_nm=wavelength_nm
            )
        self._cghWorker.sigStartComputation.emit()
    

    def on_cgh_computed(self,slmKey,secKey, result_dict,msg=""):
        """Handle CGH computed signal from CGH worker."""

        msgs=[msg] if msg else []
        engine = self._patternEngines.get(slmKey)
        try:
            engine_msg = engine.set_new_cgh_pattern(secKey, result_dict["cgh_pattern"])
            if engine_msg is not None:
                msgs.append(engine_msg)
        except:
            m = f"Computation sucessful but setting new cgh pattern in PatternEngine failed, " \
                  f"likely due to padding/cropping patterns. Double-check that target sizes make sense."
            self._widget.on_cgh_computation_result(slmKey,secKey,success=False,msg=m)
            raise

        cgh_name = result_dict.get("cgh_name")
        
        # format msg
        full_msg = None
        if len(msgs) >0:
            processed_msgs = [m.replace("\n", "<br>") for m in msgs]
            full_msg = "<br><br>".join(processed_msgs)

        # store results and notify widget computation is done
        self._cghResults.setdefault(slmKey,{})[secKey] = result_dict
        self._widget.on_cgh_computation_result(slmKey,secKey,success=True,msg=full_msg,cgh_name=cgh_name)


    def on_cgh_computation_failed(self, slmKey, secKey, msg):
        self._widget.on_cgh_computation_result(slmKey,secKey,success=False, msg=msg)


    def on_visualize_target(self,slmKey,secKey):
        """Retrieve target array and send it to widget."""
        try:
            self.sync_target(slmKey,secKey)
            target_array =  self._targets.get(slmKey).get(secKey).array
            self._widget.plot_target(target_array)
        except Exception as e:
            self._widget.show_message_box(title="Error Creating Target",msg_type="warning",
                                          message=f"Could not create target:\n{e}")
            self.__logger.error(traceback.format_exc())
            return

    def on_visualize_cgh_performances(self, slmKey,secKey):
        """Query CGH performances for given SLM and send them to widget to be displayed."""
        performances = self._cghResults.get(slmKey, {}).get(secKey, {}).get("performances", None)
        self._widget.plot_cgh_performances(performances)
    
    def on_show_cgh_result(self, slmKey, secKey,pad_size):
        """Simulates CGH result (expected image in sample plane) and send it to widget to be displayed."""
        cgh_array = self._cghResults.get(slmKey, {}).get(secKey, {}).get("cgh_pattern", None)
        
        if cgh_array is None:
            self._widget.show_message_box(title="No CGH Pattern",msg_type="warning",
                                          message="No CGH pattern computed yet for the selected SLM and section.")
            return
        
        result = cgh.simulate_propagation_fft(cgh_array, padding=True, pad_size=pad_size)
        self._widget.plot_cgh_result(result)

    def on_load_feedback(self,slmKey,secKey,path=None):
        if path is None:
            path = askForFilePath(self._widget, "Select feedback image",isSaving=False)
            if not path or not os.path.exists(path):
                return
        try:
            img = np.array(Image.open(path))
            self._experimentalResults.setdefault(slmKey, {})[secKey] = img
        except Exception as e:
            self._widget.show_message_box(title="Error Loading Feedback",msg_type="error",message=e)
            self.__logger.error(traceback.format_exc())
            return


    def on_feedback_analysis_prm(self,slmKey,secKey):
        """ Retrieves analysis parameters of the current target, opens JSON editor dialog
        enabling user to modify them, and upates target analysis paramters."""
        target_type = self._widget.getCurrentTargetType(slmKey,secKey)
        if target_type is None:
            return
        target = self._targets.get(slmKey,{}).get(secKey,None)
        if target is None or target.name != target_type:
            try:
                self.sync_target(slmKey,secKey)
                target = self._targets.get(slmKey,{}).get(secKey,None)
            except:
                self.__logger.error(traceback.format_exc())
                return 
            
        if not hasattr(target, "analysis_prm"):
            return
        
        params = target.analysis_prm
        updated = JsonEditorDialog.edit_params(self._widget, params)
        if updated is not None:
            target.update_analyze_prm(updated)


    def on_feedback_reset(self,slmKey,secKey):
        target = self._targets.get(slmKey,{}).get(secKey) 
        if target is not None:
            target.reset_feedback()
        self._experimentalResults.setdefault(slmKey,{})[secKey]=None
        self._cghResults.setdefault(slmKey, {})[secKey] = {} # clear any previous cgh result


    def on_feedback_snap(self, slmKey, secKey):
        """
        Connect communication channel signal "sigUpdateImage" to a handler waiting 
        for the snap image to arrive, with a timeout of 1s. 
        """
        def handle_image(img=None, isCurrentDetector=None,timeout=False):
            if timeout:                    
                self._widget.show_message_box(title="Snap failed",msg_type="warning",
                                            message="No feedback image acquired.")
                return False
            
            if isCurrentDetector and img is not None:
                self._experimentalResults.setdefault(slmKey, {})[secKey] = img
                return True
            else:
                return False

        timeout_ms = 1000 # 1s
        wrapper_slot = lambda _, img, __, ___, isCurrentDetector: handle_image(img, isCurrentDetector)
        wrapper_slot._timeout_handler = lambda timeout=False: handle_image(timeout=timeout)

        self._oneshot = signaltools.OneShotConnection(
            signal = self._commChannel.sigUpdateImage,
            slot = wrapper_slot,
            timeout_ms = timeout_ms,
            notify_timeout = True,
            wait_for_success = True
        )

    
    def on_feedback_analysis(self,slmKey,secKey):
        target = self._targets.get(slmKey,{}).get(secKey) 
        result = self._experimentalResults.get(slmKey,{}).get(secKey)
        
        if target is None:
            msg = "Target not created yet."
            success = False

        elif result is None:
            msg = "Not result found, acquire first before doing result analysis."
            success = False

        else:
            try: 
                success, msg = target.analyze_result(result)
            except Exception as e:
                success = False
                msg = e
                self.__logger.error(traceback.format_exc())

        if not success:
            self._widget.show_message_box(title="Feedback analysis failed",msg_type="error",message=msg)


    def on_feedback_update_target(self, slmKey,secKey):

        target = self._targets.get(slmKey,{}).get(secKey)
        if target is None:
            msg = "Target not created yet."
            success = False

        else:
            try:
                success, msg = target.adapt_target()
            except Exception as e:
                success = False
                msg = e
                self.__logger.error(traceback.format_exc())

        if not success:
            self._widget.show_message_box(title="Updating target failed",msg_type="error",message=msg)
        else:
            # clear experimental result and update widget count
            self._experimentalResults.setdefault(slmKey,{})[secKey]=None
            self._widget.update_feedback_count(slmKey,secKey,target.feedback_count)


     # ----- Calibration ----- #

    # def on_calibrate_cgh_target(self, slmKey, secKey):
    #     self.sync_target(slmKey,secKey)
    #     target = self._targets.get(slmKey,{}).get(secKey,None)
    
    #     params = target.calib_params
    #     if params is None:
    #         self.__logger.error(f"Target {target.target_type} is not exposing calibration parameters.")
    #         return
        
    #     calib_values = self._widget.CalibrateDialog.set_new_calib(self._widget, params)
    #     conv_factor_dict = target.calibrate(calib_values)
    #     if conv_factor_dict is None:
    #         return
        
    #     self._widget.set_conv_factor_label(conv_factor_dict)
    #     self._conv_factors.setdefault(slmKey,{})[secKey] = conv_factor_dict

    # def on_set_default_conv_factor(self,slmKey,secKey):
    #     conv_factor = self._conv_factors.get(slmKey,{}).get(secKey)

    #     error=False
    #     if conv_factor is None:
    #         error=True
    #         self.__logger.error(f"Cannot set default conversion factor for {slmKey}, {secKey}",
    #                             f" because current factor is None.")
    #     elif not isinstance(conv_factor,dict):
    #         error=True
    #         self.__logger.error(f"Cannot set default conversion factor for {slmKey}, {secKey}",
    #                             f" because expected a dict with: 'x', 'y' keys. Instead",
    #                             f"got type {type(conv_factor)}, and value: {conv_factor}")
    #     else:
    #         try:
    #             self._set_setup_config_conv_factor(slmKey, secKey, conv_factor)
    #         except:
    #             error = True
    #             self.__logger.error(traceback.format_exc())

    #     if error:
    #         self._widget.show_message_box(
    #             title="Setting default conversion factor",
    #             msg_type="error",
    #             message=f"Setting default conversion factor failed. Check logger for full error detail."
    #         )
        
    
    # def _set_setup_config_conv_factor(self, slmKey, secKey, conv_factor):
    #     slmName = self._slmNames.get(slmKey)
    #     slmInfo = getattr(self._setupInfo, "slms", {}).get(slmName)
    #     if slmInfo is None:
    #         raise KeyError(f'Could not find SLM "{slmName}" in setupInfo.slms')
    #     conversion_factors = getattr(slmInfo, "conversion_factors", None)
    #     if conversion_factors is None:
    #         conversion_factors = {}
    #         object.__setattr__(slmInfo, "managerProperties", conversion_factors)
        
    #     conversion_factors.setdefault[secKey] = conv_factor
    #     configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)


     # ----- CGH Worker ----- #
    class CGHWorker(Worker):
        """ Worker class to compute CGH patterns in a separate thread. """

        sigStartComputation = Signal()
        sigWorkerCGHComputed = Signal(str, str, dict, str)  # slmKey, secKey, result dict, optional message
        sigWorkerCGHComputationFailed = Signal(str, str, str)  # slmKey, secKey, error message

        def __init__(self):
            super().__init__()
            self._mutex = Mutex()
            self._numQueuedComputations = 0
            self.is_running = False
            self.__logger = initLogger(self)

        def prepareForNewComputation(self, slmKey, secKey, target, cgh_name, comput_params, target_params,
                                     previous_pattern=None, quad_initial_phase=None,pixel_size_um=None,
                                     wavelength_nm=None,):
            self._skmKey = slmKey
            self._secKey = secKey
            self._target = target
            self._cgh_name = cgh_name
            self._previous_pattern = previous_pattern
            self._comput_params = comput_params
            self._target_params = target_params
            self._pixel_size_um = pixel_size_um
            self._wavelength_nm = wavelength_nm
            self._mutex.lock()
            self._numQueuedComputations += 1
            self._mutex.unlock()

        def compute(self):
            self.is_running = True
            try:
                if self._numQueuedComputations > 1:
                    # Skip to catch up
                    return
                # pattern, performances, msg, err = cgh.gerchberg_saxton(self._target,previous_pattern=self._previous_pattern,**self._comput_params)

                # Vector target -> direct-summation backend.
                if (
                    getattr(self._target, "uses_direct_summation", False)
                    or getattr(self._target, "spot_vectors_kxy", None) is not None
                ):
                    pattern, performances, msg, err = direct_cgh.direct_spot_wgs_from_target(
                        target=self._target,
                        comput_params=self._comput_params,
                        previous_pattern=self._previous_pattern,
                        pixel_size_um=self._pixel_size_um,
                        wavelength_nm=self._wavelength_nm,
                    )
                    # pattern, performances, msg, err = slmsuite_cgh.compressed_spot_hologram(
                    #     target=self._target,
                    #     comput_params=self._comput_params,
                    #     previous_pattern=self._previous_pattern,
                    #     pixel_size_um=self._pixel_size_um,
                    # )

                # Raster target -> legacy GS backend.
                else:
                    target_array = (
                        self._target.array
                        if hasattr(self._target, "array")
                        else self._target
                    )

                    pattern, performances, msg, err = cgh.gerchberg_saxton(
                        target_array,
                        previous_pattern=self._previous_pattern,
                        **self._comput_params,
                    )

                if pattern is None:
                    self.sigWorkerCGHComputationFailed.emit(self._skmKey, self._secKey,msg)
                    if err is not None:
                        self.__logger.error(traceback.format_exc())
                else:
                    result_dict = {
                        "cgh_name": self._cgh_name,
                        "cgh_pattern": pattern,
                        "performances": performances,
                        "comput_params": self._comput_params,
                        "target_params": self._target_params,
                    }

                    self.sigWorkerCGHComputed.emit(self._skmKey, self._secKey, result_dict, msg)

            except Exception as e:
                msg = str(e)
                self.sigWorkerCGHComputationFailed.emit(self._skmKey, self._secKey,msg)
                self.__logger.error(traceback.format_exc())

            finally:
                self.is_running = False
                self._mutex.lock()
                self._numQueuedComputations -= 1
                self._mutex.unlock()

