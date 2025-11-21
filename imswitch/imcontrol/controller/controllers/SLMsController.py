import json
import os
import numpy as np
from PIL import Image

from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.view.guitools import askForFilePath
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcommon.model import dirtools

from ..patterndesigners.registries import PATTERNS_REGISTRY, ABERRATIONS_REGISTRY
from ..patterndesigners import cghPatterns as cgh
from ..patterndesigners.patternEngine import PatternEngine

full_registry = {
    "patterns": PATTERNS_REGISTRY,
    "aberrations": ABERRATIONS_REGISTRY
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
        self._loadedTargets = {}    # {slmKey: {secKey: target_array}}
        self._currentTargets = {}   # {slmKey: {secKey: target_array}}
        self._cghResults = {}       # {slmKey: {secKey: {"cgh_pattern":..., "performances":...}}}
        self._wavelengths = {}      # {slmKey: {secKey: wl}}

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
                if slmInfo.widgetOptions.get("startConfig") is not None:
                    start_config = slmInfo.widgetOptions.get("startConfig")
                    config_path = os.path.join(self.configsDir, start_config)
                    if os.path.isfile(config_path):
                        self.on_load_config(slmKey, path=config_path)
                    else:
                        self.__logger.warning(f"Initial SLM config file {config_path} not found.")

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
                raise FileNotFoundError(f"Cannot find correction pattern of {slmName} at wavelength {wl}")
            
            correctionImg = np.array(Image.open(correctionPatternFullPath))
            engine.update_correction_pattern(secKey,correctionImg)
            msg = None
        
        except Exception as e:
            sectionName = self._widget._tab_names_dict.get(slmKey,{}).get(secKey,secKey)
            msg = f"<b>{slmName} - {sectionName}</b>: Failed to load correction pattern :\n{e}"
        
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

            engine.update_twopi_value(secKey,twopivalue)
            msg = None
            if not measured:
                sectionName = self._widget._tab_names_dict.get(slmKey,{}).get(secKey,secKey)
                msg = f"<b>{slmName} - {sectionName}</b>: 2Pi value not characterized for {wl}nm. Using default manufacturer one."

        except Exception as e:
            sectionName = self._widget._tab_names_dict.get(slmKey,{}).get(secKey,secKey)
            msg = f"<b>{slmName} - {sectionName}</b>: failed to update 2pi value:\n{e}"

        return msg
    
    def update_cached_wl(self,slmKey,params):
        """ Update cached wavelengths of `slmKey` with wavelenghts in `params` for each section"""
        sectList = self._widget._slmSectionList.get(slmKey)
        for secKey in sectList:
            wl = params.get(secKey).get("general").get("wavelength_nm")
            if wl != self._wavelengths.get(slmKey,{}).get(secKey,0): 
                self._wavelengths.setdefault(slmKey,{})[secKey] = wl


    # --------- saving/loading related -------- #

    def on_save_config(self, slmKey,slm_params, msg_box=True):
        """Save `slm_params` to a user-defined JSON file."""
        try:
            suggested = os.path.join(self.configsDir,slmKey+"_config")
            path = askForFilePath(self._widget, "Select file to save configuration", defaultFolder=suggested,isSaving=True)
            if not path:
                return
            path = path + ".json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(slm_params, f, indent=2)
                
        except Exception as e:
            self.__logger.error(f"Failed to save config: {e}")
            if msg_box:
                self._widget.show_message_box(title="Error Saving Configuration",msg_type="error",
                                      message=f"Could not save configuration:\n{e}")


    def on_load_config(self, slmKey, path=None):
        """Load SLM configuration from a JSON file and send to widget"""
        if path is None:
            path = askForFilePath(self._widget, "Select configuration file to load", defaultFolder=self.configsDir,isSaving=False)
            if not path or not os.path.exists(path):
                return
        with open(path, "r", encoding="utf-8") as f:
            slm_params = json.load(f)
        self._widget.on_config_loaded(slmKey,slm_params,msg_box=True)


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
    


    # ----- CGH related methods ----- #


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
            if result_dict.get("target_params") is not None:
                name = targetPrmToStr(result_dict.get("target_params"))
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
        if cgh_general.get("use_loaded_target", False):
            target = self._loadedTargets.get(slmKey,{}).get(secKey,None)
            if target is None:
                self._widget.on_cgh_computation_result(slmKey, secKey, success=False, msg="Could not find a loaded target")
                return
        else:
            target_type = cgh_general.get("target_type",None)
            target_params = cgh_params.get(target_type, None)
            try:
                target = cgh.create_target(target_type, **target_params)
            except Exception as e:
                self._widget.on_cgh_computation_result(slmKey, secKey,success=False, msg=e)
                return
        
        self._currentTargets.setdefault(slmKey,{})[slmKey] = target # store current target

        # dispatch computation to CGH worker
        target_params["target_name"] = target_type
        comput_params = cgh_params.get("cgh_computation",{})
        self._cghWorker.prepareForNewComputation(slmKey, secKey, target, comput_params, target_params)
        self._cghWorker.sigStartComputation.emit()
    

    def on_cgh_computed(self,slmKey,secKey, result_dict):
        """Handle CGH computed signal from CGH worker."""
    
        engine = self._patternEngines.get(slmKey)
        try:
            msg = engine.set_new_cgh_pattern(secKey, result_dict["cgh_pattern"])
        except:
            msg = f"Computation sucessful setting new cgh pattern in PatternEngine failed, " \
                  f"likely due to padding/cropping patterns. Double-check that target sizes make sense."
            self._widget.on_cgh_computation_result(slmKey,secKey,success=False,msg=msg)
            raise

        cgh_name = targetPrmToStr(result_dict.get("target_params"))
        # store results and notify widget computation is done
        self._cghResults.setdefault(slmKey,{})[secKey] = result_dict
        self._widget.on_cgh_computation_result(slmKey,secKey,success=True,msg=msg,cgh_name=cgh_name)


    def on_cgh_computation_failed(self, slmKey, secKey, msg):
        self._widget.on_cgh_computation_result(slmKey,secKey,success=False, msg=msg)


    def on_visualize_target(self,target_type,target_params):
        """Create target pattern based on provided parameters and send it to widget."""
        try:
            target = cgh.create_target(target_type, **target_params)
        except Exception as e:
            self._widget.show_message_box(title="Error Creating Target",msg_type="warning",
                                          message=f"Could not create target:\n{e}")
            return
        
        self._widget.plot_target(target)

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


     # ----- CGH Worker ----- #
    class CGHWorker(Worker):
        """ Worker class to compute CGH patterns in a separate thread. """

        sigStartComputation = Signal()
        sigWorkerCGHComputed = Signal(str, str, dict)  # slmKey, secKey, result dict: {"cgh_pattern":..., "performances":...}
        sigWorkerCGHComputationFailed = Signal(str, str, str)  # slmKey, secKey, error message

        def __init__(self):
            super().__init__()
            self._mutex = Mutex()
            self._numQueuedComputations = 0
            self.is_running = False

        def prepareForNewComputation(self, slmKey, secKey, target, comput_params, target_params):
            self._skmKey = slmKey
            self._secKey = secKey
            self._target = target
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
                pattern, performances, msg = cgh.gerchberg_saxton(self._target,**self._comput_params)

                if pattern is None:
                    self.sigWorkerCGHComputationFailed.emit(self._skmKey, self._secKey,msg)
                else:
                    result_dict = {
                        "cgh_pattern": pattern,
                        "performances": performances,
                        "comput_params": self._comput_params,
                        "target_params": self._target_params,
                    }
                    self.sigWorkerCGHComputed.emit(self._skmKey, self._secKey, result_dict)
            
            except Exception as e:
                msg = str(e)
                self.sigWorkerCGHComputationFailed.emit(self._skmKey, self._secKey,msg)

            finally:
                self.is_running = False
                self._mutex.lock()
                self._numQueuedComputations -= 1
                self._mutex.unlock()



def targetPrmToStr(target_prm:dict):
    if target_prm.get("target_name") == "multi_foci":
        targetx = target_prm.get("target_size_x")
        targety = target_prm.get("target_size_y")
        nfoci = target_prm.get("n_foci")
        period = target_prm.get("period")
        name = f"mf_trgt{targetx}x{targety}_N{nfoci}_P{period}"
        return name
    
    elif target_prm.get("target_name") == "bfp_spots":
        target = target_prm.get("target_size")
        direction = target_prm.get("direction")
        dist = target_prm.get("spot_distance")
        offset = target_prm.get("offset")
        i1 = target_prm.get("spot1_intensity")
        i2 = target_prm.get("spot2_intensity")
        name = f"bfpSpots_{direction}_trgt{target}_dist{dist}_offset{offset}_i1{i1}_i2{i2}"
        return name
    
    else:
        return None