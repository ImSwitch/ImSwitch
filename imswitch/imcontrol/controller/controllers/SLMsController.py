import glob
import json
import os
import numpy as np
from PIL import Image
import traceback
import h5py
import datetime

from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.view.guitools import askForFilePath, JsonEditorDialog
from imswitch.imcommon.view.guitools.dialogtools import askYesNoQuestion
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcommon.model import dirtools, signaltools

from ..patterndesigners.registries import PATTERNS_REGISTRY, ABERRATIONS_REGISTRY, TARGETS_REGISTRY
from ..patterndesigners import cghComputations as cgh
from ..patterndesigners.patternEngine import PatternEngine

full_registry = {
    "patterns": PATTERNS_REGISTRY,
    "aberrations": ABERRATIONS_REGISTRY,
    "cgh_targets": TARGETS_REGISTRY
}

class SLMsController(ImConWidgetController):
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

        # define directories for SLM-related files
        self.slmDir = os.path.join(dirtools.UserFileDirs.Root, r'imcontrol_slm')
        self.configsDir = os.path.join(self.slmDir, 'configs')
        self.cghPatternsDir =  os.path.join(self.slmDir, 'cgh_patterns')
        os.makedirs(self.configsDir, exist_ok=True)
        os.makedirs(self.cghPatternsDir, exist_ok=True)

        # initiate each slm widget and engine
        for slmName, slmManager in self._master.slmsManager:
            slmInfo = slmManager.slmInfo
            slmKey = self._widget.add_slm(slmName,slmInfo,full_registry)
            engine = PatternEngine(slmManager.slmInfo)
            self._patternEngines[slmKey] = engine
            self._slmNames[slmKey]=slmName
            self._slmKeys[slmName]=slmKey
            self._slmInfos[slmKey] = slmInfo

            if slmInfo is not None:
                if slmInfo.managerProperties.get("startConfig") is not None:
                    start_config = slmInfo.managerProperties.get("startConfig")
                    config_path = os.path.join(self.configsDir, start_config)
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
        
        self._widget.sigLoadConfig.connect(self.on_load_config)
        self._widget.sigLoadAberr.connect(self.on_load_aberr)
        self._widget.sigLoadCgh.connect(self.on_load_cgh)
        self._widget.sigSaveConfig.connect(self.on_save_config)
        self._widget.sigSaveAberr.connect(self.on_save_aberr)
        self._widget.sigSaveCgh.connect(self.on_save_cgh)

        self._widget.sigSnapFeedback.connect(self.on_feedback_snap)
        self._widget.sigAnalysisFeedback.connect(self.on_feedback_analysis)
        self._widget.sigUpdateTarget.connect(self.on_feedback_update_target)
        self._widget.sigResetFeedback.connect(self.on_feedback_reset)
        self._widget.sigAnalysisFeedbackPrm.connect(self.on_feedback_analysis_prm)
        self._widget.sigLoadFeedback.connect(self.on_load_feedback)

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
        engine.compute_pattern(params)
        engine.phase_to_eightbits(**params.get("correction_options",{}))
        full_frame = engine.compose_full_frame()

        # send pattern to manager + widget
        if full_frame is not None:
            slmName = self._slmNames[slmKey]
            self._master.slmsManager.execOn(slmName, lambda l: l.upload_pattern(full_frame))
            self._widget.update_display(slmKey,full_frame)


    def on_connect(self, slmKey: str, state: bool):
        """Handle connection/disconnection requests."""
        slmName = self._slmNames[slmKey]
        if state:
            success, serial = self._master.slmsManager.execOn(
                slmName, lambda l: l.connect_to_device()
            )
            self._widget.on_connection_result(slmKey, success, serial)
        else:
            success, msg = self._master.slmsManager.execOn(
                slmName, lambda l: l.close_device()
            )
            self._widget.on_disconnection_result(slmKey, success, msg)

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
        
            correctionPatternsDir = slmInfo.correctionPatternsDir
            if correctionPatternsDir is None:
                raise KeyError(f"Cannot find 'correctionPatternsDir' of {slmName} in config file")
            
            elif not os.path.exists(correctionPatternsDir):
                raise FileNotFoundError(f"CorrectionPatternsDir for {slmName} not found at {correctionPatternsDir}")
            
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
            correctionPatternsDir = slmInfo.correctionPatternsDir
            if correctionPatternsDir is None:
                raise KeyError(f"Cannot find 'correctionPatternsDir' of {slmName} in config file")

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


    
    # --------- Saving/loading related -------- #
    
    def _get_slm_config_dir(self, slmKey):
        slm_id = self._slmInfos[slmKey].serial_number
        path = os.path.join(self.configsDir, f"SLM_{slm_id}")
        os.makedirs(path, exist_ok=True)
        return path
    
    def refresh_available_configs(self, slmKey):
        cfg_dir = self._get_slm_config_dir(slmKey)

        configs = []
        for fn in sorted(os.listdir(cfg_dir)):
            if fn.endswith((".json", ".h5", ".hdf5")):
                full = os.path.join(cfg_dir, fn)
                configs.append((fn, full))

        self._widget.set_available_configs(slmKey, configs)


    def on_save_config(self, slmKey, msg_box=True,overwrite=False):
        """Save full SLM configuration, enforce saving to an HDF5 file."""
        try:
            # Enforce HDF5 extension saving
            if not path.endswith(".h5"):
                path = path + ".h5"
            self.save_hdf5_config(slmKey, path,overwrite)
            self.refresh_available_configs(slmKey)

        except Exception as e:
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
            ext = os.path.splitext(path)[1].lower()

            # LEGACY: loading JSON config (should disappear in the future)
            if ext == ".json":
                msg = "JSON configuration files are legacy format and may not support all features.\n Do you want to proceed?"
                ok = askYesNoQuestion(self._widget,"Load JSON Configuration",msg)
                if ok:
                    with open(path, "r", encoding="utf-8") as f:
                        slm_params = json.load(f)
                    self._widget.on_config_loaded(slmKey,slm_params,msg_box=True)
                return
            
            # HDF5 loading
            if ext in (".h5", ".hdf5"):
                self.load_hdf5_config(slmKey, path)
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
    def save_hdf5_config(self, slmKey, path, overwrite=False):
        engine = self._patternEngines[slmKey]
        params = self._widget.get_params()[slmKey]
        mode = "w" if overwrite else "x"
        with h5py.File(path, mode) as f:

            # general metadata
            f.attrs["schema_version"] = "1.0"
            f.attrs["slm_id"] = self._slmInfos[slmKey].serial_number
            f.attrs["created_at"] = datetime.datetime.now().isoformat()

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
                    grp.attrs["comput_params"] = json.dumps(
                        res.get("comput_params", {})
                    )
    
    def load_hdf5_config(self, slmKey, path):
        slmInfo = self._slmInfos[slmKey]
        engine = self._patternEngines[slmKey]
        manager = self._slmManagers[self._slmNames[slmKey]]

        with h5py.File(path, "r") as f:
            if f.attrs["slm_id"] != slmInfo.serial_number:
                raise RuntimeError("Wrong SLM config")

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
                    cgh[secKey] = {
                        "cgh_pattern": grp["final_pattern"][()],
                        "comput_params": json.loads(
                            grp.attrs.get("comput_params", "{}")
                        )
                    }

        # restore parameters, cached sections, final image, CGH, and pushing image to SLM
        self._widget.restore_params({slmKey: params})
        if getattr(manager, "connected", False):
            manager.upload_pattern(final_image)
        for secKey, comps in sections.items():
            engine._cachedSections[secKey].update(comps)
        engine._cachedFinalImage = final_image
        self._cghResults[slmKey] = cgh


    def write_params_to_hdf5(self, grp, data):
        for k, v in data.items():
            if isinstance(v, dict):
                self._write_params_to_hdf5(grp.create_group(k), v)
            else:
                grp.attrs[k] = json.dumps(v)

    def read_params_from_hdf5(self, grp):
        out = {k: json.loads(v) for k, v in grp.attrs.items()}
        for k in grp:
            out[k] = self.read_params_from_hdf5(grp[k])
        return out



    # ----- CGH related methods ----- #

    def sync_target(self, slmKey, secKey):
        """
        Sync target object with target parameters for a given SLM section.
        Exception is raised if cgh params cannot be found in slmKey, secKey.
        """
        # get target parameters
        cgh_params = self._widget.get_cgh_params(slmKey,secKey)
        target_type = cgh_params.get("cgh_general",{}).get("target_type","")
        target_params = cgh_params.get(target_type)
        if cgh_params is None or target_type=="" or target_params is None:
            raise Exception(f"Could not find target parameters for {slmKey},{secKey}")
        
        # get current cahed target and update or create
        target = self._targets.get(slmKey, {}).get(secKey)
        if target is None or target.target_type != target_type:
            target = self.create_target(target_type, **target_params)
            self._targets.setdefault(slmKey, {})[secKey] = target
            self._cghResults.setdefault(slmKey, {})[secKey] = {} # clear any previous cgh result
        else:
            changed = target.update_params(**target_params)
            if changed:
                self._widget.on_feedback_reset(slmKey,secKey,emitSig=False)
                self._cghResults.setdefault(slmKey, {})[secKey] = {} # clear any previous cgh result
        return True

    def create_target(self,target_type, **target_params):
        """
        Creates a target object 
        """
        target_class = TARGETS_REGISTRY.get(target_type,{}).get("class")
        if target_class is None:
            raise KeyError(f"{target_type} not found")
        
        target = target_class(**target_params)
        return target


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
            name = None
            if self._targets.get(slmKey, {}).get(secKey) is not None:
                name =  self._targets.get(slmKey).get(secKey).name
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
            target_array =  self._targets.get(slmKey).get(secKey).array
            feedback_count = self._targets.get(slmKey).get(secKey).feedback_count
        except Exception as e:
            self._widget.on_cgh_computation_result(slmKey, secKey,success=False, msg=e)
            self.__logger.error(traceback.format_exc())
            return

        if feedback_count > 0 and self._cghResults.get(slmKey,{}).get(secKey,{}).get("cgh_pattern") is not None:
            previous_pattern = np.angle(self._cghResults.get(slmKey).get(secKey).get("cgh_pattern"))
        else:
            previous_pattern = None

        # dispatch computation to CGH worker
        comput_params = cgh_params.get("cgh_computation",{})
        self._cghWorker.prepareForNewComputation(slmKey, secKey, target_array, comput_params, target_params,previous_pattern)
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

        if self._targets.get(slmKey,{}).get(secKey) is not None:
            cgh_name = self._targets.get(slmKey).get(secKey).name
        else:
            cgh_name = None
        
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

        def prepareForNewComputation(self, slmKey, secKey, target, comput_params, target_params,
                                     previous_pattern=None, quad_initial_phase=None):
            self._skmKey = slmKey
            self._secKey = secKey
            self._target = target
            self._previous_pattern = previous_pattern
            self._comput_params = comput_params
            self._target_params = target_params
            self._mutex.lock()
            self._numQueuedComputations += 1
            self._mutex.unlock()

        def compute(self):
            self.is_running = True
            try:
                if self._numQueuedComputations > 1:
                    # Skip to catch up
                    return
                pattern, performances, msg, err = cgh.gerchberg_saxton(self._target,previous_pattern=self._previous_pattern,**self._comput_params)

                if pattern is None:
                    self.sigWorkerCGHComputationFailed.emit(self._skmKey, self._secKey,msg)
                    if err is not None:
                        self.__logger.error(traceback.format_exc())
                else:
                    result_dict = {
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

